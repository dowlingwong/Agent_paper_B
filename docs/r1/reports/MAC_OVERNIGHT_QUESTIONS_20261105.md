# Overnight author questions — 5 November 2026

AI-assisted (Codex). Draft only: no row or option below is an author decision or authorization. Ordered by the work it would unblock. This is a living list; items are updated as the independent reviews proceed. Sources: `docs/r1/PLAN.md` §10 author rows; `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` §(j); `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` O2; and the scoped review files named below.

## Q0 — B1 rule row and authorization note, after the blockers

**Context.** The rule and unsigned note have received scoped review, but the pilot reference, three B1-related baseline failures, final combined checkout and TASL-7 handover remain open. A decision on the rule or note is the author's alone; no launch can start solely because the proposed line appears here.

**Options.** (A) Once those prerequisites and Q1–Q2 are resolved, approve the candidate rule and the reviewed B1 note. (B) Defer or request revisions.

**Recommendation.** B until the missing pilot evidence and B1 checks are resolved; then A if the author agrees. The author may give the wording to record verbatim in PLAN §10.

**Paste-ready answer when prerequisites are closed.** `I approve x5_rule_v2 SHA256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad and the reviewed B1 authorization note for TASL-7, subject to the agreed anchor reference, exact final checkout, and all reviewed handover and phase gates.`

## Q1 — B1 amendment acceptance record

**Context.** B1 binds the two Stage A table SHA-256 values and an amendment-acceptance record. The O1 report contains both accepted table digests and is already on the integration branch. Proposed format: `stage_a_amendment_acceptance_sha256` is the SHA-256 of the exact committed bytes of `docs/r1/reports/OPS_O1_20261104.md`, currently `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`; the path is bound too. If those bytes are corrected, a new digest and re-review are required.

**Options.** (A) Use those exact report bytes and digest. (B) Name a different committed acceptance record and digest.

**Recommendation.** A, subject to the independent B1 review and verification of the file at the operator's checkout.

**Paste-ready answer.** `B1 acceptance record: use OPS_O1_20261104.md sha256 0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e.`

## Q2 — B1 anchor duplicate reference

**Context.** The B1 config requires `anchor_duplicate_reference` with source, SHA and bounds, but all four are TODO and the reviewed B1 verifier now requires the source SHA and numerical bounds to match a JSON document with `lower` and `upper` fields. The applicable pilot source and derivation of the bounds have not yet been established; a matching JSON file alone does not prove pilot provenance. The existing `docs/r1/reports/DUPLICATE_RATE_PILOT_20261022.md` explicitly reports no confidence intervals, mixes different node/memory strata, and defines duplicates separately from no-ops. Its memory-on digits stratum has only two liveness campaigns of ten trials; DT4's six digits campaigns are memory-off, whereas B1 uses `append_only_summary` (`docs/r1/reports/exam_phase2_20261026/STAGE_A_SOURCE_PREREQUISITE.md`; `r1/exam/b1_batch.py`). B1 counts `active_config_seen_before` among evaluated novelty events; its denominator and duplicate definition must be reconciled with the pilot before selecting a comparable CI.

**Options.** (A) Author names a committed reference and fixed bounds after the Mac agent identifies the evidence. (B) Author specifies a different reference and bounds. (C) Defer B1 pending a reference.

**Recommendation.** A if a protocol-authorized, independently reviewable source exists; otherwise C. Do not invent values from a convenient pilot.

**Paste-ready answer.** `B1 anchor duplicate reference: use JSON <path> sha256 <SHA256>, lower <value>, upper <value>, derived from <pilot evidence and method>.`

## Q3 — Stronger provenance (optional)

**Context.** The requested minimum checks committed HEAD, a clean tree, dated PLAN §10 decision row, and bound note/file hashes. A repository writer could create a false row or note; independent review and the author's own instruction mitigate this as process, not cryptography.

**Options.** (A) Use the reviewed minimum and process boundary. (B) Add a separate signed or independently authenticated published authority root before future phases.

**Recommendation.** A for the present B1 verifier; consider B for later work. This optional stronger scheme does not block B1 under the overnight instruction.

**Paste-ready answer.** `B1 uses the reviewed committed-HEAD verifier and independent review; consider signed provenance separately.`

## Q4 — Test exceptions, only after classification and review

