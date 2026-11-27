# Report — D.3 G1 charged-run snapshot core; two pre-code blockers (task `compute/20261127-04`)

**Task:** `compute/20261127-04` with `cluster/20261126-02`. **Result: G1 snapshot core DELIVERED; the full G1 runner
is not complete.** Two pre-code blockers need a decision before the adapter can be written.

- **Branch:** `compute-d3-g1-snapshot-20261127`
- **Tip:** `51cf07f76c261fa34a0fb3f1d8f623fb978a6030`
- **Base:** `origin/main` `6684e840`
- **Unit record:** `docs/r1/reports/d3_g1_20261127/D3_G1_UNIT_20261127.md`
- **Tests:** `r1/tests/test_d3_g1_snapshots.py` + `test_d3_g1_chunk.py`: **16 passed** (Python 3.12.8, pytest 9.2.0,
  harness pin `a3fedbbd`). Full `r1/tests`, same environment: base `6684e840` **102 failed / 4326 passed / 161
  skipped / 3 errors**; tip `51cf07f7` **102 failed / 4342 passed / 161 skipped / 3 errors**. The sorted failing-id
  lists are byte-identical (sha256 `7ac566ac…`); the only difference is the 16 new tests. **Zero new failures.**
  The tip was amended once before review to add this comparison (earlier tip `121ba63d`; no `main` push).

## What it does

The coordinator's option 1 replaced the missing per-run harness callback with a G1 worker wrapper. The unit implements
`ParityBudget` (observes every immutable `ComputeBudget` charge and checks the charged-run parity at the charge),
`CountingWorker` (one count per `run_trial`/`run_trial_at_seed`, including a call that raises), `RecordingController`
(action and controller LLM calls) and `SnapshotRecorder` (E0/E1/E2 hook, exact `w`, `final.json`, atomic writes, no
overwrite). `campaign_chunk.py` adds the launcher-neutral chunk layout, launch validation, the revision-6b
hardware/proposer/lease/memory refusals and `SHA256SUMS`.

Covered by tests: a verify block reaches `w=5` through the four seeded runs; `w=10/15/20` main; `final.json` alias at
`w=20`; a skip charges no run; a block charge fails closed at the charge; `w=0` final uses the start configuration.

## Pre-code blockers (they stop the full G1 runner)

1. **Verify seeds collide with the D21 noise-floor block.** The pinned harness hardcodes verify seeds
   `1000 + 10*budget_index + index` (`campaign.py:721`): budget indices 1–3 use 1010–1031, intersecting the D21
   namespace 1001–1030. The D.3 pre-declaration §4.2 declares those namespaces disjoint. Every verify arm (A1, A2, A3,
   A5, A6) fails the design's P10 verify-seed check at this pin. A new reviewed harness pin or a decision is needed; no
   workaround was coded.
2. **FIXR3 and EGATE are not harness controllers.** `r1/c3/d3_replicate.py` gives them
   `step(config_sha256, run, counter)`, not `decide(view, mask)`; their replicate seeds 6501–6679 are outside the
   harness E1/E2 actions. Running them needs a new harness action or a G1-specific loop outside `run_real_campaign`.
   This is a design change; none was coded.
3. **The A1/A2/LADDER constants file does not exist** (pre-declaration §5.0, `constants_file_sha256: <pending>`; the
   LADDER η search is not in `arms_constants.py`). The real adapter waits for G2 and the signed revision 4.

**Decided alone:** to implement the counting/parity core first and stop before the adapter rather than choose a
verify-seed rule or a FIXR3/EGATE integration the design does not settle; to hash a documented controller projection
because the harness has no controller state serialisation; to keep `llm_calls` exact through the observed budget.

**Needs:** a decision on blockers 1–2; G2 constants and the signed revision 4; a tier-E review of this unit.
