# Build PH — executor response to review round 1 (16 Nov 2026)

ENGINEERING_ONLY. Executor: chat-session Claude. Review: `BUILD_PH_REVIEW_20261116.md` (round 1, NOT ACCEPTED, 4 MAJOR / 8 MINOR). Tests: 89 passed. `python -m paperc.census` regenerates the committed JSON (schema `paperc_census/v2`). The report's §4–§6 were rewritten; several round-1 conclusions are withdrawn.

| # | Finding | Change |
|---|---|---|
| 1 | sources not read | the census now reads the C1 D28 composite (paired sd, sign-flip rate, campaign_wrong, decision regret), the C3 audit pilot (random rows), the three E1b analyses and the three S1.1 factorials; report §3.2–§3.3 and §4 reconcile them |
| 2 | trial-1 artefact | new `trial1` block (Track S: drop and net gain over all 120 S0.4+S0.5 campaigns; sweep: trial-1 metric vs C1 default and recorded gain after trial 1); report §2 comes first and states that keep quality is conditional on it; guarded first acceptance added as a channel candidate and confound (§6.2b) |
| 3 | E1 contradiction and ∞ artefact | node-level V\* computed under 1 σ_d and under C1's paired noise; "misspecified" when the assumed noise is at least the observed sd; `inf` written as "inf"; E1 criterion is a two-sided band 0.3–3; the "none passes" sentence is withdrawn (OpenML nodes are inside the band under paired noise, with tiny stakes) |
| 4 | unit and stakes | E2 near-margin shares in the node's own noise unit (C1 paired sd for sweep 1, robust comparison noise for Track S); stakes columns (kept increment medians, keeps per campaign, campaigns without keeps, C1 decision regret); "draw on noise" withdrawn; no confirmatory node choice until the audits of §6.2 exist |
| 5 | keep rules differ | stated in §1; `logged_action_mismatches` asserts S0.4 actions == Δ̂ > 0 (0 on both nodes, tested); the S0.5-rule sensitivity is cited from the review, not recomputed |
| 6 | missed-keep magnitudes | tie count and audited median / max of the misses reported |
| 7 | winner's curse | per-keep and per-campaign means with se, correlation with the number of keeps, the measure defined, reading "no winner's curse detected; underpowered" |
| 8 | memory modes and duplicates | per-mode table (duplicates, comparisons, keeps per campaign, campaigns without keeps); duplicate definition named (patch hash vs Track S configuration level); the "gate cannot exploit" claim corrected (the rule layer already skips duplicates; the cost is in calls and slots) |
| 9 | budget | shadow price stated as undefined; W described as the price of verify runs |
| 10 | inputs table | §7 lists every file with its git object id (ledger directories as trees); the TASL-2 / TASL-7 host mix is noted |
| 11 | tests and structure | fixture tests for `parse_sweep_campaign`, `join_keeps` (including a keep without a row), `logged_action_mismatches`, `c1_paired`, `node_level_v_star` and inf encoding; the P1-adapter deviation is recorded in the module docstring and BUILD_STATUS (B5 loader) |
| 12 | precision | degenerate robust sd labelled; wdbc's `proposal_precondition_failed` named; the D21 selection of the OpenML nodes stated (§4.7) |
