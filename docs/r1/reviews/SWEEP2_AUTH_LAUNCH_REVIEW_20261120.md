# Independent review — sweep-2 launch authorization note and scheduler dry-run report

- **Reviewer:** fresh, independent, read-only reviewer (AI-assisted, DeepSeek Harness subagent). Not the note's
  author, not the executing cluster agent. This review file is the **only** artifact written; it is left uncommitted
  in the worktree.
- **Target:** branch `sweep2-auth-20261119` @ `344e387a779321eb466b10f3ebee71ef0222ee94`, worktree
  `.claude-worktrees/sweep2-auth-20261119`. Published authority: `origin/main` @
  `3a6dcf4d15c0c70b38ac8e38feaea63230897083`. The branch is clean and ahead of `origin/main` by 7 commits;
  `git diff --quiet origin/main..HEAD -- sweep2/` is empty, i.e. the integrated sweep-2 code on the branch is
  byte-identical to published `main`.
- **Reviewed:** `docs/r1/authorizations/c3_sweep2_20261119.md` (note),
  `docs/r1/reports/sweep2_20261116/SWEEP2_SCHEDULER_DRYRUN_20261120.md` + `..._SHA256SUMS` (dry-run report),
  and the required-edit list in `docs/r1/reviews/SWEEP2_C5_INTEGRATION_REVIEW_20261119.md` §5, against
  `R1-SWEEP2-AUTH`, `R1-SWEEP2-INTEGRATE`/`-AMEND`, `R1-SWEEP2-MEASURED-GPU`, `R1-SWEEP2-MEMORY`,
  `R1-SWEEP2-LAYOUT-H200`, `R1-SWEEP2-IMAGE`, `R1-SWEEP2-SETTINGS`, `R1-S2C3-ACCEPT`, `R1-S2C3B-LAUNCH`/`-RERUN`,
  `R1-BX-D8-CONFIRM`, `R1-B2-GO`/`PIN-FIX2` on `origin/main`, and the integrated code
  (`sweep2/s2_c5_switch.py`, `sweep2/s2_c2_lib.py`, `sweep2/render_jdl.py`).
- **Review time:** 20 November 2026 (Europe/Berlin). **Method: read-only.** No jobs, no `condor_*`, no project
  test suite, no git writes. The only execution was stdlib Python applying the integrated parsers to the committed
  blobs (`parse_note`; `resolve_label`/`validate_spec` with the note staged in a temp sandbox; `check()` with the
  publication gate simulated by monkeypatching `_authorized_note`), plus read-only `git` commands (`show`,
  `cat-file`, `merge-base --is-ancestor`, `ls-tree`, `diff`).

Note sha256 (committed bytes, 8,750 bytes): `6121422ee06f0e0fdeb7b24cdd279bd4bde84beeed1bbc4cb42e17ed07595809`.
Dry-run report sha256: `89a27f303d689aeee5aa27a0101baca39e6f5ca8982a15b05cfea6bae8dfc718`; its hash file:
`6da4bc9ea788aef31f62d7741b60cae5cf4d10dda430ef19dd45d6113d9831d5`.

---

## 0. Verdict summary

The §5 edits are **all present and exact**, the integrated `parse_note` **accepts** the committed note, the
integrated `resolve_label`/`validate_spec` **accept EVIDENCE once the note is staged**, `check()` **accepts once the
note is published on `origin/main`** (and correctly STOPs before that), every AUTH bound is satisfied, the dry-run
report is internally consistent and its hashes are reproducible for the canonical integrated render, and the switch
is still two-key disabled. **The dry-run report is acceptable as a record, subject to minors.**

The note is **not yet ready to publish byte-identically as the launch authority**. Three statements in the prose
(which the parser does not check and which the §5 edit list did not enumerate) are stale or false, and one of them
leaves a required pre-approval evidence item apparently outstanding while the key block now says `approved: true`.
Because the note must be published byte-identically and its cited evidence must be resolvable, these are fixes to
make before publication, not after. No code or parser change is required: every fix is a prose edit in the note.

**Final line (round 1): `VERDICT: NOT ACCEPTED`** (one blocker, two majors, three minors; §6 numbers the fixes;
superseded by the round-2 addendum at the end of this file).

---

## 1. What checks out (traceable evidence)

### 1.1 Git state and ancestry (read-only)

