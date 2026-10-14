# Prompt: run and monitor the LLM E1b rerun-2 on Ada (R1-E1B-RERUN2)

*Written by Claude (coordinating session) on 14 Oct 2026 at the author's request. Hand this whole file to an agent that runs on the author's Mac and reaches Ada as `experiment_zhixu`. **Use it only after batch 4 is complete** (Step 0 checks this).*

---

You are the implementation agent for Paper B, route R1. Your job:

1. launch the E1b rerun-2 on Ada with the entrypoints built in batch 4;
2. monitor it to completion or STOP;
3. verify the committed results;
4. report the numbers to the author.

You do not change the design, the code or the plan.

## What runs

This follows PLAN §10, row **R1-E1B-RERUN2**, gated by the revised **D28**. The runner `r1/scripts/ada_e1b_rerun2.py` executes these phases in order, and checkpoints each one:

1. preconditions;
2. LLM liveness (memory on) on `digits_mlp`, `tabular_mlp`, `openml_ionosphere`, `openml_breast_w`;
3. arm A: LLM, `append_only_summary`;
4. arm B: LLM, `none` (contrast);
5. arm C: scripted;
6. per-arm analysis, commit and regeneration check;
7. the cross-arm comparison report;
8. STATUS.

Each arm runs 18 instances per eligible node, W = 20, E2 points 4/8/12, continue vs verify (r = 2), 2 repetitions and 6 audit seeds. All outputs are PILOT or ENGINEERING_ONLY.

Fixed facts:

- pinned model `qwen2.5-coder:7b`, digest `dae161e2…f4364`, temperature 0.2, seeded per call (D26);
- model files at `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/ollama_models`, binary `/usr/local/bin/ollama`;
- GPU co-tenancy (PLAN §10, 13 Oct): a shared card is fine when its free memory is at least 5,304 + 2,048 MiB. Latency is descriptive only.

## Hard rules

1. **Shared machine.** Never stop or disturb other users' processes or sessions. Use one GPU. Stop only our own sessions, and only under rule 4.
2. **No design or code changes.** Do not edit code, PLAN, RUNBOOK, the model, nodes, seeds, budgets or analysis. No LLM runs on the Mac.
3. **No retries.** If the runner STOPs, preserve everything and report. A completed phase is never re-run. An interrupted phase is not resumed or relaunched without a new author decision. A failing node in the liveness phase is an expected outcome, not a STOP, unless fewer than 2 nodes pass.
4. **When you may intervene:** only if (a) the runner process is gone but `batch_state.json` has no `finished_utc`, or (b) neither the runner log nor the collection has made progress for 60 minutes. Then stop only our tmux sessions (`r1_e1b_rerun2` and our `r1_ollama_*` session), keep every file, and report. Slowness on a shared card is not a reason to intervene.
5. **Git.** While the runner is active, do not push to `origin/main` from the Mac; the runner commits from Ada. Never force-push or rewrite history. If a runner push is rejected as non-fast-forward, you may run `git pull --rebase && git push` in the batch clone without changing any content, and you must say so.
6. **No manual environment changes on Ada.** Do not install packages, edit git config, or patch files in a batch clone by hand. The launcher does all setup. If `--prepare` fails for an environmental reason, report it. Earlier batch directories (e.g. `…_20261014_nH08fo`) are evidence: leave them untouched and never resume them.
7. **Honesty.** Report a STOP as a STOP. Give numbers without interpretation beyond the report's readings template. Label your work as AI-assisted.

## Step 0: preconditions (Mac, read-only)

```sh
cd ~/Documents/agent_paper_B && git pull --ff-only && git status --short   # must be empty
```

Check each of the following. If any check fails, stop and report.

- `docs/r1/STATUS.md` has a batch-4 entry, and `docs/r1/reviews/BUILD_REVIEW_20261014b.md` has a "Resolution" section with no open MAJOR finding.
- STATUS has a batch-4c entry reporting a passing end-to-end desktop dry run (`results/r1/engineering/rerun2_dryrun_<UTC>/summary.json`), and `docs/r1/reviews/BUILD_REVIEW_20261014c.md` has a "Resolution" section with no open MAJOR finding.
- These files exist: `r1/scripts/ada_e1b_rerun2.py`, `r1/scripts/ada_e1b_rerun2_launch.sh`, `r1/scripts/HARNESS_PIN_RERUN2`, `r1/headroom/e1b_compare.py`.
- The `HARNESS_PIN_RERUN2` commit is on `origin/r1` of the harness (`git -C ~/Documents/autoresearch_harness fetch && git -C ~/Documents/autoresearch_harness branch -r --contains <pin>`).
- PLAN §10 contains the rows `R1-E1B-RERUN2`, `D28 (revised criterion 2)` and `R1-COMPUTE (GPU co-tenancy, 13 Oct)`.

