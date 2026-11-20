# Independent review: sweep-2 EVIDENCE authorization note (approved: true) and scheduler dry-run report

Code-Commit: 344e387a779321eb466b10f3ebee71ef0222ee94

Reviewer: fresh, independent, read-only reviewer (AI-assisted, Claude). Nothing was pushed and no branch was modified. I worked in a
detached worktree at `origin/sweep2-auth-20261119` = `344e387a` (`scratchpad/review_note20`), which I removed afterwards.
I ran no test suite, so no `/tmp/r1_c3_*` or `/tmp/c3_audit_tmp_*` folders were created. I read no secrets or credential files.

## Scope

- Target files at `344e387a`:
  - `docs/r1/authorizations/c3_sweep2_20261119.md` (sha256 `6121422ee06f0e0fdeb7b24cdd279bd4bde84beeed1bbc4cb42e17ed07595809`)
  - `docs/r1/reports/sweep2_20261116/SWEEP2_SCHEDULER_DRYRUN_20261120.md`
  - `docs/r1/reports/sweep2_20261116/SWEEP2_SCHEDULER_DRYRUN_20261120_SHA256SUMS`
- Published main: `origin/main` = `3a6dcf4d15c0c70b38ac8e38feaea63230897083` after `git fetch origin`. This is also the merge base, so the branch is
  `main` plus 7 commits.
- Binding rows were read on `origin/main:docs/r1/PLAN.md` §10:
  - R1-SWEEP2-AUTH (l.1299), R1-SWEEP2-MEASURED-GPU (l.1302), R1-SWEEP2-MEMORY (l.1303), R1-SWEEP2-LAYOUT-H200 (l.1284),
    R1-SWEEP2-IMAGE (l.1287) and R1-SWEEP2-SETTINGS (l.1207);
  - R1-SWEEP2-RESOURCES (l.1244), R1-SWEEP2-LAYOUT-AMEND (l.1233), R1-S2C3-ACCEPT (l.1298), R1-S2C3B-LAUNCH (l.1243)
    and R1-S2C3B-RERUN (l.1286);
  - R1-SWEEP2-INTEGRATE (l.1316), R1-SWEEP2-INTEGRATE-AMEND (l.1323) and R1-MAIN-PROPOSER (c)/(g) (l.732).
- Prior reviews: `SWEEP2_C5_INTEGRATION_REVIEW_20261119.md` (§5) and `SWEEP2_AUTH_REVIEW_20261119.md` (round 3, R3-n1…n4).
- Code consulted on `origin/main`: `sweep2/s2_c5_switch.py`, `sweep2/s2_c2_lib.py` and `sweep2/render_jdl.py`. For comparison I also read
  `sweep2/render_jdl.py` at `d9ff7813`.

## Parser results (check 1)

I ran a small driver script with `AR_HARNESS_ROOT=…/scratchpad/harness_a3fedbb`. It imports `sweep2/s2_c5_switch.py` and
`sweep2/s2_c2_lib.py` from the worktree and runs them on the committed note bytes.

| Check | Result |
|---|---|
| `s2_c5_switch.parse_note` | **Accepted.** `approved=true`, `label=EVIDENCE`, `run_id=s2ev-20261119-a`. It returned 20 fields: the 12 required fields, `phase` and P1–P7. No duplicates. |
| `s2_c2_lib.resolve_label` (the only definition, `s2_c2_lib.py:307`; called by `validate_spec` at :286, the wrapper path) | **Returns `EVIDENCE`.** Input: a spec with `run_id=s2ev-20261119-a` that pins the note basename and its sha256, with the note in a sandbox dir. With a wrong run id it STOPs ("does not name this run id exactly"). |
| Lines matched by the `parse_note` regex `^([A-Za-z0-9_]+)\s*:` | Only l.15–34, all inside the fenced key block. |
| Lines matched by `resolve_label` (`partition(":")`, key in {approved, label, run_id}) | Only l.15–17. The prose occurrence of `approved: true` at l.97 is mid-line in backticks and is not read. |
| Encoding | UTF-8, LF line endings, no CR, trailing newline. |

The switch's `_authorized_note` (`s2_c5_switch.py:54-58`) accepts only a byte-identical blob on `origin/main`. So `check()` cannot pass
until the note is published. That is the intended order.

## Values against bounds (check 2)

