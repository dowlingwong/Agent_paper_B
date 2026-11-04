# Review — HoreKa agent runbook, revision 1 (4 Nov 2026)

**Reviewer:** independent fresh agent (Claude), AI-assisted. I reviewed documents only. I started no run, opened no session, and committed or pushed nothing.
**Under review:** `docs/r1/prompts/HOREKA_RUNBOOK_20261104.md` (rev 1), branch `docs/runbooks-04nov`, commit `0e13a9fc`.
**Evidence read:** `reports/HOREKA_SCAN_20261104.md` and its raw files `reports/horeka_scan_20261104/{query_scan,probe_out}.txt`; `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (rev 2) and `reviews/HOREKA_1GC_REVIEW_20261104.md`; `prompts/TRACK_G_RUNBOOK.md`; `RUNBOOK.md` (banner, §1, §3, Track G); `PLAN.md` §10 (R1-BX-D1…D14, R1-BX-REVISIONS, the 11:29 rulings including R1-BX-PROPOSED-CONFIRM and R1-BX-PORTING-CONFIRM, R1-COMPUTE 13 Oct, R1-EXAM-TRANSFER, R1-T1-HOREKA, R1-SERVER-AGENTS-TWO); `prompts/HOREKA_SCAN_PROMPT_20261104.md` rev 5.6; `prompts/HOREKA_QUEUE_PROBE_PROMPT_20261104.md` rev 1; `prompts/OPERATOR_RUNBOOK_20261104.md` rev 3.3; `prompts/MAC_LOCAL_RUNBOOK_20261104.md` (M10). Slurm semantics checked against the `sbatch` manual (slurm.schedmd.com, read 4 Nov).

Line numbers refer to the runbook unless another file is named.

## Verdict

**NOT ACCEPTED.** 1 BLOCKING, 11 MAJOR, 13 MINOR, 6 NIT.

| Class | Count |
|---|---|
| BLOCKING | 1 |
| MAJOR | 11 |
| MINOR | 13 |
| NIT | 6 |

**What holds.**
- Most of §0.1 matches the scan: the account and fair-share factor 0.79, `PrivateData`, the partition shapes, dev QoS 1/3, the `--test-only` dates, the 29-minute backfill, the GPU index renumbering, Xorg at 17 MiB, the driver, storage, modules and the downtime dates.
- The `--deadline` statement in §0.5 is **correct**. The `sbatch` manual says: "Remove the job if no ending is possible before this deadline (start > (deadline − time[-min]))". With `--time=T` and no `--time-min`, Slurm never starts a job that cannot end by the cutoff. The scan's warning (its "Surprises" item 2) was about deadlines fixed earlier than the real cutoff.
- The runbook keeps the scan's fixes: an explicit `--mem` (DefMemPerGPU 186,720 MB), mapping GPUs through `CUDA_VISIBLE_DEVICES` and UUIDs, an occupancy check that ignores Xorg, a 90-job ceiling under MaxSubmitJobs = 100, polling no more often than every 60 s, and own-job views only.
- It keeps the governance invariants of the operator runbook: authority order, fresh-reviewer loop, never touching others' jobs, pins, run labels, the seed rules (7006–7010 evaluation only, exam seeds excluded, 8001–8010 floors, K = 10 until a D3 row), R1-BX-D8 gating, "authorizes nothing", and Chinese/English reporting.
- Most agent additions are marked *(proposed)* or *(open)*.

**What fails.**
- A PLAN *(open)* item on who submits production jobs is presented as answered (BLOCKING-1).
- The design premise rests on a backfill claim the scan does not support (MAJOR-1).
- The cutoff, freeze and copy-back times contradict each other (MAJOR-2).
- The one-session-per-user limit of the `agent` QoS is missed (MAJOR-3).
- The 300 GPU-h STOP can be bypassed by self-submitting jobs, and the budget basis is wrong (MAJOR-4).
- The label-validity argument has real holes: timeouts and OOMs counted as divergence, timing-dependent kernels, k and placement ordering, co-location (MAJOR-5, MAJOR-6).
- A shared-node localhost exposure is not handled (MAJOR-7).
- The sealed copy-back is not defined (MAJOR-8).
- The second proposer is stated as decided without a PLAN row (MAJOR-9).
- The §8 row mixes agent text into the decision cell (MAJOR-10).
- Two adopted Track G steps are missing: D28 liveness and S1.1 (MAJOR-11).

## Answers to the six checks (short)

1. **Factual accuracy.** Mostly correct. Overstatements:
   - Every GPU-node fact comes from the single **dev** node `hkn0901`, not from the `gpu-h100` nodes `hkn[0902-0922]` (m1).
   - "backfill admits short ones quickly" is not shown for `gpu-h100` (MAJOR-1).
   - Self-submission was tested only with `--test-only` (m2).
2. **Slurm semantics.**
   - `--deadline`: correct as stated. Add: never use `--time-min`, and treat the `DEADLINE` state as expected (m2).
   - `--exclusive`: shown only by a `--test-only` estimate (128 processors). Acceptable.
   - `--mem` defaults: correct for the GPU partitions. The `cpu` partitions use DefMemPerCPU = 1,945 MB instead (n1).
   - MaxSubmit: correct, but it counts all of the user's jobs. There is also a running-job limit, GrpJobs = 50 (n2).
   - dev QoS: correct. It is shared by `dev-cpu` and `dev-gpu-h100` (n2).
   - PrivateData: correct. `sinfo_t_idle` looks filtered (n3).
3. **Scientific validity.**
   - The fixed-step argument is necessary but not sufficient (MAJOR-5).
   - The floor-vs-label rule is right, but the phase order breaks it and "placement" is undefined (MAJOR-6).
   - J3 co-location fits in memory but is untested for result identity (MAJOR-6). Its localhost server is exposed on shared nodes (MAJOR-7).
   - One GPU model per table: confirm that the production nodes are the same SKU as the dev node (m1).
   - Seeds: right, but J5's seed sets are not written out (m6).
   - Budget: 8 × 40 = 320 and 8 × 60 = 480 are right, but the basis is wrong (MAJOR-4).
4. **Safety and compliance.**
   - Login-node use: correct (two commands).
   - The `nodessh-raw` wrapper works for how git and rsync call ssh. Git calls `<cmd> [-o SendEnv=GIT_PROTOCOL] vscode-hk2 "git-receive-pack '<path>'"`, and its AUTO variant probe `-G` succeeds. rsync calls `<cmd> vscode-hk2 rsync --server …`. Problems: remote paths must be absolute, the placeholder is fragile, and there is no gate check (m3).
   - No credentials: correct, except for gated Hugging Face artefacts (m13).
   - Never touching others' jobs: correct.
   - Cutoff and copy-back: contradictory (MAJOR-2).
   - Production submission by the agent: not settled (BLOCKING-1).
5. **Governance.**
   - R1-T1-HOREKA says H100, and the runbook keeps H100 with H200 as *(open)*: correct.
   - The second proposer is **not** a PLAN row. R1-BX-D6 and R1-BX-PROPOSED-CONFIRM D6 (F3) still say an API model (MAJOR-9).
   - The §8 row needs restructuring (MAJOR-10).
   - The porting branch and authority rest on a *(proposed)* consequence (m7).
6. **Executability.**
   - Session concurrency (MAJOR-3).
   - Missing steps: D28 and S1.1 (MAJOR-11).
   - H0 is circular with the §8 row (MAJOR-10).
   - Unit and interruption handling (m5).
   - Build pitfalls (m4).
   - The term "H1" is overloaded (m8).
   - The schedule depends on the author's 2FA availability, including on a Saturday (m9).

---

## Findings

### BLOCKING

**BLOCKING-1 — The runbook says the NHR@KIT question is answered and lets the agent (and the jobs) submit production jobs. PLAN keeps both open.**
*Evidence.*
- Runbook line 304: "the NHR@KIT question of draft §4 is answered by the tunnel route".
- Draft line 72: "(a) is largely answered; (c) remains". Question (c), draft line 79: "does an LLM-driven loop running inside a GPU batch job (the campaign proposer) count as an 'AI agent workload' that belongs in the `agent` partition?"
- PLAN line 794, R1-T1-HOREKA *(open)*: "Whether agents may submit and monitor jobs routinely stays open until NHR@KIT answers the draft's §4 questions. **Until then the author submits production jobs.**"
- The runbook nevertheless has the agent submit every J1–J5 job (lines 142–150, 250–257), and has jobs submit their own continuations (lines 140, 265).
- The proposed §8 row (line 320) does not mention that it would settle or override this open item.

The tunnel route answers only "where may the agent's commands run". It does not answer (c). J3 runs an LLM proposer that drives code edits inside `gpu-h100` batch jobs, and (c) is exactly about that.

*Fix.*
- Replace line 304 with: "The tunnel route answers where the agent's commands run (draft §4 (a)). Question (c) — whether the J3 proposer loop inside GPU batch jobs is an 'AI agent workload' — is *(open)*, and so is routine job submission by the agent (PLAN R1-T1-HOREKA, *(open)*: until NHR@KIT answers, the author submits production jobs)."
- Add to §7 a new item 1: "**Production submission and question (c).** Either (i) the author sends questions (a) and (c) to NHR@KIT support and records the answer, or (ii) the author rules in the §8 row that the HoreKa agent submits production jobs from the `agent` node, including self-submitted continuations, and that J3 runs inside GPU batch jobs, pending NHR@KIT's answer."
- Add to §8's *(open)* list: "who submits production jobs; NHR@KIT question (c)".
- Add to §5: "any reply from NHR@KIT that restricts agent submission or LLM loops in batch jobs".
- Until the row exists, J1b, J2, J3 and J4 on `gpu-h100` are submitted by the author (the agent prepares them with `hk2_submit.py --dry-run`).

### MAJOR

**MAJOR-1 — The design premise "backfill admits short [jobs] quickly" is not supported by the scan for `gpu-h100`, and nothing covers the case where the probe refutes it.**
*Evidence.*
- Line 130: "The scan shows a deep `gpu-h100` queue for long and wide jobs, and backfill admits short ones quickly." Line 41: "**Short, small jobs.** The queue probe decides how short".
- Scan line 158: "the 1-GPU 4 h shape is **no better** (11-12T00:26)".
- The only fast start was the 15-minute job in **`dev-gpu-h100`**. That is a separate one-node partition (`Nodes=hkn0901`, `QoS=dev`; query_scan lines 126–131) with its own queue. It says nothing about backfill in `gpu-h100`.

*Fix.*
- Line 130: "The scan's `--test-only` estimates give 12 Nov for both 4 × 24 h exclusive and 1 × 4 h. A 15-minute job in the separate `dev-gpu-h100` partition was backfilled in 29 minutes. *(proposed hypothesis, tested by the queue probe)* short 1-GPU jobs start much earlier than their estimates in `gpu-h100` too."
- Add an H0 branch: "If no measured `gpu-h100` or `gpu-h200` 1-GPU shape started within 24 h of submission, STOP. The author chooses between accepting the later start, H200 (an amending row), the Ada whole-table fallback (R1-T1-HOREKA), or a smaller T1 scope."
- Note that the probe takes one sample per shape at one moment.

**MAJOR-2 — The cutoff, the freeze and the copy-back contradict each other.**
*Evidence.*
- Line 120: "At the cutoff [22 Nov 00:00] no job of yours is running or pending, and every result is copied to the Mac."
- Line 123: every job sets `--deadline=<cutoff>`, "and never anything earlier". So a job can **run until 22 Nov 00:00**.
- Line 125: on 21 Nov, "submit nothing new after 12:00 … Copy everything back and verify". That copy-back happens while jobs may still run for up to 12 h.
- The continuation guard in §3 item 1 (line 255) refuses only "now + `--time` passes the cutoff", so self-submitted continuations are **not** stopped by the 12:00 freeze (lines 140, 265).
- Results produced between the 21 Nov copy-back and 22 Nov 00:00 are not copied before the 24 h margin. Any copy after 00:00 eats into it.
- 21 Nov 2026 is a **Saturday**, and the copy needs the author's 2FA master connection.

*Fix.* Define three distinct times *(proposed)*:
- **Submission freeze F = 21 Nov 12:00 CET.** `hk2_submit.py` refuses every submission after F, continuations included. Write this into §3 item 1 and item 6.
- **Job-end cutoff C = 21 Nov 18:00 CET.** All three guards use C. `--deadline=C`, never earlier. Submission refuses now + `--time` > C. The in-job check stops before C.
- **Copy-back deadline D = 22 Nov 00:00 CET.** Copy-back and the `SHA256SUMS` check run between C and D.

Then restate line 120 as: "by D every job has ended and every result is copied and verified". Update §0.5, §2 H8, §4, §5 ("21 Nov 12:00"), §7 item 2 and §8. Add to §7: "the author confirms availability for a session on Sat 21 Nov after 18:00, or moves F, C and D one day earlier."

**MAJOR-3 — The `agent` QoS allows one session per user at a time. The runbook ignores this, while H0 overlaps with the queue probe's sessions.**
*Evidence.*
- QoS `agent` has `MaxTRESPU=cpu=2` (scan line 97).
- With only the scan session 120262 running, the association showed `GrpTRES=cpu=N(2),mem=N(3890)` and `GrpJobs=50(1)` (query_scan line 74). One session therefore takes both allowed CPUs: 2 × DefMemPerCPU 1,945 MB = 3,890 MB.
- A second session by the HoreKa agent, the queue-probe agent or the author's own VS Code session would pend. The scan procedure then STOPs at "No snippet after 5 minutes" (scan prompt line 129).
- The schedule runs the queue probe and H0 on the same days (line 273).
- Also: sessions last ≤ 1 h (line 56). The scan procedure forbids ending a reply while a session is open (scan prompt line 115). So every status check or copy needs the author's master connection, opened with 2FA. This bounds the monitoring cadence, and the runbook does not state it.

*Fix.* Add to §0.2:
- "*(proposed)* **One `agent` session per user.** The QoS `agent` caps a user at 2 CPUs, which one session uses (scan: `GrpTRES cpu=N(2)` with one session). Before asking for the master connection, ask the author to confirm that no other session of his is open (his own, the scan or queue-probe agent's). Never run a session while another agent's session is open. A session that pends more than 5 minutes is the scan procedure's STOP; report it as 'session slot busy'."
- "**Cadence.** Work in sessions of ≤ 1 h, each opened at the author's request. State in each report when you need the next session and why. Nothing in the plan may depend on monitoring more often than the author can open sessions."

**MAJOR-4 — The 300 GPU-h STOP can be bypassed, and the budget basis does not match the ledger.**
*Evidence.*
- Line 114: the ledger is filled "from `sacct` after each job ends", by the agent, who is present only in author-opened sessions.
- Jobs submit their own continuations (lines 140, 265) between sessions, with no budget check in `hk2_submit.py` (lines 250–257). A continuation chain can therefore pass 300 or even 400 GPU-h unseen.
- Basis: line 116 quotes 320/480 GPU-h from REVISIONS (f) / draft §7. Those numbers are per-run GPU time at 2-minute runs: floor ≈ 2, executions ≈ 8, audits ≈ 30–50 per node (TRACK_G line 104). The ledger counts **allocation** time (elapsed × GPUs, line 114).
- Not in the estimate:
  - J3's sequential campaigns (W = 20 proposal-then-run cycles per root, with the GPU allocated throughout);
  - per-job start-up (venv, a GGUF load of up to about 20 GB, data copy);
  - the census of **every screened candidate**, not only the 8 retained ones (R1-BX-D12 funnel);
  - J0, J1 and J1b;
  - the H5 pilot;
  - re-runs of cut units;
  - S1.1 (MAJOR-11).
- Under every estimate the 300 STOP triggers inside H6 or H7, whatever K is.

*Fix.*
- §3 item 1: "`hk2_submit.py` refuses a submission when used GPU-h (own jobs from `sacct -X -u $USER -S <campaign start>`, AllocTRES `gres/gpu` × elapsed) plus reserved GPU-h (time limit × GPUs of every own pending or running job) plus the new job's time limit × GPUs exceeds the STOP threshold (300, *proposed*). Continuations go through the same check."
- §0.4: "Projections are in allocation GPU-h and include the census of all screened candidates, setup, smoke, qualification, the pilot, re-runs and S1.1."
- Add a gate before H6: "STOP after H5 with the projection for H6 + H7 at the K in force. The author fixes the node count, K and the budget before any G.5 note."

**MAJOR-5 — "Fixed step budgets → co-tenancy changes only throughput, never the metric" (line 134) is not true as the system stands.**
*Evidence and mechanisms.*
1. **Wall-clock timeout feeds the outcome class.** The port carries "a timeout of 3 × the measured run time" (TRACK_G line 28; runbook line 187, "resource limits"). Divergence is defined as "a non-finite loss, **or no metric at the fixed budget**" (PLAN line 749, E5; line 728 (c)). A run slowed by neighbours on the node, by k runs on the GPU, or by llama-server in J3 can time out. It then ends with no metric and is recorded as a **divergence**, which "is never re-run to hide it" (line 92). The same applies to an OOM caused by co-located processes.
2. **Timing-dependent numerics.** `torch.backends.cudnn.benchmark = True` (common in CIFAR-style baselines) picks kernels by timing, so contention can change the numerics. Non-deterministic atomics also exist.
3. **CPU-count-dependent behaviour.** A DataLoader `num_workers` or BLAS thread count taken from `nproc` changes the per-worker RNG streams and the summation order when `-c` differs.
4. Line 135 ("the census measures the metric noise in this same layout") holds only if the floor runs are spread across jobs and compute nodes the way labels are. Determinism is checked only as "the same seed twice" (line 197), possibly within one job.

*Fix.*
- Replace lines 133–136 with a conditional argument: fixed step budgets make the metric independent of throughput **only if** (a) the port forces deterministic algorithms (`cudnn.benchmark = False`, `torch.use_deterministic_algorithms(True)`, `CUBLAS_WORKSPACE_CONFIG`), or else records their absence; (b) worker and thread counts are fixed in the NodeSpec, never derived from `nproc`; (c) the H3 determinism check runs the same seed in **two different jobs on two different compute nodes, one of them under load** (k = 4 plus a llama-server load), and compares bitwise.
- If (c) fails, σ̂ is estimated from floor seeds spread over at least 3 jobs on different compute nodes, and this is disclosed.
- Add to §0.3: "*(open, for the author)* **Infrastructure failure vs divergence.** A run killed by the timeout, by Slurm (time limit, node failure) or by an OOM while co-located processes exceed their declared memory is an *infrastructure failure*: recorded, its unit re-run whole, and never counted as a divergence. An OOM within the run's own memory cap stays an outcome of the edit. Two infrastructure failures of the same unit is a STOP."
- Set the timeout from the runtime measured **at the chosen k and placement** (MAJOR-6).
- Add to §5: "an infrastructure-failure rate above 2 % in any wave *(proposed)*".

**MAJOR-6 — Floor and labels are not guaranteed the same k and placement. The phase order defeats the rule, and co-location is never tested.**
*Evidence.*
- Line 91 requires "the same runs-per-GPU k and the same placement as its labels".
- H3 measures the floor (step 4, line 197) **before** the concurrency sweep (step 6, line 200). "Then the author fixes … k" (line 204). Unless the author picks the k the floor happened to use, the floor is re-measured, costing GPU-h nobody planned.
- "Placement" is never defined. J3 puts llama-server on the same GPU as task runs (line 148). The accepted draft review required, for that case, to "show in J2 that GPU 0 slots give the same results" (`HOREKA_1GC_REVIEW` line 118, m7). The runbook replaces this with "the pilot checks the fit" (memory only, line 221).
- J1b checks within-server identity (line 146) but not under J3's co-located load, which is the T1 serving configuration (one serving configuration per tier, PLAN line 749 E1/E2).

*Fix.*
- Define in §0.3: "**Placement** = (GPU model; 1-GPU job on a shared compute node; k task runs per GPU; whether llama-server shares the GPU; `-c` and `--mem` per run; worker and thread counts). Labels are the J4 audit runs: no llama-server, k fixed."
- Reorder H3: determinism → concurrency sweep (k = 1, 2, 4; throughput plus identity at each k) → STOP: the author fixes k → floor at that k and the J4 placement → D21.
- Add to J2: "a co-location arm — the baseline × 3 seeds with an active llama-server load on the same GPU — compared bitwise with the same seeds without it. If they differ, J3 does not co-locate (the draft's separate-GPU layout) unless the author rules otherwise."
- J1b: "the identity test runs once on an idle GPU and once with k task runs on the same GPU".

**MAJOR-7 — On shared compute nodes, llama-server on `127.0.0.1` is reachable by other users' jobs, and its port can be pre-empted.**
*Evidence.*
- Line 148: llama-server is "bound to 127.0.0.1, port from `SLURM_JOB_ID`".
- On TASL, deepthought and Ada the loopback interface was effectively ours. Under the runbook's own 1-GPU design (line 133: "Other users' jobs on the same node"), other users share the node's loopback interface. Any process on the node can then (i) send requests to our server, which adds load and changes the latency records, or (ii) bind the derived port first. The harness would then talk to a foreign server, and the proposals would not come from the pinned model.
- Nothing in §3 checks the server's identity.

*Fix.* In §3 item 3 and the J3 row:
- "llama-server starts with `--api-key` set to a random per-job token generated inside the job. It is not a credential to any outside service. The harness sends it on every request.
- Before the first request, the runner checks that the listening socket on the port belongs to its own llama-server PID (`ss -ltnp`), and that the server's reported model path and sha match the pin.
- If the derived port is taken, choose the next free port and record it.
- Any mismatch is a STOP."

**MAJOR-8 — The analysis-gate copy-back is undefined, and the generic copy-back breaks it.**
*Evidence.*
- Line 93: "Copy-back for safety (§0.5) goes to a sealed folder that analysis code does not read."
- Line 79: the copy-back is `rsync -a … r1/results/ <Mac worktree>/results/r1/trackg/hk2/`, then "Commit JSON, manifests and `.jsonl`".
- That copies every sweep-2 T1 ledger, audit record and J5 table into a committed, non-sealed path. R1-BX-D8 (PLAN line 721) forbids copying a sweep-2 label table back "for analysis or read by any analysis code" before R1-BX-D8-CONFIRM.
- The sealed folder has no path, no commit rule, and no reader-side refusal.

*Fix.*
- On HoreKa, write EVIDENCE outputs (H6, H7, J5) under `$PROJECT/r1/results/evidence/` and everything else under `$PROJECT/r1/results/engineering/`.
- Before R1-BX-D8-CONFIRM, the regular copy-back syncs `engineering/` only. The safety copy (§0.5) syncs `evidence/` to `<Mac>/results/r1/trackg/hk2_sealed/`. *(proposed)* That folder is not committed to `mac-int-*` or `hk2-ops-*`; only its `SHA256SUMS` and file counts are committed.
- Ask the Mac agent (M10/M11) to make every analysis reader refuse the `hk2_sealed/` path, in addition to the D8 PLAN-line check.
- State this in §0.2 and §0.3.

**MAJOR-9 — The second proposer is stated as decided ("a local model") without a PLAN row, against the standing rows.**
*Evidence.*
- Line 94: "Since 4 Nov (packet (j), the author's '用 exam 第二名') the second proposer is a local model".
- PLAN line 719, R1-BX-D6: "One **API proposer**, in closed-loop evaluation only".
- PLAN line 749, R1-BX-PROPOSED-CONFIRM D6 (F3): "a commercial mid-tier model of a family other than the main proposer's … cost cap €100–200".
- "Packet (j)" is the Mac agent's list of questions for the author (`MAC_LOCAL_RUNBOOK` lines 406–426), not a decision. A grep of `docs/` finds "用 exam 第二名" only in this runbook.
- Separately, the second proposer serves only closed-loop evaluation (G.6/D.3), whose host plan is *(open)* (PLAN line 810). Qualifying it on HoreKa (line 208) is outside the T1 scope that R1-T1-HOREKA gives this agent.

*Fix.*
- Line 94: "**Secrets.** Never read `~/.config/r1/secrets.env` or any key file. No API calls run on HoreKa. *(open)* The author has said in chat '用 exam 第二名' (use the exam runner-up instead of an API model) for the second proposer. That is not yet a PLAN row: R1-BX-D6 and R1-BX-PROPOSED-CONFIRM D6 (API, other family, cost cap) still stand until an amending row is committed."
- Line 208: "*(open)* The second proposer is qualified here only if an amending R1-BX-D6 row and the Phase C/D host plan put its closed loop on HoreKa."
- Add both to §7 and to §8's *(open)* list. Flag for the author: the runner-up may be of the same family as the pick, which F3 excludes.

**MAJOR-10 — The §8 row puts agent text in the decision cell, cites words that do not adopt the runbook, and is circular with H0.**
*Evidence.*
- Line 320's decision cell opens with an agent sentence in bold, "The HoreKa agent runs the T1 tier … by `prompts/HOREKA_RUNBOOK_20261104.md`". It then quotes the 17:12 words as if they supported it, and holds *(proposed)* and *(open)* text inside the same cell.
- The 17:12 words approve the queue probe, accept 400 GPU-h, say 12 Nov is too late, and **ask for** a runbook ("写 HoreKa 执行 runbook"). None adopts one. The same pattern was MAJOR-1 of `HOREKA_1GC_REVIEW` (line 44: keep the cell to the author's words and put consequences below the table).
- The row does not list what it amends or settles: R1-T1-HOREKA's *(open)* "author submits production jobs" (BLOCKING-1); its *(proposed)* "draft becomes the design basis"; R1-BX-PORTING-CONFIRM's branch `ops-trackg-<date>` (m7); R1-ADA-CENSUS.
- Circularity: line 16 says ENGINEERING_ONLY work needs the row, but H0 step 3 (a HoreKa session) runs before it, and H0 step 4 (line 168) has the author "write T_max and the GPU model into the PLAN row". A committed dated row is amended by a new row, not edited.
- Line 318 says the Mac agent "records it", while line 16 says it holds once "the author has committed" it. Both can be true, but say so.

*Fix.*
- Decision cell: "**[the author's words when he adopts it, quoted verbatim, with time]**". Leave it empty in the draft.
- Context line above the table: the four 17:12 quotes, with "400 GPU-h" rendered as "the author accepted 400 GPU-h" (m11).
- Below the table, "Consequences noted by the recording agent (not part of the decision)": the *(proposed)* design items, the amended or settled rows listed above, and the *(open)* items, with BLOCKING-1's and MAJOR-9's items added.
- H0: steps 1–2 are Mac-side desk work. Move step 3 (reading the session script) to H1. T_max and the GPU model are fixed by a **second** dated row ("R1-HOREKA-TMAX"), not by editing this one.
- Line 318: "the Mac agent drafts the row on `mac-int-20261104`; it holds once the author commits it or tells the Mac agent in chat to commit it".

**MAJOR-11 — Two adopted Track G steps are missing: D28 diff liveness, and the S1.1 interaction measurement.**
*Evidence.*
- TRACK_G G.1b step 4 (line 66): "**D28 liveness** with the main proposer … 2 instances × W = 10".
- R1-BX-D12 screens "under D21 and D28" (PLAN line 725). R1-BX-PROPOSED-CONFIRM D4 (E3): a pick that fails diff liveness on a T1 node is a STOP.
- The runbook mentions it only as "waits for X.7 and the pinned G.2" (line 204). No phase runs it, yet G.3 (the T1 list) follows H3 directly.
- G.5 bullet (TRACK_G line 95) and R1-BX-D4: "The S1.1 edit–edit interaction measurement on each T1 node". It is absent from H6/H7 and from the budget.

*Fix.*
- Add an H4b, "D28 liveness (G.1b step 4; ENGINEERING_ONLY)". Needs X.7, G.2 pinned and J1b passed. One J3-shaped job per candidate node, 2 instances × W = 10. Output: the D28 column of the census report.
- State that the G.3 row waits for H4b, or that the author fixes G.3 provisionally and confirms it after H4b.
- Add S1.1 to H6 (as in TRACK_G G.5), with its GPU-h in the H3 and H5 projections.

### MINOR

**m1 — GPU-node facts come from the dev node only.**
*Evidence.*
- Lines 38, 42–44 attribute to `gpu-h100` nodes "95,830 MiB each … 755 GB per node", the 3.4 TB `/scratch`, Xorg and network access "from GPU nodes".
- The probe ran on `hkn0901` (probe_out line 9), which is the `dev-gpu-h100` node (query_scan line 131). The `gpu-h100` nodes are `hkn[0902-0922]` (query_scan line 103).
- "755" is the `free -g` figure (GiB). Slurm's allocatable memory is 746,880 MB per node (15,684,480 M / 21).
- Network was tested by `curl -sI` against front pages only. Hugging Face file downloads are redirected to CDN hosts, and the MLAgentBench and OGB dataset hosts were not tested.

*Fix.*
- Mark these "measured on `hkn0901` (dev); confirm from the queue-probe job outputs (GPU name and memory per node) in H0".
- Use 746,880 MB.
- In J0, test the exact download URLs (with redirects) before relying on them.
- H0 confirms that the production nodes have the same GPU SKU as the dev node, as one GPU model per table requires.

**m2 — Self-submission and environment.**
*Evidence.*
- Line 47 says self-submission was "tested with `--test-only`", but lines 140 and 265 treat it as working.
- `SLURM_*` variables are always propagated to the submitted job (`sbatch` manual).
- The agent node's sshd exports the session job's 70 `SLURM_*` variables (scan line 23), and a parent job exports its own. Stale `SLURM_MEM_PER_*` or `SLURM_NTASKS` values can make an `srun` inside the child fail or mis-size it.
- A job removed by `--deadline` ends in state `DEADLINE`.

*Fix.*
- `hk2_submit.py` calls `sbatch` with a scrubbed environment (`SLURM_*` and `SBATCH_*` removed).
- Templates never use `srun` unless tested.
- H1 includes one real self-submission test (a `cpu` job submitting one `cpu` job).
- Templates never set `--time-min`.
- The status tool and the ledger treat `DEADLINE` as expected: no re-submission, reported.

**m3 — `nodessh-raw` details.**
*Evidence.*
- Lines 64–72: the quoted heredoc leaves a literal `S="<this session folder>"` for the agent to edit by hand.
- Line 76: "`vscode-hk2:<path under $PROJECT>`". Git single-quotes the path in `git-receive-pack '<path>'`, and rsync ≥ 3.2.4 escapes remote arguments, so `$PROJECT` is not expanded.
- The wrapper does not check `gate2_ok`, and it has no time limit, unlike `nodessh`.
- macOS may ship openrsync rather than rsync.

*Fix.*
- Generate the first line with `printf 'S=%q\n' "$S"`.
- Add `[ -e "$S/gate2_ok" ] || { echo "gate2 not passed"; exit 1; }`.
- Write remote paths absolute (`/hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/...`).
- Add `rsync --timeout=300`.
- Record `rsync --version` and `git --version` on the Mac in the H1 report.
- Create the bare repositories with `"$S/nodessh" 'git init --bare <abs path>'` before the first push.

**m4 — Build and bootstrap.**
*Evidence.*
- J0 builds llama.cpp on the `cpu` partition (line 144), whose nodes (`hk2n*`, 384 CPUs, query_scan line 145) are not the GPU nodes' AMD EPYC 9354 (scan line 312). The ISA is unmeasured, and llama.cpp builds with `GGML_NATIVE` on by default, so the binary may hit an illegal instruction on the GPU nodes.
- CUDA 12.9's `nvcc` does not accept the newest GCC. The cluster's own pairing is `NCCL/2.27.7-GCCcore-14.3.0-CUDA-12.9.1` (scan line 221).
- `hk2_submit.py` must run before J0 has built the venv. The system `python3` is 3.9.21 (scan line 243), and the harness needs ≥ 3.11.

*Fix.*
- Build with `-DGGML_NATIVE=OFF -DCMAKE_CUDA_ARCHITECTURES=90`, or build inside the `dev-gpu-h100` job.
- Pair `CUDA/12.9.1` with `GCC/14.3.0` *(proposed)*.
- Write `hk2_submit.py` and `hk2_status.py` with the standard library only, compatible with Python 3.9, and test them under 3.9.

**m5 — Units, interruptions and evidence.**
*Evidence.*
- Line 139: a cut unit "is discarded".
- Line 109: "Never delete evidence".
- `/scratch` is per-job and private (scan line 326) and presumably removed at job end.
- A unit longer than T_max is cut every time, so continuations loop.
- A trial killed mid-run leaves the harness `*_pending.json` guard.

*Fix.*
- Use `#SBATCH --signal=B:USR1@600`. On the signal, the runner archives the partial unit to `$PROJECT/r1/results/_interrupted/<jobid>/` (never read for labels) and exits.
- A unit cut twice is a STOP.
- H5 must show that a campaign root fits in ≤ 0.6 × T_max at the chosen k.
- Re-runs start from a fresh working copy, so no pending guard is carried over.
- The ledger records each interruption.

