# Paper B B2 repair re-check — 8 October 2026

**Revised scoped controller/evaluation-core verdict: design-ready: yes.** All four findings in `B2_REREVIEW_20261008.md` are resolved in the reviewed working-tree repairs. This is disposition of the same bounded independent AI-assisted review, not a new broad review, human review or external review. It does not close B1, author novelty gate B2-N, author BAVAR gate B2-BAVAR, scientific-readiness or execution-authorization gates.

The original report, original outputs and original GitHub clone are preserved. The original reviewed B-only commit remains `b09c85a0cd67a67cf4c1f5918091a4ae41ee6173`. The repaired review target is the author B-only working tree on that HEAD, restricted to the four source/test diffs captured in `results/validation_logs/B2_REPAIR_RECHECK_20261008/reviewed_repairs.diff`. Exact reviewed SHA-256 values:

| File | SHA-256 |
|---|---|
| `experiment_scaffold/src/causal_branch/control/evaluate_tree.py` | `90fe0e2f38a0b92585c5840532dfd5667776f598ee7de9c8f9372f73a6a9b7f2` |
| `experiment_scaffold/src/causal_branch/control/timing.py` | `ed42ff4a4745046bcf203f48ab96e8c1409aa515942d99f98c884e5fce0cd4fd` |
| `tests/control/test_evaluate_tree.py` | `fd2181fff64351eac18944ae664c5af6f84fbf65e8a038bb45eaef46da897b61` |
| `tests/control/test_timing.py` | `3db8701c3f395d8925caff953eb705d81f7d4da62ab66cc1baf9d0389f81ab67` |

Citations below refer to these repaired bytes. CPU-only, the same isolated Python 3.13.4/locked environment. No source repository/Paper A access, task-realism rerun, model/API/GPU work, scientific change, authorization mutation, commit or push. The reviewer made no repair/source edits.

## Dispositions, with quoted implementation and observed evidence

**B2-R1 — MAJOR — RESOLVED.** `timing.py:350–356` now accepts `fit(..., c2=...)` and forwards that cutoff to `fit_global`. `evaluate_tree.py:293–302` creates candidate models at the existing grid cutoffs and retains the model matching the selected parameters:

```python
candidate_models = {c2: controller.fit(dev_rows, c2=c2)
                    for c2 in dict.fromkeys(p.c2 for p in controller.grid())}
...
models[name] = (candidate_models[params[name].c2]
                if candidate_models is not None else model)
```

Calibration uses `scores_by_c2[params.c2]` (`:133–140`), and diagnostics receive the retained model's cutoff (`:362–363`). In the original cutoff counterexample's bounded context world (development/test seeds30/31, 240 roots each), the independent score spy now observes development model cutoffs **−.5, 0, .1**; the selected parameter, held-out scored model and diagnostic cutoff are all **0**. Every controller still has **27** grid configurations, ridge `l2=.01`, and **5** family folds; no grid, data or model-family/capacity/fold definition changed. The new explicit-cutoff test demonstrates the same bounded .05 continuation-gain world gives `Vwait>.04` for `c2=0` and zero for `c2=.1`, with unchanged A1/A2.

This is an execution correction to adopted design §3: `B_CONTROLLER_DESIGN_20260927.md:75–87` already defines `d2=1{A2>c2}` and the target using that calibrated policy. It preserves §4's model/fold/data and candidate-count constraints (`:97–102`). No author scientific-controller or tuning-protocol decision is needed for this correction. The default standalone median-cutoff API remains available; the reviewed evaluation path now explicitly supplies the declared candidates.

**B2-R2 — MAJOR — RESOLVED.** `evaluate_tree.py:111–112` now forwards:

```python
feasible1=bool(r.get("feasible1", True)),
feasible2=bool(r.get("feasible2", True)),
```

