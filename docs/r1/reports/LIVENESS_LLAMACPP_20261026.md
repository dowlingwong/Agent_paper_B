# D28 LLM liveness on the eight D21 nodes under llama.cpp — 26/27 October 2026

AI-assisted (Claude, implementation agent on deepthought). **ENGINEERING_ONLY, not evidence.**
Authority: `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phase 6 (RUNBOOK A.7), PLAN §10 D28 (revised criterion 2,
14 Oct), R1-INFER-LLAMACPP, R1-SCHEMA, R1-DT-PIN.

## Verdict: 4 of 8 nodes pass. **STOP — the author decides.**

Per the runbook, a failing node is neither repaired nor dropped. This report is a read-only
diagnosis. No node list, criterion, threshold, seed or pinned value was changed.

| Node | D28 | Failed criterion | Active novelty (≥ 0.5) | Invalid rate (< 0.3) | Keeps after trial 1 (≥ 1) |
|---|---|---|---|---|---|
| `digits_mlp` | **pass** | — | 0.90 (18/20) | 0.00 | **10** |
| `tabular_mlp` | **pass** | — | 0.76 (16/21) | 0.048 | **9** |
| `openml_credit_approval` | **pass** | — | 0.60 (12/20) | 0.00 | **1** |
| `openml_ionosphere` | **pass** | — | 0.70 (14/20) | 0.20 | **1** |
| `openml_breast_w` | **fail** | `keep_after_trial_1` | 0.60 (12/20) | 0.10 | 0 |
| `openml_sonar` | **fail** | `keep_after_trial_1` | 0.75 (15/20) | 0.05 | 0 |
| `openml_blood_transfusion` | **fail** | `keep_after_trial_1` | 0.65 (13/20) | 0.20 | 0 |
| `openml_wdbc` | **fail** | `keep_after_trial_1`, `invalid_rate` | 0.50 (10/20) | **0.30** (fails `< 0.3` exactly) | 0 |

**Every node passes `active_novelty_fraction`**, so the manager is not repeating itself into
inertia. Seven of eight pass `invalid_rate`. The whole failure is concentrated in
`keep_after_trial_1`, and on one node in a boundary `invalid_rate`.

## How it was run

The runner's own liveness command, at the configured liveness size, against the batch's own real
`llama-server` started with the pinned config values:

```
python -m r1.liveness --run --manager langgraph --memory-mode append_only_summary \
  --nodes digits_mlp tabular_mlp openml_breast_w openml_ionosphere openml_wdbc \
          openml_credit_approval openml_sonar openml_blood_transfusion \
  --instances 2 --runs 10 --transport-max-attempts 3 \
  --manager-model llamacpp/r1-manager --proposal-schema manager_proposal/v1 \
  --out results/r1/engineering/liveness_llamacpp_20261026T230913Z --work <local scratch>
