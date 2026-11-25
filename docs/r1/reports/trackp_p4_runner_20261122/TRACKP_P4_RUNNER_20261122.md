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
- **`check_env3_freeze`** (R1-TRACKP-V21-FREEZE). **[Superseded** by R1-TRACKP-P4-RUNNER-DECISIONS (1); see "env3 check: R1-TRACKP-P4-RUNNER-DECISIONS (1), implemented" in the v2.2 section: direct references and the `causal_conv1d` spelling are now STOPs.**]** The sorted line sets must be equal, with one exception: one
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
- **R1-TRACKP-V21-FREEZE:** **[Superseded** by R1-TRACKP-P4-RUNNER-DECISIONS (1); see "env3 check: R1-TRACKP-P4-RUNNER-DECISIONS (1), implemented" in the v2.2 section: direct references and the `causal_conv1d` spelling are now STOPs.**]** The pinned freeze is R1-ENV-PIN's. Admitted: identical; a local label; an underscore
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

- **"The same version number"** (R1-TRACKP-V21-FREEZE): decided by R1-TRACKP-P4-RUNNER-DECISIONS (1); see
  "On main `3024db3f`, image v2.2" below for the check as now implemented.
- **Staging** is the one network step of the job: weights by curl with size and sha256 checks, as the staged E0 job
  does; tokenizers through the hub into the job's `HF_HOME`. Data building and training run offline, which is the
  draft's "network access to the Hugging Face hub (offline mode)" STOP applied after staging. If the author wants the
  tokenizers staged by curl as well, that is a small change.
- **The first arm**, `kev-0.8b`, goes alone. It is a runner choice: the smallest job that stages an adapter and a
  base.

## Needs a cluster test

All on NEMO2 H200, now with image v2.2 (written for v2.1; see "On main `3024db3f`, image v2.2" below):
- the env3 `uv pip freeze` line format in the image (the v2.2 build record says the sorted freeze is identical to the
  pin);
- the host config's local paths relative to the job directory;
- staging speed and the transfer of a 4B base;
- the synthetic test path with a real base;
- the output transfer and seal of `out.tar`.

These also fall within the draft's §10 and the SFT probe.

## On main `3024db3f`, image v2.2 (24 Nov 2026)

Prepared by the Mac-desk agent (Claude), AI-assisted, 24 Nov 2026. Desk work only: no GPU, no image pull, no server
access. A disclosure about one search is under "Incidental output from sealed-data files" below.

**Basis.** The branch carries two merge commits from `main`, both made with `git merge --no-ff origin/main`, both
without conflicts (the runner branch only adds files and the host config was untouched on `main`):

| merge | main merged | what main brought for this unit |
|---|---|---|
| `4e26995a` | `76a3c71f` | — (at that time the v2.2 records were only on `origin/trackp-v22-image-20261124` @ `a20bd02e`, and R1-TRACKP-P4-RUNNER-DECISIONS was on no ref) |
| `d7d5a32f` | **`3024db3f`** (`3024db3f8c9aa806c5c3458426e55d63d09edcab`) | the v2.2 report `docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md` and review `docs/r1/reviews/TRACKP_V22_IMAGE_REVIEW_20261124.md` (merge `ac981011`), and the PLAN row **R1-TRACKP-P4-RUNNER-DECISIONS** (`ffe1edff`) |

The row says, as recommended: "(1) 'the same version number' in R1-TRACKP-V21-FREEZE reads as version 1.7.0, any local
build label admitted and recorded; with image v2.2 building causal_conv1d from source (R1-TRACKP-IMAGE-V22-B) the env3
line is checked against 1.7.0; (2) tokenizers are staged through the hub into `HF_HOME`; (3) `kev-0.8b` is the first,
solo arm. The P4 tick and the signature of the phase-1 note follow later."

### What changed

- **Image fields** (from the v2.2 report):

  | where | value |
  |---|---|
  | `p4_spec.json` `image.digest` | `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` |
  | `p4_spec.json` `image.row` / `tag` / `build_record` | `R1-TRACKP-IMAGE-V22-B` / `20261124-v2.2-667bb9c2` / the v2.2 report path |
  | host config `r1/scripts/configs/trackp_htcondor_v2.json` `image` | gpu `sha256:49dd9900…`, cpu `sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8`, tag `20261124-v2.2-667bb9c2`; `host` "HTCondor GPU (image v2.2)"; the comment names v2.2 |
  | note draft `image:` | the v2.2 gpu digest, tag, row and report |

  - The host config's sha256 goes from `d53681c9…` to
    **`18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140`**; the spec's TODO comment says so.
  - Its `TODO_VERIFY_ON_HOST` values are unchanged, including `venv.causal_conv1d`.
  - No code reads its `image` or `host` fields.
  - `image.cpu` and `image.tag` were set together with `image.gpu`, because the three describe one build.
