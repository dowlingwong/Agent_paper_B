> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the Paper B validation rows.
> The source copy in agent-checkpoint-intervention is the historical one.

# Validation ledger — Paper B

Only commands that were actually executed are listed, each with the source
commit it ran against. Rows copied from the shared ledger describe the source
repository's commits; the 8 October section below records checks in this
repository.

## 4 October — Paper B configurator scaffold and readiness re-checks

Source: working tree at `c5a8638d` plus the uncommitted configurator files.
Python 3.12.14 venv outside the repository, from `requirements.lock`.

| Executed check | Result |
|---|---|
| `unittest tests.control.test_configurator` | 22 PASS |
| `unittest discover -s tests/control -p 'test_*.py'` | 188 PASS |
| `unittest discover -s tests/release -p 'test_*.py'` | 5 PASS |
| `experiments/paper_b/smoke_b.py` (output outside the repo) | 11/11 engineering checks pass |
| `cc_live_realism.py --families 8` (output outside the repo) | FAIL as recorded: R1 and R4 False for the typical behaviour (0/5/3; verify_gain_max −0.040) |
| `ls run_screen.py bind_runtime_artifacts.py` | absent |

## 29 September — legacy retirement and TKV citation revision (B row)

Source: working tree based on `b9b56265`.

| Executed check | Result |
|---|---|
| `make -C papers/paper_b verify` | PASS; citations/references resolved |

## 26 September — integration/repair `12507267` and the L8–L10 rows

Copied from the source repository at S = 4154f153, where these rows describe the
source commit `12507267`; the B halves only.

| Check | Result |
|---|---|
| `make test-split` | 14 measurement + 20 control + 5 release tests pass |
| `make paper-a paper-b` | verify clean; A 42 pp, B 27 pp; A theory checks pass |
| `make release-a release-b` + `check_release_independence.py --paper a/b` | PASS: A 85 files, B 53 files; hashes match source; clean build (quick mode); B smoke exits 0 (ENGINEERING_ONLY, not an endorsement of its bootstrap estimates) |

| Commit / item | Commands | Observed result |
|---|---|---|
| L8 | `make smoke-b B_SMOKE_OUTPUT=results/paper_b/smoke_v2_20260926`; `make path-check check-split test-split`; control repair tests; `git diff --check` | PASS: 33 control tests (13 added counterexample tests), 5 release; 9 engineering smoke checks. Old smoke preserved. New output is ENGINEERING_ONLY, not a result or pilot. Logs: `results/validation_logs/L8/`. |
| L9 | `make path-check check-split test-split`; `protocols/paper_b/launch_validator.py --phase engineering --lane one_step`; default draft `--for-launch`; v1 byte comparison with `1d474f15` | PASS: 43 control, 5 release tests. Engineering accepts; draft launch refuses as expected. Later phases refuse "phase not yet implemented". Historical v1 byte-identical. Logs: `results/validation_logs/L9/`. No execution authorization claimed. |
| L10 | `make path-check check-split test-split`; `experiments/paper_b/tree_fixtures.py --output results/paper_b/tree_v1_20260926` | PASS: 49 control, 5 release tests; eight ENGINEERING_ONLY fixed trees. No sequential learner or scientific result. Logs: `results/validation_logs/L10/`. |

## 2026-09-27 queue (NEXT_WORK_QUEUE v2, B rows)

Interpreter: a Python 3.12 venv outside the repository
(Python 3.12.7, NumPy 2.3.0, SciPy 1.18.1). All live-study statements remain
PLANNED; no model, GPU, network, release, push or merge was run.

