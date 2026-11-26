# Compute resource survey, Ada readiness and placement proposal — 26 November 2026

**Task:** `compute/20261126-01` (with the resource-card part of `experiment/20261126-02`). **Status:** PASS as a
read-only survey; **Ada training readiness is NOT ready** and **Ada LLM serving is ready**. This is a snapshot, not
a reservation. Read-only on every host: no `sudo`, no other user's process touched, no evidence run. The one GPU
measurement is the named ENGINEERING_ONLY timing in §5.

**Snapshot times (UTC, 26 Nov 2026):** deepthought 22:39:44; deepthought2 22:39:46; TASL-7 22:39:52; Ada
22:40:12; TASL-2 22:40:25; the timing at 22:38. Captures are in
`COMPUTE_RESOURCE_SURVEY_20261126_captures/` with their sha256 in §8.

## 1. One table — CPUs, memory, GPUs, disk

| Host | CPUs / load | RAM (GiB total / available) | GPUs and current state | Free disk under the work paths |
|---|---|---|---|---|
| **deepthought** | 40 logical (2× Xeon E5-2630 v4), load 7.48 | 503 / 448 | 4× GTX TITAN X 12,288 MiB, driver 525.147.05. No card is empty: `amonsch` has an app on all four; `friemer` shares card 1. Free memory: card 0 11,550; card 1 6,450; card 2 11,554; card 3 11,554 MiB. Card 1 at 100 %; the others 0 %. | `/work` 951 GB free; `/ceph` 334 TB free |
| **deepthought2** | 128 logical (2× EPYC 9335), load 8.55 | 1,006 / 893 | 2× L40S 46,068 MiB, driver 570.211.01. Card 0 shared (`lbogner` 13,810 MiB + our `dwong` r2_sparse_sk job 4,418 MiB), 27,226 MiB free, 100 %. Card 1 empty, 45,465 MiB free, 0 %. | same `/work` and `/ceph` |
| **ETP HTCondor pool** | 433 Claimed / 18 Unclaimed / 9 Drained / 1 Owner | — | Advertises only **2 TITAN X** (deepthought) and **1 L40S** (deepthought2); **no H200, H100, A100, and no NEMO2 L40S**. `760065` (P.4 T1 H200) is Idle with no match. | `/work` and `/ceph` on ETP workers make the same 951 GB / 334 TB |
| **TASL-2** | 32 logical (i9-14900KF; CPUs 8–11 never used), load 0.05 | 62 / 58 | 1× RTX 4090 24,564 MiB, driver 535.309.01, 23,830 MiB free, **empty**, 0 %. No compute apps. | `/` 343 GB free |
| **TASL-7** | 24 logical (Ryzen 9 7900X), load 0.83 | 62 / 60 | 1× RTX 4090 24,564 MiB, driver 580.178.04, 24,029 MiB free, **empty**, 0 %. No compute apps. | `/` 398 GB free |
| **Ada** (`ucrtasl`) | 96 logical (2× EPYC 9254), load 12.15 | 503 / 383 | 8× RTX 6000 Ada 49,140 MiB, driver 545.23.08. Cards 0 and 2 empty (5 MiB used, 48,427 MiB free, 0 %); cards 1, 3, 4, 5 33,715 MiB used / 14,717 free, 100 % (`vla-reasoning`); cards 6, 7 27,200/27,210 MiB used, 21,232/21,222 free (`vla-reasoning`). | `/data1` 2.1 TB free |
| **Mac** | desk only | — | no model work | no shared filesystem |

The pool counts move between snapshots (an earlier read had 434/16/4/1). They are capacity, not a reservation. The
two TITAN X slots are advertised while the cards show foreign apps; the one L40S slot is on a host whose card 1 is
empty.

## 2. GPU detail and other users

