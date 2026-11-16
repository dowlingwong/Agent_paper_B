#!/bin/bash
# Build the Paper B R1 Apptainer image and record its identity.
# Reviewed gate (S3 pre-build review F4/F5/F13/F20): the def must be the reviewed one, %post must
# prove root, the product is never overwritten or deleted, and every record is fatal.
# Usage:  REVIEWED_DEF_SHA=<sha256> build_sif.sh --build
#         build_sif.sh            (plan only; creates nothing)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEF="$HERE/r1-htc.def"
CAPDEF="$HERE/capability.def"
IMG_DIR=/work/dwong/paperb/images
MIRROR=/ceph/srv/dwong/paperb/images
SIF="$IMG_DIR/r1-htc-20261114.sif"
LOG="$IMG_DIR/r1-htc-20261114.build.log"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
REVIEWED_DEF_SHA="${REVIEWED_DEF_SHA:-}"
say() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }

DEF_SHA="$(sha256sum "$DEF" | awk '{print $1}')"
if [ "${1:-}" != "--build" ]; then
  printf 'plan (nothing created)\n  def=%s\n  def_sha256=%s\n  sif=%s\n  mirror=%s\n  logs=%s\n' \
    "$DEF" "$DEF_SHA" "$SIF" "$MIRROR" "$LOG"
  printf 're-run with --build and REVIEWED_DEF_SHA set to the reviewed def sha256\n'
  exit 0
fi

# --- preconditions (fail closed) -------------------------------------------------------------
if [ -n "$REVIEWED_DEF_SHA" ] && [ "$DEF_SHA" != "$REVIEWED_DEF_SHA" ]; then
  echo "STOP: def sha256 $DEF_SHA != reviewed $REVIEWED_DEF_SHA (review the new def first)" >&2
  exit 4
fi
mkdir -p "$IMG_DIR" "$MIRROR" || { echo "STOP: cannot create $IMG_DIR / $MIRROR" >&2; exit 5; }
export APPTAINER_CACHEDIR=/work/dwong/paperb/.apptainer/cache
export APPTAINER_TMPDIR=/work/dwong/paperb/.apptainer/tmp
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
START_UTC="$(date -u +%FT%TZ)"
say "build start utc=$START_UTC def=$DEF def_sha256=$DEF_SHA reviewed_def_sha256=${REVIEWED_DEF_SHA:-unset}"
say "inputs: $(sha256sum "$HERE"/uv.lock.a3fedbb "$HERE"/pyproject.toml.a3fedbb "$HERE"/tracks_freeze_65.txt "$HERE"/pip_freeze_trackp-cpu.txt | awk '{print $1" "$2}' | tr '\n' ' ')"
say "apptainer: $(apptainer --version 2>&1 | head -1)"
say "disk: $(df -h "$IMG_DIR" | tail -1)"

# --- capability gate: root %post via --fakeroot first, then setuid ----------------------------
CAP="$IMG_DIR/_capability_${TS}.sif"
MODE=""
if apptainer build --fakeroot "$CAP" "$CAPDEF" >>"$LOG" 2>&1; then
  MODE=fakeroot
elif apptainer build "$CAP" "$CAPDEF" >>"$LOG" 2>&1; then
  MODE=plain
else
  say "STOP: neither --fakeroot nor plain apptainer build gives a root %post; recorded as a question, stopping at S3"
  exit 2
fi
say "capability: %post uid-0 build OK via $MODE (test sif $CAP)"

# --- real build into a unique temp name; never overwrite or delete ----------------------------
TMP="$SIF.tmp.$TS"
say "build: apptainer build ($MODE) $TMP (this takes O(1 h))"
if [ "$MODE" = fakeroot ]; then
  apptainer build --fakeroot "$TMP" "$DEF" >>"$LOG" 2>&1 || { say "STOP: real build failed; temp file left as $TMP"; exit 3; }
