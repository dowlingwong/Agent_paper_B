#!/bin/bash
# XC3 TASL-2 collection: the four declared sealed G.1b attempt metadata, peer-transfer verification, compare logs,
# and post-compare host state. Read-only on the sealed tree; copies into the capture directory.
set -u
B=/home/dowling/r1_tracks/t1_tasl
C=$B/captures/xc3_20261126/TASL-2
PY=$B/envs/torch312/bin/python
mkdir -p "$C/attempts"
{
  echo "# collection $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
  echo "# HEAD=$(git -C "$B/paper_xc3" rev-parse HEAD) origin/main=$(git -C "$B/paper_xc3" rev-parse origin/main)"
} > "$C/collection.txt"
for pair in "mlab_imdb 1" "mlab_ogbn_arxiv 1" "mlgym_fmnist 3" "mlgym_houseprice 1"; do
  set -- $pair
  N=$1
  A=$2
  S=$B/sealed_g1b/g1b-tasl-20261121-b/$N/attempt-$A
  D=$C/attempts/$N-attempt-$A
  mkdir -p "$D"
  cp -a "$S/job_record.json" "$S/SHA256SUMS" "$S/SEAL_RECEIPT.json" "$D/"
  {
    echo "=== $N attempt-$A ==="
    echo "--- sha256sum -c ---"
    ( cd "$S" && sha256sum -c SHA256SUMS )
    echo "--- hashes ---"
    sha256sum "$S/job_record.json" "$S/out.tar" "$S/SHA256SUMS"
    echo "$(sha256sum "$S/out.tar" | cut -d' ' -f1)  out.tar" > "$D/out_tar.sha256"
  } >> "$C/attempts/verify.txt" 2>&1
done
{
  echo "# post-compare host state $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "--- user compute processes ---"
  pgrep -u dowling -af "noise_floor|g1b_crosscheck|g1b_tasl|g5_tasl|t1_tasl"
  echo "--- disk ---"
  df -h "$B" | tail -1
  echo "--- peer tree ---"
  find "$C/peer_TASL-7" -maxdepth 3 -type f | sort
  echo "--- verdict files ---"
  ls -la "$B/paper_xc3/docs/r1/reports/tasl_chain_20261122/" | grep XC3_SHORT_VERDICT
} > "$C/postcompare_state.txt" 2>&1
echo "COLLECT2_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$C/collection.txt"
