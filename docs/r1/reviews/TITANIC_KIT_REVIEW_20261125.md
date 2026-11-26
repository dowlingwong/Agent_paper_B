# Independent review — Track G T1 expansion kit: MLGym Titanic node `mlgym_titanic` (25 November 2026)

**Verdict: ACCEPTED** — the ENGINEERING_ONLY harness kit for R1-T1-NODE-EXPANSION MLGym Titanic
(`mac-trackg-titanic-20261125` @ `3a67042ba7e4211feb9681524f3879643c8cf635`) is accepted for the U2 census and a
new G.1b note, with the MINOR corrections m1–m8 (paper-side record and evidence-root only; the one frozen
spec-comment label is deferred to c8) and the conditions c1–c8 before any census/G.1b run. **No BLOCKING, no
MAJOR.** I verified the branch, push, content, every pin and every SHA in the
record independently, recomputed the committed/deployed pins from the committed blobs, re-fetched the pinned
upstream data and matched all three file hashes, and re-derived the CPU-smoke values, outcomes and isolation
fields from the host run records. The kit is honest about what it did **not** measure (no GPU, no U2, no G.1b,
no noise floor) and flags the two real risks (data-provenance choice and a far-past-convergence budget).

**Reviewer and method.** Fresh independent reviewer (`titanic-kit-reviewer`), delegated by the lead; no
involvement in the port, the data setup, the smoke or the report. Read-only: the only file written in any
repository is this review; no run/edit/commit/push/delete of any repository or host artefact, no HTCondor, no GPU
job, and no test/census re-executed. TASL-2 (`portal_zhixu`, host clock **2026-11-25T04:42 PST = 12:42 UTC**)
was read with `ssh -o BatchMode=yes` using read-only commands only (`ls`, `stat`, `cat`, `sha256sum`,
`sha256sum -c`, `git rev-parse/status/ls-remote/show/log/diff/ls-tree/cat-file/merge-base`, and `curl -s` GETs
whose output was piped, never saved). Pins and canonical hashes were recomputed with read-only Python
(`python -B`, `PYTHONDONTWRITEBYTECODE=1`) that only read files; derived hashes were printed, nothing was
written into the repository, the data root or the capture tree. Capture logs were accepted as captured evidence
(integrity checked, §6) because re-executing tests/runs is outside this review's remit.

**Object under review.**

- Kit branch `mac-trackg-titanic-20261125`, tip **`3a67042ba7e4211feb9681524f3879643c8cf635`**, pushed to
  `origin` (`github.com/dowlingwong/autoresearch_harness.git`); parent/base
  **`c025f89aeafc2199bf3487b4bcaa16678273c702`** = `origin/mac-trackg-t1-tasl-20261121`; host worktree
  `/home/dowling/r1_trackp/wt/titanic-20261125`.
- Report `docs/r1/reports/tasl_chain_20261122/TITANIC_KIT_20261125.md` — **259 lines, 20,796 B, sha256
  `a1844bfef44e742795e6b74eef1738f70bec228bd4e13d6d58aa2eb13457ed10`**; untracked in `ops-tasl-20261116`
  (HEAD `9253192f`) and absent from `origin/main` `912a7e02` (paper-side record; correct, nothing pushed to
  paper `main`).
- Captures `TITANIC_KIT_20261125_captures/` — **51 checksummed files** (52 files including `SHA256SUMS`);
  `sha256sum -c SHA256SUMS` **rc 0** on the Mac, `SHA256SUMS` sha256
  **`e18deca34c5ac3e795dc7b0af5a4a203cf44e70577c14aee4d757494daeccd62`**, `CAPTURES.md` sha256
  `fabd07b4a47a1e7ee903409a64aada00a7b01b6c185c66c778fcc0f7c0adb803`.
- Authority: `R1-T1-NODE-EXPANSION` and `R1-T1-D21-SCOPE` (PLAN on `origin/main` `912a7e02`, row line 1516),
  `R1-BX-D5`, `R1-TRACKG-LICENCES`, `R1-TRACKG-ROLE`, `R1-HARNESS-ISOLATION`, `R1-G1B-TIMEOUT`;
  `TRACKG_PORT_CHECKLIST.md` (§A–§F); the accepted T1 TASL base `c025f89a`.

## 1. Branch, push and content — verified

- Branch exists on `origin` at `3a67042` (`git ls-remote origin refs/heads/mac-trackg-titanic-20261125` = local
  HEAD = the same commit); `git rev-list --count origin/mac-trackg-titanic-20261125..HEAD` = **0** (nothing
  unpushed). The kit commit is contained only in this branch (local and remote) and is **not** an ancestor of
  `origin/main` `3c80b53c`; the base ref `refs/heads/mac-trackg-t1-tasl-20261121` is unchanged at `c025f89a`.
