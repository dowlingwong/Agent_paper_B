# TASL-7 B1 host preflight: bounded operator plan

**Draft for fresh independent review; not executed.** This plan describes the remaining B1 checks, not a B1 authorization, site observation or final-head acceptance. The author's §0.5 allows bounded engineering checks ahead of the final B1 checkout; no preliminary result substitutes for checking the exact finally reviewed B1 HEAD. The 7 November evening decision permits normal pinned-harness temp/lock/pending cleanup, requires preservation of repository, remote and experiment evidence, and removes any B1 cgroup, supervisor, freezer, fsync/receipt-durability or malicious-same-UID requirement. Use Stage A's ordinary process management and the accepted B1 units, not the excluded candidate branches.

## Order and preconditions

1. Collect a fresh reviewed read-only census of the applicable Track X/S/P STATUS and `~/r1_locks`, watcher/collector and P.3a state, GPU UUID/apps, host identity and the filesystems holding models and outputs. The author allows continuing despite unrelated agents, but never preempt their work, signal their processes or alter their files. A point-in-time listing is not a reservation. Wait for an actual safe idle window; if the GPU is in use, do not run a real-server probe. Use a new dated B1-owned engineering directory, exclusive evidence filenames, and retain all partial records. Capture UTC, commands, exit statuses and hashes privately; independently review each result.
2. Complete the independently reviewed real-worker engineering test and its source/environment checks. `60ecf1da` engineering evidence applies only to that source and must be compared against the final checkout before deciding whether a retest is needed. No normal B1 worker or LLM proposal is run during this preflight.
3. Prepare the author-approved `approved:true` note candidate under the already authorized ordering. Integrate all required accepted units, author PLAN rows, frozen rule, Q2 JSON, registry/config and note; obtain fresh independent acceptance of that precise clean committed HEAD. Approval of the candidate note permits preparing this head; it is not by itself authority to launch. On TASL-7 run the actual committed gate on that same clean checkout and compare the returned HEAD, hashes and config below. Do not set `approved:true` by inference or alter the author's decision cells.
4. In a non-preemptive idle window, run the bounded host preflight dry run described below: no campaign or inference, real cooperative lock plus a dedicated, owned llama-server if pins and site conditions permit. Preserve its separate engineering output and stop that server/release that lease. Review the actual site result. Only then do the reviewed O2 marker, feature-branch STATUS, watcher and safe P.3a handover, and recheck the actual B1 lease, GPU and all conditions immediately before launch. If the real-server preflight cannot obtain a naturally idle window before O2, wait and report; do not create the marker early or stop somebody else's process to make it pass.

## Exact HEAD, worker and author gate

Use the final independently accepted checkout as `CHECKOUT`, its absolute venv interpreter as `PYTHON`, and the accepted 40-hex head as `EXPECTED_HEAD`. Record the values in an exclusively new private evidence log outside the checkout. The following is read-only with respect to tracked source and runs no worker, server or GPU. It must be executed from the checkout root; use `PYTHONDONTWRITEBYTECODE=1` and an absent private cache prefix so that the clean-tree requirement is meaningful. The reviewer checks the actual command, hashes, environment and exit status. A failure is STOP, not an invitation to alter a pin or retry automatically.

```bash
cd "$CHECKOUT"
test "$(git rev-parse HEAD)" = "$EXPECTED_HEAD"
test -z "$(git status --porcelain --untracked-files=all)"
test "$(git -C "$AR_HARNESS_ROOT" rev-parse HEAD)" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2
test -z "$(git -C "$AR_HARNESS_ROOT" status --porcelain --untracked-files=no)"
"$PYTHON" -B - <<'PY'
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
rule, sha=load_rule(cfg['rule'],cfg['rule_sha256'])
if rule.get('version')!='x5_rule/v2': raise SystemExit('STOP: wrong rule')
if author_gate(cfg,'b1',sha)!=head: raise SystemExit('STOP: gate HEAD mismatch')
verify_anchor_reference(cfg)
env=worker_environment()
for node in cfg['nodes']: print('node_source',node,b1_harness_sources(node,cfg['harness_commit']))
print('gate_head',head,'rule_sha256',sha,'python',sys.executable,'worker_python',str(Path(sys.executable).parent/'python3'))
print('threads',*(env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')))
PY
```

Export `EXPECTED_HEAD`, `AR_HARNESS_ROOT`, `PYTHONDONTWRITEBYTECODE=1` and the reviewed absent `PYTHONPYCACHEPREFIX` before this block. Compare `sys.executable`, PATH-resolved `python3`, venv prefix and imported package versions with the actual server/worker environment, not just a previous separate engineering venv. `worker_environment()` requires the sibling `python3` to be executable and the same file as the parent interpreter; it sets OMP/OpenBLAS/MKL to 1. Record Python, NumPy and scikit-learn versions, and do not silently install or substitute an interpreter. `author_gate` verifies the exact dated PLAN row, note, node/cap/worker/host/GPU/reference fields and SHA bindings including both Stage A tables and the accepted amendment record. The t7h8 table digest is `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c`, t7j10 is `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`; `OPS_O1_20261104.md` records the accepted Stage A/A1 evidence, not a B1 result. The gate checks the actual config's values; the reviewer compares them to the approved note and receipt. The t7j10 amendment acceptance must match its committed specified SHA, not a reconstructed document.

## Native server and lock preflight (no inference)

