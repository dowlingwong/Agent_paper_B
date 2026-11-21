#!/bin/bash
# R1-TRACKG-AR-U2-TASL2 — ONE clean isolated smoke of autoresearch_fixedtokens on TASL-2 (option A).
#
# usage: run_tasl2_smoke.sh <gpu_uuid> <cpus> <evidence_dir>
#
# TASL-2 only.  Kit worktree /home/dowling/r1_trackp/harness_cond7a_20261121 @ 7330338 (detached, clean);
# venv /home/dowling/r1_trackp/venvs/ar-cond7a (copy of trackp-gpu + node requirements); data root
# /home/dowling/r1_trackp/data (outside the repo).  One delegated 8 GiB user scope, CG inside the scope,
# one-line command, CUDA_VISIBLE_DEVICES="", taskset, runs-root outside the repo, provisional 1800 s.
# Exclusive flock on ~/r1_locks/gpu0.lock (no lease-log write); no Paper A gate on TASL-2 (Paper A is on
# Ada) but GPU exclusivity: 0 compute apps at launch + a co-tenant monitor that aborts the scope if another
# user's compute app appears.  No deletion; no push.
set -u
GPU=${1:?gpu_uuid}; CPUS=${2:?cpus}; E=${3:?evidence_dir}
BU=/home/dowling/r1_trackp
W=$BU/harness_cond7a_20261121
V=$BU/venvs/ar-cond7a
UV=/home/dowling/.local/bin/uv
NODE=autoresearch_fixedtokens
NODE_DIR=$W/nodes/$NODE
SPEC=$W/configs/trackg/nodes/$NODE.yaml
DATA=$BU/data/$NODE
EXPECTED_ENV_FREEZE_SHA=11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1
EXPECTED_SPEC_SHA=5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192
EXPECTED_DATA_MANIFEST=ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51
COMMITTED_PIN_EXPECTED=147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc
DEPLOYED_PIN_EXPECTED=$(grep -o '"pin": "[0-9a-f]\{64\}"' "$E/prep/pins_deployed_recheck.txt" 2>/dev/null | head -1 | cut -d'"' -f4)
MIN_FREE_MIB=20000
MIN_DISK_BYTES=53687091200
UNIT=tasl2_ar_smoke_cond7a
UIDN=$(id -u)
UNAME=$(id -un)
export XDG_RUNTIME_DIR=/run/user/$UIDN
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UIDN/bus
export PATH=$UV:${V}/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG=$E/logs/run_tasl2_smoke.log
STATUS=$E/RESULT_STATUS.txt
: > "$LOG"
: > "$STATUS"
say(){ echo "$*" | tee -a "$LOG"; }
stop(){ echo "STOP: $*" | tee -a "$STATUS" "$LOG"; }
done_marker(){ echo "DONE_$1 $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$E/DONE"; }
CG_PATH=/sys/fs/cgroup/user.slice/user-$UIDN.slice/user@$UIDN.service/app.slice/$UNIT.scope

say "# R1-TRACKG-AR-U2-TASL2 one isolated smoke node=$NODE gpu=$GPU cpus=$CPUS ev=$E start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "host=$(hostname) user=$UNAME uid=$UIDN"
say "committed_pin_expected=$COMMITTED_PIN_EXPECTED"
say "deployed_pin_expected(TASL-2 data root)=$DEPLOYED_PIN_EXPECTED"

# ---------- fresh-run guard ----------
if [ -e "$E/DONE" ]; then stop "evidence dir already has a DONE marker; one smoke only"; exit 3; fi
mkdir -p "$E"/{gate,gpu,sampler,logs}
if [ -e "$E/runs" ] && [ -n "$(ls -A "$E/runs" 2>/dev/null)" ]; then
  stop "runs root is not empty; fresh run root required"; done_marker PRELAUNCH_STOP; exit 3
fi
mkdir -p "$E/runs"

# ---------- host / boot / driver ----------
{
  echo "# host captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"; echo "whoami=$(whoami) uid=$(id -u) gid=$(id -g) groups=$(id -G)"
  echo "uname=$(uname -a)"; echo "nproc=$(nproc)"; echo "loadavg=$(cat /proc/loadavg)"
  echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"; echo "uptime=$(uptime -p)"
  echo "os_release:"; cat /etc/os-release
  echo "meminfo:"; head -3 /proc/meminfo; echo "free_g:"; free -g
  echo "nvidia_smi_version:"; nvidia-smi --version
  echo "driver_query:"; nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total --format=csv
  echo "nvidia_proc_version:"; cat /proc/driver/nvidia/version 2>/dev/null
  echo "sysctls:"; sysctl kernel.unprivileged_userns_clone user.max_user_namespaces kernel.yama.ptrace_scope kernel.apparmor_restrict_unprivileged_userns 2>/dev/null
  echo "systemd=$(systemd --version | head -1)"
  echo "tools: $(flock --version | head -1); $(/usr/bin/time --version 2>&1 | head -1)"
} > "$E/host_at_smoke.txt" 2>&1

