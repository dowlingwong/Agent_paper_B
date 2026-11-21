#!/bin/bash
# R1-T1-HOST-TASL: G.4 proposer prerequisites on TASL-7 (before any G.4 run; no server start here).
#
# The exam llama-server is used in place (R1-T1-TASL-ENV option A).  Records, read-only:
#   * the *whole build directory* sha256 manifest via the merged main's own ``g4_tasl.py bin-manifest``
#     (the executable and its shared libraries, symlinks as links), and the manifest text's sha256;
#   * the binary sha256 / size / file / ``--version`` build line;
#   * ``ldd`` resolution with no LD_LIBRARY_PATH / LD_PRELOAD, and every libllama*/libggml*/libmtmd* entry
#     resolving inside the build directory (plus the RPATH/RUNPATH it relies on);
#   * the GGUF sha256 / size;
#   * Tailscale addresses and route facts (TASL-7's own .51 vs the shared-node alias .50 that TASL-2 sees).
#
# No server start, no GPU use, no lease here; the bind-only start/stop is ``bind_test.sh``.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
CAP="$BASE/captures"
BIN=/home/dowling/exam-x/work/llama.cpp/build-exam/bin
BIN_LLAMA=/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server
GGUF=/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf
EXPECT_BIN_SHA=b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b
EXPECT_GGUF_SHA=2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
EXPECT_GGUF_SIZE=19598489952
EXPECT_BUILD="0.7.0-dev (build 1, commit 620d222)"
G4TASL="$BASE/proposer/scripts/t1_tasl/g4_tasl.py"
mkdir -p "$CAP/logs" "$CAP/proposer"
cd "$BASE" || exit 2

{
  echo "=== utc=$(date -u +%FT%TZ) host=$(hostname) euid=$(id -u)"
  echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-<unset>}"
  echo "LD_PRELOAD=${LD_PRELOAD:-<unset>}"
  echo "bin_dir=$BIN"
  echo "binary=$BIN_LLAMA"
  echo "gguf=$GGUF"
  echo "g4_tasl.py=$G4TASL sha256=$(sha256sum "$G4TASL" | cut -d' ' -f1)"
} > "$CAP/proposer/identity_inputs.txt" 2>&1

# ---- 1. the whole build-directory manifest, with the merged main's own helper --------------------------
env -u LD_LIBRARY_PATH -u LD_PRELOAD /usr/bin/python3 "$G4TASL" bin-manifest "$BIN" \
  > "$CAP/proposer/bin_manifest.txt" 2> "$CAP/proposer/bin_manifest.stderr.txt"
echo "bin_manifest_rc=$?" > "$CAP/proposer/bin_manifest_rc.txt"
# the file itself (text + the "manifest_sha256: ..." line) and the text-only digest
sha256sum "$CAP/proposer/bin_manifest.txt" | cut -d' ' -f1 > "$CAP/proposer/bin_manifest.file_sha256.txt"
grep -o 'manifest_sha256: [0-9a-f]*' "$CAP/proposer/bin_manifest.txt" | cut -d' ' -f2 \
  > "$CAP/proposer/bin_manifest.text_sha256_from_helper.txt"
sed '$d' "$CAP/proposer/bin_manifest.txt" | sha256sum | cut -d' ' -f1 \
  > "$CAP/proposer/bin_manifest.text_sha256_recomputed.txt"
wc -l "$CAP/proposer/bin_manifest.txt" > "$CAP/proposer/bin_manifest.lines.txt"
ls -la "$BIN" > "$CAP/proposer/bin_dir_listing.txt" 2>&1

# ---- 2. binary identity and build line ---------------------------------------------------------------
stat -c '%n|%s|%Y|%Z|%a|%U|%G' "$BIN_LLAMA" > "$CAP/proposer/binary.stat.txt" 2>&1
sha256sum "$BIN_LLAMA" > "$CAP/proposer/binary.sha256.txt" 2>&1
file -b "$BIN_LLAMA" > "$CAP/proposer/binary.file.txt" 2>&1
env -u LD_LIBRARY_PATH -u LD_PRELOAD "$BIN_LLAMA" --version \
  > "$CAP/proposer/binary.version.txt" 2>&1
echo "version_rc=$?" >> "$CAP/proposer/binary.version.txt"

