# Independent review — Track P image v2.2 Dockerfile/workflow diff (R1-TRACKP-IMAGE-V22-B), 24 November 2026 (rounds 1–2)

Reviewer: `reviewer-v22-dockerfile`, fresh-context delegated subagent; independent and read-only.
Review windows: round 1 2026-11-24 00:22–00:34 CET (23:22–23:34Z); round 2 00:35–00:40 CET (23:35–23:40Z).

Object: worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htc-image-v2.2-20261124`,
branch `htc-image-v2.2-20261124`; round-1 object **`c04be5e4`**
(`c04be5e4958f6784ec1b2265bd008fcc27851b1d`), round-2 (current, final) object **`3c54a0e8`**
(`3c54a0e893098c7d6cc95d6581114c64435cfa30`); parent `006fc315` (the v2.1 branch tip
`006fc315f7700130a49ce465cdacda28e85674c5`). The branch is **not pushed** at either point:
`git branch -r --contains <tip>` is empty, `git ls-remote --heads origin 'htc-image-v2.2-*'` is empty, and
`git branch -vv` shows `ahead 1` (round 1) then `ahead 2` (round 2) of `origin/htc-image-v2.1-20261121`.
Authority: published `main` **`44c3d80e`** (`44c3d80e6202030e6aeef7a62d672a402f92884d`), which is also
`origin/main` at review time; row **R1-TRACKP-IMAGE-V22-B** at `docs/r1/PLAN.md:1500` and
**R1-TRACKP-V21-FREEZE** at `docs/r1/PLAN.md:1385`.

Method: read-only git in the worktree and in the published main tree; downloaded and hashed the pinned PyPI
sdist and the v1.7.0 GitHub release wheel; read `torch/utils/cpp_extension.py` at tag `v2.6.0`; ran local
behaviour experiments in `/tmp` with the Dockerfile's pinned `uv 0.13.6` and an environment carrying the same
build-dependency versions as the env3 freeze (setuptools 84.2.1, wheel 0.48.0; packaging 26.4 local vs 26.2
frozen). No repository write other than this review; no push, no image build, no job action. Limitation: no
Docker daemon is available in this session, so there is no in-container run; the loader-level conclusion in
blocker B3 is derived from the extension's ELF and from torch 2.6's link flags, and a container confirmation is
recommended before the next push.

## Round 2 (final) — commit `3c54a0e8`: ACCEPTED

Round-2 object: same worktree and branch, now at **`3c54a0e8`**
(`3c54a0e893098c7d6cc95d6581114c64435cfa30`), parent `c04be5e4`; still **not pushed** (no remote branch
contains `3c54a0e8`; `git ls-remote --heads origin 'htc-image-v2.2-*'` empty; `git branch -vv` shows
`[origin/htc-image-v2.1-20261121: ahead 2]`). Round-2 diff: **Dockerfile only**, +25/−11; the workflow file is
byte-identical to the round-1 reviewed version. Worktree clean.

| file | sha256 at `3c54a0e8` |
|---|---|
| `r1/scripts/htcondor/docker/Dockerfile` | `40c35e2c9600bbb6dabb8ea8b159c565f00730960122cfba5a4f19f589bb3764` |
| `.github/workflows/r1-htc-image.yml` (unchanged from round 1) | `2e7605dfb6904a6fdb1b88334630244fcd1fd2c6963e4a08e94370b1ac6e6a65` |

Cumulative v2.2 diff vs v2.1 `006fc315`: two files, +43/−12; the `apptainer/` freeze/lock/def are untouched
and frozen line 10 remains `causal-conv1d==1.7.0`.

### Round-1 blockers: resolution verification

**B1 — resolved: the sdist now really compiles.** The new block (Dockerfile lines 116–124) extracts the pinned
sdist (sha256 `3202758494…cd32b` unchanged and still checked), runs the exact Python edit, and invokes
`"$TP" setup.py bdist_wheel -d /tmp/causal_wheel` with `CAUSAL_CONV1D_FORCE_BUILD=TRUE`
`CAUSAL_CONV1D_FORCE_CXX11_ABI=FALSE`. In the pinned sdist, `CachedWheelsCommand.run()` returns
`super().run()` when `FORCE_BUILD` (`setup.py:43,323–325`), so the cached-wheel `urlretrieve` download is
unreachable. The prebuilt-wheel URL/pin is gone (only the explanatory comment mentions "cxx11abiFALSE"), and
`CAUSAL_CONV1D_SKIP_CUDA_BUILD` / `CAUSAL_CONV1D_LOCAL_VERSION` are not set. The build output is redirected to
`/opt/r1/causal_conv1d_build.log` (plain redirect; `-e`/`pipefail` still abort on failure), and its sha256 plus
the built wheel's sha256 are recorded (`CAUSAL_CONV1D_BUILD_LOG_SHA256`, `CAUSAL_CONV1D_WHEEL_SHA256`,
`CAUSAL_CONV1D_SO_SHA256`; copied to the gpu target and recorded in VERSIONS).

**B2 — resolved: the freeze line stays version-only.** The build produces
`/tmp/causal_wheel/causal_conv1d-1.7.0-*.whl` and installs it **by name** with
`uv pip install --no-deps --no-index --find-links /tmp/causal_wheel 'causal-conv1d==1.7.0'` (line 126); no
local direct-URL requirement is installed. Verified with the Dockerfile's pinned `uv 0.13.6` and the same
build-dependency versions as the env3 freeze (setuptools 84.2.1, wheel 0.48.0): a scratch package named
`causal_conv1d` version 1.7.0 with a C extension, built via `setup.py bdist_wheel -d`, yields
`causal_conv1d-1.7.0-cp…-*.whl` (the Dockerfile glob matches), and the name+`--find-links` install freezes as
`causal-conv1d==1.7.0` with **no `direct_url.json`**. That equals the committed freeze line, so the build-stage
`diff -u` (lines 134–137) and the gpu-target repeat (lines 211–214) can pass. The sdist `__version__` is 1.7.0
and no local-version env is set, so the wheel metadata version is 1.7.0.

**B3 — resolved: torch loads first.** Both import checks now run
`import torch; import causal_conv1d_cuda, causal_conv1d` (lines 128 and 206). I extracted
`torch/lib/libtorch_python.so` from the pinned `torch-2.6.0+cu124` wheel and read its dynamic section:
`DT_NEEDED` includes `libtorch.so`, `libtorch_cpu.so`, `libtorch_cuda.so`, `libc10_cuda.so`,
`libcudart.so.12`, `libc10.so` — i.e. importing torch loads every soname the built causal_conv1d extension needs
(the wheel-side extension's `DT_NEEDED` is that set plus `libtorch_python.so`), so the extension's `dlopen`
resolves without an rpath. This was the missing ingredient for a bare extension import.

**M1 — resolved: `TORCH_CUDA_ARCH_LIST` now drives the gencode list.** The line-118 Python edit replaces the
sdist's hard-coded gencode block with `cc_flag = []`. I ran that exact command-line text (including the
Dockerfile's `\"` quoting) against the pinned sdist: the `s.index` targets match the real file, the patched
`setup.py` **py_compiles**, and no `gencode`/`arch=compute` remains in the CUDA branch (the HIP
`--offload-arch` is only in the unused HIP branch). Running torch 2.6.0's `_get_cuda_arch_flags` on the patched
nvcc argument list with `TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0"` returns exactly
`-gencode=arch=compute_80,code=sm_80`, `…compute_89…`, `…compute_90…`; on the unpatched list it returns `[]`
(env ignored), confirming the edit is both necessary and sufficient. ABI=0 is forced by torch's
`BuildExtension`: the image torch has `_GLIBCXX_USE_CXX11_ABI = False`, so it appends
`-D_GLIBCXX_USE_CXX11_ABI=0` last for both cxx and nvcc; `CXXFLAGS` agrees and
`CAUSAL_CONV1D_FORCE_CXX11_ABI=FALSE` does not override it. The VERSIONS line-224 arch claim is now truthful for
a real compile.

