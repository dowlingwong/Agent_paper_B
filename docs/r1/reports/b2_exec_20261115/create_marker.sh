#!/bin/bash
# Create the B2 marker first (hand-off §5.3). Assumes the reviewed prechecks passed.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
STATUS="$RUN_DIR/status-receipt.md"
[ "$(git -C "$PAPER" rev-parse HEAD)" = "$HEAD" ] || { echo "STOP: HEAD mismatch" >&2; exit 1; }
[ -z "$(git -C "$PAPER" status --porcelain)" ] || { echo "STOP: checkout dirty" >&2; exit 1; }
[ -e "$STATUS" ] && { echo "STOP: local STATUS exists" >&2; exit 1; }
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && { echo "STOP: marker exists" >&2; exit 1; }
set -C
python3 "$PAPER/r1/scripts/b1_o2_marker.py" create --phase b2 \
  --lock-dir "$HOME/r1_locks" --status "$STATUS" --run-id "$RUN_ID" --head "$HEAD" \
  > "$RUN_DIR/marker-receipt.json" || { echo "STOP: marker create failed" >&2; exit 1; }
[ -s "$RUN_DIR/marker-receipt.json" ] || { echo "STOP: empty marker receipt" >&2; exit 1; }
cat "$RUN_DIR/marker-receipt.json"
cat "$STATUS"
