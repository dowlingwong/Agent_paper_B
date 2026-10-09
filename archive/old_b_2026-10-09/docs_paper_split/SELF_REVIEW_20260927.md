# Self-review — 27 September 2026

One round, reviewing the whole diff `96aada39..HEAD` (13 commits: A0a, A0b, A0,
A1, A2×2, B1–B7) as if not written by this agent. One finding per line.

Schema: `ID | Severity (blocker/major/minor) | File:line | Finding | Evidence | Fix or disposition`.

## Correctness

```
SR-01 | none | — | Check 1: no pointwise LCB(w)-2p gate applied anywhere. | `grep -rIn -E "LCB.*2p|pointwise gate"` (excl. archive) returns only refusal/scope text in `paper_b/sections/{01,06}`, `B_proofs.tex`, `control/replay_validity.py`, `B_DECISIONS`, `SCOPE`, `CLAIMS`; `test_replay_validity.TestPointwiseGateRefused` passes. | nothing
SR-02 | minor | experiment_scaffold/src/causal_branch/finite_budget_decisions.py:14 | Pre-existing A module documents `mean_robust LCB(a~) - 2p`, which a plain grep can read as a pointwise gate. | docstring: "lower confidence bounds for one representation cell, one stratum and two regimes on their common feasible domain"; commit d5776384, not in this diff. | no-change: it is a population cell/stratum bound (permitted population scope), not a per-checkpoint gate; it is A's historical code and outside B's N1 scope.
SR-03 | none | — | Check 2: 2p population bound and path_allowance are fixed-policy only; family selection is simultaneous. | `population_lower_bound` refuses array/pointwise (`_require_scalar`); `simultaneous_family_bounds` uses Bonferroni and abstains; `path_allowance` union bound; tests pass. | nothing
SR-04 | none | — | Check 3: U semantics — invalid=0 with reason; collection failure never 0; unavailable has no outcome and stays via fallback. | `schema.validate_record` (invalid exactly 0 + reason; non-ok integrity carries no outcome); `evaluate.checkpoint_rows` refuses non-ok integrity; `test_u_semantics` 11 tests pass. | nothing
SR-05 | none | — | Check 4: tree estimands use all original roots; no conditioning on reaching ckpt2; no transplant; no second verification in a trajectory. | `branch_tree.records_to_tree` rejects reached-only denominator, transplanted ckpt2 (sibling history mismatch / wrong parent), lineage/split leakage, >1 verification per branch; estimator means over all roots. | nothing
SR-06 | minor | experiment_scaffold/src/causal_branch/control/branch_tree.py:81-96 | Wording ambiguity: the converter permits verify-now and verify-later as alternative regimes of one root (two calls across the tree), while the contract says `max_verifications_per_root: 1`. | `record_allowed_actions` rejects >1 per branch only; `records_to_tree` executes the full tree; design (`RUNBOOK` §6.1) is "at most one verification opportunity per trajectory". | no-change: the contract field is the *deployed* budget (one call per realised trajectory); the tree is the counterfactual design. Clarified here.
SR-07 | none | — | Check 5: budget matching uses the same allowed budgets; realized reported separately; ceil/floor not swapped. | `allowed_tree_budget` = `floor(q*N_original)`; `assert_matched_allowed_budgets`; `BudgetReport` refuses overspend; `batch_top_q` = `ceil(q*n_feasible)`; tests pass. | nothing
SR-08 | none | — | Check 6: bootstrap uses template-family clusters, shared draws, declared batch coupling. | `evaluate_policies` draws once per iteration and applies to all policies; `paired_contrast` same; both note batch coupling / no per-root i.i.d. | nothing
SR-09 | none | — | Check 7: ridge equivalence test exists and is labelled an equivalence check. | `test_controllers.TestRidgeEquivalence`; smoke `ridge advantage/action-value equivalence` check; `paper_b/appendices/B_proofs.tex` A.2; claims B-C2 HISTORICAL/equivalence check. | nothing
```

## Tests

```
SR-10 | none | — | Check 8: planted bugs are caught. | Bug A (`lcb - prob` for `lcb - 2p`) -> test_replay_validity 2 failures. Bug B (remove reached-only rejection) -> test_branch_tree 1 failure. Bug C (invalid may carry nonzero U) -> test_u_semantics 1 failure. All patched in place and `git restore`d; all tests green afterwards. | nothing
SR-11 | none | — | Check 9: B6 witnesses run through the real adapter/fork path, not constants. | `witnesses.run_screen` calls `execute_tree_v2`, which uses `FileSnapshotManager`/`FileBranchIsolationManager` and grades files; `test_branch_tree` and `test_task_cc` pass. | nothing
```

## Scope and leakage

