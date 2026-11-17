# Track G U3 port kit — suite autoresearch (17 November 2026, round 5)

**Status.** The port kit for the one autoresearch T1 candidate of the Ada census plan, for the experiment agent to
deploy and smoke-test on Ada. ENGINEERING_ONLY: nothing was measured. Independent review: see
`docs/r1/reviews/TRACKG_U3_PORT_AUTORESEARCH_REVIEW_20261117.md` once filed (rounds 1 and 2 NOT ACCEPTED; round 3
ACCEPTED with six minor findings and two notes, answered in round 4 together with output changes shared with the other
suites; round 4 ACCEPTED with two minor findings and a note about the report's claims, which this round answers in the
report and in `train.py`'s docstring). Written by the Mac-desk agent (Claude), AI-assisted.

**Authority and inputs.**
- R1-TRACKG-PORT-OWNER (the Mac agent writes the port kits) and R1-TRACKG-LICENCES (licence and provenance step;
  datasets never redistributed), on `main` `26177d82` and `author-decisions-20261117b` @ `33c82351`.
- Port checklist: `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; this branch adds its **section F (Licence and
  provenance)** in `b715e110` and moves it after section E in this round.
- Candidate: `docs/r1/reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md` and the licence audit
  `U1_LICENCE_AVAILABILITY_20261117.md` §2 (both on `ops-tasl-20261116`): "autoresearch (short fixed-step variant,
  1 task)".
- Harness: `r1-local-trackg-v2-20261114` @ `717ad835`.

**Harness branch.** `mac-trackg-port-ar-20261117b` of the `autoresearch_harness` repository, based on `717ad835`, tip
`b3a08ff0743fbb58c6f1c9deae7d0350a82f0672`. It only adds files under `nodes/autoresearch_fixedtokens/`,
`configs/trackg/nodes/` and `tests/trackg/`; no existing harness file changes. Commits:
- `9fb6b483` port kit (round 1); `5eac9802` manifest reproduction across Python minor versions (round 1);
- `38854b9e` round 2: the round-1 review fixes and R1-TRACKG-LICENCES (below);
- `4f705e5e` the prepared data directory made read-only after the manifest;
- `735aacca` round 3: the round-2 review fixes (frozen metric with a causality probe, result lines on a saved
  descriptor and `os._exit`, recorded refusals, unlisted data files refused, forked download workers, licence text,
  tests);
- `d6e64927` round 4: the round-3 review minors (probe with infinities and its measured change printed, frozen
  tokenizer, bound cross-entropy, prepare restored, weights unchanged by the evaluation, data re-checked after
  `train.py`, model contract in the yaml, re-declared edits) and the output seal shared with the other suites;
- `b3a08ff0` round 5: the round-4 review minors (contract in `train.py`'s docstring, re-declared edits; unbound
  `nn.Module` methods; prepare and data checked after the evaluation) and fixes found by the sibling reviews (plain
  tensor and disabled torch-function dispatch in the frozen arithmetic, the seal's newline), with tests.

## Node `autoresearch_fixedtokens`

- **Source.** The harness's own `nodes/autoresearch-macos`: the miolini/autoresearch-macos fork of karpathy/autoresearch
  (MIT, as both READMEs declare; neither repository has a LICENSE file or a copyright line), imported at harness
  `fb405e1` and changed at `d075bb3` — the platform check **and** an `AUTORESEARCH_CACHE_DIR` override of the cache
  directory in `prepare.py`, which the port relies on. The frozen `prepare.py` is therefore the harness's modified copy
  (byte-identical to it; a test checks this), not the fork's file.
- **Why the fork, and how the baseline differs from upstream (`228791fb`).** Upstream loads Flash-Attention-3 kernels
  from the Hugging Face `kernels` hub at import time (`varunneal/flash-attention-3` on Hopper,
  `kernels-community/flash-attn3` on other GPUs), which needs hub access in every run, the `kernels` package and its
  torch 2.9.1 pin. The fork runs on plain PyTorch. The fork's baseline differs from upstream in: `DEPTH` 8 → 4;
  `TOTAL_BATCH_SIZE` 2^19 → 2^16; `DEVICE_BATCH_SIZE` 128 → 16; `WINDOW_PATTERN` "SSSL" → "L"; upstream's
  `isnan(loss) or loss > 100` fast-fail reduced to `loss > 100`; SDPA with an explicit mask instead of FA3; torch
  2.6.0 instead of 2.9.1/cu128; and code differences that should not change results on CUDA (device selection,
  where `torch.compile` is applied, scalar casts in the optimizer). Upstream's README recommends this kind of
  reduction for small compute. All of this is in `LICENCES.md`, which now also carries the MIT licence text (with a
  bracketed note that upstream names no copyright holder).
- **Task.** Pretraining of the fork's small GPT on climbmix text: depth 4, width 256, vocabulary 8,192, context 2,048,
  Muon + AdamW. Metric: autoresearch's bits per byte on the pinned validation shard 06542 (`val_bpb`, minimized), as
  `prepare.evaluate_bpb` defines it, **computed by the frozen wrapper from the model's logits** (round 3, below).
  **Not test-scored**: autoresearch has no test split.
- **Editable.** `train.py`, the whole training script, as in autoresearch. The port's changes from the harness copy
  are listed in its docstring and marked "Track G port": the budget and the schedules' progress are training tokens
  (`TRAIN_TOKENS`), not seconds; each micro-step fetches its own batch (no prefetch past the budget); the hard-coded
  seed 42 moved to the wrapper (seeded from `AR_TRAIN_SEED`); one progress line per step; the final evaluation moved
  to the wrapper.
- **Frozen.** `prepare.py`; `run_fixed_budget.py`; `ar_budget.py`; `ar_data.py`; `prepare_data.py`;
  `requirements.txt`; `LICENCES.md`; `data/`; `representative_edits/`.
- **Budget enforcement (`ar_budget.py`, `run_fixed_budget.py`).** The wrapper replaces `prepare.make_dataloader` by a
  budgeted factory before `train.py` runs:
  - the training loader serves exactly `--tokens` tokens; a request beyond it raises `BudgetExhausted` → **exit 7**;
  - **the validation split is refused while `train.py` runs** (`ValidationRequested` → **exit 8**); the wrapper opens it
    only after `train.py` returns;
  - each refusal is recorded before it is raised, so a `train.py` that catches the exception still gets exit 7 / 8
    (round 3);
  - the token counter is a closure, not a module global `train.py` can assign;
  - any other exception or `SystemExit` out of `train.py` → **exit 4**; unused budget → **exit 3**.
- **Metric, frozen (round 2, finding 3; round 3, findings 1, 3–6).** autoresearch's `evaluate_bpb` asked the editable
  model for its own loss (`model(x, y, reduction='none')`), so an edited loss (zero) or a model that reads the next
  token reached the metric. The wrapper computes the same quantity itself: `EVAL_TOKENS` tokens of the validation shard
  in rows of `MAX_SEQ_LEN`, logits from `model(x)` (shape (B, T, vocab)), cross-entropy computed in the wrapper, special
  tokens of byte length 0 excluded, nats / (ln 2 · bytes). On the real `train.py` it equals `evaluate_bpb` bit for bit
  (reviewer, round 3). Round 4 hardens it:
  - the tokenizer is the frozen one (`prepare.Tokenizer.from_directory()`), not an object `train.py` left behind;
    `torch.nn.functional.cross_entropy`, `prepare.get_token_bytes`, `MAX_SEQ_LEN` and `EVAL_TOKENS` are bound before
    `train.py` runs; prepare's module attributes are restored to their state before `train.py` ran (undoing, e.g., a
    changed `VAL_FILENAME` or `importlib.reload(prepare)`);
  - **causality probe** on the first evaluation batch: for cuts at 1/4, 1/2 and 3/4 of the row, the tokens after the
    cut are replaced and the logits before the cut must not change by more than 0.05 (soft-capped at 15); equal
    infinities count as equal, so a `-inf` logit no longer turns the probe off; otherwise **exit 9**. The largest
    change is printed as `AR_INFO causal_probe_max_change=` on every run, for the census (see open point 4);
  - the model's parameters and buffers must be unchanged by the evaluation (per-tensor sums), otherwise **exit 10**: a
    model that updates itself in `forward` cannot train on the validation shard;
  - round 5: `model(x)` must return a plain `torch.Tensor` (a subclass is refused, exit 4) and the frozen arithmetic
    (probe, cross-entropy, sums) runs with torch-function dispatch disabled, so no editable `__torch_function__`
    subclass or mode runs inside it (found in the MLAgentBench and MLGym reviews); eval mode, the device and the weight
    fingerprint use the unbound `nn.Module` methods (parameters and all buffers), not the model's own overrides; after
    the evaluation, prepare's attributes and the data are checked once more, because the model's own code ran during it
    (round 4, finding 1);
  - **contract change from upstream** (round 3, finding 6): `model(x)` must return causal logits for **every**
    position (a "last position only" edit is `divergent`), and the metric is plain cross-entropy from those logits
    whatever training loss an edit uses. Round 5 states it in the docstring of the editable `train.py`, which the
    proposer sees (the harness prompt shows the editable files, not the yaml description); it is also in the yaml
    description. The docstring had still said the wrapper used `prepare.evaluate_bpb`; corrected.
- **Result lines (round 2, finding 1; round 3, finding 8).** `AR_TOKENS` and `AR_METRIC` are written with
  `ar_data.emit` to a copy of the standard output descriptor taken when `ar_data` is imported, before `train.py` runs;
  just before the metric the wrapper points descriptors 1 and 2 at /dev/null and writes a newline to the saved
  descriptor (`ar_data.seal`), so a thread `train.py` started can no longer print into the log through them and a
  partial line cannot swallow the metric line (the reviewer's thread forgery won 2 of 3 runs before this;
  a thread that took its own copy of descriptor 1 earlier still can: 1 of 3 runs in a busy loop); the run ends
  with `os._exit(0)` right after the metric (`ar_data.finish`), so an `atexit` handler cannot add a line and replacing
  `sys.stdout` cannot rewrite it.
- **Remaining in-process limits.** See the threat model in the common section: against deliberately adversarial
  `train.py` the metric is not tamper-proof (a forged line and an early exit; a descriptor to the log obtained before the
  seal; a seek in the log; a forked child; run-time patches of `ar_data`, the wrapper or torch; direct reads of the
  parquet files or `prepare._document_batches`; a model that is causal only on the probe's inputs or leaks below its
  tolerance; code run through the model's own methods during the evaluation, such as a temporary change of
  `prepare.VAL_FILENAME` that is undone before the final check, or learned state kept in a plain tensor attribute; a
  thread running into the evaluation; chmod of the data). For a token budget the harness does not read `AR_TOKENS`.
- **Budget.** `kind: tokens`, 32,768,000 (500 optimizer steps of 65,536 tokens) in place of the 5-minute wall-clock
  budget — **an estimate**: about 1 min of training on an L40S for this model size, plus `torch.compile` and the
  evaluation of 21M validation tokens; the census measures it. An edit's batch size must divide the budget (powers of
  two do), otherwise its own `train.py` assertion fails (`divergent`). Changing the budget after the census changes the
  spec hash and requires a new manifest (both `run_budget` and `node_spec_sha256` are in it).
- **Loss log.** `loss_regex` reads `train.py`'s own `step … | loss: …` lines, printed by editable code; an edit that
  removes them leaves no loss lines. A NaN loss is then caught by the loss pattern or by a non-finite `val_bpb`
  (the fork's `loss > 100 → exit 1` does not catch NaN, since `nan > 100` is false).
- **Data (`prepare_data.py`, the setup command).** Runs autoresearch's own preparation into
  `$AR_TRACKG_DATA_ROOT/autoresearch_fixedtokens`:
  - the climbmix dataset revision is resolved and must start with `915333b`, the revision U1 observed (or one the
    author accepts with `--accept-revision`); the shards are downloaded from that exact revision;
  - before the tokenizer is trained, `data/` must hold exactly `shard_00000`–`shard_00009` and `shard_06542`;
    prepare.py's download only prints failures, so a partial download stops the setup **without** a manifest; an
    `--out` that already holds parquet files is refused; `--out` must lie under `$AR_TRACKG_DATA_ROOT`, and the setup
    command itself checks that the variable is set;
  - prepare.py's download workers are a multiprocessing pool; the setup forces the `fork` start method so they
    inherit the pinned download URL (under `spawn` / `forkserver` they would re-import prepare and use `resolve/main`;
    round 2, finding 5); leftover `.tmp` files stop the setup;
  - the manifest (every file's sha256, the dataset and its revision) is written last, after prepare.py's tokenizer
    sanity check, and the directory is then made read-only, so **accidental** writes by a run fail;
  - every run checks all eleven shards and the tokenizer against the manifest, and **refuses any file the manifest
    does not list** (round 2, finding 2: a copy of the validation shard planted as `shard_00010.parquet` was read as
    training data) — exit 5 otherwise; the start-of-run failure is classed `infrastructure_failure` (the node's pattern
    `AR_ERROR data ` before `AR_DEVICE`): the data were broken before this run;
  - the data are checked again after `train.py` returns, so **a run that changes them fails itself** (exit 5,
    `AR_ERROR train.py changed the data:`, `divergent`), not the runs after it (round 3, finding 2);
  - not prevented: code running as the directory's owner can restore the write bits (as root the bits do not apply)
    and rewrite data and manifest together. On Ada: give the prepared data another owner or a read-only mount, and
    after the census pin the manifest's sha256 (a reviewed frozen change). Data are never redistributed: the node and
    branch hold none.
- **Allocator.** The run command sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, which torch 2.6 reads (the
  fork's `PYTORCH_ALLOC_CONF` is read only from torch 2.9 on, so under the pinned torch it did nothing). Ada and the
  L40S host must use the same torch.
- **Seeds.** `AR_TRAIN_SEED` seeds initialisation; data order is fixed by autoresearch; `AR_SPLIT_SEED` has no effect
  (fixed validation shard) and is logged as such.

## Representative edits (declared before any measurement; re-declared in round 2)

The round-2 spec change (run command, setup command, `LICENCES.md` in `frozen_paths`) changed `node_spec_sha256`, so
the edits were re-declared with `scripts/trackg_declare_edits.py` (Python 3.12) and committed in `38854b9e`; the
round-1 manifest is kept at `representative_edits/superseded/manifest_round1.json`. The diffs are unchanged.
Round 3 changed only frozen file contents, which the manifest does not hash. Round 4 changed the yaml (the description's
model contract and the data infrastructure pattern) and round 5 the editable `train.py`'s docstring (the contract), so
the edits were re-declared each time (Python 3.12); the earlier manifests are kept in `representative_edits/superseded/`
(`manifest_round1.json`, `manifest_round2.json`, `manifest_round3.json`); the diffs are unchanged. Nothing has been measured.

| Manifest sha256 | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| `d8f89c32cbc8beb744304af0d9c146f39e9753af0bec6d3c5959e14dea5e5fe6` | Muon matrix lr 0.04 → 0.05 | depth 4 → 6 (more compute per token) | GELU in place of ReLU² | total batch 2^16 → 2^15 tokens (twice the steps; interacts with E1) |

Edit sha256: E1 `84ca3baf…7830`, E2 `3e8d9889…19cc5`, E3 `90543409…7266`, E4 `5d6f9c12…ab2e` (full values in
`manifest.json`).

## Design common to the three suite kits

- **What the frozen code guarantees, and what it does not (threat model).** The editable code runs in the wrapper's process, as in the suites. The frozen code fixes the data, the budget it serves, the evaluation and the metric's arithmetic against ordinary edits, and it closes the deliberate forgeries the reviews demonstrated: a line added after the result lines (an `atexit` handler, a `print` in evaluation code, a thread printing through descriptors 1 or 2 — except a write already in progress at the moment of the seal — and a partial line left before them), a rewritten `sys.stdout`, a tensor subclass or torch-function mode inside the frozen arithmetic, hidden `step()` calls, planted data files (refused at the next start, and the run that planted them fails its own end-of-run check). It does **not** make the metric tamper-proof against deliberately adversarial code. In-process code can still, for example: print a forged result line and end the process before the wrapper prints; write into the log through a descriptor obtained before the seal (the saved descriptor, its own `dup` of descriptor 1, or the log reopened by path); seek in the log, which the runner opens without `O_APPEND`, to overwrite lines or put an infrastructure line at the top; fork a child that writes after the wrapper has exited; patch frozen modules at run time; or read the task data directly. All of these need deliberate code that is visible in the diff (`os._exit`, `os.fork`, `os.dup`, `os.write`, `lseek`, `/proc/self/fd`, `threading`, `AR_METRIC`, `importlib`, `np.load` / `read_csv` / `parquet` in editable files). Closing them needs the harness, not the port: run the editable code in a separate process with a result channel it cannot write, open the log with `O_APPEND` or as a pipe, kill the process group when the wrapper exits, and refuse a run with more than one metric match (open point for the coordinator). Until then the declared-edit review and the S1 audit must read proposals for such code.

- Each node is `nodes/<node>/` plus `configs/trackg/nodes/<node>.yaml` (`trackg_node/v1`, strict loader). Every
  committed file is editable or frozen (a test checks this); `allow_new_files: false`; the node directory holds the
  editable baseline, the frozen wrapper and helpers, `prepare_data.py` (for nodes with task data), `requirements.txt`,
  **`LICENCES.md`** (checklist F: licence, source URL and revision, data source and hash, per U1) and
  `representative_edits/` with `manifest.json`.
- Result lines `AR_METRIC …` (and `AR_TEST …`, `AR_STEPS …`, `AR_TOKENS …`) are written by the frozen wrapper only,
  after the budget checks, through `ar_data.emit` (a copy of the output descriptor taken before the editable code is
  imported), and every wrapper ends with `os._exit(0)` after them (`ar_data.finish`; inline in the Breakout wrapper,
  which has no `ar_data`); a test checks that no wrapper prints them otherwise and that no editable file contains them.
  Known limit in every suite: editable code can still print a forged line and end the process before the wrapper
  prints; and the harness's six default infrastructure patterns (`No space left on device`, …) are unanchored, so
  editable code that prints one forces an infrastructure re-run (a harness property that predates the port).
- Data: `prepare_data.py` fetches into `$AR_TRACKG_DATA_ROOT/<node>`, records every file's sha256 and the source
  revision in `data_manifest.json`, makes the directory read-only (accidental writes fail; the owner can restore the
  bits) and links it into the node as `data`; every run verifies it and refuses unlisted files outside the setup-only
  subdirectories the manifest names (`ar_data.py`, identical in all nodes). Datasets are never redistributed
  (R1-TRACKG-LICENCES).
- Determinism: spec defaults kept (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`);
  `dataloader_workers: 0`, `threads: 4`. Whether every baseline and edit runs under deterministic algorithms on CUDA is
  for G.1b on the GPU host.
- Tests: one shared `tests/trackg/port_support.py`, identical on the three branches; static tests (spec, scope,
  helpers identical, metric lines, compile, manifest complete and reproducible, frozen-path diff refused with
  `scope_violation`, new file refused); a synthetic smoke on random data of the real shapes (baseline `ok`, frozen diff
  refused, broken diff `discarded_divergent`, every edit runs, repeat baseline equal, complete records,
  `not_forced == ["dataloader_workers"]` on every executed record of a torch node, including the stub-manager runs and
  the repeat baseline, patterns match the log). `tests/trackg/port_smoke_gpu.py` runs the same checklist-E smoke on
  the census host with the real data, full budget, seeds 8001, the GPU by UUID (required except for the CPU-only
  House Prices node), a CPU list and the stated memory cap.
- Harness property (unchanged from round 1): the normalised code-state hashes are built from the interpreter's AST and
  differ between Python 3.12 and 3.13; manifests were declared with 3.12 and reproduce byte for byte there (the other
  fields under 3.13). The census and G.1b should run the same Python minor version, preferably 3.12.

## Checks run here

Python 3.12, torch 2.6.0+cu124 on CPU (no GPU on this host): `tests/trackg/test_port_autoresearch.py` at `b3a08ff0`:
**21 passed** (20 in the full run; the new shared `test_output_seal` first failed because the test wrote the child's
output to a pipe, which a spamming thread filled so that a blocked write landed after the result line; with a log file,
as the runner uses, it passed 5 of 5 times before the commit). Covered: static (result lines only through `emit`,
`seal()` right before `AR_METRIC`, nothing after it, `finish()` after `main()`), manifest (reproduced byte for byte
under 3.12), frozen-path refusal, prepare.py identity, whole-step budget, the budget closure (counter, over-request,
validation refusal and opening, recorded refusals), the wrapper's exits on synthetic data (`train.py` stand-ins: under
budget → 3, over budget → 7, asking for validation → 8, catching that refusal → 8, a forged metric then `sys.exit(0)` →
4), the frozen metric (a causal stand-in whose edited loss is zero, which also registers an `atexit` line and swaps
`sys.stdout` for a filter that rewrites metric lines: exit 0, exactly one `AR_METRIC` line, the last line, with the
wrapper's value; stand-ins that read the next token → 9, also with a `-inf` logit; one that updates its weights in
`forward` → 10; one that returns a tensor subclass → 4; one that plants a data file → 5 with "train.py changed the
data"), an unlisted data file → 5, the output seal against a partial line and a writing thread, the exact-shard and
data-root guards of `prepare_data.py`, and the synthetic smoke (with `TORCHDYNAMO_DISABLE=1` on CPU, because torch 2.6's
CPU inductor crashed in autoresearch's compiled Muon step; the compiled GPU path runs only on the census host). In the
smoke, `AR_INFO causal_probe_max_change` was exactly 0 on the baseline and every edit (CPU, bf16 autocast). The synthetic smoke (random-word corpus, budget 2^16 tokens, rows of
256 tokens, seeds 8001; the numbers say nothing about the task):

**`autoresearch_fixedtokens`**

| Run | Diff | Outcome | Validation metric | Sealed test | not_forced |
|---|---|---|---|---|---|
| baseline | - | ok | 2.18766 | - | dataloader_workers |
| frozen-path diff | refused (scope_violation) | not run | - | - | - |
| broken diff | applied | divergent (non_finite_loss) |  | - | dataloader_workers |
| E1 (stub manager) | applied | ok | 2.18549 | - | dataloader_workers |
| baseline repeat | - | ok | 2.18766 | - | dataloader_workers |
| E1 (on baseline) | applied | ok | 2.18549 | - | dataloader_workers |
| E2 (on baseline) | applied | ok | 2.19356 | - | dataloader_workers |
| E3 (on baseline) | applied | ok | 2.19196 | - | dataloader_workers |
| E4 (on baseline) | applied | ok | 2.20252 | - | dataloader_workers |

## Open points for the author

1. **Compute per token is editable; the budget fixes only tokens** (round 1, finding 3). From `estimate_flops`,
   training FLOPs relative to the baseline are about 2.5× for E2 (depth 6) and about 4.9× for depth 8 — upstream's own
   default and a likely proposal. Such proposals can overrun the runner's timeout (3× the measured baseline, checklist
   D) and the ~5 min closed-loop bound of R1-BX-D5; the harness classes a timeout as `infrastructure_failure`
   (re-run, not deduplicated), not as the proposal's effect. Options: (a) a frozen compute cap — the wrapper refuses,
   with its own non-zero exit (divergent), a model whose parameter count or `num_flops_per_token` exceeds k× the
   baseline's; (b) a FLOP budget instead of a token budget; (c) a node-specific timeout basis set from the largest
   allowed configuration. Proposed, pending your decision: read an over-compute timeout on this node as the
   proposal's cost. The harness currently classes every timeout as `infrastructure_failure` and re-runs it, and a port
   cannot change outcome classes; applying the proposal needs a harness change or a recorded manual reclassification.
   It does not affect the census of E1–E4.
2. **Dataset revision.** `prepare_data.py` accepts only the U1-observed revision prefix `915333b` unless you accept
   another; if the hub moved, the setup STOPs and asks for that decision.
3. **One torch for both hosts** (allocator variable, compiled kernels).
4. **Causality probe tolerance** (round 3, finding 3). A causal model should change its earlier logits by exactly 0
   under the spec's deterministic settings; 0.05 is loose (it admits a leak worth roughly 0.015–0.02 bpb, the size of
   real edit effects). Proposed: the census reads `AR_INFO causal_probe_max_change=` on the baseline and every edit;
   if it is 0 (or bf16 noise far below 1e-3), tighten `CAUSAL_ATOL` to 1e-3 in a reviewed frozen change before G.1b.
5. **For the coordinator (harness, outside the port):** in-process `train.py` can still write a forged `AR_METRIC`
   line (to the saved descriptor, or before ending the process early), and the harness scores the last match.
   Refusing a run whose log has more than one metric match would close it.

---

Bundle: one bundle per suite with the paper branch `mac-trackg-u3-ar-20261117b` (this report, the checklist's section F,
the review record) and the harness branch `mac-trackg-port-ar-20261117b`.
