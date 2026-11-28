# compute/20261128-09 — G.5 P11: run the engineering smoke matrix (supersedes `compute/20261128-05` item 1)

The reviewed P11 engineering smoke path is on `main` `cb20c9fd` (local branch `local-20261128-02-p11-smoke` @ `b9e195ac`, review ACCEPTED). Run the matrix on
TASL-2 and TASL-7 with the exact per-item commands in the local handoff (`coord/local` `a6bbd33e`, `reports/20261128-02-p11-engineering-smoke.md`,
"Compute handoff after coordinator publication"): C2, C4, C5, C9, C10 short span (a restart is an infrastructure STOP), the C11 chunk side, C14, pre-run
C15, C16 and the G.5 seal path. ENGINEERING_ONLY under `~/r1_engineering/g5-p11`; nothing enters a release. Check the leases first: the TASL-7 card is also
wanted by the E0 repeat (`compute/20261128-08`), which goes first on that card. Then an item-by-item host record (PASS/STOP per item with captures and
hashes) on a branch with a fresh review; the coordinator records P11 under R1-G5-P11 only from that reviewed record.
