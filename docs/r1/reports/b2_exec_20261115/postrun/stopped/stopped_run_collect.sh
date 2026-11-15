#!/bin/bash
# B2 stopped-run collection (host): preserve evidence after a STOP (no analysis requirement).
# Creates $RUN_DIR/postrun_stopped (fresh/absent); never deletes; no retry.
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
BATCH="/home/dowling/exam-x/work/b2_${RUN_ID}"
SO="$RUN_DIR/postrun_stopped"
stop() { echo "STOP: $*" >&2; exit 2; }
[ -s "$RUN_DIR/b2.exit" ] || stop "b2.exit missing (runner may still be running; do not collect yet)"
[ "$(cat "$RUN_DIR/b2.exit")" != 0 ] || stop "b2.exit is 0; use the normal postrun unit"
[ ! -e "$SO" ] || stop "postrun_stopped exists (no retry)"
mkdir -m 700 "$SO" || stop "cannot create postrun_stopped"
set -C
printf 'stopped_collect_utc=%s\nb2_exit=%s\n' "$(date -u +%FT%TZ)" "$(cat "$RUN_DIR/b2.exit")" > "$SO/STOPPED.txt"
cp -p "$RUN_DIR/b2.log" "$SO/b2.log" 2>/dev/null || stop "cannot copy b2.log"
cp -p "$BATCH/batch_state.json" "$SO/batch_state.json" 2>/dev/null || echo "batch_state absent" > "$SO/batch_state.absent.txt"
find "$BATCH" -name campaign_manifest.json -printf '%p\n' 2>/dev/null | sort > "$SO/manifests.txt"
find "$BATCH" -name b1_proposals.jsonl -printf '%p\n' 2>/dev/null | sort > "$SO/journals.txt"
python3 - "$SO" "$RUN_DIR" <<'PY' || stop "state summary failed"
import json, sys
from pathlib import Path
so, rd = Path(sys.argv[1]), Path(sys.argv[2])
try: st = json.loads((so / 'batch_state.json').read_text())
except Exception: st = {}
summary = {'exit': (rd / 'b2.exit').read_text().strip(), 'batch_status': st.get('status'),
           'completed': len(st.get('completed') or {}), 'manifests': len((so/'manifests.txt').read_text().splitlines()),
           'journals': len((so/'journals.txt').read_text().splitlines()),
           'marker_present': (Path.home()/'r1_locks'/'trackx_evidence.active').exists()}
(so / 'STOPPED_STATE.json').write_text(json.dumps(summary, indent=1) + '\n')
print(json.dumps(summary, indent=1))
PY
sha256sum "$SO"/* > "$SO/SHA256SUMS" 2>/dev/null || true
set -C; printf 'STOPPED_COLLECT_OK\n' > "$SO/STOPPED_COLLECT_OK" || stop "cannot write ok receipt"
echo "STOPPED_COLLECT_OK $SO"
