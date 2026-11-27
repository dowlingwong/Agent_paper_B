# local/20261127-08 — D.3 revision 4 binding preparation (STOP before final review)

for: coordinator

- Base `e153df24ee3435bbe0b2fa994297b15250550c30`; draft-only branch `mac-d3-r4-binding-prep-20261127` @ `f16c6677b175913c2c15c6f899d256b563fe64bd`. Draft SHA-256 `8423d507a328457d78f52ae5d79225fbb48bed0cbcf899254626b3d99c886dc8`.
- The reviewed verify-seed checker is on `main`. The draft now names harness `9bb416805175149eb87b71f28d77530572aa4bce` and checker `e44d966f201d15aa627d5399ca2fe7ada0e15958` (SHA-256 `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2`). The actual `python -m r1.c3.d3_verify_namespaces` result is **PASS**: 160 seeds in 20010–20801 for `vary`, `r=2` and one-based indexes 1–80.
- `test_d3_analysis.py` plus `test_d3_verify_namespaces.py` returned 60 passed and 18 subtests passed. The analysis script and test hashes still match §9/§14. The existing script implements the selected rule settings, Holm families, wording cases, `last_improving_run` field and HPO proposal cap. This draft does not change those files. The verify-seed unit had independent tier-E acceptance. **Final step-(5) review has not started** for the declaration because required fields are still pending.

**Dependencies.** G2 fitter code is merged but the reviewed A1/A2/LADDER constants artifact and exact SHA-256 have not been reported. See the dev-only command in `reports/20261127-06-d3-g2-constants.md`. The HPO-REF item still needs the pinned SMAC3 version and environment after G1/G6, and §7.5(e) still needs the exact gate report path/key binding. Item 16 remains open under R1-D3-PREDECL-R4; the coordinator fills `signed_by` and `frozen_utc` after the review. Complete these bindings, obtain the review of the exact document/script/tests and the diff-only re-check, then the coordinator freezes and publishes it. No job submission is authorized by this draft.

Decided alone: delivered the available reviewed pin as a draft while leaving the remaining fields pending. No signed file or real analysis input was changed or opened.
