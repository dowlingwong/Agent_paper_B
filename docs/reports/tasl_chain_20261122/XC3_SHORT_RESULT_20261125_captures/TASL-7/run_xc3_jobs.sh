#!/bin/bash
# XC3 short cross-check (run g1b-tasl-20261121-b-xc3-a) — the four TASL-7 jobs, sequential, per
# docs/r1/reports/tasl_chain_20261122/XC3_SHORT_CROSSCHECK_PREP_20261125.md §7 and the signed note
# docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md. Each job is started by sweep2/t1_tasl/t1_tasl_node.sh xc
# and, on wrapper rc 0, sealed with g1b_tasl.py seal against its derived spec. Nothing is deleted; no retry.
set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_xc3
S=$P/sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json
NOTE=$P/docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md
PY=$B/envs/torch312/bin/python
C=$B/captures/xc3_20261126/TASL-7
J=$C/jobs
RUN=g1b-tasl-20261121-b-xc3-a-TASL-7
export G1B_TASL_ENABLE_REAL=1 T1_TASL_ORCHESTRATOR_PYTHON=$PY
mkdir -p "$J"
{
  echo "# driver start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) pid=$$"
  echo "# HEAD=$(git -C "$P" rev-parse HEAD) origin/main=$(git -C "$P" rev-parse origin/main)"
  echo "# spec_sha256=$(sha256sum "$S" | cut -d' ' -f1)"
  echo "# note_sha256=$(sha256sum "$NOTE" | cut -d' ' -f1)"
} > "$J/status.txt"
for N in mlab_imdb mlab_ogbn_arxiv mlgym_fmnist mlgym_houseprice; do
  {
    echo "=== $N launch-prep $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    git -C "$P" fetch origin main
    echo "fetch_rc=$? origin/main=$(git -C "$P" rev-parse origin/main)"
  } >> "$J/$N.fetch.log" 2>&1
  T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "$T0 $N launching" >> "$J/status.txt"
  bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" xc "$S" "$N" "$NOTE" TASL-7 --enable > "$J/$N.wrapper.out" 2>&1
  rc=$?
  T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "$T1 $N wrapper_rc=$rc (start $T0)" >> "$J/status.txt"
  if [ "$rc" -eq 0 ]; then
    "$PY" "$P/sweep2/t1_tasl/g1b_tasl.py" seal \
      "$B/runs/$RUN/$N/attempt-1" "$B/runs/$RUN/_specs/$N.json" --node "$N" \
      > "$J/$N.seal.json" 2> "$J/$N.seal.err"
    src=$?
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $N seal_rc=$src" >> "$J/status.txt"
    if [ "$src" -ne 0 ]; then echo "SEAL_FAILED $N" >> "$J/status.txt"; fi
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $N no-seal wrapper_rc=$rc" >> "$J/status.txt"
  fi
done
echo "ALL_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$J/status.txt"
