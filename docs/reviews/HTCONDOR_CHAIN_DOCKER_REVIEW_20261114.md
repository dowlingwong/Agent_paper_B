# Independent review — Docker route for the Paper B R1 image (`Dockerfile` + GitHub Actions workflow) — 14 Nov 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the Dockerfile, the workflow or
the Apptainer def; I did not build, push, pull or run any image and did not touch the cluster.

**Date/time:** 14 November 2026, 23:00–23:10 CET (Europe/Berlin).

**Worktree:** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-chain-20261114`,
branch `htcondor-chain-20261114` at **`696be7ad`** when this review was written (the branch advanced from
`0221b37d` during the session; the Docker-route section and the raw copies are in `696be7ad`). The
authoritative Docker-route files are on branch **`htc-image-20261114` @ `74820315f56e8170a8c2aaaa4ddaa5ebdb952551`**
(verified with `git ls-remote`), read with `git show origin/htc-image-20261114:<path>`.

**Artifacts reviewed (SHA-256, as committed):**

| Artifact | Ref | SHA-256 |
|---|---|---|
| `r1/scripts/htcondor/docker/Dockerfile` (144 lines) | `htc-image-20261114` @ `74820315` | `844298f41879d813c147286aa410e3c986fbde2dac913897731bcd6c7d7a1b79` |
| `.github/workflows/r1-htc-image.yml` (102 lines) | `htc-image-20261114` @ `74820315` | `637f82ffbcf1f21908f2b39de97f8fb2db622326c312debfe9e61f7897afd949` |
| `r1/scripts/htcondor/apptainer/r1-htc.def` (accepted def, 124 lines) | both branches | `a5a0c9da4e969548bd4aa902f6ed96191a20d4af4556b653c9582204a6690c25` |
| `raw/Dockerfile.htc-image-20261114.txt`, `raw/r1-htc-image.workflow.yml.txt` (chain-branch copies) | `696be7ad` | byte-identical to the two files above (hashes match) |

**Compared against** (all read in full): the accepted Apptainer def and its accepted review
`docs/r1/reviews/HTCONDOR_CHAIN_S3_REVIEW_20261114.md` (def `a5a0c9da…`, verdict ACCEPTED after
re-review), the chain report `docs/r1/reports/HTCONDOR_CHAIN_20261114.md` §8, the S4/S5 units
(`s4_local_cpu_ghcr.jdl`, `s5_nemo2_gpu_ghcr.jdl`, `s4_run.sh`, `s5_run.sh`), the S5 review, and the four
committed build inputs (`uv.lock.a3fedbb` `dd42d018…`, 536 392 B; `pyproject.toml.a3fedbb` `72c43589…`;
`tracks_freeze_65.txt` `f1c818e5…`, 65 lines; `pip_freeze_trackp-cpu.txt` `17da9a3a…`, 101 lines).

**Limits of this review.** No build, no registry login, no pull, no cluster access, no SSH. I cannot see
the GitHub Actions run, the job summary/artifact or the pushed digests (the chain report §8 records that
the repository is private and the digests must come from the author's job summary/artifact); I also cannot
execute the image. Statements about the built images are therefore **static + web-verified**, not
runtime-verified. The public web checks below were used only for action pins and image tags.

---

## 1. What was checked, and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | The Dockerfile, all 144 lines | read from `git show` | Read in full; line references below are to `74820315`. |
| 2 | The workflow, all 102 lines | read from `git show` | Read in full. |
| 3 | Accepted def vs Dockerfile, step by step | side-by-side comparison | Every version/commit/flag matches; deliberate differences are the multi-stage bases, the dropped build-only tools, the llama.cpp source-tree drop and the `curl` removal (see §3). |
| 4 | The four build inputs vs the def's pins | `git show` piped to `sha256sum`, on the image branch | **All exact**: `dd42d018…` (536 392 B), `72c43589…`, `f1c818e5…` (65 lines), `17da9a3a…` (101 lines). The `tracks_freeze_65.txt` contains the expected `-e file:///home/dowling/…` line, which the Dockerfile filters (same as the def). `pip_freeze_trackp-cpu.txt` contains no editable/local lines, so the env-3 filter only removes the four pinned lines by design. |
| 5 | Chain-branch copies | hashes of `raw/Dockerfile…txt` / `raw/r1-htc-image.workflow.yml.txt` | Byte-identical to `git show` — provenance is intact. |
| 6 | Every `uses:` pin | regex + GitHub API `git/ref/tags/<tag>` | **6/6 are 40-hex commit SHAs and each matches the stated tag**: checkout `11bd7190…` = v4.2.2; setup-buildx `b5ca5143…` = v3.10.0; login `74a5d142…` = v3.4.0; build-push `471d1dc4…` = v6.15.0 (twice); upload-artifact `ea165f8d…` = v4.6.2. No mutable refs. |
| 7 | Workflow permissions / secrets | read + grep | `contents: read`, `packages: write` only; no `id-token`, no `secrets: inherit`; the only secret is `${{ secrets.GITHUB_TOKEN }}` (a token reference, not plaintext); no `docker login` with personal credentials; no credential files. |
| 8 | Base image tags | Docker Hub registry API | All three exist: `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` (amd64 `sha256:9acaa2fe…d17175`, 4.64 GB), `nvidia/cuda:12.4.1-cudnn-runtime-rockylinux9` (amd64 `sha256:fcef8f2f…b8a559`, 2.20 GB), `rockylinux:9` (amd64 `sha256:d644d203…c3a9e0`, 64 MB). The tags are **mutable** (both nvidia tags last pushed 2024-04-24; `rockylinux:9` 2024-05-29) and are not digest-pinned — recorded as a supply-chain note (D5), not a blocker. |
| 9 | Build context / file / targets / platform / tags / digest output | read + first-CI-run evidence in the Dockerfile header | `context: r1/scripts/htcondor/apptainer`, `file: r1/scripts/htcondor/docker/Dockerfile`, `target: cpu`/`gpu`, `platforms: linux/amd64`, `push: true`, tags `ghcr.io/dowlingwong/r1-htc-{cpu,gpu}:20261114-<sha8>`; digest via `steps.{cpu,gpu}.outputs.digest` into `r1-htc-image-digests.txt` + `$GITHUB_STEP_SUMMARY` + artifact. The first CI run reached the `dnf` step (the `curl` conflict documented in the Dockerfile header), which proves the file/context wiring works. |
| 10 | `curl` removal (author-noted change) | def vs Dockerfile + base-image behaviour | The def installs full `curl`; the Dockerfile omits it because the Rocky 9 bases ship `curl-minimal` (the first CI run failed exactly on that conflict). `curl-minimal` provides `/usr/bin/curl`, which is what the `uv` installer needs in the build stage; the runbook §3 tool list is `git, rsync, jq, xrootd-client` (no `curl`), and neither S4 nor S5 calls `curl`. **Consistent; no capability lost for the reviewed jobs.** |
| 11 | Multi-stage correctness | read + Docker COPY semantics | The build stage (CUDA devel base) builds envs 1–3 and llama.cpp; `cpu` (rockylinux:9) copies `/opt/uv`, `/opt/r1/pythons`, envs 1+2, `/opt/r1/harness` (lock+pyproject only) and `/opt/r1/locks`; `gpu` (cudnn-runtime base) copies `/opt/uv`, `/opt/r1/pythons`, all three envs, harness/locks, `/opt/r1/llama` (only `build/bin`) and the two llama record files. No llama.cpp source tree, no code checkout, no model, no data, no credential in either final image. The absolute `/opt/...` paths are identical in build and final stages, so the uv-managed Pythons and venvs stay valid. |
| 12 | Import checks | read | cpu: env1 `numpy, sklearn, pandas, pytest`; env2 `numpy, sklearn, pandas`. gpu: the same for env1/env2 plus `import torch` for env3. Meaningful without a GPU (imports do not initialise CUDA); the absence of a GPU is correctly noted in the gpu stage comment. |
| 13 | `/opt/r1/VERSIONS.txt` vs the def | read | cpu records the image/base/build time/uv/Python versions/lock+freeze hashes; gpu records all of the def's fields **except `llama_server_version`** (D1). `base=` correctly records the runtime base for gpu (a deliberate difference from the def's devel base). |
| 14 | PATH / UV_PYTHON_INSTALL_DIR / LD_LIBRARY_PATH | read | Envs match the def's intent: `PATH=/opt/uv:$PATH` (cpu) and `PATH=/opt/uv:/opt/r1/llama/bin:$PATH` (gpu, replacing the def's `/opt/r1/llama.cpp/build/bin`); `UV_PYTHON_INSTALL_DIR=/opt/r1/pythons`; gpu adds `LD_LIBRARY_PATH=/opt/r1/llama/bin` — essential because llama.cpp's build-tree RUNPATH points at the (absent) source tree, and the copied `build/bin` carries `libggml*`/`libllama*`. NIT: the trailing `:` in `LD_LIBRARY_PATH` adds the CWD to the library search path (n1). |
| 15 | Driver scope / TITAN X decision | def vs Dockerfile + POOL_FACTS drivers | Preserved functionally: CUDA 12.4.1 (needs driver ≥ 550.54.14) and `CMAKE_CUDA_ARCHITECTURES="70;80;89;90"` exclude the TITAN X (sm_52, driver 12.0/525) exactly as the def decided; all in-scope classes (L40S 12.8/13.4, A100 13.3, V100S 13.0, H200 13.4) satisfy ≥550.54.14. The **decision is not recorded** in the Dockerfile/README/VERSIONS (D4). |
| 16 | S4 satisfiability (cpu target) | `s4_run.sh` + cpu Dockerfile | Env1 harness with the `dev` extra (pytest) and env2 tracks are present; `git`, `rsync`, `jq`, `xrootd-client` (S6 uses `xrdfs`/`xrdcp`), `uv`, coreutils and `gawk`/`grep` are present; env3 and llama-labelled checks degrade to "absent by design" in the script. **S4's image needs are met**, subject to the digest/env verification. |
| 17 | S5/I3 satisfiability (gpu target) | `s5_run.sh` + gpu Dockerfile | All three envs + `/opt/r1/llama/bin/llama-server` + CUDA runtime base (12.4.1, driver ≥550.54.14) are in place; the driver window covers NEMO2 L40S/H200, TOpAS V100S/A100. **One gap: llama-server's runtime closure is never exercised** (D1). |
| 18 | A build result / digests in the repo | `grep` of the chain branch | Not present; the chain report §8 records that they must come from the author's job summary/artifact (D8). No CI run URL/log committed. |

