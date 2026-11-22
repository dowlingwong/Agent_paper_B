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

All on NEMO2 H200 with image v2.1:
- the env3 `uv pip freeze` line format in v2.1 (the build record says it is identical to the pin);
- the host config's local paths relative to the job directory;
- staging speed and the transfer of a 4B base;
- the synthetic test path with a real base;
- the output transfer and seal of `out.tar`.

These also fall within the draft's §10 and the SFT probe.
