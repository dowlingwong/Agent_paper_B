# Rows of 26 Nov (g) in work not yet launched: inventory, and G.5 under R1-NO-TIMEOUT (2) (local/20261126-07)

AI-assisted (Claude, Mac-desk worker), 27 Nov 2026, over published `main` `47df6f55`. Revision 2 after the tier-E review (`docs/r1/reviews/ROWS_G_INVENTORY_REVIEW_20261127.md`: NOT ACCEPTED on B1 and B2; this revision answers B1, B2 and M1–M9).

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
| 2 | CPU-set check (inherited) | node wall limit, about 10,582 s, from `run_node_job` (`g1b_tasl.py:258-262, 1225, 1276-1290`) | job deadline ("node deadline reached") | **S** | The G.1b runner is reviewed launch code, so it follows its note; it changes only through a reviewed unit. In principle R1-NO-TIMEOUT (1) withdraws the limit, but the check takes about 30 s, so it cannot bind in practice. |
| 3 | CPU-set check (inherited) | per-run engine timeout 3 × slowest census = 20.382 s, a `TimingStop` (`g1b_tasl.py:249, 806-808, 1113-1118`) | run budget | **B** | R1-G1B-TIMEOUT's budget. Under R1-CARD-SHARE (3) a timeout beside another process is an infrastructure failure. The check holds the TASL-2 lease, and its driver retries only infrastructure. |
| 4 | CPU-set driver (branch `mac-cpuset-repeats-20261126`, on `main` since `47df6f55`) | lease wait of 720 × 5 s = 1 h, then "STOP: … nothing ran" (`run_cpuset_check.sh:56-68`) | ends the driver before any run; decides no outcome | **H** | Keep. Nothing is recorded as a result, and the operator runs the driver again. A later revision could word it as "nothing ran; run again" rather than STOP. |
| 5 | CPU-set driver | one check run per UTC day (`run_cpuset_check.sh:34-38`) | run-id namespace | **H**, with a defect | The date names the run. But a check run that fails after its root is created can only run again on the next UTC day, which is a date gating a step (R1-STEP-ORDER (1); review M6). A later revision should use a sequence-numbered run id (`…-<YYYYMMDD>-<n>`), which needs `CPUSET_RUN` in `g5_tasl.py` to accept it (signed code). Until then, one run per day stands, and an infrastructure failure costs a day. |
| 6 | G.5 revision 13 | per-run budget 3 × slowest census; baseline timeout = STOP 8 (`g5_job.py:97, 171-178, 405-453`) | proposal failure, baseline STOP | **B** | Keep (R1-NO-TIMEOUT (2) names it). The shared-card case is item 2 below. |
| 7 | G.5 revision 13 | "median run time > timeout basis" → timing STOP of a wave (`g5_job.py:435-500, 594, 1764`) | wall-time criterion that STOPs a wave | **S** (would be **W**) | Signed as drafted. Item 2 proposes the addendum reading. |
| 8 | G.5 revision 13 | campaign and audit-chunk deadlines → STOP 9, node class (`g5_job.py:175-178, 1426-1463, 1759, 1883, 1935-1940`); chunk sizing to 82,800 s (`g5_job.py:96, 300-304`) | job deadline as a node STOP | **S** (would be **W**) | Signed as drafted. Item 2 proposes that a deadline STOP be read as an infrastructure failure and repeated. The chunk sizing only shapes jobs (**H**). |
| 9 | G.5 revision 13 | GPU-hour cap 425 → STOP 9 (`g5_job.py:644-646, 756-758, 983-985, 1053`) | cap that stops jobs | **S**, read under R1-NO-TIMEOUT (3) | The row pre-authorises the coordinator's addendum that raises the figure if reviewed code stops at it. Projection 216.9. |
| 10 | G.5 revision 13 | freeze-wait release date 2027-12-31 (S6 (c)) → STOP 14 (`g5_tasl.py:2366-2391`) | date condition | **S** | Signed as "a technical bound and not a rule" (R1-G5-SIGNATURE S6). Harmless at that date. |
| 11 | G.5 revision 13 | `pilot_basis` dates recomputed on the declared day 2026-11-25 (`g5_tasl.py:2563-2600`) | reproducibility check; decides nothing by the calendar | **H** | Keep. The dates are targets (R1-BX-D14-G4B as amended by R1-STEP-ORDER). |
| 12 | G.5 revision 13 | `/health` HTTP 10 s, 20 latency probes (`g4_tasl.py:552-603`); server-down probe | health guard; a failure is a STOP 12 re-run as a new attempt | **H** | Keep. |
| 13 | G.5 revision 13 | LLM call: no time limit in this repository. The engine's limit is in the harness (`trackg/audit_g5`); the 60 s fallback only sizes the deadline | — | to check | Owner: the G.5 repeat-list code unit (§2) reads the harness engine's call timeout at G5-7 `cbf7a003` and G5-AR `ccdb3774` and records it in its report (review M8). Under (1) a call that times out is re-issued and does not count against the cap. |
| 14 | G.5 / G.1b / P.4 helpers | subprocess timeouts: 600 s, 60 s, 3600 s, clone 1800 s, uv 900/3600 s, setup 7200 s (`g1b_lib.py`, `g1b_tasl.py:814`, `p4_lib.py:358-577`) | helper guards (setup 7200 s raises a STOP) | **H** | Keep. `run_setup`'s STOP should be read as infrastructure in new launchers. |
| 15 | P.4 phase 1 (unsigned) | probe walltime 7200 s (`p4_lib.py:172`, `p4_probe_spec.json:119`, JDL `+RequestWalltime`) | probe time limit | **W** | Fold into the P.4 unit (`local/20261126-06` unit 1, in progress): no time limit on a probe attempt. HTCondor still needs a requested walltime, so treat it as a request (**H**), with a walltime kill recorded as infrastructure, as `seal` already does. |
| 16 | P.4 phase 1 | arm walltime 1.5 × estimate + 1800 s; 86,400 s per job; 64 slot-hours (`p4_lib.py:139-141, 215-353`; `p4_switch.py:318-342`) | scheduler requests and caps that refuse submission | **H** (requests); caps as a threshold (R1-NO-TIMEOUT (3)) | Fold into P.4: walltime is a scheduler request only (an overrun is infrastructure). The 40 GPU-h and 64 slot-hours become reporting thresholds (R1-NO-TIMEOUT (3)), not refusals. |
| 17 | P.4 phase 1 | `trackp(…, timeout=86400)` (`p4_lib.py:664-670`); the test path's 7200 s (`:876`) | a wall limit on the arm's training call; a guard on the synthetic test path | **W** / **H** | The 86,400 s bounds the training call itself (review M7). Fold it into the P.4 unit with row 16: an overrun is infrastructure, not an outcome. The test path's 7200 s stays **H**. |
| 18 | Screening (branch `mac-screen-measure-fix-20261126`) | deadline option | job deadline | **W, done** | Withdrawn in `611b34c0` (reviewed, accepted). |
| 19 | Screening | worker 600 s per run (`screen_measure.py:291, 343`) | T0 run budget | **B** | Keep (R1-NO-TIMEOUT (2) names T0's 600 s). |
| 20 | Screening | co-tenancy sampled every 60 s (`screen_measure.py:90, 569-577`) | sampling interval; the threshold is cores | **H** | Keep. |
| 21 | Screening | worker-runtime probe `timeout=30` → `worker_runtime` STOP (`r1/c3/audit.py:206`) | a time limit on a probe whose failure is a STOP | **H** if read as infrastructure (review N4) | Fold into the screening unit's next revision: a probe timeout becomes an infrastructure failure, repeated. Proposed, not changed in this unit (`audit.py` is shared code). |
| 22 | D.3 pre-declaration revision 3 (branch `mac-d3-predecl-20261122`) and design | chunk walltime 1.5 × smoke and "a chunk over its walltime" STOP; P7 140 GPU-h projection STOP (`D3_PREDECLARATION_DRAFT_20261122.md:451-487, 547`; `D3A_AUTHORIZATION_DRAFT…:50-62`; design `:39, 79, 85, 160`) | job deadline as STOP; cap as STOP | **W** / threshold | Fold into revision 4 (`local/20261126-03`, in progress): the walltime is a request, an overrun is infrastructure, and 140 GPU-h is a reporting threshold. No LLM-call time limit as an outcome; a re-issued call does not count against 80. |
| 23 | D.3 revision 3 | "R1-SUBMISSION-MIN's 3 Jan rule" for A6 (`:315`) | date rule | **W** | Fold into revision 4 (R1-STEP-ORDER (1)). |
| 24 | G.5 addendum (not built) | "by 2 Dec 2026" joining cutoff, latest starts, "until 2 Dec" precedence (G.5 draft :241, 700-707, 813-845, 1885, 1950) | date conditions | **W** for the addendum | R1-STEP-ORDER (2)(a): a candidate joins whenever its G.1b completes with determinism PASS. The addendum code (`local/20261126-12`) takes this. |
| 25 | Expansion G.1b (signed note `g1b_x_t1_tasl_20261126.md`) | cutoff 2026-12-01T23:00Z for join versus T2; latest starts; `check_x_note` requires the wording (`g1b_tasl.py:1630, 1702-1705`) | date condition (stated in note text; no code compares it) | **S**, superseded in effect | R1-STEP-ORDER (1) withdraws the 2 Dec cutoff as a rule. The signed note's text remains; the join is decided by (2)(a). The coordinator may record this against the note. No code enforces the comparison. |

**Items 3 and 4 of the task, folded into their own units:**
- P.4 (`local/20261126-06` unit 1): no probe time limit; GPU-hours as a threshold; new launchers check free memory, not an empty card; job records list the card's other compute processes.
- D.3 revision 4 (`local/20261126-03`): no LLM-call time limit as an outcome; re-issued calls are free against the cap; GPU-hours as a threshold.
- Screening (`local/20261126-02`): no deadline (done). Item 21 is proposed.

Each unit's report names them.

## 2. G.5 under R1-NO-TIMEOUT (2): what launches now, and the repeat-list unit

**The question:** under R1-NO-TIMEOUT (2) a run that reaches its budget, or runs out of memory, while another compute process was on its card is an infrastructure failure and is repeated. Can revision 13 meet that without a new revision of its launch code?

### What revision 13 already does (checked against the code)

- At every job start, `check_no_foreign` refuses beside a foreign compute process on the worker card (`g1b_tasl.py:841-860`; called at `g5_job.py:1365, 1444`). The lease (`gpu_lease`) is our own flock and does not exclude other users; the refusal comes from `check_no_foreign`.
- After the engine (`g5_job.py:1475, 1488-1496`), a foreign process still on the card makes the attempt an **infrastructure** STOP, which is already repeated in a new attempt (review M1).
- **Two cases are left uncovered:**
  - (i) a foreign process that came and went during the engine;
  - (ii) the deadline and orphan paths, which raise STOP 9 (class `node`, `g5_job.py:1446-1463, 1757`) before the after-check runs. The same goes for STOP 8 and the wave timing STOP (class `timing`, `:588, 594-595, 1752, 1764-1766`).
- **A recorded `node` or `timing` STOP halts the node:**
  - `node_stopped` (`g5_job.py:671-685`) and `check_order` (`:753-755`) refuse anything further;
  - the TASL-7 claim paths refuse it too (`:980-982, 1024-1026`);
  - `g5_assemble._one_attempt` (`:283-285`) refuses a directory that holds a sealed attempt whose class is not `infrastructure`.

  So an addendum alone cannot turn such a STOP into a repeat: **reading it as infrastructure needs code** (review B1).
- **Where a monitor file can go:**
  - The seal copies only `ATTEMPT_FILES` and `node.log` (`g5_seal.py:88, 333-342`).
  - TASL-7 registration refuses foreign files in an attempt directory (`g5_job.py:881, 1098-1101`).
  - The attempt number is assigned at start.

  So **a monitor cannot write into the attempt** (review B2).

### What launches now

Revision 13 can **start and run** as it stands:
- The run budget (#6) needs nothing.
- A foreign process still present at the end is already infrastructure.

What it cannot do without code is repeat cases (i) and (ii).

### Proposal

**1. A card monitor (tier D: it records card facts only and touches no label).** A new script, run by the operator for the whole campaign, one process per worker card (TASL-2's 4090; TASL-7's 4090 while it runs audit chunks).
- **Where it runs:** in its own user scope, outside the job scopes and the attempt trees.
- **Where it writes:** its own directory, `runs/<run_id>/_card_monitor/<host>/<gpu_uuid>/segment-<k>.jsonl`.
- **What it samples:** every 10 s, one line even when the card is idle (a heartbeat). Each line holds:
  - the UTC time;
  - for each compute process on the card (`nvidia-smi --query-compute-apps=pid,used_memory --id=<uuid>`), its memory and its classification.
- **How it classifies a process** (review M4): **ours** if `/proc/<pid>/cgroup` lies under a G.5 job scope's `cgroup_parent`, or under the proposer server's unit on TASL-7; **foreign** otherwise. It records counts, memory and the classification only (R1-CARD-SHARE (4)).
- **How a segment is closed:** before a wave's repeat list is built, the segment is ended and closed by a receipt with its sha256, committed beside the wave's diagnostics.

**2. A G.5 repeat-list code unit (tier E: it decides which attempts' rows become labels).** One reviewed unit for both parts of the earlier (a) and (b) (review B1, M9):
- **(a) Reclassification list:** `node_stopped`, `check_order`, the TASL-7 claim checks and `g5_assemble._one_attempt` honour a published, reviewed reclassification list. The list names attempt ids whose `node` or `timing` STOP (STOP 8, STOP 9, the wave timing STOP) had a foreign sample in its window. Each listed attempt counts as `infrastructure`. The original record is untouched.
- **(b) Assembly of repeats:** the assembly takes a repeat's rows in place of the listed attempt's.
- **The repeat-list reader** (part of the same unit) builds the list from the sealed monitor segments and the sealed job records.

**3. Safeguards, fixed now, not per addendum** (review M2):
- **(i) What may be read.** The list is decided only from the monitor samples, the job records' `stop`, `stop_class` and times, and each run's failure class and window. No metric, score, label or ledger decision value is read before the list is published.
- **(ii) How it is read.** The reader is reviewed and reads only those fields through the logged member reader (`tar_members`, with an access-log entry). It writes the list and its inputs' sha256 before anything else happens to that wave.
- **(iii) Order.** The list is published, as the coordinator's addendum, before any repeat runs and before the wave's E5 or assembly reads.
- **(iv) Every item is repeated.** Every listed item is repeated, with no option to skip. The repeat replaces the original whatever its result, and "keep the better" is never allowed. A repeat that is itself shared is repeated again under the same rule.
- **(v) What a repeat is.** A campaign item is repeated as the whole campaign job of that wave, as a new attempt; splicing in a step is never allowed. An audit run is repeated at the same seed, on the same hardware class (R1-HOST-FREE (2)(a)), or on TASL-7 only where its cross-host PASS allows.
- **(vi) Monitor gaps.** A heartbeat gap of more than two intervals inside a window counts as shared.
- **(vii) Missing run times.** Where rows carry no run times, the attempt window is used, and every budget, OOM, STOP 8 or STOP 9 failure in an attempt with a foreign sample is listed.
- **(viii) Disclosure.** The number of repeats and the original rows are disclosed per node.

**4. CPU nodes (review M5).** `mlgym_houseprice` runs on TASL-2 CPUs 0-7 with no card (`gpu` None, so `check_no_foreign` checks nothing). R1-NO-TIMEOUT (2) speaks of "another compute process on its card", so CPU nodes are outside this proposal: a budget timeout there counts under the signed note. Whether CPU load from other users on the leased set should be treated alike is a question for the author. It is listed below; I do not recommend it now, since S13's leases already serialise our own jobs on 0-7.

### What the author decides

- **(1)** The safeguards and the repeat-list unit as above. Recommended: build the unit now, before the first wave's audits; it is mine.
- **(2)** CPU nodes outside the rule. Recommended: yes.

The monitor script (tier D) and the repeat-list unit (tier E) are mine to build after the decision. Until the unit is on `main`, a case (i) or (ii) failure stays a STOP for the author, exactly as revision 13 says.

**Draft row:**

`| R1-G5-SHARED-REPEAT (date) | G.5 (revision 13, signed) under R1-NO-TIMEOUT (2) and R1-CARD-SHARE (3): a card monitor per worker card, outside the job scopes and attempt trees, records the card's compute processes every 10 s (heartbeat lines; ours by cgroup, else foreign) into receipted segments; a reviewed repeat-list unit (tier E) makes node_stopped, check_order, the TASL-7 claim checks and the assembly honour a published reclassification list: a run that reached its budget or ran out of memory, and a STOP 8, STOP 9 or wave timing STOP, with a foreign sample (or a heartbeat gap over two intervals) in its window, is an infrastructure failure; the list is built metric-blind from the monitor and job records only, published before any repeat or E5/assembly read, every listed item is repeated (a campaign as its whole wave job, an audit run at its seed on the same hardware class), the repeat replaces the original unconditionally, originals stay sealed and are disclosed; CPU-only nodes are outside this row. |`
