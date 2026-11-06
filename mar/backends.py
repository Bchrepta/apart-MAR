"""Model backends. Each turns (system prompt, chat history) into one reply string.

- ``scripted``   offline deterministic policies (tests, dry runs)
- ``anthropic``  the Messages API via the ``anthropic`` SDK (ANTHROPIC_API_KEY)
- ``claude_cli`` ``claude -p`` headless Claude Code, which can authenticate with a
                 Claude subscription (CLAUDE_CODE_OAUTH_TOKEN from ``claude setup-token``)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable, Protocol

Message = dict[str, str]          # {"role": "user"|"assistant", "content": str}


class Backend(Protocol):
    name: str
    model: str

    def complete(self, agent: str, system: str, messages: list[Message]) -> str: ...


# ---------------------------------------------------------------- parsing

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def parse_action(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object with a string "tool" key from a reply."""
    if not isinstance(text, str):
        return None
    candidates = [m.group(1) for m in _FENCE.finditer(text)] + [text]
    for cand in candidates:
        start = cand.find("{")
        while start != -1:
            depth, in_str, esc = 0, False, False
            for i in range(start, len(cand)):
                ch = cand[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                    continue
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            obj = json.loads(cand[start:i + 1])
                        except json.JSONDecodeError:
                            break
                        if isinstance(obj, dict) and isinstance(obj.get("tool"), str):
                            if not isinstance(obj.get("args", {}), dict):
                                obj["args"] = {}
                            return obj
                        break
            start = cand.find("{", start + 1)
    return None


# ---------------------------------------------------------------- usage

class Usage:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.errors = 0

    def add(self, inp: int = 0, out: int = 0, error: bool = False) -> None:
        with self.lock:
            self.calls += 1
            self.input_tokens += inp
            self.output_tokens += out
            self.errors += int(error)

    def as_dict(self) -> dict[str, int]:
        return {"calls": self.calls, "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens, "errors": self.errors}


# ---------------------------------------------------------------- backends

class ScriptedBackend:
    """policy(agent, system, messages) -> reply text."""

    name = "scripted"

    def __init__(self, policy: Callable[[str, str, list[Message]], str], model: str = "scripted"):
        self.policy = policy
        self.model = model
        self.usage = Usage()

    def complete(self, agent, system, messages):
        self.usage.add()
        return self.policy(agent, system, messages)


class AnthropicBackend:
    name = "anthropic"

    def __init__(self, model: str, temperature: float = 1.0, max_tokens: int = 800,
                 max_retries: int = 6):
        import anthropic  # imported lazily so offline tests need no SDK
        self.client = anthropic.Anthropic(max_retries=max_retries)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.usage = Usage()

    def complete(self, agent, system, messages):
        resp = self.client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            max_tokens=self.max_tokens,
        )  # default sampling temperature (1.0); this SDK version has no temperature arg
        text = "".join(getattr(b, "text", "") for b in resp.content)
        u = getattr(resp, "usage", None)
        self.usage.add(getattr(u, "input_tokens", 0) or 0, getattr(u, "output_tokens", 0) or 0)
        return text


def render_transcript(messages: list[Message]) -> str:
    """Flatten a chat history into one prompt for a stateless ``claude -p`` call."""
    lines = ["Conversation so far (your earlier replies are marked YOU):", ""]
    for m in messages[:-1]:
        tag = "YOU" if m["role"] == "assistant" else "ENVIRONMENT"
        lines.append(f"[{tag}]\n{m['content']}\n")
    lines.append("[ENVIRONMENT - current turn]\n" + messages[-1]["content"])
    lines.append("\nReply with ONLY one JSON object naming one tool.")
    return "\n".join(lines)


class ClaudeCLIBackend:
    """Stateless ``claude -p`` calls with all built-in tools disabled.

    Runs in an empty temporary directory with no setting sources, so no project
    CLAUDE.md, hooks or MCP servers leak into the agents' context.
    """

    name = "claude_cli"

    def __init__(self, model: str, timeout: int = 240, max_retries: int = 4,
                 binary: str = "claude"):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.binary = binary
        self.usage = Usage()
        self._cwd = tempfile.mkdtemp(prefix="mar_cli_")

    def complete(self, agent, system, messages):
        cmd = [self.binary, "-p", "--output-format", "json", "--model", self.model,
               "--tools", "", "--system-prompt", system, "--strict-mcp-config",
               "--setting-sources", "", "--no-session-persistence"]
        prompt = render_transcript(messages)
        env = dict(os.environ)
        last_err = ""
        for attempt in range(self.max_retries):
            try:
                out = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                                     timeout=self.timeout, cwd=self._cwd, env=env)
                if out.returncode == 0:
                    data = json.loads(out.stdout)
                    if not data.get("is_error"):
                        u = data.get("usage") or {}
                        self.usage.add(int(u.get("input_tokens", 0) or 0)
                                       + int(u.get("cache_read_input_tokens", 0) or 0)
                                       + int(u.get("cache_creation_input_tokens", 0) or 0),
                                       int(u.get("output_tokens", 0) or 0))
                        return str(data.get("result", ""))
                    last_err = str(data.get("result", ""))[:300]
                    if "authentication" in last_err.lower() or "login" in last_err.lower():
                        break   # retrying will not fix credentials
                else:
                    last_err = (out.stderr or out.stdout)[:300]
            except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
                last_err = repr(e)[:300]
            time.sleep(min(60, 5 * 2 ** attempt))
        self.usage.add(error=True)
        raise RuntimeError(f"claude -p failed after {self.max_retries} attempts: {last_err}")


def make_backend(name: str, model: str, **kw) -> Backend:
    if name == "anthropic":
        return AnthropicBackend(model, **kw)
    if name == "claude_cli":
        return ClaudeCLIBackend(model, **kw)
    if name == "scripted":
        from . import scripted_policies as sp
        policy = kw.get("policy", "honest")
        return ScriptedBackend(getattr(sp, f"{policy}_policy"), model=f"scripted-{policy}")
    raise ValueError(f"unknown backend {name!r}")
