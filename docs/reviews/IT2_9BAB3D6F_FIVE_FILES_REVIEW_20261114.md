Reviewed base: ec6e30a98811fd6502d168361371a084387c135d (the five files only)

# IT-2: independent review of the five held 9bab3d6f diffs as carried in M3 (14 November 2026)

Author decision IT-2 (A), 14 Nov: an independent review of the five file changes of `9bab3d6f` in M3's accepted commit `ec6e30a9` (`r1/c3/train/run.py`, `r1/c3/train/trainer.py`, `r1/c3/env.py`, `r1/c3/control.py`, `r1/c3/prior_model.py`); the author decides after reading it (R1-B2-REPAIR-SCOPE-ACK); until then Track P reads no real table. One round by a freshly spawned independent reviewer agent (AI-assisted, Claude): **accepted** for these five files only. This is not a review of M3 as a whole and not B.2 launch readiness. Nothing was merged.

Accepted commit (round 1, last): ec6e30a98811fd6502d168361371a084387c135d (five files)

Summary of the reviewer's findings (the round text below is authoritative):
- Identity confirmed: each file's diff `9bab3d6f^..9bab3d6f` equals `a15300ca..ec6e30a9`; contents identical at `9bab3d6f` and `ec6e30a9`.
- The diffs only add refusals; no guard is weakened; on rows without an EVIDENCE marker training, env, AWR and prior outputs are unchanged, except that `run.py` now refuses or strips five evaluation-side field names (no current caller uses them).
- Which diff fixes which test: `run.py` the 8 TrackPStop tests (5 by the new names, 2 by the nested-list walk, 1 by the EVIDENCE block); `trainer.py` the Trainer P.4 test; `env.py` + `prior_model.py` the env/prior test; `control.py` the AWR test.
- 28 Oct finding 3 still stands: marker- and name-based checks are conservative refusals, not proof of isolation (marker-stripped rows, all-seed `delta_audit`/`se`, seed IDs only as values and the `Trainer` `evaluate` callback pass). Findings 1 and 4 (environment freeze, publication) still apply to B.2 launch; finding 2 is resolved.
- Per-file recommendation: acknowledge all five as is, with follow-ups N1–N8 (N2, an allow-list of `delta_label` in `control.py` with a test over all five names, the most worthwhile). Separable from M3 either way.

The round text is reproduced unchanged below.

---

Reviewed commit: ec6e30a98811fd6502d168361371a084387c135d (files: r1/c3/train/run.py, r1/c3/train/trainer.py, r1/c3/env.py, r1/c3/control.py, r1/c3/prior_model.py)

# Independent review IT-2: the five held `9bab3d6f` diffs as carried in M3, round 1 (14 Nov 2026)

The reviewer is a freshly spawned independent Claude subagent that did not write this code. The review is AI-assisted. It was read-only on `/tmp/pb/repo`, with scratch only under `/tmp/rev_it2`: two detached worktrees (`ec6e30a9`, `a15300ca`) and plain `git archive` copies for transplants and mutations. Nothing was committed, stashed, pushed or deleted in any repo. No network was used, no secrets or key files were read, and no label-seed, exam-seed or real sweep data was read. The five pilot-table tests that read `results/r1/engineering/c3_audit_pilot_20261019T001338Z/audits.jsonl`, which holds per-seed audit outcomes, were deliberately **not** run; see §4.

Scope: only the five file diffs, for decision row R1-B2-REPAIR-SCOPE-ACK (`a15300ca:docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` l. 69) and Q24. This review is not a review of M3 as a whole, of the trial conflict resolutions, or of B.2 launch readiness.

## 1. Identity checks (both confirmed)

