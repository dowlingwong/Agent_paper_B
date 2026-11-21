# R1-TRACKP-IMAGE-V21 diagnostic — image v2 on NEMO2 H200 (job 759916, ENGINEERING_ONLY)

21 November 2026. One read-only diagnostic job on `g4402.nemo.privat`, image v2 GPU
`sha256:b1144ece…`, H200 `GPU-b9c61835…`, submitted from `deepthought`. Job **759916.0** exited 0
and wrote `handback/job.log` and `handback/exit_status.txt` (0). A first submission, **759915.0**,
was held with `HoldReasonCode 26` ("Job used more disk space than requested", `DiskUsage`
17,500,000 KB against a 10,000,000 KB request) before any probe ran; it was removed and the same
unit was resubmitted with `request_disk = 35,000,000` (the smoke's reviewed value). No probe
output from 759915 is used.

Unit hashes: `job.jdl` `dc0687f3…`, `diag.sh` `5934ca5f…`, `diag.py` `adb39dc5…`.
Job log: 318 lines, `trackp-image-v21-diag 759916.0 g4402.nemo.privat 2026-11-21T22:14:00Z`.

## Findings

| Check | Result |
|---|---|
| gcc / cc / clang / g++ / c++ / make on PATH | **all MISSING** |
| `/usr/bin/gcc`, `/usr/bin/cc`, `/usr/bin/clang`, `/usr/bin/g++` | absent |
| binutils / ld | `binutils-2.35.2-42.el9_3.1`, `/usr/bin/ld` present |
| `glibc-devel`, `gcc`, `gcc-c++` RPMs | not installed |
| `CC` / `CXX` | unset / unset |
| Triton | 3.2.0; `driver.active.get_current_target()` → `RuntimeError: Failed to find C compiler. Please specify via CC environment variable.` at `triton/backends/nvidia/driver.py:80` (`CudaUtils` → `compile_module_from_src` → `_build`) |
| trivial `@triton.jit` kernel | not reached: the NVIDIA driver cannot initialise without a compiler (`OSError: could not get source code` in the in-process exec is an artefact of `exec`-defined kernels; the subprocess kernel run fails earlier in the same driver path) |
| `import causal_conv1d` | **`ImportError: undefined symbol: _ZN3c106detail14torchCheckFailEPKcS2_jRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE`** from `causal_conv1d_cuda.cpython-312-x86_64-linux-gnu.so` |
| `import fla` | `RuntimeError: Failed to find C compiler…` (same Triton driver path; `fla.utils._device` warns "Triton is not supported on current platform") |
| torch / device | 2.6.0+cu124, CUDA 12.4, H200 capability (9, 0), `cuda_available True` |

## Reading

Two independent defects, not one:

1. **No C compiler in the gpu runtime image.** Triton compiles its CUDA launcher at run time; the
   v2 gpu target installs no compiler (only the `build` stage does), so the Triton driver raises
   before any kernel runs. `fla` fails through that path. This is the smoke's `kernel_import_error`
   and is fixed by adding `gcc` to the gpu target.
2. **causal_conv1d 1.7.0 was built with the cxx11 ABI while the pinned torch 2.6.0+cu124 wheel is
   the pre-cxx11 (ABI=FALSE) build.** The extension's `torchCheckFail` symbol takes
   `std::__cxx11::basic_string`, which libtorch does not export, so the import fails before any
   compiler could matter. A compiler alone does not fix this. The official v1.7.0 release ships
   `cu12torch2.6` wheels for both ABI variants; the matching `cxx11abiFALSE` cp312 wheel
   (`sha256:5a76a78a…`, metadata version 1.7.0) replaces the source build.

Both fixes are exactly the two that R1-TRACKP-IMAGE-V21 authorises for image v2.1 (a C compiler,
plus the prebuilt causal_conv1d wheel if one fits the pinned torch/CUDA/Python), so v2.1 proceeds
and no STOP is raised.

Evidence: `handback/job.log` (on `/work/dwong/paperb/work/trackp-h200-v21-diag-20261121.TVe0xh`),
job stdout/err/log in the same staging directory.
