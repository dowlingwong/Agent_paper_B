# Independent review: Paper C plan addendum of 19 Nov 2026 and PLAN §10 author rows

**AI-assisted (Claude, independent reviewer; did not write the amendment).** Reviewed commit `946d8120` on `paperc-plan-amend-20261119` (parent `cf045c39`, tip of `paperc-build-20261115`). Files under review: `paperC/docs/PLAN_ADDENDUM_20261119.md` (cited as "add."), `docs/r1/PLAN.md` lines 1195–1209 (the "19 November 2026 — Paper C (author)" section), and `paperC/README.md`. The decision memo the rows refer to ("Paper C 待定决策备忘录") is not in the repository. Faithfulness is therefore checked against the decision list in the review request.

**VERDICT: NOT ACCEPTED** (4 MAJOR, 12 MINOR)

Most of the amendment is accurate. Nearly every number attributed to a report checks out (see "Verified" at the end). Four points must be fixed first: (1) the consequences of the gate in A.2/A.4 cannot be carried out as written; (2) the restore-fidelity replay check does not define what the replay is compared with; (3) the PLAN row changes an adopted value (K) without saying so, and states T1's K = 6 as unconditional; (4) the English addendum adds a scope rule for R1-PAPERC-CORE that the author did not decide and that the Chinese row does not contain.

---

## MAJOR

### 1. "Round A" consequences in A.2 and A.4 cannot be carried out, and the E2 stakes source is inconsistent
- **Where:** add. lines 45, 49, 66; PLAN lines 1202, 1204.
- **Problem:**
  - (a) Plan §3.3 (plan lines 107–112) defines round A as the round where only **E1** is controlled and E2 is frozen, and calls it descriptive (also §17 P2). So line 45 ("An epoch that fails is not run in round A on that node; the other epoch may still run") has no meaning for E2, which is never run in round A. Line 66 ("descriptive only in round A") is vacuous, because round A is already descriptive. The SPT-2 pre-declaration needs to know what actually happens when E2 fails the gate, or when a node misses the stakes floor: no collection or forks at that epoch? Excluded from the Q1/Q3 confirmatory families? The text does not say. After the reframe (R1-PAPERC-REFRAME, "round B′"), "A" also collides with "option A".
  - (b) Line 49 says the stakes floor "needs census measurement (a)". Line 66 says the node rule uses measurement (b). Neither says which data feed the pre-SPT-2 gate: (a)/(b), which use sweep-1's 7B proposer and logs, or SPT-1, which uses the pick.
  - (c) Line 44's E2 stakes condition is "median kept increment ≥ 0.5 σ_d **or** decision regret ≥ 0.1 σ_d". Line 66's node rule has only the kept-increment criterion. A node that passes on regret alone passes A.2 but is "descriptive only" under A.4.
- **Fix:** Replace "round A" with explicit consequences, confirmed by the author. For example: "an epoch that fails is not controlled in SPT-2/SPT-3 on that node (its actions follow the frozen tier rule, no forks at that epoch) and enters no confirmatory comparison there", and "a node below the stakes floor gets no confirmatory Q1/Q3 test". State which measurement supplies each number: for example, (b) with (a)'s audit procedure for the node choice, and SPT-1 for the pre-SPT-2 gate. Either align A.4 with A.2's "or regret" clause or state that the difference is deliberate. Make the same change in rows 1202 and 1204.

### 2. The restore-fidelity replay check (§B) leaves its reference trajectory and failure path undefined
- **Where:** add. lines 91–93; PLAN line 1206.
- **Problem:**
  - Line 91 re-runs "the logged action … under the logged continuation policy" and compares the result "with the live run". The continuation policies are N1/N0 (A.1). The live root continued under its behaviour component (an SPT-2 mixture member). These are different policies, so if "live run" means the root, the comparison fails by construction. If it means a previously executed fork leaf, "live" is the wrong word, and that check does not test what Pakhomov and Nijkamp tested: their abstract compares restored continuations with the live continuation (24/24 agree only after the random-stream position is restored; checked).
  - Line 92 ("extends SPT-1's A/A identity check") points to the first reading, i.e. plan §4.2's A/A replay: "a fork that takes the root's action reproduces the root's ledger" (plan line 173). Under that reading the continuation must use the root's own policy and ε stream.
  - Also undefined:
    - what counts as a match: each step, or the whole continuation through termination;
    - that both arms of every fork must start from the same restored snapshot (no reuse of the live process for one arm);
    - when the check runs, given that SPT-1's go/no-go also uses fork data and line 93 only says it is "read with that in mind";
    - what happens if a node never reaches the threshold.
