# Author questions — current B1 STOP and historical records

**Current as of 8 November 2026; draft for independent review. No author answer is recorded or inferred here.** The 5 November list below is retained byte-for-byte as a historical record; its Q0–Q24 descriptions, recommendations and old STOP table are not automatically current. Several matters have since been decided or superseded, including the B1 note sequence and harness/temp scope, B1 author/committer, 20 workers, partial T1, 20% divergence STOP, Track S and thinking-off decisions, and the authorized feature-branch STATUS. Consult the dated PLAN rows and later reviewed evidence before asking any old item. The original 5 November file copied from `eb8766079a91d613e1a66626f7b01b492a45db20` has SHA-256 `5cb61b539e7631c116de8dfac9c618c35cdd472682c808e9c4d8558c03b0cab1`; the historical 7 November questions are retained separately alongside this file. No silence or elapsed time constitutes a decision.

## Current Q1 — B1 discriminating-power STOP: how to inspect

**Context.** The independently reviewed STOP report `B1_STOP_6835_20261108.md` records run `6835_20261108_a`, frozen checkout `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`, and at 2026-11-08 01:19:49 UTC the literal stop reason `random-valid < scripted cannot be shown; no discriminating power`. It reports 36 completed roots, exit 1, server-stop observation and retained marker; the cause and any actual comparison values are not established. The later separately reviewed read-only census has bounded visibility and does not prove every possible descendant absent. Existing B1 outputs, logs, records, ledger, marker and other tracks' work remain preserved; no rerun, gate recomputation, marker retirement or automatic restoration is authorized by this question.

**Options.** (A) Permit a narrowly scoped read-only inspection of existing B1 anchor manifests, logs and provenance sufficient to explain the observed STOP, with exact commands independently reviewed first; report observed values only as needed and do not rerun or recompute the gate. (B) Keep the scene preserved and defer inspection until you give further instructions. Either choice leaves the present STOP and all phase boundaries in force.

**Recommendation.** A, if you want an evidence-based diagnosis; use the existing records only and seek independent review of the findings. If you prefer not to examine the preserved outputs yet, choose B. This is not a proposal to waive the anchor criterion or choose a replacement result.

**Paste-ready answer.** `B1 STOP: 允许经独立审查的只读检查现有 anchor manifest、日志和来源，以解释 STOP；不重算 gate、不重跑、不修改或退役任何现场文件，结论先交独立审查。`

**Alternative paste-ready answer.** `B1 STOP: 保全现场，暂不检查，等待我的进一步指示；不重跑、不重算 gate。`

## M4 sequencing — already recorded, still unresolved

The 7 November question list already records the M4 sequencing question; it is preserved in `MAC_OVERNIGHT_QUESTIONS_20261107.md` below as a separate historical file, rather than asked a second time. The current independent scope recheck `44925cf194dc337cbfdf5b8b16f2202ca4eb3404`, reviewed at `5097b6a36ce8d73b5519e736540777e9cd832903`, found that the author's 7 November conditional instruction holds M4's non-shared pieces when they conflict with the runbook's M3-first order. No M4 ordering change or DTQ authorization is inferred. M3 remains unaccepted; the author may later resolve the existing question. B2 power/note and M11 D8 remaining choices also stay separate, and the latter's statistical implementation details go through review and preregistration before the existing author SHA confirmation, not assumed new decisions.

---

## Historical 5 November list — retained, not current status

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

**Context.** The runbook requires a committed author G.5 note after HK5 and the author's decisions on task-node count, K and budget. The present submit tool refuses EVIDENCE and HK6/HK7 unconditionally; the single HK1 switch cannot enable them. A proposed, unsigned per-manifest JSON format is in `docs/r1/proposals/HK2_EVIDENCE_AUTH_NOTE_FORMAT_DRAFT_20261105.md`; a standalone checker for that option is independently accepted at `0d6d569`, but is not connected to submission. Its manifest hash binds exact bytes but does not prove the command's semantic classification.

**Options.** (A) A separate committed note per exact manifest, with phase, manifest SHA and the author's post-HK5 node count, K and budget. (B) A separately reviewed bounded manifest-set format. (C) Another specified format.

**Recommendation.** A for the smallest initial scope; consider B only with unambiguous, independently reviewed membership and limits. Either choice requires implementation, actual-work classification and independent review; it does not authorize a job or decide the post-HK5 values.

**Paste-ready answer.** `For HoreKa EVIDENCE, use <per-manifest / reviewed manifest-set / other specified> committed author-note format; the post-HK5 node count, K and budget still require my decision.`

## Q19 — HoreKa submitted-job limits (open; HK0/HK1)

