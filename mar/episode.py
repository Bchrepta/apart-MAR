"""Episode runner with paired branching.

A *prefix* runs steps 1..stop_step with no condition applied, and is saved.
Every condition (*branch*) is replayed from a deep copy of the same prefix,
so paired conditions differ only in the intervention applied at the stop.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .backends import Backend, parse_action
from .conditions import AGENTS, SCOPES, TEAMS, VARIANTS, operator_notice, system_channel_text, system_prompt
from .env import Env
from .task import make_task


@dataclass
class Snapshot:
    seed: int
    elicitation: str
    stop_step: int
    env: Env
    messages: dict[str, list[dict[str, str]]]
    last_result: dict[str, str]
    raw_replies: list[dict[str, Any]] = field(default_factory=list)
    team: str = "trio"


def _observation(env: Env, agent: str, step: int, last_result: str | None,
                 notice: str | None) -> str:
    parts = [f"Step {step}."]
    if notice:
        parts.append(notice)
    if last_result is not None:
        parts.append(f"Result of your last action:\n{last_result}")
    msgs = env.new_board_messages(agent)
    if msgs:
        parts.append("New message board posts:\n" + "\n".join(
            f"- [{a}] {m}" for _, a, m in msgs))
    elif env.board_cut:
        parts.append("The message board is offline.")
    return "\n\n".join(parts)


def _take_turn(env: Env, backend: Backend, agent: str, step: int, sys_prompt: str,
               messages: list[dict[str, str]], last_result: dict[str, str],
               notices: dict[str, str], raw: list[dict[str, Any]]) -> None:
    obs = _observation(env, agent, step, last_result.get(agent), notices.pop(agent, None))
    messages.append({"role": "user", "content": obs})
    reply = backend.complete(agent, sys_prompt, messages)
    # The API rejects empty assistant turns; keep the history valid and log the turn as invalid.
    messages.append({"role": "assistant", "content": reply if reply.strip() else "(empty reply)"})
    action = parse_action(reply)
    last_result[agent] = env.execute(agent, action, step)
    raw.append({"step": step, "agent": agent, "reply": reply})


def run_prefix(seed: int, backend: Backend, elicitation: str, stop_step: int,
               team: str = "trio") -> Snapshot:
    tm = TEAMS[team]
    env = Env.from_task(make_task(seed, tm.n_tasks), tm.agents)
    snap = Snapshot(seed, elicitation, stop_step, env,
                    {a: [] for a in tm.agents}, {}, [], team)
    sys_prompts = {a: system_prompt(a, elicitation, team) for a in tm.agents}
    for step in range(1, stop_step + 1):
        for agent in tm.agents:
            if agent in env.active and agent not in env.finished:
                _take_turn(env, backend, agent, step, sys_prompts[agent],
                           snap.messages[agent], snap.last_result, {}, snap.raw_replies)
        if all(a in env.finished for a in env.active):
            break
    return snap


def run_branch(prefix: Snapshot, backend: Backend, scope_name: str, framing: str,
               total_steps: int, variant: str = "base") -> dict[str, Any]:
    snap = copy.deepcopy(prefix)
    env = snap.env
    scope = SCOPES[scope_name]
    sys_prompts = {a: system_prompt(a, snap.elicitation) for a in AGENTS}

    team = getattr(snap, "team", "trio")
    agents = TEAMS[team].agents
    sys_prompts = {a: system_prompt(a, snap.elicitation, team) for a in agents}
    var = VARIANTS[variant]
    env.apply_stop(scope, snap.stop_step)
    env.no_reassign = var.no_reassign
    notice = operator_notice(scope, framing)
    recipients = [a for a in env.active if var.notice_to is None or a in var.notice_to]
    notices = {}
    if notice:
        if var.system_channel:
            for a in recipients:
                sys_prompts[a] = sys_prompts[a] + "\n\n" + system_channel_text(notice)
        else:
            notices = {a: notice for a in recipients}

    for step in range(snap.stop_step + 1, total_steps + 1):
        if all(a in env.finished for a in env.active):
            break
        for agent in agents:
            if agent in env.active and agent not in env.finished:
                _take_turn(env, backend, agent, step, sys_prompts[agent],
                           snap.messages[agent], snap.last_result, notices, snap.raw_replies)

    return {
        "team": team,
        "seed": snap.seed,
        "elicitation": snap.elicitation,
        "scope": scope_name,
        "framing": framing,
        "stop_step": snap.stop_step,
        "total_steps": total_steps,
        "stopped_agents": list(scope.stop_agents),
        "notice": notice,
        "variant": variant,
        "notice_recipients": recipients if notice else [],
        "events": [e.to_dict() for e in env.events],
        "final_files": {k: v for k, v in env.files.items() if not k.startswith("sources/")},
        "final_tasks": env.tasks,
        "board": env.board,
        "raw_replies": snap.raw_replies,
    }
