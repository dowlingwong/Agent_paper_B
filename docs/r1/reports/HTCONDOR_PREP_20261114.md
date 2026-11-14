# ETP HTCondor preparation — night of 13/14 Nov 2026

**Phase:** HTCondor preparation (runbook `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` + errata `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md`). **AI-assisted** (DeepSeek Harness agent, "cluster agent" role). **Reported to the author in Chinese.**
**Window:** started 23:37 CET 13 Nov; the author moved the hard stop to **09:30 CET** 14 Nov (the runbook's 05:30 figure is superseded for this session; P4/P5 stay queued at least until 05:30 as instructed). **Status:** probe wave submitted and monitored (P1/P3/P5 completed, P2/P4/P6/P7 queued); W2 STOPPED on a difference; image build impossible (docker gate); **8 of 9 moves done and backfilled, `work` skipped (ACL)**; report under the runbook's §6 review loop.
**Evidence:** `docs/r1/reports/htcondor_prep_20261114/` (raw host facts, inventory, stats, pool facts, move plan, probe outputs, W2 summary); reviews in `docs/r1/reviews/HTCONDOR_*_20261114.md`.

---

## 1. Goal and what was actually possible

| Night goal (runbook) | Result |
|---|---|
| 1. Move small-file dirs `/ceph/dwong` -> `/work/dwong` safely | **Done for 8 of 9 entries (12.3 GB)** after the plan review (NOT ACCEPTED round 1 -> revision 2 -> ACCEPTED), each one entry at a time with copy -> verify -> retire into `_to_delete` -> symlink; the ninth (`work`) skipped because `/work` cannot hold POSIX ACLs. **No deletion anywhere.** |
| 2. Build a pinned container image | **Not possible tonight.** `docker info` on deepthought fails (daemon unreachable; two timestamped runs in `raw/evidence_capture_0331.txt`) — the errata's docker gate (A3) stops §3 before the build; no `docker login`, no credential read, no registry guess. `apptainer`/`singularity` are present. I1–I4 were therefore not submitted |
| 3. Try it on the batch system with small probe jobs | **Partial:** probe wave 1 (P1–P7) and wave 2 (P1w2/P3w2) were submitted after the JDL review; **P1, P3, P5, P1w2 and P3w2 ran and exited 0**; P2 queues on capacity; P4 queues on A100 occupancy; P6/P7 cannot match (NEMO2 has no Docker / H200 drained) |
| 4. Record queue times for every resource class | **Partial:** local CPU classes measured (P1, P3), **TOpAS V100S measured (P5, wait 212 s)**; 8-core local, A100, NEMO2 L40S and NEMO2 H200 not measured tonight (capacity / no-docker / drained) |

**Review discipline kept:** the runbook itself was reviewed by a fresh reviewer (NOT ACCEPTED round 1 -> errata -> **ACCEPTED**); the probe wave was reviewed before submission (**ACCEPTED**); the M1/M2 conditions were then measured after submission and recorded (`raw/evidence_capture_0331.txt`), and they support the JDLs; the move plan was NOT ACCEPTED round 1 -> revision 2 -> **ACCEPTED**, and the author's verification change got a one-sentence confirmation from the same reviewer. The phase report itself was reviewed (NOT ACCEPTED round 1; fixes applied — see §9).

## 2. Inventory and move plan (§1)

- 70 top-level entries under `/ceph/dwong` inventoried: **634.10 GB, 385,937 files** (sum of `raw/inventory.tsv`; the move-plan review independently computed the same 634.10 GB) (full top-level list in `raw/inventory.tsv`; per-entry percentiles in `raw/entry_stats.tsv`, whose four rows `hcp_meg`, `models`, `trigger_efficiency.tar.zst`, `round5-titan-c7517f1.bundle` are malformed and were re-measured directly — the plan uses the re-measured numbers).
- `/work` at inventory time: 1.4 T size, 385 G used, **1.1 T free (27 % used)**; `/ceph` 1.4 P with 346 T free (75 % used). `quota -s`/`quota -Q` print **no output** (no measurable per-user quota), so the errata's 15 % floor is computed against the filesystem capacity (≈210 G) — conservative.
- `pinned_paths.txt`: 213 lines from a read-only `git grep '/ceph/dwong'` across `docs/runbooks-14nov`, `origin/mac-int-20261107`, `origin/trackS-ops-20261030`, `origin/mac-b1-20261107`, `origin/dt-sweep1-20261026`. It pins `r1_batch1_*`, `agent_paper_B`, `opt` (llama.cpp build), `models` (the pinned GGUF), and `autoresearch_harness` paths.
- `MOVE_PLAN.md` revision 2: **9 entries to move (19.7 GB)**, 61 skipped with reasons (pinned/evidence/venv/large-file/unreadable/tiny/regular-file). The first review removed `hf_cache` (19.1 GB blob cache), the seven single-file entries, `ceph_lwindett` (root-only), and six evidence-boundary trees (conservative), and required the in-use check, disk gate, order/cut-off, and `_to_delete`/collision guards that revision 2 now has.
- **Moves (review trail: NOT ACCEPTED -> revision 2 -> ACCEPTED from the same reviewer, R1/R2 inline fixes, then the author's 14 Nov verification change confirmed in one sentence by the same reviewer).** Result: **8 of 9 entries moved, 12.3 GB**, each by copy -> verify -> re-check in-use -> retire into `_to_delete` -> symlink back; the old paths work through the symlinks. Every moved entry was re-verified after the fact against its retired original (`moves/from_host/MOVE_BACKFILL.tsv`, 8/8 `verdict=ok`, all six checks yes). The ninth entry, `work` (7.38 GB), was **not** moved: `/work` does not support POSIX ACLs and the source has them (`rsync -A` fails with `Operation not supported`); its partial `/work` copy was retired to `/work/dwong/_to_delete/work.failed_20261113T235407Z` (no deletion; `raw/evidence_capture_0331.txt`) and the original stays at `/ceph/dwong/work` (Q12). The same treatment was applied to the `zc_host` false-negative copy: `/work/dwong/_to_delete/zc_host.failed_20261113T234708Z`.
- **Verification metric (author-accepted, reviewer-confirmed):** the first entry exposed that `du -sb` counts CephFS directory `st_size`, giving a false byte mismatch; the check now compares file-content bytes, file count, path-normalised per-file SHA-256 manifest, directory count, symlink-list SHA-256 and permission-list SHA-256. The reviewer's confirmation sentence is recorded verbatim in `MOVE_LOG.tsv` and `moves/MOVE_LOG_NOTES.md`. A second refinement excludes the volatile `*/.git/index` cache from the content manifest (git identity still checked by HEAD + porcelain status) after `zc_host` differed only there; all eight backfills are green under it.
- **Deviation, disclosed:** copying uses `nice -n 19 ionice -c2 -n7` (not `-c3`; runbook §1.4 only says "with nice and ionice"); `-c3` gave ~5.3 MB/s on the first entry (2.4 GB copied in ~7.5 min, from the observed progress), too slow for the window. `work`'s ACL failure is recorded, not worked around: no deletion, no overwrite.
## 3. Pool facts (§2) — headline numbers

Full detail in `POOL_FACTS.md`. Measured 23:39–23:44 CET:

- `condor_version` **25.0.12** (2026-07-07), platform x86_64_AlmaLinux8.
- `condor_status -total`: **1105 slots, 1051 claimed, 22 unclaimed, 31 drain** — the pool is heavily busy; queue waits are the dominant measurement tonight.
- Both collectors answer: `c03-001-140.gridka.de` (TOpAS/GridKa) and `f03-001-140-e.gridka.de` (ETP + NEMO2). The schedd is `deepthought.etp.kit.edu`.
- GPU device strings measured and matched by the probes: `Tesla V100S-PCIE-32GB` (TOpAS), `NVIDIA A100-PCIE-40GB` (TOpAS), `NVIDIA L40S` (NEMO2), `NVIDIA H200` (NEMO2, drained), `NVIDIA GeForce GTX TITAN X` (deepthought), `NVIDIA L40S` (deepthought2).
- `CloudSite` measured: local ETP (`deepthought`) = `portal`; ETP worker `ms02` = `schnepf`; NEMO2 = `BwForCluster-Nemo2` (the P6/P7 requirement term is therefore valid).
- `ProvidesETPResources` exists and is true on **323** slots; **`HasDocker` is true on 315 slots, all of them also ETP** (`raw/evidence_capture_0331.txt`); `HasSingularity` is true on 1094 slots (counts are dynamic snapshots: 315 docker / 323 ETP at 03:30 CET, 318 / 326 at 03:38 — `raw/m1_m2_checks.txt`). On the NEMO2 GPU slots `HasDocker` is **undefined** and `HasSingularity=true`.
- Accounting: the author has **no completed past HTCondor jobs** (`condor_history dwong` empty; userprio shows 0 weighted hours, last usage "20770+22:4"). One **job of the same account, not ours**, was visible at 23:40 CET: cluster 759618 (`/work/dwong/r2_batch/tiny/exe.sh`, `AcctGroup=cms`, `AccountingGroup=cms.dwong`); it later left the queue as REMOVED (status 3, never executed) and was never touched. Several further `r2_batch` clusters appeared during the night from the same other session (759626–759636); none was touched. The probes were submitted **without** `accounting_group` per §0.4 A; none was held for that reason. This job is never touched.
- `/ceph/srv` exists but has **no `dwong` directory**; `/work`, `/home` are 1 %/27 % used.

## 4. Docker/image (§3) — gate result

`docker info` on deepthought: **cannot connect to the Docker daemon** (twice, 23:39 and 23:41 CET). The account is in the `docker` group, and `apptainer`/`singularity` exist, but the errata's A3 gate forbids:
- reading `~/.docker/config.json` (credential file), so no registry-login check is possible;
- `docker login` (never);
- inventing a registry/namespace;
and the `docker save` archive is not a pullable image reference for HTCondor's docker universe. Therefore **no image was built and I1–I4 were not submitted tonight**; the registry/namespace and the daemon question are in the question list (Q2). This is the explicit fallback the pre-execution review required, not a late discovery.

## 5. Probe wave (§4) — results so far

All seven JDLs were reviewed and accepted before submission; M1/M2 were then measured (see §3) and support them.

| Probe | Class | Cluster | State | Wait | Run | Site / host | Notes |
|---|---|---|---|---|---|---|---|
| P1 | local CPU, docker, 1 CPU / 2 GB | 759619 | **COMPLETED exit 0** | 73 s | 1 s | `schnepf` / `slot1_21@ms02.etp.kit.edu` | /work and /ceph mounted; `/ceph/srv` also present; `/cvmfs` empty; no `/scratch`; `nproc=1`; Xeon Silver 4214 |
| P2 | local CPU, docker, 8 CPU / 16 GB | 759620 | **IDLE (capacity)** | — | — | — | 0 willing now, **5 slots would match if drained**; pool at 1051/1105 claimed |
| P3 | "remote" CPU, docker, 1 CPU | 759621 | **COMPLETED exit 0** | 7 s | 1 s | `schnepf` / `slot1_21@ms02.etp.kit.edu` | `+RemoteJob=True` still matched local ETP; remote-CPU class NOT measured (best effort, recorded) |
| P4 | TOpAS A100 | 759622 | **IDLE (A100 capacity)** | — | — | — | local-schedd analysis: 0 A100 match; against the `c03`/TOpAS collector: 3 A100 slots, all **Drained**, `[10]&&[11]` 0, "2 would match if drained"; the A100 parent (`slot1@c03-001-167`) carries `TotalSlotGPUs=8` but `GPUs=0`, `Cpus=0`. Kept queued per the author (Q9); the host_facts A/B A100-slot ambiguity is recorded (probe review M5) |
| P5 | TOpAS V100S | 759623 | **COMPLETED exit 0** | **212 s** | 2 s | `topas` / `slot4_1@c03-001-159.gridka.de` | TOpAS reachable by flocking; remote: `/work`,`/ceph`,`/ceph/srv` MISSING (expected), `/tmp` 5.2 T; `CUDA_VISIBLE_DEVICES=GPU-…` UUID, `NVIDIA_VISIBLE_DEVICES=void` |
| P6 | NEMO2 L40S | 759624 | **IDLE (structural no-match: no Docker)** | — | — | — | measured `raw/evidence_capture_0331.txt`: at 03:30 CET the NEMO2 view had 6 L40S slots (4 Unclaimed, 2 Drained) and 3 H200 slots, all with `HasDocker=undefined`, `HasSingularity=true`, `CloudSite=BwForCluster-Nemo2`. P6 analysis: `[2]` (CloudSite∧device) 6, `[5]` HasDocker 6, `[6]=[2]&&[5]` **0** (`raw/p6_analyze.txt`). The docker-universe design cannot run there (Q10) |
| P7 | NEMO2 H200 | 759625 | **IDLE (no eligible slot)** | — | — | — | the H200 slots moved Idle→Drained between 23:38 and 23:40 CET and all were Drained at analysis; no match |

`queue_times.tsv` (snapshots: `raw/queue_times_snapshot1.tsv` for wave 1, `raw/queue_times_current.tsv` for waves 1–2) carries submit/execute/end, wait, run, site, host, GPU, evictions, holds and exit per probe.

**Author guidance received at ~00:35 CET and followed:** P4/P5 are **not** withdrawn; GPU jobs are matched through the TOpAS pool, so a 0-match in the local schedd view can be normal — the tutorial-form re-analysis (`condor_q -better-analyze -pool f03-001-140-e.gridka.de`) was run and recorded (`raw/pool_analyze_p4_20261114.txt`; against `c03` the A100 condition matched 3 drained slots, `[10]&&[11]` 0, "2 would match if drained"), and the jobs stay queued (P5 had already completed; P4 is the one still queued). NEMO2 is Singularity-only and the image→SIF-on-`/work` route is question Q10; **no new job types were submitted**. Local docker/ETP slot counts (docker∧ETP=315, unclaimed docker 5 / ETP 13 at 00:35) are recorded for tomorrow's local-CPU container decision (Q11). The +3 h sample (P1, P3, P4, P6 unchanged) is planned around 02:50 CET; the +6 h wave cannot fit before the 05:30 stop (errata A4) and is dropped.

**Per-class queue-time statistics (samples to date; single-night probe, not a benchmark):**

| resource class | samples | waits (s) | n | median (s) | range (s) |
|---|---|---:|---:|---:|---|
| local CPU 1 core, docker (ETP workers) | P1, P3, P1w2, P3w2 | 73, 7, 21, 21 | 4 | **21** | **7–73** |
| local CPU 8 cores, docker | P2 | still queued | 0 | — | — |
| remote CPU (best effort) | P3, P3w2 | 7, 21 (both matched local ETP) | 2 | 14 | 7–21 |
| TOpAS V100S | P5 | 212 | 1 | 212 | — |
| TOpAS A100 | P4 | queued (capacity) | 0 | — | — |
| NEMO2 L40S / H200 | P6, P7 | no match (no Docker / drained) | 0 | — | — |

The four local-1-core samples come from waves 1 and 2; the 8-core, A100, L40S and H200 classes have no measured wait.

**Queue-time summary (wave 1, single samples):**

| class | probe | wait | outcome |
|---|---|---:|---|
| local CPU 1 core, docker | P1 | **73 s** | completed (host `ms02`, `CloudSite=schnepf`) |
| local CPU 1 core, docker, **wave 2** | P1w2 | **21 s** | completed on `mdm1.etp.kit.edu` (`CloudSite=mdm`), run 2 s |
| remote CPU (best effort), **wave 2** | P3w2 | **21 s** | completed on `ms04.etp.kit.edu` (`schnepf`), run 1 s |
| local CPU 8 cores, docker | P2 | **still idle after ~3 h 40 min at 03:31 CET** | `raw/p2_analyze.txt`: 0 willing, 5 would match if drained — capacity wait |
| remote CPU (best effort) | P3 | **7 s** | completed **locally**; remote-CPU class not measured |
| TOpAS A100 | P4 | **idle** | A100 node fully allocated; kept queued per author (re-analysis with `-pool` recorded) |
| TOpAS V100S | P5 | **212 s** | completed; TOpAS flocking works |
| NEMO2 L40S | P6 | **no match** | `HasDocker=undefined` on NEMO2 slots (Singularity only) — design blocker, Q10 |
| NEMO2 H200 | P7 | **no match** | only H200 slot Drained at submit/analysis time |

Wave 2 (**+2 h 52 m** after wave 1) ran `P1`/`P3` unchanged as `P1w2`/`P3w2` (distinct output/log names): both completed with **21 s** submit→execute on `mdm1` and `ms04` (P3's wave-2 wait is 21 s vs 7 s in wave 1 — slower, within a low-load night sample anyway). P4/P6 were **not** resubmitted as duplicates: the author instructed that P4/P5 stay queued, so the original P4/P6 entries are the continuous queue samples (this is a deliberate deviation from runbook §4.3's "resubmit P1,P3,P4,P6", labelled here). **A +6 h sample (`P1w3`/`P3w3`) is planned at ~05:52 CET** and is possible only because the author moved the hard stop to 09:30; the report records its outcome if it runs and says so if it does not.

---

## 6. W2 side task (§5) — STOP, difference found

The start-message line W2 was in scope. Read-only run from a clean detached checkout of `origin/mac-w2-budget-20261109` (`0b62fb03df5480faf558cddd8f715cbb5310416e`), with the sweep's Python environment (`/ceph/dwong/r1_prepare_20261025/venv`, Python 3.13.15, `import r1.c3.features` + `r1.c3.analysis_guard` OK), `--runs-total 20` (top-level `"runs": 20` of `r1/scripts/configs/c3_sweep_deepthought.json`, SHA-256 `2fa891f4…`), over the **288** sweep-1 ledgers (`C3_sweep_append_only_summary_20261027T154834Z`: 144; `C3_sweep_none_20261027T224356Z`: 144).

**Result: `STOP_DIFFERENCE`, exit 3 — 14 of 288 ledgers differ**, all on `precheck_rejection` rows (53 rows total): e.g. `digits_mlp__s114` 20 differing rows / 13 precheck rejections, `digits_mlp__s224` 17/9, `digits_mlp__s194` and `digits_mlp__s264` 15 each. The other 274 ledgers are `IDENTICAL`; no ledger exceeds the 20-run cap. This is exactly the difference `docs/r1/reports/W2_BUDGET_FIELDS_20261109.md` on `origin/mac-w2-budget-20261109` predicted for sweep tables containing precheck rejections — a real difference between the trial-index and worker-run definitions, **not a bug**. **Per the start message: STOPPED; nothing adopted, recomputed, edited or resubmitted; handed to the author (Q1).** Summary: `raw/w2/w2_check.json`; ledger list: `raw/w2/ledgers.txt`.

## 7. What works, what does not

**Works tonight:** HTCondor submission from `deepthought.etp.kit.edu` (condor 25.0.12); docker universe on the **ETP worker fleet** (`ms*`, `mdm*`; 315 docker slots, all ETP); flocking to **TOpAS** (`P5` ran on `c03-001-159`, wait 212 s, exit 0); ETP workers have `/work`, `/ceph`, `/ceph/srv`, `/cvmfs` (empty) and 718 G `/tmp`; TOpAS has 4.7 T job `/tmp` but no ETP mounts; the event log gives clean submit/execute/terminate times; the move protocol ran end-to-end (8 entries, backfill 8/8 green) with **no deletion**.
**Does not work / blocked:** docker daemon on deepthought (no image build; I1–I4 deferred); **NEMO2 GPU execution for docker-universe jobs** (Singularity only — measured design blocker, not queue); A100 capacity (node fully allocated); H200 slot drained; 8-core local docker capacity (P2 queued); `/ceph/srv/dwong` absent; `/work` cannot preserve POSIX ACLs (Q12).
**Not measured:** remote-CPU queue class (P3 matched locally), 8-core/A100/L40S/H200 queue waits, image runtime behaviour, and the +6 h sample.

**Recommendation per Paper B workload:**
- **C3 T0 audits (CPU):** viable on the ETP worker class (P1/P3 ran in seconds) with `/ceph`+`/work` mounted; the 8-core class needs a capacity window; no image needed for a plain-venv port.
- **Track P training:** **not measured** — the 8-core class never ran (P2 still queued), so even data-prep throughput on that class is unmeasured; the 1-core ETP worker ran fine but is not the intended shape. Training needs a TOpAS A100 window, or the NEMO2 route with a Singularity/SIF job design (Q10).
- **T1 GPU labels:** TOpAS V100S is reachable and ran ~3.5 min submit→end; A100 only when the node frees. NEMO2 L40S/H200 are unusable with the current docker design. GPU use stayed far below the 6 GPU-h cap (P5 used 2 s of GPU time).
- **X.7 (main proposer):** the pinned GGUF is on `/ceph/dwong/models` and its SHA-256 was verified tonight as `509287f7…4d3c` (matches the pin; transcript `raw/gguf_sha256.txt`); it is **not** on `/ceph/srv/dwong`, so loading it on TOpAS needs a transfer route (xrootd endpoint unverified, Q4) or a SIF/`/work` path (Q10).

## 8. Delivery

Committed on `htcondor-prep-20261114` (from `origin/docs/runbooks-14nov` @ `69b3576b`): the runbook review + errata + the accepted post-errata re-check; `POOL_FACTS.md`, `MOVE_PLAN.md` (revision 2 + R1/R2 + the author's metric change), `pinned_paths.txt`; `raw/` inventory, per-entry stats, host facts, pool analysis, queue-times snapshots; probe JDLs/probe.sh/dry-runs; W2 summary; move scripts + `MOVE_LOG.tsv` + `MOVE_LOG_NOTES.md` + `MOVE_BACKFILL.tsv`; this report; the question list. The branch is pushed to `origin` as `origin/htcondor-prep-20261114` (push verified with `git push`; if the final push fails, a bundle + `READY.txt` is written under `~/Documents/agent_paper_B/Claude outputs/`).

## 9. Review status

- Runbook review: red first (NOT ACCEPTED: 2 BLOCKING + 5 MAJOR + 17 MINOR/NIT), errata applied, **ACCEPTED** by the same reviewer after re-check.
- Probe JDL unit: **ACCEPTED** (0 BLOCKING/MAJOR; M1/M2 pre-submission checks run and recorded).
- Move plan: NOT ACCEPTED (5 MAJOR) -> revision 2 -> **ACCEPTED**; R1/R2 applied; the author's verification-metric change confirmed in one sentence by the same reviewer.
- This report: submitted to a **fresh reviewer** before the end of the window (runbook §6); its verdict and any fixes are recorded in `docs/r1/reviews/HTCONDOR_PREP_REPORT_REVIEW_20261114.md`.

---

## 10. Handover summary (what is left for tomorrow)

1. **W2 decision (Q1):** the sweep-1 tables split cleanly: 274 ledgers are pure exec-all (`IDENTICAL`), 14 campaigns contain `precheck_rejection` rows and differ under the worker-run definition. Nothing was adopted tonight. Author decides (a) split the tables by definition, (b) restrict W2 to the synthetic/golden evidence, or (c) a new rule.
2. **Image (Q2/Q10):** build it when the deepthought docker daemon is reachable (or have the author name a registry/namespace); convert the result to an Apptainer SIF under `/work`/`/ceph` for NEMO2, and define the per-site docker-vs-Singularity rule. Until then I1–I4 stay unexecuted.
3. **GPU measurements:** TOpAS works by flocking (V100S measured 212 s; A100 blocked by node occupancy). NEMO2 is Singularity-only. P4/P7 remain queued; P6 is structurally unable to match. The next window should either use a Singularity JDL for NEMO2 (new reviewed unit) or drop NEMO2 from the probe set.
4. **Local CPU:** docker+ETP = 315 slots, unclaimed 5 at 00:35; the 8-core class waits for a drain window; P2's wait is the measurement. Local CPU work (C3 audits) is viable without an image.
5. **Moves (Q12):** 8 entries moved and backfilled (12.3 GB); `work` stayed on `/ceph` because `/work` cannot hold POSIX ACLs. The author decides whether to retry `work` with `--no-acls` and whether ACL preservation matters for the other sessions.
6. **`/ceph/srv/dwong`** does not exist; if the model path on TOpAS is wanted, place the pinned GGUF there or confirm the xrootd endpoint (Q4). Its sha256 on `/ceph/dwong/models` was verified tonight (`509287f7…4d3c`).
7. **Nothing was deleted anywhere.** Retired originals live in `/ceph/dwong/_to_delete/*.moved_20261114` and the two failed copies in `/work/dwong/_to_delete/`; the old paths are symlinks into `/work`.

**Final probe state at this report:** P1/P3/P5/P1w2/P3w2 completed with exit 0; P2/P4/P6/P7 still queued (P4/P5 are not withdrawn, per the author); no `condor_rm`/`condor_hold` was issued by this agent; the only job-level commands used were `condor_submit`, `condor_q`, `condor_history` on the account.
