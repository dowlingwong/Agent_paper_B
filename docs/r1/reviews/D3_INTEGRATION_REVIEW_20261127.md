Verdict: CHANGES REQUIRED

# D.3 runner → audit → outcome-table integration — independent tier-E review

**Task:** `compute/20261127-23`. **Reviewed tip:** `1bd7f3d6d724a9d2653fd06807e639a5ef4f4129`
(`compute-d3-integration-20261127`); **base:** `origin/main` `840ad01d`. **Harness:**
`9bb416805175149eb87b71f28d77530572aa4bce`. **Unit record:**
`docs/r1/reports/d3_integration_20261127/D3_RUNNER_AUDIT_TABLE_20261127.md`.

**Independence.** I am a fresh tier-E reviewer. I did not write this unit, I did not work on the
task branch, and I did not modify it. I read the diff in a separate worktree created from the
reviewed tip and ran the tests and probes below myself. This review branch
(`compute-d3-integration-review-20261127`) contains only this record. No real campaign, GPU job,
label, evaluation or sealed read occurred; all campaigns and audit metrics below are synthetic.

The two step-(5) gaps are substantively closed for campaigns with at least one charged run: G1 now
writes the exact `d3_outcome_table.SUMMARY_KEYS` record from the production ledger, events and
recorder captures; G6 audits each kept incumbent at its charged-run count on the declared seeds and
writes `Y_keep.jsonl` and `g7_rows.jsonl`; and G7 and the pinned analysis are byte-identical to the
reviewed source. The seven review cases and the 882-row synthetic table pass. I do not accept yet,
because two producer-side contract errors remain (B1, B2); both are small fixes but they can produce
an unassemblable table or a table containing a stopped campaign.

## Findings

| ID | Severity | Finding |
|---|---|---|
| B1 | **Blocking** | G6 `g7_rows` always emits a `final` audit row, including for `w_final = 0`; G7 explicitly forbids any audit row for a campaign with no charged run. A valid `llm_call_cap` campaign with zero worker runs cannot be assembled. |
| B2 | **Blocking** | G1 maps `ended_on` values `stop` and `error` to summary `status = "complete"` (because `ENDED_ON` includes them). A stopped campaign at W or at the call cap is therefore accepted by G7 as a normal `worker_runs`/`llm_call_cap` row, contradicting §10 and the chunk record's `status = "stopped"`. |
| M1 | Major | The mechanism-count guard fails open when the event log is absent/empty for a flag-logging arm: A1/A2/LADDER/A0R silently get zero mechanism counts instead of the declared STOP. The A2 chunk test relies on this fixture tolerance using `ContinueController`, which is not a valid A2 campaign. |
| M2 | Major | Test evidence bypasses the production disk boundary and does not pin the review cases: `assemble.py` is never called by a test; `Y_keep.jsonl`/`g7_rows.jsonl` are written but never read/asserted; the seven-case test asserts only campaign id/status, not the review's runs/last-keep/keeps/Y values; the 882-row test hand-edits cloned summaries. |
| M3 | Major (carry-forward) | `proposer_gpu_seconds` is a hard-coded `0.0` and `infra_attempts` a hard-coded `1`; tokens/worker seconds are zero when the event stream has no telemetry. Judged acceptable for this integration (descriptive fields, no invented values), but not acceptable as final measured compute without a producer or an explicit "unmeasured" basis. |
| m1 | Minor | The unit record still says "full suite pending at this commit"; the full-suite evidence is supplied by this review. |

### B1 — a valid `w_final = 0` campaign cannot be assembled

`r1/c3/d3/audit.py::g7_rows` unconditionally does `add("final", result["final"])`. G7's reviewed
`build_row` has the opposite rule for `runs == 0`:

```python
if runs == 0:
    if set(audit) != {"keep"} or audit["keep"]:
        raise OutcomeTableError(f"{cid}: a campaign with no charged run has no audit row")
```

and `r1/tests/test_d3_outcome_table.py::test_a_campaign_without_a_charged_run_has_y_zero_and_no_audit`
pins that contract. A zero-run campaign is a declared outcome: a replicate arm can spend all 80
LLM calls on control-plane rejections without a single worker run (`run_replicate_campaign` then
ends `llm_call_cap` with `counter.used == 0`), and G7 accepts it with `y_raw = 0` and no audit.

I reproduced this through the production route, not a fixture: a real `run_chunk` EGATE campaign
whose `validate()` returns `None` for every proposal, then the production `audit_campaign` and the
new `assemble.build`:

