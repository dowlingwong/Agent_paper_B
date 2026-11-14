#!/usr/bin/env bash
# Track S Phase 4 — S0.5 pilot on TASL-7 (node digits_mlp), 13 Nov 2026.
# Authority: Track S operator runbook rev 3.3 Phase 4; reports/TRACKS_DIGITS_HOSTMOVE_20261112.md
# (host move, accepted; new dirs s05_t7_20261113); paper pin 8237fd02; prior a2u_prior_r2_20261111.json.
# k is the Phase-1 decision; the TASL-7 S0.1 result (13 Nov) decided k = 2. ENGINEERING_ONLY.
# Run as: ssh tasl7 bash $R/launch/tasl7_digits_s05_20261113.sh
# Resumes the same directory only when it already contains a manifest; never touches the preserved
# TASL-2 $OUT/digits_mlp/s05 scene (different host; this script never contacts TASL-2).
set -euo pipefail
R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; WORK=$R/scratch/digits_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
# K is the Phase-1 decision: the TASL-7 S0.1 result (13 Nov) decided k = 2 (both URLs 100% and cross 100%).
K=${K:-2}
RUN=$OUT/s05_t7_20261113; WRUN=$WORK/s05_t7_20261113; SESSION=trks_s05_t7
LOG=$R/logs/s05_t7_20261113_launch.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  [ ! -e "$f" ] || { echo "REFUSE: priority marker $f" >&2; exit 2; }
done
tmux has-session -t "$SESSION" 2>/dev/null && { echo "REFUSE: $SESSION session already exists" >&2; exit 2; }
if [ -e "$RUN" ] && [ ! -e "$RUN/manifest.json" ]; then
  echo "REFUSE: $RUN exists without a manifest (not a resumable run)" >&2; exit 2
fi
if [ -e "$RUN" ] && [ -d "$RUN" ] && [ ! -s "$RUN/manifest.json" ]; then
  echo "REFUSE: $RUN/manifest.json is empty" >&2; exit 2
fi
P=8237fd02b09ef2d28016a1c9f6acac3c35bb768b
[ "$(git -C "$R/work/Agent_paper_B" rev-parse HEAD)" = "$P" ] || { echo "REFUSE: paper is not at pin $P" >&2; exit 2; }
[ -z "$(git -C "$R/work/Agent_paper_B" status --porcelain --untracked-files=all)" ] || { echo "REFUSE: paper worktree dirty" >&2; exit 2; }
PRIOR=$OUT/a2u_prior_r2_20261111.json
[ -f "$PRIOR" ] || { echo "REFUSE: prior file $PRIOR missing (copy it from the Mac with sha256 5c849d15…)" >&2; exit 2; }
[ "$(sha256sum "$PRIOR" | cut -d' ' -f1)" = "5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607" ] || { echo "REFUSE: prior sha256 mismatch" >&2; exit 2; }

LIVE=$( (pgrep -u dowling -f 'llama-server .*--port 1810[12]' || true) | wc -l | tr -d ' ' )
if tmux has-session -t trks_llm 2>/dev/null; then
  [ "$LIVE" -eq "$K" ] || { echo "REFUSE: trks_llm has $LIVE servers but K=$K" >&2; exit 2; }
else
  if nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | grep -q .; then
    echo "REFUSE: a GPU compute process is present and no trks_llm session of ours is running" >&2
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv >&2; exit 2
  fi
  flock -n "$HOME/r1_locks/gpu0.lock" true || { echo "REFUSE: gpu0.lock is held" >&2; exit 2; }
fi

mkdir -p "$RUN" "$WRUN" "$IN"
log "Phase 4 S0.5 start (node digits_mlp, host TASL-7, k=$K, pin 8237fd02, out $RUN)"

if tmux has-session -t trks_llm 2>/dev/null; then
  log "tmux trks_llm already running (resume path); not starting a second server"
else
  log "starting fresh servers k=$K in tmux session trks_llm"
  tmux new -d -s trks_llm "$R/bin/trks-servers $K"
  sleep 2
  if ! tmux has-session -t trks_llm 2>/dev/null; then
    log "ERROR: trks_llm exited immediately (lease held or marker) — see server log"
    tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
  fi
fi

T0=$(date +%s); READY=0; DEADLINE=$((T0 + 900))
while :; do
  NOW=$(date +%s); ok=1
  for p in $(seq 18101 $((18100 + K))); do
    curl -sf --max-time 5 "http://127.0.0.1:$p/v1/models" 2>/dev/null | grep -q r1-manager || ok=0
  done
  if [ "$ok" -eq 1 ]; then READY=1; log "endpoints 18101..1810$K ready after $((NOW - T0))s"; break; fi
  if [ "$NOW" -ge "$DEADLINE" ]; then
    log "ERROR: readiness timeout after 900s"; tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
  fi
  sleep 5
done
log "server pid: $(pgrep -f 'llama-server .*--port 18101' | tr '\n' ',')"
log "GPU compute apps: $(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | tr '\n' ';')"
log "lease: $(flock -n "$HOME/r1_locks/gpu0.lock" true && echo FREE || echo HELD)"

log "starting S0.5 collector in tmux session $SESSION"
trks-run "$SESSION" 18101 collect --phase S0.5 --node digits_mlp --prior "$PRIOR" --prior-sha256 5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607 --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file "$RUN/STOP" --out "$RUN" --work "$WRUN"
log "S0.5 collector started; monitor logs/trks_s05_t7.log / .exit and trks-status"