- **Single, non-merge commit**: parent exactly `c025f89a`; author = committer `Dowling Wong
  <wangdowling@gmail.com>`, `2026-11-25 04:28:07 -0800`; subject "trackg T1 expansion candidate 1: MLGym Titanic
  isolated port kit (mlgym_titanic)".
- `git diff --shortstat c025f89a..HEAD` = **20 files, +2,007/−9**, exactly the report's §2 list: the node spec
  (`third_party/mlgym/configs/trackg/nodes/mlgym_titanic.yaml`), the node directory (7 frozen `.py`, frozen
  `LICENCES.md`/`README.md`/`requirements.txt`, editable `train.py`, `representative_edits/` E1–E4 + manifest),
  `tests/trackg/test_port_mlgym.py` (+75/−7, additive: the node is added to `NODES`/`INTERACTING`, the synthetic
  Titanic table and setup-pin test are added; no existing test removed or weakened), and the **1-line**
  `CPU_ONLY_NODES` registrations in `src/autoresearch/trackg/noise_floor.py` and
  `tests/trackg/port_smoke_gpu.py`. No deletion, no rename, no harness-core edit, nothing unrelated.
- Worktree status: **clean** (`git status --porcelain` empty; only ignored `__pycache__/` dirs). The host-specific
  `data` link has been moved aside to
  `/home/dowling/r1_engineering/titanic_20261125/node_data_link_moved_aside_for_commit` so the committed node
  tree has no `data` entry (that is what the option-A committed pin expects); `git ls-tree -r HEAD` contains
  **no task data** (no `.csv` under the node; the only `.csv` files in the tree are the pre-existing harness
  assets).
- Accepted T1 TASL ancestors confirmed on the branch: `68cdd1a` (isolation core), `e85f50b` (its merge),
  `5403392e` (Ada isolation fix), `0c1df3a` (its merge), `f07875de` (MLGym isolated port tip), `c11ef75`
  (option-A committed pin / data-manifest check), `6843847` + `c025f89a` (direct-host/CPU-only chunk support) are
  all ancestors of `c025f89a`.
- Shared-helper claims hold at HEAD: the node's `ar_isolated.py` is
  `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` (= `src/autoresearch/trackg/node_lib/`
  master and every mlab/mlgym node copy); `ar_fixed_loop.py` `28562cfa…`,
  `ar_data.py` `85cec63f…`, `ar_parent.py` `cbef1d38…` are byte-identical to the accepted torch nodes. The
  per-node `ar_worker.py` (`791ea71d…`) is the node-specific worker.
- CPU-only registration is genuinely required and correctly two-sided: the chunk validator in
  `noise_floor.py` refuses `device: cpu` for a node not in `CPU_ONLY_NODES` (`mlgym_houseprice`,
  `mlgym_titanic` now), and `port_smoke_gpu.py` uses the same set to allow a CPU smoke without `--gpu-uuid`.

## 2. Node design and paper/task semantics — verified against the pinned upstream commit

I re-fetched MLGym at the pinned commit
`9d40c1b5035202018cd7091fb4e83a9c68b377c0` (external data, GETs piped): `configs/tasks/titanic.yaml` confirms
task id **`titanicSurvival`** (read `train.csv`, write `submission.csv` predicting `Survived`, scored by
accuracy), dataset `datasets/titanic.yaml` (`data_path: data/titanic/data`), and `data/titanic/evaluate.py`
scores accuracy against `ground_truth.csv`. The task ships **no baseline script** (starter code is only
`evaluate.py`; the task prompt asks the agent to write one), so the report's statement that the editable
`train.py` is the port's own baseline is correct. The port keeps the task surface (same tables, same
`Survived`/accuracy task) but fixes the training loop (frozen worker/parent, fixed step budget, isolated
result channel) — a stated deviation of the Track G port pattern, not a silent one.

