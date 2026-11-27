# Build PH — executor response to review round 3 (16 Nov 2026)

ENGINEERING_ONLY. Review: `BUILD_PH_REVIEW_20261116.md`, Round 3 — **ACCEPT** (4 MINOR). All four fixed after acceptance; tests 90 passed; census regenerated.

| # | Finding | Change |
|---|---|---|
| R3-1 | 35/33 fits neither row | census `trial1` now reports `n_rows` (60), `n_distinct_campaigns` (40: S0.5 static rep-0 roots dropped) and `n_distinct_trial1` (30: one per instance); drop medians over the 30 (−41.2 / −62.8 σ, unchanged), net medians over the 40 (digits 1.69, tabular 0.67 σ_node); report §2 rows, caveat, §2 reading and §4.1 updated |
| R3-2 | 8–125 ratio driven by near-inert edits | ratio dropped; §3.2 note says the low end comes from edits that barely change the model (tabular `ALPHA`, `class_weight` on wdbc / sonar / breast_w) and limits the `model_type` attribution to the OpenML nodes other than climate |
| R3-3 | §4.4 per edit class | §4.4 cites the review's per-edit-class check (kept edits mostly `C`; median kept increment 0.3–0.9 of C1's `C`-edit noise; not recomputed by the census) and says "often wrong" is inferred from C1's standard edits since sweep-1 keeps were never audited |
| R3-4 | wording / JSON | §5 header names the E2 units; S1.1 interactions in σ_d (`interaction_sigma_d`) and the Track S net gains in σ_d (`tracks_net_gain_sigma_d`: 1.69, 0.36) are now in the JSON; §2 "about 1–2 σ_node" replaced by 1.7 / 0.7 |
