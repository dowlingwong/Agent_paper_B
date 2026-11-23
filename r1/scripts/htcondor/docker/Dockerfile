# Paper B R1 HTCondor images, v2 proposal (15 Nov 2026): Docker route via GitHub Actions -> ghcr.io.
#
# v2 scope (author Q-TORCH ruling + image-v2 items; proposal only, the v1 digests in use stay):
# - Python patch versions are pinned (3.13.4 / 3.12.15 / 3.11.18: the patches of the validated
#   TASL-7 exam, Track P GPU and Track S venvs) instead of "latest 3.x" at build time;
# - libgomp is installed explicitly in every stage (llama.cpp / torch OpenMP runtime, D1);
# - the gpu target carries nvidia-smi (copied from the CUDA devel base) so the S5 GPU gate can run
#   inside the container;
# - env 3 (Track P training) is rebuilt from the committed Track P GPU freeze
#   (r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt, the TASL-7-validated 121-line freeze):
#   Python 3.12.15, --no-deps pinned set, torch==2.6.0+cu124 from the cu124 index,
#   causal-conv1d==1.7.0 built from source with TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0"; the build
#   fails unless `uv pip freeze` (sorted) is identical to the committed freeze. VERSIONS records it.
#
# Paper B R1 HTCondor images: Docker route via GitHub Actions -> ghcr.io (14 Nov 2026).
#
# This is the Docker translation of the reviewed Apptainer definition
# r1/scripts/htcondor/apptainer/r1-htc.def (accepted def SHA-256 a5a0c9da...). The build stage
# repeats its %post step for step. Two final targets:
#   cpu  -> envs 1 and 2 (harness, tracks) + tools; for CPU jobs (C3 audits, gate, determinism).
#   gpu  -> all three envs + llama-server (CUDA arch 70;80;89;90) on the CUDA runtime base.
# The build context is r1/scripts/htcondor/apptainer/ (the committed lock and freeze files).
# The image holds no code checkout, model, data or credential. It is meant to be public.
#
# Differences from the def, all deliberate:
# - Multi-stage: final images use cudnn-runtime (gpu) or rockylinux:9 (cpu) instead of the
#   devel base, and carry only the build outputs (smaller pulls on the worker nodes).
# - llama.cpp: only build/bin is kept, not the source tree.
# - The cpu target omits env 3 (Track P training) and llama-server.
# - "curl" is not in the dnf lists: the Rocky 9 bases ship curl-minimal, which provides the curl
#   binary and conflicts with the full curl package (first CI run, 14 Nov 2026 21:44Z).

ARG CUDA_DEVEL=nvidia/cuda:12.4.1-cudnn-devel-rockylinux9
ARG CUDA_RUNTIME=nvidia/cuda:12.4.1-cudnn-runtime-rockylinux9
ARG CPU_BASE=rockylinux:9
ARG PY313=3.13.4
ARG PY312=3.12.15
ARG PY311=3.11.18