```
summary {'worker_runs': 0, 'llm_calls': 80, 'keeps': 0, 'last_keep_run': None,
         'status': 'complete', 'unfundable': False}
ASSEMBLE REFUSED: OutcomeTableError D.3a__EGATE__digits_mlp__s6201__r0:
  a campaign with no charged run has no audit row
```

The G1 summary and G6 audit are otherwise correct; only the unconditional final row is wrong.
Fix in G6: omit the `final` row when the audited final has `w == 0` (the `keep` set is empty), and
add a regression test that runs a production chunk/audit and builds the row. G7 and the analysis
must not change.

### B2 — stopped/errored campaigns are labelled complete

Both routes in `r1/c3/d3/campaign_chunk.py` do:

```python
status = "complete" if ended_on in ENDED_ON else "stopped"
```

but `snapshots.ENDED_ON` is `("worker_runs", "llm_call_cap", "no_fundable_candidate", "stop",
"error")`. G7's `_check_summary` refuses only `status != "complete"`; it never sees `ended_on`.
Consequently a campaign whose factory returns the permitted `"stop"` (or, where the at-W equality
happens to hold, `"error"`) is written as complete. I ran a real harness chunk whose factory
returned `"stop"` at W and then audited it through G6/G7:

```
campaign summary status complete | chunk status stopped | row ended_on worker_runs | worker_runs 20
```

