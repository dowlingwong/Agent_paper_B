# Independent review of the M10 port kit and diff support (Task 2), 9–10 Nov 2026

Freshly spawned independent reviewers (Claude subagents; did not write the unit). Round 1 by one reviewer; rounds 2–3 by a second reviewer, because the first was cut off by a usage limit. Status: rounds 1–2 changes requested; round 3 **accepted** at harness `76bc49f` and paper `f4e09f87`. Rounds copied verbatim below.

---

## Round 1

# Review — Task 2 (M10 steps 0–1): Track G port kit and diff support, round 1

**Reviewer:** fresh independent reviewer agent (Claude), 9 Nov 2026. AI-assisted. Read-only on both worktrees; every probe ran in `/tmp/pb/scratch_rev_t2/` (scripts in `probes/`, a scratch clone of the harness in `clone/` for the T0 mutations).

**Unit under review**
- Harness `/tmp/pb/wt/harness-trackg`, branch `r1-local-trackg-20261109`, `a3fedbb..c642b6f` (4 commits).
- Paper `/tmp/pb/wt/trackg`, branch `mac-trackg-20261109`, `a15300ca..6299b837` (3 commits).

**Governing text read:** `MAC_OVERNIGHT_RUNBOOK_20261109.md` §0 and §2 (from `origin/docs/runbooks-09nov`); `MAC_LOCAL_RUNBOOK_20261104.md` §M10; `TRACK_G_RUNBOOK.md` §§1–4; `HOREKA_RUNBOOK_20261104.md` HK2; PLAN rows R1-BX-D2, D4, D5, R1-BX-REVISIONS (c), R1-TRACKG-ROLE.

## What I checked and what holds

- **Git hygiene.** All 7 commits are by `Dowling Wong <wangdowling@gmail.com>` and carry the attribution lines. `git diff --diff-filter=MDRT a3fedbb HEAD` is empty: the 24 harness files are all new. `a3fedbb` = `pin-a3fedbb` = `a3fedbbd4430…`, unchanged. Nothing outside `src/autoresearch/trackg/`, `tests/trackg/` and `scripts/trackg_*` mentions `trackg`, so no T0 module imports the new package. No deletions. Both worktrees are still clean after my review (only ignored `__pycache__`).
- **Tests.** `tests/trackg`: **102 passed** (about 10 s). The worker's logs in `/tmp/trackg_logs/` show the same failure set before and after for the harness (15 entries) and the paper (5 entries); I diffed the `*_failset.txt` files and they are identical.
- **T0 byte-identical test (the critical check).** It is genuine:
  - It really runs a `manager_proposal/v1` `run_real_campaign` (LangGraphManager → local fake llama-server, LocalWorker, event store, default controller) against the `src` of `a3fedbb` (exported with `git archive`) and then against HEAD's `src`, in the same work path. It compares the 5 request bodies and `final_train.py` unnormalised, and `trials.jsonl`/`events.jsonl` after normalisation.
  - **The normalised fields are run-to-run nondeterminism only.** I ran the probe twice at the same commit and diffed every key. The keys that differ are exactly `timestamp`, `timestamp_start`, `timestamp_end`, `event_id`, `latency_ms` (both in events and in `trials.extra.manager.llm_call`) and `elapsed_seconds`. `wall_clock_seconds` did not differ in my two runs, but it is computed from second-resolution timestamps, so it can differ. The LLM `seed` is deterministic and is **not** normalised (good). Every other output file, including `artifacts/**` and the node copy, was byte-identical between the two runs.
  - **It detects real T0 changes.** In a scratch clone (`git clone` into scratch; the worktree was not touched): a double space in the manager's system prompt (`langgraph_manager.py:116`) fails on `requests/000.json`; an extra key in the `decision_made` payload (`campaign.py:1791`) fails on `events.jsonl`; a change to the `patch.diff` written by `LocalWorker` fails on `trials.jsonl` (through `patch_hash`). Unmutated, the clone passes. The base run really imports the base `src`: `autoresearch` is not installed in the venv, and the probe runs with `-I` and puts `--harness-src` first on `sys.path`.
  - **Gap:** a change to the worker's `run.log` is **not** detected (finding 5).
  - **No conflict with the rule against dry-run tests that copy the harness.** It exports only `src`, `nodes/lr_synthetic` and `configs/nodes/lr_synthetic.yaml` from git objects. It makes no worktree, changes nothing in the repository and takes about 7–20 s.
