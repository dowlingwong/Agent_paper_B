# llama.cpp bring-up on Deepthought — 25 October 2026

## Current outcome — authorized retry complete (25 October)

AI-assisted by GPT-6 (Codex). ENGINEERING_ONLY. The author's revised runbook explicitly authorized retrying instrumentation failures and revised the offload acceptance. The original stopped record remains preserved below and on the host; this second load attempt completed without rebuilding or changing the source/GGUF pins.

| Check | Observed result |
|---|---|
| GPU 0 full offload | **29/29 layers**, verbose log; acceptance route (i) |
| GPU 1 concurrent full offload | **29/29 layers** while GPU 0 remained loaded; route (i) |
| Loaded per-process memory | 4,920 MiB on each target card before acceptance; 5,253 MiB each after requests |
| One-token requests | Completed on GPU 0 and GPU 1 |
| Manager smoke | 20 requests, max_tokens 512, temperature 0.2; mean input 864.2 and output 91.65 tokens |
| Mean prompt throughput | 250.73 tokens/s, mean of per-request server timings |
| Mean generation throughput | 24.87 tokens/s, mean of per-request server timings |
| Request latency | Mean 7.2609 s; range 5.0395–9.1382 s |
| Determinism | Three identical requests, seed 4242, temperature 0.2: response text identical |
| 5,800-call projection | **11.70 hours inference only**, from measured mean request latency |
| Cleanup | Both owned PID/process groups validated and stopped cleanly; return codes 0 |
| Probe result | `status: COMPLETE`; wrapper exit 0; STOP paths now exit nonzero |

Loaded GPU utilisation was captured before acceptance (GPU 0: 18%; GPU 1: 35%). GPU 0 process 3552631 used UUID `GPU-c89fb4b0-1365-2f30-ba0b-4008046662ca`; GPU 1 process 3554283 used UUID `GPU-2516f262-6a75-eee3-26ee-b2e8d908c07d`. After cleanup each card returned to its 3 MiB baseline. No unrelated process was signalled, no OOM/partial offload was observed, and no host was substituted.

The source tag/commit, model revision/hash, compiler and binary paths are unchanged from the verified-artifact table below. The sole server-flag change was `--verbose`. Loaded-state GPU and per-process telemetry were saved before checking the layer count. A CPU control was unnecessary because the direct layer-count criterion passed. There were 25 completion requests total: 20 smoke, three determinism and two one-token probes. These use synthetic engineering manager contexts; they are not D28 liveness or evidence labels.

The 11.70-hour projection is below the five-day inference threshold. It does not estimate workers, fresh-seed audits, restarts, longer real histories or contention, and is not a whole-sweep completion forecast. Raw retry records remain at `/ceph/dwong/r1_bringup_20261025/revised_probe_02/`, with the launcher/exit record alongside it. Only summary documentation is pushed; raw internal logs/scripts remain local, as required by the earlier approval-review restriction.

Phase 1 acceptance is complete. The current author request permits only Batch B–independent preparation and climate PILOT next, with a hard stop before Phase 4.

## Historical first load attempt — stopped before inference

AI-assisted by GPT-6 (Codex). ENGINEERING_ONLY, not evidence.

### Outcome: Phase 1 STOP, incomplete

Phase 0 is complete and was pushed in commit `7a8ee19`. Phase 1 built both binaries and verified the official GGUF, then stopped during startup acceptance. **No chat-completion request was sent.** The 20-request smoke, determinism check, throughput estimate, and concurrent GPU 1 load were not performed. Phase 2 and all later phases were not started.

The author's revised execution runbook explicitly permitted Phases 0–1 despite the missing Batch B handoff. It did not waive Phase 1 acceptance or the global runner STOP boundary. The stopped standalone engineering probe is preserved; it was not retried.

### Verified artifacts

