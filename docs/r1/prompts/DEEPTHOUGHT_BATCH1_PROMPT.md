# Prompt — R1 deepthought batch 1 (LLM-backed steps)

Written 12 Oct 2026 by the coordinating session (Claude) at the author's request. Under R1-COMPUTE (PLAN §1, 12 Oct), no LLM runs on the Mac; this batch moves every LLM-backed step to deepthought.

**How to use:**
- Paste everything inside the fence into an agent session (Claude Code or Codex) running **on deepthought2.etp.kit.edu**, in a terminal under `/ceph/dwong`.
- Edit the AUTHOR DECISIONS block first, if needed.

```text
You are running "deepthought batch 1" of Paper B, route R1: noise-aware
control of governed autoresearch loops. You run on deepthought2
(deepthought2.etp.kit.edu), a shared server with many CPU cores and
4 x NVIDIA TITAN (12 GB each). Repositories live under /ceph/dwong.
Nothing you produce is evidence: every output is ENGINEERING_ONLY or PILOT,
so no authorization note is needed (RUNBOOK §1 rule 3).

READ FIRST, in this order, in /ceph/dwong/agent_paper_B:
- docs/r1/PLAN.md: §1 decisions, including R1-REFRAME, R1-INDEX,
  R1-GATE-FIRST and R1-COMPUTE; §10 decisions;
- docs/r1/RUNBOOK.md: §1 ground rules, §3 order and compute map;
- docs/r1/STATUS.md: the two 12 Oct entries;
- docs/r1/reports/HEADROOM_PILOT_20261012.md;
- docs/r1/reports/E2_STOP_MEMO_20261012.md.
Only PLAN, RUNBOOK and STATUS have authority. The archive has none.

AUTHOR DECISIONS (stated by the author by sending this prompt)
- D15 on deepthought: manager model qwen2.5-coder:7b served by Ollama, pinned
  by digest dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
  (Q4_K_M). [EDIT only if the author changes the model.]
- No API models in this batch. No model larger than 7B.
- The E2 STOP decisions (D18, D21, D23, the D4 amendment, the verify split
  policy) are NOT taken yet. Do not record any of them as decided. Do not
  build L11.

HARD RULES
1. Shared machine. Before using a GPU, run `nvidia-smi` and pick a card whose
   free memory is at least the model footprint plus 2 GiB; other users'
   processes on that card are allowed and logged (author decision of 13 Oct
   2026, PLAN §10, which replaced the earlier "no other user's process" rule;
   latency is descriptive only). Never kill or disturb other users' jobs. Use at
   most 2 cards unless all 4 are idle. Put long runs in tmux (or the site's
   batch system if interactive use is discouraged) and log to files.
2. Never force-push, rewrite pushed history, or delete ledgers or results.
   Do not delete or overwrite existing directories under /ceph/dwong; if a
   path is taken by something unexpected, clone next to it and say so.
3. One commit per logical step. End each commit message with:
     Co-Authored-By: <your model> <noreply@anthropic.com>   (or your agent's equivalent)
   Push after each step to the branch named below.
4. Default behaviour is sacred (BUILD_RUNBOOK §0). If you must change
   harness code, add a test that fails before and passes after, in its own
   commit, and report it. Otherwise only run code.
5. STOP and report instead of improvising when: the Ollama digest differs
   from the pinned one; a test that passed before now fails; no GPU is free
   for more than 1 h; or a step needs a decision that PLAN §10 does not record.
6. Write all files in English. Label every output directory PILOT or
   ENGINEERING_ONLY, exactly as the existing tools do.

REPOSITORIES AND EXPECTED COMMITS
- Paper B: GitHub dowlingwong/Agent_paper_B, branch main, at or after
  commit "Record deepthought batch 1 prompt" (see `git log`).
  Location: /ceph/dwong/agent_paper_B.
- Harness: GitHub dowlingwong/autoresearch_harness, branch r1, at or after
  4e8fd69 ("L14 review fixes ..."). Location: /ceph/dwong/autoresearch_harness.
  Note: that path may already hold an older rsync copy
  (scripts/sync_to_deepthought2.sh). If it is a git checkout, `git fetch`
  and `git checkout r1 && git pull --ff-only`. If it is not a git checkout,
  or has local changes, clone into /ceph/dwong/autoresearch_harness_r1
  instead and use that path below.
- R1 code finds the harness through AR_HARNESS_ROOT. Always export it:
    export AR_HARNESS_ROOT=/ceph/dwong/autoresearch_harness   # or ..._r1

DT0 — Sync and environment (no GPU)
- Clone or pull both repositories as above. Record both HEAD commits.
- Harness: `uv sync --extra dev` (uv is in the module system, or install it
  with the official one-liner). Python >= 3.11.
- Run the harness suite:
  `uv run python -m pytest -q -p no:cacheprovider --continue-on-collection-errors`.
  Expected on the Mac VM: 347 passed, 9 failed, 1 error. The failures and
  the error are environmental (/bin/zsh, missing KDD paper sections and
  manifests, the uninitialised claw-code submodule). Report your exact
  numbers and any difference from that set.
- Paper B: `make r1-test R1_PY=$AR_HARNESS_ROOT/.venv/bin/python`.
  Expected: 64 passed.
- OpenML data: openml_credit_g has no local data cache. If deepthought can
  reach openml.org, run that node once to fill its cache; otherwise note
  the blocker.
- Record: hostname, CPU count, RAM, GPU models and free memory, CUDA driver,
  Docker or Podman availability, and whether Ollama is installed.
- Accept when: both suites match the expected numbers, or you have reported
  why they differ. Commit nothing in this step except the STATUS note at the
  end of the batch.

DT1 — L4-dt: serve and pin the manager on deepthought
- Install or locate Ollama under your user (no root needed: use the
  standalone binary, with OLLAMA_MODELS on /ceph/dwong). Start it on a free
  GPU, e.g. `CUDA_VISIBLE_DEVICES=<free card> OLLAMA_HOST=127.0.0.1:11434 ollama serve`.
- Pull qwen2.5-coder:7b and verify its digest equals the pinned one
  (`ollama list` / `ollama show --modelfile`, or the API). Mismatch -> STOP.
- Measure latency with the harness script scripts/r1_llm_latency.py, as L4
  did on the Mac (STATUS, 9 Oct: median about 6.2 s on the M1 Pro). Use 10
  calls on lr_synthetic with LocalWorker.
- Optional, only if two or more cards are idle: a second instance on port
  11435 on a second card, to show that two parallel workers scale.
- Output: experiments/r1/pilot/L4dt_<UTC>/ in the harness (latency table,
  digest, GPU, Ollama version). Label PILOT.
- Accept when: the digest matches, and you have the latency table and
  0 parse failures (or a count of them).

DT2 — L12 live smoke: LLM self-control side query with the real model
- In Paper B, write a small script r1/scripts/l12_live_smoke.py that:
  - builds LLMSelfController (r1/llm_control.py) around a LangChain chat
    model for the pinned Ollama model; reuse the harness's
    autoresearch.llm.langchain_client._build_chat_model with
    autoresearch.llm.providers.resolve_llm_config("ollama/qwen2.5-coder:7b");
  - runs one run_real_campaign on digits_mlp with LocalWorker, the scripted
    proposer (r1/headroom/scripted_manager.py) as the manager, and
    ComputeBudget(max_worker_runs=10, max_llm_calls=12);
  - writes the events and the ledger to
    results/r1/engineering/L12_live_<UTC>/.
- Report:
  - the number of side queries and their action distribution;
  - parse failures and disallowed actions (from controller.log);
  - that llm_calls in control_decision events sum to the charged LLM calls;
  - that the campaign stopped at or before the caps.
- Accept when: the run completes, every event carries llm_calls, and the
  totals reconcile. Commit the script and the outputs.

DT3 — E1b smoke with the LLM manager
- From /ceph/dwong/agent_paper_B:
    PY=$AR_HARNESS_ROOT/.venv/bin/python
    $PY -m r1.headroom.e1b_collect --manager langgraph --nodes digits_mlp \
        --instances 1 --runs 10 --points 4 --reps 1 --audit-seeds 2 \
        --work /ceph/dwong/tmp/r1_e1b_smoke --workers 2 \
        --label ENGINEERING_ONLY --split engineering \
        --out results/r1/engineering/E1b_llm_smoke_<UTC>
  Repeat with --resume <out dir> until a session reports jobs_before 0.
- Check:
  - leaves exist for continue and verify;
  - no collection_failure;
  - the manifest says manager kind "langgraph";
  - proposals in the branch ledgers are LLM proposals (proposal_summary
    differs from the scripted "SYMBOL a -> b" pattern).
- Accept when: all checks pass. If LangGraphManager proposals fail to parse
  often (> 20 %), STOP and report examples.

DT4 — E1b with the LLM manager (the real pilot; PILOT)
- Same design as the scripted main run, so the two compare directly:
    $PY -m r1.headroom.e1b_collect --manager langgraph \
        --nodes digits_mlp openml_ionosphere --instances 6 --runs 20 \
        --points 4 8 12 --reps 2 --audit-seeds 6 \
        --work /ceph/dwong/tmp/r1_e1b_llm --workers 4
  Note the out dir it prints (results/r1/pilot/E1b_<UTC>). If it is
  interrupted, resume with --resume <out dir>.
- Workers share one Ollama instance unless you started more. Expect
  roughly 1,700 manager calls; run in tmux.
- Analyse:
    $PY -m r1.headroom.e1b_analyze results/r1/pilot/E1b_<UTC> \
        --md docs/r1/reports/HEADROOM_PILOT_<date>_llm_tables.md
- Write docs/r1/reports/HEADROOM_PILOT_<date>_llm.md, mirroring
  HEADROOM_PILOT_20261012.md. Include:
  - what ran, with harness commit, model digest and GPU;
  - the headroom bracket table: naive oracle (biased up; its upper CI is
    the conservative ceiling) and leaf-split oracle (biased down). Never
    call the leaf-split value "cross-fitted";
  - a side-by-side with the scripted-proposer run E1b_20261012T161034Z;
  - deviations;
  - a short "what this changes for the E2 STOP" paragraph, phrased as
    input, not as a decision.
- Commit the run directory (the *.jsonl files are git-ignored: use
  `git add -f`) and the report.
- Accept when: 0 collection failures (or each one explained), the analysis
  regenerates from committed data, and the report is written.

DT5 — MLGym feasibility (optional; only if Docker or Podman works for your user)
- Clone facebookresearch/MLGym under /ceph/dwong/third_party (CC-BY-NC-4.0;
  note the licence). Try 1-2 light CPU tasks (e.g. titanicSurvival, 3SATTime)
  as in STATUS 9 Oct. Do not write a harness adapter.
- Report: works / blocked, with exact reasons. One JSON file under
  experiments/r1/pilot/MLGym_dt_<UTC>/ in the harness.

FINISH
- Add one dated entry at the top of docs/r1/STATUS.md (Paper B):
  - the steps done, with commits and the output paths;
  - checks with numbers;
  - what was not done and why;
  - open questions for the author.
  Label everything PILOT or ENGINEERING_ONLY. Push both repositories.
- Reply with a short summary: commits, the E1b LLM headroom bracket per
  node next to the scripted one, and anything that needs the author.
```