- **Outcome classes** are exclusive by construction (`RunOutcome.__post_init__`). Real-process probes:

  | Case | Result |
  |---|---|
  | NaN mid-training, then a finite metric | `divergent/non_finite_loss` |
  | Timeout after the metric was printed | `infrastructure_failure/timeout` |
  | Exit 0, no metric | `divergent/no_metric_at_budget` |
  | Self-SIGKILL (OOM-killer stand-in), plain and compound command | `infrastructure_failure/killed` (rc 137) |
  | MemoryError under `RLIMIT_DATA` | `divergent/nonzero_exit` |

  All of these match the spec and the hand-off.
- **Diff application.** I fuzzed it differentially against `git diff --no-index` (400 random edits, `-U0/-U1/-U3`, with and without a final newline): 0 mismatches. These were refused as they should be: `..`, `model/../x`, absolute paths, a symlinked file, a symlinked directory (edit and create), renames (as git headers and as `---/+++`), binary patches, mode changes and prose around the diff. Scope really goes through `control_plane.permissions.validate_edit_scope`.
- **Node template.** Wall-clock `run_budget.kind`, `default_budget.max_wall_clock_hours`, non-integer budgets and fuzzy determinism settings are refused. The shipped template loads.
- **v2-diff schema.** Strict parser; the v1 `manager_response_format` is unchanged. The commit SHAs in the hand-off are correct.

## Findings

### Blocking

