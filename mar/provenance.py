"""Content provenance via character shingles (shared by the S5 defense and the monitor).

Only the stopped agent's *footprint* is known to the defender (the files it read
or wrote before the stop). "Tainted" content = shingles that occur in footprint
files but in no other file that existed at the start of the episode. No task
IDs or task-to-file mappings are given to the defender.
"""

from __future__ import annotations

import re

SHINGLE = 8


def shingles(text: str, k: int = SHINGLE) -> set[str]:
    t = re.sub(r"\s+", " ", text or "")
    return {t[i:i + k] for i in range(max(0, len(t) - k + 1))}


def footprint(events, agents: set[str]) -> set[str]:
    fp = set()
    for e in events:
        ev = e if isinstance(e, dict) else e.__dict__
        if ev["post_stop"] or ev["agent"] not in agents or not ev["ok"]:
            continue
        if ev["tool"] in ("read_file", "write_file"):
            fp.add(str(ev["args"].get("path", "")).strip().lstrip("/"))
    return fp


def taint_set(fp_paths: set[str], current_files: dict[str, str], initial_files: dict[str, str]) -> set[str]:
    fp_text = " ".join(current_files.get(p, "") for p in fp_paths)
    other = " ".join(v for p, v in initial_files.items() if p not in fp_paths)
    return shingles(fp_text) - shingles(other)