| Field | Note | Bound / row | OK |
|---|---|---|---|
| image | `…@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296` (l.19) | R1-SWEEP2-IMAGE, `s2_c2_lib.FROZEN_IMAGE` (:77) | yes |
| walltime | 8735 (l.20) | ceil(1.5 × 5823) = 8735 (MEASURED-GPU, LAYOUT-H200); ≤ 17,469 (AUTH) | yes |
| disk | 42460970 (l.21) | LAYOUT-H200 / RESOURCES (peak × 1.4); `EVIDENCE_DISK_KB` (:40) | yes |
| memory | 32000 (l.22) | R1-SWEEP2-MEMORY (15,620 is a floor); `EVIDENCE_MEMORY_MB` (:39) | yes |
| chunks | 16 (l.23) | AUTH; 8 nodes × 2 memory modes | yes |
| layout_gpu_hours | 25.88 (l.24) | 16 × 5823 s / 3600 = 25.88 exactly; ≤ 60 | yes |
| layout_wall_hours | 25.88 (l.25) | ≤ 48 | yes, see m1 |
| b2_audits | exact required string (l.26) | SETTINGS (2), AUTH | yes |
| d8_lock | true (l.27) | AUTH; R1-BX-D8-CONFIRM is on main (l.1252) | yes |

**How `layout_wall_hours` 25.88 is derived.** It equals the GPU-h figure, which is the **serial** projection: all 16 chunks run one after
another at the measured 5,823 s each, 93,168 s = 25.88 h. With any concurrency the wall time is lower. If every chunk instead ran to its
walltime limit, serially, the total would be 16 × 8,735 s = 139,760 s = 38.82 h, which is still ≤ 48 h. A chunk that runs past its walltime
is a STOP, so 38.82 h is the worst case for run time. Queue wait is not bounded by either figure, as in any S2-C4-style projection. The
value is a valid projection within the cap, but the note does not say how it was derived (m1).

**P-line citations** (all checked with `git merge-base --is-ancestor <c> origin/main`):

- `dd1e22be`, `62b92bf8`, `3a6dcf4d`, `888f7ff4`/`ee2c2b5d`, `ab79b4ce`, `6cac401a` and `d9ff7813` are all ancestors of main.
- `62b92bf8` has parents `bab65f52` and `dd1e22be`; its subject is "Merge int-sweep2-c5-20261119 into main".
- The cited rows all exist on main: R1-SWEEP-HOST-HTC, R1-SWEEP-HOST-L40S-SITES, R1-SWEEP2-ANY-GPU, R1-SWEEP2-MEASURED-GPU,
  R1-S2C3-ACCEPT, R1-SWEEP2-LAYOUT-H200, R1-SWEEP2-MEMORY and R1-SWEEP2-IMAGE.
- `SWEEP2_C5_INTEGRATION_REVIEW_20261119.md` is on main with the verdict ACCEPTED WITH MINORS.
- The sweep-1 B.2 PASS is on main: `docs/r1/reports/b2_audit_20261119/PASS.json`, and `B2_AUDIT_RUN_REVIEW_20261119.md` gives VERDICT ACCEPTED
  with Code-Commit `ab79b4ce`.
- The P6 dry-run report exists only on this branch (see m6).
- Other pins match main:
  - noise summary sha `3d12ce05…`;
  - registry `gemma4_31b.json` sha `a04a0346…`;
  - harness `a3fedbbd…` (`s2_c2_lib.py:81`).

## The five integration-review §5 edits (check 3)

1. `layout_wall_hours` was added (l.25). **Done.**
2. P2 is PASS and cites `dd1e22be`, `62b92bf8` and the review (l.29). **Done.**
3. P3 reads `PASS — this note` (l.30). **Done.**
4. P6 is PASS, cites the switch at `dd1e22be`/`62b92bf8` and the review, and requires launch-commit C3b (l.33). **Done.**
5. `approved: true` (l.15). **Done.**

The header (l.3–9) no longer says "Draft" and no longer says P2/P6 are at STOP. Other prose that §5 asked to align is still stale (B1, M2,
m2 below).

## Dry-run report (check 4)

- The report states 16/16 dry-run rc 0, `request_memory = 32000`, `request_disk = 42460970`, `+RequestWalltime = 8735`, the v1 digest,
  `periodic_hold = (NumJobStarts > 1)` and `TARGET.GPUs_DeviceName =?= "NVIDIA H200"` (report l.8-10, l.33-35).
