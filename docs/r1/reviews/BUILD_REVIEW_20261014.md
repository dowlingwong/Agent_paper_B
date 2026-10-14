# Build review — batch 3 (D24–D28), 14 October 2026

*Independent, fresh-context, AI-assisted review of the third R1 build batch (Paper B, route R1). The reviewer had no access to the implementer's reasoning or notes; every claim below was re-checked against the diffs, the code at the heads, the test logs, or a fresh run. The reviewer edited no code in either repository, made no commit and no push; this file is the only write.*

**Repositories under review**

| Repo | Branch | Base | Head |
|---|---|---|---|
| `~/Documents/autoresearch_harness` | `r1` | `9c4902d0d8776f18a081e1ff2478d651fc7096c1` | `ff6191174b35a78a3f2625a8ff4aa8e43378c805` |
| `~/Documents/agent_paper_B` | `main` | `0a3f284a640b57ec0a180c34ba73b859ad1ec0ef` | `24b97ebb785c40ceffeb56ab99a02d9f5f2c5652` |

The supplied patch files are byte-identical to `git diff <base>..<head>` in both repositories (sha256 compared). Time alignment note: the scripted liveness smoke committed in the paper repo was produced with the harness at `4540fa5` (recorded in its manifest), while the harness head under review is `ff61911`; the extra commit only changes the display of a missing summary metric and cannot affect a scripted, `memory_mode="none"` run.

---

## 1. Are D24–D28 implemented as written?

**Verdict: implemented, with one MAJOR deviation on D25 (finding 1) and five MINOR findings (2–6).**

- **D24** — summary line uses `node_spec.metric_name` (`summarizer.py:130-136`), a 0.0 metric is shown (`in`/`.get`, not `or`), `_best_strategy_line` respects `metric_direction` (`summarizer.py:149-167`). The collector takes `memory_mode` from the manifest with default `none` and no literal call-site value (`r1/headroom/e1b_collect.py:116-131, 289-291, 309-313`). Snapshot continuation carries the root's mode (`snapshot.py:410, 845, 867`). Fine.
- **D25** — declaration mechanism (`nodes/active_keys.py`), prompt filtering (`campaign.py:210-216`), rejection before any run with a 2-revision limit charged to the LLM cap (`campaign.py:1134-1191`, `MAX_INACTIVE_KEY_REVISIONS=2`), model_type-dependent active set (test `test_active_set_follows_a_model_type_change_in_the_workspace`), undeclared-node hashes unchanged (see §4). **However**: the declared fixed point "its proposal sequence for existing seeds must stay identical" does not hold in the live campaign (finding 1).
- **D26** — deterministic SHA-256 seed from (campaign, budget index, repetition, revision attempt) (`langgraph_manager.py:46-62`), recorded in the `llm_call` event via `llm_meta["seed"]` (`langgraph_manager.py:479-486`, `campaign.py:299-314`), temperature stays 0.2. The `revision_attempt` term is one component beyond the row's `(instance, trial index, repetition)`; it is required so a revision is not a repeat of the seeded call it is revising, and it defaults to 0 on the primary call. I do not count it as a deviation.
- **D27** — flags in a separate `edit_novelty` event, records untouched (`campaign.py:1422-1447`; test `test_records_are_unchanged`). The E1 skip arm exists and is labelled (`r1/controllers.py:29, 82-155`). Two edge gaps: resumed campaigns (finding 3) and dry campaigns (finding 4).
- **D28** — criteria constants and evaluation (`r1/liveness/check.py:30-36, 101-137`), per-node JSON/Markdown, `--offline`/`--run` modes, and the gate wired into the batch runner before any collector call (`r1/scripts/deepthought_batch1_resume.py:146-167`; test `test_collect_is_gated_before_any_collector_call`). The committed scripted smoke is `memory_mode="none"` (`results/r1/engineering/liveness_scripted_20261014T064533Z/manifest.json`); the D28 LLM/memory-on check is explicitly out of this batch's scope, so this is a note, not a finding.

Nothing outside the D24–D28/A1 scope was found in the diffs (no changes to node metrics, no history rewrite, `results/r1/pilot/` untouched).