**Context.** The latest Mac full suite had 39 historical failure IDs; some touch B1 or shared safety paths and cannot be treated as exceptions merely because they predate M2. The independent classification identifies 21 pre-existing non-B1 cases and 3 environment cases; 14 B1 cases and one unresolved nested B1 case are excluded from exceptions. Twelve B1 fake-server cases have an independently accepted fixture fix. The old Stage A dryrun ID now passes a revised STOP-preservation test, which does not reproduce its former kill/resume coverage; the real-worker model test and outer nested rerun2 remain unverified under the no-model instruction. A retained historical preparation's 14 collection errors share a missing module in its older harness pin; see the independently reviewed `MAC_B1_NESTED_RERUN2_CAUSE_20261105.md` on the B1 branch. That diagnosis does not make the outer test pass.

**Options.** (A) Review an exact, evidence-backed list of non-B1 exceptions after the B1-path failures are resolved. (B) Require all tests to pass.

**Recommendation.** A only for the independently reviewed outside-B1/environment cases, with unresolved cases excluded. The reviewed 23-ID draft is `docs/r1/proposals/M2_TEST_EXCEPTIONS_DRAFT_20261105.md` on `mac-b1-overnight-20261105`, review `MAC_M2_TEST_EXCEPTION_DRAFT_REVIEW_20261105.md`; the control dryrun and all B1-related failures are excluded.

**Paste-ready answer.** `I accept the 23 explicitly listed non-B1 exception candidates in M2_TEST_EXCEPTIONS_DRAFT_20261105.md; B1-related failures remain blocking.`

## Q5 — T1 divergence rule: denominator and timing

**Context.** The author chose `设 20% STOP` in response to a question specifying a STOP when divergence is **above** 20%. The exact counted proposals, handling of missing outcomes and evaluation time were not specified.

**Options.** (A) Per node, count distinct completed label proposals with all audit-seed outcomes classified; numerator is proposals where more than half of audit seeds diverged, as the existing REVISIONS (c) rule states. For partial divergence at or below half, use the remaining valid seeds under that rule. STOP when the resulting per-node fraction exceeds 20%, reporting counts; missing/ambiguous outcomes separately STOP. (B) Specify a different denominator, timing or minimum sample size.

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

**Context.** PLAN §10 `R1-1GC-FALLBACK` has already selected MLAgentBench as the third suite. Its eventual task-level T1/T2 assignments and domain coverage remain unsettled (decision packet §(j), item 14).

**Options.** (A) Treat MLAgentBench light tasks as T1/T2 candidates for selection at G.3; any extra public-dataset 1GC tasks are T2 evaluation-only and outside the 12–16 primary count; settle their evaluation placement and domain coverage at G.3. Do not use T2 data for training. (B) Specify other roles or defer all choices.

**Recommendation.** A, subject to actual access, suitability and G.3 review; it does not assert that 1GC's code is available. The older draft phrase “T2-only” and “always training-side” is internally inconsistent, so the latter is not adopted as a consequence.

**Paste-ready answer.** `MLAgentBench and 1GC: option A; final tasks and domains at G.3.`

## Q11 — Container capability checks

**Context.** The selected host's actual container capabilities are not established by the Mac; existing placement decisions remain in force. Checks must be read-only and belong to each host's authorized operator.

**Options.** (A) Have the operator check Docker, Podman and Apptainer on the 4090 hosts and Ada, and the HoreKa agent check HoreKa during their already authorized scans. (B) Name different hosts or defer checks.

**Recommendation.** A, within existing access authority; this does not authorize a container job.

**Paste-ready answer.** `Container checks: option A, read-only within existing operator authority.`

## Q12 — D8 gate confirmation

**Context.** PLAN §10 `R1-BX-D8` and `R1-BX-PROPOSED-CONFIRM` require an author row naming the independently reviewed gate code and SHA before sweep-2 label analysis. The full gate implementation remains under development.

**Options.** (A) Wait for reviewed gate code and then decide its row. (B) Specify a different schedule without opening the gate.

**Recommendation.** A; keep the analysis guard closed until the committed row exists.

**Paste-ready answer.** `D8: wait for the reviewed gate code and SHA before my confirmation.`

## Q13 — Licence checks

**Context.** The decision packet §(j), item 7, requires the G.0/HoreKa inventory to establish task and data licences; those results are not available here.

