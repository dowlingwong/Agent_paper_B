Reviewed base: d19c9072d0985cf343fe07fd2415a7fc5ecfb41b

# B2 hand-off draft (not armed) — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 5. Branch `mac-b2-handoff-20261114` from `gh/mac-b1-20261107` @ `1e5728f9` (the runbook's `origin/mac-b1-20261107`; the local `origin/` ref `3b7d5704` is an ancestor; found acceptable). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (two blocking: the B1→B2 marker transition ignored Track S and the `_d` post-run unit; B1-scoped invalid-trial rules were presented as settled for B2).
- Round 2: **accepted** at `d19c9072`.

Accepted commit (round 2, last): d19c9072d0985cf343fe07fd2415a7fc5ecfb41b

Round-2 notes, not blocking (left for the armed version): the model-output pre-check is wired at `campaign.py` l. 119–135 and 238 (l. 292–295 only validate the journals); the B2-start order is partly circular (Track P and the Track S watcher pause because the marker appears, while the draft wants Track S paused before it exists; fails safe); the no-preempt reading should cite hand-off `_d` and R1-EXAM-HOST-B1B2-TASL7 rather than R1-TASL7-AGENT-OCCUPANCY-07NOV; "for every phase" should read "for every evidence phase".

The round texts are reproduced unchanged below.

---

# Independent review — Unit 5, B2 hand-off draft (round 1)

Reviewed commit: 5879b892ef65c7ccc44551948297ac11c19d12fa
Branch: `mac-b2-handoff-20261114` (worktree `/tmp/pb/wt/b2h`), parent `1e5728f9d7433a38cf8fbff08cf526601fb4b264`
File under review: `docs/r1/proposals/B2_HANDOFF_DRAFT_20261114.md` (the only change; 156 lines added)
Sources checked: `ops-b1-restart-d-20261113` @ `7912b7ff` (code, configs, rule, RUNBOOK, PORTAL_EXAM_RUNBOOK, PLAN,
hand-off `_d`, diagnosis), `78c6fd7d` (`_c` post-run unit) and `gh/trackS-ops-20261030` @ `d7992019` (reviews of the
`_c` unit, the `_d` post-run candidate, the Track S S0.5 resume candidate). Task: `69b3576b:docs/r1/prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md`
§5; runbook review interpretation 10 / S12. Reviewer was read-only. Scratch was under `/tmp/rev_u5` and has been removed.

## Base choice

The runbook says "from `origin/mac-b1-20261107`". Locally `origin/` = `3b7d5704` and `gh/` = `1e5728f9`. `1e5728f9` is a
fast-forward descendant of `3b7d5704` (`git merge-base --is-ancestor` passes). It adds only two docs commits: the
`## 2026-11-13 — Track X B1 running` STATUS entry and nine `_d` review records (`git diff --stat 3b7d5704 1e5728f9`: 10
files, all under `docs/r1/`). The branch name is the same, and the author took the newest known tip of it. **Acceptable.**
Record the choice in the commit message or in READY.txt.

## Verified correct (sample)

- Rule sha256 `53018aa7…16ad` matches `x5_rule_v2.yaml` bytes. Checked rule fields: `ranking_mode: "off"`; finalists
  4 + 1 absent family, ≤ 5, ties `registry_order`; `b2_mode: "off"`; `selection` = b2_final_audited_y, ties lower GPU-h;
  `b2_instances: author_decision_from_b1_variance`.
- `exam_runner.py`: l. 405 `range(9011, 9011+n)` for b2. l. 394 STOPs if `b2_thinking_mode` ≠ off. l. 515–516 is the
  b2 STOP in `main`.
- `runtime.py`: l. 594–595 STOP in `start`; l. 924 `range(9201,9211)`; `author_gate` reads author/phase/approved/rule_sha256
  (l. 406). The v2 b2 STOP is at l. 425–426.
- `campaign.py`: l. 171–173 is the `collect` STOP; l. 306–311 is the final-Y block (unreachable at `7912b7ff`, as the draft implies).
- `analyze.py`: l. 267 and l. 281 refuse anything but ten seeds 9201–9210; l. 325 is the grid STOP.
- Config values, B1 vs B2: `b2_instances_per_node`, `nodes`, `llm_call_cap`, `workers` (4 vs 20), `paper_commit`,
  `anchor_duplicate_reference`, `authorizations.b2`, `d22_pick`, `template_repairs` (3 models), host/GPU UUID, harness
  `a3fedbb`, `cache_prompt` false, ctx 32768, q8_0, temperature 0.2, binary sha `b70f4882…7d8b`, build `620d222`. Anchor
  reference sha `84200770…85dd` matches the committed JSON.
