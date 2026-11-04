# Paper B (route R1) — HoreKa agent runbook: the T1 tier on HoreKa 2 (4 Nov 2026, revision 2)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request ("写 HoreKa 执行 runbook", 17:12); AI-assisted.** Revision 2 addresses the independent review `reviews/HOREKA_RUNBOOK_REVIEW_20261104.md`, which did not accept revision 1 (1 BLOCKING, 11 MAJOR, 13 MINOR, 6 NIT). The answers to that review are in §9.

**Sources.**
- The scan report `docs/r1/reports/HOREKA_SCAN_20261104.md`, with its raw output under `reports/horeka_scan_20261104/`.
- The draft `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (rev 2). For execution, this runbook replaces it.
- `prompts/TRACK_G_RUNBOOK.md`, for what each step G.0–G.6 measures.
- PLAN §10: R1-T1-HOREKA (13:45), R1-SERVER-AGENTS-TWO (14:58) and the R1-BX rows.

**The author's words at 17:12, after the scan.**
- "批准第 1 步的排队实测": approval of the queue probe, `prompts/HOREKA_QUEUE_PROBE_PROMPT_20261104.md`.
- "400GPU小时没问题": 400 GPU-hours are acceptable.
- "11月12开始太晚了": 12 November is too late to start.
- "写 HoreKa 执行 runbook": the request for this file.

**This runbook authorizes nothing by itself.**
- It holds only once the author has committed the PLAN row in §8. The Mac agent drafts that row on `mac-int-20261104`; it holds once the author commits it, or tells the Mac agent in chat to commit it.
- ENGINEERING_ONLY work also needs that row.
- EVIDENCE work also needs the author's committed authorization note. EVIDENCE here means the T1 part of sweep 2, its audits, and the closed loop.

**Who you are.** You are the **HoreKa agent** (Claude Code), started by the author on his Mac.
- You act only on **HoreKa 2** (R1-SERVER-AGENTS-TWO).
- The operator acts on TASL-2, TASL-7, deepthought and Ada. You never act there.
- The Mac-local agent writes the shared code (task M10) and integrates the documents on `mac-int-20261104`.

**Terms.**
- A **task node** is a harness benchmark node (for example an MLGym task). A **compute node** is a HoreKa machine.
- The phases are **HK0–HK8**.
- "**PLAN item H1**" is the author's pending decision on the B.7 date and the partial-T1 fallback.

**Authority, in order.** If two of these conflict, STOP and ask.
1. `docs/r1/PLAN.md` §10 on `mac-int-20261104`, at the commit the author gives you.
2. `docs/r1/RUNBOOK.md` (Track G) and `prompts/TRACK_G_RUNBOOK.md`.
3. `docs/r1/STATUS.md`.
4. This file.

Report to the author in **Chinese**, short and concrete. Write reports, reviews and commit messages in **English**.

---

## 0. Ground rules

### 0.1 HoreKa 2 as the scan measured it (4 Nov)

**Where the facts come from.** The GPU-node facts below were measured on **`hkn0901`**, which is the `dev-gpu-h100` node. The production `gpu-h100` nodes are `hkn[0902-0922]`. The queue probe's job outputs confirm the GPU model and memory per production node (HK0).

| Item | Value | Consequence |
|---|---|---|
| Account | `hk-project-p0027888`, the only one. The association has no GPU limit; GrpJobs = 50 running; MaxSubmitJobs = 100. Fair-share factor 0.79 | Every job sets `-A hk-project-p0027888`. The 100-job limit counts all of the user's jobs, including the queue probe's |
| `PrivateData` | `accounts,events,jobs,nodes,reservations,usage,users` | Refused: `sinfo -s`, `scontrol show node`, cluster-wide `squeue`, `sreport`, reservations. Works: `squeue -u $USER`, `sacct -u $USER`, `scontrol show partition`, `scontrol show job`. `sinfo_t_idle` looks filtered; do not use it for planning |
| `gpu-h100` | 21 compute nodes × 4 H100; 128 CPUs per node; 746,880 MB allocatable per node; MaxTime 2 days; `OverSubscribe=NO`. DefMemPerGPU 186,720 MB | `--exclusive` gave a whole node in a `--test-only` estimate (128 CPUs). No running job has confirmed it yet |
| `gpu-h200` | 13 compute nodes × 4 GPUs; 192 CPUs per node; MaxTime 2 days; open to all accounts | Waiting time is measured by the queue probe |
| `dev-cpu`, `dev-gpu-h100` | 1 h maximum. Both use QoS `dev`: **one job at a time per user**, 3 submitted | Setup and smoke tests only |
| `agent` | One compute node, 384 cores, 3 days. QoS `agent` caps a user at **2 CPUs**, which one session uses | **One session per user at a time** (§0.2) |
| Queue | `--test-only` estimates for `gpu-h100`: 4 GPUs × 24 h exclusive → 12 Nov; **1 GPU × 4 h → also 12 Nov**. A 15-min job in the separate `dev-gpu-h100` partition, estimated at +6 h, started after 29 min | *(hypothesis, tested by the queue probe)* Short 1-GPU jobs also start well before their estimates in `gpu-h100`. HK0 decides |
| GPU (`hkn0901`) | H100, 95,830 MiB, `sm_90`, driver 615.71.09, CUDA UMD 13.4, MIG off. Xorg holds 17 MiB. `SLURM_JOB_GPUS=3` shows up as `CUDA_VISIBLE_DEVICES=0` | Map GPUs through `CUDA_VISIBLE_DEVICES` and UUIDs, never node indices. The occupancy check ignores Xorg (§3) |
| Storage | `$HOME` and `$PROJECT=/hfs2/data/project/hk-project-p0027888/ka_ir7683` are on the same GPFS (5.4 PB, 3 % used); no quota could be measured. `/scratch` (= `/tmp`) is per job and private, 3.4 TB on `hkn0901` | Code, venv, GGUFs and results go under `$PROJECT`. Per-run working copies go under the job's `/scratch`, which is lost at job end |
| Network | The front pages of `huggingface.co`, `pypi.org` and `github.com` answer from the `agent` node and from `hkn0901`, with no proxy | HK1 tests the exact download URLs, including redirects |
| Modules | `CUDA/12.6.0 … 13.3.0`, `GCC/12.3.0 … 16.2.0`, `CMake/4.2.1-GCCcore-15.2.0`, `Python/3.11.3 … 3.14.2`. System `python3` is 3.9.21. Present: git, git-lfs, apptainer, rsync. Missing: `uv`, `conda` | The modules are pinned in HK1 and recorded in every job |
| Downtime | **23 Nov – 4 Dec 2026**. No time of day is published, nor any policy for pending jobs. Weekly reboot window: Thursdays 07:00–09:00 | §0.5 |
| Self-submission | `sbatch --test-only` works inside a job. A real self-submission is untested | HK1 tests it once |

### 0.2 How you act on HoreKa

**Never on a login node.** NHR@KIT: "Interactive AI agent usage on login nodes is prohibited… Use the SSH tunnel to compute nodes". Every command of yours runs on the `agent` compute node, through the tunnel.

**Sessions.**
- Open and close each session by `prompts/HOREKA_SCAN_PROMPT_20261104.md` revision 5.6, §1 steps 0–5: the wrappers, the author's open master connection, the session script, the forward, the two gates, and the ordered teardown.
- Use a new folder for each session: `…/_snapshots/hk2_session_<UTC date-time>/`.
- Gate 2 passes when both of these hold, as in the scan: `SLURM_JOB_ID` equals the session job id, and `squeue -u $USER -p agent -t R` shows that job running on the host. (`scontrol show node` is refused on this account.)
- On the login node, exactly two things run for you: the session script, and the forward on the author's master connection.
- **One session per user.** The `agent` QoS allows 2 CPUs per user, and one session takes both.
  - Before asking for the master connection, ask the author to confirm that no other session of his is open. That includes his own and the queue-probe agent's.
  - Never open a session while another one is open.
  - If a session is still pending after 5 minutes, that is the scan procedure's STOP. Report it as "session slot busy".
- **Cadence.**
  - A session lasts at most 1 h, unless HK1 finds that the script accepts a longer time.
  - Each session is opened at the author's request, through his 2FA master connection.
  - In each report, say when you need the next session and why.
  - No part of the plan may depend on checking more often than the author can open sessions.
- Batch jobs keep running after a session ends.

**A third wrapper, `nodessh-raw`, for git and rsync.** These tools put the host name into the ssh command themselves. Create the wrapper in each session folder, after Gate 2:

```bash
bash -s <<'EOF'
S="$HOME/Documents/agent_paper_B/.claude-worktrees/_snapshots/hk2_session_<UTC date-time>"
{ printf '#!/bin/bash\nS=%q\n' "$S"; cat <<'W'
[ -e "$S/gate2_ok" ] || { echo "gate2 not passed" >&2; exit 1; }
KH="$S/known_hosts_$(cat "$S/session_tag" 2>/dev/null || echo none)"
exec ssh -F "$S/vscode_ssh_config" -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=4 \
  -o IdentitiesOnly=yes -o UserKnownHostsFile="$KH" -o StrictHostKeyChecking=accept-new "$@"
W
} > "$S/nodessh-raw"; chmod 700 "$S/nodessh-raw"; echo RAW_OK
EOF
```

- Use it only with the host `vscode-hk2`.
- Remote paths are always absolute: `/hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/…`. Git and rsync quote remote paths, so `$PROJECT` would not be expanded.
- Give rsync `--timeout=300`. Record `rsync --version` and `git --version` from the Mac in the HK1 report; macOS may ship openrsync.

**Code transfer.** There are no GitHub credentials on HoreKa, as on the portal (R1-EXAM-TRANSFER).
- Create the bare repository first: `"$S/nodessh" 'git init --bare /hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/git/<repo>.git'`.
- Push from the Mac: `GIT_SSH_COMMAND="$S/nodessh-raw" git push vscode-hk2:/hfs2/…/r1/git/<repo>.git <commit>:refs/heads/<branch>`.
- Check out **detached** at the pinned commits into `/hfs2/…/r1/work/<repo>@<short sha>/`.

**Downloads.**
- On HoreKa, download only **ungated** URLs, pinned by revision and sha256.
- A gated artefact is fetched on the Mac and pushed through the tunnel with `rsync -e "$S/nodessh-raw"`.
- No token is ever placed on HoreKa.

**Results on HoreKa.**
- EVIDENCE outputs (HK6, HK7, J5) go under `/hfs2/…/r1/results/evidence/`.
- Everything else goes under `/hfs2/…/r1/results/engineering/`.
- Interrupted units go under `/hfs2/…/r1/results/_interrupted/<jobid>/` (§1). They are never read for labels.

**Copy-back.**
- Normal copy-back: `engineering/` only, to `<Mac worktree>/results/r1/trackg/hk2/`. Commit JSON, manifests and `.jsonl` up to 20 MB; gzip larger files and list them in `SHA256SUMS`.
- Sealed copy: `evidence/` to `<Mac>/results/r1/trackg/hk2_sealed/`.
  - *(proposed)* That folder is never committed to any branch. Only its `SHA256SUMS` and file counts are committed.
  - The Mac agent makes every analysis reader refuse the `hk2_sealed/` path, in addition to the D8 PLAN check.
  - After R1-BX-D8-CONFIRM, the author decides how the evidence enters analysis.

**The author does these things for you:**
- confirms that no other session is open;
- opens the master connection (`ssh -fN hk2`);
- does any one-time key setup;
- answers the STOPs.

### 0.3 Rules

**Production submission and NHR@KIT question (c) — open.**
- R1-T1-HOREKA keeps this *(open)*: "Whether agents may submit and monitor jobs routinely stays open until NHR@KIT answers the draft's §4 questions. Until then the author submits production jobs."
- The tunnel route answers only draft §4 question (a): where the agent's commands run.
- Question (c) is still open: does an LLM proposer loop inside a GPU batch job count as an "AI agent workload"?
- **Until the author rules on this (§7 item 1):**
  - You submit only jobs in `dev-cpu`, `dev-gpu-h100` and `cpu`, and only for HK1 and HK2.
  - Every `gpu-h100`/`gpu-h200` job is prepared by you with `hk2_submit.py --dry-run`. The author submits it himself, in a session he opens for that.
  - No job submits its own continuation.

**Never touch what you did not start.**
- Never cancel, signal or edit another user's job or file, or a job the author started himself.
- You cancel only your own job ids, which you record at submission.
- A standing recovery authorization exists only if the author writes one to you, with a scope.

**Pins.** Every job runs the commits and artefacts of the RUNBOOK §5 pin table: paper and harness commits, the llama.cpp build, GGUF sha256 values, configs. A mismatch is a STOP.

**Run labels.** ENGINEERING_ONLY (environment, ports, census, qualification, liveness, pilot) needs the §8 row. EVIDENCE also needs the author's note.

**Seeds.**
- 7006–7010 are evaluation seeds only.
- Exam seeds (9001+, 9101+, 9201+) never enter a C3 sweep.
- Noise floors use 8001–8010.
- K = 10 until an author row puts R1-BX-D3's K = 6 into force.
- J5 takes labels only from 7001–7005 at K = 10 (7001–7003 at K = 6). The evaluation columns take only 7006–7010 (7006–7008). J5 refuses any other seed.

**Placement and one GPU model per table (R1-BX-D5).**
- **Placement** is the tuple:
  - GPU model;
  - a 1-GPU job on a shared compute node;
  - k task runs per GPU;
  - whether llama-server shares the GPU;
  - `-c` and `--mem` per run;
  - worker and thread counts.
- **Labels** are the J4 audit runs: no llama-server, with k fixed.
- A task node's σ̂ comes from a floor measured at the **same placement as its labels**. Changing any element means re-measuring the floor.

**When fixed step budgets keep the metric independent of throughput.** Fixed budgets alone are not enough. They are enough when all three of these hold:
- (a) the port forces deterministic algorithms (`cudnn.benchmark = False`, `torch.use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG`), or records which of them it cannot force;
- (b) worker and thread counts are fixed in the `NodeSpec`, never derived from `nproc`;
- (c) the HK3 determinism check (same seed, two different jobs, two different compute nodes, one of them under load) is bitwise equal.

If (c) fails, σ̂ comes from floor seeds spread over at least 3 jobs on different compute nodes, and the report says so.

**Infrastructure failure versus divergence** *(proposed; §7 item 7)*.
- These are **infrastructure failures**:
  - a run killed by its timeout;
  - a run killed by Slurm (time limit, node failure);
  - an OOM while co-located processes exceed their declared memory.
- An infrastructure failure is recorded, its unit is re-run whole, and it never counts as a divergence.
- An OOM within the run's own memory cap stays an outcome of the edit.
- Divergence keeps its meaning: a non-finite loss, or no metric at the budget, from the run itself. It is never re-run to hide it.
- The run timeout is 3 × the run time **measured at the chosen placement** (HK3).

**Analysis gate (R1-BX-D8).** No sweep-2 T1 label table enters analysis before R1-BX-D8-CONFIRM. The sealed copy (§0.2) is how results are kept safe until then.

**Secrets and the second proposer.**
- Never read `~/.config/r1/secrets.env` or any key file. No API calls run on HoreKa.
- *(open)* In chat the author said "用 exam 第二名": use the exam runner-up instead of an API model for the second proposer. That is not yet a PLAN row. R1-BX-D6 and R1-BX-PROPOSED-CONFIRM D6 (an API model of another family, with a cost cap) stand until an amending row is committed.
- The second proposer serves only the closed loop. Its host plan is open. You qualify it only if an amending row and the Phase C/D host plan put that loop on HoreKa.

**Review loop at every STOP.**
1. Spawn a **fresh** reviewer. Give it the phase goal, this runbook, the pins and the outputs, but not your conclusions.
2. The reviewer writes `docs/r1/reviews/HK2_<PHASE>_REVIEW_<date>.md`.
3. Fix or answer each finding, and re-check with the same reviewer until it writes **accepted**. You never accept your own phase.

**Branches.**
- Reports go on `hk2-ops-20261104`, made from `mac-int-20261104` in your own worktree. Never use the Mac's main working tree.
- Ports go on `hk2-trackg-20261104` *(proposed; R1-BX-PORTING-CONFIRM names `ops-trackg-<date>` for the operator, and the §8 row amends it)*.
- Never push `main`, `r1` or `exam-x-*`, and never force-push.
- Commit author: `Dowling Wong <wangdowling@gmail.com>`, with the attribution lines the author gives you.

**Reports.** After every STOP:
1. Write `docs/r1/reports/HK2_<PHASE>_<date>.md`.
2. Add a STATUS entry.
3. Send the author a short Chinese message: what is done, commits, checks, the review verdict, the decisions needed, and when you need the next session.

**Deletions.** Never delete evidence. To retire anything, move it into a `_to_delete/` folder next to it and tell the author.

### 0.4 GPU-hour budget

- *(interpretation, for the author to confirm)* "400GPU小时没问题" is treated as a **ceiling of 400 GPU-h**.
- **Ledger:** `results/r1/trackg/hk2/gpu_ledger.csv`, one row per job: job id, name, phase, partition, GPUs, elapsed time, allocation GPU-h, end state. Allocation GPU-h = elapsed × GPUs allocated; an exclusive job counts all 4 GPUs. A job ended by `--deadline` (state `DEADLINE`) is recorded, never resubmitted, and reported.
- **Guard at submission** (§3 item 1). `hk2_submit.py` refuses a job when the sum of these passes the STOP threshold (*proposed*: 300 GPU-h):
  - used GPU-h, from `sacct -X -u $USER` since the campaign start;
  - reserved GPU-h, the time limit × GPUs of every pending or running job of yours;
  - the new job's time limit × GPUs.

  The same check applies to every submission, the author's included.
- **Projections** are in allocation GPU-h. They include:
  - the census of every screened candidate (the R1-BX-D12 funnel);
  - setup, smoke and qualification;
  - the pilot;
  - re-runs;
  - S1.1;
  - job start-up time (venv, GGUF load, data copy).

  The draft's 320 GPU-h (K = 6) and 480 GPU-h (K = 10) for about 8 task nodes count run time only, so they are lower bounds.
- **A gate before HK6:** STOP after HK5 with the projection for HK6 + HK7 at the K in force. The author fixes the number of task nodes, K and the budget before any G.5 note.

### 0.5 The downtime: three times *(proposed; §7 item 3)*

| Time | When | Meaning |
|---|---|---|
| **F, submission freeze** | Fri 20 Nov 12:00 CET | `hk2_submit.py` refuses every submission after F |
| **C, job-end cutoff** | Fri 20 Nov 20:00 CET | Every job sets `--deadline=2026-11-20T20:00:00` (cluster local time, CET; HK1 checks `date +%Z`). It is never set earlier. Submission refuses now + `--time` > C. The runner inside each job stops at a unit boundary before C |
| **D, copy-back done** | Sat 21 Nov 18:00 CET | Between C and D: copy back `engineering/`, make the sealed copy of `evidence/`, verify `SHA256SUMS`, report |

- *Why Friday:* the margin before 23 Nov stays above 24 h even if the shutdown starts in the early morning, and D is not late on a Saturday. The author confirms that he can open sessions on 20–21 Nov, or moves F, C and D.
- **Slurm's `--deadline`:** Slurm removes a pending job whose start would be later than C − `--time`. So a job never starts if it cannot end by C. Templates never set `--time-min`.
- **After the downtime (from 5 Dec, expected):**
  1. Before anything else, check your own state: `squeue -u`, `sacct -u` since 20 Nov, the `$PROJECT` tree and its checksums.
  2. Resume nothing automatically.
  3. Report, and wait for the author.

## 1. Job design

*(proposed hypothesis, tested by the queue probe in HK0)* The work unit is a **1-GPU job of at most T_max hours** (default 4 h). No production job requests more than the probed shape: `-c ≤ 32`, `--mem ≤ 180G`. A larger request makes the measured wait meaningless. Whole-node exclusive jobs are not used, unless the author rules otherwise.

**Units.**
- The unit is one run, one campaign root, or one audit pair.
- A unit's records are written only when the unit is complete.
- Each job sets `#SBATCH --signal=B:USR1@600`. On the signal, the runner moves the open unit to `results/_interrupted/<jobid>/` and exits cleanly.
- The next job re-runs that unit whole, from a fresh working copy. No `*_pending.json` guard carries over.
- A unit cut twice is a STOP.
- HK5 must show that a campaign root fits in ≤ 0.6 × T_max.