**Options.** (A) Decide after the scan. (B) Specify an alternative standard now.

**Recommendation.** A; do not assume an unexamined licence permits use.

**Paste-ready answer.** `Licences: decide after the G.0 inventory and review.`

## Q14 — T1/T2 task lists

**Context.** The decision packet §(j), item 8, puts the actual task lists at G.3 after the census; suite selection and task selection are distinct.

**Options.** (A) Choose lists after the G.0/G.3 evidence. (B) Name specific tasks now.

**Recommendation.** A, with the selected tiers and data use recorded before labels.

**Paste-ready answer.** `T1/T2 lists: choose at G.3 after the census.`

## Q15 — Phase C/D hosts

**Context.** The decision packet §(j), item 10, ties the later host plan to the G.4 and B.7 results; the author has retained the existing item-by-item host decisions.

**Options.** (A) Decide later as one reviewed plan. (B) Specify a change now.

**Recommendation.** A; preserve existing placements meanwhile.

**Paste-ready answer.** `Phase C/D hosts: decide after G.4 and B.7; retain existing placements meanwhile.`

## Q16 — HoreKa job design

**Context.** The decision packet §(j), item 13, treats the T1 jobs draft as a design basis for consideration after the HoreKa scan; it is not itself a phase authorization. The author already confirmed J3 is covered by the submission ruling, subject to NHR restrictions.

**Options.** (A) Review the design against the scan and choose its adoption then. (B) Specify another design basis.

**Recommendation.** A; a design choice does not authorize jobs.

**Paste-ready answer.** `HoreKa design: decide after the scan and review.`

## Q17 — Track S GPU-node manager

**Context.** PLAN `R1-BX-D10` and the decision packet §(j), item 15, defer the GPU-node manager choice until G.0/D28. The CPU-node manager and the repeat-with-exam-pick timing were already decided separately.

**Options.** (A) Decide after G.0/D28. (B) Name a manager now.

**Recommendation.** A.

**Paste-ready answer.** `Track S GPU manager: decide after G.0 and D28.`

## Q18 — HoreKa EVIDENCE note format (open; later phase)

**Context.** The runbook requires a committed author G.5 note after HK5 and the author's decisions on task-node count, K and budget. The present submit tool refuses EVIDENCE and HK6/HK7 unconditionally; the single HK1 switch cannot enable them. A proposed, unsigned per-manifest JSON format is in `docs/r1/proposals/HK2_EVIDENCE_AUTH_NOTE_FORMAT_DRAFT_20261105.md`. Its manifest hash binds exact bytes but does not prove the command's semantic classification.

**Options.** (A) A separate committed note per exact manifest, with phase, manifest SHA and the author's post-HK5 node count, K and budget. (B) A separately reviewed bounded manifest-set format. (C) Another specified format.

**Recommendation.** A for the smallest initial scope; consider B only with unambiguous, independently reviewed membership and limits. Either choice requires implementation, actual-work classification and independent review; it does not authorize a job or decide the post-HK5 values.

**Paste-ready answer.** `For HoreKa EVIDENCE, use <per-manifest / reviewed manifest-set / other specified> committed author-note format; the post-HK5 node count, K and budget still require my decision.`

## Q19 — HoreKa submitted-job limits (open; HK0/HK1)

**Context.** `r1/scripts/hk2/hk2_config.json` labels the following values as proposals, not decisions: freeze F 20 Nov 12:00 CET, cutoff C 20 Nov 20:00 CET, copyback D 21 Nov 18:00 CET; campaign accounting start 4 Nov 00:00 CET; 400 GPU-h ceiling and 300 GPU-h STOP; four-hour `T_max`; and the 1-GPU, 32-CPU, 180-GiB probed shape. The author's statement that 400 GPU-h is acceptable does not itself fix a ceiling or the 300 threshold. `T_max` is decided after HK0; the proposed STOP-marker path also needs a reviewed operational decision.

**Options.** (A) Decide F/C/D, accounting start and budget limits now, and decide `T_max`/shape after HK0. (B) Defer the full set until the queue-probe results and HK0 review. (C) Specify alternatives item by item.

**Recommendation.** B unless the author has the queue-probe results and wants to decide some items earlier. Before HK1 use, review every proposed config value and establish the exact authorized limits and marker handling; no default becomes a decision merely because the tool displays it.