- **`VERSIONS.txt` sha256: left `TODO_VERIFY_ON_HOST`.**
  - It is not in the v2.2 report, its review, or anywhere on `main` `3024db3f` or the v2.2 branch. No raw capture of
    759993/759994/759997/760000 is committed.
  - It cannot be derived: image VERSIONS has a `build_utc` line.
  - The spec holds `TODO_VERIFY_ON_HOST: …` and the note draft holds `<FILL: … TODO_VERIFY_ON_HOST …>`. Both are
    refused at launch strength or at signature.
- **`p4_lib.py`:**
  - image v2 **and v2.1** (`sha256:31478d99…`, whose prebuilt causal_conv1d failed to import in smoke 759983) are
    refused as the P.4 image;
  - `image.row` must be `R1-TRACKP-IMAGE-V22-B` (`IMAGE_ROW`);
  - `first_arm` must be `kev-0.8b` (`FIRST_ARM`, decision (3));
  - `PLAN_ROWS` adds **R1-TRACKP-P4-RUNNER-DECISIONS**, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B; all eleven rows
    are on `3024db3f` (a test checks this checkout's `PLAN.md`; `verify_launch_p4` checks `origin/main` at launch);
  - `assemble` compares the env3 local label across jobs too;
  - docstrings say v2.2 and cite the row.
- **`r1/c3/train/p4_phase1.py`: `check_env3_freeze` implements decision (1)** (below).
- **`p4_switch.py`:**
  - P5 must cite all three image rows, R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B. A row id is
    matched as a whole id (`_cites`), so `R1-TRACKP-IMAGE-V22-B` alone does not cite `R1-TRACKP-IMAGE-V22`.
  - The note's `env3_freeze:` must also name R1-TRACKP-P4-RUNNER-DECISIONS.
- **`p4_render_jdl.py`, `p4_job.sh`:** the header comments say image v2.2. The JDL's `container_image` is the spec
  digest.
- **Note draft** (still `approved: false`, unsigned):
  - `image:` is filled;
  - `env3_freeze:` states decision (1), with no placeholder;
  - `job_layout:` cites decision (2); the submission order cites decision (3);
  - `h200_smoke_e0:` names the v2.2 report on main since `ac981011` and keeps `<FILL: the independent review of these
    run records>`;
  - P5 is PENDING, cites the three rows, and gives the v2.2 records: report and review on main since `ac981011`;
    review round 2 ACCEPTED at `3c54a0e8`; Actions run 45290856704; tag; gpu and cpu digests; build-log sha256
    `fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312`; I2 759993 PASS; I3 759994 PASS; smoke 759997
    PASS (kernels_bound); E0 760000 equivalent;
  - P7 names the v2.2 image fields.

### env3 check: R1-TRACKP-P4-RUNNER-DECISIONS (1), implemented

**Before** (READY 82):
- equal sorted line sets gave `identical`;
- otherwise one causal_conv1d line for one, at the pinned PEP 440 public version, gave `causal_conv1d_only`. The
  name was normalised, so `causal_conv1d==1.7.0` passed, and three forms were admitted: a local label, a direct
  reference to a wheel of 1.7.0 (`@ file://…whl`, `@ https://…whl`), and the other name spelling;
- the identical case did not look at the causal line.

**Now** (`check_env3_freeze`, constants `CAUSAL_VERSION = "1.7.0"`, `PINNED_CAUSAL_LINE = "causal-conv1d==1.7.0"`):
1. A duplicate line in either freeze is a STOP (unchanged).
2. The pinned freeze must hold `causal-conv1d==1.7.0`. The line is checked against 1.7.0, not against whatever the
   pinned file says. The pin file is also sha256-pinned (`50238e5a…`).
3. Every line other than causal_conv1d must match the pin exactly; any other difference is a STOP.
4. The image freeze must hold exactly one causal_conv1d line. It must read `causal-conv1d==1.7.0` or
   `causal-conv1d==1.7.0+<label>`, where the label is a PEP 440 local label: alphanumeric segments joined by dots.
5. Everything else is a STOP:
   - another version (`1.7.1`, `1.7.0.post1`, `1.7.1+x`);
   - an empty or malformed label;
   - another name spelling (`causal_conv1d==…`) or another operator;
   - a direct reference (`@ file://…`, `@ https://…`, even to a 1.7.0 wheel);
   - a removed or added causal line.
6. The record for the job (`job_record.json` → `env3_freeze`) always carries `rule` (R1-TRACKP-V21-FREEZE),
   `decision` (R1-TRACKP-P4-RUNNER-DECISIONS (1)), `image_line`, `version` 1.7.0, **`local_label`** (null when bare),
   `sha256_sorted`, the pin's sha256 and the image freeze's sha256. Then:
   - an identical freeze gives `status: identical`;
   - a labelled line gives `status: causal_conv1d_only`, with `pinned_line` and a disclosure naming the label, "recorded
     in the job record and disclosed in the P.4 report".

**Image v2.2.** Its build records the sorted freeze identical (`causal-conv1d==1.7.0`, built from source and installed
by name; VERSIONS `env3_sorted_diff=empty`), so it gives `identical` with `local_label: null`. A test feeds the pinned
freeze in another line order and gets that result. One sentence in the v2.2 report, "only the `causal_conv1d` line
differs", repeats a Dockerfile comment the v2.2 review calls stale. The review states the line is identical.

**Narrowing to note for the reviewer.** Two forms the READY-82 code admitted are now STOPs: the direct reference and
the other name spelling. I read "any local build label admitted" together with the coordinator's instruction (accept
`causal-conv1d==1.7.0` and `1.7.0+<local label>`; every other line must match exactly) as excluding them. Neither
appears in image v2.2's recorded freeze.

