#!/usr/bin/env bash
# Track S Phase 1 — S0.1 LLM determinism, latency and CPU census for tabular_mlp on TASL-7 (host move).
# Authority: Track S operator runbook rev 3.3 Phase 1; reports/TRACKS_S01_TASL7_RESULT_20261113.md (the
# reviewed digits TASL-7 S0.1 discipline); the author's 14 Nov amendment (add a tabular_mlp S0.1 re-run at
# the new pin 8237fd02, k=2, after S0.4 and before S0.5); R1-CACHEPROMPT-FALSE (cache_prompt=false carried by
# the pinned harness). ENGINEERING_ONLY.
#
# Session names are trks_s01t_serial / trks_s01t_conc, NOT trks_s01_serial / trks_s01_conc: the latter are
# the DIGITS TASL-7 S0.1's log/exit files (logs/trks_s01_{serial,conc}.{cmd,log,exit}, 13 Nov) and trks-run
# would overwrite/append them; this keeps the digits evidence intact.
#
# Servers must already be running with k = 2 (runbook):
#   tmux new -d -s trks_llm $R/bin/trks-servers 2
# Run as: ssh tasl7 bash $R/launch/tasl7_tabular_s01_20261114.sh
# The operator records the llama_1810{1,2}.log byte offsets immediately BEFORE starting the k=2 servers; this
# script logs the sizes again at launcher start (i.e. after the servers are up, before the first probe) so identity
# can be recomputed from the saved raw responses in the append-only server logs. This script does NOT start the
# servers (the reviewed digits S0.1 discipline): the operator starts them with `tmux new -d -s trks_llm $R/bin/trks-servers 2`.
set -euo pipefail
R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
S01=s01_t7_20261114
LOG=$R/logs/${S01}_launch.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
log "S0.1 start (node tabular_mlp, host TASL-7, k=2 probe period, pin 8237fd02)"
log "llama_18101.log size at start: $(wc -c < "$R/logs/llama_18101.log" 2>/dev/null || echo 0) bytes; llama_18102.log size at start: $(wc -c < "$R/logs/llama_18102.log" 2>/dev/null || echo 0) bytes"

for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  [ ! -e "$f" ] || { echo "REFUSE: priority marker $f" >&2; exit 2; }
done
[ ! -e "$OUT/$S01" ] || { echo "REFUSE: $OUT/$S01 already exists" >&2; exit 2; }
for s in trks_s01t_serial trks_s01t_conc; do
  ! tmux has-session -t "$s" 2>/dev/null || { echo "REFUSE: tmux session $s exists" >&2; exit 2; }
done
P=8237fd02b09ef2d28016a1c9f6acac3c35bb768b
[ "$(git -C "$R/work/Agent_paper_B" rev-parse HEAD)" = "$P" ] || { echo "REFUSE: paper is not at pin $P" >&2; exit 2; }
[ -z "$(git -C "$R/work/Agent_paper_B" status --porcelain --untracked-files=all)" ] || { echo "REFUSE: paper worktree dirty" >&2; exit 2; }
tmux has-session -t trks_llm 2>/dev/null || { echo "REFUSE: trks_llm (k=2 servers) not running; start: tmux new -d -s trks_llm $R/bin/trks-servers 2" >&2; exit 2; }
# verify exactly two llama-server processes on 18101/18102 (k = 2) before probing
NS=$(pgrep -f 'llama-server .*--port 1810[12]' | wc -l | tr -d ' ')
[ "$NS" = 2 ] || { echo "REFUSE: expected 2 llama-server processes (k=2 on 18101/18102), found $NS" >&2; exit 2; }

BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1"
S1="$BASE --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"
S2="$BASE --port 18102 -ngl 999 -c 8192 --parallel 1 --verbose"
T0=$(date +%s); DEADLINE=$((T0 + 900))
ready(){ curl -sf --max-time 5 "http://127.0.0.1:$1/v1/models" 2>/dev/null | grep -q r1-manager; }
while :; do
  if ready 18101 && ready 18102; then log "both endpoints ready"; break; fi
  [ "$(date +%s)" -lt "$DEADLINE" ] || { echo "ERROR: readiness timeout" >&2; tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3; }
  sleep 5
done
log "server pids: $(pgrep -f 'llama-server .*--port 1810[12]' | tr '\n' ',') ; lease: $(flock -n "$HOME/r1_locks/gpu0.lock" true && echo FREE || echo HELD)"

mkdir -p "$OUT/$S01" "$IN"
rc_of(){ sed -n 's/.*rc=//p' "$R/logs/$1.exit" 2>/dev/null | tail -1; }
wait_session(){ while tmux has-session -t "$1" 2>/dev/null; do sleep 15; done; }

trks-run trks_s01t_serial - probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 \
  --order-seed 1 --proposal-schema manager_proposal/v1 --node tabular_mlp --server-args "$S1" \
  --out "$OUT/$S01/serial.json"
wait_session trks_s01t_serial
log "serial rc=$(rc_of trks_s01t_serial)"
[ "$(rc_of trks_s01t_serial)" = 0 ] || { echo "serial probe failed" >&2; exit 1; }

trks-run trks_s01t_conc - probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent \
  --clients-per-url 2 --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 --node tabular_mlp \
  --server-args "$S1 | $S2" --out "$OUT/$S01/concurrent.json"
wait_session trks_s01t_conc
log "concurrent rc=$(rc_of trks_s01t_conc)"
[ "$(rc_of trks_s01t_conc)" = 0 ] || { echo "concurrent probe failed" >&2; exit 1; }
log "S01 DONE (results: $OUT/$S01/serial.json, $OUT/$S01/concurrent.json)"