- `HEAD` = `344e387a`, `origin/main` = `3a6dcf4d`, branch ahead by 7; working tree clean before this review.
- `dd1e22be` parents = `efc55ed8` + `ee2c2b5d`; `62b92bf8` parents = `bab65f52` + `dd1e22be`; `3a6dcf4d` parent =
  `62b92bf8`; all of `dd1e22be`, `62b92bf8`, `3a6dcf4d` are ancestors of `origin/main`. So P2/P6's citation
  "merge `dd1e22be`, merged as `62b92bf8` on `main` `3a6dcf4d`" is **verified true**.
- The note is committed in `HEAD` and **absent on `origin/main`** (`git cat-file -e origin/main:docs/r1/authorizations/
  c3_sweep2_20261119.md` fails), as expected before publication.
- `sweep2/s2_c5_switch.py`, `sweep2/s2_c2_lib.py`, `sweep2/render_jdl.py`, `sweep2/spec.example.json` are present on
  `origin/main`; the branch adds only docs (4 files, including this review), so the dry-run report's "rendered from the
  integrated sweep-2 code on published `main` `3a6dcf4d`" is accurate.
- `origin/main:docs/r1/PLAN.md` carries the required rows `R1-SWEEP2-AUTH`, `R1-SWEEP2-MEASURED-GPU`,
  `R1-SWEEP2-MEMORY`, `R1-SWEEP2-LAYOUT-H200`, `R1-SWEEP2-IMAGE`, `R1-SWEEP2-SETTINGS`, `R1-S2C3-ACCEPT`,
  `R1-S2C3B-LAUNCH`, `R1-B2-GO`, `R1-B2-PIN-FIX2`, `R1-BX-D8-CONFIRM` (`_verify_launch`'s required four are among
  them).
- Two-key disabled: no `S2C5_ENABLE_REAL` is set in the environment or committed outside code/docs/tests; no
  `S2C5_SUBMISSIONS.jsonl` or `S2C5_SUBMIT_STARTED.json` exists in the tree; `origin/main`'s
  `sweep2/s2_c5_authorization.template.md` still says `approved: false`; there is no `c3_sweep2_*` note on
  `origin/main`.

### 1.2 §5 edits — present and exact

| §5 requirement | In the committed note | Verdict |
|---|---|---|
| Add `layout_wall_hours` finite in (0, 48] after `layout_gpu_hours` | l.25 `layout_wall_hours: 25.88` (after l.24) | **PASS** |
| P2 `PASS — `, citing integration + review | l.29: `PASS — main carries the integrated S2-C2 wrapper/fix units and S2-C5 (merge dd1e22be, merged as 62b92bf8 on main 3a6dcf4d), reviewed in SWEEP2_C5_INTEGRATION_REVIEW_20261119.md` | **PASS** |
| P3 `PASS — this note` + R1-SWEEP2-AUTH | l.30: `PASS — this note (R1-SWEEP2-AUTH)` | **PASS** |
| P6 `PASS — `, cites integrated switch + review + launch-commit C3b requirement | l.33: integrated switch (`dd1e22be`, `62b92bf8`), review, dry-run report path, "launch-commit C3b 8/8 required, switch enabled with both keys for this run id only" | **PASS** |
| `approved: true` exactly | l.15 `approved: true` (lower-case, exact) | **PASS** |
| `b2_audits` exact string | l.26 `b2_audits: none (this authorization carries no B.2 audits)` | **PASS** |
| P4 cites `R1-S2C3-ACCEPT` | l.31 | **PASS** |
| P5 / P7 correct | l.32 H200 smoke 759751/759752 + `R1-SWEEP2-LAYOUT-H200`, `R1-SWEEP2-MEMORY`; l.34 v1 digest + `R1-SWEEP2-IMAGE` | **PASS** |

Whole-file parser scan: exactly **20** `key: value` lines, all in the fenced block (lines 15–34): the 12 required
fields + `phase` + P1–P7. **No duplicates, no stray prose key-lines.** The extra `phase: c3_sweep2` is harmless
(neither required nor duplicated). No stale void layout values (12,203 / 42,460,977 / 41.72) occur in the note or
report.

### 1.3 Parser matrix (integrated code @ `origin/main`)

