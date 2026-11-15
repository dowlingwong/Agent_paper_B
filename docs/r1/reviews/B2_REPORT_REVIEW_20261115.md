# B2 report — STOP 6 independent review (recomputation from the §6 hand-back)

**Reviewer role:** independent, read-only STOP 6 reviewer (not the author, not the operator, not the
author of the B2 units). No SSH, no host command, no unit execution, no git write; only this review file
was written. All hand-back artifacts are in the repo; the report is
`docs/r1/reports/b2_exec_20261115/B2_REPORT_20261115.md`, the hand-back is
`docs/r1/reports/b2_exec_20261115/handback/`, and the start/completion record is
`B2_START_RECEIPT.md` (+ its completion section).

**Reviewed at** pinned exec commit **`486f7bc7`** on `ops-b2-exec-20261115` (= origin); run HEAD
**`8709dce792d45bbb5c05d9f7d239e19454efbb15`**; run ID `8709_20261115_b2`; phase b2 under x5_rule/v2
(rule SHA-256 `53018aa7…`). Hand-back SHAs verified against the Lead's list: `analysis.json`
`de110ca6…`, `b2_manifests.json` `1c8d0e57…` (494,573 B), `batch_state.json` `f09b78be…`,
`invalid_trials.json` `a0d3a0a1…`, `marker-retirement.json` `1ca0b35a…`, `trks_stop_before_after.txt`
`fe93edc3…`, `watch.log.tail.txt` `b41a3563…`. STATUS branch `mac-b1-20261107` @ `78afa073` = origin
(parent `524f0a8a`); the Mac status checkout is at `78afa073`, clean.

**Review verdict in one line:** the B2 result tables recompute exactly; the run's normal completion,
marker retirement, STATUS publication and watcher stop check out; the report has material data-quality,
open-item and hand-back-completeness errors that must be corrected before the author's X.7 decisions.

## 1. Recomputed result (from the hand-back manifests)

`b2_manifests.json` is the candidate aggregate (label `EXAM`): one finalist, `gemma4_31b` (bartowski
imatrix Q4_K_M; model SHA-256 `2959c1b0…`), 24 `root_manifests`, 12 primary (mode off) final audits and
12 thinking-on (mode on) descriptive final audits, each with the 10 audit seeds 9201–9210. Recomputing
from the aggregate's `final_audits`/`sensitivity_final_audits` and cross-checking the analysis:

| table | recomputed | report | match |
|---|---|---|---|
| primary (off) final_y | 0.9402810083333333 (mean of the 12 instance means; 120 audit metrics) | 0.9402810083333333 | yes |
| primary instances | 12 = 3 nodes × seeds 9011–9014 | 12 | yes |
| per-node primary | digits_mlp 0.972632275; openml_credit_approval 0.925997225; openml_ionosphere 0.922213525 | not tabulated | — |
| descriptive (on) final_y | 0.9552304833333333 (12 instances, 120 metrics) | 0.9552304833333333 | yes |
| per-node descriptive | digits_mlp 0.973189275; openml_credit_approval 0.93551705; openml_ionosphere 0.956985125 | not tabulated | — |
| selection | gemma4_31b, primary off, rule top, schema-sensitivity rows none | same | yes |
| grid verification | `verified: true`; finalist gemma4_31b; nodes digits_mlp/openml_credit_approval/openml_ionosphere; 4 instances/node; seeds 9011–9014; modes [off, on]; audit seeds 9201–9210 | same | yes |
| batch state | `COMPLETE`, 24/24 completed, interruptions `[]`, 2 server intervals (off, on) | COMPLETE, 24/24, 0 interruptions, 2 intervals | yes |
| proposal-journal invalid | `rejected_by_check = {}`; 24 roots, 24 journals, 480 rows | same | yes |
| candidate diagnostics | trials 480, evaluated 480, **invalid 58**, duplicates 82, noops 58, parse_failed 0, forecast 480/0 | not stated | **no (F1)** |
| GPU hours | analysis/grid `gpu_hours` 0.5049170030487908; manifest `total_gpu_hours` 4.6106076256434125 (dedicated server wall intervals incl. load/audit) | 0.5049170030487908 ("≤10 GPU-h round cap") | partial (F2) |
| labels | `execution_label: EVIDENCE`, `author_decision_pending: true`, descriptive not a selection row | same | yes |

