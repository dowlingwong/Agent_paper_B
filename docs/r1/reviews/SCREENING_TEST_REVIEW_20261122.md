# Review: direct ancestor–descendant screening test (R1-D3-CHOICES (1))

**AI-assisted independent review (Claude, fresh session, 22 Nov 2026). Commits `4b65f91c` (design) and `c9ad184c` (results).** Branch `mac-screening-test-20261122`. Label `ENGINEERING_ONLY`. Rows read: R1-D3-CHOICES, R1-THEORY-RHO, R1-TRACKS-STOP4-END, R1-TRACKS-STOP4-CONSEQUENCES, R1-E1B-RERUN2 (PLAN), and sweep-2 prereg §3 and §6. No sealed partition, evidence audit directory, B.2/sweep-2 audit output or G.1b/G.4 output was opened. The reviewer re-ran `run` to `/tmp` (Track S and E1b only, through the script's own `_refuse_protected`) and ran one post-hoc sensitivity on those data. Nothing in the repository was changed except this file.

## Verdict: ACCEPT WITH MINOR

The permission table is right. The design was fixed before the run: the script is byte-identical between the commits, and `run` reproduces `run.json` exactly. The recommendation follows the pre-specified mapping and is labelled as a recommendation. Five minor findings, all in the wording or the record. None changes the decision.

## Checks

- **Tests:** `python3 -m pytest r1/tests/test_screening_test.py -q -p no:cacheprovider` gives 13 passed.
- **Pre-specification:** `git diff 4b65f91c c9ad184c -- r1/` is empty. The file mtimes are `design.json` 23:12:36, commit `4b65f91c` 23:13:48, then `run.json` 23:13:57 (9 s later). A re-run's output is identical to the committed `run.json`.
- **Post-hoc arithmetic (report:160):** from `design.json` (digits; mean, sd): p = 0.37 (0.311, 0.096) gives Φ(−2.32) = 0.010; p = 0.24 (0.209, 0.098) gives 0.107; the kernel (−0.001, 0.107) gives an upper tail of 0.206. The report's 0.01 / 0.11 / 0.21 are correct and labelled "post hoc and approximate".
- **Seeds 3301–3360:** clear of every interval in `RESERVED_SEED_NAMESPACES` (`r1/c3/d3_analysis.py:134-149` @ `mac-d3-predecl-20261122`). Also clear of the D.3 blocks (6201–6218, 6301–6329, 6501–6679, 6701–6880) and of the sweep instance universe (computed: 90 seeds in 100–275). Every noise-floor manifest under `results/r1/noise` and `results/r1/pilot` has `seeds_per_condition` ≤ 30, so the joint block ends at 3030.

## MAJOR

None.

## MINOR

1. **Stale docstring states the superseded c0 rule.** `r1/noise/screening_test.py:32-33` says c0 is "the one configuration hash audited on every primary instance". That is the rule which failed on metadata (report:62). The code (`:311-337`) and report §2.3 use the second-distinct-hash rule.
   *Fix:* a one-line docstring correction in a separate commit, with a note in §2.6 that it changes no code path.
2. **The post-hoc comparison is model-dependent, and the report does not say so** (report:160, 186). The reference simulation assumes ϱ = 0.82 on every link. The realised links differ: on digits the mean g–p correlation is 0.37 (c0 → I_8 spans several keeps) and the mean p–c is 0.81. Reviewer sensitivity on digits, post hoc: triples with r_pc < 0.95 give +0.17 (n = 23); those with r_pc ≥ 0.95 give −0.14 (n = 8).
   *Fix:* add one sentence saying the reference geometry does not match the data. Soften §4.1's "the T5 target calibration looks less likely" to "is not supported, against a reference whose link geometry differs from the data".
3. **The tabular NO_SHARED comes from near-duplicate links; this should be said** (report:163-166). Of the 38 eligible triples, 36 have r_pc ≥ 0.95, and sd(c − p) ≈ 0.001 for the excluded ones. Triples that start at c0 average −0.04 (19); triples of later incumbents only average −0.41 (19).
   - It is not an n = 5 bias. The null of a 5-point partial is Uniform(−1, 1), which is symmetric; the per-triple sd here is 0.573 against 0.577. The exclusions select on |r|, not on sign.
   - A smooth, non-Markov error field across tiny edits does give negative partials, because the error of p is then close to an average of the errors of g and c.

   *Fix:* add these two points to §3.3 item 3. Keeping "not interpreted further" is fine.
4. **§4.1 second bullet (report:187) moves Track S content into the manuscript.** It asks the limitation to "name both directions". The negative direction rests on Track S, which R1-TRACKS-STOP4-END and CONSEQUENCES (9) bar from use as a result even without numbers, and on the tabular E1 proxy, which is PILOT and awaits R1-THEORY-RHO (5).
   *Fix:* keep "the scope statement must not imply the kernel holds on the T0 nodes". Drop "name both directions", or make it conditional on R1-THEORY-RHO (5).
5. **The §4.2 power table has no record, and it is optimistic** (report:200-205). No committed file holds the command or its output. A reviewer reproduction, `power_e1b([3]*18, 60, s, nsim=100)`, gives 0.85 / 1.00 / 0.91 against the reported 0.86 / 1.00 / 0.91. The simulation also treats the 18 triples as independent lineages from c0. In the design, each c_ij appears in two triples and each c0 + e_i is the middle of up to four, so the effective count is lower.
   *Fix:* record the call and its output (for example in `run.json` or a small JSON), and add "upper bound; shared members not modelled".

## NOTE

1. **c0 identification (report:61-63) is neutral but can't be dated by git.** Both rules predate `4b65f91c`. The new rule uses only hashes, seeds and file order, and the change was forced by a metadata failure. Its correctness rests on two things, both verified on `origin/trackS-ops-20261030`:
   - candidate-first order in `collect.calibration_rows` (`r1/tracks/collect.py:1008-1009`);
   - `AuditCache` writing each (hash, seed) once (`:379-393`).

   The check that all 20 instances agree is a weak safeguard, because campaigns start alike (report:62).
2. **"No audit value read" holds for what was used and emitted, not for what was loaded.** `design` parses whole rows of `s05b_truncated.jsonl` and `audit_runs.jsonl`, value fields included (`screening_test.py:306, 324, 343`). It uses only metadata, and `design.json` holds no value. I could not check whether files were viewed interactively.
3. **Permissions (report §1).**
   - Track S: R1-TRACKS-STOP4-END limits citation, not reading, and no guard covers it (the re-run passed `_refuse_protected`). The verdict is correct.
   - B.2, sweep-2 audit, G.1b and G.4: the "No" verdicts are correct. The two "unclear, not opened" calls are conservative and appropriate.
   - E1b: its instances are the P3 T0 seed universe (R1-E1B-RERUN2, k = 0–17; prereg §3), so its values touch P3 test instances. Prereg §6 does not bar this, since there are no label or evaluation seeds, and E1b decides nothing. List it for the arms-frozen disclosure if this test is cited in the D.3 record.
4. **Method.** Centring is a no-op inside a sample correlation; it is harmless.
   - Pooling r rather than Fisher z is right: Var z ≈ 1 at n = 5, and z is unbounded as |r| → 1.
   - The instance-cluster bootstrap matches the dependence (overlapping triples, one seed set per instance). With 17–19 clusters it may under-cover slightly. The simulated null P(SHARED) ≤ 0.002 already includes this, because the simulation uses the same estimator, exclusions, K = 5 and chain lengths, so attenuation (0.31 against 0.37) is built into the power figures.
   - The kernel unit test uses K = 10 (`r1/tests/test_screening_test.py:70`). The K = 5 null is covered only by `design.json` (mean −0.001).
5. **The E1b seed bootstrap with K = 6 degenerates.** Resamples with ≤ 3 distinct seeds give partials of ±1, hence the bounds at ±1.00 in §3.2 (d). This is acceptable for a descriptive table.
6. **Small wording points.**
   - Report:101 says 0.20 where `design.json` has 0.209; report:160 says 0.21.
   - Report:208 calls 0.9 s "wall time … under parallel load" but then states CPU-minutes. Say which.
   - If Option A is adopted, add 3301–3360 to `RESERVED_SEED_NAMESPACES`.
7. **Conclusions (§4).** INCONCLUSIVE maps to the row's "otherwise" branch, as R1-D3-CHOICES (1) is worded, and "R1-THEORY-RHO (2) stands" sits under "recommendation, not a decision" (report:179, 183). The underpowered-digits caveat is explicit (report:186).
   - Option A is coherent: 15 configurations; 9 children = C(5,2) − 1, because two edits share `HIDDEN_UNITS`; cost 900 × 0.9 s ≈ 13.5 min and 7,000 × 0.9 s ≈ 1.75 h.
   - An underpowered screen defaulting to "stands" is a weak gate. The report says so and offers Option A.