**M2 — resolved: the nm gate fails closed.** Lines 129–130 and 208–209 write `nm -D -C "$C1DSO"` to a file and
then test `! grep -q 'std::__cxx11' <file>`: no pipe, so no SIGPIPE/`pipefail` inversion; if `nm` fails the
chain aborts. Verified directly: a file containing `std::__cxx11` makes the check fail, a clean file passes, and
an `nm` failure aborts (does not pass). The torch-first import above is what makes the nm check reachable on a
good build.

### Residual minors (non-blocking)

- Line-105 comment still says "only the causal-conv1d line differs"; with the name-based install the freeze line
  is identical (`causal-conv1d==1.7.0`), which is exactly what lets the strict diff pass — reword at the next
  touch.
- `TORCH_CXX_FLAGS` remains inert (torch 2.6 `cpp_extension` never reads it); ABI=0 actually comes from torch's
  injected flag plus `CXXFLAGS`. Harmless; annotate or drop.
- "CXX11 ABI 0" in VERSIONS line 224 should read "pre-cxx11 (old) ABI"; the `torch_cxx11_abi` value `False`
  already says it.
- The build log is redirected to a file, so the Actions console will not show nvcc progress; the first CI run
  should be watched via the log/artifact if the job looks quiet.
- The Python edit is inherently text-pinned; it fails closed (`s.index` raises) if the sdist ever changes, which
  is acceptable given the sha pin. Optional belt-and-braces: assert the patched text contains `cc_flag = []`
  and/or that the log shows `building 'causal_conv1d_cuda' extension` (not "Guessing wheel URL") before the
  long nvcc step.
