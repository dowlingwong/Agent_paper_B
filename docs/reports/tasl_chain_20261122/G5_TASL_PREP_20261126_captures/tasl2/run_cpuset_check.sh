#!/bin/bash
# G.5 TASL-2 houseprice cpuset determinism check (G.5 report section 12.3).
# ENGINEERING_ONLY: 3 sealed attempts of the node's G.1b default part, no G.1b row, no label.
set -u
cd /home/dowling/r1_tracks/t1_tasl/paper_g5prep || exit 2
CAP=/home/dowling/r1_tracks/t1_tasl/captures/g5_tasl_prep_20261126
D=$(date -u +%Y%m%d)
RUN=tasl2-cpuset-mlgym_houseprice-$D
ROOT=/home/dowling/r1_tracks/t1_tasl/runs/$RUN
SPEC=$ROOT/_specs/mlgym_houseprice.json
SEALED=/home/dowling/r1_tracks/t1_tasl/sealed_g1b
mkdir -p "$ROOT/_specs" "$ROOT/_logs"
echo "driver_start=$(date -u +%FT%TZ)" | tee "$CAP/cpuset_driver.status"
git rev-parse HEAD > "$CAP/cpuset.checkout.head.txt"
git status --porcelain > "$CAP/cpuset.checkout.status.txt"
echo "=== derive spec" | tee -a "$CAP/cpuset_driver.status"
python3 sweep2/t1_tasl/g5_tasl.py cpuset-spec sweep2/t1_tasl/g5_tasl_spec.json --node mlgym_houseprice --run-id "$RUN" --out "$SPEC" > "$CAP/cpuset_spec.out.json" 2> "$CAP/cpuset_spec.err"
echo "cpuset_spec_rc=$?" | tee -a "$CAP/cpuset_driver.status"
sha256sum "$SPEC" > "$CAP/cpuset_spec.sha256"
# host state before
{
  date -u
  echo '--- load'; uptime
  echo '--- relevant processes'
  ps -eo pid,user,etime,args --sort=pid | grep -E 'dry_run|g1b_tasl|run_node_job|systemd-run|expansion|baseline' | grep -v grep
  echo '--- locks before'; ls -l /home/dowling/r1_locks/
} > "$CAP/cpuset_host_before.txt" 2>&1
# leases: the TASL-2 GPU lease plus the expansion CPU-set leases of 0-3 and 4-7 (non-blocking; wait if busy)
exec 7>>/home/dowling/r1_locks/gpu0.lock
exec 8>>/home/dowling/r1_locks/cpus-0-3.lock
exec 9>>/home/dowling/r1_locks/cpus-4-7.lock
ok=0
for n in $(seq 1 120); do
  a=1
  flock -n 7 || a=0
  if [ $a = 1 ]; then flock -n 8 || a=0; fi
  if [ $a = 1 ]; then flock -n 9 || a=0; fi
  if [ $a = 1 ]; then ok=1; break; fi
  flock -u 7; flock -u 8; flock -u 9
  echo "lease busy, waiting iteration $n" >> "$CAP/cpuset_driver.status"
  sleep 5
done
if [ "$ok" != "1" ]; then echo "STOP: a lease is busy" | tee -a "$CAP/cpuset_driver.status"; exit 1; fi
echo "leases_held=$(date -u +%FT%TZ)" | tee -a "$CAP/cpuset_driver.status"
{
  date -u
  echo '--- held fd targets'; ls -l /proc/$$/fd/7 /proc/$$/fd/8 /proc/$$/fd/9
  echo '--- lock files and inodes'
  for f in /home/dowling/r1_locks/gpu0.lock /home/dowling/r1_locks/cpus-0-3.lock /home/dowling/r1_locks/cpus-4-7.lock; do echo "$f inode $(stat -c %i "$f")"; done
  echo '--- /proc/locks (head)'; cat /proc/locks | head -40
  echo '--- expansion jobs running?'
  ps -eo pid,user,etime,args --sort=pid | grep -E 'dry_run|run_node|baseline_stability|port_smoke|harness_metamaze|forest' | grep -v grep
} > "$CAP/cpuset_lease_state.txt" 2>&1
# three sealed attempts of the node's G.1b default part, pinned to cpus 0-7
for i in 1 2 3; do
  LOG="$ROOT/_logs/mlgym_houseprice-$(date -u +%Y%m%dT%H%M%SZ)-$$.node.log"
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- env T1_LOG="$LOG" bash -c '
    CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG"
    unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
    taskset -c 0-7 python3 sweep2/t1_tasl/dry_run_node.py "$0" mlgym_houseprice' "$SPEC" >> "$LOG" 2>&1
  echo "attempt_${i}_rc=$? log=$LOG" | tee -a "$CAP/cpuset_driver.status"
  python3 sweep2/t1_tasl/g1b_tasl.py seal "$ROOT/mlgym_houseprice/attempt-$i" "$SPEC" --node mlgym_houseprice > "$CAP/seal_attempt_$i.out" 2> "$CAP/seal_attempt_$i.err"
  echo "seal_${i}_rc=$?" | tee -a "$CAP/cpuset_driver.status"
done
# release the leases explicitly (the shell also holds them; release now so a sibling can use 4-7)
flock -u 9; flock -u 8; flock -u 7
echo "leases_released=$(date -u +%FT%TZ)" | tee -a "$CAP/cpuset_driver.status"
{
  date -u
  echo '--- load'; uptime
  echo '--- relevant processes after'
  ps -eo pid,user,etime,args --sort=pid | grep -E 'dry_run|g1b_tasl|run_node_job|systemd-run' | grep -v grep
  echo '--- sealed dir'; ls -la "$SEALED/$RUN/mlgym_houseprice" 2>&1
} > "$CAP/cpuset_host_after.txt" 2>&1
# verdict
python3 sweep2/t1_tasl/g5_tasl.py cpuset-verdict sweep2/t1_tasl/g5_tasl_spec.json --node mlgym_houseprice \
  --check-spec "$SPEC" --reference "$SEALED/g1b-tasl-20261121-b/mlgym_houseprice/attempt-1" \
  --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-1" --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-2" \
  --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-3" > "$CAP/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_$D.json" 2> "$CAP/cpuset_verdict.err"
echo "verdict_rc=$?" | tee -a "$CAP/cpuset_driver.status"
sha256sum "$CAP/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_$D.json" | tee -a "$CAP/cpuset_driver.status"
head -c 1800 "$CAP/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_$D.json" | tee -a "$CAP/cpuset_driver.status"
echo "driver_end=$(date -u +%FT%TZ)" | tee -a "$CAP/cpuset_driver.status"
