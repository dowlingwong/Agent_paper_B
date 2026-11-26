#!/bin/bash
# TASL-2 host check at harness pin 2d09f9a9 for the autoresearch G.1b spec (procedure
# TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md): phase A = sections 0-3 (preflight, the second harness checkout,
# the node pins, the ar-cond7a environment).  A STOP in section 3 ends this run: sections 4-5 are NOT started.
# ENGINEERING_ONLY.  Nothing is deleted, committed or pushed; TASL-7, HTCondor and deepthought are not touched.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122
T1=/home/dowling/r1_tracks/t1_tasl
REPO=$T1/harness_ar
SEVEN=$T1/harness
VENV=/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python
UV=/home/dowling/.local/bin/uv
PIN=2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
SEVEN_PIN=c025f89aeafc2199bf3487b4bcaa16678273c702
CAP="$BASE/captures"
SCRIPTS="$BASE/scripts"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export PYTHONDONTWRITEBYTECODE=1
export LC_ALL=C
mkdir -p "$CAP/logs" "$BASE/work" "$BASE/records" "$CAP/scripts"
cd "$BASE" || exit 2
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "$STAMP" > "$CAP/stamp_utc.txt"
: > "$CAP/step_results.txt"
: > "$CAP/stop_items.txt"

run_step() {
  local name="$1"; shift
  local logf="$CAP/logs/$name.log"
  { echo "=== $name start $(date -u +%FT%TZ)"; printf 'cmd:'; printf ' %q' "$@"; echo; "$@"; } >"$logf" 2>&1
  local rc=$?
  echo "--- $name rc=$rc" >>"$logf"
  echo "$name rc=$rc" | tee -a "$CAP/step_results.txt"
  return $rc
}

stop_item() {
  echo "$*" | tee -a "$CAP/stop_items.txt"
}

echo "=== TASL-2 AR-pin host check start $STAMP host=$(hostname) euid=$(id -u) base=$BASE repo=$REPO pin=$PIN"
"$VENV" -VV; /usr/bin/python3 -VV; "$UV" --version

# ---- 0. preflight facts ---------------------------------------------------------------------------------
run_step host_facts taskset -c 16-31 "$VENV" "$SCRIPTS/probe_host.py" --repo "$REPO" --seven "$SEVEN" \
  --base "$BASE" --out "$CAP/host_facts.json" --text "$CAP/host_facts.txt"
nvidia-smi -L > "$CAP/nvidia_smi_L.txt" 2>&1
nvidia-smi > "$CAP/gpu_state_before.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_before_all.txt" 2>&1
{
  echo "=== lease test $(date -u +%FT%TZ) (flock -n, no write to the lease log)"
  exec 9>"$HOME/r1_locks/gpu0.lock"
  if flock -n 9; then echo "lease_free"; else echo "lease_HELD"; fi
  flock -u 9
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
} > "$CAP/lease_status_pre.txt" 2>&1
{
  echo "=== seven-node checkout before $(date -u +%FT%TZ)"
  echo "path=$SEVEN"
  echo "head=$(git -C "$SEVEN" rev-parse HEAD 2>&1)"
  echo "expected=$SEVEN_PIN"
  echo "symbolic_ref=$(git -C "$SEVEN" symbolic-ref -q HEAD 2>&1; echo rc=$?)"
  echo "status_porcelain_start"
  git -C "$SEVEN" status --porcelain 2>&1
  echo "status_porcelain_end"
  echo "status_untracked_all_start"
  git -C "$SEVEN" status --porcelain --untracked-files=all 2>&1
  echo "status_untracked_all_end"
  echo "stash_list_start"
  git -C "$SEVEN" stash list 2>&1
  echo "stash_list_end"
  echo "log_oneline_3"
  git -C "$SEVEN" log --oneline -3 2>&1
} > "$CAP/seven_node_before.txt" 2>&1
{
  echo "=== pre-existing state $(date -u +%FT%TZ)"
  echo "base_exists=$(test -e "$BASE" && echo yes || echo no)"
  echo "harness_ar_exists=$(test -e "$REPO" && echo yes || echo no)"
  echo "ar_data_exists=$(test -e "$T1/data/autoresearch_fixedtokens" && echo yes || echo no)"
  echo "data_listing:"; ls -la "$T1/data" 2>&1
  echo "t1_tasl_listing:"; ls -la "$T1" 2>&1
  echo "r1_engineering_listing:"; ls -la /home/dowling/r1_engineering 2>&1
  echo "running_jobs (t1_tasl_node|g1b|g4-|noise_floor|ar_worker):"
  ps -u "$(id -u)" -o pid,etime,cmd --no-headers 2>/dev/null | grep -Ei \
    "t1_tasl_node|g1b|g4-|noise_floor|run_g1b|ar_worker" | grep -v grep || true
} > "$CAP/pre_existing_state.txt" 2>&1
{
  echo "=== attempt-1 archive / lease log (stat only) $(date -u +%FT%TZ)"
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/p3a_operator_20261027 2>&1
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl 2>&1
} > "$CAP/attempt1_stat_before.txt" 2>&1

