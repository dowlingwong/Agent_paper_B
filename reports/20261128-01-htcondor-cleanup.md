# compute/20261128-04 — HTCondor stale requests removed

**Result: 759624 and 759625 removed after the Idle/owner/command check; 760065 confirmed already gone and recorded
as withdrawn. No other job touched.**

- Task: `compute/20261128-04` (author's decision, 28 Nov).
- Branch: `compute-htcondor-cleanup-20261128` @ `459d10c03bad77c6057c95011f7d8cc2a3c3c3ad` (base `origin/main`
  `a98d2eff`), documentation only.
- Submit host: deepthought.

| Job | Pre-check | Action | Post-check |
|---|---|---|---|
| 759624 | Owner `dwong`, JobStatus 1 (Idle), Cmd `.../probes/probe.sh` | `condor_rm` | gone; history captured |
| 759625 | same | `condor_rm` | gone; history captured |
| 760065 | not in queue | none | history: JobStatus 3 (Removed), `via condor_rm (by user dwong)` |

Captures and `SHA256SUMS` in `docs/r1/reports/htcondor_cleanup_20261128/`; record
`HTCONDOR_CLEANUP_20261128.md` sha256 `0cd972ce877d37190b1d051428a9ec8d48217030f514d691768f33605c83f74f`.

No review required beyond the coordinator's check (documentation only, per the card).

Next: nothing waits on this cleanup; the D.3 preflight re-check is separate (`compute/20261128-03`, no startable
slot).
