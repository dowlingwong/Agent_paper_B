# Track S S0.3 (collector side): implementation notes

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Spec: runbook rev. 3 (§2 S0.3 and the arm-invariance
tests, §3 A2-U, §4 controls and settings, §5, §6 arms) plus the coordinator's amendments for rev. 4, 5, 6 and
6.1 (rev. 6 supersedes rev. 5's dynamic family).
This file lists every place where the code had to choose between readings, and what is not implemented.
Nothing here is a result.

## Code map

| Piece | Where |
|---|---|
| Arm-override hook (`ArmOverride`, `resume_campaign(arm=...)`), shadow record | harness `control_plane/snapshot.py` |
| Controller ledger view (`run_real_campaign(controller_ledger_view=...)`) | harness `control_plane/campaign.py` |
| Skip displays `hidden/v1`, `reason/v1` | harness `memory/summarizer.py` |
| Manager seed key (`LangGraphManager(seed_key=...)`) | harness `manager/langgraph_manager.py` |
| A2-U, policies, prior fit, predictive intervals | `r1/tracks/a2u.py` |
| Collector (all phases) | `r1/tracks/collect.py` |
| Synthetic nodes P1, P2, N0 | `r1/tracks/synthetic.py` |
| S0.1 probe, S1.1 factorial | `r1/tracks/probes/` |
| Fast oracle simulator of synthetic nodes (10^4 campaigns per member) | `r1/tracks/oracle.py` |
| Tests | harness `tests/stage2/test_r1_track_s_arms.py`; `r1/tests/test_tracks_*.py` |

## Decisions (readings of the spec)

1. **Ghost / ctrl_only in the harness.** The ledger gets exactly the skip record a skip writes (plus
   `extra.control.arm`, which no display or featurizer reads); the executed result, with its decision forced to
   non-keep, goes to `branch_shadow.jsonl` and `ResumeResult.shadow_record`. `ctrl_only` substitutes the shadow
   for the skip record in every later controller view and keep-prior view; the manager memory, the ledger, the
   harness novelty set and snapshots keep the true ledger. Consequence: the controller-side state features of
   ctrl_only (e.g. `prior_skips`) differ from ghost's by construction; that is part of the Δ_I contrast.
2. **Skip reason of forced skips.** `ArmOverride.skip_reason` defaults to `prior_no_gain` (a fork is never a
   duplicate or a no-op, so this is the only reason a myopic skip can have). `reason/v1` shows a skip with an
   unknown or missing reason as "skipped by the control plane", never as "predicted no gain".
3. **`hidden/v1`** hides control-plane skips only (`is_control_plane_skip`); D25 inactive-key skips keep their
   generic line, as under `one_line/v1`. The prompt's "Budget index" still counts every trial (numbering
   unchanged, as specified).
4. **A2-U model (rev.-4 MA-1).** Groups (key, sign of step), sign = the C3 featurizer's `direction`
   (+1/−1; categorical edits form group "0"). Group mean m ~ N(μ0, τ0²); one executed, non-rule Δ̂ is an
   observation of m with variance λ(σ_cmp² + τ_w²), λ = `obs_inflation` (default 1); forecast = predictive
   N(μ_n, τ_n² + τ_w²). Rule-skipped, no-op and duplicate rows never enter the update. `fit_prior` takes A2's
   node prior per kind with `r1.c3.arms.RulesPrior` (pooled-node soft labels, weight 1, the arms' τ floor),
   estimates τ_w from within-(instance, key, sign) spread and sets τ0² = τ_A2² − τ_w² so that the first
   forecast equals A2's prior. Kinds with < 5 rows fall back to the local prior (flagged `kind_fallback`).
5. **Price (rev.-4 amendment 2).** Roots and continuations run A2-U at g0 (`--g0`, default = the declared g);
   both are in the manifest and in `Provenance.g_declared/g0`. The declared g defaults to 0.1 σ_node (the C3
   convention, `G_PRIMARY`); the runbook does not fix its value — **author decision needed**.
6. **E2 verify** is off for every Track S policy; A2-U never returns `verify`; `--e2-verify` refuses.
7. **Keep rules of non-default policies** (static e2off, dynamic, π′, score models) are served to the harness's
   `bayes_threshold/v1` rule as a shifted keep prior with the policy's threshold on Δ̂. This is exact when the
   policy's keep score is affine and increasing in m̂ (true for every rule here and for ridge models with a
   positive coefficient on `index_value`); otherwise the controller refuses (no silent approximation). A ridge
   model with a non-positive `index_value` coefficient at E2 therefore cannot be run; a harness hook for a
   controller-forced keep would be needed.
