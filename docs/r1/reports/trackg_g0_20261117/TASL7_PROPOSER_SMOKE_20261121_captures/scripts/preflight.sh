#!/bin/bash
# Read-only preflight / postflight host capture for the proposer engineering smoke.
set -uo pipefail
ROOT=/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121
CAP="$ROOT/captures"
phase="${1:?usage: preflight.sh <label>}"
out="$CAP/preflight_${phase}.txt"
{
  echo "== UTC =="; date -u +%FT%TZ
  echo "== local =="; date -Is
  echo "== host =="; hostname; uname -a; id
  echo "== boot_id =="; cat /proc/sys/kernel/random/boot_id
  echo "== uptime =="; uptime
  echo "== mem =="; free -m | head -3
  echo "== disk =="; df -h /home/dowling | tail -1
  echo "== nvidia-smi full =="; nvidia-smi
  echo "== nvidia-smi compute apps =="; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
  echo "== nvidia-smi gpu =="; nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,memory.reserved,utilization.gpu,temperature.gpu,power.draw --format=csv
  echo "== llama/ollama procs =="; pgrep -af "llama-server|llama-cli|ollama" | grep -v pgrep || echo NONE
  echo "== port 8095 =="; ss -ltn 2>/dev/null | grep -E ":8095 " || echo FREE
  echo "== flock probe gpu0.lock =="; flock -n /home/dowling/r1_locks/gpu0.lock -c "echo LOCK_FREE" 2>&1 || echo LOCK_BUSY
  echo "== gpu0.lock stat =="; stat -c "%n|%s|%Y|%Z|%y|%z|%U|%G|%a|%i" /home/dowling/r1_locks/gpu0.lock 2>&1
  echo "== lease logs sha256 =="; sha256sum /home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl 2>&1
  echo "== lease logs stat =="; stat -c "%n|%s|%Y|%Z|%y|%z|%U|%G|%a|%i" /home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl 2>&1
  echo "== /dev/shm =="; ls -la /dev/shm; echo "dev_shm_count=$(ls /dev/shm | wc -l)"
  echo "== r1_engineering =="; ls -la /home/dowling/r1_engineering
  echo "== r1_locks =="; ls -la /home/dowling/r1_locks
  echo "== self cgroup =="; cat /proc/self/cgroup
  echo "== user@1011.service memory.max =="; cat /sys/fs/cgroup/user.slice/user-1011.slice/user@1011.service/memory.max 2>/dev/null || echo n/a
  echo "== repos =="
  for r in /home/dowling/r1_trackp/harness_cond7a_20261121_t7 /home/dowling/r1_trackp/autoresearch_harness; do
    echo "--- $r"
    git -C "$r" rev-parse HEAD 2>&1
    git -C "$r" branch --show-current 2>&1
    git -C "$r" status --porcelain 2>&1 | head -5
  done
  echo "== attempt1 archive root =="; stat -c "%n|%s|%Y|%Z|%i" /home/dowling/r1_trackp/runs/p3a_operator_20261027 2>&1
  echo "== systemd user state =="; systemctl --user is-system-running 2>&1
} > "$out" 2>&1
echo "WROTE $out"
