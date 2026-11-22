#!/bin/bash
# Authorized G.1b amendment run: mlgym_fmnist on TASL-2 (note g1b_t1_tasl_20261122.md).
# Invokes the signed command once; a node/timing/complete STOP ends it. Only an infrastructure STOP is retried once.
set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_fmnist
SPEC=$P/sweep2/t1_tasl/g1b_tasl_spec.json
NOTE=$P/docs/r1/authorizations/g1b_t1_tasl_20261122.md
NODE=mlgym_fmnist
LOG=$B/logs/g1b_fmnist_20261122.driver.log
STATUS=$B/logs/g1b_fmnist_20261122.status
PY=python3
mkdir -p "$B/logs"
echo "DRIVER_START $(date -u +%FT%TZ) pid=$$" >> "$LOG"
cd "$P" || { echo "STOP_CD $(date -u +%FT%TZ)" >> "$STATUS"; exit 1; }
tries=0
while true; do
  tries=$((tries+1))
  git fetch -q origin main || { echo "STOP_FETCH try=$tries $(date -u +%FT%TZ)" >> "$STATUS"; exit 1; }
  echo "TRY $tries MAIN=$(git rev-parse origin/main) HEAD=$(git rev-parse HEAD) $(date -u +%FT%TZ)" >> "$LOG"
  G1B_TASL_ENABLE_REAL=1 bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" g1b "$SPEC" "$NODE" "$NOTE" --enable >> "$LOG" 2>&1
  rc=$?
  A=$(ls -dt "$B"/runs/g1b-tasl-20261121-b/"$NODE"/attempt-* 2>/dev/null | head -1)
  echo "WRAPPER_RC try=$tries rc=$rc attempt=${A:-none} $(date -u +%FT%TZ)" >> "$LOG"
  if [ "$rc" -eq 0 ] && [ -n "$A" ]; then
    "$PY" "$P/sweep2/t1_tasl/g1b_tasl.py" seal "$A" "$SPEC" --node "$NODE" >> "$LOG" 2>&1
    src=$?
    echo "SEAL_RC rc=$src attempt=$A $(date -u +%FT%TZ)" >> "$LOG"
    if [ "$src" -eq 0 ]; then
      echo "DONE_SEALED $(date -u +%FT%TZ) attempt=$A" >> "$STATUS"
      exit 0
    fi
    echo "STOP_SEAL rc=$src attempt=$A $(date -u +%FT%TZ)" >> "$STATUS"
    exit 2
  fi
  cls=noattempt
  if [ -n "$A" ]; then
    cls=$("$PY" - "$A" <<PY
import json, sys
from pathlib import Path
try:
    print(json.loads((Path(sys.argv[1])/"job_record.json").read_text()).get("stop_class") or "none")
except Exception:
    print("missing")
PY
)
  fi
  echo "STOP_CLASS try=$tries class=$cls $(date -u +%FT%TZ)" >> "$LOG"
  if [ "$cls" = "infrastructure" ] && [ "$tries" -lt 2 ]; then
    echo "RETRY_INFRA try=$tries $(date -u +%FT%TZ)" >> "$LOG"
    continue
  fi
  echo "STOP rc=$rc class=$cls attempt=${A:-none} tries=$tries $(date -u +%FT%TZ)" >> "$STATUS"
  exit 1
done
