# Independent review — sweep-2 authorization note DRAFT, `c3_sweep2_20261119.md`

- **Reviewer role:** fresh, independent, read-only reviewer. Not the author of the note, not the executing cluster
  agent. This review file is the only artifact written; it is left uncommitted in the worktree.
- **Target:** branch `sweep2-auth-20261119` @ `ed1f01bd` (worktree
  `.claude-worktrees/sweep2-auth-20261119`), base published `main` `de3de54f`. The branch adds exactly one file:
  `docs/r1/authorizations/c3_sweep2_20261119.md` (81 lines, `approved: false`). `docs/r1/PLAN.md` on the branch is
  byte-identical to `de3de54f` (checked with `git diff --quiet`).
- **Review time:** 19 November 2026, 01:17–01:26 CET (Europe/Berlin).
- **Method / no execution.** Read-only. I ran no jobs, no `condor_*`, no project tests, and made no git write. The
  only execution was a stdlib Python text-level application of the two parsers (copied read-only from the branches
  into `/tmp/s2rev/`) to the note text, plus `git` read commands. No repository file was executed or modified.
- **Authority read:** `docs/r1/PLAN.md` on `de3de54f` (row ids with line numbers below), the S2-M1 v6 draft
  (`docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md`) and its accepted review
  (`docs/r1/reviews/S2_M1_V6_REVIEW_20261117.md`), the S2-M2 report/review, the branch launch checklist
  (`sweep2-main-20261116` @ `d9ff7813`), the S2-C2 parser (`sweep2/s2_c2_lib.py` @ `sweep2-main-20261116`), the S2-C5
  parser (`sweep2/s2_c5_switch.py` @ `s2c5-switch-20261116` @ `84a0dc30`) and its review
  (`docs/r1/reviews/S2_C5_REVIEW_20261116.md`), the worker-fix review, the H200 re-measurement record (`6cac401a`),
  `r1/scripts/HARNESS_PIN_C3` and `r1/c3/gate.py` on `main`.
- **Read-only checks used for the parser matrix** are in §4.

Row file/line references are to `docs/r1/PLAN.md` at `de3de54f` (identical on this branch): R1-SWEEP2-SETTINGS
l.1207; R1-SWEEP-HOST-HTC l.1201; R1-SWEEP2-LAYOUT-AMEND l.1233; R1-S2C3B-LAUNCH l.1243; R1-SWEEP2-RESOURCES
l.1244; R1-SWEEP2-STOP-PRECEDENCE l.1245; R1-SWEEP-HOST-L40S-SITES l.1242; R1-SWEEP2-LAYOUT-H200 l.1284;
R1-S2C3-DIAG l.1285; R1-SWEEP2-IMAGE l.1287; R1-S2C3-ACCEPT l.1298; R1-SWEEP2-AUTH l.1299;
R1-SWEEP2-MEASURED-GPU l.1302; R1-SWEEP2-MEMORY l.1303; R1-B2-PIN-FIX2 l.1309; R1-B2-GO l.1266;
R1-SWEEP2-ANY-GPU l.1267; R1-BX-D8 l.752; R1-BX-D8-CONFIRM l.1252; R1-E1-OPENML-AMEND l.1241.

## 1. Verdict summary

The note is a good short distillation and its **key block is parser-shaped**, but it was evidently assembled from the
`sweep2-main-20261116` branch state + the S2-M1 v6 draft and it **has not applied the last day of published-main
authority** (`R1-S2C3-ACCEPT`, `R1-SWEEP2-AUTH`, `R1-SWEEP2-MEASURED-GPU`, `R1-SWEEP2-MEMORY`, `R1-B2-PIN-FIX2`, all
on `de3de54f`). Four of the P/launch statements are therefore false or stale, and one required launch precondition
(sweep-1 B.2 status) is missing. The blockers are **not** honestly marked: P4 is wrongly called STOP (the author
already accepted it), P2 is wrongly called PASS (the accepted S2-C2 units are not on `main`), and the GPU-admission
rule follows a provision that the author has amended. It should not be sent to the author in this state.

