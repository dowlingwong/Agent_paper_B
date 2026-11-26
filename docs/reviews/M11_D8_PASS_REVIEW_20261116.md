Reviewed base: d8188b86e3f1cc98393ff9223de7230e67e85e3f

# D8-PASS unit and R1-BX-D8-V3-B draft — independent review record (16 November 2026)

Branch `mac-d8-pass-20261116` from `e9f00371`. Unit:
- declaration `a30d458f` (before script and run);
- script `4f782ad7`;
- outputs, report and the V3-B draft.

One freshly spawned independent reviewer agent (AI-assisted, Claude), two rounds. The reviewer's exact rerun matched the committed output, and its independent re-implementation of all five tests disagreed in 0 of 1,336 decisions.
- **Round 1 (`b8dbb467`): ACCEPT,** with 11 MINOR findings. These were wording, labelling and disclosure fixes. They include a post hoc reviewer diagnostic of the +∞ screen on heterogeneous μ and on T1 × 6.
- **Round 2 (`d8188b86`, all fixed): ACCEPT.** Two optional nits are left as is:
  - "0.66–0.91 of reps" means of reps that did not STOP;
  - "more than 2.5 %" should read "at least 2.5 %" (50 or more of 2,000 resamples).

The declared outcome: item 4 is (b2), and item 5 is the floor T0 ≥ 9, T1 ≥ 3.

Accepted commit (last round): d8188b86e3f1cc98393ff9223de7230e67e85e3f

The round texts are reproduced unchanged below.

---

# Independent review: D8-PASS unit and R1-BX-D8-V3-B draft (round 1)

Reviewed base: `mac-d8-pass-20261116` @ `b8dbb467af081aa95f7596cc814fdf30e2999491` (from `e9f00371`).
Authority: R1-BX-D8-V3-A in `gh/author-decisions-20261116` @ `4da73306`. Reviewer scratch: `/tmp/pb/rev_d8pass/`
(`chk.py`, `chk2.py`, `repro.py`, `diag.py`). No worktree file was written; no state-changing git command was run.

VERDICT: ACCEPT

No BLOCKING or MAJOR finding. The declared rule was applied exactly; the code reproduces bit for bit and agrees with
an independent re-implementation of all five tests; the outcome ((b2), floor T0 ≥ 9, T1 ≥ 3) follows from the
declaration. The MINOR items below are wording, labelling and disclosure fixes. They do not change the declared
outcome, and they can be fixed before the draft goes to the author.

## Findings

1. **MINOR: report §1 table, (c″SR) exceedance count.** The table says "no (16)" for T1 × 12. The JSON has 8 per-arm
   exceedances on T1 × 12 (and 8 on T1 × 6). 16 is the per-arm list plus the two-arm flags. Fix: "no (8)".

2. **MINOR: report header, output hashes swapped.** The report gives `sim_output.json` sha256 `743800cb…` and
   `sim_output.md` `85b7def3…`. Actual: `sim_output.json` = `85b7def3…`, `sim_output.md` = `743800cb…`. The script
   hash `6372d8eb…` is correct and equals the blob at `4f782ad7`. Fix: swap the two.

3. **MINOR: report §2.1 and V3-B "Why it is calibrated": scope of the D8-SKEW §3.3 citation.** D8-SKEW §3.3 covers
   homogeneous μ, T1 × 12, P2 and P3 only (its own Limits say so). The report extends it to "the settings here" as "the
   same in kind", and the draft says "D8-SKEW §3.3 showed that this screen ... carries the calibration under left
   skew", while the row claims calibration on T1 × 6 and under heterogeneous μ. The claim is still true. A post hoc
   reviewer diagnostic (`diag.py`, 300 reps, new seeds, PoI kept, arm 1) on the uncovered settings gives:

   | left-skewed, g = 0 | share of read reps the screen fails | (b2) per arm | drop-bad variant per arm |
   |---|---|---|---|
   | hom T1 × 6, μ = 1 / 2 | 0.91 / 0.67 | 0.000 / 0.023 | 0.060 / 0.067 |
   | het T1 × 12, μ = 1 / 2 | 0.90 / 0.66 | 0.010 / 0.013 | 0.070 / 0.040 |
   | het T1 × 6, μ = 1 / 2 | 0.91 / 0.71 | 0.000 / 0.007 | 0.057 / 0.063 |

   The hom T1 × 12 control matches D8-SKEW §3.3 (0.94 / 0.65; drop-bad 0.053 / 0.073). Normal noise at g = 0.3: het
   T1 × 12, μ = 1, screen 0.78, power per arm 0.083 against 0.52 for drop-bad. Fix: say that §3.3 covered
   hom / T1 × 12. Then either state that the extension to het and T1 × 6 is an inference, or cite this review's
   diagnostic as a post hoc check (not a rule).

