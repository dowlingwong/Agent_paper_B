#!/bin/bash
# I3 submission gates (run on deepthought): dry-run, gpu snapshot, submission note. One GPU job.
# usage: submit_i3.sh <nemo2|topas>
set -euo pipefail
WHICH="${1:?usage: submit_i3.sh <nemo2|topas>}"
case "$WHICH" in
  nemo2) JDL=i3_nemo2_l40s.jdl ;;
  topas) JDL=i3_topas_v100s.jdl ;;
  *) echo "unknown target $WHICH"; exit 2 ;;
esac
D="$(pwd)"
case "$D" in /work/dwong/paperb/work/i3_*) ;; *) echo "STOP: run from /work/dwong/paperb/work/i3_*"; exit 2;; esac
mkdir -p "$D"
cd "$D"
echo "== digest =="; grep -nE "container_image|docker_image" "$JDL"
grep -q "sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296" "$JDL" || { echo "STOP: gpu digest missing"; exit 2; }
echo "== gpu snapshot =="
bash /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.sh /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.tsv "pre-I3-$WHICH" >/dev/null 2>&1 || true
grep -E "pre-I3-$WHICH" /work/dwong/htcondor_prep_20261114/chain_20261114/gpu_availability.tsv | grep -E "L40S|V100S|H200|A100"
{
  echo "target=$WHICH jdl=$JDL"
  echo "image=ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35... (verified, SIF 5226487808 B)"
  echo "model=Qwen/Qwen2.5-Coder-7B-Instruct-GGUF revision 13fb94bfda8c8cf22497dc57b78f391a9acb426a"
  echo "model sha256 expected=509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c size=4683073536"
  echo "model choice reason: $WHICH (author order: NEMO2 L40S first, then TOpAS V100S once)"
} > submission_note.txt
echo "== one-at-a-time guard =="
ACTIVE=$(condor_q dwong -af Cmd 2>/dev/null | grep -c "i3_run.sh" || true)
echo "active_i3_jobs=$ACTIVE"
[ "$ACTIVE" -eq 0 ] || { echo "STOP: an i3_run job is already active"; exit 3; }
echo "== dry-run =="
AD="/tmp/${JDL}.dry"
condor_submit -dry-run "$AD" "$JDL" | tee dryrun.log
if [ -f "$AD" ]; then install -m 644 "$AD" dryrun.ad; else echo "WARN: dry-run ad $AD not found"; fi
grep -E "^(JobUniverse|ContainerImage|ContainerImageSource|DockerImage|WantContainer|WantDocker|Requirements|RequestCpus|RequestMemory|RequestDisk|RequestGPUs|RemoteJob|Cmd|TransferInput)=" dryrun.ad | head -22 || true
echo "== queue snapshot =="; condor_q dwong -af ClusterId ProcId JobStatus Cmd > queue_before.txt; wc -l < queue_before.txt
echo "== submit =="; condor_submit "$JDL" | tee submit.txt
echo "== queue after =="; condor_q dwong -af ClusterId ProcId JobStatus Cmd | grep i3_run.sh || true
