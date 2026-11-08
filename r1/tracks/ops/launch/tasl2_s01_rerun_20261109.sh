#!/usr/bin/env bash
# Track S — S0.1 determinism re-run on TASL-2 (node digits_mlp), 9 Nov 2026.
#
# Authority: operator runbook O3 (OPERATOR_RUNBOOK_20261104.md, branch docs/runbooks-09nov),
#   PLAN §10 row R1-TRACKS-S01-RERUN, Track S operator runbook rev 3.3 (docs commit 13badb0,
#   sha256 a93fb84b…) Phase 1, and the author's scope of 9 Nov ("S0.1 重跑允许用新会话名，只追加
#   watcher 和 server 日志，在 TASL-2 上按 O3 执行").
#
# This is the 31 Oct re-run procedure (fresh servers; k = 2; serial then concurrent; cache_prompt
# false, carried by the pinned harness at a3fedbb / paper d10b05b7), with the race that invalidated
# the 31 Oct attempt fixed: the serial probe starts only after BOTH /v1 endpoints answer.
#
# New output directory and new probe session names, so no Oct-30/31 evidence is overwritten.
# ENGINEERING_ONLY. k is set only by the Phase 1 "Done when" rule as amended by clause (b).
#
# Run as:  ssh portal_zhixu bash $R/launch/tasl2_s01_rerun_20261109.sh
# Servers are started and left running for the operator to stop after inspection; the watcher
# can stop them (name trks_llm) if a priority marker appears.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; WORK=$R/scratch/digits_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH

S01_SUFFIX=${S01_SUFFIX:-_rerun20261109}
D="$OUT/s01$S01_SUFFIX"
LOG=$R/logs/s01_rerun_20261109_launch.log
BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1"
S1="$BASE --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"
S2="$BASE --port 18102 -ngl 999 -c 8192 --parallel 1 --verbose"
NSERIAL=trks_s01_serial_r2
NCONC=trks_s01_conc_r2

log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }
rc_of() { sed -n 's/.*rc=//p' "$R/logs/$1.exit" 2>/dev/null | tail -1; }
wait_session() { while tmux has-session -t "$1" 2>/dev/null; do sleep 15; done; }

# --- guards: never overwrite, never reuse a session, never start over a priority marker or GPU job ---
mkdir -p "$D" "$IN"
if [ -e "$D/serial.json" ] || [ -e "$D/concurrent.json" ]; then
  echo "REFUSE: $D/serial.json or concurrent.json already exists" >&2; exit 2
fi
for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  if [ -e "$f" ]; then echo "REFUSE: priority marker $f" >&2; exit 2; fi
done
for s in trks_llm "$NSERIAL" "$NCONC"; do
  if tmux has-session -t "$s" 2>/dev/null; then echo "REFUSE: tmux session $s already exists" >&2; exit 2; fi
done
if nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | grep -q .; then
  echo "REFUSE: a GPU compute process is present" >&2
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv >&2; exit 2
fi
if ! flock -n "$HOME/r1_locks/gpu0.lock" true; then echo "REFUSE: gpu0.lock is held" >&2; exit 2; fi

log "S0.1 re-run start (node digits_mlp, host TASL-2, out $D)"
# offsets so the post-run capture can extract exactly this run's server-log segment (logs are append-only)
OFF1=$(wc -c < "$R/logs/llama_18101.log" 2>/dev/null || echo 0)
OFF2=$(wc -c < "$R/logs/llama_18102.log" 2>/dev/null || echo 0)
log "llama_18101.log offset before start: $OFF1 bytes; llama_18102.log offset before start: $OFF2 bytes"

# --- fresh servers, k = 2 (trks-servers takes the lease and checks the markers itself) ---
log "starting fresh servers k=2 in tmux session trks_llm"
tmux new -d -s trks_llm "$R/bin/trks-servers 2"
sleep 2
if ! tmux has-session -t trks_llm 2>/dev/null; then
  log "ERROR: trks_llm exited immediately (lease held or marker) — see server logs"
  tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
fi

# --- bounded readiness poll on BOTH endpoints (fixes the 31 Oct race: 600/1177 transport errors) ---
T0=$(date +%s); READY1=0; READY2=0; DEADLINE=$((T0 + 900))
while :; do
  NOW=$(date +%s)
  if [ "$READY1" = 0 ] && curl -sf --max-time 5 http://127.0.0.1:18101/v1/models 2>/dev/null | grep -q r1-manager; then
    READY1=1; log "18101/v1/models ready after $((NOW - T0))s"
  fi
  if [ "$READY2" = 0 ] && curl -sf --max-time 5 http://127.0.0.1:18102/v1/models 2>/dev/null | grep -q r1-manager; then
    READY2=1; log "18102/v1/models ready after $((NOW - T0))s"
  fi
  if [ "$READY1" = 1 ] && [ "$READY2" = 1 ]; then break; fi
  if [ "$NOW" -ge "$DEADLINE" ]; then
    log "ERROR: readiness timeout after 900s (18101 ready=$READY1, 18102 ready=$READY2)"
    tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true
    tail -n 20 "$R/logs/llama_18102.log" 2>/dev/null || true
    exit 3
  fi
  sleep 5
