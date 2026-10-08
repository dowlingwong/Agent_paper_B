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
at commit `d5c63bd` (after the second AI-assisted review corrections), with a
Python 3.13.15 virtual environment outside both repositories built from
`requirements.lock` (adding `hypothesis==6.112.1`, `attrs==26.1.0`,
`sortedcontainers==2.4.0`, `scikit-learn==1.5.2`, `scipy==1.18.1`). The second
AI-assisted review also ran the checks on Python 3.13.16. The reference is a
`git archive` export of the source at `S = 4154f153` under the same interpreter.
The review records are committed after this file.

| Executed check | Result |
|---|---|
| `unittest discover -s tests/control -p 'test_*.py'` (new clone) | **207 PASS** |
| same command on the S export | **207 PASS** |
| `unittest discover -s tests/release -p 'test_*.py'` | 6 PASS |
| `unittest discover -s tests/standalone -p 'test_*.py'` | **12 PASS**; the allowlist test rejects the planted `import causal_branch.variance_adaptive`, `from causal_branch import variance_adaptive`, `from .. import state_audit`, `import causal_branch.state_audit` in a shared module, `from causal_branch.measurement import facade`, a dynamic `importlib.import_module('causal_branch.variance_adaptive')` literal, and `import causal_branch.deepseek_portal` |
| `experiments/paper_b/smoke_b.py --output <scratch>` | **11/11** engineering checks; output byte-identical to the S export (`smoke_summary.json`, `SMOKE_BANNER.txt`) |
| `make smoke-b` and `make -C papers/paper_b smoke` | **11/11** each, on a clean checkout; output byte-identical to S; the targets remove the tracked `results/paper_b/smoke_latest` first and the directory was restored with `git checkout --` |
| `launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase qualification --lane one_step --for-launch` | refuses, exit 1; stdout/stderr byte-identical to S |
| same with `--lane sequential` | refuses, exit 1; byte-identical to S |
| `launch_validator.py --contract protocols/paper_b/contract_v2.yaml --phase <all five phases> --lane <one_step\|sequential> --for-launch` | refuses in all ten combinations (engineering, qualification, pilot, main_collection, final_evaluation × two lanes), exit 1; byte-identical to S |
| `make release-b` | **108 files** in `release/paper_b/` (adds `requirements.lock`) |
| `make check-release-b` without latexmk, no flag | **FAIL**, exit 2: `pdf_built: false`, `pdf_skip_reason: latexmk not found` |
| `make check-release-b ALLOW_NO_PDF=1` without latexmk | **PASS (PDF not built)**, exit 0, with the same recorded reason |
| `make check-release-b` with a stub `latexmk` on `PATH` (no TeX on this host) | **PASS**, `pdf_built: true`; exercises the success branch. The second AI-assisted review built the real PDF (`pdf_built: true`, 302,691 B) on its host |
| package `tests/control` with only the package's `requirements.lock` installed (fresh venv) | **207 PASS** |
| `make test` | 207 + 6 + 12 PASS |
| `make -C papers/paper_b anonymity-check` | **PASSED** (submission mode) |
| `make paper-b` | PDF build blocked: `latexmk` is not installed on this host. The second AI-assisted review built it (12 pp, verify clean); the verify and anonymity halves are recorded separately here |
| `scripts/verify_vendored_pi.py` | fails exactly as at S, exit 1, JSON byte-identical: `unexplained additions to the vendored tree: packages/coding-agent/src/core/http-dispatcher.ts, .../core/sdk.ts, .../test/http-dispatcher.test.ts` |
| Host-path scan (macOS and Linux home-directory prefixes, macOS temp-directory prefixes, dataset-root and shared-storage prefixes, the author username, and credential filenames) | clean outside `third_party/pi/`. The 13 remaining hits are upstream `third_party/pi` examples/tests/fixtures only: `coding-agent/CHANGELOG.md`, `coding-agent/docs/rpc.md`, `examples/extensions/doom-overlay/doom/build/doom.js`, `examples/extensions/overlay-qa-tests.ts`, `src/core/export-html/template.js`, `test/fixtures/before-compaction.jsonl`, `test/fixtures/large-session.jsonl`, `test/footer-width.test.ts`, `test/paths.test.ts`, `test/session-id-readonly.test.ts`, `test/suite/regressions/6104-find-root-relativization.test.ts`, `packages/tui/test/terminal-image.test.ts`, `test.sh`. No credential files (the only matches are upstream Pi placeholder API-key strings in its own tests) |

`make check-release-b` rewrote `release/check_release_b.json`; it was restored
with `git checkout -- release/check_release_b.json` afterwards. `make paper-b`,
`make smoke-b` and `make check-release-b` are documented in
[README.md](../../README.md) as rewriting tracked files inherited from S until
the targets write elsewhere.

### Dispositions of the first-round findings

| ID | Disposition |
|---|---|
| M1 | Applied: `make smoke-b` removes the tracked `smoke_latest` first and gives 11/11. The sub-Makefile `smoke` target now does the same (R2-B8) |
| M2 | Applied: the two RUNBOOK links are URLs into the source at S; no relative link dangles |
| M3 | Applied; the initial rewrite of historical commands was corrected in R2-B3 |
| m1 | Not applied: `latexmk` is absent on this host, and the rules forbid installing TeX. The build agent recorded it; the second AI-assisted review built the PDF on its host |
| m2 | Applied: `OPEN_ITEMS.md` says `L1_BASELINE.md` is in the source repository at S |
| m3 | Applied: the B copies begin with a two-line provenance note |
| n1 | Applied: the unused `make_release.py` helpers are gone |
| n2 | Not applied, recorded here: the allowlist test allows a local module stem, so `import task` passes because a local `task.py` exists. Benign today; tightening it is not worth the risk |