########################################################################################
# nvidia-smi sidecar: the CUDA Rocky 9 bases (devel and runtime) and the Ubuntu CUDA bases ship no
# NVIDIA driver utilities, and the cuda-repo driver packages need dkms/kmod (no kernel in a container).
# Take the user-space nvidia-smi from Ubuntu 20.04's nvidia-utils (glibc 2.31, forward-compatible with
# Rocky 9's glibc 2.34); at run time the batch system injects libnvidia-ml, as for any container job.
# License note: this redistributes the NVIDIA user-space driver utility inside the image; the author
# approved shipping nvidia-smi in v2 — record the package version in VERSIONS.
FROM ubuntu:20.04 AS nvutils
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends nvidia-utils-535 \
 && rm -rf /var/lib/apt/lists/*

########################################################################################
FROM ${CUDA_DEVEL} AS build
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
# Global ARGs are only available in FROM lines; re-declare them inside the stage so the pinned Python
# patches are visible to RUN (the v2 first CI build failed here with "PY313: unbound variable").
ARG PY313
ARG PY312
ARG PY311

# EPEL first: xrootd-client is EPEL-only on Rocky 9.
RUN dnf install -y --setopt=install_weak_deps=False epel-release \
 && dnf install -y --setopt=install_weak_deps=False \
        git rsync jq xrootd-client gcc gcc-c++ make cmake tar gzip findutils which procps-ng gawk grep libgomp diffutils \
 && dnf clean all

# uv pinned to 0.13.6; no cache in the image.
ENV UV_INSTALL_DIR=/opt/uv \
    UV_PYTHON_INSTALL_DIR=/opt/r1/pythons \
    UV_NO_CACHE=1 \
    PATH=/opt/uv:$PATH
RUN curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh \
 && mkdir -p /opt/r1/envs /opt/r1/pythons /opt/r1/harness /opt/r1/locks \
 && uv python install ${PY313} ${PY312} ${PY311}

COPY uv.lock.a3fedbb          /opt/r1/harness/uv.lock
COPY pyproject.toml.a3fedbb   /opt/r1/harness/pyproject.toml
COPY tracks_freeze_65.txt     /opt/r1/locks/tracks_freeze_65.txt
COPY pip_freeze_trackp-cpu.txt /opt/r1/locks/pip_freeze_trackp-cpu.txt
COPY pip_freeze_trackp-gpu.txt /opt/r1/locks/pip_freeze_trackp-gpu.txt

# Env 1 - harness: uv.lock at harness a3fedbb (Python 3.13), plus the dev extra for pytest.
# The harness pyproject has no [build-system], so uv treats it as a virtual project: only the
# locked dependencies are installed, no harness code.
RUN cd /opt/r1/harness \
 && UV_PROJECT_ENVIRONMENT=/opt/r1/envs/harness uv sync --frozen --extra dev --python ${PY313}

# Env 2 - Track S/Track P: the 65-package freeze (Python 3.11); drop the editable line that
# points at the author's /home path.
RUN grep -vE '^(-e|--editable)([[:space:]]|$)' /opt/r1/locks/tracks_freeze_65.txt > /tmp/tracks_install.txt \
 && uv venv --python ${PY311} /opt/r1/envs/tracks \
 && uv pip install --python /opt/r1/envs/tracks/bin/python -r /tmp/tracks_install.txt

# Env 3 - Track P training (v2, author Q-TORCH ruling 15 Nov 2026): rebuilt from the committed
# Track P GPU freeze exactly. Python 3.12.15; the pinned set is installed --no-deps; the three VCS
# dependencies are installed --no-deps at their pinned commits; torch comes from the cu124 index.
# v2.2 (R1-TRACKP-IMAGE-V22-B, 24 Nov 2026): the prebuilt causal_conv1d wheels on the 1.7.0 release are
# C++11-ABI binaries even under the "cxx11abiFALSE" tag (undefined c10::detail::torchCheckFail with
# std::__cxx11::basic_string; v2.1 smoke 759983). env3 therefore builds causal-conv1d 1.7.0 from the pinned
# sdist against this image's torch 2.6.0+cu124 with -D_GLIBCXX_USE_CXX11_ABI=0 and sm 8.0/8.9/9.0, then
# imports it and rejects any std::__cxx11 reference in the extension. The build log's sha256 is recorded.
# The env3 freeze check below is unchanged: only the causal-conv1d line differs (source build at 1.7.0).
RUN uv venv --python ${PY312} /opt/r1/envs/trackp \
 && TP=/opt/r1/envs/trackp/bin/python \
 && grep -viE '^(torch==|causal-conv1d==|kev[[:space:]]|laya[[:space:]]|startlux-decide[[:space:]])' /opt/r1/locks/pip_freeze_trackp-gpu.txt > /tmp/trackp_pinned.txt \
 && uv pip install --python "$TP" --no-deps -r /tmp/trackp_pinned.txt \
 && uv pip install --python "$TP" --no-deps 'kev @ git+https://github.com/jaredpalmer/kev@2074cc44256200bb37540103fa4572901faa10f3' \
 && uv pip install --python "$TP" --no-deps 'laya @ git+https://github.com/NandhaKishorM/laya@a478221bcad24d1a9c47b361c79328ebd2b100c6' \
 && uv pip install --python "$TP" --no-deps 'startlux-decide @ git+https://github.com/StartLuxLabs/StartLux-Decision@a99977d9332decc9fb27a2488b4a83b533b6cd5f' \
 && uv pip install --python "$TP" --no-deps --index-url https://download.pytorch.org/whl/cu124 'torch==2.6.0+cu124' \
 && curl -fsSL -o /tmp/causal_conv1d-1.7.0.tar.gz 'https://files.pythonhosted.org/packages/f4/d1/eba27735f31bd5527d39a3c7f693e6ded7b844cab275db719a15ad37b6cd/causal_conv1d-1.7.0.tar.gz' \
 && printf '%s  %s\n' '3202758494eaa7b597ce1c282dfa188889506bfcb92cad3c407d26736bfcd32b' '/tmp/causal_conv1d-1.7.0.tar.gz' | sha256sum -c - \
 && { TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0" MAX_JOBS="$(nproc)" \
      CXXFLAGS="-D_GLIBCXX_USE_CXX11_ABI=0" TORCH_CXX_FLAGS="-D_GLIBCXX_USE_CXX11_ABI=0" \
      uv pip install --python "$TP" --no-deps --no-build-isolation /tmp/causal_conv1d-1.7.0.tar.gz; } 2>&1 | tee /opt/r1/causal_conv1d_build.log \
 && C1DSO=$(ls /opt/r1/envs/trackp/lib/python3.12/site-packages/causal_conv1d_cuda*.so) \
 && /opt/r1/envs/trackp/bin/python -c "import causal_conv1d_cuda, causal_conv1d; print('causal_conv1d import ok')" \
 && ! nm -D -C "$C1DSO" | grep -q 'std::__cxx11' \
 && sha256sum /opt/r1/causal_conv1d_build.log > /opt/r1/CAUSAL_CONV1D_BUILD_LOG_SHA256 \
 && sha256sum "$C1DSO" > /opt/r1/CAUSAL_CONV1D_SO_SHA256 \
 && uv pip freeze --python "$TP" | sort > /tmp/env3_built.sorted \
 && sort /opt/r1/locks/pip_freeze_trackp-gpu.txt > /tmp/env3_pinned.sorted \
 && diff -u /tmp/env3_pinned.sorted /tmp/env3_built.sorted \
 && echo "env3 sorted diff: empty"
# llama.cpp at the pinned commit, CUDA build for V100, A100, L40S/4090, H200.
RUN git clone https://github.com/ggml-org/llama.cpp /opt/r1/llama.cpp \
 && git -C /opt/r1/llama.cpp checkout 620d2225cc436ab0b001e3200e590e3b286ef9ab \
 && cmake -S /opt/r1/llama.cpp -B /opt/r1/llama.cpp/build \
        -DGGML_CUDA=ON -DGGML_NATIVE=OFF -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_CUDA_ARCHITECTURES="70;80;89;90" \
 && cmake --build /opt/r1/llama.cpp/build -j"$(nproc)" --target llama-server \
 && mkdir -p /opt/r1/llama \
 && cp -a /opt/r1/llama.cpp/build/bin /opt/r1/llama/bin \
 && sha256sum /opt/r1/llama/bin/llama-server > /opt/r1/LLAMA_SERVER_SHA256 \
 && git -C /opt/r1/llama.cpp rev-parse HEAD > /opt/r1/LLAMA_CPP_COMMIT

########################################################################################
FROM ${CPU_BASE} AS cpu
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
LABEL org.opencontainers.image.source="https://github.com/dowlingwong/agent_paper_b" \
      org.opencontainers.image.description="Paper B R1 HTCondor CPU image: harness env (Py3.13) + Track S env (Py3.11). No code, models, data or credentials." \
      r1.def_route="r1/scripts/htcondor/apptainer/r1-htc.def (a5a0c9da)"
RUN dnf install -y --setopt=install_weak_deps=False epel-release \
 && dnf install -y --setopt=install_weak_deps=False git rsync jq xrootd-client tar gzip findutils which procps-ng gawk grep libgomp diffutils \
 && dnf clean all
COPY --from=build /opt/uv /opt/uv
COPY --from=build /opt/r1/pythons /opt/r1/pythons
COPY --from=build /opt/r1/envs/harness /opt/r1/envs/harness
COPY --from=build /opt/r1/envs/tracks /opt/r1/envs/tracks
COPY --from=build /opt/r1/harness /opt/r1/harness
COPY --from=build /opt/r1/locks /opt/r1/locks
ENV PATH=/opt/uv:$PATH UV_PYTHON_INSTALL_DIR=/opt/r1/pythons
RUN /opt/r1/envs/harness/bin/python -c "import numpy, sklearn, pandas, pytest; print('env1 ok', numpy.__version__, sklearn.__version__, pandas.__version__, pytest.__version__)" \
 && /opt/r1/envs/tracks/bin/python -c "import numpy, sklearn, pandas; print('env2 ok', numpy.__version__, sklearn.__version__, pandas.__version__)" \
 && { echo "image=r1-htc-cpu"; echo "build_utc=$(date -u +%FT%TZ)"; echo "base=rockylinux:9"; \
      echo "uv=$(uv --version)"; \
      echo "python_313=$(/opt/r1/envs/harness/bin/python -VV 2>&1)"; \
      echo "python_311=$(/opt/r1/envs/tracks/bin/python -VV 2>&1)"; \
      echo "harness_lock_sha256=$(sha256sum /opt/r1/harness/uv.lock | awk '{print $1}')"; \
      echo "tracks_freeze_sha256=$(sha256sum /opt/r1/locks/tracks_freeze_65.txt | awk '{print $1}')"; \
    } > /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt

########################################################################################
FROM ${CUDA_RUNTIME} AS gpu
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]
LABEL org.opencontainers.image.source="https://github.com/dowlingwong/agent_paper_b" \
      org.opencontainers.image.description="Paper B R1 HTCondor GPU image: three pinned envs + llama-server 620d2225 (CUDA 70;80;89;90). No code, models, data or credentials." \
      r1.def_route="r1/scripts/htcondor/apptainer/r1-htc.def (a5a0c9da)"
# v2.1 (R1-TRACKP-IMAGE-V21, 21 Nov 2026): gcc is the only addition to the gpu target. Triton
# builds its C launcher at run time and causal_conv1d's import path probes Triton; without a
# compiler both fail with "Failed to find C compiler" (H200 smoke STOP, job 759914). On Rocky 9
# the gcc package provides /usr/bin/gcc and /usr/bin/cc. Nothing else changes.
RUN dnf install -y --setopt=install_weak_deps=False epel-release \
 && dnf install -y --setopt=install_weak_deps=False git rsync jq xrootd-client tar gzip findutils which procps-ng gawk grep libgomp diffutils gcc \
 && dnf clean all
COPY --from=build /opt/uv /opt/uv
COPY --from=build /opt/r1/pythons /opt/r1/pythons
COPY --from=build /opt/r1/envs /opt/r1/envs
COPY --from=build /opt/r1/harness /opt/r1/harness
COPY --from=build /opt/r1/locks /opt/r1/locks
COPY --from=build /opt/r1/llama /opt/r1/llama
COPY --from=build /opt/r1/LLAMA_SERVER_SHA256 /opt/r1/LLAMA_CPP_COMMIT /opt/r1/
COPY --from=build /opt/r1/causal_conv1d_build.log /opt/r1/CAUSAL_CONV1D_BUILD_LOG_SHA256 /opt/r1/CAUSAL_CONV1D_SO_SHA256 /opt/r1/
# nvidia-smi for the in-container S5-style GPU gate (the runtime base does not ship it); the CUDA
# driver libraries are injected by the batch system at run time, as for the v1 image.
COPY --from=nvutils /usr/bin/nvidia-smi /usr/bin/nvidia-smi
RUN test -x /usr/bin/nvidia-smi
ENV PATH=/opt/uv:/opt/r1/llama/bin:$PATH UV_PYTHON_INSTALL_DIR=/opt/r1/pythons \
    LD_LIBRARY_PATH=/opt/r1/llama/bin:${LD_LIBRARY_PATH}
# No GPU on the build runner: import checks only (torch.cuda is not exercised here).
RUN /opt/r1/envs/harness/bin/python -c "import numpy, sklearn, pandas, pytest; print('env1 ok', numpy.__version__, sklearn.__version__)" \
 && /opt/r1/envs/tracks/bin/python -c "import numpy, sklearn, pandas; print('env2 ok', numpy.__version__, sklearn.__version__)" \
 && /opt/r1/envs/trackp/bin/python -c "import causal_conv1d_cuda, causal_conv1d; print('env3 causal_conv1d import ok')" \
 && C1DSO=$(ls /opt/r1/envs/trackp/lib/python3.12/site-packages/causal_conv1d_cuda*.so) \
 && ! nm -D -C "$C1DSO" | grep -q 'std::__cxx11' \
 && /opt/r1/envs/trackp/bin/python -c "import torch, numpy, sklearn; print('env3 ok', torch.__version__, numpy.__version__, sklearn.__version__)" \
 && uv pip freeze --python /opt/r1/envs/trackp/bin/python | sort > /tmp/env3_image.sorted \
 && sort /opt/r1/locks/pip_freeze_trackp-gpu.txt > /tmp/env3_pinned_image.sorted \
 && diff -u /tmp/env3_pinned_image.sorted /tmp/env3_image.sorted \
 && echo "env3 sorted diff: empty" \
 && { echo "image=r1-htc-gpu"; echo "build_utc=$(date -u +%FT%TZ)"; echo "base=nvidia/cuda:12.4.1-cudnn-runtime-rockylinux9"; \
      echo "uv=$(uv --version)"; \
      echo "python_313=$(/opt/r1/envs/harness/bin/python -VV 2>&1)"; \
      echo "python_311=$(/opt/r1/envs/tracks/bin/python -VV 2>&1)"; \
      echo "python_trackp=$(/opt/r1/envs/trackp/bin/python -VV 2>&1)"; \
      echo "torch_pin=torch==2.6.0+cu124 (Q-TORCH ruling: install from the cu124 index)"; \
      echo "torch_actual=$(/opt/r1/envs/trackp/bin/python -c 'import torch; print(torch.__version__)')"; \
      echo "trackp_gpu_freeze_sha256=$(sha256sum /opt/r1/locks/pip_freeze_trackp-gpu.txt | awk '{print $1}')"; \
      echo "env3_sorted_diff=empty"; \
      echo "env3_causal_conv1d_arch=8.0;8.9;9.0 (source build, CXX11 ABI 0)"; \
      echo "torch_cxx11_abi=$(/opt/r1/envs/trackp/bin/python -c 'import torch; print(torch._C._GLIBCXX_USE_CXX11_ABI)')"; \
      echo "causal_conv1d_sdist_sha256=3202758494eaa7b597ce1c282dfa188889506bfcb92cad3c407d26736bfcd32b"; \
      echo "causal_conv1d_so_sha256=$(awk '{print $1}' /opt/r1/CAUSAL_CONV1D_SO_SHA256)"; \
      echo "causal_conv1d_build_log_sha256=$(awk '{print $1}' /opt/r1/CAUSAL_CONV1D_BUILD_LOG_SHA256)"; \
      echo "nvidia_smi=/usr/bin/nvidia-smi"; \
      echo "nvidia_utils_package=ubuntu20.04 nvidia-utils-535 (user-space, host libnvidia-ml injected at runtime)"; \
      echo "libgomp=$(rpm -q libgomp)"; \
      echo "llama_cpp_commit=$(cat /opt/r1/LLAMA_CPP_COMMIT)"; \
      echo "llama_server_sha256=$(awk '{print $1}' /opt/r1/LLAMA_SERVER_SHA256)"; \
      echo "harness_lock_sha256=$(sha256sum /opt/r1/harness/uv.lock | awk '{print $1}')"; \
      echo "tracks_freeze_sha256=$(sha256sum /opt/r1/locks/tracks_freeze_65.txt | awk '{print $1}')"; \
      echo "trackp_freeze_sha256=$(sha256sum /opt/r1/locks/pip_freeze_trackp-cpu.txt | awk '{print $1}')"; \
    } > /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt
