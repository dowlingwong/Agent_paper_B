#!/bin/bash
# TASL-2 AR-pin host check, rerun after the authorised R1-G1B-AR-PY option-A fix, at harness pin 2d09f9a9 for
# the autoresearch G.1b spec.  Procedure: docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md
# sections 1-6 (preflight included).  ENGINEERING_ONLY.  Nothing is deleted, committed or pushed; TASL-7,
# HTCondor and deepthought are not touched; the Track P attempt-1 archive/lease log are stat-ed only.  The
# seven-node checkout is never modified.  The GPU is used only in C6, under the exclusive flock lease, by the
# ar-cond7a interpreter, with no lease-log write and no foreign compute.
set -uo pipefail
umask 077

TOP=/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122
BASE=$TOP/rerun_after_ar_py_optionA_20261122
T1=/home/dowling/r1_tracks/t1_tasl
REPO=$T1/harness_ar
SEVEN=$T1/harness
VENV=/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python
UV=/home/dowling/.local/bin/uv
PIN=2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
SEVEN_PIN=c025f89aeafc2199bf3487b4bcaa16678273c702
AR_DATA=$T1/data/autoresearch_fixedtokens
LEAD=/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122
CAP="$BASE/captures"
SCRIPTS="$BASE/scripts"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
export PYTHONDONTWRITEBYTECODE=1
export LC_ALL=C
mkdir -p "$CAP/logs" "$CAP/scripts" "$CAP/records" "$BASE/work" "$BASE/records" "$BASE/logs"
cd "$BASE" || exit 2
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "$STAMP" > "$CAP/stamp_utc.txt"
: > "$CAP/step_results.txt"
: > "$CAP/stop_items.txt"

run_step() {
  local name="$1"; shift
  local logf="$CAP/logs/$name.log"
  { echo "=== $name start $(date -u +%FT%TZ)"; printf 'cmd:'; printf ' %q' "$@"; echo; "$@"; } \
    >"$logf" 2>&1
  local rc=$?
  echo "--- $name rc=$rc end $(date -u +%FT%TZ)" >>"$logf"
  echo "$name rc=$rc" | tee -a "$CAP/step_results.txt"
  return $rc
}

stop_item() {
  echo "$*" | tee -a "$CAP/stop_items.txt"
}

stopped() {
  [ -s "$CAP/stop_items.txt" ]
}

json_flag() {
  # dotted key path, e.g. condition_3_pass or checks.python_3_12_15
  "$VENV" -c 'import json,sys
try:
    cur = json.load(open(sys.argv[1]))
except Exception:
    print("false"); raise SystemExit(0)
for part in sys.argv[2].split("."):
    cur = cur.get(part) if isinstance(cur, dict) else None
print(str(bool(cur)).lower())' "$1" "$2" 2>/dev/null
}