4. **MINOR: V3-B row, how item 4 relates to V3-A item (1).** V3-A (1) sets a bad resampled node's gap closed to −∞
   before the IQM. Item 4 adds a separate pivot convention: any such resample gets t\* = +∞. That convention is not a
   consequence of (1). With the IQM's zero weight on the lowest quarter, (1) alone would usually trim the −∞ node, or
   would give t\* = −∞, which is anti-conservative for the upper quantile. The simulated (b2) applies both, and the
   row's wording is explicit, so it is not contradictory. Still, the S2-M4 CONFIRM draft (path B, "Coupled items")
   notes that under (b2) item (1)'s bootstrap clause has no further effect, and V3-B does not say this. Fix: add one
   clause to item 4: "this convention applies on top of item (1); under it item (1)'s resample clause has no further
   effect on the bound."

5. **MINOR: V3-B row, Holm level wording.** "Lower bound (97.5 %) ... Holm over the two arms unchanged" can be read
   as fixing 97.5 % for both arms, while R1-BX-D8 sets 97.5 % for the first-ranked arm and 95 % for the second. Under
   the +∞ convention a 95 % bound fails whenever ≥ 5 % of resamples are bad, which was not simulated. It matters only
   for the second arm's verdict, not for the gate's pass. Fix: "(97.5 % for the first-ranked arm and 95 % for the
   second, as in R1-BX-D8's Holm)", and note that only the 97.5 % step was simulated.

6. **MINOR: V3-B row, the normative specification of (b2).** The row abbreviates the method. Gate v3 needs exact
   details that the row leaves out: the per-node delta-method se formula; the se\* recomputed in each resample with
   that resample's own IQM order; the gb = 0 placeholder (overridden); the linear quantile; and 2,000 resamples. Fix:
   add "exactly as declared in `M11_D8_SKEW_DECLARATION_20261115.md` §2 (b2) and implemented in
   `r1/scripts/d8_skew_sim.py` @ `dc899aad`", so the gate-v3 review has a fixed reference.

7. **MINOR: V3-B item 5 bracket, PoI treatment and simulation coverage.** The option "not IQM-eligible and is
   reported" does not say whether such a node stays in the PoI. R1-BX-D8 keeps δ_n-excluded nodes in the PoI. Also,
   the simulation covers neither option, because every simulated node is at or above the floor. Fix: write the option
   as "[excluded from the IQM, kept in the PoI and reported | a STOP]" (or add a third option if intended), and add
   one sentence saying the floor was simulated only with every T1 node exactly at 3 (T1 × 6) or 6 (T1 × 12) test
   instances.

8. **MINOR: PoI dependence of (b2) under symmetric noise is not disclosed.** (b2)'s primary bound alone reaches 0.040
   per arm (normal, hom, T1 × 12, μ = 2; the full rule gives 0.0175). That is within MC error. Still, under symmetric
   noise part of the calibration comes from the PoI conjunct, which D8-SKEW §3.2 showed gives no protection under
   skew. The (c′) and (c″J) primary bounds also reach 0.0375–0.040 under t3. Fix: in "What the author should know",
   add "under symmetric noise the PoI conjunct also contributes (primary-only max 0.040 per arm)".

9. **MINOR: report §2.2 / V3-B, the (c″J) near-miss.** The statement is accurate: 3 of 24 exceed, at
   0.0375–0.0425, all under one MC SE (0.009) above 0.035. For balance, add the pooled figure. Over the 6 left-skew
   T1 × 12 scenarios with μ ≥ 1, (c″J)'s per-arm rate is 0.035 (SE 0.004): its true rate under this skew is about the
   threshold, not clearly below it. On T1 × 6 it is 0.028.

10. **MINOR: report §1, "STOP rate at g = 0 (V1n)" label.** The numbers are P(no eligible) + P(test STOP). For
    example, at T1 × 12, μ = 0.5 the 0.28 is 0.11 no-eligible plus 0.165 test STOP. Fix: label it "STOP or no
    eligible node".

11. **MINOR: floor and power.** The report proposes T1 ≥ 3 without giving (b2)'s power at that size. Mean two-arm
    power at μ ≥ 1 is 0.26 on T1 × 6, against 0.36 on T1 × 12. Fix: one line in report §3 / the V3-B "The floor"
    bullet.

