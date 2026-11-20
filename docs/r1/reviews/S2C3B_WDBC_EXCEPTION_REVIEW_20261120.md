# Review: R1-S2C3B-WDBC declared C3b exception (Paper B, route R1)

Reviewer: independent code reviewer (fresh context, judged from the repository only)
Date: 2026-11-20
Branch: `origin/s2c3b-wdbc-exception-20261120`; parent = published main `df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`
Code-Commit: 31ae7ad46c8d4ac44b897c0852781af0a921fba1
Diff reviewed: `git diff df58bcd5 31ae7ad4` (4 files, +173/-2): `sweep2/s2_c3b_lib.py`, `sweep2/s2_c5_switch.py`,
`r1/tests/htcondor/test_s2_c3b.py`, `r1/tests/htcondor/test_s2_c5_switch.py`. PLAN is not touched by this commit
(the row R1-S2C3B-WDBC is absent on published main and at 31ae7ad4; it is to be committed with this code).
Real data: `docs/r1/reports/sweep2_20261116/s2c3b_launch_20261120/job_record.json` on
`origin/ops-s2c3b-launch-stop-20261120` (paper_commit df58bcd5, `stop` = "only 7/8 ... ['openml_wdbc']").

## Summary

The exception is narrow and fail-closed for every realistic input. The 8/8 path is unchanged in both the driver and
the switch. With the real STOP record's `liveness_results`, the exception is accepted when the row is present and
refused when it is absent, in both the driver and the launch check. After acceptance the driver goes on exactly as
on 8/8: prompt measurement, cross-check, sweep-1 comparison, `finished_utc`, persist. The accepted record meets every
other `_verify_launch` condition. Nothing else in `sweep2/` blocks a 16-chunk launch. The remaining findings are
minor hardening and documentation items, plus one launch precondition outside the code (the PLAN row and the
authorization note's 8/8 wording).

## Findings

### Blockers
None.

### Major (code)
None.

### Launch precondition (not code; must be handled in the PLAN commit)
- **P-1. Published authority text still says 8/8.** R1-SWEEP2-AUTH (PLAN on main, row at ~line 1299) says the launch
  commit is one "at which the S2-C3b liveness is rerun and passes 8/8". The approved authorization note
  `docs/r1/authorizations/c3_sweep2_20261119.md` repeats this: line 7 ("rerun 8/8"), line 33 (P6 "launch-commit C3b 8/8
  required"), lines 73, 90 and 108, and line 113, which lists "liveness < 8" among the declared STOPs. The template
  `sweep2/s2_c5_authorization.template.md:24` says the same. The switch does not parse this prose
  (`parse_note`, `s2_c5_switch.py:66-109`), so it will not refuse. But a 7/8 launch would contradict the approved note
  that the spec pins by sha256 unless the R1-S2C3B-WDBC row explicitly amends R1-SWEEP2-AUTH's "8/8" and the note's
  "liveness < 8" STOP for exactly this shortfall. If the note itself is changed, its sha changes, and the
  `label_source.authorization_sha256` pins in all 16 chunk specs must be regenerated. Also note R1-S2C3B-RERUN
  (~line 1286), which already anticipates "the author decides that the 7 nodes proceed as usual, with disclosure". The new row should cite it.

### Minor
- **m1. The switch trusts the driver's `declared_exception` and does not re-derive it from `nodes`.**
  `s2_c5_switch.py:182-194` checks `live_nodes == 7`, `failed_nodes == ["openml_wdbc"]`, the five declared keys and
  `observed`, but not `gate["nodes"]["openml_wdbc"]["failed_criteria"]` / `criteria.invalid_rate`. Verified in Python:
  a record whose `declared_exception` is correct but whose `nodes.openml_wdbc.failed_criteria` is
  `["invalid_rate","keep_after_trial_1"]`, or whose `criteria.invalid_rate.observed` is 0.9, or whose `nodes` key
  is removed, is accepted by `liveness_nodes_ok`. Such a record can come only from a buggy or forged driver, and
  the record must also carry the hash-verified cluster seal (`s2_c5_switch.py:224-229`). So this is defence in
  depth, not an open path. Suggested fix: call `s2_c3b_lib.apply_declared_exception` on the gate with `pass` reset
  (the switch already imports from `s2_c3b_lib`, line 30), or at least re-check the wdbc node entry.
- **m2. A malformed `criteria` value raises AttributeError instead of a STOP.** In `apply_declared_exception`
  (`s2_c3b_lib.py:558-559`), if `criteria` or `criteria["invalid_rate"]` is a non-dict (list, float, str),
  `.get` raises AttributeError. `evaluate_liveness` (line 519-521) passes `criteria` through unchecked. This can
  happen only when the row is present, wdbc is the sole failing node and `failed_criteria == ["invalid_rate"]`.
  Then `run_liveness_job` unwinds through `finally` (server killed) without `_stop_with_evidence`, so no record
  is persisted. The result is still fail-closed (no pass), but the "shortfall evidence persists" property is lost. Fix: guard
  with `isinstance(..., dict)`.
- **m3. Coercion in `evaluate_liveness` widens what `failed_criteria == ["invalid_rate"]` means.** Line 519 does
  `list(entry.get("failed_criteria") or [])`, so a report with `failed_criteria` given as the dict `{"invalid_rate": ...}` or
  the set `{"invalid_rate"}` is accepted (verified). `r1.liveness/2` emits lists, so this is theoretical.
- **m4. The other two D28 criteria are checked for presence only, not for their values.** Line 564 checks that
  `active_novelty_fraction` and `keep_after_trial_1` keys exist, which matches the author's "evaluated" wording. But
  an inconsistent report (e.g. novelty observed 0.1 while `failed_criteria` lists only invalid_rate) is accepted
  (verified). In the real record the values are novelty 0.7 (>= 0.5) and keep 2 (>= 1). Optional hardening: require
  novelty `observed >= 0.5` and keep `observed >= 1`.
- **m5. `observed` bounds.** `0 <= observed <= 0.30` (line 561-562; switch line 191-192) also admits values that
  could never have failed `< 0.3` (e.g. 0, an inconsistent report). Because the failure itself is required, the only
  consistent value is exactly 0.3 (6/20). 0.1+0.2 (=0.30000000000000004) and 7/20 are refused, and NaN, inf, bool,
  str, None and negative values are refused. Harmless; a tighter `observed == 0.3` (or `math.isclose`) would state the
  "exactly this result" decision literally.
- **m6. The row regex is the same as the existing authority-row checks but loose about meaning.**
  `^\| R1-S2C3B-WDBC \|` (driver line 540, switch line 194) correctly needs the first cell to be exactly
  `R1-S2C3B-WDBC` with single spaces. `|R1-S2C3B-WDBC|`, `| R1-S2C3B-WDBC-2 |`, bold, indented and prose
  mentions are refused. It also matches a line inside a fenced code block and a row whose content is, say,
  "REJECTED", and it matches CRLF lines. This is consistent with how `_verify_launch` checks R1-SWEEP2-AUTH and
  similar rows (line 218-220). Acceptable; just make sure the committed row uses exactly `| R1-S2C3B-WDBC | ... |`.
- **m7. PLAN is read on every path, including 8/8.** `s2_c3b_lib.py:1339-1343` reads PLAN before the `pass`
  short-circuit. `except OSError` → `""` is fail-closed, but a non-UTF-8 PLAN would raise UnicodeDecodeError
  (a ValueError), which is not caught and would crash an otherwise-passing 8/8 job without a persisted record.
  The PLAN at main decodes as UTF-8 (checked), so this is low risk. Catching `(OSError, UnicodeDecodeError)` or
  reading PLAN only when `pass` is false would remove it.
- **m8. Docstrings and comments are now stale.** The module docstring (`s2_c3b_lib.py:6`, "no exemption"; `:12`,
  "requires all eight nodes to pass") and the comment at `:66` ("no exemption") still describe 8/8 as having no
  exception. The accepted record also carries `min_live_nodes: 8` with `live_nodes: 7, pass: true`. Nothing in
  the code recomputes pass from these, but a reader of the record could misread it, and `declared_exception`
  explains it.
- **m9. Test gaps.** The new tests are meaningful unit tests: the exact shortfall, a missing row, observed 0.35,
  a second criterion, a second node, missing criteria, a changed requirement string, 8/8 identity and no
  mutation; on the switch side, 8/8, the declared 7/8 and 8 refusals, plus a parity test asserting
  `sw.WDBC_EXCEPTION == c3b.DECLARED_EXCEPTION`. Missing: (a) the `run_liveness_job` call site (PLAN read from
  `paper/docs/r1/PLAN.md`, then the job continues to prompt measurement and persists without `stop`); (b)
  `_verify_launch` with an accepted 7/8 record; (c) NaN, str, non-dict `criteria` and real-record fixtures. The
  Python checks below cover (c) and the real record.

## Check 1: fail-closed analysis (driver `apply_declared_exception`, switch `liveness_nodes_ok`)

Driver (`s2_c3b_lib.py:543-571`): returns the input unchanged unless all of these hold: `pass` is not True; the row
is in the PLAN of the paper clone at the commit under test; `live_nodes == 7`; `failed_nodes == ["openml_wdbc"]`
(an exact list, so duplicates and reordering are refused); the wdbc `failed_criteria == ["invalid_rate"]`;
`required == "< 0.3"`; `observed` is a non-bool int/float in [0, 0.30]; both other criteria keys are present. On
acceptance it copies the dict (the input is not mutated), sets `pass: True` and records `declared_exception`
with the observed value. 8/8 returns the same object (identity is tested).

Switch (`s2_c5_switch.py:182-194`): `live_nodes == 8` → True (identical to the old `!= 8` refusal, so the 8/8
path is unchanged). Otherwise it needs `declared_exception` to be a dict, `live_nodes == 7`,
`failed_nodes == ["openml_wdbc"]`, the five keys equal to the constants (`max_observed` 0.30 survives a JSON round
trip), `observed` a non-bool number in [0, 0.30], and the row on **published main**
(`plan = git show origin/main:docs/r1/PLAN.md`, line 217). `_verify_launch` still separately requires
`gate.pass is True` (line 234).

PLAN source consistency: the driver reads PLAN from the paper clone at `spec.paper.commit`, and the switch reads
`origin/main`. `_verify_launch` requires the launch commit to descend from main and requires PLAN and the other
authority files to be byte-identical between `origin/main` and the commit (lines 213-216). C3b must run at that
same commit (`paper_commit != commit` refused, line 236). So at launch both see the same PLAN, and removing or
renaming the row on main afterwards makes the switch refuse.

Edge cases run against the code (results: True = accepted, False = refused):

| Input (row present unless noted) | Driver | Switch |
|---|---|---|
| real record, row absent | False | False |
| real record, row present | True | True |
| observed NaN / inf / "0.3" / True / None / -0.1 | False | False (NaN, str, bool tested) |
| observed 0.1+0.2, 7/20 | False | n/a |
| observed 0 (inconsistent) | True (m5) | True |
| `required` missing / "<0.3" / "<= 0.3" | False | n/a |
| `criteria` None | False | n/a |
| `criteria` list, or invalid_rate entry a float | AttributeError (m2) | n/a |
| failed_criteria duplicated / str / missing | False | n/a |
| failed_criteria dict or set {"invalid_rate"} | True (m3) | n/a |
| keep_after_trial_1 missing | False | n/a |
| novelty observed 0.1 but not in failed_criteria | True (m4) | n/a |
| wdbc pass "false" / 0, unexpected extra node | STOP (pre-existing evaluate_liveness) | n/a |
| second failing node | False | False |
| live_nodes 7.0 / True / 8.0 | n/a | True / False / True (8.0 == 8, as before) |
| declared_exception correct but nodes inconsistent or removed | n/a | True (m1) |

## Check 2: does the accepted record satisfy the rest of `_verify_launch`?

Yes. After `apply_declared_exception` (`s2_c3b_lib.py:1343`), `record["liveness_results"]` gets the accepted
verdict and `if not verdict["pass"]` does not fire. The job then runs `build_prompt_texts` / `measure_prompts` over
all 8 nodes (wdbc included; prompt measurement does not depend on liveness pass). It then runs
`cross_check_liveness_usage`, which uses the job's own ledgers (wdbc ran, so its ledgers exist; the result is
reported, not gating), then `compare_with_sweep1` (needs all 8 nodes' prompt variants, which are present), then
`_write_prompt_outputs`, `finished_utc` and `_persist`. No `stop` key is set. `seal` (line 1356 ff.) does not
inspect liveness. In `_verify_launch` (line 233-240): schema, label ENGINEERING_ONLY, `stop` falsy,
`finished_utc` set, `gate.pass is True`, `liveness_nodes_ok`, `all_fit_ctx is True`, and the commit, image,
server settings, harness and model pins are all independent of the exception. The STOP message now says "8/8 (or
the R1-S2C3B-WDBC 7/8)".

## Check 3: the real STOP record, re-evaluated

Script: `/tmp/claude-0/-home-claude/381b2f1b-01d8-56ab-a219-11b65d0f8a2d/scratchpad/chk/check.py`.
- The recorded verdict is byte-equal to `evaluate_liveness` of a report rebuilt from its nodes: `True`.
- Real verdict + PLAN at published main (no row): driver `pass False`; switch False.
- Real verdict + PLAN at main with the row appended: driver `pass True`,
  `declared_exception = {row R1-S2C3B-WDBC, node openml_wdbc, criterion invalid_rate, required "< 0.3", max_observed 0.3, observed 0.3}`.
  The JSON round-trip of the accepted verdict is accepted by `liveness_nodes_ok` with the row and refused without it.
- Real wdbc entry: `failed_criteria ["invalid_rate"]`, n_trials 20, invalid_rate 0.3 (required "< 0.3"),
  active_novelty_fraction 0.7 (>= 0.5), keep_after_trial_1 2 (>= 1). The other 7 nodes pass.

## Check 4: other gates in `sweep2/`

- `min_live_nodes` stays 8 everywhere (`s2_c2_lib.py:53`, spec validation `:259`, example and dry-run specs). C3b's
  `evaluate_liveness` still computes `pass = live >= 8`; the exception is applied afterwards. This is consistent
  (see m8 on readability).
- `s2_c2_lib.run_liveness` (`:815-862`, C2 `kind: liveness`, still requires 8) is not on the EVIDENCE launch path.
  EVIDENCE chunks (`run_job`) have no chunk-level liveness check (the only reference is `record["spec_liveness"]`,
  `:969`).
- Collection (`s2_c2_lib.py:~1060-1150`) still requires all 16 node/memory pairs, including both openml_wdbc chunks,
  with per-chunk 18-root/runtime/parse gates and the pooled worker-failure gate (wdbc counted). This fits "run all 16
  chunks". It also means a wdbc chunk failure would block collection even though wdbc is only a sensitivity row. That is a
  design consequence to keep in mind, not a defect.
- `render_jdl.py:201-205` stages `s2_c3b_lib.py` from the launch checkout (`HERE`), so the C3b job runs the reviewed
  code at the commit and reads PLAN from the clone at the same commit.
- `sweep2/dryrun/c3b/*` and `sweep2/dryrun/*` are historical dry-run snapshots that had already diverged before this
  change (e.g. `PAPER_COMMIT`). They are not staged at launch, and no test compares them with `sweep2/`. Not affected.
- `PAPER_COMMIT` in `s2_c3b_lib.py:54` is unused, so it puts no constraint on the new launch commit.
- Nothing found that blocks a 16-chunk launch at the code level. See P-1 for the authority text.

## Check 5: tests

- `AR_HARNESS_ROOT=.../scratchpad/harness_a3fedbb python3 -m pytest -q -p no:cacheprovider r1/tests/htcondor` at
  31ae7ad4: **396 passed** in 2.05 s (0 failed, 0 skipped, 0 errors).
- The subset `-k "wdbc or liveness_nodes_ok or same_exception"` gave **19 passed** (the new tests: 1 + 5 + 1 + 1 + 1 in
  `test_s2_c3b.py`; 1 + 8 + 1 in `test_s2_c5_switch.py`).
- The full suite was not run (it is run separately). The `/tmp/r1_c3_*` and `/tmp/c3_audit_tmp_*` folders present
  at the end of this review (timestamps 23:53-23:55) predate my htcondor run (about 23:56). They belong to the concurrent full-suite run,
  whose command line removes them when it finishes, so I left them in place to avoid breaking that run. My
  htcondor run created none.

## Recommendation

Merge the code with the R1-S2C3B-WDBC row, written exactly as `| R1-S2C3B-WDBC | ... |`. The row should explicitly
amend R1-SWEEP2-AUTH's "8/8" and the authorization note's "liveness < 8" STOP for exactly this shortfall (P-1).
Optionally address m1 (re-derive in the switch) and m2/m7 (non-dict criteria, decode errors) before the C3b rerun.
None of the minors lets a different shortfall through in practice.

Code-Commit: 31ae7ad46c8d4ac44b897c0852781af0a921fba1
Verdict: ACCEPTED WITH MINORS
