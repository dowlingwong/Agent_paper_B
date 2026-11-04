# Draft — running Track G T1 work on HoreKa 2 by Slurm job submission (4 Nov 2026)

**Status.** AI-assisted draft (Claude, chat session), written at the author's request ("怎么把t1改写成horeka compatible的提交任务"). It is **not adopted** and authorizes nothing. Whether T1 moves to HoreKa 2 is the author's decision. PLAN §10 currently puts the T1 label runs on Ada (R1-BX-PROPOSED-CONFIRM). If the author moves them, a PLAN row records it and RUNBOOK G.0–G.5 and the two execution runbooks are revised, with an independent review.

**Sources.**
- The author's cheat sheet "HoreKa / HoreKa 2 — Slurm Job Submission" (chat attachment, 4 Nov).
- NHR@KIT documentation: <https://docs.nhr.kit.edu/usage/slurm/> and <https://docs.nhr.kit.edu/get-started/migration/>, read 4 Nov.

Facts not found in these sources are marked *(to check)*.

## 1. Facts that shape the design

| Fact | Source | Consequence |
|---|---|---|
| H100 (Teal) and H200 (Ruby) are on HoreKa 2, `hk2-x86.scc.kit.edu`, user `ka_ir7683`; partition `gpu-h100`, 4 × H100 per node, max 2 days per job, `--partition` and `--time` mandatory | cheat sheet; slurm page | Every job carries an explicit partition and time; every job ≤ 2 days and resumable |
| **Downtime 23 Nov – 4 Dec 2026**: no data access, no jobs | cheat sheet | No job may run into 23 Nov 00:00; results must be copied out before then |
| Max 100 submitted jobs per user (300 per group); dev partitions 1 job | cheat sheet; slurm page | Pack many short runs into one job; never one job per training run |
| `squeue` polled faster than every 30 s gets jobs killed | cheat sheet | Every status helper sleeps ≥ 60 s |
| "Compute intensive tasks must not run on login nodes" | slurm page | Builds, tests and smoke runs go to `dev-*` or batch jobs |
| **"Interactive AI agent usage on login nodes is prohibited"**; an `agent` partition (1 core, ≤ 3 days) exists for AI agent workloads | migration page; slurm page | The SSH operator agent must not drive HoreKa from the login nodes without the centre's confirmation (§4) |
| `$HOME` 50 GB / 2 M inodes; a `PROJECT` directory per compute project; workspaces exist | migration page | Venvs, data, GGUFs and outputs go under `PROJECT` (or a workspace), not `$HOME` |
| Modules move to EasyBuild, with different names | migration page | Module names are discovered on the system and pinned in the job template |
| Compute resources are tied to the project and accounted by Slurm | slurm page | The project's remaining GPU-hours must be checked before planning (§6) |
| Internet from compute nodes; node-local scratch; H100 memory; container support | not stated | *(to check)*. Plan as if there is no internet on compute nodes: stage everything first |

## 2. Why HoreKa 2 suits T1

- **One GPU model for the whole T1 table (H100).** This meets R1-BX-D5 without the cross-model rule change proposed on 4 Nov.
- **Whole GPUs allocated per job.** No co-tenancy, and no interruption by other users.
- **Most of the work is independent short runs.** About 75 % of the T1 GPU-hours are audits (R1-BX-REVISIONS (f)), which pack naturally into a few long jobs.

## 3. Job types

All jobs are generated from one manifest by a submit tool (§5), never written by hand.

| Job | Partition, resources, time | What it runs | Resume |
|---|---|---|---|
| **J0 setup** | `dev-cpu` (1 h), then one `dev-gpu-h100` job (1 h) | Create the venv under `PROJECT` from pinned wheels; build llama.cpp `620d222` for sm_90 inside the GPU job; record versions and sha256 | Re-runnable |
| **J1 smoke** | `dev-gpu-h100`, 1 GPU, ≤ 1 h | One fixed-step run per ported T1 node with a stub manager; llama-server load probe of the main proposer's GGUF | — |
| **J2 census** (G.0 cost, G.1b noise floor) | `gpu-h100`, 1 node × 4 GPUs, ≤ 12 h | For each node, the declared representative edits × seeds 8001–8010, plus a concurrency sweep (1, 2, 4 runs per GPU) to measure runs per GPU | Per-run result files; skips done runs |
| **J3 campaigns** (G.4 pilot, G.5 sweep 2 T1) | `gpu-h100`, 1 node × 4 GPUs, `--time` ≤ 47 h and ending before the downtime | GPU 0 hosts llama-server for the main proposer (thinking off, `cache_prompt: false`, port derived from `SLURM_JOB_ID`, bound to 127.0.0.1). Task runs go into k slots per GPU on GPUs 0–3 (k from J2). The collector runs with `--deadline` = job time − 45 min | Per campaign root, as sweep 1. An interrupted root is re-run whole |
| **J4 audits** | `gpu-h100`, 1 node × 4 GPUs, ≤ 24 h each; the plan split into S shards, one job per shard | The audit plan (candidate and incumbent on the K seeds), k runs per GPU | Per-shard run cache (as `r1/c3/audit.py` `RunCache`); deadline then exit; re-submitted until the shard is done |
| **J5 merge** | `dev-cpu` or `cpu`, ≤ 1 h | Merge shard caches, check for duplicates and missing runs, build the T1 label table per Track G | — |

**Pairing rule.** For each audited proposal, the candidate and its incumbent run on all K seeds inside the same job, on H100. Pairs are never split across jobs.

