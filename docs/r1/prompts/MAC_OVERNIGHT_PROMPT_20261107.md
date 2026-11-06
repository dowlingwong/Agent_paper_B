# Prompt — Mac-local agent, overnight run with B1 authorized (7 Nov 2026, from about 01:00 CET)

**Written 7 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted. Revision 3 (01:05 CET).** The author's words, in order:
- 00:45, after reading the 5 Nov morning report: "没有的话让它继续做，我还是回去睡觉 handsoff";
- 00:49: "加上顺手回答 Q1， 那个agent可以ssh，可以动GPU跑实验，你update一下prompt";
- 00:55: "我是想让它今晚直接跑正式实验，你update下prompt".

Revision 3 replaces revision 2's ENGINEERING_ONLY limit: the author authorizes the formal B1 run tonight, under the conditions in §0. Paste everything below the line into the Mac-local agent. The author read this prompt before sending it; sending it is his approval of §0.

---

The author has read your 5 Nov morning report (`mac-int-20261104` @ `e9641c1`). He wants **the formal Track X B1 run started tonight**. He is asleep and hands-off until about 09:00 CET and will not answer. **Keep working the whole time; do not stop to wait for him.** Record every author decision below in PLAN §10 as dated author rows, with his words verbatim and a pointer to this prompt file (`docs/r1/prompts/MAC_OVERNIGHT_PROMPT_20261107.md` on `docs/runbooks-04nov`).

## 0. Author decisions tonight (7 Nov, 00:45–00:55 CET)

### 0.1 Q1 — B1 acceptance record

Option A:

> B1 acceptance record: use `OPS_O1_20261104.md` sha256 `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`.

If those bytes ever change, the binding is void, and the change goes back to the author.

### 0.2 Q2 — B1 anchor duplicate reference: the author delegates it to this fixed rule

The rule is fixed now, before any B1 data. Apply it exactly. Do not tune it after computing anything.

**Source.** Sweep-1 campaigns (frozen under R1-B1-CORPUS-FREEZE; read their proposal ledgers only) that meet all of these:
- proposer `qwen2.5-coder:7b`;
- memory `append_only_summary`;
- one of the three B1 nodes (`digits_mlp`, `openml_credit_approval`, `openml_ionosphere`);
- W = 20.

Never read evaluation audit values (seeds 7006–7010).

**Statistic.** duplicates / evaluated, exactly as B1's anchor gate computes it for `qwen25_coder_7b` (`exam_runner.anchor_gate`: `diagnostics.duplicates / diagnostics.evaluated`, pooled over the anchor's campaigns). Use the same code path that produces B1's `diagnostics`. If you use a re-implementation instead, a test must show it is identical on the B1 dry-run fixtures.

**Interval: a 99 % predictive interval, not a confidence interval for the mean.** B1's anchor rate is itself estimated from B1's own few anchor campaigns, so the reference must cover that sampling variation.
- Draw 10,000 times with a fixed seed recorded in the JSON.
- In each draw, resample with replacement, per node, the same number of sweep-1 campaigns as B1 runs for the 7B anchor on that node, and compute the pooled rate as B1 does.
- `lower` and `upper` are the 0.5 % and 99.5 % quantiles.

**Comparability.** Check and record in the JSON:
- **Blocking mismatches** (sending you to the fallback below): proposer model and quantization, memory mode, nodes, W, and the duplicate definition.
- **Disclosed differences** (recorded, not blocking): host and GPU, llama.cpp build and flags, `cache_prompt` default vs false, context length, B1's charged A4 side query (it never enters the manager context), and the harness pin.

**Output.**
- A JSON with `source`, `lower`, `upper`, the derivation, the seed, the script sha256, the campaign list, and the comparability table.
- Its sha256 bound in the B1 note.
- One independent review of the computation and the definition match.

**Fallback.** Use it only if a blocking mismatch exists, or if the sweep-1 ledgers for these strata cannot be read.
- Set the anchor duplicate check to descriptive: `lower` 0, `upper` 1, with the JSON stating the reason.
- Keep the scripted-vs-random discrimination gate unchanged.
- Disclose the fallback in the PLAN row and the B1 report.
- Do not invent another source.

### 0.3 Q0 — rule and note approved, launch authorized

