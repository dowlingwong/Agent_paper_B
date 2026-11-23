# Review of commit `eb05ff58` (author rows "22 November 2026 (d)", CURRENT.md, novelty sweep part 3)

**AI-assisted independent review (Claude, fresh session, 22 Nov 2026) of commit `eb05ff58` on `author-minsub-20261122`,
against `origin/main` `3c3f822a`. No human review. Scope: consistency, traceability, executability; the scientific
choices are not judged. No sealed label or evaluation value file was opened.**

**Verdict: REVISE.** 4 MAJOR, 14 MINOR, 6 NOTE. Every fix is text only; no code or signed note needs to change.
Short paths: PLAN = `docs/r1/PLAN.md`, PREREG = `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`,
CUR = `docs/r1/CURRENT.md`, RB = `docs/r1/RUNBOOK.md`, NOV3 = `docs/r1/inputs/NOVELTY_SWEEP_PART3_20261122.md`.

## MAJOR

1. **R1-ARMS-FREEZE-CUTOFF restates the leave-one-suite-out STOP as a per-suite "not run".** PLAN:1408 ("for a suite
   without a labelled node is reported as not run"); CUR:76 ("can cost at most that one node and its suite's fold").
   Frozen: PLAN:1358 (R1-BX-D8-CONFIRM-V31, "otherwise leave-one-suite-out STOPs"), PREREG:180-181, :270, :243-244;
   the reviewed module STOPs the whole analysis before any statistic (`r1/c3/fold_analysis.py:6-8, 170-172`). The
   node most likely to miss the date is `autoresearch_fixedtokens`, the only node of its suite, so the cut-off can
   remove the whole primary generalisation test. It also sets aside the stated reason of R1-G5-DECISIONS G5-AR A
   (PLAN:1397), which PLAN:1403 says stands. **Fix:** "if a suite has no labelled T1 node at the cut-off, the whole
   leave-one-suite-out analysis STOPs and is reported as a STOP; a remedy needs an author row"; correct CUR:76; say
   that the cut-off may undo the purpose of G5-AR A.
2. **The same row allows a later table that the preregistration forbids.** PLAN:1408 "Such a node may appear later
   only in a clearly separate, non-primary table". PREREG:169-170 (PRE-T1 A): "A later read with more T1 nodes is not
   allowed"; option B (:171-172, a later secondary read) was not chosen; PREREG:176 limits test reads to arms in the
   arms-frozen record. The row cites PRE-T1 A as allowing it. **Fix:** delete the sentence, or: "its test labels and
   evaluation values stay sealed unless a signed preregistration amendment allows a read; only label-free facts
   (counts, noise floor, run status) are reported".
3. **R1-D3-MIN lets the D.3b contrasts be declared after D.3a outcomes exist.** PLAN:1409 ("Each stage needs its
   pre-declaration ... before it starts"; the stages share instances and seeds so arms are paired). RB:36 requires
   contrasts, sample sizes and analysis script "committed with a hash before any outcome exists". The learned-arm
   contrasts (A3 or A5 against A2 and A0) would be fixed with one side already observed. **Fix:** one
   pre-declaration for both stages, hashed before D.3a starts (all contrasts, instances, seeds, sample sizes,
   script); the D.3b note may add only the frozen arms' sha256s.
4. **R1-PROCESS-TIERS puts evidence-bearing units below tier E.** PLAN:1411. Tier E lists runs, readers of sealed
   or test partitions, preregistrations, notes, launch bindings and gate code. By the tier-S definition ("feed a
   tier-E unit but no claim directly") these fall to S: code that writes, admits or parses label and evaluation
   records (audit, the D4-B path of PLAN:1382, the collection change of PLAN:1349, G.5 drivers, metric parsers);
   arm training, selection and calibration code and the arms-frozen record (PREREG:229-236); D.2 pre-declarations
   and D.3 analysis scripts. Tier D ("proposals, prompts") takes draft notes, preregistration drafts and launch
   prompts. In tier S a fix to a minor finding merges unchecked; in tier D nothing is recorded. Main requires a
   committed review re-checked "until it writes accepted" (`prompts/MAC_LOCAL_RUNBOOK_20261104.md:67-71`;
   `prompts/FOLLOWUP_PROMPTS_20261119.md:35`). **Fix:** add the units above to tier E by name; a draft takes the tier
   of the unit it becomes; state that a tier-S review record is committed under `reviews/`.

## MINOR

5. **"Reads no label table" is not true of D.3a as specified.** PLAN:1409. A1's constants are fitted on dev campaigns
   (`C3_DESIGN.md:86`; PREREG:112-118), so A1 and A2 need the sweep-2 dev label block, which does not exist until the
   sweep-2 audit is registered and released (PLAN:1366). **Fix:** "reads no test label, no evaluation value and no
   T1 label; A1's constants are those of PRE-A2 C, pinned by sha256 in the pre-declaration and entered unchanged in
   the arms-frozen record"; name the dependency on the sweep-2 train/dev release.
6. **R1-D3-MIN leaves these to guesswork** (PLAN:1409): T0 node set (seven or eight; `openml_wdbc`); memory mode(s);
   values of W and the LLM-call cap; K and seeds of the audited Y; audit host (deepthought was allowed "for this
   audit only", PLAN:1391); whether D.3b runs if the gate fails (RB:143, :363 "only if B.7 passes" are not in the
   row's amend list); whether the reference arms of R1-C3 (ladder) (PLAN:420) and the required baselines of PLAN:144-153
   are cut, offline only or optional; whether the "anytime-valid gate" is the PACE-style gate of PLAN:147.
   **Fix:** list them as required contents of the pre-declaration and complete the amend list.
7. **R1-ARMS-FREEZE-CUTOFF does not say what happens on the date.** PLAN:1408 uses one date for "labels released"
   and "record signed", but arms, fold arms and secondary arms are trained after the release (PREREG:228-236).
   Missing: the latest label-release date (cut-off minus measured training time); a partially labelled node
   (PREREG:167-168 admits one with at least 1 train and 1 dev instance; test floor :248); whether G.5 keeps running
   on a left-out node; whether R1-T1-LABELS-UNSEAL may name a subset. **Fix:** add the four rules.
8. **B.7 has two meanings.** CUR:58 dates "T1 labels and audits complete" at about 15 Dec. On main B.7 is the gate
   STOP (RB:143) and equals labels done + 3 days (`sweep2/g4/g4_lib.py:668`; `sweep2/t1_tasl/g4_tasl_dates_params.json:24`),
   so the 15 Dec of R1-G5-DECISIONS is the gate read and labels are done about 12 Dec. RB:9 then lists B.7 before the
   record that must precede it. **Fix:** CUR:58 "about 12 Dec labels done; about 15 Dec gate read (target)"; state
   that at the cut-off the gate read is on or after 20 Dec; reword CUR:65.
9. **ICML dates are not traceable.** PLAN:1407, CUR:63, RB:9 give "abstract 14 Jan, paper 22 Jan" as fact. Main has
   only a projection of about 16 Jan and 22 Jan, "not yet announced" (RB:29); `git grep "14 Jan"` on main finds
   nothing. **Fix:** cite the call for papers with the date read and the time zone, or write "projected".
10. **Dates and decisions that exist only in the RUNBOOK box or CURRENT.md.** "D.3a early to mid December", "D.3b from
    the gate read to 3 Jan" / "22 Dec to 3 Jan" (RB:9, CUR:57, :60, cited to R1-D3-MIN, which has no date); "mock
    review until 13 Jan" (CUR:62; R1-BX-D14 has only 10 Jan); "not checked by 3 Jan leave the main text" (CUR:75);
    "written from 22 Nov" and branch `mac-manuscript-20261122` (RB:11, CUR:40; changes R1-BX-D14's "from early
    December", PLAN:758, with no row). **Fix:** move them into the rows, or mark each "target, no row".
11. **CURRENT.md misstates the label release.** CUR:36 "Train and dev blocks of sweep 1 and sweep 2 are released".
    PLAN:1366: sweep 2's release STOPs until its audit is run and registered; CUR:34 says that audit only started.
    **Fix:** "sweep 1 released; sweep 2 after its audit is registered".
12. **Other CURRENT.md statements not on main.** CUR:34 "audit started 22 Nov": main records the authorization only
    (PLAN:1391; no start record in `reports/s2_audit_20261121`, `reports/s2_d4b_20261122`, STATUS). CUR:39 "every
    statement awaits the author's proof check" contradicts R1-T4-PROOF-CHECK (PLAN:1217; `reviews/T4_PROP10_REVISION3_REVIEW_20261116.md`):
    Prop. 8', 10(a') and 10(c) are accepted with errata; CUR:75 and PLAN:1407 (2) do not say which statements are
    still open. CUR:37 "A5 and A6 must be frozen before the gate read" is in neither cited row; RB:345 trains A6
    after B.7 passes. CUR:47 makes deepthought the standing T0 audit host. **Fix:** correct or cite each.
13. **"Open for the author" (CUR:73-80) adds proposals and omits open points.** Items 2 (G.5 run order), 5 (ICML
    quota) and 6 (a dev-tuned threshold arm, "add it to D.3a") are in no row; item 6 also conflicts with finding 5.
    Missing: the G.5 note's signature (PLAN:1397); the D.3b pre-declaration and note (item 4 names D.3a only); the
    points of findings 6 and 7. **Fix:** move the three proposals to a `proposals/` file and add the missing items.
14. **R1-SUBMISSION-CUTS cites rows that do not exist and analyses the preregistration does not hold.** PLAN:1410.
    (a) "R1-SEQ rows": no such id in PLAN §10; cite R1-T4-PROOF-CHECK (PLAN:1217), which defers the forced-branch
    test. (b) "A4 against A5/A6 offline" and "fold retraining of A5 or A6": A6 is not a gate series
    (`r1/c3/gate.py:147`) and not a PRE-SECONDARY A arm (PREREG:186); trained after the gate, it cannot be in the
    arms-frozen record, so an A6 test read needs a signed amendment. (c) "the table reports the arms that did" cannot
    run on the reviewed fold module, which refuses a missing fold arm (`fold_analysis.py:175-177`); a fold arm absent
    from the arms-frozen record never reads test (PREREG:176). **Fix:** correct the citation; limit A6 to D.3b or
    name the amendment; replace (c) with "a fold whose arms are not all in the arms-frozen record is not run".
15. **PLAN §9 is relaxed without being named.** PLAN:279-309 ("must meet all"): items 2 (baselines), 4 (ablations),
    5 (second proposer in closed loop) and 6 (every C2 statement author-checked; PLAN:1407 (2) allows unchecked
    appendix statements) no longer hold under PLAN:1407 and :1410. **Fix:** "amends §9 items 2, 4, 5, 6 as follows",
    so that RB E.4's checklist can be run.
16. **Wrong fallback citation.** PLAN:1407 "as §3's fallback already provides": PLAN:78 is the headroom-gate fallback
    of the 9 Oct plan. The C3-gate fallback is RB:143 and RB:396 ("C3 reported as the measured negative; C1 + C2
    carry the paper"), and the new wording differs from it. **Fix:** cite RB B.7 and §6 and say the row replaces them.
17. **Novelty note against the earlier files.** (a) NOV3:32 "arXiv 2610.15738 (still not fetched since part 2)":
    `inputs/NOVELTY_FULLTEXT_20261019.md:12` read its main text through a mirror on 19 Oct (appendices missing).
    (b) NOV3:32 "the five Snippet rows": there are six (NOV3:16-21). (c) NOV3:27 "several nodes in two tiers, two
    proposers" against PLAN:1407 (1) "on T0". (d) PLAN:1413 "since the 18-19 Oct sweep ... has grown (PACE, SAGE,
    SGM ...)": PACE is in the 9 Oct sweep (`NOVELTY_SWEEP_20261009.md:54`), SAGE in part 2; SGM is arXiv 2510.
    **Fix:** correct the four statements.
18. **Verification level of external claims is unclear.** "Opened" means read through a summarising reader (NOV3:5).
    NOV3:13-15 give exact figures, and the links of :13-14 are conference listing pages, so abstract or full text is
    not stated; the caveat of `NOVELTY_FULLTEXT_20261019.md:16` (check against the PDF before quoting) is absent and
    NOV3:32 lists only Snippet rows. PLAN:1413 and `C3_DESIGN.md:193` state these papers' content as fact. For
    Calibration Is Not Control, "trains its supervision target on intervention utility" (PLAN:1413; NOV3:30) has no
    table row in NOV3, and the earlier entry (`NOVELTY_SWEEP_20261009.md:83-87`) describes only a random-forest
    witness. **Fix:** split "Opened" into listing or abstract and full text; add the caveat; add a row for this paper.

## NOTE

19. PLAN:1403: the adopted "chat-session review of 22 Nov 2026" is not in the repo, so the rows cannot be compared
    with what was recommended. Commit it under `proposals/` and cite it (no quotation of the author is needed).
20. PLAN:1411: "bundled into one author row per day" does not say who judges "no trade-off" or that work waits for
    the row (RB:34). "One STATUS line": STATUS has no entry after 15 Nov (STATUS.md:3 says 16 Nov), and CUR §3 now
    carries state although RB:3 sends progress only to STATUS.
21. PLAN:1413: the four-week rerun rule is PLAN:305 (§9 item 8), not RUNBOOK E.2. RB:10: "R1-TRACKS-STOP4" is not a
    row id (R1-TRACKS-STOP4-END, -CONSEQUENCES). NOV3:36: `paperC/docs/PLAN_ADDENDUM_20261119.md` is on branch
    `paperc-plan-amend-20261119`, not on main.
22. CUR:27 drops the qualifiers "mean two-arm" and "μ ≥ 1" that PRE-POWER A keeps (PREREG:205; PLAN:1407 has the first).
23. PLAN:1413 "'RL' is not used for anything": word or method? RB:345 (P.5) includes a GRPO check for A6; if such
    a variant is reported, its estimator has to be named.
24. Checked and consistent: R1-SUBMISSION-MIN (3) with PRE-WDBC B and PRE-T1 A; power 0.36 and 0.26; K, seeds,
    305 and 138 GPU-h, 15 and 11 Dec with R1-G5-DECISIONS; the eight T1 nodes with the split file; host roles with
    R1-T1-HOST-TASL; 288 campaigns and 5,760 trials with `reports/sweep2_20261116/SWEEP2_REPORT_20261121.md:48`;
    the R1-BX-D6, D7, D9, D11, D12, D13 citations; the quoted C3_DESIGN sentence. The commit changes only `docs/`,
    sits on an `author-*` branch (BRANCHES.md:7), is in English and labels AI assistance. `analysis_guard` returns
    the same confirmation commit (`31dab9ef`) for PLAN before and after the commit.

## Not checked

- The external papers and the ICML 2027 dates (no web access was used).
- That the author adopted each row as written (finding 19).
- G.5 draft revision 7 (`mac-g5-tasl-20261122`, not on main): 305, 138, 15 Dec and 11 Dec were traced to the
  R1-G5-DECISIONS row only.
- Host state (whether the sweep-2 audit, G.1b or G.4 are running) and the content of `mac-manuscript-20261122`.
- No test suite was run; the gate and fold behaviour cited in findings 1 and 14 was read from code, not executed.
