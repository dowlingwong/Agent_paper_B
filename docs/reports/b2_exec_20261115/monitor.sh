#!/bin/bash
# B2 30-minute monitor capture (run on the host; append-only new files in $RUN_DIR/monitor/).
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
BATCH="/home/dowling/exam-x/work/b2_${RUN_ID}"
TS=$(date -u +%Y%m%dT%H%M%SZ)
D="$RUN_DIR/monitor/$TS"
[ -e "$D" ] && { echo "STOP: monitor dir exists" >&2; exit 1; }
mkdir -m 700 "$D" -p || exit 1
{
  echo "capture_utc=$(date -u +%FT%TZ) host=$(hostname)"
  echo "== runner process =="; pgrep -a -f "exam_runner b2" || echo "RUNNER_NOT_RUNNING"
  echo "== exit (if finished) =="; cat "$RUN_DIR/b2.exit" 2>/dev/null || echo "no b2.exit yet"
  echo "== log tail =="; tail -20 "$RUN_DIR/b2.log" 2>/dev/null
  echo "== batch_state =="; cat "$BATCH/batch_state.json" 2>/dev/null | head -40
  echo "== manifests =="; find "$BATCH" -name manifest.json -printf '%T@ %s %p\n' 2>/dev/null | sort | tail -20
  echo "== journal =="; find "$BATCH" -name "b1_proposals.jsonl" -printf '%T@ %s %p\n' 2>/dev/null | tail -5
  echo "== gpu =="; nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader 2>&1 | head -5
  echo "== lease =="; if flock -n /home/dowling/r1_locks/gpu0.lock true; then echo LEASE-FREE; else echo LEASE-HELD; fi
  echo "== marker =="; [ -e /home/dowling/r1_locks/trackx_evidence.active ] && echo MARKER_PRESENT || echo MARKER_ABSENT
} > "$D/capture.txt" 2>&1
sha256sum "$D"/* > "$D/SHA256SUMS" 2>/dev/null || true
echo "MONITOR_CAPTURE $D"
