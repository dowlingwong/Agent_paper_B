# Track G port kits on the isolated runner, with the port decisions (17 November 2026)

**Status.** ENGINEERING_ONLY: nothing was measured. The independent review record is
`docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md` (added on this branch after the review). Written by the Mac-desk agent (Claude), AI-assisted.

**Authority.**
- PLAN row R1-TRACKG-PORT-DECISIONS (1)–(3) (on `main` `50176481`): the MLGym subtree with a CC BY-NC 4.0 LICENSE and a
  root scope line; House Prices from the user's Kaggle file via `--from-file`, with its hash recorded; the imdb baseline
  frozen, reviewed and disclosed.
- R1-HARNESS-ISOLATION: the kits run on the isolated runner. The core unit is
  `docs/r1/reports/HARNESS_ISOLATION_20261117.md` on paper branch `mac-harness-isolation-report-20261117` (READY 60;
  not on this branch), harness `mac-harness-isolation-20261117` @ `68cdd1a`.
- Queue of 17 November 2026, item (2).

**What came before.** The three port kits were accepted as U3 units on 17 November (READY 56–58; reports
`TRACKG_U3_PORT_{AUTORESEARCH,MLAB,MLGYM}_20261117.md`). In those kits the editable code ran in the frozen wrapper's
process. This unit moves each node onto the isolated runner and applies the port decisions. The U3 reports remain the
reference for data, budgets, licences and declared edits, except where this report changes them.

## 1. Harness branches

Each branch is based on its accepted U3 tip and merges the isolation core (`68cdd1a`). `src/` equals the core in all
three; the kit-side changes are under the node directories, `configs/trackg/nodes/` and `tests/trackg/`, plus, for
MLGym, `third_party/mlgym/` and the root `README.md`/`LICENSE`.

| Suite | Branch | Base (U3 tip) | Tip |
|---|---|---|---|
| MLGym | `mac-trackg-iso-mlgym-20261117` | `334c89c` | `061d638` |
| MLAgentBench | `mac-trackg-iso-mlab-20261117` | `8596a0e` | `0aae2f6` |
| autoresearch | `mac-trackg-iso-ar-20261117` | `08d0650` | `5d3dccc` |

Full shas are in the review record.

## 2. How every node now runs

Each node's spec has an `isolation` block. Each node directory holds:
- the frozen **parent** `run_fixed_budget.py`, which is the runner's entry. Its first statements make the process
  non-dumpable and open the result channel. It checks the data, makes the split, holds every label it scores, starts
  the worker, computes the metric and writes the one `AR_METRIC` line (and for test-scored nodes the one `AR_TEST` line)
  to the result channel;
- the frozen **worker entry** `ar_worker.py`, the only process that imports editable code. It answers the parent's
  requests (`train`, then `logits` or `fit_predict` or `act_logits`) through a socket pair. It never sees the result
  channel;
