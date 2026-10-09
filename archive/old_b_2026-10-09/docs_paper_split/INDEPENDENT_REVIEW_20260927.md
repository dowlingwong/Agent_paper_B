# Independent review — Paper B controller design v2, task realism, A supplement

Reviewer session, 2026-09-27. Branch `local-work-2026-09-26`, diff range
`9494e0bc..HEAD` (HEAD `c176f266`). Specification:
`B_CONTROLLER_DESIGN_20260927.md`, `FIX_QUEUE_20260927.md`. The implementer's
reports were **not** trusted; every statement below was reproduced from the code
and from commands run in this session. No file was edited except this one; no
models, remote hosts, merges or commits were used.

Environment: `.venv/bin/python` 3.12.7 (numpy 2.3.0, sklearn 1.5.2,
hypothesis 6.112.1); LaTeX present; `rg` absent so the `grep` tool and Python
AST were used.

## Findings

`ID | blocker/major/minor/none | file:line | finding | evidence (command + observed output) | required fix`

H1 | none | experiment_scaffold/src/causal_branch/control/*.py | No function or method that returns an action, regime, score or allocation reads a replay allowance, directly, by attribute or by import. | Custom AST scan (`ast_gate.py`) over `control/**`: no replay-named parameter anywhere; the only "REPLAY-READ" hits are `replay_validity.py` (by design) and `evaluate_tree.py` (N1 evaluation). Only `evaluate_tree.py` imports `replay_validity`; `timing.py`, `allocator.py`, `controllers.py`, `branch_tree.py` do not. | none

H2 | minor | tests/control/test_no_hidden_gate.py:18 | The F2 AST guard only inspects functions literally named `choose`/`decide`/`allocate`/`select`/`policy`/`score`; a controller returning an action under another name (e.g. the real `scores` methods) with a `p` parameter would not be caught. | Read file: `CONTROLLER_NAMES = {...}` excludes `scores`, `predict`, `reserve`. No actual violation exists (see H1), so latent. | Extend the guard to any function whose return is an action/regime/score/allocation, not just name-matched ones.

C1 | blocker | experiment_scaffold/src/causal_branch/control/evaluate_tree.py:95-101 | The evaluated "proposed" and "repeated_myopic" controllers are identical in practice: both are scored by `score_global` (myopic `s1=a1`, proposed `s1=a1−vwait`), and the calibrated allocator selects the same roots. The headline primary contrast is degenerate. | `identity.py` on three fixture worlds: proposed-vs-myopic agreement 150/150, 150/150, 150/150 (proposed-vs-constant_reserve likewise 1.000). `eval_semantics.py` on a world with V̂_wait SD=0.357: contrast point exactly +0.0000, lcb=ucb=0.0000, reading "equivalence". | Remove the degeneracy: make proposed `s1` actually reorder the allocation, and verify proposed≠myopic on the evaluated path (C4). |

C2 | major | experiment_scaffold/src/causal_branch/control/evaluate_tree.py:104-120,224-226 | The "constant_reserve" ablation is byte-identical to "repeated_myopic": both use `fit_global`, `_score` maps both to `s1=a1,s2=a2,vwait=0`, and `_calibrate` chooses the same `(c1,c2,R)`. The intended constant-reserve mechanism is never used by the harness. | `identity.py`: myopic-vs-constant_reserve 150/150 in every world; printed params identical, e.g. `(-0.5,-0.5,2)`. | Give the ablation distinct score/reserve semantics inside the evaluated path, or drop the ablation.

C3 | major | experiment_scaffold/src/causal_branch/control/timing.py:185; evaluate_tree.py:225 | The evaluated BAVAR-inspired comparator has `s2 ≡ 0.0` for every root (`score_bavar_global` sets `a2=vwait=s2=0.0`), so at checkpoint 2 it cannot apply "the same scorer"; it verifies all reached roots or none by the constant `c2`, contradicting design §4. | Direct call: `score_bavar_global(fit_bavar_global(rows),rows)` → `bavar s2 values: {0.0}`. | Implement an H₂ scorer for the comparator (the unused class method `BavarInspiredVOI.scores` sets `s2=a2`, but is not the evaluated path).

C4 | major | tests/control/test_timing.py:105-116 | The F6/F13 identity guard tests the class `reserves()` maps, which are dead in evaluation (U1); it never runs the allocator. Aliasing the evaluated `fit_global`/`score_global` proposed path would fail no test. | Read test + grep: `evaluate_tree` uses module-level `fit_global`/`score_*`; the classes are used only by `matching_report` and `test_timing`. | Guard the actual decision path (regimes returned by `allocate`), not unused methods.

U1 | major | experiment_scaffold/src/causal_branch/control/timing.py:203,222,254,289,305,294 | Six public methods are never executed by the single evaluation entrypoint: `ProposedTiming.scores`, `RepeatedMyopicComparator.scores`, `BavarInspiredVOI.scores`, `ConstantReserveAblation.scores`, `ConstantReserveAblation.reserves`, `FixedRegimeController.scores`. | `coverage.py` (settrace over `evaluate_tree` + `displacement_check`): defined 38, covered 32, UNCOVERED = the six listed. | Either wire the classes into the entrypoint or delete them as duplicate implementations; then fix the coverage test.

U2 | major | tests/control/test_evaluate_tree.py:101-104 | The F7 "17/17 public functions, uncovered: none" claim is reached only because the coverage test filters `inspect.isfunction` over module attributes, which omits class methods. The FIX_REPORT coverage statement is misleading. | Read test; instrumented run (U1) shows 6 uncovered methods. | Include class methods (`inspect.getmembers` on classes); the claim becomes false until U1 is fixed.

L1 | major | experiment_scaffold/src/causal_branch/control/branch_tree.py:229 | `DecisionView` is defined but never instantiated outside tests. `evaluate_tree`/`timing` pass raw row dicts (carrying `u_now`,`u_later`,`u_never`,`h2`) to `fit_global`/`score_global`, so a controller can read leaf outcomes and H₂ at "checkpoint 1". The F5 "only object a controller receives" invariant is not enforced end-to-end. | grep `DecisionView`: definition + tests only. `evaluate_tree._score:95-101` reads raw rows. Direct check: DecisionView does block `outcome()`/`hidden()`/`later_state()` when used; it just isn't used. | Build `DecisionView` in the pipeline and hand only it to scoring, or explicitly record that the invariant is unenforced.

L2 | none | branch_tree.py:140-150,294-381; timing.py:40-42 | Later and never fork from the same checkpoint-2 state (same parent and `history_hash_at_decision`), and folds are by template family. | 150 control tests pass, including `test_later_and_never_share_the_checkpoint2_state` and `test_folds_keep_families_whole`. | none

M1 | blocker | experiment_scaffold/src/causal_branch/control/timing.py:97-104,139-145 | The max-bias correction does not work. The `Y_wait` target used to fit `V̂_wait` uses an in-sample (not out-of-fold) second-stage decision, so `V̂_wait` stays positively biased and is essentially the naive `max(Â₂,0)` in a true-null world, contradicting design §3 step 2. | `maxbias.py` (300 reps, true A₂≡0): cross-fitted mean `V̂_wait` = +0.028/+0.056/+0.112 at noise 0.5/1/2 vs naive +0.028/+0.057/+0.113; a nested out-of-fold target gives +0.0002/+0.0003/+0.0006. `maxbias2.py` confirms the same gap. | Construct `Y_wait` with a per-root out-of-fold `d̂₂` (nested cross-fit), then re-test.

M2 | major | tests/control/test_timing.py:60-68 | The max-bias test cannot detect the failure in M1: it only asserts `|mean V̂_wait| < 0.15`, and the biased values (≈0.118 at noise 2) satisfy that while naive (≈0.119) also satisfies `>0.05`. | `maxbias.py`: at noise=2, `V̂_wait=0.118`, naive=0.119; both assertions pass. | Assert the corrected target is significantly closer to 0 than naive (paired difference CI), not an absolute threshold.

B1 | none | allocator.py:81-143 | Allocator invariants hold: realized calls ≤ `floor(.25·N)` via `budget_for`, ≤1 per root, unspent capacity retained, deterministic hash ties, no phase-2 call for unreached/terminated/infeasible2/already-verified roots. | `budget.py`: "allocator random property trials passed: 20000"; tie run picks the minimum-hash id `c`. | none

B2 | minor | allocator.py:88-92 | `allocate` itself accepts any integer `budget`; it does not enforce `B=floor(.25·N)`. The harness caller always uses `budget_for`, and the bundled property test passes arbitrary budgets, so the guarantee is caller-side only. | Read `allocator.py` + `test_allocator.py:102-128` (`budget=st.integers(0,6)`). | Assert `budget == floor(q*len(roots))` in `allocate` (or document the caller obligation).

N1 | none | bounds.py:27-40 | The Hoeffding width is derived from the declared contrast range `[-1,1]` (width 2), and equals `2·sqrt(log(1/α)/(2n))`. | `eval_semantics.py`: `hoeffding_radius(100,0.05,width=2)=0.24477468306808164` = formula; `radius_for_range==width2` True. | none

N2 | major | evaluate_tree.py:284-287 | `path_allowance` is fed the two primary **contrasts'** grid p-values as if they were checkpoint-1/checkpoint-2 allowances. Design §7 defines `D_path` over checkpoints of a root; the union bound is misapplied. | `p_report` keys are `"proposed-myopic"`/`"proposed-bavar"`; `path_allowance(CheckpointAllowance(p_report["proposed-myopic"]), CheckpointAllowance(p_report["proposed-bavar"]))`. | Compute checkpoint-wise `p₁,p₂` (or state the mapping explicitly) before applying the union bound.

N3 | major | evaluate_tree.py:294-296 | The reported population bound applies the per-root `2p` tax, not the derived `2·m·p` (`m=3`): `population_lower_bound(lcb, 0.02)` subtracts 0.04, while `population_tax_2mp` is computed from a different `p_path`. When the p-grid is empty, `p_path=0.0` yet the bound still subtracts 0.04. | Harness run: `p_grid={None,None}`, `p_path=0.0`, `population_tax_2mp=0.0`, but `population_bound_at_working_p=-0.04`. | Apply `m` consistently and use the same `p` in the tax and the bound.

N4 | minor | docs/paper_split/N1_DISPLACEMENT.md:42-48 | Proof step 3 is self-contradictory ("k2 = B−k1 changes by at most 1 − 1 = 0 ... so k2 changes by at most one"). The bound itself is otherwise sound. | Read doc; independent `displace.py` search over 4000 random batches finds max changed roots = 3. | Reword step 3.

N5 | none | evaluate_tree.py:302-305; N1_DISPLACEMENT.md | The p-grid scope statement is present and `m≤3` is independently reproduced, including my own single-field perturbation search (not only the bundled checker). | `displacement_check(300,24)` → max_changed_roots 3; `displace.py` exhaustive single-field search → worst 3. | none

E1 | none | evaluate_tree.py:128-148,230-264 | Allocator is re-run inside every bootstrap draw; policy value is over all resampled original roots; intervals are Bonferroni-2; the five readings match design §6. | Read code; `eval_semantics.py` prints valid readings and contrast sets. | none

E2 | major | evaluate_tree.py:245-258 | A zero-variance contrast (identical policies, C1) yields `lcb=ucb=0` and is reported as positive "equivalence" evidence, even though it is an implementation artifact rather than evidence about timing. | `eval_semantics.py` waitvar world: point 0.0000, lcb 0.0000, ucb 0.0000, reading "equivalence". | Require a non-degenerate interval and distinct-policy precondition before an equivalence reading.

E3 | minor | evaluate_tree.py:169-180 | Null diagnostics report ranking (correlations) and heterogeneity, but no calibration of `Â₁`, `Â₂`, `V̂_wait` (slope/intercept/reliability) as design §8 requires. | Read `_null_diagnostics`. | Add out-of-fold calibration metrics.

T1 | major | experiments/paper_b/task_cc_live/cc_live_realism.py:30 | F9 task realism FAILS R1 and R4 for the typical behaviour; consequently F10 is stopped. Reproduced exactly. | Re-ran `cc_live_realism.py --families 8`: checks `{R1:False, R4:False, rest True}`; typical regimes now/later/never = 0/5/3, `verify_gain_max=-0.040`. | Genuine signal; F10 remains stopped pending a task/verifier redesign (the queue permits no further tuning).

T2 | minor | docs/paper_split/TASK_REALISM_REPORT.md:12; commit 7d1e83f7 | The "thresholds frozen before the run" claim is not independently verifiable: `THRESHOLDS` was added in the same commit that applied the one repair to the generator and behaviours and produced the results. | `git show --stat 7d1e83f7`: adds `cc_live_realism.py` and modifies `cc_live_generator.py`/`cc_live_candidate.py` together. | Freeze thresholds in a separate prior commit/timestamp.

T3 | none | cc_live_task.py:25,69; test_task_cc_live.py:50-62 | The hidden split lives only in the task object and is never written to the workspace. | Ran a tree: workspace contains only `dev1.csv`, `dev2.csv`, `candidate.json`, `features.json`; no "hidden" file; no "hidden" string in contents. | none

S1 | major | protocols/paper_b/ (absent) | F10 live-run safety cannot be verified: `experiments/paper_b/run_screen.py` and `protocols/paper_b/bind_runtime_artifacts.py` do not exist (F10 was stopped by the F9 FAIL). `--mode live` refusal, pre-dispatch caps and `--dry-run` cannot be inspected or run. | `find . -name run_screen.py -o -name bind_runtime_artifacts.py` → no results; no such files in history. | Implement F10 and its CPU tests before any qualification authorization request.

S2 | none | experiments/paper_b/task_cc_live/; adapters/toy.py | No path in the new task code launches a model or opens a network connection; only `MockModelProvider` is used. | grep for `requests`/`urllib`/`openai`/`socket` under `experiments/paper_b` → no matches. | none

P1 | none | scripts/make_supplement.py | `make supplement-a` builds a deterministic 86-entry / 404,618 B ZIP (≤100 MB) with a recorded SHA-256; independent extraction found no author name, username, host path (except the checker's own regex), or git metadata, and no `.git`/dotfiles. | `make supplement-a` → `86 entries, 404618 bytes`; unzip + grep: no author name, username or host path. | none

P2 | minor | scripts/make_supplement.py:72 | The shipped file `papers/paper_a/scripts/check_anonymity.sh` contains literal host-path and `Acknowledg` strings (its detector regexes), so an unprimed independent scan flags it; the build skip-lists it. Third-party style-kit emails in `.sty`/`.bst` files are not scanned (benign). | `grep -rIl "<host-path pattern>" extract` → only `check_anonymity.sh`; email grep lists only style-kit authors. | Exclude/neutralise the checker's own patterns and document the skip.

M-1 | none | papers/paper_b/sections/05_method.tex:16; 10_related.tex:73 | Manuscript claims match design §8: explicitly "budget-constrained heuristic, not the optimal policy"; no new-method, optimality, safety-guarantee or exclusivity claim; the "reported to" placeholder is gone. | grep for `reported to|optimal|only branch|clean` → only the negated/explanatory usages. | none

M-2 | major | papers/paper_b/references.bib:1286-1293 | The BAVAR citation is not verified at source: the bib note states the preprint page could not be re-fetched (bot protection) and asks for an author re-check, contradicting design §8's "verified 2026-09-27"; the manuscript still cites §4.2 for the signals. Calibrate-Then-Act **is** verified. | `webfetch preprints.org/manuscript/202608.2057` → "Powered and protected by Privacy"; `webfetch arxiv.org/abs/2602.16699` → Ding, Tomlin, Durrett, v3 (matches). Longstaff & Schwartz (RFS 14(1):113-147) and Ernst et al. (JMLR 6:503-556) bibliographic data are correct. | Verify at source or mark the citation unverified and remove the §4.2 attribution until it is.

M-3 | major | papers/paper_b/sections/05_method.tex:60-71; timing.py:166-186 | The manuscript enumerates six BAVAR signals (actor uncertainty/candidate disagreement, action criticality, verifier reliability, expected information value, progress, remaining budget) as implemented, but the comparator uses only H₁ features plus `Â₁` (and `s2≡0`, C3). | Read 05_method.tex:60-64 and timing.py:166-186 (`x = H₁ keys + a1`). | Implement/document the signals, or describe the actual scorer (the documented deviation) in the manuscript.

F1 | none | Makefile:1131-1167 | All F12 acceptance checks pass. | `make path-check` PASS (0); `make check-split` PASS (0); `make test-split` OK — 150 control + 36 measurement + 5 release tests (0); `protocols/validate_claims.py` 21 claims PASS (0); `make paper-a` (0, 27 pp); `make paper-b` (0, 12 pp); `make supplement-a` (0); `git diff --check` (0). | none

F2 | minor | protocols/test_*.py | Out-of-scope `protocols` tests fail (1 failure + 17 errors in `test_manuscript_registrations`/`test_validate_claims`) about paper-track/E0 wording; none of those files are touched by this diff, so they appear pre-existing, but the F12 framing ("all paper_a tests") is silent on them. | `.venv/bin/python -m unittest discover -s protocols` → `FAILED (failures=1, errors=17)`. | Confirm pre-existing and state so explicitly.

## Verdicts

- **B design-ready: no.** Three independent blockers: the max-bias correction does not work (M1) and its test cannot see it (M2); the evaluated proposed controller is not distinguishable from repeated-myopic (C1), making the primary contrast degenerate; and the N1 population tax documented as the paper's scoped sensitivity result is mis-computed (N2, N3). DecisionView enforcement (L1), the BAVAR comparator (C3) and the ablation (C2) are additional majors. The engineering checks (F1) and the allocator (B1) are sound and the A supplement (P1) is clean, but the controller/evaluation core does not yet support the design's claims.
- **task realism: fail.** Reproduced R1 and R4 failures for the typical behaviour (T1); this is a legitimate outcome and F10 is correctly stopped.
- **Ready to request Ada qualification authorization: no.** Task realism fails (T1), and the F10 qualification/screen tooling (`run_screen.py`, `bind_runtime_artifacts.py`) does not exist, so live-run safety is unverifiable (S1). The BAVAR citation is also unverified (M-2).