## 2. Default-path byte-identity; are the regression tests real or vacuous?

**Verdict: real for the prompt, records and `none` mode; the scripted-proposer regression test is vacuous with respect to the actual change (finding 1).**

- **Undeclared-node prompt**: `UNDECLARED_PROMPT_SHA256` in `tests/stage2/test_r1_d25_active_keys.py:31` was re-derived by running the *base* `_prepare_context` on the same fixed status/memory: `dacd99999c6b1b59c9e582c938a456276bd27964a4910c724623ce7f5ccec822` — exact match. The test would fail if the default prompt changed.
- **`memory_mode="none"`**: `test_none_mode_output_is_unchanged` pins the four-line block byte for byte; it passes on the base code too (it is a guard, not a fail-before test).
- **Old manifests**: `manifest.get("memory_mode", "none")` at both scheduling sites (`e1b_collect.py:290, 313`) and the `run_root` default; `test_missing_memory_mode_means_none` passes.
- **Scripted proposer**: the golden is genuinely pre-change (base-code replay reproduces it; §8), but both base and head code reproduce it, so the test cannot fail on the changed path. See finding 1 for the live divergence.
- **Records**: unchanged (`test_records_are_unchanged`; the only added record text is the D25 skip rationale on the new skip path). **Events**: on the default path only `edit_novelty` is new. `proposal_rejected_inactive_key` also exists, but only on nodes with a declaration when an inactive key is actually named; it is required by the batch task H2 and does not appear on the default path.

## 3. Information leaks

**Verdict: none found.**

- Memory is built from `existing_records + records` only, i.e. this campaign's completed prior trials (`campaign.py:1092`); no sibling or future record is passed.
- `_summary_line` exposes only the node metric, decision, proposal summary, delta, rationale and failure category (`summarizer.py:118-146`); under `append_only_summary` nothing else is injected. A missing metric prints `missing` and never a different parsed metric (D24 follow-up), verified by `test_a_missing_node_metric_never_leaks_another_parsed_metric`.
- `ManagerStatus` carries no audit/test fields (`manager/base.py:10-21`); `current_best_metric` is the validation metric. Audit metrics live in separate audit files and never enter `TrialRecord.parsed_metrics` as the node metric.
- The `llm_call` event payload contains latency/tokens/seed/parse flags only.

## 4. D25 specifics

**Verdict: enforcement, revision limit, cap accounting and active-set update verified; the scripted-sequence clause fails (finding 1).**

- **No worker run on an inactive key**: the loop runs before the pending guard and the worker call; tests `test_inactive_key_is_rejected_before_any_worker_run` (worker runs once, for the revised, active edit), `test_exhausted_revisions_skip_with_reason_and_spend_no_run` (0 runs) and `test_llm_cap_stops_revisions_before_the_limit` pass. No in-repo path was found that runs a worker for a detected inactive key.
- **Revision limit and cap**: `MAX_INACTIVE_KEY_REVISIONS = 2`; each revision consumes one LLM call after the call and the loop checks `_llm_cap_reached` first (`campaign.py:1142-1176`). With `max_llm_calls=1` the loop performs 0 revisions; with the cap off it performs exactly 2 and then skips. The initial call is charged at `campaign.py:1128-1131`.
- **Active set follows `model_type`**: `test_active_set_follows_a_model_type_change_in_the_workspace` rewrites `config.yaml` to `gradient_boosting` and observes `class_weight` out / `learning_rate` in.
- **Undeclared-node hashes unchanged**: re-derived `build_node_research_context` hashes (which hash `node_spec.to_dict()`) on base and head: `lr_synthetic`, `mlp_synthetic`, `digits_mlp` identical; `openml_ionosphere` changed by design (declaration added). `to_dict` pops an empty declaration (`spec.py:110-131`).

## 5. D26 specifics

**Verdict: verified.**

- Derivation stable, non-negative 32-bit, differs across trial, repetition, revision and instance (`test_seed_differs_across_trials_repetitions_and_revisions`).
- Logged in the `llm_call` event (`test_llm_call_event_carries_the_seed`).
- Reaches the pinned backend: with `langchain-ollama 1.1.0`, `ChatOllama(seed=...)` stores `seed` and `_chat_params` maps it into the request `options` dict (`"seed": self.seed`); the harness test asserts `model.seed == 12345` and `temperature == 0.2`. A live Ollama round-trip was not possible under the no-LLM rule (see "could not be verified").

