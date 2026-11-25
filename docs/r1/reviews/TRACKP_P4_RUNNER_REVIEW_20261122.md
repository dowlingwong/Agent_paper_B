Reviewed base: `9c2979a2` (published `main` at the start; `3c3f822a` now, which does not touch the unit's files); accepted at `66fb86590dfef134efb31ca3ce37d41d4b188035`, post-acceptance fixes confirmed at `7a40746c00f404e737041f43e75618b479482673`

# Independent review record — Track P P.4 phase 1: the runner unit and the phase-1 note draft

**Unit.** On `mac-trackp-p4-runner-20261122`: `r1/scripts/htcondor/trackp_p4/` (`p4_lib.py`, `p4_switch.py`, the job script, render and spec),
`r1/c3/train/p4_phase1.py`, `r1/scripts/trackp_p4_test_path.py`, `r1/tests/test_trackp_p4_runner.py`, the phase-1 note draft
`docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md` and the report `docs/r1/reports/trackp_p4_runner_20261122/TRACKP_P4_RUNNER_20261122.md`.
Authority: the P.4 phase-1 authorization draft revision 4.2 on `main` (its §7 P3, the runner unit), R1-TRACKP-V21-FREEZE; the queue of
22 Nov 2026 (01:22), item 3, and the queue of 22 Nov 2026 (11:33), item 3.

**Process.** One independent reviewer for all rounds, read-only, synthetic data only (no label, evaluation, sealed or secrets file opened),
scratch under `/tmp/rev_p4run/` moved to its `_to_delete/`. Round 1 found three blocking defects (the clone's script path, the env3 freeze,
an assembly that could never pass), three majors and nine minors; round 2 found one major and six minors; round 3 accepted with three minors
(one running job per arm, the ledger entry before `condor_submit`, the probe record checked on `main`). The fixes were confirmed by the same
reviewer, and its two non-blocking notes (pin the order in a test; a recovery procedure after a failed submit) were taken in one more commit,
also confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `6cc0f95d` | NOT ACCEPTED (B1–B3, M1–M3; minors 1–9) |
| 2 | `7809d8e8` | NOT ACCEPTED (1 major; minors 2–7) |
| 3 | `66fb8659` | ACCEPTED (three minors) |
| 4 | `c6ad7e25` | CONFIRMED (the three round-3 minors fixed; two non-blocking notes) |
| 5 | `7a40746c` | CONFIRMED (both notes taken) |

**Open items.** For the author (report, "For the author"): the reading of "the same version number" in R1-TRACKP-V21-FREEZE (a local wheel label admitted today; one regex if the author forbids it); tokenizers staged through the hub rather than by curl; `kev-0.8b` as the first arm. The note draft stays `approved: false` with P4 PENDING (the author's tick). Cluster tests on NEMO2 H200 with image v2.1 (report, "Needs a cluster test"): the env3 `uv pip freeze` line format, the host config's paths, staging, the synthetic test path with a real base, and the transfer and seal of `out.tar`. Reviewer's edge case: an empty attempt sealed for recovery and a late job of the same arm sealed too are both charged (over-count, never under-count).

## Round 1 (`6cc0f95d`)

> **Verdict: NOT ACCEPTED.** Unit: branch mac-trackp-p4-runner-20261122 @ 6cc0f95d, compared with main 9c2979a2.
>
> All 65 new tests pass, and 171 pass together with test_trackp_sft, test_trackp_sft_test_eval and test_trackp_p3. But three defects mean no real H200 job could finish, and an assembly could never pass. The tests miss them because they replace `sh`, `trackp` and the job's inputs with fakes.
>
> ## BLOCKING
>
> **B1. Every `trackp.py` call in the job fails: wrong working directory.** `r1/scripts/htcondor/trackp_p4/p4_lib.py:474-475`
> - What is wrong: the script is given as the relative path `"r1/scripts/trackp.py"`, but it is run with `cwd=job_dir`. The clone is at `job_dir/paper`, so the path does not exist.
> - Failure scenario: I reproduced it in scratch. `L.trackp(...)` gives `ProtocolStop | STOP: trackp.py sft-select refused: python: can't open file '<job>/r1/scripts/trackp.py'`.
>   - Every job STOPs at step 7 (data).
>   - The STOP is also misclassified as `protocol`, because Python exits with code 2 here.
>   - The same happens to `sft_dev` and to the 2-step run of the test path.
> - Why the tests miss it: `test_trackp_failures_are_classified` and the end-to-end test both fake this call.
> - Fix:
>   - Use `str(clone / "r1/scripts/trackp.py")`, or run with `cwd=clone` (as `configs()` at :369 already does).
>   - Classify "can't open file" as `infrastructure`.
>   - Add a test that runs the real `_sh` against a clone stand-in, for example with `sft-select` on a missing run.
>
> **B2. The env3 freeze step fails: env3 has no pip.** `p4_lib.py:329`
> - What is wrong: the step runs `/opt/r1/envs/trackp/bin/python -m pip freeze`.
>   - env3 is built with `uv venv` plus `uv pip install` (`r1/scripts/htcondor/docker/Dockerfile:100-112`), which does not install pip.
>   - The committed freeze, which the image build checks line for line, has no `pip` line.
>   - The image's own check and the G.1b model (`g1b_lib.py:37`, `compare_freeze`) both use `uv pip freeze`.
> - Failure scenario: every job STOPs at step 3 with "No module named pip" (class `infrastructure`). The test fakes `sh`.
> - Fix: run `["/opt/uv/uv", "pip", "freeze", "--python", ENV3_PYTHON]`.
>   - The v2.1 build record (`docs/r1/reports/trackp_h200_20261118/V21_IMAGE_006FC315.md:21-27`) says the uv freeze still reads `causal-conv1d==1.7.0`, so the expected status is `identical`.
>
> **B3. `assemble` can never pass: the data and label identities contain the job's absolute paths.**
> - What is wrong: the job directory inside the container is the per-job HTCondor execute directory. The H200 smoke records show `/var/lib/condor/execute/dir_3154509/...` (`smoke_h200_20261121/handback/gpu_smoke.json`); I3 shows other dir_N. Paths under it end up in both values `assemble` compares:
>   - `trackp.py cmd_sft_data` writes `table.path` (`Path(args.table).resolve()`), `labels.path`, `labels.release_receipt.path`, `prompts.sweep_index.path` and `prompts.classification.path` into `sft_data.json`. Its sha256 is `record["data"]["sft_data_sha256"]`.
>   - `check_partition` returns `"partition": str(part)` (`p4_phase1.py:140`), which goes into `rec["inputs"]["labels"]`.
> - Failure scenario: with four jobs in four directories, `assemble` (`p4_lib.py:682-694`) always STOPs with "the jobs differ in ['data', 'labels']". I reproduced the label half in scratch: the same partition in two job directories gives different `check_partition` records.
>   - This breaks P4-JOB's "the data directory … bound by its manifest sha256 (the same in every job)".
>   - `test_assemble…` writes path-free records by hand, so it cannot catch this.
> - Fix (either one):
>   - build with job-relative paths and stop `trackp.py` from resolving them; or
>   - record and compare a path-free data identity in the job record and in `assemble`: `rows_sha256`, `splits_sha256`, the label sha256 and receipt, the table sha256s and the sweep-index sha256. Drop `partition` from the compared label record.
>   - Then add a test with two different job directories.
>
> ## MAJOR
>
> **M1. The per-arm pin file never binds the best checkpoint on a real model.** `r1/c3/train/p4_phase1.py:250-256`
> - What is wrong: `run_entry` hashes `stage_s/best/record.json`, which only the tiny stand-in writes (`tiny.py:123`). The real wrappers write `best/manifest.json` (`model.py:74,214-228`). The best-step record is `stage_s/best.json`.
> - Failure scenario: on the cluster, `best_record_sha256` is `None` for all 15 runs, with no STOP. `test_arm_pin_records_every_run` passes only because it uses the hashbag model.
> - Fix: hash `stage_s/best.json`, `best/manifest.json` and the `best/` tree (as `sft_test_eval._tree_sha` does), and STOP if any is missing. `trackp.py:382` has the same pre-existing issue (`model_files` is empty for real bases).
>
> **M2. The GPU-hour cap ignores repeats.** `p4_lib.py:695` (`assemble`), `p4_switch.py:188-225` (`submit`)
> - What is wrong: P4-CAP bounds the GPU-hours consumed, and P4-JOB says "a repeat counts against the cap and is not submitted if it would exceed it". `assemble` sums only the one chosen STOP-free attempt per arm. `submit` never adds up earlier attempts before a repeat.
> - Failure scenario: a 4B job that STOPs late (about 7 h) and is resubmitted from a new stage is not counted. The cap can be exceeded silently.
> - Related: `seal` (:637-639) refuses a record without the H200/image identity. A STOP at identity, an empty pre-created record after a walltime kill (JSONDecodeError), or a STOP before the `try` (:521-523) cannot be sealed at all. So those attempts are neither kept as sealed outputs (§4: "sealed partial outputs are kept") nor counted.
> - Fix:
>   - Seal every attempt; mark ones without identity as `unverified`, and keep the empty-record case.
>   - In `assemble`, and in `submit` before any repeat, sum `gpu_hours` (or the walltime if missing) over every `attempt-*` of the run.
>   - Have `assemble` refuse an arm with more than one STOP-free attempt (no picking among attempts).
>
> **M3. Test gaps hide the blocking defects.**
> - The `trackp.py` arguments the job builds are never parsed by the real CLI (B1).
> - The freeze step's `sh` is faked (B2).
> - The job directories are fixed and the records are hand-written (B3).
> - `arm_pin` is tested only on the tiny model (M1).
> - The happy path of `r1/scripts/trackp_p4_test_path.py` is never run; only its refusal of real labels is tested. That path is the evaluator wiring P3 asks for.
> - Fix:
>   - Parse the job's real argument lists with `trackp.main`'s argparse.
>   - Add a two-directory assemble test.
>   - Add a pin test on a manifest.json-style checkpoint.
>   - Add a CPU run of `trackp_p4_test_path` with an injectable `_build` (hashbag model) through `replay_test_prompts`, `predict_test` and `evaluate_test`.
>
> ## MINOR
>
> 1. **Freeze reading** (`p4_phase1.py:78-116`). It is fail-closed and is a defensible reading of R1-TRACKP-V21-FREEZE. Since the v2.1 build reports the freeze unchanged, consider narrowing it to `identical` only (or the exact `==1.7.0`), so the author question about local labels never comes up. The report's question stays valid otherwise.
> 2. **Freeze record contents not checked.** §4 asks the job to STOP if "the freeze is not signed". `inputs()` (:409-412) checks only the path and sha256. It should also check the file holds `approved: true` and `cdae9c3f…`.
> 3. **Freeze record not passed to the data build.** `data_build` does not pass `--label-freeze`, so the data manifest has `labels.freeze: null`.
> 4. **Receipt not tied to the table.** `inputs()` does not compare the receipt's `inputs.proposals_sha256` with the `sweep1_v3` proposals pin. `build_sft_data` only records `table_matches_audit_table`.
> 5. **Job does not check the protocol that actually ran.** It never asserts each `sft_report.json` protocol (micro_batch 8, effective batch 16, epochs, patience, loss), and `arm_pin` records the constant `MICRO_BATCH`.
> 6. **Switch binding gaps** (`p4_switch.py`):
>    - The §8 keys `table_pin`, `duplicate_policy`, `split`, `lr_grid`, `host` and `harness_commit` are neither required nor bound.
>    - `h200_sft_probe` is not tied to the spec's `estimate.source`.
>    - The `gpu_hours_cap` regex accepts "40.5".
>    - `STAGE_MANIFEST.json` is not bound, and `check` does not re-check the staged partition against the spec (the job does).
>    - `check(table=, partition=)` are unused parameters.
> 7. **Note draft:**
>    - Check 1 ("approved: false as the only open field") cannot work as written: `check` STOPs first with "not committed on origin/main".
>    - P4 is pre-marked PASS, but the draft wants an explicit author tick. Mark it as the author's.
>    - The v2.1 digest already exists on main (`V21_IMAGE_006FC315.md`, gpu `sha256:31478d99…`). It could be cited, pending P5.
>    - `gpu_hours_cap` says 16.94 for the four jobs; the draft's 14–19 includes the probe. Say so.
> 8. **Doc mismatch:** the `p4_lib.py` docstring lists env3 before the clone; the code (correctly) clones first.
> 9. **Ledger scope:** the test-read ledger lives inside each job's `out/`, so "one read per arm" holds only within a job. Harmless for synthetic data; worth stating.
>
> ## Verified as sound
>
> - `check_env3_freeze` is fail-closed: duplicates, any other package, a removed or added causal line, another version, `.post`, a wheel of another version and unreadable references all STOP. The pinned freeze is R1-ENV-PIN's (`50238e5a…`) with `causal-conv1d==1.7.0`.
> - `check_partition` pins `labels:` and `label_receipt:`, source/stage, the frozen block and the receipt output. `LabelBlockSource` re-checks through `open_partition` and `release_row` using the clone's git; the full clone with `origin/main` fetched supports that.
> - `lc_points` and `lc_subset`:
>   - points are those below the training-set size, plus `full`;
>   - seed is `20261122 + n`, no replacement, rule no-ops included;
>   - val and val_seen rows and `splits.json` are unchanged, and the result loads with `load_sft_data` (real-label checks pass, the split config is unchanged);
>   - a subset of a subset is refused.
> - `rps_skill_bootstrap`:
>   - primary val rows follow `load_sft_data` order, which matches `pred_val_logits.npy` (`run_stage_s` predicts over `val` in file order);
>   - clusters are instance ids (`<node>__s<seed>`, unique across nodes);
>   - resamples are paired across seeds, and the weighted RPS skill is a ratio of weighted means with the training base rate;
>   - 2,000 resamples, seed 20261108; T comes from `best/temperature.json`; the data sha256 is bound.
> - The `trackp.py` option names, the `--run-dir` layout (`<run-dir>/data`, `<run-dir>/stage_s`, `select/report.json`) and the `sft-select` usage match the real CLI. Only the script path is wrong (B1).
> - The sweep ledgers are tracked under `results/r1/evidence/…` and reached through the classification remap. Offline tokenizer reuse through `snapshot_download` at commit revisions works. Kev and the controls load from local paths.
> - `validate_spec`:
>   - placeholders are refused at launch; v2 is refused; env3, the split, table, labels, arms (controls always), protocol and caps are fixed;
>   - walltime is at most 86,400 s;
>   - projection reproduces 16.94 GPU-h and 24.41 slot-hours;
>   - the SFT and host config sha256 in the spec match the current files.
> - The JDL matches the G.1b model. The preview stage cannot be submitted. `verify_launch_p4` is equivalent to `verify_launch_tasl`.
> - Switch: two keys, committed spec, launch binding with `PLAN_ROWS`, once-only marker, first-arm gate.
> - `trackp_p4_test_path.py` uses `sft_test_eval` correctly by reading (but untested):
>   - `run_record` on `stage_s`;
>   - `LEDGER_NAME` under `<out>/ledgers/sweep1_v3/`;
>   - synthetic provenance (seed, shift_z) equal to the manifest's;
>   - model loaded through `trackp._build` plus `model.load` under the lease.
> - The note draft reads `approved: false`. Its §8 values and P-texts match draft rev 4.2. The fields left open are right: image/VERSIONS/smoke/E0/probe, host config sha256, labels/receipt/freeze, P2, P3, P5, P7, spec sha256 and code_commit.
> - The diff only adds 10 new files and modifies nothing existing.
>
> Housekeeping: the worktree is untouched (clean, HEAD 6cc0f95d), and my scratch is in `/tmp/rev_p4run/_to_delete/`. No memory facts were used.

## Round 2 (`7809d8e8`)

> Reviewed base: 7809d8e873dd0146a748cdfa4a5efbcabc3a4452 (mac-trackp-p4-runner-20261122, parent 6cc0f95d)
>
> # Track P P.4 runner unit, review round 2
>
> **Verdict: NOT ACCEPTED.** All six round-1 findings except M2 are closed; M2 is not closed for a job killed at walltime or one that STOPs early (finding 1). Fixing it is small.
>
> Targeted tests: 180 passed (test_trackp_p4_runner, test_trackp_sft, test_trackp_sft_test_eval, test_trackp_p3). The worktree is clean and still at 7809d8e8. My scratch is in /tmp/rev_p4run/_to_delete/ (r2_scratch, r2_t).
>
> ## Round-1 findings
>
> - **B1 (trackp.py script path): closed.**
>   - The job now calls `str(clone / TRACKP_SCRIPT)` from the job directory; `configs()` uses the same path.
>   - A failure counts as a protocol STOP only when the exit code is 2 and stderr has a line starting `STOP: `. A missing script or an argparse error is an infrastructure STOP.
>   - The new test runs the real `_sh`.
> - **B2 (no pip in env3): closed.** The step runs `/opt/uv/uv pip freeze --python /opt/r1/envs/trackp/bin/python`, and `image_identity` requires the uv binary.
>   - The path matches the Dockerfile (`UV_INSTALL_DIR=/opt/uv`, copied into the gpu stage) and G.1b's `UV`.
> - **B3 (job paths in the compared identities): closed.**
>   - `data_identity` drops every `path` key, which covers `table.path`, `labels.path`, `labels.release_receipt.path`, `labels.freeze.path`, `prompts.sweep_index.path` and `prompts.classification.path`. The rows, splits, table, index, classification and label sha256s stay.
>   - `comparable` leaves out `partition`.
>   - Checked in scratch: four `run_job` records in four separate `…/execute/dir_N` directories seal with `identity_verified`, `sums: verified` and charge basis `job_record.gpu_hours`, and `assemble` passes.
> - **M1 (pin file did not bind the checkpoint): closed.**
>   - Each run entry binds `best.json`, the checkpoint manifest (`manifest.json`, or `record.json` for the CPU stand-in), the whole `best/` tree, `temperature.json` and `sft_report.json`.
>   - A missing file is a STOP. A test covers the real-wrapper layout.
> - **M2 (cap ignores repeats): partly closed.** `seal` now seals STOP records and records without identity, `charged_hours` sums every attempt, `assemble` refuses a second STOP-free attempt and requires `identity_verified`, and the switch has `check_cap`. The remaining gap is finding 1.
> - **M3 (test gaps): closed.**
>   - The argument lists the job builds (`data_argv`, `sft_dev_argv`, `select_argv`) parse with `trackp.main`'s own parser.
>   - The test path runs end to end on CPU. I checked that it evaluates 22 primary test proposals (23 secondary), writes `test_report.json` and the one-read ledger, and that `evaluation_seeds_read` is False.
> - **Minors 2–9: closed.**
>   - The freeze record must contain `approved: true` and the frozen block; `--label-freeze` is passed to the data build.
>   - The receipt's `proposals_sha256` must equal the `sweep1_v3` pin.
>   - Every run is checked by `check_run_protocol`, and the pin file's micro-batch is taken from the runs.
>   - The switch requires and binds `table_pin`, `duplicate_policy`, `split`, `lr_grid`, `host`, `harness_commit` and `h200_sft_probe`, refuses "40.5" as the cap, re-checks the staged partition and receipt against the spec, and records the stage-manifest sha256.
>   - Note draft: check 1 is restated as `parse_note` plus `check_binding`; P4 is PENDING as the author's tick; it points to the v2.1 digest; the cap wording is fixed.
>   - The job docstring's step order is fixed, and the ledger's scope is stated.
> - **Minor 1 (narrowing the freeze reading)** is left as an author question, as the report says. That is acceptable and not a finding.
>
> ## New findings
>
> **1. MAJOR: a job killed at walltime, or one that STOPs early, cannot be sealed, so its GPU-hours are not charged.**
> - Where: `p4_lib.py` `seal` (the SHA256SUMS check), together with `p4_job.sh:9,12,20`.
> - What is wrong: `p4_job.sh` `_precreate` writes an empty `SHA256SUMS` at job start and again on every STOP. `run_job` writes real sums only when it gets to the end.
>   - So after a walltime kill, after a STOP in `p4_job.sh`, or after a `validate_spec` / arm STOP raised before `run_job`'s `try`, the transferred `SHA256SUMS` is a 0-byte file.
>   - `seal` treats any existing file as present, and `sha256sum -c` on an empty file exits 1 ("no properly formatted checksum lines found").
> - Reproduced in scratch: a directory with an empty `job_record.json`, empty `SHA256SUMS`, empty `out.tar` and `p4_run.log` gives `STOP: transferred SHA256SUMS verification failed`.
> - Consequence: the STOP comes before `attempt-N` is created, so `charged_hours` never sees the attempt and the cap is under-counted without any message. A killed 4B job (up to about 10.5 h requested) would not count.
> - Why the test misses it: `test_repeats_are_kept_counted_and_never_chosen` builds the "killed job" with no `SHA256SUMS` file at all, which is not what the job script leaves behind.
> - Fix: treat a missing or 0-byte `SHA256SUMS` as `sums: "absent"` (and an empty `out.tar` as no outputs). Add a test that seals the exact set `_precreate` leaves and checks the attempt is charged at the requested walltime.
>
> **2. MINOR: `assemble` charges nothing if the sealed root is wrong.**
> - Where: `charged_hours` (`root.is_dir()` false gives `[]`) and `assemble`.
> - Probe: `assemble(sealed, spec, sha, wrong_root)` passes with `gpu_hours_consumed: 0`. `assemble` never checks that the sealed directories it is given lie under `sealed_root/<run_id>/<arm>/attempt-N`.
> - Fix: require that layout for every given directory, and STOP when `charged_hours` does not list each of them.
>
> **3. MINOR: `check_cap` only counts sealed attempts.**
> - Where: `p4_switch.check_cap` and `submit`.
> - What is wrong: a job submitted from another stage that has not finished or been sealed is not counted. `submit` also does not refuse an arm that already has a sealed STOP-free attempt, so that job would only be rejected later by `assemble`, after spending GPU-hours.
> - Fix: count unsealed entries in `P4_SUBMISSIONS.jsonl` at their requested walltime (or require every earlier submission to be sealed), and refuse an arm that already has a STOP-free attempt.
>
> **4. MINOR: an empty probe citation passes and makes the note binding meaningless.**
> - Where: `validate_spec` (line 256) and `check_binding`'s `h200_sft_probe` check.
> - What is wrong: `estimate.source = "h200_sft_probe:"` with nothing after it passes at launch strength. The note check then looks for an empty string, which every note contains.
> - Fix: require a record path after the prefix, for example `docs/r1/reports/…\.md`.
>
> **5. MINOR: `check_run_protocol` does not check for a protocol deviation.**
> - What is wrong: it does not assert `protocol_deviation is None`. The selection step refuses a deviating grid run, but nothing does so for the learning-curve runs.
> - Fix: add the assertion, and optionally `data_sha256` equal to the data directory's.
>
> **6. MINOR (test nit).**
> - Where: `test_the_test_path_runs_replay_predict_and_report_on_cpu`.
> - What is wrong: `out["evaluation_seeds_read"] in ("none", [], None, 0)` passes on `False` only because `False == 0` in Python.
> - Fix: assert `is False` and `test_n > 0`.
>
> **7. MINOR (record keeping).** The Revision 2 section cites `reviews/TRACKP_P4_RUNNER_REVIEW_20261122.md`, which is not on the branch. Commit the round-1 and round-2 texts with the unit.
>
> ## Also checked, no problem found
>
> - `check_run_protocol` against the real `trackp_sft.json`: all ten keys exist in `train`, and the report's protocol (`{**DEFAULT_PROTOCOL, **train minus comment, micro_batch from host}`) matches it.
> - `trackp_p4_test_path.run`: the default `_real_build` (lease plus `trackp._build`) is a proper context manager, and the in-job call `T.main(sys.argv[1:])` still works.
> - The new switch bindings match the note draft's lines; the note draft still reads `approved: false`.
> - The new receipt and freeze checks fail closed.
> - The diff touches only the unit's own files.

## Round 3 (`66fb8659`)

> Reviewed base: 66fb86590dfef134efb31ca3ce37d41d4b188035 (mac-trackp-p4-runner-20261122, parent 7809d8e8)
>
> # Track P P.4 runner unit — review round 3
>
> **Verdict: ACCEPTED.** All seven round-2 findings are closed. The three findings below are minor; they do not block acceptance and can be fixed before the launch commit.
>
> Targeted tests (test_trackp_p4_runner, test_trackp_sft, test_trackp_sft_test_eval, test_trackp_p3): 180 passed. The worktree is clean at 66fb8659. My scratch is in /tmp/rev_p4run/_to_delete/ (r3_scratch, r3_t).
>
> ## Round-2 findings
>
> 1. **Major — killed or early-STOP jobs could not be sealed: closed.**
>    - `seal` now treats a missing or 0-byte `SHA256SUMS` as absent. A non-empty one must still verify (tested).
>    - Scratch reproduction with the real files `p4_job.sh` pre-creates (empty `job_record.json` and `SHA256SUMS`, a valid empty tar, a log): the attempt seals as `sums: absent`, `record_readable: false`, charged at the requested walltime (10.46 h for kev-4b), with stop "STOP: no readable job record". Round 2 refused exactly this set.
> 2. **Wrong sealed root counted nothing: closed.**
>    - `assemble` computes `charged_hours` first. It then requires every attempt it is given to resolve to `<sealed_root>/<run_id>/<arm>/attempt-N` and to appear in that count.
>    - A wrong root is refused (tested). A symlinked sealed root still works, because both sides are resolved (scratch).
> 3. **Unsealed or repeat submissions not charged: closed.**
>    - The switch now appends every submission to `<sealed_root>/<run_id>/_submissions.jsonl`.
>    - `pending_submissions` charges each arm's submissions minus its sealed attempts at the requested walltime. `charged_hours` now skips files among the arm directories, so the ledger file is not mistaken for an arm.
>    - `check_cap` refuses an arm that already has a sealed STOP-free attempt.
>    - Scratch flow: one ledger entry gives one pending charge, which goes to zero after its seal. After four real `run_job` records are sealed from four `…/execute/dir_N` directories, `assemble` passes, charging the killed attempt plus the four actual runs (10.4649 GPU-h, 5 attempts). An extra unsealed submission adds its walltime to the total.
> 4. **Empty probe citation passed launch: closed.** At launch, `estimate.source` must fully match `h200_sft_probe: docs/r1/reports/\S+\.md`, so the switch's `h200_sft_probe` check can no longer be satisfied by an empty string. A bare `h200_sft_probe:` is refused (tested).
> 5. **Protocol deviation and data directory not checked per run: closed.**
>    - `check_run_protocol` refuses any non-null `protocol_deviation` and a `data_sha256` other than the one passed in.
>    - `run_job` passes the data directory's `sft_data.json` sha256 for the grid runs and the subset's for the learning-curve runs.
>    - The job's own argument lists never pass `--steps` or `--eval-every`, so real runs record `protocol_deviation: None`. The 2-step run in the test path is, correctly, not checked.
>    - The end-to-end job test still passes through these checks.
> 6. **Loose test assertion: closed.** It now asserts `evaluation_seeds_read is False` and `test_n > 0`.
> 7. **Review record missing: closed.** `docs/r1/reviews/TRACKP_P4_RUNNER_REVIEW_20261122.md` is committed with rounds 1–2 (marked in progress); this round needs adding.
>
> ## New findings (all MINOR)
>
> 1. **An arm can be submitted twice while its first job is still running.** `p4_switch.check_cap` refuses an arm that has a sealed STOP-free attempt, but not one that only has a pending (submitted, unsealed) submission, possibly from another stage.
>    - The duplicate is charged, and `assemble` would later refuse two STOP-free attempts, so this fails closed. But it can waste up to one walltime of GPU hours.
>    - Fix: also refuse arms whose pending count in `pending_submissions` is above zero.
> 2. **A crash after `condor_submit` can lose a charge.** `p4_switch.submit` writes the run-ledger entry after `condor_submit` succeeds. If the switch crashes in between, a running job is not charged.
>    - Fix: write the ledger entry, marked as intended, before `condor_submit` (charging a failed submit is the conservative side), or keep the per-stage marker and cross-check it.
> 3. **The probe record is checked by name only.** Nothing checks that the cited `docs/r1/reports/<record>.md` exists on `origin/main`.
>    - Fix (optional): `git cat-file -e origin/main:<path>` in `check_binding`.
>
> ## Nothing new broke
>
> - **`seal` on real records:** still sealed as verified with charge basis `job_record.gpu_hours`.
> - **`assemble`:** the two-job-directory comparison, refusal of a second STOP-free attempt, refusal of unverified attempts, and the cap check all still pass.
> - **Switch:** the round-2 bindings (table_pin, duplicate_policy, split, lr_grid, host, harness_commit, h200_sft_probe, cap "40.5", staged partition and receipt, stage-manifest sha256) are unchanged.
> - **Test path:** `trackp_p4_test_path.run` is unchanged and still passes on CPU.
> - **Note draft:** still reads `approved: false`.
> - **Freeze reading:** narrowing it (round-1 minor 1) remains an open author question, as documented.

## Round 4 (`c6ad7e25`)

> Reviewed base: c6ad7e25ce5251af2874d45d41b15e00467cfb05 (mac-trackp-p4-runner-20261122, parent 66fb8659)
>
> **Verdict: CONFIRMED.** All three round-3 minors are fixed and nothing regressed.
>
> The diff since 66fb8659 changes only `p4_switch.py`, the runner tests and a new "Post-acceptance fixes" section in the report. The four targeted test files pass (180 passed: test_trackp_p4_runner, test_trackp_sft, test_trackp_sft_test_eval, test_trackp_p3). The worktree is clean and still at c6ad7e25. My scratch is in /tmp/rev_p4run/_to_delete/ (c_scratch, c_t).
>
> **1. One running job per arm: fixed.**
> - `check_cap` now refuses any requested arm that has a submitted but unsealed entry in the run ledger ("not sealed yet").
> - This check comes after the existing refusal for an arm that already has a sealed STOP-free attempt, and before the cap sum.
> - The double-submit test now expects the ledger refusal. It still checks the stage's once-only marker separately, using another sealed root.
>
> **2. Ledger entry before `condor_submit`: fixed.**
> - The run-ledger line (`arm`, `stage`, `intended_utc`) is written after the per-stage marker and before `condor_submit`. The old write after the submit is gone.
> - I checked the ordering in scratch with a failing `condor_submit`:
>   - the ledger file already existed when `condor_submit` was called;
>   - afterwards the arm was pending, charged at its requested walltime (1.745 GPU-h for kev-0.8b);
>   - the stage's `P4_SUBMISSIONS.jsonl` was not written, as intended.
> - Recovery works: sealing an empty directory for that arm charges it 1.745 h and clears the pending entry.
>
> **3. Probe record must be on main: fixed.**
> - `check()` takes the record path from `estimate.source` (the same value the note must contain) and verifies it with `git cat-file -e origin/main:<path>`. It runs after `check_binding` and is also used by `submit`.
> - Run against the real repository, `_blob_on_main` returns True for `docs/r1/PLAN.md` and False for a missing record.
> - Tests cover a record that is not on main.
>
> **Two non-blocking notes**
> - A failed `condor_submit` is charged a full walltime, and its arm stays blocked until someone seals an empty directory for it. This is the conservative choice I suggested and recovery works, but the operator runbook or report should say how to recover.
> - The new test for fix 2 only checks that `intended_utc` is present, not the ordering. The failing-submit check above shows the ordering is right; adding it as a test would pin it.

## Round 5 (`7a40746c`)

> Reviewed base: 7a40746c00f404e737041f43e75618b479482673 (parent c6ad7e25)
>
> **Verdict: CONFIRMED.**
>
> The diff since c6ad7e25 changes only the test file and the report; no code under `r1/scripts` or `r1/c3` changed. The four targeted test files pass (180 passed: test_trackp_p4_runner, test_trackp_sft, test_trackp_sft_test_eval, test_trackp_p3). The worktree is clean at 7a40746c. My scratch is in /tmp/rev_p4run/_to_delete/f_t.
>
> **Test change.** The fake `condor_submit` now fails unless the run ledger under `tmp_path/"sealed"` already holds that arm, so the ledger-before-submit order is pinned.
> - Every call that reaches `condor_submit` uses that sealed root.
> - The one call that uses `other_root` stops earlier, at the stage's once-only marker, before the ledger write and before `condor_submit`. The assertion therefore never sees the wrong ledger.
>
> **Recovery paragraph.** It matches `p4_lib.seal`, `charged_hours`/`pending_submissions` and `p4_switch.check_cap`:
> - **"Charged its requested walltime and refused as 'not sealed yet'".** `pending_submissions` charges every ledger entry with no sealed attempt at `arm_walltime_s`. `check_cap` refuses an arm that has such an entry.
> - **"Seal an empty attempt directory … keeps the walltime charge, clears the pending entry and records the failure".** For an empty directory, `seal` finds no readable record and treats `SHA256SUMS` as absent. It creates `attempt-N` with `charged_gpu_hours` equal to the requested walltime and `stop` "STOP: no readable job record". The arm then has as many sealed attempts as submissions, so it is no longer pending. I ran this in the previous round: 1.745 GPU-h charged for kev-0.8b and the pending list empty afterwards.
> - **"Submitted again from a new stage".** This is required, because the failed stage keeps its once-only marker. After sealing, `check_cap` lets the arm through: its sealed attempt is a STOP, so it does not count as done, and nothing is pending.
> - **"If a job does exist, let it finish and seal it normally".** Sealing that job's output uses up the pending entry the same way.
>
> One edge case, which errs on the safe side: if an operator seals an empty attempt and a job of that arm later turns up and is sealed too, both attempts are charged. That over-counts, never under-counts, and the paragraph's `condor_q`/`condor_history` check is meant to prevent it.

---

Code-Commit: 7a40746c00f404e737041f43e75618b479482673
Verdict: ACCEPTED

Accepted: the P.4 phase-1 runner unit at `66fb8659`, with the round-3 minors fixed and confirmed at `c6ad7e25` and the confirmation notes taken and confirmed at `7a40746c`; the phase-1 note draft stays `approved: false`.
