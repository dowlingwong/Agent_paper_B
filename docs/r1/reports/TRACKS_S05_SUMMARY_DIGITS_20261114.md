# Track S — S0.5 summary, `digits_mlp` part (Mac, 14 November 2026)

**AI-assisted (Claude, Mac-local agent). ENGINEERING_ONLY: these values feed the pre-declaration and are never
quoted as results. Not an author decision.** This is the Mac-side S0.5 summary of Track S operator runbook rev 3.3
(`13badb0d`, sha256 `a93fb84b…`) Phase 4, for `digits_mlp` only. `tabular_mlp` follows; the summary is complete, and
STOP 4 can be sent, only when both nodes are in. Branch `mac-tracks-s05-summary-20261114` from
`trackS-ops-20261030` @ `7593ee5b` (the accepted digits-half record, review `TRACKS_S05_T7_STOP4_REVIEW_20261114.md`).

## 1. Input and command

- Input: `results/r1/tracks/digits_mlp/s05_t7_20261113/` as committed at `7593ee5b`; its `SHA256SUMS` verifies 40/40
  here. `s05_calibration.jsonl` `2e4c9a8c…` (298 rows), `s05b_truncated.jsonl` `cd296fd8…` (200 rows), `roots.jsonl`
  `039b6955…` (50 roots), `manifest.json` `68a0d6e0…`. Seeds are Track S blocks (instances 30500–30519, audits
  200000+), none in 7001–7010 or 9001–9210.
- Code: `r1/tracks/analyze.py` at the run's paper pin `8237fd02` (sha256 `b952af6c…`; the file is identical at
  `7593ee5b`), harness `a3fedbb`, Python 3.13.18 (`/tmp/trackg_venv`). Run with `python -P` so the pin's package is
  imported, not the branch checkout:

  ```
  AR_HARNESS_ROOT=<harness a3fedbb> PYTHONPATH=<paper 8237fd02> python -P -m r1.tracks.analyze s05-summary \
    --node digits_mlp=results/r1/tracks/digits_mlp/s05_t7_20261113 \
    --out results/r1/tracks/s05_summary/s05_summary_digits_20261114.json
  ```
- λ₂: the runbook §11.6 snippet, unchanged, on the same `s05_calibration.jsonl` →
  `results/r1/tracks/s05_summary/lambda2_digits_20261114.json`.

## 2. Values (digits only)

| Quantity | Value |
|---|---|
| Binding share per W (S0.5b; 50 roots) | W 8: 1.00 · W 10: 1.00 · W 12: 0.94 · W 20: 0.04 |
| W (digits alone) | **12**, provisional. W is the largest candidate that binds in ≥ 50 % on **every** primary node, so `tabular_mlp` can lower it |
| σ_cmp,vary | 0.008356 (median paired sd over 298 calibration audits) |
| σ_D between the two pilot policies at W = 12 (m = 20) | **0.0, UCL 0.0** (see §4) |
| σ_D between repetitions, `static:0.00198,0`, W = 12 (m = 10) | sd 0.006834, UCL (80 %) **0.008839** |
| `between_policy_sd_at_cap` (W = 40) | **0.0** (see §4) |
| Near band b | 0.008587 (0.5 × median \|margin\|, 596 eligible E1/E2 decisions; median E1 0.01717, E2 0.02208) |
| λ (obs_inflation) | 1.0 (manifest = prior metadata; the λ check at S0.5 holds) |
| LLM calls / audit runs per campaign | 40.0 / 35.4 |
| Calibration status | **fail** (§3) |

## 3. Calibration gate: fail (design S0.5 (iii), runbook Phase 4)

The gate requires coverage of the 80 % intervals in [0.70, 0.90] overall and in every stratum with ≥ 20 predictions.
It is evaluated **per node**; for `digits_mlp`:

| Stratum (n_group) | n | covered | coverage | in [0.70, 0.90] | Direction |
|---|---|---|---|---|---|
| 0 | 65 | 35 | **0.5385** | no | too low |
| 1-2 | 89 | 60 | **0.6742** | no | too low |
| ≥ 3 | 144 | 136 | **0.9444** | no | too high |
| overall | 298 | 231 | 0.7752 | yes | — |