The analysis's own consistency checks hold: `batch_verification.batch_state_sha256` = `f09b78be…` and
`batch_manifests_sha256` = `1c8d0e57…` (both match the hand-back files), `authorization_checkout_head` =
`8709dce7…`, `b1_analysis_sha256` = `07cb62de…`; `stage_a_pass: true` (source `a1_amendment_measurement`),
`d28_pass: true`, `cache_prompt: false` for all 24 roots, `thinking_on_rerun: descriptive`,
`thinking_on_d28: {pass: false, roots: 12, role: descriptive_never_changes_eligibility}`.

## 2. Findings

Severity: BLOCKING (report cannot go to the author) / MAJOR (material data-quality or open-item error) /
MINOR / NIT.

### MAJOR

- **F1 — "invalid trials none" under-discloses the candidate-level diagnostics.** The hand-off's
  invalid-trial table is the proposal journal (`proposal_journal.rejected_by_check`), which is correctly
  empty (24 roots / 24 journals / 480 rows). But the hand-back's `b2_manifests.json` records
  `diagnostics = {trials: 480, evaluated: 480, invalid: 58, duplicates: 82, noops: 58, parse_failed: 0,
  forecast_queries: 480, forecast_query_failed: 0}`. The report's Section 4 says "zero rejected trials
  (no invalid-trial classes to report)" and the headline says "invalid trials none" without the 58
  campaign-level `failed_invalid` decisions (and the 82 duplicates / 58 noops). Fix: add a data-quality
  note that separates the proposal-journal table (empty) from the campaign diagnostics (invalid 58,
  duplicates 82, noops 58, parse_failed 0), with a one-line definition of each (`invalid` =
  `decision == failed_invalid`; not the proposal-journal rejection classes). The result table itself is
  correct, but the omission is material for the author's X.7 reading.
- **F2 — the "GPU hours" claim uses the selection metric, not the round total.** The analysis/grid
  `gpu_hours` is 0.5049170030487908 (the candidate's `gpu_hours`, method
  `dedicated_server_wall_intervals_including_load_and_audit`; the manifest's `total_gpu_hours` is
  4.6106076256434125, i.e. the 24-root total incl. the descriptive run). The report's "GPU hours
  (finalists) 0.504917 h (well below the ≤10 GPU-h round cap)" therefore understates the round's GPU
  hours by ~9×. Both are below 10, so the cap statement is true for either number, but the number shown
  is the selection/tie-break metric, not the round total. Fix: state both (selection `gpu_hours`
  0.504917; round `total_gpu_hours` 4.6106) and use the total in the cap sentence.
- **F3 — the TASL-2 open item contradicts the completed census.** The report's open item says "TASL-2
  read-only inventory — still blocked: `portal_zhixu` (100.120.160.70) offline …, the reviewed unit is
  ready". The same exec commit contains the accepted census: `trks_stop/tasl2_census_20261115/` with
  `request.txt` (2026-11-15T21:11:14Z), `reachability.rc` = 0, `inventory.rc` = 0, the 152-line
  inventory (host TASL-2, user dowling), and `TASL2_READONLY_CENSUS_REVIEW_20261115.md` final
  **Verdict: accepted**; the deferred bare-repo fast-forward was executed at 21:19:18Z
  (`tasl2_bare_push_receipt.txt`: 52-commit fast-forward, no force). Fix: replace the open item with the
  actual state (census complete and accepted; the only TASL-2 action was the deferred bare-repo
  fast-forward; nothing resumed, no lock released; no further TASL-2 use).

