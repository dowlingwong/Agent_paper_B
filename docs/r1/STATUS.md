# Paper B (route R1) — status log

Newest entry first. Only this file says what is done.

## 9 October 2026 — batch 1 review and fixes

All ENGINEERING_ONLY. Seven review findings on harness branch `r1` (at
`201e025`) fixed, one commit each, then `r1` merged into harness `main`.
Tests ran in a Linux VM (Python 3.11.16, env built outside the repo; the
macOS `.venv` was not touched).

### Findings and commits (harness)

- **F1 (MAJOR) revise ignored its feedback — `8086f97`.** E1 `revise` now
  calls `propose_next_trial(..., revision_feedback=feedback)`.
  `LangGraphManager` adds a REVISION REQUEST block to the prompt and records
  `extra.revision_feedback` only when feedback is given; the default prompt is
  byte-identical (golden sha256 test). `revise` is also masked out for
  managers whose `propose_next_trial` lacks the keyword, so it cannot fall
  back to a plain resample. This answers open question 4 of the previous
  entry: the feedback channel is the `revision_feedback` keyword.
- **F2 (MAJOR) verify could run unseeded — `5ec9e9d`.** The E2 mask uses
  `hasattr(worker, "run_trial_at_seed")` (real and dry loops), and
  `_run_worker_at_seed` raises `SeedInjectionUnsupportedError` instead of
  falling back to `run_trial`.
- **F3 (MAJOR) demote could revert verified keeps — `ddba025`.** The mask
  input is now `top_of_stack_unverified`; `_perform_demote` pops exactly the
  top entry and refuses an empty stack or a verified top.
- **F4 (MAJOR) coupled seeds — `81c5bd5`.** `lr_synthetic` builds its dataset
  from `AR_SPLIT_SEED` and trains with `AR_TRAIN_SEED` (both default 42);
  `openml_*` `SPLIT_SEED` defaults to 42 independently. `_run_verify` and
  `run_real_campaign` take `verify_split_policy` (`"fixed"` default, or
  `"vary"`), recorded as `extra.control.verify.split_policy`.
  `LocalWorker.run_trial_at_seed(split_seed=None)` now keeps the worker's
  configured split seed, so "fixed" really re-runs on the campaign's split.
- **F5 (MINOR) LLM calls counted for deterministic managers — `04ba041`.**
  Proposals count against `max_llm_calls` only when
  `not getattr(manager, "deterministic", False)`, in both campaign loops.
- **F6 (MINOR) infeasible choice crashed the campaign — `6756d68`.**
  `_require_feasible` is gone. A masked-out or epoch-unsupported action emits
  `control_decision_rejected` `{epoch, action, mask}` and the trial continues.
- **F7 (MINOR) docs — `d9b4401`.** Docstrings (`run_real_campaign`,
  `run_dry_campaign`, controller module, `ComputeBudget`, `seeds`), the README
  R1 section and `CLAUDE.md` updated. `run_dry_campaign` is documented as
  continue-only; its `NotImplementedError` message now says so.

New tests: `tests/stage2/test_r1_review_fixes.py` (21 tests). Every finding
has at least one test that failed on the pre-fix code and passes after it. A
few companion tests guard behaviour that was already right and pass on both:
the F1 golden default prompt, the F2 mask with a seeded worker, the F3
single-top demote, and F5 counting for an LLM manager. Two existing tests
were adapted:
- `test_r1_l6.py`: the mask test uses the renamed keyword. The six-trial
  scripted run now demotes at trial 4 and verifies at trial 5, because a
  demote right after a verified keep is no longer feasible.
- `test_r1_defects.py` L3.4: with the dataset now fixed, train seeds 7 and 8
  give the same `lr_synthetic` val_score (0.921357). The different-seed check
  uses train seed 100 and tests the split seed separately.

### Checks (Linux VM)

| Run | Passed | Failed | Errors |
|---|---|---|---|
| Baseline, `r1` at `201e025` | 299 | 9 | 1 |
| After fixes, `r1` at `d9b4401` | 320 | 9 | 1 |
| `main` after merge (`3c80b53`) | 320 | 9 | 1 |

- The failures and the error are identical across all three runs and are
  environmental: the 9 failures are the same set as the macOS baseline (missing
  untracked ledgers, figures and paper sections; `/bin/zsh`), and the error is
  the `src.autoresearch_worker` collection error.