| Commit / item | Commands | Observed result |
|---|---|---|
| B7 | `make path-check check-split test-split`; `protocols/validate_claims.py`; `make paper-a paper-b` (source repository; B half relevant); `launch_validator.py --phase engineering --lane one_step/sequential`; `--phase qualification --lane one_step` | PASS. `contract_v2.yaml` migrated deliberately. Validator accepts `b_branch_v2`; engineering PASS both lanes; qualification REFUSES on the unbound Devstral/runtime/task-generator/evaluator/split/p bindings; pilot/main/final still refuse; `budget_cap_errors` added and tested. 106 control + 5 release tests pass; claims validator PASS. |
| B6 | `make path-check check-split test-split`; `experiments/paper_b/task_cc/witnesses.py --output results/paper_b/task_cc_screen_20260927` | PASS/WITNESSES_OK. New B-only task; eight executable fixed-policy witnesses (2 families each) run through the B5 real-fork driver: **all eight orderings hold**. Frozen screen law hash `ade3c319…`; pilot-law hash `449b97c3…` (not run). 6 new tests; 105 control tests. Output ENGINEERING_ONLY. |
| B5 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_branch_tree.py'` | PASS. New `control/branch_tree.py`; `records_to_tree` rejects transplanted checkpoint-2 state, reached-only denominator, leakage and a second verification; original-root estimators with family-cluster bootstrap. 10 new tests; 99 control tests. |
| B4 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_controllers.py'`; `pip install scikit-learn==1.5.2` | PASS. New `control/controllers.py`; `allowed_tree_budget` uses `floor(q*N_original)`; `assert_matched_allowed_budgets`; `BudgetReport`; `RFWitness`; ridge equivalence at 1e-12. 13 new tests; 89 control tests. |
| B3 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_replay_validity.py'` | PASS. New `control/replay_validity.py`; scalar-only `population_lower_bound`, simultaneous family bounds, `p_grid_report`, `path_allowance`. 16 new tests including the planted-defect world. 76 control tests. |
| B2 | `make path-check check-split test-split`; `experiments/paper_b/smoke_b.py --output results/paper_b/smoke_v2_20260927` | PASS. `schema.py` adds `invalid_reason`/`integrity_status`; U primary. 11 engineering checks pass, ENGINEERING_ONLY. New `tests/control/test_u_semantics.py` (11 tests). 60 control tests. |
| B1 | `make -C papers/paper_b verify`; `sh papers/paper_a/scripts/check_anonymity.sh --mode submission` (source repository; script now copied to `papers/paper_b/scripts/`); `make check-split`; greps; `pdftotext \| wc -w` | PASS. Rewrote abstract and all 12 sections around the two-checkpoint timing spine; displaced sections moved to `papers/paper_b/archive/B1_20260927/`. B builds clean at 11 pages. Anonymity PASS. No pointwise `LCB(w)-2p`; no `\input` of A files. No model call. |

## 2026-09-27 fix queue (F0–F13, B rows)

Interpreter: a Python 3.12 venv outside the repository.
Local CPU only; all live studies PLANNED.

| Item | Commands | Observed result |
|---|---|---|
| F2 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_no_hidden_gate.py'` | PASS. Removed `p`/`use_allowance` from `choose()`; fixed the constant-reserve checkpoint-2 bug. New AST guard; planted param/import caught. 109 control tests. |
| F3 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_replay_validity.py'` | PASS. Shared `control/bounds.py`; both callers use the same width-2 radius. 111 control tests. |
| F4 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_allocator.py'` | PASS. New `control/allocator.py`; 12 tests including a hypothesis property. 123 control tests. |
| F5 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_branch_tree.py'` | PASS. later/never fork from the same checkpoint-2 state with ≥2 repetitions; `DecisionView` sole input. 128 control tests. |
| F6 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_timing.py'` | PASS. New `control/timing.py`; comparators; `matching_report`. 137 control tests. |
| F7 | `make path-check check-split test-split`; `unittest discover -s tests/control -p 'test_evaluate_tree.py'` | PASS. New `control/evaluate_tree.py`; N1 wired in evaluation; `N1_DISPLACEMENT.md` derives m ≤ 3. 142 control tests. |
| F8 | `make path-check check-split test-split`; `experiments/paper_b/task_cc_live/cc_live_run_task.py --output results/paper_b/task_cc_live_20260927`; `unittest discover -s tests/control -p 'test_task_cc_live.py'` | PASS. New `experiments/paper_b/task_cc_live/`; 8 families (now-best 2, later-best 3, never-best 3). 8 tests; 150 control tests. ENGINEERING_ONLY. |
| F9 | `experiments/paper_b/task_cc_live/cc_live_realism.py --output results/paper_b/task_realism_20260927`; `make check-split test-split` | **FAIL after one recorded repair pass.** R1 and R4 fail for the *typical* behaviour. R2/R3/R5/R6/R7/R8/R9 pass. F10 stops. See [TASK_REALISM_REPORT.md](TASK_REALISM_REPORT.md). |
| F11 | `make -C papers/paper_b verify`; `sh papers/paper_a/scripts/check_anonymity.sh --mode submission` (source repository; script now copied to `papers/paper_b/scripts/`); greps; `pdfinfo` | PASS. §5/§6 rewritten to design v2; N1 as qualifying conclusions. B builds clean at 12 pages; anonymity PASS. |
| F10 | — | Not implemented. F9 FAIL stops F10 per the fix queue. |
| F12 | `make path-check check-split test-split`; `protocols/validate_claims.py`; `make paper-a paper-b` (source repository; B half relevant) | PASS. Added `design_decisions_20260927b.yaml`; contract comparators/allocator/N1; CLAIMS B-C6 aligned. 150 control tests. |
| F13 | 9 planted bugs applied in place, relevant test run, restored | PASS. Every plant caught. No test needed adding. 150 control tests. |

