# P.4 off HTCondor: the direct launch path under R1-HOST-FREE (card local/20261126-06, unit 1)

ENGINEERING_ONLY; AI-assisted (Claude, the local worker), 26-27 Nov 2026. Branch `mac-p4-direct-20261126`, built on
`origin/main` 54082a05 and merged with `origin/main` 47df6f55. Tier E. To be reviewed by a fresh agent.

## Content

Track P P.4 phase 1 no longer depends on the HTCondor pool. The spec (`p4_spec.json`, and the probe template
`p4_probe_spec.json`) replaces the fixed `gpu_model` by admitted **host classes** (`hosts`): `nemo2_h200`
(NVIDIA H200, 9.0, HTCondor, `trackp_htcondor_v2.json`) and `ada_rtx6000` (NVIDIA RTX 6000 Ada Generation, 8.9,
direct launch, the new `r1/scripts/configs/trackp_ada_v1.json` with 26 `TODO_VERIFY_ON_HOST` values), each with its
own host config and its own SFT probe estimate. Each job is told its class (third argument of `p4_job.sh` /
`p4_probe.sh`, `--host-class`), admits exactly one GPU of that class's name and compute capability, and a direct job
must run on the card its launcher leased (`P4_LEASED_GPU_UUID`); the record names class, host, GPU model, UUID,
driver, env3 freeze and the card's other compute processes at start and end. The env3 freeze check
(`r1/c3/train/p4_phase1.py`) is untouched. The new host-side launcher `p4_direct.py` (stdlib, Python 3.6+) is run by
the compute agent over SSH on Ada from the same canonical stage as an HTCondor job (same `TRANSFER_INPUTS`, a
descriptor `p4direct_<arm>.json` in place of the JDL): it checks the stage against its manifest and the host name,
requires the switch's once-only marker for a P.4 job, launches a stage once, creates a fresh job directory, takes the
GPU lease (`flock -n` on `<lock_dir>/gpu<N>.lock`; busy is a refusal), checks the card's model and free memory, copies
the inputs, runs the entry script in the digest-pinned image v2.2 through apptainer (`--nv --nvccli`) or docker
(`--gpus device=<uuid>`) only, with only the leased card visible, as the calling non-root user, without any time
limit, and writes `direct_launch.json` (`trackp_p4_direct_launch/1`). `seal` accepts a direct attempt, binds its
launcher record and charges GPU-hours on any card; `charged_hours`, the probe charges and the charge files sum
HTCondor and direct attempts; `assemble` records each arm's class and card. The fill hook fills per class
(`trackp_p4_host_fill/2`, `--template --host-class ada_rtx6000`; the H200 class keeps `/1` and its 19 paths). The
switch's checks apply to direct stages (canonical descriptor, `p4_direct.py` byte-equal, note key lines per class)
and its `submit` of a direct stage writes the marker and ledger entry and starts nothing. The phase-1 note draft is
revised to R1-HOST-FREE and rows (g) (`approved: false`).

## Rows (g) applied (coordinator's message; R1-NO-TIMEOUT, R1-STEP-ORDER, R1-CARD-SHARE)

1. **No time limit decides an attempt.** HTCondor's `+RequestWalltime` stays a scheduler request only (the 86,400 s
   check now applies only to HTCondor classes, as a request); a direct launch has no limit (`proc.wait()` without a
   timeout); a walltime kill (no readable record) is sealed with `stop_class: infrastructure` as before. Said in the
   `p4_lib` and `p4_direct` docstrings, the descriptor (`walltime_rule`) and the note draft (`job_layout:`, STOPs).
2. **40 GPU-h and 64 slot-h are reporting thresholds (R1-NO-TIMEOUT (3)), on both paths.** `validate_spec`,
   `p4_switch.check_cap`, `probe_records` and `assemble` no longer refuse for the figures; they return
   `threshold` (`threshold_report`: usage, the figures, `reached`, `report_to_author`), the switch prints
   "REPORT TO THE AUTHOR" to stderr and carries the report in the marker/ledger/submission entry. The spec's
   `caps.probe_gpu_hours` no longer has a 40 upper bound. Ledger integrity checks (`check_probe_ledger`) still refuse.
   The change was small enough to make for the HTCondor path too, so there is no follow-up.
3. **Free memory, not an empty card (R1-CARD-SHARE (1)).** The launcher refuses a card whose free memory is below the
   host config's `direct.min_free_mib` and otherwise runs beside other processes (`card_shared` recorded);
   `p4_direct.py cards` lists free memory and processes so that the agent takes an empty card first. Our own GPU lease
   (`flock`) still keeps two of our P.4 jobs off one lease. Inside the job, `trackp.py` skips its foreign-process
   check for `"lease": "direct_gpu_lease"` (the H200 `htcondor_slot` path is unchanged).
