# Mac-local overnight runbook — 9/10 November 2026

**Written 9 Nov 2026 by the chat session (Claude) at the author's request ("desktop work你整合成一个runbook，我会让一个mac agent通宵去完成"); AI-assisted.** Not independently reviewed yet. It authorizes only what §0.3 lists. It does not replace `MAC_LOCAL_RUNBOOK_20261104.md`, the PLAN §10 rows or the 7 Nov prompt; where they differ, the dated PLAN rows win and you STOP to report the conflict.

You are the **Mac-local agent** for Paper B (route R1). The author, Dowling Wong, is asleep and hands-off tonight. Do not wait for answers: when you need a decision, write it into the question list (§3) with options, a recommendation and a paste-ready answer, and go on with the next task. Report to the author in **Chinese**; write files in **English**.

---

## 0. Ground rules

### 0.1 Standing rules (unchanged)

- **No deletion.** R1-EXAM-B1-NO-DELETION-07NOV ("继续严格禁止，先修复") stands. Never delete or overwrite evidence, STOP scenes, logs or another track's files. In the repo, retire things by moving them into a `_to_delete/` folder next to them and saying so in the report.
- **Never touch what you did not start.** No signal, cancel or edit of another user's or another agent's process, job or file (R1-TASL7-AGENT-OCCUPANCY-07NOV allows working beside them, not preempting them).
- **Independent review at every unit.** For each code or report unit, spawn a **fresh** reviewer with the goal, this runbook, the inputs and the outputs, but not your conclusions. Fix or answer each finding and re-check with the same reviewer until it writes *accepted*. You never accept your own unit.
- **Git.** Work in your own worktrees; never in `~/Documents/agent_paper_B` itself. Never push `main`, `r1` or `exam-x-*`; never force-push. Commit author `Dowling Wong <wangdowling@gmail.com>` with the attribution lines you were given. One feature branch per task (names below), integrated into `mac-int-20261107` only after its review.
- **Seeds.** C3 label seeds 7001–7005 and evaluation seeds 7006–7010 are never read for analysis tonight. Exam seeds (9001–9004 instance, 9101–9104 audit) never enter a C3 sweep.
- **Secrets.** Never read `~/.config/r1/secrets.env` or any key file.
- **SSH captures.** Every SSH call records its real exit code (`set -o pipefail`; `rc=$?` into the log and a separate `.rc` file). A capture without a recorded exit code is not evidence.

### 0.2 Not authorized tonight

B2, X.7, sweep 2 (T0 or T1), Track S, Track P, deepthought work, any HoreKa login, any change to a frozen pin or to an author rule, reading any sweep-2 label table, changing `approved` in an authorization note except as §1 step 1.6 says.

### 0.3 Authorized tonight

1. The B1 STOP diagnosis on TASL-7, read-only (§1), and a B1 restart under the conditions of `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §5 (author: "B1stop可以起草诊断，修好之后开始跑").
2. Code, tests and documents on the Mac for §2–§4.
3. Read-only SSH to TASL-7 for §1 only.

### 0.4 Author answers that may be pasted below this line

The author may paste one or more of these lines into your start message. Treat a line as given **only if it appears verbatim in the start message**; record it as a PLAN §10 row through the normal integration review.

- **A1 (B1 criterion):** `B1 判据：若诊断确认是设计问题（两个随机锚点无法排序），采用 R4：去掉锚点排序这道 STOP，锚点结果作描述性报告，保留 7B 重复率检查，附录披露为事后修订；修好审查后直接重跑。`
- **A2 (M4 order):** `M4 可以先做不和 M3 共享的部分。`
- **A3 (budget fields):** `采纳 R1-SEQ-BUDGET-FIELDS（W2）。`

## 1. Task 1 — B1 STOP: diagnosis, fix, restart (highest priority)

**Read first.** `reports/B1_STOP_6835_20261108.md`; `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (this branch); the accepted descriptive capture and its review on `mac-b1-stop-descriptive-review-20261108` (`reviews/B1_STOP_ANCHOR_DESCRIPTIVE_RESULT_REVIEW_20261108.md`). That capture already shows per-root mean `delta_audit` from about −0.0166 to +0.0148 for `random_valid` and from about −0.0028 to +0.0013 for `scripted`. This is descriptive only, but it points to hypothesis H1/H3 of the plan (two random proposers, one with tiny local edits).

