#!/bin/bash
set -u
H=${1:?host}; shift
NODES="$*"
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_xc2
SPEC=$P/sweep2/t1_tasl/g1b_crosscheck_spec.json
NOTE=$P/docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md
PY=$B/envs/torch312/bin/python
TAG=$(echo "$H" | tr 'A-Z-' 'a-z_')
RUNID=g1b-tasl-20261121-b-xc2-$H
LOG=$B/logs/xc2_${TAG}_resume_20261122.log
STATUS=$B/logs/xc2_${TAG}_resume_20261122.status
C=$B/captures/xc2_20261122/$H
mkdir -p "$C" "$B/logs"
if [ -e "$STATUS" ] || [ -e "$LOG" ]; then echo "STOP: $STATUS or $LOG exists"; exit 9; fi
export G1B_TASL_ENABLE_REAL=1
export T1_TASL_ORCHESTRATOR_PYTHON="$PY"
export PYTHONDONTWRITEBYTECODE=1
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$H nodes=$NODES" >> "$LOG"
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$H nodes=$NODES" >> "$STATUS"
cd "$P" || { echo "STOP cd" >> "$STATUS"; exit 9; }
for N in $NODES; do
  git -C "$P" fetch -q origin main || { echo "STOP_FETCH $N" >> "$STATUS"; exit 1; }
  OM=$(git -C "$P" rev-parse origin/main)
  LM=$(git -C "$P" ls-remote origin refs/heads/main | cut -f1)
  echo "FETCH $N origin_main=$OM lsremote=$LM $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  echo "NODE_START $N $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  T0=$(date +%s)
  bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" xc "$SPEC" "$N" "$NOTE" "$H" --enable >> "$LOG" 2>&1
  rc=$?
  T1=$(date +%s)
  A=$(ls -dt "$B"/runs/"$RUNID"/"$N"/attempt-* 2>/dev/null | head -1)
  echo "NODE_RC $N rc=$rc wall_s=$((T1-T0)) end=$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt=${A:-none}" >> "$LOG"
  if [ "$rc" -ne 0 ] || [ -z "$A" ]; then
    echo "STOP $N rc=$rc attempt=${A:-none}" >> "$STATUS"
    if [ -n "$A" ] && [ -f "$A/job_record.json" ]; then cp "$A/job_record.json" "$C/$N.stop.job_record.json"; fi
    echo "STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
    exit 1
  fi
  DS=$B/runs/"$RUNID"/_specs/"$N".json
  "$PY" "$P/sweep2/t1_tasl/g1b_tasl.py" seal "$A" "$DS" --node "$N" >> "$LOG" 2>&1
  src=$?
  echo "SEAL_RC $N rc=$src $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  if [ "$src" -ne 0 ]; then echo "STOP_SEAL $N rc=$src" >> "$STATUS"; exit 2; fi
  SD=$(ls -d "$B"/sealed_g1b/"$RUNID"/"$N"/attempt-* 2>/dev/null | head -1)
  echo "SEALED $N $SD" >> "$LOG"
  "$PY" - "$A" "$SD" "$DS" "$N" "$H" > "$C/$N.record.json" 2>&1 <<'PY'
import json, sys
from pathlib import Path
a, sd, ds, node, host = sys.argv[1:6]
rec = json.loads((Path(a) / "job_record.json").read_text())
rcpt = json.loads((Path(sd) / "SEAL_RECEIPT.json").read_text())
out = {"node": node, "host": host, "attempt": rec.get("attempt"), "run_id": rec.get("run_id"),
       "spec_sha256": rec.get("spec_sha256"), "harness_commit": rec.get("harness_commit"),
       "stop": rec.get("stop"), "stop_class": rec.get("stop_class"),
       "parts": rec.get("parts"), "timing": rec.get("timing"), "determinism": rec.get("determinism"),
       "host_ident": rec.get("host"), "gpu": rec.get("gpu"), "lease": rec.get("lease"),
       "node_log": rec.get("node_log"), "started_utc": rec.get("started_utc"),
       "finished_utc": rec.get("finished_utc"), "runs": rec.get("runs"),
       "deadline_s": rec.get("deadline_s"), "sealed_path": str(sd), "receipt": rcpt}
print(json.dumps(out, indent=1, sort_keys=True))
PY
  ( cd "$SD" && sha256sum SEAL_RECEIPT.json job_record.json out.tar node.log SHA256SUMS ) > "$C/$N.sealed.sha256" 2>&1
  echo "CAPTURED $N $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
done
echo "DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATUS"
echo "DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
exit 0