### Decisions (2) and (3)

- **(2)** was already the runner's behaviour. `p4_lib.stage` fetches the registry weights by curl, with size and
  sha256 checks. It then runs `serialize.load_tokenizer` for the pool with `HF_HOME=<job>/hf` and the hub online; every
  later step runs offline. The staging test now asserts that the tokenizers go through the hub, in one env3 Python
  call, into `<job>/hf`, and that curl fetches only registry files. The note's `job_layout:` cites (2).
- **(3)** was the spec's `first_arm` and the switch's solo-first gate. `validate_spec` now *requires* `first_arm:
  kev-0.8b`, and `kev-0.8b` among the arms. Tests refuse another first arm, and arms without `kev-0.8b`. If P2's P.3a
  records remove `kev-0.8b` under P4-ARMS A, the runner STOPs and the question returns to the author; the note says
  so.

### Text decoding in the job (review note on the sweep-1 freeze record)

A reviewer of the separate sweep-1 freeze-record unit reproduced a failure. Under a forced ASCII locale (`LC_ALL=C`,
`PYTHONCOERCECLOCALE=0`, `PYTHONUTF8=0`), `inputs()` read the signed freeze record with a bare `read_text()`, and the
record's UTF-8 dashes raised `UnicodeDecodeError` instead of a STOP. The fix:
- every text file the job reads in `p4_lib.py` goes through `_read_utf8`: the bytes are decoded as UTF-8, and a
  non-UTF-8 file is a STOP. The freeze record gives `ProtocolStop`, as its other refusals do; every other file gives
  an infrastructure `Stop`. This covers the spec, the pinned freeze, the SFT and host configs, the receipt, the freeze
  record, data manifests and reports, records, receipts and the run ledger;
- `p4_phase1._rows` does the same, with a `P4Stop`;
- the job's subprocess output (`_sh`, `_git`) is decoded as UTF-8 with `errors="replace"`, so a non-UTF-8 byte cannot
  raise. In the env3 freeze such a byte would then mismatch the pin and STOP;
- the two log files that hold subprocess output are written as UTF-8.

Tests: a UTF-8 freeze record with dashes passes `inputs()`, and a non-UTF-8 one is a `ProtocolStop`. A child Python
run under that ASCII locale shows that a plain `read_text()` raises there, while `_read_utf8` reads the record,
STOPs on a bad file, and `_sh` decodes UTF-8 output and replaces a bad byte. The child is run without `-I`, because
`-I` drops `PYTHONUTF8=0` and the C locale then turns UTF-8 mode on. The test skips on a platform with no ASCII
locale.

### Incidental output from sealed-data files (review M2)

While I looked for raw captures of the v2.2 jobs, I ran this from the main checkout (`/tmp/pb/repo`):

`git grep -n "759993\|759994\|759997\|760000" origin/trackp-v22-image-20261124 | cut -c1-250 | head -20`