| Item | Observed value |
|---|---|
| Host | `deepthought.etp.kit.edu`, RHEL 8.10, four GTX TITAN X, compute 5.2, driver 525.147.05 |
| Toolkit | Installed `/usr/local/cuda-11.8`, nvcc 11.8.89; no installation, sudo, or root action |
| Source | `/ceph/dwong/opt/llama.cpp`, clean source tree |
| Release | [`v0.7.0`](https://github.com/ggml-org/llama.cpp/releases/tag/v0.7.0) |
| Source commit | `620d2225cc436ab0b001e3200e590e3b286ef9ab` |
| Binaries | `/ceph/dwong/opt/llama.cpp/build-gcc13/bin/llama-server` and `llama-cli` |
| Server version | `version: 0.7.0-dev (build 1, commit 620d222)`; `built with GNU 13.3.1 for Linux x86_64` |
| Official model | `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`, `qwen2.5-coder-7b-instruct-q4_k_m.gguf`, 4,683,073,536 bytes |
| Model revision | `13fb94bfda8c8cf22497dc57b78f391a9acb426a` |
| Model local path | `/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf` |
| Model SHA-256 | `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` |
| Raw batch | `/ceph/dwong/r1_bringup_20261025` |

Model URL: [official GGUF at pinned revision](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q4_k_m.gguf). The upstream LFS SHA-256 was checked before renaming the download, and independently recomputed immediately before the startup attempt. Both matched. Binary hashes, version, clean source status and final GPU/disk census are preserved locally in the raw evidence, which is not included in this push.

### Build attempts and environment adjustments

The runbook's initial recipe targeted `52` with installed CUDA 11.8 and system GCC 8.5. CUDA compilation succeeded, but server C++ compilation failed with class template deduction errors in `server-schema.cpp` and missing `std::setw` in `server-context.cpp`. Exit code 2 and the original logs are preserved. This was a build attempt, not an interrupted benchmark or evidence run.

The same unmodified tag was then built with already installed GCC Toolset 13.3.1 for C/C++, while CUDA retained `/usr/bin/g++` (GCC 8.5) as its supported host compiler. An explicit C++ include flag handled the upstream `<iomanip>` omission; no source patch was applied. The exact successful configuration was:

```sh
cmake -B build-gcc13 \
  -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-11.8/bin/nvcc \
  -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++ \
  -DCMAKE_C_COMPILER=/opt/rh/gcc-toolset-13/root/usr/bin/gcc \
  -DCMAKE_CXX_COMPILER=/opt/rh/gcc-toolset-13/root/usr/bin/g++ \
  '-DCMAKE_CXX_FLAGS=-include iomanip'
cmake --build build-gcc13 -j 32 --target llama-server llama-cli
```

Runtime `LD_LIBRARY_PATH` included `/usr/local/cuda-11.8/lib64` and `/opt/rh/gcc-toolset-13/root/usr/lib64`. Both binaries built successfully; `build_gcc13.exit` is 0. The different build directory preserves the first failed build. Build and download jobs ran in tmux sessions prefixed `r1_`, with output teed to logs.

### Startup STOP: evidence and limits

The probe launched GPU 0 only, with `CUDA_VISIBLE_DEVICES=0`, loopback port 18081, `-ngl 999 -c 8192`. PID and process group were both 3546902. The command is recorded in the preserved local `probe.json`.

The preserved local startup log records:

```text
common_params_print_info: verbosity = 3 (adjust with the `-lv N` CLI arg)
load_model: initializing, n_slots = 4, n_ctx_slot = 8192, kv_unified = 'true'
llama_server: model loaded
llama_server: listening on http://127.0.0.1:18081
```

It does **not** contain the required `offloaded N/N layers` line. After health became ready, the probe's acceptance assertion therefore stopped it with `AssertionError('STOP full offload not proven')`. This is a limitation of the measurement, not proof that the GPU was unable to offload the model. No loaded-state VRAM snapshot was recorded before that assertion; only pre-load and post-cleanup snapshots exist. The probe should have recorded loaded-state telemetry before its acceptance assertion. This is an agent instrumentation error.

Read-only diagnosis after cleanup: `llama-server --list-devices --verbose`, with no model load, enumerated all four TITAN X CUDA devices. `ldd libggml-cuda.so` resolved CUDA 11.8 libraries and the driver without missing dependencies; the diagnosis is preserved locally in `device_diagnosis.txt`. At this source commit, `src/llama-model.cpp:1988` emits the offload count through `LLAMA_LOG_INFO`; help describes default verbosity 3 as info. The exact reason the count was absent remains unconfirmed. More verbose logging is a proposed diagnostic, not a demonstrated fix.

The standalone script records `status: STOP` and zero requests. Its wrapper exit is 0 because the exception was recorded and cleanup completed; **that shell exit is not a passed probe**. Any future automation must inspect the recorded status or propagate a nonzero exit.

### Cleanup and current state

Before SIGTERM, the script checked the recorded PID, process group and exact command line. The owned server exited with code 0. No other process was signalled. Final census shows zero compute processes and 0 MiB used on every GPU. No model server from this execution remains running. Ceph still reports about 303 TiB free, above the 50 GiB floor. The source, both build directories, GGUF, and all failed/stopped records remain preserved.

No scientific interpretation, liveness verdict, host suitability verdict, or sweep readiness is established. No throughput or five-day projection can be calculated from this attempt. Harness-locked environments, caches, tests and pins were not set up or checked in Phase 2.

### Concrete next step, not executed

A locally preserved draft verbose probe adds `--verbose`, saves loaded GPU telemetry before testing the offload log, uses a fresh `verbose_probe_01` directory, and propagates STOP as a nonzero exit. Its Python syntax was checked without running it. It retains the same source/model pins and request protocol. It has **not** been transferred for execution or launched. Author continuation after this STOP is required before a new load attempt; there is no basis here for changing hosts or relaxing full-offload acceptance.

If Phase 1 subsequently passes, stop at Phase 2 until Batch B is merged and pushed to `origin/main`, as the author instructed. No author authorization note was written.

### Local evidence and publication scope

The raw host batch and a hashed local evidence copy in the isolated reporting checkout preserve build scripts/logs, the request-free probe manifest, synthetic prompt draft, device diagnosis and final state. Raw logs and scripts are not published in this branch. Their SHA-256 manifest was checked locally (21 files). Synthetic prompts were formatted from the then-uncommitted manager source only to prepare the standalone engineering smoke; they were never sent and are not a sweep pin. No existing committed result or ledger was edited or removed.

Automatic approval review rejected the initial push containing the full internal evidence bundle because publication of that broader payload was not considered clearly authorized. That commit remains local only. This replacement push contains just this summary report and STATUS; no raw logs or scripts are included.