**Final line: `VERDICT: NOT ACCEPTED`** — numbered fixes in §3.

## 2. What checks out (traceable to authority or to the parsers)

- **Key-block shape.** All 11 fields `parse_note` requires are present (`approved`, `label`, `run_id`, `image`,
  `layout_request_walltime_s`, `layout_request_disk_kb`, `layout_request_memory_mb`, `layout_chunks`,
  `layout_gpu_hours`, `b2_audits`, `d8_lock`) plus `P1`–`P7`. A regex scan of the whole note finds **only these 19
  `key: value` lines, no duplicates, and none outside the fenced block**; the `phase` extra key is harmless.
- **v1 image digest** is byte-exact against R1-SWEEP2-IMAGE (l.1287) and the switch's `FROZEN_IMAGE`.
- **H200 layout arithmetic is correct.** ⌈1.5 × 5,823⌉ = 8,735; ⌈1.4 × 30,329,264⌉ = 42,460,970 kB (the peak is in
  the H200 re-measurement record, `6cac401a` §"Re-measurement on H200"); 16 × 5,823 / 3,600 = 25.88 GPU-h; 32,000 MB
  is the R1-SWEEP2-MEMORY value (l.1303). The H200 values match R1-SWEEP2-LAYOUT-H200 (l.1284).
- **Harness pin** `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` equals `r1/scripts/HARNESS_PIN_C3` on `main`.
- **GGUF**: file name and sha256 match the S2-C2 spec and the v6 draft; the provenance registry doc
  (`docs/r1/reports/exam_phase2_20261026/gemma4_31b.json`) is on `main` with sha256 `a04a0346…` (verified).
- **Noise source**: `results/r1/noise/D28_REPAIR_20261027/summary.json` on `main` hashes to
  `3d12ce…` (verified).
- **Server flags / thinking bytes / disclosed non-numeric differences** match R1-SWEEP2-SETTINGS (1) and
  R1-SWEEP2-LAYOUT-AMEND: 32,768, `-ngl 999`, `-np 1`, `--jinja`, q8_0 K/V, `cache_prompt` false, exactly
  `{"enable_thinking":false}`, `--no-webui` and `-lv 4` disclosed.
- **No B.2 audits** and seed reservation 7001–7010 match R1-SWEEP2-SETTINGS (2) / R1-SWEEP1-CLASSIFY; the liveness
  seed policy `sweep1_d28_reuse` and its overlap disclosure match R1-S2C3B-SEEDS.
- **No resume / STOP precedence** matches R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-STOP-PRECEDENCE: `periodic_hold =
  (NumJobStarts > 1)`, whole-chunk rerun only for a no-STOP-cause eviction, old directory moved aside and disclosed,
  over-walltime = STOP.
- **Seal / D8**: sealed `/ceph/.../sweep2/<run_id>/<chunk_id>/` with SHA256SUMS/SEAL_RECEIPT; gate code
  `r1/c3/gate.py` @ `6aa9985c` matches R1-BX-D8-CONFIRM (l.1252; `file sha256 ffb70d7a…` verified on `main`).
- **Selection-vs-deployment disclosure** (4090 selection vs HTCondor deployment) is present.
- **No stale L40S requirement, no 16k context, no CPU/site pin.** The historical L40S row is correctly superseded
  for the model/site pin.
- **`approved: false` fails closed in both parsers**: S2-C2 `resolve_label` STOPs "authorization note is not
  approved"; S2-C5 `parse_note` STOPs first on `P4`/`P6` not PASS, then on `approved: false`. No enablement is
  possible as drafted.

## 3. Findings

### BLOCKERS (fix before the note goes to the author)

