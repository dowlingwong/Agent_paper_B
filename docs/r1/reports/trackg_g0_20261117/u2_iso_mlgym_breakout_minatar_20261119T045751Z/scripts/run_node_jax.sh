#!/bin/bash
# Track G G.0 U2 per-node isolated smoke runner for the JAX node mlgym_breakout_minatar.
# usage: run_node_jax.sh <gpu_uuid> <cpus>
# Unit: docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md
#   - one delegated 8 GiB user scope; CG computed inside the scope; one-line command; JAX env
#     envs/jax312 (NOT torch312); no data setup; no AR_TRACKG_DATA_ROOT;
#   - inside-scope launch prechecks BEFORE the smoke: JAX 8 GPU devices without the CUDA mask,
#     fresh uv-pip-freeze sha (sorted convention, 68 lines after the recorded test-only pytest add),
#     smoke_entry import dry-run, pytest present;
#   - then CUDA_VISIBLE_DEVICES="" and the exact port_smoke_gpu invocation; 1 s whole-smoke sampler;
#     before/mid/after GPU census; /usr/bin/time -v; gate; host/driver; pins; disk; record verification.
set -u
GPU=${1:?gpu_uuid}; CPUS=${2:?cpus}
NODE=mlgym_breakout_minatar
KIT=mlgym
BASE=/home/dowling/r1_trackg_20261117
JENV=$BASE/envs/jax312
PY=$JENV/bin/python
UV=/home/dowling/.local/bin/uv
PAPER=$BASE/Agent_paper_B_main_16185b0b
E=/home/dowling/r1_engineering/u2_iso_20261119
WT=$BASE/harness_iso_mlgym
NODE_DIR=$WT/third_party/mlgym/nodes/$NODE
SPEC=$WT/third_party/mlgym/configs/trackg/nodes/$NODE.yaml
PINS=$E/../iso_kit_update_20261119/pins/new_mlgym.json
PINSD=$E/../iso_kit_update_20261119/pins/deployed_mlgym.json
# env freeze: pre-pytest 65-line freeze sorted sha == the JAX fix record d33c9612; the recorded
# test-only pytest add (3 packages, review C3 path) gives the 68-line launch freeze below.
FIX_FREEZE_SHA=d33c96120c0be3cf20fcb2b9d783ac5366d6b0d3313e6cfe4c90583f89940217
EXPECTED_FREEZE_SHA=80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1
EXPECTED_FREEZE_LINES=68
COMMITTED_PIN=cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4
TS=$(date -u +%Y%m%dT%H%M%SZ)
EV=$E/u2_iso_${NODE}_${TS}
mkdir -p "$EV"/gate "$EV"/gpu "$EV"/sampler "$EV"/runs "$EV"/logs
printf '%s\n' "$EV" > "$E/last_ev_${NODE}.txt"
LOG=$EV/logs/run_node.log
STATUS_FILE=$EV/RESULT_STATUS.txt
: > "$STATUS_FILE"

say() { echo "$*" | tee -a "$LOG"; }
stop() { echo "STOP: $*" | tee -a "$STATUS_FILE" "$LOG"; }

say "# U2 isolated-node (JAX) run node=$NODE gpu=$GPU cpus=$CPUS ev=$EV start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

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

