# Paper C (working name): sequential control of governed autoresearch loops — the plan as it stands

**As of 26 Nov 2026. AI-assisted (coordinating chat, Claude).** A view, not an authority: the R1-PAPERC-* rows of
`docs/r1/PLAN.md` §10 control. It introduces no decision.

**Where the material is.** Not on `main`. The latest line is branch `paperc-esyn-scaling-20261122` (folder `paperC/`,
18 R1-PAPERC rows in that branch's PLAN). Two branches are not in that line and conflict with it:
`codex/paperc-theory-20261117` and `mac-paperc-rl-20261121`. One consolidated branch on current `main` is queued with
the local worker, at the lowest priority. Paper C is not on Paper B's critical path.

## 1. Topic

Paper B studies each decision of the loop on its own and states the conditions (no feedback, no information, fixed
price) under which the loop reduces to one-step decisions. In the real loop those conditions fail: the budget binds,
a run tells something about later edits, edits interact with the incumbent, the proposer reacts to what was kept, and
the recorded incumbent carries a shared error. Paper C asks where non-myopic control is worth anything, through which
channel, and whether multi-step RL or a language decision model adds anything beyond strong non-RL sequential methods.
After Track S ended at STOP 4 it is framed as a map of where sequential control pays (R1-PAPERC-REFRAME).

## 2. Questions

| ID | Question | Status in the core version |
|---|---|---|
| Q1 | Does non-myopic control beat the tuned static rule on whole campaigns? | confirmatory |
| Q2 | With the same immediate estimate, does a continuation term help beyond a level shift? | secondary |
| Q3 | Does multi-step RL beat the strongest non-RL multi-step method at matched information, data and budget (superiority or TOST equivalence at a pre-declared δ)? | confirmatory only after a passed go/no-go |
| Q4 | Does a decision model that reads the proposal text add value in the multi-step policy? | secondary |
| Q5 | Which channel produces the gain: budget, information, feedback, interaction, shared incumbent error? | secondary |
| OPD | Does on-policy distillation beat offline distillation and sparse-return RL at equal interaction? | open (P10) |

## 3. Approach

- **Sequential Policy Track.** Transitions logged under a behaviour mixture plus repeated fork trees; a fixed method
  ladder trained and selected on development instances; frozen arms tested on fresh campaigns with fresh-seed audits.
- **Environments.** E-SYN: synthetic worlds with one channel on at a time and exact or certified oracles. E-T0:
  `digits_mlp` and `tabular_mlp`. E-INT: one interaction-rich GPU task, descriptive.
- **Methods.** Non-RL rungs on one frozen belief (N0 execute-all, N1 tuned static, N2 myopic, N2b action head, N3
  non-myopic thresholds, N4 budget DP, N6 fork-Q regression); offline RL (R0 fitted Q iteration, R1 IQL); language-model
  routes on Paper B's decision models (M1 offline distillation in the core; M2, M3, M4 as extensions).
- **Proposer of record.** `gemma4_31b`, thinking off, as in Paper B (R1-PAPERC-PROPOSER).
- **Statistics.** Unit: the campaign instance, paired. Q1 and Q3 at α = 0.025 each, Holm across nodes;
  δ_n = max(0.002, 0.25 · s̃_n) on E-T0 (R1-PAPERC-DELTA, R1-PAPERC-EQUIV-DESIGN).
- **Core version (first submission).** E-SYN and the two E-T0 nodes; Q1 confirmatory; Q3 as above.

## 4. State

| Item | State |
|---|---|
| Decisions | 18 rows, 15 to 22 Nov: proposer, δ, OPD, no waiting for Paper B, home folder, reframing, census first, go/no-go, relevance gate, equivalence design, measure first, OPE support, fork-restore fidelity, estimand and guards, scope, harness pin (`a3fedbbd`) |
| Build | Phases P0 to P9 accepted by independent review (schema, seed registry, headroom census, E-SYN with exact DP and certified oracle, policies, relevance, fork validation, OPE, learners, power); 234 tests |
| Data | ENGINEERING_ONLY. No real-node run. In the E-SYN budget world the best static rule takes 91.8 % of the gap between N1 and the DP oracle |
| Manuscript | none |

## 5. Next

1. Consolidate the six branches into one on current `main`; PLAN rows as additions only.
2. The two CPU measurements of R1-PAPERC-MEASURE-FIRST, each with its runbook, review and authorization; then
   R1-PAPERC-CORE (nodes and channels of the core version).
3. A manuscript skeleton (sections, planned figures).

## 6. What Paper B hands over

- The external reviews of 26 Nov ask for exploration-aware and information-aware control. Paper B does not build
  them. Its closed loop records value skips, proposal diversity and the offline–online agreement of the arms
  (R1-D3-OUTCOMES2); those results are inputs to Paper C's channel question Q5.
- D.3's instances, seeds and ledgers follow Paper B's seed registry, which Paper C's registry already excludes.
