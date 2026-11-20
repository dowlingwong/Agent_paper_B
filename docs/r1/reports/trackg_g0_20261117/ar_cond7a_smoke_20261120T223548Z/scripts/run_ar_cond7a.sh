#!/bin/bash
# Track G R1-TRACKG-AR-COND7 option A — one isolated Ada GPU smoke of autoresearch_fixedtokens.
# usage: run_ar_cond7a.sh <gpu_uuid> <cpus>
# Fresh worktree harness_iso_ar_cond7a_20261120 @ 7330338 (origin branch mac-trackg-iso-ar-cond7a-20261120);
# one delegated 8 GiB user scope, CG inside the scope, one-line command, torch312 env, CUDA_VISIBLE_DEVICES="",
# taskset, runs-root outside the repo, provisional 1800 s; Paper A gate three-check, idle GPU >=8 GiB/no app,
# whole-smoke 1 s compute-app sampler, GPU before/mid/after census, /usr/bin/time -v, cgroup memory.max/swap and
# memory.peak, data manifest + pins, record verification (no CUDA IPC, effective:true, waivers {}, exceptions []).
set -u
GPU=${1:?gpu_uuid}; CPUS=${2:?cpus}
NODE=autoresearch_fixedtokens
BASE=/home/dowling/r1_trackg_20261117
W=$BASE/harness_iso_ar_cond7a_20261120
PY=$BASE/envs/torch312/bin/python
UV=/home/dowling/.local/bin/uv
PAPER=$BASE/Agent_paper_B_main_16185b0b
E=/home/dowling/r1_engineering/u2_iso_20261119
NODE_DIR=$W/nodes/$NODE
SPEC=$W/configs/trackg/nodes/$NODE.yaml
DATA=$BASE/data/$NODE
EXPECTED_ENV_FREEZE_SHA=d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42
EXPECTED_SPEC_SHA=5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192
EXPECTED_DATA_MANIFEST=ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51
TS=$(date -u +%Y%m%dT%H%M%SZ)
EV=$E/ar_cond7a_smoke_$TS
mkdir -p "$EV"/gate "$EV"/gpu "$EV"/sampler "$EV"/runs "$EV"/logs
printf '%s\n' "$EV" > "$E/last_ev_ar_cond7a.txt"
LOG=$EV/logs/run_node.log
STATUS_FILE=$EV/RESULT_STATUS.txt
: > "$STATUS_FILE"
PREP=$(cat "$E/last_prep_ar_cond7a.txt" 2>/dev/null || true)
[ -n "${PREP:-}" ] && [ -d "$PREP" ] && cp -R "$PREP" "$EV/prep"
COMMITTED_PIN=$(grep -o '"pin": "[0-9a-f]\{64\}"' "$EV"/prep/pins_committed.txt 2>/dev/null | head -1 | cut -d'"' -f4)
DEPLOYED_PIN_EXPECTED=$(grep -o '"pin": "[0-9a-f]\{64\}"' "$EV"/prep/pins_deployed.txt 2>/dev/null | head -1 | cut -d'"' -f4)

say() { echo "$*" | tee -a "$LOG"; }
stop() { echo "STOP: $*" | tee -a "$STATUS_FILE" "$LOG"; }

say "# R1-TRACKG-AR-COND7A isolated GPU smoke node=$NODE gpu=$GPU cpus=$CPUS ev=$EV start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ---------- host / boot / driver ----------
{
  echo "# host/boot/driver captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"; echo "uname=$(uname -a)"
  echo "os_release:"; cat /etc/os-release
  echo "nproc=$(nproc)"; echo "loadavg=$(cat /proc/loadavg)"
  echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"
  echo "uptime=$(uptime -p) / $(uptime -s)"
  echo "mem_gib:"; free -g
  echo "nvidia_smi_version:"; nvidia-smi --version
  echo "driver_query:"; nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total --format=csv
  echo "nvidia_proc_version:"; cat /proc/driver/nvidia/version 2>/dev/null
} > "$EV/host.txt" 2>&1

