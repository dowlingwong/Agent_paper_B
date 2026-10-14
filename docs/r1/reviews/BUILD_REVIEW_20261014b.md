# Independent build review — batch 4 (D27 F3 fix, D28 revised criterion 2, R1-E1B-RERUN2 entrypoints)

Reviewer: an independent, fresh-context, AI-assisted reviewer with no access to the
implementer's reasoning or notes. I edited no code and made no commit or push; the only
write is this file. Hard rules observed: no LLM calls, no GPU, no Ada. Every claim below
was re-checked against the diffs, the code at the heads, a fresh local run, or a
reproduction of the implementer's fail-before logs.

Reviewed:
- Paper: `/Users/wongdowling/Documents/agent_paper_B`, branch `main`, base `5f650be`, head `9dd245c` (P6 `271fc16`, P7 `9dd245c`).
- Harness: `/Users/wongdowling/Documents/autoresearch_harness`, branch `r1`, base `0f2d9e9`, head `ed55297`.
- Both remotes are at the heads (`ls-remote` verified). `r1/scripts/HARNESS_PIN_RERUN2` = `ed55297c1ac447453d9389494554d1f710a6b4d1`, which equals the harness head.

## My own test runs (fresh, this session)

| run | result | compare with claim |
|---|---|---|
| Harness `tests/stage2/test_r1_d27_novelty.py` | 8 passed | — |
| Harness full suite (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`) | 8 failed, 386 passed, 1 warning, 1 error | identical to `harness_suite_head.log`; the 9 IDs are exactly the launcher's accepted list minus the Ada `/bin/zsh` exception |
| Paper `make r1-test` (absolute `AR_HARNESS_ROOT`, harness venv) | 135 passed in 18.6 s | identical |
| Paper `make test` | 212 OK, 6 OK, 12 OK | identical |
| New paper tests (`test_d28_liveness.py`, `test_d28_gate.py`, `test_e1b_compare.py`) | 25 passed | — |
| New runner tests (`test_ada_e1b_rerun2.py`) | 17 passed | — |
| F3 reviewer reproduction at harness base `0f2d9e9` (base worktree, head venv, `PYTHONPATH=<base>/src`) | prints `config_seen_before: false` | matches `f3_base_reproduction.log` |
| Same script at harness head `ed55297` | prints `config_seen_before: true` plus the four new fields | fix confirmed independently |
| New D28 gate tests against paper base `5f650be` (base worktree) | 5 failed, 8 passed | matches `paper_base_new_tests.log` |
| New D27 test file against harness base `0f2d9e9` | collection error (`_active_config_sha256` missing) | matches `harness_base_d27_tests.log`; behavioural fail-before comes from the reproduction above |
| TrialRecord comparison: same deterministic 5-trial campaign at harness base vs head, timestamps stripped | record JSON identical (sha256 `f13ac01b…`) | supports "TrialRecord bytes unchanged" |
| DT4 `e1b_analyze` regeneration from a committed-inputs `git archive` | `analysis.json` sha256 identical (`d0d5979a…`) | the runner's regeneration-check pattern is deterministic |
| Committed smoke re-derivation: `python -m r1.liveness --offline results/r1/engineering/liveness_scripted_20261014T075806Z/ledgers` | all five nodes reproduce the committed numbers, source and verdict | F5 (un-re-derivable scripted report) is resolved for this smoke |
| Offline DT4 liveness via the CLI | `openml_ionosphere` FAIL (criteria 1 and 2), `digits_mlp` FAIL (criterion 2) | matches the tests |

## Checklist verdicts

### 1. Each row is implemented as written — PASS with one MAJOR measurement defect (F7)

D27: the `edit_novelty` event gains `effective_config_sha256`, `active_config_sha256`,
`active_config_equals_incumbent`, `active_config_seen_before`
(`src/autoresearch/control_plane/campaign.py:1506-1523`); E2 snapshots store both seen sets
(`snapshot.py:275-278,350-359`) and `resume_campaign` seeds them (`snapshot.py:856-866`);
old snapshots resume with an `seen_before_resume: "unknown"` marker on the first event and
never a silent empty set (`campaign.py:1068-1070,1524-1526`). Real committed DT4 snapshots
lack the fields and read back as `None` (checked `…E1b_20261013T151857Z/provenance/snapshots/digits_mlp__s104/E2_b004/manifest.json`).
D28: criterion 2 is now active-key novelty with the denominator over evaluated trials
(`r1/liveness/check.py:52-85`), inactive-key rejections are a separate count
(`r1/liveness/check.py:96-101,210-211`), legacy ledgers are replayed and the report states
`novelty_source` (`r1/liveness/novelty.py:92-131`), and the gate accepts only
LLM-backed memory-on manifests with the contrast exemption (`r1/liveness/gate.py:34-66`).
R1-E1B-RERUN2: the runner, launcher and comparison are as specified (details under items 6–9).
The one defect is the definition of the "full configuration" used for undeclared nodes
(F7): the event flags and the replay both project through
`build_effective_config`, which silently drops real editable constants of `digits_mlp`
(and `tabular_mlp`). Criterion 1 still uses a literal `1` in `verdict()`
(`check.py:81`) as before; criteria 2 and 3 use named constants as the prompt requires.

### 2. `TrialRecord` bytes unchanged; default paths byte-identical — PASS

No record/serialization code is in either diff; the new data travels in separate
`edit_novelty` events and in snapshot manifests. `test_records_are_unchanged` passes, and
my base-vs-head run of the same deterministic five-trial sequence produced byte-identical
records after stripping only the timestamp fields. Default output paths are unchanged in
the diffs (`e1b_collect` default `E1b_<UTC>`, liveness default `liveness_<manager>_<UTC>`,
snapshot file layout); the rerun's new names (`liveness_llm_*`, `E1b_rerun2_*`,
`HEADROOM_RERUN2_*`) are additions, not changes.

### 3. F3 reproduction fixed; old snapshots give "unknown" — PASS

F3 is fixed: my fresh rerun of the reviewer's exact scenario gives
`config_seen_before: true` and `active_config_seen_before: true` at head
(the same script prints `false` at base). Old-format snapshots (`None` sets) produce
`seen_before_resume: "unknown"` on the first `edit_novelty` event and are documented in
both docstrings (`campaign.py:1053-1061`, `snapshot.py:856-866`); the new test asserts the
marker appears once and never on later events. One adjacent gap is F9 (E1-snapshot replay).

### 4. Active vs full hashing when `model_type` changes mid-campaign — PASS

`_project_active_config` resolves the active set from the *config's own* `model_type`
(`campaign.py:469-497`), the incumbent active config follows keeps and demotes
(`campaign.py:1153-1156,1647-1649`), and case differences (`C` vs `c`) are handled by the
lower-case canonical map. `test_event_level_projection_across_a_model_type_switch`
switches logistic_regression → gradient_boosting and then makes an inert `class_weight`
change: the active hash/flags equal the incumbent while the full hash/flags differ —
exactly the intended behaviour.

### 5. Novelty denominator excludes skipped trials; legacy replay vs independent recomputation — PARTIAL (F7)

Denominator: `replay_tally` skips `decision == "skipped"` (`novelty.py:98-100`), the events
source counts one payload per evaluated trial, and the boundary tests pin 1/2 = pass and
1/3 = fail plus "0 evaluated can never pass" (`test_d28_liveness.py:130-162`). Skipped
`inactive_key` trials get no `edit_novelty` event, so both sources agree.

The independent-recomputation requirement does **not** hold in the strong sense: the test's
"independent" script (`test_d28_liveness.py:47-103`) still calls `build_effective_config`
for the projection, so it cannot detect that the projection drops three of `digits_mlp`'s
five editable constants. My own replay from the node's actual constants gives different
numbers: DT4 digits 32/120 novel (vs 8/120 reported; verdict still FAIL) and scripted
smoke digits 20/20 novel (vs 7/20 reported FAIL). See F7.

### 6. Gate: only LLM memory-on manifests; arm-B exemption cannot bypass arm A — PASS

`require_live` rejects any manifest whose `manager_kind != langgraph` or whose
`memory_mode` is not in `("append_only_summary", "append_only_summary_with_rationale")`
*unconditionally*, before the exemption (`gate.py:49-66`), so the contrast exemption can
only skip the mode match. `r1/scripts/deepthought_batch1_resume.py:172-182` gates only the
`langgraph` collection and passes arm A's declared mode; the runner's `ARMS` table is
fixed (`ada_e1b_rerun2.py:59-63`). Tests cover scripted/memory-off manifests rejected even
for the contrast role, and a memory-off primary rejected. Fail-before confirmed at paper
base. The earlier F5 ambiguity (newest committed manifest is the scripted smoke) is now
closed because scripted manifests are rejected, not accepted. Two remarks (not findings):
the mode match is skipped when a caller omits `memory_mode` entirely (the built runner
never does), and the default manifest search is lexicographic, see F11.

### 7. Runner phases, no retry, no redo, whitespace check end-to-end — PASS with F10

`phase()` writes `started_utc` before running and only marks `completed` after the body
returns; a restart with an incomplete entry raises `PhaseInterrupted`, which `_entrypoint`
maps to a "no automatic retry" STOP; a completed phase is skipped
(`ada_e1b_rerun2.py:81-99,316-328`). Tests cover both directions and the liveness
eligibility floor. `commit()` runs `git diff --cached --check` (excluding
`results/r1/**`, `experiments/r1/**`) before every commit
(`deepthought_batch1_resume.py:60-73`); the end-to-end test generates every Markdown/JSON
kind the runner commits from the fixtures in a temporary git repo and is non-vacuous: a
trailing blank line in a checked path aborts before any commit
(`test_ada_e1b_rerun2.py:346-409`). I additionally confirmed the DT4 analysis regenerates
byte-identically from a committed-inputs archive. Defect: `finish` is not checkpointed (F10).

### 8. `e1b_compare` — PASS

Code: `paired_memory_effect` draws one instance resample per iteration and indexes both
arms with it (`e1b_compare.py:127-136`); the test hand-reproduces the first shared draw
(`test_e1b_compare.py:55-82`) and the difference of the two contrasts is asserted equal.
The Bonferroni count is `m =` number of per-node memory effects (ALL excluded), stated in
the JSON and in the Markdown (`e1b_compare.py:395-419,302-315`); the fixture test pins
`m = 2` and the adjusted level. The readings section only prints the fixed
supported/inconclusive/opposite template; no narrative interpretation is emitted. The
two-arm fixture path says "not computed" explicitly rather than silently skipping.

### 9. Launcher pins the harness head and cannot start twice — PASS with F8

`--prepare` clones the harness, checks out the pin read from the paper clone, and verifies
`HARNESS_HEAD == PIN`; the runner re-verifies both checkouts against their origin heads and
against `HARNESS_PIN_RERUN2` (`ada_e1b_rerun2_launch.sh:120-128`,
`ada_e1b_rerun2.py:117-131`). `refuse_duplicates` rejects an existing `r1_e1b_rerun2` or
any `r1_ollama_*` session in both modes, the runner additionally refuses if the port or its
own Ollama session is live, and the tmux stubs tests cover the refusals. A concurrent
double `--start` cannot both win because tmux rejects the duplicate session name. Defect
F8: the harness suite's exit code is recorded but not used in the accept decision.

### 10. Fail-before / pass-after on at least two changes — PASS

1. F3: base `0f2d9e9` prints `config_seen_before: false`; head prints `true` with the new
   fields (my fresh runs, both repos' code as above).
2. D28 gate: the new gate tests fail at paper base `5f650be` (5 failed, including "DID NOT
   RAISE" for memory-off and the unexpected-kwarg errors) and pass at head (25 passed
   across the three new files).
3. Extra: the deterministic record comparison is identical base vs head; the new D27 test
   file cannot even be collected at harness base.

## Findings

### F7 — MAJOR — D28 novelty (and the D27 active hash) silently drops real editable constants on undeclared nodes; `digits_mlp` is wrongly failed

`r1/liveness/novelty.py:87-89` (`active_projection` → `_project_active_config`), harness
`src/autoresearch/control_plane/campaign.py:448-456` (`_effective_config_at` →
`build_effective_config`) and `:469-497` (`_project_active_config`), harness
`src/autoresearch/manager/hyperparam_edits.py:331-362,387-427`. `build_effective_config`
maps only `BATCH_SIZE`→`batch_size` and `MAX_ITER`→`max_iter` among `digits_mlp`'s five
editable symbols; `HIDDEN_UNITS`, `ALPHA` and `LEARNING_RATE_INIT` are absent, although
all three reach `run_benchmark` (`nodes/digits_mlp/train.py:13-27`). On an undeclared node
the code calls the resulting dict "the full configuration"
(`campaign.py:469-476`), but it is a partial projection.

Failure scenario (reproduced from committed artifacts, no new runs):
- The committed scripted smoke scores `digits_mlp` **7/20 FAIL**
  (`results/r1/engineering/liveness_scripted_20261014T075806Z/digits_mlp.json`;
  `equals_incumbent_trials = 13`). Replaying the same committed ledgers over the node's
  actual five editable constants finds **20/20** trials whose configuration differs from
  the incumbent and from every earlier configuration — the scripted proposer never
  repeated a configuration, yet the node is failed by criterion 2.
- On the DT4 ledgers the events source counts 58 of 120 digits trials as equal to the
  incumbent — exactly the 58 `HIDDEN_UNITS` edits, which are invisible to
  `build_effective_config` (my replay: 32/120 novel vs 8/120 reported; both FAIL, so the
  pinned verdict survives, but the pinned numbers are not reproducible by a genuinely
  independent recomputation).
- Consequence for the coming Ada run: `digits_mlp` and `tabular_mlp` are two of the four
  nodes gated by the D28 LLM memory-on liveness. DT4's LLM changed `HIDDEN_UNITS` in 58 of
  120 digits trials; under the current projection every such trial is recorded as
  `active_config_equals_incumbent=True`, so a genuinely novel proposer can be scored as
  stuck and the node excluded by the gate. (For declared OpenML nodes the projection is
  correct and my recomputation matches exactly.) The test purported to guard this
  (`test_d28_liveness.py:47-103`) shares `build_effective_config`, so it cannot catch it.

Rating MAJOR: it is the batched-out criterion itself that is mis-measured for two of the
four nodes the batch is built for, and the committed artifact already contains a wrong
verdict from it.

### F8 — MINOR — the launcher accepts a harness suite that exited non-zero without parsed FAILED/ERROR lines

`r1/scripts/ada_e1b_rerun2_launch.sh:74,82,87,152-153`. `write_prepare_json` computes
`unexpected` only from `^(FAILED|ERROR)` lines and sets `ok = not unexpected`;
`harness_rc` is stored in `prepare.json` but never used, and `--start` checks only `ok`
and `unexpected`. Scenario: `uv run python -m pytest` dies with an internal error, is
killed, or exits 4 (usage/collection crash writing no per-test lines); `prepare.json`
records `harness_tests.returncode != 0` yet `ok: true`, and `--start <batch>` launches the
batch as if the suite were clean.

### F9 — MINOR — an E1-snapshot resume never counts the replayed captured trial among "seen" and emits no `edit_novelty` for it

Harness `src/autoresearch/control_plane/snapshot.py:686-826` (`_complete_captured_trial`
commits the replayed E1 trial without a novelty event) and `:856-866,892-916` (the
continuation is seeded only from the snapshot, which was taken before the trial ran).
Reproduced (my probe `e1_resume_probe.py`): after resuming an E1 snapshot, the captured
proposal is replayed and evaluated (trial 1), then a later trial proposes the same
configuration; the event reports `config_seen_before: false` although that configuration
was evaluated earlier in the same resumed segment. Impact is contained — the E1b flow
snapshots only at E2 and D28 falls back to replay when any evaluated record lacks an
event — but the D27 flag is wrong for this path.

### F10 — MINOR — `finish` is not checkpointed, so restarting the runner re-runs it

`r1/scripts/ada_e1b_rerun2.py:58,81-99,293-328`; `deepthought_batch1_resume.py:253-290`
sets `state['steps']['STATUS']` but nothing reads it. Scenario: a run completes (the
six-phase `PHASES` tuple is exhausted and `finish(None)` writes and pushes a STATUS entry);
the operator restarts `ada_e1b_rerun2.py` in the same batch directory (e.g. after an SSH
drop); all six phases skip, and `finish(None)` appends a second "completed" STATUS block
and commits/pushes it again. The prompt lists `finish` as phase 8 and says a completed
phase is never redone.

### F11 — MINOR (latent) — the default liveness-manifest search is lexicographic by name, not by date

`r1/scripts/deepthought_batch1_resume.py:160-167`: `sorted(liveness_*/liveness.json)[-1]`.
Directory prefixes order `langgraph < llm < scripted` regardless of date, so with
`$R1_LIVENESS_MANIFEST` unset and both a passing `liveness_llm_<old>` and a newer failing
`liveness_langgraph_<new>` present, the older passing manifest is selected and the gate
passes on a stale verdict (the scripted direction is safe: scripted always sorts last and
is now rejected). Not reachable from the built Ada runner, which always sets the env var
before the arms, but the docstring's "newest" is wrong for mixed prefixes.

## What could not be verified

- **Ada-only behaviour**: the launcher on `ucrtasl`, GPU co-tenancy card selection, tmux
  lifetime, Ollama `OLLAMA_KEEP_ALIVE=-1`/full offload, and the digest check were reviewed
  statically and through stubbed tests only; no Ada session was used (session rule).
- **The accepted-failure set on Ada at the new head.** The launcher's list matches my
  Mac head failures (8) plus the 12 Oct author-approved `/bin/zsh` test, but the 12 Oct
  Ada STATUS entry also shows
  `TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` failing then
  (STATUS.md:163). That test passes in my Mac head run; if it still fails on Ada at the
  pinned head, `--start` will (correctly, but obstructively) refuse until the list is
  updated. I could not check Ada.
- **The `finish` restart duplication (F10)** was established by code reading, not by
  executing `finish` (it writes STATUS and pushes, which this review must not do); the
  phase mechanism itself is exercised by the tests.
- **The batch-4 Finish steps** (STATUS entry with DT4/smoke verdicts, compute estimate,
  review summary; push) are not present at the reviewed head `9dd245c` — by the batch
  prompt they follow this review and the correction round, so they were out of scope, not
  a defect. The only untracked file in the paper tree is
  `paper/tables/artifact_completeness_report.txt`, a generated file outside the commits.
- **`e1b_compare` on three real rerun arms and the paired memory effect on the actual
  Ada data**: only fixtures exist locally; the paired-bootstrap path was verified on the
  committed fixtures (DT4 as B, scripted as C, scripted copy as A) and by the
  hand-reproduced first draw.

## Summary

The D27 F3 fix, the D28 revision machinery, the gate wiring, the runner/launcher and
`e1b_compare` are implemented and tested broadly as specified; the fail-before/pass-after
evidence is real and reproducible, and the committed smoke is fully re-derivable. The
serious problem is F7: the "active/full" configuration used by the new criterion is the
narrow `build_effective_config` projection, which drops three of `digits_mlp`'s five
editable constants, so the committed scripted smoke wrongly fails `digits_mlp` (7/20 while
20/20 configurations were novel) and the Ada gate can exclude a live node. Four MINOR
findings (F8–F11) affect refusal robustness, an E1-resume flag edge case, `finish`
checkpointing and default manifest selection. I recommend fixing F7 before the Ada
rerun-2 (either map the node's editable constants into the effective config or treat an
undeclared node's full parsed editable configuration as its active configuration) and
re-pinning the DT4 digits numbers after a genuinely independent recomputation.

---

## Resolution (implementation agent, 14 October 2026)

One correction round, as required. Harness correction head `411c605` (pushed); paper correction head `0cb76a3` (pushed). The harness pin `r1/scripts/HARNESS_PIN_RERUN2` moves to `411c6054c8505f93a6429e2f9eed526952793882`.

| Finding | Severity | Status |
|---|---|---|
| F7 — novelty drops real editable constants; digits_mlp wrongly failed | MAJOR | **Fixed** (harness `411c605`, paper `0cb76a3`) |
| F8 — launcher ignores a non-zero harness/paper exit without parsed failures | MINOR | **Fixed** (paper `0cb76a3`) |
| F9 — E1-snapshot resume does not count the replayed captured trial | MINOR | **Fixed** (harness `411c605`) |
| F10 — `finish` is not checkpointed; a completed batch re-finishes | MINOR | **Fixed** (paper `0cb76a3`) |
| F11 — default liveness-manifest pick is lexicographic, not by date | MINOR | **Fixed** (paper `0cb76a3`) |

**F7.** The novelty configuration is now `_novelty_config`: `build_effective_config` extended, via `setdefault`, with every editable symbol the builder does not cover (undeclared nodes contribute all parsed editable constants). `_effective_config_at`, the `edit_novelty` hashes and flags, the snapshot-seeded sets and the paper replay (`r1/liveness/novelty.replay_tally`) all use it, so the two sources stay trial-by-trial consistent. Fresh evidence: at `ed55297` the probe prints `HIDDEN_UNITS` absent and the hash unmoved by an `HIDDEN_UNITS` edit, and DT4 digits replays as 8/120; at the correction head both are `True` and DT4 digits replays as **32/120**, exactly the reviewer's independent raw-constants count. The DT4 digits pin is updated to `(novel 32, evaluated 120, keeps 11)`; the verdict stays FAIL on novelty, as it must with memory off. The independent recomputation in `test_d28_liveness.py` no longer calls `build_effective_config` at all: it tracks the parsed editable constants as plain tuples, which is equivalent for an undeclared node and can detect the F7 class of bug. The scripted smoke was rerun on the corrected code into `results/r1/engineering/liveness_scripted_20261014T084101Z/` (ledgers force-added): all five nodes now PASS, with `digits_mlp` 20/20 and `tabular_mlp` 20/20 (previously 7/20 and 10/20), and `openml_wdbc` 19/20, resolving the reviewer's repro in the intended direction. New harness tests: an uncovered editable symbol moves the hash; the flags see an uncovered symbol (both fail at `ed55297`); the F9 test below.

**F8.** `write_prepare_json` marks `harness_rc != 0` with no parsed FAILED/ERROR lines (and a paper `r1-test` exit with no parsed failures) as `unexpected`, so `--start` refuses. The pinned-batch/binary/batch-root/remotes are now env-overridable (`R1_RERUN2_*` with the Ada defaults unchanged), which lets the launcher's `--prepare` path be tested off Ada: four stub tests cover the accepted-only case, an unknown failure, the crash-without-lines case, and a failing `r1-test`.

**F9.** `_complete_captured_trial` now returns the evaluated candidate's `(effective_sha256, active_sha256)` — taken before the non-keep restore — and `resume_campaign` unions them into the continuation seeds for E1 and E2 snapshots. The new harness test resumes an E1 snapshot, replays the captured proposal, then proposes the same configuration: `config_seen_before` is `True` at the correction head and was `False` at `ed55297`. The old-format marker test was updated accordingly: the captured trial is now legitimately seen inside the resumed segment, while a genuine pre-resume configuration still reports `False` with the `seen_before_resume: "unknown"` marker on the first event only.

**F10.** `_entrypoint` loads the checkpoints and, when all six phases and the STATUS entry are already complete, exits with `STOP: this rerun-2 batch already finished; nothing to do` instead of calling `finish` again. A test pins that a completed batch writes no second STATUS entry.

**F11.** The default manifest search sorts by the trailing UTC stamp in the directory name (fallback: directory mtime), not by path. A new runner test places an older passing `liveness_llm_*` beside a newer failing `liveness_langgraph_*` and asserts the newer, failing verdict is the one enforced (the lexicographic pick would have passed on the stale one).

**Re-run after the correction round.** Harness suite: `8 failed, 389 passed, 1 warning, 1 error` (same pre-existing set; the three new tests are the pass delta). Paper `r1/tests`: **141 passed**. `make test`: 212 / 6 / 12 OK. All new tests were shown to fail at the pre-correction heads (`ed55297` granular probe for F7/F9; paper `5f650be`/`9dd245c` fail-before logs for the P6/P7 suites).

**Open items carried forward (unchanged by this round).** The reviewer's unverifiable items stand: Ada-only behaviour, the Ada accepted-failure set at the pinned head (the 12 Oct STATUS lists one extra failing test on Ada that passes on the Mac; if it still fails there, `--start` will refuse by design and the operator must report), and the real three-arm comparison. The D4 amendment, D18, D21, D23 and the verify split policy remain open author decisions.
