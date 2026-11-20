#!/bin/bash
# Track G G.0 U2 per-node isolated CPU smoke runner for mlgym_houseprice.
# usage: run_node_houseprice.sh <cpus>
# Unit docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md (executed bytes 0f13d2dc…,
# reviewed bytes 397ccfd1…): one delegated 8 GiB user scope, CG inside the scope, one-line command, torch312
# env, CUDA_VISIBLE_DEVICES="", taskset CPU affinity, no --gpu-uuid, runs-root outside the repo,
# --provisional-timeout 1800; Paper A gate + CPU co-tenancy before/mid/after; data manifest/source from the
# author's --from-file setup; record verification; captures + DONE.
set -u
CPUS=${1:?cpus}
NODE=mlgym_houseprice
KIT=mlgym
BASE=/home/dowling/r1_trackg_20261117
PY=$BASE/envs/torch312/bin/python
PAPER=$BASE/Agent_paper_B_main_16185b0b
E=/home/dowling/r1_engineering/u2_iso_20261119
WT=$BASE/harness_iso_mlgym
NODE_DIR=$WT/third_party/mlgym/nodes/$NODE
SPEC=$WT/third_party/mlgym/configs/trackg/nodes/$NODE.yaml
PINS=$E/../iso_kit_update_20261119/pins/new_mlgym.json
DATA=$BASE/data/mlgym_houseprice
EXPECTED_ENV_FREEZE_SHA=d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42
EXPECTED_DEPLOYED_PIN=4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144
EXPECTED_SPEC_SHA=1b95447d3d1c0753a11749fc4b11639959e770f1aa10a142b2ff583d5a92a389
TS=$(date -u +%Y%m%dT%H%M%SZ)
EV=$E/u2_iso_${NODE}_${TS}
mkdir -p "$EV"/gate "$EV"/cpu "$EV"/runs "$EV"/logs
printf '%s\n' "$EV" > "$E/last_ev_${NODE}.txt"
LOG=$EV/logs/run_node.log
STATUS_FILE=$EV/RESULT_STATUS.txt
: > "$STATUS_FILE"
PREP=$(cat "$E/last_prep_houseprice.txt" 2>/dev/null || true)
[ -n "${PREP:-}" ] && [ -d "$PREP" ] && cp -R "$PREP" "$EV/prep"

say() { echo "$*" | tee -a "$LOG"; }
stop() { echo "STOP: $*" | tee -a "$STATUS_FILE" "$LOG"; }

say "# U2 isolated-node (CPU) run node=$NODE cpus=$CPUS ev=$EV start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ---------- host / boot / kernel ----------
{
  echo "# host/boot/kernel captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "hostname=$(hostname)"; echo "uname=$(uname -a)"
  echo "os_release:"; cat /etc/os-release
  echo "nproc=$(nproc)"; echo "loadavg=$(cat /proc/loadavg)"
  echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"
  echo "uptime=$(uptime -p) / $(uptime -s)"
  echo "mem_gib:"; free -g
  echo "nvidia_driver_installed:"; cat /proc/driver/nvidia/version 2>/dev/null | head -1
} > "$EV/host.txt" 2>&1

# ---------- env (torch312; CPU node, no GPU) ----------
PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$PY" > "$EV/env_freeze.txt" 2> "$EV/env_freeze.stderr.txt"
FREEZE_SHA=$(sha256sum "$EV/env_freeze.txt" | cut -d' ' -f1)
FREEZE_LINES=$(wc -l < "$EV/env_freeze.txt")
{
  echo "# env captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "env=$BASE/envs/torch312"
  echo "python=$("$PY" -V 2>&1)"
  echo "uv_version=$(PATH=/home/dowling/.local/bin:$PATH uv --version 2>&1)"
  echo "env_freeze_lines=$FREEZE_LINES"
  echo "env_freeze_sha256=$FREEZE_SHA"
  echo "env_freeze_sha256_expected=$EXPECTED_ENV_FREEZE_SHA"
  echo "numpy=$("$PY" -c 'import numpy;print(numpy.__version__)' 2>&1)"
  echo "pandas=$("$PY" -c 'import pandas;print(pandas.__version__)' 2>&1)"
  echo "scikit_learn=$("$PY" -c 'import sklearn;print(sklearn.__version__)' 2>&1)"
  echo "pytest=$("$PY" -c 'import pytest;print(pytest.__version__)' 2>&1)"
  echo "torch=$("$PY" -c 'import torch;print(torch.__version__)' 2>&1)"
  echo "cpu_only_note=port_smoke_gpu CPU_ONLY_NODES includes mlgym_houseprice; no --gpu-uuid; CUDA hidden inside the run"
} > "$EV/env.txt" 2>&1