| File | diff `9bab3d6f^..9bab3d6f` == diff `a15300ca..ec6e30a9` | blob at `9bab3d6f` == blob at `ec6e30a9` | base blob `a15300ca` == `9bab3d6f^` |
|---|---|---|---|
| r1/c3/train/run.py | yes | yes (`ab6e939b`) | yes (`d57e9582`) |
| r1/c3/train/trainer.py | yes | yes (`e096afa8`) | yes (`528439fc`) |
| r1/c3/env.py | yes | yes (`458eda20`) | yes (`6d99677c`) |
| r1/c3/control.py | yes | yes (`989c40f1`) | yes (`73f5543c`) |
| r1/c3/prior_model.py | yes | yes (`34c429c2`) | yes (`3620fd09`) |

`9bab3d6f` is an ancestor of `ec6e30a9` and not of `a15300ca`. The only dependency of the five diffs is `r1/c3/evidence_boundary.py`. It is byte-identical at `9bab3d6f`, `a15300ca` and `ec6e30a9`, so mac-int already has it.

## 2. Per-file analysis

### r1/c3/train/run.py (l. 37, 104–106, 113–119)
- **Change.** (a) `EVAL_COLUMNS` now also matches the exact keys `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics` and `incumbent_metrics` (anchored, so `label_delta_audit`, `label_se_audit` and `delta_true_source` are not matched). (b) `_keys` now walks lists and tuples, under the same depth bound of 6. (c) `guard_rows` refuses identifiable sweep-EVIDENCE rows for every purpose except `p4_final_eval`, and for that purpose only with the P.4 note present.
- **Correct?** Yes. The five names are exactly the all-seed or evaluation-half fields produced by `offline_eval.assemble` (l. 205, 223, 228) and `audit.audit_results` (l. 240). The cycle case is bounded and tested. The inner note check (l. 118–119) is needed: a marked row without eval columns would otherwise return at l. 121–122 without any note check.
- **Guards and results.** No guard is weakened. `guard_rows` still returns the input rows unchanged, and only refusals are added. Two behaviour changes apply to **unmarked** rows. First, the five keys are now refused anywhere in a row, nested lists included. Second, `strip_eval_columns` (l. 131–133) now also drops them. No production caller passes these keys. I grepped `r1/c3/train`, `r1/scripts/trackp*.py` and `mac-trackp-rl-20261114`, and `strip_eval_columns` has no non-test caller. The synthetic E0 path is not affected: `exam_run.e0_rows` gives 3000 train and 1000 test rows, all accepted by `guard_rows` at both commits.
- **28 Oct.** The diff implements the C3/Track P side of the author's 28 Oct seed-role clarification. 28 Oct finding 3 (marker- and name-based, not a proof of isolation) still stands against it; see N1.

### r1/c3/train/trainer.py (l. 118–120)
- **Change.** `Trainer` refuses `purpose == "p4_final_eval"` before `guard_rows`.
- **Correct?** Yes. Before this change, `Trainer(..., purpose="p4_final_eval")` plus any `trackp_p4_*.md` file let evaluation-seed columns into a *training* loop. That hole is now closed. No non-test caller passes this purpose: `exam_run.py` l. 73/80/223, `spike.py` l. 180 and `trackp.py` l. 134 all use the default `"train"`.
- **Guards and results.** It is purely a refusal. No computed result changes.
- **28 Oct.** Nothing is reintroduced. The `evaluate` callback of `Trainer` is still unguarded; this falls under 28 Oct finding 3 (N8).

### r1/c3/env.py (l. 86–90)
- **Change.** `OfflineBanditEnv.__init__` refuses identifiable sweep-EVIDENCE rows for both splits.
- **Correct?** Yes. It is a pure predicate before unchanged code. `label_rows` on an EVIDENCE table yields rows marked `_evidence_seed_split` (`offline_eval.py` l. 190–191), so the env can no longer be built on EVIDENCE tables at all. That is the stated intent: no authenticated purpose separation exists.
- **Guards and results.** Unmarked rows give an identical `evaluate_policy` output at `a15300ca` and `ec6e30a9` (synthetic 40-row equivalence, both splits; same digest).
- **28 Oct.** Finding 3 still stands. Nothing is reintroduced.

