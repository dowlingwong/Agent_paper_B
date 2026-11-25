# Independent review — Track G T1 expansion kit: MLGym MetaMaze node `mlgym_metamaze` (25 November 2026)

**Verdict: ACCEPTED** — the ENGINEERING_ONLY harness kit for R1-T1-NODE-EXPANSION candidate 3
("MLGym MountainCarContinuous or MetaMaze", node `mlgym_metamaze`,
branch `mac-trackg-mountaincar-20261125` @ `aa354485bff6b5746c48ddadcb50d92e9c6f3645`) is accepted for the
U2 census and a new G.1b note, with the MINOR corrections m1–m10 (paper-side report/captures/evidence-root;
the two frozen-file wording items are deferred to c8) and the conditions c1–c8 before any census/G.1b run.
**No BLOCKING, no MAJOR.** I verified the branch, push, content, every pin and every SHA in the record
independently, recomputed the canonical spec hash, the committed and deployed pins, the edits manifest, the
data manifest and the environment freeze from the committed blobs and the host, re-fetched the nine pinned
upstream MLGym files and matched their hashes and sizes, confirmed the 6,400-episode MountainCar and MetaMaze
baseline semantics against the pinned upstream commit, and re-derived the CPU-smoke values, outcomes,
isolation fields, determinism record and sealed-test containment from the host run records. The kit is honest
about what it did **not** measure (no GPU, no U2, no G.1b, no noise floor) and discloses the branch-name/node-name
mismatch and the GPU-host data-manifest difference. The suitability decision (MountainCarContinuous rejected,
MetaMaze ported) is justified by the evidence, with the wording corrections m3/m4.

**Reviewer and method.** Fresh independent reviewer (`metamaze-kit-reviewer`), delegated by the lead; no
involvement in the port, the data setup, the smoke or the report. Read-only: the only file written in any
repository is this review; no run/edit/commit/push/delete of any repository or host artefact, no HTCondor, no
GPU job, and no test/census re-executed. TASL-2 (`portal_zhixu`, host clock **2026-11-25T05:04–05:12 PST =
13:04–13:12 UTC**) was read with `ssh -o BatchMode=yes` using read-only commands only (`ls`, `stat`, `cat`,
`sha256sum`, `readlink`, `git -C … --no-optional-locks rev-parse/log/show/diff/ls-tree/cat-file/merge-base/
ls-remote`, `curl -fsS … | sha256sum`, `journalctl`); nothing was written into the host, the repositories, the
data root or any capture tree. Pins and canonical hashes were recomputed with read-only Python
(`python -B`, `PYTHONDONTWRITEBYTECODE=1`) that only read files and printed derived hashes; the node's YAML was
canonicalised exactly as the loader does
(`json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)` → sha256), and
the frozen pins were rebuilt from the committed blobs (not from `pins.json`). Capture logs were accepted as
captured evidence (integrity checked, §7) because re-executing tests/runs is outside this review's remit.

**Object under review.**

- Kit branch `mac-trackg-mountaincar-20261125`, tip **`aa354485bff6b5746c48ddadcb50d92e9c6f3645`**, pushed to
  `origin` (`github.com/dowlingwong/autoresearch_harness.git`); parent/base
  **`c025f89aeafc2199bf3487b4bcaa16678273c702`** = `origin/mac-trackg-t1-tasl-20261121`; host worktree
  `/home/dowling/r1_trackg_20261125/harness_metamaze`.
- Report `docs/r1/reports/tasl_chain_20261122/MOUNTAINCAR_KIT_20261125.md` — **307 lines, 26,439 B, sha256
  `0cede51b0dba90af8cc485748d577c2049d3671361f07facff70baabed635e7e`**; untracked in `ops-tasl-20261116`
  (HEAD `9253192f276f42a271baa2d989691a9a724b2f17`) and absent from `origin/main` `912a7e02` (paper-side
  record; correct, nothing pushed to paper `main`).
- Captures `MOUNTAINCAR_KIT_20261125_captures/` — **42 files = 41 checksummed entries + `SHA256SUMS`**;
  `sha256sum -c SHA256SUMS` **rc 0** on the Mac, `SHA256SUMS` sha256
  **`f5ee03bc1f22d5a7c25097eb3c38909b0c2a92ed93839815a543bd9473203a81`**; **all 42 files are byte-identical**
  to `/home/dowling/r1_engineering/metamaze_20261125/captures/<same path>` (my 42/42 hash diff was empty).