**m6 — J5 seed sets are not written out.**
*Evidence.* Line 150 says "from label seeds only", while the draft J5 row (line 61) and R1-MAIN-PROPOSER (b) / PROPOSED-CONFIRM (E4) give the sets.
*Fix.* "Labels from 7001–7005 at K = 10, or 7001–7003 at K = 6; evaluation columns only from 7006–7010, or 7006–7008; J5 refuses any other seed."

**m7 — Porting authority and branch name.**
*Evidence.*
- Line 103 names `hk2-trackg-20261104` without a marker.
- R1-BX-PORTING-CONFIRM (PLAN line 741) names `ops-trackg-<date>` and "the operator". The move to the HoreKa agent is a *(proposed)* consequence of R1-SERVER-AGENTS-TWO (PLAN line 808). TRACK_G line 57 says "proposed `hk2-trackg-<date>`".
- `MAC_LOCAL` M10 (line 416) still points to the draft's §5, not to this runbook's §3.

*Fix.*
- Mark the branch *(proposed)*.
- List "porting by the HoreKa agent on `hk2-trackg-<date>`, amending R1-BX-PORTING-CONFIRM" among the §8 row's consequences.
- Note that `MAC_LOCAL` M10's HoreKa paragraph must be updated to this §3 once the row exists.

**m8 — Ambiguous terms.**
*Evidence.*
- "H1" is both the environment phase (line 170) and the pending B.7-timing item (lines 282, 315; PLAN line 753).
- "node" means both a harness task and a compute node ("several jobs per node", line 147).
- "expected time" (line 291) is undefined, and Slurm caps runtime at `--time` anyway.
- "only where a measurement needs them" (line 130) names no measurement.

*Fix.*
- Rename the phases HK0–HK8, or call the item "the B.7-timing item (PLAN 'H1')".
- Use "task node" and "compute node".
- Replace the 50 % STOP with "a unit takes more than 1.5 × its H5-measured time".
- Either name the exclusive measurement or delete the clause.

**m9 — Schedule realism.**
*Evidence.*
- Every session needs the author's 2FA master connection (line 60).
- The freeze falls on a Saturday (see MAJOR-2).
- Thursdays 07:00–09:00 are the weekly reboot window (scan line 183; 12 and 19 Nov).
- Each STOP has a fresh-review loop.
- Fair-share 0.79 will fall with heavy use.
- A queue surge after the downtime is likely from 5 Dec.
- The queue probe gives one sample per shape.

*Fix.* Add these to §4 as risks. Say that H2/H3 cannot outpace the author's session availability, and that the post-downtime start of H6/H7 may itself wait days. This strengthens line 282.

