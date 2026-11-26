Reviewed base: e3022076553a5520af843a4a112a56b6ad5f72aa

# S2-M4 R1-BX-D8-CONFIRM draft — independent review record (16 November 2026)

Branch `mac-s2-m4-d8confirm-20261116` from `mac-m11-d8-skew-20261115` @ `cb36a30f`. Unit: `proposals/R1_BX_D8_CONFIRM_DRAFT_20261116.md` and `r1/tests/test_d8_confirm_draft_20261116.py`. Sweep-2 work plan unit S2-M4. The D8-SKEW part was accepted earlier at `4d87d9c8`, READY entry 35. One freshly spawned independent reviewer agent (AI-assisted, Claude), two rounds.
- Round 1 (`e2972e77`): REVISE. 2 MAJOR: the draft misstated the author's 14 Nov answers, both "dev z ≥ 6 not adopted as the final rule" and Q4 "d→c". 5 MINOR, among them a vacuous fence test.
- Round 2 (`e3022076`): ACCEPT. Three optional MINORs are left as is:
  - §3 says the test "checks two things", but it now checks more;
  - Path B step 2 names V1n and `ELIG_Z_MIN` = 3 as if already chosen;
  - V2 is not covered under "Coupled items".
- The reviewer reported that in round 1 a `python -I` probe wrote two git-ignored `__pycache__` directories, which it then removed. The worktree was clean afterwards.

Accepted commit (last round): e3022076553a5520af843a4a112a56b6ad5f72aa

The round texts are reproduced unchanged below.

---

# Independent review: S2-M4 (part 2), draft `R1-BX-D8-CONFIRM` after D8-TEST and D8-SKEW (round 1)

Reviewed base: `e2972e776fd5cfb695ae64139438854e2f8dcf1e` on `mac-s2-m4-d8confirm-20261116`, one commit on
`mac-m11-d8-skew-20261115` @ `cb36a30f`. `git diff --stat cb36a30f e2972e77` lists only
`docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261116.md` (+102) and `r1/tests/test_d8_confirm_draft_20261116.py` (+53).
Reviewer: independent agent (AI-assisted, Claude). I did not write the work.

## VERDICT: REVISE

The mechanics are right. Path A is byte-identical to the 14 Nov row and passes the real guard. The gate commit, the
SHA and the ancestry are correct. The path-B template is the parser's fixed text with exactly two placeholders. Nothing
in the draft can satisfy the guard.

Two MAJOR findings are about how faithfully the draft represents the author's own earlier answers. It presents as
open, or as live options, two things the author ruled on in the 14 Nov message quoted in
`M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md`: Q4 and dev z ≥ 6. One test assertion is vacuous.

## Findings

### 1. MAJOR: Q4 is shown as "still open", and the decision row offers an option the author did not choose

- **Location.** §1 table, last row ("Item 15: no minimum test instances per node (Q4) | still open | the author's answer
  to Q4"). Decision-row draft, item (5): "minimum test instances per node (Q4): [none | n]".
- **Evidence.**
  - The options put to the author for D8-Q4 (`/tmp/pb/questions_20261114.md`) were:
    - (a) no minimum;
    - (b) 10 only after a plan change;
    - (c) a per-tier minimum the plans allow, stated with the split proportions;
    - (d) fix the proportions first, then decide.
  - The author answered on 14 Nov: "Q4 先固定 train/dev/test 比例，再定计划可达的分层下限（选项 d→c）". In English: fix the
    proportions first, then set a plan-achievable per-tier floor. The message is quoted at
    `docs/r1/reports/M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md` l. 8. The same report's §4 reads it as
    "Q4 (d → c)".
  - D8-TEST §4 then gives the per-tier floors that follow from each split:
    - P3: T0 ≥ 9; T1 ≥ 6 (× 12) or ≥ 3 (× 6);
    - P2: T0 ≥ 6; T1 ≥ 4 or ≥ 2.
  - So the form of the Q4 answer is decided (per-tier floor, option c). Only its values remain, and they follow from
    the split choice in item (3).
  - The draft calls Q4 "still open", offers "none", which is option (a) and was not chosen, and offers a single "n",
    which cannot express a per-tier floor.
- **Fix.**
  - In the table, record the author's 14 Nov Q4 answer (d → c). Say what is still open: the floor values, which follow
    from the split.
  - In the decision row, replace (5) with a per-tier floor tied to (3), for example "[P3: T0 ≥ 9, T1 ≥ 6 (× 12) / ≥ 3
    (× 6) | P2: T0 ≥ 6, T1 ≥ 4 / ≥ 2]".
  - Note that a per-tier floor is gate code (a STOP), so it belongs in gate v3. Note also that a floor of 2–3 on T1
    interacts with V1n's point-denominator STOP.