- **The L5 golden-fixture regression (`test_r1_l5.py`) passes on Linux**, at
  baseline and after every fix. The fixture was not edited.
- The tree of `main` after the merge is identical to `r1`.

### Merge and push

- Harness merge commit on `main`: **`3c80b53`** ("Merge r1: R1 build batch 1
  (L3, L5, L6) with review fixes"); `r1` is checked out again.
- `git push origin main r1` **failed**: `fatal: could not read Username for
  'https://github.com': terminal prompts disabled`. The VM has no GitHub
  credentials, and none were configured. Push both branches from the Mac.
- This STATUS commit's own push is attempted right after it is made; the
  result is in the session reply. It is expected to fail the same way.

### Observation for the author

- On `lr_synthetic` the training seed now barely moves the metric (≤ 1e-4 on
  val_score, often 0 at 6 dp), while the split seed moves it by about 0.01.
  Under the default `"fixed"` policy, verify's paired deltas on this node
  will therefore be almost entirely the candidate-versus-incumbent difference,
  with little seed noise. Choose whether `lr_synthetic` verify should use
  `"vary"`.

## 9 October 2026 (night) — build batch 1: L3, L5, L6

All ENGINEERING_ONLY: no evidence. Harness work is on branch `r1` of
`~/Documents/autoresearch_harness`, based on `da8dcbd` (7 commits, not pushed).

### L3 — the four harness defects (one commit each)

- **c4efce7** `prompt_manager`: added `deterministic = True` and a docstring
  stating it makes no LLM call; corrected `CLAUDE.md` and the `README.md`
  layout comment. Test: `TestPromptManagerIsDeterministic` (2 tests).
- **6e670dc** `ClawWorker`: the legacy path no longer stores `1 - val_bpb`
  under a `val_bpb` node's metric name (minimise nodes keep the raw sign;
  AUC-style nodes still convert). Test: `TestClawWorkerMetricSign`.
- **f446429** `_current_best`: now respects `metric_direction` and counts only
  `KEPT` records. Tests: `TestCurrentBestOnResume` (minimise resume; invalid
  high metric ignored).
- **bf3df0d** Seed injection: new `worker/seeds.py`; `LocalWorker` and
  `ClawWorker` pass `AR_TRAIN_SEED` / `AR_SPLIT_SEED` to node subprocesses;
  `nodes/lr_synthetic/train.py` and both `nodes/openml_*/benchmark.py` read
  them with 42 as the default. Tests: `TestSeedInjection` (same seed
  reproduces, different seed changes the metric; seed vars are not editable
  symbols).

Files changed: `src/autoresearch/manager/prompt_manager.py`,
`src/autoresearch/worker/{claw_worker,local_worker,seeds}.py`,
`src/autoresearch/control_plane/campaign.py`, `nodes/lr_synthetic/train.py`,
`nodes/openml_credit_g/benchmark.py`, `nodes/openml_bank_marketing/benchmark.py`,
`CLAUDE.md`, `README.md`, `tests/stage2/test_r1_defects.py`.

### L5 — decision hooks and budgets (bb15e01)

- New `control_plane/controller.py`: `ControlView`, `ControlDecision`,
  `Controller` protocol, default `ContinueController`, `build_control_view`
  (leak-refusing) and `compute_mask`.
- E0/E1/E2 hooks in `run_real_campaign` (and E0/E1/E2 in `run_dry_campaign`),
  with the E2 evaluate/commit split before the single immutable append.
- New `control_decision` event; the default controller emits nothing.
- New `ComputeBudget(max_worker_runs, max_worker_seconds, max_llm_calls)` next
  to `BudgetState`; with only `--budget N` behaviour is unchanged.
- CLI: `--controller`, `--max-worker-runs`, `--max-worker-seconds`,
  `--max-llm-calls` (documented in `README.md`).
- Tests (written first, against the unmodified code):
  `test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`
  compares every non-excluded `TrialRecord` field against a golden fixture
  (`tests/stage2/fixtures/l5_default_records.json`) captured from the
  unmodified harness, for a dry campaign and a fixed-seed `LocalWorker`
  campaign; `TestControlViewLeak` (4 tests) rejects audit metrics, future
  records and sibling outcomes.

