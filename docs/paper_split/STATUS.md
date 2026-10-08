> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the Paper B status entries.
> The source copy in agent-checkpoint-intervention is the historical one.

# Paper B status

**Plan authority:** [RUNBOOK.md](RUNBOOK.md) v2.4. §12/§12.2a and subsequent
repair records govern B's experiment. Executed checks are in
[VALIDATION.md](VALIDATION.md).

Planned work is not completed work. No paid run or submission has been made. No
model call has been made. B's analysis side runs on CPU; the live lane is not
built.

## 4 October — DAC/configurator amendment proposed; readiness audit

At the author's request:
[B_DAC_CONFIGURATOR_AMENDMENT_20261004.md](B_DAC_CONFIGURATOR_AMENDMENT_20261004.md)
(PROPOSED; decisions D-DAC1–6 open) and a CPU scaffold in
`control/configurator/` (serialiser, Kev/CLM encoder slots stubbed until bound,
projection, shared heads), with `tests/control/test_configurator.py` (22 pass)
and scripted trees in `experiments/paper_b/configurator_scripted.py`.
[B_READINESS_AUDIT_20261004.md](B_READINESS_AUDIT_20261004.md): the analysis
side passes on CPU, but B is **not ready to run**. F9 realism still fails
(reproduced), F10 tooling is absent, no real agent path has been exercised, no
transcripts are recorded, and the contract bindings are null. No experiment,
model call or status change.

Copied from S (the 4 October "decisions adopted" entry, B sentence): the author
adopted P-B1 and P-B2 with corrections. **B: one bounded task attempt with a
fixed failure disposition; cutoffs 15 Nov and 30 Nov 2026 for the ICML 2027
route.**

## Version pointers (copied from S)

- Last source-bound packages: A 85 files, **B 53 files, source `12507267`**
  (`release/*_manifest.json`, `release/check_release_*.json`). The B manifest and
  check report are kept here as at S.

## 30 September — TKV2017 recommendations adopted

RUNBOOK §14 makes the recommendations actionable. B-TKV1 (budget separation)
and B-TKV2 (context-conditioned sharing/shrinkage baseline) are PLANNED design
work; B-TKV3 (fixed-cost N/R diagnostic) remains optional after the current
qualification/pilot gates. B's continuous utility, family splits, matched budgets
and state/Markov assumptions are explicit. No manuscript, contract, experiment or
release status advances.

## 2026-09-27 queue progress (B1–B7)

Executing NEXT_WORK_QUEUE.md v2. Authority: RUNBOOK §12 (controls over §11),
[B_DECISIONS_20260927.md](B_DECISIONS_20260927.md),
`protocols/paper_b/design_decisions_20260927.yaml`. All live-study statements are
PLANNED. No model/GPU/network/release/push/merge.

- B1 DONE: B manuscript spine rewritten to the two-checkpoint verification-timing
  design (working title *When to Spend a Verification Budget under Replay
  Uncertainty*). Displaced sections/appendices/figures preserved in
  `papers/paper_b/archive/B1_20260927/`. `make -C papers/paper_b verify` clean,
  anonymity PASS, no pointwise `LCB(w)-2p`, no `\input` of A files, H2 is an
  equivalence check, Strategic Verification is a TODO. All B results remain PLANNED.
- B2 DONE: U is primary end to end. `invalid_reason` and `integrity_status`
  added; invalid is exactly U=0 with reason retained; collection failure carries
  no outcome and is refused as 0; mixed S/U contrasts are refused; unavailable
  actions stay in the original-root analysis via fallback. Fresh engineering
  smoke `results/paper_b/smoke_v2_20260927` (U primary, S secondary, 11 checks)
  is ENGINEERING_ONLY. 60 control tests pass.
- B3 DONE: `control/replay_validity.py` implements the population-scoped `2p`
  allowance. Scalar-only fixed-policy bound; array/pointwise gate refused;
  simultaneous Bonferroni family bounds with abstention; `p_grid_report`;
  `path_allowance = min(1,p1+p2)` with provenance refusal. 16 new tests, including
  the planted-defect world. 76 control tests pass.
- B4 DONE: `control/controllers.py` adds repeated-myopic, frozen reserve/VOI,
  fixed never/now/later and a sampling-only variant on one shared information
  set; `floor(q*N_original)` allowed-budget matching; per-leaf cost ledger;
  CINC-style RF witness; ridge equivalence at 1e-12. 13 new tests; 89 control
  tests pass. scikit-learn pinned in requirements.lock.
- B5 DONE: `control/branch_tree.py` adds `b_branch_v2` records, a real-fork tree
  driver, the `records_to_tree` converter with transplant/reached-only/leakage/
  second-verification rejections, and original-root estimators with a
  template-family cluster bootstrap. 10 new tests; 99 control tests pass.
