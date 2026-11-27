# D.3 runner → audit → outcome-table integration (unit record)

**Task:** `compute/20261127-23`. **Base:** `main` `840ad01d`. **Result: PASS for the two
production interfaces and the seven synthetic cases; full suite pending at this commit.**
ENGINEERING_ONLY: synthetic campaigns and synthetic audit metrics only; no real campaign, GPU job,
label, evaluation or sealed read.

The step-(5) repeat review found two production gaps: G1 wrote a summary G7 could not read, and G6
did not audit every kept incumbent. This unit changes **G1 and G6 only**; `d3_outcome_table.py`
(G7) and `d3_analysis.py` are byte-identical to the reviewed source.

## What changed

| File | sha256 | Change |
|---|---|---|
| `r1/c3/d3/summary.py` | `8daf261f3b00bf3556805109ed7abd540dd4a2c8bac399a6c4cd2f86b6e5b837` | New G1 producer of the exact `SUMMARY_KEYS` record G7 reads: stage `D.3a`/`D.3b`, the G2/G8 mechanism counts from the ledger/events, per-trial configuration hashes, start/final hashes, `last_keep_run`, `infra_attempts`, the compute seconds/tokens and the declared `worker_runs`/`llm_calls`. It also produces the per-keep list (charged-run count, configuration sha256 and files). |
| `r1/c3/d3/snapshots.py` | `f15d9deef382c6d5e899eaefa91a2eefbadcc86bff0116ac37391a6f28526a48` | The recorder captures each executed trial's live configuration at E2 (`note_trial_config`/`trial_configs`/`config_by_trial`). No snapshot, controller or budget rule changes. |
| `r1/c3/d3/campaign_chunk.py` | `98c16b6dd4e826572e92dbd10f35fbed2917b399aaafef20dbf1f283e7935bcb` | Both routes write `keeps/keep-<charged-run>.json` and the G7 `summary.json` from the production ledger, events and recorder captures. The chunk-level summary/records are unchanged. |
| `r1/c3/d3/replicate_campaign.py` | `be6464fbc5949fcd80deb0cef57389dfc2a0fe1becbed8dbfb4df02361a905fd` | The replicate loop records every candidate configuration and returns its start/final contents. |
| `r1/c3/d3/audit.py` | `f17d8c15cac5e738cfc2de851c801f008eb55a047701c86540676a6aedfa346f` | G6 reads `keeps/`, audits every kept incumbent on the declared seeds with the shared cache, writes `Y_keep.jsonl`, the per-keep records and a six-key `g7_rows.jsonl`; `g7_rows()` is the G7 projection. |
| `r1/c3/d3/assemble.py` | `7671543bac1b081ac61c5bdaa32433b5dae886c928ea37080596f82d1d96444a` | Assembles the G7 table directly from the production `campaigns/*/summary.json` and `g7_rows.jsonl`; no fixture summary or hand-supplied audit. |
| `r1/tests/test_d3_integration.py` | `46985962304244f95c29402224c71e44dcd69f31dc8c4f8a20df1d70b7e5080c` | The seven step-(5) cases (harness keep/discard/early cap, FIXR3 keep/discard, EGATE keep/discard) through the production G1 summary, G6 audit and G7 `build_row`; then a full 882-row table repeated from the seven production cases, `write_table`, `load_table` and `D3.analyse`. |
| `r1/tests/test_d3_g1_chunk.py` | `3f2ed3d5b037f90a4f4f36a95362113b844e5e5a8a7fcaedaee0ba7309072170` | The chunk test now asserts the G7 summary keys and the `campaign.json` end condition. |

## What G1 now emits (field by field)

`summary.json` has exactly `SUMMARY_KEYS`: `schema`, `stage`, `arm`, `node`, `instance_seed`,
`repetition`, `status`, `gpu_model`, `infra_attempts`, `worker_runs`, `llm_calls`, `unfundable`,
`start_config_hash`, `final_config_hash`, `last_keep_run`, the three `COMPUTE_INT_KEYS`, the four
`COMPUTE_SECONDS_KEYS`, and the six `MECHANISM_KEYS`.

- Mechanism counts come from the ledger/events, as G7's reviewed function defines them. A0 and the
  two replicate arms have no rule layer; a missing E1 rule flag is tolerated **only** for them.
  A1/A2/A0R/LADDER with an event log but no E1 flags is a STOP.
- `config_by_trial` is the recorder's live E2 capture, so a kept configuration is the bytes the
  worker executed, not a recomputed edit chain. The ledger's final decision decides keep/discard
  (a verify may demote a provisional keep).
