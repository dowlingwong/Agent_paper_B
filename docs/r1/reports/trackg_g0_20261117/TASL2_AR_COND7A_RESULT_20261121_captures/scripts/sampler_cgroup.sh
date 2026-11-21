#!/bin/bash
# cgroup v2 memory sampler (2 s) for the one R1-TRACKG-AR-U2-TASL2 smoke (TASL-2).
# usage: sampler_cgroup.sh <evidence_dir> <cgroup_path>
set -u
E=${1:?}; CG=${2:?}
while [ ! -f "$E/monitor_stop" ]; do
  cur=$(cat "$CG/memory.current" 2>/dev/null)
  peak=$(cat "$CG/memory.peak" 2>/dev/null)
  ev=$(tr '\n' ';' < "$CG/memory.events" 2>/dev/null)
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),current_bytes=${cur:-NA},peak_bytes=${peak:-NA},events=${ev:-NA}" >> "$E/sampler/cgroup_sampler.csv"
  sleep 2
done
