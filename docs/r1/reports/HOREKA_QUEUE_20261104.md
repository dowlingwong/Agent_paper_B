# HoreKa 2 queue-latency probe — `gpu-h100` vs `gpu-h200` (4 Nov 2026)

**Author's words (4 Nov 2026):** "批准第 1 步的排队实测" — and "11月12开始太晚了". This probe measures how long jobs of each shape actually wait, not what `--test-only` predicts.

**Status:** 10 jobs submitted **once each**, no resubmission, no additions. **All 10 were still PENDING at the end of the scan window** (last observation 2026-11-04T18:01+01:00, ≈35 min after submission). None started, so no job output exists and the GPU-model / GPU-memory / per-job process columns are **not measured**. Nothing was cancelled; the 10 jobs are left in the queue and will cancel themselves at their `--deadline` (≈2026-11-07T17:26) if they never start.

**Prompt followed:** `HOREKA_QUEUE_PROBE_PROMPT_20261104.md` (rev 1), which reuses `HOREKA_SCAN_PROMPT_20261104.md` **rev 5.6** with §3/§4 replaced by §A/§B, a new folder, and the gate-2 rule the scan established.

## 1. Setup

| Item | Value |
|---|---|
| Working folder | `~/Documents/agent_paper_B/.claude-worktrees/_snapshots/horeka_queue_20261104` (fresh; the scan folder was not written to) |
| Local tools gate (step 0.2) | `LOCAL_TOOLS_OK` after the sandbox approved `ps` (see Deviations) |
| Master connection (author's, reused, never stopped) | `Master running (pid=42629)` **before** and **after**; no configured forwards before the run |
| Session script (login-node command 1) | `start-vscode-remote-ssh.sh`, run as a **managed background task** (rev 5.6's fix, not `nohup`) |
| Session job id | **120373** (read from `session.log`, never from `squeue`) |
| Compute node | **hk2n1254** (log: "Compute node : hk2n1254") |
| sshd on the node | **port 22223** (log: "NOTE: port 22222 was in use; using 22223 instead") |
| Tunnel (login-node command 2) | `127.0.0.1:22222:hk2n1254:22223` added with `ssh -O forward`; listener PID 42629 = the master's PID |
| Gate 1 (local) | `ssh -G vscode-hk2` → `hostname 127.0.0.1`, `user ka_ir7683`, `port 22222`, no proxy → `GATE1_OK` |
| Gate 2 (§C-1 rule) | `host=hk2n1254 job_env=120373` and `squeue -p agent -t R` → `120373 hk2n1254 59:12 2026-11-04T17:24:32`. `scontrol show node` is refused on this account (`PrivateData` includes `nodes`), as in the scan; the two required signals both hold → **passed** |
| Session remaining at Gate 2 | `%L` = 59:12 |
| Teardown 5.1 | `scancel 120373` → rc 0; 20 s later `nodessh true` → `Connection reset by peer` (rc 255, expected) |
| Teardown 5.2 | `-O cancel` → `NO_LISTENER`; master still `Master running (pid=42629)` |
| Teardown 5.3 | `CLIENT_GONE`, `NO_CLIENT_PROCESS`; the managed background session job also exited 0 |

## 2. Partition facts (`gpu-h200`, `gpu-h200-8`)

`scontrol show partition gpu-h200` (verbatim excerpt):

```
PartitionName=gpu-h200
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=NO QoS=N/A
   MaxNodes=13 MaxTime=2-00:00:00 MinNodes=1 LLN=NO MaxCPUsPerNode=192 MaxCPUsPerSocket=UNLIMITED
   Nodes=hkn[1951-1963]
   OverSubscribe=NO PreemptMode=OFF State=UP TotalCPUs=2496 TotalNodes=13
   JobDefaults=DefCpuPerGPU=48,DefMemPerGPU=186720
   TRES=cpu=2496,mem=9709440M,node=13,billing=2496,gres/gpu=52
```

`scontrol show partition gpu-h200-8` (verbatim excerpt):

```
PartitionName=gpu-h200-8
   AllowGroups=ALL AllowAccounts=ALL AllowQos=ALL
   AllocNodes=ALL Default=NO QoS=N/A
   MaxNodes=1 MaxTime=2-00:00:00 MinNodes=1 LLN=NO MaxCPUsPerNode=192 MaxCPUsPerSocket=UNLIMITED
   Nodes=hkn1970
   OverSubscribe=NO PreemptMode=OFF State=UP TotalCPUs=192 TotalNodes=1
   JobDefaults=DefCpuPerGPU=12,DefMemPerGPU=254300
   TRES=cpu=192,mem=2034400M,node=1,billing=192,gres/gpu=8
```

| | `gpu-h200` | `gpu-h200-8` |
|---|---|---|
| Nodes | `hkn[1951-1963]` — 13 nodes | `hkn1970` — 1 node |
| GPUs per node | **4** (`gres/gpu=52` / 13 nodes) | **8** (`gres/gpu=8` / 1 node) |
| CPUs per node | 192 | 192 |
| GPU memory **shown by `scontrol`** | not a GPU property; the Slurm default is `DefMemPerGPU=186720` (≈182 GiB per GPU) | `DefMemPerGPU=254300` (≈248 GiB per GPU) |
| MaxTime | **2 days** (`2-00:00:00`) | **2 days** |
| AllowAccounts / AllowGroups / AllowQos | `ALL` / `ALL` / `ALL` | `ALL` / `ALL` / `ALL` |
| QoS | `N/A` | `N/A` |
| OverSubscribe / Exclusive | `NO` / `NO` | `NO` / `NO` |

`sinfo_t_idle` at probe time shows **0 idle nodes in every GPU partition**:

```
Partition dev-gpu-h100            :      0 nodes n/a
Partition gpu-h100                :      0 nodes n/a
Partition gpu-h200                :      0 nodes n/a
Partition gpu-h200-8              :      0 nodes n/a
Partition cpu                     :      1 nodes drain / 1 nodes plnd
Partition large                   :      2 nodes idle
```

**`gpu-h200` is not refused for this account** — all five `gpu-h200` `--test-only` shapes were accepted, so all 10 jobs were submitted. `DefMemPerGPU=254300` on `gpu-h200-8` is the only number in this scan that suggests a larger per-GPU memory class than the `gpu-h200` nodes; it is a **Slurm default**, not a measured GPU size.

## 3. The 10 jobs

`--test-only` estimates (all 10 accepted, `testonly.txt`), submitted at **2026-11-04T17:26:00** (all ten `sacct` `Submit` values are identical), and still pending at the last observation.

| Job name | `--test-only` estimate | Submit | Start | Wait at last check | Node | GPU (from job output) |
|---|---|---|---|---|---|---|
| `r1q_h100_g1_1h` | 2026-11-12T00:26:35 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h100_g1_4h` | 2026-11-12T00:26:35 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h100_g1_12h` | 2026-11-12T00:26:35 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h100_x4_4h` | 2026-11-12T03:10:23 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h100_x4_12h` | 2026-11-12T03:10:23 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h200_g1_1h` | 2026-11-19T10:24:47 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h200_g1_4h` | 2026-11-19T10:24:47 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h200_g1_12h` | 2026-11-19T10:24:47 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h200_x4_4h` | 2026-11-19T10:24:47 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |
| `r1q_h200_x4_12h` | 2026-11-19T10:24:47 | 2026-11-04T17:26:00 | **pending at 2026-11-04T18:01** | ≥ 35 min | none | not measured |

Job ids in order: **120384–120393** (all `PENDING`, `Start=Unknown`, `NodeList=None assigned`, from `sacct -X`, `sacct.txt`).

**The scheduler's live `%S` start estimate is not stable, and it disagrees with `--test-only`.** Seven `squeue` checks at 5-minute intervals (`status_checks.txt`) gave, for the same jobs over 30 minutes:

| Job | `%S` at 17:31 | `%S` at 18:01 | `--test-only` |
|---|---|---|---|
| `r1q_h100_g1_1h` | 2026-11-09T06:40 (Priority) | **2026-11-05T10:40** (Priority) | 2026-11-12T00:26 |
| `r1q_h100_g1_4h` | N/A (Priority) | 2026-11-11T00:40 (Priority) | 2026-11-12T00:26 |
| `r1q_h100_x4_4h` | N/A (Resources) | 2026-11-11T00:50 (Resources) | 2026-11-12T03:10 |
| `r1q_h200_g1_1h` | 2026-11-06T00:40 (Priority) | 2026-11-06T00:40 (Priority) | 2026-11-19T10:24 |
| `r1q_h200_x4_4h` | 2026-11-06T01:40 (Priority) | 2026-11-06T01:40 (Priority) | 2026-11-19T10:24 |
| `r1q_h100_x4_12h`, `r1q_h100_g1_12h`, `r1q_h200_g1_12h`, `r1q_h200_x4_12h` | N/A | N/A | as above |

So: `gpu-h200`'s `--test-only` estimate (11-19) was **13 days later** than the live `%S` the same day (11-06), and `gpu-h100`'s single-shot estimate moved by up to **4 days** within 30 minutes of observation. Neither number is a wait measurement, which is why this probe measures the wait directly.

## 4. Processes on the GPU

**Not measured.** No job ever reached `RUNNING`, so the `nvidia-smi --query-compute-apps` line in `q.sh` never ran and no output file exists (`job_outputs.txt` contains only the shell's `No such file or directory` for the glob). Consequently the GPU model, GPU memory, and any per-job foreign process (Xorg or otherwise) of `gpu-h200` / `gpu-h100` nodes are **not measured by this probe** — the scan's `hkn0901` result (H100, 95 830 MiB, `/usr/libexec/Xorg` 17 MiB) still stands for `dev-gpu-h100` only.

## 5. What to read later

One line, from the Mac:

```
ssh hk2 "sacct -X -u ka_ir7683 -S 2026-11-04 -n -P -o JobName,JobID,Partition,State,Submit,Start,End | grep r1q_"
```

Expected outcomes: jobs that started show a `Start` and an `End` a couple of seconds later (their `q.sh` output is in `~/r1_queue_20261104/<name>-<id>.out`); jobs that never start will be cancelled by `--deadline` at ≈**2026-11-07T17:26** and show `CANCELLED`. Reading the file directly is also possible:

```
ssh hk2 "ls -l ~/r1_queue_20261104/; cat ~/r1_queue_20261104/*.out"
```

## 6. Deviations from this prompt

1. **`ps` needed a sandbox approval (twice: step 0.2 and teardown 5.3).** The local sandbox refused `ps` (`Operation not permitted`); I requested the exact runbook command, and it was approved. No HoreKa call was made before the step-0 approval.
2. **The test-only call ended with one extra `squeue -u $USER`.** I added a final `=== my jobs now ===` line to the test-only script, run before submission. It is one squeue call outside the 5-minute cadence (it showed only the session job, since the 10 jobs did not exist yet). Disclosed for the check-count bookkeeping: **7 probe status checks** (cap 9) **+ 1 extra squeue**, i.e. 8 squeue calls in total.
3. **`q.sh` was written on the node from a heredoc in the same call, not byte-transferred from `$S/q.sh`.** The content is the prompt's script verbatim, and the local canonical copy is `$S/q.sh`; a byte-level comparison was not possible after the session ended. Everything else (`create ~/r1_queue_20261104/`, `jobs.txt`, submissions) matches §A3.
4. **No STOP condition was hit.** No policy message; the longest-lived job never ran at all (so the ">60 s" rule could not trigger); `squeue` never showed more than **11** lines (10 probe jobs + the session job).

## Raw files beside this report

- `partitions.txt` — `scontrol show partition gpu-h200`, `gpu-h200-8`, `sinfo_t_idle`.
- `testonly.txt` — the 10 `sbatch --test-only` estimates (job ids 120374–120383 are estimates, not real jobs).
- `jobs.txt` — `name jobid`, 120384–120393.
- `status_checks.txt` — the 7 timed `squeue` checks.
- `sacct.txt`, `job_outputs.txt`, `final_record.txt` — the final record at 18:01 (all pending, no outputs).
- `session.log`, `liveness.txt`, `preflight.txt`, `ssh_G.txt`, `master_before.txt`, `master_after.txt`, `forward_spec`, `tunnel.log`, `teardown_results.txt` — setup and teardown evidence.
- `q.sh`, `testonly.sh`, `submit.sh`, `poll.sh`, `teardown.sh` — the scripts used.
- `draft.md` — the design draft (unchanged from the scan).