## Step 1: preflight on Ada (read-only)

```sh
ssh experiment_zhixu 'hostname -s; tmux ls 2>&1; ss -ltn | grep 11434 || echo port-free;
  nvidia-smi --query-gpu=index,uuid,memory.free,memory.used,utilization.gpu --format=csv;
  nproc; df -h /data1 | tail -1;
  git ls-remote git@github.com:dowlingwong/Agent_paper_B.git refs/heads/main;
  git ls-remote git@github.com:dowlingwong/autoresearch_harness.git refs/heads/r1'
```

Check:

- the hostname is `ucrtasl`;
- none of our sessions exist;
- port 11434 is free;
- GitHub access works;
- there is enough disk space.

Note the CPU count and which cards currently qualify. If no card qualifies, that is not an error: the runner waits.

## Step 2: prepare, then start

Read the author's git identity from the Mac repository and pass it to the launcher. The launcher sets it repository-locally in the fresh clones. Do not set it any other way.

```sh
GN=$(git -C ~/Documents/agent_paper_B config user.name); GE=$(git -C ~/Documents/agent_paper_B config user.email)
ssh experiment_zhixu "R1_GIT_NAME='$GN' R1_GIT_EMAIL='$GE' bash -s -- --prepare" < ~/Documents/agent_paper_B/r1/scripts/ada_e1b_rerun2_launch.sh
```

Record the printed batch directory `$B`. Read `$B/prepare.json`, which holds the heads, the test numbers, any failure, the pytest version and the git identity and push dry-run checks. Then:

- If a failure lies outside the accepted environmental set (the known harness failures plus the Ada missing-`/bin/zsh` exception), stop and report.
- Otherwise:

  ```sh
  ssh experiment_zhixu "R1_GIT_NAME='$GN' R1_GIT_EMAIL='$GE' bash -s -- --start $B" < ~/Documents/agent_paper_B/r1/scripts/ada_e1b_rerun2_launch.sh
  ```

  Copy the launcher's one-line self-check summary. Within 2 minutes, confirm that the tmux session `r1_e1b_rerun2` is alive and that `$B/runner.log` exists. Copy the compute estimate the runner prints (leaves and expected LLM calls per arm).

## Step 3: monitor until the runner finishes

Every 15 minutes, read only (over SSH):

- `tail -n 20 $B/runner.log`;
- `$B/batch_state.json`: the current phase, completed phases, `stop_reason`, `finished_utc`;
- the last line of `$B/gpu_census.jsonl`: selected free MiB, need, and co-tenants;
- `curl -s 127.0.0.1:11434/api/ps` on Ada: `size_vram` must equal `size`;
- progress of the current arm: the counts in its run directory's `leaves/` and `audits/`, and the last session in its `manifest.json`;
- `tmux ls`: our sessions only.

Keep a short monitoring log in your notes (time, phase, leaves, free MiB, co-tenants). Do not post intermediate numbers as results.

Expected volume: with all 4 nodes eligible, about 864 leaves per arm (4 × 18 × 3 × 2 × 2), plus the roots. Use the runner's estimate for time; the LLM arms take several hours each.

## Step 4: verify (Mac, after the runner finishes)

```sh
cd ~/Documents/agent_paper_B && git pull --ff-only
```

Check:

1. STATUS has the runner's completed (or stopped) entry.
2. The liveness manifest `results/r1/engineering/liveness_llm_<UTC>/` exists, with per-node verdicts and `manager_kind: langgraph`, `memory_mode: append_only_summary`.
3. For each finished arm, the run directory has:
   - `collection_checks.json`: 0 collection failures, and parse failures ≤ 20 % for A and B;
   - `analysis.json` and the tables;
   - in `$B/batch_state.json`, matching committed and regenerated `analysis.json` hashes.
4. The comparison report and its JSON exist.
5. `make r1-test` passes (absolute `AR_HARNESS_ROOT`, venv interpreter).

## Step 5: report to the author

A short message with:

1. the outcome (completed, or STOP with its reason), and the commits pushed by the runner;
2. the batch directory, GPU UUID, co-tenants seen, minimum free MiB, the offload evidence at load and after each arm, and the wall time per phase;
3. the liveness table (per node: the three criteria, `novelty_source`, verdict) and the list of eligible nodes;
4. from the comparison report, per node and for ALL:
   - ρ per arm;
   - `always_verify − ρ` per arm, with CI;
   - the memory effect `(B − A)`, with CI;
   - naive and leaf-split headroom per arm;
   - the readings exactly as the template states them;
5. waste: the active-novelty fraction, inactive-key rejections, `config_seen_before` rate, LLM calls and parse failures per arm;
6. any deviation, and anything done under rules 3–5.

No interpretation beyond this. The E2 decisions belong to the author.