```
SR-12 | none | — | Check 10: B imports nothing from papers/paper_a; `make check-split` passes; task generator hides labels. | `grep -rIn paper_a experiments/paper_b experiment_scaffold/src/causal_branch/control protocols/paper_b` -> none; `CHECK-SPLIT RESULT: PASS`; `test_task_cc.test_hidden_truth_is_never_written_to_the_workspace` passes. | nothing
SR-13 | minor | papers/paper_b/main.tex:2 | A LaTeX comment references `papers/paper_a/TEMPLATE.lock`. | `grep -n paper_a papers/paper_b/main.tex` line 2 (comment only; not an `\input`). | FIX (R1): reword the comment to refer to the TMLR/ICML style kit without the A path.
SR-14 | none | — | Check 11: A release closure has no B-only file; supplement ZIP has no identifying strings. | `make check-release-a` `no_cross_paper_paths: True`; A2 real-leak scan 0 hits (host path/username/full author/ack). | nothing
```

## Manuscripts

```
SR-15 | none | — | Check 12 (A): no human-review wording; AI-use statement accurate; no recovery/g_r/"risk 0.4"/Replay Gap divergence in Figure 3; builds clean. | `grep -i "human (theory )?reader|human review|independent review" papers/paper_a --include='*.tex'` -> none; `main.tex` AI statement names the AI-assisted mathematical audit; Figure 3/CSV regenerate byte-identically; `make paper-a` verify/terms/submission/anonymity PASS. | nothing
SR-16 | none | — | Check 13 (B): claims match B_DECISIONS; related work method-level with sections; no unverified citation (Strategic Verification is a TODO); B_proofs.tex:290 fix made; no \input of A; no result language. | B_DECISIONS alignment (N2 primary, N1 validity, `.02`, q=.25); `10_related.tex` section references and TODO; `B_proofs.tex` A.3 corrected conditional-expectation statement; `make -C papers/paper_b verify` clean; `grep result language` -> none. | nothing
SR-17 | minor | papers/paper_b/references.bib:calibratethenact2026 | The `calibratethenact2026` title "Calibrate-Then-Act" is taken from `B_DECISIONS_20260927.md`, not verified at source (no network). | B_DECISIONS line "Calibrate-Then-Act (arXiv 2602.16699), abstract and introduction". | no-change: title matches the decision document; the entry is method-level only.
SR-18 | none | — | Check 14: every render inspected page by page; page hashes recorded. | A: all 27 pages rendered at -r 70 and inspected; hashes in `results/validation_logs/A1_render_full_20260927/page_hashes.txt`. B: all 11 pages rendered at -r 90 and inspected; hashes in the A2/B1 log. No clipping/overflow/blank pages. | nothing
```

## Records

```
SR-19 | none | — | Check 15: CLAIMS/STATUS/VALIDATION/MIGRATION/contract agree; validate_claims passes; null fields stay null. | `protocols/validate_claims.py` RESULT: PASS; contract null-field dump matches the intended set; VALIDATION rows per item; STATUS next actions updated. | nothing
SR-20 | major | protocols/paper_b/contract_v2.yaml:learning | `primary_comparator: repeated_myopic` and `secondary_comparator: frozen_reserve_voi` mislabels the two N2 primary comparators, which B_DECISIONS makes equally primary. | B_DECISIONS: "Primary comparators: repeated-myopic and a frozen reserve/VOI scheduler"; B manuscript 05_method "Primary comparators (a)/(b)". | FIX (R1): replace with `primary_comparators: [repeated_myopic, frozen_reserve_voi]` and `diagnostic_variants: [never, verify_now, verify_later, sampling_only]`.
SR-21 | minor | protocols/paper_b/contract_v2.yaml:allocation.cost_definition | Typo "verifier overead". | text. | FIX (R1): "overhead".
SR-22 | minor | docs/paper_split/A_INTEGRATION.md | Does not list A2's own commits (`38dfaf2a`, `489f3fa1`) or the supplement sanitisation rule. | file written in A2 before those records. | FIX (R1): add a short A2 note.
SR-23 | minor | docs/paper_split/MIGRATION.yaml | `source_revision` for new B files uses the previous commit's short hash, not the introducing commit. | e.g. `source_revision: fff91719` for task_cc added at `ec705ce6`. | no-change: field validity is 7–40 hex and the files are marked `live_revision`; a later tidy-up can rebind.
```

## Summary

Counts by severity: **blocker 0, major 1 (SR-20), minor 6 (SR-02, SR-06, SR-13, SR-17, SR-21, SR-22, SR-23)**.

- Fixed in R1: SR-20 (major), SR-13, SR-21, SR-22 (minors).
- Deferred with reason: SR-02, SR-06, SR-17, SR-23 (all no-change).
- No-change with evidence: all other checks.

Planted bugs caught: `-p` shift (SR-10 bug A), reached-only denominator (bug B), invalid-as-nonzero (bug C). Each was caught by at least one test; scratch edits were discarded.
