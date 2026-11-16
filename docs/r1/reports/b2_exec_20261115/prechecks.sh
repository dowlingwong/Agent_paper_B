#!/bin/bash
# B2 pre-marker read-only inventory (fail-closed). Writes only inside $RUN_DIR/prechecks/.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
PD="$RUN_DIR/prechecks"
OUT="$PD/prechecks.log"
OK="$PD/prechecks.ok"
EXPECT_GPU=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
stop() { printf 'STOP: %s\n' "$*" >> "$OUT"; echo "STOP: $*" >&2; exit 2; }
[ "$HOME" = /home/dowling ] || { echo "HOME mismatch" >&2; exit 1; }
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || { echo "missing RUN_DIR" >&2; exit 1; }
[ -d "$PD" ] && [ ! -L "$PD" ] || { echo "missing prechecks dir" >&2; exit 1; }
[ -e "$OUT" ] && { echo "prechecks.log exists" >&2; exit 1; }
set -C
exec 9> "$OUT" || exit 1
{ echo "=== B2 prechecks $(date -u +%FT%TZ) local $(date +%FT%T%z) ==="
  echo "host=$(hostname) uid=$(id -u) user=$(id -un) home=$HOME"
  echo "head=$HEAD run_id=$RUN_ID run_dir=$RUN_DIR"; } >&9
