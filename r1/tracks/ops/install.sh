#!/usr/bin/env bash
# Install the §11 ops scripts into <host>:<R>/bin, filling HOST_LABEL and GPU UUID per host.
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
scp -q "$tmp"/trks "$tmp"/trks-run "$tmp"/trks-servers "$tmp"/trks-watch "$tmp"/trks-status "$host":/home/dowling/r1_tracks/bin/
ssh "$host" 'chmod +x /home/dowling/r1_tracks/bin/trks /home/dowling/r1_tracks/bin/trks-run /home/dowling/r1_tracks/bin/trks-servers /home/dowling/r1_tracks/bin/trks-watch /home/dowling/r1_tracks/bin/trks-status; cd /home/dowling/r1_tracks/bin && sha256sum trks trks-run trks-servers trks-watch trks-status && grep -E "^HOST_LABEL=|^GPU_ID=" trks'
echo "installed on $host as $label ($uuid)"
