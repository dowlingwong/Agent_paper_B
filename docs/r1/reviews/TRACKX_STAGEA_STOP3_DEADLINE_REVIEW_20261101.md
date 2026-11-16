# Track X Stage A — scoped review of the STOP-3 deadline fix (v8, config-only)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7/TASL-2 access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`ps`/point-in-time `nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` of the v8 config-only deadline fix (`root_timeout_seconds` 3600 → 43200), with the
conditions in §7.** The change is a config-only watchdog cap, not a correctness gate: the dedicated-server
watchdog, GPU census/margin checks, lease re-verification and all offload/cache/lease/load gates are
unchanged; B1/B2 remain hard STOP; no retry/resume semantics changed; the config is pinned in the manifest.
The STOP-3 classification (tooling/deadline defect, not a model/offload/cache failure) and the
author-authorized recovery are supported by the evidence. The longer deadline's residual risk (a hung worker
holding the GPU up to 12 h) and the monitoring/conditions are recorded.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v8` |
| `SHA256SUMS` SHA-256 | `2f947752d1a0706b4ff1ccb82e6dab17a0d98e285da62642b48585b63dca2b30` — **verified**; 53/53 entries OK (51 `files/` + `tracked.patch` + `README.md`) |
| Base | published launcher-filter `d6841e6` + binding `9b7fdd1` |
| Delta vs v7 | **only** `r1/scripts/configs/exam_portal.json`: `root_timeout_seconds` 3600 → **43200**, comment updated; `paper_commit` stays `d6841e6e0b24c4fce778d51a08160b0d2eb2b1e1`; no runtime-checked path changed |
| Everything else | v8 `files/` == live worktree (0 mismatches); live HEAD `9b7fdd1` with the config delta uncommitted; all other accepted v7 bytes unchanged |

Config SHA-256 in v8: `b2bd08a76a5b06667f50ffb23979bedaf7876d02f32569384da3ed5ebc251b05`
(`tracked.patch` = 1 file, 1901 bytes; the only `+` line is `root_timeout_seconds: 43200`).

## 2. Deadline assessment — a backstop, not a weakening

- `ExamRunner.run_job` checks, each poll: the stage-a lease re-verification, free space, GPU census/margin
  (the server pid must be the only compute app and free memory ≥ 1 GiB), `RunnerWatchdog.check()`, then
  `time.monotonic()-started > cfg['root_timeout_seconds']` → `TimeoutError('STOP: campaign deadline')`; the
  exception path never signals a Stage A child (preserved), the batch records the interruption and STOPs, and
  the guardian retains the lock. `root_timeout_seconds` is a **per-`run_job`** cap (each candidate worker,
  and the qualification worker), not a scheduling target.
- The dedicated-server watchdog (`RunnerWatchdog`) is unchanged: `server_exited` (process ended),
  `unresponsive` (`health` fails `unresponsive_checks=3` consecutive polls at `health_timeout=2 s`), and
  `model_missing`/`model_unloaded` (`/v1/models` alias absent for `model_checks=3`). The GPU census/margin
  check and the lease re-verification are also unchanged. B1/B2 remain hard STOP (`runtime.start`,
  `exam_runner`, `campaign.collect`); the B1/B2 campaign worker stays TASL-2-only. Retry/resume semantics are
  untouched (`refuse_existing_stage_a_output`, `reject_stopped_batch`); a deadline STOP is a STOP, not a
  retry.
- The config is in the guardian manifest `files` list (pinned by SHA-256); `paper_commit` stays `d6841e6`
  because no runtime-checked path changed — the launcher's ancestor + no-diff rule passes
  (`r1/exam/runtime.py` etc. unchanged between `d6841e6` and the new config commit), and the manifest pins
  the config bytes. The 12 h cap is consistent with the measured ~5–6 h per always-on candidate; the author
  accepts a multi-night continuous run.

## 3. Risks recorded (the author should know)

1. **A hung worker can hold the GPU/server up to 12 h.** The watchdog catches a dead/unresponsive/unloaded
   *server* and the GPU census check catches occupancy loss, but neither detects a worker that is alive and
   making no progress while the server is healthy/idle (the `root_trials.jsonl` progress check in `run_job` is
   DRYRUN-only). The only production backstop for a spinning worker is the 12 h deadline. Mitigation: the
   planned periodic operator checks should include **progress** (journal/ledger growth, GPU compute app,
   server `/props` health) and a decision to STOP/recover; a future reviewed progress-based watchdog would
   close this gap (not required for this attempt).
2. **The qualification worker has no `RunnerWatchdog`** (`self.service` is None during qualification, so the
   watchdog is not constructed); a hung qualification probe is bounded by the probe's own HTTP/start timeouts
   and the same 12 h cap. The periodic checks should cover the qualification phase too.
3. **A future STOP still leaves the worker preserved** (the Stage A never-signal rule); the STOP-3 orphan wrote
   into the STOPped batch until the author-authorized recovery. The longer deadline reduces deadline STOPs but
   does not change the orphan/recovery handling; the operator must recover only under the author's
   authorization, and orphan writes are not Stage A evidence.
4. **Multi-night lock holding.** The guardian holds the real flock continuously for the multi-night run; a host
   crash/`SIGKILL` retains the lock via the shared OFD (guardian+server). The author accepts continuous
   holding; the periodic checks should include the guardian/lease and the lock; a STOP recovery remains the
   author's decision.
5. The 12 h cap applies to every `run_job` (including the qualification worker); it is a cap, not an expected
   runtime. The total Stage A run is multi-night across the five always-on candidates.

## 4. STOP-3 classification — supported by the evidence

Attempt `r1_stagea_20261101_t7b2` (TASL-7):
- `batch_state.json`: `status: STOPPED`, `stop_reason: "TimeoutError: STOP: campaign deadline"`,
  interruption path `muse_glimmer_30b/stage-a/32768`, time 1793567636.88; six completed entries (the two
  software anchors + `qwen25_coder_7b`, `qwen38_27b`, `qwen36_27b`, `gemma4_31b`); the muse server interval
  open; guardian `STOP.json` `lease_retained: true`, `retry_permitted: false`,
  `completed_release: false`, utc 21:13:57Z.
- Deadline arithmetic: muse server interval start 1793564025.63; the interruption/Stop 1793567636.88 →
  ~3611 s, matching the attempt's `root_timeout_seconds=3600`.
- Muse `d3_true_calls.jsonl` (643 rows; 129 attempts/128 responses/128 checks): sequence 118→119 checked
  delta **58.2 s**, i.e. ~400 calls/candidate → ~5–6 h; the deadline fired while the replay was progressing.
  The journal's final `stop` is `RemoteDisconnected` at sequence 129 (`ns` 2684075266796108), which happened
  after the runner STOP when the orphan worker's preserved server was ended at recovery — the orphan's
  post-STOP writes, not Stage A evidence.
- All offload records (`servers/*/exam_offload.json`) are `full: true`, `line: "full"`, `route: "log_line"`,
  `offloaded N/N` (qwen25 29/29; qwen38 66/66; qwen36 66/66; gemma4 61/61; muse 53/53), `cpu_fallback_lines: []`.
  Muse qualification: `status: PASS`, `footprint_mib: 16172`, `offload_route: log_line`. Muse true replay
  first call (`sequence 1`) `cached: 0`, `first_call: True` (cold true-first); sequence 2 `cached: 659`.
- **Conclusion:** the STOP-3 classification — a tooling/deadline defect, not a model/offload/cache failure — is
  supported. The attempt is NOT Stage A evidence (STOPPED; partial replay; no `stage_a_table.json`).

## 5. Recovery record — verified

- `~/exam-x/work/r1_stop3_shutdown_20261101T214210Z/before.txt` (21:42:10Z): guardian 2206536/2206538, native
  server 2256704 (muse, FD 4 → gpu0.lock per the lease record), orphan `r1.exam.stage_a` worker 2256930, lock
  `FLOCK ADVISORY WRITE 2206538 103:02:56251186`; GPU compute app 2256704. `after.txt` (21:42:22Z): no
  stage_a/llama-server/guardian processes; `LOCK-FREE`; lock size 0, inode 56251186, nlink 1; GPU 243 MiB,
  0 %.
- Current (21:44–21:46Z): pids 2256704/2256930/2206538 **absent**; `/proc/locks` has **no** line for inode
  56251186; `gpu0.lock` unchanged (dev 66306, inode 56251186, nlink 1, size 0); GPU 243 MiB/23805 MiB/0 %;
  models **22/22 `.verified`, 0 `.failed`**.
- STOP-3 evidence integrity: the five lease/batch files match the recovery `before` hashes
  (`lease_inheritance 63c8f50f…`, `runner 8e7d704f…`, `start da784443…`, `STOP a2b48b1e…`,
  `batch_state f30a71b5…`); the muse journal's hash differs from the `before` value
  (`0a428775…` now vs `6febeb69…` at the recovery start) **only** because the orphan worker wrote until it
  was ended (its final `RemoteDisconnected` is in the journal); the operator did not edit/delete/relabel the
  STOP-3 evidence. The STOP-3 batch is not resumed or reused and is not Stage A evidence.
- TASL-2 re-verified untouched (21:46Z): no experiment processes; STOP-1/STOP-2 pids 2576846/2611135/2920661/
  3005245 absent; `/proc/locks` free for inode 120090387; STOP `2d38fece…`/`d1eddb9f…` unchanged; stopped
  namespace fixture unchanged (mtime=ctime=1793446875, mode 700).

## 6. Tests

Relevant Mac CPU subset on the v8 tree: **375 passed, 1 skipped** — matches. The delta is config-only; no
test semantics changed.

## 7. Conditions

1. **Commit/push the v8 config** (root_timeout 43200), keep `paper_commit=d6841e6` (no runtime-checked path
   changed), check out clean on TASL-7, rebuild the guardian manifest (the config hash `b2bd08a7…` and the
   manifest SHA change) and verify the manifest pins the launcher/config/prompts/registry/code (M1/M2 carry
   over; M3 on TASL-7).
2. **Preflight:** re-run the TASL-7 real-lock preflight under the v8 config/manifest before `t7c3` (one model;
   the preflight is a hard gate and the new manifest/config bytes should be validated); if the Lead instead
   relies on the `t7b2` preflight, record an explicit equivalence justification that the config-only deadline
   change does not touch the preflight path and that the new manifest still pins the same code/models. The
   preflight must again show route (i) `log_line`, no fallback, FD/OFD chain, zero generation, validated
   release, M1/M2/M3.
3. **New attempt `r1_stagea_20261101_t7c3`:** new out/evidence dirs; the reviewed guardian holds the real
   lock continuously; periodic operator checks during the multi-night run — GPU compute app, server health,
   journal/ledger **progress**, guardian/lease and `/proc/locks`, disk; the 22/22 models are verified; no reuse
   of any STOP batch; B1/B2 remain STOP.
4. If a STOP occurs (including a deadline), preserve the site per the Stage A rule, do not signal/clean/retry
   without the author's authorization, and treat orphan writes as not evidence (the STOP-3 precedent).
5. Record the author's authorizations (recovery, deadline fix, multi-night continuous run) and the deadline
   change in the coordinator docs (PLAN/STATUS).

## 8. NOT CHECKABLE in this scoped review

- The new `t7c3` attempt's behaviour (deadline/hang handling) and the multi-night monitoring outcomes (not
  yet run).
- The future config commit/manifest bytes and the exact manifest SHA (M1).
- Host-global single-server / same-UID non-interference (carry over); continuous observation.
- B1/B2 on TASL-7 (not authorized; hard STOP).
- Any future STOP's orphan/recovery behaviour beyond the reviewed rules.

## 9. Final verdict

**`ACCEPT`** of the frozen v8 config-only deadline fix (`root_timeout_seconds` 3600 → 43200), with the §7
conditions. The 12 h cap is an acceptable backstop, not a correctness gate; the dedicated-server watchdog, GPU
census/margin checks and all offload/cache/lease gates are unchanged; B1/B2 remain hard STOP; no retry/resume
semantics changed; the config is manifest-pinned and `paper_commit` stays a reviewed runtime-code commit. The
STOP-3 classification (tooling/deadline, not model/offload/cache) is supported, the author-authorized recovery
is recorded and the site is lock-free with 22/22 models verified, and the STOP-3 evidence is preserved and not
reused. The residual risk (a hung worker holding the GPU up to 12 h) and the required progress-monitoring are
recorded.