# ---------- worktree / spec / kit ----------
{
  echo "# worktree captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "worktree=$W"
  echo "branch=$(git -C "$W" symbolic-ref --short HEAD 2>&1)"
  echo "tip=$(git -C "$W" rev-parse HEAD 2>&1)"
  echo "tip_expected=73303380197477df971e865440d0ae11135fe1b3"
  echo "tracked_dirty_lines=$(git -C "$W" status --porcelain --untracked-files=no | wc -l)"
  echo "git_status_tracked:"; git -C "$W" status --porcelain --untracked-files=no
  echo "git_status_all:"; git -C "$W" status --porcelain
  echo "node_spec_path=$SPEC sha256=$(sha256sum "$SPEC" 2>&1)"
  echo "node_spec_manifest_sha256=$(sha256sum "$NODE_DIR/representative_edits/manifest.json" 2>&1)"
  echo "spec_raw_sha256_expected=$EXPECTED_SPEC_SHA"
  echo "frozen_files_sha256:"; sha256sum "$NODE_DIR"/ar_*.py "$NODE_DIR"/LICENCES.md "$NODE_DIR"/prepare.py "$NODE_DIR"/prepare_data.py "$NODE_DIR"/run_fixed_budget.py "$NODE_DIR"/requirements.txt 2>&1
  echo "code_report_sha_branch=$(git -C "$W" show HEAD:docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "no_cuda_ipc_scan:"; cat "$EV/prep/cuda_ipc_scan.txt" 2>/dev/null
} > "$EV/kit.txt" 2>&1

# ---------- env ----------
PATH=/home/dowling/.local/bin:$PATH "$UV" pip freeze --python "$PY" > "$EV/env_freeze.txt" 2> "$EV/env_freeze.stderr.txt"
{
  echo "# env captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "env=$BASE/envs/torch312"
  echo "python=$("$PY" -V 2>&1)"
  echo "uv_version=$(PATH=/home/dowling/.local/bin:$PATH "$UV" --version 2>&1)"
  echo "env_freeze_lines=$(wc -l < "$EV/env_freeze.txt")"
  echo "env_freeze_sha256=$(sha256sum "$EV/env_freeze.txt" | cut -d' ' -f1)"
  echo "env_freeze_sha256_expected=$EXPECTED_ENV_FREEZE_SHA"
  echo "torch=$("$PY" -c 'import torch; print(torch.__version__, torch.version.cuda)' 2>&1)"
  echo "cuda_available_no_mask=$("$PY" -c 'import torch; print(torch.cuda.is_available(), torch.cuda.device_count())' 2>&1)"
} > "$EV/env.txt" 2>&1

# ---------- data ----------
{
  echo "# data captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "AR_TRACKG_DATA_ROOT=$BASE/data (outside the repository)"
  echo "data_dir=$DATA"
  echo "data_manifest_sha256=$(sha256sum "$DATA/data_manifest.json" 2>&1)"
  echo "data_manifest_sha256_expected=$EXPECTED_DATA_MANIFEST"
  echo "data_files=$(find "$DATA" -type f | wc -l) files / $(find "$DATA" -type f -printf '%s\n' | awk '{s+=$1} END {print s}') bytes"
  echo "data_du=$(du -sh "$DATA" 2>&1)"
  echo "data_perms:"; stat -c '%A %a %U:%G %n' "$DATA" "$DATA/data_manifest.json"
  echo "node_data_link=$(readlink -f "$NODE_DIR/data" 2>&1) (target=$(readlink "$NODE_DIR/data" 2>&1))"
  echo "setup_log=$EV/prep/setup.log sha256=$(sha256sum "$EV"/prep/setup.log 2>/dev/null | cut -d' ' -f1)"
  echo "setup_ar_data_line=$(grep -m1 'AR_DATA ' "$EV"/prep/setup.log 2>/dev/null)"
  python3 - "$DATA/data_manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
print("node=", m.get("node"), "schema=", m.get("schema"), "files=", len(m.get("files", {})))
print("source=", json.dumps(m.get("source", {}))[:600])
print("synthetic_key_present=", "synthetic" in m)
PY
} > "$EV/data_manifest.txt" 2>&1

