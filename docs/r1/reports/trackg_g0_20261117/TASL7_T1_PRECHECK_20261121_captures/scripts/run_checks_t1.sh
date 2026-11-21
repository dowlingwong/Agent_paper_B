#!/bin/bash
# R1-T1-HOST-TASL: the G.1b plan §6 host checks on TASL-7, at harness pin c025f89a, for the T1 launch
# (R1-T1-HOST-TASL / R1-TRACKG-AR-U2-TASL2).  ENGINEERING_ONLY.
#
# Runs the HARNESS_ISOLATION_20261117 §3 host conditions 1-7 at the T1 pin (the seven ``host_check_items``), plus
# the T1 environment binding (torch312/jax312 from the census freezes) and the jax312 GPU check.  One session,
# writes captures/, SUMMARY.{json,txt}, SHA256SUMS.  Nothing is deleted, committed or pushed; TASL-2 / the Track P
# attempt-1 archive and lease log / HTCondor and deepthought are untouched.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
REPO=/home/dowling/r1_tracks/t1_tasl/harness
VENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python
SYS=/usr/bin/python3
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
  { echo "=== $name start $(date -u +%FT%TZ)"; echo "cmd: $*"; "$@"; } >"$logf" 2>&1
  local rc=$?
  echo "--- $name rc=$rc" >>"$logf"
  echo "$name rc=$rc" | tee -a "$CAP/step_results.txt"
  return $rc
}

echo "=== R1-T1-HOST-TASL host check start $STAMP host=$(hostname) euid=$(id -u) base=$BASE repo=$REPO pin=$PIN"
"$VENV" -VV; "$SYS" -VV

# ---- E0: environment binding (uv 0.13.6, Python 3.12.16, torch312/jax312 freeze byte-equality) -----
run_step envs "$VENV" "$SCRIPTS/probe_envs.py" --base "$BASE" \
  --out "$CAP/c0_envs.json" --text "$CAP/c0_envs.txt"

# ---- A0: binding assertions (host, pin, clean tree, GPU full UUID, no compute app, ptrace, disk) -----
run_step assertions "$VENV" "$SCRIPTS/probe_assertions.py" --base "$BASE" --pin "$PIN" \
  --out "$CAP/c0_assertions.json" --text "$CAP/c0_assertions.txt"

# ---- C7 pre: read-only fingerprint of the Track P attempt-1 archive + lease log (before) -------------
run_step archive_before bash "$SCRIPTS/fingerprint_attempt1.sh" before

# ---- C7a: initial host/GPU/tool facts ---------------------------------------------------------------
run_step host_facts "$VENV" "$SCRIPTS/probe_host.py" --repo "$REPO" --base "$BASE" \
  --out "$CAP/host.json" --text "$CAP/host_facts.txt"
nvidia-smi > "$CAP/gpu_state_before.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_before_all.txt" 2>&1

# ---- C1: unprivileged user+mount+PID+network(+cgroup) namespaces ------------------------------------
run_step c1_userns_venv "$VENV" "$SCRIPTS/probe_userns.py" --out "$CAP/c1_userns_venv.json"
run_step c1_userns_syspy "$SYS" "$SCRIPTS/probe_userns.py" --out "$CAP/c1_userns_syspy.json"

# ---- C2: Yama ptrace_scope >= 1 ----------------------------------------------------------------------
run_step c2_ptrace "$VENV" "$SCRIPTS/probe_ptrace.py" --out "$CAP/c2_ptrace.json"

# ---- C3: delegated cgroup v2 subtree with cgroup.kill (systemd-run --user --scope, Delegate=yes) -----
run_step c3_cgroup systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  "$VENV" "$SCRIPTS/probe_cgroup.py" --repo "$REPO" \
  --out "$CAP/c3_cgroup.json" --text "$CAP/c3_cgroup.txt"

# ---- C4: non-root euid + interpreter sys.path hard check (system, torch312, jax312) ------------------
run_step c4_interp "$VENV" "$SCRIPTS/probe_interp.py" --repo "$REPO" --base "$BASE" \
  --out "$CAP/c4_interp.json" --text "$CAP/c4_interp.txt"

# ---- C5: real sandboxed isolated smoke, effective:true ----------------------------------------------
run_step c5_smoke systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  bash -c "export PYTHONDONTWRITEBYTECODE=1; CG=\$(cut -d: -f3 /proc/self/cgroup); \
           export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
           exec \"$VENV\" \"$SCRIPTS/probe_smoke.py\" --repo \"$REPO\" --base \"$BASE\" \
             --out \"$CAP/c5_smoke.json\" --tag g0_smoke --interpreter \"$VENV\""