- **Fix:**
  - Define the check as an A/A replay at fork points: restore, take the root's logged action, continue under the root's behaviour component with its logged ε stream, and compare with the root's live continuation through termination.
  - Optionally add a separate leaf-replay check on recorded fork leaves.
  - Define a match as all steps identical: edit hash, action, keep decision, and metric within tolerance. Report the step where the replay first diverges.
  - Require both arms to start from the same restored snapshot.
  - Require the threshold, sample size and tolerance to be declared in B11's runbook before the check runs, and run the check in SPT-0/SPT-1 before SPT-1's go/no-go is read.
  - Below the threshold: STOP for the author, and that node's fork data are not used for τ̂², N6 or OPE. Whether SPT-1's go/no-go on such a node becomes "not assessed" would be a new rule, so it needs the author.

### 3. K: the change from the adopted memo is undisclosed, and T1's K = 6 is conditional
- **Where:** add. line 56; PLAN lines 1197, 1203.
- **Problem:** The correction itself is right for T0. R1-BX-PROPOSED-CONFIRM (PLAN line 780) says: "K = 6 for T1 audits only; T0 stays at K = 10". Paper C's E-T0 nodes are T0 CPU nodes, so the memo's "K = 6 as in Paper B" was wrong for them. Two problems remain:
  - (a) Line 1197 says the author adopted **all** memo recommendations, but row 1203 records a value the memo did not contain, without saying so. A PLAN row is an author record.
  - (b) R1-BX-D3 (PLAN line 747) is conditional: "Until the check has passed and its result is recorded in a PLAN row, K = 10 applies everywhere". No such row exists on `origin/main` (checked 19 Nov; sweep-1 B.2 has just passed, so the check can now run). "K = 6 on T1" therefore states a conditional value as settled. A smaller point: plan §12 costs E-INT with K = 5 (plan line 446).
- **Fix:** In A.3 and row 1203, add: "K = 6 on T1 only after R1-BX-D3's subsampling check has passed and been recorded; until then K = 10". Add a disclosure to row 1203 (or the preamble at line 1197), for example: "备忘录写'K = 6，同 Paper B'；Paper B 的规则是 T0 K = 10（R1-BX-PROPOSED-CONFIRM），记录时据此更正，待作者确认." Note that the E-INT cost in plan §12 has to be recomputed.

### 4. A.4 adds a core-scope rule that was not decided
- **Where:** add. line 70, second sentence ("If neither node meets the stakes floor, Paper C's core is E-SYN plus descriptive E-T0, and the contribution is the map …").
- **Problem:** The author decided that R1-PAPERC-CORE is written **after** measurements (a) and (b) (R-C3). This sentence decides the core in one branch in advance, and the census itself lists other options (an OpenML node; the GPU tier, census §6.4). It does not follow necessarily from the decisions, and row 1204 does not contain it. As a result the English addendum, which "controls" the plan, says more than the author row.
- **Fix:** Delete the sentence, or reword it as an open question for R1-PAPERC-CORE ("if neither node meets the stakes floor, R1-PAPERC-CORE decides between …"). Keep English and Chinese in step.

---

## MINOR

### 5. Go/no-go: state the multiplicity, the count of statistic 2 and the sensitivity rule
- **Where:** add. lines 25–28, 38; PLAN line 1201.
- **Problem:**
  - As written, the rule passes if any of up to **6** checks passes: 2 nodes × (statistic 1 in E1 and in E2 + one statistic 2). It is 8 if statistic 2 is also split by epoch, which the text leaves open. There is no multiplicity adjustment.
  - Each check is conservative (magnitude floor plus lower bound; on E-SYN the null rate of lower bound > 0 is 0.020–0.025 per epoch, and N6 is 0/200). The union is lenient, but line 38 calls the whole rule "the intended conservatism".
  - This is acceptable, because the gate only decides whether RL is trained, and Q3's confirmatory test runs on fresh blocks at its own α. The text should say so.
  - Also open:
    - if only one node passes, is Q3 tested on both nodes (Holm over 2) or only on the passing node?
    - "floors of 0.25 δ_n" (line 28): does only statistic 1's floor drop to 0.25 δ_n, or both floors?
    - plan §9.1 gate 1 (plan line 330) still uses "τ̂² above its floor".
