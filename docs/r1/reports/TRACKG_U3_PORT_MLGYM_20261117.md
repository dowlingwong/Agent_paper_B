# Track G U3 port kit — suite MLGym (17 November 2026, round 5)

**Status.** Port kits for the four MLGym T1 candidates of the Ada census plan (CIFAR-10, Fashion-MNIST, House Prices,
Breakout-MinAtar), for the experiment agent to deploy and smoke-test on Ada. ENGINEERING_ONLY: nothing was measured.
Independent review: see `docs/r1/reviews/TRACKG_U3_PORT_MLGYM_REVIEW_20261117.md` once filed (round 1 was NOT
ACCEPTED; round 2 answered it and was NOT ACCEPTED in turn — forged lines through a forked child, an own `dup` of
the log descriptor or a seek in the log, and a tensor subclass inside the frozen accuracy; a revision of round 2
answered those, stated the threat model plainly and fixed the smaller findings, and was NOT ACCEPTED with three minor
findings — a dispatch mode left active, a partial line hiding a NaN loss line, four threat-model inaccuracies — which
round 3 answered; round 3 NOT ACCEPTED: the new mode check refused an ordinary `torch.set_default_device` edit, which
round 4 answered; round 4 ACCEPTED with notes: the frozen sampler would break under an edit that sets the default
device to CUDA (now drawn on the CPU), and a mode active during training can hide a non-finite loss (now in the threat
model, with `nan_to_num` on the editable loss); this round 5 carries both). Written by the Mac-desk agent
(Claude), AI-assisted.