The q₉₀ of \|z\| (z = (`delta_audit` − `mu`) / `sd`) is 3.14 in stratum 0, 3.11 in 1-2 and 0.98 in ≥ 3. All
three failures are real (n ≥ 20 in each stratum; no null `delta_audit`).

**What the runbook allows**:
- **Coverage too low in stratum 1-2:** the λ₂ revision applies. λ₂ = max(1, (q₉₀ / 1.2816)²) with q₉₀ over all 298
  rows = 2.385, so **λ₂ = 3.463** (`n 298, n_null_skipped 0`). The steps would be:
  - `set_obs_inflation` to `a2u_prior_l2.json`;
  - re-run S0.5 and S0.5b into new `s05_l2` directories with λ₂;
  - every later command uses that prior;
  - a second failure is a STOP.
- **A failing stratum 0, or coverage too high (stratum ≥ 3):** **STOP for the author.** The runbook gives no other
  action. λ ≥ 1 only widens intervals and does not change stratum-0 intervals (they come from the prior alone), so
  the λ₂ revision cannot fix either failure.

Both cases occur here, so the gate **cannot pass through the runbook's only revision**: λ₂ leaves stratum 0 unchanged
and cannot lower stratum ≥ 3 coverage. A λ₂ re-run would therefore end in the second-failure STOP. **This is a STOP
for the author.** The runbook offers the author two things:
1. Order the λ₂ = 3.463 re-run anyway, as the declared one-step revision for the low part only, accepting that stratum
   0 and stratum ≥ 3 stay out of band, so a second failure, and a STOP, is expected.
2. Hold Phase 4 at this STOP. Any other remedy (stratum-0 intervals, which come from the prior; the over-covered ≥ 3
   intervals) is outside the runbook and would be a design change by the author ("anything not covered: STOP and
   ask", §10).

The Phase 4 **fallback** rule (dropping a node whose projected S0.7 + S3e time exceeds 4 days) concerns the Phase 1
time projection, not calibration. It is not an option for this failure, and no projection is computed here.

## 4. Finding not covered by the runbook: the two pilot policies coincide on digits

The two pilot policies are `a2u` (A2-U, `a2u/v2`, prior `5c849d15…`, g = 0.00066) and `static:0.00198,0`
(0.3 σ_node). On every one of the **20** primary (rep-0) instances they took **identical action sequences**:
- E1 skip/execute and E2 keep/discard/failed_invalid agree decision by decision;
- the margins differ slightly, for example E1 0.0172 vs 0.0159;
- so `runs_used` and `y_terminal` are identical at W = 40 and at every truncation W.

Over the 20 a2u roots the actions were: E1 skip 429, execute 318; E2 discard 170, keep 148, failed_invalid 53.

So the between-policy differences D are exactly 0. **σ_D between policies is 0 and its UCL is 0**, at W = 12 and at
the cap (`between_policy_sd_at_cap` = 0, the S0.6 input). These zeros are not variance estimates. A zero σ_D in the
pre-declaration or in S0.6 (`--between-policy-sd`) would make any power or size calculation degenerate. The
between-repetition UCL (0.008839) is not affected.

The runbook has no rule for this, so by §10 it goes to the author, with the calibration STOP. Whether the coincidence
is expected (A2-U's index decisions reduce to the static threshold at this prior and g) is a question for the design
owner. Nothing was changed or re-run here.

## 5. Not done here

- `tabular_mlp` S0.5 (TASL-2 was unreachable on 12–14 Nov); the joint W; STOP 4 itself (the operator sends the author
  W, σ_D, b, λ and the projection).
- No STATUS entry, so that the operator branch is not touched; this report and the two JSON files are the record.

## 6. Files

- `results/r1/tracks/s05_summary/s05_summary_digits_20261114.json`: `tracks_s05_summary/v2`, the full
  `s05-summary` output; `out_dir` is repo-relative.
- `results/r1/tracks/s05_summary/lambda2_digits_20261114.json`: the §11.6 line.