### L6 — actions (efca691, 201e025)

- `TrialDecision.SKIPPED` + `TrialState.SKIPPED` (PROPOSED → SKIPPED) with
  `TrialRecord` validation for skipped records (no metric, execution FAILED,
  validity VALID, no failure category, `extra.control`).
- `skip`, `revise`, `verify` (paired fresh-seed re-runs, frozen response rule,
  veto/rescue, hash-checked swaps), `demote` (incumbent stack) and `stop`;
  masks per problem spec §2.1.
- Skipped counted separately in `evaluation/metrics.py`, `memory/similarity.py`
  and `reporting/export_figures.py`; `summarizer.py` handles it via
  `decision.value`.
- Tests: `test_r1_l6.py` (10 tests) — one per action, the masks, the
  `TrialRecord.from_mapping` round-trip for skipped records, and a scripted
  controller issuing each action once across a 6-trial `lr_synthetic`
  campaign (with `LangGraphManager` + an injected stub LLM, no Ollama).

### Checks

- **Full harness suite** (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **299 passed, 9 failed, 1 error, 2 subtests
  passed**. L1 baseline was 277/9/1, so +22 new tests and **the same 9 failed
  and 1 error**. The failures are the pre-existing ones listed in the L1 entry
  below.
- **Default behaviour.** The L5 regression is green after every commit; the
  default `ContinueController` adds no record fields and no events.
- **New tests by name:** `test_r1_defects.py` (7), `test_r1_l5.py` (5),
  `test_r1_l6.py` (10). Full list in the session reply.
- **README dry-run:** `scripts/run_campaign.py --node lr_synthetic
  --campaign-id smoke --budget 3 --dry-run` runs cleanly. The `smoke` ledger
  already holds the 3 records from the L1 baseline check, so it resumes
  (`records_written=0`); a fresh id (`r1_check`) writes 3. A fresh run with
  `--max-worker-runs 2` stops after 2, confirming the compute cap.

### Not done, and why

- The `r1` harness branch is **not pushed**. Only the Paper B repo push was
  requested (L1). Say the word and I will push it.
- `run_dry_campaign` still raises for non-`continue` actions; the actions are
  implemented in `run_real_campaign`, which the L6 tests exercise. The runbook
  only asks for the dry path to carry the E0/E1/E2 hooks.
- `verify` re-runs use a synthetic (non-ledger) budget index and a no-edit
  proposal; the incumbent is restored from the pre-trial editable snapshot.
  The verify budget is measured but the per-run wall time is passed as 0.
- There is a pre-existing test-order flake: `test_artifact_completeness...`
  writes `paper/tables/artifact_completeness_report.txt`, and once that file
  exists one pre-existing failure flips to a pass (8 vs 9 failures). It is not
  caused by R1 code; I report the clean-tree count (`9 failed`).

### Open questions for the author

1. Push the harness `r1` branch to `origin`?
2. The runbook's verify rule sets `current_best` to the candidate's original
   single-run metric on a rescue or keep. On a rescue this can *lower*
   `current_best` (a rescued discard had a worse metric than the incumbent).
   Confirm that is intended, or change the rule.
3. `t_min` (stop threshold, default 3) and `verify_runs` (default 2) are
   function parameters only. Add `--t-min` / `--verify-runs` CLI flags?
4. `revise` records a fixed structured feedback string; the manager interface
   (`propose_next_trial(status, memory_context, node_spec)`) has no feedback
   argument, so the manager does not yet consume it. Confirm the intended
   feedback channel for L12.

## 9 October 2026 (evening) — build batch 1: L1

**L1 — Housekeeping.**
- **Paper B commit.** One commit, "Archive old Paper B plans; adopt route R1 canonical plan": the deletion of `docs/paper_split/`, the new `archive/old_b_2026-10-09/` and `docs/r1/`, the `README.md` banner, and the dated author decisions in PLAN §10 (D1, D3, D4, D14, D19, D20 — "decided 9 Oct 2026 by the author"). Pushed.
- **Harness.** Branch `r1` created from `main` at `da8dcbd` (the base commit). `uv sync --extra dev` succeeded. The `harness/claw-code` submodule is **not** initialised (D19).
- **Baseline test result** (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`): **277 passed, 9 failed, 1 error, 2 subtests passed**. Pre-existing, recorded not fixed:
  - `tests/test_artifact_completeness_and_manifest.py` ×4 (missing checked-in campaign report / manifest entries);
  - `tests/test_kdd_paper_sections.py` ×5 (the `paper/kdd_aae_2026/sections/*.md` files are absent);
  - `tests/test_legacy_noop_skip.py` error (imports `src.autoresearch_worker` from the uninitialised `harness/claw-code` submodule).

## 9 October 2026 (15:45) — build runbook and first prompt

Added `docs/r1/BUILD_RUNBOOK.md`, a per-step specification for L1–L14 written against the harness at `da8dcbd`, and `docs/r1/prompts/BUILD_BATCH1_PROMPT.md`, which covers L1, L3, L5 and L6 with the L2 defaults in an editable block. Nothing has been implemented yet.

## 9 October 2026 (15:30) — execution order adopted

RUNBOOK §3 gains the local-first order: build steps L1–L14 on the Mac, then experiments E1–E8. The next step is L1.

## 9 October 2026 (15:20) — configurator: encoder proposal

PLAN §7 is revised. The proposed primary is now a ModernBERT-family encoder decision model (Laya checkpoint vs plain ModernBERT-large), with late fusion of numeric features. Training is supervised, then an RL step with an RLCR-style bounded proper-score reward. Kev moves to the decoder comparison. D16 stays open.

## 9 October 2026 (afternoon) — format, benchmarks, configurator proposal

- **Author decisions:**
  - No manuscript format is fixed yet (R1-FORMAT).
  - ResNet-trigger is removed; experiments and configurator training use agent benchmarks across the board (R1-BENCH).
- **New open decision D20:** the benchmark set and scope. The proposal is in PLAN §6.
- **PLAN §7 gains** a verified candidate table and a proposed primary: Kev typed decision model; CLM, generative LLM and tabular as ablations. D16 stays open for discussion.

## 9 October 2026 (later) — venue, ledgers, harness clone

- **Author decisions:**
  - TMLR is the primary venue, with an ICML main-track quality bar (PLAN §9; D17 closed).
  - The original 1,355-trial ledgers are lost (D12 closed). Only aggregate tables survive, in the workshop-paper repo.
- **Harness clone.** `dowlingwong/autoresearch_harness` was cloned to `~/Documents/autoresearch_harness` at `da8dcbd`. The folder the author connected, `~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation`, is the workshop-paper repo (camera-ready; also the harness's submodule), not the harness code.
- **Note for the author.** Because the ledgers are lost, the `ClawWorker` `1 − val_bpb` sign issue cannot be checked for the workshop paper's autoresearch trials.
- **New default D14:** harness work on branch `r1` of that clone (confirm).
- **New open decision D19:** worker backend.

## 9 October 2026 — route R1 adopted; old plans archived; canonical plan written

- **Author decisions** (PLAN §1):
  - R1-ROUTE
  - R1-VENUE: rolling journal; TMLR recommended, to be confirmed as D17
  - R1-CARRY
  - R1-ARCHIVE
  - R1-PLAN
- **Archive.** All of the old `docs/paper_split/` moved to `archive/old_b_2026-10-09/docs_paper_split/`. The move includes the uncommitted §19 and §20 additions of 9 Oct and the 9 Oct prompt pack. Legacy code and the old manuscript stay in place for now (PLAN §8; RUNBOOK 0.1 decides).
- **New files:**
  - `docs/r1/PLAN.md`
  - `docs/r1/RUNBOOK.md`
  - this STATUS
  - `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`
  - `docs/r1/inputs/NOVELTY_SWEEP_20261009.md`

  The two inputs are AI-assisted subagent outputs and were not independently reviewed. In the sweep, three arXiv entries were spot-checked against their abstract pages (2607.05458, 2603.24647, 2608.21027). COTA's "0.5B" size is not stated on its arXiv page.
- **Not committed.** The file moves were made in the working tree with `mv`; nothing is committed yet. The first Phase 0 session commits them as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Next:** Phase 0 (RUNBOOK §3). The first prompt covers 0.1–0.3.
- **Open:**
  - D1–D12 and D14–D18 (PLAN §10);
  - the configurator architecture discussion (D16);
  - venue confirmation (D17).
