# TASL-7 bounded Python discovery: historical exam venv and system Python

AI-assisted (Codex). **Candidate for fresh independent review, not a site observation or B1 launch.** The prior reviewed 22:05 UTC probe found four candidates unusable and observed `/usr/bin/python3` on PATH; it did not check system packages. The retained historical exam transport evidence `reports/exam_phase2_20261026/transport_parallelism_change.json` and `transport_migration.json` references `/home/dowling/exam-x/work/venv/bin/python`, a distinct path not examined in that probe. Those older records do not establish that path exists now or which host has it. Two additional explicitly bounded Track S locations are plausible path checks, not claims that they exist. This proposal checks those three paths and the observed system interpreter; it searches no broad directory tree.

After fresh read-only STATUS, locks and host/process census, and no-preemption review, run once as below. This runs CPU-only package imports with one thread and `CUDA_VISIBLE_DEVICES=''`, no model, no package installation, no GPU, no remote output file or remote deletion. `-I -B` ignores user-site/PYTHONPATH and bytecode caches, but normal venv startup can run site hooks; the author's amendment permits normal Python caches and internal temporary cleanup. The purpose is a bounded informational check, not proof of zero filesystem side effects. If a Python startup hook is known to alter other tracks or data, do not run that candidate. Ordinary paths and versions may appear in the private capture; review/redact before publication. Timeout, interruption, unreadable identity or failed import are NOT CHECKABLE/unusable for that candidate, not permission to install, retry, preempt or launch B1.

```bash
set -u
umask 077
OUT=$(mktemp -d /private/tmp/paper-b-tasl7-python-next-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$OUT/discovery.txt" 2>&1 <<'REMOTE'
set -u
date -u; hostname
if ! command -v timeout >/dev/null 2>&1; then
  printf '%s\n' 'STOP: timeout unavailable'
  exit 2
fi
for python in "$HOME/exam-x/work/venv/bin/python" \
              "$HOME/r1_tracks/work/venv/bin/python" \
              "$HOME/r1_tracks/.venv/bin/python" \
              /usr/bin/python3; do
  printf '\nCANDIDATE %s\n' "$python"
  if ! test -x "$python"; then printf '%s\n' 'NOT_EXECUTABLE'; continue; fi
  printf 'resolved='; readlink -f "$python"; printf 'readlink_rc=%s\n' "$?"
  env -i HOME=/dev/null XDG_CACHE_HOME=/dev/null PATH=/usr/bin:/bin \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
    timeout --signal=TERM --kill-after=2s 15s "$python" -I -B -c '
import sys
print("python", sys.executable, sys.version.replace("\\n", " "), "prefix", sys.prefix)
for name in ("pytest", "numpy", "sklearn", "yaml"):
    try:
        m = __import__(name)
        print("IMPORT_OK", name, getattr(m, "__version__", "unknown"), getattr(m, "__file__", "unknown"))
    except Exception as exc:
        print("IMPORT_FAILED", name, type(exc).__name__)
'
  printf 'import_rc=%s\n' "$?"
done
REMOTE
rc=$?
printf 'ssh_exit=%s\n' "$rc" > "$OUT/ssh-status.txt"
shasum -a 256 "$OUT/discovery.txt" "$OUT/ssh-status.txt"
printf 'SSH exit %s; inspect all per-candidate results before relying on them.\n' "$rc"
```

For venv candidates, independently verify `pyvenv.cfg`, `python` versus sibling `python3` executable, resolved paths and `sys.prefix`, all required modules and worker PATH in the already reviewed actual worker plan. System package discovery is informational: the current worker plan requires a pre-existing venv and accepting system Python would require a reviewed plan amendment and equivalent parent/worker interpreter and dependency checks. No earlier result is inferred from this proposal. A successful discovery establishes no held lease, GPU readiness, final author gate, or B1 authorization.