- These match what `render_jdl.py` on main emits for an EVIDENCE chunk spec that pins a note:
  - the H200 clause is added only when `label_source.authorization` is set (`render_jdl.py:41-43`);
  - `periodic_hold` is emitted at :83.
- The table has 16 rows: the 8 sweep-1 nodes (same set as `c3_sweep1_20261027.md`) × `{append_only_summary, none}`.
- The SHA256SUMS file has 32 entries: 16 `s2_c2_job.jdl` and 16 `s2_c2_job.dryrun.txt`. Every table hash equals its SUMS entry (0
  mismatches) and there are no duplicate hashes.
- **Not checkable here:** the JDL and dry-run files are on the pool (`/work/dwong/htcondor_prep_20261114/s2_dryrun_20261120/`), which this
  container cannot reach. I could not confirm that the hashes match the files or that the files contain the claimed lines. The verification
  is internally consistent, but it rests on the report.

## Branch diff (check 5)

`git diff --stat origin/main...344e387a` lists 4 files, all additions:

- the note;
- the dry-run report;
- the SUMS file;
- `docs/r1/reviews/SWEEP2_AUTH_REVIEW_20261119.md`.

There is no code, no PLAN change and no other authorization file.

## Findings

### Blockers

- **B1. The note says that pre-approval evidence is still missing, yet it carries `approved: true`**
  (`c3_sweep2_20261119.md:87-90`). The section "Evidence to publish before approval" still reads:
  - "the H200 re-measurement report/review is not yet on `main` (branch commit `6cac401a`)". This is now false, because `6cac401a` is an
    ancestor of main.
  - "the v6 precondition 9 harness-defaults check is still to be recorded". This is still true. R1-MAIN-PROPOSER (c) and (g)3 (PLAN
    l.732) require a check that the harness defaults used by the sweep are unchanged (`6adf385` → `a3fedbb`). I found no record of such a check on
    `main` or on any remote branch. A `git grep` for the harness-defaults check finds only the note itself, the auth review, and the old
    draft/handoff placeholders (`C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md:407`, `S2_M3_CLUSTER_HANDOFF_20261116.md:41`).
  - By its own text, the note is therefore not approvable. Publishing it would also make this contradiction part of the binding record,
    and changing it later changes the note sha.
  - **Fix:** record the harness-defaults check (report plus review, or an author row that settles it), cite it, and rewrite or remove l.87-90.
    Keep only the note-sha pinning sentence, which is still correct.

### Majors

- **M1. The note declares a worker-failure STOP that the EVIDENCE code does not enforce, and it leaves an "author decision" open.**
  - The note (l.73-76, and the STOP list at l.100-102) declares a STOP on the per-(node, mode) failure rate: "sweep-1 per-(node, memory
    mode) baseline + 5 pp with the 1 % exact-binomial small-n control". It calls per-(node, mode) versus overall "an author decision" and
    says "the current implementation is per-(node, mode)".
  - The integrated code does the opposite for EVIDENCE:
    - the per-chunk gate is skipped ("deferred to pooled sweep-2 collection", `s2_c2_lib.py:786-789`);
    - `collect_evidence` applies the **overall** pooled gate, sweep-1 rate + 5 pp, with no binomial term (`s2_c2_lib.py:1128-1149`);
    - the per-cell binomial check runs only for non-EVIDENCE (pilot) chunks (:790-793).
  - The code matches PLAN, which states an overall rate (R1-SWEEP2-LAYOUT-AMEND, l.1233). No PLAN row has the binomial control.
  - The consequence: a per-(node, mode) exceedance that a published "declared STOP" covers would not stop the run.
  - **Fix:** state the overall pooled +5 pp STOP as implemented. Drop the open "author decision" and either drop the per-cell clause or mark
    it descriptive.
