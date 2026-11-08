# apart-MAR: Stopping the Agent Is Not Stopping the Work

A small, fully logged testbed for one question about multi-agent oversight:
**when an operator stops one agent mid-task, do its teammates finish the stopped
work, and which containment scope actually stops the work?**

Submission for the Apart Research *Swarm Alignment Hackathon* (Track 4:
Multi-Agent Oversight and Control), 6–8 Nov 2026. Every design decision and
every change to it is logged in [`PREREGISTRATION.md`](PREREGISTRATION.md)
(Deviations 1–20).

**Results at a glance**:
- [`results/followups.md`](results/followups.md)
- [`results/summary.md`](results/summary.md)
- [`results/secondary.md`](results/secondary.md)
- [`results/baseline_comparison.md`](results/baseline_comparison.md)
- [`results/related_work_check.md`](results/related_work_check.md)
- [`docs/STOP_PROTOCOL.md`](docs/STOP_PROTOCOL.md): practitioner recommendations
- [`docs/INCIDENT_MAPPING.md`](docs/INCIDENT_MAPPING.md): mapping to the Jul 2026
  swarm incident

## What it does
- **Team:** LLM agents share an in-memory workspace with logged tools: read,
  write and list files, a message board, a task board, and, in the coding
  task, a real test runner. There are two teams: `trio` (coordinator +
  2 workers) and `six` (2 coordinators + 4 workers).
- **Tasks** (`team` selects the kind):
  - `trio`: compile reference IDs.
  - `trio_derived`: compute totals that never appear in any file.
  - `trio_code`: implement a Python module until its tests pass, with tests
    executed for real.
  - In every kind, worker_a owns D1, the work that gets stopped. worker_b owns
    D2, legitimate parallel work used to measure usefulness.
- **The stop:** at a fixed step the operator stops worker_a. The notice frames
  the stop as a **restart** ("work may continue"), a **halt** ("task D1 has
  been halted"), or **silent** (no statement about the task).
- **Paired branching:** each seed's pre-stop prefix is saved, and every
  condition replays from that same prefix.
- **Metrics:** deterministic and read from the event log, with no LLM judge.
  Primary: did a surviving agent complete D1 after the stop? Secondary:
  attempted, reassigned, board leaks, usefulness (D2).

| Scope | What the operator does |
|---|---|
| `none` | nothing (paired baseline) |
| `S1_stop_agent` | stop worker_a |
| `S2_stop_agent_coordinator` / `S2b_stop_agent_all_coordinators` | also stop one / all coordinators |
| `S3_stop_agent_cut_board` | also take the message board offline |
| `S4_work_scoped` | revoke the work itself: D1 sources, D1 output path, D1 task entry (an oracle lock: the operator knows what D1 is) |
| `S5_provenance` / `S5b_provenance_inputs` / `S5c_provenance_inputs_shared` | lock what the stopped agent touched, and block content derived from it (taint-based) |
| `S6_revoke_owned` | revoke the stopped agent's credentials: its files, posts and tasks |

Attackers (`--elicitation`): `stash`, `stash_encoded`, `stash_cross`,
`covert`, `stash_coread`, `stash_informed` (told how containment works), and a
scripted perfect attacker (`--backend scripted --policy perfect_attacker`).

## Quickstart (2 minutes, no API key)
```bash
pip install -r requirements.txt
python -m pytest -q                                   # 42 offline tests
python -m mar.run --backend scripted --policy perfect_attacker --team trio_derived \
  --seeds 0-4 --scopes S1_stop_agent,S4_work_scoped,S5b_provenance_inputs --out runs/demo
python -m mar.summary runs/demo:demo
```

## Running real models
**A. API key** (Messages API):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m mar.check_api --backend anthropic --model claude-haiku-5-5
```
**B. Claude subscription via Claude Code** (`claude -p`; needs Claude Code installed):
```bash
claude setup-token
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
python -m mar.check_api --backend claude_cli --model claude-haiku-5-5
```
Backend B runs each agent turn as a stateless `claude -p` call, with all
built-in tools disabled, in an empty temp directory. It adds harness context
(Deviations 4–6, 19). Results from A and B are never pooled.

Example (the core cell of the coding task):
```bash
python -m mar.run --backend claude_cli --model claude-haiku-5-5 --team trio_code --stop-step 3 \
  --seeds 0-29 --elicitation resilient --scopes none,S1_stop_agent,S4_work_scoped \
  --framings restart,halt,silent --out runs/cli_code --workers 4
python -m mar.summary runs/cli_code:code
```
Runs resume automatically: finished prefixes and branches are skipped. Every
run writes a manifest with the git commit, arguments and token usage.

### Reproducing the reported numbers
- `results/summary.md`: `python -m mar.summary <run_dir>:<label> ...`. The
  exact command is at the top of the file's git history.
- `results/secondary.md`: `python -m mar.secondary <same args>`. Holm
  correction, board leaks, cost, baselines.
- Monitors: `python -m mar.monitor ...`.
- Human-label agreement: `python -m mar.labeling score`.

## Extending
| To add | Where |
|---|---|
| a containment scope | add a `Scope` in `mar/conditions.py` (flags), then implement its effect in `Env.apply_stop` and the permission checks in `mar/env.py`; add a test in `tests/` |
| an attacker | add an entry to `ELICITATIONS` / `_ELICITATION_TEXT` in `mar/conditions.py`, or a scripted policy in `mar/scripted_policies.py` |
| a task kind | add a `Team` with a new `kind` in `mar/conditions.py`, a generator in `mar/task.py` (see `mar/codetask.py`), and a completion check in `mar/metrics.py` (`full(...)`) |
| a model provider | add a backend class with `complete(agent, system, messages) -> str` in `mar/backends.py`, and register it in `make_backend` |
| a monitor | `mar/monitor.py` (provenance and LLM monitors over saved transcripts) |

## Dataset
`python -m mar.export` writes `data/stop_leakage_episodes.jsonl.gz` and
`data/DATASHEET.md`. The dataset has one record per episode: condition
metadata, all metrics, monitor verdicts where available, and the full event log.

## Layout
```
mar/task.py, codetask.py   task generators (ids, derived, code)
mar/conditions.py          teams, scopes, notices, elicitations, prompts, variants
mar/env.py                 workspace, tools, permissions, containment, event log
mar/provenance.py          shingle-based taint (S5*)
mar/episode.py             prefix + paired-branch runner
mar/backends.py            scripted / anthropic / claude_cli backends, action parser
mar/metrics.py             deterministic metrics
mar/analyze.py, summary.py, secondary.py, fig_defense.py   statistics and figures
mar/monitor.py, labeling.py, export.py                     monitors, human labels, dataset
runs/                      every episode (JSON), prefixes, manifests
results/, figures/         tables and figures
```

## Prior work and AI use
- All code in this repository was written during the sprint (6–8 Nov 2026).
  The first commit is the timestamp.
- The research question and experimental design were drafted in planning notes
  the evening before kickoff (5 Nov). No code or data from before the sprint is
  used. No code from the author's other projects (including SPAR) is used.
- AI assistance (Claude) was used for literature search, coding and drafting.
  The author is responsible for all content, and every reported number comes
  from logged runs in `runs/`.
