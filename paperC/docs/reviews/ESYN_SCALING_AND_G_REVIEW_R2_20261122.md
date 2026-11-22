# Independent review, round 2: settlement of addendum §G, and the E-SYN scaling and headroom study

**AI-assisted (Claude, the independent reviewer of round 1; wrote none of the commits). 22 Nov 2026.**
- **Reviewed:** commit `0c713e81` on `paperc-esyn-scaling-20261122`, against round 1 at `abe14a5c` (`git diff abe14a5c 0c713e81`).
- **Method:** read the diff; recomputed every count and number of report §7 and the §6 table from `scaling_v1.json` and the two stored tables; ran `tests/test_esyn_scaling.py` (8 passed); re-read the cited files. The benchmark was not re-run.
- **Short names** as in round 1: "add.", "report", "run", "render", "PLAN".

**VERDICT: ACCEPT WITH MINOR** (0 MAJOR, 2 MINOR, 6 NOTE)
- All twelve graded findings of round 1 are resolved. The corrections introduced one new MINOR (N1).
- N2 is a MINOR that was already in `abe14a5c`. I missed it in round 1; it is not a fault of the corrections.
- The recorder may fix both after acceptance. Neither needs a rerun.

---

## Round-1 findings

| Finding | Status | What I checked |
|---|---|---|
| B1 (MAJOR) "cannot show … whatever the data size" | resolved | report:125. The heading now says little room, none taken. DP − static on the test roots is 8.5 [4.7, 12.3] × 10⁻⁵, which I recomputed (8.517, 4.688, 12.347). Round 1 wrote 12.4; that was my rounding slip, and 12.3 is right. |
| B2 (MAJOR) "not an effect of the training size" | resolved | report:117-121. Counts recomputed: above zero 0, 0, 0; below zero 15, 13, 2 of 15 for R0, R1, N6. R0 at 4,096 roots: 68.5% and 80.5%. Six sets pass the gate; R1 is not separable in two, with the values printed. Added settings selected in 1 and 6 of 15. "Flattens" is gone. |
| A1 (MINOR) G7 unit | resolved | add.:38, :268; PLAN:1219. Track S's unit is stated, with Paper B's 0.187 σ_node on tabular_mlp. |
| A2 (MINOR) G7 source of g | resolved | add.:258, :268; PLAN:1219. g is named as the recorder's proposal and flagged for the author. The role of 0.05 and 0.2 is stated. |
| A3 (MINOR) harness source | resolved | add.:229; PLAN:1220. The file is called the authorization note, and the sweep-2 index is cited. Both are on `origin/main` and carry the hash. |
| A4 (MINOR) G4 mark | resolved | add.:9, :58, :265. The mark is in A.1 item 7 and gives the validity argument and the report for the other node. |
| A5 (MINOR) G3 floors | resolved | add.:125, :264; PLAN:1219. Both floors are written out, with the consequence for digits_mlp (0.14 σ_d) and tabular_mlp (0.02 σ_d), as in the census table. |
| A6 (MINOR) PLAN row for the study | resolved | PLAN:1222. It is now a recorder's note under the table, marked "非作者决定". No other file refers to the old row id. |
| B3 (MINOR) `margin` grouping | resolved | render:28-39; report:88-91, :101. keep_feedback reads "shrink: −9.2%". Gap and "left" equal the stored values in all seven worlds. The swap restores the run's constants (tested). The sources-hash check raises if a table changed. One wording remainder: N5. |
| B4 (MINOR) point 5 beyond E-SYN | resolved | report:130 is limited to E-SYN's two budget worlds. Its new second sentence is N1. |
| B5 (MINOR) static rule not tuned | resolved | report:115, :132. |
| B6 (MINOR) report overwrite | resolved | The new test asserts that the committed report is render's output; the README line and report:91 state the post-run changes. The stored code hash still matches; run and data are unchanged. |

Round-1 notes A7, A8 and B7 to B11 needed no action. What remains of them is in N3 and N4.

---

## New findings

**N1 (MINOR, introduced by the correction). "Whether budget pacing leaves room on real nodes is what SPT-1 measures."** report:130; render:197-198.
- SPT-1 gives pilot variances, binding shares and the go/no-go statistics (plan §6). The addendum says that a passed go/no-go is not reported as evidence of headroom (add.:59, settled as G11), and that a no-go is likely even where a real channel exists (add. A.1, "Expected consequence").
- Fix: "Whether budget pacing leaves room on real nodes is a question for real-node data; E-SYN does not answer it."

**N2 (MINOR, already in `abe14a5c`; missed in round 1). "Room for a learner: yes" says more than the three worlds show.** report:93, :98, :100, :102, :108, :127, :131.
- **interaction.** The oracle member is privileged: it knows the true interaction matrix. `ESYN_ORACLE_TABLE_20261116.md:71-74` calls it "an upper reference rather than a learnable target". The reading rule "elsewhere 'left' is a lower bound on the true room" (report:108) does not hold there.
- **shared_error and eval_allocation.** The oracle member is itself a fixed hand-parameterised rule of the `evalloc` family. The P4 ladder rows have no re-audit action (`LADDER_TABLE_20261116.md:268`). "Left" there measures the value of that action. It does not show room for a learned policy above a hand-built rule that has the action.
- So report:93 ("the room a learned policy could win over rules written by hand") and point 5's second bullet ("a world where §6 shows room") are stronger than the table.
- Fix in render:
  - head the last column "Room above the P4 ladder rows";
  - mark the interaction row as measured against a privileged reference, and exclude it from the lower-bound rule;
  - add to point 4 and to point 5's second bullet that a dev-tuned member of the `evalloc` family must be a comparator, and that §6 does not show room above it.

**N3 (NOTE). G4 meets G9.** add.:58, :171. "A node where the go/no-go did not pass" also covers a node that G9 reports as "not assessed". Say which label Q3 gets there.

**N4 (NOTE). Limits paragraph** (report:135). Two round-1 points are still absent: draws 1 and 2 share data across sizes; all 45 results share one dev block and one test block, the ones P8 used.

**N5 (NOTE). One-step rows.** report:88. shrink and rawkeep keep on the raw increment and are belief-refit references, so "decided on its own forecast" is loose. shrink is now the keep_feedback entry.

**N6 (NOTE). The DP − static number is not in the data file.** render:42-47 simulates it at render time (about 2 s, deterministic). §7's heading says the reading is "for `scaling_v1.json`". Add "(computed by the report module)" at report:125.

**N7 (NOTE). "Settled" and "for the author to confirm".** add.:9 and PLAN:1219 say all thirteen points are settled; add.:258 and PLAN:1219 flag g for the author. Both hold if merging the branch is the confirmation. One clause would say so.

**N8 (NOTE). Checked and found correct.**
- Report §7: every number and count matches `scaling_v1.json`. No sentence in points 1 to 3 goes beyond the 15 training sets of this world; "what this does not show" is stated. Point 2's sizes hold for this world and logging mixture, which the section's scope implies.
- Addendum: the G3, G4 and G7 texts agree with A.2, plan §6 and §11.2, PLAN:442 and `r1/c3/dataset.py:77`. G.1 and the PLAN row say the same.

---

## Not checked

The 22 Nov chat (the author's request; whether the author has seen the flag on g) and the private memo. The 45 stored cells: no rerun, as in round 1.
