# Pool facts — ETP HTCondor, 13/14 Nov 2026 (night of the prep)

**Phase:** HTCondor prep night (runbook `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` §2 + errata). **Read-only** on `deepthought.etp.kit.edu` over SSH from the Mac (KIT VPN). Collected 23:39–23:44 CET, 13 Nov 2026. Raw outputs: `raw/host_facts_A.txt`, `raw/host_facts_B.txt`, `raw/pool_facts_raw.txt`.

**Source of truth caveat.** The official ETP wiki and tutorial GitLab are login-gated from the Mac (see the pre-execution review §3). These facts are measured on the pool itself, which is a stronger source than the wiki for tonight; where the runbook text and a measured fact disagree, the measured fact wins and the discrepancy goes to the question list.

## 1. Version and pool totals

| Item | Value |
|---|---|
| `condor_version` | `$CondorVersion: 25.0.12 2026-07-07 BuildID: 930047 PackageID: 25.0.12-1`; platform `x86_64_AlmaLinux8` |
| `condor_status -total` (23:44 CET) | **1105 slots total: 1051 claimed, 22 unclaimed, 31 drain, 1 owner** — the pool is heavily busy; queue waits are expected to be the dominant unknown the probes measure |
| Collectors that answer | `c03-001-140.gridka.de` (TOpAS/GridKa view) **and** `f03-001-140-e.gridka.de` (ETP + NEMO2 view); the default schedd is `deepthought.etp.kit.edu:9618` |
| Author's priority line | `dwong@etp.kit.edu` — config quota 500 / 1000, **0 weighted hours used, last usage `20770+22:4` (i.e. no recent jobs)**; `condor_history dwong` is empty |
| Author's jobs at collection time | **one IDLE job, cluster 759618, not started by this agent**: `Cmd=/work/dwong/r2_batch/tiny/./exe.sh`, `Iwd=/work/dwong/r2_batch/tiny`, `AcctGroup=cms`, `AccountingGroup=cms.dwong`, QDate 23:40 CET. It belongs to another session of the same account; it is not ours and is not touched |
| Accounting-group evidence | the only group the account currently shows in use is `cms.dwong` (from job 759618); no *past* job by the author was found, so §0.4 A's "use the group they used" has no history to follow. Probes start without `accounting_group` (runbook §0.4 A first branch); if the pool holds/rejects for that reason, the errata A7-F16 fallback is the documented `belle`, not `cms.higgs`, and the choice is recorded |

## 2. GPU slots as reported (measured attributes)

| Site / slot | Device | Driver | GPUs in slot | State at 23:44 |
|---|---|---|---|---|
| `deepthought.etp.kit.edu` | NVIDIA GeForce GTX TITAN X | 12.0 | 2 | Unclaimed |
| `deepthought2.etp.kit.edu` | NVIDIA L40S | 12.8 | 1 | Unclaimed |
| `nemo2_gpu-*@g3606.nemo.privat` (×3 visible) | NVIDIA L40S | 13.4 | 1 each | Unclaimed |
| `nemo2_gpu-71f4f514cf@g4401.nemo.privat` | NVIDIA H200 | 13.4 | 1 | Drained at 23:40; previously Idle |
| `c03-001-159.gridka.de` slots 1–7 | Tesla V100S-PCIE-32GB | 13.0 | 7–8 each (partitionable) | 7 Unclaimed partitionable slots; each has claimed children |
| `c03-001-167.gridka.de` | NVIDIA A100-PCIE-40GB | 13.3 | 8 (partitionable) | Unclaimed |
| `c03-001-175/179.gridka.de` | (partitionable, GPUs 0 in the -af:t listing) | — | 0 | — |

`CUDADriverVersion` is `undefined` on these slots; `GPUs_DriverVersion` is populated. **The device strings in the runbook/review are confirmed by measurement:** `NVIDIA A100-PCIE-40GB`, `Tesla V100S-PCIE-32GB`, `NVIDIA L40S`, `NVIDIA H200`. The V100S count question (16 vs 24) is not settled by the listing (partitionable slots report per-node GPUs, not a site total) — question only.

## 3. Storage, quota, scratch, tools

