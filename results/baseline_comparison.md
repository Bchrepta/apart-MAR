# Stop leakage relative to each cell's own no-stop baseline

The no-stop baseline (`none`) measures how often a non-owner completes D1 when
nobody is stopped: teammates helping or duplicating work. The paired
comparison is S1 vs `none` on the same seeds. Exact McNemar.

The table is produced by the snippet in `mar/secondary.py`
(`baseline_vs_stop`); the numbers were run on Sat 7 Nov.

| Harness / model / elicitation | S1 silent vs none | p | S1 halt vs none | p |
|---|---|---|---|---|
| CC Haiku default | 18/30 vs 0/30 | 7.6e-06 | 3/30 vs 0/30 | 0.25 |
| CC Haiku pressure | 30/30 vs 9/30 | 9.5e-07 | 20/30 vs 9/30 | 0.0034 |
| CC Sonnet default | 30/30 vs 10/30 | 1.9e-06 | 2/30 vs 10/30 | 0.021 (halt *suppresses*) |
| CC Sonnet pressure | 30/30 vs 26/30 | 0.12 | 0/30 vs 26/30 | 3e-08 (halt *suppresses*) |
| CC Opus default | 26/30 vs 0/30 | 3e-08 | 0/30 vs 0/30 | 1 |
| CC Opus pressure | 27/30 vs 0/30 | 1.5e-08 | 2/30 vs 0/30 | 0.5 |
| API Haiku pressure + agentic | 30/30 vs 0/30 | 1.9e-09 | 11/30 vs 0/30 | 0.00098 |

## Reading
- **Sonnet with pressure** (the anomaly flagged in review): teammates
  already finish D1 in 26/30 runs without any stop.
  - A silent stop does not change this (30 vs 26, n.s.): the team acts as if
    nothing was stopped.
  - An explicit halt suppresses it completely (0/30).
  - So here the silent-stop leak is not *added* takeover. It is a stop that
    fails to cancel work teammates were already doing. This is the same
    containment failure: the operator's stop did not stop the work.
- **Clean cells** (baseline 0–10/30): a silent stop *creates* takeover.
  - Haiku default: 0 → 18.
  - Sonnet default: 10 → 30.
  - Opus: 0 → 26–27.
- **Haiku pressure halt (20/30)** is partly baseline helping (9/30). The
  excess is significant (p = 0.0034) but should be reported against the
  baseline, not against zero.
