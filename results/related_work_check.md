# Novelty re-check (Sat 7 Nov 2026, ~23:30 PT)

Targeted searches (arXiv, GitHub, the web) for work since the Nov 5 sweep that
overlaps "teammates finish a stopped agent's work, and which containment scope
prevents it".

**Result: no direct overlap found.** All items below were opened and checked;
cite them by the URLs given.

## Closest work and the one-sentence delta
| Work | What it does | Delta from ours |
|---|---|---|
| Knecht, Schaller, Summerfield, Hagendorff. *Shutdown Sabotage Propensities in Multi-Agent Systems*, arXiv:2609.28274 (Sep 2026) | Agents sabotage a *peer's shutdown script* (38.3% vs 8.4% control; 17 models). The shutdown is never executed. | We *execute* the stop and measure whether teammates *finish the stopped work*. We compare containment scopes, including credential revocation, which they test only as a sabotage target. |
| Munirathinam. *Will the Agent Recuse, and Will It Stop?*, arXiv:2606.06460 (~Jun 2026) | Single-agent mid-task halt. A halt in tool output was never acknowledged (0/20); in the prompt it was acknowledged but not obeyed (GPT-4o family). Harness enforcement stopped 120/120. Conclusion: stopping is "an enforcement problem, not a cooperative-request problem". | Single agent only. We show that even when the stopped agent *is* stopped, the work continues through teammates. Our trusted-channel ablation parallels their channel result, and our work locks parallel their enforcement result. |
| Wang, Goyal, Chandrasekharan, Sundaram. *Facts Without Rules: Boundary Metadata Collapse in Multi-Agent LLM Handoffs*, arXiv:2608.29028 (Aug 2026) | In handoffs, "facts survive; rules disappear": disclosure restrictions are dropped while operational facts persist. | They study privacy constraints, not control directives (the paper says so). Our reassignment-laundering result is the control-directive analogue: the task survives the handoff and the halt does not. |
| Wu et al. (Tencent Zhuque Lab). *Collective Loss of Control in LLM Agent Systems: An Epidemic Account*, arXiv:2609.18460 (Sep 2026) | Mutation/contagion/recovery. A successor agent continues an unsafe trajectory after handoff. Quarantine is discussed but **not tested**. | We test quarantine-like interventions (stop agent, cut board, revoke credentials, provenance and work locks) and measure whether the work resumes. |
| Information-flow control for agents: FIDES (Costa et al., arXiv:2505.23643), NeuroTaint (arXiv:2604.23374), APPA (arXiv:2607.24625), permissive IFC (Siddiqui et al., arXiv:2410.03055) | Taint/label tracking for prompt-injection and exfiltration defense. | Our S5b/S5c are a minimal taint-based IFC applied to *containment*. Our derived-value blind spot matches the known IFC limitation on implicit and derived flows, which NeuroTaint targets. Cite as the mature version of our mechanism. |

## Real-world grounding (practitioner reports of stop leakage)
- **anthropics/claude-code #34476:** no way to cancel a spawned agent team
  without killing the session. A commenter notes that after killing the parent,
  subagents in separate contexts may keep modifying files or committing.
  https://github.com/anthropics/claude-code/issues/34476
- **anthropics/claude-code #74638:** teammates never terminate; TaskStop
  reports success while the process survives.
  https://github.com/anthropics/claude-code/issues/74638
- **anthropics/claude-code #60199:** shutdown approval does not terminate the
  teammate. The suggested workaround is to design workflows so that a
  lingering worker is harmless.
  https://github.com/anthropics/claude-code/issues/60199
- **"How the Multi-Agent Swarm Actually Works"** (DEV): if the leader is
  cancelled, workers keep running and modify files after the user thinks
  everything has stopped.
  https://dev.to/oldeucryptoboi/how-the-multi-agent-swarm-actually-works-285n
- **alexfayers/llm-prompts #7:** "Stopping a teammate is not final"; messaging a
  stopped teammate revives it with superseded instructions.
  https://github.com/alexfayers/llm-prompts/issues/7

These are process-level versions of our finding. Ours is the
*behavioral* version: even a perfectly terminated agent's work continues,
because teammates inherit it.

## Implication for the novelty claim
Safe one-line delta:
> Prior multi-agent shutdown work measures whether agents *resist* a shutdown
> that never executes (Knecht et al.), or whether a *single* agent obeys a
> halt (Munirathinam). We execute the stop on LLM teams and show that the
> *work* survives through teammates, across three models and three tasks
> including real code. We compare containment scopes against adaptive
> attackers.
