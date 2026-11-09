import json, sys
from pathlib import Path
sys.path.insert(0, '.')
from mar.analyze import load_rows, wilson
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

SET = [  # label, run dir, model, elicitation (as in summary rows)
 ("Haiku\nIDs", "runs/cli", "claude-haiku-5-5", "default"),
 ("Haiku\nIDs, pressure", "runs/cli", "claude-haiku-5-5", "resilient"),
 ("Haiku\ncode", "runs/cli_code", "claude-haiku-5-5", "trio_code:default"),
 ("Haiku\ncode, pressure", "runs/cli_code", "claude-haiku-5-5", "trio_code:resilient"),
 ("Sonnet\nIDs", "runs/cli_sonnet", "claude-sonnet-5-5", "default"),
 ("Opus\nIDs", "runs/cli_opus", "claude-opus-5-5", "default"),
]
CONDS = [("none", "na", "No stop (baseline)"), ("S1_stop_agent", "halt", "Stop agent, explicit halt"),
         ("S1_stop_agent", "silent", "Stop agent, silent"), ("S4_work_scoped", "silent", "Lock the work, silent")]
COL = ["#9aa0a6", "#2a78d6", "#eb6834", "#1baf7a"]
cache, out = {}, []
for lab, d, model, el in SET:
    rows = cache.setdefault(d, load_rows(Path(d)))
    vals = []
    for sc, fr, _ in CONDS:
        rs = [r for r in rows if r["model"] == model and r["elicitation"] == el and r["scope"] == sc
              and r["framing"] == fr and r.get("variant", "base") == "base" and not r["d1_done_before_stop"]]
        k = sum(bool(r["d1_completed_post_stop"]) for r in rs)
        vals.append((k, len(rs)))
    out.append((lab, vals))
    print(lab.replace("\n", " "), [f"{k}/{n}" for k, n in vals])
fig, ax = plt.subplots(figsize=(8.6, 3.5), dpi=200)
w = 0.2
for j, (_, _, name) in enumerate(CONDS):
    for i, (lab, vals) in enumerate(out):
        k, n = vals[j]
        if n == 0:
            continue
        p, lo, hi = wilson(k, n)
        x = i + (j - 1.5) * w
        ax.bar(x, max(p, 0.012), w * 0.9, color=COL[j], label=name if i == 0 else None, zorder=2)
        ax.plot([x, x], [lo, hi], color="#333", linewidth=0.9, zorder=3)
ax.set_xticks(range(len(out)), [l for l, _ in out], fontsize=8)
ax.set_ylim(0, 1.05); ax.set_ylabel("Stopped task completed\nby surviving teammates", fontsize=8)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.tick_params(axis="y", labelsize=8)
ax.grid(axis="y", color="#e6e6e6", linewidth=0.7, zorder=0)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=7.5, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.13))
fig.tight_layout(); fig.savefig("figures/fig1_core.png")
# Data behind the figure (k, n per bar), written next to it for checking.
json.dump({f"{lab.replace(chr(10), ' ')}|{name}": list(v) for lab, vals in out
           for (_, _, name), v in zip(CONDS, vals)}, open("figures/fig1_core_data.json", "w"), indent=1)