- All PLAN rows named exist at `7912b7ff`. R1-EXAM-HOST-B1B2-TASL7 (4 Nov 18:10) does say P.3a only between B1 and B2
  or after B2. Diagnosis §3/§5 agrees with §6 of the draft on which M-codes became invalid trials (M2, M5–M9,
  M19 after trial 1, M20) and which stay STOP (M10, M15, M16, M17, M18, M21; M14 executes).
- Observer timeout is 60 s (`observer.py` l. 148). `mac-b1-obs180-20261113` holds the accepted standby (review at `dd0aa0da`).
- The `_c` post-run unit at `78c6fd7d` is the accepted rev (`B1_C_POSTRUN_REVIEW_R5_20261112.md`: accepted). Its
  commit message says "rev 5", but the file header still says "rev 4". This is cosmetic.
- Not-armed statement (l. 3–6, §0, l. 33 "No agent sets `approved: true`", l. 156) is clear.

## Findings

### BLOCKING

**B1. §5 marker transition: Track S is missing, and l. 127–132 reads as an instruction to retire the `_d` marker.**
(`B2_HANDOFF_DRAFT_20261114.md` l. 127–138)

- Between B1 and B2, TASL-7 runs more than P.3a. The `_d` post-run candidate
  (`gh/trackS-ops-20261030:docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md`, rev 2, `491e1241`) runs "before
  the Track S S0.5 resume". The resume candidate `TRACKS_S05_T7_RESUME_20261114.md` resumes S0.5 on TASL-7 once the
  `_d` marker is retired. Its watcher pauses on a priority marker; that pause is "resume later, not a failure".
- So at B2 start the B2 marker also pauses Track S, and a Track S GPU job may hold `gpu0.lock`. The draft only confirms the
  P.3a safe pause (l. 134). It does not confirm the Track S watcher (`trks_watch`) paused state, the free lease, or
  that no Track S collector or GPU job is running. That conflicts with "do not preempt other users' work" and with
  R1-TRACKS-HOST-2 ("Track S never pre-empts either"; Track S takes the same lease).
- l. 128 says "retire the `_d` marker with `b1_o2_marker.py retire` … as the `_c` post-run unit specified". That is an
  imperative for an action that this draft does not govern. The action has its own unit, the `_d` post-run candidate
  above, which the draft does not cite.

*Fix:*
- Cite the `_d` post-run unit (path, branch, commit, review status) as the procedure that retires the `_d` marker. Say
  that this draft neither performs nor authorizes that retirement. Keep `78c6fd7d` as the accepted pattern it adapts.
- Add Track S to "Between B1 and B2", citing the S0.5 resume candidate.
- At B2 start, confirm all of these, else STOP:
  - P.3a safe pause;
  - the Track S watcher has paused, or Track S is at a resumable boundary;
  - no Track S/P GPU job;
  - `flock -n ~/r1_locks/gpu0.lock true` succeeds.
- If the Track S priority on TASL-7 against B2 is unclear, route it to the author.
- In one sentence, reconcile R1-PORTAL-SCHEDULE's single marker ("created before the first B1 job, removed after the
  last B2 job") with the retire-and-recreate scheme. The scheme rests on R1-EXAM-HOST-B1B2-TASL7 (P.3a between B1 and B2)
  and the 12 Nov "cooperative lock, renamable" agreement cited in the `_c` unit header.

**B2. §2/§6 present B1-scoped invalid-trial rules as settled B2 rules, with a wrong factual premise.**
(l. 84–85, l. 142–146, l. 47)

- l. 84–85 says "once in PLAN — the 16,384 completion cap of R1-EXAM-B1-TRUNCATION-INVALID and the model-output rules
  of R1-EXAM-B1-MODEL-OUTPUT-INVALID". Both rows are already in PLAN at `7912b7ff` (PLAN.md l. 1141 and l. 1147). They
  are, however, **B1** amendments: "A B1 STOP …"; RUNBOOK l. 85 amends X.4/Phase 5 only.
- l. 142 then says "the B2 code must make these **invalid trials, not STOPs**". Applying them to B2 changes B2's
  evidence rule. That is the author's decision. Neither row nor X.6/Phase 6 makes it, and §0.2's authorization fields
  do not cover it.
