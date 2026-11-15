#!/usr/bin/env bash
# Track S Phase 4 — S0.5b calibration/truncation sweep for tabular_mlp on TASL-7 (CPU-only, no servers).
# Authority: Track S operator runbook rev 3.3 Phase 4; the author's 14 Nov amendment (relayed by the Lead);
# the tabular S0.5 k=2 run. ENGINEERING_ONLY.
# Run after S0.5 has completed AND its servers are stopped.
# Run as: ssh tasl7 bash $R/launch/tasl7_tabular_s05b_20261114.sh
# Session name trks_s05bt_t7 is distinct from the DIGITS S0.5b session trks_s05b_t7 (log-file collision rule).
set -euo pipefail
R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; PATH=$R/bin:$PATH
RUN=$OUT/s05_t7_20261114; WRUN=$WORK/s05_t7_20261114; SESSION=trks_s05bt_t7
LOG=$R/logs/s05b_t7_tabular_20261114_launch.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  [ ! -e "$f" ] || { echo "REFUSE: priority marker $f" >&2; exit 2; }
done
tmux has-session -t "$SESSION" 2>/dev/null && { echo "REFUSE: $SESSION session already exists" >&2; exit 2; }
tmux has-session -t trks_llm 2>/dev/null && { echo "REFUSE: trks_llm still running; stop the S0.5 servers first" >&2; exit 2; }
pgrep -f 'llama-server .*--port 1810[12]' >/dev/null 2>&1 && { echo "REFUSE: an S0.5 llama-server is still running" >&2; exit 2; }
[ -s "$RUN/manifest.json" ] || { echo "REFUSE: $RUN/manifest.json missing; S0.5 not complete" >&2; exit 2; }
"$R/venv/bin/python" - "$RUN/manifest.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
sessions = d.get("sessions") or []
done = (sessions[-1].get("done") if sessions else None) or {}
status = done.get("status")
if status != "complete":
    raise SystemExit("REFUSE: S0.5 done.status=%r (need complete)" % (status,))
print("S0.5 manifest complete")
PY

mkdir -p "$RUN" "$WRUN"
log "Phase 4 S0.5b start (node tabular_mlp, host TASL-7, CPU, out $RUN)"
trks-run "$SESSION" - collect --phase S0.5b --node tabular_mlp --truncate-W 8,10,12,20 --out "$RUN" --work "$WRUN"
while tmux has-session -t "$SESSION" 2>/dev/null; do sleep 15; done
rc=$(sed -n 's/.*rc=//p' "$R/logs/$SESSION.exit" 2>/dev/null | tail -1)
log "S0.5b collector rc=${rc:-unknown}"
[ "${rc:-}" = 0 ] || { echo "S0.5b collector failed rc=${rc:-unknown}" >&2; exit 1; }
log "S0.5b DONE"
