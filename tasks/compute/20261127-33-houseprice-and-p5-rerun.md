# compute/20261127-33 — reruns: houseprice CPU-set check and Ada P5 (both fixes on main)

Both units are on `main` `1f1b5d41`.
1. **houseprice CPU-set check:** the driver fix (`mac-houseprice-cpuset-count-20261127`, review ACCEPTED). Run the exact command in the local
   report `reports/20261127-27-houseprice-cpuset-rerun.md` (or the one named in `63cd96e1`) on TASL-2 from a clean checkout of `origin/main`, with a
   new capture directory; keep the STOP scene. On PASS, commit the single `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_<date>.json` record on a branch.
2. **Ada P5 (`compute/20261127-29`):** the per-card Track P lease (`mac-trackp-per-card-lease-20261127`, re-check ACCEPTED). Follow the local
   report `reports/20261127-28-trackp-per-card-lease.md` "Compute handoff": the staged Track P smoke with `--gpu "$CARD_UUID"` on an empty Ada card,
   then E0, fresh capture directories, and a fresh review of the records.
Order: the screening run first (running); then these two; then the P11 TASL-2 items.
