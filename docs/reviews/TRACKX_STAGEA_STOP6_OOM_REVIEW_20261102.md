# Track X Stage A — scoped review of the real-shape OOM classification (v12)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-02 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` (with conditions).** The real-shape OOM classifier is correct and fail-closed: it
classifies the actual retained STOP-6 probe/log only with retained in-attempt log + SHA, pinned
GPU/binary/model/build identity, a recorded startup exit, the cudaMalloc-OOM line (timestamp prefix allowed),
and the healthy-idle post-stop census; the worker exits 0 only for that evidenced class, the runner re-checks
the OOM evidence, and the 16k fallback is reached exactly as the runbook intends. I verified this directly on
the **actual retained STOP-6 log** (`9ec47056…`), not only on the fixture. One provenance defect: the
`stop6_nemotron_server.log` fixture is **not** byte-identical to the retained log (the probe fixture is
exact); this is a test-fixture/claim issue, not a classifier defect, and is a condition below.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v12` |
| `SHA256SUMS` SHA-256 | `3aa26eda2dbed2eac6bd57803906bfdf35a8e6090f2cac3ced6e764526b9ed92` — **verified**; 57/57 entries OK (55 files + `tracked.patch` + `README.md`) |
| Base | published occupancy commit `caa2f70` + binding `5d66967` |
| Delta vs v11 | `r1/exam/qualify.py`, `r1/scripts/exam_runner.py`, `r1/tests/test_exam_qualify.py`, `r1/tests/test_exam_qualify_guard.py`, plus fixtures `r1/tests/fixtures/stop6_nemotron_probe.json` and `stop6_nemotron_server.log` (the v11→v12 config difference is the already-published `caa2f70` binding) |
| Files | v12 `files/` == live worktree (0 mismatches); live HEAD `5d66967` with the delta uncommitted |

Delta hashes: `qualify.py 496097c1…`, `exam_runner.py 3bfaae9e…`, `test_exam_qualify.py 80a4ae82…`,
`test_exam_qualify_guard.py f322afd2…`, `stop6_nemotron_probe.json 1a941310…`,
`stop6_nemotron_server.log 1164f51e…`.

## 2. Real-shape OOM classification (question a) — correct and fail-closed

`known_load_oom(raw, cfg, out, spec)` now requires all of: log file inside `out` (SHA stored);
`verdict=='STOP'`; `footprint_mib_to_pin is None`; top-level `gpu_uuid`/`binary_sha256`/`model_sha256`/
`build.version_line` equal to the accepted config/candidate pins; a recorded startup exit
(`server_stop.returncode` **or** a `dedicated llama-server exited during start (rc=N)` stop reason); the
cudaMalloc-OOM line anywhere in the log (timestamp prefix allowed; `re.search(... re.M)` without `^`); then
the post-stop healthy-idle census (`gpu_compute_apps()==[]` and `gpu_sample(cfg)['free_mib']>=1024`); anything
missing or the census unavailable/foreign → `healthy_idle_after_stop=False` → `PREPARATION_STOP`.

- **Verified on the actual retained STOP-6 log** (fetched from TASL-7,
  `.../nemotron35_30b_a3b/.../llama_server_58383.log`, SHA `9ec47056…`, 21187 B): with the exact retained
  probe fixture (SHA `1a941310…` = the retired qualification's `raw_probe_sha256`) and the healthy-idle
  census, the classifier returns the `cuda_allocation_out_of_memory` evidence with the matched
  `ggml_backend_cuda_buffer_type_alloc_buffer: … cudaMalloc failed: out of memory` line, the `(rc=1)` stop
  reason, and `healthy_idle_after_stop=True`; `qualification_exit_code` would be 0.
- **Fail-closed negatives** (verified directly on the real shape): mutated `binary_sha256`, mutated
  `model_sha256`, mutated `build.version_line`, empty `stop_reasons` (no recorded exit), a log without the
  OOM line, and a log outside the attempt dir all → `None` → `PREPARATION_STOP`. The parameter test's
  `foreign` GPU app and `no_census` (`gpu_compute_apps` None) also → `PREPARATION_STOP`.
- **Cannot be spoofed by a generic load failure:** the classifier requires the explicit cudaMalloc-OOM line,
  the accepted GPU/binary/build/model pins, the STOP/no-footprint state, the recorded startup exit, and the
  healthy idle. A generic startup failure (no OOM line) stays `PREPARATION_STOP`; the OOM evidence is the
  specific capacity failure. The template classifier is unchanged (STOP-4 fix intact); the OOM path is tried
  first, so a 32k OOM at allocation is classified before a later 16k template/other failure.
- The healthy-idle rule is the pre-existing one (no compute apps + ≥1 GiB free); it is not weakened. The
  16k fallback is reached only with `MECHANICAL_FAILURE`, which requires `healthy_idle_after_stop=True`.

## 3. No infrastructure relabel (question b)

The template classifier (`known_template_parse_failure`) is v10-identical and its STOP-4 tests still pass.
The OOM classifier cannot relabel a generic/other infrastructure failure: it needs the exact OOM line, the
pinned identity, the recorded exit, and the healthy idle; an OOM with a non-healthy post-state (foreign GPU
app, nvidia-smi unavailable, census exception) stays `PREPARATION_STOP`. The only path to the 16k fallback is
the evidenced, healthy-idle 32k OOM.

## 4. Runner evidence re-check (question c)

`exam_runner.run_fresh_qualification` for `MECHANICAL_FAILURE` already re-checked the kind and
`healthy_idle_after_stop`; it now additionally requires the evidence `server_log` to be a file inside the
qualification attempt dir with a matching `server_log_sha256`. The `raw_probe` binding check is unchanged.
The updated 32k→16k fallback test (`test_exam_qualify_guard.py`) supplies a retained OOM log + digest and
passes. The 16k-path semantics are otherwise unchanged.

## 5. Stop semantics (question d) — unchanged

The v12 `exam_runner.py` diff only adds the OOM evidence log re-check; `_stage_a_cooperative`, the
`MechanicalFailure` handling, the 16k fallback, the no-serve-after-failed-16k behaviour and the server
preservation rules are exactly the accepted v10/v11 code. The OOM path: 32k `MECHANICAL_FAILURE` → ctx 16384
qualification; PASS → the 16k run; FAIL → the candidate failure row, no serve. Auth/lease/offload/parse/
timeout/STOP semantics are unchanged.

## 6. Tests

v12 relevant Mac CPU subset: **388 passed, 1 skipped** — matches. The new tests are genuine: the
`test_real_oom_at_32k_is_evidenced_mechanical_failure` (retained probe + log; expects
`MECHANICAL_FAILURE`, evidence kind, `healthy_idle_after_stop=True`, `(rc=1)` exit evidence, log name, exit 0)
and `test_real_oom_negatives_remain_preparation_stop` (mutated binary/model/build, missing OOM line, missing
recorded exit → `PREPARATION_STOP`), plus the updated `test_load_failure_classification` (real shape) and the
32k→16k fallback test. The older template STOP-4 tests still pass.

## 7. Fixture provenance — one real defect to correct (condition)

- `stop6_nemotron_probe.json` `1a94131065462829ce8401ea29ff60f5caae77ef6c8b1ea6806feaf1ea19bf5c` is
  **byte-identical** to the retained probe (`raw_probe_sha256` matches).
- `stop6_nemotron_server.log` `1164f51ec5ea…` (21234 B, 227 lines) is **not** byte-identical to the retained
  `llama_server_58383.log` `9ec47056…` (21187 B, 225 lines; ~19k differing bytes). The OOM line is identical
  (`0.03.957.863 E ggml_backend_cuda_buffer_type_alloc_buffer: … cudaMalloc failed: out of memory`), and the
  retained log classifies correctly (verified in §2), so this is a fixture/claim defect, not a classifier
  defect — but the README/Lead description of it as the actual retained file is inaccurate. Condition:
  replace the fixture with the exact retained bytes (`9ec47056…`) or document the normalization (and record
  both hashes; keep the OOM-line identity assertion). Do not rely on the current log fixture as the actual
  retained evidence.

## 8. STOP-6 evidence and recovery (verified read-only)

- Attempt `r1_stagea_20261102_t7e5`: `batch_state` STOPPED with `stop_reason` `root worker exit 1`; 11 rows
  in `completed` (anchors + qwen25/qwen38/qwen36/gemma4/muse/olmo31_32b/devstral/qwen36_35b_a3b/
  gemma4_26b_a4b); the nemotron qualification interruption (`qualification.json` `PREPARATION_STOP` under the
  old v11 classifier, `allocation_failure_evidence:null`); the retained log has the 32k OOM
  (`allocating 102.00 MiB … cudaMalloc failed: out of memory` → `failed to allocate buffer for kv cache` →
  `exiting due to model loading error`); guardian `STOP.json` `lease_retained:true`, `retry_permitted:false`,
  guardian 2602930, utc 13:55:30Z. The 11 rows are not Stage A evidence and t7e5 is not reused.
- Recovery `r1_stop6_shutdown_20261102T164722Z/` at 16:47:22Z: `before` shows only guardian 2602930 (the
  server had exited at the OOM; the worker exited) with the FLOCK on inode 56251186; `after` LOCK-FREE, lock
  size 0/inode 56251186/nlink 1, GPU 243 MiB/0 %. Current: guardian 2602930 absent, `/proc/locks` free, GPU
  idle, 22/22 models verified (0 failed), code clone `5d66967`. STOP-6 lease/batch hashes unchanged
  (`2cd53720…`, `52ee7483…`, `652df9d4…`, `e00da02e…`, `60d3301c…`) and match the recovery `before`.

## 9. Conditions

1. Correct the STOP-6 log fixture provenance (§7): exact retained bytes or documented normalization, with
   both hashes; keep the OOM-line identity.
2. Commit the v12 delta; **rebind `paper_commit` to the v12 code commit** (`r1/exam/qualify.py`,
   `r1/scripts/exam_runner.py` are runtime-checked; the current `caa2f70` binding would fail the launcher's
   ancestor/no-diff); clean TASL-7 checkout; rebuild the guardian manifest (M1/M2/M3).
3. Fresh TASL-7 real-lock preflight; then the new `t7f6` attempt in new out/evidence dirs, 22/22 models,
   continuous guardian lock, periodic GPU/server/lease/**progress** checks (the 12 h-deadline risk note still
   applies), B1/B2 remain STOP; no STOP batch reused; the t7e5 rows not used.
4. The 16k fallback is allowed only for the evidenced, healthy-idle 32k OOM; if the post-stop census is
   unavailable/foreign, the batch STOPs as infrastructure (fail-closed). The template policy decision
   (a/b/c) is recorded in PLAN and remains the author's.

## 10. NOT CHECKABLE in this review

- The `t7f6` behaviour (not run), including whether the other 32k candidates hit OOM/template at load.
- The exact retained log fixture provenance (checked; the defect is reported) and the future
  commit/binding/manifest bytes.
- Host-global single-server / same-UID non-interference (carry over); B1/B2 on TASL-7 (STOP).

## 11. Final verdict

**`ACCEPT`** of the real-shape OOM classification (v12), with the §9 conditions. The classifier works on the
actual retained STOP-6 probe/log (verified directly), is fail-closed on mutated pins / missing OOM line /
missing exit / outside-dir / non-healthy census, cannot relabel a generic infrastructure failure, the runner
re-checks the OOM evidence, and the 16k fallback/stop/server-preservation semantics are unchanged. The
`stop6_nemotron_server.log` fixture is not byte-identical to the retained log (the probe is), which is a
test-fixture provenance defect to correct, not a classifier defect.