**Context.** `r1/scripts/hk2/hk2_config.json` labels the following values as proposals, not decisions: freeze F 20 Nov 12:00 CET, cutoff C 20 Nov 20:00 CET, copyback D 21 Nov 18:00 CET; campaign accounting start 4 Nov 00:00 CET; 400 GPU-h ceiling and 300 GPU-h STOP; four-hour `T_max`; and the 1-GPU, 32-CPU, 180-GiB probed shape. The author's statement that 400 GPU-h is acceptable does not itself fix a ceiling or the 300 threshold. `T_max` and GPU model are decided after HK0; H100 is the current T1 choice and H200 would need an amending row. The 20–21 Nov session availability and proposed STOP-marker path also need confirmation.

**Options.** (A) Decide F/C/D, 20–21 Nov session availability, accounting start and budget limits now, and decide `T_max`, GPU model and shape after HK0. (B) Defer the full set until the queue-probe results and HK0 review. (C) Specify alternatives item by item.

**Recommendation.** B unless the author has the queue-probe results and wants to decide some items earlier. Before HK1 use, review every proposed config value and establish the exact authorized limits and marker handling; no default becomes a decision merely because the tool displays it.

**Paste-ready answer.** `HoreKa limits: decide F/C/D, 20–21 Nov session availability, accounting start, budget ceiling/STOP, T_max, GPU model, shape and STOP marker after HK0 and review.`

## Q20 — HoreKa placement after HK3

**Context.** HK3 measures concurrency at k = 1, 2, 4, task determinism and a co-location arm. The author then fixes runs per GPU, J4 audit placement and whether J3's proposer and task share a GPU; the proposed two-GPU fallback needs a separate shape exception and costs more.

**Options.** (A) Decide after HK3 measurements and review. (B) Specify placement now.

**Recommendation.** A, using co-location only if HK3 and the loaded J1b identity check pass; otherwise decide the reviewed fallback and budget separately.

**Paste-ready answer.** `HoreKa placement: decide k, J4 placement and J3 co-location after HK3 and review.`

## Q21 — Infrastructure failure, divergence and wave STOP

**Context.** Runbook §0.3 proposes treating timeouts, Slurm termination and OOM caused by exceeding declared co-location memory as infrastructure failures; it proposes whole-unit reruns for those, while a run's own-cap OOM remains an edit outcome and non-finite loss/no metric at fixed budget is divergence. The runbook separately proposes a >2% infrastructure-failure STOP per wave. This is distinct from the already chosen >20% T1 divergence STOP.

**Options.** (A) Adopt the proposed distinction, 3× placement-measured timeout and >2% wave STOP with a reviewed denominator. (B) Specify different categories, timeout or threshold. (C) Defer until the operator provides a concrete denominator and failure-report design.

**Recommendation.** C for the exact wave denominator; consider A once the unit counts and handling of incomplete outcomes are reviewed. Never re-run a divergent outcome merely to conceal it.

**Paste-ready answer.** `HoreKa failures: decide the categories, timeout and >2% wave denominator after the reviewed failure-report design.`

## Q22 — J1b pass criterion

**Context.** Before HK4, the author must commit the proposer qualification criterion. J1b checks full offload, 50 prompts × 3 with `cache_prompt: false`, identity on an idle GPU and with the chosen task load, latency and projection.

**Options.** (A) Adopt a reviewed exact-identity criterion of 1.000 in both tests plus full offload and recorded latency/projection. (B) Specify a different criterion. (C) Decide after HK3 and the concrete J1b protocol are reviewed, before HK4.

**Recommendation.** C, with A as the starting proposal and no tolerance inferred without an author decision.

**Paste-ready answer.** `J1b: decide the committed criterion after HK3 and protocol review, before HK4; evaluate exact identity 1.000 as the proposed starting point.`

## Q23 — Two server-agent routing consequences

**Context.** The author already chose two server agents with disjoint hosts and asked to retain existing individual host decisions. PLAN R1-SERVER-AGENTS-TWO separately labels the detailed proposed row amendments, author-opened HoreKa tunnel and handover through the author or pushed branches as consequences for confirmation; this question does not replace individual host choices.

**Options.** (A) Confirm the specific routing and amendments after reviewing them individually. (B) Keep them proposed and specify any changes. (C) Defer.

**Recommendation.** A only for each consequence the author agrees with; preserve the existing individual host decisions and current NHR restrictions.

**Paste-ready answer.** `Server-agent consequences: review the proposed amendments, tunnel and handover individually; retain the existing host decisions.`

## Q24 — Five held M3 file diffs, after review

**Context.** The held `9bab3d6f` changes affect `r1/c3/train/run.py`, `r1/c3/train/trainer.py`, `r1/c3/env.py`, `r1/c3/control.py` and `r1/c3/prior_model.py`. Their prior review blocked B.2 launch; the author asked to decide after M3 review. Full M3 is not accepted and these diffs have not been merged.

