# T1 expansion candidate 3 — MLGym MetaMaze isolated harness kit (25 November 2026)

**Status.** An isolated Track G harness kit for node `mlgym_metamaze` — R1-T1-NODE-EXPANSION candidate 3,
"MLGym MountainCarContinuous or MetaMaze" — built and tested on TASL-2 (CPU only; no GPU job, no lease, no U2
census, no label measurement).  The candidate was checked for noise-floor suitability first: **MountainCarContinuous
was rejected** (solved/not-solved metric, no partial credit; evidence in §3) and **MetaMaze was ported**, as the
expansion row allows.  The kit branch is pushed to `origin`; **no PR and no merge was opened**.  ENGINEERING_ONLY;
AI-assisted (DeepSeek Harness agent `port-mlgym-mountaincar`, delegated by the lead).  Independent review
**pending**.

The report file keeps the name the lead fixed for candidate 3 (`MOUNTAINCAR_KIT_20261125.md`); the node inside it
is `mlgym_metamaze` and the harness branch is `mac-trackg-mountaincar-20261125` (the candidate slot's name).  The
branch name is the only place "mountaincar" survives; the branch contains no MountainCarContinuous node.

## 1. Authority and inputs

- PLAN row **R1-T1-NODE-EXPANSION** (25 Nov 2026, author-signed with R1-T1-D21-SCOPE): candidate 3 is "MLGym
  MountainCarContinuous or MetaMaze"; per node an isolated harness kit (reviewed) → U2 census on TASL → G.1b on
  TASL under a new G.1b note.  A candidate whose G.1b completes with determinism PASS by 2 Dec 2026 enters G.5
  under R1-T1-D21-SCOPE.
- Port checklist `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; budget row **R1-BX-D5** (fixed step/token budget,
  never wall clock); **R1-HARNESS-ISOLATION** (core `68cdd1ae…` + accepted fix `5403392e…`); licence audit
  `U1_LICENCE_AVAILABILITY_20261117.md` §3 (MLGym = CC-BY-NC-4.0, HEAD `9d40c1b…`; gymnax/gymnax-blines
  Apache-2.0).
- Prior judgement: `reports/TRACKG_U3_PORT_MLGYM_20261117.md` (17 Nov 2026) had already chosen Breakout-MinAtar
  over MountainCarContinuous for "a MinAtar/MountainCar-type RL task", recording that "MountainCarContinuous
  tends to end solved or not solved, a poor fit for a noise floor".  This kit re-checks that judgement at the
  fixed-budget class before choosing the node (§3).
- Harness repo `https://github.com/dowlingwong/autoresearch_harness` on TASL-2, new worktree
  `/home/dowling/r1_trackg_20261125/harness_metamaze`; JAX CPU environment
  `/home/dowling/r1_trackg_20261125/venv_jax` (Python 3.12.16).

## 2. Harness branch and base

- **Branch:** `mac-trackg-mountaincar-20261125`, created from the accepted Track G T1 base
  **`origin/mac-trackg-t1-tasl-20261121` @ `c025f89a`** (`trackg noise_floor (T1 TASL review r1)`).  That base
  carries the accepted isolation core `68cdd1a` (merge `e85f50b`), the accepted Ada fix `5403392e` (merge
  `0c1df3a`), the three accepted isolated port tips, the G.1b review B1 option-A committed pin
  (`c11ef75`) and the TASL direct-host/CPU-only chunk support (`6843847`, `c025f89`).
- **Commit:** `aa354485bff6b5746c48ddadcb50d92e9c6f3645` — a single commit
  (`trackg T1 expansion kit: isolated node mlgym_metamaze (...)`) with 23 files changed, 2,574 insertions and 6
  deletions: the new node, its spec and the suite test extension; no other branch touched.
- **Pushed:** `origin/mac-trackg-mountaincar-20261125` = `aa354485bff6b5746c48ddadcb50d92e9c6f3645`
  (verified with `git ls-remote` after the push; `captures/git/push_verify.txt`).  No PR, no merge, no push to
  paper `main`; T1/Track P archives untouched.

## 3. Suitability decision: MountainCarContinuous rejected, MetaMaze ported

The expansion row names *MountainCarContinuous or MetaMaze*; the lead's instruction says to prefer MetaMaze
only if MountainCarContinuous is unsuitable for a noise floor ("if MountainCarContinuous ends solved/not-solved
or has no graded metric").  It does end solved/not-solved:

1. **The metric has no partial credit.**  In `MountainCarContinuous-v0` an episode ends when the car reaches
   the goal and the +100 bonus is paid once, terminally.  A solved episode returns ≈ +95 (100 minus the action
   penalty over ~100–199 steps); an unsolved episode is truncated (999-step cap, MLGym evaluates 200 frames)
   and returns a negative value proportional to the summed squared actions.  The aggregate is therefore a
   two-mode mixture — a monotone transform of the solved fraction.
2. **MLGym's own baseline shows the two-point mixture.**  The task record gives `Reward Mean 33.7938`,
   `Reward Std 41.7073` over 6,400 individual evaluation episodes: the standard deviation exceeds the mean.
3. **At the fixed 1–2 min-class budget the metric is pinned in the unsolved mode.**  A CPU probe of MLGym's
   PPO at 2,000,000 environment steps (MLGym's own `rlMountainCarContinuous` config: 256 environments, n_steps
   256, i.e. 30 PPO updates — the same number of updates a GPU run at that budget takes) gave 512 evaluation
   episodes all below −25: mean −160.28, sd 19.16, range −217.34…−25.50 — **every episode returned < −25; none reached the solved mode, and none was in the −25…−5 band either**.
   The only variation left is action magnitude — a penalty term, not task progress; a noise floor read there
   would measure noise in an uninformative direction.
4. Raising the budget to the solve transition does not help: MLGym trained 5 × 10M steps per checkpoint for
   the 33.8 mean, and at that point the per-seed value is dominated by whether the seed solves (the two-mode
   problem again).

**MetaMaze's return is a graded goal count:** the goal is re-drawn each time the agent reaches it and the
episode continues to 200 steps (MLGym evaluates 199 frames), with +10 per goal and no step penalty, so
partial progress is a graded value.  The same probe method:

| probe (CPU, TASL-2, MLGym PPO, at 2,000,000 env steps unless noted) | return mean | sd | min–max | episodes | distribution |
|---|---|---|---|---|---|
| random initialisation (0 updates, 2 eval seeds) | 1.41 | 3.90 | 0–30 | 512 | 447×0, 59×10, 5×20, 1×30 |
| trained, seed 42 | 8.13 | 12.30 | 0–50 | 256 | 151×0, 53×10, 18×20, 20×30, 11×40, 3×50 |
| trained, seed 43 (2 eval seeds) | 7.91 | 9.69 | 0–70 | 512 | 247×0, 167×10, 66×20, 25×30, 6×40, 1×70 |

The trained-at-budget return is above the random start and **below** MLGym's published baseline
(`Reward Mean 15.734375`, `Reward Std 16.312`) trained with 10M steps per checkpoint × 5 checkpoints, so the
fixed budget leaves headroom and the graded count moves smoothly with policy quality.  Probe logs:
`captures/smoke/probe_*.log`.  These are engineering probes, not a noise floor and not a census.

## 4. Node design

| Field | Value |
|---|---|
| Node | `mlgym_metamaze` (third_party/mlgym tree, CC BY-NC 4.0 scope) |
| Suite / domain | MLGym / RL |
| Upstream task | `rlMetaMazeMisc` (`configs/tasks/rlMetaMaze.yaml`, `gymnax` `MetaMaze-misc`), commit `9d40c1b5035202018cd7091fb4e83a9c68b377c0` |
| Editable | `config.yaml` (MLGym's hyperparameters without the three wrapper-owned keys), `networks.py` (MLGym's actor-critic network) |
| Frozen | `run_fixed_budget.py` (isolated parent), `ar_worker.py` (only process importing editable code), `ar_data.py`, `ar_parent.py`, `ar_isolated.py` (master `37d99ab0…`), `policy.py` (MLGym PPO with the reviewed port changes), `helpers.py`, `evaluate_policy.py` (MLGym rollout in the parent), `prepare_data.py`, `requirements.txt`, `requirements_gpu.txt`, `LICENCES.md`, `README.md`, `data/`, `representative_edits/` |
| Data | none (simulated environment); setup **downloads only** the pinned MLGym task/package snapshot (9 files at `9d40c1b…`), sha256-checks it, records the package pins and links it as `data/`.  Nothing is redistributed or committed |
| Selection metric | `val_return` (maximise, `^AR_METRIC val_return=(\S+)$`), validation keys derived from `AR_SPLIT_SEED` (5 keys) |
| Sealed test | `test_return` (`^AR_TEST test_return=(\S+)$`), MLGym's test keys `PRNGKey(0..4)`; never selected |
| Loss / steps lines | `step <env steps> loss <PPO total loss>`, `AR_STEPS env_steps=<n>` |
| Budget | `run_budget: {kind: steps, value: 2000000}` — environment steps, no wall-clock key anywhere (R1-BX-D5).  Proposed from a CPU measurement of ~50–58 s of training at this budget on four cores (1–2 min on the TASL RTX 4090 is expected); the U2 census measures it |
| Workers / determinism | `dataloader_workers: 0`, `threads: 4`; determinism defaults (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`, `PYTHONHASHSEED=0`).  The JAX worker sets `XLA_FLAGS --xla_gpu_deterministic_ops=true`, `XLA_PYTHON_CLIENT_PREALLOCATE=false`, `TF_CUDNN_DETERMINISTIC=1` before importing jax |
| Isolation | `isolation.entry: run_fixed_budget.py`, `args: ["--steps", "{budget}"]`; the parent holds the result channel and never imports editable code; only `ar_worker.py` imports `networks.py` |
| Environment | node `requirements.txt` (jax[cpu] 0.4.35, flax 0.10.2, optax 0.2.4, chex 0.1.88, gymnax 0.0.9, tensorflow-probability 0.25.0, dotmap 1.3.30, tqdm 4.70.1, numpy 2.5.4; the same pins the accepted JAX node `mlgym_breakout_minatar` uses) and `requirements_gpu.txt` (jax[cuda12]) for the GPU host.  The local CPU check is `venv_jax` (Python 3.12.16, 56 packages, freeze sha256 below) |

**One model per run.**  MLGym's `src/train.py` trains five checkpoints (five seeds) and its evaluator scores all
five; the port trains **one** model, initialised exactly as MLGym's first checkpoint (the training seed's
`PRNGKey`, `rng_list[1]`), and keeps MLGym's evaluation procedure (5 keys × 256 environments; only the test keys
are sealed).

**Budget semantics.**  The count is environment steps taken by the frozen PPO loop (MLGym's rounding
`(steps // num_train_envs + 1) * num_train_envs`, printed as `AR_STEPS env_steps=` and checked by the worker);
the parent cross-checks the step counter against the node's budget.  An edit can change compute per step but not
the step count; evaluation is frozen and outside the budget.  **Changing `run_budget.value` changes
`node_spec_sha256` and the edits manifest** → re-declared edits and a new review (checklist A).

## 5. Data preparation, manifest and licence

- `setup_command`: `test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_metamaze"`.
- `prepare_data.py` downloads exactly the nine pinned MLGym task/package files from
  `https://raw.githubusercontent.com/facebookresearch/MLGym/9d40c1b5035202018cd7091fb4e83a9c68b377c0/...`
  (`configs/tasks/rlMetaMaze.yaml`; `data/rlMetaMazeMisc/evaluate.py`, `requirements.txt`, `src/__init__.py`,
  `src/config.yaml`, `src/helpers.py`, `src/networks.py`, `src/policy.py`, `src/train.py`), checks each file's
  sha256 **and size** against the values pinned in the script, records the sha256s, the two requirements files'
  sha256 and the resolved package versions in the hashed data manifest, makes the directory read-only and links
  it as the node's `data/`.  The frozen parent and the worker verify the manifest at the start of every run, so a
  changed snapshot ends the run (`ar_data` exit 5) before training starts.
- Setup on TASL-2 (25 Nov 2026), `AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/metamaze_20261125/data`:
  nine fetches, all pinned sha256/size confirmed; data root `/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze`
  (9 files, 32,201 bytes), **`data_manifest.json` sha256 `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`**.
  Captures: `captures/data/`.
  Because the manifest records the **resolved package versions** (and the two requirements files' hashes), a
  setup on the GPU host produces the same nine asset hashes but a **different `data_manifest.json` sha256**
  (the jaxlib build differs); the runs verify the manifest's file table and hashes, not `source.packages`, so
  this is expected — the census records its own host's manifest sha256.  The value quoted here is the TASL-2
  CPU setup's.
- **Licence / provenance** (`LICENCES.md`, frozen): MLGym code and the adopted files under **CC BY-NC 4.0** with
  attribution and the list of port changes; MLGym's PPO/rollout parts are adapted from gymnax-blines/gymnax
  (**Apache-2.0**, licence copy at `third_party/mlgym/LICENSE-APACHE-2.0`); the downloaded snapshot under
  `data/` is CC-BY-NC 4.0 material and is **never redistributed**; the branch contains no task data.  The
  MLGym-in-MIT-tree licensing conflict is the pre-existing suite issue recorded by U1 §3 and R1-TRACKG-LICENCES,
  not a new decision of this kit.

## 6. Representative edits E1–E4 (declared before any measurement)

Manifest `third_party/mlgym/nodes/mlgym_metamaze/representative_edits/manifest.json`, sha256
**`6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2`**
(`schema trackg_representative_edits/v1`, `measured: false`, `node_spec_sha256 d97bb182…`,
`run_budget {steps, 2000000}`).  Declaration required Python 3.12 (the harness's normalised code-state hashes are
AST-based); a first manifest produced by the system Python 3.10 was **moved aside** to
`/home/dowling/r1_engineering/metamaze_20261125/moved_aside/manifest_first_attempt_py310.json` (not deleted) and
the set re-declared with the Python 3.12 environment.

| Edit | Change | sha256 |
|---|---|---|
| E1 | `config.yaml` PPO learning rate 5e-04 → 2e-04 (`lr_begin` and `lr_end`) | `9aacd7fd568e8bff3670efe1193b4cc29891afd431842d04c5f73a015c6137d5` |
| E2 | `config.yaml` PPO learning rate 5e-04 → 1e-03 (same two lines as E1, so E1/E2 are alternatives) | `ff4cd594788fa908ac26f2713c9bf5e7bf2b480325e8e89ca3aef13219474703` |
| E3 | `config.yaml` entropy coefficient 0.05 → 0.01 | `c76634e908b787e4bc397294b750aef28a25fa2c0c426def3544b8dee02d2a53` |
| E4 | `networks.py` hidden-layer activation `nn.relu` → `nn.tanh` in both the actor and the critic (4 sites, code-level) | `ec73a85a98c0690191e22be3cca97106c7daca51ba773ae484f696c01fb9f918` |

Composability (`tests/trackg/test_port_mlgym.py::test_interacting_edits_compose`): E1+E3, E1+E4, E2+E3, E2+E4 and
E3+E4 apply in both orders; E1+E2 conflict (same lines).  **Declared interaction for S1.1: E2 × E3** (3× higher
learning rate with a 5× lower entropy bonus).  No edit is expected to diverge; the synthetic smoke's deliberate
NaN network diff covers the divergence class.

## 7. Checks run (25 November 2026, TASL-2, CPU only)

All runs from the kit worktree, `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, no GPU
(`CUDA_VISIBLE_DEVICES` empty).  Captures are in `MOUNTAINCAR_KIT_20261125_captures/`.

| Check | Command | Result | Capture |
|---|---|---|---|
| Static port tests (all five MLGym nodes, kit branch) | `pytest tests/trackg/test_port_mlgym.py -q -k "not smoke"` in the torch 3.12 env | **32 passed, 2 skipped, 5 deselected** in 10.77 s (spec loads, scopes, frozen copies, manifest re-declared byte-identically, scope refusals) | `test_logs/pytest_port_mlgym_static.log` |
| New node tests incl. synthetic-snapshot smoke | `pytest tests/trackg/test_port_mlgym.py -q -k "metamaze"` in the JAX env | **9 passed** in 81.14 s (baseline `ok`; frozen-path diff refused `scope_violation`; NaN network diff `divergent/non_finite_loss`; E1–E4 `ok`; repeat baseline reproduces the metric exactly; snapshot-tamper refused exit 5; candidate/suitability record) | `test_logs/pytest_port_mlgym_metamaze.log` |
| Isolation core (delegated cgroup, `AR_TEST_CGROUP_PARENT`) | `pytest tests/trackg/test_trackg_isolation.py -q` | **27 passed, 1 skipped** — the accepted TASL-2 host-check count | `test_logs/pytest_isolation.log` |
| Whole `tests/trackg -k "not smoke"` on the kit branch | torch 3.12 env | **339 passed, 1 failed, 24 skipped, 11 deselected** in 48.18 s | `test_logs/pytest_full_suite_kit.log` |
| The same suite at the pristine base `c025f89a` (read-only worktree `/tmp/base_c025f89a`) | torch 3.12 env | **333 passed, 1 failed, 22 skipped** in 44.90 s — **the same single failure** (`test_trackg_review_round2.py::test_child_that_leaves_the_group_but_not_the_session_is_killed`, an environment/host-race failure: `child.pid` absent), so it is pre-existing, not a kit regression; the +6 passes and +2 skips are the new node's (two of its tests need the JAX packages, absent from the torch interpreter) | `test_logs/pytest_full_suite_base.log` |

**Checklist-E CPU smoke on the real (downloaded, pinned) snapshot, full 2,000,000-step budget, seeds 8001/8001,
inside a delegated `systemd-run --user --scope -p Delegate=yes -p MemoryMax=16G` cgroup** — the frozen parent
through `WorkingCopyRunner` in the stub-manager campaign, then every declared edit and a second baseline
(`real_smoke.py`; ENGINEERING_ONLY, **not** U2 and not the GPU census):

| run | decision | diff | outcome | val_return | elapsed s |
|---|---|---|---|---|---|
| `s000_baseline` | baseline | — | ok | **8.703125** | 55.84 |
| `s001` | not_run_refused | frozen path | `scope_violation` | — | — |
| `s002` | discarded_divergent | NaN network | `non_finite_loss` | — | 63.13 |
| `s003` (E1 stub through the manager) | discarded | E1 | ok | 7.062500 | 57.70 |
| `E1` | — | applied | ok | 7.062500 | 60.22 |
| `E2` | — | applied | ok | 8.062500 | 60.31 |
| `E3` | — | applied | ok | **2.929688** | 57.10 |
| `E4` | — | applied | ok | **15.468750** | 54.94 |
| `B2` (repeat baseline) | — | — | ok, **same value as s000** | **8.703125** | 75.54 |

Every executed record: complete `run_record.json`, `isolation.effective: true`, `waivers {}`, `exceptions []`,
`frozen_files_checked: 19` (18 committed files + the `data` link), worker sandbox + cgroup `cgroup.kill` +
`ptrace_scope 1` recorded, `process.killed_with: null`, no `sealed` key in the manager view.  The sealed test
returns stay in the run records (not copied into this memo).  `check_baseline_log` saw the loss/step patterns,
exactly one selection line and one sealed-test line in the result channel and none in the log, and no carriage
returns.  The validation metric responds to the declared edits (E3 2.93, E4 15.47 vs 8.70), which is promising
for D28 liveness — but this is a port smoke, not the noise floor.  Captures: `captures/smoke/`.

**`determinism.not_forced` explanation** (checklist E item): the interpreter is the torch-free JAX environment,
so the shim records four entries as `not_forced` with reason `torch_absent`
(`cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`, `torch.set_num_threads`,
`dataloader_workers`); none is settable there and the JAX node's fixed-seed determinism comes from the frozen
PPO loop, the seeds and the deterministic XLA flags.  The fixed-seed determinism check itself is G.1b's (GPU).

## 8. Pins and fields for the U2/G1b spec (all values computed on the kit at the branch tip)

```
harness branch          = mac-trackg-mountaincar-20261125
harness base            = c025f89aeafc2199bf3487b4bcaa16678273c702   (origin/mac-trackg-t1-tasl-20261121)
harness tip (pushed)    = aa354485bff6b5746c48ddadcb50d92e9c6f3645  (1 commit; 23 files, +2574/-6)
node                    = mlgym_metamaze   (suite mlgym, domain RL)
node_spec_sha256        = d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9
                          (canonical spec.raw_sha256, what the harness records/checks)
spec raw sha256         = d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59
                          (the YAML file bytes; informational)
committed_pin_sha256    = 759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db
                          (frozen_pin_sha256(committed_view(...)); 18 committed files, without the setup data link;
                          re-derived from a clean `git archive HEAD` tree to the same value)
deployed_pin_sha256     = 1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7
                          (with the host data link; what a run record carries — the census uses the committed pin)
edits_manifest_sha256   = 6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2
data_manifest_sha256    = e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000
env freeze (venv_jax)   = 630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9
                          (Python 3.12.16, 56 packages, sha256 of `pip freeze`; node requirements.txt is the
                          declared env; the census records its own freeze)
node ar_isolated sha256 = 37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610  (= master, match)
host / device           = TASL-2; CPU only; no GPU job, no lease
run budget              = steps 2000000 (environment steps; R1-BX-D5)
seeds                   = AR_TRAIN_SEED / AR_SPLIT_SEED (split default 42)
setup_command           = test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_metamaze"
run_command             = python3 run_fixed_budget.py --steps {budget}
isolation               = entry run_fixed_budget.py, args ["--steps", "{budget}"]
metrics                 = val_return (maximise, validation) / test_return (sealed)
workers                 = dataloader_workers 0, threads 4
determinism             = cudnn_benchmark false, deterministic_algorithms true, cublas ":4096:8", PYTHONHASHSEED 0
data link (deployed)    = /home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze
```

The full per-file pin table (`frozen_files`, 18 entries), the HEAD-archive manifest and the pinned spec/edits/data
hashes are in `captures/pins/` and `captures/git/head_archive_sha256.txt`.

## 9. Risks, anomalies and open points for the reviewer/lead

1. **The candidate's name vs the node.**  The lead fixed candidate 3 as "MountainCarContinuous or MetaMaze" but
   also fixed the branch name `mac-trackg-mountaincar-20261125` and this report's filename; the node is
   `mlgym_metamaze`.  If the reviewer prefers the branch to be named after the ported node
   (`mac-trackg-metamaze-20261125`), that is a branch rename with no content change; the tip and pins above are
   what the census binds.
2. **MountainCarContinuous rejection.**  §3 records the evidence (two-mode metric; MLGym baseline sd > mean; a
   fixed-budget probe wholly in the unsolved mode; no graded partial credit at any budget because the goal ends
   the episode).  If the lead wants the candidate screened empirically anyway, that is a second kit, not a change
   to this one.
3. **Download-only snapshot and network.**  The setup fetches the nine pinned MLGym files from
   `raw.githubusercontent.com`; the census host needs that egress once (no account, no API).  The run then only
   verifies hashes.  A host without egress must have the snapshot pre-placed (same manifest) — an operational
   note for U2, not a code change.
4. **Budget is an estimate for U2.**  ~50–58 s of CPU training at 2,000,000 steps on four cores (the smoke's
   full runs took 55–75 s including the frozen-frame-loop evaluation); the TASL RTX 4090 must measure its own
   time and set the timeout = 3 × its slowest record.  Changing the value re-opens the spec/manifest pins.
5. **Evaluation is 10 × 199 frame-loop steps with a worker call per frame** (by design: only the logits come from
   the editable network).  It costs ~4–8 s of the ~55–75 s CPU record and should be negligible on the GPU host,
   but the census should confirm the eval share.
6. **Sealed test kept out of this memo** (titanic-kit convention); it is in the run records for the census.
7. **Pre-existing full-suite failure** (§7) fails identically at the base commit; it is a host-race in the review
   round-2 test, not this kit.
8. **`frozen_entry_count_committed = 14`** in `pins.json` counts `frozen_paths` entries minus `data/`; the
   expanded committed file set is the **18** files listed in `frozen_files` (the `representative_edits/` entry
   expands to 5).  Read the 18.
9. **No U2 census, no GPU job, no G.1b noise floor, no D21/D28, no label/evidence use** was run; the
   lead runs U2 after independent review.  No paper-main push, no PR, no merge; T1/Track P archives untouched.

## 10. Reproduction

```
# branch (TASL-2 worktree)
git -C /home/dowling/r1_trackg_20261125/harness_metamaze log --oneline -1   # aa354485bff6b5746c48ddadcb50d92e9c6f3645
git ls-remote origin mac-trackg-mountaincar-20261125                        # same tip
# setup (once, outside the repo; needs GitHub raw egress)
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/metamaze_20261125/data
cd third_party/mlgym/nodes/mlgym_metamaze && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_metamaze"
# static + synthetic tests
PYTHONPATH=src /home/dowling/r1_trackp/venvs/trackp-cpu/bin/python -m pytest tests/trackg/test_port_mlgym.py -q -k "not smoke"
PYTHONPATH=src /home/dowling/r1_trackg_20261125/venv_jax/bin/python -m pytest tests/trackg/test_port_mlgym.py -q -k "metamaze"
# checklist-E CPU smoke on the real snapshot (full budget, cgroup-isolated)
systemd-run --user --scope -p Delegate=yes -p MemoryMax=16G -p MemorySwapMax=0 \
  /home/dowling/r1_trackg_20261125/venv_jax/bin/python /home/dowling/r1_engineering/metamaze_20261125/real_smoke.py
# pins (from the kit root, harness on PYTHONPATH)
/home/dowling/r1_trackg_20261125/venv_jax/bin/python /home/dowling/r1_engineering/metamaze_20261125/pins.py
```

## 11. Captures (this directory)

`MOUNTAINCAR_KIT_20261125_captures/` — `git/` (head, refs, status, show stat, diffstat vs base, HEAD-archive
per-file sha256, push verify), `spec/` (node spec + sha), `edits/` (E1–E4 + manifest + sha), `data/` (data
manifest + sha), `env/` (venv freeze + sha, requirements, Python version), `test_logs/` (static, metamaze,
isolation, full suite kit, full suite base), `smoke/` (checklist-E log, records summary, four suitability-probe
logs), `pins/` (pins.json, pins.txt, pins.err), `SHA256SUMS`.  TASL-2 evidence roots:
`/home/dowling/r1_engineering/metamaze_20261125/` (data, captures, CPU smoke runs, probes) and the kit worktree
`/home/dowling/r1_trackg_20261125/harness_metamaze`.

## 12. What was not done

No U2 census, no G.1b noise floor, no GPU job, no lease, no label read, no test-metric selection, no PR/merge, no
change to `mac-trackg-t1-tasl` or any other branch, no push to paper main.  No MountainCarContinuous node was
built (rejected in §3, documented rather than forced).
