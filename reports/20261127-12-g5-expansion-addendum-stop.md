# local/20261126-12 — G.5 expansion addendum template ready; switch pending

for: coordinator

- Base `e153df24ee3435bbe0b2fa994297b15250550c30`. Draft template branch `mac-g5-expansion-addendum-prep-20261127` @ `4fe8ac1f11b7667fdd02ee3d29e4d89545de6eed`.
- `docs/r1/proposals/G5_EXPANSION_ADDENDUM_TEMPLATE_20261127.md`, SHA-256 `c9e13cf4e16a8a7b6d7a4ccd8143942a4d77aef407d60ea11396232898a917ff`, **ACCEPTED for draft-template handoff** by an independent reviewer. The review and wording refinement are in `docs/r1/reviews/G5_EXPANSION_ADDENDUM_TEMPLATE_REVIEW_20261127.md`. Verified the published expansion G.1b note and spec bindings and staged split digest. `git diff --check` passed. Draft-only change.
- S9 is signed. The template keeps the future addendum `approved: false` and requires the matching published per-node G.1b PASS, exact launch code, split, node configuration, environment and host/lease bindings. MLGym joins under its own suite. 1GC is reported separately by node and stays outside SFT, arms and gate. The projection is a GPU-hour report under R1-NO-TIMEOUT (3), with no date requirement.

**Pending.** The switch and per-node addendum are not delivered. The current G.5 switch accepts only the eight-node note and fixed spec. The coordinator must first land the reviewed S9 split implementation and settle the shared launch-code binding with the main G.5 note. The exact switch, spec entry and label routing need tier-E tests, full suite and review. The first node note additionally needs its published determinism PASS and assembly/noise bindings. Latest compute receipt has ETTh1 complete and sealed, with publication and the rest of the expansion assembly pending; see `coord/compute` @ `372d2099`. The main G.5 note still awaits P11, `paper.commit` and final review.

Decided alone: prepared the coordinator's fill-in template from the published expansion note and spec while the launch bindings are pending. No real labels or evaluation files were opened and no job was submitted.
