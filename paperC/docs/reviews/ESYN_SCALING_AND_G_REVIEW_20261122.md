# Independent review: settlement of addendum §G, and the E-SYN scaling and headroom study

**AI-assisted (Claude, independent reviewer, fresh session; wrote neither commit). 22 Nov 2026.**
- **Reviewed:** commits `465e1860` (plan record) and `abe14a5c` (study) on `paperc-esyn-scaling-20261122`, on top of `461ecae9`.
- **Method:** read both diffs, the two addenda, the plan, Paper B's PLAN, C3_DESIGN and C3 code, and `origin/main` at `52f4e3e5`. Ran `tests/test_esyn_scaling.py` (7 passed). The benchmark was not re-run. Three small checks of my own are described where they are used (B1, B9, B11).
- **Short names:** "add." = `paperC/docs/PLAN_ADDENDUM_20261119.md`; "report" = `ESYN_SCALING_HEADROOM_20261122.md`; "run" = `esyn_scaling.py`; "render" = `esyn_scaling_report.py`; "PLAN" = `docs/r1/PLAN.md`.

**VERDICT: REVISE** (2 MAJOR, 10 MINOR, 7 NOTE)
- The data file, the code and the tables are correct as far as I could check. Both MAJOR findings are sentences in the written reading (report §7) that say more than the data. Rewording fixes them; no rerun is needed.
- Commit `465e1860` taken alone would be ACCEPT WITH MINOR.

---

## Part A — commit `465e1860` (plan record)

**A1 (MINOR). G7: "Paper B's value" is a different number on tabular_mlp.** add.:38, :267, :278; PLAN:1219.
- The words trace: PLAN:442 (row "g (22 Oct)") and `docs/r1/C3_DESIGN.md:11` say g = 0.1 σ_node with 0.05 and 0.2 as sensitivity values.
- The unit does not. PLAN:442 defines σ_node as "the same σ that standardises the bins". In Paper B's code that is the median over *material* edits (`r1/c3/dataset.py:77`), which add. A.0 calls σ_d. Add. A.0's σ_node is Track S's unit (all five edits). On tabular_mlp σ_d = 1.87 σ_node (`HEADROOM_CENSUS_20261116.md:30`), so Paper B's sweep price there is 0.187 σ_node in the addendum's unit. On digits_mlp the two agree.
- G7 as written follows Track S (R1-TRACKS-S02 (i), PLAN:637), which is consistent with A.0 and A.2.
- Fix: one sentence at add.:38 and :267. "g is 0.1 of A.0's σ_node, as in Track S. Paper B's C3 sweep applies the same row in σ_d, which is 0.187 σ_node on tabular_mlp, inside the sensitivity range."

**A2 (MINOR). G7: g was settled without a written recommendation.** add.:247, :257, :267.
- §G gives a recommendation for h only; for g the default is "none". G.1's own rule (add.:257) keeps the default where there is no recommendation. The value of g follows from neither.
- The role of 0.05 and 0.2 in Paper C is not stated. Paper B judges its gate at 0.1 only.
- Fix: say at add.:267 where g's value was proposed (the 22 Nov chat, if so), and that A.2, A.4 and A.5 use g = 0.1, with 0.05 and 0.2 reported only.

**A3 (MINOR). Harness commit: the hash is right, the source is mislabelled.** add.:228; PLAN:1220.
- `origin/main:docs/r1/authorizations/c3_sweep2_20261119.md:59` names `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`. It is also the commit Track S ran on (`docs/r1/RUNBOOK.md:82`).
- That file is the authorization note, not the launch record. It speaks of "the launch record" as another document (its lines 76 and 107), and its 19 Nov draft (`61a3a625`) already named this commit. The launch record (`SWEEP2_LAUNCH_20261121.md`) is on `origin/ops-sweep2-launch-20261121`, not on `main`.
- What confirms the launched pin on `main`: `docs/r1/reports/s2_audit_20261121/precondition2/C3_sweep2_index_s2ev-20261119-a.json` (`harness_commit`) and `SWEEP2_REPORT_20261121.md:8-10`.
- Fix: call the file "the authorization note" in both places and cite the sweep-2 index as the record of the pin that ran.

**A4 (MINOR). G4 has no mark in the text and leaves two things unsaid.** add.:9, :57, :264.
- add.:9 says the four differing places are marked. The four marks belong to G7 (twice), G3 and G9. G4 has none.
- add.:57 still justifies the unadjusted gate with "the gate only decides whether RL is trained". Under G4 the gate also picks Q3's nodes, and with one passing node the Holm halving is gone. This stays valid because the gate reads SPT-1 data and Q3 reads fresh blocks, but the text should say so.
- G.1 does not say what Q3 reports on the node that did not pass.
- Fix: a "[settled 22 Nov, G4]" mark at add.:57 with both sentences ("not testable at this budget" on the other node, plan §6).
- The amendment of plan §11.2 is declared. I found no other conflict: plan §11.3 and R1-PAPERC-DELTA say "Holm across nodes".

