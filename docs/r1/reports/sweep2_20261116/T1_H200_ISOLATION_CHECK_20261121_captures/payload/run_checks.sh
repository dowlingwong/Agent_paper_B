#!/bin/bash
# R1-T1-HOST-H200: harness-isolation host-condition check inside the HTCondor container on one NEMO2 H200.
# ENGINEERING_ONLY.  Runs the probes in docs/r1/reports/HARNESS_ISOLATION_20261117.md §3 (+ §5.5 GPU smoke) and
# writes out/isolation_check.json.  Exit code 0 = the check completed (the verdict is in the JSON); 2 = payload
# problem (nothing measured).
set -uo pipefail
umask 077

JOB="$(pwd)"
OUT="$JOB/out"
BASE="$JOB/work"
mkdir -p "$OUT/logs" "$BASE" "$JOB/records"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
echo "$STAMP" > "$OUT/stamp_utc.txt"

echo "=== R1-T1-HOST-H200 isolation check start $STAMP host=$(hostname) u=$(id -u) iwd=$JOB"

# ---- payload ----------------------------------------------------------------------------------------
if [ ! -f "$JOB/isolation_payload.tar.gz" ]; then echo "PAYLOAD MISSING"; exit 2; fi
tar -xzf "$JOB/isolation_payload.tar.gz" -C "$JOB" || { echo "PAYLOAD UNPACK FAILED"; exit 2; }
PAY="$JOB/payload"
[ -f "$PAY/lib_iso.py" ] || { echo "PAYLOAD INCOMPLETE"; exit 2; }
REPO_OLD="$PAY/repo_68cdd1a"
REPO_FIX="$PAY/repo_5403392e"
[ -d "$REPO_OLD/src/autoresearch/trackg" ] || { echo "old repo missing"; exit 2; }
[ -d "$REPO_FIX/src/autoresearch/trackg" ] || { echo "fix repo missing"; exit 2; }

PY=""
for candidate in ${ISO_PYTHON:-} /opt/r1/envs/trackp/bin/python /opt/r1/envs/harness/bin/python /usr/bin/python3; do
  if [ -x "$candidate" ]; then PY="$candidate"; break; fi
done
[ -n "$PY" ] || { echo "NO PYTHON IN IMAGE"; exit 2; }
echo "driver_python=$PY ($($PY -VV 2>&1))"

run_step() {
  local name="$1"; shift
  local logf="$OUT/logs/$name.log"
  { echo "=== $name start $(date -u +%FT%TZ)"; echo "cmd: $*"; "$@"; } >"$logf" 2>&1
  local rc=$?
  echo "--- $name rc=$rc" >>"$logf"
  echo "$name rc=$rc" | tee -a "$OUT/step_results.txt"
  tail -n 4 "$logf" | sed 's/^/    /'
  return $rc
}

# ---- 0. facts about the container job itself --------------------------------------------------------
{
  echo "stamp=$STAMP host=$(hostname -f 2>/dev/null || hostname) iwd=$JOB uid=$(id -u) euid=$(id -ru) user=$(id -un)"
  echo "uname: $(uname -a)"
  echo "os-release:"; cat /etc/os-release 2>&1
  echo "python: $($PY -VV 2>&1)"
  echo "APPATAINER/CONTAINER env:"; env | grep -aiE 'APPTAINER|SINGULARITY|CONTAINER|CONDOR|CUDA_VISIBLE|NVIDIA_VISIBLE' | sort
  echo "nvidia devices:"; ls -l /dev/nvidia* 2>&1
  echo "driver:"; cat /proc/driver/nvidia/version 2>&1
  echo "/opt/r1/VERSIONS.txt:"; cat /opt/r1/VERSIONS.txt 2>&1
  echo "/proc/self/cgroup:"; cat /proc/self/cgroup 2>&1
  echo "cgroup controllers:"; cat /sys/fs/cgroup/cgroup.controllers 2>&1
  echo "cgroup subtree_control:"; cat /sys/fs/cgroup/cgroup.subtree_control 2>&1
  echo "/sys/fs/cgroup mount:"; grep ' /sys/fs/cgroup ' /proc/self/mountinfo 2>&1
  echo "/sys mount:"; grep ' /sys ' /proc/self/mountinfo 2>&1
  echo "sysctls yama/apparmor/userns:"
  cat /proc/sys/kernel/yama/ptrace_scope 2>&1
  cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>&1
  cat /proc/sys/kernel/unprivileged_userns_clone 2>&1
  cat /proc/sys/user/max_user_namespaces 2>&1
  echo "nvidia-smi -L:"; nvidia-smi -L 2>&1
  echo "job ad container/gpu lines:"
  if [ -r "${_CONDOR_JOB_AD:-}" ]; then
    grep -aiE '^(ContainerImage|ContainerImageSource|WantContainer|RequestGPUs|GPUsProvisioned|RequestCpus|RequestMemory|RequestDisk|RemoteJob|ImageSize|JobStartDate|Machine|Name )' "$_CONDOR_JOB_AD" 2>/dev/null | head -20
  fi
} >"$OUT/container_facts.txt" 2>&1
echo "container facts -> $OUT/container_facts.txt"

