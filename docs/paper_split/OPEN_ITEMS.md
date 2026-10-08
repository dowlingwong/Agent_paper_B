> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the Paper B open items (B1–B6), the B decisions and the B housekeeping.
> The source copy in agent-checkpoint-intervention is the historical one.

# Open items — Paper B

As of 8 October 2026 for Paper B (RUNBOOK v2.4 plus the adopted decisions below).

This is the checklist of what is still open for B. [RUNBOOK.md](RUNBOOK.md)
remains the plan authority and [STATUS.md](STATUS.md) the progress log; this
file does not change either. To close an item: tick it, add the commit or record
that shows it is done, and add a [VALIDATION.md](VALIDATION.md) row where checks
ran. An item is not closed because it is planned.

Owner: **W** = work any agent can do · **D** = decision by Dowling ·
**X** = needs Ada access or another external step.

---

## Paper B — ICML 2027 target

### B1. Blocker: task realism (attempt 2, unsealed)

- [ ] **Task redesign, attempt 2** (W/D, P-B1). Attempt 1 remains a recorded
  failure: typical R1/R4 failed. Task-dependent Ada work remains blocked;
  D-F10 permits the stated model-free exception only.
- [x] Preserve attempt-1 code/results at the author-approved `b09c85a` citation
  baseline; do not rerun it for parameter search.
- [x] Complete the single AI-assisted challenge and retain its original NO
  verdict; written dispositions are in the [revised design](../../experiments/paper_b/task_cc_v2/ATTEMPT2_DESIGN.md).
- [x] Record the author’s partial D-ATT2 adoption: end-of-run R4 (> .02),
  behaviour changes, never-as-control (144 leaves), symmetry-aware metric,
  information surfaces, CPU caps and execution-bug-only repairs.
- [x] Revise cohorts: development **0–7 realism, 8–15 screen, 16–47 pilot**;
  test reserved for final collection under a law frozen before final outcomes.
  No final test generation before that law freeze.
- [x] Define balanced screen: four mismatch × migration classes, two families
  each, `k=(family_index−8) mod 4`, assigned before generation. Pilot uses its
  separate independent random law, explicitly labelled **artificial mixture**.
- [ ] **Balanced realism families: adopt / decline** (D). Bracketed choice is
  unanswered; neither balancing nor random mixture is silently adopted.
- [x] Specify candidate fitting-schema provenance and audit conversion
  `w_canonical=M_fittedᵀw` before `D=M_currentᵀ`; preserve schema metadata in
  executable round-trips and rejection/fork restoration.
- [x] Prepare [pre-seal reach record](../../experiments/paper_b/task_cc_v2/ATTEMPT2_PRESEAL_RECORD.md):
  author-supplied **7/8 (.875)** for `a2-r0`…`a2-r7`; not recomputed here.
- [ ] **STOP D-ATT2:** author inspects revised B1/B2 and diff and approves the
  complete design before any seal, outcome code or generation. **Nobody
  evaluates RNG streams 20–23 before the seal.**
- [ ] Seal the approved design and pre-seal record; then implement and run
  realism once. No families added/redrawn to manufacture winners.
- [x] Execution bug defined by the author as a **test-demonstrable mismatch
  between code and sealed text**; each repair records the provision, a test
  failing before/passing after, and preserves completed evidence. No substantive
  post-outcome mechanism/threshold tuning.
- [ ] failure disposition (adopted P-B1): if attempt 2 fails substantive
  realism criteria, stop this task/verifier setup and drop its ICML 2027
  route. Execution bugs may be fixed transparently; mechanisms and thresholds
  are not tuned against the result.

### B2. Before B can be called design-ready

- [x] Independent AI-assisted review of the imported B controller/evaluation
  code and bounded repair recheck, committed in `d9c5e30`. All four new findings
  closed; scoped core verdict **design-ready: yes**. 212 control tests pass;
  original findings/evidence retained in [review](B2_REREVIEW_20261008.md) and
  [recheck](B2_REPAIR_RECHECK_20261008.md). No source/Paper A checkout was read.
