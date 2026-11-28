# compute/20261127-33 item 1 — G.5 houseprice TASL-2 CPU-set check PASS

**Result: PASS.** Three complete, deterministic, sealed attempts; each bit-identical to the declared TASL-2 G.1b
reference; max wall 3.810 / 3.858 / 3.848 s against the 9.486 s budget; affinity CPUs 0-7. Fresh review
**ACCEPTED** after one finding (missing ignored `*.out` capture) was fixed.

- Task: `compute/20261127-33` item 1 with disposition `compute/20261128-05` item 2; rule R1-TASL2-CPU.
- Base `origin/main` `a98d2eff1d2847e34f00effe66b53bc00467e936`.
- Deliverable branch: `compute-houseprice-cpuset-20261128` @ `e1a16d59e298d1fb869f535d04dee60627046fda`
  (record commit `e62a9fc0`, capture fix `e1a16d59`).
- Review branch: `compute-houseprice-cpuset-20261128-review` @
  `280d846ed4afed85e6abba878087234746b8f7b5`; `Verdict: ACCEPTED` in
  `docs/r1/reviews/HOUSEPRICE_CPUSET_CHECK_REVIEW_20261128_RECHECK.md`, sha256
  `ac6eac6d83d6d514800fc1bf338e260dbf3ff20746ec04101933fc638c4b2c84` (first review
  `3a66f6a4…` was CHANGES REQUIRED on the ignored `.out` files; fixed without amend).
- Run: `tasl2-cpuset-mlgym_houseprice-20261128`, 2026-11-28T00:14:01Z–00:15:34Z, TASL-2, checkout at `a98d2eff`,
  driver at `b5626bf4` (on `main`).
- Canonical record: `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261128.json` sha256
  `2447e4363976b6d5565f4b49efa079d35989f8cf8a284bb8190f6a43e4665c61`; check spec sha256
  `323434a3d597f4a2900816ffff1d32cadbc7f3b6848b4c2bfad00da22334652d`; `verdict = PASS`, `reason = null`,
  `complete = true`.
- Record memo: `docs/r1/reports/g5_cpuset_20261128/G5_TASL2_CPUSET_CHECK_20261128.md`; 20 files tracked,
  `SHA256SUMS` verifies 19/19 listed in a clean checkout.
- The 26/27 Nov STOP scenes are untouched; nothing resumed or overwritten.

Decided alone: first unused UTC date as the run id and a fresh capture/checkout pair, as the reviewed handoff
specifies. Next: the coordinator publishes the accepted record; houseprice remains gated pending that publication
and the G.5 note.