- **Fix:** Add one sentence on the union rule and why it does not affect Q3's error rate. Say that a passed go/no-go is not reported as evidence of headroom. Say whether statistic 2 is pooled over epochs or computed per epoch. State Q3's node scope after a one-node pass and the exact sensitivity floors. Add: "plan §9.1 gate 1 reads τ̂² as A.1's per-epoch τ̂²_d".

### 6. The rationale for the statistic-2 floor is a heuristic, and the repository's own theory note says so
- **Where:** add. line 36.
- **Problem:** "If the sum of all one-step improvements stays below δ_n, an RL policy is unlikely to gain δ_n" is not established. The theory working note (`origin/codex/paperc-theory-20261117`, `THEORY_WORKING_NOTE_20261117.md` line 58) finds that one exact rollout update captures 59.34 % of the static-to-optimal gap in `budget`. There the optimum gains about 1.7× the one-step improvement.
- **Fix:** Label it a heuristic and cite T-C3 as unproven, or drop "unlikely".

### 7. SPT-1's size and set-up do not match the plan's cost row and the E-SYN evidence
- **Where:** add. lines 24, 34, 38.
- **Problem:**
  - r = 2 under N1 and N0 means 4 continuations per arm. τ̂² needs R ≥ 2 per policy (`forks.py` docstring). Plan §12's SPT-1 row (plan line 429: "60 forks × 2 arms × 20", 8.4k calls) assumes one continuation per arm. With four, the fork part is 9.6k calls and the total about 15.6k.
  - The E-SYN detection rates behind the "expected consequence" come from about 280–410 forks over 40 roots. SPT-1 plans 60 forks per node, split across two epochs.
  - N1 must already be tuned to serve as a continuation policy at SPT-1. The text does not say on what data, or that those data are disjoint from the go/no-go forks.
  - It does not say whether SPT-3 uses the same continuation policies.
- **Fix:** State SPT-1's fork count and recompute its cost row. Qualify line 38 ("at 60 forks the detection rates of FORK_VALIDATION §C, measured at ≈ 280–410 forks, are optimistic"). Say where N1 is tuned before SPT-1. State that N1/N0 with r = 2 also apply to SPT-3, or say otherwise.

### 8. Precision of three report citations
- **Where:** add. lines 34, 49.
- **Problem:**
  - (a) "Bootstrap intervals are narrow (… 0.70–1.20), hence the lower-bound condition". The report says intervals are "too narrow by up to 30 %" (FORK_VALIDATION line 134), and the range includes ratios above 1. An interval that is too narrow makes a lower-bound-only rule anti-conservative, so the reasoning points to the magnitude floor, not to the lower bound. (Per-epoch `d` ratios, which I checked in the JSON, also lie within 0.77–1.16.)
  - (b) "N6's lower bound never exceeded 0" refers to the **per-decision** refit interval (`forks_validation.py` `ci_above_0`; BUILD_STATUS P6 says "per-decision"). Statistic 2 is the per-campaign value, whose positivity was not tabulated.
  - (c) "E2 near-margin shares of 58–83 % but median kept increments of only 0.08–0.18 σ_d" mixes node sets. 58–83 % includes climate (83 %); 0.08–0.18 excludes climate (0.88 σ_d) (census §5, §4.1). Without climate the shares are 58–80 %.
- **Fix:**
  - (a) "intervals can be up to 30 % too narrow (bootstrap s.e./sd 0.70–1.20), so a lower bound alone is not relied on; hence the magnitude floor";
  - (b) "the per-decision primary lower bound";
  - (c) "on the OpenML nodes other than climate, 58–80 % … 0.08–0.18 σ_d".