- CI-only residual: the actual nvcc compile for sm80/89/90 (3 `.cu` × 3 archs, `MAX_JOBS=$(nproc)` on a
  4-vCPU/16 GB runner) and its memory/time are first exercised by the build; the 300-min timeout is ample, but
  lower `MAX_JOBS` to 2 if the runner OOMs.
- Process: the cpu target still gets a new digest from the rebuild although its inputs are unchanged (base
  re-resolution); the R1-TRACKP-IMAGE-V22 "I2 only if the CPU image changes" call is still due once the digest
  exists.

### Workflow (round 2)

Unchanged from the round-1 reviewed file (`sha256 2e7605df…`), so all four round-1 checks still hold: the
`htc-image-v2.2-*` push trigger, the `20261124-v2.2-<sha8>` tag prefix, workflow-token-only ghcr login (no
secret/credential change), both gpu/cpu targets with digest recording, and no git-main push. The YAML still
parses. A push of `3c54a0e8` would tag `20261124-v2.2-3c54a0e8`.

### Round-2 judgment

Every round-1 blocker and both majors are addressed, and the mechanisms are verified against the exact pinned
sdist, the pinned `uv 0.13.6` and the pinned `torch 2.6.0+cu124` wheel. No new defect was found; the remaining
items are comments/wording or CI-observability notes. **ACCEPTED** for push/build.

## Round 1 (commit `c04be5e4`) — NOT ACCEPTED (historical; superseded by Round 2 above)

**NOT ACCEPTED. Do not push the branch and do not start the GitHub Actions build.** The workflow half of the
diff is correct and the pinned sdist is authentic, but the Dockerfile does not build `causal_conv1d` from source
at all: the pinned sdist's own `bdist_wheel` command (`CachedWheelsCommand`) downloads the **same broken
prebuilt wheel v2.1 pinned** and installs it, so the new import check would fail with exactly the
v2.0/smoke-759983 cxx11-ABI error. Even if that were corrected, two further defects stop the build: a
local-sdist install records a PEP 610 direct URL that breaks the sorted-freeze `diff`, and the literal
`import causal_conv1d_cuda, causal_conv1d` order cannot load the extension before torch. In addition,
`TORCH_CUDA_ARCH_LIST` is silently ineffective for this sdist (so the planned VERSIONS arch record is false),
and the `nm` gate is fail-open under `set -o pipefail`.

## Artifacts reviewed

