#!/bin/bash
# R1-T1-HOST-TASL TASL-2 G.1b pre-launch host check (G.1b/T1_TASL_PLAN §6 items in scope; HARNESS_ISOLATION
# §3 items 1-7 at the harness pin c025f89a).  ENGINEERING_ONLY.  Runs in one session, writes captures/,
# SUMMARY.{json,txt}, SHA256SUMS.  Nothing is deleted, committed or pushed; TASL-7, the Track P attempt-1
# archive/lease log, HTCondor and deepthought are not touched.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_engineering/tasl2_t1_precheck_20261121
T1=/home/dowling/r1_tracks/t1_tasl
REPO=$T1/harness
VENV=$T1/envs/torch312/bin/python
JAXPY=$T1/envs/jax312/bin/python
SYS=/usr/bin/python3
UV=/home/dowling/.local/bin/uv
PIN=c025f89aeafc2199bf3487b4bcaa16678273c702
CAP="$BASE/captures"
SCRIPTS="$BASE/scripts"
mkdir -p "$CAP/logs" "$BASE/work" "$BASE/records"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export PYTHONDONTWRITEBYTECODE=1
cd "$BASE" || exit 2
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "$STAMP" > "$CAP/stamp_utc.txt"
: > "$CAP/step_results.txt"

run_step() {
  local name="$1"; shift
  local logf="$CAP/logs/$name.log"
  { echo "=== $name start $(date -u +%FT%TZ)"; printf 'cmd:'; printf ' %q' "$@"; echo; "$@"; } >"$logf" 2>&1
  local rc=$?
  echo "--- $name rc=$rc" >>"$logf"
  echo "$name rc=$rc" | tee -a "$CAP/step_results.txt"
  return $rc
}

echo "=== R1-T1-HOST-TASL TASL-2 pre-launch host check start $STAMP host=$(hostname) euid=$(id -u) base=$BASE repo=$REPO pin=$PIN"
"$VENV" -VV; "$JAXPY" -VV; "$SYS" -VV; "$UV" --version

# ---- T1 dirs (created in this prep; pre-existing r1_tracks work untouched) -----------------------------
{
  echo "=== t1_tasl dirs $(date -u +%FT%TZ)"
  ls -ld "$T1"/{base,runs,sealed_g1b,sealed_g4,data,proposer,envs,harness}
  echo "=== envs"
  ls -l "$T1/envs"
  echo "=== existing r1_tracks (not modified)"
  ls -la /home/dowling/r1_tracks/
} > "$CAP/t1_dirs.txt" 2>&1

# ---- HARNESSISOLATION §3 item 7 inputs: host/kernel/tool/GPU facts, harness pin state ----------------
run_step host_facts "$VENV" "$SCRIPTS/probe_host.py" --repo "$REPO" --base "$BASE" \
  --out "$CAP/host.json" --text "$CAP/host_facts.txt"
nvidia-smi -L > "$CAP/nvidia_smi_L.txt" 2>&1
nvidia-smi > "$CAP/gpu_state_before.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_before_all.txt" 2>&1
{
  echo "=== harness pin $(date -u +%FT%TZ)"
  echo "pin=$PIN"
  echo "head=$(git -C "$REPO" rev-parse HEAD)"
  echo "symbolic_ref_rc=$(git -C "$REPO" symbolic-ref -q HEAD; echo rc=$?)"
  echo "status_porcelain_start"
  git -C "$REPO" status --porcelain
  echo "status_porcelain_end"
  git -C "$REPO" log --oneline -3
  git -C "$REPO" remote -v
  echo "origin_branch=$(git -C "$REPO" rev-parse origin/mac-trackg-t1-tasl-20261121)"
} > "$CAP/harness_pin.txt" 2>&1

# ---- T1 §6.5: the census environments at Python 3.12.16, freeze byte equality, torch/jax GPU ---------
run_step env_check "$VENV" "$SCRIPTS/probe_env.py" --out "$CAP/env_check.json" --text "$CAP/env_check.txt"

# ---- HARNESS_ISOLATION §3 item 1: unprivileged user+mount+PID+network(+cgroup) namespaces -------------
run_step c1_userns_venv "$VENV" "$SCRIPTS/probe_userns.py" --out "$CAP/c1_userns_venv.json"
run_step c1_userns_syspy "$SYS" "$SCRIPTS/probe_userns.py" --out "$CAP/c1_userns_syspy.json"

# ---- §3 item 2: Yama ptrace_scope >= 1 ---------------------------------------------------------------
run_step c2_ptrace "$VENV" "$SCRIPTS/probe_ptrace.py" --out "$CAP/c2_ptrace.json"

# ---- §3 item 3 / T1 §6.1: delegated cgroup v2 subtree with cgroup.kill, 8G / swap 0 --------------------
run_step c3_cgroup systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  "$VENV" "$SCRIPTS/probe_cgroup.py" --repo "$REPO" \
  --out "$CAP/c3_cgroup.json" --text "$CAP/c3_cgroup.txt"

