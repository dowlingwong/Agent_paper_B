# Deepthought independent preparation — 25 October 2026

AI-assisted by GPT-6 (Codex). ENGINEERING_ONLY, not evidence.

## Outcome

The Batch B–independent environment and data preparation are complete. The requested baseline suites ran, but **the runner test gate is not accepted**: retry/resume integration checks remain unresolved after bounded engineering retries. Full Phase 2 acceptance is not claimed. Phase 3 continued independently and is reported in [NOISE_FLOOR_CLIMATE_20261025.md](NOISE_FLOOR_CLIMATE_20261025.md). Stop before Phase 4 as the author requested.

| Phase 2 item | Status |
|---|---|
| 1–2: final merged backend and sweep harness pin | Deferred; Batch B is absent from published main |
| 3: locked libraries / Python 3.13 environment | Complete, with the patch-version difference below |
| 4: paper and harness suites | Executed; runner integration acceptance remains blocked |
| 5: eight pool nodes plus climate data | All nine independently checked; all seven OpenML caches pass offline checks |

## Source and environment provenance

Fresh, isolated preparation roots are under `/ceph/dwong/r1_prepare_20261025/`; the pre-existing host checkout was not reset. Paper source is published main `3d3ec488be5e1cdcb12ee66b8130305fc9c7db26`. Final ref verification still showed that main commit and no Batch B merge.

The preparation harness is **`7305434c7506512fca741c91751936fbd099fd81`**, the snapshot named in the Batch A handoff and containing the adopted climate reserve adapter. The published harness `r1` branch was only at `4012897`; the exact local committed delta was imported with a verified 13 KiB Git bundle. No harness commit was published or rewritten. This snapshot is **not substituted for main's C3 sweep pin** (`4d68c54875654cf9986daa1cf36d609adb48ef45`); final sweep pin verification remains deferred. Both canonical source trees were tracked-clean at the final census.

Canonical environment: `/ceph/dwong/r1_prepare_20261025/venv`, built with uv 0.12.5 and the unchanged harness lock. Lock SHA-256: `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090`.

| Component | Verified version |
|---|---|
| Python | 3.13.15, Clang 22.1.3 |
| scikit-learn | 1.8.0 |
| NumPy | 2.4.4 |
| pandas | 3.0.3 |
| SciPy | 1.17.1 |
| LightGBM extra used for paper tests | 4.7.0, installed without changing locked dependencies |

The common-run manifest records Python **3.13.16**, but this host's uv has no downloadable build for that patch. The runbook specifies Python 3.13; the nearest available patch, 3.13.15, was used and recorded. The metric-library versions match exactly. This is not an assertion of a byte-identical reference environment or cross-platform metric equivalence. The original common run was aarch64; this host is x86_64.

Engineering attempts were recorded by item: paper clone HTTPS credential prompt → existing SSH authentication; preparation harness missing from the published branch → exact committed bundle; environment system-Python inspection error → unavailable managed 3.13.16 → managed 3.13.15 success. No item was silently counted as successful and no pin, node or acceptance threshold was changed.

## Data checks

Missing caches were fetched using each node's own loader, then `r1.noise.check_caches` ran with its network block active. It returned 7/7 OpenML nodes `ok`, including NODE_INFO and D25 categorical/imputer consistency. The two non-OpenML nodes are deliberately `skipped` by that command; separate network-disabled `load_pool()` calls verified them.

| Node | Data source/check | Shape | Verdict |
|---|---|---|---|
| `digits_mlp` | bundled/generated, offline | 1797 × 64 | ok |
| `tabular_mlp` | bundled/generated, offline | 2000 × 20 | ok |
| `openml_breast_w` | OpenML 15, cached/offline | 699 × 9 | ok |
| `openml_ionosphere` | OpenML 59, cached/offline | 351 × 34 | ok |
| `openml_wdbc` | OpenML 1510, cached/offline | 569 × 30 | ok |
| `openml_credit_approval` | OpenML 29, cached/offline | 690 × 15 | ok |
| `openml_sonar` | OpenML 40, cached/offline | 208 × 60 | ok |
| `openml_blood_transfusion` | OpenML 1464, cached/offline | 748 × 4 | ok |
| `openml_climate` | OpenML 1467, cached/offline | 540 × 20 | ok |

