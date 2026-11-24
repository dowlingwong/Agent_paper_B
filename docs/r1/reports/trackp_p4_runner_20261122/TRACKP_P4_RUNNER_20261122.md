# Track P P.4 phase 1: the runner unit (P3 of the draft) and the phase-1 note draft

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, on `mac-trackp-p4-runner-20261122` over published
`main` `9c2979a2`, for item 3 of the queue of 22 Nov 2026 (01:22). This is desk work: synthetic data only, no GPU, no
image, no label file of a real audit, no network.

## Authority

- The P.4 phase-1 authorization draft, revision 4.2 on `main` (`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`).
  This unit is its §7 P3: "the P.4 runner unit, independently reviewed at the launch commit: the split config
  `split_file` bound to the signed P3 split file, `LabelBlockSource` on the receipted train/dev partition only, with
  the job pinning the note's `labels:` sha256, its `label_receipt:` sha256 … and the receipt's source block …, the
  job's clone full with `origin/main` fetched (P4-JOB), the learning-curve sampler of P4-LC, the bootstrap interval of
  §3, the test evaluator wired in with a ledger path per table, the per-arm pin file, and the HTCondor job of P4-JOB:
  spec, job script, JDL render, the identity checks and STOPs of §4, sealing with receipts, and a switch with two keys
  and the S2-C5 launch binding (as the G.1b H200 job)".
- R1-TRACKP-P4-DECISIONS: every decision as recommended.
- **R1-TRACKP-V21-FREEZE** (new on `main`): "the env3 `pip freeze` in image v2.1 may differ from R1-ENV-PIN's freeze
  (`pip_freeze_trackp-gpu.txt`) only in the `causal_conv1d` line, at the same version number … The difference is
  recorded in the P.4 job record and disclosed in the P.4 report. Any other difference in the freeze is a STOP."
- R1-T1-HOST-TASL (H200), R1-TRACKP-IMAGE-V21, R1-HTC-QTORCH, R1-S2-LABELS-TRAINDEV-RELEASE, R1-TRACKP-SFT-DEV,
  R1-SWEEP2-PREREG (PRE-SPLIT A).

## What changed

**`r1/c3/train/p4_phase1.py` (new).** The pieces around the SFT pipeline; the module docstring has the rules.
- **`check_env3_freeze`** (R1-TRACKP-V21-FREEZE). The sorted line sets must be equal, with one exception: one
  `causal_conv1d` line may differ, one line for one line, at the pinned public version 1.7.0. It returns
  `identical`, or `causal_conv1d_only` with both lines verbatim, for the job record.
  - **Reading of "the same version number":** the same PEP 440 public version. A local label (`1.7.0+cu12torch2.6…`,
    the form of the prebuilt wheels) and a direct reference to a wheel file of that version are admitted and recorded.
  - Every other difference is a STOP: another package line, another version, a removed or added causal line, an
    unreadable version, a duplicate line.
  - The author can narrow this reading if the local label should count as a different version (see "For the author").
- **`check_partition`.** The note's `labels:` and `label_receipt:` sha256 must match. The receipt must be the sweep-1
  train/dev release, its source block (`inputs.label_block_sha256`) must be the frozen `cdae9c3f…9aca`, and its
  outputs must bind this partition. `LabelBlockSource` (`release.open_partition`) still re-checks every receipt
  binding when the data is built.
- **`lc_points` / `lc_subset`** (P4-LC A). The points below the training-set size are kept, plus `full`, which is the
  selected-lr grid runs. A subset is a derived data directory:
  - n training rows (rule no-ops included), drawn without replacement by seed `20261122 + n`;
  - every val and val_seen row, and `splits.json` unchanged;
  - an `lc_subset` record binding the parent's `sft_data.json` sha256.

  It loads with `load_sft_data`. A subset of a subset is refused.
- **`rps_skill_bootstrap`** (§3). The instance-cluster bootstrap on **primary** val: 2,000 resamples, seed 20261108,
  instances resampled with replacement as row weights. It gives the seed-mean RPS skill of the selected-lr runs,
  raw and at each run's fitted temperature, with a 95 % percentile interval. It is readiness only; no gate decision
  is taken.
