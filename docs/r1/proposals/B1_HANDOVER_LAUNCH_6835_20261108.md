# B1 6835 exact handover and one launch — conditional proposal

**Review only; no host action.** This fills accepted forward operator template `4783fc60` (review `cee491f609dd5b3d24d5f3622fb6a41688d64022`) for exact candidate `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`, run ID `6835_20261108_a`, pinned harness `a3fedbb`, and the same clean venv as native preflight. It does not modify that candidate. The actual receive, author gate and native server/lease preflight must each be independently accepted first; no success is presumed. Apply all current O2 and author decisions, including the 7 Nov no-cgroup process handling, no preemption, retention and STOP rule. No B2, X.7 or sweep 2. No command may be executed before fresh independent review of this exact plan and all applicable prerequisites.

Before marker creation, prepare a clean separate status checkout of feature branch `mac-b1-20261107`, check its remote tip and independently review this exact intended append; its commit and actual remote verification follow marker creation. Refresh and record STATUS, watcher, collectors, lock, GPU, free disk/inodes/RAM and P.3a; establish the ordinary watcher behavior, intended STOP touches, cooperative no-new-starts, P.3a safe pause/absence and a separately reviewed no-deletion restoration route. Do not signal or alter other operators' work; inability to establish a safe handover means STOP. Handover follows accepted O2 `B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` and its independent reviews; watcher actual effects must be observed after marker creation. Marker `/home/dowling/r1_locks/trackx_evidence.active` is the Track P authority. Never infer a complete handover solely from the feature-branch status.

Exact reviewed STATUS append (date must be reconfirmed at execution; if date changes prepare and review the changed append):

```markdown
## 2026-11-08 — Track X B1 running

Run: `6835_20261108_a`; reviewed checkout HEAD: `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`.
```

Publish only the independently reviewed append from the separate clean status checkout after marker creation, commit as author Dowling Wong and committer Codex, push normally to `refs/heads/mac-b1-20261107`, verify the remote SHA equals that commit. If a branch advances, publication fails or state is uncertain, preserve marker and evidence and STOP; no force, overwrite or automatic retry. The exact branch base and resulting commit SHA are site-time facts to verify, not invented in advance.

The following exact local file contents and SHA-256 are conditional. On host, `marker` first creates only its unique B1-owned handover directory and empty status receipt, then uses accepted O2 marker create; it checks clean exact HEAD. The marker receipt and all files persist at failure. Start and receipt are transferred only into that new directory with exclusive creation, their hashes checked against the literals immediately before the one tmux send. Verify transferred bytes and ownership, actual tmux version and socket behavior independently. The exact exclusive transfer command below requires independent review; no transfer occurs here. Run marker once only after the prerequisite checks above; immediately publish and verify STATUS, then observe watcher and P.3a safe pause, confirm launch conditions, transfer the scripts, and run the tmux block exactly once. No reruns after failure or uncertain SSH status. All commands run in a clean environment with `HOME=/home/dowling` and fixed `PATH=/usr/bin:/bin`; launch sets its approved venv and explicit variables.

## start — `/private/tmp/b1-6835-start-20261108.sh`