- **M2. Stale pre-integration placement and render text that contradicts MEASURED-GPU and the launch-commit rule.**
  - l.79-80 ("Integration note") tells the operator to "render the launch JDL from the integrated wrapper `sweep2-main-20261116` @
    `d9ff7813`".
    - `render_jdl.requirements()` at `d9ff7813` has **no GPU-model clause** (`d9ff7813:sweep2/render_jdl.py:23-31`). It predates `9d3f35d2`
      "Restrict sweep-2 production placement to measured H200 GPUs" and nine other later commits to `s2_c2_lib.py`/`render_jdl.py`.
    - A JDL rendered as l.79-80 instructs could therefore match unmeasured GPUs.
    - The instruction also contradicts the launch-commit rule (render at main HEAD, or at a reviewed descendant) and the dry-run report,
      which rendered from `3a6dcf4d`.
    - The switch fails closed: the spec commit must descend from main and the JDL must equal the canonical render. But the binding text is
      wrong.
  - l.45-46 says "No site/GPU-model pin beyond that". This is false for EVIDENCE, which pins `GPUs_DeviceName =?= "NVIDIA H200"`
    (`render_jdl.py:41-43`; report l.10).
  - **Fix:** say the launch JDL is rendered from the launch commit with the H200 `gpu_measured` spec, and state the H200 pin.

### Minors

- **m1.** The note does not state how `layout_wall_hours: 25.88` was derived. It is the serial projection 16 × 5,823 s; the walltime worst
  case is 38.82 h ≤ 48. Integration-review m2 noted that the code does not cross-check this value. Add one parenthetical in the Layout bullet (l.65-67).
- **m2.** l.97-98 says "or an `author-*` branch the S2-C5 switch accepts". The integrated switch accepts only `origin/main`
  (`s2_c5_switch.py:54-58`). The wording is stale but fails closed.
- **m3.** l.62-64 says the sweep-1 B.2 audit "must finish before sweep 2". It has finished, as recorded at l.7-8 and in `B2_AUDIT_RUN_REVIEW_20261119.md`.
  Reword it to past tense.
- **m4.** The dry-run report:
  - does not record which note sha256 the 16 specs pinned (the H200 clause proves that a note was staged; `render_jdl.py:41-43`, :108-118);
  - lists err/rc files among the retained outputs, but the committed SUMS covers only `.jdl` and `.dryrun.txt`;
  - relies on pool files that cannot be checked from here.

  Record the pinned note sha. These are engineering dry runs, and the launch JDLs will differ anyway, because they are rendered at the
  launch commit.
- **m5.** P2 (l.29) cites only the C5 integration review. The wrapper/fix units were reviewed in `SWEEP2_INTEGRATION_REVIEW_20261118.md`
  (Code-Commit `16e67957`) and `SWEEP2_MEASURED_GPU_REVIEW_20261118.md` (Code-Commit `5b8d1afa`), both on main. Citing them would settle
  R3-n1 (the units being "only partly reviewed").
- **m6.** P6 (l.33) cites `SWEEP2_SCHEDULER_DRYRUN_20261120.md`, which is not on main. Publish the report and its SUMS in the same commit
  as the note.

## Before publication and launch (check 6)

1. Fix B1, M1 and M2 (and ideally m1–m6), then have the revised note re-reviewed. Any edit changes the note sha, and every spec must
   re-pin it.
2. Publish the note, the dry-run report and SUMS, and all review files to `main` together. Do not add another commit to `main` after
   that before launch.
3. Rerun S2-C3b at that exact `main` HEAD (or at a reviewed descendant whose authority files are identical), with the launch image digest,
   harness, server settings and the H200 layout. It must pass 8/8 (R1-S2C3B-LAUNCH; the note requires 8/8, stricter than R1-S2C3B-RERUN's
   7-node option). Earlier C3b passes (`759770` at `d9ff7813`) do not count.
4. Render the 16 launch specs and JDLs at the launch commit, pinning the published note's basename and sha256. Run `s2_c5_switch check`
   with `--liveness-record`. Then submit with both keys (`--enable`, `S2C5_ENABLE_REAL=1`) for `s2ev-20261119-a` only.
5. Record the launch commit, the note sha and the C3b record in the launch record.

## Summary

- The key block is correct. Both parsers accept it (EVIDENCE, `s2ev-20261119-a`). Every numeric value is within R1-SWEEP2-AUTH's bounds
  and matches the code's constants, and the five §5 edits are done.
- The prose that will become binding on publication still has problems:
  - it says pre-approval evidence (the harness-defaults check) is outstanding (B1);
  - it declares a worker-failure STOP that differs from PLAN and from the EVIDENCE code (M1);
  - it tells the operator to render from a pre-H200 commit whose JDL has no GPU-model pin (M2).
- The note is published byte-identically and its sha is pinned, so these must be fixed before publication, not after.

Verdict: REVISE
