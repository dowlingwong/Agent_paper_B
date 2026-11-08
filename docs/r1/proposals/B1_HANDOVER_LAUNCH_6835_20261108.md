# B1 6835 exact handover and one launch — conditional proposal

**Review only; no host action.** This fills accepted forward operator template `4783fc60` (review `cee491f609dd5b3d24d5f3622fb6a41688d64022`) for exact candidate `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`, run ID `6835_20261108_a`, pinned harness `a3fedbb`, and the same clean venv as native preflight. It does not modify that candidate. The actual receive, author gate and native server/lease preflight must each be independently accepted first; no success is presumed. Apply all current O2 and author decisions, including the 7 Nov no-cgroup process handling, no preemption, retention and STOP rule. No B2, X.7 or sweep 2. No command may be executed before fresh independent review of this exact plan and all applicable prerequisites.

Before marker creation, prepare a clean separate status checkout of feature branch `mac-b1-20261107`, check its remote tip and independently review this exact intended append; its commit and actual remote verification follow marker creation. Refresh and record STATUS, watcher, collectors, lock, GPU, free disk/inodes/RAM and P.3a; establish the ordinary watcher behavior, intended STOP touches, cooperative no-new-starts, P.3a safe pause/absence and a separately reviewed no-deletion restoration route. Do not signal or alter other operators' work; inability to establish a safe handover means STOP. Handover follows accepted O2 `B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` and its independent reviews; watcher actual effects must be observed after marker creation. Marker `/home/dowling/r1_locks/trackx_evidence.active` is the Track P authority. Never infer a complete handover solely from the feature-branch status.

Exact reviewed STATUS append (date must be reconfirmed at execution; if date changes prepare and review the changed append):

```markdown
## 2026-11-08 — Track X B1 running

Run: `6835_20261108_a`; reviewed checkout HEAD: `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`.
```

Publish only the independently reviewed append from the separate clean status checkout after marker creation, commit as author Dowling Wong and committer Codex, push normally to `refs/heads/mac-b1-20261107`, verify the remote SHA equals that commit. If a branch advances, publication fails or state is uncertain, preserve marker and evidence and STOP; no force, overwrite or automatic retry. The exact branch base and resulting commit SHA are site-time facts to verify, not invented in advance.

The following exact local file contents and SHA-256 are conditional. On host, `marker` first creates only its unique B1-owned handover directory and empty status receipt, then uses accepted O2 marker create; it checks clean exact HEAD. The marker receipt and all files persist at failure. Start and receipt are transferred only into that new directory with exclusive creation, their hashes checked against the literals immediately before the one tmux send. Verify transferred bytes and ownership, actual tmux version and socket behavior independently. The operator must use an independently reviewed exclusive transfer method; no transfer occurs here. Run marker once only after the prerequisite checks above; then observe safe pause, publish and verify STATUS, confirm launch conditions, and run tmux block exactly once. No reruns after failure or uncertain SSH status. All commands run in a clean environment with `HOME=/home/dowling` and fixed `PATH=/usr/bin:/bin`; launch sets its approved venv and explicit variables.

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

SHA-256 `94f63b2622dd810fd735e2b19a728fbd2a7f84f5396f4a5ffb6e48d42604722c`.

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
python3 "$PAPER/r1/scripts/b1_o2_marker.py" create --lock-dir /home/dowling/r1_locks --status "$STATUS" --run-id "$RUN_ID" --head "$HEAD" > "$RUN_DIR/marker-receipt.json"
```

Monitor every 30 minutes or sooner if needed, appending new B1-owned observations of UTC, HEAD, run, identities, progress, GPU, RAM and disk/inodes; preserve other work. On STOP, stop starting new work, stop owned workers and B1 server via existing paths, preserve all output, logs, ledger, marker and tmux, publish STATUS, and record shutdown writes; do not automatically change or retry. Only after verified normal completion may the exact O2 identity-bound no-replace marker retirement and separately reviewed restoration be performed. The process exit alone is not complete-batch acceptance.