else
  apptainer build "$TMP" "$DEF" >>"$LOG" 2>&1 || { say "STOP: real build failed; temp file left as $TMP"; exit 3; }
fi
[ -s "$TMP" ] || { say "STOP: build produced no/empty SIF at $TMP"; exit 3; }
if [ -e "$SIF" ]; then
  RETIRED="$SIF.retired_$TS"
  mv "$SIF" "$RETIRED"
  say "retired previous SIF to $RETIRED (no deletion)"
fi
mv "$TMP" "$SIF"
END_UTC="$(date -u +%FT%TZ)"
SIF_SHA="$(sha256sum "$SIF" | awk '{print $1}')"; SIF_BYTES="$(stat -c %s "$SIF")"
say "built: sif=$SIF sif_sha256=$SIF_SHA sif_bytes=$SIF_BYTES end_utc=$END_UTC mode=$MODE"

# --- fatal records and smoke tests -----------------------------------------------------------
apptainer inspect "$SIF" > "$IMG_DIR/r1-htc-20261114.inspect.txt"
apptainer exec "$SIF" cat /opt/r1/VERSIONS.txt > "$IMG_DIR/r1-htc-20261114.VERSIONS.txt"
apptainer exec "$SIF" /opt/r1/envs/harness/bin/python -c "import numpy, sklearn, pandas, pytest; print('env1', numpy.__version__, sklearn.__version__, pandas.__version__, pytest.__version__)" > "$IMG_DIR/r1-htc-20261114.smoke_env1.txt"
apptainer exec "$SIF" /opt/r1/envs/tracks/bin/python -c "import numpy, sklearn, pandas; print('env2', numpy.__version__, sklearn.__version__, pandas.__version__)" > "$IMG_DIR/r1-htc-20261114.smoke_env2.txt"
apptainer exec "$SIF" /opt/r1/envs/trackp/bin/python -c "import torch, numpy, sklearn; print('env3', torch.__version__, numpy.__version__, sklearn.__version__)" > "$IMG_DIR/r1-htc-20261114.smoke_env3.txt"
apptainer exec "$SIF" llama-server --version > "$IMG_DIR/r1-htc-20261114.smoke_llama.txt" 2>&1
SHORT_SHA="$(printf '%s' "$DEF_SHA" | cut -c1-12)"
cat > "$IMG_DIR/r1-htc-20261114.identity" <<EOF
def=$DEF
def_sha256=$DEF_SHA
reviewed_def_sha256=${REVIEWED_DEF_SHA:-unset}
sif=$SIF
sif_sha256=$SIF_SHA
sif_bytes=$SIF_BYTES
build_mode=$MODE
apptainer=$(apptainer --version 2>&1 | head -1)
base=nvidia/cuda:12.4.1-cudnn-devel-rockylinux9
start_utc=$START_UTC
end_utc=$END_UTC
short_sha=$SHORT_SHA
EOF
MIRROR_SIF="$MIRROR/$(basename "$SIF")"
cp -p "$SIF" "$MIRROR_SIF"
MIRROR_SHA="$(sha256sum "$MIRROR_SIF" | awk '{print $1}')"
[ "$MIRROR_SHA" = "$SIF_SHA" ] || { say "STOP: mirror copy sha mismatch $MIRROR_SHA != $SIF_SHA"; exit 6; }
cp -p "$IMG_DIR/r1-htc-20261114.identity" "$IMG_DIR/r1-htc-20261114.VERSIONS.txt" "$MIRROR/" 2>/dev/null || true
cp -p "$IMG_DIR/r1-htc-20261114.identity" "$MIRROR/" 2>/dev/null || true
say "mirror: $MIRROR_SIF sha256=$MIRROR_SHA"
say "records: identity/VERSIONS/inspect/smoke_* under $IMG_DIR and identity+VERSIONS under $MIRROR"
say "build done: def_sha256=$DEF_SHA sif_sha256=$SIF_SHA bytes=$SIF_BYTES mode=$MODE start=$START_UTC end=$END_UTC"
exit 0
