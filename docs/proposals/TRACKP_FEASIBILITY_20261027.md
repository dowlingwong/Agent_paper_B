# Track P feasibility proposal — 27 October 2026

AI-assisted, read-only analysis of committed records; no Track P model runs, training or edits to `r1/c3/train/`. This is a proposal for the author, not an adopted scope, an authorization, an E0 result or a scientific claim. The time plan is conditional on the independently reviewed [L3 proposal](ICML_REPLAN_20261027.md), not yet adopted. The pilot is partial/engineering-only and cannot establish a finalist ranking or a C3 gate result.

## Label budget and detectable RPS-skill differences

RUNBOOK Track P estimates ~2,000 audited proposals and the task brief uses ~1,400 for training; these are **projections**, not a realized label count. The actual training/dev/test allocation, cluster sizes and two finalists' paired out-of-sample RPS losses are not yet known. Training count alone does not fix test precision. In particular, the committed pilot does not contain paired predictions from the future finalists, so their variance, paired bootstrap power and a defensible minimum detectable finalist difference are **not checkable** from these inputs.

To show the sensitivity to a concrete stand-in rather than invent finalist performance, [bootstrap_proxy.py](trackp_feasibility_20261027/bootstrap_proxy.py) reads only the committed [19 Oct pilot](../../../results/r1/engineering/c3_audit_pilot_20261019T001338Z/) and uses its randomly audited non-inert rows, disjoint pilot evaluation seeds, and two artificial fixed forecasts. It does not fit a model. Its [output](trackp_feasibility_20261027/bootstrap_proxy.json) records all assumptions and the random seed. The proxy selects 147 rows in 42 pilot instances; it excludes pilot rows classified inert, does not apply the pilot's inverse sampling weights, and does not treat these selected rows as representative of the future sweep. It estimates the base-rate denominator on those same pilot labels and holds it fixed in every bootstrap draw. This is not a held-out training estimate, omits denominator-estimation uncertainty, and has no established direction of bias for the skill difference or power.

For an **assumed** 600 evaluation rows (2,000 less 1,400 training, with no dev allocation), the proxy resamples 172 pilot instance clusters per draw with replacement; the number of rows in a draw varies, rather than being exactly 600. It treats repeated pilot clusters as if they were independent future instances, imposes an additive shift in paired skill difference, and compares the shifted distribution with the empirical two-sided 95% null critical value. This is a centered-bootstrap sensitivity calculation, not a nested paired-bootstrap confidence-interval power study. Under those assumptions, its paired skill-difference bootstrap s.d. is ~0.058 and the first tested effect on a 0.005 grid reaching 80% rejection is **0.160 RPS-skill units**. That number is an exploratory result for the arbitrary forecast pair and denominator only; it is **not** the detectable difference between finalists. A smaller held-out set, dev allocation, cluster dependence, node shift, unequal sampling or more similar finalist predictions can change precision substantially. No outcome-dependent choice of effect size is registered here.

The two initial analysis attempts failed before reading data: first, Python could not import `r1` without `PYTHONPATH`; second, the initial root-path index was wrong. The third attempt used `PYTHONPATH=.` and the corrected root, producing the committed output; no acceptance criterion was relaxed. Reproduce from the paper worktree with:

```sh
env PYTHONPATH=. CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /private/tmp/paper-b-local-20261026-venv/bin/python docs/r1/proposals/trackp_feasibility_20261027/bootstrap_proxy.py
```

**Recommendation for the author:** after the candidate predictions and held-out design exist, predefine the cluster unit, split, paired loss, base-rate denominator, target effect and bootstrap method before using actual finalists' paired losses for a power/sensitivity analysis. Do not interpret the proxy as a guaranteed effect size, change a selection threshold to match it, or train on evaluation labels.

## GPU-hour estimates and schedule

The only directly timed E0 input here is one portal DRYRUN: two Kev-0.8B soft/hard runs, together ~6.6 leased minutes, including reduced probes ([DRYRUN report](../reports/TRACKP_P3A_DRYRUN_20261026.md)). It is neither a TASL-7 measurement nor an evidence pass. The P.0 spike report gives ~0.83 s per step for Kev-0.8B and ~3.29 s for Kev-4B at a roughly 1,024-token, batch-8 timing point ([P.0 report](../reports/TRACKP_P0_SPIKES_20261026.md)). Those are past measured engineering timings; the estimates below assume they transfer and exclude loading, validation, checkpoints, contention and failed runs.

