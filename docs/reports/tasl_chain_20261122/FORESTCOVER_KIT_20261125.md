# Track G T1 expansion kit — 1GC-7RC Forest Cover, node `gc7rc_forestcover` (25 November 2026)

**Status.** ENGINEERING_ONLY port kit: complete, CPU-smoke-tested and **pushed** as harness branch
`mac-trackg-forestcover-20261125` @ **`85851664679d10889c5af406843c4a3fc38f7a49`** (no PR, no merge). **U2 census
and G.1b were not run** (no GPU job, no lease); no noise floor, no D21/D28, no label/evidence use is claimed.
Written by a DeepSeek Harness agent (`port-1gc-forest`, delegated by the lead) on TASL-2 and the Mac ops
worktree, AI-assisted. Independent review **pending**.

**Authority and inputs.**
- `R1-T1-NODE-EXPANSION` (25 Nov 2026, author-signed with `R1-T1-D21-SCOPE`, PLAN row 1516): the additional T1
  candidates are MLGym MountainCarContinuous or MetaMaze, MLGym Titanic, 1GC-7RC ETTh1 and **1GC-7RC Forest
  Cover (AG News as reserve)**; per node an isolated harness kit (reviewed) → U2 census on TASL → G.1b on TASL
  (D21 protocol, 460 runs) under a new G.1b note; a candidate whose G.1b completes with determinism PASS by
  2 Dec 2026 enters G.5. This report describes **candidate 4, 1GC-7RC Forest Cover** (AG News is the reserve).
- `R1-1GC-FALLBACK` (4 Nov 2026): 1GC-7RC is **not a suite** (its repository was 404); its public datasets may
  be used as extra tasks, not as a suite. This kit therefore follows the **paper's public dataset/task
  semantics**, not suite code.
