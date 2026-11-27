#!/bin/bash
# Track P P.4 phase-1 job entry point (inside the container job, image v2.2; one job = one base, ENGINEERING_ONLY).
# Pre-creates the transferred outputs so an early STOP is the job's exit, not a hold on a missing output file
# (the G.1b / S2-C2 pattern), then runs the reviewed library with the image's env3 Python. AI-assisted (Claude).
set -u
set -o pipefail
umask 077
PY=${P4_VENV_PYTHON:-/opt/r1/envs/trackp/bin/python}
_precreate() { for f in job_record.json SHA256SUMS; do [ -s "$f" ] || : > "$f"; done; [ -s out.tar ] || tar -cf out.tar --files-from /dev/null 2>/dev/null || : > out.tar; }
STOP() { echo "STOP: $*" >&2; _precreate; exit 2; }
exec > >(tee -a p4_run.log) 2>&1
_precreate
[ "$#" -eq 3 ] || STOP "usage: p4_job.sh <p4_spec.json> <arm> <host class>"
[ -x "$PY" ] || STOP "env3 python missing: $PY"
[ -f "$1" ] || STOP "spec missing: $1"
export GIT_TERMINAL_PROMPT=0 PYTHONDONTWRITEBYTECODE=1
echo "P4 container job start $(date -u +%FT%TZ) host=$(hostname) arm=$2 host_class=$3 uid=$(id -u)"
"$PY" -B "$(dirname "$0")/p4_lib.py" job "$1" --arm "$2" --host-class "$3"
RC=$?
_precreate
echo "P4 container job end $(date -u +%FT%TZ) rc=$RC"
exit "$RC"