| Check | Result |
|---|---|
| `s2_c5_switch.parse_note` on committed blob | **ACCEPTED.** `approved=true`, `label=EVIDENCE`, `run_id=s2ev-20261119-a`, frozen v1 image, layout `8735 / 42460970 / 32000 / 16`, `layout_gpu_hours=25.88`, `layout_wall_hours=25.88`, exact `b2_audits`, `d8_lock=true`, P1–P7 with `PASS — ` and P4 citing `R1-S2C3-ACCEPT`. |
| Negative `parse_note` controls | STOP on `P2` not PASS, `approved: false`, wrong `b2_audits`, and `layout_wall_hours` = 49 / `nan` / 0. Fail-closed confirmed. |
| `s2_c2_lib.resolve_label` with the committed note staged in the job sandbox | **`EVIDENCE`** (approved + label + exact run id). |
| `s2_c2_lib.validate_spec` on an H200 EVIDENCE spec (8735/42460970/32000, `layout_measured_chunk_s=5823`, `gpu_measured=true`, `evidence_ready=true`) with the note staged | **ACCEPTED**, label `EVIDENCE`. Wrong approved flag, wrong run id, wrong image digest and wrong walltime all STOP. |
| `s2_c5_switch.check(spec, note, jdl)` with the committed note in `docs/r1/authorizations/`, JDL rendered by the integrated `render_jdl`, and the publication gate **simulated** | **ACCEPTED**, returning `run_id=s2ev-20261119-a`, `note_sha256=6121422e…`, `jdl_sha256=b512932fd7c7…`, layout 8735/42460970/32000/16. |
| `s2_c5_switch.check(...)` with the **real** `_authorized_note` | **STOP: "authorization note is not committed on origin/main"** — publication remains the single gate before `check()` can pass. |
| `resolve_label`/`validate_spec` semantics | EVIDENCE is accepted only with the approved note (run id, image, H200 layout, disk/memory, 18 instances, three transport attempts, `evidence_ready=true`); none of these is weakened. |

The reproduced canonical JDL sha256 for `digits_mlp-append_only_summary` is
`b512932fd7c7262165fdd46d564d0f5fe85f0b3a6d7e5c1445e7958b0acf780b` — exactly the first row of the dry-run report's
table and of `..._SHA256SUMS`. This is independent corroboration that the dry-run JDLs are the integrated canonical
renders for the approved note run id/name and the H200 layout (see §4).

### 1.4 AUTH bounds and recorded prerequisites

| R1-SWEEP2-AUTH bound / row | Note value | Verdict |
|---|---|---|
| request walltime per GPU model ≤ 17,469 s | 8,735 s = ceil(1.5 × 5,823) | **PASS** |
| projection ≤ 60 GPU-h | `layout_gpu_hours: 25.88` = 16 × 5,823 / 3,600 = 93,168 / 3,600 | **PASS** |
| projection ≤ 48 h wall | `layout_wall_hours: 25.88` (≤ 48; see m1 for derivation nuance) | **PASS** |
| disk / memory per R1-SWEEP2-RESOURCES / -MEMORY | disk `42,460,970` = ceil(1.4 × 30,329,264); memory `32,000` MB (the measured ~15,620 MB × 1.4 is a floor, not a cap) | **PASS** |
| v1 GPU image (R1-SWEEP2-IMAGE) | `sha256:69b06b35…05296` = `lib.FROZEN_IMAGE` byte-exact | **PASS** |
| 16 chunks | `layout_chunks: 16` = 8 nodes × 2 memory modes = `SWEEP1_WORKER_BASELINE` pairs | **PASS** |
| no B.2 audits | exact string; audit seeds 7001–7010 reserved in prose | **PASS** |
| `d8_lock: true` | present; `R1-BX-D8-CONFIRM` row is on `main` (gate `r1/c3/gate.py` sha256 `ffb70d7a…`, verified) | **PASS** |
| P4 by R1-S2C3-ACCEPT | cited; S2-C3 stays NOT PASS | **PASS** |
| Sweep-1 B.2 PASS recorded | on `main`: `docs/r1/reports/b2_audit_20261119/PASS.json` (`attempt b2-ab79b4ce-20261119T002306Z`), `REPORT.md`, and `B2_AUDIT_RUN_REVIEW_20261119.md` (`VERDICT: ACCEPTED`); `ab79b4ce` is an ancestor of `origin/main` | **PASS** |

No false claim was found among the bounds/evidence statements in §"Scope and pins", except the two stale items in
the "Evidence to publish before approval" bullet (finding B1) and the two prose claims in findings M1/M2.

---

## 2. Dry-run report (`SWEEP2_SCHEDULER_DRYRUN_20261120.md` + `..._SHA256SUMS`)

Verified mechanically against the committed bytes:

