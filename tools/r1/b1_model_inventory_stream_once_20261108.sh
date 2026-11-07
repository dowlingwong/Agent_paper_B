#!/bin/bash
# DRAFT: do not run until explicit author approval and independent review.
set -u
set -o pipefail
umask 077
SOURCE=/private/tmp/paper-b-model-inventory-io-plan-20261108
SCRIPT="$SOURCE/tools/r1/b1_model_inventory_20261108.py"
MANIFEST_FILE=/private/tmp/paper-b-model-inventory-manifest-20261108.txt
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = a62999240234de4f97bb282d9c0df60bf571551fcff359095b3883e263256b82 ] || exit 1
[ "$(shasum -a 256 "$MANIFEST_FILE" | awk '{print $1}')" = dab132c24fbebb2b54b3b9608c1c912e342d324aa92e1450106d22c883f87713 ] || exit 1
cd "$SOURCE" || exit 1
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_OPTIONAL_LOCKS=0
[ "$(git --no-optional-locks rev-parse HEAD)" = a6de91031f1f8ec56fd8b01be2d5cd6d0111c5a0 ] || exit 1
STATUS=$(git --no-optional-locks status --porcelain --untracked-files=all) || exit 1
[ -z "$STATUS" ] || exit 1
GENERATED=$(python3 -B "$SCRIPT" prepare) || exit 1
MANIFEST=$(cat "$MANIFEST_FILE") || exit 1
[ "$GENERATED" = "$MANIFEST" ] || exit 1
CAP=$(mktemp -d /private/tmp/paper-b-model-inventory-stream-20261108.XXXXXXXX) || exit 1
printf 'PRIVATE_CAPTURE=%s\n' "$CAP"
python3 -B - "$SCRIPT" "$MANIFEST_FILE" "$CAP/payload.json" <<'PY' || exit 1
import base64,json,sys
from pathlib import Path
code=Path(sys.argv[1]).read_bytes(); manifest=Path(sys.argv[2]).read_text().strip()
with Path(sys.argv[3]).open('x',encoding='utf-8') as f:
 json.dump({'script':base64.b64encode(code).decode('ascii'),'manifest':manifest},f,separators=(',',':'))
PY
REMOTE=$(cat <<'REMOTE_COMMAND'
set -eu
export PATH=/usr/bin:/bin
if command -v ionice >/dev/null 2>&1 && command -v nice >/dev/null 2>&1; then
 printf 'IO_MODE=ionice_idle_nice_19\n'; set -- nice -n 19 ionice -c 3
elif command -v ionice >/dev/null 2>&1; then
 printf 'IO_MODE=ionice_idle_no_nice\n'; set -- ionice -c 3
elif command -v nice >/dev/null 2>&1; then
 printf 'IO_MODE=nice_19_no_ionice\n'; set -- nice -n 19
else
 printf 'IO_MODE=unmodified_no_ionice_or_nice\n'; set --
fi
exec env -i HOME=/home/dowling PATH=/usr/bin:/bin "$@" /usr/bin/python3 -I -B -c 'import base64,hashlib,json,sys; p=json.load(sys.stdin); code=base64.b64decode(p["script"],validate=True); m=p["manifest"]; assert hashlib.sha256(code).hexdigest()=="a62999240234de4f97bb282d9c0df60bf571551fcff359095b3883e263256b82"; assert hashlib.sha256((m+"\n").encode()).hexdigest()=="dab132c24fbebb2b54b3b9608c1c912e342d324aa92e1450106d22c883f87713"; sys.argv=["b1_model_inventory","host",m]; exec(compile(code,"<reviewed-inventory>","exec"),{"__name__":"__main__"})'
REMOTE_COMMAND
) || exit 1
set -C
if ! exec 3> "$CAP/inventory.log"; then exit 1; fi
if ssh -o BatchMode=yes -o ConnectTimeout=12 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 tasl7 "$REMOTE" < "$CAP/payload.json" >&3 2>&1; then ssh_rc=0; else ssh_rc=$?; fi
if ! printf '\nSSH_EXIT=%s\n' "$ssh_rc" >&3; then exit 1; fi
if ! printf '%s\n' "$ssh_rc" > "$CAP/inventory.rc"; then exit 1; fi
printf 'SSH_EXIT=%s\n' "$ssh_rc"
[ "$ssh_rc" = 0 ] || exit 1
grep -qx 'B1_MODEL_INVENTORY_PASS' "$CAP/inventory.log" || exit 1
grep -qx 'SSH_EXIT=0' "$CAP/inventory.log" || exit 1
shasum -a 256 "$CAP/payload.json" "$CAP/inventory.log" "$CAP/inventory.rc"
printf 'INVENTORY_FOR_REVIEW=%s\n' "$CAP"