Node design matches the spec: editable `train.py` only (`allow_new_files: false`); frozen list covers every
committed node file (`data/` and `representative_edits/` are frozen paths, the spec YAML sits outside the node);
`run_budget {kind: steps, value: 150000}` with no wall-clock key anywhere (the strict loader would refuse one;
`run_command`/`setup_command` carry no time flag); `isolation.entry: run_fixed_budget.py`,
`args: ["--steps", "{budget}"]`; workers `dataloader_workers: 0`, `threads: 4`; determinism defaults
(`cudnn_benchmark: false`, `deterministic_algorithms: true`, `:4096:8`, `PYTHONHASHSEED=0`,
`deterministic_warn_only: false`); `seed_env` two different variables; `selection: {test_scored: true,
selection_split: validation, test_metric_name: test_accuracy}` with the anchored `AR_METRIC val_accuracy=`
regex (test line under a separate `AR_TEST test_accuracy=`), so no test-based selection.
I read `run_fixed_budget.py`/`ar_worker.py`/`ar_fixed_loop.py`: the parent imports no editable code and holds
the result channel and both label arrays; only `ar_worker.py` imports `train.py`; the encoder is fitted on the
**training rows only** (20 % of `train.csv` is validation, 178 of 891 rows, drawn by `AR_SPLIT_SEED`); the test
labels are aligned by `PassengerId` in the parent; the frozen loop counts `optimizer.step()` calls with a
post-step hook and fails (exit 3) unless the count equals the budget; the metric arithmetic (argmax accuracy)
is the parent's. The smoke log shows `AR_SEEDS train=8001 split=8001`, `AR_SPLIT train=713 val=178 test=418`,
`AR_STEPS completed=150000`, `AR_DEVICE cpu`, `CUDA_VISIBLE_DEVICES: ""`.

Representative edits (declared, `measured: false`): E1 `LEARNING_RATE 1e-3→3e-4`, E2 `1e-3→3e-3` (same line as
E1, so E1/E2 conflict as declared), E3 batch norm after every hidden layer, E4 two engineered features in
`_raw_columns`; pair-composability tests cover E1+E3, E1+E4, E2+E3, E2+E4, E3+E4. The manifest's
`baseline_code_state_sha256` and each edit's `code_state_sha256` match the run records' code states (E1
`448a0113…`, E2 `329f04eb…`, E3 `e728a53c…`, E4 `891503be…`, baseline `d6e64df7…`). The declared S1.1
interaction (E2×E3) exists only in the memo — it must be carried into the S1.1/G.1b record explicitly (m8).

## 3. Data preparation, licence and download-only provenance — verified

`prepare_data.py` is a one-off `setup_command` (never part of a run): it GETs exactly three files from
`https://raw.githubusercontent.com/facebookresearch/MLGym/9d40c1b5…/data/titanic/data/`, checks each against a
sha256 pinned in the frozen script, checks shapes (`891×12`, `418×11`, `418×2`) and the `PassengerId` alignment
of `test.csv`/`ground_truth.csv`, writes the hashed manifest last, makes the data root read-only and links it as
the node's `data/`. It requires `--out` under `$AR_TRACKG_DATA_ROOT` and refuses a non-empty `--out` without a
manifest. I re-fetched the three pinned URLs **today** and reproduced the pins exactly:

| file | sha256 (pinned in script, manifest and report) | bytes |
|---|---|---|
| `train.csv` | `4a437fde05fe5264e1701a7387ac6fb75393772ba38bb2c9c566405af5af4bd7` | 60,302 |
| `test.csv` | `5c78320a80dc159b35c408363be46a5d93f078183d539db75ee42a796d6a4e95` | 28,210 |
| `ground_truth.csv` | `af6609cdf1dad0b699bd3414c13e999b2c2f651972f0938254a835985d584306` | 2,839 |

The TASL-2 data root `/home/dowling/r1_engineering/titanic_20261125/data/mlgym_titanic` holds exactly those three
files plus `data_manifest.json` (sha256 **`c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4`**,
equal to the captured manifest and the report), all read-only (`dr-xr-xr-x`, files `-r--r--r--`), 91,351 bytes
total. `LICENCES.md` (frozen) records MLGym's CC-BY-NC-4.0 code licence with attribution and the port's changes,
and the Kaggle competition data as "no explicit licence stated / Kaggle competition terms", pulling no task data
into the branch and never redistributing it — consistent with U1 §3 and checklist F. The data are the
MLGym-forwarded Kaggle tables; their identity with the user's Kaggle download was not row-checked, and the report
states that.

**Provenance deviation (disclosed, not hidden).** `R1-TRACKG-PORT-DECISIONS` (2) required the user's own Kaggle
download for House Prices; the report openly applies a different source here (MLGym's pinned commit, the only
credential-free reproducible source) and offers to switch to a user-provided file with new pins and a new review.
Checklist F explicitly permits hashes known in advance "inside a pinned upstream commit", so this is compliant
with F; whether (2) was intended as a general Kaggle rule is an author/lead decision, not an engineering defect
(condition c6(i)). No new licence decision is introduced by the node (same MLGym CC-BY-NC scope as the other
MLGym nodes).

## 4. Pins, budget, selection and environment — independently recomputed