The table builder accepted it as a `worker_runs` row. That violates §10 ("a stage with a campaign
that is not complete is a STOP") and contradicts the chunk-level status. The current adapter's
resolver does not return `stop`/`error`, so this is latent in the adapter, but the G1 chunk's
documented factory contract permits them and the chunk already records the stopped status. Fix:
make the summary complete only for `worker_runs`, `llm_call_cap` and `no_fundable_candidate` (or
refuse a summary for `stop`/`error`), and test the stopped case.

### M1 — the rule-flag guard fails open on an absent event log

`summary.mechanism_counts` guards an executed trial without E1 rule flags only when `events` is
truthy:

```python
if ran and flag is None and arm not in NO_RULE_FLAGS and events:
    raise SummaryStop(...)
```

Thus a production A1/A2/LADDER/A0R campaign whose `events.jsonl` is missing or empty silently gets
`duplicates_proposed = 0` (and any rule/value skips as zero), which G7 then accepts. This is
fail-open where G7's reviewed `mechanism_counts` is fail-closed. The A2 chunk-layout test relies on
this tolerance because it uses `ContinueController` and no event store, but `ContinueController` is
not a valid A2 controller and that is a test fixture, not a production campaign.

Probe:

```
A2 empty events accepted; duplicates_proposed = 0 keeps = 1 proposals = 1
LADDER empty events accepted; duplicates_proposed = 0 keeps = 1 proposals = 1
A0 empty events accepted; duplicates_proposed = 0 keeps = 1 proposals = 1
```

The A0/replicate tolerance is itself deliberate and semantically correct (those arms have no rule
layer). The defect is that the tolerance is not scoped to them. Require a marker for fixture
campaigns, or make an empty event log a STOP for the flag-logging arms and give the chunk test a
valid controller/event store.

### M2 — tests do not exercise the production assembly boundary and do not pin the review cases

The code under test is largely exercised, but the delivered evidence has gaps:

- `assemble.py` is imported but never called in `test_d3_integration.py` (`assemble.load_summaries`,
  `load_audits` and `build` are untested). The seven cases hand the in-memory summary and the
  in-memory `g7_rows` projection to `build_row`; the disk `summary.json`/`g7_rows.jsonl` boundary is
  validated only by my manual probe (one summary, 24 audit rows, row built).
- `audit_campaign` writes `Y_keep.jsonl` and `g7_rows.jsonl`, but no test reads or asserts their
  contents. The integration helper calls `audit.g7_rows(result)` on the returned object instead.
- The seven-case test asserts only `campaign_id` and `status`. It does not pin the review's case
  values. My probe of the production records reproduces them (runs / last keep / keeps): A0 20/20/20,
  20/19/19, 7/7/7; FIXR3 20/20/6, 20/17/5; EGATE 20/20/2, 20/1/1, with the expected `y_raw`
  (0, 0.05, 0.05, 0.70, 0.60, 0.80, 0.10). Without those assertions a consistent keep-accounting
  regression would pass G1 and G7 together.
- `test_full_design_assembly` uses `_clone` to rewrite `node`, `instance_seed`, `arm`, `repetition`
  and `start_config_hash` by hand and reuses one production template per arm family; it is a
  coverage scaffold (the docstring says so), not 882 independent production campaigns. It does
  assemble, write, reload and analyse 882 rows, but it should not be read as end-to-end evidence for
  each campaign.
- There is no test of the w=0 case, the stopped/error status, the empty-event STOP, or a no-keep
  campaign through the full route.

These do not by themselves make the core interfaces wrong — I verified w>0 assembly manually — but
they are why B1/B2 were not caught, and the regression suite should be tightened before this unit is
used as the freeze gate.

### M3 — placeholder and unmeasured compute fields (judged acceptable here)

- `infra_attempts = 1`: **acceptable.** A retained campaign is one attempt; a whole-chunk retry is a
  new chunk and the lost one is not charged or tabulated.
- `proposer_gpu_seconds = 0.0`: **a sentinel, not a measurement.** G7 requires a finite non-negative
  number and the pre-declaration marks compute descriptive, so this does not change an outcome and
  is not a STOP for the synthetic integration. It must not be presented as measured proposer use;
  before a real outcome table either populate it from the launcher/events or record an explicit
  unmeasured basis.
- `llm_tokens_prompt`/`llm_tokens_completion`: real when `llm_call`/`llm_meta` events carry token
  telemetry; zero in the synthetic test because the factory supplies no event store. Acceptable for
  this test; production runs should populate them.
- `controller_seconds` is zero unless a decision event carries `latency_s`; `worker_seconds` is zero
  for the harness fixture without events. Both are typed and non-negative; acceptable as
  descriptive fields, with the same carry-forward.

I do **not** require G7 or the analysis to change for any of these; G7's contract is already the
authority and both are hash-pinned.

## Checks that passed

1. **G1 summary shape and derivation.** `build_campaign_summary` constructs the record from the
   ledger (`keeps`, `last_keep_run`, charged runs, rule/value skips), the event log (proposals,
   duplicate flags, tokens, worker/controller seconds) and the recorder's E2 live configuration
   captures (`config_sha256` for every executed trial). Start/final hashes come from the recorder's
   start config and the live post-decision worker/engine configuration, not a recomputed edit chain.
   It verifies `set(summary) == SUMMARY_KEYS` on every build. The seven production cases and the
   changed chunk test assert the exact key set.
2. **G6 per-keep audits.** For every `keeps/keep-<run>.json` G6 audits the captured bytes at
   `w = run` on `audit_seeds(instance)` (6701–6880), using the shared `(node, config_sha256, seed)`
   cache, writes a per-keep record, `Y_keep.jsonl` and the six-key `g7_rows.jsonl`. The last keep's
   audit has the final configuration and the same cached `y_raw` as the final audit, so G7's
   last-keep/final equality passes for all seven cases. (B1 is the zero-run exception; M1 is the
   event-log gap.)
3. **G7 and the pinned analysis are unchanged.** `r1/c3/d3_outcome_table.py` sha256
   `a9ce5d90…fba3ca`, `r1/c3/d3_analysis.py` `c0be0399…a484ce`, analysis tests `c6c56c33…f01a4` —
   byte-identical to the reviewed source. `git diff --name-status origin/main..tip` touches only G1,
   G6, the new summary/assembly modules and tests; no declaration or signed value changed.
4. **Seven cases and the 882-row table.** All seven go through the production `run_chunk`
   (harness and replicate routes), the production summary, `audit_campaign` and G7 `build_row`.
   The full-table test assembles 882 rows, writes, reloads (`D3.load_table`) and runs `D3.analyse`;
   it passes. Caveats are M2, not a failure of the values.
5. **Focused tests and the changed layout test.** `156 passed, 18 subtests passed` in 8.27 s.
   `test_d3_g1_chunk.py` still checks the campaign/chunk layout, the four record files, the
   `SHA256SUMS` entries, the `record_name`/`campaign_id`, the summary keys/status/runs and the
   `campaign.json` end condition.

## Commands, counts and hashes

Focused command (tip, Python 3.12.8 / pytest 9.2.0, pinned harness `9bb41680`):

```
AR_HARNESS_ROOT=<harness9bb> python -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_snapshots.py \
  r1/tests/test_d3_g1_replicate.py r1/tests/test_d3_adapter.py \
  r1/tests/test_d3_audit_g6.py r1/tests/test_d3_integration.py \
  r1/tests/test_d3_outcome_table.py r1/tests/test_d3_analysis.py
```

`156 passed, 18 subtests passed` (8.27 s).

Full suite, same command without the file list, `-rfE --continue-on-collection-errors`, run in a
detached worktree at the base and in this worktree at the tip:

| Run | Result |
|---|---|
| base `840ad01d` | **115 failed, 4984 passed, 163 skipped, 3 errors, 71 subtests passed** (767.04 s) |
| tip `1bd7f3d6` | **116 failed, 4985 passed, 163 skipped, 3 errors, 71 subtests passed** (764.04 s) |

Tip ids not present in the base log (2):

- `FAILED r1/tests/test_t1_tasl_chain.py::test_the_seven_node_row_assembles_across_the_three_notes`
- `FAILED r1/tests/test_t1_tasl_crosscheck.py::test_default_part_on_both_hosts_seal_and_compare`

Both fail with `g1b_lib.Stop: STOP: the GPU lease /Users/wongdowling/r1_locks/gpu0.lock is held by
another job (no shared card)` while other suites were running. Targeted reruns of these three TASL
tests under the same held lease failed the same way at **both** the base and the tip (base: chain +
default failed; tip: chain failed; the previously base-only `test_short_job_on_tasl7…` also moved
with lease timing). They do not touch D3 and are environment/lease contention, not new code
failures. The one id that failed at base but not tip is the same TASL lease family:
`FAILED r1/tests/test_t1_tasl_crosscheck.py::test_short_job_on_tasl7_then_compare_with_the_g1b_tasl2_attempt`.
No new D3 test id appears at the tip; the two new integration tests pass.

Probes (scratch only, not committed):

| Probe | Result |
|---|---|
| production EGATE chunk, all proposals rejected, 80 LLM calls, 0 runs → `assemble.build` | `OutcomeTableError … a campaign with no charged run has no audit row` (B1) |
| harness chunk, factory returns `"stop"` at W → summary/audit/`build_row` | summary `complete`, chunk `stopped`, row `ended_on=worker_runs` accepted (B2) |
| A2/LADDER summary with empty events | accepted, `duplicates_proposed=0` (M1) |
| `assemble.load_summaries`/`load_audits` on a real runs>0 case | 1 summary, 24 audit rows, row built and accepted |
| seven production cases | runs/last-keep/keeps and `y_raw` match the reviewed case table |

File hashes at the reviewed tip:

| File | sha256 |
|---|---|
| `r1/c3/d3/summary.py` | `8f27ba0d1d232b341b20884f09b3504c71d71f6dd623ecf73b816b3b58e03b72` |
| `r1/c3/d3/snapshots.py` | `f15d9deef382c6d5e899eaefa91a2eefbadcc86bff0116ac37391a6f28526a48` |
| `r1/c3/d3/campaign_chunk.py` | `25eab803f04ed68d4a51834b6c928e134efc6f272b6b45382a1a8090d5319a66` |
| `r1/c3/d3/replicate_campaign.py` | `0f866d66d9320e5dbbf5eb8cabdfd38bcdc5616c29ea6d7c842d4fa9b7cec2aa` |
| `r1/c3/d3/audit.py` | `69eb588306a6321ce6c6d55c66a67c3cced2028f5fd6f0d77a2ef8fd5a9b61ac` |
| `r1/c3/d3/assemble.py` | `7671543bac1b081ac61c5bdaa32433b5dae886c928ea37080596f82d1d96444a` |
| `r1/tests/test_d3_integration.py` | `2c3fea366e4ce582c9d0a740c511885642b61dd2b81ea39b5f1ca3db4dc82d10` |
| `r1/tests/test_d3_g1_chunk.py` | `81e103c81ecfc902538a81228ee8f22a3030167970a6bf7678c96febcf6bc7de` |
| `r1/c3/d3_outcome_table.py` (G7) | `a9ce5d904c711642932c4b393f2d1f52e00e7f59e1f6d20cd1ea530fd7fba3ca` |
| `r1/c3/d3_analysis.py` | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| `r1/tests/test_d3_analysis.py` | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |

The published G6 at `origin/main` was `452724ec…a4a3`; the changed G6 here is
`69eb5883…61ac`, as intended by this unit. `git diff --check origin/main..tip` is clean.

## Conclusion

The step-(5) integration gaps are fixed for the presented runs, and the seven cases do reproduce the
review's outcomes. The unit is not ready for the freeze gate: fix B1 and B2 in G1/G6 (no G7 or
analysis change), scope or close the M1 fail-open, and add the missing end-to-end regression tests.
The declaration remains `frozen: false`; no freeze is authorised by this review.