# ---- 3. ldd resolution (no LD_LIBRARY_PATH/LD_PRELOAD) and where the llama.cpp libs resolve ------------
env -u LD_LIBRARY_PATH -u LD_PRELOAD ldd "$BIN_LLAMA" > "$CAP/proposer/ldd.txt" 2>&1
echo "ldd_rc=$?" > "$CAP/proposer/ldd_rc.txt"
readelf -d "$BIN_LLAMA" 2>/dev/null | grep -Ei "rpath|runpath" > "$CAP/proposer/readelf_rpath.txt" 2>&1
grep -E "libllama|libggml|libmtmd" "$CAP/proposer/ldd.txt" > "$CAP/proposer/ldd_llama_libs.txt" 2>&1
echo "not_found_count=$(grep -c 'not found' "$CAP/proposer/ldd.txt")" > "$CAP/proposer/ldd_not_found.txt"
awk '{print $3}' "$CAP/proposer/ldd_llama_libs.txt" 2>/dev/null | grep -c "^$BIN/" \
  > "$CAP/proposer/ldd_llama_libs_inside_bin_dir.txt" 2>&1
awk '{print $3}' "$CAP/proposer/ldd_llama_libs.txt" 2>/dev/null | grep -v "^$BIN/" \
  > "$CAP/proposer/ldd_llama_libs_outside.txt" 2>&1

# ---- 4. GGUF identity ---------------------------------------------------------------------------------
sha256sum "$GGUF" > "$CAP/proposer/gguf.sha256.txt" 2>&1
stat -c '%n|%s|%Y' "$GGUF" > "$CAP/proposer/gguf.stat.txt" 2>&1

