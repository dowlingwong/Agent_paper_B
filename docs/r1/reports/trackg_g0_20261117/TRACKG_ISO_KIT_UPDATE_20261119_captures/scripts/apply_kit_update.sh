#!/bin/bash
# Apply the accepted harness-isolation fix (5403392) to the three Track G port kits on Ada:
#  1. normal (no-ff) merge of 5403392 into the kit branch (reviews: clean in all three);
#  2. copy the fixed master src/autoresearch/trackg/node_lib/ar_isolated.py over each node copy;
#  3. recompute the frozen pin of every node and record the values in the commit message;
#  4. commit locally (two commits: the merge, then the node-copy/pin commit). Never pushes.
# Fails closed on any unexpected tip, dirty tree, master hash or copy mismatch.
# usage: apply_kit_update.sh <ar|mlab|mlgym|all>
set -uo pipefail
BASE=/home/dowling/r1_trackg_20261117
E=/home/dowling/r1_engineering/iso_kit_update_20261119
PY=$BASE/envs/torch312/bin/python
FIX=$BASE/harness_iso_fix_20261119
FIXSHA=5403392e94cb59d732f45d6702fc857531ad8fd5
MASTER_REL=src/autoresearch/trackg/node_lib/ar_isolated.py
MASTER_SHA_EXPECT=37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610
export GIT_AUTHOR_NAME='Dowling Wong' GIT_AUTHOR_EMAIL='wangdowling@gmail.com'
export GIT_COMMITTER_NAME='Dowling Wong' GIT_COMMITTER_EMAIL='wangdowling@gmail.com'

fail() { echo "STOP: $*" >&2; exit 1; }

[ "$(git -C "$FIX" rev-parse HEAD)" = "$FIXSHA" ] || fail "fix worktree tip is not $FIXSHA"
[ -z "$(git -C "$FIX" status --porcelain=v1 -uall)" ] || fail "fix worktree is dirty"
MASTER_SHA=$(sha256sum "$FIX/$MASTER_REL" | cut -d' ' -f1)
[ "$MASTER_SHA" = "$MASTER_SHA_EXPECT" ] || fail "fix master ar_isolated.py is $MASTER_SHA, expected $MASTER_SHA_EXPECT"

