#!/bin/bash
# XC3 TASL-7 collection: sealed attempts, derived specs, job records, hashes and post-run host state.
# Read-only on the run tree; copies into the capture directory. Nothing is deleted.
set -u
B=/home/dowling/r1_tracks/t1_tasl
C=$B/captures/xc3_20261126/TASL-7
PY=$B/envs/torch312/bin/python
RUN=g1b-tasl-20261121-b-xc3-a-TASL-7
mkdir -p "$C/jobs/sealed" "$C/jobs/specs" "$C/jobs/records"
{
  echo "# collection $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
  echo "# HEAD=$(git -C "$B/paper_xc3" rev-parse HEAD) origin/main=$(git -C "$B/paper_xc3" rev-parse origin/main)"
} > "$C/jobs/collection.txt"
for N in mlab_imdb mlab_ogbn_arxiv mlgym_fmnist mlgym_houseprice; do
  d=$B/runs/$RUN/$N/attempt-1
  s=$B/sealed_g1b/$RUN/$N/attempt-1
  echo "=== $N ===" >> "$C/jobs/collection.txt"
  cp -a "$s" "$C/jobs/sealed/$N-attempt-1"
  cp -a "$d/job_record.json" "$C/jobs/records/$N.job_record.json"
  [ -f "$B/runs/$RUN/_specs/$N.json" ] && cp -a "$B/runs/$RUN/_specs/$N.json" "$C/jobs/specs/"
  {
    echo "--- unsealed attempt files ---"
    ls -la "$d"
    echo "--- sealed dir ---"
    ls -la "$s"
    echo "--- sha256sum -c on the sealed copy ---"
    ( cd "$C/jobs/sealed/$N-attempt-1" && sha256sum -c SHA256SUMS )
    echo "--- sealed file hashes ---"
    sha256sum "$s"/*
    echo "--- derived spec sha256 ---"
    sha256sum "$B/runs/$RUN/_specs/$N.json"
  } >> "$C/jobs/$N.sha256.txt" 2>&1
done
{
  echo "# post-run host state $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "--- nvidia-smi ---"
  nvidia-smi
  echo "--- compute apps ---"
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
  echo "--- lease ---"
  ls -l /home/dowling/r1_locks/
  fuser /home/dowling/r1_locks/gpu0.lock 2>&1
  echo "--- user compute processes ---"
  pgrep -u dowling -af "noise_floor|g1b_crosscheck|g1b_tasl|g5_tasl|t1_tasl|llama-server" 
  echo "--- disk ---"
  df -h "$B" | tail -1
  echo "--- runs tree ---"
  ls -la "$B/runs/$RUN"
  ls -la "$B/sealed_g1b/$RUN"
  echo "--- refusals (none expected) ---"
  ls -la "$B/runs/$RUN/_refusals" 2>&1
} > "$C/postrun_state.txt" 2>&1
"$PY" /tmp/xc3_summarise_records.py > "$C/jobs/records_summary.json" 2> "$C/jobs/records_summary.err"
echo "COLLECT_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$C/jobs/collection.txt"
