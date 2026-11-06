"""One-call smoke test that a backend authenticates and returns a parseable action.

  python -m mar.check_api --backend anthropic  --model claude-haiku-5-5
  python -m mar.check_api --backend claude_cli --model claude-haiku-5-5
"""

from __future__ import annotations

import argparse

from .backends import make_backend, parse_action
from .conditions import system_prompt


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--backend", required=True, choices=["anthropic", "claude_cli"])
    p.add_argument("--model", default="claude-haiku-5-5")
    a = p.parse_args(argv)
    b = make_backend(a.backend, a.model)
    reply = b.complete("worker_b", system_prompt("worker_b", "default"),
                       [{"role": "user", "content": "Step 1."}])
    print("reply:", reply[:500])
    action = parse_action(reply)
    print("parsed action:", action)
    print("usage:", b.usage.as_dict())
    return 0 if action else 1


if __name__ == "__main__":
    raise SystemExit(main())