# ---------- worktree / kit ----------
{
  echo "# worktree captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "worktree=$W"; echo "base_repo=$BU/autoresearch_harness"
  echo "branch=$(git -C "$W" symbolic-ref --short HEAD 2>&1)"
  echo "tip=$(git -C "$W" rev-parse HEAD 2>&1)"
  echo "tip_expected=73303380197477df971e865440d0ae11135fe1b3"
  echo "tracked_dirty_lines=$(git -C "$W" status --porcelain --untracked-files=no | wc -l)"
  echo "git_status_all:"; git -C "$W" status --porcelain
  echo "merge_base_isolation_core=$(git -C "$W" merge-base --is-ancestor 68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e HEAD && echo yes || echo no)"
  echo "merge_base_adafix=$(git -C "$W" merge-base --is-ancestor 5403392e94cb59d732f45d6702fc857531ad8fd5 HEAD && echo yes || echo no)"
  echo "spec_sha256=$(sha256sum "$SPEC" 2>&1)"
  echo "manifest_sha256=$(sha256sum "$NODE_DIR/representative_edits/manifest.json" 2>&1)"
  echo "frozen_files_sha256:"; sha256sum "$NODE_DIR"/ar_*.py "$NODE_DIR"/LICENCES.md "$NODE_DIR"/prepare.py "$NODE_DIR"/prepare_data.py "$NODE_DIR"/run_fixed_budget.py "$NODE_DIR"/requirements.txt 2>&1
  echo "code_report_sha_branch=$(git -C "$W" show HEAD:docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "no_cuda_ipc_scan:"
  cd "$W" && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src "$V/bin/python" - <<'PY'
import ast
from pathlib import Path
base = Path("nodes/autoresearch_fixedtokens")
for f in ("run_fixed_budget.py", "ar_worker.py"):
    t = ast.parse((base / f).read_text())
    hits = [n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)
            and n.attr in {"cuda_share", "cuda_open", "_share_cuda_", "_new_shared_cuda", "bind_cuda"}]
    print(f, "CUDA_IPC_API_HITS=", sorted(set(hits)) or "NONE")
PY
} > "$E/kit.txt" 2>&1

# ---------- env ----------
uv pip freeze --python "$V/bin/python" > "$E/env_freeze.txt" 2> "$E/env_freeze.stderr.txt"
{
  echo "# env captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "env=$V (copy of trackp-gpu made for this task; base venv unmodified)"
  echo "python=$("$V/bin/python" -V 2>&1)"
  echo "uv_version=$(uv --version 2>&1)"
  echo "env_freeze_lines=$(wc -l < "$E/env_freeze.txt")"
  echo "env_freeze_sha256=$(sha256sum "$E/env_freeze.txt" | cut -d' ' -f1)"
  echo "env_freeze_sha256_expected=$EXPECTED_ENV_FREEZE_SHA"
  echo "torch=$("$V/bin/python" -c 'import torch; print(torch.__version__, torch.version.cuda)' 2>&1)"
  echo "cuda_available_no_mask=$("$V/bin/python" -c 'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())' 2>&1)"
  echo "requirements_sha256=$(sha256sum "$NODE_DIR/requirements.txt" | cut -d' ' -f1)"
} > "$E/env.txt" 2>&1

