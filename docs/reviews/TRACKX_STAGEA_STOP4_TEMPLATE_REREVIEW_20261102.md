# Track X Stage A — re-review of the corrected STOP-4 template-failure fix (v10)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-02 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `ACCEPT` (with conditions)** of the corrected v10 STOP-4 classifier. The v9 BLOCK is addressed:
the classifier now uses the **real STOP-4 probe shape** (no `pins_match`; `server_stop: null`; top-level
`gpu_uuid`/`binary_sha256`/`model_sha256`/`build.version_line`; a `dedicated llama-server exited during
start (rc=1)` stop reason), the fixtures are the actual retained probe/log (byte-identical, hashes below),
the real-shape classification produces `TEMPLATE_FAILURE`, the fail-closed negatives stay
`PREPARATION_STOP`, the row/continue mapping is unchanged and proven, and the recovery/STOP-4 evidence is
unchanged.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v10` |
| `SHA256SUMS` SHA-256 | `4f387beb32e08427fc76bef6181dfaf063e8bd6c34114ad9e06ed5cd4e50b400` — **verified**; 55/55 entries OK (53 files + `tracked.patch` + `README.md`) |
| Base | published deadline fix `7a386f8` (`paper_commit` still `d6841e6`) |
| Delta vs v9 | corrected `r1/exam/qualify.py`, `r1/tests/test_exam_qualify.py`, plus fixtures `r1/tests/fixtures/stop4_olmo_probe.json`, `r1/tests/fixtures/stop4_olmo_server.log`; `exam_runner.py` and `test_exam_qualify_guard.py` are v9-identical |
| Files | v10 `files/` == live worktree (0 mismatches); live HEAD `7a386f8` with the delta uncommitted |

Delta hashes: `qualify.py 9fdc3adb…`, `test_exam_qualify.py 7bd9c297…`, `exam_runner.py e4422a2a…` (v9),
`test_exam_qualify_guard.py 9a22a202…` (v9), `stop4_olmo_probe.json ac83fde3…`,
`stop4_olmo_server.log 6daa4cc1…`.

## 2. Fixtures are the actual retained STOP-4 files (byte-identical)

- `stop4_olmo_probe.json` SHA-256 `ac83fde374af10a387589ad766b5b47d47a20e4fa64f7a08ad41ccee16863470`
  equals the retired qualification's recorded `raw_probe_sha256` and the retained
  `probe_20261102T035958Z.json` hash on TASL-7.
- `stop4_olmo_server.log` SHA-256 `6daa4cc16bcaf89e80b1950151aed1659cb03b82c6ba44fa6df42e92b370d50d`
  equals the retained `probe_20261102T035958Z/llama_server_41919.log` hash on TASL-7.
- The fixture probe has the real shape: `verdict STOP`, `footprint_mib_to_pin None`, `server_stop None`,
  no `pins_match`, top-level `gpu_uuid` `GPU-ab72fb4a-…`, `binary_sha256 b70f4882…`,
  `model_sha256 437635de…`, `build.version_line version: 0.7.0-dev (build 1, commit 620d222)`,
  `stop_reasons ["RuntimeError: STOP: dedicated llama-server exited during start (rc=1)"]`; the log has the
  `chat template parsing error` line and `exiting due to model loading error`.

## 3. Corrected classifier — real-shape classification works and is fail-closed

`qualify.known_template_parse_failure(raw, cfg, out, spec)` now requires **all** of:
retained log file inside `out` (SHA stored); `verdict=='STOP'`; `footprint_mib_to_pin is None`;
`gpu_uuid == cfg['gpu_uuid']`; `binary_sha256 == cfg['server']['binary_sha256']`;
`model_sha256 == spec['quant_source']['sha256']`; `build.version_line == cfg['server']['build']`;
a recorded startup exit (`server_stop.returncode` **or** a `dedicated llama-server exited during start
(rc=N)` stop reason); the log contains `chat template parsing error` **and** `exiting due to model loading
error`. Then it returns evidence (`kind chat_template_parse_error`, log path+SHA, matched line,
`exit_evidence`, `pins`, `failure_class template`, `retry_at_16k false`); otherwise `None`
→ `PREPARATION_STOP` and a nonzero worker exit.

Verified directly on the real fixture (log copied into the attempt dir, `server_log` repointed):
- **Evidence produced** (the STOP-4 shape classifies): `kind chat_template_parse_error`,
  `exit_evidence.stop_reason` ends `(rc=1)`, `pins.build` matches; `qualification_exit_code == 0`.
- **Fail-closed** (all → `None` / `PREPARATION_STOP`): mutated `binary_sha256`, mutated `model_sha256`,
  mutated `build.version_line`, empty `stop_reasons` (no recorded exit), log missing the template line, log
  missing the model-loading line, log outside the attempt dir. The v10 parameterised test covers the same
  negatives plus the outside-dir test; the real-shape positive test asserts `TEMPLATE_FAILURE`, evidence
  kind/failure class/`retry_at_16k false`, the repointed log, the `(rc=1)` exit evidence, and exit code 0.

**No infrastructure relabel (question a):** an OOM is handled first by the unchanged `known_load_oom`; a
generic infra STOP lacks the explicit `chat template parsing error` + `exiting due to model loading error`
pair, and the classifier additionally requires the accepted GPU/binary/build/model pins, the STOP verdict, no
footprint, and a recorded startup exit. A log that contained the template-parser failure lines *is* the
pinned-build template parser failure; the classifier is fail-closed for everything else.

## 4. Row/continue semantics (question b) — unchanged v9 evidence, proven

`exam_runner.py` and the mapping test are v9-identical (hashes above); `_stage_a_cooperative` writes the
`passed:false, failure_classes:['template']` row with retained evidence and `prefill_not_attempted_reason`,
breaks the ctx loop (no 16k fallback), never calls `runner.server` for that candidate, and continues to the
next candidate; the mapping test asserts the row and `served == ['tmpl_good']` (failed candidate never starts
a server), and it passes in the v10 subset. The worker exits 0 only for the evidenced TEMPLATE_FAILURE;
infrastructure PREPARATION_STOP still exits nonzero; `run_fresh_qualification` still re-validates the kind,
in-attempt log path and digest. No auth/lease/offload/parse/timeout/STOP semantics changed.

## 5. Tests

v10 relevant Mac CPU subset: **384 passed, 1 skipped** — matches. The new real-shape positive + the
parameterised negatives + the outside-dir test + the unchanged mapping test all pass; the fixtures are the
retained files (not synthetic).

## 6. STOP-4 evidence and recovery — unchanged (re-verified)

- `batch_state`/`STOP.json`/`lease_inheritance`/`runner`/`start` hashes unchanged
  (`93d7c687…`, `f457418d…`, `6c4297fb…`, `9cbbb5b6…`, `129c6caa…`) and match the recovery `before` record;
  no `stage_a_table.json` (the STOP ended the attempt; the seven rows are in `batch_state.completed`, not
  Stage A evidence); the muse row remains `failure_classes:['grammar','template']`.
- Recovery `r1_stop4_shutdown_20261102T062008Z/` (06:20Z) is unchanged: only guardian 2306409 was ended
  (server/worker already gone); `after.txt` LOCK-FREE, lock size 0/inode 56251186/nlink 1, GPU 243 MiB/0 %.
  Current: guardian absent, `/proc/locks` free, lock metadata unchanged, GPU idle, 22/22 models verified
  (0 failed); code clone at `7a386f8`.
- The STOP-4 batch is not resumed/reused and is not Stage A evidence. (Other candidates with `tojson`-risk
  templates — the scan flagged several — would now become `template` rows; the coverage/repair/new-build-pin
  decision remains the author's, question c.)

## 7. Conditions

1. Commit the v10 delta; **rebind `paper_commit` to the v10 code commit** (`r1/exam/qualify.py` and
   `r1/scripts/exam_runner.py` are runtime-checked paths; the current `d6841e6` binding would fail the
   launcher's ancestor+no-diff), clean TASL-7 checkout, rebuild the guardian manifest (M1/M2/M3; the manifest
   pins the launcher/config/prompts/registry/code; the test fixtures are not runtime inputs).
2. Fresh TASL-7 real-lock preflight under the v10 config/manifest; then the new `t7d4` attempt in new
   out/evidence dirs, with the reviewed guardian holding the lock continuously, 22/22 models verified,
   periodic GPU/server/lease/**progress** checks (the STOP-3 12 h-deadline risk note still applies),
   B1/B2 remain STOP.
3. On any template-class hit in `t7d4`, record the row and continue (never start that candidate's server, no
   16k fallback); do not reuse any STOP batch; the STOP-4 evidence stays untouched; the other template-risk
   candidates' coverage / template repair / new build pin remains a separate author decision.
4. On any STOP, preserve the site and recover only under the author's standing authorization (the STOP-4
   recovery precedent); orphan writes are not evidence.

## 8. NOT CHECKABLE in this review

- The `t7d4` behaviour (not run), including whether other candidates hit the same template class at runtime.
- The future commit/binding/manifest bytes; host-global/same-UID assumptions; B1/B2 on TASL-7 (STOP).
- The pinned build's parser behaviour for the other candidates (the scan is a risk indicator; only the
  retained logs of actual loads classify them).

## 9. Final verdict

**`ACCEPT`** of the corrected v10 STOP-4 template-failure fix, with the §7 conditions. The classifier now
matches the real retained STOP-4 probe shape (verified: real fixture → `TEMPLATE_FAILURE` + exit 0;
mutated pins/missing lines/no recorded exit/outside-dir → `PREPARATION_STOP`), the fixtures are byte-identical
to the retained probe/log, the row/continue semantics are unchanged and proven, and the recovery/STOP-4
evidence is unchanged. The v9 BLOCK is resolved.