### r1/c3/control.py (l. 393–398)
- **Change.** `fit_awr_direct` materialises `rows`, refuses marked rows, and widens the `value_key` denylist from `delta_true` to all five evaluation-side names.
- **Correct?** Yes. On unmarked lists the fitted parameters are unchanged: `test_awr_training_never_reads_the_evaluation_half` asserts equal params, and my synthetic AWR params digest is equal at both commits.
- **Guards and results.** Only refusals are added. The denylist is still a denylist; see N2.
- **28 Oct.** Finding 3 still stands. Nothing is reintroduced.

### r1/c3/prior_model.py (l. 125–129)
- **Change.** `TableArmPrior.fit` materialises `rows` and refuses marked rows.
- **Correct?** Yes. A1 and A2 digests on unmarked rows are equal at both commits, for list and generator input. A3 was not checked locally because `lightgbm` is not installed in the venv; the code path is identical. One side effect is that `offline_arm(name)` (l. 152–154) used through `offline_eval.crossfit` on EVIDENCE rows now STOPs. Crossfit's sanitised training rows keep `_evidence_seed_split` (`offline_eval.py` l. 255), and I reproduced the refusal. Default `crossfit` arms do not go through `TableArmPrior.fit` and are unaffected (N3).
- **Overlap.** It merges cleanly three-way with `trackS-ops-20261030` (`git merge-file`: 0 conflicts).

## 3. The 28 October findings against these exact diffs

| 28 Oct finding (`ac2e9c45`/`023b8c9a`) | Relation to the five diffs |
|---|---|
| 1. Historical runtime freeze not bound; same-environment verification NOT CHECKABLE | Not touched (audit/runner code). Stands for B.2 launch, not against these diffs. |
| 2. Joint-seed protocol uses 7006–7010 for task-level fitting | Resolved by the author's 28 Oct clarification (B.2 task level only; prohibited for C3/Track P training, tuning or selection). The diffs implement the prohibition side. Consistent; nothing is reintroduced. |
| 3. Marker-based boundary cannot identify stripped/unlabelled rows; global isolation NOT CHECKABLE; the guards are not a proof of isolation or acceptance of later training | **Still stands against all five diffs.** They are neither fixed nor worsened. Residual gaps are demonstrated in N1. |
| 4. Classification/pure-move commits unpublished; published-decision guards reject B.2 | Not touched. |
| Runner process-identification tests failing on Mac baseline; Linux validation open | Not touched. |

## 4. Tests

The prescribed command was run in the worktrees with `/tmp/trackg_venv`. That venv has no `torch`, so the trainer tests skip there. They were also run with `/tmp/trackp_venv` (torch 2.6, but no `sklearn`, so `test_a4_calls_the_injected_client_once_and_calibrates` fails there for an environment-only reason and passes under trackg). The set was `test_c3_evidence_other_boundaries`, `test_trackp_trainer`, `test_c3_env`, `test_c3_prior_model`, `test_c3_direct_arms`, `test_c3_rule_controller`, `test_c3_sidecar`, `test_c3_skip_display`, `test_trackp_model`, `test_trackp_e0_v2`, `test_trackp_sidecar_loader` and `test_trackp_cli`. The five pilot-table tests were excluded: `reproduce_offline_eval` (×2 files), `forecast_moments_equal`, `training_rewards_use_label_seeds_only` and `learned_fixed_policy`.

| | ec6e30a9 | a15300ca |
|---|---|---|
| trackg venv | 45 passed, 14 skipped, 0 failed | 35 passed, **10 failed** |
| trackp venv (torch) | 64 passed, 1 failed (sklearn, env-only) | 53 passed, **11 failed** + same env-only failure |
| 8 TrackPStop tests (`-k` on the three test names, whole `r1/tests`) | 8 passed | 8 failed |

All failures at `a15300ca` are in `test_c3_evidence_other_boundaries.py`, which is identical at both commits. Per-file transplants were done on plain copies: "mac + f" means mac-int plus one file, and "M3 − f" means M3 with one file reverted.

