# ETP HTCondor preparation — night of 13/14 Nov 2026 (report, draft)

**Phase:** HTCondor preparation (runbook `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` + errata `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md`). **AI-assisted** (DeepSeek Harness agent, "cluster agent" role). **Reported to the author in Chinese.**
**Window:** started 23:37 CET 13 Nov; VPN-dependent work must stop by **05:30 CET** 14 Nov (runbook §6). **Status at this draft:** probes submitted and being monitored; W2 STOPPED on a difference; image build impossible (docker gate); moves pending the reviewed plan.
**Evidence:** `docs/r1/reports/htcondor_prep_20261114/` (raw host facts, inventory, stats, pool facts, move plan, probe outputs, W2 summary); reviews in `docs/r1/reviews/HTCONDOR_*_20261114.md`.

---

## 1. Goal and what was actually possible

| Night goal (runbook) | Result |
|---|---|
| 1. Move small-file dirs `/ceph/dwong` -> `/work/dwong` safely | **Plan only, not executed at this draft.** Inventory + per-entry statistics are complete; `MOVE_PLAN.md` revision 2 was submitted to the fresh reviewer after a first NOT ACCEPTED round (5 MAJOR, all plan-text classification/coverage/protocol issues, no BLOCKING). Moves start only after the plan is accepted, one entry at a time, and stop being started at 03:30 CET |
| 2. Build a pinned container image | **Not possible tonight.** `docker info` on deepthought fails (daemon unreachable) — the errata's docker gate (A3) stops §3 before the build; no `docker login`, no credential read, no registry guess. `apptainer`/`singularity` are present. I1–I4 were therefore not submitted |
| 3. Try it on the batch system with small probe jobs | **Partially done:** the official-image probe wave P1–P7 was submitted (reviewed JDLs); P1, P3 and **P5** ran and exited 0; P2 queues on capacity; P4/P6/P7 have structural no-match (below) |
| 4. Record queue times for every resource class | **Partial:** local CPU classes measured (P1, P3), **TOpAS V100S measured (P5, wait 212 s)**; 8-core local, A100, NEMO2 L40S and NEMO2 H200 not measured tonight (capacity / no-docker / drained) |

**Review discipline kept:** the runbook itself was reviewed by a fresh reviewer (NOT ACCEPTED round 1 -> errata -> **ACCEPTED**); the probe wave was reviewed before submission (**ACCEPTED**, with M1/M2 pre-submission checks, both of which were then measured and support the JDLs); the move plan is in its second review round.

## 2. Inventory and move plan (§1)

