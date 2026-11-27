# D.3 G1 final snapshots — the terminal keep on both runner routes (compute/20261127-20)

**Task:** `compute/20261127-20`; base `origin/main` `c4250f7ea26a97e0f3c7b475613287864110a14c`. The two blocking
findings of the revision-4 step-(5) review (`docs/r1/reviews/D3_PREDECL_R4_STEP5_REVIEW_20261127.md`, full step
**NOT ACCEPTED**) are fixed in `r1/c3/d3/snapshots.py` and `r1/c3/d3/campaign_chunk.py`; no G6, G7 or analysis file
changed. ENGINEERING code and synthetic tests only; no campaign, audit, label or evaluation value was read.

## Result

`final.json` now comes from the post-decision incumbent on both routes, and the at-W record is canonicalised to the
final when the campaign reaches W. A keep on the last trial reaches `final.json`; the pre-decision record is kept as a
distinct `w<W>_pre.json` for replay (its payload is unchanged apart from the two provenance fields
`pre_decision` and `superseded_by`). The two reproductions in
`docs/r1/reports/d3_predecl_r4_step5_20261127/REPRODUCTIONS.md` fail on the base and pass on the tip:
the harness reproduction's recorded and live hashes now agree at both endings, and the replicate `w20` and `final`
carry the same configuration.

## What changed

### Harness route (`campaign_chunk.py`)

`run_real_campaign` is followed by `SnapshotRecorder.write_final_live(...)`, not the old `write_final`:

- it reads the **live** editable files after the campaign (`read_worker_config(worker, node_spec)`) — the harness has
  applied the last keep and restored a discard, so this is the terminal incumbent;
- the ledger supplies the last kept trial index (the last `keep`/`kept` `budget_index`), the final trial id and the
  LLM-call count;
- the controller state is the one after the last E1/E2 decision (`RecordingController` hands the inner controller to
  the recorder after `decide`); the exact-w snapshots keep the E1 state, as coordinator condition 3 requires.

### Replicate route (`replicate_campaign.py` via `write_final_from_state`)

The engine's post-decision `incumbent_config` was already correct. `_write_final_payload` now canonicalises the at-W
record: the pre-decision `w20.json` is preserved as `w20_pre.json` (with `pre_decision: true` and
`superseded_by: final.json`) and `w20.json` is rewritten from the post-decision final (`canonical_final: final.json`).
The campaign records carry `pre_decision_snapshots` beside `snapshots`; G6 ignores the `_pre` file by name and its
existing alias rule audits one canonical Y(W). No G6/G7/analysis code changed, so their pinned hashes stand.

### The four conditions of `compute/20261127-04`

1. The counting wrapper's count still equals `ComputeBudget.worker_runs` at every hook and at the end; `write_final_live`
   checks `w_final == recorder.count` and the chunk still checks the final budget parity.
2. Only budget-charged runs are counted; the counting worker is unchanged.
3. Exact-w snapshots keep the last E1 controller state; the final is a post-decision record (as the replicate route
   already was), not an exact-w snapshot. No controller call is introduced between an E1 hook and a run.
4. The independent review (below) confirms this reading.

## Reproductions

Base `c4250f7e`, harness `9bb41680`, the reproduction script from `REPRODUCTIONS.md` (synthetic worker, scripted
manager, improving metrics):

| End | ledger last keep | final keep (base) | hashes (base) | tip |
|---|---:|---:|---|---|
| worker-run cap W=20 | 20 | 19 | live `4b1b4f8d…`, recorded `a12ae00c…` | live = recorded `4b1b4f8d…`, final keep 20 |
| LLM-call cap at 7 | 7 | 6 | live `a12ae00c…`, recorded `4b1b4f8d…` | live = recorded `a12ae00c…`, final keep 7 |

On the tip the same script with `write_final_live` prints `match: true` for both endings; at W the canonical
`w20.json` has the final config and `w20_pre.json` keeps the pre-decision one. The new tests
`test_final_is_the_live_last_keep_at_w_and_an_early_cap` and the updated
`test_replicate_final_is_separate_from_w20_and_carries_the_last_keep` exercise both.

## Tests

- Focused D.3 modules (`test_d3_g1_snapshots`, `test_d3_g1_chunk`, `test_d3_g1_replicate`, `test_d3_adapter`,
  `test_d3_audit_g6`, `test_d3_outcome_table`, `test_d3_analysis`, `test_d3_verify_namespaces`): **161 passed, 18
  subtests**, harness `9bb41680`.
- Full `r1/tests` at harness `9bb41680`, serial runs with the same environment (Python 3.12.8, pytest 9.2.0, no
  LightGBM; the known environment failures are unchanged):

| Checkout | Passed | Failed | Errors | Skipped | Subtests |
|---|---:|---:|---:|---:|---:|
| Base `c4250f7e` | 4,980 | 117 | 3 | 163 | 71 |
| Tip | 4,982 | 117 | 3 | 163 | 71 |

  Zero new failures. The tip's 120 `FAILED`/`ERROR` ids are the **same set** as the base's 120
  (`FULL_SUITE_FAILURE_IDS_FINAL_20261127.txt`, file sha256
  `811be7a90113d4c76025d0a6246da51ec1a958fd3c753b750011114584a073a3`, newline-joined sorted id-list sha256
  `03339eb10919c3772e705195d5dc37cdee44a38d76ebaa5be1acd10f74d02977`; the adapter unit's older 111-id list is
  untouched). The independent reviewer's rerun saw 114 failed / 4,985 passed and 117 ids, a strict subset of the
  base's 120: three base failures (`test_b1_real_worker_run_is_seed_deterministic`,
  `test_real_worker_run_is_seed_deterministic`, `test_dryrun_start_refuses_external_batch_before_log_write`) passed
  for it and pass individually here; they are environment-flaky, and no new id appears in either run. The two extra
  passes over the base are the new tests. At `ended_on="error"` the at-W record is not canonicalised (fail-closed;
  G7 would refuse a differing W/error row).
- `git diff --check` clean.

## Files

| File | sha256 |
|---|---|
| `r1/c3/d3/snapshots.py` | `5241dcc079f606582a8e9233886a51d93b656aef3362571b4898c9ab748819a2` |
| `r1/c3/d3/campaign_chunk.py` | `4131ffcc6946e5fd156ea159e44c466fed8b6de8d3a2e0b88731898976f96f1c` |
| `r1/tests/test_d3_g1_snapshots.py` | `c57926a438811e9042af0d2adbed4bcebc11c2d5e270b3d1d2e0d851a1c41ef5` |

## Review

A fresh tier-E review of this branch is required before the local worker repeats step (5); its verdict and any
findings are reported separately on `coord/compute`. No D.3 evidence job starts before the pre-declaration is frozen.