**m10 — The probe's shape should bind the templates, and H0's input has no path.**
*Evidence.*
- The probe's 1-GPU shapes use `-c 32 --mem=180G` (`HOREKA_QUEUE_PROBE` lines 24–33).
- Line 152 leaves `-c` and `--mem` free.
- Line 162 names `HOREKA_QUEUE_20261104.md` but not where it is committed.

*Fix.* "Production 1-GPU jobs request no more than the probed shape (`-c ≤ 32`, `--mem ≤ 180G`); larger requests invalidate the measured wait." Give the path where the author or the Mac agent commits the probe report (for example `docs/r1/reports/HOREKA_QUEUE_20261104.md`).

**m11 — "400GPU小时没问题" is read as a hard cap.**
*Evidence.* Line 113 calls it "The author's budget". The words say 400 GPU-h is acceptable. Whether it is a ceiling is an interpretation.
*Fix.* "*(interpretation, for the author to confirm)* 400 GPU-h is treated as the ceiling."

**m12 — The occupancy check must exclude the job's own processes.**
*Evidence.* Line 261 exits on "a foreign compute process above that size". In J3 and J4 the job's own llama-server and k runs are compute processes above 256 MiB.
*Fix.* "Check at job start before launching anything, and afterwards only for PIDs not descended from the job's own processes (or not owned by `$USER`)."

