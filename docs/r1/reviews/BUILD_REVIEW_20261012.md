# L14 build review — 12 October 2026

*A fresh-session AI-assisted review (a Claude subagent that had not seen the work) of the R1 build as it stood on 12 Oct 2026, followed by one correction round by the implementing session. This is not a human review. The reviewer's full report was delivered in-session; its findings are reproduced here in short form, each with its disposition.*

**Scope.**
- Paper B `r1/` package: L9, L10, L12, L13, the T2/T3 code, and the E1/E1b tooling.
- Harness diff `b55209f..c686517`: L8b nodes, the L7 resume fix and the L12 charging.
- Theory docs T1–T3 and the E1 report.

**Reviewer checks:** 50 pure-Python tests rerun; resume semantics traced; the oracle bias simulated; the T2 numbers recomputed.

## Findings and dispositions

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | MAJOR | `llm_control.py`: a non-dict `scores` raised `AttributeError`. Inside a hook this would abort the campaign. | **Fixed**: any parse error falls back to `continue`. Tests added. |
| 2 | MAJOR | Harness `_complete_captured_trial`, E1 path: the worker run and the revise LLM call were not charged. Also no exception handling, no proposal metadata and no revision digests. | **Fixed** in harness `4e8fd69`, with tests. **Open:** `repeated_bad_count` stamping on resumed E1/skip records. |
| 3 | MAJOR | With R = 2, the "cross-fitted" oracle is biased downward as an estimate of headroom, and the name was misleading. | **Fixed**: renamed `oracle_leafsplit`. Reports now give the bracket [leaf-split (biased down), naive (biased up)]. The naive oracle's upper CI is the conservative upper bound. |
| 4 | MAJOR | E1b ran verify under `"fixed"` on `openml_ionosphere`, where T2 Proposition 3 predicts it is worthless (σ_t ≪ σ_s). | **Addressed**: a `"vary"` sensitivity run on `openml_ionosphere` (`E1b_vary_ionosphere_20261012`) is reported next to the main run. The other deviations from 0.4b are stated in the report: E2 actions only, PACE not scored, horizon = rest of budget, scripted proposer. |
| 5 | MAJOR | The KG index priced verify with the Bayes response under `"vary"`, but the harness executes the frozen response under `"fixed"`. | **Fixed**: `KGIndex(response="frozen")` is now the default and uses the campaign's split policy (feature `split_policy`). The Bayes VoI stays available as `response="bayes"`, an upper bound. |
| 6 | MAJOR (plausible → confirmed) | The new nodes printed `test_score`. `LocalWorker` parses every `key: value` line, so the test metric reached the ledger and the LLM side query. | **Fixed** in harness `4e8fd69`: the score is no longer printed. Earlier E1/E1b ledgers contain it, but no R1 arm reads it (features are built from `val_score` only). |
| 7 | MINOR | `_resolve_first_action` built the mask without compute headroom, so a forced verify could overshoot `max_worker_runs`. | **Fixed** in `4e8fd69`, with a test. |
| 8 | MINOR | `build_table` ignored `executed_action`, so a rejected forced action would be scored as the action requested. | **Fixed**: such an action is treated as unobserved at that point. Test added. |
| 9 | MINOR | If every verify pair fails, the response is `reject` and vetoes a keep on missing evidence. | **Open, for the author**: declare the rule (keep the original decision vs reject). |
| 10 | MINOR | The LLM-call cap is soft within a trial: it is checked only at the top of the loop. | **Open, documented here.** The charge is correct; the overshoot is at most the trial's remaining decisions. |
| 11 | MINOR | `best_simple` is chosen in-sample and held fixed in the bootstrap; per-policy undefined points can differ. | **Documented** in `evaluate.py`. No change. |
| 12 | MINOR | `harness_heuristic` (repeated_bad is always 0 at E2) and `random_matched` (matched to the KG rate of 0) were identical to ρ. | `random_matched` now matches the most interventionist tuned arm. `harness_heuristic` is labelled degenerate at E2 in the report (it is an E1 skip rule). |
| 13 | MINOR | `IndexController` hard-coded `n_keeps = 0` and ignored metric direction. | **Fixed**: n_keeps comes from the ledger digests; direction is respected. |
| 14 | MINOR | σ_d = hypot(median σ_t, median σ_s) overstates the paired noise. E1 shows the two seed effects are not additive. | **Fixed**: σ_d is the median sd_joint, with the components rescaled. Noted in the E1 report and in T2's limits. |
| 15 | MINOR | The PACE-style docstring overstated its null: clipping changes it. | **Fixed** (docstring). |
| 16 | MINOR | L10 spec gaps: no risk-ranked ridge, no two-step continuation-value rule, PACE not scored. | **Open**: both rules are secondary under the revised PLAN §5. PACE needs a `verify:pace` action version (D4). |
| 17 | MINOR | Labels missing from `summary.json`/`analysis.json`; the e2e directory said `PILOT`; STATUS had no entry. | **Fixed**: label fields added, e2e writes `ENGINEERING_ONLY`/`engineering`, STATUS entry added. |
| 18 | MINOR | The second row of the T2 Proposition 5 table was wrong (max VoI does not depend on μ₀). | **Fixed**: 0.0018 / 0.0009; threshold g < 0.00044. |
| 19 | MINOR | E1 report: the P(wrong) plug-in is capped by selection at about 0.26; two ranges were misquoted. | **Fixed** in the report. |
| 20 | MINOR (plausible) | `mlp_synthetic` defaults would change if the worker exported empty seed variables. | **Checked, not a defect**: `seed_environment` leaves a variable untouched when its seed is `None`. |
| NIT | — | T2 wording (concavity, the σ_d = 0 edge case, figures valid only under `"vary"`); `_tune` tie-break; a vacuous test; `np.trapezoid` needs numpy ≥ 2; an unused import. | Wording fixed in T2. `_tune` now prefers fewer interventions on ties. The test was rewritten. The import was removed. numpy ≥ 2 is noted. |

## Items the reviewer checked and found correct

- Default behaviour of the harness changes: no new event fields or records under the default controller.
- Resumed E2 commit semantics after `f0dcd6a`: one append per trial, restore on non-keep, stack push on keep, verify charged, matched compute between siblings.
- Action semantics against the L6 table and D4.
- Leak safety of the offline arms under leave-one-instance-out.
- The cluster bootstrap (instance resampling, shared draws).
- T2 Propositions 1–4 and the Proposition 5 prices.
- The L12 forked-context guarantees.

## Suites after the correction round

- **Harness:** 347 passed, 9 failed, 1 error (the pre-existing environmental set: `/bin/zsh`, missing KDD sections and manifests, the claw-code submodule).
- **Paper B `r1/tests`:** 64 passed.
