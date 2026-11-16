Reviewed base: bedba308b45995fc39a6b0820debc187bf2b4994

# Cross-proposer disclosure paragraph (from X.7(c)) — independent review record (16 November 2026)

Branch `mac-xprop-disclosure-20261116` from `mac-s2-m5-x7c-20261116`. Unit:
- `proposals/CROSS_PROPOSER_DISCLOSURE_DRAFT_20261116.md` (EN and ZH);
- `r1/scripts/x7c_mu_paired.py`, post hoc;
- `reports/x7c_appendix_20261116/mu_paired.{json,md}`.

Author request of 16 Nov (item 4). One freshly spawned independent reviewer agent (AI-assisted, Claude), three rounds. Each round's rerun reproduced the post hoc outputs byte for byte.
- **Round 1 (`f10da83b`): REVISE.** 3 MAJOR and 7 MINOR. The MAJOR findings:
  - the skip conclusion compared an upper bound with an upper bound;
  - the paragraph was not scoped to the exam data, and the stack and seed disclosures were missing;
  - the Q2 sentence was partly wrong.
- **Round 2 (`228bc5d2`): ACCEPT,** with 3 minors.
- **Round 3 (`bedba308`, minors fixed): ACCEPT.** Two optional nits are left as is:
  - two adjacent sentences start "The pick was selected on…";
  - the llama-server build difference could go in the full manuscript table.

Accepted commit (round 3, last): bedba308b45995fc39a6b0820debc187bf2b4994

The round texts are reproduced unchanged below.

---

# Review R1: cross-proposer disclosure paragraph (Paper B / R1), 16 Nov 2026

Reviewer: independent agent (did not write the work). Read-only; scratch only under /tmp/pb/rev_xprop/.
Reviewed base: `f10da83bcaa85239208b47f20d5d75aba377d7aa` (branch `mac-xprop-disclosure-20261116`, parent `31ed1c19`).

VERDICT: REVISE

All the numbers I checked but one are right. The rerun reproduces `mu_paired.json` byte for byte, and the post hoc
script matches the appendix's bootstrap. Three MAJOR problems remain in the wording: one inference does not follow,
one claim is partly wrong, and one scope is missing.

## Findings

### 1. MAJOR: the "much less to skip" conclusion rests on comparing an upper bound with an upper bound
- **Location.** EN paragraph, "The first is the share…" ending "Under the pick the rule layer therefore has much less
  to skip than in sweep 1." ZH, "因此在 pick 下，规则层可跳过的远少于 sweep 1。"
