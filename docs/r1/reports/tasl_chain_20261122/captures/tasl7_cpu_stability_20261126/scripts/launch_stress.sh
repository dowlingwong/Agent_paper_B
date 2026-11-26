#!/bin/bash
# TASL-7 CPU stability stress - sequential baseline-only census runs, 6 CPU groups x 3 repeats.
#
# Read-only CPU-set stability check on TASL-7 (AMD Ryzen 9 7900X, 12C/24T, CPUs 0-23): the reviewed census
# baseline run (s000_baseline, full 2,000,000 steps, seeds 8001/8001, real pinned data, isolation, limits)
# is run once per (CPU group, repeat) - CPUs 0-3, 4-7, 8-11, 12-15, 16-19, 20-23 x 1,2,3 - sequentially,
# each inside its own delegated 8G/swap-0 systemd user scope, no GPU, PATH pinned to venv_jax first,
# absolute interpreter.  A crash of one run does not stop the remaining ones.  No system change, no
# deletion, no GPU lease, no sudo.
set -u

E=/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126
ENV=/home/dowling/r1_trackg_20261125/venv_jax
PY=$ENV/bin/python
H=/home/dowling/r1_trackg_20261125/harness_metamaze
DRIVER=$E/run_baseline_stability.py
mkdir -p "$E/logs" "$E/results" "$E/runs"
LOG=$E/logs
LEDGER=$LOG/ledger.tsv
CONSOLE=$LOG/launch_console.log

exec > >(tee -a "$CONSOLE") 2>&1

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*"; }

log "=== TASL-7 CPU stability stress launcher start; host=$(hostname); utc=$(ts)"
log "evidence root: $E"
log "kit: $H"
log "env: $ENV (absolute interpreter $PY)"
log "driver sha256: $(sha256sum "$DRIVER" | awk '{print $1}')"
log "loadavg: $(cat /proc/loadavg)"