| Item | Value |
|---|---|
| `/work` | 1.4 T filesystem, 385 G used, **1.1 T available (27 % used)** — the author's tripled quota is not visible as a separate number |
| `quota -s` / `quota -Q` | the binary exists but prints **no output**; no measurable per-user quota. The errata's 15 % floor is therefore computed against the filesystem capacity (15 % of 1.4 T ≈ **210 G**), which is strictly conservative |
| `/ceph` | 1.4 P filesystem, 986 T used, **346 T available (75 % used)** — above the 15 % floor |
| `/home` | 100 G, 202 M used |
| `/ceph/srv` | exists (world-writable root), **no `/ceph/srv/dwong` directory** → the I3 model-load path via `/ceph/srv` is unavailable (I3–I4 are deferred anyway, errata A3) |
| Scratch | `SCRATCH`/`TMPDIR` unset; `/scratch` does not exist; `/tmp` is on the 442 G root filesystem (127 G avail) |
| `docker` | `/usr/bin/docker` present and the user is in group `docker`, but **`docker info` fails: cannot connect to the daemon** → §3's docker gate fails; no image build tonight (errata A3); `apptainer` and `singularity` are present |
| Python | default `python3` = anaconda3 3.12.2; the sweep environment `venv` at `/ceph/dwong/r1_prepare_20261025/venv` is **Python 3.13.15** and imports `r1.c3.features` / `r1.c3.analysis_guard` from a paper checkout (used for W2) |
| Paper clone | `/ceph/dwong/agent_paper_B` is a git repo (origin `git@github.com:dowlingwong/Agent_paper_B.git`), branch `dt-sweep1-20261026` checked out, one untracked file, and it carries `origin/mac-w2-budget-20261109` = `0b62fb03` |
| Sweep-1 outputs | batch `r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B/results/r1/pilot/`: `C3_sweep_append_only_summary_20261027T154834Z` (144 roots) and `C3_sweep_none_20261027T224356Z` (144 roots) — **W2 read 288 ledgers there** |
| Other active sessions on deepthought | a `codex app-server` (17 days), a VS Code server with terminals whose cwd is `/ceph/dwong`; both are not ours and are not touched. They are why the in-use check must be repeated before every move |
| In-use process check | processes of `dwong` whose cwd is under `/ceph/dwong`: the VS Code terminal shells (pids 1791926, 1800582 at collection). No process was seen opening a moved entry's files at collection; the check is repeated per move (§1.4) |

## 4. What tonight's probes are trying to measure (so the numbers are interpretable)

The pool is at 1051/1105 claimed. The probe wave is the only measurement of **queue wait per resource class**; expectations are therefore explicitly not guessed. Queue waits are recorded from the job event log (000/001/005/004/012) as in §4.2, with the +3 h resample (P1w2/P3w2) already run at 02:43 CET; the +6 h sample (P1w3/P3w3) is planned at ~05:52 CET under the author's 09:30 extension and its outcome is recorded when it runs (or recorded as not run).

## 5. Matching facts measured by the real probe submissions (23:51–00:05 CET)

These were measured by submitting P1–P7 (accepted unit, `reviews/HTCONDOR_PROBES_JDL_REVIEW_20261114.md`) and reading `condor_q -better-analyze` / `condor_history`; they supersede the pre-submission assumptions where they differ. Raw evidence is in `raw/` beside this file and in the probe directory on deepthought.

