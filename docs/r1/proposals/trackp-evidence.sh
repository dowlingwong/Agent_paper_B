#!/usr/bin/env bash
# trackp-evidence — Track P evidence marker and GPU-lease helper for TASL-7 (draft, 30 Oct 2026; rev 2).
# Install as ~/r1_locks/bin/trackp-evidence (chmod +x). See docs/r1/proposals/TRACKP_EVIDENCE_MARKER_20261030.md.
#
#   trackp-evidence begin <phase>                 create ~/r1_locks/trackp_evidence.active before the first
#                                                 evidence job of <phase> (e.g. P.3a); other tracks then yield
#   trackp-evidence run [--wait S] -- <cmd ...>   run one GPU job under ~/r1_locks/gpu0.lock, waiting up to S s
#                                                 (default 4200) for the lease; needs an open phase
#   trackp-evidence end <phase>                   remove the marker after the last job, or when <phase> is
#                                                 stopped for good
#   trackp-evidence status                        marker, lease and GPU 0 compute processes
#
# Exit codes: 0 ok; 1 marker state wrong; 2 usage; 75 lease not obtained within --wait; 76 GPU 0 busy (or
# nvidia-smi failing) under the lease; otherwise the job's own exit code. A job that itself exits 75 or 76 is
# told apart by the log: the helper's own 75/76 have no "job starting" line for that run.
set -euo pipefail
L=${R1_LOCKS:-$HOME/r1_locks}
M=$L/trackp_evidence.active
LOCK=$L/gpu0.lock
LOG=$L/trackp_evidence.log
mkdir -p "$L"
now() { date -u +%FT%TZ; }
log() { echo "$(now) [$$] $*" >> "$LOG"; }
usage() { sed -n '4,13p' "$0" >&2; exit 2; }

sub=${1:-}; [ $# -gt 0 ] && shift
case "$sub" in
  begin)
    ph=${1:?phase}
    if ! ( set -C; printf '{"phase":"%s","started_at":"%s","host":"%s","user":"%s"}\n' \
           "$ph" "$(now)" "$(hostname)" "$(id -un)" > "$M" ) 2>/dev/null; then
      echo "trackp-evidence: marker already present: $(cat "$M" 2>/dev/null)" >&2; exit 1
    fi
    log "begin $ph"
    echo "marker created; other tracks will yield (Track S usually within minutes, at most about 1 h)" ;;
  end)
    ph=${1:?phase}
    if [ ! -e "$M" ]; then echo "trackp-evidence: no marker" >&2; exit 1; fi
    if ! grep -qF "\"phase\":\"$ph\"," "$M"; then
      echo "trackp-evidence: marker belongs to another phase: $(cat "$M")" >&2; exit 1
    fi
    unlink "$M"; log "end $ph" ;;
  run)
    wait=4200
    if [ "${1:-}" = "--wait" ]; then [ $# -ge 2 ] || usage; wait=$2; shift 2; fi
    case "$wait" in ''|*[!0-9]*) echo "trackp-evidence: --wait needs whole seconds" >&2; exit 2 ;; esac
    if [ "${1:-}" = "--" ]; then shift; fi
    [ $# -ge 1 ] || usage
    if [ ! -e "$M" ]; then echo "trackp-evidence: run needs an open phase (trackp-evidence begin <phase>)" >&2; exit 1; fi
    log "run: waiting up to ${wait}s for the lease: $*"
    set +e
    # -o: the job and its children do not inherit the lock fd; flock itself holds the lease until the job exits.
    TPE_LOG=$LOG TPE_ID=$$ flock -o -w "$wait" -E 75 "$LOCK" bash -c '
      n="?"
      for i in $(seq 1 30); do                       # the lease is ours; let the previous holder leave GPU 0
        if out=$(nvidia-smi -i 0 --query-compute-apps=pid --format=csv,noheader 2>/dev/null); then
          n=$(printf "%s\n" "$out" | grep -c . || true)
          if [ "$n" -eq 0 ]; then
            echo "$(date -u +%FT%TZ) [$TPE_ID] run: lease and GPU 0 free; job starting" >> "$TPE_LOG"
            exec "$@"
          fi
        else
          n="unknown (nvidia-smi failed)"
        fi
        sleep 2
      done
      echo "trackp-evidence: GPU 0 not free under the lease: $n compute process(es)" >&2; exit 76' _ "$@"
    rc=$?
    set -e
    log "run: exit rc=$rc"
    exit "$rc" ;;
  status)
    if [ -e "$M" ]; then echo "marker: $(cat "$M")"; else echo "marker: absent"; fi
    if flock -n "$LOCK" true; then echo "lease: free"; else echo "lease: held"; fi
    nvidia-smi -i 0 --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null \
      || echo "nvidia-smi failed" ;;
  *) usage ;;
esac
