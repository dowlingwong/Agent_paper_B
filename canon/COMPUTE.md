# Compute resources

**As of 26 Nov 2026. AI-assisted (coordinating chat, Claude).** Facts with their sources in the repository; a value no
record supports is marked *to verify* and is filled by the agent that works on the host (a read-only command set, no
`sudo`). PLAN §10 rows decide which host a table may use.

**This repository is public.** This file holds host names, account names and private-range addresses only, all of
which already appear in committed records. No password, key, token or content of a credential file is ever written
here, and no agent reads one (`~/.config/r1/secrets.env`, `~/.ssh` keys, `~/.docker/config.json`, `.docker-config`).

## 1. Hosts

| Host | Address, account | CPU, memory | GPU | Storage | Shared? | Used for |
|---|---|---|---|---|---|---|
| **deepthought** | `deepthought.etp.kit.edu`, user `dwong`; no VPN needed | 40 logical CPUs (2 × Xeon E5-2630 v4), 503 GiB RAM | 4 × GTX TITAN X 12 GB (sm_52), usually held by other users' processes | code under `/ceph/dwong`, `/work/dwong`; project data `/ceph/srv/dwong/paperb`, `/work/dwong/paperb` | Yes. At least 10 of 40 cores stay free; audits use 16 workers | T0 audits, sweep-1 host, HTCondor submit host (schedd), D.3 audits |
| **deepthought2** | `deepthought2.etp.kit.edu`, user `dwong` | 128 logical CPUs (2 × EPYC 9335), 1,006 GiB RAM | 2 × L40S 46 GB, shared with other users' processes; one is offered through the HTCondor pool | as deepthought | Yes | pool GPU; has Apptainer; no docker group for the account |
| **ETP HTCondor pool** | submitted from deepthought; collectors `f03-001-140-e.gridka.de` (ETP + NEMO2) and `c03-001-140.gridka.de` (TOpAS) | about 1,100 slots, heavily used | **On 26 Nov the pool advertised no H200, H100 or A100 at all**: NEMO2's H200 (`g4402.nemo.privat`) has been absent since 24 Nov and no NEMO2 L40S is listed. What remains is one L40S slot on deepthought2 and two TITAN X on deepthought, both in state Owner. TOpAS (other collector): V100S 32 GB, A100 40 GB | `/work` and `/ceph` are mounted on ETP workers; **not** on TOpAS workers; NEMO2 jobs run under Apptainer (no Docker) | Yes, opportunistic | sweeps, Track P (P.4), D.3 proposer |
| **TASL-2** (zhixu portal) | SSH alias `portal_zhixu`, Tailscale `100.120.160.70`, user `dowling` (uid 1008) | i9-14900KF, 32 logical CPUs, 62 GiB RAM. **CPUs 8-11 are not used** (R1-TASL2-CPU) | 1 × RTX 4090, 24,564 MiB, driver 535 | local NVMe, 2.0 TB, about 837 GiB free on 26 Oct; work under `/home/dowling/r1_tracks/` and `/home/dowling/r1_trackp/` | Another user's desktop session; GPU exclusive to the author by agreement | T1 worker card: G.1b, G.4b, G.5, expansion nodes (CPU) |
| **TASL-7** | SSH alias `tasl7`, Tailscale `100.106.74.51` (`tasl-7.tail119748.ts.net`), user `dowling` (uid 1011); no `sudo` | Ryzen 9 7900X, 24 logical CPUs, 62 GiB RAM; all six 4-CPU groups pass the stability check | 1 × RTX 4090, 24,564 MiB, driver 580 | local NVMe, 1.9 TB, 965 GiB free on 26 Oct; same work paths as TASL-2 | Declared exclusive, but users `tianyu` and `jiachenl` have sessions; **a job of `jiachenl` held the GPU on 26 Nov** | T1 proposer server; G.5 audit chunks for seven nodes |
| **Ada** (zhixu experiment) | SSH alias `experiment_zhixu`, hostname `ucrtasl`, user `dowling` | *to verify* | 8 × RTX 6000 Ada 48 GB | `/data1/dowling` | Yes; jobs may be interrupted | census, overflow, whole-table fallback |
| **HoreKa 2** | `hk2-x86.scc.kit.edu`, user `ka_ir7683`; needs the KIT VPN, which cannot run beside Tailscale on the Mac | Slurm | H100, H200 | *to verify* | Project allocation; downtime 23 Nov to 4 Dec per the author's notes | not in use for Paper B tables |
| **HoreKa (legacy)** | `horeka.scc.kit.edu`, user `ir7683` | Slurm | A100 | — | login-only in December, retired 31 Dec 2026 | not in use |
| **Mac** | the author's M1 Max MacBook Pro, 64 GB | — | no model work when another machine can do it | `~/Documents/agent_paper_B`; deliveries in `Claude outputs/` | — | desk work only: code, specs, notes, reviews |

## 2. File systems and transfer

- deepthought, deepthought2 and the ETP workers share `/work` and `/ceph`. TASL-2, TASL-7, Ada and the Mac share
  nothing with them or with each other. Everything else moves through git (branches on GitHub) or `scp`.
- Container images for HTCondor are built by GitHub Actions and pulled by digest from `ghcr.io/dowlingwong/r1-htc-gpu`;
  the current Track P image is v2.2 (R1-TRACKP-IMAGE-V22-B). Sweep 2 used the v1 digest, and the D.3 draft proposes it.
