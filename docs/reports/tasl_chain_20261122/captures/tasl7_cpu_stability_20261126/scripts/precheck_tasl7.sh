#!/bin/bash
# TASL-7 CPU stability check - pre-stress state capture (read-only): host workload, no other smoke, GPU, governor.
set -u
E=/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126
mkdir -p "$E/logs" "$E/results" "$E/runs" "$E/host" "$E/validation"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
{
  echo "=== TASL-7 CPU stability pre-stress state $(ts)"
  echo "--- identity"; id; echo "sudo -n: $(sudo -n true 2>&1 | head -1)"
  echo "--- loadavg (1/5/15) + procs"; cat /proc/loadavg
  echo "--- uptime"; uptime
  echo "--- governor / epp snapshot"
  for c in 0 4 8 12 16 20; do
    echo "cpu$c governor=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/scaling_governor 2>/dev/null) epp=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/energy_performance_preference 2>/dev/null) cur=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/scaling_cur_freq 2>/dev/null) max=$(cat /sys/devices/system/cpu/cpu$c/cpufreq/cpuinfo_max_freq 2>/dev/null)"
  done
  echo "--- our kit processes (dowling) - must be none"
  ps -u dowling -o pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py|port_smoke_gpu|run_baseline_stability\.py|harness_metamaze|venv_jax/bin/python' | grep -v -E 'grep -E' || echo "NONE"
  echo "--- any user processes matching the kit / smoketest patterns (context)"
  ps -eo user,pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py|port_smoke_gpu|run_baseline_stability\.py|harness_metamaze' | grep -v -E 'grep -E|precheck' || echo "NONE"
  echo "--- top CPU consumers (any user, context)"
  ps -eo pid,user,pcpu,pmem,args --sort=-pcpu | head -8
  echo "--- per-cpu busy snapshot (1x)"
  mpstat -P ALL 1 1 2>/dev/null | tail -26 || echo "mpstat unavailable"
  echo "--- GPU state (recorded only; CPU-only check, no lease)"
  (nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader 2>&1 || echo "nvidia-smi unavailable")
  echo "--- lock dir (must show no lease taken by us)"; ls -la /home/dowling/r1_locks 2>&1 | head -10
  echo "--- temperature/thermal snapshot"
  (sensors 2>/dev/null | head -20) || echo "sensors unavailable"
  echo "--- disk"; df -h /home | tail -1
} 2>&1 | tee "$E/logs/precheck.txt"
echo "PRECHECK_WRITTEN $(ts)"
