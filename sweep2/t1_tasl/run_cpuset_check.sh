#!/bin/bash
# R1-TASL2-CPU fixed-seed determinism check of mlgym_houseprice on TASL-2 CPUs 0-7 (G.5 draft section 12.3, S14 A).
# ENGINEERING_ONLY: three sealed attempts of the node's G.1b default part under the derived spec of
# g5_tasl.py cpuset-spec, then g5_tasl.py cpuset-verdict. No G.1b row, no label, no G.5 job.
# local/20261126-01: the three attempts share one check run (tasl2-cpuset-<node>-<YYYYMMDD>) and are produced by
# dry_run_node.py, which allows the check spec three complete attempts (an infrastructure STOP is retried in a new
# attempt; anything else stops the loop). Run from a clean checkout whose HEAD is on published main (fetched) and
# contains the fix; the driver refuses otherwise.
# The sealed attempt 1 of tasl2-cpuset-mlgym_houseprice-20261126 (G5_TASL_PREP_20261126 section 4, checkout a1597f70)
# is SUPERSEDED: it is kept as capture evidence and is never combined with new attempts. Each check is a fresh dated
# run made entirely by this driver; an existing run root or sealed run of the day is refused.
# Usage: bash run_cpuset_check.sh <new capture dir>   (on TASL-2, from the checkout's root; a fresh dir per run, which must lie
# OUTSIDE the checkout, or the clean-tree check fails). Exit 0 only on a PASS verdict.
set -u
NODE=mlgym_houseprice
CPUS=0-7
FIX=32da3235                      # local/20261126-01: the checkout must contain it
CAP=${1:?usage: run_cpuset_check.sh <capture dir>}
T1=/home/dowling/r1_tracks/t1_tasl
SEALED=$T1/sealed_g1b
REF=$SEALED/g1b-tasl-20261121-b/$NODE/attempt-1
LOCKS=/home/dowling/r1_locks
MAX_TRIES=6                       # three complete attempts plus up to three infrastructure retries
mkdir -p "$CAP" || exit 2
st() { echo "$*" | tee -a "$CAP/cpuset_driver.status"; }

st "driver_start=$(date -u +%FT%TZ)"
git rev-parse HEAD > "$CAP/cpuset.checkout.head.txt"
git status --porcelain > "$CAP/cpuset.checkout.status.txt"
if [ -s "$CAP/cpuset.checkout.status.txt" ]; then st "STOP: the checkout is not clean"; exit 2; fi
if ! git merge-base --is-ancestor "$FIX" HEAD; then st "STOP: the checkout does not contain $FIX"; exit 2; fi
if ! git fetch -q origin main || ! git merge-base --is-ancestor HEAD origin/main; then
  st "STOP: HEAD $(git rev-parse HEAD) is not on published origin/main"; exit 2; fi
D=$(date -u +%Y%m%d)
RUN=tasl2-cpuset-$NODE-$D
ROOT=$T1/runs/$RUN
SPEC=$ROOT/_specs/$NODE.json
if [ -e "$ROOT" ] || [ -e "$SEALED/$RUN" ]; then st "STOP: $ROOT or $SEALED/$RUN exists (one check run per day)"; exit 2; fi
st "run=$RUN"

# The derived spec goes to the capture dir first; the run root is created only once the leases are held, so a
# failure before that does not use up the day's run id.
CSPEC="$CAP/cpuset_spec.$NODE.json"
python3 sweep2/t1_tasl/g5_tasl.py cpuset-spec sweep2/t1_tasl/g5_tasl_spec.json --node "$NODE" --run-id "$RUN" \
  --out "$CSPEC" > "$CAP/cpuset_spec.out.json" 2> "$CAP/cpuset_spec.err"
rc=$?; st "cpuset_spec_rc=$rc"
if [ "$rc" != 0 ]; then st "STOP: cpuset-spec failed"; exit 2; fi
SPEC_SHA=$(sha256sum "$CSPEC" | cut -d' ' -f1)
echo "$SPEC_SHA  $SPEC" | tee "$CAP/cpuset_spec.sha256"

{ date -u; echo '--- load'; uptime; echo '--- relevant processes'
  ps -eo pid,user,etime,args --sort=pid | grep -E 'dry_run|g1b_tasl|run_node_job|systemd-run|g5_job' | grep -v grep
  echo '--- locks'; ls -l "$LOCKS/"; } > "$CAP/cpuset_host_before.txt" 2>&1

# The TASL-2 lease and the CPU-set leases of 0-3 and 4-7 (S13), held for the whole check; wait while any is busy.
exec 7>>"$LOCKS/gpu0.lock"; exec 8>>"$LOCKS/cpus-0-3.lock"; exec 9>>"$LOCKS/cpus-4-7.lock"
ok=0
for n in $(seq 1 720); do
  a=1
  flock -n 7 || a=0
  if [ $a = 1 ]; then flock -n 8 || a=0; fi
  if [ $a = 1 ]; then flock -n 9 || a=0; fi
  if [ $a = 1 ]; then ok=1; break; fi
  flock -u 7; flock -u 8; flock -u 9
  echo "lease busy, waiting iteration $n" >> "$CAP/cpuset_driver.status"
  sleep 5