# ---- refuse to start if the host is not idle (no other smoke of this kit / no leftover run) --------
others=$(ps -u "$(id -u)" -o pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py|port_smoke_gpu|run_baseline_stability\.py' | grep -v -E 'grep -E|launch_stress\.sh' || true)
if [ -n "$others" ]; then
  log "STOP: another kit process is running; refusing to start:"
  echo "$others" | sed 's/^/    /'
  exit 3
fi
log "idle check: no other run_fixed_budget/ar_worker/ar_parent/port_smoke process"

# ---- GPU must not be used: record state and lease file, assert no lease taken ----------------------
log "=== gpu state pre"; (nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader 2>&1 || echo "nvidia-smi unavailable") | sed 's/^/    /'
log "=== gpu lock dir"; ls -l "$HOME/r1_locks" 2>&1 | sed 's/^/    /' || true

# ---- capture the launch command and the whole binding for the record ------------------------------
{
  echo "=== TASL-7 CPU stability stress - launch commands"
  echo "authorisation: lead, 26 Nov 2026 - read-only CPU-set stability check on TASL-7, equivalent to the accepted"
  echo "  TASL-2 one, so the G.5 TASL-7 audits have evidence; work TASL-7 only; no system change (no BIOS/firmware/"
  echo "  kernel/governor/sysctl), no sudo, no deletion, no G1b/G5/G4 jobs, no GPU lease. CPU-only."
  echo "utc at write: $(ts)"
  echo "host: TASL-7 (ssh -o BatchMode=yes tasl7), AMD Ryzen 9 7900X 12-Core (Zen 4), 24 logical CPUs (0-23)"
  echo "test: the reviewed census BASELINE run only (s000_baseline) via the kit's own run_smoke_campaign with an"
  echo "  empty proposal list - same run id, seeds 8001/8001, full 2,000,000-step budget, real pinned data,"
  echo "  isolation and limits as the accepted census command (tests/trackg/port_smoke_gpu)."
  echo "groups x repeats: 0-3, 4-7, 8-11, 12-15, 16-19, 20-23 x 1,2,3 = 18 runs, sequential, no other smoke."
  echo "each run:"
  echo "  systemd-run --user --scope --unit=tasl7-baseline-<group>_r<n>-<utc> --collect \\"
  echo "    -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \\"
  echo "    env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$H/src \\"
  echo "      PATH=$ENV/bin:\$PATH VIRTUAL_ENV=$ENV HOME=/home/dowling \\"
  echo "    taskset -c <group> $PY $DRIVER --group <group> --repeat <n> \\"
  echo "      --runs-root $E/runs/g<group>_r<n> --out $E/results/g<group>_r<n>.json"
  echo "kit: $H @ aa354485bff6b5746c48ddadcb50d92e9c6f3645 (branch mac-trackg-mountaincar-20261125)"
  echo "env: $ENV (freeze 630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9)"
  echo "data: $HOME/r1_engineering/metamaze_20261125/data/mlgym_metamaze (read-only, manifest e233819526e8)"
  echo "no repository file is changed by the driver (imports only); runs root outside the repo."
} > "$E/commands.txt"
log "commands recorded: $E/commands.txt"

echo -e "group\trepeat\tutc_start\tutc_end\twall_s\trc\tresult_json\tverdict\ttail" > "$LEDGER"

i=0
for g in 0-3 4-7 8-11 12-15 16-19 20-23; do
  for r in 1 2 3; do
    i=$((i+1))
    tag="g${g//-/_}_r${r}"
    runs="$E/runs/$tag"
    out="$E/results/$tag.json"
    errlog="$LOG/$tag.stderr.txt"
    console="$LOG/$tag.console.txt"
    if [ -e "$out" ] || [ -e "$runs" ]; then
      log "SKIP $tag: result/runs already exist (no overwrite, no deletion)"
      continue
    fi
    unit="tasl7-baseline-$tag-$(date -u +%Y%m%dT%H%M%SZ)-$$"
    start=$(ts); t0=$(date +%s)
    log "=== RUN $i/18 group=$g repeat=$r unit=$unit start=$start"
    before=$(ps -u "$(id -u)" -o pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py' | grep -v -E 'grep -E|launch_stress\.sh' || true)
    [ -n "$before" ] && { log "WARNING: kit process seen just before $tag:"; echo "$before" | sed 's/^/    /'; }
    systemd-run --user --scope --unit="$unit" --collect \
      -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
      env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$H/src" \
        PATH="$ENV/bin:$PATH" VIRTUAL_ENV="$ENV" HOME="/home/dowling" \
      taskset -c "$g" "$PY" "$DRIVER" --group "$g" --repeat "$r" --runs-root "$runs" --out "$out" \
      > "$console" 2> "$errlog"
    rc=$?
    end=$(ts); t1=$(date +%s); wall=$((t1-t0))
    verdict="NO_RESULT"; tailmsg=""
    if [ -f "$out" ]; then
      verdict=$("$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));print(d.get('verdict','?'))" "$out" 2>/dev/null || echo UNREADABLE)
      tailmsg=$("$PY" -c "import json,sys;d=json.load(open(sys.argv[1]));r=d.get('run') or {};print('outcome=%s rc=%s sig=%s val=%s elapsed=%s'%( (r.get('outcome') or {}).get('kind'), (r.get('process') or {}).get('returncode'), r.get('signal'), r.get('val_return'), r.get('elapsed_seconds_info_only')))" "$out" 2>/dev/null || true)
    fi
    log "=== DONE  $i/18 group=$g repeat=$r rc=$rc wall=${wall}s verdict=$verdict $tailmsg"
    echo -e "$g\t$r\t$start\t$end\t$wall\t$rc\t$out\t$verdict\t$tailmsg" >> "$LEDGER"
    # leftover-process check: the run cgroup must have been killed; nothing may linger
    sleep 2
    left=$(ps -u "$(id -u)" -o pid=,args= | grep -E 'run_fixed_budget\.py|ar_worker\.py|ar_parent\.py' | grep -v -E 'grep -E|launch_stress\.sh' || true)
    if [ -n "$left" ]; then
      log "WARNING: leftover kit processes after $tag (recorded, not killed):"
      echo "$left" | sed 's/^/    /'
    fi
    log "loadavg after $tag: $(cat /proc/loadavg)"
  done
done

log "=== gpu state post"; (nvidia-smi --query-gpu=index,name,memory.used,utilization.gpu --format=csv,noheader 2>&1 || echo "nvidia-smi unavailable") | sed 's/^/    /'
log "=== TASL-7 CPU stability stress launcher complete utc=$(ts)"
log "results: $E/results"
log "ledger: $LEDGER"