- Authority: PLAN row **R1-T1-NODE-EXPANSION** and `R1-T1-D21-SCOPE` (PLAN on `origin/main` `912a7e02`, row
  line 1516: "MLGym MountainCarContinuous or MetaMaze, MLGym Titanic, 1GC-7RC ETTh1, 1GC-7RC Forest Cover (AG
  News as reserve)", unnumbered; per node "isolated harness kit (reviewed) → U2 census on TASL → G.1b on
  TASL (D21 protocol, 460 runs) under a new G.1b note"; 2 Dec 2026 determinism-PASS entry to G.5),
  `R1-BX-D5`, `R1-TRACKG-LICENCES`, `R1-HARNESS-ISOLATION`, `R1-G1B-TIMEOUT`;
  `TRACKG_PORT_CHECKLIST.md`; the accepted T1 TASL base `c025f89a`; U1 licence audit §3; the U3 port report's
  earlier MountainCar judgement (`docs/r1/reports/TRACKG_U3_PORT_MLGYM_20261117.md`: "MountainCarContinuous
  tends to end solved or not solved, a poor fit for a noise floor").

## 1. Branch, push and content — verified

- Branch exists on `origin` at `aa35448` (`git ls-remote origin refs/heads/mac-trackg-mountaincar-20261125` from
  TASL-2 = local HEAD); `git rev-list --count origin/mac-trackg-mountaincar-20261125..HEAD` = **0** (nothing
  unpushed). The branch is **not** an ancestor of `origin/main` `3c80b53c`; the base ref
  `refs/heads/mac-trackg-t1-tasl-20261121` is unchanged at `c025f89a` on the remote. The paper report is absent
  from `origin/main` `912a7e02` (verified on the paper repository) and is untracked, as cited.
- **Single, non-merge commit**: parent exactly `c025f89a` (`git rev-list --parents -n1 HEAD`), author = committer
  `Dowling Wong <wangdowling@gmail.com>`, `Wed Nov 25 04:47:57 2026 -0800`; subject "trackg T1 expansion kit:
  isolated node mlgym_metamaze (R1-T1-NODE-EXPANSION candidate 3, MetaMaze)"; `rev-list --count` base..HEAD = 1.
- `git diff --shortstat c025f89a..HEAD` = **23 files, +2,574 / −6**: the 20 node files (2 editable:
  `config.yaml`, `networks.py`; 18 frozen counting the five `representative_edits/` entries), the node spec
  (`third_party/mlgym/configs/trackg/nodes/mlgym_metamaze.yaml`, +122), the additive `tests/trackg/
  test_port_mlgym.py` extension (+86/−6), and a 3-line `third_party/mlgym/README.md` update (node inventory
  "four"→"five" + the metamaze row) — the report's §2 list omits the README update (m2; content is related and
  benign). No deletion, no rename, no harness-core edit, nothing unrelated.
- Worktree status: **clean except the untracked setup `data` symlink**
  (`?? third_party/mlgym/nodes/mlgym_metamaze/data`) — exactly the host-specific link that the committed pin
  is defined to exclude (the run records carry the deployed pin). `git ls-tree -r HEAD` contains **no task
  data** and no `data` entry; the only committed files are the 20 node files + spec.
- Accepted T1 TASL ancestors confirmed on the branch at the base: `68cdd1a` (isolation core), `e85f50b` (its
  merge), `5403392e` (Ada isolation fix), `0c1df3a` (its merge), `c11ef75` (G.1b review B1 option-A committed
  pin / data-manifest check), `6843847` and `c025f89a` (direct-host/CPU-only chunk support), and the three
  accepted isolated port tips `f07875d` (MLGym), `448f682` (autoresearch), `fb6e7d7` (MLAgentBench) — all
  ancestors of `c025f89a`.
- Shared-helper claims hold at HEAD: `ar_isolated.py` =
  `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` = `src/autoresearch/trackg/node_lib/`
  master = the breakout node's copy; `ar_data.py` `85cec63f…`, `ar_parent.py` `cbef1d38…` are shared node
  library files; `ar_worker.py` `b66d1f1d…` is the node-specific worker. `requirements.txt`/`requirements_gpu.txt`
  carry exactly the pins of the accepted JAX node `mlgym_breakout_minatar` (differ in the comment line only).
- Branch name vs node: `mac-trackg-mountaincar-20261125` (the candidate-slot name fixed by the lead) but the
  node is `mlgym_metamaze`; the report discloses this in the status paragraph and §9.1, and the branch contains
  no MountainCarContinuous node. Verified.

## 2. Suitability decision: MountainCarContinuous rejected, MetaMaze ported — verified

The expansion row allows either task; the decision is documented, not forced. I re-read the probe script,
probe logs and the pinned upstream task files, and independently confirmed the numbers:

- **MountainCarContinuous is a two-mode (solved / not-solved) metric.** Pinned `rlMountainCarContinuous.yaml`
  (upstream) gives `baseline_scores: Reward Mean 33.793758392333984, Reward Std 41.70726013183594`; MLGym's
  `evaluate.py` evaluates 5 checkpoints × 5 seeds × 256 environments = **6,400 episodes** (confirmed: `SEEDS =
  list(range(0,5))`, 5 checkpoint files, `batch_size = 256`, `max_frames = 200`). Standard deviation > mean.