# --- pins / disk / GPU ---------------------------------------------------------------------
gpu=$(nvidia-smi --query-gpu=uuid,memory.total --format=csv,noheader | head -1)
echo "GPU: $gpu" >&9
case "$gpu" in *"$EXPECT_GPU"*) : ;; *) stop "GPU uuid mismatch (expected $EXPECT_GPU)";; esac
avail=$(df -B1 --output=avail /home/dowling | tail -1 | tr -d ' ')
echo "DISK_AVAIL_BYTES=$avail" >&9
[ "$avail" -ge 100000000000 ] || stop "disk below 100 GB floor"
# --- lease (this takes the cooperative lock transiently; not part of the read-only census) --
if flock -n /home/dowling/r1_locks/gpu0.lock true; then echo "LEASE-FREE" >&9; else stop "gpu0.lock BUSY (lease held)"; fi
# --- locks and markers ---------------------------------------------------------------------
ls -la /home/dowling/r1_locks >&9 2>&1
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && stop "trackx marker present"
echo "TRACKX_MARKER_ABSENT" >&9
shopt -s nullglob; set -- /home/dowling/r1_locks/*.active; shopt -u nullglob
[ "$#" -eq 0 ] || stop "another *.active marker present: $*"
echo "NO_OTHER_ACTIVE_MARKERS" >&9
echo "=== _to_delete (read-only listing) ===" >&9; ls -la /home/dowling/r1_locks/_to_delete >&9 2>&1 || true
# --- watcher identity ----------------------------------------------------------------------
command -v tmux >/dev/null 2>&1 || stop "tmux unavailable (cannot census watcher)"
pgrep -a -f "trks_watch|trks-watch" >&9 2>&1 || echo "NO_WATCHER" >&9
pgrep -f "trks_watch|trks-watch" >/dev/null 2>&1 || stop "watcher not running"
tmux list-panes -a -F 'session=#{session_name} pane=#{pane_id} pid=#{pane_pid} command=#{pane_current_command}' >&9 2>&1 || stop "tmux list-panes failed"
[ -f /home/dowling/r1_tracks/bin/trks-watch ] || stop "watcher script missing"
sha256sum /home/dowling/r1_tracks/bin/trks-watch >&9 2>&1
[ -r /home/dowling/r1_tracks/logs/watch.log ] || stop "watch.log missing/unreadable"
echo "WATCH_LOG_LINES_BEFORE=$(wc -l < /home/dowling/r1_tracks/logs/watch.log)" >&9
# --- collectors / servers / P.3a -----------------------------------------------------------
if pgrep -a -f "python -m r1\.tracks\.collect .*--stop-file" > "$PD/collectors.txt" 2>&1; then stop "Track S collectors running (cannot establish a safe stop within 1 h)"; fi
if pgrep -a -f "trks_llm" > "$PD/trks_llm.txt" 2>&1; then stop "trks_llm server running"; fi
if pgrep -a -f "P\.3a|p3a" > "$PD/p3a.txt" 2>&1; then stop "P.3a running (owner safe pause not established)"; fi
echo "NO_COLLECTORS NO_TRKS_LLM NO_P3A" >&9
# --- GPU compute apps, full process census, owners -----------------------------------------
if nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader | grep -q .; then nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader >&9; stop "GPU compute app present"; fi
echo "GPU_COMPUTE_APPS_NONE" >&9
ps -eo user,pid,ppid,stat,etime,comm > "$PD/ps-all.txt" 2>&1 || stop "ps failed"
# --- manifest inventory (traversal errors are STOP) ----------------------------------------
: > "$PD/find.err"
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PD/find.err" > "$PD/manifest_inventory_before.txt" || stop "manifest find failed"
[ -s "$PD/find.err" ] && stop "manifest find traversal error (see find.err)"
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PD/find.err" > "$PD/stop_inventory_before.txt" || stop "STOP find failed"
[ -s "$PD/find.err" ] && stop "STOP find traversal error"
while IFS= read -r m; do
  d=$(dirname "$m"); [ -e "$d/STOP" ] && echo "STOP_PRESENT $d/STOP" || echo "STOP_ABSENT $d/STOP"
done < <(awk '{print $8}' "$PD/manifest_inventory_before.txt") > "$PD/stop_absence_before.txt"
cat "$PD/manifest_inventory_before.txt" >&9; cat "$PD/stop_inventory_before.txt" >&9
# --- frozen venv / harness pins (pre-marker, read-only) ------------------------------------
[ -r "$RUN_DIR/venv_pins.txt" ] || stop "venv_pins.txt missing"
/home/dowling/exam-x/work/venv/bin/python - "$RUN_DIR" <<'PYV' >> "$PD/pins.log" 2>&1
import importlib.metadata as md, platform, sys
pins = {}
for line in open(sys.argv[1] + '/venv_pins.txt'):
    line = line.strip()
    if not line or line.startswith('#'): continue
    k, v = line.split('=', 1); pins[k] = v
assert platform.python_version() == pins['python'], 'python version'
assert sys.prefix == pins['prefix'], 'prefix'
for k in ('openai','langchain_openai','langchain_core','langgraph','pydantic','pydantic_core','httpx','pytest','numpy','scikit-learn'):
    got = md.version(k); assert got == pins[k], f'{k} {got} != {pins[k]}'
print('VENV_PINS_OK')
PYV
grep -q VENV_PINS_OK "$PD/pins.log" || stop "venv pins mismatch (see prechecks/pins.log)"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
[ "$(git -C "$HARNESS" rev-parse HEAD)" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 ] || stop "harness pin mismatch"
[ -z "$(git -C "$HARNESS" status --porcelain --untracked-files=all)" ] || stop "harness dirty (incl. untracked)"
echo "VENV_PINS_OK HARNESS_OK" >&9
# --- watcher identity compare (pane/bash pid + script sha; a restart is a STOP) ------------
[ -r "$RUN_DIR/watcher_expected.txt" ] || stop "watcher_expected.txt missing"
. "$RUN_DIR/watcher_expected.txt"
tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' > "$PD/tmux_panes.txt" 2>&1 || stop "tmux list-panes failed"
grep -Eq "^[^ ]+ ${WATCHER_PANE_PID} bash$" "$PD/tmux_panes.txt" || stop "watcher pane pid ${WATCHER_PANE_PID} not found in tmux panes"
wsha=$(sha256sum /home/dowling/r1_tracks/bin/trks-watch | awk '{print $1}')
[ "$wsha" = "$WATCHER_SCRIPT_SHA256" ] || stop "watcher script changed ($wsha)"
echo "WATCHER_IDENTITY_OK pane_pid=$WATCHER_PANE_PID sha=$wsha" >&9
echo "NOTE: tmux list-panes uses the tmux client socket (B1 boundary report caveat); census only." >&9
# --- predecessor _d retirement -------------------------------------------------------------
[ -s /home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d/marker-retirement_after_run.json ] || stop "predecessor _d retirement record missing"
cat /home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d/marker-retirement_after_run.json >&9 2>&1
# --- STATUS sources (historical record only) ----------------------------------------------
for repo in /home/dowling/exam-x/work/agent_paper_B /home/dowling/r1_trackp/Agent_paper_B /home/dowling/r1_tracks/work/Agent_paper_B; do
  p="$repo/docs/r1/STATUS.md"
  if [ -f "$p" ] && [ ! -L "$p" ] && [ -r "$p" ]; then echo "STATUS_SHA $p $(sha256sum "$p" | awk '{print $1}')"; else echo "STATUS_ABSENT_OR_UNREADABLE $p"; fi
done >&9 2>&1
echo "=== done $(date -u +%FT%TZ) ===" >&9
printf 'PRECHECKS_PASS\n' >> "$OUT"
set -C; printf 'PRECHECKS_PASS\n' > "$OK" || { echo "cannot write prechecks.ok exclusively" >&2; exit 1; }
echo "PRECHECKS_PASS $OUT"
