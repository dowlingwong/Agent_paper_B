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
if find "$BATCH" -name campaign_manifest.json -printf '%p\n' 2>/dev/null | sort > "$SO/manifests.txt"; then :; else echo "manifest list failed" >&2; exit 2; fi
if find "$BATCH" -name b1_proposals.jsonl -printf '%p\n' 2>/dev/null | sort > "$SO/journals.txt"; then :; else echo "journal list failed" >&2; exit 2; fi
[ -s "$SO/manifests.txt" ] || echo "EMPTY_MANIFEST_LIST" > "$SO/manifests.empty.txt"
[ -s "$SO/journals.txt" ] || echo "EMPTY_JOURNAL_LIST" > "$SO/journals.empty.txt"
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
# deterministic artifact set: the batch state may legitimately be absent; nothing is silenced
ARTS="STOPPED.txt STOPPED_STATE.json"
if [ -s "$SO/batch_state.json" ]; then ARTS="$ARTS batch_state.json"; else [ -e "$SO/batch_state.absent.txt" ] || stop "batch_state neither copied nor marked absent"; ARTS="$ARTS batch_state.absent.txt"; fi
( cd "$SO" && sha256sum $ARTS > SHA256SUMS ) || stop "cannot write SHA256SUMS"
( cd "$SO" && sha256sum -c SHA256SUMS >/dev/null ) || stop "stopped artifact SHA-256 verification failed"
# collection-ok receipt: built completely in a temp file, validated, then renamed atomically
OK="$SO/STOPPED_COLLECT_OK"; TMP="$SO/STOPPED_COLLECT_OK.tmp"
[ ! -e "$OK" ] || stop "STOPPED_COLLECT_OK already exists"
[ ! -e "$TMP" ] || stop "STOPPED_COLLECT_OK.tmp already exists"
{
  echo "stopped_collect_ok_utc=$(date -u +%FT%TZ)"
  ( cd "$SO" && sha256sum $ARTS ) | sed 's# .*/# #'
} > "$TMP" || stop "cannot write STOPPED_COLLECT_OK.tmp"
[ "$(grep -c '^[0-9a-f]\{64\}  ' "$TMP")" -ge 2 ] || stop "STOPPED_COLLECT_OK artifact hash lines incomplete"
mv "$TMP" "$OK" || stop "cannot finalise STOPPED_COLLECT_OK"
echo "STOPPED_COLLECT_OK $SO"
