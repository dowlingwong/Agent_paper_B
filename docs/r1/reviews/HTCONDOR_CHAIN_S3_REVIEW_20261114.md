# Independent pre-build review — S3 Apptainer image definition (`r1-htc.def`) — 14 Nov 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author, not the executing agent.

**Date/time:** 14 November 2026, 11:05–11:30 CET, before any build.

**Scope (author instruction S3, 14 Nov 2026):** write and review *before building* an Apptainer
definition file with base `docker://nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` (CUDA chosen from the
lowest driver in `POOL_FACTS`), contents as the original runbook §3 (three fixed `uv` environments +
llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab` with `CMAKE_CUDA_ARCHITECTURES="70;80;89;90"`),
product `/work/dwong/paperb/images/r1-htc-20261114.sif` with SHA-256 and size recorded and a copy under
`/ceph/srv/dwong/paperb/images/`; if `--fakeroot` is needed and unavailable, record a question and STOP
at S3. The deepthought Docker daemon is inactive, so this is the Apptainer route; the earlier Dockerfile
route is not operative.

**Reviewed at commit `df2a8b45`** (branch `htcondor-chain-20261114`; worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-chain-20261114`, clean). Files
reviewed, with the SHA-256 values a build should be held to:

| File | SHA-256 |
|---|---|
| `r1/scripts/htcondor/apptainer/r1-htc.def` | `c394e00230021f9753bdddaf11c70bfab1c366a569628a060f1a627dcece397d` |
| `r1/scripts/htcondor/apptainer/build_sif.sh` | `c6f85ae0afc33254d37a470759df72137520d1d58a54b55e6f27b0c624f7ba4f` |
| `r1/scripts/htcondor/apptainer/capability.def` | `41ae828733634964e0b06692b949016517b6fd4715dc7bff74337ee40070b94c` |
| `r1/scripts/htcondor/apptainer/README.md` | `2e56d14e493a2f82cbbeb1705574b9e25f5601c806ca1cb154887ef9d7873bd5` |
| `uv.lock.a3fedbb` (a3fedbb) | `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` (536 392 B) |
| `pyproject.toml.a3fedbb` (a3fedbb) | `72c4358991b6dfcf291ab0f098b0ab71799945574575c6c8fcdd26c4ba2feba8` |
| `tracks_freeze_65.txt` (TRACKS_HOST_FACTS §0.5) | `f1c818e560b32cc554656c23e1273ae80c0fd770bd1e3df0b5a68bafc0d3a687` (65 lines) |
| `pip_freeze_trackp-cpu.txt` (Track P CPU freeze) | `17da9a3a441919829f2bb5cd1cd0a752725274bfa69cc2b0ca6a8c4fd4388524` (101 lines) |

**Limits of this review.** No SSH, no build, no cluster commands, no execution of the def or the script.
Everything below is a static review plus web checks of the package/index/image facts. Nothing was run on
deepthought; the cluster-side facts (apptainer version, `/etc/subuid`, network reachability from
deepthought, actual build result) are unverified and listed in §6.

---

