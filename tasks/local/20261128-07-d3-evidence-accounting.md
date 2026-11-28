# local/20261128-07 — D.3a P5: evidence accounting producer (proposer GPU seconds, infra attempts)

From the readiness inventory (`main` `dbce0316`, `docs/r1/reports/D3A_READINESS_20261128.md`, P5): `r1/c3/d3/summary.py` still writes
`proposer_gpu_seconds=0.0` and both `campaign_chunk.py` routes omit `infra_attempts` (default 1), the dependency the step-(5) review left open. Build a
reviewed producer that records the actual per-campaign values as the signed accounting already declares them (no change to the declared accounting;
a change would be the author's): proposer GPU seconds from the lease/telemetry, infra attempts from the retry ledger. Targeted tests, a retry/telemetry
check, full suite base vs tip, tier-E review. Also list the exact Code-Commit/review set for P5. Priority: first in your queue.