SHA-256 `c5559d5f52238c4fb640dd3c448fc8dfd40e031e80a2f7ce6040a841110437e2`.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
HEAD=68357d3d8cd0c9f301005e483a49ecfd05f6e5bb
RUN_ID=6835_20261108_a
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
case "$HEAD" in *[!0-9a-f]*|'') die 'bad reviewed HEAD';; esac
[ "${#HEAD}" -eq 40 ] || die 'wrong HEAD length'
case "$RUN_ID" in *[!a-zA-Z0-9_-]*|'') die 'bad run ID';; esac
PAPER="/home/dowling/r1_b1_engineering/b1_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
RUN_DIR="/home/dowling/r1_b1_engineering/b1_handover_${RUN_ID}"
BATCH="/home/dowling/exam-x/work/b1_${RUN_ID}"
[ ! -L "$BATCH" ] && [ ! -e "$BATCH" ] || die 'batch path exists'
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || die 'paper checkout missing or symlink'
[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ] || die 'harness missing or symlink'
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || die 'run directory missing or symlink'
[ -x "$PY" ] || die 'Python unavailable'
cd "$PAPER" || die 'cannot enter checkout'
export GIT_OPTIONAL_LOCKS=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export AR_HARNESS_ROOT="$HARNESS" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
CURRENT=$(git --no-optional-locks rev-parse HEAD) || die 'cannot read HEAD'
[ "$CURRENT" = "$HEAD" ] || die 'HEAD mismatch'
STATUS=$(git --no-optional-locks status --porcelain --untracked-files=all) || die 'cannot read checkout status'
[ -z "$STATUS" ] || die 'checkout is dirty'
exec "$PY" -B -m r1.scripts.exam_runner b1 --config "$PAPER/r1/scripts/configs/exam_b1_v2.json" --out "$BATCH"
```

## receipt — `/private/tmp/b1-6835-receipt-20261108.sh`

SHA-256 `4c48fc579d97873f4ce7043a83bcd8ca27bdc4fd1c12175533e8fa9993ca119b`.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a
set -C
if ! exec 3> "$RUN_DIR/b1.log"; then printf 'STOP: cannot create b1.log\n' >&2; exit 1; fi
if /bin/bash "$RUN_DIR/start.sh" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nB1_EXIT=%s\n' "$rc" >&3 || { printf 'STOP: cannot write log footer\n' >&2; exit 1; }
printf '%s\n' "$rc" > "$RUN_DIR/b1.exit" || { printf 'STOP: cannot write exit file\n' >&2; exit 1; }
exit "$rc"
```

## tmux — `/private/tmp/b1-6835-tmux-20261108.sh`

SHA-256 `ed589c8d742050f9654c0d9ceb494a6fce813b6c035b2001a6521bdc46aa52ce`.

```bash
set -eu
umask 077
RUN_ID=6835_20261108_a
case "$RUN_ID" in *[!a-zA-Z0-9_-]*|'') exit 1;; esac
RUN_DIR="/home/dowling/r1_b1_engineering/b1_handover_${RUN_ID}"
SOCKET="$RUN_DIR/tmux.sock"
SESSION="b1_${RUN_ID}"
START_SHA=c5559d5f52238c4fb640dd3c448fc8dfd40e031e80a2f7ce6040a841110437e2
RECEIPT_SHA=4c48fc579d97873f4ce7043a83bcd8ca27bdc4fd1c12175533e8fa9993ca119b
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || exit 1
[ -f "$RUN_DIR/start.sh" ] && [ ! -L "$RUN_DIR/start.sh" ] || exit 1
[ -f "$RUN_DIR/receipt.sh" ] && [ ! -L "$RUN_DIR/receipt.sh" ] || exit 1
[ ! -e "$SOCKET" ] && [ ! -L "$SOCKET" ] || exit 1
tmux -S "$SOCKET" new-session -d -s "$SESSION" '/bin/bash --noprofile --norc -i'
tmux -S "$SOCKET" set-option -s exit-empty off
tmux -S "$SOCKET" set-option -w -t "$SESSION:0" remain-on-exit on
tmux -S "$SOCKET" has-session -t "=$SESSION"
[ "$(sha256sum "$RUN_DIR/start.sh" | awk '{print $1}')" = "$START_SHA" ] || exit 1
[ "$(sha256sum "$RUN_DIR/receipt.sh" | awk '{print $1}')" = "$RECEIPT_SHA" ] || exit 1
tmux -S "$SOCKET" send-keys -t "$SESSION:0.0" "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash '$RUN_DIR/receipt.sh'" C-m
```

## marker — `/private/tmp/b1-6835-marker-20261108.sh`

SHA-256 `1c9a67463825ede1d53d36fea93e55d6f14b7814508279673c4753bf759ef90b`.

```bash
set -eu
umask 077
HEAD=68357d3d8cd0c9f301005e483a49ecfd05f6e5bb
RUN_ID=6835_20261108_a
PAPER=/home/dowling/r1_b1_engineering/b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb/paper
RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a
STATUS="$RUN_DIR/status-receipt.md"
[ ! -e "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || exit 1
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || exit 1
[ "$(git --no-optional-locks -C "$PAPER" rev-parse HEAD)" = "$HEAD" ] || exit 1
STATE=$(git --no-optional-locks -C "$PAPER" status --porcelain --untracked-files=all) || exit 1
[ -z "$STATE" ] || exit 1
mkdir -m 700 "$RUN_DIR"
set -C
: > "$STATUS"
TZ=Europe/Berlin python3 "$PAPER/r1/scripts/b1_o2_marker.py" create --lock-dir /home/dowling/r1_locks --status "$STATUS" --run-id "$RUN_ID" --head "$HEAD" > "$RUN_DIR/marker-receipt.json"
```