The pattern was meant to find job ids, but it also matched digit runs inside data files. Up to 250 characters of
each matching line were printed:
- two lines from `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json`, each showing a `"delta_audit"` field
  and its number;
- fifteen lines from `docs/r1/reports/b2_audit_20261119/evaluation_block.jsonl`, each showing the `proposal_id`, the
  `node` and the
  `seeds` list. Each line was cut at or before the start of the `delta_evaluation` key, so no evaluation value was
  shown;
- three lines from `docs/r1/reports/b2_audit_20261119/label_block.jsonl`, showing the `proposal_id`, the `node`,
  `"label_kind": "audit"` and the start of the `seeds` list, cut before any label value.

Nothing in this unit uses that output: no value, id or seed from it appears in any file or test. I did not open those
files again, either to check or to write this. The later searches were limited to named paths, or used patterns
that printed no lines from those files. None of them used an explicit `*block.jsonl` exclusion.

**For the author:** is a record beyond this paragraph needed? In particular, do the seed lists shown from
`evaluation_block.jsonl` count as sealed evaluation data? Does the `delta_audit` number from `b1_manifests.json`
matter?

### `image.versions_sha256`: how it gets filled (review m1)

The value is not in any cluster record, so the cluster agent records it, and it is filled in the launch commit:
1. Inside the digest-pinned v2.2 gpu image on NEMO2, run `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt`.
   Use an HTCondor job with the same header as the staged smoke,
   `docs/r1/reports/trackp_h200_20261118/stages/smoke_h200/probe.jdl`: `universe = container`,
   `container_image = docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949`,
   and the NEMO2 `requirements`. Those scripts have no explicit `apptainer` command; HTCondor runs the container.
2. Commit the VERSIONS.txt text together with the sha256 line. Alternatively, commit the handback captures of
   759994/759997/760000, whose probe scripts `cat /opt/r1/VERSIONS.txt`, with the sha256 of the exact file.
3. Do not use the I2 identity's `versions_sha256` (`s4_run.sh`): I2 runs on the cpu image.

The same text is in the spec as `image.versions_sha256_comment`.

### Review of `df616ec6` (NOT ACCEPTED): findings and fixes

| finding | fix |
|---|---|
| **M1**: the note's `env3_freeze:` still admitted "a wheel of that version" | Rewritten. Admitted forms: exactly `causal-conv1d==1.7.0`, or `causal-conv1d==1.7.0+LABEL` with a PEP 440 local label (written `LABEL`, because the switch refuses any `<…>` in a note), the label recorded. STOP forms named: a direct reference (`causal-conv1d @ file://…` / `@ https://…`, even of version 1.7.0) and the `causal_conv1d` spelling. Signing therefore ratifies the narrowing. The STOP list at the end of the note matches. Test: the line contains no "wheel" and no "wheel … admitted", names both STOP forms, and the code refuses both. |
| **M2**: "no label or evaluation file read" contradicted the incidental `git grep` output | The sentence is replaced by the disclosure above (command, what was printed, nothing used, no re-opening, later searches), plus a question for the author. |
| **m1**: no procedure for `image.versions_sha256` | Procedure above, and `image.versions_sha256_comment` in the spec. The value stays `TODO_VERIFY_ON_HOST`. |
| **m2**: `_read_record` raised `Stop` on a non-UTF-8 record, so `seal()` refused | `_read_record` catches that `Stop` and returns None, so the attempt is sealed as unreadable and charged the walltime. Test: a non-UTF-8 record is sealed with `record_readable: false`, unverified, at the walltime, with its bytes kept. |
| **m3**: `estimate.hours` not bound at launch | Enforced. `p4_switch.check` reads the probe record from `origin/main` and requires one `p4_estimate_hours: <arm> <hours>` line per spec arm, equal to `estimate.hours` (`check_probe_hours`). The 8× placeholder hours therefore cannot launch unless the probe gives exactly them. The spec's `estimate.hours_comment` and the note's `h200_sft_probe:` FILL state the line format. Tests: the right lines pass; missing, unequal, duplicated or absent lines are refused. |
| nit: host config comment "I2/I3 redone on v2" | **Not changed.** Editing the host config changes its sha256 (`18f18cfc…`), which the other author's test plan on `df616ec6` may use, and it would take the change outside the runner files. Left for the next host-config touch (the P7 fill changes the sha256 anyway). |
| nit: report lines on the old freeze reading | Marked superseded, under "What changed" (`check_env3_freeze`) and "Tests" (R1-TRACKP-V21-FREEZE). |
| nit: cross-check spec `image.digest` against host config `image.gpu` in `validate_spec` | **Not done.** `validate_spec` also runs inside the job, where `p4_lib.py` is transferred without the repository, and the job's `configs()` and its tests use non-JSON stand-ins. The shipped pair is already checked by `test_the_shipped_spec_host_config_and_note_draft_name_image_v22`. |

