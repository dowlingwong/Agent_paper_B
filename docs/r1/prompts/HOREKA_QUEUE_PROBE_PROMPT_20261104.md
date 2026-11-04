# Prompt — HoreKa 2 queue-latency probe (4 Nov 2026, revision 1)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.** The scan `reports/HOREKA_SCAN_20261104.md` found that `sbatch --test-only` gives `gpu-h100` start estimates about 8 days out, but backfill started a short probe 5.5 h earlier than its estimate. The author (4 Nov, 17:12): "批准第 1 步的排队实测", "11月12开始太晚了". This probe measures how long jobs of each shape **actually** wait on `gpu-h100` and `gpu-h200`. Each job runs for a few seconds, so the GPU-time cost is negligible. Paste everything below the line into the agent that ran the scan, or into another Claude Code agent on the author's Mac that can `ssh hk2`. It authorizes nothing beyond what is described here.

---

You are a **read-only probing agent** for HoreKa 2 (NHR@KIT). The author is Dowling Wong. You ran the scan before, or you have its prompt at hand.

**What you reuse.** Follow `~/Documents/agent_paper_B/.claude-worktrees/_snapshots/HOREKA_SCAN_PROMPT_20261104.md` (revision 5.6) exactly, with three changes:

1. **A new folder.** Replace every occurrence of `horeka_scan_20261104` with `horeka_queue_20261104` in every command, including the two wrapper scripts of step 0. This includes `~/r1_scan_20261104/`, which becomes `~/r1_queue_20261104/`. Never write into the scan folder.
2. **§3 and §4 are replaced** by §A and §B below. Keep §0, §1 (steps 0–5, gates, teardown), §5 and §7. Keep the rules of §2, except rule 2 ("exactly one short job"), which is replaced by §A.
3. **The report** is `"$S/HOREKA_QUEUE_20261104.md"`, as described in §C.
4. **Gate 2 as the scan found it.** On this account `scontrol show node` is refused (`PrivateData` includes `nodes`). So Gate 2 passes when both of these hold: `job_env` equals the session job id from `session.log`, and `squeue -h -u "$USER" -p agent -t R` lists that job id as running on the same host. This is how the scan passed it (scan report, deviation 3). Any other failure of Gate 2 is still a STOP.

Report to the author in **Chinese**, short and concrete. Write the report file in **English**.

## §A. The jobs (replaces scan rule 2 and §4)

**Exactly 10 jobs, submitted once each. Never resubmit, never add a job, never change a shape.**

| Name | Partition | Resources | `--time` |
|---|---|---|---|
| `r1q_h100_g1_1h` | `gpu-h100` | `--gres=gpu:1 -c 32 --mem=180G` | `01:00:00` |
| `r1q_h100_g1_4h` | `gpu-h100` | `--gres=gpu:1 -c 32 --mem=180G` | `04:00:00` |
| `r1q_h100_g1_12h` | `gpu-h100` | `--gres=gpu:1 -c 32 --mem=180G` | `12:00:00` |
| `r1q_h100_x4_4h` | `gpu-h100` | `--gres=gpu:4 --exclusive` | `04:00:00` |
| `r1q_h100_x4_12h` | `gpu-h100` | `--gres=gpu:4 --exclusive` | `12:00:00` |
| `r1q_h200_g1_1h` | `gpu-h200` | `--gres=gpu:1 -c 32 --mem=180G` | `01:00:00` |
| `r1q_h200_g1_4h` | `gpu-h200` | `--gres=gpu:1 -c 32 --mem=180G` | `04:00:00` |
| `r1q_h200_g1_12h` | `gpu-h200` | `--gres=gpu:1 -c 32 --mem=180G` | `12:00:00` |
| `r1q_h200_x4_4h` | `gpu-h200` | `--gres=gpu:4 --exclusive` | `04:00:00` |
| `r1q_h200_x4_12h` | `gpu-h200` | `--gres=gpu:4 --exclusive` | `12:00:00` |

