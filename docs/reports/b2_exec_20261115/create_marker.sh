#!/bin/bash
# Create the B2 marker first (hand-off §5.3). Requires bootstrap-created RUN_DIR and the
# pre-created empty local receipt STATUS (b1_o2_marker.py opens --status O_APPEND without O_CREAT).
set -eu
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
STATUS="$RUN_DIR/status-receipt.md"
[ "$HOME" = /home/dowling ] || { echo "STOP: HOME mismatch" >&2; exit 1; }
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || { echo "STOP: RUN_DIR missing" >&2; exit 1; }
[ -s "$RUN_DIR/prechecks/prechecks.ok" ] || { echo "STOP: prechecks not passed" >&2; exit 1; }
[ -f "$STATUS" ] && [ ! -L "$STATUS" ] && [ -O "$STATUS" ] || { echo "STOP: receipt STATUS missing/not owned" >&2; exit 1; }
[ "$(stat -c %s "$STATUS")" -eq 0 ] || { echo "STOP: receipt STATUS not empty" >&2; exit 1; }
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && { echo "STOP: marker exists" >&2; exit 1; }
[ "$(git -C "$PAPER" rev-parse HEAD)" = "$HEAD" ] || { echo "STOP: HEAD mismatch" >&2; exit 1; }
[ -z "$(git -C "$PAPER" status --porcelain)" ] || { echo "STOP: checkout dirty" >&2; exit 1; }
set -C
python3 "$PAPER/r1/scripts/b1_o2_marker.py" create --phase b2 \
  --lock-dir "$HOME/r1_locks" --status "$STATUS" --run-id "$RUN_ID" --head "$HEAD" \
  > "$RUN_DIR/marker-receipt.json" || { echo "STOP: marker create failed" >&2; exit 1; }
[ -s "$RUN_DIR/marker-receipt.json" ] || { echo "STOP: empty marker receipt" >&2; exit 1; }
python3 - "$RUN_DIR/marker-receipt.json" "$RUN_ID" "$HEAD" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
assert r.get('run_id') == sys.argv[2], 'run_id mismatch'
assert r.get('head') == sys.argv[3], 'head mismatch'
assert isinstance(r.get('ino'), int) and isinstance(r.get('dev'), int) and len(r.get('sha256','')) == 64
print('MARKER_RECEIPT_OK', r['run_id'], r['head'], r['dev'], r['ino'], r['sha256'])
PY
bash "$RUN_DIR/inventory_after.sh" || { echo "STOP: post-marker inventory failed" >&2; exit 1; }
echo "MARKER_CREATED"; cat "$STATUS"
