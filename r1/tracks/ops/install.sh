#!/usr/bin/env bash
# Install the §11 ops scripts into <host>:<R>/bin, filling HOST_LABEL and GPU UUID per host.
# Also installs the STOP-1 diagnostic runner (ops/diag) as bin/trks-diag + bin/cache_prompt_diag.py,
# and syncs the committed launch scripts (ops/launch/*.sh) into <host>:<R>/launch.
# usage: install.sh <ssh-alias> <host-label> <gpu-uuid>
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
host=${1:?ssh alias}; label=${2:?host label}; uuid=${3:?gpu uuid}
case "$label" in TASL-2|TASL-7) ;; *) echo "install.sh: unexpected host label $label" >&2; exit 2 ;; esac
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for f in trks trks-run trks-servers trks-watch trks-status; do
  sed -e "s|@HOST_LABEL@|$label|g" -e "s|@GPU_ID@|$uuid|g" "$here/$f" > "$tmp/$f"
  bash -n "$tmp/$f"
done
# diagnostic runner (no host substitution; identical on both hosts)
cp "$here/diag/trks-diag" "$tmp/trks-diag"; bash -n "$tmp/trks-diag"
cp "$here/diag/cache_prompt_diag.py" "$tmp/cache_prompt_diag.py"
python3 -m py_compile "$tmp/cache_prompt_diag.py"
# committed launch scripts (identical on both hosts; host-specific ones carry their own node/host)
mkdir -p "$tmp/launch"; cp "$here"/launch/*.sh "$tmp/launch/"
for f in "$tmp"/launch/*.sh; do bash -n "$f"; done
scp -q "$tmp"/trks "$tmp"/trks-run "$tmp"/trks-servers "$tmp"/trks-watch "$tmp"/trks-status \
       "$tmp"/trks-diag "$tmp"/cache_prompt_diag.py "$host":/home/dowling/r1_tracks/bin/
scp -q "$tmp"/launch/*.sh "$host":/home/dowling/r1_tracks/launch/
ssh "$host" 'cd /home/dowling/r1_tracks/bin && chmod +x trks trks-run trks-servers trks-watch trks-status trks-diag && chmod +x /home/dowling/r1_tracks/launch/*.sh && sha256sum trks trks-run trks-servers trks-watch trks-status trks-diag cache_prompt_diag.py && echo "-- launch:" && cd /home/dowling/r1_tracks/launch && sha256sum *.sh && grep -E "^HOST_LABEL=|^GPU_ID=" /home/dowling/r1_tracks/bin/trks'
echo "installed on $host as $label ($uuid)"