# ---------- pins ----------
{
  echo "# pins captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "committed_file_pin=$COMMITTED_PIN (20 entries; kit-update/cond7a convention; census value)"
  echo "deployed_pin_expected=$DEPLOYED_PIN_EXPECTED (21 entries with data link, recomputed at setup)"
  echo "pins_committed_capture:"; cat "$EV/prep/pins_committed.txt" 2>/dev/null
  echo "pins_deployed_capture:"; cat "$EV/prep/pins_deployed.txt" 2>/dev/null
} > "$EV/pins.txt" 2>&1

# ---------- disk ----------
disk_capture() {
  local out=$1
  {
    echo "# disk captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "df_bytes:"; df -B1 / /home /tmp 2>&1
    echo "df_human:"; df -h / /home /tmp 2>&1
    echo "evidence_du=$(du -sh "$EV" 2>&1)"
    echo "runs_du=$(du -sh "$EV/runs" 2>&1)"
    echo "data_du=$(du -sh "$DATA" 2>&1)"
    echo "evidence_root_du=$(du -sh "$E" 2>&1)"
  } > "$out" 2>&1
}
disk_capture "$EV/disk_before.txt"
AVAIL_BYTES=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
if [ "${AVAIL_BYTES:-0}" -lt 53687091200 ]; then
  stop "disk free ${AVAIL_BYTES} B < 50 GiB; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 42
fi

# ---------- GPU qualification (>=8 GiB free, no other app) ----------
{
  echo "# GPU qualification captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$EV/gpu/gpu_qualify.txt" 2>&1
GPU_ROW=$(nvidia-smi --query-gpu=uuid,memory.free,utilization.gpu --format=csv,noheader | awk -F', ' -v g="$GPU" '$1==g {print $0}')
GPU_FREE=$(echo "$GPU_ROW" | awk -F', ' '{print $2}' | tr -dc '0-9')
GPU_UTIL=$(echo "$GPU_ROW" | awk -F', ' '{print $3}' | tr -dc '0-9')
GPU_APP_LINES=$(nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | awk -F', ' -v g="$GPU" '$1==g' | wc -l | tr -dc '0-9')
{
  echo "selected_gpu_uuid=$GPU"; echo "gpu_row=$GPU_ROW"
  echo "free_mib=${GPU_FREE:-none}"; echo "utilization_pct=${GPU_UTIL:-none}"
  echo "other_compute_apps_on_card=$GPU_APP_LINES"; echo "floor_mib=8192"
} >> "$EV/gpu/gpu_qualify.txt"
if [ -z "${GPU_FREE:-}" ] || [ "$GPU_APP_LINES" != "0" ] || [ "${GPU_FREE:-0}" -lt 8192 ]; then
  stop "GPU qualification failed (free=${GPU_FREE:-unknown} MiB, other apps=$GPU_APP_LINES); no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 41
fi

# ---------- Paper A gate ----------
(cd "$PAPER" && "$PY" r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json \
  > "$EV/gate/gate_${TS}.json" 2> "$EV/gate/gate_stderr.txt")
GATE_RC=$?
GATE_JSON=$EV/gate/gate_${TS}.json
CFG_RUN_DIR=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["run_dir"])' "$PAPER/r1/scripts/configs/paper_a_status_ada.json")
CFG_ABS=$(readlink -f /home/dowling/agent-checkpoint-intervention/"$CFG_RUN_DIR" 2>/dev/null)
NEWEST_LIVE=$(ls -dt /home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_* 2>/dev/null | head -1)
PGREP_LIVE=$(pgrep -af 'port_smoke_gpu' 2>/dev/null | grep -v 'run_node' || true)
PGREP_PAPERA=$(pgrep -af 'agent-checkpoint-intervention' 2>/dev/null || true)
{
  echo "# gate captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "gate_json=$GATE_JSON"; echo "gate_json_sha256=$(sha256sum "$GATE_JSON" 2>&1)"
  echo "gate_script_rc=$GATE_RC"; echo "gate_stdout_last_line=$(tail -1 "$GATE_JSON" 2>&1)"
  echo "gate_stderr=$(cat "$EV/gate/gate_stderr.txt" 2>&1)"
  echo "configured_run_dir=$CFG_RUN_DIR -> $CFG_ABS"; echo "newest_live_dir=$NEWEST_LIVE"
  if [ "$(readlink -f "$NEWEST_LIVE" 2>/dev/null)" = "$(readlink -f "$CFG_ABS" 2>/dev/null)" ]; then echo "newest_live_equals_configured=yes"; else echo "newest_live_equals_configured=NO"; fi
  echo "pgrep_port_smoke_self_excluded=$PGREP_LIVE"; echo "pgrep_paper_a=$PGREP_PAPERA"
} > "$EV/gate/gate_check.txt" 2>&1
GATE_CHECK=$(python3 - "$GATE_JSON" <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({"ok": False, "error": repr(exc)})); raise SystemExit(0)
ok = (d.get("verdict") == "clear_finished" and d.get("paper_a_live_waiting_for_card") is False
      and ((d.get("evidence") or {}).get("gpu") or {}).get("paper_a_processes") == []
      and ((d.get("evidence") or {}).get("gpu") or {}).get("unidentified_apps") == 0)