Monitor every 30 minutes or sooner if needed, appending new B1-owned observations of UTC, HEAD, run, identities, progress, GPU, RAM and disk/inodes; preserve other work. On STOP, stop starting new work, stop owned workers and B1 server via existing paths, preserve all output, logs, ledger, marker and tmux, publish STATUS, and record shutdown writes; do not automatically change or retry. Only after verified normal completion may the exact O2 identity-bound no-replace marker retirement and separately reviewed restoration be performed. The process exit alone is not complete-batch acceptance.

## Exclusive script transfer — conditional

`/private/tmp/b1-6835-transfer-20261108.sh`, SHA-256 `a174d69b702547fdb16ca2492b901b931da814dbe91e28a4606e85eebbefe93a`, uses separate SSH calls and fresh private log and rc for each file. Remote path components are opened without following symlinks; each file is created with `O_EXCL|O_NOFOLLOW`, written once and reread for SHA verification. Partial files and captures remain; the second transfer is not attempted if the first fails, and no transfer is repeated on failure or unknown status. Review and verify the script SHA before a single execution as a local file. This is not launch.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
OUT=$(mktemp -d /private/tmp/paper-b-6835-launch-transfer-20261108.XXXXXXXX) || exit 1
set -C
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
transfer() {
  name=$1
  file=$2
  expected=$3
  [ "$(shasum -a 256 "$file" | awk '{print $1}')" = "$expected" ] || return 1
  if ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c 'import base64;exec(base64.b64decode(\"aW1wb3J0IHN5cyxvcyxoYXNobGliCm5hbWUsZXhwZWN0ZWQ9c3lzLmFyZ3ZbMTpdCmFzc2VydCBuYW1lIGluICgic3RhcnQuc2giLCAicmVjZWlwdC5zaCIpCmQ9c3lzLnN0ZGluLmJ1ZmZlci5yZWFkKDEwMDAwMSkKYXNzZXJ0IGxlbihkKTw9MTAwMDAwIGFuZCBoYXNobGliLnNoYTI1NihkKS5oZXhkaWdlc3QoKT09ZXhwZWN0ZWQKZmQ9b3Mub3BlbigiLyIsb3MuT19SRE9OTFl8b3MuT19ESVJFQ1RPUlkpCmZvciBwYXJ0IGluICgiaG9tZSIsImRvd2xpbmciLCJyMV9iMV9lbmdpbmVlcmluZyIsImIxX2hhbmRvdmVyXzY4MzVfMjAyNjExMDhfYSIpOgogbmV3PW9zLm9wZW4ocGFydCxvcy5PX1JET05MWXxvcy5PX0RJUkVDVE9SWXxvcy5PX05PRk9MTE9XLGRpcl9mZD1mZCkKIG9zLmNsb3NlKGZkKTsgZmQ9bmV3Cm91dD1vcy5vcGVuKG5hbWUsb3MuT19XUk9OTFl8b3MuT19DUkVBVHxvcy5PX0VYQ0x8b3MuT19OT0ZPTExPVywwbzYwMCxkaXJfZmQ9ZmQpCnZpZXc9bWVtb3J5dmlldyhkKQp3aGlsZSB2aWV3Ogogbj1vcy53cml0ZShvdXQsdmlldykKIGFzc2VydCBuPjAKIHZpZXc9dmlld1tuOl0Kb3MuY2xvc2Uob3V0KQpjaGVjaz1vcy5vcGVuKG5hbWUsb3MuT19SRE9OTFl8b3MuT19OT0ZPTExPVyxkaXJfZmQ9ZmQpCmg9aGFzaGxpYi5zaGEyNTYoKQp3aGlsZSBUcnVlOgogYj1vcy5yZWFkKGNoZWNrLDY1NTM2KQogaWYgbm90IGI6IGJyZWFrCiBoLnVwZGF0ZShiKQpvcy5jbG9zZShjaGVjayk7IG9zLmNsb3NlKGZkKQphc3NlcnQgaC5oZXhkaWdlc3QoKT09ZXhwZWN0ZWQKcHJpbnQoIlRSQU5TRkVSX1BBU1MiLG5hbWUsZXhwZWN0ZWQpCg==\"))' $name $expected" < "$file" > "$OUT/$name.log" 2>&1; then rc=0; else rc=$?; fi
  printf '\nSSH_EXIT=%s\n' "$rc" >> "$OUT/$name.log" || return 1
  printf '%s\n' "$rc" > "$OUT/$name.rc" || return 1
  [ "$rc" -eq 0 ] || return "$rc"
  grep -Fx "TRANSFER_PASS $name $expected" "$OUT/$name.log" >/dev/null || return 1
}
transfer start.sh /private/tmp/b1-6835-start-20261108.sh c5559d5f52238c4fb640dd3c448fc8dfd40e031e80a2f7ce6040a841110437e2 || exit 1
transfer receipt.sh /private/tmp/b1-6835-receipt-20261108.sh 4c48fc579d97873f4ce7043a83bcd8ca27bdc4fd1c12175533e8fa9993ca119b || exit 1
shasum -a 256 "$OUT/start.sh.log" "$OUT/start.sh.rc" "$OUT/receipt.sh.log" "$OUT/receipt.sh.rc"
printf 'TRANSFER_CAPTURE_COMPLETE=%s\n' "$OUT"
```

The encoded remote Python is exactly the following (`/private/tmp/b1-6835-transfer-remote-20261108.py`, SHA-256 `b8e11af70dad7dd678151f50958e7ecff605ae4d3af1d29f90d090087a30a01c`):

```python
import sys,os,hashlib
name,expected=sys.argv[1:]
assert name in ("start.sh", "receipt.sh")
d=sys.stdin.buffer.read(100001)
assert len(d)<=100000 and hashlib.sha256(d).hexdigest()==expected
fd=os.open("/",os.O_RDONLY|os.O_DIRECTORY)
for part in ("home","dowling","r1_b1_engineering","b1_handover_6835_20261108_a"):
 new=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
 os.close(fd); fd=new