- **16/16 rows**; the chunk set is exactly the 8 sweep-1 nodes × 2 memory modes (16 unique pairs) — no missing or
  extra chunk.
- **`..._SHA256SUMS` = 32 entries** = 16 `s2_c2_job.jdl` + 16 `s2_c2_job.dryrun.txt`, all 32 hashes distinct, all
  filenames of the expected form.
- **Table ↔ hash file: 0 mismatches** — each row's JDL hash and dry-run hash equal the corresponding SHA256SUMS
  entry. The report's table and the committed hash file are consistent.
- **Reproducible canonical JDL.** Rendering chunk 1 from the integrated code with the approved note name/run id and
  the H200 layout gives exactly the report's first JDL hash (`b512932f…`). That hash encodes the run id
  `s2ev-20261119-a`, chunk id, v1 image digest, `request_memory = 32000`, `request_disk = 42460970`,
  `+RequestWalltime = 8735`, `periodic_hold = (NumJobStarts > 1)`, the canonical `requirements` line with
  `TARGET.GPUs_DeviceName =?= "NVIDIA H200"`, and the transfer input list including `c3_sweep2_20261119.md`.
- The report's claims (required lines on all 16, H200 requirement, dry runs only, no submission/queue change) are
  internally consistent, and no submission artifact exists in the tree. I could not independently re-check the
  cluster-side `.dryrun.txt/.err/rc` files: they are retained at
  `/work/dwong/htcondor_prep_20261114/s2_dryrun_20261120/` on deepthought and are not committed (see m2). The
  committed hash file is the only binding artifact.

---

## 3. Launch-commit rule and switch state

The note's "Launch commit (R1-SWEEP2-AUTH)" bullet (l.81–84) reproduces the PLAN rule correctly: `main` HEAD, or an
independently reviewed integration commit descending from published `main` with authority files (PLAN,
`authorizations/`, classification sidecars and index) byte-identical to published `main`, at which the S2-C3b
liveness is rerun and passes 8/8 (R1-S2C3B-LAUNCH); the launch commit is recorded in every job record and merged into
`main` afterwards; no commit to `main` between the C3b rerun and the launch. The note correctly **does not name a
launch commit** — that is left to launch — and `_verify_launch`
(`sweep2/s2_c5_switch.py:177-239`) implements exactly these gates (local `origin/main` equals `ls-remote`,
tracked-clean checkout at the spec commit, ancestry from `origin/main`, authority-path byte identity, required PLAN
rows, sealed C3b 8/8 at the exact pins, staged-byte identity, canonical render).

The switch remains **two-key disabled**: `submit()` needs `--enable` **and** `S2C5_ENABLE_REAL=1`
(`s2_c5_switch.py:243-258`); neither key is present. Before the note is published, `check()` STOPs at the
committed-note gate.

**What remains for the actual launch (after the fixes in §6):** (i) publish the corrected note byte-identically on
`origin/main` — the integrated `_authorized_note` accepts **only** `origin/main` (see M2), and its sha256 must be the
one pinned in the spec's `label_source.authorization_sha256`; (ii) publish the dry-run report/hash file with it if the
P6 citation is to resolve on `main` (see m2); (iii) build the launch spec and render the JDL from the integrated
launch code, pinning `reviewed_jdl_sha256`; (iv) record the launch commit, then rerun S2-C3b 8/8 there and seal the
record; (v) stage the exact bytes and pass `_verify_launch`; (vi) both keys, one-shot marker. No `main` commit during
the C3b-rerun→launch window.

---

## 4. Findings

### BLOCKERS

**B1. `approved: true` contradicts the note's own "Evidence to publish before approval" bullet (l.87–90), which is
also partly false.**
- l.87–88 still says the H200 re-measurement report/review "is not yet on `main` (branch commit `6cac401a`)".
  This is **false as of the target authority**: `6cac401a` is an ancestor of `origin/main` (`git merge-base
  --is-ancestor 6cac401a origin/main` succeeds; it entered `main` via `dd1e22be` → `62b92bf8`), and published
  `main` already records the H200 re-measurement in
  `docs/r1/reports/sweep2_20261116/S2_C4_RESULTS_20261116.md` ("Re-measurement on H200 … layout fixed": clusters
  759751/759752, 5,823 s, 8,735 s, 42,460,970 kB, 32,000 MB, 25.88 GPU-h) with the independent review
  `docs/r1/reviews/SWEEP2_MEASURED_GPU_REVIEW_20261118.md` (Verdict: **ACCEPTED**) also on `main`. The clause must
  be removed or corrected.
