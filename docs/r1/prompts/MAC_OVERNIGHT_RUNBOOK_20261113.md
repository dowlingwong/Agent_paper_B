# Mac-local overnight runbook — night of 13/14 November 2026

**Written 13 Nov 2026 by the chat session (Claude); AI-assisted; self-checked, not independently reviewed.** Start by having a freshly spawned independent reviewer read this file. Begin after it writes *accepted*.

You are the **Mac-local agent** for Paper B (route R1). You do **desktop work only**: code, tests, analysis and documents. You have no SSH access to any server. The experiment agent runs everything on TASL-2/TASL-7, and the cluster agent runs everything on HTCondor/HoreKa. The author is asleep: do not wait for answers. Write each decision you need into the question list (§9) with options, a recommendation and a paste-ready answer, then go on. Report to the author in **Chinese**; files in **English**.

---

## 0. Ground rules

### 0.1 Standing rules (unchanged)

- **No deletion.** Retire by moving into `_to_delete/` next to the item and say so. Never delete or overwrite evidence, STOP scenes, logs or another track's files.
- **Never touch what you did not start.**
- **Independent review at every unit.** Spawn a fresh reviewer with the goal, this runbook, the inputs and the outputs, but not your conclusions. Fix or answer each finding and re-check with the same reviewer until it writes *accepted*. You never accept your own unit.
- **Git.** Work in your own worktrees, never in `~/Documents/agent_paper_B` itself. One branch per unit; the names are given below. Never push `main`, `r1` or `exam-x-*`, and never force-push. Commit author `Dowling Wong <wangdowling@gmail.com>`, with the attribution lines you were given. If you cannot push, deliver bundles plus `READY.txt` under `Claude outputs/` (branch, SHA, review file), as before.
- **Seeds and data.** Never read C3 label seeds 7001–7005 or evaluation seeds 7006–7010 for analysis. Never let exam seeds (instances 9001 and up, audits 9101–9104 and 9201–9210) enter a C3 sweep. Read no sweep-2 or T1 label table.
- **Secrets.** Never read `~/.config/r1/secrets.env` or any key file.
- **Disk.** Keep temporary files in `/tmp` and check free space before each unit. Last time the VM disk filled up. If less than 5 GB is free, stop starting units and report.

### 0.2 Not authorized tonight

Any server access; B2, X.7, sweep 2; any change to a frozen pin or an author rule; setting `approved: true`; pushing into `mac-int-20261107` itself; committing an author row (you write drafts only).

### 0.3 Things running elsewhere tonight (do not depend on them)

- **B1 `_d`** runs on TASL-7 (run `7912_20261113_d`) and is expected to finish around 06:00–11:00 CET.
- **The cluster agent** works through `prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` (branch `docs/runbooks-14nov`). Its report arrives in the morning.
- **Track S** is paused on TASL-7.

### 0.4 Author answers to Q1–Q10

The author may paste answers to the 10 November questions (`reports/MAC_OVERNIGHT_QUESTIONS_20261110.md` on `origin/mac-overnight-report-20261109`) into your start message. **Act only on answers that appear in the start message.** For any question without an answer, the unit that needs it does only the parts the answer does not affect, and the question stays in the question list.

## 1. Unit 1 — D8 gate changes from the author's answers (C3 sweep-2 prerequisite; highest priority)

**Base.** `origin/mac-m11-d8-20261109` @ `83a12b44`. **Branch:** `mac-m11-d8-v2-20261114`.

Apply exactly what the answers to Q1–Q5 say, in `r1/c3/gate.py` and its tests:

- **Q1.** Under answer (b), the per-suite partial-T1 rule applies to leave-one-suite-out only, not to the whole gate. The confirmation row's wording changes with it.
- **Q2.** Under answer (b), add a dev-split eligibility rule: a node is eligible only if its **dev** denominator is positive with dev z ≥ the stated threshold. The test split is untouched. Then:
  - re-run the whole-gate STOP-probability simulation of `reports/M11_D8_GATE_20261109.md` with the rule and report the new probabilities next to the old ones (0.52 and 0.66);
  - keep reporting the offending nodes (option (c)).
- **Q3.** Set `NUMPY_VERSION` to the stated version, and record the named environment in the gate's header.
- **Q4.** Under answer (b), add the STOP below the stated minimum of test instances per node. **Before** implementing it, check the planned test-instance counts per T1 node (C3 design / Track G plans). If any planned node would fall below the minimum, do not implement; put it in the question list.
- **Q5.** No code change under "keep".

