# Handover — Paper B (route R1): what exists, what is unfinished, what is not delivered

**Written 26 Nov 2026, 20:30Z, by the interim coordinator** (claude.ai chat session `session_01GRrwsCm2qxekvutQfX6Dr9`).
**`main` at the time of writing: `4cb92b70`.** AI-assisted (Claude). English in files; the author is addressed in Chinese.

This file is a view. `docs/r1/PLAN.md` §10 rows on `main` decide; where this file and a row differ, the row is
right. Nothing here is a decision. Facts this session did not check itself are marked *(verify)*.

**If you take over the coordinator role:** read §8 first (three things on `main` and off `main` contradict each
other), then replace the file `COORDINATOR` on this branch in one commit that names your session.

---

## 1. The work in one page

**Paper B.** Question (R1-ALIGN-OUTCOME, 26 Nov): at a matched worker-run budget and LLM-call cap, which control
decisions of a governed autoresearch loop raise the fresh-seed audited gain of a campaign, and by how much?

| Claim | Evidence it needs | State |
|---|---|---|
| Loop (headline) | Closed loop D.3 on T0: D.3a rule arms, D.3b learned arms (always run), D.3c on three T1 nodes (descriptive) | No campaign has run |
| C3 offline | The preregistered gate, read once (R1-SWEEP2-PREREG, gate v3.1; simulated power 0.36 at effect 0.3) | Unread. T0 labels complete; T1 labels not collected |
| C1 | Control errors of the default keep rule, from the fresh-seed audits of sweeps 1 and 2 | Audits complete; numbers not released |
| C2 | The one-step rule under noise; conditions for global optimality | Main text limited to statements that pass R1-PROOF-POLICY |

Nothing is established yet: the gate is unread, no arm is frozen, no closed-loop campaign has run. Paper B makes
no multi-step or RL claim (R1-BX-D9); the learned arms are forecasters (A3 tabular; A5 a small language model
trained by supervised fine-tuning, not started).