- As written, the draft decides an evidence rule for B2.
- l. 47 also points to "The STOPs of §5", but the STOPs are in §6 (§5 is the marker transition).

*Fix:*
- Replace "once in PLAN" with: "in PLAN at `7912b7ff` (l. 1141, 1147), scoped to B1".
- Add a §0 precondition: an author PLAN row, or explicit text in the B2 authorization, adopts the cap, the M2/M5–M9/M19/M20
  invalid-trial rules and the proposal journal for B2.
- Phrase §6's first paragraph as "proposed for B2, subject to that row".
- Change "§5" to "§6" at l. 47.

### NON-BLOCKING

**N1. §0.3 STOP count and missing STOP sites** (l. 34–40). l. 34 says "four places STOP", then lists five; the commit
message says five. At `7912b7ff` there are at least two more b2 STOPs:
- `exam_runner.evidence` l. 327–328, `STOP: only x5_rule/v2 B1 evidence is implemented`;
- `campaign._collect_b1_review` l. 208, `STOP: B1 candidate refuses other phases`. This is behind `collect` but is the
  function that holds the final-Y block the draft cites at l. 91.

Fix: say "at least these places", add the two sites, and give line numbers for `exam_runner.main` (l. 515–516) and
`author_gate` (l. 425–426).

**N2. §0.3/§0.2 list of B1-only protections is incomplete** (l. 42–46, l. 30–33).
- Not listed, though gated on `phase=='b1'` at `7912b7ff`:
  - the cooperative GPU lease `~/r1_locks/gpu0.lock` (`runtime.py` l. 648–650);
  - `claim_runner_lock(preserve_existing=…)` (l. 651);
  - fresh-batch-only creation under `work_dir` (l. 611–619);
  - `author_gate`'s host / GPU UUID / workers / anchor-reference bindings (l. 441–458). For b2 these are not checked,
    so §2's "Unchanged from B1 and bound by sha: host TASL-7 and GPU …" (l. 80) is not enforced at `7912b7ff`.
- The journals and `cache_prompt` evidence live in `campaign._collect_b1_review` (l. 292–295), not in the cited `runtime.py`
  ranges. Also, l. 932–934 (harness hashes in `root`) lie just past "900–931".
- §0.2 should list every field `author_gate` reads for b2: `nodes`, `stage_a_table_sha256`, the amendment table and
  acceptance shas, `b1_analysis_sha256`, `llm_call_cap`, `instances_per_node` (l. 429–440). It should also list the
  host, GPU, workers and anchor fields the code unit is to add. "B2 values of §2" does not cover `b1_analysis_sha256`, which is in §1.

**N3. Per-node B1 variance** (l. 59, l. 68).
- `analyze b1` at `7912b7ff` outputs only a per-candidate pooled `increment_sd` (l. 190). It gives no per-node variance
  and no final-Y variance, because B1 has no final-Y audit.
- No "declared rule" for the power plan exists. The rule says only `author_decision_from_b1_variance`. The grid design
  (`B2_GRID_VERIFIER_DESIGN_20261104.md` l. 5) says the power plan is open.

Fix: mark the source as "to be computed by a reviewed script / author" and the rule as "to be declared in the author's
PLAN row". Also note the code bound `1 ≤ n ≤ 89` (namespace 9011–9099, `runtime.py` l. 438).

**N4. Audit seeds** (l. 69–70, l. 89–91).
- `exam_b2_v2.json` also carries B1's `audit_seeds` 9101–9104. Like `instance_seeds`, they are not read for b2. Say so.
- At `7912b7ff` the b2 job passes 9201–9210 as `audit_seeds` for **every** per-proposal paired audit too (`runtime.py`
  l. 924 → `campaign.py` l. 280–287 / `run_b1_audits`), not only for the final-Y audit. Audits are post-campaign, so
  this is not leakage into selection. But each audited proposal costs 2 × 10 seed runs instead of 2 × 4. That matters for
  the B2 time estimate and for audit time counted in GPU-h (the tie-break).

Fix: state this, and have the code unit or the author confirm it is intended.

**N5. X.6/Phase 6 wording vs x5_rule_v2** (l. 78, l. 94).
- RUNBOOK X.6 says "Top 3 also rerun once with thinking off where possible" and "zhixu portal". Phase 6 says "other
  thinking mode".
