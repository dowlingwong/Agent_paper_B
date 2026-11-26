Reviewed base: origin/main `f1f1b6511` (main has since moved to `cdb8be91`, docs only, no overlap); accepted at `aa73dc343` (code `a6732a48`), post-acceptance follow-ups confirmed at `ba5627f21` (code `0cc30a6c`)

# Independent review record — P.4: T1's RemoteWallClockTime charged to the probe (R1-P4-PROBE-CHARGE, P4-T1CHARGE A) and the pool tokenizers recorded from the GPU job's staging (the T4 addendum)

**Unit.** On `mac-trackp-p4-t1charge-20261126`: `r1/scripts/htcondor/trackp_p4/p4_lib.py`, `p4_switch.py`, `p4_spec.json` and
`p4_probe_spec.json` (comment only), `r1/tests/test_trackp_p4_runner.py`, the phase-1 note draft (`approved: false`), the unit report
`docs/r1/reports/trackp_p4_runner_20261122/P4_T1CHARGE_20261126.md`, and dated notes in the cluster test plan and the F2 report. Authority:
R1-P4-PROBE-CHARGE; the queue of 26 Nov 2026 (02:26), item 2, and the user's addendum (02:38) on T4. On the question raised in review, the
user confirmed on 26 Nov 2026 that T1 stays unchanged: the tokenizers are staged in the probe and P.4 GPU job (step 6, env3 in the v2.2 GPU
image, before any GPU work) and recorded in the job record.

**Process.** One independent reviewer for all rounds, read-only, synthetic data only, no label, evaluation, sealed or secrets file opened.
Round 1 found that T1's record was matched by file names only (a resubmission elsewhere, or an `unverifiable` fallback, under-charged T1).
Round 2 accepted with two minors (resubmissions under non-standard names or folders; the JSON-only route never compared with a later history
file), fixed by a second author after the first author's session was lost, and confirmed.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `f1f1b651` 59 failed, 4123 passed, 197 skipped, 3 errors;
code tip `0cc30a6c` 59 failed, 4135 passed, 197 skipped, 3 errors; `FULLSUITE_BASE_f1f1b651.txt` = `FULLSUITE_T1CHARGE_TIP_R2.txt` =
`FULLSUITE_BASE_cdb8be91.txt` (62 entries).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `af16cb11` | NOT ACCEPTED (M1 T1 record unpinned; m1–m4) |
| 2 | `aa73dc34` | ACCEPTED (r2-m1, r2-m2, r2-n1) |
| 3 | `ba5627f2` | CONFIRMED (two nits) |

**Open items.** T1 (job 760065) has not run (no H200 machine in the NEMO2 collector); before the probe record its `condor_history 760065 -af
ClusterId ProcId JobStatus RemoteWallClockTime` output is committed as `T1_versions/condor_history.txt`. `paper.commit` for the probe must be a
main commit containing this unit and the host-config fill (`p4-hostconfig-fill-20261126`). The T4 rc-127 record (`8a9d48a1f`) is only on branch
`trackp-p4-cluster-20261125`. Nits c-n1 (a second non-standard submit line in a top file) and c-n2 (a symlinked subfolder in the pinned folder)
are left for a later unit.

## Round 1 (`af16cb11`)