out=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
view=memoryview(d)
while view:
 n=os.write(out,view)
 assert n>0
 view=view[n:]
os.close(out)
check=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
h=hashlib.sha256()
while True:
 b=os.read(check,65536)
 if not b: break
 h.update(b)
os.close(check); os.close(fd)
assert h.hexdigest()==expected
print("TRANSFER_PASS",name,expected)
```

## Single-action SSH capture wrapper

Use `/private/tmp/b1-6835-action-wrapper-20261108.sh` (SHA-256 `ff8b615346b62a4ebcb15992f99d3cb8ddf3aef8cb6c20c03c6c387589ce6142`) only after this exact filled plan and current prerequisites are independently accepted. Run `bash /private/tmp/b1-6835-action-wrapper-20261108.sh marker` once for marker creation, and only after the required STATUS publication, verified handover and transfer, run `bash /private/tmp/b1-6835-action-wrapper-20261108.sh tmux` once. It reads the reviewed remote block from a file, hashes it, uses clean environment, creates a distinct private capture and records actual SSH exit in log and rc. Marker uses `TZ=Europe/Berlin`; if the date differs from the proposed STATUS date, independently review the corrected STATUS append before marker. Missing capture, nonzero exit or uncertain state is STOP with no retry.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
case "${1-}" in
 marker) SCRIPT=/private/tmp/b1-6835-marker-20261108.sh; EXPECTED=1c9a67463825ede1d53d36fea93e55d6f14b7814508279673c4753bf759ef90b ;;
 tmux) SCRIPT=/private/tmp/b1-6835-tmux-20261108.sh; EXPECTED=ed589c8d742050f9654c0d9ceb494a6fce813b6c035b2001a6521bdc46aa52ce ;;
 *) printf 'STOP: expected marker or tmux\n' >&2; exit 1 ;;
esac
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-6835-action-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s ACTION=%s\n' "$OUT" "$1"
if ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 'exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash -s' < "$SCRIPT" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc"
printf 'SSH_EXIT=%s PRIVATE_CAPTURE=%s ACTION=%s\n' "$rc" "$OUT" "$1"
exit "$rc"
```
