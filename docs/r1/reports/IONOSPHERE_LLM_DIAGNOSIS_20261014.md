# Ionosphere LLM diagnosis — 14 October 2026

**Label: `ENGINEERING_ONLY`. Not evidence.** Read-only diagnosis of the degenerate
`openml_ionosphere` result in the DT4 LLM rerun. **AI-assisted**: written and executed by an
AI agent (opencode / deepseek-v4.1-flash) at the author's request; no human review. No LLM
calls, no GPU, no worker runs, no change to the harness, manager, prompts, nodes, PLAN or
RUNBOOK. No decision is recorded; the fix belongs to the author.

Sources (all read-only):

- LLM run `results/r1/pilot/E1b_20261013T151857Z` (PILOT; pinned `qwen2.5-coder:7b`;
  harness `9c4902d`): `provenance/ledgers/{roots,branches}/**/*.jsonl`, `points.json`,
  `provenance/snapshots/`.
- Scripted run `results/r1/pilot/E1b_20261012T161034Z` (PILOT; scripted stand-in):
  `roots/`, `points.json`, `records.jsonl`.
- Harness `~/Documents/autoresearch_harness` at `9c4902d` (`git show 9c4902d:<path>`).
- Ada, read-only: `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/r1_e1b_llm_work/`
  (per-trial `patch.diff`, `run.log`).

Reproducible tables: `r1/diagnostics/ionosphere_llm_diag.py`
(`python3 r1/diagnostics/ionosphere_llm_diag.py --q all`).

---

## Summary

The working hypothesis is **confirmed**. On `openml_ionosphere` the LLM edits only
`n_estimators` (90/120 root trials) and `max_depth` (30/120); under
`model_type: logistic_regression` the node's `_build_model` passes neither to
`LogisticRegression`, so the metric is bit-identical to the incumbent on **114/114** root
trials (100 %) and **720/720** branch trials. The strict keep rule (`delta > 0`,
`decision.py:54-66`) therefore never fires after trial 1: across 840 ionosphere trials only
the 6 first-valid metrics are kept and Δ̂ = 0 everywhere. The scripted proposer on the same
node/seeds edits only keys active for the current model and keeps 18/66 root trials
(27.3 %), which is why it found ρ = +0.0189 while the LLM finds 0. Decoding is **not**
deterministic (temperature 0.2, no seed): only 3/72 branch pairs agree across repetitions.

---

## Q1. What did the LLM propose on ionosphere?

Full per-trial tables are printed by the script (`--q 1`, ~840 rows). Summary:

| Set | trials | valid | with incumbent | metric bit-identical to incumbent | edited keys |
|---|---|---|---|---|---|
| six root ledgers | 120 | 120 | 114 | **114 (100 %)** | `n_estimators`=90, `max_depth`=30 |
| branch ledgers, new trials after each point | 720 | 720 | 720 | **720 (100 %)** | `n_estimators`=576, `max_depth`=144 |
| **total** | **840** | **840** | 834 | 834 (100 %) | `n_estimators`=666, `max_depth`=174 |