Then:
- update the known-answer synthetic tests;
- recompute the gate's SHA-256;
- redraft `proposals/R1_BX_D8_CONFIRM_DRAFT_20261114.md` with the new commit, SHA and blob (do not commit it as an author row);
- check that every sweep-2 reader still refuses without the exact confirmation row.

Independent review until *accepted*.

## 2. Unit 2 — HTCondor adapter (desktop part)

**Branch:** paper `mac-htcondor-20261114` from `origin/mac-int-20261107`.

Build `r1/scripts/htcondor/` in the style of `r1/scripts/hk2/hk2_submit.py` and `hk2_config.json`:

- **Submission.** A JDL generator from a small manifest (`htc_job/v1`): image, CPUs, memory, disk, walltime, GPUs, an exact GPU device name (required when GPUs > 0), site constraints, local vs remote, accounting group, executable and arguments, input and output files.
- **Guards.**
  - `real_submission_enabled` defaults to false.
  - `--dry-run` renders the JDL and runs `condor_submit -dry-run` when available.
  - `RequestGPUMemoryMB` is refused (whole GPUs only).
  - Over 100 MB of transfer input is refused.
  - A GPU job is refused without `+RemoteJob = True` and an exact `GPUs_DeviceName`.
  - Config statuses use `ruled:` / `measured:` / `proposed:`, as in `hk2_config.json`.
- **Queue-time logger.** Parses an HTCondor job event log (000 submit, 001 execute, 004 evicted, 005 terminated, 012 held, 013 released) into the row format of the cluster runbook §4.2. Test it on synthetic logs.
- **Resume-safe units.** A helper that marks a unit complete only after its output manifest is written atomically. A restarted job (eviction, or one of up to 6 starts) detects completed units and skips them.
- **Outcome mapping for the M10 classifier**: eviction, preemption, a hold for memory or walltime, and a container pull failure are `infrastructure_failure`. A CUDA OOM stays `divergent` (Q8.1) only because the GPU device name is pinned per table; the adapter refuses a table without one.
- **GPU identity.** HTCondor sets `NVIDIA_VISIBLE_DEVICES` in a short UUID form. Make the M10 runner accept it: resolve it against `nvidia-smi -L` inside the job, record the full UUID, and refuse if it is ambiguous.

Tests use fakes only (no `condor_*` binaries needed). Write a hand-off `reports/HTCONDOR_ADAPTER_HANDOFF_20261114.md` for the cluster agent. Independent review until *accepted*.

## 3. Unit 3 — M10 next steps: v2-diff into manager and campaign

**Base.** Paper `mac-trackg-20261109` @ `f56f7f35`; harness `r1-local-trackg-20261109` @ `76bc49f2` (from the overnight bundle if not on origin). **Branches:** `mac-trackg-v2-20261114` and harness `r1-local-trackg-v2-20261114`.

1. Wire `manager_proposal/v2-diff` into one manager and the campaign path behind an explicit flag.
2. Add the repeated-timeout cap: after 2 timeouts of the same code state the proposal becomes `divergent`, with reason `timeout_repeated`. Act on this only if the author's Q8 answer accepts it; otherwise implement it behind a default-off flag and leave the question open.
3. **The T0 path must stay byte-identical**: the `manager_proposal/v1` campaign comparison from the 9 Nov kit must still pass.

Independent review until *accepted*.

## 4. Unit 4 — Track P: the missing training stages (code and synthetic tests only)

**Base.** `origin/mac-int-20261107`. **Branch:** `mac-trackp-rl-20261114`. **Spec:** `docs/r1/TRACK_P_POST_TRAINING.md` §6.3 (R-A), §6.4 (R-B) and §6.5 (Stage D, DAgger).

