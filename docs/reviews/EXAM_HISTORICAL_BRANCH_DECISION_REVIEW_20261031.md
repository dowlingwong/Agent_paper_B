# Independent review: historical prompt branch decision

31 October 2026. Reviewed commit `168a674a4cd96902cfbc9b45cd7526a1ed1d6795` in `/private/tmp/paper-b-coordinator-20261031`. This review is limited to the decision record and its consistency with the retained exposure review. It contains no prompt text. No model task, freeze, or push was performed.

## Verdict: PASS for the scoped decision record

The author explicitly decided to include the historical verify/continue branches in the permitted historical source range and to disclose them. PLAN §10, `R1-EXAM-PROMPT-HISTORICAL-BRANCHES` (`docs/r1/PLAN.md:663`), records that exception for the historical rerun-2 branch manager calls and requires disclosure. It preserves the prohibition on use by other exam candidates and subsequent exam evaluation, and preserves the requirement that selection did not use exam-model output as an independently verifiable gate. The earlier historical source manager and seed conditions remain in `docs/r1/PLAN.md:661-662`.

The recorded 21 of 50 contexts and 62 distinct later calls agree with the independent exposure review: 32 continue and 30 verify records, all with positive completion tokens and start timestamps later than the corresponding source-root call (`docs/r1/reviews/EXAM_PROMPT_EXPOSURE_REVIEW_20261031.md:18-27`). This is a review of the consistency of the decision record with that report, not an independent recomputation of the retained source records.

## Gates and limits that remain

- Other candidate exposure and global selection independence remain **NOT CHECKABLE** under the bounded evidence (`docs/r1/reviews/EXAM_PROMPT_EXPOSURE_REVIEW_20261031.md:9,38-40`). The exception does not establish absence of unlogged or subsequent exam use.
- The prompt set remains **UNFROZEN**; Stage A and B1/B2 remain **BLOCK** under the conditions recorded in `docs/r1/STATUS.md:8-9`. This decision is not a freeze or execution authorization.
- The exposure review's original STOP and request for author interpretation (`docs/r1/reviews/EXAM_PROMPT_EXPOSURE_REVIEW_20261031.md:5-7`) record the state before the present author decision. The decision resolves that specific interpretation, not the separate unresolved evidence gates.
