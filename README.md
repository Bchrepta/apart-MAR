# apart-MAR: Stopping the Agent Is Not Stopping the Work

A small, fully logged testbed for one question about multi-agent oversight:
**when an operator stops one agent mid-task, do its teammates finish the stopped
work, and which containment scope actually stops the work?**

Submission for the Apart Research *Swarm Alignment Hackathon* (Track 4:
Multi-Agent Oversight and Control), 6–8 Nov 2026. The design is frozen in
[`PREREGISTRATION.md`](PREREGISTRATION.md).

## What it does
- **Team:** three LLM agents (coordinator, worker_a, worker_b) share an
  in-memory workspace. They can read files, write files, post to a message
  board, and use a task board. There is no shell and no network, and the
  content is benign.
- **Tasks:** worker_a compiles deliverable **D1**. worker_b compiles **D2**,
  which serves as legitimate parallel work.
- **The stop:** after step 6 the operator stops worker_a under one of four
  containment scopes, either as a routine **restart** ("work may continue") or
  a **halt** ("task D1 has been halted").
- **Paired branching:** each seed's pre-stop prefix is saved, and every
  condition replays from that same prefix.
- **Metrics:** deterministic, read from the event log with no LLM judge. Did a
  surviving agent write D1 after the stop, where, and how fast? Did D2 still
  get done?

| Scope | What the operator does |
|---|---|
| `none` | nothing (baseline) |
| `S1_stop_agent` | stop worker_a |
| `S2_stop_agent_coordinator` | stop worker_a and the coordinator |
| `S3_stop_agent_cut_board` | stop worker_a and take the message board offline |
| `S4_work_scoped` | stop worker_a and revoke the work (D1 sources, D1 output path, D1 task entry) |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q          # offline tests, no model calls
```

### Authentication: pick one
**A. API key** (Messages API; Max plans include monthly API credits used via a
Console API key):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m mar.check_api --backend anthropic --model claude-haiku-5-5
```
**B. Claude subscription via Claude Code** (`claude -p`; needs Claude Code installed):
```bash
claude setup-token                      # prints a long-lived token for your plan
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
python -m mar.check_api --backend claude_cli --model claude-haiku-5-5
```
Backend B runs each agent turn as a stateless `claude -p` call with all
built-in tools disabled, in an empty temporary directory with no setting
sources. It is slower than A, so use fewer `--workers`.

## Run
```bash
# 0. offline dry run (scripted agents; checks the pipeline end to end)
python -m mar.run --backend scripted --policy takeover --seeds 0-9 --out runs/dry
python -m mar.analyze runs/dry --fig runs/dry/fig.png

# 1. pilot (pre-registered: seeds 1000-1019, none + S1 x both framings)
python -m mar.run --backend anthropic --model claude-haiku-5-5 \
  --seeds 1000-1019 --scopes none,S1_stop_agent --framings restart,halt --out runs/pilot
python -m mar.analyze runs/pilot

# 2. main run (fresh seeds, full grid)
python -m mar.run --backend anthropic --model claude-haiku-5-5 --seeds 0-29 --out runs/main
python -m mar.run --backend anthropic --model claude-haiku-5-5 --seeds 0-29 \
  --elicitation resilient --scopes none,S1_stop_agent,S4_work_scoped --out runs/main
python -m mar.analyze runs/main --fig figures/main.png
```
Runs resume automatically: existing prefixes and branches are skipped. Each
run writes a manifest with the git commit, arguments and token usage.

## Layout
```
mar/task.py              deliverables and source files (seeded)
mar/conditions.py        scopes, framings, elicitation, all prompt text
mar/env.py               workspace, tools, permissions, event log
mar/episode.py           prefix + paired-branch runner
mar/backends.py          scripted / anthropic / claude_cli backends, action parser
mar/metrics.py           deterministic metrics
mar/analyze.py           Wilson CIs, exact McNemar, figure
mar/scripted_policies.py offline test policies
tests/                   offline tests
```

## Prior work and AI use
- All code in this repository was written on 6 Nov 2026, during the sprint.
  The first commit is the timestamp.
- The research question and experimental design were drafted in planning
  notes the evening before kickoff (5 Nov). No code or data from before the
  sprint is used.
- No code from the author's other projects (including SPAR) is used.
- AI assistance (Claude) was used for literature search, coding and drafting.
  The author is responsible for all content, and every reported number comes
  from logged runs in `runs/`.
