# G.5 houseprice TASL-2 CPU-set check — PASS (28 Nov 2026)

Task `compute/20261127-33` item 1 (with the disposition `compute/20261128-05` item 2). ENGINEERING_ONLY.
Rule R1-TASL2-CPU; G.5 plan S13/S14 (three sealed attempts, CPUs 0-7, bit-identical to the declared TASL-2
reference, each run within 9.486 s).

- **Base:** `origin/main` `a98d2eff1d2847e34f00effe66b53bc00467e936`.
- **Host:** TASL-2, CPUs 0-7 on physical cores 0-3, GPU lease held (`gpu0.lock`) together with `cpus-0-3.lock`
  and `cpus-4-7.lock` for the whole check.
- **Checkout:** detached `paperB_cpuset_20261128T001400Z` at `a98d2eff`, clean.
- **Run id:** `tasl2-cpuset-mlgym_houseprice-20261128` (first unused UTC date; the 27 Nov live and sealed roots
  are untouched).
- **Driver:** `sweep2/t1_tasl/run_cpuset_check.sh` from the reviewed tip `b5626bf4` (on `main`).
- **Result:** `verdict = PASS`, `reason = null`, `complete = true`, three attempts sealed.

| Attempt | Complete | Deterministic | Identical to reference | Max wall (s) | Within 9.486 s | Affinity |
|---|---|---|---|---|---|---|
| 1 | yes | yes | yes | 3.810 | yes | 0-7 |
| 2 | yes | yes | yes | 3.858 | yes | 0-7 |
| 3 | yes | yes | yes | 3.848 | yes | 0-7 |

- **Check spec sha256:** `323434a3d597f4a2900816ffff1d32cadbc7f3b6848b4c2bfad00da22334652d`.
- **Canonical record:** `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261128.json` sha256
  `2447e4363976b6d5565f4b49efa079d35989f8cf8a284bb8190f6a43e4665c61`.
- **Harness commit:** `c025f89aeafc2199bf3487b4bcaa16678273c702`.
- **Reference:** sealed `g1b-tasl-20261121-b/mlgym_houseprice/attempt-1`, job record
  `15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa`.
- **Sealed attempts:** `tasl2-cpuset-mlgym_houseprice-20261128/mlgym_houseprice/attempt-{1,2,3}` on TASL-2.
- **Driver span:** `2026-11-28T00:14:01Z` – `2026-11-28T00:15:34Z` (leases released at the end).

The earlier `tasl2-cpuset-mlgym_houseprice-20261126` scene (one superseded attempt) and the 27 Nov STOP scene are
kept unchanged and are not combined with these attempts.

## Files

`G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261128.json`, `cpuset_driver.status`, `cpuset_host_before.txt`,
`cpuset_host_after.txt`, `cpuset_lease_state.txt`, `cpuset_spec.mlgym_houseprice.json`, `cpuset_spec.sha256`,
`cpuset.checkout.head.txt`, `cpuset.checkout.status.txt`, the three `seal_attempt_{1,2,3}.{out,err}`.
`SHA256SUMS` binds them.

Decided alone: used the first unused UTC date as the run id and a fresh capture/checkout pair, as the reviewed
handoff specifies; nothing was resumed or overwritten.