- l.88–89 still says "the v6 precondition 9 harness-defaults check is still to be recorded". I searched the branch
  and published `main` (paths and contents: `harness-defaults`, `precondition 9`, "harness defaults"/"defaults
  unchanged", all local heads' `docs/r1/reports` and `docs/r1/reviews`) and found **no record** of that check for
  sweep 2. `R1-MAIN-PROPOSER (c)` and `RUNBOOK.md` B.1b prerequisite 3 require that check before the sweep, and the
  note itself lists it as evidence to publish **before approval**. Setting `approved: true` in the same file is
  therefore either premature or self-contradictory.
- **Fix:** record the harness-defaults check (and cite it), remove/correct the stale H200 clause, and then either
  drop the bullet or retitle it as launch-time tasks; only then is `approved: true` internally consistent. If the
  coordinating chat holds that the check is not a launch gate, the bullet must still be rewritten to say so
  explicitly — the current text cannot be published with `approved: true`.

### MAJORS

**M1. The "Integration note" (l.79–80) points at a wrapper that cannot produce the JDL the integrated switch
requires.**
The note says to render the launch JDL from "the integrated wrapper `sweep2-main-20261116` @ `d9ff7813`". `d9ff7813`
is the tip of `sweep2-main-20261116`, and its `render_jdl.requirements()` (no spec argument) emits the any-GPU floor
**without** the `TARGET.GPUs_DeviceName =?= "NVIDIA H200"` line. The integrated code on `main` adds that line whenever
the spec carries an authorization (reviewed in `SWEEP2_MEASURED_GPU_REVIEW_20261118.md`), and the integrated switch
requires `requirements == render_jdl.requirements(spec)`. I rendered a `d9ff7813`-style JDL and ran the integrated
`check()`: it STOPs **"reviewed JDL must require the measured H200 placement"**. The dry-run report itself states it
was rendered from the integrated code on `main` `3a6dcf4d`, and its first JDL hash reproduces from that code (not
from `d9ff7813`). Calling `d9ff7813` "the integrated wrapper" is wrong; rendering from it fails closed.
**Fix:** replace the sentence with "render the launch JDL from the launch commit (the integrated `main`/reviewed
descendant) with the H200 `gpu_measured` spec, as in the dry-run report; do not render from the pre-measured-placement
branch tips (`d9ff7813` predates the H200 requirement)". The report already gives the correct procedure.

**M2. The boundary claim that an `author-*` branch suffices is false for the integrated switch.**
l.97–98: "the note on published `main` (or an `author-*` branch the S2-C5 switch accepts)". The integrated
`_authorized_note` (`sweep2/s2_c5_switch.py:54-58`) compares the note bytes **only** against
`git cat-file blob origin/main:<path>`; there is no `author-*` acceptance in the integrated code (the pre-integration
switch at `ee2c2b5d` did scan `refs/remotes/origin/main` + `refs/remotes/origin/author-*`; the integration replaced
that with the main-only form — a tightening, not a release). The note's own header (l.8–9) already says the correct
thing ("must be published byte-identically on `main`"). If the coordinating chat followed the parenthetical, the
switch would STOP ("not committed on origin/main"). **Fix:** delete the parenthetical `(or an author-* branch the
S2-C5 switch accepts)`; publication to `origin/main` is the only accepted route.

### MINORS

**m1. `layout_wall_hours: 25.88` is the execution-time sum, not a strict serial wall upper bound.**
16 × 5,823 s = 93,168 s = 25.88 h is the sum of measured chunk execution times (equivalently the GPU-hours
projection). Under the requested 8,735 s per chunk, a serial run's worst-case wall is 16 × 8,735 s = 139,760 s =
38.82 h — still ≤ 48 h, so the bound holds and the parser accepts 25.88. But the Layout bullet's "~25.88 GPU-h (< 60
GPU-h cap, < 48 h wall)" reads as if wall were 25.88 h; the integration review §5's phrase "serial upper bound" is
imprecise (the measured-GPU review on `main` correctly lists both 25.88 GPU-h and 38.82 h of requested run time).
Optional fix: "25.88 GPU-h / 25.88 h if chunks overlap; ≤ 38.82 h serial, both inside the 48 h cap".

