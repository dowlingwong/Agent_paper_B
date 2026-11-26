**AI-assisted independent re-review (Claude, fresh reviewer session, 26 Nov 2026). Tier E; design only.**
Scope: revision 2 of **D** = `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, branch
`mac-d3-design-20261126` @ `dedba911`, checked against revision 1 @ `e16235b3` and against the same authority
as the round-1 review: **PD** = `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, branch
`mac-d3-predecl-20261122` @ `a24a55bf`, §§2, 4, 7 and 12 (and §§8–11 where they fix the interfaces);
**PLAN** = `docs/r1/PLAN.md` at `dedba911`, `R1-D3-OUTCOMES2` (PLAN:1562) and `R1-D3-ORDER` (PLAN:1564);
**S** = `r1/c3/d3_analysis.py`, **A** = `r1/c3/audit.py` at `a24a55bf`. The diff is one file:
57 insertions, 22 deletions, 8 hunks (`git diff --unified=0 e16235b3 dedba911`). I wrote no code, ran no
job/audit/test, and opened no label, evaluation, split, sweep-table or sealed file.

# D.3 G1/G6 design revision 2: re-review

**VERDICT: ACCEPT WITH CHANGES.** Revision 2 fixes the core of MAJOR 1 and MAJOR 2 in the primary-outcome
and snapshot text, and correctly states the MAJOR 3 scope (Y(w) is outside signed PD §7). It is **not**
`ACCEPTED FOR CODE`: B1–B3 remain blockers and B4 is a pre-code condition. Also, the commit message says
it addresses "preflight/record/audit-no-label/smoke/P7 notes", but the diff does not touch §2.3, §4 or §5,
so those minors are still open (list below). The progress is real; the remaining changes are text-sized,
except the Y(w) unit decision of B2.

## What revision 2 fixed (verified in the diff)

- **MAJOR 1, core.** R2:18–20 and R2:94–100 now define the primary outcome as `Y_final = Y(w_final)`, the
  final incumbent at the campaign's actual final charged-run count, exactly as PD §7.1 defines Y; early
  endings are kept, no w=20 completeness filter, no imputed Y(20), and Y(5), Y(10), Y(15), Y(20) are
  descriptive budget-curve points only. R2:114–116 removes the rev-1 "complete instance sets at w=20" rule.
- **MAJOR 2, semantics.** R2:53–57 defines w as charged worker runs from G8/accounting (trial runs,
  candidate/incumbent replicate runs, 2r per verify; skips no run; failed runs charged once; reuse not
  charged twice). R2:58–69 defines a live per-charged-run hook at exact w ∈ {5,10,15,20}, snapshot before
  the decision, `controller_state_sha256` after the run before its decision, `pending_action`, and
  `snapshots/final.json` at actual `w_final`. This answers rev-1 MAJOR 2's questions in the text.
- **MAJOR 3, scope.** R2:127–132 states that PD §7 declares only Y(final), that Y(w) comes from PLAN
  R1-D3-OUTCOMES2 and must be written into the PD before any D.3 run, and that before code either PD
  §7/§8 gain the Y(w) text and S is re-pinned in §9/§14, or the author declares Y(w) as a separate,
  descriptive, reviewed unit with its own script/sha. That is the right authority statement.
- **Good smaller fixes.** R2:107–109 gives the audit record a per-campaign path
  `audit/<stage>/<arm>/r<rep>/w<w>/<instance_id>.json` (fixes the rev-1 collision) and splits
  `Y_final.jsonl` (primary) from `Y_w.jsonl` (descriptive); R2:120–121 drops "exact tests" and refers to
  §7.3's t/Holm/bootstrap; R2:30–32 states the measured-GPU-model basis.

## Remaining blockers