Every value in the report's §8 was re-derived on TASL-2 from the **committed** tree (committed blob hashes) and
from the host data, not copied:

| field | report | recomputed |
|---|---|---|
| `node_spec_sha256` (loader canonical `raw_sha256`) | `059fd0d50059b4627382979fc9064a9f223f79e06b616eba195eefbb3f3380c1` | equal (independent YAML→`json.dumps(sort_keys, separators, ensure_ascii=False, default=str)`→sha256) |
| spec file sha256 (YAML bytes) | `08876175e02d498b10680d3c35b5969b731404c513ec3fffc858374fa484ddac` | equal (`git cat-file` blob of HEAD) |
| `committed_pin_sha256` (15 frozen files, no data link) | `0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086` | equal (independent JSON canonicalization of the 15 committed blob hashes) |
| `deployed_pin_sha256` (with `data` link, information only) | `4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107` | equal (15 + `data: link:/home/dowling/r1_engineering/titanic_20261125/data/mlgym_titanic`) |
| `edits_manifest_sha256` | `fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce` | equal (committed blob; `measured: false`) |
| `data_manifest_sha256` | `c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4` | equal (host data root and captured manifest) |
| env `torch312` freeze | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages, Python 3.12.16; freeze artifact lists `torch==2.6.0`, run records report `2.6.0+cu124`; numpy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1) | equal to the acceptance census freeze `sweep2/g1b/env/torch312.freeze.txt` (the *content*; the capture artefact is discussed in m5) |
| `ar_isolated.py` = master | `37d99ab0…` | equal (all node copies share the same blob) |
| run budget / selection / sealed | steps 150,000; `val_accuracy` selected; `test_accuracy` sealed in the record | equal (spec, records, `AR_STEPS completed=150000`) |

The full per-file frozen table is in `captures/pins.txt` (15 entries) and matches my committed-blob hashes for
all 15 files; the report's §8 "six `.py` frozen files" should be **seven** (m2). The committed pin is
recomputable without the host-specific `data` link, and the deployed pin adds only that link — the accepted
option-A convention (census uses the committed pin; the deployed pin is what a run record carries and is not
compared to it). The accepted smoke's work copies on TASL-2 contain exactly the committed frozen bytes
(`LICENCES.md a296158a…`, `README.md 94a34466…`, `ar_worker.py 791ea71d…`, `prepare_data.py 8cc046b6…`,
`requirements.txt dd41e686…`, `manifest fd464c6e…`, E1–E4 `e1a6/9e29/dfa0/eb1f…`, `ar_isolated 37d99ab0…`,
`ar_fixed_loop 28562cfa…`, `ar_data 85cec63f…`, `ar_parent cbef1d38…`, `run_fixed_budget eadaf816…`), so the
accepted evidence is of the committed tree, not of an earlier draft. The kit commit (04:28 PST) postdates the
accepted smoke/tests, but the final manifest (04:01) predates the accepted measurements, E1–E3 kept the same
diff shas through every iteration, and the only edit ever measured before it was finalised is the disclosed E4
draft (m7).

## 5. Tests and checklist-E smoke — records verified against the host

- **Port tests**: static **32 passed, 5 deselected**; full (incl. synthetic smoke) **36 passed, 1 skipped** (the
  skip is `mlgym_breakout_minatar`, whose JAX stack is absent from `torch312`); isolation **23 passed, 5
  skipped**; G.1b/noise-floor tooling **33 passed**. The captured logs carry exactly these counts
  (`captures/test_logs/`); the 24-dot/`s`/12-dot pattern of the full log is consistent with 32 static + 4 node
  smokes + 1 JAX skip. The 5 isolation skips are the cgroup/root-dependent tests (not explained in the report —
  m6).
- **Checklist-E CPU smoke (real data, full 150,000 steps, seeds 8001/8001, delegated systemd cgroup,
  `CHECKLIST_E_PASSED mlgym_titanic`)**: I re-read the host run records and result channels; they match the
  report's §7 table exactly:

