#!/bin/bash
# Build the Paper B R1 Apptainer image and record its identity. No deletion anywhere.
# Usage: build_sif.sh [--build]   (without --build it only prints the plan)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEF="$HERE/r1-htc.def"
IMG_DIR=/work/dwong/paperb/images
MIRROR=/ceph/srv/dwong/paperb/images
SIF="$IMG_DIR/r1-htc-20261114.sif"
LOG="$IMG_DIR/r1-htc-20261114.build.log"
mkdir -p "$IMG_DIR" "$MIRROR"
say(){ printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }
DEF_SHA="$(sha256sum "$DEF" | awk '{print $1}')"
say "plan: def=$DEF def_sha256=$DEF_SHA sif=$SIF mirror=$MIRROR"
if [ "${1:-}" != "--build" ]; then say "dry plan only; re-run with --build"; exit 0; fi
say "inputs: $(sha256sum "$HERE"/uv.lock.a3fedbb "$HERE"/pyproject.toml.a3fedbb "$HERE"/tracks_freeze_65.txt "$HERE"/pip_freeze_trackp-cpu.txt 2>/dev/null | awk '{print $1" "$2}' | tr '\n' ' ')"
cd "$HERE" || exit 1
# 1) capability: a tiny scratch build tells us whether the plain (setuid) build works.
CAP="$IMG_DIR/_capability_test.sif"
rm -f "$CAP" 2>/dev/null || true
say "capability: apptainer build (plain) $CAP"
if apptainer build "$CAP" "$HERE/capability.def" >>"$LOG" 2>&1; then
  say "capability: plain build OK"
  MODE=plain
else
  say "capability: plain build failed; trying --fakeroot"
  if apptainer build --fakeroot "$CAP" "$HERE/capability.def" >>"$LOG" 2>&1; then
    say "capability: --fakeroot build OK"; MODE=fakeroot
  else
    say "STOP: neither plain nor --fakeroot apptainer build works; recorded as a question, stopping at S3"; exit 2
  fi
fi
# 2) real build into a temp name; rename only on success (no deletion of a failed attempt).
TMP="$SIF.tmp.$$"
say "build: apptainer build ($MODE) $TMP"
if [ "$MODE" = fakeroot ]; then apptainer build --fakeroot "$TMP" "$DEF" >>"$LOG" 2>&1; else apptainer build "$TMP" "$DEF" >>"$LOG" 2>&1; fi
RC=$?
if [ "$RC" -ne 0 ] || [ ! -s "$TMP" ]; then
  say "STOP: real build failed rc=$RC; temp file left as $TMP (not deleted)"; exit 3
fi
mv "$TMP" "$SIF" || { say "STOP: could not rename temp SIF"; exit 3; }
SIF_SHA="$(sha256sum "$SIF" | awk '{print $1}')"; SIF_BYTES="$(stat -c %s "$SIF")"
say "built: sif=$SIF sif_sha256=$SIF_SHA sif_bytes=$SIF_BYTES def_sha256=$DEF_SHA mode=$MODE"
apptainer inspect "$SIF" >>"$LOG" 2>&1
apptainer exec "$SIF" cat /opt/r1/VERSIONS.txt > "$IMG_DIR/r1-htc-20261114.VERSIONS.txt" 2>>"$LOG" \
  && say "versions: recorded $IMG_DIR/r1-htc-20261114.VERSIONS.txt"
cp -p "$SIF" "$MIRROR/" && say "mirror: copied to $MIRROR/$(basename "$SIF") ($(sha256sum "$MIRROR/$(basename "$SIF")" 2>/dev/null | awk '{print $1}'))"
printf 'def_sha256=%s\nsif_sha256=%s\nsif_bytes=%s\nmode=%s\n' "$DEF_SHA" "$SIF_SHA" "$SIF_BYTES" "$MODE" > "$IMG_DIR/r1-htc-20261114.identity"
say "identity: $IMG_DIR/r1-htc-20261114.identity"
exit 0