# ---- 1..5: host conditions (C2, C5, C3 userns, C1 cgroup) ------------------------------------------
run_step host_facts "$PY" "$PAY/probe_host.py" --repo "$REPO_FIX" --out "$OUT/host.json"
run_step userns "$PY" "$PAY/probe_userns.py" --base "$BASE" --out "$OUT/userns.json"
run_step cgroup "$PY" "$PAY/probe_cgroup.py" --repo "$REPO_FIX" --base "$BASE" \
  --out "$OUT/cgroup.json" --parent-out "$OUT/cgroup_parent.txt"
CGROUP_PARENT="$(cat "$OUT/cgroup_parent.txt" 2>/dev/null || true)"
echo "cgroup_parent='${CGROUP_PARENT}'"
if [ -n "${CGROUP_PARENT:-}" ]; then export AR_TEST_CGROUP_PARENT="$CGROUP_PARENT"; fi
# diagnostic waivers (labelled, never effective): only to show whether the sandbox/pivot_root/CUDA-IPC mechanics
# work when a required host condition fails.
DIAG=""
if [ -z "${CGROUP_PARENT:-}" ]; then DIAG="no_cgroup"; fi
PTR_SCOPE="$(cat /proc/sys/kernel/yama/ptrace_scope 2>/dev/null || true)"
case "${PTR_SCOPE:-}" in ""|0) DIAG="${DIAG:+$DIAG,}ptrace_scope" ;; esac
if [ "$(id -u)" = "0" ]; then DIAG="${DIAG:+$DIAG,}root"; fi
echo "diagnostic_waivers='${DIAG}'"

# ---- 6. the unit's own sandbox probe + sys.path hard check, both revisions and three interpreters -----
for rev_pair in "old_68cdd1a:$REPO_OLD" "fix_5403392e:$REPO_FIX"; do
  rev="${rev_pair%%:*}"; repo="${rev_pair#*:}"
  for interp in /opt/r1/envs/trackp/bin/python /opt/r1/envs/harness/bin/python /usr/bin/python3; do
    [ -x "$interp" ] || continue
    tag="${rev}_$(basename "$(dirname "$(dirname "$interp")")")"
    run_step "sandbox_${tag}" "$PY" "$PAY/probe_sandbox.py" --repo "$repo" --revision "$rev" \
      --interpreter "$interp" --tag "$tag" --base "$BASE" --out "$OUT/sandbox_${tag}.json"
  done
done

# ---- 7. real sandboxed smoke records (C7); no waivers unless the cgroup condition failed ------------
run_step smoke_old_nowaiver "$PY" "$PAY/probe_smoke.py" --repo "$REPO_OLD" --revision "old_68cdd1a" \
  --interpreter "$PY" --tag smoke_old_nowaiver --base "$BASE" \
  --cgroup-parent "${CGROUP_PARENT:-}" --out "$OUT/smoke_old_nowaiver.json"
run_step smoke_fix_nowaiver "$PY" "$PAY/probe_smoke.py" --repo "$REPO_FIX" --revision "fix_5403392e" \
  --interpreter "$PY" --tag smoke_fix_nowaiver --base "$BASE" \
  --cgroup-parent "${CGROUP_PARENT:-}" --out "$OUT/smoke_fix_nowaiver.json"
if [ -n "${DIAG:-}" ]; then
  # diagnostic only: labelled waivers so the report can separate "no cgroup / low ptrace_scope" from "no sandbox"
  run_step smoke_fix_diag "$PY" "$PAY/probe_smoke.py" --repo "$REPO_FIX" --revision "fix_5403392e" \
    --interpreter "$PY" --tag smoke_fix_diag --base "$BASE" --diag-waivers "$DIAG" \
    --out "$OUT/smoke_fix_diag.json"