### 9. Undefined quantities that the SPT-2 pre-declaration needs
- **Where:** add. lines 42–44, 67, 74; PLAN lines 1202, 1205.
- **Problem:**
  - **h**, the E2 threshold, is not defined. RELEVANCE_ESYN used N1's own tuned h. P7's clusters used m̂ > 0, so "the structure P7 validated" (line 74) holds only if h = 0. A tuned h would not be available when the clusters are fixed in SPT-0.
  - **σ_node vs σ_d:** the gate mixes the two units without defining them. On tabular, σ_d = 1.87 σ_node (census §1).
  - **"Decision regret"** is not defined (census: C1's `decision_regret`).
  - **"Declared real run price" g:** the text does not say who declares it, when, or in what unit.
  - **"V\*" in 0.3 ≤ price/V\* ≤ 3** is not defined (median over eligible decisions under the deployed forecaster, as in census §3.1?).
- **Fix:** Add a short definitions paragraph covering all five, each with its source and the time it is frozen (before SPT-1 or SPT-2).

### 10. The OPE clusters (A.5) do not fit the likely core
- **Where:** add. lines 74, 80; PLAN line 1205.
- **Problem:**
  - (a) The 8 clusters assume that both epochs are controlled. On E-T0, V\* − g was 2.6–4.1 σ_node, so the E1 "V\* < g" clusters would be empty and fail the 30-per-action target automatically. A.4 also makes E1 conditional.
  - (b) The worst-case figure of 4,800 decisions assumes equal cluster sizes. The smallest cluster governs, so unequal sizes need more.
  - (c) A.4's core channels include verify and re-audit (B17), but neither A.1 (epochs E1/E2) nor A.5 (clusters) covers those actions.
- **Fix:**
  - "8 clusters when both epochs are controlled; 4 (E2 only) otherwise"; say how empty clusters are treated.
  - "assuming roughly equal cluster occupancy".
  - Note that fork/OPE coverage of verify, re-audit and final selection is decided in R1-PAPERC-CORE.

### 11. Equivalence design details (A.3)
- **Where:** add. lines 55–56; PLAN line 1203.
- **Problem:**
  - The method for E-T0 power is not stated. R1-PAPERC-DELTA requires whole-pipeline simulation; line 59's closed form (n ≈ 10.5 (σ_D/δ)², which checks: (1.960 + 1.282)² = 10.51; 672 pairs at δ/σ_D = 0.125) is for planning only.
  - Regression adjustment on y_start: within a pair, y_start is the same for both arms (same instance, start configuration and audit seeds), so it can reduce the variance of D_i only through effect heterogeneity. The estimator is not specified.
  - Plan §10 says the pairing gain from common random numbers is measured, not assumed.
- **Fix:** "E-T0 power by the whole-pipeline simulation of R1-PAPERC-DELTA". Specify the adjusted estimator (for example OLS of D_i on centred y_start, with the intercept as the estimand) and include it in the power simulation. Add "the pairing gain is measured (plan §10)".

### 12. Estimand (§C): parse failures and informative truncation
- **Where:** add. line 98; PLAN line 1207.
- **Problem:** The termination/censoring statement and the Pardo et al. reading are correct. However, the list of truncation causes keeps "parse failure beyond retry", while Paper B now records cut-off or unparseable replies as invalid trials charged to the call budget, with the campaign continuing (R1-EXAM-B1-TRUNCATION-INVALID, exam code). Under §C's estimand, such a charged failure is an in-episode outcome. Dropping whole pairs is unbiased only if truncation does not depend on arm or outcome. The per-arm STOP and the per-cluster rates are diagnostics, not a guarantee.
- **Fix:** B11's runbook states how the pinned harness handles parse failures. If they are charged invalid trials, they are outcomes, not truncation. Add one sentence on the assumption that truncation is non-informative.

### 13. Measurement (a): Paper C seed block vs sharing with B.2, and the proposer for (b)
- **Where:** add. lines 63–65; PLAN line 1204.
- **Problem:** "On a Paper C seed block" and "shared with Paper B's B.2 where they coincide" pull in opposite directions. B.2 audits use 7001–7010, and R1-SWEEP1-CLASSIFY says 7006–7010 are "never used for training or selection of any evidence", which covers Paper C's node choice. The proposer for measurement (b) is not specified (pick or 7B), although the stakes depend on it.
- **Fix:** Either run (a) only on Paper C audit seeds, or reuse only B.2's label-seed (7001–7005) values and say so. Name the proposer for (b). Note that (a) and (b) are real-node runs, each with its own runbook (line 3 covers this in general).

### 14. The B11 pin is a forward reference, and PLAN cross-references do not resolve on this branch
- **Where:** add. line 125; PLAN line 1209.
- **Problem:** Sweep 2 has not launched. There is no `authorizations/c3_sweep2_*.md` on `origin/main`, and R1-SWEEP2-INTEGRATE (19 Nov noon) is still pre-launch. So the record that defines the pin does not exist yet. R1-SWEEP2-AUTH exists only on `origin/main`: on this branch, PLAN.md mentions it only inside the new row. In the other direction, `origin/main`'s PLAN.md has no R1-PAPERC-* rows (0 matches), so the 15 Nov and 19 Nov Paper C sections exist only on the paperc line.
- **Fix:** Add "(sweep 2 not launched as of 19 Nov; B11's runbook waits for its launch record)". Before merging, rebase the Paper C rows onto `origin/main` §10 in date order so that R1-SWEEP2-AUTH resolves.

### 15. Smaller additions not on the decision list, and traceability
- **Where:** add. lines 98 (truncation rates per state cluster), 121, 126–127, 120; PLAN line 1197.
- **Problem:**
  - Reporting truncation rates per state cluster is in both languages; it is harmless but not on the decision list.
  - The "Also outside Paper C" list (line 121) is English-only. Its "a staleness channel" can be read against E.1's "re-auditing the incumbent tests whether stored experience is still valid".
  - The theory-note process rule (line 127) is English-only.
  - "The separate later paper" (line 120) is not named anywhere in the repository.
  - "A2" collides with A2-U and A2's soft labels.
  - The memo is not committed.
- **Fix:** Confirm these items with the author or mark them as the recorder's proposals. Give the later paper a working name or a pointer. Rename "A2" (for example, "the memory-reset branch"). Commit the memo, for example under `paperC/docs/inputs/`, or cite where it lives.

### 16. Clarity and README
- **Where:** add. lines 46, 59, 76, 82; `paperC/README.md` lines 3, 73.
- **Problem:**
  - "P5/P6/P7/P9/P10" are overloaded: runbook phases, plan §17 decisions P1–P9, and addendum 15 Nov open item P10. Line 46's "P5 keeps the two apart" is ambiguous.
  - The README status line is still "Status (15 Nov 2026) … not adopted by PLAN rows".
  - The README Extension line still lists "verify and stop actions", although verify and re-audit are core channels (R1-PAPERC-REFRAME; add. line 67).
- **Fix:** Write "runbook phase P5" and so on throughout. Update the README status line to 19 Nov. Move verify and re-audit out of the Extension line (stop stays there).

---

## Verified (no change needed)
- **FORK_VALIDATION:**
  - τ²_q strict_null 21.809 and channel worlds 23.416–1200.971 (× 10⁻⁶);
  - τ²_d in shared_error: E1 −0.012, E2 2.290;
  - τ_d/σ: interaction 0.489, keep_feedback 0.783;
  - null coverage of `d` 0.930–0.940;
  - N6 lower bound > 0 in 0/40 (0/200 null).
- **Track S STOP 4:** V\* − g was 2.58–4.06 σ_node (rounded to 2.6–4.1).
- **POWER_VALIDATION:** 0/12 TOST rejections at 512 pairs per test block, interval [0.00, 0.26].
- **LEARNER_VALIDATION:** N6 88.6 % [79.2, 98.0]; N6 against the short-horizon static rule spans 0; R0 and R1 lie entirely below 0.
- **OPE_VALIDATION:** "insufficient data" for N0, with 124 zero-propensity held-out rows; the cluster structure is as described except for h (finding 9).
- **TOST planning coefficient:** 10.51, 672 pairs at δ/σ_D = 0.125.
- **Support arithmetic:** 30 / 0.05 × 8 = 4,800; 4,800 / 20 = 240 and 4,800 / 14 ≈ 343.
- **K:** T0 K = 10 per R1-BX-PROPOSED-CONFIRM, so the memo's K = 6 was wrong for E-T0.
- **N1/N0 and bookkeeping:** the claim matches `forks.py`.
- **PLAN §11** names restore audits.
- **Related work:**
  - arXiv:2611.05650 (Pakhomov and Nijkamp) says what §B says;
  - Counterfactual Rollout Replay (arXiv:2609.33875) and Calibration Is Not Control (arXiv:2606.21399) exist with matching topics;
  - TRACE exists (arXiv:2606.11119); its EMNLP anthology id was not checked.
- **Language and README:** the English addendum and the Chinese rows agree, except for findings 4 and 15. The README decisions table and layout entries are consistent with the rows.
