# Track G U3 port kit — suite MLAgentBench (17 November 2026, round 8)

**Status.** Port kits for the three MLAgentBench T1 candidates of the Ada census plan (cifar10, imdb, ogbn-arxiv), for
the experiment agent to deploy and smoke-test on Ada. ENGINEERING_ONLY: nothing was measured. Independent review:
see `docs/r1/reviews/TRACKG_U3_PORT_MLAB_REVIEW_20261117.md` once filed (round 1 NOT ACCEPTED; round 2 ACCEPTED with
four minor findings and four notes; round 3, which reviewed the answers to those together with changes shared with the
other two suites after the autoresearch review, NOT ACCEPTED: editable evaluation code still ran after the real
`AR_METRIC` line; round 4 NOT ACCEPTED: a partial line left before the seal swallowed the real result line, and a
tensor subclass returned by `predict_logits` ran editable code inside the frozen accuracy; this round answers both and
states the threat model plainly; round 5 ACCEPTED with text findings, answered here together with two code changes
shared after the other suites' reviews: no torch dispatch mode may be active during the frozen argmax and accuracy, and every line `emit` writes starts with a newline; round 6 ACCEPTED; round 7 narrows that mode check to
dispatch modes after the MLGym and autoresearch reviews found that it refused an ordinary `torch.set_default_device`
edit; round 7 ACCEPTED with a text finding (a mode active during training can hide a non-finite loss), now in the
threat model; round 8 draws the frozen batch order on the CPU, after the MLGym review found that an edit setting the
default device to CUDA would break it in the frozen sampler). Written by the Mac-desk agent (Claude), AI-assisted.