**A5 (MINOR). G3: an ambiguous floor and an unstated consequence.** add.:124, :263.
- "each against the same floor": A.2 has two floors, 0.5 σ_d for the kept increment and 0.1 σ_d for decision regret (add.:84).
- Decision regret is C1's frozen node value (add.:85), so it is known today: digits_mlp 0.14 σ_d, tabular_mlp 0.02 σ_d (`HEADROOM_CENSUS_20261116.md:97-98`). Under G3, digits_mlp passes the node screen now, before measurement (b). Only tabular_mlp still depends on it.
- Fix: write both floors out, and add that sentence to G.1 row G3.

**A6 (MINOR). PLAN row R1-PAPERC-ESYN-SCALING.** PLAN:1215, :1221.
- The row is in the "(author)" table, whose introduction covers only the request to settle §G. The report calls itself "not an author decision".
- It states that the study's reading "is an input to R1-PAPERC-CORE". Given B1 and B2, the reading should not bind in its present wording.
- The row is added one commit before the report it cites.
- Fix: mark the row [记录者], word it "may be read as input after review", and let it bind only after B1 and B2 are fixed.

**A7 (NOTE). G9 edge case.** add.:52, :170. If one node is "not assessed" and the other fails, A.1 item 5 still prints "not testable at this budget". Say whether that is intended.

**A8 (NOTE). Checked and found correct.** The nine "default" rows of G.1 repeat the defaults at add.:241-253. G9 and h follow written recommendations. The "consequences" list matches the "decide before" column. PLAN:1219 says the same as G.1. Nothing conflicts with addendum 15 Nov (g = 0.1 σ_node, its line 78). `paperC/README.md:3` still reads "Status (19 Nov 2026)".

---

## Part B — commit `abe14a5c` (study)

**B1 (MAJOR). "This world cannot show a learner beating simple rules, whatever the data size."** report:123; render:130-134.
- The same paragraph says the room is about twice the half-width of a paired comparison. A policy that takes the room is then resolved.
- My check (2 s of simulation, same world and test roots): DP − best static = 8.5 × 10⁻⁵, 95% interval 4.7 to 12.4. On the report's own test block a policy does read above the static rule.
- Test roots are unrecorded (instances from 7,000,000), so the registry does not limit the test block. It can be made larger.
- "Whatever the data size" was not tested. R0 is still rising (B2).
- What the data support: the room is small (8.2% of the gap, 0.013 σ). A learner must take about half of it to be resolved on 6,000 test roots. None did up to 8,192 training roots.
- Fix: reword the heading that way, delete "whatever the data size", and add the DP − static interval to §3. Reword point 5's last bullet (report:131), which rests on this point.

**B2 (MAJOR). "P8's result is not an effect of the training size."** report:115-119; render:106-126.
- **R0.** The bullet itself says R0 depends strongly on the data. "The curve flattens: the last doubling adds 1.7 points" compares two nested draw-0 points. At 4,096 roots the two draws read 68.5% and 80.5% (report:57), and −19.9 against −7.0 [−13.0, −1.0] × 10⁻⁵ relative to the static rule. There is one draw at 8,192. Flattening is not shown. The report applies this caution to R1 ("single-draw differences of that size are not signal") but not to R0.
- **R1.** "In draw 0 it stays below the static rule at every size" is true and leaves out the other draws. Of the six training sets that pass the gate, R1 is below the static rule with an interval clear of zero in four. In the other two it reads +1.7 [−1.1, +4.5] (draw 1, 4,096 roots) and +1.6 [−2.0, +5.2] (draw 2, 2,048 roots), both with the added wider setting. P8's "R1 below static" therefore changes with draw and setting, though not with size.
- **"0 of 45 intervals above zero"** (report:119) is correct. The other half belongs beside it: the interval is below zero in 15 of 15 sets for R0, 13 of 15 for R1 and 2 of 15 for N6.
- Fix: heading "Up to 8,192 roots no learner is shown above the static rule. R0 is still limited by data; R1 and N6 are not." Add the draw-1 and draw-2 numbers to the R0 and R1 bullets and drop "flattens".

**B3 (MINOR). `margin` is in the wrong group.** run:71; report:88, :99.
- `BudgetMargin` keeps iff m̂ > h0 + c × runs used / W (`policies.py:363-377`). It reads the budget, which is the report's own definition of the second group.
- Effect: only the keep_feedback cell "best one-step rule". Without margin it is shrink at −9.2%, not margin at 84.8%: no one-step rule beats N1 there. "Left" and the last column do not change.
- shrink and rawkeep are belief-refit reference rows that keep on the raw increment (`LADDER_TABLE_20261116.md:38-39`). They are the best one-step row in three worlds, so "decided on its own forecast" is loose. The other rows are grouped as the code defines them.
- Fix in render, since run must stay unchanged: regroup margin at render time or footnote the keep_feedback cell, and name shrink and rawkeep as belief-refit references.

