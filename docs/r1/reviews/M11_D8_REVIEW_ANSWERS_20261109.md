# M11 D8 — answers to independent review round 1 (9 November 2026)

**AI-assisted; executing agent's answers, for the same reviewer to re-check.** The review: `REVIEW_M11_D8_round1.md` (reviewer scratch `scratch_rev_d8/`), on commits `421a1c38` (gate, tests, report) and `962acd60` (draft). The fixes are new commits on `mac-m11-d8-20261109`; history is not rewritten. `PLAN.md` is untouched and no author row was created.

| Commit | Content |
|---|---|
| `fe453fcb463cafb6475cf6bda67caa392128ed64` | `r1/c3/gate.py`, `r1/tests/test_d8_gate_synthetic.py`, `r1/tests/test_d8_sweep2_reader_refusal_matrix.py`, `docs/r1/reports/M11_D8_GATE_20261109.md` |
| the commit after it (this file) | redrafted `docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261109.md` and this file |

New gate bytes: SHA-256 `007a484ca0852fb663ee4a20df653f830388e5ef193a9d02be3e41b8b3d9693c`, blob `2859f38e39db4aad93949978506824c03935b8a8`, in commit `fe453fcb`. The draft names these. `test_d8_confirm_draft_matches_parser.py` passes: the real guard accepts the drafted row in a synthetic repository holding these bytes.

