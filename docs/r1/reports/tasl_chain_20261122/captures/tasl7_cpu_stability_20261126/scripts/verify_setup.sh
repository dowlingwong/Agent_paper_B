#!/bin/bash
# TASL-7 CPU stability check - pre-flight verification of the copied kit / env / data (read-only checks only).
set -u
H=/home/dowling/r1_trackg_20261125/harness_metamaze
ENV=/home/dowling/r1_trackg_20261125/venv_jax
PY=$ENV/bin/python
DATA=/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze
NODE=$H/third_party/mlgym/nodes/mlgym_metamaze
PIN=aa354485bff6b5746c48ddadcb50d92e9c6f3645
BRANCH=mac-trackg-mountaincar-20261125
FREEZE=630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9
DATAMAN=e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000
fail=0
chk() { if [ "$2" = "$3" ]; then echo "OK   $1 = $2"; else echo "FAIL $1 = $2 (expected $3)"; fail=1; fi; }

echo "=== utc $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
echo "--- interpreter"
chk "python_version" "$($PY -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])')" "3.12.16"
chk "python_realpath" "$(readlink -f $ENV/bin/python)" "/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12"
echo "--- git binding"
chk "git_head" "$(git -C $H rev-parse HEAD)" "$PIN"
chk "git_branch" "$(git -C $H rev-parse --abbrev-ref HEAD)" "$BRANCH"
st=$(git -C $H status --porcelain | tr '\n' '|')
chk "git_status" "$st" "?? third_party/mlgym/nodes/mlgym_metamaze/data|"
git -C $H merge-base --is-ancestor c025f89aeafc2199bf3487b4bcaa16678273c702 HEAD && echo "OK   base_commit_ancestor" || { echo "FAIL base_commit_ancestor"; fail=1; }
echo "--- pinned file hashes"
chk "node_spec_sha256" "$(sha256sum $H/third_party/mlgym/configs/trackg/nodes/mlgym_metamaze.yaml | cut -d' ' -f1)" "d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59"
chk "edits_manifest_sha256" "$(sha256sum $NODE/representative_edits/manifest.json | cut -d' ' -f1)" "6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2"
chk "data_manifest_sha256" "$(sha256sum $DATA/data_manifest.json | cut -d' ' -f1)" "$DATAMAN"
chk "node_ar_isolated_sha256" "$(sha256sum $NODE/ar_isolated.py | cut -d' ' -f1)" "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610"
chk "master_ar_isolated_sha256" "$(sha256sum $H/src/autoresearch/trackg/node_lib/ar_isolated.py | cut -d' ' -f1)" "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610"
echo "--- data files (manifest + per-file hashes, read-only)"
$PY - "$DATA" <<'PYEOF'
import hashlib, json, sys, os
data = sys.argv[1]
man = json.load(open(os.path.join(data, "data_manifest.json")))
print("schema=%s node=%s files=%d" % (man.get("schema"), man.get("node"), len(man["files"])))
bad = []
for name, meta in sorted(man["files"].items()):
    p = os.path.join(data, name)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    ok = h == meta["sha256"] and os.path.getsize(p) == meta["bytes"]
    if not ok: bad.append(name)
    print("%-28s %s bytes=%-8d mode=%s match=%s" % (name, h[:16], os.path.getsize(p), oct(os.stat(p).st_mode & 0o777), ok))
print("DATA_ALL_MATCH" if not bad else "DATA_BAD " + repr(bad))
mode = os.stat(data).st_mode & 0o777
rw = any(os.stat(os.path.join(data, f)).st_mode & 0o222 for f in man["files"])
print("data_root_mode=%s any_file_write_bit=%s" % (oct(mode), rw))
PYEOF
echo "--- env freeze"
$PY -m pip freeze > /tmp/tasl7_freeze.txt 2>/dev/null || $PY -m pip freeze > /home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126/freeze.txt
F=$(sha256sum /tmp/tasl7_freeze.txt | cut -d' ' -f1)
echo "freeze_packages=$(grep -c '==' /tmp/tasl7_freeze.txt) freeze_sha256=$F"
chk "freeze_sha256" "$F" "$FREEZE"
echo "--- versions"
$PY - <<'PYEOF'
import importlib.metadata as md
for n in ("jax","jaxlib","flax","optax","gymnax","tensorflow_probability","dotmap","numpy"):
    try: print("%-22s %s" % (n, md.version(n)))
    except md.PackageNotFoundError: print("%-22s ABSENT" % n)
import importlib.util
print("torch_importable", importlib.util.find_spec("torch") is not None)
PYEOF
echo "--- data symlink"
ls -la $NODE/data
echo "--- disk"
df -h /home | tail -1
echo "PRECHECK_RC=$fail"
exit $fail
