# Fix report — Paper B controller design v2, task realism, A supplement

Branch `local-work-2026-09-26`; start `9494e0bc`; F0–F12 implemented, **F10
stopped**, F13 planted-bug check complete. Local CPU only. No merge, push,
release, model call, GPU, paid API, remote host or contact. No stale
`.git/index.lock`; nothing moved to `.git/claude-lock-junk/`. All live studies
are PLANNED.

## 1. Per item

| Item | Commit | Files | Commands / observed | Status |
|---|---|---|---|---|
| F0 | `af380f45` | B_CONTROLLER_DESIGN, FIX_QUEUE, REVIEWER_PROMPT, RUNBOOK §12.2a, README | committed | done |
| F1 | `64c74bda` | `scripts/make_supplement.py`, Makefile `supplement-a`, `.gitignore`, A_RELEASE_CHECKLIST, test_supplement | target builds a deterministic 86-entry / 404,618 B ZIP, 0 findings; planted leaks fail | done |
| F2 | `f7f5a070` | control/controllers.py, test_controllers, test_no_hidden_gate | allowance removed from controllers; c2 bug fixed; AST guard passes | done |
| F3 | `2ccbe7ea` | control/bounds.py, replay_validity, allocation, test_replay_validity | shared width-2 radius; width-1 plant fails | done |
| F4 | `f623163d` | control/allocator.py, test_allocator, requirements.lock | two-phase allocator + hypothesis property | done |
| F5 | `2f46e858` | control/branch_tree.py, test_branch_tree | DecisionView, lineage, ≥2 reps, `policy_value` retired | done |
| F6 | `c1a6e7c7` | control/timing.py, test_timing | proposed rule + comparators; max-bias test | done |
| F7 | `5e52264e` | control/evaluate_tree.py, timing.py, test_evaluate_tree, N1_DISPLACEMENT.md | single entrypoint; N1 in evaluation; m ≤ 3; coverage 17/17 | done |
| F8 | `0ba57b71` | experiments/paper_b/task_cc_live/**, test_task_cc_live, results log | 8 families through the real fork path with the toy mock provider | done |
| F9 | `7d1e83f7` | cc_live_realism.py, cc_live_generator/candidate, TASK_REALISM_REPORT, results | realism **FAIL** (R1, R4) after one repair | done (fail recorded) |
| F10 | — | — | **STOPPED** by F9's FAIL per the queue | stopped |
| F11 | `7f8d7b6d` | paper_b §5/§6/§10, references.bib, main.pdf | design-aligned; 12 pages; anonymity PASS | done |
| F12 | `596444dd` | design_decisions_20260927b.yaml, contract_v2.yaml, CLAIMS, MIGRATION, STATUS | addendum + contract + claims; all accept checks pass | done |

## 2. F9 realism table (thresholds frozen first)

| Check | Pass rule | Run 2 (post-repair) | Result |
|---|---|---|---|
| R1 decision room | each regime best in ≥1 family per behaviour | typical now-best = 0 | **FAIL** |
| R2 context-dependent Vwait | between-family SD > 0.02 | 0.070–0.136 | PASS |
| R3 new checkpoint-2 information | disjoint splits; hidden not in workspace | verified | PASS |
| R4 verifier not redundant | verify − ordinary refit > 0.02 in ≥1 class | typical max −0.04 | **FAIL** |
| R5 harm possible | ≥1 family where verification lowers U | all behaviours | PASS |
| R6 U has spread | baseline mean ∈ [.2,.8], root SD > .05 | 0.578 / 0.087 | PASS |
| R7 reachability | 50–90% | 0.75 | PASS |
| R8 cost fits cap | 512×1350 ≤ 2M tokens; 512×12 s ≤ 10 h | yes | PASS |
| R9 old failure mode | fit tool returns executable candidate | Stump round-trip | PASS |

One repair pass was made (balanced harder target + label noise; careless now
invokes the verifier). R1/R4 remain fail for *typical*: for a competent fit the
verifier does not beat ordinary refit, and checkpoint-1 verification is never
best. Verdict: **task realism FAIL (repaired once)**; F10 stopped.

## 3. F13 plant → test map

| # | Plant | Test that caught it |
|---|---|---|
| 1 | `adv1 − 2*p` in a controller | `test_no_hidden_gate` (1 failure) |
| 2 | proposed aliased to the reserve rule | `test_timing` (1 failure) |
| 3 | Hoeffding width 1 | `test_replay_validity` (2 failures) |
| 4 | evaluator never calls `p_grid_report` | `test_evaluate_tree` (3 errors) |
| 5 | naive `max(A2,0)` continuation target | `test_timing` max-bias (1 failure) |
| 6 | allocator verifies over budget | `test_allocator` (8 errors) |
| 7 | controller reads a leaf outcome | `test_branch_tree` (1 failure) |
| 8 | later/never different checkpoint-2 states | `test_branch_tree` (7 errors) |
| 9 | supplement with an absolute home-directory path | `make supplement-a` refused (host path + username) |

All nine caught; no new test needed. Scratch edits restored; a stale
`__pycache__` left by a plant was cleared, after which 150/150 control tests pass.

## 4. F7 coverage

Entrypoints `evaluate_tree.evaluate_tree` + `displacement_check` execute all
**17/17** public functions defined in `replay_validity`, `allocator`, `timing`
and `evaluate_tree`.  Uncovered: **none**.

## 5. m derivation status

`docs/paper_split/N1_DISPLACEMENT.md` derives `m ≤ 3` for the two-phase
allocator (the root itself, ≤1 phase-1 displacement, ≤1 phase-2 displacement)
and records a planted single-root perturbation attaining 3 over 3 seeds × 300
batches.  Status: **provisional, pending independent review**; the population tax
is `2·m·p_path = 6·p_path`, and the p-grid report states it covers allocation
interference under the derived m (pending review).

## 6. Contract fields still null

`population.{task_law,checkpoint_rule,condition_mixture}`;
`runtime.{model_revision,model_artifact_hash,harness_commit,task_generator_hash,evaluator_revision,tool_versions,continuation_revision,verifier_revision,response_rule}`;
`statistics.{split_manifest,independent_unit_count}`;
`resources.{runtime_ceiling,storage_ceiling,monetary_ceiling}`;
`qualification_report`; `freeze_commit`; all
`qualification.<lane>.{pool,checks,units,engineering_report,authorization}`;
`replay_allowance.{p,provenance,measured_p,p_path}`.  Now set:
`replay_allowance.displacement_m = 3`, `provenance_kind = sensitivity_assumption`,
`working_p = 0.02`; `learning.primary_comparators = [repeated_myopic,
bavar_inspired_voi]`, `ablations = [constant_reserve]`.

## 7. Verdicts

- **B engineering:** CPU engineering implemented and tested (150 control + 36
  measurement + 5 release tests, claims PASS, A/B builds clean, supplement
  builds clean).
- **Task realism:** **FAIL** (repaired once; R1 and R4 for the typical
  behaviour).
- **B design-ready:** **WITHHELD** until `REVIEWER_PROMPT_20260927.md` runs in a
  separate session.
- **F10 (Ada tooling):** STOPPED by the F9 FAIL.

Do not merge, push, release, run models or contact anyone.
