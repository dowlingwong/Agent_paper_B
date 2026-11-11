#!/usr/bin/env bash
# Track S Phase 3 — S0.4 rerun at the A2-U pin on TASL-2 (node digits_mlp), 11 Nov 2026.
#
# Authority: operator runbook O3; Track S operator runbook rev 3.3 (docs commit 13badb0,
# sha256 a93fb84b…) Phase 3; STOP-3 ruling §11 (author decision (a)) and PLAN §10
# R1-TRACKS-A2U-STALE: rerun at paper pin 8237fd02 in new --out/--work dirs.
# k = 1 for digits_mlp (STOP-1 clause (b)); single server on port 18101.
# ENGINEERING_ONLY.
#
# Run as: ssh portal_zhixu bash $R/launch/tasl2_s04r2_20261111.sh
# Starts the k=1 server in tmux trks_llm if it is not already running, waits (bounded) for
# 127.0.0.1:18101/v1/models to answer, then launches the S0.4 collector as its own tmux session
# (trks_s04r2) via trks-run. Re-running the same script after a deadline/stop resumes this rerun
# (the collector resumes from committed roots); delete the new phase STOP file first per runbook §0.4.
# The old $OUT/s04 and $WORK/s04 STOP scene is never read or written by this script; the new session
# keeps $R/logs/trks_s04.* (old STOP evidence) from being appended to.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; WORK=$R/scratch/digits_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
LOG=$R/logs/s04_r2_20261111_launch.log
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

# --- guards: no priority marker, no foreign GPU job, no duplicate collector ---
for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  if [ -e "$f" ]; then echo "REFUSE: priority marker $f" >&2; exit 2; fi
done
if tmux has-session -t trks_s04r2 2>/dev/null; then
  echo "REFUSE: trks_s04r2 session already exists" >&2; exit 2
fi
# Refuse an existing new output dir unless it is a resumable run of that dir (manifest present).
if [ -e "$OUT/s04_r2_20261111" ] && [ ! -e "$OUT/s04_r2_20261111/manifest.json" ]; then
  echo "REFUSE: $OUT/s04_r2_20261111 exists without a manifest (not a resumable run)" >&2; exit 2
fi
if [ -e "$WORK/s04_r2_20261111" ] && [ ! -e "$OUT/s04_r2_20261111/manifest.json" ]; then
  echo "REFUSE: $WORK/s04_r2_20261111 exists without a resumable manifest" >&2; exit 2
fi
if ! tmux has-session -t trks_llm 2>/dev/null; then
  if nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | grep -q .; then
    echo "REFUSE: a GPU compute process is present and no trks_llm session of ours is running" >&2
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv >&2; exit 2
  fi
  if ! flock -n "$HOME/r1_locks/gpu0.lock" true; then echo "REFUSE: gpu0.lock is held" >&2; exit 2; fi
fi

mkdir -p "$OUT/s04_r2_20261111" "$WORK/s04_r2_20261111" "$IN"
log "Phase 3 S0.4 rerun start (node digits_mlp, host TASL-2, k=1, pin 8237fd02, out $OUT/s04_r2_20261111)"

# --- fresh k=1 server (port 18101) if not already up ---
if tmux has-session -t trks_llm 2>/dev/null; then
  log "tmux trks_llm already running (resume path); not starting a second server"
else
  log "starting fresh server k=1 in tmux session trks_llm"
  tmux new -d -s trks_llm "$R/bin/trks-servers 1"
  sleep 2
  if ! tmux has-session -t trks_llm 2>/dev/null; then
    log "ERROR: trks_llm exited immediately (lease held or marker) — see server log"
    tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
  fi
fi

# --- bounded readiness poll on the single endpoint (before any collector) ---
T0=$(date +%s); READY=0; DEADLINE=$((T0 + 900))
while :; do
  NOW=$(date +%s)
  if curl -sf --max-time 5 http://127.0.0.1:18101/v1/models 2>/dev/null | grep -q r1-manager; then
    READY=1; log "18101/v1/models ready after $((NOW - T0))s"; break
  fi
  if [ "$NOW" -ge "$DEADLINE" ]; then
    log "ERROR: readiness timeout after 900s"; tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
  fi
  sleep 5
done
log "server pid: $(pgrep -f 'llama-server .*--port 18101' | tr '\n' ',')"
log "GPU compute apps: $(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | tr '\n' ';')"
log "lease: $(flock -n "$HOME/r1_locks/gpu0.lock" true && echo FREE || echo HELD)"

# --- S0.4 collector (rev-3.3 Phase 3 command; own tmux session via trks-run) ---
log "starting S0.4 rerun collector in tmux session trks_s04r2"
trks-run trks_s04r2 18101 collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/s04_r2_20261111/STOP --out $OUT/s04_r2_20261111 --work $WORK/s04_r2_20261111
log "S0.4 rerun collector started; monitor logs/trks_s04r2.log / .exit and trks-status"