- 70 top-level entries under `/ceph/dwong` inventoried: **560.3 GB, 385,744 files** (full top-level list, per-entry bytes/files and file-size percentiles in `raw/inventory.tsv` and `raw/entry_stats.tsv`).
- `/work` at inventory time: 1.4 T size, 385 G used, **1.1 T free (27 % used)**; `/ceph` 1.4 P with 346 T free (75 % used). `quota -s`/`quota -Q` print **no output** (no measurable per-user quota), so the errata's 15 % floor is computed against the filesystem capacity (≈210 G) — conservative.
- `pinned_paths.txt`: 213 lines from a read-only `git grep '/ceph/dwong'` across `docs/runbooks-14nov`, `origin/mac-int-20261107`, `origin/trackS-ops-20261030`, `origin/mac-b1-20261107`, `origin/dt-sweep1-20261026`. It pins `r1_batch1_*`, `agent_paper_B`, `opt` (llama.cpp build), `models` (the pinned GGUF), and `autoresearch_harness` paths.
- `MOVE_PLAN.md` revision 2: **9 entries to move (19.7 GB)**, 61 skipped with reasons (pinned/evidence/venv/large-file/unreadable/tiny/regular-file). The first review removed `hf_cache` (19.1 GB blob cache), the seven single-file entries, `ceph_lwindett` (root-only), and six evidence-boundary trees (conservative), and required the in-use check, disk gate, order/cut-off, and `_to_delete`/collision guards that revision 2 now has.
- **Moves (review trail: NOT ACCEPTED -> revision 2 -> ACCEPTED from the same reviewer, R1/R2 inline fixes, then the author's 14 Nov verification change confirmed in one sentence by the same reviewer).** Result: **8 of 9 entries moved, 12.2 GB**, each by copy -> verify -> re-check in-use -> retire into `_to_delete` -> symlink back; the old paths work through the symlinks. Every moved entry was re-verified after the fact against its retired original (`moves/from_host/MOVE_BACKFILL.tsv`, 8/8 `verdict=ok`, all six checks yes). The ninth entry, `work` (7.38 GB), was **not** moved: `/work` does not support POSIX ACLs and the source has them (`rsync -A` fails with `Operation not supported`); its partial `/work` copy was retired to `/work/dwong/_to_delete/` (no deletion) and the original stays at `/ceph/dwong/work` (Q12).
- **Verification metric (author-accepted, reviewer-confirmed):** the first entry exposed that `du -sb` counts CephFS directory `st_size`, giving a false byte mismatch; the check now compares file-content bytes, file count, path-normalised per-file SHA-256 manifest, directory count, symlink-list SHA-256 and permission-list SHA-256. The reviewer's confirmation sentence is recorded verbatim in `MOVE_LOG.tsv` and `moves/MOVE_LOG_NOTES.md`. A second refinement excludes the volatile `*/.git/index` cache from the content manifest (git identity still checked by HEAD + porcelain status) after `zc_host` differed only there; all eight backfills are green under it.
- **Deviation, disclosed:** copying uses `nice -n 19 ionice -c2 -n7` (not `-c3`; runbook §1.4 only says "with nice and ionice"); `-c3` measured ~5 MB/s. `work`'s ACL failure is recorded, not worked around: no deletion, no overwrite.
## 3. Pool facts (§2) — headline numbers

Full detail in `POOL_FACTS.md`. Measured 23:39–23:44 CET:

- `condor_version` **25.0.12** (2026-07-07), platform x86_64_AlmaLinux8.
- `condor_status -total`: **1105 slots, 1051 claimed, 22 unclaimed, 31 drain** — the pool is heavily busy; queue waits are the dominant measurement tonight.
- Both collectors answer: `c03-001-140.gridka.de` (TOpAS/GridKa) and `f03-001-140-e.gridka.de` (ETP + NEMO2). The schedd is `deepthought.etp.kit.edu`.
- GPU device strings measured and matched by the probes: `Tesla V100S-PCIE-32GB` (TOpAS), `NVIDIA A100-PCIE-40GB` (TOpAS), `NVIDIA L40S` (NEMO2), `NVIDIA H200` (NEMO2, drained), `NVIDIA GeForce GTX TITAN X` (deepthought), `NVIDIA L40S` (deepthought2).
- `CloudSite` measured: local ETP (`deepthought`) = `portal`; ETP worker `ms02` = `schnepf`; NEMO2 = `BwForCluster-Nemo2` (the P6/P7 requirement term is therefore valid).
- `ProvidesETPResources` exists and is true on the local ETP slots; **`HasDocker` is true on 324 slots** (all also ETP), and **undefined on the NEMO2 GPU slots** (they advertise `HasSingularity=true`).
- Accounting: the author has **no completed past HTCondor jobs** (`condor_history dwong` empty; userprio shows 0 weighted hours, last usage "20770+22:4"). One **idle job of the same account, not ours**, is visible: cluster 759618 (`/work/dwong/r2_batch/tiny/exe.sh`), `AcctGroup=cms`, `AccountingGroup=cms.dwong`. The probes were submitted **without** `accounting_group` per §0.4 A; none was held for that reason. This job is never touched.
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
| P1 | local CPU, docker, 1 CPU / 2 GB | 759619 | **COMPLETED exit 0** | 73 s | 1–3 s | `schnepf` / `ms02.etp.kit.edu` (slot1_21) | /work and /ceph mounted; `/ceph/srv` also present; `/cvmfs` empty; no `/scratch`; `nproc=1`; Xeon Silver 4214 |
| P2 | local CPU, docker, 8 CPU / 16 GB | 759620 | **IDLE (capacity)** | — | — | — | 0 willing now, **5 slots would match if drained**; pool at 1051/1105 claimed |
| P3 | "remote" CPU, docker, 1 CPU | 759621 | **COMPLETED exit 0** | 7 s | 1 s | `schnepf` / `ms02.etp.kit.edu` | `+RemoteJob=True` still matched local ETP; remote-CPU class NOT measured (best effort, recorded) |
| P4 | TOpAS A100 | 759622 | **IDLE (A100 node fully allocated)** | — | — | — | A100 parent slot `TotalSlotGPUs=8` but `GPUs=0`, `Cpus=0`, all children Claimed/Preempting; becomes runnable when the node frees |
| P5 | TOpAS V100S | 759623 | **COMPLETED exit 0** | **212 s** | 2 s | `topas` / `c03-001-159.gridka.de` (slot4_1) | TOpAS reachable by flocking; remote: `/work`,`/ceph`,`/ceph/srv` MISSING (expected), `/tmp` 5.2 T; `CUDA_VISIBLE_DEVICES=GPU-…` UUID, `NVIDIA_VISIBLE_DEVICES=void` |
| P6 | NEMO2 L40S | 759624 | **IDLE (structural no-match)** | — | — | — | CloudSite+device matched 6 L40S slots, but `TARGET.HasDocker` matched **0**: NEMO2 slots have `HasDocker=undefined`, `HasSingularity=true`. The runbook's docker-universe design cannot run there |
| P7 | NEMO2 H200 | 759625 | **IDLE (no eligible slot)** | — | — | — | the only visible H200 slot `g4401` is Drained; no match |

`queue_times.tsv` (raw at `raw/queue_times_snapshot1.tsv`, updated on the host) carries submit/execute/end, wait, run, site, host, GPU, evictions, holds and exit per probe.

**Author guidance received at ~00:35 CET and followed:** P4/P5 are **not** withdrawn; GPU jobs are matched through the TOpAS pool, so a 0-match in the local schedd view can be normal — the tutorial-form re-analysis (`condor_q -better-analyze -pool f03-001-140-e.gridka.de`) was run and recorded (`raw/pool_analyze_p4_20261114.txt`; against `c03` the A100 condition matched 3 drained slots, `[10]&&[11]` 0, "2 would match if drained"), and the jobs stay queued. NEMO2 is Singularity-only and the image→SIF-on-`/work` route is question Q10; **no new job types were submitted**. Local docker/ETP slot counts (docker∧ETP=315, unclaimed docker 5 / ETP 13 at 00:35) are recorded for tomorrow's local-CPU container decision (Q11). The +3 h sample (P1, P3, P4, P6 unchanged) is planned around 02:50 CET; the +6 h wave cannot fit before the 05:30 stop (errata A4) and is dropped.

**Resource-class medians so far:** local CPU 1-core wait **73 s** (P1; P3 7 s for the same class at a better moment); TOpAS V100S **212 s**; 8-core local ≥ (still queued); A100, NEMO2 L40S, H200 not measured. Single samples only — this is a queue-time probe, not a benchmark.

## 6. W2 side task (§5) — STOP, difference found

The start-message line W2 was in scope. Read-only run from a clean detached checkout of `origin/mac-w2-budget-20261109` (`0b62fb03`) with the sweep's Python env (3.13.15), `--runs-total 20` (sweep config SHA `2fa891f4…`), over the 288 sweep-1 ledgers (144 append-only + 144 none).

**Result: `STOP_DIFFERENCE`, exit 3 — 14 of 288 ledgers differ, all because of `precheck_rejection` rows (53 rows total).** The 274 pure exec-all ledgers are `IDENTICAL`; no `worker_runs_total` exceeds the 20-run cap. This is the difference `reports/W2_BUDGET_FIELDS_20261109.md` predicted for tables with precheck rejections. **Per the start message: STOPPED; nothing adopted, recomputed, edited or resubmitted; handed to the author.** Full JSON: `raw/w2/w2_check.json`. Question Q1.

## 7. What works, what does not

**Works tonight:** ETP schedd submission; docker universe on the ETP worker fleet (`ms*`, `mdm*`); `+RemoteJob` flocking to TOpAS (V100S ran); ETP workers have `/work`, `/ceph`, `/ceph/srv`, `/cvmfs` (empty) and 718 G `/tmp`; TOpAS has 4.7 T job `/tmp` but no ETP mounts; the HTCondor event log gives clean wait/run times.
**Does not work / blocked:** docker on deepthought (daemon); NEMO2 GPU execution for docker-universe jobs (Singularity only); A100 node fully allocated (capacity); H200 slot drained; 8-core local capacity waits; `/ceph/srv/dwong` absent; the image/registry path (Q2).

**Recommendation per Paper B workload (as asked in §6):**
- **C3 T0 audits (CPU):** viable in the *local ETP worker* class (P1/P3 ran in seconds) and the 8-core class needs a capacity window (P2 queued); `/ceph` and `/work` are mounted there, so the data path works. No image is needed for a plain-venv port.
- **Track P training:** unknown tonight — no GPU training probe ran (P4/P6 blocked, no image). The 8-core CPU + 187 GB RAM worker class is fine for data prep; track training needs either a TOpAS A100 window or the NEMO2 route, and the latter requires a non-docker (Singularity) job design.
- **T1 GPU labels:** TOpAS V100S is reachable and ran in ~3.5 min from submit to end; A100 only when the node frees. NEMO2 L40S/H200 cannot be used with the current docker design — a measured blocker, not a queue effect.
- **X.7 (main proposer):** the GGUF is on `/ceph/dwong/models` (pinned, sha verified in the repo) but **not** on `/ceph/srv/dwong`; loading it on TOpAS would need a transfer route (xrootd endpoint unverified, Q4).

## 8. Delivery

Committed on `htcondor-prep-20261114` (from `origin/docs/runbooks-14nov` @ `69b3576b`): runbook reviews, errata, `POOL_FACTS.md`, `MOVE_PLAN.md`, `pinned_paths.txt`, raw inventory/stats/host facts, probe JDLs/`probe.sh`/dry-runs, W2 summary, this report and the question list. If a push is impossible, a bundle and `READY.txt` go under `~/Documents/agent_paper_B/Claude outputs/`.