| File | Tests that fail without the diff (M3 − f) | Tests fixed by adding only that file to mac-int |
|---|---|---|
| run.py | the 8 TrackPStop tests: `test_trackp_guard_rejects_identifiable_sweep_training`; `…eval_aliases_even_in_prompt_meta[×5]`; `…evaluation_fields_in_nested_sequences[×2]` | same 8 |
| trainer.py | `test_trainer_rejects_p4_even_with_authorization_and_accepts_synthetic_e0` (torch) | same |
| env.py | `test_env_and_prior_reject_identifiable_sweep_rows` | none alone (the test also needs prior_model.py) |
| control.py | `test_awr_rejects_even_when_alias_is_supplied` | same |
| prior_model.py | `test_env_and_prior_reject_identifiable_sweep_rows` | none alone (the test also needs env.py) |

mac-int plus all five files gives every one of these tests passing (53/53 in the torch set). On the integration trial's attribution: of the 8 Track P leak-guard tests, 5 depend on the `EVAL_COLUMNS` alias, 2 on the `_keys` list walk (plus the alias), and 1 on the new EVIDENCE block. So "traced to `EVAL_COLUMNS`" is only partly right; all 8 come from `run.py`. No regression appears in `test_c3_evidence_guards`, `test_c3_evidence_seed_isolation`, `test_c3_evidence_authorization`, `test_c3_sidecar` or `test_c3_skip_display`: mac-int and mac-int plus five show the same 5 pre-existing failures (D8 STOP, harness spoof, attestation), which are unrelated to these files.

**Not run, and why.** The five pilot-table tests read per-seed pilot audits. They were replaced by a synthetic equivalence script on unmarked rows (A1/A2 `TableArmPrior` digests with list and generator input, `OfflineBanditEnv` `evaluate_policy` on both splits, `fit_awr_direct` params). It gives an identical combined digest at both commits (`209221c6…`). The pilot table itself is `ENGINEERING_ONLY` (checked from the `build.json`/`manifest.json` label key only), so it carries no EVIDENCE marker and the new refusals cannot fire on it.

## 5. Mutation check (scratch copies of the `ec6e30a9` tree, torch venv, same test set)

Killed (13 of 17): `_keys` list walk removed; alias alternation removed; `se_audit` alias dropped from `EVAL_COLUMNS`; EVIDENCE block removed; EVIDENCE block opened to every purpose; EVIDENCE-block note check removed; `_keys` depth bound removed; trainer p4 refusal removed; env refusal removed; control refusal removed; `delta_audit_all` dropped from the AWR denylist; `delta_true` dropped from the AWR denylist; prior_model refusal removed.

Survived (4): `se_audit` dropped from the AWR denylist; `candidate_metrics`/`incumbent_metrics` dropped from the AWR denylist (a list value would still fail at `float()`, by accident); `rows = list(rows)` removed in `control.py` l. 395; the same in `prior_model.py` l. 127. None of these weakens a guard that is relied on today (see N2, N6).

## 6. Findings

No BLOCKING findings.

