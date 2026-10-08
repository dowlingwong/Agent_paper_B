> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the Paper B open items (B1–B6), the B decisions and the B housekeeping.
> The source copy in agent-checkpoint-intervention is the historical one.

# Open items — Paper B

As of 7 October 2026 for Paper B (RUNBOOK v2.4 plus the adopted decisions below).

This is the checklist of what is still open for B. [RUNBOOK.md](RUNBOOK.md)
remains the plan authority and [STATUS.md](STATUS.md) the progress log; this
file does not change either. To close an item: tick it, add the commit or record
that shows it is done, and add a [VALIDATION.md](VALIDATION.md) row where checks
ran. An item is not closed because it is planned.

Owner: **W** = work any agent can do · **D** = decision by Dowling ·
**X** = needs Ada access or another external step.

---

## Paper B — ICML 2027 target

### B1. Blocker: task realism (TASK_REALISM_REPORT.md)

- [ ] **Task redesign, attempt 2** (W, under adopted P-B1). The F9 check FAILED
  after its one allowed repair: for the typical behaviour, no family is now-best
  (R1) and the verifier never beats ordinary refitting (R4; best −0.04 U). Ada
  tooling (F10) is stopped. See P-B1.
  - [ ] attempt 1 kept unchanged as a recorded failure;
  - [ ] before running: freeze where verification gets diagnostic value beyond
    refitting, where waiting has a real information-versus-delay tradeoff, and
    the qualification thresholds;
  - [ ] no families added just to manufacture now/later/never winners;
  - [ ] failure disposition (adopted P-B1): if attempt 2 fails substantive
    realism criteria, stop this task/verifier setup and drop its ICML 2027
    route. Execution bugs may be fixed transparently; mechanisms and thresholds
    are not tuned against the result.

### B2. Before B can be called design-ready

- [ ] Re-review the 28 Sept R2 fix commits (`d6b3bd3e`…`b9b56265`) independently
  against the 27 Sept review, whose verdict was "design-ready: no" (blockers C1,
  M1/M2, N2/N3). The re-review must establish that the evaluated controllers can
  differ, that the corrected continuation target addresses the bias, and that
  the reported allowance/tax matches the stated analysis (W, separate session).
- [ ] Novelty and overlap verdict on B_NOVELTY_MEMO.md and
  [PRIOR_DISCLOSURE.md](PRIOR_DISCLOSURE.md) §7 (D). Task realism and
  implementation correctness are separate gates; both must pass before
  "design-ready".
- [ ] Read the BAVAR / Strategic Verification preprint (preprints.org
  202608.2057) by hand; automated access is blocked. Then fix or confirm the
  related-work text and the comparator description (D).
- [ ] Build the F10 qualification/screen tooling (`run_screen.py`,
  `bind_runtime_artifacts.py`) only after B1 passes (W).

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

- [ ] D-DAC1–6: adopt the DAC framing; choose the primary encoder slot (Kev or
  CLM) and size; freeze the Kev question set or the CLM variant; choose the
  primary feature set and projection. All before any pilot outcome (D).
- [ ] B-DAC4 history capture in the tree driver and live task. Prerequisite for
  any text encoder (W).
- [ ] B-DAC5 contract v3 configurator fields, once D-DAC1–6 are decided (W, then D).
- [ ] B-DAC6 configurator provenance in `matching_report` (W).
- [ ] B-DAC7 encoder binding: Kev pinned revision offline on the Mac, or CLM
  pooling server and head hash on Ada (X/D).
- [x] CPU scaffold and 22 tests (4 Oct).

---

## Standalone repository

Open items specific to this repository, created by the Phase 1–2 copy from
`agent-checkpoint-intervention` at S = 4154f153 (7 October 2026). None of these
blocks the CPU checks; the first three block the live lane.

- [ ] **Missing `B_INFRA_RUNBOOK_20261005.md`.** `control/executor.py` and
  `experiments/paper_b/cc_live_agent.py` cite
  `docs/paper_split/B_INFRA_RUNBOOK_20261005.md`, which exists in no ref of the
  source repository. Commit it from the machine that holds it, or re-point both
  citations.
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
- [ ] **Stale 5–6 October B records and §B6** (plan v3.1 IP0 step 1): add the
  5–6 Oct entries to STATUS/VALIDATION and update §B6's B-DAC4/5.
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
- [ ] **GitHub repository name and first push.** The author creates the remote
  and chooses its name; there is no remote in this repository.
- [ ] **Phase 3 in the source repository** (removing B from
  `agent-checkpoint-intervention`) waits for Paper A's submission.
- [ ] **Paper B work after S still lands in the source repository** until the
  author switches to this one. Reconcile before treating this repository as
  authoritative.

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
