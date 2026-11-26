Reviewed base: 3fec3c50b386251101fdaedefe968c266f49dea4

# B1 appendix disclosure drafts — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 6. Branch `mac-appendix-20261114` from `gh/mac-b1-20261107` @ `1e5728f9` (the runbook's `origin/mac-b1-20261107`; the local `origin/` ref `3b7d5704` is an ancestor; both reviews found the base acceptable). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (four blocking: M4 classification, M19/M20 count source, truncation eligibility channel, PLAN-required disclosures in the combined paragraph).
- Round 2: **accepted** at `3fec3c50`.

Accepted commit (round 2, last): 3fec3c50b386251101fdaedefe968c266f49dea4

Round-2 notes, not blocking: "the `paper_commit` re-pin carries only this change" holds for executable B1 code (the span `f2eccd77`→`fb57c6a4` also touches docs, tests and host tools); a few lines exceed the wrap width.

The round texts are reproduced unchanged below.

---

# Independent review — Unit 6, B1 appendix disclosure drafts (round 1)

Reviewed commit: bf43178e27f1f21fa10a94f3438f3ce9b6e4b6b5

Branch `mac-appendix-20261114`, worktree `/tmp/pb/wt/appx`. The only change is
`docs/r1/reports/B1_APPENDIX_DISCLOSURES_DRAFT_20261114.md` (147 lines, new). Read-only review; scratch under
`/tmp/rev_u6` (removed). Runbook `69b3576b:docs/r1/prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md` §6; runbook review
interpretation 10 (sources from `ops-b1-restart-d-20261113` @ `7912b7ff`).

## Base

Parent is `1e5728f9`, which equals `gh/mac-b1-20261107` (tip). The runbook names `origin/mac-b1-20261107`; the local
`origin/` ref is the older bundle ref `3b7d5704`, an ancestor of `1e5728f9`. The two commits in between
(`6d6e8bba`, `1e5728f9`) add only docs (the `_d` handover status and its reviews), and the reviewed commit adds a single
new file. **Base acceptable.**

## What was checked and found correct

- Commits `fb57c6a4`, `4542360e` (paper_commit `f2eccd77` → `fb57c6a4`), `1334c616`, `62adc6a3` (`fb57c6a4` → `1334c616`),
  `3458b672`, `02a91494`, `2eda52e7` (`1334c616` → `3458b672`), `c5bf524b` (`3458b672` → `02a91494`): exist, subjects and
  re-pins match the PLAN rows.
- `x5_rule_v2` sha256 `53018aa7…16ad` = PLAN `R1-EXAM-RULE-X5V2` and `exam_b1_v2.json` `rule_sha256`.
- §1: X.3 criterion (12 pairs, 9001–9004, 2000 resamples, seed 20261026, lower bound ≤ 0, interval
  [0.4239, 0.5800]); STOP 8 Nov 01:19:49 UTC after 36 anchor roots; +0.0046 [−0.0006, +0.0089]; 120/242 = 0.4959;
  class D on H2 alone, H1 not supported, D7 PASS; `scripted_minus_random` / `descriptive_only` (present in
  `fb57c6a4:r1/scripts/exam_runner.py:228`); PLAN rows and dates 9 Nov / 11 Nov.
- §2: 11 Nov 13:51:09 UTC, `qwen36_27b` on, `openml_credit_approval` s9001 trial 13, 31,551 completion tokens, 32,768
  context, `--reasoning-budget 2048`, 64 roots, `LengthFinishReasonError` → `llm_call_failed` → worker exit; largest
  completion 2,178; rule text matches `R1-EXAM-B1-TRUNCATION-INVALID`.
- §3: 13 Nov 03:01:55 UTC, 89 roots, `olmo31_32b` / `openml_credit_approval__s9002` trial 020; 018/019 `invalid_config`;
  "turned into invalid trials" = M5–M9, M19 (after trial 1), M20 — matches diagnosis §3 and the PLAN row; the
  "still STOP" list (M10, M15 timeout, M16, M17, M18, M21) and M14 "executes" match diagnosis §3; the two §4.2a
  exceptions are stated; the 21 items are all accounted for.
- Check names in the placeholder (except `python_value_*`, see N6) match `CHECKS` in
  `7912b7ff:r1/exam/b1_proposal_precheck.py`; `proposal_journal.rejected_by_check` exists
  (`7912b7ff:r1/exam/b1_proposal_journal.py:71`, manifest field set in `r1/exam/campaign.py:295,319`).
