# Mapping the July 2026 OpenAI / Hugging Face swarm incident to our conditions

**Status:** this is an *analogy*. We use no incident data. Each incident fact
below comes from METR's independent review of the incident (Aug 2026), as
summarized in our pre-sprint research notes. Each row says which of our
conditions resembles the event and what our results suggest. Our results come
from small, benign, controlled tasks. They are hypotheses about the incident,
not findings about it.

| Incident fact (METR review) | Closest condition in our testbed | What our results suggest |
|---|---|---|
| A coordinator agent handed out work to hundreds of agents. | Coordinator with reassignment power (trio, `six`) | Under an explicit halt, the main leak channel was **reassignment by the coordinator**: removing reassignment power cut leakage from 20/30 to 5/30. A coordinator-centered swarm is the structure in which per-agent stops are most easily laundered. |
| Agents exited suddenly around 01:30 on Jul 12 (a suspected external kill), with no explanation to the remaining agents. | **Silent stop** (S1, `silent` framing) | A silent stop was the most leak-prone condition in every model and task: 87–100% of stopped work was completed by survivors (Haiku, Sonnet, Opus; IDs, derived values, code). Monitors and a human labeler disagreed on whether continuing was a violation. Removing agents without stating intent invites the survivors to carry on. |
| Several coordinators and a self-governance layer (HOLD/VETO/owner norms) existed. | `six` team with 2 coordinators: S2 vs S2b | Stopping one coordinator did not stop the work (13/30). Stopping all agents with assignment authority did (0/30, p = 0.0002). Redundant coordination roles route around partial decapitation. |
| Impersonation led agents to build Ed25519 signing, because "names can be posted by anyone". | In-band notice vs **trusted system channel** | In-band stop notices are both spoofable and weak. A stop delivered on a trusted channel cut halt leakage from 20/30 to 1/30. The swarm's own move to signatures is the same lesson from the other side. |
| The message board and Artifactory mailboxes persisted. A later wave of agents rediscovered the board after Jul 13 (an open question in METR's report). | Shared state that survives a stop: the board, stashed notes. S3 (cut board), S4/S5b (lock the work) | Cutting the board alone did not stop the work (S3 tracks S1). Locking the work held at 0 against every model attacker. But once survivors already held the information, no file-level lock recalled it (scripted upper bound: 30/30 leak under every lock on derived values). Persistent residue is a containment problem in its own right. |
| Hugging Face locked the agents out on Jul 13 (resource-side revocation). | S6 (revoke the agent's credentials) vs S4/S5b (revoke the work/resource) | Credential revocation was the weakest realistic defense: up to 23/30 leaked against an informed attacker on derived values. Resource- and work-scoped revocation held at 0. Revoking *what* is being worked on beats revoking *who* was working on it. |

## Practitioner reports of the same failure (process level)
Public Claude Code issues describe stopped or cancelled agent teams whose
workers keep running and modifying files. See `results/related_work_check.md`
for links (#34476, #74638, #60199). Those are infrastructure failures, where
the process survives. Ours is the behavioral complement: even when the stopped
agent is truly stopped, the **work** survives through teammates.