# ---------- env freeze / JAX versions (pre-scope capture; the fresh check is inside the scope) ----------
PATH=/home/dowling/.local/bin:$PATH "$UV" pip freeze --python "$PY" > "$EV/env_freeze.txt" 2> "$EV/env_freeze.stderr.txt"
sort "$EV/env_freeze.txt" > "$EV/env_freeze_sorted.txt"
FREEZE_SHA=$(sha256sum "$EV/env_freeze.txt" | cut -d' ' -f1)
FREEZE_SHA_SORTED=$(sha256sum "$EV/env_freeze_sorted.txt" | cut -d' ' -f1)
FREEZE_LINES=$(wc -l < "$EV/env_freeze.txt")
{
  echo "# env captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "env=$JENV"
  echo "python=$("$PY" -V 2>&1)"
  echo "uv_version=$(PATH=/home/dowling/.local/bin:$PATH "$UV" --version 2>&1)"
  echo "env_freeze_lines=$FREEZE_LINES"
  echo "env_freeze_sha256_raw=$FREEZE_SHA"
  echo "env_freeze_sha256_sorted=$FREEZE_SHA_SORTED"
  echo "env_freeze_sha256_fix_record=$FIX_FREEZE_SHA"
  echo "env_freeze_sha256_launch_expected=$EXPECTED_FREEZE_SHA"
  echo "env_freeze_lines_launch_expected=$EXPECTED_FREEZE_LINES"
  echo "jax=$("$PY" -c 'import jax; print(jax.__version__)' 2>&1)"
  echo "jaxlib=$("$PY" -c 'import jaxlib; print(jaxlib.__version__)' 2>&1)"
  echo "jax_cuda12_plugin=$("$PY" -c 'import importlib.metadata as m; print(m.version("jax-cuda12-plugin"))' 2>&1)"
  echo "jax_cuda12_pjrt=$("$PY" -c 'import importlib.metadata as m; print(m.version("jax-cuda12-pjrt"))' 2>&1)"
  echo "jax_devices_no_mask=$(env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false "$PY" -c 'import jax; ds=jax.devices(); print(len(ds), ds[0].platform if ds else None)' 2>&1)"
  echo "nvidia_cuda_nvcc_cu12=$("$PY" -c 'import importlib.metadata as m; print("present" if "nvidia-cuda-nvcc-cu12" in [d.metadata["Name"] for d in m.distributions()] else "absent")' 2>&1)"
  echo "pytest=$("$PY" -c 'import pytest; print(pytest.__version__)' 2>&1)"
  echo "test_only_pytest_add=review condition C3 path: pytest==9.2.0 + iniconfig==2.3.1 + pluggy==1.7.0 "
  echo "test_only_pytest_add_evidence=$E/prechecks_jax_20261119T045425Z (freeze diff exactly these 3 lines)"
} > "$EV/env.txt" 2>&1

# ---------- data: none (simulated gymnax Breakout-MinAtar) ----------
{
  echo "# data captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "data=none: node setup_command is empty; external_benchmark.data is 'none (simulated environment gymnax Breakout-MinAtar)'"
  echo "node_dir=$NODE_DIR"
  echo "setup_command=$(PATH=/home/dowling/.local/bin:$PATH "$PY" -c 'import yaml,sys; d=yaml.safe_load(open(sys.argv[1])); print(repr(d.get("setup_command")))' "$SPEC" 2>&1)"
  echo "external_benchmark_data=$(PATH=/home/dowling/.local/bin:$PATH "$PY" -c 'import yaml,sys; d=yaml.safe_load(open(sys.argv[1])); print(repr((d.get("external_benchmark") or {}).get("data")))' "$SPEC" 2>&1)"
  echo "data_link_in_node=$(readlink "$NODE_DIR/data" 2>/dev/null || echo none)"
  echo "data_tree_mlgym_breakout_minatar=$(test -e "$BASE/data/$NODE" && echo present || echo absent)"
  echo "dataset_download=none"
  echo "synthetic_marker=n/a (no data manifest; simulated environment)"
  echo "data_note=docs/r1/reports/trackg_g0_20261117/TRACKG_U2_DATA_PREP_20261117.md: mlgym_breakout_minatar has no data setup; the kit-update report's stale 'MinAtar data' wording is superseded"
} > "$EV/data_manifest.txt" 2>&1

