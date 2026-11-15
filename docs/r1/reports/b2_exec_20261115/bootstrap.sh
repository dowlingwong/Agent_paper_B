#!/bin/bash
# B2 bootstrap (host): create RUN_DIR + the empty local receipt STATUS that b1_o2_marker.py
# requires (it opens --status O_APPEND without O_CREAT). No marker, no STATUS publication.
set -eu
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
STATUS="$RUN_DIR/status-receipt.md"
[ "$HOME" = /home/dowling ] || { echo "STOP: HOME mismatch" >&2; exit 1; }
[ ! -e "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || { echo "STOP: RUN_DIR exists" >&2; exit 1; }
mkdir -m 700 "$RUN_DIR"
mkdir -m 700 "$RUN_DIR/prechecks" "$RUN_DIR/postmarker" "$RUN_DIR/monitor"
set -C
# exclusive creation of the empty receipt STATUS (owned regular file, no symlink)
: > "$STATUS" || { echo "STOP: cannot create status-receipt" >&2; exit 1; }
chmod 600 "$STATUS"
{ echo "bootstrap_utc=$(date -u +%FT%TZ)"; echo "head=$HEAD run_id=$RUN_ID";
  echo "run_dir=$RUN_DIR"; echo "status=$STATUS"; stat -c 'status dev=%d ino=%i mode=%A owner=%u' "$STATUS"; } \
  > "$RUN_DIR/bootstrap-receipt.txt"
echo "BOOTSTRAP_OK $RUN_DIR"
