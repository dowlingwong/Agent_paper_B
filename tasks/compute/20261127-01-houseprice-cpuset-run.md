# compute/20261127-01 — houseprice TASL-2 CPU-set check: run it (the later task file experiment/20261126-03 waits for)

Owner: compute. Runbook §2 order 2B; PLAN R1-TASL2-CPU, R1-G5-SIGNATURE (1) S14 A. **Ready now**, after item 1 of your queue
(the expansion launch).

The fix is on `main` `47df6f55` (merge of `mac-cpuset-repeats-20261126` @ `5f1aead0`; review accepted; full suite with zero new
failures). The procedure is in the local worker's report `reports/20261126-01-cpuset-fix.md` on `coord/local` @ `6df43013`,
"What happens next" item 2. On TASL-2, from a clean detached checkout of `origin/main` (must contain `47df6f55`), with a new
capture directory outside the checkout:

    bash sweep2/t1_tasl/run_cpuset_check.sh "$CAP"; echo "rc=$?"

The driver takes `gpu0.lock`, `cpus-0-3.lock` and `cpus-4-7.lock` by `flock -n`. **While MetaMaze (0-3) and Forest Cover (4-7) of
the expansion G.1b run, it will wait and then give up after 1 h.** That is expected and not a STOP. Run it when those two leases
are free, or let it wait. The old sealed attempt 1 of `tasl2-cpuset-mlgym_houseprice-20261126` stays untouched (superseded). A
verdict other than PASS is a STOP: keep the scene and report it.

On PASS: commit `docs/r1/reports/tasl_chain_20261122/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_<YYYYMMDD>.json`, with captures under
a `*_captures/` folder, on a branch. Report the tip and the record's sha256. Exactly one such `.json` may reach `main`.
