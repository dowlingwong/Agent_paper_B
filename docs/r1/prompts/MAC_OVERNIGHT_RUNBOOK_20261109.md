# Mac-local overnight runbook — 9/10 November 2026

**Written 9 Nov 2026 by the chat session (Claude); AI-assisted.** Not independently reviewed yet. It authorizes only what §0.3 lists. It does not replace `MAC_LOCAL_RUNBOOK_20261104.md`, the PLAN §10 rows or the 7 Nov prompt; where they differ, the dated PLAN rows win and you STOP to report the conflict.

You are the **Mac-local agent** for Paper B (route R1). You do **desktop work only**: code, tests, analysis and documents on the Mac. You have no SSH access to any server; everything that runs on a server is done by the experiment agent, to whom you hand scripts and instructions. The author, Dowling Wong, is asleep and hands-off tonight. Do not wait for answers: when you need a decision, write it into the question list (§3) with options, a recommendation and a paste-ready answer, and go on with the next task. Report to the author in **Chinese**; write files in **English**.

---

## 0. Ground rules

### 0.1 Standing rules (unchanged)

- **No deletion.** The no-deletion rule stands. Never delete or overwrite evidence, STOP scenes, logs or another track's files. In the repo, retire things by moving them into a `_to_delete/` folder next to them and saying so in the report.
- **Never touch what you did not start.** No signal, cancel or edit of another user's or another agent's process, job or file (working beside them is fine; preempting them is not).
- **Independent review at every unit.** For each code or report unit, spawn a **fresh** reviewer with the goal, this runbook, the inputs and the outputs, but not your conclusions. Fix or answer each finding and re-check with the same reviewer until it writes *accepted*. You never accept your own unit.
- **Git.** Work in your own worktrees; never in `~/Documents/agent_paper_B` itself. Never push `main`, `r1` or `exam-x-*`; never force-push. Commit author `Dowling Wong <wangdowling@gmail.com>` with the attribution lines you were given. One feature branch per task (names below), integrated into `mac-int-20261107` only after its review.
- **Seeds.** C3 label seeds 7001–7005 and evaluation seeds 7006–7010 are never read for analysis tonight. Exam seeds (9001–9004 instance, 9101–9104 audit) never enter a C3 sweep.
- **Secrets.** Never read `~/.config/r1/secrets.env` or any key file.

### 0.2 Not authorized tonight

Any SSH or other server access; B2, X.7, sweep 2 (T0 or T1), Track S, Track P; any change to a frozen pin or to an author rule; reading any sweep-2 label table; setting `approved: true` in an authorization note.

### 0.3 Authorized tonight

Code, tests, analysis and documents on the Mac for §1–§5, including the scripts and the hand-off for the experiment agent in §1.

### 0.4 Author answers that may be pasted below this line

The author may paste one or more of these lines into your start message. Act on a line **only if it appears in the start message**.

- **A1 (B1 criterion):** `B1 判据：若诊断确认是设计问题（两个随机锚点无法排序），采用 R4：去掉锚点排序这道 STOP，锚点结果作描述性报告，保留 7B 重复率检查，附录披露为事后修订；修好审查后直接重跑。`
- **A2 (M4 order):** `M4 可以先做不和 M3 共享的部分。`
- **A3 (budget fields):** `采纳 R1-SEQ-BUDGET-FIELDS（W2）。`

## 1. Task 1 — B1 STOP: desktop part of the diagnosis and the fix (highest priority)