# ---------- data ----------
{
  echo "# data captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "AR_TRACKG_DATA_ROOT=$BU/data (outside the repository)"
  echo "data_dir=$DATA"
  echo "data_manifest_sha256=$(sha256sum "$DATA/data_manifest.json" 2>&1)"
  echo "data_manifest_sha256_expected=$EXPECTED_DATA_MANIFEST"
  echo "data_files=$(find "$DATA" -type f | wc -l) files / $(find "$DATA" -type f -printf '%s\n' | awk '{s+=$1} END {print s}') bytes"
  echo "data_du=$(du -sh "$DATA" 2>&1)"
  echo "data_perms:"; stat -c '%A %a %U:%G %n' "$DATA" "$DATA/data_manifest.json"
  echo "node_data_link=$(readlink "$NODE_DIR/data" 2>&1)"
  echo "setup_log=$E/logs/setup_data.log sha256=$(sha256sum "$E/logs/setup_data.log" | cut -d' ' -f1)"
  echo "setup_ar_data_line=$(grep -m1 'AR_DATA ' "$E/logs/setup_data.log" 2>/dev/null)"
  echo "hf_revision_precheck=$E/prep/hf_revision_precheck.txt sha256=$(sha256sum "$E/prep/hf_revision_precheck.txt" | cut -d' ' -f1)"
  "$V/bin/python" - "$DATA/data_manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
print("node=", m.get("node"), "schema=", m.get("schema"), "files=", len(m.get("files", {})))
print("source=", json.dumps(m.get("source", {}))[:600])
print("synthetic_key_present=", "synthetic" in m)
PY
} > "$E/data_manifest.txt" 2>&1

# ---------- pins ----------
{
  echo "# pins captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "host=TASL-2 data_root=$BU/data (Ada 17 Nov/20 Nov used /home/dowling/r1_trackg_20261117/data)"
  echo "committed_file_pin=$COMMITTED_PIN_EXPECTED (20 entries; committed kit tree, no data link)"
  echo "deployed_pin_expected=$DEPLOYED_PIN_EXPECTED (21 entries incl. data -> $DATA; path-dependent)"
  echo "deployed_pin_ada_value_for_reference=069e987ac71a8ff30db7a28b7410778a4a8211aa3ecff00e23437498f2e9d2ed (Ada data root, NOT this host)"
  echo "committed_recheck:"; cat "$E/prep/pins_committed_recheck.txt" 2>/dev/null
  echo "deployed_recheck:"; cat "$E/prep/pins_deployed_recheck.txt" 2>/dev/null
} > "$E/pins.txt" 2>&1

# ---------- Paper A gate: not applicable on TASL-2 ----------
{
  echo "# Paper A gate capture $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "paper_a_gate=NOT_APPLICABLE_ON_TASL2"
  echo "reason=Paper A runs on Ada; TASL-2 authority (R1-TRACKG-AR-U2-TASL2) requires GPU exclusivity, not the Paper A gate"
  echo "substitute_controls=0 compute apps at launch; exclusive flock on ~/r1_locks/gpu0.lock; 1 s compute-app sampler; co-tenant abort monitor"
  echo "track_x_evidence_marker=$([ -e "$HOME/.r1_track_x_evidence" ] && echo PRESENT || echo absent)"
} > "$E/gate/gate_not_applicable.txt" 2>&1

# ---------- disk before ----------
disk_capture() {
  local out=$1
  {
    echo "# disk captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    df -B1 / /home /tmp 2>&1; echo; df -h / /home /tmp 2>&1
    echo "evidence_du=$(du -sh "$E" 2>&1)"; echo "runs_du=$(du -sh "$E/runs" 2>&1)"; echo "data_du=$(du -sh "$DATA" 2>&1)"
  } > "$out" 2>&1
}
disk_capture "$E/disk_before.txt"
AVAIL_BYTES=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
if [ "${AVAIL_BYTES:-0}" -lt "$MIN_DISK_BYTES" ]; then
  stop "disk free ${AVAIL_BYTES} B < 50 GiB; no smoke launched"; done_marker PRELAUNCH_STOP; exit 42
fi

# ---------- GPU qualification ----------
{
  echo "# GPU qualification $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$E/gpu/gpu_qualify.txt" 2>&1
GPU_ROW=$(nvidia-smi --query-gpu=uuid,memory.free,memory.used,utilization.gpu --format=csv,noheader | awk -F', ' -v g="$GPU" '$1==g {print $0}')
GPU_FREE=$(echo "$GPU_ROW" | awk -F', ' '{print $2}' | tr -dc '0-9')
GPU_USED=$(echo "$GPU_ROW" | awk -F', ' '{print $3}' | tr -dc '0-9')
GPU_UTIL=$(echo "$GPU_ROW" | awk -F', ' '{print $4}' | tr -dc '0-9')
GPU_APP_LINES=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | awk -F', ' -v g="$GPU" '$1==g' | wc -l | tr -dc '0-9')
{
  echo "selected_gpu_uuid=$GPU"; echo "gpu_row=$GPU_ROW"
  echo "free_mib=${GPU_FREE:-none} used_mib=${GPU_USED:-none} utilization_pct=${GPU_UTIL:-none}"
  echo "other_compute_apps_on_card=$GPU_APP_LINES"
  echo "floor_mib=$MIN_FREE_MIB (idle card, no other user's compute app)"
  echo "card_total_mib=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)"
} >> "$E/gpu/gpu_qualify.txt"
if [ -z "${GPU_FREE:-}" ] || [ "$GPU_APP_LINES" != "0" ] || [ "${GPU_FREE:-0}" -lt "$MIN_FREE_MIB" ]; then
  stop "GPU qualification failed (free=${GPU_FREE:-unknown} MiB, other apps=$GPU_APP_LINES); no smoke launched"
  done_marker PRELAUNCH_STOP; exit 41
