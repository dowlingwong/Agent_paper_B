# D.3 G1 final snapshots — independent tier-E review (compute/20261127-20)

**Reviewed source:** `292cde9787750436a5ee769ed78982aa3b3cedbc` on `compute-d3-g1-final-20261127`;
base `c4250f7ea26a97e0f3c7b475613287864110a14c`. Harness `9bb416805175149eb87b71f28d77530572aa4bce`.
**Reviewer:** a fresh independent tier-E reviewer, 27 Nov 2026. Synthetic/read-only checks only; no real campaign,
audit, label read or GPU job was run.

**Verdict: ACCEPTED.** Both blocking findings of the revision-4 step-(5) review
(`docs/r1/reviews/D3_PREDECL_R4_STEP5_REVIEW_20261127.md`) are fixed on the harness and replicate routes. The four
conditions of `compute/20261127-04` are preserved. No code change is required. The minor findings were documentation
and evidence wording/variance (F1, F2, F5) and were addressed in the `2d014725`/`ff244366` re-checks; F3 remains
informational and F4 is documented.

**Branch note.** The assigned tip is `292cde97`. At review time the remote branch
`origin/compute-d3-g1-final-20261127` had advanced one doc-only commit to
`72cbd96f2060f6225e150e90f6e25ba981e6c454` ("full-suite failure id list"); `git diff 292cde97..72cbd96f` touches
only `docs/r1/reports/d3_g1_20261127/FULL_SUITE_FAILURE_IDS_20261127.txt`. The code bytes at both commits are
identical, so this review applies to both. The review branch was created from `292cde97` as instructed. The task
branch later advanced through doc-only `2d014725` (review minors) and `ff244366` (F2 sorting/hash wording); §§11–12
re-check those. The code hashes are unchanged from the reviewed docstring version (`5241dcc0…`, `4131ffcc…`,
`c57926a4…`).

## 1. Diff and scope

`git diff --name-status c4250f7e..292cde97`:

```
A	docs/r1/reports/d3_g1_20261127/D3_G1_FINAL_SNAPSHOT_20261127.md
M	r1/c3/d3/campaign_chunk.py
M	r1/c3/d3/snapshots.py
M	r1/tests/test_d3_g1_snapshots.py
```

No G6, G7 or analysis file changed. SHA-256 at the tip:

| File | sha256 |
|---|---|
| `r1/c3/d3/snapshots.py` | `c55a26bc75bc919800d4539cb96c64a29604d5454cc500c71e72bd52415e1267` |
| `r1/c3/d3/campaign_chunk.py` | `4131ffcc6946e5fd156ea159e44c466fed8b6de8d3a2e0b88731898976f96f1c` |
| `r1/tests/test_d3_g1_snapshots.py` | `c57926a438811e9042af0d2adbed4bcebc11c2d5e270b3d1d2e0d851a1c41ef5` |
| `r1/c3/d3/audit.py` | `452724ec92b9820ddfb187f2ea4999f3c0bbc6c1241b55f4594b8a4b0cd5a4a3` (same at base) |
| `r1/c3/d3_outcome_table.py` | `a9ce5d904c711642932c4b393f2d1f52e00e7f59e1f6d20cd1ea530fd7fba3ca` (same at base) |
| `r1/c3/d3_analysis.py` | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` (same at base; the value pinned in §§9/14) |

The three report hashes in `D3_G1_FINAL_SNAPSHOT_20261127.md` were reproduced exactly. `git diff --check` is clean;
the worktree is clean.

## 2. Blocking finding 1 — the harness terminal keep

The wrapper now calls `SnapshotRecorder.write_final_live(...)` after `run_real_campaign` (`r1/c3/d3/campaign_chunk.py`).
It reads the live editable files through the `CountingWorker` (`read_worker_config(worker, node_spec)`), takes the
last kept `budget_index` from the ledger, and uses the post-decision controller hash stored by `RecordingController`
after the last E1/E2 decision. The old `write_final` refuses at `w>0`; it still writes the historical `w=0` record.

I ran the `REPRODUCTIONS.md` harness script on the base with `write_final`, and the same script on the tip with
`write_final_live` (replacing

```python
rec.write_final(w_final=rec.count, ended_on=ended_on)
```

with

```python
rec.write_final_live(w_final=rec.count, ended_on=ended_on, worker=kwargs["worker"],
                     node_spec=kwargs["node_spec"], ledger_path=records_path)