- The sealed label trees live under `/ceph/srv/dwong/paperb/`. Test and evaluation partitions are read only after
  their release rows.

## 3. Limits

| Limit | Value | Source |
|---|---|---|
| `/work` | 1.4 TB file system, 950 GB free on 26 Nov; no per-user quota is reported by `quota -s` | `reports/cluster_resource_card_20261126/RESOURCE_CARD.md` |
| `/ceph` | 1.4 PB, 334 TB free on 26 Nov; no per-user quota reported | same |
| HTCondor request shapes in use | P.4: 8 CPUs, 131,072 MB, 150,000,000 KB disk, 1 H200; probe jobs: `request_disk` 35,000,000 KB. Larger disk requests left jobs idle (R1-TRACKP-I2-DISK) | P.4 host config; R1-TRACKP-I2-DISK |
| deepthought CPU | at most 16 audit workers, 10 of 40 cores free | R1-SWEEP2-B2-GO |
| TASL cards | one job per card, by lease (`gpu0.lock`); CPU jobs take `cpus-<set>.lock` | G.1b and G.5 specs |
| GPU-hour caps | see `PAPER_B_PLAN.md` §5 | the notes |
| HoreKa budget, Ada limits | *to verify* | — |

## 4. Known conditions

- **Batch GPUs:** no H200 machine has been in the collector since 24 Nov, and on 26 Nov no NEMO2 GPU of any model
  was advertised; end unknown. Track P (P.4) and the D.3 proposer both need a batch GPU, so this is the largest
  open resource risk. The question belongs to the ETP HTCondor administrators (the machines are provisioned into the
  pool, not owned by it). A different host or GPU model for a table is the author's decision.
- **TASL-2:** CPUs 8-11 (physical cores 4 and 5) crash under load; no job uses them.
- **TASL-7:** the GPU is not always free of other users; a lease check refuses to start beside a foreign compute
  process.
- **One GPU model per table** (24 Oct rule): a label table, the arms of one stage, and both stages of D.3 each stay
  on one GPU model.

## 5. Resource card (each agent, first task under this file)

Read-only, per host it works on: `hostname`, `id -un`, `nproc`, `lscpu | head -20`, `free -g`, `nvidia-smi`
(model, memory, driver, compute processes with their users), `df -h` of the work paths, `quota -s` where it exists,
and for the pool `condor_status` per GPU model (machines, GPUs, free now). The agent sends the values; the coordinator
replaces every *to verify* above.

## 6. Next-phase placement and capacity

These are the latest committed observations reviewed for the
[next-phase runbook](../docs/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md). A hardware listing is capacity.
A dated observation or lease is evidence of availability.

| Lane | Verified layout and limits | Last observation or dependency |
|---|---|---|
| T0 audit and D.3 CPU work | deepthought: 40 logical CPUs, 503 GiB total RAM, up to 16 audit workers while keeping at least 10 CPUs free. Use the shared ETP work paths for staged inputs and sealed outputs. | At 13:08 CET on 26 Nov the host had 451 GiB available RAM. The TITAN X cards had foreign compute processes. The CPU and GPU observations are separate. |
| Batch proposer and P.4 | P.4's recorded H200 shape is 8 CPUs, 131,072 MB RAM and 150,000,000 KB requested disk. Use the pinned image and exact scheduler request when comparing placement. D.3 needs one declared proposer-GPU layout. | At 13:08 CET the ETP collector advertised no H200, H100 or A100. Its one advertised L40S was in Owner/Idle state. H200 job 760065 had no match. The alternate TOpAS collector has different storage visibility. Verify live matching before relying on any slot. |
| T1 G.5 workers and audits | TASL-2 and TASL-7 each have one RTX 4090 with 24,564 MiB. Use the reviewed per-node placements, one GPU lease at a time, and the pinned CPU lease groups. Exclude TASL-2 CPUs 8–11. Approved TASL-7 audit scope covers seven nodes. | On 26 Nov TASL-2 passed the G.5 pilot-basis check. Houseprice's first CPU-set attempt completed and matched the reference, but the current procedure cannot produce the other two required attempts. TASL-7's card was occupied in the recorded snapshot. |
| Paper C memory-capped census | Candidate placement is one spare TASL 4090 lease or one Ada 48 GB card, with the memory cap stated explicitly and one layout for all four comparison cells. Reserve no live capacity until the owner confirms the slot and its note is accepted. | Design and smoke preparation can proceed on the desk. Ada's available memory, CPU limits and free disk remain to verify. No Paper C slot or GPU-hour allocation is assumed. |
| Mac and scratch | Design, manuscript builds, E-SYN setup and local code review. Launch scripts and inputs use the existing deployment path. | The Mac has no shared filesystem with ETP, TASL or Ada. Copy only the declared code, outputs and metadata through the appropriate channel. |

Reference observations are the [ETP cluster card](../docs/reports/cluster_resource_card_20261126/RESOURCE_CARD.md)
and [G.5 TASL preparation](../docs/reports/tasl_chain_20261122/G5_TASL_PREP_20261126.md).
When an operator refreshes capacity for a runbook, record time, device model and driver, total and currently
usable memory, foreign occupancy and lease, usable CPU groups, filesystem visibility and free space, and the
scheduler match against the exact request. Capture compute estimates and evidence results separately.