- [ ] Novelty and overlap verdict on B_NOVELTY_MEMO.md and
  [PRIOR_DISCLOSURE.md](PRIOR_DISCLOSURE.md) §7 (D). B1 realism, code correctness
  and author novelty remain distinct; overall readiness is withheld.
- [ ] Read BAVAR / Strategic Verification (preprints.org 202608.2057) by hand,
  then fix or confirm related work and comparator description (D).
- [ ] Build F10 qualification/screen tooling (`run_screen.py`,
  `bind_runtime_artifacts.py`) (W). D-F10 permits pre-B1 **model-free parts
  only**: no task-mechanism-specific code, live mode refuses, no endpoint
  dispatch. Task-dependent/live work waits for B1 and later gates. Shelve this
  tooling if attempt 2 fails; it never justifies another attempt.

### B3. Design work (RUNBOOK §14.2)

- [ ] **B-TKV1** Separate the offline collection budget from the online
  verification budget, and record which is held fixed in each comparison (W).
- [ ] **B-TKV2** Specify a context-conditioned shrinkage baseline with
  development-only fitting (W).
- [ ] **B-TKV3** Fixed-cost `N`/`R` diagnostic. Optional, only after the pilot.

### B4. External gates (each needs author authorization)

- [ ] Bind Devstral-Small-2-24B on Ada (weights/tokenizer hashes, quantization,
  server build, decoding, harness commit, task generator, verifier) (X).
- [ ] Qualify both lanes (X).
- [ ] 96-leaf screen → 384-leaf pilot (X).
- [ ] Route decision: COMBINE / CORE_ONLY / narrow report; then freeze the final
  design and authorize its budget (D).
- [ ] Contract fields still null: model/runtime hashes, split manifest,
  qualification report, authorization.

### B5. Venue timing

- [ ] **15 November 2026:** both runtime lanes qualified, with the B1/B2
  blockers closed. If missed, retarget B beyond ICML 2027 (adopted P-B2).
- [ ] **30 November 2026:** screen and pilot complete, route selected, final
  design frozen and budget authorized. If missed, retarget B beyond ICML 2027.
- [ ] Recheck the ICML 2027 CFP when published and move these cutoffs earlier if
  needed. These are new resource cutoffs, not reinstated historical dates. Do not
  compress validation to keep the venue.

### B6. Configurator / DAC framing (proposed 4 Oct; B_DAC_CONFIGURATOR_AMENDMENT_20261004.md)

- [x] D-DAC1: DAC framing only adopted by author on 8 Oct (RUNBOOK §16);
  both deviations stated in manuscript §2; §14.2 caveats unchanged.
- [ ] D-DAC2–6: choose primary encoder slot (Kev or CLM) and size; freeze
  questions/max_chars; choose feature set and projection before pilot outcomes (D).
- [x] B-DAC4 history capture **on the scripted executor path**: H₁/H₂ from
  session entries (`control/executor.py`, imported at `a93e2b7`; 207 control
  tests revalidated at `1554732`, takeover record `3f93c31`).
  - [ ] Pi-native history translation and capture remain open (IP2; no live
    session has been exercised). This does not complete history capture on all paths.
- [x] B-DAC5 **draft scaffold fields** in `protocols/paper_b/contract_v3.yaml`
  (import `a93e2b7`; both draft launch refusals revalidated in `3f93c31`).
  - [ ] Adopted values, bindings, encoder extensions and qualification remain
    open pending D-DAC1–6 and later evidence; v2 stays active and v3 draft.
- [ ] B-DAC6 configurator provenance in `matching_report` (W).
- [ ] B-DAC7 encoder binding: Kev pinned revision offline on the Mac, or CLM
  pooling server and head hash on Ada (X/D).
- [x] CPU scaffold and 22 tests (4 Oct).

---

## Standalone repository

Open items specific to this repository, created by the Phase 1–2 copy from
`agent-checkpoint-intervention` at S = 4154f153 (7 October 2026). None of these
blocks the CPU checks; the first three block the live lane.

- [x] **Missing infrastructure-runbook citations resolved** under author
  D-INFRA-RB (8 Oct): `control/executor.py` and
  `experiments/paper_b/task_cc_live/cc_live_agent.py` now cite plan v3.1 IP2
  and execution Stage 4.1. The author reports no committed copy in any source
  branch, with the code originating in `9de9c908`; not independently searched
  by takeover. A later supplied copy is historical, not a prerequisite.
