# Evidence map — (b) and (i)–(iv), R1-E1-OPENML-AMEND, e1 run 2026-11-17

Every item below is produced by `r1/scripts/c3_env_replay.py` +
`r1/c3/e1_openml_offline.py` + `r1/c3/e1_offline_network.py` at the deployed tip
`bbcfc4a9` (reviewed code `5bddab73`), inside this run, and is retained in this
directory. "Field" refers to `replay_plan.json` /
`environment.openml_offline_mechanism` unless stated otherwise.

| Clause | Requirement (row R1-E1-OPENML-AMEND) | Code path | Runtime evidence (this run) | Observed |
|---|---|---|---|---|
| **(b)** | Worker subprocesses have **no network** — enforced, not assumed | `e1_offline_network.install()` at the start of `run()` (before numpy/sklearn import); `enforce()` proves in-process + worker-representative child; inherited by every worker; `reverify()` after the last case | `environment.openml_offline_mechanism.network` (`in_process`, `worker_subprocess`); `summary.json` `openml_offline_mechanism.post_run.network` | `seccomp_mode: 2`; `socket(AF_INET)`, `socket(AF_INET6)`, `connect` all errno **101 ENETUNREACH** in-process and in child; 21 syscalls blocked; re-proven post-run; all 16 workers ran under it |
| **(i)** | OpenML data id equals the sweep-1 record | `verify_dataset_ids()` reads `git show 6adf3859:configs/nodes/<n>.yaml` and `nodes/<n>/dataset.json` (pinned commit, not worktree) and compares five sources | per-node `dataset_id` and `dataset_identity.sources` | 15/59/1510/29/40/1467; sources `harness_node_spec`, `harness_dataset_json`, `sweep1_cache_check`, `audit_cache_check`, `audit_node_spec` all equal per node; dataset name/target cross-checked |
| **(ii)** | Sweep-1 loaded-data fingerprint, recomputed on the same cache, equals value by value | `bind_cache_check()` (sha/mtime/pre-launch) + `verify_fingerprints()` using the sweep's own `r1.noise.check_caches.check_node`, run under the already-installed (b) denial | per-node `loaded_data_fingerprint`, `authority.sweep1_record`, `environments` | all six nodes equal on the ten fields; record sha `35e76f37…`, mtime `15:22:39Z` < launch `15:48:34Z`; versions Python 3.13.15 / sklearn 1.8.0 / NumPy 2.4.4 / pandas 3.0.3 |
| **(iii)** | Cache ARFF md5 equals the OpenML `md5_checksum` in the cache metadata | `verify_arff_md5()` / `_arff_consistency()` (decompress metadata + ARFF, id/file_id consistency) | per-node `arff` (`metadata`, `arff`, `file_id`, `md5_checksum`, `arff_md5`) | equal for all six: 15 `88633c06…`, 59 `23dd3c8b…`, 1510 `7aa183d3…`, 29 `a948be96…`, 40 `3ab630fb…`, 1467 `c3d91dc5…` |
| **(iv)** | Every cache file SHA-256 and tree digest unchanged before/after use and equal to `OFFLINE_MECHANISM_AUDIT.json` | `snapshot_cache()` before scheduling; `verify_case_cache(...,'before'/'after')` per OpenML case; `verify_source_caches()` after the last case | per-node `cache_files` (24 non-dotfile hashes), `cache_tree_digest`; per-case `cases.jsonl` `openml_offline_cache_checks`; `summary.json` `post_run.source_caches`; `logs/postrun_integrity2.log` | 24/24 file SHA-256 and 6/6 tree digests equal the audit; before/after phases on all 12 OpenML cases; post-run source digests equal; independent operator re-read matches (`ALL_SIX_CACHES_UNCHANGED_AND_AUDITED = True`) |
| **Order** | (b)+(i)–(iv) proved **before** the out dir is created | `run()` order: token → `enforce()` → corpus/cases → host/batch/env checks → `prepare()` → `out.mkdir()` → write plan with `state = VERIFIED` → first case | `replay_plan.json` `written_utc 00:48:26Z`, mechanism report `written_utc 00:48:32Z`, out dir birth `00:48:32.946Z`, plan birth `00:48:32.949Z`, first raw-log mtime `00:48:36.102Z`; plan `openml_offline_mechanism.state = VERIFIED` | plan with `VERIFIED` predates the first case; a (b)/(i)–(iv) failure would have raised before `out.mkdir()` (fail-closed) |
| **Pass rule** | All 16 cases exact tokens + every environment check PASS, unchanged | `case_passes()` (`TOLERANCE = 0`, emitted token, no re-rounding), `check_environment`/`check_harness`/`check_resources` | `cases.jsonl` (16 rows), `summary.json`, `environment` in plan | 16/16 exact; `changed_files: []`; `data_cache_unchanged: true`; `verdict: PASS`, `stop: null`; all environment checks passed |

## Tamper/failure behaviour (fail-closed, from the reviewed code)

Any mismatch or unreadable input raises `MechanismStop`/`NetworkDenialStop` → driver `Stop`
before `out.mkdir()`, retaining artifacts and writing no retry. The accepted independent review
(`docs/r1/reviews/E1_AMEND_REVIEW_20261117.md`, rounds 1–2) verified the tamper paths by fixture
tests; this run did not observe any STOP.

## Files

- `replay_plan.json` — real-run plan incl. the full (i)–(iv)+(b) report and `state = VERIFIED`.
- `cases.jsonl` — 16 case results incl. per-case before/after cache checks.
- `summary.json` — driver PASS, post-run source-cache digests and network re-proof.
- `raw/*.log` — raw worker logs (16).
- `dryrun/replay_plan.json` — dry-run plan (`DEFERRED_TO_HOST`).
- `pins.json` — code/harness/batch/venv/host/co-tenancy/seccomp pins.
- `logs/` — command logs, co-tenancy, preflight, post-run integrity, seccomp evidence.