| file | sha256 at `c04be5e4` (reviewed) | sha256 at `006fc315` (v2.1 base) |
|---|---|---|
| `r1/scripts/htcondor/docker/Dockerfile` | `7f8e0ca61ed646042ce21b7e9e6a9d74995ca0a4896a83468f9634669e789d11` | `a1d73ee95e09381e3fdba41bbbc32335407571ad4224c3fd95e75775bbd947fe` |
| `.github/workflows/r1-htc-image.yml` | `2e7605dfb6904a6fdb1b88334630244fcd1fd2c6963e4a08e94370b1ac6e6a65` | `73bba03a9fb08591cd14b6687873a19a0e3b7e7b0d08b369fc65affccd59e9cf` |
| `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt` (claimed unchanged) | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` | same |

Diff: two files, +29/−12; the whole `apptainer/` directory (freeze, lock, def) is untouched. Line 10 of the
freeze is `causal-conv1d==1.7.0`; the build deps the new source build relies on are in it:
`setuptools==84.2.1` (line 98), `wheel==0.48.0` (line 118), `ninja==1.13.2` (line 59), `packaging==26.2` (line 78).

## Blockers

### B1 — the "source build" is not a compile: the sdist downloads the same broken prebuilt wheel

The pinned sdist (`https://files.pythonhosted.org/packages/f4/d1/eba27735f31bd5527d39a3c7f693e6ded7b844cab275db719a15ad37b6cd/causal_conv1d-1.7.0.tar.gz`,
Dockerfile line 112) is authentic — its sha256 is
`3202758494eaa7b597ce1c282dfa188889506bfcb92cad3c407d26736bfcd32b`, identical to the PyPI JSON digest and to a
local download — but its `setup.py` does **not** compile by default:

- sdist `setup.py:43`: `FORCE_BUILD = os.getenv("CAUSAL_CONV1D_FORCE_BUILD", "FALSE") == "TRUE"`;
- sdist `setup.py:315`: `class CachedWheelsCommand(_bdist_wheel)`, used as the `bdist_wheel` command;
- sdist `setup.py:323–330`: unless `FORCE_BUILD`, it computes the release-wheel URL and calls
  `urllib.request.urlretrieve(wheel_url, wheel_filename)`; only an `HTTPError` (404) falls back to the real
  build (`setup.py:345`, "Precompiled wheel not found. Building from source...").

With the image's torch (2.6.0+cu124, `torch._C._GLIBCXX_USE_CXX11_ABI = False` per
`docs/r1/reports/trackp_v22_20261123/V22_BUILD_STOP_20261123.md`) the computed URL is exactly
`https://github.com/Dao-AILab/causal-conv1d/releases/download/v1.7.0/causal_conv1d-1.7.0+cu12torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl`
(the v2.1 pin). That asset responds 302→200 with `content-length: 196306803` and sha256
`5a76a78af8b600dac20cfc017bb45b7b650d27322f1d8f9250b28e51f6bf9ea9` (verified locally), i.e. the wheel whose
binary is cxx11-ABI (27 `NSt7__cxx11` dynamic symbols; the undefined
`_ZN3c106detail14torchCheckFailEPKcS2_jRKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE` from smoke 759983).

The Dockerfile sets no `CAUSAL_CONV1D_FORCE_BUILD` (only `TORCH_CUDA_ARCH_LIST`, `MAX_JOBS`, `CXXFLAGS`,
`TORCH_CXX_FLAGS` at lines 114–116), so `uv pip install … /tmp/causal_conv1d-1.7.0.tar.gz` builds the sdist,
whose `bdist_wheel` downloads and installs that wheel. **No `nvcc` call happens.** I confirmed that uv's sdist
build really runs the project's `bdist_wheel` cmdclass: with the pinned `uv 0.13.6` + setuptools 84.2.1 +
wheel 0.48.0, a scratch sdist whose `bdist_wheel` subclass prints a marker shows in the `--verbose` log:
`Calling setuptools.build_meta.build_wheel(...)`, `running bdist_wheel`,
`CACHED-WHEELS-HOOK-REACHED: would download a prebuilt wheel here` — that is the exact hook causal_conv1d
overrides.

