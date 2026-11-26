# T1 expansion candidate 1 — MLGym Titanic isolated harness kit (25 November 2026)

**Status.** An isolated Track G harness kit for node `mlgym_titanic` — R1-T1-NODE-EXPANSION candidate 1,
"MLGym Titanic" — built and tested on TASL-2 (CPU only; no GPU job, no lease, no U2 census, no label
measurement). The kit branch is pushed to `origin`; no PR and no merge was opened. ENGINEERING_ONLY;
AI-assisted. This memo gives the branch, tip and every pin the U2/G1b spec needs, plus the anomalies the
independent review should see.

## 1. Authority and inputs

- PLAN row **R1-T1-NODE-EXPANSION** (candidates fixed: MLGym MountainCarContinuous or MetaMaze, **MLGym
  Titanic**, 1GC-7RC ETTh1, 1GC-7RC Forest Cover; per node: an isolated harness kit (reviewed) → U2 census on
  TASL → G.1b on TASL under a new G.1b note).
- Port checklist `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`; budget row **R1-BX-D5** (fixed step/token budget,
  never wall clock).
- Licence audit `U1_LICENCE_AVAILABILITY_20261117.md` §3 (MLGym = CC-BY-NC-4.0, HEAD
  `9d40c1b5035202018cd7091fb4e83a9c68b377c0`; Kaggle task data: record URL/terms, do not claim a licence).
- Harness repo `https://github.com/dowlingwong/autoresearch_harness` on TASL-2
  (`/home/dowling/r1_trackp/autoresearch_harness`, new worktree
  `/home/dowling/r1_trackp/wt/titanic-20261125`).

## 2. Harness branch and base

- **Branch:** `mac-trackg-titanic-20261125`, created from the accepted Track G T1 base
  **`origin/mac-trackg-t1-tasl-20261121` @ `c025f89`** (`trackg noise_floor (T1 TASL review r1)`).
  That base already carries, in order, the accepted isolation core
  **`68cdd1a`** (merge `e85f50b`), the accepted Ada fix **`5403392e`** (merge `0c1df3a`), the MLGym
  isolated port tip **`f07875de`** (all node `ar_isolated.py` copies = master `37d99ab0…`), the G.1b review
  B1 **option-A committed pin without the host-specific `data` link** (`c11ef75`:
  `noise_floor.committed_view`/`frozen_pin_sha256`), and the TASL direct-host/CPU-only chunk support
  (`6843847`, `c025f89`).
- **Commit(s):** `3a67042ba7e4211feb9681524f3879643c8cf635` (single commit: kit, spec, tests, CPU-only-node registration). Nothing else changed;
  `mac-trackg-t1-tasl` and every other branch are untouched.

## 3. Node design

