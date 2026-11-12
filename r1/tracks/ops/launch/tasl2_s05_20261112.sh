#!/usr/bin/env bash
# Track S Phase 4 — S0.5 pilot on TASL-2 (node digits_mlp), 12 Nov 2026.
#
# Authority: operator runbook O3; Track S operator runbook rev 3.3 (docs commit 13badb0,
# sha256 a93fb84b…) Phase 4; the author's line L1 (runbook §4) present in the start message;
# paper pin 8237fd02; prior a2u_prior_r2_20261111.json.
# k = 1 for digits_mlp (STOP-1 clause (b)); single server on port 18101.
# ENGINEERING_ONLY.
#
# Run as: ssh portal_zhixu bash $R/launch/tasl2_s05_20261112.sh
# Starts the k=1 server in tmux trks_llm if it is not already running, waits (bounded) for
# 127.0.0.1:18101/v1/models to answer, then launches the S0.4 collector as its own tmux session
# (trks_s05) via trks-run. A deadline-stopped session is resumed with the identical command (runbook
# ruling); the S0.5 guard refuses an existing $OUT/s05 unless it is a resume of that directory.
# The old $OUT/s04 / $WORK/s04 STOP scene and the s04_r2_20261111 rerun are never read or written.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; WORK=$R/scratch/digits_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
LOG=$R/logs/s05_20261112_launch.log
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

# --- guards: no priority marker, no foreign GPU job, no duplicate collector ---
for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  if [ -e "$f" ]; then echo "REFUSE: priority marker $f" >&2; exit 2; fi
done
if tmux has-session -t trks_s05 2>/dev/null; then
  echo "REFUSE: trks_s05 session already exists" >&2; exit 2
fi
# Refuse an existing S0.5 output dir unless it is a resumable run of that dir (manifest present).
if [ -e "$OUT/s05" ] && [ ! -e "$OUT/s05/manifest.json" ]; then
  echo "REFUSE: $OUT/s05 exists without a manifest (not a resumable run)" >&2; exit 2
fi
if ! tmux has-session -t trks_llm 2>/dev/null; then
  if nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | grep -q .; then
    echo "REFUSE: a GPU compute process is present and no trks_llm session of ours is running" >&2
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv >&2; exit 2
  fi
  if ! flock -n "$HOME/r1_locks/gpu0.lock" true; then echo "REFUSE: gpu0.lock is held" >&2; exit 2; fi
fi

mkdir -p "$OUT/s05" "$WORK/s05" "$IN"
log "Phase 4 S0.5 start (node digits_mlp, host TASL-2, k=1, pin 8237fd02, out $OUT/s05)"

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
log "starting S0.5 collector in tmux session trks_s05"
trks-run trks_s05 18101 collect --phase S0.5 --node digits_mlp --prior $OUT/a2u_prior_r2_20261111.json --prior-sha256 5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607 --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/s05/STOP --out $OUT/s05 --work $WORK/s05
log "S0.5 collector started; monitor logs/trks_s05.log / .exit and trks-status"
