Reviewed base: 5a317b14a2c994722776e03baac9d1ef1be6826b

# B2 power (precision) plan: rule, script, number and PLAN-row draft — independent review record (14 November 2026)

Branch `mac-b2-plan-20261114`: rule `b7a4fa40` (committed before any number), script and tests `73830064`, result and draft `a97c2f94`, draft rev 2 `5a317b14`. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude), who re-derived n_j = 4 / 3 / 3 and n = 4 independently from the raw manifests. Round 1 (`a97c2f94`): changes requested (the literal `b2_instances_per_node = 4` appeared twice in the decision cell; the row overstated the conservatism). Round 2 (`5a317b14`): **accepted**; the paste blocks pass the B2 gate functions (bare ID, literal once, dated author heading). Notes, not blocking: the gate code was uncommitted at review time (tested version sha256 `0a218f5f…`); gemma4_31b's own 3-dof upper limit would give n = 5 (disclosed in the draft body); a paste mistake makes the gate STOP without saying which.

Accepted commit (last round): 5a317b14a2c994722776e03baac9d1ef1be6826b

The round texts are reproduced unchanged below.

---

# Independent review: B2 power plan (branch mac-b2-plan-20261114), round 1

Reviewed commit: a97c2f94d2d13d9630e35127cc8256ecaf665de7

Verdict: changes requested

Reviewer: independent (Claude, reviewer agent); I did not write this work. No worktree modified, no commit, no push.
Scope: b7a4fa40 (rule), 73830064 (script + tests), a97c2f94 (result JSON + PLAN-row draft). a0018635 (later, unrelated
INVALID-TRIALS draft) was not reviewed; it does not touch any file in scope (`git show --stat`).

## Summary

The statistics are sound and the number is reproduced exactly. The rule was committed before the computation, the
script implements the rule, the output is byte-identical on rerun, and my own code gives n_j = 4 / 3 / 3 and n = 4.
The number also holds under the sensitivity checks I ran. Two text defects in the **PLAN-row draft**, which is the
text the author will sign, need fixing before signature: (B1) the decision literal appears twice in the decision
cell, and (B2) the row calls the variance estimate "conservative" without stating the lag bias of unknown
direction or the pooling assumption. The rule, script and JSON need no change. Only the draft has to be revised.

## Checks performed

1. **Order.** b7a4fa40 (23:34:53) → 73830064 (23:36:04) → a97c2f94 (23:37:00) is linear, each commit's parent is the
   previous one, and each touches only its own files. The rule file is byte-identical at a97c2f94 (sha256
   `0294387c0ceacaebe0907ef2c7368d85986052cac8870252bbda96454bd90142`). b7a4fa40 contains no data-derived value.
   Its only data-shaped facts are structural: 15 candidates, an empty `final_audits` and the three nodes, and all of
   these are known without computing a variance. The ignored `r1/scripts/__pycache__/b2_power_plan.cpython-313.pyc`
   has mtime 23:36:15, after the script commit, which is consistent with the stated order. Git order cannot prove that
   no exploratory number was seen earlier. That limit is inherent and is not a finding.
2. **Run and tests.** With `/tmp/trackg_venv/bin/python` and `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin`, the script on
   the pinned manifests (sha `dc5cd04d…b510e62` verified) exits 0. Its output sha256 is `1236d805…6208a6b` and it is
   **byte-identical** to the committed JSON. All 7 tests pass. A run with two finalists returns k = 2 and n_j 5/4/4,
   so n = 5, which matches the draft's sensitivity line.