print(json.dumps({"ok": ok, "verdict": d.get("verdict"),
                  "paper_a_live_waiting_for_card": d.get("paper_a_live_waiting_for_card"),
                  "paper_a_processes": ((d.get("evidence") or {}).get("gpu") or {}).get("paper_a_processes"),
                  "unidentified_apps": ((d.get("evidence") or {}).get("gpu") or {}).get("unidentified_apps")}))
PYEOF
)
echo "gate_three_check=$GATE_CHECK" >> "$EV/gate/gate_check.txt"
case "$GATE_CHECK" in *'"ok": true'*) : ;; *)
  stop "Paper A gate three-check not clear: $GATE_CHECK; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; exit 43 ;;
esac
grep -q 'newest_live_equals_configured=yes' "$EV/gate/gate_check.txt" || {
  stop "newest live_* dir does not equal the configured run dir; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; exit 44
}

# ---------- GPU before snapshot ----------
{
  echo "# gpu before $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$EV/gpu/gpu_before.txt" 2>&1

# ---------- 1 s sampler + mid-run GPU census ----------
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1 > "$EV/sampler/sampler_required.csv" 2>&1 &
SAMP1=$!
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,timestamp --format=csv -l 1 > "$EV/sampler/sampler_timestamped.csv" 2>&1 &
SAMP2=$!
(
  i=0
  while [ "$i" -lt 3600 ]; do
    i=$((i + 1))
    elapsed=$((i * 2))
    used=$(nvidia-smi --query-gpu=uuid,memory.used --format=csv,noheader 2>/dev/null | awk -F', ' -v g="$GPU" '$1==g {print $2}' | tr -dc '0-9')
    if [ "${used:-0}" -gt 100 ] || [ "$elapsed" -ge 60 ]; then
      {
        echo "# gpu mid (used=${used} MiB) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
        echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
      } > "$EV/gpu/gpu_mid.txt" 2>&1
      break
    fi
    sleep 2
  done
) > /dev/null 2>&1 &
MID=$!
echo "sampler_pids required=$SAMP1 timestamped=$SAMP2 mid=$MID started=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/sampler/sampler_pids.txt"

# ---------- build and launch the unit's one-line inner command ----------
read -r -d '' INNER <<'INNER_EOF'
cd @W@ || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data
export CUDA_VISIBLE_DEVICES=""
{
  echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
  echo "memory.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.max")"
  echo "memory.swap.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")"
  echo "expected_memory.max=8589934592"
  echo "expected_memory.swap.max=0"
  echo "which_python_before_PATH=$BEFORE"
  echo "which_python_after_PATH=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "PYTHONPATH=$PYTHONPATH"
  echo "VIRTUAL_ENV=$VIRTUAL_ENV"
  echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
  echo "taskset_cpus=@CPUS@"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > @EV@/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
{
  echo "# launch prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "torch=$(python -c 'import torch;print(torch.__version__, torch.version.cuda)' 2>&1)"
  echo "env_freeze_live_sha256=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "env_freeze_expected=@EXPECTED_ENV_FREEZE_SHA@"
  echo "data_manifest_sha256=$(sha256sum @DATA@/data_manifest.json 2>&1)"
  echo "data_manifest_expected=@EXPECTED_DATA_MANIFEST@"
  echo "node_data_link=$(readlink @NODE_DIR@/data 2>&1)"
  echo "spec_raw_sha256=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("@SPEC@").raw_sha256)' 2>&1)"
  echo "spec_raw_sha256_expected=@EXPECTED_SPEC_SHA@"
  echo "committed_file_pin=@COMMITTED_PIN@"
  echo "deployed_pin_expected=@DEPLOYED_PIN_EXPECTED@"
  echo "no_cuda_ipc_in_result_path:"
  python - <<'PY'
import ast
from pathlib import Path
base = Path("nodes/@NODE@")
for f in ("run_fixed_budget.py", "ar_worker.py"):
    t = ast.parse((base / f).read_text())
    hits = [n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)
            and n.attr in {"cuda_share", "cuda_open", "_share_cuda_", "_new_shared_cuda", "bind_cuda"}]
    print(f, "CUDA_IPC_API_HITS=", sorted(set(hits)) or "NONE")