- Combined paragraph: no `_d` value is presented as measured; all are ⟨…⟩.

## BLOCKING

**B1. M4 is misclassified as an "already invalid trial"** — `B1_APPENDIX_DISCLOSURES_DRAFT_20261114.md:103-104`.
Diagnosis §3 gives M4 as "revision, then skip"; in harness `a3fedbb` the exhausted D25 case sets `skip_trial` and writes
`_skipped_record(...)` with `decision=TrialDecision.SKIPPED` (`src/autoresearch/control_plane/campaign.py:1548-1552`,
`600-638`), not `failed_invalid`. It therefore does not count in `diagnostics.invalid` or the D28 invalid rate, and a
filler of "invalid trials by class" would misattribute it. In addition, the parenthesis "M3, M4 (left to the harness's
D25 loop)" reads as covering M3, which is a harness precondition failure (invalid), not a D25 case.
*Fix:* rename the group to "Already handled by the harness without a STOP, unchanged", and list "M1 (parse failure,
invalid), M2 (truncation, §2, invalid), M3 (unresolvable `param` / no `new_value`, invalid precondition), M4 (D25 inactive
key: revision, then skip — a skipped trial, not an invalid one), M11–M13 (invalid)".

**B2. M19/M20 counts are pointed at a field that does not contain them** — `:123-127`.
The placeholder says the table, including the columns "context overflow (M19), unencodable summary (M20)", is "read from
each root manifest's `proposal_journal.rejected_by_check` (same counts in `b1_proposals.jsonl`)". `rejected_by_check`
counts only journal rows with `check == 'rejected'`, i.e. the nine `check_model_output` codes
(`b1_proposal_journal.py:69-71`). A context-overflow or unencodable reply is an empty / parse-failed proposal, so its
journal row has `check: 'not_applicable'` (`b1_llm_truncation.py:252-266, 290-291`) and never appears in
`rejected_by_check`. Read as written, the M19/M20 columns would be filled with 0.
*Fix:* split the source: M5–M9 from `proposal_journal.rejected_by_check`; M19 and M20 from the journal rows' boolean
`context_overflow` / `unencodable_reply` (equivalently the `llm_call` event fields of the same names, or the per-root
`context_overflow` / `unencodable_reply` counts of `r1/scripts/b1_completion_usage.py:121-122`). Use the codes
`context_overflow` and `unencodable_reply` as the column names.

**B3. §2 "what it cannot affect" omits the eligibility channel of truncation** — `:74-78`, and `:142-143` in §4.
A truncated reply is recorded `failed_invalid` (`PROPOSAL_PRECONDITION_FAILED`; PLAN row: "a truncated trial counts under
`invalid` and `parse_failed`"), so it counts toward D28 criterion 3 (invalid rate < 30 %, thinking-off roots for v2
eligibility) exactly like a model-output rejection. §3 (`:119-121`) and §4 (iii) state this channel in bold for
rejections; §2 and §4 (ii) state only the valid-proposal rate and μ̂, which by contrast reads as "truncation cannot affect
eligibility". Truncation is mostly a thinking-on effect, but a thinking-off reply can also reach 16,384 tokens (e.g. a
repetition loop), so the channel is real.
*Fix:* in §2 add "Truncated trials count toward D28's invalid-trial rate (eligibility uses thinking-off roots), so
frequent truncation in thinking-off mode can make a candidate ineligible." In §4 (ii) add "and, like the rejections in
(iii), count toward the eligibility gate's invalid-trial rate". Add a ⟨thinking-off truncations per candidate⟩ field to
the §2 `_d` values.

**B4. The combined appendix paragraph drops disclosures the PLAN rows require** — `:134-147`.
- `R1-EXAM-B1-ANCHOR-R4-H2` (2): "the appendix gives the reason as the design of the check **and H2**, and discloses that
  the ranking quantity of `x5_rule_v2` (`pooled_audited_mean_proposal_increment`) is an incumbent-relative increment".
  §4 (i) gives only the design reason ("because the check compares two random proposers…") and says nothing about the
  ranking quantity, so the halves table appears without its reason. §1 (`:46-48`) has it; the paragraph offered as
  appendix text does not.
- `R1-EXAM-B1-TRUNCATION-INVALID` Disclosure: "…and whether the 2,048-token thinking budget took effect in this build".
  Missing from §4 (ii) and from its final placeholders.
- Same row: the cap was "fixed before the per-root usage of the stopped run was read". §4 (ii) gives only "a cap that no
  reply of the completed roots had reached", which without the order reads as a cap chosen from the data.