## 6. D27 specifics

**Verdict: correct on the tested edges; MINOR gaps on resumed campaigns (finding 3) and dry campaigns (finding 4). Records unchanged.**

- First trial: `incumbent_effective` is the workspace start config, `seen_effective` empty → all flags false unless the first edit is a no-op (`test_flags_on_the_constructed_sequence`, T1).
- After a keep: `incumbent_effective = candidate_effective` (`campaign.py:1557-1558`), so a repeat of the new incumbent is `config_equals_incumbent=True` (T5), and the pre-break restore on a discard keeps the old incumbent (T2/T3).
- After a restore: discarded/invalid trials call `_restore_editable_state` and do not update the incumbent; the E0 demote path re-reads the workspace (`campaign.py:1088-1090`). The demote path is verified by code reading, not by a test.
- `metric_identical_to_incumbent` uses the pre-trial `current_best` and a bit-exact float compare (`campaign.py:1440-1444`), correct on the tested sequence.

## 7. D24/P1 — collector and branch continuations

**Verdict: verified.**

- No literal memory mode remains at any collector call site (grep of `r1/headroom/e1b_collect.py`; the only literals are the default `"none"` of the function argument and of the new-run manifest assembly).
- The E2 snapshot stores `memory_mode` (`snapshot.py:90, 263, 339`) and `resume_campaign` continues with it (`snapshot.py:845, 867`).
- `test_branch_continuation_inherits_the_root_memory_mode` fails on the base (run_root rejects the kwarg) and passes at head: the snapshot is `append_only_summary` and every branch record carries it.

## 8. P2 — golden file

**Verdict: the golden is genuinely pre-change and covers categorical switches, but its regression range misses the change that D25 actually introduces in the live path (finding 1).**

- Golden `harness_commit` is `9c4902d0…` (`r1/tests/data/scripted_proposal_golden_E1b_20261012T161034Z.json`); the base-code replay (paper_base manager + harness_base utilities) reproduces all three golden tests; the head repro also passes (107-test suite).
- Symbols covered: `model_type` 33, `class_weight` 42, `scaler` 36 occurrences over 12 instances × 3 repetitions × 20 indices. The categorical family is covered.
- What is *not* covered: the state where a categorical key is inactive (e.g. `class_weight` after a kept switch to `gradient_boosting`), because `replay()` constructs `ManagerStatus.current_constants` directly (`scripted_golden.py:55`) and never goes through `_manager_status`, which is where the filtering happens.

## 9. P4 — liveness

**Verdict: criteria, offline acceptance and gate verified; one MINOR reproducibility gap (finding 5).**

- Criteria: keep after trial 1 (`kept and budget_index > 1`), metric-different fraction with a strict `< 0.5` fail and a guard against the empty-comparable vacuous pass, invalid rate strictly `< 0.30` (`check.py:101-137`). The metric-different fraction is computed over comparable trials (metric present and incumbent present); for every committed verdict the choice of denominator (comparable vs all trials) does not change pass/fail (digits 92/114 = 0.807 vs 92/120 = 0.767; wdbc 7/18 = 0.389 vs 7/20 = 0.35; ionosphere 0 in both).
- Offline test on committed ledgers (`results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots`, tracked in git): re-run reproduces `openml_ionosphere` FAIL with `keep_after_trial_1 = 0`, `metric_diff_fraction = 0.0` (0/114), `invalid_rate = 0.0`, n = 120; `digits_mlp` PASS with 11 keeps and 0.807. This matches `test_d28_liveness.py` exactly.
- The committed scripted smoke is reproducible from its on-disk ledgers (re-evaluated: identical except `generated_utc`/`run_manifest`). It records `openml_wdbc` FAIL (`metric_diff_fraction` 7/18 = 0.389) and the other four nodes PASS.
- Gate: `require_live` raises `STOP:` for missing/failed nodes, accepts the report and bare-verdict formats, and is called inside `collect` before any collector command (test monkeypatches `cmd` and asserts zero calls).

