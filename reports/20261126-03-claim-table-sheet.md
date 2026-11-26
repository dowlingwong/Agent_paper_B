# writer/20261126-03 — revised outline and claim-to-table sheet: delivered, review accepted with minor, corrected

Task: `writer/20261126-03` (runbook §2 order 1, §3). Tier S. AI-assisted (Claude, writer).
Base: `main` `54082a05`, on top of the restructure branch `writer-20261126-01-manuscript-restructure` @ `6b72e27c`
(the sheet names that manuscript's tables and macros, so it merges after or with it).

## Result in five lines

1. One sheet, `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md`: the line from question to claim; the revised
   outline with draft pages and targets; every claim with its contrast, table or figure, evidence level, placeholder
   macros and the step of `canon/PAPER_B_PLAN.md` §4 that fills them; what each arm contrast identifies; the items for
   the author; the items for the design agent and revision 4 of the D.3 pre-declaration.
2. It takes no figure from an unreleased result. The only numbers are committed facts with a source (3,274 of 4,999
   duplicates in sweep 1; 126 of 180 proposals run in the T1 pilot), which the reviewer checked against their sources.
3. One fresh review: **ACCEPT WITH MINOR**, no MAJOR; 18 MINOR and 6 notes. One correction round applied all of them.
4. The review found three points the sheet had missed and that need the author (below, items 2a, 2b and 10).
5. Proposal only. It decides nothing.

## Branch and hashes

| What | Value |
|---|---|
| Branch | `writer-20261126-03-claim-table-sheet` |
| Tip | `a9a9f6bb` (sheet `3a402490` → review `ba18f1b8`, committed unchanged → correction round `a9a9f6bb`) |
| Sheet sha256 | `58d335903e46a87a2dc3ed6440951a9c4d8364ead807ed8b3e35d6a53bb21020` |
| Review | `docs/r1/reviews/PAPER_B_CLAIM_TABLE_SHEET_REVIEW_20261126.md`, sha256 `d4d90881310a7ffed75d0cb4e04beab1e6adf78f35b75e4c7c96c88e8e5607f9` |
| Tests | documentation only; no code, so no `r1/tests` run |

The review covered the sheet at `3a402490`. The correction round is not re-reviewed (tier S: a second round only after
a MAJOR finding).

## Claims and readings the author must confirm (sheet §5)

1. What "A2 > A0" and "A3 or A5 > A2" mean in the five declared readings. Draft: the Holm rejection in the favourable
   direction of A2 − A0 (D.3a family) and of A3 − A2 or A5 − A2 (D.3b family). Recommended home: revision 4.
2. The fifth reading: the sentence "Not an ICML submission in the present form" stays out of the paper text.
2a. **New.** A gain that comes from the rule layer alone (A0R − A0 rejected, A2 − A0R not). Readings three and four
   would then credit the one-step rule with a de-duplication gain. Recommended: declare the wording in revision 4.
2b. **New.** A statistical STOP of the gate has no row in the readings and no drafted text.
3. Contribution order and wording in the introduction. 4. The abstract and the title (four options; recommended:
   "Which Control Decisions Pay? A Matched-Budget Decomposition of a Governed Autoresearch Loop").
5. The theory section keeps two main-text statements; the rest moved to the appendix. 6. Proof-status wording.
7. Offline–online agreement covers A2, A3, A5 (A0R and the reference rules have no offline read).
8. Whether the pre-declaration states what difference D.3 can detect. 9. Wording of the incidental-output disclosure.
10. Committed facts quoted, and **new:** the two figures from other papers in the introduction (49.9 %, 2.7×) are not
   yet checked against the PDFs (R1-C1-POSITION).

## Decided alone (level 0)

The layout of the sheet; basing the branch on the restructure branch; applying every MINOR finding.

## What other roles need to do

- **Coordinator:** merge with or after `writer/20261126-01`. Pass sheet §6 to the owner of `local/20261126-03`
  (D.3 pre-declaration revision 4): the two contrast families and their multiplicity, the rule for items 1 and 2a,
  the rule-layer setting of FIXR3, EGATE and LADDER, charging of repeated attempts, the detectable difference.
- **Design agent:** check §3 and §4 (claims, estimands, contrasts). No design handoff existed when the sheet was written.
- **Author:** the items above, as one decision sheet when the coordinator prepares it.

## Next

`writer/20261126-01` (+02): pushed at `6b72e27c`, its independent review is running; report follows.

## Update after the restructure's review

The sheet branch now carries the corrected manuscript: tip `78886f11` (merge of the restructure branch at `6138b54f`,
then one edit of the sheet's state lines and of item 2a). Sheet sha256
`e969bea07414ce2a68fe655e4ef8922becd559c362b98f5462c84de91aa2305b`. The table in "Branch and hashes" gives the values at `a9a9f6bb`.