*Fix:* in (i) add, e.g., "…and because its statistic, like the ranking quantity of the pre-specified rule (the pooled
audited mean proposal increment), is an incumbent-relative increment, which the diagnosis found falling on one node; the
rule was kept unchanged, and we report first- vs second-half increments for every model (Table ⟨n⟩)". In (ii) add "fixed
before the stopped run's per-call usage was read" and "⟨whether the 2,048-token thinking budget took effect for every
thinking-on candidate⟩".

## NON-BLOCKING

**N1. Attribution of the anchor numbers** — `:32-33`. The values +0.0046 [−0.0006, +0.0089] and 120/242 follow the
citation of `B1_STOP_6835_20261108.md`, but that report states it "does not show the anchor values"; they are the
diagnosis's recomputation (D1, D7). *Fix:* "Recomputed in the diagnosis (D1, D7): …".

**N2. R4's original condition is paraphrased too loosely** — `:42`. "conditional on a class-D design verdict" hides that
R4 required class D **with H1 supported** and expressly excluded the H2-alone outcome that occurred (diagnosis summary:
"R4 under line A1: Not applicable"). *Fix:* "(conditional on class D with H1 supported; the observed H2-alone outcome was
not covered and went to the author)".

**N3. R4-H2 code commit not cited** — `:43`. The halves script and the R4-H2 changes are in `20fe72a6`
(11 Nov 02:21 CET), not in `fb57c6a4` / `4542360e`. *Fix:* add "R4-H2 changes and `b1_candidate_halves.py`: `20fe72a6`".

**N4. "does not change … pins"** — `:46` against `:43`, which lists the re-pin `4542360e` (paper_commit
`f2eccd77` → `fb57c6a4`). *Fix:* "model, server and harness pins" (the paper_commit re-pin carries only this change).

**N5. Undefined threshold in the §1 placeholder** — `:50-51`. "candidates whose second-half increment falls by more than
⟨…⟩ σ_joint" introduces a cut-off no PLAN row defines; picking it after reading `_d` would be a post-hoc criterion on a
table the PLAN declares descriptive. *Fix:* replace with "first- vs second-half table: Table ⟨n⟩", or fix and state the
value now as descriptive only.

**N6. Expand `python_value_*`** — `:126`: `python_value_too_long`, `python_value_not_literal`,
`python_value_not_finite_number` (the exact `CHECKS` codes).

