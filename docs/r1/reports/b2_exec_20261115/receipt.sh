#!/bin/bash
# Launch with a log and an exit record (B1 receipt pattern); no clobber, no retry.
set -u
set -o pipefail
umask 077
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
[ ! -e "$RUN_DIR/b2.log" ] || { printf 'STOP: b2.log already exists (no retry)\n' >&2; exit 1; }
[ ! -e "$RUN_DIR/b2.exit" ] || { printf 'STOP: b2.exit already exists (no retry)\n' >&2; exit 1; }
set -C
exec 3> "$RUN_DIR/b2.log" || { printf 'STOP: cannot create b2.log\n' >&2; exit 1; }
if /bin/bash "$RUN_DIR/start.sh" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nB2_EXIT=%s\n' "$rc" >&3 || { printf 'STOP: cannot write log footer\n' >&2; exit 1; }
printf '%s\n' "$rc" > "$RUN_DIR/b2.exit" || { printf 'STOP: cannot write exit file\n' >&2; exit 1; }
exit "$rc"
