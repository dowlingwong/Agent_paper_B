#!/bin/bash
# Deliver the reviewed exec files into $RUN_DIR (no-clobber) and verify their SHA-256.
# Run on the Mac from this directory after bootstrap.sh succeeded on TASL-7.
set -eu
umask 077
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
FILES="prechecks.sh inventory_after.sh create_marker.sh postwatch_check.sh preflight.sh start.sh receipt.sh publish_status.sh monitor.sh pins/expected.txt pins/venv_pins.txt"
for f in $FILES; do
  [ -f "$f" ] || { echo "STOP: local file missing $f" >&2; exit 1; }
  b=$(basename "$f")
  if ssh -o BatchMode=yes tasl7 "test -e '$RUN_DIR/$b'"; then echo "STOP: remote file exists $b" >&2; exit 2; fi
  ssh -o BatchMode=yes tasl7 "set -C; cat > '$RUN_DIR/$b'" < "$f"
  ssh -o BatchMode=yes tasl7 "chmod 700 '$RUN_DIR/$b'"
  l=$(sha256sum "$f" | awk '{print $1}')
  r=$(ssh -o BatchMode=yes tasl7 "sha256sum '$RUN_DIR/$b'" | awk '{print $1}')
  [ "$l" = "$r" ] || { echo "STOP: delivered sha mismatch $b $l $r" >&2; exit 3; }
  echo "delivered $b $r"
done
ssh -o BatchMode=yes tasl7 "printf 'delivered_utc=%s\n' \"\$(date -u +%FT%TZ)\" >> '$RUN_DIR/delivered-receipt.txt'; sha256sum '$RUN_DIR'/prechecks.sh '$RUN_DIR'/create_marker.sh '$RUN_DIR'/preflight.sh '$RUN_DIR'/start.sh >> '$RUN_DIR/delivered-receipt.txt'"
echo "DELIVER_OK"
