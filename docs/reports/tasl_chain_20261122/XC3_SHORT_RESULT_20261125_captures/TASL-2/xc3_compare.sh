#!/bin/bash
# XC3 short cross-check: the four `compare --mode short` comparisons on TASL-2, per the signed note's
# `comparison` line and the prep doc §7. Run from the TASL-2 paper_xc3 checkout. Writes each verdict to the fixed
# repository path bound by the spec. Exit codes are recorded: 0 PASS, 3 STOP, 2 refusal (no verdict written).
set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_xc3
S=$P/sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json
PY=$B/envs/torch312/bin/python
X=$B/captures/xc3_20261126/peer_TASL-7
C=$B/captures/xc3_20261126/TASL-2
R=docs/r1/reports/tasl_chain_20261122
mkdir -p "$C/compare"
{
  echo "# compare driver start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
  echo "# HEAD=$(git -C "$P" rev-parse HEAD) origin/main=$(git -C "$P" rev-parse origin/main)"
  echo "# spec_sha256=$(sha256sum "$S" | cut -d' ' -f1)"
} > "$C/compare/status.txt"
# node, TASL-2 attempt number (the spec's declared sealed G.1b attempt)
for pair in "mlab_imdb 1" "mlab_ogbn_arxiv 1" "mlgym_fmnist 3" "mlgym_houseprice 1"; do
  set -- $pair
  N=$1
  A=$2
  OUT=$P/$R/G1B_XC3_SHORT_VERDICT_${N}_20261125.json
  echo "=== $N compare start $(date -u +%Y-%m-%dT%H:%M:%SZ) (TASL-7 attempt-1 vs TASL-2 attempt-$A) ===" >> "$C/compare/status.txt"
  "$PY" "$P/sweep2/t1_tasl/g1b_crosscheck.py" compare "$S" --mode short --node "$N" \
    --a "$X/$N/attempt-1" --b "$B/sealed_g1b/g1b-tasl-20261121-b/$N/attempt-$A" --out "$OUT" \
    > "$C/compare/$N.compare.out" 2> "$C/compare/$N.compare.err"
  rc=$?
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $N compare_rc=$rc out=$OUT" >> "$C/compare/status.txt"
  if [ -f "$OUT" ]; then
    sha256sum "$OUT" >> "$C/compare/verdict_shas.txt"
    cp "$OUT" "$C/compare/verdict_${N}.json"
  fi
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 3 ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $N REFUSAL_OR_ERROR rc=$rc" >> "$C/compare/status.txt"
  fi
done
echo "COMPARE_ALL_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$C/compare/status.txt"
