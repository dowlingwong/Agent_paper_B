# Overnight author questions — 5 November 2026

AI-assisted (Codex). Draft only: no row or option below is an author decision or authorization. Ordered by the work it would unblock. This is a living list; items are updated as the independent reviews proceed.

## Q1 — B1 amendment acceptance record

**Context.** B1 binds the two Stage A table SHA-256 values and an amendment-acceptance record. The O1 report contains both accepted table digests and is already on the integration branch. Proposed format: `stage_a_amendment_acceptance_sha256` is the SHA-256 of the exact committed bytes of `docs/r1/reports/OPS_O1_20261104.md`, currently `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`; the path is bound too. If those bytes are corrected, a new digest and re-review are required.

**Options.** (A) Use those exact report bytes and digest. (B) Name a different committed acceptance record and digest.

**Recommendation.** A, subject to the independent B1 review and verification of the file at the operator's checkout.

**Paste-ready answer.** `B1 acceptance record: use OPS_O1_20261104.md sha256 0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e.`

## Q2 — B1 anchor duplicate reference

**Context.** The B1 config requires `anchor_duplicate_reference` with source, SHA and bounds, but all four are TODO and the reviewed B1 verifier now requires the source SHA and numerical bounds to match a JSON document with `lower` and `upper` fields. The applicable pilot source and derivation of the bounds have not yet been established; a matching JSON file alone does not prove pilot provenance. The existing `docs/r1/reports/DUPLICATE_RATE_PILOT_20261022.md` explicitly reports no confidence intervals, mixes different node/memory strata, and defines duplicates separately from no-ops. B1 counts `active_config_seen_before` among evaluated novelty events; its denominator and duplicate definition must be reconciled with the pilot before selecting a comparable CI.

**Options.** (A) Author names a committed reference and fixed bounds after the Mac agent identifies the evidence. (B) Author specifies a different reference and bounds. (C) Defer B1 pending a reference.

**Recommendation.** A if a protocol-authorized, independently reviewable source exists; otherwise C. Do not invent values from a convenient pilot.

**Paste-ready answer.** `B1 anchor duplicate reference: use JSON <path> sha256 <SHA256>, lower <value>, upper <value>, derived from <pilot evidence and method>.`

## Q3 — Stronger provenance (optional)

**Context.** The requested minimum checks committed HEAD, a clean tree, dated PLAN §10 decision row, and bound note/file hashes. A repository writer could create a false row or note; independent review and the author's own instruction mitigate this as process, not cryptography.

**Options.** (A) Use the reviewed minimum and process boundary. (B) Add a separate signed or independently authenticated published authority root before future phases.

**Recommendation.** A for the present B1 verifier; consider B for later work. This optional stronger scheme does not block B1 under the overnight instruction.

**Paste-ready answer.** `B1 uses the reviewed committed-HEAD verifier and independent review; consider signed provenance separately.`

## Q4 — Test exceptions, only after classification and review

**Context.** The latest Mac full suite had 39 historical failure IDs; some touch B1 or shared safety paths and cannot be treated as exceptions merely because they predate M2. The independent classification identifies 21 pre-existing non-B1 cases and 3 environment cases; 14 B1 cases and one unresolved nested B1 case are excluded from exceptions. Twelve B1 fake-server cases have an independently accepted fixture fix; the real-worker model test remains unrun under the no-model instruction, and two other B1 cases need resolution.

**Options.** (A) Review an exact, evidence-backed list of non-B1 exceptions after the B1-path failures are resolved. (B) Require all tests to pass.

**Recommendation.** A only for the independently reviewed outside-B1/environment cases, with unresolved cases excluded.

**Paste-ready answer.** `I accept the explicitly listed non-B1 test exceptions in <reviewed report and commit>; B1-path failures remain blocking.`

## Q5 — T1 divergence rule: denominator and timing

**Context.** The author chose `设 20% STOP` in response to a question specifying a STOP when divergence is **above** 20%. The exact counted proposals, handling of missing outcomes and evaluation time were not specified.

**Options.** (A) Per node, count distinct completed label proposals with an observed valid outcome; numerator is proposals with at least one declared divergence; STOP immediately once more than 20% are divergent, reporting count and denominator; missing/ambiguous outcomes separately STOP. (B) Specify a different denominator, timing or minimum sample size.