## 1. What was checked and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | The four S3 files, line by line | `read` | Read in full; line references below are to `df2a8b45`. |
| 2 | The three committed input files vs their provenance | `sha256sum` of the committed copies; GitHub raw fetch of harness `a3fedbb` `uv.lock`/`pyproject.toml`; `origin/docs/runbooks-14nov` copy of the Track P freeze | **All match exactly**: `dd42d018…`, `72c435899…`, `f1c818e5…`, `17da9a3a…`; the harness `uv.lock` is 536 392 B as claimed; the duplicate copies under `docs/r1/reports/htcondor_chain_20261114/s3/` are byte-identical. |
| 3 | Original runbook §3 contents | `git show origin/docs/runbooks-14nov:docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` | The def covers the three environments, llama.cpp and the tool list; the `xrootd-client` tool and the env-3 recipe are the problems (F1–F3). |
| 4 | `%files` sources and syntax | Read + Apptainer source/docs | Sources exist beside the def; Apptainer copies `%files` **before** `%post` and creates missing parent directories (`internal/pkg/build/files/copy.go: makeParentDir` → `os.MkdirAll`), so `/opt/r1/harness/uv.lock` etc. are copied correctly. No finding. |
| 5 | Env 1 recipe (`uv sync --frozen --no-dev --python 3.13`, then `mv .venv`) | Read; `uv.lock` root entry; uv docs | The lock's root project is `source = { virtual = "." }`, so `uv sync` does not need the harness source tree and will not install the project — OK. But pytest is an **optional extra**, not a dev dependency group (F8), and the venv is moved after creation (F9). |
| 6 | Env 2 recipe (65-package freeze, Python 3.11) | `cat tracks_freeze_65.txt` | Line 4 is `-e file:///home/dowling/r1_tracks/work/autoresearch_harness` — an absolute host path that does not exist in the image (F1, **BLOCKING**). |
| 7 | Env 3 recipe (Track P freeze + cu124 torch) | `cat pip_freeze_trackp-cpu.txt`; PyPI JSON for `transformers`/`peft`; pyproject files of the three VCS pins | The freeze contains three VCS requirements (kev @`2074cc4`, laya @`a478221`, startlux-decide @`a99977d`) and the def installs the whole file with dependency resolution. Kev's pinned `pyproject.toml` requires **`numpy>=2.5.3`** while the freeze pins **`numpy==2.4.4`** → resolution cannot succeed; the Track P handoff says these repos were installed `--no-deps` (F2, **BLOCKING**). |
| 8 | Proposed cu124 torch | `download.pytorch.org/whl/cu124/torch/` index pages | cu124 has **only** torch 2.5.0, 2.5.1 and 2.6.0 (no 2.x ≥ 2.7; `2.14` count = 0). `torch==2.14.1` from cu124 **cannot exist**; the fallback `torch` installs the newest cu124 wheel = **2.6.0+cu124**, which is exactly the documented Track P GPU venv torch (`STATUS` L607: torch 2.6.0+cu124, transformers 5.19.0) and satisfies kev's `torch>=2.6,<2.9` (F7). |
| 9 | `dnf` package names against Rocky 9 | Rocky 9 BaseOS/AppStream package indexes; EPEL 9 index; NVIDIA image config history | `git`, `rsync`, `jq`, `gcc`, `cmake`, `which`, `tar`, `gzip`, `curl`, `findutils` exist in Rocky 9 BaseOS/AppStream (jq 1.6 is in BaseOS). **`xrootd-client` exists only in EPEL 9**; the nvidia base image history shows only `cuda.repo` and yum installs — no EPEL repo/`epel-release` — so the first `%post` line fails (F3, **BLOCKING**). `awk` is used by the def's VERSIONS block but not installed (F15). |
| 10 | Base image and driver window | Docker Hub tag check; `POOL_FACTS.md` (last night) §2; NVIDIA CUDA compatibility | `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` exists (HTTP 200). CUDA 12.4 requires driver ≥ 550.54.14. Measured pool drivers (CUDA version): TITAN X **12.0** (deepthought, driver 525.147.05), L40S 12.8/13.4, A100 13.3, V100S 13.0, H200 13.4 → 12.4.1 is compatible with every in-scope class but **not** with the TITAN X; the arch list `70;80;89;90` also excludes the TITAN X (sm_52). See §3 (F6) for the required scope statement. |
| 11 | `build_sif.sh` safety and records | Read; `grep` for `rm`; record steps | Capability test does not test root (F4); `rm -f "$CAP"` is a deletion (F5); the capability retry can hit "file exists" (part of F5); post-build records can fail silently while the script still exits 0 (F13); the product path, SHA-256/size, inspect, VERSIONS, mirror copy and log are all present. |
| 12 | Credentials / network at job time | `grep` of the def/script; URL review | No secrets, tokens, `docker login`, `~/.docker/config.json`, `.netrc` or key reads; only public https/git/PyPI URLs. The design needs no network at job time (all envs and llama.cpp are built at image-build time). |
| 13 | Feasibility | Last night's `POOL_FACTS.md` §3; estimated image contents | `/work` = 1.4 T with **1.1 T available**; `/ceph` 346 T available. Estimated final SIF 15–25 GB (base + three envs + CUDA torch + llama.cpp), build time ≈ 1–2 h; it fits. UV cache and `/tmp` are the two size/time risks (F11). |
| 14 | llama.cpp commit / flags / arch | GitHub API; runbook §3 | Commit `620d2225…` exists publicly; `-DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="70;80;89;90"` is buildable with CUDA 12.4 (compute capabilities 5.0–9.0) and Rocky 9 gcc 11.5; the binary SHA is recorded. The `llama-server --version` line is not recorded (F12). |
| 15 | Review authority text | `git grep` in the branch | The S3 instruction itself is only relayed/asserted (README); it is not committed as a document. Not blocking; see N3. |

