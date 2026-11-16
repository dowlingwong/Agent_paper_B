# Independent review — ETP HTCondor preparation phase report (night of 13/14 Nov 2026)

**Reviewer role:** fresh, independent, read-only reviewer for the runbook's §6 review loop. Not the
author of the report or of any reviewed file; I did not run the night, submit a job, move a file or
write anything on the cluster.

**Date/time of review:** 14 November 2026, 03:20–03:45 CET (Europe/Berlin).

**Worktree:** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-prep-20261114`,
branch `htcondor-prep-20261114`.

**Commit reviewed:** `067770a53cea23f3e01430d84b79738aa148f10d` ("report finalised with handover
summary"). Report file `docs/r1/reports/HTCONDOR_PREP_20261114.md`, SHA-256
`d0e9ed93f4738ceb6f317c3072c0b76adf277bc3715b7f222746968e893d77ad`; question list
`docs/r1/reports/HTCONDOR_QUESTIONS_20261114.md`, SHA-256
`726bb192724738a153b8adb9c33e339b4c40c70f0a17a61d731f71cf4ee82bfc`. The working tree was clean before
this review; only this review file was added (it is untracked — no commit was made).

**Scope.** Whether the phase report can be accepted as a truthful, complete and evidence-backed record
of the night, against runbook §6 (and §0.2, §0.5, §1, §3, §4, §5, §7) and the operative errata A1–A7.
I re-derived every headline number from the committed/mirrored evidence rather than from the prose:
`raw/host_facts_A.txt`, `raw/host_facts_B.txt`, `raw/pool_facts_raw.txt`,
`raw/pool_analyze_p4_20261114.txt`, `POOL_FACTS.md`, `raw/inventory.tsv`, `raw/entry_stats.tsv`,
`MOVE_PLAN.md`, `moves/from_host/MOVE_LOG.tsv` (+ `.v1`), `MOVE_BACKFILL.tsv`, `MOVE_LOG_NOTES.md`,
`moves/move_entry.sh`, `moves/verify_pair.sh`, `probes/P1–P7.jdl`, `probes/probe.sh`, `probes/dryrun/`,
`probes/out/`, `raw/queue_times_current.tsv`, `w2/w2_check.json`, `w2/ledgers.txt`, and the three review
files named in the task.

**Hard limits of this review (deliberate).** No SSH, no cluster command, no job submission, no file move,
no git commit/push. Every statement below about cluster state comes from the mirrored evidence; where the
evidence is silent I say so rather than filling the gap. I cannot observe the live pool after 03:08 CET
or the actual remote push.

---

## 1. What was checked, and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Runbook §6 contents list, §0.2 standing rules, §0.5 STOPs, §1 moves, §3 image, §4 probes, §5 W2, §7 questions | full read (240 lines) | Requirements extracted; used as the acceptance checklist below. |
| 2 | Errata A1–A7 (operative over the runbook) | full read (106 lines) | Applied: A1 W2, A3 image, A4 timetable, A5 move safety, A6 GPU/10-job accounting, A7 details. |
| 3 | Inventory completeness | `raw/inventory.tsv` rows vs `/ceph/dwong` top-level list | **70 entries** (+ header + `DONE`); 9 move + 61 skip = 70 in `MOVE_PLAN.md`. Complete. |
| 4 | Inventory totals | arithmetic over the 70 rows | **634,100,228,441 B = 634.10 GB / 385,937 files**, not the report's 560.3 GB / 385,744 (B2). The independent move-plan review also computed 634.10 GB. |
| 5 | Move plan counts and arithmetic | parsed the 9 move rows + 61 skip rows | 9 entries = 19,682,786,459 B = 19.68 GB; 8 moved = 12,298,122,900 B = 12.30 GB (report says 12.2, m2). |
| 6 | Move log: 8 moved / 1 failed (`work`) | `MOVE_LOG.tsv` rows 2–8, `MOVE_LOG.tsv.v1` | **8 `moved`** (hcp_xopt_20261107/06, arXiv-v1, y19_host, zc_host after a first failure, megz_timing_host, megz_host, megz_r1_host_20261014) + **`work` `failed copy_failed(rc=23)`**. Confirmed. |
| 7 | Backfill | `MOVE_BACKFILL.tsv` | **8 rows, all `verdict=ok`**, count/bytes/dirs/symlink/perm/manifest all `yes`. Confirmed. |
| 8 | No deletion | grep of `move_entry.sh`, `verify_pair.sh`, logs/notes/report for `rm` | No `rm` command anywhere; the only matches are prose "never `rm`". `mv` is used for retirement. Confirmed. |
| 9 | Originals retired / symlinks | `MOVE_LOG.tsv` `moved_to`, `symlink_ok`, `old_path_ok` columns | All 8 moved rows carry `/ceph/dwong/_to_delete/<X>.moved_20261114`, `symlink_ok=yes`, `old_path_ok=yes`. Confirmed. |
| 10 | Failed copies retired | `work` row, `MOVE_LOG_NOTES.md`, Q12 | The `work` partial copy is said to be at `/work/dwong/_to_delete/work.failed_20261113T235407Z`; the `zc_host` first copy at `/work/dwong/_to_delete/zc_host.failed_*`. **No committed `ls` transcript**; the paths are prose only (m5). |
| 11 | False negatives disclosed | report §2, `MOVE_LOG.tsv` row 2 vs v1 row, notes | `du -sb` CephFS `st_size` false byte mismatch and `zc_host` `.git/index` false content mismatch are both disclosed. Confirmed (the first backfill attempt is only in the notes, m6). |
| 12 | Pool totals / version | `raw/pool_facts_raw.txt`, `host_facts_A` A3/A6/A7, `host_facts_B` B2/B3 | 1105 / 1051 / 22 / 31 at 23:44 matches; `host_facts_A` at 23:38 has 1107/1055/20 (earlier snapshot — the report uses the later one). `condor_version` 25.0.12 confirmed. |
| 13 | Docker gate | `host_facts_A` A9 (`Cannot connect to the Docker daemon`), `docker` group, apptainer/singularity | Gate result confirmed. Only **one** transcript, not the "twice" in the report (m8). |
| 14 | Quotas / disk | `host_facts_A` A1/A2, `pool_facts_raw` | `/work` 1.4 T / 385 G / 1.1 T free (27 %); `/ceph` 1.4 P / 346 T free (75 %); `quota -s/-Q` no output; 15 % floor ≈ 210 G. Confirmed. |
| 15 | Pool counts used by Q10/Q11 | `raw/pool_analyze_p4_20261114.txt` L59–65 | `docker_slots=315`, `etp_slots=323`, `docker_and_etp=315`, `docker_unclaimed=5`, `etp_unclaimed=13`, `singularity_slots=1094`, `nemo2_gpu_slots=5`. The report's 324 in §3 contradicts this (M3); "6 L40S slots" in §5 is not in the evidence (M2). |
| 16 | Probe JDLs vs §4.1 | `P1–P7.jdl` + `dryrun/P*.dry` | Images, requirements, requests, walltime 1800, `+RemoteJob` on P3–P7, GPU type strings, output/log/error names all present. P4/P5/P6/P7 request 2 CPUs / 4000 MB / 1 GPU (the runbook table left CPU implicit). |
| 17 | Queue times | `raw/queue_times_current.tsv` rows 2–10 | P1 73/1 s, P3 7/1 s, P5 212/2 s, P1w2 21/2 s (mdm1), P3w2 21/1 s (ms04) **match the report exactly**. P2/P4/P6/P7 `IDLE`. Confirmed. |
| 18 | Probe stdout / environment claims | `probes/out/P1.out`, `P3.out`, `P5.out`, `P1w2.out`, `P3w2.out` | Content matches the report (nproc, Xeon/EPYC, `/work`/`/ceph`/`/ceph/srv` present on ETP, missing on TOpAS, `/cvmfs` zero, `/scratch` missing, V100S UUID/`NVIDIA_VISIBLE_DEVICES=void`). **These five `.out` files are untracked/ignored** (`.gitignore:4:*.out`); only `.err` and `queue_times.tsv` are committed (M8). |
| 19 | P1/P3/P5 outcome | queue_times + stdout | Completed exit 0; matches. Confirmed. |
| 20 | P2/P4/P6/P7 states and reasons | queue_times, `pool_analyze_p4`, `host_facts_A/B` | States `IDLE` confirmed. P2 capacity (no P2 analyze committed); P4 reason contradictory (M4); P6 reason has no committed `HasDocker`/`CloudSite` transcript (M2); P7 Drained confirmed, but the 23:38 Idle→23:40 Drained transition is omitted (m7). |
| 21 | Wave-2 statement | `raw/queue_times_current.tsv` rows 9–10; `P1w2.out`, `P3w2.out` | 21 s on mdm1/ms04, run 2/1 s — confirmed. "faster than wave 1's 73 s / 7 s" is false for P3 (21 > 7; m1). P4/P6 were not resubmitted at all; this is disclosed but not labelled a deviation from A4 (m13). |
| 22 | W2 counts and semantics | `w2/w2_check.json` (288 results), `w2/ledgers.txt` (288 lines) | **288 = 144 + 144**; **14** ledgers with `differences>0`; **53** `rows_not_counting_one` total (all `precheck_rejection`); 274 zero-difference; `worker_runs_total` max 20, `worker_runs_over_cap=false`. Examples s114 20/33 rows, 13 prechecks; s224 17/9; s194 and s264 15 each. Confirmed. `status=STOP_DIFFERENCE`; exit code 3 is not recorded in the W2 artifacts (m16). |
| 23 | W2 read-only / nothing adopted | JSON fields, report/Q1 | Fields are `budget_index`, `trial_indexed_used`, `worker_runs_used`, `rows_not_counting_one`; no labels/metrics. Report states nothing adopted. Consistent. |
| 24 | Image / I1–I4 | docker gate, absence of I*.jdl | No image built; no I1–I4 submitted. The report states this explicitly per A3. Confirmed. |
| 25 | §6 completeness | report §1–§10 vs runbook §6 | Inventory, move log, pool facts, image, probe table, W2, works/doesn't, four workload recommendations present. **Per-class n/median/range missing and the local-CPU median is wrong (M1)**; I2 result is deferred per A3 (acceptable); gpu_register absent (M6). |
| 26 | Question list §7 | Q1–Q12 | All numbered questions present; **Q4/Q5/Q6/Q7/Q9/Q11 lack the required options/recommendation** (M7). |
| 27 | Review trail | runbook review, probe review, move review | Runbook: rejected then accepted after errata. Probe: accepted before submission (review mtime 23:50:36, first submission 23:51:21). Move: rejected then accepted with R1/R2. The report's §1 "move plan is in its second review round" is stale (B1). |
| 28 | Delivery / push | `git branch -r`, report §8, `git status` | No `origin/htcondor-prep-20261114` ref in the worktree; report §8 says both "is pushed" and "the final push is done at the end of the window" (M9). Branch is committed locally and clean. |

**Positive result.** The core of the report is supported: the 8 moved / 1 failed count, the 8/8 green
backfill, the absence of `rm`, the `_to_delete` retirements and symlinks, the two false-negative
disclosures, the 288/14/53 W2 counts, the 274 identical ledgers, the 20-run cap, the docker gate, the
1105-slot pool snapshot, and every P1/P3/P5/P1w2/P3w2 wait/run/site/host number in the queue table. The
report is not a fabrication; the problems below are stale text, unsupported headline numbers, missing
required statistics, and evidence that exists only as prose.

---

## 2. Findings

Severity: **BLOCKING** = the report cannot be accepted as the phase record because a central statement is
false or unsupported, or a required §6/§7 element is absent; **MAJOR** = a required element is missing,
wrong or unsupported and must be fixed before acceptance; **MINOR** = a claim is imprecise, stale or
unverifiable and should be corrected; **NIT** = wording/evidence hygiene.

### BLOCKING

**B1 — §1 says the night's main deliverable was not executed, directly contradicting the report's own
header and §2/§9.**
*Evidence:* `HTCONDOR_PREP_20261114.md` L13 says "**Plan only, not executed at this draft**" and
"Moves start only after the plan is accepted"; L18 says "the move plan is in its second review round".
But L4 says "**8 of 9 moves done and backfilled, `work` skipped (ACL)**"; L26 says 8 of 9 moved, backfill
8/8 `ok`; L114 says the move plan was "NOT ACCEPTED (5 MAJOR) -> revision 2 -> **ACCEPTED**". A reader of
§1 alone would conclude that no move happened and the plan was still under review. This is not a wording
slip: §1 is the report's own goal table.
*Exact fix:* rewrite §1 row 1 to "**8 of 9 moved (12.3 GB); `work` skipped — `/work` has no POSIX ACLs;
plan accepted after revision 2; backfill 8/8 `ok`**"; delete "at this draft" and the "second review
round" sentence; update row 3 to include P1w2/P3w2; change the title from "(report, draft)" to final.

**B2 — The inventory summary's totals are not the totals of `raw/inventory.tsv`.**
*Evidence:* report L22: "70 top-level entries … **560.3 GB, 385,744 files**", citing `raw/inventory.tsv`
and `raw/entry_stats.tsv`. The 70 data rows of `raw/inventory.tsv` sum to
**634,100,228,441 B = 634.10 GB and 385,937 files** (header + 70 entries + `DONE`; `DONE` contributes 0).
The independent move-plan review (`HTCONDOR_MOVE_PLAN_REVIEW_20261114.md` L319/L338) also computed
**634.10 GB** and found 0 mismatches against the plan. The report's 560.3 GB is 73.8 GB low and 193 files
low; no single-entry exclusion from the inventory reproduces either figure (e.g. excluding `hcp_meg`
gives 568.07 GB / 385,747 files, not 560.3 / 385,744).
*Exact fix:* replace with "**634.1 GB, 385,937 files** (sum over the 70 rows of `raw/inventory.tsv`,
excluding the `DONE` sentinel)" or, if a subset/time is intended, name the subset and cite the command
and time. Do not leave a headline number that the cited file contradicts.

### MAJOR

**M1 — §6's per-class median and range are missing, and the one "median" stated is not the class
median.**
*Evidence:* runbook §6 L222 requires "the probe table with queue times: the median and the range per
resource class". The report L68 says "**median** 73 s (P1; P3 7 s …)" and "Single samples only", and
L70–82 is a per-probe table, not a per-class n/median/range. `raw/queue_times_current.tsv` has four
local-CPU 1-core samples: 73, 7, 21, 21 s → **median 21 s, range 7–73 s**. The 73 s is P1 alone. The
8-core (P2), A100 (P4), L40S (P6) and H200 (P7) classes have no executed sample and should be marked
censored, not omitted from the required table.
*Exact fix:* add a per-class table with columns `class, probes, n, wait samples (s), median, range,
outcome`: local CPU 1-core (P1/P3/P1w2/P3w2) n=4, median 21, range 7–73; TOpAS V100S (P5) n=1, 212,
212; 8-core local (P2) n=0, idle 3 h 27 min at 03:19 (censored); A100/L40S/H200 n=0 (censored, give the
reason). Remove "median 73 s" as the class figure.

**M2 — The NEMO2 `HasDocker`/`HasSingularity`/`CloudSite`/"6 L40S slots" conclusion is asserted as
measured, but no committed transcript contains those attributes.**
*Evidence:* report L38 ("HasDocker … **undefined on the NEMO2 GPU slots** (they advertise
`HasSingularity=true`)"), L37 ("CloudSite measured: … NEMO2 = `BwForCluster-Nemo2`"), L61 ("CloudSite+
device matched **6 L40S slots**, but `TARGET.HasDocker` matched **0**"), §7 L97 ("NEMO2 … Singularity
only — measured design blocker"), Q8/Q10. The committed raw files contain no `HasDocker`,
`HasSingularity` or `CloudSite` output: `raw/pool_analyze_p4_20261114.txt` is the **P4** analysis only;
`raw/host_facts_A/B` and `raw/pool_facts_raw.txt` list NEMO2 slots by device/driver/state only. The
probe review's M1 (`HTCONDOR_PROBES_JDL_REVIEW_20261114.md` L180–198) explicitly said `CloudSite` was
**not** confirmed by any measured fact and required a read-only check before P2–P7. The counts also
disagree: `raw/pool_analyze_p4_20261114.txt` L65 says `nemo2_gpu_slots=5`, while `host_facts_A` A6 and
`host_facts_B` B3 show **3** NEMO2 L40S slots, not 6.
*Exact fix:* commit the P6 `condor_q -better-analyze`/`condor_status` output (at minimum
`-af Name CloudSite HasDocker HasSingularity GPUs_DeviceName` for the NEMO2 view) and the exact
`condor_q -better-analyze 759624 -pool …`; correct "6 L40S" to the measured count (3 visible in both
snapshots, 5 NEMO2 GPU slots in the 00:34 count). If no transcript exists, downgrade the sentence to
"author-reported / inferred from P6's no-match" and put the open check into Q8/Q10; do not call it
"measured".

**M3 — `HasDocker=true` on 324 slots contradicts the committed count (315) and the report's own later
sections.**
*Evidence:* report L38 says **324**; `raw/pool_analyze_p4_20261114.txt` L59–61 says
`docker_slots=315`, `docker_and_etp=315`, `etp_slots=323`; report L66, Q10, Q11 and §7 L124 use **315**.
The parenthetical "all also ETP" cannot hold against the 00:35 figures (324 > 323). There is no
committed output for 324.
*Exact fix:* use **315** and cite `raw/pool_analyze_p4_20261114.txt`; or, if 324 was a 23:44 snapshot,
state both times and the command, and reconcile "all also ETP" (it would be 315 at 00:35, not 324). Keep
one number per time.

**M4 — The P4 (A100) reason is internally contradictory and is contradicted by the committed
`condor_q -better-analyze` output.**
*Evidence:* report L59 says the A100 parent has "`GPUs=0`, `Cpus=0`, **all children
Claimed/Preempting**; becomes runnable when the node frees". Report L66 (same page) says the c03 analysis
"matched **3 drained slots** … `[10]&&[11]` 0, **2 would match if drained**". `raw/pool_analyze_p4_20261114.txt`
L35–48 is explicit: `[0] 3 matched / 3 drained`, `[12] 0 matched / 3 drained`, "2 slots would match if
drained". `host_facts_B` L26 shows the A100 parent `8 Unclaimed`; `host_facts_A` A7 L99 shows `0` CPUs /
`0` GPUs under the `-af:t Name CPUs Memory Disk GPUs` query. The probe review's M5 said exactly this
ambiguity must be recorded, not resolved by guessing.
*Exact fix:* replace the P4 reason with the committed analyze result — "3 A100 slots match the device
term, all 3 are Drained; 0 match now, 2 would match if drained" — and add one sentence recording the
`host_facts_B` (8 GPUs, Unclaimed) vs `host_facts_A` (0/0) ambiguity per M5. Delete "all children
Claimed/Preempting" unless a committed `condor_status` transcript shows it.

**M5 — The +6 h wave is simultaneously "dropped" and "prepared", and the stated cut-off basis
contradicts the report's own 09:30 hard stop.**
*Evidence:* report L66: "the +6 h wave **cannot fit before the 05:30 stop** (errata A4) and is
**dropped**." L84: "A +6 h sample is **prepared as `P1w3`/`P3w3`** if the report/review stay on
schedule." The header L4 says the hard stop was moved to **09:30 CET**, which would make a ~05:50 +6 h
sample fit; errata A4's reason for dropping it was the 05:30 stop. No `P1w3.jdl`/`P3w3.jdl` or queue rows
exist.
*Exact fix:* state one outcome. If the 09:30 extension is real, either run the +6 h sample and add
`P1w3`/`P3w3` rows, or say "not run — the report/review priority and the remaining window did not allow
it", without the false "cannot fit before 05:30" rationale. If the extension is not real, revert to the
05:30 stop and say "dropped". Remove the "prepared" claim unless the JDLs/rows are committed.

**M6 — `gpu_register.tsv`, required by errata A4/A6, is absent, so the GPU-hour claim is unbacked.**
*Evidence:* A4's deliverable list includes `gpu_register.tsv`; A6 requires one row per job with
`gpu_hours = run_s/3600`, restarts/evictions counted, stop at 5.0 GPU-h. The file is not under
`docs/r1/reports/htcondor_prep_20261114/` (`ls` fails). Report L103 says "GPU use stayed far below the
6 GPU-h cap (P5 used 2 s of GPU time)" but there is no register, and P4/P6/P7 plus the wave-2 jobs are
not tabulated.
*Exact fix:* commit `gpu_register.tsv` with one row per GPU job (P4 0 s idle, P5 2 s, P6 0 s, P7 0 s;
wave-2 P1/P3 have no GPU) and cite it in §7; or state explicitly that the register was not maintained and
that the 6 GPU-h statement is an upper bound, not a measured register.

**M7 — Several open questions do not meet runbook §7's required shape (context, options,
recommendation, paste-ready answer).**
*Evidence:* `HTCONDOR_QUESTIONS_20261114.md` Q4 has a recommendation and a paste-ready line but **no
options**; Q5 has a bundle of five facts, a placeholder paste-ready line (a fill-in template rather than
an answer) and **no recommendation**; Q6 has no options and no recommendation; Q7 is "informational" with
no recommendation; Q9 has no options and no recommendation; Q11 has no options and no recommendation.
Runbook §7 L233: "Each question gets its context, options, a recommendation and a paste-ready answer."
*Exact fix:* add an explicit `Options` and `Recommendation` to Q4/Q5/Q6/Q7/Q9/Q11, and replace Q5's
placeholder with a concrete answer line that names the measured V100S count, the `g4401` Drained state
and the `bms2` reachability. Q7 may stay informational only if it is moved out of the numbered question
list.

**M8 — The probe stdout that supports the environment claims is not committed.**
*Evidence:* `P1.out`, `P3.out`, `P5.out`, `P1w2.out`, `P3w2.out` exist in the worktree but are ignored
by `.gitignore:4:*.out`; `git ls-files docs/r1/reports/htcondor_prep_20261114/probes/out` lists only
`P1.err`, `P3.err` and `queue_times.tsv`. The report's claims about `nproc`, CPU model, `/work`/`/ceph`
mounts, `/cvmfs`, `/scratch`, the V100S UUID and `NVIDIA_VISIBLE_DEVICES=void` depend on these files.
*Exact fix:* force-add the five `.out` files (or copy them to `raw/probe_out/` and commit), and add them
to §8's delivery list. The queue-time numbers are already safe in `raw/queue_times_current.tsv`; this is
about the environment evidence.

**M9 — The delivery section's push statement is self-contradictory and not supported by the local
repository.**
*Evidence:* report L108: "The branch is pushed to `origin` (the dry-run confirmed the push is possible;
**the final push is done at the end of the window**)." `git branch -r` has no
`origin/htcondor-prep-20261114` ref; the report is committed at 03:19 while the stated window runs to
09:30. The two clauses cannot both be true at the report's own timestamp.
*Exact fix:* state "**committed locally; push/bundle pending**" and, after the push, record the pushed
SHA and the `READY.txt`/bundle path; or state the exact `origin` ref and time if the push did happen.
Do not claim "is pushed" before it is.

**M10 — The X.7 claim that the GGUF SHA-256 was "verified tonight" has no transcript.**
*Evidence:* report L104/L126: "its SHA-256 was **verified tonight** as `509287f7…4d3c`". No
`sha256sum` output for `/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf` is committed; the hash
appears only in older reports (`DT_SWEEP1_READINESS_20261027.md`, `LIVENESS_LLAMACPP_20261026.md`), and
no hashing step for it appears in the night's evidence.
*Exact fix:* add the `sha256sum` transcript (with time) to `raw/`, or reword to "matches the 26 Oct pin
`509287f7…4d3c`; **not re-hashed tonight**". The X.7 recommendation can stand on the older pin, but not
on an unrecorded tonight verification.

**M11 — "Track P data prep is fine on the 8-core/187 GB workers" is not measured.**
*Evidence:* report L102. P2 (the 8-core/16 GB job) never ran — `raw/queue_times_current.tsv` L3 is
`IDLE`; only P1 (1 CPU, 187 GB host) ran. No 8-core execution or data-prep probe exists.
*Exact fix:* say "the 1-CPU/187 GB worker class is observed and suitable for light data prep; the 8-core
class was not measured (P2 still idle), so Track P data-prep throughput is unmeasured."

**M12 — "M1/M2 pre-submission checks run and recorded" is not what the report itself says, and no
record exists.**
*Evidence:* report L18/L113 says the probe unit was accepted "with M1/M2 **pre-submission** checks, both
of which were then measured"; L52 says "M1/M2 were **then** measured (see §3)". The probe review's M1
required a `CloudSite` check **before P2–P7**, and M2 a `ProvidesETPResources`/`HasDocker` check **after
P1**; no such output is in `raw/`. P1's success supports `ProvidesETPResources`, but the `CloudSite`/
`HasDocker` attributes are exactly the M2 gap above.
*Exact fix:* replace with "P1's result supports `ProvidesETPResources`; the `CloudSite`/`HasDocker`
checks were not run before P2–P7, and P6's no-match raised Q8" — or commit the checks and the time they
ran. Do not claim a pre-submission record that does not exist.

### MINOR

**m1 — "both completed with 21 s … faster than wave 1's 73 s / 7 s" (L84) is false for P3.** P3w2's
21 s is slower than P3's 7 s (`raw/queue_times_current.tsv` L4 vs L10). *Fix:* "P1 wave 2 was faster
(21 vs 73 s); P3 wave 2 was slower (21 vs 7 s)."

**m2 — "8 of 9 entries moved, 12.2 GB" (L26/L125).** The eight moved rows sum to
12,298,122,900 B = **12.30 GB**, not 12.2. *Fix:* "12.3 GB".

**m3 — "P2 > 45 min (idle at this draft)" (L77).** At the report's 03:19 timestamp P2 had been idle
since 22:52 UTC = **3 h 27 min** (3 h 16 min at the 03:08 queue snapshot). ">45 min" is a stale 00:37
figure and is far below the runbook §4.2 `>4h` note. *Fix:* "idle 3 h 27 min at 03:19, still queued".

**m4 — The queue-times pointer is stale.** L64 cites `raw/queue_times_snapshot1.tsv` (wave 1 only) and
calls it "updated on the host"; the wave-2 rows are in `raw/queue_times_current.tsv`, and
`probes/out/queue_times.tsv` is the older wave-1 file with blank site/host and a truncated GPU string.
*Fix:* cite `raw/queue_times_current.tsv` for the final table and say which file is which.

**m5 — The failed-copy retirement paths are not in the log.** `MOVE_LOG.tsv` `work` row (line 8) has
`moved_to` blank and only `copy_failed(rc=23)`; the `zc_host` first failure (line 5) has `moved_to`
blank. The paths (`/work/dwong/_to_delete/work.failed_20261113T235407Z`, `zc_host.failed_*`) are only in
Q12/notes. *Fix:* add the two retirement paths and an `ls` of `/work/dwong/_to_delete` to
`MOVE_LOG.tsv`/`raw/`.

**m6 — `MOVE_BACKFILL.tsv.first_attempt_<UTC>` is referenced but absent.** `MOVE_LOG_NOTES.md` says the
first backfill attempt "was preserved as `MOVE_BACKFILL.tsv.first_attempt_<UTC>`"; no such file is in the
worktree. *Fix:* commit it, or delete the claim and say the first attempt was discarded.

**m7 — The H200 Idle→Drained transition is omitted.** `host_facts_A` A6 L90 shows `g4401` `Unclaimed
Idle` at 23:38; `host_facts_B` B3 L33 shows `Drained`. The report L62 says only "Drained". The probe
review's M3 asked for the submit-time state and the transition. *Fix:* record both snapshots and the
state at submission.

**m8 — "`docker info` … (twice, 23:39 and 23:41 CET)" (L44) — one transcript.** `host_facts_A` A9 L119–
123 is one failure (22:38 UTC = 23:38 CET); no second run is committed. *Fix:* commit the second output
or say "once at 23:38".

**m9 — 759618's "IDLE", `Iwd` and `Cmd` are not in the raw evidence.** `raw/pool_facts_raw.txt` shows
only `759618 cms cms.dwong`; `host_facts_B` B1 says "1 held" for all users. The report L39 and Q3 repeat
the unrecorded Iwd/Cmd/state. *Fix:* quote the `condor_q -af ClusterId JobStatus Iwd Cmd
AccountingGroup` output and reconcile "idle" with "1 held" (this was already move-plan review F15).

**m10 — "all four ETP login hosts … mount `/ceph/dwong`" (Q9).** `MOVE_LOG.tsv` `inuse_hosts` shows the
hosts were reached and `screen` was checked; it does not show a `/ceph/dwong` mount check. *Fix:* record
the mount check (`ls /ceph/dwong` per host) or say "reachable; mount not separately checked".

**m11 — "`-c3` measured ~5 MB/s" (L28) is unsupported.** No measurement is committed; the script uses
`-c2 -n7`. *Fix:* remove the number or record the measurement.

**m12 — The W2 citation is broken.** L92/Q1 cite `reports/W2_BUDGET_FIELDS_20261109.md`; no such file
exists in this worktree (it may be on `origin/mac-w2-budget-20261109`). *Fix:* cite the branch/commit and
the full path, or drop the "exactly predicted" claim.

**m13 — P4/P6 were not resubmitted in wave 2, but the report does not label this a deviation from
errata A4.** A4's 02:50–03:10 window says "P1, P3, P4, P6 (+3 h sample)"; the report L84 explains why
P4/P6 were left as continuous samples, which is a reasonable choice, but it is a deviation. *Fix:* say
"deviation from A4: only P1/P3 were resubmitted; P4/P6 left as continuous queue samples (P4 idle, P6
no-match), so the +3 h sample covers 2 of 4 planned probes."

**m14 — "P4/P6/P7 have structural no-match" (L15).** P4 is a capacity wait (the report's own table says
so); only P6 is structural and P7 is drained. *Fix:* "P4 capacity; P6 structural no-match; P7 drained".

**m15 — "P2 … 0 willing now, 5 slots would match if drained" (L57) has no committed P2 analyze.**
`raw/pool_analyze_p4_20261114.txt` is P4-only. *Fix:* commit `condor_q -better-analyze 759620` or
soften to "0 willing at the snapshot; no P2 analyze saved".

**m16 — W2's interpreter/checkout/exit code are prose only.** The W2 directory has `w2_check.json` and
`ledgers.txt`; the `python -VV`, the clean detached checkout path, and exit 3 are not recorded there.
*Fix:* commit the stdout/stderr/`python -VV` and the exit code (or add an `env` block to
`w2_check.json`).

**m17 — `POOL_FACTS.md` says P1 "run 3 s" (§5 L59) while the report and `raw/queue_times_current.tsv`
say 1 s.** The report is right; the evidence package is inconsistent. *Fix:* correct `POOL_FACTS.md` to
1 s (P1 submit 22:51:21, execute 22:52:34, end 22:52:35).

### NIT

**n1 — "Wave 2 (+2h51m)" (L84).** `22:51:21Z` → `01:43:21Z` is **+2 h 52 min**. *Fix:* "+2 h 52 min".

**n2 — "P4/P5 stay queued at least until 05:30" (L4).** P5 completed at 22:56:07Z; it is not queued.
*Fix:* "P4 stays queued; P5 completed".

**n3 — The report title still says "(report, draft)" although the commit is "report finalised".**
*Fix:* remove "draft" (folded into B1).

**n4 — The header's probe status omits wave 2.** L4 says "P1/P3/P5 completed, P2/P4/P6/P7 queued" while
L129 correctly includes P1w2/P3w2. *Fix:* include the wave-2 completions in the header.

**n5 — The "hard stop moved to 09:30" is not traceable to a committed message.** L4/POOL_FACTS §7 assert
it; no verbatim author line is in `raw/`. This is an author instruction, not host evidence, but it
changes the runbook's 05:30 safety rule. *Fix:* record the author's line and time in the report (or in a
small `raw/author_guidance.txt`), and state the B1/Tailscale handover.

**n6 — `raw/entry_stats.tsv` still contains the four malformed rows (`hcp_meg`, `models`,
`trigger_efficiency.tar.zst`, `round5-titan-c7517f1.bundle`).** The report does not mention it; the
move-plan provenance does (R3). *Fix:* add one sentence "the four `entry_stats.tsv` rows are malformed;
the plan uses the direct re-measurements" or correct the TSV.

---

## 3. Verdict

The report's move log, backfill, no-deletion protocol, W2 counts and probe wait/run numbers are
supported by the evidence, and the two false-negative incidents are disclosed honestly. It is not,
however, acceptable as the phase report: §1 contradicts the body on whether the night's main deliverable
happened, the inventory headline is not the sum of its own cited file, §6's per-class median/range is
missing, several central pool/NEMO2/GPU-hour claims have no committed transcript, the question list does
not meet §7's shape, and the delivery statement is self-contradictory. B1–B2 and M1–M12 must be fixed and
the report re-submitted to a fresh reviewer.

VERDICT: NOT ACCEPTED

---

## 4. Minimal fix list (in order)

1. **B1:** rewrite §1 rows 1/3 and the review-discipline sentence; remove "at this draft"/"second review
   round"/"draft" from the title.
2. **B2:** replace 560.3 GB / 385,744 files with 634.1 GB / 385,937 files (or name the subset and cite
   the command/time).
3. **M1:** add the per-class n/median/range table; local CPU 1-core median 21 s, range 7–73 s; mark
   censored classes.
4. **M2:** commit the NEMO2 `CloudSite`/`HasDocker`/`HasSingularity` check and the P6 analyze; correct
   6 L40S → the measured count (3 visible; 5 NEMO2 GPU slots in the 00:34 count); or downgrade to
   author-reported.
5. **M3:** use 315 (or two timestamped counts) for `HasDocker`; reconcile "all also ETP".
6. **M4:** replace the P4 reason with the committed analyze (3 Drained; 0 now; 2 if drained) and record
   the A7/B2 ambiguity.
7. **M5:** state one +6 h outcome; remove the "05:30 cannot fit" rationale if the hard stop is 09:30.
8. **M6:** commit `gpu_register.tsv` or state it was not maintained.
9. **M7:** add options + recommendation to Q4/Q5/Q6/Q7/Q9/Q11; make Q5's paste-ready concrete.
10. **M8:** force-add the five `.out` files (or `raw/probe_out/`) and list them in §8.
11. **M9:** state "committed locally; push/bundle pending" or record the pushed SHA/`READY.txt`.
12. **M10:** add the GGUF `sha256sum` transcript or say "matches the 26 Oct pin; not re-hashed tonight".
13. **M11:** say the 8-core class was not measured; do not call data prep "fine".
14. **M12:** replace "M1/M2 pre-submission checks run and recorded" with what was actually done.
15. Then m1–m17 and n1–n6 (mostly one-line corrections).

---

## 5. What I could not check, and residual risk

- **Live pool after 03:08 CET.** `raw/queue_times_current.tsv` is the last snapshot I have; P2/P4/P6/P7
  may have run, been held or been removed after it. The report's "still queued" is true at that
  snapshot, not necessarily at 09:30.
- **Remote push / bundle / `READY.txt`.** No network and the main checkout is off-limits; the local repo
  has no `origin/htcondor-prep-20261114` ref. The report's "pushed" claim cannot be confirmed here.
- **The author's 09:30 hard-stop change and ~00:35 guidance.** No verbatim message is committed; I can
  only note that the report and `POOL_FACTS.md` assert it.
- **The actual `/ceph/dwong` and `/work/dwong` state now.** No SSH: I cannot see the symlinks, the
  `_to_delete` originals, the `work`/`zc_host` failed copies, or confirm nothing was deleted. The
  scripts and `MOVE_LOG`/`MOVE_BACKFILL` are consistent with no deletion, but they are the only evidence.
- **The raw rsync/in-use/job-event transcripts.** `moves/rsync_*.log`, `moves/inuse_*.txt`,
  `probes/P*.log`, `clusters.tsv` are not committed; the report's ACL failure, the per-host in-use
  checks and the event-log times rest on the summary logs and `raw/queue_times_current.tsv`.
- **The image.** No docker daemon, no build, no I1–I4; the report's deferral is correct under A3, but the
  image's contents/CUDA/llama.cpp SHA are untested.
- **The ETP wiki facts.** Login-gated from this machine; I relied on the errata's fact ledger, as the
  report does.
- **W2's interpreter and exit code.** Not in `w2/`; the JSON status is `STOP_DIFFERENCE`, which is
  consistent with A1's exit-3 semantics, but the code itself is not recorded.

**Residual risk if the above fixes are applied:** the report would still be a single-snapshot,
single-observer record of a busy pool; the P2/P4/P6/P7 classes would remain censored, the NEMO2 Docker
conclusion would still need the site's confirmation (Q8/Q10), and the GPU-hour register would be a
post-hoc reconstruction unless the event logs are committed. None of these blocks a corrected report,
but they should be stated in it.

---

## Re-check round — report fixes at 207b2a7f (final go/no-go)

**Reviewed:** `docs/r1/reports/HTCONDOR_PREP_20261114.md` at commit **`207b2a7f`** (HEAD of
`htcondor-prep-20261114`; `git ls-remote --heads origin htcondor-prep-20261114` returns the same
`207b2a7ffb0d49886d00737b2e54f50bc6edbb68`, so the round-1 M9 push question is settled), report SHA-256
`6bdca60d1cf8e703556103304da711f61e68ab67015230849f1c37c694683bc1`; question list SHA-256
`3d00f03064b13065ff15afe323d917c180d5e83a1dc02b8219e840348eafc9a6`. Same worktree, working tree clean
at the reviewed commit. **Date/time:** 14 November 2026, 03:33–03:40 CET. Read-only, as required: no SSH,
no cluster command, no job, no move, no git commit; only this review file was written (it is untracked).

**Scope.** Re-check of the round-1 findings B1–B2, M1–M12, m1–m17, n1–n6 against the committed evidence,
plus the honesty/standing-rule check. This is not a fresh full review; the unchanged parts are covered by
round 1.

### R.1 Round-1 findings — status

| ID | Round-1 subject | Status | Evidence in the reviewed commit |
|---|---|---|---|
| B1 | §1 stale "plan only" | **fixed** | §1 row 1 records 8/9 moved (12.3 GB), `work` ACL-skipped, "No deletion anywhere"; title has no "(draft)"; "second review round" gone; §1's review sentence names the report's own NOT ACCEPTED → fixes. |
| B2 | inventory totals | **fixed** | independent sum of the 70 `raw/inventory.tsv` rows = **634,100,228,441 B = 634.10 GB / 385,937 files** — exactly what §2 now says. |
| M1 | per-class median/range | **fixed** | `raw/queue_times_current.tsv`: local 1-core P1/P3/P1w2/P3w2 = 73, 7, 21, 21 s → n=4, median **21**, range **7–73**; the report's class table has exactly that and marks the censored classes. |
| M2 | NEMO2/P6 claims | **fixed except R2** | `raw/nemo2_attrs.txt`, `raw/p6_analyze.txt` and `raw/evidence_capture_0331.txt` committed: 6 L40S (4 Unclaimed, 2 Drained), `HasDocker=undefined`, `HasSingularity=true`, `CloudSite=BwForCluster-Nemo2`, P6 analyze `[2]`=6, `[5]`=6, `[6]`=0. H200 count is off (R2). |
| M3 | `HasDocker` 324→315 | **fixed (number) / R3 (citations)** | 315 docker / 323 ETP / 1094 singularity / 5 and 13 unclaimed are in `raw/pool_analyze_p4_20261114.txt`; report/POOL_FACTS now use 315 and "all also ETP". The file/time attribution is wrong (R3). |
| M4 | P4 reason | **fixed** | `raw/p4_analyze_local.txt` (0 local-schedd match) and `raw/pool_analyze_p4_20261114.txt` (3 matched / 3 drained, `[10]&&[11]`=0, 2 would match if drained): the report's P4 reason now says exactly that, records the A100 parent `TotalSlotGPUs=8` vs `GPUs=0`/`Cpus=0` ambiguity and the author's keep-queued instruction. |
| M5 | +6 h wave | **NOT fixed — R1** | Report L95 and POOL_FACTS L88 say planned at ~05:52 CET under the 09:30 extension; report L66 and POOL_FACTS L51 still say "cannot fit before the 05:30 stop (errata A4) and is dropped". Same contradiction as round 1. |
| M6 | gpu_register.tsv | **fixed (file) / R6 (citation)** | `gpu_register.tsv` committed: P4 0, **P5 2 s = 0.000556 GPU-h**, P6/P7 0, total 0.000556, under the 5.0/6 GPU-h caps. Not cited in §7/§8 (R6). |
| M7 | question shape | **fixed except R7** | the "Completing the runbook §7 shape" section adds Options / Recommendation / Paste-ready for Q4, Q5, Q6, Q7, Q9, Q11; Q5's answer line is still generic (R7). |
| M8 | probe stdout committed | **fixed (files) / R8 (list)** | `git ls-files` shows `probes/out/P1.out`, `P3.out`, `P5.out`, `P1w2.out`, `P3w2.out` committed. Not in §8's delivery list (R8). |
| M9 | push statement | **fixed** | `origin/htcondor-prep-20261114` = HEAD `207b2a7f` (verified by `git ls-remote`); §8 now states the pushed branch. |
| M10 | GGUF sha transcript | **fixed** | `raw/gguf_sha256.txt` committed: `509287f7…4d3c  /ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf`. |
| M11 | Track P "fine" | **fixed** | §7 says Track P training is **not measured** (8-core class never ran; P2 queued). |
| M12 | M1/M2 timing | **mostly fixed — R4** | §1/§5 now say the checks were measured **after** submission; §9 L124 still says "M1/M2 pre-submission checks run and recorded". |
| m1–m4, m6, m7, m10–m17 | minors | **fixed** | wave-2 slower-for-P3 wording; 12.3 GB; P2 ~3 h 40 min at 03:31; queue pointer to `raw/queue_times_current.tsv`; `MOVE_BACKFILL.tsv.first_attempt_20261113T235210Z` committed; H200 Idle→Drained note; `raw/login_hosts_mounts.txt` + Q9 bms2 verified; -c3 ≈5.3 MB/s derivation; W2 report exists on `origin/mac-w2-budget-20261109`; A4 deviation labelled; `raw/p2_analyze.txt`; `w2/w2_run.txt` (interpreter/checkout/exit 3); POOL_FACTS P1 run 1 s. |
| m5 | failed-copy paths | **fixed** | `raw/failed_copies.txt` committed: `work.failed_20261113T235407Z` and `zc_host.failed_20261113T234708Z`; report §2 names both. |
| m8 | docker runs | **NOT fixed — R9** | report §4 says "twice, 23:39 and 23:41 CET"; committed transcripts are both `2026-11-14T02:30:10Z` (03:30 CET). |
| m9 | 759618 fate | **NOT fixed — R10** | report asserts "REMOVED (status 3)" and clusters 759626–759636; `raw/foreign_jobs.txt` contains neither 759618 nor its status, and only 759636. |
| n1, n3, n6 | nits | **fixed** | +2 h 52 m; no "draft" in the title; §2 states the four malformed `entry_stats.tsv` rows. |
| n2, n4, n5 | nits | **NOT fixed — R11–R13** | header still says "P4/P5 stay queued", still omits P1w2/P3w2, and the 09:30 hard-stop change still has no committed author line. |

**Other things re-verified in this round (round-1 positives hold):** 8 moved entries = **12,298,122,900 B
= 12.30 GB** (sum of the moved rows in `MOVE_LOG.tsv.v1` + `MOVE_LOG.tsv`); `MOVE_BACKFILL.tsv` 8/8
`verdict=ok` on all six checks; v2 20-column `MOVE_LOG.tsv` with the reviewer's metric confirmation row
recorded verbatim (plus `MOVE_LOG_NOTES.md`); the v2.2 `*/.git/index` manifest exclusion is implemented in
both `move_entry.sh` and `verify_pair.sh` and disclosed; `zc_host` first-copy false negative and `work`
ACL failure are disclosed with retired copies, and **no `rm` appears anywhere**; W2 re-parsed from
`w2/w2_check_rerun2.json`: **288 ledgers, 14 with differences** (`import` gives 20, 9, 15 …), **53
precheck_rejection rows**, max `worker_runs_total` 20, `worker_runs_over_cap=false`, status
`STOP_DIFFERENCE`, `w2_run.txt` records `exit_code=3`, interpreter and checkout `0b62fb03`; the 15 %
disk floor and the 10-job/GPU caps are respected (move log floors 212 GiB; gpu register 0.000556 GPU-h);
I1–I4 not run and P3-not-remote are stated.

### R.2 Remaining findings (exact fixes)

| ID | Sev | Finding and evidence | Exact fix |
|---|---|---|---|
| R1 | **MAJOR** (the pending +6 h item) | Report L66: "the +6 h wave cannot fit before the 05:30 stop (errata A4) and is dropped"; POOL_FACTS L51: "the +6 h wave is dropped (errata A4)". Report L95/POOL_FACTS L88: "planned at ~05:52 CET … possible only because the author moved the hard stop to 09:30". The same self-contradiction round-1 M5 flagged is still present; the 05:30 rationale is false under the 09:30 extension. | Replace the L66 clause with "the +6 h sample is planned at ~05:52 CET under the author's 09:30 extension; its outcome is recorded when it runs (or recorded as not run)"; make POOL_FACTS L51 the same. |
| R2 | MINOR | §5 L61 and POOL_FACTS L64/L93 say the 03:30 NEMO2 view had **3 H200** slots; `raw/evidence_capture_0331.txt` (`2026-11-14T02:30:10Z` = 03:30 CET) and `raw/nemo2_attrs.txt` list **4 H200** slots (1 Unclaimed, 3 Drained). The 03:32 CloudSite check (`raw/m1_m2_checks.txt`) lists a different 3-slot set. | "6 L40S (4 Unclaimed, 2 Drained) + 4 H200 (1 Unclaimed, 3 Drained) at 03:30; the 03:32 CloudSite check lists 3 H200 slots". |
| R3 | MINOR | §3 L38 attributes 315/323/1094 to `raw/evidence_capture_0331.txt` and says "315/323 at 03:30 CET, 318/326 at 03:38 — raw/m1_m2_checks.txt". The counts are in `raw/pool_analyze_p4_20261114.txt` (last failed match 00:34:42Z = 00:35 CET); `raw/m1_m2_checks.txt` is timestamped `02:32:02Z` (03:32 CET) and shows "326 318"; there is no 03:38 evidence. Same mis-attribution in POOL_FACTS L69/L93. | Cite `raw/pool_analyze_p4_20261114.txt` (00:35 CET) for 315/323/1094/5/13 and `raw/m1_m2_checks.txt` (03:32 CET) for 326/318; drop "03:38". |
| R4 | MINOR | §9 L124 still says "M1/M2 pre-submission checks run and recorded"; the committed checks were run after submission (`raw/m1_m2_checks.txt` 02:32:02Z; `raw/evidence_capture_0331.txt` 02:30:10Z), and §1/§5 now say so; the probe review's M1/M2 were pre-submission *conditions*, not a record. | "M1/M2 conditions measured after submission (03:30/03:32 CET) and recorded; they support the JDLs." |
| R5 | MINOR | §5 P7 (L62/L93) says the H200 slots "all were Drained at analysis"/"only H200 slot Drained at submit"; `raw/evidence_capture_0331.txt` has **1 Unclaimed H200 at 03:30**, and `host_facts_A` A6 shows it Unclaimed Idle at 23:38. The no-match is primarily structural (`HasDocker=undefined`, as P6), with the H200 state varying. | "P7: no match because NEMO2 slots have `HasDocker=undefined` (structural, same as P6); H200 state was Unclaimed Idle at 23:38, Drained at 23:40, and 1 Unclaimed at 03:30 — all ineligible for a docker-universe job." |
| R6 | NIT | `gpu_register.tsv` is committed (P4–P7; 0.000556 GPU-h total) but is not cited in the report or POOL_FACTS, so §7's "far below the 6 GPU-h cap" reads as prose. | Cite `gpu_register.tsv` in §7 (and list it in §8). |
| R7 | NIT | Q5's "paste-ready" line is still generic (`V100S 总数 <待确认>`), and does not name the measured V100S nodes (8 GPUs each, site total unresolved), the g4401 Drained transition or bms2 reachability, as round-1 M7 required. | One concrete Q5 line: "以实测为准；V100S 按 8-GPU 节点（站点总数待确认）；g4401 于 23:40 Drained；bms2 可登录并挂载 /ceph/dwong（Q9）。" |
| R8 | NIT | The five `probes/out/*.out` files are committed (verified with `git ls-files`) but §8's delivery list only says "probe JDLs/probe.sh/dry-runs". | Add `probes/out/` to §8. |
| R9 | MINOR | §4 L44: "`docker info` … (twice, 23:39 and 23:41 CET)". The committed transcripts (`raw/docker_info.txt`, `raw/evidence_capture_0331.txt`) are both `2026-11-14T02:30:10Z` (03:30 CET), and the second run's capture shows only the client banner, not the daemon error. | "Two runs at 03:30 CET (raw/docker_info.txt); the first shows the daemon error, the second capture is truncated after the client banner — one confirmed failure; the original 23:38 failure is `host_facts_A` A9." Or commit the full second output. |
| R10 | MINOR | §3 L39 asserts 759618 "later left the queue as REMOVED (status 3, never executed)" and "clusters 759626–759636"; `raw/foreign_jobs.txt` (titled 759618/759636) contains neither 759618 nor its status, and lists only 759636 besides our own idle probes 759620/759622/759624/759625. | Commit the query showing 759618's final state (ClusterId/JobStatus) and correct the cluster range to the clusters actually observed; otherwise delete the fate claim. |
| R11 | NIT | Header L4 still says "P4/P5 stay queued at least until 05:30"; P5 completed at 22:56:08Z (`raw/queue_times_current.tsv`). (L66 has the correct "P5 had already completed".) | "P4 stays queued (P5 completed)". |
| R12 | NIT | Header L4 status still lists only "P1/P3/P5 completed, P2/P4/P6/P7 queued"; wave 2 (P1w2/P3w2) is missing from the header (it is present in §1/§5). | Include P1w2/P3w2 in the header status. |
| R13 | NIT | The 09:30 hard-stop change supersedes the runbook's 05:30 safety rule but still has no committed author line (round-1 n5). | Add `raw/author_guidance.txt` with the author's message and time. |
| R14 | NIT | §2 L26 cites `raw/evidence_capture_0331.txt` for the `work` ACL failure, but that file has only the failed-copy `ls`; the "Operation not supported" text is prose (Q12/MOVE_LOG_NOTES) and the log row has `copy_failed(rc=23)`. | Cite the `MOVE_LOG.tsv` row + a committed rsync transcript (or say the rc is the record). |

### R.3 Honesty and standing-rule check (round-1's central question)

- **Deviations disclosed:** `du -sb` CephFS `st_size` false negative (report L27 + `MOVE_LOG_NOTES.md` + the
  v1 log rows) ✓; `zc_host` `.git/index` false negative and the retired first copy ✓; `work` ACL failure
  and the retired partial copy ✓; I1–I4 not run (docker gate) ✓; P3 did not run remotely ✓; +6 h wave
  pending (R1); bms2 now **verified** reachable and mounting `/ceph/dwong` (`raw/login_hosts_mounts.txt`,
  Q9) ✓; the author's 09:30 extension is stated (traceability R13).
- **No deletion:** every move log row and backfill row is consistent with retire-by-move + symlink; no `rm`
  in the scripts, logs or report; the two failed copies are under `/work/dwong/_to_delete/` with an `ls`
  transcript ✓.
- **10-job / 6 GPU-h / 15 % disk:** gpu register 0.000556 GPU-h (caps untouched) ✓; move floors 212 GiB
  recorded, post-plan free ~1.08 T ✓; no `condor_rm`/`condor_hold` (report L140) and the probe jobs are
  own jobs only ✓.
- **Paper B data / secrets / W2 carve-out:** W2 read is field-limited (budget_index/decision/worker_mode/
  extra.control), nothing adopted; no labels/metrics; no credential reads or `docker login` ✓.
- **Review trail:** runbook rejected→accepted; probe unit accepted; move plan rejected→accepted (+R1/R2,
  metric confirmation); this report rejected→fixed — the report now states this correctly (§9) ✓.
- **Fresh-review scope of this round:** the numbers above were re-derived from the committed evidence, not
  read from the prose. The only evidence I could not verify directly is the live pool after 03:08 CET, the
  host-side `/work`/`_to_delete` state, and the W2/rsync event logs (no SSH) — same limits as round 1.

**Result.** All round-1 BLOCKING and 11 of 12 MAJOR findings are fixed and evidence-backed; M5 is the only
MAJOR-level item still open, and it is exactly the pending +6 h item (its one-line stale clause is R1).
The remaining R2–R14 are MINOR/NIT precision/citation corrections. The report is **acceptable subject to**
(a) the R1 one-line correction (remove the "cannot fit before 05:30 … dropped" clause in the report and
POOL_FACTS), (b) the +6 h outcome recorded after ~05:52 CET, and (c) the R2–R14 one-line corrections in
the same final pass — none of them changes the report's substance, and **no new review round is needed**;
I will re-check the final diff if asked. Residual risk carried: the report remains a single-observer,
single-snapshot record; P2/P4/P6/P7 waits stay censored; NEMO2 Docker remains a site question (Q8/Q10);
`work` stays on `/ceph` (ACL) and `_to_delete` keeps the originals until the author retires them.

VERDICT: ACCEPTED

---

## Final verification (post-R1–R14 + wave 3)

**Reviewed:** HEAD **`2b8becbb`** (`git ls-remote --heads origin htcondor-prep-20261114` =
`2b8becbb8a5a37991ab5dee967a9d14e6ac72800`), diff `207b2a7f..2b8becbb` (10 files, +273/−26).
Report SHA-256 `83658398…e7f`; POOL_FACTS `c9ba8336…8ed`; questions `31d470ff…26e`. Worktree clean;
**06:01–06:05 CET**, read-only: no SSH, no job, no move, no git commit; only this review file was written.
This is a diff check, not a new review round.

### V.1 What the diff verified (Lead claims checked one by one)

| R | Claim | Result |
|---|---|---|
| R1 | both "+6 h dropped / cannot fit before 05:30" sentences gone; outcome recorded | **mostly ✓ / N1** — report L66 and POOL_FACTS §4/§7 now say "planned at ~05:52 under the author's 09:30 extension"; report §5 L95 records "submitted at 05:50:32 CET … both completed within 18 s (ms04/ms03, exit 0)"; header lists wave 3. `raw/queue_times_current.tsv` P1w3/P3w3: `submit 2026-11-14T04:50:32Z`, wait **18 s**, run 1 s, exit 0, `slot1_24@ms04` / `slot1_21@ms03` ✓. POOL_FACTS itself does **not** record the outcome (N1). |
| R2 | 4 H200 (1 Unclaimed, 3 Drained) in report and POOL_FACTS | **mostly ✓ / N2** — report P6/P7 rows and POOL_FACTS §5 P6 row now say 4 H200; POOL_FACTS §8 evidence list still says "6 L40S + 3 H200" (N2). |
| R3 | counts cited to pool_analyze (00:35) and m1_m2_checks (03:32, 326/318); no 03:38 | **mostly ✓ / N3** — report §3 and POOL_FACTS §5 L69 now cite the right files/times, no "03:38" anywhere; report §3 keeps a stray `(raw/evidence_capture_0331.txt)` after the 315 clause and POOL_FACTS §8 L93 still attributes the counts to evidence_capture (N3). (The raw 326/318 pair is unlabeled; 326 ETP > 318 docker is a sound inference but should be labelled.) |
| R4 | §9 "measured after submission" | **✓** — §9 bullet now says 03:30/03:32 CET, recorded in evidence_capture/m1_m2_checks. |
| R5 | P7 reason structural + H200 variation | **mostly ✓ / N4** — report P7 row fixed; POOL_FACTS §5 P7 row still says "the only visible H200 slot, g4401, is Drained" (N4). |
| R6 | gpu_register cited in §7 | **✓** — §7 says "`gpu_register.tsv`: 0.000556 GPU-h used, 5.0 GPU-h stop not approached". |
| R7 | Q5 concrete paste-ready | **✓** — names the 8-GPU V100S partitionable slots, c03-001-167 A100, g4401 Drained, bms2 login+mounts, site total unresolved. |
| R8 | probes/out in §8 | **✓ (five committed files) / N5** — §8 now lists "probe JDLs/probe.sh/dry-runs and the five probe stdout files (`probes/out/`)". P1w3.out/P3w3.out are **not** committed (git-ignored `*.out`, N5); the report does not cite them, so no report claim depends on them. |
| R9 | docker timing corrected | **partial / N6** — §1 row 2 fixed ("first failure 23:39 in host_facts_A; two runs at 03:30 in raw/docker_info.txt"); §4 L44 still says "twice, 23:39 and 23:41 CET" (N6). |
| R10 | foreign_jobs with 759618 REMOVED + clusters | **✓** — `raw/foreign_jobs.txt`/`raw/r10_r14_evidence.txt` show `759618 0 3 undefined 1794609657 …` (JobStatus 3 = REMOVED, ExitCode undefined = never executed) and clusters 759626–759636; report L39 backed. |
| R11/R12 | header P4/P5 + waves 1–3 | **✓ header / N7 P2 row** — header says "P4 stays queued (author asked P4/P5 not withdrawn; P5 completed at 22:56)" and lists waves 1–3; the new P2 row has wrong numbers (N7). |
| R13 | 09:30 as chat-level provenance | **✓** — header quotes the author's words `其余按 errata 继续，09:30 硬停` and marks them chat-level, not a committed author note. |
| R14 | ACL failure cited + rc=23 | **partial / N8** — the transcript IS committed in `raw/r10_r14_evidence.txt` ("rsync: set_acl … Operation not supported (95) … code 23") and the MOVE_LOG `work` row has `copy_failed(rc=23)`; but report §2 L26 still cites evidence_capture, and `raw/rsync_work_failed.log` itself is git-ignored/uncommitted (N8). |
| wave 3 / table | 18 s ms04/ms03; n=6 median 19.5 range 7–73 | **✓** — queue rows match; class table `73,7,21,21,18,18 → n=6, median 19.5, range 7–73`; remote best-effort `7,21,18 → n=3, median 18`; header "+5 h 58 m" is consistent with wave 1 at ~23:52 CET. |

**No BLOCKING or MAJOR finding.** The move log/backfill, W2 numbers, pool facts, wave 1–3 queue
numbers, the +6 h outcome, the docker gate, the 09:30 provenance and the no-deletion record all check out
against committed evidence.

### V.2 Remaining findings (all one-line MINOR/NIT)

| ID | Sev | Finding | Exact fix |
|---|---|---|---|
| N1 | NIT | POOL_FACTS does not record the +6 h outcome (only "planned … outcome recorded when it runs"), although it ran. | Add to POOL_FACTS §4 (or §7): "Outcome: P1w3/P3w3 ran at 05:50:32 CET, 18 s waits, exit 0 (`raw/queue_times_current.tsv`)." |
| N2 | MINOR | POOL_FACTS §8 evidence list still says the 03:30 capture has "6 L40S + 3 H200" (evidence_capture/nemo2_attrs show 4 H200). | "… NEMO2 slot attributes (6 L40S: 4 Unclaimed/2 Drained; 4 H200: 1 Unclaimed/3 Drained), all `HasDocker=undefined` …" |
| N3 | MINOR | Report §3 L38 keeps `(raw/evidence_capture_0331.txt)` right after "HasDocker is true on 315"; POOL_FACTS §8 L93 attributes the counts to evidence_capture. | Drop the stray parenthetical in §3 (the next sentence already cites pool_analyze); in POOL_FACTS L93 change "counts (315/323/1094)" to "counts (315/323/1094; `raw/pool_analyze_p4_20261114.txt`, 00:35 CET)". Optionally label the two numbers in `raw/m1_m2_checks.txt` as ETP/docker. |
| N4 | MINOR | POOL_FACTS §5 P7 row contradicts the report and the P6 row: "no H200 slot … the only visible H200 slot, g4401, is Drained". | Use the report's P7 wording: structural `HasDocker=undefined`; H200 state 1 Unclaimed Idle 23:38 → Drained 23:40 → 4 slots (1 Unclaimed, 3 Drained) at 03:30. |
| N5 | MINOR | `raw/P1w3.out`, `raw/P3w3.out`, `probes/out/P1w3.out`, `probes/out/P3w3.out` and `raw/rsync_work_failed.log` are git-ignored (`*.out`, `*.log`) and **not in the pushed commit** — the Lead's "committed" claim for the wave-3 stdout is not true. | Either `git add -f` the two wave-3 stdout files (as was done for the first five; §8 then says seven) or state that only `raw/queue_times_current.tsv` carries the wave-3 record. The rsync transcript is already committed inside `raw/r10_r14_evidence.txt`, so the `.log` itself is optional. |
| N6 | MINOR | Report §4 L44 still says `docker info` failed "twice, 23:39 and 23:41 CET"; the committed evidence is one failure at 23:39 (`raw/host_facts_A.txt` A9) and two runs at 03:30 CET (`raw/docker_info.txt`). | "… cannot connect (failure at 23:39 in `raw/host_facts_A.txt`; two runs again at 03:30 CET in `raw/docker_info.txt`) …" — or say "once at 23:39; re-checked twice at 03:30". |
| N7 | MINOR | Report §5 P2 row has three wrong numbers: "~7 h 5 min" (correct elapsed from 23:52:27 CET to 06:00 CET is **~6 h 8 min**); "0 willing at 00:35/03:30 analyses" (no P2 analyze exists at 00:35); "(2 willing / 4 drained at 04:00)" (the 04:00 analyze summary says **1** slot match and willing, **4 would match if drained**). Root: `raw/queue_4h_notes.txt` header says "submitted 2026-11-13T22:52 CET" but 22:52 is **UTC** (= 23:52 CET). | P2 row → "**still idle at 06:00 CET (~6 h 8 min; >4 h note captured 04:00 in `raw/queue_4h_notes.txt`)** | capacity: 0 match / 5 would match if drained at 03:30; 1 match / 4 would match if drained at 04:00"; fix the `queue_4h_notes.txt` header to "submitted 2026-11-13T22:52 UTC = 23:52 CET". |
| N8 | NIT | Report §2 L26 cites `raw/evidence_capture_0331.txt` for the `work` ACL failure; that file has only the failed-copy `ls`. The transcript is in `raw/r10_r14_evidence.txt`; `raw/rsync_work_failed.log` is uncommitted. | Cite `raw/r10_r14_evidence.txt` (and the MOVE_LOG `work` row `copy_failed(rc=23)`), or force-add the `.log`. |
| N9 | NIT | Report L66 still reads "planned at ~05:52 … outcome is recorded when it runs" although it ran; only §5 L95 records the run. | Append "it ran at 05:50:32 CET (see §5)" to L66. |

### V.3 Result

The material record is verified and consistent with the committed evidence; nothing changes a headline
number, the move/W2 record, the pool facts or any recommendation. The remaining items are the five
partially-applied R2/R3/R5/R9/R14 corrections (N1–N4, N6, N8) plus three evidence/arithmetic nits
(N5, N7), all one-line edits. After they are applied, no new review round is needed — I can confirm the
final diff. Residual risk unchanged: single-observer/single-snapshot record, censored P2/P4/P6/P7 waits,
NEMO2 Docker as a site question, `work` on `/ceph` and the originals in `_to_delete` until retired.

VERDICT: NOT ACCEPTED (remaining)

---

## Final diff check — N1–N9 at 7af377ec (last gate)

**Checked:** HEAD `7af377ec60356eb4c7fde28e523d684dd9550100` (= `origin/htcondor-prep-20261114`
by `git ls-remote`), diff `2b8becbb..7af377ec` (9 files: report, POOL_FACTS,
`probes/out/P1w3.out`/`P3w3.out`, `raw/P1w3.out`/`P3w3.out`, `raw/queue_4h_notes.txt`,
`raw/rsync_work_failed.log`, this review file), report SHA-256 `ce32ff2e…`, POOL_FACTS `4bea4e6e…`;
06:06–06:08 CET, read-only (no SSH, no git), only this file written.

**Confirmation.** The diff is clean for N2/N3/N4/N5/N6/N7/N8/N9 and matches the committed evidence:
POOL_FACTS §8 now says "6 L40S: 4 Unclaimed/2 Drained; 4 H200: 1 Unclaimed/3 Drained" and cites the
315/323/1094/5/13 counts to `raw/pool_analyze_p4_20261114.txt` (00:35 CET); the report §3 stray
`(raw/evidence_capture_0331.txt)` is gone; POOL_FACTS P7 now gives the structural `HasDocker=undefined`
reason with the H200 23:38→23:40→03:30 variation; §4 docker timing is "first failure 23:39
(`raw/host_facts_A.txt`); two further runs at 03:30 (`raw/docker_info.txt`)" with no 23:41 claim; §5 P2 is
now "~6 h 8 min" with the 04:00 analysis (1 matching/willing, 4 would match if drained) and the
`raw/queue_4h_notes.txt` header is fixed to "22:52 UTC = 23:52 CET"; §2 cites `raw/rsync_work_failed.log`
(force-added) + the `MOVE_LOG.tsv` `work` row `copy_failed(rc=23)`; §5 L66 says the +6 h sample **ran** at
05:50:32 CET; `probes/out/` now has seven tracked stdout files (P1w3/P3w3 force-added, both real
`probe=P1w3`/`P3w3` output on ms04/ms03) and §8 says seven; wave-3 numbers still match
`raw/queue_times_current.tsv` (18 s, ms04/ms03, exit 0; n=6 median 19.5, range 7–73). Two NIT residuals
only, neither affecting any number, conclusion or the move/W2/pool record: (i) **N1 is not actually in
POOL_FACTS** — §4/§7 still say the +6 h sample "is planned at ~05:52 … its outcome is recorded when it
runs (or recorded as not run)" although it ran; the report carries the outcome, so add the one-line
"ran: P1w3/P3w3 at 05:50:32 CET, 18 s, ms04/ms03, exit 0" to POOL_FACTS for consistency; (ii) report §5 P2
still says "earlier analyses (00:35/03:30) showed 0 willing / 5 drained" — there is no committed P2
analysis at 00:35 (cite 03:30 only) and "5 drained" should read "5 would match if drained". Both are
one-line copyedits; fix them in the close-out commit if convenient — I do not require another gate.
Residual risk is unchanged (single-observer/single-snapshot record, censored P2/P4/P6/P7 waits, NEMO2
Docker as a site question, `work` on `/ceph` with originals in `_to_delete` until retired).

VERDICT: ACCEPTED (final)
