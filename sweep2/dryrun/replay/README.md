# S2-C3 replay dry-run staging (ENGINEERING)

Staged by `python3 sweep2/render_jdl.py sweep2/spec.replay.example.json --out
sweep2/dryrun/replay/s2_c3_replay_job.jdl --stage-dir sweep2/dryrun/replay/<tmp>` and copied here (the reviewed C2
convention). `s2_c3_replay_job.jdl` is the exact JDL the operator should dry-run; the staged files next to it are the
transfer-input set (source code, replay spec, reviewed label patch, criteria document and the 25 flattened pinned B2
replay inputs).

## `condor_submit` is not available on this machine

This unit was prepared on macOS, where `condor_submit` is not installed (`which condor_submit` → not found), so the
real `condor_submit -dry-run` **has not been done here**. It must be done later by the deepthought operator on the
submit host, from this directory:

    cd sweep2/dryrun/replay
    condor_submit -dry-run s2_c3_replay_job.jdl > s2_c3_replay_job.dryrun.txt

and the captured ad should show (C2-accepted values):

- `JobUniverse=5`, `WantContainer=true`, `ContainerImageSource=docker`,
  `container_image=docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…`;
- `RequestGPUs=1`, `RequestCpus=16`, `RequestDisk=50000000`, `RequestMemory=128000`, `RequestWalltime=7200`;
- `+RemoteJob=True`;
- requirements `CloudSite=BwForCluster-Nemo2 && GPUs_DeviceName="NVIDIA L40S" && Arch=X86_64 && OpSys=LINUX &&
  Cpus>=16 && CpuFamily=6 && CpuModelNumber=207`, plus the scheduler's `HasContainer && HasDockerURL`;
- **no** `ProvidesEtpCeph` requirement (NEMO2 slots do not advertise it);
- `TransferInput` = the 31 staged files; `TransferOutput=out,work,job_record.json,SHA256SUMS,llama-server.log`.

**Do not submit.** The replay preflight (see `docs/r1/reports/sweep2_20261116/S2_C3_UNIT.md`) is expected to STOP
at the B2 authorization gate before any server starts; the author decision is required first.

The per-node specs are `sweep2/spec.replay.example.json` (digits_mlp),
`sweep2/spec.replay.openml_credit_approval.json`, `sweep2/spec.replay.openml_ionosphere.json`; render each the same
way after any author-approved protocol change.