---

## 2. Findings

Severity: **BLOCKING** = the build as written fails or violates a standing rule and must be fixed
before any build; **MAJOR** = a stated S3 requirement is not met as written (fix before build);
**MINOR** = correctness/robustness that should be fixed now; **NIT** = wording/records.

| ID | Sev | Where | Evidence and finding | Exact fix |
|---|---|---|---|---|
| **S3-F1** | **BLOCKING** | `r1-htc.def` L41; `tracks_freeze_65.txt` L4 | Env 2 runs `uv pip install -r /opt/r1/locks/tracks_freeze_65.txt`; the committed freeze (SHA `f1c818e5…`, the authentic TRACKS freeze) contains `-e file:///home/dowling/r1_tracks/work/autoresearch_harness`. That path does not exist in the image, so the install fails (`uv` cannot build the editable) and `set -eux` aborts the build. | Filter local/editable lines before installing (e.g. `grep -vE '^(-e \|--editable )' tracks_freeze_65.txt > /tmp/tracks_no_editable.txt`), keep the committed file unchanged as provenance, and provide the harness code the way Track S does (PYTHONPATH to a job-time checkout, as `TRACKS_HOST_FACTS` shows) — or commit a harness source archive at `a3fedbb` and install it explicitly. Document the choice in the README. |
| **S3-F2** | **BLOCKING** | `r1-htc.def` L43–58 | Env 3 installs the whole Track P freeze with dependency resolution. The freeze contains VCS requirements `kev @ git+…@2074cc4`, `laya @ git+…@a478221`, `startlux-decide @ git+…@a99977d`; kev's pinned `pyproject.toml` requires `numpy>=2.5.3` while the freeze pins `numpy==2.4.4` (and `kev` requires `torch>=2.6,<2.9`, so the filtered freeze also triggers a PyPI torch install). Resolution cannot satisfy both numpy pins → `uv pip install -r` fails. `TRACKP_CODE_HANDOFF` §Environment records that these three code repos were installed **`--no-deps`** for exactly this reason. Even if resolution happened to succeed, the result would not be the pinned freeze. | Split the recipe: install the pinned non-torch set with `--no-deps` (`grep -vE '^(torch\|.* @ git\+)' … > /tmp/pinned.txt; uv pip install --no-deps -r /tmp/pinned.txt`), install the three VCS repos individually with `--no-deps` at the pinned commits from the freeze, then install the CUDA torch **last** from the pytorch index (F7). Record the three refs and the exact commands in `/opt/r1/VERSIONS.txt` and the README. |
| **S3-F3** | **BLOCKING** | `r1-htc.def` L22–24 | `dnf install -y … xrootd-client …`: `xrootd-client` is EPEL-only (present in the EPEL 9 package index, absent from Rocky 9 BaseOS and AppStream). The base image config history shows only `COPY cuda.repo` and `yum install cuda-*`; EPEL is neither installed nor enabled. The first `%post` line therefore fails ("No match for argument") and the build aborts. | Install EPEL first (`dnf install -y epel-release` or the `epel-release-latest-9` rpm) and then `xrootd-client`, or drop `xrootd-client` from tonight's image (I1–I4 are deferred by the chain's errata) and record it as a question/add it next window. Keep the committed def's provenance in mind: this edit changes the reviewed def SHA. |
| **S3-F4** | **MAJOR** | `capability.def`; `build_sif.sh` L18–32 | The "capability test" builds a trivial `scratch` def whose `%post` just writes `/capability.txt`. A plain (non-`--fakeroot`) setuid build can succeed for that def while `%post` runs as the invoking user; the real def's `dnf`/`uv` installs into `/opt` then fail. So the script can set `MODE=plain` and never try `--fakeroot`, defeating the S3 rule "if `--fakeroot` is needed and unavailable, record a question and STOP at S3". A failed plain attempt followed by `--fakeroot` to the same path can also hit apptainer's "file exists" refusal (no `--force`). | Make the capability test a **privilege** test: e.g. `capability.def` `%post` does `test "$(id -u)" -eq 0 && echo fakeroot-ok > /capability.txt` (or `id -u` written to a file and checked after `apptainer exec`), and test `--fakeroot` **first**; if `--fakeroot` yields uid 0 use it, else try plain only if it can install (unlikely), else `say "STOP: no root-capable build mode; question recorded"` and exit 2. Leave the failed test SIF in place. |
| **S3-F5** | **MAJOR** | `build_sif.sh` L20, L41 | (a) `rm -f "$CAP"` is a deletion and the author's standing rule is no deletion anywhere; the S3 review criterion says failed temp SIFs are left in place and `mv` happens only after success. (b) `mv "$TMP" "$SIF"` overwrites an existing product on a re-run (destroys the previous SIF without retiring it). | Use a unique capability path (`_capability_test.<UTC>.sif`) instead of `rm`; at the product step, if `"$SIF"` already exists, move it to `r1-htc-20261114.prev_<UTC>.sif` (or a `_to_delete` beside it) and record it, never delete; only then `mv` the new temp into place. Keep the failed-temp behaviour already present (L39). |
| **S3-F6** | **MAJOR** | `r1-htc.def` L2; README | Driver/scope: CUDA 12.4 requires driver ≥ 550.54.14. The measured pool has **TITAN X at CUDA 12.0 (driver 525.147.05)** on deepthought — incompatible with both the 12.4.1 base and `cu124` torch — plus L40S 12.8/13.4, A100 13.3, V100S 13.0, H200 13.4. The arch list `70;80;89;90` also excludes the TITAN X (sm_52), so the image is by design for the other classes; but the S3 instruction says "base per the lowest driver in `POOL_FACTS`", and the lowest measured is 12.0. Nothing in the README records this. | Add a short "Driver window / scope" section: the TITAN X (deepthought, driver 525/CUDA 12.0, cc 5.2) is **out of scope** and cannot run this image; the lowest **in-scope** driver is 12.8 (≥ 550), so 12.4.1 is the right base and no lower CUDA base is needed. Record it as an author question (S3 wording) in the question list and in `VERSIONS.txt`. If the author actually wants the TITAN X, that is a different (and currently impossible) torch/CUDA choice — put it to the author instead of guessing. |
| **S3-F7** | **MAJOR** | `r1-htc.def` L44–58; README L18 | The `proposed:` torch `2.14.1` from the cu124 index **does not exist** (cu124 tops out at 2.6.0), so the first branch always fails and the unpinned fallback silently installs 2.6.0+cu124. That fallback is actually the correct, documented value (Track P GPU venv: torch 2.6.0+cu124, `STATUS` L607; it satisfies kev's `torch>=2.6,<2.9` and transformers 5.19 needs only `torch>=2.5`), but the recipe as written is not pinned and the README records the wrong `proposed:` value. | Pin `torch==2.6.0+cu124` from the cu124 index as the `proposed:` choice (note the source: `STATUS` L607 / `TRACKP_PHASE2_ENV_PINS_TASL7`), drop the unpinned `torch` fallback (or keep it only as a recorded last resort), and make the README say "proposed: torch 2.6.0+cu124; author ruling before production". Also record the resolved version (`torch_actual`) — already in VERSIONS. |
| **S3-F8** | **MAJOR** | `r1-htc.def` L36 | Env 1 has no pytest. `pyproject.toml.a3fedbb` puts `pytest>=8.0.0` in `[project.optional-dependencies] dev`; `uv sync --no-dev` only disables a `[dependency-groups] dev` group (none here) and does not enable extras, so pytest is absent. The reviewed I2 determinism command runs **pytest** in the harness environment (B1 reviews: pytest 9.0.3, harness `a3fedbb`), so I2 cannot run in env 1 as built. | Change to `uv sync --frozen --extra dev --python 3.13` (or `--all-extras`), record `python -m pytest --version` in VERSIONS; keep `--no-dev` only if a real dependency group is added. |
| **S3-F9** | **MAJOR** | `r1-htc.def` L36–37 | `uv sync` creates `/opt/r1/harness/.venv` and the def then `mv`s it to `/opt/r1/envs/harness`. uv venvs are not relocatable by default: console scripts and `activate` embed the old path (Python imports via `bin/python` may still work, but the recipe is fragile and any script usage breaks). | Set `export UV_PROJECT_ENVIRONMENT=/opt/r1/envs/harness` before `uv sync` so the venv is created at its final path (uv supports this env var; verified in the uv docs), and drop the `mv`. If a move must stay, use a relocatable venv and say so. |
| **S3-F10** | **MAJOR** | `r1-htc.def` L32, L48 | Env 3 uses Python **3.13**, but the Track P CPU freeze was created in **Python 3.12.15** (`TRACKP_CODE_HANDOFF` L9) and the freeze's pins are resolved for it; the recipe records no justification. Kev's `requires-python = ">=3.12,<3.14"` allows 3.13, so this is not a certain failure, but the environment is not the pinned one and some 2026 pins may lack cp313 wheels. | Use `uv python install 3.12 …` and `uv venv --python 3.12` for env 3 (matching the freeze's provenance), or record the 3.13 deviation as `proposed:` with the author question. Keep env 1 at 3.13 and env 2 at 3.11. |
| **S3-F11** | **MAJOR** | `r1-htc.def` `%post`; `build_sif.sh` | No uv cache control: env installs cache wheels in `/root/.cache/uv` inside the image; the torch/nvidia wheels are multi-GB, so the SIF grows by several GB and build time increases (worse while F2/F7 pull a PyPI torch before the cu124 one). No `APPTAINER_CACHEDIR`/`APPTAINER_TMPDIR`: `POOL_FACTS` says `/tmp` is 127 G on the root FS; a 15–25 GB SIF build plus docker-layer cache plus double torch download can approach that and the PLAN (`R1-BX-REVISIONS` (g)) explicitly says to put these under `/ceph/dwong`. | In `%post`: `export UV_NO_CACHE=1` (or a cache dir under `/tmp` plus `uv cache clean` before the end of `%post`; build-cache cleanup is not author data) and record the cache policy. In `build_sif.sh`: `export APPTAINER_CACHEDIR=/work/dwong/paperb/apptainer-cache` and `export APPTAINER_TMPDIR=/work/dwong/paperb/apptainer-tmp` before the build, and log the disk/free check. |
| **S3-F12** | **MAJOR** | `build_sif.sh` L42–49; `r1-htc.def` L67–84 | Required record/verification gaps: `llama-server --version` is never recorded (the runbook §4.4 and S3 check (c) expect the version line); `apptainer --version`, the base-image digest, and the build start/end time are not recorded; no post-build smoke test of the three envs or the binary. | Add to `build_sif.sh` after a successful build: `apptainer --version`, `apptainer exec "$SIF" llama-server --version`, `apptainer exec "$SIF" <env>/bin/python -c 'import numpy, sklearn'` for env 1, tracks import for env 2, `import torch; print(torch.__version__)` for env 3; record them in `r1-htc-20261114.VERSIONS.txt` and the identity file; record the base digest (from the build log / `apptainer inspect`) and the build duration. |
| **S3-F13** | **MAJOR** | `build_sif.sh` L44–49 | `apptainer inspect` output, the VERSIONS copy, the mirror copy and the identity file are guarded with `&&` inside a script without `set -e`; a failed inspect/VERSIONS/mirror leaves the script exiting 0 with a missing required record or mirror copy (the S3 requires both). | After each step check the result explicitly and `say "STOP: …"` + `exit 3` on failure, leaving all artifacts in place. Verify the mirror copy SHA against the local SHA and record both. |
| **S3-F14** | **MAJOR** | `README.md` | (a) The "Build" line is the raw `apptainer build r1-htc-20261114.sif r1-htc.def`, which bypasses the capability gate, the SHA/size records and the mirror copy — the reviewed build path is `build_sif.sh --build`. (b) "Build inputs are committed so the SIF is reproducible" is overstated: the base tag is mutable, llama.cpp is cloned from the network, and the torch fallback was unpinned. (c) No `--fakeroot` prerequisite/STOP, no driver/scope statement, no size/time estimate, and no job-time usage example (`apptainer exec --nv … <env>/bin/python`). | Point the Build section at `./build_sif.sh --build`; replace "reproducible" with "inputs pinned; base tag recorded; the SIF is not bit-reproducible"; add the fakeroot prerequisite + STOP, the driver/scope paragraph (F6), an expected-size/time line, and one usage example per environment. |
| **S3-F15** | **MINOR** | `r1-htc.def` L80–83 | The VERSIONS block uses `awk`, which is not in the dnf install list; `grep` is also used but not installed explicitly. Rocky 9 has `gawk` and `grep` packages, but whether the nvidia base image already contains them is unverified; a missing `awk` fails the build at the very end. | Add `gawk grep` to the `dnf install` list (harmless if already present), or rewrite the VERSIONS block without awk. |
| **S3-F16** | **MINOR** | `build_sif.sh` L11 | `mkdir -p "$IMG_DIR" "$MIRROR"` runs even when the script is invoked without `--build` ("dry plan"), creating `/ceph/srv/dwong/paperb/images` before any approval-to-build; on this pool that is a write to shared storage. | Move the `mkdir -p` after the `--build` check, or make the dry plan print the intended paths only. |
| **S3-F17** | **MINOR** | `build_sif.sh` L8; README | The S3 deliverable requires the copy under `/ceph/srv/dwong/paperb/images/`, but `/ceph/srv/dwong` does not exist yet (`POOL_FACTS` §3: `/ceph/srv` exists world-writable, no `dwong` dir) and the script's `mkdir -p` failure is not fatal (F13). | State in the README that the mirror directory is created on first build; make the `mkdir`/copy failure fatal (F13); record the mirror path and SHA in the identity file. |
| **S3-F18** | **NIT** | `build_sif.sh` L4 | `set -uo pipefail` without `-e` is deliberate for the manual RC handling, but a failed `sha256sum`/`mkdir` is not caught. | Fine to keep, but add explicit checks for the commands whose failure would invalidate the record (F13). |
| **S3-F19** | **NIT** | `r1-htc.def` L13–17 | `%files` relative sources resolve against the build working directory; `build_sif.sh` cds to the def's directory (good), but the README's raw build command only works from that directory too. | Note in the README that the build must run from `r1/scripts/htcondor/apptainer/` (or always use `build_sif.sh`). |
| **S3-F20** | **NIT** | `build_sif.sh` L13, L48 | The reviewed def SHA (`c394e002…`) is not compared with the def actually built; the identity records the def SHA but the build would silently proceed on an edited def. | Record the reviewed SHA in the README/identity and have `build_sif.sh` warn/stop if the def SHA differs from the reviewed value (a one-line `diff` or string comparison), unless a new review accepted the edit. |
| **S3-F21** | **NIT** | The branch | The author's S3 instruction text (14 Nov) is not committed; the README and this review rely on the relayed text. | Commit the instruction text (or a one-paragraph record of it) next to the def for provenance. |

---

## 3. Base and driver compatibility (S3 check (d))

The measured pool's GPU driver window (last night's `POOL_FACTS.md`, §2):

| Site / class | GPU | Driver (CUDA version) | Compatible with CUDA 12.4.1? |
|---|---|---|---|
| deepthought | GeForce GTX TITAN X (cc 5.2) | **12.0** (driver 525.147.05) | **No** — needs ≥ 550.54.14; also sm_52 is not in the arch list |
| deepthought2 | L40S | 12.8 | Yes |
| NEMO2 | L40S, H200 | 13.4 | Yes |
| TOpAS | Tesla V100S-PCIE-32GB | 13.0 | Yes |
| TOpAS | NVIDIA A100-PCIE-40GB | 13.3 | Yes |

**Determination:** the 12.4.1 base and the `cu124` torch are compatible with every GPU class this image
is built for (L40S/A100/V100S/H200), and with the L40S on deepthought2 (driver 12.8 ≥ 550.54.14). A
*lower* CUDA base is not needed for those classes; it would not rescue the TITAN X anyway (torch 2.6/cu124
needs ≥ 550, and no current torch build targets CUDA 12.0). The TITAN X is incompatible and outside the
arch list, so it must be recorded as out of scope and as an author question — the S3 phrase "base per the
lowest driver in `POOL_FACTS`" reads as 12.0 unless the scope exclusion is stated (S3-F6).

---

## 4. Safety, credentials and standing rules

- **No deletion:** only one `rm` exists, `rm -f "$CAP"` in `build_sif.sh` (S3-F5); the failed real-build
  temp is left in place (L39) as required. Fix S3-F5 and the failed-temp policy holds.
- **No secrets / no credentials:** the def and script use only public https/git/PyPI URLs; there is no
  `docker login`, no credential-file read, no token, and the S3 inputs contain no secrets. (grep hits are
  package names such as `tiktoken`/`tokenizers`.)
- **No Paper B data:** the image contains no code checkouts beyond the llama.cpp source it builds and the
  Track P training packages installed from the committed freeze; no models, data or experiment outputs.
  The `kev`/`laya`/`startlux` packages are the runbook §3 "Track P training packages"; record that they
  are installed from their pinned commits.
- **Job-time no-network:** true by design — every environment and llama.cpp are built at image-build
  time; jobs need only the SIF. Keep it this way when fixing F7 (no runtime installs).
- **Product identity:** the product path, SHA-256, size, `apptainer inspect`, VERSIONS copy, local log
  and `/ceph/srv` mirror are all present in the plan; F12/F13 tighten the records and their failure
  handling.

---

## 5. Feasibility (S3 check (f))

`/work` had 1.1 T available and `/ceph` 346 T (`POOL_FACTS` §3), so a 15–25 GB SIF plus cache fits;
build time ≈ 1–2 h is plausible on deepthought. The two things that can push size/time are the missing
cache control (F11) and the unpinned/duplicate torch path (F2/F7); both are fixed by the minimal fixes.
`/tmp` (127 G, root FS) is the one local-space risk if the Apptainer cache/temp dirs are left at their
defaults — fix F11. The image is read at job time only from inside the SIF, so no network is needed then.

---

## 6. What this review could not check (no SSH, no build, by rule)

- The apptainer version and whether `--fakeroot` actually works on deepthought (the `/etc/subuid` /
  subgid and setuid state); the capability gate fix is what will establish it.
- Network reachability from deepthought to astral.sh, GitHub, PyPI and `download.pytorch.org`, and the
  actual download/install behaviour of the three environments.
- Whether every 2026 pin has a cp313 wheel (relevant to F10) and whether the Track P GPU venv on TASL-7
  is Python 3.12 (the CPU freeze provenance is 3.12.15; the GPU venv's Python version is not recorded in
  the files I could read).
- The `docker info`/apptainer state, L40S/H200 device names and drivers were taken from last night's
  `POOL_FACTS.md`; they are not re-measured here.
- Any actual build result, SIF size, or run on the pool.

---

## 7. Verdict

VERDICT: NOT ACCEPTED

**Minimal fixes before the build may start** (the BLOCKING/MAJOR items; the MINOR/NIT items can be
folded in the same edit and the def SHA re-recorded):

1. **S3-F1** — filter the `-e file:///home/dowling/...` line out of the env-2 install and provide the
   harness code explicitly (PYTHONPATH or a committed archive); document it.
2. **S3-F3** — enable EPEL before `xrootd-client`, or drop `xrootd-client` for tonight and record it.
3. **S3-F2 + S3-F7 + S3-F10** — install the Track P pinned set and the three VCS repos with `--no-deps`
   (as the handoff did), pin `torch==2.6.0+cu124` (the documented GPU venv value) as `proposed:`, and
   use Python 3.12 for env 3 (or record the 3.13 deviation); update the README's proposed line.
4. **S3-F4** — make the capability test a real root/`--fakeroot` privilege test (uid-0 check), try
   `--fakeroot` first, and STOP with a recorded question if neither yields root; unique test-SIF names.
5. **S3-F5** — remove the `rm -f` deletion, use unique capability paths, and guard the product `mv`
   against overwriting an existing SIF (retire it, never delete).
6. **S3-F6** — add the driver/scope statement (TITAN X out of scope; lowest in-scope driver 12.8 ≥ 550,
   so 12.4.1 is correct) and the author question on the S3 "lowest driver" wording.
7. **S3-F8 + S3-F9 + S3-F11** — env 1 `--extra dev` (pytest) and `UV_PROJECT_ENVIRONMENT` instead of
   moving the venv; `UV_NO_CACHE` (or cache cleanup) and `APPTAINER_CACHEDIR`/`APPTAINER_TMPDIR` under
   `/work`.
8. **S3-F12 + S3-F13 + S3-F14 + S3-F15** — record `llama-server --version`, apptainer version, base
   digest and build time; make inspect/VERSIONS/mirror failures fatal; fix the README build path,
   "reproducible" claim, fakeroot prerequisite and usage examples; add `gawk grep` to the dnf list.

After those edits the def/build plan should be re-submitted to this reviewer (the def SHA changes), and
only then may `build_sif.sh --build` start. No build was performed and no cluster command was issued by
this review.
