#!/bin/bash
set -u
umask 077
set -o noclobber
remote=/private/tmp/b1-stop-census-20261108.remote.sh
expected=078b6d653189e8d0c2dee48f13499d5af06f33e9956eb30da6936807556b8a6f
actual=$(shasum -a 256 "$remote") || exit 1
[ "${actual%% *}" = "$expected" ] || { printf 'STOP: remote script hash mismatch\n' >&2; exit 1; }
out=$(mktemp -d /private/tmp/paper-b-stop-census-20261108.XXXXXXXX) || exit 1
printf 'CAPTURE=%s\n' "$out" || exit 1
if ! ( : > "$out/ssh.log" && : > "$out/ssh.rc" ); then
    printf 'STOP: cannot create exclusive capture\n' >&2
    exit 1
fi
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 tasl7 'env -i PATH=/usr/bin:/bin /bin/bash -s' < "$remote" >> "$out/ssh.log" 2>&1
rc=$?
if ! printf 'SSH_EXIT=%s\n' "$rc" >> "$out/ssh.log"; then
    printf 'STOP: cannot append SSH receipt\n' >&2; exit 1
fi
if ! printf '%s\n' "$rc" >> "$out/ssh.rc"; then
    printf 'STOP: cannot write SSH rc\n' >&2; exit 1
fi
if ! shasum -a 256 "$out/ssh.log" "$out/ssh.rc"; then
    printf 'STOP: cannot hash capture\n' >&2; exit 1
fi
if [ "$rc" -ne 0 ] || ! grep -Eq '^B1_CENSUS_END matches=[0-9]+ raced_or_unreadable=[0-9]+$' "$out/ssh.log"; then
    printf 'STOP: SSH failure or incomplete census\n' >&2; exit 1
fi