PY
  echo "import_port_smoke_gpu:"; python -c 'import tests.trackg.port_smoke_gpu; print("import OK")' 2>&1
  echo "smoke_entry:"; python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("@NODE@") is not None)' 2>&1
} > @EV@/prechecks.txt
FS=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)
[ "$FS" = "@EXPECTED_ENV_FREEZE_SHA@" ] || { echo "STOP env freeze sha $FS != expected" >&2; exit 92; }
DM=$(sha256sum @DATA@/data_manifest.json 2>/dev/null | cut -d' ' -f1)
[ "$DM" = "@EXPECTED_DATA_MANIFEST@" ] || { echo "STOP data manifest sha $DM != expected" >&2; exit 93; }
SS=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("@SPEC@").raw_sha256)' 2>/dev/null)
[ "$SS" = "@EXPECTED_SPEC_SHA@" ] || { echo "STOP spec raw sha $SS != expected" >&2; exit 94; }
ENTRY=$(python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("@NODE@") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 95 ;; esac
taskset -c @CPUS@ /usr/bin/time -v -o @EV@/time_v.txt python -m tests.trackg.port_smoke_gpu --node @NODE@ --gpu-uuid @GPU@ --cpus @CPUS@ --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root @EV@/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
{
  echo "# cgroup memory after the smoke $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for f in memory.peak memory.current memory.events memory.max memory.swap.max memory.swap.current; do
    if [ -f "$AR_TEST_CGROUP_PARENT/$f" ]; then echo "$f=$(cat "$AR_TEST_CGROUP_PARENT/$f")"; else echo "$f=NOT_EXPOSED"; fi
  done
} > @EV@/memory_cgroup.txt
exit $RC
INNER_EOF
INNER=${INNER//@W@/$W}
INNER=${INNER//@EV@/$EV}
INNER=${INNER//@NODE_DIR@/$NODE_DIR}
INNER=${INNER//@DATA@/$DATA}
INNER=${INNER//@SPEC@/$SPEC}
INNER=${INNER//@NODE@/$NODE}
INNER=${INNER//@GPU@/$GPU}
INNER=${INNER//@CPUS@/$CPUS}
INNER=${INNER//@EXPECTED_ENV_FREEZE_SHA@/$EXPECTED_ENV_FREEZE_SHA}
INNER=${INNER//@EXPECTED_DATA_MANIFEST@/$EXPECTED_DATA_MANIFEST}
INNER=${INNER//@EXPECTED_SPEC_SHA@/$EXPECTED_SPEC_SHA}
INNER=${INNER//@COMMITTED_PIN@/${COMMITTED_PIN:-}}
INNER=${INNER//@DEPLOYED_PIN_EXPECTED@/${DEPLOYED_PIN_EXPECTED:-}}
printf '%s\n' "$INNER" > "$EV/invocation_inner.sh"
say "# launching delegated 8 GiB scope (cond7a GPU smoke; inside-scope prechecks then smoke)"
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c "$INNER" >> "$LOG" 2>&1
SRC=$?
say "systemd_run_rc=$SRC"
grep -E '^(\{|CHECKLIST_E_PASSED )' "$LOG" > "$EV/smoke_stdout_extract.txt" 2>&1

# ---------- stop samplers, after state ----------
kill "$SAMP1" "$SAMP2" "$MID" 2>/dev/null
wait "$SAMP1" "$SAMP2" "$MID" 2>/dev/null
{
  echo "# gpu after $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$EV/gpu/gpu_after.txt" 2>&1
disk_capture "$EV/disk_after.txt"
du -sh "$EV/runs" > "$EV/runs_du.txt" 2>&1

# ---------- sampler maximum ----------
"$PY" "$E/scripts/compute_sampler_max.py" "$GPU" "$EV/sampler/sampler_required.csv" \
  "$EV/sampler/sampler_timestamped.csv" "$EV/sampler/sampler_max.json" > "$EV/sampler/sampler_max.stdout.txt" 2>&1
SAMPLER_RC=$?
say "sampler_max_rc=$SAMPLER_RC"

# ---------- verify records ----------
"$PY" "$E/scripts/verify_ar_cond7a.py" "$EV/runs" --node "$NODE" --gpu "$GPU" --cpus "$CPUS" \
  --smoke-log "$LOG" --committed-pin "${COMMITTED_PIN:-}" --deployed-pin "${DEPLOYED_PIN_EXPECTED:-}" \
  --node-spec-sha "$EXPECTED_SPEC_SHA" > "$EV/verify_full.json" 2> "$EV/verify_full.stderr.txt"
VERIFY_RC=$?
python3 - "$EV/verify_full.json" > "$EV/verify_full.summary.txt" 2>&1 <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as exc:  # noqa: BLE001
    print("verify_full.json unreadable:", repr(exc)); raise SystemExit(0)
print("ok:", d.get("ok"), "records:", d.get("records"), "executed:", d.get("executed_records"),
      "refused_s001:", d.get("refused_s001"), "deployed_pin:", d.get("deployed_pin_sha256"),
      "committed_pin:", d.get("committed_pin_sha256"), "peak_vram_mb_list:", d.get("peak_vram_mb_list"),
      "no_cuda_ipc_error:", d.get("no_cuda_ipc_error"))
for issue in d.get("issues", []):
    print("ISSUE:", json.dumps(issue))
PYEOF
"$PY" /home/dowling/r1_engineering/iso_kit_update_20261119/scripts/verify_records.py "$EV/runs" --node "$NODE" > "$EV/verify_records.json" 2> "$EV/verify_records.stderr.txt"
VERIFY2_RC=$?
"$PY" /home/dowling/r1_engineering/iso_kit_update_20261119/scripts/collect_smoke_summary.py "$EV/runs" > "$EV/summary.json" 2> "$EV/summary.stderr.txt"
SUMMARY_RC=$?
find "$EV/runs" \( -name 'run_record.json' -o -name 'run.log' -o -name 'result_channel.txt' \) | sort | xargs sha256sum > "$EV/record_hashes.txt" 2>&1

# ---------- slowdown analysis (measured; 17 Nov reference: smoke wall 564 s, B1 67.901 s) ----------
"$PY" - "$EV" > "$EV/slowdown.json" 2> "$EV/slowdown.stderr.txt" <<'PY'
import json, re, sys
from pathlib import Path
ev = Path(sys.argv[1])
OLD_B1 = 67.901
OLD_SMOKE_WALL = 564.0
REQUESTS = 644  # 640 validation + 3 causality probe + 1 repeat, per run (cond7a report sec 8)
rows = {}
for rp in sorted((ev / "runs").rglob("run_record.json")):
    d = json.loads(rp.read_text())
    rid = d.get("run_id")
    if d.get("executed") is False or rid == "s001":
        continue
    log = rp.parent / "run.log"
    text = log.read_text(errors="replace") if log.exists() else ""
    pv = re.findall(r"AR_INFO peak_vram_mb=([0-9.]+)", text)
    rows[rid] = {
        "elapsed_seconds": d.get("elapsed_seconds_info_only"),
        "outcome_value": (d.get("outcome") or {}).get("value"),
        "peak_vram_mb_worker": float(pv[-1]) if pv else None,
    }
b1 = rows.get("s000_baseline", {}).get("elapsed_seconds")
b2 = rows.get("B2", {}).get("elapsed_seconds")
timing = {k: v for k, v in rows.items() if v["elapsed_seconds"] is not None and k != "s002"}
mean_elapsed = sum(v["elapsed_seconds"] for v in timing.values()) / len(timing) if timing else None
median = sorted(v["elapsed_seconds"] for v in timing.values())
median_elapsed = (median[len(median)//2] if median else None)
# smoke wall from the log start/end markers
log = (ev / "logs/run_node.log").read_text(errors="replace")
import datetime
start = re.search(r"start=([0-9T:Z-]+)", log)
end = re.search(r"# finished status=", log)
end_epoch = None
m = re.findall(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", (ev / "RESULT_STATUS.txt").read_text())
# fall back to file timestamps
wall = None
try:
    t0 = (ev / "disk_before.txt").stat().st_mtime
    t1 = (ev / "disk_after.txt").stat().st_mtime
    wall = round(t1 - t0, 1)
except OSError:
    pass
out = {
    "reference_17nov": {"smoke_wall_seconds": OLD_SMOKE_WALL, "B1_seconds": OLD_B1,
                        "peak_vram_mb_worker": 5211.3,
                        "source": "TRACKG_U2_AR_RESULT_20261117.md (accepted)"},
    "measured": {"smoke_wall_seconds": wall, "B1_seconds": b1, "B2_seconds": b2,
                 "mean_executed_run_seconds": round(mean_elapsed, 3) if mean_elapsed else None,
                 "median_executed_run_seconds": median_elapsed,
                 "requests_per_run": REQUESTS,
                 "per_run_slowdown_vs_17nov_B1": round(b1 / OLD_B1, 3) if b1 else None,
                 "smoke_slowdown_vs_17nov_wall": round(wall / OLD_SMOKE_WALL, 3) if wall else None,
                 "per_request_transfer_surrogate_seconds": round((b1 - OLD_B1) / REQUESTS, 4) if b1 else None,
                 "transfer_surrogate_note": "derived: (measured B1 - 67.901 s)/644 requests; the code prints no per-request transfer timer",
                 "rows": rows},
}
(ev / "slowdown.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(json.dumps(out, indent=2, sort_keys=True))
PY
SLOW_RC=$?
say "slowdown_rc=$SLOW_RC"

# ---------- status ----------
STATUS=PASS
[ "$SRC" -eq 0 ] || { STATUS=STOP; stop "smoke systemd_run_rc=$SRC (timeout/OOM/failure; no retry)"; }
[ "$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)" -ge 1 ] || { STATUS=STOP; stop "CHECKLIST_E_PASSED $NODE missing"; }
[ "$VERIFY_RC" -eq 0 ] || { STATUS=STOP; stop "full record verification rc=$VERIFY_RC (see verify_full.summary.txt)"; }
[ "$VERIFY2_RC" -eq 0 ] || { STATUS=STOP; stop "kit verify_records rc=$VERIFY2_RC"; }
[ "$SUMMARY_RC" -eq 0 ] || { STATUS=STOP; stop "collect_smoke_summary rc=$SUMMARY_RC"; }
[ "$SAMPLER_RC" -eq 0 ] || { STATUS=STOP; stop "sampler max computation rc=$SAMPLER_RC"; }
[ "$SLOW_RC" -eq 0 ] || { STATUS=STOP; stop "slowdown analysis rc=$SLOW_RC"; }
AVAIL_AFTER=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
[ "${AVAIL_AFTER:-0}" -lt 53687091200 ] && { STATUS=STOP; stop "disk free after ${AVAIL_AFTER} B < 50 GiB"; }
{
  echo "status=$STATUS"
  echo "node=$NODE gpu=$GPU cpus=$CPUS"
  echo "evidence_dir=$EV"
  echo "utc_ts=$TS"
  echo "systemd_run_rc=$SRC"
  echo "checklist_e_passed=$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)"
  echo "verify_full_rc=$VERIFY_RC"
  echo "kit_verify_records_rc=$VERIFY2_RC"
  echo "summary_rc=$SUMMARY_RC"
  echo "sampler_max_rc=$SAMPLER_RC"
  echo "slowdown_rc=$SLOW_RC"
  echo "disk_avail_before_bytes=$AVAIL_BYTES"
  echo "disk_avail_after_bytes=$AVAIL_AFTER"
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$STATUS_FILE"
if [ "$STATUS" = PASS ]; then echo "DONE_PASS $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; else echo "DONE_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; fi
say "# finished status=$STATUS"
exit 0