**m13 — Gated artefacts.**
*Evidence.* "No credentials on HoreKa" (line 75), while J0 downloads GGUFs and datasets inside jobs (line 144). A gated Hugging Face repository would need a token.
*Fix.* "Only ungated URLs pinned by revision and sha256 are downloaded on HoreKa. A gated artefact is fetched on the Mac and pushed through the tunnel with `rsync -e "$S/nodessh-raw"`. No token is ever placed on HoreKa."

### NIT

- **n1.** Line 152: "the default is 186,720 MB per GPU" holds for the GPU partitions. `cpu` (J0, J5) defaults to DefMemPerCPU = 1,945 MB (query_scan line 150).
- **n2.** Also note the association's running-job limit GrpJobs = 50 (query_scan line 72). The 90-job ceiling counts **all** of the user's jobs, including the queue probe's 10 jobs, which may pend until 7 Nov. QoS `dev` is shared by `dev-cpu` and `dev-gpu-h100`.
- **n3.** Line 37 recommends `sinfo_t_idle`. Its output shows "0 nodes n/a" for every GPU partition (scan lines 357–364), which looks filtered. Do not use it for planning.
- **n4.** Line 38, "`--exclusive` honoured": shown by a `--test-only` estimate (128 processors), not by a running job. Say so.
- **n5.** Give the deadline in the form the tool emits (`--deadline=2026-11-21T18:00:00`, cluster local time, CET in November; the probe printed `+01:00`), and check `date +%Z` on the agent node in H1.
- **n6.** H1's "the RUNBOOK §5 pin table" exists only after the Mac agent's M1 is accepted (`OPERATOR_RUNBOOK` line 10). List M1 under H1's needs.

