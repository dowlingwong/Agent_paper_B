# U4 census addendum — autoresearch condition-7 clean smoke still blocked (21 Nov 2026)

**Status: addendum to the accepted U4 census; no measured row changes.** The accepted census
(`TRACKG_U4_CENSUS_20261120.md`, R5 ACCEPTED) records the 20 Nov autoresearch smoke STOP from an external
co-tenant CUDA OOM. A bounded infrastructure retry session was then run (`ar_cond7a_retry_20261120T232847Z/`,
3 h window, max 2 fresh attempts, card requirement 0 compute apps + >=40 GiB free, Paper A gate re-checked;
result `R1_TRACKG_AR_COND7A_RETRY_RESULT_20261121.md`, SHA256SUMS `f9d5a7c4…`):

- attempt 1: card 5 idle at 23:40:00Z, launch 23:40:04Z; zihaozhao apps appeared within ~2 min; aborted
  23:41:50Z before any run record (0 records; cgroup killed);
- attempt 2: card 4 idle at 00:06:24Z, launch 00:06:28Z; hefeifeijiang app appeared; aborted 00:08:14Z before
  any run record (0 records);
- session `STOP_EXTERNAL_CONTENTION` at 00:08:25Z; both attempts were launch-verified idle but no card stayed
  clean, and no shared-card launch was made. **No CHECKLIST_E_PASSED, no B2, no measured slowdown.** All
  evidence preserved (1,723 files, 41 M); no deletion/push.

No U4 measured row or accepted number changes: autoresearch remains **blocked** and is not a U4 row. A clean
autoresearch cond7a smoke still needs an Ada card guaranteed idle for the whole ~30–60 min smoke (reservation
or quiet window), or a revised policy explicitly permitting a mid-run co-tenant with a contaminated
upper-bound slowdown. Two fresh attempts have now been consumed; another attempt needs fresh coordinator
authorization. G.1b/G.4 remain unblocked for the six earlier nodes and HousePrice per R1-TRACKG-G3-EARLY; the
autoresearch row joins only after a clean smoke + U2 review.
