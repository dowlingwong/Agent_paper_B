**AI-assisted independent re-review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
Scope: revision 4 of **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, branch
`mac-d3-design-20261126` @ `7e9dad50`, checked against revision 3 @ `45ebf156` (reviewed in
`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R3_20261126.md`) and revision 2 @ `dedba911`. Authority is unchanged:
**PD** = `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch
`mac-d3-predecl-20261122` @ `a24a55bf`, §§2, 4, 7 and 12 (and §§8–11 for interfaces); **PLAN** =
`docs/r1/PLAN.md` at `7e9dad50`, `R1-D3-OUTCOMES2` (PLAN:1562), `R1-D3-ORDER` (PLAN:1564),
`R1-SWEEP2-MEASURED-GPU` (PLAN:1302), `cacheprompt` (PLAN:724); **S** = `r1/c3/d3_analysis.py` at
`a24a55bf`. Diff `45ebf156..7e9dad50`: one file, 34 insertions, 24 deletions (the whole document is 202
lines). I wrote no code, ran no job/audit/test, and opened no label, evaluation, split, sweep-table or
sealed file.

# D.3 G1/G6 design revision 4: re-review

**VERDICT: ACCEPT WITH CHANGES.** Revision 4 closes several R3 items, but it is **not** `ACCEPTED FOR
CODE`: five of the claimed R3 corrections are present only in the new/edited paragraph while the
authoritative older paragraph still says the opposite, and one new path contradiction was introduced
(final.json for campaigns reaching w=20). B3 and B4 are therefore still not fully closed. These are
text-only fixes; the design itself needs no further design decision.

## What revision 4 fixed (verified in the diff)

- R4:3 status says revision 4 (the body still has a stale "Revision 2 answers …" sentence — see minor).
- R4:14–16 §1 now says the H200 is **not** a prerequisite and launch binds the measured pool model
  (PLAN:1564); consistent with §2.1 and §4.
- R4:46–47 §2.2 now reports `ended_on` with the §3.3 enum and precedence instead of the old
  `runs`/`llm_cap` labels.
- R4:55–57 §2.2 now counts verify as **r = 2 pairs, 2r = 4** charged runs.
- R4:68–70 removes the "multi-run action crosses a w boundary" sentence and states the hook charges one run
  at a time, no block charges, so exact w points are always recorded; R4:60–72 states the live hook and
  `final.json` at `w_final`.
- R4:84 §2.3 smoke now records walltimes **and** the compute projection (PD:120).
- R4:137–139 removes the duplicate Y(w) paragraph and keeps one MAJOR 3 statement.
- §3.3 now has the corrected G7 five-tuple (R4:159–160), cache key with c0 by `config_sha256`
  (R4:166–168), G6 compute reported against PD §11 with no invented allowance (R4:163–165), A0R/D.3b
  as PLAN rows for PD revision 4 (R4:169–171), the final/w=0 rule (R4:175–178), the final-at-actual-w
  audit description (R4:179–180), and the killed-chunk recovery-vs-STOP statement (R4:156–158).
- B1/B2 from revision 3 remain settled: STOP/error excluded from `Y_final` (R4:97–103), and the
  G1→G6→G7→pinned-S data path with Y(w) author-gated (R4:124–139).

## Remaining blockers

**R4-1 (B4a residual) — the stale verify count is still in §3.3.**
R4:148 still says "a verify's `2r` is **two separate charged runs**". R4:55–57 now correctly says
verify r = 2 → 2r = 4 charged runs, and PD:208–209 fixes 2r = 4. The two sentences contradict each
other; the old parenthetical must be deleted or changed to "2r separate charged runs (4 for r=2)".
A literal implementation of R4:148 would under-charge a verify by half and move the w snapshot points.

**R4-2 (B4b residual) — the hook's pin/pre-code condition was not added.**
R4:146–149 still asserts "the G1 hook executes inside that pinned harness/runner" without naming the
hook/action or commit, and without a pre-code check that the hook exists. `a3fedbbd` is on the
`cacheprompt-20261031` harness branch (PLAN:724, STATUS:138), not `r1`; the local harness checkout is
`897d83c8` and does not contain it. The design must either name the hook/action and the reviewed pin
that provides it, or state the pre-code check and that, if absent, a new reviewed pin named in the D.3a
note is required (PD:64). "If a controller or harness can only charge a block, code stops for an author
decision" covers the block case, not the missing-hook case.

**R4-3 (B3 residual) — §2.3 still lists killed/non-clean chunk among the STOPs.**
R4:79–80 still says the §10 STOP list applies including "killed/non-clean chunk", while R4:156–158 now
correctly says a killed/non-clean chunk is recovered whole in a new directory (recovery, not a STOP
class). Remove it from §2.3's STOP list and make §2.3 carry the recovery rule; §3.1:103's "stage-wide
STOP handling is in §2.3" also points at a definition that is only in §3.3.

**R4-4 (B3 residual) — §3.2 still has the four-tuple G7 row.**
R4:127–128 says G7 emits a row per **(stage, arm, node, instance)**, while R4:159–160 in §3.3 now says
per `(stage, arm, node, instance, repetition)`. The §8 schema and S require the campaign/repetition key
(`S:126–128`, `S:190–193`, `S:223–330`; optional rep 2 per PD:47, PD:526–527), so §3.2 must be fixed to
the five-tuple (or point to §3.3).

**R4-5 (B3 residual) — §3.1 still keys c0 by symbol.**
R4:106–107 still gives the cache keys as `(node, config_sha256, audit_seed)` and
`(node, c0, audit_seed)`, while R4:166–168 now correctly keys c0 by `config_sha256`. Fix the §3.1 line
so both places agree; an unresolvable c0 cache key would make the cross-arm/cross-w cache unverifiable.

**R4-6 (new) — `snapshots/final.json` is not written for campaigns that reach w=20.**
R4:71–72 says final.json is written "If a campaign ends before 20"; R4:179–180 says the final-at-actual-w
audit reads "`snapshots/final.json` (present for every normal campaign)". A campaign that spends all 20
runs is a normal campaign but has no final.json under R4:71–72. Either write final.json also at
`w_final = 20` (and keep the Y_final/Y(20) dedup of R4:175–178), or make the audit read
`snapshots/w20.json` for that case. The primary audit path cannot depend on a file that does not exist.

**Minor, same pass (not blockers but inconsistent):**
- R4:5 still says "Revision 2 answers the independent design review …" and R4:141 still heads §3.3
  "(revision 3)"; update both to revision 4.
- R4:76–78 preflight says "no test labels" only, while R4:153–158 says "no evaluation/T1 label read";
  use the §10 wording in both places.
- R4:46–47's `ended_on` enum includes `stop`/`error`, which are not §8 table values (S:193); make the
  runner-internal → G7/table mapping explicit (the §3.3 "not eligible" text is the right base).
- R4:177–178 says for `w_final=0` "an audit path is written only for w>0"; confirm G6 writes the
  canonical `Y_final=0` row at w=0 (or points to final.json) so G7 can emit it without an audit record.

## Evidence

`git show 7e9dad50:docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` (202 lines);
`git diff 45ebf156 7e9dad50` (one file, 34+/24−; hunks at §1, §2.2, the §2.3 smoke line, §3.1/§3.2/
§3.3 text, §4/§5 were unchanged in this pass); the same PD/S/PLAN files at `a24a55bf`/`7e9dad50` used in
rounds 1–3; harness facts from PLAN:724/1302 and the local harness checkout `897d83c8`.
No code, job, campaign, audit or test was run; no label, evaluation, split, sweep-table or sealed file
was opened. B1/B2 remain settled; B3/B4 have the five stale/contradictory lines above. One more targeted
text pass should close them; no other design work is needed.

VERDICT: ACCEPT WITH CHANGES
