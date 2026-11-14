#!/usr/bin/env bash
# Track S Phase 3 — S0.4 dev campaigns for tabular_mlp on TASL-7 (host move), 14 Nov 2026.
#
# Authority: operator runbook O3; Track S operator runbook rev 3.3 (docs commit 13badb0,
# sha256 a93fb84b…) Phase 3; the author's STOP-1 decision (a) reading and the STOP-3 ruling §11
# (author decision (a)) / PLAN §10 R1-TRACKS-A2U-STALE: run at paper pin 8237fd02 in new --out/--work dirs.
# tabular_mlp has no new-pin S0.1 (the only tabular S0.1, Oct 30 on the old pin, failed its identity tiers),
# so k was never set for tabular; per the Lead's instruction and the author's STOP-1 decision (a) reading,
# this unit runs k = 1 (single server, port 18101) and flags the open author-decision item in the report.
# ENGINEERING_ONLY.
#
# Run as: ssh tasl7 bash $R/launch/tasl7_tabular_s04_20261114.sh
# Starts the k=1 server in tmux trks_llm if it is not already running, waits (bounded) for
# 127.0.0.1:18101/v1/models to answer, then launches the S0.4 collector as its own tmux session
# (trks_s04_t7) via trks-run. Re-running the same script after a deadline/stop resumes this run (the
# collector resumes from committed roots); delete the new phase STOP file first per runbook §0.4.
# The old tabular scenes (s01, s01_diag*, s01_rerun_INVALID…, s11, smoke) are never read or written.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
NEW=$OUT/s04_t7_20261114; NEWW=$WORK/s04_t7_20261114; SESSION=trks_s04_t7
LOG=$R/logs/s04_t7_tabular_20261114_launch.log
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

# --- guards: no priority marker, no foreign GPU job, no duplicate collector ---
for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  if [ -e "$f" ]; then echo "REFUSE: priority marker $f" >&2; exit 2; fi
done
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "REFUSE: $SESSION session already exists" >&2; exit 2
fi
# Refuse an existing new output dir unless it is a resumable run of that dir (manifest present).
if [ -e "$NEW" ] && [ ! -e "$NEW/manifest.json" ]; then
  echo "REFUSE: $NEW exists without a manifest (not a resumable run)" >&2; exit 2
fi
if [ -e "$NEWW" ] && [ ! -e "$NEW/manifest.json" ]; then
  echo "REFUSE: $NEWW exists without a resumable manifest" >&2; exit 2
fi
if ! tmux has-session -t trks_llm 2>/dev/null; then
  if nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | grep -q .; then
    echo "REFUSE: a GPU compute process is present and no trks_llm session of ours is running" >&2
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv >&2; exit 2
  fi
  if ! flock -n "$HOME/r1_locks/gpu0.lock" true; then echo "REFUSE: gpu0.lock is held" >&2; exit 2; fi
fi

mkdir -p "$NEW" "$NEWW" "$IN"
log "Phase 3 S0.4 start (node tabular_mlp, host TASL-7, k=1, pin 8237fd02, out $NEW)"

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
log "starting S0.4 collector in tmux session $SESSION"
trks-run "$SESSION" 18101 collect --phase S0.4 --node tabular_mlp --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file "$NEW/STOP" --out "$NEW" --work "$NEWW"
log "S0.4 collector started; monitor logs/$SESSION.log / .exit and trks-status"
