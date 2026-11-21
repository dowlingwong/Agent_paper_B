# R1-T1-HOST-H200: harness-isolation host conditions inside the HTCondor container on NEMO2 H200 (21 November 2026)

**Status: FAIL — the harness isolation does not work inside the HTCondor container on NEMO2 H200. Per PLAN row
R1-T1-HOST-H200 the whole T1 table moves to Ada.** ENGINEERING_ONLY: nothing was measured; no T1 label run, no
sweep-2 change, no change to `main`, no push, no deletion. AI-assisted.

This report records the check that PLAN row **R1-T1-HOST-H200** requires before any T1 label run on NEMO2 H200: it
runs the §3 "Host conditions and waivers" table and the experiment-agent list (items 1–7) of
`docs/r1/reports/HARNESS_ISOLATION_20261117.md` — including the requirement that a real isolated smoke record says
`effective: true` and the §5.5 GPU smoke (CUDA IPC across the worker's PID namespace) — inside a v2-image
HTCondor container job on one NEMO2 H200. It is the harness-isolation counterpart of the Ada host check; no T1
labels are involved.

Three independent classes of failure were found, each sufficient on its own:

1. **No delegated cgroup v2 subtree in the container (host condition C1).** `/sys/fs/cgroup` is a cgroup2
   mount, but the job's cgroup belongs to a root-owned Slurm step (`system.slice/slurmstepd.scope/.../task_0`)
   and has no `nsdelegate`; the unit's own `RunCgroup.create` gets `EACCES` on every candidate parent. A run
   cgroup cannot be created, so a timeout cannot kill the run's cgroup and the no-waiver runner refuses.
2. **Yama `ptrace_scope = 0` on the NEMO2 H200 hosts (host condition C4).** The accepted unit refuses a run
   without the `ptrace_scope` waiver, and with that waiver the run is not effective.
3. **The accepted unit's own non-dumpable integrity check does not hold inside the apptainer job (new,
   container-specific, not waivable).** With the cgroup and ptrace conditions waived for diagnosis, the sandbox
   starts and the parent connects, but the runner **STOPs** with
   `the run's parent was traced (TracerPid None) or dumpable at the accept (True)` and record field
   `parent_dumpable_at_accept: true`. Every isolated run — CPU smoke and GPU smoke — is refused before any metric
   channel use. No `effective: true` record can be produced in the container, so condition 6/7 and §5.5 fail.

The v2 image itself is correct (digest as authorized, `VERSIONS.txt` markers match), the H200 GPU and plain CUDA
IPC work (a plain-process control opened the CUDA IPC tensor correctly), and the *worker sandbox* itself starts
inside the container (user/mount/PID/network/cgroup namespaces and `pivot_root` all work; the unit's own
`worker_sandbox_available` returns `ok` for both node interpreters on the accepted sandbox fix). The refusals are
in the host conditions and the container integration, not in the image or the GPU.

## Authority and inputs

- PLAN row **R1-T1-HOST-H200** on published main `4aac52092813b2b01ddb96cd7d135c390aeff645`: "the cluster agent
  checks in an ENGINEERING job that the harness isolation (R1-HARNESS-ISOLATION; READY 60 host checks) works
  inside the HTCondor container on H200; if it does not, the whole T1 table moves to Ada (the existing
  whole-table fallback)."
- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions and waivers), §4 (tests), §5 item 5 (§5.5:
  CUDA IPC across the PID namespace is untested on the development host), and the "For the experiment agent on
  Ada / TASL-7" list (items 1–7).
