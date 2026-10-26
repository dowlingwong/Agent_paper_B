Paper L0 CPU baseline, 2026-10-26 UTC
Paper clone: /private/tmp/paper-b-baseline-paper-20261027/clone
Paper HEAD: 1f5c27ed0731917d52a3f58b07ea2e1633b78c11
Harness: /private/tmp/paper-b-harness-local-20261027 at 897d83c8efa364ec2fdd37288241cc42e01d7274
Both clones clean after runs. No commits, downloads, real model weights, GPU or remote operations.

Main: run.py, run.json, run.log, junit.xml. make r1-test, exit 2, 111.086 s wall; pytest: 510 passed, 55 failed, 34 skipped, 2 deselected (109.25 s). 52 failures report PermissionError errno 1. One process discovery assertion returned [] for a spawned PID; the sandbox denied an independent ps query, although causality is not established. Two byte-identity assertions fail: synthetic exam compressed output differs from committed output, while committed output matches its own SHA; v1 pilot table assembly hash differs from its reference. Full assertion evidence in log and XML.
Main skipped: 24 unavailable local tokenizers, 9 missing lightgbm, 1 local-only pilot table.

Excluded files and exact collected IDs: excluded-collection.log (collection-only invocation; no tests executed). test_trackp_model.py and test_trackp_sidecar_loader.py were initially excluded conservatively over model inference; subsequently separately tested as permitted random-weight CPU unit tests below. test_c3_sweep_dryrun.py, test_c3_control_dryrun.py and test_exam_dryrun.py were excluded conservatively because they execute synthetic dryrun campaign/label or evidence pipelines. Additional deselections: r1/tests/test_trackp_trainer.py::test_kill_and_resume_matches_an_uninterrupted_run (previously exceeded 10 min) and r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun (executes desktop campaign dryrun). No evidence or label-producing campaign executed intentionally.

Focused: focused-run.py, focused-run.json, focused-run.log, focused-junit.xml. Random tiny CPU model tests: exit 1, 9.596 s wall; 8 passed, 1 failed, 39 skipped (8.16 s). Failure test_tree_mask_matches_the_spec_formula_and_kev: ModuleNotFoundError for kev. All 39 skips cite missing pool tokenizers under empty HF_HOME. No cases known to exceed 10 minutes in focused selection. Environment and exact commands in JSON and scripts. Empty HF_HOME, HF/Transformers offline, CUDA_VISIBLE_DEVICES empty, threads 1; no MPS selected by inspected code.