The author approves, verbatim from the morning report's proposed answer:

> I approve x5_rule_v2 SHA256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad and the reviewed B1 authorization note for TASL-7, subject to the agreed anchor reference, exact final checkout, and all reviewed handover and phase gates.

Record it as the PLAN §10 row **R1-EXAM-RULE-X5V2**, with the rule sha (the id `runtime.author_gate` requires), and add a dated row with the 00:55 words. The "agreed anchor reference" is the one produced by §0.2.

**Launch conditions. All must hold.** Set `approved: true` in the note, and launch, only when every one of these is true:
1. **Q2 JSON.** It was produced under §0.2 and its independent review is ACCEPTED.
2. **Tests.**
   - Every B1-path or B1-related failure in `MAC_M2_FAILURE_CLASSIFICATION_20261105.md` is either fixed or has a reviewed reason.
   - The former Stage A kill/resume coverage on the B1 path is restored.
   - The real-worker determinism test passes on TASL-7 (ENGINEERING_ONLY run).
3. **Final combined checkout.** All accepted B1 units, the Q1 binding, the Q2 JSON, the PLAN rows and the approved note are integrated into one checkout. Its committed HEAD is independently reviewed and ACCEPTED, and it is clean.
4. **TASL-7 host checks pass.**
   - The cooperative flock and the server descriptor.
   - The worker's Python binding.
   - The GPU UUID matches the note (`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`).
   - Disk space for the full B1 output.
5. **The author gate passes on the committed HEAD.** The pre-flight dry run on the host passes.
6. **The TASL-7 handover sequence is complete.** O2's marker/watcher sequence is adapted to TASL-7, written down, and reviewed. Then:
   - Create the Track X evidence marker and publish the running STATUS.
   - Let the Track S watcher on TASL-7 pause its collectors and stop its servers, if one is active.
   - Bring Track P P.3a to a safe point and pause it (R1-EXAM-HOST-B1B2-TASL7: Track X evidence takes priority over Track P on TASL-7; P.3a pauses while B1 runs).
   - **Never kill a running job outside the reviewed pause procedure.** If a job cannot reach a safe point, wait. If it cannot reach one before the morning, do not launch: record it.

If any condition fails: **do not launch.** Record exactly which one, what would unblock it, who must act and the effort. Then keep working on everything else. There is no deadline for the launch: it may start at any hour once the conditions hold.

### 0.4 While B1 runs

- **Operate it per the reviewed operator message v3** (`B1_OPERATOR_MESSAGE_V3_DRAFT_20261105.md`). Update it with tonight's verified TASL-7 facts, and have the update reviewed before launch. Its STOPs apply as written.
- **On any STOP from the runner, guardian, author gate or anchor gate:**
  - stop at once and preserve everything;
  - publish the STATUS;
  - report.
  - Never re-run, change code, change pins, widen the anchor interval or override a gate to get past a STOP. A STOP waits for the author.
- **No change to the checkout, pins, config or note after launch.**
- **Monitor at a fixed cadence** (at least every 30 minutes). Log progress (completed campaigns per candidate, failures, GPU state) to a dated `reports/` file. Keep monitoring after the author is back; his return does not stop B1.
- **On normal completion:**
  - release the lease;
  - restore the Track S and Track P state per the reviewed sequence;
  - run the complete-batch verifier;
  - publish the B1 manifest and the verifier result.
- **B2, X.7 and sweep 2 are not authorized tonight.** B2 needs B1 complete, the accepted B2 ranking and its own note.

### 0.5 Host access and GPU, outside the B1 run

From the 00:49 words, ENGINEERING_ONLY host work on TASL-2, TASL-7 and deepthought is also allowed: host checks, determinism tests, test suites, latency and memory measurements, and site qualification. Rules:
- Read `~/r1_locks` and STATUS before acting. If another agent or operator holds the host or GPU, do not touch it.
- Never pre-empt a running job (R1-TRACKS-S01-FOLLOWUP-REV), and nothing on TASL-7's GPU while B1 runs.
- Release every lease, and stop every server you start.
- Work in your own dated directories. Do not modify Track S, Track P or Track X work trees, servers or `$WORK` data. Never delete remote files.
- **HoreKa stays with the HoreKa agent** (R1-SERVER-AGENTS-TWO); do not log in there.
- Record every host action — commands, times, GPU UUIDs, outputs, sha256 — in a dated `reports/` file, independently reviewed.