| Host | Card | Free MiB | Util | Other compute processes (count, memory, user) |
|---|---|---|---|---|
| deepthought | 0 | 11,550 | 0 % | 1, 652 MiB, `amonsch` |
| deepthought | 1 | 6,450 | 100 % | 2: 4,184 MiB `amonsch`; 1,568 MiB `friemer` |
| deepthought | 2 | 11,554 | 0 % | 1, 650 MiB, `amonsch` |
| deepthought | 3 | 11,554 | 0 % | 1, 650 MiB, `amonsch` |
| deepthought2 | 0 | 27,226 | 100 % | 2: 13,810 MiB `lbogner`; 4,418 MiB `dwong` (r2_sparse_sk, not Paper B) |
| deepthought2 | 1 | 45,465 | 0 % | none — empty |
| TASL-2 | 0 | 23,830 | 0 % | none — empty; `gpu0.lock` and all CPU-set locks free |
| TASL-7 | 0 | 24,029 | 0 % | none — empty; `gpu0.lock` free |
| Ada | 0 | 48,427 | 0 % | none at 22:40 (during the 22:38 timing, `zihaozhao` had 3,014 + 5,682 MiB, both gone by 22:40) |
| Ada | 1 | 14,717 | 100 % | 1, 33,684 MiB, `vla-reasoning` |
| Ada | 2 | 48,427 | 0 % | none — empty |
| Ada | 3 | 14,729 | 100 % | 1, 33,672 MiB, `vla-reasoning` |
| Ada | 4 | 14,729 | 100 % | 1, 33,672 MiB, `vla-reasoning` |
| Ada | 5 | 14,729 | 100 % | 1, 33,672 MiB, `vla-reasoning` |
| Ada | 6 | 21,232 | 0 % | 3, 8,658–8,662 MiB each, `vla-reasoning` |
| Ada | 7 | 21,222 | 100 % | 3, 8,660–8,670 MiB each, `vla-reasoning` |