---

## Required for acceptance

Fix BLOCKING-1 and MAJOR-1 to MAJOR-11. The MINOR and NIT findings should be applied or answered one by one. I will re-check the next revision against this list.

Verdict: NOT ACCEPTED

---

## Round 2 — re-check of revision 2 (commit `fbb33c15`)

**Reviewer:** the same independent agent (Claude), AI-assisted. Documents only. I edited nothing in the runbook and committed nothing.
**Checked:** `git diff 0e13a9fc fbb33c15 -- docs/r1/prompts/HOREKA_RUNBOOK_20261104.md`, the full revision 2 text, and its §9 answer table, against the round-1 required list. Line numbers below refer to revision 2. I ran the new `nodessh-raw` construction locally under a path containing spaces (scratch directory, stub `ssh` body).

### Status of the round-1 findings

| Finding | Status | Evidence in rev 2 |
|---|---|---|
| BLOCKING-1 (NHR (c), production submission) | **Resolved** (one new MINOR, R2-m1, on the mechanism) | Lines 133–140: the PLAN *(open)* item is quoted; the tunnel answers only (a); until the §7 item 1 ruling the agent submits only `dev-*` and `cpu` jobs for HK1/HK2, the author submits every `gpu-*` job, and there are no continuations. §3 item 1 (line 419), §5 (line 462), §6 (line 485), §7 item 1, §8 (line 518) |
| MAJOR-1 (backfill premise) | **Resolved** | Line 56 marks it a hypothesis, with "1 GPU × 4 h → also 12 Nov" and the dev partition named as separate; line 249; HK0 step 4 branch (lines 293–297); one-sample caveat (line 290) |
| MAJOR-2 (cutoff, freeze, copy-back) | **Resolved** | §0.5 table (lines 234–238); F in `hk2_submit.py` (line 416); C used for `--deadline`, the submission check and the in-job stop; the copy-back window runs from C to D. See "Points the coordinator asked about" (1) |
| MAJOR-3 (one session per user) | **Resolved** | Line 55; lines 73–81; §5 "session slot busy"; §4 risks |
| MAJOR-4 (budget bypass and basis) | **Resolved** | §0.4 lines 215–230: a submission guard counting used + reserved + new GPU-h, applied to the author's submissions too; allocation basis; the 320/480 figures as lower bounds; a STOP gate before HK6 (line 375) |
| MAJOR-5 (fixed steps not sufficient) | **Resolved** | Lines 169–184: conditions (a)–(c), the 3-job fallback, infrastructure failure *(proposed; §7 item 7)*, timeout at the chosen placement. HK3 step 3; HK2 step 1; §5 2 % STOP |
| MAJOR-6 (k and placement, co-location) | **Resolved** (one new MINOR, R2-m2) | Placement defined (lines 158–167); HK3 reordered with a STOP at step 6 before the floor (lines 333–341); co-location arm (step 5); J1b loaded identity test (line 265); J3 co-locates only if both pass (line 267) |
| MAJOR-7 (llama-server exposure) | **Resolved** (NIT R2-n2) | Lines 273–277; §3 item 3; §5 |
| MAJOR-8 (sealed copy-back) | **Resolved** (NIT R2-n3) | Lines 113–123; §3 item 6 |
| MAJOR-9 (second proposer) | **Resolved** | Lines 188–191 *(open)*, with R1-BX-D6 and PROPOSED-CONFIRM D6 standing; §7 item 6 with the family caveat |
| MAJOR-10 (§8 row, HK0 circularity) | **Resolved** | §8 decision cell holds only a placeholder for the author's words; the 17:12 quotes are a context line; consequences, amended rows and open items sit below the table. HK0 is desk work ending in a new row, R1-HOREKA-TMAX (line 298). Line 18 clarifies drafting vs committing |
| MAJOR-11 (D28, S1.1) | **Resolved** | HK4b (lines 351–359), with G.3 waiting for it; S1.1 in HK6 (line 385) and in the projection (line 226) |
| m1 | Resolved | Line 46 source note; 746,880 MB; HK0 step 2; HK1 step 4 |
| m2 | **Partly**; see R2-M1 | Scrubbed environment, `DEADLINE` handling and no `--time-min` are done. The real self-submission test (HK1 step 5) is placed wrongly |
| m3 | Resolved (NIT R2-n1 on invocation quoting) | Lines 86–101, 104 |
| m4 | Resolved (MINOR R2-m3 on placement) | Line 263; §3 items 1–2 |
| m5 | Resolved (MINOR R2-m4 on signal delivery) | Lines 251–257; §3 item 5 |
| m6 – m13 | Resolved | Seeds (line 156); branch *(proposed)* (line 200); terms (lines 27–30); 1.5 × STOP; §4 risks; probed shape (line 249) and report path (line 287); the budget as an interpretation (line 213); own-process exclusion (line 425); ungated downloads (lines 108–111) |
| n1 – n6 | Resolved | Line 269; line 50; line 51; line 52; line 237 and HK1 step 2; HK1 needs M1 (line 302) |

### Points the coordinator asked about

1. **F / C / D = Fri 20 Nov 12:00 / Fri 20 Nov 20:00 / Sat 21 Nov 18:00.** These are consistent and acceptable.
   - Between F and C there are 8 h, which is more than T_max (4 h by default). A job submitted just before F can still end by C.
   - `--deadline=C` removes any pending job that can no longer finish by C. That is correct Slurm semantics, and line 241 states it correctly.
   - D leaves 30 h before 23 Nov 00:00, so the margin still holds if the shutdown starts early that morning.
   - All later references match: §0.4 "since 20 Nov", §4, §5 "F is reached", §7 item 3, HK8.
   - The copy-back still needs one author-opened session between Friday 20:00 and Saturday 18:00. Line 240 and §7 item 3 make his availability an explicit item, which is enough.
2. **The interim rule (§0.3).** It is the right fix for BLOCKING-1: production `gpu-*` work waits for the author's ruling. Two gaps remain (R2-m1):
   - the mechanism by which "the author submits" is undefined;
   - the scope of the rule ("only for HK1 and HK2", line 138) and the tool's guard (only `gpu-*`, line 419) differ.
3. **The HK1 step 5 self-submission test inside QoS `dev`.** It cannot stay as written (**R2-M1**, below). It breaks NHR@KIT's rule on dev partitions and three rules of this runbook.
4. **The `nodessh-raw` heredoc.** The construction is correct.
   - I reproduced it with `$S` containing spaces: `printf %q` writes `S=/…/home\ sp/snap\ dir`, the quoted inner heredoc passes `"$S"` and `"$@"` through literally, the gate check refuses before `gate2_ok` exists, and arguments with spaces reach `ssh` intact.
   - Two fragile spots remain in how it is called (R2-n1). Under the same test, `GIT_SSH_COMMAND="$S/nodessh-raw"` (line 105) failed: git hands `GIT_SSH_COMMAND` to `sh`, which splits at the space ("…/home: not found"). With `GIT_SSH_COMMAND="'$S/nodessh-raw'"` the wrapper was reached.
   - `rsync -e` likewise splits its command at spaces unless quoted (rsync manual, `--rsh`).
   - The real path (`~/Documents/agent_paper_B/.claude-worktrees/_snapshots/…`) has no space, so this is a NIT.

### New findings (round 2)