| Stage | Estimate and source | Limits / dependency |
|---|---|---|
| Host setup and equivalence | GPU-hours **unknown**; required by R1-TASL7-TRACKP and the Track P runbook host-change header | No TASL-7 timing or accepted equivalence record is established here. |
| P.3a E0/E6 | **~0.88 GPU-hour projected arithmetic:** 6.6 min × 8 candidate bases ÷ 60, if every candidate's paired DRYRUN costs the same | Not a forecast for 4B models; setup, phase reviews, retries and fuller probes omitted. E0 design and author note remain open. |
| P.3b | **~8 GPU-hours projected:** ~1 hour per model × 8 bases from `TRACK_P_POST_TRAINING.md` §5.4's E3 estimate | Other exam rungs, selection, Jev, E7 and model-size variation add unknown cost; E0 disqualifications or an author decision can reduce the pool. No model is selected here. |
| E7 head comparison | **~2 GPU-hours projected:** ~1 hour each on the top two from `TRACK_P_POST_TRAINING.md` §5.4 | This is a source projection, not measured TASL-7 runtime, and is separate from the illustrative E3 budget. |
| P.4 A5 | **~0.61–2.40 GPU-hours per model for three seeds, illustrative compute only:** assume 1,400 training rows × 5 epochs ÷ batch 8 = 875 batch-8 microsteps per seed; 875 × 3 × 0.83 or 3.29 seconds ÷ 3,600 | Assumes the portal P.0 per-step timing carries to the actual A5 data and TASL-7, full five epochs, effective-batch accumulation, no overhead or early stop. It is not an empirical P.4 duration. Multiply by author-confirmed finalists/controls and the learning-curve configurations; their count is not fixed here. |
| P.5 A6 and P.6 R-B | **Unknown**; no measured full-stage cost or fixed full matrix here | Depend on P.4 RL gate, C3 gate, separate notes, H.8 and author scope. Reasoning tokens and rollout costs cannot be inferred from the one E0 timing. |
| LONO, 4B sidecar/deployment | **Unknown** | Additional folds, matched compute and host equivalence; do not use an optimistic one-model time as an allocation. |

The L3 proposal's conservative full-route scenario extends beyond its **estimated**, not official, abstract date; these illustrative GPU calculations do not establish that it will fit. Host setup, label publication, author decisions, model fit and reviews are critical-path uncertainties. No utilization or allocation is asserted.

## Scope and spec questions for the author

| Stage | Claim or comparison it supports | Consequence of a proposed deferral |
|---|---|---|
| A5/P.4 | Learned-belief SFT row in B.5, one possible A3-or-A5 input to B.7, and reference for later post-training | Omitting it removes the A5-specific comparison and later A5-based claims; the author must decide any scope change. |
| R-A0 / R-A1 | Rule on A5 belief versus detached action-head policy | Omitting either weakens the learned-policy-versus-theory-rule comparison on the same belief. |
| R-A2 / R-A3 | Shared-representation and smoothed-rule ablations | Deferral removes the respective drift or objective ablation. |
| R-B | Distilled reasoning/self-control arm | Deferral narrows self-control evidence; the required predeclared three-way comparison does not disappear. |
| E7 | Adopted head-form comparison for the top two in P.3b | Deferral is a proposed change requiring author decision; it removes the planned head-form selection evidence. |

The research value and actual necessity of individual stages for a particular claim depend on what the author declares. These are possible scope changes, not authorized cuts. PLAN §9's matched baselines, action/information ablations and held-out generalisation do not disappear automatically.

Corrections for the Track P owner, without editing its code: bin edges differ between the historical C3 document and Track P; E0 hard-label contrast and the absolute hard-label prohibition need an explicit scope ruling; R-A0 has two descriptions; the specification's RPS scaling and shared-representation language require reconciliation with the implementation and R1-C3-POST. Details and options are in [route proposals R2–R6](ROUTE_PROPOSALS_20261027.md). The DRYRUN also leaves head-fit, step-budget and context-limit handling for author decision. The independent theory audit and E0 data regeneration discrepancy are separate unresolved checks, not grounds to tune a frozen rule after seeing outcomes.

**Questions:** Which stages are essential to the chosen paper claims? What training/dev/test and cluster design should the later paired power calculation use? Which bin-edge and scoring specification is authoritative? What E0 design and scope should be frozen before the next authorized phase?