- `infra_attempts` is 1 (the initial attempt) unless a later unit records retries; G7 requires
  `>= 1`. `proposer_gpu_seconds` is 0.0: the proposer server's card time is not measured per
  campaign in G1. Both are honest placeholders for the fields the current records do not carry;
  they are named here so the reviewer can require a later producer.
- `llm_tokens_*` and `controller_seconds` sum the events' `llm_meta`/`latency_s` when present
  (0 otherwise); `worker_seconds` sums `worker_finished.elapsed_seconds` (or the replicate
  attempts' seconds); `wall_seconds` is measured around the campaign call.

## G6 per-keep audits

For every kept incumbent G1 writes `keeps/keep-<keep_run>.json` with the configuration bytes, its
sha256 and the charged-run count. G6 audits each on the instance's ten declared seeds
(6701–6880), reusing the shared `(node, config_sha256, seed)` cache; it writes the per-keep record,
`Y_keep.jsonl` and the six-key `g7_rows.jsonl`. The last keep's audit is the same cache entry as
the final audit, so G7's last-keep/final equality check holds. A campaign with no keeps writes no
keep rows; G7 then requires `last_keep_run = null` and `final = start`.

## Independent review findings and fixes

The first review (`compute-d3-integration-review-20261127` @ `58e6f571`) was **CHANGES REQUIRED**.
This revision answers it:

- **B1 (w=0 campaigns could not be assembled):** `audit.g7_rows` now omits every audit row when the
  campaign's final `w` is 0; `Y_final.jsonl` keeps the descriptive row. A production zero-run EGATE
  case (80 LLM calls, 0 runs) is now a test and passes `build_row`.
- **B2 (stopped/errored campaigns labelled complete):** the summary status is `complete` only for
  `worker_runs`, `llm_call_cap` and `no_fundable_candidate`; `stop`/`error` are `stopped`. A stopped
  harness case is a test; G7 refuses it.
- **M1 (mechanism counts failed open without events):** an A1/A2/A0R/LADDER record that ran without
  E1 rule flags is now a STOP even when the event log is empty; A0/FIXR3/EGATE have no rule layer
  and are accepted. The chunk fixture now uses A0 (its purpose is record layout). A test pins the
  A2 refusal.
- **M2 (tests bypassed the production disk boundary):** the seven-case test now calls
  `assemble.load_summaries`/`load_audits` and the full 882-row table is written to the production
  `campaigns/*/summary.json` + `g7_rows.jsonl` layout, assembled by `assemble.build`, written,
  reloaded and analysed. Each case asserts its review-table `worker_runs`, `last_keep_run`, `keeps`,
  final `y_raw`/config hash and last-keep equality; a zero-run case and a stopped case are covered.
- **M3 (placeholders):** `infra_attempts=1` and `proposer_gpu_seconds=0.0` remain named placeholders
  for this synthetic integration; they must be populated or explicitly marked unmeasured before a
  real outcome table.

## Tests

With Python 3.12.8, pytest 9.2.0, harness `9bb41680`:

```
AR_HARNESS_ROOT=<harness9bb> python -m pytest -q \
  r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py \
  r1/tests/test_d3_g1_replicate.py r1/tests/test_d3_adapter.py \
  r1/tests/test_d3_audit_g6.py r1/tests/test_d3_integration.py \
  r1/tests/test_d3_outcome_table.py r1/tests/test_d3_analysis.py
156 passed, 18 subtests passed (three integration tests after the fix).
```

The seven-case test calls `table.build_row` on each production summary and G6 audit. The full-table
test repeats the seven production cases across the declared design (only to satisfy G7's exact
coverage check), writes and reloads the table, and runs `D3.analyse`; both pass. The full
`r1/tests` suite is running at this commit; the base comparison and a fresh tier-E review follow.

## What this unit does not do

- It does not change G7, the pinned analysis, the pre-declaration or any signed value. If the
  reviewer finds G7 must change, that is a separate STOP (the task says so).
- It does not run a real campaign, audit, GPU job or sealed read. The integration test's worker,
  manager and audit metrics are synthetic.
- It does not decide whether `infra_attempts=1` / `proposer_gpu_seconds=0` are sufficient for the
  final outcome table; they are the current records' honest values and are named for review.

## Decided alone

To capture the executed configuration at E2 rather than recompute an edit chain; to build keeps
from the ledger's final decisions (so a verify demotion is respected) while using the E2 capture
for the bytes; to keep G7/analysis untouched and put the table assembly in a new G1-side module; to
repeat the seven production cases across the full design in the regression test only for G7's
coverage check, while the seven case checks themselves use production records directly.