- **Invalid trials:** 0/840.
- **Kept:** 6/840 — exactly one per root (trial 1, "First valid metric becomes the current
  best"); every later trial is `discarded` with `delta = 0.0`.
- **Distinct proposals per root:** 3–4 (e.g. `s103`: `n_estimators 100→200`, `n_estimators
  200→300`, `max_depth 5→6`, `max_depth 5→10`). **Longest run of an identical proposal:** 3,
  3, 4, 9, 5, 7 for `s103, s113, s123, s133, s143, s153`.

Example, root `openml_ionosphere__s103` (ledger
`provenance/ledgers/roots/openml_ionosphere__s103/root_trials.jsonl`): trial 1
`n_estimators 100→200` kept (metric 0.930341, becomes best); trials 2–20 alternate
`n_estimators 200→300` and `max_depth 5→{6,10}`, all `valid`, all parsed `val_auc = 0.930341`
= incumbent, all `discarded`, `delta = 0.0`.

**Established by:** `structured_edit.symbol` and `parsed_metrics.val_auc` in every ledger
record; `current_best_before` = 0.930341 on every trial after the first.

---

## Q2. Are those edits inert under `logistic_regression`?

### (a) Which keys reach the model

From `nodes/openml_ionosphere/benchmark.py` at `9c4902d`:

| key | status under `logistic_regression` | source |
|---|---|---|
| `model_type` | **used** — selects the estimator and the OneHot `sparse_output` | `_build_model:224-248`; `_build_pipeline:204` |
| `C` | **used** — `LogisticRegression(C=...)` | `benchmark.py:227` |
| `class_weight` | **used** — `LogisticRegression(class_weight=...)` | `benchmark.py:228` |
| `max_iter` | **used** — `LogisticRegression(max_iter=...)` | `benchmark.py:229` |
| `scaler` | **used** — `StandardScaler`/`MinMaxScaler` step | `benchmark.py:188-191` |
| `imputer` | **used in code, inert here** — only the *categorical* imputer; ionosphere has no categorical columns, so that branch is never built | `benchmark.py:192-201` |
| `max_depth` | **ignored** — passed only to `RandomForestClassifier`/`GradientBoostingClassifier` | `benchmark.py:236, 245` |
| `n_estimators` | **ignored** — same | `benchmark.py:235, 243` |
| `learning_rate` | **ignored** — `GradientBoostingClassifier` only | `benchmark.py:244` |

The LR branch (`benchmark.py:225-231`) constructs
`LogisticRegression(C, class_weight, max_iter, solver="liblinear", random_state=SEED)`.
`solver`, `SEED` and the numeric imputer (`strategy="median"`, line 187) are fixed, so they
are not editable. **The node advertises nine editable symbols but only five (`model_type`,
`C`, `class_weight`, `max_iter`, `scaler`) can move the metric of this node** (four, if
`model_type` stays `logistic_regression`).

### (b) Did the LLM ever change an active key?

**No.** Across all 840 ionosphere trials the `structured_edit.symbol` is only `n_estimators`
or `max_depth`. `model_type`, `C`, `class_weight`, `scaler`, `imputer` and `max_iter` are
never edited (Q1 table). So the metric cannot move: it is the same `logistic_regression`
fit on the same split/seed every time.

### (c) Worker runs

Not run. (a) is definitive from the node code, and the 720 branch trials with bit-identical
metrics are direct empirical confirmation. The rule permits up to 10 CPU runs *only if (a)
leaves doubt*; it does not, so no `results/r1/engineering/ionosphere_diag_*` was created.

---

## Q3. What does the manager see?

The committed ledgers record only `llm_call` **counts** (tokens, latency, `parse_ok`), not
the prompt text. The prompt is nevertheless recoverable: `LangGraphManager._prepare_context`
is a pure function of the status/constants/memory, so it can be rebuilt and checked against
the ledger's `context_sha256`. Reconstructed trial 1 and trial 5 prompts of
`openml_ionosphere__s103` hash to `5544361c…` and `f12f4206…`, **identical to the ledger**.

- **Is `model_type` shown?** **Yes.** `_prepare_context` (`langgraph_manager.py:83-88`) lists
  every entry of `status.current_constants` (which is the filtered config, including
  `model_type`):

  > `Editable values currently in config.yaml (use exact names):`
  > `  model_type = logistic_regression`
  > `  C = 0.15`
  > `  max_depth = 5`
  > `  n_estimators = 100`
  > …

- **Is the LLM told which keys apply to the current model?** **No.** All nine editable values
  are listed flat, with no annotation of which are active for `logistic_regression`. The
  constraints (`langgraph_manager.py:130-134`) only say: "change exactly one listed value",
  "param must be one of the editable values listed above".

- **Does the history show that earlier edits left the metric unchanged?** **No.**
  `memory_mode` is `none`, so `MemoryContext.context_text` is the fixed four-line block
  (`memory/summarizer.py:63-71`):

  > `node=openml_ionosphere`
  > `budget_index=5`
  > `metric=val_auc direction=maximize`
  > `editable_paths=config.yaml`

  It contains no decisions, no metrics, no deltas. `memory_context_built` events confirm
  `compressed_chars` 98–99 for every ionosphere trial. The manager cannot see that its last
  19 edits produced Δ = 0.

- **Any instruction discouraging structural changes?** No explicit one. The prompt does carry
  a mandatory **AVOIDANCE RULE** (`langgraph_manager.py:92-102`) telling the model not to
  repeat a parameter change in the same direction, and the worked example is a numeric
  learning-rate change — but nothing forbids or deprioritises changing `model_type`, and the
  rule was ineffective here (the model repeated `n_estimators`/`max_depth` anyway).

---

## Q4. Is decoding deterministic?

- **Sampling settings at `9c4902d`:** `temperature = 0.2`
  (`langgraph_manager.py:293-313`, `configs/managers/langgraph_manager.json`), passed to
  `ChatOllama(model, base_url, temperature)` (`langchain_client.py:141-151`). **No `seed`,
  no `top_p`/`top_k`** — Ollama defaults. Non-zero temperature without a seed is not
  guaranteed deterministic.
- **Do identical ledger prefixes give identical proposals across repetitions?** Mostly not.
  Comparing the two repetitions (`r1` vs `r2`) of every branch, element by element over the
  new trials: **only 3/72 pairs are fully identical (4.2 %)**; the rest diverge, usually at
  the first or second new trial (distribution of first-divergence index 1–10). E.g.
  `openml_ionosphere__s103__b004__continue` agrees for new trials 1–5 then diverges at 6;
  `digits_mlp__s124__b008__continue` diverges at 10. So the LLM is *locally* stable on short
  prefixes but decoding is **not deterministic**.
- **`digits_mlp` repetition statistics** (`--q 4b`): 120 root trials, all valid, 114 with an
  incumbent, **22 (19.3 %)** candidate metrics bit-identical to the incumbent; edited keys
  `BATCH_SIZE`=62, `HIDDEN_UNITS`=58; distinct proposals per root 3–8, longest identical run
  3–13. Unlike ionosphere, digits edits *do* move the metric (`HIDDEN_UNITS 64→128` →
  `val_score 0.9694`; `BATCH_SIZE 64→128` → 0.9638), but the LLM still repeats the same
  losing edit because the incumbent never changes and no outcome is fed back.

---

## Q5. How does the scripted proposer differ?

The scripted stand-in is `r1/headroom/scripted_manager.py`. Its numeric edits are restricted
to `OPENML_ACTIVE[model_type]` (`:34-38`) — for `logistic_regression` only `C` and `max_iter`
— plus a 30 % chance of a categorical switch among `model_type`, `class_weight`, `scaler`
(`:39, 69-74`). It therefore **cannot edit an inert key by construction**.

Per-trial scripted proposals are not in the committed artifacts (the scripted run wrote
`root_trials.jsonl` only under the ephemeral `/tmp/dw_r1/e1b` work dir; RUNBOOK line 169
records the loss). They are, however, recoverable: the proposer is deterministic (RNG keyed
by `(seed, repetition, budget_index)`), and the committed `points.json` carries the editable
snapshot hash at each E2 point. Replaying the proposer and searching keep/discard decisions
yields a **unique** match to all three snapshot hashes for each of the six roots
(`n_matches = 1` in every case; the recorded `n_keeps` disambiguates the rest).

Scripted ionosphere roots, trials 1–12 (`--q 5`):

- **edited keys:** `C`=24, `max_iter`=18, `class_weight`=9, `scaler`=7, `model_type`=6,
  `max_depth`=4, `n_estimators`=3, `learning_rate`=1. `max_depth`/`n_estimators`/
  `learning_rate` appear **only after a `model_type` switch**, i.e. when they became active.
- **keeps:** 18/66 trials 1–11 (27.3 %), 12 of them after trial 1. The LLM keeps 6/66 (all
  at trial 1, the first valid metric) and **0/60 after trial 1** on the same trials.
- The scripted run's aggregate ρ on ionosphere is **+0.0189** (`HEADROOM_PILOT_20261012.md`,
  line 37); the LLM run's ρ is **0.0000**.

