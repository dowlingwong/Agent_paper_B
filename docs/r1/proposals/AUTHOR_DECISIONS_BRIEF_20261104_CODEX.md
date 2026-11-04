# Author decision briefing — recorded replies and open Mac packet items (4 November 2026)

AI-assisted (Codex). This is an explanatory draft, not an authorization or a decision. It summarizes `AUTHOR_DECISIONS_20261104.md` sections (b), (c), (h), (i), and (j), with later PLAN rows taking precedence. Proposed recommendations are not author decisions. Operational tests and authorizations remain separate.

## (b) Host plan

The packet proposes a consolidated assignment: TASL-7 for Track P and gaps for Track S; TASL-2 for Track S `digits_mlp`; deepthought for B.2 CPU replay/audits, DTQ and conditional proposer hosting; Ada as overflow and whole-T1 fallback; HoreKa 2 for T1. The 18:10 R1-EXAM-HOST-B1B2-TASL7 row already moves B1/B2 to TASL-7 and pauses P.3a while either runs. The packet's older claim that B1/B2 run on TASL-2 is stale and must not be adopted. The author selected "保留现有逐项决定" (PLAN R1-HOSTS-04NOV-DEFER). No job is thereby authorized.

## (c) Sweep-2 stack disclosure if deepthought is chosen

If DTQ qualifies and the author selects deepthought for the main proposer, the proposed disclosure replaces the 4090-vs-TITAN build comparison with the same pinned `620d222` sm_52 build as sweep 1, and adds a two-TITAN layer split. The author selected "先等 DTQ 结果" (PLAN R1-B1B-DIFF-DT-DEFER). The packet recommends not adding deepthought2 as a host now, because it is unqualified. Neither option establishes that DTQ has passed.

## (h) Main-proposer proposed items

The five items presented were: (1) fresh-seed audits on deepthought CPUs, otherwise on the sweep host with a 50-proposal two-host check; (2) a STOP when one-host projected duration exceeds four days; (3) select pooled training versus sweep-2-only on validation before reading test results; (4) keep `qwen2.5-coder:7b` for Track S CPU nodes, deciding the GPU-node manager later; (5) choose the P.3b exam set from the sweep-2 training partition, or from sweep 1 with disclosure until sweep 2 exists. The author replied "采用五项建议" (PLAN R1-MAIN-PROPOSER-ITEMS); the recorder lists their consequences as proposed, and all later gates remain. The original packet also asks whether to repeat Track S with the exam pick after the outcome. The author subsequently replied "结果出来后再决定" (R1-TRACKS-PICK-REPEAT-DEFER); no repeat is authorized by that reply.

## (i) Dates and partial T1 fallback (H1)

B.7 around 8 December, Track S fallback around 15 December, D.3 around 3 January and manuscript 10 January are targets, not commitments. They are to be recomputed after G.4. H1 asks whether, if only some T1 nodes have labels by B.7, the gate can be read using T0 plus those T1 nodes while disclosing the node count. The proposed condition requires at least one labelled T1 node per suite for leave-one-suite-out, otherwise STOP. The author replied "采用此部分 T1 方案" (PLAN R1-B7-PARTIAL-T1). The pre-analysis R1-BX-D8-CONFIRM gate remains required.

## (j) Remaining individual decisions

1. **D8 confirmation:** gate-code path, commit and SHA come from M11; decide only once reviewed, before sweep-2 labels are copied back for analysis or enter analysis, as the original packet specifies.
2. **Second proposer:** the 4 Nov author reply confirms "用 exam 第二名"; the proposed local, different-family, B2 audited-Y ranking and closed-loop-only consequences are recorded in PLAN. The earlier API-model option is superseded only to the extent of that decision; the actual finalist and host plan await the exam and subsequent planning.
3. **G.5 divergence STOP:** the author replied "设 20% STOP" (PLAN R1-TRACKG-G5-DIVERGENCE); the asked threshold was strictly >20% of T1 label proposals. The 20% originated as an agent proposal, not a measured threshold. The numerator, denominator and evaluation time require an auditable specification; moving a node to T2 needs an author row.
4. **T0 held-out suite:** packet suggests exclude it from the primary leave-one-suite-out test, but permit a separately reported secondary fold. Alternative: never hold it out.
5. **Probe A6:** its >0.01 mean absolute RPS condition for a P.3a rerun is already recorded; packet suggests otherwise treating it descriptively, with no new row now.
6. **Heavy-tailed floors:** packet suggests author declares the node at G.3 after inspecting census kurtosis and sets Student-t degrees of freedom before labels; alternative is a predeclared numeric rule. Example cutoff and degrees of freedom are proposals, not findings.
7–8. **Licence and T1/T2 lists:** wait for G.0 and the census/G.3 respectively; no decision now.
9. **Containers:** the packet proposed availability checks; verify the actual operator and HoreKa reports before deciding what checks remain. It does not authorize running a job.
10. **Phase C/D host plan:** packet recommends deciding as one plan after G.4 and B.7; the API wording in the older packet needs updating for the author's local-second-proposer decision.
11. **Two server agents:** proposed consequences include host lists, affected rows and the HoreKa agent's compute-node/tunnel working mode. Confirm only against the updated host plan; never revive the stale B1/B2 placement.
12. **Ada fallback and Track S floor:** packet suggests holding Ada G.0 until HoreKa cannot run T1, and measuring a separate 4090 noise floor for Track S GPU nodes. The current queue facts are incomplete; the author can decide with updated evidence.
13. **HoreKa design basis:** the rev 3 runbook was adopted in R1-HOREKA-RUNBOOK after the packet was drafted; no duplicate decision is needed.
14. **MLAgentBench and 1GC-7RC:** packet suggests light MLAgentBench tasks as T1/T2 candidates selected at G.3, and public-dataset 1GC tasks as T2 only, outside the 12–16 count and always training-side in folds. Domain coverage waits for census.
15. **Track S GPU-node manager:** after G.0/D28, as already scheduled; no decision now.

## Other open item: HoreKa J3 and NHR question (c)

The author already allowed the agent to submit GPU jobs and continuations from the agent node. The author subsequently confirmed "确认涵盖 J3" (PLAN R1-HOREKA-J3-CONFIRM), covering a local LLM proposer loop *inside* a GPU batch job pending NHR@KIT's answer. NHR's answer has not been recorded. A restrictive NHR answer causes a STOP; a decision does not waive phase, code-review, budget, resource, or evidence-authorization gates.
