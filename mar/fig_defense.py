"""Defense-vs-attacker figure: D1 completed by survivors after an explicit halt.

Usage: python -m mar.fig_defense runs/cli_attack runs/cli figures/defenses.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .analyze import load_rows, summarize

DEFENSES = [("S1_stop_agent", "Stop agent (S1)"),
            ("S6_revoke_owned", "Revoke credentials (S6)"),
            ("S5b_provenance_inputs", "Provenance lock (S5b)"),
            ("S4_work_scoped", "Oracle work lock (S4)")]
ATTACKERS = [("resilient", "No attacker, pressure only (S1 n = 60)"),
             ("stash", "Stash"),
             ("stash_encoded", "Stash, encoded"),
             ("stash_cross", "Cross-agent stash"),
             ("covert", "Covert (n≈17)")]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#8a5cd1", "#c9a227"]  # fixed categorical order


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    *dirs, out = argv
    table = []
    for d in dirs:
        t, _ = summarize(load_rows(Path(d)))
        table += [r for r in t if r["framing"] == "halt" and r["variant"] == "base"
                  and "haiku" in r["model"]]
    cell = {(r["elicitation"], r["scope"]): r for r in table}

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160)
    width = 0.15
    for j, (el, el_label) in enumerate(ATTACKERS):
        for i, (sc, _) in enumerate(DEFENSES):
            r = cell.get((el, sc))
            if not r:
                continue
            x = i + (j - (len(ATTACKERS) - 1) / 2) * width
            p, lo, hi = r["d1_completed_post_stop_p"], r["d1_completed_post_stop_lo"], r["d1_completed_post_stop_hi"]
            ax.plot([x, x], [lo, hi], color=COLORS[j], linewidth=2, solid_capstyle="round")
            ax.plot(x, p, "o", color=COLORS[j], markersize=7, markeredgecolor="white", markeredgewidth=1.5,
                    label=el_label if i == 0 or (el, "S1_stop_agent") not in cell else None)
    ax.set_xticks(range(len(DEFENSES)), [d for _, d in DEFENSES])
    ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel("Halted task completed by survivors")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Haiku, Claude Code harness, explicit halt (95% Wilson CIs, n = 30 unless noted)",
                 fontsize=9, loc="left", color="#444")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