**Authority and inputs.**
- R1-TRACKG-PORT-OWNER and R1-TRACKG-LICENCES, on `main` `26177d82` and `author-decisions-20261117b` @ `33c82351`.
- Port checklist: `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; this branch carries its **section F (Licence and
  provenance)** in `b715e110` (the same commit as on the autoresearch branch), moved after section E in this round.
- Candidates: `docs/r1/reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md` and the licence audit
  `U1_LICENCE_AVAILABILITY_20261117.md` §4 (both on `ops-tasl-20261116`).
- Suite: MLAgentBench, https://github.com/snap-stanford/MLAgentBench, `5d71205cc20a8e95d43aa7cb7120e89ca3323e31`
  (the HEAD U1 §4 records). Its `LICENSE` is MIT with the unfilled template line `Copyright (c) [year] [fullname]`.
- Harness: `r1-local-trackg-v2-20261114` @ `717ad835`.

**Harness branch.** `mac-trackg-port-mlab-20261117b` of the `autoresearch_harness` repository, based on `717ad835`, tip `8596a0ec730b4924e031adf90cb0c38a9a897399`. It only adds files under `nodes/mlab_*/`, `configs/trackg/nodes/` and `tests/trackg/`; no existing harness file changes. The first three commits are round 1 (as on `mac-trackg-port-mlab-20261117`), then round 2 (`b77e68a`), round 3 (`4659b83`), round 4 (`b634596`), round 5 (`5563fa3`), round 6 (`1db6847`), round 7 (`666f3a7`) and round 8:

- `6cf1f2f` trackg U3 port kit, suite MLAgentBench: mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv
- `cb1796f` trackg U3 port kit (MLAgentBench): shared port test support in step with the other suites
- `fbecd13` trackg U3 port tests: manifest reproduction across Python minor versions
- `b77e68a` trackg U3 port kit, suite MLAgentBench, round 2: review round 1 fixes and R1-TRACKG-LICENCES
- `4659b83` trackg U3 port kit, suite MLAgentBench, round 3: review round 2 minors and the changes shared after the autoresearch review
- `b634596` trackg U3 port kit, suite MLAgentBench, round 4: review round 3 fixes
- `5563fa3` trackg U3 port kit, suite MLAgentBench, round 5: review round 4 fixes
- `1db6847` trackg U3 port kit, suite MLAgentBench, round 6: shared fixes after the other suites' reviews
- `666f3a7` trackg U3 port kit, suite MLAgentBench, round 7: the shared mode check refuses only torch dispatch modes
- `8596a0e` trackg U3 port kit, suite MLAgentBench, round 8: frozen batch order drawn on the CPU

## Nodes

| Node | Task | Budget | Selection / sealed test | Split |
|---|---|---|---|---|
| `mlab_cifar10` | cifar10, 10-class images | 1,950 steps | `val_accuracy` / `test_accuracy` | 45,000 / 5,000 drawn from train by the split seed; suite test set of 10,000 |
| `mlab_imdb` | imdb, binary sentiment | 1,000 steps | `val_accuracy` / `test_accuracy` | 22,500 / 2,500 drawn from train by the split seed; suite test set of 25,000 |
| `mlab_ogbn_arxiv` | ogbn-arxiv, 40-class nodes | 356 steps | `val_accuracy` / `test_accuracy` | official split by year; the split seed has no effect |

The editable path of each node is `train.py` (model, optimizer, schedule, loss, preprocessing); the loop, the step
budget, the data, the split and the metric are frozen (`run_fixed_budget.py`, `ar_fixed_loop.py`, `ar_data.py`).

**`mlab_cifar10`.** The suite's own baseline: the LeNet-style CNN, SGD (lr 0.1, momentum 0.9), batch 128,
cross-entropy, normalisation by 0.5/0.5 (`benchmarks/cifar10/env/train.py`). Budget: the suite's 5 × 390 batches =
1,950 steps; over the 45k training split this is about 5.6 epochs.

**`mlab_imdb`.** **The suite has no runnable baseline** (its `train.py` has `model = None`); the baseline is the port's,
for the task's stated goal: `distilbert-base-uncased` with a fresh 2-class head, the first 256 of the 512 stored
tokens, AdamW at lr 2e-5 with weight decay 0.01 **except on biases and on every LayerNorm weight** (round 2: the filter
now also matches DistilBERT's `sa_layer_norm` and `output_layer_norm`; round 1 decayed them), linear decay to zero,
clipping at 1.0, bf16 autocast, batch 16. The budget of 1,000 steps (about 0.7 epoch) is **an estimate** of about
1 min of training on an L40S; the census measures it. Runs set `HF_HUB_OFFLINE=1`.

**`mlab_ogbn_arxiv`.** The suite's baseline: a 2-layer MLP on node features (hidden 16, batch norm, dropout 0), Adam at
lr 1, batches of 1,024 training nodes, no schedule (the suite builds a ReduceLROnPlateau scheduler and never steps it).
**Deviations from the suite** (round 2 states all three, in `train.py`'s docstring, `LICENCES.md` and the yaml):
1. 40 outputs instead of the suite's 172 (the frozen evaluation needs the 40 classes);
2. **batch norm sees only the 1,024 training seeds**: the suite trains on `batch.x` of a NeighborLoader subgraph (the
   seeds plus sampled 2-hop neighbours, 30 per hop) and takes the loss on the seeds, so its batch statistics include
   mostly non-training neighbours;
3. **the last partial batch of each epoch is dropped**: the suite has 89 batches per epoch (the last of 829 nodes), the
   frozen loop 88 full batches, so 356 steps are about 4.05 epochs of full batches (not "4 epochs of 89 batches").

The editable code receives the full feature matrix and edge list on the device; labels in `info` are those of the
training nodes only (validation and test masked to -1). That masking is not a barrier: in-process code can read
`data/y.npy` (see the limits below).

## Budget enforcement and its limits (round 1, finding 2; round 2, findings 1 and 4)

`ar_fixed_loop.train_fixed_steps` draws exactly `--steps` batches from the seeded sampler and calls
`optimizer.step()` once per batch. `build_optimizer` must return a `torch.optim.Optimizer`; a post-step hook counts its
`step()` calls, and the run fails with exit 3 unless the count equals the budget (the harness classes this
`divergent` / `nonzero_exit` with return code 3). An edit that calls `step()` of that optimizer inside
`training_step` is therefore refused.

**Not enforced** (the editable code runs in the wrapper's process; the round-1 report's "the budget cannot be bypassed"
was wrong):
- the hook counts `step()` calls, not updates: an optimizer (or subclass) whose single `step()` makes several updates —
  Lookahead or SAM written inside `step()` — passes; so does tampering with the optimizer's hook registry or calling the
  unwrapped `step`;
- a second optimizer or manual parameter updates inside `training_step` (several passes per batch), an EMA copy used by
  `predict_logits`;
- patching `ar_fixed_loop` at run time; printing a forged `step`/`AR_` line and ending the process before the wrapper
  prints, or writing one from a thread it started that runs concurrently with the result lines (the harness takes the
  last metric match). Round 4: both evaluations (validation and test, which call the editable `predict_logits`) and the
  accuracies now run before the first result line, which only formats Python floats, and just before it the wrapper
  points descriptors 1 and 2 at /dev/null (`ar_data.seal`), so a thread of the editable code can no longer print into
  the log (a reviewer's thread forgery won 3 of 5 runs on a reordered copy without it); in round 3 the test evaluation
  ran after the real `AR_METRIC` line, so a `print` in `predict_logits` appended a forged line that the harness scored
  (review round 3, finding 1). The wrapper's own lines go through `ar_data.emit` and the run ends with `os._exit(0)`,
  so they can be neither rewritten through `sys.stdout` nor followed by an `atexit` line. Round 5: `seal()` first
  writes a newline to the saved descriptor, so a partial line left by the editable code (`"AR_METRIC …\nZ"`) can no
  longer swallow the real line (review round 4, finding 1); `predict_logits` must return a plain `torch.Tensor` (a
  subclass is refused, exit 4) and the frozen argmax and accuracy run with torch-function dispatch disabled, so no
  editable `__torch_function__` subclass or mode runs inside them (round 4, finding 2); the loss must be a plain tensor
  too, and the loss lines go through `emit`, so a `sys.stdout` filter cannot hide a NaN loss; the data are checked again
  before the result lines. Round 6: no torch dispatch mode may be active when the frozen argmax and accuracy run (exit 4;
  a dispatch mode left active had rewritten `aten.eq`, review round 5, finding 1); torch-function modes are not refused,
  since the arithmetic runs with torch-function dispatch disabled and an ordinary edit can leave one active
  (`torch.set_default_device`; refusing it, as the first version of this check did, failed such an edit — found in the
  MLGym and autoresearch reviews); every line `emit` writes
  starts with a newline, so a partial line cannot hide a NaN loss line either (found in the MLGym review); a patch of
  torch itself (`torch.Tensor.__eq__ = …`) stays possible (threat model). What stays possible is in the threat model (common section);
- reading `data/*.npy` directly (including validation and test labels);
- restoring the write bits of the shared data (the owner can), or keeping state under a setup-only subdirectory or
  outside the data directory, which `verify` does not check (see Data in the common section).

One case fails a legitimate edit: a subclass whose `step()` calls `super().step()` is counted twice if an instance of
the parent class was created earlier in the run (torch's hook wrapping); such a run fails as divergent. The loop fixes
the batches drawn and the `step()` calls it drives; the declared-edit review and the S1 audit should read any proposal
that adds updates of its own as "train longer", which is visible in the diff.

## Representative edits (declared before any measurement; re-declared in round 2)

The round-2 changes to `train.py` (imdb, ogbn), to the setup command, `frozen_paths`, the infrastructure patterns and
the description changed the spec and baseline hashes, so all three manifests were re-declared with `scripts/trackg_declare_edits.py` under Python 3.12
in `b77e68a9` (rounds 3 and 4 change only frozen file contents, which the manifests do not hash: re-declaring
reproduces them byte for byte; round 5 likewise); the round-1 manifests are kept at `representative_edits/superseded/manifest_round1.json`. The
cifar10 diffs are unchanged; the imdb and ogbn diffs have the same changes with new context lines.

| Node | Manifest sha256 | E1 | E2 | E3 | E4 |
|---|---|---|---|---|---|
| `mlab_cifar10` | `a4099110d75c7396dc7e297b7978efa9ca27cfcdc4b89a139ed7f82b27c6fe49` | lr 0.1 → 0.05 | batch norm after both convs | Adam 1e-3 + cosine schedule | lr 0.1 → 1.0 (likely divergent) |
| `mlab_imdb` | `49a0c06c655a0e29845980f1dbd4bc08387cb97a1398b6d4d37357393668cb63` | lr 2e-5 → 3e-5 | lr 2e-5 → 1e-4 | 10 % linear warmup | batch 32, 128 tokens |
| `mlab_ogbn_arxiv` | `0bfd9206979e9c8b66e44f96b685000ca6e499090bddd2f518171adda998a3bf` | lr 1 → 0.5 | lr 1 → 0.01 | hidden 256, 3 layers, dropout 0.5 | 2-layer GraphSAGE with lr 0.01 |

Edit sha256 values (from the committed manifests):

- `mlab_cifar10`: E1 `345f0bcd6585491bad429fcfad08a89c186e1d032304be6d2a4c4a6f5cc3f341`; E2 `39fd85d00eb2ff90e98524505e5c1932ecb5df522b7e3167306a66a4caea8a5c`; E3 `4d25e5997d8e8dd3061a67b6959514d1696573617ec0ecebe22babf03d93c0a3`; E4 `261b474a67ed6ce97eef4c50fa90e9ea2e586d4fa985beceae5266725e11f56a`
- `mlab_imdb`: E1 `67fa8741b2b48ab8be0a6c267eb1d28281098eefe0f43d1847dfe686c0f97ed6`; E2 `bd23dd4a88d3abffaff6b2c3071ca5674584099323a152d6e0fb17f7c2664c54`; E3 `09a516efe90c3dc6a2696b59177bcc29ad0986ab266fcddd4dc30f8423f2f5d7`; E4 `fca63fff7702966ea9e5c76b83cd6d3c56b063856ded14180fed9bd8d42656a3`
- `mlab_ogbn_arxiv`: E1 `77c4dbb32e09ac9094cddc283d530f8c14e3312abcaaaa6b6e17d773d4a08bfb`; E2 `c8d2b67f3ae9b78ec0cb3214fe9497d2c519e08ffdfa3406db5411735bdb15f9`; E3 `ffa1b54ab8949a904344819d91b2ab2c3d25d4f95587da431880f42865336b46`; E4 `ed265c6151cf91ba7b7e453284f495a67b22da7b5b2d3bb5ca26b58f943151e5`

**Pair composability (round 1, finding 4).** Each ordered pair applied in sequence with the harness's `apply_diff`
(`tests/trackg/test_port_mlagentbench.py::test_interacting_edits_compose` checks the listed pairs in both orders):

| Node | Pairs that compose (both orders) | Pairs that conflict (both set the same line) |
|---|---|---|
| `mlab_cifar10` | E1+E2, E1+E3, E2+E3, E2+E4, E3+E4 | E1+E4 (two learning rates) |
| `mlab_imdb` | E1+E3, E1+E4, E2+E3, E2+E4, E3+E4 | E1+E2 (two learning rates) |
| `mlab_ogbn_arxiv` | E1+E3, E2+E3, E3+E4 | E1+E2, E1+E4, E2+E4 (each sets the learning rate) |

To get there, the baselines were re-laid without changing behaviour: in ogbn the optimizer constant `LEARNING_RATE`
moved next to `build_optimizer`, away from the model constants; in imdb `MAX_LEN` moved next to `_inputs`, away from
`LEARNING_RATE`.

**Which composing pairs interact (round 2, finding 2).** Applying cleanly is not enough: cifar10 E3's Adam ignores the
learning rate that E1 and E4 set (E1+E3 and E3+E4 run exactly as E3 alone), and ogbn E4's GraphSAGE has its sizes
hard-coded, so E3's `HIDDEN` / `NUM_LAYERS` / `DROPOUT` are dead code after it (E3+E4 runs exactly as E4). The pairs for
S1.1 interaction runs, where both edits act, are: cifar10 E1+E2, E2+E3, E2+E4; imdb E1+E3, E1+E4, E2+E3, E2+E4, E3+E4;
ogbn E1+E3 (learning rate × capacity), E2+E3. The test's `INTERACTING` table lists exactly these. ogbn has no edit
expected to diverge.

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

Python 3.12, torch 2.6.0 on CPU, numpy 2.5.4, transformers 4.49.0 (no GPU on this host): `tests/trackg/test_port_mlagentbench.py` at the tip: **21 passed** — static (result lines only through `emit`, `seal()` right before `AR_METRIC`, nothing after it, `finish()` after `main()`), manifest (re-declaration reproduces the three manifests byte for byte under 3.12), frozen-path refusal, the interacting pairs, the output seal against a partial line and a writing thread (three runs each), the refusal of a tensor subclass from `predict_logits` (an accuracy computed through such a subclass stays correct) and of a dispatch mode left active (a torch-function mode left by `set_default_device` is accepted), a loss line emitted after a partial line, and the synthetic smoke for the three nodes, whose table is identical to rounds 2–7. In round 2 the same tests passed on a copy with `data` links in place, as after setup (round 1, finding 1), and the whole `tests/trackg` directory without the other two suites' files gave 187 passed, 1 failed — `test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`, which fails the same way on the unchanged base `717ad835` in this environment.

The table is from the synthetic smoke on random data of the real shapes, reduced budgets (cifar10 30 steps, imdb 6,
ogbn 20) and seeds 8001/8001; the numbers say nothing about the task. The imdb smoke seeds its tiny random DistilBERT
(round 1, finding 10), so its rows reproduce.

**`mlab_cifar10`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_accuracy 0.086667 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |
| baseline repeat | - | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.0982 | test_accuracy 0.13 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.096 | test_accuracy 0.133333 | dataloader_workers |

**`mlab_imdb`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.4864 | test_accuracy 0.48 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_accuracy 0.52 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.4864 | test_accuracy 0.49 | dataloader_workers |
| baseline repeat | - | ok | 0.4864 | test_accuracy 0.48 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.4864 | test_accuracy 0.49 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.49 | test_accuracy 0.455 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.4872 | test_accuracy 0.48 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.4904 | test_accuracy 0.49 | dataloader_workers |

**`mlab_ogbn_arxiv`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 0.0375 | test_accuracy 0.04 | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | test_accuracy 0.0475 | dataloader_workers |
| E1 (stub manager) | applied | ok | 0.0225 | test_accuracy 0.0125 | dataloader_workers |
| baseline repeat | - | ok | 0.0375 | test_accuracy 0.04 | dataloader_workers |
| E1 (on baseline) | applied | ok | 0.0225 | test_accuracy 0.0125 | dataloader_workers |
| E2 (on baseline) | applied | ok | 0.0325 | test_accuracy 0.02 | dataloader_workers |
| E3 (on baseline) | applied | ok | 0.015 | test_accuracy 0.0225 | dataloader_workers |
| E4 (on baseline) | applied | ok | 0.025 | test_accuracy 0.04 | dataloader_workers |

## What is not shown here, and the risks to watch on the GPU host

- **GPU and determinism.** Nothing ran on a GPU or under CUDA's deterministic mode. Candidates for an error under
  `use_deterministic_algorithms(True)`: DistilBERT's SDPA backward (imdb), `nll_loss`/`cross_entropy` on CUDA,
  `index_add_` in ogbn E4. An op that raises makes the run `divergent`; `deterministic_warn_only: true` for a node is a
  G.1b decision for review, never applied silently.
- **Setup is unexercised.** `prepare_data.py` was not run (no hub or download access from this host). Round 2 makes it
  stricter: `--out` must lie under `$AR_TRACKG_DATA_ROOT` (and the setup command checks the variable is set); a first
  run needs an empty or new `--out`, so a partial earlier attempt is never reused (for ogbn this also avoids `ogb`'s
  `input()` prompt and its `torch.load` of a half-written processed file under torch 2.6's `weights_only` default);
  the manifest is written last and the directory is then made read-only, so accidental writes fail (round 1, finding
  9; the owner can restore the bits); every run refuses files the manifest does not list outside its setup-only
  subdirectories (`torchvision_raw/`, `ogb_raw/`, `pretrained/.cache/`); the imdb dataset revision
  must start with U1's `e628166` unless the author accepts another; torchvision's CIFAR-10 md5 must be the published
  value. `torchvision==0.21.0` (the build for torch 2.6.0), `ogb==1.3.6` and `huggingface_hub==0.36.2` are pinned;
  each `requirements.txt` says to install it in one resolver call.
- **CPU fallback (round 1, finding 8).** When the runner assigns a GPU (`CUDA_VISIBLE_DEVICES` non-empty) and CUDA is
  unavailable, the wrapper prints `AR_INFRA …` and exits 6 before the editable code is imported. The node's
  `infrastructure_log_patterns` entry matches that line only when no `AR_DEVICE` line precedes it, so the same text
  printed later by editable code is not classed as an infrastructure failure, unless it seeks in the log (threat model)
  (checked by hand in review round 2;
  no port test covers the `AR_INFRA` path). `tests/trackg/port_smoke_gpu.py` runs the census-host smoke with the GPU
  given by UUID, which it now requires for every node except the CPU-only House Prices node.

## Open points for the author or coordinator

1. **imdb's baseline is the port's** (the suite ships none): confirm that a port-written baseline is acceptable for a
   T1 candidate, or move imdb to the R1-BX-D12 appendix.
2. **Run length and timeouts (round 1, finding 7).** cifar10 and ogbn keep the suites' own run lengths, which are
   seconds of training, well under R1-BX-D5's 1–2 minutes; start-up and data hashing dominate, so a timeout of 3× the
   measured run is fragile on a shared host. The batch-size caps also let a one-line edit multiply compute per run:
   cifar10 up to 4,096 (32× the baseline's 128), ogbn up to 90,941 (full batch, about 89×), imdb up to 128 (8×). A
   timeout is classed `infrastructure_failure` (re-run, not deduplicated). Options: keep the suite lengths and set a
   node timeout from the largest allowed batch; scale the budgets towards the guideline (a new spec hash and new
   manifests); tighten the caps. Proposed, pending your decision: read an over-compute timeout on these nodes as the
   proposal's cost. The harness currently classes every timeout as `infrastructure_failure` and re-runs it, and a port
   cannot change outcome classes; applying the proposal needs a harness change or a recorded manual reclassification.
3. **Data hashes not known in advance**: the ogbn download has no published archive hash, and distilbert's hub
   revision is resolved at setup. Checklist F leaves these to the census: it records each data manifest's sha256, and
   later setups must reproduce it — a manual comparison; no script checks it.
4. Data licences as U1 records them: CIFAR-10 terms unknown / not stated; IMDb `license: other`, terms unspecified;
   ogbn-arxiv ODC-BY as OGB's page states; distilbert-base-uncased Apache-2.0 per its model card, not covered by U1.
   Data are never redistributed; each node's `LICENCES.md` carries the record.
5. **For the coordinator (harness, outside the port):** the threat model (common section) lists what in-process
   editable code can still do to the log; closing it needs the harness — a separate process for the editable code with
   a result channel it cannot write, the log opened with `O_APPEND` or as a pipe, every descendant killed (a cgroup
   kill: the runner's existing kill of the process group and session misses a child that left the session), and a run with more than one metric match refused (that last rule alone does not catch an early exit
   that leaves a single forged line).
6. The census plan's prerequisites still apply before any Ada GPU job (Paper A status gate U0, the co-tenancy check,
   G.1b on L40S).

## Deployment on Ada (for the experiment agent)

1. Fetch the bundle; check out `mac-trackg-port-mlab-20261117b` in the harness checkout (base `717ad835`).
2. Run the static tests before setup: `PYTHONPATH=src python3 -m pytest tests/trackg/test_port_mlagentbench.py -k "not smoke"`
   (round 2: the tests also pass with the `data` links in place — checked here on a copy with links — but before setup
   is the documented order).
3. Set up one torch environment per host from the three `requirements.txt` files in one resolver call, with the CUDA
   build of torch 2.6.0 for the host; record the versions.
4. With `AR_TRACKG_DATA_ROOT` set outside the repository, run each node's `setup_command` from its node directory;
   record each `data_manifest.json` sha256 in the census.
5. Run `PYTHONPATH=src python3 -m tests.trackg.port_smoke_gpu --node <node> --gpu-uuid GPU-… --cpus … --memory-limit …
   --runs-root <outside the repo> --provisional-timeout …` for each node and check checklist E.

---

Bundle: one bundle for this suite with the paper branch `mac-trackg-u3-mlab-20261117b` (this report, the checklist's
section F and, once the review is accepted, its record) and the harness branch `mac-trackg-port-mlab-20261117b`.
