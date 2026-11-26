# Resource card — deepthought, deepthought2 and the ETP HTCondor pool (26 Nov 2026)

Read-only values from the hosts (`hostname`, `id -un`, `nproc`, `lscpu | head`, `free -g`, `nvidia-smi`,
`df -h`, `quota -s`) and `condor_status`; no request or file changed. Sample time 26 Nov 2026 13:08 CET
(12:08Z).

## deepthought (`deepthought.etp.kit.edu`, user `dwong`)
- CPU: **40** logical (2 sockets × 10 cores × 2 threads), Intel Xeon E5-2630 v4 @ 2.20 GHz (max 3.10 GHz).
- RAM: **503 GiB** total; 44 used, 153 free, 305 buff/cache, **451 available**; swap 3 GiB (full).
- GPU: **4 × NVIDIA GeForce GTX TITAN X, 12,288 MiB**, driver 525.147.05, compute mode Default.
  At sample: GPU0 0% / 657 MiB; **GPU1 87% / 5,757 MiB**; GPU2 0% / 653 MiB; GPU3 0% / 653 MiB.
  Compute processes are foreign (`/work/amonsch/.../python` 652+4,184+650+650 MiB; `python3` 1,568 MiB), so the
  cards are **not** free for a new job merely because utilization is 0%.
- Storage: `/work` 1.4 TB, 385 GB used, **950 GB avail (29 %)**; `/ceph` 1.4 PB, 998 TB used, **334 TB avail
  (75 %)**; `/` 442 GB, 383 GB used, 60 GB avail (87 %). `quota -s` reports no user quota.

## deepthought2 (`deepthought2.etp.kit.edu`, user `dwong`)
- CPU: **128** logical (2 sockets × 32 cores × 2 threads), AMD EPYC 9335 32-Core, max 4.42 GHz.
- RAM: **1,006 GiB** total; 69 used, 636 free, 307 buff/cache, **937 available**; no swap.
- GPU: **2 × NVIDIA L40S, 46,068 MiB**, driver 570.211.01. At sample: **GPU0 97% / 18,244 MiB**;
  **GPU1 0% / 9,647 MiB**. Foreign compute processes: `.venv/bin/python` 13,810 MiB,
  `/home/dwong/anaconda3/bin/python3` 4,420 MiB, `python` 9,638 MiB.
- Storage: same `/work` and `/ceph` values as deepthought; `/` 949 GB, 482 GB used, **468 GB avail (51 %)**.
  `quota -s` reports no user quota.

## ETP HTCondor pool (`condor_status`, 12:08Z)
- **H200: 0 machines/slots**; H100: 0; A100: 0. The NEMO2 H200 has been absent since after 24 Nov.
- **GTX TITAN X**: one partitionable slot `slot1@deepthought.etp.kit.edu`, CloudSite `portal`,
  `GPUs=2` of `TotalGPUs=4`, 12,207 MiB per GPU, State **Owner/Idle** (not a standard match for our jobs).
- **L40S**: one partitionable slot `slot1@deepthought2.etp.kit.edu`, CloudSite `portal`,
  `GPUs=1` of `TotalGPUs=2`, 45,468 MiB per GPU, State **Owner/Idle**.
- T1 760065 remains queued; `condor_q -better-analyze` reports no matching machine for the H200 requirement.

Resource-card values sent for COMPUTE.md §5; source commands were read-only.
