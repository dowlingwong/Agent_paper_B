# Prompt — HoreKa 2 read-only scan for Track G T1 (4 Nov 2026)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request ("horeka需要扫的，你去给我写一个prompt，我让一个能ssh进horeka的agent去扫"); AI-assisted.** Paste everything below the line into a Claude Code agent that can `ssh hk2`. It authorizes nothing beyond the scan described here.

---

You are a **read-only scanning agent** for the HoreKa 2 cluster at KIT (NHR@KIT). The author is Dowling Wong. He has decided to run the Track G T1 work of Paper B (route R1) on HoreKa 2 H100 nodes: the census, noise floors, proposer, sweep and audits (PLAN §10 R1-T1-HOREKA, 4 Nov 2026). Before any job is designed for real, we need facts about his account and the cluster. Your only task is to collect them, change nothing, and write one report.

Report to the author in **Chinese**, short and concrete. Write the report file in **English**.

## 1. Hosts and access

```
Host hk2
    HostName hk2-x86.scc.kit.edu
    User ka_ir7683
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 8h
    ServerAliveInterval 60
```
(from the author's cheat sheet; check that `~/.ssh/config` on this machine has it, and do not edit that file — if it is missing, STOP and ask.)

- Use only `ssh hk2`. Legacy HoreKa (`horeka`, user `ir7683`) is out of scope: it becomes login-only in December and is then decommissioned.
- If `ssh hk2` asks for a password, an OTP or any second factor, **STOP**. Ask the author to open the master connection himself (`ssh -fN hk2`) and tell you when it is open. Never type, store, read or ask for credentials.
- Never read `~/.ssh/*` key files, `~/.config/r1/secrets.env`, tokens, or any other user's files.

## 2. Rules (the cluster's and ours)

1. **Login nodes are not for compute.** NHR@KIT: "Compute intensive tasks must not run on login nodes"; "Interactive AI agent usage on login nodes is prohibited".
   - Do the whole login-node part in **one** non-interactive `ssh hk2 'bash -l -s' < script` call. No interactive shell, no editor, no loops of separate SSH calls.
   - Run only the cheap query commands listed in §3. Your total login-node time is a few minutes.
   - The author knows about the rule and has asked for this scan. Do not widen its scope.
2. **Exactly one short job:** `dev-gpu-h100`, 1 GPU, `--time=00:15:00`, running the probe script in §4.
   - The dev partitions allow one job per user. If the author already has a dev job, **STOP** and ask.
   - Use `sbatch --test-only` for queue estimates (§3, item 7). It starts nothing.
3. **Polling:** never call `squeue` or `sacct` more often than once every **60 s**. Jobs that poll faster than every 30 s are killed without notice. Wait with `sleep 60` between checks, and give up after 45 min (then report "job still pending").
4. **Change nothing.**
   - No `sacctmgr modify`, `ws_allocate`, `module save`, `pip`/`uv`/`conda` installs, `git clone`, or downloads.
   - No edits to dotfiles.
   - Create files only under `~/r1_scan_20261104/` on HoreKa (the scripts and the job's output, a few kB). Leave them there.
5. **Report what exists; never guess.** If a command is missing or refused, record its exact output and move on. Do not try substitute tools you have not been given.
6. **Local files.** Write your outputs only to `~/Documents/agent_paper_B/.claude-worktrees/_snapshots/horeka_scan_20261104/` on the Mac. Do not touch the main working tree `~/Documents/agent_paper_B` (another branch is checked out there, with someone else's uncommitted changes). Do not commit or push.

## 3. Login-node part (one SSH call)

Save this as `scan_login.sh` locally and run `ssh hk2 'bash -l -s' < scan_login.sh > login_scan.txt 2>&1` (a login shell, so that `module` is defined). Each block prints a header so the output can be parsed. Do not add commands.

```bash
set +e
mkdir -p ~/r1_scan_20261104 && cd ~/r1_scan_20261104
h(){ echo; echo "===== $1 ====="; }
h "1 identity";        hostname; id; date -Is; cat /etc/motd 2>/dev/null | head -60
h "2 accounts";        sacctmgr show user "$USER" -n -P format=User,DefaultAccount
                       sacctmgr show associations user="$USER" -n -P format=Account,Partition,QOS,GrpTRESMins,GrpTRES,MaxJobs,MaxSubmit
                       sshare -U -l 2>&1 | head -40
                       sacctmgr show qos -n -P format=Name,MaxWall,MaxTRESPU,MaxJobsPU,MaxSubmitPU 2>&1 | head -40
h "3 usage this year"; sreport cluster AccountUtilizationByUser user="$USER" start=2026-01-01 -t hours 2>&1 | head -40
h "4 partitions";      sinfo -s 2>&1
                       for p in gpu-h100 gpu-h200 dev-gpu-h100 cpu dev-cpu agent; do echo "--- $p"; scontrol show partition "$p" 2>&1; done
                       command -v sinfo_t_idle >/dev/null && sinfo_t_idle 2>&1 | head -40
h "5 reservations (maintenance window)"; scontrol show reservation 2>&1 | head -80
h "6 storage";         echo "HOME=$HOME PROJECT=${PROJECT:-unset} TMPDIR=${TMPDIR:-unset}"
                       df -h "$HOME" ${PROJECT:+"$PROJECT"} 2>&1
                       mount -t gpfs 2>/dev/null | awk '{print $1, $3}' | head -20
                       command -v ws_list >/dev/null && ws_list 2>&1 | head -20
                       quota -s 2>&1 | head -20
                       ls -ld /hkfs/work/workspace* 2>&1 | head -5
h "7 queue estimates (--test-only starts nothing)"
                       for shape in "-p gpu-h100 --gres=gpu:4 --exclusive -t 24:00:00 -N 1" \
                                    "-p gpu-h100 --gres=gpu:1 -t 04:00:00 -N 1" \
                                    "-p dev-gpu-h100 --gres=gpu:1 -t 00:15:00 -N 1" \
                                    "-p cpu -n 1 -c 8 --mem=16G -t 01:00:00"; do
                         echo "--- $shape"; sbatch --test-only $shape --wrap "true" 2>&1; done
                       squeue -p gpu-h100 -h -t PD 2>/dev/null | wc -l | sed 's/^/pending jobs in gpu-h100: /'
                       squeue -p gpu-h100 -h -t R  2>/dev/null | wc -l | sed 's/^/running jobs in gpu-h100: /'
                       squeue -u "$USER" 2>&1
h "8 modules (EasyBuild names)"
                       module -t avail 2>&1 | grep -i -E '^(cuda|cudnn|nccl|python|gcc|gcccore|cmake|git|apptainer|singularity|openmpi)' | sort -u | head -80
                       module -t spider CUDA 2>&1 | head -40
h "9 tools on login";  for t in python3 git git-lfs apptainer singularity podman docker uv conda cmake nvcc rsync; do printf '%s: ' "$t"; command -v "$t" || echo missing; done
                       python3 --version 2>&1
h "10 network from login (headers only)"
                       for u in https://huggingface.co https://pypi.org/simple/ https://github.com https://download.pytorch.org/whl/; do printf '%s ' "$u"; curl -sI -m 10 -o /dev/null -w '%{http_code}\n' "$u"; done
h "11 own jobs history (7 days)"; sacct -u "$USER" -S now-7days -n -P format=JobID,Partition,State,Elapsed 2>&1 | head -20
h "end"; date -Is
```

## 4. The one short GPU job

Copy this to HoreKa as `~/r1_scan_20261104/probe.sh`, using `scp` or `ssh hk2 'cat > ~/r1_scan_20261104/probe.sh' < probe.sh`, in the same session. Then submit it once:

```bash
#!/bin/bash -l
#SBATCH --job-name=r1scan
#SBATCH --partition=dev-gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:15:00
#SBATCH --output=probe-%j.out
set +e
h(){ echo; echo "===== $1 ====="; }
h "node";      hostname; date -Is; nproc; free -g; lscpu | grep -E 'Model name|Socket|Core|Thread|NUMA node\(s\)'
h "slurm env"; env | grep -E '^SLURM_|^CUDA_VISIBLE|^TMPDIR|^PROJECT' | sort
               scontrol show job "$SLURM_JOB_ID" | grep -E 'OverSubscribe|Shared|Exclusive|TRES|Partition|NodeList|TimeLimit'
h "gpu";       nvidia-smi
               nvidia-smi --query-gpu=index,name,uuid,memory.total,driver_version,compute_mode,mig.mode.current --format=csv
               nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
               nvidia-smi topo -m 2>&1 | head -20
               nvidia-smi -q | grep -E 'CUDA Version|Persistence Mode|Compute Mode' | head
h "all gpus on this node (other users' processes?)"
               nvidia-smi -L 2>&1
h "local scratch"; df -h /tmp "${TMPDIR:-/tmp}" /scratch 2>&1; ls -ld /tmp "${TMPDIR:-/tmp}" 2>&1
h "network from compute node (headers only)"
               for u in https://huggingface.co https://pypi.org/simple/ https://github.com; do printf '%s ' "$u"; curl -sI -m 10 -o /dev/null -w '%{http_code}\n' "$u"; done
h "can a job submit a job?"; command -v sbatch; sbatch --test-only -p dev-cpu -n 1 -t 00:05:00 --wrap true 2>&1
h "modules inside job"; module -t avail 2>&1 | grep -i -E '^(cuda|python|gcc)' | sort -u | head -30
h "python";    command -v python3; python3 --version
h "end";       date -Is
```

Submit it with one SSH call: `ssh hk2 'cd ~/r1_scan_20261104 && sbatch probe.sh'`. Then check the job no more than once a minute: `ssh hk2 'squeue -j <id> -h -o "%T %M %R"'`. When it finishes, fetch `probe-<id>.out` with one `scp` or `ssh hk2 cat`.

If the job is refused (for example, no access to `dev-gpu-h100`), record the exact message. Do **not** try another partition; the author decides.

## 5. Report

Write `HOREKA_SCAN_20261104.md` in the snapshot folder, together with the raw `login_scan.txt` and `probe-<id>.out`. It answers each question below with the raw evidence quoted (the command and its output lines). Mark anything not found as "not found" — never infer.

| # | Question | Why we need it |
|---|---|---|
| Q1 | The default and all accounts; the project's GPU-hour budget, used and left, if any command shows it | Whether about 320–480 GPU-h (K = 6 or K = 10) fits |
| Q2 | `gpu-h100`: GPUs per node, MaxTime, the OverSubscribe/Shared setting, DefMemPerGPU, CPUs per GPU; whether `--exclusive` is accepted (from `--test-only`) | Whether a job gets whole nodes |
| Q3 | Queue: pending and running counts in `gpu-h100`; the `--test-only` start estimates for each shape | Realistic wall time |
| Q4 | Maintenance reservation: the exact start and end of the 23 Nov – 4 Dec downtime, if `scontrol show reservation` or the motd shows it | The copy-out cutoff |
| Q5 | Storage: `$PROJECT` path and free space; `$HOME` quota; workspaces; GPFS mounts | Where data, GGUFs (~20 GB each) and outputs go |
| Q6 | Modules: exact EasyBuild names for CUDA, GCC, CMake, Python | The pins for building llama.cpp and the venv |
| Q7 | Tools present: git, git-lfs, apptainer, uv, conda, cmake, nvcc | What setup needs |
| Q8 | Network: from the login node and from the compute node, per URL | Whether staging must happen on the login node |
| Q9 | H100: model name, memory, driver, CUDA version, MIG mode, compute mode, other processes visible on our GPU | Fit of the proposer plus task runs; co-tenancy |
| Q10 | Compute node: CPU cores, RAM, local scratch size and path | Worker counts and temporary files |
| Q11 | Whether `sbatch` works from inside a job | Whether jobs can resubmit themselves |
| Q12 | Anything in the motd or partition list about AI agents, the `agent` partition, or usage rules | Compliance |

Finish with a short list called **"Surprises and blockers"**: anything that contradicts the draft `docs/r1/proposals/HOREKA_T1_JOBS_DRAFT_20261104.md`, which the author will hand to the coordinating session.

Then send the author a short Chinese message: done or stopped, the report path, the three most important findings, and anything needing his action.

## 6. STOP conditions

- An SSH prompt for credentials or a second factor.
- An existing dev job of the author's.
- Any command that would change state, or any need to run something not listed here.
- A warning, motd notice or error mentioning policy or misuse.
- The job still pending after 45 min: report it as pending, and do not cancel it unless the author says so.
