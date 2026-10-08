# b_tree_v1 — ENGINEERING_ONLY

One record contains one original root and exactly three ordered leaves:
verify_now, verify_later, never. All leaves inherit root ID, template-family ID
and split. Roots cannot repeat; sibling families cannot cross splits.
The root specifies action-dependent reachability, termination after continuing,
availability and nonnegative costs and budget. Each leaf records both actions,
checkpoint-2 reachability, budget after each action and the fixture outcome.

verify_now acts only when available and affordable; otherwise it continues.
verify_later continues first and verifies at checkpoint 2 only when reached,
available and affordable. Early termination, unavailable actions, unreachable
checkpoint 2 and exhausted budget all fall back to continue. Never continues
at both checkpoints. A regime uses at most one verification. Reachability after
verify-now is recorded independently of reachability after continue.

Means use all original roots, including terminated and non-reaching roots.
The synthetic potential outcomes are fixture inputs, not estimated outcomes.
Validation recomputes traces from roots and rejects changed budgets, reachability,
missing leaves, descendant leakage and alternate denominators. These checks do
not establish identification in a real environment.

Run `.venv/bin/python experiments/paper_b/tree_fixtures.py --output NEW_DIRECTORY`.
The driver refuses an existing directory. Fixed regimes and a hand-constructed
greedy counterexample exercise the schema; no sequential learner is implemented.
B-C5 remains PLANNED and later contract phases remain unimplemented.
