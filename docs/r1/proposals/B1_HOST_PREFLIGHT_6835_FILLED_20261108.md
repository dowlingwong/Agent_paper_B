# B1 candidate 6835: conditional host author gate and native preflight

**For independent review; do not execute yet.** Exact candidate `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` received exact-HEAD review da32; local artifact review `7d7d15e92fa0e1730c55a1490a2135043f6fe341`. The author authorized one new Paper receive, which is in progress; neither its result nor its acceptance is assumed. Record that decision and receive evidence in external review/STATUS, without mutating the frozen candidate. Before either gate or model preflight, the actual received checkout and this filled invocation require fresh independent review and all O2/handover, occupancy, resource and other applicable conditions must hold. Preserve first attempt and all partials. This proposal does not authorize launch or remove any STOP.

This fills accepted template `f872f8e0ccf08e6536d574484fe522a6e794e892`, review `6726e8eb4f62d20a596a15a48b3d45712730fc1e`, and follows the 9dfd filled form reviewed at `0d5c2f72b0f382a6444ab43c46960873a27f5396`. It binds Paper `/home/dowling/r1_b1_engineering/b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb/paper`, separate pinned harness `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness`, and `/home/dowling/exam-x/work/venv/bin/python`. The gate checks committed note, config, registry, rule, Stage A and Q2 through production paths. After that, native preflight rechecks inputs and starts its own anchor server under its own cooperative lease, loads a model on GPU without inference, stops its own server and closes its own descriptor. It must not run from stale occupancy or over other work. Preflight is not the campaign.

The remote script is `/private/tmp/b1-final-host-preflight-6835-20261108.remote.sh`, SHA-256 `4854a6cd4564b38c75fd005b46ceebb22eb13a5dafd4ed2ae5fdb2f5b18f9fda`; the local capture script is `/private/tmp/b1-final-host-preflight-6835-20261108.local.sh`, SHA-256 `bdefc0403085c4fdd8e6cc69369c2256314fc4cdd57fb82588fd4aad6acb63f8`. Both passed `bash -n`; no remote execution was made. Remote capture, cache and output paths are unique to 6835 and checked absent including symlinks. `env -i` and fixed PATH prevent inherited Python/Git redirects and unapproved GPU/LLM overrides. The actual SSH exit is recorded both in the private local log and a separate exit file. Remote gate and preflight log and exit files are separately retained. If a collision, gate failure, nonzero or unknown exit, interruption, missing completion marker or uncertain cleanup occurs: STOP and preserve all outputs; no automatic retry. Success markers and zero exit are preliminary evidence, not independent acceptance. Independently examine the actual logs, hashes, exact HEAD, eligible model checks, lock contender, descriptor inheritance, GPU identity/load/offload, shutdown and lease release; recheck final B1 worker environment. A 100 GB floor alone does not establish full output or 20-worker RAM headroom.

## Remote script