Consequences: after the import-order issue (B3) is fixed, line 118 (`import causal_conv1d_cuda, causal_conv1d`)
fails with the same cxx11-ABI `torchCheckFail` error; CI is red. If GitHub ever returned 404 for the asset the
build would instead switch to a real compile and then hit B2/B4 — so the mechanism is also nondeterministic.

This also explains the earlier "source build": image v2 (commit `e1cb6d8e`, Dockerfile line 108) installed the
same sdist via `--no-binary causal-conv1d --no-build-isolation 'causal-conv1d==1.7.0'`, and its extension was
cxx11-ABI. torch's `BuildExtension` *always* appends `-D_GLIBCXX_USE_CXX11_ABI=<int(torch._C._GLIBCXX_USE_CXX11_ABI)>`
(`cpp_extension.py:951–953`, applied at `573–574`), so a genuine compile against torch ABI=False cannot emit
cxx11-ABI symbols; the v2 artifact was therefore the wheel fetched by the same shortcut. v2.2 as written
reproduces it.

Fix: set `CAUSAL_CONV1D_FORCE_BUILD=TRUE` for the build command (optionally `CAUSAL_CONV1D_SKIP_CUDA_BUILD=FALSE`)
and fail the build if the captured log contains "Guessing wheel URL:"/"Precompiled wheel not found" or lacks a
compile banner.

### B2 — the install form breaks the sorted-freeze gate in both stages

A local sdist path is a direct-URL requirement: uv records PEP 610 `direct_url.json` and `uv pip freeze` prints
`causal-conv1d @ file:///tmp/causal_conv1d-1.7.0.tar.gz`, not `causal-conv1d==1.7.0`. The `diff -u` at
Dockerfile lines 122–125 (and the identical check in the final gpu target, lines 198–201) then fails; the RUN
aborts before VERSIONS. Reproduced with the pinned `uv 0.13.6`: a scratch sdist installed with
`uv pip install --no-deps --no-build-isolation /tmp/…/demo_init_pkg-1.7.0.tar.gz` freezes as
`demo-init-pkg @ file:///tmp/…/demo_init_pkg-1.7.0.tar.gz` (with
`direct_url.json: {"url":"file:///…","archive_info":{}}`), while the wheel built from the same sdist and
installed by requirement name from `--find-links` freezes as `demo-init-pkg==1.7.0`.

This is exactly the property v2.1 relied on and documented: the wheel was installed "by requirement name
(`--no-index --find-links`) so `uv pip freeze` still reports `causal-conv1d==1.7.0` and the committed-freeze
diff is unchanged" (`docs/r1/reports/trackp_h200_20261118/V21_IMAGE_006FC315.md`). v2.2 changed the install
shape and lost it.

Fix: build a wheel from the verified sdist into a local wheelhouse (with `FORCE_BUILD=TRUE`), then
`uv pip install --python "$TP" --no-deps --no-index --find-links /tmp/wheels 'causal-conv1d==1.7.0'` (the v2.1
pattern), so the freeze line stays `causal-conv1d==1.7.0`. Do not paper over it by deleting `direct_url.json`.

### B3 — the import check as written cannot load the extension before torch

`import causal_conv1d_cuda, causal_conv1d` (Dockerfile line 118; repeated at line 194) imports the compiled
extension first. The sdist builds it as a torch `CUDAExtension`, which links `-lc10 -ltorch -ltorch_cpu
-ltorch_python -lcudart -lc10_cuda -ltorch_cuda` (`cpp_extension.py:1133–1148`), so the `.so` has
`DT_NEEDED` `libc10.so`, `libtorch.so`, `libtorch_cpu.so`, `libtorch_python.so`, `libcudart.so.12`,
`libc10_cuda.so` — verified on the v1.7.0 wheel's `causal_conv1d_cuda.cpython-312-x86_64-linux-gnu.so`; a
source build uses the same link line. For setup.py builds torch does not add an rpath to `torch/lib` (the
`-Wl,-rpath,{TORCH_LIB_PATH}` at `cpp_extension.py:1980` is in the JIT path only); the wheel's only
`DT_RUNPATH` is the build runner's Python lib dir (`/opt/hostedtoolcache/Python/3.12.14/x64/lib`). The image
sets no `LD_LIBRARY_PATH` for `torch/lib` (the gpu `ENV`, Dockerfile lines 189–190, is llama only). A bare
extension import before `import torch` therefore fails at loader time with
`libc10.so`/`libtorch_python.so: cannot open shared object file`, even on a correct ABI build. Every existing
import path (the staged smoke, diagnostic 759916) imports torch first, which is why they reached the ABI error
and this check would not.