```

). Command (from the respective checkout; `$H` is the pinned harness, `$D3VENV` the Python 3.12.8 / pytest
9.2.0 environment):

```
H=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb
D3VENV=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv
AR_HARNESS_ROOT=$H PYTHONPATH="$PWD" $D3VENV/bin/python -B repro_harness.py
```

with the reproduction body copied from `REPRODUCTIONS.md` into `repro_harness.py` in the review scratch directory.

| End condition | Base: ledger last keep | Base: final last kept | Base: live hash | Base: recorded hash | Tip: final last kept | Tip: live = recorded |
|---|---:|---:|---|---|---:|---|
| worker-run cap W=20 | 20 | 19 | `4b1b4f8dcc271f804508a0e122a570b3f3c14b78527b849ac50eeb69eb414cfb` | `a12ae00c87ecb01463f2b10a59e7699166f10523f58d38b5f983c4c3adfa9185` | 20 | yes, `4b1b4f8d…` |
| LLM-call cap at 7 | 7 | 6 | `a12ae00c87ecb01463f2b10a59e7699166f10523f58d38b5f983c4c3adfa9185` | `4b1b4f8dcc271f804508a0e122a570b3f3c14b78527b849ac50eeb69eb414cfb` | 7 | yes, `a12ae00c…` |

The base `alias_of` was `w20.json` in the W case and absent in the early-cap case; the tip final has no `alias_of`.
This reproduces the blocking review's exact hashes and reverses them at the early cap, as reported.

At W the tip writes `w20_pre.json` with `pre_decision: true`, `superseded_by: "final.json"` and the pre-decision
config, and rewrites `w20.json` from the final with `final: false`, `ended: false`, no `ended_on`, and
`canonical_final: "final.json"`. In the keep-at-20 trace the canonical `w20` config equals the final
(`4b1b4f8d…`) and `w20_pre` carries the pre-decision `a12ae00c…`.

I also checked the terminal-discard case with a synthetic worker whose last metric is worse, so the last ledger
decision is `discarded`: the live final, canonical `w20` and `w20_pre` all carry the last kept (trial 19) config
`a12ae00c…`, and `last_kept_trial_index` is 19. That is the correct terminal incumbent, and it shows the
canonicalisation is not conditional on a keep.

## 3. Blocking finding 2 — the replicate at-W pair

The replicate route's engine already supplied the post-decision `incumbent_config`; `_write_final_payload` now
canonicalises the at-W record exactly as on the harness route: the pre-decision `w20.json` is preserved as
`w20_pre.json` and `w20.json` is rewritten from the final. The updated
`test_replicate_final_is_separate_from_w20_and_carries_the_last_keep` passes and asserts:

- `w20.json.incumbent_config == post`, `config_sha256 == config_sha256(post)`, `canonical_final == "final.json"`;
- `w20_pre.json.incumbent_config == pre`, `pre_decision is True`, `superseded_by == "final.json"`;
- `final.json.incumbent_config == post`.

I also ran the actual EGATE replicate loop (`EgateEngine`, synthetic metrics, rising so the gate commits) to
`worker_runs = 20`, `ended_on = worker_runs`. It wrote `w20.json` and `w20_pre.json`; the canonical `w20` and final
configs are equal (`cc36d7aea5d52dfb58733d409544e4034f4a3e80108ed62167bd6c6aeee80879`), and the pre record has
`pre_decision: true`. This exercises the production `write_final_from_state` call, not only the recorder-level test.

For the record, the old replicate failure still reproduces on the base: the synthetic EGATE fixture gives
`w20 y_raw = 0.4999999999999999`, config `13a9c57235d3e70ce8c81ae67fcda9a880b63e56a129d17b7bef2614349c3926`, and
`final y_raw = 0.7`, config `6ee4cb3803c068ae990fb5c2691cb6fbd4861dad2750904622bd2968698fafb5`; G7 refuses with
“at w = 20 the snapshot audit is the final audit (one canonical audit)” and `d3_analysis.validate_table` refuses
with “y_raw_w at w = 20 must equal y_raw”. The tip removes the pair by construction.

## 4. G6, G7 and analysis see one Y(20)

G6 reads exact names (`w{5,10,15,20}.json`, `final.json`) and ignores `w20_pre.json`; that is unchanged. On the tip's
real harness W=20 campaign, G6:

- audited `w20` and final with `config_sha256 = 4b1b4f8d…` and `y_raw = 0.11574793274415374`;
- set `final.alias_of_w = 20` and `final.audit_record = a/A0/r0/w20/digits_mlp__s6201.json`, so it ran one audit,
  not two;
- G7 `build_row` accepted the row with `y_raw_w["20"] == y_raw`; and a `synthetic_table()` row carrying the same
  values passed `d3_analysis.validate_table(complete, "D.3a")`.

This is the design's alias rule applied to the post-decision final, and it preserves the G7/analysis equality at W.

## 5. Edge cases checked

| Case | Result |
|---|---|
| `w=0` harness final | `write_final_live(0, ended_on="no_fundable_candidate")` writes the start config, `last_kept_trial_index=None`, `worker_runs=0`; no canonicalisation. |
| no keep at all, `w>0` | ledger rows all `discard`; `last_kept_trial_index=None`; final config is the live start config. |
| keep on the final trial | final carries the live kept config; canonical `w20` equals final; `w20_pre` differs. |
| discard on the final trial | final carries the last kept (trial 19) config; canonical `w20` and `w20_pre` equal it by definition. |
| `ended_on="error"` at W | at-W canonicalisation is skipped; `w20.json` remains the pre-decision record and no `w20_pre.json` is created. The final is still the live config. This is fail-closed: G7 would refuse a W/error row whose `w20` and final differ, rather than audit a wrong Y(20). |
| charged-run parity | `write_final_live(w_final=19)` with `count=20` raises `SnapshotParityStop`; `run_chunk` still checks `recorder._last_budget.worker_runs == w_final` before the final. |
| `write_final` at `w>0` | refuses with `SnapshotStop` (“a final at w>0 needs the live incumbent and ledger; use write_final_live”). |
| `start_config` | final and canonical `w20` carry the same non-empty start config; G6's `load_snapshot` accepts both. |
| controller state | exact-w snapshots still use the E1 state (`test_verify_snapshots_keep_the_e1_controller_state` passes); the final and canonical `w20` use the post-decision E1/E2 hash; `w20_pre` keeps the exact-w E1 record. |

The `w20_pre` record is not literally byte-for-byte the old `w20`: the writer adds `pre_decision` and
`superseded_by` before writing it. The pre-decision *payload* (config, hashes, timestamp, pending state) is
preserved, but the original `w20` file bytes and full-file digest are not retained. Measured on a fresh W run:
original `w20` sha256 `409941f698ca39dad78ef834856aef8e5138b0ced0f131fd96ec97edf4244a66`, `w20_pre` sha256
`587dbd7a21877a8d2c7c7632200d26f8a983cf5d8b905f8bdbfc3f531dcef7a2` (extra keys `pre_decision`,
`superseded_by`), canonical `w20` `7467487601d55925507a5d3ad29fd7a9c656320c7af9ee1d5dc3bd1b151189c8`. Semantically
the pre record is distinct and replayable; the report's “byte-for-byte” wording is the only defect here (F1).

## 6. The four conditions of `compute/20261127-04`

1. **Count parity.** `ParityBudget`, `CountingWorker` and `note_run` are unchanged. `check_parity` runs at every
   hook/charge, `run_chunk` checks the end-of-campaign budget parity, and `write_final_live` checks
   `w_final == recorder.count`. Focused tests `test_hook_parity_is_checked_at_every_hook`,
   `test_parity_stop_on_block_charge`, `test_parity_budget_fails_closed_without_a_wrapper_count` and the chunk
   tests pass.
2. **Only budget-charged runs.** The counting worker is unchanged; a rules skip charges no run
   (`test_skip_charges_no_worker_run` passes), and no new charge/counter is introduced.
3. **E1 controller state / no extra controller call.** The exact-w records keep the E1 state and `note_run` still
   asserts the controller-call count (`test_verify_snapshots_keep_the_e1_controller_state`,
   `test_recording_controller_reports_action`). The canonical `w20` is the post-decision final alias, not the
   preserved exact-w record; `w20_pre` carries the E1 state. No controller call is added between an E1 hook and a
   run. This is the intended exception required by finding 1: the final (and its at-W alias) is post-decision, as
   the replicate final already was.
4. **Independent review.** This review confirms that reading explicitly: condition 3 is preserved for the exact-w
   records (including the preserved `w20_pre`); the canonical `w20`/`final` are the post-decision terminal record.

## 7. Tests run

Focused modules at the tip, with the pinned harness:

```
AR_HARNESS_ROOT=$H PYTHONPATH="$PWD" $D3VENV/bin/python -m pytest -q \
  r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py \
  r1/tests/test_d3_g1_replicate.py r1/tests/test_d3_adapter.py \
  r1/tests/test_d3_audit_g6.py r1/tests/test_d3_outcome_table.py \
  r1/tests/test_d3_analysis.py r1/tests/test_d3_verify_namespaces.py
