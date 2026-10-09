# Final report — NEXT_WORK_QUEUE v2 implementation, 27 September 2026

Branch `local-work-2026-09-26`; base `96aada39`; HEAD `063e35ff`. No merge,
push, release, model call, GPU job, paid API, remote host or external contact
was made. Every live-study statement is PLANNED. Frozen history was read-only.
No `.git/index.lock` existed at any point; nothing was moved to
`.git/claude-lock-junk/`.

## 1. Per item

13 commits; one commit per item (A0 spans A0a/A0b + a record commit; A2 spans
docs + records), plus the bounded `R1` fix pass.

| Item | Commit(s) | Main files | Commands / observed result | Status |
|---|---|---|---|---|
| A0a | `004662c9` | RUNBOOK, SCOPE, README, PAPER_A_TMLR_RUNBOOK, NEXT_WORK_QUEUE, B_DECISIONS, B_NOVELTY_MEMO, MIGRATION, design_decisions, B decision-review logs, AGENT_KICKOFF | committed unmodified | done |
| A0b | `55b7a418` | all `papers/paper_a/**`, A_GAP_REVIEW, A_THEORY_AUDIT, A gap-review logs | committed unmodified | done |
| A0 accept | `a152e1e9` | VALIDATION, STATUS | `make -C papers/paper_a verify theory-check terms-check submission-check`; `make check-split test-split`; 8 calculator tests → PASS; leftover reproduction dir left untracked | done |
| A1 | `965bf1d2` | A_THEORY_AUDIT, A_GAP_REVIEW, CLAIMS A-C2 note, STATUS; intro phrase removal; main.pdf; A_RENDER_QA | reader waived; AI-assisted assessment disclosed; grep clean; Figure 3/CSV byte-identical; pages 1–3 rendered (hashes) → PASS | done |
| A2 docs | `38dfaf2a` | A_INTEGRATION.md, A_RELEASE_CHECKLIST.md | written | done |
| A2 record | `489f3fa1` | A_RELEASE_CHECKLIST, VALIDATION, STATUS | `make release-a` (90 files, no B paths) + `make check-release-a` PASS (5/5); `release/` restored clean; anonymised supplement 417,504 B / 90 entries / 0 real-leak hits (scratch, not committed) | done |
| B1 | `8cbde2d3` | paper_b abstract/sections/appendices/figures/main.tex/references.bib; archive/B1_20260927; MIGRATION | `make -C papers/paper_b verify` clean; anonymity PASS; 11 pp / 7,569 words; no pointwise `LCB-2p`; no `\input` of A; H2 = equivalence; Strategic Verification = TODO | done |
| B2 | `09131bdb` | control/{schema,evaluate,learners,world}.py; smoke_b.py; contract hash; test_u_semantics | invalid=0+reason; collection failure refused as 0; unavailable via fallback; S/U mixing refused; U-primary smoke (11 checks) ENGINEERING_ONLY; 60 control tests | done |
| B3 | `ef0c1505` | control/replay_validity.py; test_replay_validity | scalar-only 2p bound; pointwise gate refused; Bonferroni family; p-grid; `min(1,p1+p2)`; audit arithmetic (24→.11735, 149→.02); 16 tests | done |
| B4 | `6b8b7a86` | control/controllers.py; test_controllers; requirements.lock | repeated-myopic, reserve/VOI, fixed, sampling-only; floor allowed budget; cost ledger; RF witness (sklearn 1.5.2); ridge equivalence 1e-12; 13 tests | done |
| B5 | `fff91719` | control/branch_tree.py; evaluate.py reachability; test_branch_tree | real-fork tree driver; converter rejections; original-root estimators; 10 tests | done |
| B6 | `ec705ce6` | experiments/paper_b/task_cc/**; test_task_cc; results log | 8 fixed-policy witnesses through the real adapter; **all orderings hold**; verifier not redundant; later information exists → WITNESSES_OK (no stop); screen law hash `ade3c319…`; pilot law `449b97c3…` (not run) | done |
| B7 | `f24b3d0d` | contract_v2.yaml; launch_validator.py; QUALIFICATION_AND_SCREEN_LAUNCH_SPEC.md; CLAIMS; STATUS | contract migrated; engineering PASS both lanes; qualification REFUSED (unbound); budget caps; 106 control tests; claims PASS; A/B builds clean | done |
| R1 | `063e35ff` | SELF_REVIEW, A_INTEGRATION, main.tex, main.pdf, contract_v2.yaml, launch_validator.py, render hashes | one fix pass; full check set re-run → all PASS | done |

No item was blocked or stopped. B6's stop conditions were checked and did **not**
fire.

## 2. Self-review summary

Full review in `SELF_REVIEW_20260927.md`. Counts: **blocker 0, major 1, minor 6**.

- Fixed in `R1`: SR-20 (major — contract mislabelled the two N2 primary
  comparators; now `primary_comparators: [repeated_myopic, frozen_reserve_voi]`),
  SR-13 (B comment referenced the A path), SR-21 (`overead` typo), SR-22
  (A_INTEGRATION now records the A2 commits and supplement rule).
- Deferred with reason (no-change): SR-02 (A's pre-existing population cell
  `mean_robust LCB-2p`), SR-06 (per-trajectory vs per-root verification wording),
  SR-17 (Calibrate-Then-Act title from the decision doc), SR-23 (approximate
  MIGRATION source revisions).
- No-change with evidence: all remaining checks (1–7, 9–16, 19).

Planted bugs (check #8) and what caught them:
1. `-p` shift (`lcb - prob` instead of `lcb - 2p`) → `test_replay_validity` (2 failures).
2. Reached-only denominator accepted → `test_branch_tree` (1 failure).
3. Invalid outcome allowed a nonzero U → `test_u_semantics` (1 failure).

Scratch edits were discarded; all three test files pass afterwards.

## 3. Verdicts

- **A: ready for A-only integration review.** Tier 1; human theory reader waived
  and the AI-assisted mathematical assessment disclosed as AI-assisted. The A
  release closure has no B-only file; the dry run passes. Author-only fields
  remain **blank** (ETAAI archival confirmation, author list and OpenReview
  profiles, funding/conflicts, title choice, supplement yes/no, merge route).
  Proposed defaults shown but not applied.
- **B engineering: CPU ENGINEERING READY.** U pipeline, population-scoped
  allowance, matched controllers, real-fork tree, candidate-consistency
  witnesses and contract v2 all pass their engineering checks; no live evidence
  is implied.
- **B design-ready: WITHHELD pending independent review.** Not self-awarded.
- **B qualification / pilot / main / submission: NOT EARNED.**

## 4. Contract fields still null

`population.{task_law,checkpoint_rule,condition_mixture}`,
`runtime.{model_revision,model_artifact_hash,harness_commit,task_generator_hash,evaluator_revision,tool_versions,continuation_revision,verifier_revision,response_rule}`,
`statistics.{split_manifest,independent_unit_count}`,
`resources.{runtime_ceiling,storage_ceiling,monetary_ceiling}`,
`qualification_report`, `freeze_commit`,
`qualification.{one_step,sequential}.{pool,checks,units,engineering_report,authorization}`,
`replay_allowance.{p,provenance,measured_p,p_path}`.
`replay_allowance.provenance_kind = sensitivity_assumption` and
`working_p = 0.02` (working assumption, never measured).

## 5. Exact next external step

Bind the Devstral-Small-2-24B-Instruct-2512 artifacts on Ada, per
`protocols/paper_b/QUALIFICATION_AND_SCREEN_LAUNCH_SPEC.md` §1. The intended
command (executor written later; **not run here**):

```sh
python protocols/paper_b/bind_runtime_artifacts.py \
  --contract protocols/paper_b/contract_v2.yaml \
  --server-url "$ADA_SERVER_URL" \
  --harness-commit "$(git -C "$ADA_HARNESS" rev-parse HEAD)" \
  --model-root "$ADA_MODEL_ROOT" \
  --out protocols/paper_b/runtime_bindings_2026.json
```

After binding, run qualification for both lanes, then the 96-leaf bounded screen
(§4 of the launch spec), then the 384-leaf pilot, then the COMBINE / CORE_ONLY
route decision. These need the Ada host and a separate author authorization.

## 6. Stop

Do not merge, push, release, run models or contact anyone. This report ends the
authorized local work.
