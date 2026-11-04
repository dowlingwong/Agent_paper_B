# Draft — running Track G T1 work on HoreKa 2 by Slurm job submission (4 Nov 2026, revision 2)

**Status.** AI-assisted draft (Claude, chat session), written at the author's request ("怎么把t1改写成horeka compatible的提交任务"). It is **not adopted** and authorizes nothing. Revision 2 addresses the independent review `reviews/HOREKA_1GC_REVIEW_20261104.md` (not accepted: 7 MAJOR, 11 MINOR).

**Sources.** The author's cheat sheet "HoreKa / HoreKa 2 — Slurm Job Submission" (chat attachment, 4 Nov; it is the only source for the host name, the user name and the downtime dates). NHR@KIT documentation, read 4 Nov: <https://docs.nhr.kit.edu/usage/slurm/> and <https://docs.nhr.kit.edu/get-started/migration/>. Facts not in these sources are marked *(to check)*.

## 0. What adopting this would change

PLAN currently places the T1 label runs on Ada and the census on Ada. Moving T1 to HoreKa 2 needs an author row that amends:
- R1-BX-PROPOSED-CONFIRM (the REVISIONS (f) and E1 bullets: T1 label runs on Ada; the proposer on deepthought or a 4090);
- R1-ADA-CENSUS (census and noise floors on Ada);
- R1-BX-REVISIONS (f) (hosts);
- R1-BX-D14 ("noise floors and liveness start on Ada");
- RUNBOOK G.0's GPU-model list, and "Ada first" in RUNBOOK G.0/G.1b, TRACK_G and OPERATOR O0/O8.

Two further points:
- A proposer served on H100 is a **new serving configuration** for the T1 tier. It needs a qualification like O5 (full offload, within-server identity 1.000 at `cache_prompt: false`, a projection), and it is listed among the stack differences.
- "Ada as fallback" can only mean that **the whole T1 label table** moves to Ada. One GPU model per table (R1-BX-D5) forbids splitting it.

## 1. Facts that shape the design

| Fact | Source | Consequence |
|---|---|---|
| H100 (Teal) and H200 (Ruby) are on HoreKa 2, `hk2-x86.scc.kit.edu`, user `ka_ir7683` | cheat sheet | — |
| `gpu-h100`: 4 × H100 per node, maximum 2 days; access policy **"Shared"**; `--exclusive` reserves a whole node | slurm page | Jobs use `--exclusive`. Exclusive allocation is *(to check)*; the jobs keep a light occupancy check |
| `--partition` and `--time` are mandatory | cheat sheet | Every job script sets both |
| Downtime 23 Nov – 4 Dec 2026: no data access, no jobs | cheat sheet | The exact start hour, whether 4 Dec is included, and what happens to pending jobs are *(to check)* |
| Max 100 submitted jobs per user (300 per group) | cheat sheet; slurm page | Pack many runs per job |
| Dev partitions: one job per user; not for production | cheat sheet; slurm page | Dev partitions only for setup and smoke tests |
| `squeue` polled faster than every 30 s gets jobs killed | cheat sheet | Status helper polls once a minute at most |
| "Compute intensive tasks must not run on login nodes" | slurm page | Builds, hashing of large files and tests run in jobs |
| **"Interactive AI agent usage on login nodes is prohibited"**; an `agent` partition (1 core, ≤ 3 days) exists | migration page; slurm page | The SSH operator does not act on HoreKa until NHR@KIT confirms what is allowed (§4) |
| `$HOME` 50 GB / 2 M inodes; a `PROJECT` directory per compute project | migration page | Data, venvs, GGUFs and outputs under `PROJECT` |
| Modules move to EasyBuild with new names | migration page | Names discovered and pinned per template |
| Resources are tied to the compute project and accounted by Slurm | slurm page | The remaining GPU-hours are checked first (§6) |
| HoreKa 2 CPU nodes are shared: set `--ntasks`, `--cpus-per-task`, `--mem` | cheat sheet; migration page | Set in every template, GPU jobs included |
| Internet from compute nodes, node-local scratch, H100 memory, the CUDA arch flag (`sm_90` expected), the file-system type | not stated | *(to check)* |

## 2. Why HoreKa 2 could suit T1

- **One GPU model (H100) for the whole T1 table.** This meets R1-BX-D5 without mixing GPU models.
- **Whole nodes by `--exclusive`.** If confirmed *(to check)*, this removes co-tenancy noise.
- **The work splits well.** About three quarters of the T1 GPU-hours are audits (30 of 40 GPU-h per node at K = 6; R1-BX-REVISIONS (f)), and audits are independent pairs of runs.

