#!/bin/bash
# S2-C2 job entry point (inside the container job). Runs the reviewed wrapper, which validates the spec,
# verifies the frozen image/GPU/CPU identity, fetches the pinned GGUF, starts an owned llama-server with the
# exam flags and drives the harness root campaigns; all raw outputs go to the sealed /ceph path only.
set -u
set -o pipefail
umask 077
PY=/opt/r1/envs/harness/bin/python
STOP() { echo "STOP: $*" >&2; exit 2; }
[ "$#" -eq 1 ] || STOP "usage: s2_c2_job.sh <spec.json>"
[ -x "$PY" ] || STOP "harness python missing in the image: $PY"
[ -f "$1" ] || STOP "spec missing: $1"
[ -d /opt/r1/llama/bin ] || STOP "llama binaries missing in the image"
echo "S2C2 container job start $(date -u +%FT%TZ) host=$(hostname) spec=$1"
"$PY" -B "$(dirname "$0")/s2_c2_lib.py" run "$1" --scratch "$PWD/scratch"
RC=$?
echo "S2C2 container job end $(date -u +%FT%TZ) rc=$RC"
exit "$RC"