### 2. MAJOR: path A and decision-row option (2) do not say that the author ruled out dev z ≥ 6 as the final rule

- **Location.** §2 "Path A: confirm gate v2 as it is" ("This adopts every v2 convention, including … dev z ≥ 6").
  §1 table, row "Item 14". Decision row, item (2): "[or: keep dev z ≥ 6]".
- **Evidence.**
  - The author's 14 Nov message (eligibility-alternatives report, l. 7) says: "D8：暂不确认。Q2 的 dev z ≥ 6 在 2–6 个
    dev 实例下近乎随机排除节点，不采用为最终规则". In English: D8 not confirmed for now; dev z ≥ 6 excludes nodes nearly at
    random with 2–6 dev instances, and is not adopted as the final rule.
  - The draft offers path A, and "keep dev z ≥ 6" in the decision row, as plain options. Path A's list of required
    disclosures does not mention the ruling.
  - The table cites only the gate v2 report's finding and "D8-TEST simulated R1 instead". That reads as a technical
    preference, not an author ruling.
- **Fix.**
  - State in path A that confirming gate v2 as it is would reverse the author's 14 Nov ruling on dev z ≥ 6.
  - In the table's Item 14 row, cite the ruling.
  - In the decision row, either drop "keep dev z ≥ 6" or mark it "(reverses the 14 Nov ruling)".
  - Path A can stay, because the author may reverse the ruling. It must not read as the uncontroversial default.

### 3. MINOR: the "fenced block" assertion in `test_decision_row_draft_is_not_a_confirmation` is vacuous

- **Location.** `r1/tests/test_d8_confirm_draft_20261116.py`, last two lines. The comment reads "Every candidate row
  in the draft is inside a fenced block, so the draft text itself confirms nothing."
- **Evidence.** I ran a probe that calls the real `_confirmation_commit` on variants of the draft text, with the
  test's own `## 10.` and `### 16 November 2026 (author)` prefix. Results:

  | Input | Result |
  |---|---|
  | as in the test | `None` |
  | **all ``` fences removed** | **`None`** |
  | fences removed and the draft's own `#` headings removed | `None` |
  | fences removed, headings removed, `\| ID \| Decision \|` header inserted before the path-A row | `da264a40…` (accepted) |
  | fences kept, header inserted, headings removed | `None` |

  - The assertion still passes with the fences removed, for two reasons. The draft's first line, `# Draft …`, resets
    `dated_author`, and `## 1.` leaves §10. And the draft has no decision-table header.
  - So the test proves nothing about the fences. It would not catch an edit that unfences the rows.
  - The real property the comment claims does hold, because only the fences stop the row once a header is present.
    The guard reads only `PLAN.md`, so this is not a safety hole.
- **Fix.** Build the synthetic input so that only the fences can be what refuses it:
  - strip the draft's `#` lines;
  - insert a `| ID | Decision |` header before each candidate row;
  - assert `None`;
  - add a control assertion that the same input with the fences removed returns the path-A commit.

  Otherwise, drop the claim from the comment. The other three tests are meaningful:
  - path A is equal to the 14 Nov row;
  - the filled template passes the real parser with the current SHA;
  - the filled template equals path A with only the commit replaced;
  - the template with its placeholders is refused (the hex pattern fails).

### 4. MINOR: D8-SKEW's findings are attributed to gate v2 without their conditions, and PoI is overstated for (a)

