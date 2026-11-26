**AI-assisted independent re-review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
Scope: revision 5b of **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`,
branch `mac-d3-design-20261126` @ `261c3bd1`, checked against revision 5 @ `a430e503` and the full R1–R5
review chain (`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_20261126.md` and the R2–R5 addenda). Authority is
the same throughout: **PD** = `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch
`mac-d3-predecl-20261122` @ `a24a55bf`, §§2, 4, 7 and 12 (and §§8–11 for interfaces); **S** =
`r1/c3/d3_analysis.py` at `a24a55bf`; **PLAN** = `docs/r1/PLAN.md` at `261c3bd1`, `R1-D3-OUTCOMES2`
(PLAN:1562), `R1-D3-ORDER` (PLAN:1564), `cacheprompt` (PLAN:724). Diff `a430e503..261c3bd1`: one file,
11 insertions, 9 deletions, four hunks (status header/body, §3.3 heading, §3.3 hook/verify paragraph). I
wrote no code, ran no job/audit/test, and opened no label, evaluation, split, sweep-table or sealed file.

# D.3 G1/G6 design revision 5b: final acceptance

**VERDICT: ACCEPTED FOR CODE.**

The two substantive R5 residuals and the version-text residual are now present in the committed file, and
the R1–R5 review chain is closed. The design may proceed to implementation; the implementation itself
remains subject to the standard tier-E unit reviews and the pre-code checks the design now names.

## Closure verified in the diff

- **R5-1 (verify charge), closed.** R5b:149–153 now says "Verify has r = 2 pairs, hence **`2r = 4`
  separate charged runs**, each charged singly." This agrees with R5b:54–56 and R5b:68–70 and with PD:208–209
  (r = 2 → 2r = 4); the stale "two separate charged runs" sentence is gone.
- **R5-2 (hook pin/pre-code), closed.** R5b:149–153 now names the hook as a **G1 runner-level charged-run
  hook implemented in the reviewed G1 code**, states it is not an existing harness action, requires harness
  pin `a3fedbbd…` (or a new reviewed harness pin named in the D.3a note if the pin cannot expose per-run
  charges), and requires a **pre-code cluster pin/API check before code** that the hook/action is present at
  that pin. The block-charge case stops for an author decision; no block charge is implemented. That is the
  condition R4/R5 asked for (PD:64 for the new-pin route).
- **R5-3 (version text), closed.** R5b:3 is "revision 5"; R5b:143 heads §3.3 "(revision 5)"; R5b:5–7 says
  "Revisions 2–5 answer … R2–R5 addenda (R1–R5: ACCEPT WITH CHANGES)". The R6 acceptance is this addendum;
  no further version edit is required before code.

## Prior blockers, re-confirmed settled

- **B1** — STOP/error campaigns are excluded from `Y_final` and the outcome table (R5b:98–105); only
  normal early endings (all-skip A1 Y=0, LLM-cap end, `no_fundable_candidate`) contribute. Matches PD §10
  (PD:458–461), PD §8 status (PD:399–407) and S (S:276, S:193).
- **B2** — primary `Y_final` routes G1 → G6 → G7 outcome-table builder → the unchanged pinned `d3_analysis.py`
  (R5b:126–131); G7 emits the five-tuple `(stage, arm, node, instance, repetition)` row (R5b:130, 164).
  Y(w) remains outside signed PD §7 and author-gated before any Y(w) code (R5b:132–139); the primary path
  is independent of that decision.
- **B3** — H200 is not a prerequisite (R5b:14–16, 184–186); smoke records walltimes **and** the compute
  projection and sets 1.5× walltime, P10 re-run at launch (R5b:83–84, 155–157); killed/non-clean chunk is
  recovery, not a STOP class, with stage-wide STOP coordination (R5b:79–84, 160–163); `final.json` exists for
  every normal campaign including w=20 (alias) and the w=0 canonical case (R5b:70–72, 183–187); G7 row,
  c0 cache key, and `ended_on` internal→table mapping are fixed (R5b:107–109, 164, 171–173, 175–179).
- **B4** — charged-run counter is G8/accounting (R5b:53–59), w increments by exactly 1 per charged run with
  no block charges and exact w points (R5b:60–70), and the hook/pre-code condition is now stated (R5b:149–153).

## Non-blocking implementation notes (no design change needed)

1. **G6 audit-job scheduling wording (R5b:116–119).** The G6 unit still says "separate HTCondor CPU chunks
   (deepthought direct, no GPU) … one per stage/arm/repetition, 16 workers"; "deepthought direct" vs
   "HTCondor CPU chunks" and the one-host/16-worker serialisation are an operator/unit detail, not a fixed
   value. Settle it as part of the G6 unit review, together with the seal point and single-writer cache
   protocol (the cache provenance is already fixed at R5b:169–173). This is not a design blocker.
2. **§3.2 refusal wording (R5b:129–131).** §3.2 still says S refuses "a test-label read"; S's actual
   `refuse_input_path` refuses label/evaluation/split/sweep-table/`r1_sealed` names (S:196–200, PD:410–419).
   The pinned S is unchanged and performs the broader refusal; the G6/G7 units should rely on it and the
   audit no-label guard (R5b:161–163) rather than narrow the statement. Non-blocking wording.
3. **The design text labels this revision 5** while the commit/review chain calls it 5b; this is editorial
   and does not affect content.

## Acceptance basis and limits

I checked the diff and the full current document at `261c3bd1` against PD §§2,4,7,12 (and the interfaces in
§§8–11), S at `a24a55bf`, and PLAN `R1-D3-OUTCOMES2`/`R1-D3-ORDER`/`cacheprompt`. This acceptance is for
the **design** only: no code, job, campaign, audit, test, label, evaluation, split, sweep-table or sealed
file was read or run, and the standard tier-E implementation reviews, the pre-code hook/pin check, the
stage-note preconditions, the PD revision 4/author items, and the Y(w) author gate all still apply before any
run. The fixed values checked in rounds 1–5 (seven T0 nodes/WDBC exclusion, W=20 every arm, cap 80 proposed,
all seed blocks, `campaign_id` = instance id, ledger roots, K=10 audit seeds/conditions, no resume, no
test/evaluation labels) remain correct in this revision.

VERDICT: ACCEPTED FOR CODE
