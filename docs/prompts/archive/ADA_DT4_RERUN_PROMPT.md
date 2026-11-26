# Prompt: run and monitor the DT4 rerun on Ada (13 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to an agent that runs on the author's Mac and can reach Ada over SSH.*

---

You are the implementation agent for Paper B, route R1. Your job: push the prepared commits, launch the fresh DT4 attempt on Ada, monitor it to completion or STOP, verify the result, and report to the author. You do not change the experiment design, the code or the plan.

## Context (read before acting)

- Repository on the Mac: `~/Documents/agent_paper_B` (branch `main`, remote `origin` = `github.com/dowlingwong/Agent_paper_B`).
- Ada: SSH alias `experiment_zhixu` (hostname `ucrtasl`, 8 × RTX 6000 Ada 48 GB, shared with other users).
- Read first: `docs/r1/PLAN.md` §10, the two rows dated 13 Oct (**R1-COMPUTE (GPU co-tenancy, 13 Oct)** and **R1-COMPUTE (DT4 rerun, 13 Oct)**), and the newest three entries of `docs/r1/STATUS.md`.
- What DT4 is: E1b with the pinned LLM manager `qwen2.5-coder:7b` (digest `dae161e2…f4364`) on `digits_mlp` and `openml_ionosphere`, 6 instances each, W = 20 worker runs, E2 points 4/8/12, continue vs verify (r = 2), 2 repetitions, 6 audit seeds, `"fixed"` split. Label PILOT. DT1–DT3 are done and are never repeated.
- The rule that changed: a GPU may be shared with other users' processes when its free memory is at least 5,304 MiB (model) + 2,048 MiB (margin). Latency is descriptive only. The runner enforces this itself (`check_gpu`, `assert_full_offload` in `r1/scripts/deepthought_batch1_resume.py`).
- Entrypoints: `r1/scripts/ada_dt4_rerun_launch.sh` (run on Ada; clones origin/main into a new batch directory under `/data1/dowling/tmp/`, starts tmux session `r1_dt4_rerun`) → `r1/scripts/ada_rerun_dt4.py` (preconditions, card selection, Ollama with `OLLAMA_KEEP_ALIVE=-1`, offload checks, then `run_dt4`, then `finish`, which writes and pushes a STATUS entry).
- The interrupted attempt `results/r1/pilot/E1b_20261013T090510Z` stays as it is. Never resume, analyse or delete it.

## Hard rules

1. **Shared machine.** Never stop, renice or otherwise disturb other users' processes or tmux sessions. Use one GPU. Only stop processes that this batch started, and only under rule 4.
2. **No design changes.** Do not edit code, PLAN, RUNBOOK, the model, nodes, seeds, budget or analysis. Do not start a second Ollama instance. No LLM runs on the Mac.
3. **No retries.** If the runner STOPs, a collection fails, or a precondition fails, preserve everything and report. Do not relaunch, resume or patch without a new author decision. A precondition `SystemExit` before the claim is not a STOP of the experiment; report it, but do not edit files in the previous batch to get past it.
4. **When to intervene yourself:** only if (a) the runner process is gone but `batch_state.json` has no `finished_utc`, or (b) the runner is alive but its log and the collection have made no progress for 60 minutes. Then stop only our tmux sessions `r1_dt4_rerun` and `r1_ollama_resume_20261012`, keep every file, and report. Slowness from sharing a card is not a reason to intervene.
5. **Git.** Do not push anything to `origin/main` from the Mac while DT4 is running; the runner pushes its own commits from Ada at the end. Never force-push or rewrite history. If the runner's final push is rejected as non-fast-forward, you may run `git pull --rebase` and `git push` in the batch clone on Ada, without changing any content, and say so.
6. **Honesty.** Everything is PILOT or ENGINEERING_ONLY. Report a STOP as a STOP. Label your own work as AI-assisted.

## Steps

### 0. Push the prepared commits (Mac)

```sh
cd ~/Documents/agent_paper_B
git status --short          # must be empty
git log --oneline -5        # expect, newest first: this prompt's commit, 409d43d, 8358a89, bdf1e5f, a570423
git push origin main
git ls-remote origin refs/heads/main   # must equal: git rev-parse HEAD
```

