# Review: Track P implementation of the author's evening decisions (rule v2, E0 thresholds and budget) — 26 Oct 2026

AI-assisted. Independent reviewer (Claude, separate session from the executing Track P agent; makes no fixes; edited no
tracked file while the GPU validation DRYRUN was running). Scope: `git log 6d9dc83..471f93f` on `trackp-20261026` —
`460ba52` (PLAN rows) and `471f93f` (code, spec, runbook, rule v2). The running short DRYRUN
(`runs/p5_e0v2_twostage_short/`) is not reviewed here. CPU only.

Tests (venv `trackp-cpu`, at `471f93f`): the changed modules `test_trackp_e0_v2.py`, `test_trackp_exam_analyze.py` and `test_trackp_cli.py` pass (**48 passed**, 21 min). The full `test_trackp_*.py` suite did not finish within my 30-minute cap: the CPU is shared with the running DRYRUN. The executing agent should record a full-suite pass at the final commit. Throwaway probes in
`/tmp/claude-1008/rv/`: the L-BFGS head fit on synthetic features, with the bootstrap slope checked against `np.polyfit`.

## Findings

1. **minor — Some choices of the Track P agent are written into the spec as fact rather than marked as the agent's.**
   The coordinator's list of self-made choices is mostly reasonable. These items are stated as settled in
   `TRACK_P_POST_TRAINING.md` without the "(Track P agent's …)" tag that other agent choices carry:
   - **The L-BFGS head initialises the LoRA stage** (§5.5, "it initialises the head of the LoRA stage"). R1-E0-HEADFIT
     says only that the head fit is descriptive. The final E0 metrics depend on this initialisation, so the author
     should confirm it. The alternative is a fresh head trained only together with LoRA.
   - **The hard-label and native runs use the stage-2 budget** (6,000 steps, patience 10). The author confirmed reusing
     the lr, not the budget.
   - **A4 ≥ 95 % is kept as a non-disqualifying E6 record** (§5.6: "recorded under E6, not disqualifying — §5.7.1").
     This is consistent with the unchanged §5.7.1. But the author set "E0/A4 thresholds" together, so whether a failed
     A4 disqualifies is the author's call.
   - **The bootstrap lower bound is a two-sided percentile.** It is taken as the 2.5th percentile of a two-sided 95 %
     percentile interval. The spec flags only the resampling unit as the agent's choice. "95 % lower bound" can also be
     read as one-sided, i.e. the 5th percentile; the 2.5th is the stricter reading.
   - **Resampling unit, for the author's information.** Resampling the 1,000 test prompts ignores the clustering into
     10 test cells. On my synthetic probe the interval is about ±0.025 around the slope, so "lower bound > 0" never binds
     once the slope is ≥ 0.6. A cell-level bootstrap would bind but would be very wide with 10 cells. Prompt level is
     defensible; the author should know the condition is effectively vacuous under it.

   Fix: tag each item "(Track P agent's reading; author to confirm)" in §5.5, §5.6 and §5.7, and add them to the list
   of agent choices under the evening PLAN rows. That list currently covers only the morning items.

2. **minor — The text on the control readout is stale after R1-CONTROL-READOUT.**
   R1-CONTROL-READOUT amends R1-C3-CONTROL: the primary readout is a fresh LayerNorm + linear head, and the bin-token
   readout becomes a secondary row. The following text still describes the bin tokens as the control's belief readout:
   - `RUNBOOK.md:197` (P.1: "12 reserved bin tokens read from the LM head (belief)");
   - `RUNBOOK.md:198` (P.2: "control LM-head tokens");
   - spec §2.2 wrapper table (`TRACK_P_POST_TRAINING.md:72`).

   Only the §5.1 table was updated. Fix: amend these three places, citing R1-CONTROL-READOUT, with the bin tokens as
   the secondary row.

3. **minor — Outputs that are not the E0 result still carry pass flags.**
   - `e0_v2` sets `out["pass"] = e0_pass_v2(...)` for every soft run, including `stage="screen"`. R1-E0-BUDGET says the
     E0 metrics come from the stage-2 run only, so a screen run reporting `"pass": true/false` invites misreading.
   - `probes` still emits the v1 `A4` record with `"pass"` (raw monotonicity in s, v1 rule), next to `A4_v2`.

   Fix: `pass: null` (or omit it) for screen runs; for v1 A4, drop the `pass` key or rename it (e.g. `v1_criterion_met`)
   so that only `A4_v2.pass` reads as the A4 result.

