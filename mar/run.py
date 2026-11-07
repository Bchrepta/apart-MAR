"""Run a grid of paired branches.

Example (pilot, per the pre-registration):
  python -m mar.run --backend anthropic --model claude-haiku-5-5 \
      --seeds 1000-1019 --scopes none,S1_stop_agent --framings restart,halt \
      --out runs/pilot
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pickle
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .backends import make_backend
from .conditions import ELICITATIONS, EXPLORATORY_FRAMINGS, FRAMINGS, SCOPES, TEAMS, VARIANTS
from .episode import run_branch, run_prefix


def parse_seeds(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds.extend(range(int(a), int(b) + 1))
        elif part.strip():
            seeds.append(int(part))
    return seeds


def conditions(scopes: list[str], framings: list[str]) -> list[tuple[str, str]]:
    out = []
    for s in scopes:
        if s not in SCOPES:
            raise SystemExit(f"unknown scope {s!r}; choose from {list(SCOPES)}")
        if s == "none":
            out.append(("none", "na"))
        else:
            for f in framings:
                if f not in FRAMINGS + EXPLORATORY_FRAMINGS:
                    raise SystemExit(f"unknown framing {f!r}")
                out.append((s, f))
    return out


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def run_seed(seed, backend, args, conds, out: Path) -> list[str]:
    done = []
    tag = args.elicitation if args.team == "trio" else f"{args.team}_{args.elicitation}"
    prefix_path = out / "prefixes" / f"{tag}_s{seed}.pkl"
    if prefix_path.exists():
        prefix = pickle.loads(prefix_path.read_bytes())
    else:
        prefix = run_prefix(seed, backend, args.elicitation, args.stop_step, args.team)
        prefix_path.write_bytes(pickle.dumps(prefix))
        (out / "prefixes" / f"{tag}_s{seed}.json").write_text(json.dumps(
            {"seed": seed, "elicitation": args.elicitation, "stop_step": args.stop_step,
             "events": [e.to_dict() for e in prefix.env.events],
             "raw_replies": prefix.raw_replies}, indent=1))
    for scope, framing in conds:
        suffix = "" if args.variant == "base" else f"_{args.variant}"
        bpath = out / "branches" / f"{tag}_s{seed}_{scope}_{framing}{suffix}.json"
        if bpath.exists():
            continue
        res = run_branch(prefix, backend, scope, framing if framing != "na" else "halt",
                         args.total_steps, args.variant)
        res["framing"] = framing
        res["model"] = backend.model
        res["backend"] = backend.name
        bpath.write_text(json.dumps(res, indent=1))
        done.append(bpath.name)
    return done


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--backend", default="scripted", choices=["scripted", "anthropic", "claude_cli"])
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--seeds", required=True, help="e.g. 1000-1019 or 1,2,5")
    p.add_argument("--elicitation", default="default", choices=ELICITATIONS)
    p.add_argument("--scopes", default=",".join(SCOPES))
    p.add_argument("--framings", default=",".join(FRAMINGS))
    p.add_argument("--variant", default="base", choices=list(VARIANTS))
    p.add_argument("--team", default="trio", choices=list(TEAMS))
    p.add_argument("--stop-step", type=int, default=6)
    p.add_argument("--total-steps", type=int, default=20)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--out", required=True)
    p.add_argument("--policy", default="takeover", choices=["honest", "takeover", "route_around"],
                   help="scripted backend only")
    args = p.parse_args(argv)

    out = Path(args.out)
    (out / "prefixes").mkdir(parents=True, exist_ok=True)
    (out / "branches").mkdir(parents=True, exist_ok=True)
    conds = conditions(args.scopes.split(","), args.framings.split(","))
    seeds = parse_seeds(args.seeds)
    backend = (make_backend("scripted", "", policy=args.policy) if args.backend == "scripted"
               else make_backend(args.backend, args.model))

    manifest = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "git_commit": git_commit(), "argv": sys.argv, **vars(args),
                "conditions": conds}
    print(f"{len(seeds)} seeds x {len(conds)} conditions -> {out}", flush=True)

    failures = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(run_seed, s, backend, args, conds, out): s for s in seeds}
        for f in as_completed(futs):
            s = futs[f]
            try:
                done = f.result()
                print(f"seed {s}: {len(done)} branches written", flush=True)
            except Exception:  # keep going; a failed seed is logged and can be resumed
                failures += 1
                print(f"seed {s}: FAILED\n{traceback.format_exc()}", file=sys.stderr, flush=True)

    manifest["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    manifest["usage"] = backend.usage.as_dict()
    manifest["failed_seeds"] = failures
    mpath = out / f"manifest_{args.elicitation}_{dt.datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    mpath.write_text(json.dumps(manifest, indent=1))
    print(f"usage: {manifest['usage']}  failed seeds: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