**B1 — P4 is recorded STOP, but published-main authority resolves it: P4 must be PASS.**
The draft (l.6–9, l.29) treats S2-C3 as "currently a STOP" and tells the author both P4 and P6 must be resolved.
`R1-S2C3-ACCEPT` (PLAN l.1298), committed 17 Nov 23:46 and present on `de3de54f`, says: "Sweep-2 prerequisite P4
counts as passed by this acceptance", while "S2-C3 stays recorded as NOT PASS on its declared criteria". The
H200-vs-H200 determinism and the cross-stack difference from B2 are accepted, and the further L40S S2-C3 is a
descriptive diagnostic that "does not block launch". `R1-SWEEP2-AUTH` (l.1299) requires the note to say
"P1–P7 all PASS, with P4 by R1-S2C3-ACCEPT" before it may carry `approved: true`. As written the note can never
satisfy that bound and it asks the author to re-decide a point already decided. **Fix:** `P4: PASS — R1-S2C3-ACCEPT
(S2-C3 NOT PASS on its declared criteria is recorded; H200-vs-H200 deterministic, cross-stack difference from B2
accepted with disclosure; L40S descriptive diagnostic non-blocking)`; rewrite the opening paragraph.

**B2 — P2 is recorded PASS, but the "accepted S2-C2 fix units" are not on published `main`.**
`de3de54f` has **no `sweep2/` path at all** (`sweep2/s2_c2_lib.py`, `render_jdl.py`, `spec.example.json`,
`s2_c5_switch.py` are all absent; `git ls-tree de3de54f -- sweep2/` is empty). The reviewed S2-C2 wrapper and its
fix units live on `sweep2-main-20261116` @ `d9ff7813`, and the S2-C5 switch on `s2c5-switch-20261116` @ `84a0dc30`;
commits `8a8ea832`, `2efbb6f6`, `82c04862`, `61282190`, `83799722`, `d9b31a30` and `84a0dc30` are **not ancestors**
of `de3de54f` (checked with `git merge-base --is-ancestor`). The S2-M2 report
(`docs/r1/reports/INT_MAIN_SWEEP2_20261116.md` §1) itself says the S2-C2 wrapper was "**not included** (author:
later, with S2-C5)" in the S2-M2 integration. `9ae6d877` (the S2-M2 review record, whose accepted branch tip is
`0a8ce27c`) is on `main`, but it is only the integration's review record and does not bring the wrapper or its
fix units. The v6 review records the same: no review record exists on the branch for `61282190`, `2efbb6f6`,
`82c04862`, `83799722` or `d9b31a30`, and none is on `main`. P2 as written is therefore false. It matters beyond
prose: S2-C5's `parse_note` only checks that `P2` *starts with* `PASS`, so a false PASS would satisfy the switch's
P-check once the layout constants are updated, while the wrapper the jobs would run is still unintegrated. **Fix:**
`P2: STOP — the accepted S2-C2 wrapper and its fix units are not on main; no integration commit/review records
exist` (and name the v6 precondition-2 items in a "Preconditions before launch" section). If the author prefers the
narrower launch-checklist definition of P2 ("main contains the reviewed S2-M2 integration"), then P2 may be PASS
**only after** the text drops the fix-unit clause and a separate explicit STOP/precondition states that the wrapper
+ fix units are not yet integrated.