**Read first.** `reports/B1_STOP_6835_20261108.md`; `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (this branch); the accepted descriptive capture and its review on `mac-b1-stop-descriptive-review-20261108` (`reviews/B1_STOP_ANCHOR_DESCRIPTIVE_RESULT_REVIEW_20261108.md`). That capture already shows per-root mean `delta_audit` from about −0.0166 to +0.0148 for `random_valid` and from about −0.0028 to +0.0013 for `scripted`. This is descriptive only, but it points to hypothesis H1/H3 of the plan (two random proposers, one with tiny local edits).

**Branch.** `mac-b1-diag-20261109`, from `mac-b1-20261107`.

**Steps.**

1. **What the code alone can answer** (no server data): plan §3 D5 (metric orientation per node, from the node configs and `paired()`) and D6 (diff of the anchor path between Stage A's accepted checkout and `68357d3d`: managers, value grids, worker, wrappers, OpenML bootstrap guard; value-grid file hash). Report `reports/B1_STOP_CODE_CHECKS_20261109.md`. Independent review.
2. **The diagnosis script for the experiment agent:** extend the accepted descriptive script `proposals/B1_STOP_ANCHOR_DESCRIPTIVE_20261108.py` to the server-side steps D0–D4, D7 and D8 (same read-only boundary: fixed paths under `/home/dowling/exam-x/work/b1_6835_20261108_a`, `O_NOATIME`, hash checks before output; JSON output). The σ_node values for D3 come from the committed D21 noise-floor tables, cited by path and SHA and embedded as constants. Synthetic tests in the style of `r1/tests/test_b1_stop_anchor_descriptive_synthetic.py`. Independent review. Then write `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` for the experiment agent: the script path and SHA, the exact command, what to send back (the capture with its exit code and SHA).
3. **A small analysis script** that turns that JSON into the report tables of plan §3 and a class verdict per hypothesis, tested on a synthetic JSON. When the experiment agent's capture arrives, run it and write `reports/B1_STOP_DIAGNOSIS_<date>.md`; independent review.
4. **Fix candidates, prepared now so the restart is not delayed:**
   - **If A1 was given:** implement R4 in `r1/scripts/exam_runner.py::anchor_gate` on its own branch `mac-b1-r4-20261109`. Remove only the ordering STOP; keep computing and recording `scripted_minus_random` as a descriptive field; keep the 7B duplicate-rate STOP unchanged. Tests: the duplicate-rate STOP still fires; the ordering no longer stops. Draft the appendix disclosure `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md` (original criterion, reason, date; the numbers are filled in from the diagnosis later). Independent review. It is used only if the diagnosis classifies the STOP as D.
   - **If step 1 finds an engineering defect:** fix it with a regression test on `mac-b1-fix-20261109`; independent review.
5. **Restart hand-off:** for whichever fix applies, prepare the exact new checkout (committed, clean, independently reviewed) and `proposals/B1_RESTART_HANDOFF_20261109.md` for the experiment agent: the commit, the new run ID suffix, and the restart conditions of plan §5. You do not set `approved: true`, run the author gate on the host, or launch anything.

**Done when** the code checks, the diagnosis script and both hand-offs are reviewed and pushed, and the fix candidate is ready or the open question is in the question list.

## 2. Task 2 — HoreKa porting kit and diff support (M10 steps 0–1; unblocks HoreKa HK2)

**Why tonight.** The HoreKa agent can start HK1 without this, but it cannot port any GPU task (HK2) until these shared pieces exist at a reviewed commit (`HOREKA_RUNBOOK_20261104.md` HK2 "Needs"; `MAC_LOCAL_RUNBOOK_20261104.md` M10 steps 0–1; `TRACK_G_RUNBOOK.md` §2, G.2).

**Branches.** Paper `mac-trackg-20261109` from `mac-int-20261107`; harness `r1-local-trackg-20261109` from `origin/r1` in a separate worktree of `autoresearch_harness`. Do not change the harness pin `a3fedbb` used by B1.

**Step 0 — shared pieces for ports** (harness side unless noted):
- a node template: `NodeSpec` YAML with `editable_paths`, `frozen_paths`, run command, metric name and direction, and a **fixed step or token budget field** (a wall-clock budget is refused);
- a base metric parser that returns one of `ok(value)`, `divergent` (non-finite loss, or no metric at the budget) or `infrastructure_failure` (timeout, killed), never mixing them;
- a per-run working-copy runner: copies the node, applies limits (GPU by UUID, CPU and memory caps, timeout = 3 × measured run time as a parameter), fixed worker and thread counts from the NodeSpec, deterministic-algorithm settings (`cudnn.benchmark = False`, `torch.use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG`) with a record of which could not be forced;
- validation-only selection for test-scored tasks;
- a checklist file for declaring 3–5 representative edits as diffs, hashed and committed before any measurement (paper side, `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`).

Tests on fake runs: a frozen-path edit is refused; a NaN loss is classified `divergent`; a timeout is `infrastructure_failure`; a wall-clock budget is refused.

**Step 1 — diff support (G.2):** apply a unified diff inside the per-run copy through the existing scope validator; refuse any hunk outside `editable_paths` or inside `frozen_paths`; inert detection (empty after whitespace/comment normalisation, or an AST equal to the incumbent's); duplicate detection (normalised diff hash and resulting code-state hash against every evaluated state); provenance fields (diff text, hash, files touched, code-state hash); schema `manager_proposal/v2-diff`. **The T0 path must stay byte-identical:** a test runs a `manager_proposal/v1` campaign on a CPU fixture before and after and compares requests and records byte for byte.

**Done when** both branches' tests pass with the failure set unchanged apart from new tests, a fresh reviewer has accepted (checking the byte-identical T0 test in particular), and the hand-off note `reports/M10_PORTKIT_HANDOFF_20261109.md` names the two commits for the HoreKa agent.

## 3. Task 3 — M3 code completion (unblocks B.2 and M4)

Continue M3 where the 8 Nov reviews left it (`mac-m3-*` branches; latest reviews `MAC_M3_*_20261108.md`): the Linux supervisor, notification withdrawal and HUP handling, and the 16 cases. Code and synthetic tests only; the on-site qualification is a later host step, not tonight. Independent review. M4 starts only if line A2 was given, and then only its parts that do not touch `r1/scripts/c3_label_sweep.py`.

## 4. Task 4 — M11 aggregate gate (D8) and the confirmation draft

Finish the D8 gate statistic in `r1/c3/gate.py` (or the existing module): gap closed per node against the noisy-oracle ceiling, IQM across nodes, probability of improvement, node-stratified bootstrap; synthetic tables with known answers. Confirm every sweep-2 reader refuses without a table row whose first cell starts with `R1-BX-D8-CONFIRM`. Draft that row for the author in `proposals/R1_BX_D8_CONFIRM_DRAFT_20261109.md` with the gate code's SHA. Do not commit it as an author row. Independent review.

## 5. Task 5 — budget fields from worker runs (only if A3 was given)

`proposals/SEQUENTIAL_POLICY_REVISION_20261104.md` (branch `docs/seq-revision-04nov`) §4.2 W2: redefine `budget_frac_left` and the serialized budget line from remaining worker runs; a test that values are identical on execute-all tables. Independent review.

## 6. Order, time and stopping

Order: Task 1 → Task 2 → Task 3 → Task 4 → Task 5. If a task STOPs, record it and move to the next. Stop starting new units at 07:30 CET.

## 7. Morning report (08:30 CET)

`reports/MAC_OVERNIGHT_REPORT_20261110.md` and a STATUS entry, then a short Chinese message to the author with:
1. B1: the code checks, the diagnosis script and its hand-off for the experiment agent, the fix candidate and the restart hand-off (commits and review verdicts).
2. Each task: done / partly done / STOP, branch and commit, review verdict.
3. The question list `reports/MAC_OVERNIGHT_QUESTIONS_20261110.md`: each question with context, options, recommendation and a paste-ready answer.
4. For the HoreKa agent: the port-kit commits (Task 2), or why they are not ready.
