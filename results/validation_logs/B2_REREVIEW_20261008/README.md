# B2 independent AI-assisted reproduction package, 2026-10-08

Reviewed repository: https://github.com/dowlingwong/Agent_paper_B.git
Reviewed HEAD: b09c85a0cd67a67cf4c1f5918091a4ae41ee6173.
Scratch clone: /private/tmp/B2_rereview_20261008.
Scratch interpreter: /private/tmp/B2_rereview_env/bin/python (Python 3.13.4).
Dependencies installed exactly from requirements.lock. All probes are bounded, CPU-only.
No repository source is edited. In-memory monkeypatches restore original functions.
Set B2_REVIEW_ROOT to another fresh GitHub clone pinned to the reviewed HEAD.

Actual commands (run from the fresh clone except probes, which locate it via common.py):

```sh
git clone https://github.com/dowlingwong/Agent_paper_B.git /private/tmp/B2_rereview_20261008
/opt/homebrew/bin/python3.13 --version
/opt/homebrew/bin/python3.13 -m venv /private/tmp/B2_rereview_env
/private/tmp/B2_rereview_env/bin/python -m pip install -r requirements.lock
/private/tmp/B2_rereview_env/bin/python -m unittest discover -s tests/control -v > /private/tmp/B2_control_tests.log 2>&1
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/identity.py > /private/tmp/B2_probes/identity.json
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/maxbias.py > /private/tmp/B2_probes/maxbias.json
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/maxbias2.py > /private/tmp/B2_probes/maxbias2.json
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/planted_maxbias_test.py > /private/tmp/B2_probes/planted_maxbias_test.json
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/eval_semantics.py > /private/tmp/B2_probes/eval_semantics.json
OPENBLAS_NUM_THREADS=1 /private/tmp/B2_rereview_env/bin/python /private/tmp/B2_probes/harness.py > /private/tmp/B2_probes/harness.json
git status --porcelain
```

The first clone failed in the sandbox with DNS unavailable; the permitted network retry succeeded. Lockfile installation succeeded on the first install attempt.

Bounds: identity uses 3 worlds × 240 development/240 test roots × 100 bootstrap draws; maxbias uses 3 noise levels × 100 independent repetitions × 100 roots; maxbias2 uses 100 repetitions with 100 training/100 fresh test roots; plant uses the existing 40-repetition test twice; eval_semantics uses at most 100 draws per scenario plus 72,000 allocator perturbations; harness uses 100 draws and 2 noise levels × 100 repetitions. Context-world U is clipped to [0,1]. The Gaussian null probes intentionally violate bounded U to amplify a training-noise mechanism and reproduce the prior review's stress test; they are not population-bound experiments or scientific results. Their confidence intervals are repetition-level mean ±1.96 standard errors, not the manuscript's family intervals.

Historical limit: old_oof reconstructs the described in-sample second-stage decision, with current ridge helpers and data. It is not a historical source checkout or exact old-byte verification. No source repository or Paper A was accessed.

The JSON outputs and test log are observed artifacts, not regenerated expected outputs. See the report for findings and limitations. The output package is advisory; it records no authorization and does not resolve author novelty/BAVAR gates.