```

| Item | Value |
|---|---|
| Harness | `897d83c8efa364ec2fdd37288241cc42e01d7274`, branch `r1`, clean |
| Manager | `langgraph`, `llamacpp/r1-manager`, temperature 0.2, `proposal_schema manager_proposal/v1`, transport retry 3 |
| Seed policy | `llamacpp_seed`, `manager_seed(campaign_id, budget_index, repetition, revision_attempt)` per request |
| Build / GGUF | `version: 0.7.0-dev (build 1, commit 620d222)`; sha256 `509287f78cb…94d3c` re-verified (18.6 s) |
| Card | TITAN index 1, `GPU-2516f262-6a75-eee3-26ee-b2e8d908c07d`, port 18083 |
| Full offload | `full: true`, route `gpu_memory`, **5253 MiB = the pinned footprint exactly**, checked before and after the whole run |
| Served / props | `/v1/models` lists `r1-manager`; one-token probe answered |
| Scale / runtime | 2 instances × W = 10 per node, 16 roots, **161 trials**, `--runs` fixed at 10 outside DRYRUN; **1,592.8 s** (26.5 min), return code 0 |
| Memory mode | `append_only_summary` (memory on), as D28 requires |

Outputs: `results/r1/engineering/liveness_llamacpp_20261026T230913Z/` (per-node JSON and Markdown,
`liveness.json`, `manifest.json`, the 16 root ledgers, `liveness_run_record.json`, and the driver
`phase6_liveness.py` as run).

## R1-SCHEMA under load: 161 trials, zero parse failures

`parse_failed` is `false` on **every one of the 161 trials**, and every trial carries
`schema_version: manager_proposal/v1` in its `llm_call` record. The schema is recorded per trial, in
the run manifest and in the per-node records. No trial needed the heuristic fallback, and none was
counted as a parse failure. Combined with the Phase 5 two-request check (prose without the schema,
strict six-field JSON with it), structured decoding is working exactly as R1-SCHEMA specifies.

Transport: every `llm_call` shows `attempt 1` with `error_class: null` — no retries, no dropped
requests, over 161 calls.

## Diagnosis of the four failures

### The mechanism: on these nodes no proposal ever beat the incumbent

From the 161 ledger trials, the distribution of `delta_vs_best`:

| Node | max Δ | Δ > 0 | Δ = 0 | Δ < 0 | invalid | kept | edit symbols the manager used |
|---|---|---|---|---|---|---|---|
| `digits_mlp` | **+0.21727** | 10 | 0 | 8 | 0 | 12 | `HIDDEN_UNITS` 10, `BATCH_SIZE` 8, `LEARNING_RATE_INIT` 2 |
| `tabular_mlp` | **+0.17058** | 9 | 0 | 9 | 1 | 11 | `HIDDEN_UNITS` 11, `BATCH_SIZE` 8, `LEARNING_RATE_INIT` 2 |
| `openml_credit_approval` | **+0.00637** | 1 | 10 | 7 | 0 | 3 | `max_iter` 12, `C` 8 |
| `openml_ionosphere` | **+0.00464** | 1 | 10 | 3 | 4 | 3 | `max_iter` 11, `C` 9 |
| `openml_breast_w` | **0.00000** | **0** | 12 | 4 | 2 | 2 | `max_iter` 13, `C` 7 |
| `openml_sonar` | **0.00000** | **0** | 12 | 5 | 1 | 2 | `C` 12, `max_iter` 8 |
| `openml_blood_transfusion` | **0.00000** | **0** | 5 | 9 | 4 | 2 | `C` 8, `max_iter` 7, `class_weight` 4, `scaler` 1 |
| `openml_wdbc` | **0.00000** | **0** | 10 | 2 | 6 | 2 | `max_iter` 11, `C` 6, `class_weight` 3 |

On the four failing nodes **not one of the 20 trials produced a positive delta**. The keep rule
therefore kept only trial 1 (which establishes the incumbent) in each of the two roots — 2 keeps per
node, both at `budget_index` 1 — and `keep_after_trial_1` is 0 by construction, not by chance.

Two things drive this, and both are properties of the node's edit space, not of the manager:

1. **`max_iter` edits are exactly inert.** These nodes fit a model that has already converged at the
   default iteration count, so raising `max_iter` changes the metric not at all: the Δ = 0 column is
   10–12 of 20 trials on three of the four failing nodes. Example (`openml_wdbc__s100`, trial 2):
   `max_iter: 2000 → 3000`, `current_best_before: 0.997052`, `delta_vs_best: 0.000000`,
   `decision_rationale: "Candidate did not improve current best; delta=0.000000."`
2. **`C` edits mostly hurt, and there is almost no headroom to win.** Baseline `val_auc` at trial 1:
   `openml_wdbc` **0.9971**, `openml_breast_w` **0.9919**, `openml_sonar` 0.9454,
   `openml_blood_transfusion` 0.7174. The two passing OpenML nodes sit lower —
   `openml_ionosphere` 0.9412 and `openml_credit_approval` 0.8951 — and each found exactly one
   improving proposal, worth +0.0046 and +0.0064. `openml_blood_transfusion` is the exception to the
   ceiling story: it has plenty of nominal headroom but is a genuinely hard 4-feature dataset on
   which neither `C`, `max_iter`, `class_weight` nor `scaler` helped (9 of 20 trials were worse).

The template's edit space is the limiting factor. Six of the eight nodes share the OpenML template
and its two effective knobs (`max_iter`, `C`); PLAN §10 already flags this (D21 pool, 22 Oct: "six
of the eight target nodes share the OpenML template's edit space", with "one further MLP-type node
for diversity" listed as optional). The two MLP nodes, with three real knobs, produce deltas two
orders of magnitude larger (+0.17 to +0.22) and 9–10 keeps each.

### Is this the 19 October `digits_mlp` failure?

**No — the opposite.** On 19 Oct, under Ollama, `digits_mlp` was the node that made no keep after
trial 1 and repeated edits. Here `digits_mlp` is the **healthiest node in the pool**: novelty 0.90,
invalid rate 0.00, **10** keeps after trial 1, max Δ +0.217. PLAN §10 (`digits_mlp`, 22 Oct) directed
repair rather than exclusion and a D28 re-run; under llama.cpp with the schema it passes every
criterion by a wide margin. The known risk did not materialise; four different nodes failed instead,
for a different reason.

### Repetition exists but does not cause the failure

Half the trials on `openml_wdbc` repeat an earlier proposal (`seen_before_trials` 10 of 20; novelty
0.50, exactly at the threshold). Identical edits recurring on the failing nodes include
`max_iter: 2000 → 3000` five times each on `wdbc`, `sonar` and `blood_transfusion`, and
`max_iter: 2000 → 2500` five times on `breast_w`. With memory on, the manager is told the previous
summary and keeps circling the same two knobs — but even its *novel* proposals score Δ ≤ 0, so
removing the repetition would not produce a keep. Repetition is a C1-waste observation, not the
cause of the D28 failure.

### `openml_wdbc`'s second failure: `invalid_rate` exactly 0.30

6 of 20 trials were `failed_invalid` / `invalid_config`, which is `0.30` against a strict `< 0.30` —
a boundary miss by one trial. All 18 invalid trials in the whole run are **value errors the schema
deliberately does not constrain** (R1-SCHEMA is structure-only: six string fields, no enum of keys
or values, so D25 validity stays the model's):

| Node | Invalid edit | Count | Why the node refused it |
|---|---|---|---|
| `openml_wdbc` | `class_weight: balanced → balanced_subsample` | 3 | allowed values are `{None, "balanced"}`; `balanced_subsample` exists only for forest estimators |
| `openml_wdbc` | `max_iter: 2000 → 4000` / `→ 3500` | 2 / 1 | allowed range is `[100, 3000]` |
| `openml_ionosphere` | `max_iter: 1000 → 3500` / `→ 4000` | 3 / 1 | same range |
| `openml_blood_transfusion` | `class_weight: balanced → balanced_subsample` / `→ "None"` / `→ "auto"` | 2 / 1 / 1 | same allowed set (`"None"` as a string is not `None`; `auto` was removed from scikit-learn years ago) |
| `openml_breast_w` | `max_iter: 1000 → 3500` | 2 | same range |
| `openml_sonar` | `max_iter: 2000 → 4000` | 1 | same range |
| `tabular_mlp` | `HIDDEN_UNITS: 512 → 1024` | 1 | `proposal_precondition_failed` (not a config-range error) |

So the invalid trials are the manager proposing out-of-range numbers and estimator-wrong enum
strings — exactly the error class R1-SCHEMA chose to leave measurable rather than constrain away.
The node's D25 validation caught every one; none reached a metric.

## What is *not* claimed

- No verdict on whether these four nodes should be repaired, replaced or dropped. That is the
  author's decision (runbook Phase 6; PLAN §10 `min_live_nodes` = 8, "a pool below 8 is an author
  decision", RUNBOOK §6).
- No claim that the D28 criteria are wrong. The observation is only that `keep_after_trial_1`, on a
  node whose default pipeline is at or near its metric ceiling and whose edit space has two
  effectively inert knobs, measures the node's headroom as much as the manager's liveness.
- Nothing here is a C3 label, a noise-floor measurement or a headroom estimate. These are
  ENGINEERING_ONLY liveness campaigns at W = 10.

## Options the author may want to weigh (proposals, not adopted)

1. **Run sweep 1 with fewer nodes** — the 4 passing nodes — and record the pool change. This
   contradicts `min_live_nodes` = 8 and needs a PLAN row.
2. **Substitute the reserve.** `openml_climate` qualified under D21 on 25 Oct (PILOT,
   `NOISE_FLOOR_CLIMATE_20261025.md`), but it is one node and shares the same OpenML template and
   edit space, so it is likely to fail `keep_after_trial_1` for the same reason; its D28 under
   llama.cpp has not been run. R1-DT-PIN allows the substitution only if the author makes it.
3. **Widen the failing nodes' edit space** (a third effective knob per node, or raising the
   `max_iter` ceiling so that edits are not inert) and re-run D28. This changes the nodes, i.e. the
   measurement instrument, so it is a PLAN decision, and it would invalidate comparison with the
   22 Oct C1 noise floor measured on the current nodes.
4. **Re-read `keep_after_trial_1` for near-ceiling nodes**, e.g. "at least one keep after trial 1 *or*
   a demonstrated non-inert edit space". This is a change to a D28 criterion and only the author can
   make it; recorded here because the evidence points at the criterion's interaction with the node,
   not at the manager.

Everything needed for the decision is in the per-node JSON and the 16 root ledgers in the output
directory, which are committed with this report.

## Co-tenancy during the run

Logged, never signalled. A fourth user held 1,170 MiB on **all four** TITANs throughout; TITAN
index 0 carried 6,377 MiB of three other users' work. The selected card kept 11,111 MiB free against
the co-tenancy need of 5253 + 2048 = 7,301 MiB. The run was unaffected, but **this host is not
exclusive in practice**.