# ---------- kit tip, spec/representative manifests, frozen files ----------
{
  echo "# kit captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "worktree=$WT"
  echo "branch=$(git -C "$WT" symbolic-ref --short HEAD 2>&1)"
  echo "tip=$(git -C "$WT" rev-parse HEAD 2>&1)"
  echo "tracked_dirty_lines=$(git -C "$WT" status --porcelain --untracked-files=no | wc -l)"
  echo "git_status_tracked:"; git -C "$WT" status --porcelain --untracked-files=no
  echo "git_status_all:"; git -C "$WT" status --porcelain
  echo "node_spec_path=$SPEC sha256=$(sha256sum "$SPEC" 2>&1)"
  echo "node_spec_manifest_sha256=$(sha256sum "$NODE_DIR/representative_edits/manifest.json" 2>&1)"
  echo "representative_edit_files:"; sha256sum "$NODE_DIR"/representative_edits/*.diff 2>&1
  echo "frozen_files_sha256:"; sha256sum "$NODE_DIR"/ar_*.py "$NODE_DIR"/LICENCES.md "$NODE_DIR"/policy.py "$NODE_DIR"/helpers.py "$NODE_DIR"/evaluate_policy.py "$NODE_DIR"/networks.py "$NODE_DIR"/config.yaml "$NODE_DIR"/requirements.txt "$NODE_DIR"/requirements_gpu.txt "$NODE_DIR"/run_fixed_budget.py 2>&1
} > "$EV/kit.txt" 2>&1

# ---------- pins (committed-file + deployed expected; no-data node expects equality) ----------
{
  echo "# pins captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# committed-file pin = accepted kit update sec 3/sec 10.2 (pins/new_mlgym.json); census value"
  echo "pins_new_file=$PINS sha256=$(sha256sum "$PINS" 2>&1)"
  echo "pins_deployed_file=$PINSD sha256=$(sha256sum "$PINSD" 2>&1)"
  python3 - "$PINS" "$PINSD" "$NODE" <<'PYEOF'
import json, sys
new = json.load(open(sys.argv[1])); dep = json.load(open(sys.argv[2])); node = sys.argv[3]
print(f"committed_file_pin[{node}]={new[node]['pin']}")
print(f"committed_file_entries[{node}]={len(new[node]['files'])}")
print(f"deployed_pin_expected[{node}]={dep[node]['pin']}")
print(f"pin_equality_expected=yes (no setup_command, so no data link is hashed)")
PYEOF
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
    echo "evidence_root_du=$(du -sh "$E" 2>&1)"
    echo "data_root_du=$(du -sh "$BASE/data" 2>&1)"
  } > "$out" 2>&1
}
disk_capture "$EV/disk_before.txt"

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
  echo "selected_gpu_uuid=$GPU"
  echo "gpu_row=$GPU_ROW"
  echo "free_mib=${GPU_FREE:-none}"
  echo "utilization_pct=${GPU_UTIL:-none}"
  echo "other_compute_apps_on_card=$GPU_APP_LINES"
  echo "floor_mib=8192"
} >> "$EV/gpu/gpu_qualify.txt"
if [ -z "${GPU_FREE:-}" ] || [ "$GPU_APP_LINES" != "0" ] || [ "${GPU_FREE:-0}" -lt 8192 ]; then
  stop "GPU qualification failed (free=${GPU_FREE:-unknown} MiB, other apps=$GPU_APP_LINES); no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 41
fi
AVAIL_BYTES=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
if [ "${AVAIL_BYTES:-0}" -lt 53687091200 ]; then
  stop "disk free ${AVAIL_BYTES} B < 50 GiB; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 42
fi

# ---------- Paper A gate (immediately before launch) ----------
(cd "$PAPER" && "$BASE/envs/torch312/bin/python" r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json \
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
  echo "gate_json=$GATE_JSON"
  echo "gate_json_sha256=$(sha256sum "$GATE_JSON" 2>&1)"
  echo "gate_script_rc=$GATE_RC"
  echo "gate_stdout_last_line=$(tail -1 "$GATE_JSON" 2>&1)"
  echo "gate_stderr=$(cat "$EV/gate/gate_stderr.txt" 2>&1)"
  echo "configured_run_dir=$CFG_RUN_DIR -> $CFG_ABS"
  echo "newest_live_dir=$NEWEST_LIVE"
  if [ "$(readlink -f "$NEWEST_LIVE" 2>/dev/null)" = "$(readlink -f "$CFG_ABS" 2>/dev/null)" ]; then echo "newest_live_equals_configured=yes"; else echo "newest_live_equals_configured=NO"; fi
  echo "pgrep_port_smoke_self_excluded=$PGREP_LIVE"
  echo "pgrep_paper_a=$PGREP_PAPERA"
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
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 43 ;;
esac
grep -q 'newest_live_equals_configured=yes' "$EV/gate/gate_check.txt" || {
  stop "newest live_* dir does not equal the configured run dir; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 44
}

# ---------- GPU before snapshot ----------
{
  echo "# gpu before $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
  echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
} > "$EV/gpu/gpu_before.txt" 2>&1

# ---------- 1 s compute-app sampler + mid-run census watcher ----------
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1 > "$EV/sampler/sampler_required.csv" 2>&1 &
SAMP1=$!
nohup nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,timestamp --format=csv -l 1 > "$EV/sampler/sampler_timestamped.csv" 2>&1 &
SAMP2=$!
(
  i=0
  while [ "$i" -lt 1800 ]; do
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
cd @WT@ || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=@JENV@/bin:/home/dowling/.local/bin:$PATH
export VIRTUAL_ENV=@JENV@
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
  echo "CUDA_VISIBLE_DEVICES_before_smoke=$(printenv CUDA_VISIBLE_DEVICES || echo "<unset>")"
  echo "taskset_cpus=@CPUS@"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > @EV@/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
# fresh prechecks inside the scope, BEFORE the CUDA mask
{
  echo "# JAX/device/freeze/smoke-entry prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "jax=$(python -c 'import jax; print(jax.__version__)' 2>&1)"
  echo "jaxlib=$(python -c 'import jaxlib; print(jaxlib.__version__)' 2>&1)"
  echo "jax_cuda12_plugin=$(python -c 'import importlib.metadata as m; print(m.version("jax-cuda12-plugin"))' 2>&1)"
  echo "jax_cuda12_pjrt=$(python -c 'import importlib.metadata as m; print(m.version("jax-cuda12-pjrt"))' 2>&1)"
  echo "nvidia_cuda_nvcc_cu12=$(python -c 'import importlib.metadata as m; print("present" if "nvidia-cuda-nvcc-cu12" in [d.metadata["Name"] for d in m.distributions()] else "absent")' 2>&1)"
  echo "pytest=$(python -c 'import pytest; print(pytest.__version__)' 2>&1)"
  echo "jax_devices (no CUDA mask):"
  env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'import jax; ds=jax.devices(); print("n_devices", len(ds)); print("platform", ds[0].platform if ds else None); print(ds)' 2>&1
  PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" > @EV@/precheck_freeze_live.txt 2> @EV@/precheck_freeze_live.stderr.txt
  sort @EV@/precheck_freeze_live.txt > @EV@/precheck_freeze_live_sorted.txt
  echo "live_freeze_lines=$(wc -l < @EV@/precheck_freeze_live.txt)"
  echo "live_freeze_sha256_raw=$(sha256sum @EV@/precheck_freeze_live.txt | cut -d' ' -f1)"
  echo "live_freeze_sha256_sorted=$(sha256sum @EV@/precheck_freeze_live_sorted.txt | cut -d' ' -f1)"
  echo "expected_launch_freeze_sha256_sorted=@EXPECTED_FREEZE_SHA@"
  echo "fix_record_freeze_sha256_sorted=@FIX_FREEZE_SHA@"
  echo "smoke_entry (no CUDA mask):"
  env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("mlgym_breakout_minatar"))' 2>&1
  echo "import_test_port_mlgym:"
  env -u CUDA_VISIBLE_DEVICES python -c 'import tests.trackg.test_port_mlgym; print("import OK")' 2>&1
} > @EV@/prechecks_jax.txt
NDEV=$(env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'import jax; print(len(jax.devices()))' 2>/dev/null)
[ "$NDEV" = "8" ] || { echo "STOP jax.devices() count is $NDEV, expected 8" >&2; exit 92; }
LFS=$(sha256sum @EV@/precheck_freeze_live_sorted.txt | cut -d' ' -f1)
[ "$LFS" = "@EXPECTED_FREEZE_SHA@" ] || { echo "STOP launch env freeze sha $LFS != expected @EXPECTED_FREEZE_SHA@" >&2; exit 93; }
ENTRY=$(env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("mlgym_breakout_minatar") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 94 ;; esac
export CUDA_VISIBLE_DEVICES=""
taskset -c @CPUS@ /usr/bin/time -v -o @EV@/time_v.txt python -m tests.trackg.port_smoke_gpu --node @NODE@ --gpu-uuid @GPU@ --cpus @CPUS@ --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root @EV@/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
exit $RC
INNER_EOF
INNER=${INNER//@WT@/$WT}
INNER=${INNER//@JENV@/$JENV}
INNER=${INNER//@EV@/$EV}
INNER=${INNER//@NODE@/$NODE}
INNER=${INNER//@GPU@/$GPU}
INNER=${INNER//@CPUS@/$CPUS}
INNER=${INNER//@FIX_FREEZE_SHA@/$FIX_FREEZE_SHA}
INNER=${INNER//@EXPECTED_FREEZE_SHA@/$EXPECTED_FREEZE_SHA}
printf '%s\n' "$INNER" > "$EV/invocation_inner.sh"
say "# launching delegated 8 GiB scope (JAX env, inside-scope prechecks then smoke)"
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

# ---------- verify every executed run record ----------
"$PY" "$E/scripts/verify_u2_records_jax.py" "$EV/runs" --node "$NODE" --gpu "$GPU" --cpus "$CPUS" \
  --smoke-log "$LOG" > "$EV/verify_full.json" 2> "$EV/verify_full.stderr.txt"
VERIFY_RC=$?
python3 - "$EV/verify_full.json" > "$EV/verify_full.summary.txt" 2>&1 <<'PYEOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as exc:  # noqa: BLE001
    print("verify_full.json unreadable:", repr(exc)); raise SystemExit(0)
print("ok:", d.get("ok"), "records:", d.get("records"), "executed:", d.get("executed_records"),
      "refused_s001:", d.get("refused_s001"), "deployed_pin:", d.get("deployed_pin_sha256"),
      "sealed_key:", d.get("sealed_key"))
for issue in d.get("issues", []):
    print("ISSUE:", json.dumps(issue))
PYEOF
"$PY" /home/dowling/r1_engineering/iso_kit_update_20261119/scripts/verify_records.py "$EV/runs" --node "$NODE" > "$EV/verify_records.json" 2> "$EV/verify_records.stderr.txt"
VERIFY2_RC=$?
"$PY" /home/dowling/r1_engineering/iso_kit_update_20261119/scripts/collect_smoke_summary.py "$EV/runs" > "$EV/summary.json" 2> "$EV/summary.stderr.txt"
SUMMARY_RC=$?
find "$EV/runs" \( -name 'run_record.json' -o -name 'run.log' -o -name 'result_channel.txt' \) | sort | xargs sha256sum > "$EV/record_hashes.txt" 2>&1

# ---------- status ----------
STATUS=PASS
[ "$SRC" -eq 0 ] || { STATUS=STOP; stop "smoke systemd_run_rc=$SRC (precheck/timeout/OOM/failure; no retry per unit)"; }
[ "$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)" -ge 1 ] || { STATUS=STOP; stop "CHECKLIST_E_PASSED $NODE missing"; }
[ "$VERIFY_RC" -eq 0 ] || { STATUS=STOP; stop "full record verification rc=$VERIFY_RC (see verify_full.summary.txt)"; }
[ "$VERIFY2_RC" -eq 0 ] || { STATUS=STOP; stop "kit verify_records rc=$VERIFY2_RC"; }
[ "$SAMPLER_RC" -eq 0 ] || { STATUS=STOP; stop "sampler max computation rc=$SAMPLER_RC"; }
AVAIL_AFTER=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
[ "${AVAIL_AFTER:-0}" -lt 53687091200 ] && { STATUS=STOP; stop "disk free after ${AVAIL_AFTER} B < 50 GiB"; }
{
  echo "status=$STATUS"
  echo "node=$NODE kit=$KIT gpu=$GPU cpus=$CPUS"
  echo "evidence_dir=$EV"
  echo "utc_ts=$TS"
  echo "systemd_run_rc=$SRC"
  echo "checklist_e_passed=$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)"
  echo "verify_full_rc=$VERIFY_RC"
  echo "kit_verify_records_rc=$VERIFY2_RC"
  echo "summary_rc=$SUMMARY_RC"
  echo "sampler_max_rc=$SAMPLER_RC"
  echo "disk_avail_before_bytes=$AVAIL_BYTES"
  echo "disk_avail_after_bytes=$AVAIL_AFTER"
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$STATUS_FILE"
if [ "$STATUS" = PASS ]; then echo "DONE_PASS $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; else echo "DONE_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; fi
say "# finished status=$STATUS"
exit 0
