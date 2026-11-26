**AI-assisted independent re-review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
Scope: revision 3 of **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, branch
`mac-d3-design-20261126` @ `45ebf156`, checked against revision 2 @ `dedba911` and revision 1 @ `e16235b3`.
Authority is the same as the round-1/round-2 reviews: **PD** =
`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch `mac-d3-predecl-20261122` @ `a24a55bf`,
§§2, 4, 7 and 12 (and §§8–11 where they fix interfaces); **PLAN** = `docs/r1/PLAN.md` at `45ebf156`,
`R1-D3-OUTCOMES2` (PLAN:1562), `R1-D3-ORDER` (PLAN:1564), `R1-SWEEP2-MEASURED-GPU` (PLAN:1302) and the
`cacheprompt` row (PLAN:724); **S** = `r1/c3/d3_analysis.py` at `a24a55bf`. The diff `dedba911..45ebf156`
is one file, 61 insertions, 22 deletions: §3.1 (STOP exclusion), §3.2 (data path), a new §3.3, §4 and §5.
I wrote no code, ran no job/audit/test, and opened no label, evaluation, split, sweep-table or sealed file.

# D.3 G1/G6 design revision 3: re-review

**VERDICT: ACCEPT WITH CHANGES.** Revision 3 settles **B1** and the structural part of **B2**, and the new
§3.3 is the right home for the fixed-settings/minor items. It is **not** `ACCEPTED FOR CODE` yet: **B3**
and **B4** are not fully settled — B3 because §1 and §2.3 still carry the superseded text that §3.3/§4
contradict, and B4 because §3.3 has one numeric error in the charged-run rule, §2.2 still has the
block-charge sentence, and the per-charged-run hook is not shown to exist at the pinned harness
`a3fedbbd`. These residuals are text-level (two are pre-code verification), so no further design work
is needed — one correction pass should close them.

## What revision 3 fixed (verified in the diff)

- **B1 — STOP/error campaigns excluded from `Y_final`.** R3:94–102 now says only *normal* early endings
  (all-skip A1 Y=0, LLM-cap end, `no_fundable_candidate`) contribute the final row; a STOP/error campaign
  does not contribute and is not in the outcome table, per PD §10 (`PD:458–461`, no outcome table from a
  partial design) and the pinned analysis (`S:276`, `S:193`). This is the right rule.
- **B2 — primary data path.** R3:121–128 now routes primary `Y_final` as **G1 → G6 → G7
  outcome-table builder → the pinned `d3_analysis.py`**, which reads the `r1_d3_outcome/v1` table as it
  does now; S is not changed to read `summary.json`/`Y_final.jsonl`; G7 (the reviewed unit, PD:509) emits
  the §8 row. That resolves the interface mismatch. R3:129–132 correctly states Y(w) is outside signed
  PD §7 and is not authorized as code until the author either amends PD §7/§8 (S re-pin) or declares a
  separate descriptive unit; the primary Y_final path is independent of that decision.
- **B3 — §4 and §5.** R3:174–180 now says the H200 is **not** a prerequisite (measured pool model,
  PLAN:1564), §7 contrasts are at `Y_final` (not w=20), and Y(w) is not part of §7.3; §5's questions are
  replaced with the right pre-code questions (R3:185–192).
- **B4 — snapshot rule, in substance.** R3:147–149 says the G1 hook runs inside the pinned harness/runner,
  `w += 1` per charged worker run, no block charge; if a controller/harness can only block-charge, code
  stops for an author decision. That is the correct condition; the residual is the exact wording and the
  pin check below.
- **§3.3 addresses the earlier minors:** fixed PD §2 settings (memory mode, proposal schema/temperature,
  server `cache_prompt:false`/thinking off, skip display, g, pins) R3:143–149; smoke records walltimes
  **and** the compute projection and sets 1.5× walltime, P10 re-run at launch R3:150–152; preflight/STOP
  additions incl. constants sha, arms-frozen constants, S sha/tests, stage note, fallback >1 %, no
  evaluation/T1 label, measured-GPU chunk time/P7 R3:153–157; audit no-label guard R3:158–159; G6
  4-w compute projection R3:160–161; cache provenance and missing-provenance STOP R3:162–163;
  A0R/D.3b-unconditional as author items R3:164–165; `ended_on` enum/precedence R3:166–168;
  `Y_final`/Y(20) dedup when `w_final=20` R3:169–170.

## Remaining blockers

**B3 residual — §1 and §2.3 still carry the superseded rules that §3.3 and §4 contradict.**
- R3:14–15 still says "the H200 is currently out of the pool, so launch waits for it or for an author row
  that changes the measured model", while R3:30–32 says launch uses the measured pool model and R3:174–176
  says the H200 is not a prerequisite. Delete the §1 sentence or align it with §2.1/§4.
- R3:81 still says smoke "outputs may set walltimes only", while R3:150–151 says walltimes **and** the
  compute projection (PD:120). §2.3 must be aligned (or say §3.3 supersedes it).
- R3:77 still lists "killed/non-clean chunk" in the §10 STOP list, while R3:156–157 and R3:37–38 give the
  whole-rerun recovery rule. Remove the killed-chunk item from the STOP list and make the STOP-class /
  recovery distinction explicit in §2.3; the stage-wide STOP handling that R3:100 refers to should be
  written in §2.3, not only in §3.3.
- R3:45–46 still reports `ended_on` as `runs`/`llm_cap`/`stop`/`error` while R3:166–168 defines the
  schema enum `worker_runs`/`llm_call_cap`/`no_fundable_candidate` plus the non-table `stop`/`error`.
  State the runner-internal → §8-table mapping and the precedence once, and make §2.2 reference §3.3.
- The document header (R3:3) still says "revision 2"; it should say revision 3 (the text also says
  "Revision 2 answers …"). Purely editorial, but this is the review record.

**B4a residual (charged-run rule numeric error).** R3:148 says "a verify's `2r` is two separate charged
runs". The pre-declaration fixes A1/A2 verify `r = 2`, each verify charged **2r = 4** runs (PD:208–209);
G8/accounting counts each of those worker runs. "Two separate charged runs" is wrong for r=2 and would
under-count a verify by half if implemented literally. Fix to "2r separate charged runs (4 for r=2)".
This is the B4 item that can change the W accounting and the snapshot points.

**B4b residual (block-charge sentence and the hook's pin).**
- R3:66–67 still says "If a multi-run action crosses a w boundary, the hook still records the exact w point
  after the crossing run"; R3:147–149 now says there is **no** block charge (`w += 1` per charged run) and
  a block-charging controller stops for an author decision. The two cannot both hold; delete the "crosses
  a w boundary" sentence or say the exact-w point exists only under the one-run-at-a-time rule.
- The hook is asserted to run "inside that pinned harness/runner" (R3:146–147), but the local harness
  checkout is at `897d83c8` and does not contain `a3fedbbd`; `a3fedbbd` is on the `cacheprompt-20261031`
  harness branch (PLAN:724, STATUS:138), not `r1`. The design should name the harness hook/action (or the
  runner wrapper) and the exact commit that provides it, or make it a pre-code check that, if absent,
  requires a new reviewed pin named in the D.3a note (PD:64) — not silently a §3.3 code stop.

## Smaller/remaining items (not blockers, but fix in the same pass)

- **G7 row granularity (B2 tail).** R3:124 says G7 emits one row per `(stage, arm, node, instance)`, but
  §8's schema keys a row per campaign, i.e. per `(stage, arm, node, instance, repetition)`
  (`S:126–128`, `S:190–193`, `S:223–330`); with the optional second repetition (`PD:47`, `PD:526–527`) the
  design's four-tuple would merge two campaigns. Write the five-tuple.
- **§3.3 "rows/arms" statement is inaccurate.** R3:164 says "revision-4 rows A0R and D.3b unconditional
  are marked PROPOSED in the PD". At `a24a55bf` they are not in the PD; they are the 26 Nov PLAN rows
  `R1-D3-DECOMP`/`R1-D3B-UNCONDITIONAL` (PLAN:1560–1561) that `R1-D3-ORDER` step (2) requires the PD
  revision 4 to absorb. Say so.
- **Cache key.** R3:103 still keys the start-configuration runs as `(node, c0, audit_seed)` while
  R3:162 gives the key as `(node, config_sha256, audit_seed)`; c0 must be identified by its config sha in
  both places (and §3.3's provenance = run-record sha is otherwise right).
- **G6 compute "allowance".** R3:160–161 says G6 "stays within the D.3 audit CPU allowance"; PD §11
  gives an estimate, not an allowance/STOP. Say what the budget/STOP is (or that it is a pre-launch
  author item) so the projection has a threshold.
- **Final-at-actual-w audit record path.** R3:109 gives `audit/.../w<w>/...` for `w = w_final`; the
  `snapshots/final.json` path (R3:68) is not mirrored in the audit tree (distinguish `final` from
  `w<w_final>` and define the `w=0`/no-audit case for the all-skip A1 campaign).
- Two Y(w) paragraphs remain in §3.2 (R3:121–132 and R3:134–139); merge them so the author-gate is
  stated once.
- `§3.3` says "all §10 items" but does not include the no-use-of-D.3-output STOP and the
  evaluation/T1 path refusal wording (it says no evaluation/T1 label read — good); make the §10 mapping
  explicit against the still-stale §2.3.
- The diff is silent on the earlier `PD:120` "compute projection" and `P10` — §3.3 now covers them, so
  those are resolved if §2.3 is reconciled (first B3 bullet).

## Evidence

`git show 45ebf156:docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` (192 lines);
`git diff dedba911 45ebf156` (one file, 61+/22−; hunks at §3.1, §3.2, §3.3, §4, §5 only — §2.3 and §1 are
unchanged from revision 2); the same PD/S/PLAN files at `a24a55bf`/`45ebf156` read in rounds 1–2; harness
facts from PLAN:724/1302 and the local harness checkout `897d83c8` (which does not contain `a3fedbbd`).
No code, job, campaign, audit or test was run; no label, evaluation, split, sweep-table or sealed file was
opened. B1 is settled; B2 is settled in structure with the G7-row tail; B3 and B4 need the text corrections
above before `ACCEPTED FOR CODE`.

VERDICT: ACCEPT WITH CHANGES