**Packing.** One job uses one node (4 GPUs). Jobs per wave: J2 about 1–3, J3 about 2–4, J4 about S = 4–8. This stays far below the 100-job limit.

## 4. Who submits: the AI-agent rule

The migration page prohibits "interactive AI agent usage on login nodes". The operator agent runs on the Mac and acts through SSH, so commands it issues would execute on the login node. Until the centre answers, the proposal is:

1. **The author submits.** Each wave is two or three commands that the author runs on the login node: `hk2_submit.py --manifest <m> --dry-run`, then `hk2_submit.py --manifest <m>`. The tool writes every job script, checks the rules in §5 and prints the job ids.
2. **Status and copy-back are also done by the author**, with `hk2_status.py`, which polls at most once a minute, and an `rsync` of the output tree to the Mac. The operator then analyses the copied files.
3. **The author asks NHR@KIT support** whether an AI agent may (a) run `sbatch`, `squeue` and `rsync` through SSH from outside, or (b) run as a dispatcher in the `agent` partition. If they allow (a) or (b), the operator runbook gets a HoreKa section, and only then.

## 5. Code changes (Mac agent; draft, for review)

All of these live in the paper repo except the provider bits already in the harness. Each change is tested against fake Slurm environment variables and a fake llama-server.

1. **`r1/scripts/hk2/hk2_submit.py`** generates `#SBATCH` scripts from a manifest. It refuses:
   - a missing `--partition` or `--time`;
   - any job whose start plus `--time` reaches **2026-11-23 00:00 Europe/Berlin** (or a later downtime listed in the manifest);
   - more than 90 jobs outstanding;
   - a dev partition used for production.

   It records the manifest sha256 in each job script.
2. **`hk2_status.py`** prints `squeue` and `sacct` at most once every 60 s.
3. **A `slurm` host mode** in `r1/scripts/c3_label_sweep.py` and the collector:
   - GPUs come from Slurm's `CUDA_VISIBLE_DEVICES`;
   - the `gpu_uuid` occupancy wait, the co-tenancy margin check and the Paper A check are skipped (whole GPUs, not Ada);
   - provenance records `SLURM_JOB_ID`, the node name, GPU UUIDs from `nvidia-smi`, the driver, CUDA and the module list;
   - phase commits are local (no push from compute nodes).
4. **A GPU slot allocator** for task runs, used by the collector and `r1/c3/audit.py`. Each worker process gets `CUDA_VISIBLE_DEVICES=<one GPU>`, with k workers per GPU (`--gpu-slots k`). The CPU-node path stays unchanged and byte-identical (tested).
5. **Audit sharding:**
   - `audit.py --shard i/S` takes a deterministic slice of the plan, keeping each candidate–incumbent pair whole;
   - each shard has its own cache file, so no file locking is needed on GPFS;
   - `audit.py merge` combines the shards and refuses duplicates or missing runs.
6. **Staging tool**, run on the login node: downloads datasets, GGUFs and pinned wheels into `PROJECT`, verifies the sha256s and writes a staging manifest. Its size must be light enough for the login node; it fetches files and does no computation.
7. **Templates for J0–J5.**

## 6. Before any plan depends on HoreKa (author, read-only commands)

1. `sacctmgr show associations user=$USER -n -P format=Account`: the project account. Also check the project's remaining GPU-hours.
2. `echo $PROJECT; df -h $PROJECT; ws_list` *(if workspaces are used)*: the storage location and quota.
3. `module avail 2>&1 | grep -i -E 'cuda|python|gcc'`: the EasyBuild names to pin.
4. Inside a `dev-gpu-h100` job: `nvidia-smi` (H100 memory and driver); `curl -sI https://huggingface.co` (internet from compute nodes); `df -h /tmp $TMPDIR` (node-local scratch).
5. The question to NHR@KIT support in §4.

## 7. Schedule (if adopted; estimates)

| When | What |
|---|---|
| Now – 15 Nov | §6 checks; J0 setup; code §5 with review; J1 smoke on the first ported T1 nodes |
| 15 – 22 Nov | J2 census on H100, which gives the noise floors for the T1 table; J3 pilot (G.4) on 2–3 nodes; if time allows, a first J3 + J4 wave for the nodes already ported. **Copy everything out by 22 Nov** |
| 23 Nov – 4 Dec | Downtime: nothing runs. Porting and the Mac-side work continue |
| From 5 Dec | Remaining J3 + J4 waves; J5 merge; B.7. B.7 lands around 10–12 Dec unless the first wave covered enough nodes (the H1 decision is still pending) |

**GPU-hours.** The T1 estimate of about 400 GPU-h assumed 2-minute runs on a 4090-class card. On H100 with k runs per GPU, the wall time is roughly 400 / (GPUs held × speed-up × k). For example, 8 GPUs give about 2 days at a speed-up × k of about 3. This is an estimate, replaced by J2's measurements.

## 8. What stays elsewhere

- Track X (TASL-2, R1-EXAM-HOST);
- Track S (host-pinned identity, S0.1);
- B.2 sweep-1 audits (the replay must use the sweep's own environment on deepthought);
- Track P (TASL-7).

D.1 fold retraining and the T2 closed loop (D.3) may follow on HoreKa 2 later, by separate rows.

## 9. Open for the author

1. Move the T1 tier (census, noise floors, proposer, campaigns, audits) to HoreKa 2 H100, with Ada as fallback?
2. The downtime plan: a first wave before 22 Nov, the rest from 5 Dec; and the B.7 date (H1).
3. Ask NHR@KIT about AI-agent use (§4); until then the author submits.
4. The project account and its GPU-hour budget.