### MINOR

- **F4 — timeline time-zone error.** The report's Section 2 is headed "(UTC)", but the outage row copies
  the `MONITOR_INCIDENT_20261115.md` times, which are **CET**: 21:34–21:47 CET = 20:34–20:47 UTC (during
  the run, between 21 and 22 roots), and the incident's "last confirmed state 21:22 CET" (20:22 UTC,
  RUNNING 21/24) is not the report's 21:22 UTC run end. The "did not affect the runner" conclusion is
  correct (the runner continued; 22/24 at 21:50 CET, 20:50 UTC). Fix: label the outage row CET or convert
  to UTC (20:34–20:47) and note it occurred during the on-mode run.
- **F5 — hand-back completeness for "recompute every table".** The hand-back's `b2_manifests.json` is the
  candidate aggregate (1 manifest, 24 root paths), not the 24 root `campaign_manifest.json`s; the
  proposal-journal table can be cross-checked against the aggregate (24 roots / 480 trials / `{}`), but
  the 24 root journals are not in the hand-back, so the invalid table is verified only against the
  aggregate counts and the `invalid_trials.json`, not recomputed per root. Similarly the stop's
  `manifests.diff`/`stops.diff`/`stop_receipt.txt` and the collect's `POSTRUN_COLLECT_OK`/`analysis.rc`/
  `b2.exit` are not in the hand-back (only the summary `trks_stop_before_after.txt` and the four end
  artifacts). Fix: include (or record the SHA-256 of) the root manifests/journals (or the per-root
  `proposal_journal` aggregate), the stop receipt + sorted scene diffs, and the collect-ok/analysis.rc/
  b2.exit receipts, so the STOP 6 statements are fully recomputable from the hand-back alone.
- **F6 — review-count summary is imprecise.** The report's Section 3 says "occupancy/launch review rounds
  1–11 final ACCEPTED; post-run unit rounds 9–11 final ACCEPTED"; the actual series are occupancy/launch
  rounds 1–8 (final accepted), post-run unit rounds 9–11 (final round 11 accepted; the coordination's
  round-12 post-run bytes accepted), STOP4 units rounds 12–13 (round 12 not accepted on the earlier
  bytes; round 13 accepted for the current units; the coordination's round-2 final accepted), TASL-2
  census accepted, run-HEAD review accepted. The "all final ACCEPTED in their final rounds" statement is
  true for the final rounds; the lists overlap and should be corrected.
- **F7 — STATUS placement.** `78afa073` = origin and the content is correct (`## 2026-11-15 — Track X B2
  running` at `524f0a8a` and `## 2026-11-15 — Track X B2 done` at `78afa073`), but the two B2 entries are
  appended at the **bottom** of `docs/r1/STATUS.md`, below the older B1 entries; the file's convention is
  newest first (the 14 Nov B1 entry is still at the top). Note the placement (or prepend on future
  publications); the commit/remote/no-force checks are satisfied.
- **F8 — the thinking-on descriptive D28 status is not mentioned.** The candidate manifest records
  `thinking_on_d28: {pass: false, roots: 12, role: descriptive_never_changes_eligibility}`; the report
  correctly says the thinking-on rerun is descriptive only and not a selection row, but the Section 4
  data-quality note should mention the descriptive D28 false (it does not change eligibility, but it is
  part of the descriptive record).

### NIT

- **F9 — the marker-gone analysis's "full script" omits two comment lines** (`# run as: tmux new -d -s
  trks_watch …` and `# LLM collectors only`); the code body matches the reviewed census SHA
  `cf68843e…`; the coordination's round-2 review m-20 notes the same. Cosmetic.
- **F10 — Section 5's HTCondor image-v2 item** is outside the B2 data/STOP 6 scope (an exec-branch CI
  item); keep it, but label it as out-of-scope for the B2 result review.

