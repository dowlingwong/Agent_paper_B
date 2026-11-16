#!/bin/bash
# Deliver the reviewed exec files into $RUN_DIR (no-clobber) and verify the reviewed bytes.
# Run on the Mac from this directory (docs/r1/reports/b2_exec_20261115) at the pinned exec commit.
# Usage: REVIEWED_EXEC_SHA=<40-hex> bash deliver.sh
set -eu
umask 077
EXEC="${REVIEWED_EXEC_SHA:?set REVIEWED_EXEC_SHA to the reviewed exec commit}"
case "$EXEC" in *[!0-9a-f]*|'') echo "STOP: bad REVIEWED_EXEC_SHA" >&2; exit 1;; esac
[ "${#EXEC}" -eq 40 ] || { echo "STOP: wrong length" >&2; exit 1; }
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
FILES="prechecks.sh inventory_after.sh create_marker.sh postwatch_check.sh preflight.sh start.sh receipt.sh monitor.sh pins/expected.txt pins/venv_pins.txt pins/watcher_expected.txt"
HERE=$(git rev-parse --show-toplevel)
[ "$HERE" = "/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-b2-20261115" ] || { echo "STOP: run from the b2 exec worktree" >&2; exit 2; }
[ "$(git -C "$HERE" rev-parse HEAD)" = "$EXEC" ] || { echo "STOP: local HEAD != REVIEWED_EXEC_SHA" >&2; exit 3; }
[ -z "$(git -C "$HERE" status --porcelain)" ] || { echo "STOP: exec worktree dirty" >&2; exit 4; }
REMOTE=$(git -C "$HERE" ls-remote origin refs/heads/ops-b2-exec-20261115 | awk '{print $1}')
[ "$REMOTE" = "$EXEC" ] || { echo "STOP: origin exec branch != reviewed commit ($REMOTE)" >&2; exit 5; }
[ "$(ssh -o BatchMode=yes tasl7 hostname)" = TASL-7 ] || { echo "STOP: remote host is not TASL-7" >&2; exit 6; }
ssh -o BatchMode=yes tasl7 "[ -d '$RUN_DIR' ] && [ ! -L '$RUN_DIR' ]" || { echo "STOP: RUN_DIR missing/symlink" >&2; exit 7; }
REC="$RUN_DIR/delivered-receipt.txt"
LOCALREC="$HERE/docs/r1/reports/b2_exec_20261115/delivered-receipt.local.txt"
ssh -o BatchMode=yes tasl7 "test ! -e '$REC'" || { echo "STOP: host delivered-receipt exists (no retry)" >&2; exit 8; }
[ ! -e "$LOCALREC" ] || { echo "STOP: local delivered-receipt exists (no retry)" >&2; exit 8; }
set -C
: > "$LOCALREC" || { echo "STOP: cannot create local receipt" >&2; exit 8; }
ssh -o BatchMode=yes tasl7 "set -C; { echo 'exec_commit=$EXEC'; echo 'delivered_utc=$(date -u +%FT%TZ)'; echo 'files:'; } > '$REC'" || { echo "STOP: cannot create host receipt" >&2; exit 8; }
{ echo "exec_commit=$EXEC"; echo "delivered_utc=$(date -u +%FT%TZ)"; echo "files:"; } >> "$LOCALREC"
for f in $FILES; do
  b=$(basename "$f")
  [ -f "$f" ] || { echo "STOP: local file missing $f" >&2; exit 9; }
  reviewed=$(git -C "$HERE" show "$EXEC:docs/r1/reports/b2_exec_20261115/$f" | sha256sum | awk '{print $1}')
  local_sha=$(sha256sum "$f" | awk '{print $1}')
  [ "$reviewed" = "$local_sha" ] || { echo "STOP: local bytes differ from reviewed commit: $f" >&2; exit 10; }
  ssh -o BatchMode=yes tasl7 "test -e '$RUN_DIR/$b'" && { echo "STOP: remote file exists $b" >&2; exit 11; }
  ssh -o BatchMode=yes tasl7 "set -C; cat > '$RUN_DIR/$b'" < "$f"
  ssh -o BatchMode=yes tasl7 "chmod 700 '$RUN_DIR/$b'"
  remote_sha=$(ssh -o BatchMode=yes tasl7 "sha256sum '$RUN_DIR/$b'" | awk '{print $1}')
  [ "$remote_sha" = "$reviewed" ] || { echo "STOP: delivered sha mismatch $b ($remote_sha != $reviewed)" >&2; exit 12; }
  echo "  $b sha256=$reviewed" >> "$LOCALREC"
  ssh -o BatchMode=yes tasl7 "printf '  %s sha256=%s\\n' '$b' '$reviewed' >> '$REC'" || { echo "STOP: cannot append host receipt" >&2; exit 12; }
done
ssh -o BatchMode=yes tasl7 "cat '$REC'" >/dev/null || { echo "STOP: host receipt unreadable" >&2; exit 12; }
echo "DELIVER_OK $EXEC (host receipt $REC, local $LOCALREC)"