**Recommendation.** A as an operational clarification, subject to Track G design and independent review; do not infer a minimum sample size. Only the author may move a stopped node to T2.

**Paste-ready answer.** `Divergence: use option A, strictly greater than 20%, with missing outcomes STOP; T2 requires my decision.`

## Q6 — T0 in leave-one-suite-out

**Context.** T0 is the controlled CPU testbed; the primary generalisation question concerns held-out real benchmark suites. Whether T0 also gets its own held-out fold was left open.

**Options.** (A) Keep T0 out of the primary held-out suites and report a separate T0-held-out fold as secondary. (B) Include T0 in the primary folds. (C) Omit the extra fold.

**Recommendation.** A, declared before reading test results.

**Paste-ready answer.** `LOSO T0: option A, separate secondary fold.`

## Q7 — Heavy-tailed noise and Student-t soft labels

**Context.** A 10-seed noise floor is too small to treat an arbitrary excess-kurtosis threshold as a measured law; the proposed threshold >3 and degrees of freedom 5 were agent suggestions, not author decisions.

**Options.** (A) After G.0, declare affected nodes and degrees of freedom in G.3 before labels are built, reporting per-node kurtosis and its uncertainty. (B) Predeclare a numerical criterion and fixed degrees of freedom. (C) Specify another method.

**Recommendation.** A; choose degrees of freedom before labels and analysis rather than retrofitting them to outcomes.

**Paste-ready answer.** `Heavy tails: option A; I will set affected nodes and degrees of freedom at G.3 before label construction.`

## Q8 — A6 probe beyond its existing P.3a use

**Context.** The existing P.3a decision already uses A6's mean absolute RPS change >0.01 for a rerun decision. Its other uses remain unspecified.

**Options.** (A) Treat other A6 results as descriptive. (B) State an additional predeclared decision rule.

**Recommendation.** A; it does not alter the existing P.3a criterion.

**Paste-ready answer.** `A6: descriptive outside the existing P.3a rule.`

## Q9 — Ada fallback and Track S GPU noise floors

**Context.** T1 currently belongs to HoreKa; Ada is a fallback, and Track S GPU nodes need an appropriate noise floor if their analyses use one.

**Options.** (A) Hold Ada G.0 raw-cost work until the HoreKa scan finds a need for fallback; measure a separate noise floor for Track S GPU nodes when separately authorized. (B) Start Ada work earlier or choose a different floor policy.

**Recommendation.** A; this decision alone authorizes no census or run.

**Paste-ready answer.** `Ada and Track S: option A; each run still needs its own authorization.`

## Q10 — MLAgentBench and 1GC task roles

**Context.** The existing fallback permits MLAgentBench when 1GC's code is unavailable, but the eventual T1/T2 task assignments and domain coverage are not settled.

**Options.** (A) Treat MLAgentBench light tasks as T1/T2 candidates for selection at G.3; any extra public-dataset 1GC tasks are T2-only, outside the 12–16 primary count and training-side in LOSO; settle domains at G.3. (B) Specify other roles or defer all choices.

**Recommendation.** A, subject to actual access, suitability and G.3 review; it does not assert that 1GC's code is available.

**Paste-ready answer.** `MLAgentBench and 1GC: option A; final tasks and domains at G.3.`

## Q11 — Container capability checks

**Context.** The selected host's actual container capabilities are not established by the Mac; existing placement decisions remain in force. Checks must be read-only and belong to each host's authorized operator.

**Options.** (A) Have the operator check Docker, Podman and Apptainer on the 4090 hosts and Ada, and the HoreKa agent check HoreKa during their already authorized scans. (B) Name different hosts or defer checks.

**Recommendation.** A, within existing access authority; this does not authorize a container job.

**Paste-ready answer.** `Container checks: option A, read-only within existing operator authority.`

## Q12 — D8 confirmation and remaining evidence-dependent choices

**Context.** D8's decision row must identify the independently reviewed final gate bytes and precede any sweep-2 label read. Licensing, T1/T2 task lists, Phase C/D hosts, and the Track S GPU-node manager depend on G.0/G.3/G.4/B.7 or the proposer result; they are not yet available. The author already chose exam runner-up from a different family for the second proposer, and the Track S repeat decision waits for its result.

**Options.** (A) Wait for the required gate code and census/results, then decide each remaining item with its evidence. (B) Set an alternative decision schedule now.