**B3 — The GPU-admission scope is stale: `R1-SWEEP2-MEASURED-GPU` restricts sweep-2 chunks to measured GPU models
and amends the 17,469 s unmeasured-model rule.**
The draft's title (l.1), Host bullet (l.37–41), Layout bullet (l.60) and selection bullet (l.71) still present the
unrestricted `R1-SWEEP2-ANY-GPU` rule ("any GPU ≥ 24 GB, CC ≥ 7.0", no model pin) and state "Other GPU types:
walltime 3 × H200 chunk = 17,469 s until measured (R1-SWEEP2-LAYOUT-H200)". `R1-SWEEP2-MEASURED-GPU` (PLAN l.1302),
on `main`, says sweep-2 chunks "run only on GPU models with a measured chunk time from a 2-instance ENGINEERING
smoke with working worker runs (`gates.worker` PASS): now H200 only"; the cluster agent may add another model
(e.g. NEMO2 L40S) only after such a smoke; walltime = 1.5 × the measured chunk; the projection over all admitted
models must stay ≤ 60 GPU-h and ≤ 48 h wall; "Once L40S is admitted, HTCondor `rank` still prefers it". That row
"**Amends R1-SWEEP2-ANY-GPU and the 17,469 s rule for unmeasured models in R1-SWEEP2-LAYOUT-H200, for sweep 2
only**". `R1-S2C3-ACCEPT` (l.1298) also requires the L40S `rank` preference. The draft therefore states an
admission rule the author has amended, has no unmeasured-model STOP, and omits the `rank` preference. **Fix:**
state measured-model-only admission (H200 now; L40S only after its own measured 2-instance smoke), per-model
walltime = 1.5 × measured and still ≤ 17,469 s, `rank` prefers L40S once admitted, keep the floor/record/disclosure
requirements, and add "chunk on an unmeasured GPU model" to the STOP list. `P1` should cite `R1-SWEEP2-MEASURED-GPU`
as well.

**B4 — The launch-commit rule as written is unsatisfiable and omits the `R1-SWEEP2-AUTH` alternatives.**
The draft (l.51–52) fixes "paper = launch commit (main HEAD at launch, containing S2-M2 and the accepted fix units)".
Because of B2 there is no such `main` HEAD. `R1-SWEEP2-AUTH` (l.1299) allows the launch commit to be "`main` HEAD,
**or** an independently reviewed integration commit that descends from published `main`, whose authority files
(PLAN, `authorizations/`, classification sidecars and index) are byte-identical to published `main`", and requires
that "at which the S2-C3b liveness is rerun and passes 8/8", that "the launch commit is recorded in every job
record and merged into `main` afterwards". `R1-S2C3B-LAUNCH` (l.1243) requires the C3b rerun at that commit and that
no earlier pass replaces it. The draft omits: the integration-commit option and its byte-identical authority
condition; the rule that nothing may change the launch commit between C3b and launch; the record-in-every-job and
merge-into-main-afterwards rules. It also does not say that the 8/8 C3b pass at paper `50176481` (job 759770) cannot
count, because `main` has since moved to `de3de54f` and will move again when the note is published. **Fix:** rewrite
the launch-commit paragraph verbatim from `R1-SWEEP2-AUTH`/`R1-S2C3B-LAUNCH` and state the no-commit window.