8. **`static:g=x,e2off=y`** means execute iff V* ≥ x and keep iff m̂ > y, so that `dynamic` with zero slopes is
   exactly `static:g=g0,e2off=h0` (tested). `matched_static:g=..,h=..` is the same rule under its own name
   (rev. 6 amendment 4; runs on every S3e instance like any policy). The controller version omits the policy name, so two
   policies with identical rules produce byte-identical ledgers (tested).
9. **Dynamic family (rev. 6, sign fixed; rev. 6.1 convention).** E1 execute iff V*_n + b_info·τ_pred,n ≥
   g0 − b_budget·r; E2 keep iff m̂_n > h0 − h_budget·r (h_budget of either sign), r = runs_left/W −
   proposals_left/N_cap evaluated before the decision, with proposals_left INCLUDING the current proposal:
   min(trials left, LLM calls left + 1) (the current trial is not yet consumed and its manager call is already
   charged) and N_cap = min(trial budget, LLM cap). At E2 runs_left already excludes the trial's own run.
   No new-group indicator (b_info multiplies τ_pred directly). The E1 comparison is ≥ (as `rules.execute`) so
   that zero slopes reproduce static exactly; the runbook writes ">", which differs only on ties
   (probability zero). The D1′ example (N = 2, K = 1) is pinned in a test: r = 0 at proposal 1, +0.5 at
   proposal 2 after a skip.
10. **π′ features (secondary).** Score models see `STATE_FEATURES` plus `budget_gap` (= r) and `tau_pred` and an
    `e2` indicator, so a ridge model nests the static and dynamic rules (up to E1 ties).
11. **Fork selection.** Poisson sampling per eligible decision: p_u = min(1, `--forks` / n_eligible(root)) per
    root (so `--forks` is the expected number of uniform forks per root, not a node total), plus the
    near-threshold oversample with `--p-near` within `--near-band` (default off; b is declared from S0.5).
    Channel arms and A/A are Bernoulli draws (1/3 and `--aa-fraction`), keyed by (SELECTION_SEED, fork id);
    "a random third" is therefore a third in expectation. Every selected fork's decision is rebuilt from its
    snapshot alone (the STOP of §10 on a mismatch); A/A leaves additionally re-run the continuation.
