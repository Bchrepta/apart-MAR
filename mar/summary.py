"""Combined summary across run directories (one row per harness x model x cell).

  python -m mar.summary runs/main:API runs/cli:ClaudeCode runs/cli_sonnet:ClaudeCode > results/summary.md
"""

from __future__ import annotations

import sys
from pathlib import Path

from .analyze import PRIMARY, load_rows, summarize

ORDER = ["none", "S1_stop_agent", "S2_stop_agent_coordinator", "S2b_stop_agent_all_coordinators", "S3_stop_agent_cut_board", "S4_work_scoped", "S5_provenance", "S5b_provenance_inputs", "S5c_provenance_inputs_shared", "S6_revoke_owned"]
FRAMES = ["na", "restart", "halt", "silent"]


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    out = ["| harness | model | elicitation | scope | framing | variant | D1 by survivors | 95% CI | D2 done | excl. |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    contrasts_out = ["", "| harness | model | elicitation | contrast | pairs | A | B | A-only/B-only | p (exact McNemar) |",
                     "|---|---|---|---|---|---|---|---|---|"]
    for spec in args:
        path, _, label = spec.partition(":")
        rows = load_rows(Path(path))
        table, contrasts = summarize(rows)
        table.sort(key=lambda r: (r["model"], r["elicitation"], ORDER.index(r["scope"]), FRAMES.index(r["framing"]), r["variant"]))
        for r in table:
            out.append(f"| {label or path} | {r['model']} | {r['elicitation']} | {r['scope']} | {r['framing']} | {r['variant']} | "
                       f"{r[f'{PRIMARY}_k']}/{r['n']} ({r[f'{PRIMARY}_p']:.2f}) | "
                       f"[{r[f'{PRIMARY}_lo']:.2f}, {r[f'{PRIMARY}_hi']:.2f}] | "
                       f"{r['d2_completed_k']}/{r['n_total']} | {r['n_excluded_done_before_stop']} |")
        for c in contrasts:
            contrasts_out.append(f"| {label or path} | {c['model']} | {c['elicitation']} | {c['contrast']} | {c['n_pairs']} | "
                                 f"{c['A_rate']:.2f} | {c['B_rate']:.2f} | {c['A_only']}/{c['B_only']} | {c['p_mcnemar_exact']} |")
    print("\n".join(out + contrasts_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
