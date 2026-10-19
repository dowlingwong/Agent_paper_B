# C3 offline pipeline — overnight handoff (19 Oct 2026)

**ENGINEERING_ONLY. AI-assisted (Claude), overnight agent.** Branch `overnight/c3-offline` (worktree `.claude-worktrees/c3-offline`), fast-forwarded to `main` at `a312f89` before work. Not pushed. `docs/r1/STATUS.md` and `docs/r1/PLAN.md` are untouched. No LLM, Ollama, GPU, SSH or network use. CPU worker runs only: 672 runs, ≈ 13 CPU-minutes, plus about 12 CPU-minutes of tests.

## What was built (`r1/c3/`)

| Module | Content |
|---|---|
| `rules.py` | T4 closed forms: `value` V(t; μ, τ, σ), `bayes_threshold` t* = −μσ²/τ², `proposal_value` (1−π)V(t*), `execute` (V* ≥ g), `keep` (Δ̂ > t*), `decide`, Proposition 7 `gap_exact` (closed-form integral), `gap_bounds`, `gap_approx`, Proposition 8 `screening_term` (g − V*)⁺. |
| `labels.py` | 12 bins (bin 0 exact-inert; z edges −∞, −3, −2, −1, −0.5, −0.15, 0.15, 0.5, 1, 2, 3, +∞), `soft_label` = N(Δ_audit, se²) integrated over bins (inert → bin 0 = 1), `moments` → (π, μ, τ) from midpoints (tails ±4) × σ_node, `prob_positive`, `log_score`. |
| `features.py` | Ledger replay from the start configuration with the logged structured edits (harness `_apply_edit` regexes, stale-edit check) → candidate and incumbent file texts per proposal. Features exactly by C3_DESIGN §3 groups. Task: node, rows, features, classes, minority share, model type. Edit: key, old/new, log ratio, direction, structural, D25 active key, incumbent-equal, D27 active and full seen-before. Ledger: key edit count, last Δ̂/σ and decision for the key, keeps, trials since keep, recorded gain/σ, budget fraction left, memory mode, invalid count, same-edit count, reversal flag. Leakage: features of trial n are frozen before trial n's outcome enters the history (tested). Replay self-checks: incumbent-equal ⇒ Δ̂ = 0; re-evaluated active configuration ⇒ same metric. |
| `audit.py` | Candidate and incumbent on K common fresh joint seeds (default 7001–7006) via `LocalWorker.run_trial_at_seed` with a no-edit proposal on an isolated node copy (same mechanism as E1 / `e1b_collect._audit`). Run cache `runs.jsonl` keyed by (node, config hash, seed), written per configuration. Time-boxed, resumable `run` and `collect` CLI. |
| `dataset.py` | `build` (proposal table, configs by hash, replay checks, E1 noise table: σ_node = median material sd_joint; σ per edit kind local / model_type; δ_n = max(0.002, 0.25 × median sd_joint over all E1 edits), which reproduces PLAN D18's ≈ 0.002 / ≈ 0.004). `plan` (seeded stratified random audit sample + `--di` DI-changed candidates, checked against E2 snapshots). |
| `arms.py` | A1 constant per-node prior; A2 = A1 + rules (π = 1 on incumbent-equal / duplicate / inactive-key); A3 LightGBM multiclass on 12 bins, soft labels by sample-weight expansion, same rule override. τ floored at 0.15 σ_node. |
| `offline_eval.py` | One-step realised value Σ(Δ_true·keep − g·execute) per arm with the logged Δ̂. Cross-fitting by instance seed (k = 3) and LONO. g grid in σ_node units. Log score, P(Δ > 0) and π calibration, T4 Proposition 7 / 8 checks. C3 gate per g: 20 × mean per-proposal (A3 − A2) vs δ_n, instance-cluster bootstrap 95 % bound, pass iff ≥ 2 nodes. Stratum inverse-sampling weights; DI-only audits train but do not evaluate. **Label/value seed split by default** (see findings). |

Tests: `r1/tests/test_c3_{rules,labels,features,audit,arms_eval,dataset}.py`. Rules are checked against Monte Carlo (10⁶–2·10⁶ draws), plus synthetic replay and leakage tests, cache/resume with a fake worker, one real seed-determinism worker run, synthetic learnable / unlearnable gate behaviour, and the real committed ledgers (0 replay violations, 19 DI candidates).

## How to run

```sh
cd <worktree>; export PATH=$HOME/scratch/hv313/bin:$PATH AR_HARNESS_ROOT=$HOME/mnt/autoresearch_harness \
  OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
D=results/r1/engineering/c3_audit_pilot_<UTC>
python -m r1.c3.dataset build --out $D
python -m r1.c3.dataset plan --table $D --di            # or --quota source:node:n ...
python -m r1.c3.audit run --plan $D/plan.jsonl --configs $D/configs.json --out $D --workers 4 --deadline 140   # repeat until configs_remaining = 0
python -m r1.c3.audit collect --plan $D/plan.jsonl --out $D
python -m r1.c3.offline_eval --table $D                 # --no-seed-split for the all-seeds variant
python -m pytest -q r1/tests/test_c3_*.py
```

`PATH` must put the venv's `python3` first: node `run_command`s call `python3`. On the VM the system `python3` has no sklearn, so every run fails silently with no metric. On Ada/Deepthought, use the harness `.venv`.

## Test results

- `r1/tests/test_c3_*.py`: **40 passed** (4.3 s).
- Full `r1/tests`: everything passes except `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun`. That test assumes the source repository's checked-out branch is `main`: the fake runner pushes `main` and then `ls-remote refs/heads/main` returns nothing in a worktree on `overnight/c3-offline`, giving `IndexError`. On a clean clone of `main` it fails differently (nothing to commit in its fixture). It is environmental and unrelated to C3. Before that fix, three LightGBM tests failed inside the dry-run's harness venv (no lightgbm), so they now `importorskip("lightgbm")`.

## Pilot numbers (details: `docs/r1/reports/C3_OFFLINE_PILOT_20261019.md`)

- Table: 1,323 proposals from 1,400 root-ledger rows; replay violations 0.
- Audited: 166 proposals (150 random: 70 tabular memory-on, 54 breast-w memory-on, 26 digits DT4; plus 19 DI candidates, 3 overlapping). 672 runs, 0 failures, 216 s wall on 4 workers.
- **Cost:** 1.16 s per worker run. 4.7 run-seconds per audited proposal with incumbent sharing (13.9 s without). 1.3 s wall per proposal on 4 workers. A rerun-2-sized sweep (≈ 1,000 non-inert) is ≈ 1.3–3.9 CPU-hours.
- **Offline gate quantity (seed split, instance cross-fit):** no g gives ≥ 2 passing nodes. Digits (6 instances) shows +0.005 to +0.0075 per 20 runs with CI > 0. Tabular is +0.0021 [−0.0002, 0.0040] at g = 0.1σ. Breast-w is ≈ 0 (increments far below σ_node). Without the seed split the pilot "passes" at g = 0.05σ and 0.1σ: an artefact of shared audit noise across recurring (candidate, incumbent) pairs. One LONO cell passes, which is consistent with multiple-g noise. **Not a gate decision.**
- **DI candidates:** with the fresh audit replacing the selected D̄, the memory-on tabular value residual moves from −0.00122 [−0.00222, −0.00026] to +0.00004 (point estimate). Memory-off digits moves from +0.00051 to −0.00003. The verify direction agrees in sign with the audit at only 7/13 tabular points. Per-point numbers: report §3 and `di_candidate_audits.json`.

## Known gaps and open issues

1. **Duplicates ≠ zero increment.** 727 of 841 rule-inert proposals duplicate a *non-incumbent* evaluated configuration, and 520 have Δ̂ ≠ 0. T4 §1's "Δ̂ = 0 on I_n" holds only for incumbent-equal and inactive-key edits. For duplicates, Δ̂ is known before the run. The skip rule is unaffected and A3 − A2 is unaffected, but the label "inert ⇒ Δ = 0" and A0/A1 levels are wrong for them. Needs an author decision: a known-Δ̂ category, or a T4 §1 wording fix.
2. **Seed split for labels** halves K for each role (3 + 3). For the sweep, use K = 10 (5 + 5) or a separate evaluation-seed audit.
3. g is not pre-declared or dev-tuned. The gate must be computed at one declared g (or a declared g-selection rule on dev instances), or the multiple-g search inflates passes.
4. "Scaled to a 20-run campaign" is implemented as 20 × the mean per-proposal value (one logged proposal = one run in W = 20 roots). Under screening, skipped proposals free runs for more proposals. That is not modelled (needs the LLM-call cap).
5. A1 lacks the D23 KG-verify part. Verify lies outside this one-step evaluation.
6. Liveness and ionosphere were not audited. The DT4 ionosphere stratum is 100 % inert. The memory-on source is the PARTIAL arm (fixed split).
7. LightGBM hyperparameters are untuned defaults for tiny data. The NGBoost variant and A4–A6 were not built.
8. Δ_true for audited proposals is the fresh K-seed mean (noisy, se ≈ 0.0008 on tabular, ≈ 0.0019 on digits). It is unbiased for the one-step value, but it inflates the variance of the gate estimate.
9. Sigma per edit kind: MLP nodes use σ_node for every edit. OpenML uses local/structural medians from E1 (breast-w local σ ≈ 0.00045 vs σ_node 0.0039).
10. The `di_test` bootstrap was not re-run with audited immediate values. That is the natural next step for C4, and it needs a change to `r1/diagnostics/di_test.py`, which this session did not modify.