| run | outcome | val_accuracy | elapsed (s) | effective / waivers / exceptions / `not_forced` |
|---|---|---|---|---|
| `s000_baseline` | ok | 0.775281 | 137.05 | true / {} / [] / [dataloader_workers] |
| `s001` frozen-path diff | refused `scope_violation` | — | — | not executed |
| `s002` NaN diff | divergent `non_finite_loss` | — | 123.352 | true / {} / [] / [dataloader_workers] |
| `s003` = E1 (stub kept) | ok | 0.803371 | 127.05 | true / {} / [] / [dataloader_workers] |
| `E1` | ok (applied) | 0.803371 | 127.074 | true / {} / [] / [dataloader_workers] |
| `E2` | ok (applied) | 0.775281 | 148.343 | true / {} / [] / [dataloader_workers] |
| `E3` | ok (applied) | 0.792135 | 155.759 | true / {} / [] / [dataloader_workers] |
| `E4` | ok (applied) | 0.792135 | 138.668 | true / {} / [] / [dataloader_workers] |
| `B2` baseline repeat | ok | 0.775281 | 136.717 | true / {} / [] / [dataloader_workers] |

  Every executed record has `isolation.effective: true`, `waivers {}`, `exceptions []`, `log_intact: true`,
  `ptrace_scope: 1`, cgroup `kill.empty_after: true`, `frozen_files_checked: 16` (15 committed + the `data`
  link), `frozen_files_changed: []`, `CUDA_VISIBLE_DEVICES: ""`, `cpu_list [8,9,10,11]`, external 8 GiB
  systemd cap, provisional timeout 1800 s (first measuring run), `process.killed_with: null`, and code/diff
  hashes equal to the committed manifest. The log has 15,000 loss lines, no `AR_METRIC`/`AR_TEST` lines and no
  carriage returns; each result channel has exactly one selection and one sealed-test line (63 B), so the
  `check_baseline_log` claims hold. E1/E2/E3/E4 records apply exactly the declared diffs; `s001` is refused by
  the frozen-path scope check; `s002` is a genuine non-finite-loss divergence; `B2` reproduces `s000` to the
  digit (fixed-seed determinism at the recorded seeds).
- **Sealed-test discipline**: every executed record carries a `sealed.test_accuracy` field in the host
  `run_record.json`; it is absent from the manager-view ledger, from `smoke_summary.json` and from the memo —
  verified. I do **not** reproduce the sealed values here. Selection used `outcome.value` (validation accuracy)
  only; nothing in the records or the manager view selects on the sealed metric.
- **E4 rewrite (as disclosed)**: the first E4 draft added `FarePerPerson`/`CabinDeck`; the host attempt
  `cpu_smoke_runs_attempt2_e4_nonfinite/runs_edits/E4/run.log` records exit 4,
  `AR_ERROR build_features' encoder returned non-finite feature values`. I verified the mechanism: `train.csv`
  has **0** missing `Fare` values while `test.csv` has **1**, so a `Fare`-derived column outside `MEDIAN_FILL`
  is finite on the fit rows and NaN on the test row — exactly the reported cause. The final E4 (`eb1f5c86…`)
  uses `FamilyBucket = min(FamilySize, 4)` and `SexPclass = Sex × Pclass` (finite for every row), and the
  synthetic Titanic table now carries missing `Fare` values, so the same bug class is catchable without task
  data. This is an honest, specific disclosure.
- **Failed attempts**: `cpu_smoke_runs_attempt1_module_not_found/` (baseline `ModuleNotFoundError: pandas` from
  a PATH interpreter; its per-edit runs additionally show `PermissionError` on `data/data_manifest.json` from
  the reported `chmod`-through-the-data-symlink incident, with the data root since restored to read-only and
  hashes re-verified) and `cpu_smoke_runs_attempt2_e4_nonfinite/` (E4). Both are kept aside and excluded from
  the accepted record, as the report says.
- Nothing in these records is a GPU run, a census, a noise floor or a campaign/label measurement; the report
  claims none (but see m3 on the phrase "no label read").

## 6. Report and captures accuracy — verified

- `SHA256SUMS` sha256 `e18deca3…` matches and all **51** entries verify (rc 0) on the Mac. Cross-checked against
  TASL-2: **23/51** files are byte-identical at the same relative path under
  `/home/dowling/r1_engineering/titanic_20261125/captures`; the 25 `synthetic_smoke/titanic_run_records/` files
  were renamed from the pytest basetemp `captures/synthetic_smoke/test_synthetic_smoke_mlgym_titcurrent/` and
  all **25 match byte-for-byte** after path mapping; `CAPTURES.md` is Mac-authored (absent on the host). The two
  remaining entries — `test_logs/test_port_mlgym_static.log` and `test_logs/test_trackg_isolation.log` — differ
  from the host's final copies **in elapsed time only** (`7.76` vs `6.69 s`; `8.95` vs `8.75 s`; counts
  identical: 32/5 and 23/5). The curated set was assembled before the host logs were refreshed at 04:26–27 PST;
  no claimed result depends on the timing (m5). The host capture directory itself holds 1,646 files (pytest
  basetemps), so the paper-side set is a curated subset, not a verbatim copy.