The operator checks the actual config and registry from the reviewed HEAD and applies the existing `ExamRunner.validate_spec`, `template_repair_args` and `stage_a_pass_set` logic to every eligible candidate and the `qwen25_coder_7b` anchor: exact GGUF size/SHA, licence/quant source, server ELF SHA/build, template file SHA, Stage A selection and frozen inputs. Record unresolved or unavailable pins as STOP; never substitute a model, build, path, table or footprint. The current registry includes `TODO_VERIFY_ON_HOST` footprint fields: they are not measured values. The 100 GB floor in `space_check` is only a floor; estimate the complete retained B1 campaign/audit output and verify sufficient free bytes on every actual output filesystem, including growth headroom. Recheck host and GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, compute-app census and no competing job immediately before starting. An unreadable census is STOP; an idle snapshot is not an exclusive lease.

For the real descriptor preflight use the reviewed configuration's existing B1 APIs, in one B1-owned process and fresh private engineering directory: `r1.exam.b1_lease.acquire` takes the existing `~/r1_locks/gpu0.lock` nonblocking and records FD/device/inode; an independently opened own contender must be refused while it is held. Use the reviewed `qwen25_coder_7b` anchor and exactly the same server binary, GGUF, `EXAM_SERVER_ARGS`, `template_repair_args`, thinking-off policy, 32768 context, Q8 KV and full GPU layers as the B1 `_server` path. Instantiate `LlamaServerInstance` with a unique own port and directory, set its existing B1 record-preservation option, and call `start(..., b1_lease_fd=fd)`; this uses `pass_fds` and invokes `b1_lease.verify_server_fd` once healthy. Record the parent and server PID/start identity, FD number, parent/server `/proc/<pid>/fd/<fd>` device/inode, observed GPU UUID/occupancy, health, model alias/path, and the existing offload route with its pinned measured footprint. Check the inherited descriptor again while the server is healthy and before stopping. No prompt or generation request is necessary. Missing FD, mismatch, failed offload, unhealthy server, insufficient 1024 MiB free margin or unexpected compute process is STOP. This is the actual B1 same-inode descriptor check; do not describe it as a `kcmp` proof of shared open-file description. The earlier t7j10 real-server receipt and standalone ancestor/child `kcmp` result are useful context but do not test this new server instance.

Use `LlamaServerInstance.stop()` **only for the server instance this preflight started**. On every success or error path, stop it through that existing owned-process path; retain shutdown log/record writes and confirm the owned process has exited. Then close the preflight's own lease FD, record release and recheck the GPU/lock state without modifying another process. If the server cannot be safely identified/stopped or lock release cannot be observed, preserve the scene and report STOP; do not signal unrelated PIDs, infer release from a receipt, rerun, or launch B1. A separately reviewed short invocation must use a fresh output path and make this cleanup run even if server startup or descriptor verification raises. The existing `b1_lease` and `LlamaServerInstance` APIs are the implementation, not a new guardian or cgroup mechanism.

## Host dry-run boundary and remaining finite action

The existing `r1/scripts/exam_dryrun.py` and `runtime.host_check` explicitly forbid fake EXAM DRYRUN on approved production hosts. Do not bypass that guard or run its killed-root recovery on TASL-7. The author nevertheless requires a host preflight dry run. The concrete minimal host-compatible candidate is `r1/scripts/b1_host_preflight.py`: the committed real gate, worker, frozen-source and model checks followed by one owned real-server/lease exercise, with a separate `ENGINEERING_ONLY` output and no generation request. It must be independently reviewed and its actual site result accepted before it is counted. The implementation's scoped mock-server tests cover success, start/descriptor/cleanup failure and preservation of the initiating failure, not actual TASL-7 or GPU behavior. The exact invocation, after all prerequisites above, is:

```bash
cd "$CHECKOUT"
set -C
"$PYTHON" -B -m r1.scripts.b1_host_preflight --head "$EXPECTED_HEAD" --out "$PROBE_DIR" > "$EVIDENCE_LOG" 2>&1
```

`PROBE_DIR` must be an absent new direct child of the approved work directory, `EVIDENCE_LOG` a separate absent B1-owned file outside the clean checkout; capture the exit code and retain both even on failure. The operator must set `AR_HARNESS_ROOT`, an absent private `PYTHONPYCACHEPREFIX` and `PYTHONDONTWRITEBYTECODE=1` and use the verified Python binding. Require the actual gate HEAD, validated pins, held-lock contention refusal, live inherited descriptor, healthy correctly pinned native server, full offload and post-stop `PREFLIGHT_PASS`, then independently inspect logs/records and confirm the owned server exited and lease was released. A nonzero exit, missing pass, inability to stop, uncertain process/lease state or missing evidence is STOP. Never repeat automatically or signal an unidentified process. The script checks only current idle GPU and the 100 GB storage floor; the operator must separately prove enough space for the complete retained B1 output. If stopping the owned server fails the script records the failure and cannot claim quiescence; the operator must preserve the scene and investigate without touching other processes.
 This is not permission to perform a B1 root or request inference. Owner: local implementation agent and independent reviewer, then TASL-7 operator; effort is one bounded script/review and one site check, subject to model availability and an idle GPU. If those checks cannot meet the required host dry run, record the exact gap and STOP; do not treat the Mac fake dryrun as a host pass.

Once the reviewed host dry-run evidence is accepted, apply `B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` and the author-approved `mac-b1-20261107` STATUS/Track P marker decision. Confirm watcher effects and restoration route, safely pause P.3a without preemption, publish and verify feature-branch STATUS, and retain the marker and evidence on STOP. Recheck author gate, HEAD, GPU and actual lease at the start of B1. No B2, X.7 or sweep 2 follows automatically.
