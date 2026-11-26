# B1 retained-output capacity, 20-worker memory and note readiness

**Planning assessment, not a host check or B1 authorization.** Source snapshot `c8ab675c6deb3905cc39f997decfe85286c2a789`; no host, GPU, model or experiment was run for this assessment. The author chose `workers=20`, `W=20` and cap 80: this plan does not change them. It proposes a bounded ENGINEERING_ONLY measurement using separately owned paths and non-B1 seeds, not a scientific measurement or evaluation-audit read. No recorded STOP is resumed or retried automatically.

## What is known and what is not

The reviewed 22:23:52 UTC O2 capture reports approximately **585 GiB free** on the filesystem containing `~/exam-x/work`; the separate 22:16:16 UTC capacity capture reports **59 GiB MemAvailable** on a 62 GiB host, with **1.0 GiB swap already used**. These are time-bounded, non-atomic observations, not current reservations, free-space proof for every output filesystem, or proof that 20 concurrent audits fit. Stage A's selected GPU MiB footprints describe GPU server allocations, not CPU RAM for the audit workers. The existing single `tabular_mlp` real-worker test took 4.17 s on TASL-7, but did not measure the simultaneous three-node audit memory profile or retained B1 output size. Do not treat 59 GiB or the 100 GB `space_check` floor as evidence that the full run fits.

`run_b1_audits` submits at most `min(20, distinct uncached configurations)` calls to `run_config` concurrently; each call copies a node and, for OpenML nodes, its data cache, then runs the four audit seeds sequentially. Each pool Python process can also have a node-training subprocess. The B1 runner, manager and separately owned llama-server remain resident. Prior `artifacts` directories, editable versions, trial logs, cache/state snapshots and server records are retained, so output grows. Queueing 20 does **not** mean only 20 OS processes or 20 files. Configurations are deduplicated by hash, but invalid/duplicate proposal records and actual log sizes must not be assumed to obey a simplistic 20-proposal bound.

The independently reviewed Stage A capture at Paper `92fb4057` selects 16 model-backed entries plus two software anchors. Under the captured registry/grammar state, 11 selected models are switchable. Current B1 logic therefore implies **216 primary roots** (`18 × 3 nodes × 4 seeds`) and **44 descriptive thinking-on roots** (`11 × 1 node × 4 seeds`), or **260 roots if all complete**. This is a planning count derived from the accepted capture and current logic, not a promise of successful completion or a fixed count after an actual STOP; re-evaluate against the final accepted HEAD/tables. It does not bound the bytes per root or the number of retained audit copies. No source reviewed here gives a trustworthy full-run byte or inode upper bound, nor a qualified per-node peak RAM envelope.

## Bounded read-only site inventory

After the usual fresh STATUS/lock/process and no-preemption review, an authorized operator may run the following **once** with `HARNESS_ROOT` set to the previously verified absolute `a3fedbb` host checkout. The safe-character check prevents shell interpolation; preserve the new private capture and its exit file. It reads only the three relevant source-node directories, the two existing pinned OpenML caches, the model/output filesystems and kernel aggregate capacity; it does not read any audit values, create a remote file, train a model or use GPU. Missing paths, inaccessible filesystems, command errors, quota/inode visibility gaps or concurrent changes are **NOT CHECKABLE**, not zero usage. `du` is a non-atomic measurement; if a cache is on a different filesystem, retain its own `df` output. Adapt only the separately verified harness path, not B1 pins or seeds.

