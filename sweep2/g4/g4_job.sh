#!/bin/bash
# G.4 H200 pilot job entry point (inside the container job; one job = one pilot node, ENGINEERING_ONLY).
# Pre-creates the transferred outputs so an early STOP is visible as the job's exit instead of a hold on a missing
# output file (S4-B1 / S2-C2 pattern), then runs the reviewed library with the image's harness Python.
set -u
set -o pipefail
umask 077
PY=/opt/r1/envs/harness/bin/python
_precreate() { for f in job_record.json SHA256SUMS llama-server.log; do [ -s "$f" ] || : > "$f"; done; [ -s out.tar ] || tar -cf out.tar --files-from /dev/null 2>/dev/null || : > out.tar; }
STOP() { echo "STOP: $*" >&2; _precreate; exit 2; }
exec > >(tee -a g4_run.log) 2>&1
_precreate
[ "$#" -eq 2 ] || STOP "usage: g4_job.sh <g4_spec.json> <node>"
[ -x "$PY" ] || STOP "harness python missing in the image: $PY"
[ -f "$1" ] || STOP "spec missing: $1"
echo "G4 container job start $(date -u +%FT%TZ) host=$(hostname) node=$2 uid=$(id -u)"
"$PY" -B "$(dirname "$0")/g4_lib.py" job "$1" --node "$2"
RC=$?
_precreate
echo "G4 container job end $(date -u +%FT%TZ) rc=$RC"
exit "$RC"
