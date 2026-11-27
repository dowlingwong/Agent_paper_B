# D.3 G1/G6 revision 6c-3 — independent re-review (R3) of the replicate-arm driver

**Reviewer.** Fresh, independent re-reviewer; I did not write revision 6c-1/6c-2/6c-3, the FIXR3/EGATE
engines, G8 accounting, the G1 snapshot core or the chunk shell. Read-only: no code, campaign, audit, job,
label, evaluation, split, sweep-table or sealed file was run or opened; the reviewed branch was not
modified. The only writes are this review file and scratch worktrees under the session's temporary
directory.

**Target.** `origin/compute-d3-g1-design-r6c-20261127` @ `c1832cf6`, file
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md`,
sha256 `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521` (verified with
`git show c1832cf6:... | shasum -a 256`). A new commit on the same branch as 6c-1 (`ed0ad83b`) and 6c-2
(`690e8626`), not a force-push.

**Prior reviews.** 6c-1 `D3_G1_G6_REV6C_REVIEW_20261127.md` (CHANGES REQUIRED; 4 BLOCKING, 5 MAJOR,
7 MINOR) and 6c-2 `D3_G1_G6_REV6C_REVIEW_R2_20261127.md` (CHANGES REQUIRED; 3 MAJOR, 4 MINOR, 2 notes,
file sha256 `686d3277d3c01868149406968e8ac8c38a1e2e497cc47f65266c5f6e7cfaf5d1`). Revision 6c-3 answers
the 6c-2 N1–N9 in §11.

**Method.** Read 6c-3 in full with §11 against §3–§8; re-checked the same delivered files
(`r1/c3/d3_replicate.py`, `r1/c3/accounting.py`, `r1/c3/d3/snapshots.py`, `r1/c3/d3/campaign_chunk.py`)
and the pinned `ComputeBudget` (`harness_pin/src/autoresearch/control_plane/budget.py` at `a3fedbbd`);
re-ran the same unit modules. No integration test exists; 6c-3 changes no code.

---

Verdict: ACCEPTED FOR CODE

---

## Summary

All nine 6c-2 findings are resolved in substance:

- **N1** — the frozen `ComputeBudget` is kept in `budget_holder["value"]`, and both
  `consume_llm_call()` (§3.2) and `consume_worker_run(seconds)` (§3.5) reassign the returned object; the
  LLM cap and the parity check are defined through that holder.
- **N2** — `begin_step`/`write_final_from_state` take `incumbent_config`/`final_config` **contents** dicts;
  the recorder computes `config_sha256`; `engine.incumbent` is used only for the EGATE lookup and the
  projection; the final carries the final config contents.
- **N3** — `trial_id`, `last_kept_trial_index` and `llm_calls` are explicit `begin_step` arguments and are
  written into `extra.control`/`summary.json`; `w` comes from `recorder.count`.
- **N4–N9** — the harness w=20 comparison is corrected (the replicate final is separate because its
  exact-w snapshot is pre-decision); condition 5's field list now names `campaign_kind`, `pending`,
  `zero_variance_cases` and the `RunAttempt` failure classes; the G2 file is a harness-arm prerequisite,
  not a FIXR3/EGATE one; `run_one` maps `config_sha256` to the validated proposal/config and restores the
  incumbent workspace; the prior-review sha citations and the pre-declaration status are corrected.

No new BLOCKING or MAJOR issue was found. Three **MINOR** text residuals remain (below): the §3.6/§5
parity/cap check lines still spell `budget` instead of `budget_holder["value"]`; §4's final sentence still
says “from `engine.incumbent`” before the `final_config` call; and the final `write_final_from_state`
arguments are partly elided. These are wording/reference fixes; the holder, contents and field decisions
are explicit elsewhere and the design is accepted for code.

## Per-finding resolution

| Finding | Status | Evidence |
|---|---|---|
| **N1** frozen `ComputeBudget` not reassigned | **Resolved** (MINOR text residual) | §3.2 (`6c-3:78-80`): `budget_holder["value"] = budget_holder["value"].consume_llm_call()` before the call; §3.5 (`:99-100`): `budget_holder["value"] = budget_holder["value"].consume_worker_run(seconds)` before the engine charge; §11 N1 (`:279`) says the parity/cap checks read the holder. The `ComputeBudget` is `@dataclass(frozen=True)`; `consume_*` return a new object (`budget.py:43`, `:87-105`). MINOR: §3.6 (`:105`) and §5 (`:168-169`) still spell `budget.worker_runs`/`budget.llm_calls`; should be `budget_holder["value"].…` (R3-m1). |
| **N2** `engine.incumbent` is a sha, not config contents | **Resolved** (MINOR text residual) | §3.4 (`6c-3:87-91`): `incumbent_config` is the **config contents** of the last kept trial (`start_config` before the first keep); the recorder computes `config_sha256`; `engine.incumbent` is used only for the EGATE lookup and the projection. §4 (`:127-131`) repeats the contents/`config_sha256` rule; `write_final_from_state(..., incumbent_config=final_config, ...)` (`:156-157`) carries the final contents. `Fixr3Engine.incumbent`/`EgateEngine.incumbent` are `str` (`d3_replicate.py:122`, `:187`) and are used only for `counter.lookup`/the projection. MINOR: §4 (`:152`) still says “from `engine.incumbent`”; the next lines pass `final_config` contents (R3-m2). |
| **N3** missing `trial_id`, `last_kept_trial_index`, `llm_calls` | **Resolved** (MINOR text residual) | §3.4 (`6c-3:87-88`) passes `trial_id`, `last_kept_trial_index`, `llm_calls` explicitly; §3.7 (`:110-112`) writes them into `extra.control`/`summary.json`; §4 (`:127-130`) says `w` is read from `recorder.count` at the charge. `_TrialState` requires exactly these fields (`snapshots.py:261-269`), and the payload writes them (`:383-388`). MINOR: the `write_final_from_state` call (`6c-3:156`) elides the final `trial_id`/`last_kept_trial_index`/`llm_calls` in `...`; make them explicit, or state that the final uses the last step's `_trial` plus the post-decision keep (R3-m3). |
| **N4** wrong harness w=20 comparison | **Resolved** | §4 (`6c-3:157-159`): “The harness route keeps its own 5b rule unchanged; the replicate exact-w snapshot is pre-decision, so its `final.json` is necessarily a separate post-decision record.” The false “harness ... after the decision” sentence is gone. |
| **N5** field list incomplete | **Resolved** | §8 condition 5 (`6c-3:237-239`): new fields are `campaign_kind`, the optional `pending` object, and the trial/summary `extra.control` fields `zero_variance_cases` and the `RunAttempt` failure classes; `replicates` is the existing G8 field. |
| **N6** G2 listed as a FIXR3/EGATE prerequisite | **Resolved** | §7 (`6c-3:215-218`): G2 is a prerequisite for the A1/A2/LADDER harness arms; FIXR3/EGATE need no constants file; the pre-declaration freeze/publication (steps (3)/(5), including the G2 and verify-seed checks for the harness arms) is separate. |
| **N7** worker proposal/config mapping and restore unstated | **Resolved** | §3.5 (`6c-3:96-98`): `run_one` maps `config_sha256` to the current step's validated proposal/config (`config_by_sha`; the worker receives the proposal, not the sha) and restores the incumbent workspace before the call if the previous step discarded its candidate. |
| **N8** prior-review sha citation | **Resolved** | Header (`6c-3:9-13`): 6c-1 commit file sha `041c3c03…` and self-line content hash `c9c136d1…`; 6c-2 review file sha `686d3277…`. |
| **N9** pre-declaration status | **Resolved** | §7 (`6c-3:216-218`): `R1-D3-PREDECL-R4` is on `main`, binding in its own order and not yet frozen; the stale “signature still required” wording is gone. |

## §8 conditions

| # | Condition | Result | Evidence |
|---|---|---|---|
| 1 | Every actual worker call charged exactly once through one `ChargedRunCounter` (engine-owned; `run_one` exceptions → failed `RunOutcome`); reused incumbent never charged; fail closed on counter/budget/record/parity differences | **PASS** | Engine owns the charge (`d3_replicate.py:134-137`, `:217-220`, `:233-236`); `run_one` does not charge and converts a raise to `RunOutcome(success=False)` (`6c-3:92-104`); the counter is the single charge; EGATE reuse is `counter.lookup` with `charged: false` (`d3_replicate.py:190-191`, `:240-242`). The budget is the holder value, reassigned in §3.2/§3.5; §11 N1 states the checks read the holder. MINOR R3-m1: §3.6/§5 should spell `budget_holder["value"]` in the check lines. |
| 2 | Step-start projection of §4 (including EGATE `incumbent_runs`); no manager/step-ending E2 between capture and any run; deterministic hash; exact w=5,10,15,20 live; `pending` metrics/diffs | **PASS** | §4 (`6c-3:127-151`): `begin_step` records `trial_id`, contents, `start_config`, `last_kept_trial_index`, `llm_calls`, `w` from `recorder.count`, step index and the projection; EGATE `incumbent_runs` from `counter.lookup`; hash `json.dumps(..., sort_keys=True, separators=(",", ":"))` with no `repr`/ids/times; narrowed assertion allows per-pair `gate.decide`; `pending` carries candidate/incumbent metrics and diffs. |
| 3 | Same record layout (`campaigns/<instance_id>/`), `campaign_id`, record name, `final.json`, G6 path; `extra.control.replicates` exactly G8; `final.json` post-decision | **PASS** | §6 (`6c-3:189-195`) and §3.7/§3.9 (`:108-117`): layout, writers, `campaign_kind`, G8 `replicates`; §4 (`:152-159`): `final.json` is a separate post-decision record from `final_config` contents, not a `w20.json` alias; `engine.incumbent` is used only for the EGATE lookup/projection. MINOR R3-m2: the preceding “from `engine.incumbent`” phrase should say “identified by `engine.incumbent`, contents in `final_config`”. |
| 4 | §5.4/§5.5 unchanged; LLM cap charged through `ComputeBudget` before each manager call; `ended_on` follows `table_ended_on` | **PASS** | Rules/constants/seeds unchanged (`d3_replicate.py:105-258`); §3.2 (`6c-3:78-83`) charges the holder before each manager call and stops at 80; §5 (`:180-183`) uses `table_ended_on`, matching `accounting.py:228-244` / `d3_analysis.py:262-281`. MINOR R3-m1: §5 (`:168-169`) should read the holder. |
| 5 | No evidence/label/evaluation/sealed read; new record fields `campaign_kind`, optional `pending`, `zero_variance_cases` and `RunAttempt` failure classes | **PASS** | The revision is documentation; `accounting._jsonl` calls `refuse_sealed` (`accounting.py:53-56`); the engines read no label/evaluation/split/sweep-table; §8 (`6c-3:237-239`) now lists the complete new-field set. |

## MINOR residuals (non-blocking)

**R3-m1. The §3.6/§5 parity and cap check lines still name `budget`, not the holder.**
§3.6 (`6c-3:105-106`) says `counter.used == budget.worker_runs == …` and `budget.llm_calls == …`; §5
(`:168-169`) says `counter.used == budget.worker_runs` and `budget.llm_calls`. The holder is
`budget_holder["value"]` (§3.2/§3.5), and §11 N1 says the checks read the holder. The text should spell
`budget_holder["value"].worker_runs`/`.llm_calls` (or define `budget` as the holder's current value). The
design's intent is unambiguous from §3.2/§3.5/§11; this is a wording/reference fix.

**R3-m2. §4's final sentence still says “from `engine.incumbent`” before the `final_config` call.**
§4 (`6c-3:152-157`) says `final.json` is written “from `engine.incumbent` (or `start_config` …)”, then
passes `incumbent_config=final_config` and says the recorder computes `config_sha256` from `final_config`.
The call is correct; the preceding phrase should read “identified by `engine.incumbent`, contents in
`final_config`”. Wording-only.

**R3-m3. The final `write_final_from_state` call elides the final `trial_id`/`last_kept_trial_index`/
`llm_calls`.**
§4 (`6c-3:156`) shows `write_final_from_state(w_final, ended_on, incumbent_config=final_config,
state=projection(...), ...)`. The `begin_step` writes these fields explicitly; the final should either pass
the post-decision values explicitly or state that it uses the last step's `_trial` with the last keep
applied. Wording/API-clarity, not a design change.

## Scope and limits

**In scope.** Revision 6c-3 §11 and the changed §3–§8 against the same delivered engine, accounting,
snapshot and chunk files and the pinned `ComputeBudget`; the nine 6c-2 findings; the five §8 conditions;
the three MINOR residuals.

**Out of scope / not decided here.** The FIXR3/EGATE rules, constants, seeds, W=20, cap 80, K=10, Y_final
(no change found); the accepted 5b/6b text except where 6c-3 relies on it; the level-2 verify-seed and
pre-declaration status (R1-D3-VERIFY-SEED / R1-D3-PREDECL-R4; §7 now states it correctly); the tier-E
review of the engines/accounting/snapshot core themselves; any campaign, audit, label, evaluation, sealed
read, GPU job or smoke. I did not modify `main`, `coord/*`, the reviewed branch, the engine branch or the
snapshot branch.

**Test evidence.** The code is unchanged from 6c-1/6c-2; re-ran the same delivered unit modules in scratch
worktrees: `test_d3_fixr3.py`, `test_d3_egate.py`, `test_d3_g8_accounting.py` → **69 passed**;
`test_d3_g1_snapshots.py`, `test_d3_g1_chunk.py` → **16 passed**. There is still **no** integration test
for the replicate route + `begin_step`/`on_charge`/`write_final_from_state` + `campaign_chunk.py`; that is
expected for the G1 code unit's own tier-E review, not a design blocker.

## Review record

- Review target: `origin/compute-d3-g1-design-r6c-20261127` @ `c1832cf6`.
- Reviewed file sha256: `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521`.
- Prior reviews: 6c-1 `D3_G1_G6_REV6C_REVIEW_20261127.md` (CHANGES REQUIRED; 6c-1 commit file sha
  `041c3c03…`, self-line content hash `c9c136d1…`); 6c-2 `D3_G1_G6_REV6C_REVIEW_R2_20261127.md`
  (CHANGES REQUIRED; file sha `686d3277…`).
- Verdict: **ACCEPTED FOR CODE** — no BLOCKING or MAJOR remains; three MINOR text residuals (R3-m1–R3-m3).
- Base: the review branch `compute-d3-g1-design-r6c-review-20261127` (based on `origin/main` `5c901d19`;
  the reviewed branch is not merged).

**Review file sha256:** `78e94143078f5a90b37e888e6df8126dac4b7dc670e5ade14a255d27f4097345` — the sha256 of this review text above this line. The sha256 of the
committed file (this line included) is reported in the commit message and in the reviewer's report.

*Prepared by a fresh independent re-reviewer; no part of the reviewed work was authored by this session.*