```bash
set -eu
umask 077
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONNOUSERSITE=1
HEAD=68357d3d8cd0c9f301005e483a49ecfd05f6e5bb
case "$HEAD" in *[!0-9a-f]*|'') exit 1;; esac
[ "${#HEAD}" -eq 40 ] || exit 1
PAPER="/home/dowling/r1_b1_engineering/b1_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
CAP=/home/dowling/r1_b1_engineering/b1_final_gate_preflight_6835_20261108_a
OUT=/home/dowling/exam-x/work/b1_host_preflight_6835_20261108_a
CACHE=/home/dowling/r1_b1_engineering/b1_final_gate_pycache_6835_20261108_a
[ "$HOME" = /home/dowling ] || exit 1
[ ! -L "$CAP" ] && [ ! -e "$CAP" ] || exit 1
[ ! -L "$OUT" ] && [ ! -e "$OUT" ] || exit 1
[ ! -L "$CACHE" ] && [ ! -e "$CACHE" ] || exit 1
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || exit 1
[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ] || exit 1
[ -x "$PY" ] || exit 1
mkdir -m 700 "$CAP"
set -C
export EXPECTED_HEAD="$HEAD" AR_HARNESS_ROOT="$HARNESS"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$CACHE" GIT_OPTIONAL_LOCKS=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
cd "$PAPER"
if "$PY" -B - > "$CAP/gate.log" 2>&1 <<'PY'
import os, sys
from pathlib import Path
from r1.exam.runtime import (REPO, B1_CONFIG_REL, load_config, require_committed_b1_config,
    require_committed_b1_registry, author_gate, worker_environment, b1_harness_sources)
from r1.exam.analyze import load_rule
from r1.scripts.exam_runner import verify_anchor_reference
cfg=load_config(REPO/B1_CONFIG_REL)
head=require_committed_b1_config(REPO/B1_CONFIG_REL,cfg)
if head != os.environ['EXPECTED_HEAD']: raise SystemExit('STOP: reviewed HEAD mismatch')
require_committed_b1_registry(cfg,head)
rule,sha=load_rule(cfg['rule'],cfg['rule_sha256'])
if rule.get('version')!='x5_rule/v2' or author_gate(cfg,'b1',sha)!=head:
    raise SystemExit('STOP: rule or author gate mismatch')
verify_anchor_reference(cfg)
env=worker_environment()
for node in cfg['nodes']: print('node_source',node,b1_harness_sources(node,cfg['harness_commit']))
print('GATE_PASS',head,sha,'python',sys.executable,'prefix',sys.prefix,
      'worker_python',str(Path(sys.executable).parent/'python3'),
      'threads',*(env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')),flush=True)
PY
then gate_rc=0; else gate_rc=$?; fi
printf '%s\n' "$gate_rc" > "$CAP/gate.exit"
[ "$gate_rc" -eq 0 ] || exit "$gate_rc"
if "$PY" -B -m r1.scripts.b1_host_preflight --head "$HEAD" --out "$OUT" > "$CAP/preflight.log" 2>&1; then probe_rc=0; else probe_rc=$?; fi
printf '%s\n' "$probe_rc" > "$CAP/preflight.exit"
printf 'PRIVATE_CAPTURE=%s\nPREFLIGHT_OUTPUT=%s\n' "$CAP" "$OUT"
sha256sum "$CAP/gate.log" "$CAP/gate.exit" "$CAP/preflight.log" "$CAP/preflight.exit"
[ "$probe_rc" -eq 0 ] || exit "$probe_rc"
grep -F "GATE_PASS $HEAD " "$CAP/gate.log" >/dev/null
grep -Fx 'PREFLIGHT_PASS: owned server exited and own lease descriptor closed' "$CAP/preflight.log" >/dev/null
printf '%s\n' 'BEGIN_GATE_LOG'
cat "$CAP/gate.log"
printf '%s\n' 'END_GATE_LOG' 'BEGIN_PREFLIGHT_LOG'
cat "$CAP/preflight.log"
printf '%s\n' 'END_PREFLIGHT_LOG' 'FINAL_PREFLIGHT_CAPTURE_COMPLETE'
exit 0
```

## Local capture script

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
REMOTE_SCRIPT=/private/tmp/b1-final-host-preflight-6835-20261108.remote.sh
EXPECTED=4854a6cd4564b38c75fd005b46ceebb22eb13a5dafd4ed2ae5fdb2f5b18f9fda
[ "$(shasum -a 256 "$REMOTE_SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-final-host-preflight-6835-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash -s' < "$REMOTE_SCRIPT" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.exit" || exit 1
shasum -a 256 "$REMOTE_SCRIPT" "$OUT/ssh.log" "$OUT/ssh.exit"
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx 'SSH_EXIT=0' "$OUT/ssh.log" || exit 1
grep -q '^GATE_PASS 68357d3d8cd0c9f301005e483a49ecfd05f6e5bb ' "$OUT/ssh.log" || exit 1
grep -qx 'PREFLIGHT_PASS: owned server exited and own lease descriptor closed' "$OUT/ssh.log" || exit 1
grep -qx 'FINAL_PREFLIGHT_CAPTURE_COMPLETE' "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```