**B4 (MINOR). Point 5, first bullet, reaches beyond E-SYN.** report:128.
- It rests on N4 reaching the DP in the budget world. N4's recursion is exact there by construction (`LADDER_TABLE_20261116.md:257`; `BUILD_RUNBOOK.md:224` uses it as a build check). On a real node N4's law can be wrong. Fix: "In E-SYN's budget worlds, where N4's model is the true one, …; real nodes are not covered."

**B5 (MINOR). The "best static rule" is not a tuned rule.** run:306, :325; report:21, :130.
- It is the exact optimum over thresholds, computed from the true law, with keep iff m̂ > 0. A static rule tuned on dev campaigns can only equal it or be worse. Every "vs static" number is against this upper bound, as in P8. Point 5's third bullet names the dev-tuned rule instead. Fix: one sentence in §3.

**B6 (MINOR). The report can be overwritten without notice, and one post-hoc change is missing from it.** run:620; render:5-9; `paperC/README.md:118`.
- Verified: the stored `code_sha256` equals the hash of the committed run and its sources; both stored table hashes match; `render.markdown` reproduces the committed report byte for byte. The report states the two-module arrangement accurately (report:3, :82).
- `python -m paperc.esyn_scaling --report-only`, or any rerun, writes the first rendering over the report: no §7, and "not resolved" for the budget world. No test catches that.
- Only render's docstring says that §6's last-column rule was changed after the first rendering.
- Fix: a test asserting `REPORT.read_text() == render.markdown(result)`; a warning line in the README; one sentence under §6's reading rules.

**B7 (NOTE). The Limits paragraph (report:133) should add three things.**
- Draws 1 and 2 also share data across sizes: draw 1 is nested, and draw 2 at n lies inside draw 1 at 2n. Draws are independent within one size only.
- All 45 results use one dev block and one test block, the ones P8 used. They share test-block noise (the block reads the DP at 95.1%, about one s.e. low), so "0 of 45" is not 45 independent results.
- The added settings were chosen after P8's test result on this block was known.

**B8 (NOTE). Headroom: the best row of each group is chosen by its test value** (run:273), on the block that also gives its share and "left". This lowers "left" slightly, which is conservative for "yes" and not for "none shown". The margins in budget and keep_feedback are wide; no verdict changes.

**B9 (NOTE). Reproduction of P8 (report:72-80).** The explanation is worded as a possibility, which is right. My check narrows it. With the same three library versions, P8's own unchunked collection of the 4,096 roots and fits in the main process give exactly this run's N6 and R1 policy ids, not P8's. Chunked and unchunked data agree bitwise (observations, arrays, fork indices, fork labels). P8's stored code hash equals the current sources. So chunking, ordering, the forked R1 child and a code change are excluded. The library versions or the hardware of the P8 run remain; the report could name both.

**B10 (NOTE). Leakage and design: no defect found.**
- Training roots are disjoint from support, dev and test roots in every draw (run:99-108, tested).
- Selection reads `dev_gain` only (run:186-190). Test values of all candidates are computed before selection (run:176) and stored; neither module uses them for selection or for text.
- The P8-grid selection is `rows[:3]`. It differs from P8 in one declared way: P8 drops candidates that fail the support check before selecting. Where the selected policy passes the check (every set from 2,048 roots) both rules select the same setting.
- P8's N6 fork-label coverage check (`learners.py:293-306`) is not recorded.

**B11 (NOTE). Statistics and spot checks.**
- `lv._paired` gives a Student interval over test roots of the per-root mean over three fit seeds. The share and its interval are that gain divided by the exact gap. "vs static" is the same interval on the difference to the static rule. Report §2 and §3 describe this accurately, including the 87.1% reading and what the intervals do not cover.
- Headroom rows budget, keep_feedback and information, recomputed by hand from the two JSON files: every column and verdict matches. `verdict` and the thresholds work as §6 describes.
- Every number in §7 points 1, 2 and 4 matches `scaling_v1.json`.

---

## Not checked

- The chat of 22 Nov: the author's request, and whether g = 0.1 σ_node was recommended there. The private decision memo.
- Whether the study's design was fixed before the run. Both arrive in one commit, and the run can resume from a cache.
- The 45 stored cells themselves: no rerun. Only the selected 4,096-root draw-0 fits were refitted (B9).
- The content of the sweep-2 launch record on the ops branch beyond finding that it does not name the harness commit.
