#!/bin/bash
# Co-tenant monitor for the one R1-TRACKG-AR-U2-TASL2 smoke (TASL-2).
# usage: monitor_cotenant.sh <evidence_dir> <gpu_uuid> <unit> <uid> <uname> <cgroup_path>
# Every 2 s: list the used card's compute apps, resolve each owner; two consecutive ticks with a foreign
# (other-user) app => record CONTENTION_ABORT and cgroup.kill the delegated scope (no shared-card run).
set -u
E=${1:?}; GPU=${2:?}; UNIT=${3:?}; UIDN=${4:?}; UNAME=${5:?}; CG=${6:?}
foreign_ticks=0
while [ ! -f "$E/monitor_stop" ]; do
  sleep 2
  apps=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>/dev/null \
         | awk -F', ' -v g="$GPU" '$1==g {print $2":"$3}' | tr '\n' ';')
  foreign=""
  oldifs=$IFS; IFS=';'
  for a in $apps; do
    [ -n "$a" ] || continue
    pid=${a%%:*}
    u=$(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')
    [ -z "$u" ] && u=$(stat -c %U "/proc/$pid" 2>/dev/null)
    case "$u" in
      "$UNAME"|"$UIDN"|"") : ;;
      *) foreign="$foreign ${pid}:${u}" ;;
    esac
  done
  IFS=$oldifs
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),apps=[${apps}],foreign=[${foreign# }]" >> "$E/gpu/co_tenant_monitor.log"
  if [ -n "$foreign" ]; then foreign_ticks=$((foreign_ticks + 1)); else foreign_ticks=0; fi
  if [ "$foreign_ticks" -ge 2 ]; then
    {
      echo "# co-tenant abort $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "foreign_compute_apps=[${foreign# }] (two consecutive 2 s ticks)"
      echo "action=cgroup.kill the delegated scope $UNIT.scope (no shared-card run, one smoke only)"
      nvidia-smi --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv
      nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
      echo "cgroup_memory_current=$(cat "$CG/memory.current" 2>/dev/null)"
    } > "$E/gpu/CONTENTION_ABORT.txt" 2>&1
    systemctl --user kill --signal=SIGKILL --kill-whom=all "$UNIT.scope" 2>/dev/null
    echo 1 > "$CG/cgroup.kill" 2>/dev/null
    break
  fi
done