# gate: disk and lease before any host work
DF_FREE_GIB=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
echo "disk_free_gib=$DF_FREE_GIB" >> "$CAP/lease_status_pre.txt"
if [ "$DF_FREE_GIB" -lt 20 ]; then stop_item "STOP: disk on / free ${DF_FREE_GIB} GiB < 20 GiB"; fi
if grep -q "lease_HELD" "$CAP/lease_status_pre.txt"; then
  stop_item "STOP: ~/r1_locks/gpu0.lock is held (a T1 job? wait; never stop it)"
fi

# ---- 1. the second harness checkout at the pin ----------------------------------------------------------
if [ -e "$REPO" ]; then
  ASIDE="$T1/_to_delete/harness_ar_${STAMP}"
  mkdir -p "$T1/_to_delete"
  mv "$REPO" "$ASIDE" && echo "moved aside: $REPO -> $ASIDE" > "$CAP/harness_ar_moved_aside.txt"
fi
run_step step1_clone git clone --no-checkout https://github.com/dowlingwong/autoresearch_harness.git "$REPO"
GIT_LS_REMOTE="$(git ls-remote https://github.com/dowlingwong/autoresearch_harness.git mac-trackg-t1-ar-20261121 2>&1)"
printf '%s\n' "$GIT_LS_REMOTE" > "$CAP/step1_git_ls_remote.txt"
if ! printf '%s' "$GIT_LS_REMOTE" | grep -q "^$PIN[[:space:]]"; then
  stop_item "STOP: GitHub branch mac-trackg-t1-ar-20261121 does not resolve to $PIN (ls-remote: $GIT_LS_REMOTE)"
fi
run_step step1_fetch git -C "$REPO" fetch origin mac-trackg-t1-ar-20261121
run_step step1_checkout git -C "$REPO" checkout --detach "$PIN"
{
  echo "=== step 1 checks $(date -u +%FT%TZ)"
  echo "head=$(git -C "$REPO" rev-parse HEAD)"
  echo "expected_head=$PIN"
  echo "head_matches=$(test "$(git -C "$REPO" rev-parse HEAD)" = "$PIN" && echo yes || echo no)"
  echo "symbolic_ref_rc=$(git -C "$REPO" symbolic-ref -q HEAD >/dev/null 2>&1; echo $?)"
  echo "status_porcelain_untracked_all_start"
  git -C "$REPO" status --porcelain --untracked-files=all
  echo "status_porcelain_untracked_all_end"
  git -C "$REPO" merge-base --is-ancestor "$SEVEN_PIN" HEAD; echo "ancestor_c025f89a_rc=$?"
  git -C "$REPO" log --oneline -3
  git -C "$REPO" remote -v
  echo "origin_branch=$(git -C "$REPO" rev-parse origin/mac-trackg-t1-ar-20261121 2>&1)"
  echo "worktree_list:"; git -C "$REPO" worktree list
} > "$CAP/harness_ar_pin.txt" 2>&1
{
  echo "=== seven-node checkout after step 1 $(date -u +%FT%TZ)"
  echo "head=$(git -C "$SEVEN" rev-parse HEAD)"
  echo "status_porcelain_start"
  git -C "$SEVEN" status --porcelain
  echo "status_porcelain_end"
} > "$CAP/seven_node_after_step1.txt" 2>&1
HEAD_OK=$(grep -c "^head_matches=yes$" "$CAP/harness_ar_pin.txt")
if [ "$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" != "$PIN" ]; then
  stop_item "STOP: harness_ar HEAD is not $PIN"
fi
if ! git -C "$REPO" merge-base --is-ancestor "$SEVEN_PIN" HEAD; then
  stop_item "STOP: $SEVEN_PIN is not an ancestor of harness_ar HEAD"
fi
STATUS_ALL="$(git -C "$REPO" status --porcelain --untracked-files=all)"
if [ -n "$STATUS_ALL" ]; then
  stop_item "STOP: harness_ar is not clean after checkout: $STATUS_ALL"
fi
if [ "$(git -C "$SEVEN" rev-parse HEAD)" != "$SEVEN_PIN" ]; then
  stop_item "STOP: the seven-node checkout is not at $SEVEN_PIN"
fi
SEVEN_TRACKED_DIRTY="$(git -C "$SEVEN" status --porcelain --untracked-files=no)"
if [ -n "$SEVEN_TRACKED_DIRTY" ]; then
  stop_item "STOP: the seven-node checkout has tracked changes: $SEVEN_TRACKED_DIRTY"
fi

# ---- 2. node pins at the pin (ar-cond7a, PYTHONPATH=harness_ar/src) -------------------------------------
run_step step2_node_pins env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/node_pins.py" \
  --root "$REPO" --out "$CAP/node_pins.json" --text "$CAP/node_pins.txt"
STEP2_RC=$?

