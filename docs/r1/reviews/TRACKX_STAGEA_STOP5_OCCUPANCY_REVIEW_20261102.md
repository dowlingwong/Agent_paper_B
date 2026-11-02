# Track X Stage A — scoped review of the launcher host-occupancy pre-check (v11)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-02 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` (with conditions).** The launcher now refuses to prepare a run when a visible
`llama-server` process or a GPU compute process is already present, before the manifest is written. It is
fail-closed for the observed STOP-5 cause, does not alter the runtime census, and does not change production
semantics; the helpers are explicitly documented as an occupancy check, not an exclusivity proof.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v11` |
| `SHA256SUMS` SHA-256 | `f2c6adf510a5d83e8b18dba93d818f39263fc75c30810048863fbbe18be774f8` — **verified**; 55/55 entries OK (53 files + `tracked.patch` + `README.md`) |
| Base | published config binding `746b3d6` (`paper_commit 0d4e987`, the v10 template-classification tree) |
| Delta vs v10 | only `r1/scripts/trackx_stagea_launch.py` and `r1/tests/test_trackx_stagea_launch.py`; the v10→v11 config difference is the already-published `paper_commit 0d4e987` binding |
| Files | v11 `files/` == live worktree (0 mismatches); live HEAD `746b3d6` with the launcher/test delta uncommitted |

Delta hashes: `trackx_stagea_launch.py 1bfb30c8…`, `test_trackx_stagea_launch.py 32fbc786…`.

## 2. The change

- `visible_llama_servers(proc_root='/proc')`: scans decimal `/proc` entries, reads `/proc/<pid>/exe`, and
  returns the PIDs whose executable basename is exactly `llama-server`; unreadable/vanished links are
  skipped; a missing `/proc` returns `[]`. Its docstring says explicitly: *occupancy check, not a proof of
  exclusivity; unreadable links, other executable names, other namespaces and between-sample lifetimes are
  not covered.*
- `host_occupancy_check(*, servers_fn=visible_llama_servers, apps_fn=None)`: raises `LaunchStop` if any
  visible `llama-server` exists, or (when `apps_fn` is given) if `llama_server_instance.gpu_compute_apps()`
  reports any compute process; an `apps_fn` returning `None` (nvidia-smi unavailable, e.g. Mac) skips the GPU
  part. The launcher calls it as `host_occupancy_check(apps_fn=gpu_compute_apps)`.
- Placement: in `main`, after the config path/prompts-bundle checks and **before** the commit/dirty/
  `paper_commit`/prompt-digest/binary/build/registry/model checks and the manifest write
  (`pinned_files`/`write_json`/`os.open(manifest_path)` are all later). A refusal therefore happens before
  any manifest is written; the manifest content/argv/environment are unchanged by the check.

## 3. Fail-closed, but honest about scope (questions a/b)

- **Fail-closed for the observed cause.** The STOP-5 stale diagnostic was a `llama-server` process (the
  recovery `before` shows `ornith10_9b` pid 2589942 with `-ngl 0` — a CPU-only diagnostic, i.e. *not* a GPU
  compute app). The `/proc` basename scan is exactly the guard that would have refused it; the GPU-compute-app
  check alone would not have caught that case. The check refuses on any such process, so a doomed batch is
  stopped before the manifest rather than at the first qualification.
- **Not over-broad.** It refuses only on clear occupancy: a process whose executable basename is exactly
  `llama-server`, or a GPU compute app reported by nvidia-smi. It does not scan/kill unrelated processes, does
  not require exclusivity, does not refuse on non-GPU unrelated jobs, and skips the GPU part only when
  nvidia-smi is unavailable (on the Mac, `/proc` is absent so the scan is empty). The docstring is honest that
  unreadable links, other executable names, other namespaces and between-sample lifetimes are not covered —
  the host-global single-server/same-UID assumption remains NOT_CHECKABLE, deliberately.
- **Cannot mask a later census error.** The runtime census (`cache_proc`/`capture_parent_identity`/
  `gpu_compute_apps` in `run_job`/server start) is unchanged; the launcher check is a pre-manifest guard.
  A stale process that the scan cannot see (unreadable/other-UID, or a `/proc/<pid>/exe` target ending
  `llama-server (deleted)`) would still be caught by the runtime census and STOP the batch at the first
  qualification, as STOP-5 did. The check can only refuse earlier; it cannot hide or relabel a runtime census
  failure.
- **No production semantics changed.** The delta is launcher-only (the runtime `exam_runner`/`qualify`/cache
  code is the accepted v10 tree, unchanged); the launcher's other checks, argv, environment and manifest
  content are unchanged; the check writes nothing. The `paper_commit` must remain a runtime-code commit
  ancestor with an empty runtime-path no-diff (the launcher is manifest-pinned; `paper_commit 0d4e987` still
  satisfies the ancestor/no-diff rule — the Lead's planned rebind to the v11 code commit is also fine).

## 4. Tests

v11 relevant Mac CPU subset: **386 passed, 1 skipped** — matches. The new unit tests are genuine:
`test_visible_llama_servers_and_occupancy_refusal` builds a synthetic `/proc` tree (pid 10 → `/x/llama-server`,
pid 11 → `python3`, pid 12 no `exe`) and checks `[10]` and `[]` for a missing tree;
`test_host_occupancy_check_refuses_stale_server_or_gpu_app` checks the pass case, the stale-server refusal
(`visible llama-server`), the GPU-app refusal, and the `apps_fn=None` (nvidia-smi-unavailable) pass. The
existing launcher tests (including the Mac `test_main_refuses_existing_evidence_dir_before_any_write`) still
pass with the check inserted in `main`.

## 5. STOP-5 evidence and recovery (verified read-only)

- Attempt `r1_stagea_20261102_t7d4`: `batch_state` STOPPED with `stop_reason` `root worker exit 1`; only the
  two software-anchor rows in `completed` (no `stage_a_table.json`; the 2 anchor rows are not used as
  evidence); the first qualification (`qwen25_coder_7b/.../qualification/runner.log`) ends
  `STOP: RuntimeError: STOP: observed server count or identity mismatch`; guardian `STOP.json`
  `lease_retained:true`, `retry_permitted:false`, guardian 2593920, utc 06:43:10Z.
- Cause confirmed by the recovery `before` (07:09:48Z): stale diagnostic `ornith10_9b` llama-server pid
  2589942 (`-ngl 0`, started 06:25Z), the preserved qwen25 server pid 2595132 (5732 MiB), guardian 2593920
  holding the FLOCK on inode 56251186. The `/proc`-visible stale server plus the qualification's qwen25
  server made the census see two llama-servers. (Factual note: the stale server was CPU-only, not holding GPU
  memory; the `/proc` basename scan is the relevant guard — the Lead's "holding GPU memory" wording is
  imprecise.)
- Recovery: stale server 2589942, preserved qwen25 server 2595132 and guardian 2593920 ended; `after`
  LOCK-FREE, lock size 0/inode 56251186/nlink 1, GPU 243 MiB/0 %; evidence
  `r1_stop5_shutdown_20261102T070948Z/` (before/after + hashes). Current: pids 2589942/2595132/2593920
  absent, `/proc/locks` free, lock unchanged, GPU idle, 22/22 models verified (0 failed), code clone
  `746b3d6`.
- STOP-5 evidence hashes unchanged and match the recovery `before`
  (`lease_inheritance 74155b7d…`, `runner 07ae9a17…`, `start b557b212…`, `STOP c24e1dae…`,
  `batch_state e0453a6a…`). The t7d4 batch is not reused; the new attempt is separate.

## 6. Conditions

1. Commit the v11 launcher/test delta; **rebind `paper_commit`** to the v11 code commit if that is the chosen
   binding (the launcher is not runtime-checked, so `0d4e987` also satisfies the ancestor/no-diff rule; the
   manifest pins the launcher bytes); push; clean TASL-7 checkout; rebuild the guardian manifest
   (M1/M2/M3; the launcher SHA changes).
2. Ensure no stale/preserved `llama-server` (or GPU compute app) is present at launch — the new check refuses
   otherwise; the STOP-5 recovery cleared the host.
3. Fresh TASL-7 real-lock preflight under the v11 config/manifest (the occupancy check runs in the preflight
   launcher too); then the new `t7e5` attempt in new out/evidence dirs, 22/22 models verified, continuous
   guardian lock, periodic GPU/server/lease/progress checks (the STOP-3 12 h-deadline risk note still applies),
   B1/B2 remain STOP.
4. The t7d4 anchors are not reused; the template-coverage/repair/build-pin decision remains the author's; on
   any STOP preserve the site and recover only under the author's standing authorization; orphan writes are
   not evidence.

## 7. NOT CHECKABLE in this review

- The `t7e5` behaviour (not run); whether other stale/unreadable/`(deleted)`-executable processes exist at
  launch (the check is an occupancy heuristic, not exclusivity; the runtime census remains the gate).
- Host-global single-server / same-UID non-interference (carry over, NOT_CHECKABLE).
- The future commit/binding/manifest bytes; B1/B2 on TASL-7 (STOP).

## 8. Final verdict

**`ACCEPT`** of the v11 launcher host-occupancy pre-check, with the §6 conditions. It refuses only on clear
occupancy (visible `llama-server` basename or a GPU compute app), fails closed for the real STOP-5 cause
(including the CPU-only stale server that the GPU check alone would miss), keeps the runtime census unchanged
so it cannot mask a census error, and changes no production semantics; the helpers are honestly scoped and
unit-tested. The STOP-5 evidence and recovery are verified and the t7d4 anchors are not reused.