# ---------- data manifest + source (author --from-file setup) ----------
{
  echo "# data captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "data_dir=$DATA"
  echo "data_outside_repo=yes"
  echo "data_manifest_sha256=$(sha256sum "$DATA/data_manifest.json" 2>&1)"
  echo "data_files=$(find "$DATA" -type f | wc -l) files / $(find "$DATA" -type f -printf '%s\n' | awk '{s+=$1} END {print s}') bytes"
  echo "data_du=$(du -sh "$DATA" 2>&1)"
  echo "data_perms:"; stat -c '%A %a %U:%G %n' "$DATA" "$DATA"/houseprice.csv "$DATA/data_manifest.json"
  echo "node_data_link=$(readlink -f "$NODE_DIR/data" 2>&1) (target=$(readlink "$NODE_DIR/data" 2>&1))"
  echo "setup_log=$(ls -t "$EV"/prep/setup.log 2>/dev/null | head -1) sha256=$(sha256sum "$EV"/prep/setup.log 2>/dev/null | cut -d' ' -f1)"
  echo "setup_ar_data_line=$(grep -m1 'AR_DATA ' "$EV"/prep/setup.log 2>/dev/null)"
  echo "manifest_source:"; python3 - "$DATA/data_manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1])); src = m.get("source", {})
digest = m["files"]["houseprice.csv"]["sha256"]
print("schema=", m.get("schema"), "node=", m.get("node"))
print("provided_by=", src.get("provided_by"))
print("from_file_name=", src.get("from_file_name"))
print("source_sha256=", src.get("sha256"), "equals_file_digest=", src.get("sha256") == digest)
print("source_md5=", src.get("md5"))
print("rows=", src.get("rows"), "kaggle=", src.get("kaggle"))
print("files=", json.dumps({k: {"sha256": v["sha256"], "bytes": v["bytes"]} for k, v in m["files"].items()}, sort_keys=True))
print("synthetic_key_present=", "synthetic" in m, "(absent => synthetic false/no marker)")
PY
} > "$EV/data_manifest.txt" 2>&1

# ---------- kit tip, spec/representative manifests, pins ----------
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
  echo "frozen_files_sha256:"; sha256sum "$NODE_DIR"/ar_*.py "$NODE_DIR"/LICENCES.md "$NODE_DIR"/prepare_data.py "$NODE_DIR"/run_fixed_budget.py "$NODE_DIR"/train.py "$NODE_DIR"/requirements.txt 2>&1
} > "$EV/kit.txt" 2>&1
{
  echo "# pins captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "pins_new_file=$PINS sha256=$(sha256sum "$PINS" 2>&1)"
  echo "committed_pin_source=accepted kit update sec 3/sec 9 / pins/new_mlgym.json (census value; full 64-hex)"
  python3 - "$PINS" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))["mlgym_houseprice"]
