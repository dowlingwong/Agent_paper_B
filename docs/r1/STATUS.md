# Paper B (route R1) — status log

Newest entry first. Only this file says what is done.





## 12 October 2026 — Ada continuation authorized; waiting on both launch prerequisites

AI-assisted ENGINEERING_ONLY setup; no inference or evidence.

- The author explicitly accepted the Ada missing `/bin/zsh` deterministic-extraction failure as environmental; recorded in PLAN §10 at pushed commit `0f25a18`. The recorded suite remains Paper B **65 passed**, harness **347 passed, 10 failed, 1 error**. Only the recorded environment failure set is accepted; all other STOP rules remain.
- Pushed `ef34671`: Ada-only watcher, fixed to GPU 0 UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`; host/path guards and actual runtime provenance. New scripts compile; no harness behavior was changed. The private fresh checkouts and environment remain under `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`.
- Dedicated Ada tmux `r1_ada_wait_20261012` checks every 60 seconds. It must observe both an unoccupied GPU 0 and a verified `deepthought_disabled.json` before creating one permanent `ada_runner_claim` and invoking DT1–DT4. It never selects another card or clears a claim.
- **GPU 0 became occupied:** user `vla-reasoning` now holds the selected card (PIDs 116617, 117775, 117778, 117779, 117780 at census). Their jobs were untouched.
- **Duplicate prevention is still pending:** direct IPv4 SSH to both Deepthought hosts timed out again. No claim was cleared or overwritten and no Ada model was loaded. Shutdown-only monitoring continues for the old shared claim/launchers; the separate Ada experiment monitor has been re-enabled under the author's exception.
- **DT1–DT4 remain unstarted.** Once both waiting gates pass, the runner must verify `qwen2.5-coder:7b` digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`, then demonstrate Ollama `size_vram > 0` and an owned process on selected GPU before the latency campaign or later steps. GPU offload has not yet been tested.
- No additional author decision is needed for the known missing-zsh failure. Other test regressions, model digest changes, CPU fallback or unrecorded experiment decisions remain STOP conditions. E2 decisions remain open; L11 is unbuilt. All outputs remain PILOT or ENGINEERING_ONLY.

## 12 October 2026 — Ada migration preparation: hard STOP before inference

AI-assisted ENGINEERING_ONLY preparation; no empirical evidence.

- Author authorized Ada GPU 0 for DT1–DT4, fresh checkouts and tests, pinned-model GPU offload, and prevention of duplicate Deepthought runs. Recorded in PLAN §10, commit `b246a4f` (pushed). Ada path/host guards and the duplicate-launch prerequisite were committed as `0d9874b` (pushed); harness code was unchanged.
- Fresh checkouts and private uv/Python environment: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`. Paper B test HEAD `b246a4f`; harness HEAD `cbbd5fb`. uv 0.13.0, managed Python 3.11.17. Existing Ada checkouts were preserved.
- Ada GPU 0: NVIDIA RTX 6000 Ada, UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`, no processes at census, about 47 GiB free. Seven other cards were occupied. No GPU process or Ollama server was started by this preparation.
- Tests: Paper B **65 passed**. Harness **347 passed, 10 failed, 1 error**, four subtests passed. Nine failures and the collection error are the recorded missing paper/artifact/submodule set. The artifact-report existence test returns to its initial failure on a fresh checkout; the prior passing result was already documented as a generated-report flake.
- **New failure / hard STOP:** `tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`, previously passing on Deepthought, raises `FileNotFoundError: [Errno 2] No such file or directory: /bin/zsh` on Ada. Under batch hard rule 5, this stops DT1–DT4 before inference. No harness fix, shell substitution, submodule initialization or test retry was attempted.
- Preserved logs and exact test identities: `results/r1/engineering/DT0_Ada_20261012T194751Z/`. Copies remain in the remote engineering scratch directory.
- **Duplicate prevention remains unconfirmed:** direct IPv4/default SSH to both Deepthought hosts and the existing portal jump routes timed out. Their prior shared claim and tmux launchers could not be inspected or disabled. Ada inference was therefore withheld; there is no Ada/Deepthought duplicate launch by this preparation.
- **DT1–DT4:** unstarted on Ada; model digest has not been checked through a serving instance, and actual GPU offload has not been demonstrated. The pinned 7B model and all other rules remain unchanged. No headroom bracket is available. No E2 decision was recorded; L11 remains unbuilt.
- **Needs author / infrastructure:** disposition of the missing-zsh environmental failure under the hard STOP rule, and working SSH access to reserve the old shared claim and stop the old launch watchers before any Ada inference.

## 12 October 2026 — Deepthought batch 1 automatic resumption armed

AI-assisted ENGINEERING_ONLY preparation; model workloads remain PILOT or ENGINEERING_ONLY.

