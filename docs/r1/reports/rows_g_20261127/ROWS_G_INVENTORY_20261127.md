# Rows of 26 Nov (g) in work not yet launched: inventory, and G.5 under R1-NO-TIMEOUT (2) (local/20261126-07)

AI-assisted (Claude, Mac-desk worker), 27 Nov 2026, over published `main` `47df6f55`.

- **Item 1** is a tier-D inventory: one entry per bound, with a classification.
- **Item 2** is a proposal for the coordinator and the author.

**Rows:** R1-NO-TIMEOUT, R1-STEP-ORDER and R1-CARD-SHARE.

**Classes:**
- **W**: withdrawn (R1-NO-TIMEOUT (1) or R1-STEP-ORDER (1)).
- **H**: kept as a helper guard (R1-NO-TIMEOUT (4)). It only turns a hang into an infrastructure failure and decides no outcome.
- **B**: kept as the proposal's run budget (R1-NO-TIMEOUT (2)).
- **S**: the work is under a signed note that fixes the bound. It follows that note (R1-NO-TIMEOUT preamble; R1-HOST-FREE (3)), and a change needs an addendum.

**Sources:** a read-only sweep of code and drafts on `main` and on the branches named. File:line references are on `main` unless a branch is named.

## 1. Inventory

| # | Work | Bound (where) | What it decides | Class | Action |
|---|---|---|---|---|---|
| 1 | Houseprice CPU-set check | 9.486 s per run, the `too_slow` pass criterion (`g5_tasl.py:910-914, 2094-2113, 2171-2194`; note line `tasl2_cpuset_check`) | pass criterion of a check | **S** | Signed as S14 A in R1-G5-SIGNATURE ("criterion kept", task -01). Under (1) it would be withdrawn. It stays unless an author row or an addendum removes it. Flagged for the author. |
| 2 | CPU-set check (inherited) | node wall limit, about 10,582 s, from `run_node_job` (`g1b_tasl.py:258-262, 1225, 1276-1290`) | job deadline ("node deadline reached") | **W** in principle; **S** in practice | The G.1b runner is reviewed launch code. It changes only through a reviewed unit; the check takes about 30 s, so the limit cannot bind in practice. |
| 3 | CPU-set check (inherited) | per-run engine timeout 3 × slowest census = 20.382 s, a `TimingStop` (`g1b_tasl.py:249, 806-808, 1113-1118`) | run budget | **B** | R1-G1B-TIMEOUT's budget. Under R1-CARD-SHARE (3) a timeout beside another process is an infrastructure failure. The check holds the TASL-2 lease, and its driver retries only infrastructure. |
| 4 | CPU-set driver (branch `mac-cpuset-repeats-20261126`, on `main` since `47df6f55`) | lease wait of 720 × 5 s = 1 h, then "STOP: … nothing ran" (`run_cpuset_check.sh:56-68`) | ends the driver before any run; decides no outcome | **H** | Keep. Nothing is recorded as a result, and the operator runs the driver again. A later revision could word it as "nothing ran; run again" rather than STOP. |
| 5 | CPU-set driver | one check run per UTC day (`run_cpuset_check.sh:34-38`) | run-id namespace | **H** (not a date rule) | Keep. The date only names the run; no step waits for a date. |
| 6 | G.5 revision 13 | per-run budget 3 × slowest census; baseline timeout = STOP 8 (`g5_job.py:97, 171-178, 405-453`) | proposal failure, baseline STOP | **B** | Keep (R1-NO-TIMEOUT (2) names it). The shared-card case is item 2 below. |
| 7 | G.5 revision 13 | "median run time > timeout basis" → timing STOP of a wave (`g5_job.py:435-500, 594, 1764`) | wall-time criterion that STOPs a wave | **S** (would be **W**) | Signed as drafted. Item 2 proposes the addendum reading. |
| 8 | G.5 revision 13 | campaign and audit-chunk deadlines → STOP 9, node class (`g5_job.py:175-178, 1426-1463, 1759, 1883, 1935-1940`); chunk sizing to 82,800 s (`g5_job.py:96, 300-304`) | job deadline as a node STOP | **S** (would be **W**) | Signed as drafted. Item 2 proposes that a deadline STOP be read as an infrastructure failure and repeated. The chunk sizing only shapes jobs (**H**). |
| 9 | G.5 revision 13 | GPU-hour cap 425 → STOP 9 (`g5_job.py:644-646, 756-758, 983-985, 1053`) | cap that stops jobs | **S**, read under R1-NO-TIMEOUT (3) | The row pre-authorises the coordinator's addendum that raises the figure if reviewed code stops at it. Projection 216.9. |
| 10 | G.5 revision 13 | freeze-wait release date 2027-12-31 (S6 (c)) → STOP 14 (`g5_tasl.py:2366-2391`) | date condition | **S** | Signed as "a technical bound and not a rule" (R1-G5-SIGNATURE S6). Harmless at that date. |
| 11 | G.5 revision 13 | `pilot_basis` dates recomputed on the declared day 2026-11-25 (`g5_tasl.py:2563-2600`) | reproducibility check; decides nothing by the calendar | **H** | Keep. The dates are targets (R1-BX-D14-G4B as amended by R1-STEP-ORDER). |
| 12 | G.5 revision 13 | `/health` HTTP 10 s, 20 latency probes (`g4_tasl.py:552-603`); server-down probe | health guard; a failure is a STOP 12 re-run as a new attempt | **H** | Keep. |
| 13 | G.5 revision 13 | LLM call: no time limit in this repository. The engine's limit is in the harness (`trackg/audit_g5`); the 60 s fallback only sizes the deadline | — | to check | The harness engine's call timeout should be read by whoever reviews item 2. Under (1) a call that times out is re-issued and does not count against the cap. |
| 14 | G.5 / G.1b / P.4 helpers | subprocess timeouts: 600 s, 60 s, 3600 s, clone 1800 s, uv 900/3600 s, setup 7200 s (`g1b_lib.py`, `g1b_tasl.py:814`, `p4_lib.py:358-577`) | helper guards (setup 7200 s raises a STOP) | **H** | Keep. `run_setup`'s STOP should be read as infrastructure in new launchers. |
| 15 | P.4 phase 1 (unsigned) | probe walltime 7200 s (`p4_lib.py:172`, `p4_probe_spec.json:119`, JDL `+RequestWalltime`) | probe time limit | **W** | Fold into the P.4 unit (`local/20261126-06` unit 1, in progress): no time limit on a probe attempt. HTCondor still needs a requested walltime, so treat it as a request (**H**), with a walltime kill recorded as infrastructure, as `seal` already does. |
| 16 | P.4 phase 1 | arm walltime 1.5 × estimate + 1800 s; 86,400 s per job; 64 slot-hours (`p4_lib.py:139-141, 215-353`; `p4_switch.py:318-342`) | scheduler requests and caps that refuse submission | **H** (requests); cap **R** | Fold into P.4: walltime is a scheduler request only (an overrun is infrastructure). The 40 GPU-h and 64 slot-hours become reporting thresholds (R1-NO-TIMEOUT (3)), not refusals. |
| 17 | P.4 phase 1 | `trackp(…, timeout=86400)` and the test path's 7200 s (`p4_lib.py:664-670, 876`) | subprocess guards (infrastructure) | **H** | Keep. |
| 18 | Screening (branch `mac-screen-measure-fix-20261126`) | deadline option | job deadline | **W, done** | Withdrawn in `611b34c0` (reviewed, accepted). |
| 19 | Screening | worker 600 s per run (`screen_measure.py:291, 343`) | T0 run budget | **B** | Keep (R1-NO-TIMEOUT (2) names T0's 600 s). |
| 20 | Screening | co-tenancy sampled every 60 s (`screen_measure.py:90, 569-577`) | sampling interval; the threshold is cores | **H** | Keep. |
| 21 | Screening | worker-runtime probe `timeout=30` → `worker_runtime` STOP (`r1/c3/audit.py:206`) | a time limit on a probe whose failure is a STOP | **W** in principle | Fold into the screening unit's next revision: a probe timeout becomes an infrastructure failure, repeated. Proposed, not changed in this unit (`audit.py` is shared code). |
| 22 | D.3 pre-declaration revision 3 (branch `mac-d3-predecl-20261122`) and design | chunk walltime 1.5 × smoke and "a chunk over its walltime" STOP; P7 140 GPU-h projection STOP (`D3_PREDECLARATION_DRAFT_20261122.md:451-487, 547`; `D3A_AUTHORIZATION_DRAFT…:50-62`; design `:39, 79, 85, 160`) | job deadline as STOP; cap as STOP | **W** / threshold | Fold into revision 4 (`local/20261126-03`, in progress): the walltime is a request, an overrun is infrastructure, and 140 GPU-h is a reporting threshold. No LLM-call time limit as an outcome; a re-issued call does not count against 80. |
| 23 | D.3 revision 3 | "R1-SUBMISSION-MIN's 3 Jan rule" for A6 (`:315`) | date rule | **W** | Fold into revision 4 (R1-STEP-ORDER (1)). |
| 24 | G.5 addendum (not built) | "by 2 Dec 2026" joining cutoff, latest starts, "until 2 Dec" precedence (G.5 draft :241, 700-707, 813-845, 1885, 1950) | date conditions | **W** for the addendum | R1-STEP-ORDER (2)(a): a candidate joins whenever its G.1b completes with determinism PASS. The addendum code (`local/20261126-12`) takes this. |
| 25 | Expansion G.1b (signed note `g1b_x_t1_tasl_20261126.md`) | cutoff 2026-12-01T23:00Z for join versus T2; latest starts; `check_x_note` requires the wording (`g1b_tasl.py:1630, 1702-1705`) | date condition (stated in note text; no code compares it) | **S**, superseded in effect | R1-STEP-ORDER (1) withdraws the 2 Dec cutoff as a rule. The signed note's text remains; the join is decided by (2)(a). The coordinator may record this against the note. No code enforces the comparison. |

**Items 3 and 4 of the task, folded into their own units:**
- P.4 (`local/20261126-06` unit 1): no probe time limit; GPU-hours as a threshold; new launchers check free memory, not an empty card; job records list the card's other compute processes.
- D.3 revision 4 (`local/20261126-03`): no LLM-call time limit as an outcome; re-issued calls are free against the cap; GPU-hours as a threshold.
- Screening (`local/20261126-02`): no deadline (done). Item 21 is proposed.

Each unit's report names them.

## 2. G.5 without a new revision of its launch code

**The question:** under R1-NO-TIMEOUT (2) a run that reaches its budget, or runs out of memory, while another compute process was on its card is an infrastructure failure and is repeated. How can revision 13 meet that without changing reviewed launch code?

**What revision 13 already does:**
- Every G.5 job holds the TASL-2 lease.
- It refuses to start beside a foreign compute process (`check_no_foreign`; kept by R1-CARD-SHARE (5)).
- It records foreign-process checks before and after each part.
- So a foreign process can only appear **during** a job, between two checks.

**Proposal:**
1. **A monitor beside each G.5 job** (a new script outside the launch code, run by the operator in the same scope). Every 10 s it writes one JSONL line per sample into the job's log directory, sealed with the attempt as a member the code does not read: UTC time, `nvidia-smi --query-compute-apps=pid,process_name,used_memory --id=<worker UUID>`, and our job's PIDs. Count and memory only, as R1-CARD-SHARE (4) asks.
2. **A repeat step by addendum** after each wave. A reviewed script reads the sealed monitor logs and the sealed run rows and lists every run that reached its budget (`divergent:timeout`), or failed with an out-of-memory signature, while a foreign PID was on the card within its run window. The coordinator publishes an addendum note listing those runs. Each is run again in a new attempt (an audit run at its seed, or a campaign step as the addendum fixes), and the repeat's row replaces the shared-card row in the assembly. The original rows stay sealed and are disclosed. Only rows of attempts that had the card to themselves count as a proposal's failure.

**Does revision 13 launch as it stands?** Yes for the run budget: rows #6 and #8 need nothing in the launch code. Two lines need the author or the coordinator:
- **(a)** STOP 9 on a missed job deadline (#8) and the wave timing STOP (#7) are, under R1-NO-TIMEOUT (1), withdrawn for unsigned work. G.5 is signed as drafted. A missed deadline beside a foreign process would be a node STOP that R1-CARD-SHARE (3) calls an infrastructure failure. **Recommendation:** an addendum reading in which such a STOP, when the monitor shows a foreign process in the window, is an infrastructure failure: the attempt is closed, sealed and repeated, and the node continues. The code stays the same, but the operator's response to the STOP changes. The author confirms, since it changes how a STOP is read.
- **(b)** The replacement of rows in the assembly needs `g5_assemble` to accept a repeat list. That is a code unit, and it touches how a label is recorded, so it is tier E. It is needed only if a shared-card failure occurs; the monitor makes that detectable.

**What the author decides:** (a) as recommended, and whether (b) is built now or only when the monitor first shows a shared-card failure. I recommend now, before the first wave's audits. The monitor script and the repeat-list reader are mine to build after the decision.

**Draft row:** `| R1-G5-SHARED-REPEAT (date) | G.5 (revision 13, signed) under R1-NO-TIMEOUT (2) and R1-CARD-SHARE (3): a card monitor beside each G.5 job records the card's compute processes every 10 s into the sealed attempt; a run that reached its budget or ran out of memory while a foreign process was on its card, and a STOP 8/9 or wave timing STOP whose window shows one, is an infrastructure failure, repeated in a new attempt by an addendum the coordinator publishes after each wave; the repeat's row replaces it in the assembly, and the original stays sealed and disclosed. |`