```

**161 passed, 18 subtests passed** (7.05 s). The six modules named in the task without the adapter/namespace pair:
**141 passed, 18 subtests passed** (5.21 s). This matches the report's focused count.

Full suite:

```
AR_HARNESS_ROOT=$H PYTHONPATH="$PWD" $D3VENV/bin/python -m pytest -q r1/tests
```

My rerun at the tip: **114 failed, 4,985 passed, 163 skipped, 3 errors, 71 subtests** (695.93 s). The
117 `FAILED`/`ERROR` ids are a strict subset of the base log's 120 ids: three base-log failures passed in my run
(`test_b1_real_worker_determinism.py::test_b1_real_worker_run_is_seed_deterministic`,
`test_c3_audit.py::test_real_worker_run_is_seed_deterministic`,
`test_rerun2_batch4c.py::test_dryrun_start_refuses_external_batch_before_log_write`), and all three pass
individually in 3.80 s. No new failure id appears at the tip, so the unit's “zero new failures” claim holds. The
report's exact tip count (117 failed / 4,982 passed) and its stronger “identical 120 ids” wording were not
reproduced; the difference is three baseline failures that did not reproduce, not a D.3 change (F5).

The base full-suite log at `9bb41680` (`/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/g1base_full.log`)
reports **117 failed, 4,980 passed, 163 skipped, 3 errors, 71 subtests**, with 120 `FAILED`/`ERROR` ids. The reviewed
report's 120-line failure file at `72cbd96f` has file sha256
`e4ac065fe75186c26e8ecfa283b8d8d37753bc9a2196b0857fe9ddd110d99164`; its sorted id set is identical to the base
log's 120 ids (sorted-id-list sha256
`c95419f6470cc13c35582cdbf7dfa0a81c355b9525b602b1b4dd2e64ba7f4bfa`). The report's phrase “the 120 sorted
FAILED/ERROR ids … sha256 e4ac…” is the hash of the whole 120-line file, not of the newline-joined id list; that
wording is minor (F2). An earlier tip log (`g1final_full.log`, 09:02) had two extra T1 failures, both
`~/r1_locks/gpu0.lock held by another job` GPU-lease contention, not a code difference.

## 8. Evidence, labels and sealed files

The diff contains no evidence, label, evaluation, sealed-partition, results or data path. The review's synthetic
runs used a temporary copy of the `digits_mlp` node, `ConfigMetricWorker`/`ImprovingWorker`, `ScriptedManager`,
`FakeRunner` and synthetic tables; no sealed file, label, evaluation value or real campaign was read. The unit's
own code path is ENGINEERING-only. G6/G7/analysis bytes are unchanged from the base.

## 9. Findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| F1 | LOW (documentation) | The report says the pre-decision `w20` is preserved “byte-for-byte” as `w20_pre.json`; the writer adds `pre_decision` and `superseded_by`, so the bytes and full-file digest differ. The payload and replay semantics are preserved. | `_write_final_payload` adds both keys; measured original/pre/canonical sha256 `409941f6…` / `587dbd7a…` / `74674876…`. |
| F2 | LOW (evidence wording) | At reviewed commit `292cde97`, `FULL_SUITE_FAILURE_IDS_20261127.txt` is the stale adapter-base list (111 ids, file sha256 `aedf99f5…`), not the 120 ids cited in the report. The doc-only `72cbd96f` replaces it with the 120-line list (file sha256 `e4ac065f…`); the sorted id set matches the base log. The report's “sha256 of the ids” is the file hash, not the id-list hash (`c95419f6…`). | `git show 292cde97:…FULL_SUITE_FAILURE_IDS…`, `git show 72cbd96f:…`, `shasum -a 256`. |
| F3 | INFO | The canonical `w20.json` carries the post-decision controller hash, while the exact-w E1 state is in `w20_pre.json`. This is consistent with “the final governs” but changes what a consumer reading only `w20.json` sees for controller state; replay should read `w20_pre.json`. | Code and the W-run snapshots. |
| F4 | INFO | At `ended_on="error"` the at-W canonicalisation is skipped; a W/error row with differing `w20`/final would be refused by G7. This is fail-closed and produces no incorrect audit, but it is not documented in the report. | `_write_final_payload` condition `payload.get("ended_on") != "error"`; synthetic error case. |
| F5 | LOW (evidence variance) | The report's exact tip full-suite count (117 failed / 4,982 passed) was not reproduced; my run gave 114 failed / 4,985 passed / 163 skipped / 3 errors. The 117 failure ids are a strict subset of the base 120, and the three base failures that passed also pass individually, so there is no new tip failure. | `tip_full.log`; `diff base_old.ids tip_new.ids`; the three tests pass in 3.80 s alone. |

No finding touches the two blocking findings or the four conditions. F1, F2 and F5 are documentation/evidence only;
F3/F4 are informational.

## 10. Verdict

**ACCEPTED.** The harness route now records the live terminal incumbent, including a keep on the final trial, and
the replicate route's at-W record is canonicalised to the post-decision final while preserving the pre-decision
record. Both blocking findings are resolved; G6 audits one Y(20), G7 and the pinned analysis see `Y(20) = final`,
and the four conditions of `compute/20261127-04` hold. F1, F2, F4 and F5 were addressed in the two re-checks; F3
remains informational. No code change is required.

No D.3 evidence job was run for this review. The pre-declaration can proceed to the local worker's step (5)
repetition.

## 11. Minor findings re-check (task tip `2d014725`)

Re-checked `2d0147253dd5f4a649ca2e8ec37ad1c21a324a22`. The code diff from the reviewed `292cde97` is the docstring
only: `r1/c3/d3/snapshots.py` has 4 removed / 4 added lines inside `_write_final_payload`; `campaign_chunk.py` and
`test_d3_g1_snapshots.py` are byte-identical. The new `snapshots.py` sha256 is
`5241dcc079f606582a8e9233886a51d93b656aef3362571b4898c9ab748819a2`, matching the report. Focused tests at
`2d014725`: **36 passed** for the three recorder/chunk/replicate modules and **161 passed, 18 subtests** for the
eight D.3 modules. The adapter failure-id file is byte-identical to base `c4250f7e`
(`aedf99f598b2c5b35ebdc74a19529513971622c1227f85e7a0925982131e32ef`, 111 ids).

| Finding | Status | Re-check evidence |
|---|---|---|
| F1 | **RESOLVED** | The report and the `_write_final_payload` docstring now say the pre-decision payload is unchanged “apart from the two provenance fields `pre_decision` and `superseded_by`”. This matches the measured writer behaviour (original/pre/canonical sha256 `409941f6…` / `587dbd7a…` / `74674876…`). No byte-for-byte claim remains. |
| F2 | **PARTIALLY RESOLVED — one claim is still wrong** | The restored `FULL_SUITE_FAILURE_IDS_20261127.txt` is exactly the base bytes `aedf99f5…` (111 ids). The new `FULL_SUITE_FAILURE_IDS_FINAL_20261127.txt` has 120 ids and its id set equals the base 120, so the list content is correct. However, the file header states only the id-list hash, not its own file sha; its own file sha256 is `a07721cbe70eeb2ba2535a3eae18d9d68c16b94f6c4bc3fb539b7486fe6bbc36`, not the stated `9b0350c2…`. The stated `9b0350c2…` is the hash of the newline-joined ids **in file order with a trailing newline**; the sorted id list hashes to `03339eb10919c3772e705195d5dc37cdee44a38d76ebaa5be1acd10f74d02977`, and the file order is not sorted (e.g. `test_c3_sweep_dryrun…` precedes `test_c3_sweep2_audit…`). The report calls `9b0350c2…` the file's sha256 and the 120 ids “sorted”; both statements are inaccurate. The 120-id set itself is correct. |
| F3 | **INFO, unchanged** | Canonical `w20.json` carries the post-decision controller hash; the exact-w E1 state remains in `w20_pre.json`. No action required; replay should read `w20_pre.json`. |
| F4 | **RESOLVED (documented)** | The report now records that `ended_on="error"` skips at-W canonicalisation and that this is fail-closed; this matches the code. |
| F5 | **RESOLVED IN SUBSTANCE; wording still loose** | The report now gives the serial 117 failed / 4,982 passed run and my independent 114 failed / 4,985 passed rerun, says no new id appears, and no longer claims an identical 120-id set. My rerun's 117 ids are a strict subset of the base 120, and the three non-reproducing base failures are named. Remaining nit: “the 120 sorted … ids at the tip are a subset of the 120 at the base” is non-strict (the serial sets are equal) and “sorted” is false under F2; “the two extra passes over the base are the new tests” applies to the serial run, not to my +5 rerun. |

**Re-check verdict at `2d014725`: the verdict stayed ACCEPTED WITH MINOR.** The code behaviour and both blocking
fixes remained correct, and F1/F4 were cleanly resolved. The F2 fix was substantively right but its file-sha and
“sorted” claims were still wrong; F5 was substantively right but retained loose wording. These were
evidence/documentation only and needed no code change. §12 supersedes this after the F2 correction at `ff244366`.

## 12. F2 re-check (task tip `ff244366`)

Re-checked `ff244366b7168a210a302b37deda5438f83c9e6e`, parent `2d014725`. The only changes from `2d014725` are the
two doc files; the code hashes are unchanged from the reviewed docstring version:
`r1/c3/d3/snapshots.py` `5241dcc0…`, `r1/c3/d3/campaign_chunk.py` `4131ffcc…`, test `c57926a4…`.

- `FULL_SUITE_FAILURE_IDS_FINAL_20261127.txt` is now `LC_ALL=C` sorted: 120 ids, `body == sorted(body)`, first
  `test_b1_real_worker_run_is_seed_deterministic`, last `test_the_tables_diffs_enter_the_proposal`.
- Its file sha256 is `811be7a90113d4c76025d0a6246da51ec1a958fd3c753b750011114584a073a3`, matching the report.
- The newline-joined **sorted** id-list sha256 (with trailing newline) is
  `03339eb10919c3772e705195d5dc37cdee44a38d76ebaa5be1acd10f74d02977`, matching both the file header and the report.
  The 120-id set equals the base 120.
- The report now cites the file sha and the id-list sha separately, calls the tip set the **same set** as the base's
  120, and describes my 117-id rerun as a strict subset of that base set. That wording matches the artifacts and the
  two suite runs.

**F2 is RESOLVED.** F1, F2 and F4 are resolved; F5 remains resolved in substance (the §11 “two extra passes”
wording nit is cosmetic and does not affect the result); F3 remains informational. **Final verdict: ACCEPTED.**