Climate has class counts `1: 46`, `2: 494`, minority share 46/540 = 0.085185…, no categorical columns and no missing values. The node's positive label is `2`. Existing NODE_INFO values match; no source correction or new metadata test was needed.

## Test results and unresolved checks

| Run | Result |
|---|---|
| Initial full paper suite, canonical environment / Ceph scratch | **317 passed, 5 failed, 6 skipped**, 675.89 s |
| First targeted retry of retry/permanent test, local scratch environment copy | **1 failed**, 85.29 s: fake liveness admitted only one of two nodes; permanent-failure scenario passed |
| Final targeted C3 integration module, same source/packages with fully local runtime and scratch | **1 passed, 2 failed**, 316.25 s |
| Scripted live-golden retry in local scratch | **1 passed**, 0.41 s |
| Harness full suite on same-commit local scratch clone | **427 passed, 9 failed, 1 collection error**, 51 subtests passed, 64.62 s |

The paper's known `test_real_runner_desktop_dryrun` failure remains. All three C3 integration tests initially failed under the Ceph setup; the retry/permanent test hit its 170 s subprocess timeout. The live-golden failure was an explicit `OSError: [Errno 122] Disk quota exceeded` in `tempfile.mkdtemp`; it passed unchanged in local scratch.

The final targeted module kept all deadlines and assertions unchanged. Its watchdog test **passed**, including detected SIGTERM, restart and whole-root recovery. The retry scenario still exceeded its **75 s** limit. The interruption scenario failed the archive assertion for **`openml_breast_w__s105`** (`c3_sweep_dryrun.py`, `check_interrupt`, assertion requiring the interrupted root archive and partial ledger). These are unresolved checks, not a proved runtime regression or scientific liveness verdict. The retry/permanent test reached its three-attempt limit and was not run a fourth time. No seeds, nodes, liveness threshold or deadline were adjusted to pass.

Harness totals match the handoff's count baseline, but the failing set is not identical: four artifact-completeness/manifest tests (including `test_checked_in_report_contains_all_plan_campaigns`), five KDD section tests, and the expected `test_legacy_noop_skip.py` collection error. The ClawWorker extraction test that failed in the handoff passed here. The additional checked-in artifact-report failure is recorded rather than silently categorized as already accepted. These historical manuscript/artifact tests do not establish a C3 pipeline failure or clear the runner gate.

## File quota and bounded recovery

The host returned `Disk quota exceeded` while creating directories/files. Native counters showed `ceph.quota.max_files=500000`, with `max_bytes=0`; the shared filesystem still reported about 303 TiB free. Quotas can constrain file count independently of bytes, and reporting can lag, as documented in the [Ceph quota documentation](https://docs.ceph.com/en/latest/cephfs/quota/). No quota was changed, no root action was taken, and nobody was contacted.

New scratch work and the second climate attempt were routed to local `/tmp`, on the same host with the same inputs. Only this task's inventoried reproducible caches were removed: the idle uv cache (uv reported 8,848 files / 305.0 MiB) and 2,120 `.pyc` files plus 282 empty cache directories under its own environment/runtime. Source, installed packages, GGUF, compiled binaries, datasets, ledgers and all run records were preserved. A canonical environment source-file hash and all four metric-library versions were verified after cleanup. No shared filesystem saving is inferred from these logical cache counts.

Final native snapshot: 421,393 files and 77,715 subdirectories beneath the 500,000 file-count quota. This is limited headroom, not storage readiness for a long sweep; check quota again before future host writes. The interrupted climate attempt is preserved and never pooled into the completed pilot.

## Cleanup, retained records and boundary

One orphaned **fake** server from the failed retry fixture was stopped only after its recorded PID, process group, exact command, port and models directory matched. No owned fake server remained; the final GPU compute-process query was empty. Other workloads were not signalled.

Raw setup/test records remain under `/ceph/dwong/r1_prepare_20261025/` and `/tmp/r1_prepare_dwong_20261025/`; only this summary and STATUS are pushed. No actual sweep config, PLAN decision or author authorization note was written. Before later execution, Batch B must be published/merged and the deferred source/pin/tests checks redone. The current task stops before Phase 4 regardless.