# ---- 3. the environment ar-cond7a ----------------------------------------------------------------------
run_step env_uv taskset -c 16-31 "$UV" --version
run_step env_freeze taskset -c 16-31 "$UV" pip freeze --python "$VENV"
cp "$CAP/logs/env_freeze.log" "$CAP/env_freeze_raw.log" 2>/dev/null
run_step step3_env_check env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/env_check.py" \
  --freeze "$BASE/work/committed/ar-cond7a.freeze.txt" --out "$CAP/env_check.json" \
  --text "$CAP/env_check.txt" --freeze-out "$CAP/env_freeze_uv.txt"
STEP3_RC=$?

# ---- STOP gate ------------------------------------------------------------------------------------------
STEP2_PASS=$(grep -c '"condition_2_pass": true' "$CAP/node_pins.json" 2>/dev/null || true)
STEP3_PASS=$(grep -c '"condition_3_pass": true' "$CAP/env_check.json" 2>/dev/null || true)
[ "$STEP2_RC" -ne 0 ] && stop_item "STOP: node pins differ from section 2 (see node_pins.txt)"
[ "$STEP3_RC" -ne 0 ] && stop_item "STOP: the ar-cond7a freeze or Python differs from section 3 (see env_check.txt)"

if [ -s "$CAP/stop_items.txt" ]; then
  echo "=== STOP: phase A ended before section 4; sections 4-5 were not started ==="
  cat "$CAP/stop_items.txt"
  taskset -c 16-31 "$VENV" - "$BASE" "$CAP" <<'PYEOF'
import json, sys, time
from pathlib import Path
base, cap = Path(sys.argv[1]), Path(sys.argv[2])
def load(name, default=None):
    try:
        return json.loads((cap / name).read_text())
    except (OSError, ValueError):
        return default
node, env, host = load("node_pins.json", {}), load("env_check.json", {}), load("host_facts.json", {})
stops = [line for line in (cap / "stop_items.txt").read_text().splitlines() if line.strip()]
summary = {
    "schema": "tasl2_ar_pin_hostcheck_summary/v1",
    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "host": "TASL-2", "pin": "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe",
    "seven_node_pin": "c025f89aeafc2199bf3487b4bcaa16678273c702",
    "engine": "deepseek-harness agent ar-pin-hostcheck",
    "scope": "phase A: procedure sections 0-3 (sections 4-5 not started because of a STOP)",
    "verdict": "FAIL / STOP",
    "stop_items": stops,
    "checkout": {"head": "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe",
                 "node_pins_condition": node.get("condition_2_pass"),
                 "pins_got": node.get("got"), "pins_checks": node.get("checks")},
    "environment": {"condition": env.get("condition_3_pass"), "checks": env.get("checks"),
                    "python": (env.get("python") or {}).get("version"),
                    "uv": (env.get("uv") or {}).get("version"),
                    "freeze_sha256": (env.get("freeze") or {}).get("sha256_raw"),
                    "freeze_lines": (env.get("freeze") or {}).get("lines"),
                    "readlink_f": env.get("readlink_f_venv")},
    "host_facts_present": bool(host),
    "sections_not_started": ["4 data", "5 C1-C7", "supplementary pytest", "AST CUDA-IPC scan", "6 binding record"],
}
(cap / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
lines = ["TASL-2 AR-pin host check — phase A (sections 0-3)", f"utc={summary['utc']} pin={summary['pin']}",
         f"verdict={summary['verdict']}", "STOP items:"]
lines += ["  " + s for s in stops]
ni, en = summary["checkout"], summary["environment"]
lines += [f"node pins condition_2_pass={ni['node_pins_condition']}",
          f"pins_got={json.dumps(ni['pins_got'], sort_keys=True)}",
          f"env condition_3_pass={en['condition']}",
          f"env_checks={json.dumps(en['checks'], sort_keys=True)}",
          f"python={en['python']} uv={en['uv']} freeze_sha256={en['freeze_sha256']} freeze_lines={en['freeze_lines']}",
          "sections 4-5 not started (STOP)."]
(cap / "SUMMARY.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
PYEOF
  cp -a "$SCRIPTS"/. "$CAP/scripts/"
  ( cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
  ( cd "$CAP" && sha256sum SHA256SUMS ) > "$BASE/SHA256SUMS.sha256"
  echo "captures_sha256sums_file=$(cat "$BASE/SHA256SUMS.sha256")"
  echo "=== TASL-2 AR-pin host check phase A end (STOP) $(date -u +%FT%TZ)"
  exit 10
fi

echo "=== phase A PASS (checkout, pins, env); phase B (sections 4-5) not run by this script ==="
cp -a "$SCRIPTS"/. "$CAP/scripts/"
( cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
( cd "$CAP" && sha256sum SHA256SUMS ) > "$BASE/SHA256SUMS.sha256"
echo "=== TASL-2 AR-pin host check phase A end $(date -u +%FT%TZ)"
exit 0