---

## 2. Findings

Severity: **BLOCKING** = a required element is wrong/unsafe and the images must not be used as they are;
**MAJOR** = a required property of the image is unverified/likely broken and must be closed before the
affected use; **MINOR** = should be fixed in the next rebuild/edit; **NIT** = hygiene/wording.

**No BLOCKING finding.** The def translation is faithful on every content pin, the images carry no code,
model, data or credentials, the workflow's actions are SHA-pinned and its permissions are minimal, and the
only paths into the registry are the workflow token. The one MAJOR item is a runtime verification gap that
the planned digest check can close.

| ID | Sev | Where | Evidence and finding | Exact fix |
|---|---|---|---|---|
| **D1** | **MAJOR** | gpu final stage (`Dockerfile` L111–144); def L83–105 | The gpu image never runs `llama-server`: the def's post-build smoke and `VERSIONS.txt` recorded `llama-server --version` (def L100, L98–100), but the Dockerfile's gpu stage only imports the three Python envs and records `llama_server_sha256`; it does not execute the binary and does not record `llama_server_version`. llama.cpp is built with the default `GGML_OPENMP=ON` (the gpu/CPU backend links **libgomp**), while the final gpu base (`…cudnn-runtime…`) installs only the CUDA/NCCL/NPP runtime libraries and the gpu stage's dnf list (`git rsync jq xrootd-client tar gzip findutils which procps-ng gawk grep`) does not include `libgomp`; a transitive pull by `xrootd-client` is possible but unverified. A missing `libgomp.so.1` would make `llama-server` fail at load time at S5/I3 while CI still passes — the exact regression the def's smoke prevented. | Add `libgomp` to the gpu final `dnf install` list; add a smoke line `/opt/r1/llama/bin/llama-server --version` (non-zero rc fails the build) and add `llama_server_version=$(…)` to the gpu `VERSIONS.txt` block, mirroring the def. **For tonight**, before S5/I3, run the same smoke in the read-only digest check on deepthought (`apptainer exec docker://ghcr.io/…@<digest> /opt/r1/llama/bin/llama-server --version`); if it fails, rebuild with the fix — do not use the gpu image for S5/I3 until it passes. The cpu image is unaffected (no llama.cpp). |
| D2 | MINOR | branch tree | `r1/scripts/htcondor/docker/README.md` **does not exist**; runbook §3 requires "Dockerfile and README.md". The accepted def route has a README carrying the deliberate properties, driver scope, gate and usage; the Docker route has only comments in the Dockerfile. | Add `r1/scripts/htcondor/docker/README.md`: what the two targets carry, the deliberate differences from the def (runtime/cpu bases, no source tree, curl-minimal, build-only tools dropped), driver scope (D4), target/registration usage by digest for S4/S5, how to re-run the workflow and where the digest artifact lands, and the tag scheme (D7). |
| D3 | MINOR | workflow (no verification step); def build script had `REVIEWED_DEF_SHA` | The Docker build does not assert the accepted def SHA (`a5a0c9da…`) or the four input hashes before building; a push that later changes an input on the image branch would rebuild silently with different pins (the S3 review's F20/R2 gate is lost in translation). | Add a pre-build step: `sha256sum -c` style assertions for `uv.lock.a3fedbb` (`dd42d018…`), `pyproject.toml.a3fedbb` (`72c43589…`), `tracks_freeze_65.txt` (`f1c818e5…`), `pip_freeze_trackp-cpu.txt` (`17da9a3a…`) and the def (`a5a0c9da…`), failing the job on mismatch. Record the five values in the digest artifact. |
| D4 | MINOR | Dockerfile header/labels/VERSIONS; def L24–26 | The def explicitly records the driver-scope decision (CUDA 12.4 ⇒ driver ≥ 550.54.14; in-scope L40S/A100/V100S/H200; TITAN X 12.0/525 and sm_52 **out of scope**). The Dockerfile preserves the behaviour (12.4.1 base + `70;80;89;90`) but neither the header nor the labels nor `VERSIONS.txt` states it, so a consumer cannot see why the TITAN X is excluded. | Add a "Driver scope" header paragraph and label/`VERSIONS` lines (e.g. `r1.driver_min=550.54.14`, `r1.gpu_scope="L40S/A100/V100S/H200; TITAN X (cc5.2, driver 525) out of scope"`), or carry the def's sentence in the README (D2). |
| D5 | MINOR | workflow (no base-digest record); Dockerfile `ARG` tags | The three base images are referenced by **mutable tags** and their digests are not recorded anywhere. At review time they are: devel `sha256:9acaa2fe278c3333f80b30301d774ac0ba9ec91ff8a4904cbf512d217bd17175`, runtime `sha256:fcef8f2fb99546530d0b86a2294536257118084de79a71981ac4d35568b8a559`, rockylinux:9 `sha256:d644d203142cd5b54ad2a83a203e1dee68af2229f8fe32f52a30c6e1d3c3a9e0`. This is the same base-by-tag residual the S3 review accepted (R3); the Docker route makes it easy to close. | Add a step before the builds that resolves and writes the three base digests into `r1-htc-image-digests.txt`/summary (`docker buildx imagetools inspect nvidia/cuda:…` etc.); optionally pin the `ARG` defaults by digest in a follow-up rebuild. Jobs use the built-image digest, so this is provenance, not a use blocker. |
| D6 | MINOR | workflow `Record digests` step, artifact, checkout, images | (a) The digest record/summary/artifact steps are only reached if **both** builds succeed; a gpu failure would leave the already-pushed cpu digest unrecorded. (b) No image **size** is recorded, although the S5 unit sizes `request_disk` to the transferred image. (c) `actions/checkout` keeps the token in `.git/config` for later steps (`persist-credentials` default true) and `runs-on: ubuntu-latest` is a mutable label. (d) `provenance: false`, no SBOM. | Make the record step `if: always()` (or split cpu/gpu into matrix jobs each with its own record); add the sizes (`docker buildx imagetools inspect … --format '{{json .Manifest}}'` or `docker image inspect --format '{{.Size}}'`) to the digest file; add `persist-credentials: false` to checkout; note the `provenance:false`/no-SBOM choice in the README (digest-pinned use is the primary control); accept `ubuntu-latest` or pin a runner image if the author wants. |
| D7 | MINOR | workflow `Tag` step vs runbook §3 | Runbook §3 asks for the image tag `r1-htc:20261114-<short SHA of the Dockerfile>`. The workflow tags `ghcr.io/dowlingwong/r1-htc-{cpu,gpu}:20261114-${GITHUB_SHA::8}` — the **commit** short SHA — and records the Dockerfile's SHA-256 separately in the digest artifact. Functionally sound (jobs use digests; the Dockerfile hash is recorded), but it is a documented deviation. | Either state in the README/report that the tag short SHA is the commit and the Dockerfile SHA-256 is in the digest artifact (and that jobs use digests, not tags), or add a second tag built from the Dockerfile sha8 (`:r1-htc:<dockerfile_sha8>`) for runbook parity. |
| D8 | MINOR | chain branch / report §8 | The CI run, its log, the pushed digests and the image sizes are not in the repository; report §8 says they are in the author's job summary/artifact. The review and the later S4/S5 digest substitution depend on those values. | After the read-only digest verification, commit a small `docs/r1/reports/htcondor_chain_20261114/raw/ghcr_digests_<UTC>.txt` with the run URL, commit, tag, both digests, image sizes and the base digests, and point §8/report at it. |
| n1 | NIT | gpu `ENV` | `LD_LIBRARY_PATH=/opt/r1/llama/bin:${LD_LIBRARY_PATH}` expands to a trailing `:` when the inherited value is empty, adding the CWD to the library search path. | Use `${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}` or drop the variable and rely on the `$ORIGIN` RUNPATH; harmless in practice. |
| n2 | NIT | cpu/gpu `COPY` | The cpu image copies `/opt/r1/pythons` (all three managed Pythons) although it only carries envs 1–2 (the 3.12 install is unused but small relative to the envs). | Optional: copy only 3.11/3.13 pythons for the cpu target. |
| n3 | NIT | labels | The def's `%labels` recorded `r1.paper`, `r1.base`, `r1.envs`, `r1.llama_cpp`; the Docker images carry `org.opencontainers.image.source/description` and `r1.def_route="… (a5a0c9da)"` only (the def SHA is truncated to 8 hex). | Add the def's labels (full def SHA, env list, llama.cpp commit) to both stages; keep `r1.def_route`. |
| n4 | NIT | build stage | the uv installer `curl -LsSf https://astral.sh/uv/0.13.6/install.sh` piped to `sh` is version-pinned but not checksum-verified; the llama.cpp `git clone` is full-history (larger/slower than `git init`+`fetch <sha>`). | Optional hardening: record/verify the uv installer SHA-256; clone with `--filter=blob:none`/single-commit fetch. |
| n5 | NIT | workflow "Free disk space" step | `sudo rm -rf /usr/share/dotnet …` deletes GitHub-runner toolchains. This is **not** the author's data and the standing "no deletion" rule targets the cluster/author data, so it does not violate it — but it should be said explicitly, because the rule is absolute in the runbook. | Add a one-line comment in the workflow/README: "deletion limited to the ephemeral GitHub runner image (no repository/author data)". Alternatively use a slimmer runner. |
| n6 | NIT | gpu stage | The gpu image inherits the nvidia base's `ENTRYPOINT ["/opt/nvidia/nvidia_entrypoint.sh"]`; harmless under Apptainer/`universe = container` (which runs the job executable), but unexpected for a future docker-universe use. | Optional: `ENTRYPOINT []` (or document the inheritance) if the image is ever used with `universe = docker`. |

---

## 3. Def-parity table (version/commit/step, def → Dockerfile)

| Def item | Def value | Dockerfile | Status |
|---|---|---|---|
| Base (build) | `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9` | same `ARG CUDA_DEVEL` default | ✓ |
| EPEL before xrootd-client | def L36–39 | build L27–31; cpu L90–92; gpu L116–118 | ✓ (all three stages) |
| dnf tools | git rsync jq xrootd-client gcc gcc-c++ make cmake tar gzip curl findutils which procps-ng gawk grep | build: same list **minus `curl`**; final stages: runtime subset (no compilers / no full curl) | ✓ deliberate, documented (curl-minimal; runbook §3 needs no curl) |
| uv | 0.13.6, `UV_INSTALL_DIR=/opt/uv`, `UV_NO_CACHE=1`, `PATH=/opt/uv:$PATH` | same | ✓ |
| Pythons | `uv python install 3.13 3.12 3.11`, `UV_PYTHON_INSTALL_DIR=/opt/r1/pythons` | same | ✓ |
| Env 1 (harness) | `uv sync --frozen --extra dev --python 3.13`, `UV_PROJECT_ENVIRONMENT=/opt/r1/envs/harness`, uv.lock `dd42d018…`/pyproject `72c43589…` | same | ✓ (pytest extra verified in the committed pyproject: `dev = ["pytest>=8.0.0"]`) |
| Env 2 (tracks) | drop `-e`/`--editable` lines from `tracks_freeze_65.txt` (`f1c818e5…`), `uv venv --python 3.11`, `uv pip install -r` | same | ✓ |
| Env 3 (Track P) | Python 3.12; filter `torch==`/`kev ` /`laya `/`startlux-decide `; pinned set `--no-deps`; three VCS pins `kev@2074cc44…`, `laya@a478221…`, `startlux-decide@a99977d…`; `torch==2.6.0+cu124` from the cu124 index (proposed); `uv pip check || true` | same (full SHAs in the Dockerfile) | ✓; `pip_freeze_trackp-cpu.txt` (`17da9a3a…`) has no local/editable lines, so the filter is exactly the def's four patterns |
| llama.cpp | commit `620d2225cc436ab0b001e3200e590e3b286ef9ab`; `-DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES="70;80;89;90"`; target `llama-server`; record SHA+commit | same; copies only `build/bin` to `/opt/r1/llama/bin` (def kept the source tree) | ✓ (source-tree drop is deliberate and documented) |
| Final contents | single image with envs 1–3 + llama.cpp + tools | cpu = envs 1–2 + tools; gpu = envs 1–3 + `llama-server` + tools; **no** code/model/data/credentials in either | ✓ (cpu split is deliberate) |
| Smoke/records | post-install imports for envs 1–3; VERSIONS with all fields incl. `llama_server_version`; `llama_server_sha256`, `llama_cpp_commit`; `%environment` PATH/UV_PYTHON_INSTALL_DIR | imports in the final stages; VERSIONS has all fields **except `llama_server_version`**; PATH/UV_PYTHON_INSTALL_DIR + `LD_LIBRARY_PATH`; `llama_server_sha256`/`llama_cpp_commit` recorded | ✓ except D1 |
| Driver scope | comment L24–26 (≥550.54.14; TITAN X out of scope) | behaviour identical (base+arch list), record missing | ✓ behaviour / D4 record |
| No deletion / no secrets / no Paper B data | — | only GitHub-runner cleanup (n5); public URLs only; no model/data/code | ✓ |

---

## 4. Would the targets satisfy S4 and S5/I3?

- **S4 (cpu):** yes. Env 1 carries the harness lock's `dev` extra (pytest) so the I2 determinism test can run
  in the same environment; env 2 carries the 65-package Track S freeze; env 3 and `llama-server` are
  deliberately absent and `s4_run.sh` already records them as "absent by design"; `git`, `rsync`, `jq`,
  `xrootd-client` and coreutils are present for the S6 round-trip and the `/work` checkouts. The image's
  `VERSIONS.txt` gives the versions the S4 report needs. **Use after the digest/env verification.**
- **S5/I3 (gpu):** the environments, `torch==2.6.0+cu124` (with its pip `nvidia-*` runtime wheels), the
  CUDA 12.4.1 runtime base and the `/opt/r1/llama/bin/llama-server` path match what `s5_run.sh` expects, and
  the driver window (≥ 550.54.14) covers NEMO2 L40S/H200 and TOpAS V100S/A100 while the TITAN X stays out
  of scope exactly as the def decided. **The one gap is D1:** the image never proves `llama-server` starts,
  so S5/I3 must not be taken as satisfied until the digest verification runs the binary (fix on failure).
  Carried caveat (not the image's fault): HTCondor 25.0.12 vs the 25.14.1 automatic `--nv` behaviour for
  container-universe GPU jobs (S5 review); and `/ceph/srv/dwong` does not exist, so the I3 model must come
  from `/ceph/dwong/models` via a transfer route.

---

## 5. Safety, credentials and no-deletion re-check

- **No model/data/credentials in the images:** the final images contain only package environments, lock /
  freeze files, the uv binary, the llama.cpp build outputs and the tools; the build inputs are public
  (harness repo lock, TRACKS freeze, Track P freeze, llama.cpp). No `~/.docker`, `.netrc`, token or Paper B
  artefact is copied; the ghcr token is used only by `docker/login-action` on the runner.
- **Workflow token scope:** `GITHUB_TOKEN` with `contents: read` + `packages: write`; no personal token, no
  `docker login` with a password, no plaintext secret.
- **No deletion of author data:** the Docker route deletes nothing; the only `rm -rf` is the GitHub runner
  toolchain cleanup (n5), and the superseded Apptainer SIF route left its failed build in place (Q-BUILD).
- **Provenance:** the def SHA, the four input hashes and the Dockerfile/workflow hashes are all recorded
  above; the chain branch keeps byte-identical copies of the two files; the image branch commit is
  `74820315`. The remaining provenance gap is the CI run/digests (D8).
- **Supply chain:** all GitHub Actions are pinned by commit SHA (verified against the tags), but the base
  images are by mutable tag (D5) and `provenance: false`/no SBOM is a deliberate trade (D6).

---

## 6. What this review could not check, and residual risk

- **No build / no registry access:** the CI run, pushed digests, image sizes and the actual final-image layer
  contents were not inspected; the digest verification on deepthought is the gate for those.
- **No execution:** `llama-server` and the CUDA path cannot be exercised here; D1 is the residual risk until
  the digest check runs the binary on deepthought.
- **The def's own accepted residuals carry over:** torch `2.6.0+cu124` is `proposed:` and needs an author
  ruling before production (the freeze says `2.14.1+cpu`; Q-TORCH); env 3 is installed `--no-deps` by design
  and `uv pip check` is non-fatal, so a Track P training run is not yet a validated environment; the base
  tags are mutable; the TITAN X is out of scope.
- **S5's own checks:** `s5_run.sh`'s PASS test greps `"llama-server"` in `s5_llama.txt`, which the header
  echo alone would satisfy even if `llama-server --version` failed (the rc is recorded but not gated); worth
  tightening in the S5 unit so a D1-style failure is visible in `s5_PASSFAIL.txt`.
- **The `curl` change** is consistent for the reviewed jobs; if a future job needs full `curl` (protocols
  beyond curl-minimal), add `dnf swap curl-minimal curl` in the final stages.

---

## 7. Verdict

The Dockerfile is a faithful translation of the accepted def on every content pin (uv 0.13.6; Python
3.13/3.12/3.11; harness lock `dd42d018…`; 65-package freeze `f1c818e5…`; Track P freeze `17da9a3a…`; the
three VCS commits; `torch==2.6.0+cu124`; llama.cpp `620d2225…`; EPEL→xrootd-client; gawk/grep; the
`curl` removal; CUDA `70;80;89;90`; the multi-stage outputs; no source/code/model/data/credentials), the
workflow is well-formed with all actions SHA-pinned (verified against their tags), minimal permissions and
no plaintext secrets, and both targets match what S4 and S5/I3 expect — with one MAJOR verification gap
(D1: the gpu image never runs `llama-server` and likely lacks `libgomp`) and a set of MINOR/NIT
documentation/robustness items.

**Images may be used — subject to the read-only digest verification on deepthought** (`apptainer inspect
docker://ghcr.io/dowlingwong/r1-htc-{cpu,gpu}@<digest>`, `cat /opt/r1/VERSIONS.txt` via `apptainer exec`,
the three env imports, and **for the gpu image the `llama-server --version` smoke**). If the gpu
`llama-server` smoke fails (expected failure mode: missing `libgomp.so.1`), apply the D1 fix in the
Dockerfile and rebuild before using the gpu image for S5/I3; the cpu image is unaffected. Apply D2–D8 in
the next edit/rebuild. Residual risk: the CI run/digests are not yet committed (D8), the base tags are
mutable (D5), the torch `proposed:` value and the `--no-deps` env 3 remain the def's accepted residuals, and
the TITAN X stays out of scope.

VERDICT: ACCEPTED