- the shared files `ar_parent.py` (budget, seeds, worker calls, array checks), `ar_isolated.py` (the node library;
  byte-identical to the core's master copy), `ar_data.py` (hashed data manifests) and, for the step-loop nodes,
  `ar_fixed_loop.py`; plus node-specific frozen helpers (Breakout's `policy.py`, `helpers.py`, `evaluate_policy.py`;
  autoresearch's `prepare.py` and `ar_budget.py`).

What crosses the channel, per node. For the classification and regression nodes the parent sends no label it scores:
no validation or test label, and no metric. For autoresearch the scored targets are the next input tokens, which the
worker necessarily receives in `x`; that is inherent to language-model evaluation, and it is why that node has the
causality probe and the repeat check.

| Node | Worker receives | Worker returns | Parent computes |
|---|---|---|---|
| `mlgym_cifar10`, `mlgym_fmnist`, `mlab_cifar10` | budget, train seed, training and validation indices | validation and test logits (float32, in order) | accuracies |
| `mlab_imdb` | the same | the same | accuracies |
| `mlab_ogbn_arxiv` | budget, train seed (official split; train.py gets a copy with validation and test labels masked to −1, but the full labels stay in the worker's memory and on disk) | logits for the validation or test node ids | accuracies |
| `mlgym_houseprice` | train seed; train, validation and test row indices | predictions for the three row sets | RMSEs |
| `mlgym_breakout_minatar` | budget, train seed; then observation batches, frame by frame | policy logits | the rollout (environment, keys, action sampling, sums) on CPU JAX, and the returns |
| `autoresearch_fixedtokens` | budget, train seed; then validation input tokens, batch by batch | `model(x)` logits into a buffer the parent owns (CUDA IPC on a GPU, a memfd sealed against resizing on the CPU) | bits per byte from its own targets and byte counts, the causality probe (exit 9) and the repeat check (exit 10) |

## 3. The port decisions

**(1) MLGym licence (MLGym branch).**
- The four MLGym nodes and their specs moved to `third_party/mlgym/{nodes,configs/trackg/nodes}`.
- `third_party/mlgym/LICENSE` is MLGym's own CC BY-NC 4.0 text at commit `9d40c1b5` (copied by the port; the kit
  reviewer could not compare it with upstream offline).
- `third_party/mlgym/README.md` lists the nodes and states the scope: the material adapted from MLGym is CC BY-NC 4.0;
  the parts MLGym took from gymnax and gymnax-blines (Breakout's PPO code) are Apache-2.0, with the licence text in
  `third_party/mlgym/LICENSE-APACHE-2.0` (kit review round 2, N-c); files written for this
  repository (parents, workers, the node library, setup scripts) stay under the repository's MIT licence.
- The root `LICENSE` and `README.md` each gained one scope statement saying the same. These are the only base files
  changed. The t0 identity test now allows those two files to differ from the base by added lines naming
  `third_party/mlgym/`, and still fails on any other change (checked).
- Each node's `LICENCES.md` states the scope and lists which files are adapted and which are written by the port.

**(2) House Prices from the user's Kaggle file (MLGym branch).**
- `prepare_data.py` downloads nothing. A first setup needs `--from-file <train.csv>`; the spec's `setup_command` reads
  it from `$AR_HOUSEPRICE_TRAIN_CSV`.
- At first setup it checks the table's shape (1,460 rows × 81 columns, with `Id` and `SalePrice`; not re-checked on a
  re-run or by the parent, which check the hashes) and records the sha256 and md5 in the data manifest's source (`provided_by: "user download, passed with --from-file"`).
- A re-run accepts only a directory whose manifest records the user's download with those hashes, and a `--from-file`
  given again must be the same file (kit review round 1, M1).
- A manifest marked `synthetic` skips the source check; only the port tests write such manifests, and the run then
  prints `synthetic (port tests only; not the task data)`, which the census must refuse.
- Every run checks the manifest's source and refuses any other non-synthetic source. It prints
  `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…` for the census record; the comparison with MLGym's forwarded
  copy is for information only.

**(3) imdb baseline frozen and disclosed (MLAgentBench branch).**
- The editable `train.py` of `mlab_imdb` was written by the port; the suite ships only a skeleton.
- Its sha256 `01dcb7c4352d4c80495856542683c1c02412fc2da5824c41503e31283215a50a` is recorded as `BASELINE_SHA256` in
  `nodes/mlab_imdb/LICENCES.md`. A port test fails if `train.py` differs from it, as does the declared-edits manifest
  test. The kit reviewer confirmed both by mutation and reviewed the baseline itself (correct; one cosmetic point:
  truncation drops `[SEP]` on long reviews). A coordinated change of `train.py`, `LICENCES.md` and a re-declared
  manifest would still pass the tests; only the census's committed `frozen_pin_sha256` and code-state hash catch it.
- **Disclosure:** the census funnel and the paper's appendix must say, for `mlab_imdb`: "The mlab_imdb baseline
  (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton for this task." Neither document
  exists yet; whoever writes them must carry this sentence.

**(4) Timeout** is implemented in the core (3 × the census-measured baseline time; a measured timeout is the proposal's
failure). The kits need the census's measured run time per node.

## 4. Changes in the autoresearch node from the kit review

- **Shared buffer without expandable segments (B1).** The spec's isolation environment sets
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` for training, and it reaches the parent too. torch 2.6 cannot
  share expandable-segment memory with a process in another PID namespace (it needs `pidfd_getfd` on the non-dumpable
  parent). The parent therefore turns expandable segments off before it allocates the shared logits buffer; it does no
  training. **Untested here (no GPU): the census GPU smoke (`port_smoke_gpu.py`) must pass before this node is used.**
  A failure to share the buffer would currently end the run as the proposal's runtime failure, not as an
  infrastructure failure; the smoke precondition covers that. The kit reviewer suggested a self-check (look up the
  buffer's segment in `torch.cuda.memory_snapshot()` and fail clearly if it is expandable); it was not added because it
  cannot be tested here.
- **Validation read first (M3).** The parent reads every validation batch before it starts the worker. Without the
  worker sandbox (a `no_worker_sandbox` waiver), the editable code could otherwise swap the scored text in between.
- **Fixed evaluation batch size (M4).** The parent uses `EVAL_BATCH_SIZE = 16`, the baseline's `DEVICE_BATCH_SIZE`,
  not `train.py`'s value. 16 divides the 10,240 validation rows, so every row is scored, the same rows `evaluate_bpb`
  scores for the baseline. The parent prints `AR_INFO eval_rows=… eval_batch_size=…`.
- In the suite, M3 and M4 are checked by a source-order test (and the parent probes, `test_wrapper_metric_is_frozen` through `ps.run_parent`, check the printed batch size). The
  behavioural evidence is the kit reviewer's scratch probes: on `4b831e5` a shard swap and a different
  `DEVICE_BATCH_SIZE` both give the honest run's `val_bpb` (round 1: they did not).
- **`shared_dev_shm: true`.** torch keeps its CUDA IPC reference counters in `/dev/shm`, so this node opts out of the
  private `/dev/shm`. Its runs record the exception and are always `effective: false`; see §6.

## 5. Tests

| Suite | Port tests | `tests/trackg` (rest) |
|---|---|---|
| MLGym | `test_port_mlgym.py`: 30 passed | 1 failed: the known t0 environment failure |
| MLAgentBench | `test_port_mlagentbench.py`: 22 passed | same |
| autoresearch | `test_port_autoresearch.py`: 29 passed | same |

These counts are for `a4b4537` (MLGym) and `4b831e5` (autoresearch), plus the text-only core merge. The round-2 notes
`061d638` (a licence file) and `5d3dccc` (an exit code) were followed by the static, manifest and scope tests.

Each suite's synthetic smoke runs its nodes through the runner on synthetic data, with the worker sandbox (on this
root test container with the `root`, `ptrace_scope` and, without `AR_TEST_CGROUP_PARENT`, `no_cgroup` waivers). The
probes (forgeries, budget exits, causality and repeat checks) run the frozen parent directly with a result channel
and a worker process, but without the sandbox (`ps.run_parent`), so they test the kit's own checks. The kit reviewer
reproduced the counts and mutation-checked several tests: the imdb freeze, the static checks, and the parent's repeat
check (M5's new probe fails when the check is removed).

## 6. Threat model of the kits after isolation

**Closed for every node** (by the core, given `effective: true`; autoresearch is never `effective: true` because of
`shared_dev_shm`, item 5, so for it this holds except for that channel): forged metric lines from the editable code, in or out
of its process; a second metric line; a rewritten log; tampering with the frozen parent, the node library or the
frozen data checks during a run; surviving the timeout; reaching other runs.

**Still open:**
1. **Labels on disk are readable (all nodes except Breakout).** The worker's sandbox binds the node's data directory
   read-only, and every data directory holds the validation and test labels: `test_y.npy` for the image and imdb
   nodes, the full `y` for ogbn, `SalePrice` of every row for House Prices, and the validation shard for autoresearch.
   No classification or regression parent sends a scored label to the worker (autoresearch: see §2), but editable code can read the file and return logits or predictions
   built from the labels. Some workers also load test labels into memory without needing them (cifar, imdb, ogbn).
   For autoresearch an edited `train.py` can also read the validation parquet directly and train on it, which
   bypasses the loader's refusal of the validation split (exit 8).
   Closing this needs a per-node layout in which the worker's data hold only the training split (for example, the
   parent writes the training arrays into the worker's working copy and the data directory is not bound). **Author
   decision:** whether to require that before T1, or to rely on the declared-edit review and the S1 audit reading every
   diff for label access.
2. **Breakout's evaluation episodes are recognisable.** `AR_SPLIT_SEED` reaches the worker (the environment allow-list
   keeps `AR_*`), and MLGym's test keys `PRNGKey(0..4)` are public constants. A policy could plan against the parent's
   rollout.
3. **No causality or repeat probes in the MLGym and MLAgentBench nodes.** Unlike autoresearch, none of their parents
   checks that the worker answers evaluation requests as a fixed model would (no permutation, repeat or causality
   probe), so a worker could answer validation and test requests differently from the model it trained.
4. **autoresearch: answers that differ from a fixed model.** The causality probe and the repeat check narrow this; they
   do not close it.
5. **autoresearch: `shared_dev_shm`.** This reopens a cross-run channel, so the node's runs are always `effective: false`.
   **Author decision:** accept the exception for T1 with disclosure, or require a memfd-only path. The CPU path already
   uses a memfd sealed against resizing, but full-size logits through host memory are large: 16 × 2,048 × 8,192 float32 is 1 GiB per
   batch.
6. **The budget is not enforced against an adversarial edit.** Step and token counting runs in the worker, next to
   the editable code: an edit can add updates another way (a second optimizer, manual parameter updates) or read the
   data files directly, beyond what the frozen loop or loader counts. Compute per step is editable too, so the budget
   fixes steps or tokens, not FLOPs (as in the U3 reports). The timeout bounds the time; the declared-edit review and
   the S1 audit are what catch such edits.
7. **CUDA paths are untested on this host**: autoresearch's CUDA IPC across the PID namespace (with B1's fix), Breakout's
   GPU worker with the CPU-JAX parent, and the torch nodes on GPU. The census GPU smoke covers them.

## 7. Steps for the experiment agent on Ada

1. Check the core's host conditions (core report §3, READY 60), including a sandboxed smoke whose record shows
   `effective: true`.
2. Per node, run `setup_command` with `AR_TRACKG_DATA_ROOT` outside the repository.
   - For House Prices, set `AR_HOUSEPRICE_TRAIN_CSV` to the user's Kaggle `train.csv`. A data directory from the old U3
     setup (MLGym's copy) is refused: move it aside.
   - Record each `data_manifest.json` sha256.
3. Run `port_smoke_gpu.py` per node, each with its own Python environment (Breakout has a separate JAX environment),
   with `--gpu-uuid` (not for House Prices), `--cpus`, `--memory-limit` and `--runs-root` outside the repository. It
   runs through the runner with the worker sandbox. Set `AR_TEST_CGROUP_PARENT` to the delegated cgroup. **The smoke
   itself does not check isolation:** `port_support.limits()` waives `root`, `ptrace_scope` and `no_cgroup` when their
   condition is missing, and `check_smoke` does not look at `effective`. So check every run record yourself:
   `isolation.waivers` must be empty and `effective` true, except for autoresearch, where `effective` is false by
   design and `exceptions` must be exactly `["shared_dev_shm"]`. **autoresearch must pass this smoke before any use.**
   Refuse any run whose log carries the `synthetic` marker.
4. The census commits each node's `frozen_pin_sha256` and measured baseline run time.
