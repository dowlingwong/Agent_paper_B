# C3 B.1 e1 environment replay — operator report (ENGINEERING_ONLY)

**Verdict: STOP.** No actual replay of the 16 fixed cases was possible. The reviewed driver
`r1/scripts/c3_env_replay.py` refused the whole 16-case set at its predeclared **OpenML hard STOP**
before scheduling any case, because OpenML offline dataset availability and worker network denial
are not verified. The authorization (`docs/r1/authorizations/c3_env_replay_20261116.md` @ `4da73306`,
R1-E1-AUTH) retains that refusal and forbids bypassing it. Zero-tolerance PASS cannot be evaluated:
0 of 16 cases ran, so this is not a pass.

- **Authorization:** `docs/r1/authorizations/c3_env_replay_20261116.md` @ `4da73306`, basis R1-B2-REPLAY-GO.
- **Reviewed mechanism:** M3 `ec6e30a9` (`docs/r1/reviews/MAC_M3_REVIEW_20261104.md`,
  `MAC_M3_REVIEW_20261109.md`) + IT-1 (a) `5ef9db16` (`M3_DRYRUN_PATH_REVIEW_20261114.md`).
- **Protocol / cases:** `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md` and
  `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` §1.
- **Host:** deepthought, CPUs only, workers = 1, `CUDA_VISIBLE_DEVICES=""`, thread env = 1.
- **Operator:** deepthought operator session, 2026-11-16 (one operator per host). No B.2, no audit,
  and no other deepthought job was started.

## 1. What was run, in the authorized order

All commands are verbatim in `commands.txt`. Everything ran inside the preserved batch environment:
`. <batch>/env.sh`, `AR_HARNESS_ROOT=<batch>/autoresearch_harness`, `PYTHONDONTWRITEBYTECODE=1`,
batch-venv `python -B -m r1.scripts.c3_env_replay`.

1. **Deployment.** Fresh clone of `git@github.com:dowlingwong/Agent_paper_B.git` (default `main` →
   `9ae6d877`), then checked out **exactly the reviewed pin** `5ef9db16faf0d43843a5e8110b9181173b49175c`
   (detached). `5ef9db16` was verified to be an ancestor of `origin/main` (and of the
   `mac-m3-dryrun-path-20261114` tip `129317d1`). Driver file SHA-256
   `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8`, byte-identical at `5ef9db16`
   and `9ae6d877`. Deployment path: `/ceph/dwong/r1_e1_20261116/agent_paper_B`.
2. **Dry run first, into a new dry-run out dir.** Exit 0, `{"label": "DRYRUN", "cases": 16, ...}`.
   Retained: `.../results/r1/engineering/C3_env_replay_20261116T094408Z_dryrun/replay_plan.json`
   (SHA256 `a5f04ef271ba5eab57543f238c2c2b82481a303fb19e5a454ad2accb5f055ba6`; copy in this
   directory). Plan inspection is §3.
3. **Real replay second, into a different new out dir** (no `--dry-run`). Exit **2**:
   ```
   {"verdict": "STOP", "reason": "STOP: OpenML offline dataset availability and worker network denial are not verified; no replay scheduled"}
   ```
   The driver raised inside `run()` **before** `out.mkdir()` and before `check_environment`,
   `check_harness` and `check_resources`. The real out dir was therefore **not created**, the
   `/tmp/r1_c3_env_replay_20261116T094408Z` scratch was **not created**, and the driver emitted no
   `cases.jsonl`, `summary.json` or `STOP.json`. `STOP.json` here is operator-authored and says so.

No retry was made. Everything is retained; nothing was deleted.

## 2. Pre-execution environment checks (operator read-only recheck)

The authorization's pre-run protocol requires the operator to independently re-verify the host. The
driver's own environment checks were **never reached** (the OpenML STOP precedes them at lines
588–590), so the values below are **operator read-only observations, not the driver's verdict** and
cannot supply a PASS. Full capture: `logs/env_observations.log`; pins: `pins.json`.

