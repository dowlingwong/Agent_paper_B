#!/bin/bash
# Retire ONLY this run's marker after a collected STOP (hand-off §5.9 "stopped for good").
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
stop() { echo "STOP: $*" >&2; exit 2; }
[ -s "$RUN_DIR/postrun_stopped/STOPPED_COLLECT_OK" ] || stop "stopped collection not complete"
( cd "$RUN_DIR/postrun_stopped" && sha256sum -c SHA256SUMS >/dev/null ) || stop "stopped artifact SHA-256 verification failed"
python3 - "$RUN_DIR/marker-receipt.json" "$RUN_ID" "$HEAD" <<'PY' || stop "run id/head not bound to marker receipt"
import json, sys
d = json.load(open(sys.argv[1]))
if d.get('run_id') != sys.argv[2] or d.get('head') != sys.argv[3]:
    raise SystemExit('STOP: marker receipt run_id/head mismatch')
PY
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker already absent"
[ ! -e "$RUN_DIR/marker-retirement-stopped.json" ] || stop "retirement receipt exists (no retry)"
pgrep -f "python.*-B -m r1\.scripts\.exam_runner b2 " >/dev/null 2>&1 && stop "runner still running"
set -C
python3 "$PAPER/r1/scripts/b1_o2_marker.py" retire --lock-dir "$HOME/r1_locks" \
  --receipt "$RUN_DIR/marker-receipt.json" > "$RUN_DIR/marker-retirement-stopped.json" || stop "retirement primitive failed"
[ -s "$RUN_DIR/marker-retirement-stopped.json" ] || stop "empty retirement receipt"
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && stop "marker still present"
echo "MARKER_RETIRED_STOPPED"; cat "$RUN_DIR/marker-retirement-stopped.json"