Tests (the unit's command): 366 passed and 4 failed. The 4 failures are the pre-existing ones in `test_c3_evidence_guards.py`, the same 4 as on HEAD~2.

## Blocking

**1. Real node layout.** *Fixed.*
- `gate.py` pins `T0_NODES` (the D21 pool of 8, R1-DT-PIN) and `SUITES = ('autoresearch', 'MLAgentBench', 'MLGym')` (R1-BX-D2 as amended by R1-1GC-FALLBACK).
- T0 nodes must carry `"suite": null`. T1 nodes must carry a pinned suite.
- `expected_suites` was removed from the input; the input schema is now `r1_d8_gate_input/v2`.
- The per-suite check runs over the three T1 suites only.
- Tests with the real shape:
  - 8 T0 nodes with no suite plus 2 T1 nodes per suite run (the reviewer's `t1_suite.py` layout);
  - each suite without a T1 node STOPs (parametrised);
  - a table of T0 nodes only STOPs.
- Every `evaluate` test now uses this shape.
- On the semantic point:
  - The R1-B7-PARTIAL-T1 consequence ties the "≥ 1 labelled T1 node per suite" condition to leave-one-suite-out.
  - The row text the accepted parser requires states it without that qualifier.
  - The gate keeps the stricter whole-gate STOP and discloses it as an extension: report convention 10, draft item 10, author question Q1.
  - Relaxing it would also need new parser wording.

**2. The SHA binds the whole statistic; NumPy is enforced.** *Fixed.*
- `node_iqm` and the node-equal PoI are inlined as `_node_iqm` / `_node_poi`, with the same arithmetic. A test checks equality with the accepted `d8_point_statistics` on random inputs.
- `gate.py` no longer imports that module. A test pins the import list to the standard library, `numpy` and `analysis_guard`.
- `NUMPY_VERSION = '2.4.4'` is a constant (the harness `uv.lock` pin). `_require_pins()` STOPs on any other version:
  - in `evaluate` and `load_and_evaluate` before the input file is opened;
  - again in `_evaluate`.
- Tests:
  - a mismatch STOPs and opens nothing;
  - a match runs.
- NumPy 2.4.4 and 2.5.3 produced byte-identical `PCG64` draws and quantiles on a ten-size fixture (checked in scratch).
- Which version to pin is author question Q4.
- The draft was redrafted with the new commit, SHA and blob. Its test passes.

## Should-fix

**3. Probability of the whole-gate STOP.** *Disclosed and quantified; the rule is unchanged.*
- I ran my own Monte Carlo (1,000 replicates per cell) over three distributions: normal, left-skewed and right-skewed lognormal. Per-instance oracle − A2 differences; n = 10–150; z = 3–8 test standard errors.
- The table is in the report section "Whole-gate STOP probability".
- Normal case, per node: ≈ 0.07–0.08 at z = 5 and ≈ 0.23–0.31 at z = 4. This agrees with `stopsim.py`.
- Per gate: ≈ 0.52 with 10 eligible nodes at z = 5, and ≈ 0.66 with 15.
- A heavy left tail makes it much worse: ≈ 0.21 per node even at z = 5.
- On a STOP the gate now lists every offending node with its count, which is option (c) of the author question.
- The STOP is kept (briefing option A).
- Alternatives for the author are in Q3: SE-aware dev eligibility; keep and report; post hoc exclusion, which is not recommended.

**4. Holm ranking dual to the pass test.** *Fixed.*
- The ranking key is now (fails the pass test at 97.5 %, composite tail share, A3/A5 order). An arm passing at 97.5 % always ranks first, so the verdict is "some arm passes at 97.5 %" and does not depend on the labels.
- New tests:
  - the reviewer's tie case (`holm_tie.py`): PASS under both labellings;
  - a 400-case label-swap property test built to hit the 50- and 100-draw boundaries. The round-1 code changed 16 of the 400 verdicts under a swap; the fix changes none.
- The duplicate-wording sentence in the report was replaced with the validity argument (Holm/Bonferroni, intersection–union).

**5. Refusal-matrix coverage.** *Fixed.*
- Added `env.label_rows` (called only; the file is unchanged), `audit._verify_replay`, `audit.evidence_blocks` and `dataset.build_from_sweep`. The last uses a synthetic sweep-2 index under `<paper>/results/r1/pilot/`, and that index is also checked as not opened.
- `match` is now `^STOP: .*R1-BX-D8-CONFIRM`.
- With the D8 check replaced by a no-op, the four new readers fail later instead (`JSONDecodeError` or a schema/repository `ValueError` on the synthetic bytes). So their refusal comes from the D8 check. This was checked in scratch and not committed.
- On "Track P loaders": the report says that `r1/c3/train` reads prebuilt datasets, so there is no direct Track P reader of sweep-2 tables to test. Prebuilt training files are the inventory's open item.

**6. The draft's list of frozen conventions.** *Fixed.*
- The report's convention list now has 13 items. It adds: ratio of means, the fractional-edge IQM, exact-equality ties, layout pins and completeness, the whole-gate partial-T1 STOP, δ_n units, input strictness, executing-file binding, and the NumPy pin.
- The draft's "What confirming would mean" lists all 13 and points to questions Q1–Q6.

**7. Node-set completeness and δ_n units.** *Fixed, with one limit disclosed.*
- A missing, extra, renamed or relabelled T0 node, a T0 node with a suite, or a T1 node outside the pinned suites (including null) is a STOP. There is a test for each.
- The T1 node list cannot be pinned because of partial T1. That limit is disclosed in convention 9.
- δ_n units are stated in the module docstring and in convention 11: the 20-run-scaled utility units of U (D18). They are not checked.

## Notes

| Note | Status |
|---|---|
| 8 small nodes | Disclosed in "Scope and limits"; no minimum invented (the rows set none). Author question Q5. |
| 9 overflow / NaN dev denominator | Fixed: a vector whose 4·n·max\|v\| is not finite is refused, and a non-finite dev denominator raises `ValueError`; tests with 1e308 values. |
| 10 duplicate JSON keys | Fixed: `object_pairs_hook` refuses duplicates, `parse_constant` refuses `NaN`/`Infinity`; test. |
| 11 accepted primitives unused | Disclosed in the report; test that the verdict equals `min(holm_two(...)) ≤ 0.05` away from the boundary (300 random cases, > 200 checked). |
| 12 executing file vs checked file | Fixed: `_require_pins()` STOPs unless `__file__` resolves to `analysis_guard.REPO/r1/c3/gate.py` with identical bytes; test (same bytes at another path, absent path). |
| 13 dated 4 Nov template; commit survival | Fixed in the draft: the template form is refused, and the named commit must be merged, not squashed/rebased/cherry-picked. |
| 14 report wording | Fixed: the dangling "§ open questions" is replaced by a real "Questions for the author" section; Holm/Bonferroni/IUT validity added; inference stated as conditional on the fixed node set. |

## Open for the author (also in the report, Q1–Q6)

1. **Q1.** The partial-T1 STOP: does it apply to the whole gate (current) or only to leave-one-suite-out?
2. **Q2.** Are the T0 ids and suite spellings right? Do suite-less 1GC-7RC dataset tasks enter the gate as T1?
3. **Q3.** Nonpositive-denominator STOP versus an SE-aware dev eligibility rule.
4. **Q4.** NumPy pin: 2.4.4 (current) or the version of the venv that will actually run the gate.
5. **Q5.** Minimum n_test per node.
6. **Q6.** Keep ratio of means, exact-equality ties and the fractional-edge IQM.

Any answer that changes `gate.py` changes the SHA. The draft must then be redrafted and the gate re-reviewed.
