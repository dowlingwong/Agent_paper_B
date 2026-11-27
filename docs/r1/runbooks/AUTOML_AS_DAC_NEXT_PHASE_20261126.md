# AutoML as DAC — next-phase runbook

**Design draft for review, 26 Nov 2026.** The author selected the fixed-memory, variable-length training task for
the Paper C development census. Follow [PLAN §10](../PLAN.md#10-open-decisions) and the existing signed notes for
execution. This draft proposes a work order and defines what each handoff must establish.

**Start here.** [Paper B](../../../canon/PAPER_B_PLAN.md), [Paper C](../../../canon/PAPER_C_PLAN.md),
[compute](../../../canon/COMPUTE.md), and [design agent](../../../canon/agents/design/SOUL.md).
Use [the documentation index](../README.md) for reports, code pins and experiment-specific notes.
The live queue and current blockers are on [coord/coordinator](https://github.com/dowlingwong/Agent_paper_B/tree/coord/coordinator).

## 1. Scientific aim and evidence at the start

Study the control of AutoML search under noisy, expensive evaluations. A proposer suggests an edit. The
controller decides whether to execute it (E1), whether to keep it after observing a result (E2), and, when
available, whether to verify. Worker runs and manager calls are budgeted. Audited terminal improvement is the
campaign outcome.

| Project | Question | Evidence |
|---|---|---|
| Paper B | How much do de-duplication, noise-aware decisions and proposal-level forecasts improve the loop at the same budget? | Fresh D.3 campaigns on the seven primary T0 nodes. The offline gate tests a separate claim about one-step utility on logged proposals. |
| Paper C | When does a budget-aware one-step controller capture the value of sequential control? | Isolated channels and oracles in E-SYN, then fresh trajectories under different actions and paired campaigns with a strong one-step comparator. |

In Paper B, NF and NI give a sufficient fixed-price reduction. Hard-budget opportunity cost is a separate
channel. For Paper C's first comparison, give the one-step and sequential controllers the same immediate
forecast, controller actions, runtime information and budgets. A budget-only reference assumes an exogenous
proposal process and prices the remaining runs and calls. A sequential controller can additionally model how an
action changes future proposals, incumbent-dependent edits or information. SFT and distillation are ways to
implement a controller with a specified target.

**Evidence status on 27 Nov.** Both T0 sweeps are audited. Train/dev releases contain 850/422 labels from sweep 2
and 593/276 from sweep 1, with A3 reviewed on T0. G.4b passed for its pilot nodes. G.5 awaits reviewed assembly
and the launch note checks. D.3 rev 4 and its verify-seed option are signed, with engineering work still in progress.
The gate is unread and the campaign result tables are placeholders. Run the frozen A3/A5 arms after arms freeze
regardless of the gate verdict (R1-D3B-UNCONDITIONAL). Paper C has engineering runs and E-SYN tooling, with real-node
evidence still to collect.
Sources are the [current B plan](../../../canon/PAPER_B_PLAN.md), [A3 review](../reviews/ARMS_A3_RUN_REVIEW_20261123.md),
[Track S stop](../reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md), and the [C plan](../../../canon/PAPER_C_PLAN.md).

## 2. Work order and ownership

The coordinator issues one task per deliverable. The design agent supplies the claim, comparator, estimand and
acceptance check. The writer handles manuscript changes. Local and compute implement their assigned units and
a fresh reviewer checks each unit at its required tier. Compute operates the live hosts in
[COMPUTE.md](../../../canon/COMPUTE.md).

| Order | Task and owner | Depends on | Done when |
|---|---|---|---|
| 0 | **Repository hygiene**, design + coordinator + each checkout owner | Branch inventory on the published base | Current paths resolve. Each proposed retirement has an exact tip, owner and recovery route. Retained refs are accounted for. See [hygiene audit](../reports/REPO_HYGIENE_AUDIT_20261126.md). |
| 1 | **Paper B manuscript correction**, writer + design | R1-ALIGN-OUTCOME, R1-D3B-UNCONDITIONAL, R1-D3-DECOMP and R1-D3-ORDER | Both draft builds show the same D.3a/b design and separate the offline gate verdict from the campaign outcome. Revised outline and claim-to-table sheet reviewed. |
| 2A | **T0 screening smoke and D.3**, local + compute | Repeat the screening smoke after the reviewed cache fix merges. Close the remaining D.3 rev 4 freeze prerequisites and the runner and audit checks. | The complete D.3a/b arm list and accounting pass on the pinned harness. One matched GPU layout works in smoke. The designated audit computes the paired terminal outcome from fresh seeds. |
| 2B | **T1 labels and A5 readiness**, compute + local | Review the sd-matched G.5 assembly, complete the per-node checks and publish the note. Advance the Ada Track P probe in parallel. | Eligible G.5 label tables and receipts follow the signed release sequence. Passing expansion nodes join by addendum under S9. |
| 2C | **D.3c descriptive transfer**, compute + design | G.5 completion, frozen arms, own pre-declaration and authorization, code-diff sidecar smoke | New disjoint instances of CIFAR-10, Fashion-MNIST and MinAtar Breakout use the approved D.3c arms. Report cost and paired outcomes with descriptive scope. |
| 3A | **Paper C E-SYN and CPU census**, local worker + design | Consolidate Paper C work and the existing PLAN rows, then apply R1-PAPERC-MEASURE-FIRST | An exact or certified oracle checks each synthetic channel. CPU report measures retention stakes and decision relevance before fixing the real-node design. |
| 3B | **Paper C fixed-memory census**, design + experiment | One approved development task, cap, pin, and a host lease that fits Paper B's schedule | Reproducible baseline, measured headroom and evidence about whether the first edit changes follow-up feasibility or quality. See §5. |
| 4 | **Paper C core decision and new trajectories**, design + coordinator + author | CPU census and, where available, development results from E-INT | Approve R1-PAPERC-CORE with eligible nodes/actions, frozen comparators, practical margin, supported interventions, audit, budget/power statement and test split. Then collect evidence under the signed runbooks. |

Run the manuscript correction, CPU runner work and resource checks in parallel. The compute agent advances the
Ada P.4 probe and the D.3 HTCondor preflight in parallel under R1-P4-D3-GPU-PREFLIGHT. The D.3 preflight can
start while G1/G6 are being implemented. Paper B remains the first call on its signed devices and budget.
Paper C's CPU work and task specification can proceed while the batch GPU is unavailable. The coordinator
tracks departures in the existing queue.

Advance by reviewed prerequisites under R1-STEP-ORDER. Complete the G.5 labels for the eligible set, publish the
train/dev release, freeze the trained and calibrated arms and then read the gate once. Include optional evidence
when it is complete and reviewed at the submission decision. Venue dates govern submission scheduling.

## 3. Paper B manuscript and results

The writer works in a standalone clone of [paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript) (R1-MANUSCRIPT-REPO). Start with
[introduction](https://github.com/dowlingwong/paper_B_manuscript/blob/main/sections/introduction.tex),
[problem](https://github.com/dowlingwong/paper_B_manuscript/blob/main/sections/problem.tex),
[theory](https://github.com/dowlingwong/paper_B_manuscript/blob/main/sections/theory.tex),
[setup](https://github.com/dowlingwong/paper_B_manuscript/blob/main/sections/setup.tex), and
[results](https://github.com/dowlingwong/paper_B_manuscript/blob/main/sections/results.tex).
Build both drafts there. Put the manuscript branch, commit and build results on this repository's
`coord/writer`. The coordinator publishes reviewed manuscript changes and advances the research pin.

1. **Lead with the decisions and outcome.** Show a proposer, incumbent, E1/E2 controller and independent terminal
   audit. State the matched hard-budget question in the abstract and first page. The learning object in A3/A5 is a
   forecast of the immediate increment. The decision rule translates it into actions.
2. **Put the matched-budget decomposition first.** In the design and main result table show A0, A0R, A1 and A2.
   A0R−A0 measures the rules layer under default keep, and A2−A0R measures the incremental index policy under
   the same rules layer. Add A3/A5 versus A2 and A5 versus A3 as specified by D.3b. Interpret A5−A3 as the
   difference between the full forecasting arms, which also use different input representations. Keep the
   replication, commit gate and margin rule comparisons declared for D.3a.
3. **Keep the theory at its proved scope.** Present the one-step rule and exact fixed-price reduction as a short
   pair of results. Explain how reused incumbent scores violate the simple model and why a hard-budget campaign
   is measured directly. Main-text statements follow R1-PROOF-POLICY. Put long proofs and pilot details in the
   appendix. Paper C owns the empirical test of when a continuation model adds value.
4. **Synchronize the two result templates.** In both versions, A3 and A5 run in D.3b after freeze. A6 retains its
   separate gate condition. Add A0R and D.3c in setup/results, update the deviations, and use the declared
   four-way outcome reading in [the alignment memo](../proposals/GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md).
   Replace placeholders only from released results. Build both drafts before review and verify the final build
   flags unresolved fields.
5. **Maintain four evidence levels.** Report calibration and A3 development results as development. Read the
   preregistered offline gate once from its released split. Report closed-loop data from D.3 after its declaration
   and audits. Introduce the richer E-INT environment in Paper C; it changes neither the B gate nor its test set.

## 4. Experiments and resource assignment

| Work | Route and existing limits | Verification and handoff |
|---|---|---|
| D.3a/b Paper B | Seven T0 nodes × 18 fresh instances per node, same start/instance pairing across arms, 20 charged worker runs and 80 manager calls, ten fresh audit seeds. deepthought for the CPU audit within its 16-worker / 10-free-CPU rule. Proposer GPU from the declared layout. | Compute reports the job/event accounting, SHA and schema. Verify that rule skips count the manager call and consume zero worker runs. Report D.3a's projection against the 140 GPU-hour threshold. |
| G.5 Paper B | TASL pair under reviewed per-node routing, projected 216.9 GPU-h against 425 GPU-h in the current plan. TASL-2 excludes CPUs 8–11. TASL-7's eligible audit chunks follow the cross-host checks. | Experiment reports correct pin and lease, per-node completions and any failures. The houseprice procedure stops that node on the affected host. Test and evaluation partitions follow the release notes. |
| P.4 Paper B | Run the probe on one RTX 6000 Ada through the direct launcher. The existing H200 queue request is independent of this route. The phase-1 reporting threshold includes the probe charge. | Compute confirms the approved launch account, finishes the reviewed Ada host configuration, verifies the environment and lease, and delivers timing, peak GPU memory and charges for the phase-1 note. |
| Paper C E-SYN and E-T0 | Desk/CPU work with pinned harness and separate seed registry. R1-PAPERC-MEASURE-FIRST specifies new audits of retained/final configurations on four nodes and a guarded first-accept check on digits and tabular. | Report decision relevance, immediate stakes and expected paired precision first. Compare E1 and E2 separately. E1 only enters the proposed core where its declared threshold produces decision-relevant variation. |
| Paper C E-INT | One declared 24 GB or 48 GB GPU with an explicit VRAM cap on that host. Candidate route is a spare TASL lease or Ada once the owner confirms availability and the author accepts the layout. | Record device model, free/allowed memory, software and lease, exact token accounting, throughput and loss. Use one GPU model and identical conditions across the four cells. |

### D.3 single-GPU HTCondor preflight

The compute agent uses one ETP L40S or TOpAS A100 in an engineering job. Verify the intended single-GPU request
matches (GPU, CPU, RAM and scratch), and that the pinned candidate container starts and can use the assigned
GPU. The ETP workers can read the shared ETP paths. TOpAS workers have neither the ETP `/work` nor `/ceph`
mounts. For TOpAS, stage the approved inputs from the submit side and check their hashes inside the job sandbox
before relying on that route. Use approved non-sealed fixtures for any inputs that are still sealed or unavailable,
and list those substitutions in the report.

Report the job ID and match or failure reason, GPU model and driver, image digest, and the in-container input
read and hash checks. Record partial coverage explicitly if an image or input is still unverified. Keep the
per-arm smoke behind its own G1/G6, constants and runner checks. The
[compute card](../../../canon/COMPUTE.md) records inventory and observed occupancy separately.

## 5. Fixed-memory, variable-length sequence census

Use one small, naturally variable-length training workload. First check whether `autoresearch_fixedtokens` can
retain meaningful document lengths and a common validation evaluator under a new development-only adapter.
If that asset uses fixed blocks end to end, document the mismatch and propose one compatible workload with
pinned data and split. Reuse of a task family does not reuse Paper B's sealed rows or test seeds.

**Design.** Freeze initial configuration, data and token counting. A changes training batch construction to
length bucketing or boundary-safe sequence packing, selected in the development spec. B increases model-visible
training context within the same peak-memory cap. Run baseline, A, B and A+B on matched development seeds. A
first estimate is three seeds per configuration, up to twelve short training attempts plus the launch smoke.
The acceptance note binds the exact token and time budget after a smoke so the census fits the chosen host.
Packing requires a correctness check for attention masks, sequence boundaries and loss accounting.

- **Primary census measurement:** can B finish within the declared memory cap without A, and can it finish with
  A? Record OOM or other invalid outcomes by cause and charge the actual consumed time. If both are feasible,
  estimate the paired interaction in held-out quality, `Y(A+B) - Y(A) - Y(B) + Y(base)`.
- **Matched comparison:** count real training tokens contributing to loss. Hold the effective optimizer
  token budget per update fixed where the engineering comparison permits it, and log batching order and
  accumulation. Use the same held-out documents, target positions, evaluation context and scoring code. Record peak allocated
  and reserved GPU memory, wall time, tokens per second, worker GPU-seconds and exit status.
- **Readout:** proceed to a proposed descriptive sequential-control run only if the baseline is repeatable,
  there is measurable headroom, and the first edit changes the feasibility or value of a legal follow-up. Count
  how often this occurs with the real proposer in a small development search. A speed gain alone establishes
  systems headroom. To translate speed into search value requires a separately declared GPU-time experiment.
  If the census is inconclusive, report it and keep E-INT descriptive.

The census checks one mechanism. For an actual sequential contrast, collect new observations under both early
actions with a declared continuation and an independent terminal audit. The behavior mixture or repeated
forks must cover the eligible actions. Use the existing restore and support checks for forks. If the design uses
native randomized action assignment instead, write a new declaration before evidence collection.

## 6. Final handoff before the next evidence runbook

The design agent delivers one sheet to the coordinator with the claim, comparator, estimate, action and seed
support, output schema, hardware options, cost, precision and interpretation for each outcome. Keep the existing
Paper C RL go/no-go. A small or imprecise contrast supports a claim only at the declared margin and for the
measured policies.

### Stage approval and reporting

1. Collect one approval for the stage under R1-STAGE-APPROVAL. Include the comparisons, primary outcomes and
   analysis, allowed data, budget, launch conditions, and the exact documents and publication steps the approval
   covers. Record the approval and the reviewed version in PLAN §10.
2. Assign implementation, tests and review. Track acceptance checks in `STATE.md`. When all agreed checks pass,
   the coordinator publishes the explicitly authorised note or pre-declaration and records the commit and check
   results. Evidence starts from the launch pin after the required strict checks.
3. Keep open author decisions in `AUTHOR.md`. Report completed work, verifiable results, next steps, and all ready
   decisions in one short Chinese digest each day. For each decision give the recommendation and reason, the
   consequence, the blocked task and the exact reply. Raise a Level 2 decision immediately if it blocks the
   critical path. Follow the existing notice requirements and explicit sealed-data release procedure.

**Proposed record for the author-approved census selection.** Add the fixed-memory, variable-length sequence
training benchmark as Paper C's chosen E-INT development census. Keep E-INT descriptive until the census and
the core decision establish further scope. Bind the workload, host, time cap and seed block in the census note.
