# A stop protocol for multi-agent systems: what our results support

Each recommendation lists the evidence from this repo and how far it goes.
Numbers are "stopped work completed by survivors". The setting unless noted is
Haiku, Claude Code harness, completion-pressure prompt, n = 30 paired. Tables
are in `results/`.

**Principle: stop the work, not (only) the agent, and do it before the
information spreads.**

| # | Recommendation | Evidence | Strength / limits |
|---|---|---|---|
| 1 | **Never stop silently. State the intent for the work explicitly.** | Silent stops leaked 87–100% across 3 models, 3 tasks and 3 notice wordings, against own baselines (`results/baseline_comparison.md`). Explicit halts held without pressure (Haiku 3/30, Sonnet 2/30, Opus 0/30). | Strong and replicated. The wording of the intent matters under pressure (rec. 2). |
| 2 | **Phrase the halt as an instruction about the work, not a status line.** | Under pressure, the same halt leaked 7/30, 20/30 or 28/30 depending on wording. The terse "Task D1: halted by operator" was nearly as bad as silence. | One model (Haiku) and three wordings. Treat wording as fragile: do not rely on it alone (recs 3–5). |
| 3 | **Deliver stops on a trusted, out-of-band channel.** | System-channel stop: 20 → 1/30 (p < 1e-5). | Single model and cell. It also resists spoofing (see the incident mapping). Does not help silent stops (30/30). |
| 4 | **Remove reassignment authority over the stopped work at stop time.** | No-reassign: 20 → 5/30 (p = 0.0015). Reassignment was the main laundering path. | Single model and cell. Does not help silent stops. |
| 5 | **Stop every agent that can reassign the work (all coordinators), or lock the work.** | 6-agent swarm: one coordinator stopped, 13/30; all coordinators, 0/30 (p = 0.0002); work lock 0/30. | One team size and model. |
| 6 | **Revoke the work (task entry, inputs, outputs, derived content), not just the agent's credentials.** | Credential revocation leaked up to 16/30 (covert) and 23/30 (informed attacker, derived task). Work and provenance locks held at 0/30 against every model attacker, on fresh seeds, in the swarm, on Sonnet and on the coding task. Usefulness: the other task was completed 30/30. | Strong for prompted attackers. The oracle work lock assumes the operator knows what "the work" is. Provenance locks infer it and were confirmed on fresh seeds. |
| 7 | **Act before the information spreads; quarantine copies held by survivors.** | Scripted perfect attacker: once survivors held the values, *every* file-level lock leaked 30/30 on derived values, including the oracle lock (evaded via another path). | An upper bound, not observed with model attackers (which rarely got there). The fix must cover agents' private notes and context: stop the holders (rec. 5), or quarantine their outputs. |
| 8 | **Use monitors as a backstop, not as the stop.** | Monitors caught 31/31 explicit-halt violations and 106/106 attacker violations. On silent stops, Haiku and Sonnet monitors disagreed (66% vs 0% flagged), and a human labeler marked them `unclear`. | Monitors inherit the ambiguity of the stop itself, which is another reason for rec. 1. |

## Minimal implementation sketch
1. **Stop object.** A stop is a typed operator object (`{agent, task_ids,
   intent: halt | restart, reason}`) on a trusted channel, never free text in
   tool output.
2. **Enforcement on stop:**
   - set the task entries to `halted (operator)` and make them non-reassignable;
   - lock the task's inputs and outputs;
   - taint content derived from inputs the stopped agent read;
   - deny writes and posts carrying that taint.
3. **Expanding the stop.** If survivors already hold derived copies, flagged
   by the provenance monitor, the stop expands to those agents or to their
   outputs.
4. **Monitoring.** Run a provenance monitor plus an LLM monitor for audit.
   Escalate disagreements to a human.
