# B2 repair disposition evidence, 2026-10-08

This is the bounded re-check of B2-R1–R4. Original review report and probe outputs are preserved in their original directory. Original scratch clone remains at b09c85a0cd67a67cf4c1f5918091a4ae41ee6173. Repaired code is the B-only working-tree diff captured in reviewed_repairs.diff; reviewed_sha256.json binds exact reviewed bytes. No repair/source edits, model, task realism, authorization, commit or push were performed.

Executed commands from the author B-only checkout:

```sh
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python -m unittest discover -s tests/control -p 'test_evaluate_tree.py' -v > /private/tmp/B2_recheck/evaluate_tests.log 2>&1
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python -m unittest discover -s tests/control -p 'test_timing.py' -v > /private/tmp/B2_recheck/timing_tests.log 2>&1
B2_REVIEW_ROOT="${B2_CODE_CHECKOUT}" OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/identity.py > /private/tmp/B2_recheck/identity.json
B2_REVIEW_ROOT="${B2_CODE_CHECKOUT}" OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_recheck/repair_probe.py > /private/tmp/B2_recheck/repair_probe.json
B2_REVIEW_ROOT=/private/tmp/B2_rereview_20261008 OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_recheck/regression_detection.py > /private/tmp/B2_recheck/regression_old.json
B2_REVIEW_ROOT="${B2_CODE_CHECKOUT}" OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_recheck/regression_detection.py > /private/tmp/B2_recheck/regression_repaired.json
```

All commands exited 0. The old-code regression failures/errors are intentional observed evidence captured by regression_detection.py, not passing tests. It imports the selected code first, then loads the new tests from the B-only working copy. No historical source reconstruction is used here: the original reviewed B-only clone provides the pre-repair code.

repair_probe.py uses common.py from the original scratch package; copy that existing file alongside the probe or adjust sys.path when replaying elsewhere. Bounds: original identity3 worlds×100 draws; repair probe1 cutoff check×20draws and3 mask scenarios×20draws; regression detection5cases×2code states. No additional noise/realism study. All original review scope limits and author gates remain.

Repository copies replace workstation checkout paths with `<B_MAC_CHECKOUT>`; raw artifacts remain in scratch. Set B2_REVIEW_ROOT to the reviewed code checkout and B2_TEST_ROOT to the repaired tests/control directory for old-code detection. SHA256.json hashes these portable copies; source hashes in the report remain unchanged.

For replay set B2_CODE_CHECKOUT to the actual B checkout. The copied probes resolve common.py in the sibling original package. To test old code, additionally set B2_TEST_ROOT to the repaired B tests/control directory. Paths under scratch document the actual original executions.