done
if [ "$ok" != 1 ]; then st "STOP: a lease stayed busy for an hour; nothing ran"; exit 1; fi
st "leases_held=$(date -u +%FT%TZ)"
if [ -e "$ROOT" ]; then st "STOP: $ROOT appeared while waiting"; exit 2; fi
mkdir -p "$ROOT/_specs" "$ROOT/_logs" || exit 2
cp "$CSPEC" "$SPEC" || exit 2
if [ "$(sha256sum "$SPEC" | cut -d' ' -f1)" != "$SPEC_SHA" ]; then st "STOP: the copied spec differs"; exit 2; fi
{ date -u; ls -l /proc/$$/fd/7 /proc/$$/fd/8 /proc/$$/fd/9
  for f in "$LOCKS/gpu0.lock" "$LOCKS/cpus-0-3.lock" "$LOCKS/cpus-4-7.lock"; do echo "$f inode $(stat -c %i "$f")"; done
  echo '--- /proc/locks (head)'; head -40 /proc/locks; } > "$CAP/cpuset_lease_state.txt" 2>&1

ATTS=()
tries=0
# Each sealed attempt contributes two arguments: --attempt and its path.
while (( ${#ATTS[@]} / 2 < 3 && tries < MAX_TRIES )); do
  tries=$((tries + 1))
  BEFORE=$(ls -d "$ROOT/$NODE"/attempt-* 2>/dev/null | wc -l)
  LOG="$ROOT/_logs/$NODE-$(date -u +%Y%m%dT%H%M%SZ)-$$.node.log"
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- env T1_LOG="$LOG" bash -c '
    CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG"
    unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
    taskset -c '"$CPUS"' python3 sweep2/t1_tasl/dry_run_node.py "$0" '"$NODE" "$SPEC" >> "$LOG" 2>&1
  rc=$?
  AFTER=$(ls -d "$ROOT/$NODE"/attempt-* 2>/dev/null | wc -l)
  LAST=$(ls -d "$ROOT/$NODE"/attempt-* 2>/dev/null | sed 's/.*attempt-//' | sort -n | tail -1)
  st "try_${tries}_rc=$rc attempt=${LAST:-none} log=$LOG"
  if [ "$AFTER" -le "$BEFORE" ]; then st "STOP: try $tries made no new attempt (refused before the run; see $ROOT/_refusals/)"; break; fi
  if [ -z "$LAST" ] || [ ! -f "$ROOT/$NODE/attempt-$LAST/job_record.json" ]; then st "STOP: no attempt with a job record"; break; fi
  CLS=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("stop_class"))' "$ROOT/$NODE/attempt-$LAST/job_record.json")
  st "attempt_${LAST}_stop_class=$CLS"
  if [ "$rc" = 0 ] && [ "$CLS" = None ]; then
    python3 sweep2/t1_tasl/g1b_tasl.py seal "$ROOT/$NODE/attempt-$LAST" "$SPEC" --node "$NODE" \
      > "$CAP/seal_attempt_$LAST.out" 2> "$CAP/seal_attempt_$LAST.err"
    src=$?; st "seal_${LAST}_rc=$src"
    if [ "$src" != 0 ]; then st "STOP: seal of attempt $LAST failed"; break; fi
    ATTS+=(--attempt "$SEALED/$RUN/$NODE/attempt-$LAST")
  elif [ "$CLS" != infrastructure ]; then
    st "STOP: attempt $LAST ended with stop_class $CLS (rc $rc); no further attempt"; break
  fi
done
flock -u 9; flock -u 8; flock -u 7
st "leases_released=$(date -u +%FT%TZ) sealed=$(( ${#ATTS[@]} / 2 ))"
{ date -u; uptime; ps -eo pid,user,etime,args --sort=pid | grep -E 'dry_run|g1b_tasl|run_node_job|systemd-run' | grep -v grep
  echo '--- sealed'; ls -la "$SEALED/$RUN/$NODE" 2>&1; } > "$CAP/cpuset_host_after.txt" 2>&1

# The verdict over the sealed attempts (fewer than three gives STOP too_few_attempts).
OUT="$CAP/G5_TASL2_CPUSET_CHECK_${NODE}_$D.json"
if [ "${#ATTS[@]}" -eq 0 ]; then st "STOP: no sealed attempt; no verdict"; exit 1; fi
python3 sweep2/t1_tasl/g5_tasl.py cpuset-verdict sweep2/t1_tasl/g5_tasl_spec.json --node "$NODE" \
  --check-spec "$SPEC" --reference "$REF" "${ATTS[@]}" > "$OUT" 2> "$CAP/cpuset_verdict.err"
vrc=$?; st "verdict_rc=$vrc"
sha256sum "$OUT" | tee -a "$CAP/cpuset_driver.status"
python3 -c 'import json,sys; v=json.load(open(sys.argv[1])); print("verdict="+str(v.get("verdict")), "reason="+str(v.get("reason")))' "$OUT" \
  | tee -a "$CAP/cpuset_driver.status"
st "driver_end=$(date -u +%FT%TZ)"
if [ "$vrc" = 0 ] && python3 -c 'import json,sys; sys.exit(json.load(open(sys.argv[1])).get("verdict") != "PASS")' "$OUT"; then
  exit 0
fi
exit 1
