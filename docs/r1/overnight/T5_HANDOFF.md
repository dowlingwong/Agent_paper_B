# T5 overnight handoff — 19 Oct 2026

*AI-assisted (Claude). `ENGINEERING_ONLY`. Model-based numbers, not measurements. Worktree `.claude-worktrees/t5-sim`, branch `overnight/t5-sim`, fast-forwarded to main `a312f89` before work. Not pushed. `docs/r1/STATUS.md` and `PLAN.md` were not touched.*

## What was built

| File | Content |
|---|---|
| `r1/theory/simulate_t4.py` | Vectorised campaign simulator. It covers heterogeneous proposal types, local vs structural ϱ, iid or record noise, four proposers (stationary, diminishing returns, memory-reading on raw B, memory-reading on debiased B̃), and policies ρ / A1 / A2 / oracle / calibrated or uncalibrated predictors, with threshold, screening and a lookahead shift. It also holds the closed forms (Propositions 7–10) and the E1b-style continue/verify branch study (DI contrasts and value residual). |
| `r1/theory/t5_report.py` | Resumable runner (`--max-seconds`, `--quick`, `--only`). It writes `parts/`, `tables.md` and `manifest.json`. |
| `r1/tests/test_t5_simulate.py` | 14 tests. All pass, as do the T2/T3 suites: 37 passed. |
| `results/r1/engineering/T5_20261019T004918Z/` | The full run: 84 parts, about 400 CPU-seconds, base seed 20261019. |
| `docs/r1/theory/T5_SIMULATION.md` | Setup, results by check, what the simulation supports, and limits. |

Reproduce with `python -m r1.theory.t5_report --out <dir>`. The full suite runs in about 7 min on one core.

## Outcomes (10⁻³ metric; δ_n = 2)

1. **Proposition 7.** Realised campaign gain matches the summed exact gap with ratios 0.98–1.02, within 1–2 s.e., in all stationary iid cells. It always lies between the bounds. Examples: digits_on at W = 20, +3.10 ± 0.04 vs +3.04; tabular_on, +2.00 vs +2.03. With feedback or the record channel the ratio is 0.36–1.31.
2. **Proposition 8.** In the Lagrangian check, the realised gain equals Σ(g − V*)⁺ to MC error. At the hard budget, learned screening adds +1.9 (digits_on) and +0.7 (tabular_on) at W = 20. It adds about 0 with memory off, because the call cap binds.
3. **Proposition 9.** The inverse-Mills formula holds for every proposer and policy (residual ≤ 0.02 on means of 9–13). The debiased display removes the display bias. Its effect on gain has a sign that depends on the bold edits: −1.9 to −4.9 if they have positive value under selection, +1.0 to +3.4 if they are harmful.
4. **Proposition 10.** Under DI, the lookahead family never beats myopic. Under the modelled DI violations myopic loses ≤ 0.54 δ_n (record channel plus raw-B memory at W = 40). The gain comes mostly from offsetting the record bias.
5. **DI artefact and value residual.**
   - Under DI, Δ̂ contrasts carry (1 − ϱ) of the record drop and absolute metrics carry the rest, plus ±Δ_p. Both, and even the true candidate value, fail the distance criterion at high rates.
   - Only audited increments are clean: flag rate 0.00 under DI, 0.92–1.00 power for a 0.5 σ_d shift on tabular.
   - Expected residual under DI (fixed split, r = 2): tabular −1.64 to −1.88 (homogeneous noise) or −0.79 to −0.88 (near-null mix); digits −1.2 to −2.4. It is almost all proxy bias, with bias/proxy 0.83–0.88 on tabular. Applied to the observed proxy +0.83, that gives **≈ −0.7 expected under DI**, against the observed −1.22 [−2.22, −0.26].
   - The C3 offline pilot's audited proxy bias, +1.26 (residual → +0.04), lies inside the simulated range. **"Violated in value terms" is not supported.**
6. **Headroom.**
   - Oracle-prior control minus A2+screen at W = 20: digits_on 2.4 δ_n, tabular_on 1.35, digits_off 2.3, tabular_off 0.87.
   - A calibrated predictor with μ error of 1 sd of the type means keeps 0.76–1.06 δ_n. An uncalibrated predictor with 2 sd error loses to A2.
   - The C3 gate is passable on memory-on nodes only with a calibrated predictor (μ error ≲ 0.5–1 sd_types).

## Open points for the author / coordinator

- Re-run `di_test` with audited immediate values and with **audited-increment** next-k outcomes (not abs metric) before any C4 verdict.
- The memory proposer, its bold type and the type mixtures are invented calibrations. The route D sign depends on them.
- Simulated change rates are below the observed ones. The branch mechanics follow the report text, not the harness code.
- Nothing here has been checked by a human (PLAN §9 item 6).
