# Prompt — Mac-local agent, hands-off continuation (7 Nov 2026, from about 01:00 CET)

**Written 7 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted. Revision 2 (00:55 CET).** The author read the 5 Nov morning report and said: "没有的话让它继续做，我还是回去睡觉 handsoff". At 00:49 he added: "加上顺手回答 Q1， 那个agent可以ssh，可以动GPU跑实验，你update一下prompt". Revision 2 adds his Q1 answer and the host/GPU authorization (§0), and the host tasks that follow from it. Paste everything below the line into the Mac-local agent.

---

The author has read your 5 Nov morning report (`mac-int-20261104` @ `e9641c1`). He is asleep and hands-off until about 09:00 CET and will not answer. **Keep working the whole time; do not stop to wait for him.**

## 0. Author decisions tonight, and the limits

### 0.1 Author answer to Q1 (7 Nov 00:49 CET)

"加上顺手回答 Q1". The author chooses option A:

> B1 acceptance record: use `OPS_O1_20261104.md` sha256 `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`.

Record it in PLAN §10 as a dated author row with his words verbatim, then bind it in the B1 note draft. If those report bytes ever change, the binding is void, and the change goes back to the author. Q0 and Q2 remain **open**.

### 0.2 Host access and GPU (author, 7 Nov 00:49 CET)

The author's words are "那个agent可以ssh，可以动GPU跑实验". Record them verbatim in PLAN §10. This replaces the old limit "no server access, no experiment, no model run, no GPU". The scope below is how this prompt reads that authorization; if anything is unclear, take the narrower reading and write the question down.

**Allowed tonight:** SSH to TASL-2, TASL-7 and deepthought, and GPU and model runs, **labelled ENGINEERING_ONLY**. This covers:
- host checks;
- qualification and determinism tests;
- test suites on the hosts;
- latency and memory measurements;
- site qualification.

**Still not allowed without the author's separately signed note:** any EVIDENCE run. That means B1, B2, sweep 2, Track S phases, Track P stages, HK phases, and anything whose output enters a paper table.
- B1 in particular stays closed until the author approves Q0 and chooses Q2. The B1 author gate must keep refusing.
- Do not work around it, and do not start B1 "to save time".

**Rules on every host:**
- **Before acting, read the host's lock and lease directory (`~/r1_locks`) and STATUS.** If another agent or operator holds the host or the GPU, do not touch it; record the conflict and move on.
- **Host priorities stand.** Track X goes first on TASL-2 and Track P first on TASL-7 (R1-TRACKS-HOST-2). Running jobs are never pre-empted (R1-TRACKS-S01-FOLLOWUP-REV).
- **Use the existing cooperative lease and marker procedures**, as in the operator runbook. Release every lease, and stop every server you start. Leave each GPU idle and the host as you found it.
- **Keep your work isolated.** Work only in your own dated directories. Do not modify Track S, Track P or Track X work trees, servers or `$WORK` data. Never delete remote files.
- **HoreKa stays with the HoreKa agent** (R1-SERVER-AGENTS-TWO). Do not log in there.
- **Record every host action** — commands, times, GPU UUIDs, outputs and sha256 values — in a dated `reports/` file, and have it independently reviewed like any other unit.

### 0.3 Unchanged rules

`MAC_OVERNIGHT_PROMPT_20261105.md` §1 (except the server/model/GPU limit, now replaced by 0.2) and §2 still apply in full:
- No author decisions beyond 0.1 and 0.2. Silence on the other questions is not a decision.
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
- Run the full Mac CPU suite on the integrated head.
- Record pass/fail/skip and the failure-ID diff against the historical 39.
- Where a failure is Mac-environment-specific, also run the suite, or the failing subset, on TASL-7 under the B1 Python binding. Use ENGINEERING_ONLY and follow §0.2.

**(d) Final combined B1 checkout.**
- Bind the Q1 answer (§0.1).
- Integrate the accepted B1 units into one checkout and have it independently reviewed.

**(e) TASL-7 host checks for B1** (ENGINEERING_ONLY; §0.2). On the final combined checkout:
- Verify the accepted cooperative flock and the server descriptor on the host.
- Verify the B1 worker's Python binding.
- Run the real-worker determinism test that the residual-test STOP names: one small model/worker run, ENGINEERING_ONLY, not B1 data.
- Work out how O2's TASL-2 marker and watcher sequence applies to TASL-7, including whether a Track S watcher is active there, and write the exact sequence down.
- Run the B1 entry in dry-run mode on the host, and confirm that the author gate refuses because the Q0 row and the approved note are absent.

Target for the morning: B1 needs only the author's Q0 line and Q2 choice, plus the operator message v3 updated with tonight's verified host facts (still held, not sent).

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

Same time-box as before. The **Linux site qualification** that the M3 STOP names (kernel and HUP behaviour on the target Linux host) may now be run under §0.2, ENGINEERING_ONLY, once the supervisor code is accepted.

**(b) The parts of M4 that do not touch `r1/scripts/c3_label_sweep.py`.** These can proceed now without breaking the shared-file rule:
- step 1, the harness pin candidate on `r1-local-20261104` (not merged into `r1`);
- the `llama_server_instance.py` parts of steps 2(a) and 2(e);
- step 3, the config template;
- step 4, the DTQ tool, with its dry run against a fake server;
- their tests.

The `c3_label_sweep.py` edits wait for M3's accepted commit and rebase on it. If the DTQ tool is accepted tonight, you may run it once on deepthought's two cards under §0.2, ENGINEERING_ONLY, with the largest Stage A finalist's GGUF as the worst case. The author is waiting for DTQ results (R1-B1B-DIFF-DT-DEFER, "先等 DTQ 结果"). The output is a measurement, not a pass/fail decision: the DTQ pass criterion is still the author's. If you judge that starting these parts conflicts with `MAC_LOCAL_RUNBOOK_20261104` §M4 or the separation rule, do not start them. Add them to the question list as an option instead.

### If capacity remains

1. M11 D8 gate to ACCEPTED, so that the author can commit R1-BX-D8-CONFIRM.
2. The M10 EVIDENCE/HK6 path.

## 3. Morning report

At about 08:30 CET on 7 Nov, write the report in the same format, in Chinese for the author.
- For each blocker: closed, or what remains, who must act, and the effort.
- List every host action and GPU use, with its report file.
- Put the Q2 option A, if built, at the top.
- Update the question list.
- Push everything.