## 10. Fail-before / pass-after spot checks

**Verdict: verified on both repositories by running the head's new tests against the base code.**

- Harness base + new tests: `5 failed, 3 passed, 2 errors` — `test_r1_d24_summary.py` fails on the node-metric, 0.0, missing-metric and minimise tests; `test_r1_d27_novelty.py` fails on 0 `edit_novelty` events; `test_r1_d25_active_keys.py` and `test_r1_d26_seed.py` are collection errors (missing `MAX_INACTIVE_KEY_REVISIONS`, `manager_seed`). The three passes are expectations met by both revisions (maximise direction, `none` output, records unchanged); none of them distinguishes the revisions.
- Paper base + new tests: `4 failed, 4 passed, 3 errors` — the D24 collector tests fail with `TypeError`/missing `seed_policy`/`_repetition`; `test_d27_noop_skip.py`, `test_d28_gate.py` and `test_d28_liveness.py` are collection errors (missing modules); `test_scripted_golden.py` passes on the base, which is the positive evidence that the golden predates the change.
- Head suites: harness `8 failed, 376 passed, 1 warning, 1 error` (identical failing set to the baseline `349 passed`); paper `r1/tests` `107 passed`; `make test` `212 / 6 / 12 OK` (identical to baseline).

---

## Findings

### F1 — MAJOR — the D25 change silently alters the scripted proposer's live campaign sequence, and the golden test cannot detect it
`src/autoresearch/control_plane/campaign.py:213-216` filters `ManagerStatus.current_constants` down to the active set; `r1/headroom/scripted_manager.py:95, 97-102` reads that filtered mapping and computes its categorical edit only `if key in consts`; `r1/headroom/scripted_golden.py:55` builds the replay status directly with unfiltered constants, bypassing `_manager_status`.

Concrete failure scenario (reproduced with the real campaign code, same node, seed, worker and keep rule on both revisions): start `openml_ionosphere` from the committed config, seed 123, repetition 0, every edit kept. Trial 1 switches `model_type` to `gradient_boosting`. At trial 4 the base proposes `class_weight balanced -> null` (the inert edit the pre-change law issues at that point; the committed golden contains that draw); the head proposes `n_estimators 100 -> 235`. The RNG stream was identical up to that draw, and every later proposal diverges. A manager-level simulation over the six E1b ionosphere seeds × three repetitions shows divergence in 8/18 pairs; `openml_wdbc` diverges in 6/18. The base and the head both reproduce the committed golden bit for bit, which shows the golden exercises a code path that is unchanged by construction and therefore cannot fail on this defect. D25's sentence "its proposal sequence for existing seeds must stay identical" is not satisfied, and the claim in `docs/r1/reports/NODE_KEY_AUDIT_20261014.md:129` that the stand-in "still draws `class_weight` … [and] the control plane now rejects the proposal" is unreachable for the scripted campaign: with the filtered status the draw never happens, so no rejection is ever emitted for the scripted arm. Consequence: a rerun of the archived E1b scripted seeds (`E1b_20261012T161034Z`) no longer produces the same proposals, and the invariance the batch was required to prove is untested.

### F2 — MINOR — the D25 revision loop passes `revision_attempt` without the accepted-kwarg guard used elsewhere
`src/autoresearch/control_plane/campaign.py:1160-1169` calls `propose_next_trial(..., revision_feedback=..., revision_attempt=...)` while the loop condition at `:1145` only checks `_accepts_revision_feedback`. The E1 revise path guards the same kwarg (`campaign.py:1290-1292`).
Failure scenario: a manager class that accepts `revision_feedback` but not `revision_attempt` (e.g. any third-party manager written against the pre-batch `LangGraphManager` signature) used on a declared node: the first inactive-key naming raises `TypeError: propose_next_trial() got an unexpected keyword argument 'revision_attempt'`, aborting the campaign mid-run instead of skipping the trial. No in-repo manager is affected (the only non-deterministic one accepts both; the others are deterministic and never enter the loop).

