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

########################################################################################
FROM ${CUDA_DEVEL} AS build
SHELL ["/bin/bash", "-euxo", "pipefail", "-c"]

# EPEL first: xrootd-client is EPEL-only on Rocky 9.
RUN dnf install -y --setopt=install_weak_deps=False epel-release \
 && dnf install -y --setopt=install_weak_deps=False \
        git rsync jq xrootd-client gcc gcc-c++ make cmake tar gzip findutils which procps-ng gawk grep \
 && dnf clean all

# uv pinned to 0.13.6; no cache in the image.
ENV UV_INSTALL_DIR=/opt/uv \
    UV_PYTHON_INSTALL_DIR=/opt/r1/pythons \
    UV_NO_CACHE=1 \
    PATH=/opt/uv:$PATH
RUN curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh \
 && mkdir -p /opt/r1/envs /opt/r1/pythons /opt/r1/harness /opt/r1/locks \
 && uv python install 3.13 3.12 3.11

COPY uv.lock.a3fedbb          /opt/r1/harness/uv.lock
COPY pyproject.toml.a3fedbb   /opt/r1/harness/pyproject.toml
COPY tracks_freeze_65.txt     /opt/r1/locks/tracks_freeze_65.txt
COPY pip_freeze_trackp-cpu.txt /opt/r1/locks/pip_freeze_trackp-cpu.txt

# Env 1 - harness: uv.lock at harness a3fedbb (Python 3.13), plus the dev extra for pytest.
# The harness pyproject has no [build-system], so uv treats it as a virtual project: only the
# locked dependencies are installed, no harness code.
RUN cd /opt/r1/harness \
 && UV_PROJECT_ENVIRONMENT=/opt/r1/envs/harness uv sync --frozen --extra dev --python 3.13

# Env 2 - Track S/Track P: the 65-package freeze (Python 3.11); drop the editable line that
# points at the author's /home path.
RUN grep -vE '^(-e|--editable)([[:space:]]|$)' /opt/r1/locks/tracks_freeze_65.txt > /tmp/tracks_install.txt \
 && uv venv --python 3.11 /opt/r1/envs/tracks \
 && uv pip install --python /opt/r1/envs/tracks/bin/python -r /tmp/tracks_install.txt

# Env 3 - Track P training: Python 3.12; pinned set --no-deps, VCS deps --no-deps at their
# pinned commits, then the CUDA torch build. torch==2.6.0+cu124 is "proposed:" in the def
# (the CPU freeze says torch==2.14.1+cpu); it needs an author ruling before production use.
RUN uv venv --python 3.12 /opt/r1/envs/trackp \
 && TP=/opt/r1/envs/trackp/bin/python \
 && grep -viE '^(torch==|kev[[:space:]]|laya[[:space:]]|startlux-decide[[:space:]])' /opt/r1/locks/pip_freeze_trackp-cpu.txt > /tmp/trackp_pinned.txt \
 && uv pip install --python "$TP" --no-deps -r /tmp/trackp_pinned.txt \
 && uv pip install --python "$TP" --no-deps 'kev @ git+https://github.com/jaredpalmer/kev@2074cc44256200bb37540103fa4572901faa10f3' \
 && uv pip install --python "$TP" --no-deps 'laya @ git+https://github.com/NandhaKishorM/laya@a478221bcad24d1a9c47b361c79328ebd2b100c6' \
 && uv pip install --python "$TP" --no-deps 'startlux-decide @ git+https://github.com/StartLuxLabs/StartLux-Decision@a99977d9332decc9fb27a2488b4a83b533b6cd5f' \
 && uv pip install --python "$TP" --index-url https://download.pytorch.org/whl/cu124 'torch==2.6.0+cu124' \
 && (uv pip check --python "$TP" || true)

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
 && dnf install -y --setopt=install_weak_deps=False git rsync jq xrootd-client tar gzip findutils which procps-ng gawk grep \
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
RUN dnf install -y --setopt=install_weak_deps=False epel-release \
 && dnf install -y --setopt=install_weak_deps=False git rsync jq xrootd-client tar gzip findutils which procps-ng gawk grep \
 && dnf clean all
COPY --from=build /opt/uv /opt/uv
COPY --from=build /opt/r1/pythons /opt/r1/pythons
COPY --from=build /opt/r1/envs /opt/r1/envs
COPY --from=build /opt/r1/harness /opt/r1/harness
COPY --from=build /opt/r1/locks /opt/r1/locks
COPY --from=build /opt/r1/llama /opt/r1/llama
COPY --from=build /opt/r1/LLAMA_SERVER_SHA256 /opt/r1/LLAMA_CPP_COMMIT /opt/r1/
ENV PATH=/opt/uv:/opt/r1/llama/bin:$PATH UV_PYTHON_INSTALL_DIR=/opt/r1/pythons \
    LD_LIBRARY_PATH=/opt/r1/llama/bin:${LD_LIBRARY_PATH}
# No GPU on the build runner: import checks only (torch.cuda is not exercised here).
RUN /opt/r1/envs/harness/bin/python -c "import numpy, sklearn, pandas, pytest; print('env1 ok', numpy.__version__, sklearn.__version__)" \
 && /opt/r1/envs/tracks/bin/python -c "import numpy, sklearn, pandas; print('env2 ok', numpy.__version__, sklearn.__version__)" \
 && /opt/r1/envs/trackp/bin/python -c "import torch, numpy, sklearn; print('env3 ok', torch.__version__, numpy.__version__, sklearn.__version__)" \
 && { echo "image=r1-htc-gpu"; echo "build_utc=$(date -u +%FT%TZ)"; echo "base=nvidia/cuda:12.4.1-cudnn-runtime-rockylinux9"; \
      echo "uv=$(uv --version)"; \
      echo "python_313=$(/opt/r1/envs/harness/bin/python -VV 2>&1)"; \
      echo "python_311=$(/opt/r1/envs/tracks/bin/python -VV 2>&1)"; \
      echo "python_trackp=$(/opt/r1/envs/trackp/bin/python -VV 2>&1)"; \
      echo "torch_pin=torch==2.6.0+cu124 (proposed)"; \
      echo "torch_actual=$(/opt/r1/envs/trackp/bin/python -c 'import torch; print(torch.__version__)')"; \
      echo "llama_cpp_commit=$(cat /opt/r1/LLAMA_CPP_COMMIT)"; \
      echo "llama_server_sha256=$(awk '{print $1}' /opt/r1/LLAMA_SERVER_SHA256)"; \
      echo "harness_lock_sha256=$(sha256sum /opt/r1/harness/uv.lock | awk '{print $1}')"; \
      echo "tracks_freeze_sha256=$(sha256sum /opt/r1/locks/tracks_freeze_65.txt | awk '{print $1}')"; \
      echo "trackp_freeze_sha256=$(sha256sum /opt/r1/locks/pip_freeze_trackp-cpu.txt | awk '{print $1}')"; \
    } > /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt
