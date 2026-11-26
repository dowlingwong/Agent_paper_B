#!/bin/bash
# S4 pre-submission gates + submission (run on deepthought). Read-only checks first; one CPU job.
set -euo pipefail
D=/work/dwong/paperb/work/s4_submit
mkdir -p "$D"
cd "$D"
echo "== digest in JDL =="; grep -n "container_image" s4_local_cpu_ghcr.jdl
grep -q "sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa" s4_local_cpu_ghcr.jdl || { echo "STOP: cpu digest missing"; exit 2; }
echo "== dry-run =="
condor_submit -dry-run /tmp/s4_local_cpu_ghcr.dry s4_local_cpu_ghcr.jdl | tee dryrun.log
grep -E "^(ContainerImage|ContainerImageSource|WantContainer|Requirements|RequestCpus|RequestMemory|RequestDisk|RequestWalltime|Cmd|Iwd|TransferInput)=" /tmp/s4_local_cpu_ghcr.dry | head -20
echo "== queue snapshot before submit =="
condor_q dwong -af ClusterId ProcId JobStatus Cmd > queue_before.txt; wc -l < queue_before.txt
echo "== submit =="
condor_submit s4_local_cpu_ghcr.jdl | tee submit.txt
echo "== queue after submit =="
condor_q dwong -af ClusterId ProcId JobStatus Cmd | grep s4_run.sh || true
