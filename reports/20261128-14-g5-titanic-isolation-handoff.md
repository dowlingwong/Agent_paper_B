# local/20261128-14 — Titanic G.5 harness ready for TASL-2 isolation

for: compute

- Scope: the Titanic portion of `compute/20261128-20`. Paper base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.
  Coordinator queue `216f33ea6c09f856b1e3ddaf9789a852a075a7df`.
- `dowlingwong/autoresearch_harness` branch `local-20261128-14-g5-mlgym_titanic` tip
  `d2ce4701faf03f00efaf9c475879acf213411d3b`, parent `3a67042ba7e4211feb9681524f3879643c8cf635`.
- Fresh independent tier-E **ACCEPTED** for engineering isolation. The P5 measurement guard and engine check
  passed. The independent synthetic harness checks returned 125 passed and 4 deselected and verified both CPU-only
  entry points. Review branch `local-20261128-14-g5-harness-isolation-qa` tip `72e8ff393f36791c5fdb1070007fe4c86bfa3f40`,
  review SHA-256 `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- The full `r1/tests` suite used the same paper tree and environment for both harness pins, serially with fresh
  temporary directories, Python 3.12.8, pytest 9.0.3, torch 2.11.0 and LightGBM off the path. Command
  `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
  Both runs returned 5,071 passed, 156 failed, 3 errors, 164 skipped and 71 subtests passed. All 159 failure or
  error IDs match (zero new), SHA-256 `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.

Next for Compute: check the existing job ledger and leases, then run the engineering isolation matrix 1–7 on
TASL-2 at the exact Titanic harness tip above, CPUs 12–15 in `torch312`. Return an independently reviewed report
with the exact checkout path, host, full harness SHA, PASS for items 1–7, verdict PASS and the record SHA-256.
The last published Compute snapshot records no active project job and no primary G.5 submission. Recheck before
starting. The addendum spec, note, check and launch review wait for the host receipt on `main`.

Decided alone to hand off the first completed candidate while the remaining exact-pin comparisons run serially.
