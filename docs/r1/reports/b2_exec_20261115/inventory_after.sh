#!/bin/bash
# Post-marker inventory (same commands as prechecks, separate files). Read-only.
set -u
set -o pipefail
umask 077
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
PD="$RUN_DIR/postmarker"
[ -d "$PD" ] && [ ! -L "$PD" ] || { echo "missing postmarker dir" >&2; exit 1; }
[ -e "$PD/manifest_inventory_after.txt" ] && { echo "postmarker inventory exists" >&2; exit 1; }
set -C
: > "$PD/find.err" || exit 1
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PD/find.err" > "$PD/manifest_inventory_after.txt" || { echo "STOP: manifest find failed" >&2; exit 2; }
[ -s "$PD/find.err" ] && { echo "STOP: traversal error" >&2; exit 3; }
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PD/find.err" > "$PD/stop_inventory_after.txt" || { echo "STOP: STOP find failed" >&2; exit 2; }
[ -s "$PD/find.err" ] && { echo "STOP: traversal error" >&2; exit 3; }
sha256sum "$PD"/* > "$PD/SHA256SUMS"
echo "INVENTORY_AFTER_OK $PD"
