Verdict: ACCEPTED

# D.3 runner → audit → outcome-table integration — independent tier-E review R2

**Task:** `compute/20261127-23`. **Reviewed tip:** `d8cfd7d0a715ba52a93d6cbf8578666b7e05399b`
(the fix commit for B1/B2/M1/M2); **base:** `origin/main` `840ad01d`. **Harness:**
`9bb416805175149eb87b71f28d77530572aa4bce`. **R1 record (kept):**
`docs/r1/reviews/D3_INTEGRATION_REVIEW_20261127.md`.

**Independence.** I am the same fresh, independent tier-E reviewer as R1. I did not write this
unit and did not modify the task branch. This record is committed on
`compute-d3-integration-review-20261127`; no G7, analysis, declaration or signed value was changed.
All campaigns and audit metrics below are synthetic; no real campaign, GPU job, label, evaluation or
sealed read occurred.

**Branch note.** In this worktree the reviewed tree `d8cfd7d0` is a commit whose parent is the R1
record `58e6f571`; the local ref `compute-d3-integration-20261127` still points at `1bd7f3d6`. The
code/test diff against `1bd7f3d6` is the fix commit and no G7/analysis change. I reviewed the tree
at `d8cfd7d0` and did not move or modify the task-branch ref.

The R1 blocking findings are closed for the integration: a zero-run campaign now produces no
`final`/`w`/`keep` G7 rows and `build_row` accepts it; `stop`/`error` summaries are `stopped` and
G7 refuses them; rule-logging arms without E1 events are a STOP while A0/FIXR3/EGATE are accepted;
G7 and the pinned analysis are byte-identical to the reviewed source. The seven cases and the
882-row table pass, and the full suite has **no new failure id** against the base list. The
remaining items are minor test/assembler hardening, not blockers.

## Findings

| ID | Severity | Status |
|---|---|---|
| B1 | **Closed** | `g7_rows` omits `final` when the audited final has `w == 0`; the zero-run probe produces zero G7 rows and `build_row` accepts. Residual empty-audit-directory edge is m2 below. |
| B2 | **Closed** | `COMPLETE_ENDED_ON` makes only `worker_runs`, `llm_call_cap` and `no_fundable_candidate` complete; `stop`/`error` are `stopped` and G7 refuses them. Both stop and error were probed. |
| M1 | **Closed** | An executed A1/A2/A0R/LADDER trial without E1 rule flags is now a STOP even with an empty event log; A0/FIXR3/EGATE are accepted. Test coverage is narrower (m3). |
| M2 | **Closed in substance** | The seven cases load the G1 summary and G6 rows from the production disk layout; the full 882-row table is written and assembled by `assemble.build`, then reloaded and analysed. Minor residuals m1/m3. |
| M3 | Carry-forward, accepted | `infra_attempts=1` and `proposer_gpu_seconds=0.0` remain named placeholders; they are descriptive and not a blocker for this synthetic integration, but must be populated or marked unmeasured before a real outcome table. |
| m1 | Minor | The seven-case `y_raw` assertion is relational (`row["y_raw"] == audits["final"]["y_raw"]`), not the hard-coded review values. |
| m2 | Minor | `assemble.load_audits` raises `AssembleStop("no audit rows found")` on an existing but empty `g7_rows.jsonl`; a stage whose campaigns are all zero-run would fail to assemble even though G7 accepts each row. |
| m3 | Minor | Test coverage is narrower than the checks: rule-arm STOP test covers only A2/A0; zero-run test asserts no `final` only; stopped test covers `stop` but not `error`; 882 rows are still clones of seven templates. |
| m4 | Minor | The unit record reports `156 passed` (actual focused run is **157**) and still says the full `r1/tests` suite is running; its full-suite evidence is stale. |

### (a) Zero-run campaign — closed

Probe on the production route (real `run_chunk` with a `ReplicateUnit` whose engine charges no
worker runs, then production `audit_campaign`):

```
summary {'worker_runs': 0, 'llm_calls': 80, 'keeps': 0, 'last_keep_run': None, 'status': 'complete'}
g7 rows []
Y_final rows 1 Y_keep rows 0
build_row OK 0 0.0 llm_call_cap {'5': None, '10': None, '15': None, '20': None}
```

`g7_rows` correctly omits `final`, `w` and `keep`; the descriptive `Y_final.jsonl` row is retained;
`build_row` accepts with `y_raw = 0`. The test `_zero_run_case` pins this at the G7 boundary.

**Residual m2:** passing that audit directory alone to the new assembler gives

```
assemble.load_audits REFUSED: AssembleStop no audit rows found
```

because `load_audits` treats an empty existing `g7_rows.jsonl` as an error. A normal 882-row stage
has other audit rows, so this is a degenerate all-zero stage; it is nevertheless a valid complete
stage that G7 would accept. Allow an existing empty file to return `[]` (and add a test).

### (b) Stopped/errored campaigns — closed

Real harness chunks whose factory returns `"stop"` and `"error"` at W:

```
stop  summary status stopped chunk status stopped -> REFUSED OutcomeTableError: status 'stopped'; ... (§10)
error summary status stopped chunk status stopped -> REFUSED OutcomeTableError: status 'stopped'; ... (§10)
```

`c3_d3.campaign_chunk` now uses `COMPLETE_ENDED_ON` on both routes; the chunk record and the
summary agree, and G7 refuses the stage. The test covers `stop`; `error` was verified by this probe
(m3).

### (c) Rule-flag STOP and no-rule arms — closed

Direct probe of `mechanism_counts` with one executed record and an empty event log:

```
A1 STOP SummaryStop  A2 STOP SummaryStop  A0R STOP SummaryStop  LADDER STOP SummaryStop
A0 ACCEPTED  FIXR3 ACCEPTED  EGATE ACCEPTED
```

