# Independent review of the B1 STOP diagnosis report (mac-b1-diag-report-20261111), 11 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not write the unit). Status: rounds 1–2 changes requested; round 3 **accepted** at `b92fe6f5`. Rounds copied verbatim below.

---

## Round 1

# Review — B1 STOP diagnosis report unit (round 1)

Unit: `/tmp/pb/wt/diagrep`, branch `mac-b1-diag-report-20261111`, `7b08c2ad..75c05787` (6c2a857f analysis N1 checks + hand-off filename; 75c05787 report). Reviewer: independent, freshly spawned; read-only; scratch in `/tmp/pb/scratch_rev_diagrep/`. Line numbers refer to `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md` at 75c05787 unless stated.

## What I verified (no finding)

- **Capture.** `/tmp/pb/cap/ssh.log` SHA-256 `c6bc8a84…6df5` and `ssh.rc` `9a271f2a…86aa` equal the receipt on `mac/ops-b1-20261109` @ `d1d30687`. Run times (00:07:34–00:07:40 UTC), the pinned state SHA `cfe74faf…5794` (pinned flag true) and `stop_changed: false` are as §2 says.
- **N1 checks (6c2a857f).** `_median`/`_summary` are line-for-line the diagnosis script's (`B1_STOP_DIAGNOSIS_20261109.py:168-185`). The D4 halves `(len+1)//2` and the budget split at `W//2` match `summarize` (lines 323-330). `SIGMA_JOINT` and `MEDIAN_SD_DELTA` equal `NOISE_FLOOR_COMMON_20261022.md` Table 1, and that file's SHA-256 is `9be292b7…c01d`. `DUP_REF_PINNED` equals `exam_b1_v2.json@68357d3d` `anchor_duplicate_reference`, and the source JSON's SHA-256 is `84200770…85dd`. The D7 check compares bounds, source and SHA exactly. N1's three items are covered, plus D8 and the budget split. The rules, thresholds, `verdicts()` and `tables()` are unchanged. The only other change is the docstring.
- **Refusal tests are genuine.** With the analysis script at 7b08c2ad dropped into a copy of HEAD, all 7 new cases fail (7 failed, 26 passed). At HEAD the three named test files pass (56 passed).
- **Script identity.** The analysis script at 6c2a857f and at HEAD both have SHA-256 `c97b8e77…aafe`, as §2 says.
- **Numbers.** I re-ran the analysis on the capture (exit 0). Every number in the §1 and §3 tables matches its output: D1 point/lower/upper; node mean z +0.221/+0.181/+0.158/all +0.187; pairs ahead 2/4, 4/4, 3/4, 9/12; all D2 counts; D3 including D8; D4; D7 120/242 = 0.49586776859504134 inside the unrounded interval. I also recomputed independently from `rows`, getting the D1 point, node z, the counts, D7, termination/worker runs (all `worker_cap`, 20), D0 = 0, and the H2 pooled drop of 0.756 for `random_valid`. Running the diagnosis script's own `summarize()` on the capture rows reproduces the whole `summary` block, bootstrap bounds included, to 1e-12. Count ratios 1.56/1.18/1.41 are correct.
- **Class and consequence.** H4 NOT SUPPORTED → H1 NOT SUPPORTED, H2 SUPPORTED → class D. `r4_applicable_under_A1` is false. This matches PLAN row `R1-EXAM-B1-ANCHOR-R4` ("A class-D verdict resting on H2 alone … goes to the author") and restart hand-off §0.1/§0 "Not covered" on `/tmp/pb/wt/r4` (HEAD `4ddc820e`). So "not armed" is correct.
- **Other checks.** The recommendation and the paste-ready line are labelled ("Recommendation:", "Paste-ready (if the author agrees)") and record no decision as made. Per-proposal `delta_audit`: none in the report. Per-instance values are not listed either; there are only node/anchor aggregates and counts. No capture file is committed. The hand-off diff changes only the review filename. Both commits are by Dowling Wong <wangdowling@gmail.com>. There are no deletions and the worktree is clean.

## Findings

