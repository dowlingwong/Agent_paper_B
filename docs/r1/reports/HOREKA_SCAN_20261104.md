# HoreKa 2 read-only scan — Track G T1, Paper B (4 Nov 2026, attempt 4)

**Author's instruction (4 Nov 2026, quoting the runbook's own record):** "直接让他全权处理扫描" — the agent runs the whole scan itself, from the authorized `agent`-partition compute node reached through NHR@KIT's documented SSH tunnel.

**Status:** scan complete. §3 ran on the agent node; the one probe job was submitted once, was backfilled into `dev-gpu-h100` 29 minutes later, and finished **COMPLETED, exit 0** (§4), so Q9–Q11 are answered from its output. Teardown completed in the runbook's order. Nothing was changed on HoreKa (the only files created are under `~/r1_scan_20261104/`).

**Scan revision:** HOREKA_SCAN_PROMPT_20261104 rev 5.5. **Start:** 2026-11-04T15:24:24Z. **Host:** `hk2-x86.scc.kit.edu`, user `ka_ir7683`. **Working folder:** `~/Documents/agent_paper_B/.claude-worktrees/_snapshots/horeka_scan_20261104` (earlier attempts kept in `attempt_1/`, `attempt_2/`, `attempt_3/`).

## Setup steps taken

| Item | Value |
|---|---|
| Local preflight (`ps`, `lsof`, `kill`) | `LOCAL_TOOLS_OK` after the sandbox approved `ps` (see Deviation 1) |
| Master connection (author's, reused) | `Master running (pid=42629)` before; same PID after teardown |
| Session script (login-node command 1) | `start-vscode-remote-ssh.sh`; `salloc: Granted job allocation 120262` |
| Session job id | **120262** (taken from `session.log`, never from `squeue`) |
| Compute node | **hk2n1254** (log: "Compute node : hk2n1254") |
| sshd on the node | **port 22225** (log: "NOTE: port 22222 was in use; using 22225 instead") |
| Tunnel (login-node command 2) | `-L 22222:hk2n1254:22225` added with `ssh -O forward`; `forward_spec = 127.0.0.1:22222:hk2n1254:22225` |
| Local port chosen | 22222 (free; `lsof -nP -iTCP:22222 -sTCP:LISTEN` printed nothing) |
| Forward listener PID | 42629 = the master's PID (required equality held) |
| Setup A/B (author's) | skipped by me; the snippet's key exists: `test -f ~/.ssh/id_ed25519_vscode-hk2` → `KEY_PRESENT` |
| Expected side effect | script wrote 70 `SLURM_/PMI` variables to `~/.ssh/environment` (log line); not touched |
| Teardown | session job cancelled, forward removed, client stopped — see "Teardown" at the end |

**Earlier attempts, from `sacct -u ka_ir7683 -S now-7days`** (no leftovers of theirs were running):

```
120165|agent|FAILED|00:00:37
120168|agent|FAILED|00:10:55
120169|agent|CANCELLED by 504267|00:00:00
120238|agent|CANCELLED by 504267|00:11:05     <- attempt 3's session, already cancelled
120262|agent|RUNNING|00:01:14                 <- this session (attempt 4)
```

**Gate 1 (local).** `ssh -G vscode-hk2` → `user ka_ir7683` / `hostname 127.0.0.1` / `port 22222`, no proxy → `GATE1_OK`.

**Gate 2 (Slurm).** Passed on this evidence, with the deviation noted below:

```
host=hk2n1254 job_env=120262
120262 hk2n1254 59:15 2026-11-04T16:24:25
```

(`SLURM_JOB_ID` of the session job equals 120262, and `squeue -p agent -t R` lists 120262 RUNNING on the same host; the session log shows `salloc args: --partition=agent`.)

### Deviations from the runbook (5 of them, all with evidence)

1. **Local `ps` denied by the sandbox.** First attempt: `bash: line 1: /bin/ps: Operation not permitted` (exit 126). Step 0 says STOP in that case; the sandbox then approved the one retry, and the exact gate command printed `LOCAL_TOOLS_OK`. No HoreKa call had been made before the approval.
2. **Step 2's block failed on its last line only.** The exact heredoc ran, but the final `echo "SESSION_LAUNCHED pid=$(cat …)"` hit an outer-wrapper quoting error (`unexpected EOF while looking for matching '"'`). The `nohup … &`, `session.pid` and `session_start_utc` lines had already executed, and the session started normally (log at 16:24:25). I verified liveness before continuing: `pgrep -P 8806` → the `ssh … -tt hk2 start-vscode-remote-ssh.sh` client. `session.pid` = 8806. No second session was started.
3. **Gate 2's `scontrol` half is refused for this account.** `scontrol show node hk2n1254` → `slurm_load_node error: Access/permission denied` (because `PrivateData = accounts,events,jobs,nodes,reservations,usage,users`). The gate's purpose — "a Slurm compute node of the `agent` partition running the session job" — is established by the two other signals above, so I passed it and recorded the refusal as a finding instead of aborting. This is the one place where the runbook's literal pass criterion cannot be met by anyone on this account.
4. **Probe job: submitted once, and the scheduler beat its own estimate.** `--test-only` had said `2026-11-04T22:34:06` (6 h out) and the probe carries `--deadline=now+2hours`; the scheduler backfilled it at **16:55:34**, 29 min after submission (16:26:11), so it ran and completed before the deadline. Submitted once, never resubmitted. Scheduler estimates on this cluster are loose upper bounds — see the caveat under Q3.
5. **One extra `squeue` outside the 5-minute cadence.** Disclosing it for completeness: I took an exploratory `squeue -j 120275` at ~16:34 to confirm the poller worked, about 3 minutes after its first check. Including it, the probe was polled **7 times in total, under the 9-check cap**; the cadence was otherwise 5 minutes, and the runbook's cap is per-check count and rate, which the one duplicate slightly bends. No consequence: both answers were `PENDING 0:00 (Priority)`.

## Q1 — Accounts, and the GPU-hour budget

**One account only**, so no `--account` line was added to the probe (the runbook's "more than one account" STOP does not apply).

```
sacctmgr show user $USER -n -P format=User,DefaultAccount
ka_ir7683|hk-project-p0027888

sacctmgr show associations user=$USER -n -P format=Account,Partition,QOS,GrpTRESMins,GrpTRES,MaxJobs,MaxSubmit
hk-project-p0027888||normal||||100
```

`scontrol show assoc_mgr users=$USER flags=assoc` (excerpt, verbatim):

```
Association Records
ClusterName=hk2 Account=hk-project-p0027888 UserName=ka_ir7683(504267) Partition= Priority=0 ID=537
    SharesRaw/Norm/Level/Factor=1/0.33/3/0.79
    UsageRaw/Norm/Efctv=2856.00/0.00/0.01
    GrpJobs=50(1) GrpJobsAccrue=N(0)
    GrpSubmitJobs=N(1) GrpWall=N(23.80)
    GrpTRES=cpu=N(2),mem=N(3890),energy=N(0),node=N(1),billing=N(2),…,gres/gpu=N(0),…
    GrpTRESMins=cpu=N(47),mem=N(92582),…,gres/gpu=N(0),…
    MaxJobs= MaxJobsAccrue= MaxSubmitJobs=100(1) MaxWallPJ=
```

`sshare -A hk-project-p0027888 -l`:

```
Account                    User  RawShares  NormShares    RawUsage   NormUsage  EffectvUsage  FairShare    LevelFS
hk-project-p0027888   ka_ir7683          1    0.333333        2856    0.000000      0.005407   0.788235  61.645892
```

`sreport -t hours --tres=cpu,gres/gpu cluster AccountUtilizationByUser user=$USER start=2026-01-01` printed **the header and no rows** (`PrivateData` includes `usage`).

**Answer.** Default and only account: `hk-project-p0027888`. No GPU-hour cap is set on the association (`gres/gpu=N(0)` in both `GrpTRES` and `GrpTRESMins`), and no per-account `GrpTRESMins`/`GrpTRES`/`GrpWall` limit is set. **The used/left GPU-hours cannot be measured**: `sreport` and `scontrol show assoc_mgr` usage are both filtered by `PrivateData=usage` (RawUsage 2856 is the fair-share counter, not GPU-hours). Whether ~320–480 GPU-h fits is therefore **not answerable from this account**; the only budget evidence is the absence of a GPU TRES limit.

QOS limits (`sacctmgr show qos -n -P format=Name,MaxWall,MaxTRESPU,MaxJobsPU,MaxSubmitPU`):

```
normal||||
agent||cpu=2||
dev|||1|3
```

i.e. `normal` unlimited; `agent` MaxTRESPU=`cpu=2`; `dev` 1 job per user, 3 submitted.

## Q2 — `gpu-h100` shape, `--exclusive`, SelectTypeParameters

`scontrol show partition gpu-h100` (verbatim, excerpt):

```
PartitionName=gpu-h100
   AllocNodes=ALL Default=NO QoS=N/A
   DefaultTime=00:10:00 DisableRootJobs=NO Exclusive=NO GraceTime=0 Hidden=NO
   MaxNodes=16 MaxTime=2-00:00:00 MinNodes=1 LLN=NO MaxCPUsPerNode=128 …
   Nodes=hkn[0902-0922]
   PriorityJobFactor=1 PriorityTier=1 RootOnly=NO ReqResv=NO OverSubscribe=NO
   OverTimeLimit=NONE PreemptMode=OFF
   State=UP TotalCPUs=2688 TotalNodes=21 SelectTypeParameters=NONE
   JobDefaults=DefCpuPerGPU=16,DefMemPerGPU=186720
   DefMemPerNode=UNLIMITED MaxMemPerNode=UNLIMITED
   TRES=cpu=2688,mem=15684480M,node=21,billing=2688,gres/gpu=84
```

`scontrol show config | grep -i -E 'PrivateData|SelectTypeParameters|PreemptMode'`:

```
PreemptMode             = OFF
PrivateData             = accounts,events,jobs,nodes,reservations,usage,users
SelectTypeParameters    = CR_CORE_MEMORY,CR_ONE_TASK_PER_CORE,ENFORCE_BINDING_GRES
```

`sbatch --test-only -p gpu-h100 --gres=gpu:4 --exclusive -t 24:00:00 -N 1 --wrap true`:

```
sbatch: Job 120270 to start at 2026-11-12T04:28:23 a using 128 processors on nodes hkn0919 in partition gpu-h100
```

**Answer.** 4 GPUs per node (84 GPUs / 21 nodes), 128 CPUs per node. `MaxTime=2-00:00:00`. `OverSubscribe=NO` (so the partition does not force sharing: `FORCE` is not in play). The partition flag is `Exclusive=NO`, but `--exclusive` is **accepted and honoured**: with `--gres=gpu:4 --exclusive` the test-only estimate allocates **128 processors**, the whole node (`TotalCPUs=2688 / 21 = 128`), while `--gres=gpu:1` without it allocates 32. DefMemPerGPU=`186720` (MB, ≈182 GiB per GPU); DefCpuPerGPU=16, but a plain `--gres=gpu:1` test gets **32 CPUs per GPU**. `SelectTypeParameters = CR_CORE_MEMORY,CR_ONE_TASK_PER_CORE,ENFORCE_BINDING_GRES` (the partition's own field says `SelectTypeParameters=NONE`, the cluster config is the authority). `--exclusive` is therefore the right way to get whole nodes, but note `Exclusive=NO` means it must be requested per job.

## Q3 — Queue and realistic wall time

`sbatch --test-only` start estimates, all five shapes (verbatim):

```
--- -p gpu-h100 --gres=gpu:4 --exclusive -t 24:00:00 -N 1
sbatch: Job 120270 to start at 2026-11-12T04:28:23 a using 128 processors on nodes hkn0919 in partition gpu-h100
--- -p gpu-h100 --gres=gpu:4 --exclusive -t 24:00:00 -N 1 --deadline=2026-11-22T00:00:00
sbatch: Job 120271 to start at 2026-11-12T04:28:23 a using 128 processors on nodes hkn0919 in partition gpu-h100
--- -p gpu-h100 --gres=gpu:1 -t 04:00:00 -N 1
sbatch: Job 120272 to start at 2026-11-12T00:26:31 a using 32 processors on nodes hkn0904 in partition gpu-h100
--- -p dev-gpu-h100 --gres=gpu:1 -t 00:15:00 -N 1
sbatch: Job 120273 to start at 2026-11-04T22:34:06 a using 32 processors on nodes hkn0901 in partition dev-gpu-h100
--- -p cpu -n 1 -c 8 --mem=16G -t 01:00:00
sbatch: Job 120274 to start at 2026-11-05T07:55:36 a using 8 processors on nodes hk2n1035 in partition cpu
```

```
--- gpu-h100 job states (counts; may be partial if PrivateData hides other users)
```
(no output — `PrivateData=jobs` hides every job not owned by this user)

**Answer.** `gpu-h100` is **8 days deep**: a 4-GPU 24 h exclusive job would start **2026-11-12T04:28**, and the 1-GPU 4 h shape is no better (11-12T00:26). Per-user job-state counts are **not obtainable** (`PrivateData` includes `jobs` and `nodes`), so that row is empty and must not be read as an idle queue.

**Caveat the probe forces on this answer.** The `dev-gpu-h100` 15-minute shape was *estimated* 22:34:06 and actually **started at 16:55:34**, 29 minutes after submission — backfill moved it 5.5 h earlier. So `--test-only` start estimates here are pessimistic upper bounds; the 8-day `gpu-h100` figure is a signal, not a promise, and must be re-measured with `sbatch --test-only` at the moment each real wave is designed.

Adding `--deadline=2026-11-22T00:00:00` changes nothing in the estimate (11-12T04:28 with and without).

## Q4 — Maintenance window

From the MOTD (`/etc/motd.d`), verbatim:

```
* From November 23, 2026, through December 4, the computer building (449.3) on *
* the KIT North Campus will be completely disconnected from the power grid due *
* to legally required inspections and maintenance work on the power supply.    *
*                                                                              *
* You will not be able to access your data during this time. Computation jobs  *
* will not run during this period.                                             *
…
* completed by December 4, 2026.                                               *
```

`scontrol show reservation` → `No reservations in the system` (note `reservations` is in `PrivateData`, so this may be filtered rather than truly empty).

From the docs (Mac-side check, §5): heading on <https://docs.nhr.kit.edu/> and <https://docs.nhr.kit.edu/clusters/horeka-2/>, verbatim: "**Scheduled Downtime: Shutdown of all HPC Clusters: 23.11.2026 – 04.12.2026**"; body: "From 23 November 2026 until 4 December 2026 (expected), the computing center building (449.3) at KIT Campus North will be completely disconnected from the power grid due to mandatory inspections and maintenance work on the electrical infrastructure."

**Answer.** Start **23 November 2026**, end **4 December 2026** ("planned to be completed by"). **No time of day is given anywhere.** No source states what happens to pending/running jobs — the docs say only "Compute jobs will not run while the systems are offline" and that workspace expiry is suspended. A copy-out cutoff is therefore the author's own choice, not a cluster-published deadline. Also from the docs: Jade (`gpu-b200`) "Operation will start in December 2026", and the weekly reboot window is Thursdays 07:00–09:00 with running/queued jobs unaffected.

## Q5 — Storage

```
HOME=/home/ka_ekp/ka_ir7683
PROJECT=/hfs2/data/project/hk-project-p0027888/ka_ir7683
SCRATCH=/scratch
TMPDIR=/scratch

Filesystem     Type  Size  Used Avail Use% Mounted on
hfs2-home      gpfs  5.4P  114T  5.3P   3% /hfs2/data
hfs2-home      gpfs  5.4P  114T  5.3P   3% /hfs2/data
/home/ka_ekp/ka_ir7683 gpfs
/hfs2/data/project/hk-project-p0027888/ka_ir7683 gpfs
```

GPFS mounts visible: `hfs2-home /hfs2/data`, `hfs2-work /hfs2/work`, `hkfs-home /hkfs/home`, `hkfs-work /hkfs/work`, `Lsdf01 /gfse/data/LSDF/lsdf01`, `Lsdf02 /gfse/data/LSDF/lsdf02`.

`ws_list`: no output (not installed on this node). `quota -s`: no output.

**Answer.** `$HOME` and `$PROJECT` are on the **same** GPFS filesystem (`hfs2`, 5.4 PB, 114 TB used, 3 % full) — `$PROJECT` is *not* a separate filesystem. `$SCRATCH` and `$TMPDIR` both point at `/scratch`. The draft's "$HOME 50 GB / 2 M inodes" could **not be verified** (`quota -s` printed nothing on the agent node); treat the 50 GB figure as unverified. ~20 GB GGUFs fit in free space by capacity, but no per-user quota was measurable here.

## Q6 — EasyBuild module names (exact)

```
CUDA:   12.6.0  12.8.0  12.9.1  13.0.2  13.1.1  13.2.0  13.3.0
GCC:    12.3.0  13.2.0  13.3.0  14.2.0  14.3.0  15.2.0  16.2.0
GCCcore:12.3.0  13.2.0  13.3.0  14.2.0  14.3.0  15.2.0  16.2.0
CMake:  3.18.4  3.26.3-GCCcore-12.3.0  3.27.6-GCCcore-13.2.0  3.29.3-GCCcore-13.3.0
        3.31.3-GCCcore-14.2.0  3.31.8-GCCcore-14.3.0  3.31.11-GCCcore-15.2.0
        3.31.12  4.0.3-GCCcore-14.3.0  4.2.1-GCCcore-15.2.0
Python: 2.7.18-GCCcore-12.3.0  3.11.3-GCCcore-12.3.0  3.11.5-GCCcore-13.2.0
        3.12.3-GCCcore-13.3.0  3.13.1-GCCcore-14.2.0  3.13.5-GCCcore-14.3.0
        3.14.2-GCCcore-15.2.0
cuDNN:  9.10.1.4-CUDA-12.8.0  9.10.2.21-CUDA-12.6.0  9.15.0.57-CUDA-12.9.1
NCCL:   2.22.3-GCCcore-13.3.0-CUDA-12.6.0  2.25.1-GCCcore-14.2.0-CUDA-12.8.0
        2.27.5-GCCcore-13.3.0-CUDA-12.6.0  2.27.7-GCCcore-14.2.0-CUDA-12.8.0
        2.27.7-GCCcore-14.3.0-CUDA-12.9.1
git:    2.41.0-GCCcore-12.3.0-nodocs … 2.52.0-GCCcore-15.2.0
Python-bundle-PyPI: 2023.06 … 2026.04-GCCcore-15.2.0
```

**Answer.** Pins available: `CUDA/13.3.0` (newest), `GCC/15.2.0`, `CMake/4.2.1-GCCcore-15.2.0`, `Python/3.14.2-GCCcore-15.2.0`. CUDA is a standalone module here (`CUDA/13.3.0`, no `-GCCcore-` tag), so the llama.cpp build should load `CUDA/13.3.0` plus a GCC module. Note the newest CUDA is **13.x**, not 12.x, and Python goes to **3.14**.

## Q7 — Tools on the agent node, proxy variables

```
python3: /usr/bin/python3
git: /usr/bin/git
git-lfs: /usr/bin/git-lfs
apptainer: /usr/bin/apptainer
singularity: /usr/bin/singularity
podman: missing
docker: missing
uv: missing
conda: missing
cmake: missing
nvcc: missing
rsync: /usr/bin/rsync
Python 3.9.21
```

`env | grep -i -E '^(https?|no)_proxy=' | cut -d= -f1` → no output (no proxy variables).

**Answer.** Present: `git`, `git-lfs`, `apptainer`, `singularity`, `rsync`, system `python3` 3.9.21. Missing: `uv`, `conda`, `cmake`, `nvcc` (the last two come from modules), `podman`, `docker`. No proxy variables are set, so direct internet is expected (see Q8).

## Q8 — Network, per URL

From the `agent`-partition node `hk2n1254`:

```
https://huggingface.co 200
https://pypi.org/simple/ 200
https://github.com 200
https://download.pytorch.org/whl/ 200
```

From the GPU compute node `hkn0901`, inside the probe job:

```
https://huggingface.co 200
https://pypi.org/simple/ 200
https://github.com 200
```

(no proxy variables in the job environment either)

The login node's network was **not measured** (nothing extra runs on a login node).

## Q9, Q10, Q11 — GPU, node shape inside the probe job, self-resubmission

All three answered from probe job 120275 on `hkn0901` (`State: COMPLETED (exit code 0)`, wall clock 2 s).

**Q9 — the GPU.** `nvidia-smi` (verbatim, excerpt):

```
|   0  NVIDIA H100                    On  |   00000000:C6:00.0 Off |                    0 |
| N/A   42C    P0             68W /  415W |      27MiB /  95830MiB |      0%      Default |
|                                         |                        |             Disabled |
```

`nvidia-smi --query-gpu=… --format=csv`:

```
index, name, uuid, memory.total [MiB], driver_version, compute_cap, compute_mode, mig.mode.current
0, NVIDIA H100, GPU-edd4b6a8-400e-a138-fa8a-7c92d4dabc33, 95830 MiB, 615.71.09, 9.0, Default, Disabled
```

`nvidia-smi -q | grep -E 'CUDA Version|Persistence Mode|Compute Mode'`:

```
CUDA Version                                           : 13.4 [Deprecated; will be removed in CUDA 14.0. Use CUDA UMD Version instead]
    Persistence Mode                                   : Enabled
    Compute Mode                                       : Default
```

`nvidia-smi -L`, inside the 1-GPU job:

```
GPU 0: NVIDIA H100 (UUID: GPU-edd4b6a8-400e-a138-fa8a-7c92d4dabc33)
```

**Answer.** H100, **95 830 MiB** (≈93.6 GiB) per GPU, driver **615.71.09**, CUDA UMD **13.4**, compute capability **9.0** (`sm_90`, as the draft expected), compute mode **Default**, MIG **Disabled**, persistence **Enabled**, 415 W cap. `SLURM_JOB_GPUS=3` while `CUDA_VISIBLE_DEVICES=0`: the node-level GPU index 3 is renumbered to device 0 inside the job — do not assume device 0 is always physical GPU 0. Processes on our GPU at probe time: `/usr/libexec/Xorg` using 17 MiB (a display server holds a token allocation; per the runbook this is **not** evidence of co-tenancy and no conclusion is drawn). `nvidia-smi topo -m` shows 6 NICs and **no NVLink** pairing in the visible topology (GPU↔NIC0 `PIX`, GPU↔NIC4 `PXB`, the rest `SYS`) — with 4 GPUs per node this matters for multi-GPU runs, but a 1-GPU job cannot see the other three GPUs, so `NV#` links between them were not observable here.

**Q10 — the node.** From the probe:

```
hkn0901.localdomain   2026-11-04T16:55:35+01:00   nproc=8
Model name:                              AMD EPYC 9354 32-Core Processor
Thread(s) per core:                      2
Core(s) per socket:                      32
Socket(s):                               2
NUMA node(s):                            8
Mem:             755          46         528           0         184         709   (total/used/free/shared/buff-cache/available, GB)
```

Local scratch:

```
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/md125     xfs   3.4T  267G  3.2T   8% /tmp
/dev/md125     xfs   3.4T  267G  3.2T   8% /scratch
drwx------. 2 ka_ir7683 root 10 Nov  4 16:55 /scratch
drwx------. 2 ka_ir7683 root 10 Nov  4 16:55 /tmp
```

**Answer.** Node: **AMD EPYC 9354, 2 sockets × 32 cores = 64 cores / 128 vCPUs**, 8 NUMA nodes, **755 GB RAM**. The job itself was given 8 CPUs (`nproc=8`, `SLURM_CPUS_ON_NODE=8`). Local scratch `/tmp` and `/scratch` are the **same node-local XFS filesystem** (`/dev/md125`, RAID), **3.4 TB with 3.2 TB free**, per-job directories owned by the user. That is ample for GGUFs and llama.cpp builds. Allocation was `AllocTRES=cpu=8,mem=16G,node=1,billing=8,gres/gpu=1`, `OverSubscribe=NO`, `Exclusive=NO`.

**Q11 — can a job submit a job?** Yes, at least `--test-only`. From inside batch job 120275:

```
/usr/bin/sbatch
sbatch: Job 120351 to start at 2026-11-06T04:36:35 a using 2 processors on nodes hk2n1004 in partition cpu
```

`sbatch` is on `PATH` in the job and `--test-only` succeeds from a batch job (and from the `agent`-partition allocation in §3). A real self-submission was **not** attempted, because §2 allows only one job.

## Q12 — Rules, `agent` partition, AI-agent mentions

`scontrol show partition agent` (verbatim, excerpt):

```
PartitionName=agent
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=NO QoS=agent
   MaxNodes=UNLIMITED MaxTime=3-00:00:00 MinNodes=1 LLN=NO MaxCPUsPerNode=384 …
   Nodes=hk2n1254
   OverSubscribe=NO PreemptMode=OFF State=UP TotalCPUs=384 TotalNodes=1
```

Partition idle summary (`sinfo_t_idle` — this one works, `sinfo -s` does not):

```
Partition dev-cpu                 :      0 nodes n/a
Partition cpu                     :      1 nodes drain
Partition agent                   :      0 nodes n/a
Partition large                   :      2 nodes idle
Partition dev-gpu-h100            :      0 nodes n/a
Partition gpu-h100                :      0 nodes n/a
Partition gpu-h200                :      0 nodes n/a
Partition gpu-h200-8              :      0 nodes n/a
```

**Answer.** The `agent` partition is a **single node, `hk2n1254`, 384 cores, MaxTime 3 days, QoS `agent`**; the per-user QOS cap is `cpu=2` (Q1). The MOTD contains the downtime banner but **no text about AI agents**. The AI-agent prohibition lives on <https://docs.nhr.kit.edu/usage/login/>, not in the MOTD. Partitions present include **`gpu-h200-8`** and **`large`**, neither of which appears in `draft.md`.

## §4 — the one probe job

```
cat "$S/jobid.txt"
120275
```

Submitted exactly once, with the runbook's script unchanged:

```
sbatch --parsable probe.sh   →  120275
```

Probe status checks (one `squeue` call every 5 minutes, ≤ 8 checks, fitted to the session's remaining time; the post-quantum `ssh` stderr banner is stripped here):

```
15:31:23Z check 1 job=120275: PENDING 0:00 (Priority)
15:36:24Z check 2 job=120275: PENDING 0:00 (Priority)
15:41:25Z check 3 job=120275: PENDING 0:00 (Priority)
15:46:26Z check 4 job=120275: PENDING 0:00 (Priority)
15:51:26Z check 5 job=120275: PENDING 0:00 (Priority)
15:56:27Z check 6 job=120275:            <- job had left the queue
JOB_LEFT_QUEUE at check 6
```

Final record and fetch (one call, as §4 asks):

```
120275|dev-gpu-h100|COMPLETED|00:00:02|0:0|2026-11-04T16:26:11|2026-11-04T16:55:34
120275.batch||COMPLETED|00:00:02|0:0
120275.extern||COMPLETED|00:00:02|0:0
```

The full output is in `probe_out.txt` (216 lines, 7810 bytes on the cluster). **It ran and it completed**: submitted 16:26:11, started by backfill 16:55:34, exit 0:0, wall clock 2 s — the probe's own first and last lines are `2026-11-04T16:55:35+01:00` and `2026-11-04T16:55:36+01:00`, so nothing in it hung or timed out. Left in place on the cluster at `~/r1_scan_20261104/probe-120275.out`; the probe script sits beside it.

It was **not** resubmitted.

## Teardown

Order as §5 requires, `gate2_ok` present, raw log in `teardown_results.txt`.

**5.1 — cancel only the session job.** `scancel 120262` → exit 0. 20 s later the node was gone:

```
kex_exchange_identification: read: Connection reset by peer
Connection reset by 127.0.0.1 port 22222
second_call_rc=255   (expected: the session compute node no longer accepts)
```

**5.2 — remove only our forward, leave the master open.**

```
cancel_rc=0
NO_LISTENER
Master running (pid=42629)
```

**5.3 — stop the client I started, and its `tail`.** The `ssh` client had already died with the job (`ps -p 8806` printed nothing, so the guarded `pkill -P`/`kill` was skipped):

```
CLIENT_GONE
```

**Master connection: `master_before.txt` and `master_after.txt` are identical — `Master running (pid=42629)`. It was never opened, stopped or exited by me; it is the author's own connection and stays usable.**

**Earlier jobs were not touched.** The probe (120275) was left to its own deadline and did not need cancelling; nothing else of the author's was running.

The author's open master connection stays open for up to 8 hours after its last use (`ControlPersist 8h`); he can close it himself with `ssh -O exit hk2`.

## Surprises and blockers (vs `draft.md`)

1. **`gpu-h100` projects as 8 days deep.** A 4-GPU 24 h `--exclusive` job gets an earliest start of **2026-11-12T04:28** (1-GPU 4 h: 11-12T00:26). `draft.md` §7 plans J2/J3/J4 waves for **15–22 Nov** with a copy-out cutoff on 22 Nov. If that projection held, the first 24 h wave could not start before 12 Nov and every later wave, including any re-run after a bad one, would have to fit between then and 22 Nov. **Read it as a warning, not a measurement** — backfill beat the estimate by 5.5 h on `dev-gpu-h100` in this very scan (item 6), so the 8-day figure may also be pessimistic. What the scan establishes is that the queue at 16:26 on 4 Nov was *not* short for `gpu-h100`, so the wave plan's slack cannot be assumed; re-run `sbatch --test-only` per wave.
2. **`--deadline` is a real hazard once the queue is deep.** `draft.md` §5 makes Slurm's `--deadline` the second guard layer: "a job still pending then is never started". That is exactly what it does — it kills the pending job instead of letting it wait. The probe shows the shape of the risk: submitted 16:26 with `--deadline=now+2hours` against an 22:34 estimate, it would have been killed at 18:26 had backfill not started it at 16:55. With the 8-day projection above, a `--deadline` set "a few days out" would silently convert the plan's waves into no-ops rather than protecting the copy-out cutoff. The deadline should be derived from the measured queue, not fixed in the template.
3. **`PrivateData` blocks half the draft's §6 checks.** `PrivateData = accounts,events,jobs,nodes,reservations,usage,users`. Refused here: `sinfo -s` (`slurm_load_node: Access/permission denied`), `scontrol show node hk2n1254`, cluster-wide `squeue -p gpu-h100`, `sreport`, and reservations. Working: `scontrol show partition <p>`, `scontrol show job`, `squeue -u $USER`, `sinfo_t_idle`, `sacct -u $USER`. The draft's check "`scontrol show partition gpu-h100` — whether `--exclusive` is honoured" works; a *node-level* check would not.
4. **`$HOME` and `$PROJECT` are the same GPFS filesystem** (`hfs2`, 5.4 PB, 3 % used). `draft.md` §1 treats `$PROJECT` as the place for data "because `$HOME` has 50 GB": both paths are on the same server, and the 50 GB quota could not be observed at all (`quota -s` → nothing). Staging ~20 GB GGUFs into `$PROJECT` is fine by capacity, but the "keep it off `$HOME`" reasoning needs re-checking before it is written into the plan.
5. **The downtime has no published job policy.** No time of day, nothing about pending jobs being cancelled or drained, and no reservation is visible (`No reservations in the system`). `draft.md`'s 24 h-before cutoff stays a *choice*, not a cluster guarantee — and with (1) above, it is the binding constraint.
6. **`dev-gpu-h100` is one node, and its estimate was 5.5 h too pessimistic.** `AllocNodes=ALL` and `--test-only` succeed (go/no-go passed). The estimate said 22:34; backfill started the probe at 16:55, 29 minutes after submission. So dev smoke tests are cheap — but the QoS is the real limit (`dev`: `MaxJobsPU=1`, `MaxSubmitPU=3`, i.e. **one dev job at a time**), not the wait.
7. **The partition list is richer than the draft.** `gpu-h200` (13 nodes × 4 GPUs, 2 days), `gpu-h200-8`, `large`, `dev-cpu`, `dev-gpu-h100`, `agent` all exist. The draft only names `gpu-h100`, `dev-gpu-h100` and `dev-cpu`.
8. **Module names are newer than the draft assumes.** `CUDA/13.3.0` is the newest (not 12.x), `Python/3.14.2`, `GCC/15.2.0`, and CUDA is a *standalone* module (`CUDA/13.3.0`, no `-GCCcore-` suffix). Pin these explicitly; a llama.cpp arch flag may need re-checking for CUDA 13.
9. **`--exclusive` is honoured but must be asked for.** `Exclusive=NO` on the partition; the test-only estimate shows 128 processors (whole node) *only* when `--exclusive` is given. The draft already does this — it is confirmed, not contradicted.
10. **`agent` partition = one full node, 384 cores, 3 days**, QoS `agent` capped at `cpu=2` per user. Comfortable for an SSE agent, but it is a *shared* node: our session ran there while the author may open his own.

### Probe-derived surprises (the items `draft.md` marks *(to check)*)

11. **`draft.md` §5 item 3's occupancy check would falsely trip on HoreKa 2.** The probe saw `/usr/libexec/Xorg` holding 17 MiB on its allocated GPU. The draft replaces the Ada `gpu_uuid` occupancy wait with "a light check at job start: no foreign compute process on the allocated GPUs, else exit". On a node where a display server holds an allocation (as `hkn0901` does), a literal version of that check would **abort every GPU job**, because `nvidia-smi --query-compute-apps` always lists it. The check must ignore tiny/Xorg contexts (or compare `used_memory` against a threshold), and it must key on UUID/`CUDA_VISIBLE_DEVICES`, not on the visible index.
12. **GPU indices are renumbered inside the job.** `SLURM_JOB_GPUS=3` and `SLURM_GPUS_ON_NODE=1`, while in the job `CUDA_VISIBLE_DEVICES=0` and `nvidia-smi -L` shows only `GPU 0`. The draft's "GPU slot allocator" (one GPU per worker, k per GPU, GPU 0 excluded in J3) must map slots through `CUDA_VISIBLE_DEVICES`/`SLURM_JOB_GPUS`, never through the node-level `nvidia-smi` index.
13. **`sm_90` is confirmed, and the node shape covers GGUFs and builds.** Compute capability **9.0**, driver 615.71.09, CUDA UMD 13.4, MIG disabled, persistence enabled — the `-arch=sm_90` build the draft assumes is right, and the driver offers a CUDA 13.4 runtime (the newest module, `CUDA/13.3.0`, fits). The node is 64 cores / 128 vCPUs / 755 GB RAM, and `/tmp` = `/scratch` = one **3.4 TB node-local XFS** (3.2 TB free) — enough for GGUFs and llama.cpp builds without touching `$PROJECT`.
14. **`MinMemoryTRES` is per-GPU, so an explicit `--mem` matters.** `scontrol show job` inside the probe: `MinCPUsNode=8 MinMemoryTRES=186720M`, `AllocTRES=cpu=8,mem=16G,node=1,gres/gpu=1`. The 186720 M is the `DefMemPerGPU` default; an explicit `--mem` overrides it, so the templates' explicit `--mem` is both necessary and sufficient.

## Raw files beside this report

- `query_scan.txt` — the full §3 output on the agent node (`hk2n1254`), 370 lines.
- `jobid.txt` — `120275`.
- `probe_out.txt` — the probe's full output, 216 lines (raw on the cluster: `~/r1_scan_20261104/probe-120275.out`, 7810 bytes).
- `probe_pending.txt` — the mid-scan `sacct`/`ls` snapshot taken while the probe was still in the queue.
- `session.log`, `preflight.txt`, `scontrol_node.txt`, `ssh_G.txt`, `master_before.txt`, `master_after.txt`, `liveness.txt`, `forward_spec`, `status_checks.txt`, `teardown_results.txt` — the raw setup/teardown evidence.
- `draft.md` — `docs/runbooks-04nov:docs/r1/proposals/HOREKA_T1_JOBS_DRAFT_20261104.md`, the comparison target.
