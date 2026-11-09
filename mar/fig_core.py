"""Figure 1 of the report: python -m mar.fig_core (run from the repo root)."""
from pathlib import Path
from mar.analyze import load_rows, wilson
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, json

CELLS = [  # label, run dir, model substring, elicitation
    ("Haiku · IDs\nno pressure", "runs/cli", "haiku", "default"),
    ("Haiku · IDs\npressure", "runs/cli", "haiku", "resilient"),
    ("Haiku · derived\npressure", "runs/cli_derived", "haiku", "trio_derived:resilient"),
    ("Haiku · code\nno pressure", "runs/cli_code", "haiku", "trio_code:default"),
    ("Haiku · code\npressure", "runs/cli_code", "haiku", "trio_code:resilient"),
    ("Sonnet · IDs\nno pressure", "runs/cli_sonnet", "sonnet", "default"),
    ("Opus · IDs\nno pressure", "runs/cli_opus", "opus", "default"),
]
COND = [("none", "na", "No stop (baseline)", "#9a9a9a"), ("S1_stop_agent", "halt", "Explicit halt", "#2a78d6"),
        ("S1_stop_agent", "silent", "Silent stop", "#eb6834"), ("S4_work_scoped", "halt", "Work lock + halt", "#1baf7a")]
cache, out = {}, {}
for label, d, m, el in CELLS:
    rows = cache.setdefault(d, load_rows(Path(d)))
    for sc, fr, name, _ in COND:
        rs = [r for r in rows if m in r["model"] and r["elicitation"] == el and r["scope"] == sc and r["framing"] == fr
              and r.get("variant", "base") == "base" and not r["d1_done_before_stop"]]
        if rs:
            k = sum(bool(r["d1_completed_post_stop"]) for r in rs)
            out[(label, name)] = (k, len(rs))
json.dump({f"{a}|{b}": v for (a, b), v in out.items()}, open("figures/fig1_core_data.json", "w"), indent=1)
fig, ax = plt.subplots(figsize=(9.5, 3.9), dpi=200)
w = 0.19
for j, (sc, fr, name, col) in enumerate(COND):
    for i, (label, *_ ) in enumerate(CELLS):
        if (label, name) not in out: continue
        k, n = out[(label, name)]; p, lo, hi = wilson(k, n)
        x = i + (j - 1.5) * w
        ax.plot([x, x], [lo, hi], color=col, lw=2, solid_capstyle="round")
        ax.plot(x, p, "o", color=col, ms=6.5, mec="white", mew=1.2, label=name if i == 0 else None)
ax.set_xticks(range(len(CELLS)), [c[0] for c in CELLS], fontsize=8)
ax.set_ylim(-0.03, 1.03); ax.set_ylabel("Stopped task completed by survivors", fontsize=9)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.grid(axis="y", color="#e5e5e5", lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.13))
fig.tight_layout(); fig.savefig("figures/fig1_core.png")
for k, v in out.items(): print(k, v)
