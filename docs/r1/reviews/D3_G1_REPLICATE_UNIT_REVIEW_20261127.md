# D.3 G1 — tier-E unit review of the replicate-arm driver (FIXR3/EGATE)

**Reviewer.** Fresh, independent tier-E reviewer (subagent). I did not write the reviewed branch, the
design, the engines, the G8 accounting unit or the snapshot core. Read-only on the reviewed branch: no
campaign, audit, GPU job, label, evaluation, split, sweep table or sealed file was read or run. The only
writes are this review file and a scratch worktree under the session's temporary directory.

**Target.** `origin/compute-d3-g1-replicate-20261127` @ `fb1013861f7109cf0738e8ea7e5c4e1bd414f6df`,
based on `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30`. Unit record:
`docs/r1/reports/d3_g1_20261127/D3_G1_REPLICATE_UNIT_20261127.md`. Design authority:
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md` (revision 6c-3,
sha256 `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521`), `ACCEPTED FOR CODE` by
`docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_R3_20261127.md`. The six file hashes in the unit record match the
branch tip exactly.

**Method.** Read the 6c-3 design (especially §3–§8 and §10–§11), the unit record, and the complete branch
diff. Read the delivered `r1/c3/d3_replicate.py` and `r1/c3/accounting.py` as the engine/accounting
contracts, and the pinned `ComputeBudget` in `AR_HARNESS_ROOT`. Ran the required unit modules in a scratch
worktree, then all `r1/tests/test_d3_*.py`, then wrote three small read-only probes against the branch
code for the parity, record-shape and failure-classification paths. Python 3.11.5 / pytest 7.4.0 on this
host (the author reported 3.11.13 / 9.2.0); the same tests pass here. The author's full-`r1/tests`
comparison is not yet available and was not run.

---

Verdict: CHANGES REQUIRED

---

## Summary

The core design is implemented in the right shape: the engine owns the single charge, `run_one` converts a
worker exception to a failed `RunOutcome` without charging the counter itself, reused EGATE incumbent runs
are not charged, the step-start projection is built from config contents and a deterministic ordered state,
exact `w` snapshots are written from `on_charge`, and `final.json` is a separate post-decision record rather
than a `w20.json` alias. The six required test modules pass (31 new/changed + 75 related), and all 399
`test_d3_*.py` tests pass.

One **BLOCKING** fail-open remains: the loop never checks the step's charged delta against the engine's
`result.runs_charged`, nor the replicate entries against the counter, so a record that disagrees with the
counter is written instead of stopping. Three **MAJOR** record-contract defects follow from the same area:
the G8 `extra.control.replicates` record path is not written at all, `zero_variance_cases` is overcounted,
and `RunAttempt` failure classes are neither captured nor classifiable.

## Per-condition results (§8)

| # | Condition | Result | Evidence |
|---|---|---|---|
| 1 | Every actual worker call charged exactly once through the one `ChargedRunCounter`; `run_one` exception → failed `RunOutcome` and no charge; reused incumbent not charged; fail closed on any counter/budget/record/parity difference | **FAIL — BLOCKING B1** | Charging and reuse are correct (engine charges at `d3_replicate.py:134-137`, `:217-220`, `:233-236`; EGATE reuse `:240-244`; `run_one` does not charge, `replicate_campaign.py:191-220`). The counter/budget check exists (`replicate_campaign.py:228-233`). But the design's third leg — the engine's `runs_charged` and the step's replicate record — is never compared (`:239-245`). Probe below. |
| 2 | Step-start projection from config contents (§4, including EGATE `incumbent_runs` from `counter.lookup`); no manager call or step-ending E2 between capture and any run; deterministic hash; exact `w` = 5/10/15/20 live, including inside a 3-run step / pair loop; `pending` metrics/diffs | **PASS** | `begin_step` takes contents and hashes `json.dumps(..., sort_keys=True, separators=(",",":"))` (`snapshots.py:368-398`); projection is the documented ordered state with no `repr`/id/time (`replicate_campaign.py:61-90`); EGATE `incumbent_runs` is read from `counter.lookup` (`:80-89`); unknown arm refuses (`:90`); `on_charge` requires the next sequential `w` and writes immediately (`snapshots.py:412-427`); `pending` is set before each charge (`replicate_campaign.py:216-217`). The `propose` call is made once before `begin_step` and only after the previous step (`:157-187`); no manager call exists inside `engine.step`. |
| 3 | Same layout (`campaigns/<instance_id>/`), `campaign_id`, record name, `final.json` and G6 path; `extra.control.replicates` exactly G8; `final.json` post-decision | **FAIL — MAJOR M1/M2** | Layout, `campaign_id`, record name and `final.json` are correct (`campaign_chunk.py:328-368`); the final is separate from `w20` (`snapshots.py:527-588`; test `test_replicate_final_is_separate_from_w20_and_carries_the_last_keep`). But the replicate ledger is not a G8 trial record: no `extra.control`, no `worker_mode`/`budget_index`, no events file (M1). `zero_variance_cases` is overcounted (M2). |
| 4 | §5.4/§5.5 rules/constants unchanged; LLM cap charged through `ComputeBudget` before each manager call; `ended_on` follows `table_ended_on` | **PASS with MINOR m1** | The engines are used as delivered; `test_d3_fixr3.py` / `test_d3_egate.py` pass. `budget_holder["value"] = ...consume_llm_call()` runs before `unit.propose` and stops at 80 (`replicate_campaign.py:158-169`). MINOR: the `llm_call_cap` and `no_fundable_candidate` ends assign the string directly (`:159`, `:167`, `:225`) instead of calling `table_ended_on`; values coincide today, but the pinned rule is bypassed. |
| 5 | No evidence/label/evaluation/sealed read; new fields are `campaign_kind`, optional `pending`, `zero_variance_cases`, and the `RunAttempt` failure classes | **FAIL — MAJOR M3 (and M2)** | No evidence/label/evaluation/sealed read exists in the loop. `campaign_kind` and `pending` are correct. `zero_variance_cases` is present but wrong (M2). The `RunAttempt` failure classes are absent and cannot be produced from the serialized record (M3). `campaign.json` also carries an extra `steps` count (`campaign_chunk.py:346`) not in the §8 list (MINOR m5). |

## Findings

### BLOCKING

**B1. The step record is not checked against `result.runs_charged` or the counter — a disagreeing record is
written instead of a STOP.**

`run_replicate_campaign` checks only `counter.used == budget.worker_runs` (`replicate_campaign.py:228-233`).
It stores `int(result.runs_charged)` and `list(result.replicates)` without comparing either to the step's
charge delta or to each other (`:239-245`). The design's §2 contract is
`counter.used == ComputeBudget.worker_runs == the engine's runs_charged` at every step end, and §5 makes a
trial record whose replicate entries disagree with the counter a STOP. Neither check exists.

