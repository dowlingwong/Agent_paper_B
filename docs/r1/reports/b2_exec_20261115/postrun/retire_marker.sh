#!/bin/bash
# Retire ONLY this run's marker after verified normal completion (hand-off §5.9), under this
# reviewed post-run unit. Fails closed; preserves the scene on any mismatch.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
stop() { echo "STOP: $*" >&2; exit 2; }
[ "$(cat "$RUN_DIR/b2.exit" 2>/dev/null)" = 0 ] || stop "b2.exit is not 0; marker must stay"
OK="$RUN_DIR/postrun/POSTRUN_COLLECT_OK"
[ -s "$OK" ] && grep -q '^analysis_rc=0$' "$OK" || stop "postrun collection not complete/passed"
[ "$(grep -c '^[0-9a-f]\{64\}  ' "$OK")" -eq 4 ] || stop "POSTRUN_COLLECT_OK does not list all four artifact hashes"
for a in analysis.json batch_state.json b2_manifests.json invalid_trials.json; do
  grep -Eq "^[0-9a-f]{64}  $a\$" "$OK" || stop "POSTRUN_COLLECT_OK artifact list is missing $a"
done
( cd "$RUN_DIR/postrun" && sha256sum -c SHA256SUMS >/dev/null ) || stop "postrun artifact SHA-256 verification failed"
python3 - "$RUN_DIR/marker-receipt.json" "$RUN_ID" "$HEAD" <<'PY' || stop "run id/head not bound to marker receipt"
import json, sys
d = json.load(open(sys.argv[1]))
if d.get('run_id') != sys.argv[2] or d.get('head') != sys.argv[3]:
    raise SystemExit('STOP: marker receipt run_id/head mismatch')
PY
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker already absent"
[ ! -e "$RUN_DIR/marker-retirement.json" ] || stop "retirement receipt already exists (no retry)"
pgrep -f "python.*-B -m r1\.scripts\.exam_runner b2 " >/dev/null 2>&1 && stop "runner still running"
set -C
python3 "$PAPER/r1/scripts/b1_o2_marker.py" retire --lock-dir "$HOME/r1_locks" \
  --receipt "$RUN_DIR/marker-receipt.json" > "$RUN_DIR/marker-retirement.json" || stop "retirement primitive failed"
[ -s "$RUN_DIR/marker-retirement.json" ] || stop "empty retirement receipt"
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && stop "marker still present after retirement"
echo "MARKER_RETIRED"; cat "$RUN_DIR/marker-retirement.json"