**Paper C** (follow-up, not on Paper B's critical path): when one-step control is enough and when modelling the
effect of an action on the later search pays. Infrastructure only (build phases P0 to P9 reviewed, 234 tests, on
branch `paperc-esyn-scaling-20261122`); engineering data only; no real-node run; no manuscript.

**Read next:** `canon/README.md`, `canon/PAPER_B_PLAN.md`, `canon/PAPER_C_PLAN.md`, `canon/COMPUTE.md`, the role files
under `canon/agents/`, and `docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md` (all on `main`).

## 2. Where things are

| Thing | Place |
|---|---|
| Repository | `dowlingwong/Agent_paper_B` (public: never write a credential). Harness: `dowlingwong/autoresearch_harness`, pin `a3fedbbd` |
| Decisions | `docs/r1/PLAN.md` §10 on `main`. New rows go before "## 11. Relation to Paper A", under a dated heading; rows are only added |
| Plans as views | `canon/` on `main` |
| Work order (draft) | `docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md` on `main` |
| Tasks, state, author list | this branch: `tasks/<role>/`, `STATE.md`, `AUTHOR.md` |
| Rows drafted today, not on `main` | branch `coordinator-rows-fg-20261126` (§4.1) |
| Signed notes | `docs/r1/authorizations/` |
| Drafts and proposals | `docs/r1/proposals/` (G.5 note draft, revision 13: `T1_G5_AUTHORIZATION_DRAFT_20261120.md`; expansion G.1b note draft: `G1B_X_T1_TASL_NOTE_DRAFT_20261126.md`; goal and metric alignment: `GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md`) |
| Manuscript | `papers/r1` (about 22k words; both gate outcomes written; result tables hold placeholders) |
| Branch inventory | `docs/r1/reports/repo_hygiene_20261126/branch_inventory.tsv` (203 remote branches, at `53b72f1d`) |

## 3. Progress by track

| Track | Done | Not done | Waits for |
|---|---|---|---|
| T0 labels (8 CPU nodes) | Both sweeps audited; label tables frozen; train/dev released (sweep 2: 850/422, sweep 1: 593/276); A3's T0 run reviewed | Test release rows | The arms-frozen record and the gate read |
| T1 noise floors (8 GPU nodes) | G.1b sealed for all eight; cross-host checks xc2 and xc3 PASS (seven nodes may audit on TASL-7) | — | — |
| T1 pilot | G.4b PASS: 126 of 180 proposals ran; liveness 0.62 to 0.82 | — | — |
| T1 labels (G.5) | Code and note draft revision 13 on `main`; pilot-basis PASS on TASL-2; projection 216.9 GPU-h | **No label run has started.** Signing sheet S1 to S14 for the author (§11.1 of the draft) not written; houseprice CPU-set check STOPped | The author's signature; the sheet (coordinator); the fix (local worker) |
| Expansion nodes (Titanic, ETTh1, MetaMaze, Forest Cover) | Kits and census PASS; spec on `main` (`sweep2/t1_tasl/g1b_tasl_x_spec.json`, sha256 `d0dce058…cfd238`, launch commit `7d0279d8`); four host checks and two determinism checks PASS; env row R1-T1-X-ENV | **Note not published; no run.** P2 (kit reviews' condition c1), P4 and the four gate lines are PENDING in the draft | The kit c1 disposition record (task `experiment/20261126-01`, not started) |
| Decision models (P.4, arm A5) | Runner, probe mode, charging and tokenizer staging on `main`; cluster tests T0 and T2 PASS | **No probe, no training.** T1 queued (job 760065, no machine matches); T4 and T6 STOP (§7); host-config fill not merged; phase-1 note unsigned | A GPU: the ETP pool has advertised no H200/H100/A100 since 24 Nov. A launch path outside HTCondor does not exist |
| Offline gate | Preregistered 21 Nov, amended 23 Nov | T1 train/dev release row; arms trained, selected, calibrated; arms-frozen record; the one read | G.5 labels; P.4 |
| Closed loop D.3 | Design of the runner (G1) and the audit (G6) accepted for code (review R6); pre-declaration draft revision 3 on a branch | **Runner, audit, outcome table and the arms A0R, FIXR3, EGATE, LADDER are not built.** Pre-declaration revision 4 not written; screening measurement not run | The screening smoke STOP (§7); revision 4; the author's signatures |
| Theory (C2) | Main-text statements limited by R1-PROOF-POLICY | Remaining proof checks before the gate read *(verify which)* | — |
| Manuscript | Draft built for both gate outcomes | Restructure after R1-ALIGN-OUTCOME: question first, decomposition table, D.3b unconditional, A0R and D.3c, procedure to the appendix (task `writer/20261126-01`, not started) | — |
| Paper C | Build P0 to P9 reviewed | Consolidation of three branches onto `main`; the two CPU measurements of R1-PAPERC-MEASURE-FIRST; the row R1-PAPERC-CORE; a manuscript | Lowest priority behind Paper B |
| Agents | Rows R1-AUTONOMY and R1-AGENT-RUNTIMES on `main`; this branch live; first tasks written | **No agent has picked up a task from this branch.** No `coord/<role>` report branch exists. The tmux coordinator and the server agent have not been started | The author starts them |

## 4. Written but not on `main`

### 4.1 Rows of 26 Nov (f) and (g), with the `canon/` changes that follow them

Branch **`coordinator-rows-fg-20261126`**, tip `52a3ce7a`: `main` `4cb92b70` plus four commits (one is the merge of
`main`). It is a proposed state of `main`, held for the author's word. **None of its rows is in force.**

| Row | Content | The author's word | Open |
|---|---|---|---|
| R1-AGENT-COMPUTE | The cluster agent and the experiment agent become one compute agent on DeepSeek with SSH to every host | Said in chat, 26 Nov ("cluster/experiment agent合成一个agent … 这个agent需要是deepseek") | "推 main" not given |
| R1-HOST-FREE | A job runs on any host and card that fits; only runs that are compared stay on one hardware class | Said in chat ("我们实验里能不和卡绑定就不和卡绑定"). The bindings (2)(a) to (c) are the coordinator's reading; the author may strike any | "推 main" not given |
| R1-CARD-SHARE | A job may share a card; an attempt lost to the card is repeated, never an outcome; the author accepts the reliability risk | Said in chat ("速度显存不对实验结果构成影响，可靠性我自己负责") | "推 main" not given |
| R1-NO-TIMEOUT | No wall-clock limit decides a check or an outcome | Said in chat ("把超时的所有限制…全部抹除") | **(2) is not what the author said.** See below |
| R1-STEP-ORDER | No calendar date decides anything; a step starts when the steps before it are complete | Said in chat ("把…日期限制都全部抹除，按步骤流程一步一步向下走") | "推 main" not given |

**The open choice in R1-NO-TIMEOUT (2).** The author said to erase every timeout. The draft keeps one: the per-run
budget of a proposal (T1: 3 × the slowest census record, R1-G1B-TIMEOUT; T0: 600 s). Reason given to the author:
that budget is part of the task (it makes a proposal that trains many times longer, or never ends, a failed
proposal), the frozen T0 labels and the G.4b pilot used it, and removing it means rebuilding and re-reviewing the
expansion G.1b spec and the G.5 code. Option **A** (drafted, recommended): the budget stays and never decides on a
shared card; a run that reaches it or runs out of memory beside another process is repeated, and counts only on an
attempt alone on its card. Option **B**: remove it as the author said. **The author has not answered.** If B,
rewrite (2) before anything is published; the row text now says A was "chosen by the author", which is not yet
true.

**Three additions by the coordinator that the author has not seen confirmed** (he may strike each): GPU-hour caps
become reporting thresholds (R1-NO-TIMEOUT (3)); ICML 2027's dates stop being rules of the plan (R1-STEP-ORDER (3));
the reviewed TASL launch code keeps its empty-card lease check until a unit changes it (R1-CARD-SHARE (5)).

**Checks on `52a3ce7a`:** PLAN additions only (0 removed lines against `main`); the D8 guard passes; the PLAN-reading
test subset equals the baseline (§10). One merge conflict was resolved (the header of `canon/PAPER_B_PLAN.md`; both
lines kept). The two role files replaced by the compute agent's are kept under
`canon/_to_delete/roles_merged_20261126/`.

**To publish:** the author's "签 (g) TIMEOUT A" (or B) and "推 main" in his own message. Then merge the branch
into `main` with a merge commit, re-run the checks, push.

### 4.2 This branch (`coord/coordinator`)

Task files that rest on the rows of §4.1 carry a first line "NOT IN FORCE until …". They are: `tasks/compute/*`,
`tasks/local/20261126-06` and `-07`, `tasks/writer/20261126-02`. Until the rows are on `main`, the tasks under
`tasks/cluster/` and `tasks/experiment/` stand as written and the dates of the rows on `main` apply.

### 4.3 Agent branches with work that is not on `main`

| Branch (tip) | Content | Review | Why not merged; next |
|---|---|---|---|
| `p4-hostconfig-fill-20261126` (`021c4eec`) | P.4 host configuration for the H200, all 19 placeholders filled | Two independent reviews: accepted | Its torch test files cannot run in the coordinator's container. Run `r1/tests/test_trackp_p4_runner.py` and `test_trackp_sft.py` on a host with torch (task `cluster/20261126-01`), then merge |
| `trackp-p4-cluster-20261125` (`8a9d48a1`) | One commit after the merged tip: the T4 CPU retry (job 760071) failed, `env3` is missing in the CPU image (rc 127); T4 STOP | None seen | Not merged; a STOP record. See §7 |
| `p4-staging-20261125` (`3bbf2f52`) | One commit after the merged tip: outage status and target dates added to the provisional evidence-phase note | None seen | Not merged. It writes target dates that R1-STEP-ORDER would withdraw; decide after §4.1 |
| `screen-measure-prep-20261126` (`01e50def`) | Screening measurement: pre-declaration, authorization draft, reviews (re-check accepted), preparation report; contains `mac-screen-measure-20261123` and `smeas-smoke-result-20261123` | Pre-declaration accepted; the preparation ended in a STOP | Engineering smoke STOP (§7). After the diagnosis: bring onto `main`, smoke, the author signs, run |
| `mac-d3-predecl-20261122` (`a24a55bf`) | D.3 pre-declaration and D.3a authorization drafts, revision 3; diff checks accepted (round 4) | Accepted for revision 3 | Superseded in content by the rows of 26 Nov (d): revision 4 must add A0R, D.3b unconditional, A5 − A3, the secondary outcomes, the reference rows, D.3c. Task `local/20261126-03`, not started |
| `mac-controls-pos-20261123` (`25d5a510`) | Positive control (R1-CONTROLS-ROW): code, results, reading | Accept with minor; a correction round was pushed; no acceptance of the corrections seen | Not merged *(verify whether a re-check exists)* |
| `mac-screening-test-20261122` (`e7392a61`) | Ancestor–descendant screening test (R1-D3-CHOICES (1)) | Accept with minor; corrections pushed; no re-check seen | Not merged *(verify)* |
| `mac-t5-shared-20261122` (`d0ef5282`) | T5 theory re-run with a shared-component error model | None seen | Not merged *(verify whether it is still wanted)* |
| `htc-image-v2.2-20261124` (`667bb9c2`) | Dockerfile and workflow of image v2.2 | Round 2 accepted | Its Dockerfile and workflow differ from `main`'s *(verify whether `main` should carry them; the image itself was built and is pinned by digest)* |
| `ops-tasl-20261116` and other `ops-*` branches | Raw operator records of the TASL chain and the sweeps | — | Kept unmerged as evidence branches; see the inventory |

The full list (48 branches not merged at `53b72f1d`) is in the branch inventory. This session classified only the
ones above.

### 4.4 Paper C

Three lines that are not on `main` and conflict with each other: `paperc-esyn-scaling-20261122` (the main line; 18
R1-PAPERC rows live only in that branch's PLAN), `codex/paperc-theory-20261117`, `mac-paperc-rl-20261121`. The
consolidation onto current `main` has not started.

### 4.5 `codex/layout-flatten-preview` (`20f39a52`, pushed 26 Nov 19:04Z)

Moves 12,378 files out of the `r1` directory layer. A preview, not a unit. The row R1-LAYOUT-FLATTEN (27 Oct) sets
the conditions: one batch, every agent at a STOP and no evidence job running, all accepted branches merged first, a
committed old-to-new path map, identical test outcome ids before and after, an independent review before agents
resume; the new package name is still open for the author. **Do not merge it before those hold.** Signed notes,
specs and launch commits name `r1/…` paths. This session did not review it.

## 5. On `main` but not through the coordinator

`fe381df2` and `4cb92b70` (author "Codex", 26 Nov about 17:47Z and 18:05Z) were pushed to `main` directly. They add
the next-phase runbook, `canon/agents/design/SOUL.md`, the documentation indexes and the repository hygiene audit,
and they rewrite `canon/PAPER_C_PLAN.md`. What this session checked afterwards: documentation only; `PLAN.md`
unchanged; the D8 guard passes. No independent review record exists for them. Three points need the author:

1. The runbook and both plan views are marked "draft for author review". They are not adopted.
2. They record that the author selected the fixed-memory, variable-length sequence training task as Paper C's
   E-INT development census, and they add a design agent. Neither has a PLAN row.
3. `canon/README.md` rule 1 says only the coordinator publishes `main`. Ask the author whether Codex is now a
   publisher; if so that rule needs a row.

## 6. Waiting on the author

| Item | What he is asked | Blocks |
|---|---|---|
| Rows (f) and (g) | "签 (g) TIMEOUT A" or B, the three additions, "推 main" | Everything in §4.1 and §4.2 |
| G.5 note | Signature with S1 to S14. **The sheet is owed by the coordinator** and should follow the TIMEOUT answer (B changes the note) | The T1 labels |
| S9 | How an expansion node joins the frozen eight-node split (sheet owed by the local worker, task `local/20261126-04`) | The G.5 addendum |
| Signatures to come | Screening-measurement note; D.3 pre-declaration revision 4; P.4 phase-1 note (after the probe) | D.3; P.4 |
| Agents | Start the server agent and the tmux coordinator; say which agent now coordinates | Every task in `tasks/` |
| §5 | The three points there | The roles and Paper C |

## 7. Open STOPs

| STOP | Where | Next |
|---|---|---|
| Houseprice CPU-set check on TASL-2: the runner refuses a second attempt after a complete one, so the three sealed attempts cannot be produced | `main-t1-g5-prep-20261126`, report §4 (merged) | A procedure fix by the local worker (task `local/20261126-01`), then the re-check. It blocks that node only |
| Screening measurement, engineering smoke: `determinism_unverifiable openml_breast_w c5 seed 999` | `screen-measure-prep-20261126` | Diagnosis (task `local/20261126-02`) |
| P.4 cluster test T4 (tokenizer staging without a GPU): the step cannot be exercised with the CPU image (`env3` is missing there; retry job 760071, rc 127) | `trackp-p4-cluster-20261125` `8a9d48a1`, report `docs/r1/reports/trackp_p4_cluster_20261125/P4_CLUSTER_T0_T1_T2_T4_T6_20261125.md` | No patch was made. The report says the step can be exercised inside a GPU job. No task written yet |
| P.4 cluster test T6 (H200 slot shapes): 0 slots advertised | same report | A capacity STOP; nothing to fix in the code |
| P.4 test T1: job 760065 idle | No H200 in the pool | A GPU, or a launch path elsewhere |

## 8. Three contradictions to settle first

1. **Dates.** On `main` the dated rules stand: expansion cutoff 2 Dec 00:00 CET, T1 release by 17 Dec, arms-frozen
   record by 20 Dec, the 3 Jan rule. The runbook on `main` repeats them. The author said in chat on 26 Nov to erase
   every date limit; that exists only as the draft row R1-STEP-ORDER. Until it is on `main`, the dates apply. The
   2 Dec cutoff is close: the expansion G.1b needs the kit c1 record first.
2. **Agents and cards.** `main` (canon, runbook) has two host agents (cluster, experiment), one GPU model per
   table, and empty cards. The draft rows merge the two agents, free the placement and allow shared cards. Do not
   act on the draft rows.
3. **Roles.** `main` now has a design agent (from Codex) beside the writer; the row R1-AGENT-RUNTIMES still names a
   "writing and brainstorming agent" only, and the draft row R1-AGENT-COMPUTE changes the host agents. One row from
   the author should state the roles as he now wants them.

## 9. Next actions, in order

1. Get the author's answers of §6, first row.
2. Publish what he signs (§4.1), then push this branch's dependent tasks as in force (remove their first line).
3. Write the G.5 signing sheet (S1 to S14: options, a recommendation, the row text) and send it.
4. Kit c1 disposition record (server agent), independent review; then fill P2, P4 and the four gate lines of the
   expansion note, run the draft check, publish the note (pre-authorised by R1-T1-NODE-EXPANSION), run the strict
   `check-note-x`, launch the four nodes from `7d0279d8`.
5. Houseprice fix and re-check; the screening smoke diagnosis.
6. P.4: decide where it runs (the pool has no GPU), build that launch path, run the torch tests of the host-config
   fill, merge it, probe, phase-1 note to the author.
7. D.3: pre-declaration revision 4; units G1, G3 to G8 and A0R, each reviewed; the per-arm smoke.
8. Manuscript restructure (writer).
9. After G.5: T1 train/dev release row, arms, the arms-frozen record, the one gate read.
10. Paper C consolidation and its two CPU measurements, when Paper B leaves room.

## 10. How to verify, and limits of the coordinator's container

- **D8 guard** (fails while PLAN is uncommitted):
  `python3 -c "from r1.c3 import analysis_guard as g; g.require_d8_confirmation()"`
- **PLAN additions only:** `git diff origin/main -- docs/r1/PLAN.md | grep -c "^-[^-]"` must print 0.
- **Full suite** (code units, against the unit's base):
  `AR_HARNESS_ROOT=<harness checkout at a3fedbb> PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors --basetemp=<tmp> r1/tests`
- **PLAN-reading subset** (documentation-only pushes): `r1/tests/test_plan_row_check.py test_c3_arms_freeze.py
  test_t1_tasl_xc3.py test_t1_g5_tasl.py test_t1_tasl_g1b_x.py test_t1_tasl_g4.py
  test_c3_runner_package_environment.py test_b1_other_snapshot_unittest.py` and `r1/tests/hk2`.
- **Baselines in a container without torch and LightGBM:** subset 4 failed, 541 passed, 3 errors (reproduced on
  `52a3ce7a`); full suite 39 failed, 4 errors after the merges of 26 Nov. Compare against a base run on the same
  machine, not against these numbers. `test_trackp_p4_runner.py` and `test_trackp_sft.py` need torch.
  `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks` fails on `main` (it reads live
  `main`; a test-only fix is queued with the local worker).
- Test runs leave `/tmp/r1_c3_*` and `/tmp/c3_audit_tmp_*`; they filled the disk once.

## 11. Rules that bind (the short list; `canon/README.md` has all nine)

- `main`: merge commits only (no squash, rebase or cherry-pick), no force push, and only on the author's explicit
  "推 main" in his own message. In this session a push that relied on R1-AUTONOMY (3) alone was refused by the
  session's safety check and was not retried.
- Never push `r1` or `exam-x-*`. Nothing is deleted: a file to remove goes to a `_to_delete/` folder.
- No credential file is read (`~/.config/r1/secrets.env`, key files, `~/.docker/config.json`, `.docker-config`); no
  `docker login`. Other users' processes are never touched.
- Sealed data stays sealed until its release row. An evidence run starts only from the launch commit its signed
  note names.
- The author's words in chat are not decisions until they are PLAN rows on `main`.
- Every unit is reviewed by a fresh agent that did not write it; tier E until "accepted" (R1-PROCESS-TIERS).

## 12. What this session did, and what it did not check

- The hourly coordinator wake-up of this session was paused at 16:11Z on 26 Nov. No coordinator round has run
  since 16:05Z. Nothing was merged or published after `53b72f1d`.
- Not checked: the content of the two Codex commits beyond the points in §5; `codex/layout-flatten-preview`; the
  branches marked *(verify)*; the state of any host (no SSH from the coordinator's container); whether any agent
  is running outside this repository's branches.
- Scratch files of this session are not needed: everything that matters is on the two branches named in §2.
