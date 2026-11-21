#!/bin/bash
# TASL-2 data setup for R1-TRACKG-AR-U2-TASL2: run the node's frozen setup_command
# (prepare_data.py: download 10 climbmix training shards + pinned val shard, train tokenizer, manifest, link data).
# Author-signed task; guarded: HF revision must match the reviewed 915333b...; no deletion; data root outside repo.
set -u
E=/home/dowling/r1_engineering/tasl2_ar_cond7a_20261121
BU=/home/dowling/r1_trackp
W=$BU/harness_cond7a_20261121
V=$BU/venvs/ar-cond7a
NODE=autoresearch_fixedtokens
export PATH="$V/bin:/home/dowling/.local/bin:/usr/local/bin:/usr/bin:/bin"
export VIRTUAL_ENV="$V"
export PYTHONDONTWRITEBYTECODE=1
export AR_TRACKG_DATA_ROOT=$BU/data
export HF_HOME=${HF_HOME:-$HOME/.cache/huggingface}
OUT=$AR_TRACKG_DATA_ROOT/$NODE
LOG=$E/logs/setup_data.log
: > "$LOG"
say(){ echo "$*" | tee -a "$LOG"; }
say "# node setup_command run start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "task=R1-TRACKG-AR-U2-TASL2 (author-signed) node=$NODE"
say "worktree=$W tip=$(git -C "$W" rev-parse HEAD 2>&1)"
say "python=$(command -v python3) version=$(python3 -V 2>&1) venv=$VIRTUAL_ENV"
say "AR_TRACKG_DATA_ROOT=$AR_TRACKG_DATA_ROOT (outside the repository)"
say "out=$OUT"
say "setup_command=$(cd "$W/nodes/$NODE" && python3 - <<'PY'
from autoresearch.trackg.node_template import load_trackg_node_spec
PY
)"
say "hf_revision_precheck: $(tr '\n' ' ' < "$E/prep/hf_revision_precheck.txt")"
grep -q '^prefix_ok= True' "$E/prep/hf_revision_precheck.txt" || { say "STOP: HF revision does not match reviewed 915333b prefix; nothing downloaded"; echo "STOP $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$E/prep/SETUP_STOP"; exit 5; }
say "existing data root: $(ls -la "$AR_TRACKG_DATA_ROOT" 2>&1 | head -5)"
mkdir -p "$AR_TRACKG_DATA_ROOT"
cd "$W/nodes/$NODE" || { say "STOP: node dir missing"; exit 3; }
say "# invoking frozen setup_command: AR_TRACKG_DATA_ROOT=... python3 prepare_data.py --out $OUT"
/usr/bin/time -v -o "$E/prep/setup_time_v.txt" python3 prepare_data.py --out "$OUT" >> "$LOG" 2>&1
RC=$?
say "setup_rc=$RC"
if [ "$RC" -eq 0 ]; then
  say "# manifest + tree"
  sha256sum "$OUT/data_manifest.json" | tee -a "$LOG"
  find "$OUT" -type f | wc -l | tee -a "$LOG"
  du -sh "$OUT" | tee -a "$LOG"
  say "# node data link: $(readlink "$W/nodes/$NODE/data" 2>&1)"
  echo "DONE_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$E/prep/SETUP_DONE"
else
  say "STOP: setup_command failed rc=$RC"
  echo "STOP rc=$RC $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$E/prep/SETUP_STOP"
fi
say "# setup end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit $RC