- The draft's "thinking on, descriptive" (code l. 398–399; `analyze._b2_summary_v2`) and "same host" (R1-EXAM-HOST-B1B2-TASL7)
  are the correct v2 readings. But the draft should say explicitly that it departs from the X.6 text and cite the rows
  that supersede it: R1-MAIN-PROPOSER, R1-EXAM-RULE-X5V2, R1-EXAM-HOST-B1B2-TASL7.

**N6. Schema sensitivity ordering** (l. 77, l. 95–100).
- `--free-sensitivity` needs a PLAN line naming D22 and the pick (`exam_runner.py` l. 362–363). The D22 pick is the
  author's X.7 (a) decision, which comes after the B2 report and STOP 6.
- So "runs after the primary result" (l. 96) should read "after the author records the D22 pick (X.7 (a)) in PLAN". The
  report then needs an addendum for it, rather than §3.4 sitting before §3.6.

**N7. Marker creation tool** (l. 135). `b1_o2_marker.py create` hard-codes the STATUS heading
`## <date> — Track X B1 running` (l. 48 at `7912b7ff`). Used for B2, it would write a B1 heading, contrary to
R1-PORTAL-SCHEDULE / §4.6 (`B2 running`). Fix: note that the B2 code unit must parameterise the phase in the marker tool,
or name the reviewed B2 equivalent.

**N8. §6 small omissions** (l. 143–154).
- M9 also covers non-finite numbers.
- The still-STOP list should add M19 **at trial 1**, and "any proposal that reaches the worker guard and fails it"
  (PLAN l. 1147 (4)).

## Summary

The draft is well sourced. Line citations, config keys and values, the rule hash and the M-code mapping check out
against `7912b7ff`, and the not-armed statement is unambiguous. Two items need fixing before acceptance:
- **B1:** the B1→B2 marker transition ignores Track S's planned S0.5 resume on TASL-7 and does not cite the `_d`
  post-run unit, while telling the reader to retire the `_d` marker.
- **B2:** B1-scoped invalid-trial rules are presented as settled for B2, on the false premise that the rows are not
  yet in PLAN.

Verdict: changes requested

---

# Independent review — Unit 5, B2 hand-off draft (round 2)

Reviewed commit: d19c9072d0985cf343fe07fd2415a7fc5ecfb41b
Branch: `mac-b2-handoff-20261114` (worktree `/tmp/pb/wt/b2h`), parent `5879b892` (round 1), base `1e5728f9`.
File: `docs/r1/proposals/B2_HANDOFF_DRAFT_20261114.md`. It is the only file changed (+88/−45), and the worktree is clean.
Sources: `7912b7ff`; `78c6fd7d`; `trackS-ops-20261030` @ `d7992019`. The `_d` post-run unit is byte-identical at
`491e1241` and `d7992019`, and the Track S resume unit is rev 2 at `d7992019`. The review was read-only; the scratch
folder `/tmp/rev_u5` has been removed.

## Correction to round 1

In `exam_runner.py` at `7912b7ff`, `def evidence` is at l. 328 and its b2 STOP is at l. 329–330. My round-1 N1 said
l. 327–328, which was off by one. The draft's "l. 328–330" is correct.

## Round-1 findings: fix check