1. **Blocking — line 117, line 121, line 123: the R4 argument for an H2-only D leaves out the main counter-consideration.**
   - What the report says: "Plan §4's reason for R4 … holds whether the D comes from H1 or H2". The recommendation and paste-ready line then ask the author to widen A1 to "class D (H1 or H2)".
   - What it leaves out:
     - H2 is the hypothesis that the *mean incumbent-relative audited increment is not monotone in proposer quality*.
     - Under R4 the frozen B1 rule carries the ranking. That rule ranks on exactly this quantity: `r1/exam/rules/x5_rule_v2.yaml:4`, `ranking_quantity: pooled_audited_mean_proposal_increment`.
     - The PLAN row excludes "a class-D verdict resting on H2 alone (a metric or orientation problem)" on purpose.
   - Why it matters: an H2-supported diagnosis questions the very metric R4 would rely on. R3 is plan §4's route that changes the criterion to a campaign-level outcome.
   - Fix: state this tension in the R4 bullet and in the recommendation. Say that A1 left out H2 explicitly and that H2 bears on the ranking quantity of `x5_rule_v2`. Then either keep R4 with a reason why the within-root increment drop does not bias candidate ranking, or present R3 (or the tension) on an equal footing. Keep the paste-ready line in step with whatever the text says.

2. **Should-fix — line 117 ("only the PLAN row's condition and the restart hand-off's precondition would need a reviewed one-line widening") and line 121 ("restart hand-off unchanged otherwise"): this understates the change.** On `mac-b1-r4-20261109` the "H1 supported" condition also appears in:
   - restart hand-off §0 line 13: "Not covered … class D resting on H2 alone";
   - `docs/r1/RUNBOOK.md:152`, the X.3 amendment: "i.e. H1 supported";
   - `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md:3`. The draft's condition and rationale ("the two random anchors cannot be ordered") would be contradicted by this diagnosis, where H1 is not supported, so the disclosure text itself needs rewriting, not just its condition.

   Fix: list these places and drop "one-line" / "unchanged otherwise".

3. **Should-fix — line 100: the H2 mechanism claim goes beyond the data.**
   - "This is the mechanism the plan describes" asserts a cause; the data are only *consistent with* it.
   - The supporting number, "in-run gain", is the final kept record minus the first valid trial over the whole run (line 57). It is not evidence that the incumbent rose *early*.
   - On the raw scale `random_valid`'s in-run gain on ionosphere (+0.0747) is as large as on digits_mlp (+0.0724), yet ionosphere shows no drop. Only in σ_joint units are the in-run gains ordered like the drops.
   - Fix: write "consistent with the plan's H2 mechanism". Drop "early" or replace it with something D4 actually shows (the budget-index split). If in-run gain is cited, cite it in σ units.

4. **Should-fix — line 100: "Scripted's own drop is below the threshold".** Scripted's pooled standardised change from the first to the second half is −0.030 σ_joint: its second half is slightly *higher*, so there is no drop. Fix: "scripted shows no pooled drop (−0.03 σ_joint)".

5. **Should-fix — line 98: the H1 reading overreaches.**
   - "The two random anchors are ordered in the expected direction on every node" rests on positive node-mean point estimates only. On digits_mlp only 2 of 4 pairs are positive, and they carry the largest magnitudes in both signs (line 99).
   - The D1 interval includes 0, which is exactly why the gate STOPped ("cannot be shown"). Saying the anchors "are ordered" reads as the opposite of the recorded STOP.
   - Fix: say that the H1 pattern of plan §2 ("point estimate near 0 or negative, consistently across nodes") is absent: the point is +0.0046 and the node means are positive on all three nodes. Also say that the ordering is still not shown at the gate's level (lower −0.0006).

6. **Should-fix — line 115, line 118, line 101: the §6 options do not map one-to-one onto plan §4.**
   - Plan §4's options for D are R4, R1, R2 and R3. The report drops the name R1, presents "P (a)" in its place and adds P (b). Plan §4 assigns P (b) to "H3 without H1/H2", which is not this outcome.
   - Plan §4 says R1 is "only sensible if D3 shows a clear standardised gap that the raw scale hid". The report does not apply this condition. The D3 standardised gaps are about 0.19/0.19/0.15, and the raw point is already positive.
   - Line 101's "under the plan's ordering D precedes P" cites an ordering the plan does not state. The plan *defines* P as "H3 without H1/H2", which is what excludes P here.
   - Fix: name R1 (= P (a)) with its plan condition. Mark P (b) as a P-route fix offered beyond plan §4's D options, or drop it. Reword line 101 to cite the P definition.

