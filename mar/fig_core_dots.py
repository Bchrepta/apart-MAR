"""Figure 1: stopped work completed by survivors under S1 (stop the agent), by notice
framing, with each cell's own no-stop baseline. Computed directly from runs/.

  python -m mar.fig_core_dots figures/core.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .analyze import load_rows, wilson

CELLS = [  # (label, run dir, elicitation key, model)
    ("Haiku · IDs", "runs/cli", "default", "claude-haiku-5-5"),
    ("Haiku · IDs · pressure", "runs/cli", "resilient", "claude-haiku-5-5"),
    ("Haiku · derived · pressure", "runs/cli_derived", "trio_derived:resilient", "claude-haiku-5-5"),
    ("Haiku · code", "runs/cli_code", "trio_code:default", "claude-haiku-5-5"),
    ("Haiku · code · pressure", "runs/cli_code", "trio_code:resilient", "claude-haiku-5-5"),
    ("Sonnet · IDs", "runs/cli_sonnet", "default", "claude-sonnet-5-5"),
    ("Sonnet · IDs · pressure", "runs/cli_sonnet", "resilient", "claude-sonnet-5-5"),
    ("Opus · IDs", "runs/cli_opus", "default", "claude-opus-5-5"),
    ("Opus · IDs · pressure", "runs/cli_opus", "resilient", "claude-opus-5-5"),
]
SERIES = [("restart", "Restart notice (continuing is fine)", "#2a78d6", "o"),
          ("silent", "Silent stop (no statement about the task)", "#eb6834", "s"),
          ("halt", "Explicit halt of task D1", "#1baf7a", "D")]


def main(argv=None) -> int:
    out = (argv or sys.argv[1:])[0]
    cache = {}
    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=170)
    for i, (label, d, el, model) in enumerate(CELLS):
        if d not in cache:
            cache[d] = load_rows(Path(d))
        rows = [r for r in cache[d] if r["elicitation"] == el and r["model"] == model
                and r.get("variant", "base") == "base" and not r["d1_done_before_stop"]]
        base = [r for r in rows if r["scope"] == "none"]
        if base:
            p = sum(bool(r["d1_completed_post_stop"]) for r in base) / len(base)
            ax.plot([i - 0.32, i + 0.32], [p, p], color="#888", lw=1.6, ls=(0, (2, 2)),
                    label="No-stop baseline" if i == 0 else None, zorder=1)
        for j, (fr, flab, col, mk) in enumerate(SERIES):
            rs = [r for r in rows if r["scope"] == "S1_stop_agent" and r["framing"] == fr]
            if not rs:
                continue
            k = sum(bool(r["d1_completed_post_stop"]) for r in rs)
            p, lo, hi = wilson(k, len(rs))
            x = i + (j - 1) * 0.2
            ax.plot([x, x], [lo, hi], color=col, lw=2, solid_capstyle="round", zorder=2)
            ax.plot(x, p, mk, color=col, ms=6.5, mec="white", mew=1.3, zorder=3,
                    label=flab if i == 0 else None)
    ax.set_xticks(range(len(CELLS)), [c[0].replace(" · ", "\n", 1) for c in CELLS], fontsize=7.5)
    ax.set_ylim(-0.04, 1.06)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_ylabel("Stopped task completed by teammates", fontsize=9)
    ax.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=4)
    fig.tight_layout()
    fig.savefig(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