4. **minor (nits).**
   - **Two sources for the thresholds.** They live in the rule (`width_slope_vs_label_lb95_gt`) and again in
     `exam_synthetic.E0_V2_THRESHOLDS` (`width_slope_vs_label_lb_gt`), under different key names. The bootstrap settings
     (`E0_BOOT`) appear in the rule only as a comment, so the sha256 does not freeze them. Better: carry the bootstrap
     settings as keys in a later rule version, or have `e0_pass_v2` read the rule.
   - **E2 tolerance at the boundary.** `_pick_second` keeps `key <= best + 0.01` in floating point, so a difference of
     exactly 0.01 can fall either way. A tiny epsilon, or a comparison on rounded values, would make it deterministic.

## Checked and found correct

- **Rule v2 and its sha256:**
  - `r1/c3/rules/p3_rule_v2.yaml` hashes to `a0a53eef…1533`, which matches the `.sha256` file.
  - It contains the E0 v2 thresholds: 0.6, lower bound > 0, mean slope 0.8.
  - It has A4 0.95 and A5 descriptive under E6, `first: e3_point_top`, the four tie-breaks for the second finalist,
    `e2_tie_tolerance: 0.01`, and no pending families.
  - `load_rule` refuses any version other than `p3_rule/v2` (v1 is refused; test). `analyze` refuses E0 records not of
    protocol `trackp_e0/v2` (test).
- **Finalist logic:**
  - Finalist 1 = `ranking[0]`, the E3 point top among candidates that pass step 1; controls and floors are excluded.
  - The tied set starts with the top. The second-finalist pool is the tied models of another class.
  - Selection filters in order: E2 within 0.01 of the best (a missing E2 counts as worst), then |width ratio − 1|, then
    base before instruct, then cost, then name. The steps are recorded in a trace (tests for the order and for the
    StartLux candidate).
- **E0 pass:** `e0_pass_v2` requires the slope ≥ 0.6, the lower bound > 0 and the mean slope ≥ 0.8. The vectorised
  bootstrap slope equals the OLS slope (it reproduces `polyfit` on the full sample). `_step1` checks the same three
  conditions from the rule.
- **Two-stage budget:**
  - The config splits `e0.screen` (2,000 / 100 / patience 5) and `e0.final` (6,000 / 100 / patience 10).
  - `--stage` selects the budget, and `e0-select` accepts screen runs only.
  - The driver runs the screen over the grid, selects the lr, then runs the final, hard and native runs at the selected
    lr, then probes on `final/saved`.
  - `SHORT=1` overrides are recorded as `budget_override`.
- **L-BFGS head fit:**
  - Full batch, float64, on CPU, with a strong-Wolfe line search.
  - It is declared converged after two stalls with the history reset in between, or when the gradient is ≈ 0.
  - The report records the iteration and restart counts, `converged`, train and val RPS, and that it is descriptive.
  - On my synthetic probe it converged (14 outer steps, 1 restart, gradient norm 2.6e-6).
- **A5:** read on the model's own head form (`linear12` for the Qwen fresh run), with `pass: null` and
  `criterion_met` recorded. The bin list stays in canonical order (`bin_order` default).
- **PLAN rows:** R1-E0-THRESHOLDS, R1-E0-BUDGET, R1-E0-HEADFIT, R1-CONTROL-READOUT, R1-TRACKP-CHOICES, R1-EXAM-RULE-V2
  and R1-P3A-READY follow the author's text faithfully, including "E0 is a floor, not a ranking", "zhixu experiment not
  used", and that validation cells are disjoint from the test cells (also asserted in code). The spec's §9 open item is
  closed. R1-TOKEN-INIT and the agent-choice note are updated to "confirmed".
- **No relaxation:** no other criterion or pinned value changed. Rule v1 stays on disk with its sha256 and is now
  refused.

Verdict: changes required