- Every number I checked in the report matches a capture or the host: commit/branch/base/push, 20 files/+2,007/−9,
  clean tree, the 15-entry pin table and all four pins, the freeze content, the three data pins/bytes, the test
  counts, the 9 smoke rows (values, elapsed, outcomes), the E4 rewrite evidence and the failed-attempt
  directories. The report's own claims "no data committed", "no test-based selection", "sealed value not copied
  into the memo", "no PR/merge", "nothing pushed to paper main" are all consistent with what I see.
- **No overclaim of measurement found.** The report says no GPU job, no U2 census, no G.1b/noise floor, no
  D21/D28, no label campaign, and that a budget change after the census needs a new review. It flags the two real
  risks itself (data-provenance choice; a 150,000-step budget far past convergence whose edits may separate
  weakly, to be read against the D21 noise floor before the node is committed). Two assertions are overstated and
  are m4 and m3: "the selection metric is stable" (deterministic at fixed seeds — verified — but the only
  cross-seed evidence shows a ~0.034 baseline move between seeds 42/42 and 8001/8001), and "no label read"
  (the smoke's frozen parent did read the labels and record the val + sealed test accuracies; it selected on
  validation only).
- **Suitability / noise-floor read.** At the smoke seed pair, validation accuracy quantises to 1/178 ≈ 0.0056:
  baseline 138/178, E1 143/178, E3 141/178, E4 141/178, E2 138/178, B2 138/178. E2 is indistinguishable from the
  baseline and E3 = E4 at this single seed pair, while E1 moves 5 rows. That is consistent with the report's own
  "far past convergence / edits may separate weakly" caveat and is exactly what the 30-seed D21 noise floor must
  quantify; it must not be read as evidence that any edit is better (the memo does not claim that). Note also
  that under `R1-T1-D21-SCOPE`, D21 does not gate T1 node entry into G.5 (determinism PASS does); the funnel
  must still report the noise floor (c6).

## 7. Findings (no BLOCKING, no MAJOR)

- **m1 (MINOR, wording/authority, paper side; frozen comment deferred).** "R1-T1-NODE-EXPANSION candidate 1"
  is not a label in the PLAN row, which lists four unnumbered candidates (MLGym MountainCarContinuous or
  MetaMaze, MLGym Titanic, 1GC-7RC ETTh1, 1GC-7RC Forest Cover; AG News reserve). Either cite the numbering
  source (the lead's parallel-kit order) or say "the MLGym Titanic candidate" (as the ETTh1 review did for
  "candidate 2"). The same label is in the frozen spec header comment; **do not** churn that file now (see c8).
- **m2 (MINOR, accuracy, paper side).** Report §8 says the frozen pin covers "the six `.py` frozen files"; it is
  **seven** (`ar_data`, `ar_fixed_loop`, `ar_isolated`, `ar_parent`, `ar_worker`, `prepare_data`,
  `run_fixed_budget`), plus `LICENCES.md`, `README.md`, `requirements.txt`, the four diffs and the manifest = the
  15 entries. The pin value itself is right. Also: E4 is described as "two engineered interaction features" but
  `FamilyBucket` is a bucket of `FamilySize`, not an interaction (only `SexPclass` is); and the §7 table's
  "Decision" for `B2` says "applied" although `B2` has `diff: null` and the stub-manager decision `per_edit`.
  Say "two engineered features (a family-size bucket and a sex×class interaction)" and label B2 "per-edit
  campaign / baseline repeat".
- **m3 (MINOR, wording, paper side).** §12 and the status line say "no label read" / "no label measurement".
  Literally, the checklist-E smoke's frozen parent read the task labels and computed both the validation and the
  sealed test accuracies (recorded, sealed, never used for selection). Say "no label campaign/measurement; the
  sealed test accuracy was computed and recorded by the frozen parent for the checklist-E validation only".
- **m4 (MINOR, evidence/disclosure, paper side).** "the selection metric is stable" (§9 risk 4) is not
  supported as written. It is reproducible at fixed seeds (B2 = s000), but the only cross-seed real-data
  observation differs by ~0.034 (an **undisclosed** full-budget baseline run at `AR_TRAIN_SEED=42`,
  `AR_SPLIT_SEED=42` — not the node's defaults, since the default train seed is 0 and the default split seed is
  42: `/tmp/titanic_probe/realrun.out`, 132.8 s, val 0.808989, sealed test accuracy recorded) versus 0.775281 at
  8001/8001 — larger than the E1−baseline smoke step (0.028). Disclose that pre-smoke run as engineering
  validation (it is not a campaign label run), and qualify the sentence as "deterministic at fixed seeds; the
  seed/split sensitivity is what the 30-seed noise floor measures". This is the main substantive risk for
  suitability after U2.