# ---- §3 item 4: non-root euid + interpreter sys.path hard check (both new envs + system python) ------
run_step c4_interp "$VENV" "$SCRIPTS/probe_interp.py" --repo "$REPO" --base "$BASE" \
  --out "$CAP/c4_interp.json" --text "$CAP/c4_interp.txt"

# ---- §3 item 5: real sandboxed isolated smoke, effective:true ----------------------------------------
run_step c5_smoke systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  bash -c "CG=\$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
           exec \"$VENV\" \"$SCRIPTS/probe_smoke.py\" --repo \"$REPO\" --base \"$BASE\" \
             --out \"$CAP/c5_smoke.json\" --tag g0_smoke --interpreter \"$VENV\""

"$VENV" - "$CAP/c5_smoke.json" "$CAP/records/g0_smoke" <<'PYEOF'
import json, shutil, sys
from pathlib import Path
rec = json.loads(Path(sys.argv[1]).read_text())
run_dir, out = Path(rec["run_dir"]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
for name in ("run_record.json", "run.log", "result_channel.txt"):
    if (run_dir / name).is_file():
        shutil.copyfile(run_dir / name, out / name)
print("copied", out, sorted(p.name for p in out.iterdir()))
PYEOF

# ---- §3 item 6: GPU smoke with the sandbox on (torch312), exclusive GPU (flock lease + scope) ---------
run_step c6_gpu_smoke bash "$SCRIPTS/run_gpu_smoke.sh"

# ---- T1 §6.5 / §6.4: jax312 GPU smoke (Breakout env) and CPU-only houseprice beside a GPU node --------
run_step c6b_jax_gpu_smoke bash "$SCRIPTS/run_jax_smoke.sh"
run_step c6c_cpu_gpu bash "$SCRIPTS/run_cpu_gpu.sh"

# ---- supplementary: the unit's own isolation test file at the pin (record only) ----------------------
run_step pytest_isolation systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  bash -c "CG=\$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
           export PYTHONPATH=\"$REPO/src:$REPO\"; cd \"$REPO\"; \
           timeout 900 \"$VENV\" -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider"
"$VENV" - "$CAP/logs/pytest_isolation.log" "$CAP/pytest_isolation.json" <<'PYEOF'
import json, re, sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(errors="replace")
tail = log[-6000:]
counts = {}
for key in ("passed", "failed", "skipped", "deselected", "error"):
    m = re.search(r"(\d+) " + key, tail)
    if m:
        counts[key] = int(m.group(1))
m = re.search(r"--- pytest_isolation rc=(\d+)", tail)
Path(sys.argv[2]).write_text(json.dumps({"rc": int(m.group(1)) if m else None, "counts": counts,
                                         "tail": tail[-2500:]}, indent=2) + "\n")
PYEOF

# ---- §3 item 7: end state, GPU after, leftovers, disk, host/kernel, versions, hashes -----------------
run_step c7_final "$VENV" "$SCRIPTS/probe_final.py" --repo "$REPO" --base "$BASE" \
  --captures "$CAP" --out "$CAP/c7_final.json" --text "$CAP/c7_final.txt" \
  --gpu-before "$CAP/c6_gpu_smoke.json"
nvidia-smi > "$CAP/gpu_state_after.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_after_all.txt" 2>&1
{
  echo "=== harness pin after $(date -u +%FT%TZ)"
  echo "head=$(git -C "$REPO" rev-parse HEAD)"
  echo "status_porcelain_start"
  git -C "$REPO" status --porcelain
  echo "status_porcelain_end"
} > "$CAP/harness_pin_after.txt" 2>&1

# ---- summary + scripts copy + SHA256SUMS -------------------------------------------------------------
run_step summarize "$VENV" "$SCRIPTS/summarize.py" --captures "$CAP" --repo "$REPO" --t1 "$T1"
mkdir -p "$CAP/scripts"
cp -a "$SCRIPTS"/. "$CAP/scripts"/
cp "$REPO"/src/autoresearch/trackg/isolation.py "$CAP/scripts/unit_isolation.py"
cp "$REPO"/src/autoresearch/trackg/runner.py "$CAP/scripts/unit_runner.py"
cp "$REPO"/tests/trackg/isolated_fixture.py "$CAP/scripts/unit_isolated_fixture.py"
cp "$REPO"/src/autoresearch/trackg/gpu_identity.py "$CAP/scripts/unit_gpu_identity.py"
cp "$REPO"/src/autoresearch/trackg/noise_floor.py "$CAP/scripts/unit_noise_floor.py"
( cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
( cd "$CAP" && sha256sum SHA256SUMS ) >> "$CAP/logs/summarize.log" 2>&1

echo "=== R1-T1-HOST-TASL TASL-2 pre-launch host check end $(date -u +%FT%TZ)"
cat "$CAP/SUMMARY.txt"
exit 0
