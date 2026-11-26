#!/bin/bash
# HTCondor probe for the night of 13/14 Nov 2026 (P1-P7).
# Authority: docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md §4 and the errata A4/A7.
# Prints the resource fingerprint the runbook asks for and exits 0. Read-only in the job.
set -u
PROBE="${1:-UNNAMED}"
echo "probe=$PROBE"
echo "hostname=$(hostname -f 2>/dev/null || hostname)"
echo "date_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "nproc=$(nproc 2>/dev/null)"
echo "cpu_model=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2- | sed 's/^ *//')"
echo "== free -g =="; free -g 2>&1
for p in /work /ceph /ceph/srv /cvmfs /scratch /tmp "$PWD"; do
  if [ -e "$p" ]; then
    echo "df[$p]=$(df -h "$p" 2>/dev/null | awk 'NR==2{print "size="$2" avail="$4" use="$5" on="$6}')"
  else
    echo "df[$p]=MISSING"
  fi
done
echo "== env NVIDIA|CUDA =="; env | grep -E 'NVIDIA|CUDA' | head -20
echo "== env _CONDOR (first 40) =="; env | grep -E '^_CONDOR_' | head -40
echo "== gpu =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi -L 2>&1
  nvidia-smi --query-gpu=name,uuid,memory.total,driver_version,compute_cap --format=csv,noheader 2>&1
else
  echo "nvidia-smi MISSING"
fi
show() { echo "-- $1 --"; sed -n '1,200p' "$1" 2>&1; }
exit 0
