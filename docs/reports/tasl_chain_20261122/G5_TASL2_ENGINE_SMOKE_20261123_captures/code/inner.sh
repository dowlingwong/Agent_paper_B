#!/bin/bash
# In-scope launcher for the ENGINEERING G.5 smoke (replica of t1_tasl_node.sh's
# g5 scope argv: systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G
# -p MemorySwapMax=0, AR_TEST_CGROUP_PARENT and taskset on the delegated cpus).
set -u
CG=$(sed -n "s/^0:://p" /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G5_TASL_NODE_LOG="${T1_LOG:-}"
export SMOKE_ROOT="${T1_ROOT:?}"
export SMOKE_PAPER="${T1_PAPER:?}"
unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
taskset -c "${T1_CPUS:?}" "${T1_PY:?}" "$SMOKE_ROOT/bin/driver.py" "$@"
RC=$?
echo "NODE_EXIT=$RC"
exit "$RC"