Fix: `import torch, causal_conv1d_cuda, causal_conv1d` (torch first), or `import causal_conv1d` first (its
`causal_conv1d_interface` imports torch before the extension); keep importing both modules as the row requires.

## Major issues (must be fixed or the record corrected before the image is accepted)

### M1 — `TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0"` has no effect on this sdist, and the VERSIONS arch line would be false

`torch.utils.cpp_extension._get_cuda_arch_flags(cflags)` returns `[]` when any nvcc flag already contains
`"arch"` (`cpp_extension.py:2016–2024`), and the sdist's `setup.py` always appends explicit gencode flags
`arch=compute_75,code=sm_75`, `compute_80`, `compute_87` and, for CUDA ≥ 11.8, `compute_90`. With CUDA 12.4 the
fatbin of a real source build would be **7.5/8.0/8.7/9.0**, not 8.0/8.9/9.0. Dockerfile line 211
(`env3_causal_conv1d_arch=8.0;8.9;9.0 (source build, CXX11 ABI 0)`) would therefore record an arch set the
binary does not contain. Functionally H200 (sm_90) is covered and L40S (sm_89) should still load the sm_87
cubin under NVIDIA's minor-revision binary compatibility (a cubin for X.y runs on X.z with z ≥ y), but the
authority's explicit arch configuration is not what gets built.

Fix: patch the sdist's gencode list (build exactly compute_80/89/90) or delete the hardcoded gencode block so
the torch env var takes effect, and record the true list. Optionally assert the fatbin contains the required
targets.

### M2 — the `nm` gate is fail-open under `set -o pipefail`

Dockerfile line 119 (and 196): `&& ! nm -D -C "$C1DSO" | grep -q 'std::__cxx11'`. With the stage's
`set -euo pipefail`, `grep -q` exits on the first match and `nm` then dies of SIGPIPE (141); `pipefail` makes
the pipeline status 141 and `!` turns that into **success**, so the gate passes in the very case it must
reject. Demonstrated: `set -euo pipefail; ! seq 1 300000 | grep -q 1` succeeds although the pattern is present
(it only works for streams smaller than the pipe buffer; `nm -D -C` output for this `.so` is ≈206 kB). The gate
also passes silently if `nm` is missing or errors (exit 127 / non-ELF → grep 1 → pipeline 1 → `!` → 0).
`nm` availability itself is fine: binutils is present in the v2/v2.1 gpu image (`V21_DIAGNOSTIC_759916.md`:
`binutils-2.35.2-42.el9_3.1`, `/usr/bin/ld` present on the gpu image), and the build stage has gcc-c++/
binutils — the defect is the shell construction.

Fix: capture first, then test, e.g. `NM_OUT="$(nm -D -C "$C1DSO")"` (aborts under `-e` if nm fails) followed by
`if printf '%s\n' "$NM_OUT" | grep -q 'std::__cxx11'; then echo "STOP: new-ABI symbols"; exit 1; fi`; record
the nm output sha if useful.

## Minors and observations

- **m1 — `TORCH_CXX_FLAGS` is inert.** torch 2.6.0's `cpp_extension.py` has no reference to it, and it is not a
  distutils/setuptools variable. The ABI=0 outcome actually comes from torch's own
  `_add_gnu_cpp_abi_flag` (appended last to `extra_compile_args`, so it wins) plus `CXXFLAGS` (honoured by
  setuptools; verified in a scratch build: the env flag appears early, `extra_compile_args` later). The
  technique is right for a real compile, but the comment/Dockerfile should say so and drop (or annotate) the
  inert variable.