---

## Q6. Does anything else explain Δ̂ = 0?

Each candidate ruled out with evidence:

| candidate | verdict | evidence |
|---|---|---|
| metric-parsing default | **ruled out** | `metric_parser.parse_val_auc` returns `{}` (not 0) when `VAL_AUC=` is absent (`metric_parser.py:12-16`); `validity_checks` includes `metric_present`, and all 840 trials are `valid` with an explicit parsed value (0.930341 / 0.894737 / …). |
| incumbent read error | **ruled out** | `current_best_before` is 0.930341 on every ionosphere root trial after trial 1 and equals the prior kept metric; `delta_vs_best = candidate − best = 0.0` (`decision.py:54`). No drift. |
| edit never applied (patch present, file unchanged) | **ruled out** | Ada `…/openml_ionosphere__s103/art/trial-004/patch.diff` shows `max_depth: 5 → 6`; the committed snapshot `…/E2_b004/editable/config.yaml` reads `max_depth: 6, n_estimators: 200` while `incumbent/config.yaml` reads `max_depth: 5`; `node_state/artifacts/run.log` shows `MODEL=logistic_regression / VAL_AUC=0.930341`. The file changed and the worker ran. |
| worker reusing a cached result | **ruled out** | every trial has a distinct `timestamp_start` (20/20) and its own `patch_ref`/`run.log`; `patch_hash` repeats only because the *content* repeats (the LLM re-issues the same diff). On `digits_mlp` the same worker returns three distinct values (0.9777, 0.9694, 0.9638) for distinct edits, so there is no global cache. |

