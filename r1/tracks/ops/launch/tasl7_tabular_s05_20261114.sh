#!/usr/bin/env bash
# Track S Phase 4 — S0.5 pilot for tabular_mlp on TASL-7, 14 Nov 2026.
# Authority: Track S operator runbook rev 3.3 Phase 4; the author's 14 Nov amendment (relayed by the Lead:
# S0.5/S0.5b for tabular as for digits, k from the S0.1 measurement); the accepted STOP-3 tabular S0.4 record
# (docs/r1/reviews/TRACKS_S04_T7_TABULAR_REVIEW_20261114.md, sha fbf0a874…); the tabular S0.1 re-run decided
# k = 2 (within-server identity 100% on both URLs and cross_server_identity 100%).
# Prior: the S0.4 A2-U prior $OUT/tabular_mlp/s04_t7_20261114/a2u_prior.json (sha256 ba8f7783…), NOT the s01 dir.
# ENGINEERING_ONLY.
# Run as: ssh tasl7 bash $R/launch/tasl7_tabular_s05_20261114.sh
# Session name is trks_s05t_t7, deliberately distinct from trks_s05_t7: the latter are the DIGITS TASL-7 S0.5's
# log/.cmd/.exit files and trks-run would overwrite/append them.
set -euo pipefail
R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
K=2
RUN=$OUT/s05_t7_20261114; WRUN=$WORK/s05_t7_20261114; SESSION=trks_s05t_t7
PRIOR=$OUT/s04_t7_20261114/a2u_prior.json
PRIOR_SHA=ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f
LOG=$R/logs/s05_t7_tabular_20261114_launch.log
log(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$LOG"; }

for f in "$HOME/r1_locks/trackx_evidence.active" "$HOME/r1_locks/trackp_evidence.active" "$R/trks_drill.active"; do
  [ ! -e "$f" ] || { echo "REFUSE: priority marker $f" >&2; exit 2; }
done
tmux has-session -t "$SESSION" 2>/dev/null && { echo "REFUSE: $SESSION session already exists" >&2; exit 2; }
if [ -e "$RUN" ] && [ ! -e "$RUN/manifest.json" ]; then
  echo "REFUSE: $RUN exists without a manifest (not a resumable run)" >&2; exit 2
fi
P=8237fd02b09ef2d28016a1c9f6acac3c35bb768b
[ "$(git -C "$R/work/Agent_paper_B" rev-parse HEAD)" = "$P" ] || { echo "REFUSE: paper is not at pin $P" >&2; exit 2; }
[ -z "$(git -C "$R/work/Agent_paper_B" status --porcelain --untracked-files=all)" ] || { echo "REFUSE: paper worktree dirty" >&2; exit 2; }
[ -f "$PRIOR" ] || { echo "REFUSE: prior file $PRIOR missing" >&2; exit 2; }
[ "$(sha256sum "$PRIOR" | cut -d' ' -f1)" = "$PRIOR_SHA" ] || { echo "REFUSE: prior sha256 mismatch (want $PRIOR_SHA)" >&2; exit 2; }

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
log "Phase 4 S0.5 start (node tabular_mlp, host TASL-7, k=$K, pin 8237fd02, out $RUN)"

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

T0=$(date +%s); DEADLINE=$((T0 + 900))
while :; do
  NOW=$(date +%s); ok=1
  for p in $(seq 18101 $((18100 + K))); do
    curl -sf --max-time 5 "http://127.0.0.1:$p/v1/models" 2>/dev/null | grep -q r1-manager || ok=0
  done
  if [ "$ok" -eq 1 ]; then log "endpoints 18101..1810$K ready after $((NOW - T0))s"; break; fi
  if [ "$NOW" -ge "$DEADLINE" ]; then
    log "ERROR: readiness timeout after 900s"; tail -n 20 "$R/logs/llama_18101.log" 2>/dev/null || true; exit 3
  fi
  sleep 5
done
log "server pid: $(pgrep -f 'llama-server .*--port 1810[12]' | tr '\n' ',')"
log "GPU compute apps: $(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | tr '\n' ';')"
log "lease: $(flock -n "$HOME/r1_locks/gpu0.lock" true && echo FREE || echo HELD)"
log "prior: $PRIOR sha256 $(sha256sum "$PRIOR" | cut -d' ' -f1)"

log "starting S0.5 collector in tmux session $SESSION"
trks-run "$SESSION" 18101 collect --phase S0.5 --node tabular_mlp --prior "$PRIOR" --prior-sha256 "$PRIOR_SHA" \
  --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00057,0 --rep 0 --rep 1 --rep-instances 10 \
  --forks 1.5 --aa-fraction 0.1 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file "$RUN/STOP" --out "$RUN" --work "$WRUN"
log "S0.5 collector started; monitor logs/$SESSION.log / .exit and trks-status"
