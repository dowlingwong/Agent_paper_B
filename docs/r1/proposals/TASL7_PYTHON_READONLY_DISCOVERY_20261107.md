# TASL-7 Python venv discovery — read-only engineering candidate

AI-assisted (Codex). **Candidate; fresh independent review required before execution.** This is a bounded informational probe to find a possible venv for the separately reviewed real-worker preflight. It does not install, update or create an environment, use a GPU, start a model, acquire a lease, modify another track, or authorize B1. The 21:59 UTC census is only a point-in-time observation; apply current host, STATUS, lock and no-preemption instructions before any site action. The probe checks only four explicit likely locations and `python3` path metadata; failure to find one does not establish that no suitable venv exists elsewhere.

No remote output file is intentionally created. Imports are executed with `-I -S -B`, no user site, no `.pth` processing, a scrubbed environment, nonwritable configuration/cache destinations and one BLAS/OpenMP thread. `-S` plus the explicitly selected venv `site-packages` supports an informational dependency check without normal startup hooks; it is not the exact normal venv startup used by production. Python/library initialization may have unanticipated side effects and filesystem reads can update access times; these commands are not a system-call-level proof that no remote filesystem metadata or bytes changed. If the import behavior cannot be accepted within the author's no-write constraint, do not run the import part. Record failures; do not retry automatically. No argv, environment contents or secret files are printed. The transcript remains private until reviewed and redacted.

On the Mac, after review, run once using an exclusively created private local directory. The remote script writes to stdout only. The fixed `timeout` bounds each interpreter invocation; it only controls the invocation it starts. A failed query or missing `timeout` is NOT CHECKABLE, not an invitation to install anything. Never copy or alter a pre-existing environment.

```bash
set -u
umask 077
DISCOVERY_DIR=$(mktemp -d /private/tmp/paper-b-tasl7-python-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$DISCOVERY_DIR/discovery.txt" 2>&1 <<'REMOTE'
set -u
printf '%s\n' 'UTC / HOST'
date -u; printf 'date_rc=%s\n' "$?"
hostname; printf 'hostname_rc=%s\n' "$?"
printf '%s\n' 'PATH python3 (metadata only)'
command -v python3; printf 'command_rc=%s\n' "$?"
if ! command -v timeout >/dev/null 2>&1; then
  printf '%s\n' 'STOP: timeout unavailable; imports NOT CHECKABLE'
  exit 2
fi
for venv in "$HOME/exam-x/work/autoresearch_harness/.venv" \
            "$HOME/exam-x/work/agent_paper_B/.venv" \
            "$HOME/exam-x/.venv" "$HOME/autoresearch_harness/.venv"; do
  printf '\nCANDIDATE %s\n' "$venv"
  if ! test -f "$venv/pyvenv.cfg" || ! test -x "$venv/bin/python"; then
    printf '%s\n' 'MISSING_OR_UNUSABLE'
    continue
  fi
  printf 'python_realpath='; readlink -f "$venv/bin/python"; printf 'realpath_rc=%s\n' "$?"
  if test -x "$venv/bin/python3"; then
    printf 'python3_realpath='; readlink -f "$venv/bin/python3"; printf 'python3_realpath_rc=%s\n' "$?"
  else
    printf '%s\n' 'python3_MISSING_OR_NOT_EXECUTABLE'
  fi
  found=0
  for site in "$venv"/lib/python*/site-packages; do
    test -d "$site" || continue
    found=1
    printf 'SITE %s\n' "$site"
    env -i HOME=/dev/null XDG_CACHE_HOME=/dev/null PYTHONDONTWRITEBYTECODE=1 \
      PATH=/usr/bin:/bin OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
      CUDA_VISIBLE_DEVICES='' timeout --signal=TERM --kill-after=2s 15s \
      "$venv/bin/python" -I -S -B -c '
import sys
sys.path.insert(0, sys.argv[1])
print("interpreter", sys.executable, sys.version.replace("\\n", " "))
for name in ("pytest", "numpy", "sklearn"):
    try:
        module = __import__(name)
        print("IMPORT_OK", name, getattr(module, "__version__", "unknown"), getattr(module, "__file__", "unknown"))
    except Exception as exc:
        print("IMPORT_FAILED", name, type(exc).__name__)
' "$site"
    printf 'import_rc=%s\n' "$?"
  done
  test "$found" -eq 1 || printf '%s\n' 'SITE_PACKAGES_NOT_FOUND'
done
REMOTE
ssh_rc=$?
printf 'ssh_exit=%s\n' "$ssh_rc" > "$DISCOVERY_DIR/ssh-status.txt"
shasum -a 256 "$DISCOVERY_DIR/discovery.txt" "$DISCOVERY_DIR/ssh-status.txt"
printf 'SSH exit: %s; inspect private transcript and individual outcomes.\n' "$ssh_rc"
```

The operator checks that each successful module actually came from the candidate environment, checks `python`/`python3` logical and resolved paths, and retains the private transcript and reviewed redacted summary. `IMPORT_OK` under `-S` is not a production venv qualification or proof that the worker `python3` resolves to the same interpreter and venv prefix. The separately reviewed worker preflight must repeat its normal, exact PATH and prefix checks, as well as verify the pinned sources and test evidence. A missing package, unexpected path, timeout, SSH loss or no viable candidate is STOP for that candidate; preserve evidence and proceed only through separately reviewed next steps. Do not alter author decisions or automatically run the worker.
