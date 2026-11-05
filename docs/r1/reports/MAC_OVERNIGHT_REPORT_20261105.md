# Mac overnight report — 5 November 2026

**DRAFT — interim inventory; update and review at the morning handoff.** AI-assisted (Codex). No author decision is recorded by this report. All branches below are feature branches, not `main`, `r1`, or `exam-x-*`.

## Outcome and scope

B1 is **not ready to start from one author signature**. Its rule, committed-HEAD authority check, launch components, complete-batch verifier and unsigned draft have separate independent acceptances, but the pilot anchor reference, author decisions, historical test coverage and TASL-7 qualification remain open. The earlier whole-handoff review `MAC_B1_FINAL_READINESS_REVIEW_20261105.md` is NOT ACCEPTED for launch; the later sealed-path fix and draft repin were separately reviewed, and the eventual final checkout still needs review. B2 ranking is a separate STOP, outside B1's scoped work.

No experiment host or real model service was contacted, no experiment or real model was run, no GPU was used, and no author decision cell was supplied. GitHub was used for authorized feature-branch pushes. Synthetic tests and test-owned local fakes are identified as such in their reviews. The original Mac working tree was not modified.

The historical Mac full suite recorded 896 passed, 39 failed and 11 skipped (`MAC_M2_FAILURE_CLASSIFICATION_20261105.md` and its linked log). It was not rerun after these changes under the overnight no-model instruction; the focused synthetic results below do not establish a passing current full suite.

## Reviewed units and publication

| Unit | Published branch / code | Independent review and limits |
|---|---|---|
| X5 v2 rule | `mac-b1-overnight-20261105`; SHA-256 `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad` | `MAC_M2_B1_RULE_REVIEW_20261105.md`: B1 rule scope only; descriptive thinking-on retained, thinking-off alone for D28. |
| B1 committed-HEAD author gate | `f7ecf2c` on B1 branch | `MAC_B1_AUTHORITY_OVERNIGHT_REVIEW_20261105.md`; a repository writer could forge a row/note, mitigated by the author's instruction and independent review, not cryptography. |
| B1 lease, worker, preservation and synthetic lifecycle | `9d010a1`, `528f12e`, `bc52181`, `650f6eb`, `19da54e` on B1 branch | `MAC_B1_COMBINED_REVIEW_20261105.md` and `MAC_B1_PARENT_E2E_REVIEW_20261105.md`; host lease and real worker remain unverified. |
| B1 complete-batch verifier and draft | Code pin `bab4b8cb0569b94c23f2828f1a8cdb5ce3782dcf`; B1 branch includes sealed-path fix `bab4b8c` and repin review `4019756` | `MAC_B1_BATCH_VERIFIER_REVIEW_20261105.md` accepts offline/synthetic scope, with partly mocked full-batch fixtures; `MAC_B1_BATCH_ADVERSARIAL_AUDIT_20261105.md` accepts the sealed-path correction; `MAC_B1_COMBINED_DRAFT_REVIEW_20261105.md` accepts unsigned documentation only. |
| Failure classification and historical diagnosis | B1 branch through `c03d76f` | All 39 historical IDs classified in `MAC_M2_FAILURE_CLASSIFICATION_20261105.md`; `MAC_B1_NESTED_RERUN2_CAUSE_REVIEW_20261105.md` accepts a bounded diagnosis, not a passing outer test. A 23-ID exception draft is unsigned. |
| M10 submission/status | `mac-int-20261104`, initial code `9f7675e`, fixes `3e43e6c` / `59b08d3`, review `113eec8` | Fresh audit found authority-parser and DEADLINE-resubmission defects; `MAC_M10_FINAL_INTEGRATION_REVIEW_20261105.md` accepts those repairs within engineering scope, 38 fake Python 3.9 tests. **Full M10 remains NOT ACCEPTED**: EVIDENCE and HK6/HK7 remain refused; real submission switch OFF. |
| M10 proposed EVIDENCE note checker | `mac-int-20261104`, `3ff6de7`, integration review `0d6d569` | `MAC_M10_EVIDENCE_NOTE_INTEGRATION_REVIEW_20261105.md` accepts the standalone proposed-format checker; seven Python 3.9 synthetic tests. It is unused by the submitter; Q18 and actual work classification are open. |
| M11 readers | `mac-int-20261104`, initial units `44e1475`, `f6bc280`, `64b384d`, `d298b32`, `aaf34c9`; fixes `8645778` / `d9447e1` | `MAC_M11_FINAL_READER_INTEGRATION_REVIEW_20261105.md` accepts the scoped decision-table/date, case-insensitive sealed-path and audit-helper corrections, 39 synthetic tests. Full D8 gate, author confirmation and protected training-reader coverage remain open. |
| M3 loader snapshot | `mac-int-20261104`, `414d8a1` | `MAC_M3_LOADER_SNAPSHOT_REVIEW_20261105.md`, eight synthetic loader checks; full M3 remains STOP. |
| M3 recovered cases / cache copy | `mac-m3-case-binding-20261105` @ `9ce6b3b`; `mac-m3-cache-copy-20261105` @ `ecf1ce3` | `MAC_M3_RECOVERED_CASE_BINDING_REVIEW_20261105.md` and `MAC_M3_CACHE_COPY_COMPONENT_REVIEW_20261105.md`: planning/cooperative-filesystem scope only, not integrated production replay. |
| M3 and HoreKa dependency inventories | `mac-int-20261104`, `c4b4d97` and `bdf5c51` | `MAC_M3_STATIC_DEPENDENCY_INVENTORY_REVIEW_20261105.md` and `MAC_M10_WORK_IDENTITY_INVENTORY_REVIEW_20261105.md` accept file-only source inventories; neither proves offline executability or authorizes a job. |
| P.3a template inventory | `mac-int-20261104`, `b77ec1b` | `MAC_M13_TEMPLATE_INVENTORY_REVIEW_20261105.md`: local read-only scope; actual P.3a attempt-1 order and pin NOT CHECKABLE without host records. |