**m2. Dry-run report: hash coverage, naming, and publication.**
- The committed hash file covers JDL + `.dryrun.txt` only (32 entries); the report also claims per-chunk
  `.dryrun.err` and rc are retained, but those are not hash-bound, so "16/16 rc 0" and "no job was submitted" are
  report assertions rather than independently checkable artifacts in the repository. The cluster output directory is
  outside the repo and I had no access to it (read-only brief); the reproduced first-JDL hash is the only independent
  corroboration of report content.
- The report calls the file `DRYRUN_SHA256SUMS`, while the committed file is
  `SWEEP2_SCHEDULER_DRYRUN_20261120_SHA256SUMS`; the report never names the committed copy. State the committed name
  (and that it binds JDL+txt only; rc/err live in the retained cluster directory).
- The report and hash file are only on the branch, not on `origin/main`; P6 cites the report path, so if only the note
  is published the citation will dangle on `main`. Publish the report + hash file together with the note (recommended)
  or make P6's citation point to something already on `main`.

**m3. The Audits bullet still uses present/future tense for a completed prerequisite.**
l.62–64 says the sweep-1 B.2 audit "is a separate authorization and must finish before sweep 2"; B.2 has in fact
passed (`PASS.json`, independent review ACCEPTED). With `approved: true` this reads as an outstanding condition.
Reword to "has finished (PASS; `docs/r1/reports/b2_audit_20261119/`, independent review ACCEPTED)" — the header
already says this in l.7–8.

### Observations (not defects, recorded for the record)

- The reproduced canonical chunk-1 JDL hash (`b512932f…`) is a strong, independent bind between the dry-run report,
  the approved note's run id/name, the H200 layout and the integrated renderer.
- The integration removed the pre-integration `author-*` acceptance (`ee2c2b5d` → `origin/main`); the integration
  review's claim that "no S2-C5 behaviour or check was lost" is imprecise about this tightening. It does not weaken
  the gate, but it is the source of M2.
- The note's key block itself is parser-shaped and fails closed: on the unedited draft the parser would STOP; with the
  committed bytes it accepts, and with the real gate it STOPs only at publication.

---

## 5. Verdict

The requested §5 edits, the parser behaviour, the AUTH bounds, the launch-commit rule and the dry-run report all
check out. The note is, however, an authority document that will be published byte-identically and its prose still
carries one blocker and two majors that the parser does not see: it declares `approved: true` while listing
pre-approval evidence that is either already on `main` (false) or apparently still outstanding (the v6 precondition-9
harness-defaults check), it directs the operator to render the launch JDL from a commit whose renderer the integrated
switch rejects, and it claims an `author-*` publication route the integrated switch does not accept. All are prose
fixes; none requires a code or parser change. After the numbered fixes below and a `parse_note` re-run, I expect a
clean re-review.

**Required fixes before publication:** (1) B1 — record/cite the harness-defaults check and remove/correct the stale
H200 clause in the "Evidence to publish before approval" bullet (or keep `approved: false`); (2) M1 — replace the
`d9ff7813` instruction with "render from the launch commit / integrated `main` as in the dry-run report"; (3) M2 —
delete the `author-*` parenthetical; (4) m1–m3 as wording/record improvements (m2 also decides whether the dry-run
report is published alongside the note). Re-run the integrated `parse_note` on the edited bytes and update the
note-sha pin accordingly.

VERDICT: NOT ACCEPTED (round 1; superseded by the round-2 addendum below)

---

# Round 2 addendum — re-review at branch tip `e4f11d01` (20 November 2026)

**This addendum supersedes the round-1 verdict above.** Target: branch `sweep2-auth-20261119` @
`e4f11d01df1ee5a12d104396f99f9599c876a145` (ahead 8 of published `origin/main` @ `3a6dcf4d`; working tree clean);
the round-1 review is committed at this tip. The only artifact changed by this re-review is this addendum
(uncommitted). Current hashes: note `d3e2c02ccd7cf371f9497b384a1393709f7ea4a43bf38a535da93e5487b18876` (9,521
bytes), dry-run report `5164ea68…`, its hash file `654ff1b7…`, new harness-check report `bc467b0a…`.

## R2.1 Round-1 findings — status

