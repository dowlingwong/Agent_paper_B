# Review — R1-1GC-FALLBACK propagation and the HoreKa 2 T1 job draft (4 Nov 2026)

**Reviewer:** independent fresh agent (Claude), AI-assisted. Documents only; no run started, nothing committed or pushed.
**Scope:** commit `bf402b24` (`git diff 7a19d568 bf402b24`) on `docs/runbooks-04nov`: `README.md`, `docs/r1/{PLAN,RUNBOOK,STATUS,C3_DESIGN,TECH_ROUTE}.md`, `docs/r1/prompts/{MAC_LOCAL_RUNBOOK_20261104,OPERATOR_RUNBOOK_20261104,TRACK_G_RUNBOOK}.md`, and the new `docs/r1/proposals/HOREKA_T1_JOBS_DRAFT_20261104.md`.
**Sources checked:** recommendation A4 in `docs/r1/proposals/RECOMMENDATIONS_1121_20261104.md` (line 6); the author's words as quoted in the commit (11:55 "1GC-7RC没公开repo"; 12:45 "1GC-7RC 换成 MLAgentBench我同意"); the author's cheat sheet (chat attachment `horeka_job_submission.md`); <https://docs.nhr.kit.edu/usage/slurm/> and <https://docs.nhr.kit.edu/get-started/migration/>, both fetched 4 Nov.

## Summary

| Class | Count |
|---|---|
| BLOCKING | 0 |
| MAJOR | 7 |
| MINOR | 11 |

**What holds.** The 1GC-7RC → MLAgentBench change reaches every live tier statement: README, PLAN §6 banner, §9 item 5, §10 index, RUNBOOK banner, Track G table, G.0 and risk table, TRACK_G §1, G.0 and §6, both execution runbooks, C3_DESIGN and TECH_ROUTE. `grep -rn 1GC docs/r1 README.md` finds no live text that still treats 1GC-7RC as a suite, except two PLAN passages that need a forward pointer (m1). The remaining hits are dated history (R1-BENCH-HARD, R1-TRACKG-SCOPE, older STATUS entries, overnight handoffs, the expansion review, `MAC_LOCAL_RUNBOOK.md`). G.0 reads the same way in RUNBOOK, TRACK_G and OPERATOR O8. The T1/T2 lists agree across README, RUNBOOK and TRACK_G. Every count still says three suites, which is the number leave-one-suite-out needs.

The HoreKa draft is clearly marked as a draft: "not adopted", "authorizes nothing", and the host choice is the author's (lines 3, 90; STATUS line 3). It gets most cluster facts right: partition and time are mandatory, `gpu-h100` has 4 × H100 and a 2-day maximum, the job limits are 100/300 and dev partitions allow one job, the `squeue` interval is ≥ 30 s, no compute on login nodes, AI agents are prohibited on login nodes, the `agent` partition exists, `$HOME` is 50 GB / 2 M inodes, there is one `PROJECT` per project, EasyBuild, and Slurm accounting. Unknowns (internet, scratch, GPU memory, containers) are marked *(to check)*. The 75 % audit share matches R1-BX-REVISIONS (f) (30 of 40 GPU-h). Seeds 8001–8010 match E4. The author does the submitting until NHR@KIT answers.

**What fails.** The PLAN row adds substance that A4 and the author's words do not contain (MAJOR-1). In the draft, the pairing rule contradicts the resume scheme (MAJOR-2). The wall-time example is wrong by a factor of 3 (MAJOR-3). The downtime guard cannot be implemented as written (MAJOR-4). One unverified claim ("whole GPUs, no co-tenancy") is used to drop safety checks (MAJOR-5). The staging tool runs on the login node with no named runner (MAJOR-6). The list of PLAN rows the move would change is incomplete (MAJOR-7).

## Check (a) — the R1-1GC-FALLBACK row against A4 and the author's words

A4 (verbatim): "1GC-7RC 仓库：operator 在 G.0 第一天查；若仍未公开，用 MLAgentBench 作第三个 suite，不按论文自建；1GC 的公开数据集可以作为额外任务，但不算 suite。"

