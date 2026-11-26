#!/bin/bash
set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_ar
SPEC=$P/sweep2/t1_tasl/g1b_tasl_ar_spec.json
NOTE=$P/docs/r1/authorizations/g1b_ar_t1_tasl_20261122.md
LOG=$B/logs/ar_g1b_tasl2.log
STATUS=$B/logs/ar_g1b_tasl2.status
cd "$P" && git fetch -q origin main || { echo STOP_FETCH >> "$STATUS"; exit 1; }
echo "START $(date -u +%FT%TZ) main=$(git rev-parse origin/main) HEAD=$(git rev-parse HEAD)" >> "$LOG"
G1B_TASL_ENABLE_REAL=1 bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" g1b "$SPEC" autoresearch_fixedtokens "$NOTE" --enable >> "$LOG" 2>&1
rc=$?
A=$(ls -dt "$B"/runs/g1b-ar-tasl-20261122-a/autoresearch_fixedtokens/attempt-* 2>/dev/null | head -1)
echo "NODE_RC rc=$rc attempt=$A" >> "$LOG"
if [ "$rc" -eq 0 ] && [ -n "$A" ]; then
  /home/dowling/r1_trackp/venvs/ar-cond7a/bin/python "$P/sweep2/t1_tasl/g1b_tasl.py" seal "$A" "$SPEC" --node autoresearch_fixedtokens >> "$LOG" 2>&1
  echo "SEAL_RC rc=$?" >> "$LOG"
  echo "DONE $(date -u +%FT%TZ)" >> "$STATUS"
else
  echo "STOP rc=$rc $(date -u +%FT%TZ)" >> "$STATUS"
fi
