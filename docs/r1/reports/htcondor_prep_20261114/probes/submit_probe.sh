#!/bin/bash
# Submit one probe JDL and record probe -> cluster id. Usage: submit_probe.sh P1
set -u
P="${1:?probe id required}"
cd /work/dwong/htcondor_prep_20261114/probes || exit 1
out=$(condor_submit "$P.jdl" 2>&1); rc=$?
printf '%s\n' "$out"
if [ "$rc" -eq 0 ]; then
  cid=$(printf '%s\n' "$out" | sed -n 's/.*submitted to cluster \([0-9][0-9]*\).*/\1/p' | head -1)
  printf '%s\t%s\t%s\n' "$P" "${cid:-}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /work/dwong/htcondor_prep_20261114/probes/clusters.tsv
  echo "RECORDED $P ${cid:-UNKNOWN}"
else
  echo "SUBMIT_FAILED $P rc=$rc"
fi
exit "$rc"