- **m2 — comment/freeze contradiction.** Dockerfile line 103 says "the env3 freeze check below is unchanged:
  only the causal-conv1d line differs (source build at 1.7.0)", but the `diff -u` it describes requires the
  sorted freeze to be byte-identical. With the recommended name-based wheel install the causal line is
  identical (`causal-conv1d==1.7.0`); with the current direct-URL install it is not a version line at all.
  Reword to "identical; the causal line is the same version, installed from the pinned source build".
- **m3 — wording.** Line 211's "CXX11 ABI 0" is the *old/pre-cxx11* ABI; say "pre-cxx11 ABI (torch ABI
  False)" so a later reader does not read it as the new ABI.
- **m4 — process note (not this diff).** The cpu target will get a new digest from the rebuild although its
  inputs are unchanged (base re-resolution; same as v2.1). R1-TRACKP-IMAGE-V22's "I2 only if the CPU image
  changes" needs an explicit call in the next unit once the digest exists.

## Parts verified correct

- **sdist pin:** URL resolves to the PyPI sdist and the sha256 is exactly the pinned
  `3202758494…cd32b` (PyPI JSON and local download agree); the supply-chain pin itself is sound.
- **Build deps:** setuptools 84.2.1, wheel 0.48.0, ninja 1.13.2 and packaging 26.2 are in the committed
  freeze; wheel 0.48.0 still ships the `wheel/bdist_wheel` shim the sdist's `setup.py` imports, so
  `--no-build-isolation` is satisfiable.
- **Failure/diagnostic capture:** `tee` under `pipefail` preserves failure (`{ false; } 2>&1 | tee log` returns
  non-zero and aborts the RUN — verified); the build log is created in the build stage, its sha256 is recorded,
  and log + both sidecar hashes are copied to the gpu target (lines 184, 211–215); VERSIONS records the torch
  ABI and the sdist/so/build-log hashes.
- **env3 change scope:** only `causal-conv1d` changes: the exclusion regex (line 106) and the committed freeze
  file are unchanged; no other env3 package changes.
- **ABI technique (for a real compile):** torch 2.6's `BuildExtension` injects
  `-D_GLIBCXX_USE_CXX11_ABI=0` (torch ABI=False), `CXXFLAGS` is honoured and the injected flag comes last, so
  ABI=0 would be achieved — the problem is that no compile happens (B1), not the flag handling.
- **Glob/paths:** `causal_conv1d_cuda*.so` under `…/site-packages` is the correct path/name for the extension
  (site-packages root, `cpython-312-x86_64-linux-gnu.so`); no missing-path defect.

## Workflow review (4/4 checks pass)

1. **Trigger:** `push.branches` adds `htc-image-v2.2-*`; `htc-image-v2.2-20261124` matches, and the `paths`
   filter (`docker/**`, `apptainer/**`, the workflow file) is touched by this commit. YAML parses
   (`yaml.safe_load`), one `build` job.
2. **Tag:** the `case "$GITHUB_REF_NAME"` maps v2.2 branches to prefix `20261124-v2.2`; this push would tag
   `20261124-v2.2-c04be5e4`. The v2.1/v2 patterns do not overlap.
3. **Secrets/credentials:** no secret or credential change; ghcr login remains the workflow token
   (`secrets.GITHUB_TOKEN`) with `packages: write`; no personal `docker login`.
4. **Targets/digests/main:** both `gpu` and `cpu` build-and-push steps are present and unchanged (YAML check:
   targets `['gpu','cpu']`), the digest record step writes both digests plus dockerfile sha and tag to the
   artifact/step summary, and nothing pushes to git main.

Process note: the workflow fires automatically on the branch push, so the push itself is the trigger; there is
no dry-run mode. Do not push until the Dockerfile blockers above are fixed.