# kit, worktree, pre tip, node root, node list, merge message, commit summary
update_kit() {
  local KIT=$1 WT=$2 PRETIP=$3 NODEROOT=$4 NODES=$5 MERGEMSG=$6 SUMMARY=$7 LOG
  LOG=$E/git/update_$KIT.log
  {
    echo "=== kit=$KIT worktree=$WT start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "pre tip: $(git -C "$WT" rev-parse HEAD)"
    [ "$(git -C "$WT" rev-parse HEAD)" = "$PRETIP" ] || fail "$KIT pre tip mismatch"
    [ -z "$(git -C "$WT" status --porcelain=v1 -uall)" ] || fail "$KIT worktree dirty before merge"
    if git -C "$WT" merge-base --is-ancestor "$FIXSHA" HEAD; then
      fail "$KIT already contains $FIXSHA (refusing to re-merge)"
    fi
    git -C "$WT" merge --no-ff -m "$MERGEMSG" "$FIXSHA" || fail "$KIT merge failed"
    local MERGE_TIP; MERGE_TIP=$(git -C "$WT" rev-parse HEAD)
    echo "merge tip: $MERGE_TIP"
    echo "--- merge diffstat (pre..merge):"
    git -C "$WT" diff --stat "$PRETIP" "$MERGE_TIP"
    git -C "$WT" diff --numstat "$PRETIP" "$MERGE_TIP"
    local MF; MF=$(sha256sum "$WT/$MASTER_REL" | cut -d' ' -f1)
    echo "kit master sha256 after merge: $MF"
    [ "$MF" = "$MASTER_SHA" ] || fail "$KIT merged master hash $MF != $MASTER_SHA"
    echo "--- copying the master over the node copies:"
    for n in $NODES; do cp -p "$FIX/$MASTER_REL" "$WT/$NODEROOT/$n/ar_isolated.py"; done
    for n in $NODES; do
      local H; H=$(sha256sum "$WT/$NODEROOT/$n/ar_isolated.py" | cut -d' ' -f1)
      echo "  $WT/$NODEROOT/$n/ar_isolated.py $H"
      [ "$H" = "$MASTER_SHA" ] || fail "$KIT node $n copy hash mismatch"
    done
    ( cd "$WT" && PYTHONPATH=src "$PY" "$E/scripts/compute_pins.py" "$KIT" $NODES > "$E/pins/new_$KIT.json" ) \
      || fail "$KIT pin recomputation failed"
    echo "--- new pins (no data link yet):"
    cat "$E/pins/new_$KIT.json"
    {
      echo "$SUMMARY"
      echo
      echo "Merge 5403392e94cb59d732f45d6702fc857531ad8fd5 (accepted R1-HARNESS-ISOLATION fix: condition 6"
      echo "PASS on Ada, condition 7 GPU CUDA-IPC blocked/disclosed) and copy the fixed master"
      echo "$MASTER_REL (sha256 $MASTER_SHA) byte-identically over every node"
      echo "copy. Only ar_isolated.py changes among the frozen files; the recomputed frozen_pin_sha256"
      echo "values (frozen_file_hashes exactly as WorkingCopyRunner takes them) are:"
      "$PY" - "$E/pins/new_$KIT.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
for name, value in sorted(d.items()):
    print("  %-26s %s" % (name, value["pin"]))
PYEOF
    } > "$E/git/msg_$KIT.txt" || fail "$KIT commit message build failed"
    echo "--- commit message:"; cat "$E/git/msg_$KIT.txt"
    local -a FILES=()
    for n in $NODES; do FILES+=("$NODEROOT/$n/ar_isolated.py"); done
    git -C "$WT" add -- "${FILES[@]}" || fail "$KIT git add failed"
    git -C "$WT" commit -F "$E/git/msg_$KIT.txt" || fail "$KIT commit failed"
    echo "post tip: $(git -C "$WT" rev-parse HEAD)"
    echo "--- copy commit stat:"; git -C "$WT" show --stat --oneline --no-renames HEAD
    echo "status after: [$(git -C "$WT" status --porcelain=v1 -uall)]"
    echo "=== kit=$KIT end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >> "$LOG" 2>&1
  return $?
}

case "${1:-all}" in
  ar)
    update_kit ar "$BASE/harness_iso_ar" 5d3dccccf1790203212d2e0aa96c969f7c703fdc nodes \
      "autoresearch_fixedtokens" \
      "Merge mac-harness-isolation-fix-20261119 (isolation core fix 5403392, accepted: condition 6 PASS on Ada)" \
      "trackg autoresearch port: fixed ar_isolated.py (sha256 37d99ab0) in the node; frozen pin updated" ;;
  mlab)
    update_kit mlab "$BASE/harness_iso_mlab" 0aae2f68376a5665ce1869e835906615b7e08ecc nodes \
      "mlab_cifar10 mlab_imdb mlab_ogbn_arxiv" \
      "Merge mac-harness-isolation-fix-20261119 (isolation core fix 5403392, accepted: condition 6 PASS on Ada)" \
      "trackg MLAgentBench port: fixed ar_isolated.py (sha256 37d99ab0) in the three nodes; frozen pins updated" ;;
  mlgym)
    update_kit mlgym "$BASE/harness_iso_mlgym" 061d638edc91254477d699b3be89e40625cc99ec third_party/mlgym/nodes \
      "mlgym_breakout_minatar mlgym_cifar10 mlgym_fmnist mlgym_houseprice" \
      "Merge mac-harness-isolation-fix-20261119 (isolation core fix 5403392, accepted: condition 6 PASS on Ada)" \
      "trackg MLGym port: fixed ar_isolated.py (sha256 37d99ab0) in the four nodes; frozen pins updated" ;;
  all)
    "$0" ar || exit $?
    "$0" mlab || exit $?
    "$0" mlgym || exit $?
    echo "ALL_KITS_UPDATED" ;;
  *) echo "usage: $0 <ar|mlab|mlgym|all>" >&2; exit 2 ;;
esac