- Review `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`, round 8 **ACCEPTED**, code
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e`, branch `mac-harness-isolation-20261117` of `autoresearch_harness`.
- The Ada host check and its accepted sandbox fix (branch `ops-tasl-20261116` of this repo, **not** on published
  main): `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md` and
  `HARNESS_ISOLATION_FIX_20261119.md`. Fix code `5403392e94cb59d732f45d6702fc857531ad8fd5`, branch
  `mac-harness-isolation-fix-20261119`, independently ACCEPTED. It is used here only to separate a **code**
  defect from a **host** refusal; the as-instructed revision is `68cdd1a` (the accepted code on published main).
- Image authority **R1-QTORCH-AMEND** (PLAN): v2 gpu image
  `ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd`
  (tag `20261115-v2-e1cb6d8e`).
- Container-universe JDL conventions and the sweep-2 chunk layout (`/work/dwong/sweep2_launch_20261120/`,
  `docs/r1/reports/sweep2_20261116/S2_C2_UNIT.md`).

## Code revisions under test

| purpose | repo / branch | tip | role |
|---|---|---|---|
| as instructed | `autoresearch_harness` `mac-harness-isolation-20261117` | `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` | the accepted core (READY 60) that published main pins |
| sandbox-fix diagnostic | `autoresearch_harness` `mac-harness-isolation-fix-20261119` | `5403392e94cb59d732f45d6702fc857531ad8fd5` | accepted fix of the bind-remount and interpreter-symlink defects |

Both trees were archived (`src/autoresearch`, `tests/trackg`) from the harness repository into the job payload;
`harness_repo/repo_tips.txt` has the remote tips and the local hashes, `payload/payload_sha256.txt` the payload
hashes. Both revisions were probed with the same payload; the host-condition table uses the accepted revision
and the as-instructed result is reported separately.

## Job record

| field | value |
|---|---|
| cluster / process | **759828.0** (the only authoritative job; one start, `periodic_hold` on `NumJobStarts > 1`) |
| submit host / dir | `deepthought.etp.kit.edu`; `/work/dwong/iso_h200_20261121/stage` |
| submit / start / end (UTC) | 2026-11-21T00:33:38 / 01:08:58 / 01:16:26 (run 448 s, exit 0) |
| job host | **`g4402.nemo.privat`**, slot `slot1_3@nemo2_gpu-131c50fcda@g4402.nemo.privat`, `CloudSite = BwForCluster-Nemo2` |
| universe / image | `container` with `docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ece…`; runtime apptainer (`APPTAINER_COMMAND=exec`, `pid1_comm=appinit`), image `VERSIONS.txt` `build_utc=2026-11-16T00:19:23Z` (v2 markers) |
| resources | `request_GPUs=1`, `request_cpus=4`, `request_memory=16000`, `request_disk=20000000` kB, `+RequestWalltime=4000`, 1 GPU `GPU-c483223d` (H200, 143169 MiB, driver 620.70.06 / CUDA 13.5) |
| container iwd | `/srv` = HTCondor scratch `/var/lib/condor/execute/dir_2727771`; outputs transferred `out/` |
| job-level files | `out_759828/isolation_h200.{out,err,log}`, `jobs/job_ad_759828_{pre,post}.txt` |
| output integrity | the job's own `out/SHA256SUMS` verified on the submit host and again locally (all files OK) |

Two CPU-only submissions were made and cancelled because the site policy makes them impossible: the `Start`
expression on every GPU node is
`ifThenElse(TotalSlotGPUs > 0, TARGET.RequestGPUs isnt undefined && TARGET.RequestGPUs > 0, true)`. The 21 Nov
00:37 UTC reverse-analysis of the CPU-only job 759830 showed step `[7] … TARGET.RequestGPUs > 0` matching 0
clusters; it never started (`condor_rm 759830`). Its JDLs are kept (`jobs/isolation_h200_cpu.jdl`). The lead
confirmed the H200-only plan, so a supplementary CPU-node/L40S job was not used.

## Image and container

`out_759828/container_facts.txt`, `out_759828/host.json`:

- Image `r1-htc-gpu`, `build_utc=2026-11-16T00:19:23Z`, base `nvidia/cuda:12.4.1-cudnn-runtime-rockylinux9`,
  `torch_actual=2.6.0+cu124`, `env3_sorted_diff=empty`, `llama_server_sha256=f8d35fd3…`, harness env
  Python 3.13.4, tracks 3.11.18, trackp 3.12.15. The job ad's `ContainerImage` is exactly the authorized
  `sha256:b1144ece…` digest.
- Host `glibc`/OS: Rocky Linux 9.3, kernel `5.14.0-570.60.1+28.1.el9_6_ciq.x86_64`, appinit as PID 1; the job
  runs as uid `236760` (the site's `ka_jg9936` account), not root.
- The job's host cgroup is the Slurm step `system.slice/slurmstepd.scope/s08HM7V3H04W00/step_batch/user/task_0`
  (`/proc/self/cgroup`). `/sys/fs/cgroup` is a cgroup2 mount
  `rw,nosuid,nodev,noexec,relatime master:915` with controllers
  `cpuset cpu io memory hugetlb pids rdma misc` and **no `nsdelegate`** mount option.
- GPUs present: 4 × `NVIDIA H200`; only the assigned `GPU-c483223d` is visible through `CUDA_VISIBLE_DEVICES`;
  plain-process CUDA and CUDA IPC work (see C8).

## §3 conditions, one by one

| # | Condition (core report §3 / experiment-agent list) | Waiver | Result | Evidence |
|---|---|---|---|---|
| C1 | a cgroup v2 parent the run's uid can write, with `cgroup.kill` | `no_cgroup` | **FAIL** | `out_759828/cgroup.json`, `logs/cgroup.log` |
| C2 | the run is not root | `root` | **PASS** | `host.json`: `euid=236760` |
| C3 | unprivileged user namespaces with mount, PID and network namespaces (the sandbox probe) | `no_worker_sandbox` | **PASS** | `out_759828/userns.json`, `sandbox_*_fix_5403392e_*.json` |
| C4 | Yama `ptrace_scope >= 1` | `ptrace_scope` | **FAIL** | `host.json`: `/proc/sys/kernel/yama/ptrace_scope = 0` |
| C5 | timeout factor 3 (R1-TRACKG-PORT-DECISIONS (4)) | `timeout_factor` | **PASS** | `host.json`: `timeout_factor_check` |
| C6 | the run interpreter's `sys.path` holds no home directory / runs tree (hard `RunnerError`, no waiver) | none | **PASS** | `sandbox_*_*.json`: `sys_path_hard_check.ok = true` for all three interpreters, both revisions |
| C7 | a real sandboxed smoke whose record shows `effective: true` (experiment-agent item 6) | none taken | **FAIL** | `smoke_*.json`; no-waiver smoke refused, diagnostic smoke STOPs at accept |
| C8 | GPU smoke with the sandbox on, CUDA IPC across the PID namespace (§5.5) | none taken | **FAIL** | `gpu_smoke_diag.json`; sandboxed run STOPs before CUDA IPC; plain-process IPC control passes |

**Overall: FAIL (C1, C4, C7, C8).** No waiver was taken for any of these results; the diagnostic runs that used
waivers are labelled below and were never effective.

### C1 — no delegated cgroup v2 subtree (FAIL)

`probe_cgroup.py` tries the unit's own `isolation.RunCgroup.create` on the job's cgroup and its parents, the
cgroup v2 root and the systemd user-slice paths. Every candidate fails with `EACCES` ("Permission denied");
`user.slice/user-236760.slice` does not exist. Exact first failures:

```
/sys/fs/cgroup/system.slice/slurmstepd.scope/s08HM7V3H04W00/step_batch/user/task_0:
  cannot create the run cgroup …/ar_hostcheck_73_73_627622853: [Errno 13] Permission denied
