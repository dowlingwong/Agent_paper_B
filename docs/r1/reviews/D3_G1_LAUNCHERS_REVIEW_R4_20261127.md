Verdict: ACCEPTED

# D.3 G1 launchers — R4 delta confirmation (`08301947`)

**Delta re-check, 27 November 2026.** This confirms the two commits after the accepted R3 tip
`3cfaa6fe88e315b5be6a0f234a8a5d2c261ecb92`: `f4cbda4b` (remove the low-level `probe()` 46,000 default, refresh
the unit record) and `08301947` (refresh the probe hash). I wrote R1/R2/R3; all remain in history
(`da23bd5e`, `ceea2f7f`, `0b4f7490`). The full diff `3cfaa6fe..08301947` changes **one line of code**
(`r1/c3/d3/probe.py:63`, `required_memory_mib: int = 46000` → `required_memory_mib: int`), the unit report's
probe hash and full-suite line, and adds the R3 review file; the launcher, chunk, request, end-sampler,
snapshot, lease and host-check code is unchanged. The signature change is safe: `probe_from_records` already
passes `required_memory_mib=required` and is the only production caller; the only other caller is the focused
test, which passes `20000`; an omitted value now raises `TypeError: probe() missing 1 required keyword-only
argument: 'required_memory_mib'` instead of silently using 46,000. The probe's `gpu_index` default remains 0,
but `probe_from_records` derives the lease index and passes it, so no card-selection path regressed.

**Commands and counts.** Focused suite, tip `08301947`, cwd the review worktree:

```
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb \
  /private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python \
  -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py
```

Result: **47 passed in 3.05s**. I did not re-run the full suite: the delta changes only the `probe()` default
(called from `probe_from_records` and the focused test) and documentation; the R3 full run at `3cfaa6fe` remains
**114 failed / 5003 passed / 163 skipped / 3 errors / 71 subtests**, 117 ids, identical to base `2d88fe1b`. The
unit report's full-suite line now cites 5,003 at the R3 tip.

**Hashes.** Tip `08301947baec57d5686613b5248daaf8279fbfa0`; base `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`;
`r1/c3/d3/probe.py` `584d4c63a875bc51c169cd2b97e0fcde7b16412582b6d556832d1010ccdadd62` (matches the refreshed unit
report); `r1/tests/test_d3_launchers.py` `3db7585a4087bb9623f93b98d51bbb83724f3607f71ede828a4545bae78a4177`.
R3 minors are unchanged and none is blocking: a per-UUID lease (`GPU-abc.lock`) still falls back to index 0, an
SSH alias/FQDN host difference is refused by the exact comparison, the probe-refusal/SSH-script/HTCondor-lease
tests are still not explicit, and the report's "Focused new tests: 14 passed; 44 focus" line is still stale (the
run is 17/47). The ACCEPTED verdict stands; no blocking or major findings remain.
