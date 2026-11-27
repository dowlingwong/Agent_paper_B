#!/bin/bash
# compute/20261127-26 — screening cache rebuild and engineering smoke (ENGINEERING_ONLY)
# Host: deepthought. Code: c12136d664ae588a2539b76b2602e36742979ce8 (reviewed cache fix).
# The checkout is a clean detached clone of the repository at that commit, an ancestor of the
# published origin/main at run time (docs-only R1-D3-STEP8-HOLD followed it).
# The STOP below happened before any output directory was created: refs/remotes/origin/main was
# one commit behind the remote after the coordinator published 4a9a1f4a. The fetch in the second
# block made the strict environment check pass; no attempt had started.
set -euo pipefail

ROOT=/work/dwong/screen_fix_20261127
cd "$ROOT/paper"
git fetch -q origin
test "$(git rev-parse refs/remotes/origin/main)" = "$(git ls-remote origin refs/heads/main | cut -f1)"

VENV=/ceph/dwong/r1_prepare_20261025/venv
export PATH="$VENV/bin:$PATH"
export AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness
export PYTHONDONTWRITEBYTECODE=1
test "$(git -C "$AR_HARNESS_ROOT" rev-parse HEAD)" = 6adf3859de66c4814fcf376eed59880fbd8eeaf7
test -z "$(git -C "$AR_HARNESS_ROOT" status --porcelain --untracked-files=no)"

CACHE_STAMP=$(cat "$ROOT/RUN_STAMP")   # 20261127T134927Z
CACHE="$ROOT/data_cache_$CACHE_STAMP"

# 1. Build a new cache. data-cache fills each node once, then performs a fresh offline load and
#    refuses if that load changes the tree.
"$VENV/bin/python3" -B -m r1.noise.screen_measure data-cache \
  --out "$CACHE" --tmp "/tmp/r1_cache_build_$CACHE_STAMP"

# 2. Engineering smoke at seed 999 with the evidence worker-runtime checks (python3 worker).
SMOKE_STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SMOKE="$ROOT/smoke_FIXED_$SMOKE_STAMP"
test ! -e "$SMOKE"
"$VENV/bin/python3" -B -m r1.noise.screen_measure run --engineering-smoke \
  --out "$SMOKE" --workers 16 --tmp "/tmp/r1_smoke_fixed_$SMOKE_STAMP" --data-cache "$CACHE"

sha256sum "$CACHE/MANIFEST.json" "$SMOKE/manifest.json" "$SMOKE/design.json" \
  "$SMOKE/lineage_runs.jsonl" "$SMOKE/worker_runtime.jsonl" "$SMOKE/cotenancy.log"
