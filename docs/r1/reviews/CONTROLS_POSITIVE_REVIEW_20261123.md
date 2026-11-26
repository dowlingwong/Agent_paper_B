# Review: positive control (R1-CONTROLS-ROW), commits `9396b915`..`56313e1f` — 23 November 2026

**AI-assisted independent review (Claude, fresh session, 23 Nov 2026). Not an author decision.** Branch `mac-controls-pos-20261123`. Reviewed: `docs/r1/reports/CONTROLS_POSITIVE_20261123.md` (report), `r1/noise/controls_positive.py` (script), `r1/tests/test_controls_positive.py`, `results/r1/engineering/controls_positive_20261123/`. Governing rows: R1-CONTROLS-ROW (read from local `author-minsub-20261122` @ `aaaabba3`; `origin/author-minsub-20261122` does not contain it, as report:5 says) and R1-E1-PILOT-ACCEPT (PLAN.md:1417). No sealed partition, test/evaluation block, sweep audit output or `E1_D28_REPAIR` run data was opened.

## Verdict: ACCEPT WITH MINOR (0 MAJOR, 6 MINOR, 7 NOTE)

The statistic, the δ_n values, the computation and the scope are correct and reproducible. The minor findings tighten the wording of §4 and one header claim. None changes a number.

## Verified (no finding)
- **Statistic.** The report uses the paired mean over common joint seeds with sd at ddof = 1, as `r1/c3/audit.py:391–398` (`paired`) computes it. K = 5 is the label/evaluation half (`audit.py:1013–1019`), and K = 10 is y_raw of a one-edit campaign (D.3 draft §7.1). This matches `C3_DESIGN.md:67`, preregistration `:18`, `:20` and `:131–134`. Every cited line was checked.
- **δ_n.** I recomputed D18 independently from the 22 Oct `summary.json`: 0.002 (digits, tabular, credit_approval, breast_w, wdbc), 0.003990 (ionosphere), 0.003192 (sonar). For the four current-start nodes, the JSON's `delta_n_pinned` equals these values.
- **§1 before computation.** Report lines 1–58 are unchanged from `9396b915` (13:52:49) to `56313e1f`. The script came in `b1d0eb61` (13:56:25) and the outputs in `1cfc3d18` (13:57:16). `ba259f93` changes only the summary key strings, and no probability moves.
- **Re-run.** `python3 -m r1.noise.controls_positive --out /tmp/…` produced byte-identical files: JSON sha256 `1ee1bc9d…`, tables sha256 `2917014d…`. The JSON's `script_sha256` matches the current script (`f94a9872…`). The outputs contain no absolute paths.
- **Hand spot-checks.** These used my own enumeration and an independent RNG, not the script:
  - credit_approval → gradient boosting, K = 5 exact: R-δ 0.8341, R-t 0.1977, R-0 0.8982. K = 10 Monte Carlo: R-δ 0.9405, R-t 0.4143.
  - tabular_mlp BATCH 64 → 32: K = 5 R-δ 0.7202, R-t 0.8845. K = 10 R-δ 0.8366.
  - wdbc C × 2: K = 10 R-t 0.5036, R-δ 0.
  
  All agree with report:133–162 to the third decimal, or within Monte Carlo error.
- **Analytic values.** Super 0.8991, fpc 0.9410 (equal to the resampled 0.941), Δ̂ − 2 se 0.5485, noncentral t 0.4584. The finite-population factors are 2/3 and 5/6. The largest resampled-minus-super gap over the 8 informative cells at K = 10 is 0.0416, so "≤ 0.042" holds. Other R-δ super values are ≥ 0.996 (K = 10) and ≥ 0.969 (K = 5). |R-δt − R-t| ≤ 0.00084.
- **Classification.** The ±2 se class rule (script:134–141) gives near, not above, at the borderline rows (credit C × 0.5, tabular BATCH, breast_w RF, sonar C × 0.5).
- **Scope.** `openml_climate` is not in the accepted run (script:264–266), and breast_w, sonar and wdbc are flagged `pre_repair` (script:62, :268). Both are stated in report:83–89 and :226.
- **Tests.** `python3 -m pytest r1/tests/test_controls_positive.py -q -p no:cacheprovider`: 14 passed.

## MINOR
1. **report:3, "reads only the accepted 22 Oct E1 runs", is incomplete.**
   - The script also reads the pinned noise source `results/r1/noise/D28_REPAIR_20261027/summary.json` (script:26–27, :231–237, :396). For breast_w, sonar and wdbc, its constants come from the R1-D28-REPAIR re-measurement, which R1-E1-PILOT-ACCEPT does not cover. The R-δ at the pinned δ_n for sonar uses it.
   - *Fix:* add to report:3 "and, for the δ_n/σ_node comparison only, the sha256-checked pinned noise source; no per-edit effect is read from it".