print("committed_file_pin[mlgym_houseprice]=" + d["pin"])
print("committed_file_entries[mlgym_houseprice]=" + str(len(d["files"])))
PY
  echo "deployed_pin_expected_from_review_C1=$EXPECTED_DEPLOYED_PIN (actual recorded from the run records)"
  echo "deployed_expected_recomputed_with_data_link:"
  cd "$WT" || exit 3
  PYTHONPATH=src "$PY" "$E/../iso_kit_update_20261119/scripts/compute_pins.py" mlgym "$NODE" 2>&1 | grep -E '"pin"' | head -2
} > "$EV/pins.txt" 2>&1
COMMITTED_PIN=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["mlgym_houseprice"]["pin"])' "$PINS" 2>/dev/null)

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
# ---------- CPU co-tenancy capture ----------
cpu_capture() {
  local out=$1
  {
    echo "# CPU census captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "nproc=$(nproc)"
    echo "loadavg=$(cat /proc/loadavg)"
    echo "users:"; ps -eo user= | sort | uniq -c | sort -rn | head -10
    echo "# mpstat all cpus (1 s)"; mpstat -P ALL 1 1 2>&1
    echo "# mpstat selected cpus $CPUS (1 s)"; mpstat -P "$CPUS" 1 1 2>&1
    echo "# kernel processes/threads"; cat /proc/loadavg
    echo "# top processes"; ps -eo pid,user,psr,pcpu,pmem,etime,args --sort=-pcpu 2>/dev/null | head -25
    echo "# foreign processes on the selected cpus"
    ps -eLo pid,user,psr,pcpu,comm 2>/dev/null | awk -v list="$CPUS" 'BEGIN{n=split(list,a,",");for(i=1;i<=n;i++)want[a[i]]=1} $3 in want {print}' | head -40
  } > "$out" 2>&1
}
disk_capture "$EV/disk_before.txt"
AVAIL_BYTES=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
if [ "${AVAIL_BYTES:-0}" -lt 53687091200 ]; then
  stop "disk free ${AVAIL_BYTES} B < 50 GiB; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 42
fi
cpu_capture "$EV/cpu/cpu_before.txt"
LOAD1=$(cut -d' ' -f1 /proc/loadavg | cut -d. -f1)
NPROC=$(nproc)
if [ "${LOAD1:-0}" -gt $((NPROC / 2)) ]; then
  stop "host 1-min load ${LOAD1} > half the ${NPROC} CPUs; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 45
fi
# chosen cpus must be mostly idle (>= 80% mean idle over the selected set in the before snapshot)
IDLE_OK=$(mpstat -P "$CPUS" 1 1 2>/dev/null | awk 'NR>4 && $NF ~ /^[0-9.]+$/ {sum+=$NF;n++} END {if (n>0) printf "%.1f", sum/n}')
{
  echo "selected_cpus=$CPUS"
  echo "selected_cpus_mean_idle_pct_before=${IDLE_OK:-unknown}"
  echo "idle_threshold_pct=80"
  echo "load_threshold=half the nproc"
  echo "1min_load_before=${LOAD1}"
  echo "nproc=$NPROC"
} >> "$EV/cpu/cpu_before.txt"
awk -v i="${IDLE_OK:-0}" 'BEGIN{exit !(i < 80)}' && {
  stop "selected CPU set mean idle ${IDLE_OK:-unknown}% < 80%; no smoke launched"
  echo "DONE_PRELAUNCH_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"
  exit 46
}

# ---------- Paper A gate (immediately before launch) ----------
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

# ---------- mid-run CPU watcher ----------
(
  i=0
  while [ "$i" -lt 300 ]; do
    i=$((i + 1))
    if pgrep -f 'python -m tests.trackg.port_smoke_gpu --node mlgym_houseprice' >/dev/null 2>&1 || [ "$((i * 2))" -ge 30 ]; then
      cpu_capture "$EV/cpu/cpu_mid.txt"
      break
    fi
    sleep 2
  done
) > /dev/null 2>&1 &
MID=$!

