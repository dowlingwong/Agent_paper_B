# Prompt — R1 build batch 2 (L4, L7, L8) for a local implementation agent

Written 9 Oct 2026 by the coordinating session (Claude). Paste everything inside the fence into a local agent session running **natively on the Mac** (Claude Code or Codex in a terminal), not inside a sandbox VM. **Before pasting, edit the AUTHOR DECISIONS block.**

```text
You are implementing local build batch 2 of "Paper B, route R1": learned
control of governed autoresearch loops. Batch 1 (L3, L5, L6, plus review
fixes F1–F7) is merged into harness main at 3c80b53. Nothing you produce is
evidence: every output is ENGINEERING_ONLY or PILOT.

AUTHOR DECISIONS (stated by the author by sending this prompt)
- D15 manager model for local runs: qwen2.5-coder:7b via Ollama, pinned by
  digest. [EDIT if you want another local model.]
- Verify split policy: keep the default "fixed" for every node. The Phase 0
  noise pilot (E1) will measure the train-seed versus split-seed noise per
  node before anything changes.
- OpenML pool for this batch: 5 small binary-classification datasets that
  you select by the criteria in L8, recorded with their IDs.
Record these as dated rows in ~/Documents/agent_paper_B/docs/r1/PLAN.md
§10 ("decided 9 Oct by the author") in your first Paper B commit. Record
nothing else as decided.

STEP 0 — sync and orient
- Harness ~/Documents/autoresearch_harness:
  - run `git status`, then `git fetch`;
  - push `main` and `r1` if origin does not have them yet (batch 1 could
    not be pushed from the sandbox);
  - continue on branch `r1` (it equals main's tree).
- Paper B ~/Documents/agent_paper_B: push `main` if it is ahead of origin.
  Then commit this prompt file (docs/r1/prompts/BUILD_BATCH2_PROMPT.md) and
  the PLAN §10 rows as one commit.
- Record the machine in STATUS: chip (`sysctl -n machdep.cpu.brand_string`),
  memory (`sysctl -n hw.memsize`) and the macOS version.
- Use the repo's own environment (`uv sync --extra dev`). Record the
  baseline test counts. Batch 1 on Linux was 320 passed, 9 failed, 1 error;
  the failures were environmental. On macOS the 9 may differ: record which.

READ FIRST
1. ~/Documents/agent_paper_B/docs/r1/BUILD_RUNBOOK.md: §0 conventions, L4,
   L7, L8. This is your specification.
2. ~/Documents/agent_paper_B/docs/r1/STATUS.md: the batch 1 entries and the
   review-fix entry (F1–F7). They describe the current hooks, actions,
   masks, seeds and split policy.
3. ~/Documents/agent_paper_B/docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md:
   §2.2 (the state layers that must be restored) and §5.2 (what branch
   labels identify).
4. Harness:
   - src/autoresearch/control_plane/campaign.py (E0/E1/E2 hooks,
     _IncumbentEntry, _run_verify, _current_best) and controller.py;
   - worker/local_worker.py, seeds.py;
   - scripts/run_counterfactual.py and scripts/reexecute_kept_trials.py:
     existing counterfactual and re-execution code; reuse it where it fits;
   - scripts/reset_node_state.py, scripts/create_trial_worktree.py;
   - configs/nodes/*.yaml and nodes/openml_credit_g/
     (NodeSpec.yaml, benchmark.py, config.yaml);
   - nodes/mlagentbench_vectorization/.

TASKS, in order. Commit after each logical change on harness branch `r1`.
Each new behaviour needs a test. With the default ContinueController, the
L5 regression and every batch-1 test must stay green after every commit.

- L4 Pinned local manager model (BUILD_RUNBOOK L4)
  - Check Ollama is installed and running. Pull the D15 model and record
    its digest (from `ollama show` or the API).
  - Smoke tests on lr_synthetic with LocalWorker:
    1. `scripts/run_campaign.py --node lr_synthetic --manager
       langgraph_manager --budget 3 --dry-run --llm-stub`;
    2. a real `--budget 5` campaign with the pinned model.
  - Write a small script `scripts/r1_llm_latency.py` that reads the events
    and records per call: latency, tokens in and out (where the backend
    reports them) and proposal parse failures.
  - Output goes to `experiments/r1/pilot/L4_<UTC>/`, labelled PILOT. Put
    the summary table in STATUS.
- L7 Restore and branching at E1 / E2 (BUILD_RUNBOOK L7)
  Design it yourself, within these requirements:
  - A capture mechanism. An optional `snapshot_hook` (or an equivalent
    callback) is invoked at configured epochs. It is None by default, so
    behaviour is unchanged. It produces a `CampaignSnapshot` holding:
    - editable-file bytes;
    - the non-editable node-state paths: a declared list per node with
      defaults (artifacts/, results.tsv, experiment_memory.jsonl,
      .autoresearch_artifacts/, run.log, plus any cache the node writes;
      make the list declarable in the node YAML as `branch_state_paths`);
    - the ledger prefix;
    - an explicit current_best and the incumbent stack (verified flags
      included);
    - budget and compute-budget states and the seed settings;
    - the manager config (model, digest, temperature) and the controller
      identity;
    - the epoch-local objects: the proposal at E1; the provisional record
      and worker result at E2.
  - Snapshots are serialised to disk (JSON plus file blobs) with a
    manifest of per-layer SHA-256 hashes.
  - Restore into a fresh, isolated node directory (copytree) with its own
    records path and events path. Continue from the captured epoch with a
    FORCED first action (any action the snapshot's mask allows), then a
    given controller policy for horizon h trials. Resuming mid-trial at E1
    or E2 must not call the manager again for the captured proposal.
  - Siblings never share writable paths. Write a test that writes in one
    branch and checks the other.
  - Restore audit: from a snapshot, replay the ORIGINAL action and check
    the resulting metric is bit-identical to the original, on lr_synthetic
    and openml_credit_g (fixed seeds, LocalWorker). Write
    `restore_audit.json` with per-layer hashes and the result. A mismatch
    is a finding to report: never loosen equality to a tolerance.
  - CLI: `scripts/r1_branch.py`, which, given a snapshot, an action list
    and h, runs the siblings and writes a branch manifest.
  - Tests: snapshot round-trip; restore equivalence (restored state hashes
    equal the originals); forced first action honoured (and rejected when
    masked, per F6's semantics); isolation; the audit on lr_synthetic.
- L8 Benchmark adapters, local subset (BUILD_RUNBOOK L8)
  1. OpenML template. Generalise openml_credit_g into a template
     parameterised by OpenML dataset ID: NodeSpec, config.yaml, benchmark,
     metric parser, AR_SPLIT_SEED / AR_TRAIN_SEED. Add 5 datasets. Criteria:
     - binary classification;
     - ≤ 20k rows and ≤ 100 features;
     - preferably in OpenML-CC18;
     - one run takes seconds on CPU;
     - a permissive licence on the dataset page.
     Record IDs, sizes and licences. Register each node, and give each a
     3-trial smoke campaign with LocalWorker.
  2. MLAgentBench. Check that mlagentbench_vectorization runs with
     LocalWorker and that seed injection reaches it, or record that its
     metric is deterministic and seed-free. Run a 3-trial smoke campaign.
  3. MLGym feasibility. Clone facebookresearch/MLGym OUTSIDE the harness
     (e.g. ~/Documents/third_party/MLGym) and read its README and task
     list. Find out whether it needs Docker, a GPU or network. Check
     whether 2–3 light tasks run on this Mac. Write an adapter only if they
     do; otherwise record the blocker and what would remove it.
  4. Mark future held-out benchmarks with `held_out: true` in the registry
     (MLAgentBench stays a training/dev node for now; that decision is the
     author's).
  - Every new node gets the determinism check: same config and same seed
    twice gives bit-identical metrics. Record the result.

HARD RULES
- Default behaviour is sacred: the L5 regression and the batch-1 tests stay
  green, and new parameters default to "off".
- No double appends; the control plane alone writes the ledger; the pending
  guard is unchanged.
- Never force-push or rewrite history. Never delete ledgers. Never edit
  archive/ in the Paper B repo or the L5 fixture.
- No API models, no GPU jobs, no campaigns longer than 10 trials. Large
  downloads (> 2 GB) need the author first: stop and ask.
- If a step needs a decision not recorded in PLAN §10, or the code
  contradicts BUILD_RUNBOOK in a way that changes semantics, STOP and
  report. Do not guess.
- Label everything ENGINEERING_ONLY or PILOT. Quote no number as a result.

FINISH
- Run the full harness suite and compare it with your Step-0 baseline.
- Push harness branch `r1`. Do NOT merge into main: the coordinating session
  reviews batch 2 first.
- Add a dated STATUS entry in ~/Documents/agent_paper_B/docs/r1/STATUS.md:
  - per task: commits, files, tests, check results;
  - the L4 latency table;
  - the L7 restore-audit result;
  - the L8 adapter table (node, dataset ID, rows/features, licence,
    determinism, smoke result, blocker if any);
  - open questions for the author.
  Commit and push Paper B main.
- Return the same summary in chat.
```