I reproduced the fail-open with an `Fixr3Engine` wrapper that leaves the engine behaviour unchanged but
reports `runs_charged = 1` after each 3-run step. The campaign completed normally with `worker_runs = 18`
and six step records that each claimed `runs_charged = 1` while carrying two charged candidate entries
(and the implicit charged j = 0 trial run). No `ReplicateStop` was raised and `campaign.json`/`ledger.jsonl`
would have recorded the inconsistent step.

Required fix: after each `engine.step`, compute the delta from the counter and require
`delta == result.runs_charged`; require the number of charged replicate entries (plus the candidate j = 0
trial run) to equal that delta; validate the entry contract (the `replicate_entries` rules: no candidate
j = 0, no uncharged candidate, no duplicate `(role, j)`) and raise `ReplicateStop` on any difference.

### MAJOR

**M1. The replicate campaign does not write the G8 `extra.control.replicates` trial record or the events
that `campaign_usage` needs.**

`_run_replicate_chunk` writes ledger rows of the form
`{instance_id, step, decision, replicates, detail}` (`campaign_chunk.py:351-354`). There is no `extra`
object, no `control`, no `worker_mode`, no `budget_index`, and no proposal/revision event stream.
`accounting.replicate_entries` reads exactly `record["extra"]["control"]["replicates"]`
(`accounting.py:98-136`); on an actual branch-produced ledger row my probe returned `[]`, and
`campaign_usage` would count neither the replicate runs nor the manager calls. The entry objects
themselves (`role`, `j`, `seed`, `success`, `charged`, candidate j = 0 excluded) already have the G8 shape,
so the engines do not need to change; the record container/writer does.

This is the condition-3 `extra.control.replicates` contract and the §3.2/§3.7 "record each proposal/
revision event so `campaign_usage` counts the same calls" requirement. Required fix: write the per-step
trial records with `extra.control` (`replicates`, `trial_id`, `last_kept_trial_index`, `llm_calls`) and an
events stream, and add a test that runs `replicate_entries`/`campaign_usage` over the produced records.

**M2. `zero_variance_cases` is overcounted.**

Each step record stores the engine's **cumulative** `zero_variance_cases` (`replicate_campaign.py:244`), and
the chunk sums those cumulative values into the campaign record (`campaign_chunk.py:347`). With constant
metrics, FIXR3's per-step values are `[0, 1, 2, 3, 4, 5]` and the engine's actual count is 5, but the probe's
`campaign.json` recorded **15**. The ledger writer does not even write `zero_variance_cases`
(`campaign_chunk.py:351-354`). Condition 5/§3.7 requires the reported count to be the campaign's count.
Use the final engine value once, or store per-step deltas.