# ---------- build and launch the unit's one-line inner command ----------
read -r -d '' INNER <<'INNER_EOF'
cd @WT@ || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312
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
  echo "# launch env/import/versions prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "numpy=$(python -c 'import numpy;print(numpy.__version__)' 2>&1)"
  echo "pandas=$(python -c 'import pandas;print(pandas.__version__)' 2>&1)"
  echo "scikit_learn=$(python -c 'import sklearn;print(sklearn.__version__)' 2>&1)"
  echo "pytest=$(python -c 'import pytest;print(pytest.__version__)' 2>&1)"
  echo "torch=$(python -c 'import torch;print(torch.__version__)' 2>&1)"
  echo "cuda_available_under_mask=$(python -c 'import torch;print(torch.cuda.is_available())' 2>&1)"
  echo "env_freeze_live_sha256=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "env_freeze_expected=@EXPECTED_ENV_FREEZE_SHA@"
  echo "data_manifest_sha256=$(sha256sum @DATA@/data_manifest.json 2>&1)"
  echo "data_link=$(readlink @NODE_DIR@/data 2>&1)"
  echo "import_port_smoke_gpu:"; python -c 'import tests.trackg.port_smoke_gpu; print("import OK")' 2>&1
  echo "smoke_entry:"; python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("mlgym_houseprice")["budget"])' 2>&1
} > @EV@/prechecks.txt
FS=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)
[ "$FS" = "@EXPECTED_ENV_FREEZE_SHA@" ] || { echo "STOP env freeze sha $FS != @EXPECTED_ENV_FREEZE_SHA@" >&2; exit 92; }
DM=$(sha256sum @DATA@/data_manifest.json 2>/dev/null | cut -d' ' -f1)
[ "$DM" = "@DATA_MANIFEST_SHA@" ] || { echo "STOP data manifest sha $DM != @DATA_MANIFEST_SHA@" >&2; exit 93; }
ENTRY=$(python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("mlgym_houseprice") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 94 ;; esac
taskset -c @CPUS@ /usr/bin/time -v -o @EV@/time_v.txt python -m tests.trackg.port_smoke_gpu --node mlgym_houseprice --cpus @CPUS@ --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root @EV@/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
exit $RC
INNER_EOF
DATA_MANIFEST_SHA=$(sha256sum "$DATA/data_manifest.json" | cut -d' ' -f1)
INNER=${INNER//@WT@/$WT}
INNER=${INNER//@EV@/$EV}
INNER=${INNER//@NODE_DIR@/$NODE_DIR}
INNER=${INNER//@DATA@/$DATA}
INNER=${INNER//@CPUS@/$CPUS}
INNER=${INNER//@EXPECTED_ENV_FREEZE_SHA@/$EXPECTED_ENV_FREEZE_SHA}
INNER=${INNER//@DATA_MANIFEST_SHA@/$DATA_MANIFEST_SHA}
printf '%s\n' "$INNER" > "$EV/invocation_inner.sh"
say "# launching delegated 8 GiB scope (CPU node, inside-scope prechecks then smoke)"
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c "$INNER" >> "$LOG" 2>&1
SRC=$?
say "systemd_run_rc=$SRC"
grep -E '^(\{|CHECKLIST_E_PASSED )' "$LOG" > "$EV/smoke_stdout_extract.txt" 2>&1
kill "$MID" 2>/dev/null; wait "$MID" 2>/dev/null
[ -f "$EV/cpu/cpu_mid.txt" ] || cpu_capture "$EV/cpu/cpu_mid.txt"
cpu_capture "$EV/cpu/cpu_after.txt"
disk_capture "$EV/disk_after.txt"
du -sh "$EV/runs" > "$EV/runs_du.txt" 2>&1

# ---------- verify every executed run record ----------
"$PY" "$E/scripts/verify_u2_records_cpu.py" "$EV/runs" --node "$NODE" --cpus "$CPUS" \
  --smoke-log "$LOG" --committed-pin "${COMMITTED_PIN:-}" --deployed-expected "$EXPECTED_DEPLOYED_PIN" \
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
      "sealed_key:", d.get("sealed_key"), "ar_data_line:", d.get("ar_data_line"))
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
[ "$SUMMARY_RC" -eq 0 ] || { STATUS=STOP; stop "collect_smoke_summary rc=$SUMMARY_RC"; }
AVAIL_AFTER=$(df -B1 --output=avail / | tail -1 | tr -dc '0-9')
[ "${AVAIL_AFTER:-0}" -lt 53687091200 ] && { STATUS=STOP; stop "disk free after ${AVAIL_AFTER} B < 50 GiB"; }
{
  echo "status=$STATUS"
  echo "node=$NODE kit=$KIT cpus=$CPUS (CPU-only node; no GPU requested)"
  echo "evidence_dir=$EV"
  echo "utc_ts=$TS"
  echo "systemd_run_rc=$SRC"
  echo "checklist_e_passed=$(grep -c "^CHECKLIST_E_PASSED $NODE" "$LOG" 2>/dev/null || true)"
  echo "verify_full_rc=$VERIFY_RC"
  echo "kit_verify_records_rc=$VERIFY2_RC"
  echo "summary_rc=$SUMMARY_RC"
  echo "disk_avail_before_bytes=$AVAIL_BYTES"
  echo "disk_avail_after_bytes=$AVAIL_AFTER"
  echo "end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$STATUS_FILE"
if [ "$STATUS" = PASS ]; then echo "DONE_PASS $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; else echo "DONE_STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$EV/DONE"; fi
say "# finished status=$STATUS"
exit 0
