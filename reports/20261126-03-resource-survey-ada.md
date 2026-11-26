# Report — resource survey, Ada readiness and placement proposal

**Task:** `compute/20261126-01` (resource-card part of `experiment/20261126-02`).
**Result: PASS as a read-only survey.** Ada LLM serving is **ready**; Ada training/P.4 is **not ready** (no torch
environment; no usable container runtime). No reservation is made.

- **Branch:** `compute-resource-survey-20261126` @ `19396b62b4f3b83b3020b5ad38a717f96cf58947`
- **Report:** `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126.md` sha256
  `334ea05d46f287f8df25fc1d42e8f7543b53d524424e5fc6c233b6aeffb0c9f5`
- **Captures:** `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126_captures/` (six files; hashes in the report).
- **Snapshot:** 26 Nov 2026, 22:39–22:40 UTC.

## The table (snapshot; capacity, not a reservation)

| Host | CPU / load | RAM avail | GPUs now | Disk |
|---|---|---|---|---|
| deepthought | 40 / 7.48 | 448 GiB | 4× TITAN X 12 GB; no empty card; foreign apps on all four; free 6.45–11.55 GB | `/work` 951 GB, `/ceph` 334 TB |
| deepthought2 | 128 / 8.55 | 893 GiB | 2× L40S 46 GB; card 0 shared (27.2 GB free), card 1 **empty** (45.5 GB) | same |
| ETP pool | 433 Claimed / 18 Unclaimed / 9 Drained / 1 Owner | — | only 2 TITAN X + 1 L40S; **no H200/H100/A100/NEMO2 GPU**; `760065` (P.4 T1) Idle unmatched | — |
| TASL-2 | 32 / 0.05 | 58 GiB | 1× 4090 24 GB, **empty** (23.8 GB free) | 343 GB |
| TASL-7 | 24 / 0.83 | 60 GiB | 1× 4090 24 GB, **empty** (24.0 GB free) | 398 GB |
| Ada | 96 / 12.15 | 383 GiB | 8× RTX 6000 Ada 48 GB; cards 0 and 2 **empty** (48.4 GB free); 1/3/4/5 14.7 GB free (`vla-reasoning`); 6/7 21 GB free | `/data1` 2.1 TB |

TASL-2 has no R1 job; all its locks are free. TASL-7 has no R1 job and no compute app: the `jiachenl` GPU holder is
**gone** at this snapshot; `gpu0.lock` is free. TASL-2 CPUs 8–11 remain excluded. No request of another user was
changed.

## Ada readiness

- **LLM serving: ready.** `build-sm89-round7/{llama-server,llama-bench,llama-cli}` (llama.cpp `d8df12ebc`), the
  `gemma-4-31B-it-Q4_K_M.gguf` model, CUDA 12.4 and driver 545.23.08 are present. **ENGINEERING_ONLY timing** on
  card 0: **2,005 t/s prompt, 41.84 t/s generation** (`-p 256 -n 64 -ngl 99`), under 0.01 GPU-h, shared with
  `zihaozhao` at the start. Capture: `ada_gemma4_31b_bench.txt`.
- **Training / P.4 SFT: not ready.** System Python 3.10.12 has no torch; no venv/uv/conda; `docker` CLI exists but
  the daemon socket is permission-denied (uid 1030 not in `docker`); no `apptainer`/`singularity`/`podman`. The
  pinned v2.2 image `sha256:49dd9900…` cannot run as-is. It needs (a) a venv from the P.4 lock with a CUDA 12.x
  torch wheel (no sudo, internet, ~10–20 GB), or (b) a rootless runtime/docker group from the host owner, or (c)
  the pool's L40S/H200 when advertised. Not built, per the task.
- **T1 audits beyond the TASL pair:** Ada is not in the signed G.5 note; a per-node cross-host PASS and an addendum
  note are required. Its two empty cards are a plausible overflow host.

## Placement proposal

- **Expansion G.1b:** TASL-2, CPU-only, sets 0-3 / 4-7 / 12-15 / 16-31, no GPU. Waits only for the published note
  and strict check; the c1 record and gates are done.
- **G.5:** TASL-2 worker + TASL-7 audit chunks on the 4090 model; waits for the published G.5 note and the
  houseprice CPU-set fix; TASL-7's card is free now.
- **P.4 probe/SFT:** Ada card 0 or 2 first; the pool's L40S/H200 when advertised. Waits for the direct-launch path
  and Ada host config (local), the phase-1 note under R1-HOST-FREE, and the venv/container route.
- **D.3a/b proposer:** Ada card 0/2 (gemma4_31b) or the TASL pair; one GPU model per instance and per campaign.
  Waits for G1/G6, pre-declaration r4 and the per-arm smoke. D.3a's Y audit is CPU on deepthought (≤16 workers).
- **T1 audits beyond the TASL pair:** Ada only after a cross-host PASS and addendum note; no run now.

## What remains open

- The Ada two-hour process series is one sample only (the host is shared); the next round should take the second.
- TASL-7's six-hour GPU-holder series is one sample (empty now); the next round should recheck.
- No H200/H100/A100; the pool watch is recurring. No P.4/A5 batch GPU is available.
- No venv build was attempted (task says do not build yet).

## Rows of 26 Nov (g) — acknowledged (`compute/20261126-03`)

1. A shared card is allowed when memory fits; an empty card is taken first. The expansion G.1b and G.5 keep their
   reviewed empty-card lease checks until a reviewed unit changes them. The survey took the empty Ada card 0 first
   (it was shared at the timing start with `zihaozhao`, both processes named in the capture).
2. Job records name the other compute processes at start and end (count and memory only). For a label campaign I
   will keep the 60 s `nvidia-smi --query-compute-apps=pid,used_memory` log until `local/20261126-07` fixes the form;
   no command line or user name of another user's process will be recorded there.
3. An attempt lost to the card/host is sealed and repeated; no STOP, no attempt limit. A run that reached its
   budget/OOM beside another process is listed for the repeat, not relabelled.
4. No latest start or cutoff applies; I report the completed steps and what each open step waits for. A GPU-hour
   figure reached will be reported at once and the work continues.
5. The survey adds the free memory of every card in use (table above).

## Decided alone

To use TASL-2 as the jump host for the Ada read-only survey (the Mac has no route to Ada), and to take the empty
Ada card 0 for the named under-one-GPU-hour ENGINEERING_ONLY timing. No request, pin, sealed file or other user's
process was touched.

## What happens next

The expansion note publication, the G.5 note and the P.4 direct-launch path are the gates for the next compute
runs; all are with the coordinator/local worker. Compute's next ready cards are the D.3 G1/G6 code and the
torch tests of the P.4 host-config fill; I proceed with them in order.
