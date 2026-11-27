# D.3 G1 — tier-E unit review, round 2 (replicate-arm driver)

**Reviewer.** Fresh, independent tier-E reviewer (subagent), same reviewer as round 1. I did not write the
reviewed branch, the design, the engines, the G8 accounting unit or the snapshot core. Read-only on the
reviewed branch: no campaign, audit, GPU job, label, evaluation, split, sweep table or sealed file was read
or run. The only writes are this review file and a scratch worktree under the session's temporary
directory.

**Target.** `origin/compute-d3-g1-replicate-20261127` @
`02ad2370627c06404079bc9749105bb86227568b`, a normal commit on top of `fb101386` (no force push). Unit
record: `docs/r1/reports/d3_g1_20261127/D3_G1_REPLICATE_UNIT_20261127.md`. Design authority:
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md` (revision 6c-3,
sha256 `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521`), `ACCEPTED FOR CODE` by
`docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_R3_20261127.md`. Round-1 review:
`docs/r1/reviews/D3_G1_REPLICATE_UNIT_REVIEW_20261127.md` (`CHANGES REQUIRED`; 1 BLOCKING, 3 MAJOR, 5
MINOR). The six file hashes in the updated unit record match the reviewed tip exactly.

**Method.** Read the complete `fb101386..02ad2370` diff, the new tests and the updated unit record; re-read
the affected loop, recorder and chunk paths against 6c-3 §3–§8; re-ran the six required modules and all
`r1/tests/test_d3_*.py` in a fresh scratch worktree at `02ad2370` with
`AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness`; re-ran the round-1 probes for the
charge/entry parity, G8 ledger row, `campaign_usage`, `zero_variance_cases` and failure-class paths. Python
3.11.5 / pytest 7.4.0 on this host (the author reported 3.11.13 / 9.2.0); the same tests pass here. The
author's final full-`r1/tests` comparison is not yet available and was not run.

---

Verdict: ACCEPTED

---

## Summary

All round-1 BLOCKING/MAJOR findings are resolved in substance:

- **B1** — `run_replicate_campaign` now pins `before_runs`, requires
  `result.runs_charged == counter.used - before_runs`, and compares the charged `result.replicates` entries
  with the new counter runs (candidate j = 0 excluded). The new `Liar` test raises `ReplicateStop`; my
  round-1 lying-engine probe now stops with `step 0: the engine reports 1 charged runs, the counter gained 3`.
- **M1** — each step now writes a G8 trial row (`budget_index`, `trial_id`, `worker_mode`,
  `last_kept_trial_index`, `extra.control.replicates`, `extra.control.zero_variance_cases`) to
  `ledger.jsonl`, and `events.jsonl` is written. `replicate_entries` now returns the expected entries, and
  `campaign_usage` over a branch-produced FIXR3 campaign returns `worker_runs=18`, `replicate_runs=12`,
  `replicate_runs_reused=0`, `llm_calls=7`, matching the campaign summary.
- **M2** — `zero_variance_cases` is now the per-step delta; the constant-metric FIXR3 probe records **5**
  (was 15).
- **M3** — `RunAttempt` now carries `failure_class` and card/host process counts, the adapter may return a
  4th detail dict or raise an exception carrying them, and the new `oom` test records
  `failure_class="oom"`, `card_other_processes=[1,1]`, `host_other_processes=[3,3]`.
- **m1–m5** — `table_ended_on` is used for the unfundable and empty-stream-at-cap ends; the spec/engine arm
  check and the harness-branch FIXR3/EGATE refusal are present; `w_final=0` only accepts
  `llm_call_cap`/`error`; the extra `steps` count is removed from `campaign.json` and the per-trial fields
  are written to the G8 rows.

The remaining items are **MINOR** hardening/documentation residuals, listed below. None changes the
charged-run accounting, the snapshot contract, the G6 path or the outcome-table end condition for the
delivered engines.

## Per-condition results (§8)

| # | Condition | Result | Evidence |
|---|---|---|---|
| 1 | Every actual worker call charged exactly once through the one `ChargedRunCounter`; `run_one` exception → failed `RunOutcome` and no charge; reused incumbent not charged; fail closed on any counter/budget/record/parity difference | **PASS** (MINOR m1) | Engine-owned single charges (`d3_replicate.py:134-137`, `:217-220`, `:233-236`); EGATE reuse `:240-244`; `run_one` converts a raise without charging (`replicate_campaign.py:204-245`); `counter == budget` after the step (`:258-263`); `runs_charged` and charged-entry parity (`:264-278`). My lying-engine probe now raises `ReplicateStop`. MINOR m1: the entry comparison is a set of `(role, j, seed, success)`, so a metric-only difference or a duplicate entry is not caught; a duplicate would be refused later by `replicate_entries`. |
| 2 | Step-start projection from contents (EGATE `incumbent_runs` from `counter.lookup`); no manager/step-ending E2 between capture and any run; deterministic hash; exact `w` = 5/10/15/20 live; `pending` | **PASS** | Unchanged from round 1 and verified again: `begin_step` contents/hash (`snapshots.py:368-398`), deterministic projection (`replicate_campaign.py:61-90`), `on_charge` sequential exact-`w` write (`snapshots.py:412-427`), `pending` set before each charge (`replicate_campaign.py:216-217`). The manager call remains outside the step; no manager call or step-ending decision is interleaved with the runs. |
| 3 | Same layout (`campaigns/<instance_id>/`), `campaign_id`, record name, `final.json`, G6 path; `extra.control.replicates` exactly G8; post-decision `final.json` | **PASS** | Layout/writers (`campaign_chunk.py:328-368`); G8 rows now include `extra.control.replicates` and the per-trial fields (`replicate_campaign.py:295-302`); `events.jsonl` written (`campaign_chunk.py:351-357`); separate `final.json` (`snapshots.py:527-588`; test `test_replicate_final_is_separate_from_w20_and_carries_the_last_keep`); `zero_variance_cases` corrected (`replicate_campaign.py:279-281`, `campaign_chunk.py:350`). |
| 4 | §5.4/§5.5 rules/constants unchanged; LLM cap charged through `ComputeBudget` before each manager call; `ended_on` follows `table_ended_on` | **PASS** (MINOR m3/m4) | Engines unchanged; `test_d3_fixr3.py`/`test_d3_egate.py` pass. LLM charge before `unit.propose` and cap check (`replicate_campaign.py:163-181`). Unfundable and empty-stream-at-cap ends now call `table_ended_on` (`:177-180`, `:251-255`); the `w = 20` path does too (`:313-321`). MINOR m3: the top-of-loop cap branch still assigns `"llm_call_cap"` directly (`:164-166`). MINOR m4: an empty proposal at the cap is charged but produces no event, so `campaign_usage` undercounts that call by one on the designed empty-stream end path. |
| 5 | No evidence/label/evaluation/sealed read; new fields are `campaign_kind`, optional `pending`, `zero_variance_cases`, and the `RunAttempt` failure classes | **PASS** (MINOR m2/m6) | No evidence/label/evaluation/sealed read in the loop; `campaign_kind` and `pending` correct; failure class and card/host counts now recorded in `runs.jsonl` (`replicate_campaign.py:53-62`, `:225-239`); `oom` test added. MINOR m2: the default `failure_class="runtime_error"` is written for successful attempts too, and `"runtime_error"` is not a G8 class (`classify_worker_failure` refuses it). MINOR m6: the classes are in `runs.jsonl`, not in the trial `extra.control`/campaign summary that §3.7 also mentions. |

## Round-1 finding resolution

| Finding | Status | Evidence |
|---|---|---|
| **B1** missing `runs_charged`/entry parity | **Resolved** (MINOR m1) | `replicate_campaign.py:247-278`; new `test_engine_runs_charged_must_match_the_counter` (`test_d3_g1_replicate.py:143`); round-1 lying-engine probe now stops. |
| **M1** no G8 `extra.control.replicates`/events | **Resolved** | G8 trial rows `replicate_campaign.py:295-302`; `ledger.jsonl`/`events.jsonl` `campaign_chunk.py:351-357`; chunk test `test_d3_g1_chunk.py:249-251`; `replicate_entries`/`campaign_usage` probe above. |
| **M2** cumulative `zero_variance_cases` overcount | **Resolved** | per-step delta `replicate_campaign.py:279-281`, `:293`; chunk sum `campaign_chunk.py:350`; constant-metric probe records 5. |
| **M3** `RunAttempt` classes/counts absent | **Resolved** (MINOR m2/m6) | `RunAttempt.failure_class`/counts `replicate_campaign.py:47-62`; detail/exception capture `:225-239`; `oom` test `test_d3_g1_replicate.py:169`. |
| **m1** direct `ended_on` | **Partially resolved** — unfundable/empty-stream fixed, top-of-loop branch remains (m3) | `replicate_campaign.py:164-166`, `:177-180`, `:251-255`, `:313-321`. |
| **m2** no spec/engine arm check | **Resolved** | `campaign_chunk.py:336-338`. |
| **m3** harness branch accepted replicate arms | **Resolved** | `campaign_chunk.py:196-197`. |
| **m4** `w_final=0` end restriction | **Resolved** | `snapshots.py:550-551`; test `test_w_zero_final_refuses_a_non_cap_end` (`test_d3_g1_snapshots.py:363`). |
| **m5** extra `steps` / missing per-trial fields | **Resolved** | `steps` removed (`campaign_chunk.py:349`); `trial_id`/`budget_index`/`llm_calls`/`last_kept_trial_index` in G8 rows (`replicate_campaign.py:295-302`). |

## MINOR residuals (non-blocking)

**m1. The entry parity is set-based and omits metric/duplicate/uncharged checks.**
`replicate_campaign.py:270-278` compares `{(role, j, seed, success)}` for charged entries. A charged entry
whose `metric` differs from the counter's run, or a duplicate charged entry, would pass the set comparison
(the duplicate would later be refused by `accounting.replicate_entries`). A `charged: false` entry is not
checked against an actual prior run at all. Recommended follow-up: compare a list/multiset of the full G8
entry (including `metric`) and run the `replicate_entries` validation before writing the row.

**m2. `failure_class` defaults to the non-G8 string `"runtime_error"` and is written on successes.**
`replicate_campaign.py:50` defaults every `RunAttempt` to `"runtime_error"`, including a successful run;
`accounting.classify_worker_failure("runtime_error")` raises `ValueError` (the G8 unit treats an unknown
runtime error as a STOP). A typed exception/detail (as in the new `oom` test) is classified correctly.
Recommended follow-up: `None` on success, and either require a declared class or fail closed when a failed
run has no class.

**m3. The top-of-loop LLM-cap branch still bypasses `table_ended_on`.**
`replicate_campaign.py:164-166` assigns `ended_on = "llm_call_cap"` directly. The value is correct under the
current preconditions, but the other three ends now use the pinned rule; route this one through it for
consistency.

**m4. An empty proposal at the cap is charged but not evented.**
If `unit.propose` returns `None` on call 80, the loop charges the call, ends `llm_call_cap`, and returns
`llm_calls = 80`; `events.jsonl` has only 79 `proposal_created` events, so `campaign_usage` reports 79. I
reproduced this on the branch (all proposals rejected until call 80, then `None`). This is the designed
empty-stream end path (§3.8); add an event for the empty call (or another counted event type) so the G8
cross-check matches.

**m5. The unit record's per-file test counts are wrong.**
The record says `test_d3_g1_snapshots.py 19`, `test_d3_g1_chunk.py 9`, `test_d3_g1_replicate.py 8` (36),
but the branch collects and passes **18 + 9 + 7 = 34**; the record's total `34` is correct. Documentation
only.

**m6. Failure classes are only in `runs.jsonl`.**
The new G8 trial rows carry `extra.control.replicates` and `zero_variance_cases` but not the `RunAttempt`
failure classes; those live in the attempt side record `runs.jsonl`. §3.7 says "`extra.control` /
`summary.json`"; if the intent is a single trial-level summary, add the classes there (or state that the
`runs.jsonl` side record is the canonical location).

**Note (not a finding).** `budget_index` in the replicate G8 rows is 0-based (`step_index`), while the G8
unit's synthetic harness rows use 1-based indexes. `campaign_usage` does not depend on the base, but a
downstream reader that assumes 1-based trial indexes should be checked when the replicate adapter is
connected.

## Test evidence

In a fresh scratch worktree at `02ad2370`, with
`AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness`:

- `python3 -m pytest r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py r1/tests/test_d3_g1_replicate.py -q`
  → **34 passed** (18 + 9 + 7).
- `python3 -m pytest r1/tests/test_d3_fixr3.py r1/tests/test_d3_egate.py r1/tests/test_d3_g8_accounting.py -q`
  → **75 passed**.
- `python3 -m pytest r1/tests/test_d3_*.py -q` → **402 passed**.
- The author's final full-`r1/tests` comparison is **pending/not available**; I did not run the full suite.
- Probes: the round-1 lying-engine probe now raises `ReplicateStop`; a branch-produced FIXR3 campaign's
  `campaign_usage` returns `(worker_runs=18, replicate_runs=12, reused=0, llm_calls=7)` and
  `zero_variance_cases=5`; the empty-at-cap end path shows `llm_calls=80` with 79 events (m4).

## Scope and limits

Reviewed: the five §8 conditions for the `fb101386..02ad2370` diff and the new tests, against 6c-3, the
delivered engines/G8 accounting, and the pinned `ComputeBudget`. Not reviewed here: the real D.3 adapter
(node specs, gemma4_31b manager, seven arms), the G6 audit implementation, the FIXR3/EGATE statistical
rules themselves (delivered and tested), and the author's full-suite comparison. No main, coord or reviewed
branch was modified.

*Prepared by a fresh independent tier-E reviewer; no part of the reviewed work was authored by this
session.*
