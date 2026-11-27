# Report — D.3 G1 final snapshots: terminal keep on both runner routes

**Task:** `compute/20261127-20`; base `origin/main` `c4250f7ea26a97e0f3c7b475613287864110a14c`.
**Result: PASS.** Both blocking findings of the revision-4 step-(5) review are fixed; the reproductions pass; no G6,
G7 or analysis code changed.

- **Task branch:** `compute-d3-g1-final-20261127` @ `ff244366b7168a210a302b37deda5438f83c9e6e` (5 files: the two
  code files, one test file, the unit report and the sorted full-suite id list). Only `r1/c3/d3/snapshots.py`,
  `r1/c3/d3/campaign_chunk.py` and `r1/tests/test_d3_g1_snapshots.py` are code/test changes.
- **Hashes:** `snapshots.py` `5241dcc079f606582a8e9233886a51d93b656aef3362571b4898c9ab748819a2`;
  `campaign_chunk.py` `4131ffcc6946e5fd156ea159e44c466fed8b6de8d3a2e0b88731898976f96f1c`;
  `test_d3_g1_snapshots.py` `c57926a438811e9042af0d2adbed4bcebc11c2d5e270b3d1d2e0d851a1c41ef5`.
- **Review:** `compute-d3-g1-final-review-20261127` @ `d5acf3ab2cdff98cdd6c0e2760f427ebf88df891`,
  **ACCEPTED** (first review accepted with minor findings; the F2 re-check closed them). It reproduced the base
  failures and the tip fixes, ran the focused suite (161 + 18 subtests) and a full suite (114 failed / 4,985 passed;
  117 ids, a strict subset of the base's 120), and verified G6 aliases the canonical W audit and G7/analysis accept
  it.

**What was wrong and what changed**

1. **Harness `final.json` lost a keep on the final trial.** The recorder cached the E1 incumbent and the old
   `write_final` aliased the pre-decision w20 (or used the cached E1 state below W). `campaign_chunk.py` now calls
   `write_final_live`, which reads the live editable files after `run_real_campaign` (the terminal incumbent,
   including a final-trial keep), takes the last kept `budget_index` from the ledger, and uses the post-decision
   controller state captured after the last E1/E2 decision. The exact-w snapshots still keep the E1 state.
2. **Replicate W could produce two valid but different audits.** `write_final_from_state` now canonicalises the at-W
   record: the pre-decision `w20.json` payload is preserved as `w20_pre.json` (plus `pre_decision` and
   `superseded_by`), and `w20.json` is rewritten from the post-decision final (`canonical_final: final.json`). The
   chunk records carry `pre_decision_snapshots`. G6 reads the exact `w5/10/15/20/final` names, ignores `_pre`, and
   aliases one canonical Y(W); G7 and the pinned analysis then pass.

The four conditions of `compute/20261127-04` are preserved: count parity is unchanged, only budget-charged runs are
counted, exact-w snapshots keep the E1 state with no new controller call, and the review confirms the reading. At
`ended_on="error"` the at-W record is deliberately not canonicalised (fail-closed).

**Evidence**

- Base reproduction, harness `9bb41680`: W=20 ledger keep 20 / final keep 19 (live `4b1b4f8d…`, recorded `a12ae00c…`,
  `alias_of: w20.json`); early cap 7 final keep 6 (hashes reversed). Tip with `write_final_live`: both `match: true`,
  final keeps 20 and 7; `w20.json` = final config and `w20_pre.json` = pre-decision config.
- Tests: 161 passed + 18 subtests in the eight D.3 modules; 36 passed in the three recorder/chunk/replicate modules.
  Full suite serial: base 117 failed / 4,980 passed / 3 errors / 163 skipped; tip 117 / 4,982 / 3 / 163; the tip's
  120 ids equal the base's 120 (sorted id-list sha `03339eb1…`, file sha `811be7a9…`). The reviewer's rerun saw 114 /
  4,985 and 117 ids (a subset); three known environment-flaky base failures passed for it and individually here. No
  new failure id in either run. The adapter unit's 111-id list is restored untouched.
- No campaign, server, audit, GPU job or label/evaluation read; the tests are synthetic and CPU-only.

**Decided alone:** to read the terminal config from the live node on the harness route (the harness has applied the
final keep and restored a discard), to preserve the pre-decision W payload as a separate replay record rather than
mutation, and to leave G6/G7/analysis bytes untouched so their revision-4 pins stand.

**Needs:** coordinator merges the task branch and the review branch after its checks; the local worker then repeats
revision 4 step (5) (`local/20261127-16`). No other dependency.

**Task id:** compute/20261127-20. **Branch/tip:** `compute-d3-g1-final-20261127` @ `ff244366`. **Tests:** 161 + 18
focused; full suite zero new ids. **Review:** `d5acf3ab` ACCEPTED. **What happens next:** merge, then step (5).