3. **Independent re-derivation** (`/tmp/rev_power/rederive.py`, my own code that does not import the script). It
   takes the last audited off-mode proposal per root by trial index and asserts that every `/b1/off/` root has one,
   so 0 roots are excluded. It pools ddof-1 variances within candidate, applies the χ² 80 % UCL and the t-based
   smallest n ≥ 2. σ_node is the median `sd_joint` over material edits: digits 5/5 material, credit 2/5, ionosphere
   2/5.

   | node | roots (dof) | sd̂ | sd UCL | σ_node | n_j |
   |---|---|---|---|---|---|
   | digits_mlp | 60 (45) | 0.00282 | 0.00312 | 0.00661 | 4 |
   | openml_credit_approval | 60 (45) | 0.00492 | 0.00544 | 0.01462 | 3 |
   | openml_ionosphere | 60 (45) | 0.01122 | 0.01239 | 0.04237 | 3 |

   **n = 4.** By hand for digits: n = 3 gives 4.303·√(9.733e-6/3) = 0.00775 > 0.00661, and n = 4 gives 3.182·√(9.733e-6/4) = 0.00496 ≤ 0.00661.
4. **σ_node source.** PLAN.md row `R1-C1-FLOOR (24 Oct)` (line 470, identical at 7912b7ff and fcf52c09) accepts
   `results/r1/pilot/E1_20261022T214606Z/` as the C1 noise-floor table. PLAN row `g (22 Oct)` (line 442) defines σ_node
   as the E1 paired comparison-noise sd. The computation matches `r1/c3/dataset.py::noise_table` line for line. As a
   cross-check, PLAN `R1-TRACKS-S02 (c)` gives digits δ_Y = 0.0033 = 0.5 × 0.00661. The E1 summary sha256 is `eabc2f5c…3793`, which matches the draft.
5. **Draft shas.** The rule (`0294387c…0142`), script (`c74a4252…a59f`, full), data (`dc5cd04d…b510e62`), E1
   (`eabc2f5c…3793`) and output (`1236d805…a6b`, full) all match the files at a97c2f94. The table values match the JSON.
6. **Soundness of the rule components.**
   - *Proxy.* B1's `final_audits` is empty for all 18 manifests, so a proxy is needed. B1 ran at W = 20 (RUNBOOK
     X.4), the same W as B2, so there is no budget mismatch. Bias 2 (4 versus 10 seeds) is correct, and the seed
     part of the variance is 2.5× larger, which is conservative. Bias 1 (a missed keep at or after the last audited
     trial) is honestly called of unknown direction in the rule. As a sensitivity check, an upper-envelope proxy
     max(incumbent, candidate) of the last audited proposal gives sd 0.00317 / 0.00508 / 0.01120, and n is unchanged at 4.
   - *Pooling.* Levene (median) tests across the 15 candidates give p = 0.46 / 0.20 / 0.69, so there is no evidence of
     heterogeneity, although the test has low power with 4 instances each. With 45 dof against 3 for the finalist alone,
     pooling is the defensible pre-declared choice.
     gemma4_31b's own sd is 0.00088 / 0.00666 / 0.01922. That is above the pooled UCL on credit_approval and
     ionosphere, and gemma4_31b is the largest of the 15 on ionosphere. Its own point estimate still gives n = 4,
     while its own 80 % UCL on 3 dof would give 5. See B2.
   - *χ² UCL.* V̂·dof/χ²_{0.20}(dof) is the correct one-sided 80 % upper limit. It is the same convention as Track S's
     σ_D,UCL, which is a one-sided 80 % UCL (`r1/tracks/analyze.py` and TRACK_S runbook MA-3 on other branches).
   - *Target and formula.* The target, a 95 % t-CI half-width ≤ 1·σ_node, is a precision target, correctly
     implemented. Plugging V in gives the half-width only at the planning variance. The assurance at n = 4, meaning
     the probability that the realised half-width is ≤ σ_node, is 0.85–0.91 on digits (true sd = UCL or point) and
     ≥ 0.96 elsewhere. That is acceptable but is not stated (see N3). Taking n = max_j n_j is correct for a common
     per-node count.
   - *Cap.* n > 10 gives `cap_status = STOP_author_decides`, `b2_instances_per_node = null`, exit code 3, and the
     number is never clipped. The tests cover this. The behaviour matches the author's signed constraint.
   - *≥ 2 finalists.* k = 2 bounds Var(Y_a − Y_b) by 2V under equal variances and non-negative within-instance
     correlation. Empirically, on B1's shared instances 9001–9004, the mean paired-difference variance divided by
     the mean (V_a + V_b) is 0.93 / 0.82 / 0.49 for the three nodes, so the bound is conservative as claimed.
7. **Overclaims about between-finalist power.** I found none. The rule and draft call this precision, not power,
   and present the k = 2 result only as a descriptive sensitivity. The "POWER-PLAN" naming is addressed in N2.

## BLOCKING

**B1. The decision literal appears twice in the decision cell.** In the English row (draft line 37),
`b2_instances_per_node = 4` occurs twice: in the bold lead ("…rule; b2_instances_per_node = 4.") and again in the
result clause ("**b2_instances_per_node = 4**, seeds 9011–9014"). `grep -o` on the draft gives lines 37 and 37. The
Chinese block also contains it twice (lines 41 and 53), so pasting either version gives two occurrences. The
requirement is exactly once. The B2 verifier design (`B2_GRID_VERIFIER_DESIGN_20261104.md`) also says to "refuse
ambiguous duplicates", and a strict single-match parser would STOP on this row.
*Fix:* keep the literal once, preferably in the lead clause, and write the result clause as "n = 4, seeds 9011–9014".
Make the same change in the Chinese text.

**B2. The signed row overstates conservatism.** The English row says the UCL is "(conservative for B2, which
averages 10 seeds, not 4)". The Chinese says "所以这个估计对 B2 偏保守". Neither mentions the rule's bias 1 (the
last-audited-incumbent lag, direction unknown) or the assumption that between-instance variance is equal across
candidates. The rule itself states bias 1. The draft drops it and so presents the estimate as conservative overall.
For the actual finalist this is not established: gemma4_31b's own sd exceeds the pooled UCL on two of three nodes
(0.00666 vs 0.00544; 0.01922 vs 0.01239). The number is robust: gemma's own point estimate, the upper-envelope
proxy and pooling all give n = 4. The issue is only the signed wording.
*Fix:* in both languages, say that the seed-noise part is conservative (4 versus 10 seeds), that the lag of the last
audited incumbent has unknown direction, and that pooling assumes equal within-candidate variance. Optionally add one
sentence: "gemma4_31b's own B1 point estimate also gives n = 4."

## NON-BLOCKING

- **N1. Function name.** The rule (§3) and the script docstring cite `r1.c3.dataset.node_noise`. The function is
  `r1.c3.dataset.noise_table`, and the computation matches it. Correct the name in the draft or a later note. The
  committed rule should not be edited.
- **N2. "Power" naming.** The row ID and the rule title say "power plan", but the rule is a precision plan. Under
  k = 2, a half-width of 1·σ_node gives only about 50 % power to detect a true difference of 1·σ_node. One clause in
  the row would prevent a reader from treating "power-planned" (RUNBOOK X.6) as power for comparing finalists, for
  example: "precision target; no power claim".
- **N3. Unstated assumptions.** The multiplier 1·σ_node is a declared choice with no stated justification. It is
  coarse compared with δ_Y = 0.5 σ_node (Track S) and g = 0.1 σ_node, so B2 per-node means cannot resolve
  differences on those scales. The planning plugs in V and does not state assurance (computed above as ≥ 0.85).
  Both points deserve a sentence for the author.
- **N4. E1 sha missing from the row.** The E1 summary sha (`eabc2f5c…`) appears in the Inputs table but not in the
  English or Chinese row text, although σ_node is a load-bearing input. The script also only reports this sha and
  does not pin it. Consider adding it to the row.
- **N5. Chinese and English texts differ.** The Chinese block omits the English row's final sentence recording the
  author's 14 Nov instruction. It is also a multi-paragraph blockquote, which cannot be pasted into one §10 table cell
  without `<br>`.