- **Evidence.** The paragraph says correctly that Q1 is an upper bound. It then compares the pick's bound (0.175) with
  the anchors' bounds (0.545, 0.579) and concludes "therefore". But a smaller upper bound does not show a smaller true
  share. The conclusion is valid only because the anchors' replayed repeats alone are above the pick's whole bound:
  0.351 for qwen2.5-coder and 0.219 for random_valid (`X7C_APPENDIX_20261116.md` §2.1 breakdown and "What the comparison
  supports"). The X.7(c) review (round 2, lines ~231–233 and ~300–301) required the sweep sentence to rest on exactly
  that comparison of a lower bound with an upper bound. The draft keeps that argument in "Notes for the author" but
  leaves it out of the paragraph, so a reader of the manuscript sees a non sequitur.
- **Fix.** Before "therefore", add one sentence to both paragraphs, for example: "The replayed repeats alone, a lower
  bound on the skippable share, are 0.351 for `qwen2.5-coder:7b` and 0.219 for `random_valid`, above the pick's whole
  upper bound (post hoc decomposition)." Then keep the conclusion.

### 2. MAJOR: the paragraph is not scoped to the exam data, and does not say the sweep contrast is "proposer plus stack" (R1-MAIN-PROPOSER (c), (i))
- **Location.** EN title "Proposer differences between the two sweeps", the opening sentences, and "…than in sweep 1".
  Same in ZH.
- **Evidence.**
  - Every number comes from the exam: B1, 12 thinking-off instance clusters on the three exam nodes, exam seeds 9101+,
    K = 4 audits, run on the exam's 4090 stack. B2 is the finalist only, with K = 10. None of it is sweep data.
  - Sweep 2 has not run, and R1-SWEEP-HOST-HTC does not authorize it. The paragraph still says "sweep 2 uses" and draws
    a conclusion about sweep 1 against sweep 2.
  - R1-MAIN-PROPOSER (c) says the cross-proposer contrast between the sweeps is "proposer **plus** stack", and that the
    stack differences go in every cross-proposer table. Since then they include the 4090 selection host against the
    L40S deployment host (R1-SWEEP-HOST-HTC, "如实披露") and context 32,768 (R1-SWEEP2-SETTINGS).
  - (i) asks for the node-overlap / disjoint-seed statement as well as the winner's curse.
  - The draft's header says the paragraph serves (c) and (i), but the paragraph mentions only the winner's curse, and
    "Two C3 premises differ by proposer" reads as a claim about the sweeps.
  - Within B1 the comparison is proposer-only, which is a strength, but the paragraph never says so.
- **Fix.**
  - State that the values come from the selection exam: B1, three of the eight sweep nodes, exam instances and seeds,
    one stack. Say what they imply for the sweeps, for example "we expect the A2 layer to have much less to skip in
    sweep 2 than in sweep 1".
  - Use future or conditional tense for sweep 2.
  - Add one sentence: the sweep 1 and sweep 2 contrast also differs in stack, with the differences listed in the
    table (R1-MAIN-PROPOSER (c), as amended).
  - Add one sentence that exam and sweep seeds are disjoint, so no label leaks ((i)).

### 3. MAJOR: the Q2 sentence is partly wrong and gives no direction
- **Location.** EN "The second is the dispersion of audited increments. Its pooled difference comes mostly from one
  node." ZH "第二，审计增量的离散度。其合并差异主要来自一个节点。"
- **Evidence.**
  - Q2 differs from all three anchors, in different directions: the pick is lower than `random_valid` and
    `qwen2.5-coder:7b`, and higher than scripted.
  - I dropped one node at a time from the B1 thinking-off deltas (scratch `s/check.py`):
    - **Against `qwen2.5-coder:7b`.** Without `digits_mlp` the pooled sds become 0.0061 for qwen2.5-coder and 0.0154
      for the pick, so the order reverses. The difference comes from one node. ✓
    - **Against scripted.** Without `openml_ionosphere` they become 0.0060 and 0.0051, so the order reverses. ✓
    - **Against `random_valid`.** The pick is lower on all three nodes (per node 0.044/0.0175/0.024 against
      0.005/0.0052/0.021). With any single node dropped, `random_valid` stays higher (0.0207–0.0358 against
      0.0051–0.0154). Here the difference does **not** come from one node. The appendix §2.2 says the same ("lower on
      all three nodes").
  - The singular "Its pooled difference" hides all of this.
- **Fix.** Either drop Q2 from the paragraph (the request was about Q1 and μ̂), or state it per anchor. For example:
  "Pooled dispersion is lower than for `qwen2.5-coder:7b` and `random_valid` and higher than for scripted. The
  qwen2.5-coder and scripted differences each come from one node (`digits_mlp`, `openml_ionosphere`); the
  `random_valid` difference holds on all three nodes."

### 4. MINOR: a rounding error in one interval endpoint
- **Location.** EN and ZH, scripted line: "difference −0.00030 [−0.00177, 0.00096]".
- **Evidence.** `mu_paired.json`: ci95 lower = −0.0017648913869928277, which rounds to **−0.00176** at five decimals.
  `mu_paired.md` shows −0.001765.
- **Fix.** Change it to −0.00176 in both languages.

### 5. MINOR: the paragraph does not mark the paired μ̂ intervals as post hoc
- **Location.** EN and ZH, μ̂ bullet list.
- **Evidence.** The script docstring, the draft header and the Notes all say post hoc, but the paragraph presents the
  difference intervals in the same voice as the declared Q1–Q3 comparisons. `mu_paired.md` is a bare table without a
  post hoc line, and `mu_paired.json` has no `post_hoc` or description field.
- **Fix.**
  - Add "(post hoc paired cluster-bootstrap intervals)" to the μ̂ sentence in both languages.
  - Put one header line in `mu_paired.md` and a `"note"` field in the JSON.

### 6. MINOR: "does not differ" reads as a claim of equality
- **Location.** "the scripted anchor's bound, 0.149, does not differ from the pick's"; "The A4 forecast calibration
  does not differ". ZH: "无差异", "没有差异".
- **Evidence.** The CIs [−0.024, 0.080] and [−0.010, 0.074] include zero. With 12 clusters, that is not evidence of
  equality.
- **Fix.** Use "is not distinguishable from" ("区间含 0，无法区分").

### 7. MINOR: the EN and ZH versions differ slightly
- **Location.** ZH Brier sentence.
- **Evidence.** EN says "0.239 vs 0.214 for `qwen2.5-coder:7b`". ZH says "Brier 0.239 对 0.214" without naming the
  comparator. Otherwise the two say the same thing. ZH "预声明" for EN "declared" is acceptable, because x5_rule_v2 was
  approved in R1-EXAM-RULE-X5V2 before B1.
- **Fix.** Add "（对 `qwen2.5-coder:7b`）".

### 8. MINOR: the post hoc script drops the appendix's input self-checks
- **Location.** `r1/scripts/x7c_mu_paired.py` `main`.
- **Evidence.** The script drops these checks from `x7c_appendix.py`:
  - the EVIDENCE/b1/COMPLETE manifest gate;
  - the "12 off roots" check;
  - "usage trials == manifest trials";
  - μ̂ against the B1 analysis to 1e-12.

  It also does not record the Python or NumPy version. The outputs are right: the input sha256 values match the
  appendix's recorded inputs, and μ̂ matches the appendix. So this is about robustness only.
- **Fix (optional).** Reuse the gate checks, assert `len(ids) == 12`, and record `python` and `numpy` in the JSON.

### 9. MINOR (optional): leaving out `random_valid` from the μ̂ list understates the disclosure
- **Location.** μ̂ bullet list.
- **Evidence.** Pick − `random_valid` = +0.00400 [−0.00050, 0.00802]: on B1 μ̂ the pick cannot be distinguished even
  from the random anchor. The Notes say so, but the paragraph does not. The request did not ask for it, and the
  paragraph makes no strength claim, so this is optional.
- **Fix.** Consider adding a fourth bullet or a clause.

### 10. MINOR: some terms need defining in the manuscript
- **Evidence.** "R1-EXAM-X7", "C3 premises", "A2/A4", "B1/B2", "root" and "anchor" are internal names. That is fine
  for a draft, but they need defining or replacing in the manuscript.

## What I verified

1. **Provenance.**
   - HEAD is `f10da83b`, parent is `31ed1c19` (the accepted X.7(c) review record), one commit, four files.
   - The worktree is clean after my rerun (`git status --porcelain` is empty).
2. **Rerun.**
   - `x7c_mu_paired.py` with the given inputs writes `/tmp/pb/rev_xprop/mu.json`, which is byte-identical to
     `docs/r1/reports/x7c_appendix_20261116/mu_paired.json` (`cmp`).
   - The input sha256 values (`dc5cd04d…`, `b5107bcb…`) equal the b1 inputs recorded in `x7c_output.json`.
3. **Consistency with the appendix bootstrap.**
   - The script uses the same seed (20261116), B = 10,000, sorted instance ids, the thinking-off filter on both usage
     and audited proposals, `row_data`/`quantities`/`interval`, and a shared resample per draw across rows (paired).
   - The RNG draws one index vector per resample whatever the row count. I confirmed that the 4-row and 18-row
     bootstraps give identical μ̂ draws, and that the per-row μ̂ CIs equal the appendix's `ci95.mu_hat` exactly for
     all four rows.
   - The paired differences from the 18-row draws equal `mu_paired.json`.
4. **Numbers against the sources.**
   - Q1 0.175 [0.129, 0.221]; B2 0.188 [0.142, 0.242]; qwen2.5-coder 0.545 [0.484, 0.608]; random_valid 0.579
     [0.524, 0.625]; scripted 0.149 (pick − scripted +0.026 [−0.024, 0.080]).
   - Both Q1 finalist − anchor CIs exclude zero, also under Bonferroni.
   - Brier 0.239 against 0.214 (CI [−0.010, 0.074]).
   - μ̂: −0.00089, −0.00059, +0.00016.
   - Differences: −0.00030 [−0.00176 (draft says −0.00177), 0.00096] and −0.00105 [−0.00497, 0.00296].
   - Notes: 0.351 and 0.219, 10,000 resamples, seed 20261116. All match except the one endpoint in finding 4.
5. **Over-claiming.**
   - The paragraph calls Q1 an upper bound and names its components (repeats/no-ops, invalid, first trials).
   - The winner's curse is stated, and no strength claim is made.
   - "None of these differences excludes zero" is backed by the paired intervals, and the ordering is disclosed as
     R1-EXAM-X7 (a) requires (below scripted; the paired CI is a stronger basis than "overlapping CIs").
   - "Chosen by the declared rule" agrees with R1-MAIN-PROPOSER (a): finalists by B1 thinking-off μ̂, pick by best B2
     audited Y.
   - What remains is findings 1–3.
6. **PLAN.** I read R1-EXAM-X7, R1-MAIN-PROPOSER (a), (c) and (i), R1-EXAM-RULE-X5V2, R1-SWEEP-HOST-HTC and
   R1-SWEEP2-SETTINGS from `gh/author-decisions-20261116:docs/r1/PLAN.md` (finding 2).

Scratch: `/tmp/pb/rev_xprop/mu.json`, `/tmp/pb/rev_xprop/PLAN.md`, `/tmp/pb/rev_xprop/s/check.py`.

---

# Review R2: cross-proposer disclosure paragraph (Paper B / R1), 16 Nov 2026

Reviewer: independent agent (did not write the work). Read-only; scratch only under /tmp/pb/rev_xprop/.
Reviewed base: `228bc5d28fa8731d920e52489265da377c4bf68e` (one commit on `f10da83b`). Worktree clean before and after.

VERDICT: ACCEPT

All ten round-1 findings are resolved. The rerun with `--b1-analysis` reproduces `mu_paired.json` and `mu_paired.md`
byte for byte. Every number in both paragraphs matches the sources, and the ZH paragraph says the same as the EN one.
Three MINOR points remain, all about the completeness of the stack list. None blocks acceptance; the author can apply
them when the text goes into the table.

## Round-1 findings: status

| R1 finding | Status | Evidence |
|---|---|---|
| F1 MAJOR (bound vs bound) | resolved | Both paragraphs now give the post hoc decomposition before the conclusion: the replayed repeats alone are 0.351 for qwen2.5-coder and 0.219 for random_valid, both above the pick's upper bound of 0.175. The conclusion is hedged ("can be expected to", "可以预期"). The numbers match the appendix §2.1 breakdown. |
| F2 MAJOR (scope, (c), (i)) | resolved (see m1 and m2) | The title and opening now say "measured on the selection exam". The scope is given as B1 thinking-off roots on 3 of the 8 sweep nodes, one 4090 stack, with B2 values for the pick only. Sweep 2 is in the future tense. B1 is described as proposer-only. The sweep contrast is "proposer plus stack", with a list. Exam and sweep seeds are stated as disjoint, matching PLAN (i): exam 9001+ and 9101+/9201+, sweeps 7001–7010 and the sweep instance seeds. |
| F3 MAJOR (Q2) | resolved | Q2 is now stated per anchor: lower than qwen2.5-coder, mostly from `digits_mlp`; lower than random_valid on all three nodes; higher than scripted, mostly from `openml_ionosphere`. My leave-one-node-out check from round 1 agrees: dropping `digits_mlp` reverses the qwen order, dropping `openml_ionosphere` reverses the scripted order, and random_valid stays higher whichever single node is dropped. |
| F4 (rounding) | resolved | −0.00176 in EN and ZH. |
| F5 (post hoc label) | resolved | The paragraph says "paired post hoc intervals" ("事后配对区间"). `mu_paired.md` now starts with a post hoc line, and `mu_paired.json` has a `post_hoc` field. |
| F6 ("does not differ") | resolved | The text now says "not distinguishable" ("无法区分") for scripted Q1, for A4, and for the random_valid μ̂ difference. |
| F7 (ZH Brier) | resolved | ZH now names `qwen2.5-coder:7b`. |
| F8 (script checks) | resolved | The script now has the EVIDENCE/b1/COMPLETE gate, a 12-off-roots check, a check that usage trials equal manifest trials, and a check of μ̂ against the B1 analysis to 1e-12. It records Python and NumPy. A negative test with the scripted μ̂ shifted by 1e-9 in a scratch copy of the analysis stops with "STOP: scripted mu_hat differs from the B1 analysis", exit 1. The recorded `b1_analysis` sha256 `07cb62de…` equals the appendix's input. |
| F9 (random_valid) | resolved | Added: +0.00400 [−0.00050, 0.00802] (JSON +0.0040037 [−0.0005026, 0.0080229]). |
| F10 (terms) | resolved | The Notes list the terms to define. |

## Remaining findings

### m1. MINOR: the sweep stack list leaves out one R1-MAIN-PROPOSER (c) item
- **Location.** EN and ZH, the "Between the sweeps the contrast is proposer plus stack" list.
- **Evidence.** PLAN R1-MAIN-PROPOSER (c) lists "the CPU host of the in-campaign worker runs", and says all items go
  in every cross-proposer table. The sweep-2 authorization draft (`mac-s2-m1-redraft-20261116` @ `11db0f65`,
  "Disclosed differences") also lists it. The paragraph leaves it out.
- **Fix.**
  - Add "the CPU host of the in-campaign worker runs" (ZH "in-campaign worker run 的 CPU 主机").
  - Optionally add sm_52 against sm_89 to the GPU line.
  - Optionally write "default KV cache against q8_0", matching (c) and the authorization draft.

### m2. MINOR: the gap between the exam and the sweep-2 deployment is implicit
- **Location.** The scope sentence and the stack list.
- **Evidence.** R1-SWEEP-HOST-HTC requires the difference between the selection host (4090) and the deployment host
  (L40S) to be disclosed ("如实披露"). The authorization draft lists it separately: "From the selection exam … GPU 4090
  against L40S; a direct server against an HTCondor container with the frozen image; the llama-server binary".
  The paragraph names both hosts but never sets them side by side. That gap matters here, because the exam-measured Q1
  is used to predict sweep 2.
- **Fix.** Add one sentence, for example: "The pick was selected on a direct llama-server on the 4090 and will run in
  sweep 2 in an HTCondor container on L40S (R1-SWEEP-HOST-HTC)."

### m3. MINOR: the sweep-2 pins are planned, not fixed
- **Location.** Stack list: "harness `6adf385` against `a3fedbb`", "the container image".
- **Evidence.**
  - No PLAN row names `a3fedbb` as the sweep-2 pin. The authorization draft says so itself: the value comes from
    `HARNESS_PIN_C3` and the author's S2-M2 answer.
  - The image digest is still "proposed v1", and sweep 2 is not authorized.
  - The future tense covers most of this, but a reader of the list sees fixed values.
- **Fix.** Add "(as planned in the sweep-2 authorization)", or fill in the values from the committed authorization
  note once it exists.

## What I verified

1. **Provenance.**
   - HEAD is `228bc5d2`, parent `f10da83b`, four files changed.
   - `git status --porcelain` was empty after the reruns.
2. **Rerun.** With `--b1-analysis /tmp/pb/s2m5/b1_analysis.json` the script writes `/tmp/pb/rev_xprop/mu_r2.json` and
   `/tmp/pb/rev_xprop/mu_r2.md`. Both are byte-identical to the committed `mu_paired.{json,md}`. The μ̂ values and
   differences are unchanged from round 1.
3. **Consistency with the appendix (from round 1, still holding).**
   - The script uses the same seed, B, sorted ids, thinking-off filter and shared per-resample indices as the
     appendix.
   - The 4-row and 18-row bootstraps give identical μ̂ draws.
   - The per-row μ̂ CIs equal the appendix's.
4. **Numbers.**
   - Q1: 0.175 [0.129, 0.221]; B2 0.188 [0.142, 0.242]; qwen2.5-coder 0.545 [0.484, 0.608]; random_valid 0.579
     [0.524, 0.625]; scripted 0.149, not distinguishable.
   - Decomposition: 0.351 and 0.219.
   - Brier: 0.239 against 0.214.
   - μ̂: −0.00089, −0.00059, +0.00016.
   - Differences: −0.00030 [−0.00176, 0.00096], −0.00105 [−0.00497, 0.00296], +0.00400 [−0.00050, 0.00802].
   - Seeds: 9001+, 9101+, 9201+, 7001–7010.
   - Stack values (TITAN X against L40S, 8,192 against 32,768, q8_0, `--jinja` and the thinking flag,
     `cache_prompt: false`, 6adf385 against a3fedbb) agree with PLAN (c), R1-SWEEP-HOST-HTC, R1-SWEEP2-SETTINGS and the
     authorization draft.
   - EN and ZH agree item by item.
5. **No over-claiming.**
   - Q1 is called an upper bound and its components are named.
   - The sweep implication is hedged and rests on the comparison of lower bounds with the upper bound.
   - The winner's curse is stated, and no strength claim is made.
   - The μ̂ ordering is disclosed with paired post hoc intervals, as R1-EXAM-X7 (a) requires.
   - "Chosen by the declared rule" agrees with R1-MAIN-PROPOSER (a) and R1-EXAM-RULE-X5V2.

Scratch: `mu_r2.json`, `mu_r2.md`, `s/bad_analysis.json`, `s/bad.json` (the last was not written, because the run
stopped) under /tmp/pb/rev_xprop/.

---

# Review R3: cross-proposer disclosure paragraph (Paper B / R1), 16 Nov 2026

Reviewer: independent agent (did not write the work). Read-only.
Reviewed base: `bedba308b45995fc39a6b0820debc187bf2b4994` (one commit on `228bc5d2`). Worktree clean.

VERDICT: ACCEPT

`git diff 228bc5d2 HEAD` touches only `docs/r1/proposals/CROSS_PROPOSER_DISCLOSURE_DRAFT_20261116.md` (+20/−12).
The script, `mu_paired.{json,md}` and every number accepted in round 2 are unchanged.

## Round-2 minors: status

| R2 finding | Status | Evidence |
|---|---|---|
| m1 (stack list incomplete) | resolved | EN and ZH now include "the CPU host of the in-campaign worker runs" ("运行 campaign 内 worker 的 CPU 主机"), "TITAN X (sm_52) against L40S (sm_89)", "the default KV cache against q8_0" and "`cache_prompt` at the default against an explicit `false`". The list now covers every item of R1-MAIN-PROPOSER (c), as amended by R1-SWEEP-HOST-HTC (host) and R1-SWEEP2-SETTINGS (context 32,768). It also matches the "From sweep 1" list in the sweep-2 authorization draft (`mac-s2-m1-redraft-20261116` @ `11db0f65`). |
| m2 (exam vs deployment) | resolved | A new sentence in EN and ZH says the pick was selected on a direct llama-server on a 4090 and will run in an HTCondor container on an L40S (R1-SWEEP-HOST-HTC). This meets that row's "如实披露". |
| m3 (planned values) | resolved | The list now opens "As planned for sweep 2, which is not yet authorized" ("以下是 sweep 2 的计划值，sweep 2 尚未授权"). It says "the planned `a3fedbb`" and "digest still proposed" ("digest 仍为提议"). |

EN and ZH agree item by item in the changed passages.

## Optional nits (not required)

- **n1.** Two sentences in a row begin "The pick was selected on…": the new 4090/L40S sentence and the winner's-curse
  sentence. The author may merge them or rephrase one.
- **n2.** The authorization draft's "From the selection exam" list also names a difference in the llama-server
  binary: same commit `620d222`, different build. If the manuscript table gives the deployment differences in full,
  the author can add it there. The paragraph does not need it.

## What I verified

- **The diff.** It is limited to the draft doc, and both language versions change in parallel. I checked the new
  items against PLAN R1-MAIN-PROPOSER (c), R1-SWEEP-HOST-HTC and R1-SWEEP2-SETTINGS, and against the authorization
  draft's "Disclosed differences".
- **Earlier checks still hold.** The round-2 rerun reproduced `mu_paired.{json,md}` byte for byte, and that check is
  still valid, because neither the files nor their inputs changed in this commit.
- **Nothing reopened.** No earlier finding is reopened, and no BLOCKING or MAJOR finding remains.