## 3. Job types

All jobs are generated from one manifest by the submit tool (§5).

| Job | Partition, resources, time | What it runs | Resume unit |
|---|---|---|---|
| **J0 setup** | `dev-cpu` (≤ 1 h), then `dev-gpu-h100` (≤ 1 h) | Venv under `PROJECT` from pinned wheels; llama.cpp `620d222` built for the H100 arch *(to check)*; version and sha256 records | Re-runnable |
| **J0b hashing** | `cpu`, a few cores, ≤ 2 h | sha256 of the staged datasets and GGUFs against the staging manifest | Re-runnable |
| **J1 smoke** | `dev-gpu-h100`, 1 GPU, ≤ 1 h | One fixed-step run per ported T1 node with a stub manager; llama-server load probe of the main proposer | — |
| **J1b proposer qualification** | `gpu-h100`, 1 GPU, ≤ 4 h | O5-style: full offload, 50 prompts × 3 at `cache_prompt: false`, identity, latency, projection (§0) | — |
| **J2 census** (G.0 cost, G.1b noise floors) | `gpu-h100 --exclusive`, 1 node, ≤ 12 h | Declared representative edits × seeds 8001–8010 plus the baseline; a concurrency sweep (1, 2, 4 runs per GPU) | Per run |
| **J3 campaigns** (G.4 pilot, G.5 sweep 2 T1) | `gpu-h100 --exclusive`, 1 node, `--time` ≤ 47 h | **GPU 0:** llama-server for the main proposer (thinking off, `cache_prompt: false`, port from `SLURM_JOB_ID`, bound to 127.0.0.1), with no task runs on it. **GPUs 1–3:** task runs, k per GPU | Per campaign root (as sweep 1); an interrupted root is re-run whole |
| **J4 audits** | `gpu-h100 --exclusive`, 1 node, ≤ 24 h each; the plan split into S shards | Candidate–incumbent pairs on the K seeds, k runs per GPU | **Per pair**: a pair's runs are written only when all of them have finished. A pair cut off by the deadline is discarded and re-run whole in the next job |
| **J5 merge** | `cpu`, ≤ 1 h | Merge shard results; refuse duplicates or missing pairs; build the T1 label table **from label seeds only** (7001–7003 at K = 6, 7001–7005 at K = 10). Evaluation seeds 7006–7010 go only into the evaluation columns | — |

**Rules for every job.**
- **Same k in the floor and the labels.** The label runs use the same runs-per-GPU k and the same GPU placement as the noise floor that sets σ̂ for that node. If k changes, the floor is re-measured.
- **Pairing.** A candidate and its incumbent run all K seeds on H100 within one job. Pairs are never split, and the resume unit is the pair.
- **Templates set** `--account`, `--partition`, `--time`, `--ntasks`, `--cpus-per-task`, `--mem`, `--gres=gpu:4`, `--exclusive` *(to check)*, and Slurm's `--deadline`.

**Packing.** One job uses one node. Per wave: J2 1–3 jobs, J3 2–4, J4 S = 4–8 — far below 100.

## 4. Who acts on HoreKa: the AI-agent rule

The migration page prohibits "interactive AI agent usage on login nodes". The operator agent works through SSH, so its commands would run on the login node. Until NHR@KIT answers:
1. **The author** runs the submit tool (`--dry-run`, then the real submission), the status helper, the staging download, and the `rsync` copy-back. The operator only analyses files the author copies back.
2. **The question to NHR@KIT support**, in three parts:
   - (a) may an AI agent outside the cluster run `sbatch`, `squeue` and `rsync` through SSH?
   - (b) may it run as a dispatcher in the `agent` partition?
   - (c) does an LLM-driven loop running inside a GPU batch job (the campaign proposer) count as an "AI agent workload" that belongs in the `agent` partition?
3. Only after a positive answer does the operator runbook get a HoreKa section.

## 5. Code changes (Mac agent; for review)

1. **`r1/scripts/hk2/hk2_submit.py`** generates the job scripts from a manifest and records the manifest sha256 in each. Its downtime guard has three layers:
   - **at submission**, it refuses a job if now + `--time` reaches the downtime start;
   - **every template** sets Slurm's `--deadline` to the downtime start, so a job still pending then is never started;
   - **inside each job**, the runner checks the clock and stops cleanly before the downtime starts.

   It also refuses a missing partition or time, more than 90 jobs outstanding, and any production job on a dev partition.
