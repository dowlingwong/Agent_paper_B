# B1 final-head TASL-7 gate and native preflight invocation

**Candidate for independent review; not executed.** Source inspected: Paper HEAD `ab8fdf45f86a647385705fbcc4d0bfa8c3554fbd`. It is not the final approved-note HEAD: at that inspected HEAD the configured `docs/r1/authorizations/trackx_b1_20261105.md` is absent. Do not run this invocation at `ab8fdf45`. Under the author's later ordering, first prepare the other independent prerequisites, commit the allowed `approved:true` candidate and obtain independent acceptance of that exact HEAD. The real gate and host preflight are subsequently run on that exact final HEAD; all other launch conditions and handover remain in force. An independently reviewed final source/command/artifact and fresh host state are prerequisites, not implied by this document.

## Concrete bindings and sequencing

- The accepted offline Paper checkout staging plan places the separate checkout at `/home/dowling/r1_b1_engineering/b1_paper_final_<FULL_FINAL_HEAD>/paper`. The previously staged harness is `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness`, pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`. `AR_HARNESS_ROOT` **must be exported before any `r1.exam.runtime` import**: that import reaches `r1.exam.campaign`, which resolves and imports the harness at module import time. Otherwise the sibling default is wrong for these independent checkouts.
- The committed B1 config inspected here fixes `work_dir=/home/dowling/exam-x/work` and `models_dir=/home/dowling/exam-x/models`. `host_check` requires these exact non-aliased paths; `b1_host_preflight.check_inputs` additionally requires its fresh `--out` to be a **direct child** of `work_dir`, not of the staged checkout or its engineering parent. Use the distinct absent `/home/dowling/exam-x/work/b1_host_preflight_20261108_a`; reserve a different fresh child for an eventual B1 batch. The preflight itself must create its output directory; do not precreate it. A separate absent evidence directory under `/home/dowling/r1_b1_engineering` is outside the checkout and holds gate and preflight logs. Existing model paths, Stage A tables, repository files, other outputs and worktrees are inputs only.
- The runtime requires checkout-root cwd, clean tracked/untracked state and the committed config/registry/rule/note bindings. `ExamRunner` also requires the configured `paper_commit` to be an ancestor of final HEAD with no changes in its protected code paths. The actual config at final HEAD and the fixed t7h8/t7j10 table hashes, acceptance report, Q2 reference, node sources, model/repair templates, binary SHA/build and Stage A PASS-row footprints are rechecked by the existing code. No `TODO_VERIFY_ON_HOST` footprint is replaced by a guessed value. Actual data/cache provenance and the retained offline-loader evidence STOP must first have their independently accepted disposition.
- Verify the host Python `/home/dowling/exam-x/work/venv/bin/python` and its sibling `python3`/PATH binding against the actual B1 worker environment; `worker_environment()` checks identity. Limit BLAS/OpenMP to one and prevent Python cache writes in the checkout. The script itself rechecks eligible model specs, current GPU UUID, current compute processes and the 100 GB floor. The latter is not a full retained-B1 storage estimate; 20-worker memory/headroom and total output capacity remain separate prerequisites.
- Fresh reviewed census/no-preemption and a genuinely idle GPU are required. The native probe holds the cooperative lock, starts **one owned** pinned anchor server, verifies descriptor inheritance and offload without inference, then invokes the existing owned-server stop path and closes its own lease. Preserve shutdown writes; no unrelated process may be signalled. The author has rejected cgroup/supervisor/freezer requirements. A failed, interrupted or unclear gate/probe/cleanup is STOP; retain evidence and do not automatically rerun. The real preflight result needs fresh independent review, and only afterward may the reviewed O2 STATUS/marker handover and eventual authorized B1 launch proceed.

## Exact one-shot template

The operator and independent reviewer must replace `REPLACE_WITH_FINAL_REVIEWED_40_HEX_HEAD` with the final accepted full SHA, verify the staged checkout and preflight script at that SHA, review all literal paths and choose unused run-specific suffixes, then review the completed command. The following is a **remote bash body**, not permission to run it now. It records separate gate and preflight exits/logs in an exclusively created directory; source and model inputs are never modified by this body. The filled remote script, its SHA and the local SSH wrapper below must also be independently reviewed; a dropped SSH connection does not establish completion.

```bash
set -eu
umask 077
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONNOUSERSITE=1
HEAD=REPLACE_WITH_FINAL_REVIEWED_40_HEX_HEAD
case "$HEAD" in *[!0-9a-f]*|'') exit 1;; esac
[ "${#HEAD}" -eq 40 ] || exit 1
PAPER="/home/dowling/r1_b1_engineering/b1_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
CAP=/home/dowling/r1_b1_engineering/b1_final_gate_preflight_20261108_a
OUT=/home/dowling/exam-x/work/b1_host_preflight_20261108_a
CACHE=/home/dowling/r1_b1_engineering/b1_final_gate_pycache_20261108_a
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
exit "$probe_rc"
```

PASS needs both exit records 0, the exact `GATE_PASS` HEAD and rule, output of the existing native preflight including held-lock contention refusal, live inherited server descriptor, correct model/offload checks, and `PREFLIGHT_PASS`; independently verify the owned server has exited and its lease is released. Missing logs/exit records, an unavailable dependency, path collision, current occupancy, incomplete cleanup or inconsistent HEAD is STOP, never a retry. This template does not itself establish final scientific readiness or launch authority.

After filling the remote script into a new local file with exclusive creation and obtaining an independent review of its exact SHA and bindings, this is the proposed local transport and capture (replace both placeholders with the reviewed file and full hash). A failed or incomplete session is STOP, and both local and remote partial scenes must be preserved. The local capture directory is fresh; no output file is reused.

```bash
set -u
umask 077
REMOTE_SCRIPT=/absolute/path/to/uniquely-created-reviewed-remote-script.sh
EXPECTED_SCRIPT_SHA=REPLACE_WITH_REVIEWED_64_HEX_SHA256
[ "$(shasum -a 256 "$REMOTE_SCRIPT" | awk '{print $1}')" = "$EXPECTED_SCRIPT_SHA" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-final-host-preflight-capture-20261108.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' < "$REMOTE_SCRIPT" > "$OUT/ssh.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/ssh.exit"
shasum -a 256 "$REMOTE_SCRIPT" "$OUT/ssh.log" "$OUT/ssh.exit"
printf 'Private capture=%s; SSH exit=%s\n' "$OUT" "$rc"
```