## 8 October — Stage 0 takeover, fresh GitHub clone

Source: `1554732b1a769abb7138bfa75250e3543fc09121`. Fresh clone from
`https://github.com/dowlingwong/Agent_paper_B.git` into a scratch directory.
Python 3.13.4, as pinned; all dependencies installed from `requirements.lock`.
CPU engineering checks only; no model, GPU or task-realism rerun.

| Executed command / inspection | Observed result |
|---|---|
| `git remote -v`; `git ls-remote origin main` | Correct B URL; remote `1554732b1a769abb7138bfa75250e3543fc09121`. Initial sandbox DNS attempt failed; permitted network retry succeeded. |
| `git status --short`; `rg --files --hidden -g AGENTS.md -g '!.git'` | Only received runbook untracked; only AGENTS is inside vendored Pi (no edits there). |
| `git clone https://github.com/dowlingwong/Agent_paper_B.git <scratch>/b0` | Fresh clone succeeded at required commit. |
| `python3.13 --version`; `python3.13 -m venv .venv`; `.venv/bin/python -m pip install -r requirements.lock`; `.venv/bin/python -m pip check` | Python 3.13.4; 10 locked distributions installed; no broken requirements. |
| `make test` | 207 control, 6 release, 12 standalone PASS; test execution 29.992 / 0.680 / 0.707 seconds. |
| `make smoke-b` | 11/11 PASS; ENGINEERING_ONLY; train/calibration/test records 309/171/195. |
| `.venv/bin/python protocols/paper_b/launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase qualification --lane one_step --for-launch` | Structure OK; exit 1; refuses draft, null runtime/task/configurator/split/budget bindings and missing qualification/engineering/authorization records. |
| Same command with `--lane sequential` | Structure OK; exit 1; same expected refusal classes. |
| `make paper-b` | Real PDF: 12 pages, 302688 bytes; verify clean; anonymity PASS (submission mode). |
| `.venv/bin/python scripts/verify_vendored_pi.py` | Exit 1; inherited unexplained files: `packages/coding-agent/src/core/http-dispatcher.ts`, `packages/coding-agent/src/core/sdk.ts`, `packages/coding-agent/test/http-dispatcher.test.ts`; ledger not changed. |
| `git restore -- results/paper_b/smoke_latest papers/paper_b/main.pdf`; `git status --short` (scratch clone) | Tracked build/smoke outputs restored; clean scratch tree. |
| `command -v python3.13`; `command -v latexmk` | Both available on Mac; Ada not contacted pending D-ADA1. |

The optional `uv python list --only-installed` probe failed because the default
cache is outside the writable roots; the pinned system interpreter was used
instead. A sandboxed local process-list probe was denied, and the permitted
retry identified only the Stage 0 test process. No test repair was needed.

Received runbook SHA-256 (before host-example normalization):
`8d80a3ff1d65a7598da9b8200993f9f9d0bbfcc0a05811fdc9830f14b5567969`.
Home-directory examples in the committed copy use logical placeholders;
no science field or execution gate was changed.

## 5–6 October — historical engineering checks, reconciled 8 October

Source-reported only, from committed
`B_INFRA_CONSTRUCTION_PLAN_20261006.md` (basis, §0.3, §8).
Source implementation `9de9c908`, merge `f463209d`; imported at `a93e2b7`.
These are not commands newly executed during takeover. The retained plan
names the check entrypoints but not their full historical shell invocations;
no invocation or log has been invented here.

| Check named in retained record | Recorded observation |
|---|---|
| `tests/control` (6 Oct, Python 3.13, CPU) | 207 PASS reported by plan v3.1 |
| `smoke_b.py` (6 Oct, CPU) | 11/11 ENGINEERING_ONLY reported by plan v3.1 |
| executor / ledger / configurator / draft contract inspection | Plan records scripted executor (11 tests), ledger (8 tests), configurator scaffold, v3 draft; independently inspected in B during takeover, no Pi/model execution |

## 8 October — Stage 1 documentation verification

Based on Stage 0 `3f93c31`. Documentation changes only. No new scientific
run or implementation test is needed for the decision-sheet handoff.

| Executed check | Observed result |
|---|---|
| `git diff --check` (Stage 0) | PASS |
| Added-content host-path and credential-pattern scan (Python, Stage 0) | PASS; existing inherited content excluded, full new runbook scanned |
| `git push origin main`; `git ls-remote origin main` (Stage 0) | Pushed and verified `3f93c31412a5a62227547ff1a814c3cbc33a4336` |
| Stage 1 Python document check: added-content hygiene, local links, decision-ID coverage, review-scope constraint | PASS: 17 local links resolve; all 24 decision contexts/options/recommendations present; one H1 per new file; source/Paper A exclusion retained |
| `git diff --check` (Stage 1) | PASS |

The historical 28 September fix-round checks remain in the copied records;
no new historical commit validation is claimed. The B2 prompt is prepared,
not a completed review. Stage 1 author answers and science amendments remain
pending; no authorization record has been created or modified.