4. **Other compute processes at start and end (R1-CARD-SHARE (4)).** Every job record (both paths) carries
   `card_processes_start` / `card_processes_end` (count and memory, from inside the job; a failed query is recorded);
   the direct launcher records `other_processes_start` / `other_processes_end` host-side, and the seal receipt copies
   them.
5. **A loss beside another process is infrastructure (R1-CARD-SHARE (3)).** An arm STOP (CUDA OOM) with another
   compute process on the card at start or end is reclassified `infrastructure` with `lost_beside_another_process`
   (in the job record, and again at seal from the launcher's host-side counts); an interrupted or refused direct
   launch is infrastructure too. Each is repeated in a new stage and attempt directory, never resumed.

## Decided alone (level 0)

- Spec shape: `hosts.<class>` = {launch, gpu_name, compute_capability, host_config, estimate}; the top-level
  `gpu_model`, `host_config` and `estimate` are refused (no compatibility layer). A probe spec names its one class
  (`host_class`, a fifth filled template field); one probe run holds stages of one class only.
- The job learns its class from an explicit argument (JDL `arguments` and descriptor), never from the landed GPU; the
  HTCondor JDL bytes change accordingly (nothing was ever staged or submitted with the old ones).
- Running class kept in a scoped module context (`_job_host`) so the existing job steps read the class's host config
  without changing their signatures (the H200 class outside a job, as before).
- Projection and walltime bound take each arm at its largest estimate over the admitted classes (conservative).
- At launch strength every admitted class needs a filled host config and its own probe record; to launch on Ada only,
  the launch spec admits only `ada_rtx6000` (the note's `h200_sft_probe:` then reads `none`).
- Direct charge: complete launcher record = max(lease span / 3600, record `gpu_hours`); incomplete record (launcher
  killed) = max(launch start to seal, the requested walltime bound, record hours) because nothing bounds a direct
  job's wall clock; no launcher record while the job record names a direct class = STOP; malformed record = STOP.
- Launcher: stdlib Python (not bash) for testable JSON and lease handling; apptainer with `--nvccli` and docker with
  `--gpus device=<uuid>`, both keep the job's unchanged "exactly one GPU visible" rule; a SIGTERM/SIGINT/SIGHUP stops
  the container (`docker kill`) and is recorded.
- `trackp.py` treats `"lease": "direct_gpu_lease"` like `htcondor_slot` (no Track X STATUS read) and skips the in-job
  foreign-process check there (rows (g) 3).
- Direct ordering of probe attempts uses the ledger entry's stage-manifest sha256 (the receipt carries it from the
  launcher record).
- Existing tests edited only where the behaviour changed by design (spec shape, the class argument, the note's host
  lines, the cap now reported); they pass at tip (with torch, see below).

## Needs a decision (level 1 or 2)

**D1. Arms on different GPU models in one P.4 assembly.** The code admits it and records `gpu_models` and
`mixed_gpu_models` (the card's reading of R1-HOST-FREE (1): "the GPU model is recorded, not fixed; one arm's training
run stays on one card"; (2)(a) binds only bit-identical comparisons; (2)(c) is for closed-loop instances).
Options: A, admit and record (built); B, require one GPU model across the four arms (`assemble` refuses mixed models;
one line). Recommendation: A, because the arms are compared by readiness intervals, not bit for bit, and the paper
states hardware per row (R1-HOST-FREE (4)). Draft row text: "R1-P4-ARMS-HW (coordinating chat, under R1-AUTONOMY): the
four P.4 phase-1 arms may run on different admitted GPU models; the assembly records each arm's model, and the P.4
report states it."

**D2. Released train/dev labels on a shared host.** A direct P.4 job stages `label_block.traindev.jsonl` and its
`RECEIPT.json` on Ada (as HTCondor transfers them to a NEMO2 worker), in a 0700 job directory of the user `dowling` on
a host other users share. Options: A, allowed (train/dev is released by R1-S2-LABELS-TRAINDEV-RELEASE; copy with
owner-only modes); B, P.4 jobs that read labels stay on hosts without other users. Recommendation: A, with the
`rsync --chmod` below; level 1 unless the coordinator reads the release row otherwise.

**D3 (minor, level 1).** The per-arm estimate sanity range stays (0, 20] h per class; a 4B arm on a slower card above
20 h would be refused at validation. Recommend keeping it until the Ada probe gives numbers.

## Tests

- New `r1/tests/test_trackp_p4_direct.py` (no torch; 36 tests): shipped specs and classes; spec refusals (old
  `gpu_model`, top-level blocks, unknown/altered class, per-class estimate labels, `host_class` in a launch spec);
  slowest-class projection and the HTCondor-only walltime request; reporting thresholds; `gpu_identity` per class;
  lease binding; card processes and loss reclassification; the canonical descriptor and its refusals; the JDL's class
  argument and wrapper syntax; the launcher end to end with fakes for nvidia-smi, the runtime and the clock and a real
  `flock` (job dir, inputs, record, docker argv, lease held during the run and released, once per stage, refusals:
  host name, card model, free memory, busy lease, changed file, preview, runtime, unpinned image, relative paths,
  `min_free_mib`), sharing a card with enough memory, the switch marker for P.4 jobs, signals, apptainer argv,
  `cards`; seal of direct attempts (charge, record hours larger, incomplete record, refusals, OOM beside another
  process, refused launch); probe charges and charge files with direct attempts; switch key lines per class; probe
  hours per class; the per-class fill hook (H200 form unchanged, Ada's 26 values, refusals); `trackp.py`'s lease.
- `r1/tests/test_trackp_p4_runner.py` (needs torch): fixtures moved to the new spec shape; three new tests: a job on
  Ada (class, card, lease, processes, OOM beside another process, missing lease, class not admitted), assembly with
  mixed models and its one-card refusals, and the direct path end to end (stage on Ada, switch check, two-key submit
  with no `condor_submit`, marker and ledger, launcher, seal, charges).
- With torch (`~/anaconda3/envs/hupdate`, torch 2.11): `test_trackp_p4_runner.py` 159 passed at tip (157 at base);
  `test_trackp_p4_direct.py` 36 passed.

## Full suite (anaconda Python, no torch; fresh TMPDIR each, one at a time)

`TMPDIR=<fresh> PYTHONDONTWRITEBYTECODE=1 AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness python -m
pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`

| Tree | Commit | Result |
|---|---|---|
| base | `origin/main` 47df6f55 (detached worktree) | 178 failed, 3929 passed, 165 skipped, 26 errors |
| tip | this branch (df6aef36 merged with 47df6f55) | 178 failed, 3965 passed, 165 skipped, 26 errors |

The sorted FAILED/ERROR id lists are identical (204 ids each): **zero new failing test ids at tip**; the 36 extra
passes are `test_trackp_p4_direct.py`. The known failures are the environment's (no torch: `test_trackp_p4_runner.py`
and other torch-importing modules fail to collect in this Python); the runner tests were run with torch separately
(above).

## Operator commands for the compute agent

Paths are examples; `<sealed root>` is `/ceph/srv/dwong/paperb/trackp_p4` on deepthought, where `seal`,
`probe-record` and the switch run. `P=r1/scripts/htcondor/trackp_p4`.

**(a) Fill the Ada host config from the survey (compute/20261126-01)** — in a checkout of `main`, on a branch:

    python $P/p4_fill_host_config.py --template --host-class ada_rtx6000 \
        > docs/r1/reports/trackp_p4_ada_<YYYYMMDD>/host_fill_ada.json
    # replace every FILL value from the survey: direct.container_runtime (apptainer with --nvccli, or docker usable
    # without sudo), direct.work_root (e.g. /data1/dowling/r1_trackp_p4/jobs), direct.lock_dir (e.g. ~/r1_locks),
    # direct.hostname (`hostname`, e.g. ucrtasl), direct.shm_size (e.g. 16g), direct.min_free_mib (46000 before the
    # probe), work_dir ".", gpu.lock_path "gpu0.lock", the four unused bases "models/<base>", venv.causal_conv1d
    python $P/p4_fill_host_config.py docs/r1/reports/trackp_p4_ada_<YYYYMMDD>/host_fill_ada.json \
        --host-class ada_rtx6000 --dry-run
    python $P/p4_fill_host_config.py docs/r1/reports/trackp_p4_ada_<YYYYMMDD>/host_fill_ada.json \
        --host-class ada_rtx6000            # prints the new sha256 of r1/scripts/configs/trackp_ada_v1.json
    git add r1/scripts/configs/trackp_ada_v1.json docs/r1/reports/trackp_p4_ada_<YYYYMMDD>/ && git commit

**(b) A direct probe on Ada (compute/20261126-07)**, after the fill commit is on `main`:

    # a filled copy of $P/p4_probe_spec.json: paper.commit = the fill commit on main, image.versions_sha256 = T1's
    # value, host_class = "ada_rtx6000", hosts.ada_rtx6000.host_config.sha256 = the sha256 from (a)
    python $P/p4_render_jdl.py probe_spec_ada.json /work/dwong/trackp_p4_direct/stages/probe_kev-0.8b \
        --table <sweep1_v3 table dir> --probe --arm kev-0.8b
    rsync -a --chmod=Du=rwx,Dgo=,Fu=rw,Fgo= /work/dwong/trackp_p4_direct/stages/probe_kev-0.8b/ \
        experiment_zhixu:/data1/dowling/r1_trackp_p4/stages/probe_kev-0.8b/
    ssh experiment_zhixu 'python3 /data1/dowling/r1_trackp_p4/stages/probe_kev-0.8b/p4_direct.py cards'
    ssh experiment_zhixu 'cd /data1/dowling/r1_trackp_p4/stages/probe_kev-0.8b && setsid nohup python3 p4_direct.py \
        launch --stage $PWD --arm kev-0.8b --gpu <free card> > launch_kev-0.8b.json 2>&1 < /dev/null &'
    # when launch_kev-0.8b.json shows the summary: copy back the five outputs of its job_dir
    rsync -a experiment_zhixu:'<job_dir>/{out.tar,job_record.json,SHA256SUMS,p4_run.log,direct_launch.json}' \
        /work/dwong/trackp_p4_direct/out/probe/kev-0.8b/<stamp>/
    python $P/p4_lib.py seal /work/dwong/trackp_p4_direct/out/probe/kev-0.8b/<stamp> probe_spec_ada.json --arm kev-0.8b
    # the other bases: --first-record <sealed root>/<probe run>/kev-0.8b/attempt-N/job_record.json at staging
    echo '{"schema": "trackp_p4_condor_wallclock/1", "runs": {}}' > wallclock_none.json   # direct: no HTCondor job
    python $P/p4_lib.py probe-record probe_spec_ada.json $P/p4_spec.json <sealed attempt dirs> \
        --out probe_records_ada.json --wallclock wallclock_none.json --t1-history

**(c) A direct arm job on Ada**, after the launch commit (spec admitting `ada_rtx6000` with its probe estimate) and the
signed note are on `main`:

    python $P/p4_render_jdl.py $P/p4_spec.json /work/dwong/trackp_p4_direct/stages/p4_ada_1 --table <table dir> \
        --partition <release root>/sweep1/traindev --host-class ada_rtx6000
    python $P/p4_switch.py check --stage /work/dwong/trackp_p4_direct/stages/p4_ada_1 \
        --note docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md
    TRACKP_P4_ENABLE_REAL=1 python $P/p4_switch.py submit --stage /work/dwong/trackp_p4_direct/stages/p4_ada_1 \
        --note docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md --enable --arm kev-0.8b
    rsync -a --chmod=Du=rwx,Dgo=,Fu=rw,Fgo= /work/dwong/trackp_p4_direct/stages/p4_ada_1/ \
        experiment_zhixu:/data1/dowling/r1_trackp_p4/stages/p4_ada_1/
    ssh experiment_zhixu 'cd /data1/dowling/r1_trackp_p4/stages/p4_ada_1 && setsid nohup python3 p4_direct.py \
        launch --stage $PWD --arm kev-0.8b --gpu <card> > launch_kev-0.8b.json 2>&1 < /dev/null &'
    # copy back the five outputs as in (b), then
    python $P/p4_lib.py seal <copied dir> $P/p4_spec.json --arm kev-0.8b
    # the other arms: submit with --first-record <sealed root>/trackp-p4-p1-20261122-a/kev-0.8b/attempt-N/job_record.json
    # from a fresh stage per repeat; an infrastructure loss is repeated from a new stage

## What remains

- The Ada survey and fill (a), then the Ada probe (b) with its review; the launch commit and the note's signature.
- The survey must confirm: `nvidia-smi` names the card exactly "NVIDIA RTX 6000 Ada Generation" with compute
  capability 8.9 (else the class's fixed values need a reviewed change); `python3` exists; docker usable without sudo,
  or apptainer whose `--nvccli` works unprivileged (otherwise the job sees all eight cards and stops at identity,
  fail closed); `ghcr.io` reachable for the image digest; free space under `/data1/dowling`.
- Job directories on Ada keep their staged models and clone; nothing is deleted by the launcher (rule 2). A cleanup
  rule for host scratch needs a decision when space runs short.
- The cluster test plan and the authorization draft still describe the H200-only path; a documentation unit should
  bring them to R1-HOST-FREE (the note draft is revised here).
- Unmerged `origin/p4-hostconfig-fill-20261126` touches only `trackp_htcondor_v2.json` and reports; it does not
  conflict, and its sha256 goes into `hosts.nemo2_h200.host_config.sha256` (not the removed top-level field).
