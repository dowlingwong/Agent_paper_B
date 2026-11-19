#!/bin/bash
# usage: setup_node.sh <kit: ar|mlab|mlgym> <node> <logfile>
# Runs the node's documented setup_command with AR_TRACKG_DATA_ROOT outside the repository;
# re-checks the existing read-only data tree and links it into the node (nothing downloaded if complete).
# The node dirs live under the kit worktree; the data link is untracked runtime state.
set -u
KIT=$1; NODE=$2; LOG=$3
BASE=/home/dowling/r1_trackg_20261117
PY=$BASE/envs/torch312/bin/python
export AR_TRACKG_DATA_ROOT=$BASE/data
case "$KIT" in
  ar)   HOME_DIR=$BASE/harness_iso_ar ;;
  mlab) HOME_DIR=$BASE/harness_iso_mlab ;;
  mlgym) HOME_DIR=$BASE/harness_iso_mlgym/third_party/mlgym ;;
  *) echo "bad kit" >&2; exit 2 ;;
esac
NODE_DIR=$HOME_DIR/nodes/$NODE
{
  echo "# setup kit=$KIT node=$NODE node_dir=$NODE_DIR start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$NODE_DIR" || exit 3
  "$PY" prepare_data.py --out "$AR_TRACKG_DATA_ROOT/$NODE" 2>&1
  echo "SETUP_EXIT=$?"
  echo "data link: $(readlink data 2>&1)"
  echo "manifest sha256: $(sha256sum "$AR_TRACKG_DATA_ROOT/$NODE/data_manifest.json" 2>&1)"
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