fi

# ---------- exclusive flock on the Track P lock (no lease-log write) ----------
exec 9>"$HOME/r1_locks/gpu0.lock"
if ! flock -w 300 9; then
  stop "could not acquire exclusive flock on $HOME/r1_locks/gpu0.lock within 300 s; no smoke launched"
  done_marker PRELAUNCH_STOP; exit 45
fi
LEASE_ACQUIRED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "lease_log_written=NO (the Track P attempt-1 lease log was not touched)"
  echo "acquired_utc=$LEASE_ACQUIRED"
} > "$E/gpu/gpu_lease_status.txt"

# ---------- 1 s compute-app sampler (the unit's exact command) + timestamped companion ----------
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1 > "$E/sampler/sampler_required.csv" 2>&1 &
SAMP1=$!
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,timestamp --format=csv -l 1 > "$E/sampler/sampler_timestamped.csv" 2>&1 &
SAMP2=$!
echo "sampler_pids required=$SAMP1 timestamped=$SAMP2 started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$E/sampler/sampler_pids.txt"

# ---------- cgroup memory sampler (2 s) ----------
nohup bash "$E/scripts/sampler_cgroup.sh" "$E" "$CG_PATH" > /dev/null 2>&1 &
CGSAMP=$!

# ---------- co-tenant monitor: abort the scope if another user's compute app appears ----------
nohup bash "$E/scripts/monitor_cotenant.sh" "$E" "$GPU" "$UNIT" "$UIDN" "$UNAME" "$CG_PATH" > /dev/null 2>&1 &
MON=$!
echo "monitor_pid=$MON started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$E/gpu/co_tenant_monitor.log"

# ---------- GPU mid snapshot ----------
nohup bash "$E/scripts/gpu_mid.sh" "$E" "$GPU" "${GPU_USED:-353}" > /dev/null 2>&1 &
MID=$!

# ---------- launch the one delegated 8 GiB scope ----------
say "# launching delegated 8 GiB scope (unit $UNIT) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
date -u +%Y-%m-%dT%H:%M:%SZ > "$E/smoke_start_utc.txt"
systemd-run --user --scope --unit="$UNIT" -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  -- bash "$E/scripts/smoke_inner.sh" "$GPU" "$CPUS" "$E" >> "$LOG" 2>&1
SRC=$?
date -u +%Y-%m-%dT%H:%M:%SZ > "$E/smoke_end_utc.txt"
say "systemd_run_rc=$SRC"
grep -E '^(\{|CHECKLIST_E_PASSED )' "$LOG" > "$E/smoke_stdout_extract.txt" 2>&1