- **N6. Unverifiable gate citation.** The draft says that "the B2 code unit's author gate … requires … the literal
  `b2_instances_per_node = <n>`". I found no code or design text in any local branch that defines this literal
  requirement: the grid design asks for the decision cell to bind the count, not for a literal. Either cite the source
  or soften the wording.
- **N7. Script details.** `NAMESPACE_MAX` is defined but unused, which is moot under the cap. The script does not
  check `audit_seeds == [9101..9104]` or the run id `7912_20261113_d`. It does check the manifest sha, `label`,
  `phase` and `status`. None of this affects the result.
- **N8. Possible improvement for ≥ 2 finalists (future).** Because B1 instances are shared across candidates, the
  paired-difference variance could be estimated directly instead of bounded by 2V. Multiplicity across pairs is not
  addressed. Neither point matters with one finalist.

## Reproduction

```
cd /tmp/pb/wt/b2plan; export AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin
/tmp/trackg_venv/bin/python r1/scripts/b2_power_plan.py --manifests docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json \
  --manifests-sha256 dc5cd04dfc31758b26bb9ed5ebdec38e80ef06730b304d491c433da18b510e62 \
  --e1-summary results/r1/pilot/E1_20261022T214606Z/summary.json --finalists gemma4_31b   # exit 0, sha 1236d805…, byte-identical
/tmp/trackg_venv/bin/python -m pytest -q r1/tests/test_b2_power_plan.py                    # 7 passed
```

Removing the draft-only defects B1 and B2 (and nothing else) should be sufficient for acceptance in round 2. The rule,
script and output can stay as committed.

---

# Independent review: B2 power plan (branch mac-b2-plan-20261114), round 2

Reviewed commit: 5a317b14a2c994722776e03baac9d1ef1be6826b

Verdict: accepted

Accepted commit: 5a317b14a2c994722776e03baac9d1ef1be6826b

Reviewer: independent (Claude, reviewer agent); I did not write this work. No worktree was modified and nothing was
committed or pushed. Scratch work was done in /tmp/rev_power and that folder has been removed.

Scope. 5a317b14 changes only `docs/r1/proposals/PLAN_ROW_R1-EXAM-B2-POWER-PLAN_DRAFT_20261114.md`. The branch
head d1ac6678 adds only the INVALID-TRIALS draft, which I did not review here. That commit does not change any file
in the scope of this review.

## 1. Unchanged inputs and matching shas

These files have identical git blobs at a97c2f94, 5a317b14 and d1ac6678. Their sha256 values at 5a317b14 are:

| file | sha256 |
|---|---|
| rule | `0294387c0ceacaebe0907ef2c7368d85986052cac8870252bbda96454bd90142` |
| script | `c74a4252ed952a7ad4fb69d32fbe69ccc0a58626a3fce9ad12b480025e24a59f` |
| tests | `86a2a898…273d` |
| output JSON | `1236d805ada9587ffd9a5853252ffaa45d345686fb54c331a9cf1e3d96208a6b` |
| B1 manifests | `dc5cd04dfc31758b26bb9ed5ebdec38e80ef06730b304d491c433da18b510e62` |
| E1 summary | `eabc2f5c05b08cf900ab988838e41dc7f8db35a4131f4b57e72514e0e5513793` |

The Inputs table of the draft now gives all five shas in full, and each one matches its file. Each paste block cites
the same five shas by their 8-character prefixes, which also match. The round-1 reproduction (byte-identical output,
7 tests pass, my own code gives n = 4) therefore still applies without change.

The STOP 5 finalist list "accepted at `7bdce776`" is supported by `REVIEW_STOP5_round1.md` (Verdict: accepted,
Accepted commit 7bdce776…).