- [ ] **`verify_vendored_pi.py` fails at S.** The verifier reports three files
  under `third_party/pi/packages/coding-agent` changed in `6d4642b6` that are
  missing from `protocols/pi_local_modifications.yaml`. The failure is inherited
  unchanged; do not "fix" the ledger to silence it.
- [ ] **Live-lane pieces that do not exist yet:** B's Pi extension (three tools),
  B's system-prompt file, `endpoint_b.json`, and the Pi-backed executor path
  itself (plan v3.1 IP2). The pinned Node v22.19.0 runtime and a built Pi are
  host prerequisites.
- [ ] **Six files named in `runtime_identity.RUNTIME_GLOBS`** are not in this
  repository. Decide whether they travel with the Pi-backed executor or stay
  host-local.
- [ ] **`run_local_soak.py` other defaults** point at E0 files that are not
  copied. They are only reached by the E0 soak path, not by B's checks.
- [ ] **`checkpoint.py` reads `protocols/e0_instrument_protocol.yaml`** in one
  code path; that file is not copied. Reachable only from E0, not from B.
- [ ] **Starting points in the source repository:** `experiment_scaffold/configs/`
  endpoint and prompt templates, `experiments/paper_a/panel_v2/` and
  `experiments/paper_a/ada/` as live-run templates. They stay in the source.
- [ ] **Tests for the copied Pi stack stay in the source repository**
  (`experiment_scaffold/tests/test_pi_*`, `test_model_client.py`,
  `test_registered_tools.py`, `test_device_attestation_launchers.py`). Port them
  if the live lane is built here.
- [ ] **Card selection for B's Ada runs** is undecided (ports 18081/18082 are
  assigned to E0; A's E-R2 holds 18083). Confirm ownership on the host.
- [x] **Stale 5–6 October B records and §B6** reconciled in the Stage 1
  STATUS/VALIDATION entries and scoped B-DAC4/5 checkboxes; evidence is the
  committed plan v3.1, imported executor/ledger/v3 files, and current takeover
  checks. Historical checks remain labeled source-reported, not rerun today.
- [ ] **`make doctor` / `make bootstrap`** are named in copied files but absent
  from this repository's Makefile.
- [ ] **Make targets that rewrite tracked files:** `make paper-b`, `make smoke-b`
  and `make check-release-b` rewrite files inherited from S
  (the PDF, `results/paper_b/smoke_latest/`, `release/check_release_b.json`).
  Restore them with `git checkout -- <files>` until the targets write elsewhere.
  `make release-b` writes only the ignored `release/paper_b/`.
- [ ] **`*.jsonl` in `.gitignore`.** The inherited rule ignores `*.jsonl`; a
  new exception `!results/paper_b/**/*.jsonl` keeps B's governance ledgers
  (`events.jsonl`, `timing.jsonl`) committable under `results/paper_b/`.
- [x] **GitHub repository name and first push.** `Agent_paper_B` is the
  author-specified remote; `git ls-remote origin main` verified `1554732`
  and then Stage 0 `3f93c31`. This supersedes the copied no-remote statement.
- [ ] **Phase 3 in the source repository** (removing B from
  `agent-checkpoint-intervention`) waits for Paper A's submission.
- [x] **Paper B authority switched** by the author's 8 October kickoff:
  all takeover work lands in `Agent_paper_B` (Stage 0 `3f93c31`). No post-S
  inspection or modification of the off-limits source repository was performed.

---

## B housekeeping

- [ ] Record the R2 fix round in STATUS and VALIDATION.
- [ ] Pre-existing failures outside the split: 89 failing/erroring test IDs
  (recorded in `L1_BASELINE.md` in the source repository at S), and `protocols/`
  registration tests (F2). These do not block B but are not claimed to pass.

---

## Adopted decisions (4 October, B)

