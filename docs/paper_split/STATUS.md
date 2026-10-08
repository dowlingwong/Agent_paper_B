> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the Paper B status entries.
> The source copy in agent-checkpoint-intervention is the historical one.

# Paper B status

**Plan authority:** [RUNBOOK.md](RUNBOOK.md) v2.4. §12/§12.2a and subsequent
repair records govern B's experiment. Executed checks are in
[VALIDATION.md](VALIDATION.md).

Planned work is not completed work. No paid run or submission has been made. No
model call has been made. B's analysis side runs on CPU; the live lane is not
built.

## 8 October — Stage 1 records and author handoff

Stage 0 committed and pushed as `3f93c31`; remote full hash verified as
`3f93c31412a5a62227547ff1a814c3cbc33a4336`.
[Decision sheet](B_DECISION_SHEET_20261008.md) and
[B2 re-review prompt](B2_REREVIEW_PROMPT_20261008.md) prepared. The reviewer
prompt applies the author's source/Paper A exclusion and distinguishes
historical-code reconstruction from an actual historical-source check.
It has not been dispatched; no independent review verdict exists.

OPEN_ITEMS now scopes B-DAC4 as complete for the scripted executor and open
for Pi; B-DAC5 has draft v3 fields while adopted values/bindings remain open.
The stale no-remote/authority entries are reconciled to the author's kickoff.
The execution runbook suggests route after screen; scientific RUNBOOK
§12.2–§12.3 says after pilot. D-ROUTE requests an explicit author amendment.
Nothing in the scientific RUNBOOK, contracts, fixtures or claims was changed.

**STOP:** author answers needed for D-PLAN, D-DAC1, D-F10, D-INFRA-RB and
D-ROUTE. Stage 1 is prepared, not accepted/complete. Stages 2–5 have not
started. No Ada, model call, realism run, authorization or submission.

## 5–6 October — imported engineering work, records reconciled 8 October

Historical, source-reported entry from plan v3.1 (basis and §0.3, IP2/IP4,
§8): source `9de9c908`, merged in `f463209d`, imported into B at `a93e2b7`.
The scripted executor has three regimes, chained filesystem/session forks,
one-verification guard and H₁/H₂ capture; the deterministic ledger exports
back to trees and detects tampering; contract v3 is a draft with null
bindings; the configurator is a scaffold, not a bound model. The plan reports
6 October CPU checks: **207 control tests and smoke 11/11**. These historical
checks were not run by this session; the Stage 0 fresh-clone checks separately
revalidate the current imported code. No historical source checkout was read.

The 28 September controller-fix round is described in FIX_REPORT and the
independent-review records copied into B. Current CPU checks pass, but the
B2 re-review of those fixes, author novelty verdict and BAVAR hand-reading
remain open; recording the fixes does not close B2.

## 8 October — takeover, Stage 0

8 Oct: takeover; [this runbook](B_EXECUTION_RUNBOOK_20261008.md) is the
execution order. The author's kickoff establishes this repository as the
B authority. Science remains governed by RUNBOOK v2.4; plan v3.1 and DAC
framing are pending author decisions. The source repository and Paper A
were not accessed. Source-reading suggestions in the supplied runbook do
not override the author's narrower scope instruction.

GitHub `main` was verified at `1554732b1a769abb7138bfa75250e3543fc09121`.
A fresh GitHub clone at that commit, Python **3.13.4**, dependencies from
`requirements.lock`: **207 control + 6 release + 12 standalone tests PASS**;
smoke **11/11 ENGINEERING_ONLY**; v3 qualification launches REFUSE for both
lanes (draft and missing bindings/authorization); manuscript **12 pages**,
verify clean, anonymity PASS. The inherited three-file Pi verifier failure
was reproduced and left unchanged. Generated tracked files were restored
in the scratch clone; its tree is clean. See VALIDATION's takeover rows.

Machines: the Mac checkout and GitHub fetch are reachable; real TeX Live
2023 / latexmk is available on the Mac and built the PDF. Ada access, B's
clone path, GitHub credentials there, GPU contexts and ports are **not
verified**; no SSH or GPU command was issued. D-ADA1 is pending and gates
the later read-only pre-flight. The source repository is off limits.

The supplied runbook was moved from `docs/` to its canonical `docs/paper_split/`
path. Home-directory examples were replaced with logical placeholders to
satisfy §2.8; its rules and stage text were preserved. README and PROVENANCE
had no URL placeholder at takeover, so the verified destination URL was added.

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

- Last source-bound package: **B 53 files, source `12507267`**
  (`release/paper_b_manifest.json`, `release/check_release_b.json`). The B
  manifest and check report are kept here as at S.

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