Sessions: deepthought 5 users; deepthought2 18 users; TASL-2 `ZhixuGroup` on pts/0 and pts/3 plus `dowling` on
pts/2 (this worker's own SSH); TASL-7 no sessions; Ada `myan035` and `zli538`, plus CPU processes of `jiachenl`.
TASL-2 has no R1 job and no compute process. TASL-7 has no R1 job and no compute process; the `jiachenl` GPU holder
recorded earlier is **gone** at this snapshot.

## 3. HTCondor pool

- Advertised GPU devices: 1 machine with 2× GTX TITAN X (deepthought) and 1 machine with 1× L40S (deepthought2).
  **No H200, H100, A100, and no NEMO2 GPU of any model.**
- Jobs under `dwong`: `760065` (P.4 T1, H200) Idle and unmatched; `760142`, `760143`, `760145`, `760146` Running,
  each 4 CPUs / 32 GB / 1 GPU, requiring `NVIDIA A100-PCIE-40GB` — these are the r2_sparse_sk project, **not Paper
  B**; `759624`, `759625` are old idle probes. No request was changed.
- Pool state counts: 433 Claimed, 18 Unclaimed, 9 Drained, 1 Owner.

## 4. Ada readiness

**LLM serving — ready.** `/data1/dowling/models/llama.cpp/build-sm89-round7/` holds `llama-server`, `llama-bench`
and `llama-cli` (llama.cpp `d8df12ebc`, build 10474); `/data1/dowling/models/round7-blackwell-grouped/` holds
`gemma-4-31B-it-Q4_K_M.gguf` (18,323,733,440 B). CUDA 12.4 (`/usr/local/cuda` → 12.4.131), driver 545.23.08,
`gcc`/`g++`/`cmake`/`ninja` present. Ollama 0.9.2 is installed but no instance is running. The proposer fits on one
48 GB card (17.05 GiB of weights).

**Training / P.4 SFT — not ready.** System `python3` is 3.10.12 and has **no torch**; there is no venv, `uv` or
`conda` in the account, and `/data1/dowling/toolchain/python` is a plain 3.13 build. The pinned v2.2 GPU image
(`sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949`) **cannot be run by this account**:
the `docker` CLI exists but the daemon socket is permission-denied (uid 1030 is in `dowling`, `video`, `render`, not
`docker`), and `apptainer`, `singularity` and `podman` are absent. What it would take, without building now:
(a) a Python venv under `/data1/dowling` from the P.4 lock/requirements with a CUDA 12.x torch wheel, transformers
and peft — no sudo, needs internet and about 10–20 GB; or (b) a rootless container runtime or `docker` group from
the host owner (admin action); or (c) run P.4 on the pool's L40S/H200 when one is advertised, where the image runs
under the scheduler. The direct-launch path and the phase-1 note must exist first; neither does yet.

**T1 audits beyond the TASL pair — not ready.** Ada is not a host in the signed G.5 note; using it needs a per-node
cross-host PASS and an addendum note. Its two empty 48 GB cards make it a plausible overflow host later.

**Process series.** One snapshot at 22:40 shows `vla-reasoning` on six cards, `zihaozhao` on card 0 (exited before
22:40), `jiachenl` on the CPUs, and two interactive users. The two-hour process series is **not complete** in this
round; the next round should take the second sample.

## 5. ENGINEERING_ONLY timing (named in the task)

On card 0, 22:38Z, with `zihaozhao` sharing the card at the start (3,014 + 5,682 MiB, both gone at the end):
`llama-bench -m gemma-4-31B-it-Q4_K_M.gguf -p 256 -n 64 -r 1 -ngl 99` → **prompt 2,005.47 t/s; generation 41.84
t/s** (CUDA, 99 layers, 17.05 GiB, 30.70 B params, build `d8df12ebc`). Cost well under 0.01 GPU-h; descriptive
only, not an outcome. Capture: `ada_gemma4_31b_bench.txt`.

## 6. Placement proposal (R1-HOST-FREE)

| Work | Host now | What must exist first |
|---|---|---|
| Expansion G.1b (4 CPU nodes) | **TASL-2**, CPU-only, sets 0-3 / 4-7 / 12-15 / 16-31, no GPU lease | the published expansion note and its strict check (c1 record is now delivered); the per-node gates are already on main |
| G.5 campaigns | **TASL-2** worker + **TASL-7** audit chunks, one RTX 4090 model | the published G.5 note; the houseprice CPU-set fix on TASL-2; the TASL-7 cross-host PASS/xc3 for audit chunks; the card is free now |
| P.4 probe and SFT | **Ada card 0 or 2** (48 GB, empty) first; the pool's L40S/H200 when advertised | the direct-launch path and Ada host configuration (local), the phase-1 note revised under R1-HOST-FREE, and either a venv from the lock or a container runtime; 40 GPU-h cap including the probe |
| D.3a/b proposer | **Ada card 0/2** (gemma4_31b at 41.8 t/s generation) or the TASL pair; all arms of one instance on one GPU model, one model per campaign | the G1/G6 runner, pre-declaration revision 4, and the per-arm smoke; the audit is CPU on deepthought |
| D.3a Y audit | **deepthought** CPU, at most 16 workers while keeping 10 cores free | the G6 audit unit with Y(w) at w = 5, 10, 15, 20 |
| T1 audits beyond the TASL pair | **Ada** card 0/2 only after a per-node cross-host PASS and an addendum note | that PASS and note; no run now |
| Paper C E-SYN / CPU work | desk/CPU, Mac or deepthought | separate Paper C decision; not in this survey |
| Mac | desk only | no shared filesystem with ETP/TASL/Ada |

The P.4 note must name the hardware it actually uses (R1-HOST-FREE (3)); a run under the signed G.5 note stays on
the TASL pair. The pool's L40S is a real batch alternative, but the two TITAN X cards are sm_52/12 GB and are not a
substitute for P.4's H200 shape.

## 7. What is not established here

- Ada's two-hour occupancy series (one sample only; shared host, changes quickly).
- A build from the P.4 lock (not attempted; the task says do not build yet) and the exact venv disk/time.
- Any H200/H100/A100 availability; the pool has none at this snapshot.
- TASL-7's six-hour GPU-holder series (one sample; the card is empty now).
- Any label/evaluation read: none; `labels_read: none`.

## 8. Captures

| File | sha256 |
|---|---|
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/deepthought.txt` | `0913bf756e82eab66a337d205956cb916ff1a77f1efb620755b2545f9a46aeed` |
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/deepthought2.txt` | `3002baff6729f4c153388d3a7ee67f7e9a835ea55fbe31a2e8b78be9a807c68c` |
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/TASL-2.txt` | `e84d40362478ccdf932e8fb8dc35c1601563e62ee866e08d26de6fd4d599f60f` |
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/TASL-7.txt` | `9bf2d62f6c814b266e2f1cfa634a3bc9b3494c7215d96bb2f931cd1284d8a9f1` |
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/Ada.txt` | `93d5224e258e0b0198b14224f79180df76dbde9864ff83f11cc50f918ef3b7bb` |
| `COMPUTE_RESOURCE_SURVEY_20261126_captures/ada_gemma4_31b_bench.txt` | `b7b15c25e6da3af845b76e2e148d8559e4d4e6ae995e0c2a0e69492c474f5c62` |

The commands were read-only: `hostname`, `id`, `nproc`, `lscpu`, `free -g`, `uptime`, `nvidia-smi` queries,
`df -h`, `quota -s` (none), `ps`, `who`, `fuser` on our own lock files, `condor_status`, `condor_q`, and the
`llama-bench` timing above. No command line or file of another user was read.