# ---------- stop samplers / monitor ----------
touch "$E/monitor_stop"
kill "$SAMP1" "$SAMP2" "$CGSAMP" "$MON" "$MID" 2>/dev/null
wait "$SAMP1" "$SAMP2" "$CGSAMP" "$MON" "$MID" 2>/dev/null
{
  echo "# gpu after $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$E/gpu/gpu_after.txt" 2>&1

# ---------- release the flock ----------
flock -u 9
LEASE_RELEASED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "released_utc=$LEASE_RELEASED" >> "$E/gpu/gpu_lease_status.txt"
exec 9>&-

disk_capture "$E/disk_after.txt"
du -sh "$E/runs" > "$E/runs_du.txt" 2>&1
{
  echo "# executed unit bytes (on-disk working copies of the executed runs) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for d in "$E"/runs/*/*/; do
    [ -d "$d" ] || continue
    echo "$(du -sb "$d" 2>/dev/null | cut -f1) $d"
  done
  echo "runs_total_bytes=$(du -sb "$E/runs" 2>/dev/null | cut -f1)"
} > "$E/executed_unit_bytes.txt" 2>&1

# ---------- sampler maximum ----------
"$V/bin/python" "$E/scripts/compute_sampler_max.py" "$GPU" "$E/sampler/sampler_required.csv" \
  "$E/sampler/sampler_timestamped.csv" "$E/sampler/sampler_max.json" > "$E/sampler/sampler_max.stdout.txt" 2>&1
SAMPLER_RC=$?
say "sampler_max_rc=$SAMPLER_RC"

# ---------- full COND7-aware record verification ----------
"$V/bin/python" "$E/scripts/verify_ar_cond7a.py" "$E/runs" --node "$NODE" --gpu "$GPU" --cpus "$CPUS" \
  --smoke-log "$LOG" --committed-pin "$COMMITTED_PIN_EXPECTED" --deployed-pin "$DEPLOYED_PIN_EXPECTED" \
  --node-spec-sha "$EXPECTED_SPEC_SHA" > "$E/verify_full.json" 2> "$E/verify_full.stderr.txt"
VERIFY_RC=$?
python3 - "$E/verify_full.json" > "$E/verify_full.summary.txt" 2>&1 <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as exc:  # noqa: BLE001
    print("verify_full.json unreadable:", repr(exc)); raise SystemExit(0)
print("ok:", d.get("ok"), "records:", d.get("records"), "executed:", d.get("executed_records"),
      "refused_s001:", d.get("refused_s001"), "deployed_pin:", d.get("deployed_pin_sha256"),
      "committed_pin:", d.get("committed_pin_sha256"), "peak_vram_mb_list:", d.get("peak_vram_mb_list"),
      "no_cuda_ipc_error:", d.get("no_cuda_ipc_error"), "B1:", d.get("B1_seconds"), "B2:", d.get("B2_seconds"))
for issue in d.get("issues", []):
    print("ISSUE:", json.dumps(issue))
PYEOF

# ---------- per-run record hashes ----------
find "$E/runs" \( -name 'run_record.json' -o -name 'run.log' -o -name 'result_channel.txt' \) | sort | xargs sha256sum > "$E/record_hashes.txt" 2>&1

# ---------- measured slowdown / peak resources ----------
"$V/bin/python" "$E/scripts/slowdown_tasl2.py" "$E" > "$E/slowdown.stdout.txt" 2> "$E/slowdown.stderr.txt"
SLOW_RC=$?
say "slowdown_rc=$SLOW_RC"

# ---------- status ----------
STATUS_TXT=PASS
[ "$SRC" -eq 0 ] || { STATUS_TXT=STOP; stop "smoke systemd_run_rc=$SRC (timeout/OOM/co-tenant kill/failure; one smoke, no retry)"; }
[ -e "$E/gpu/CONTENTION_ABORT.txt" ] && { STATUS_TXT=STOP; stop "co-tenant appeared on the card mid-smoke; scope aborted (no shared-card run)"; }
[ "$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)" -ge 1 ] || { STATUS_TXT=STOP; stop "CHECKLIST_E_PASSED $NODE missing"; }
[ "$VERIFY_RC" -eq 0 ] || { STATUS_TXT=STOP; stop "full COND7-aware verification rc=$VERIFY_RC (see verify_full.summary.txt)"; }
[ "$SAMPLER_RC" -eq 0 ] || { STATUS_TXT=STOP; stop "sampler max computation rc=$SAMPLER_RC"; }
[ "$SLOW_RC" -eq 0 ] || { STATUS_TXT=STOP; stop "slowdown analysis rc=$SLOW_RC"; }
AVAIL_AFTER=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
[ "${AVAIL_AFTER:-0}" -lt "$MIN_DISK_BYTES" ] && { STATUS_TXT=STOP; stop "disk free after ${AVAIL_AFTER} B < 50 GiB"; }
{
  echo "status=$STATUS_TXT"
  echo "node=$NODE gpu=$GPU cpus=$CPUS"
  echo "evidence_dir=$E"
  echo "utc_ts=$TS"
  echo "systemd_run_rc=$SRC"
  echo "checklist_e_passed=$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)"
  echo "verify_full_rc=$VERIFY_RC"
  echo "sampler_max_rc=$SAMPLER_RC"
  echo "slowdown_rc=$SLOW_RC"
  echo "contention_abort=$([ -e "$E/gpu/CONTENTION_ABORT.txt" ] && echo yes || echo no)"
  echo "disk_avail_before_bytes=$AVAIL_BYTES"
  echo "disk_avail_after_bytes=$AVAIL_AFTER"
  echo "lease_acquired_utc=$LEASE_ACQUIRED"
  echo "lease_released_utc=$LEASE_RELEASED"
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$STATUS"
say "# finished status=$STATUS_TXT $(date -u +%Y-%m-%dT%H:%M:%SZ)"
done_marker "$STATUS_TXT"
exit 0
