#!/bin/bash
# Publish the running STATUS from a clean separate checkout of mac-b1-20261107 (hand-off §5.4).
# Run on the Mac. Usage: publish_status.sh <status_checkout_dir> <run_id> <head>
set -eu
umask 077
SC="${1:?status checkout}"; RUN_ID="${2:?run id}"; HEAD="${3:?head}"
BRANCH=mac-b1-20261107
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
stop() { echo "STOP: $*" >&2; exit 2; }
case "$HEAD" in *[!0-9a-f]*|'') stop "bad head";; esac
[ "${#HEAD}" -eq 40 ] || stop "bad head length"
[ -d "$SC" ] && [ ! -L "$SC" ] || stop "status checkout missing"
[ -z "$(git -C "$SC" status --porcelain)" ] || stop "status checkout dirty"
[ "$(git -C "$SC" rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || stop "status checkout branch mismatch"
[ -s "$SC/docs/r1/STATUS.md" ] || stop "STATUS.md missing"
ssh -o BatchMode=yes tasl7 "test -s '$RUN_DIR/marker-receipt.json'" || stop "marker receipt absent on host"
LOCAL=$(git -C "$SC" rev-parse HEAD)
REMOTE=$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
[ "$LOCAL" = "$REMOTE" ] || stop "status branch advanced since checkout (local $LOCAL remote $REMOTE)"
python3 - "$SC/docs/r1/STATUS.md" "$RUN_ID" "$HEAD" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); run_id, head = sys.argv[2], sys.argv[3]
text = p.read_text()
new = f"\n## 2026-11-15 — Track X B2 running\n\nRun: `{run_id}`; reviewed checkout HEAD: `{head}`.\n"
if new in text: raise SystemExit('STOP: heading already present')
p.write_text(text + new)
print('STATUS_APPENDED')
PY
git -C "$SC" add docs/r1/STATUS.md
git -C "$SC" -c user.name="Dowling Wong" -c user.email="dowling@users.noreply.github.com" \
  commit -m "STATUS: Track X B2 running ($RUN_ID, HEAD $HEAD)" || stop "commit failed"
COMMIT=$(git -C "$SC" rev-parse HEAD)
git -C "$SC" push origin "HEAD:refs/heads/$BRANCH" || stop "push failed (marker preserved; no force, no retry)"
REMOTE2=$(git ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
[ "$REMOTE2" = "$COMMIT" ] || stop "remote verification failed ($REMOTE2 != $COMMIT)"
{ echo "status_branch=$BRANCH"; echo "commit=$COMMIT"; echo "head=$HEAD"; echo "run_id=$RUN_ID";
  echo "published_utc=$(date -u +%FT%TZ)"; } > "$SC/../b2_status_receipt.txt" 2>/dev/null || true
echo "STATUS_PUBLISHED $BRANCH $COMMIT"
