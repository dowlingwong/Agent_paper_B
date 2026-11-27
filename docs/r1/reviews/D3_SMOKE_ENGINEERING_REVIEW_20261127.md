# Review — D.3 per-arm ENGINEERING smoke (`compute/20261127-27`)

**Reviewer:** a fresh independent agent (general subagent) that did not write the unit. The reviewer only read code and
records; it ran no campaign, GPU job, label or evaluation read, and changed no file.

**Unit under review:** `compute-d3-smoke-20261127` @ `66f13e1c` (driver
`r1/scripts/d3_smoke_engineering.py`; smoke audit block in `r1/c3/d3/audit.py`; tests
`r1/tests/test_d3_smoke_engineering.py` and `r1/tests/test_d3_audit_g6.py`).

**Verdict: ACCEPTED.**

## Review rounds

1. **First review — CHANGES REQUIRED.** The reviewer found: B1 the G7 row builder cannot accept the reserved smoke
   seed because `d3_analysis.audit_seeds` accepts only 6201-6218; B2 the synthetic full-design expansion carried the
   wrong `audit_seeds`; B3 the driver accepted deployment seeds/nodes, leaving a route to outcome-eligible records;
   B4 the signed pre-declaration fixes the smoke to `openml_climate` and says it is never audited for Y, while the
   task card asks for a G6 audit; M1-M7 covered the launcher, exercise table, harness pin, tests, audit retry,
   worker identity and unregistered smoke audit block.
2. **Second review — CHANGES REQUIRED.** The table step was corrected to refuse rather than fabricate; the seed and
   node guards, the direct launcher record, the harness check, the audit-root refusal, the worker probe and the
   disjointness test were added. The remaining blocker was that `smoke.json` and `campaign.json` were trusted without
   validating the record hash or the reserved seed. M1-M4: stale record route, default node, failure identity and
   sigma derivation.
3. **Third review — CHANGES REQUIRED.** The self-hash was not actually written (`_write_json` wrote before the key
   was added), so validation refused every real record. The four majors were otherwise accepted.
4. **Final confirmation — ACCEPTED.** `_write_record` hashes the body and writes `{**body, "record_sha256": digest}`
   atomically; `smoke.json`, `audit.json` and `table.json` use it; `_verify_record` validates the persisted hash; the
   self-hash test passes. No blocking item remained.

## Accepted properties

- The driver uses the production G1 core (`run_chunk`, `make_campaign_factory`, `make_replicate_factory`,
  `SnapshotRecorder`) and the production G6 audit (`audit_chunk`, `harness_runner`, `Cache`); it duplicates no
  campaign logic.
- It refuses seeds other than the reserved smoke seeds 6301/6302, nodes outside the engineering set, and A3/A5/A6.
- The signed values are unchanged: W = 20, LLM-call cap = 80, harness `9bb416805175149eb87b71f28d77530572aa4bce`,
  `verify_seed_base = 20000`, one GPU model for the instance.
- The smoke audit block 6391-6410 is separate from every deployment block; the tests assert disjointness.
- `table_check` never writes an `r1_d3_outcome/v2` table. It reports the pinned analysis's refusal of the smoke seed
  as **REFUSED** and records the failing arm/campaign. This is the correct STOP under the signed pre-declaration.
- `audit_smoke` validates the record self-hash and every campaign's reserved seed before auditing, refuses an
  existing audit root, and derives `sigma_node` from the record (or the pinned constants) rather than trusting the
  caller.

## Residual, non-blocking

- The engineering smoke runs on `digits_mlp` (the TASL-2 host has no `openml_climate` data cache); the signed design
  node is `openml_climate`. The deviation is recorded in `smoke.json` and the delivery report.
- The task card's G7/analysis acceptance cannot be met without changing the hash-pinned `d3_analysis.py`; the
  delivery reports a STOP for that sub-item and asks the coordinator for a signed amendment or a re-scope.
- The G6 audit is an engineering check only; its Y rows are not evidence and never enter an outcome table.
- `audit_smoke` has no resume path: a partial audit leaves `audits/` behind and a rerun refuses it (manual recovery in
  a new run root).