| Check | Observed | Pin | Result |
|---|---|---|---|
| Batch `python`/`python3` wrappers | both `#!/bin/sh` `exec /ceph/dwong/r1_prepare_20261025/venv/bin/python "$@"` | shared venv | match |
| Interpreter realpath / prefix | `.../python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13` / `.../venv` | Python 3.13.15 | match |
| Library versions | sklearn 1.8.0, numpy 2.4.4, pandas 3.0.3, scipy 1.17.1 | same | match |
| Full package list | 59 packages, normalized SHA256 `c09242ac…` | 28 Oct observation `c09242ac…` | match |
| Newest dist-info mtime | `2026-10-26T22:09:12.359336Z` | must precede `2026-10-27T15:48Z` launch | match |
| Freeze vs current list | only addition `narwhals==2.27.1` | allowed addition only | match |
| Batch `uv.lock` SHA | `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` | same | match |
| 25 Oct freeze SHA | `c760b28f2d03cfd31ae491b13b13ec6a348caee603b051349d9f85f9af282406` | same | match |
| Harness | HEAD `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean | clean pinned commit | match |
| Worker `python3` on batch PATH | the batch wrapper | batch wrapper | match |
| Disk / file-count headroom | `/` 136.7 GB free, `/ceph` 377.99 TB free; ceph 400,104/1,500,000 files used | Ceph 50 GiB + file floor | match |
| Co-tenancy (O4) | ~1.13 cores used, **~38.9 of 40 free** at both checks | leave ≥ 10 free | PASS |

Pre-existing condition recorded, not caused here: the preserved harness working tree has untracked
`nodes/openml_{breast_w,credit_approval,ionosphere,wdbc}/data_cache/` directories and
`paper/tables/artifact_completeness_report.txt`; the driver's tracked-clean test ignores untracked
files. Those caches are exactly the presence-only "evidence" the M3 review found insufficient
(see §4).

## 3. Dry-run plan inspection

`replay_plan.json` is labelled `DRYRUN`, schema `r1.c3_env_replay/1`, `tolerance: 0`,
`comparison: "emitted metric token, exact; no re-rounding"`, `environment: DEFERRED_TO_HOST`,
`harness_commit: 6adf3859…`, thread env `OMP/OPENBLAS/MKL_NUM_THREADS=1`, `llm_requests: none`.
Corpus binds the frozen index `812468e2…`, sidecar `bb6d891c…`, frozen trees `6b1c0c61…` /
`468e57ce…`, original blobs verified; collector binding `ccb4712`, blob `0001260442f9…`, both seed
bindings present. The 16 selected cases match the declared list in `MAC_M3_DRYRUNS_20261104.md` §1
exactly:

| Case | Node | Seed | Metric | Recorded token | Decision |
|---|---|---|---|---|---|
| `digits_mlp__s104:t001` | digits_mlp | 104 | val_score | 0.718663 | kept |
| `digits_mlp__s104:t002` | digits_mlp | 104 | val_score | 0.799443 | kept |
| `tabular_mlp__s102:t001` | tabular_mlp | 102 | val_score | 0.738750 | kept |
| `tabular_mlp__s102:t002` | tabular_mlp | 102 | val_score | 0.909325 | kept |
| `openml_breast_w__s105:t001` | openml_breast_w | 105 | val_auc | 0.992351 | kept |
| `openml_breast_w__s105:t002` | openml_breast_w | 105 | val_auc | 0.992351 | discarded |
| `openml_ionosphere__s103:t001` | openml_ionosphere | 103 | val_auc | 0.941176 | kept |
| `openml_ionosphere__s103:t002` | openml_ionosphere | 103 | val_auc | 0.941176 | discarded |
| `openml_wdbc__s100:t001` | openml_wdbc | 100 | val_auc | 1.000000 | kept |
| `openml_wdbc__s100:t002` | openml_wdbc | 100 | val_auc | 1.000000 | discarded |
| `openml_credit_approval__s100:t001` | openml_credit_approval | 100 | val_auc | 0.895052 | kept |
| `openml_credit_approval__s100:t002` | openml_credit_approval | 100 | val_auc | 0.895052 | discarded |
| `openml_sonar__s105:t001` | openml_sonar | 105 | val_auc | 0.844538 | kept |
| `openml_sonar__s105:t002` | openml_sonar | 105 | val_auc | 0.844538 | discarded |
| `openml_climate__s104:t001` | openml_climate | 104 | val_auc | 0.889961 | kept |
| `openml_climate__s104:t002` | openml_climate | 104 | val_auc | 0.889961 | discarded |

12 of the 16 cases are OpenML; the 4 local MLP cases cannot be replayed on their own under the
authorized 16-case protocol.

## 4. The STOP: what is missing and where it stopped

**Where it stopped.** `r1/scripts/c3_env_replay.py` @ `5ef9db16`, in `run()`:

```python
if any(case['node'].startswith('openml_') for case in cases):
    raise Stop('STOP: OpenML offline dataset availability and worker network denial are not verified; no replay scheduled')