| ID | Decision |
|---|---|
| P-B1 | One new bounded task attempt; attempt 1 preserved; mechanisms, thresholds, budget and failure disposition frozen before running; failure stops this setup and its ICML 2027 route. |
| P-B2 | Internal cutoffs 15 Nov (both lanes qualified) and 30 Nov (pilot done, route chosen, design frozen, budget authorized); missing either retargets B beyond ICML 2027. |

## Author decision table — 8 October takeover

[Decision sheet](B_DECISION_SHEET_20261008.md); [fresh-session B2 prompt](B2_REREVIEW_PROMPT_20261008.md).
The five now items below are author decisions, recorded in RUNBOOK §16.
All other rows remain pending; none is an evidence-run authorization.

| ID | Needed | Status / recommendation |
|---|---|---|
| D-PLAN | now | adopted 8 Oct: adopt with three corrections; no GPU/model work |
| D-DAC1 | now | adopted 8 Oct: adopt framing only; caveats unchanged |
| D-F10 | now | adopted 8 Oct: yes with stated model-free limits; shelve on failure |
| D-INFRA-RB | now | adopted 8 Oct: re-point to plan IP2 and execution Stage 4.1 |
| D-ROUTE | now | adopted 8 Oct: after pilot; reject after-screen recommendation |
| D-DEC1 | Stage 4 | pending; positive temperature and recorded transported seeds |
| D-CAP1 | Stage 5 | pending; separate engineering allowance; explicit qualification accounting |
| D-RES1 | Stage 5 | pending; bounded supervised infrastructure resumption |
| D-ADA1 | by 20 Oct | partially answered: author authorized Ada B-only access/clone; completed through existing SSH key. Card, port and execution plan remain pending |
| D-DAC2 | after measurement | pending; conditional Kev-4B primary, CLM ablation |
| D-DAC3–6 | before pilot | pending; questions/max_chars, features, projection, Kev size |
| D-REF1 | Stage 4 | pending; descriptive oracle/random references |
| D-GOV1/2 | Stage 5 | pending; schema/ledger/adjudication, default no panel |
| D-PT1/2/3 | after screen | pending; post-freeze extension and separate budget |
| B2-N / B2-BAVAR | before 15 Nov | pending; author's verdict and hand-reading |
| D-ATT2 | Stage 2 | NOT APPROVED as written; partial subitems adopted, required revisions prepared; balanced realism adopt/decline and complete revised approval pending |
| Evidence authorizations | per phase | absent; author must create and commit each himself |

Stage 1's decision STOP is closed: the author answered all five now items,
recorded here and in RUNBOOK §16. D-ROUTE retains route after pilot; plan
IP10.4 and execution Stage 8 now agree. Citation repairs are recorded above.
B1/B2 and all live gates remain open. Next Stage 2 STOP is D-ATT2: author
approval of the independently challenged design before sealing and outcome
code. Ada access/clone is authorized; GPU/model work remains unapproved, and evidence phases require their
own author-created, author-committed authorization records.

## 8 October — current B2 and attempt-2 disposition

[B2 original review](B2_REREVIEW_20261008.md) preserved; [repair recheck](B2_REPAIR_RECHECK_20261008.md) resolves both major and both minor findings. Scoped code verdict is design-ready yes, with 212 control tests passing. Author B2-N/B2-BAVAR remain open.

[Attempt-2 draft](../../experiments/paper_b/task_cc_v2/ATTEMPT2_DESIGN.md) includes proposed fixes to the [single challenge](ATTEMPT2_CHALLENGE_20261008.md). D-ATT2 is the next STOP; no hash, task outcome code or run exists. Proposed changes include SGD instead of stumps, canonical-prefix/raw-batch deployment audit, fixed eight-slot tails, exact replay/aggregation rules, symmetry-aware family audit, and terminal budget-matched R4 comparison with unchanged .02 threshold. None is adopted by this status record.

## D-ATT2 revision decision — 8 October 2026

The author rejected the previous complete draft and requested a pre-seal revision/diff. The B1/B2 section above records the supplied corrections and partial adoptions. The new test families are final-only, screen is development-balanced, pilot is a separate artificial mixture, and audit weight conversion precedes decoder replacement. The complete design remains unapproved; no seal/RNG/task execution is authorized.