> ## Round 1, `af16cb11` (on main `f1f1b651`): NOT ACCEPTED
>
> One MAJOR (T1's charge not tied to T1's committed record); 4 minors, 4 nits. Charge chain, tokenizer change, scope and tests otherwise sound.
>
> ### Checks
> Tests one file at a time: test_trackp_p4_runner 151, test_trackp_sft 35, test_trackp_p3 23 passed; full-suite lists byte-identical (62). `validate p4_spec.json` 16.94 GPU-h; template refuses unfilled `paper.commit`; spec sha256s `6167dd53…`, `72349c5b…`. Scope clean; no `approved: true`. Author's facts confirmed: T1 = 760065, record holds `.dry`, `.jdl`, `.sh`, `.submit`; jdl/sh = reviewed bytes `fa7ec821…`, `125342d1…`; the rc-127 record only at `8a9d48a1f`.
>
> ### MAJOR
> - **M1.** `t1_record` (`p4_lib.py:1271-1294`, `t1_charge` `:1325-1333`) accepts any folder with files named `versions.jdl`/`versions.sh`, does not check their bytes, resolves `record_dir` against the cwd. Reproduced: (a) a resubmission committed under `trackp_p4_cluster_20261127/T1_versions/` with the input naming only it gives `match` and 760065 is never charged; (b) jdl/sh copy without `.submit` → `unverifiable`, any ClusterId accepted; (c) arbitrary bytes → `match`. Fix: pin `T1_RECORD_DIR` (repo root) and the jdl/sh sha256s; drop `unverifiable` (no submit = STOP; 760065 required); STOP on uncovered `T1_versions*` submit files elsewhere; `check_probe_ledger` re-reads the pinned record's ClusterIds and STOPs on any not in `t1.jobs`. Tests for each.
>
> ### minor
> - **m1** a T1 job submitted after the probe record cannot be charged and nothing notices (`:1248`, `:1586-1606`); add M1 point 4; test plan: T1 not resubmitted after the record, else a STOP for the chat.
> - **m2** no `condor_history` cross-check or proof the job left the queue; acceptable now (same trust as READY 109's wall clocks, bounded by one GPU and `+RequestWalltime 3600`); recommended: commit `condor_history -af ClusterId ProcId JobStatus RemoteWallClockTime` output as `T1_versions/condor_history.txt` and parse it (JobStatus 3 or 4, ProcId 0, equal wall clock) or build the JSON from it.
> - **m3** `tokenizer_record` (`:625-630`) silently skips broken symlinks; STOP on `is_symlink() and not exists()` or `resolve(strict=True)`.
> - **m4** the user's "before T1 or the probe" was reinterpreted (no staging in T1); agree on the merits but needs the user's OK; the first real staging run is the first probe (T7); huggingface_hub 2.2.0 cache constants and layout match the new checks; optional pre-check on deepthought (snapshot_download + `tokenizer_record` without AutoTokenizer).
>
> ### nit
> n1 test plan §6 step 3 still says "T4 if the chat says go" (T4 blocks nothing; say it is dropped); n2 merge the cluster branch tip so `8a9d48a1f` resolves on main; n3 drive the real `stage` in the staging-STOP test; n4 optionally add tokenizer sha256s to `comparable()`.
>
> ### Brief answers
> T1 repeats caught in input and same folder; other folders and `unverifiable` under-charge (M1); a submit file proves existence if pinned and complete; no floor correct (RemoteWallClockTime accumulates across restarts; `request_GPUs = 1`); exactly-once chain holds end to end; step 6 runs in `run_probe` (1110) and `run_job` (791) after identity, clone, freeze, configs and before table, data, sampler and `sft-dev`; GPU digest only, no CPU path; T4 blocks nothing; no regressions.

## Round 2 (`aa73dc34`)

> ## Round 2, `aa73dc34` (code `a6732a48`): ACCEPTED
>
> M1 fixed and checked; m1–m3, n1, n3, n4 fixed; n2 left (a merge decision); m4 closed by the user's confirmation of 26 Nov (T1 unchanged). Two new minors and one nit, reachable only by breaking the written procedure.
>
> - Tests one file at a time: test_trackp_p4_runner 155, test_trackp_sft 35, test_trackp_p3 23 passed; `FULLSUITE_T1CHARGE_TIP_R1.txt` byte-identical to the base list (62). Scope unchanged; `approved: false`.
> - **M1.** `T1_RECORD_DIR`, full jdl/sh sha256s and `T1_FIRST_CLUSTER` 760065 pinned in code; other `record_dir` STOP; no `unverifiable`; a `*.submit` in another `T1_versions*` folder under docs/ STOPs; `check_t1_record_charged` (from `check_probe_ledger`, i.e. `assemble` and `check_cap`) and the rebuild path (`p4_lib.py:1845`) re-read the pinned record. Real repo: `['760065']`. Scratch: a T1 job added after the record, a changed or deleted `condor_history.txt`, another `record_dir` each STOP.
> - **m2.** `--t1-history`: 4 fields, ProcId 0, JobStatus 3/4, exact submit set; `inf`, `nan`, `undefined`, status 5 STOP; tabs parse; sha256 stored in the base file.
> - **m3.** `resolve(strict=True)`; real `stage` tested.
> - Repo root `parents[4]` correct (same root as the switch's `REPO_ROOT`); only `t1_charge`, `check_probe_ledger` and the rebuild read the record; job copies never resolve it; a stage-copy `assemble` STOPs (fails closed).
>
> ### minor
> - **r2-m1** (`p4_lib.py:1302-1320`) only top-level `*.submit` in the pinned folder and case-sensitive `T1_versions*` strays are found (a resubmission in `T1_versions/rerun/`, as `versions.2.submit.txt`, or under `t1_versions/` is uncharged). Fix: scan the pinned folder recursively and STOP on any other file containing "submitted to cluster"; match strays case-insensitively.
> - **r2-m2** (`check_t1_record_charged`, `p4_lib.py:1413-1425`) the JSON-only route is never checked against a history file added later (0 s recorded, 3500 s committed later passes). Fix: require `condor_history.txt` for the first record, or compare stored wall clocks with any history file present and STOP if lower.
>
> ### nit
> - **r2-n1** an old T1 folder moved to `docs/**/_to_delete/T1_versions*` with its `.submit` makes the launch STOP (correct, fails closed); add one line to the test plan; do not exclude `_to_delete`.

## Round 3 (`ba5627f2`)

> ## Confirmation round, `ba5627f2` (code `0cc30a6c`): CONFIRMED
>
> The fixes for r2-m1, r2-m2 and r2-n1 do what report §7 says, and the real record on main passes the stricter scan. No new BLOCKING, MAJOR or minor findings; two nits needing a deliberately unusual layout.
>
> - `aa73dc34..ba5627f2` contains exactly: `p4_lib.py` (recursive `_t1_submit_like_files`, stricter `t1_record`, `condor_history.txt` required on the `--t1-wallclock` route, wall-clock comparison in `check_t1_record_charged`), `test_trackp_p4_runner.py` (two new tests; `_t1` gained `history`), test-plan markers, report §7, two full-suite lists. Scope unchanged; no `approved: true`. Main's move to `cdb8be91` touches nothing under `r1/`, `trackp_p4` or `T1_versions`.
> - Tests one file at a time: test_trackp_p4_runner 157, test_trackp_sft 35, test_trackp_p3 23 passed; `FULLSUITE_T1CHARGE_TIP_R2.txt` byte-identical to `FULLSUITE_BASE_f1f1b651.txt` and `FULLSUITE_BASE_cdb8be91.txt` (62).
> - r2-m1: `rerun/versions.submit`, `versions.2.submit.txt`, a lower-case `t1_versions/` with the submit line, `x.SUBMIT`, and a broken link each STOP; a `T1_versions_notes/` folder without submit text does not misfire. r2-n1: a `T1_Versions` folder under `docs/_to_delete/` with its submit file STOPs, as documented. r2-m2: `--t1-wallclock` without the history file refused; a stored wall clock below the history value, or a missing file, STOPs; equal values pass; the comparison runs whether or not a sha256 was stored.
> - Legitimate layout: on the real repo `t1_record()` returns `['760065']`; the pinned folder holds only `versions.{dry,jdl,sh,submit}` on every branch; a synthetic post-run layout (`versions.out/.err/.log`, `gpu_visibility.txt`, `T1_versions_sha256.txt`, `T1_VERSIONS.txt`, `condor_history.txt`) charges correctly via `--t1-history`; a legitimate `versions.2.submit` with a two-line history charges both jobs. Repo-root resolution unchanged and correct.
> - nit c-n1: a top-level submit file can hold a second job in a non-standard line that is not counted (fix: count case-insensitive "submitted to cluster" occurrences equal to `T1_SUBMIT_LINE` matches).
> - nit c-n2: a symlinked subfolder inside the pinned folder is not scanned (`os.walk` does not follow it); fix: any symlink inside a T1 folder is a STOP.

---

Code-Commit: 0cc30a6c
Verdict: ACCEPTED

Accepted 26 Nov 2026.