done
log "both endpoints ready; total readiness wait $(( $(date +%s) - T0 ))s"
# positive exclusion of the 31 Oct "serial raced server start" class: record the server pids and
# the lease state now, before either probe starts.
log "tmux sessions: $(tmux ls 2>/dev/null | tr '\n' ';')"
log "GPU compute apps: $(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | tr '\n' ';')"
for p in 18101 18102; do
  log "port $p llama-server pid: $(pgrep -f "llama-server .*--port $p" | tr '\n' ',')"
done
log "lease: $(flock -n "$HOME/r1_locks/gpu0.lock" true && echo FREE || echo HELD)"
log "llama_18101.log new segment (load/listen lines): $(tail -c +$((OFF1 + 1)) "$R/logs/llama_18101.log" 2>/dev/null | grep -a -E 'offloaded|server is listening|starting the main loop|model loaded' | tail -n 4 | tr '\n' ';')"
log "llama_18102.log new segment (load/listen lines): $(tail -c +$((OFF2 + 1)) "$R/logs/llama_18102.log" 2>/dev/null | grep -a -E 'offloaded|server is listening|starting the main loop|model loaded' | tail -n 4 | tr '\n' ';')"

# --- serial probe (new session name; exact rev-3.3 Phase 1 arguments) ---
log "starting serial probe in tmux session $NSERIAL"
trks-run "$NSERIAL" - probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 \
  --order-seed 1 --proposal-schema manager_proposal/v1 --node digits_mlp --server-args "$S1" \
  --out "$D/serial.json"
wait_session "$NSERIAL"
RCS=$(rc_of "$NSERIAL"); log "serial rc=$RCS"
[ "$RCS" = 0 ] || { log "ERROR: serial probe rc=$RCS — STOP, evidence preserved"; exit 4; }
python3 - "$D/serial.json" serial <<'PY' >> "$LOG" 2>&1 || { log "ERROR: serial probe check FAILED"; exit 5; }
import json, sys
f, mode = sys.argv[1], sys.argv[2]
d = json.load(open(f)); pu = d["per_url"]; tot = sum(v["errors"] for v in pu.values())
print(f"serial.json: mode={d['mode']} n={d['n_prompts']} repeats={d['repeats']} clients_per_url={d['clients_per_url']} order_seed={d['order']['seed']}")
print(f"  cache_prompt={d.get('cache_prompt')!r} request_example.cache_prompt={d.get('request_example',{}).get('cache_prompt')!r}")
print(f"  per_url errors={ {u: v['errors'] for u, v in pu.items()} } total_errors={tot}")
print(f"  per_url identity_rate={ {u: v['identity_rate'] for u, v in pu.items()} }")
for u, v in pu.items():
    print(f"  {u}: identity_rate_per_client={v['identity_rate_per_client']} latency={v['latency']}")
print(f"  cpu_before={d['cpu_before']} cpu_after={d['cpu_after']}")
sys.exit(0 if (tot == 0 and d.get("cache_prompt") is False) else 1)
PY

# --- concurrent probe (new session name; exact rev-3.3 Phase 1 arguments) ---
log "starting concurrent probe in tmux session $NCONC"
trks-run "$NCONC" - probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent \
  --clients-per-url 2 --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 --node digits_mlp \
  --server-args "$S1 | $S2" --out "$D/concurrent.json"
wait_session "$NCONC"
RCC=$(rc_of "$NCONC"); log "concurrent rc=$RCC"
[ "$RCC" = 0 ] || { log "ERROR: concurrent probe rc=$RCC — STOP, evidence preserved"; exit 4; }
python3 - "$D/concurrent.json" concurrent <<'PY' >> "$LOG" 2>&1 || { log "ERROR: concurrent probe check FAILED"; exit 5; }
import json, sys
f, mode = sys.argv[1], sys.argv[2]
d = json.load(open(f)); pu = d["per_url"]; tot = sum(v["errors"] for v in pu.values())
print(f"concurrent.json: mode={d['mode']} n={d['n_prompts']} repeats={d['repeats']} clients_per_url={d['clients_per_url']} order_seed={d['order']['seed']}")
print(f"  cache_prompt={d.get('cache_prompt')!r} request_example.cache_prompt={d.get('request_example',{}).get('cache_prompt')!r}")
print(f"  per_url errors={ {u: v['errors'] for u, v in pu.items()} } total_errors={tot}")
print(f"  per_url identity_rate={ {u: v['identity_rate'] for u, v in pu.items()} }")
print(f"  cross_server_identity={d.get('cross_server_identity')!r}")
for u, v in pu.items():
    print(f"  {u}: identity_rate_per_client={v['identity_rate_per_client']} cross_client_identity={v['cross_client_identity']} latency={v['latency']}")
print(f"  cpu_before={d['cpu_before']} cpu_after={d['cpu_after']}")
sys.exit(0 if (tot == 0 and d.get("cache_prompt") is False) else 1)
PY

log "S01 RERUN DONE — servers LEFT RUNNING in trks_llm for post-run inspection/stop"
