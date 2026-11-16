Reviewed base: f77dbe322178cbc36932802882f54b6de314324d (paper); harness 717ad835df32bbe1047d032fb5bb8dde5384a258

# M10 v2-diff wiring — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 3. Harness branch `r1-local-trackg-v2-20261114` (from `r1-local-trackg-20261109` @ `76bc49f2`); paper branch `mac-trackg-v2-20261114` (from `mac-trackg-20261109` @ `f56f7f35`). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (two blocking: baseline failure handling, prompt file selection; five should-fix).
- Round 2: **accepted** at harness `717ad835`, paper `f77dbe32`.

Accepted commit (round 2, last): harness 717ad835df32bbe1047d032fb5bb8dde5384a258, paper f77dbe322178cbc36932802882f54b6de314324d

Round-2 notes, not blocking: the report's "as for B1" means the B1 exam (not the baseline finding B1); the interleaving test's docstring promises a cross-step case it does not cover (behaviour checked by the reviewer's probe); `extra_payload` is checked only at construction; `better()` keeps an unreachable branch for a missing best value.

The round texts are reproduced unchanged below.

---

# Review: Unit 3 — v2-diff into a manager and the campaign path (round 1)

Reviewer: independent (Claude subagent). I did not write this unit.
Unit: `MAC_OVERNIGHT_RUNBOOK_20261113.md` §3 (on `gh/docs/runbooks-14nov`), with the accepted runbook review's S7b, S8, S11 and §3 interpretations 6/7, and the author's Q8 answer (M10 §5 items 1–8 all (a)).
Subject:
- harness `r1-local-trackg-v2-20261114` @ `776282e9424b39d95d06d976db1c6598a61899f8` (parent `76bc49f25258…`), worktree `/tmp/pb/wt/tgv2`;
- paper `mac-trackg-v2-20261114` @ `ad80a2d25bb17b3935e9291e4a29675fdaf68ef7` (parent `f56f7f359d2a…`), worktree `/tmp/pb/wt/tgv2p`.

I modified no branch or worktree (both `git status` clean after the runs). I read no secrets. I used scratch dirs under `/tmp/rev_u3/` (shared clones at both commits, probe scripts) and removed them at the end.

## 1. What I ran

| Check | Result |
|---|---|
| Diff vs base | harness: 3 files, all `A` (`manager_v2_diff.py`, `campaign_v2_diff.py`, `test_trackg_campaign_v2_diff.py`). `git diff --diff-filter=MDRT --name-only a3fedbb 776282e9` is empty. `tests/trackg/test_trackg_t0_identity.py` is byte-identical to `76bc49f2` (empty diff). paper: 1 file `A` (`docs/r1/reports/M10_V2DIFF_WIRING_20261114.md`) |
| Imports | stdlib only (`hashlib`, `json`, `urllib.request`, `dataclasses`, `pathlib`, `typing`) plus `autoresearch.trackg.*`. No new dependency; `pyproject`/`uv.lock` untouched |
| `pytest tests/trackg` (the given command, in the worktree) | **168 passed** (161 + 7), 15 s |
| T0 identity, verbose, in a scratch clone at `776282e9` | 3/3 passed (byte-for-byte v1 probe, structural test, normalisation test); none skipped |
| Full harness suite, `--continue-on-collection-errors`, in scratch clones | head `776282e9`: 14 failed, **644 passed**, 1 error; base `76bc49f2`: 14 failed, 637 passed, 1 error. Failure sets (15 entries) **identical**, and identical to the list in `M10_PORTKIT_HANDOFF_20261109.md` §3 |
| New test file 8× under 2× CPU oversubscription (2 cores) | 8/8 passed. In the timeout test the baseline takes 0.05–0.12 s against its 0.5 s timeout, so the margin is ~5×; the two `sleep` runs are genuine timeouts (`executed: true`, `timed_out`) |
| Probes (scratch scripts, patched only in-process) | see findings: prompt file selection, sealed value in ledger, baseline failure, `extra_payload`, STOP mid-campaign, minimize direction, timeout counting with interleaving across steps, and whether the infra-rerun test's reruns really execute |
| Commit metadata | both commits: author and committer `Dowling Wong <wangdowling@gmail.com>`; `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01GRrwsENkCbv1g4aZuxYGQR` present. Branch names and bases as the runbook says |
| Unit 2 cross-check | `mac-htcondor-20261114:r1/scripts/htcondor/htc_events.py` uses reasons `htcondor_eviction`, `…_preemption`, `…_memory_hold`, `…_walltime_hold`, `…_image_pull`, `…_restart_limit`, none equal to `timeout`, so they are consistent with the cap counting only the runner's `timeout` (S8) |

### What is right (verified)

- **Flag.** `run_v2_diff_campaign` refuses unless `enable_v2_diff is True`, before creating anything (tested). Nothing in the T0 path imports the new modules.
- **Cap per item 8 / Q8 (a), on in the v2 path.** Only `infrastructure_failure/timeout` counts; after `timeout_cap` (2) timeouts of the same normalised code state the step's final outcome is `divergent/timeout_repeated`, and the state is registered in `EvaluatedStates`, so the same code state later is `not_run_duplicate` (tested with a real timeout). The counter is per code state and survives across steps: my probe with *timeout, killed ×3 → `infrastructure_failure_final`* in step 1 and the same diff in step 2 gives one timeout in step 2 → `timeout_repeated` (2 in total). Interleaving with another state Y (timeout, then ok → kept) does not disturb X's count. This matches "2 timeouts of the same code state".
- **Other infrastructure failures** (incl. `htcondor_walltime_hold` in a probe) never count toward the cap and stop after `max_infra_reruns` (2) reruns; the worst case per proposal is bounded (≤ `timeout_cap` + `max_infra_reruns` + 1 runs). Reruns of the same diff are not duplicates, because the runner never registers an infrastructure failure (real-timeout test: both runs executed).
- **Keep/discard direction.** Strict improvement, both directions (probe with `minimize`: 0.6 → 0.55 kept, worse discarded). The next incumbent is `result.code_dir`, the pre-run snapshot, as in the smoke.
- **Budget.** One manager call per step; reruns are inner-loop and do not call the manager; an unparsable reply is `invalid_proposal`, charged, with `parse_error` and the raw reply recorded, never repaired.
- **Ledger.** `runs_root` and the ledger are created with `exist_ok=False`, then only appended. Run records go through `manager_view`; a probe campaign's ledger contains neither a `sealed` key nor the fixture's test value.
- **Manager.** `temperature` 0, per-step seed, structure-only v2-diff `response_format`, strict parser; a transport exception raises `STOP: …`.

## 2. Findings

### Blocking

**B1. A baseline that is not `ok` is neither rerun nor a STOP; the first `ok` proposal is then kept unconditionally.**
`src/autoresearch/trackg/campaign_v2_diff.py:92-98` runs the baseline once. If it is `infrastructure_failure` (an eviction or a timeout, which Q8 says are infrastructure and therefore rerun) or `divergent`, `best` stays `None` and the campaign continues; `better(value, None)` (l. 89-90) is then true for any value. Probe: a baseline that times out → `best_after: None`, and the step-1 proposal is recorded as `kept` (0.51) with no comparison. The repeated-timeout cap also does not apply to the baseline. The ledger then holds a keep decision that is not a keep/discard against the pre-run incumbent.
*Fix:* run the baseline through the same outcome handling as a proposal (timeout → rerun, cap 2; other infrastructure failure → up to `max_infra_reruns` reruns). If the baseline is still not `ok`, append a ledger line (`decision: "stop_baseline_not_ok"` with its outcome) and raise a STOP (`V2DiffCampaignError`) before the first manager call. Add a test for each path (baseline timeout ×2, baseline eviction then ok, baseline divergent).

**B2. The prompt's file selection does not use the scope validator's path semantics: frozen files can reach the prompt, and some editable files are missing.**
`src/autoresearch/trackg/manager_v2_diff.py:55-72` compares raw spec strings and follows symlinks. Probes with specs the loader accepts:
- frozen `./model/metric.py` (frozen inside the editable `model/`) → `=== model/metric.py ===` **is shown** (l. 65 compares `rel` with the raw `"./model/metric.py"`);
- a symlink `model/labels_link.csv → ../data/secret_test_labels.csv` in an editable directory → the **frozen data file's content is shown** (`path.is_file()` and `read_text` follow the link, l. 62/68). The runner copies symlinks as links and `diff_support` refuses edits through them, but the prompt reader does not;
- editable `model/*` (a form the scope validator and `_norm_scope` accept) → `model/net.py` is **not shown** (l. 59-60 treat `model/*` as a literal path).
The unit's requirement is "editable files only, frozen excluded"; the first two break that boundary with ordinary specs.
*Fix:* list files from `os.walk(root, followlinks=False)`; skip every symlink (and any path with a symlink component); keep a file only if `validate_edit_scope([rel], spec.to_base_node_spec()).valid` (same normalisation and `dir/`, `dir/*` handling as the diff path). Add tests for `./`-prefixed frozen entries, `dir/*` editable entries and a symlink in an editable directory.

### Should-fix

**S1. The infra-rerun test passes for the wrong reason: its reruns are duplicate refusals, not executions.**
`tests/trackg/test_trackg_campaign_v2_diff.py:90-108` wraps the real `WorkingCopyRunner.run`. The real run of `s001` succeeds and the runner registers its state as evaluated *before* the wrapper overwrites the outcome with `htcondor_eviction`. My probe of the same set-up: `s001_r1` and `s001_r2` have `executed: False`, `diff status: duplicate, duplicate_of: s001`; the wrapper then paints `htcondor_eviction` over `outcome None`. So the test does not show that a rerun after an infrastructure failure really runs, and would not catch a regression there.
*Fix:* inject the outcome before registration, for example by monkeypatching `autoresearch.trackg.runner.parse_run_log` to return the scripted outcome (that is how my probe did it). Assert `run["executed"] is True` and `run["diff"]["status"] == "applied"` for every rerun. Add the interleaving cases as tests: timeout then ok on the rerun (kept; counter not reset), and *timeout + killed ×3 → final* followed by the same diff in a later step (one more timeout → `timeout_repeated`).

**S2. `extra_payload` can silently override the pinned request fields, and the ledger does not record the request parameters.**
`manager_v2_diff.py:115-117` spreads `**self.extra_payload` last. Probe: `extra_payload={"temperature": 0.9, "seed": 1}` sends temperature 0.9 and seed 1, while the call record still says seed 4011020074 (l. 118-119). The call record also lacks `model`, `temperature`, `max_tokens`, the `response_format` and `extra_payload` itself, so a ledger cannot show what was asked of which model.
*Fix:* refuse `extra_payload` keys that collide with `model`, `messages`, `temperature`, `seed`, `max_tokens`, `response_format` (a constructor-time `ValueError`). Record the whole payload except `messages` (plus the base `seed` of the manager) in the call record. Test both.

**S3. A transport STOP leaves no trace in the ledger.**
`manager_v2_diff.py:120-123` raises out of `campaign_v2_diff.py:101`. Probe: after a STOP at step 2 the ledger has 2 lines (baseline, step 1) and nothing about the STOP.
*Fix:* in the campaign, catch the manager's STOP, append `{"step": n, "decision": "stop_transport", "error": …, "manager_call": {prompt hash, seed}}`, then re-raise. A dedicated exception class (`ManagerTransportStop(RuntimeError)`) lets callers tell a STOP from a bug; `except Exception` at l. 122 would otherwise also turn a programming error inside a custom transport into a "transport" STOP.

**S4. The round-3 open note "pass the run's real interpreter to the shadowing check when v2-diff is wired in" is neither done nor listed.**
The hand-off (`M10_PORTKIT_HANDOFF_20261109.md`, review line and §4) names this for exactly this step. `run_v2_diff_campaign` → `WorkingCopyRunner.run` → `apply_diff(…)` uses the default `interpreter="python3"` (`diff_support.py:486`); the campaign has no way to pass the node's interpreter (for example `.venv/bin/python`).
*Fix:* add an `interpreter` parameter to `WorkingCopyRunner.run` (a kit file added after `a3fedbb`, so the structural test is not affected) and to `run_v2_diff_campaign`, pass it to `apply_diff`, and record it; or, at minimum, list it as open in the report's §"Open or not done".

**S5. The report overstates the HTCondor path and leaves out facts a reader needs.**
`docs/r1/reports/M10_V2DIFF_WIRING_20261114.md`:
- l. 40 (and the module docstring, `campaign_v2_diff.py:22-23`) say other failures include "an HTCondor-level reason such as `htcondor_eviction`" "passed in by a caller". There is no API for that: the campaign sees only runner outcomes. An HTCondor eviction kills the job running the whole campaign, and a restarted job fails on the existing `runs_root` (`mkdir(exist_ok=False)`, l. 74): nothing is overwritten, but the campaign has no resume. Only the (flawed, S1) test injects such a reason. Say this plainly, and that resume-safe campaigns (Unit 2's helper) are not wired.
- State that the timeout counter is per code state over the whole campaign, so the second timeout may come in a later step (my probe D2), and that an `infrastructure_failure_final` state is not registered, so it can be proposed and run again (bounded by the manager budget).
- State the policy for `seen_diff_other_incumbent` (run; Q7 (a)) — the hand-off §4 left that policy to this step.
- l. 55 gives only the `tests/trackg` count. Add the full-suite result (14 failed / 644 passed / 1 error at head vs 637 passed at base, identical failure set; I reproduced it).
- Add B1/B2 fixes or limits once resolved.

### Notes

- **N1.** No total prompt cap (`manager_v2_diff.py:87-88`; only 20,000 characters per file). A node with many editable text files can overflow the server context; llama-server answers HTTP 400, which is a transport STOP for the whole campaign. Consider a total cap with a recorded truncation, or treat a context-length error as an invalid proposal (decide which, and say so).
- **N2.** The history (l. 90-94) never shows the baseline or the current best value, and a `timeout_repeated` step appears only as `discarded_divergent`. Showing the incumbent's validation value and the final outcome reason would give the model the information a human would use. Prompt-design choice; fine to leave for Track G porting, as the report says.
- **N3.** The call record keeps `raw_reply` and the prompt hash but not the prompt text or `finish_reason`. The prompt is reconstructable from the snapshots and history, but storing it (or the request body, as the T0 probe does) would make audits direct; `finish_reason == "length"` would separate truncated replies from malformed ones (as B1 does for exam trials).
- **N4.** The real-timeout test (l. 75-87) does not assert that the baseline was `ok`. In an environment with real torch installed, the determinism shim imports torch at start-up and the 0.5 s timeout would make the baseline time out too; the test would still pass while exercising a degenerate path. Add `assert entries[0]["runs"][0]["outcome"]["kind"] == "ok"` (it holds here, 0.05–0.12 s under load).
- **N5.** Slurm's `DUE TO TIME LIMIT` is `infrastructure_log_pattern`, not `timeout`, so a proposal that hits the Slurm walltime before the runner timeout is bounded by `max_infra_reruns`, not by the cap. Consistent with S8 for HTCondor; worth one sentence in the report, next to the open question on walltime holds.
- **N6.** The fixture's `train.py` contains the literal `test_accuracy: 0.4242`, so that value appears in every prompt as code (not as a measured value). This is a fixture artefact, not a leak; it explains why the test only checks the history section.

## 3. Summary

The wiring is clean and additive, T0 is untouched (unchanged test file, byte-for-byte probe and structural test pass, full-suite failure set identical to base), and the item-8 cap is implemented on, per code state, with the right exclusions. Two issues block acceptance: an un-rerun, non-STOP baseline failure that leads to an unconditional keep (B1), and prompt file selection that can show frozen content and hide editable files (B2). One test passes for the wrong reason (S1), and the ledger/reporting gaps S2–S5 should be fixed in the same round.

Verdict: changes requested

---

# Review: Unit 3 — v2-diff into a manager and the campaign path (round 2)

Reviewer: the same independent reviewer as round 1 (`REVIEW_U3_V2DIFF_round1.md`).
Subject:
- harness `r1-local-trackg-v2-20261114` @ `717ad835df32bbe1047d032fb5bb8dde5384a258`, one commit on `776282e9`;
- paper `mac-trackg-v2-20261114` @ `f77dbe322178cbc36932802882f54b6de314324d`, one commit on `ad80a2d2`.

I modified neither branch nor worktree (both clean). I read no secrets. I used scratch dir `/tmp/rev_u3/` (a shared clone at `717ad835` and probe scripts) and removed it at the end.

## 1. What I ran

| Check | Result |
|---|---|
| Round-2 diff | harness: `campaign_v2_diff.py`, `manager_v2_diff.py`, `runner.py` (+`interpreter` parameter, passed to `apply_diff`), the new test file. `diff_support.editable_files` already existed in the kit, so it is reused and not changed. paper: the report only |
| Base invariants | `git diff --diff-filter=MDRT --name-only a3fedbb 717ad835` is empty. `tests/trackg/test_trackg_t0_identity.py` is byte-identical to `76bc49f2` |
| `pytest tests/trackg` (in the worktree, the given command) | **173 passed**; nothing skipped |
| Full harness suite, `--continue-on-collection-errors`, in a scratch clone at `717ad835` | 14 failed, **649 passed** (637 + 12 new), 1 error. The failure set is identical to the 15 entries at base `76bc49f2` and in the 9 Nov hand-off (same md5 of the sorted list) |
| New test file and T0 identity file, 6× with the 2 cores oversubscribed 3× | 6/6 passed (15 tests each time) |
| Probes | see §2 |
| Commits | author and committer `Dowling Wong <wangdowling@gmail.com>`; `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01GRrwsENkCbv1g4aZuxYGQR` on both |

## 2. Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| **B1** baseline | **Resolved** | `campaign_v2_diff.py:141-153`: the baseline goes through `run_with_retries` (timeout → cap, other infrastructure failure → `max_infra_reruns`); not `ok` → `baseline_failed` ledger line, then `V2DiffCampaignError` STOP before any manager call. `best` is never `None` afterwards. Tests: two baseline timeouts → STOP with one ledger line and runs `s000_baseline`, `s000_baseline_r1`; a kill then an `ok` baseline → 0.6 used, and 0.55 is `discarded` |
| **B2** prompt files | **Resolved** | `manager_v2_diff.py:61-78` uses `diff_support.editable_files` (`os.walk`, which does not follow directory links, plus `validate_edit_scope`) and skips symlinked files. My probe, with spec `editable: [train.py, model/*]`, `frozen: [evaluate.py, data/, ./model/metric.py]`, a file link to frozen data, a directory link to `data/` and a directory link outside the node: `model/net.py` shown; `model/metric.py`, the frozen content and the outside content all absent |
| **S1** test scripting | **Resolved** | outcomes scripted at `runner.parse_run_log`, before registration; the test asserts `executed is True` for every rerun. Interleaving test: timeout, killed, timeout → `timeout_repeated` |
| **S2** pinned fields | **Resolved** | `__post_init__` refuses collisions with `PINNED_FIELDS` (probe: `response_format` refused); the call record has `request` (payload without messages) and `base_seed`; tested |
| **S3** transport STOP | **Resolved** | `ManagerTransportStop` carries the call record; the campaign writes `stop_transport` and re-raises (`campaign_v2_diff.py:156-162`); tested |
| **S4** interpreter | **Resolved** | `interpreter` passes from `run_v2_diff_campaign` through `WorkingCopyRunner.run` to `apply_diff`; the default `python3` keeps earlier kit behaviour; the report says callers must set it |
| **S5** report | **Resolved** | HTCondor reasons removed from the campaign path and the no-resume limit stated. Also stated: timeout counting across steps, re-proposal after `infrastructure_failure_final`, the Q7 policy, walltime vs the cap, and full-suite numbers (attributed to the reviewer) |
| N4 | Done | baseline-`ok` assert in the real-timeout test |
| N1, N2, N3, N5 | Listed as open in the report | acceptable |

The rest of round 1 still holds: the flag, the cap per item 8 (on in the v2 path, per code state, registered as evaluated), the keep/discard direction, the pre-run snapshot incumbent, budget accounting, the append-only ledger, no sealed metric in ledger or prompt, temperature 0 with per-step seeds, strict parse, and no new dependency.

## 3. New findings

### Blocking

None.

### Should-fix

None.

### Notes (optional; no new round needed)

- **N1.** Report, "The manager", last bullet but one: "(… is such a STOP today: open item, as for B1.)". "B1" here presumably means the B1 exam's handling of over-long output, but in this unit's review record B1 is the baseline finding. Write "as the B1 exam does for truncated output" or drop the reference when the report is next touched.
- **N2.** `test_timeouts_interleaved_with_infra_failures_and_across_steps`: the docstring talks about counting across steps, but the test covers one step only. The cross-step behaviour is correct (my round-1 probe D2: one timeout in step 1, then the same diff in step 2 times out once → `timeout_repeated`). A two-step case would make the name true.
- **N3.** `extra_payload` is checked only in `__post_init__`. The dict is mutable, so a caller could add a pinned key afterwards. Copying it into a `MappingProxyType`, or re-checking in `propose`, would close this; low risk.
- **N4.** `better()` (`campaign_v2_diff.py:100-101`) keeps a `best is None` branch that can no longer be reached. Harmless.

## 4. Summary

Every round-1 blocking and should-fix finding is resolved, and the fixes are tested. Base and T0 invariants hold: no `a3fedbb` file changed, the T0 identity file is unchanged and passes, and the full-suite failure set is identical to base. The remaining notes are cosmetic or low-risk.

Verdict: accepted
Accepted commit: harness 717ad835df32bbe1047d032fb5bb8dde5384a258, paper f77dbe322178cbc36932802882f54b6de314324d