- **Fixed-budget probe**: the log `probe_mountaincar_2m.log` records `budget_steps 2,000,000`,
  `expected_env_steps 2,000,128 = (2000000//256+1)*256`, `ppo_updates 30`, `num_envs 256`, `n_steps 256`
  (MLGym's own config, `num_train_envs: 256`), and **512 evaluation episodes** (2 eval seeds × 256) all in the
  unsolved mode: mean **−160.2776**, sd **19.1564**, min **−217.3393**, max **−25.5043** — every episode
  `< −25`; the `[−25,−5)` and `[85,105)` bands are exactly 0.0. The report's §3.3 numbers match the log.
  The probe used the port-adapted `policy.py` (the documented, training-neutral `on_update`/eval-off/
  `total_steps` changes — the PPO algorithm, buffers, loss and update are unchanged) and the pinned
  `config.yaml` (byte-equal to upstream `c55afc3c…`); the conclusion is unaffected.
- **MetaMaze is a graded goal count** (pinned `rlMetaMaze.yaml`: +10 per goal, no step penalty, 200-step
  episode; MLGym evaluates 199 frames): probe logs give random init 512 episodes mean **1.4062** / sd **3.9000**
  / range 0–30; trained seed 42 256 episodes **8.1250** / **12.2952** / 0–50; trained seed 43 512 episodes
  **7.9102** / **9.6889** / 0–70 — with multiple goals per episode (seed 43 has 6×40 and 1×70), i.e. the return
  is 10 × goals, not a pass/fail. All values match the report's §3 table. The trained-at-budget value is above
  the random start and **below** MLGym's published baseline `Reward Mean 15.734375` / `Reward Std
  16.312131881713867` (pinned `baseline_scores`), so the fixed budget leaves headroom. These are engineering
  probes, not a noise floor, and the report says so.
- The node README (frozen) and report also record the earlier U3 judgement; the decision to port MetaMaze is
  therefore supported by (i) a graded metric, (ii) a two-mode metric rejected at the node's fixed budget, and
  (iii) headroom below the published baseline. §3 of the report's four-part argument is correct except for the
  wording items m3 (goal re-draw) and m4 (MountainCar training budget per checkpoint).

## 3. Node design, task surface and isolation — verified against the pinned upstream commit

I re-read the committed node files and the upstream MLGym task at `9d40c1b5035202018cd7091fb4e83a9c68b377c0`
(re-fetched, §5). The port keeps MLGym's task and PPO and fixes the loop:

- **Editable**: `config.yaml` (MLGym's `data/rlMetaMazeMisc/src/config.yaml` minus the three wrapper-owned keys
  `num_train_steps`, `evaluate_every_epochs`, `num_test_rollouts`) and `networks.py` (MLGym's actor-critic).
  The worker refuses a `config.yaml` that re-introduces a wrapper key (`EXIT_BAD_EDITABLE_API = 4`); a test
  asserts the keys are absent. **Frozen**: `run_fixed_budget.py` (isolated parent), `ar_worker.py` (only process
  importing editable code), `ar_parent.py`, `ar_isolated.py`, `ar_data.py`, `policy.py`, `helpers.py`,
  `evaluate_policy.py`, `prepare_data.py`, `requirements.txt`, `requirements_gpu.txt`, `LICENCES.md`,
  `README.md`, `data/`, `representative_edits/` — the spec's `frozen_paths` covers every committed node file
  (18 expanded entries). The spec sits outside the node dir. `allow_new_files: false`.
- **One model per run**: MLGym's `train.py` trains five checkpoints (five `rng_list[1:]` seeds) at the full
  `num_train_steps` each; the port trains **one** model, initialised exactly as MLGym's first checkpoint
  (`jax.random.split(PRNGKey(seed), 6)`, training rng `rng_list[0]`, init `rng_list[1]`), and keeps MLGym's
  evaluation procedure. Confirmed in `ar_worker.py`; the budget check is
  `expected_steps = (budget // num_train_envs + 1) * num_train_envs` and the worker fails (exit 3) unless
  `total_steps == expected_steps` and `>= budget`.
- **Budget semantics**: `run_budget {kind: steps, value: 2000000}` — environment steps, no wall-clock key
  anywhere (the strict loader refuses one); `run_command`/`setup_command` carry no time flag. The smoke's
  `AR_STEPS env_steps=2000064` (observed) is `(2000000//64+1)*64` — MLGym's rounding with this task's
  `num_train_envs: 64`; the harness outcome classifier accepts `steps >= budget` and the smoke records
  `outcome ok`. Changing the value changes `node_spec_sha256` and the edits manifest (checklist A).
- **Evaluation and sealing**: the frozen parent holds the runner result channel and runs MLGym's rollout
  (`evaluate_policy.py`: 256 environments, exactly 199 frames, categorical sampling with MLGym's key split;
  only the logits come from the worker), with 5 validation keys derived from `AR_SPLIT_SEED` (asserted disjoint
  from the test keys) and MLGym's test keys `PRNGKey(0..4)`. `AR_METRIC val_return=` and `AR_TEST test_return=`
  are written by the parent; the spec's `selection {test_scored: true, selection_split: validation,
  test_metric_name: test_return}` means selection is validation-only and the test metric is sealed.
- **Isolation spec**: `isolation.entry: run_fixed_budget.py`, `args: ["--steps", "{budget}"]`; the runner starts
  the parent directly (no shell), the parent starts `ar_worker.py`. The parent does not import editable code
  (confirmed by reading `run_fixed_budget.py`); the worker imports `helpers`/`policy`/`networks` only after
  checking the device, verifying the data and checking the wrapper keys.
- **Determinism fields**: `cudnn_benchmark: false`, `deterministic_algorithms: true`, `cublas_workspace_config
  ":4096:8"`, `pythonhashseed "0"`, `deterministic_warn_only: false`, `dataloader_workers: 0`, `threads: 4`;
  the worker sets `XLA_FLAGS --xla_gpu_deterministic_ops=true`, `XLA_PYTHON_CLIENT_PREALLOCATE=false`,
  `TF_CUDNN_DETERMINISTIC=1` before importing JAX; `seed_env` is `AR_TRAIN_SEED`/`AR_SPLIT_SEED`.
- **Task semantics**: the pinned `rlMetaMaze.yaml` / `gymnax 0.0.9 MetaMaze-misc` pays +10 on goal, has no
  step penalty, `max_steps_in_episode = 200`, and `done` only at the time limit; on a goal the **agent position
  is re-sampled and the goal stays fixed** (`meta_maze.py`: `goal=state.goal`; the task yaml says "The goal
  position remains fixed during an episode"). The port's graded-count conclusion is correct; the report's
  "the goal is re-drawn each time" wording is wrong (m3), in the report and in the frozen spec/README (deferred
  to c8 because it would change the committed pin).
- Data binding: `run_fixed_budget.py` and `ar_worker.py` both call `ar_data.verify(...)` on the nine-file
  snapshot (`ar_data` exit 5 before training on a changed snapshot); the parent verifies before starting the
  worker and the worker before importing the editable network. The tamper test in the suite covers it.

## 4. Pins, budget and environment — independently recomputed

Every value in the report's §8 was re-derived on TASL-2 from the **committed** tree (committed blobs / clean
tree) and from the host, not copied from `pins.json`:

| field | report | independently recomputed |
|---|---|---|
| `node_spec_sha256` (loader canonical `raw_sha256`) | `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9` | **equal** (YAML→`json.dumps(sort_keys, separators, ensure_ascii=False, default=str)`→sha256) |
| spec raw sha256 (YAML bytes) | `d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59` | **equal** (`git cat-file blob HEAD:…`) |
| `committed_pin_sha256` (18 frozen files, no data link) | `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db` | **equal** (independent sorted-JSON canonicalisation of the 18 committed blob sha256s) |
| `deployed_pin_sha256` (with `data` link; information only) | `1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7` | **equal** (18 + `data: link:/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze`) |
| `edits_manifest_sha256` | `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2` | **equal** (committed blob; `measured: false`) |
| `data_manifest_sha256` | `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000` | **equal** (host data root, captured manifest) |
| env `venv_jax` freeze | `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9` (56 packages, Python 3.12.16) | **equal** (host freeze file; 56 lines, Python 3.12.16) |
| `node ar_isolated` = master | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` | **equal** (committed blob and on-disk master) |
| frozen entry count / expanded files | `frozen_entry_count_committed 14`; 18 committed files | **equal** (15 `frozen_paths` − `data/` = 14; expansion = 18) |

- The four edits (declared, `measured: false`): **E1** `config.yaml` lr `5e-04→2e-04` (both lines;
  `9aacd7fd…`), **E2** `5e-04→1e-03` (same lines, so E1/E2 are alternatives; `ff4cd594…`), **E3**
  entropy `0.05→0.01` (`c76634e9…`), **E4** `networks.py` `nn.relu→nn.tanh` at the 4 hidden-layer sites of
  actor and critic (`ec73a85a…`). Manifest schema `trackg_representative_edits/v1`, `measured: false`,
  `node_spec_sha256 d97bb182…`, `run_budget {steps, 2000000}`, baseline/E-code states. The synthetic smoke and
  the real-data smoke apply exactly these diff bytes (run-record `diff_sha256` equals the committed E-file
  sha256 for E1–E4; code states equal the manifest's). Declared S1.1 interaction E2×E3; composability test
  covers E1+E3, E1+E4, E2+E3, E2+E4, E3+E4 (E1+E2 conflicts).
- The first manifest attempt (declared with Python 3.10) was moved aside, not deleted:
  `/home/dowling/r1_engineering/metamaze_20261125/moved_aside/manifest_first_attempt_py310.json` exists; its
  baseline raw code state equals the final one while the normalised (AST-based) state differs — consistent with
  the report's Python-version explanation. The final manifest was declared with the Python 3.12 environment.
- Metric/regex fields match the spec: `^AR_METRIC val_return=(\S+)$`, `^AR_TEST test_return=(\S+)$`,
  `^step \d+ loss (\S+)$`, `^AR_STEPS env_steps=(\d+)$`; `val_return` maximise; `test_scored: true`; no
  wall-clock key. The four representative edits are declared, composable as stated, and none is expected to
  diverge (the synthetic NaN-network diff covers the divergence class).

## 5. Data preparation, licence and download-only provenance — verified

`prepare_data.py` is a one-off `setup_command` (never part of a run): it GETs exactly nine files at
`raw.githubusercontent.com/facebookresearch/MLGym/9d40c1b5…/` — the task config `configs/tasks/rlMetaMaze.yaml`
and `data/rlMetaMazeMisc/{evaluate.py,requirements.txt,src/__init__.py,src/config.yaml,src/helpers.py,
src/networks.py,src/policy.py,src/train.py}` — checks each sha256 and size against values pinned in the frozen
script, writes the hashed manifest last, makes the directory read-only, refuses a non-empty `--out` without a
manifest and requires `--out` under `$AR_TRACKG_DATA_ROOT`. The manifest also records the two requirements
files' sha256 and the resolved package versions; `ar_data.verify` re-checks every listed file's size/sha256, the
node name/schema and that no unlisted file exists — but **not** `source.packages` (so a GPU-host setup with a
different jaxlib build yields the same nine asset hashes and a different `data_manifest.json` sha; the report
§5 says this explicitly).

I re-fetched the nine pinned URLs today (GETs piped) and reproduced the pins exactly:

| file | sha256 (script / manifest / report) | bytes |
|---|---|---|
| `rlMetaMaze.yaml` | `45104e08cfcf81ad1de7567a9c2b0eaab2580adba4600a8e8603337da5884d82` | 4,249 |
| `evaluate.py` | `00ea0abc4223fb605b645ab7e73acec0634b18bc6198599bd0579f8f5ed07315` | 4,111 |
| `requirements.txt` | `6b90179a69d2bc321b83c8fa2c5539066b3affa648f6b81902062d945271f731` | 70 |
| `__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `config.yaml` | `f91f5586ff587cb72afb2c5add2e37c6c98e487ef2c82d20016b9cb545e420eb` | 860 |
| `helpers.py` | `b9e0e07b8020323e892d08ba5ad231d95a2b8c3fcbcf35186bc0a5d8c1099859` | 2,186 |
| `networks.py` | `bc527dbaf530be2c573fd9b69ccbf3cbf9fd9a7b853fb791ef69cc73a4edd424` | 3,238 |
| `policy.py` | `755d8ec938c2baaa8163306de8ad84263091bcf30b4e9c99badc5cfe682f2ee6` | 15,369 |
| `train.py` | `22f37c40c509a7583916c4fed9af01b414105793fb8f5a41d52f1ba3333a8bbf` | 2,118 |

The TASL-2 data root `/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze` holds exactly those
nine files (`32,201` bytes total) plus the 4,226-byte `data_manifest.json`
(sha256 `e2338195…` = the report and captured manifest), all read-only (`dr-xr-xr-x`, files `-r--r--r--`). The
report's §5 wording "(9 files, 32,201 bytes)" for the data root counts the nine downloaded assets — the
directory actually holds ten files including the manifest (m7).
`LICENCES.md` (frozen) records MLGym CC-BY-NC-4.0 with attribution and the port changes, the gymnax/gymnax-blines
Apache-2.0 parts, the MIT boundary for the port-written files, and that the downloaded snapshot is CC-BY-NC 4.0
material **downloaded, never redistributed** and outside the repository; the branch contains no task data. The
MLGym-in-MIT-tree licensing conflict is the pre-existing suite issue (U1 §3), not a new decision here. The node's
tests generate their own synthetic snapshot and never read task data (the new test also asserts no `.csv/.npy/
.npz` under the node).

## 6. Tests and checklist-E CPU smoke — records verified against the host

All test runs are captured; I read each captured log and the host's final copies (identical, §7), and re-read
the host run records for the smoke:

| check | captured result | verified |
|---|---|---|
| static port tests (5 MLGym nodes, kit branch, torch 3.12, `-k "not smoke"`) | **32 passed, 2 skipped, 5 deselected** in 10.77 s | counts and skips consistent (5 smoke tests deselected; the 2 skips are the new JAX-gated metamaze tests) |
| new node tests incl. synthetic-snapshot smoke (JAX env, `-k metamaze`) | **9 passed**, 30 deselected, 81.14 s | 9 = 5 node-parametrised static/scope/compose/manifest/metric-helper + wrapper-key + task/suitability + tamper + synthetic smoke |
| isolation core (delegated cgroup, `AR_TEST_CGROUP_PARENT`) | **27 passed, 1 skipped**, 14.24 s | matches the accepted TASL-2 host-check count pattern |
| whole `tests/trackg -k "not smoke"` on the kit branch (torch 3.12) | **339 passed, 1 failed, 24 skipped, 11 deselected** in 48.18 s | matches |
| the same suite at pristine base `c025f89a` (`/tmp/base_c025f89a`, torch 3.12) | **333 passed, 1 failed, 22 skipped, 10 deselected** in 44.90 s, **same failure** (`test_trackg_review_round2.py::test_child_that_leaves_the_group_but_not_the_session_is_killed`, `child.pid` absent) | base worktree exists at `c025f89a`, clean; the failing test file is unchanged by the kit commit → pre-existing host race, not a kit regression. +6 passes/+2 skips/+1 deselected = the new node's tests exactly |

**Checklist-E CPU smoke on the real (downloaded, pinned) snapshot, full 2,000,000-step budget, seeds
8001/8001, delegated systemd cgroup (`CHECKLIST_E_PASSED_CPU_REAL_DATA mlgym_metamaze`, EXIT=0)** — re-read
from the host's nine run records; every value matches the report's §7 table:

| run | decision | diff | outcome | val_return | elapsed (s) |
|---|---|---|---|---|---|
| `s000_baseline` | baseline | — | ok | **8.703125** | 55.837 |
| `s001` | not_run_refused | frozen path | `scope_violation` (refused before execution) | — | — |
| `s002` | discarded_divergent | NaN network | `non_finite_loss` (returncode 4) | — | 63.127 |
| `s003` (E1 through the stub manager) | discarded | E1 | ok | 7.062500 | 57.698 |
| `E1` | — | applied (sha `9aacd7fd…`) | ok | 7.062500 | 60.218 |
| `E2` | — | applied (`ff4cd594…`) | ok | 8.062500 | 60.310 |
| `E3` | — | applied (`c76634e9…`) | ok | **2.929688** | 57.103 |
| `E4` | — | applied (`ec73a85a…`) | ok | **15.468750** | 54.937 |
| `B2` baseline repeat | — | — | ok, **same value as s000** | **8.703125** | 75.544 |

Every executed record has a complete `run_record.json`, `isolation.effective: true`, `waivers {}`,
`exceptions []`, `frozen_files_changed []`, **`frozen_files_checked: 19`** (18 committed files + the `data`
link), `frozen_pin_sha256 == deployed pin 1eaaeac3…`, `node_spec_sha256 d97bb182…`, `gpu_uuids []`,
`cpu_list [0,1,2,3]`, external cgroup `run-r935856…scope`, worker sandbox with `cgroup.kill.empty_after: true`,
`ptrace_scope: 1`, `process.killed_with: null`, `CUDA_VISIBLE_DEVICES: ""`, `AR_DEVICE cpu`, and code/diff
states equal to the committed manifest. The smoke's work copies are the **committed bytes** (checked
`config.yaml 6416a530…`, `networks.py 6b3013a6…`, `policy.py b3c992bf…`, `ar_worker.py b66d1f1d…`,
`LICENCES.md 421a4231…`, `README.md 155f8aee…`, `run_fixed_budget.py f00cd743…` against the HEAD blobs; the
first run started after the commit at 04:47:57 PST, run records 04:49–04:56). The `data` link in the work
copies points at the pinned data root.

- **Sealed discipline**: `sealed.test_return` exists in every executed host `run_record.json`, and the
  manager-view ledger, `smoke_summary`/`records.json` and the memo have **zero** `sealed` occurrences
  (`grep -c sealed smoke_ledger.jsonl` = 0); each executed result channel has **exactly one** `AR_METRIC
  val_return=` and one `AR_TEST test_return=` line, and no log contains either pattern (and no carriage
  returns; 0 CRs, 947 finite `step … loss …` lines). The manuscript does not reproduce the sealed values.
- **Fixed-seed determinism at the recorded seeds**: `B2` reproduces `s000` to the digit (8.703125); this is
  CPU evidence only — GPU determinism is G.1b's, as the report says.
- **`determinism.not_forced`**: the record's list is `["cudnn.benchmark=False", "dataloader_workers",
  "torch.set_num_threads", "torch.use_deterministic_algorithms(True)"]`; the captured shim file carries the
  three torch settings with reason `torch_absent: ModuleNotFoundError`, and `dataloader_workers` is added with
  reason "advertised via AR_NUM_WORKERS only". This differs from the report's sentence ("the shim records four
  entries as not_forced with reason torch_absent") — m5.
- **Cap inconsistency**: the report §7 (and `real_smoke.py`'s docstring/§10) say the smoke ran under
  `systemd-run --scope -p MemoryMax=16G`, but every run record's
  `isolation.limits.external_limit` says "systemd-run --user --scope -p MemoryMax=8G …" — that string is
  hardcoded in `real_smoke.py` (apparently copied from the isolation-test command) and is not the actual
  parent. The journal shows the delegated scope `run-r935856…scope` consumed the smoke and its cgroup is the
  recorded parent, so the cgroup isolation is real; the recorded cap label and the report disagree (m6; no
  waiver, no impact on validity, fix the string or the report).
- Nothing in these records is a GPU run, a census, a noise floor or a campaign/label measurement; the report
  claims none.

## 7. Report and captures accuracy — verified

- Report sha256/size/lines as above; untracked and not on paper `main`; captures 42/42 byte-identical to the
  host capture tree; `SHA256SUMS` verifies rc 0 and all 41 entries match; `SHA256SUMS` sha `f5ee03bc…`.
- Every number I checked in the report matches a capture or the host: branch/tip/base/push, single commit,
  23 files/+2,574/−6, clean-except-data-link status, the 18-entry frozen table and all pins
  (`d97bb182…/d46dee59…/759d6bf0…/1eaaeac3…/6de5741f…/e2338195…/630ed6e1…/37d99ab0…`), the freeze content,
  the nine data pins/sizes, the test counts, the nine smoke rows (values, elapsed, outcomes), the E1–E4 code
  states and diff shas, the tamper/scope/NaN checks, the MountainCar and MetaMaze probe numbers and the
  published baselines, the `AR_STEPS env_steps=2000064` value and the wrapper-key/data-link/candidate-record
  tests. The report's own claims "no data committed", "no test-based selection", "sealed value not copied into
  the memo", "no PR/merge", "nothing pushed to paper main", "no GPU/U2/census/lease" are consistent with what I
  see.
- **No overclaim of measurement found.** The report explicitly says no GPU job, no U2 census, no G.1b/noise
  floor, no D21/D28, no label campaign; it flags the real risks (branch/node naming, MountainCar screening,
  download-only egress, budget estimate, eval cost, sealed containment, pre-existing full-suite failure, the
  14-vs-18 frozen-entry reading, and that U2/G.1b are the lead's next steps). The GPU-host `data_manifest.json`
  difference is disclosed in §5 (but needs to be carried into the §8 pin block/G.1b spec — m8).
- **Suitability/noise-floor read.** The smoke's validation metric responds to the declared edits (E3 2.93,
  E4 15.47 vs 8.70; E1 = s003 7.06; E2 8.06) and B2 = s000 exactly, which is promising for D28 liveness — but
  this is a port smoke at one seed pair on CPU, not a noise floor; the 30-seed D21/460-run measurement is
  G.1b's and nothing here should be read as an effect estimate. Under `R1-T1-D21-SCOPE`, D21 does not gate T1
  entry into G.5 (determinism PASS does); the funnel still reports the noise floor.
- Minor accuracy items found are m1–m10 (none changes a verdict or a pin): candidate numbering not in the
  PLAN row; the omitted `third_party/mlgym/README.md` change in §2's file list; the MetaMaze goal/agent
  re-spawn wording; MountainCar's "5 × 10M per checkpoint"; the not_forced attribution; the 16G/8G cap label;
  the data-root file count; the §8 CPU-manifest caveat; the budget cross-check attribution; and the
  test-log/setup-log evidence gaps plus the host capture-assembler drift.

## 8. Findings (no BLOCKING, no MAJOR)

- **m1 (MINOR, numbering/authority, paper side; frozen comment deferred to c8).** The status line and §1 call
  this "R1-T1-NODE-EXPANSION candidate 3". PLAN row line 1516 lists the four candidates **unnumbered**
  ("MLGym MountainCarContinuous or MetaMaze, MLGym Titanic, 1GC-7RC ETTh1, 1GC-7RC Forest Cover (AG News as
  reserve)"), and the "candidate 3" label is the lead's parallel-kit order (Titanic = 1, ETTh1 = 2, this kit =
  3). Say that ("candidate 3 in the lead's parallel-kit order") rather than implying the PLAN numbers it. The
  same label is in the frozen spec header/description and the node README — **do not** churn those now (c8).
- **m2 (MINOR, accuracy, paper side).** Report §2 describes the 23 files as "the new node, its spec and the
  suite test extension"; the commit also updates `third_party/mlgym/README.md` (+2/−1: "four"→"five" Track G
  nodes and the `mlgym_metamaze` inventory row). The change is related and benign, but it should be listed (it
  is a surveyed-branch change, not a node-file change).
- **m3 (MINOR, task semantics, paper side; frozen wording deferred).** §3 and the node README/spec say the
  **goal** is re-drawn on success ("the goal moves on each success"). The pinned environment and task yaml say
  the opposite: on a goal the **agent is re-spawned at a random position and the goal remains fixed during the
  episode** (`gymnax/environments/misc/meta_maze.py`: `goal=state.goal`; `rlMetaMaze.yaml`: "The goal position
  remains fixed during an episode"). The graded-count conclusion is unaffected (multiple goals per episode,
  +10 each, no step penalty) — the probe's 0–70 returns prove it — but the sentence should be corrected
  paper-side; the frozen `README.md`/spec wording would change the committed pin, so it is deferred (c8).
- **m4 (MINOR, accuracy, paper side).** §3.4 says "MLGym trained 5 × 10M steps per checkpoint for the 33.8
  mean". The pinned `rlMountainCarContinuous` config has `num_train_steps: 20000000`, and `train.py` trains
  five checkpoints, each for the full `num_train_steps` — i.e. 5 × 20M, not 5 × 10M (10M is the MetaMaze
  config and the port's own §4 statement about MetaMaze). The rejection conclusion is unaffected.
- **m5 (MINOR, wording, paper side).** §7's determinism paragraph says "the shim records four entries as
  not_forced with reason `torch_absent` (… `dataloader_workers`)". The shim file has **three** torch settings
  (`cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`, `torch.set_num_threads`), all
  `torch_absent: ModuleNotFoundError`; the run record's `not_forced` list adds **`dataloader_workers`** with
  reason "advertised via AR_NUM_WORKERS only". The record's four-name list is right; the attribution is not.
- **m6 (MINOR, evidence metadata, paper side + evidence root).** §7, `real_smoke.py` and §10 say the smoke ran
  under `-p MemoryMax=16G`, but every run record's `isolation.limits.external_limit` string says
  `MemoryMax=8G` (hardcoded in `real_smoke.py`, apparently copied from the isolation-test command). The
  delegated scope and cgroup are real (journal + `cgroup_parent`), so this is a label/metadata inconsistency,
  not a missing cap; fix the string (or the report) and re-capture. No waiver, no effect on the smoke's
  isolation verdict.
- **m7 (MINOR, wording, paper side).** §5 says the data root holds "(9 files, 32,201 bytes)"; the directory
  holds ten files — the nine downloaded assets (which sum to 32,201 bytes) plus `data_manifest.json` (4,226 B,
  its own sha256 given). Say "nine downloaded assets (32,201 B) plus `data_manifest.json`". Same nuance in the
  README §2 table ("9 files, sha256-pinned").
- **m8 (MINOR, pin-block caveat, paper side).** §8 lists `data_manifest_sha256 = e2338195…` among the "pins and
  fields for the U2/G1b spec" without the caveat that it is the **TASL-2 CPU** setup value. §5 correctly says a
  GPU-host setup produces a different manifest sha (the jaxlib build differs, and `ar_data.verify` does not
  check `source.packages`). Put the caveat in §8 and require the U2/G1b spec to carry its own host's manifest
  sha; pinning `e2338195…` on the GPU host would STOP the run.
- **m9 (MINOR, wording, paper side; frozen README deferred).** §4 (and the frozen README) say "the parent
  cross-checks the step counter against the node's budget". The cross-check is the **harness outcome
  classifier's** (`outcome.classify_run`: `steps >= budget`, `budget_not_reached` otherwise), while the
  worker enforces the exact rounded count (`total_steps == expected_steps`, exit 3) and the parent checks its
  `--steps` against `AR_BUDGET_*`. The mechanism is present and correct; the attribution should say so.
- **m10 (MINOR, evidence hygiene, paper side + evidence root).** (i) The captured pytest logs are
  summary-only: no command, rootdir, interpreter or date (the report's §7 table has the commands); the base row
  also omits the log's "10 deselected" (`333 passed, 1 failed, 22 skipped, 10 deselected`). (ii) No capture of
  the setup output ("nine fetches, pinned sha256/size confirmed") is kept — I independently re-fetched and
  matched all nine, so the claim holds, but a one-line setup log should be kept. (iii) The host capture
  assembler `capture_all.sh` has a leftover line writing `test_logs/pytest_port_1gc.log` for a test file that
  does not exist (`tests/trackg/test_port_1gc.py` absent), and that log is absent from the captured set —
  evidence of script drift; no cited artefact is affected and the 42-file set is complete and checksummed, but
  the assembler should be re-run/cleaned so the capture can be reproduced byte-for-byte.

## 9. Conditions before the U2 census and the G.1b spec

- **c1.** This acceptance is recorded before any census. No U2/G.1b run before m1–m10 are applied or
  explicitly waived (all are paper-side, evidence-root or frozen-wording; the frozen-file items m1/m3/m9 are
  deferred to c8), and never before c2–c4.
- **c2.** U2 on TASL-2 must run the standard CPU checklist-E/stub-manager smoke at the full 2,000,000-step
  budget, in a pinned JAX environment, with a CPU list, a memory cap, `CUDA_VISIBLE_DEVICES` empty and a
  delegated systemd scope; record the host, CPU list, wall times and every run's `run_record.json` with
  `isolation.effective: true`, `waivers {}`, `exceptions []`, `frozen_files_checked: 19`, the `not_forced`
  list (`["cudnn.benchmark=False", "dataloader_workers", "torch.set_num_threads",
  "torch.use_deterministic_algorithms(True)"]`, reasons as in m5) and a fixed-seed repeat. Set
  `measured_run_seconds` from its own census records and the timeout = 3 × the slowest of those
  (R1-G1B-TIMEOUT; smoke records excluded) — note the chunk schema requires `measured_run_seconds` in
  (0, 300]; the smoke's worst full-budget record was 75.5 s, so a quiet host should fit, else a reviewed schema
  change is needed. No budget/spec change after the census without a new review (checklist A).
- **c3.** Recompute and record on the census host: `node_spec_sha256 d97bb182…`, spec raw `d46dee59…`,
  **committed pin `759d6bf0…`** (clean tree, no `data` link), deployed pin `1eaaeac3…` (with the link; not the
  census pin), `edits_manifest_sha256 6de5741f…`, `ar_isolated 37d99ab0…`, the host's own freeze sha and the
  **host's own `data_manifest_sha256`** (`e2338195…` is the TASL-2 CPU value; a GPU-host setup will differ —
  m8). The chunk deployment must run the node's `setup_command` so `node_dir/data` exists (the chunk's
  `check_node_pins` verifies `data/data_manifest.json`), and the chunk must carry `device: "cpu"`, no GPU UUID,
  `n_edits: 4`, `timeout_factor: 3.0`, `stop_on_timeout: true` (R1-G1B-TIMEOUT: the first T1 run that reaches
  the declared timeout is a STOP for the author).
- **c4.** Confirm and record on the census host that the baseline runs under the forced deterministic settings
  and that a fixed-seed repeat is identical (observed at 8001/8001 on CPU: B2 = s000 = 8.703125) or record the
  difference; if the node cannot run deterministically on the host, the port must say so and a re-review is
  required before any G.1b chunk. GPU determinism stays a G.1b measurement, not established here.
- **c5.** The new G.1b spec/note (D21 protocol, 460 runs for this node, seeds, 40 GPU-h expansion cap) is
  published by the coordinating chat only after c1–c4, is itself independently reviewed and launch-checked,
  uses a new run id, and cites the pins above and the measured timeout.
- **c6.** The appendix/funnel and the new note must carry: (i) the **suitability record** — MountainCarContinuous
  rejected (two-mode solved/not-solved; MLGym baseline sd > mean; fixed-budget probe 512/512 unsolved; the
  report's budget wording corrected per m4) and MetaMaze ported (graded +10 goal count, headroom below the
  published 15.734 mean; probes are engineering probes, CPU, 1–2 eval seeds, not a noise floor); (ii) the
  **licence record** — MLGym CC-BY-NC-4.0, gymnax/gymnax-blines Apache-2.0, the downloaded snapshot never
  redistributed, the port-written files under the repository MIT, no author/legal line yet; (iii) the
  **task-surface deviation** — one model per run instead of MLGym's five, validation keys derived from the
  split seed instead of MLGym's in-training evaluation, 5 keys × 256 environments for validation and for the
  sealed test, and a budget counted in environment steps, not FLOPs (an edit may change compute per step);
  (iv) the **threat model** — the worker (which imports the editable network) receives observation batches and
  can answer the parent's logits requests differently from its trained model, the data are read-only but the
  same uid can restore the bits, the budget bounds environment steps, and the sealed test return is in the run
  records only (never the manager view or the memo); the S1 audit must read diffs for data access; (v) the
  **limits** — no GPU, no U2, no G.1b/noise floor/D21/D28 yet, and under `R1-T1-D21-SCOPE` D21 does not gate T1
  entry into G.5 (the funnel reports the noise floor regardless); (vi) the **data caveat** — `e2338195…` is
  the TASL-2 CPU manifest, the census host records its own, and the GPU-host setup will produce a different
  `data_manifest.json` sha (m8).
- **c7.** Keep the task snapshot out of the repository, bundles and reports beyond the hash record; leave the
  data root read-only; the census must fetch the pinned source (hash-checked) and refuse a different revision;
  run `prepare_data.py` with the pinned JAX environment so the manifest's `source.packages` are the declared
  ones; do not copy the nine files or the manifest contents into any branch or capture beyond the hashes
  already kept.
- **c8.** The pins in §4 are the accepted ones. Any change to a committed/frozen kit file after this review —
  including the frozen spec/README wording of m1 ("candidate 3") and m3 (the goal/agent re-spawn sentence) or
  any README/LICENCES/worker comment — changes the committed pin and requires a full pin re-derivation and a
  new review before U2. m2, m4–m8 and m10 are to be applied to the paper-side report/captures and the
  evidence root (pin-neutral); m6/m10(iii) are evidence-root fixture fixes. `tests/trackg/test_port_mlgym.py`
  is not in the node's frozen pin but is part of the surveyed branch, so changing it should be re-reviewed.

## 10. What this review does not establish

No measurement, no GPU time, no U2 census, no G.1b noise floor/D21/D28, no GPU determinism verdict, no
label/evidence use and no Track G readiness. I did not re-execute the tests or the smoke (read-only review):
their logs, run records, host data, the pinned upstream source and the host capture tree were verified for
integrity and cross-checked against the report, and I re-derived the pins, the canonical spec hash, the
18-file committed pin, the edits/data/freeze hashes and the nine upstream file hashes independently. The
files under `third_party/mlgym/` and the pinned MLGym snapshot are treated as external, untrusted data; they
were used only to check the port's stated semantics and pinned hashes. The sealed test return exists and is
correctly contained in the run records; its values are deliberately not reproduced here. No legal opinion is
given on MLGym's CC-BY-NC-4.0 or the MLGym-in-MIT-tree licence boundary.

**AI-assisted: DeepSeek Harness reviewer (`metamaze-kit-reviewer`), delegated by the lead, 25 Nov 2026.
ENGINEERING_ONLY. Read-only review; the only file written in any repository is this review.**