**B1 (MAJOR 1 residual) — a STOP/error campaign cannot contribute a primary `Y_final` row.**
R2:95–97 says an arm that ends early, including a "STOP/error campaign", "still contributes its final
row". PD:458–461 says that on a STOP the stage is reported as stopped with the STOP record and no outcome
table is built from a partial design; PD §8 requires `status: complete` (PD:399–407); S rejects a
non-complete row (S:276) and has no `stop`/`error` in `ENDED_ON` (S:193). Fix: only completed campaigns
(`worker_runs`, `llm_call_cap`, `no_fundable_candidate`) contribute `Y_final`; a STOP ends the stage with
no contrast. Say explicitly that "error" is not a complete-campaign status and that a non-clean chunk is
recovered by the whole-rerun rule (R2:37–38), not turned into a primary row.

**B2 (MAJOR 3 residual) — §3.2 still describes an interface the pinned S does not have, and the Y(w) unit
is still an open author decision.**
R2:119–125 says "`d3_analysis.py` receives the campaign `summary.json`/`Y_final.jsonl`, and a separate
descriptive `Y_w.jsonl`, … builds primary contrasts at Y_final". S reads only one or two
`r1_d3_outcome/v1` tables, the pre-declaration, the D.3b note and the pinned noise summary (S:9–16,
513–527); it computes Y from the table's `y_raw` (S:386–397) and validates the exact declared design
(S:310–312). The component that consumes G1/G6 outputs and writes the §8 table is G7 (PD:509), not S.
Fix: say primary `Y_final` goes G1 snapshots → G6 audit → **G7 outcome-table builder** → unchanged
`r1_d3_outcome/v1` → S; do not claim S reads `Y_final.jsonl`/summary. Y(w) is correctly declared outside
PD §7 (R2:127–132), but its schema/script is still undecided and the design itself says no code writes it
until the author chooses; that is a pre-code prerequisite, so the design as a whole is not code-ready for
Y(w). Also resolve the contradiction between R2:119 ("receives … `Y_w.jsonl`") and R2:132 ("no code writes
Y(w) until settled").

**B3 (MAJOR 1/3 documentation inconsistency) — §4 (and §5) still state the superseded design.**
R2:139 still says "§7: … paired contrasts at w=20, Y(w) secondary", contradicting R2:18–20 and
R2:94–100 and the MAJOR 3 statement at R2:127–132. R2:136 still says "H200 prerequisite" and R2:14–15
still says launch waits for the H200 or an author row, while R2:30–32 says launch uses the measured pool
model. §5's questions (R2:145–153) are stale (Q1 and Q2 are answered in R2; Q5 remains). These are
text-only but authoritative: an implementer reading §4 would reintroduce the w=20 primary rule and the
H200 gate. Make §1, §2.1, §4 and §5 consistent: primary contrasts at `Y_final` (not w=20); Y(w) outside
PD §7; GPU model per PD §2/§11 and PLAN:1564 (measured pool model, no H200 prerequisite).

**B4 (MAJOR 2 pre-code condition) — the per-charged-run hook's pin and the indivisible-charge rule.**
R2:58–67 asserts a live per-charged-run hook that fires after each charged run and before the decision.
PD:64 pins harness `a3fedbbd` unless FIXR3/EGATE needs a harness change, in which case a new reviewed pin
is named in the D.3a note with the §7.2 audit equality check. State whether the hook is available at the
current pin, or which new reviewed pin/action version provides it (G1/G8 dependency), and pre-register
that accounting increments w by exactly one per charged run so the hook can fire at exact w. R2:66–67
("if a multi-run action crosses a w boundary, the hook still records the exact w point after the crossing
run") is contradictory for a block charge (after the crossing run w > the declared point); with per-run
increments the sentence is unnecessary, without them exact w may not exist (an author decision). Settle
before code.

## Rev-1 minors still open (the diff does not touch §2.3, §4 or §5)

`git diff --unified=0 e16235b3 dedba911` has hunks only at §1, §2.1, §2.2, §3.1 and §3.2; §2.3
(R2:72–83), §4 (R2:134–141) and §5 (R2:143–153) are byte-identical to rev 1. Therefore:

- R1 MINOR 1 — `ended_on` is still `runs`/`llm_cap`/`stop`/`error` in §2.2 (R2:45–46); §3.2 (R2:122) now
  adds `stop`/`error` to the analysis enum, which is not in §8/S (S:193), and the both-budgets-hit
  precedence is still undefined. Open.
- R1 MINOR 2 — preflight/STOP list still misses the constants-file sha, the arms-frozen per-node
  constants, S's sha/tests, the stage note's preconditions, `cache_prompt`/`enable_thinking` flag
  mismatches, >1 % A5/A6 fallback, evaluation/T1-label reads and the no-use rule. Open; §2.3 unchanged.
- R1 MINOR 3 — a killed/non-clean chunk is still listed among the stage STOPs (R2:77) although R2:37–38
  gives the whole-rerun recovery rule; stage-wide STOP coordination across the ~42 chunks is still
  undefined. Open.
- R1 MINOR 4 — the per-campaign audit path is fixed (R2:107), but the per-chunk-vs-shared-ledger-root
  absence check and the final-at-actual-w audit record path are still undefined. Partly open.
- R1 MINOR 5 — G6 job layout/cache/scheduling is unchanged: "deepthought direct" vs "separate HTCondor CPU
  chunks", one host with 16 workers (jobs serial or sharing workers), seal point, single-writer/atomic
  cache and provenance. Open.
- R1 MINOR 6 — the audit still says "as `r1/c3/audit.py` runs B.2 audits" (R2:90) without saying G6 writes
  no label/evaluation block (PD:339–340); §3.2's refusal is still only "a test-label read" (R2:124), not
  the label/evaluation/split/sweep/sealed path set of PD:410–419/S:196–200. Open.
- R1 MINOR 7 — smoke is still "outputs may set walltimes only" (R2:81 against PD:120's "walltimes and the
  compute projection"); "(12 campaigns)" still covers only the six D.3a arms; the P10 verify-seed re-run
  at the launch commit is still absent (R2:82–83). Open.
- R1 MINOR 8 — the runner text still lacks `append_only_summary`, proposal schema/temperature 0.2, the
  server `cache_prompt:false`/thinking-off flags, and the `one_line/v1` skip display in the manifest;
  `chunk.json` (R2:39) still lists only pins/image/model/server/host/walltime/status. Open.
- R1 MINOR 9 — measured D.3 chunk time, 1.5x walltime and the P7 projection STOP are still absent from
  preflight; "H200 prerequisite" and the two H200 sentences contradict R2:30–32 (also B3). Open.
- R1 MINOR 10 — no G6 compute projection for four w points (the §11 43-min/11.5-worker-h figure is one
  audit per campaign). Open.
- R1 MINOR 11 — cache key `(node, c0, audit_seed)` still uses the symbol rather than c0's config sha;
  canonical `config_sha256` and "its record sha matches" are still undefined; cache provenance is still
  unstated. Open.
- R1 MINOR 12 — the design still targets pre-declaration revision 3 while the 26 Nov PLAN rows
  (`R1-D3B-UNCONDITIONAL`, `R1-D3-DECOMP`) require revision 4 before signing (PLAN:1560–1564); the arm
  list/smoke count/contrast families are still fixed rather than parameters; 80/1-repetition PROPOSED
  labels are still not marked in §2.2/§4. Open.
- New minor — for a campaign reaching w=20, `Y_final` and the descriptive Y(20) are the same audit; define
  the row/dedup rule between `Y_final.jsonl` and `Y_w.jsonl` (R2:107–109, 115–116).

## Evidence

`git show dedba911:docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` (153 lines);
`git diff e16235b3 dedba911 -- <design>` (one file, 57+/22−, 8 hunks in §1/§2.1/§2.2/§3.1/§3.2);
`git show a24a55bf:` the same PD, S, A and C read in round 1. No code, job, campaign, audit or test was
run; no label, evaluation, split, sweep-table or sealed file was opened. The seed/K/audit-condition checks
of round 1 are unchanged and still pass by inspection; this re-review is diff-focused.

VERDICT: ACCEPT WITH CHANGES