- **`arm_pin`.** The per-arm pin file records:
  - the base and adapter revisions and the staged weight sha256;
  - the data directory's sha256, the micro-batch and the host config sha256;
  - the selected lr and the mean best val RPS;
  - for every grid and learning-curve run: lr, seed, best value, data sha256, and the sha256 of its best record and
    temperature.

**`r1/scripts/htcondor/trackp_p4/` (new): the HTCondor job of P4-JOB A**, modelled on the G.1b H200 job.

- **`p4_lib.py`.** Spec validation (`trackp_p4_job/v1`, fail-closed; launch strength refuses every placeholder):
  - image v2.1 by digest (v2 is refused) with its `VERSIONS.txt` sha256, row R1-TRACKP-IMAGE-V21;
  - the H200;
  - env3 with R1-ENV-PIN's freeze (sha256 `50238e5a…`) under R1-TRACKP-V21-FREEZE;
  - the host and SFT config sha256;
  - the signed P3 split file and the `sweep1_v3` table with its index and classification;
  - the receipted sweep-1 train/dev partition, its receipt, the frozen block and the signed freeze record;
  - the arms (both controls always);
  - the fixed protocol: lr grid, seeds, LC points and seed, micro-batch 8, effective batch 16, the decided policy,
    no real-label test read, the bootstrap;
  - the caps (40 GPU-h, 64 slot-hours) against the projection. Per arm, that is training hours × 1.5 + 30 min of
    startup, each job ≤ 86,400 s. At launch the estimate must cite the H200 SFT probe.

  The job (`run_job`), one per arm:
  1. identity (VERSIONS.txt, exactly one H200, non-root);
  2. a full clone at the paper commit, with `origin/main` fetched; not shallow, on main, clean;
  3. the env3 freeze: `uv pip freeze` (env3 is a uv venv without pip) against the clone's committed freeze
     (`check_env3_freeze`; the record goes into the job record);
  4. the configs (both sha256; `trackp.py --check-config` clean);
  5. the transferred inputs (table pins; partition, receipt and source block; the freeze record in the clone);
  6. staging, the one network step: the arm's registry weights by size and sha256 from the clone's `registry.yaml`,
     the pool tokenizers into the job's `HF_HOME`, and the config's local paths naming the staged directories;
  7. offline from here (`HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE`): `trackp.py sft-data` on the partition, with the
     signed freeze record (`--label-freeze`); the data's path-free identity (`data_identity`) is recorded;
  8. the 9-run grid (`sft-dev`), `sft-select`, and the learning curve at the selected lr; every run's
     `sft_report.json` protocol is checked against the fixed one (`check_run_protocol`);
  9. the bootstrap;
  10. the pin file;
  11. the synthetic test path;
  12. `out.tar`, `job_record.json` and `SHA256SUMS`, written for a STOP too.

  STOP classes: `infrastructure`, `protocol` (a refusal of the pipeline: `trackp.py` printed `STOP:`), and `arm` (a
  CUDA OOM at micro-batch 8, the author's decision); a missing script or an argument error is `infrastructure`.
  `seal` makes a new `attempt-N` for every job (STOP-free, STOP, without the H200/image identity, or with an empty
  record after a walltime kill), never overwriting and never resuming, and its receipt charges the attempt's GPU-hours
  (the record's, else the requested walltime). `assemble` needs one sealed, verified, STOP-free attempt per arm and no
  other STOP-free attempt of that arm; the same spec, paper commit, image, configs, labels (without the job-local
  partition path), env3 status, run protocol and data identity in all four (`comparable`); and the GPU-hours charged
  by every attempt of the run within the cap (`charged_hours`). The launch binding
  `verify_launch_p4` works as `g1b_tasl.verify_launch_tasl` (the TASL binding the G.1b and G.4 notes use; the S2-C5
  binding cannot be met by a note on main that names the launch commit).
- **`p4_job.sh`**: pre-creates the transferred outputs, then runs the library with the image's env3 Python.
- **`p4_render_jdl.py`**: stages the job files, the spec and the transferred inputs (table files checked against the SFT
  config's pins; partition and receipt against the spec), and one JDL per arm. The JDL has image v2.1, one GPU, the
  H200 requirement, `+RequestWalltime` per arm, no resume, and no ProvidesEtpCeph or GPU share. `--preview` stages are
  not submittable.
- **`p4_switch.py`**: `check` binds the author-signed note `docs/r1/authorizations/trackp_p4_<date>.md` (on main;
  approved; phase 1; P1–P8 PASS with citations; the §8 key lines against the staged spec; no `<…>`) to the stage
  (manifest and canonical render). `submit` adds both keys (`--enable`, `TRACKP_P4_ENABLE_REAL=1`), the committed spec,
  the launch binding with `p4_lib.PLAN_ROWS`, a once-only marker, and `condor_submit`. The first arm (`kev-0.8b`) goes
  alone; the others need its sealed, STOP-free record (`check_first_record`).
- **`p4_spec.json`** (run `trackp-p4-p1-20261122-a`). Its TODO fields are those the cluster or the author fills: the
  paper commit, the image v2.1 digest and VERSIONS sha256, the host config sha256 after its fill, the partition,
  receipt and freeze record, and the probe-based estimate. Until then the estimate is the draft's 8× case: 0.83 h
  of training for a 0.8B base, 6.64 h for a 4B base. That projects 16.94 GPU-h and 24.41 slot-hours against 40 and
  64.

**`r1/scripts/trackp_p4_test_path.py` (new): the evaluator's synthetic path** inside the job (P4-PHASE1-TEST A). On a
synthetic-label build of the same table and a 2-step `sft-dev` on it, it runs:
- `replay_test_prompts`;
- `predict_test`, loading the run's best model through `trackp.py`'s builder under the GPU lease;
- `evaluate_test`, with the one-read ledger `<out>/ledgers/sweep1_v3/trackp_p4_test_reads.jsonl`, one per table.

A data directory with real labels is refused before anything is read.

**`docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md` (new): the phase-1 note** (approved: false). It is
filled with every value known now:
- the run id, source block, table pins, policy, split and split file, arms, lr grid, LC, readiness;
- the host, micro-batch, env3 freeze rule, job layout, the reads (none), and the caps;
- P4 (not applicable, an author tick), P6 and P8 PASS.

Still open:
- the image, VERSIONS and smoke/E0/probe fields, which need the cluster's v2.1 results;
- the host config sha256;
- the labels, receipt and freeze record (P1);
- P2 (P.3a records), P3 (this review), P5 and P7;
- the spec sha256 and the code commit.

A test fills only these open fields and checks that `p4_switch` accepts the note against a filled spec.

## Tests

`r1/tests/test_trackp_p4_runner.py`, 65 tests:
- **R1-TRACKP-V21-FREEZE:** the pinned freeze is R1-ENV-PIN's. Admitted: identical; a local label; an underscore
  spelling; a file wheel or a URL wheel of 1.7.0. STOPs: 1.7.1, 1.7.0.post1, a wheel of 1.6.0, an unreadable
  reference, a removed line, an added causal line, another package changed (torch), an extra package, a duplicate line.
- **The partition:** both pins, the source block, the source and stage, a symlink.
- **The data:** LC points; an LC subset that loads with `load_sft_data` (same held-out rows, fixed seed, other seed,
  refusals); a bootstrap on three real Stage S runs of the CPU stand-in (interval, seed mean equal to the reports',
  determinism, another data directory refused); the pin file.
- **The spec:** the shipped spec validates and refuses launch until filled (four TODOs); 23 refusals.
- **The host steps:**
  - the GPU and the image identity;
  - the env3 step recording the V21 difference and refusing others;
  - the clone (shallow, not on main, dirty refused);
  - the configs (sha256, check-config);
  - the inputs (layout, table pin, freeze record);
  - staging (sizes and sha256, tampering, local paths);
  - the trackp error classes (OOM → arm, refusal → protocol, crash → infrastructure).
- **The job end to end**, with the host steps faked and `trackp.py` replaced by the real data builder and the real Stage
  S loop on the CPU stand-in: the 9 grid runs, the selection, the LC point at the selected lr, the bootstrap, the pin
  file, the sums, the seal and a second attempt. An OOM mid-grid records `stop_class: arm` and still writes the sums.
- **Assembly:** every arm; one data directory; the cap; STOP-free attempts.
- **The JDL render and stage:** inputs, refusals, preview.
- **The switch:** the note bound to the stage, with 12 field refusals; submission with both keys, the binding rows,
  the first-arm gate, the once-only marker and the committed spec; the first-record gate.
- **The launch binding** on a scratch repository: rows, repository, untracked code, code after the paper commit,
  unpublished HEAD.
- **The note draft:** placeholders refused now, and the completed copy accepted.
- **The test path:** refuses real labels, and runs replay, prediction and the report with its ledger on CPU (hash-bag
  stand-in, synthetic labels as `sft-data --labels synthetic` writes them). Plus the job script's syntax.

Existing tests: `test_trackp_sft`, `test_trackp_sft_test_eval` and `test_trackp_p3`, together with the new file, give
180 passed.

## Revision 2 (review round 1, `reviews/TRACKP_P4_RUNNER_REVIEW_20261122.md`)

- **B1:** `trackp.py` is called by its absolute path in the clone (the job directory stays the working directory);
  only a `STOP:` refusal is a protocol STOP. Test: the real `_sh` from a job directory reaches the clone's script, and
  a clone without it is an infrastructure STOP.
- **B2:** the freeze step runs `/opt/uv/uv pip freeze --python /opt/r1/envs/trackp/bin/python`; `image_identity`
  requires `/opt/uv/uv`. Test: the exact argument list.
- **B3:** `assemble` compares path-free values (`comparable`): the data identity (the `sft_data.json` manifest with
  every `path` removed, hashed), and the label record without the job-local partition path. Test: two jobs in two
  directories (one under `/var/lib/condor/execute/dir_42`) give different `sft_data.json` sha256 and equal comparable
  records.
- **M1:** the pin file (schema `/v2`) binds `stage_s/best.json`, the checkpoint manifest (`best/manifest.json`;
  `record.json` for the CPU stand-in), the whole `best/` tree, `temperature.json` and `sft_report.json`, and STOPs
  when any is missing. Test: a `manifest.json`-style checkpoint, a weight change moving the tree sha256, each missing
  file refused.
- **M2:** every attempt is sealed and charged (`seal`, `charged_hours`); `assemble` sums all attempts and refuses a
  second STOP-free attempt of an arm; the switch refuses a submission whose charged plus projected hours pass the cap
  (`check_cap`). Tests: a late STOP repeat counted, a killed job's empty record sealed at its walltime, an identity
  STOP sealed unverified, an unreceipted attempt directory refused, the switch blocked by charged hours.
- **M3:** the job's `trackp.py` argument lists (`data_argv`, `sft_dev_argv`, `select_argv`) parse with the real CLI;
  the test path's happy path runs on CPU (`trackp_p4_test_path.run` takes injectable replay inputs, tokenizers and
  builder).
- **Minors:** the freeze record must read `approved: true` and name the frozen block; `--label-freeze` passed to the
  data build; the receipt's `inputs.proposals_sha256` must be the `sweep1_v3` pin; every run's protocol checked and
  the pin file's micro-batch taken from the runs; the switch requires and binds `table_pin`, `duplicate_policy`,
  `split`, `lr_grid`, `host`, `harness_commit` and ties `h200_sft_probe` to the spec's `estimate.source`, refuses
  "40.5" as the cap, re-checks the staged partition and receipt against the spec and records the stage manifest's
  sha256; the note draft's check 1, P4 (the author's tick, PENDING), the v2.1 digest pointer and the cap wording; the
  job docstring's order; the test-read ledger's scope stated. Minor 1 (narrowing the freeze reading) is left as the
  author's question below.

## Revision 3 (review round 2)

- **1 (major):** `seal` treats a missing or empty `SHA256SUMS` as absent, so the empty files `p4_job.sh` pre-creates
  (a walltime kill, an early STOP) are sealed and charged at the requested walltime; non-empty sums must still verify.
  Test: the exact pre-created set.
- **2:** `assemble` requires every given attempt to lie in `<sealed_root>/<run_id>/<arm>/attempt-N` and to be listed by
  `charged_hours`; a wrong sealed root is refused.
- **3:** the switch appends every submission to a run ledger `<sealed_root>/<run_id>/_submissions.jsonl`;
  `charged_hours` charges submissions not yet sealed at their requested walltime (across stages), and `check_cap`
  refuses an arm that already has a sealed STOP-free attempt.
- **4:** `estimate.source` must be `h200_sft_probe: docs/r1/reports/<record>.md` at launch.
- **5:** `check_run_protocol` refuses a run with a protocol deviation and one trained on another data directory.
- **6, 7:** the test asserts `evaluation_seeds_read is False` and a non-empty test population; the review record (rounds
  so far) is committed with the unit.

## Post-acceptance fixes (round 3 minors)

Round 3 accepted `66fb8659` with three minor findings; all three are fixed in `p4_switch.py`:

1. **One running job per arm.** `check_cap` now also refuses an arm that has a pending submission in the run
   ledger (submitted, not sealed). Before, an arm could be submitted twice from two stages while its first job
   was still running.
2. **Ledger before submit.** The run-ledger entry (`<sealed_root>/<run_id>/_submissions.jsonl`, field
   `intended_utc`) is written before `condor_submit`, so a crash between the two still charges the cap at the
   requested walltime. The stage's own `P4_SUBMISSIONS.jsonl` is still written after a successful submit.
3. **Probe record on main.** `check` verifies that the H200 SFT probe record named in `estimate.source` exists
   on `origin/main` (`git cat-file -e`), not only its name.

Tests: `test_trackp_p4_runner.py` covers all three (the fake `condor_submit` asserts that the run ledger already
holds the arm when it is called); 180 pass together with the sft, sft_test_eval and p3 tests.

**Recovery after a failed `condor_submit`** (operator runbook). A failed or crashed submit leaves the arm in the run
ledger without a sealed attempt: it is charged its requested walltime and refused as "not sealed yet". After checking
with `condor_q`/`condor_history` that no job of that arm exists, the operator seals an empty attempt directory for it
(`p4_lib.seal`; an empty or missing `SHA256SUMS` counts as absent), which keeps the walltime charge, clears the pending
entry and records the failure; the arm is then submitted again from a new stage. If a job does exist, it is left to
finish and sealed normally.

## For the author

- **"The same version number"** (R1-TRACKP-V21-FREEZE): the code admits the same public version 1.7.0, with or without
  a local label (a prebuilt wheel's `+cu12torch2.6…`). If the author reads the row as forbidding a local label, the one
  regex in `_causal_version` changes, before any training job.
- **Staging** is the one network step of the job: weights by curl with size and sha256 checks, as the staged E0 job
  does; tokenizers through the hub into the job's `HF_HOME`. Data building and training run offline, which is the
  draft's "network access to the Hugging Face hub (offline mode)" STOP applied after staging. If the author wants the
  tokenizers staged by curl as well, that is a small change.
- **The first arm**, `kev-0.8b`, goes alone. It is a runner choice: the smallest job that stages an adapter and a
  base.

## Needs a cluster test

All on NEMO2 H200, now with image v2.2 (written for v2.1; see "On main `76a3c71f`, image v2.2" below):
- the env3 `uv pip freeze` line format in the image (the v2.2 build record says the sorted freeze is identical to the
  pin);
- the host config's local paths relative to the job directory;
- staging speed and the transfer of a 4B base;
- the synthetic test path with a real base;
- the output transfer and seal of `out.tar`.

These also fall within the draft's §10 and the SFT probe.

## On main `76a3c71f`, image v2.2 (24 Nov 2026)

Prepared by the Mac-desk agent (Claude), AI-assisted, 24 Nov 2026. Desk work only: no GPU, no image pull, no server
access, no label or evaluation file read.

**Basis.** After `git fetch origin`, `origin/main` is still `76a3c71f` (`76a3c71fe94082e0c1274a1200c7e103a06b90bf`).
The branch was brought onto it with a merge commit (`git merge --no-ff origin/main`, `4e26995a`). There were no
conflicts: the runner branch only adds files, so every shared file is main's.

At the time of writing:
- the image v2.2 cluster report (`docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md`) and its review
  (`docs/r1/reviews/TRACKP_V22_IMAGE_REVIEW_20261124.md`) are **not on `main`**. They are only on the remote branch
  `origin/trackp-v22-image-20261124` @ `a20bd02e`, which contains `76a3c71f`;
- the PLAN row **R1-TRACKP-P4-RUNNER-DECISIONS is on no ref** (`git log --all -S` finds nothing).

This update cites the v2.2 records by their paths on that branch. It does not copy them into this branch.

### What changed

- **Image fields** (from the v2.2 report):

  | where | value |
  |---|---|
  | `p4_spec.json` `image.digest` | `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` |
  | `p4_spec.json` `image.row` / `tag` / `build_record` | `R1-TRACKP-IMAGE-V22-B` / `20261124-v2.2-667bb9c2` / the v2.2 report path |
  | host config `r1/scripts/configs/trackp_htcondor_v2.json` `image` | gpu `sha256:49dd9900…`, cpu `sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8`, tag `20261124-v2.2-667bb9c2`; `host` "HTCondor GPU (image v2.2)"; the comment names v2.2 |
  | note draft `image:` | the v2.2 gpu digest, tag, row and report |

  The host config's sha256 goes from `d53681c9…` to
  **`18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140`** (the spec's TODO comment says so). Its
  `TODO_VERIFY_ON_HOST` values are unchanged, including `venv.causal_conv1d`. The host config is the file `p4_lib`
  pins as `HOST_CONFIG`; no code reads its `image` or `host` fields. I set `image.cpu` and `image.tag` together with
  `image.gpu` because the three describe one build. The task named only the gpu digest, so the reviewer may want to
  confirm the cpu field.
- **`VERSIONS.txt` sha256: left `TODO_VERIFY_ON_HOST`.** It is not in the v2.2 report, its review, or anywhere on
  the v2.2 branch. That branch adds only the report and the review; no raw capture of 759993/759994/759997/760000 is
  committed. It cannot be derived either, because image VERSIONS has a `build_utc` line. The spec holds
  `TODO_VERIFY_ON_HOST: …` and the note draft holds `<FILL: … TODO_VERIFY_ON_HOST …>`. Both are refused at launch
  strength.
- **`p4_lib.py`:**
  - image v2 **and v2.1** (`sha256:31478d99…`, whose prebuilt causal_conv1d failed to import in smoke 759983) are
    refused as the P.4 image;
  - `image.row` must be `R1-TRACKP-IMAGE-V22-B` (`IMAGE_ROW`);
  - `PLAN_ROWS` adds R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B, beside R1-TRACKP-IMAGE-V21 and
    R1-TRACKP-V21-FREEZE. All ten rows are on `76a3c71f`; a test checks this against this checkout's `PLAN.md`.
  - `verify_launch_p4` checks the rows against `origin/main:docs/r1/PLAN.md` at launch (unchanged);
  - the VERSIONS message and docstrings say v2.2.
- **`p4_switch.py`:** P5 must cite all three rows: R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and
  R1-TRACKP-IMAGE-V22-B. A row id is matched as a whole id (`_cites`), so citing `R1-TRACKP-IMAGE-V22-B` alone does
  not count as citing `R1-TRACKP-IMAGE-V22`. Other citations (the label-freeze file prefix, `docs/r1/reviews/`,
  `--check-config`) are still substrings.
- **`p4_render_jdl.py`, `p4_job.sh`:** the header comments say image v2.2. The JDL's `container_image` comes from the
  spec digest, so it did not change.
- **Note draft** (still `approved: false`, still unsigned):
  - `image:` is filled;
  - `h200_smoke_e0:` names the v2.2 report and jobs, and keeps `<FILL: the main commit carrying it and the review of
    these run records>`;
  - P5 is PENDING, cites the three rows, and gives the v2.2 records: report, review (round 2 ACCEPTED at `3c54a0e8`),
    Actions run 45290856704, tag, gpu and cpu digests, build-log sha256
    `fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312`, I2 759993 PASS, I3 759994 PASS, smoke 759997
    PASS (kernels_bound), E0 760000 equivalent;
  - P7 names the v2.2 image fields;
  - `env3_freeze:` has a `<FILL: the reading of R1-TRACKP-P4-RUNNER-DECISIONS (1) once on main>`, so the note cannot
    be signed before that reading is written in.
- `r1/c3/train/p4_phase1.py` is **unchanged** (see the env3 check below).

### env3 check — PENDING R1-TRACKP-P4-RUNNER-DECISIONS (1)

The row is not available, so nothing in the check was changed.

**What the rows say.**
- R1-TRACKP-V21-FREEZE: env3's freeze "may differ … only in the `causal_conv1d` line, at the same version number (the
  prebuilt wheel in place of the source build) … Any other difference in the freeze is a STOP".
- R1-TRACKP-IMAGE-V22: "R1-TRACKP-V21-FREEZE applies unchanged (only the causal_conv1d line may differ, at the same
  version number)".
- R1-TRACKP-IMAGE-V22-B: "R1-TRACKP-V21-FREEZE unchanged (only the causal_conv1d line may differ, at 1.7.0)".

**What the v2.2 records say.**
- causal-conv1d 1.7.0 is built from the pinned sdist with `CAUSAL_CONV1D_FORCE_BUILD=TRUE`, and the built wheel is
  installed **by name**. The freeze line therefore stays `causal-conv1d==1.7.0`, with no `direct_url.json`, and the
  sorted freeze diff is empty: VERSIONS has `env3_sorted_diff=empty`.
- The image build itself compares the full `uv pip freeze | sort` with the sorted committed freeze, byte for byte, in
  both the build stage and the gpu stage. That freeze has sha256 `50238e5a…`, the same file as R1-ENV-PIN's
  `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`. The build fails on any difference.
- One sentence in the report, "R1-TRACKP-V21-FREEZE holds: only the `causal_conv1d` line differs, same 1.7.0", repeats
  a Dockerfile comment. The v2.2 review flags that comment as stale (residual minor): the line is identical, and that
  is what lets the strict diff pass. I read the record as **identical**.

**What the check does now** (`p4_phase1.check_env3_freeze`, called from `p4_lib.env3_freeze` on
`/opt/uv/uv pip freeze --python /opt/r1/envs/trackp/bin/python` against the clone's freeze, sha256-pinned):
1. Blank lines are dropped, lines are stripped and sorted, and a duplicate line is a STOP.
2. Equal line sets give `status: identical`.
3. Otherwise every differing line must be a `causal-conv1d` line (name normalised), one line for one line. Its
   version must be the pinned PEP 440 public version `1.7.0`. Two forms are admitted and recorded verbatim with
   `status: causal_conv1d_only`:
   - a **local label** (`==1.7.0+cu12torch2.6…`);
   - a **direct reference** to a wheel file of 1.7.0 (`@ file://…/causal_conv1d-1.7.0…whl` or an https wheel URL).
4. Anything else is a STOP: another package, another version (`1.7.1`, `1.7.0.post1`), an unreadable reference, a
   removed or added line.
5. The `causal_conv1d_only` record's `disclosure` text speaks of "the prebuilt causal_conv1d wheel"; that is v2.1
   wording.

**Against v2.2.** The recorded v2.2 freeze gives `identical`. A new test feeds the pinned freeze in another line
order and gets `identical`. So the current check **does not wrongly fail** v2.2, and I kept it unchanged.

**What reading (1) might choose.** Each of these passes v2.2's recorded freeze. They differ only on images whose
freeze is not identical:
- **(a) Exact match only.** The V21 allowance would be dropped for v2.2, since its build already guarantees an
  identical freeze. `causal_conv1d_only` would become a STOP. This is a one-line change in `check_env3_freeze`, plus
  tests, the note's `env3_freeze:` and the STOP list.
- **(b) The rows' text as written** (the current code). One causal_conv1d line may differ, at 1.7.0. A local label and
  a direct wheel reference are admitted.
- **(c) As (b), but narrower.** For example, a version-only `==1.7.0` line with no local label, or no direct reference
  (`file://` sdist or wheel). The v2.2 review notes that a `file://` line "is not 'the same version number'" for the
  build's strict check. Either narrowing is a change to the regexes in `_causal_version`.
- **(d) Add source-build evidence.** For example, the job could also check the image's
  `causal_conv1d_build_log_sha256` (`fe872a3e…`), wheel sha256 (`9ec74ffe…`) or extension sha256 (`8d6065c7…`) in
  VERSIONS. This is not stated by any row. Today the VERSIONS sha256 pin covers those lines indirectly.

If (a) is chosen, the `disclosure` wording no longer matters. If (b) or (c) is chosen, it should say "a causal_conv1d
build of the same version" rather than "the prebuilt wheel".

### Fields still TODO (the cluster or the author fills them)

- **Spec** `p4_spec.json`:
  - `paper.commit` (the published launch commit);
  - `image.versions_sha256` (`TODO_VERIFY_ON_HOST`: VERSIONS.txt of image v2.2);
  - `host_config.sha256` (after the `TODO_VERIFY_ON_HOST` fill; `18f18cfc…` today);
  - `labels.partition_sha256`, `labels.receipt_sha256`, `labels.freeze_record.path` and `.sha256` (P1);
  - `estimate.source` and `estimate.hours` (the H200 SFT probe; until then the 8× case).
- **Host config:** every `TODO_VERIFY_ON_HOST` value (paths, GPU record, model `local_path`/`adapter_local_path`,
  `venv.path`, `venv.causal_conv1d`).
- **Note draft:** `spec_sha256`, `code_commit`, `labels`, `label_receipt`, `label_freeze`, `host_config` (sha256),
  `versions_sha256`, `env3_freeze` (the reading of decision (1)), `h200_smoke_e0` (main commit and run-record review),
  `h200_sft_probe`, P1, P2, P3 (the review of this unit at the launch commit), P4 (the author's tick), P5, P7, and
  `approved`.

### Open points for the reviewer and the author

1. The v2.2 report and review are not on `main`. Before signature, P5 and `h200_smoke_e0` need the main commit that
   carries them.
2. P5 asks for an independent review of each record. The v2.2 review I found covers the Dockerfile and workflow
   diff, not the I2/I3/smoke/E0 run results.
3. R1-TRACKP-P4-RUNNER-DECISIONS is **not** added to `PLAN_ROWS`. The row was not on any ref and I did not know its
   text. If the author wants the launch binding to require it, add it once it is on main.
4. The host config's `image.cpu` and `image.tag` were updated together with `image.gpu` (see above).
5. No v2.1-specific behaviour is left in the job other than the `disclosure` string discussed above.

### Tests

- `r1/tests/test_trackp_p4_runner.py`: 78 passed (74 at `7ab79a9d8`). The four new tests:
  - the shipped spec, host config and note draft name image v2.2; VERSIONS and the other cluster fields stay
    placeholders; P5 cites the three rows with the v2.2 records; every `PLAN_ROWS` row is in this checkout's
    `PLAN.md`; the v2 and v2.1 digests appear nowhere as the image;
  - v2.2's recorded freeze passes as `identical`;
  - the v2.1 digest is refused;
  - `image.row` `R1-TRACKP-IMAGE-V21` is refused.
- The switch test adds three P5 refusals: V21 missing, V22 missing (V22-B alone does not count), V22-B missing.
- The note-draft completion test fills `env3_freeze` as a declared open field.
- Related files, one at a time: `test_trackp_sft` 35 passed, `test_trackp_sft_test_eval` 48 passed,
  `test_trackp_p3` 23 passed.
