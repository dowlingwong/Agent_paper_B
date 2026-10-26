# Track P Phase 2 — environment, downloads and pins on the portal (26 Oct 2026)

AI-assisted (Claude Code, Track P agent on zhixu portal). ENGINEERING_ONLY. **Status: pending independent review (STOP 2).** Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 2. Branch `trackp-20261026` (the author's overnight instruction: Phases 2–4 use the reviewed Track P branch instead of a merged `main`; Phase 1 accepted at `51d0d57`). Evidence: `trackp_phase2_20261026/`.

## 2.1 Run venv

`~/r1_trackp/venvs/trackp-gpu` (uv 0.13.5, Python 3.12.15): harness deps from its `uv.lock`; **torch 2.6.0+cu124** (triton 3.2.0), transformers 5.19.0, peft 0.21.2, safetensors 0.8.0, accelerate, datasets; ModernBERT is in transformers 5.19 (no extra package); linear-attention kernels that transformers 5.19 binds for Qwen3.5's Gated DeltaNet layers (`use_kernel_func_from_hub_with_fallback`: package if importable, else the torch path): **flash-linear-attention 0.5.2** (fla-core 0.5.2) and **causal-conv1d 1.7.0** built from source against the local CUDA 12.2 toolkit for sm_89; code pins `kev` @ `2074cc4`, `laya` @ `a478221`, `startlux-decide` @ `a99977d` (`--no-deps`). All PyPI packages `--exclude-newer 2026-10-11`. Full list: `pip_freeze_trackp-gpu.txt`.

Torch choice, attempts recorded:

| Attempt | torch | Result |
|---|---|---|
| 1 | 2.5.1+cu121 (native CUDA 12.1 on driver 535 / CUDA 12.2; within transformers' declared floor ≥ 2.5 and Kev's pin < 2.9) | **Failed:** transformers 5.19 calls `torch.accelerator` (torch ≥ 2.6) at import (`module 'torch' has no attribute 'accelerator'`). |
| 2 | **2.6.0+cu124** (closest CUDA to the driver inside Kev's pin ≥ 2.6, < 2.9; runs on driver 535 through CUDA minor-version compatibility — Phase 0 risk R1) | Imports; GPU smoke test passes (below). |

Known limitations of this venv (recorded, not failures of a Phase 2 criterion):
- fla 0.5.2 warns that Triton 3.2 is below its recommended 3.3; its kernels were therefore checked numerically on the card (below).
- With `CUDA_VISIBLE_DEVICES=""` transformers 5.19 cannot import under torch 2.6 (`torch.accelerator` raises when no device is visible). transformers binds the CUDA-only `causal_conv1d` kernel for every Qwen3.5 forward, so Qwen3.5-family models cannot run on CPU tensors in this venv. Consequence: CPU dry runs (`trackp.py --tiny`) and the CPU unit tests use the Phase 1 venv `trackp-cpu` (torch 2.14.1+cpu; all Track P tests pass there); `trackp-gpu` is for GPU work only. Running the Track P tests in `trackp-gpu` (card visible, under the lease): 123 passed, 27 failed / 3 errors, all of these two kinds (`trackp_tests_in_gpu_venv.txt`).

**Done when — bf16 matmul and one DeltaNet forward on the GPU** (`r1/scripts/trackp_gpu_smoke.py`, under the GPU lease; `gpu_smoke_attempt2.json`):
- bf16 matmul 2048² on the RTX 4090 (cc 8.9): relative error vs fp32 2.9e-3. Pass.
- Forward of the downloaded, verified Qwen3.5-0.8B-Base (409 tokens; fla + causal-conv1d bound) on the GPU in fp32 and bf16: finite; compared with a pure-fp32 CPU forward on transformers' torch path. fp32: max |Δlogit| 0.029 (logits up to 30.7), next-token argmax agreement 100 %; bf16: 0.236, agreement 99.5 %. Pass.
- Criterion history: attempt 1 of the smoke test (`gpu_smoke_attempt1.json`) compared the fast path with the torch path on the GPU against an **arbitrary** 2e-3 and "failed" at 0.029. A probe (`parity_probe.py`) showed the torch path itself deviates by 0.020 from the fp32 CPU reference as soon as TF32 matmuls are on, i.e. 0.029 is TF32-class precision of fla's Triton dots, not a kernel error. The check was replaced by a calibrated criterion (fast-path deviation ≤ 2 × that of a known-correct reduced-precision torch-path run: TF32 for fp32, bf16 for bf16; argmax agreement ≥ 99 %): fp32 0.029 ≤ 0.040, bf16 0.236 ≤ 0.530 (the fla path is closer to fp32 than the bf16 torch path). This is a check of my own, not a runbook criterion; the reviewer should judge it.
- Speed (after Triton warm-up): fla path 0.13 s vs torch path 0.14 s for this forward; the first fla call compiles Triton kernels (~20 s).

## 2.2 Downloads and registry

`r1/c3/train/registry.py` → `r1/c3/train/registry.yaml`: 8 repos at the Phase 0 revisions (Kev at its `v1.0` release tag commit), into `~/r1_trackp/models/<org>__<name>@<rev12>`; **every file verified against the Hub's own record at that revision** (LFS sha256 for LFS files, git blob sha1 for the others) and its sha256 recorded; free-space floor 100 GB (R1-EXAM-STORAGE, shared filesystem) checked before and after each download (≈ 879 GB free at the start). `--verify` re-hashed all 112 files after download: no mismatch.

| Key | Repo @ revision | Files | GB |
|---|---|---|---|
| kev-0.8b | jaredpalmer/kev-0.8b @ 788ddbdd6571 (v1.0) | 12 | 0.07 |
| kev-4b | jaredpalmer/kev-4b @ 591dcb5bd6d0 (v1.0) | 16 | 0.16 |
| qwen3.5-0.8b-base | Qwen/Qwen3.5-0.8B-Base @ dc7cdfe2ee41 | 12 | 1.77 |
| qwen3.5-4b-base | Qwen/Qwen3.5-4B-Base @ 1001bb4d826a | 13 | 9.34 |
| laya | convaiinnovations/laya-typed-decisions @ e929ae5cf69b | 8 | 0.85 |
| startlux-0.8b | startlux-models/StartLux-Decision-v1.1-0.8B-Instant @ 6496ae641cc7 | 16 | 1.77 |
| startlux-2b | startlux-models/StartLux-Decision-v1.1-2B-Instant @ f1e6cd147dda | 17 | 4.57 |
| startlux-4b | startlux-models/StartLux-Decision-v1.1-4B-Instant @ 416088f77cfc | 18 | 9.34 |

Kev adapters ("the released ones named in the Kev README"): additionally cross-checked against the GitHub release `kev-1.0` — `kev-0.8b.tar.gz` and `kev-4b.tar.gz` match `SHA256SUMS.txt` and GitHub's asset digests, and `adapter_model.safetensors`, `head.pt`, `adapter_config.json` inside them are byte-identical to the Hub files in the registry (`kev_release_tarballs.sha256`). Kev's `training_config.json` `base_revision` equals the pinned Qwen base revisions.

## 2.3 Config

`r1/scripts/configs/trackp_portal.json` filled from the registry (work/models/runs/HF dirs, GPU, lock path, every base's revision and local path, Kev adapter paths, code pins, venv record); `python r1/scripts/trackp.py --check-config` → no placeholder, exit 0 (config sha256 `f9b7354f…`). One value is a choice to be confirmed: `jev.model = jev-1.14.0` (newest versioned id in the TypeSafe docs, the PLAN row's example; needed only in Phase 7, and the client refuses any other returned version). The CLI test that assumed placeholders in the shipped config now builds a temporary placeholder config.

## GPU use

Lease log (`gpu_lease_log.jsonl`): smoke attempt 1 (04:35:24–04:36:11 UTC), parity probe (04:36:36–04:36:43), smoke attempt 2 (04:37:18–04:37:33), Track P tests in the GPU venv (flock). Total < 5 GPU-minutes; no Track X job ran; no other compute process was present.

## Questions for the author

1. Torch 2.6.0+cu124 on driver 535 via minor-version compatibility (attempt 1 with native cu121 is impossible under transformers 5.19). Acceptable, or upgrade the driver?
2. `jev.model = jev-1.14.0`?
