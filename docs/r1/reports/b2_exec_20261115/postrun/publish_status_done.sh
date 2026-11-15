#!/bin/bash
# Publish "Track X B2 done" from a clean separate checkout of mac-b1-20261107 (hand-off §5.9).
# Gated on exit 0, marker retirement, verified analysis, and the complete POSTRUN_COLLECT_OK set.
set -eu
umask 077
SC="${1:?status checkout}"; RUN_ID="${2:?run id}"; HEAD="${3:?head}"
BRANCH=mac-b1-20261107
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
stop() { echo "STOP: $*" >&2; exit 2; }
[ -z "$(git -C "$SC" status --porcelain)" ] || stop "status checkout dirty"
[ "$(git -C "$SC" rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || stop "status branch mismatch"
LOCAL=$(git -C "$SC" rev-parse HEAD); REMOTE=$(git -C "$SC" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
[ "$LOCAL" = "$REMOTE" ] || stop "status branch advanced"
[ -s "$RUN_DIR/b2.exit" ] && [ "$(cat "$RUN_DIR/b2.exit")" = 0 ] || stop "b2.exit is not 0"
[ -s "$RUN_DIR/marker-retirement.json" ] || stop "marker not retired"
ssh -o BatchMode=yes tasl7 "test -s '$RUN_DIR/postrun/POSTRUN_COLLECT_OK' && test -s '$RUN_DIR/postrun/analysis.json' && test -s '$RUN_DIR/postrun/invalid_trials.json' && test -s '$RUN_DIR/postrun/b2_manifests.json' && test -s '$RUN_DIR/postrun/batch_state.json'" || stop "incomplete POSTRUN_COLLECT_OK set"
ssh -o BatchMode=yes tasl7 "grep -q 'analysis_rc=0' '$RUN_DIR/postrun/POSTRUN_COLLECT_OK'" || stop "collected analysis rc is not 0"
python3 - "$SC/docs/r1/STATUS.md" "$RUN_ID" "$HEAD" <<'PY' || stop "STATUS append refused"
import sys, pathlib
p = pathlib.Path(sys.argv[1]); run_id, head = sys.argv[2], sys.argv[3]
text = p.read_text(); new = f"\n## 2026-11-15 — Track X B2 done\n\nRun: `{run_id}`; reviewed checkout HEAD: `{head}`.\n"
if new in text: raise SystemExit('STOP: heading already present')
p.write_text(text + new)
PY
git -C "$SC" add docs/r1/STATUS.md
git -C "$SC" -c user.name="Dowling Wong" -c user.email="wangdowling@gmail.com" \
  commit -m "STATUS: Track X B2 done ($RUN_ID, HEAD $HEAD)" || stop "commit failed"
COMMIT=$(git -C "$SC" rev-parse HEAD)
git -C "$SC" push origin "HEAD:refs/heads/$BRANCH" || stop "push failed (no force, no retry)"
[ "$(git -C "$SC" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')" = "$COMMIT" ] || stop "remote verification failed"
OUT="${B2_STATUS_RECEIPT:-/tmp/b2_status_done_receipt.txt}"
[ ! -e "$OUT" ] || stop "receipt exists"
printf 'status_branch=%s\ncommit=%s\nrun_id=%s\nhead=%s\npublished_utc=%s\n' "$BRANCH" "$COMMIT" "$RUN_ID" "$HEAD" "$(date -u +%FT%TZ)" > "$OUT"
echo "STATUS_DONE_PUBLISHED $COMMIT"