- **m5 (MINOR, captures).** (i) `captures/env/torch312.freeze.txt` is the census freeze **plus** an appended
  `sha256sum` line: its own sha256 is `836b7b86…`, while `d2e70fe4…` is the 77-package content/census-file
  hash (verified) and the adjacent `.sha256` names
  `/home/dowling/r1_engineering/titanic_20261125/captures/torch312.freeze.txt`, a path not in the capture set.
  Split the freeze content from its hash metadata. (ii) The curated capture set is a renamed subset of the host
  tree (§6): document the mapping (`synthetic_smoke/titanic_run_records/` ← the pytest basetemp) and the as-of
  time; two logs from an earlier same-count run should be refreshed or annotated. (iii) §11's inventory says
  "spec/ (node spec + sha), edits/ (… + sha), data_manifest/ (manifest + sha)" although those directories hold no
  separate sha files (the hashes are in `SHA256SUMS`), and it does not mention `CAPTURES.md`, `pins_final.txt`,
  `kit_docs/` or `synthetic_smoke/`.
- **m6 (MINOR, evidence gaps).** No capture of the setup output (the "three fetches, pinned sha256 confirmed"
  claim is true — I independently reproduced the fetch/hashes — but a one-line setup log should be kept); the
  four captured pytest logs contain only the summary line (no command, rootdir, interpreter or date, although
  `commands.txt` has the commands); the isolation suite's 5 skips (cgroup/root-dependent) are unexplained,
  unlike the one port-test skip; the captured `smoke/` set contains the checklist log, ledger and summary but not
  the per-run diff/code-state provenance (host-only), so the paper-side evidence cannot independently re-check
  the manifest↔record bindings.
- **m7 (MINOR, disclosure/no-deletion, paper side + host).** E4 changed after the first real-data smoke; the
  superseded manifests (`d6d8f9903c475b0ac9b924046a035f13b873ab33aa9e4eef7215411e7f836776` with E4
  `c2363a88…`, and `e379e8de1ca6670dec67a7c1b8aa7f910cfb5e06520d7d3830317f97413e3812` with E4 `e1b51dee…`)
  and the failed E4 diff are preserved only in TASL-2 `/tmp/titanic_probe/` and in the failed run record, not in
  the capture set or the durable evidence root. Record their hashes and keep them under
  `/home/dowling/r1_engineering/titanic_20261125/` (checklist C.4 no-deletion spirit; the final manifest is
  `measured: false`, and only the disclosed draft was measured before replacement). Relatedly, §9.7's "two
  checklist-E launches failed … the second because a chmod …" does not match the preserved evidence: the PATH
  failure and the chmod `PermissionError` are both in **attempt1**, while the E4 non-finite failure is the
  **attempt2** campaign disclosed in §6; describe per attempt ("two failed campaigns, three failure events").
- **m8 (MINOR, paper-side record).** (i) The report cites the PLAN row without the plan commit; cite the
  `origin/main` `912a7e02` (row line 1516) as the ETTh1 review does. (ii) The declared S1.1 interaction E2×E3
  appears only in the memo — carry it into the S1.1/G.1b record; the manifest has no field for it. (iii) §3/§9.3
  say the 2-line `CPU_ONLY_NODES` registration is "the only non-node harness change", but
  `tests/trackg/test_port_mlgym.py` is also a (purely additive) harness-side change — scope the sentence to "the
  only non-node functional harness change".

## 8. Conditions before the U2 census and the G.1b spec

- **c1.** This acceptance is recorded before any census. No U2/G.1b run before m1–m8 are applied or explicitly
  waived (all are paper-side or evidence-root corrections, except the frozen spec-comment label in m1, which is
  deferred to c8), and never before c2–c4.
- **c2.** U2 on TASL-2 must run the standard CPU checklist-E/stub-manager smoke at the full 150,000-step budget in
  the pinned `torch312` environment, with a CPU list, a memory cap, `CUDA_VISIBLE_DEVICES` empty and a delegated
  systemd scope; record the host, CPU list, wall times and every run's `run_record.json` with
  `isolation.effective: true`, `waivers {}`, `exceptions []`, `not_forced` = `["dataloader_workers"]` only and a
  fixed-seed repeat. Set `measured_run_seconds` from its own census records (B1, B2, E1–E4) and the timeout
  = 3 × the slowest of those (R1-G1B-TIMEOUT; smoke records excluded) — **note the chunk schema requires
  `measured_run_seconds` in (0, 300]**, and the smoke's worst real-data time was 155.8 s on a shared host: run the
  census on a quiet host, or a reviewed schema change is needed if the slowest record exceeds 300 s. No
  budget/spec change after the census without a new review (checklist A).