If the tree is not clean or the history differs, stop and report.

### 1. Preflight on Ada (read-only)

```sh
ssh experiment_zhixu 'hostname -s; tmux ls 2>&1; ss -ltn | grep 11434 || echo port-free;
  nvidia-smi --query-gpu=index,uuid,memory.free,memory.used,utilization.gpu --format=csv;
  ls /data1/dowling/tmp/ | grep -E "r1_(batch1|DT4)"; git ls-remote git@github.com:dowlingwong/Agent_paper_B.git refs/heads/main'
```

Check: the hostname is `ucrtasl`; no tmux sessions `r1_dt4_rerun` or `r1_ollama_resume_20261012`; port 11434 is free; the remote head equals the Mac head; GitHub access works from Ada. Note which cards have ≥ 7,352 MiB free. No card qualifying is not an error, because the runner waits and re-checks every 60 s.

### 2. Launch

```sh
ssh experiment_zhixu 'bash -s' < ~/Documents/agent_paper_B/r1/scripts/ada_dt4_rerun_launch.sh
```

Record the printed batch directory `$B`. Within 2 minutes, confirm that `tmux ls` shows `r1_dt4_rerun` and that `$B/runner.log` exists.

### 3. Monitor until the runner finishes

Every 10 minutes, run read-only checks over SSH:

- `tail -n 20 $B/runner.log`;
- `$B/batch_state.json`: the `stop_reason` and `finished_utc` keys, and `steps.DT4`;
- the last line of `$B/gpu_census.jsonl`: `selected_free_mib`, `need_free_mib`, `other_owners_on_selected`;
- `curl -s 127.0.0.1:11434/api/ps` on Ada: `size_vram` must equal `size`;
- progress: the number of files in `$B/agent_paper_B/results/r1/pilot/E1b_<new stamp>/leaves/` and `audits/`, and the last session in its `manifest.json`;
- `tmux ls` (our two sessions only).

Keep a short monitoring log in your own notes: time, phase, leaves and audits, free MiB, co-tenants. Expected leaves: 144 (2 nodes × 6 instances × 3 points × 2 actions × 2 reps). The interrupted attempt reached 48 leaves in about 3.5 minutes, so expect roughly 1–2 hours, more on a busy card.

The runner STOPs by itself on: insufficient free memory, a partial or CPU load of the model, digest mismatch, collection failures, missing continue/verify leaves, parse failures above 20 %, a report-path collision, or a non-reproducible analysis. That is correct behaviour; report it under rule 3.

### 4. Verify the result (Mac, after the runner finishes)

```sh
cd ~/Documents/agent_paper_B && git pull --ff-only
```

Check:

- STATUS has a new "Remote batch 1: completed" (or "stopped") entry from the runner;
- on success: `results/r1/pilot/E1b_<stamp>/` with `collection_checks.json` (0 collection failures, LLM calls > 0, parse failures ≤ 20 %), `analysis.json`, `docs/r1/reports/HEADROOM_PILOT_<date>_llm.md` and `..._llm_tables.md`, and `steps.DT4.committed_analysis_sha256 == regenerated_analysis_sha256` in `$B/batch_state.json`;
- `make r1-test` still passes (needs `AR_HARNESS_ROOT=~/Documents/autoresearch_harness`).

Do not interpret beyond the report. The E2 decisions belong to the author.

### 5. Report to the author

A short message with:

1. the outcome (completed or STOP + reason) and the commits pushed by the runner;
2. batch directory, GPU UUID, the co-tenants seen on that card, and the minimum free MiB observed;
3. the offload evidence (`size_vram` vs `size`) at load and after collection;
4. counts: leaves, audits, LLM calls, parse failures, wall time;
5. the headroom table from the report, LLM vs scripted, both nodes and ALL (naive and leaf-split brackets);
6. anything you did under rules 4–5, and any deviation.

If the runner has already pushed a STATUS entry, do not write a second one. Add a STATUS entry yourself only to record an intervention under rule 4 or a failure before the runner started.
