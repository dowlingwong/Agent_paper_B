# S2-C3 replay dry-run staging (ENGINEERING)

Staged by `python3 sweep2/render_jdl.py sweep2/spec.replay.example.json --out
sweep2/dryrun/replay/s2_c3_replay_job.jdl --stage-dir sweep2/dryrun/replay/<tmp>` and copied here (the reviewed C2
convention). `s2_c3_replay_job.jdl` is the exact JDL the operator should dry-run; the staged files next to it are the
transfer-input set: the driver sources, replay spec, reviewed **label patch**, reviewed **driver shim**, the
pre-declared criteria document, the declared-inputs manifest + its 8 declared input files (Stage A tables, Stage A
prompt set, OpenML cache archive, pinned inputs SHA256SUMS, criteria, both patches) and the 24 flattened pinned B2 root
inputs — **37 transfer inputs** in total.

Round-2 refresh (review `docs/r1/reviews/S2_C3_DRIVER_REVIEW_20261116.md`, B1/M1): the JDL now carries the
author-accepted **32k layout** from the spec (`request_memory = 32000`, `request_disk = 42460977`,
`+RequestWalltime = 12203`; R1-SWEEP2-LAYOUT), and the staged `s2_c3_driver_shim.diff` is the re-reviewed shim with the
fourth hunk in `r1/scripts/exam_runner.py`.

## `condor_submit` is not available on this machine

This unit was prepared on macOS, where `condor_submit` is not installed (`which condor_submit` → not found), so the
real `condor_submit -dry-run` **has not been done here**. It must be done later by the deepthought operator on the
submit host, from this directory:

    cd sweep2/dryrun/replay
    condor_submit -dry-run s2_c3_replay_job.jdl > s2_c3_replay_job.dryrun.txt

and the captured ad should show (C2-accepted values):

- `JobUniverse=5`, `WantContainer=true`, `ContainerImageSource=docker`,
  `container_image=docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…`;
- `RequestGPUs=1`, `RequestCpus=16`, `RequestDisk=42460977`, `RequestMemory=32000`, `RequestWalltime=12203`
  (the author-accepted 32k layout, R1-SWEEP2-LAYOUT; the values are spec-declared, not renderer defaults);
- `+RemoteJob=True`;
- requirements `CloudSite=BwForCluster-Nemo2 && GPUs_DeviceName="NVIDIA L40S" && Arch=X86_64 && OpSys=LINUX &&
  Cpus>=16 && CpuFamily=6 && CpuModelNumber=207`, plus the scheduler's `HasContainer && HasDockerURL`;
- **no** `ProvidesEtpCeph` requirement (NEMO2 slots do not advertise it);
- `TransferInput` = the 37 staged files, including `S2C3_IN_DECLARED.json`, `S2C3_IN_stage_a_table_t7h8.json`,
  `S2C3_IN_stage_a_amendment_table_t7j10.json`, `S2C3_IN_prompts.jsonl`, `S2C3_IN_openml_cache.tar.gz` and
  `s2_c3_driver_shim.diff`;
- `TransferOutput=out,work,job_record.json,SHA256SUMS,llama-server.log`.

**Do not submit.** After independent review (`docs/r1/reports/sweep2_20261116/S2_C3_DRIVER.md`), the preflight must
report **exactly** the reviewed TASL refusal set in its unshimmed walk (no more, no fewer) and pass **all five** B2
authorization gates in its shimmed walk — including the Stage A pass-set/`_authorized_candidate` gate — before
fetching the model; an unexpected refusal or a missing expected refusal is a STOP with everything retained. The model
fetch and the ~19.6 GB GGUF download happen only after that preflight. Only the author's sweep-2/EVIDENCE gate may
authorise the actual 3 ENGINEERING jobs.

The per-node specs are `sweep2/spec.replay.example.json` (digits_mlp),
`sweep2/spec.replay.openml_credit_approval.json`, `sweep2/spec.replay.openml_ionosphere.json`; render each the same
way after any author-approved protocol change. The staged `s2_c3_spec.json` here is the digits_mlp one.
