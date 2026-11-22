# Round 2: review of commit `6cd9c74b` (corrections to the "22 November 2026 (d)" rows)

**AI-assisted independent review (Claude, fresh session of round 1, 22 Nov 2026) of commit `6cd9c74b` on
`author-minsub-20261122`, on top of `eb05ff58`; round 1 is `reviews/MINSUB_PLAN_REVIEW_20261122.md`. No human review.
Scope as in round 1. No sealed label or evaluation value file was opened.**

**Verdict: ACCEPT WITH MINOR.** No MAJOR remains. Of findings 1-23: 22 resolved, 1 partly resolved (15). New: 5 MINOR
(one of them the rest of finding 15), 5 NOTE; each fix is one clause or sentence. Short paths as in round 1.

## Status of the round-1 findings

| # | Status | Where |
|---|---|---|
| 1 | Resolved | PLAN:1408 (d): whole-analysis STOP, cites R1-BX-D8-CONFIRM-V31; cost against G5-AR A stated; CUR:66, :81 |
| 2 | Resolved | PLAN:1408 (c): records stay sealed, a read needs a signed amendment; see N4 for instances |
| 3 | Resolved | PLAN:1409: one pre-declaration, hashed before any D.3 run; see N3 for A6 |
| 4 | Resolved | PLAN:1411: named units in tier E; a draft takes the tier of its unit; tier-S review committed; see N5 |
| 5 | Resolved | PLAN:1409: A1 constants under PRE-A2 C, pinned by sha256, unchanged in the arms-frozen record |
| 6 | Resolved | PLAN:1409: required contents listed; D.3b only if the gate passes; amend list completed; see N1 |
| 7 | Resolved | PLAN:1408 (a)-(c): release date, node admission, left-out nodes; see N4 and N6 |
| 8 | Resolved | CUR:57-60; RB:9 "gate read (B.7)" |
| 9 | Resolved (accepted limit) | PLAN:1407, CUR:64, :77: marked to be confirmed |
| 10 | Resolved | CUR:56-63 marked "target"; CUR:40 says the early manuscript start has no row; RB:11 |
| 11 | Resolved | CUR:36 |
| 12 | Resolved | CUR:34, :37, :39, :47 |
| 13 | Resolved | CUR:74-83; `proposals/MINSUB_RECOMMENDATIONS_20261122.md` §3 |
| 14 | Resolved | PLAN:1410: citation corrected; A6 has no offline test read; incomplete folds are not run |
| 15 | **Partly resolved** | PLAN:1407 names §9 items 2, 4, 5, 6; see N2 |
| 16 | Resolved | PLAN:1407 cites RUNBOOK B.7 and §6 and states what the row adds |
| 17 | Resolved | NOV3:24, :28, :29, :33; PLAN:1413 |
| 18 | Resolved (accepted limit) | NOV3:5, :20, :33; `C3_DESIGN.md:193` |
| 19 | Resolved | `proposals/MINSUB_RECOMMENDATIONS_20261122.md`; PLAN:1403 |
| 20 | Resolved | PLAN:1411 (the author decides the row, work waits); PLAN:1412 |
| 21 | Resolved | PLAN:1413; RB:10; NOV3:37 |
| 22 | Resolved | CUR:27 |
| 23 | Resolved | PLAN:1413 (the estimator is named if the GRPO check is reported) |

## The five points the coordinator named

- **(a)** Rules (a)-(e) agree with PRE-T1 A (PREREG:166-170), §4 steps 2-5 (PREREG:228-238) and PLAN:1358. 20 Dec
  minus three days is 17 Dec; on the source of the three days see N6. Gap: N4.
- **(b)** Agrees with RB:36 (pre-declaration), PRE-A2 C and §4 step 4 (A1 constants; PREREG:116-118, :122),
  RB:143 and :363 (gate condition) and RB:345 (A6). Gaps: N1, N3.
- **(c)** Gap: N5. **(d)** Matches PLAN:1217 and `proposals/T4_PROP10_REVISION_20261028.md:244`; the §9 sentence is
  incomplete (N2). **(e)** No decision is made in CURRENT.md; state lines trace to rows or records except N10.

## New findings