**1. Duplicate detection gives false positives: distinct edits at different places share one "normalised diff hash".** `src/autoresearch/trackg/diff_support.py:226-244` (`normalised_diff_sha256`) hashes only the removed and added lines per file. It drops context and position. `EvaluatedStates.check` (`:300-307`) tests the diff hash before the code-state hash.
- **Reproduced** (`probes/diff_probe.py`): a file with `x = 1` in both `a()` and `b()`. Diff A changes it in `a()`, diff B changes it in `b()`. B is reported `duplicate` (`duplicate_kind: normalised_diff`, `duplicate_of: trialA`) although its resulting code state differs from A's. Hunks are also concatenated per file, so hunks `(-a,+b),(-c,+d)` and one hunk `(-a,-c,+b,+d)` collide as well.
- **Effect:** a genuinely new proposal is not run, and the duplicate rate is inflated.
- **Fix:** include each hunk's normalised context lines (` ` lines, after the same blank/comment/whitespace normalisation) in the hashed payload, in order, hunk by hunk: `[path, kind, [[context_before, removed, added, context_after] per hunk]]`. This keeps the intended insensitivity to line numbers and trailing whitespace (the existing test variant stays a duplicate). Add a regression test with the two-location case.
- **Decision to state in the hand-off (§5):** the same diff against a *different* incumbent (after a keep) is also flagged `normalised_diff` although it reaches a new code state (reproduced: LR diff after a WIDTH keep). If that is intended (as D27's "seen before"), record it as its own kind (for example `normalised_diff_other_incumbent`, from also storing the incumbent state per registered diff), so the campaign policy can tell the two apart. Otherwise key `by_diff` on `(incumbent_code_state_sha256, normalised_diff_sha256)`.

**2. A timeout can leave the training process running (and holding the GPU).** `src/autoresearch/trackg/runner.py:275-287` (`_kill_group`) sends SIGTERM to the group. It escalates to SIGKILL only if the **shell** has not exited within the grace period.
- **Reproduced** (`probes/runner_probe.py`): with `run_command: "cd . && python3 job.py"` and a child that ignores SIGTERM (as Lightning-style SLURM preemption handlers do), the shell dies on SIGTERM, `proc.wait` returns, no SIGKILL is sent, and the child is **still alive** after the run returned `infrastructure_failure/timeout`. I killed it afterwards. On HoreKa that is a leaked GPU process that co-tenants the next run.
- **Fix:** after the grace period, always `os.killpg(pgid, signal.SIGKILL)` if the group still exists (probe with `os.killpg(pgid, 0)`), whatever the shell's state. Record `killed_with` (`SIGTERM`/`SIGKILL`) in the record.
- **Same fix for normal exit:** after a normal exit, also SIGKILL any remaining members of the session (orphaned data-loader workers) and record that this happened.
- **Test:** a regression test with a SIGTERM-ignoring grandchild under a compound command.

### Should fix

**3. The code-state hash crashes on any non-UTF-8 file under an editable path.** `diff_support.py:276-280` decodes with `surrogateescape`, but `_sha256_text` (`:194-195`) re-encodes strictly.
- **Reproduced:** a 4-byte binary `model/vocab.bin` in the node makes `apply_diff` raise `UnicodeEncodeError`. That is not a `DiffRefused`, so the runner, `declare_edits` and the smoke all crash. The smoke crashed the same way when the task wrote a binary output under `model/`.
- **Fix:** hash files that are not valid UTF-8 by raw bytes (`semantic_form` → `"BYTES:" + sha256(raw)`), or encode with `surrogateescape` in `_sha256_text`. Add a test with a binary file in an editable directory.

**4. The validation-only selection can still select the test metric.** `selection.py:26-42` refuses only *textually identical* `metric_regex`/`test_metric_regex`.
- **Reproduced:** with `metric_regex: 'accuracy:\s*(\S+)'` (no anchor), the run is `ok` with value **0.42 = the test accuracy**, because the test line matches the selection regex last.
- **Fix:** in `classify_run`/`parse_run_log`, when the spec is test-scored with a `test_metric_regex`, refuse any selection-metric match whose span overlaps a test-metric match. Make it a runtime spec error, or at least `divergent` with reason `metric_regex_matches_test_line`; do not drop it silently. Add a load-time sanity check of both regexes on the template's example lines. Add a test.

**5. The T0 identity test does not compare the worker artifacts, and it relies on one configuration.** `tests/trackg/test_trackg_t0_identity.py:85-105` compares only `<work>/out`.
- **Reproduced:** prefixing `run.log` in `LocalWorker` (`local_worker.py:302`) passes the test. `artifacts/trial-*/patch.diff` and `run.log` are byte-identical run to run, so they can be compared unnormalised.
- **Fix:**
  - (a) compare `artifacts/**` (and `node/.autoresearch_baseline/**`) as well;
  - (b) add a cheap structural test: `git diff --diff-filter=MDRT --name-only <base> HEAD -- src configs/nodes nodes` must be empty, and no module outside `src/autoresearch/trackg/` may import `autoresearch.trackg`.

  (b) covers the T0 configurations the probe does not exercise (keep rules, D27 skip, observers, `seed_key`, `transport_retry`).

**6. "Wall-clock refused at any depth" is overstated; time keys and time flags pass.** `node_template.py:43-47` and `:52-57`.
- **Accepted by the loader** (`probes/spec_probe.py`): `external_benchmark: {time_limit: 3600}`, `{timeout_s: …}`, `{max_time: …}`, `{hours: 1}`, `notes: {runtime_minutes: 5}`, and `run_command: "python train.py --time-budget 300"` or `"TIME_BUDGET=300 python train.py"`. `external_benchmark` and `notes` are free-form and unchecked.
- **Fix:**
  - widen the key regex (add `time`, `timeout`, `hour`, `minute`, `second`, `runtime`);
  - require `notes`/`external_benchmark` to be strings, or scan them too;
  - refuse a `run_command` matching `(?i)time[_-]?budget|--time\b|--timeout|max[_-]?time|TIME_BUDGET`.
  - The hand-off's "any wall-clock-looking key at any depth is refused" (§2 table) must match whatever is implemented.

**7. A NaN loss is caught only if the porter declares `loss_regex`.** `node_template.py:127-137` makes `loss_regex` optional. Without it, a NaN loss followed by a finite metric is `ok`, which contradicts R1-BX-REVISIONS (c) ("a non-finite loss" → divergent).
- **Fix:** make `metric.loss_regex` required (the checklist already demands it).
- **Also:** treat loss tokens like `tensor(nan)` / `nan%` that `parse_float_token` cannot parse. They are currently ignored (reproduced: `loss: tensor(nan)` → `ok`). At least extract the float inside, or count `nan|inf` substrings in matched loss tokens.

**8. Proposal diffs may create new files that shadow modules the frozen code imports.** `diff_support.py:444-448` and `:382-385`: creating a file inside an editable directory is accepted, including `model/numpy.py` and `model/sitecustomize.py` (reproduced). If an editable directory is on the frozen evaluator's `sys.path` (the script's directory, or a package directory), the proposal can replace `numpy`/`json`/`sklearn` for the evaluator and forge the metric.
- **Fix:** refuse by default the creation of `*.py` files whose stem is in `sys.stdlib_module_names`, is `sitecustomize`/`usercustomize`, or is a top-level module importable in the run environment (`importlib.util.find_spec`). Add a per-node opt-in `allow_new_files: false|true` (default false) in `trackg_node/v1`.
- **Checklist A:** add "no frozen script lives in an editable directory".

**9. The smoke campaign promotes the post-run work directory, outputs included, as the next incumbent.** `smoke.py:117-118`, `:135-136`.
- **Reproduced** (`probes/smoke_probe.py`): the baseline writes `ckpt.txt` and `model/weights.bin`. Run `s001` sees the baseline's checkpoint (`resumed_from_previous_run: True`), and its `incumbent_code_state_sha256` ≠ the baseline's, because outputs under `model/` enter the code state.
- **Effect:** a resumable trainer would start from the previous run's checkpoint, and duplicate detection against the baseline state breaks.
- **Fix:** keep a pristine code copy per run (snapshot `work` right after diff application, before execution, for example `run_dir/code/`) and promote that, or re-apply the kept diff to a clean copy of the previous incumbent. Add a test.