7. **Note — line 100: H2 rests on one anchor × node.** Without digits_mlp, `random_valid`'s pooled drop is about 0.036 σ_joint, far below 0.25. The report says "concentrated on digits_mlp", which is accurate. Saying explicitly that the H2 verdict depends on that single node (4 roots, the node with the smallest σ_joint) would help the author and the appendix.

8. **Note — line 97: "this closes class E" is stronger than the evidence.**
   - The capture's D0 is the three counters k≠4, None and mismatch, not the full plan D0 inventory.
   - The capture's own `limitations` field says "cooperative producer/path provenance".
   - Suggest: "no engineering defect shown by the pre-declared checks and the code checks (H4 not supported)".

9. **Note — §5 (lines 103-111).** `UNCLASSIFIED` is also a class plan §4 does not have. List it next to `REVIEW`. "(declared, not used tonight)" could be "(declared; not triggered by this capture)".

10. **Note — `B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py:236-242`.** The D4 recomputation takes each root's `proposals` in capture order. It relies on the diagnosis script having sorted them by `budget_index`. A one-line `_need(sorted-by-budget_index)` would make the half split self-checking. I confirmed the order holds for this capture, so this is not needed for acceptance.

VERDICT: changes requested

---

## Round 2

# Review — B1 STOP diagnosis report unit (round 2)

Unit: `/tmp/pb/wt/diagrep`, `7b08c2ad..d4a99fe5`. The new commits since round 1 are `db73a0d0` (analysis budget-order check) and `d4a99fe5` (report revision). Line numbers refer to `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md` at `d4a99fe5`.

## Re-checks

- **Code (`db73a0d0`).**
  - The only rule change is a strict budget-index order check per root, plus its refusal test.
  - The test is genuine: with the analysis script from `6c2a857f` dropped into a copy of HEAD, `proposals_out_of_order` fails (1 failed, 33 passed).
  - At HEAD the three test files pass (57 passed).
  - The script's SHA-256 is `fdbfbeb1…970a`, as §2 says.
  - I checked the capture SHA again and re-ran the analysis: exit 0, and the output is byte-identical to round 1's.
- **Hygiene.**
  - The hand-off has not changed since round 1.
  - No per-proposal `delta_audit` in the report, and no capture file committed.
  - All commits are by Dowling Wong <wangdowling@gmail.com>, with no deletions; the worktree is clean.

## Round-1 findings

1. **(blocking) Resolved in substance.** The tension now opens §6 (line 117). It is disclosed in the recommendation and in the R4 paste-ready line. The claim that the ranking quantity was "pre-specified before Stage A" is correct: `x5_rule_v1.yaml` already ranked on `pooled_audited_mean_proposal_increment` when it was frozen at `4b9c6566` (26 Oct), and Stage A completed on 4 Nov. One follow-on inconsistency remains; see new finding 11.
2. **Resolved.** R4 now lists the PLAN row, restart hand-off §0, RUNBOOK X.3 and the appendix draft (line 121).
3. **Resolved.** The H2 mechanism is now "consistent with … not established", with the in-run-gain and ionosphere counterpoint (line 100).
4. **Resolved.** Scripted is now +0.030 σ (second half higher). The sign convention is consistent with the −0.036 σ for `random_valid` without digits_mlp. I reproduced both from the rows.
5. **Resolved.** H1 is now limited to the point estimates, digits 2/4, and an interval that includes 0 (line 98).
6. **Resolved.**
   - R1–R4 are mapped to plan §4, and P (b) is marked as P-only (line 126).
   - The class paragraph cites "H3 without H1/H2".
   - R1's numbers match D3 and D1: −0.351/−0.172/−0.156; −0.157/+0.013/−0.009; +0.158 to +0.221.
7. **Resolved.**
8. **Resolved.**
9. **Resolved.**
10. **Resolved.**

## New findings

