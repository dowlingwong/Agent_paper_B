# Independent review — B1 authorization draft (5 November 2026)

AI-assisted (Codex); fresh reviewer, independent of the draft author. Scope: the working-tree draft `docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261104.md` on `/private/tmp/paper-b-mac-20261104`, the proposed acceptance format in `reports/MAC_OVERNIGHT_QUESTIONS_20261105.md` Q1, integrated PLAN §10 and committed O1 report; no code acceptance, real inference, GPU, server access, or author decision. The checked-out integration HEAD was `c78215f`. The initial reviewed draft had SHA-256 `f20f23db24a0bcf431eeb212f1004c8c06421ea82cf25ce99b6905db18e367e9`.

## Round 1 — NOT ACCEPTED

1. **MAJOR — missing B1 anchor-reference prerequisite.** The B1 config at the M2 branch still has TODO values for `anchor_duplicate_reference` source, SHA, lower and upper; `exam_runner.anchor_gate` reads the bounds without validating the source hash. The draft omitted this unresolved B1 prerequisite. It must not imply the note is launch-ready until a protocol-authorized source and bounds are identified, bound and reviewed. No values are invented in this review.
2. **MAJOR — O1 report availability in the actual code checkout.** The O1 report is committed on the integration checkout and hashes to the proposed value, but is absent from `mac-b1-overnight-20261105` @ `6d24c21`. Requiring the author note to bind that report is operationally incomplete unless the eventual reviewed host checkout contains and verifies the same bytes.
3. **MINOR — stale M2 head and scope.** The phrase `current M2 head 75134796` was stale; later M2 code and containment commits exist. The overnight author instruction explicitly permits B1-scoped acceptance with B2 ranking stopped, so the precondition should state that scope rather than require the entire M2 unit accepted.
4. **MINOR — verifier integration qualification.** The introductory claim that `author_gate` checks `workers` applies to accepted verifier `f7ecf2c`, which was not yet integrated into the current B1 code/PLAN checkout. Distinguish its accepted-unit state from an already integrated launch path.

## Checks

- The author-selected `digits_mlp`, `openml_credit_approval`, `openml_ionosphere`, `llm_call_cap=80`, and `workers=20` match PLAN R1-EXAM-B1-DRAFT-VALUES and its labelled recorder consequences. The practical 20-worker resource headroom is expressly unmeasured in the draft.
- `t7h8` `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` and `t7j10` `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103` match PLAN and O1.
- `git show HEAD:docs/r1/reports/OPS_O1_20261104.md` on integration HEAD hashes to `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e` and equals the checked-out bytes. The author has not selected this acceptance-record format; Q1 identifies it as a proposal.
- The rule file at the B1 branch hashes to `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`, but is a draft until the author records R1-EXAM-RULE-X5V2. The machine-readable block has `approved: false`, so it is not an authorization.
- TASL-7 is the recorded B1/B2 host; P.3a remains paused during either phase, as PLAN states. The author has not authorized a B1 launch with this draft. Separate observer, entrypoint, full-suite and host qualifications remain.

## Same-reviewer recheck — ACCEPTED AS A DRAFT ONLY

Rechecked updated working-tree draft SHA-256 `21a19cea79e4da9577efb399635dfc5c18c3ed771471961fd74f9fc6d20a06b8` against the same PLAN and O1 sources. The preconditions now explicitly name B1-scoped acceptance, the unintegrated verifier, the need for identical O1 report bytes in the actual reviewed checkout, the missing `anchor_duplicate_reference` source/hash/bounds and source digest verification, and the still-present entry/observer STOPs. The stale `75134796` head claim is removed. The record format remains labelled proposed, the selected values and hashes are unchanged, `approved` remains false, and the paper pin remains TODO.

**Verdict:** ACCEPTED only as the reviewable proposed B1 note and acceptance-record format. This is not acceptance of M2, the verifier integration, the unresolved anchor source, a frozen rule, an author decision, an operator handoff or any run. The author's selection of the acceptance-record format and all stated preconditions remain necessary.