**Options.** (A) After a complete independent M3 review, accept the exact reviewed diffs. (B) Request fixes or reject some/all. (C) Continue deferring pending that review.

**Recommendation.** C now; provide the final diff and findings before asking for a file-level decision.

**Paste-ready answer.** `Five held M3 files: defer my decision until the complete independent M3 review and exact diffs are available.`

## Resolved bounded units (not author decisions)

- B1 committed-HEAD verifier: accepted at `f7ecf2c`, review `MAC_B1_AUTHORITY_OVERNIGHT_REVIEW_20261105.md`.
- B1 observer, parent binding and production entry: accepted within separately named scopes, including code `cdd28dc` and review `MAC_B1_ENTRY_REVIEW_20261105.md`. The separate B2 entry and ranking remain STOP.
- B1 cooperative lock, previous-server preservation and worker Python binding: scoped acceptances at `9d010a1`, `528f12e` and `bc52181`; actual TASL-7 behavior remains an operator check. Parent dry-run host exclusions were accepted at `650f6eb`.
- B1 complete-batch verifier: accepted in offline/synthetic scope at `1dd6e88`, review `MAC_B1_BATCH_VERIFIER_REVIEW_20261105.md`; case-insensitive sealed-path correction `bab4b8c` reviewed in `MAC_B1_BATCH_ADVERSARIAL_AUDIT_20261105.md`. The unsigned note repin was independently reviewed at `4019756`; these reviews do not establish real-worker or host readiness.
- M3 recovered-case/cache-identity binding: accepted for planning-only scope at `2e65bec`, review `MAC_M3_RECOVERED_CASE_BINDING_REVIEW_20261105.md`, published separately at `mac-m3-case-binding-20261105` @ `9ce6b3b`. It does not establish physically independent copies, offline executability or host containment, and depends on a separately held replay driver.

## Other current STOPs and resolution owners

| STOP | What unblocks it | Who acts | Estimated effort |
|---|---|---|---|
| B1 source/interval | Identify the comparable 7B pilot and its documented CI; put matching `lower`/`upper` in SHA-bound JSON and independently review definitions and provenance. | Mac agent prepares evidence; author chooses Q2; operator verifies host bytes. | Several hours if suitable local ledger data exist; otherwise depends on evidence availability. |
| B1 residual tests | Restore or explicitly resolve the former Stage A/B1 kill/resume coverage and address the outer nested rerun2 test after its reviewed historical collection-error diagnosis; the real-worker determinism test needs an independently authorized model/worker run later. The replacement dryrun checks STOP preservation but not former coverage. No model run is authorized tonight. | Mac agent for code and independent review; author/operator for the later scoped real-worker check. | Several hours for test repair; host test time unknown. |
| B1 final checkout and GPU lease | Verify the accepted flock and server descriptor on TASL-7; finish B1-scoped M2 review, confirm Q1 and Q2, publish the author's rule row and approved note, then review the exact resulting committed HEAD and host O2 handover. | Mac implementer and reviewer, author, then operator. | Local review hours plus author response and host preflight. |
| M3 offline replay | Three-round timebox reached: finish and independently review the Linux supervisor, distinguish normal HUP from monitor failure, bind all 16 cases in the reviewed execution path and prove their offline executability before scheduling; separately qualify the target Linux site under its own authority. | Mac implementer/reviewer, then authorized operator. | Multi-day engineering and site qualification; no host work tonight. |
| M11 D8 | Finalize and review the gate code and its SHA, complete authorized protected training-reader coverage, then author commits R1-BX-D8-CONFIRM. The separately scoped reader/parser fixes were accepted at `3d0b915`. | Mac implementer/reviewer; author for protected-file decisions and confirmation. | Gate and reader implementation/review hours or longer, plus author response. |
| M10 HK1 | The authority and DEADLINE fixes were independently accepted at `113eec8`. The author resolves the proposed values in Q19; the authorized HK1 operator verifies the pinned PLAN, actual `sacct`/`squeue` visibility, accounting latency, shared-lock behavior and site policy before enabling the switch within the applicable reviewed phase scope. | Author, then HoreKa operator and reviewer under HK1 authority. | Author response and site-specific elapsed time, including accounting lag. |
| M10 EVIDENCE | Implement and independently review the HK6/HK7/J5 path, connect an adopted author-note verifier, and establish actual work/manifest binding; author chooses Q18 and signs the G.5 note only after HK5 prerequisites. The standalone proposed-format checker is accepted but unused. The default-off switch alone cannot enable these phases. | Mac implementer/reviewer, author, then authorized operator. | One to several engineering/review days plus author response and later phase timing. |
| B2 ranking | Implement and independently review ranking/authority after B1. | Mac implementer/reviewer, then author. | Roughly 1–3 engineering days plus independent review; uncertain and outside B1 path. |
