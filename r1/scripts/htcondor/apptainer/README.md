# Paper B R1 HTCondor image — Apptainer route (14 Nov 2026)

**Authority.** Author instruction 14 Nov 2026 (S3): base `docker://nvidia/cuda:12.4.1-cudnn-devel-rockylinux9`, contents as `HTCONDOR_PREP_RUNBOOK_20261114.md` §3 (three pinned `uv` environments + llama.cpp `620d2225` with CUDA arch `70;80;89;90`), product `/work/dwong/paperb/images/r1-htc-20261114.sif` with SHA-256 and size recorded and a copy under `/ceph/srv/dwong/paperb/images/`. The deepthought Docker daemon is inactive (Q-D1), so this is the `apptainer build` route; the Dockerfile + `docker-daemon://` route is not used today.

**Files.**
| File | Purpose |
|---|---|
| `r1-htc.def` | the Apptainer definition (reviewed before any build) |
| `uv.lock.a3fedbb`, `pyproject.toml.a3fedbb` | harness lock and project at harness commit `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (env 1) |
| `tracks_freeze_65.txt` | the 65-package freeze, SHA-256 `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687` (env 2) |
| `pip_freeze_trackp-cpu.txt` | Track P freeze from `docs/r1/overnight/trackp_code_20261026/` (env 3) |
| `build_sif.sh` | capability test, build, record SHA-256/size, copy to the mirror |
| `capability.def` | tiny `scratch` def used only to test whether builds work without fakeroot |

**Environments.**
1. `/opt/r1/envs/harness` — Python 3.13, from the harness `uv.lock` at `a3fedbb` (`uv sync --frozen --no-dev`).
2. `/opt/r1/envs/tracks` — Python 3.11, the 65-package freeze.
3. `/opt/r1/envs/trackp` — Python 3.13, the Track P freeze minus its CPU torch wheel, plus a CUDA torch build. **No cu124 torch version is pinned in any committed file, so `torch==2.14.1` from the cu124 index is `proposed:`**; if that exact build is not published the def falls back to the newest cu124 wheel and records it in `/opt/r1/VERSIONS.txt`. Replace with an author ruling before production use.

**llama.cpp.** `620d2225cc436ab0b001e3200e590e3b286ef9ab`, `-DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="70;80;89;90"`; the binary SHA-256 and commit are in `/opt/r1/LLAMA_SERVER_SHA256` and `/opt/r1/LLAMA_CPP_COMMIT` and are echoed into `/opt/r1/VERSIONS.txt`. The binary will differ from TASL-7's build; that is expected.

**Not in the image:** code checkouts, models, data, credentials.

**Build record.** After a reviewed build, `build_sif.sh` writes `r1-htc-20261114.build.log` beside the SIF, records `def_sha256`, `sif_sha256`, `sif_bytes`, `apptainer inspect` output and the `VERSIONS.txt` copy, and copies the SIF to `/ceph/srv/dwong/paperb/images/`. Build inputs are committed so the SIF is reproducible.