fi

# ---- 8. the unit's own isolation test subset (record only) ------------------------------------------
PYTEST_JSON="$OUT/pytest_isolation.json"
if [ "${ISO_SKIP_PYTEST:-}" = "1" ]; then
  echo "pytest skipped: ISO_SKIP_PYTEST=1 (CPU-only allocation: short job; the 1-GPU job runs the subset)" \
    >"$OUT/logs/pytest_isolation.log"
  OUTJSON="$PYTEST_JSON" "$PY" -c 'import json,os; open(os.environ["OUTJSON"],"w").write(json.dumps({"skipped": True, "reason": "ISO_SKIP_PYTEST=1 (CPU-only short allocation)"}, indent=2)+chr(10))' 2>/dev/null || printf '{"skipped": true}\n' > "$PYTEST_JSON"
elif true; then
  {
    echo "=== pytest tests/trackg/test_trackg_isolation.py (fix 5403392e) $(date -u +%FT%TZ)"
    cd "$REPO_FIX" || exit 3
    # deselect the helper-timed test that blocks on a file when the host cannot run the scenario (Ada host
    # check: it hung there in the same situation); the remaining 27 tests cover the sandbox/cgroup/result channel
    PYTHONPATH="$REPO_FIX/src:$REPO_FIX" timeout 600 "$PY" -m pytest tests/trackg/test_trackg_isolation.py \
      -q -p no:cacheprovider \
      --deselect tests/trackg/test_trackg_isolation.py::test_elapsed_time_beyond_the_timeout_is_a_timeout_even_after_a_normal_exit
    echo "--- pytest rc=$?"
  } >"$OUT/logs/pytest_isolation.log" 2>&1
  tail -n 6 "$OUT/logs/pytest_isolation.log" | sed 's/^/    /'
  "$PY" - "$OUT/logs/pytest_isolation.log" "$PYTEST_JSON" <<'PYEOF'
import json, re, sys
from pathlib import Path
log = Path(sys.argv[1]).read_text(errors="replace")
tail = log[-4000:]
counts = {}
m = re.search(r"(\d+) passed", tail)
if m: counts["passed"] = int(m.group(1))
m = re.search(r"(\d+) failed", tail)
if m: counts["failed"] = int(m.group(1))
m = re.search(r"(\d+) skipped", tail)
if m: counts["skipped"] = int(m.group(1))
m = re.search(r"r=(\d+)", tail[-200:])
Path(sys.argv[2]).write_text(json.dumps({"rc": int(m.group(1)) if m else None, "counts": counts,
                                        "tail": tail[-1500:]}, indent=2) + "\n")
PYEOF
fi

# ---- 9. GPU smoke (C8): CUDA IPC across the worker PID namespace, sandbox on -------------------------
if [ -n "${CGROUP_PARENT:-}" ]; then
  run_step gpu_smoke "$PY" "$PAY/probe_gpu.py" --repo "$REPO_FIX" --revision "fix_5403392e" \
    --interpreter "$PY" --tag gpu_smoke --base "$BASE" --cgroup-parent "$CGROUP_PARENT" \
    --out "$OUT/gpu_smoke.json"
fi
if [ -n "${DIAG:-}" ]; then
  run_step gpu_smoke_diag "$PY" "$PAY/probe_gpu.py" --repo "$REPO_FIX" --revision "fix_5403392e" \
    --interpreter "$PY" --tag gpu_smoke_diag --base "$BASE" --diag-waivers "$DIAG" \
    --out "$OUT/gpu_smoke_diag.json"
fi

# ---- 10. aggregate + hashes -------------------------------------------------------------------------
run_step aggregate "$PY" "$PAY/aggregate.py" --out-dir "$OUT" --out "$OUT/isolation_check.json"
( cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
( cd "$OUT" && sha256sum SHA256SUMS ) >> "$OUT/logs/aggregate.log" 2>&1

echo "=== R1-T1-HOST-H200 isolation check end $(date -u +%FT%TZ)"
"$PY" - "$OUT/isolation_check.json" <<'PYEOF'
import json, sys
data = json.load(open(sys.argv[1]))
print("OVERALL:", data["overall"])
print("FAILED:", data.get("failed_conditions"))
for item in data["conditions"]:
    print(f"{item['id']} {item['result']} {item['name']}")
print("VERDICT:", data["verdict"])
PYEOF
exit 0
