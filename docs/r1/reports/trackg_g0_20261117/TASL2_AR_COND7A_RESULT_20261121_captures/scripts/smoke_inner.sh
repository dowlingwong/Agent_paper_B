#!/bin/bash
# Inner script of the ONE R1-TRACKG-AR-U2-TASL2 isolated smoke, executed INSIDE the delegated 8 GiB
# systemd user scope (Delegate=yes, MemoryMax=8G, MemorySwapMax=0).
# usage: smoke_inner.sh <gpu_uuid> <cpus> <evidence_dir> [--prechecks-only]
# Establishes AR_TEST_CGROUP_PARENT from the live scope cgroup, sets the ar-cond7a env / PATH / VIRTUAL_ENV,
# CUDA_VISIBLE_DEVICES="", checks the 8 GiB / 0 swap cgroup, env/data/spec/pins, then runs the kit's one-line
# smoke command under taskset + /usr/bin/time -v, and captures the post-smoke cgroup memory.  ENGINEERING_ONLY.
set -u
GPU=${1:?gpu_uuid}; CPUS=${2:?cpus}; E=${3:?evidence_dir}; MODE=${4:-run}
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
COMMITTED_PIN=$(grep -o '"pin": "[0-9a-f]\{64\}"' "$E/prep/pins_committed_recheck.txt" 2>/dev/null | head -1 | cut -d'"' -f4)
DEPLOYED_PIN=$(grep -o '"pin": "[0-9a-f]\{64\}"' "$E/prep/pins_deployed_recheck.txt" 2>/dev/null | head -1 | cut -d'"' -f4)
cd "$W" || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
BEFORE=$(command -v python || true)
export PATH="$V/bin:$(dirname "$UV"):/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export VIRTUAL_ENV="$V"
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export AR_TRACKG_DATA_ROOT=$BU/data
export CUDA_VISIBLE_DEVICES=""
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
{
  echo "# delegated scope probe (inside the systemd-run --user --scope) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
  echo "memory.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.max" 2>&1)"
  echo "memory.swap.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max" 2>&1)"
  echo "expected_memory.max=8589934592"
  echo "expected_memory.swap.max=0"
  echo "memory.peak_exposed=$( [ -e "$AR_TEST_CGROUP_PARENT/memory.peak" ] && echo yes || echo no)"
  echo "cgroup.kill_exposed=$( [ -e "$AR_TEST_CGROUP_PARENT/cgroup.kill" ] && echo yes || echo no)"
  echo "nsdelegate=$(grep -o 'nsdelegate' /proc/self/mountinfo | head -1)"
  echo "which_python_before_PATH=${BEFORE:-}"
  echo "which_python_after_PATH=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "PYTHONPATH=$PYTHONPATH"
  echo "VIRTUAL_ENV=$VIRTUAL_ENV"
  echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
  echo "taskset_cpus=$CPUS"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$E/cgroup_probe.txt"
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max" 2>/dev/null)" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max" 2>/dev/null)" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
# env freeze of the run interpreter (recorded; stderr kept for diagnosis)
uv pip freeze --python "$(command -v python)" > "$E/env_freeze_live.txt" 2> "$E/env_freeze_live.stderr.txt"
ENV_FREEZE_LIVE_SHA=$(sha256sum "$E/env_freeze_live.txt" 2>/dev/null | cut -d' ' -f1)
{
  echo "# launch prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "torch=$(python -c 'import torch;print(torch.__version__, torch.version.cuda)' 2>&1)"
  echo "env_freeze_live_sha256=$ENV_FREEZE_LIVE_SHA"
  echo "env_freeze_live_lines=$(wc -l < "$E/env_freeze_live.txt" 2>/dev/null)"
  echo "env_freeze_live_stderr=$(tr '\n' ';' < "$E/env_freeze_live.stderr.txt" 2>/dev/null)"
  echo "env_freeze_expected=$EXPECTED_ENV_FREEZE_SHA"
  echo "data_manifest_sha256=$(sha256sum "$DATA/data_manifest.json" 2>&1)"
  echo "data_manifest_expected=$EXPECTED_DATA_MANIFEST"
  echo "node_data_link=$(readlink "$NODE_DIR/data" 2>&1)"
  echo "spec_raw_sha256=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("'"$SPEC"'").raw_sha256)' 2>&1)"
  echo "spec_raw_sha256_expected=$EXPECTED_SPEC_SHA"
  echo "committed_file_pin=$COMMITTED_PIN"
  echo "committed_file_pin_expected=147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc"
  echo "deployed_pin_expected=$DEPLOYED_PIN (21 entries, data link included; TASL-2 data root)"
  echo "no_cuda_ipc_in_result_path:"
  python - <<'PY'
import ast
from pathlib import Path
base = Path("nodes/autoresearch_fixedtokens")
for f in ("run_fixed_budget.py", "ar_worker.py"):
    t = ast.parse((base / f).read_text())
    hits = [n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)
            and n.attr in {"cuda_share", "cuda_open", "_share_cuda_", "_new_shared_cuda", "bind_cuda"}]
    print(f, "CUDA_IPC_API_HITS=", sorted(set(hits)) or "NONE")
PY
  echo "import_port_smoke_gpu:"; python -c 'import tests.trackg.port_smoke_gpu; print("import OK")' 2>&1
  echo "smoke_entry:"; python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("'"$NODE"'") is not None)' 2>&1
  echo "affinity=$(taskset -pc $$ 2>&1)"
  echo "ulimit_core=$(ulimit -c)"; echo "nproc=$(nproc)"
} > "$E/prechecks.txt"
FS="$ENV_FREEZE_LIVE_SHA"
[ "$FS" = "$EXPECTED_ENV_FREEZE_SHA" ] || { echo "STOP env freeze sha $FS != expected (see $E/env_freeze_live.stderr.txt)" >&2; exit 92; }
DM=$(sha256sum "$DATA/data_manifest.json" 2>/dev/null | cut -d' ' -f1)
[ "$DM" = "$EXPECTED_DATA_MANIFEST" ] || { echo "STOP data manifest sha $DM != expected" >&2; exit 93; }
SS=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("'"$SPEC"'").raw_sha256)' 2>/dev/null)
[ "$SS" = "$EXPECTED_SPEC_SHA" ] || { echo "STOP spec raw sha $SS != expected" >&2; exit 94; }
ENTRY=$(python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("'"$NODE"'") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 95 ;; esac
if [ "$MODE" = "--prechecks-only" ]; then
  echo "PRECHECKS_ONLY_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit 0
fi
echo "# launching one-line smoke command $(date -u +%Y-%m-%dT%H:%M:%SZ)"
taskset -c "$CPUS" /usr/bin/time -v -o "$E/time_v.txt" python -m tests.trackg.port_smoke_gpu \
  --node "$NODE" \
  --gpu-uuid "$GPU" \
  --cpus "$CPUS" \
  --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
  --runs-root "$E/runs" \
  --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
{
  echo "# cgroup memory after the smoke $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for f in memory.peak memory.current memory.events memory.max memory.swap.max memory.swap.current; do
    if [ -f "$AR_TEST_CGROUP_PARENT/$f" ]; then echo "$f=$(cat "$AR_TEST_CGROUP_PARENT/$f")"; else echo "$f=NOT_EXPOSED"; fi
  done
} > "$E/memory_cgroup.txt"
exit $RC