| Item | Fix in `e4f11d01` | Re-review result |
|---|---|---|
| **B1** `approved: true` vs stale pre-approval evidence | "Evidence to publish before approval" replaced by "Pre-approval evidence" (note l.91–97): H200 report/review stated on `main`; harness-defaults check recorded in `docs/r1/reports/sweep2_20261116/HARNESS_DEFAULTS_CHECK_20261120.md` | **Closed** — see R2.2.1 |
| **M1** `d9ff7813` render instruction | Integration note (l.79–82) now says render from the integrated code on the launch commit exactly as the H200 dry-run report; states `d9ff7813` lacks the H200 requirement and must not be used | **Closed** — claim verified (0 `GPUs_DeviceName` occurrences at `d9ff7813`; the integrated gate rejects such a JDL, round-1 §1.3) |
| **M2** false `author-*` acceptance | Deleted; boundary (l.104–106) now says only byte-identical published `main`; no `author-*` string remains in the note | **Closed** |
| **m1** wall-hours derivation | l.89–90 adds: `layout_wall_hours: 25.88` is the execution-time projection 16 × 5,823 s / 3,600; worst-case serial bound 16 × 8,735 s = 38.82 h ≤ 48 h. Arithmetic verified (139,760 s / 3,600 = 38.82 h) | **Closed**; placement nit → m4 |
| **m2** dry-run rc/err not hash-bound; hash-file name | `..._SHA256SUMS` now 64 entries (JDL + `.dryrun.txt` + `.dryrun.rc` + `.dryrun.err`); report names the committed hash file and says it covers rc/err | **Closed** — see R2.2.2 |
| **m3** B.2 present tense | Audits bullet (l.62–64) now says B.2 PASSED and independently ACCEPTED (`ops-b2-audit-20261119`, `B2_AUDIT_RUN_REVIEW_20261119.md`), satisfying R1-SWEEP2-SETTINGS (3) | **Closed** — review on `main` has `VERDICT: ACCEPTED`; `ab79b4ce` is an ancestor of `origin/main` |

## R2.2 Verification performed

### R2.2.1 Pre-approval evidence (B1)

- **H200 report/review on `main`:** confirmed. `origin/main:docs/r1/reports/sweep2_20261116/S2_C4_RESULTS_20261116.md`
  carries the H200 re-measurement (759751/759752, 5,823 s, 8,735 s, 42,460,970 kB, 32,000 MB, 25.88 GPU-h), and
  `origin/main:docs/r1/reviews/SWEEP2_MEASURED_GPU_REVIEW_20261118.md` has `Verdict: ACCEPTED` and records the same
  smoke figures. (Observation: that review is the measured-placement code review that accepts the smoke figures, not
  a standalone "re-measurement review"; this is acceptable for v6 precondition 5.)
- **Harness-defaults check:** the new report is committed at the branch tip; I re-read it and then verified its
  substantive claims against a retained clone at `/tmp/harness_check` (both pins present; HEAD = `a3fedbb`):
  - `git log --oneline --reverse 6adf3859… a3fedbbd…` = exactly the five commits listed in the report
    (`f8bc222`, `115df37`, `987fb26`, `382cbab`, `a3fedbb`).
  - `git diff --stat 6adf3859… a3fedbbd… -- configs nodes harness` = **empty**, as reported.
  - The reported **47** files = 16 `nodes/**/config.yaml` (including the two `.autoresearch_baseline` copies) + 31
    `configs/**` files at the new pin — count matches.
  - The full pin-to-pin diff touches only 8 code/test files (`llm/`, `manager/`, `control_plane/`, `memory/`, tests);
    the only default-affecting change is the accepted explicit `cache_prompt: false` (plus opt-in additions:
    optional `seed_key`, `controller_ledger_view` default `None` preserving historical records, Track S
    views/Summarizer). The report's "no config/default change" conclusion is therefore substantiated.
  - **Residual minor (m5):** the report's "combined config digest `e8d8b8e0…`" is not reproducible from the report
    as written — the digest's exact recipe/order is not stated and no per-file SHA256SUMS is committed (I tried the
    obvious recipes and none matched). The underlying claims were verified directly, so this does not block.

### R2.2.2 Dry-run hash file (m2)

- 64 entries verified: 16 `s2_c2_job.jdl`, 16 `.dryrun.txt`, 16 `.dryrun.rc`, 16 `.dryrun.err`, all over the same
  16 (node, memory-mode) chunk directories. Table ↔ hash file for JDL/txt: **0 mismatches**.
- All 16 `.rc` hashes are `9a271f2a…` = SHA-256 of `0\n`; all 16 `.err` hashes are `e3b0c442…` = SHA-256 of the empty
  file — consistent with the reported rc 0 / clean stderr for every chunk (the hash file now binds the rc claim).