```bash
set -u
umask 077
HARNESS_ROOT=/absolute/path/to/verified/a3fedbb/harness
case "$HARNESS_ROOT" in /*) ;; *) exit 1;; esac
case "$HARNESS_ROOT" in *[!A-Za-z0-9_./-]*|'') exit 1;; esac
OUT=$(mktemp -d /private/tmp/paper-b-b1-capacity-readonly-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "HARNESS_ROOT=$HARNESS_ROOT bash -s" > "$OUT/inventory.txt" 2>&1 <<'REMOTE'
set -u
date -u; hostname
printf 'HARNESS_HEAD '; git -C "$HARNESS_ROOT" rev-parse HEAD; printf 'head_rc=%s\n' "$?"
for path in "$HARNESS_ROOT/nodes/digits_mlp" "$HARNESS_ROOT/nodes/openml_credit_approval" "$HARNESS_ROOT/nodes/openml_ionosphere" \
 "$HARNESS_ROOT/experiments/r1/pilot/L8_20261009T152916Z/nodes/openml_credit_approval/data_cache" \
 "$HARNESS_ROOT/experiments/r1/pilot/L8_20261009T152916Z/nodes/openml_ionosphere/data_cache"; do
  printf 'PATH %s\n' "$path"
  du -sk "$path"; printf 'du_rc=%s\n' "$?"
  df -Pk "$path"; printf 'df_rc=%s\n' "$?"
  df -Pi "$path"; printf 'inode_rc=%s\n' "$?"
done
for path in "$HOME/exam-x/work" "$HOME/exam-x/models"; do
  printf 'FILESYSTEM %s\n' "$path"
  df -Pk "$path"; printf 'df_rc=%s\n' "$?"
  df -Pi "$path"; printf 'inode_rc=%s\n' "$?"
done
printf 'MEMORY\n'; free -b; printf 'free_rc=%s\n' "$?"
printf 'LOAD\n'; uptime; printf 'uptime_rc=%s\n' "$?"
printf 'CPUS '; getconf _NPROCESSORS_ONLN; printf 'cpu_rc=%s\n' "$?"
printf 'OWN LIMITS\n'; ulimit -a; printf 'limits_rc=%s\n' "$?"
REMOTE
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/inventory.txt" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

The operator independently compares the target checkout commit and clean source/cache identity with the actual planned B1 harness; a nominal path or `du` value is not a data qualification. Capture current per-filesystem quota if the site exposes one, otherwise record quota as NOT CHECKABLE. Space estimates must count the separate copied node/cache directories **per unique audit configuration**, retained four-seed node outputs, per-trial artifacts, archived editable files, full versions of rewritten state/cache, logs, manifests, and file/inode counts. `observed node + cache bytes × number of copies` is a lower-bound component, not a full-run estimate; do not use compression, deduplication or an absent directory as a free allocation without verifying the actual filesystem. Compare the measured, reviewed envelope for the full 260-root scenario to current writable bytes, inode/quota headroom and the existing 100 GB floor on every relevant filesystem. If no defensible envelope or room remains, STOP and keep measuring; no number is silently invented and no author budget change is implied.

## Bounded CPU profiling when inventory is insufficient

The minimal next engineering unit is a small independently reviewed driver using the existing `r1.c3.audit.run_config` and the pinned `a3fedbb` loader, not a new scheduler. In a fresh private, explicitly ENGINEERING_ONLY directory on TASL-7, with the same verified venv/thread caps and no GPU/LLM, run **one unmodified configuration per B1 node** with one fixed, non-B1 joint seed, e.g. 98001; do not use or read 7006–7010 or B1's 9101–9104 audit values. These are real CPU node executions on development input: retain the resulting copied caches, output, trial logs and timing, and do not interpret the metrics scientifically. Record each output tree's bytes and inode count and sample only the driver's own worker/child processes and their `/proc` RSS/PSS, `MemAvailable`, swap and CPU pressure during each run; report sampling interval, missed reads and whether a descendant escaped observation. Do not read other users' command arguments or signal their processes. Use the accepted engineering process-group wrapper and a maximum of **180 seconds per node**; a timeout, invalid metric, missing process identity, unexpected file collision or resource pressure is STOP with one attempt and preserved evidence.

For a conservative *observed-workload* admission calculation, use the largest measured complete one-worker process-tree RSS across the three nodes, multiply by 20, and include the measured B1 controller/manager resident memory and the owned native server's host RAM once each. If the server was already resident when `MemAvailable` was sampled, do not count it twice. Compare against fresh `MemAvailable` and available swap/limits while preserving space for existing tasks; this is a screening bound, not an exact maximum or a formal guarantee against different configurations, unsampled peaks, kernel allocations or new jobs. Do not infer RAM demand from the server's GPU MiB. If the screening bound and no-preemption checks show it is safe, a separately reviewed **one-shot controlled 20-worker** diagnostic using the worst measured node and distinct non-B1 seeds can validate the estimate, monitoring actual aggregate PSS/RSS and pressure. Start at most 20 jobs, use owned sessions and bounded wrapper/cleanup, preserve outputs, and STOP on failure or pressure; do not launch it if the screening calculation cannot establish room. The site operator and independent reviewer must accept the actual command before executing. The three single-node calls have at most **3 × 180 s** of configured runtime plus setup and cleanup; the optional 20-worker diagnostic has its own **180 s** cap. Actual setup, model fitting, evidence review, copied-cache disk consumption and any slow shutdown may take longer. This is an operational screening procedure, not a new protocol threshold or author decision.

For disk, size the retained one-node outputs and enumerate the copies and state versions actually generated by these diagnostics. Combine with the 260-root planning count and a conservative, independently reviewed bound on unique audited configurations and retained per-root growth derived from the actual final code and input/configuration contract. If that bound cannot be established because record or log growth is not bounded by the present evidence, report precisely which term is unknown rather than assert completion capacity from the 100 GB floor. In either case monitor available bytes/inodes during B1 and STOP before the existing floor; no deletion or automatic resume follows.

## Note creation readiness versus launch

The Q2 JSON and its reference computation have a scoped ACCEPTED review, and the conditional rule/note approval is recorded. The unsigned draft is still `approved:false`; the configured production note path is absent. The later author explicitly allowed the sequencing in which a committed `approved:true` **candidate** is prepared once the other independent prerequisites are ready, followed by exact-HEAD independent review, real committed author gate and host preflight, and only then launch after handover. The candidate does not itself authorize a launch, and the reviewer—not the implementer—accepts the exact HEAD.

Before preparing that candidate, finish the non-circular prerequisites: a reviewed disposition of every B1-path/B1-related historical failure and relevant later failures; the previously required Stage A-to-B1 interruption/kill-resume coverage; verified input/rule/Q2/Stage A bindings and accepted B1 units; and a reviewed, currently feasible host/handover plan. In the retained 60ec Mac focused result the recovery follow-up was **1 failed, 2 passed**, with `PreparationStop: [Errno 1] Operation not permitted` before the intended crash; the precise operation/cause is not established. The reviewed 38-failure classification did not waive the shared watchdog/lease and nested DRYRUN issues; later focused fixes need comparison and review at the intended final code. The real-worker TASL-7 determinism test and Linux synthetic STOP tests have scoped ACCEPTED evidence at **60ec**, but their applicability to the final changed code still needs review. Disk capacity and 20-worker RAM are not yet established by the snapshots. Owners are the implementation/test agent and independent reviewer for code and dispositions, and the site operator plus independent reviewer for bounded capacity/site facts; effort depends on failed-test diagnosis and the measured system, not an arbitrary deadline.

The preliminary inventory and CPU measurements can be made before the note without starting a real server. The measured real-server host RAM and combined final capacity check may depend on the gate-bound host preflight; under the author-authorized ordering they can follow the committed candidate note. They must be completed and reviewed before launch, not assumed from the earlier preliminary screen.

After those prerequisites are ready, prepare the exact candidate note with the author's existing words and chosen values, integrate and independently review the clean committed HEAD, then run the real committed gate and the host preflight in the authorized order. O2's `mac-b1-20261107` STATUS and Track P marker decision is already recorded; the actual watcher/P.3a handover, real GPU lease/server descriptor, final space and no-preemption checks remain. Do not interpret this plan, a proposed capacity calculation, the candidate note or an engineering test as launch permission.