Tests after the fixes, run one file at a time: `test_trackp_p4_runner` 89 passed, `test_trackp_sft` 35 passed,
`test_trackp_p3` 23 passed. The changes stay inside the runner files, the note draft, this report and the runner test,
so the full suite was not rerun. The lists above are for `de6dd56d`.

### Fields still TODO (the cluster or the author fills them)

- **Spec** `p4_spec.json`:
  - `paper.commit`;
  - `image.versions_sha256` (`TODO_VERIFY_ON_HOST`, VERSIONS.txt of image v2.2);
  - `host_config.sha256` (after the `TODO_VERIFY_ON_HOST` fill; `18f18cfc…` today);
  - `labels.partition_sha256`, `labels.receipt_sha256`, `labels.freeze_record.path` and `.sha256` (P1);
  - `estimate.source` and `estimate.hours` (the H200 SFT probe; until then the 8× case).
- **Host config:** every `TODO_VERIFY_ON_HOST` value: paths, GPU record, model `local_path` and `adapter_local_path`,
  `venv.path`, `venv.causal_conv1d`.
- **Note draft:** `spec_sha256`, `code_commit`, `labels`, `label_receipt`, `label_freeze`, `host_config` (sha256),
  `versions_sha256`, `h200_smoke_e0` (the review of the run records), `h200_sft_probe`, P1, P2, P3 (the review of this
  unit at the launch commit), P4 (the author's tick), P5, P7, and `approved`.

### Open points for the reviewer and the author

1. P5 asks for an independent review of each record. The v2.2 review on main covers the Dockerfile and workflow diff,
   not the I2/I3/smoke/E0 run results.
2. The narrowing above: direct references and the other name spelling are now STOPs.
3. The host config's `image.cpu` and `image.tag` were updated along with `image.gpu`.
4. `first_arm` is now fixed to `kev-0.8b`, so a P2 outcome without `kev-0.8b` needs the author.

### Tests

- `r1/tests/test_trackp_p4_runner.py`: 88 passed; there were 74 at `7ab79a9d8`. New or changed:
  - **text decoding:** the ASCII-locale test, and the UTF-8 and non-UTF-8 freeze records in the inputs test;
  - **decision (1):**
    - admitted, with the label recorded: bare `==1.7.0`, `+cu12torch2.6cxx11abiFALSE`, `+local`, `+cu124.src.1`;
    - refused: `1.7.1`, `1.7.0.post1`, `1.7.1+local`, an empty label, a malformed label, the underscore spelling,
      `>=1.7.0`, file and https wheel references, an unreadable reference, a removed line, an added line, `torch`
      with another local label, an extra package, a duplicate;
    - a pin without `causal-conv1d==1.7.0` is refused;
    - the job step records `local_label` and `decision`, and v2.2's freeze gives `identical` with no label;
  - **decisions (2) and (3):** the staging test (hub, `HF_HOME`); `first_arm` other than `kev-0.8b` refused; arms
    without `kev-0.8b` refused;
  - **image v2.2:**
    - the shipped spec, host config and note draft name v2.2, and the cluster fields stay placeholders;
    - P5 cites the three rows with the v2.2 records;
    - the note's `env3_freeze:` states (1) with no placeholder, `job_layout:` cites (2), the note cites (3);
    - every `PLAN_ROWS` row, including R1-TRACKP-P4-RUNNER-DECISIONS, is in this checkout's `PLAN.md`;
    - the v2 and v2.1 digests appear nowhere as the image;
    - the v2.1 digest and an `image.row` of V21 are refused;
  - **switch:** P5 refusals (V21, V22, V22-B each missing), and an `env3_freeze:` without the decisions row refused.
- Related files, one at a time: `test_trackp_sft` 35 passed, `test_trackp_sft_test_eval` 48 passed,
  `test_trackp_p3` 23 passed.

### Full suite (`r1/tests`, baseline `3024db3f` and the unit's tip)

Command: `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`, with
`AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, `PYTHONDONTWRITEBYTECODE=1`, a fresh `TMPDIR` cleared between the runs, and
lightgbm not installed. The runs were one after the other, never at the same time as another full suite.

| run | checkout | result |
|---|---|---|
| baseline | detached clean `3024db3f` (worktree removed afterwards) | 58 failed, 3823 passed, 197 skipped, 3 errors (575 s) |
| tip | `de6dd56d` (this unit, code as committed) | 58 failed, 3911 passed, 197 skipped, 3 errors (566 s) |

The sorted `FAILED`/`ERROR r1/tests/…` node ids, with pytest's ` - message` suffix cut, are in
`FULLSUITE_BASE_3024db3f.txt` and `FULLSUITE_P4_TIP.txt` beside this report. The two lists are **identical** (61 lines
each), so the unit adds no failure. The 88 extra passes are `test_trackp_p4_runner.py`, which is not on `main`. Every
failing file is outside this unit; the files and counts are in the lists.

## On `912a7e02`: P4-F2 A, the probe mode, P4-PROBECAP A, the host-config fill hook (25 Nov 2026)

Prepared by the Mac-desk agent (Claude), AI-assisted, on `mac-trackp-p4-f2-probe-20261125`, under
R1-P4-TESTPLAN-DECISIONS (25 Nov 2026 (b)). The full record is `P4_F2_PROBE_HOSTCFG_20261125.md` beside this report.
In short:
- **F2 (P4-F2 A).** `p4_phase1.check_receipt_table` accepts only the receipt whose `inputs.proposals_sha256` is the
  sealed v2 table `arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256`, and runs A3's `arms_freeze.require_feat_one` on the
  identity result A3 consumed (`docs/r1/reports/arms_a3_20261123/feat_one_identity.json`, sha256 pinned).
  `p4_phase1.join_labels` joins the released labels to `sweep1_v3` by proposal id with A3's `load_traindev` and
  `training_rows`. `p4_lib.inputs` (step 5) runs both. The render's `check_inputs` runs the binding (not the join).
  The earlier v3-pin check of the receipt (review round 1, minor 4) is replaced: under P4-F2 A a v3-pin receipt is
  refused. All pins stay.
- **The probe mode (F1, P4-PROBE A).** `p4_lib.py probe`, `validate --probe`, `probe-record`; `p4_probe.sh`;
  `p4_probe_spec.json` (a template); `p4_render_jdl.py --probe`. The P.4 job's own steps run unchanged, and nothing is
  added to the training path.
- **P4-PROBECAP A.** A new spec field `caps.probe_gpu_hours` (a placeholder until the spec-fill commit). It is added
  by `projection`, `charged_hours`, `assemble` and the switch's `check_cap`, and required at launch. The switch binds
  it to the probe record's `p4_probe_gpu_hours:` line and the note's `gpu_hours_cap:`. `seal` charges an unreadable
  probe attempt at the probe's `walltime_s`.
- **F7 / F5.** `p4_fill_host_config.py` writes the 19 values from a host-side input file. The tests hold for the
  placeholder and the filled host config and spec; `test_trackp_sft.py` changed by one assertion. `verify_launch_p4`
  is unchanged.
- **The note draft** (`approved: false`): a new filled field `label_table_binding:` (required by the switch), and
  `gpu_hours_cap:` and `h200_sft_probe:` updated for the probe charge.
- Tests: `test_trackp_p4_runner.py` 119 passed (89 at `912a7e02`). Full suite: baseline `912a7e02` and tip, 58 failed
  and 3 errors each, with identical lists (`FULLSUITE_BASE_912a7e02.txt`, `FULLSUITE_F2_PROBE_TIP.txt`).
- **Review round 1** (`51860ca3`, NOT ACCEPTED; two majors in the probe cap accounting, six minors): fixed in
  `45575c526`. The probe charge is now re-derived from the sealed tree in `assemble` and `check_cap`, a staged probe is
  recorded as a pending submission, `probe-record` takes `condor_history` wall clocks (and optionally T1's,
  decision P4-T1CHARGE), and `seal` checks the attempt kind. Details: §7 of `P4_F2_PROBE_HOSTCFG_20261125.md`.
- **Review round 2** (`1d51c578`, NOT ACCEPTED; one major): fixed in `493122fc5`. `probe-record` writes the charges
  it used once into the sealed tree (`<probe run>/_wallclock.json`, sha256 bound in `probe_records.json`), and the
  launch-time re-derivation applies them and STOPs on any later probe attempt. A never-submitted probe stage is sealed
  as a probe attempt (2 h). Details: §7 of `P4_F2_PROBE_HOSTCFG_20261125.md`.
