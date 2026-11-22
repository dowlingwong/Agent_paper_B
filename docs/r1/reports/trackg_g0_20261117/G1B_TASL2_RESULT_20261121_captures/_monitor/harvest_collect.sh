#!/bin/bash
# Harvest small evidence for the G.1b TASL-2 run from TASL-2 (READ-ONLY on the host: cat/ls/sha256sum/ls -t only;
# copies by scp, never writes to the host). Validated in dry-run mode against runs_dryrun_20261121 /
# sealed_dryrun_20261121 before the real harvest.
#
# Usage: [RID=... RUNS_ROOT=... SEALED_ROOT=... NODES="..." CAP=...] bash harvest_collect.sh
# Defaults point at run g1b-tasl-20261121-b and the real captures directory.
set -u
B=/home/dowling/r1_tracks/t1_tasl
RID="${RID:-g1b-tasl-20261121-b}"
RUNS_ROOT="${RUNS_ROOT:-$B/runs}"
SEALED_ROOT="${SEALED_ROOT:-$B/sealed_g1b}"
NODES="${NODES:-mlab_ogbn_arxiv mlgym_fmnist mlab_imdb mlgym_houseprice}"
CAP="${CAP:-/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116/docs/r1/reports/trackg_g0_20261117/G1B_TASL2_RESULT_20261121_captures}"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=25 portal_zhixu"
mkdir -p "$CAP/_harvest"
OUT="$CAP/_harvest/remote_harvest.txt"
: > "$OUT"

for N in $NODES; do
  echo "##### harvesting $N"
  $SSH "N=$N B=$B RID=$RID RUNS_ROOT=$RUNS_ROOT SEALED_ROOT=$SEALED_ROOT bash -s" >> "$OUT" 2>&1 <<'REMOTE'
set -u
N="${N:-}"
RA=$(ls -dt "$RUNS_ROOT/$RID/$N"/attempt-* 2>/dev/null | head -1)
SA=$(ls -dt "$SEALED_ROOT/$RID/$N"/attempt-* 2>/dev/null | head -1)
echo "NODE_BEGIN $N"
echo "RUNS_ATTEMPT=${RA:-none}"
echo "SEALED_ATTEMPT=${SA:-none}"
echo "RUNS_ALL=$(ls -d "$RUNS_ROOT/$RID/$N"/attempt-* 2>/dev/null | tr '\n' ' ')"
echo "SEALED_ALL=$(ls -d "$SEALED_ROOT/$RID/$N"/attempt-* 2>/dev/null | tr '\n' ' ')"
echo "REFUSALS=$(ls -d "$RUNS_ROOT/$RID/_refusals"/*"$N"* 2>/dev/null | tr '\n' ' ')"
if [ -n "$SA" ]; then
  echo "SEALED_LS_BEGIN"
  ls -la "$SA"
  echo "SEALED_LS_END"
  echo "SHA_VERIFY_SEALED_BEGIN"
  ( cd "$SA" && sha256sum -c SHA256SUMS 2>&1 )
  echo "SHA_VERIFY_SEALED_RC=$?"
  echo "SHA_VERIFY_SEALED_END"
  for f in job_record.json SEAL_RECEIPT.json SHA256SUMS node.log out.tar; do
    if [ -f "$SA/$f" ]; then echo "SEALED_SHA_$f=$(sha256sum "$SA/$f" | cut -d" " -f1)"; fi
  done
fi
if [ -n "$RA" ]; then
  echo "RUNS_LS_BEGIN"
  ls -la "$RA"
  echo "RUNS_LS_END"
  echo "SHA_VERIFY_RUNS_BEGIN"
  ( cd "$RA" && sha256sum -c SHA256SUMS 2>&1 )
  echo "SHA_VERIFY_RUNS_RC=$?"
  echo "SHA_VERIFY_RUNS_END"
  for f in job_record.json SHA256SUMS; do
    if [ -f "$RA/$f" ]; then echo "RUNS_SHA_$f=$(sha256sum "$RA/$f" | cut -d" " -f1)"; fi
  done
  [ -f "$RA/attempt.json" ] && echo "ATTEMPT_JSON=$(tr -d '\n' < "$RA/attempt.json")"
fi
echo "NODE_LOGS=$(ls -la "$RUNS_ROOT/$RID/_logs" 2>/dev/null | grep -- "^-" | grep -- "$N-" | awk '{print $NF}' | tr '\n' ' ')"
echo "NODE_END $N"
REMOTE

  # Determine attempt name + sealed path locally from the block just printed.
  SAD=$(sed -n '/^NODE_BEGIN '"$N"'$/,/^NODE_END '"$N"'$/p' "$OUT" | sed -n 's/^SEALED_ATTEMPT=//p' | tail -1)
  RAD=$(sed -n '/^NODE_BEGIN '"$N"'$/,/^NODE_END '"$N"'$/p' "$OUT" | sed -n 's/^RUNS_ATTEMPT=//p' | tail -1)
  if [ -n "${SAD:-}" ] && [ "$SAD" != "none" ]; then SRC="$SAD"; DST="$CAP/$N/$(basename "$SAD")"
  elif [ -n "${RAD:-}" ] && [ "$RAD" != "none" ]; then SRC="$RAD"; DST="$CAP/$N/$(basename "$RAD")"
  else echo "  no attempt dir for $N yet"; SRC=""; DST=""; fi
  if [ -n "$SRC" ]; then
    mkdir -p "$DST"
    for f in job_record.json SEAL_RECEIPT.json SHA256SUMS node.log attempt.json; do
      scp -o BatchMode=yes -o ConnectTimeout=25 "portal_zhixu:$SRC/$f" "$DST/" 2>/dev/null || true
    done
    echo "  copied -> $DST"
  fi
done

# runner script, run log, status, and any refusal records (small; read-only on host)
mkdir -p "$CAP/_run"
scp -o BatchMode=yes "portal_zhixu:$B/run_g1b_tasl2.sh" "$CAP/_run/run_g1b_tasl2.sh.txt" 2>/dev/null || true
scp -o BatchMode=yes "portal_zhixu:$B/logs/g1b_tasl2_20261121.log" "$CAP/_run/g1b_tasl2_20261121.log.txt" 2>/dev/null || true
if $SSH "test -f $B/logs/g1b_tasl2.status"; then
  scp -o BatchMode=yes "portal_zhixu:$B/logs/g1b_tasl2.status" "$CAP/_run/g1b_tasl2.status.txt" 2>/dev/null || true
else
  echo "STATUS_FILE_MISSING_AT_HARVEST $(date -u +%FT%TZ)" > "$CAP/_run/g1b_tasl2.status.txt"
fi
$SSH "ls -la $RUNS_ROOT/$RID/_logs 2>/dev/null; echo '---'; ls -la $RUNS_ROOT/$RID/_refusals 2>/dev/null" > "$CAP/_run/runs_extra_listing.txt" 2>&1
$SSH "for f in $RUNS_ROOT/$RID/_logs/*.node.log; do echo \"### \$f\"; cat \"\$f\"; echo; done 2>/dev/null" > "$CAP/_run/node_logs_all.txt" 2>&1
echo "HARVEST_DONE $(date -u +%FT%TZ)"
