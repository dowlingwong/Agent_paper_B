# Track X Stage A cooperative-lease release — independent adversarial review

Reviewer: independent reviewer (not the implementer; no edits to the artifact).
Date (review): 2026-11-01 (Europe/Berlin). Host probes timestamped in UTC below.
v2 verdict: **BLOCK** (§9, historical). Re-review of v3 (§11): **ACCEPT with conditions**. Pre-flight
launcher/config deltas C3/C4 confirmed (§12): **ACCEPT remains, with the §12.5 conditions**.

---

## 1. Artifact identity

| Item | Value |
|---|---|
| Core snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v2` |
| `SHA256SUMS` SHA-256 | `5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486` — **verified** |
| Base commit | `1be426fd653e4dcf2f601a678a4b36a83cd228e7` (live detached worktree `/private/tmp/paper-b-stagea-cooperative-20261031`) |
| Supplementary fixture snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v2-extra` |
| supplementary `SHA256SUMS` SHA-256 | `ec8dbb29ab3da8ad53ea3cbecc1bd98a4b4fba00bc388bc212baa1e52dbb97a9` — **verified** |
| v1 snapshot `SHA256SUMS` SHA-256 | `5f2d25bcdf209aaee54ddc1f44d1b59f3308f3f1ad01aa75a54cb877029398f9` — **unchanged** |
| Frozen prompt set (TASL-2) | `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a` — **re-read read-only, matches** |

All commands below were executed from the Mac shell or `ssh -o BatchMode=yes portal_zhixu` (TASL-2, user `dowling`), except where marked.

### 1.1 Snapshot integrity (verified)