| Probe | Class | Result | Measured reason |
|---|---|---|---|
| P1 | local CPU, docker, 1 CPU / 2 GB | **COMPLETED, exit 0**, host `ms02.etp.kit.edu`, run 1 s, wait 73 s | 1 matching slot willing; the ETP worker nodes (`ms*`, `mdm*`) are docker-capable (`HasDocker=true`) and mount /work and /ceph |
| P2 | local CPU, docker, 8 CPU / 16 GB | **IDLE (capacity)** | 0 slots match now, 5 would match if drained — the pool is at 1051/1105 claimed; this is a queue measurement, not a defect |
| P3 | "remote" CPU, docker, 1 CPU | **COMPLETED, exit 0**, also on `ms02.etp.kit.edu`, wait 7 s, run 1 s | `+RemoteJob=True` did **not** force a remote site; it matched a local ETP worker. Best-effort class (errata A7-F12): the remote-CPU queue class is **not measured** tonight; site recorded as `schnepf` (the `MachineAttrCloudSite0` of `ms02`) |
| P4 | TOpAS A100 | **IDLE, no match (capacity)** | P5 proves TOpAS IS reachable, so P4's failure is not the pool route: the A100 slot `slot1@c03-001-167.gridka.de` advertises `TotalSlotGPUs=8` but `GPUs=0`, `Cpus=0` with all children Claimed/Preempting — the A100 node is fully allocated and the partitionable parent has no free GPUs/CPUs to provision. It becomes runnable only when the node frees resources |
| P5 | TOpAS V100S | **COMPLETED, exit 0**, host `dwong-759623.0-c03-001-159.gridka.de` (site `topas`, slot4_1@c03-001-159), wait 212 s, run 2 s | TOpAS **is reachable by flocking**: the pool match found a free V100S slot on `c03-001-159` (GridKa). Job ran in docker (`NVIDIA_VISIBLE_DEVICES=void`, `CUDA_VISIBLE_DEVICES=GPU-918aeb0c-…` UUID); `/work`, `/ceph`, `/ceph/srv` are MISSING remotely (expected for `+RemoteJob`), `/tmp` 5.2 T |
| P6 | NEMO2 L40S | **IDLE, no match** | measured at 03:30 CET: 6 L40S slots (4 Unclaimed, 2 Drained) + **4 H200 slots (1 Unclaimed, 3 Drained)**, all `HasDocker=undefined`, `HasSingularity=true`, `CloudSite=BwForCluster-Nemo2`. P6 analysis (`raw/p6_analyze.txt`): `[2]` 6, `[5]` 6, `[6]=[2]&&[5]` **0** — a docker-universe job cannot run there |
| P7 | NEMO2 H200 | **IDLE, no match (structural: no Docker)** | same structural blocker as P6 (`HasDocker=undefined`, `HasSingularity=true`); H200 state varied: 1 Unclaimed Idle 23:38 → Drained 23:40 → 4 slots (1 Unclaimed, 3 Drained) at 03:30 — none eligible for a docker-universe job |

Additional measured facts:

- `TARGET.ProvidesETPResources` **exists and is true** on the local ETP slots (`bms1/2/3`, `deepthought`, `deepthought2`, `mdm*`, `ms*`), and `HasDocker=true` on **315** slots (all of them also ETP; `ProvidesETPResources` on 323, `HasSingularity` on 1094; from `raw/pool_analyze_p4_20261114.txt`, 00:35 CET; the 03:32 CET re-check in `raw/m1_m2_checks.txt` shows 326/318 — dynamic snapshots). The JDL requirement is valid — M2 is resolved in its favour.
- `CloudSite` **exists**: local ETP = `portal`, NEMO2 = `BwForCluster-Nemo2`. The JDL term is valid — M1 is resolved in its favour; no JDL edit was needed.
- A100 parent slot `slot1@c03-001-167.gridka.de`: `TotalSlotGPUs=8`, `GPUs=0` (unprovisioned partitionable parent), `Cpus=0`, all children Claimed/Preempting. So even inside the TOpAS pool the A100 node was fully allocated; the `GPUs` attribute is 0 on the parent.
- The author's schedd is `deepthought.etp.kit.edu`; `condor_q -better-analyze` negotiates a small view ("52 slots on 50 machines") that includes NEMO2 slots and local ETP workers but **not** the c03/TOpAS slots — the "Last failed match" line names `etprain.etp.kit.edu` for P4/P5 and `c03-001-140.gridka.de` earlier, i.e. the pool-federation attempt does not resolve to TOpAS.
- The probe's `probe.sh` in the official image ran as expected: `nproc=1` for the 1-CPU job, `/work` and `/ceph` mounted, `/ceph/srv` also mounted at ETP workers (contrary to the note that it is TOpAS-only), `/cvmfs` present but empty, no `/scratch`; `NVIDIA_VISIBLE_DEVICES=none`, `CUDA_VISIBLE_DEVICES=10000` for the CPU job.

## 6. Corrections after the first moves/checks (14 Nov 2026, 00:00–00:20 CET)