Legacy mask-free rows explicitly default to feasible (`:102–104`), and `_run_allocator` calls the same allocation-result adapter (`:120–121`). The independent mask spy observes **196 allocations per scenario**, including **80 bootstrap allocations**, for three scenarios: both masks false, only phase1 false, only phase2 false. All allocations preserve the explicit masks; no prohibited phase is selected during calibration, held-out allocation or bootstrap. With both masks false, each controller now spends **0 calls**, leaves **60 unspent**, and assigns every root never; all **240 original roots** remain in the denominator, giving value **.5**. This directly reverses the original reproduced60-call violation.

**B2-R3 — MINOR — RESOLVED.** `evaluate_tree.py:389` now captures the all-bounds result:

```python
_, family_bounds = simultaneous_family_bounds(per_family_gains, 0.05, 0.0)
```

It emits that result under `family_bounds_at_p0` (`:395`). In the all-infeasible scenario, both primary contrast keys are retained and each negative bound is **−0.7841002756996854**. The old qualifying-only implementation returned an empty mapping on such a scenario. Working-p and grid arithmetic were not changed by this repair.

**B2-R4 — MINOR — RESOLVED.** The report now preserves per-controller `realized_calls`, `unspent_calls`, `allocator_work`, `work_per_call=1.0`, and explicit scope (`evaluate_tree.py:308–314`):

```python
"scope": "allocator units; excludes fitting, model tokens and elapsed time"
```

`EvaluationReport.resource_accounting` is declared at `:90–91` and returned at `:424`. The independent probe compares accounting with every base realized-regime map. All-false masks produce **calls0/unspent60/allocator_work0** per controller; phase-specific scenarios produce **calls60/unspent0/allocator_work60** per controller. These are allocator units only, not measured runtime, training compute or model-token costs.

No remaining BLOCKER, MAJOR, MINOR or NIT defect was found within these four dispositions.

## Regression and counterexample checks

| Observed command/check | Result |
|---|---|
| Pinned Python unittest discovery for `test_evaluate_tree.py` | **15 tests**, 2.236s, OK, exit0 |
| Pinned Python unittest discovery for `test_timing.py` | **14 tests**, .359s, OK, exit0 |
| Independent repaired-path cutoff/mask/report probe | all assertions pass; three mask scenarios, 20 bootstrap draws each |
| Original bounded identity probe, now pointing at repaired B checkout | proposed/myopic agreement **.98333, .91667, .84167**; myopic/constant-reserve agreement **.58333, .56667, .575** |
| Five new repaired tests against original unchanged B-only clone | every test detects original defect through assertion failure or unsupported API/report-field error |
| The same five tests against repaired code | all five pass, zero failures/errors |

The identity probe's `Vwait` SD remains **.108992, .111726, .111992**. The repaired cutoff path therefore preserves evaluated distinguishability; it does not establish superiority or a task result.

The old-code detection uses the exact original reviewed B-only checkout, not a historical source reconstruction. Individual detection results: explicit cutoff test **1 API error** (old fit lacks c2); selected-cutoff test **1 assertion failure**; all-infeasible test **1 assertion failure**; phase-specific/accounting test **1 subtest assertion failure +1 missing-field error**; negative-bound test **1 assertion failure**. Capturing these failures makes the regression check executable evidence rather than tests that merely mirror the repaired implementation.

The evidence package is `results/validation_logs/B2_REPAIR_RECHECK_20261008/`; its README lists exact executed commands. Original report SHA-256 remains **`5e672fcbf053a91d2db2da32cd2d76392b0a89653880185dc25cf827150cf504`**. Original review artifacts were not overwritten. No fresh realism, max-bias experiment, literature search, manuscript build, live-safety audit, population-theorem certification or broad review was conducted. The original advisory review's limitations continue to apply.

**Disposition:** all four findings closed for the exact reviewed repair bytes. The controller/evaluation-core code verdict is now **design-ready: yes**, scoped to this review and repair re-check. The author still supplies B2-N and B2-BAVAR; overall B readiness, B1, scientific conclusions and authorization remain separate.