- **Location.** §1 table, row "Item 2" ("under left-skewed data (a) false-passes up to 0.24 per arm … Under symmetric
  noise the PoI conjunct is what keeps (a), (b1) and (d) calibrated"). Path A disclosures ("that PoI alone carries its
  calibration under symmetric noise").
- **Evidence.**
  - Every D8-SKEW rule ran with V1n and R1 z ≥ 3 (D8-SKEW §1), not with gate v2's V0 and dev z ≥ 6. Under V0 the gate
    STOPs in 0.94–0.99 of reps up to μ = 1.5 (D8-TEST §3.1). D8-TEST §3.4 says that when V0 reads under skew, it
    false-passes in up to 0.50 of those reads, and that this rests on very few reads.
  - D8-SKEW §3.2 says PoI keeps (b1) and (d) calibrated "and partly" (a). §4 names only (b1) and (d). Rule (a)'s primary
    bound alone exceeds the thresholds only within MC error (0.068 two-arm, 0.038 per arm), apart from the secondary
    T1 × 6 check.
  - D8-SKEW §4 asks the confirmation draft to say two things: that PoI gives no protection against skew, and what PoI
    does under symmetric noise. Path A's list only implies the first.
- **Fix.**
  - Qualify the Item 2 finding as "(with V1n and R1 z ≥ 3)".
  - For path A, cite D8-TEST §3.4 for v2 as it is.
  - Change the PoI wording to "(b1) and (d), and partly (a)".
  - Add "PoI gives no protection under left skew" to path A's disclosures.

### 5. MINOR: the decision row treats coupled items as independent, and claims the split is bound by the gate SHA

- **Location.** Decision-row draft, items (1), (3), (4) and its closing sentence.
- **Evidence.**
  - Under (4)(b2), the declared +∞ convention fails the arm whenever more than 2.5 % of resamples have an eligible node
    with mean(d\*) ≤ 0. That replaces V1n's node-level −∞ clause from (1). It is a denominator-positivity screen, the
    mechanism D8-TEST moved away from, and the reason (b2) has almost no power at μ ≤ 1 (D8-SKEW §3.3).
  - Under (4)(c), the pass decision does not resample the ratio at all.
  - So V1n's bootstrap clause has effect only with (a), or for an IQM effect-size interval if one is reported. The
    author should see this when choosing (1) and (4) together.
  - Separately, the draft's own table says the split is "not in the gate; the caller supplies them". The row's closing
    sentence still says all items are "Implemented in gate v3 … and bound by R1-BX-D8-CONFIRM's SHA". Item (3) is not.
- **Fix.**
  - Add one clause to (1): "the bootstrap clause applies to the IQM interval; under (4)(b2) the +∞ screen governs;
    under (4)(c) only the point STOP applies".
  - Reword the closing sentence: either "(1), (2), (4), (5) implemented in gate v3 …; (3) applied by the split code and
    recorded", or have gate v3 check the per-tier test counts.

### 6. MINOR: the option framing in items (1) and (2) leans towards the recommendations

- **Location.** Decision row, items (1) and (2).
- **Evidence.**
  - Items (3) to (5) use symmetric brackets.
  - Items (1) and (2) write the recommended option (V1n; R1 z ≥ 3) as the row's main text, with the alternative as
    "[or: keep …]".
  - Item (1) also omits D8-TEST's other listed alternatives: V2 (which changes the estimand and needs a PLAN amendment)
    and V1 (the strict reading).
- **Fix.** Use the same bracket form for every item, e.g. "[V1n … | V1 … | V2 (amends R1-BX-D8's per-node gap
  closed) | v2's STOP]". Mark which one the reports recommend in the prose outside the row.

### 7. MINOR: under (c), the amendment covers more than "R1-BX-D8's primary criterion"

- **Location.** §2 paragraph under path B, step 3. Decision-row option (4)(c).
- **Evidence.** These texts are affected under (c):
  - R1-BX-D8 (author branch `fd275c53`, `PLAN.md` l. 752) fixes the primary criterion as "the IQM of gap closed and the
    probability of improvement, with node-stratified bootstrap CIs";
  - R1-BX-PROPOSED-CONFIRM (D8) (l. 780) confirms the number "pass if the IQM lower bound is > 0 and the PoI lower
    bound is > 0.5".

  Option (c) changes both: a Student-t test replaces the IQM bootstrap bound.
- **What the draft gets right.** Its claim that (c) needs an explicit amendment and a change to the parser pattern is
  correct. The pattern is a `re.fullmatch` on fixed wording, which includes "with the numbers confirmed in
  R1-BX-PROPOSED-CONFIRM (D8)". Under (c) that wording would be false, and no amendment row can make it true without
  new wording. (b2) keeps the IQM and a node-stratified bootstrap bound, so "changes only its interval" is fair.
- **Fix.** In option (4)(c), write "amending R1-BX-D8's primary criterion and the confirmed pass rule of
  R1-BX-PROPOSED-CONFIRM (D8)".

## What I verified

1. **Path A.**
   - It is byte-identical to the 14 Nov row: the new test checks this, and the 14 Nov test still finds exactly one row
     in the old file.
   - `sha256(r1/c3/gate.py)` = `02fdbdd2…c873` in the worktree, at `da264a40`, and on `int-main-sweep2-20261116`
     (`bc164b2e`).
   - `git merge-base --is-ancestor da264a40 int-main-sweep2-20261116` returns 0.
   - `analysis_guard.py` SHA `2f6a720e…d213` is unchanged since the 14 Nov draft, as §3 says. It is identical on the
     integration branch.
   - `test_d8_confirm_draft_matches_parser.py` runs the real `require_d8_confirmation` in a synthetic repo, and it
     passes.
   - The gate v2 review is accepted at `80d70832`, with `gate.py` unchanged since `da264a40`.