/sys/fs/cgroup/system.slice/slurmstepd.scope/s08HM7V3H04W00/step_batch/user:
  cannot create the run cgroup …/ar_hostcheck_73_73_627921067: [Errno 13] Permission denied
/sys/fs/cgroup: cannot create the run cgroup …/ar_hostcheck_73_73_629049192: [Errno 13] Permission denied
/sys/fs/cgroup/user.slice: cannot create the run cgroup …/ar_hostcheck_73_73_629275085: [Errno 13] Permission denied
```

The job's cgroup is created and owned by the root Slurm step; `/sys/fs/cgroup` has no `nsdelegate`, so the uid
cannot create a child cgroup, cannot write `cgroup.kill` and cannot delegate a subtree to the run. The required
delegation (`systemd-run --user --scope -p Delegate=yes`, or a site-delegated subtree) is not present in an
HTCondor container job on NEMO2. There is no in-container workaround: cgroup v2 delegation needs the host's
systemd/slurm to delegate, not something a job can create.

### C2 — not root (PASS)

`host.json`: `euid = 236760`, user `ka_jg9936`, `HOME=/var/lib/condor/execute/dir_2727771`. The run records that
would be written also carry `euid: 236760` (the diagnostic run reached the record; see C7).

### C3 — unprivileged user namespaces + mount/PID/network + pivot_root (PASS) with a code-revision caveat

`userns.json` standalone probe (the same syscall shape as the sandbox): one `unshare(CLONE_NEWUSER|NEWNS|NEWPID|
NEWNET|NEWCGROUP)` → ok; uid/gid mapped `0 → 236760` → ok; `/` made private → ok; PID-1 `pivot_root` → **ok**;
detach old root → ok; fresh `/proc` over a bound `/proc` → **ok**; write in the new root → **ok**; read
`/proc/self/status` → ok. The host allows unprivileged user namespaces; AppArmor is not enabled on Rocky 9
(`kernel.apparmor_restrict_unprivileged_userns` absent), `user.max_user_namespaces = 2147483647`.

The unit's own `worker_sandbox_available` probe inside the container:

| revision | `/opt/r1/envs/trackp/bin/python` | `/opt/r1/envs/harness/bin/python` | `/usr/bin/python3` (3.9) |
|---|---|---|---|
| `68cdd1a` (as instructed) | **refused**: `worker sandbox setup failed at read-only /etc: PermissionError(1, 'remount: Operation not permitted')` | same refusal | same refusal |
| `5403392e` (accepted fix) | **ok** | **ok** | refused: `worker sandbox setup failed at pivot_root: OSError(14, 'read-only root: Bad address')` |

So **the host namespace capability is present, and the worker sandbox of the fixed accepted core starts inside
the container for both node environments.** The as-instructed `68cdd1a` refuses at a read-only bind remount: this
is the already-known review defect A (bind remount drops the source mount's locked `nodev`/`noexec` flags),
reproduced on NEMO2 H200: on this host `/sys` is `rw,nosuid,nodev,noexec` and the remount probe shows
`RDONLY|NOSUID` → EPERM, `RDONLY|NOSUID|NODEV` → EPERM, `RDONLY|NOSUID|NODEV|NOEXEC` → ok, and the source-locked
flags → ok (fix). The system Python 3.9 additionally fails the fixed sandbox at the final read-only root remount
(`EFAULT`); the two node interpreters that matter both pass.

The condition is a host-capability condition and is **PASS**; the refusal of the published accepted unit is a
separate code defect, already accepted as fixed in `5403392e` but not on published main.

### C4 — Yama ptrace_scope (FAIL)

`/proc/sys/kernel/yama/ptrace_scope = 0` inside the job (the host's sysctl value is visible and read-only). The
core unit refuses an isolated run without the `ptrace_scope` waiver, because during interpreter start-up before
the parent marks itself non-dumpable, an unrelated process of the same uid could attach. With the waiver a run is
`effective: false`. The NEMO2 H200 host does not have `ptrace_scope >= 1`.

### C5 — timeout factor 3 (PASS)

`host.json`: default `timeout_factor = 3.0`, `timeout = 30.0 s` at `measured_run_seconds = 10`, and a factor of 2
is refused with the reviewed message unless the `timeout_factor` waiver is given. The code-level condition holds
in the container.

### C6 — `sys.path` hard check (PASS)

For all three interpreters (trackp 3.12.15, harness 3.13.4, `/usr/bin/python3` 3.9) and both revisions the
unit's `_sandbox_config` hard check passes: none of the interpreter's `sys.path` entries is a home directory, the
runs tree or an ancestor of either. The interpreters live under `/opt/r1/...` (image-provided) and `/usr`; the
container's `HOME` is the job scratch, not a user home. Recorded paths are in the `sandbox_*_*.json` files.

### C7 — a real sandboxed smoke with `effective: true` (FAIL)

The no-waiver smoke (`smoke_fix_nowaiver`, `smoke_old_nowaiver`) is refused before any process starts because
there is no cgroup parent: `no writable delegated cgroup v2 parent was found (host condition C1 FAIL); an
isolated run with no waivers needs limits.cgroup_parent`.

The labelled **diagnostic** run (`smoke_fix_diag`, waivers `no_cgroup` and `ptrace_scope` recorded — never
effective) gets past the sandbox and the parent connection, then the accepted unit itself raises its
non-waivable integrity STOP:

```
STOP: the run's parent was traced (TracerPid None) or dumpable at the accept (True):
a process outside the run interfered
```

The would-be record field is `parent_dumpable_at_accept: true`, `parent_traced_by: null`. The recorded waivers
are `{"no_cgroup": "diagnostic-only host check: …", "ptrace_scope": "diagnostic-only host check: …"}` and the run
outcome is a refusal, not a classification. Consequently **no record with `effective: true` exists**, and this
condition fails even independently of C1/C4: with both waived the isolated run still does not complete.

Mechanism: `isolation.non_dumpable(pid)` answers "is `/proc/<pid>/status` owned by uid 0". On a bare host that is
true for a non-dumpable process; inside this apptainer job the container's process/PID and (most likely) user
namespace view does not present that owner as uid 0, so the unit treats a correctly non-dumpable parent as
"dumpable", writes the record and raises `IntegrityError` (a STOP). The Ada host check ran on a bare host as uid
1030 and its records had `parent_dumpable_at_accept: false`, so this is a container integration defect of the
accepted unit, not a NEMO2 namespace capability problem. It needs a code change (a container-aware
non-dumpable test) and an independent review; it is not waivable.

The unit's own test file reproduces a second sandbox refusal on the same container: with the fix revision,
`pytest tests/trackg/test_trackg_isolation.py` (deselecting the helper-timed test that hangs on refusal) is
**12 failed, 10 passed, 5 skipped, 1 deselected in 1.85 s**; every failure is the same
`RunnerError: this host refuses the worker sandbox (… 'read-only root: Bad address')` because the tests use
`interpreter="python3"` (the image's `/usr/bin/python3` 3.9), which fails the fixed sandbox as recorded under C3.
Node environments are unaffected. Logs: `out_759828/logs/pytest_isolation.log`.

### C8 — GPU smoke / CUDA IPC across the PID namespace (§5.5) (FAIL)

The GPU was allocated and reachable: `gpu_smoke_diag.json` records
`NVIDIA H200`, capability 9.0, 143168.9 MiB total, 142642.1 MiB free at start, driver 620.70.06, CUDA 13.5. The
plain-process control (create the tensor in one process, `ar_isolated.cuda_share` → `ar_isolated.cuda_open` in a
separate ordinary process) **passes** (`plain_control.plain_ipc_ok: true`, values 0.0, 1.5, … 10.5), so the H200
and CUDA IPC work on this host.

The sandboxed GPU smoke never reaches CUDA IPC: the same **STOP** as C7 is raised at the accept of the isolated
run (`gpu_smoke_diag.json`, `refusal_reason` identical, `parent_dumpable_at_accept: true`). The same would happen
with no waivers at C1 first. Therefore the §5.5 question — does CUDA IPC work from inside the worker's user/PID/
mount namespaces — **cannot be exercised in this container** until the harness can start an isolated run there.
The aggregate called this "no GPU probe result" because the 1-GPU no-waiver branch was skipped; the exact refusal
is in `out_759828/gpu_smoke_diag.json` and that is the operative evidence.

The GPU was used only by its own allocated job: one 8-float tensor in the plain control (about 0.5 GiB resident
at probe start was the job's own interpreter context; it returned to the initial state). It did not touch any
sweep-2 job's card.

## Run-record fields

No run record with `effective: true` exists in this container (see C7), so the §3 "record's isolation block"
could not be produced as specified. The diagnostic run's would-be fields, as far as they were reached:

| field | value |
|---|---|
| `effective` | not written — the runner raised `IntegrityError` (STOP) before the record was accepted |
| `waivers` | diagnostic only: `no_cgroup`, `ptrace_scope` (labelled; never effective) |
| `exceptions` | `[]` |
| `euid` | `236760` (non-root) |
| `ptrace_scope` | `0` |
| `nsdelegate` | `false` (no `nsdelegate` on the `/sys/fs/cgroup` mount) |
| `cgroup` | `null` — no run cgroup could be created (C1) |
| `worker_sandbox` | present (the sandbox starts with the fixed core for node interpreters) |
| `parent_traced_by` | `null` |
| `parent_dumpable_at_accept` | **`true`** — the STOP |

## Overall verdict

**FAIL.** Conditions C1 (delegated cgroup v2 subtree), C4 (`ptrace_scope >= 1`), C7 (real smoke with
`effective: true`) and C8 (§5.5 GPU smoke) fail; C2, C3, C5 and C6 pass. No waiver was taken for the acceptance
result; the two diagnostic runs are labelled and were never effective.

## What this means for the T1 table

Per PLAN row **R1-T1-HOST-H200**: the harness isolation does not work inside the HTCondor container on NEMO2
H200, so **the whole T1 table moves to Ada** (the existing whole-table fallback). This check does not itself
decide anything else about T1; it records the H200 container blocker. What would have to change before a re-check
could pass:

1. **Site/host:** delegate a writable cgroup v2 subtree with `cgroup.kill` and `nsdelegate` to container jobs
   (C1), and set `kernel.yama.ptrace_scope = 1` on the NEMO2 H200 hosts (C4). Neither is a repository change.
2. **Harness code (accepted unit):** make the non-dumpable integrity check container-aware (C7/C8 STOP), and
   merge the already-accepted bind-remount/interpreter fix `5403392e` into the accepted line (the published
   `68cdd1a` cannot start its sandbox on this host at all); then re-run this check.
3. Only then could the §5.5 GPU smoke be exercised, and only a later check could decide it.

For Ada: the Ada host check (branch `ops-tasl-20261116`) records condition 6 PASS with `effective: true` after
the fix, and condition 7 (CUDA IPC across the PID namespace) blocked by a driver-level namespace limitation
there. That is the existing state the T1 table falls back to; the author/coordinating chat owns the decision.

## Integrity of this check

- No T1 label run, no Track G U2/census run, no sweep-2 change, no change to `main`, no push, no deletion.
- The sweep-2 jobs (16 chunks, submitted 01:17 CET) were not modified, cancelled or reprioritised. The check job
  was submitted at priority 0 after them and waited in the same-user FIFO; it used one H200 for its own 448 s
  run only. The two old idle probe jobs 759624/759625 were not touched.
- The 1-GPU job was submitted once and started once (`NumJobStarts = 1`, `periodic_hold` on a second start); no
  retry was made. The CPU-only attempts 759829/759830 never started and were removed; their JDLs are kept.
- Output integrity: the job's `out/SHA256SUMS` was verified on the submit host and locally; the report's
  captures directory has its own `SHA256SUMS`.
- Evidence is filed on `/ceph/srv/dwong/paperb/isolation_h200_20261121T0033Z/` (inputs, job outputs, logs) and in
  the sibling captures directory of this report.

## Capture index

Sibling directory `T1_H200_ISOLATION_CHECK_20261121_captures/`:

- `out_759828/` — the transferred `out/` of job 759828 exactly as produced: `isolation_check.json` (aggregate),
  `host.json`, `userns.json`, `cgroup.json`, `cgroup_parent.txt`, `container_facts.txt`,
  `sandbox_{old_68cdd1a,fix_5403392e}_{harness,trackp,usr}.json`, `smoke_*.json`, `gpu_smoke_diag.json`,
  `pytest_isolation.json`, `logs/` (every step's stdout/stderr), the job's `SHA256SUMS`, `step_results.txt`, and
  the job-level `isolation_h200.{out,err,log}`.
- `payload/` — every probe/aggregate script and the wrapper that ran, their hashes.
- `jobs/` — the submitted H200 JDL, the impossible CPU-only JDLs, the pre/post job ads.
- `harness_repo/repo_tips.txt` — the harness branch tips and accepted tree hashes.
- `SHA256SUMS` — hashes of every file above.