This is the intended split: the four rule-logging arms fail closed; A0 and the two replicate
engines have no rule layer. The new test covers A2 (STOP) and A0 (accepted); the other arms are
covered by this probe, not by the test (m3).

### (d) Production disk boundary and case values — closed in substance

`test_seven_production_cases_pass_g7` now asserts, for each of the seven production cases, the
hard-coded `(worker_runs, last_keep_run, keeps)` tuple and loads the summary/G6 rows back from the
production `campaigns/*/summary.json` and `g7_rows.jsonl` layout with
`assemble.load_summaries`/`assemble.load_audits`. The full-table test writes the 882 summaries and
the `g7_rows.jsonl` to disk and calls `assemble.build`, then `write_table`/`D3.load_table`/
`D3.analyse`. The seven production values reproduced by my probe are:

| Case | runs | last keep | keeps | `y_raw` |
|---|---:|---:|---:|---:|
| harness keep at W | 20 | 20 | 20 | 0.0 |
| harness discard at W | 20 | 19 | 19 | 0.05 |
| harness terminal keep at early cap | 7 | 7 | 7 | 0.05 |
| FIXR3 keep at W | 20 | 20 | 6 | 0.70 |
| FIXR3 discard at W | 20 | 17 | 5 | 0.60 |
| EGATE keep at W | 20 | 20 | 2 | 0.80 |
| EGATE discard at W | 20 | 1 | 1 | 0.10 |

The runs/last-keep/keeps values are pinned in the test; the `y_raw` column is not hard-coded — the
test only checks `row["y_raw"] == audits["final"]["y_raw"]` (m1). The 882 rows are still clones of
the seven templates, so this is a coverage scaffold, not independent evidence for every campaign
(m3); that was already accepted in R1 as necessary for G7's exact coverage check.

### (e) No G7 or analysis change — closed

`git diff 1bd7f3d6..d8cfd7d0 -- r1/c3/d3_outcome_table.py r1/c3/d3_analysis.py
r1/tests/test_d3_analysis.py` is empty. Hashes at the reviewed tip:

| File | sha256 |
|---|---|
| `r1/c3/d3/summary.py` | `8daf261f3b00bf3556805109ed7abd540dd4a2c8bac399a6c4cd2f86b6e5b837` |
| `r1/c3/d3/audit.py` | `f17d8c15cac5e738cfc2de851c801f008eb55a047701c86540676a6aedfa346f` |
| `r1/c3/d3/campaign_chunk.py` | `98c16b6dd4e826572e92dbd10f35fbed2917b399aaafef20dbf1f283e7935bcb` |
| `r1/c3/d3/replicate_campaign.py` | `be6464fbc5949fcd80deb0cef57389dfc2a0fe1becbed8dbfb4df02361a905fd` |
| `r1/c3/d3/assemble.py` | `7671543bac1b081ac61c5bdaa32433b5dae886c928ea37080596f82d1d96444a` |
| `r1/tests/test_d3_integration.py` | `46985962304244f95c29402224c71e44dcd69f31dc8c4f8a20df1d70b7e5080c` |
| `r1/tests/test_d3_g1_chunk.py` | `3f2ed3d5b037f90a4f4f36a95362113b844e5e5a8a7fcaedaee0ba7309072170` |
| `r1/c3/d3_outcome_table.py` (G7) | `a9ce5d904c711642932c4b393f2d1f52e00e7f59e1f6d20cd1ea530fd7fba3ca` |
| `r1/c3/d3_analysis.py` | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| `r1/tests/test_d3_analysis.py` | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |

`git diff --check 1bd7f3d6..d8cfd7d0` is clean.

## Tests and counts

Focused command (tip, Python 3.12.8, pytest 9.2.0, harness `9bb41680`):

```
AR_HARNESS_ROOT=<harness9bb> python -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py \
  r1/tests/test_d3_g1_replicate.py r1/tests/test_d3_adapter.py \
  r1/tests/test_d3_audit_g6.py r1/tests/test_d3_integration.py \
  r1/tests/test_d3_outcome_table.py r1/tests/test_d3_analysis.py
```

**157 passed, 18 subtests passed** (10.46 s). The unit record's `156` is stale (m4).

Full suite, same command without the file list, `-rfE --continue-on-collection-errors`, with a
fresh `TMPDIR`:

| Run | Result |
|---|---|
| base `840ad01d` (reused list) | **115 failed, 4984 passed, 163 skipped, 3 errors, 71 subtests passed** (767.04 s) |
| tip `d8cfd7d0` | **114 failed, 4988 passed, 163 skipped, 3 errors, 71 subtests passed** (693.09 s) |

**No new failure ids at the tip.** The base list has 118 `FAILED`/`ERROR` ids; the tip has 117, a
strict subset. The one base-only id that is absent at the tip is
`FAILED r1/tests/test_t1_tasl_crosscheck.py::test_short_job_on_tasl7_then_compare_with_the_g1b_tasl2_attempt`
(shared GPU-lease timing; the TASL tests fail on `gpu0.lock` contention depending on run order). No
D3 test id fails at either tip. The three new integration tests pass in the full suite; their
addition accounts for the +4 passes (three new tests plus the one lease-timing pass), with no new
failure.

## Conclusion

The R1 blocking findings B1/B2 and the M1 fail-open are closed, and the M2 production disk boundary
is exercised. The code and the seven-case/882-row integration pass focused and full suites with no
new failure. I accept the integration for the synthetic unit, with the named minor test/assembler
hardening (m1–m4) and the unchanged M3 compute-placeholder carry-forward. The declaration remains
`frozen: false`; a real outcome table still needs measured or explicitly unmeasured proposer
compute. No G7 or analysis change is required.
