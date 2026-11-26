#!/bin/bash
# Publish "Track X B2 stopped" from a clean separate checkout of mac-b1-20261107.
# Runs on the Mac: the status checkout is local; every host gate is read over ssh to TASL-7.
set -eu
umask 077
SC="${1:?status checkout}"; RUN_ID="${2:?run id}"; HEAD="${3:?head}"; DAY=$(date -u +%F)
BRANCH=mac-b1-20261107
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20 tasl7"
stop() { echo "STOP: $*" >&2; exit 2; }
[ -z "$(git -C "$SC" status --porcelain)" ] || stop "status checkout dirty"
[ "$(git -C "$SC" rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || stop "branch mismatch"
[ "$(git -C "$SC" rev-parse HEAD)" = "$(git -C "$SC" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')" ] || stop "status branch advanced"
# ---- host gates (TASL-7), read over ssh ----
$SSH "test -s '$RUN_DIR/postrun_stopped/STOPPED_COLLECT_OK'" || stop "stopped collection incomplete"
$SSH "test -s '$RUN_DIR/marker-retirement-stopped.json'" || stop "marker not retired (stopped path)"
$SSH "python3 - '$RUN_DIR/marker-receipt.json' '$RUN_ID' '$HEAD' <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if d.get('run_id') != sys.argv[2] or d.get('head') != sys.argv[3]:
    raise SystemExit('STOP: marker receipt run_id/head mismatch')
PY" || stop "run id/head not bound to marker receipt"
$SSH "cd '$RUN_DIR/postrun_stopped' && sha256sum -c SHA256SUMS >/dev/null" || stop "stopped artifact SHA-256 verification failed"
python3 - "$SC/docs/r1/STATUS.md" "$RUN_ID" "$HEAD" "$DAY" <<'PY' || stop "append refused"
import sys, pathlib
p = pathlib.Path(sys.argv[1]); run_id, head, day = sys.argv[2], sys.argv[3], sys.argv[4]
text = p.read_text(); new = f"\n## {day} — Track X B2 stopped\n\nRun: `{run_id}`; reviewed checkout HEAD: `{head}`.\n"
if new in text: raise SystemExit('STOP: heading already present')
p.write_text(text + new)
PY
git -C "$SC" add docs/r1/STATUS.md
git -C "$SC" -c user.name="Dowling Wong" -c user.email="wangdowling@gmail.com" \
  commit -m "STATUS: Track X B2 stopped ($RUN_ID, HEAD $HEAD)" || stop "commit failed"
COMMIT=$(git -C "$SC" rev-parse HEAD)
git -C "$SC" push origin "HEAD:refs/heads/$BRANCH" || stop "push failed (no force, no retry)"
[ "$(git -C "$SC" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')" = "$COMMIT" ] || stop "remote verification failed"
OUT="${B2_STATUS_RECEIPT:-/tmp/b2_status_stopped_receipt.txt}"; [ ! -e "$OUT" ] || stop "receipt exists"
printf 'status_branch=%s\ncommit=%s\nrun_id=%s\nhead=%s\npublished_utc=%s\n' "$BRANCH" "$COMMIT" "$RUN_ID" "$HEAD" "$(date -u +%FT%TZ)" > "$OUT"
echo "STATUS_STOPPED_PUBLISHED $COMMIT"