### F3 — MINOR — `config_seen_before` is blind to configs evaluated before a resume
`src/autoresearch/control_plane/campaign.py:1006-1007` starts `seen_effective` empty and never seeds it from `existing_records`; the flag is emitted at `:1437-1439`. Failure scenario (reproduced): trial 1 of a ledger evaluates `lr_synthetic` at `LEARNING_RATE=0.002` and discards it; the same ledger is resumed and the next trial proposes `LEARNING_RATE=0.002` again; the `edit_novelty` payload is `{"config_equals_incumbent": false, "config_seen_before": false, "metric_identical_to_incumbent": false}` although D27 defines the flag as "equal to an earlier evaluated config". This is exactly the shape of the E1b branch continuations (`snapshot.py:862-871` continues over the restored ledger with `horizon=200` in `run_leaf`), so duplicate counters computed from these events undercount branch waste.

### F4 — MINOR — dry campaigns emit no `edit_novelty` flags
`run_dry_campaign` (`campaign.py:1597-…`) has no D27 instrumentation: D27's "record-only flags on every trial" is implemented only in `run_real_campaign` (`campaign.py:1422-1447`). Failure scenario: a dry campaign with N evaluated trials produces zero `edit_novelty` events, so any offline waste counting over dry ledgers is impossible. The R1 data collection uses the real path, so the practical impact is limited to synthetic runs.

### F5 — MINOR — the committed scripted liveness report cannot be re-derived from the repository, and the gate will read it for LLM runs
`results/r1/engineering/liveness_scripted_20261014T064533Z/liveness.json` records its inputs as absolute local paths (`/Users/wongdowling/…`) to `ledgers/**/root_trials.jsonl`, which `.gitignore:49` (`*.jsonl`) excludes from git; only the derived reports are committed. A fresh checkout cannot re-run `--offline` on the smoke ledgers or check the pass/fail table. In addition, the D28 gate defaults to the newest `results/r1/engineering/liveness_*/liveness.json` (`r1/scripts/deepthought_batch1_resume.py:159-162`); that newest manifest is this scripted, `memory_mode="none"` run, so the gate cannot distinguish a scripted smoke pass from the LLM/memory-on check D28 describes. (The LLM check is explicitly a later prompt, so this is a latent ambiguity, not a defect of this batch.)

### F6 — MINOR — an Anthropic-backed `LangGraphManager` now fails on every proposal
`src/autoresearch/llm/langchain_client.py:189-190` raises `ValueError` when a seed is supplied for provider `anthropic`, and `LangGraphManager.propose_next_trial` always passes a seed for the real backend (`langgraph_manager.py:410-423`). Failure scenario: any caller that constructed `LangGraphManager` for an Anthropic model before this batch now raises on the first proposal; the batch changed a provider path it was not asked to touch. No test covers it. The pinned R1 path is Ollama, so the practical exposure is outside R1.

---

## What could not be verified

- A live Ollama HTTP round-trip of the seed (no LLM calls allowed in this review). Verification stops at `ChatOllama(seed=…)` storing the field and `langchain-ollama 1.1.0` mapping it into the request `options`.
- There is no dedicated golden for the default-path *event stream* of undeclared nodes; byte-identity outside `edit_novelty` is argued from code reading, the unchanged pre-existing suite and the record-level tests, not from an event-by-event golden.
- The D27 demote/restore edge case was verified by code reading only; no test exercises an E0 demote followed by an `edit_novelty` flag.
- The D28 LLM liveness run and the memory-on primary arm (both explicitly deferred to a later Ada prompt), and therefore whether the committed scripted/none smoke is what the author intends the gate to consume.
- The `imputer` activity claims for `openml_bank_marketing` and `openml_credit_g`: no OpenML feature metadata exists in the repository and the audit report itself flags them for the author.
- Whether the author accepts the scripted-sequence change documented in F1 as a deliberate consequence of showing only active keys (the row currently says it must not change).

---

## Resolution (implementation agent, 14 October 2026)

One correction round, as required. Harness correction head `0f2d9e9` (pushed); paper correction head `e2653b5`.

