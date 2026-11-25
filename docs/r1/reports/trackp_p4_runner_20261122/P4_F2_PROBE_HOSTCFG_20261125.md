# Track P P.4 phase 1: the F2 receipt binding, the probe mode, the host-config fill hook and the F5 tests

Prepared by the Mac-desk agent (Claude), AI-assisted, 25 Nov 2026, on `mac-trackp-p4-f2-probe-20261125` over
published `main` `912a7e02`. ENGINEERING_ONLY. Revised after independent review rounds 1 (`51860ca3`), 2 (`1d51c578`) and
3 (`4706de7d`), all NOT ACCEPTED: see §7; §2, §5 and §6 are updated for them. Desk work only: synthetic fixtures, no GPU, no image, no server, no
label or evaluation file opened, nothing pushed. For independent review.

## Authority

- **R1-P4-TESTPLAN-DECISIONS** (25 Nov 2026 (b)): P4-F2 A, P4-PROBE A, P4-PROBECAP A (P4-INCID A needs nothing here).
- **R1-C3-SWEEP1-LABELS-FROZEN**: the signed freeze record `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md`
  has sha256 `d0c8d10aa2f6728dd135481b9dde1a4345410272ee67bada0ce93a5be01f7914` at `20ccf7e3` and the same at
  `912a7e02` (checked; `git diff 20ccf7e3 912a7e02` touches only `PLAN.md`). This unit does not change it.
- Rows these cite, read: R1-ARMS-DECISIONS (FEAT-ONE A), R1-TRACKP-P4-DECISIONS (P4-CAP A, P4-MB A),
  R1-TRACKP-P4-RUNNER-DECISIONS, R1-TRACKP-IMAGE-V22 and -V22-B, R1-HTC-QTORCH.
- The cluster test plan `P4_CLUSTER_TEST_PLAN_20261124.md` and its review (findings F1-F10, §2-§6, the field table).

## 1. F2: the receipt bound to the sealed v2 table (P4-F2 A)

**Rule implemented.** The only sweep-1 receipt table P.4 accepts is the sealed v2 table
`arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256` (`b713c423…57c4`). Any other `inputs.proposals_sha256` is a STOP,
including the `sweep1_v3` pin `d0048567…d1d5` that the accepted runner required.

**Code.**
- `r1/c3/train/p4_phase1.py`:
  - `check_receipt_table(receipt, table_proposals_sha256=…, root=…)`. It checks the receipt's table against
    `arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256` (read at call time). Then it calls `arms_freeze.require_feat_one`,
    A3's own function, not a re-implementation, on the identity result A3 consumed:
    `docs/r1/reports/arms_a3_20261123/feat_one_identity.json`, sha256 `039b8360…2971` (A3 `RUN_I.md` command 1 and its
    `SHA256SUMS`). The sha256 is pinned in `FEAT_ONE_IDENTITY`. This is what `arms_freeze train-a3` does
    (`require_feat_one(identity, sealed_sha256=receipt.inputs.proposals_sha256, arms_sha256=<v3 table>)`). The check
    is STOP on a missing or altered identity file, a failing result, a result for another sealed table, another arms
    table, other configs, or no `budget_frac_left` difference.
  - `join_labels(release_root, receipt_sha256=…, table_dir=…)`: A3's join by proposal id, with A3's functions
    `arms_freeze.load_traindev` (receipt pinned, `release.open_partition`) and `arms_freeze.training_rows`. STOP on a
    non-inert, non-duplicate train/dev row without its label, a label for a proposal outside the table, a label on a
    duplicate or a test row, or a duplicate label row. It returns counts only. `ArmsFreezeError` and `ReleaseStop` both
    become `P4Stop`.
  - `check_partition` now takes `table_proposals_sha256` and `identity_root` as required keywords. It calls
    `check_receipt_table` after the existing checks, and returns the binding as `table_binding`.
- `p4_lib.inputs` (job step 5), in this order:
  1. the table files against the pins (factored out as `table_inputs`);
  2. the partition pins and the source block;
  3. `check_receipt_table`, with the identity result read from the clone at the paper commit;
  4. the freeze record;
  5. `join_labels`.

  Any STOP is a `ProtocolStop`. The old v3-pin comparison is removed. The record carries `labels.table_binding` and
  `label_join` (counts).
- `p4_render_jdl.check_inputs` (T5, T8; preview or not): the same `check_receipt_table`, with the identity file of
  the submit checkout. No label row is read at the render, and the join runs only in the job. So a stage can no
  longer pass while every job would STOP at step 5. This turns S9's manual gate into a code gate once the unit is in
  the code commit.
- **Pins kept:** receipt `f06e37a9…65c1`, partition `6a6327a3…7b2a`, source block `cdae9c3f…9aca`, `sweep1_v3`
  `d0048567…d1d5`.
- `p4_lib` keeps copies of the sealed-table and v3 sha256 and of the identity pin for the note's new line. A test
  checks that they equal the values in `arms_freeze` and `p4_phase1`.
- **Note binding.** A new required field, `label_table_binding:`, is filled in the draft. `p4_switch.check_binding`
  requires it to contain `P4-F2 A`, the sealed sha256, the v3 sha256, and the identity path and sha256.

## 2. The probe mode (F1, test plan §4.2; P4-PROBE A)

