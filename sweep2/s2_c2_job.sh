#!/bin/bash
# S2-C2 job entry point (inside the container job). Pre-creates the five transferred outputs so an early STOP is
# visible in the job's exit instead of holding on a missing output file (S4-B1 pattern), then runs the wrapper.
set -u
set -o pipefail
umask 077
PY=/opt/r1/envs/harness/bin/python
STOP() { echo "STOP: $*" >&2; mkdir -p out work; : > job_record.json; : > SHA256SUMS; : > llama-server.log; exit 2; }
mkdir -p out work; : > job_record.json; : > SHA256SUMS; : > llama-server.log
[ "$#" -eq 1 ] || STOP "usage: s2_c2_job.sh <spec.json>"
[ -x "$PY" ] || STOP "harness python missing in the image: $PY"
[ -f "$1" ] || STOP "spec missing: $1"
[ -d /opt/r1/llama/bin ] || STOP "llama binaries missing in the image"
echo "S2C2 container job start $(date -u +%FT%TZ) host=$(hostname) spec=$1"
"$PY" -B "$(dirname "$0")/s2_c2_lib.py" run "$1"
RC=$?
echo "S2C2 container job end $(date -u +%FT%TZ) rc=$RC"
exit "$RC"