2. **Path-B template.**
   - Filled with the current SHA and a 40-hex commit, it is accepted by `_confirmation_commit`, a `fullmatch` on the
     fixed pattern.
   - It equals path A with only the commit replaced. Together these show it is the parser's text with exactly two
     placeholders.
   - With its placeholders it is refused.
   - The fenced-block assertion is vacuous (finding 3).
3. **Summary table.**
   - These items are accurate: item numbers 2, 4, 14 and 15 against the 14 Nov list; "2–9 test instances"; V1n's
     definition; R1 with δ_n kept; the split recommendation (lean P3, keep P2 if Track P binds); and the D8-SKEW figures
     (0.238 → "0.24", (b2) 0.285 → "0.29", (c) ≤ 0.083 and 0.840).
   - The acceptance commits are correct: D8-TEST at `1d34de18` (review R3 ACCEPT) and D8-SKEW at `4d87d9c8` (review
     ACCEPT).
   - Two items need revision: Q4 status (finding 1) and the conditions and PoI wording (finding 4).
4. **Decision row.**
   - It does not decide for the author.
   - Its representation needs the fixes in findings 1, 2, 5, 6 and 7.
   - The claim that (c) amends R1-BX-D8 and needs a parser-pattern change is correct (finding 7).
5. **Authority and order.**
   - The guard reads only `docs/r1/PLAN.md` at HEAD. The draft is in `docs/r1/proposals/`.
   - Every candidate row is fenced. The R1-BX-D8-V3 row's first cell is not `R1-BX-D8-CONFIRM`, so pasting it would
     neither confirm anything nor break the guard's one-row rule.
   - No code reads PLAN for the substring `R1-BX-D8-CONFIRM`. `gate.CONFIRM_ID` is an unused constant.
   - §4's order is correct: confirmation before any sweep-2 label table is copied back for analysis or read
     (R1-BX-D8, PLAN l. 752); collection and sealed storage are not blocked (runbook `docs/r1/prompts/
     SWEEP2_HTCONDOR_RUNBOOK_20261116.md` @ `a2789ea6`, l. 21–23 and S2-M1; R1-SWEEP-HOST-HTC keeps the lock).
   - The draft's `prompts/…` citation is relative to `docs/r1`, consistent with its `reports/…` citations.
6. **Tests.** `test_d8_confirm_draft_20261116.py` and `test_d8_confirm_draft_matches_parser.py` give 6 passed.
   Together with `test_c3_analysis_guard.py` they give 45 passed (pinned venv, `-p no:cacheprovider`,
   `PYTHONDONTWRITEBYTECODE=1`).

**Process note.** My first probe ran Python with `-I`, which ignores `PYTHONDONTWRITEBYTECODE`. It wrote
`r1/__pycache__/` and `r1/c3/__pycache__/` (git-ignored, untracked) into the worktree at 02:05:56. I deleted exactly
those two directories, and `git status --short --ignored` is now empty. Nothing else in the worktree or the repo was
changed. Scratch is under `/tmp/pb/rev_s2m4/`: `probe.py`, `plan_author.md` and this file.

---

# Independent review: S2-M4 (part 2), draft `R1-BX-D8-CONFIRM`, round 2

Reviewed base: `e3022076553a5520af843a4a112a56b6ad5f72aa` on `mac-s2-m4-d8confirm-20261116`. It is one commit on the
round-1 base `e2972e77`. `git diff --stat e2972e77 e3022076` touches only
`docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_20261116.md` (+/− 44) and `r1/tests/test_d8_confirm_draft_20261116.py`
(+/− 28). Reviewer: the same independent agent as in round 1 (AI-assisted, Claude). I worked read-only, did not use
`python -I`, and `git status --short --ignored` is empty after my runs.

## VERDICT: ACCEPT

All round-1 findings are resolved. No BLOCKING or MAJOR finding remains. Three MINOR wording points are listed below.
They are optional and do not affect the verdict.

## Round-1 findings: status