**R2-M1 (MAJOR) — The HK1 step 5 self-submission test breaks NHR@KIT's dev-partition rule and three rules of this runbook.**
*Evidence.* Line 309: "a `dev-cpu` job submits one `dev-cpu` job … QoS `dev` allows only one running job, so the child waits until its parent ends". The QoS semantics are right (MaxJobsPU = 1, MaxSubmitPU = 3), but the test breaks four rules:
- NHR@KIT's Slurm page, as quoted in `reviews/HOREKA_1GC_REVIEW_20261104.md` line 122: "Do not misuse these partitions for regular, short-running jobs or **chain jobs**!" A job in a dev partition that submits a job in a dev partition is a chain job there.
- `hk2_submit.py` refuses "a second job in QoS `dev` while one is outstanding" (line 413). Continuations must go through `hk2_submit.py` (line 259), so the tool itself would refuse the child.
- §0.3 (line 140): "No job submits its own continuation", until the §7 item 1 ruling.
- Self-submission is needed only if the author allows continuations. Before that ruling, the test has no purpose.

*Fix.* Replace HK1 step 5 with:
> "*(only after the §7 item 1 ruling allows continuations)* One real self-submission test in `cpu`: a parent job (`-c 1 --mem=1G -t 00:05:00`) calls `hk2_submit.py` with a scrubbed environment to submit one child (`-c 1 --mem=1G -t 00:02:00 --wrap true`). Record the child's environment (`env | grep ^SLURM_`) and its `sacct` line. Never in a `dev-*` partition."

Also add to §1 Continuations: "never in a `dev-*` partition". Add to §3 item 1: "refuses any submission from inside a job (`SLURM_JOB_ID` set and partition ≠ `agent`) into a `dev-*` partition."

**R2-m1 (MINOR) — The author's submissions have no defined mechanism, and the rule's scope differs from the tool's guard.**
*Evidence.*
- Line 139: the author submits each `gpu-*` job "himself, in a session he opens for that". It does not say whether that is the agent's tunnel session (where the agent types) or his own terminal.
- The budget guard, F, C and the probed-shape checks apply "to every submission, the author's included" (line 220). That holds only if he uses `hk2_submit.py`, not plain `sbatch`.
- Line 138 limits the agent to `dev-*` and `cpu` "for HK1 and HK2". The tool refuses only `gpu-*` (line 419), so a `cpu` job in a later phase is not covered.

*Fix.*
- "The agent writes the manifest and the `--dry-run` output into the session folder. The author runs `hk2_submit.py submit <manifest>` himself from his own terminal, on the login node or in the agent session. A `gpu-*` submission asks for a confirmation typed at `/dev/tty`, which the agent's `BatchMode` calls never answer. The author always submits through `hk2_submit.py`, never plain `sbatch`, so the guards hold."
- Align line 138 and line 419: either both say "`gpu-*` only", or the tool also refuses agent submissions outside HK1/HK2.
- §4's gate column lists "the §7 item 1 ruling" for HK1 (line 438), yet §0.3 lets HK1 run without it. Remove the ruling from HK1's gate or explain it.

**R2-m2 (MINOR) — The 2-GPU J3 fallback is refused by the tool's own shape guard.**
*Evidence.*
- Line 267: if co-location fails, "J3 uses 2 GPUs, one for each".
- Line 249 and §3 item 1 (line 415) refuse any request above the probed shape, and the queue probe measured only 1-GPU and 4-GPU exclusive shapes.
- A 2-GPU job also doubles J3's allocation GPU-h.

*Fix.* Either allow `--gres=gpu:2 -c ≤ 64 --mem ≤ 360G` explicitly as an *(proposed)* unprobed shape (its first waits recorded, and its GPU-h in the HK5 projection), or name the fallback "the probed 4-GPU exclusive shape, running two campaigns' proposer–runner pairs". Add the choice to §7 item 5.

**R2-m3 (MINOR) — J0 now puts downloads and hashing on the single dev GPU node.**
*Evidence.*
- Line 263: J0 runs entirely in `dev-gpu-h100`, "≤ 1 h, in several steps". That includes the venv, downloads of GGUFs of up to about 20 GB, and sha256 checks.
- That node is the only one in its partition, QoS `dev` allows one job at a time, and HK2's smoke tests need the same slot.
- With `-DGGML_NATIVE=OFF` and an explicit CUDA architecture, the build no longer depends on the build host's CPU. So the round-1 reason to leave `cpu` (m4) no longer applies to the build itself.

*Fix.* "J0a in `cpu`: venv, downloads, sha256, and optionally the llama.cpp build (`GGML_NATIVE=OFF`). J0b in `dev-gpu-h100` (≤ 1 h): the GPU check and a one-token llama-server load. If J0a builds the binary, J0b also runs `llama-server --version` and a short CPU-side test on the GPU node, to rule out an illegal instruction."

**R2-m4 (MINOR) — `--signal=B:USR1@600` reaches only the batch shell.**
*Evidence.*
- Lines 254 and 271. With `B:`, Slurm signals only the batch script's shell.
- Bash runs a `trap` only after its foreground child exits, so a runner started as a plain foreground command never sees the signal in time.

*Fix.* Line 254: "the batch script `exec`s the runner, or starts it in the background and `wait`s with a `trap` that forwards `USR1`". Add a real-job test of this in HK1 (a `cpu` job with `-t 00:12:00` and `--signal=B:USR1@600`), besides the fake-signal unit test in §3 item 7.

**R2-m5 (MINOR) — The session folder changes, but the scan procedure's wrappers hard-code the scan folder.**
*Evidence.*
- Line 70: a new folder `hk2_session_<UTC date-time>` per session.
- The scan prompt rev 5.6 that line 69 reuses hard-codes `S=…/horeka_scan_20261104` in every block and inside the `nodessh` wrapper (scan prompt lines 50, 61, 68), and names `~/r1_scan_20261104/`. The queue-probe prompt handled this with an explicit "replace every occurrence" rule (`HOREKA_QUEUE_PROBE` change 1); revision 2 has none.

*Fix.* Add under "Sessions": "In every block and wrapper of the scan procedure, replace `horeka_scan_20261104` with this session's folder name. Remote files go under `/hfs2/…/r1/`, never `~/r1_scan_20261104/`. The scan's §3 query script and §4 probe are not run."