The residual explanation is exactly Q2: the metric is deterministic in the inputs the LLM
changes, and the LLM changes only inputs that are not used.

---

## Implications

- **E1b (this pilot).** The ionosphere headroom measured under the LLM proposal law is a
  measurement of a **frozen config**, not of the LLM's search ability: Δ̂ = 0, `n_keeps` = 1,
  every leaf Y = 0, ρ = 0. The E2 STOP memo's claim that "the LLM rerun shows large headroom"
  is *not* supported on ionosphere — the LLM headroom there is 0, and the difference from the
  scripted ρ = +0.0189 is attributable to the proposal law, not to the decision policy. The
  `digits_mlp` half is less degenerate (the metric moves) but still shows the same
  "re-propose the same losing edit" pathology, so its headroom is also suspect.
- **E3.** Any E3 comparison that scores the LLM manager against a scripted/random proposer
  on the OpenML pool will be confounded unless the proposer is constrained to active keys or
  the node stops advertising inert symbols. A manager that cannot observe outcomes cannot
  learn, regardless of the policy layered on top.
- **OpenML pool.** Every node of this template (`openml_ionosphere`, `openml_credit_g`,
  `openml_wdbc`, …) advertises the same nine `editable_symbols` and the same
  `model_type`-dependent `_build_model`, so the same degeneracy is available on every
  OpenML node whose start `model_type` is `logistic_regression`. It is not ionosphere-specific.

---

## Fix options for the author (choose one; not a prescription)

1. **Expose only the keys active for the current `model_type`.** The manager lists, and the
   worker accepts, only `{model_type, C, class_weight, max_iter, scaler}` when the incumbent
   is `logistic_regression` (and the corresponding sets otherwise). *Cost:* small; a filter
   in `_prepare_context`/`_extract_structured_edit` and in the node's validity check.
   *Changes the proposal law:* removes inert edits entirely.
2. **Tell the manager which keys are active.** Keep the flat list but annotate each key
   "active"/"ignored for the current model_type". *Cost:* small (prompt text only).
   *Changes the law:* soft — the model may still choose an inert key.
3. **Surface "metric unchanged" in the history.** Raise `memory_mode` above `none` so the
   manager sees each trial's metric/delta (or at least a "no improvement" flag). *Cost:*
   small; changes the prompt and the memory context. *Changes the law:* lets the model learn
   from outcomes; addresses the digits pathology too.
4. **Set a sampling temperature and seed for the manager.** E.g. `temperature=0.0` (greedy)
   or `temperature=0.2, seed=…`. *Cost:* trivial; a D15-scope decision. *Changes the law:*
   makes repetitions reproducible; does not by itself stop inert edits.
5. **Leave it as is and treat inert edits as part of the proposer.** *Cost:* none.
   *Changes the law:* nothing — but the author must then report ionosphere headroom as 0 and
   not attribute the scripted/LLM gap to the decision policy.

Options 1 and 3 are complementary and target the two distinct defects (inert keys on
ionosphere; no outcome feedback on both nodes).
