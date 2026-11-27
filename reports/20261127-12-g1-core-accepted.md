# Report — D.3 G1 snapshot core corrected and `ACCEPTED` (task `compute/20261127-09` item 1)

**Result: PASS.** The independent tier-E review of the corrected snapshot core is **`Verdict: ACCEPTED`**; the
four coordinator conditions pass and the full suite shows zero new failing ids. The earlier review's B1–B5/M1–M4
are fixed on the same branch by new commits (no force push).

- **Branch:** `compute-d3-g1-snapshot-20261127` @ `44075323`
- **Reviewed tip:** `44075323` (first review `51cf07f7`; corrections `f1b1ad20`, `44075323`)
- **Unit record:** `docs/r1/reports/d3_g1_20261127/D3_G1_UNIT_20261127.md` sha256
  `e6d69524206d347fe929f671fdac7aebf27f650cb672813982114b6c722e3d46`
- **Code hashes:** `r1/c3/d3/snapshots.py` `8fffeca7…`; `r1/c3/d3/campaign_chunk.py` `653804b8…`
- **Reviews:** `D3_G1_SNAPSHOT_CORE_REVIEW_20261127.md` (R1, CHANGES REQUIRED),
  `..._R2_20261127.md` (R2, CHANGES REQUIRED: model-source fail-open),
  `..._R3_20261127.md` (R3, **`Verdict: ACCEPTED`**, sha256
  `d1eb76708727d12e35a78df345407412d7340cdb5bc9670a15dd263b3af7553b`) on
  `compute-d3-g1-core-review-20261127` @ `381262de`.

## Corrections

1. **Parity at every hook (B1):** `observe_budget` checks `ComputeBudget.worker_runs` at E0/E1/E2 as well as at
   each charge; a mismatch raises `SnapshotParityStop`. The end check remains.
2. **E1 state is authoritative (B2):** the E2 hook no longer replaces `_trial`; verify snapshots keep the E1
   controller state with `pending_action=verify`; `note_run` asserts +1 controller call for a main run and +2 for
   a verify run, so an extra revise/re-screen fails closed.
3. **Deterministic projection (B3):** no `repr` fallback; an unsupported object is a `SnapshotStop`; a controller
   must provide a JSON-able `snapshot_state()`.
4. **Hardware wiring (B4):** `run_chunk` requires the observed hardware record and calls `check_hardware` before
   creating output; missing model/proposer/memory check/lease/`instance_model` is a refusal, and the
   `campaign_model_source_sha256` key is now required (R2 N1).
5. **Chunk layout (B5):** each campaign writes `ledger.jsonl`, `runs.jsonl`, `summary.json`, `campaign_id` and
   `record_name`; `chunk.json` carries the named hardware/proposer/request/scope/environment/status fields.
6. **Final alias (M1):** `final.json` at w=20 copies `w20.json` and adds the final fields; the controller state and
   incumbent are equal to the w20 record, not recomputed from E2.
7. **Smaller items:** `note_decision` no longer accepts an ignored `llm_calls`; `campaign_id` is asserted; chunk
   `status` is `stopped` on stop/error.

## Tests

- Unit modules: **20 passed** (13 snapshot + 7 chunk) at the pin `a3fedbbd`, Python 3.12.8, pytest 9.2.0.
- Full suite, same environment: base `6684e840` **100 failed, 4328 passed, 161 skipped, 3 errors**; tip
  `44075323` **100 failed, 4348 passed, 161 skipped, 3 errors**. The 103 FAILED/ERROR ids are identical, sha256
  `e6f2073eb1adeafb5438af19d88bb9e8ad97666a009d029961b6c5ccbad70880`; **+20 passed, zero new failures**.
- A separate same-machine run with a different dependency environment gave 46/4401; its two extra ids fail on
  base too. It is not used for the raw-count comparison.

## Remaining MINOR (non-blocking, recorded by R3)

The unit record still says 19 tests (actual 20); the `campaign_id` refusal happens after `out.mkdir` and can leave
an empty scaffold; `host_class`/`lease_path`/`chunk_start_utc` can be null if the observed record omits them; a
chunk with `status=stopped` still runs its remaining instances (full-runner STOP behaviour is future work).

## What happens next

The coordinator can merge the corrected G1 core. The next G1 unit is the revision 6c replicate driver (FIXR3/EGATE)
with the additive recorder API and the replicate chunk branch; the harness verify-seed unit is `local/20261127-07`.

**No force push:** all corrections are new commits on the branch.
