#!/bin/bash
# G.1b T1 GPU-node noise-floor chunk — container entry point (ENGINEERING_ONLY; prepared 16 Nov 2026, not run).
#
# Runs inside the frozen v1 gpu image on a NEMO2 L40S slot. The wrapper (g1b_lib.py) validates the spec fail-closed
# (it STOPs while the G.0 census has not named the candidate nodes), measures one pre-declared chunk of the D21
# 30-seed noise floor, and writes out/ (runs.jsonl, edits.json, manifest.json) plus job_record.json and SHA256SUMS.
# Pre-creates the transferred outputs so an early STOP is visible in the job's exit instead of holding on a missing
# output file (S4-B1 pattern), and tars out/ on the way out so a STOP still transfers its evidence.
set -u
set -o pipefail
umask 077

PY=/opt/r1/envs/trackp/bin/python
STOP() {
  echo "STOP: $*" >&2
  mkdir -p out
  : > job_record.json
  : > SHA256SUMS
  : > g1b_run.log
  : > out.tar
  exit 2
}

mkdir -p out
: > job_record.json
: > SHA256SUMS
: > g1b_run.log
: > out.tar

[ "$#" -eq 1 ] || STOP "usage: g1b_job.sh <g1b_spec.json>"
[ -x "$PY" ] || STOP "pinned torch python missing in the image: $PY"
[ -f "$1" ] || STOP "chunk spec missing: $1"
[ -f /opt/r1/VERSIONS.txt ] || STOP "image identity file missing: not the frozen v1 gpu image"
[ -f "$(dirname "$0")/g1b_lib.py" ] || STOP "wrapper missing next to the job script"

echo "G1B noise-floor chunk start $(date -u +%FT%TZ) host=$(hostname) spec=$1"
"$PY" -B "$(dirname "$0")/g1b_lib.py" run "$1" 2>&1 | tee g1b_run.log
RC=${PIPESTATUS[0]}
echo "G1B noise-floor chunk end $(date -u +%FT%TZ) rc=$RC" | tee -a g1b_run.log

# Keep the evidence transferable even when the wrapper stopped before writing out.tar.
if [ ! -s out.tar ]; then
  if [ -d out ] && [ -n "$(ls -A out 2>/dev/null)" ]; then
    tar -cf out.tar out 2>/dev/null || : > out.tar
  fi
fi
[ -f SHA256SUMS ] || : > SHA256SUMS
exit "$RC"