**Recommendation.** A; keep the D8 gate closed until its author row is committed.

**Paste-ready answer.** `D8 and remaining evidence-dependent items: wait for their reviewed code and required results.`

## Working blockers (not author decisions)

- **B1 committed-HEAD verifier — RESOLVED on return.** After switching units, the same reviewer accepted the fixes at code `f7ecf2c` / review `6d24c21`; the following records the earlier time-boxed finding. **Earlier: round 3 not accepted.** A mixed space/tab indentation expands to a Markdown code block but can be read as a table row; the parser also accepts a standalone pipe line without a Markdown table header and separator. Owner: Mac-local code editor; unblock by strict Markdown table parsing, mixed-indentation and malformed-table regression tests, then same-reviewer recheck. Estimated local effort: 30–60 minutes; return to this after the next unit, per the three-round time box. The current checkout is uncommitted at `/private/tmp/paper-b-overnight-b1-20261105`; B1 entry STOP remains. This does not ask the author to decide the technical fix.
- **B1 observer execution — bounded entry accepted.** Candidate code `cdd28dc` and review `9286e2f` pass 125 synthetic tests; source provenance, final integrated checkout and remaining failures still require work. Earlier concern: The pinned `a3fedbb` harness catches observer `Exception` and proceeds, while B1's observer currently requires a Stage-A-only context; root manifest does not bind the durable observer journal. Owner: Mac-local code editor and independent reviewer; unblock by a B1-scoped observer execution path that propagates STOP immediately, records/verifies every cache-false request and binds the observer journal, with actual pinned-harness fake-server integration tests. Estimate: 2–4 hours; after three review rounds or two hours without acceptance, report and switch tasks. B2 remains stopped.
- **B1 observer integration candidate — standalone unit accepted on return.** Code `03b5002` and review `726ba86` pass 22 synthetic tests; parent-to-child binding and the production entry STOP remain separate. **Earlier: round 3 not accepted.** Marked dry-run checks compare hostnames case-sensitively, so lowercase `tasl-7.example` can evade the exam-host exclusion. Owner: Mac-local editor and same reviewer; unblock by case-normalizing host short names, adding upper/lower/FQDN regression tests, and completing parent-to-child authorization wiring and pinned-harness end-to-end review. Estimated local effort: 30–90 minutes after the time-box switch; no experiment is authorized. The isolated candidate is `/private/tmp/paper-b-b1-observer-20261105`; production `collect` remains STOP.

## Other current STOPs and resolution owners

| STOP | What unblocks it | Who acts | Estimated effort |
|---|---|---|---|
| B1 source/interval | Identify the comparable 7B pilot and its documented CI; put matching `lower`/`upper` in SHA-bound JSON and independently review definitions and provenance. | Mac agent prepares evidence; author chooses Q2; operator verifies host bytes. | Several hours if suitable local ledger data exist; otherwise depends on evidence availability. |
| B1 residual tests | Diagnose and fix the obsolete Stage A/B1 dryrun and nested rerun2 cause; the real-worker determinism test needs an independently authorized model/worker run later. No model run is authorized tonight. | Mac agent for code and independent review; author/operator for the later scoped real-worker check. | Several hours for test repair; host test time unknown. |
| B1 final checkout | Finish B1-scoped M2 review, confirm Q1 and Q2, publish the author's rule row and approved note, then review the exact resulting committed HEAD and host O2 handover. | Mac reviewer, author, then operator. | Local review hours plus author response and host preflight. |
| M3 offline replay | Implement and independently review descendant-safe Linux offline enforcement and all-configuration preflight; qualify the target Linux site under its own authority. | Mac implementer/reviewer, then authorized operator. | Multi-day engineering and site qualification; no host work tonight. |
| M11 D8 | Review the final gate code and its SHA; author commits R1-BX-D8-CONFIRM. | Mac reviewer, then author. | Gate review hours plus author response. |
| M10 HK1 | HK1 verifies actual `sacct`/`squeue` visibility, accounting latency, shared-lock behavior and site policy before enabling the one configuration switch. | HoreKa operator under HK1 authority. | Site-specific; a short capability check, elapsed time depends on accounting lag. |
| B2 ranking | Implement and independently review ranking/authority after B1. | Mac implementer/reviewer, then author. | Not yet estimated; outside B1 path. |
