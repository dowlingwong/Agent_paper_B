# Prompts — handing the Mac-local agent's work to a new agent (4 Nov 2026)

**Written 4 Nov 2026 (18:15 CET) by the chat session (Claude) at the author's request ("mac agent这阶段结束后能换个agent吗？mac agent额度用完了"); AI-assisted.** There are two parts:
- **Part A** goes to the current Mac agent, if it has any budget left. It is its last action.
- **Part B** starts the new agent.

The new agent takes over the same role, under `prompts/MAC_LOCAL_RUNBOOK_20261104.md` (rev 3.3). This file authorizes nothing new.

---

## Part A — to the current Mac agent: last action, then stop

Do not start anything new. In this order:

1. **Push every branch that holds work**, so that nothing is lost when your session ends:
   - your worker branches `mac-x5v2-20261104` (M2) and `mac-b2-20261104` (M3);
   - any other `mac-*` branch.

   Push them as they stand, reviewed or not. Put "WIP, not accepted" in the last commit message wherever a review has not accepted it. Never push `main`, `r1` or `exam-x-*`, and never force-push.
2. **Write `docs/r1/reports/MAC_HANDOVER_20261104.md`** on `mac-int-20261104`, and push it. It contains:
   - every task M1–M15 with its state: done (commit, review), in progress (branch, head, what is left), or not started;
   - every review still running: the reviewer's file, the subject, the round;
   - every instruction the author gave you that is **not yet recorded** in PLAN or STATUS, quoted verbatim with its time;
   - the operator messages you drafted and whether the author has sent them;
   - the next three steps you would take.
3. Reply to the author in Chinese, in a few lines: the handover file's commit, and the pushed branch heads.

---

## Part B — to the new agent: start

You are the **Mac-local agent** of Paper B (route R1), taking over from a previous agent whose budget ran out. The author is Dowling Wong. Report to him in **Chinese**, short and concrete. Write documents in **English**.

**Your role and rules** are those of `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md` (rev 3.3), read on `mac-int-20261104`. In short:
- Only the author decides. A decision exists only as a dated PLAN §10 row, with his words quoted in the decision cell. Anything you add is marked *(proposed)* or *(open)*.
- At every STOP, a fresh independent reviewer reviews the work. You never accept your own work.
- You may run up to 3 worker subagents, each in its own worktree and branch, with you as the single integrator (§0).
- You are the single editor of `r1/exam/`, `r1/scripts/exam_*` and `r1/c3/train/` (R1-HANDOVER-04NOV).
- Never touch the Mac's main working tree. It holds someone else's uncommitted move of `docs/r1/` to `docs/`. Work in your own clone or worktree from GitHub (`https://github.com/dowlingwong/agent_paper_b`).
- Never push `main`, `r1` or `exam-x-*`, and never force-push. Commit author: `Dowling Wong <wangdowling@gmail.com>`, with the attribution lines the author gives you.
- Never read `~/.config/r1/secrets.env` or any key file.
- Things to delete go into a `_to_delete/` folder, never `rm`.

**Read first, in this order:**
1. `docs/r1/reports/MAC_HANDOVER_20261104.md`, if the previous agent wrote it.
2. `docs/r1/STATUS.md`: the top entries, from 4 Nov.
3. `docs/r1/PLAN.md` §10: every subsection dated 4 November.
4. `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md`.
5. `docs/r1/BRANCHES_20261104.md` (on `docs/repo-tidy-20261104`) for the branch map.

**State at 18:15 on 4 Nov, as the chat session knows it.** Check every item against the repository; where they disagree, the repository wins.
- **M1:** accepted. `mac-int-20261104` is the integration head.
- **M2** (`mac-x5v2-20261104`, `x5_rule_v2` sha `79d8c5cb…`): delivered, under independent review.
- **M3** (`mac-b2-20261104`): in progress.
- **M5 review of `ab74203`** (R1-EXAM-AB74203-M5-REVIEW): running, written to `reviews/MAC_M5_AB74203_REVIEW_20261104.md`.
- **Track X Stage A:** `t7h8` and M1 `t7j10` (10/10 PASS) were accepted by the operator's O1 review (`ops-20261104` @ `f52db28e`). The author's acceptance row is not yet recorded.
- **Documents to merge into `mac-int`:**
  - `docs/runbooks-04nov` @ `87841096`, which includes HoreKa runbook rev 3 (accepted), scan prompt rev 5.6, the scan and queue-probe reports, and the P.3a amendment draft;
  - `docs/repo-tidy-20261104` @ `d413dc81`;
  - `ops-20261104` (the operator's records; take its head at merge time).

**Author instructions the chat session handed him to send to the Mac agent, which may not have reached it or may not be recorded yet.** Ask the author which of these he sent, and record only those he confirms, each as a PLAN row with his words in the decision cell and a fresh review. Numbering as in the chat:
- **8.** Second proposer (R1-BX-D6): "用 exam 第二名". Details *(proposed)*: the runner-up by `x5_rule_v2` B2 thinking-off audited Y, of a different family than the pick (otherwise the next different-family finalist); served locally; no API.
- **9.** Stage A acceptance: `t7h8` and `t7j10`. B1 candidates = 8 + 7 PASS + 3 anchors.
- **10.** The fastest path to B1: M2 first; then the author writes R1-EXAM-RULE-X5V2 with the sha; then you draft the B1 note (`rule_sha256`, `nodes`, both Stage A table shas, `llm_call_cap`).
- **11.** Adopt `prompts/HOREKA_RUNBOOK_20261104.md` rev 3 as row R1-HOREKA-RUNBOOK (runbook §8). Point M10's HoreKa paragraph to the runbook's §3, and start `hk2_submit.py` and `hk2_status.py`.
- **12.** The author's ruling (18:00): "我直接裁定：agent 可以从 agent 节点提交 GPU 作业，包括续作业，同时等 NHR 回复。"
- **13.** Commit the P.3a amendment (`proposals/AUTH_DRAFT_trackp_p3a_amend_20261104.md`) as `authorizations/trackp_p3a_amend_20261104.md`, on the author's word.
- **14.** B1/B2 on TASL-7 instead of TASL-2 (amending R1-EXAM-HOST-TASL7), with Track X before Track P on TASL-7. Check `APPROVED_EXAM_HOSTS`, `cfg.host` and the v2 configs.

**Your first actions:**
1. Read the files above.
2. Send the author a short Chinese state summary: what is done, what is running, what is waiting for him.
3. Ask him which of items 8–14 to record.
4. Then continue with **M2's review** first: it is on the critical path to B1, and B1 to X.7.
