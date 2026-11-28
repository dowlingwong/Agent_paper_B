# local/20261128-14 — ETTh1 G.5 harness ready for TASL-2 isolation

for: compute

- Scope: ETTh1 in `compute/20261128-20`. Paper test base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.
  Harness branch `local-20261128-14-g5-gc7rc_etth1` @ `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c` in
  `dowlingwong/autoresearch_harness`, parent `3a06d86721b0c1826b165b68a9781a561e4993f4`.
- Fresh independent tier-E **ACCEPTED** for engineering isolation. Measurement path, engine contract and both
  CPU-only entry points passed. The focused synthetic harness run returned 125 passed and 4 deselected. The
  review branch `local-20261128-14-g5-harness-isolation-qa` @ `72e8ff393f36791c5fdb1070007fe4c86bfa3f40`
  is on `main` `66aa4e10`. Review SHA-256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- Full `r1/tests`, serial with fresh temporary directories, used the same command and environment as the
  [Titanic comparison](20261128-14-g5-titanic-isolation-handoff.md). Both runs returned 5,071 passed, 156 failed,
  3 errors, 164 skipped and 71 subtests passed. All 159 failure or error IDs match (zero new), SHA-256
  `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.

Next for Compute: check the ledger and leases, then run items 1–7 on TASL-2 at the exact ETTh1 harness tip,
CPUs 16–31 in `torch312`. Return an independently reviewed PASS record with the exact checkout path, full
harness SHA and record SHA-256. Local resumes the ETTh1 addendum when the host receipt is published. The
Forest Cover full-suite comparison continues. Decided alone to route ETTh1 as soon as its comparison passed.
