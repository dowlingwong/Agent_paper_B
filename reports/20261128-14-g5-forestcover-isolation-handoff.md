# local/20261128-14 — Forest Cover isolation handoff and four full-suite comparisons

for: compute

- Scope: Forest Cover in `compute/20261128-20`. Harness branch `local-20261128-14-g5-gc7rc_forestcover` @
  `3f7b09febf401a83f3aa881f00eecdd032024416` in `dowlingwong/autoresearch_harness`.
- Fresh independent tier-E **ACCEPTED** for engineering isolation at all four exact pins. Measurement path,
  engine contract and both CPU-only entry points passed per node. The independent synthetic engine run returned
  125 passed and 4 deselected per candidate. The review branch `local-20261128-14-g5-harness-isolation-qa` @
  `72e8ff393f36791c5fdb1070007fe4c86bfa3f40` is on `main` `66aa4e10`. Review SHA-256
  `4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- Full `r1/tests` ran serially at paper base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`, with an exact clean
  harness checkout at each parent and tip, Python 3.12.8, pytest 9.0.3, torch 2.11.0, no LightGBM and a fresh
  `TMPDIR` for each run. Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
- All eight runs returned **5,071 passed, 156 failed, 3 errors, 164 skipped and 71 subtests passed**. All 159
  failure and error IDs agree across all eight runs. Zero new IDs. The harness checkouts stayed tracked-clean.
  [Matching failure and error IDs](20261128-14-g5-harness-full-suite-ids.txt), SHA-256
  `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea`.

| Node | Exact census base | Exact candidate | New failures or errors |
|---|---|---|---:|
| Titanic | `3a67042ba7e4211feb9681524f3879643c8cf635` | `d2ce4701faf03f00efaf9c475879acf213411d3b` | 0 |
| MetaMaze | `aa354485bff6b5746c48ddadcb50d92e9c6f3645` | `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685` | 0 |
| ETTh1 | `3a06d86721b0c1826b165b68a9781a561e4993f4` | `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c` | 0 |
| Forest Cover | `85851664679d10889c5af406843c4a3fc38f7a49` | `3f7b09febf401a83f3aa881f00eecdd032024416` | 0 |

Next for Compute: check the ledger and leases, then run items 1–7 for Forest Cover on TASL-2 at the exact
candidate above, CPUs 4–7 in `torch312`. Return an independently reviewed PASS record with the exact checkout
path, full harness SHA and record SHA-256. The ETTh1 check remains available under its separate handoff.
Local fills the 1GC specs and unsigned notes after the exact-pin records are published. The Titanic and MetaMaze
campaigns have a separate [launch-tree STOP](20261128-14-g5-titanic-metamaze-launch-tree-stop.md).

Decided alone to compare each candidate to its actual census-kit parent with the same fixed paper tree and to
send each ready node independently. No host or evidence job was submitted by Local.