**M3. `RunAttempt` failure classes are neither captured nor classifiable.**

`RunAttempt.as_dict` (`replicate_campaign.py:53-58`) drops `card_other_processes` and
`host_other_processes`; `ReplicateUnit.run_trial` returns only `(success, metric, seconds)`
(`:119`, `:207-211`), so those fields are never populated; and on a worker exception the stored cause is
`"<ExceptionType>: <message>"` (`:212-215`). A probe's failed attempt serialized as
`"cause": "RuntimeError: synthetic worker failure"`, and
`classify_worker_failure("RuntimeError: synthetic worker failure")` raised
`ValueError: unknown failure cause ...`. A `budget_hit`/`oom` conditional-infrastructure failure cannot be
classified without the card/host counts, so the §5 failure rule (infrastructure loses the whole attempt;
proposal failure is charged) cannot be applied from the record. Condition 5 names the `RunAttempt` failure
classes as a record field. Required fix: a structured cause and the R1-CARD-SHARE counts in the attempt
record, plus the classification/class field G8 can consume.

### MINOR

**m1. `ended_on` does not always go through `table_ended_on`.** The `llm_call_cap` and
`no_fundable_candidate` branches assign the string directly (`replicate_campaign.py:159`, `:167`, `:225`);
only the `w = 20`/fallback path calls `table_ended_on` (`:253-261`). The values are equivalent under the
current preconditions (w < 20, calls < 80), but the design's §5 pins the rule; route every end through it (or
assert the direct value equals it).

**m2. No arm cross-check between the spec and the adapter.** `_run_replicate_chunk` accepts a FIXR3/EGATE
`spec.arm` and builds the recorder with that arm (`campaign_chunk.py:319-337`), but never checks
`unit.engine.arm == spec.arm`. A mispaired factory would write spec-arm snapshots/records with an
engine-arm projection and the wrong `pending_action`. Add the check before the first campaign.

**m3. `run_chunk` does not refuse the harness `factory` path for a replicate arm.** With no
`replicate_factory`, a FIXR3/EGATE `ChunkSpec` is accepted by the harness branch (`campaign_chunk.py:186-200`)
and would be routed through `run_real_campaign`, outside the replicate loop. The replicate branch checks its
arm, but the harness branch does not check that the arm is a harness arm. Add the complementary guard.

**m4. `write_final_from_state` does not enforce the `w_final = 0` end-condition rule.** It accepts any
`ENDED_ON` at `w_final = 0` (`snapshots.py:541-557`); design §4 m1 permits only `llm_call_cap` (or the
excluded `error`). The loop cannot currently produce the illegal case, but the public recorder API can.

**m5. Extra record field / missing per-trial fields.** `campaign.json` adds a `steps` count
(`campaign_chunk.py:346`) beyond the condition-5 field list, and §3.7's per-trial `trial_id`,
`last_kept_trial_index` and `llm_calls` are written only into snapshots, not into a trial record or
`summary.json` (the summary has only campaign totals). This overlaps M1 and is fixed with it.

## Test evidence

In the scratch worktree at `fb101386`, with
`AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness`:

- `python3 -m pytest r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_replicate.py -q`
  → **31 passed**.
- `python3 -m pytest r1/tests/test_d3_fixr3.py r1/tests/test_d3_egate.py r1/tests/test_d3_g8_accounting.py -q`
  → **75 passed**.
- `python3 -m pytest r1/tests/test_d3_*.py -q` → **399 passed**.
- The author's full-`r1/tests` comparison is **pending/not available**; I did not run the full suite.
- Probes (outside the repository, no branch modification): the `runs_charged`-mismatch campaign finished
  without a STOP; a branch-produced ledger row returned `[]` from `replicate_entries`; the constant-metric
  FIXR3 campaign recorded `zero_variance_cases = 15` where the engine count was 5; a failed attempt's
  serialized record lacked the card/host counts and its cause was refused by `classify_worker_failure`.

## Scope and limits

Reviewed: the five §8 conditions for the branch diff (`r1/c3/d3/replicate_campaign.py`,
`r1/c3/d3/snapshots.py`, `r1/c3/d3/campaign_chunk.py`, the three tests, the unit record) against 6c-3, the
delivered engines/G8 accounting, and the pinned `ComputeBudget`. Not reviewed here: the real D.3 adapter
(node specs, gemma4_31b manager, seven arms), the G6 audit implementation, the FIXR3/EGATE statistical
rules themselves (delivered and tested), and the author's full-suite comparison. No main, coord or reviewed
branch was modified.

*Prepared by a fresh independent tier-E reviewer; no part of the reviewed work was authored by this
session.*
