#!/usr/bin/env bash
set -uo pipefail
R=/home/dowling/r1_tracks
CUDA=/usr/local/cuda-12.2
echo "=== llama.cpp build start $(date -u +%FT%TZ) ==="
cd $R
cmake -S opt/llama.cpp -B opt/llama.cpp/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DCMAKE_CUDA_COMPILER=$CUDA/bin/nvcc -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -30
echo "CONFIGURE_RC=${PIPESTATUS[0]}"
cmake --build opt/llama.cpp/build -j --target llama-server 2>&1 | tail -40
echo "BUILD_RC=${PIPESTATUS[0]}"
ls -la opt/llama.cpp/build/bin/llama-server 2>&1
opt/llama.cpp/build/bin/llama-server --version 2>&1 | head -5
echo "=== build done $(date -u +%FT%TZ) ==="
