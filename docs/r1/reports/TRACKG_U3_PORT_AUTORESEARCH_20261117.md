# Track G U3 port kit — suite autoresearch (17 November 2026, round 2)

**Status.** The port kit for the one autoresearch T1 candidate of the Ada census plan, for the experiment agent to
deploy and smoke-test on Ada. ENGINEERING_ONLY: nothing was measured. Independent review: see
`docs/r1/reviews/TRACKG_U3_PORT_AUTORESEARCH_REVIEW_20261117.md` once filed (round 1 was NOT ACCEPTED; this round
answers it). Written by the Mac-desk agent (Claude), AI-assisted.

**Authority and inputs.**
- R1-TRACKG-PORT-OWNER (the Mac agent writes the port kits) and R1-TRACKG-LICENCES (licence and provenance step;
  datasets never redistributed), on `main` `26177d82` and `author-decisions-20261117b` @ `33c82351`.
- Port checklist: `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; this branch adds its **section F (Licence and
  provenance)** in `b715e110`.
- Candidate: `docs/r1/reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md` and the licence audit
  `U1_LICENCE_AVAILABILITY_20261117.md` §2 (both on `ops-tasl-20261116`): "autoresearch (short fixed-step variant,
  1 task)".
- Harness: `r1-local-trackg-v2-20261114` @ `717ad835`.

**Harness branch.** `mac-trackg-port-ar-20261117b` of the `autoresearch_harness` repository, based on `717ad835`, tip
`4f705e5e0f7d2bd19e0e60ffa20f08a78b139894`. It only adds files under `nodes/autoresearch_fixedtokens/`,
`configs/trackg/nodes/` and `tests/trackg/`; no existing harness file changes. Commits:
- `9fb6b483` port kit (round 1); `5eac9802` manifest reproduction across Python minor versions (round 1);
- `38854b9e` round 2: the round-1 review fixes and R1-TRACKG-LICENCES (below);
- `4f705e5e` the prepared data directory made read-only after the manifest.

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
  2.6.0 instead of 2.9.1/cu128. Upstream's README recommends this kind of reduction for small compute. All of this
  is in `LICENCES.md`.
- **Task.** Pretraining of the fork's small GPT on climbmix text: depth 4, width 256, vocabulary 8,192, context 2,048,
  Muon + AdamW. Metric: autoresearch's frozen `evaluate_bpb`, bits per byte on the pinned validation shard 06542,
  `val_bpb`, minimized. **Not test-scored**: autoresearch has no test split.
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
  - **the validation split is refused while `train.py` runs** (`ValidationRequested` → **exit 8**): the validation
    shard is the only metric data, and round 1 showed `train.py` could train on it unbudgeted. The wrapper opens it
    only after `train.py` returns, for `evaluate_bpb`;
  - the token counter is a closure, not a module global `train.py` can assign;
  - any other exception or `SystemExit` out of `train.py` → **exit 4**, so `print("AR_METRIC …"); sys.exit(0)` cannot
    skip the budget check; unused budget → **exit 3**; `AR_TOKENS consumed=` and `AR_METRIC val_bpb=` are printed only
    after these checks.
  - **Remaining in-process limits** (the editable code runs in the wrapper's process): it can print forged `AR_` lines
    before failing, patch the wrapper's functions at run time, introspect the budget closure, or read the parquet files
    directly. The checks and the line order narrow these; they do not close them.
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
  - the manifest (every file's sha256, the dataset and its revision) is written last, after prepare.py's tokenizer
    sanity check, and the directory is then made read-only;
  - every run checks all eleven shards and the tokenizer against the manifest (exit 5 otherwise). Data are never
    redistributed: the node and branch hold none; the census records the manifest's sha256, which can then be pinned.
- **Allocator.** The run command sets `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, which torch 2.6 reads (the
  fork's `PYTORCH_ALLOC_CONF` is read only from torch 2.9 on, so under the pinned torch it did nothing). Ada and the
  L40S host must use the same torch.
- **Seeds.** `AR_TRAIN_SEED` seeds initialisation; data order is fixed by autoresearch; `AR_SPLIT_SEED` has no effect
  (fixed validation shard) and is logged as such.

## Representative edits (declared before any measurement; re-declared in round 2)

The round-2 spec change (run command, setup command, `LICENCES.md` in `frozen_paths`) changed `node_spec_sha256`, so
the edits were re-declared with `scripts/trackg_declare_edits.py` (Python 3.12) and committed in `38854b9e`; the
round-1 manifest is kept at `representative_edits/superseded/manifest_round1.json`. The diffs are unchanged.
Nothing has been measured.

| Manifest sha256 | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| `088e80f6f9b962656e58d91cde9def6f9d84772479f4d718b2950113fb936106` | Muon matrix lr 0.04 → 0.05 | depth 4 → 6 (more compute per token) | GELU in place of ReLU² | total batch 2^16 → 2^15 tokens (twice the steps; interacts with E1) |

Edit sha256: E1 `84ca3baf…7830`, E2 `3e8d9889…19cc5`, E3 `90543409…7266`, E4 `5d6f9c12…ab2e` (full values in
`manifest.json`).

## Design common to the three suite kits

- Each node is `nodes/<node>/` plus `configs/trackg/nodes/<node>.yaml` (`trackg_node/v1`, strict loader). Every
  committed file is editable or frozen (a test checks this); `allow_new_files: false`; the node directory holds the
  editable baseline, the frozen wrapper and helpers, `prepare_data.py` (for nodes with task data), `requirements.txt`,
  **`LICENCES.md`** (checklist F: licence, source URL and revision, data source and hash, per U1) and
  `representative_edits/` with `manifest.json`.
- Metric lines `AR_METRIC …` (and `AR_TEST …` for test-scored nodes) are printed by the frozen wrapper only, after the
  budget checks; no editable file contains `AR_METRIC`, `AR_TEST`, `AR_STEPS` or `AR_TOKENS` (a test checks this).
- Data: `prepare_data.py` fetches into `$AR_TRACKG_DATA_ROOT/<node>`, records every file's sha256 and the source
  revision in `data_manifest.json`, makes the directory read-only and links it into the node as `data`; every run
  verifies it (`ar_data.py`, identical in all nodes). Datasets are never redistributed (R1-TRACKG-LICENCES).
- Determinism: spec defaults kept (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`);
  `dataloader_workers: 0`, `threads: 4`. Whether every baseline and edit runs under deterministic algorithms on CUDA is
  for G.1b on the GPU host.
- Tests: one shared `tests/trackg/port_support.py`, identical on the three branches; static tests (spec, scope,
  helpers identical, metric lines, compile, manifest complete and reproducible, frozen-path diff refused with
  `scope_violation`, new file refused); a synthetic smoke on random data of the real shapes (baseline `ok`, frozen diff
  refused, broken diff `discarded_divergent`, every edit runs, repeat baseline equal, complete records,
  `not_forced == ["dataloader_workers"]`, patterns match the log). `tests/trackg/port_smoke_gpu.py` runs the same
  checklist-E smoke on the census host with the real data, full budget, seeds 8001, the GPU by UUID, a CPU list and
  the stated memory cap.
- Harness property (unchanged from round 1): the normalised code-state hashes are built from the interpreter's AST and
  differ between Python 3.12 and 3.13; manifests were declared with 3.12 and reproduce byte for byte there (the other
  fields under 3.13). The census and G.1b should run the same Python minor version, preferably 3.12.

## Checks run here

Python 3.12, torch 2.6.0+cu124 on CPU (no GPU on this host): `tests/trackg/test_port_autoresearch.py` **12 passed** —
static, manifest (reproduced byte for byte under 3.12), frozen-path refusal, prepare.py identity, whole-step budget,
the budget closure (counter, over-request, validation refusal and opening), the wrapper's exits 3 / 7 / 8 / 4 on
synthetic data (a `train.py` stand-in under budget, over budget, asking for validation, and printing a forged metric
then `sys.exit(0)`), the exact-shard and data-root guards of `prepare_data.py`, and the synthetic smoke (with
`TORCHDYNAMO_DISABLE=1` on CPU, because torch 2.6's CPU inductor crashed in autoresearch's compiled Muon step; the
compiled GPU path runs only on the census host).

## Open points for the author

1. **Compute per token is editable; the budget fixes only tokens** (round 1, finding 3). From `estimate_flops`,
   training FLOPs relative to the baseline are about 2.5× for E2 (depth 6) and about 4.9× for depth 8 — upstream's own
   default and a likely proposal. Such proposals can overrun the runner's timeout (3× the measured baseline, checklist
   D) and the ~5 min closed-loop bound of R1-BX-D5; the harness classes a timeout as `infrastructure_failure`
   (re-run, not deduplicated), not as the proposal's effect. Options: (a) a frozen compute cap — the wrapper refuses,
   with its own non-zero exit (divergent), a model whose parameter count or `num_flops_per_token` exceeds k× the
   baseline's; (b) a FLOP budget instead of a token budget; (c) a node-specific timeout basis set from the largest
   allowed configuration. **Until you decide, an over-compute timeout on this node is not an infrastructure failure**
   and must be read as the proposal's cost, not re-run.
2. **Dataset revision.** `prepare_data.py` accepts only the U1-observed revision prefix `915333b` unless you accept
   another; if the hub moved, the setup STOPs and asks for that decision.
3. **One torch for both hosts** (allocator variable, compiled kernels).

---

Bundle: one bundle per suite with the paper branch `mac-trackg-u3-ar-20261117b` (this report, the checklist's section F,
the review record) and the harness branch `mac-trackg-port-ar-20261117b`.