| Row clause (PLAN line 773) | In A4 / author's words? |
|---|---|
| 1GC-7RC not a suite; MLAgentBench is the third suite | Yes (A4 + 12:45) |
| Not rebuilt from the paper | Yes ("不按论文自建") |
| Public datasets may be extra tasks, not a suite | Yes |
| "disclosed" | No. Taken from R1-BX-D2's *(open)* text; harmless, but not A4 (MAJOR-1) |
| "The three suites are therefore autoresearch, MLGym and MLAgentBench" | Follows directly; acceptable |
| MLAgentBench light tasks "become T1 candidates as well as T2 candidates, chosen in the census (G.0/G.1b) and fixed by … G.3" | **No.** A tier placement of the recording agent's own (MAJOR-1) |
| "amends R1-BX-D2's suite list and resolves the Pending A4 item" | Bookkeeping; acceptable |
| "The remaining G.0 licence check covers MLAgentBench's task assets" | No. Follows from R1-BX-REVISIONS (e), not from A4 (MAJOR-1) |
| A4's "operator checks on G.0's first day; if still not public" | Silently dropped. Justified by the author's 11:55 statement, but the row should say so (MAJOR-1) |

## Findings

### MAJOR

**MAJOR-1 — The decision cell adds content beyond A4 and the author's words.**
*Location:* PLAN §10 "4 November 2026 (11:55, 12:45)", row R1-1GC-FALLBACK (line 773).
The cell is headed "Author decision", but it contains four agent-derived clauses: the T1+T2 candidacy of MLAgentBench light tasks, "disclosed", the licence-check sentence, and the census mechanism. It also drops A4's G.0 first-day condition without saying why. The T1 candidacy is a real consequence: R1-BX-D1 ("train on two suites, test on the third") needs labelled T1 nodes in every suite. But it is a consequence, not something the author said, and the row never states the requirement that makes it necessary.
*Fix:* Keep the decision cell to A4's clauses and the author's two quotes. Add a separate line under the table, "Consequences noted by the recording agent (not the author's words)", with: (i) A4's G.0 check is moot because the author stated at 11:55 that the repository is not public; (ii) leave-one-suite-out needs at least one labelled T1 node per suite, so the G.3 selection must include at least one MLAgentBench T1 node, or the author rules otherwise; (iii) the R1-BX-REVISIONS (e) licence check now covers MLAgentBench's task assets; (iv) disclosure of the extra tasks, citing R1-BX-D2. Mark (ii) *(proposed)*.