**B5 — A required launch precondition is missing: sweep-1 B.2 is not complete.**
`R1-SWEEP2-SETTINGS` (3) (l.1207) orders e1 → e2 → sweep-1 B.2, in parallel with sweep-2 preparation, and says
"暂不给例外" ("no exception for now"; an exception only if B.2 becomes sweep 2's sole blocker). The state of `main`
is that B.2 is authorized for one fresh attempt under a corrected pin: the live preflight at `435513d2` stopped in
the provenance guard, and `R1-B2-PIN-FIX2` (l.1309) allows "one fresh B.2 attempt" at `ab79b4ce` with new
scratch/output paths. **B.2 is not shown complete on `main`** (no completion record; the 18 Nov attempt stopped
before any seed run and the fresh attempt is only authorized). `R1-SWEEP2-AUTH` says the note is filled "once the
run is launch-ready", so this must be recorded. The draft has no `(g)2`/B.2 status line at all. **Fix:** add a
"Preconditions before launch" section (as in the v6 draft, precondition 7) recording: e1 accepted
(`E1_AMEND_RUN_REVIEW_20261117.md` is on `main`), B.2 authorized with one fresh attempt (`R1-B2-PIN-FIX2`), B.2 not
yet complete at the time of writing, and the no-exception rule; the launch gate must include it.

### MAJORS

**M1 — P6's STOP is honest but materially incomplete: the reviewed switch cannot accept this note even if P4/P6 are
set to PASS.**
The text (l.31) says only "switch on branch … reviewed, disabled; not yet on main". Two additional facts must be in
the note:
1. The reviewed `84a0dc30` switch hard-codes the **void** 16 Nov layout: `ACCEPTED_LAYOUT = {12,203 s,
   42,460,977 kB, 32,000 MB, 16 chunks, 41.72 GPU-h}` and the same in `REQUIRED_SPEC_LAYOUT`
   (s2_c5_switch.py l.28–35). With `approved: true` and P4/P6 set PASS, `parse_note` still rejects this note with
   "layout_request_walltime_s=8735 is not the accepted 32k layout" (checked, §4). The switch must be updated to the
   H200 values (8,735 / 42,460,970 / 32,000 / 16 / 25.88), re-reviewed and integrated before P6 can be PASS.
2. `_authorized_note` accepts the note only if its bytes are committed on `origin/main` or an `origin/author-*`
   branch (s2_c5_switch.py l.45–61). The note currently exists only on `origin/sweep2-auth-20261119`, which is
   neither; publication to `main` or an `author-*` branch is required before the switch's committed-note gate can
   pass. (This matches the publication path in `R1-SWEEP2-AUTH`; note the row says the **coordinating chat** publishes
   it to `main` without asking again, not the author.)
**Fix:** expand the P6 STOP text to name (i) switch integration into `main`/an integration commit, (ii) the void
layout constants needing update + re-review, (iii) publication of the note to `main` or an `author-*` branch, (iv)
enablement per run id only after P1–P7 are all PASS.

**M2 — Collection gate (w2) is stated in the cluster's per-(node, mode)+binomial form, not the row's overall form;
the deviation needs the author's decision.**
`R1-SWEEP2-LAYOUT-AMEND` (l.1233) writes (w2) as "**整体** worker 失败率超过 sweep 1 的失败率 + 5 个百分点即
STOP" (overall; sweep-1's rate computed from its ledger and recorded first). The draft (l.64–65, l.79) states the
cluster implementation: per-(node, memory mode) baseline + 5 pp **and** a 1 % exact-binomial small-n allowance
(`s2_c2_lib.py` `SWEEP1_WORKER_BASELINE`, `WORKER_BINOMIAL_ALPHA = 0.01`, `WORKER_FAILURE_MARGIN = 0.05`). The v6
draft marked this as an open author choice (item 2f / note 1). The two gates are not equivalent and the implemented
one can fail to STOP where the overall row would. **Fix:** record the deviation and the author's choice, or add
(w2) as written; also record sweep-1's overall failure rate from its ledger (v6 precondition 10) — it is not in the
note.

**M3 — P5's evidence is not on `main`, and two launch preconditions are missing.**
P5 (l.30) cites smoke 759751/759752 and R1-SWEEP2-LAYOUT-H200. The supporting re-measurement report is the branch
commit `6cac401a` on `sweep2-main-20261116` (not on `main`) and I found **no independent review record** for it;
the v6 draft's precondition 5 required both the report and its review. `R1-SWEEP2-AUTH` also requires the note to be
filled from an "independently reviewed launch spec", and no reviewed launch spec/integration commit is cited.
Missing alongside it: the harness-defaults check (R1-MAIN-PROPOSER (c); v6 precondition 9) and the sweep-1 worker
failure-rate record (v6 precondition 10). **Fix:** either publish the H200 report+review to `main` and cite them, or
mark P5/P2 as "PASS pending review"; add the harness-defaults check and sweep-1 baseline record.

### MINORS

1. **P3 PASS is premature.** `P3: PASS — this note` on a draft that is `approved: false` and not committed on
   `main`/`author-*` is circular. In the cluster template P3 only becomes PASS when the author commits/approves
   "this note". Mark `P3: DRAFT` now and let the author's signed note make it PASS.
2. **D8/analysis wording is stale.** "nothing reads labels before R1-BX-D8-CONFIRM (signed …)" (l.68–70) reads as a
   future gate, but R1-BX-D8-CONFIRM is **signed** and says sweep-2 label tables "may be analysed from this row on";
   the lock is satisfied. The closing "Labels count only after independent review and the author's freeze" (l.81) is
   not in the listed rows (R1-B1-CORPUS-FREEZE is sweep-1; R1-BX-D8-CONFIRM governs sweep-2 analysis). Align with
   R1-BX-D8 / R1-BX-D8-CONFIRM and drop or source the "freeze" sentence.
3. **STOP list is internally inconsistent.** l.78–80 declares a STOP on any "server difference", while l.48–49
   discloses the `--no-webui`/`-lv 4` non-numeric server differences as allowed. Say "server difference other than
   the disclosed non-numeric differences"; "paper … difference" is undefined.
4. **Liveness wording.** l.61–63 correctly says C3b runs at the launch commit, but it should add (a) no earlier
   S2-C3b pass replaces it (R1-S2C3B-LAUNCH) — in particular the 8/8 pass at paper `50176481`/job 759770 is not the
   launch commit now — and (b) the result is recorded in the launch record, not in this note.
5. **Per-campaign record claim depends on an open fix.** l.40–41 mirrors R1-SWEEP2-ANY-GPU ("every campaign records
   site …"), but the v6 draft's item 2i (whether each campaign's own record carries the job's host record) was open,
   and the liveness job record does not record `site`. Since P2 is STOP this is implementation-dependent; keep it
   as an integration check.
6. **Note-sha / spec binding missing.** The S2-C2 wrapper labels only when the spec's `label_source.authorization`
   names the note and `authorization_sha256` matches; the draft has no "checks before launch" line for this (the v6
   draft did). Add it.
7. **Citation nits.** l.59: `request_memory 32,000 MB` should cite R1-SWEEP2-MEMORY (l.1303: RESOURCES' 15,620 MB
   peak × 1.4 is a floor, not a cap). P1 should also cite R1-SWEEP2-MEASURED-GPU. The S2-M2 accepted tip is
   `0a8ce27c` (`9ae6d877` is the review-record commit). l.5–6 says the author publishes the note; R1-SWEEP2-AUTH says
   the coordinating chat publishes it to `main` after the author's approval.
8. **Caps incomplete.** l.59 cites the 60 GPU-h cap but not the 48 h wall cap, nor the per-admitted-model projection
   bound (R1-SWEEP2-SETTINGS (5), R1-SWEEP2-AUTH, R1-SWEEP2-MEASURED-GPU).
9. **Residual enforcement gap.** S2-C2 `resolve_label` checks only `approved`, `run_id` and `label`; it does not
   enforce P1–P7. If `approved` were flipped to true while P4/P6 stay STOP, a manually submitted wrapper job would
   label EVIDENCE; only S2-C5 (P6, disabled) enforces the P lines. Keep `approved: false` until the P block is
   correct and add a boundary that submission happens only through S2-C5.

## 4. Parser / bounds matrix (check 2)

All checks are static text-level applications of the branch parsers; no job/server/submission was involved.

| Check | Result |
|---|---|
| `parse_note` on the note **as drafted** | STOP: `authorization prerequisite P4 is not recorded as PASS` (also `approved: false` fails once P lines pass). Fails closed. |
| Stray `key: value` scan (the switch reads every line) | Exactly 19 matching lines: the 11 required fields, `phase`, and P1–P7. No duplicates; none outside the block. OK. |
| `parse_note` with `approved: true` and P4/P6 set to PASS | STOP: `authorization layout_request_walltime_s=8735 is not the accepted 32k layout`. The reviewed switch still pins `ACCEPTED_LAYOUT` = 12,203 / 42,460,977 / 32,000 / 16 / 41.72 (void R1-SWEEP2-LAYOUT). The switch must be updated to the H200 layout before P6 can be PASS. |
| `parse_note` field-level semantics | `image` = `FROZEN_IMAGE` ✅; `b2_audits` first token `none` ✅; `d8_lock` = `true` ✅; `layout_chunks` 16 ✅; `layout_gpu_hours` 25.88 vs 41.72 ❌ (same layout issue). |
| `_authorized_note` (committed-note gate) | The note is on `origin/sweep2-auth-20261119` only; the switch accepts only `origin/main` or `origin/author-*` → would STOP until published. |
| `resolve_label` (S2-C2) on the note as drafted | STOP: `authorization note is not approved` (regex `^approved:\s*true\s*$`). ✅ prevents EVIDENCE labelling. |
| `resolve_label` with `approved: true` | Returns `EVIDENCE` (`run_id` and `label: EVIDENCE` present). Note: it does **not** check P1–P7 (see minor 9). |
| Spec binding | The note's layout fields (8,735 / 42,460,970 / 32,000) match the branch `spec.example.json`; `run_id`/image would match a spec filled from it. Once the switch layout constants are updated, `check`'s layout comparison would pass. |

## 5. Recommended P block for the author's final note

| Field | Recommended now | Why |
|---|---|---|
| P1 | PASS — cite R1-SWEEP-HOST-HTC as amended by L40S-SITES, ANY-GPU **and MEASURED-GPU** | The model/site pin is gone; admission is now measured-model-only. |
| P2 | STOP (unless the author adopts the narrower S2-M2-only definition and rewords) | S2-C2 wrapper + accepted fix units are not on `main`; no integration commit/reviews. |
| P3 | DRAFT → PASS when the author commits/approves "this note" | A draft cannot certify itself. |
| P4 | **PASS — R1-S2C3-ACCEPT** | S2-C3 NOT PASS on its criteria accepted; H200 deterministic, cross-stack difference accepted; L40S descriptive diagnostic non-blocking. |
| P5 | PASS — smoke 759751/759752 + R1-SWEEP2-LAYOUT-H200 (report/review to be published or noted) | Author row is on `main`; the supporting report/review is only on the branch. |
| P6 | STOP — switch not on `main`; void layout constants must be updated to H200, re-reviewed, integrated; note published to `main`/`author-*`; enable per run id only | See M1. |
| P7 | PASS — v1 digest `69b06b35…` | R1-SWEEP2-IMAGE. |

## 6. Answers to the five review checks

1. **Fidelity.** Most pins trace cleanly (§2). Stale/contradictory items: P4 STOP vs R1-S2C3-ACCEPT; the "any GPU /
   17,469 s until measured" admission rule vs R1-SWEEP2-MEASURED-GPU (+ missing L40S `rank`); P2's fix-unit claim;
   the launch-commit paragraph; P5's unreviewed report; and the 48 h wall cap. No old L40S layout, 16k context or
   CPU/site pin remains.
2. **Parsers/bounds.** The key block is structurally valid and `approved: false` + STOP lines fail closed. When
   P4/P6 are "resolved", the **reviewed** switch still rejects the note on the void layout constants, and the
   committed-note gate rejects the current branch name; `resolve_label` works once `approved: true`. No stray
   `key: value` lines.
3. **Completeness.** Present: run_id, H200 layout, GPU floor, per-campaign record, liveness launch binding, no B.2,
   D8 sealing, selection-vs-deployment, 25.88 < 60 GPU-h. Missing: launch-commit rule details (B4), 48 h wall cap,
   per-model projection, (g)2/B.2 status (B5), harness-defaults check, sweep-1 baseline record, note-sha binding.
4. **Honesty about blockers.** P4 must be PASS, not STOP (R1-S2C3-ACCEPT). P6 STOP is right but incomplete (M1).
   P2 must be STOP, not PASS. P3 is a draft. Other unmet/precondition items: sweep-1 B.2 not complete (B5), the
   wrapper/fix-unit integration and reviews (B2), the H200 report/review (M3), e1 is on `main` and accepted
   (`E1_AMEND_RUN_REVIEW_20261117.md`; no action needed beyond the (g)2 status line).
5. **Findings.** Blockers B1–B5, majors M1–M3, minors 1–9 above.

---

VERDICT: NOT ACCEPTED
