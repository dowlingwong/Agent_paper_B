#!/bin/bash
set -u
umask 077
remote=/private/tmp/b1-stop-census-20261108.remote.sh
expected=078b6d653189e8d0c2dee48f13499d5af06f33e9956eb30da6936807556b8a6f
actual=$(shasum -a 256 "$remote") || exit 1
[ "${actual%% *}" = "$expected" ] || { printf 'STOP: remote script hash mismatch\n' >&2; exit 1; }
out=$(mktemp -d /private/tmp/paper-b-stop-census-20261108.XXXXXXXX) || exit 1
printf 'CAPTURE=%s\n' "$out"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 tasl7 'env -i PATH=/usr/bin:/bin /bin/bash -s' < "$remote" > "$out/ssh.log" 2>&1
rc=$?
printf 'SSH_EXIT=%s\n' "$rc" >> "$out/ssh.log"
printf '%s\n' "$rc" > "$out/ssh.rc"
shasum -a 256 "$out/ssh.log" "$out/ssh.rc"
exit "$rc"