### 0.6 Unchanged rules

`MAC_OVERNIGHT_PROMPT_20261105.md` §1 and §2 apply, except that the server/model/GPU limit is replaced by §0.3–§0.5:
- No author decisions beyond §0.1–§0.5. Silence on the other questions is not a decision.
- Never push `main`, `r1` or `exam-x-*`. Never force-push. Never delete anything.
- Every unit is accepted only by a fresh independent reviewer.
- At most 3 workers.
- Minimal first.
- Time-box non-B1 items: 3 review rounds or about 2 hours, then move on.
- Commit and push each accepted unit at once.

## 1. Feedback on the report

The report is good. It separates accepted scope from STOP cleanly and claims nothing beyond the evidence. But the 5 Nov goal ("B1 signable with one line") was not met, and nothing has been pushed since 07:24 on 5 Nov.

The critical path is B1 → B2 → X.7 → sweep 2, with M3 → M4 in parallel, then audits → D8 → B.7 (≈ 8 Dec). The HoreKa freeze is 20 Nov 12:00. Tonight's goal is **B1 launched**, with B2 ranking and M3/M4 moving in parallel.

## 2. Work — three workers in parallel

### Worker A — B1 to launch (priority 1)

Work through the §0.3 conditions in order:
1. Q2 JSON (§0.2) and its review.
2. Residual tests, kill/resume coverage, and the full Mac CPU suite on the integrated head. Record the failure-ID diff against the historical 39, and run Mac-specific failures on TASL-7.
3. The PLAN rows and the approved-note candidate.
4. The final combined checkout and its review.
5. TASL-7 host checks and the determinism test.
6. The adapted handover sequence, operator message v3 update, and its review.
7. The dry run.
8. Launch and monitoring (§0.4).

### Worker B — B2 ranking (priority 1, in parallel)

B2 follows B1, and X.7 needs its ranking. Implement the minimal v2 ranking exactly as `x5_rule_v2` states:
- enforce the complete node/instance grid;
- refuse duplicate primary candidates;
- rank by thinking-off audited Y;
- break ties by lower GPU-h.

Add tests and take it to ACCEPTED, so that B2 can be authorized as soon as B1 completes.

### Worker C — the sweep-2 path (priority 2, in parallel)

**(a) M3.** Continue toward a minimal accepted offline replay: the Linux supervisor, HUP vs monitor failure, all 16 cases bound in the reviewed execution path, and the offline executability proof. The Linux site qualification may run under §0.5 once the supervisor code is accepted.

**(b) The parts of M4 that do not touch `r1/scripts/c3_label_sweep.py`.** These can proceed now without breaking the shared-file rule:
- step 1, the harness pin candidate on `r1-local-20261104` (not merged into `r1`);
- the `llama_server_instance.py` parts of steps 2(a) and 2(e);
- step 3, the config template;
- step 4, the DTQ tool, with its dry run against a fake server;
- their tests.

The `c3_label_sweep.py` edits wait for M3's accepted commit.

If the DTQ tool is accepted, you may run it once on deepthought's two cards under §0.5, with the largest Stage A finalist's GGUF as the worst case. The author is waiting for DTQ results ("先等 DTQ 结果"). The result is a measurement only; the pass criterion is the author's.

If you judge that starting these M4 parts conflicts with `MAC_LOCAL_RUNBOOK_20261104` §M4 or the separation rule, do not start them; add them to the question list.

### If capacity remains

1. M11 D8 gate to ACCEPTED, so the author can commit R1-BX-D8-CONFIRM.
2. The M10 EVIDENCE/HK6 path.

## 3. Morning report

At about 08:30 CET on 7 Nov, in Chinese for the author, in the same format:
- **First line:** B1 launched or not. If launched: start time, progress, ETA and any STOP. If not: the failing §0.3 condition and what unblocks it.
- **The Q2 result:** the interval, or the fallback and why.
- Every host action and GPU use, with its report file.
- Each other blocker: closed, or what remains, who must act, and the effort.
- The updated question list.
- Push everything.