**N7. "Three groups" with a fourth case** — `:98`, `:107-108`. M14 (executes) is neither of the three groups but is
appended to the "Still STOP" bullet. *Fix:* "four groups", with M14 as its own bullet ("Executes, unchanged; flagged for
the author").

**N8. Context overflow is absorbing** — `:119-121`. Diagnosis §4.2 notes that once a root overflows, the rest of its
budget becomes invalid trials. Worth one clause in the eligibility sentence ("a context overflow makes the rest of that
root's calls invalid").

**N9. "found no defect"** — `:137`. The diagnosis says no engineering defect was shown by the pre-declared checks (H4 not
supported). *Fix:* "found no implementation defect".

**N10. "restarted three times"** — `:134`. True only if `_d` (running at the time of writing) is the final run; the
status line already says "or its successor". *Fix:* make the count a placeholder or add "⟨if `_d` is the final run⟩".

## Verdict

Four BLOCKING findings: the M4 classification (B1), the M19/M20 placeholder source (B2), the missing eligibility channel
for truncation (B3), and PLAN-mandated disclosures missing from the combined paragraph (B4). All are small text fixes.

Verdict: changes requested

---

# Independent review — Unit 6, B1 appendix disclosure drafts (round 2)

Reviewed commit: 3fec3c50b386251101fdaedefe968c266f49dea4

Branch `mac-appendix-20261114`, worktree `/tmp/pb/wt/appx`. `3fec3c50` sits directly on the round-1 commit `bf43178e`
and changes only `docs/r1/reports/B1_APPENDIX_DISCLOSURES_DRAFT_20261114.md` (+54/−33). The base is unchanged
(`1e5728f9` = `gh/mac-b1-20261107`) and was accepted in round 1. Read-only review; scratch under `/tmp/rev_u6`, removed.
Sources are the same as in round 1 (`7912b7ff` PLAN, reports and code; `1e5728f9` STOP reports; harness `a3fedbb`).

## Round-1 findings: verification

| Finding | Status | Evidence |
|---|---|---|
| B1 M4 grouping | **Fixed** (`:110-113`) | The group is renamed "Already handled by the harness without a STOP". M4 is now "revision, then skip — a **skipped** trial", matching harness `campaign.py:1548-1552, 637` (`TrialDecision.SKIPPED`). M3 now has its own description (an invalid precondition failure). The M11–M13 descriptions match diagnosis §3. |
| B2 M19/M20 source | **Fixed** (`:134-141`) | M5–M9 come from `proposal_journal.rejected_by_check` (rows with `check: rejected`, `b1_proposal_journal.py:69-71`). M19/M20 come from the journal rows' `context_overflow` / `unencodable_reply` flags, whose rows carry `check: not_applicable` (`b1_llm_truncation.py:290-291`, journal row `:318-319`). The same fields sit on the proposer `llm_call` event payloads (`call.update(outcome)`, `:251`), and `b1_completion_usage.py:70,121-122` counts them from those payloads. All nine `CHECKS` codes are spelled exactly. |
| B3 truncation eligibility | **Fixed** (`:81-83`, `:87-88`, `:161-162`) | §2 now says truncated trials are `failed_invalid` and count toward D28's invalid rate (thinking-off roots), so they can make a candidate ineligible. §4 (ii) says the same. A placeholder for thinking-off truncations per candidate is added. |
| B4 PLAN-required disclosures in §4 | **Fixed** (`:152-163`) | (i) gives H2 (the fall, driven by one node) and the design reason. It now states that the statistic and the ranking quantity (`pooled_audited_mean_proposal_increment`) are both incumbent-relative increments, that the rule was kept, and that the halves table is reported. (ii) states that the cap was fixed before the usage was read, and has a placeholder for whether the 2,048-token thinking budget took effect. This meets the disclosure clauses of R4-H2 (2) and `R1-EXAM-B1-TRUNCATION-INVALID`. |
| N1 | Fixed (`:32-34`) | The numbers are now attributed to diagnosis D1/D7, and the STOP report is noted as not showing them. |
| N2 | Fixed (`:43-44`) | R4's condition is "class D with H1 supported", and the H2-alone outcome is noted as not covered. |
| N3 | Fixed (`:45-46`) | `20fe72a6` (11 Nov) added `r1/scripts/b1_candidate_halves.py` and its tests. Verified. |
| N4 | Fixed (`:49-50`) | The wording is now "model, server and harness pins", with the paper_commit re-pin named. See N-a below for a residual nuance. |
| N5 | Fixed (`:54-55`) | The threshold is gone: "descriptive, no threshold: Table ⟨n⟩". |
| N6 | Fixed (`:137-138`) | |
| N7 | Fixed (`:105`, `:118`) | Four groups, with M14 as its own group. The 21 items are all accounted for (7 + 7 + 6 + 1). |
| N8 | Fixed (`:131-132`) | Consistent with diagnosis §4.2 ("absorbing"). |
| N9 | Fixed (`:154`) | |
| N10 | Fixed (`:149`) | The restart count is now a placeholder. |

## New content checked

- `:116-117`: "a proposal that reaches the worker guard and fails it (now an internal inconsistency)" is still a STOP.
  This matches PLAN `R1-EXAM-B1-MODEL-OUTPUT-INVALID` (4) and diagnosis §4.1.
- The §4 paragraph presents no `_d` value as measured. Every new item (restart count, thinking-budget effect, tables)
  is in ⟨…⟩. Nothing in the added text overclaims what the changes cannot affect.
- No number, date, commit or path from round 1 has changed, and those verified in round 1 still hold.

## BLOCKING

None.

## NON-BLOCKING

**N-a. "the `paper_commit` re-pin carries only this change"** (`:49-50`). The span `f2eccd77..fb57c6a4` touches 87
files. Outside docs, tests and host tools, the only changes are `r1/scripts/exam_runner.py` (the R4 gate) and the
config line itself, and `4542360e`'s message states the scope as "among the protected exam paths". So the claim holds for
executable B1 code. *Optional:* "carries no other change to executable B1 code".

**N-b. Cosmetic.** `:43`, `:49`, `:83`, `:87`, `:116` and `:131` run past the file's wrap width. Rewrap if wanted.

## Verdict

All round-1 BLOCKING findings (B1–B4) and NON-BLOCKING findings (N1–N10) are fixed and verified against the sources.
No new BLOCKING issue.

Verdict: accepted

Accepted commit: 3fec3c50b386251101fdaedefe968c266f49dea4