2. **`hk2_status.py`** queries at most once every 60 s.
3. **`slurm` host mode** in `c3_label_sweep.py` and the collector:
   - GPUs come from Slurm;
   - the Ada-only Paper A check is skipped;
   - the `gpu_uuid` occupancy wait is replaced by a light check at job start: no foreign compute process on the allocated GPUs, else exit;
   - provenance records `SLURM_JOB_ID`, the node, GPU UUIDs, driver, CUDA and modules;
   - commits are local only.
4. **GPU slot allocator** for task runs: one GPU per worker, k workers per GPU, GPU 0 excluded in J3. The CPU-node path stays byte-identical (tested).
5. **Pair-unit audit sharding:** `audit.py --shard i/S` takes whole pairs; a pair is committed only when complete; `audit.py merge` checks for duplicates and missing pairs.
6. **Staging:**
   - `hk2_stage.py`, **run by the author** on the login node, only downloads files listed in a manifest;
   - hashing runs in J0b, not on the login node.
7. **Templates J0–J5**, and tests against fake Slurm variables and a fake llama-server.

## 6. Checks before any plan depends on HoreKa (author, read-only)

1. **Account:** `sacctmgr show associations user=$USER -n -P format=Account`, and the project's remaining GPU-hours.
2. **Storage:** `echo $PROJECT; df -h $PROJECT`.
3. **Modules:** `module avail 2>&1 | grep -i -E 'cuda|python|gcc'`.
4. **Inside a `dev-gpu-h100` job:**
   - `nvidia-smi` — H100 memory and driver;
   - `curl -sI https://huggingface.co` — internet from the compute node;
   - `df -h /tmp $TMPDIR` — local scratch;
   - `scontrol show partition gpu-h100` — whether `--exclusive` is honoured.
5. **The downtime details:** the exact start hour, and what happens to pending jobs.
6. **The NHR@KIT question** in §4.

## 7. Schedule (if adopted; estimates, with gates)

| When | What | Gates |
|---|---|---|
| Now – 15 Nov | §6 checks; J0, J0b; code §5 reviewed; J1 smoke on the first ported nodes | Author's HoreKa row; R1-BX-PORTING-CONFIRM; M10 shared pieces |
| 15 – 22 Nov | J1b proposer qualification; J2 census (the T1 noise floors on H100); J3 pilot (G.4) on 2–3 nodes; if possible, a first J3 + J4 wave. **Copy everything out before the downtime** | X.7 (the pick); G.3 row; M10 diff support pinned; the K row (R1-BX-D3); the G.5 authorization note for any EVIDENCE wave |
| 23 Nov – 4 Dec | Downtime: no jobs. Porting and Mac-side work continue | — |
| From 5 Dec | Remaining J3 + J4 waves; J5; B.7 | R1-BX-D8-CONFIRM before any label table is analysed |

**GPU-hours (estimate).** After the 1GC change about 8 T1 candidates remain: autoresearch (1), MLGym (about 4) and MLAgentBench (about 3). R1-BX-REVISIONS (f) gives about 40 GPU-h per node at 2-minute runs and K = 6, and about 60 at K = 10. That totals about **320 GPU-h at K = 6** and **480 at K = 10**. Wall time ≈ total / (GPUs held × H100 speed-up × effective k). For example, 8 GPUs with speed-up × k ≈ 3 gives 320 / 24 ≈ 13 h, or 480 / 24 = 20 h. J3 uses only 3 of its 4 GPUs for task runs. J2 replaces these guesses with measurements.

## 8. What stays elsewhere

- Track X (TASL-2, R1-EXAM-HOST);
- Track S (host-pinned identity, S0.1);
- B.2 sweep-1 audits (replay in the sweep's own environment on deepthought);
- Track P (TASL-7).

D.1 fold retraining and the D.3 T2 closed loop may follow on HoreKa 2 later, by separate rows.

## 9. Open for the author

1. Move the whole T1 tier to HoreKa 2 H100 (census, floors, proposer, campaigns, audits), with Ada as a whole-table fallback (§0)?
2. The downtime plan and the B.7 date (H1, pending).
3. The NHR@KIT question (§4); until it is answered, the author submits and copies.
4. The project account and its GPU-hour budget.