**Continuations.** A job may submit its own continuation only after the author's ruling in §7 item 1, and only through `hk2_submit.py` with all its guards: budget, F, C, 90 jobs. `sbatch` is called with a scrubbed environment (no `SLURM_*` or `SBATCH_*` variables). HK1 tests one real self-submission first.

| Job | Partition and resources *(proposed)* | What it runs |
|---|---|---|
| **J0 setup** | `dev-gpu-h100`, 1 GPU, ≤ 1 h, in several steps | The venv under `$PROJECT` from pinned wheels. llama.cpp at the pinned commit, built **on the GPU compute node** with `-DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES=90` and `CUDA/12.9.1` + `GCC/14.3.0` *(proposed; the cluster's own pairing for CUDA 12.9.1)*. Downloads from exact, tested URLs. sha256 against the staging manifest. Version records |
| **J1 smoke** | `dev-gpu-h100`, 1 GPU, ≤ 1 h, one at a time | One fixed-step run per ported task node with a stub manager; the frozen-path refusal; a llama-server load test of a model the author names |
| **J1b proposer qualification** | 1 GPU, ≤ T_max | O5-style checks: full offload, 50 prompts × 3 at `cache_prompt: false`, latency, a projection. **Within-server identity twice: on an idle GPU, and with k task runs on the same GPU.** The pass criterion is committed by the author before it runs |
| **J2 census** | 1 GPU, ≤ T_max | In the HK3 order: determinism, concurrency sweep, co-location arm, then floors at the fixed placement |
| **J3 campaigns** (HK4b liveness, HK5 pilot, HK6 sweep) | 1 GPU, ≤ T_max | llama-server for the main proposer (thinking off, `cache_prompt: false`) and the campaign's task runs. They share the GPU **only if** the HK3 co-location arm and J1b's loaded identity test pass; otherwise J3 uses 2 GPUs, one for each *(proposed)* |
| **J4 audits** | 1 GPU, ≤ T_max | Candidate–incumbent pairs on the K seeds, k runs per GPU, no llama-server. A pair is written only when complete |
| **J5 merge** | `cpu`, ≤ 1 h, `--mem` explicit (the `cpu` default is 1,945 MB per CPU) | Merges shards; refuses duplicates, missing pairs and wrong seeds (§0.3); builds the T1 label table |

**Every template sets** `-A`, `-p`, `--time`, `-N 1`, `-n 1`, `-c`, `--mem` (explicit), `--deadline=<C>` and `--signal=B:USR1@600`. Templates use `srun` only where a test covers it.

**The llama-server in J1b and J3, on a shared compute node.**
- It listens on 127.0.0.1 with `--api-key` set to a random per-job token generated inside the job. The token is not a credential to any outside service.
- Before the first request, the runner checks two things: the listening socket belongs to its own llama-server PID (`ss -ltnp`), and the server reports the pinned model path and sha.
- If the derived port is taken, the runner picks the next free port and records it.
- Any mismatch is a STOP.

**GPU model.** One model for the whole T1 table: H100, per R1-T1-HOREKA. *(open)* H200 instead, if the queue probe shows much shorter waits there; that needs an author row amending R1-T1-HOREKA, and every floor and label is then measured on H200.

## 2. Phases

Durations are estimates.

### HK0 — Queue facts and the job shape (Mac-side desk work; ½ day)

**Needs:** the queue probe report, committed at `docs/r1/reports/HOREKA_QUEUE_20261104.md`; the author's `sacct` line from it a day later.

**Steps:**
1. For each partition and shape, give the **measured** waits. One sample per shape at one moment is all the probe gives; say so.
2. Confirm from the job outputs that the production compute nodes have the same GPU model and memory as `hkn0901`.
3. Propose T_max and the partition, with the evidence.
4. **If no 1-GPU shape in `gpu-h100` or `gpu-h200` started within 24 h of submission, STOP.** The author chooses one of:
   - accepting later starts;
   - H200, by an amending row;
   - the Ada whole-table fallback (R1-T1-HOREKA);
   - a smaller T1 scope.
5. STOP. The author fixes T_max and the GPU model in a **new** dated row, R1-HOREKA-TMAX.

### HK1 — Environment (J0; ENGINEERING_ONLY; 1 day)

**Needs:** the §8 row; the Mac agent's M1 accepted (the RUNBOOK §5 pin table exists only after it); the pins of the harness, the paper and the llama.cpp commit; `hk2_submit.py` and `hk2_status.py` (§3), reviewed.

**Steps:**
1. In the first session, read the session script on the compute node (`command -v start-vscode-remote-ssh.sh`, then read the file). Does it accept a longer `--time`?
2. Check `date +%Z`.
3. Create the bare repositories and push (§0.2).
4. Run J0. Test the exact download URLs with redirects first.
5. Run one real self-submission test: a `dev-cpu` job submits one `dev-cpu` job with a scrubbed environment. QoS `dev` allows only one running job, so the child waits until its parent ends.
6. Record the modules, the versions and `rsync`/`git` on the Mac.

**Done when** a fresh reviewer has accepted `HK2_HK1_<date>.md`.

### HK2 — Ports and smoke (G.1; ENGINEERING_ONLY; 3–5 days)

**Needs:** the Mac agent's M10 step 0 (the shared pieces), reviewed; R1-BX-PORTING-CONFIRM as amended by the §8 row.

**Steps,** per candidate task:
1. Port it on `hk2-trackg-20261104`:
   - data preparation;
   - the fixed-step wrapper;
   - the deterministic settings of §0.3 (a) and (b);
   - the metric parser with the divergence class;
   - the `NodeSpec`;
   - resource limits;
   - **3–5 representative edits declared as diffs before any measurement**, committed with a hash.
2. A fresh reviewer reviews each port before use.
3. Run J1 smoke. **Done when** scope enforcement rejects a frozen-path edit and the smoke manifest is complete.
4. Test-scored tasks select on validation only.

### HK3 — Census (G.0, G.1b steps 1–3; ENGINEERING_ONLY; 3–5 days)

**Steps,** per ported task node, **in this order**:
1. Licence and availability (G.0.1). Desk work on the Mac.
2. Raw cost at the fixed step budget.
3. **Determinism:** the same seed in two different jobs, on two different compute nodes, one of them under load (k = 4). Compare bitwise.
4. **Concurrency sweep:** k = 1, 2, 4 runs per GPU. Measure throughput, and check identity at each k.
5. **Co-location arm:** the baseline × 3 seeds with an active llama-server load on the same GPU, compared bitwise with the same seeds without it.
6. **STOP.** The author fixes k and the J4 placement, and whether J3 co-locates.
7. **Noise floor** at that placement: seeds 8001–8010 × the declared edits plus the baseline. Spread the seeds over at least 3 jobs if step 3 failed. Report σ̂, the largest |z| and the excess kurtosis.
8. The D21 verdict.

**Output:** `docs/r1/reports/TRACKG_CENSUS_<date>.md`, with one row per candidate, the screening funnel per suite (R1-BX-D12), and the allocation GPU-h projection for HK4–HK7 at K = 6 and K = 10 (§0.4).

### HK4 — Proposer qualification (J1b; ENGINEERING_ONLY; ½ day)

**Needs:** X.7 (the main proposer) and the author's committed pass criterion.

**Steps:** run J1b with both identity tests, then the review loop.

### HK4b — D28 diff liveness (G.1b step 4; ENGINEERING_ONLY; 1 day)

**Needs:** HK4 passed and G.2 pinned.

**Steps:**
- One J3-shaped job per candidate task node: 2 instances × W = 10.
- Output: the D28 column of the census report.
- A pick that fails diff liveness on a T1 node is a STOP (R1-BX-PROPOSED-CONFIRM D4).
- **The G.3 row (the T1/T2 lists) waits for HK4b**, or the author fixes G.3 provisionally and confirms it after HK4b.

### HK5 — T1 pilot (G.4; ENGINEERING_ONLY; 1–2 days)

**Needs:** HK4b and the G.3 row.

**Steps:** on 2–3 T1 task nodes, a short sweep-2-shaped run. Measure:
- proposals per hour and run time;
- diff liveness;
- the duplicate, inert and divergence rates;
- the infrastructure-failure rate;
- prompt lengths with code context;
- the campaign-root length against 0.6 × T_max.

**Then:**
- The Mac agent recomputes the R1-BX-D14 dates and reports them to the author before applying them.
- **STOP with the HK6 + HK7 projection (§0.4).**

### HK6 — Sweep 2, T1 part (G.5; EVIDENCE)

**Needs:** the author's G.5 note and the budget decision after HK5.

**Steps:**
- W = 20.
- About 12 campaigns per task node.
- Memory `append_only_summary` and `none`.
- **The S1.1 edit–edit interaction measurement on each T1 task node** (R1-BX-D4); its GPU-h is in the HK5 projection.

**STOPs:** as B.1b, plus:
- divergence above twice the census rate *(proposed)*;
- an infrastructure-failure rate above 2 % in a wave *(proposed)*;
- a scope violation;
- a pin mismatch.

### HK7 — Audits and merge (J4, J5; EVIDENCE)

- About 150 audited proposals per task node, at K = 10 unless K = 6 is in force.
- Pairs are never split.
- J5 builds the table under `evidence/`.
- It enters analysis only after R1-BX-D8-CONFIRM.

### HK8 — Downtime (§0.5)

- F, C and D.
- The sealed copy.
- The state check after the downtime.

## 3. Code the Mac agent writes (M10, HoreKa part; reviewed before use)

These revise draft §5. The Mac runbook's M10 paragraph points here once the §8 row exists.

1. **`r1/scripts/hk2/hk2_submit.py`.** It uses the standard library only and runs under the system Python 3.9 (tested under 3.9). It generates job scripts from a manifest and records the manifest sha256 in each. It calls `sbatch` with a scrubbed environment, and records the `--test-only` output at submission. It refuses:
   - a missing partition, time, account or `--mem`;
   - more than 90 jobs outstanding;
   - a second job in QoS `dev` while one is outstanding;
   - any production job on a dev partition;
   - a request above the probed shape;
   - any submission after F;
   - now + `--time` > C;
   - the budget guard of §0.4;
   - until the §7 item 1 ruling: any `gpu-*` submission not run by the author.

   It sets `--deadline=<C>` and `--signal=B:USR1@600`.
2. **`hk2_status.py`** (standard library only, Python 3.9). It runs `squeue -u $USER` and `sacct -u $USER` only, at most once every 60 s. It treats the `DEADLINE` state as expected, and it fills the ledger.
3. **The `slurm` host mode** of `c3_label_sweep.py` and the collector:
   - **GPUs come from `CUDA_VISIBLE_DEVICES` inside the job.** Record `SLURM_JOB_GPUS`, the UUIDs, the driver, CUDA and the modules.
   - **Occupancy check.** It runs at job start, before anything is launched, and later only for PIDs that are not descendants of the job. It ignores graphics processes (type `G`, such as Xorg) and processes under 256 MiB *(proposed)*. It records every process it sees.
   - **The llama-server checks** of §1: api key, port owner, model sha.
   - The Ada-only Paper A check is skipped. Commits stay local.
4. **The GPU slot allocator.** It places k runs per GPU on the job's GPUs, with the co-located or 2-GPU J3 layout as HK3 decides. The CPU-node path stays byte-identical (tested).
5. **Resumable units.** Unit-complete writes, the `USR1` handler, the `_interrupted/` archive, and the "cut twice" STOP. `audit.py --shard i/S` and `audit.py merge` refuse duplicates, missing pairs and wrong seeds.
6. **The evidence/engineering split** (§0.2), and readers that refuse `hk2_sealed/`.
7. **Templates J0–J5.** Tests run against fake Slurm variables (including `SLURM_JOB_GPUS=3` with `CUDA_VISIBLE_DEVICES=0`), a fake Xorg process, a fake llama-server, a taken port, and a `USR1` signal.

## 4. Schedule (estimates) and risks

| When | What | Gates |
|---|---|---|
| 4–6 Nov | Queue probe; HK0; the §8 row; M10 step 0 and §3 code | The author's rows |
| 6–9 Nov | HK1 | §3 reviewed; the §7 item 1 ruling |
| 9–16 Nov | HK2 ports and smoke; HK3 census, task node by task node | Each port reviewed |
| about 13–19 Nov | HK4, HK4b and HK5, **if X.7 has named the pick by then** | X.7, G.2 pinned, G.3 |
| 20 Nov | F 12:00, C 20:00 | — |
| 21 Nov | D 18:00: copy-back and sealed copy done | — |
| 23 Nov – 4 Dec | Downtime; Mac-side work continues | — |
| from 5 Dec | State check; HK6 and HK7; J5 | G.5 note; R1-BX-D8-CONFIRM before analysis |

**Risks.**
- Every session needs the author's 2FA and a free session slot, so HK1–HK3 cannot move faster than his availability.
- The Thursday 07:00–09:00 reboot window falls on 12 and 19 Nov.
- Each STOP has a review loop.
- The fair-share factor (0.79) falls with heavy use.
- A queue surge is likely after the downtime.
- The probe gives one sample per shape.

**For PLAN item H1 (B.7 ≈ 8 Dec, R1-BX-D14).**
- The T1 labels need X.7, then HK4–HK5, then HK6–HK7. With Track X's B1 now at 15 candidates, most of HK6/HK7 will fall after 5 Dec, and may wait for the queue there.
- B.7 on 8 Dec with T1 labels is therefore unlikely.
- The author decides once HK3 and HK5 give numbers.

## 5. STOPs

- Any step of §0.2 fails: the session, the forward, a gate, the teardown. A session still pending after 5 minutes counts ("session slot busy").
- A policy message from NHR@KIT or Slurm that names this account, warns about misuse, or says a job was blocked. **Any reply from NHR@KIT that restricts agent submission or LLM loops in batch jobs** also counts.
- A pin mismatch, a scope violation, or a frozen-path edit that is not refused.
- A foreign compute process on an allocated GPU; a llama-server identity mismatch.
- A unit cut twice. A unit that takes more than 1.5 × its HK5-measured time.
- An infrastructure-failure rate above 2 % in a wave *(proposed)*.
- The budget guard refuses a job.
- F is reached with work outstanding.
- Anything this runbook does not cover.

## 6. Relation to other documents

**The draft** `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` stays as history. This runbook changes it in these ways:
- jobs are 1-GPU and short;
- the proposer co-locates with task runs only if tested;
- `--deadline` equals C;
- there are three downtime times;
- the occupancy check ignores Xorg and the job's own processes;
- GPUs are mapped by `CUDA_VISIBLE_DEVICES`;
- downloads happen inside jobs;
- the llama-server has identity checks;
- the evidence/engineering split;
- the 400 GPU-h budget guard.

The NHR@KIT question (c) stays open (§0.3, §7 item 1).

**Other documents.**
- `TRACK_G_RUNBOOK.md` says what each G step measures; this runbook says how it runs on HoreKa 2.
- The scan prompt (rev 5.6) is the session procedure.
- The Mac runbook's M10 HoreKa paragraph points to this §3 once the §8 row exists.

## 7. Open for the author

1. **Production submission and question (c).** Either:
   - (i) send questions (a) and (c) of draft §4 to NHR@KIT support and record the answer; or
   - (ii) rule in the §8 row that the HoreKa agent submits production jobs from the `agent` node (continuations included), and that J3 runs inside GPU batch jobs, pending NHR@KIT's answer.

   Until then, you submit every `gpu-*` job yourself (§0.3).
2. **T_max and the GPU model** (H100, or H200 by an amending row), after HK0, in row R1-HOREKA-TMAX.
3. **F, C and D** (20 Nov 12:00, 20 Nov 20:00, 21 Nov 18:00), and your availability for sessions on 20–21 Nov.
4. **The budget:** 400 GPU-h as a ceiling, and the 300 GPU-h STOP.
5. **k, the J4 placement and J3 co-location**, after HK3 step 6.
6. **The second proposer:** an amending R1-BX-D6 row for "用 exam 第二名". Note that the runner-up may be of the same family as the pick, which D6 (F3) excludes.
7. **Infrastructure failure versus divergence** (§0.3).
8. **The J1b pass criterion**, before HK4.
9. **PLAN item H1** (B.7), after HK3 and HK5.

## 8. PLAN row to commit

**Context line above the table:** the author's words at 17:12: "批准第 1 步的排队实测"; "400GPU小时没问题"; "11月12开始太晚了"; "写 HoreKa 执行 runbook".

> | R1-HOREKA-RUNBOOK (date) | **[the author's words when he adopts the runbook, quoted verbatim with the time]** |

**Below the table, "Consequences noted by the recording agent (not part of the decision)":**
- *(proposed)* `prompts/HOREKA_RUNBOOK_20261104.md` (the revision as accepted) governs the HoreKa agent: short 1-GPU jobs; the budget guard; F, C and D; the evidence/engineering split.
- Rows this amends or settles:
  - R1-T1-HOREKA's *(proposed)* "the draft becomes the design basis";
  - R1-T1-HOREKA's *(open)* "the author submits production jobs", if the author rules on §7 item 1;
  - R1-BX-PORTING-CONFIRM: porting by the HoreKa agent on `hk2-trackg-<date>`;
  - R1-ADA-CENSUS.
- *(open)* §7 items 1–9.

## 9. Answers to the review of revision 1

| Finding | Answer |
|---|---|
| BLOCKING-1 (NHR (c), production submission) | §0.3 "Production submission"; §7 item 1; §5; §6; §8 |
| MAJOR-1 (backfill premise) | §0.1 queue row and §1 marked as a hypothesis; the HK0 step 4 branch |
| MAJOR-2 (cutoff, freeze, copy-back) | §0.5: F, C and D, with no Saturday freeze; §3 item 1 |
| MAJOR-3 (one session per user) | §0.1 `agent` row; §0.2 "One session per user" and "Cadence"; §4 risks |
| MAJOR-4 (budget bypass and basis) | §0.4 guard at submission, allocation GPU-h, the gate before HK6; §3 item 1 |
| MAJOR-5 (fixed steps not sufficient) | §0.3 conditions (a)–(c) and infrastructure failure; HK3 step 3; §5 |
| MAJOR-6 (k and placement order, co-location) | §0.3 "Placement"; HK3 reordered with a STOP at step 6; co-location arm; J1b's loaded identity test |
| MAJOR-7 (llama-server exposure) | §1 llama-server checks; §3 item 3; §5 |
| MAJOR-8 (sealed copy-back) | §0.2 results split and sealed copy; §3 item 6 |
| MAJOR-9 (second proposer) | §0.3 "Secrets and the second proposer"; §7 item 6 |
| MAJOR-10 (§8 row, HK0 circularity) | §8 restructured; HK0 is desk work and ends in a new row R1-HOREKA-TMAX |
| MAJOR-11 (D28, S1.1) | HK4b; S1.1 in HK6 and in the HK5 projection |
| m1 | §0.1 source note; HK0 step 2; HK1 step 4 (URLs) |
| m2 | §1 continuations; HK1 step 5; §0.4 `DEADLINE`; no `--time-min` |
| m3 | §0.2 `nodessh-raw` (`printf %q`, gate check, absolute paths, `--timeout`, versions); bare repository init |
| m4 | J0 builds on the GPU compute node with `GGML_NATIVE=OFF`; CUDA 12.9.1 + GCC 14.3.0; §3 items 1–2 Python 3.9 |
| m5 | §1 units: `--signal`, `_interrupted/`, cut-twice STOP, 0.6 × T_max |
| m6 | §0.3 seeds, J5 sets |
| m7 | Branch marked *(proposed)*; §8 consequences; §6 M10 pointer |
| m8 | Phases HK0–HK8; "PLAN item H1"; task node and compute node; the 1.5 × STOP; exclusive jobs not used |
| m9 | §4 risks |
| m10 | §1 probed shape; HK0 report path |
| m11 | §0.4 marked as an interpretation |
| m12 | §3 item 3 occupancy check |
| m13 | §0.2 downloads |
| n1–n6 | J5 `--mem`; §0.1 GrpJobs and MaxSubmit, QoS `dev` shared; `sinfo_t_idle` not used; `--exclusive` from `--test-only` only; the deadline format and `date +%Z`; M1 under HK1's needs |