## 3. Receipts, ordering, no-deletion/no-retry

- **Normal completion:** batch_state `COMPLETE`, 24/24 completed, interruptions `[]`, 2 server intervals
  (off then on); the report's 21:22 UTC end is consistent with the on-mode interval end and the hand-back
  `b2_manifests.json` (494,573 B); the `b2.exit`/`POSTRUN_COLLECT_OK`/`analysis.rc` receipts are not in
  the hand-back (F5) but the analysis's `batch_verification` SHAs bind the hand-back batch_state and
  b2_manifests.
- **Marker retirement:** `handback/marker-retirement.json` = `{dev 66306, ino 56261620, sha256
  "4ecb2779…", retired "trackx_evidence.active.2109cd07…", run_id 8709_20261115_b2, head 8709dce7…}`;
  the marker is absent; the retirement is a move into `_to_delete` (no deletion); the stop summary
  records `marker_retirement_sha256=1ca0b35a…`, matching the hand-back file.
- **STATUS:** `78afa073` = origin, parent `524f0a8a`, no force, the B2 done heading present (F7
  placement).
- **Watcher stop:** `trks_stop_before_after.txt`: stop requested 21:26:05Z (after the marker retirement),
  watcher before `1388760 bash …/trks-watch` + `trks_watch pane=%0 pane_pid=1388760 cmd=bash`, watcher
  script SHA `cf6884…`, no Track S collectors/llama, no GPU compute, `WATCHER_GONE` after; the stop's
  sorted scene diffs/receipt are not in the hand-back (F5). The watch.log tail shows the B2 pause
  (`16:28:39Z priority marker seen`), the marker-gone line (`21:24:39Z`), and the earlier drill line
  (`2026-11-14T22:23:37Z`), consistent with the reviewed marker-gone analysis.
- **No-deletion/no-retry:** no file deletion in the retirement/stop path; the batch is read-only for the
  collect/analysis; the failed-attempt evidence (pre-marker attempt dir, preflight attempts, smoke dirs,
  patched-preflight/postrun records) is preserved; the report's "all preserved, nothing deleted" holds
  for the evidence it lists (the hand-back gaps are F5, not deletions).
- **Over/under-claims:** the result tables are exact; the report under-discloses the diagnostics invalid
  58 (F1) and the round total GPU hours 4.61 (F2), and its TASL-2 open item is factually wrong (F3); the
  timeline's outage row has the CET/UTC error (F4); the review-count list is imprecise (F6).

## 4. Verdict

The B2 result is independently recomputed and correct: primary off `gemma4_31b` final_y
0.9402810083333333 over 12 instances, thinking-on descriptive 0.9552304833333333 over 12, grid verified,
proposal-journal invalid table empty (24 roots/24 journals/480 rows), normal completion, marker retired,
STATUS done at `78afa073`, watcher stopped after the marker retirement with the scene preserved. The
receipts/hashes that are present are consistent, and no deletion or retry is evident in the reviewed
record.

However, the report contains MAJOR data-quality/open-item errors that would misinform the author's X.7
decisions: the candidate diagnostics' 58 invalid (plus 82 duplicates/58 noops) are not disclosed (F1);
the "GPU hours" figure is the selection metric 0.5049, not the round total 4.6106 (F2); and the TASL-2
open item says the census is still blocked when the accepted census and the deferred bare-repo
fast-forward are in the same commit (F3). The timeline CET/UTC error (F4), the hand-back gaps (F5), and
the review-count/STATUS-placement/D28 notes (F6–F8) are minor but should be fixed. Do not take the report
to the author's X.7 decisions until the report is corrected; the B2 result itself does not change. After
the corrections (and the optional hand-back additions), a targeted re-review of the corrected report
suffices; the B2 run's tables and receipts are otherwise accepted.

VERDICT: NOT ACCEPTED