# ---- 5. Tailscale facts -------------------------------------------------------------------------------
tailscale ip -4 > "$CAP/proposer/tailscale_ip4.txt" 2>&1
tailscale status > "$CAP/proposer/tailscale_status.txt" 2>&1
tailscale status --json > "$CAP/proposer/tailscale_status.json" 2>&1
ip -4 -o addr show > "$CAP/proposer/ip4_addr.txt" 2>&1
ip route get 100.106.74.50 > "$CAP/proposer/route_to_50.txt" 2>&1
ip route get 100.106.74.51 > "$CAP/proposer/route_to_51.txt" 2>&1
ip route > "$CAP/proposer/ip_route.txt" 2>&1
ss -ltn > "$CAP/proposer/ss_listen_before.txt" 2>&1
# is the shared-node alias .50 an address on this host at all?  (bind must fail with EADDRNOTAVAIL)
env -u LD_LIBRARY_PATH -u LD_PRELOAD /usr/bin/python3 - > "$CAP/proposer/bind_probe_50.txt" 2>&1 <<'PYEOF'
import errno, socket
for host in ("100.106.74.50", "100.106.74.51"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        print(f"{host}: bind_ok local={s.getsockname()}")
    except OSError as error:
        print(f"{host}: bind_failed errno={error.errno} ({errno.errorcode.get(error.errno)}) {error}")
    finally:
        s.close()
PYEOF
# TASL-2 is not logged into from here (no touch); its reachability of .50 over the shared node is cited from
# TASL7_PROPOSER_SMOKE_20261121.md and the route facts above.

# ---- 6. summary JSON ----------------------------------------------------------------------------------
/usr/bin/python3 - "$CAP/proposer" > "$CAP/proposer/proposer_prereq_result.json" 2> "$CAP/proposer/proposer_prereq_result.stderr" <<'PYEOF'
import json, re, sys
from pathlib import Path
cap = Path(sys.argv[1])
def read(name):
    try:
        return (cap / name).read_text(errors="replace").strip()
    except OSError:
        return ""
manifest = read("bin_manifest.txt")
m = re.search(r"^manifest_sha256: ([0-9a-f]{64})$", manifest, re.M)
version = read("binary.version.txt")
ldd = read("ldd.txt")
llama_libs = [ln for ln in read("ldd_llama_libs.txt").splitlines() if ln.strip()]
outside = [ln for ln in llama_libs if "/home/dowling/exam-x/work/llama.cpp/build-exam/bin/" not in ln]
expect_bin = "b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b"
expect_gguf = "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75"
expect_build = "0.7.0-dev (build 1, commit 620d222)"
bin_sha = read("binary.sha256.txt").split()[0] if read("binary.sha256.txt") else None
gguf_sha = read("gguf.sha256.txt").split()[0] if read("gguf.sha256.txt") else None
gguf_size = int(read("gguf.stat.txt").split("|")[1]) if read("gguf.stat.txt") else None
checks = {
    "bin_dir_manifest_written": bool(manifest),
    "bin_manifest_rc_0": read("bin_manifest_rc.txt").strip() == "bin_manifest_rc=0",
    "bin_dir_manifest_digest_present": bool(m),
    "bin_dir_manifest_digest_recomputed_equal":
        (read("bin_manifest.text_sha256_from_helper.txt") == read("bin_manifest.text_sha256_recomputed.txt") and bool(m)),
    "binary_sha256_expected": bin_sha == expect_bin,
    "build_expected": f"version: {expect_build}" in version,
    "ldd_ok": read("ldd_rc.txt").strip() == "ldd_rc=0" and "not found" not in ldd,
    "llama_libs_all_inside_bin_dir": bool(llama_libs) and not outside,
    "gguf_sha256_expected": gguf_sha == expect_gguf,
    "gguf_size_expected": gguf_size == 19598489952,
    "no_ld_library_path": "LD_LIBRARY_PATH=<unset>" in read("identity_inputs.txt"),
    "no_ld_preload": "LD_PRELOAD=<unset>" in read("identity_inputs.txt"),
    "tailscale_ip_51": "100.106.74.51" in read("tailscale_ip4.txt"),
    "shared_node_alias_50_not_local": "EADDRNOTAVAIL" in read("bind_probe_50.txt"),
}
result = {
    "utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
    "host": __import__("socket").gethostname(),
    "bin_dir": "/home/dowling/exam-x/work/llama.cpp/build-exam/bin",
    "binary": read("identity_inputs.txt").splitlines()[-3:],
    "checks": checks,
    "bin_dir_manifest_sha256": m.group(1) if m else None,
    "bin_dir_manifest_file_sha256": read("bin_manifest.file_sha256.txt"),
    "bin_dir_manifest_lines": int(read("bin_manifest.lines.txt").split()[0]) if read("bin_manifest.lines.txt") else None,
    "binary_sha256": bin_sha,
    "build": next((ln.strip() for ln in version.splitlines() if ln.startswith("version:")), None),
    "build_rc": next((ln for ln in version.splitlines() if ln.startswith("version_rc=")), None),
    "ldd_rc": read("ldd_rc.txt"),
    "ldd_not_found": read("ldd_not_found.txt"),
    "llama_lib_lines": llama_libs,
    "llama_libs_outside_bin_dir": outside,
    "llama_libs_count": len(llama_libs),
    "rpath_runpath": read("readelf_rpath.txt"),
    "gguf": {"path": "/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf",
             "sha256": gguf_sha, "size": gguf_size},
    "tailscale": {"ip4": read("tailscale_ip4.txt"),
                  "status_first_lines": read("tailscale_status.txt").splitlines()[:12],
                  "route_to_50": read("route_to_50.txt"), "route_to_51": read("route_to_51.txt"),
                  "bind_probe": read("bind_probe_50.txt")},
    "condition_proposer_prereq_pass": all(checks.values()),
}
print(json.dumps(result, indent=2, sort_keys=True))
PYEOF

/usr/bin/python3 - "$CAP/proposer" > "$CAP/proposer/proposer_prereq_result.txt" 2>&1 <<'PYEOF'
import json, sys
from pathlib import Path
cap = Path(sys.argv[1])
r = json.loads((cap / "proposer_prereq_result.json").read_text())
print(f"utc={r['utc']} host={r['host']}")
for k, v in r["checks"].items():
    print(f"{k}={v}")
print(f"bin_dir_manifest_sha256={r['bin_dir_manifest_sha256']}")
print(f"bin_dir_manifest_file_sha256={r['bin_dir_manifest_file_sha256']} lines={r['bin_dir_manifest_lines']}")
print(f"binary_sha256={r['binary_sha256']} build={r['build']!r} {r['build_rc']}")
print(f"ldd_rc={r['ldd_rc']} {r['ldd_not_found']} llama_libs={r['llama_libs_count']} "
      f"outside={len(r['llama_libs_outside_bin_dir'])}")
print(f"gguf_sha256={r['gguf']['sha256']} size={r['gguf']['size']}")
print(f"rpath_runpath={r['rpath_runpath']!r}")
print(f"tailscale={json.dumps(r['tailscale'], sort_keys=True)}")
print(f"condition_proposer_prereq_pass={r['condition_proposer_prereq_pass']}")
PYEOF

cat "$CAP/proposer/proposer_prereq_result.txt"
exit 0
