#!/bin/bash
# S5 pre-submission gates + submission (run on deepthought). GPU snapshot, dry-run, one GPU job.
set -euo pipefail
D=/work/dwong/paperb/work/s5_submit
mkdir -p "$D"
cp -f s5_nemo2_gpu_ghcr.jdl s5_run.sh "$D"/
cd "$D"
grep -n "container_image" s5_nemo2_gpu_ghcr.jdl
grep -q "sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296" s5_nemo2_gpu_ghcr.jdl || { echo "STOP: gpu digest missing"; exit 2; }
# fresh GPU availability snapshot + reason (author supplement 2)
bash /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.sh /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.tsv "pre-S5" >/dev/null 2>&1 || true
tail -4 /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.tsv
echo "== dry-run =="
condor_submit -dry-run /tmp/s5_nemo2_gpu_ghcr.dry s5_nemo2_gpu_ghcr.jdl | tee dryrun.log
grep -E "^(ContainerImage|ContainerImageSource|WantContainer|Requirements|RequestCpus|RequestMemory|RequestDisk|RequestWalltime|RequestGPUs|RemoteJob|Cmd|TransferInput)=" /tmp/s5_nemo2_gpu_ghcr.dry | head -22
echo "== queue snapshot before submit =="
condor_q dwong -af ClusterId ProcId JobStatus Cmd > queue_before.txt; wc -l < queue_before.txt
echo "== submit =="
condor_submit s5_nemo2_gpu_ghcr.jdl | tee submit.txt
echo "== queue after submit =="
condor_q dwong -af ClusterId ProcId JobStatus Cmd | grep s5_run.sh || true