**Branch.** `mac-b1-diag-20261109`, from `mac-b1-20261107`.

**Steps.**

1. **Diagnosis D0–D8** (plan §3), extending the accepted descriptive script rather than writing a new reader. Same read-only boundary: fixed paths under `/home/dowling/exam-x/work/b1_6835_20261108_a`, `O_NOATIME`, hash checks before output, exit code captured. The plan's D3 needs σ_node for the three nodes: take it from the committed D21 noise-floor tables, cited by path and SHA. Report `reports/B1_STOP_DIAGNOSIS_20261109.md` plus a JSON with per-instance numbers. Independent review.
2. **Classify** per plan §4: E (engineering defect), P (power only), D (design or metric), and separately whether D7 (7B duplicate rate inside [0.4239, 0.5800]) passes.
3. **Route.**
   - **E:** fix the defect with a regression test (synthetic), independent review, then go to step 4.
   - **D with A1 given:** implement R4 in `r1/scripts/exam_runner.py::anchor_gate`. Remove only the ordering STOP; keep computing and recording `scripted_minus_random` as a descriptive field; keep the 7B duplicate-rate STOP unchanged. Add a test that the duplicate-rate STOP still fires and that the ordering no longer stops. Write the appendix disclosure text (original criterion, its numbers from D1, reason, date) into `reports/B1_GATE_AMENDMENT_20261109.md`. Independent review, then step 4.
   - **D without A1, or P, or D7 fails:** STOP Task 1. Put the question in §3 with the plan's options and your recommendation, and go to Task 2.
4. **Restart preparation** (plan §5): exact new checkout committed and clean; independent review of that exact HEAD; the authorization note re-bound to the new HEAD as an `approved: true` candidate (R1-EXAM-B1-NOTE-ORDER-07NOV); the real author gate passes on it.
5. **Host steps on TASL-7**, as for run `6835_20261108_a`: fresh read-only occupancy census; the Track P marker and handover procedure; final host preflight; offline loader check reused only if the checkout's loader files are unchanged (else repeat it once, with exit code).
6. **Launch** run `6835_20261109_b` (or the next free suffix) in a fresh output tree. Never write into `b1_6835_20261108_a`.
7. **Monitor** read-only at most every 15 minutes, with captured exit codes, exactly as on 8 Nov. On any STOP: preserve the scene, write the STOP report, get it reviewed, do not retry.

**Done when** the diagnosis report is accepted and either B1 is running (or finished) under the new run ID, or the open question is in §3.

## 2. Task 2 — HoreKa porting kit and diff support (M10 steps 0–1; unblocks HoreKa HK2)

**Why tonight.** The HoreKa agent can start HK1 without this, but it cannot port any GPU task (HK2) until these shared pieces exist at a reviewed commit (`HOREKA_RUNBOOK_20261104.md` HK2 "Needs"; `MAC_LOCAL_RUNBOOK_20261104.md` M10 steps 0–1; `TRACK_G_RUNBOOK.md` §2, G.2).

**Branches.** Paper `mac-trackg-20261109` from `mac-int-20261107`; harness `r1-local-trackg-20261109` from `origin/r1` in a separate worktree of `autoresearch_harness`. Do not touch the harness pin `a3fedbb` used by B1.

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

Order: Task 1 → Task 2 → Task 3 → Task 4 → Task 5. While B1 runs (Task 1 step 7), work on Tasks 2–5 between monitoring checks. If a task STOPs, record it and move to the next. Stop starting new units at 07:30 CET.

## 7. Morning report (08:30 CET)

`reports/MAC_OVERNIGHT_REPORT_20261110.md` and a STATUS entry, then a short Chinese message to the author with:
1. B1: diagnosis class, what was fixed, run ID and its state (running / finished / STOP), and anything preserved.
2. Each task: done / partly done / STOP, branch and commit, review verdict.
3. The question list `reports/MAC_OVERNIGHT_QUESTIONS_20261110.md`: each question with context, options, recommendation and a paste-ready answer.
4. For the HoreKa agent: the port-kit commits (Task 2), or why they are not ready.