**MAJOR-2 — The pairing rule contradicts the J4 resume scheme.**
*Location:* draft §3, the "Pairing rule" (line 45) against the J4 row (line 42).
Line 45 says the candidate and incumbent "run on all K seeds inside the same job … Pairs are never split across jobs". J4 resumes from a per-run cache ("as `r1/c3/audit.py` `RunCache`") and is "re-submitted until the shard is done". A job that hits its deadline partway through a pair leaves some of that pair's runs cached. The next job then runs the rest, so the pair is split across jobs, which line 45 forbids. Sharding (§5.5) keeps pairs whole across shards but not across resubmissions.
*Fix:* Either make the pair the unit of resumption (a pair's 2K runs are committed together and partial pairs are discarded at the deadline), or restate the rule as the repo actually has it: common seeds, one GPU model per table, same node type. Say which one in §3 and §5.5.

**MAJOR-3 — The wall-time arithmetic is wrong.**
*Location:* draft §7, "GPU-hours" (line 99).
"Wall time ≈ 400 / (GPUs held × speed-up × k). For example, 8 GPUs give about 2 days at a speed-up × k of about 3." But 400 / (8 × 3) ≈ 16.7 h, about 0.7 days. "About 2 days" matches speed-up × k ≈ 1 (400 / 8 = 50 h). The example feeds the author's decision about what fits before 22 Nov. Two smaller problems: "assumed 2-minute runs on a 4090-class card" is not in R1-BX-REVISIONS (f), and the 400 GPU-h assumes K = 6 and 10 T1 nodes. At K = 10 (still in force until the D3 check passes), (f) gives about 60 GPU-h per node, about 600 for 10 nodes. After R1-1GC-FALLBACK the T1 candidate list has 8 entries (1 + 4 + 3).
*Fix:* Correct the example: about 17 h at 8 GPUs and speed-up × k = 3, or about 50 h at speed-up × k = 1. State the K = 6 / 10-node assumption and give the K = 10 figure. Drop "4090-class" or source it. Re-check §7's B.7 sentence against the corrected numbers.

**MAJOR-4 — The downtime guard cannot work as written, and its edges are not sourced.**
*Location:* draft §1 downtime row (line 16); §5.1 second bullet (line 63); §7 (lines 95–97).
`hk2_submit.py` is to refuse "any job whose start plus `--time` reaches 2026-11-23 00:00". The start time is not known at submission: a job can wait in the queue and start later. The sources also say only "Nov 23 – Dec 4". That means the 00:00 Europe/Berlin start, an inclusive 4 Dec end ("From 5 Dec"), what happens to pending jobs, and whether the date applies to HoreKa 2 or to legacy HoreKa are all inferences. Neither NHR page mentions the downtime. The migration page gives only legacy HoreKa's "reduced operation" to 2026-12-04.
*Fix:* Make the guard work at run time. (a) Pass Slurm's `--deadline=<downtime start − margin>` so Slurm drops any job that cannot finish in time. (b) Have each job check the time left to the downtime at start and pass the smaller value to the collector's `--deadline`. (c) At submission, refuse `now + --time ≥ downtime − margin`. Mark the exact start and end times, and the fate of pending jobs, *(to check)* with NHR@KIT. Add that check to §6.

**MAJOR-5 — "Whole GPUs, no co-tenancy, no interruption" is unverified and used to drop checks.**
*Location:* draft §2 second bullet (line 29); §5.3 second bullet (line 71).
The Slurm page lists `gpu-h100` with access policy **"Shared"**. It documents `--exclusive` as the way to reserve a full node, and says nothing about preemption. The draft states "No co-tenancy, and no interruption by other users" as fact, unmarked. On that basis §5.3 skips the `gpu_uuid` occupancy wait and the co-tenancy margin check.
*Fix:* Mark the claim *(to check)*. Give J2–J4 `--exclusive` (or `--gres=gpu:4` with the partition's full CPU and memory, stated explicitly). Keep a light occupancy check in `slurm` mode (`nvidia-smi` shows no foreign processes at start, recorded in provenance) rather than skipping it.

**MAJOR-6 — The staging tool runs on the login node, and no one is named to run it.**
*Location:* draft §5.6 (line 79) against §4 (lines 51–55).
§4 has the author do submission, status and copy-back, because AI agent use on login nodes is prohibited. The migration page's prohibition includes "running AI agent processes, API calls, or similar interactive workloads". §5.6's staging tool runs "on the login node" with no named runner. If the operator runs it over SSH, that is the prohibited case. Hashing multi-GB GGUFs and datasets is also borderline under "compute intensive tasks must not run on login nodes".
*Fix:* State that the author runs the staging tool, in the same way as §4.1. Move sha256 verification (and any extraction or preparation) into a `cpu` job. If compute nodes have internet *(to check)*, move the download there too, and keep the login node for plain transfers.

**MAJOR-7 — The draft does not list all the decided rows that a move to HoreKa would change.**
*Location:* draft status paragraph (line 3); §2; §9 item 1 (line 112).
The draft names only R1-BX-PROPOSED-CONFIRM ("T1 label runs on Ada"). Moving "census, noise floors, proposer, campaigns, audits" (§9.1) would also amend:
- **R1-ADA-CENSUS** (census and noise floors on Ada);
- **R1-BX-D14** ("noise floors and liveness start on Ada");
- **R1-BX-REVISIONS (f)** (a floor measured on Ada sets σ̂ only for Ada tables);
- the **E1 proposer-host clause** of R1-BX-PROPOSED-CONFIRM (deepthought two TITANs if O5 passes, else a 4090; one serving configuration per tier);
- RUNBOOK G.0's GPU-model list and OPERATOR O0/O8's "Ada first".

An H100-served proposer is a new serving configuration (its own sm_90 binary sha). It would need a qualification like O5 before it serves sweep-2 T1. The draft also does not say what happens to the Ada census that O8 starts after STOP 0. "Ada as fallback" (§9.1) must mean the whole table moves, or R1-BX-D5 is broken.
*Fix:* List these rows and runbook steps in the status paragraph and §9. Add a §9 item for the proposer host and its qualification. State whether the Ada G.0/G.1b work continues (raw cost only; σ̂ only for Ada tables). State that a fallback to Ada moves the whole T1 label table.

### MINOR

**m1 — PLAN still has two pre-12:45 passages without a forward pointer.**
*Location:* PLAN line 752 (the "Pending" bullet **R1-1GC-FALLBACK (A4, as recommended)**, same id as the new adopted row); PLAN line 715 (R1-BX-D2's *(open)* "STOP for the author … rebuild … or make MLAgentBench the third suite").
The §10 index records the adoption, but a reader of the 11:29 subsection still sees the item as pending.
*Fix:* Append "(adopted 4 Nov 12:45; see the next subsection; this bullet is history)" to line 752, and "(resolved by R1-1GC-FALLBACK, 4 Nov)" to R1-BX-D2's *(open)* clause. Optionally note the 12:45 adoption under A4 in `RECOMMENDATIONS_1121_20261104.md`.

**m2 — The Mac-runbook pending sentence is garbled.**
*Location:* `prompts/MAC_LOCAL_RUNBOOK_20261104.md` line 150.
The line reads "H1 (A4, the 1GC-7RC fallback, was adopted at 12:45 as R1-1GC-FALLBACK) — (the B.7 timing and its partial-T1 fallback)". H1's description has been split from H1.
*Fix:* "**Pending …:** H1 (the B.7 timing and its partial-T1 fallback). A4 (the 1GC-7RC fallback) was adopted at 12:45 as R1-1GC-FALLBACK."

**m3 — The runbooks put the 1GC extra tasks in a tier and leave their role open.**
*Location:* RUNBOOK lines 198–199; TRACK_G lines 17–18.
The extra tasks sit inside the **T1** cell, but A4 gives them no tier. The documents also do not say whether they count toward the 12–16 target, how the per-suite screening funnel (R1-BX-D12) reports them, or what they do in the leave-one-suite-out folds (always training, or excluded). The heavier 1GC tasks are also treated inconsistently: TinyImageNet and VOC are struck from T2, while the lighter 1GC datasets stay listed.
*Fix:* Move the italic note out of the T1 cell into a line below the table: "1GC-7RC public datasets: possible extra tasks, no suite; tier, count toward 12–16, funnel reporting and LOSO role are open for G.3". Treat TinyImageNet and VOC the same way as the others.

**m4 — Domain coverage and cross-suite near-duplicates.**
*Location:* TRACK_G line 15; RUNBOOK G.3.
"Time series" is still in the domain list, but only ETTh1, now a no-suite extra task, covered it. Five domains are still reachable without it. MLAgentBench's cifar10, and reportedly its house-price task, closely match MLGym's CIFAR-10 and House Price. A held-out suite that shares a near-identical task with a training suite weakens leave-one-suite-out.
*Fix:* Note in G.0/G.3 that cross-suite near-duplicates are flagged in the census and either avoided in T1 or disclosed. Note that time series is covered only if the author admits an extra task.

**m5 — No STOP for an MLAgentBench screening failure.**
*Location:* RUNBOOK risk table (line 378).
The 1GC STOP was struck and nothing replaced it. R1-BX-D2's "only if cheap" condition on MLAgentBench is gone. If MLAgentBench's light tasks fail cost, D21 or D28 at G.0/G.1b, fewer than three suites have labelled T1 nodes and leave-one-suite-out collapses.
*Fix:* Add a risk row: "No MLAgentBench task qualifies for T1 → STOP for the author".

**m6 — The draft does not say how evaluation seeds are kept out of the label table.**
*Location:* draft J4/J5 rows (lines 42–43); §5.5.
Audits run on all K seeds. J5 "build[s] the T1 label table" from merged caches that also hold the evaluation seeds (7006–7010; 7006–7008 at K = 6).
*Fix:* State that J5 builds labels from the label seeds only (7001–7005, or 7001–7003). Evaluation-seed results are stored apart and not read for labels, under R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE.

**m7 — Concurrency k and GPU 0 co-location are new run conditions.**
*Location:* draft J2/J3 rows (lines 40–41); §5.4.
J2 measures k only for throughput. Label runs must use the k at which the noise floor was measured, or the census must show the metric does not depend on k. On GPU 0, task runs share the card with llama-server, so they run under different VRAM and contention than runs on GPUs 1–3.
*Fix:* Fix k before any labels are built and record it in provenance. Either keep task runs off GPU 0 in J3, or show in J2 that GPU 0 slots give the same results.

**m8 — Dev-partition use and job-script directives.**
*Location:* draft J5 row (line 43); §5.1 (line 65).
J5 on `dev-cpu` conflicts with the Slurm page ("Do not misuse these partitions for regular, short-running jobs or chain jobs!") and with the tool's own refusal of "a dev partition used for production". The templates also do not set `--ntasks`, `--cpus-per-task` and `--mem` (required on shared nodes, per the migration page and the cheat sheet), or `--account` (needed with more than one project, and `$PROJECT` follows the default account).
*Fix:* Run J5 on `cpu`. Have `hk2_submit.py` require explicit `--account`, `--ntasks`, `--cpus-per-task` and `--mem`/`--mem-per-cpu`.

**m9 — Attribution and unsourced details.**
*Location:* draft §1 line 15; §2 line 28; §5.5 line 77; J0 line 38.
The hostname `hk2-x86.scc.kit.edu` and the user `ka_ir7683` come only from the cheat sheet; the Slurm page has neither, and the migration page gives only the generic `ka_` prefix. "GPFS" and "sm_90" are not in the sources. "The cross-model rule change proposed on 4 Nov" has no anchor in the repo. The limit is per association ("MaxSubmitJobs=100"), not strictly per user.
*Fix:* Attribute each fact to its own source. Mark the file-system type *(to check)*. Cite or delete the cross-model reference.

**m10 — The question for NHR@KIT is too narrow.**
*Location:* draft §4.3 (line 55).
The question covers `sbatch`, `squeue` and `rsync` from outside, and a dispatcher in the `agent` partition. It does not ask whether the J3 workload itself (an LLM proposer driving code edits on `gpu-h100` compute nodes) counts as an "AI agent workload" that the centre wants on `agent` or allows on GPU partitions.
*Fix:* Add that question.

**m11 — The schedule leaves out the gates it depends on.**
*Location:* draft §7 (lines 94–97); J1 (line 39).
The 15–22 Nov window has the G.4 pilot and possibly a first J3 + J4 (G.5) wave. These depend on: the Track X pick (X.7, with TASL-2 held until about 15 Nov), since J1 also loads "the main proposer's GGUF"; the author's G.3 row; the M10 diff-support pin; the K row (D3 check); and, for G.5, the author's EVIDENCE authorization note. None of these is listed.
*Fix:* Add a gates column to §7 naming each prerequisite. Say that no code in §5 starts before a PLAN row adopts the draft.

## Verdict

The 1GC-7RC propagation is complete and consistent, apart from MAJOR-1 and m1–m5. The HoreKa draft decides nothing, but needs MAJOR-2 to MAJOR-7 fixed before the author can rely on it.

Verdict: not accepted

---

## Round 2 — re-check of commit `d5bcf108` (`git diff bf402b24 d5bcf108`)

**Reviewer:** the same independent agent (Claude), AI-assisted. Documents only; nothing committed or pushed. The files checked are PLAN, RUNBOOK, `prompts/MAC_LOCAL_RUNBOOK_20261104.md`, `prompts/TRACK_G_RUNBOOK.md` and `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (revision 2). The round-1 text of this review is unchanged in that commit.

### Status of the round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| MAJOR-1 (row adds to A4) | **Resolved** | PLAN line 773. The cell now holds A4's clauses and the author's two quotes. The dropped first-day check is explained by the 11:55 quote. The agent's consequences are below the table under "not part of the decision", with *(proposed)* and *(open)* marked where they matter, and the leave-one-suite-out requirement is now stated. |
| MAJOR-2 (pairing vs resume) | **Resolved** | Draft J4 row and §3 "Pairing". The pair is the resume unit: it is written only when complete and is otherwise discarded and re-run whole. §5.5 matches. |
| MAJOR-3 (arithmetic) | **Resolved** | Draft §7. 8 × 40 = 320 and 8 × 60 = 480 GPU-h. 320/24 ≈ 13 h and 480/24 = 20 h are correct. The K = 10 figure follows (f): the audit share rises to about 50, giving about 60 per node. "4090-class" is gone, and the 3-of-4 GPUs caveat for J3 is stated. |
| MAJOR-4 (downtime guard) | **Resolved** (one new MINOR, n2) | Draft §5.1. The guard now has three layers: a check at submission, Slurm `--deadline`, and an in-job clock check. The start hour, whether 4 Dec is included, and pending jobs are marked *(to check)* (§1, §6.5). |
| MAJOR-5 (shared nodes) | **Resolved** | Draft §1 row 25 now matches the Slurm page ("Shared"; `--exclusive` reserves a whole node). Exclusive allocation is *(to check)*. §5.3 keeps a light occupancy check instead of skipping it. |
| MAJOR-6 (staging on the login node) | **Resolved** | Draft §4.1 and §5.6. The author runs `hk2_stage.py` (downloads only), and hashing moves to J0b on `cpu`. |
| MAJOR-7 (rows affected) | **Resolved** (one residual MINOR, n3) | Draft §0 lists R1-BX-PROPOSED-CONFIRM (f)/E1, R1-ADA-CENSUS, R1-BX-REVISIONS (f), R1-BX-D14, RUNBOOK G.0, TRACK_G and OPERATOR O0/O8. It adds a qualification for an H100-served proposer (J1b) and makes the fallback move the whole table. |
| m1 (PLAN forward pointers) | **Resolved** | PLAN line 752 is struck through and marked "Adopted 4 Nov 12:45". R1-BX-D2 carries "Settled 4 Nov 12:45". The optional note in `RECOMMENDATIONS_1121_20261104.md` was not added; that is acceptable. |
| m2 (garbled Mac line) | **Resolved** | MAC_LOCAL line 150 now reads as suggested. |
| m3 (extra-task placement) | **Resolved** | RUNBOOK lines 198–199 and TRACK_G lines 17–18: tier, count toward 12–16 and fold role are now marked open for G.3, and TinyImageNet and VOC are treated like the other datasets. The note still sits in the T1 cell, but it no longer assigns a tier. The funnel question is in PLAN's consequences. |
| m4 (domains, near-duplicates) | **Resolved** | Recorded as *(open)* in PLAN's consequences. TRACK_G line 15 still lists time series, which is acceptable now that the open item exists. |
| m5 (no MLAgentBench STOP) | **Resolved** (one consistency MINOR, n1) | New RUNBOOK risk row. |
| m6 (evaluation seeds in labels) | **Resolved** | Draft J5: labels come from label seeds only (7001–7003 / 7001–7005), and evaluation seeds go only into evaluation columns. |
| m7 (k and GPU 0) | **Resolved** | Draft §3 "Same k" rule (same k and placement as the floor; the floor is re-measured if k changes). GPU 0 runs no tasks in J3 (§5.4). |
| m8 (dev partition, directives) | **Resolved** (see n4) | J5 runs on `cpu`. The templates set `--account`, `--ntasks`, `--cpus-per-task` and `--mem`. |
| m9 (attribution) | **Resolved** | The host and user come from the cheat sheet only (row 24, sources line). `sm_90` and the file-system type are *(to check)*. The cross-model reference is removed. "Per user" for the 100-job limit stays; the page says per association, which is negligible here. |
| m10 (NHR@KIT question) | **Resolved** | Draft §4.2 (c). |
| m11 (schedule gates) | **Resolved** (one residual, n5) | Draft §7 has a gates column: the author's HoreKa row, PORTING-CONFIRM, M10, X.7, G.3, the K row, the G.5 authorization note and R1-BX-D8-CONFIRM. Code in §5 is gated on the author's row. |

### New findings (round 2)

All are MINOR.

**n1 — The RUNBOOK risk row states as settled what PLAN marks open.**
*Location:* RUNBOOK risk table, new row "No MLAgentBench task qualifies for T1"; PLAN line 773, consequences list.
PLAN marks this consequence *(open)*. The RUNBOOK row states it as a settled rule. A STOP for the author decides nothing, so the risk is small, but the two documents should use the same marking.
*Fix:* Append "*(proposed; PLAN R1-1GC-FALLBACK consequences)*" to the RUNBOOK row.

**n2 — `--deadline` set to the downtime start leaves no time to copy results out.**
*Location:* draft §5.1, second and third layers.
`--deadline` and the in-job check both stop at the downtime start. There is no data access during the downtime, and §7 says "Copy everything out before the downtime". A job ending at 23 Nov 00:00 therefore leaves its results unreachable until about 5 Dec.
*Fix:* Use a copy-out cutoff (for example the downtime start minus 12–24 h, set in the manifest) for all three layers.

**n3 — The draft does not say what happens to Ada census work done before adoption.**
*Location:* draft §0.
O8 starts G.0/G.1b on Ada after STOP 0, independently of this draft.
*Fix:* Add one line: Ada census results kept before adoption remain valid for raw cost and for any Ada table, but set no σ̂ for an H100 table (R1-BX-REVISIONS (f)).

**n4 — "Rules for every job" contradicts several job rows.**
*Location:* draft §3 "Rules for every job", third bullet.
The bullet says every template sets `--gres=gpu:4` and `--exclusive`. That contradicts J0 (`dev-cpu`), J0b and J5 (`cpu`, no GPU), and J1 and J1b (1 GPU). `--exclusive` on a dev partition is also questionable.
*Fix:* Make GPU count and `--exclusive` per job type: `--gres=gpu:4 --exclusive` for J2–J4 only. Keep account, partition, time, ntasks, cpus-per-task, mem and `--deadline` for every job.

**n5 — Proposer timing and the J1b pass criterion.**
*Location:* draft J1, J1b and §7.
J1 (first window, before X.7) runs a "load probe of the main proposer", but the pick is gated on X.7 in the second window. J1b copies O5's measurements, but O5's pass criterion (a sweep-2 T0 projection ≤ 4 days) does not carry over to H100 T1 serving. No criterion is named.
*Fix:* J1 probes a Stage A candidate named by the author, as O5 does before X.7. Add: "the author commits J1b's pass criterion before J1b runs".

### Governance re-check

- **No run authorized.** The draft's status is unchanged, and §0 requires an author row.
- **The draft decides nothing.** §9 lists only questions, and §5 code is gated in §7.
- **Seeds 7006–7010 are evaluation-only.** This is now explicit in J5.
- **The 1GC row records only the author's decision.** The agent's consequences are labelled as not part of it.

Verdict: accepted

## Post-round-2 fixes (executing agent, 4 Nov)

- n1: the RUNBOOK MLAgentBench STOP row is tagged *(proposed)*.
- n2: the three downtime layers use a copy-out cutoff 24 h before the downtime (proposed).
- n3: §0 says Ada census results stay valid for raw cost and Ada tables, but set no H100 noise width.
- n4: `--gres=gpu:4` and `--exclusive` apply to J2–J4 only.
- n5: J1 probes an author-named Stage A candidate before X.7; J1b needs an author-committed pass criterion.
