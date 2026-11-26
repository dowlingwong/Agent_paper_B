**AI-assisted independent re-review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
Scope: revision 5 of **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, branch
`mac-d3-design-20261126` @ `a430e503`, checked against revision 4 @ `7e9dad50` (reviewed in
`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R4_20261126.md`). Authority is unchanged: **PD** =
`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch `mac-d3-predecl-20261122` @ `a24a55bf`,
§§2, 4, 7 and 12 (and §§8–11 for interfaces); **S** = `r1/c3/d3_analysis.py` at `a24a55bf`; **PLAN** =
`docs/r1/PLAN.md` at `a430e503`, `R1-D3-ORDER` (PLAN:1564) and `cacheprompt` (PLAN:724). Diff
`7e9dad50..a430e503`: one file, 21 insertions, 16 deletions; the document is 207 lines. I wrote no code,
ran no job/audit/test, and opened no label, evaluation, split, sweep-table or sealed file.

# D.3 G1/G6 design revision 5: re-review

**VERDICT: ACCEPT WITH CHANGES.** Revision 5 closes R4-3, R4-4, R4-5 and R4-6 and the preflight/`ended_on`
items, but the two substantive B4 residuals are **not** in the committed file: the stale verify count at
§3.3 and the hook-pin/pre-code condition are unchanged from revision 4. The versioning text also still
says revision 4. It is therefore not yet `ACCEPTED FOR CODE`; these are three targeted text edits.

## What revision 5 fixed (verified in the diff)

- **R4-6 (final.json for every normal campaign).** R5:71–72 now writes `snapshots/final.json` at the actual
  `w_final` for every normal campaign, including w=20 where it aliases the w=20 snapshot; R5:183–185 says the
  final-at-actual-w audit reads it for every normal campaign and states the w_final=0 canonical case. This
  closes the "final.json only if before 20" contradiction.
- **R4-3 (killed/non-clean chunk).** R5:79–84 removes it from the §2.3 §10 STOP list and adds the explicit
  recovery rule plus stage-wide STOP coordination (first STOP-class chunk stops new submissions; in-flight
  chunks finish and keep records). Correct against PD:452–453/458–461.
- **R4-4 (G7 row).** R5:130 now says G7 emits one row per `(stage, arm, node, instance, repetition)`;
  matches R5:162 and the §8/S campaign key (`S:126–128`, `S:190–193`, `S:223–330`).
- **R4-5 (c0 cache key).** R5:108–110 now keys both the incumbent and the start config by
  `config_sha256` (c0 "identified by its config_sha256, not by symbol"); matches R5:169–171.
- **Preflight label / `ended_on` mapping.** R5:76–78 says no test/evaluation/T1 label read (and the
  in-campaign §10 list now says the same); R5:175–179 gives the internal→§8-table `ended_on` mapping and
  excludes `stop`/`error` from table values; matches S:193.
- Prior R4 fixes remain: §1 H200 non-prerequisite, smoke walltimes+compute projection, §2.2 verify 2r=4,
  live per-charged-run hook/exact w, §3.2 data path/Y(w) gate, §3.3 G6 projection vs PD §11, A0R/D3b PLAN
  rows.

## Remaining blockers (both claimed fixed in the R5 message but absent from the commit)

**R5-1 (B4a residual) — the stale verify count is still in §3.3.**
R5:150–151 still says "the G1 hook executes inside that pinned harness/runner and increments `w` by exactly 1
per charged worker run (no block charge; a verify's `2r` is **two separate charged runs**)". This
contradicts R5:56 (`2r = 4` charged runs per verify) and R5:69 (a verify contributes `2r = 4` separate
charged runs) and PD:208–209 (r = 2 → 2r = 4). The diff has no hunk in this paragraph, so the R4-1 fix did
not reach the file. Replace it with "2r separate charged runs (4 for r=2)". A literal reading would
under-charge a verify by half and move the w-snapshot points.

**R5-2 (B4b residual) — the hook's pin/pre-code condition is still absent.**
R5:149–152 still asserts "the G1 hook executes inside that pinned harness/runner" without naming the
hook/action, without the pre-code cluster pin check, and without the "a3fedbbd or new reviewed pin"
condition beyond the existing FIXR3/EGATE sentence. `a3fedbbd` is on the `cacheprompt-20261031` harness
branch (PLAN:724), not `r1`, and the local harness checkout `897d83c8` does not contain it. The design must
state the pre-code check (hook/action present at the pinned harness; if absent, a new reviewed pin named in
the D.3a note per PD:64) or name the hook/action and commit. The block-charging STOP does not cover a
missing hook.

**R5-3 (minor, but claimed fixed) — version text still says revision 4.**
R5:3 status is "revision 4", not revision 5; R5:144 heads §3.3 "(revision 4)"; R5:5–7 still says
"Revision 2 answers … revisions 2–4 answer …". The R5 message says the headings/status were updated; they
were not (the only header hunk changed the body sentence at old lines 6–7). Update all three to revision 5 /
the R1–R5 review chain.

No other R4 item is open: R4-3/4/5/6 are closed, the `ended_on` mapping and preflight labels are closed, and
B1/B2 remain settled. If R5-1 and R5-2 are inserted and the version text is corrected, this review becomes
`ACCEPTED FOR CODE`; no design decision is missing.

## Evidence

`git show a430e503:docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` (207 lines);
`git diff 7e9dad50 a430e503` (one file, 21+/16−; nine hunks at header body, final.json, §2.3, §3.1 cache,
§3.2 row, §3.3 heading, `ended_on`, final audit). The claimed R4-1 (verify count) and R4-2 (hook/pin) edits
are not among the hunks: §3.3:150–151 is byte-identical to revision 4. The same PD/S/PLAN files at
`a24a55bf`/`a430e503` used in rounds 1–4; harness facts from PLAN:724 and the local harness checkout
`897d83c8`. No code, job, campaign, audit or test was run; no label, evaluation, split, sweep-table or sealed
file was opened.

VERDICT: ACCEPT WITH CHANGES