2. **"of the size the paper cares about" (report:194, :211–212) overstates the tested range.**
   - The 8 informative improvements are 3.4–12.5 δ_n (JSON `effect_over_delta_n`).
   - Improvements of about 1–3 δ_n also meet the paper's target δ_n. They fall in the near class (current start: 0.352–0.866 at K = 10).
   - *Fix:* state "3.4–12.5 δ_n" in the §4.1 heading, and replace "at least δ_n (with margin)" at :211 with that range.
3. **The plug-in sensitivity is quoted at K = 10 only (report:222, 0.548).**
   - §4.5's gate reading rests on K = 5 (≥ 0.817). At Δ̂ − 2 se the weakest K = 5 cell is 0.534 (report:183; reproduced 0.5343).
   - *Fix:* add "(0.534 at K = 5)" at :222, and repeat it in §4.5's second bullet.
4. **report:217, "a property of the proposals and the arms, not of the measurement", is stronger than the evidence.**
   - Report:214 itself lists the gate's power (finite test instances, plus five-seed evaluation noise aggregated over proposals) as a cause. That is a property of the measurement design, not of the proposals or the arms.
   - *Fix:* "not of a per-edit audit that cannot see such improvements; the gate's power remains a separate explanation".
5. **report:116 states the optimism for every reading, but it holds for R-δ and R-0 only.**
   - In the weakest informative cell, the resampled R-t is below the noncentral-t value: 0.416 vs 0.458 at K = 10, and 0.198 vs 0.255 at K = 5. Non-normality pushes R-t differences in both directions.
   - *Fix:* "the resampled R-δ and R-0 probabilities are somewhat optimistic".
6. **Pre-repair rows are pooled without a label in two places.**
   - `tables.md` Table C (script:304–319, :368–374) prints groups that mix current and pre-repair rows: "above" (16), "above, improvement" (9), "near" (7) and "below" (12). It does not say so, although `tables.md` is a standalone output.
   - §4.5's near range "0.35–0.89" (report:215) takes its maximum from pre-repair breast_w RF (0.889). It is also a K = 10 figure, while the gate reads K = 5. The current-start range is 0.352–0.866 at K = 10 and 0.413–0.758 at K = 5.
   - *Fix:* add one sentence to the `tables.md` header (script:343) saying that the 1- and 2-key groups pool pre-repair rows. In §4.5, quote the current-start range at K = 5.

## NOTE
1. **What §1 fixed.** §1 fixed the statistic, the readings, δ_n's source and K. The ±2 se class rule and the definition of "informative = current-start improvements clearly above δ_n" were fixed in `b1d0eb61`, not in §1. Commit order cannot rule out an earlier uncommitted run. No fix needed; §2 may say so.
2. **The governing row is on an unpushed branch.** R1-CONTROLS-ROW exists only on local `aaaabba3`. This acceptance assumes the row lands on the shared branch unchanged.
3. **report:49, "i.e. S = 1".** The 9 Oct spec's S = 1{Y > δ_n} uses the normalised Y. The equivalence holds only with δ_n read in metric units on y_raw, as :55 says. *Fix:* "S = 1 with δ_n in metric units".
4. **report:224, audit seeds.** D.3's Y uses per-instance seeds 6701–6880 on deepthought (D.3 draft §7.2), not 7001–7010. The exchangeability caveat covers this; name both seed sets.
5. **Sonar at the pinned δ_n.** At 0.00342, sonar C × 2 R-δ falls from 0.954 to 0.940 (K = 10) and from 0.863 to 0.823 (K = 5), so §4.4's "≥ 0.954" becomes "≥ 0.940". This affects pre-repair rows only, and the reading does not change.
6. **Which copy the test compares.** `test_t0_nodes_match_the_gate_copy` (test:208–210) compares the script's list with `r1.c3.p3_split.T0_NODES`, which is itself a copy, not with `gate.T0_NODES`. I confirmed that `r1/c3/gate.py:153–154` holds the same tuple. *Fix:* report:73 should say "p3_split's copy of `gate.T0_NODES`".
7. **A direct source for the current-start claim.** R1-D28-REPAIR (PLAN.md:595) says "the 22 Oct values remain for the four unchanged nodes". Citing it at report:85 and :231 is stronger than relying on the pinned source's provenance.

## Not checked
- The pinned noise source's `sources` field: which nodes it takes from the 22 Oct summary, and that it records sha256 `eabc2f5c…` (report:24–26, :76). A direct read was refused by the session's permission system. Only the script's sha256-checked use, and the matching δ_n and σ_node values in the JSON, were seen.
- Code identity of the four current-start nodes between harness `4012897` and the sweep pin.
- Cross-host equality of the metrics.
- The report's uncommitted ad-hoc K = 5 Monte Carlo check.
