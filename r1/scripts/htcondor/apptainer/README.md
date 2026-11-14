# Paper B R1 HTCondor image — Apptainer route (14 Nov 2026)

**Authority (committed here for traceability, review S3-F21).** The author's 14 Nov 2026 instruction S3, verbatim intent: *"构建 SIF：写 `r1/scripts/htcondor/apptainer/r1-htc.def`，以 `docker://nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` 为底（CUDA 版本按 POOL_FACTS 里的最低驱动定）；内容同原 runbook §3：用 uv 建三套固定环境，加上 llama.cpp `620d2225`（CUDA arch 70;80;89;90）。def 文件先审查，再执行 `apptainer build`（如需 `--fakeroot` 而不可用，记入问题清单并停在这一步）。产物放 `/work/dwong/paperb/images/r1-htc-20261114.sif`，记录 SHA-256 和大小；再复制一份到 `/ceph/srv/dwong/paperb/images/`。"* The deepthought Docker daemon is inactive (Q-D1; author's supplement says do not start it), so this is the `apptainer build` route. The Dockerfile + `docker-daemon://` route and the Docker Hub push are the author's later step (I3), not this one.

**Build gate.** The def must be reviewed by an independent reviewer **before** the build; `build_sif.sh --build` refuses to run when `REVIEWED_DEF_SHA` is unset or differs from the current def SHA-256 (review S3-R2; the `--build` command always sets it). The script's first action is a capability test whose `%post` asserts uid 0 (so a plain setuid build that cannot install packages is caught, not silently accepted); it tries `--fakeroot` first, then the plain setuid build, and **stops** (exit 2, question recorded) if neither works. This satisfies the author's "if `--fakeroot` is needed and unavailable, record and stop at S3".

**Usage.**
```bash
# plan only (creates nothing):
bash r1/scripts/htcondor/apptainer/build_sif.sh
# build (only after the reviewer accepts the def and its SHA-256):
REVIEWED_DEF_SHA=<reviewed def sha256> bash r1/scripts/htcondor/apptainer/build_sif.sh --build
```
The build writes `r1-htc-20261114.sif` plus `r1-htc-20261114.{build.log,identity,VERSIONS.txt,inspect.txt,smoke_env1,smoke_env2,smoke_env3,smoke_llama}` under `/work/dwong/paperb/images/`, and copies the SIF + identity + VERSIONS to `/ceph/srv/dwong/paperb/images/` (mirror SHA checked). **No deletion anywhere:** a previous SIF is retired to `*.retired_<UTC>`, a failed build leaves its temp SIF in place, and no `rm` is used.

**Files.**
| File | Purpose |
|---|---|
| `r1-htc.def` | the Apptainer definition (reviewed before any build) |
| `build_sif.sh` | capability gate, build, fatal records, mirror copy |
| `capability.def` | tiny uid-0 test def used by the gate |
| `uv.lock.a3fedbb`, `pyproject.toml.a3fedbb` | harness lock/project at harness commit `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (env 1) |
| `tracks_freeze_65.txt` | the 65-package freeze, SHA-256 `f1c818e5…` (env 2) |
| `pip_freeze_trackp-cpu.txt` | Track P freeze from `docs/r1/overnight/trackp_code_20261026/` (env 3) |

`%files` paths are relative to this directory (the build must run from here, which `build_sif.sh` does).

**Environments.**
1. `/opt/r1/envs/harness` — Python 3.13, `uv sync --frozen --extra dev` from the harness `uv.lock` at `a3fedbb`. The `dev` extra is included so **pytest** is present (pytest is an optional extra of the harness project, not a default dependency); `UV_PROJECT_ENVIRONMENT` targets the env directly, avoiding a non-relocatable `.venv` move.
2. `/opt/r1/envs/tracks` — Python 3.11, the 65-package freeze with its `-e file:///home/dowling/r1_tracks/work/autoresearch_harness` editable line **dropped** (that path cannot exist in the image; the file stays as provenance). Jobs that need the harness package in this env put the `/work` checkout on `PYTHONPATH` (as S4 does).
3. `/opt/r1/envs/trackp` — Python **3.12** (the Track P freeze provenance, TRACKP_CODE_HANDOFF). The pinned set is installed with `--no-deps` (the freeze is a complete pin set), the three VCS requirements (`kev@2074cc4`, `laya@a478221`, `startlux-decide@a99977d`) are installed with `--no-deps` at their pinned commits (as the Track P hand-off did), then torch last: **`torch==2.6.0+cu124` is `proposed:`** — no committed file pins a cu124 wheel, and 2.6.0+cu124 is the documented Track P GPU value; replace with an author ruling before production use. No silent fallback: if that wheel is unavailable the build fails.

**llama.cpp.** `620d2225cc436ab0b001e3200e590e3b286ef9ab`, `-DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="70;80;89;90"`; the binary SHA-256, commit and `llama-server --version` are recorded in `/opt/r1/{LLAMA_SERVER_SHA256,LLAMA_CPP_COMMIT,VERSIONS.txt}`. The binary will differ from TASL-7's; that is expected.

**Driver scope.** CUDA 12.4 needs driver ≥ 550.54.14. Measured in `POOL_FACTS.md`: L40S 12.8/13.4, A100 13.3, V100S 13.0, H200 13.4 — all compatible. The TITAN X (`12.0` / 525.147.05) is **out of scope** for this image (and its sm_52 is not in the CUDA arch list); this is the question recorded against S3's "lowest driver" wording.

**Size/time.** Expected SIF ≈ 15–25 GB and build ≈ 1–2 h (torch cu124 + CUDA base + llama.cpp build); `/work` had 1.0 T free and `/ceph` 345 T free at 11:02 CET. Build caches are forced onto `/work` (`APPTAINER_CACHEDIR`/`APPTAINER_TMPDIR`) and `UV_NO_CACHE=1` keeps multi-GB uv caches out of the image.

**Job-time usage (no network needed).**
```text
universe = container
container_image = /work/dwong/paperb/images/r1-htc-20261114.sif
```
```bash
# I1-style smoke inside a job:
/opt/r1/envs/harness/bin/python -VV; cat /opt/r1/VERSIONS.txt
# I2-style CPU worker (S4): use env 1 (harness), which is the 0.922225 reference stack
# (Python 3.13, numpy 2.4.4, scikit-learn 1.8.0, pytest 9.0.3). env 2 (tracks) is
# numpy 2.4.6/sklearn 1.9.1/pytest 9.2.0 and env 3 (trackp) is Python 3.12; neither is the reference stack.
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=<paper>:/<harness>/src AR_HARNESS_ROOT=<harness> \
/opt/r1/envs/harness/bin/python -m pytest -v paper/r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic
```

**Not in the image:** code checkouts, models, data, credentials. The build inputs are committed here, so the build **inputs are pinned** (the base image is recorded by tag, not digest, and a SIF is not bit-reproducible); apptainer version, base tag, def SHA and all post-build records are written beside the SIF (review S3-F12/F13/F14/R5).