## B1 draft and words held for the author

The unsigned `docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261104.md` on the B1 branch binds `digits_mlp`, `openml_credit_approval`, `openml_ionosphere`, `llm_call_cap = 80`, `workers = 20`, rule SHA above, Stage A table SHA-256 values `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` and `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`, and a proposed O1 report digest. It remains `approved: false`. The O1 format choice and anchor reference require author decisions.

Proposed PLAN row, deliberately without a decision:

```text
| R1-EXAM-RULE-X5V2 |  |
```

The **conditional** author wording below is not ready to authorize a run until the open prerequisites have been closed and reviewed:

```text
I approve x5_rule_v2 SHA256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad and the reviewed B1 authorization note for TASL-7, subject to the agreed anchor reference, exact final checkout, and all reviewed handover and phase gates.
```

The full exact operator-message draft, including O2 steps and STOPs, is `docs/r1/proposals/B1_OPERATOR_MESSAGE_V3_DRAFT_20261105.md` on the B1 branch. It is **held**, not sent; it requires a reviewed final checkout HEAD and completed prerequisites before use. Its proposed code pin is `bab4b8cb0569b94c23f2828f1a8cdb5ce3782dcf` and harness pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`.

Exact held operator text:

> B1 is assigned to TASL-7, with B1 code pin (entry, lease, preservation, worker Python binding, dry-run host exclusion, synthetic parent/child lifecycle and complete-batch verifier reviewed separately) `bab4b8cb0569b94c23f2828f1a8cdb5ce3782dcf`, harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, and rule SHA-256 `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`. Do not start until the final detached checkout HEAD, carrying the author's dated PLAN decision and committed B1 authorization note, has been independently reviewed and communicated, and all conditions below are closed.
>
> Once separately authorized, first verify how O2's TASL-2 marker and watcher sequence applies to **TASL-7**, including whether its Track S watcher is active. Then follow the applicable sequence: create the Track X evidence marker and publish the matching running STATUS; wait for any Track S watcher to pause collectors and stop its servers, reporting a forced pause; coordinate with Track P and P.3a so no other GPU work is active; verify the GPU lease is free, no `llama-server` or GPU compute process is present, and the host is otherwise safe; perform the fresh real-lock preflight and verify the selected model hashes and both Stage A table hashes; then proceed only under the reviewed phase instructions. The B1 runner acquires and holds the cooperative GPU flock through its server and worker lifecycle; validate the Linux lock and inherited server descriptor in the host preflight. A one-shot free-lock check is not a held lease. Preserve existing processes and STOP sites. The marker remains through B1 and its review STOP and B2 unless the phase is stopped for good, per O2.
>
> The exact note, row and checkout are still unsigned; the anchor duplicate reference source, provenance and interval remain open; the remaining B1-relevant baseline test failures and the complete B1-scoped M2/combined-checkout review remain open. B2 ranking is separately STOP; the author explicitly permits that outside B1 scope. Confirm the O1 acceptance-record format with the author, and verify the actual host copies and capacity. A failure, mismatch, unverified host condition or unresolved question is STOP; report it without restarting or modifying another operator's process.

## Remaining STOPs

| Blocker | Unblock and owner | Effort |
|---|---|---|
| B1 author note and row | Author chooses Q1 format, then decides rule/note; reviewer checks the exact committed final checkout. | Author response plus 1–2 local review hours. |
| B1 anchor reference | Mac agent identifies comparable pilot evidence and definitions; author chooses source and interval; reviewer verifies SHA, derivation and binding. | Source-dependent; several hours if suitable evidence exists. |
| B1 tests | Implementer/reviewer address former Stage-A kill/resume coverage and outer rerun-2; separately authorized operator/author resolves real-worker determinism. The nested historical preparation's 14 collection errors had a common old-harness missing module; this is not a passing outer test. | Local investigation hours plus separately authorized worker/site time. |
| TASL-7 handover | Authorized operator checks actual O2 marker/watcher applicability, lease/descriptor, occupancy, headroom, build/model/table hashes; reviewer checks evidence. | Bounded preflight, elapsed time host-dependent. |
| M3 offline replay | Implementer/reviewer finish qualified supervisor, all-16-case dependency/executability proof and production binding; authorized Linux operator qualifies kernel behavior; author decides if a protocol alternative is needed. | Multiple engineering days plus site qualification. |
| M11 D8 and B2 ranking | Implementer and reviewer finish the gate and authorized protected training-reader coverage; author confirms D8. B2 has its own implementation and review. | Gate and reader implementation/review hours or longer; roughly 1–3 engineering days for B2 plus review and author response. |
| M10 HK1 | The author resolves the proposed F/C/D, accounting start, budget, T_max, shape and STOP-marker values (Q19). After the accepted engineering guard fixes, the authorized HoreKa operator verifies the reviewed PLAN checkout, accounting latency, Slurm visibility, `PrivateData` and shared lock before enabling the one switch for its applicable engineering scope. | Author response and site-dependent elapsed time, including accounting lag. |
| M10 EVIDENCE authorization | Implementer supplies the reviewed HK6/HK7/J5 EVIDENCE phase path, connects an adopted committed author-note verifier and establishes manifest/work-scope binding; author approves the note after prerequisites, and reviewer checks the exact checkout. The work-identity inventory identifies later runbook templates, Slurm mode and audit shard/merge as missing in its inspected scope; these are separate from this request's §3 items 1–2. The switch alone does not enable EVIDENCE. | One to several engineering/review days for the gate and binding, plus later template work, author response and phase timing. |
| M10 residual authority and DEADLINE scope | The reviewed tool accepts a caller-selected PLAN as a process boundary and refuses exact recorded DEADLINE manifest hashes; a different manifest can represent the same work. HK1 operator and reviewer verify the pinned PLAN and coordinate semantic no-retry across all submission routes. | Bounded HK1 verification; any stronger binding requires separate implementation and review. |
| P.3a template provenance | Authorized operator inspects preserved attempt-1 manifests and corresponding wrapper/encoder code; reviewer compares evidence. | Bounded host inventory; depends on record availability. |

All author options, recommendations and paste-ready responses are in `docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261105.md`, ordered by B1 unblocking priority. Nothing in that list is an author decision.
