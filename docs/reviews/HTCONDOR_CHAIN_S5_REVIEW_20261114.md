# Independent pre-submission review — S5 NEMO2 GPU job with our SIF, transferred by HTCondor (night of 14 Nov 2026)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent;
I did not write, submit or run anything and I have no cluster access.

**Date/time of review:** 14 November 2026, 11:35–11:58 CET (Europe/Berlin).

**Reviewed unit:** `docs/r1/reports/htcondor_chain_20261114/s5/{s5_nemo2_gpu_sif.jdl, s5_run.sh}`, committed at
`43b0ba8c` and unchanged at the worktree HEAD **`48e1e938`**, pinned below by SHA-256. Nothing of this unit has
been submitted (no job/log/queue entry in the worktree); the SIF does not exist yet (S3 build gated on its
re-review, chain report §S3), so checks that need the SIF or a dry-run are stated as **pre-submission gates**.

**Basis for the review.** Author instruction S5 and author supplement 2 as reflected in
`docs/r1/reports/HTCONDOR_CHAIN_20261114.md` (authority L3: write scope `/work/dwong/paperb/`,
`/work/dwong/htcondor_prep_20261114/`, `/ceph/srv/dwong/paperb/`; ≤10 concurrent jobs; ≤10 GPU-h; whole GPUs; no
deletion; supplement 2 L62–L76: a `gpu_availability.tsv` snapshot before every GPU submission, chosen model and
reason in the submission note beside `queue_times.tsv`); the chain plan text (L90: "S5 (NEMO2 L40S, same SIF
transferred by HTCondor): I4 CUDA/torch/llama-server plus the SIF-transfer method/size/time record"); the S2
results and raw NEMO2 container evidence (`s2/S2N1.out`, `s2_queue_times.tsv`); the image def/build plan at HEAD
(`r1/scripts/htcondor/apptainer/r1-htc.def` SHA `a5a0c9da…`, `build_sif.sh` SHA `d63c2a8e…`; SIF and identity
under `/work/dwong/paperb/images/`); `gpu_availability.tsv` snapshot 1 (11:21 CET); and upstream HTCondor 23.0
container-universe / `condor_submit` / file-transfer documentation and the job ClassAd attribute reference.

**Hard limits of this review.** No SSH, no HTCondor commands, no submission, no git commit/push, no file written
except this review. Current NEMO2/GPU state is taken from the committed snapshot 1; the SIF identity is not yet
known, so the size-dependent and dry-run-dependent checks are gates below, not findings.

---

## 1. Files reviewed and pinned (SHA-256)

| File | Bytes | SHA-256 |
|---|---|---|
| `s5/s5_nemo2_gpu_sif.jdl` | 530 | `9a7046160bff3834b3c00197cb130373b71637b3e6cca1809d51cc8f754381d9` |
| `s5/s5_run.sh` | 1980 | `66a8c5b07d98842e139be093ab36a7a4f7cf3a467e106c0c727e4ba01ca398c9` |

Supporting evidence read: chain report §S2, §S4/S5, §GPU availability, §S3; `s2/S2N1.out` (NEMO2 container
environment), `s2_queue_times.tsv`; `gpu_availability.tsv` snapshot 1 (11:21:10 CET); `r1-htc.def` /
`build_sif.sh` at HEAD; the S4 review+re-review for the shared conventions (sandbox vs `/work`, `htc_events`
recorder, `output`/`error`/`log`, record set).

---

## 2. Checks performed, and results

### 2.1 JDL against the S5 brief

| Field | Line | Value | Verdict |
|---|---|---|---|
| universe | L1 | `container` | ✓ container universe (S2 proved it on NEMO2) |
| container_image | L2 | `/work/dwong/paperb/images/r1-htc-20261114.sif` | ✓ absolute SIF path (readable on the access point); NEMO2 has no `/work` (S2N1: `df[/work]=MISSING`), so the image must be transferred |
| should_transfer_files | L4 | `YES` | ✓ |
| when_to_transfer_output | L5 | `ON_EXIT` | ✓ |
| transfer_input_files | L6 | `s5_run.sh` | ✓ |
| transfer_output_files | L7 | `s5_identity.txt, s5_env.txt, s5_nvidia.txt, s5_torch.txt, s5_llama.txt` | ✓ these are created in the job sandbox with relative names (script L8–L27) — unlike S4's case, this transfer list is correct |
| should_transfer_container | (absent) | default = transfer | ✓ intended for this step (the transfer is the experiment); see §2.2 |
| walltime | L8 | `+RequestWalltime = 1800` | ✓ |
| CPU / memory / disk | L9–L11 | 2 CPUs, 4000 MB, 5 000 000 kB | CPU/mem ✓ explicit; **disk is not sized to the multi-GB SIF — MAJOR M2** |
| GPUs | L12 | `request_GPUs = 1` (no `+RequestGPUMemoryMB`) | ✓ one whole GPU |
| remote placement | L13 | `+RemoteJob = True` | ✓ |
| site/device | L14 | `(TARGET.CloudSite =?= "BwForCluster-Nemo2") && (TARGET.GPUs_DeviceName =?= "NVIDIA L40S")` | ✓ measured strings (S1 raw L43–L47; S2N1 CloudSite/host); no `ProvidesETPResources` on the remote job ✓ |
| remote GPU legality | — | `request_GPUs` + `+RemoteJob` + no local-only requirement | ✓ |
| output/error/log | (absent) | — | ✗ **MAJOR M1** |
| arguments | (absent) | — | **m2** (job-id provenance) |

### 2.2 Will the default transfer the SIF, and what if the multi-GB transfer exceeds limits? (the Lead's question a)