**10. CPU and memory caps are optional and silently absent.** `runner.py:61-89`: `cpu_list=None` and `memory_bytes=None` run uncapped, recorded as `null`. The spec asks for CPU and memory caps.
- **Fix:** require `cpu_list` and either `memory_bytes` or `memory_method: "external"` with a stated `external_limit` string (for example `slurm --mem=…`). Or require an explicit `uncapped_reason` that goes into the record.

**11. A failure inside `preexec_fn` crashes the runner and leaves a run directory without a record.** `runner.py:232-240` catches only `OSError`; a bad CPU id raises `subprocess.SubprocessError` (reproduced: `cpu_list=(4095,)` → exception; the run dir contains `work`, `run.log` and `_ar_shim` but no `run_record.json`).
- **Fix:** catch `subprocess.SubprocessError` as `launch_error` (→ `infrastructure_failure`, record written). Validate `cpu_list ⊆ os.sched_getaffinity(0)` before the copy.

### Notes (fix or record in the hand-off; not blocking)

**12. Determinism record.**
- (a) The data-loader worker count is only exported (`AR_NUM_WORKERS`), never enforced. List it in `not_forced` as `dataloader_workers (advertised via AR_NUM_WORKERS only)`, so the record does not overstate it.
- (b) The shim imports `torch` at start-up in **every** Python interpreter of the run. This adds import time to the measured run time (the timeout basis). Environment variables a task sets in-script before `import torch` (for example `PYTORCH_CUDA_ALLOC_CONF`) no longer take effect. Say so in §4 of the hand-off and in checklist B.
- (c) `DeterminismSettings.from_mapping` uses `bool()` for `cudnn_benchmark`/`deterministic_algorithms`: the string `"false"` is read as `True` and silently accepted. Use `_strict_bool` (`node_template.py:202-203`).

**13. Inert false positives in non-Python files.**
- `#` lines are dropped for `.sh` and for extensionless files, so a changed shebang (`python3` → `python2`) is `inert` (reproduced). A changed Python coding cookie is also `inert` (the AST ignores it).
- **Fix:** keep line 1 when it starts with `#!`. For `.py`, also compare the PEP 263 cookie lines.

**14. A `new file mode 100755` header is accepted, but the mode is not applied** (`diff_support.py:47`). Either refuse non-`100644` modes or apply them.

**15. Overlap check is by string only** (`node_template.py:265`). `editable: [model/]` with `frozen: [model]` loads. `editable: ["."]` loads but matches nothing in the validator. Compare after `permissions._normalize_path`, refuse `.`, and refuse an editable entry that is wholly covered by a frozen entry.

**16. Classification policy points for the hand-off's open questions (§5).**
- (a) A proposal that makes training more than 3× slower, or makes it hang, is `infrastructure_failure/timeout`. The hand-off says infrastructure failures "are rerun, not deduplicated", so such a proposal is rerun indefinitely unless the campaign caps reruns. Add a rerun cap (for example after 2 timeouts of the same code state, classify `divergent/timeout_repeated`) as an open question.
- (b) A host OOM under Slurm (`slurmstepd: error: … oom_kill`) matches a default infrastructure pattern, while CUDA OOM is `divergent`. State whether that asymmetry is wanted (question 1 covers only exceptions).

**17. Metric forging is possible by construction.** The metric is parsed from stdout, which editable code shares: a diff can print `val_accuracy: 1.0` and exit 0. Record this in §4 "Known limits". Recommend in checklist B that the frozen wrapper print the metric with a distinctive prefix after the training call returns (for example `AR_METRIC val_accuracy=…`), and that `metric_regex` anchor on it.

**18. Deviation from TRACK_G_RUNBOOK §2 not stated.** The runbook says a Track G `NodeSpec` lives "under `configs/nodes/` … registered in `nodes/registry.py`". The kit uses `configs/trackg/nodes/` and its own loader, with no registry entry. This is reasonable while v2-diff is unwired, but say it in the hand-off (§4) and in checklist A, with how T1 nodes will later reach the label-sweep path.

**19. Hand-off accuracy** (`docs/r1/reports/M10_PORTKIT_HANDOFF_20261109.md`):
- (a) Lines 69 and 80 say "17" harness-importing paper test files. `/tmp/trackg_logs/paper_test_files.txt` lists **16** (and 81 − 16 = 65 matches the "other 65"). Correct it to 16.
- (b) The wall-clock wording (see 6).
- (c) Add the limits of 12(b) and 17 to §4.
- (d) Note that the T0 test hard-codes `a3fedbb`. After a rebase onto a newer `r1`, set `TRACKG_T0_BASE_COMMIT` to the new merge base, or the test will fail for legitimate upstream T0 changes.
- Everything else I checked in the hand-off is accurate: commit SHAs, test counts (102; 578 = 476 + 102; failure sets), the base-commit explanation, the normalised field list, the mutation claims and the file list.

