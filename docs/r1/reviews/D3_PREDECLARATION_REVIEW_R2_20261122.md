**AI-assisted independent review (Claude, fresh session, subagent), 22 Nov 2026, round 2.** Tier E (R1-PROCESS-TIERS).
Under review: commit `7fbee513` (revision 2), branch `mac-d3-predecl-20261122`, against the round-1 review
`docs/r1/reviews/D3_PREDECLARATION_REVIEW_20261122.md` (`72493abc`). PD = `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`,
AN = `docs/r1/authorizations/D3A_AUTHORIZATION_DRAFT_20261122.md`, S = `r1/c3/d3_analysis.py`, T = `r1/tests/test_d3_analysis.py`.
No label, test-partition, evaluation-value, sweep-table or sealed file was opened.

# D.3 pre-declaration and D.3a note, revision 2: round-2 review

## Verdict: ACCEPT WITH MINOR (0 MAJOR, 4 MINOR, 7 NOTE)

All 20 round-1 findings are resolved except MINOR 8, which is partly resolved. None of the four new MINORs changes the
design. Each needs a text fix, and two of them also need a small script or precondition change. Any change to S
re-pins §9/§14 and the AN value.

**Checked.** `pytest T -q` gives 30 passed. sha256 of S is `91295e0d…cc96` and of T `cfe241cb…7c07`, matching PD:402-404,
PD:567 and AN:27. `python -m r1.c3.d3_analysis namespaces` passes. A word-bounded `git grep` of 6301/6302 and `__s6301`/`__s6302` over all
198 refs finds them only in the D.3 files. The compute arithmetic, the MDEs (0.310/0.314, 0.2975/0.301, 0.3045/0.3085,
0.2496/0.252) and the `PaceStyleGate` code (`r1/baselines/responses.py:18-45`, unchanged from `main`) were recomputed.

## Round-1 findings

- MAJOR 1 — **resolved**: EGATE is `PaceStyleGate` (PD:238-269), with G4 at PD:470 and item 4 at PD:495-500. One computed number in it is wrong (new MINOR A).
- MINOR 2 — **resolved**: PD:146-153 says replicate runs are not counted; G8 is "needs changes" (PD:477); G3 spec at PD:469.
- MINOR 3 — **resolved**: the clipped-mean null and its assumptions are stated where the claim is made (PD:250-253). See NOTE 1.
- MINOR 4 — **resolved**: FIXR3 rules at PD:224-230 (the "at most" sentence is reworded), EGATE at PD:263-266, item 19 at PD:531-533.
- MINOR 5 — **resolved**: table read through `guard_table`, sha-checked and filtered to dev first (PD:160-172); `fit_a2` named (PD:174, PD:468). See NOTE 6.
- MINOR 6 — **resolved**: the seven-step order is at PD:19-27. It introduces MINORs C and D.
- MINOR 7 — **resolved**: `REPETITIONS = 1` (S:68, S:233-235); `--d3b-note` / `a6_entered` (S:316-329, S:472-476); tests T:295-328.
- MINOR 8 — **partly**: smoke seeds 6301-6302 are declared (PD:113, S:86, AN:34, AN:60). Its replicate seeds and node are not (new MINOR B).
- MINOR 9 — **resolved**: [sha] marks are on items 1, 2, 3, 6, 10, 12 and 20, and this set is complete (see (g)). Item 9 has a recommendation (PD:508-511); item 16 has a reasoned "not yet" (PD:522-526).
- MINOR 10 — **resolved**: P10 and P11 added (AN:63-64); `layout_chunks` now depends on the repetitions (AN:47). P10 conflicts with P11 (MINOR C).
- NOTE 1 — **resolved; the drafter is right.** 1 − 2,512/5,760 = 0.56389, which gives 35.468 calls, factor 1.7734, and 11.3225 GPU-h × 1.7734 = 20.079.
  Three times that is 60.24, so "60.2" (PD:448) is correct. Round 1's 60.3 came from the rounded 20.10.
- NOTEs 2–10 — **resolved**: 2 at PD:350-354 (numbers verified); 3 at PD:343-344; 4 at PD:344-345 and S:394-396; 5 at S:274-281, PD:391-393 and T:158;
  6 at PD:110-111; 7 at PD:112 and PD:465; 8 at T:61-83 (see NOTE 7 below); 9 at S:299-313 and S:523-527 (refusals echo declared keys only); 10 at AN:49-52.

## Checks requested in the brief

(a) "At least 7 pairs" is correct: λ_1 = 0, λ ≤ ½ and |x| ≤ 1, and 1.5^5 = 7.59 < 10 ≤ 1.5^6 = 11.39. "0.031 by pair 8" is wrong
(MINOR A). The α statement is correct as conditional: E[clip(d_j) | past] ≤ 0 with predictable λ ≥ 0 gives a test supermartingale,
so Ville applies. Independence over seeds is a sufficient modelling assumption. It is per test (NOTE 1). (b) The §13 item 19 rules are
consistent with §5.4/§5.5 and with S's `ended_on` checks (NOTE 2). (c) No CLI bypass: `REPETITIONS` is pinned, extra repetitions are only descriptive, and
`a6_entered` must match the note. S also reads the pre-declaration (hash only), the pinned noise summary and itself (hash only). The note read leaks nothing but is
not hardened (NOTE 4). (d) The fitter follows the existing `dataset.load_table` → `guard_table` route (`r1/c3/dataset.py:523-526`). The table holds no label,
and R1-BX-D8-CONFIRM-V31 (PLAN:1358) opens sweep-2 tables. Filtering to dev first keeps PRE-A2 C and PRE-STAGE A. Compliant (NOTE 6).
(e) MINORs C and D. (f) Seeds clean (above). (g) No other §13 item changes a constant of S, so the marks are complete.

