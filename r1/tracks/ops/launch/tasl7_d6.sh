#!/usr/bin/env bash
# D6 follow-up on TASL-7 (tabular_mlp). ENGINEERING_ONLY / DIAGNOSTIC. Never a phase; sets no k.
#   f1 = cold control : cache_prompt=true, one freshly started server, ZERO prior completions on it.
#   f2 = plain S0.1   : NO cache_prompt field, one freshly started server.
# Each invocation starts its own server and stops it, so F1 and F2 cannot share a warm server.
# Freshness is proved by process age (the server's /proc start time must be >= this script's start), NOT
# by parsing the server log: this llama.cpp build has request logging disabled, so request paths never
# appear there. The server is started through bin/trks-servers, which holds flock ~/r1_locks/gpu0.lock
# for the servers' lifetime; this script ASSERTS the lock is held and never takes it (that would
# deadlock). The serving process is identified by the listener on port 18101 and tied to the single
# nvidia-smi compute pid -- never by a cmdline pattern (Track P's Python-wrapped servers and the
# trks-servers bash wrapper both contain "llama-server").
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; PORT=18101; PATH=$R/bin:$PATH
[ "$(hostname)" = "TASL-7" ] || { echo "STOP: this is $(hostname), not TASL-7" >&2; exit 1; }
phase=${1:?usage: tasl7_d6.sh f1|f2}
case "$phase" in f1|f2) ;; *) echo "phase must be f1 or f2" >&2; exit 2 ;; esac
LOG=$R/logs/llama_$PORT.log
case "$phase" in
  f1) out=$OUT/s01_diag_f1/cache_prompt_true_cold.json; mode=true ;;
  f2) out=$OUT/s01_diag_f2/plain_single_absent.json; mode=absent ;;
esac

# ---- preconditions: nothing is started yet, so nothing may be killed yet --------------------------
for m in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  [ -e "$m" ] && { echo "STOP: priority/drill marker present: $m" >&2; exit 1; }
done
tmux has-session -t trks_llm 2>/dev/null && { echo "STOP: a trks_llm session already exists (not ours to kill)" >&2; exit 1; }
l0=$(ss -H -ltn "sport = :$PORT" | grep -c . || true)
[ "$l0" = 0 ] || { echo "STOP: something already listens on $PORT (not ours to kill)" >&2; exit 1; }
n0=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -c . || true)
[ "$n0" = 0 ] || { echo "STOP: $n0 GPU compute process(es) present before start (not ours to kill)" >&2; exit 1; }
[ -e "$out" ] && { echo "STOP: would overwrite existing evidence $out" >&2; exit 1; }
mkdir -p "$(dirname "$out")"

if [ -s "$LOG" ]; then mv "$LOG" "$R/logs/llama_$PORT.$(date -u +%Y%m%dT%H%M%SZ).prev.log"; fi

# ---- start OUR server; only now may we clean up ----------------------------------------------------
script_start_epoch=$(date +%s)
tmux new -d -s trks_llm "$R/bin/trks-servers 1"
pid=""
cleanup() { tmux kill-session -t trks_llm 2>/dev/null || true; [ -n "${pid:-}" ] && kill "$pid" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 240); do grep -q "listening on http://127.0.0.1:$PORT" "$LOG" 2>/dev/null && break; sleep 1; done
grep -q "listening on http://127.0.0.1:$PORT" "$LOG" || { echo "STOP: server did not listen on $PORT" >&2; exit 1; }
grep -q "offloaded 29/29 layers" "$LOG" || { echo "STOP: no full GPU offload in $LOG" >&2; exit 1; }

# ---- the lease must be HELD (assert, never take) ---------------------------------------------------
flock -n "$HOME/r1_locks/gpu0.lock" true && { echo "STOP: lease is FREE; trks-servers is not holding it" >&2; exit 1; }

# ---- exactly one listener on our port --------------------------------------------------------------
l1=$(ss -H -ltn "sport = :$PORT" | grep -c . || true)
[ "$l1" = 1 ] || { echo "STOP: expected exactly 1 listener on $PORT, found $l1" >&2; exit 1; }
pid=$(ss -H -ltnp "sport = :$PORT" | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2 || true)
[ -n "${pid:-}" ] || { echo "STOP: could not read the listener pid on $PORT" >&2; exit 1; }
exe=$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)
case "$exe" in */llama-server) ;; *) echo "STOP: listener $pid exe is '${exe:-unreadable}', not llama-server" >&2; exit 1 ;; esac
gpc=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | tr -d ' ' | grep -c . || true)
[ "$gpc" = 1 ] || { echo "STOP: expected 1 GPU compute process, found $gpc" >&2; exit 1; }
gp=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | tr -d ' ' | head -1)
[ "$gp" = "$pid" ] || { echo "STOP: listener $pid is not the GPU compute pid $gp" >&2; exit 1; }
cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline" | sed 's/ *$//')
case "$cmd" in *"--port $PORT"*) ;; *) echo "STOP: listener cmdline lacks --port $PORT" >&2; exit 1 ;; esac

# ---- freshness: the server process must be newer than this invocation ------------------------------
server_start_epoch=$(stat -c %Y "/proc/$pid" 2>/dev/null || true)
[ -n "$server_start_epoch" ] || { echo "STOP: cannot read the server start time" >&2; exit 1; }
[ "$server_start_epoch" -ge "$script_start_epoch" ] || { echo "STOP: server (start $server_start_epoch) is older than this invocation ($script_start_epoch)" >&2; exit 1; }
echo "server_pid=$pid exe=$exe lstart=$(ps -o lstart= -p "$pid" | sed 's/^ *//') server_start_epoch=$server_start_epoch script_start_epoch=$script_start_epoch"

# ---- run the diagnostic ---------------------------------------------------------------------------
trks-diag --url "http://127.0.0.1:$PORT/v1" --node tabular_mlp --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --mode "$mode" --resident-server-count 1 --host-label TASL-7 \
  --server-pid "$pid" --script-start-epoch "$script_start_epoch" --phase-label "$phase" \
  --gguf "$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --llama-build 620d2225cc436ab0b001e3200e590e3b286ef9ab \
  --llama-server-bin "$R/opt/llama.cpp/build/bin/llama-server" \
  --server-args "$cmd" --out "$out"

[ -s "$out" ] || { echo "STOP: the diagnostic wrote no output" >&2; exit 1; }
grep -q '"calls_made": 600' "$out" || { echo "STOP: the output does not show 600 calls" >&2; exit 1; }

# ---- stop OUR server and verify the lease is released ---------------------------------------------
cleanup; trap - EXIT
for _ in $(seq 1 60); do ss -H -ltn "sport = :$PORT" | grep -q . || break; sleep 1; done
if ss -H -ltn "sport = :$PORT" | grep -q .; then echo "STOP: port $PORT still listening after stop" >&2; exit 1; fi
flock -n "$HOME/r1_locks/gpu0.lock" true || { echo "STOP: lease still held after stop" >&2; exit 1; }
echo "D6 $phase DONE"