- The report names the committed file `SWEEP2_SCHEDULER_DRYRUN_20261120_SHA256SUMS` and states the 64-entry coverage.
  Inherent residual: the `.rc`/`.err`/`.txt` contents themselves live in the cluster output directory and are only
  hash-bound here, as before; acceptable for an ENGINEERING dry-run record.

### R2.2.3 Integrated parsers on the new note

- `parse_note` on committed bytes: **ACCEPTED**; key block unchanged (`approved: true`, layout 8735/42460970/32000/16,
  `layout_gpu_hours`/`layout_wall_hours` 25.88, exact `b2_audits`, `d8_lock: true`, P1–P7 `PASS — ` with P4 citing
  `R1-S2C3-ACCEPT`).
- Whole-file scan: still exactly **20** `key: value` lines, all in lines 15–34; no duplicates or stray prose
  key-lines. No stale strings remain (`author-*`, "not yet on main", "still to be recorded", "Evidence to publish
  before approval" all absent).
- `resolve_label` → `EVIDENCE`; `validate_spec` on the H200 EVIDENCE fixture → ACCEPTED.
- `check()` with the publication gate simulated → **ACCEPTED**, returning the new `note_sha256=d3e2c02c…`; canonical
  chunk-1 JDL sha256 remains `b512932f…` (unchanged, matching the dry-run report). With the real gate, `check()`
  STOPs only at "authorization note is not committed on origin/main".
- Unchanged and re-verified: AUTH bounds (8,735 ≤ 17,469 s; 25.88 ≤ 60 GPU-h; 25.88 ≤ 48 h with the 38.82 h serial
  note; disk/memory; v1 digest; 16 chunks; no B.2; `d8_lock`); launch-commit rule (main HEAD or reviewed
  descendant with byte-identical authority files, C3b 8/8 at it, no commit window); switch still two-key disabled;
  `origin/main` still `3a6dcf4d`; note still absent on `main`.

## R2.3 Residual minors (non-blocking)

- **m4 (new, formatting).** The m1 wall/serial clarification (l.89–90) is indented as a continuation of the
  **Sealing/analysis** bullet (l.87–88), not the **Layout** bullet (l.65–69) where it belongs. Content is correct and
  the parser is unaffected, but this should be moved before the note is published byte-identically (easy two-line
  move; re-run `parse_note` and recompute the note sha after).
- **m5.** Harness-defaults check report: record the exact combined-digest command/order and commit (or attach) the
  47-file SHA256SUMS so the `e8d8b8e0…` digest is independently reproducible; note that `/tmp/harness_check` is
  transient. Underlying claims are verified above; non-blocking.
- **m6 (launch step, not a note defect).** The note cites branch-only evidence: `SWEEP2_SCHEDULER_DRYRUN_20261120.md`
  + its `_SHA256SUMS` and `HARNESS_DEFAULTS_CHECK_20261120.md`. Publish these with the note (the branch tip already
  contains them) so the citations resolve on published `main`; the note being byte-identical, the published note sha
  will be pinned in the launch spec.
- **Nit.** The integration note equates the launch commit with "`main` HEAD" while the launch-commit bullet allows a
  reviewed descendant; the stated launch plan is `main` HEAD, so this is acceptable wording rather than a defect.

## R2.4 What remains for launch (unchanged, subject to publication)

1. Fix m4 if desired, then publish the note **byte-identically** on `origin/main` together with the two cited
   evidence files; pin the published note sha256 (`d3e2c02c…` now; recompute after any edit) in the launch spec's
   `label_source.authorization_sha256`.
2. Launch at `main` HEAD: build the spec/render from the integrated code on that commit, pin `reviewed_jdl_sha256`,
   rerun S2-C3b 8/8 at that exact commit, seal the record, run `_verify_launch` against staged bytes, and enable the
   two keys only for run `s2ev-20261119-a`. No commit to `main` between the C3b rerun and the launch.
3. Publish the dry-run report/hash file and the harness-defaults check with the note (m6) so P6's citation and the
   pre-approval evidence resolve on `main`.

## R2.5 Verdict

All round-1 blockers and majors are closed and independently re-verified; the note parses and the switch accepts it
once published; the AUTH bounds, launch-commit rule and disabled state are unchanged; the dry-run hash file now binds
rc/err. Only non-blocking minors remain (m4 formatting, m5 digest recipe, m6 evidence publication, one nit). The
branch tip is ready for the author/coordinating chat, with m4 recommended before the byte-identical publication.

VERDICT: ACCEPTED
