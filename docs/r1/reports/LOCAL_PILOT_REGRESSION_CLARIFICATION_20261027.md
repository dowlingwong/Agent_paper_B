# Pilot regression tests after author clarification — 27 October 2026

AI-assisted. This records CPU engineering regression tests only, not Track P training or evaluation evidence. The 19 Oct pilot was used read-only as the existing fixture. Tested paper base `fa87d7957925929ae97fb85bab7310f6ec249471` plus the removal of the unconditional skip decorators in the three named test files. Harness `897d83c8efa364ec2fdd37288241cc42e01d7274`. No pilot source files were modified.

The temporary Python 3.13.4 environment used NumPy 2.4.4, SciPy 1.17.1, scikit-learn 1.8.0, LightGBM 4.7.0 and a locally extracted Homebrew libomp 23.1.4. The first attempt (26 passed, 5 failed) exposed a missing libomp and the pre-existing soft-label hash mismatch; the second used a temporary libomp and finished **30 passed, 1 failed in 10.29 s**. It ran:

```sh
DYLD_LIBRARY_PATH=/private/tmp/paper-b-openmp/libomp/23.1.4/lib CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PATH=/private/tmp/paper-b-local-20261026-venv/bin:$PATH AR_HARNESS_ROOT=/private/tmp/paper-b-local-harness-20261026 /private/tmp/paper-b-local-20261026-venv/bin/python -m pytest -q r1/tests/test_c3_env.py r1/tests/test_c3_prior_model.py r1/tests/test_trackp_soft_label_v2.py --tb=short
```

The H.1/H.8 tests passed. `r1/tests/test_trackp_soft_label_v2.py::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical` failed on its first seed-split comparison: expected `5960856db849b59a839d225c8f39af21b253eebff21c6c71b1fecb0da178ccd7`, actual `57d5f45a2f8965a9617c6774bd7b95ee7578026ce8aa51c12405446464cacdbf`. The later comparison and evaluation assertion in that test were not reached. No reference or acceptance criterion was altered; environment/version versus code/data causes remain unestablished. A previously documented restricted baseline also recorded byte-identity failures (`LOCAL_BASELINE_CLARIFIED_20261027.md`); this observation alone does not establish that the causes coincide.