11. **Should-fix — lines 124, 128 and 132: R3's scope is described inconsistently, and R3 does not resolve the tension the report raises.**
    - Plan §4 defines R3 as a replacement for the *anchor-ordering gate*: "Use a campaign-level criterion (final incumbent audited improvement)". The R3 paste-ready line says the same: "作为锚点判据".
    - Line 128, however, treats R3 as "changing it [the ranking quantity]". Line 117 argues that H2, if real, questions the *B1 ranking* under `x5_rule_v2`.
    - Neither R3 nor R4 changes `x5_rule_v2`'s ranking quantity. That quantity is fixed by the author's approval R1-EXAM-RULE-X5V2, by SHA.
    - So "If the author regards H2 as real, R3 is the consistent choice" (line 128) and "It answers H2 directly" (line 124) overstate R3. It answers H2 for the anchor check only. A candidate ranking on a campaign-level quantity would be a separate change to `x5_rule_v2`, needing its own author decision and review, outside plan §4's options.
    - Fix: state R3's scope as the plan defines it. Say plainly that if H2 is regarded as real for the ranking, the remedy is to change the ranking quantity, a separate author decision on `x5_rule_v2` that R3 alone does not make. Reword line 128's "changing it now (R3)" to match. Adjust the R3 paste-ready line if the author is meant to be able to choose that option.

12. **Note — line 103 and line 111.**
    - Line 103's heading still reads "(declared, not used tonight)". "(declared; not triggered by this capture)" would be clearer.
    - Item 5 of §5 lists the A1 applicability rule as an addition "made by the analysis". It comes from the PLAN row; the analysis only implements it. Labelling it as such (as round 1's "Also declared" did) would be more accurate.

13. **Note — line 122.** The R1 conclusion is fine. Plan §4's condition is a gap that "the raw scale hid", and the more direct reason it is not met is that standardisation changes no sign: raw and standardised node differences are all positive, and the raw D1 point is already > 0. Optional.

VERDICT: changes requested

---

## Round 3

# Review — B1 STOP diagnosis report unit (round 3)

**Unit:** `/tmp/pb/wt/diagrep`, `7b08c2ad..b92fe6f5`. Since round 2 there is one new commit, `b92fe6f5`, which touches only the report.

## Checks

**What changed.** The word diff `d4a99fe5..b92fe6f5` touches only §5 (heading and item 5), the §6 R1 and R3 bullets, the recommendation, a new "Outside plan §4" paragraph, and the R3 paste-ready line. No table, number, class statement or other section changed.

**Code.** The analysis script is unchanged (SHA-256 `fdbfbeb1…970a`, as cited in §2). The three test files pass (57 passed).

**Hygiene.** No capture file is tracked, and the report holds no per-proposal `delta_audit`. All commits are by Dowling Wong <wangdowling@gmail.com>. There are no deletions in the unit, and the worktree is clean.

## Round-2 findings

**11. Resolved.**
- R3 (line 124) is now described as plan §4 defines it: it replaces only the anchor gate and leaves the candidate ranking unchanged.
- The recommendation (line 128) no longer calls R3 a ranking change. It counts R3's new criterion among the post-hoc gates and notes its code cost.
- "Outside plan §4" (line 130) states correctly that none of R1–R4 changes the ranking, and that addressing H2 in the ranking would mean changing `x5_rule_v2`. That is a separate author decision, approved by SHA under R1-EXAM-RULE-X5V2. The ranking quantity was already in `x5_rule_v1` at `4b9c6566` on 26 Oct, before Stage A completed on 4 Nov; I verified this in round 2.
- This paragraph is marked as outside the plan and is not recommended.
- The R3 paste-ready line now says `x5_rule_v2` stays unchanged.
- Both paste-ready lines are still conditional proposals, and the report records no author decision as made.

**12. Resolved.**
- The §5 heading now says items 1–3 were not triggered by this capture.
- Item 5 attributes the A1 applicability rule to the PLAN row and the class order to the analysis.

**13. Resolved.** The R1 bullet now adds that standardising changes no sign here. This holds: the raw node means (digits_mlp +0.0023, credit_approval positive, ionosphere positive) and the D1 point are all positive.

## New findings

None.

VERDICT: accepted