## 2. Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| **B1** literal twice | **Resolved** | Each paste block's decision cell contains `b2_instances_per_node = 4` once. The gate regex `b2_instances_per_node\s*=\s*(\d+)(?!\d)` finds exactly 1 match in each. The result clause now reads "n = 4". |
| **B2** conservatism overstated | **Resolved** | In both languages the row now says three things: the seed-noise part is conservative (4 seeds against 10), the lag of the last audited incumbent has unknown direction, and pooling assumes equal variance across candidates. It also states that gemma4_31b's own sd exceeds the pooled UCL on credit_approval and ionosphere, and that its own point estimate gives n = 4. The draft body also discloses that gemma4_31b's own 3-dof UCL would give 5. |
| N1 `node_noise` vs `noise_table` | Resolved | An erratum in the draft corrects the name. The committed rule is correctly left unedited. |
| N2 power naming | Resolved | The preamble and both rows say "precision plan" and make no power claim about separating finalists. |
| N3 multiplier scale and assurance | Resolved | The draft body has a "Scale of the target" paragraph. Both rows give the assurance and label it as the reviewer's. The figures 0.85–0.91 and ≥ 0.96 are mine from round 1. |
| N4 E1 sha | Resolved | Both rows now include the E1 sha. |
| N5 Chinese and English differ / multi-paragraph | Resolved | The Chinese block is now a single table cell, includes the author's 14 Nov instruction, and matches the English text point for point. |
| N6 unverifiable gate citation | Resolved | The draft now cites `r1/exam/runtime.py::_b2_author_rows` / `_dated_author_decisions` in the B2 code unit and marks it as under review. I verified the format against that code (§3). |
| N7 script details | Not changed | Acceptable. The script was frozen on purpose and the result does not depend on these details. |
| N8 direct estimate of the paired-difference variance | Not changed | Future work only. It does not matter with one finalist. |

## 3. Gate format: synthetic §10 test

I read `_dated_author_decisions` and `_b2_author_rows` in `/tmp/pb/wt/b2code/r1/exam/runtime.py`, read-only, from
the uncommitted working-tree file with sha256 `0a218f5f…c375`. I exec'd those two functions and the row-ID constants
through `ast`, without importing the module, so the worktree received no `__pycache__`.

For each paste block, I built a synthetic PLAN from `docs/r1/PLAN.md` at 5a317b14. I inserted the block, followed by
a minimal dated author `R1-EXAM-B2-INVALID-TRIALS` row, immediately before `## 11.`. Results:

| case | Chinese | English |
|---|---|---|
| rows found with bare ID as first cell, under a dated author heading | 1 (dated = True) | 1 (dated = True) |
| row has exactly 2 cells (3 pipes); the full decision text is captured | yes | yes |
| literal matches in the decision cell | 1 | 1 |
| `_b2_author_rows(plan, 4)` | **True** | **True** |
| `_b2_author_rows(plan, 5)` and `(plan, 3)` | False, False | False, False |
| heading date `14 Nov 2026` | False | False |
| heading date ISO `2026-11-14` | True | True |
| heading without "author" | False | False |
| block pasted with its code fence | False | False |

If both blocks are pasted, the result is False because there are two rows with the ID. If the draft file is pasted
as-is, no row is found, because its rows sit inside code fences. The unmodified PLAN at 5a317b14 has no such row.

Every format rule stated in the draft is confirmed by these runs: the two-column table, no blank line inside it, the
`### ` heading containing "author" with a full-month or ISO date, the bare ID as first cell, one row only, and the
literal once.

## NON-BLOCKING (residual)

- **R1. Re-test if the gate code changes.** The gate code is uncommitted and still under review. If
  `_dated_author_decisions` or `_b2_author_rows` changes before B2, re-run this format check against the final code.
  The tested file's sha256 is `0a218f5f…c375`.
- **R2. Only the point estimate is in the row.** The row reports gemma4_31b's own point estimate (n = 4) but not its
  own 3-dof UCL (n = 5). The draft body discloses the UCL, which is adequate. The author may still want both in the
  signed row.
- **R3. Paste instructions.** The author must paste only the lines inside the fence, not the ``` lines. The block
  must go inside §10, before `## 11.`, with the heading date written in full-month or ISO form. The draft says all of
  this. I am repeating it because each mistake makes the gate fail silently with a STOP.
