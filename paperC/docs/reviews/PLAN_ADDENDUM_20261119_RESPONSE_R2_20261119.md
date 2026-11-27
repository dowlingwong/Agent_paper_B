# Response to review round 2 of the Paper C addendum of 19 Nov 2026

**AI-assisted (Claude, chat session; the recorder).** Review: `PLAN_ADDENDUM_20261119_REVIEW_R2_20261119.md` (NOT ACCEPTED, 1 MAJOR, 8 MINOR).

**A correction to the round-1 request.** The round-1 request summarised the author's restore decision as "a replay check gating SPT-3 data". That gate was the recorder's own first draft. What the author approved in the chat on 19 Nov was: restore the positions of the random streams when a fork restores a state, and compare a run continued "as is" from the restored state with the original run. §B and row R1-PAPERC-RESTORE now record exactly that as the author's decision, and mark everything beyond it [recorder] (§G12), including the gate on fork data.

| # | Finding | Fix |
|---|---|---|
| 1 | Restore-gate rules unmarked | §B: an "Author's decision" paragraph with the approved wording; items 2, 4–7, the timing and the gate marked [recorder]; new §G12. Row RESTORE: the author's decision first, then the recorder's definition marked [记录者，addendum §G12] |
| 2 | Other unmarked additions | "a passed go/no-go is not evidence of headroom" marked [recorder]/[记录者] and added to G11. The merge instruction is marked [recorder: housekeeping] in §F and moved out of row HARNESS-PIN into a recorder's note under the table |
| 3 | g, h clash with plan §7.1 | A.0 states that g and h are declared constants, distinct from N1's and N2's tuned (g, h), written g_N1 and h_N1 where both appear; row RELEVANCE says the same |
| 4 | Regret data | A.2 "Data" and row RELEVANCE: decision regret uses C1's frozen node value |
| 5 | §G defaults and deadlines | §G gets a "Decide before" column; G4 default = plan §11.2 (both nodes, Holm over 2), with the recommendation kept separate; G6 default = N1 and N0, r = 2; G7 states that g and h have no default and are declared in the SPT-1 pre-declaration; new G13 (checks on excluded epochs or nodes do not open the gate, default no). The PLAN preamble says open points must be settled before the named pre-declaration |
| 6 | Empty-cluster default | A.5, G11 and row OPE-SUPPORT: empty only if neither the behaviour data nor any candidate's development campaigns visit the cluster; otherwise "insufficient data" |
| 7 | Truncation list | §C and row ESTIMAND-GUARDS restore "parse failure beyond retry where the pinned harness does not charge it as an invalid trial" |
| 8 | Wording | "possibly even where a real channel is about as strong as …"; "Track S's noise unit"; N1's tuning campaigns added to the recomputed SPT-1 cost |