## Re-check plan

On the fixes, I will re-run `tests/trackg`, the scratch probes (`/tmp/pb/scratch_rev_t2/probes/{diff_probe,runner_probe,spec_probe,smoke_probe}.py`) and the T0 mutations in a fresh scratch clone (prompt, event payload, `run.log`), and re-check the hand-off numbers.

VERDICT: changes requested

---

## Round 2

# Review — Task 2 (M10 steps 0–1): Track G port kit and diff support, round 2

**Reviewer:** a fresh independent reviewer agent (Claude), 10 Nov 2026, AI-assisted. This is the round-2 re-check. The round-1 reviewer was cut off; I did not write the unit. I did not modify either worktree; both are still clean. All probes ran in `/tmp/pb/scratch_rev_t2b/`: `probes/` holds copies of the round-1 probes, pointed at the new scratch, plus the new `kill_probe.py` and `declare_probe.py`. The T0 mutations ran in a fresh scratch clone at `clone/`. I ran no paper-side tests. The paper failure set is taken from the worker's log.

**Unit**
- Harness `/tmp/pb/wt/harness-trackg`, `r1-local-trackg-20261109`, HEAD `aea6405` (round-1 fixes on top of `c642b6f`).
- Paper `/tmp/pb/wt/trackg`, `mac-trackg-20261109`, HEAD `c4af79f4`.

## What holds

- **Git hygiene.**
  - Every commit in `a3fedbb..aea6405` and `a15300ca..c4af79f4` is by `Dowling Wong <wangdowling@gmail.com>` and carries the attribution lines.
  - `git diff --diff-filter=MDRT a3fedbb HEAD` is empty: 25 files, all `A`.
  - `a3fedbb` = `pin-a3fedbb` = `a3fedbbd44…`.
  - Paper: no deletions. The only modified pre-existing file is `docs/r1/prompts/README.md` (an index row).
- **Tests.**
  - `tests/trackg`: 145 passed (14 s).
  - Full harness suite, re-run by me in the scratch clone at `aea6405` (`--continue-on-collection-errors`): 14 failed, 621 passed, 1 error. The failure set is **identical** to `/tmp/trackg_logs/harness_baseline_failset.txt` (15 entries).
  - Paper failure set: the worker's `paper_after_r1.txt` gives the same 5 entries as the baseline. I did not re-run it.
- **T0 identity.** In a fresh scratch clone, unmutated, the test passes. Each uncommitted mutation fails the byte test on the expected file:

  | Mutation | Fails on |
  |---|---|
  | Double space in the manager prompt | `out/requests/000.json` |
  | Extra key in the `decision_made` payload | `out/events.jsonl` |
  | `run.log` prefix in `LocalWorker` (the gap in round-1 finding 5) | `artifacts/trial-001/run.log` |

  Two committed mutations fail the new structural test:
  - an appended comment in `control_plane/permissions.py` (base file changed);
  - a new T0 module that imports `autoresearch.trackg`.
- **Round-1 findings re-checked with probes.**
  - **#2 (blocking): fixed.**
    - A SIGTERM-ignoring grandchild under `cd . && python3 job.py` ends in `/proc` state `Z`, meaning it was killed and is only unreaped, because PID 1 here does not reap orphans.
    - A gracefully exiting child gives `killed_with: SIGTERM`.
    - An orphaned background worker after a normal exit is killed and recorded (`leftover_processes_killed: True`).
    - Two bystander processes, one in the harness's session and one in its own session, survived every run. The kill logic does not reach unrelated processes.
  - **Fixed:** #3 (binary file in an editable directory), #4 (refused at load; overlapping match at run time is `divergent/metric_regex_matches_test_line`), #5, #6, #7 (`loss_regex` required; `tensor(nan)` and `nan,` are divergent), #9 (smoke: `resumed_from_previous_run: False` throughout; the incumbent state equals the baseline's code state), #10, #11 (bad CPU id refused before any run directory exists; preexec failures caught), #12a/c, #13, #14, #15.
  - **#8: fixed** (`new_file_not_allowed` by default, `shadowing_module` when allowed), but see finding 2 for false positives.
  - **Notes #12b, #16–#19:** documented in the hand-off and checklist as stated in the answers file. 19a ("16" files) is correct.
  - The outcome table from round 1 reproduces unchanged.