**Paste-ready answer.** `HoreKa limits: decide F/C/D, accounting start, budget ceiling/STOP, T_max, shape and STOP marker after HK0 and review.`

## Resolved bounded units (not author decisions)

- B1 committed-HEAD verifier: accepted at `f7ecf2c`, review `MAC_B1_AUTHORITY_OVERNIGHT_REVIEW_20261105.md`.
- B1 observer, parent binding and production entry: accepted within separately named scopes, including code `cdd28dc` and review `MAC_B1_ENTRY_REVIEW_20261105.md`. The separate B2 entry and ranking remain STOP.
- B1 cooperative lock, previous-server preservation and worker Python binding: scoped acceptances at `9d010a1`, `528f12e` and `bc52181`; actual TASL-7 behavior remains an operator check. Parent dry-run host exclusions were accepted at `650f6eb`.
- B1 complete-batch verifier: accepted in offline/synthetic scope at `1dd6e88`, review `MAC_B1_BATCH_VERIFIER_REVIEW_20261105.md`. The unsigned note pin was independently reviewed at `06a21b3`; neither review establishes real-worker or host readiness.
- M3 recovered-case/cache-identity binding: accepted for planning-only scope at `2e65bec`, review `MAC_M3_RECOVERED_CASE_BINDING_REVIEW_20261105.md`, published separately at `mac-m3-case-binding-20261105` @ `9ce6b3b`. It does not establish physically independent copies, offline executability or host containment, and depends on a separately held replay driver.

## Other current STOPs and resolution owners

| STOP | What unblocks it | Who acts | Estimated effort |
|---|---|---|---|
| B1 source/interval | Identify the comparable 7B pilot and its documented CI; put matching `lower`/`upper` in SHA-bound JSON and independently review definitions and provenance. | Mac agent prepares evidence; author chooses Q2; operator verifies host bytes. | Several hours if suitable local ledger data exist; otherwise depends on evidence availability. |
| B1 residual tests | Restore or explicitly resolve the former Stage A/B1 kill/resume coverage and address the outer nested rerun2 test after its reviewed historical collection-error diagnosis; the real-worker determinism test needs an independently authorized model/worker run later. The replacement dryrun checks STOP preservation but not former coverage. No model run is authorized tonight. | Mac agent for code and independent review; author/operator for the later scoped real-worker check. | Several hours for test repair; host test time unknown. |
| B1 final checkout and GPU lease | Verify the accepted flock and server descriptor on TASL-7; finish B1-scoped M2 review, confirm Q1 and Q2, publish the author's rule row and approved note, then review the exact resulting committed HEAD and host O2 handover. | Mac implementer and reviewer, author, then operator. | Local review hours plus author response and host preflight. |
| M3 offline replay | Three-round timebox reached: finish and independently review the Linux supervisor, distinguish normal HUP from monitor failure, bind all 16 cases in the reviewed execution path and prove their offline executability before scheduling; separately qualify the target Linux site under its own authority. | Mac implementer/reviewer, then authorized operator. | Multi-day engineering and site qualification; no host work tonight. |
| M11 D8 | Review the final gate code and its SHA; author commits R1-BX-D8-CONFIRM. | Mac reviewer, then author. | Gate review hours plus author response. |
| M10 HK1 | The authority and DEADLINE fixes were independently accepted at `113eec8`. The author resolves the proposed values in Q19; the authorized HK1 operator verifies the pinned PLAN, actual `sacct`/`squeue` visibility, accounting latency, shared-lock behavior and site policy before enabling the switch within the applicable reviewed phase scope. | Author, then HoreKa operator and reviewer under HK1 authority. | Author response and site-specific elapsed time, including accounting lag. |
| M10 EVIDENCE | Implement and independently review the HK6/HK7/J5 path, author-note and actual work/manifest binding; author chooses Q18 and signs the G.5 note only after HK5 prerequisites. The default-off switch alone cannot enable these phases. | Mac implementer/reviewer, author, then authorized operator. | Approximately one engineering/review day plus author response and later phase timing. |
| B2 ranking | Implement and independently review ranking/authority after B1. | Mac implementer/reviewer, then author. | Roughly 1–3 engineering days plus independent review; uncertain and outside B1 path. |
