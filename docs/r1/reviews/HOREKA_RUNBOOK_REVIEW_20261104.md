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
