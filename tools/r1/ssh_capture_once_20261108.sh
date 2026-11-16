#!/bin/bash
# Generic one-shot SSH capture; stdout/stderr and exit evidence are exclusive.
set -u
set -o pipefail
set -C
umask 077
if [ "$#" -lt 4 ]; then printf 'usage: LOG RC_FILE HOST REMOTE_COMMAND...\n' >&2; exit 64; fi
log=$1
rcfile=$2
host=$3
shift 3
if [ -e "$rcfile" ] || [ -L "$rcfile" ]; then printf 'STOP: rc path exists\n' >&2; exit 73; fi
if [ -e "$log" ] || [ -L "$log" ]; then printf 'STOP: log path exists\n' >&2; exit 73; fi
if ! exec 3> "$log"; then printf 'STOP: log exists or cannot be created\n' >&2; exit 73; fi
if ssh -n -o BatchMode=yes -o ConnectTimeout=12 "$host" "$@" </dev/null >&3 2>&1; then ssh_rc=0; else ssh_rc=$?; fi
if ! printf '\nSSH_EXIT=%s\n' "$ssh_rc" >&3; then printf 'STOP: cannot write SSH footer\n' >&2; exit 74; fi
if ! printf '%s\n' "$ssh_rc" > "$rcfile"; then printf 'STOP: cannot write SSH rc\n' >&2; exit 74; fi
printf 'SSH_EXIT=%s LOG=%s RC=%s\n' "$ssh_rc" "$log" "$rcfile"
exit "$ssh_rc"