## What was verified

**Pre-registration.**
- Commit order: `a30d458f` (declaration, 10:36:35) → `4f782ad7` (script, 10:38:00) → `b8dbb467` (outputs, report,
  draft, 10:52:00). Author and committer dates agree. The outputs' mtimes (10:48:15) fit the stated 10-minute run.
- The declaration is unchanged after `a30d458f`. The script is unchanged after `4f782ad7`.
- The declaration matches the request: candidates (b2), (c), (c′), (c″) as J and SR; per-arm ≤ 0.035; T1 × 12
  primary and T1 × 6 secondary; ≥ 400 reps; power at gap 0.3; P3 floor; draft row; fallback (c). It also matches
  V3-A's wording.
- `evaluate()` implements §4 exactly:
  - primary calibration on all 24 T1 × 12 g = 0 rows, per-arm full rule;
  - secondary on T1 × 6;
  - "both layouts" group first;
  - power metric: mean two-arm pass rate, T1 × 12, g = 0.3, μ ≥ 1 (18 rows);
  - tie within 0.02 broken by the lower T1 × 12 max per-arm rate;
  - floor rule;
  - (c) fallback;
  - two-arm flag > 0.065.
- The outcome is `calibrated = calibrated_both_layouts = tie_set = ["b2"]`, floor `{T0: 9, T1: 3}`. The
  `sim_output.md` evaluation block equals the JSON's.

**Implementation.**
- The generator body (lines 124–137) is identical to `d8_skew_sim.one_rep` lines 73–86. The helpers are imported.
  `node_se` is identical apart from indentation. (b2) is line-for-line D8-SKEW's (NEG for bad nodes in G\*; t\* = BIG
  for any bad / zero se\* / non-finite; linear 0.975 quantile; θ̂ − q·ŝe). (c) is identical.
- V1n STOP is on the point eligible-node denominator, for all rules. STOP and no-eligible count as fails.
- The PoI conjunct is computed per arm over all nodes, as in D8-SKEW. Two-arm = either arm.
- (c′): se\* uses ddof = 1 and the fixed n_j; se\* = 0 or non-finite → +∞; θ̂ − q₀.₉₇₅(t\*)·ŝe. Correct for a lower
  bound.
- (c″J): the unbiased k₃ = n Σ(x − x̄)³ / ((n − 1)(n − 2)) and κ₃ = Σ k₃_j / (k³ n_j²) are correct for the
  node-equal mean. γ = κ₃/se³ and t_J = T + γ/6 + γT²/3 is Johnson (1978) rewritten in terms of the mean's skewness.
  The sign is right: left skew lowers t_J. The df is (c)'s Welch–Satterthwaite.
- (c″SR): W_j = Σ sign·rank|a| with Var n(n + 1)(2n + 1)/6 is correct for this W. The van Elteren weights are
  1/(n_j + 1). Ties have probability 0 with continuous data; `rankdata` averages them.
- **Exact reproduction** (`repro.py`): seed 20261118 + 2 (left-skewed, hom), T1 × 12, the first three scenarios
  (μ 0.5 g 0, μ 0.5 g 0.3, μ 1 g 0) at 400 reps. All five rules' per-arm and two-arm rates equal the JSON exactly.
  This includes (c″J)'s 0.0375 exceedance.
- **Independent re-implementation** of (b2), (c), (c′), (c″J) (via `scipy.stats.kstat`) and (c″SR) (via W⁺), written
  from the declaration text. Applied to the same reps, it gave 0 decision mismatches in 1,336 arm-reads.

**Report and draft against the JSON.**
- Every number checked matches the JSON (rounded), apart from findings 1, 2 and 10:
  - max per-arm and two-arm rates per rule and layout;
  - exceedance counts for (c), (c′) and (c″J);
  - the per-condition table;
  - the normal-hom power series;
  - the 0.05 against 0.685–0.69 at μ = 1;
  - (b2)'s left-skew power of 0.16–0.19;
  - (c″J)'s exceedances and power;
  - "all exceedances under left skew" (symmetric-noise max ≤ 0.0225 for every rule on both layouts).
