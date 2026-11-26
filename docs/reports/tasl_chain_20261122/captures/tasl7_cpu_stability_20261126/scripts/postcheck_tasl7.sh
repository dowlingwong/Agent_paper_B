#!/bin/bash
# TASL-7 CPU stability check - post-stress state capture (read-only): leftover processes, no-change attestation.
set -u
E=/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126
H=/home/dowling/r1_trackg_20261125/harness_metamaze
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
{
  echo "=== TASL-7 CPU stability post-stress state $(ts)"
  echo "--- loadavg"; cat /proc/loadavg; uptime
  echo "--- our kit processes (must be none; leftover check)"
  ps -u dowling -o pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py|port_smoke_gpu|run_baseline_stability\.py|harness_metamaze' | grep -v -E 'grep -E' || echo "NONE"
  echo "--- our systemd scopes (must be none left)"
  systemctl --user list-units --type=scope --all 2>&1 | grep -E 'tasl7-baseline' || echo "NONE"
  echo "--- kit worktree state after the check"
  git -C "$H" rev-parse HEAD
  git -C "$H" rev-parse --abbrev-ref HEAD
  git -C "$H" status --porcelain
  echo "--- kit worktree files newer than check start (should be none under the kit)"
  find "$H" -newermt "2026-11-26 06:50:00" -type f 2>/dev/null | grep -v -E '/\.git' | head -5 || true
  echo "--- governor / epp after"
  for c in 0 4 8 12 16 20; do
    echo "cpu$c governor=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/scaling_governor 2>/dev/null) epp=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/energy_performance_preference 2>/dev/null) cur=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/scaling_cur_freq 2>/dev/null)"
  done
  echo "--- microcode after"
  grep -E '^microcode' /proc/cpuinfo | sort | uniq -c
  echo "--- GPU state after (recorded only; CPU-only check, no lease)"
  (nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader 2>&1 || echo "nvidia-smi unavailable")
  echo "--- GPU compute apps after (attribution: other users only; this check ran CUDA_VISIBLE_DEVICES=\"\")"
  nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>&1 | while IFS=, read -r pid mem; do
    pid=$(echo "$pid" | tr -d " ")
    [ -z "$pid" ] && continue
    echo "app pid=$pid mem=$mem owner=$(ps -o user= -p "$pid" 2>/dev/null) cmd=$(ps -o args= -p "$pid" 2>/dev/null | cut -c1-90)"
  done
  echo "--- our own python under venv_jax (must be none)"
  ps -u dowling -o pid=,args= | grep -F "/home/dowling/r1_trackg_20261125/venv_jax/bin/python" | grep -v grep || echo "NONE"
  echo "--- lock dir after"; ls -la /home/dowling/r1_locks 2>&1 | head -10
  echo "--- evidence root size"; du -sh "$E" 2>/dev/null; du -sh "$E"/* 2>/dev/null | head
  echo "--- disk"; df -h /home | tail -1
} 2>&1 | tee "$E/logs/postcheck.txt"
echo "POSTCHECK_WRITTEN $(ts)"