## 8 October — standalone repository verification

Ran in a fresh clone of this repository (`git clone ~/Documents/agent_paper_b`)
at commit `907354b` (the review-correction commit), with a Python 3.13.15
virtual environment outside both repositories built from `requirements.lock`
(adding `hypothesis==6.112.1`, `attrs==26.1.0`, `sortedcontainers==2.4.0`,
`scikit-learn==1.5.2`, `scipy==1.18.1`). The reference is a `git archive` export
of the source at `S = 4154f153` under the same interpreter. The review record is
committed immediately after this file.

| Executed check | Result |
|---|---|
| `unittest discover -s tests/control -p 'test_*.py'` (new clone) | **207 PASS** |
| same command on the S export | **207 PASS** |
| `unittest discover -s tests/release -p 'test_*.py'` | 6 PASS |
| `unittest discover -s tests/standalone -p 'test_*.py'` | 8 PASS; the allowlist test rejects every planted forbidden import, measurement import, dynamic literal and unknown causal_branch module |
| `experiments/paper_b/smoke_b.py --output <scratch>` | **11/11** engineering checks; output byte-identical to the S export (`smoke_summary.json`, `SMOKE_BANNER.txt`) |
| `make smoke-b` | **11/11**; output byte-identical to S; the target removes the tracked `results/paper_b/smoke_latest` first (review M1) and the directory was restored with `git checkout --` |
| `launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase qualification --lane one_step --for-launch` | refuses, exit 1; stdout/stderr byte-identical to S |
| same with `--lane sequential` | refuses, exit 1; byte-identical to S |
| `launch_validator.py --contract protocols/paper_b/contract_v2.yaml --phase <engineering\|qualification\|pilot> --lane <one_step\|sequential> --for-launch` | refuses in all six combinations, exit 1; byte-identical to S |
| `make release-b` | **107 files** in `release/paper_b/` |
| `make check-release-b` | **PASS**: `manifest_matches_source_commit`, `no_cross_paper_paths`, `no_measurement_core`, `no_credentials`, `smoke_exit_zero`, `control_tests_exit_zero`; `pdf_skipped_no_latexmk` (this host has no LaTeX) |
| `make test` | 207 + 6 + 8 PASS |
| `make -C papers/paper_b anonymity-check` | **PASSED** (submission mode) |
| `make paper-b` | PDF build blocked: `latexmk` is not installed on this host. The verify and anonymity halves are recorded separately above |
| `scripts/verify_vendored_pi.py` | fails exactly as at S, exit 1, JSON byte-identical: `unexplained additions to the vendored tree: packages/coding-agent/src/core/http-dispatcher.ts, .../core/sdk.ts, .../test/http-dispatcher.test.ts` |
| Host-path scan (macOS and Linux home-directory prefixes, dataset-root and shared-storage prefixes, the author username, and credential filenames) | clean outside `third_party/pi/`. Remaining hits are upstream `third_party/pi` examples/tests only: `coding-agent/test/footer-width.test.ts`, `test/paths.test.ts`, `test/suite/regressions/6104-find-root-relativization.test.ts`, `coding-agent/CHANGELOG.md`, `coding-agent/docs/rpc.md`, `examples/extensions/doom-overlay/doom/build/doom.js`, `examples/extensions/overlay-qa-tests.ts`, `src/core/export-html/template.js`, `packages/tui/test/terminal-image.test.ts`, `test.sh`, and the two `.jsonl` fixtures. No credential files |

`make check-release-b` rewrote `release/check_release_b.json`; it was restored
with `git checkout -- release/check_release_b.json` afterwards. `make paper-b`
and `make smoke-b` are documented in [README.md](../../README.md) as rewriting
tracked files inherited from S until the targets write elsewhere.

