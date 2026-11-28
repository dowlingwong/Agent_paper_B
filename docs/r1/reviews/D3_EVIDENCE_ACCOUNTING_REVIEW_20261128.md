# D.3 P5 evidence accounting — independent tier-E review

Task `local/20261128-07`. A fresh Codex reviewer who did not write or modify the unit reviewed both rounds against published base `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907`. Local transcribed the review findings and checks below.

## Round 1 · NOT ACCEPTED

Reviewed code `cacede8e8d263ee4b41f9080798a15cbb4a4d9a2`. The reviewer reproduced a per-UUID SSH lease silently selecting GPU 0 on a multi-card host. An unrelated loss row with a syntactically valid digest also counted as a retry without proof of the receipt's bytes or chunk identity. The initial synthetic suite passed 92 tests. These checks did not meet the production acceptance bar.

## Round 2 · ACCEPTED

Reviewed code `befe3fef62dfcf61d7f3594ae51b22f0eb694762`. The reviewer confirmed both blockers were resolved. Indexed and UUID-named SSH leases select the exact card and refuse a mismatching observed UUID. HTCondor uses the single resolved CUDA assignment. Both launchers stage the loss receipt's exact UTF-8 bytes. The submit and job-side checks bind the digest and run, chunk, attempt and job identities.

The reviewer executed the rendered SSH script in a scratch-only CPU smoke with fake `nvidia-smi`, an `fcntl`-backed mock `flock` and a scope executable that closed its inherited descriptor. The UUID lease probed correctly. A competing open descriptor could not obtain the lock while the scope ran and could obtain it after scope exit. The harness and replicate paths time the retained campaign body, preserve run and call accounting, and include the provenance in the chunk seal.

The diff check passed. The nine changed paths cover D.3 production modules and focused tests. The diff leaves the signed declaration and pinned analysis files intact. With a fresh `TMPDIR` and clean harness `9bb416805175149eb87b71f28d77530572aa4bce`, this command returned **97 passed in 3.35 s**.

```sh
python -B -m pytest -q -p no:cacheprovider -rfE \
    r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py \
    r1/tests/test_d3_integration.py r1/tests/test_d3_smoke_engineering.py \
    r1/tests/test_d3_outcome_table.py
```

The operator validates the disposition and digest of the original sealed job record and reconciles active job IDs before dispatch. Before evidence, Compute supplies a reviewed per-launch check that the pinned manifest endpoint serves the proposer on the exact metered GPU. Desk review used synthetic inputs and no live job, credential, or sealed partition. Local records the separate serial full-suite comparison in its handoff.
