# Independent review — 7 November overnight questions

AI-assisted (Codex). **ACCEPTED in documentary scope only.** Reviewed the uncommitted `docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261107.md` in `/private/tmp/paper-b-mac-20261104`, SHA-256 `5ba68f078c2cc189f3cec59bd98cde95c65385e0961627c259bcabe7679d9902`, against integration checkout `9ee26f2`, the supplied author prompt and the independently reviewed TASL-7 census. This review does not approve a launch, author note, host mutation, M4 start or a new author decision.

The prompt §2 Worker C explicitly instructs the agent to hold the non-shared M4 pieces and add a question if it judges that starting them conflicts with the Mac runbook. The current runbook §2 and §M4 place M4 after M3 acceptance. The question accurately states this interpretation and presents the hold as a recommendation, not as an author ruling; it does not turn a possible future amendment into approval for DTQ or another phase.

The host item accurately reflects the 00:00 UTC census: no listed GPU compute app and a `trks_watch` session, with other-user agent processes visible but their ownership of the host not established. The census is a point-in-time observation, not proof of exclusivity. The question recommends holding execution, preserves existing processes and does not infer that all visible agents own the host.

The 7 November PLAN rows and prompt record Q1, the fixed Q2 rule and the conditional Q0 rule/note approval; the question file does not repeat these as unanswered. The Q0 row still depends on the anchor reference, exact final checkout and all reviewed launch gates. Its reference to prior Q3–Q24 expressly excludes any item subsequently resolved by an author row, rather than treating earlier answers as new approvals.

Scope limit: independently checked the wording and cited documents, not any actual host, dynamic process state, Q2 computation or completeness of every future question. No server, model, GPU, experiment or author decision was used or made in this review.

## Recheck — proposed B1 note-order clarification

**ACCEPTED as a question only.** Rechecked the question file at SHA-256 `4a2ae95625665581ff213386be87b99a3473bceb685a236cf631adb87b15b7d0`, including the added B1 approved-note-order item. Prompt §0.3 states both that `approved: true` is set only when every condition holds and that conditions 3 and 5 already require a clean committed approved note and a passing real author gate. At B1 checkout `8f6fda783efdbb74f0a5187fb14f80f74e7bce3b`, `runtime.py:300–309` refuses a non-approved note, while `runtime.py:277–287` binds committed clean HEAD bytes. Thus the question accurately identifies a cycle on that literal reading; the author's intention to launch does not itself specify which ordering requirement to amend.

Option A and the paste-ready line are explicitly proposed responses for the author, not author words or permission to set the note. The recommendation preserves `approved: false` until clarification and requires the actual final-HEAD review, author gate, host preflight and full handover before any launch. Other STOPs remain independently applicable. No host access, model, GPU, test execution, author note mutation or phase approval was made for this recheck.
