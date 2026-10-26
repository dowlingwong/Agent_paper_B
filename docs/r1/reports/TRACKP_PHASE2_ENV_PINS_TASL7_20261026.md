# Track P Phase 2 on TASL-7 — same environment, same model revisions (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on TASL-7). ENGINEERING_ONLY. Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, host-change header, migration step (2), and Phase 2; PLAN §10 R1-TASL7-TRACKP and R1-ENV-PIN. Evidence is in `tasl7_phase2_20261026/`. The portal's Phase 2 record is `TRACKP_PHASE2_ENV_PINS_20261026.md`.

## 2.1 Run venv: the same pins

- **Python and uv.** `uv` 0.13.5 is installed user-level (`pip3 install --user uv==0.13.5`), and Python **3.12.15** comes from `uv python install`. Both are the portal's versions. Nothing was installed system-wide and sudo was not used.
- **Venv.** `/home/dowling/r1_trackp/venvs/trackp-gpu`, the same path as on the portal. It was built from the portal's recorded `pip_freeze_trackp-gpu.txt`:
  - every pinned package was installed with `--no-deps`, from PyPI;
  - `torch==2.6.0+cu124` came from `download.pytorch.org/whl/cu124`;
  - `causal-conv1d==1.7.0` was built from source (`--no-binary`, `--no-build-isolation`) against `/usr/local/cuda-12.2` for sm_89 (`TORCH_CUDA_ARCH_LIST=8.9`), the same toolkit as on the portal.
- **Freeze check.** `uv pip freeze` on TASL-7 (`pip_freeze_trackp-gpu_tasl7.txt`) is **identical** to the portal freeze: the sorted diff is empty, over 121 lines. That covers torch 2.6.0+cu124, triton 3.2.0, transformers 5.19.0, peft 0.21.2, flash-linear-attention / fla-core 0.5.2, causal-conv1d 1.7.0, and kev `2074cc4`, laya `a478221`, startlux-decide `a99977d`.
- **Install attempts, recorded.**
  1. One `uv pip install` with the PyTorch index as an extra index timed out fetching `nvidia-cufft-cu12` from `pypi.nvidia.com`.
  2. Installing the other packages from PyPI and then torch alone from the cu124 index worked.
- **Done when: bf16 matmul and one DeltaNet forward on the GPU.** `r1/scripts/trackp_gpu_smoke.py` ran under the lease (`gpu_smoke_tasl7.json`). **Pass.** Every numerical value agrees with the portal's `gpu_smoke_attempt3.json` to about 1e-6:

| Check | Portal | TASL-7 |
|---|---|---|
| bf16 matmul, relative error vs fp32 | 2.874e-3 | 2.874e-3 |
| fp32 DeltaNet forward, max \|Δlogit\| vs CPU fp32 / tolerance | 0.02935 / 0.0403 | 0.02935 / 0.0403 |
| bf16 DeltaNet forward, max \|Δlogit\| / tolerance / argmax agreement | 0.2361 / 0.530 / 99.51 % | 0.2361 / 0.530 / 99.51 % |
| Peak memory, fp32 / bf16 forward | 3,345 / 2,096 MiB | 3,345 / 2,096 MiB |
| Times (descriptive): matmul / bf16 forward | 113 ms / 0.13 s | 145 ms / 0.17 s |

The TASL-7 timings are about 25 % slower in this micro-benchmark. The 25-minute E0 job took the same wall time on both hosts (see the equivalence report), so this is not a training-throughput difference.

## 2.2 Downloads: the same revisions, every file re-verified

- **Download.** `python -m r1.c3.train.registry --models-dir /home/dowling/r1_trackp/models --out <scratch registry>`. The PINS in the code are unchanged, so these are the portal's revisions, and the layout `<org>__<name>@<rev12>` is the same as the portal's. The downloader checks each file against the Hub's own record at that revision: the LFS sha256, or the git blob sha1 for non-LFS files.
- **Attempts.**
  1. The `hf_xet` transfer client stalled at 0 bytes on the first large file (`download_attempt1_xet_stall.log.txt`).
  2. A rerun with `HF_HUB_DISABLE_XET=1` (plain HTTPS from the Hub CDN; a runtime setting, no package change) downloaded and verified 7 repos. It then hit a transient DNS failure on StartLux-4B (`download_attempt2.log.txt`).
  3. StartLux-4B alone was retried with `--only startlux-4b` and verified: 18 files, 9.34 GB (`download_attempt3_startlux4b.log.txt`).
- **Check against the committed registry.** Every file of every repo was re-hashed against the **committed `r1/c3/train/registry.yaml`**, which records sha256 and size per file, and no extra files were allowed (`verify_against_registry.py`, output below). Separately, the per-file sha256 and size in the registry written on TASL-7 are identical to the committed registry for every repo.
- The committed `registry.yaml` is **unchanged**, because the TASL-7 files are the same bytes.

Result: **all 8 repos, 112 files, match** (`verify_against_registry_output.txt`):

```
kev-0.8b: 12/12 files match (jaredpalmer/kev-0.8b@788ddbdd6571) dir=/home/dowling/r1_trackp/models/jaredpalmer__kev-0.8b@788ddbdd6571
kev-4b: 16/16 files match (jaredpalmer/kev-4b@591dcb5bd6d0) dir=/home/dowling/r1_trackp/models/jaredpalmer__kev-4b@591dcb5bd6d0
laya: 8/8 files match (convaiinnovations/laya-typed-decisions@e929ae5cf69b) dir=/home/dowling/r1_trackp/models/convaiinnovations__laya-typed-decisions@e929ae5cf69b
qwen3.5-0.8b-base: 12/12 files match (Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee41) dir=/home/dowling/r1_trackp/models/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41
qwen3.5-4b-base: 13/13 files match (Qwen/Qwen3.5-4B-Base@1001bb4d826a) dir=/home/dowling/r1_trackp/models/Qwen__Qwen3.5-4B-Base@1001bb4d826a
startlux-0.8b: 16/16 files match (startlux-models/StartLux-Decision-v1.1-0.8B-Instant@6496ae641cc7) dir=/home/dowling/r1_trackp/models/startlux-models__StartLux-Decision-v1.1-0.8B-Instant@6496ae641cc7
startlux-2b: 17/17 files match (startlux-models/StartLux-Decision-v1.1-2B-Instant@f1e6cd147dda) dir=/home/dowling/r1_trackp/models/startlux-models__StartLux-Decision-v1.1-2B-Instant@f1e6cd147dda
startlux-4b: 18/18 files match (startlux-models/StartLux-Decision-v1.1-4B-Instant@416088f77cfc) dir=/home/dowling/r1_trackp/models/startlux-models__StartLux-Decision-v1.1-4B-Instant@416088f77cfc
ALL OK
```

## 2.3 Config

`r1/scripts/configs/trackp_portal.json` is **unchanged**. Every path in it (work, models, runs, HF cache, lock, venv) is the same on TASL-7, so `trackp.py --check-config` passes at the branch head (no placeholders). The config digest that runs record (`588869fa…` at `8e13e77`) is therefore the same on both hosts. Its `"host": "TASL-2 (zhixu portal)"` string is a label that no code reads. The host of each run is now recorded in the manifest (`host_record()`, commit `d3bed8b`, R1-ADA-OVERFLOW). Changing the label, or adding a `trackp_tasl7.json`, would change the config digest of later runs; this is left to the author (question 1 in the migration report).

## GPU use

Lease log: `gpu_lease_log.txt`. The Phase 2 smoke test ran 22:50:48–22:51:39 UTC.