- **N1 (MINOR). Wrong section, twice.** PLAN:1409 "§8's required list": PLAN §8 is "Old Paper B evaluated for R1"
  (PLAN:229); the list is in §5 (PLAN:144-153). The row's enumeration also omits §5's "noise-aware keep threshold".
  **Fix:** "§5's required list"; add the missing entry to one of the row's two lists.
- **N2 (MINOR). The §9 amendment is empty for item 4 and misses one case of item 5 (rest of finding 15).** PLAN:1407
  reduces item 4 "as R1-D3-MIN and R1-SUBMISSION-CUTS state", but neither row mentions the action, information or
  model-size ablations (PLAN:291-295). Item 5's held-out-benchmark transfer is lost when PLAN:1408 (d) applies.
  **Fix:** state per ablation "kept as a preregistered secondary arm" or "optional under the 3 Jan rule"; add "item 5's
  held-out-suite transfer is reported as a STOP if R1-ARMS-FREEZE-CUTOFF (d) applies".
- **N3 (MINOR). A6 can enter D.3b without a pre-declared contrast.** PLAN:1409 fixes "every contrast of both stages"
  (rule arms, A3, A5) before any run, then admits A6 later; its contrast (H3, A6 against A5, `C3_DESIGN.md:134`) would
  be written after outcomes exist, against RB:36. **Fix:** add "and A6 against A5, should A6 enter". Also add "A6
  trains on the P3 train and dev label blocks only": it is trained after the test release, when the code lock no
  longer separates the partitions (PREREG:195-199, :265).
- **N4 (MINOR). Rule (c) covers left-out nodes, not left-out instances.** PLAN:1408 (b) supplies a partly labelled
  node whose remaining label runs finish later; PREREG:166 freezes "the T1 node set and its instances". **Fix:** in
  (c), "a left-out node, or an instance of a supplied node that is not in the arms-frozen record".
- **N5 (MINOR). Tier E does not name the code that computes the decisions.** PLAN:1411. The rule layer and the
  deployment controller (`r1/c3/rules.py`, `control.py`, `prior_model.py`, `serve.py`) set every keep and execute
  decision in the gate's utilities and in D.3; the noise-floor code sets δ_n, σ_node and g (PREREG:131-134). They read
  no sealed partition and write no label record, so "other code that a tier-E unit depends on" makes them tier S.
  **Fix:** add "the rule layer, the deployment controller and the noise-floor code" to the tier-E list.
- **N6 (NOTE).** PLAN:1408 (a): "the date model's three days" is `analysis_days_to_b7`
  (`sweep2/t1_tasl/g4_tasl_dates_params.json:24`): labels complete to gate read, not release to arms-frozen record.
  "Planning value" is accurate; name the parameter. PLAN:1369 projects 14-19 GPU-h for phase-1 SFT alone, so measure
  early. The "T1 train/dev release row" is R1-T1-LABELS-UNSEAL (PREREG:285).
- **N7 (NOTE).** PLAN:1407: the 16 Jan projection is in the RUNBOOK top box (RB:29), not RUNBOOK §1.
- **N8 (NOTE).** PLAN:1407: the negative-outcome text rests on T4 Proposition 7's bound, which part (2) of the same
  row classes as not author-checked. CUR:76 says so; the row does not.
- **N9 (NOTE).** PLAN:1407 "the second proposer stays ... in the offline tables": sweep 1 enters only a separate
  descriptive table, and the cross-proposer table has no test read without an amendment (PREREG:89-90, :187).
- **N10 (NOTE).** CUR:46, :48, :49 cite no row (PLAN:1412 asks for one per line). CUR:40 cites a branch that is not
  on `origin` in this clone. STATUS.md:3 says "after 16 Nov"; its last entry is of 14-15 Nov.

## Checked, and not checked

- Checked: `6cd9c74b` changes only `docs/`, in English; `analysis_guard` returns the same confirmation commit
  (`31dab9ef`) for the corrected PLAN; the corrections stay on the `author-*` branch (BRANCHES.md:7-8); the
  recommendations file's statements on the theory audit and the manuscript date match `main`.
- Not checked: external papers and the ICML dates (accepted limits); whether the author adopted each row (settled at
  merge); whether the release step can release a partly labelled node while its label runs continue (the G.5 note is
  not on `main`); files cited from other branches beyond their existence. No test suite was run.
