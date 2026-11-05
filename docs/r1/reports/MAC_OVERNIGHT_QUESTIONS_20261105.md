# Overnight author questions — 5 November 2026

AI-assisted (Codex). Draft only: no row or option below is an author decision or authorization. Ordered by the work it would unblock. This is a living list; items are updated as the independent reviews proceed.

## Q1 — B1 amendment acceptance record

**Context.** B1 binds the two Stage A table SHA-256 values and an amendment-acceptance record. The O1 report contains both accepted table digests and is already on the integration branch. Proposed format: `stage_a_amendment_acceptance_sha256` is the SHA-256 of the exact committed bytes of `docs/r1/reports/OPS_O1_20261104.md`, currently `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`; the path is bound too. If those bytes are corrected, a new digest and re-review are required.

**Options.** (A) Use those exact report bytes and digest. (B) Name a different committed acceptance record and digest.

**Recommendation.** A, subject to the independent B1 review and verification of the file at the operator's checkout.

**Paste-ready answer.** `B1 acceptance record: use OPS_O1_20261104.md sha256 0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e.`

## Q2 — B1 anchor duplicate reference

**Context.** The B1 config requires `anchor_duplicate_reference` with source, SHA and bounds, but all four are TODO and the existing anchor gate does not verify the source digest. The applicable reference and whether its bounds can be fixed from an existing committed source have not yet been established.

**Options.** (A) Author names a committed reference and fixed bounds after the Mac agent identifies the evidence. (B) Author specifies a different reference and bounds. (C) Defer B1 pending a reference.

**Recommendation.** A if a protocol-authorized, independently reviewable source exists; otherwise C. Do not invent values from a convenient pilot.

**Paste-ready answer.** `B1 anchor duplicate reference: use <committed path and SHA256>, lower <value>, upper <value>.`

## Q3 — Stronger provenance (optional)

**Context.** The requested minimum checks committed HEAD, a clean tree, dated PLAN §10 decision row, and bound note/file hashes. A repository writer could create a false row or note; independent review and the author's own instruction mitigate this as process, not cryptography.

**Options.** (A) Use the reviewed minimum and process boundary. (B) Add a separate signed or independently authenticated published authority root before future phases.

**Recommendation.** A for the present B1 verifier; consider B for later work. This optional stronger scheme does not block B1 under the overnight instruction.

**Paste-ready answer.** `B1 uses the reviewed committed-HEAD verifier and independent review; consider signed provenance separately.`

## Q4 — Test exceptions, only after classification and review

**Context.** The latest Mac full suite had 39 historical failure IDs; some touch B1 or shared safety paths and cannot be treated as exceptions merely because they predate M2. The independent classification and any B1 fixes are in progress.

**Options.** (A) Review an exact, evidence-backed list of non-B1 exceptions after the B1-path failures are resolved. (B) Require all tests to pass.

**Recommendation.** A only for the independently reviewed outside-B1/environment cases, with unresolved cases excluded.

**Paste-ready answer.** `I accept the explicitly listed non-B1 test exceptions in <reviewed report and commit>; B1-path failures remain blocking.`

## Q5 — Remaining previously asked packet items

**Context.** The remaining (j) questions on T0-held-out analysis, heavy-tail handling, Ada/Track S floor, MLAgentBench/1GC and container checks were presented separately; no response was observed at the start of this overnight work. They do not determine the B1 rule or authorization.

**Options.** Answer each existing question; defer until its required census; or specify alternatives.

**Recommendation.** Decide each at the relevant evidence gate; no answer is inferred from silence.

**Paste-ready answer.** `For item <j-number>: <decision>.`

## Working blockers (not author decisions)

- **B1 committed-HEAD verifier, round 3 not accepted.** A mixed space/tab indentation expands to a Markdown code block but can be read as a table row; the parser also accepts a standalone pipe line without a Markdown table header and separator. Owner: Mac-local code editor; unblock by strict Markdown table parsing, mixed-indentation and malformed-table regression tests, then same-reviewer recheck. Estimated local effort: 30–60 minutes; return to this after the next unit, per the three-round time box. The current checkout is uncommitted at `/private/tmp/paper-b-overnight-b1-20261105`; B1 entry STOP remains. This does not ask the author to decide the technical fix.
- **B1 observer execution.** The pinned `a3fedbb` harness catches observer `Exception` and proceeds, while B1's observer currently requires a Stage-A-only context; root manifest does not bind the durable observer journal. Owner: Mac-local code editor and independent reviewer; unblock by a B1-scoped observer execution path that propagates STOP immediately, records/verifies every cache-false request and binds the observer journal, with actual pinned-harness fake-server integration tests. Estimate: 2–4 hours; after three review rounds or two hours without acceptance, report and switch tasks. B2 remains stopped.
