#!/bin/bash
# S2-C3b job entry point (inside the container job): D28 liveness on the eight sweep-1 nodes + prompt-length
# re-measurement with the pick's tokenizer.  Pre-creates the five transferred outputs so an early STOP is visible in
# the job's exit instead of holding on a missing output file (S4-B1 pattern), then runs the wrapper.
set -u
set -o pipefail
umask 077
PY=/opt/r1/envs/harness/bin/python
STOP() { echo "STOP: $*" >&2; _precreate; exit 2; }
_precreate() { for f in job_record.json SHA256SUMS llama-server.log; do : > "$f"; done; for t in out.tar work.tar; do [ -s "$t" ] || tar -cf "$t" --files-from /dev/null 2>/dev/null || : > "$t"; done; }
_precreate
[ "$#" -eq 1 ] || STOP "usage: s2_c3b_job.sh <spec.json>"
[ -x "$PY" ] || STOP "harness python missing in the image: $PY"
[ -f "$1" ] || STOP "spec missing: $1"
[ -d /opt/r1/llama/bin ] || STOP "llama binaries missing in the image"
echo "S2C3B container job start $(date -u +%FT%TZ) host=$(hostname) spec=$1"
"$PY" -B "$(dirname "$0")/s2_c3b_lib.py" run "$1"
RC=$?
echo "S2C3B container job end $(date -u +%FT%TZ) rc=$RC"
exit "$RC"