- **The default does transfer it.** With `universe = container` and `container_image = /work/…sif` (an absolute
  local path, not a docker:// URL), the container-universe default is to transfer the image to the EP; the
  23.0 manual's escape hatch exists precisely because the default is to transfer: "A container image that would
  otherwise be transferred can be forced to never be transferred by setting `should_transfer_container = no`"
  ([container universe](https://htcondor.readthedocs.io/en/23.0/users-manual/container-universe-jobs.html)).
  Because the JDL does **not** set `should_transfer_container = no` (correct for S5) and sets
  `should_transfer_files = YES`, HTCondor transfers the image for this NEMO2 job. **No `capabilities` or
  `transfer_input_files` trick is needed** — the image is declared by `container_image`, and listing the SIF in
  `transfer_input_files` would transfer it as a normal input file, not as the container image, and could
  double-transfer it. The knobs that matter are the pool's transfer-size limit, `request_disk`, and the image
  size.
- **The size limit is the open question.** The submitted image is subject to the input-transfer size limit:
  `max_transfer_input_mb` (job-level) or the pool's `MAX_TRANSFER_INPUT_MB`; the `condor_submit` manual says "If
  the observed size of all input files at submit time is larger than the limit, the job will be immediately
  placed on hold with a `HoldReasonCode` value of 32". The pool default is normally 100 MiB; a multi-GB SIF
  would then be **refused at submit** (hold 32), not transferred. The unit must treat that as an expected,
  recordable outcome: it is exactly the "transfer refused" case the author asked to record (§2.5).
- **What to expect in the two outcomes.** (i) If the pool limit is ≥ the SIF size (or `-1`): the image is
  transferred; the transfer happens as part of the input sandbox before execution, so it appears in the
  event-log **wait** (submit→execute), unlike the docker:// case in S2 where the pull landed inside the run
  time (S2N1: 8 s wait, 107 s run including the pull). (ii) If the limit is below the SIF size: the job is held
  at submit with code 32; `condor_q -af HoldReasonCode HoldReasonSubCode HoldReason` records it; the S5 answer
  for the adapter is "default transfer refused at <limit> MiB, SIF <size> MiB", and the follow-up is a
  deliberate, reviewed deviation: `max_transfer_input_mb = -1` (documented "no limit") plus a `request_disk`
  sized from the SIF, recorded as *not* the default path. Do **not** silently add that to the first attempt —
  the default behaviour is the experiment.
- The SIF must be readable on the access point at submit time (it is, on `/work`), readable by the schedd for
  the transfer, and its SHA/size recorded before submission (§3 gates).

### 2.3 `s5_run.sh` — I4 content

- Identity block (L8): job/host/date/`iwd`; VERSIONS (L9); container/job-ad fields (L10: `ContainerImage`,
  `ContainerImageSource`, `WantContainer`, `Command`, `TransferInput`, `ImageSize`, `DiskUsage`); env
  NVIDIA/CUDA/APPTAINER/SINGULARITY/CONTAINER (L11) — good runtime/transfer evidence.
- NVIDIA (L12–13): `nvidia-smi -L` and a query (`name,uuid,memory.total,driver_version,compute_cap`) with rc
  lines ✓; handles absence.
- torch (L14–25): trackp python, `torch.__version__`, `torch.cuda.is_available()`, `torch.version.cuda`,
  device count/name, a 512×512 CUDA matmul when available, rc at L25 ✓. The current image builds trackp with
  Python 3.12 and `torch==2.6.0+cu124` (def L62–70) — CUDA 12.4 needs driver ≥ 550.54.14; record the actual
  driver from `nvidia-smi`/the job ad (last night's pool facts recorded a 13.4 CUDA-driver version at NEMO2, see
  chain-report authority L3 / `htcondor_prep_20261114/POOL_FACTS.md`), and record what torch reports either way.
- llama (L26–27): `command -v`, `--version`, sha256 of the binary, rc ✓.
- Writes: only the five relative files in the sandbox (cwd = `/srv` on NEMO2, S2N1 evidence) ✓; nothing outside;
  no credentials, no SSH/registry/docker, no network beyond HTCondor's own transfer ✓; `exit 0` always (M4/m9).
- **Missing for the transfer evidence (MAJOR M3):** the job never inspects its own sandbox for the transferred
  image. The only EP-side observation is `iwd=$(pwd)` (L8). To record "the execute-node's /srv copy if
  observable" the script should add: `ls -la`, `df -h .`, `du -sh .`, `find . -maxdepth 2 -name '*.sif'
  -printf '%p %s\n'`, a `sha256sum` of the image if present, and the `_CONDOR_SCRATCH_DIR` /
  `_CONDOR_SCRATCH_DIR_OUTSIDE_CONTAINER` values (S2N1 shows the latter = `/var/lib/condor/execute/dir_…`, which
  is the host-side sandbox path).
- **Missing summary (M4):** no I4 PASS/FAIL lines and a hard-coded `exit 0`; failures are in the per-topic files
  but not flagged. Add `I4_NVIDIA=ok|missing`, `I4_TORCH_CUDA=yes|no`, `I4_MATMUL=ok|skip`, `I4_LLAMA=ok|missing`,
  `I4_PASS`/`I4_FAIL` (and optionally exit nonzero on evidence-collection failure).
- The JOB id comes from `_CONDOR_ClusterId` (L7), which is **not in the container job environment** (S2N1's
  `_CONDOR_*` list: CHIRP_CONFIG, JOB_IWD, MACHINE_AD, JOB_AD, BIN, SCRATCH_DIR, JOB_PIDS, AssignedGPUs, SLOT);
  `JOB` will always be `local.0` (m1). Use `arguments = "$(ClusterId).$(ProcId)"` and `$1` (or parse the job ad).
- `"$_CONDOR_JOB_AD"` at L10 under `set -u`: if the variable were ever unset, the script aborts before
  `s5_env`/`s5_nvidia`/`s5_torch`/`s5_llama` are created — and with the JDL's `transfer_output_files` that turns
  the real failure into a missing-output **hold** (m3). Guard with `${_CONDOR_JOB_AD:-}` and pre-create all five
  files at the top (`: > s5_env.txt` …).

### 2.4 What must be recorded, and where (the Lead's question c)

The S5 evidence is not the job's stdout alone; it is a five-part record. Concrete plan:

**(i) Before submission (record in `s5/` and the report):**
1. SIF identity from the build record: `sif_sha256`, `sif_bytes`, `def_sha256`, mode from
   `/work/dwong/paperb/images/r1-htc-20261114.identity` (written by `build_sif.sh`), plus
   `sha256sum /work/dwong/paperb/images/r1-htc-20261114.sif` and the same for the mirror under
   `/ceph/srv/dwong/paperb/images/` (read-only); record the byte size in MB/GiB explicitly.
2. Dry-run ad (`condor_submit -dry-run s5_nemo2_gpu_sif.jdl`) → `s5/dryrun/s5_nemo2_gpu_sif.dry` + `.dry.log`;
   record `ContainerImage`, `ContainerImageSource` (`"local"` vs `"cedar"` is the transfer marker), `WantContainer`,
   `TransferInput`, `ImageSize`, `DiskUsage`, the appended SIF gate (`TARGET.HasContainer && TARGET.HasSIF`), and
   the requests.
3. `condor_config_val MAX_TRANSFER_INPUT_MB` (read-only on the submit host) — or record "unavailable"; this is the
   expected refusal threshold for the multi-GB image.
4. GPU snapshot 2 via `gpu_availability.sh` immediately before submission (supplement 2) and the chosen
   model + reason in the submission note beside `queue_times.tsv` (§2.6).
5. Queue snapshot (`condor_q dwong -af ClusterId ProcId JobStatus`), submit command, cluster id, unit hashes.

**(ii) From the job's event log (needs M1's `log`):** `htc_events.py s5.log --probe <cluster>.0=S5
--utc-offset-minutes 60 --tsv s5_queue_times.tsv` → submit/execute/end in UTC, `wait_s` (queue + negotiation +
SIF transfer), `run_s`, site/host via the `--history` JSON. Store as `s5/queue_times.tsv`.

**(iii) From `condor_history` after completion** (record which attributes exist): `JobCurrentStartTransferInputDate`,
`JobCurrentFinishTransferInputDate`, `JobCurrentStartExecutingDate`, `LastMatchTime`, `TransferInputSizeMB`,
`ImageSize`, `DiskUsage`, `ActivationSetupDuration`, `RemoteWallClockTime`, `ExitCode`, `HoldReason`,
`HoldReasonCode`, `HoldReasonSubCode`, `MachineAttrCloudSite0`, `LastRemoteHost`. Derive, if the timestamps are
present: queue_s = transfer_start − submit; transfer_s = transfer_finish − transfer_start;
execute_s = execute − transfer_finish; otherwise state that `wait_s` includes queue+transfer and give an implied
lower-bound rate = `sif_bytes / wait_s`.

**(iv) From the job itself:** the five (now six, with a summary) transferred files — `s5_identity.txt`
(SIF/versions/job-ad/placement), `s5_env.txt`, `s5_nvidia.txt`, `s5_torch.txt`, `s5_llama.txt`, plus the new
sandbox/SIF-copy section and the I4 summary — with sha256 of each; and `s5.out`/`s5.err`/`s5.log`.

**(v) The S5 transfer row:** a `s5/transfer_evidence.tsv` (or a section of the report) with one row:
`site, model, host, gpu_uuid, sif_name, sif_bytes, sif_sha256, submit_utc, execute_utc, end_utc, wait_s, run_s,
queue_s, transfer_s, implied_MBps, sandbox_sif_visible, sandbox_sif_bytes, transfer_limit_mb, outcome
(transferred|refused|too_slow|failed), hold_reason/code/subcode, exit`. Predeclare the "too slow" threshold
(e.g. wait_s > 900 s, or transfer_s > 600 s, or implied rate < 20 MB/s) and the stop rule: if refused or too
slow, record and **stop at S5** (no retry without the author).

### 2.5 Failure/hold modes to record (not hide) — the Lead's question d

| Mode | Expected evidence | Handling |
|---|---|---|
| Transfer refused by size | job held at submit, `HoldReasonCode 32` (input-transfer size limit; `condor_submit` man page) | record verbatim (+ `MAX_TRANSFER_INPUT_MB` if known); this **is** the S5 answer for the adapter; stop; a forced second attempt (`max_transfer_input_mb = -1` + sized disk) is a reviewed deviation, recorded as such |
| Transfer failed / too slow / shadow exception | event codes 007/009/004/012, `HoldReason`, `LastShadowException`, job back to idle (25.x) or held | record; do not retry blindly; if too slow, apply the predeclared threshold and stop at S5 |
| SIF not transferred / image not found on the EP | job start failure/hold; sandbox/SIF-copy section shows no image | record; distinguish "not transferred" from "transferred but image invalid" |
| Disk full at the EP | hold (disk family, e.g. code 34 subcode 104), transfer failure | record; fix `request_disk` from the SIF size (M2) before retrying |
| GPU not injected (no `--nv`) | `nvidia-smi` missing/failing, no `/dev/nvidia*`, no `libcuda`, `torch.cuda.is_available()=false`, while `NVIDIA_VISIBLE_DEVICES`/`CUDA_VISIBLE_DEVICES` carry the GPU UUID (S2N1 evidence) | record as a **HTCondor-version caveat**: automatic `--nv` for container-universe Apptainer GPU jobs is a 25.14.1 feature and the site runs 25.0.12; do not call the image or the GPU broken on this alone |
| torch CUDA / driver mismatch | torch error text (`CUDA driver version is insufficient`, `libcuda` missing), torch.cuda false | record; CUDA 12.4 needs driver ≥ 550.54.14 (last night's pool facts recorded a 13.4 CUDA-driver version at NEMO2); a mismatch should be reported, not assumed |
| llama-server missing/broken | `command -v` empty, non-zero `--version` rc, sha absent | record as an image defect; the CUDA build may still fail to load without `libcuda` (same caveat) |
| `nvidia-smi` absent from the image | nvidia-smi MISSING (S2's official image showed exactly this) | not a failure by itself; with `--nv` it would be host-injected; record |

Diagnostics to add for the GPU caveats: `ls -l /dev/nvidia* 2>&1`, `ldconfig -p | grep libcuda`, and
`cat /proc/driver/nvidia/version 2>&1` (NIT m10).

### 2.6 Model choice (the Lead's question f)

Snapshot 1 (11:21:10 CET, `gpu_availability.tsv`): **NEMO2 H200 8 total, 4 idle, 3 drained, 1 busy; NEMO2 L40S
4 total, 3 idle, 1 drained, 0 busy**; both sites advertise `HasSingularity=true` only (no Docker), which is the
container-universe route. The committed JDL (L14) uses **`NVIDIA L40S`**, matching the chain plan (L90: "S5
(NEMO2 L40S, same SIF transferred by HTCondor)") and the S2N1 L40S container precedent (`slot1_1@nemo2_gpu-
bb8342a9e6@g3606.nemo.privat` ran the docker:// image through Singularity) — so the only new variable in S5 is
the SIF transfer, which is the point of the step.

**Pick L40S** (3 idle at the snapshot; the SIF's CUDA arches include 89; the committed JDL and plan already say
L40S; no JDL change). **Fallback: H200** (4 idle/8, CUDA arch 90 is also in the SIF build arches) if a fresh
snapshot immediately before submission shows L40S idle = 0 while H200 has idle — a one-line device-string
substitution on L14, recorded with the reason in the submission note per supplement 2 (I4 is model-agnostic, so
the review's checks hold; do not switch models silently or without recording). Refresh the snapshot at submit
time and append it (never edit snapshot 1).

### 2.7 Caps, write scope, credentials (the Lead's question e)

- **Caps:** 1 GPU job × 1800 s = **0.5 GPU-h** ≤ the 10 GPU-h round cap; whole GPU (`request_GPUs = 1`, no
  `+RequestGPUMemoryMB`); concurrent jobs must be checked in the queue snapshot (the pre-S2 reading was
  `own_active=18`, `raw/s2_precheck.txt` — state the current number and which jobs are ours).
- **Write scope:** the job writes only the five/six relative files in its sandbox (`/srv` on NEMO2) and the
  outputs are transferred back to the submit directory; the submit directory and the transferred outputs must
  live under `/work/dwong/paperb/` (e.g. `/work/dwong/paperb/work/s5_submit/`), with the SIF read-only from
  `/work/dwong/paperb/images/`; nothing under `/ceph` is written (the mirror is read-only); no deletion; no
  other users' files.
- **Credentials/network:** none — local SIF, no registry pull, no `docker login`/secret read, no xrootd/network
  use inside the job; only HTCondor's own transfer traffic. ✓

### 2.8 SIF-gate / dry-run gates (cannot be done without the SIF; pre-submission)

1. **Dry-run after the SIF exists** (`condor_submit -dry-run s5_nemo2_gpu_sif.jdl`): require rc 0 and inspect
   `ContainerImage`, `ContainerImageSource` (`local` = no transfer / `cedar` = transfer path), `WantContainer`,
   `TransferInput` (does the SIF appear? — that decides whether the size limit applies as a normal input),
   `ImageSize`/`DiskUsage`, the appended `TARGET.HasContainer && TARGET.HasSIF` gate, and the requests. Commit
   `s5/dryrun/s5_nemo2_gpu_sif.dry` + `.dry.log`.
2. **Measure the SIF gate read-only on NEMO2**: `condor_status -constraint 'CloudSite =?= "BwForCluster-Nemo2"' -af
   Name HasSIF HasSandboxImage HasContainer` (and for a couple of GPU slots) — `HasSIF` is not among the
   committed `raw_container_attrs_*` booleans (those are HasContainer/HasDockerURL/HasSingularity/HasDocker); if
   `HasSIF` is false on NEMO2 the job idles (a match failure to record, not an image/transfer failure).
3. **SIF identity binding**: SIF SHA-256/bytes recorded at submit time (build identity + `sha256sum`), so the
   transfer evidence is tied to exactly that image; the mirror copy's SHA as well.
4. **MAX_TRANSFER_INPUT_MB** (read-only) recorded; the expected hold-32 case pre-stated in the submission note.

---

## 3. Findings

### BLOCKING

None certain: the JDL is a valid container-universe job and the default transfer is the right experiment. The
author's evidence requirements are not met yet (M1–M3 below), so the unit must be fixed and re-reviewed before
submission.

### MAJOR

**M1 — the JDL has no `output`, `error` or `log`.** JDL has 15 lines, none of them these three. Defaults are
`/dev/null` for stdout/stderr on Unix and **no event log at all** ("If no `log` entry is specified, HTCondor does
not create a log for this cluster", [`condor_submit`](https://htcondor.readthedocs.io/en/23.0/man-pages/condor_submit.html)).
The S5 transfer-time plan explicitly uses the event log ("submit→execute wait from the event log, run time from
the event log"), and `S5_DONE`/failure messages currently go to `/dev/null`. *Exact fix:* add
`output = s5.out`, `error = s5.err`, `log = s5.log`; record with
`python3 htc_events.py s5.log --probe <cluster>.0=S5 --utc-offset-minutes 60 --tsv s5_queue_times.tsv` (the
S2-reviewed recorder).

**M2 — `request_disk = 5 000 000` kB (~4.8 GiB) is not sized to the multi-GB SIF.** Once the image is transferred
it occupies disk in the job sandbox; the SIF (CUDA devel base + three environments + llama.cpp) is very likely
several GB, and the size is not known yet. If the requested disk is smaller than what the transfer needs, the
transfer can fail/hold on disk (or be misread as a transfer-policy refusal) and the experiment is confounded.
*Exact fix (after the SIF identity is recorded):* set `request_disk` from `sif_bytes` with a margin, e.g.
`request_disk = ` ceil(sif_bytes/1024) + 2 000 000 kB (SIF + ~2 GB for the sandbox and outputs), keep it explicit
in the JDL and record the value plus the dry-run ad's `DiskUsage`; if the SIF is enormous, record the size and
the hold instead of forcing it.

**M3 — the job does not record the EP-side SIF copy/transfer evidence.** The script only records `iwd=$(pwd)`
(L8); it never lists the sandbox, never stats a transferred `.sif`, never records `df`/`du` or
`_CONDOR_SCRATCH_DIR(_OUTSIDE_CONTAINER)`. The author asked for the SIF transfer **method, size and time** and
the Lead explicitly wants "the execute-node's /srv copy if observable" — the EP-side copy is the only in-job
proof of what landed. *Exact fix:* extend the identity block with `ls -la`, `df -h .`, `du -sh .`,
`find . -maxdepth 2 -name '*.sif' -printf '%p %s\n'`, `sha256sum` of any found `.sif`,
`env | grep _CONDOR_SCRATCH_DIR`, and record the result in `s5_identity.txt` (plus the transfer_evidence row's
`sandbox_sif_visible`/`sandbox_sif_bytes`).

### MINOR

**m1 — `JOB` is never the cluster id.** `_CONDOR_ClusterId`/`_CONDOR_ProcId` are not in the container job
environment (S2N1 evidence), so `JOB` is always `local.0`. *Fix:* add `arguments = "$(ClusterId).$(ProcId)"` to
the JDL and `JOB="${1:-local.0}"`, or parse `ClusterId` from `$_CONDOR_JOB_AD`.
**m2 — `"$_CONDOR_JOB_AD"` under `set -u`.** A missing variable would abort the script mid-way; guard with
`${_CONDOR_JOB_AD:-}`. Also pre-create all output files (`: > s5_env.txt` …) before any risky command, so an
early abort cannot turn the real failure into a missing-`transfer_output_files` hold.
**m3 — `RequestMemory = 4000` may be tight** for Apptainer + CUDA torch initialisation + llama-server; S4 uses
8000. *Fix:* consider 8000 MB (or keep 4000 and record that a memory hold would be a resource choice, not a
transfer result); record what is requested.
**m4 — no I4 PASS/FAIL summary and a hard-coded `exit 0`.** *Fix:* add explicit
`I4_NVIDIA=ok|missing`, `I4_TORCH_CUDA=yes|no`, `I4_MATMUL=ok|skip`, `I4_LLAMA=ok|missing`, `I4_PASS`/`I4_FAIL`
lines (in `s5_identity.txt` or a sixth file added to `transfer_output_files`), and return nonzero on
evidence-collection failure if the operator wants a machine-checkable result.
**m5 — no fresh snapshot / model-choice record in the unit.** Supplement 2 requires a snapshot before every GPU
submission and the chosen model+reason in the submission note. *Fix:* run `gpu_availability.sh` immediately
before submitting (append snapshot 2, never edit snapshot 1), pick L40S per §2.6 (3 idle/4 at 11:21; committed
JDL/plan; arch 89; S2N1 precedent), fall back to H200 (4 idle/8; arch 90) only if L40S idle = 0 at that moment —
one-line device-string change on L14, recorded with the reason; record the snapshot timestamp and the reason.
**m6 — the transfer-limit expectation must be recorded, not guessed.** *Fix:* record
`condor_config_val MAX_TRANSFER_INPUT_MB` (read-only; or "unavailable") at submit; pre-state the expected
refusal (hold 32) if the SIF exceeds it; if refused, record verbatim and stop at S5; if the author then wants the
size/time evidence, the reviewed deviation is `max_transfer_input_mb = -1` plus the M2 disk sizing, recorded as
"forced, not default" (re-review the one line). No `transfer_input_files` trick is appropriate for the image.
**m7 — bind the evidence to the exact image and the transfer timing.** *Fix:* record SIF sha/bytes at submit
(build identity + `sha256sum`, mirror too), the dry-run ad fields (`ContainerImage`, `ContainerImageSource`,
`TransferInput`, `ImageSize`, `DiskUsage`), and after completion the history transfer timestamps/attrs
(`JobCurrentStartTransferInputDate`, `JobCurrentFinishTransferInputDate`, `JobCurrentStartExecutingDate`,
`LastMatchTime`, `TransferInputSizeMB`, `ImageSize`, `DiskUsage`, `ActivationSetupDuration`); if they are
absent, state that `wait_s` includes queue+transfer and give the lower-bound implied rate.
**m8 — submit placement and record set.** *Fix:* copy the unit to a writable submit dir under
`/work/dwong/paperb/` (e.g. `.../work/s5_submit/`), submit from there, record the exact `condor_submit` command,
cluster id and submit UTC; the five/six outputs and `s5.out/.err/.log` land there; record their sha256.
**m9 — define "too slow" before submission.** *Fix:* predeclare the threshold and stop rule (e.g. wait_s > 900 s
or transfer_s > 600 s or implied rate < 20 MB/s → "too slow", record, stop at S5, no retry without the author),
so the author's "if too slow, record and stop" is checkable rather than judgement-in-the-moment.
**m10 — GPU-injection diagnostics.** *Fix:* add `ls -l /dev/nvidia* 2>&1`, `ldconfig -p | grep libcuda`, and
`cat /proc/driver/nvidia/version 2>&1` to the NVIDIA section; they distinguish "no `--nv` on 25.0.12" from an
image/GPU failure (S2N1 shows the GPU UUID in the env, but nvidia-smi MISSING even for the official image).
**m11 — `s5_env.txt` grep `CONTAINER` is broad**; fine, but record the full `env` sorted for the runtime
indicators (SINGULARITY_NAME/APPTAINER_NAME) so the runtime (Apptainer, singularity-only NEMO2) is documented.
**m12 — the image's current stack differs from the S4 note.** The current def builds trackp with Python 3.12 and
torch 2.6.0+cu124 (def L62–70); the S4 review's re-review note about a 3.13.x trackp applies to the pre-fix
def. Record `python -VV`/torch actual for the SIF in the S5 identity (the script does via `s5_torch.txt`), and
note it here so the SIF's stack is not misquoted later.

### NIT

**n1** — no explicit `should_transfer_container = yes`: the default is yes and the S5 experiment relies on it;
adding it explicitly would be identical semantics and makes the intent auditable — optional.
**n2** — `nvidia-smi` may be absent from the image and/or not injected without `--nv`; not a failure by itself —
the script records it correctly.
**n3** — `llama-server --version` on a CUDA build may fail without `libcuda`; record the rc/stderr, interpret
with the GPU caveat.
**n4** — with an explicit `transfer_output_files`, any extra files the container writes in the sandbox are
ignored (fine); a missing listed file would hold the job (the m2 pre-creation removes the main risk).
**n5** — record the event log and `s5.out/.err` sha256 with the other evidence, and the SIF identity in the
submission note.
**n6** — the SIF mirror under `/ceph/srv/dwong/paperb/images/` is read-only for this unit (no write needed).

---

## 4. Verdict

**The unit is close, but it cannot yet produce the evidence the author asked for:** the JDL has no event log or
stdout/stderr (M1 — the transfer-time plan explicitly uses the event log), the disk request is not sized to the
multi-GB SIF (M2), and the job does not record the EP-side SIF copy (M3). All three fixes are small and local.
The rest of the unit is sound: the default container-image transfer is the right mechanism for this step (no
`capabilities`/`transfer_input_files` trick; the refusal case is hold 32 and is itself the S5 answer), the GPU
request is one whole GPU with the measured L40S device string and CloudSite selector, the sandbox-only writes
and the transfer-back list are correct, the I4 checks cover CUDA/torch/llama-server, and the caps/write
scope/credentials are clean. Model choice: keep **L40S** (3 idle/4 at 11:21 CET, matches the plan and the S2N1
precedent), fall back to **H200** (4 idle/8) only if a fresh snapshot shows L40S idle = 0, recording the reason.

**Fix M1–M3 (plus the m-item record changes), then re-review.** Minimum change set: add
`output/error/log` (M1); size `request_disk` from `sif_bytes` after the SIF identity (M2); add the sandbox/SIF
copy section + I4 summary and the `arguments`/`_CONDOR_JOB_AD` guards (M3, m1, m2, m4); record the pre-submission
gates (SIF identity, dry-run ad, `MAX_TRANSFER_INPUT_MB`, HasSIF, snapshot 2/model note, queue snapshot) and the
transfer_evidence row (§2.4). The dry-run/HasSIF/SIF-identity gates remain pre-submission requirements even after
the fixes.

VERDICT: NOT ACCEPTED

---

## Re-review round — ghcr.io images at HEAD `f2b95c91` (supersedes the round-1 verdict above)

**Re-reviewer:** same reviewer. **Date/time:** 15 November 2026, 01:05–01:30 CET (Europe/Berlin). **Worktree
HEAD:** `f2b95c91` ("ghcr digests confirmed, Docker route review ACCEPTED (D1 condition), S5 PASS gate
tightened"). **Scope:** the S5 unit has been reworked for the ghcr-image route (`s5/s5_nemo2_gpu_ghcr.jdl`,
`s5/s5_run.sh`), and the S4 one-line change (`s4/s4_local_cpu_ghcr.jdl` + the adapted `s4/s4_run.sh`) is
confirmed here as requested. The reviewed files are committed at `f2b95c91`; the worktree is **not** clean at
review time — `verify_images.sh` is modified (the operator's read-only ghcr verification run) and **no ghcr
verification raw files are committed yet**. No SSH, no registry access, no submission, no git write; the only
file written is this appendix.

**Pinned files (SHA-256):**

| File | SHA-256 |
|---|---|
| `s5/s5_nemo2_gpu_ghcr.jdl` (19 lines) | `b53088b6f5cbdcd4114235311bf4c81834063e8a77fd332ecb4dd0300ba9a35d` |
| `s5/s5_run.sh` (61 lines) | `f31b16d6fd1774d84e5fa7cb1f6f93171265ffa97a77c4d8fb38e4d3a35b70f0` |
| `s4/s4_local_cpu_ghcr.jdl` (16 lines) | `56b23d66783e39b69f6d3df541905d047a457a3116b660b85f49da529f5c59de` |
| `s4/s4_run.sh` (120 lines) | `835de3ef97e7609a95c093653707d89fe1737569bcf1d6f2f67286da5b77ff91` |

Digests supplied by the Lead and stated as registry-verified (tag `20261114-74820315`, Actions run
`43644472626`): cpu `sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa`, gpu
`sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`.

### 1. S4 — confirmation of the one-line JDL change (the Lead's request a)

**Confirmed acceptable.** `diff s4_local_cpu_sif.jdl s4_local_cpu_ghcr.jdl` changes exactly two lines: line 2
(`container_image = /work/dwong/paperb/images/r1-htc-20261114.sif` → `docker://ghcr.io/dowlingwong/r1-htc-cpu@
DIGEST_CPU_PLACEHOLDER`) and line 3 (`should_transfer_container = no` removed, correctly: a docker:// URL is
pulled by the container runtime, never transferred). Every other line is identical to the accepted S4 unit
(`arguments`, transfer fields, `output`/`error`/`log`, `+RequestWalltime = 3600`, CPUs 2 / Mem 8000 / disk
30 GB, `requirements = TARGET.ProvidesETPResources`, `queue 1`).

The `s4_run.sh` by-design adaptation is also acceptable: preflight requires only the harness env (the cpu target
carries envs 1+2 by design), I1 records `trackp` and `llama-server` as "ABSENT in this image … by design" instead
of failing, and I2 runs in the **harness env**. The harness env is the right reference stack: the uv.lock at
`a3fedbb` pins **numpy 2.4.4, scikit-learn 1.8.0, pytest 9.0.3** — exactly the 0.922225 reference packages
(`pandas 3.0.3`, `scipy 1.17.1` also locked) — and the image's Python is 3.13.18 vs the reference's 3.13.4, the
difference the author said to record as a stack difference. I2 in the harness env is therefore closer to the
reference than the previous trackp/Python-3.12 choice.

**One literal substitution is still required before submission:** the committed JDL still contains
`DIGEST_CPU_PLACEHOLDER`; replace it with exactly the verified cpu digest above and record the tag→digest check.
That is the only S4 change; no new review round is needed for it alone.

Non-blocking S4 notes for the report (no action required before submission): (i) the identity block still probes
`$B/images/r1-htc-20261114.identity`/`.sif`, which no longer exist, so those fields will be empty — record the
image identity from the job ad's `ContainerImage` (already grepped) and `/opt/r1/VERSIONS.txt` instead; (ii)
`"$_CONDOR_JOB_AD"` at L21 is unguarded under `set -u` (it is set in practice; use `${_CONDOR_JOB_AD:-}` like
S5 for the same robustness); (iii) the header still says "using our SIF" (cosmetic); (iv) I2 hard-gates on
`0.922225`: a deterministic-but-different result on Python 3.13.18 exits 1 — the report must present
"two runs equal" and "matches recorded reference" separately and record the stack difference (the author's
instruction), not read exit 1 as a unit failure; (v) the ghcr pull from the ETP local WNs is the one unproven
step (S2L proved the same mechanism against Docker Hub): record success/failure of the pull, don't retry blindly.

### 2. S5 — disposition of the round-1 findings

| Round-1 finding | Status at `f2b95c91` |
|---|---|
| M1 no `output`/`error`/`log` | **Fixed** — JDL L9–11; recorder plan unchanged (`htc_events.py s5.log --utc-offset-minutes 60`). |
| M2 `request_disk` not sized | **Not yet fixed** — `request_disk = 50,000,000` kB is a placeholder; the Lead commits to set it from the measured gpu image size before submission and record the dry-run `DiskUsage` (gate R3). |
| M3 no EP-side pull/sandbox evidence | **Fixed with a caveat** — `s5_pull.txt` records `pwd`/`df`/`du`/`ls`, a bounded `find / -xdev -maxdepth 3`, the root listing and `/.singularity.d`, and the identity block records the job-ad container fields, runtime env and `_CONDOR_SCRATCH_DIR`. For a docker:// URL the image is pulled by the runtime to a cache **outside** the container's view, so the in-container `find` will normally show nothing: record "pulled, not observable in container" and take the size from the registry/cache measurement (gate R4), not from the job. |
| m1 arguments/cluster id | **Fixed** — JDL L4 `arguments = "$(ClusterId).$(ProcId)"`, script `JOB="${1:-local.0}"`. |
| m2 `set -u` job-ad guard / pre-created outputs | **Fixed** — `${_CONDOR_JOB_AD:-}` guard (L16) and all seven files pre-created (L9–10), so an early abort cannot become a missing-output hold. |
| m3 request_memory 4000 | **Fixed** — 8000 MB. |
| m4 PASS/FAIL summary, nonzero exit | **Fixed in form, but see R1**: the summary is written and `exit "$FAIL"` is used; the llama gate string is wrong, so the gate never passes. |
| m5 libcuda/`/dev/nvidia*`/driver diagnostics | **Fixed** — `s5_nvidia.txt` records `/proc/driver/nvidia/version`, `/dev/nvidia*`, libcuda paths. |
| m6 "too slow" threshold | Not in the unit; still to be declared in the submission note (gate §4). |
| m7 image/transfer evidence binding | **Partly**: job-ad `ContainerImage`/`ImageSize`/`DiskUsage` + VERSIONS are recorded; the image size and tag→digest come from the verification (gate R4). |
| m8 submit placement/records | Operator step; submit dir under `/work/dwong/paperb/`, record command/cluster id (gate §4). |
| m9/m10/m11/m12 | L40S + fresh snapshot/fallback plan kept; runtime env, root markers and the image root listing now recorded; the round-1 note on the pre-ghcr trackp stack is superseded by the ghcr images. |
| Requirements gate | **Correction, not a defect**: for the docker:// URL the appended requirement is `TARGET.HasContainer && TARGET.HasDockerURL` (the SIF round's `HasSIF` gate no longer applies); NEMO2 measured both true on 2380/2380 slots (S2's M1 fix, `raw/raw_container_attrs_nemo2.txt`). Confirm it in the dry-run ad. |

### 3. New findings

**R1 — MAJOR (the only required code fix): the S5 PASS/FAIL gate can never pass the llama check.**
`s5_llama.txt` writes `rc=$?` after `llama-server --version` (script L43), but the gate greps
`llama_version_rc=0` (L58) — that string is never written, so the grep always fails, `FAIL=1`,
`s5_PASSFAIL.txt` is `S5_FAIL` and the script exits 1 **even when llama-server is fine**. This defeats the
D1-tight gate the Lead intended (and mirrors the `verify_images.sh` label `llama_version_rc=$?`).
*Exact fix:* change L43 to `echo "llama_version_rc=$?"` (keep the gate as is; optionally also record
`command -v` rc). The other gates are correct against the script's output: `grep -qiE "GPU [0-9]"` matches
`nvidia-smi -L`'s `GPU 0: …`, `grep -q "cuda_available True"` matches the torch line, `grep -q "matmul_ok"`
matches the matmul line.

**R2 — required literal substitution: both JDLs still carry digest placeholders.** `s5_nemo2_gpu_ghcr.jdl` L2
has `DIGEST_GPU_PLACEHOLDER`, `s4_local_cpu_ghcr.jdl` L2 has `DIGEST_CPU_PLACEHOLDER`. Substitute exactly the
verified digests above and record the tag→digest equality (tag `20261114-74820315`). As committed, a
`docker://…@DIGEST_…_PLACEHOLDER` reference is not pullable — do not submit before this substitution; after it,
record the final JDL sha256. (A literal substitution of the confirmed digest is not a new review round.)

**R3 — gate: size `request_disk` from the measured gpu image.** `50,000,000` kB (≈47.7 GiB) is a placeholder;
set it from the measured gpu image size (registry manifest / apptainer-cache measurement in the verification) plus
a margin, and record the dry-run ad's `DiskUsage`; a disk hold must be recorded, not retried.

**R4 — gate: commit the ghcr verification and the D1 smoke before any submission.** No verification raw files are
committed and `verify_images.sh` is modified-uncommitted. Record, in `raw/`: run `43644472626`, commit
`74820315`, tag `20261114-74820315`, both digests, both image sizes, the three base digests (Docker-review D5/D8),
`apptainer inspect` + `exec cat /opt/r1/VERSIONS.txt` for both images, the three env imports, and — mandatory
before S5 — the gpu **D1** smoke `/opt/r1/llama/bin/llama-server --version` rc=0 (Docker-review MAJOR D1: llama.cpp
links libgomp, the runtime base may lack it). If the D1 smoke fails, the gpu image must be rebuilt before S5/I3;
the cpu image is unaffected.

**R5 — MINOR: pull-time attribution is stated wrongly in the script comment.** For a docker:// URL there is no
HTCondor image transfer; Singularity pulls at container start, and the S2 evidence placed the first NEMO2 pull in
the **run** time (S2N1: 8 s wait, 107 s run including the pull; S2N2 135 s run), not in the submit→execute wait.
Record `wait_s` **and** `run_s`, and estimate pull+startup as the script's first timestamp minus the execute time
(add an end timestamp to `s5_identity.txt` for the script's own duration); state in the report where the pull
landed rather than assuming the wait.

**R6 — MINOR: `s5_env.txt` is pre-created but never written** (the env output goes into `s5_identity.txt`).
Either write the env there or drop `s5_env.txt` from `$PRE` and `transfer_output_files` (7→6 files).

**R7 — NIT: the in-container `find / -xdev -maxdepth 3`** will not see the pulled image (cache outside the
container); record "not observable in container" and use the verification's cache/manifest size. The
`/.singularity.d`, root listing and runtime-env records remain useful runtime evidence.

### 4. Pre-submission gates (S4 and S5)

1. **Digest substitution (R2)** in both JDLs; record the final JDL hashes and the tag→digest verification.
2. **Verification record (R4)**: ghcr inspect/VERSIONS/env imports + sizes + base digests committed; **gpu D1
   llama smoke rc=0** before S5.
3. **S5 request_disk from the measured image size (R3)**; both dry-run ads committed
   (`s4/dryrun/s4_local_cpu_ghcr.dry`, `s5/dryrun/s5_nemo2_gpu_ghcr.dry`): rc 0; `ContainerImage`/
   `ContainerImageSource="docker"`; `WantContainer`; appended `TARGET.HasContainer && TARGET.HasDockerURL`;
   `TransferInput="…run.sh"`; `DiskUsage`; the requests; `Iwd`/`Cmd` in the submit dir; S5 `arguments`.
4. **GPU snapshot 2 immediately before S5** (`gpu_availability.sh`, append-only) with the chosen model and reason
   in the submission note: L40S (3 idle/4 at 11:21) as committed; H200 fallback (4 idle/8) only if L40S idle=0, a
   one-line device-string substitution recorded with the reason. Queue snapshot before submitting.
5. **Submit placement/records**: unit copied to a writable dir under `/work/dwong/paperb/`; record
   `condor_submit` output, cluster id and submit UTC; S4's evidence stays under `/work/dwong/paperb/work/`
   (output/error/log transferred), S5's seven files are transferred back to the submit dir.
6. **After the runs**: S4 — `i1_envs.txt`, the two `i2_run*.log` + `run.log` values/shas, `i2_compare.txt`
   (distinguish two-runs-equal vs reference-match; record the Python 3.13.18 stack difference), `s6_xrootd.txt`,
   `identity.txt`, the `/work` output dir and exit code. S5 — event log via `htc_events.py s5.log --probe
   <cluster>.0=S5 --utc-offset-minutes 60 --tsv s5_queue_times.tsv`; wait/run and the pull attribution (R5);
   the job-ad `ContainerImage`/`ImageSize`/`DiskUsage`; the SIF/image size from the verification; nvidia/devices/
   driver; torch; llama; `s5_pull.txt` (record "not observable" if empty); `s5_PASSFAIL.txt`; store under `s5/`
   and in the chain report.

### 5. Residual risk carried into submission

The ghcr pull from the ETP local WNs (S4) and NEMO2 (S5) is the one unproven network step (S2L/S2N1 proved the
same mechanism against Docker Hub; ghcr is a new registry — record any pull failure, don't retry blindly); the D1
libgomp risk on the gpu image until the smoke passes; the S4/I2 Python 3.13.18-vs-3.13.4 stack difference; the
pull cache is not observable in-container (the size/timing evidence comes from the verification and the event
log); the images' base tags are mutable and the digest verification files are not committed yet (Docker-review
D5/D8); `torch==2.6.0+cu124` remains the proposed value; model availability moves during the day (fresh
snapshot required).

**Round-1 verdict superseded.** M1/M3 and all but one of the minors are fixed; the unit is one line away from
submittable, but **R1 makes the PASS/FAIL summary wrong by construction**, and R2–R4 are uncompleted
pre-submission gates. Fix R1 (one line), apply the two literal digest substitutions, commit the verification and
size the disk from it, then S4/S5 may be submitted; I will re-check the one-line gate fix on request.

VERDICT: NOT ACCEPTED


---

## Quick re-check (R1–R4) — 15 Nov 2026, 01:55–02:05 CET

**Scope:** quick confirmation only, no full round. Worktree HEAD **`befbaf64`** ("GPU image verified … S5 disk
sized …"). S5 had already been **submitted** (cluster 759694, NEMO2 L40S, `g3606`, started 01:42 CET) and is
executing, so this is a post-submission confirmation of the unit and the gates; S4 has run. Unit hashes:
`s5/s5_nemo2_gpu_ghcr.jdl` `8c0f1db2c4043913b553dca9d7cd04ce2a31df21d84120fa0a0e92a91dcff3ec` (only the digest and
the disk value differ from the reviewed unit), `s5/s5_run.sh`
`588f35d26ee0bee9c97d9d7a3eea96dfc0c53a10ce213c0efc65d76c1f710e4b`, `s5/submit_s5.sh`
`a371ea748718c25b2ebfd3fea5e24ec190f1583dccb40ed14f64b8ebe2b6df94`; S4 JDL `72b2793f…` with the cpu digest.

- **R1 — fixed.** `s5_run.sh` L43–46 now runs `/opt/r1/llama/bin/llama-server --version > /tmp/llama.version.txt
  2>&1; LRC=$?`, prints the head and writes `llama_version_rc=$LRC`; the gate (L61) greps exactly
  `llama_version_rc=0`; the other gates (nvidia `GPU [0-9]`, torch `cuda_available True`, `matmul_ok`) match the
  script's output. The host-side verification script's old head-rc bug was tooling, as the Lead says.
- **R2 — fixed.** Both JDLs carry the literal verified digests (cpu `sha256:221ca459…75aa` in the S4 JDL, gpu
  `sha256:69b06b35…5296` in the S5 JDL); no placeholder remains. S4 already ran with the cpu digest.
- **R3 — fixed.** S5 `request_disk = 25,000,000` kB, from the measured gpu SIF 5,226,487,808 B (4.87 GiB) + sandbox
  + margin; the recorded dry-run ad shows `RequestDisk=25000000`, requirements `HasContainer && HasDockerURL`,
  `ContainerImageSource=docker`. Ample margin.
- **R4 — fixed as recorded.** The chain report now records the verification: CPU SIF 366,702,592 B /
  `7be8796e…`; GPU SIF 5,226,487,808 B / `f88382fd…`, pull 1259 s; inspect rc 0 and VERSIONS rc 0 for both; the
  three envs and torch 2.6.0+cu124; **D1: `libgomp.so.1` present**, and the login-node `llama-server --version`
  fails only on `libcuda.so.1` (no driver) — so the real GPU test is the S5 job, which captures llama rc +
  `/dev/nvidia*` + driver + libcuda. Remaining record-keeping (not unit defects): the raw verification logs live on
  the cluster and should be committed under `raw/`; the pre-S5 snapshot (L40S 7 idle/10, H200 3 idle/9) must be
  **appended** to `gpu_availability.tsv` — the repo copy still has snapshot-1 only.
- **R5/R6/R7 — addressed.** Script start/end UTC are recorded (`script_start_utc`/`script_end_utc`),
  `s5_env.txt` is written, and the in-container find limitation is stated. Cosmetic only: the L4 comment still says
  "pull time split from submit->execute wait"; the S2 evidence (and the Lead's plan) puts the first pull in
  **run_s** — read the run_s, not the wait, for the pull.
- **S4 validation (read from the committed evidence, not the summary):** cluster 759693 COMPLETED exit 0, wait
  24 s / run 233 s, host `slot1_65@mdm1.etp.kit.edu`; I2_PASS with 4/4 `val_score 0.922225`, 4/4
  `train_loss 0.314016`, identical worker `run.log` sha256; both checkouts at the pinned commits; S6 xrootd
  rc 124 on both endpoints from the worker (Q-XRD). Matches the Lead's report; no numeric stack effect from
  Python 3.13.18 vs 3.13.4.
- **S5 time-critical watch:** `+RequestWalltime = 1800` from 01:42 CET gives a hard cap near 02:12 CET; the
  login-node pull took 1259 s, so a materially slower EP pull can hit a walltime hold (codes 46/47) — record it
  and do not retry blindly (the pull cache is per-EP/per-job, so a re-run repeats the pull). The outcome must be
  read from `s5_PASSFAIL.txt` + `s5_llama.txt` + `s5_nvidia.txt`/`s5_torch.txt`/`s5_pull.txt`, and the recorder
  (`htc_events.py s5.log --utc-offset-minutes 60`) gives the wait/run split with the pull in run_s.
- **Remaining records when S5 finishes:** `s5_submit` dry-run ad, `submission_note.txt`, queue snapshot, the
  pre-S5 snapshot rows, the verification raw logs, and the outcome (wait/run, llama rc, PASS/FAIL, pull evidence)
  — commit them with the S5 report section.

VERDICT: ACCEPTED