- **`bms2` is reachable and mounts `/ceph/dwong`** (verified from the Mac, 14 Nov 00:12 CET), contrary to the wiki-derived "bms2 unverified" note in §0.3 of the runbook. All four login hosts (`portal1`, `bms1`, `bms2`, `bms3`) were used for the in-use check before the first move.
- **TOpAS is reachable by flocking** (P5 ran on `c03-001-159.gridka.de`, `CloudSite=topas`), so the earlier P4/P5 "no match" reading is refined: V100S capacity existed; the A100 node was fully allocated (`GPUs=0`, `Cpus=0` on the parent, children Claimed).
- **NEMO2 has no Docker**: GPU slots there advertise `HasDocker=undefined`, `HasSingularity=true`; a docker-universe job cannot match (P6/P7 measured). This is a design blocker for the current image-based probe, not a queue effect.
- **ETP worker `CloudSite` is `schnepf`** (P1/P3 ran on `ms02.etp.kit.edu`), while `deepthought`/`deepthought2` slots report `portal`. The runbook's "portal" assumption holds only for the portal machines.
- **Job 759618** (another session's, `/work/dwong/r2_batch/tiny`) remained IDLE throughout; it is not ours and was never touched.

## 7. Author guidance received 14 Nov ~00:35 CET (adjusts the night, not the measurements)

- **Do not withdraw P4/P5:** GPU jobs are routed to the TOpAS pool; a 0-match in the local schedd view can be normal. Re-analysis with the tutorial form (`condor_q -better-analyze -pool f03-001-140-e.gridka.de <id>`) was run and is recorded in `raw/pool_analyze_p4_20261114.txt`: against the **c03/TOpAS** pool the A100 condition matches 3 drained slots, `Cpus` 14, `GPUs` 7, `[10]&&[11]` **0**, "2 would match if drained" — so P4 stays queued (capacity), as the author instructed, until the hard stop.
- **NEMO2 is Singularity-only.** `HasDocker=undefined`, `HasSingularity=true` on its GPU slots; the current docker-universe design cannot match (P6/P7). The author's recommendation: build the image, convert to an Apptainer SIF under `/work`/`/ceph`, so no docker registry is needed; the per-site docker-vs-Singularity decision and the NEMO2 SIF JDL attribute are questions (Q10). **No new job type tonight.**
- **Local CPU container capacity:** `HasDocker=true` 315 slots (all ETP), `ProvidesETPResources` 323, unclaimed docker 5 / ETP 13 at 00:35; `HasSingularity` 1094. Recorded for tomorrow's decision (Q11).
- **Hard stop moved to 09:30 CET** (was 05:30); the +3 h resubmission still runs ~02:50, and the **+6 h sample ran: P1w3/P3w3 submitted 05:50:32 CET, both completed with 18 s waits on ms04/ms03 (exit 0; `raw/queue_times_current.tsv`)**. The report/review got priority as planned.


## 8. Evidence for the checks whose transcript was missing from the first report draft

- `raw/evidence_capture_0331.txt` — 03:30 CET capture: two timestamped `docker info` runs (daemon unreachable), NEMO2 slot attributes (6 L40S: 4 Unclaimed/2 Drained; **4 H200: 1 Unclaimed/3 Drained**, all `HasDocker=undefined`), P2/P4/P6 analyses, the foreign `r2_batch` jobs, the GGUF sha256, the failed-copy paths. The 315/323/1094/5/13 counts are from `raw/pool_analyze_p4_20261114.txt` (00:35 CET).
- `raw/p6_analyze.txt`, `raw/p2_analyze.txt` — full analyses for P6 and P2 (the local P4 analysis is in `raw/pool_analyze_p4_20261114.txt`).
- `raw/gguf_sha256.txt` — the pinned GGUF hash on `/ceph/dwong/models`.
- `raw/login_hosts_mounts.txt` — all four ETP login hosts reachable and mounting `/ceph/dwong` and `/work/dwong`.
- `raw/m1_m2_checks.txt` — the M1/M2 `CloudSite` / `ProvidesETPResources` / `HasDocker` checks, re-run and recorded at 03:30 CET (they were first inspected at 23:44 and are the reason the report says "measured after submission").
- `w2/w2_check_rerun.json` — the W2 check re-run with exit code (3 = STOP_DIFFERENCE) and interpreter recorded in `w2/w2_run.txt`.
- `moves/from_host/MOVE_BACKFILL.tsv.first_attempt_20261113T235210Z` — the first backfill attempt, kept before the git-index exclusion was actually in the script.