1. **Inventory first.** What of R-A, R-B and Stage D already exists in `r1/c3/train/`? (Tonight's check found no GRPO or DAgger code.) Write `reports/TRACKP_RL_INVENTORY_20261114.md`.
2. **R-B (GRPO).**
   - Group sampling;
   - the group-relative advantage;
   - the reward rules of §0.2;
   - LoRA on the existing wrapper.

   Use the packages already pinned in the Track P environment. If GRPO needs a package that is not pinned (for example `trl`), do **not** add it: implement the loss in `r1/c3/train/` and put the dependency choice in the question list. The SFT warm-up data path for the DeepSeek demonstrations (§6.4 step 2) is code only: **no API call tonight**.
3. **Stage D (DAgger).** A data-aggregation loop over the offline environment (`r1/c3/env.py`, `OfflineBanditEnv`), using the expert labels as specified. Synthetic environment only.
4. **R-A.** Only if the inventory shows it missing or partial, and only what §6.3 specifies.

Tests:
- known-answer checks of the advantage and the loss on toy groups;
- a tiny end-to-end run on the existing `tiny.py` or a synthetic model on CPU;
- no label seeds and no real tables.

Independent review until *accepted*.

## 5. Unit 5 — B2 hand-off draft (not armed)

**Branch:** `mac-b2-handoff-20261114` from `origin/mac-b1-20261107`. Draft `proposals/B2_HANDOFF_DRAFT_20261114.md`:

- the B2 procedure from `prompts/PORTAL_EXAM_RUNBOOK.md` and RUNBOOK X.6 (Stage B2: finalists, final audited Y with K = 10, audit seeds 9201–9210, fresh instances 9011+);
- the run-HEAD note, review, author gate, occupancy check, preflight and handover pattern of `B1_RESTART_HANDOFF_D_20261113.md`;
- B2's inputs from B1's accepted result (the ranking under `x5_rule_v2`), written as placeholders;
- the marker transition after B1's normal end;
- what B2 computes (final Y);
- the STOPs carried over from B1's model-output rules.

State clearly that it is **not armed** until the author approves B2 after reading B1's report. Independent review until *accepted*.

## 6. Unit 6 — appendix disclosure drafts

**Branch:** `mac-appendix-20261114` from `origin/mac-b1-20261107`. One section per post-hoc change to B1:

1. R4-H2 (anchor ordering made descriptive);
2. truncated output counted as an invalid trial, plus the 16,384-token cap;
3. model-output STOPs turned into invalid trials (M1–M21), plus the proposal journal.

Each gets the original criterion, the trigger (run, date, evidence path), the change, its date and PLAN row, and what it cannot affect. Leave placeholders for the `_d` counts: invalid trials by class and candidate (for example olmo31_32b's directive mismatches). Independent review until *accepted*.

## 7. Unit 7 — integration trial

**Branch:** `mac-int-trial-20261114`, a **trial** from `origin/mac-int-20261107`. It is not the integration itself.

1. Merge the accepted branches in a proposed order: M3 → M4 → M11 D8 (v2 from Unit 1 if accepted, else the 9 Nov one) → W2 → M10 kit (and v2 from Unit 3 if accepted) → Track P RL (Unit 4, if accepted).
2. Run the full paper test suite after each merge, and record conflicts and the failure set against the base.
3. Do not merge the B1 exam branches (`mac-b1-*`, `ops-b1-*`): they are run checkouts.
4. Write `reports/INTEGRATION_TRIAL_20261114.md` with the proposed order, the conflicts and their resolutions, and the test deltas.

The author decides the real integration. Independent review until *accepted*.

## 8. Unit 8 — small items

1. **M15 standby patch** on `mac-b1-m15-standby-20261114` from the `_d` run checkout `origin/ops-b1-restart-d-20261113`: raise the observer timeout from 60 s to 180 s, with tests and a PLAN row draft. It is used only if `_d` stops on M15. Independent review.
2. **M4 step 4 (DTQ tool).** The Track S paper commit `d10b05b7` that it needed is now on origin (in the history of `mac-tracks-a2u-stale-20261111`). On `mac-m4-dtq-20261114` from `origin/mac-m4-20261109`. Independent review.
3. **Q9 item 5** (only if the author's Q9 answer accepts it): the test-only harness fix that compares the L8 template test against the D28 start configs, on a harness branch from `a3fedbb`. Independent review.

## 9. Order, time and stopping

Order: Unit 1 (only if Q1–Q5 answers were given; otherwise skip to Unit 2) → 2 → 3 → 4 → 5 → 6 → 7 → 8. If a unit STOPs, record it and move on. Stop starting new units at 07:30 CET.

**Question list:** `reports/MAC_OVERNIGHT_QUESTIONS_20261114.md`.

## 10. Morning report (08:30 CET)

Write `reports/MAC_OVERNIGHT_REPORT_20261114.md` and a STATUS entry. Deliver everything (push, or bundles plus `READY.txt`). Then send the author a short Chinese message covering:
1. each unit: done / partly done / STOP, with branch, commit and review verdict;
2. the D8 confirmation draft (new SHA) and what the author still has to answer before pasting the row;
3. the questions.