- `R1-BX-D5` (fixed step/token budget; short label runs), `R1-TRACKG-LICENCES` (data never redistributed),
  `R1-TRACKG-ROLE` (validation selected, test sealed), `R1-HARNESS-ISOLATION` (core
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` + accepted fix `5403392e94cb59d732f45d6702fc857531ad8fd5`).
- Harness base: **`mac-trackg-t1-tasl-20261121` @ `c025f89aeafc2199bf3487b4bcaa16678273c702`** — the accepted T1
  TASL harness that the G.1b/G.4 authorizations and the official seven-node assembly cite
  (`harness_commit: c025f89a…`). Verified on TASL-2 that `68cdd1a`, `5403392e` and all three accepted iso port
  branches (`f07875de`, `fb6e7d73`, `448f682`) are ancestors of `c025f89a`, so this kit starts from the same tree
  the census/noise-floor code runs on.
- 1GC-7RC paper: <https://arxiv.org/abs/2605.17046v2> (HTTP 200 on 25 Nov 2026), **Task 5** ("Seven-class
  classification on Forest Cover Type (581 K rows, 54 features: 10 continuous + 44 binary one-hot; stratified
  80/10/10 split, StandardScaler-normalized) … baseline is a 3-layer MLP (128→256→128, BatchNorm, ReLU,
  dropout = 0.3)"), Table 2 (T5: 40 min, tabular, accuracy, MLP (3L), 465 K train / 58 K eval, score **0.806**,
  batch 4096) and Appendix E (CC BY 4.0). The paper's suite repository
  <https://github.com/Strolchii/1GC-7RC-Benchmark> returned **404** again on 25 Nov 2026 (U1 had also found 404
  on 17 Nov), so there is no suite code, evaluator or licence to port. The harness repo has **no 1GC-style node**:
  the only 1GC material is `docs/track_g/1gc_7rc_handoff_20261027.md` on `origin/r1-local-20261027-1gc`
  (status BLOCKED; explicitly no runnable adapter), so this kit necessarily follows the paper's public
  dataset/task semantics.

## 1. Node design (paper semantics, not suite code)

The node implements the paper's **Task 5** as a standard tabular classification task:

| Item | Value |
|---|---|
| Dataset | UCI **Covertype** (Forest Cover Type), 581,012 rows × 54 features (10 continuous + 4 wilderness one-hot + 40 soil-type one-hot), 7 classes; UCI dataset 31, DOI 10.24432/C50K5N |
| Split | the paper's **stratified 80/10/10** split: per class a seeded permutation (fixed split seed 42), 10 % validation, 10 % test, the remaining 80 % training — **464,810 / 58,101 / 58,101 rows**, chronological order not relevant; the same split in every run |
| Normalisation | per-feature mean/std (population std, StandardScaler semantics) fitted on the 464,810 training rows only; binary columns are scaled too |
| Metric | **accuracy**; selection on validation (`AR_METRIC val_accuracy=`, maximise); test sealed (`AR_TEST test_accuracy=`, never selected) — R1-TRACKG-ROLE |
| Baseline (editable `train.py`) | paper's 3-layer MLP **128→256→128**, each layer `Linear → BatchNorm1d → ReLU → Dropout(0.3)`, then a 7-logit head; batch 4096 (paper Table 2's batch), Adam lr 1e-3, cross-entropy |
| Fixed budget | **8,000 optimizer steps** (`run_budget.kind: steps`; no wall-clock key anywhere — R1-BX-D5); 464,810/4,096 = 113 steps per epoch ⇒ ≈71 epochs |
| Workers | dataloader_workers 0, threads 4 (fixed) |
| Suite/domain | `1gc7rc` / `tabular` (1GC-7RC is not a suite; the spec's `external_benchmark` says so) |

**Deviations, stated.** (a) The suite's own evaluator/baseline are unavailable (repo 404), so the 3-layer MLP
baseline and the whole fixed-step API are **written by the port from the paper's description** — the appendix
must disclose "implemented by the port from the 1GC-7RC paper's description; not the suite's assets". (b) The
paper scores Task 5 on **held-out test** (Table 2 note: Eval = held-out test for Tasks 4–6), while this node
selects on **validation accuracy** and seals the test accuracy (R1-TRACKG-ROLE); the paper's 0.806 reference is a
test-split score and is **not interchangeable** with this node's selection metric. (c) The paper states the
split and the model but no epoch count, learning-rate schedule, weight decay or optimiser name beyond the
baseline description; the port fixes Adam lr 1e-3, no schedule/weight decay, 8,000 steps (disclosed above).
(d) The paper's Table 2 says 465 K train / 58 K eval; the port's per-class rounding gives 464,810 / 58,101 /
58,101 — the same 80/10/10 proportions, recorded exactly here. (e) The paper's baseline reference 0.806 is
reproduced or beaten by the port's baseline at this budget (see §4): our baseline trains longer than the
paper's short agent-budget run, so the port's baseline is stronger; the funnel/σ̂ are read on the port's own
baseline, not against 0.806.

## 2. Data preparation and licence

**Setup (one-off; not part of a run; nothing committed).** `prepare_data.py` downloads

`https://archive.ics.uci.edu/static/public/31/covertype.zip`

(UCI dataset 31 page's canonical download, HTTP 200 on 25 Nov 2026; DOI 10.24432/C50K5N), checks the pinned
zip sha256 `89a975c2…` and its 11,251,206 bytes, extracts the member `covtype.data.gz` and checks its pinned
sha256 `614360d0…` and 11,240,707 bytes, parses the 581,012 × 55 CSV (54 features + class 1–7), writes
`X.npy` (float32 581,012 × 54) and `y.npy` (int8, classes mapped 1–7 → 0–6), records the hashed data manifest and
links the data root into the node as `data/`. Every run re-checks the manifest; the frozen parent re-checks the
pinned **source** zip sha256 and URL against the manifest for non-synthetic data (the synthetic smoke marks its
manifest `synthetic`). The legacy direct URL of the same file
(`https://archive.ics.uci.edu/ml/machine-learning-databases/covtype/covtype.data.gz`) returned the same bytes and
sha256 on 25 Nov 2026; the raw zip is kept only under the data root's setup-only `raw/`, which no run reads.

| item | value |
|---|---|
| data root (TASL-2, outside the repo) | `/home/dowling/r1_engineering/forestcover_port_20261125/data/gc7rc_forestcover` |
| `data_manifest.json` sha256 | **`2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d`** |
| `X.npy` sha256 / size | `3c9503390b527ce0cc5d1713772db126e754d12f312f3581b3f15fe6f834bfa7` / 125,498,720 B |
| `y.npy` sha256 / size | `35e11486262e974a249c66474dc624fe29d88f690d9819612239fb4dd34768a7` / 581,140 B |
| source zip sha256 / size | `89a975c2457cd48e824238ae43c5a3cb762e42c4b4078d9b44a4514055105f6d` / 11,251,206 B |
| member `covtype.data.gz` sha256 / size | `614360d0257557dd1792834a85a1cdebfadc3c4f30b011d56afee7ffb5b15771` / 11,240,707 B |
| class counts (1–7) | 211,840 / 283,301 / 35,754 / 2,747 / 9,493 / 17,367 / 20,510 |
| setup run (TASL-2, 25 Nov 2026) | exit 0; download/parse/first-run output in `captures/setup.txt` |

**Licence (R1-TRACKG-LICENCES: download, never redistribute).** The UCI dataset page states **CC BY 4.0**
(attribution required); the 1GC-7RC paper's Appendix E also lists Forest Cover Type as CC BY 4.0, so unlike
ETTh1 there is no conflicting licence claim. The dataset is **downloaded at setup, never redistributed**: the
raw zip stays outside the repository (setup-only `raw/`), the branch holds no task data, and the derived arrays
live under `$AR_TRACKG_DATA_ROOT`. Attribution recorded in `LICENCES.md`, the spec and the manifest:
"Covertype dataset, UCI Machine Learning Repository (Blackard, J. & Dean, D., 1998), DOI 10.24432/C50K5N,
CC BY 4.0". This is an engineering record, not a legal opinion.

## 3. Representative edits (declared before any measurement)

Four diffs against `train.py`, committed with their manifest **before** any training run (the manifest is
`representative_edits/manifest.json`, sha256 **`0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed`**;
`measured: false`; `node_spec_sha256` = the committed spec hash):

| Edit | Change | sha256 |
|---|---|---|
| E1 | learning rate 1e-3 → 4e-4 (small hyperparameter) | `d59cd11e4f976766f45d4fcdffbcc3ac3d12a101ad63824e639465c205f8f293` |
| E2 | learning rate 1e-3 → 5e-3 (larger, same kind) | `c960568c95067befccd929445ee030d496274252ae1cf6264b028613cb81e97a` |
| E3 | loss cross-entropy → cross-entropy with label smoothing 0.1 + gradient clipping 1.0 (code-level training change) | `19009049f5f509116b3451f7de383c97fecf0a19371aac0ac9477728ea0d1994` |
| E4 | architecture: hidden widths 128/256/128 → 256/512/256 (same 3-layer design, wider) | `29f4535bb5575e6f15e2957016051824523f1cc24251e108a6626a1930b11457` |

All four apply through the scope validator, are not inert and are pairwise distinct; the declared interacting
pairs E1+E3, E2+E3, E1+E4, E2+E4 compose in both orders (test `test_interacting_edits_compose`). E1/E2 are
alternatives (same line). E4 makes each step heavier without changing the step budget — disclosed in the
README's threat-model notes (the budget fixes steps, not FLOPs).

## 4. Tests and CPU smoke (TASL-2, no GPU)

All runs: harness worktree `/home/dowling/r1_trackg_20261125/harness_forestcover`, env
`/home/dowling/r1_tracks/t1_tasl/envs/torch312`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, no GPU.
Captures are in `FORESTCOVER_KIT_20261125_captures/`.

| Check | Result | Capture |
|---|---|---|
| new node tests `tests/trackg/test_port_1gc.py` (static, manifest, frozen-path refusal, interaction, synthetic smoke, subclass refusal, parent metric, semantics) | **8 passed** in 64.40 s | `pytest_port_1gc.log` |
| isolation core `tests/trackg/test_trackg_isolation.py`, under `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` with `AR_TEST_CGROUP_PARENT` | **27 passed, 1 skipped** in 36.86 s (the skip is the root-only test) — identical to the accepted TASL-2 host-check count | `pytest_isolation.log` |
| whole `tests/trackg -k "not smoke"` on the kit branch | **359 passed, 3 failed, 1 skipped, 11 deselected** in 162.26 s | `pytest_full_suite_kit.log` |
| the same 3 test ids on the pristine base `c025f89a` (`/home/dowling/r1_tracks/t1_tasl/harness`, read-only use), same scope/env | **3 failed, same 3 ids and same exceptions** in 2.46 s → pre-existing environment failures, not kit regressions | `pytest_base_known_failures.log` |

The 3 full-suite failures are `test_trackg_campaign_v2_diff.py::test_{measured,repeated_provisional}_timeout…`
(`STOP: the baseline did not give an ok run after reruns`, the known cgroup/timeout environment failure) and
`test_trackg_t0_identity.py::…byte_identical…` (the known t0 environment failure, langchain-openai stack
missing). All three fail identically at the base commit under the same command/environment.

**Synthetic smoke (part of the 8 tests):** baseline `ok`; a frozen-path diff refused `scope_violation`; a
deliberately broken (NaN) diff `divergent/non_finite_loss`; E1–E4 all `ok`; a second baseline with the same
seeds reproduces the metric exactly. Random data of the real shape only.

**Real-data CPU checklist-E smoke at the full 8,000-step budget** (checklist E on the real data;
ENGINEERING_ONLY, **not** U2 and not the GPU census): run through `WorkingCopyRunner` in a delegated 8 GiB cgroup
with the worker sandbox (`ps.run_smoke`, CPU, `--cpus` 16-31, `CUDA_VISIBLE_DEVICES=""`; driver
`run_cpu_smoke.py` overrides only the reviewed CLI's `--gpu-uuid` guard for this GPU-capable node). Every
executed run: `isolation.effective: true`, `waivers {}`, `exceptions []`, `determinism.not_forced ==
["dataloader_workers"]`, `frozen_files_checked 16 / changed []`, no process killed, `timed_out: false`.

| run | executed | outcome | val accuracy | sealed test accuracy | elapsed (info only) |
|---|---|---|---|---|---|
| `s000_baseline` | yes | ok | **0.896439** | **0.894683** | 139.502 s |
| `s001` frozen-path diff | no | refused `scope_violation` | — | — | — |
| `s002` broken NaN diff | yes | divergent `non_finite_loss` | 0.000000 (all logits non-finite) | 0.000000 | 130.017 s |
| `s003` first declared edit (E1) | yes | ok | 0.883083 | 0.881689 | 133.528 s |
| `E1` (lr 4e-4) | yes | ok | 0.883083 | 0.881689 | 127.649 s |
| `E2` (lr 5e-3) | yes | ok | 0.899262 | 0.898849 | 128.366 s |
| `E3` (label smoothing + clip) | yes | ok | 0.891895 | 0.890329 | 135.036 s |
| `E4` (wider 256/512/256) | yes | ok | **0.927213** | **0.927919** | 344.405 s |
| `B2` repeat baseline | yes | ok | **0.896439** | **0.894683** | 129.126 s |

**Launch accounting (disclosed).** Two earlier launches of the same driver aborted in their own preflight
before any run was started: attempt A (12:56Z) failed on the driver's `git rev-parse` cwd, attempt B (12:59Z) on
the driver's `tests` import path; both directories are preserved unmodified as
`u2_census_smoke_20261125_attemptA_preflight_abort` and `u2_census_smoke_20261125_attemptB_import_abort` under
`/home/dowling/r1_engineering/forestcover_port_20261125/` (no `runs/` was created by either). The smoke above is
attempt C, launched once after those two preflight fixes and **not retried**.

The smoke wall was **1,268.791 s** (including the refusals and all eight executed runs), scope memory peak
**1,428,860,928 B** (1.43 GB of the 8 GiB cgroup), no run timed out or was killed. `B2` reproduces `B1`'s
validation **and** sealed test accuracy to the digit (`run.log` sha256 `07c6557e…` and result-channel sha256
`bcfc9b5d…` identical for both); `s003` reproduces `E1` exactly (`run.log` `c1e7d434…`, channel `5a119acc…`) —
the CPU fixed-seed repeat is genuine. s002's channel shows 0.000000 because every logit is non-finite (the
parent's accuracy counts such rows wrong); the divergence is the NaN loss, not the metric. Validation and sealed
test accuracy agree within 0.0018 for every run, so — unlike ETTh1 — the validate/test difficulty is the same
property of a random split; selection is on validation (R1-TRACKG-ROLE) and test remains sealed.


**Determinism (CPU, seeds 8001/8001).** `B2` reproduces `B1` exactly (`val_accuracy` to the digit, identical
`run.log` and result-channel sha256) and `s003` reproduces `E1` exactly; the fixed-seed CPU repeat is genuine.
The GPU determinism check itself is G.1b's job.

**Budget expectation.** 8,000 steps at batch 4,096 — 113 steps/epoch, ≈71 epochs of the 464,810 training rows.
On the shared TASL-2 CPU the full-budget smoke measured 128–140 s per run for the baseline and E1–E3,
344 s for the 3.8×-wider E4, and 129 s for the B2 repeat (4 threads; concurrent smoke traffic on the shared
host; INFO ONLY), and the GPU run will be far shorter (the node is ≈1.7 GFLOP/step at batch 4,096, and the
accepted T1 nodes' GPU runs are seconds). **R1-BX-D5's 1–2 min window is a property of the label runs on the
label GPU, not of this shared CPU smoke host**: the baseline's 139.5 s CPU time is an upper bound measured with
4 threads on a contended host and is not the label-run number. The U2 census must record the GPU wall
time/VRAM; if the GPU run at 8,000 steps were above 120 s, the budget would have to be reduced under checklist A
(new review). The baseline converges well before the budget:
validation accuracy keeps improving to ≈0.896 by 8,000 steps in the port's CPU runs, and the paper's 0.806 test
reference is exceeded by the port's baseline. The gap reflects the port's longer training (≈71 epochs) and the
paper's own random stratified split (spatial-autocorrelation leakage in Covertype), not a stronger method; the
baseline is the port's own fixed-budget baseline and comparisons stay within-node.

## 5. Pins and environment freeze (the census block)

All pins recomputed on TASL-2 from the committed branch (`captures/pins.json`). `node_spec_sha256` is the
loader's canonical `spec.raw_sha256`; the **spec raw sha256** is the sha256 of the YAML file bytes;
`committed_pin_sha256` is `noise_floor.frozen_pin_sha256(committed_view(isolation.frozen_file_hashes(node)))`
(the frozen files **without** the `data` link) and was re-derived from a clean `git archive HEAD` tree (no data
link) to the same value (`captures/committed_pin_from_head.json`); `deployed_pin_sha256` adds the host-specific
`data` link and must not be confused with the committed pin.

| field | value |
|---|---|
| harness branch | `mac-trackg-forestcover-20261125` |
| harness base | `c025f89aeafc2199bf3487b4bcaa16678273c702` (`origin/mac-trackg-t1-tasl-20261121`) |
| harness tip (pushed) | **`85851664679d10889c5af406843c4a3fc38f7a49`** |
| `node_spec_sha256` | **`ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb`** |
| spec raw sha256 (YAML file bytes) | **`edd1a076aab8b2cc1f45192860b3555a844400c211581888b9edbcc4e5104e02`** |
| `committed_pin_sha256` | **`78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33`** |
| `edits_manifest_sha256` | **`0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed`** |
| `data_manifest_sha256` | **`2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d`** |
| deployed pin (with data link, information only) | `ec5c779161be56665bf7ae6d45adee140fde6e47cb46cb08bd583f8a0d4d5a5f` |
| `node_ar_isolated_sha256` / master | `37d99ab0…` / `37d99ab0…` (match) |
| shared frozen helpers | `ar_data.py` `85cec63f…`, `ar_parent.py` `cbef1d38…` (accepted copies); `ar_fixed_loop.py` `28562cfa…` (the accepted shared **classification** loop, byte-identical — no forecasting variant needed) |
| run budget | steps **8,000** (batch 4,096; fixed before the census) |

**Environment freeze.** TASL-2, Python **3.12.16**, torch **2.6.0+cu124**, numpy **2.5.4**, pandas **3.1.1**,
uv 0.13.6; `uv pip freeze` for `envs/torch312` = **sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`**
(77 packages), **identical to the accepted T1 TASL freeze** in `g1b_t1_tasl_20261121` (`torch312.freeze.txt`,
same sha, verified with `diff`). Captures: `env.txt`, `torch312.freeze.txt`.

**Fields for the U2/G.1b note (to be filled by the census agent):**

```
node_gc7rc_forestcover: host TASL-2; gpu (UUID to be recorded by U2); env torch312;
  node_spec_sha256      ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb;
  committed_pin_sha256  78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33;
  edits_manifest_sha256 0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed;
  data_manifest_sha256  2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d;
  data_root             /home/dowling/r1_engineering/forestcover_port_20261125/data/gc7rc_forestcover;
  census_record         none (U2 not run);  slowest census record pending; timeout (3x) pending; runs 460 pending
```

## 6. Branch content, push status, captures

Commit `8585166` adds 19 files, +2,030/−1 vs `c025f89a`: the node spec, the node directory (frozen
parent/worker/loop/helpers/data-prep/licence/README, editable `train.py`, E1–E4 + manifest),
`tests/trackg/test_port_1gc.py`, and a one-line addition of the new suite module to
`tests/trackg/port_smoke_gpu.py`'s `SUITE_MODULES` so the standard census smoke can find the node
(`CPU_ONLY_NODES` is unchanged: this is a GPU-capable torch node). Worktree status after the push: clean except
the untracked runtime `nodes/gc7rc_forestcover/data` link (expected). Pushed with
`git push origin mac-trackg-forestcover-20261125` (new branch, no force, **no PR/merge**);
`git ls-remote origin refs/heads/mac-trackg-forestcover-20261125` = TIP. The paper side of this record is the
**uncommitted** Mac ops-worktree report/captures under `docs/r1/reports/tasl_chain_20261122/`; nothing was
pushed to paper `main`.

Captures (`FORESTCOVER_KIT_20261125_captures/`, **52 files, 504 KiB**; `sha256sum -c SHA256SUMS` rc 0 on
TASL-2 **and** on the Mac, both sides byte-identical): `pins.json`, `committed_pin_from_head.json`, `env.txt`,
`torch312.freeze.txt`, `data_manifest.json`, `edits_manifest.json`, `gc7rc_forestcover.yaml`, `ancestry.txt`,
`git_{head,refs,diffstat_vs_base,show_stat,status}.txt`, `setup.txt`, `setup_verify.txt`, `push_verify.txt`,
`pytest_port_1gc.log`, `pytest_isolation.log`, `pytest_full_suite_kit.log`,
`pytest_base_known_failures.log`, `cpu_real_smoke/{summary.txt,summary.json,records.json,run_records/*,`
`run_logs/*,result_channels/*}` and `SHA256SUMS`
(sha256 **`2c75842d718f3441423ef6af67928a03247c6d06ed3e06bcd14673349086aed0`**).

## 7. Suitability, D21 notes, blockers and what this does not establish

- **Data obtainable reproducibly: YES.** Public UCI zip, HTTP 200, sha256-pinned at two levels (zip and member),
  re-checked by the frozen parent at every run; setup exit 0 on TASL-2; manifest stable. CC BY 4.0 with
  attribution is the single, clear licence; downloading (not redistribution) is compatible with the kit.
- **Suitable for a noise floor: provisionally YES, with four caveats.** (i) The baseline is deterministic on a
  same-seed repeat (B2 = B1 to the digit on the CPU); (ii) the declared edits move validation accuracy
  (see §4 table: baseline 0.8964, E1 0.8831, E2 0.8993, E3 0.8919, E4 0.9272 — deltas −0.0134 / +0.0028 /
  −0.0045 / +0.0308, against a binomial SE of ≈0.0013 near 0.90, so E1/E3/E4 are many SE and E2 is ~2 SE), so the
  task discriminates proposals (E2's small move is a useful reminder that the funnel must not over-read a
  +0.003 shift at this budget); (iii) the metric is bounded
  accuracy on 58,101 validation rows (binomial SE ≈0.0013 near 0.90), with a trivial majority-class floor of
  48.8 % (class 2) — plenty of headroom and no degenerate "all one class" optimum; (iv) the random stratified
  split shares the known covertype spatial-autocorrelation leakage of the paper's own protocol (that is the
  paper's stated split, not a port choice) — the absolute accuracy is therefore dataset-optimistic, but all
  comparisons within the node are on the same split. No test-based selection is done; the test accuracy is
  sealed.
- **D21 notes (R1-T1-D21-SCOPE).** D21 is the G.1b noise-screening statistic (mean P(wrong) over the D21
  protocol); it is **not measured here** (no GPU, no 460-run G.1b). The kit's role is to make the node ready for
  U2 and the G.1b note; under R1-T1-D21-SCOPE D21 does not select T1 nodes for G.5 (every node that passes U2,
  G.1b fixed-seed determinism and, where run, the cross-host check enters G.5), so this report claims no D21
  verdict. The task's suitability for a **low-noise** floor is supported by (i)–(iv) above but is only
  established by the G.1b run; the kit does not pre-judge it.
- **Blockers/unknowns.** (1) **Suite repository 404** (re-checked 25 Nov 2026): the kit is a paper-semantics
  port, not suite assets; the appendix/funnel must carry the disclosure ("1GC public dataset, port-implemented
  baseline"), which R1-1GC-FALLBACK allows for the dataset but not as a suite. (2) **No GPU/U2/G.1b**: VRAM, GPU
  wall time, GPU fixed-seed determinism, the 10-seed noise floor, the 3× timeout basis and D21/D28 are all
  unmeasured; the CPU smoke is not the census and `port_smoke_gpu.py` must be run on the GPU by the census agent
  with the pinned env/freeze and the pins above (`--gpu-uuid` required for this GPU-capable node). The budget's
  1–2 min claim is about the GPU label run, which is unmeasured here; the CPU smoke's 139.5 s baseline is
  disclosed as an upper bound, not as the census number. (3) The port's budget and run-time estimates are CPU
  measurements; U2 must confirm the GPU time is inside the intended short-run window (and may propose a budget
  change under checklist A). No STOP: the dataset **can** be obtained reproducibly and the task **is** usable for
  a noise-floor port; the remaining items are the reviewer's acceptance and the U2/G.1b runs.

**What this does not establish.** No measurement, no U2 raw cost, no noise floor, no determinism verdict beyond
the CPU fixed-seed repeat, no D21/D28, no label/evidence use, no GPU run and no Track G readiness. It does not
re-check the accepted iso kits or the base harness beyond the ancestry check, and it does not claim the paper's
1GC-7RC assets or evaluation protocol (unavailable). Review is pending.

**AI-assisted: DeepSeek Harness agent (`port-1gc-forest`), delegated by the lead, 25 Nov 2026. ENGINEERING_ONLY.**
