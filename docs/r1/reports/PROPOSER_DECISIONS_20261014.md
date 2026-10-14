# Proposer decisions after the ionosphere diagnosis — draft, 14 October 2026

*Drafted by an AI agent (Claude, coordinating session) at the author's request. **Nothing here is adopted.** A row becomes a decision only when the author records it, dated, in PLAN §10. Inputs: `docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md` (`dd94701`), and the harness code read on the Mac (`~/Documents/autoresearch_harness`, branch `r1`): `memory/summarizer.py`, `manager/langgraph_manager.py`, `control_plane/campaign.py`. The R1 collector is `r1/headroom/e1b_collect.py`.*

## Facts these drafts rest on

1. **Memory was switched off by our own collector, not by the harness.** `r1/headroom/e1b_collect.py`, `run_root`, calls `run_real_campaign(..., manager_mode="baseline_manager", memory_mode="none", ...)` as a literal. The value was set for the scripted stand-in, which ignores memory, and it carried over unchanged into the LLM runs (DT3, DT4). No PLAN row ever decided it.
2. **The harness offers three memory modes** (`MemoryMode` in `memory/summarizer.py`):

   | Mode | What the manager sees under "Prior trial memory" |
   |---|---|
   | `none` | Four fixed lines: `node=…`, `budget_index=…`, `metric=… direction=…`, `editable_paths=…`. No decisions, metrics or deltas. |
   | `append_only_summary` | One line per prior trial: `trial_id: decision=…; summary=…; metric=…; delta=…`. |
   | `append_only_summary_with_rationale` | The same lines plus `rationale=…; failure=…` for each trial, an optional `repeated_bad_warnings=…` line, and a `best_strategy=…` line. `rationale_max_tokens` can truncate the rationales. |

3. **Under `none` the prompt contradicts itself.** The four-line block is non-empty, so `_prepare_context` still prints "Prior trial memory:" and the mandatory AVOIDANCE RULE ("Study the trial history above carefully… you MUST NOT propose the same parameter change in the same direction again"), yet there is no history to study.
4. **There are three small defects in the summary lines** (they matter only if memory is switched on):
   - `_summary_line` takes `parsed_metrics.get("val_auc")`, and otherwise the first parsed metric. It does not use the node's `metric_name`, so on `digits_mlp` it may show `train_loss` instead of `val_score`, depending on parse order.
   - The `or` fallback skips a metric of exactly 0.0.
   - `_best_strategy_line` assumes maximisation.
5. **The OpenML template advertises nine editable keys.** Under `logistic_regression`, only `model_type`, `C`, `class_weight`, `max_iter` and `scaler` reach the model. `imputer` is inert on datasets without categorical columns, such as ionosphere. The scripted stand-in already restricts itself to active keys (`OPENML_ACTIVE` in `r1/headroom/scripted_manager.py`); the LLM path does not.
6. **Decoding is stochastic.** The temperature is 0.2 (pinned with D15 in `e1b_collect.MANAGER`) and no seed is set. Only 3 of 72 branch repetition pairs are identical. The repeated proposals come from the missing memory, not from deterministic decoding.

---

## D24 — Memory mode of the LLM manager (part of the proposal law)

| Option | Effect | Cost |
|---|---|---|
| **(a) `append_only_summary`** | The manager sees every prior decision, metric and delta, including `delta=0.0` for inert edits. | Fix fact 4 first (use `node_spec.metric_name`, handle 0.0, respect the metric direction) and add a test. The prompt grows by one line per trial (≈ 20 lines at W = 20). |
| (b) `append_only_summary_with_rationale` | As (a), plus rationales, repeated-bad warnings and a best-strategy line. | Longer prompts, slower with a 7B model. The workshop harness had a verbosity question about this mode (`rationale_max_tokens`). |
| (c) `none` (status quo) | A stateless proposer that repeats itself (fact 6). | Unrealistic for an autoresearch agent; the AVOIDANCE RULE is vacuous (fact 3). |

**Proposal (not adopted):**
- **(a) as the primary proposal law** for all LLM-backed R1 runs.
- Keep **(c) as a declared secondary contrast in E1b only**. Under T2 Proposition 5, memory should raise the value g of a fresh proposal and therefore lower the value of verify. The memory-on vs memory-off contrast on the same node and model is a direct test of that prediction, and DT4 already provides the memory-off arm.
- The collector must take the memory mode as a manifest field rather than a literal.

## D25 — Action space of the OpenML template (active keys)