## New findings

**A. MINOR — EGATE's "d ≥ 0.031 by pair 8 (0.034 by pair 7)" is wrong (PD:255-256).**
The formula (1 + (d/c)²)^7 assumes λ = x. But λ is truncated at ½ (`responses.py:40`), and the threshold x = 0.62 is above ½.
There the wealth is (1 + x/2)^(n−1). The correct thresholds are **d ≥ 0.0390 by pair 8 and d ≥ 0.0468 by pair 7**. Running `PaceStyleGate().decide([d]*8)`
gives reject at 0.031, 0.034 and 0.038, and commit at 0.039. The section is labelled "computed, not estimated", so the paper would quote it.
*Fix:* replace the numbers and the formula with (1 + d/(2c))^(n−1) ≥ 10 for d/c ≥ ½.

**B. MINOR — the smoke's FIXR3/EGATE replicate seeds (and its node) are undeclared (PD:111, PD:113, S:102-105).**
`replicate_seeds()` is defined only for 6201-6218. A FIXR3/EGATE smoke would have to invent seeds, and PD:425-426 makes
"any seed outside §4's blocks" a STOP. *Fix:* declare e.g. smoke replicates 6300 + 10(s − 6300) + j (6311-6319,
6321-6329; collide with nothing checked). Add them to `declared_d3_seeds`, name the smoke node(s) in PD:113 and P7, and re-pin.

**C. MINOR — P10 contradicts P11 and the freeze (AN:63-64; PD:115, PD:515-516; PD:24-25, PD:409, PD:418).**
Item 12 [sha] and P10 extend `check_namespaces` in S *after* the pre-declaration is frozen, when the D.3a note is signed. But S's sha256 is pinned in the frozen §14,
"a change after signing is a STOP", and P11 requires S to equal §14. *Fix:* either require the harness verify-seed rule
before step (4), or keep S fixed and put the verify-seed disjointness check in G1's runner or a separate reviewed check that P10 cites.

**D. MINOR — [sha] edits at step (5) come after the independent review at step (4) (PD:22-24).**
If the author picks a non-recommended §13 value, S (tier E) changes after acceptance with no review. *Fix:* add "the changed
S and T are re-checked by the reviewer (diff only) before signing", or settle the [sha] items before step (4).

## Notes

- **NOTE 1** PD:250-253: say "per candidate test". A campaign runs up to two tests, and they share incumbent runs, so the campaign-level false-commit rate can exceed α.
- **NOTE 2** PD:423-424: state whether failed replicate runs count in the 12.99 % pooled worker-failure STOP. Also, a stage-wide STOP on one
  EGATE incumbent replicate failure (PD:264) is costly at 756 campaigns, so consider recommending the listed alternative (discard and record).
- **NOTE 3** PD:254-262: after a full first test (16 runs), the ≤ 4 runs left cannot reach 7 pairs, so they are spent on tests that cannot commit.
  This does not affect Y but does affect usage. Disclose it beside "at most one full test", or add a futility rule (skip a pair when 1.5^(pairs left)·K < 10).
- **NOTE 4** S:316-329: the note read has no size cap and does not catch `OSError`/`UnicodeDecodeError` (it prints a traceback, not REFUSED). It does not check that the
  note is signed (`approved: true`). The note's sha256 is recorded (S:521) but not compared with anything; the D.3b launch record should pin it. Also, the per-node
  start-configuration check is done only in `check_pair` (S:337-341), so a D.3a-only analysis skips it. Move it into `validate_table`.
- **NOTE 5** AN:82 runs the analysis with `--d3b-not-run` and again later with `--d3b`, but PD:410 says "never repeated". State that the second
  run must reproduce the D.3a family exactly.
- **NOTE 6** PD:160 says "exactly two inputs" but the same paragraph also reads the split file and the noise σ. Reword. Also check the table sha against
  the train/dev receipt's `inputs.proposals_sha256` (`r1/c3/release.py:585`), not only against the addendum.
- **NOTE 7** PD:121-122 says every interval with a module constant is cross-checked. For E1b only the base is checked (T:83), and `r1/e2e.py`'s 999 is not checked. Soften the claim or add both checks.

## Could not check
The harness `vary` verify-seed rule, and whether `ComputeBudget` sees controller-issued replicate runs (`autoresearch` is not
installed). The fields of the sweep-2 `proposals.jsonl` (a sweep table, not opened), and whether the R1-BX-D8 check passes at
run time on this checkout. The PACE full text.