## Conflict with R1-TRACKP-V21-FREEZE

The freeze file is untouched and the only permitted difference remains the `causal_conv1d` line at 1.7.0, so
the source build at 1.7.0 is compatible with the row in principle; the exclusion regex and every other env3
install are unchanged. The problem is the install **form**: a `file://` direct-URL line is not "the same version
number" and breaks the strict build check, which is a stronger requirement than the row. With the recommended
name-based wheel install the line is `causal-conv1d==1.7.0` (identical), so the row's allowance is not needed
for this image — and not violated.

## Round-1 acceptance conditions (all met in Round 2 above)

1. `CAUSAL_CONV1D_FORCE_BUILD=TRUE` (+ a build-log assertion that a real compile happened, not the wheel
   shortcut).
2. Wheel-first install by requirement name so the freeze line stays `causal-conv1d==1.7.0`; no
   `direct_url.json`.
3. torch-first imports in both the build stage and the final gpu stage.
4. Arch flags actually honoured (or the truth recorded) — VERSIONS must state what was built.
5. The `nm` gate rewritten to fail closed.
6. The comment/wording fixes above (and, after a digest exists, an explicit I2 decision).

## Evidence used (read-only)

- `git diff 006fc315..c04be5e4 --stat` / `--name-status` (two files only); file hashes as tabled above;
  `git branch -r --contains c04be5e4` and `git ls-remote --heads origin 'htc-image-v2.2-*'` (empty);
  `git show 44c3d80e:docs/r1/PLAN.md` lines 1385 and 1500.
- `https://pypi.org/pypi/causal-conv1d/1.7.0/json` (sdist filename/digest/URL) and a local download of the
  pinned sdist (`sha256 3202758494…cd32b`); extracted sdist `setup.py` (lines 41–46, 268–346).
- GitHub release asset for `causal_conv1d-1.7.0+cu12torch2.6cxx11abiFALSE-cp312-cp312-linux_x86_64.whl`
  (HTTP 302→200, 196,306,803 B, sha256 `5a76a78a…`); its `.so` parsed for `DT_NEEDED`/`DT_RUNPATH`/dynsym
  with pyelftools.
- `https://raw.githubusercontent.com/pytorch/pytorch/v2.6.0/torch/utils/cpp_extension.py` lines 537–575,
  951–957, 1133–1148, 1980, 2007–2024 (ABI flag injection, link libraries, rpath, arch-flag precedence).
- Pinned `uv 0.13.6` local experiments (sdist `bdist_wheel` hook invocation; direct-URL vs name-based freeze
  lines; `tee`/pipefail and `! … | grep -q` semantics; setuptools `CXXFLAGS` ordering).
- `docs/r1/reports/trackp_v22_20261123/V22_BUILD_STOP_20261123.md`, `docs/r1/reports/release_20261122/I2_MEM_SMOKE_20261123.md`,
  `docs/r1/reports/trackp_h200_20261118/V21_IMAGE_006FC315.md`, `docs/r1/reports/trackp_h200_20261118/V21_DIAGNOSTIC_759916.md`,
  and commit `e1cb6d8e` (image v2 Dockerfile line 108).

Round-2 evidence (new material used only in the final round): pinned `uv 0.13.6` macOS binary from PyPI;
scratch `causal_conv1d`-named 1.7.0 C-extension wheel via `setup.py bdist_wheel -d`; uv 0.13.6 direct-URL vs
name+`--find-links` freeze/direct_url comparison; exact Dockerfile Python-patch line executed against the
pinned sdist + `py_compile`; torch 2.6.0 `_get_cuda_arch_flags` executed on patched/unpatched nvcc flag lists;
`torch/lib/libtorch_python.so`, `libc10_cuda.so` and `libtorch.so` extracted from the pinned
`torch-2.6.0+cu124` wheel via HTTP range requests and their `DT_NEEDED` read; `bash -n` on the changed build
RUN and the final gpu RUN blocks. The round-1 verdict `NOT ACCEPTED` at `c04be5e4` is superseded.

VERDICT: ACCEPTED
