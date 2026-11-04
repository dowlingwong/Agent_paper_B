# M3 independent review — 4 November 2026

**Verdict: NOT ACCEPTED.** Independent review by Codex (AI-assisted), performed from a separate local clone at `d09acb63` (identical tree to worker head `ec4af062`) against base `f98e315e`. No host was contacted, no real replay, model, or GPU was run, and no historical evidence was modified. This is an M3 preparation review, not authority for e1 or B.2.

## Major 1 — offline execution is not established

`r1/scripts/c3_env_replay.py` lines 423–435 and 493–499 treat the presence of **any** non-placeholder file under `data_cache` as evidence that an OpenML task can run offline. A temporary fixture containing only `unrelated.txt` returns `has_cache_files(...) == True`. The pinned harness `6adf385:nodes/openml_ionosphere/benchmark.py:175–176` calls `fetch_openml(..., data_home=...)` without `download_if_missing=False` or another demonstrated network denial. A partial or unrelated cache can therefore pass preflight and start an attempted download in the worker. The replay protocol requires a STOP before scheduling if a configuration needs a download; a later changed-cache or failed-run check cannot establish that condition. Require and test a genuinely offline preflight for the exact selected node/data and a fail-closed execution path that cannot download, preserving the frozen worker's numerical semantics. Re-review any implementation tradeoff.

## Major 2 — audit dry run does not protect the frozen corpus or verify the pinned sidecar

`r1/scripts/c3_audit_dryrun.py:124–129,161–162` accepts any new output path, including a new path inside a frozen sweep. It then creates that directory and report. The handoff §6 and gate B17 say both drivers refuse output within the corpus, but this driver has no such check. Resolve paths and refuse destinations inside the frozen corpus or preserved batch, including symlink aliases, before creating anything; add fixture coverage.

Additionally, `build_table` lines 59–68 hashes the index **against the sidecar's own index field**, and manifests against values supplied by that same sidecar, but never compares the sidecar itself to the fixed R1-SWEEP1-CLASSIFY SHA256. The report merely prints its hash. Original-blob verification is valuable but does not establish the sidecar's identity; changing an unrelated sidecar field leaves these checks satisfiable. The claimed SHA-bound sidecar/corpus provenance therefore is not fully verified. Bind both index and sidecar to the fixed published digests, and test tampering even when internal hashes are self-consistent. `--no-git` remains explicitly non-verifying and cannot supply the original-blob guarantee.

## Major 3 — e1 instructions conflict with the new-output guard

`docs/r1/proposals/AUTH_DRAFT_c3_replay_20261104.md:36–42` tells the operator to run the same command with `--dry-run` and then without it, including the same `--out`. `c3_env_replay.py:549–550,568–571` creates that directory on the dry run and refuses any existing output on the next call. The prescribed sequence deterministically stops before the real replay. Specify two distinct new output paths and preserve the dry-run artifact; test the documented sequence with synthetic sources. This finding does not authorize execution.

## Additional test portability finding

The fixture `test_resources_require_new_local_tmp_scratch_and_headroom` assumes Linux `findmnt` before testing headroom. On this Mac it fails before reaching the expected headroom condition, although the host-specific guard fails closed. Mock the mount probe when testing headroom, and retain a separate Linux/host integration check. This does not by itself imply the Linux report's results are wrong.

## Evidence and scope checked

- `git diff 9bab3d6f ec4af062 -- r1/c3/train/run.py r1/c3/train/trainer.py r1/c3/env.py r1/c3/control.py r1/c3/prior_model.py` is empty. The handoff describes these inherited changes, including unmarked-row effects in `train/run.py` and `control.py`; the author's packet (a) decision remains open. This observation is not acceptance of those changes or their later integration.
- `r1/c3/audit.py` extracts the population partition after retaining the original evidence authorization, source, table hash, and replay checks in `evidence_plan`. Existing B1 publication, B4 task-native attestation, and B6 launch-bound freeze STOPs remain open as described; a passed dry run or this review cannot close them.
- In the local Python 3.11 harness venv, the four focused files `test_c3_env_replay.py`, `test_c3_audit_dryrun.py`, `test_c3_evidence_other_boundaries.py`, and `test_c3_launch_provenance.py` gave **71 passed, 1 skipped, 1 failed** in 21.65 s; the failure is the macOS `findmnt` portability issue above. The initial system Anaconda Python 3.9 attempt failed collection because it lacks `tomllib`; it is not the target Linux Python 3.13 environment. I did not independently reproduce the two full Linux suites or the production host environment. The prior worker's full-suite counts remain attributed to that report.
- The exact emitted-token comparison is stricter than numerical float equality and is explicitly disclosed in the handoff. The 16-case replay remains a bounded check, not a launch snapshot or proof for every root, even if later passed.

The author still decides e2, the five inherited files, and the open publication, runtime-attestation and historical-environment gates. The same reviewer should re-check the fixes and final diff; no code or launch acceptance is implied here.
