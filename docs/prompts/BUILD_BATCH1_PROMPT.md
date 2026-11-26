# Prompt — R1 build batch 1 (L1, L3, L5, L6) for a local implementation agent

Written 9 Oct 2026 by the coordinating session (Claude). Paste everything inside the fence into a local agent session on the Mac, for example Claude Code or Codex in a terminal. **Before pasting, edit the AUTHOR DECISIONS block** if any default differs from what you want.

```text
You are implementing the first local build batch of "Paper B, route R1":
learned control of governed autoresearch loops. You work on the author's Mac.
Nothing you produce is evidence: all outputs are ENGINEERING_ONLY.

AUTHOR DECISIONS (stated by the author by sending this prompt, 9 Oct 2026)
- D1 budget: compute (worker runs; worker-seconds) plus an LLM-call cap; the
  trial-count budget stays available.
- D3 core actions: continue, skip (E1), revise (E1), verify with demote (E2),
  stop (E0).
- D4: the keep rule is overridden only by verify's frozen response.
- D14: harness changes go on branch r1 of ~/Documents/autoresearch_harness;
  analysis code goes in ~/Documents/agent_paper_B/r1/.
- D19: worker backend LocalWorker; do not initialise the claw-code submodule.
- D20: ML-research benchmarks only. Not needed in this batch.
Record these as dated rows in ~/Documents/agent_paper_B/docs/r1/PLAN.md §10
("decided 9 Oct by the author") in your first commit there. Record nothing
else as decided.

READ FIRST (in this order)
1. ~/Documents/agent_paper_B/docs/r1/BUILD_RUNBOOK.md: §0 conventions, then
   L1, L3, L5, L6. This is your specification.
2. ~/Documents/agent_paper_B/docs/r1/RUNBOOK.md: §1 ground rules, and §3
   "Execution order".
3. ~/Documents/agent_paper_B/docs/r1/PLAN.md: §1–§5, §10.
4. ~/Documents/agent_paper_B/docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md:
   §1.2 epochs, §2.1 actions and masks, Appendix A defects.
5. Harness: README.md, CLAUDE.md, src/autoresearch/control_plane/
   (campaign.py, decision.py, state_machine.py, budget.py, events.py),
   memory/schemas.py, worker/local_worker.py, manager/langgraph_manager.py,
   manager/prompt_manager.py, configs/nodes/lr_synthetic.yaml,
   nodes/lr_synthetic/train.py, tests/.
   Line numbers in the runbook refer to da8dcbd; re-locate them in the
   current code before editing.

TASKS, in order. Commit after each task (one logical change per commit).
- L1  Housekeeping (BUILD_RUNBOOK L1). In ~/Documents/agent_paper_B, first
      run `git status`. Expected:
        - deletions under docs/paper_split/;
        - new archive/old_b_2026-10-09/, docs/r1/;
        - a modified README.md.
      Commit exactly these as one commit: "Archive old Paper B plans; adopt
      route R1 canonical plan". Anything else: list it in your report and
      leave it alone. Push.
      Do NOT touch ~/Documents/agent_sys_paper (Paper A): its uncommitted
      plan edit belongs to another session.
      In ~/Documents/autoresearch_harness: create branch r1, sync the
      environment (uv sync --extra dev, or a venv with pip install -e
      ".[dev]"), and run the full test suite. Record the baseline pass/fail
      counts; pre-existing failures are recorded, not fixed.
- L3  The four harness defects, each with a test that fails before and
      passes after (BUILD_RUNBOOK L3):
        - prompt_manager docs and the deterministic flag;
        - the ClawWorker val_bpb sign;
        - _current_best direction and kept-only;
        - AR_TRAIN_SEED / AR_SPLIT_SEED injection, with unchanged defaults.
- L5  Controller interface, epochs E0/E1/E2, evaluate/commit split, mask,
      control_decision event, ComputeBudget, CLI flags (BUILD_RUNBOOK L5).
      The default ContinueController must reproduce today's records exactly
      (exclusions as in BUILD_RUNBOOK §0). Write that regression test FIRST,
      against the unmodified code, then implement. Also write the leak test.
- L6  Actions skip, revise, verify (+demote), stop, each with its mask and
      ledger semantics as in the BUILD_RUNBOOK L6 table, plus a scripted
      controller test on a 6-trial lr_synthetic campaign. Revise must work
      with langgraph_manager using an injected stub LLM (no Ollama needed).

HARD RULES
- Default behaviour is sacred. With the default controller and no new
  flags, all pre-existing tests stay at the L1 baseline, and the regression
  test stays green after every commit.
- No double appends to the ledger. Pending-guard semantics are unchanged.
  The control plane, never a controller, writes the ledger.
- Never force-push, rewrite pushed history, delete ledgers, or edit files
  under archive/.
- Do not install or call Ollama or any API model in this batch. Use stub
  LLMs. Do not run benchmarks other than lr_synthetic and the dry worker.
- If a step needs a decision not recorded in PLAN §10, or the code
  contradicts BUILD_RUNBOOK in a way that changes semantics, STOP and
  report. Do not guess.
- When you are unsure whether a change alters default behaviour, run the
  regression test.

CHECKS before you report
- The full harness test suite: counts compared with the L1 baseline.
- The new tests by name: L3 ×4, the L5 regression and leak tests, the L6
  action tests.
- `git log --oneline` for both repositories.
- The dry-run campaign from the harness README still works:
  `scripts/run_campaign.py --node lr_synthetic --campaign-id smoke --budget 3 --dry-run`.

REPORT (end of session)
- Write a dated entry in ~/Documents/agent_paper_B/docs/r1/STATUS.md. For
  each task, give: commits, files changed, tests added, check results,
  anything not done and why, and open questions phrased for the author.
- Return the same summary in chat.
- Next batch, for information only (do not start it): L4 (pinned Ollama
  model), L7 (restore/branching), L8 (adapters).
```