| §4.2 item | implementation |
|---|---|
| 1-5 | `run_probe` calls the job's own `image_identity`, `gpu_identity`, `host_identity`, `clone_full`, `env3_freeze`, `configs`, `stage` and `check_local_paths`, unchanged. It also records staging seconds and bytes, `visible_devices` (F3, below) and the HTCondor job ad (`ClusterId`, `ProcId`, `GlobalJobId`). |
| 2 (code binding, added) | `probe_code_binding`: the transferred `p4_lib.py` must equal the clone's at `paper.commit`, and the transferred spec must differ from the clone's committed template only in the three host fields. Otherwise STOP. |
| 6 | `table_inputs` only. No label file, receipt or freeze record is transferred (the JDL's input list and the render check this), and `inputs` is not called. |
| 7 | `data_build(..., synthetic=True)`. The manifest's `labels.kind` must be `synthetic`, else a `ProtocolStop`. |
| 8 | One `sft-dev --steps 50`, lr `1e-05`, seed 0, run dir `out/probe/<arm>`, through `p4_lib.trackp`, so a CUDA OOM is an `ArmStop`. The sampler `nvidia-smi --id=<uuid> --query-gpu=timestamp,memory.used,memory.total --format=csv,noheader,nounits -lms 500` writes `out/probe/<arm>.gpu_mem.csv`. Wall stamps go to `out/probe/wall.json` (JSON in place of the plan's `wall.txt`). |
| 9 | No test path, `sft-select`, learning curve, bootstrap or `arm_pin`. The tests fail if the probe calls `inputs` or `test_path`. |
| 10 | `out.tar` holds the allow-list `PROBE_KEEP` only: the logs, the lease log, `wall.json`, the memory samples, the run's `report.json`, `manifest.json` and `stage_s/{sft_report.json,metrics.jsonl,best.json}`, and the data directory's `sft_data.json`. There is no `ckpt/`, `best/`, `rows.jsonl`, `splits.json` or `.npy` (tested). Then `job_record.json` (schema `trackp_p4_probe_record/1`) and `SHA256SUMS`. The log is named `p4_run.log`, so `p4_lib.py seal` keeps it unchanged. |
| S10 checks | After the run: micro-batch 8 and effective batch 16, `protocol_deviation == {"max_steps": 50}`, the run's `data_sha256` equal to the synthetic build, `0 < stopped_at <= 50`, at least one memory sample. Each is a STOP. The record still holds `oom`, `memory` and `wall` after an OOM. |
| 11 | `r1/scripts/htcondor/trackp_p4/p4_probe_spec.json`, a **template**, never filled in place. It is `p4_spec.json` with run id `trackp-p4-probe-20261125-a` (the date is the template's), its own comment, and a fixed `probe` block: `steps 50, lr 1e-05, seed 0, sample_ms 500, walltime_s 7200, labels synthetic`. The cluster fills a copy in `paper.commit`, `image.versions_sha256` and `host_config.sha256`, and commits that copy with the probe record. `check_probe_template` (at staging and in the job) refuses any other difference. A test checks that the template's fixed fields equal `p4_spec.json`'s. |
| 12 | `validate_probe_spec` (CLI `validate --probe`): the default `validate_spec`; a run id matching `trackp-p4-probe-<YYYYMMDD>-<letter>` and never the P.4 run's; the fixed `probe` block; `paper.commit` 40 hex; `image.digest` equal to the v2.2 digest; `versions_sha256` and `host_config.sha256` 64 hex. The label fields, `estimate.*` and `caps.probe_gpu_hours` may stay placeholders. It does **not** require `h200_sft_probe`, which removes the chicken-and-egg problem of F1. `validate_spec(launch=True)` refuses any spec with a `probe` block. |
| JDL | `p4_render_jdl.py <filled probe spec> <stage> --table T --probe --arm A [--first-record R]` stages `p4_probe.sh`, `p4_lib.py`, the spec (as `p4_probe_spec.json`) and the three table files, and renders `p4probe_<arm>.jdl`. That JDL has `render()`'s fixed lines (container universe, the v2.2 digest, `request_GPUs = 1`, the H200 requirement, the no-resume hold, the `layout` request of 8 CPUs, 131072 MB and 150000000 KB), plus its own executable, arguments and transfer lists, and `+RequestWalltime = 7200`. A stage holds one base. A base other than `kev-0.8b` needs `--first-record`: the sealed, STOP-free `kev-0.8b` probe record of the same probe spec (`check_first_probe_record`). That puts S10's order in code. Submission stays by hand (`condor_submit`) after the pre-submit check. |
| §4.4 record | `p4_lib.py probe-record <filled probe spec> <p4_spec.json> <sealed attempt dirs…> --out probe_records.json` takes one sealed, verified, STOP-free attempt per spec arm (no choosing among attempts). The jobs must agree on commit, image, configs, synthetic data identity, `n_train` and env3 status. It writes `trackp_p4_h200_sft_probe/1` with the §4.4 fields, and prints the lines for the Markdown record: four `p4_estimate_hours: <arm> <H>` lines and one `p4_probe_gpu_hours: <P>` line. The Markdown prose stays the cluster's. |
| §4.5 | `estimate_hours`: `S = 9 × steps(n) + 3 × Σ steps(p)` for `p < n`, with `steps(m) = ceil(ceil(ceil(m/8)/2) × 5)` as in `Trainer.__init__`, and `H = S × s_per_step_wall / 3600` rounded up to 0.01 h. The plan's worked example (n = 593, 1.26 s, giving 2,430 steps and 0.86 h) is a test. |

**Nothing kept as an arm (§4.6).** No checkpoint leaves the scratch. Every run records `protocol_deviation`, which
`check_run_protocol` refuses (tested on the probe's own run). The data directory is synthetic. The run id is the
probe's, so `charged_hours`, `assemble` and `check_first_record` of the P.4 run never see a probe attempt.

### Cap accounting (P4-PROBECAP A)

- **What is charged.** Every sealed attempt of every probe run (`trackp-p4-probe-*` under the sealed root): STOP
  attempts and repeats included, each at its record's `gpu_hours`, or at the probe's `walltime_s` (2 h) when its
  record is unreadable. `probe_charges` sums them, and `probe-record` rounds the sum up to 0.01 as `P`.
- **Where P is written.** In three places, bound to each other:
  1. the probe record's one `p4_probe_gpu_hours: P` line;
  2. the spec's new field `caps.probe_gpu_hours` (a placeholder today; filled in the spec-fill commit, §6 step 9);
  3. the note's `gpu_hours_cap:` line, which must cite P4-PROBECAP A and contain `probe_gpu_hours: P` with two
     decimals.

  `p4_switch.check` binds 1 to 2 (`check_probe_charge`, exactly one line, equal within 1e-9) and 2 to 3
  (`check_binding`).
- **How the later phase-1 jobs see it.** Through the spec they are validated against:
  - `validate_spec(launch=True)` requires `caps.probe_gpu_hours` in (0, 40] with at most two decimals;
  - `projection().within_cap` uses the four jobs' projection plus P;
  - `charged_hours()` adds P to its `total`, so `assemble` (consumed ≤ 40) and the switch's `check_cap` (charged +
    pending + coming ≤ 40) count it before every submission;
  - while P is a placeholder, default-strength validation counts it as 0 and reports `probe_gpu_hours: null`;
  - (round 1, M1; round 2, M1) `assemble` and `check_cap` also re-derive the probe charge from the sealed tree, with
    the charge files `probe-record` wrote (`<sealed_root>/<probe run>/_wallclock.json`: the charge it used per
    attempt, and T1's if charged). For the attempts the record charged, the re-derived value equals P. A probe attempt
    no charge file names (sealed after the record), a pending submission, or a re-derived value above P is a STOP;
    (round 1, M2) staging a probe records a submission, charged at the probe walltime until its attempt is sealed.
- **The probe-record check.** `probe-record` validates the P.4 spec with the probe's hours and P before printing the
  lines. A projection plus P over 40 GPU-h (or over 64 slot-hours, or an hours value outside (0, 20]) is a STOP (S12).
  It flags `probe_over_2_gpu_h` (S12, the chat's agreement) and `headroom_below_15pct` (S10, reported to the author).
- **The note.** The `gpu_hours_cap:` line is rewritten for this. The spec's `comment` and `caps.probe_gpu_hours_comment`
  state the rule.

### F3 (unscoped `nvidia-smi`): the decision

The probe keeps the job's **unscoped** `gpu_identity` unchanged and does not scope it to the assigned UUID. The
trackp GPU lease's `foreign_compute_processes`, inside `trackp.py`, is also unscoped and is unchanged.

Reasons:
1. T7 asks the probe to exercise the job's own steps. A probe that scoped its queries while the P.4 job does not
   would not test the job.
2. Both queries fail closed. More than one GPU listed, or a foreign compute process, is a STOP, so the risk is a
   false STOP, not a wrong measurement.
3. T1 answers F3 on the cluster before the probe. If T1 lists more than one GPU or a process, S6 applies, and one
   reviewed scoping change is needed for the probe and the job together.

Two additions:
- `visible_devices` records `CUDA_VISIBLE_DEVICES`, `NVIDIA_VISIBLE_DEVICES` and `_CONDOR_AssignedGPUs`. It STOPs when
  either of the first two names GPU UUIDs other than exactly the one `gpu_identity` lists. This is T1's pass criterion,
  checked inside the probe.
- The memory sampler, a new query of the probe's own, **is** scoped (`--id=<uuid>`), as the reviewed smoke and E0
  stages scoped theirs.

### F4 (peak memory): the decision

Kept as planned: device memory is sampled from outside by `nvidia-smi` every 500 ms, and the record gives the peak,
the total and `headroom_frac`. Reasons:
- `memory.used` is the quantity that has to fit in the H200's memory.
- The caching allocator rarely returns memory during a run, so a 500 ms sample gives a close peak. Short spikes
  between samples are possible, which is why S10 reports a headroom below 15 %.
- PyTorch's `max_memory_allocated` would need a change in the SFT path that every P.4 run uses, which §4.2 rules out
  ("add nothing to the training path").

## 3. The host-config fill hook (F7) and the F5 tests

**Hook** `r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py`. `--template` prints the host-side input form (schema
`trackp_p4_host_fill/1`), with every forced value written in and the others as `FILL: …`. The run
`<values.json> [--config …] [--dry-run]`:
1. Lists the config's placeholders with `run.placeholders`, the rule of `--check-config`. It requires exactly the 19
   known paths, so a config that is already partly or wholly filled is refused.
2. Requires the input to name exactly those 19 paths (a partial fill or an unknown path is refused), each a non-empty
   string that is not a placeholder, and valid under its rule:
   - **forced:** the six P.4 local paths are `models/<registry key>` (what `check_local_paths` requires);
     `gpu.name` `NVIDIA H200`; `gpu.compute_capability` `9.0`; `venv.path` `/opt/r1/envs/trackp`; `hf_home` `hf`,
     `models_dir` `models` and `runs_dir` `out` (the job's `HF_HOME`, staging directory and lease-log location);
   - **job-relative path:** `work_dir`, `gpu.lock_path` and the four bases P.4 never stages (`laya`,
     `startlux-0.8b`, `startlux-2b`, `startlux-4b`; their values are the chat's choice, F7);
   - **free text:** `venv.causal_conv1d` must name `1.7.0` and `R1-TRACKP-IMAGE-V22-B`.
3. Writes the file in the repository's JSON layout. It checks that nothing else changed: exactly 19 lines differ on a
   synthetic fill, and the rest of the file is byte-identical.
4. Re-checks that no placeholder is left and that `check_local_paths` passes for every arm.
5. Prints the new file sha256 (`sha256sum`, not `config_digest`) for `host_config.sha256`, the probe spec and the
   note.

A desk run on a copy gave `18f18cfc…` before and `bb8ae63e…` after a synthetic fill, and `--check-config` clean. That
value is synthetic, not the cluster's.

**F5.** The tests now pass for the placeholder state and for a filled state:
- `test_shipped_spec_validates_and_refuses_launch_until_filled`: each spec fill field must be a placeholder or a valid
  value. Launch validation must pass exactly when none is left, and the projection is computed from the spec's own
  hours.
- `test_the_shipped_spec_host_config_and_note_draft_name_image_v22`: the host config must hold exactly the 19
  placeholders, or none with every value valid under the hook's rules and `check_local_paths` passing. In the filled
  state the spec's `host_config.sha256` must be a placeholder or the file's sha256.
- The fill-hook tests run on a synthetic copy. After the fill commit they rebuild the placeholder copy themselves.
- `r1/tests/test_trackp_sft.py::test_htcondor_config_runs_the_qtorch_checks_and_skips_the_portal_schedule`: its
  assertion that `venv.causal_conv1d` holds `TODO_VERIFY_ON_HOST` would have failed after the fill. The test plan's F5
  did not list it. It now accepts the placeholder or a value naming 1.7.0 and R1-TRACKP-IMAGE-V22-B.

**`verify_launch_p4`: unchanged.** The plan (§6 step 4, the "Terms for commits") makes the host-config fill its own
reviewed commit, an ancestor of `paper.commit`, together with the probe mode and the F5 tests. The spec-fill commit
(§6 step 9) changes only `p4_spec.json` and `docs/`. The allowed diff therefore need not admit the host config, and I
did not widen it. Widening it would let an unreviewed host-config change ride on the spec-fill commit.

## 4. Tests

- `r1/tests/test_trackp_p4_runner.py`: **119 passed** (89 at `912a7e02`). New or changed:
  - **F2:** acceptance of the sealed table; refusal of the v3 pin, of any other table, of a missing, altered or
    failing identity result, and of another arms table; the published receipt's copy and the committed identity
    result passing with the real pins (only `inputs.proposals_sha256` of the receipt is used); A3's join on a
    synthetic world from `test_c3_arms_freeze` (a missing label, a stray label, a test label and a duplicate are each
    a STOP); `inputs` with the binding and the join (the old "another table" test now also refuses the v3 pin); the
    render refusing another receipt table, preview or not;
  - **probe:** the template against the spec; probe strength; the template check; the full probe on CPU (hash-bag
    stand-in, real synthetic build, real Stage S with `--steps`), covering the arguments, the sampler argv, the record
    fields and the `out.tar` allow-list; an OOM (record, memory and wall kept), no memory sample, a visible-devices
    mismatch, a non-synthetic build, a template mismatch, and a transferred `p4_lib.py` that is not the clone's;
    sealing in the probe tree (a killed attempt charged 2 h); the first-arm gate; `probe-record` (the hours, `P` over
    every attempt, the lines bound by the switch's checks, the S12 refusal); `probe_charges` over two probe runs,
    ignoring the P.4 run; the probe stage and its JDL; `p4_probe.sh` syntax;
  - **cap:** the probe charge in the projection, `charged_hours`, `assemble` and `check_cap` (a case that fits without
    the probe and not with it); launch refusals of `caps.probe_gpu_hours`; the switch refusing a missing, duplicate or
    unequal `p4_probe_gpu_hours:` line, a `gpu_hours_cap:` without P4-PROBECAP A or with another value, and a missing
    or incomplete `label_table_binding:`;
  - **F5 and the fill hook:** both states of the shipped files; the fill on a copy; 12 refusals; a partly filled
    config.
- Related files, one at a time: `test_trackp_sft` 35 passed, `test_trackp_sft_test_eval` 48 passed, `test_trackp_p3`
  23 passed, `test_trackp_cli` 9 skipped. `test_c3_arms_freeze` (not changed; its synthetic world is reused) gives
  3 failed, 50 passed, 3 errors, the same lightgbm-absent failures as on the baseline.
- Desk commands on the tip: `p4_lib.py validate p4_spec.json` gives `ok`, 16.94 GPU-h, 24.41 slot-hours,
  `probe_gpu_hours: null`, `within_cap: true`. `validate --launch` and `validate --probe p4_probe_spec.json` each give
  `STOP: paper.commit must be filled` with rc 2. `bash -n p4_probe.sh` passes.
- Hashes on the tip:
  - `p4_spec.json`: `3f17e8dd0a429fb51da29848107996a6dc8e826bb2d17407ce7a9ce070e828d6` (was `04cfd060…`; new
    `caps.probe_gpu_hours` and comment);
  - `p4_probe_spec.json`: `23db13491818577a1d6f506cce5696e27bcd8d8d3b7583e00765519e6346f75a`;
  - the host config: unchanged, `18f18cfc…`.

**Full suite** (`/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`,
`AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, `PYTHONDONTWRITEBYTECODE=1`, lightgbm not installed, a fresh `TMPDIR` per run,
started only when no other `r1/tests` suite was running):

| run | checkout | result |
|---|---|---|
| baseline | detached clean `912a7e02` (worktree removed afterwards) | 58 failed, 3972 passed, 197 skipped, 3 errors (559 s) |
| tip | `0824e8683` (this unit's code `79de467ea` plus its docs commit) | 58 failed, 4002 passed, 197 skipped, 3 errors (512 s) |

The sorted `FAILED`/`ERROR` node ids, with the ` - message` suffix cut, are `FULLSUITE_BASE_912a7e02.txt` and
`FULLSUITE_F2_PROBE_TIP.txt` beside this report. They are **identical** (61 lines each): zero new failures. The 30
extra passes are the new tests of `test_trackp_p4_runner.py` (89 collected at `912a7e02`, 119 at the tip).

## 5. What the cluster does next (order)

1. **T1** (read-only NEMO2 H200 job, plan §3.3): the `VERSIONS.txt` sha256 and the two unscoped `nvidia-smi` queries
   (F3). If more than one GPU or a process is listed, STOP S6: the probe is not run.
2. **Host-config fill commit** (§6 step 4):
   - `p4_fill_host_config.py --template > host_fill.json`;
   - confirm and fill every value on the host (the four unused bases as the chat decides);
   - `p4_fill_host_config.py host_fill.json --dry-run`, then without `--dry-run`;
   - commit the host config together with `docs/r1/reports/trackp_p4_cluster_<date>/host_fill.json`. No test needs a
     change. The commit is reviewed and merged on `main`. This unit must already be on `main`: the probe clones that
     commit, and the job refuses a clone without `p4_probe_spec.json`.
3. **T3** on that commit: `--check-config` clean, the file sha256, `check_local_paths`.
4. **The filled probe spec:** a copy of `p4_probe_spec.json` with `paper.commit` (the fill commit), `versions_sha256`
   (T1) and `host_config.sha256` (T3). Check it with `p4_lib.py validate --probe <copy>`.
5. **The probe**, after the author's gates of S4. The v2.2 run-record review is still pending (F8):
   - from a checkout whose `p4_lib.py`, `p4_probe.sh` and probe template equal the fill commit's, with `origin/main`
     freshly fetched (the render checks all of this, and the host config's sha256 at `paper.commit`, before staging;
     the job checks the first two again), `p4_render_jdl.py <copy> <new stage> --table <T> --probe --arm kev-0.8b`.
     Staging appends one entry to `/ceph/srv/dwong/paperb/trackp_p4/<probe run id>/_submissions.jsonl`, charged at
     7200 s until the attempt is sealed;
   - the pre-submit check, then **exactly one** `condor_submit p4probe_kev-0.8b.jdl` from that stage directory (never a
     second submission of a stage; a repeat is a new stage). A job that never ran is sealed from its stage directory
     (`p4_lib.py seal <stage dir> <copy> --arm <arm>`; its `STAGE_MANIFEST.json` marks it a probe attempt, 2 h);
   - when it has left the queue: `p4_lib.py seal <out> <copy> --arm kev-0.8b` (T7's records are in it);
   - then, one stage each, `kev-4b`, `qwen3.5-0.8b-base` and `qwen3.5-4b-base` with
     `--first-record <sealed kev-0.8b>/job_record.json`, each sealed.
6. **The record:**
   - write `wallclock.json` (`trackp_p4_condor_wallclock/1`: for every sealed attempt of every probe run, its
     `ClusterId` and `condor_history -af RemoteWallClockTime`, keyed `<arm>/attempt-<N>`);
   - `p4_lib.py probe-record <copy> r1/scripts/htcondor/trackp_p4/p4_spec.json <the four sealed attempts>
     --wallclock wallclock.json --out docs/r1/reports/trackp_p4_probe_<date>/probe_records.json` (add
     `--t1-wallclock <seconds>` only if the author takes P4-T1CHARGE option A). It refuses while any probe submission
     is unsealed, charges each attempt the larger of its record and its wall clock, writes those charges once into
     `/ceph/srv/dwong/paperb/trackp_p4/<probe run>/_wallclock.json` and binds its sha256 in `probe_records.json`
     (`charge_files`), and prints one `p4_probe_charge_file: <run> <file> <sha256>` line per charge file.
     **Re-run sequence:** the charge files are written before `probe_records.json`. If the command stops after writing
     them (for example, the output cannot be written), run it again with a new `--out` and a wall-clock input that no
     longer names the runs that now have a charge file (their charges come from the file; naming them again is a STOP);
   - after the record, staging into the recorded probe run is refused. A re-probe needs a new run id in the template
     `p4_probe_spec.json` (a reviewed commit); the old run's charges stay counted through its charge files. An attempt
     sealed into the recorded run anyway blocks the launch until it is recovered:
     `p4_lib.py probe-charge <run> --wallclock <json naming exactly the run's unrecorded attempts>` writes, once,
     `_wallclock.<n>.json`; then rebuild the record (`probe-record` with a new `--out` and a wall-clock input without
     that run) and carry its new P, charge-file lines and hours into the spec and the note. The record keeps using the
     first STOP-free attempt of each arm; later attempts are only charged;
   - write `H200_SFT_PROBE_<date>.md` with the printed lines (each alone on its line: four `p4_estimate_hours:`, one
     `p4_probe_gpu_hours:` and one `p4_probe_charge_file:` per charge file) and the prose of §4.4;
   - commit, under `docs/r1/reports/trackp_p4_probe_<date>/`, the filled probe spec copy, `wallclock.json`,
     `probe_records.json` and the Markdown record.
7. **Spec-fill commit** (§6 step 9): every §5.1 field, and now also `caps.probe_gpu_hours = P`, `estimate.hours` and
   `caps.probe_charge_files` (the record's `spec_probe_charge_files`) from the printed lines; the note's new field
   `probe_charge_files:` names each run and every charge file's sha256. Then T8 and the note (`gpu_hours_cap:` with `probe_gpu_hours: P`).

## 6. Points for the reviewer and decisions for the author

1. **Decision P4-T1CHARGE (author).** T1, the read-only H200 job of minutes, uses GPU time before the probe.
   - **Option A** (the reviewer's recommendation): add T1's `RemoteWallClockTime` to the probe charge. It is built as
     a switch: `probe-record --t1-wallclock <seconds>` adds it to `p4_probe_gpu_hours`, and the record says so
     (`t1_charged`).
   - **Option B** (as built, the default): leave T1 out; only probe attempts are charged. The draft's "host checks"
     sat inside its under-2-GPU-h allowance.
2. **Probe walltime 7200 s per base** (the plan's proposal), and the charge of a killed attempt is 2 h, or its wall
   clock if larger. Four killed attempts would charge at least 8 GPU-h. `probe-record` flags anything over 2 GPU-h
   (S12). The reviewer found 7200 s fine.
3. **Values the hook forces where §5.2 said "suggested":** `hf_home = hf`, `models_dir = models`, `runs_dir = out`.
   They match what the job actually uses: `offline_env`, `stage` and the lease log inside `out.tar`. The unused bases
   are only required to be job-relative. (The chat to confirm.)
4. **A new required note field, `label_table_binding:`**, which the switch checks. Signing the note ratifies the F2
   binding in the note itself. (Author, at signature.)
5. **The probe charge sums every probe run**, not only the one probe spec given, and rounds up to 0.01 h. This is the
   conservative reading of P4-PROBECAP A.
6. **The v3-pin receipt is now refused.** It was the only form the accepted runner admitted. No such receipt exists.
7. **A probe STOP keeps its class** (`ArmStop`, `ProtocolStop`) when it is raised. `run_job` raises a plain `Stop`, as
   before. This does not change exit codes: the CLI returns 2 for both.
8. **Incidental reading during authoring.** To find the identity file A3 consumed, I read
   `docs/r1/reports/arms_a3_20261123/RUN_I.md`. Its A3 section lists PRE-SELECT dev-population values (A3's
   `dev_values` per fold). These are dev selection numbers in a committed report, not sealed data or evaluation
   values. Nothing from them is used or copied here. I also read the committed identity result
   (`feat_one_identity.json`: ids and field paths, no values) and, from the receipt's committed copy, its key names and
   `inputs` / `source` / `stage` / `outputs` names. No label file, `*block.jsonl` or `b1_manifests.json` was opened, and
   every grep named its paths.

## 7. Review round 1 (`51860ca3`, NOT ACCEPTED): findings and fixes

The review (`/tmp/revtexts/p4f2_r1.md`, to be filed with the review record) confirmed F2, the probe's safety, F3/F4,
the fill hook and F5. The fixes are in `45575c526`:

| finding | fix |
|---|---|
| **M1** the probe charge is a snapshot of `caps.probe_gpu_hours` | New `p4_lib.check_probe_ledger(spec, sealed_root)`: `ceil_hundredth(probe_charges(sealed_root)["total"])`, which covers every probe run's sealed attempts and pending submissions, must not exceed `caps.probe_gpu_hours`, else a STOP. `assemble` and `p4_switch.check_cap` call it (`check_cap` before every submission) and report it (`probe_ledger`). Tests: the tree equal to the spec passes; a probe attempt sealed after the record, a pending submission and a lower spec value are each refused. |
| **M2** a probe submission is recorded nowhere | `stage_probe` appends one entry (`arm`, `kind: probe`, stage, spec sha256, UTC) to `<sealed_root>/<probe run id>/_submissions.jsonl`, as its last step (a refused stage records nothing). `charged_hours` / `pending_submissions` price an entry with no sealed attempt at the probe's `walltime_s` (`_requested_walltime_s`), and `probe_charges` reports `pending`. `probe-record` refuses while anything is pending. The render docstring and §5 step 5 say: exactly one `condor_submit` per stage directory, and a job that never ran is sealed from its stage directory. Tests: staging records the entry and it is charged 2 h; a refused stage records none; `probe-record` refuses with a pending entry. |
| **m1** GPU-hours from the Python start only | `probe-record --wallclock <json>` is required (schema `trackp_p4_condor_wallclock/1`, `RemoteWallClockTime` per `<arm>/attempt-<N>` of every sealed attempt of every probe run; a missing or extra attempt, an extra run or a bad value is a STOP). Each attempt is charged the larger of its receipt and its wall clock. Tests. |
| **m2** `seal` cannot tell a killed probe from a killed P.4 job | `attempt_kind`: the record's schema or `mode`, else the first wrapper line of `p4_run.log` (`P4 probe container job start` / `P4 container job start`). A kind other than the spec's is a STOP. An attempt showing neither is sealed only with `--unknown-kind-confirmed` and charged the larger of the probe's and the arm's walltime. The receipt records `kind`. Tests: a killed probe refused with the P.4 spec, a killed P.4 job refused with the probe spec, an unknown attempt refused, then sealed at 2 h. The P.4 seal tests now carry the wrapper's log line, as a real killed job does. |
| **m3** the filled-state F5 test checked only the 19 values | `_host_config_state` restores the 19 placeholders (the full original `venv.causal_conv1d` text) and requires the sha256 of the result to be `18f18cfc…`, in both states. A fill that also changes another key fails (tested). |
| **m4** no desk-side pre-submit binding | `p4_render_jdl.check_probe_binding`, run by `stage_probe` before anything is staged: `ls-remote` equals the local `origin/main`; `paper.commit` is an ancestor of it; this checkout's `p4_lib.py`, `p4_probe.sh` and `p4_probe_spec.json` equal `git show <paper.commit>:…`; `host_config.sha256` equals the sha256 of the host config at `paper.commit`. Tested on a temporary git origin (pass, wrong host sha256, a later `p4_lib.py`, an unpublished commit, a stale `origin/main`). |
| **m5** `render_probe` copies `render()`'s lines | Test: every line of `render()` other than the job-specific ones (comment, executable, arguments, log/output/error, walltime, input list) appears unchanged in `render_probe()`, and no other shared line is added. |
| **m6** the status note said "unchanged" | The heading now says the inline markers on F1, F2, F5 and F7 were added. |
| nit: several `probe_gpu_hours:` values | `check_binding` requires exactly one, equal to the spec's (tested both orders). |
| nit: `probe_run_summary` | It also checks lr and seed against the probe block and requires `stopped_at`, `completed: true` and `early_stopped` (tested). |
| nit: note wording | `label_table_binding:` and the STOP list now name each refusal of A3's join (a label outside the table, on a duplicate or test row, a duplicate label row, a non-inert non-duplicate train/dev row without its label row). |
| nit: `_paths` ambiguity check could not fail | `_paths` now lists leaves and refuses two with the same dotted spelling (tested). |
| nit: report §5 step 6 | The filled probe spec copy, `wallclock.json`, `probe_records.json` and the record go under `docs/r1/reports/trackp_p4_probe_<date>/`. |
| nit: `p4_probe.sh` not bound | Bound at the desk (m4) and in the job: `probe_code_binding` compares the transferred `p4_probe.sh` with the clone's (tested). |
| nit: per-attempt rounding to 4 decimals before the ceiling | Left as is (at most 0.0001 GPU-h per attempt; noted here). |

**Tests after the fixes**, one file at a time: `test_trackp_p4_runner` 126 passed, `test_trackp_sft` 35 passed,
`test_trackp_sft_test_eval` 48 passed, `test_trackp_p3` 23 passed, `test_trackp_cli` 9 skipped, `test_c3_arms_freeze`
3 failed and 3 errors (the lightgbm-absent baseline). Desk: `validate p4_spec.json` unchanged (16.94 GPU-h, within the
cap); `probe-record` without `--wallclock` is refused by argparse; `bash -n p4_probe.sh` passes.

**Full suite after the fixes** (same command and options as §4, a fresh `TMPDIR` deleted after the run, started only
when no other `r1/tests` suite was running). `main` had not moved, so the baseline is the §4 run on `912a7e02`:

| run | checkout | result |
|---|---|---|
| baseline | detached clean `912a7e02` (§4) | 58 failed, 3972 passed, 197 skipped, 3 errors |
| tip | `45575c526` (code after round 1) | 58 failed, 4009 passed, 197 skipped, 3 errors (478 s) |

The sorted lists `FULLSUITE_BASE_912a7e02.txt` and `FULLSUITE_F2_PROBE_TIP_R1.txt` are **identical** (61 lines): zero
new failures. The 37 extra passes are the runner tests (89 at `912a7e02`, 126 now).

### Round 2 (`1d51c578`, NOT ACCEPTED): findings and fixes

The review (`/tmp/revtexts/p4f2_r2.md`) verified every round-1 fix. The fixes are in `493122fc5`:

| finding | fix |
|---|---|
| **R2-M1** the launch check re-derived from receipts only, while P used max(receipt, wall clock) plus T1, so a small later attempt fitted in the gap | `probe-record` now writes, once (`open("x")`), one charge file per probe run whose wall clocks came from its input: `<sealed_root>/<run>/_wallclock.json`, schema `trackp_p4_probe_charges/1`, with each attempt's receipt hours, `RemoteWallClockTime`, `ClusterId` and the charge used, and T1's charge (if given) in the record's own run. Their sha256 are bound in `probe_records.json` (`charge_files`). `probe_charges` applies a run's charge file by default; an attempt the file does not name is charged at least its receipt and listed as `unrecorded`. A wall-clock input that names a run that already has a charge file, or T1 given twice, is a STOP. `check_probe_ledger` (in `assemble` and `check_cap`) STOPs on any unrecorded attempt, on any pending submission, and on a re-derived charge above P. For the recorded attempts the re-derived value equals P (tested on the CLI output). The CLI also refuses to write a record while any attempt lacks a wall clock. Test with exactly the reviewer's case: P = 0.60 from a 0.30 h receipt and a 2160 s wall clock; receipts alone with a later 0.25 h attempt would give 0.55; with the file the tree gives 0.85 and the check STOPs. |
| **R2-m1** an unknown kind with a readable record of neither schema charged its own `gpu_hours` | Charged `max(record gpu_hours, the larger of the probe's and the arm's walltime)` (tested with 0.01 h giving 2 h and 5 h giving 5 h). |
| **R2-m2** a never-submitted probe stage was charged at the P.4 arm walltime | `attempt_kind` also reads the stage's `STAGE_MANIFEST.json`: `trackp_p4_probe_stage/1` with mode `probe` is a probe attempt (2 h); a non-preview `trackp_p4_stage/1` is a P.4 attempt. The render docstring and §5 step 5 now say how to seal it, with no confirmation flag. Tested: sealing the stage clears the pending entry and charges 2 h; the P.4 spec refuses it. |
| nit: `TimeoutExpired` from `ls-remote` / `git show` | Wrapped as a STOP (tested). |
| nit: ledger order | The stage is written, then the ledger appended; if the append fails, the stage directory (which this call created, empty or absent before) is removed and the call STOPs. So no stage exists without its ledger entry, and no ledger entry without its stage (tested). |
| nit: the killed-job test comment | Now names the wrapper's first log line. |

**Tests after round 2**, one file at a time: `test_trackp_p4_runner` 131 passed, `test_trackp_sft` 35 passed,
`test_trackp_sft_test_eval` 48 passed, `test_trackp_p3` 23 passed, `test_trackp_cli` 9 skipped, `test_c3_arms_freeze`
3 failed and 3 errors (the lightgbm-absent baseline). `validate p4_spec.json` unchanged; `bash -n p4_probe.sh` passes.

**Full suite after round 2** (same command, fresh `TMPDIR` deleted after the run, started only when no other
`r1/tests` suite was running; `main` still `912a7e02`, so the §4 baseline is reused):

| run | checkout | result |
|---|---|---|
| baseline | detached clean `912a7e02` (§4) | 58 failed, 3972 passed, 197 skipped, 3 errors |
| tip | `493122fc5` (code after round 2) | 58 failed, 4014 passed, 197 skipped, 3 errors (512 s) |

`FULLSUITE_BASE_912a7e02.txt` and `FULLSUITE_F2_PROBE_TIP_R2.txt` are **identical** (61 lines): zero new failures. The
42 extra passes are the runner tests (89 at `912a7e02`, 131 now).

### Round 3 (`4706de7d`, NOT ACCEPTED): findings and fixes

The review (`/tmp/revtexts/p4f2_r3.md`) verified the round-2 fixes. The fixes are in `5562a5cd6`:

| finding | fix |
|---|---|
| **R3-M1** an attempt sealed into a recorded probe run could never be recorded, so the launch stayed blocked | **(a)** `stage_probe` refuses a probe run that already has a charge file; the message, the render docstring and §5 say a re-probe needs a new template run id (a reviewed commit). **(b)** Recovery: `p4_lib.py probe-charge <run> --wallclock <json>` (`supplement_charges`). The run must have its `_wallclock.json` and no pending submission; the input must name exactly the run's currently unrecorded attempts, and only that run. It writes, once, `_wallclock.<n>.json` (the next `n`; schema `trackp_p4_probe_charges/1` with `supplement: n`; each attempt charged the larger of receipt and wall clock). `probe_charges` applies the base file and every supplement in order. A gap in the numbering, another `_wallclock*` name, a supplement carrying T1, an attempt named twice, or a charge file naming an attempt that is not sealed is a STOP. A rebuilt probe record (with a wall-clock input that does not name that run) gives the new P and lists every charge file. So that the rebuild can use the measured attempts, the record now takes the **lowest-numbered** STOP-free attempt of each arm and only charges later ones. The rule is fixed in advance, so nothing is chosen by result; it replaces "no other STOP-free attempt", for the reviewer to confirm. **(c)** End-to-end test: the record; the refused stage; a STOP-free attempt sealed into the recorded run by hand (the reviewer's demonstration); the launch STOP; the refused wall-clock input that names the run; the refused record with an unrecorded attempt; `probe-charge` refusals (empty, an extra attempt, another run); the supplement; a second `probe-charge` refused; the stale spec refused; the rebuilt record (new P, both files in the lines and in `spec_probe_charge_files`, the first attempts used); and the launch check passing with the new spec. Plus unit tests of the refusals, the ordering and double naming. |
| **R3-m1** a changed charge file was not detected at launch | A new spec field `caps.probe_charge_files` (`{<probe run>: [<sha256>, …]}`, in file order): a placeholder until the spec-fill commit, required at launch as a dict of probe run ids to non-empty 64-hex lists. `probe-record` prints one `p4_probe_charge_file: <run> <file> <sha256>` line per charge file and writes `spec_probe_charge_files` into `probe_records.json`. The switch's `check_probe_charge_files` requires the record's lines (no duplicate, no gap, at least one) to equal the spec's listing. A new required note field `probe_charge_files:` must name every run and give exactly the listed sha256. `check_probe_ledger` (in `assemble` and `check_cap`, now run at the cap step after their other refusals) requires the charge files on disk to equal the spec's listing exactly. Tested: a zeroed file, a deleted file and an added run's file are each refused by `check_probe_ledger` and by `check_cap`; record, spec and note mismatches are refused. |
| nit: a symlinked or pre-existing stage directory on failure | A symlinked `stage_dir` is refused up front. On any failure while staging (the ledger append included), only the files this call wrote are removed, and the directory only if this call created it; a pre-existing empty directory is kept. A failure inside the cleanup ends as a STOP that says to remove the stage by hand. Tested. |
| nit: the re-run sequence | §5 step 6 says the charge files are written before `probe_records.json`, and how to re-run. |

The test fixtures now include a synthetic recorded probe run matching `filled()` (`caps.probe_charge_files`, and
`probe_gpu_hours` 0.5), because every `assemble` and `check_cap` call now checks the charge files.

**Tests after round 3**, one file at a time:
- `test_trackp_p4_runner`: 138 passed.
- `test_trackp_sft`: 35 passed.
- `test_trackp_sft_test_eval`: 48 passed.
- `test_trackp_p3`: 23 passed.
- `test_trackp_cli`: 9 skipped.
- `test_c3_arms_freeze`: 3 failed and 3 errors (the lightgbm-absent baseline).

Desk: `validate p4_spec.json` is unchanged (16.94 GPU-h, within the cap); `validate --probe` on the template stops at
`paper.commit`; `bash -n p4_probe.sh` passes.

**Full suite after round 3** (same command; a fresh `TMPDIR`, deleted after the run; started only when no other
`r1/tests` suite was running). `main` is still `912a7e02`, so the §4 baseline is reused:

| run | checkout | result |
|---|---|---|
| baseline | detached clean `912a7e02` (§4) | 58 failed, 3972 passed, 197 skipped, 3 errors |
| tip | `5562a5cd6` (code after round 3) | 58 failed, 4021 passed, 197 skipped, 3 errors (507 s) |

`FULLSUITE_BASE_912a7e02.txt` and `FULLSUITE_F2_PROBE_TIP_R3.txt` are **identical** (61 lines): zero new failures. The
49 extra passes are the runner tests (89 at `912a7e02`, 138 now).
