#!/usr/bin/env bash
set -uo pipefail
R=/home/dowling/r1_tracks
URL=https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q4_k_m.gguf
F=$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
echo "=== GGUF download start $(date -u +%FT%TZ) ==="
curl -L --fail --retry 3 -o "$F" "$URL"; echo "CURL_RC=$?"
ls -la "$F"
sha256sum "$F"; echo "SHA_RC=$?"
echo "=== GGUF done $(date -u +%FT%TZ) ==="