- **#1 (blocking): partly fixed.** The round-1 reproduction (one context line, same change in `a()` and `b()`) is no longer a duplicate. The same diff against another incumbent is applied and reported in `seen_diff_other_incumbent`. The defect class remains, though: see finding 1.

## Findings

### Blocking

**1. Duplicate false positives remain when the context does not tell the two places apart.**

`src/autoresearch/trackg/diff_support.py:360-370` (`EvaluatedStates.check`) and `:271-290` (`normalised_diff_sha256`).

The diff-hash test still runs before the code-state test. The hash still ignores position, so two different edits on the **same incumbent** collide whenever their context is identical. Reproduced with `probes/diff_probe.py` ("round 2 extra"):

| Case | Result | Code states |
|---|---|---|
| `-U0` diffs, `x = 1 → x = 2` in `a()` vs in `b()` | B is `duplicate`, `duplicate_kind: normalised_diff`, `duplicate_of: trialA` | differ |
| Repeated block (`Linear(64),` / `ReLU(),` ×3): edit the first `Linear(64)` vs the second, each with correct line numbers | the second is `duplicate` | differ |

Both diffs apply cleanly at their stated lines, so they are valid proposals. Repeated layer blocks are common in ML code. The effect is the round-1 effect: a genuinely new proposal is not run, and the duplicate rate is inflated. The hand-off's claim (§2) that context makes "the same change at two different places hash differently" does not hold here.

Because `by_diff` is now keyed by the incumbent, the diff-hash test adds nothing over the code-state test:
- the same diff on the same incumbent reaches the same normalised code state;
- a whitespace or comment variant of it does too.

So the diff-hash test can only add false positives.

**Fix:**
- Make the code state authoritative. A `normalised_diff` match on the same incumbent counts as a duplicate only if `code_state_sha256` also matches. Otherwise report it as information, for example `same_diff_hash_other_state: <trial>`, not as a duplicate.
- Alternatively, add the *applied* hunk positions (`applied_at` from `_apply_patch`) to the same-incumbent key.
- Add regression tests for the `-U0` case and the repeated-block case.
- Update hand-off §2.

### Should fix

**2. The shadowing check refuses legitimate new files, depending on the working directory.**

`diff_support.py:386-402` (`shadowing_name`).

**Defect 1: existing directories are checked.** Every directory component of the new file's path is checked, including directories that already exist in the incumbent, for example the editable root itself. Such a component cannot newly shadow anything: if it could be imported, it already was.

**Defect 2: the result depends on the launch directory.** `find_spec` runs against the harness process's `sys.path`. That includes `''` (the working directory) under `python -m` and pytest. Reproduced with `allow_new_files` behaviour:
- `code/new.py` → `code` (an existing editable directory named like a stdlib module).
- Launched from the harness root: `src/helpers.py` → `src`, and the same for `tests/x.py`, `scripts/x.py`, `nodes/x.py` and `configs/a.py`. Launched from `/tmp`, all of them pass.
- Launched from the node directory, every new file under `model/` would be refused, because `model` itself is found.

The refusal is the safe direction, but it makes the outcome of the same proposal depend on where the harness was started. It also contradicts hand-off §2 ("a new module or package whose name could shadow an import").

**Fix:**
- Check only the components that do not yet exist in the working copy, plus the stem of a new `.py/.pyc/.so/.pth` file.
- Run `find_spec` against a fixed path list: `sys.path` without `''`, `os.getcwd()` and the node or work directory. Better still, use the run interpreter's path list.
- Record the basis in the provenance.
- Add a test that a new file under an existing editable directory named like an importable module (for example `code/`) is accepted when its own name is safe.

**3. `declare_edits` ignores the node's `allow_new_files`.**

`src/autoresearch/trackg/declared_edits.py:49` calls `apply_diff(...)` without `allow_new_files=spec.allow_new_files`. Reproduced with `probes/declare_probe.py`, on a spec with `allow_new_files: true` and a declared edit that creates `model/helpers.py`:
- `declare_edits` refuses it (`new_file_not_allowed`);
- `WorkingCopyRunner.run` applies the same diff.

The pre-registered edit set and the runtime therefore disagree.

**Fix:**
- Pass `allow_new_files=spec.allow_new_files`.
- At `:54`, also pass `incumbent_code_state_sha256=baseline[0]` to `register`. Today edits are registered under the key `'?'`, so a repeated declared diff shows up as `seen_diff_other_incumbent` rather than as a same-incumbent match. The code-state test still catches it.
- Add a test.

### Notes (fix or record; not blocking)

**4. Process cleanup is by process group only** (`runner.py:322-345`).
- A child that calls `setpgid`/`setpgrp` stays in the run's session but leaves its group, so it is not killed. The hand-off mentions only `setsid`. Scanning `/proc/*/stat` for the session id (`fields[3]`) as well as the group would cover this cheaply. `setsid` escapes stay as documented (reproduced: the escaped child survives).
- Theoretical race: after an empty group's leader PID is freed, it could be reused before `killpg`. This is negligible with sequential PID allocation. Mention it in §4 if you like.

**5. The wall-clock key and flag regexes are conservative** (`node_template.py:49-58`).
- False positives in the free-form `notes`/`external_benchmark`: `min_lr`, `n_timesteps`, `timestep_embedding`, `second_order`, `secondary_metric`, `datetime_split`, `wallet`.
- False positives in `run_command`: `--log-every-seconds 30`, `--eval-timeout 30`, `--max-time-steps 5`.
- Not caught: environment forms such as `TIMEOUT=3600 python …` and `MAX_SECONDS=300 python …`.
- This is acceptable for a refusal-side guard. Two improvements: name the matched word in the error message, and say in checklist A that porters rename such keys (or put them in prose).

**6. A loose `test_metric_regex` is not checked at load** (`selection.py:44-49`). For example, `accuracy:\s*(\S+)` with `metric_regex: '^val_accuracy:…'` is accepted. At run time it overlaps the validation line, so **every** run is `divergent/metric_regex_matches_test_line`. That is loud, not silent. The sealed test value could also come from the validation line when no test line is printed. Add the symmetric load-time check: `test_metric_regex` must not match `<metric_name>: 0.5` and the other sample forms.

**7. `seed_env` with the same variable for train and split loads** (`node_template.py:305-307`). `build_environment` then overwrites the train seed with the split seed. Refuse `train == split`.

**8. The structural T0 test compares `BASE_COMMIT` with `HEAD`** (`tests/trackg/test_trackg_t0_identity.py:131`), not with the working tree. Uncommitted T0 edits are caught only by the byte test, and only for the configuration it exercises. Dropping `"HEAD"` (diff against the working tree), or adding a second call that does, closes this.

**9. Hand-off accuracy** (`docs/r1/reports/M10_PORTKIT_HANDOFF_20261109.md`):
- (a) Line 131 cites `*_after_r1_failset.txt`, but only `harness_after_r1_failset.txt` exists. The paper's after-r1 failure set is only inside `paper_after_r1.txt`. Add the file or correct the text.
- (b) After fixing 1 and 2, update §2 lines 47 and 50–54, and the shadowing limit at line 144.
- (c) Line 5 ("round 2 not yet run") needs updating.
- Everything else I checked is accurate: SHAs, 25 files all `A`, 145 / 621 = 476 + 145, the failure sets, the mutation claims, the 16 paper files, and the env-var instructions for `TRACKG_T0_BASE_COMMIT`.

## Re-check plan for round 3

- Re-run `probes/diff_probe.py` ("round 2 extra": U0 and repeated block must be `applied`), `probes/declare_probe.py`, and `shadowing_name` from two working directories.
- Re-run `tests/trackg` and the structural and T0 tests.
- Diff the failure sets again.

VERDICT: changes requested

---

## Round 3

# Review — Task 2 (M10 steps 0–1): Track G port kit and diff support, round 3

**Reviewer:** the independent reviewer agent (Claude) that wrote round 2, 10 Nov 2026, AI-assisted. I did not write the unit. I did not modify either worktree; both are clean at the heads below. Probes ran in `/tmp/pb/scratch_rev_t2b/`:
- `probes/`: the round-2 probes plus the new `r3_probe.py`; `kill_probe.py` gained two `setpgid` cases;
- `clone3/`: a fresh scratch clone at `76bc49f`, for the T0 mutations and the full harness suite.

I ran no paper-side tests.

**Unit**
- Harness `/tmp/pb/wt/harness-trackg`, `r1-local-trackg-20261109`, HEAD `76bc49f` (round-2 fixes on top of `aea6405`).
- Paper `/tmp/pb/wt/trackg`, `mac-trackg-20261109`, HEAD `f4e09f87`.

## Checks

- **Git hygiene.**
  - New commits: harness `76bc49f`; paper `0a5e0c1e` and `f4e09f87`. All are by `Dowling Wong <wangdowling@gmail.com>` and carry the attribution lines.
  - `git diff --diff-filter=MDRT a3fedbb HEAD` is empty: 26 files, all `A`.
  - Paper `a15300ca..HEAD`: the only pre-existing file modified is `docs/r1/prompts/README.md`. No deletions.
- **Tests.**
  - `tests/trackg`: **161 passed**.
  - Full harness suite, re-run by me in `clone3`: 14 failed, **637 passed**, 1 error. The failure set is **identical** to `harness_baseline_failset.txt`.
  - Paper: the worker's `paper_after_r1_failset.txt` and `paper_after_r2_failset.txt` are both identical to `paper_baseline_failset.txt` (5 entries). `paper_after_r2.txt` reports 5 failed, 152 passed.
- **T0 identity at `76bc49f`.** Unmutated: 3 passed. Each mutation fails as expected:

  | Mutation | Fails on |
  |---|---|
  | Manager prompt (uncommitted) | `out/requests/000.json`, and now also the structural test ("changed in the working tree") |
  | `decision_made` payload | `out/events.jsonl` |
  | `LocalWorker` `run.log` | `artifacts/trial-001/run.log` |
  | Uncommitted edit of an unexercised base file (`control_plane/permissions.py`) | structural test (round-2 note 8 fixed) |
  | Untracked T0 module importing `autoresearch.trackg` | structural test |

## Round-2 findings

| # | Status | Evidence |
|---|---|---|
| 1 (blocking) duplicate false positives | **Fixed** | `diff_probe.py` "round 2 extra": the `-U0` B case and "repeated block, edit 2" are both `applied` with differing code states. B reports `same_diff_hash_other_state: A`, as information only. True duplicates are still caught as `code_state`: the same diff again, a trailing-whitespace variant, a comment-only variant. A baseline-equivalent diff is `inert`. Another incumbent gives `seen_diff_other_incumbent`. |
| 2 shadow-check false positives / cwd dependence | **Fixed** | `r3_probe.py` from `/`, `/tmp`, the harness root and `harness/src`: identical results. `code/new.py`, `src/helpers.py`, `tests/helper2.py` and `model/helpers.py` are applied. `model/numpy.py`, `model/yaml.py` and `model/json/__init__.py` are `shadowing_module`. The recorded `shadow_check.import_path` never contains the cwd (basis `interpreter:python3`). |
| 3 `declare_edits` and `allow_new_files` | **Fixed** | `declare_probe.py`: `declare: accepted`, and the runner agrees. The incumbent hash is registered and recorded. |
| 4 cleanup by group only | **Fixed** (setpgid); setsid documented | `kill_probe.py`: a `setpgid` child after a normal exit ends in `Z`, with `leftover_processes_killed: True`. A `setpgid` child that ignores SIGTERM under a timeout ends in `Z`, with `killed_with: SIGKILL`. The `setsid` escape survives, as documented. Four bystanders (same session and own session) survived every case. |
| 5 wall-clock regexes | **Fixed / documented** | `TIMEOUT=3600 …` and `MAX_SECONDS=300 …` are refused, and the message names the matched text. Ordinary prefixes and flags are accepted: `CUDA_VISIBLE_DEVICES=`, `OMP_NUM_THREADS=`, `PYTHONUNBUFFERED=`, `--config=`, `--warmup_steps=`, `--dataset=timeseries`, `--log_dir=runs/minutes`. Remaining false positives are listed in hand-off §4. |
| 6 loose `test_metric_regex` | **Fixed** | `accuracy:\s*(\S+)` is refused at load (it matches `val_accuracy: 0.5`). |
| 7 identical seed variables | **Fixed** | Refused at load. |
| 8 structural test only against HEAD | **Fixed** | See the mutation table above. |
| 9 hand-off accuracy | **Fixed** | The hand-off is accurate: line 5 status, the commit table (HEAD `76bc49f`), 26 files all `A`, 161 / 637 = 476 + 161, the failure-set file names (all exist), §2 duplicate and shadow text, §4 shadow-check stand-in, setsid and PID-reuse limits. |

The round-1 outcome table (`runner_probe.py`), `spec_probe.py` and `smoke_probe.py` all reproduce unchanged. The worker's remark on the PEP 263 probe case is correct: a line-1/2 comment matching `coding[:=]` is an encoding declaration, so a change to it is not inert. I accept it.

## Findings

### Blocking

None.

### Should fix

None.

### Notes (optional; no re-review needed)

**1. A child that left the group does not get a graceful SIGTERM.** `runner.py` (`_kill_group`) sends SIGTERM through `killpg` only. A session member outside the group therefore gets no SIGTERM and is SIGKILLed after the grace period (observed: `killed_with: SIGKILL`). That is the safe outcome. If graceful shutdown matters, also SIGTERM the `_run_members` before the grace wait.

**2. The shadow-check basis is `python3` on the harness's `PATH`.** `apply_diff(..., interpreter="python3")` is not set from the node spec or the runner. The limit is documented in hand-off §4 and recorded in the provenance. When v2-diff is wired in, pass the run command's interpreter.

VERDICT: accepted