- **N1, NON-BLOCKING (`run.py:111-128`, and by extension `env.py:89-90`, `control.py:396`, `prior_model.py:128`): 28 Oct finding 3 still stands.** The boundary is name- and marker-based. All of the following pass `guard_rows(purpose="sft")` and `is_identifiable_sweep_evidence` at `ec6e30a9`: a label-half row with the marker stripped; the all-seed aggregates `delta_audit`/`se`/`sd`/`k` of a raw 10-seed audit row (when `candidate_metrics` is absent); seed IDs present only as values (`{"seeds": [7006, 7007]}`); suffixed aliases (`delta_true_value`); `label: "evidence"` in lower case. `ARM_CLASSES[...]().fit` and `Trainer(evaluate=...)` bypass the entrances entirely. **Fix:** none possible within these diffs. The acknowledgement row should say "conservative refusals at five entrances; not a proof of training/selection isolation". The lasting fix is the provenance-bound label-only input boundary that the 28 Oct review asks for.
- **N2, NON-BLOCKING (`control.py:397`): the AWR `value_key` check is a denylist.** `y_eval`, `delta_7008`, `delta_true_value` or any other renamed evaluation field passes on unmarked rows. Three of the five entries are untested (mutations survived). **Fix:** allowlist `value_key in {"delta_label"}` (the only caller uses the default) or additionally refuse `EVAL_COLUMNS.search(value_key)`; parametrize `test_awr_rejects_even_when_alias_is_supplied` over all five names.
- **N3, NON-BLOCKING (`prior_model.py:125-129` with `152-154`): `offline_arm` through `crossfit`/`evaluate` on EVIDENCE rows now STOPs.** Crossfit's sanitised rows keep `_evidence_seed_split`. The default arms are unaffected, and no script uses `offline_arm` on an evidence path today. **Fix:** note it in the `offline_arm` and `offline_eval.evaluate` docstrings. A code exception would need its own review.
- **N4, NON-BLOCKING (stale docstrings): `run.py:6-8` and `:112`** (guard described as eval columns only), **`control.py:387-388`** (only `delta_true` named as refused), **`env.py:21-25`** (does not say EVIDENCE rows are refused). **Fix:** update the text.
- **N5, NON-BLOCKING (`run.py:118-119`, mechanism at `:91-93`): the P.4 unlock is a filename-glob existence check.** The new block extends it to EVIDENCE rows. This is still stricter than before, since such rows were previously accepted for every purpose. **Fix:** before any P.4 evaluator is built, bind the note to a published PLAN row and SHA, as `dataset.py` l. 264–275 does.
- **N6, NON-BLOCKING (`env.py:90`; tests for `control.py:395`, `prior_model.py:127`): generator input handling is inconsistent.** In `env.py`, a generator is consumed by the check and then fails with "no rows". That fails closed, and the type is annotated `list`. The `list(rows)` lines elsewhere are untested. **Fix:** add `rows = list(rows)` in `env.py`, and add one generator test per entrance.
- **N7, NON-BLOCKING (`run.py:37`, `:133`): behaviour change on unmarked rows (disclosure).** This is the one change the author packet already flags. No current Track P input is affected (§2). **Fix:** none; record it in the acknowledgement.
- **N8, NON-BLOCKING (`trainer.py:118-122`): `Trainer`'s `evaluate` callback and `purpose` spelling variants are outside the guard.** Spelling variants fail closed in `guard_rows`. The callback can still read anything (finding 3). **Fix:** none within this diff; record it with N1.

## 7. Per-file recommendation to the author

| File | Recommendation | Notes |
|---|---|---|
| r1/c3/train/run.py | **Acknowledge as is** | Fixes the 8 TrackPStop tests. Only refusals, plus the disclosed unmarked-row effect (N7). Follow-ups N1, N4, N5. |
| r1/c3/train/trainer.py | **Acknowledge as is** | Closes the p4-through-Trainer hole. Follow-up N8. |
| r1/c3/env.py | **Acknowledge as is** | Follow-ups N4, N6. |
| r1/c3/control.py | **Acknowledge as is** | Strictly stronger than base. Recommended follow-up N2 (allowlist and test), N4. |
| r1/c3/prior_model.py | **Acknowledge as is** | Follow-up N3 (document the `offline_arm` STOP). Merges cleanly with trackS-ops. |

Any acknowledgement should repeat that these are conservative refusals and not a proof of isolation (28 Oct finding 3), and that it says nothing about B.2 launch (28 Oct findings 1 and 4 remain).

**Separability.** The five diffs can be separated from the rest of M3. Their only dependency, `evidence_boundary.py`, is already identical on mac-int. mac-int plus the five files alone passes all 11 boundary tests with no regression in the neighbouring evidence suites, and `prior_model.py` merges cleanly with trackS-ops. Conversely, M3 can be integrated without them, but then the 11 tests in `test_c3_evidence_other_boundaries.py` fail; each reverted file fails exactly its own tests (§4). The other ~6 of the trial's 16 fixed failures come from M3's other code and test changes, not from these files.

Verdict: accepted
Accepted commit: ec6e30a98811fd6502d168361371a084387c135d
