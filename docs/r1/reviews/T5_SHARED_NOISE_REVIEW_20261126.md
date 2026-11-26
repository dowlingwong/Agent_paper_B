# Review: T5 re-run with a shared-component error model (`mac-t5-shared-20261122`)

- **Unit:** branch `origin/mac-t5-shared-20261122`, tip `d0ef5282` (2 commits: `8f7c6386` theory model, threshold correction, kernel-free check; `d0ef5282` digits_mlp re-run and note). Merge base with `origin/main`: `52f4e3e5`.
- **Reviewer:** fresh Claude Code subagent, 26 Nov 2026, AI-assisted. I did not write any part of the unit. Tier S, first (fresh) review.
- **Scope:** `docs/r1/theory/T5_SHARED_NOISE_20261122.md` (the note), the `r1/theory/simulate_t4.py` diff, `r1/theory/t5_shared_report.py`, `r1/theory/t5_shared_tables.py`, `r1/tests/test_t5_shared_noise.py`, `results/r1/engineering/T5_shared_20261122/`, and the PLAN rows R1-THEORY-RHO (4) and R1-D3-CHOICES (1) on `origin/main` (`docs/r1/PLAN.md:1467-1468`).

**What I ran.** All runs were in a detached worktree of the tip, on macOS with Python 3.11.4, NumPy 1.24.3, SciPy 1.11.1 and pytest 7.4.0. The unit was produced on Linux with Python 3.13 and NumPy 2.5.3. `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, `--basetemp` in the scratchpad.
1. `pytest r1/tests/test_t5_shared_noise.py r1/tests/test_t5_simulate.py`: **22 passed** (8 new and 14 existing T5 tests). These are the only test files that import `simulate_t4`. The same 22 tests also pass on the merged tree.
2. `git merge-tree --write-tree origin/main origin/mac-t5-shared-20261122`: **clean** (tree `22595c56`). `origin/main` has not touched `r1/theory/` since the merge base.
3. `t5_shared_tables --out <copy of committed parts>`: the regenerated `tables.md` and `reproduction.json` are **byte-identical** to the committed files.
4. `t5_shared_report --only` re-run of six committed parts from the committed code: `calibration`, `main_digits_on_record_W20__shared_0.7891`, `ecorr_digits_on_W20__all`, `p9_digits_on__all`, `a1rho_digits_on_W20__all` and `di_digits_hom_fixed_rho0.8__shared_mid`. That is about 47 CPU-s and 3,583 stored values. Every value matches the committed part. The largest relative difference is 4.6e-14 for every value except one: a `kfree.min_margin_general`, which is a near-cancellation and matches to 3.4e-10. No non-float value differs. The SHA-256 of `simulate_t4.py`, `t5_report.py` and `t5_shared_report.py` in `manifest.json` equal those of the committed files.
5. I re-derived the algebra by hand: the marginal correlation, the sibling partial correlation and its closed form, the inverse `shared_share_for_partial`, the reachable maximum ϱ/(1+ϱ), the s values 0.7891 and 0.7082, the §2 sibling partials (0.207 local–structural at s = 0.55), the structural paired sd 8.12, and the `known` threshold. I also spot-checked about 25 derived figures in the note against `tables.md`: the residual ranges, the first-keep residuals, the headroom ratios 1.34/1.55/1.78/2.12 and 1.12/1.26/1.27/1.56, the A2 − ρ falls 0.8–2.2, 2.3–5.0 and 1.5–3.4, the §4.8 example, and the feasible and oracle ranges 0.2–5.7 and 1.3–10.0 δ_n. All of them agree.

## Findings

### MAJOR

None.

### MINOR

**m1. R1-D3-CHOICES (1) quotes the oracle-prior row as A2's** (`origin/main:docs/r1/PLAN.md:1468`; source `docs/r1/theory/T5_SHARED_NOISE_20261122.md:336`, `results/r1/engineering/T5_shared_20261122/tables.md:380,393`).
- The row says the re-run "sizes the gain from correcting **A2's** threshold on `digits_mlp` at +0.47 δ_n (feasible, keep-count rule) to +1.84 δ_n (oracle)".
- +0.47 and +1.84 are the **oracle-prior** base, digits_on, W = 20, at the target s = 0.79.
- For base A2 in the same cell, the note and `tables.md` give +1.38 (table) and +3.27 (known).
- Across nodes and budgets at the target, the A2 correction is +1.38 to +5.70 (feasible) and +3.27 to +9.97 δ_n (oracle). The row therefore understates the A2 correction and gives one cell as if it covered all of `digits_mlp`.
- The decision itself (run a direct ancestor–descendant test first) does not depend on the size. The rest of the row matches the results: A1 is below the default rule in every cell, the calibration rests on PILOT data, and the E1 pattern is not reproduced.
- **Fix:** the row is the author's, so the unit cannot change it. Raise it with the author. The row should either say "oracle-prior base, digits_on W = 20", or quote the A2 figures (+1.38 to +3.27 δ_n at digits_on W = 20; +1.4 to +5.7 feasible and +3.3 to +10.0 oracle over the four cells). The note's own §5 row (line 336) is correct, but it puts four numbers in one sentence. Splitting it into "oracle prior: table / known" and "A2: table / known" would prevent a second misreading.

**m2. The "bracket" for the threshold correction is stated as a theorem, but it is a heuristic** (`docs/r1/theory/T5_SHARED_NOISE_20261122.md:283-286`, `:351`).
- The note says `known` is "an upper bound on what any history-based correction can be worth", `table` is "a lower bound on the Bayes correction", and "the Bayes correction given the history lies between table and known".
- Each rule is a per-proposal (myopic) Bayes threshold. The objective is the campaign total under budget W, and a keep changes the incumbent and every later comparison. More information per decision does not by itself bound the campaign value of a myopic rule. "Conditions on less" does not make a myopic rule worse at the campaign level either.
- For base A2 the plug-in (μ̂, τ̂) is misspecified (`r1/theory/simulate_t4.py:516`), so neither rule is Bayes for A2.
- Empirically, table < known in all 48 shared and record cells of S8, so the ordering holds here.
- **Fix:** reword lines 283–286 and 351. Say the two rules give an empirical bracket (table < known in every cell), that `known` uses strictly more information per decision than any history-based rule, and that neither is campaign-optimal.

**m3. The note says its "conservative" result is what R1-THEORY-RHO (2) states; (2) is conditional, the evidence is aggregate** (`docs/r1/theory/T5_SHARED_NOISE_20261122.md:303-309`).
- R1-THEORY-RHO (2) claims conservativeness only under conditions, including μ_n ≤ 0, E[e | F_n] ≥ 0 and Var(e | F_n) ≤ σ². For μ_n > 0 it says the direction is not determined.
- The re-run shows a lower mean executed threshold and more keeps under `known`. These are averages over type mixes that include μ > 0 types.
- So the result is *consistent with* (2) in these models. It does not test the conditional statement per proposal.
- **Fix:** replace "as PLAN R1-THEORY-RHO (2) states" with "consistent with R1-THEORY-RHO (2): on average over the mix, …".

### NOTE

**n1. The kernel-free check is correct but can only test the code** (`r1/theory/simulate_t4.py:553-575`; the note, line 132 says so).
- Under `record` and `shared`, e′ − e = (w_c − w_inc) = Δ̂ − Δ. A keep means Δ̂ > t, so e′ > e − Δ + t on every keep. Zero violations are guaranteed whenever the bookkeeping is consistent.
- In the `iid` branch, `e_n` is *defined* from that identity (`simulate_t4.py:558`), so that branch cannot fail even with a bug elsewhere.
- The note is candid about this. It is acceptable as a consistency check, not as evidence.
- The two sub-claims are right:
  - e′ > e − Δ for t ≥ 0, and e′ > e at a null keep with t ≥ 0;
  - with t < 0, many keeps have e′ ≤ e − Δ (81,903 to 95,633 per model).

**n2. The paraphrase of R1-THEORY-RHO (1) on main has no t ≥ 0 condition** (`origin/main:docs/r1/PLAN.md:1467`).
- The paraphrase reads "on every keep … the new record error exceeds the old one minus the true increment; for a null proposal it rises on every keep".
- The note's last kfree column (lines 122–137) shows this holds only for t ≥ 0, for example under the default rule. With the oracle-threshold policy's negative t it fails on 23–32 % of those keeps (81,903 of 359,543 in iid, 94,782 of 296,621 at the target).
- This is outside the unit and is not a defect of it. The manuscript text should keep the t ≥ 0 (or default-rule) condition.

**n3. The branch-study equivalence is argued, not simulated** (`r1/theory/t5_shared_report.py:189-211`; the note, lines 233 and 358).
- I checked the algebra. `branch_study` derives the per-run sd as σ_d/√(2(1 − r_w)). With r_w = (ϱ − s)/(1 − s), that equals σ√(1 − s), the sd of w.
- The structural kind then gets r_w = 0, with the same per-run sd. This is consistent with the main simulator, where the structural paired sd falls.
- The remaining assumption is that u is common to both branches of an instance. That holds if the study's branches share the campaign's seeds. The note states it as a limitation, which is enough.

**n4. Provenance.**
- `manifest.json` records `git_head_at_write = 52f4e3e5`, the merge base. The code was uncommitted when the parts were written (the note, line 15, says the manifest was rewritten after the last code change).
- The source hashes in the manifest match the committed files, and my re-run from the committed code reproduces the committed parts (item 4 above). Provenance is therefore adequate.
- Optional: one sentence in the note recording this would help.

**n5. The error model is stated precisely and matches the code.**
- `u` is drawn once per campaign from a separate generator (`simulate_t4.py:418`).
- `w` is scaled by √(1 − s) and evolves per component with r_w (`:530-535`). `u` cancels in Δ̂.
- The policies get `effective_rho = max(ϱ, s)` and the matching paired sd.
- s = 0 reproduces `record` bit for bit (test).
- The `known` threshold, −(1 − r)x + t*(μ, τ, s_f) with s_f = σ√(1 − s)√(1 − r²), is the correct conditional law of Δ̂ given x.
- `iid` and `record` output is unchanged: `reproduction.json` regenerates identically, and the 14 existing tests pass.

**n6. Grid edges and status line.**
- The note already discloses that two tuning grids bind (lines 197, 229 and 346–350).
- The status line "nobody has reviewed them" (line 3) will need updating after this review.

## Answers to the six checks

1. **Error model stated precisely and matches the code:** yes (n5).
2. **Kernel-free check correct:** yes, in both math and code. By construction it is an identity of the decision rule (n1).
3. **Numbers reproducible:** yes. The tables regenerate byte-identically, six parts re-run to floating-point precision, and about 25 derived figures in the note agree with `tables.md`.
4. **PLAN conclusions follow at the stated scope:**
   - R1-THEORY-RHO (4) is satisfied: the re-run was done, ENGINEERING_ONLY.
   - R1-D3-CHOICES (1) cites the oracle-prior numbers as A2's, for one cell only (m1). Its qualitative content follows.
5. **Tests:** the unit's 8 tests and the 14 existing T5 tests pass, on the branch and on the merged tree.
6. **Merge:** clean.

## Verdict: ACCEPT WITH MINOR