| Option | Effect | Cost |
|---|---|---|
| **(a) Node-declared active keys** | Each node declares which editable keys are active for the current configuration, keyed by `model_type`, plus a dataset-level exclusion such as `imputer` when there are no categorical columns. The manager prompt lists only active keys. A proposal that names an inactive key is rejected before any worker run, as a validation failure the manager may revise. The scripted stand-in reads the same declaration instead of its private `OPENML_ACTIVE`. | Harness change on branch `r1` (node spec, `_prepare_context`, edit validation) plus tests. Proposals now cost LLM calls but no runs. When `model_type` changes, the active set changes with it. |
| (b) Annotate keys as active/ignored | Soft. The model may still pick an inert key. | Prompt text only. |
| (c) Leave as is | Inert edits stay possible on every OpenML node that starts as `logistic_regression`. | None. The whole OpenML pool degenerates under the LLM (diagnosis, "Implications"). |

**Proposal:**
- **(a)**, because one shared declaration gives the scripted and LLM proposers the same action space.
- `digits_mlp` and `tabular_mlp` are unaffected (all their constants are active).
- Before E3, audit the other nodes (`lr_synthetic`, `mlp_synthetic`, the remaining OpenML nodes) for inert keys.

## D26 — Seed for manager sampling

| Option | Effect |
|---|---|
| **(a) Keep temperature 0.2; add a per-call Ollama `seed` derived from (instance, trial index, repetition)** | Repetitions differ only through the seed, and a branch can be re-run to the same proposals on the same model, Ollama version and hardware. Bit-reproducibility across hardware is not guaranteed. |
| (b) Unseeded (status quo) | Repetitions differ, but cannot be reproduced. |

**Proposal:**
- **(a)**: a reproducibility measure, not a fix.
- Record the seed in every `llm_call` event.
- It changes no expectation, so it is not a change of proposal law in distribution.

## D27 — No-op and duplicate edits

| Option | Effect |
|---|---|
| **(a) Record only** | Flag every trial whose effective edited config equals the incumbent's, or equals an earlier evaluated config, or whose metric is bit-identical to the incumbent's. Count these as wasted runs in C1. Do not change behaviour in the primary arms. |
| (b) Record, and add a harness-heuristic arm "skip a known no-op or duplicate at E1" | As (a), plus an E1 skip baseline. This is the doom-loop skip already listed among the PLAN §5 baselines. |
| (c) Block no-ops for every arm | Changes the default rule ρ itself. |

**Proposal:**
- **(b)**.
- After D25(a), inert-key no-ops disappear on OpenML, but duplicates remain (19 % of digits trials were bit-identical to the incumbent).
- The DT4 numbers (834/840 wasted ionosphere runs) are a vivid C1 example of a proposer-induced waste mode.

## D28 — Node liveness check before any LLM-backed collection (process)

**Proposal:**
- Before any LLM-backed collection on a node, run a short engineering check with the chosen memory mode: 1–2 instances, W = 10, no branching.
- Require all three of:
  - at least one keep after trial 1;
  - at least 50 % of trials with a metric different from the incumbent's;
  - an invalid rate below 30 %.
- A node that fails is fixed or excluded, and that is recorded in STATUS.
- The batch runner enforces the check as a STOP.
- Thresholds are placeholders for the author to set.

## Open item, not for decision now

The harness keeps the **first valid trial unconditionally** ("First valid metric becomes the current best"), and the start configuration is never evaluated inside the campaign. Trial 1 can therefore be a false keep relative to the start configuration, and in-run `current_best` never compares against it. The audited outcome Y is still measured against the start configuration, so E1b is not biased. It does affect how C1 counts false keeps. Proposed: decide at the next STOP whether to evaluate the start configuration as trial 0.

---

## If D24(a), D25(a), D26(a), D27(b) and D28 are adopted: order of work

1. **Harness (`r1` branch):**
   - the memory-summary fixes (fact 4);
   - the node-declared active keys with prompt filtering and edit validation;
   - the seeded sampling;
   - the no-op and duplicate flags.

   Each comes with a fail-before / pass-after test, and the default-path regression stays byte-identical where the default is unchanged.
2. **R1:**
   - `e1b_collect` takes the memory mode and seed from the manifest;
   - the scripted stand-in reads the node's active-key declaration;
   - the D28 liveness check goes into the runner.
3. **Liveness check (Ada)** on the five noise nodes with memory on (D21 proposal).
4. **LLM E1b rerun** with more instances:
   - memory on (primary) vs memory off (secondary);
   - continue / verify, plus the run-free acceptance rules if the D4 amendment is adopted.

   The primary target is to narrow `always_verify − ρ` and to test the memory effect predicted by Proposition 5.