finalize() {
  local rc="$1"
  # The capture set is hashed last.  Nothing inside $CAP may be written after the digest is taken, and the
  # digest's own sha256 is kept outside the set ($BASE/SHA256SUMS.sha256) so the set cannot refer to itself.
  cp -a "$SCRIPTS"/. "$CAP/scripts/"
  ( cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
  ( cd "$CAP" && sha256sum SHA256SUMS ) > "$BASE/SHA256SUMS.sha256"
  ( cd "$CAP" && sha256sum -c SHA256SUMS ) > "$BASE/logs/sha256sums_verify.log" 2>&1
  local vrc=$?
  echo "captures_sha256sums_file=$(cat "$BASE/SHA256SUMS.sha256")"
  echo "captures_file_count=$(cd "$CAP" && find . -type f | wc -l)"
  echo "sha256sums_verify_rc=$vrc"
  echo "=== TASL-2 AR-pin host check end (exit $rc) $(date -u +%FT%TZ)"
  exit "$rc"
}

finish() {
  local rc="$1" reason="$2"
  [ "$rc" -ne 0 ] && stop_item "STOP: $reason"
  echo "=== STOP: $reason ==="
  cat "$CAP/stop_items.txt"
  if [ ! -s "$CAP/SUMMARY.json" ]; then
    run_step summarize env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/summarize.py" \
      --captures "$CAP" --base "$BASE" || true
  fi
  finalize "$rc"
}

echo "=== TASL-2 AR-pin host check (rerun after R1-G1B-AR-PY option A) start $STAMP host=$(hostname) euid=$(id -u)"
echo "base=$BASE repo=$REPO pin=$PIN"
"$VENV" -VV
/usr/bin/python3 -VV
"$UV" --version

# =====================================================================================================
# section 0: preflight facts (read-only)
# =====================================================================================================
run_step host_facts taskset -c 16-31 "$VENV" "$SCRIPTS/probe_host.py" --repo "$REPO" --seven "$SEVEN" \
  --base "$BASE" --out "$CAP/host_facts.json" --text "$CAP/host_facts.txt"
[ $? -ne 0 ] && stop_item "STOP: the preflight facts probe failed (host_facts)"
nvidia-smi -L > "$CAP/nvidia_smi_L.txt" 2>&1
nvidia-smi > "$CAP/gpu_state_before.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_before_all.txt" 2>&1
{
  echo "=== lease test $(date -u +%FT%TZ) (flock -n, no write to the lease log)"
  exec 9>"$HOME/r1_locks/gpu0.lock"
  if flock -n 9; then echo "lease_free"; else echo "lease_HELD"; fi
  flock -u 9
  exec 9>&-
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_log_untouched=/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl (stat only)"
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
  echo "base_top=$TOP"
  echo "this_base=$BASE"
  echo "harness_ar_exists=$(test -e "$REPO" && echo yes || echo no)"
  echo "ar_data_exists=$(test -e "$AR_DATA" && echo yes || echo no)"
  echo "data_listing:"; ls -la "$T1/data" 2>&1
  echo "t1_tasl_listing:"; ls -la "$T1" 2>&1
  echo "r1_engineering_listing:"; ls -la /home/dowling/r1_engineering 2>&1
  echo "running_jobs (t1_tasl_node|g1b|g4-|noise_floor|ar_worker|gpu_probe):"
  ps -u "$(id -u)" -o pid,etime,cmd --no-headers 2>/dev/null | grep -Ei \
    "t1_tasl_node|g1b|g4-|noise_floor|run_g1b|ar_worker|gpu_probe" | grep -v grep || true
} > "$CAP/pre_existing_state.txt" 2>&1
{
  echo "=== attempt-1 archive / lease log (stat only) $(date -u +%FT%TZ)"
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/p3a_operator_20261027 2>&1
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl 2>&1
} > "$CAP/attempt1_stat_before.txt" 2>&1
# the lead's authorised option-A repoint evidence: fetched, verified and kept with the captures
mkdir -p "$CAP/lead_repoint_evidence"
cp "$LEAD/captures/symlinks_before.txt" "$LEAD/captures/symlinks_after.txt" "$CAP/lead_repoint_evidence/" 2>&1
sha256sum "$LEAD/SHA256SUMS" > "$CAP/lead_repoint_evidence/lead_SHA256SUMS.sha256" 2>&1
( cd "$LEAD" && sha256sum -c SHA256SUMS ) > "$CAP/lead_repoint_evidence/lead_SHA256SUMS_verify.txt" 2>&1
echo "lead_SHA256SUMS_verify_rc=$?" >> "$CAP/lead_repoint_evidence/lead_SHA256SUMS_verify.txt"

DF_FREE_GIB=$(df --output=avail -BG / | tail -1 | tr -dc '0-9')
echo "disk_free_gib=$DF_FREE_GIB" >> "$CAP/lease_status_pre.txt"
[ "$DF_FREE_GIB" -lt 20 ] && stop_item "STOP: disk on / free ${DF_FREE_GIB} GiB < 20 GiB"
grep -q "lease_HELD" "$CAP/lease_status_pre.txt" && \
  stop_item "STOP: ~/r1_locks/gpu0.lock is held (a T1 job? wait; never stop it)"
grep -q "lease_free" "$CAP/lease_status_pre.txt" || \
  stop_item "STOP: the GPU lease state could not be read as free"
stopped && finish 10 "section 0 preflight gate"

# =====================================================================================================
# section 1: the second harness checkout at the pin (made by the earlier attempt of this same procedure;
# re-verified here -- the four recorded conditions are checked afresh)
# =====================================================================================================
{
  echo "=== section 1 checkout $(date -u +%FT%TZ)"
  echo "checkout_provenance=separate clone from GitHub made by the 22 Nov earlier attempt of this same procedure; re-verified here"
  echo "path=$REPO"
  echo "head=$(git -C "$REPO" rev-parse HEAD 2>&1)"
  echo "expected_head=$PIN"
  echo "head_matches=$(test "$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" = "$PIN" && echo yes || echo no)"
  echo "symbolic_ref_rc=$(git -C "$REPO" symbolic-ref -q HEAD >/dev/null 2>&1; echo $?)"
  echo "status_porcelain_untracked_all_start"
  git -C "$REPO" status --porcelain --untracked-files=all 2>&1
  echo "status_porcelain_untracked_all_end"
  git -C "$REPO" merge-base --is-ancestor "$SEVEN_PIN" HEAD; echo "ancestor_c025f89a_rc=$?"
  git -C "$REPO" log --oneline -3 2>&1
  git -C "$REPO" remote -v 2>&1
  echo "origin_branch=$(git -C "$REPO" rev-parse origin/mac-trackg-t1-ar-20261121 2>&1)"
  echo "worktree_list:"
  git -C "$REPO" worktree list 2>&1
  echo "stash_list:"
  git -C "$REPO" stash list 2>&1
} > "$CAP/harness_ar_pin.txt" 2>&1
{
  echo "=== GitHub branch ls-remote $(date -u +%FT%TZ)"
  git ls-remote https://github.com/dowlingwong/autoresearch_harness.git mac-trackg-t1-ar-20261121 2>&1
} > "$CAP/step1_git_ls_remote.txt" 2>&1
{
  echo "=== seven-node checkout after section 1 $(date -u +%FT%TZ)"
  echo "head=$(git -C "$SEVEN" rev-parse HEAD 2>&1)"
  echo "status_porcelain_start"
  git -C "$SEVEN" status --porcelain 2>&1
  echo "status_porcelain_end"
  echo "status_untracked_all_start"
  git -C "$SEVEN" status --porcelain --untracked-files=all 2>&1
  echo "status_untracked_all_end"
} > "$CAP/seven_node_after_step1.txt" 2>&1

[ "$(git -C "$REPO" rev-parse HEAD 2>/dev/null)" != "$PIN" ] && \
  stop_item "STOP: harness_ar HEAD is not $PIN"
git -C "$REPO" merge-base --is-ancestor "$SEVEN_PIN" HEAD || \
  stop_item "STOP: $SEVEN_PIN is not an ancestor of harness_ar HEAD"
STATUS_ALL="$(git -C "$REPO" status --porcelain --untracked-files=all)"
[ -n "$STATUS_ALL" ] && stop_item "STOP: harness_ar is not clean after checkout: $STATUS_ALL"
[ "$(git -C "$SEVEN" rev-parse HEAD)" != "$SEVEN_PIN" ] && \
  stop_item "STOP: the seven-node checkout is not at $SEVEN_PIN"
SEVEN_TRACKED_DIRTY="$(git -C "$SEVEN" status --porcelain --untracked-files=no)"
[ -n "$SEVEN_TRACKED_DIRTY" ] && \
  stop_item "STOP: the seven-node checkout has tracked changes: $SEVEN_TRACKED_DIRTY"
grep -q "^$PIN[[:space:]]" "$CAP/step1_git_ls_remote.txt" || \
  stop_item "STOP: GitHub branch mac-trackg-t1-ar-20261121 does not resolve to $PIN"
stopped && finish 10 "section 1 checkout gate"

# =====================================================================================================
# section 2: node pins at the pin (ar-cond7a, PYTHONPATH=harness_ar/src)
# =====================================================================================================
run_step step2_node_pins env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/node_pins.py" \
  --root "$REPO" --out "$CAP/node_pins.json" --text "$CAP/node_pins.txt"
[ $? -ne 0 ] && stop_item "STOP: node pins differ from section 2 (see node_pins.txt)"
[ "$(json_flag "$CAP/node_pins.json" condition_2_pass)" != "true" ] && \
  stop_item "STOP: node pins differ from section 2 (condition_2_pass false)"
[ -s "$CAP/stop_items.txt" ] && finish 10 "section 2 node pins gate"

# =====================================================================================================
# section 3: the environment ar-cond7a (read-only; nothing installed, upgraded or copied)
# =====================================================================================================
run_step env_uv taskset -c 16-31 "$UV" --version
run_step env_freeze taskset -c 16-31 "$UV" pip freeze --python "$VENV"
cp "$CAP/logs/env_freeze.log" "$CAP/env_freeze_raw.log" 2>/dev/null
run_step venv_evidence_before env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" \
  "$SCRIPTS/venv_evidence.py" --out "$CAP/venv_evidence_before.json" \
  --text "$CAP/venv_evidence_before.txt" --tag before
run_step step3_env_check env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/env_check.py" \
  --freeze "$BASE/work/committed/ar-cond7a.freeze.txt" --out "$CAP/env_check.json" \
  --text "$CAP/env_check.txt" --freeze-out "$CAP/env_freeze_uv.txt"
[ $? -ne 0 ] && stop_item "STOP: the ar-cond7a freeze or Python differs from section 3 (see env_check.txt)"
[ "$(json_flag "$CAP/env_check.json" condition_3_pass)" != "true" ] && \
  stop_item "STOP: the ar-cond7a freeze or Python differs from section 3 (condition_3_pass false)"
[ "$(json_flag "$CAP/venv_evidence_before.json" checks.python_3_12_15)" != "true" ] && \
  stop_item "STOP: venv evidence before does not show Python 3.12.15"
[ -s "$CAP/stop_items.txt" ] && finish 10 "section 3 environment gate"

echo "=== sections 0-3 PASS (preflight, checkout, pins, environment); proceeding to section 4 ==="

# =====================================================================================================
# section 4: data under the T1 layout, staged once (prepare_data is the node's own setup_command)
# =====================================================================================================
[ -e "$AR_DATA" ] && \
  echo "ar_data_exists_before_staging=yes (prepare_data will re-check and re-link only)" \
    >> "$CAP/pre_existing_state.txt"
run_step step4_prepare_data env \
  PATH=/home/dowling/r1_trackp/venvs/ar-cond7a/bin:/usr/local/bin:/usr/bin:/bin \
  AR_TRACKG_DATA_ROOT="$T1/data" HF_HOME="$T1/hf" \
  taskset -c 16-31 python3 "$REPO/nodes/autoresearch_fixedtokens/prepare_data.py" --out "$AR_DATA"
PREP_RC=$?
if [ "$PREP_RC" -ne 0 ]; then
  stop_item "STOP: prepare_data failed (rc=$PREP_RC; see logs/step4_prepare_data.log)"
else
  run_step step4_data_check env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" \
    "$SCRIPTS/step4_data_check.py" --repo "$REPO" --out "$CAP/step4_data_check.json" \
    --text "$CAP/step4_data_check.txt"
  [ $? -ne 0 ] && stop_item "STOP: the data manifest/link checks failed (see step4_data_check.txt)"
  [ "$(json_flag "$CAP/step4_data_check.json" condition_4_data_pass)" != "true" ] && \
    stop_item "STOP: the data manifest/link checks failed (condition_4_data_pass false)"
fi
[ -s "$CAP/stop_items.txt" ] && finish 10 "section 4 data gate"

echo "=== section 4 PASS (data staged at $AR_DATA); proceeding to section 5 C1-C7 ==="

# =====================================================================================================
# section 5: the seven host conditions at the pin (C1-C7).  A failure records the STOP and the remaining
# condition checks are skipped; the end state (C7) is still captured and the STOP report/summary written.
# =====================================================================================================
if ! stopped; then
  # C1: unprivileged user, mount, PID, network and cgroup namespaces
  run_step c1_userns_ar_cond7a taskset -c 16-31 "$VENV" "$SCRIPTS/probe_userns.py" \
    --out "$CAP/c1_userns_ar_cond7a.json"; C1A=$?
  run_step c1_userns_syspy taskset -c 16-31 /usr/bin/python3 "$SCRIPTS/probe_userns.py" \
    --out "$CAP/c1_userns_syspy.json"; C1B=$?
  if [ "$C1A" -ne 0 ] || [ "$C1B" -ne 0 ] || \
     [ "$(json_flag "$CAP/c1_userns_ar_cond7a.json" condition_1_pass)" != "true" ] || \
     [ "$(json_flag "$CAP/c1_userns_syspy.json" condition_1_pass)" != "true" ]; then
    stop_item "STOP: C1 failed (user/mount/PID/network/cgroup namespaces; see c1_userns_*.json)"
  fi
fi
if ! stopped; then
  # C2: Yama ptrace_scope >= 1
  run_step c2_ptrace taskset -c 16-31 "$VENV" "$SCRIPTS/probe_ptrace.py" --out "$CAP/c2_ptrace.json"
  [ $? -ne 0 ] && stop_item "STOP: C2 failed (ptrace_scope; see c2_ptrace.json)"
  [ "$(json_flag "$CAP/c2_ptrace.json" condition_2_pass)" != "true" ] && \
    stop_item "STOP: C2 failed (ptrace_scope; condition_2_pass false)"
fi
if ! stopped; then
  # C3: delegated cgroup v2 subtree with cgroup.kill (census scope 8G / swap 0)
  run_step c3_cgroup systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
    taskset -c 16-31 "$VENV" "$SCRIPTS/probe_cgroup.py" --repo "$REPO" \
    --out "$CAP/c3_cgroup.json" --text "$CAP/c3_cgroup.txt"
  [ $? -ne 0 ] && stop_item "STOP: C3 failed (delegated cgroup v2 / cgroup.kill; see c3_cgroup.txt)"
  [ "$(json_flag "$CAP/c3_cgroup.json" condition_3_pass)" != "true" ] && \
    stop_item "STOP: C3 failed (delegated cgroup v2 / cgroup.kill; condition_3_pass false)"
fi
if ! stopped; then
  # C4: not root; the interpreter's sys.path holds no home dir, runs tree or ancestor
  run_step c4_interp env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/probe_interp.py" \
    --repo "$REPO" --base "$BASE" --out "$CAP/c4_interp.json" --text "$CAP/c4_interp.txt"
  [ $? -ne 0 ] && stop_item "STOP: C4 failed (non-root / interpreter sys.path; see c4_interp.txt)"
  [ "$(json_flag "$CAP/c4_interp.json" condition_4_pass)" != "true" ] && \
    stop_item "STOP: C4 failed (non-root / interpreter sys.path; condition_4_pass false)"
fi
if ! stopped; then
  # C5: a real sandboxed smoke whose record shows effective: true
  run_step c5_smoke systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
    bash -c "CG=\$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
             export PYTHONDONTWRITEBYTECODE=1; \
             exec taskset -c 16-31 \"$VENV\" \"$SCRIPTS/probe_smoke.py\" --repo \"$REPO\" --base \"$BASE\" \
               --out \"$CAP/c5_smoke.json\" --tag ar_pin_smoke --interpreter \"$VENV\""
  [ $? -ne 0 ] && stop_item "STOP: C5 failed (sandboxed smoke; see c5_smoke.json)"
  [ "$(json_flag "$CAP/c5_smoke.json" condition_5_pass)" != "true" ] && \
    stop_item "STOP: C5 failed (sandboxed smoke; condition_5_pass false)"
  if [ -f "$CAP/c5_smoke.json" ]; then
    "$VENV" - "$CAP/c5_smoke.json" "$CAP/records/ar_pin_smoke" <<'PYEOF'
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
  fi
fi
if ! stopped; then
  # C6: GPU smoke with the sandbox on, under the exclusive lease, by full UUID
  run_step c6_gpu_smoke bash "$SCRIPTS/run_gpu_smoke.sh" "$BASE" "$REPO" "$VENV" "$CAP" "$SCRIPTS"
  [ $? -ne 0 ] && stop_item "STOP: C6 failed (GPU smoke under the lease; see c6_gpu_smoke.json)"
  [ "$(json_flag "$CAP/c6_gpu_smoke.json" condition_6_pass)" != "true" ] && \
    stop_item "STOP: C6 failed (GPU smoke; condition_6_pass false)"
fi

# supplementary (not a section 3 condition): the pin's own isolation test, in a delegated scope
if ! stopped; then
  run_step pytest_isolation systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
    bash -c "CG=\$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; \
             export PYTHONDONTWRITEBYTECODE=1; export PYTHONPATH=\"$REPO/src:$REPO\"; cd \"$REPO\"; \
             exec timeout 900 \"$VENV\" -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider"
  PYTEST_RC=$?
  "$VENV" - "$CAP/logs/pytest_isolation.log" "$CAP/pytest_isolation.json" "$PYTEST_RC" <<'PYEOF'
import json, re, sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(errors="replace")
tail = log[-8000:]
counts = {}
for key in ("passed", "failed", "skipped", "deselected", "error", "errors"):
    m = re.search(r"(\d+) " + key, tail)
    if m:
        counts[key] = int(m.group(1))
Path(sys.argv[2]).write_text(json.dumps({"rc": int(sys.argv[3]), "counts": counts,
                                         "tail": tail[-3000:]}, indent=2) + "\n")
print("pytest rc=" + sys.argv[3] + " counts=" + json.dumps(counts))
PYEOF
  # supplementary (not a section 3 condition): AST CUDA-IPC scan at the pin
  run_step ast_cuda_ipc_scan env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" \
    "$SCRIPTS/ast_cuda_ipc_scan.py" --node-dir "$REPO/nodes/autoresearch_fixedtokens" \
    --out "$CAP/ast_cuda_ipc_scan.json" --text "$CAP/ast_cuda_ipc_scan.txt"
  [ $? -ne 0 ] && stop_item "STOP: the AST CUDA-IPC scan found a call site in run_fixed_budget.py/ar_worker.py"
  [ "$(json_flag "$CAP/ast_cuda_ipc_scan.json" condition_scan_pass)" != "true" ] && \
    stop_item "STOP: the AST CUDA-IPC scan found a call site in run_fixed_budget.py/ar_worker.py"
fi

# =====================================================================================================
# C7: end state (captured even when an earlier condition failed, so the STOP report has its end state)
# =====================================================================================================
run_step c7_final env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/probe_final.py" \
  --repo "$REPO" --seven "$SEVEN" --base "$BASE" --captures "$CAP" \
  --out "$CAP/c7_final.json" --text "$CAP/c7_final.txt" --gpu-before "$CAP/c6_gpu_smoke.json"
[ $? -ne 0 ] && stop_item "STOP: C7 failed (end state; see c7_final.txt)"
[ "$(json_flag "$CAP/c7_final.json" condition_7_pass)" != "true" ] && \
  stop_item "STOP: C7 failed (end state; condition_7_pass false)"
nvidia-smi > "$CAP/gpu_state_after.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_after_all.txt" 2>&1
{
  echo "=== lease after $(date -u +%FT%TZ) (flock -n, no lease-log write)"
  exec 9>"$HOME/r1_locks/gpu0.lock"
  if flock -n 9; then echo "lease_free"; else echo "lease_HELD"; fi
  flock -u 9
  exec 9>&-
} > "$CAP/lease_status_post.txt" 2>&1
{
  echo "=== harness_ar pin after $(date -u +%FT%TZ)"
  echo "head=$(git -C "$REPO" rev-parse HEAD)"
  echo "status_porcelain_untracked_all_start"
  git -C "$REPO" status --porcelain --untracked-files=all
  echo "status_porcelain_untracked_all_end"
  echo "symbolic_ref_rc=$(git -C "$REPO" symbolic-ref -q HEAD >/dev/null 2>&1; echo $?)"
} > "$CAP/harness_ar_pin_after.txt" 2>&1
{
  echo "=== seven-node checkout after $(date -u +%FT%TZ)"
  echo "head=$(git -C "$SEVEN" rev-parse HEAD)"
  echo "status_porcelain_start"
  git -C "$SEVEN" status --porcelain
  echo "status_porcelain_end"
  echo "status_untracked_all_start"
  git -C "$SEVEN" status --porcelain --untracked-files=all
  echo "status_untracked_all_end"
  echo "stash_list_start"
  git -C "$SEVEN" stash list
  echo "stash_list_end"
} > "$CAP/seven_node_after.txt" 2>&1
{
  echo "=== attempt-1 archive / lease log after (stat only) $(date -u +%FT%TZ)"
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/p3a_operator_20261027 2>&1
  stat -c "%n %y %s" /home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl 2>&1
} > "$CAP/attempt1_stat_after.txt" 2>&1
run_step venv_evidence_after env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" \
  "$SCRIPTS/venv_evidence.py" --out "$CAP/venv_evidence_after.json" \
  --text "$CAP/venv_evidence_after.txt" --tag after
if [ -f "$CAP/venv_evidence_before.json" ] && [ -f "$CAP/venv_evidence_after.json" ]; then
  "$VENV" - "$CAP/venv_evidence_before.json" "$CAP/venv_evidence_after.json" \
    "$CAP/venv_unchanged.json" <<'PYEOF'
import json, sys
from pathlib import Path
before = json.loads(Path(sys.argv[1]).read_text())
after = json.loads(Path(sys.argv[2]).read_text())
keys = ("resolved_interpreter", "interpreter_sha256", "interpreter_bytes", "python_version",
        "freeze_sha256", "freeze_lines", "pyvenv_cfg_sha256")
checks = {key: before.get(key) == after.get(key) for key in keys}
checks["links_identical"] = before.get("links") == after.get("links")
doc = {"before_utc": before.get("utc"), "after_utc": after.get("utc"),
       "checks": checks, "unchanged": all(checks.values()),
       "before": {key: before.get(key) for key in keys},
       "after": {key: after.get(key) for key in keys}}
Path(sys.argv[3]).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
print("venv_unchanged=" + str(doc["unchanged"]))
PYEOF
  [ "$(json_flag "$CAP/venv_unchanged.json" unchanged)" != "true" ] && \
    stop_item "STOP: the ar-cond7a evidence before/after differs (the venv was touched)"
fi

# =====================================================================================================
# summary + capture set
# =====================================================================================================
run_step summarize env PYTHONPATH="$REPO/src" taskset -c 16-31 "$VENV" "$SCRIPTS/summarize.py" \
  --captures "$CAP" --base "$BASE"
VERDICT="$("$VENV" -c 'import json,sys; print(json.load(open(sys.argv[1]))["verdict"])' \
  "$CAP/SUMMARY.json" 2>/dev/null || true)"
echo "verdict=$VERDICT" >> "$CAP/step_results.txt"
if [ "$VERDICT" != "PASS" ]; then
  stop_item "STOP: the recorded verdict is not PASS"
  finish 10 "final verdict gate"
fi
echo "=== TASL-2 AR-pin host check PASS: C1-C7 all pass, supplementary checks recorded ==="
cat "$CAP/SUMMARY.txt"
finalize 0