| Finding | Status | Check |
|---|---|---|
| B1 marker transition / Track S / imperative retire | **Fixed** | l. 150–151 says the section authorizes no retirement and each step needs its own accepted unit. l. 153–157 cite the `_d` post-run unit (rev 2, `491e1241`, candidate) and say "only once that unit is accepted". l. 158–160 cover Track S S0.5 resume (rev 2) and P.3a between B1 and B2. l. 161–166 add the checks before the marker: Track S safe pause, P.3a safe pause, no compute app, `flock -n` on the lease. The R1-PORTAL-SCHEDULE note (l. 173–177) is supported: PLAN l. 1141 records the author's 12 Nov agreement that the marker "is a cooperative lock, not evidence; it is renamed into `~/r1_locks/_to_delete/`". |
| B2 invalid-trial rules for B2 / "once in PLAN" / §5→§6 | **Fixed** | §0.4 (l. 61–63) gives PLAN l. 1141/1147, says the rows are "scoped to B1", and makes adoption for B2 an author PLAN row. §2 (l. 101–102) says "if the author adopts them for B2". §6 (l. 181) says "Proposed for B2". l. 64 now points to §6. |
| N1 STOP sites / count | Fixed | "at least these places". Added `evidence` l. 328–330 and `_collect_b1_review` l. 208. `main` l. 515–516 and `author_gate` l. 425–426 match. |
| N2 B1-only protections, author-gate fields | Fixed | l. 36–39: `author_gate` b2 reads at l. 429–440 match (nodes / Stage A at 429, amendment 430–432, `b1_analysis_sha256` 433, cap 434/436, instances 438–440). Also checked: B1-only host/GPU/workers/anchor at l. 441–458; lease l. 648–650; runner lock l. 651; fresh batch l. 611–619; `root` range 900–934 (harness hash at l. 932–934); marker tool l. 48. l. 103 now states that host and GPU are enforced for b1 only. |
| N3 variance / power plan | Fixed | l. 76 and l. 85: `increment_sd` at `analyze.py` l. 190; no rule declared; 1 ≤ n ≤ 89 at `runtime.py` l. 438. |
| N4 audit seeds | Fixed | l. 87: config 9101–9104 not read for b2; 9201–9210 used for every paired audit (post-campaign); 2 × 10 vs 2 × 4; counts in GPU-h; to be confirmed by the code unit or the author. |
| N5 X.6 wording | Fixed | l. 113–115 quote X.6 ("rerun once with thinking off", "zhixu portal") and Phase 6 ("other thinking mode"), and name the superseding rows. |
| N6 schema sensitivity order | Fixed | Moved to §3.6, after X.7 (a). The PLAN D22 line check is at `exam_runner.py` l. 362–363. It goes into an addendum. |
| N7 marker tool heading | Fixed | §0.3 (l. 58–60) and §5 (l. 167). |
| N8 §6 omissions | Fixed | Non-finite in M9; M19 at trial 1 still STOP; worker-guard failure still STOP. |

Nothing in the new text reads as arming or authorizing. The status block, §0, §5's preface and l. 199 are consistent.

## New findings

### BLOCKING

None.

### NON-BLOCKING

**N9. Citation for the model-output pre-check** (l. 57). `campaign.py` l. 292–295 validate the observer journal,
the proposal journal and `cache_prompt` evidence after the campaign. The pre-check itself is wired through
`exam_manager` → `B1CappedLangGraphManager` (`campaign.py` l. 119–135, used at l. 238; code in
`r1/exam/b1_llm_truncation.py`). Fix: cite l. 119–135/238 for the pre-check and journal writing, and l. 292–295 for
their validation.

**N10. Order at B2 start** (l. 161–166).
- Both Track P (R1-TRACKX-MARKER) and the Track S watcher (`TRACKS_S05_T7_RESUME_20261114.md` §3: "a priority marker
  appearing (watcher pauses …)") use the Track X marker as their pause signal.
- Requiring Track S's safe pause *before* the marker exists, with "`trks_watch` paused or reading the new marker",
  is therefore partly circular.
- It fails closed (STOP), so it is safe. Still, the armed version should pick one order:
  - (a) pause Track S and P.3a by their own reviewed procedures, then create the marker; or
  - (b) create the marker, wait for both watchers to reach their safe pause, then confirm no compute app and a free
    lease before the first B2 job.

**N11. Occupancy row** (l. 140, l. 165). The author's verbatim R1-TASL7-AGENT-OCCUPANCY-07NOV ("你继续执行，不用管他。只要能跑就去跑")
says to proceed despite others' presence whenever the run can run. It does not state a no-preemption rule. The "do not
preempt" reading comes from hand-off `_d` l. 57, so it is an inherited pattern. Track X's priority over P.3a on TASL-7
is R1-EXAM-HOST-B1B2-TASL7. Fix: cite hand-off `_d` §2.4 for the no-preempt practice and R1-EXAM-HOST-B1B2-TASL7 for
the priority, rather than attributing either to the occupancy row alone.

**N12 (nit).** l. 36 "the fields `runtime.author_gate` reads for every phase": `author_gate` returns early for
`stage-a` and for dry runs (l. 399). Say "for every evidence phase".

## Summary

Every round-1 finding is fixed and checks out against the cited sources. The new text adds no factual error that
affects the procedure, and nothing in it arms or authorizes B2 or any marker retirement. The remaining items are
citation and wording nits that can be fixed in a later revision or in the armed version.

Verdict: accepted
Accepted commit: d19c9072d0985cf343fe07fd2415a7fc5ecfb41b