- `cd <v2> && shasum -a 256 SHA256SUMS` → `5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486` (matches the required value).
- `shasum -a 256 -c SHA256SUMS` → **48/48 OK**: `tracked.patch` + 46 `files/**` + `README.md`.
- `tracked.patch` is **byte-identical** to `git -C /private/tmp/paper-b-stagea-cooperative-20261031 diff` (96126 bytes both, `cmp` equal).
- Every file under `files/` is **byte-identical** to the live worktree (`cmp` loop over all 46 files: 0 mismatches).
- `find files -type f | wc -l` = 46; `SHA256SUMS` line count = 48 (the 46 + `tracked.patch` + `README.md`).
- The live worktree HEAD is exactly `1be426f`; `git status --porcelain` contains the 14 tracked modifications and the expected new/untracked reviewed files (the snapshot's 46), plus deliberately-excluded D3 root drafts that are not in `files/`.
- Hygiene note, disclosed for transparency: while demonstrating a glob bug I imported the snapshot's guardian module directly and Python wrote a transient `files/r1/scripts/__pycache__/trackx_lease_guardian.cpython-315.pyc`. I removed exactly that directory; afterwards the snapshot is back to 46 files, `shasum -a 256 -c SHA256SUMS` = 48/48 OK, `SHA256SUMS` self-hash unchanged, and `files/` matches the live worktree again. No frozen artifact bytes were altered.
- Minor hygiene: an unlisted stray `/private/tmp/paper-b-stagea-cooperative-review-20261031-v2/.sums_tmp` exists in the snapshot root. It is not in `SHA256SUMS` and not in `files/`, so it does not affect the frozen hashes; it should be removed before the branch commit (non-blocking).

### 1.2 Supplementary fixture snapshot (verified)

- `shasum -a 256 -c SHA256SUMS` → 3/3 OK; self-hash `ec8dbb29…`.
- `files/r1/tests/stagea_lease_preflight.py` = `ca7c0de433997f3c5fde7436681bab98061306986d387c1bb4a598a9012e7640`;
  `files/r1/tests/test_stagea_lease_preflight.py` = `3ea9cc0324f2c011a423007114fab1a12f5e09f3fa0c384e508b47ad82989597`.
- Both are byte-identical to the live worktree copies (checked `cmp`).

---

## 2. What I verified and how

### 2.1 Test evidence (Mac, synthetic only)

Working command (from `/private/tmp/paper-b-stagea-cooperative-20261031`, live worktree = reviewed bytes):

```
AR_HARNESS_ROOT=$HOME/Documents/autoresearch_harness UV_CACHE_DIR=/private/tmp/uvcache \
PYTHONDONTWRITEBYTECODE=1 uv run --no-project --with pytest --with numpy --with pyyaml \
--with scipy --with scikit-learn python -m pytest <paths> -q -p no:cacheprovider
```

- Required subset (all `test_cooperative_lease.py`, `test_trackx_lease_guardian.py`, `test_exam_cache_runtime.py`,
  `test_exam_cache_*`, `test_exam_qualify*.py`, `test_exam_stagea_preserve.py`, `test_exam_observer_cache.py`,
  `test_exam_historical_seed.py`, `test_exam_prefill.py`, `test_exam_core.py`, `test_exam_observer.py`,
  `test_exam_namespace_fixture*.py`, `test_trackx_stagea_launch.py`):
  **`355 passed, 1 skipped in 24.41s`** — exactly the claimed count. The skip is the Linux-only
  `test_real_kcmp_proves_shared_ofd_with_a_synthetic_child` (`sys.platform` gate).
- Supplementary preflight guard tests: `r1/tests/test_stagea_lease_preflight.py` → **2 passed**.
- Full `r1/tests` (816 collected) on the live worktree: **`25 failed, 779 passed, 12 skipped in 440.76s`**.
  The 25 failures are in Mac/desktop-only modules (no `/proc`, no `nvidia-smi`, fake-server/desktop dry-run
  harnesses): `test_c3_control_dryrun.py` (1), `test_c3_sweep_dryrun.py` (6), `test_c3_sweep_resume.py` (2),
  `test_collector_observability.py` (2), `test_exam_dryrun.py` (1), `test_llama_server_instance.py` (3,
  all caused by `proc_cmdline`/`proc_uid` reading `/proc`, which macOS lacks), `test_llamacpp_offload_routes.py`
  (7), `test_llamacpp_probe.py` (1, `footprint_mib_to_pin is None` because `nvidia-smi` is absent),
  `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` (1, a nested desktop dry-run whose internal
  `r1-tests` check flags several files in a restricted Mac environment).
- I ran the same 8 failing modules (`test_llama_server_instance.py`, `test_llamacpp_probe.py`,
  `test_llamacpp_offload_routes.py`, `test_c3_control_dryrun.py`, `test_c3_sweep_dryrun.py`,
  `test_c3_sweep_resume.py`, `test_collector_observability.py`, `test_exam_dryrun.py`) on a clean extraction
  of base commit `1be426f` (`git archive 1be426f | tar -x -C /tmp/rvw_base`) with the same command; the
  BASE result is recorded in §2.1a.

### 2.1a Base-vs-live regression check for the patch-adjacent failing modules

I ran `test_llama_server_instance.py`, `test_llamacpp_probe.py`, `test_llamacpp_offload_routes.py` on the
clean **base** extraction. Result: **`12 failed, 35 passed in 46.15s`** with exactly the **same 12 test
names** that fail on the live worktree (3 × `test_llama_server_instance.py`, 1 × `test_llamacpp_probe.py`,
8 × `test_llamacpp_offload_routes.py`). Therefore these are **pre-existing Mac-environment failures, not
regressions** caused by this change:
- `test_llama_server_instance` failures come from `proc_cmdline`/`proc_uid` reading `/proc/<pid>/…`
  (macOS has no `/proc`); those functions are unchanged (`/tmp/rvw_base/r1/scripts/llama_server_instance.py:411-417,472`).
- `test_llamacpp_*` failures come from absent `nvidia-smi`/fake-GPU memory (`footprint_mib_to_pin is None`,
  `route (ii)` rows empty); the same assertions fail identically on base.
The remaining live-suite failures (`test_c3_control_dryrun`, `test_c3_sweep_dryrun`, `test_c3_sweep_resume`,
`test_collector_observability`, `test_exam_dryrun`, `test_rerun2_batch4c::test_real_runner_desktop_dryrun`) are
desktop/dry-run integration tests in modules **not modified by the patch** (the first fails invoking the
unmodified `r1/scripts/c3_control_dryrun.py`); they are consistent with the pre-existing Mac-only failure
claim. I did not run the slow c3/desktop modules on base (they take minutes and are unrelated); that specific
part of the claim is **partially verified** (see "NOT CHECKABLE" §8.10).

All test results above are **synthetic/CPU evidence**, not production evidence.

### 2.2 TASL-2 read-only host probes (all UTC, `ssh -o BatchMode=yes portal_zhixu`)

Observed **2026-10-31T23:24:18Z**:
- host `TASL-2`; kernel `6.8.0-136-generic`; `/proc/sys/kernel/yama/ptrace_scope` = `1`. (Matches the implementer's claim.)
- `sha256sum /home/dowling/exam-x/frozen_inputs/trackx_stagea_promptset_20261031/prompts.jsonl` =
  `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`, 50 lines. Matches config + task.
- `sha256sum /home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server` =
  `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`. Matches config `server.binary_sha256`.
- `nvidia-smi --query-gpu=uuid,name,memory.used,memory.total,utilization.gpu`:
  `GPU-4d623e76-7587-ee15-a633-46f60d220d94, NVIDIA GeForce RTX 4090, 436 MiB, 24564 MiB, 0 %`.
  Matches config `gpu_uuid`; host was idle at sample time (point-in-time only).
- Stopped namespace fixture `/tmp/d3_namespace_fixture_20261031_d61db5e9b02188f7`: **stat only**,
  `drwx------`, `mtime = ctime = 1793446875` (host local display `10月 31 04:41`). No references to
  `d61db5e9b02188f7` or `d3_namespace_fixture` occur anywhere in the core snapshot, the extra snapshot, or
  `tracked.patch` (grep: none). I did not enter, read, retry, relabel or signal it.
- Retained build line: the pinned build string `version: 0.7.0-dev (build 1, commit 620d222)` appears in
  retained portal files under `/home/dowling/exam-x/work/agent_paper_B/` (config, docs, tests). I did **not**
  execute the real binary (`--version`), so the build line is corroborated by retained records, not re-read live.
- Harness checkouts (read-only): `/home/dowling/r1_trackp/autoresearch_harness` → `897d83c8…` (clean);
  `/home/dowling/exam-x/work/autoresearch_harness` → `897d83c8…`; `/home/dowling/autoresearch_harness` → `3c80b53c…`.
  Config `harness_commit = 897d83c8…` therefore matches the sibling harness of the candidate run locations
  (`r1_trackp/…` and `exam-x/work/…`) but **not** `/home/dowling/autoresearch_harness`.
- I did **not** open, flock, stat-in-isolation or modify `/home/dowling/r1_locks/gpu0.lock`; I only saw its
  parent-directory listing. No `/home/dowling/exam-x` or `/home/dowling/r1_tracks` writes were made.

### 2.3 kcmp / Yama synthetic probe on TASL-2 (own processes, own /tmp dir, CPU only)

Observed **2026-10-31T23:24:39Z**, kernel `6.8.0-136-generic`, `ptrace_scope=1`, under
`/tmp/rvw_kcmp_synth_2229411` (new file + own forked child; exited naturally):

| probe | result |
|---|---|
| child → parent `kcmp(KCMP_FILE)` (descendant→ancestor) | `rc=0, errno=0` |
| child → parent `PTRACE_ATTACH` | `-1, errno=1 (EPERM)` |
| parent → child `kcmp(KCMP_FILE)` (ancestor→descendant) | `rc=0, errno=0` |
| parent → child `PTRACE_ATTACH` | `0` |

This **confirms the implementer's host claim**: on this kernel a descendant can `kcmp` its ancestor
(`rc=0`) while `PTRACE_ATTACH` is `EPERM` — Yama mode 1 restricts attach, not the `kcmp` READ permission.
The reviewed code does **not** rely on that permissiveness: it uses only ancestor→descendant kcmp and
treats `EPERM`/error as never-SAME, which the tests exercise (`test_eperm_kcmp_keeps_the_lock`,
`test_server_inheritance_fails_closed_when_kcmp_is_not_same`). So the surprising host property is
harmless to the design and is correctly disclosed.

### 2.4 FD-number preservation through `Popen` (synthetic, Mac)

I opened a file with `O_CLOEXEC`, passed it with `subprocess.Popen(..., pass_fds=(fd,))`, and the child
observed the **same fd number** and the same dev/ino (`CHILD_SAW_FD 3`). CPython preserves the number and
clears `CLOEXEC` for kept fds, so the production `O_CLOEXEC` lease fd survives the
guardian→runner→worker→llama-server `pass_fds` edges at the same number (also exercised by
`test_stage_a_run_job_passes_the_verified_fd_to_the_worker` and
`test_native_server_start_passes_the_fd_and_records_inheritance`). This is synthetic proof of the Python
plumbing; the real llama-server's retention is host-level and **NOT CHECKABLE** here.

### 2.5 Synthetic demonstration of the completion-set defect

A CPU-only script built the exact trees the runner collector and the guardian use, with one main server
record under `out/servers/cand/` and one qualification-probe record under
`out/cand/stage-a/32768/qualification/probe_…/` (as the real probe writes it):

```
runner rglob  : ['cand/stage-a/32768/qualification/probe_…/llama_server_9001.json',
                 'servers/cand/llama_server_9000.json']
guardian glob : ['servers/cand/llama_server_9000.json']
counts        : 2 1
guardian.validate_completion(...) -> STOP: completion server count differs from the record files
```

This is the core of blocking defect **B2**.

### 2.6 Stopped-fixture non-retry check

- `grep -rn 'd61db5e9b02188f7|d3_namespace_fixture'` over the core snapshot and the extra snapshot → **no matches**.
- The only `namespace_fixture` identifiers in the reviewed tree are the synthetic-only validator
  `r1/exam/cache_namespace_fixture.py` and its test `r1/tests/test_exam_namespace_fixture.py`, which accept
  caller-supplied dictionaries labelled `D3_NAMESPACE_SYNTHETIC_FIXTURE_ONLY/v1` and never touch `/tmp` or
  any host process.
- `r1/tests/test_exam_namespace_fixture_program.py` is likewise synthetic.
- The stopped fixture's directory `mtime`/`ctime` (1793446875) predates this work and I made no access.

### 2.7 P.3a / B.1 / B.2 STOP preservation

- `r1/exam/campaign.py:69-70` (`collect`) and `r1/scripts/exam_runner.py:142` (`evidence`) hard-STOP B1/B2;
  `runtime.py:222-223` hard-STOPs `start` for B1/B2; `exam_runner.py:256-257` stops the B1/B2 CLI before
  config/runner; `observer.py` now requires a durable journal and `require_d3_evidence()`.
- No P.3a/B.2 enabling change was found; the changed `observer_for_campaign`/`SelfForecastObserver` paths are
  behind the B1/B2 STOP.
- The `RuntimeError` messages are the expected "reviewed harness pin and observer cache evidence not implemented".

---

## 3. Prior independent-review findings — per-item verdicts

### Finding 1 — qualification `MECHANICAL_FAILURE` nonzero exit made the 32k→16k fallback unreachable — **FIXED (verified)**
- `r1/exam/qualify.py:70-78` `qualification_exit_code`: `PASS`→0; `MECHANICAL_FAILURE`→0 **only** with
  `allocation_failure_evidence.kind == cuda_allocation_out_of_memory` and `healthy_idle_after_stop is True`;
  everything else →1.
- `r1/scripts/exam_runner.py:19-43` `run_fresh_qualification` refuses an existing attempt
  (`mkdir(exist_ok=False)`), binds `model_sha256`+`ctx`, and re-verifies the OOM/idle evidence; a missing/
  unverified MECHANICAL_FAILURE is `PreparationStop`, not a fallback.
- `r1/scripts/exam_runner.py:111-120` falls back to 16384 only on `MechanicalFailure`, and only when no
  server is live; a live service turns it into `PreparationStop("preserve Stage A server after failure")`.
- Infrastructure failures in the qualification worker are nonzero exits and are re-raised by `run_job`
  (`exam_runner.py` `if self.child.returncode: raise RuntimeError(...)`), so they bubble; they are never
  converted to a model failure.
- Negative tests exist and are **not vacuous**:
  `test_qualification_exit_protocol_allows_only_bound_oom_fallback`,
  `test_fake_32k_oom_falls_back_to_16k_only_after_bound_receipt`,
  `test_unverified_mechanical_failure_cannot_fallback`,
  `test_qualification_worker_stop_not_swallowed_even_if_output_exists`.

### Finding 2 — guardian liveness/inode/PID alone could not prove the same OFD; judge the new inheritance proof — **ADDRESSED / LABELLED, with a bounded claim**
The snapshot implements and labels exactly the requested evidence:
- Child→guardian edge: guardian `/proc` witness (`pid` + `start_ticks` + `state` + `/proc/<pid>/fd/<fd>`
  dev/ino/uid) **plus** a flock re-lock/independent-contender test labelled
  `flock_relock_while_guardian_live` (`cooperative_lease.py:140-234`, `cache_runtime.py:86-128`).
- Guardian ancestor→runner `kcmp(KCMP_FILE)` with `pass_fds` (`trackx_lease_guardian.py:641-666`); a nonzero
  rc or `EPERM` is a STOP+hold, and an error is never SAME (`_kcmp_check`, `kcmp_file_result`).
- Runner/worker ancestor→server `kcmp` + `/proc` fd dev/ino + exact FD set + pid/start-ticks/ppid
  (`cache_runtime.py:253-332`; `llama_server_instance.py:404-426`).
- Worker re-checks the recorded server facts without upward kcmp (correctly, since the worker is not the
  server's ancestor) (`cache_runtime.py:335-387`).
The synthetic-lock repro from finding 2 no longer applies because the guardian's spawn-time kcmp proves the
runner holds the guardian's OFD, and the later re-lock/contender samples detect divergence. The residual
limitations are explicitly recorded (`same-UID attacker`, `guardian death between samples`, `PID reuse`,
`network FS`, `continuous possession NOT_CHECKABLE`) rather than claimed away. This is acceptable as a
**cooperative** proof; it is not host-global exclusivity.

### Finding 3 — real request/response/cache evidence, error propagation, cold true-first, served identity — **IMPLEMENTED, but REAL EVIDENCE NOT CHECKABLE**
- Static design: `cache_descriptive.true_replay` runs the 50 frozen prompts first with `cache_prompt:true`
  and requires the first call to have `cache_n == 0` (`cache_evidence.py:31-32`); `cache_false` enforces
  `cache_prompt is False` on every primary call and refuses a cache hit; `cache_order.validate_local_order`
  checks true-before-false ordering, seriality, per-call census, exact request binding and reordering;
  `cache_io` preserves chunks/`IncompleteRead`; `cache_false`/`cache_nongen` wrap every evidence failure in
  `D3EvidenceStop` (never a model parse failure); `Elastic` served identity is checked via `/v1/models`,
  `/props` and `capture_parent_identity`/`validate_worker_binding`.
- The synthetic tests are real and negative-heavy (see the preflight file list and `test_exam_cache_order.py`).
- **However**, no real request/response/cache evidence exists in the snapshot, and the run paths that would
  produce it are blocked (B1) or cannot release (B2). I therefore cannot accept finding 3 as "real evidence
  reviewed"; it is *implementation reviewed statically + synthetically*.

### Finding 4 — `hold_forever` BrokenPipe release, and no accepted normal-completion release contract — **PARTIALLY FIXED**
- BrokenPipe/hold side: **FIXED and negatively tested.** `hold_forever` ignores SIGPIPE and the catching
  terminating signals, redirects fd 1/2 to `/dev/null`, wraps STOP evidence in best effort, never closes the
  lock fd or calls `LOCK_UN`, and swallows every exception (`trackx_lease_guardian.py:520-568`); tests
  `test_closed_stdout_and_unwritable_evidence_still_hold` and
  `test_hold_forever_survives_broken_stdout_without_evidence` reproduce the former repro and pass.
- Normal-completion release contract: **exists but is broken in the integrated path** — see blocking defect
  **B2**. The low-level `write_completion` is well tested, and the guardian's `validate_completion` is well
  tested against synthetic fixtures, but the runner's collector and the guardian's record glob do not agree,
  so a genuinely complete Stage A cannot be validated for release.

---

## 4. Author-gate conditional checks (implementation, not prose)

**(a) Can any path reach generation before auth + cold + inheritance evidence?**
Statically no: `stage_a.post`/`fit_prefill`/`run_stage_a` call `require_d3_evidence()` (→
`require_authorized_stagea`); `authorize_cooperative_stagea` requires explicit `cache_prompt:false` +
`d3_policy` and a live, held, inherited lease fd; `capture_parent_identity` + `reject_unverified_cold` precede
`run_job`; `run_job` re-verifies `verified_lease_fd()` before spawning; the worker re-authorizes and
`validate_worker_binding` re-derives identity; `FalseCallRecorder` refuses any `cache_prompt` other than
`False`; `verify_server_lease_inheritance` runs inside `inst.start` before the instance is returned and again
before `capture_parent_identity`. `/health`, `/v1/models`, `/props` are issued during start/identity binding
before the inheritance proof completes, but they are not generation/chat requests; `/health` is the trigger
for the proof. **Pass statically.** In practice no path reaches generation at all because of **B1**.

**(b) Can an infrastructure STOP be converted into a model failure or a fallback?**
No: `D3EvidenceStop` is re-raised (`stage_a.py:211-212,246-247`); `PreparationStop` bubbles through
`exam_runner.main` to STOPPED; `MechanicalFailure` is raised only by the qualification/normal
`server()` paths; `qualification_exit_code` returns 0 only for the evidenced OOM; `run_fresh_qualification`
re-verifies. **Pass** (tests exercise the negatives).

**(c) Can a STOP after acquisition ever release/unlock or signal anything?**
No: after `fd` is acquired, `run()`'s `except BaseException` always enters `_retain_forever` (`guardian:690-693`);
there is no `LOCK_UN` in the guardian; `_release` only runs on a fully validated completion; `hold_forever`
never closes the lock fd and never signals; the runner's Stage A STOP path does not call `stop_tree`/`stop`
(`runtime.py:411-412`, `close(preserve_running=True)` returns immediately), and `handle_live_orphan` refuses to
signal a Stage A live prior server. **Pass** (tests: termination signals, closed stdout, non-signalling preserve).

**(d) Does the completion contract really prove every spawned native server is dead before release?**
**FAIL.** The runner collects every `llama_server_*.json` under the run root, but the guardian only inspects
`<batch_state.parent>/servers/*/llama_server_*.json`. In production the qualification probe always writes
records under `<out>/<id>/stage-a/<ctx>/qualification/probe_*/`, so the counts disagree and the guardian raises
`STOP: completion server count differs from the record files` and holds forever. Even if the collector glob
were narrowed to `servers/*`, the guardian's evidence set would then omit the lease-bearing native servers
started by the probe (and any future non-`servers/` server), so the guard would no longer check that *every*
spawned native server is dead. The guard can accept a completion whose `servers` list is only a subset of the
native servers it spawned. This is **B2**.

**(e) Is the FD/OFD claim sound?** See §5.

**(f) Config placeholders / pins for TASL-2 now?**
- `prompts`, `prompts_sha256`, `binary_sha256`, `gpu_uuid` — **verified on TASL-2** (see §2.2).
- `build` — **corroborated** by retained portal records; **not** re-read from the live binary (running the
  binary is outside my permitted scope) → NOT CHECKABLE.
- `harness_commit = 897d83c8…` — matches `/home/dowling/r1_trackp/autoresearch_harness` and
  `/home/dowling/exam-x/work/autoresearch_harness`, **not** `/home/dowling/autoresearch_harness`; the run
  checkout must be a sibling of the 897d83c8 harness, or `AR_HARNESS_ROOT` must be set (the launcher's manifest
  environment does not set it).
- `paper_commit = "COMMIT_PENDING"` — **unresolved in the snapshot**; `trackx_stagea_launch.py:145` refuses
  until the run config is bound to the checked-out commit. The README discloses this; it is a run-copy
  condition, not a code bug, but the snapshot config is not directly runnable.
- `placeholders()` only flags `TODO_*` strings (`runtime.py:71-74`), so `COMMIT_PENDING` is *not* reported by
  `exam_runner --check-config` (`exam_runner.py:269` prints `{"valid": true}` for an unbound pin). Minor
  false-positive.

**(g) Does the launcher fail closed, and is the printed guardian command consistent?**
- `absolute_new` refuses relative/existing/missing-parent; `existing_regular` refuses symlink/multilink lock;
  manifest/evidence paths are refused if they already exist (`trackx_stagea_launch.py:39-60,180-182`); the
  checkout must be clean and `paper_commit == HEAD` (`:140-146`); the config/registry/model/binary/build/prompt
  pins are checked before writing (`:148-169`); the printed guardian command uses exactly the guardian's
  `--lock/--manifest/--manifest-sha256/--evidence-dir` CLI (`:189-201` vs `guardian:707-715`), and the manifest
  schema matches `MANIFEST_KEYS` (`:171-177`). **Pass** for the standard Stage A manifest.
- Gaps: `--python` is not `required=True` (`:109,127`) so omitting it raises `TypeError: Path(None)` (not a
  clean `LaunchStop`); there is **no reviewed manifest builder for the preflight fixture** — the launcher
  hard-codes `argv[1] = exam_runner.py` (`:173-174`) while the guardian requires
  `argv[1] == --expected-runner` (`guardian:278-279,307-308`), so the preflight needs a hand-built manifest
  plus `--expected-runner r1/tests/stagea_lease_preflight.py`. The printed command does not include
  `--expected-runner` (the default is correct for Stage A only).

**(h) Do the tests really exercise the negatives, or are they vacuous?**
Largely genuine: the guardian tests spawn real synthetic guardian/runner subprocesses and assert holds/releases
with a fresh synthetic lock; BrokenPipe, SIGTERM/HUP/INT, kcmp failure/EPERM, live-server, tampered digest,
non-overwrite, missing lock, and launcher-manifest negatives are real. Cache order reordering/batching/census
negatives are real. Qualification fallback negatives are real. **One test masks the release defect**:
`test_public_start_still_stops_stage_a_dispatch` (`test_cooperative_lease.py:526-529`) asserts the still-closed
`ExamRunner.start`, so the suite is green while Stage A is disabled; and the integrated runner→guardian
completion path has no test.

---

## 5. FD/OFD inheritance assessment

**Proved (ancestor→descendant, under the cooperative assumption):**
1. Guardian acquires an exclusive flock on the existing inode, requires stable regular/nlink=1, and proves an
   independent contender is blocked (`guardian:312-374`). It never creates/replaces/unlinks the lock and never
   `LOCK_UN`s.
2. Guardian passes the same fd via `pass_fds=(fd,)` to the runner (fd number preserved; empirically verified)
   and then calls `kcmp(KCMP_FILE)` with `pid_a=runner, pid_b=guardian` (ancestor→descendant). `rc != 0` or
   `EPERM/None` → STOP + hold. This proves the runner holds the **same open file description** as the guardian
   at spawn (`guardian:641-666`).
3. Runner re-verifies the held OFD and guardian liveness with `assert_held_and_bound`: `/proc` guardian
   pid/start-tick/state, `/proc/<guardian>/fd/<fd>` dev/ino/uid, first contender blocked, re-flock of the same
   fd, second contender blocked, guardian alive after each sample (`cooperative_lease.py:140-234`). This is
   labelled `flock_relock_while_guardian_live`; it is a **sampled cooperative check**, not a kcmp proof of the
   ongoing child→guardian OFD equality, but the spawn-time kcmp already established equality and the samples
   detect later divergence.
4. Runner starts the native server with `pass_fds=(lease_fd,)`; once healthy it calls
   `verify_server_lease_inheritance`: `kcmp(runner, server, fd, fd)`, `/proc/<server>/fd/<lease_fd>` dev/ino,
   exact FD set `[lease_fd]`, server start ticks and `ppid == runner`, and persists the
   `lease_inheritance` row in the server record (`cache_runtime.py:253-332`,
   `llama_server_instance.py:404-426`). The same row is copied beside the record and re-validated by the
   guardian in the completion (`guardian:479-508`).
5. EPERM/unsupported ABI/bad args never count as SAME (`kcmp_file_result` returns `(None, …)`; callers require
   `rc == 0`). My TASL-2 synthetic confirms the host quirk (descendant→ancestor kcmp is allowed while
   `PTRACE_ATTACH` is EPERM); the code does not use that direction, and the tests prove EPERM is a hold.

**Not proved:** continuous possession of the same OFD between samples by the child→guardian edge; guardian
death between samples; PID reuse; network filesystem flock semantics; same-UID interference (author
assumption). These are explicitly labelled in the records and docstrings.

**NOT CHECKABLE in this review:** whether the real pinned `llama-server` retains the inherited FD (does not
close/dup it) — this requires the real binary on the GPU host and is precisely what the preflight fixture is
meant to establish. As frozen, the preflight cannot establish it because of **B3**. Also NOT CHECKABLE:
host-global single-server state, and same-UID non-interference.

---

## 6. BLOCKING defects

### B1 — Stage A cannot execute: the public dispatch is still hard-STOPped
- `files/r1/exam/runtime.py:219-224` (`ExamRunner.start`):
  `if phase=='stage-a': raise PreparationStop('STOP: D3 cold-cache guardian/lease integration not independently verified')`.
  The next line (`if phase=='stage-a': refuse_existing_stage_a_output(self.out)`) is unreachable.
- `files/r1/scripts/exam_runner.py:279-280` calls `runner.start(a.phase)` before `stage_a(...)`; the guardian
  launches exactly `exam_runner.py stage-a` (`trackx_stagea_launch.py:173-174`), so the guardian-spawned runner
  raises this STOP, exits 1, and the guardian holds the lock forever (`guardian:675-676`).
- `files/r1/scripts/exam_runner.py:57` docstring: "Reviewed implementation only; guarded public entry is still STOP."
- `files/r1/tests/test_cooperative_lease.py:526-529` asserts the STOP, so the green suite masks the fact that
  the author's required Stage A run cannot start.
- This contradicts `README.md` ("The draft enables the Stage A entry points … `ExamRunner.start` for stage-a")
  and the author gate's "Stage A runs on a NEW dedicated replay server". Either the README claim is false, or
  the artifact is intentionally gated and the frozen bytes are not the runnable bytes; either way, **ACCEPT is
  not possible for a Stage A release without a newly reviewed change**.

### B2 — Normal-completion release is unprovable: collector/guardian record-set mismatch
- `files/r1/scripts/exam_runner.py:234` collects `runner.out.rglob('llama_server_*.json')` (all records under
  the run root, including the qualification probe records).
- `files/r1/scripts/trackx_lease_guardian.py:460-462` validates only
  `Path(batch_state).parent/'servers'/'*/llama_server_*.json'`; `:493-494` raises
  `'STOP: completion server count differs from the record files'` on any count mismatch.
- Production **always** runs the qualification probe (`files/r1/scripts/exam_runner.py:84-93`; `not dryrun`
  is true), and the probe always writes a stopped record under
  `<out>/<id>/stage-a/<ctx>/qualification/probe_<stamp>/llama_server_*.json`
  (`files/r1/scripts/llamacpp_probe.py:197-233`; `files/r1/scripts/llama_server_instance.py:246,276-277`).
- CPU-only reproduction: guardian `validate_completion` → `STOP: completion server count differs from the
  record files` (2 collected vs 1 visible).
- Consequence: after a genuinely clean Stage A run, the guardian will **never** validate the completion and
  will retain the GPU flock indefinitely. This fails prior finding 4's required "accepted normal-completion
  release contract". The green tests do not catch it because the release test synthesizes the guardian side
  and the low-level writer, not the runner→guardian integration.
- Related survivor gap: the guardian's evidence set is only `servers/*`, so a native server started outside
  that directory (qualification/CPU-control probe) is not liveness-checked. A correct fix must make the
  runner emit a complete server set and the guardian verify **every** one of those pids (absent or
  PID-reused), not just a narrowing of the glob.

### B3 — Supplementary preflight fixture cannot be released by the guardian (preflight verdict: BLOCK)
- `files/r1/tests/stagea_lease_preflight.py:82` starts the server under `out / 'server'` (singular), so the
  record is `out/server/llama_server_<port>.json`; `:131-138` writes `batch_state.json` at `out/` and calls
  `write_completion`.
- The guardian expects `out/servers/*/llama_server_*.json` (`guardian:460-466`). `out/servers` does not exist,
  so it raises `STOP: completion names no server record files under the run root` and holds the lock forever.
  The preflight therefore cannot complete the normal-completion release it is designed to demonstrate.
- `:111` records `server_process.ppid = os.getppid()` — that is the preflight's parent (the guardian), not the
  server's parent pid; the evidence field is inaccurate.
- The fixture is not launchable by the reviewed launcher: the launcher fixes `argv[1]` to `exam_runner.py`
  (`trackx_stagea_launch.py:173-174`) and the guardian requires `argv[1] == expected_runner`
  (`guardian:278-279,307-308`); a preflight run needs a hand-built manifest and
  `--expected-runner r1/tests/stagea_lease_preflight.py`, for which no reviewed tool exists.
- The supplementary guard tests (`test_stagea_lease_preflight.py`) only cover the missing-evidence-dir and
  missing-FD refusals (2 tests); there is no completion-integration test, which is why the defect is invisible.
- The **two-step arrangement itself is acceptable in principle** as evidence tooling (preflight first, then a
  full Stage A receiving review), but **as frozen the preflight cannot produce a validated release**, so
  step 1 of the Lead's plan is blocked until B3 is fixed and re-reviewed.

---

## 7. Non-blocking defects / gaps (to fix or carry as conditions)

- **C1** Run config is not bound: `paper_commit: "COMMIT_PENDING"` (`r1/scripts/configs/exam_portal.json:21`);
  the launcher refuses (`trackx_stagea_launch.py:145`). The run copy must bind it to the accepted commit and be
  pinned; the snapshot config bytes are not directly runnable. (README discloses.)
- **C2** Harness pin: `897d83c8…` matches the `r1_trackp` and `exam-x/work` sibling harness checkouts, not
  `/home/dowling/autoresearch_harness` (`3c80b53c…`). The manifest environment omits `AR_HARNESS_ROOT`
  (`trackx_stagea_launch.py:82-101`), and `runtime.py:205-206` checks only `rev-parse HEAD` (not a dirty tree)
  and the manifest does not SHA-pin harness files. The run checkout must be a sibling of the 897d83c8 harness
  and clean; add a harness-clean/`AR_HARNESS_ROOT` check and pins.
- **C3** `trackx_stagea_launch.py:109,127`: `--python` not `required=True`; omitted → `TypeError: Path(None)`
  instead of a clean STOP.
- **C4** `r1/exam/stage_a.py:292` stale comment "The current checker always STOPs" — `reject_unverified_cold`
  now passes for a valid identity; update the prose so reviewers are not misled.
- **C5** `placeholders()` (`runtime.py:71-74`) only flags `TODO_*`, so `--check-config` reports `valid: true`
  for an unbound `COMMIT_PENDING`; treat `COMMIT_PENDING` as unresolved.
- **C6** The snapshot root has an unlisted `.sums_tmp`; remove it before the branch commit (not in `files/`, so
  no hash impact).
- **C7** Integrated completion path is untested; add a test that runs the runner's `_write_lease_completion`
  set against the guardian's `validate_completion` (including a qualification probe record) so B2 cannot recur.
- **C8** `trackx_stagea_launch.py` should either build a pinned preflight manifest or the fixture must be
  launched by a reviewed equivalent; the printed guardian command should include the `--expected-runner`
  actually required for the preflight.

---

## 8. NOT CHECKABLE items (label, do not assume)

1. Real pinned `llama-server` FD retention / non-close / non-dup behavior on the GPU host — requires the real
   binary run; the frozen preflight cannot validate it (B3).
2. Real Stage A request/response/cache evidence (cold true-first zero cached, `cache_prompt:false` primary
   calls, journal ordering, served identity) — requires the real run, which is blocked (B1) and cannot release
   (B2).
3. Real `/proc`/`nvidia-smi` census and VRAM telemetry in the actual run.
4. Host-global single-server / exclusivity — author gate says NOT_CHECKABLE.
5. Same-UID non-interference — author assumption, not measured.
6. Fresh `llama-server --version` build-line read (running the binary is outside my permitted scope); only
   retained-record corroboration was possible.
7. Whether the stopped namespace fixture's *contents* were modified — only directory `mtime`/`ctime` and the
   absence of any retry reference could be checked; no baseline content hashes exist for it.
8. Real `/home/dowling/r1_locks/gpu0.lock` state — I did not access it (forbidden); only its parent directory
   was listed.
9. The actual run copy location, bound `paper_commit`, and the final manifest bytes — not yet created; the
   harness pin is only valid for a sibling of the 897d83c8 harness.
10. Base-vs-live full `r1/tests` failure diff for the *slow c3/desktop* modules — the full live run completed
    (`25 failed, 779 passed, 12 skipped`) and the patch-adjacent failing modules reproduce **identically** on
    base (12 same-name failures, §2.1a), but I did not run the slow `test_c3_sweep_dryrun`/desktop modules on
    base; that residual part of the "pre-existing failures" claim is partially verified, not fully diffed.

---

## 9. Final verdict

**BLOCK.**

The snapshot is internally consistent and well tested as **synthetic/CPU evidence**, the snapshot hashes are
correct (`5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486`), prior finding 1 is fixed, the
BrokenPipe hold is fixed, and the FD/OFD ancestor→descendant proof is sound under the cooperative assumption.
It nevertheless cannot be accepted as the Stage A cooperative-lease release because:

1. **B1** — `ExamRunner.start('stage-a')` still unconditionally STOPs (`files/r1/exam/runtime.py:219-224`),
   and `exam_runner.main` reaches it before the Stage A flow (`files/r1/scripts/exam_runner.py:279-280`), so
   the guardian-spawned runner cannot run Stage A at all; the README's "enables … `ExamRunner.start` for
   stage-a" is false, and the test `test_public_start_still_stops_stage_a_dispatch` enshrines the defect.
2. **B2** — the completion collector (`files/r1/scripts/exam_runner.py:234`) and the guardian's record glob
   (`files/r1/scripts/trackx_lease_guardian.py:460-462,493-494`) disagree for the qualification probe records
   that production always creates, so a genuinely complete Stage A can never be validated for release; the
   guardian would retain the GPU flock forever. This is a real failure of prior finding 4's normal-completion
   contract.
3. **B3** — the supplementary preflight fixture writes its server record under `out/server` instead of
   `out/servers/*` (`files/r1/tests/stagea_lease_preflight.py:82,131-138`), so the guardian rejects its
   completion and holds forever; the two-step plan's step 1 cannot produce a validated release as frozen.

To move to ACCEPT after fixes, at minimum: (i) remove/flip the `ExamRunner.start` gate (or publish separately
reviewed enabling bytes) and re-run the negative tests, (ii) make the runner's completion server set and the
guardian's validation set identical and cover **every** spawned native server (main + qualification/CPU-control
probes), with an integrated runner→guardian test, (iii) fix the preflight record path to match the guardian and
add the missing completion-integration test (and a reviewed preflight manifest path), (iv) bind `paper_commit`
in the run config and pin the bound copy, (v) pin/clean-check the harness or set `AR_HARNESS_ROOT`.
Until then, **BLOCK**, and the frozen preflight must **not** be run (it would print success while the guardian
retains the lock, misleading the receiving review).

---

## 10. Appendix — reviewed target file hashes (from SHA256SUMS)

```
39975f8c751c84df349babb8bab84e106fb48c87364dc4f130d120c62f669f5f  files/r1/scripts/trackx_lease_guardian.py
b922e314f9bc3d7f0c8daa8b4040fcd8735f215bbd839f3821c2c83dc3ff9b97  files/r1/scripts/trackx_stagea_launch.py
d739bc06edce9e0c898f9d998f05ed1ef815e80c52990545a2cafb2cfe15c9b7  files/r1/scripts/exam_runner.py
26ba2c19dc724607db28681d5b4aea341d46e1b474f8f5c045a8092839151605  files/r1/scripts/llama_server_instance.py
d2f93f860114e8fe80d398117852b735fbbd816552c7171201a5f25baf011795  files/r1/scripts/llamacpp_probe.py
4440d867aabdf5ee13c312143b41ef1c09b7a92fc365dd3a3d19d479c125d9dd  files/r1/exam/cooperative_lease.py
12b56012de138fb9a2d03f8a98b122dc218487c2b6da174de2023617c895189b  files/r1/exam/cache_runtime.py
dddd1cc0b5d369a719be366a1f67f2ebca61ef906d224427347f079ea7a05fd2  files/r1/exam/runtime.py
4ae79faa07d01f47353206c44c1d8137925088da46a8793aeaad4e966640996a  files/r1/exam/stage_a.py
0e94015a9ac36df4da6fa45184a4c17986d02082de3b85844ba9c5bf6841cce8  files/r1/exam/qualify.py
deed413c27f8d7700196a7cdb2dc83b09afac64b4e100700bff328eee16eeaf5  files/r1/scripts/configs/exam_portal.json
b7a04c923583c5847088621b67b7dbc37c4750b74dc264ef37d385767f8bc13f  files/r1/tests/test_trackx_lease_guardian.py
75057bbe4dc14edb359a7c71631718004c6ec1e2444b796800c6ecfe929edd3b  files/r1/tests/test_cooperative_lease.py
```

Supplementary fixture:
```
ca7c0de433997f3c5fde7436681bab98061306986d387c1bb4a598a9012e7640  stagea_lease_preflight.py
3ea9cc0324f2c011a423007114fab1a12f5e09f3fa0c384e508b47ad82989597  test_stagea_lease_preflight.py
```

The full accepted file set is exactly the 48 entries in the core snapshot `SHA256SUMS`
(`5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486`) plus the 3 entries in the supplementary
`SHA256SUMS` (`ec8dbb29ab3da8ad53ea3cbecc1bd98a4b4fba00bc388bc212baa1e52dbb97a9`). No file in either snapshot was
modified by this review; the transient `__pycache__` artifact described in §1.1 was removed and the frozen
state re-verified.

---

## 11. v3 re-review after the BLOCK (2026-11-01)

This section supersedes the v2 verdict in §9 for the frozen v3 artifact. Everything in §1–§8 that is not
explicitly restated here remains the v2 analysis (and remains valid for the unchanged code); the v3 deltas
were re-read and independently re-probed.

### 11.1 Frozen v3 artifact identity (verified)

| Item | Value |
|---|---|
| Core v3 snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v3` |
| v3 `SHA256SUMS` SHA-256 | `8f033b8143a03808a703b9494135563092be0ec5b4f2dee2bdb204550733413d` — **verified** |
| v3 entries | 51 listed = 49 `files/**` + `tracked.patch` + `README.md`; `shasum -a 256 -c` → **51/51 OK** |
| v3 supplementary | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v3-extra`, `SHA256SUMS` = `1fce75bb510daed44f1eed613d41e153c54aea334f564ba9f47e864c4b1d6b82` — **verified** (3/3 OK) |
| v1 unchanged | `SHA256SUMS` still `5f2d25bcdf209aaee54ddc1f44d1b59f3308f3f1ad01aa75a54cb877029398f9` — **unchanged** |
| v2 unchanged | `SHA256SUMS` still `5d8b1065a32000d7f4c748bfd53f8e0e9cc678c87a87355becb126d4a1a32486` — **unchanged** |
| Live worktree | `files/**` == `/private/tmp/paper-b-stagea-cooperative-20261031` for all 49 files (0 mismatches); `tracked.patch` == live `git diff`; HEAD `1be426f` |
| Core vs extra preflight | the core now also carries `r1/tests/stagea_lease_preflight.py` (`730561ad…`) and `test_stagea_lease_preflight.py` (`3ea9cc03…`), **byte-identical** to the v3-extra copies |

Delta v2→v3 (verified by `diff -u` of `files/`): 3 new files (`stagea_lease_preflight.py`,
`test_stagea_completion.py`, `test_stagea_lease_preflight.py`) and 9 changed files:
`r1/exam/cooperative_lease.py`, `r1/exam/runtime.py`, `r1/scripts/exam_runner.py`,
`r1/scripts/trackx_lease_guardian.py`, `r1/scripts/trackx_stagea_launch.py`,
`r1/tests/test_cooperative_lease.py`, `r1/tests/test_exam_cache_d3_guard.py`,
`r1/tests/test_trackx_lease_guardian.py`, `r1/tests/test_trackx_stagea_launch.py`. No other file changed.

### 11.2 Re-verification of the three BLOCKs (independent synthetic probes)

**B1 — Stage A dispatch enabled.** Read `files/r1/exam/runtime.py:219-226`: the unconditional
`raise PreparationStop('STOP: D3 cold-cache guardian/lease integration not independently verified')` is
replaced by `require_authorized_stagea()` followed by the normal `refuse_existing_stage_a_output`/mkdir/
lock/`author_gate` path; `files/r1/scripts/exam_runner.py:262-276` now authorizes the cooperative D3 context
*before* constructing `ExamRunner`, so `runner.start('stage-a')` at `:279` sees the authorized context.
Independent probe: with `cache_runtime._authorized.set(True)` and a dry-run config, `ExamRunner.start('stage-a')`
**proceeds** (status `RUNNING`; the former raise is gone); an unauthorized start still STOPs before touching
output (repo test `test_runner_start_stage_a_requires_authorized_d3_context`), and `start('b1')` still raises
`PreparedStop('reviewed harness pin…')` — B1/B2 remain hard STOP.
*Test-quality note:* the renamed repo test `test_public_start_requires_authorized_d3_context_but_is_enabled`
asserts only the unauthorized STOP and the B1/B2 STOP; it does not exercise the authorized positive path
(verified here synthetically instead). Non-blocking.

**B2 — completion release provable.** Read `files/r1/scripts/trackx_lease_guardian.py:393-521`:
`COMPLETION_SERVER_KEYS` now includes `record_path`; the completion row's `record_path` must be absolute and
is `realpath`ed; the guardian recursively `os.walk`s the batch-state directory (`followlinks=False`, dot-dirs
skipped), collects every `llama_server_*.json`, rejects duplicate real paths, requires **exact set equality**
between the completion `record_path`s and the walked records (`uncovered`/`foreign` counts in the STOP), and
re-validates each record's digest, pid, start ticks, `stopped_utc` and SAME-OFD inheritance row.
`files/r1/scripts/exam_runner.py:238-240` emits `record_path` for every `runner.out.rglob('llama_server_*.json')`
record; `files/r1/exam/cooperative_lease.py` validates each `record_path` is absolute, stable, and
digest-matching, and stores `realpath`.
I re-ran the exact v2 reproduction (main record under `servers/cand/` + nested qualification-probe record)
against the v3 guardian with a synthetic completion:

| probe | result |
|---|---|
| 2 covered records (main + nested probe) | **ACCEPTED, `records_verified=2`** (the v2 2-vs-1 failure is fixed) |
| completion omits the nested record | `STOP: … (uncovered=1, foreign=0)` |
| unlisted extra nested record on disk | `STOP: … (uncovered=1, foreign=0)` |
| completion lists a record outside the run root | `STOP: … (uncovered=0, foreign=1)` |
| symlinked record *file* under the root | `STOP: unable to read pinned file` (`O_NOFOLLOW`) |
| relative `record_path` | `STOP: … record_path must be absolute` |
| `record_sha256` mismatch | `STOP: … digest/pid does not match its record file` |
| duplicate server row | `STOP: duplicate completion server pid` |
The new guardian tests are **not vacuous**: `test_nested_qualification_probe_record_is_covered_and_accepted`
(2 records, exact `record_files` set), `test_completion_rejects_record_outside_run_root_and_unlisted_nested_record`
(both negatives), `test_completion_rejects_record_path_mismatching_its_digest`; the runner-side producer is
covered by the new `test_stagea_completion.py` (nested + served records covered, unstopped/live/no-evidence STOP).

**B3 — preflight releasable.** Read the v3 preflight (`files/r1/tests/stagea_lease_preflight.py:107-141`):
it now writes `record_path` for its server record and records the real `server_ppid` from the inheritance row
instead of `os.getppid()`. The launcher (`files/r1/scripts/trackx_stagea_launch.py`) gains `--runner`/`--runner-arg`,
validates the runner is a `.py` inside the repo, prints `--expected-runner` in the guardian command, and pins
`AR_HARNESS_ROOT = <work_dir>/autoresearch_harness` in the manifest environment.
Independent probes: a synthetic preflight completion (`out/batch_state.json` + `out/server/llama_server_<port>.json`
+ completion with `record_path`) is **ACCEPTED by the v3 guardian (`records_verified=1`)**; a synthetic
preflight manifest with `argv[1]=r1/tests/stagea_lease_preflight.py` is **ACCEPTED** by
`guardian.validate_manifest(..., expected_runner=<preflight>)`, while the same manifest with
`expected_runner=<exam_runner.py>` and with a reserved `TRACKX_*` env key both STOP. The two-step arrangement
is therefore **acceptable in principle** — ACCEPT of code/config/launch, then one real-lock preflight with the
real native server, then the full Stage A with the preflight evidence in the receiving review — and the frozen
preflight can now produce a guardian-validated release.
*Test-quality note:* the new launcher test `test_runner_override_builds_preflight_argv` only greps the source
for `--runner`, `--expected-runner` and `AR_HARNESS_ROOT`; it does not exercise `main`/manifest construction.
The behavior is verified by the synthetic manifest above instead. Non-blocking.

### 11.3 Residual hardening items (non-blocking, disclosed)

- The guardian calls `os.walk(run_root, followlinks=False)` without `onerror`; Python's default silently
  skips a permission-denied subtree. I demonstrated this (a `chmod 000` subdir containing a record is skipped
  silently), so the intended "server record tree unreadable" STOP does not trigger on permissions. Under the
  author's same-UID assumption (and with the run tree created by the runner itself) this is a hardening gap,
  not a normal-path defect; passing `onerror` to raise would make it truly fail-closed.
- A **symlinked directory** under the run root is not followed (by design). A record placed through it is
  physically outside the run tree; if the completion lists it → `foreign` STOP, but if it is omitted (both
  `rglob` and the walk skip it) the guardian accepts. This requires a pre-existing symlink/same-UID mutation of
  a fresh run tree — within the disclosed cooperative assumption; recommend rejecting symlinked dirs or
  documenting this boundary.
- A record under a **dot-directory** is skipped by the guardian's walk but included by the runner's `rglob`,
  so the integrated path STOPs as `foreign` (fail-closed); a dot-dir is not created by the reviewed flow.
- Minor: stale prose remains at `files/r1/scripts/exam_runner.py:57` ("guarded public entry is still STOP") and
  `files/r1/exam/stage_a.py:292` ("The current checker always STOPs"); `trackx_stagea_launch.py:109` still
  leaves `--python` not `required=True`; a custom `--runner` without `--runner-arg` silently gets the
  `stage-a --config … --out …` argv (the preflight needs explicit `--runner-arg`).

### 11.4 Tests

- Required v3 subset (previous paths + `test_stagea_completion.py` + `test_stagea_lease_preflight.py`):
  **`366 passed, 1 skipped in 24.16s`** — exactly the claimed count (same command as §2.1).
- Full `r1/tests` v3: the run reproduced the **identical** pre-existing Mac-environment failure pattern as v2
  (c3/desktop, no `/proc`, no `nvidia-smi`, fake-server dry-runs) through ~87%, then stalled in the same
  pre-existing `test_rerun2_batch4c::test_real_runner_desktop_dryrun` nested dry-run region (the v2 run took
  440 s; this one exceeded that), so I stopped it. The patch-adjacent failing modules were already proven
  identical on the base commit in the v2 review (12 same-name failures), and every patched/new test module is
  in the 366-passing subset. No new failure was observed in the patch-relevant region. Completing the
  desktop-nested run is not needed for this acceptance and is recorded as NOT CHECKABLE.

### 11.5 Conditions of this ACCEPT

1. **Run copy binding:** the snapshot config still has `paper_commit: "COMMIT_PENDING"`; bind it to the
   accepted commit in the run copy (external, pinned copy allowed by the launcher) and keep the run checkout
   clean at that commit; `ExamRunner.__init__` requires `paper_commit` to be an ancestor of HEAD and the exam
   code to be identical between them.
2. **Harness:** the launcher now pins `AR_HARNESS_ROOT=/home/dowling/exam-x/work/autoresearch_harness`
   (read-only verified on TASL-2: HEAD `897d83c8…`, matching `harness_commit`). Confirm that path/commit on the
   run host; the runner checks only `git rev-parse HEAD` and the manifest does not SHA-pin harness files, so
   keep the harness tree clean.
3. **Two-step execution:** run the preflight once under the reviewed guardian with the real GPU flock, using
   the frozen v3/v3-extra preflight bytes and a manifest built by the reviewed launcher
   (`--runner r1/tests/stagea_lease_preflight.py --runner-arg … --expected-runner …`); its run evidence
   (real FD/OFD retention, real server identity/stop, completion release) must be clean and belongs to the
   Stage A receiving review. Only then prepare the full Stage A.
4. **Full Stage A evidence** (descriptive cold true-first zero-cached, explicit `cache_prompt:false` calls,
   per-call cache/census evidence, served identity) is for the receiving review and remains NOT CHECKABLE here.
5. Recommended hardening (not required for this ACCEPT): `os.walk(..., onerror=raise)`; reject/document
   symlinked/dot dirs; add a behaviour test for the launcher `--runner/--runner-arg`; add a repo test for the
   authorized `start('stage-a')` positive path; refresh the stale docstrings.

### 11.6 Final v3 verdict

**ACCEPT** — with the conditions in §11.5 — of the frozen v3 bytes as the reviewed Track X Stage A
cooperative-lease implementation, and of the v3-extra preflight as evidence tooling. All three v2 BLOCKs are
independently verified fixed (B1 enabled + unauthorized/B1/B2 gates intact; B2 exact record-set coverage and
the 2-vs-1 reproduction passing; B3 preflight completion and manifest validating). This ACCEPT is **not**
evidence that Stage A has run: the preflight run and the real FD/cache/VRAM evidence remain pending and
NOT CHECKABLE until that run, and the two-step arrangement proceeds only if the preflight run itself passes.

Carried-forward NOT CHECKABLE list (unchanged from §8): real pinned llama-server FD/OFD retention; real
Stage A request/response/cache evidence; real `/proc`/`nvidia-smi` census and VRAM telemetry; host-global
single-server; same-UID non-interference; fresh `--version` build-line read (retained-record corroboration
only); stopped-fixture content integrity (mtime/ctime + no retry references only); real `gpu0.lock` state
(not accessed); the concrete run copy/bound `paper_commit`/manifest bytes; and the desktop-nested full-suite
completion (partial run only).

### 11.7 v3 accepted file set

The accepted set is exactly the **51 entries** in the core v3 `SHA256SUMS`
(`8f033b8143a03808a703b9494135563092be0ec5b4f2dee2bdb204550733413d`) plus the **3 entries** in the v3-extra
`SHA256SUMS` (`1fce75bb510daed44f1eed613d41e153c54aea334f564ba9f47e864c4b1d6b82`). Key reviewed hashes:

```
c32bc8d1eb58f04d72f85cd29371ce5934b80acb4be7a9443369e634ba326738  files/r1/exam/runtime.py
989d4f1b89db06d310dafd0916d8c78d65c665fbe646c854cc89f5761e59e55f  files/r1/exam/cooperative_lease.py
e7cf4f5ee252734162dcefe40de228233a88602e9d804d03c5b24aeab3bea296  files/r1/scripts/exam_runner.py
ebdfcf4070057047be7335253bbba7f2f60449dc78159f7c76f3ac4b52f41278  files/r1/scripts/trackx_lease_guardian.py
8f23d28d9e7c6584b8cc4a08fe8f14fd65d2d599fa680c2a404730fe3f857efb  files/r1/scripts/trackx_stagea_launch.py
730561adf6f0f87d1a5d113000049141591f0f5c5fece60e8a96a543cdab9bf8  files/r1/tests/stagea_lease_preflight.py
4daee952d81786c3f68af0ba4280b0527ea0dd61e370dc5fdc6dc399129c0d4d  files/r1/tests/test_stagea_completion.py
57e14d53a8376cfe34cb39c220d949f9d337d88a8c6bbd8bbead73c00d5b31ca  files/r1/tests/test_trackx_lease_guardian.py
b543393eb729d6c702795868d84e8ca96de7c56fbb4cfd70190e62d35c216ab3  files/r1/tests/test_cooperative_lease.py
f6c6af7c9eda1d50c7112f210f0f5d6e87809cf1de01315bc733c627612eed5b  files/r1/tests/test_trackx_stagea_launch.py
3ea9cc0324f2c011a423007114fab1a12f5e09f3fa0c384e508b47ad82989597  files/r1/tests/test_stagea_lease_preflight.py
deed413c27f8d7700196a7cdb2dc83b09afac64b4e100700bff328eee16eeaf5  files/r1/scripts/configs/exam_portal.json
```

No file in any snapshot was modified by this re-review; the v3 hash checks above were re-run after the
probes, and all synthetic probes used `/tmp` fixtures or `sys.dont_write_bytecode = True` imports from the
live worktree (no snapshot `__pycache__` was created this time).

---

## 12. Pre-flight delta confirmation: C3 and C4 (2026-11-01)

Scope: the Lead's published state after the v3 ACCEPT. Commits: C1 `82dfaf5` (reviewed v3 bytes),
C2 `aa45dd1` (config binding only), C3 `d61394a` (paper-commit binding), C4 `9418d75` (verbatim
interpreter). Branch `codex/trackx-stagea-cooperative-20261031`; branch HEAD = **`9418d75`**; run checkpoint
`/home/dowling/exam-x/work/agent_paper_B` at `9418d75`, detached, **clean**, config `paper_commit=82dfaf5`.

### 12.1 Delta integrity (verified)

- C1 tree vs the accepted v3 `files/`: **0 mismatches over all 49 files** — C1 contains exactly the reviewed
  v3 bytes.
- C1 → C4 name-status: exactly **two** files — `r1/scripts/configs/exam_portal.json` and
  `r1/scripts/trackx_stagea_launch.py`. Everything else is byte-identical to the ACCEPTed v3 snapshot.
- C1 → C4 **runtime-checked no-diff** (`git diff --name-only 82dfaf5 9418d75 -- r1/exam
  r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py
  r1/headroom/e1b_collect.py`): **empty**.
- C2: only `paper_commit: "COMMIT_PENDING" → "82dfaf5"` (1 insertion / 1 deletion in the config).
- C3: only the launcher's paper-commit check (19 insertions / 2 deletions). C4: only the launcher's
  interpreter handling (8 insertions / 2 deletions).
- The live worktree HEAD is `9418d75`; the 6 untracked D3 root drafts are not part of the accepted set and are
  absent from the clean run checkpoint.
- The v3 accepted set therefore changes by exactly two file replacements (all other 47 files keep their v3
  `SHA256SUMS` hashes):
  - `r1/scripts/configs/exam_portal.json`: v3 `deed413c27f8d7700196a7cdb2dc83b09afac64b4e100700bff328eee16eeaf5`
    → C4 raw SHA-256 `dfe694a4d060378be0acdf488cb5533c3f1e80d5afcb264937d55f0014e1f9fb`.
  - `r1/scripts/trackx_stagea_launch.py`: v3 `8f23d28d9e7c6584b8cc4a08fe8f14fd65d2d599fa680c2a404730fe3f857efb`
    → C4 raw SHA-256 `df988cc2485c71cf5581f1d3d39f1e2c1d192ca2fec90cec7f953536ec82045c`.

### 12.2 C3 — ancestor + no-diff is an acceptable equivalent of condition 1

- The launcher now runs `git merge-base --is-ancestor <paper_commit> <HEAD>` (`capture_output=True`,
  `check=True`) and requires `git diff --name-only <paper_commit> -- r1/exam
  r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py
  r1/headroom/e1b_collect.py` to be empty, wrapping `CalledProcessError` in a clean
  `LaunchStop` (`files/r1/scripts/trackx_stagea_launch.py:160-173`).
- This is **exactly** the runtime rule `ExamRunner.__init__` already applies
  (`files/r1/exam/runtime.py:207-209`); the path lists match one-for-one. The old equality check was genuinely
  unsatisfiable for an in-repo config (a binding commit makes HEAD one ahead of the value it can carry).
- My condition 1 allowed an external pinned config copy; committing the config and applying the runtime rule
  is an acceptable (arguably cleaner) equivalent: the config is in the checkout and pinned by the guardian
  manifest.
- Residual trust boundary, now explicit and not a blocker: the no-diff list covers the runtime-checked code
  paths only; the launcher, guardian, config and tests are not in it. They are pinned by the guardian
  manifest file list (all `r1/**/*.py`, `r1/**/*.yaml`, the config, the prompts, the guardian, the lock; the
  `pinned_files` count is 180 py + 3 yaml + config + prompts + lock = **186**, matching the Lead's reported
  186). The manifest is built from the checked-out bytes, so the operator/reviewer must verify the run
  checkout is `9418d75`/clean and record and cross-check the printed manifest's pinned hashes against the
  accepted C4 set — this is condition M1 below, not a defect.

### 12.3 C4 — verbatim interpreter is an acceptable, real fix

- `Path(args.python).resolve()` replaced the venv path with the base interpreter, which would drop the venv's
  site-packages. TASL-2 evidence (read-only): `/home/dowling/exam-x/work/venv/bin/python` is an absolute
  symlink to `/home/dowling/.local/share/uv/python/cpython-3.13.4-linux-x86_64-gnu/bin/python3.13`; that venv
  python reports `sys.executable` = the venv path and imports numpy/scipy/transformers/yaml (`deps ok`).
  Resolving it would indeed have launched the runner without those.
- The new checks are fail-closed: `--python` must be absolute and must exist as a file, with clean
  `LaunchStop` messages (this also removes the earlier `Path(None)` `TypeError`); the manifest `argv[0]` stays
  the venv path, which the guardian accepts (absolute, basename `python`, the only interpreter constraint in
  `validate_manifest`). C4 does not weaken any manifest pin: the manifest pins script bytes, not the
  interpreter path, which is the already-disclosed boundary.
- `--print-only` cannot be reproduced here without executing the real pinned binary; the Lead's reported
  `manifest_sha256 e08363d53310ae9737d4231e286bbf00d365e64f7cb208fd7c5db6b4a83c5203` and 186 pinned files are
  consistent with the code and the count I verified (186). The manifest JSON itself must be captured in the
  preflight evidence and cross-checked (condition M1).

### 12.4 (c) Nothing else in the ACCEPT is affected

- C1 == v3 bytes for all 49 files; C1 → C4 touches only config + launcher; runtime-checked no-diff is empty.
- Relevant subset re-run on the C4 worktree: **366 passed, 1 skipped in 23.80s**; launcher tests **6 passed**.
  The full-suite failure set is the known Mac-environment one from §11.4 and is unaffected by the launcher
  delta.
- v3 conditions on config binding and harness are now satisfied for the published state: config committed at
  C2 (`paper_commit=82dfaf5`), run checkpoint clean at C4, harness `897d83c8` with the launcher pinning
  `AR_HARNESS_ROOT=/home/dowling/exam-x/work/autoresearch_harness` (verified exists, clean, 897d83c8). The
  preflight and full-Stage-A evidence conditions remain.

### 12.5 Final status and added conditions

**ACCEPT confirmed** for the published `9418d75` state. C3 and C4 are acceptable (C3 as the equivalent of
condition 1, C4 as a real fail-closed fix) and do not reopen the v3 BLOCKs; they are the only two changes to
the accepted set. In addition to the §11.5 conditions:

- **M1 (manifest/checkout):** run from `/home/dowling/exam-x/work/agent_paper_B` at `9418d75`, clean; record
  `git rev-parse HEAD` + `git status --porcelain`, and record the launcher-produced manifest JSON
  (`manifest_sha256`, pinned file rows) and cross-check the pinned hashes for the launcher/config/guardian/
  tests/exam code against this C4 accepted set. The guardian validates the manifest at startup; the printed
  manifest hash is part of the run evidence.
- **M2 (paper binding):** `paper_commit=82dfaf5`; the C1→C4 runtime-checked diff is empty (verified); the
  config/tests/launcher/guardian are manifest-pinned.
- **M3 (environment pins, already disclosed):** record the venv `sys.executable`, `sys.version`, and the
  `transformers`/`jinja2`/`tokenizers` versions with the preflight/Stage A evidence; the interpreter and venv
  remain part of the run environment, not a reviewed code pin (unchanged NOT CHECKABLE boundary).
- The preflight run and its evidence remain the next gate; do not run it until M1–M3 are recorded.

### 12.6 v4 accepted set

The accepted set is the v3 core `SHA256SUMS` (51 entries, `8f033b81…`) with the two replacements above, plus
the v3-extra entries (`1fce75bb…`, 3 entries). Net: 49 core `files/` files (two with the C4 hashes
`dfe694a4…` for the config and `df988cc2…` for the launcher) + `tracked.patch` + `README.md`, and the 3
v3-extra entries. The C1-reviewed code bytes remain exactly the v3 bytes.

No file in any snapshot was modified by this delta review; all checks were read-only (`git show`/`git diff` on
the live worktree and read-only portal probes) plus the C4 worktree test run.