- B6 DONE (no stop triggered): new B-only candidate-consistency task under
  `experiments/paper_b/task_cc/` with the corrected evaluated-candidate
  interface, visible-diagnostic verifier and strict-improvement response rule.
  Eight executable fixed-policy witnesses (four mechanism classes, two families
  each) run through the real fork path; all eight expected orderings hold. Frozen
  screen law hash `ade3c319…`; pilot law separate (`449b97c3…`, not run).
  ENGINEERING_ONLY output `results/paper_b/task_cc_screen_20260927/`. 105 control
  tests pass.
- B7 DONE: `contract_v2.yaml` migrated deliberately from
  `design_decisions_20260927.yaml` — U primary, original-root estimands,
  repeated-myopic and frozen reserve/VOI comparators, `q=0.25`, gain .02 / harm
  .02, replay block with `provenance_kind=sensitivity_assumption`, working p
  .02, grid, `p_path`, budget caps, stop rules, one repair pass and one
  challenge. `launch_validator.py` accepts `b_branch_v2`, requires the Devstral
  bindings for qualification, keeps later phases refused, and adds
  `budget_cap_errors`. `CLAIMS.yaml` adds B-C6 (N2, PLANNED) and B-C7 (N1,
  PLANNED). Contract model/runtime/split/qualification fields remain null.

## Verdicts (B only)

| Deliverable | Verdict | Basis / next gate |
|---|---|---|
| B engineering | CPU ENGINEERING CHECKS PASS | two-checkpoint U pipeline, population allowance, matched controllers, real-fork tree, candidate-consistency witnesses, contract v2 migration and launch spec; control tests; engine-only, no live evidence |
| B design-ready | WITHHELD | draft memo and ETAAI comparison prepared; author novelty/overlap decision and substantive contract bindings remain open |
| B qualification / pilot / main / submission | NOT EARNED | screen pending; ICML go/no-go 15 Nov / 30 Nov 2026 |

## Remaining external steps (B)

0. **Before any of these:** pass a redesigned task-realism check and the
   design-ready items in [OPEN_ITEMS.md](OPEN_ITEMS.md) §B1–B2.
1. **Ada binding:** bind the Devstral-Small-2-24B-Instruct-2512 weight/tokenizer
   hashes, quantization, server build, context/decoding settings, harness commit,
   task-generator hash and verifier revision into the contract (see
   `protocols/paper_b/QUALIFICATION_AND_SCREEN_LAUNCH_SPEC.md` §1).
2. **Qualification** (both lanes) on the bound substrate.
3. **Bounded screen** (96 leaves), then **pilot** (384 leaves).
4. **Route decision** COMBINE / CORE_ONLY, then a frozen final design and a
   separate budget authorization. No live phase is authorized by this work.

## 2026-09-27 fix queue (F0–F13)

Adopting `B_CONTROLLER_DESIGN_20260927.md` (controller v2). One commit per item.

- F0 DONE: design v2 addendum, fix queue, reviewer prompt, RUNBOOK §12.2a and
  README committed.
- F2 DONE: removed the per-checkpoint allowance from controllers; `choose()`
  takes no `p` and no control module (outside N1 evaluation) imports
  `replay_validity`. Fixed the constant-reserve checkpoint-2 bug. AST guard test
  added; 109 control tests pass.
- F3 DONE: shared `control/bounds.py`; `replay_validity` and `allocation` use the
  same width-2 Hoeffding radius. 111 control tests pass.
- F4 DONE: shared two-phase hard-budget allocator `control/allocator.py`; 12
  tests incl. a hypothesis property. 123 control tests pass.
- F5 DONE: later/never fork from the same checkpoint-2 state with ≥2
  repetitions; `DecisionView` is the sole controller input. 128 control tests.
- F6 DONE: proposed cross-fitted continuation-value rule and the matched
  comparators in `control/timing.py`; max-bias corrected; 137 control tests.
- F7 DONE: `control/evaluate_tree.py` is the single evaluation entrypoint; N1
  wired in evaluation only; `N1_DISPLACEMENT.md` derives m ≤ 3. 142 control tests.
- F8 DONE: realistic CPU candidate-consistency task on bundled tabular data
  (`task_cc_live`), executed through the real fork path with the toy mock
  provider; hidden split never enters the workspace; 150 control tests.
- F9 DONE (legitimate FAIL after one repair pass): task realism R1 and R4 fail
  for the typical behaviour. R2/R3/R5/R6/R7/R8/R9 pass. F10 (Ada tooling) STOPPED.
  See [TASK_REALISM_REPORT.md](TASK_REALISM_REPORT.md).
- F11 DONE: B manuscript aligned to controller design v2; N1 as qualifying
  conclusions with 2·m·p_path and the interference caveat.
- F10 STOPPED: F9 FAIL stops the Ada tooling per the fix queue; reported.
- F12 DONE: design addendum `design_decisions_20260927b.yaml`; contract
  `primary_comparators: [repeated_myopic, bavar_inspired_voi]`, constant-reserve
  ablation, two-phase allocator spec, `displacement_m: 3`, `2*m*p_path`.
- F13 DONE: all 9 planted bugs caught by existing tests; final report
  [FIX_REPORT_20260927.md](FIX_REPORT_20260927.md) written.