"$VENV" - "$CAP/c5_smoke.json" "$CAP/records" <<'PYEOF'
import json, shutil, sys
from pathlib import Path
cap = json.loads(Path(sys.argv[1]).read_text())
run = Path(cap["run_dir"])
dst = Path(sys.argv[2]) / "g0_smoke"
dst.mkdir(parents=True, exist_ok=True)
for name in ("run_record.json", "run.log", "result_channel.txt"):
    if (run / name).exists():
        shutil.copyfile(run / name, dst / name)
print("copied g0_smoke records:", sorted(p.name for p in dst.iterdir()))
PYEOF

# ---- C6: GPU smoke with the sandbox on, exclusive GPU (flock lease + delegated scope) ----------------
run_step c6_gpu_smoke bash "$SCRIPTS/run_gpu_smoke.sh"

# ---- C6b: jax312 environment GPU (G.1b mlgym_breakout_minatar's env on TASL-7) -----------------------
# As the census environment stands (no CUDA toolkit in the freeze, no /usr/local/cuda symlink on TASL-7) JAX
# cannot find ptxas; the second step records the standard --xla_gpu_cuda_data_dir host adaptation.
run_step c6b_jax_gpu bash "$SCRIPTS/run_jax_gpu.sh"
run_step c6b_jax_gpu_xla_cuda_dir bash "$SCRIPTS/run_jax_gpu_fixed.sh"

# ---- B1 (G.4 precheck): one short proposer start bound to the Tailscale address only -----------------
run_step bind_test bash "$SCRIPTS/bind_test.sh"

# ---- supplementary: the unit's own isolation test file (record only) --------------------------------
run_step pytest_isolation systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  bash -c "export PYTHONDONTWRITEBYTECODE=1; CG=\$(cut -d: -f3 /proc/self/cgroup); \
           export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
           export PYTHONPATH=\"$REPO/src:$REPO\"; cd \"$REPO\"; \
           timeout 600 \"$VENV\" -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider"
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

# ---- C7: Track P attempt-1 archive/lease fingerprint (after) + comparison ---------------------------
run_step archive_after bash "$SCRIPTS/fingerprint_attempt1.sh" after
run_step archive_compare "$VENV" "$SCRIPTS/compare_attempt1.py" --captures "$CAP" \
  --out "$CAP/attempt1_compare.json" --text "$CAP/attempt1_compare.txt"

# ---- C7: end state, GPU after, leftovers, disk, host/kernel, versions, hashes ------------------------
run_step c7_final "$VENV" "$SCRIPTS/probe_final.py" --repo "$REPO" --base "$BASE" \
  --captures "$CAP" --out "$CAP/c7_final.json" --text "$CAP/c7_final.txt" \
  --gpu-before "$CAP/c6_gpu_smoke.json" --sums "$CAP/SHA256SUMS"
nvidia-smi > "$CAP/gpu_state_after.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_after_all.txt" 2>&1
[ -e "$CAP/gpu_leaselogs_after.txt" ] && diff -u "$CAP/gpu_leaselogs_before.txt" "$CAP/gpu_leaselogs_after.txt" \
  > "$CAP/gpu_leaselogs_diff.txt" 2>&1

# ---- summary + scripts copy + SHA256SUMS ------------------------------------------------------------
run_step summarize "$VENV" "$SCRIPTS/summarize.py" --captures "$CAP" --repo "$REPO"
mkdir -p "$CAP/scripts"
cp -a "$SCRIPTS"/. "$CAP/scripts"/
cp "$REPO"/src/autoresearch/trackg/isolation.py "$CAP/scripts/unit_isolation.py"
cp "$REPO"/src/autoresearch/trackg/runner.py "$CAP/scripts/unit_runner.py"
cp "$REPO"/src/autoresearch/trackg/node_lib/ar_isolated.py "$CAP/scripts/unit_ar_isolated.py"
cp "$REPO"/tests/trackg/isolated_fixture.py "$CAP/scripts/unit_isolated_fixture.py"
# SHA256SUMS must be the LAST write under captures/ (any file written after it would not be covered);
# the digest is printed to the orchestrator's stdout, which lives outside captures/.
( cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
echo "SHA256SUMS_sha256=$( cd "$CAP" && sha256sum SHA256SUMS )"

echo "=== R1-T1-HOST-TASL host check end $(date -u +%FT%TZ)"
cat "$CAP/SUMMARY.txt"
exit 0
