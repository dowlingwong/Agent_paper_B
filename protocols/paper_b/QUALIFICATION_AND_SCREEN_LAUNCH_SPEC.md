# Paper B qualification and screen launch specification

Status: **written, not executed.** No Ada host was contacted, no model was
loaded, no artifact was bound and no screen or pilot was run. This document is
the exact specification the authors execute after binding the substrate on Ada.
Every hash slot below stays empty until it is filled from the running
configuration; nothing here is a measured value.

Authority: `docs/paper_split/B_DECISIONS_20260927.md`,
`protocols/paper_b/design_decisions_20260927.yaml`, RUNBOOK §12, and the active
contract `protocols/paper_b/contract_v2.yaml`.

## 1. The next external step: bind the Devstral artifacts on Ada

The sole initial model candidate is `mistralai/Devstral-Small-2-24B-Instruct-2512`
on the already planned Ada substrate. Bind the following from the running
configuration (not from a model name) and write them into `contract_v2.yaml`
`runtime:` before qualification:

| Binding | Where it goes | Value |
|---|---|---|
| Weight artifact SHA-256 | `runtime.model_artifact_hash` | _fill on Ada_ |
| Tokenizer artifact SHA-256 | `runtime.tool_versions.tokenizer_sha256` | _fill on Ada_ |
| Quantization / dtype | `runtime.tool_versions.quantization` | _fill on Ada_ |
| Server build (llama.cpp/server or vLLM) + commit | `runtime.tool_versions.server_build` | _fill on Ada_ |
| Context length and decoding settings | `runtime.tool_versions.context_and_decoding` | _fill on Ada_ |
| Harness commit | `runtime.harness_commit` | _fill on Ada_ |
| Verifier revision | `runtime.verifier_revision` | _fill on Ada_ |
| Task-generator hash | `runtime.task_generator_hash` | hash of `experiments/paper_b/task_cc/**` at freeze |
| Evaluator revision | `runtime.evaluator_revision` | _fill on Ada_ |
| `model_revision` | `runtime.model_revision` | resolved model revision string |

Intended binding command (the executor is written later; this is the shape, not
an executed command):

```sh
# On Ada, after the substrate is running.  Nothing is launched by this step.
python protocols/paper_b/bind_runtime_artifacts.py \
  --contract protocols/paper_b/contract_v2.yaml \
  --server-url "$ADA_SERVER_URL" \
  --harness-commit "$(git -C "$ADA_HARNESS" rev-parse HEAD)" \
  --model-root "$ADA_MODEL_ROOT" \
  --out protocols/paper_b/runtime_bindings_2026.json
```

Until `model_artifact_hash`, `harness_commit`, `task_generator_hash`,
`evaluator_revision`, the split manifest and the replay-`p` provenance are
non-null and hash-valid, `validate_for_phase(contract, 'qualification', lane)`
refuses. That refusal is intended.

## 2. Qualification checks (both lanes)

Run for `--lane one_step` and `--lane sequential`. All checks are on the
engineering pool; none produces a scientific result.

1. **Fork isolation.** Live fork through the real adapter path: identical
   serialized starting payload; immutable read-only inputs; isolated writable
   state; no cross-branch mutable links, queues or counters.
2. **Reachability.** Each root's checkpoint 2 is captured when reached; roots
   that terminate early record `terminated_before_decision`; the converter
   rejects a reached-only denominator.
3. **Integrity.** Collection failure and infrastructure stop are recorded as
   integrity statuses, never as U=0; the evaluator refuses them as outcomes.
4. **Lineage and split.** Every descendant inherits the root, template family and
   split; no transplanted checkpoint-2 state; at most one verifier call per
   trajectory.
5. **Determinism / stochastic-law diagnostics.** Deterministic known-answer
   controls plus a stochastic diagnostic where relevant; tolerances matched to
   the state contract.
6. **Budget caps.** Call `budget_cap_errors(contract, usage)` with the measured
   usage; the first ceiling reached stops collection.

Each check writes a phase/lane report bound to the contract design digest
(`binding_digest(contract, 'engineering', lane)`) and is referenced by the
qualification pool and authorization.

## 3. Predeclared screen operability and reachability rules

Fixed before collection:

- **Operability:** a leaf is *operable* iff the task adapter can prepare the
  root, capture the checkpoint, fork the branch and grade it without an
  integrity violation. A screen family that is inoperable is dropped and
  recorded; it is never repaired into success.
- **Reachability:** a root is *reaching* iff checkpoint 2 is captured under the
  declared online rule. Reaching rate is reported; roots that do not reach stay
  in the original-root denominator under the fallback.
- **Screen stop:** stop the screen at the first of the registered caps or at the
  first integrity failure; do not replace a scientific failure with a retry.
- **Disjointness:** screen families are disjoint from pilot and final families
  in the split manifest.

## 4. The 96-leaf screen

Design: 8 fresh template families × 2 roots × 2 repetitions × 3 leaves = 96,
plus 32 reserved integrity-control leaves (pilot is a separate 384-leaf
artifact). This is the screen; it is not confirmatory.

Intended command (executor written later; **not executed**):

```sh
# Requires a qualified contract and Ada authorization.  Not run in this work item.
python experiments/paper_b/run_screen.py \
  --contract protocols/paper_b/contract_v2.yaml \
  --lane sequential \
  --output results/paper_b/screen_v1 \
  --families 8 --roots 2 --repetitions 2 --leaves-per-tree 3 \
  --integrity-controls 32 \
  --enforce-budget-caps
```

The screen reports operability, reachability, integrity, realized verifier calls
and total work separately from the allowed budgets. The pilot law
(`experiments/paper_b/task_cc/pilot_law.py`, hash `449b97c3…`) is frozen before
pilot outcomes; the route decision (COMBINE / CORE_ONLY) is made after the pilot
and before confirmatory outcomes.

## 5. What remains null in the contract

`runtime.*` artifact bindings, `population.task_law`, `population.checkpoint_rule`,
`population.condition_mixture`, `statistics.split_manifest`,
`statistics.independent_unit_count`, `replay_allowance.p`,
`replay_allowance.provenance`, `replay_allowance.p_path`,
`replay_allowance.measured_p`, `qualification_report`, `freeze_commit`,
`resources.runtime_ceiling`, `resources.storage_ceiling`,
`resources.monetary_ceiling`, and every `qualification.<lane>.*` binding.
`p = 0.02` is a **working sensitivity assumption**, never a measured value.