**R2-m6 (MINOR) — An unsourced claim.**
*Evidence.* Line 455: "With Track X's B1 now at 15 candidates". I found no source for "15 candidates" in PLAN, RUNBOOK, STATUS or the Mac and operator runbooks on this branch.
*Fix.* Cite its source (a STATUS entry or the author's words, with the date) or delete the clause. The conclusion that B.7 on 8 Dec with T1 labels is unlikely does not depend on it.

**R2-n1 (NIT) — The wrapper invocations are not space-safe.** Lines 105 and 110, and the copy-back `rsync`. Use `GIT_SSH_COMMAND="'$S/nodessh-raw'"` and `rsync -e "'$S/nodessh-raw'"`, or assert at session start that `$S` contains no whitespace.

**R2-n2 (NIT) — llama-server does not report a sha.** Line 275, "the server reports the pinned model path and sha". The runner should compute the GGUF's sha256 before launch, compare it with the pin, and then check that the server's reported model path is that file.

**R2-n3 (NIT) — The sealed folder sits inside a git worktree.** Line 120: `<Mac>/results/r1/trackg/hk2_sealed/`. If that path is inside a worktree, add it to `.gitignore` there, or place it outside every worktree, so that a `git add -A` cannot commit it.

**R2-n4 (NIT) — Per-job scratch loss is stated as fact.** Line 58, "/scratch … is lost at job end". The scan showed only a private per-job directory. Write "expected to be lost at job end; HK1 checks it".

### Governance re-check

- Nothing is attributed to the author beyond his quoted words. The 17:12 quotes are context only, and the §8 decision cell is an empty placeholder for his adoption words.
- Agent additions are marked: *(proposed)* for the times, the budget STOP, the infrastructure-failure rule, the branch, the sealed-folder rule and the job resources; *(open)* or *(interpretation)* for the second proposer, question (c), the 400 GPU-h ceiling and H200.
- No PLAN row is presented as existing that does not exist. R1-BX-D6 is stated to stand. R1-HOREKA-TMAX is described as a future row.
- The runbook still authorizes nothing before the §8 row (lines 17–20). Production `gpu-*` submission waits for the author's ruling.

### Round 2 verdict

All of BLOCKING-1 and MAJOR-1 to MAJOR-11 are resolved, and so are the round-1 MINOR and NIT findings, apart from m2's test placement. Revision 2 adds one new MAJOR (R2-M1, the dev-partition self-submission test), six MINOR and four NIT findings.

R2-M1 is a one-paragraph fix: move the test to `cpu`, after the §7 item 1 ruling, and add the two refusals. Once it is applied and R2-m1 to R2-m6 are applied or answered, I expect to accept without another full round; a check of the changed lines will be enough.

Verdict: not accepted

---

## Round 3 — re-check of revision 3 (commit `ea8757eb`), changed lines only

**Reviewer:** the same independent agent (Claude), AI-assisted. Documents only. I made no runbook edit and no commit.
**Checked:** `git diff fbb33c15 ea8757eb -- docs/r1/prompts/HOREKA_RUNBOOK_20261104.md`, the new rows of the §9 table, and whether the changed lines contradict any unchanged text. Line numbers refer to revision 3.

**Local tests.**
- I ran the §1 `USR1` pattern (`runner … & pid=$!; trap 'kill -USR1 "$pid"' USR1; wait "$pid"; wait "$pid"`) under bash 5.2 with a stand-in runner, on four paths:
  - no signal, runner exits 0: job rc 0;
  - no signal, runner exits 5: job rc 5;
  - `USR1` sent to the job shell, runner archives and exits 0: job rc 0;
  - `USR1`, runner exits 3: job rc 3.

  So the second `wait` returns the runner's own status on every path. This matches the coordinator's test.
- I looked for the source of the "15 candidates" clause. It is in PLAN on `mac-int-20261104` (lines 857–860): "B1 candidate set: the 8 PASS of `t7h8` + the anchors + the `t7j10` passes, the latter counting only after the operator's acceptance".

### Status of the round-2 findings

| Finding | Status | Evidence in rev 3 |
|---|---|---|
| R2-M1 (dev self-submission test) | **Resolved** | HK1 step 6 (line 316): no dev test; one `cpu` test, only after the §7 item 1 ruling. §1 continuations (line 265): "never from a dev partition (NHR@KIT: … chain jobs)". §3 item 1 (lines 420, 426): refuses any submission from inside a dev-partition job, and, until the ruling, any submission from inside a job. HK1 step 5's `USR1` test on one `dev-cpu` job submits nothing, so it is a setup test, not a chain |
| R2-m1 (how the author submits; scope) | **Resolved** (NITs R3-n1, R3-n2) | §0.3 (lines 138–140): the agent's scope is `dev-*`/`cpu` in any phase, matching the tool's `gpu-*` guard. The author runs `hk2_submit.py --submit --author <manifest>` from his own terminal, with all guards. "You never pass `--author`". §4 gate column moved to HK2/HK3 (lines 445–446) |
| R2-m2 (2-GPU J3 fallback) | **Resolved** | J3 row (line 273): author ruling at HK3 step 6, a manifest-flag exception to the probed-shape guard, and doubled GPU-h in the projection |
| R2-m3 (J0 on the dev node) | **Resolved** | J0 row (line 269): venv, downloads, hashing and the `GGML_NATIVE=OFF` build on `cpu` (16 cores, ≤ 2 h); `dev-gpu-h100` ≤ 30 min only for the GPU check |
| R2-m4 (`--signal=B:`) | **Resolved** (NIT R3-n3) | §1 units (lines 254–260): background-and-wait pattern, verified above; real-job test in HK1 step 5 |
| R2-m5 (session folder in the wrappers) | **Resolved** | §0.2 Sessions (line 70). The `~/r1_scan_20261104/` name does not arise, because only §1 steps 0–5 are reused and they create no remote files |
| R2-m6 (15 candidates) | **Resolved** | §4 (line 462) is now conditional on O1's acceptance, and its basis is in PLAN on `mac-int-20261104` (lines 857–860). The count "7 passing" is not checked here. The conclusion does not depend on it |
| R2-n1 (spaces) | **Resolved** | Line 101 forbids spaces in the session path. Line 105 quotes `GIT_SSH_COMMAND="'$S/nodessh-raw'"`, the form I verified in round 2 |
| R2-n2 (sha) | **Resolved** | Line 281: the runner hashes the GGUF itself and compares `/props`'s model path. HK1's GPU check should confirm that the pinned llama.cpp commit reports the path in `/props`. If it does not, use the server's `--alias` or its startup log line |
| R2-n3 (sealed folder in a worktree) | **Resolved** | `~/r1_sealed/hk2/` lies outside every worktree. Readers refuse `r1_sealed/` (§0.2 line 120; §3 item 6) |
| R2-n4 (`/scratch` at job end) | **Resolved** | §0.1 storage row (line 58) |

### Consistency of the changed lines with the rest

- **Submission rules.** §0.3, §1 continuations, §3 item 1, HK1 steps 5–6 and the §4 gates now agree. Until the ruling: the agent submits `dev-*`/`cpu` jobs only, the author submits `gpu-*` jobs with `--author`, and no job submits a job. After it: continuations are allowed, never from a dev partition, and only through the guards.
- **Dev QoS.** HK1 step 5 (one `dev-cpu` job) and J0's GPU check (one `dev-gpu-h100` job) are sequential single jobs, within `MaxJobsPU = 1`.
- **Sealed folder.** Every mention was updated. No reference to `hk2_sealed/` remains in the runbook.
- **F / C / D, the budget guard and the probed shape** are unchanged and still apply to the author's `--author` submissions (lines 140, 220).

I found no new contradiction.

### New findings (round 3)

All are NITs and optional. None blocks acceptance.

- **R3-n1 — Where the author's manifest lives on HoreKa.** Line 139: the manifest and its dry-run are "committed", and the author runs the tool "in the pinned checkout under `$PROJECT`". The manifest sits on the agent's `hk2-ops` branch on the Mac, not in that checkout. *Fix:* "In its session, the agent writes the manifest to `/hfs2/…/r1/manifests/<name>.json`. The committed dry-run records its sha256. The author's command names that path, and the tool prints the sha before submitting."
- **R3-n2 — `--author` rests only on an instruction.** Only line 139's "You never pass `--author`" keeps the agent from using it. *Optional fix:* with `--author`, the tool also requires an interactive terminal (`sys.stdin.isatty()`) and a typed confirmation of the manifest sha. The agent's `BatchMode` calls have no terminal.
- **R3-n3 — The trap pattern breaks under `set -e`.** With `set -e`, the first `wait` (status > 128 after the trap) ends the script before the second `wait`. *Fix:* the job script does not use `set -e` around these lines. Add a one-line note in §1 and a template test.
- **R3-n4 — HK1's deferred step.** HK1 step 6 runs only after the ruling. *Fix:* say that HK1's acceptance does not wait for it, and that the test gets its own short review when it runs.

### Governance re-check

- The changed lines attribute nothing new to the author.
- The new design choices are marked *(proposed)* or come with an author ruling point: the manifest-flag exception, the `cpu` J0 resources, and the `~/r1_sealed/` location under the existing *(proposed)* bullet.
- No PLAN row is presented as existing that does not exist.
- The runbook still authorizes nothing before the §8 row. Production `gpu-*` work still waits for the author's ruling or his own `--author` submission.

### Round 3 verdict

Every finding of rounds 1 and 2 is resolved. The changed lines add no contradiction. R3-n1 to R3-n4 are optional NITs that can be applied without another review round.

Verdict: accepted