```

This runs after all source checks — output/scratch-new, no LLM modules, `verify_corpus`
(index/sidecar/manifests/frozen trees/original blobs), `verify_collector_binding`, and
`select_cases` (all 16 cases recovered; every recovered patch equals the recorded patch, every
archived log carries the recorded token, trial 1 kept, trial 2 continuing from the trial-1
incumbent, pinned NodeSpecs consistent) — and **before** any case is scheduled and before
`check_environment`/`check_harness`/`check_resources`. So all pre-execution source checks passed on
the host; only the OpenML gate blocked execution. `execute_case()` independently refuses an
individual OpenML case for the same reason.

**What it checks / why it refuses.** For a real run the driver will not accept an OpenML case at
all. Its only offline evidence path (`has_cache_files`, lines 434–436) treats *any* non-placeholder
file under a node's `data_cache` as availability, copying the collector's `PILOT_DATA_CACHE` when
absent. The M3 independent review of 4 November 2026 (Major 1) found this insufficient: a cache
containing only an unrelated file returns true, and the pinned harness `6adf385` node
`benchmark.py` calls `fetch_openml(..., data_home=...)` without `download_if_missing=False` or any
other demonstrated network denial, so a partial/unrelated cache could pass preflight and start a
worker download. That review's re-check records that the hard STOP "does not prove offline
availability or implement the 16-case replay"; gate A1 is OPEN/partial and A4 (offline) is OPEN.
The 9 November review of the accepted M3 overnight unit records: "Wiring into
`c3_env_replay.run` is correctly left out; the production OpenML STOPs are unchanged."

**Missing mechanism (what an independent review must first accept).** A reviewed mechanism that
(a) proves the *exact* datasets for the six OpenML nodes are available offline, bound to the exact
task/data identity rather than any cache file, and (b) enforces no network download in worker
subprocesses while preserving the frozen worker's numerical semantics — then, and only then,
wired into `c3_env_replay.run` and independently reviewed. Until then the authorization's Open
execution STOP stands and a 16-case replay cannot pass. A passing environment recheck cannot
change this STOP; only that mechanism can.

## 5. State left behind (nothing deleted, nothing reused)

| Item | State |
|---|---|
| Deployment checkout | `/ceph/dwong/r1_e1_20261116/agent_paper_B` @ `5ef9db16` (clean except the untracked dry-run out dir) |
| Dry-run out (retained) | `/ceph/dwong/r1_e1_20261116/agent_paper_B/results/r1/engineering/C3_env_replay_20261116T094408Z_dryrun/` (plan SHA `a5f04ef2…`) |
| Real out dir | not created (the driver raised before `mkdir`) |
| Scratch `/tmp/r1_c3_env_replay_20261116T094408Z` | not created |
| Preserved batch | untouched (only read); key hashes in `pins.json` |
| Harness | unchanged, `6adf3859…`, `uv.lock` `dd42d018…` |
| Processes | no lingering replay/worker processes; driver ran and exited in seconds |
| Deletions | none; nothing moved to `_to_delete/` |

The preserved batch, the corpus, `/tmp` scratch and all historical evidence are unchanged.

## 6. Evidence inventory (this directory)

- `REPORT.md` — this report.
- `STOP.json` — operator-authored STOP record (the driver emitted none).
- `replay_plan.json` — retained dry-run plan, SHA256 `a5f04ef271ba5eab57543f238c2c2b82481a303fb19e5a454ad2accb5f055ba6`.
- `cases.jsonl` — empty (0 cases ran; the driver never wrote it).
- `pins.json` — authorization, code/harness/interpreter/source/batch pins and hashes.
- `commands.txt` — exact commands and exit codes.
- `cotenancy.log` — O4 co-tenancy output (both checks).
- `logs/` — `dryrun.stdout.log`, `dryrun.stderr.log`, `real.stdout.log`, `real.stderr.log`,
  `env_observations.log`.
- `SHA256SUMS.txt` — hashes of the evidence files.

## 7. What this does and does not establish

- It establishes that on deepthought, at the reviewed pin, every pre-execution source check of the
  authorized 16-case replay passes and the fixed 16 cases are recovered exactly, and that the
  driver's predeclared OpenML hard STOP blocks execution for want of the offline/no-network
  mechanism.
- It does **not** establish any replayed metric, any environment PASS from the driver, or any
  B.1/B.2 result. No B.2 work was started and no audit was performed. The decision-record
  disclosure about a confirmed replay does not apply.
