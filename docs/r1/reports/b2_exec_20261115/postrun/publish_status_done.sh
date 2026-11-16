#!/bin/bash
# Publish "Track X B2 done" from a clean separate checkout of mac-b1-20261107 (hand-off §5.9).
# Runs on the Mac: the status checkout is local; every host gate is read over ssh to TASL-7.
# Gated on exit 0, marker retirement, verified analysis, and the complete POSTRUN_COLLECT_OK set.
set -eu
umask 077
SC="${1:?status checkout}"; RUN_ID="${2:?run id}"; HEAD="${3:?head}"; DAY=$(date -u +%F)
BRANCH=mac-b1-20261107
RUN_DIR=/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2
SSH="ssh -o BatchMode=yes -o ConnectTimeout=20 tasl7"
stop() { echo "STOP: $*" >&2; exit 2; }
[ -z "$(git -C "$SC" status --porcelain)" ] || stop "status checkout dirty"
[ "$(git -C "$SC" rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || stop "status branch mismatch"
LOCAL=$(git -C "$SC" rev-parse HEAD); REMOTE=$(git -C "$SC" ls-remote origin "refs/heads/$BRANCH" | awk '{print $1}')
[ "$LOCAL" = "$REMOTE" ] || stop "status branch advanced"
# ---- host gates (TASL-7), read over ssh: the run dir is a host path, not a local path ----
$SSH "test -s '$RUN_DIR/b2.exit' && [ \"\$(cat '$RUN_DIR/b2.exit')\" = 0 ]" || stop "b2.exit is not 0"
$SSH "test -s '$RUN_DIR/marker-retirement.json'" || stop "marker not retired"
# bind the requested RUN_ID/HEAD to the run's own marker receipt (never trust the caller's arguments alone)
$SSH "python3 - '$RUN_DIR/marker-receipt.json' '$RUN_ID' '$HEAD' <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if d.get('run_id') != sys.argv[2] or d.get('head') != sys.argv[3]:
    raise SystemExit('STOP: marker receipt run_id/head mismatch')
PY" || stop "run id/head not bound to marker receipt"
$SSH "test -s '$RUN_DIR/postrun/POSTRUN_COLLECT_OK' && test -s '$RUN_DIR/postrun/analysis.json' && test -s '$RUN_DIR/postrun/invalid_trials.json' && test -s '$RUN_DIR/postrun/b2_manifests.json' && test -s '$RUN_DIR/postrun/batch_state.json'" || stop "incomplete POSTRUN_COLLECT_OK set"
$SSH "grep -q '^analysis_rc=0$' '$RUN_DIR/postrun/POSTRUN_COLLECT_OK'" || stop "collected analysis rc is not 0"
$SSH "test \"\$(grep -c '^[0-9a-f]\\{64\\}  ' '$RUN_DIR/postrun/POSTRUN_COLLECT_OK')\" -eq 4" || stop "POSTRUN_COLLECT_OK does not list all four artifact hashes"
$SSH "for a in analysis.json batch_state.json b2_manifests.json invalid_trials.json; do grep -Eq '^[0-9a-f]{64}  '\$a'\$' '$RUN_DIR/postrun/POSTRUN_COLLECT_OK' || exit 1; done" || stop "POSTRUN_COLLECT_OK artifact list incomplete"
$SSH "cd '$RUN_DIR/postrun' && sha256sum -c SHA256SUMS >/dev/null" || stop "postrun artifact SHA-256 verification failed"
python3 - "$SC/docs/r1/STATUS.md" "$RUN_ID" "$HEAD" "$DAY" <<'PY' || stop "STATUS append refused"
import sys, pathlib
p = pathlib.Path(sys.argv[1]); run_id, head, day = sys.argv[2], sys.argv[3], sys.argv[4]
text = p.read_text(); new = f"\n## {day} — Track X B2 done\n\nRun: `{run_id}`; reviewed checkout HEAD: `{head}`.\n"
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