- Author amendment in PLAN §10 (`12db087`): monitor both authorized hosts without the previous one-hour deadline, and resume DT1–DT4 on an unoccupied GPU. The previous stopped attempt and all results are preserved.
- Both hosts are checked every 60 seconds from dedicated tmux watchers. A shared atomic claim permits one runner only. No other user's session or process is changed.
- Fresh logs and runtime state: `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z/`. The pinned `qwen2.5-coder:7b` digest stays `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; no API or larger model.
- The runner first loads at most one probe token and requires Ollama `size_vram > 0` plus a process on the selected card before DT1 latency or DT2–DT4. GPU ownership is rechecked before every step. The older host's CUDA compatibility remains unqualified until that check passes.
- Latest census: Deepthought has another user's PID 1674140 on all four cards despite 0 percent utilization; Deepthought2 has other users' processes on both cards. No model has been started by this resumption at the time of this entry.
- DT0 and its regression baselines remain as recorded below. DT1–DT4 completion requires the runner's acceptance checks and subsequent status entry; no headroom bracket is available yet. E2 decisions remain open; L11 is not built.

## 12 October 2026 — Deepthought batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **DT0:** deepthought2; Paper B `d55043c`, harness baseline `4e8fd69`; uv environment installed. Harness: 9 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 52.87s. Paper B: 64 passed. OpenML credit-g cache filled successfully.
- **DT0 environment:** Deepthought2 has 128 logical CPUs, about 1 TiB RAM, two NVIDIA L40S GPUs (46,068 MiB each), driver 570.211.01; nvidia-smi reports CUDA capability 12.8. Docker daemon access is denied; no Podman is installed.
- **Authorized fallback:** `deepthought.etp.kit.edu` (PLAN §10 author follow-up, commit `ae14877`); 40 CPUs, 503 GiB RAM, four GTX TITAN X GPUs (12,288 MiB each), driver 525.147.05. The fallback was checked without disturbing its occupied GPUs.
- **Fallback CUDA compatibility is unqualified:** current [Ollama hardware documentation](https://docs.ollama.com/gpu) requires driver 570+ for compute capability 5.0–6.2; GTX TITAN X is 5.2. The installed runtime must demonstrate actual GPU offload before DT1 is accepted; no driver upgrade was attempted.
- **Harness repair:** `0e8a817` (pushed): explicit zero `llm_calls` in emitted control decisions. Regression: failed before, 9 targeted tests passed after; full suite: 8 failed, 349 passed, 1 warning, 1 error, 4 subtests passed in 34.21s. No newly failing tests; the artifact-report existence flake accounts for one prior failure becoming a pass.
- **Preserved engineering logs:** `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e/` (environment JSON, suite logs, OpenML log, GPU census/wait, official standalone Ollama runtime).
- **Model manifest preflight:** registry manifest SHA256 matches the author pin `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`. No inference is implied by this check.

- **COLLECTOR_REPAIR:** `{"commit": "63778d35c1a4aecf91ceb10514e8ae7e333112b7", "completed": true, "reason": "Retain branch directories and ledgers after auditing", "regression": "new test failed before; all 65 R1 tests passed after"}`
- **HOST_AUTHORIZATION:** `{"commit": "ae1487788c5e93bf007629accfdfdc1403b799fb", "completed": true, "decision": "Author permits deepthought.etp.kit.edu if a GPU is idle"}`
- **DT5_FEASIBILITY_PRECHECK:** `{"commit": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "completed": true, "out": "/ceph/dwong/autoresearch_harness/experiments/r1/pilot/MLGym_dt_20261012T183511Z", "reason": "Deepthought2: Docker daemon permission denied. Deepthought: Docker daemon cannot be reached. Neither host exposes Podman in PATH.", "status": "blocked", "task_runs": 0}`
- **DT2_SCRIPT_PREPARATION:** `{"checks": "Compilation and ChatOllama/LLMSelfController constructor preflight passed; no invoke, zero model calls", "commit": "ee6eab2d4ef4cd2a7df52cf8515ff60605b2324b", "completed": true, "live_run_completed": false, "script": "r1/scripts/l12_live_smoke.py"}`

**STOP:** RuntimeError: No GPU became idle within the one-hour availability window; other users were undisturbed

DT1–DT4 are accepted only where the step entry above explicitly records completion. Uncompleted steps produced no accepted LLM headroom bracket. L12 smoke script preparation is not a live run.

- **DT5 task runs not performed:** Deepthought2 denies access to its Docker daemon; Deepthought cannot reach its Docker daemon. Podman is absent from PATH on both hosts. The PILOT precheck JSON and its commit are listed above. No MLGym clone or adapter was created.
- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. The existing fixed split policy was retained. L11 was not built.

## 12 October 2026 (evening) — steps 1–6 of the revised order; E2 STOP prepared

Executed by an AI agent (Claude) at the author's request. Outputs are PILOT or ENGINEERING_ONLY: no evidence. The work ran in the Linux VM on the Mac (4 cores, 3 GiB, Python 3.11, environment outside the repos). That VM cannot reach Ollama, so no LLM call was made anywhere.

### Harness (`autoresearch_harness`, branch `r1`; not pushed)

| Commit | What |
|---|---|
| `423addd` | **L8b:** noisy CPU nodes `digits_mlp` and `tabular_mlp` (sklearn MLP; training and split seeds injected independently); `mlp_synthetic` seed injection with unchanged defaults. 5 tests. |
| `f0dcd6a` | **L7 fix, found while debugging E1b.** A resumed E2 trial did not restore the incumbent after a discard, dropped verify's evidence, did not charge verify's re-runs, and did not push keeps onto the stack. Every branch dataset collected with earlier code is invalid. 2 tests. |
| `c686517` | **L12:** `ControlDecision.llm_calls`; controller LLM calls are charged to the LLM-call cap. Default records and events are unchanged. 3 tests. |
| `4e8fd69` | **L14 review fixes:** resumed E1 charges its run and the revise call; the resume mask respects compute headroom; the new nodes no longer print `test_score`, which the worker would have parsed into the ledger. 2 tests. |

Suite (Linux VM): **347 passed, 9 failed, 1 error**. The failures and the error are the pre-existing environmental set.

### Paper B (`r1/` package; this repo)

- **E1 (step 1):** `r1/noise/`. 1,952 runs over 11 nodes. Report `reports/NOISE_FLOOR_20261012.md`, tables `reports/NOISE_FLOOR_20261012_tables.md`, data `results/r1/pilot/E1_20261012T145353Z/`.
  - Five nodes qualify under the proposed D21 rule.
  - The OpenML logistic-regression nodes have zero training-seed noise.
  - `openml_credit_g` was not measured: there is no data cache and OpenML is blocked from the VM.
- **T1 (step 1′):** `theory/T1_MODEL.md` (model and literature map; 11 citations checked against their sources).
- **L8b (step 2):** see the harness table.
- **L9 (step 3):** `r1/branch/` (r1_branch_v1 schema, sibling table, instance-cluster bootstrap, `matching_report`).
- **T2 (step 3):** `theory/T2_DERIVATIONS.md` and `r1/theory/acceptance.py` (Propositions 1–5, Monte-Carlo-checked). D23 proposal in §7.
- **L10 (step 4):** `r1/baselines/` (ρ, always, random-matched, margin threshold, harness heuristic, KG index, ridge advantage, AWR-MLP, naive and leaf-split oracles; PACE-style and racing responses implemented but not scored).
- **E1b (step 5):**
  - Main run `results/r1/pilot/E1b_20261012T161034Z/` and sensitivity run `results/r1/pilot/E1b_vary_ionosphere_20261012/`.
  - Report `reports/HEADROOM_PILOT_20261012.md`.
  - The first E1b run is kept in `results/r1/pilot/invalid/` and was never analysed (L7 defect).
  - Headroom ceiling: +0.0006 (`"fixed"`, both nodes) and +0.0025 (`"vary"`, ionosphere). The scripted proposer stood in for the LLM.
- **L12:** `r1/llm_control.py` (forked side query; stub-LLM tests only).
- **L13:** `r1/controllers.py`, `r1/e2e.py`, `make r1-e2e`. One run in `results/r1/engineering/E2E_20261012T163133Z/` (produced before the L14 label fix, so its manifest still says PILOT).
- **T3 (step 6):** `theory/T3_SIMULATION.md`, `r1/theory/simulate.py`, data `results/r1/engineering/T3_20261012T161444Z/`.
- **L14 (step 6):** `reviews/BUILD_REVIEW_20261012.md`. A fresh-session AI review found 6 MAJOR and 14 MINOR findings. One correction round followed; the items still open are listed in the review.
- **Tests:** `make r1-test` → 64 passed.
- **E2 STOP (step 7):** `reports/E2_STOP_MEMO_20261012.md`. **The author decides.** The memo proposes:
  - the premise C1 holds;
  - verify-based C3 fails the pre-check;
  - L11 is not built yet;
  - next: an overnight LLM rerun of E1b on the Mac, a D4 amendment for run-free acceptance rules, then Phase 1 or the fallback paper.

### Not done, and why

- No LLM ran: the VM cannot reach Ollama. The E1b LLM rerun is a Mac command in the headroom report.
- Not pushed: neither repo.
- PACE was not scored: it needs its own `verify:pace` action version (D4).
- The E1 skip/revise and E0 stop/demote branches were not collected.

## 12 October 2026 — plan revised: R1-REFRAME, R1-INDEX, R1-GATE-FIRST

Planning only; no code and no runs. Author decisions of 12 Oct recorded in PLAN §1 and §10; PLAN §2, §3, §5, §6, §7, §9 and RUNBOOK §3 updated to match. Drafted by an AI agent (Claude) at the author's request.

- **R1-REFRAME.** The headline is incremental acceptance under noise. C2 is now B's own theory: the value of verify and of a raised threshold as functions of |Δ̂|/σ_n, ϱ and remaining budget; the winner's-curse bias of `current_best` and the stagnation it causes; built on ranking & selection, knowledge gradient, racing and best-arm identification. New theory track T1–T3 in the RUNBOOK.
- **R1-INDEX.** The primary contrasts are learned arms vs the C2 index policy (KG-style or PACE-style, D23). LLM self-control stays, with a stronger manager at least as a deployment check (D22). Baselines split into required and secondary.
- **R1-GATE-FIRST.** Before any model is built: E1 (noise per training seed and split seed, node selection D21) and a new E1b / 0.4b pilot headroom pre-check. D16 and L11 are deferred until the gate passes. Fallback = C1 + C2.
- **Compute map** added to RUNBOOK §3: the Mac, deepthought (many CPU cores, 4 × TITAN 12 GB) and Ada (shared 8 × RTX 6000 Ada).
- **Not committed.** The edits are in the working tree only.
- **New open decisions:** D21 (noise nodes), D22 (stronger manager), D23 (index policy).
- **Still open from 9 Oct:** the four batch-2 questions (Docker for MLGym, held-out OpenML nodes, the `lr_synthetic` split policy, `mlagentbench_vectorization`).

## 9 October 2026 — build batch 2: L4, L7, L8

All output is ENGINEERING_ONLY or PILOT: no evidence. Harness work is on
branch `r1` (now pushed), three commits on top of `3c80b53`:
`3a9f203` (L4), `1a2983b` (L7), `b55209f` (L8). Paper B: `9ff6f2a` (batch-2
prompt + PLAN §10 rows).

### Machine and baseline

- Apple M1 Pro, 16 GiB RAM, macOS 26.6.2 (build 25G83).
- Ollama 0.40.2 running locally. D15 model `qwen2.5-coder:7b` already present
  (no download): digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`,
  Q4_K_M, 7.6B params, Apache-2.0.
