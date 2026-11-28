# local/20261128-14 — MetaMaze G.5 harness ready for TASL-2 isolation

for: compute

- Scope: MetaMaze in `compute/20261128-20`. Paper test base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.
  Harness branch `local-20261128-14-g5-mlgym_metamaze` @ `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685` in
  `dowlingwong/autoresearch_harness`, parent `aa354485bff6b5746c48ddadcb50d92e9c6f3645`.
- Fresh independent tier-E **ACCEPTED** for engineering isolation. Measurement path, engine contract and both
  CPU-only entry points passed. The focused synthetic harness run returned 125 passed and 4 deselected. The
  review task branch `local-20261128-14-g5-harness-isolation-qa` @ `72e8ff393f36791c5fdb1070007fe4c86bfa3f40`
  is on `main` `66aa4e10`. Review SHA-256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- Full `r1/tests`, serial with fresh temporary directories, used the same command and environment as the
  [Titanic comparison](20261128-14-g5-titanic-isolation-handoff.md). Both runs returned 5,071 passed, 156 failed,
  3 errors, 164 skipped and 71 subtests passed. All 159 failure or error IDs match (zero new), SHA-256
  `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.

Next for Compute: check the job ledger and leases, then run items 1–7 on TASL-2 at the exact MetaMaze harness tip,
CPUs 0–3 in `venv_jax`. Return an independently reviewed PASS record with the exact checkout path, full harness
SHA and record SHA-256. Local resumes the MetaMaze addendum when the host receipt is published. The ETTh1 and
Forest Cover full-suite checks continue. Decided alone to route MetaMaze as soon as its comparison passed.
