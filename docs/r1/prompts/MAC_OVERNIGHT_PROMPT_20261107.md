# Prompt — Mac-local agent, hands-off continuation (7 Nov 2026, from about 01:00 CET)

**Written 7 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.** The author read the 5 Nov morning report and said: "没有的话让它继续做，我还是回去睡觉 handsoff". Paste everything below the line into the Mac-local agent.

---

The author has read your 5 Nov morning report (`mac-int-20261104` @ `e9641c1`). He is asleep and hands-off until about 09:00 CET and will not answer. **Keep working the whole time; do not stop to wait for him.**

## 0. Limits and rules — unchanged

`MAC_OVERNIGHT_PROMPT_20261105.md` §1 and §2 still apply in full:
- No server access, no experiment, no model run, no GPU.
- No author decisions. Silence on Q0–Q24 is not a decision.
- Never push `main`, `r1` or `exam-x-*`; never force-push; never delete anything.
- Every unit is accepted only by a fresh independent reviewer.
- At most 3 workers.
- Minimal first.
- Time-box: 3 review rounds or about 2 hours, then record the blocker and move on.
- Commit and push each accepted unit at once.

## 1. Feedback on the report

The report is good. It separates accepted scope from STOP cleanly, and it claims nothing beyond the evidence. Two points:

1. **The B1 goal was not met, and nothing has been pushed since 07:24 on 5 Nov.** The 5 Nov night's goal was "B1 signable with one line". The critical path is:
   - B1 → B2 → X.7 → sweep 2;
   - M3 → M4 in parallel with that;
   - then audits → D8 → B.7, with a target of about 8 Dec;
   - the HoreKa submission freeze is 20 Nov 12:00.

   Tonight's goal: close every B1 blocker that does not need the author, and move both parallel critical-path items (B2 ranking; M3/M4).
2. **Recommendations stay recommendations.** Keep the question list current, but never phrase a recommendation as if it were decided.

## 2. Work — three workers in parallel

### Worker A — B1 blockers that need no author (priority 1)

**(a) Anchor duplicate reference (Q2): build option A for the author.**
- Inventory the candidate sources:
  - the sweep-1 campaign ledgers (`qwen2.5-coder:7b`; `append_only_summary` and `none`; frozen under R1-B1-CORPUS-FREEZE; read only);
  - the Stage A anchor records (`t7h8`, `t7j10`);
  - `DUPLICATE_RATE_PILOT_20261022.md`.
- For each source, check whether it matches B1:
  - the duplicate definition and denominator (`active_config_seen_before` among evaluated novelty events; no-ops counted separately);
  - node, memory mode, proposer, W and call cap.
- For the best match:
  - compute the rate per B1 node with a script, with a campaign-cluster bootstrap 95 % interval;
  - write the SHA-bound JSON (`lower`, `upper`, source, derivation, script sha);
  - have it independently reviewed.
- Present it as option A of Q2. Do **not** bind it into the note as approved.
- Use proposal ledgers only. Never read evaluation audit values (seeds 7006–7010).
- If no source matches, say so in one paragraph. Give the closest option, and what a proper reference would cost to produce.

**(b) B1 residual tests.**
- Restore the former Stage A kill/resume coverage on the B1 path.
- Fix, or precisely classify, the outer nested rerun-2 test.
- Target: every B1-path or B1-related failure in `MAC_M2_FAILURE_CLASSIFICATION_20261105.md` is either fixed or has a reviewed reason.

**(c) Current full suite.**
- Run the full Mac CPU suite on the integrated head: CPU only, no model, no server. This is within the limits.
- Record pass/fail/skip and the failure-ID diff against the historical 39.

**(d) Final combined B1 checkout.**
- Integrate the accepted B1 units into one checkout and have it independently reviewed.
- After this, only two things should remain: the author's Q0/Q1/Q2 lines, and the TASL-7 host checks (flock, server descriptor, O2 handover).

### Worker B — B2 ranking (priority 1, in parallel)

B2 runs right after B1, and X.7 needs its ranking. Implement the minimal v2 ranking exactly as `x5_rule_v2` states:
- enforce the complete node/instance grid;
- refuse duplicate primary candidates;
- rank by thinking-off audited Y;
- break ties by lower GPU-h.

Add tests and take it to ACCEPTED. Its STOP entry is removed only by acceptance.

### Worker C — the sweep-2 path (priority 2, in parallel)

**(a) M3.** Continue toward a minimal accepted offline replay:
- the Linux supervisor;
- distinguishing a normal HUP from a monitor failure;
- binding all 16 cases in the reviewed execution path;
- the offline executability proof.

Same time-box as before.

**(b) The parts of M4 that do not touch `r1/scripts/c3_label_sweep.py`.** These can proceed now without breaking the shared-file rule:
- step 1, the harness pin candidate on `r1-local-20261104` (not merged into `r1`);
- the `llama_server_instance.py` parts of steps 2(a) and 2(e);
- step 3, the config template;
- step 4, the DTQ tool, with its dry run against a fake server;
- their tests.

The `c3_label_sweep.py` edits wait for M3's accepted commit and rebase on it. If you judge that starting these parts conflicts with `MAC_LOCAL_RUNBOOK_20261104` §M4 or the separation rule, do not start them. Add them to the question list as an option instead.

### If capacity remains

1. M11 D8 gate to ACCEPTED, so that the author can commit R1-BX-D8-CONFIRM.
2. The M10 EVIDENCE/HK6 path.

## 3. Morning report

At about 08:30 CET on 7 Nov, write the report in the same format, in Chinese for the author.
- For each blocker: closed, or what remains, who must act, and the effort.
- Put the Q2 option A, if built, at the top.
- Update the question list.
- Push everything.