- Step-0 baseline (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **321 passed, 8 failed, 1 error, 4 subtests**. The
  8 failures are the same environmental set as Linux (3 artifact-manifest,
  5 KDD paper-section) and the error is the `src.autoresearch_worker`
  collection error. Linux batch 1 reported 9 failures; on macOS the
  artifact-report existence test passes because the report is already on disk.

### L4 — pinned local manager model (`3a9f203`)

- Files: `manager/langgraph_manager.py` (per-call latency/usage telemetry in
  `proposal.extra["llm_call"]`), `control_plane/campaign.py` (emits an
  `llm_call` event; default controllers emit nothing new),
  `scripts/run_campaign.py` (`--worker claw|local`, default claw),
  `scripts/r1_llm_latency.py` (new), `tests/stage2/test_r1_l4.py` (4 tests).
- Smoke tests, both on `lr_synthetic`:
  - dry-run with `--llm-stub`: 3 trials, no Ollama, no `llm_call` telemetry.
  - real `--budget 5` with the pinned model and `LocalWorker` (on a copied
    node): 5 trials, 3 kept, `net_gain` ~0.00085.
- PILOT latency (5 real calls, `PILOT` table; output in
  `experiments/r1/pilot/L4_20261009T151754Z/`):

  | metric | min | median | mean | max |
  |---|---|---|---|---|
  | latency (ms) | 5943 | 6203 | 7296 | 12003 |
  | prompt tokens | 611 | 620 | 618 | 620 |
  | completion tokens | 83 | 88 | 86.6 | 88 |

  Parse failures: 0/5. Side note: the model is deterministic only in
  structure; sampling at temperature 0.2 varied the proposals.

### L7 — restore and branching (`1a2983b`)

- Files: new `control_plane/snapshot.py` (`CampaignSnapshot`, capture, write/
  read, `restore_snapshot`, `SnapshotRecorder`, `FirstActionThenPolicy`,
  `resume_campaign`, `run_restore_audit`); `control_plane/campaign.py` gains
  an optional `snapshot_hook` (None by default) invoked at E0/E1/E2 and
  `initial_current_best` / `initial_incumbent_stack`; `nodes/spec.py` gains
  `branch_state_paths` (declared per node, defaults in the module);
  new `scripts/r1_branch.py`; `tests/stage2/test_r1_l7.py` (7 tests).
- Snapshot contents: editable bytes, the declared non-editable node-state
  paths (`artifacts`, `results.tsv`, `experiment_memory.jsonl`,
  `.autoresearch_artifacts`, `run.log`, node-declared caches), ledger prefix,
  explicit `current_best` and incumbent stack (verified flags), budget and
  compute-budget states, train/split seeds, manager config, controller
  identity, and the epoch-local proposal (E1) / provisional record and worker
  result (E2). Every layer has a SHA-256 hash in `manifest.json`.
- Restore copytree's into a fresh isolated dir with its own ledger and events;
  E1/E2 resume uses the captured proposal and does **not** re-call the manager.
  Forced first actions are honoured; infeasible ones are rejected to
  `continue` (F6 semantics), which the branch CLI showed for
  revise/verify/demote/stop at E1.
- **Restore audit** (exact equality, never a tolerance). Output in
  `experiments/r1/pilot/L7_20261009T152619Z/`:

  | node | epoch | original metric | replayed metric | reproduced | editable/node_state/ledger hashes match |
  |---|---|---|---|---|---|
  | lr_synthetic | E1 | 0.922558 | 0.922558 | yes | yes/yes/yes |
  | openml_breast_w | E1 | 0.990338 | 0.990338 | yes | yes/yes/yes |

- Branch CLI smoke (`scripts/r1_branch.py`, snapshot at lr_synthetic E1,
  h=1) wrote `branch_manifest.json`; siblings are isolated (test writes in one
  branch, checks the other).

### L8 — benchmark adapters (`b55209f`)

- Files: new `nodes/openml_template/` and five node dirs
  (`openml_breast_w`, `openml_credit_approval`, `openml_diabetes`,
  `openml_ionosphere`, `openml_wdbc`); five `configs/nodes/openml_*.yaml`;
  `nodes/registry.py` registers them; `nodes/spec.py` gains `held_out`;
  `nodes/mlagentbench_vectorization/train.py` reads `AR_SPLIT_SEED` for the
  random problem; `tests/stage2/test_r1_l8.py` (4 tests).
- Adapter table (PILOT output in
  `experiments/r1/pilot/L8_20261009T152916Z/L8_adapters.json`):

  | node | OpenML id | rows | feats | licence | determinism | 3-trial smoke | blocker |
  |---|---|---|---|---|---|---|---|
  | openml_breast_w | 15 | 699 | 9 | Public | deterministic (0.993156) | kept/discarded/discarded | — |
  | openml_credit_approval | 29 | 690 | 15 | Public | deterministic (0.909670) | kept/discarded/discarded | — |
  | openml_diabetes | 37 | 768 | 8 | Public | deterministic (0.829667) | kept/kept/discarded | — |
  | openml_ionosphere | 59 | 351 | 34 | Public | deterministic (0.984520) | kept/discarded/discarded | — |
  | openml_wdbc | 1510 | 569 | 30 | Public | deterministic (0.997642) | kept/discarded/discarded | — |
  | mlagentbench_vectorization | — | — | — | MIT | **not** deterministic: `speed_score = 1/runtime` is timing-based (24.61 vs 23.85) | kept/discarded/discarded | none; seed injection added for the random problem |

- Held-out marking: `held_out` is a `NodeSpec` field (default false) and is
  serialised; no node is marked held out yet (MLAgentBench stays a dev node,
  as the author noted; the MLE-bench Lite subset is not added in this batch).
- **MLGym feasibility** (`experiments/r1/pilot/L8_20261009T152916Z/mlgym_feasibility.json`):
  cloned `facebookresearch/MLGym` to
  `~/Documents/third_party/MLGym` (CC-BY-NC-4.0; 20 task configs). Every task
  runs inside a Docker/Podman container (`dockerfiles/mlgym.dockerfile`,
  per-task conda). **Blocker: neither Docker nor Podman is installed or
  running on this Mac.** No adapter written. Removing the blocker needs
  Docker Desktop (or Podman + a Linux VM); then light CPU tasks
  (`titanicSurvival`, `3SATTime`, game-theory tasks) could be attempted,
  subject to dataset downloads and agent/model configuration.

### Checks

- Full suite after batch 2: **336 passed, 8 failed, 1 error, 4 subtests** =
  the Step-0 baseline + 15 new tests (L4 4, L7 7, L8 4), with the identical
  8-failure / 1-error set. The L5 golden regression and every batch-1 test
  stay green.
- Default behaviour: `snapshot_hook` is None by default, `initial_*` default to
  the previous derivation, and no new event is emitted for deterministic
  managers.

### Not done, and why

- The `SnapshotRecorder` snapshots only the first matching epoch by default;
  E0 snapshots store no proposal (there is none at E0).
- `resume_campaign` rebuilds `LocalWorker` and deterministic / LangGraph
  managers from the manifest; a manager with an injected stub LLM must be
  passed back in (tests do this).
- The openml nodes need a one-time OpenML fetch (network); the pilot copies
  carry `data_cache`, so re-runs are offline.

### Open questions for the author

1. MLGym needs Docker or Podman; installing one is a system change. Proceed?
2. Should any of the five OpenML nodes be held out, or is the whole OpenML pool
   training/dev (per PLAN §6, the held-out benchmarks are MLAgentBench and the
   MLE-bench Lite subset)?
3. `lr_synthetic` verify: the pilot shows training-seed noise ≤ 1e-4 while
   split-seed noise is ~0.01. Under the default `"fixed"` split policy,
   lr_synthetic verify will mostly measure the candidate difference. Confirm
   `"fixed"` remains the choice for this node.
4. `mlagentbench_vectorization`'s `speed_score` is timing-based. Keep it as a
   dev node, or exclude it from branch/label collection where determinism is
   required?

## 9 October 2026 — batch 1 review and fixes

All ENGINEERING_ONLY. Seven review findings on harness branch `r1` (at
`201e025`) fixed, one commit each, then `r1` merged into harness `main`.
Tests ran in a Linux VM (Python 3.11.16, env built outside the repo; the
macOS `.venv` was not touched).

### Findings and commits (harness)

- **F1 (MAJOR) revise ignored its feedback — `8086f97`.** E1 `revise` now
  calls `propose_next_trial(..., revision_feedback=feedback)`.
  `LangGraphManager` adds a REVISION REQUEST block to the prompt and records
  `extra.revision_feedback` only when feedback is given; the default prompt is
  byte-identical (golden sha256 test). `revise` is also masked out for
  managers whose `propose_next_trial` lacks the keyword, so it cannot fall
  back to a plain resample. This answers open question 4 of the previous
  entry: the feedback channel is the `revision_feedback` keyword.
- **F2 (MAJOR) verify could run unseeded — `5ec9e9d`.** The E2 mask uses
  `hasattr(worker, "run_trial_at_seed")` (real and dry loops), and
  `_run_worker_at_seed` raises `SeedInjectionUnsupportedError` instead of
  falling back to `run_trial`.
- **F3 (MAJOR) demote could revert verified keeps — `ddba025`.** The mask
  input is now `top_of_stack_unverified`; `_perform_demote` pops exactly the
  top entry and refuses an empty stack or a verified top.
- **F4 (MAJOR) coupled seeds — `81c5bd5`.** `lr_synthetic` builds its dataset
  from `AR_SPLIT_SEED` and trains with `AR_TRAIN_SEED` (both default 42);
  `openml_*` `SPLIT_SEED` defaults to 42 independently. `_run_verify` and
  `run_real_campaign` take `verify_split_policy` (`"fixed"` default, or
  `"vary"`), recorded as `extra.control.verify.split_policy`.
  `LocalWorker.run_trial_at_seed(split_seed=None)` now keeps the worker's
  configured split seed, so "fixed" really re-runs on the campaign's split.
- **F5 (MINOR) LLM calls counted for deterministic managers — `04ba041`.**
  Proposals count against `max_llm_calls` only when
  `not getattr(manager, "deterministic", False)`, in both campaign loops.
- **F6 (MINOR) infeasible choice crashed the campaign — `6756d68`.**
  `_require_feasible` is gone. A masked-out or epoch-unsupported action emits
  `control_decision_rejected` `{epoch, action, mask}` and the trial continues.
- **F7 (MINOR) docs — `d9b4401`.** Docstrings (`run_real_campaign`,
  `run_dry_campaign`, controller module, `ComputeBudget`, `seeds`), the README
  R1 section and `CLAUDE.md` updated. `run_dry_campaign` is documented as
  continue-only; its `NotImplementedError` message now says so.

New tests: `tests/stage2/test_r1_review_fixes.py` (21 tests). Every finding
has at least one test that failed on the pre-fix code and passes after it. A
few companion tests guard behaviour that was already right and pass on both:
the F1 golden default prompt, the F2 mask with a seeded worker, the F3
single-top demote, and F5 counting for an LLM manager. Two existing tests
were adapted:
- `test_r1_l6.py`: the mask test uses the renamed keyword. The six-trial
  scripted run now demotes at trial 4 and verifies at trial 5, because a
  demote right after a verified keep is no longer feasible.
- `test_r1_defects.py` L3.4: with the dataset now fixed, train seeds 7 and 8
  give the same `lr_synthetic` val_score (0.921357). The different-seed check
  uses train seed 100 and tests the split seed separately.

### Checks (Linux VM)

| Run | Passed | Failed | Errors |
|---|---|---|---|
| Baseline, `r1` at `201e025` | 299 | 9 | 1 |
| After fixes, `r1` at `d9b4401` | 320 | 9 | 1 |
| `main` after merge (`3c80b53`) | 320 | 9 | 1 |

- The failures and the error are identical across all three runs and are
  environmental: the 9 failures are the same set as the macOS baseline (missing
  untracked ledgers, figures and paper sections; `/bin/zsh`), and the error is
  the `src.autoresearch_worker` collection error.
- **The L5 golden-fixture regression (`test_r1_l5.py`) passes on Linux**, at
  baseline and after every fix. The fixture was not edited.
- The tree of `main` after the merge is identical to `r1`.

### Merge and push

- Harness merge commit on `main`: **`3c80b53`** ("Merge r1: R1 build batch 1
  (L3, L5, L6) with review fixes"); `r1` is checked out again.
- `git push origin main r1` **failed**: `fatal: could not read Username for
  'https://github.com': terminal prompts disabled`. The VM has no GitHub
  credentials, and none were configured. Push both branches from the Mac.
- This STATUS commit's own push is attempted right after it is made; the
  result is in the session reply. It is expected to fail the same way.

### Observation for the author

- On `lr_synthetic` the training seed now barely moves the metric (≤ 1e-4 on
  val_score, often 0 at 6 dp), while the split seed moves it by about 0.01.
  Under the default `"fixed"` policy, verify's paired deltas on this node
  will therefore be almost entirely the candidate-versus-incumbent difference,
  with little seed noise. Choose whether `lr_synthetic` verify should use
  `"vary"`.

## 9 October 2026 (night) — build batch 1: L3, L5, L6

All ENGINEERING_ONLY: no evidence. Harness work is on branch `r1` of
`~/Documents/autoresearch_harness`, based on `da8dcbd` (7 commits, not pushed).

### L3 — the four harness defects (one commit each)

- **c4efce7** `prompt_manager`: added `deterministic = True` and a docstring
  stating it makes no LLM call; corrected `CLAUDE.md` and the `README.md`
  layout comment. Test: `TestPromptManagerIsDeterministic` (2 tests).
- **6e670dc** `ClawWorker`: the legacy path no longer stores `1 - val_bpb`
  under a `val_bpb` node's metric name (minimise nodes keep the raw sign;
  AUC-style nodes still convert). Test: `TestClawWorkerMetricSign`.
- **f446429** `_current_best`: now respects `metric_direction` and counts only
  `KEPT` records. Tests: `TestCurrentBestOnResume` (minimise resume; invalid
  high metric ignored).
- **bf3df0d** Seed injection: new `worker/seeds.py`; `LocalWorker` and
  `ClawWorker` pass `AR_TRAIN_SEED` / `AR_SPLIT_SEED` to node subprocesses;
  `nodes/lr_synthetic/train.py` and both `nodes/openml_*/benchmark.py` read
  them with 42 as the default. Tests: `TestSeedInjection` (same seed
  reproduces, different seed changes the metric; seed vars are not editable
  symbols).

Files changed: `src/autoresearch/manager/prompt_manager.py`,
`src/autoresearch/worker/{claw_worker,local_worker,seeds}.py`,
`src/autoresearch/control_plane/campaign.py`, `nodes/lr_synthetic/train.py`,
`nodes/openml_credit_g/benchmark.py`, `nodes/openml_bank_marketing/benchmark.py`,
`CLAUDE.md`, `README.md`, `tests/stage2/test_r1_defects.py`.

### L5 — decision hooks and budgets (bb15e01)

- New `control_plane/controller.py`: `ControlView`, `ControlDecision`,
  `Controller` protocol, default `ContinueController`, `build_control_view`
  (leak-refusing) and `compute_mask`.
- E0/E1/E2 hooks in `run_real_campaign` (and E0/E1/E2 in `run_dry_campaign`),
  with the E2 evaluate/commit split before the single immutable append.
- New `control_decision` event; the default controller emits nothing.
- New `ComputeBudget(max_worker_runs, max_worker_seconds, max_llm_calls)` next
  to `BudgetState`; with only `--budget N` behaviour is unchanged.
- CLI: `--controller`, `--max-worker-runs`, `--max-worker-seconds`,
  `--max-llm-calls` (documented in `README.md`).
- Tests (written first, against the unmodified code):
  `test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`
  compares every non-excluded `TrialRecord` field against a golden fixture
  (`tests/stage2/fixtures/l5_default_records.json`) captured from the
  unmodified harness, for a dry campaign and a fixed-seed `LocalWorker`
  campaign; `TestControlViewLeak` (4 tests) rejects audit metrics, future
  records and sibling outcomes.

### L6 — actions (efca691, 201e025)

- `TrialDecision.SKIPPED` + `TrialState.SKIPPED` (PROPOSED → SKIPPED) with
  `TrialRecord` validation for skipped records (no metric, execution FAILED,
  validity VALID, no failure category, `extra.control`).
- `skip`, `revise`, `verify` (paired fresh-seed re-runs, frozen response rule,
  veto/rescue, hash-checked swaps), `demote` (incumbent stack) and `stop`;
  masks per problem spec §2.1.
- Skipped counted separately in `evaluation/metrics.py`, `memory/similarity.py`
  and `reporting/export_figures.py`; `summarizer.py` handles it via
  `decision.value`.
- Tests: `test_r1_l6.py` (10 tests) — one per action, the masks, the
  `TrialRecord.from_mapping` round-trip for skipped records, and a scripted
  controller issuing each action once across a 6-trial `lr_synthetic`
  campaign (with `LangGraphManager` + an injected stub LLM, no Ollama).

### Checks

- **Full harness suite** (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **299 passed, 9 failed, 1 error, 2 subtests
  passed**. L1 baseline was 277/9/1, so +22 new tests and **the same 9 failed
  and 1 error**. The failures are the pre-existing ones listed in the L1 entry
  below.
- **Default behaviour.** The L5 regression is green after every commit; the
  default `ContinueController` adds no record fields and no events.
- **New tests by name:** `test_r1_defects.py` (7), `test_r1_l5.py` (5),
  `test_r1_l6.py` (10). Full list in the session reply.
- **README dry-run:** `scripts/run_campaign.py --node lr_synthetic
  --campaign-id smoke --budget 3 --dry-run` runs cleanly. The `smoke` ledger
  already holds the 3 records from the L1 baseline check, so it resumes
  (`records_written=0`); a fresh id (`r1_check`) writes 3. A fresh run with
  `--max-worker-runs 2` stops after 2, confirming the compute cap.

### Not done, and why

- The `r1` harness branch is **not pushed**. Only the Paper B repo push was
  requested (L1). Say the word and I will push it.
- `run_dry_campaign` still raises for non-`continue` actions; the actions are
  implemented in `run_real_campaign`, which the L6 tests exercise. The runbook
  only asks for the dry path to carry the E0/E1/E2 hooks.
- `verify` re-runs use a synthetic (non-ledger) budget index and a no-edit
  proposal; the incumbent is restored from the pre-trial editable snapshot.
  The verify budget is measured but the per-run wall time is passed as 0.
- There is a pre-existing test-order flake: `test_artifact_completeness...`
  writes `paper/tables/artifact_completeness_report.txt`, and once that file
  exists one pre-existing failure flips to a pass (8 vs 9 failures). It is not
  caused by R1 code; I report the clean-tree count (`9 failed`).

### Open questions for the author

1. Push the harness `r1` branch to `origin`?
2. The runbook's verify rule sets `current_best` to the candidate's original
   single-run metric on a rescue or keep. On a rescue this can *lower*
   `current_best` (a rescued discard had a worse metric than the incumbent).
   Confirm that is intended, or change the rule.
3. `t_min` (stop threshold, default 3) and `verify_runs` (default 2) are
   function parameters only. Add `--t-min` / `--verify-runs` CLI flags?
4. `revise` records a fixed structured feedback string; the manager interface
   (`propose_next_trial(status, memory_context, node_spec)`) has no feedback
   argument, so the manager does not yet consume it. Confirm the intended
   feedback channel for L12.

## 9 October 2026 (evening) — build batch 1: L1

**L1 — Housekeeping.**
- **Paper B commit.** One commit, "Archive old Paper B plans; adopt route R1 canonical plan": the deletion of `docs/paper_split/`, the new `archive/old_b_2026-10-09/` and `docs/r1/`, the `README.md` banner, and the dated author decisions in PLAN §10 (D1, D3, D4, D14, D19, D20 — "decided 9 Oct 2026 by the author"). Pushed.
- **Harness.** Branch `r1` created from `main` at `da8dcbd` (the base commit). `uv sync --extra dev` succeeded. The `harness/claw-code` submodule is **not** initialised (D19).
- **Baseline test result** (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`): **277 passed, 9 failed, 1 error, 2 subtests passed**. Pre-existing, recorded not fixed:
  - `tests/test_artifact_completeness_and_manifest.py` ×4 (missing checked-in campaign report / manifest entries);
  - `tests/test_kdd_paper_sections.py` ×5 (the `paper/kdd_aae_2026/sections/*.md` files are absent);
  - `tests/test_legacy_noop_skip.py` error (imports `src.autoresearch_worker` from the uninitialised `harness/claw-code` submodule).

## 9 October 2026 (15:45) — build runbook and first prompt

Added `docs/r1/BUILD_RUNBOOK.md`, a per-step specification for L1–L14 written against the harness at `da8dcbd`, and `docs/r1/prompts/BUILD_BATCH1_PROMPT.md`, which covers L1, L3, L5 and L6 with the L2 defaults in an editable block. Nothing has been implemented yet.

## 9 October 2026 (15:30) — execution order adopted

RUNBOOK §3 gains the local-first order: build steps L1–L14 on the Mac, then experiments E1–E8. The next step is L1.

## 9 October 2026 (15:20) — configurator: encoder proposal

PLAN §7 is revised. The proposed primary is now a ModernBERT-family encoder decision model (Laya checkpoint vs plain ModernBERT-large), with late fusion of numeric features. Training is supervised, then an RL step with an RLCR-style bounded proper-score reward. Kev moves to the decoder comparison. D16 stays open.

## 9 October 2026 (afternoon) — format, benchmarks, configurator proposal

- **Author decisions:**
  - No manuscript format is fixed yet (R1-FORMAT).
  - ResNet-trigger is removed; experiments and configurator training use agent benchmarks across the board (R1-BENCH).
- **New open decision D20:** the benchmark set and scope. The proposal is in PLAN §6.
- **PLAN §7 gains** a verified candidate table and a proposed primary: Kev typed decision model; CLM, generative LLM and tabular as ablations. D16 stays open for discussion.

## 9 October 2026 (later) — venue, ledgers, harness clone

- **Author decisions:**
  - TMLR is the primary venue, with an ICML main-track quality bar (PLAN §9; D17 closed).
  - The original 1,355-trial ledgers are lost (D12 closed). Only aggregate tables survive, in the workshop-paper repo.
- **Harness clone.** `dowlingwong/autoresearch_harness` was cloned to `~/Documents/autoresearch_harness` at `da8dcbd`. The folder the author connected, `~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation`, is the workshop-paper repo (camera-ready; also the harness's submodule), not the harness code.
- **Note for the author.** Because the ledgers are lost, the `ClawWorker` `1 − val_bpb` sign issue cannot be checked for the workshop paper's autoresearch trials.
- **New default D14:** harness work on branch `r1` of that clone (confirm).
- **New open decision D19:** worker backend.

## 9 October 2026 — route R1 adopted; old plans archived; canonical plan written

- **Author decisions** (PLAN §1):
  - R1-ROUTE
  - R1-VENUE: rolling journal; TMLR recommended, to be confirmed as D17
  - R1-CARRY
  - R1-ARCHIVE
  - R1-PLAN
- **Archive.** All of the old `docs/paper_split/` moved to `archive/old_b_2026-10-09/docs_paper_split/`. The move includes the uncommitted §19 and §20 additions of 9 Oct and the 9 Oct prompt pack. Legacy code and the old manuscript stay in place for now (PLAN §8; RUNBOOK 0.1 decides).
- **New files:**
  - `docs/r1/PLAN.md`
  - `docs/r1/RUNBOOK.md`
  - this STATUS
  - `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`
  - `docs/r1/inputs/NOVELTY_SWEEP_20261009.md`

  The two inputs are AI-assisted subagent outputs and were not independently reviewed. In the sweep, three arXiv entries were spot-checked against their abstract pages (2607.05458, 2603.24647, 2608.21027). COTA's "0.5B" size is not stated on its arXiv page.
- **Not committed.** The file moves were made in the working tree with `mv`; nothing is committed yet. The first Phase 0 session commits them as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Next:** Phase 0 (RUNBOOK §3). The first prompt covers 0.1–0.3.
- **Open:**
  - D1–D12 and D14–D18 (PLAN §10);
  - the configurator architecture discussion (D16);
  - venue confirmation (D17).