**Authority and inputs.**
- R1-TRACKG-PORT-OWNER and R1-TRACKG-LICENCES, on `main` `26177d82` and `author-decisions-20261117b` @ `33c82351`.
- Port checklist: `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; this branch carries its **section F (Licence and
  provenance)** in `b715e110` (the same commit as on the other two suite branches), moved after section E.
- Candidates: `docs/r1/reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md` and the licence audit
  `U1_LICENCE_AVAILABILITY_20261117.md` §3 (both on `ops-tasl-20261116`). For "a MinAtar/MountainCar-type RL task" the
  port chose **Breakout-MinAtar**: MountainCarContinuous tends to end solved or not solved, a poor fit for a noise floor.
- Suite: MLGym, https://github.com/facebookresearch/MLGym, `9d40c1b5035202018cd7091fb4e83a9c68b377c0` (10 Aug 2025).
- Harness: `r1-local-trackg-v2-20261114` @ `717ad835`.

**Harness branch.** `mac-trackg-port-mlgym-20261117b` of the `autoresearch_harness` repository, based on `717ad835`, tip `334c89ce0e036022cd1f993830a84809092ca44c`. It only adds files under `nodes/mlgym_*/`, `configs/trackg/nodes/` and `tests/trackg/`; no existing harness file changes. The first two commits are round 1 (as on `mac-trackg-port-mlgym-20261117`); the rest are rounds 2–5:

- `168acb5` trackg U3 port kit, suite MLGym: mlgym_cifar10, mlgym_fmnist, mlgym_houseprice, mlgym_breakout_minatar
- `bfc4624` trackg U3 port tests: manifest reproduction across Python minor versions
- `165788a` trackg U3 port kit, suite MLGym, round 2: review round 1 fixes, R1-TRACKG-LICENCES, and the changes shared with the other suites
- `44c7ee8` trackg U3 port kit, suite MLGym, round 2 (continued): result-line order and seal shared after the MLAgentBench review
- `a6524e6` trackg U3 port kit, suite MLGym, round 2 (continued): review round 2 fixes
- `9c91e39` trackg U3 port kit, suite MLGym, round 3: review round 2 (revised) findings
- `4b03541` trackg U3 port kit, suite MLGym, round 4: review round 3 finding (the mode check refused set_default_device)
- `334c89c` trackg U3 port kit, suite MLGym, round 5: frozen batch order drawn on the CPU (review round 4, note 1)

## Licence: needs an author decision (round 1, finding 4)

MLGym is **CC BY-NC 4.0** (its `LICENSE`, U1 §3). The nodes contain material taken or adapted from it: the CNNs, the
House Prices pipeline and table, and Breakout's `policy.py`, `networks.py`, `helpers.py` and rollout; MLGym's PPO code
is itself adapted from gymnax-blines and gymnax (**Apache-2.0**, per MLGym's README). Each node's `LICENCES.md`
(checklist F) gives the licence, the attribution, the changes and the data record.

**The conflict exists today**, not only if the harness becomes public: the harness repository has an **MIT** `LICENSE`
at its root ("Copyright (c) 2026 Dowling_Wong"), with no scoping note, so the branch places non-commercial files in an
MIT-licensed tree. Each MLGym node's `LICENCES.md` now states that the root MIT licence does not cover the node's
MLGym-derived files. Remedies for the author (the port changes no existing harness file): (a) a licence-scope line in
the root `LICENSE`/`README` excluding `nodes/mlgym_*` (CC BY-NC 4.0, Apache-2.0 parts as stated); (b) keep the MLGym
nodes outside the MIT tree (a separate, non-public directory or repository); (c) drop the MLGym nodes. Use in an
academic paper is non-commercial; CC BY-NC grants no patent rights.

## Nodes

| Node | Task | Editable | Budget | Selection / sealed test | Split |
|---|---|---|---|---|---|
| `mlgym_cifar10` | imageClassificationCifar10 | `train.py` | 7,820 steps | `val_accuracy` / `test_accuracy` | 45,000 / 5,000 drawn from train by the split seed; suite test set of 10,000 |
| `mlgym_fmnist` | imageClassificationFMnist | `train.py` | 9,380 steps | `val_accuracy` / `test_accuracy` | 54,000 / 6,000 drawn from train by the split seed; suite test set of 10,000 |
| `mlgym_houseprice` | regressionKaggleHousePrice | `train.py` | 1 fit (`steps: 1`) | `val_rmse` (min) / `test_rmse` | MLGym's procedure: fixed 20 % test; 12.5 % of the rest as validation, drawn by the split seed (seed 42 = MLGym's files) |
| `mlgym_breakout_minatar` | rlBreakoutMinAtar | `config.yaml`, `networks.py` | 2,000,000 env steps | `val_return` / `test_return` | validation rollout keys from the split seed; MLGym's test keys `PRNGKey(0..4)` |

**`mlgym_cifar10` and `mlgym_fmnist`.** The suite's two-layer CNN with the Hugging Face Trainer's defaults written out:
AdamW at lr 5e-5 (betas 0.9/0.999, eps 1e-8), weight decay 0.01 except on biases, 500 warmup steps then linear decay,
clipping at 1.0, batch 64. Removed: the Trainer's per-epoch evaluation **on the test set** and its reload of the "best"
checkpoint (that selects on test). Budget: the suite's 10 epochs × 782 / 938 batches; the frozen loop drops each
epoch's last incomplete batch. Data: the Hugging Face datasets the tasks load (`uoft-cs/cifar10`,
`zalando-datasets/fashion_mnist`); setup STOPs unless the resolved revision starts with the one U1 observed (`0b27149`,
`531be5e`) or one the author accepts.

**`mlgym_houseprice`.** The suite's pipeline (mean imputation and scaling of numeric columns, "missing" imputation and
one-hot encoding of object columns, Ridge with alpha 0.1), returned unfitted by `build_model(x_train, seed)`;
`transform_target` / `inverse_transform_target` are editable. The frozen wrapper fits once and scores RMSE on the price
scale. The table is MLGym's `_helpers/train.csv`, pinned by sha256 (`1e18addf…a5f929d41`) and md5 (`80ccab65…b5577`) in
`prepare_data.py` and the wrapper. Round 1 reproduced MLGym's baseline test RMSE 30340.111853 exactly with split
seed 42. **The budget does not bound compute** (one `fit` call; see open point 3).

**Seeds and the noise floor (round 1, finding 8).** The training seed reaches only `build_model`, which Ridge ignores,
so with the baseline every seed-to-seed difference comes from re-drawing the 146-row validation set by the split seed
(split seed 42: validation RMSE 30638, test 30340). **If G.1b fixes the split seed, the baseline's noise floor is exactly
zero**; an edit with a seeded estimator (E4's gradient boosting) has training-seed variance. G.1b / D21 should read
House Prices' floor with this in mind.

**`mlgym_breakout_minatar`.** MLGym's PPO (frozen `policy.py`, three marked changes in `train_ppo`: an update callback for
the loss log, in-training evaluation switchable off, the steps taken returned). Editable: MLGym's `networks.py` and
`config.yaml` (without `num_train_steps`, `evaluate_every_epochs`, `num_test_rollouts`, which the wrapper owns). One model
per run, initialised and trained from the training seed exactly as MLGym's first checkpoint (MLGym trains five).
Evaluation: MLGym's rollout (256 environments, up to 999 frames). Budget: 2,000,000 environment steps, **an estimate** of
1–2 min on an L40S; the loop dispatches about 31,250 separate jitted `get_transition` calls from Python, so dispatch
overhead may dominate and the estimate is uncertain. **Changing the budget after the census changes the spec hash**
(`run_budget` and `node_spec_sha256` are in the manifest), so it needs re-declared edits and a new review (checklist A)
(round 1, finding 10). JAX runs in a separate environment: `requirements.txt` is the local CPU check, and **round 2 adds
`requirements_gpu.txt`** (`jax[cuda12]==0.4.35`, the same other pins) for the GPU host.

## Budget enforcement and its limits (round 1, findings 1 and 7)

Image nodes: `ar_fixed_loop.train_fixed_steps` draws exactly `--steps` batches and calls `optimizer.step()` once per
batch. **Round 2:** `build_optimizer` must return a `torch.optim.Optimizer`, a post-step hook counts its `step()` calls,
and the run fails with exit 3 (classed `divergent` / `nonzero_exit`) unless the count equals the budget, so an edit that
calls `step()` of that optimizer inside `training_step` is refused. The wrappers' result lines go through
`ar_data.emit` (Breakout: its own `emit`) to a copy of the output descriptor taken before the editable code is imported,
and every run ends with `os._exit(0)` after them, so they can be neither rewritten through `sys.stdout` nor followed by
an `atexit` line. Every wrapper runs both evaluations (validation and test: the editable `predict_logits`, estimator or
network) and computes the metrics as Python floats before its first result line, so no editable code runs after it (the
MLAgentBench review found a forged line printed by `predict_logits` during the test pass, after the real one); just
before that line it points descriptors 1 and 2 at /dev/null and writes a newline to the saved descriptor (`seal`), so
threads of the editable code cannot print into the log through those descriptors and a partial line cannot swallow the
result line. `predict_logits` and the training loss must be plain `torch.Tensor`s (a subclass is refused, exit 4) and
the frozen argmax and accuracy run with torch-function dispatch disabled and with no torch dispatch mode active (exit 4
otherwise; a torch-function mode an ordinary edit leaves, such as `torch.set_default_device`'s, is not refused, since
disabled dispatch already keeps it out — round 4, finding 1, found that refusing it failed such an edit; review round 2, finding 2, and round 3, finding 1, which also found the two suites' copies of
`ar_fixed_loop.py` out of step: resynchronised); loss lines go through `emit`, and every line `emit` writes starts with a
newline, so a partial line cannot hide a NaN loss line (round 2, finding 4; round 3, finding 2); the data are checked again before the result lines, so a run that changed them fails itself
(finding 3). What stays possible against deliberately adversarial code is in the threat model (common section; finding 1).

**Not enforced** (the editable code runs in the wrapper's process; the round-1 report's "the budget cannot be bypassed"
was wrong): the hook counts `step()` calls, not updates, so an optimizer whose single `step()` makes several updates
(Lookahead or SAM written inside `step()`) passes, as does tampering with its hook registry; a second optimizer or manual
parameter updates inside `training_step`; an EMA copy used in evaluation; compute per step (`CONFIG["batch_size"]` may be up to 4,096, 64× the baseline's 64; see open point 2); patching the
frozen modules at run time; printing a forged `step`/`AR_` line and ending the process before the wrapper prints, or
writing one to the saved descriptor itself (the harness takes the last metric match; see open point 7);
restoring the write bits of the shared data (the owner can); and **reading the task data and the split seed**: the
runner sets `AR_SPLIT_SEED` in the environment and `data/` is readable, so an edit could rebuild the validation rows
(they are in `train_x.npy`; House Prices reads the whole CSV) and fit on them, inflating the selection metric. These are
visible in the diff (mentions of `AR_SPLIT_SEED`, `data/`, `np.load`, `read_csv` in editable files) for the declared-edit
review and the S1 audit. For House Prices and Breakout the budget is the frozen wrapper's single fit / environment-step
count; the same in-process limits apply.

## Representative edits (declared before any measurement; re-declared in round 2)

The round-2 changes to the setup commands, `frozen_paths` (`LICENCES.md`; Breakout's `requirements_gpu.txt`)
and the infrastructure patterns changed the spec hashes, so the four manifests were re-declared with
`scripts/trackg_declare_edits.py` under Python 3.12 in `165788af`; the round-1 manifests are kept at
`representative_edits/superseded/manifest_round1.json`. The diffs are unchanged. Nothing has been measured.

| Node | Manifest sha256 | E1 | E2 | E3 | E4 |
|---|---|---|---|---|---|
| `mlgym_cifar10` | `ff34e96a68696cf2028955c362918a56d840d25fedae584cc99858a4ad698b48` | lr 5e-5 → 1e-4 | lr 5e-5 → 1e-3 | batch norm after both convs | random flip + shift augmentation |
| `mlgym_fmnist` | `8d9c7d831d5fed0418a6eb289457793322c2b811b6a063f54776b317697af62e` | lr 5e-5 → 1e-4 | lr 5e-5 → 1e-3 | batch norm after both convs | random flip + shift augmentation |
| `mlgym_houseprice` | `48d973622888d1d9d2f65bcee2ffba6fe86244c65601efbe19fb18aa951dd30a` | alpha 0.1 → 1.0 | alpha 0.1 → 100 | log1p target | gradient boosting, 300 trees (interacts with E3) |
| `mlgym_breakout_minatar` | `1ab0dacf71c779fbbccfa79f0c52ceb438f82dff9422dd4ceb928ae20dffffdd` | lr 5e-4 → 1e-3 | lr 5e-4 → 5e-3 | tanh hidden activations (`networks.py`) | gamma 0.99, GAE lambda 0.9 |

Edit sha256 values (from the committed manifests):

- `mlgym_breakout_minatar`: E1 `8403016b15959aa480e2f0dd1732b81899f009b452bd1bc9e723e44cd79c22bf`; E2 `e9932b594c9aa78013f5cf248456a6bb760e9e334486f6ccdfafa56f7640b48e`; E3 `ec73a85a98c0690191e22be3cca97106c7daca51ba773ae484f696c01fb9f918`; E4 `089624e9af453e56c3f075c8e50ae1a9bca8ee9e9a5eed6d017d1319c6c20cba`
- `mlgym_cifar10`: E1 `6d806f90feaa95f9d4e8dc9a8da57a9e462ba94299fc764ac16f7fa8c9df153d`; E2 `ecb86f509e7ef414319416299073b97c7ff3a02bdb79e2808f5b25002a720899`; E3 `8b84959a2e3d78bcb982902647433facf64cce3227755c669179bfe375fbfd59`; E4 `58c33a33391a8ce694915334a9d6a069a698742f546aaa9bfcd5f635391ce2fa`
- `mlgym_fmnist`: E1 `6d806f90feaa95f9d4e8dc9a8da57a9e462ba94299fc764ac16f7fa8c9df153d`; E2 `ecb86f509e7ef414319416299073b97c7ff3a02bdb79e2808f5b25002a720899`; E3 `5cc131aa0045c7c1349c9abd437f227abe4000a8e6d0da58f2f51306cac8f75c`; E4 `58c33a33391a8ce694915334a9d6a069a698742f546aaa9bfcd5f635391ce2fa`
- `mlgym_houseprice`: E1 `3ee108ef77b9fd406e1151d2bda768fefb156f3e69ac9ddc3cef59e35635b81c`; E2 `7e4a71a00ce7589f12aa4575e9598a83e91dcba14f8ca85d09e41466b5eb51ad`; E3 `81eaa685ca30cf53ee2655852b9af966d61206f15a733d50ae43b0c826878ebe`; E4 `e9a1e8e9d00413b7b9439d8b5543f1c928a26d67388fd9cc938f044eb855f63f`

**Pair composability and the interaction edits (round 1, finding 9).** Each ordered pair applied in sequence with the
harness's `apply_diff` (`test_interacting_edits_compose` checks the listed pairs in both orders):

| Node | Pairs that compose (both orders) | Pairs that conflict (both set the same line) | Declared interaction for S1.1 |
|---|---|---|---|
| `mlgym_cifar10` | E1+E3, E1+E4, E2+E3, E2+E4, E3+E4 | E1+E2 (two learning rates) | E2 × E3: a 20× higher learning rate with and without batch norm (batch norm tolerates higher rates) |
| `mlgym_fmnist` | E1+E3, E1+E4, E2+E3, E2+E4, E3+E4 | E1+E2 | E2 × E3, as for CIFAR-10 |
| `mlgym_houseprice` | E1+E3, E1+E4, E2+E3, E2+E4, E3+E4 | E1+E2 (two alphas) | E3 × E4 (log target with gradient boosting); E1/E2 (Ridge alpha) are dead code after E4, so E1+E4 and E2+E4 compose but do not interact |
| `mlgym_breakout_minatar` | E1+E3, E2+E3, E3+E4 | E1+E2 (two learning rates); E1+E4, E2+E4 (E4's hunks carry the learning-rate lines of MLGym's `config.yaml` as context; the port keeps MLGym's line order) | E2 × E3 (higher learning rate with tanh activations) |

The test's `INTERACTING` table lists the composing pairs where both edits act (for House Prices: E1+E3, E2+E3, E3+E4).
No image-node edit is expected to diverge: AdamW at 1e-3 (E2) is a standard rate for these CNNs. The checklist's
fourth bullet ("likely to diverge or to interact") is met by the declared interaction pair.

## Design common to the three suite kits

These choices are the same in all three suite kits (MLAgentBench, MLGym, autoresearch).

- **What each node directory holds.** Each node is `nodes/<node>/` plus `configs/trackg/nodes/<node>.yaml` (`trackg_node/v1`; the strict loader accepts it). The node directory holds:
  - the editable baseline;
  - a frozen `run_fixed_budget.py`, which is the run command's entry point;
  - frozen helpers;
  - a frozen `prepare_data.py`, the one-off `setup_command` (only for nodes with task data);
  - `requirements.txt` and `LICENCES.md` (checklist F: licence, source URL and revision, data source and hash, as U1 records them);
  - `representative_edits/E1–E4.diff` with `manifest.json`.

  Every committed file is in either `editable_paths` or `frozen_paths`; a test checks this. `allow_new_files: false`. The editable entries are files, so no frozen script sits in an editable directory.
- **The editable/frozen split for the torch supervised nodes.** Five nodes share this split: MLAB cifar10, imdb, ogbn-arxiv; MLGym CIFAR-10, Fashion-MNIST.
  - The editable `train.py` holds the model, optimizer, schedule, loss and preprocessing. It provides `CONFIG` (`batch_size`, `grad_clip`, `amp_bf16`), `build_model`, `build_optimizer`, `training_step` and `predict_logits`.
  - The frozen `ar_fixed_loop.py` owns everything a diff must not change:
    - exactly `--steps` optimizer steps;
    - the seeds (`AR_TRAIN_SEED`, `AR_SPLIT_SEED`);
    - the training-batch order (a seeded permutation that drops the last incomplete batch of each epoch, drawn on the CPU with a CPU generator, so an edit that calls `torch.set_default_device` neither changes it nor breaks it);
    - a per-node cap on the batch size;
    - the loss log, `step <n> loss <mean over 10 steps>`;
    - the evaluation loop;
    - a post-step hook on the returned optimizer: the run fails (exit 3) unless its `step()` was called exactly `--steps` times (calls, not updates: an optimizer whose single `step()` makes several updates passes);
    - the GPU check: `AR_INFRA` and exit 6 when a GPU was assigned but CUDA is unavailable, before the editable code is imported.
  - `ar_fixed_loop.py` is byte-identical in every node, and a test checks this.
  - **Consequence.** A proposer can change the model, optimizer, schedule, loss, augmentation and batch size; the loop, the batches drawn and the counted optimizer steps are fixed. This is a deliberate narrowing compared with the suites, where the agent may rewrite the whole script. It does not make the budget unbypassable: editable code in the same process can still add updates that do not go through the counted `step()`, keep an EMA copy, patch the loop or read the data files (see each suite's limits).
- **Metric lines.**
  - After training returns, the frozen wrapper writes `AR_METRIC <validation metric>=` and, for test-scored nodes, `AR_TEST <test metric>=`, through `ar_data.emit`: a copy of the output descriptor taken when `ar_data` is imported, before the editable code is. It then ends the process with `os._exit(0)` (`ar_data.finish`; inline in the Breakout wrapper). Every wrapper runs all editable code — both evaluations, which call `predict_logits` (or the editable model, network or estimator) — and computes the metrics as Python floats before its first result line, so nothing editable runs after it; just before that line it points the process's descriptors 1 and 2 at /dev/null (`ar_data.seal`), so a thread the editable code started can no longer print into the log through them; it first writes a newline to the saved descriptor, so a partial line the editable code left cannot swallow the result line. So editable code cannot rewrite these lines by replacing `sys.stdout`, print a line after them from its evaluation code or a thread, or add one from an `atexit` handler. Tests check that no wrapper prints a result line otherwise, that `seal()` immediately precedes the first `AR_METRIC` line, that only result lines follow it, and that `finish()` follows `main()`.
  - `metric_regex` and `test_metric_regex` are anchored on these prefixes. A test checks that no editable file contains `AR_METRIC`, `AR_TEST`, `AR_STEPS` or `AR_TOKENS`.
  - Known limits (checklist B): see the threat model below.
- **What the frozen code guarantees, and what it does not (threat model).** The editable code runs in the wrapper's process, as in the suites. The frozen code fixes the data, the budget it serves, the evaluation and the metric's arithmetic against ordinary edits, and it closes the deliberate forgeries the reviews demonstrated: a line added after the result lines (an `atexit` handler, a `print` in evaluation code, a thread printing through descriptors 1 or 2 — except a write already in progress at the moment of the seal — and a partial line left before them), a rewritten `sys.stdout`, a tensor subclass or a torch-function mode inside the frozen arithmetic (it runs with torch-function dispatch disabled), a torch dispatch mode left active for it (refused, exit 4), extra `step()` calls of the optimizer the editable code returned (not a second optimizer or manual updates), a partial line swallowing a loss or result line (every frozen line starts with a newline), planted data files (refused at the next start; the run that planted them fails its own end-of-run check if it planted them before that check). It does **not** make the metric tamper-proof against deliberately adversarial code. In-process code can still, for example: print a forged result line and end the process before the wrapper prints; write into the log through a descriptor obtained before the seal (the saved descriptor, its own `dup` of descriptor 1, or the log reopened by path); seek in the log, which the runner opens without `O_APPEND`, to overwrite lines or put an infrastructure line at the top; start a thread, a `subprocess` / `multiprocessing` worker or a forked child that changes the data or the log after the end-of-run check, or a forked child that calls `setsid()` and so escapes the runner's post-exit kill of the run's process group and session (or write from any child before that kill runs); patch torch or numpy themselves (for example `torch.Tensor.__eq__ = …`, or an aten kernel through `torch.library`), which rewrites the frozen arithmetic so that the wrapper prints a single genuine but wrong line; hide a non-finite loss from the frozen loss log while training runs (a torch-function or dispatch mode active during training, or a patch to torch; this changes the outcome class of a diverged run, not its metric — and an ordinary-looking edit can do the same by returning `torch.nan_to_num(loss)`, because the divergent class rests on the loss the editable code returns, which matters for the divergence labels); patch frozen modules at run time; or read the task data directly. All of these need deliberate code in the diff. As a reading aid for the declared-edit review and the S1 audit (not a filter: names can be built at run time), look for `os._exit`, `os.fork`, `setsid`, `os.dup`, `os.write`, `lseek`, `/proc/self/fd`, `threading`, `AR_METRIC`, `importlib`, `TorchDispatchMode`, `__torch_dispatch__`, `_python_dispatch`, `TorchFunctionMode`, `__torch_function__`, `torch.overrides`, `torch.library`, `nan_to_num`, assignments to `torch.` / `np.` attributes or `setattr(torch`, `np.load` / `read_csv` / `parquet`, `subprocess`, `multiprocessing`, `ctypes`, and writes to `sys.stdout` without a newline in editable files. Closing them needs the harness, not the port: run the editable code in a separate process with a result channel it cannot write, open the log with `O_APPEND` or as a pipe, kill every descendant (a cgroup kill, since the runner's existing kill of the process group and session misses a child that left the session), and refuse a run with more than one metric match (which alone does not catch an early exit or a rewritten arithmetic that leave a single line) (open point for the coordinator). Until then the declared-edit review and the S1 audit must read proposals for such code.
- **Validation and test.**
  - Test-scored nodes select on validation only (`R1-TRACKG-ROLE`). The suite's test set is the sealed test metric.
  - When the suite has no validation split, the wrapper carves 10 % of the training set as validation, drawn by `AR_SPLIT_SEED`.
  - When the suite has an official split (ogbn-arxiv), or a fixed one (autoresearch's validation shard), the split seed is logged and has no effect.
- **Data.**
  - `prepare_data.py` fetches the data from the suite's public source into `$AR_TRACKG_DATA_ROOT/<node>`, outside the node. It records each file's sha256 and the source revision in `data_manifest.json`, and links that directory into the node as `data` (frozen, `data/`).
  - `--out` must lie under `$AR_TRACKG_DATA_ROOT`, and a first run needs an empty or new `--out`. The manifest is written last; the directory is then made read-only, so accidental writes by a run fail. Not prevented: code running as the directory's owner can restore the write bits (as root the bits do not apply) and rewrite data and manifest together; files under the setup-only subdirectories, and anything outside the data directory, are not checked (a channel for carrying state between runs); on the census host, give the data another owner or a read-only mount, and pin the manifest sha256 after the census.
  - Every run first checks every listed file against the manifest and refuses any unlisted file outside the setup-only subdirectories the manifest names (raw downloads such as `torchvision_raw/`, `ogb_raw/`; frozen `ar_data.py`, identical in all nodes). A run on changed or added data stops with exit code 5. Every wrapper checks the data again after the editable code has run, before the result lines (`AR_ERROR the editable code changed the data:`; autoresearch: `AR_ERROR train.py changed the data:`), so the run that changed them fails itself — unless the change came after that check (a thread or an escaped child), in which case it is the last run before the failing one; a start-of-run exit 5 therefore means an earlier run changed them, and the experiment agent should STOP the campaign there and find that run.
  - Where U1 observed a hub revision, setup STOPs unless the resolved revision starts with it (or with one the author accepts by flag). Other hub revisions are resolved at setup and recorded. The census records each manifest's sha256, which can then be pinned.
  - Data are never redistributed (R1-TRACKG-LICENCES): the nodes and branches hold none, and the tests use synthetic data.
- **Determinism.** The spec defaults are kept (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`, `deterministic_warn_only: false`). No node file sets `cudnn.benchmark = True`; a test checks this. Whether every baseline and edit runs under `torch.use_deterministic_algorithms(True)` on CUDA was not tested here, because the host has no GPU. That check belongs to G.1b on L40S. Candidates to watch are named per suite below.
- **Workers.** `dataloader_workers: 0` and `threads: 4`. The data sit in device memory (or, for autoresearch, in autoresearch's own main-process loader), so no loader worker processes exist. `AR_NUM_WORKERS` is read and logged.
- **Tests.** One shared support module, `tests/trackg/port_support.py`, is identical on all three branches. Each suite has its own test file.
  - **Static tests** run anywhere:
    - the spec loads and has the expected anchors and scopes;
    - every file is in scope;
    - the shared helpers are identical across nodes;
    - the metric lines appear in the frozen wrapper only;
    - the Python files compile;
    - the manifest is complete: 3–5 edits, every `E*.diff` listed with its sha256, spec and baseline hashes current, `measured: false`, and re-declaring the edits reproduces it byte for byte;
    - a one-line diff to every committed frozen file is refused with `scope_violation`, a new file is refused, and an in-scope diff to the editable file is allowed.
  - With the setup's `data` links in place, the support module skips the linked directory (scope, stray-file and copy checks), so the tests also pass after setup.
  - **The synthetic smoke** runs when the node's runtime packages are present. It uses random data of the real shapes, never task data, and a reduced budget. It runs `run_smoke_campaign` with a frozen-path diff, a broken diff (non-finite loss) and E1, then runs every declared edit once on the baseline, then a second baseline with the same seeds. It checks:
    - the baseline is `ok`, the frozen diff is `not_run_refused`/`scope_violation`, and the broken diff is `discarded_divergent`/`non_finite_loss`;
    - every edit applies and runs `ok`, and the repeated baseline gives the same metric;
    - every run record has its fields, there is no `killed_with`, and no `sealed` key appears in the manager view;
    - for torch nodes, `determinism.not_forced == ["dataloader_workers"]` on every executed record, including the stub-manager runs and the repeat baseline;
    - the node's loss, metric, step and test patterns match the baseline log, and the log contains no carriage returns.
- **Order of work (checklist C).** Before each manifest was written, each edit was only applied and run on synthetic random data, to check that it executes; no task data were used. The diffs and manifests were then written with `scripts/trackg_declare_edits.py` and committed. Nothing has been measured.
- **Harness finding: manifests and the Python version.** The harness's *normalised* code-state hash (`baseline_code_state_sha256`, and each edit's `code_state_sha256` and `incumbent_code_state_sha256`) is built from the interpreter's AST. For these nodes it differs between Python 3.12 and 3.13: `ast.dump` changed between the two. The diff hashes and the *raw* code-state hash do not change.
  - The manifests were declared with Python 3.12. Under 3.12 a re-declaration reproduces them byte for byte. Under 3.13 everything except those three fields matches. The tests check both cases.
  - **Consequence for deployment.** Code-state hashes in run records (duplicate detection, and the manifest's baseline hash) are comparable only within one Python minor version. The Ada census and the L40S G.1b should run the harness on the same minor version as each other, preferably 3.12, which matches the manifests. This is a harness property that predates the port, reported here for the coordinator.
- **Census-host smoke.** `tests/trackg/port_smoke_gpu.py` (identical on all three branches) runs the checklist-E smoke with the real data and full budget, seeds 8001, the GPU by UUID (required for every node except the CPU-only House Prices node), a CPU list and the stated memory cap, and a provisional timeout.
- **Runner settings per host (checklist D)** are left to the experiment agent:
  - GPU by UUID;
  - CPU list and memory cap (`external` under Slurm or with an explicit `external_limit`; `rlimit_data` on Ada only if it does not break CUDA's virtual reservations, otherwise `external` with the reason recorded);
  - a provisional timeout for the first, measuring run only;
  - after that, 3 × the measured run time.
- **Python environments.** Runs use `python3` from `PATH`, so each node is run with its suite's environment first on `PATH`; the yaml's `notes.python_env` names it. Breakout-MinAtar needs a separate JAX environment.

## Checks run here

Python 3.12, torch 2.6.0 on CPU, numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1, jax 0.4.35 (CPU), flax 0.10.2, optax
0.2.4, gymnax 0.0.9, tensorflow-probability 0.25.0 (no GPU on this host): `tests/trackg/test_port_mlgym.py` at the tip:
**26 passed** — static (result lines only through `emit`, `seal()` right before `AR_METRIC`, nothing after it,
`finish()` after `main()`), manifests (re-declaration reproduces the four manifests byte for byte under 3.12),
frozen-path refusal, the interacting pairs, the output seal against a partial line (before a loss line and before the result line) and a writing
thread (one run for each of the three `ar_data` nodes; the same check passed in repeated runs before the commit), the refusal of a tensor subclass from `predict_logits` and of a dispatch mode left active, with a torch-function mode left by `set_default_device` accepted (the two image nodes), and the
synthetic smoke for the four nodes. No port test covers Breakout's inline seal (it imports jax at module level; it has
the same newline and descriptor handling). The whole `tests/trackg` directory without the other two suites' files: 193 passed, 1 failed at `165788af` (this host)
and at `44c7ee89` (the round-2 reviewer) —
`test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`, which fails the
same way on the unchanged base `717ad835` in this environment.

The tables are from the synthetic smoke on random data of the real shapes (for House Prices, a random table with a few
of the real column names), reduced budgets (image nodes 30 steps, Breakout 17,000 environment steps) and seeds
8001/8001; the numbers say nothing about the task. The smoke ran in an environment with torch, so Breakout's
`not_forced` there is `dataloader_workers` only; **in the torch-free JAX environment of the GPU host, Breakout's
`not_forced` will be `cudnn.benchmark=False`, `dataloader_workers`, `torch.set_num_threads` and
`torch.use_deterministic_algorithms(True)` (reason `torch_absent`)**, which is expected and explained here and in the
yaml; XLA CPU threads are not bounded by the shim (round 1, finding 6).

**`mlgym_breakout_minatar`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.735156 | test_return 0.738281 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_return 0.482031 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.735938 | test_return 0.73125 | dataloader_workers |
| baseline repeat | - | ok | 0.735156 | test_return 0.738281 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.735938 | test_return 0.73125 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.880469 | test_return 0.827344 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.698438 | test_return 0.641406 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.710938 | test_return 0.711719 | dataloader_workers |

**`mlgym_cifar10`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.098 | test_accuracy 0.116667 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_accuracy 0.086667 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.0974 | test_accuracy 0.093333 | dataloader_workers |
| baseline repeat | - | ok | 0.098 | test_accuracy 0.116667 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.0974 | test_accuracy 0.093333 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.096 | test_accuracy 0.136667 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.1044 | test_accuracy 0.09 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.0984 | test_accuracy 0.116667 | dataloader_workers |

**`mlgym_fmnist`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.0995 | test_accuracy 0.1 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_accuracy 0.113333 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.098667 | test_accuracy 0.093333 | dataloader_workers |
| baseline repeat | - | ok | 0.0995 | test_accuracy 0.1 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.098667 | test_accuracy 0.093333 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.103833 | test_accuracy 0.123333 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.098 | test_accuracy 0.056667 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.0985 | test_accuracy 0.1 | dataloader_workers |

**`mlgym_houseprice`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 14426.4 | test_rmse 15556.7 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_rmse nan | dataloader_workers |
| E1 (stub manager) | applied | ok | 14447.7 | test_rmse 15543.1 | dataloader_workers |
| baseline repeat | - | ok | 14426.4 | test_rmse 15556.7 | dataloader_workers |
| E1 (on baseline) | applied | ok | 14447.7 | test_rmse 15543.1 | dataloader_workers |
| E2 (on baseline) | applied | ok | 29128.7 | test_rmse 29855 | dataloader_workers |
| E3 (on baseline) | applied | ok | 22312.4 | test_rmse 29177 | dataloader_workers |
| E4 (on baseline) | applied | ok | 15058.9 | test_rmse 17115 | dataloader_workers |

## What is not shown here, and the risks to watch on the GPU host

- **GPU and determinism.** Nothing ran on a GPU or under CUDA's deterministic mode. To watch: `cross_entropy` on CUDA
  (image nodes); JAX scatter and reductions under `--xla_gpu_deterministic_ops`. An op that raises is `divergent`; any
  `deterministic_warn_only: true` is a G.1b decision for review.
- **CPU fallback (round 1, finding 5).** When the runner assigns a GPU (`CUDA_VISIBLE_DEVICES` non-empty) and CUDA is
  unavailable (torch) or JAX's first device is not a GPU (Breakout, for example with the CPU jax of `requirements.txt`),
  the wrapper prints `AR_INFRA …` and exits 6 before the editable code is imported. The nodes' `infrastructure_log_patterns`
  entry matches that line only when no `AR_DEVICE` line precedes it, so the same text printed later by editable code is
  not classed as an infrastructure failure. Treat such a run as a STOP for the census. (Editable code that seeks in
  the log can still put the line at the top; see the threat model.)
- **Setup is unexercised** for the image nodes (no hub access here); the House Prices URL was not fetched, but its pinned
  hashes come from the file in a local MLGym clone, and `--from-file` takes that file. Round 2: `--out` must lie under
  `$AR_TRACKG_DATA_ROOT` (the setup command checks the variable is set); a first run needs an empty or new `--out`; the
  manifest is written last and the directory is then made read-only (accidental writes fail; the owner can restore the
  bits); every run refuses files the manifest does not list.
- **Data licences as U1 records them:** CIFAR-10 `license: unknown` on the HF card, no licence to cite; Fashion-MNIST MIT
  (HF card); House Prices: Kaggle competition rules (Ames housing data, De Cock 2011), not relicensed by MLGym; Breakout
  has no data (gymnax, Apache-2.0). Data are never redistributed.

## Open points for the author or coordinator

1. **MLGym licence** (CC BY-NC 4.0 in an MIT-licensed harness tree): choose a remedy (above).
2. **Compute per step and timeouts.** The image nodes' batch cap (4,096, 64× the baseline) and Breakout's editable
   network, `num_train_envs`, `epoch_ppo` and `n_minibatch` let a one-line edit multiply compute per run. A timeout is classed
   `infrastructure_failure` (re-run, not deduplicated). Options: lower the caps (for example 512), set a node timeout from
   the largest allowed configuration, or a frozen compute cap. Proposed, pending your decision: read an over-compute
   timeout on these nodes as the proposal's cost. The harness currently classes every timeout as
   `infrastructure_failure` and re-runs it, and a port cannot change outcome classes; applying the proposal needs a
   harness change or a recorded manual reclassification.
3. **House Prices budget.** The task has no training steps; the budget is one fit and does not bound an edit's compute.
   Options: (a) keep it as a one-fit node with this disclosed; (b) bound compute in the frozen wrapper (an estimator list,
   caps on `n_estimators` / `max_iter`), which narrows the edit surface; (c) move House Prices to the R1-BX-D12 appendix.
4. **House Prices data source** (review round 2, finding 6). R1-TRACKG-LICENCES expects users to download task data
   themselves under the source's terms; the kit fetches MLGym's redistributed copy of the Kaggle table (pinned by its
   hashes). Choose: accept MLGym's copy explicitly, or require the Kaggle download (accepting the competition rules)
   and pass the file with `--from-file`; the pinned sha256 / md5 then confirm it is the same table.
5. **House Prices noise floor** with a fixed split seed is zero for the baseline (above).
6. **Breakout trains one model per run** where MLGym trains and averages five; the floor then reflects one-seed training,
   the intended unit for labels.
7. The census plan's prerequisites apply before any Ada GPU job (Paper A gate U0, co-tenancy, G.1b on L40S).
8. **For the coordinator (harness, outside the port):** the threat model (common section) lists what in-process
   editable code can still do to the log; closing it needs the harness — a separate process for the editable code with
   a result channel it cannot write, the log opened with `O_APPEND` or as a pipe, every descendant killed (a cgroup
   kill: the runner's existing kill of the process group and session misses a child that left the session), and a run with more than one metric match refused.
9. **House Prices synthetic mode.** The wrapper skips the pinned-hash check when the data manifest says
   `synthetic: true` (the port tests' synthetic table). A real setup never writes that; the census should confirm that
   the manifest it records has no `synthetic` key.

## Deployment on Ada (for the experiment agent)

1. Fetch the bundle; check out `mac-trackg-port-mlgym-20261117b` in the harness checkout (base `717ad835`).
2. Run the static tests before setup: `PYTHONPATH=src python3 -m pytest tests/trackg/test_port_mlgym.py -k "not smoke"`.
3. Set up two environments, each from its requirements file in one resolver call: torch (CUDA build of torch 2.6.0) for
   the image nodes and House Prices; JAX from `nodes/mlgym_breakout_minatar/requirements_gpu.txt` (which now pins
   `tqdm`, imported by the wrapper and `policy.py`) for Breakout, first on `PATH` when Breakout runs. Add `pytest` and
   `PyYAML` to the environment that runs `port_smoke_gpu.py`. Record the versions.
4. With `AR_TRACKG_DATA_ROOT` set outside the repository, run each data node's `setup_command` (for House Prices, if
   GitHub is unreachable: `python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice" --from-file <MLGym
   checkout>/data/regressionKaggleHousePrice/_helpers/train.csv`). Record each `data_manifest.json` sha256.
5. Run `PYTHONPATH=src python3 -m tests.trackg.port_smoke_gpu --node <node> --gpu-uuid GPU-… --cpus … --memory-limit …
   --runs-root <outside the repo> --provisional-timeout …` for each node (Breakout with the JAX environment; House Prices
   is CPU-only and may omit `--gpu-uuid`), and check checklist E, with Breakout's expected `not_forced` list above. If
   the census changes Breakout's budget, re-declare its edits and have the change reviewed before G.1b.

---

Bundle: one bundle for this suite with the paper branch `mac-trackg-u3-mlgym-20261117b` (this report, the checklist's
section F, the review record) and the harness branch `mac-trackg-port-mlgym-20261117b`.
