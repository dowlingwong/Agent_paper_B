# Paper B (route R1) — HoreKa agent runbook: the T1 tier on HoreKa 2 (4 Nov 2026, revision 1)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request ("写 HoreKa 执行 runbook", 17:12); AI-assisted.**

**Sources:**
- the scan report `docs/r1/reports/HOREKA_SCAN_20261104.md` (attempt 4, raw output under `reports/horeka_scan_20261104/`);
- the draft `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (rev 2), which this runbook replaces for execution;
- `prompts/TRACK_G_RUNBOOK.md` (what the T1 steps G.0–G.6 measure);
- PLAN §10 R1-T1-HOREKA (13:45) and R1-SERVER-AGENTS-TWO (14:58).

**The author's words at 17:12, after the scan:**
- "批准第 1 步的排队实测" (the queue probe, `prompts/HOREKA_QUEUE_PROBE_PROMPT_20261104.md`);
- "400GPU小时没问题" (400 GPU-hours are fine);
- "11月12开始太晚了" (12 November is too late to start).

**This runbook authorizes nothing by itself.** It holds only once the author has committed the PLAN row in §8. ENGINEERING_ONLY work needs that row. EVIDENCE work (the T1 part of sweep 2, its audits, the closed loop) also needs the author's committed authorization note.

**Who you are.** You are the **HoreKa agent** (Claude Code), started by the author on his Mac. You act only on **HoreKa 2** (R1-SERVER-AGENTS-TWO). The operator acts on TASL-2, TASL-7, deepthought and Ada, and you never act there. The Mac-local agent writes the shared code (task M10) and integrates the documents on `mac-int-20261104`.

**Authority, in order.** If two of these conflict, STOP and ask.
1. `docs/r1/PLAN.md` §10 on `mac-int-20261104`, at the commit the author gives you.
2. `docs/r1/RUNBOOK.md` (Track G) and `prompts/TRACK_G_RUNBOOK.md`.
3. `docs/r1/STATUS.md`.
4. This file.

Report to the author in **Chinese**, short and concrete. Write reports, reviews and commit messages in **English**.

---

## 0. Ground rules

### 0.1 HoreKa 2 as the scan measured it (4 Nov)

| Item | Value | Consequence |
|---|---|---|
| Account | `hk-project-p0027888`, the only one; no GPU limit on the association; fair-share factor 0.79 | Every job sets `-A hk-project-p0027888`. The budget is the author's 400 GPU-h (§0.4), not a Slurm limit |
| `PrivateData` | `accounts,events,jobs,nodes,reservations,usage,users` | `sinfo -s`, `scontrol show node`, cluster-wide `squeue`, `sreport` and reservations are refused. Use `squeue -u $USER`, `sacct -u $USER`, `scontrol show partition`, `scontrol show job`, `sinfo_t_idle` |
| `gpu-h100` | 21 nodes × 4 H100 (95,830 MiB each), 128 CPUs and 755 GB per node; MaxTime 2 days; `OverSubscribe=NO`; `--exclusive` honoured when asked | — |
| `gpu-h200` | 13 nodes × 4 GPUs, 192 CPUs per node; MaxTime 2 days; open to all accounts | Not yet measured for waiting time (queue probe) |
| `dev-gpu-h100` | 1 node, 4 GPUs, MaxTime 1 h; QoS `dev`: **one job at a time per user**, 3 submitted | Setup and smoke tests only |
| Queue | `--test-only` estimates: 4 GPUs × 24 h exclusive → 12 Nov; 1 GPU × 4 h → 12 Nov. A 15-min dev job estimated at +6 h started after 29 min (backfill) | **Short, small jobs.** The queue probe decides how short (H0) |
| Inside a job | `SLURM_JOB_GPUS=3` appears as `CUDA_VISIBLE_DEVICES=0`; `/usr/libexec/Xorg` holds 17 MiB on the GPU; compute capability 9.0 (`sm_90`), driver 615.71.09, MIG off | GPUs are mapped through `CUDA_VISIBLE_DEVICES` and UUIDs, never node indices. The occupancy check must ignore Xorg (§3) |
| Storage | `$HOME` and `$PROJECT=/hfs2/data/project/hk-project-p0027888/ka_ir7683` on the same GPFS (5.4 PB, 3 % used); quota not measurable; node-local `/scratch` = `/tmp`, 3.4 TB XFS per node | Code, venv, GGUFs and results under `$PROJECT`; per-run working copies under the job's `/scratch` |
| Network | `huggingface.co`, `pypi.org`, `github.com` reachable from the `agent` node and from GPU nodes, without a proxy | Downloads happen inside jobs, never on a login node |
| Modules | `CUDA/12.6.0 … 13.3.0`, `GCC/12.3.0 … 16.2.0`, `CMake/… 4.2.1-GCCcore-15.2.0`, `Python/3.11.3 … 3.14.2`; tools: git, git-lfs, apptainer, rsync; no `uv`, `conda`, `cmake` or `nvcc` without modules | The exact modules are pinned in H1 and recorded in every job's provenance |
| Downtime | **23 Nov – 4 Dec 2026** (MOTD and docs), no time of day, no published policy for pending jobs; no reservation visible | §0.5 |
| Self-submission | `sbatch` works inside a job (tested with `--test-only`) | A job may submit its own continuation (§1) |

### 0.2 How you act on HoreKa

- **Never on a login node.** NHR@KIT: "Interactive AI agent usage on login nodes is prohibited… Use the SSH tunnel to compute nodes". Every command of yours runs on the `agent`-partition compute node, reached through the tunnel.
- **Opening and closing a session.** Use the procedure of `prompts/HOREKA_SCAN_PROMPT_20261104.md` revision 5.6, §1 steps 0–5. That covers the wrappers, the author's open master connection, the session script, the forward, both gates and the ordered teardown.
  - Use your own session folder for each session: `…/_snapshots/hk2_session_<UTC date-time>/`.
  - Gate 2 passes as the scan passed it: `SLURM_JOB_ID` equals the session job id, and `squeue -u $USER -p agent -t R` shows that job running on the host. `scontrol show node` is refused on this account.
  - The login node runs exactly two things for you: the session script, and the forward on the author's master connection.
- **Session length.** The session script asked Slurm for `--time=01:00:00`; the `agent` partition allows 3 days. *(to check in H0)* Whether the script accepts a longer time. Read it on the compute node (`command -v start-vscode-remote-ssh.sh`, then read the file); never run anything extra on the login node for this.
  - Batch jobs keep running after a session ends. You need a session only to submit, check, and copy.
  - Never leave a session open longer than its work needs.
- **The author does three things for you:**
  - opens the master connection (`ssh -fN hk2`) when you ask;
  - completes any one-time key setup;
  - answers the STOPs.
- **A third wrapper, `nodessh-raw`.** `git` and `rsync` put the host name into the command themselves, so they need the node wrapper without its fixed host argument. Create it in each session folder next to the other two:
  ```bash
  cat > "$S/nodessh-raw" <<'W'
  #!/bin/bash
  S="<this session folder>"
  KH="$S/known_hosts_$(cat "$S/session_tag" 2>/dev/null || echo none)"
  exec ssh -F "$S/vscode_ssh_config" -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=4 \
    -o IdentitiesOnly=yes -o UserKnownHostsFile="$KH" -o StrictHostKeyChecking=accept-new "$@"
  W
  chmod 700 "$S/nodessh-raw"
  ```
  Use it only with the host `vscode-hk2`, and only after Gate 2 has passed.
- **Code transfer.** There are no GitHub credentials on HoreKa, as for the portal (R1-EXAM-TRANSFER).
  - From the Mac, `GIT_SSH_COMMAND="$S/nodessh-raw" git push vscode-hk2:<path under $PROJECT>/r1/git/<repo>.git <commit>:refs/heads/<branch>`, into bare repositories under `$PROJECT/r1/git/`.
  - Check out **detached** at the pinned commits into `$PROJECT/r1/work/<repo>@<short sha>/`.
  - Never `git clone` from GitHub with credentials on HoreKa.
- **Copy-back.** `rsync -a -e "$S/nodessh-raw" vscode-hk2:<$PROJECT path>/r1/results/ <Mac worktree>/results/r1/trackg/hk2/`, through the tunnel. Commit JSON, manifests and `.jsonl` up to 20 MB; gzip larger files and list them in `SHA256SUMS`.

### 0.3 Rules carried over unchanged

- **Never touch what you did not start.** Never cancel, signal or edit another user's job or file, or a job of the author's own. You cancel only your own job ids, recorded at submission. A standing recovery authorization exists only if the author writes one to you, with a scope.
- **Pins.** Every job runs the commits and artefacts of the RUNBOOK §5 pin table: paper and harness commits, the llama.cpp build, GGUF sha256 values and configs. A mismatch is a STOP.
- **Run labels.** ENGINEERING_ONLY (census, ports, smoke, qualification, pilot) needs the PLAN row of §8. EVIDENCE (sweep 2 T1, its audits, the closed loop) also needs the author's committed note.
- **Seeds.**
  - 7006–7010 are evaluation seeds only.
  - Exam seeds (9001+, 9101+, 9201+) never enter a C3 sweep.
  - Noise floors use 8001–8010 (R1-BX-PROPOSED-CONFIRM).
  - Audits use K = 10 until an author row puts R1-BX-D3's K = 6 into force.
- **One GPU model per label table** (R1-BX-D5). The σ̂ of a node comes from a floor measured on the same GPU model, with the same runs-per-GPU k and the same placement as its labels. Changing k, the placement or the GPU model means re-measuring the floor.
- **Fixed step budgets, never wall-clock.** A divergence is its own outcome and is never re-run to hide it.
- **Analysis gate (R1-BX-D8).** No sweep-2 T1 label table is copied back for analysis before the author's R1-BX-D8-CONFIRM row exists. Copy-back for safety (§0.5) goes to a sealed folder that analysis code does not read.
- **Secrets.** Never read `~/.config/r1/secrets.env` or any key file. Since 4 Nov (packet (j), the author's "用 exam 第二名") the second proposer is a local model, so no API calls run on HoreKa.
- **Review loop at every STOP.**
  1. Spawn a **fresh** reviewer. Give it the phase goal, this runbook, the pins and the outputs, but not your conclusions.
  2. The reviewer writes `docs/r1/reviews/HK2_<PHASE>_REVIEW_<date>.md`.
  3. Fix or answer each finding, and re-check with the same reviewer until it writes **accepted**.

  You never accept your own phase.
- **Branches.**
  - Reports go on `hk2-ops-20261104`, made from `mac-int-20261104` in your own worktree. Never use the Mac's main working tree.
  - Ports go on `hk2-trackg-20261104` in the harness repository, from the Mac agent's M10 step-0 commit.
  - Never push `main`, `r1` or `exam-x-*`, and never force-push. Commit author: `Dowling Wong <wangdowling@gmail.com>`, with the attribution lines the author gives you.
- **Reports.** After every STOP:
  1. Write `docs/r1/reports/HK2_<PHASE>_<date>.md`.
  2. Add a STATUS entry.
  3. Send the author a short Chinese message: what is done, commits, checks, the review verdict, the decisions needed.
- **Deletions.** Never delete evidence. To retire anything, move it into a `_to_delete/` folder next to it and tell the author.

### 0.4 GPU-hour budget

- The author's budget: **400 GPU-h** ("400GPU小时没问题", 4 Nov 17:12).
- **Ledger.** Keep `results/r1/trackg/hk2/gpu_ledger.csv`, with one row per job: job id, name, phase, partition, GPUs, elapsed time and GPU-hours. GPU-hours are elapsed time × GPUs allocated; an exclusive 4-GPU job counts all 4 GPUs. Fill it from `sacct` after each job ends.
- **STOP at 300 GPU-h used** *(proposed)*, with the projection for the remaining work, so the author can decide before the budget runs out.
- **K and the budget.** The draft's estimate is about 320 GPU-h at K = 6 and about 480 at K = 10, for about 8 T1 nodes. At K = 10, 400 GPU-h does not cover all of them. Report this projection after the census (H3); it does not change K. K is an author row (R1-BX-D3).

### 0.5 The downtime

- **Cutoff:** 22 Nov 2026, 00:00 CET *(proposed: 24 h before the earliest possible start, since no time of day is published)*. At the cutoff no job of yours is running or pending, and every result is copied to the Mac.
- **Guards** (code: §3):
  - at submission, refuse a job if now + `--time` passes the cutoff;
  - every job sets `--deadline=<cutoff>`, and never anything earlier. Slurm then never starts a job that cannot finish by the cutoff. The scan's warning applies to an earlier deadline, which would cancel pending jobs that could still have run;
  - the runner inside each job checks the clock and stops cleanly at a unit boundary (§1) before the cutoff.
- **21 Nov:** submit nothing new after 12:00 CET *(proposed)*. Copy everything back and verify it by `SHA256SUMS`. Report.
- **After the downtime (from 5 Dec, expected):** before anything else, run a census of your own state: `squeue -u`, `sacct -u` since 21 Nov, the `$PROJECT` tree and checksums. Resume nothing automatically. Report it, and wait for the author.

## 1. Job design

**Principle: short, small, resumable jobs.** The scan shows a deep `gpu-h100` queue for long and wide jobs, and backfill admits short ones quickly. The author says 12 Nov is too late. So the unit of work is a **1-GPU job of at most T_max hours**, where T_max is chosen in H0 from the queue probe *(proposed default: 4 h)*. Whole-node exclusive jobs are used only where a measurement needs them.

**Why 1-GPU jobs keep the labels valid.**
- `OverSubscribe=NO` means no other job shares our GPU.
- Other users' jobs on the same node share CPU, memory bandwidth and I/O. Because label runs use **fixed step budgets** (R1-BX-D5), this changes only throughput, never the metric.
- The census measures the metric noise in this same layout, so σ̂ already includes anything the layout adds.
- Throughput and latency are recorded with a GPU census of each job and reported as descriptive (R1-COMPUTE, 13 Oct).

**Units and resumption.**
- The runner writes each unit's results only when the unit is complete. A unit cut off by the time limit or the cutoff is discarded and re-run whole in the next job.
- A job that ends with work left may submit its continuation (`sbatch` works inside jobs), through the submit tool's guards. Each continuation counts against the 90-job limit and the ledger.

| Job | Partition and resources *(proposed)* | What it runs | Unit |
|---|---|---|---|
| **J0 setup** | `cpu`, 16 cores, ≤ 2 h; then `dev-gpu-h100` ≤ 1 h for a GPU check | venv under `$PROJECT` from pinned wheels; llama.cpp at the pinned commit built for `sm_90` with the pinned modules; staged datasets and GGUFs downloaded inside the job; sha256 against the staging manifest; version records | re-runnable |
| **J1 smoke** | `dev-gpu-h100`, 1 GPU, ≤ 1 h (one at a time) | one fixed-step run per ported node with a stub manager; the frozen-path refusal; a llama-server load probe of a model the author names | — |
| **J1b proposer qualification** | 1 GPU, ≤ T_max | O5-style: full offload, 50 prompts × 3 at `cache_prompt: false`, within-server identity, latency, a projection. **The pass criterion is committed by the author before it runs** | — |
| **J2 census** (G.0 raw cost, G.1b determinism and floors) | 1 GPU, ≤ T_max, several jobs per node | the declared representative edits plus the baseline × seeds 8001–8010; a concurrency sweep with k = 1, 2, 4 runs on the job's GPU | one (edit, seed) run |
| **J3 campaigns** (G.4 pilot, G.5 sweep 2 T1) | 1 GPU, ≤ T_max | llama-server for the main proposer (thinking off, `cache_prompt: false`, bound to 127.0.0.1, port from `SLURM_JOB_ID`) **on the same GPU** as the campaign's task runs *(proposed: H100 memory allows it; the pilot checks the fit)* | one campaign root; an interrupted root is re-run whole |
| **J4 audits** | 1 GPU, ≤ T_max; the audit plan split into shards | candidate–incumbent pairs on the K seeds, k runs per GPU | one pair: written only when all its runs are done |
| **J5 merge** | `cpu`, ≤ 1 h | merges shards, refuses duplicates or missing pairs; builds the T1 label table **from label seeds only**; evaluation seeds go only into the evaluation columns | — |

**Every template sets** `-A`, `-p`, `--time`, `-N 1`, `-n 1`, `-c`, `--mem` (explicitly; the default is 186,720 MB per GPU) and `--deadline=<cutoff>`. J0 and J5 request no GPU.

**GPU model.** One model for the whole T1 table: H100 per R1-T1-HOREKA. *(open)* H200 instead, if the queue probe shows much shorter waits there. That needs an author row amending R1-T1-HOREKA, and every floor and label is then measured on H200.

## 2. Phases

Each phase lists what it needs, its steps, and when it is done. Durations are estimates.

### H0 — Queue facts and the job shape (ENGINEERING_ONLY; ½ day)

**Needs:** the queue probe report `HOREKA_QUEUE_20261104.md` (run by the scan agent), and the author's final `sacct` line from it the next day.

**Steps:**
1. Read both. For each partition and shape, give the measured waits (not the estimates).
2. Propose T_max and the partition. For example: "1 GPU × 4 h on `gpu-h100` started within 2 h, so T_max = 4 h on H100". State the evidence.
3. Read the session script on the compute node: does it accept a longer `--time`?
4. STOP. The author writes T_max and the GPU model into the PLAN row (§8).

### H1 — Environment (J0; ENGINEERING_ONLY; 1 day)

**Needs:** the §8 row; the Mac agent's pins: the harness and paper commits, and the llama.cpp commit as in the RUNBOOK §5 pin table.

**Steps:**
1. Set up the bare repositories and push from the Mac (§0.2).
2. Run J0: the venv, a llama.cpp build for `sm_90`, staging, hashes.
3. Pick the CUDA module: the newest module the pinned llama.cpp commit builds with, among the 12.x modules first (`CUDA/12.9.1`), because 13.x is untested with that commit *(proposed)*. Record the module list.
4. Run the GPU check in `dev-gpu-h100`: `llama-server` loads a test model with full offload.

**Done when** a fresh reviewer has accepted `HK2_H1_<date>.md`.

### H2 — Ports and smoke (G.1; ENGINEERING_ONLY; 3–5 days, in parallel with H3 per node)

**Needs:** the Mac agent's M10 step 0 (the shared pieces) at a reviewed commit, and R1-BX-PORTING-CONFIRM (porting by you, R1-SERVER-AGENTS-TWO).

**Steps,** per candidate task:
1. Port it on `hk2-trackg-20261104`: data preparation, the fixed-step wrapper, the metric parser with the divergence class, the `NodeSpec`, resource limits, and **3–5 representative edits declared as diffs before any measurement**, committed with a hash.
2. Have a fresh reviewer review each port before use.
3. Run J1 smoke. **Done when** scope enforcement rejects a frozen-path edit and the smoke manifest is complete.
4. Test-scored tasks select on validation only.

### H3 — Census (G.0, G.1b; ENGINEERING_ONLY; 2–4 days)

**Steps,** per ported node, in J2 jobs:
1. Licence and availability (G.0.1). This is desk work, done on the Mac.
2. Raw cost at the fixed step budget.
3. Determinism: the same seed twice.
4. The noise floor over seeds 8001–8010. Report σ̂, the largest |z| and the excess kurtosis.
5. The D21 verdict.
6. The concurrency sweep (k = 1, 2, 4).

**Output:** `docs/r1/reports/TRACKG_CENSUS_<date>.md`, one row per candidate plus the screening funnel per suite (R1-BX-D12). Also the GPU-hour projection for H5–H7 at K = 6 and K = 10 (§0.4).

**Then** the author fixes the T1/T2 lists (G.3) and k. Liveness with the main proposer (G.1b step 4) waits for X.7 and the pinned G.2.

### H4 — Proposer qualification (J1b; ENGINEERING_ONLY; ½ day)

**Needs:** X.7 (the main proposer) and the author's committed pass criterion. The second proposer (the exam runner-up) is qualified the same way when its row exists.

**Steps:** run J1b, then the review loop.

### H5 — T1 pilot (G.4; ENGINEERING_ONLY; 1–2 days)

**Needs:** H3, H4, G.2 pinned, and the G.3 row.

**Steps:** a short sweep-2-shaped run on 2–3 T1 nodes. Measure:
- proposals per hour and run time;
- diff liveness;
- the duplicate, inert and divergence rates;
- prompt lengths with code context;
- whether the proposer and the task runs fit on one GPU.

**Then** the Mac agent recomputes the R1-BX-D14 dates from these numbers and reports to the author before applying them.

### H6 — Sweep 2, T1 part (G.5; EVIDENCE)

**Needs:** the author's G.5 note.

**Steps:** W = 20; about 12 campaigns per node; memory `append_only_summary` and `none`. STOPs as B.1b, plus:
- divergence above twice the census rate *(proposed)*;
- a scope violation;
- a pin mismatch.

### H7 — Audits and merge (J4, J5; EVIDENCE)

**Steps:**
- About 150 audited proposals per node, at K = 10 unless K = 6 is in force.
- Pairs are never split.
- J5 builds the table.
- The table goes to analysis only after R1-BX-D8-CONFIRM.

### H8 — Downtime (§0.5)

Freeze on 21 Nov, copy-back, and the census after the downtime.

## 3. Code the Mac agent writes (M10, HoreKa part; reviewed before use)

Each item is a revision of draft §5, with the scan's findings applied.

1. **`r1/scripts/hk2/hk2_submit.py`** generates job scripts from a manifest and records the manifest sha256 in each. It refuses:
   - a missing partition, time, account or `--mem`;
   - more than 90 jobs outstanding (`MaxSubmitJobs=100`);
   - a second job in a `dev` partition while one is outstanding;
   - any production job on a dev partition;
   - a job whose now + `--time` passes the cutoff.

   It sets `--deadline=<cutoff>`. It records `sbatch --test-only` output at submission, for the ledger and the queue record.
2. **`hk2_status.py`** runs only `squeue -u $USER` and `sacct -u $USER`, at most once every 60 s. Cluster-wide views are refused on this account.
3. **The `slurm` host mode** of `c3_label_sweep.py` and the collector:
   - **GPUs come from `CUDA_VISIBLE_DEVICES` inside the job.** Record `SLURM_JOB_GPUS`, the UUIDs (`nvidia-smi --query-gpu=uuid`), the driver, CUDA and the modules. Never use node-level indices.
   - **The occupancy check ignores graphics processes** (type `G`, for example `/usr/libexec/Xorg`) and any process under 256 MiB *(proposed)*. It exits only on a foreign compute process above that size, and records every process it saw.
   - The Ada-only Paper A check is skipped. Commits stay local.
4. **The GPU slot allocator:** k runs per GPU on the job's GPUs. In J3, the proposer shares the GPU with the task runs *(proposed)*; the multi-GPU layout of the draft remains an option. The CPU-node path stays byte-identical (tested).
5. **Resumable units:** run, campaign root, audit pair (§1). A unit's records are written only when it is complete. `audit.py --shard i/S` and `audit.py merge` refuse duplicates and missing pairs.
6. **Continuations:** a job may submit its own continuation, through `hk2_submit.py` and its guards only.
7. **The GPU ledger** (§0.4), filled from `sacct`.
8. **Templates J0–J5**, with tests against fake Slurm variables (including `SLURM_JOB_GPUS=3` with `CUDA_VISIBLE_DEVICES=0`), a fake Xorg process and a fake llama-server.

## 4. Schedule (estimates; gates as in §2)

| When | What | Gates |
|---|---|---|
| 4–6 Nov | Queue probe (today); H0; the §8 row; M10 step 0 and §3 code started | The author's row |
| 6–8 Nov | H1 environment; first ports | M10 step 0 reviewed |
| 8–15 Nov | H2 ports and smoke; H3 census node by node | Each port reviewed |
| about 12–18 Nov | H4 qualification and H5 pilot, **if X.7 has named the pick by then** | X.7, G.2 pinned, G.3 row |
| 18–21 Nov | First H6/H7 waves only if their note exists and the queue allows; otherwise more census | G.5 note |
| 21 Nov 12:00 | Freeze and copy-back | — |
| 23 Nov – 4 Dec | Downtime; Mac-side work continues | — |
| from 5 Dec | Census after the downtime; H6/H7; J5 | R1-BX-D8-CONFIRM before analysis |

**What this means for B.7 (≈ 8 Dec, R1-BX-D14).** The T1 labels need X.7, then H5, H6 and H7. Most of H6/H7 will probably fall after 5 Dec, so B.7 on 8 Dec with T1 labels is unlikely. This is the author's H1 decision; the census and pilot numbers (H3, H5) give the basis for it.

## 5. STOPs

- Any step of §0.2 fails: the session, the forward, a gate or the teardown.
- A policy message from NHR@KIT or Slurm that names this account, warns about misuse, or says a job was blocked by policy.
- A pin mismatch, a scope violation, or a frozen-path edit that is not refused.
- A foreign compute process on an allocated GPU (§3 item 3).
- The ledger reaches 300 GPU-h.
- A job of yours runs past its expected time by more than 50 % *(proposed)*.
- The cutoff is near with work outstanding: 21 Nov 12:00.
- Anything this runbook does not cover.

## 6. Relation to other documents

- **The draft** `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` stays as history. This runbook changes it in these places:
  - jobs are 1-GPU and short, not whole-node 12–47 h;
  - J3 puts the proposer and the runs on one GPU *(proposed)*;
  - `--deadline` equals the cutoff;
  - the occupancy check ignores Xorg;
  - GPUs are mapped by `CUDA_VISIBLE_DEVICES`;
  - staging happens inside jobs, so the author no longer stages on the login node;
  - the NHR@KIT question of draft §4 is answered by the tunnel route;
  - the budget is 400 GPU-h.
- **`TRACK_G_RUNBOOK.md`** says what each G step measures. This runbook says how it runs on HoreKa 2.
- **The scan prompt** (rev 5.6) is the session procedure (§0.2).

## 7. Open for the author

1. **T_max and the GPU model** (H100, or H200 by an amending row), after the queue probe (H0).
2. **The cutoff:** 22 Nov 00:00 CET, and the 21 Nov 12:00 freeze *(proposed)*.
3. **The 300 GPU-h STOP** *(proposed)*.
4. **J3 layout:** the proposer on the same GPU as the runs *(proposed)*, or the draft's separate-GPU layout.
5. **H1** (the B.7 date), after H3/H5.
6. **The J1b pass criterion**, before H4.

## 8. PLAN row to commit (the author's words go in the decision cell; the Mac agent records it)

> | R1-HOREKA-RUNBOOK (4 Nov) | **The HoreKa agent runs the T1 tier on HoreKa 2 by `prompts/HOREKA_RUNBOOK_20261104.md` (revision as accepted).** Author, 17:12: "批准第 1 步的排队实测", "400GPU小时没问题", "11月12开始太晚了", "写 HoreKa 执行 runbook". <br>*(proposed)* Short 1-GPU jobs of at most T_max hours, T_max and the GPU model fixed after the queue probe (H0); budget 400 GPU-h with a STOP at 300; cutoff 22 Nov 00:00 CET, `--deadline` equal to the cutoff, freeze 21 Nov 12:00. <br>*(open)* T_max; H100 or H200; the J3 layout; the J1b criterion; H1. |