- **c3.** Recompute and record on the census host: `node_spec_sha256 059fd0d5…`, spec raw `08876175…`,
  **committed pin `0368a73d…`** (clean tree, no data link), deployed pin `4c0399d9…` (with the link; not the
  census pin), `edits_manifest_sha256 fd464c6e…`, `data_manifest_sha256 c8ccedd0…`, `ar_isolated 37d99ab0…`,
  freeze `d2e70fe4…`; use these fields in the G.1b chunk. The chunk deployment must run the node's
  `setup_command` so `node_dir/data` exists (the chunk's `check_node_pins` verifies `data/data_manifest.json`),
  and the chunk must carry `device: "cpu"`, no GPU UUID, `n_edits: 4`, `timeout_factor: 3.0` and
  `stop_on_timeout: true` (R1-G1B-TIMEOUT: the first T1 run that reaches the declared timeout is a STOP for the
  author).
- **c4.** Confirm and record on the census host that the baseline runs under the forced deterministic settings
  and that a fixed-seed repeat is identical (observed at 8001/8001 in the kit smoke) or that the difference is
  recorded; if the node cannot run deterministically, the port must say so and a re-review is required before any
  G.1b chunk.
- **c5.** The new G.1b spec/note (D21 protocol, 460 runs for this node, seeds, 40 GPU-h expansion cap) is published
  by the coordinating chat only after c1–c4, is itself independently reviewed and launch-checked, uses a new run
  id, and cites the pins above and the measured timeout.
- **c6.** The appendix/funnel and the new note must carry: (i) the **data-provenance decision**: the three tables
  are downloaded from MLGym's pinned commit rather than from a user Kaggle download; if
  `R1-TRACKG-PORT-DECISIONS` (2) is read as covering all Kaggle data (not only House Prices), an author decision
  is required before U2 and a setup change would bring new pins and a new review; (ii) the licence record: MLGym
  CC-BY-NC-4.0, the Kaggle competition data "unknown / not stated", never redistributed, no author/legal line
  yet; (iii) the task-surface deviation: MLGym's task itself provides only train/test and scores test accuracy;
  the 20 % validation split and validation-based selection are the **port's**; (iv) the threat model: the worker
  can read the tables including `ground_truth.csv` (the test labels) and the validation labels, the budget fixes
  optimizer steps not FLOPs, and the worker can answer the parent with logits other than its model's — the S1
  audit must read diffs for label access; the sealed test accuracy is in the run records only, not the manager
  view or the memo; (v) no noise floor, D21/D28, GPU determinism verdict or label/evidence use yet, and under
  `R1-T1-D21-SCOPE` D21 does not gate T1 entry into G.5 — the funnel reports the noise floor regardless; (vi)
  the 178-row validation metric quantises at 1/178, so reported differences are row counts.
- **c7.** Keep the task data out of the repository and bundles; leave the data root read-only; the census must
  fetch the pinned source (hash-checked) and refuse a different revision; do not copy the three tables or
  `data_manifest.json` contents into any branch, report bundle or capture beyond the hash record already kept.
- **c8.** The pins in §4 are the accepted ones. Any change to a committed/frozen kit file after this review —
  including the spec-comment "candidate 1" wording (m1) or any README/LICENCES/train.py comment — changes the
  committed pin and requires a full pin re-derivation and a new review before U2. m2–m8 are to be applied to the
  **paper-side report/captures and the evidence root**, which are uncommitted/pin-neutral;
  `tests/trackg/test_port_mlgym.py` is not in the node's frozen pin, but changing it would change the surveyed
  branch and should be re-reviewed too.

## 9. What this review does not establish

No measurement, no GPU time, no census record, no noise floor/D21/D28, no GPU determinism verdict, no label
campaign/evidence use and no Track G readiness. I did not re-execute the tests or the smoke (read-only review):
their logs, run records, host data and the pinned upstream source were verified for integrity and cross-checked
against the report, and I re-derived the pins and (content-)hash of the environment freeze independently. The
MLGym repository/task and its data files are treated as external, untrusted data; they were used only to check
the port's stated semantics and pinned hashes. The sealed test accuracy exists and is correctly contained in the
run records; its values are deliberately not reproduced here. No legal opinion is given on the Kaggle data terms
or MLGym's CC-BY-NC-4.0.

**AI-assisted: DeepSeek Harness reviewer (`titanic-kit-reviewer`), delegated by the lead, 25 Nov 2026.
ENGINEERING_ONLY. Read-only review; the only file written in any repository is this review.**