12. **A/A leaves.** E1 execute and every E2 fork: no override, first action `continue` (at E2 the snapshot's
    provisional record already carries the root's decision); E1 skip: `ArmOverride("skip", root's reason)`.
    Repetition 0 (the root's), so the leaf must reproduce the root's ledger (budget index, decision, summary,
    metric): `LeafRecord.aa_reproduced`.
13. **Leaf quantities.** `runs_used` = worker runs from the fork trial on, the fork trial's own run included
    (also at E2, where it was spent before the snapshot, and for ghost/ctrl_only); verify re-runs count 2r.
    `binding` = runs before the fork trial + runs_used ≥ W. `llm_calls` = `llm_call` events of the leaf.
    `immediate_measured` = 1{fork trial kept in the leaf} × (mean audit of the kept configuration − mean audit
    of the branch's incumbent at the fork) over the same K audit seeds as Y (rev.-4 amendment 4), NaN if an
    audit seed failed. `nf_c_events` is written 0 (filled by the analysis). `dup_filtered_due_to_fork` counts
    later rule-duplicate skips whose first evaluation is the fork trial (A2-U records `duplicate_of`).
14. **S0.4** runs at W = the LLM cap (non-binding; rev.-4 amendment 7) with `ExecuteNonRuleController`; without
    a prior the keep rule is the harness default (Δ̂ > 0), with `--prior` A2-U's Bayes keep. Dev rows audit
    candidate vs incumbent at the K = 5 dev seeds.
15. **S0.5 binding shares** (`binding_shares`) are read from roots at the largest W: valid because A2-U's
    decisions do not read the budget (not valid for the dynamic family or π′).
16. **Seeds.** Instance blocks: S0.4 30000+, tune 30250+, S0.5 30500+, S3 31000+, campaign (fresh) 32000+,
    synthetic 36000+, fixtures 39000+; dev audits 33001–33005; Track S audits 34001+ (first K); selection
    35001; S1.1 37001–37030. Leaf repetition r uses D26 repetition 100 + r (root and A/A: 0). Every campaign of
    one instance (root, A2 root, leaves, tune/campaign policies) uses the same harness campaign id and manager
    `seed_key` (rev.-5 amendment 2); policies are distinguished by `root_id` and `RootRecord.policy`.
17. **Tune phase (rev. 6 amendment 2, superseding the rev.-5 per-family allocation).** Every configuration
    runs on the same paired dev instances (`--instances`, 20; 40 after a resize). `--tune-grid static|dynamic|all`
    with `--sigma-cmp-vary` (grid unit) adds the declared grid: static g ∈ {0.05, 0.1, 0.2, 0.4} (rev. 6.1;
    `--tune-g-extension` adds 0.8) × h ∈ {−0.25, 0, +0.25} = 12 configurations; dynamic members at m*'s (g, h)
    (`--m-star g,h` in σ units): budget (b_budget = +1 σ), info (b_info = +0.5, dimensionless because it
    multiplies τ_pred), keep+ (h_budget = +0.5 σ), keep− (h_budget = −0.5 σ). Choosing m* is the analysis's
    job (two collector invocations). The S3e `campaign` phase also runs every policy on every instance.
18. **Synthetic nodes (rev. 6 amendment 3)**: P0 (budget channel: binding W, independent values), P1
    (information), P2p / P2m (budget-dependent keep feedback, both signs), N0 (zero oracle gain: non-binding W,
    independent values, no information, no feedback). Each has a `gain` knob (the planted channel effect; the
    best-member oracle gain is a monotone function of it, to be calibrated by large-replication simulation with
    `r1/tracks/oracle.py`; N0 refuses gain ≠ 0) and a `variant` (`diffuse` Gaussian, or `concentrated`: a
    zero-mean two-point law with the same sd, large value with probability q). The P0 budget channel needs the
    run's W to bind (`--W` < cap); N0 needs it not to. They use the digits_mlp editable surface (so snapshots, restore and the C3 featurizer work
    unchanged) with an in-process worker (`SyntheticWorker`) and log-linear laws on ALPHA and
    LEARNING_RATE_INIT. Without shared incumbent error (default), the incumbent's recorded noise is carried in a
    comment line of `train.py` (ignored by every configuration parser; restored with the incumbent), so every
    Δ̂ = Δ + fresh noise. Parameters are constructor args with placeholder defaults (not declared values).
    A synthetic run of 2 roots with all leaves takes ~5–10 s on one CPU core. S0.4 is also allowed on
    synthetic nodes (cheap test path for the prior fit). For 10^4 campaigns per member, `oracle.simulate` runs a
    campaign in memory in ~5 ms (no files); a test checks that it reproduces the pipeline's terminal Y, worker
    runs and decisions exactly on P0, P2p, P2m and N0 under a2u / static / dynamic (`pi_prime` unsupported).
22. **S0.5b** (rev. 6.1 amendment 3): `--phase S0.5b --truncate-W 8,10,12,20` audits, at the K audit seeds,
    the incumbent of every S0.5 root ledger truncated where a campaign at that W would have stopped
    (`truncate_at_W`; equal to an actual W campaign for the budget-blind A2-U, tested). Output
    `s05b_truncated.jsonl`; resumable.
19. **Manager.** Real nodes use the harness LangGraph manager with the llama.cpp provider (`--manager llamacpp
    --manager-model llamacpp/<alias>`, `LLAMACPP_BASE_URL` set by the operator; transport retry 3 and the
    optional `manager_proposal/v1` schema as in sweep 1), built in `collect.py` to pass `seed_key`;
    `--manager scripted` is the E1b stand-in for CPU smoke runs only.
20. **S1.1** default levels are the start value and twice it (integers rounded); `--levels` overrides.
21. **S0.1** prompts are the harness LangGraph prompts of the node at trials 2..N+1 with empty memory, sent
    directly to `/chat/completions` with the D26 seeds; identity = all repeats of a prompt identical.

## Schema changes (`r1/tracks/schema.py`; defaulted fields at the end only)

* `Provenance.g_declared`, `Provenance.g0` (rev.-4 amendment 2).
* `LeafRecord.aa_reproduced` (A/A check), `LeafRecord.policy` (rev.-4 amendment 3).
* `RootRecord.policy` (rev.-4 amendment 3); helper `root_from_dict`.

## Not implemented (open)

* S3d online confirmation as its own phase (the `campaign` phase with `pi_prime:` / `dynamic:` policies on
  fresh instances covers the runs; the frozen-and-hashed Ĉ and the decision rule belong to the analysis).
* Policies `budget_dp:<table>` and `probe_first` (refused by the parser); `pi_prime` in the oracle simulator.
* S4a prompt-level display ablation runner (rebuild prompts under D0–D3 and call the manager R = 5 times);
  the displays themselves exist.
* The analysis (`analyze.py`, `simulate_controls.py`; another agent), including `nf_c_events`, U_split and
  the S0.5 sd summaries; `binding_shares` is the only S0.5 summary here.
* Root per-seed terminal audits are not a schema field; they are kept in `<work>/root_meta/<root_id>.json`.
* No GPU host run, no LLM run, no independent review yet.