| Finding | Severity | Status |
|---|---|---|
| F1 — D25 changes the scripted live proposal sequence; golden blind to it | MAJOR | **Fixed** (harness `0f2d9e9`, paper `e2653b5`) |
| F2 — unguarded `revision_attempt` kwarg in the D25 revision loop | MINOR | **Fixed** (harness `0f2d9e9`) |
| F3 — `config_seen_before` blind to pre-resume configs | MINOR | Not fixed (reason below) |
| F4 — dry campaigns emit no `edit_novelty` | MINOR | Not fixed (reason below) |
| F5 — scripted smoke not re-derivable; gate could read a scripted manifest | MINOR | **Fixed** (paper `e2653b5`) |
| F6 — Anthropic-backed manager raises | MINOR | **Fixed** (harness `0f2d9e9`) |

**F1.** Active-key filtering moved out of `_manager_status` into `_prepare_context` (`langgraph_manager.py`), so the scripted stand-in reads the same unfiltered constants as before and its live proposal sequence is unchanged; the campaign still rejects an inactive-key proposal before any worker run (the scripted arm's inert `class_weight`-under-`gradient_boosting` draws now actually reach that rejection, which the review correctly noted was previously unreachable). A second golden (`r1/tests/test_scripted_live_golden.py`, data `scripted_live_golden_E1b_seeds.json`) runs the real campaign path and was generated from the pre-change harness `9c4902d`: it fails against the reviewed head `ff61911` and passes at `0f2d9e9`. An independent base-vs-head live comparison over the reviewer's scenario (ionosphere s123 r0/r1, wdbc s100 r0/r1, ionosphere s103 r0/r1) is byte-identical after the fix. New harness tests also pin the invariant: `_manager_status` keeps the full editable set and the prompt follows `model_type`.

**F2.** The D25 revision loop now passes `revision_attempt` only when the manager accepts that keyword (`_accepts_kwarg`), matching the E1 revise path; a new test uses a manager that accepts `revision_feedback` only and verifies the revision completes with no `TypeError`.

**F3.** Not fixed. The effective configs of trials evaluated before a resume cannot be reconstructed from the ledger: `TrialRecord` stores no config or edit for unstructured proposals, and the pre-resume incumbent chain is not recoverable from the copied ledger alone. The flags are record-only (D27) and change no decision, so the consequence is an undercount of `config_seen_before` on resumed segments; the limitation is documented at the `seen_effective` initialization. A real fix would add a per-record effective-config hash to `TrialRecord`, which changes record bytes and needs an author decision.

**F4.** Not fixed, deliberately. The dry worker has no workspace, so there is no effective config to compare; emitting the flags from empty configs would report `config_equals_incumbent=True` for every dry trial, which is worse than silence. The real path is the one R1 uses for data collection. The choice is documented in `run_dry_campaign`'s docstring; if the author wants dry-path flags, that is a design decision.

**F5.** Fixed as suggested. `evaluate_ledger_paths` and the `--run` flow record `manager_kind`; the runner gate accepts only a manifest with `manager_kind: langgraph` and raises `STOP:` otherwise (the committed scripted smoke manifest is correctly rejected). The smoke run's ledgers are force-added (`git add -f`, the repo ignores `*.jsonl` by default; the DT4 provenance ledgers are tracked the same way), so the committed report is re-derivable from the checkout. Tests cover the explicit-scripted rejection, the missing-kind rejection, and the newest-manifest selection.

**F6.** Fixed. `LangGraphManager._resolve_llm` passes no seed for provider `anthropic` (D26 is an Ollama seed); the pre-batch unseeded behaviour is restored for that provider. `_build_chat_model` keeps its explicit `ValueError` for direct callers that demand a seed from Anthropic. A test pins that the manager passes `seed=None` for an Anthropic config.

After the correction round: harness `8 failed, 380 passed, 1 error` (identical known failing set to the `349 passed` baseline); paper `r1/tests` `109 passed`; `make test` `212 / 6 / 12` OK. The two open MINOR findings (F3, F4) and the audit's author flags (`imputer` on `openml_bank_marketing`/`openml_credit_g`; `resnet_trigger` configuration-dependent inert keys; `autoresearch_linux` missing node directory) go to the author.