Every job also has: `-A hk-project-p0027888 -N 1 -n 1 --deadline=now+3days -J <name> -o ~/r1_queue_20261104/%x-%j.out`. The `--deadline` makes any job that is still pending after 3 days cancel itself, so nothing is left behind.

**The job script** is the same for all 10. Write it to `"$S/q.sh"`:

```bash
#!/bin/bash
echo "start $(date -Is) host=$(hostname) job=$SLURM_JOB_ID part=$SLURM_JOB_PARTITION job_gpus=$SLURM_JOB_GPUS cvd=$CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=index,name,memory.total,uuid,driver_version,compute_cap --format=csv,noheader
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
echo "end $(date -Is)"
```

**Order, all on the compute node through `"$S/nodessh"`:**

1. **Partition facts first (read-only):** `scontrol show partition gpu-h200`, `scontrol show partition gpu-h200-8`, `sinfo_t_idle`. Save them as `"$S/partitions.txt"`.
2. **Estimates:** for each of the 10 shapes, `sbatch --test-only <the same options> --wrap true`. Save all output to `"$S/testonly.txt"`. If `gpu-h200` is refused (no access, or an account error), record the exact message, and submit only the 5 `gpu-h100` jobs.
3. **Copy and submit in one call:** create `~/r1_queue_20261104/`, copy `q.sh` there, and submit the jobs one after another with `sbatch --parsable`. Write `<name> <jobid>` lines to `~/r1_queue_20261104/jobs.txt`, and fetch that file to `"$S/jobs.txt"`. If any submission fails, record the message and submit no replacement.
4. **Status checks:** `squeue -u "$USER" -h -o '%i %j %T %S %R'`, at most once every **5 minutes**, at most 9 times. Fit them into the session's remaining time minus 10 minutes (step 4 of the scan prompt). Save every result with a UTC timestamp in `"$S/status_checks.txt"`.
5. **Final record, one call:** `sacct -X -j <comma-separated job ids> -n -P -o JobName,JobID,Partition,State,Submit,Start,End,NodeList,AllocTRES` → `"$S/sacct.txt"`, plus `cat ~/r1_queue_20261104/*.out` → `"$S/job_outputs.txt"`.
6. **Leave pending jobs in the queue. Do not cancel them.** They will run for a few seconds whenever they start, or cancel themselves after 3 days. Never cancel anything except the session job in step 5 of the scan prompt.

## §B. Rules that change

- Compute-node calls: as in the scan prompt's rule 1, but with §A's steps instead of the scan's query script and probe: one partition call, one test-only call, one copy-and-submit call, at most 9 status checks, one final call, and the session teardown.
- Only these files are created on HoreKa: `~/r1_queue_20261104/` with `q.sh`, `jobs.txt` and the job outputs.
- STOP (after the scan prompt's step 5) if:
  - a **policy message** appears, as defined in the scan prompt's §7;
  - any job runs for **more than 60 seconds** (it should take about 2 s). Do not cancel it; report its id;
  - more than 10 jobs of yours appear in `squeue`, apart from the session job and any job the author started himself.

## §C. Report

Write `"$S/HOREKA_QUEUE_20261104.md"`. Start it with the author's words: "批准第 1 步的排队实测". Then:

1. **The setup**, as in the scan report: session job id, node, tunnel, gates and teardown, briefly.
2. **The partition facts** for `gpu-h200` and `gpu-h200-8`: nodes, GPUs per node, GPU memory if it is shown, MaxTime, AllowAccounts and QoS.
3. **One table**, one row per job: name, test-only estimate, submit time, start time (or "pending at <time>"), wait in minutes, node, and the GPU name and memory from the job's output.
4. **Processes on the GPU** each job saw (for example Xorg and its memory).
5. **What the author should read later.** Give him one line he can run himself to read the final state tomorrow:
   `ssh hk2 "sacct -X -u ka_ir7683 -S 2026-11-04 -n -P -o JobName,JobID,Partition,State,Submit,Start,End | grep r1q_"`
6. Deviations from this prompt, if any, with evidence.

At the end of your message to the author, remind him that his master connection stays open for up to 8 hours after its last use, and that he can close it with `ssh -O exit hk2`.