- MC SE: 0.009 at 0.035 and 0.025 at 0.5 are correct.
- The V3-B draft:
  - matches the declared outcome;
  - states correctly that (b2) keeps R1-BX-D8's primary criterion and that (c″J) would amend R1-BX-D8,
    R1-BX-PROPOSED-CONFIRM (D8) and the `analysis_guard` row pattern;
  - labels (c″J) clearly as post hoc and outside the declared rule, needing a confirming unit declared first;
  - says the (c) default does not apply.
  - Its only bracket (item 5's below-floor handling) offers options and does not decide.
  - It contains no `| R1-BX-D8-CONFIRM |` row. Its first cell is `R1-BX-D8-V3-B`, which
    `analysis_guard._confirmation_commit` skips, and it lives in `proposals/`, not in PLAN.md.

---

# Independent review: D8-PASS unit and R1-BX-D8-V3-B draft (round 2)

Reviewed base: `mac-d8-pass-20261116` @ `d8188b86e3f1cc98393ff9223de7230e67e85e3f`, one commit on `b8dbb467`
(round 1, `REVIEW_R1.md`). Checked with `git diff b8dbb467 HEAD`. No worktree file was written; no state-changing git
command was run.

VERDICT: ACCEPT

## Scope of the change

- Only two files changed:
  - `docs/r1/reports/M11_D8_PASS_20261116.md`;
  - `docs/r1/proposals/R1_BX_D8_V3_B_DRAFT_20261116.md`.
- The declaration, the script and the committed outputs are unchanged. The round-1 verification of the
  pre-registration, the implementation, the exact reproduction and the independent re-implementation still stands.

## Round-1 findings

1. **(c″SR) count: fixed.** "no (8)" on T1 × 12, which matches the JSON.
2. **Hashes: fixed.** `sim_output.json` is now `85b7def3…` and `sim_output.md` is `743800cb…`. Both match
   `sha256sum`.
3. **§3.3 scope: fixed.**
   - The report and the draft now say that D8-SKEW §3.3 covered homogeneous μ on T1 × 12 only.
   - Both cite the reviewer's check as post hoc. The report adds "not a rule; 300 reps, fresh seeds".
   - The figures cited are 0.66–0.91 for the screen and 0.040–0.070 per arm with bad resamples dropped. They match
     the reviewer's diagnostic for the three uncovered settings (hom T1 × 6, het T1 × 12, het T1 × 6).
4. **Item 4 on top of item (1): fixed.** The row now says: "This convention applies on top of item (1); under it,
   item (1)'s resample clause has no further effect on the bound."
5. **Holm levels: fixed.** The row now reads "97.5 % for the first-ranked arm and 95 % for the second, as in
   R1-BX-D8's Holm step-down; only the 97.5 % step was simulated".
6. **Exact reference: fixed.** The row cites `M11_D8_SKEW_DECLARATION_20261115.md` §2 (b2) and
   `r1/scripts/d8_skew_sim.py` @ `dc899aad` (2,000 resamples, linear quantile).
7. **Floor bracket: fixed.**
   - The bracket now reads "[excluded from the IQM, kept in the PoI and reported | a STOP] (no node below the floor
     was simulated)".
   - Report §3 adds that every simulated T1 node was exactly at 3 or 6 test instances.
   - The bracket still offers options and does not choose for the author.
8. **PoI contribution: fixed.**
   - Disclosed in report §2.1 and in the draft: the primary bound alone gives 0.040 per arm (normal, hom, T1 × 12,
     μ = 2), against 0.018 for the full rule.
   - JSON: 0.04 and 0.0175.
9. **(c″J) pooled rate: fixed.**
   - Report: 0.035 (SE about 0.004) on T1 × 12 and 0.028 on T1 × 6. Both match the reviewer's computation.
   - The draft gives the T1 × 12 figure.
   - (c″J) is still labelled post hoc and outside the declared rule.
10. **STOP label: fixed.** The label is now "STOP or no eligible node", with the 0.11 + 0.165 breakdown.
11. **Power at the floor: fixed.** 0.26 on T1 × 6 against 0.36 on T1 × 12, in the report and the draft. The JSON
    gives 0.2582 and 0.3593.

## New issues

None at MINOR or above.

Two optional nits, not required:
- **"0.66–0.91 of reps".** These are shares of read reps (reps without a STOP or no eligible node).
- **"more than 2.5 %".** In report §2.1 the screen actually fails the arm at ≥ 50 of 2,000 resamples, that is
  "at least 2.5 %".

The row's first cell is still `R1-BX-D8-V3-B`, and the draft contains no `| R1-BX-D8-CONFIRM |` row. The declared
outcome is unchanged: (b2) for item 4, and T0 ≥ 9, T1 ≥ 3 for item 5. The (c) fallback correctly does not apply.