| R1 | Status | Check |
|---|---|---|
| F1 (MAJOR) Q4 | **Resolved** | The §1 table quotes the author's Q4 answer "d→c". Item (5) offers only the four per-tier floors tied to the split, matching D8-TEST §4 (P3: T0 ≥ 9, T1 ≥ 6 / ≥ 3; P2: T0 ≥ 6, T1 ≥ 4 / ≥ 2). It is in v3's scope and in the closing sentence. "none" and a single n are gone. Path A says it would leave the Q4 floor unimplemented. |
| F2 (MAJOR) dev z ≥ 6 | **Resolved** | The table quotes the 14 Nov ruling verbatim. It matches `M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md` l. 7. Path A's heading and text say confirming it would reverse that ruling. Item (2) offers only R1 (train + dev z ≥ 3) or R2 (σ_node after rescaling). The claim that R2 is "not calibratable until σ_node is on the instance scale" matches the alternatives report §4 item 3 and l. 129. |
| F3 (MINOR) vacuous fence test | **Resolved** | `test_fences_are_what_keep_the_draft_rows_inert` places the fenced path-A block directly under a valid author table header and the parser refuses it. It places the same block unfenced and the parser accepts it, returning the row's commit. So the fence alone decides, and the test would catch an unfencing edit. The third assertion (the whole draft with its headings stripped is refused) is weaker, because the draft has no table header before its rows, but it claims no more than that. The decision-row test now places the V3 row under a valid header and checks that the parser refuses it. |
| F4 (MINOR) D8-SKEW conditions, PoI | **Resolved** | "simulated with V1n and train + dev z ≥ 3, not with v2's settings" is stated in the table and in path A. "(b1) and (d), and partly (a)" matches D8-SKEW §3.2. "PoI gives no protection under left skew" is in the table and in path A's disclosures. |
| F5 (MINOR) coupled items, split vs SHA | **Resolved** | The new "Coupled items" paragraph covers (b2)'s +∞ screen and (c). It says the split is caller-supplied and not bound by the CONFIRM SHA. The closing sentence of the row now names only items (1), (2), (4) and (5). |
| F6 (MINOR) option framing | **Resolved** | Every item uses symmetric brackets. Item (1) now offers V1n, V1 and V2. Their definitions match D8-TEST §1. V2 carries the PLAN-amendment note, as D8-TEST §3.3 requires. |
| F7 (MINOR) scope of (c)'s amendment | **Resolved** | The prose and option (4)(c) name both amendments: R1-BX-D8 (primary criterion and its bootstrap CIs) and R1-BX-PROPOSED-CONFIRM (D8)'s pass rule. Both match the author branch `fd275c53`, `PLAN.md` l. 752 and l. 780. The parser-pattern note is kept and is correct. |

## New MINOR findings (optional)

1. **§3 "Checks" is stale.** It still says the new test "checks two things". The test now also checks that the fences
   are what keep the rows inert, and that the V3 row is not a confirmation row. Fix: add one line.
2. **Path B step 2 still lists the recommended options as fixed** ("`ELIG_Z_MIN` = 3 on train + dev; the V1n bootstrap
   convention"). The decision row now offers V1, V2 and the σ_node route as well. Fix: "as chosen in R1-BX-D8-V3 (for
   the recommended options: …)".
3. **"Coupled items" covers V1n and V1, but not V2.**
   - Under V2 with (b2) or (c), what the tier-pooled resampled-denominator STOP does is not stated.
   - V2's estimand is D8-SKEW's (d), the worst rule under left skew (0.333 per arm). That could be noted next to the
     V2 option.

## What I verified

- **Rows unchanged.**
  - Path A is still byte-identical to the 14 Nov row.
  - The template still equals path A with only the commit and the SHA replaced.
  - No line starting with `| R1-BX-D8-CONFIRM` changed in the diff.
  - Gate SHA, commit `da264a40` and ancestry are as in round 1, and nothing that bears on them was touched.
- **Tests.** `test_d8_confirm_draft_20261116.py`, `test_d8_confirm_draft_matches_parser.py` and
  `test_c3_analysis_guard.py` give 46 passed: the 7 draft tests plus the guard suite. I used the pinned venv,
  `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`.
- **Authority and order.**
  - Every candidate row is still fenced.
  - The V3 row is unique, and its first cell is not `R1-BX-D8-CONFIRM`.
  - §4's order relative to sweep 2 is unchanged and correct.
- **New factual statements** checked against their sources:
  - the 14 Nov quotes;
  - the R2 calibration statement;
  - the V1 and V2 definitions;
  - the per-tier floors;
  - the PLAN wording of R1-BX-D8 and R1-BX-PROPOSED-CONFIRM (D8).