| Field | Value |
|---|---|
| Node | `mlgym_titanic` |
| Suite / domain | MLGym / tabular |
| Upstream task | `titanicSurvival` (`configs/tasks/titanic.yaml`, dataset `titanic`), commit `9d40c1b5035202018cd7091fb4e83a9c68b377c0` |
| Editable | `train.py` (the port's own baseline — MLGym ships no baseline script for this task: 17 engineered features standardised on the training rows, a two-hidden-layer ReLU MLP with dropout, AdamW warmup + linear decay, cross-entropy; 2 logits) |
| Frozen | `run_fixed_budget.py` (isolated parent), `ar_worker.py` (only process importing editable code), `prepare_data.py`, `ar_parent.py`, `ar_isolated.py` (master `37d99ab0…`), `ar_fixed_loop.py` (`28562cfa…`, byte-identical to the other torch nodes), `ar_data.py` (`85cec63f…`), `requirements.txt`, `LICENCES.md`, `README.md`, `data/`, `representative_edits/` |
| Data | MLGym's forwarded Kaggle "Titanic - Machine Learning from Disaster" tables: `train.csv` (891 × 12, with `Survived`), `test.csv` (418 × 11, unlabelled), `ground_truth.csv` (418 × 2); downloaded from the pinned upstream commit at setup, **never redistributed** |
| Split | 20 % of `train.csv` (178 rows of 891, at seeds 8001 and at the default split seed 42) is validation, drawn by `AR_SPLIT_SEED`; the rest trains; the task's `test.csv` is the sealed test set, labels aligned to it by `PassengerId` |
| Metrics | selection `val_accuracy` (maximise, `^AR_METRIC val_accuracy=(\S+)$`); sealed `test_accuracy` (`^AR_TEST test_accuracy=(\S+)$`); loss `^step \d+ loss (\S+)$`, steps `^step (\d+) loss \S+$` |
| Budget | `run_budget: {kind: steps, value: 150000}`, exactly 150,000 optimizer steps (post-step hook); an edit may change compute per step, not the step count |
| Workers / determinism | `dataloader_workers: 0`, `threads: 4`; determinism defaults (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`, `PYTHONHASHSEED=0`) |
| Isolation | `isolation.entry: run_fixed_budget.py`, `args: ["--steps", "{budget}"]`; the parent holds the runner's result channel and the worker imports the editable code |
| CPU-only | yes — the worker pins the model and tensors to the CPU; `mlgym_titanic` is in `CPU_ONLY_NODES` in `src/autoresearch/trackg/noise_floor.py` and `tests/trackg/port_smoke_gpu.py` (the only non-node harness changes; without them the U2/G1b chunk engine refuses a chunk for a CPU-only node that is not on its list) |
| Environment | `/home/dowling/r1_tracks/t1_tasl/envs/torch312` (Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1); `uv pip freeze` sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages), **identical to the committed census freeze** `sweep2/g1b/env/torch312.freeze.txt` |

**Runtime at the budget.** The checklist-E smoke (full 150,000 steps, seeds 8001/8001, 4 threads, real data,
inside a delegated cgroup) measured `baseline 137.1 s, E1 127.1 s, E2 148.3 s, E3 155.8 s, E4 138.7 s and the repeat baseline 136.7 s (the deliberately broken run took 123.4 s)`. The host was shared with other agents' port work
(load average 8–22 observed); with 4 threads and no contention, 150,000 steps of this model are ≈60–90 s. The
U2 census must measure its own baseline on TASL-2 and set the timeout
= 3 × its slowest record (R1-G1B-TIMEOUT); the log of one full run is ≈0.39 MB (15,000 loss lines).

## 4. Data preparation, manifest and licence

- `setup_command`:
  `test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_titanic"`.
- `prepare_data.py` downloads exactly three files from
  `https://raw.githubusercontent.com/facebookresearch/MLGym/9d40c1b5035202018cd7091fb4e83a9c68b377c0/data/titanic/data/{train.csv,test.csv,ground_truth.csv}`,
  checks each against the sha256 pinned in the frozen script (the bytes of the pinned commit), checks the
  tables' shapes and the `PassengerId` alignment of `test.csv`/`ground_truth.csv`, writes the hashed data
  manifest, makes the directory read-only and links it as the node's `data/`. No Kaggle account/API is
  needed; nothing is committed.
- Setup output (TASL-2, 25 Nov): three fetches, pinned sha256 confirmed, manifest
  **`c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4`** (3 files, 91,351 bytes); see
  `captures/data_manifest/`.
- **Licence / provenance** (`LICENCES.md`, frozen): MLGym code/data layout under CC-BY-NC-4.0 with the
  attribution and the list of port changes; the three tables are Kaggle competition data ("Titanic - Machine
  Learning from Disaster"), **no explicit licence stated** (Kaggle competition terms), MLGym's CC-BY-NC does
  not relicense them; the port downloads them at setup and records the hashes; the branch holds no task
  data and the tests use synthetic tables only. Caveat for review: the household precedent
  R1-TRACKG-PORT-DECISIONS (2) required the user's own Kaggle download for House Prices; here the data are
  fetched from MLGym's pinned commit (the only reproducible, credential-free source; a Kaggle download
  needs an account and is not reproducible). If the reviewer prefers a user-provided file, that is a
  prepare_data/setup_command change with new pins and a new review (no data effect).

## 5. Isolation and frozen pins

The kit uses the accepted isolated pattern: the runner starts the frozen parent directly (no shell), the
parent holds the result channel and never imports editable code, and only `ar_worker.py` imports `train.py`
(R1-HARNESS-ISOLATION). Every node copy of `ar_isolated.py` equals the harness master
`37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610`; the other shared frozen files are
byte-identical to the accepted nodes (`ar_fixed_loop.py 28562cfa…`, `ar_data.py 85cec63f…`,
`ar_parent.py cbef1d38…`). The node spec's `frozen_paths` lists every committed file.

- **Committed pin** (`frozen_pin_sha256(committed_view(frozen_file_hashes(node))`, 15 frozen-file entries,
  no `data` link):
  **`0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086`**, recomputed from
  `git archive HEAD third_party/mlgym/nodes/mlgym_titanic` at the branch tip (not from a working copy) and
  identical to the pre-commit computation.
- **Deployed pin** (as the run records carry it, with the setup `data` link → host path):
  **`4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107`**.
  The census/chunk convention is the committed pin (option A, `noise_floor.committed_view`); the deployed
  pin is what a run record holds and is not compared to the committed pin.
- Checklist-E smoke isolation: every executed record `effective: true`, `waivers: {}`,
  `exceptions: []`; `frozen_files_checked: 16` (15 committed + the data link); worker sandbox, cgroup
  `cgroup.kill` and `ptrace_scope 1` recorded.

## 6. Representative edits E1–E4 (declared before any measurement)

Manifest: `third_party/mlgym/nodes/mlgym_titanic/representative_edits/manifest.json`,
sha256 **`fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce`**
(`schema trackg_representative_edits/v1`, `measured: false`, `node_spec_sha256 059fd0d5…`,
`run_budget {steps, 150000}`).

| Edit | Change | sha256 |
|---|---|---|
| E1 | `LEARNING_RATE = 1e-3 → 3e-4` (smaller step) | `e1a6a46e7e537143ba560f1942c45f9d1dc7e636fbb392075671a088d70a7a63` |
| E2 | `LEARNING_RATE = 1e-3 → 3e-3` (larger step; same line as E1, so E1/E2 conflict) | `9e2973b9bba9dc70b75dc3b5a95833e014d7658f9d667e366f2c18b8556a6c9b` |
| E3 | batch normalisation after every hidden layer (architecture detail) | `dfa07242010a39737b409d687e12f382a32a9e4385186be4f3c8201efdd21107` |
| E4 | two engineered interaction features `FamilyBucket`, `SexPclass` in `_raw_columns` (code-level feature change; finite for every row, so it composes with the imputation) | `eb1f5c86017d58e0b80efdcde1f8e05bd4aa4ef7a4b260ca5c61248836923c31` |

Pair composability (`tests/trackg/test_port_mlgym.py::test_interacting_edits_compose`): E1+E3, E1+E4, E2+E3,
E2+E4, E3+E4 apply in both orders; E1+E2 conflict (same line). **Declared interaction for S1.1: E2 × E3**
(a 3× higher learning rate with and without batch normalisation). No edit is expected to diverge; E2 is a
standard AdamW rate.

**Note for the review on E4.** The first E4 draft added `FarePerPerson`/`CabinDeck`; it passed the synthetic
smoke but **failed the real-data checklist-E smoke** (exit 4, "encoder returned non-finite feature values")
 because `test.csv` has one missing `Fare` and the new column inherited the NaN before the frozen
imputation step. E4 was rewritten to use always-finite features, and the synthetic table now carries
missing `Fare` values so the same bug class is caught without the task data. The failed smoke attempt is
kept in `cpu_smoke_runs_attempt2_e4_nonfinite/` (TASL-2; not part of the accepted record).

## 7. Checks run (25 November 2026, TASL-2)

| Check | Command (from the kit root) | Result |
|---|---|---|
| Static port tests | `PYTHONPATH=src python -m pytest tests/trackg/test_port_mlgym.py -q -k "not smoke"` | **32 passed, 5 deselected** (spec loads, scopes, frozen copies, manifests re-declared byte-identically, scope refusals; `captures/test_logs/test_port_mlgym_static.log`) |
| Full port tests incl. synthetic smoke | `PYTHONPATH=src python -m pytest tests/trackg/test_port_mlgym.py -q` | **36 passed, 1 skipped** (the skip is `mlgym_breakout_minatar`, whose JAX packages are not in `torch312`; `captures/test_logs/test_port_mlgym_full.log`) |
| Isolation tests | `PYTHONPATH=src python -m pytest tests/trackg/test_trackg_isolation.py -q` | **23 passed, 5 skipped** (`captures/test_logs/test_trackg_isolation.log`) |
| G.1b tooling after the CPU-only-node registration | `PYTHONPATH=src python -m pytest tests/trackg/test_trackg_noise_floor.py -q` | **33 passed** (`captures/test_logs/test_trackg_noise_floor.log`) |
| Checklist-E CPU smoke, real data, full budget, seeds 8001/8001, cgroup-isolated | `python -m tests.trackg.port_smoke_gpu --node mlgym_titanic --cpus 8-11 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo> --provisional-timeout 1800` inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` | **PASS — `CHECKLIST_E_PASSED mlgym_titanic`** (`captures/smoke/`) |

The smoke ran the baseline, a frozen-path diff, a deliberately broken diff and E1 through the stub manager,
then E1–E4 and a second baseline, at the full 150,000-step budget on the real data:

| Run | Decision | Outcome | val_accuracy | elapsed s |
|---|---|---|---|---|
| s000_baseline | baseline | ok | `0.775281` | `137.05` |
| s001 | not_run_refused | scope_violation | – | – |
| s002 | discarded_divergent | non_finite_loss (`nan`) | – | `123.35` |
| s003 (E1 stub) | kept | ok | `0.803371` | `127.05` |
| E1 | applied | ok | `0.803371` | `127.07` |
| E2 | applied | ok | `0.775281` | `148.34` |
| E3 | applied | ok | `0.792135` | `155.76` |
| E4 | applied | ok | `0.792135` | `138.67` |
| B2 (repeat baseline) | applied | ok, same value as s000 | `0.775281` | `136.72` |

Every executed record: complete `run_record.json`, `isolation.effective: true`, `waivers {}`,
`exceptions []`, `determinism.not_forced == ["dataloader_workers"]`, `process.killed_with: null`, no
`sealed` key in the manager view; `check_baseline_log` saw the loss/step patterns, exactly one selection
line and one sealed-test line in the result channel and none in the log, and no carriage returns. The sealed
test accuracy stays in the run records (not copied into this memo).

## 8. Pins and fields for the U2/G1b spec (all values computed on the kit at the branch tip)

```
node_spec_sha256        = 059fd0d50059b4627382979fc9064a9f223f79e06b616eba195eefbb3f3380c1
                          (canonical spec.raw_sha256, what the harness records/checks)
spec file sha256        = 08876175e02d498b10680d3c35b5969b731404c513ec3fffc858374fa484ddac
                          (the YAML's own bytes; informational)
committed_pin_sha256    = 0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086
                          (frozen_pin_sha256(committed_view(frozen_file_hashes)); 15 entries, no data link)
deployed_pin_sha256     = 4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107
                          (with the setup data link; what a run record carries)
edits_manifest_sha256   = fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce
data_manifest_sha256    = c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4
env (torch312) freeze   = d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42
                          (Python 3.12.16, 77 packages; sha256 of uv pip freeze; matches the census freeze)
host / device           = TASL-2; CPU only (no GPU, CUDA_VISIBLE_DEVICES empty)
budget                  = steps 150000
seeds                   = AR_TRAIN_SEED / AR_SPLIT_SEED (split default 42)
editable / frozen       = train.py / the list in §3
setup_command           = test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_titanic"
run_command             = python3 run_fixed_budget.py --steps {budget}
isolation               = entry run_fixed_budget.py, args ["--steps", "{budget}"]
selection               = val_accuracy (max, validation split); sealed test_accuracy
```

The manifest's `node_spec_sha256` equals the canonical value above; the frozen pin covers
`LICENCES.md`, `README.md`, the six `.py` frozen files, `requirements.txt`, the four diffs and the manifest.
The full per-file pin table is in `captures/pins.txt`.

## 9. Risks, anomalies and open points for the reviewer/lead

1. **MLGym CC-BY-NC 4.0 in an MIT harness tree** — pre-existing suite issue (U1 §3; the other MLGym nodes
   carry the same `LICENCES.md` scope statement). No new licence decision is introduced by this node.
2. **Data provenance choice** (§4): downloaded from MLGym's pinned commit rather than the user's Kaggle
   download; data licence "unknown/not stated"; identity with the Kaggle files not row-checked. If the
   reviewer applies R1-TRACKG-PORT-DECISIONS (2) strictly, this needs a prepare_data/setup change and new
   pins. The data manifest and pinned sha256 make either source checkable.
3. **CPU-only registration** is the one non-node harness change (`CPU_ONLY_NODES` in
   `noise_floor.py`/`port_smoke_gpu.py`, 2 lines). It is required for U2/G1b on a CPU-only node; the
   G.1b tooling tests pass (33). The census must run CPU chunks (no GPU UUID, `CUDA_VISIBLE_DEVICES` empty).
4. **Budget is large for a 891-row task** (150,000 steps). It is a genuine step bound (the frozen loop counts
   optimizer steps), and the selection metric is stable, but the model is far past convergence and edits
   may separate weakly; the D21 noise floor should be read before committing the node. Changing
   `run_budget.value` changes `node_spec_sha256` and the manifest, so it needs re-declared edits and a new
   review.
5. **Host load / timeout.** TASL-2 was shared with other port work during the smoke (load 8–22), so the
   measured times are conservative and variable; the U2 census sets the timeout = 3 × its own slowest
   record. The full-budget log is ~0.39 MB.
6. **Tooling anomaly, not the node.** The static port-test suite run *inside* the delegated cgroup scope
   segfaulted once in the pre-existing House Prices test (pandas 3.1.1 `to_csv` of a 1460×80 table); the same
   suite outside the scope and the isolated smoke runs inside the scope are fine. Disclosed so a reviewer
   does not attribute it to this kit.
7. **Operational notes.** Two checklist-E launches failed before any accepted run: the first because the
   run's `python3` came from `PATH` without the node environment (fixed by putting `torch312/bin` first on
   PATH, as the census procedure already does), the second because a `chmod 644` wildcard on the node
   directory had followed the `data` symlink and removed the data directory's execute bit (restored to the
   setup's read-only mode; hashes unchanged and re-verified by the manifest). The accepted smoke is the one
   reported here; the failed attempt directories are kept aside on TASL-2.
8. **No U2/U census, no GPU job, no label measurement** was run; the lead runs U2 after independent review.

## 10. Reproduction

```
# branch (TASL-2 worktree)
git -C /home/dowling/r1_trackp/wt/titanic-20261125 log --oneline -1        # 3a67042ba7e4211feb9681524f3879643c8cf635
# setup (outside the repo)
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/titanic_20261125/data
python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_titanic"
# static + synthetic tests
PYTHONPATH=src python -m pytest tests/trackg/test_port_mlgym.py -q
# checklist-E CPU smoke (real data, full budget, isolated)
python -m tests.trackg.port_smoke_gpu --node mlgym_titanic --cpus 8-11 \
  --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
  --runs-root /home/dowling/r1_engineering/titanic_20261125/cpu_smoke_runs --provisional-timeout 1800
# pins (from the kit root, with the harness on PYTHONPATH)
python3 - <<'PY'
from pathlib import Path
from autoresearch.trackg.node_template import load_trackg_node_spec
from autoresearch.trackg import isolation
from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256
spec = load_trackg_node_spec(Path("third_party/mlgym/configs/trackg/nodes/mlgym_titanic.yaml"))
node = Path("third_party/mlgym/nodes/mlgym_titanic")
print(spec.raw_sha256, frozen_pin_sha256(committed_view(isolation.frozen_file_hashes(node, spec.frozen_paths))))
PY
```

## 11. Captures (this directory)

`TITANIC_KIT_20261125_captures/` — `spec/` (node spec + sha), `edits/` (E1–E4 + manifest + sha),
`data_manifest/` (manifest + sha), `env/` (torch312 freeze, sha, Python version), `test_logs/` (static, full,
isolation, noise-floor), `smoke/` (checklist-E log, ledger summary, run-record summary), `pins.txt`,
`kit_files_sha256.txt`, `git.txt`, `commands.txt`, `SHA256SUMS`. Evidence roots on TASL-2:
`/home/dowling/r1_engineering/titanic_20261125/` (data, captures, smoke runs) and the kit worktree
`/home/dowling/r1_trackp/wt/titanic-20261125`.

## 12. What was not done

No U2 census, no G.1b/noise floor, no GPU job, no lease, no label read, no test-metric selection, no PR/merge,
no change to `mac-trackg-t1-tasl` or any other branch, no push to paper main.
