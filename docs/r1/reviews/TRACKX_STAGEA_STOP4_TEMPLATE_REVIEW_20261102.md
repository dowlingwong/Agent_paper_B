# Track X Stage A — scoped review of the STOP-4 template-failure fix (v9)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-02 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`); local test runs as before.

**Verdict: `BLOCK`.** The candidate-level classification design is sound and fail-closed in principle, and the
row/continue mapping and tests are correct — **but the implemented evidence preconditions do not match the real
STOP-4 probe JSON**, so the fix would still classify the observed `olmo31_32b` template failure as
`PREPARATION_STOP` and the new attempt `t7d4` would STOP again at the same point. I reproduced this with the
real-shaped probe fields: `known_template_parse_failure()` returns `None` because the retained probe has
`server_stop: None` and `pins_match: None` (the build/model pins are top-level; the server record's
`returncode` is also `None`; the probe's `stop_reasons` carries the rc=1 exit). The new tests use a synthetic
probe shape (`server_stop`/`pins_match` set) that does not occur in the STOP-4 evidence.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v9` |
| `SHA256SUMS` SHA-256 | `a2db130d77afad4b6475a5ddb1a0f07d01e4fcc21c566af73678c918b77b4555` — **verified**; 53/53 entries OK |
| Base | published deadline fix `7a386f8` (`paper_commit` still `d6841e6`) |
| Delta vs v8 | `r1/exam/qualify.py`, `r1/scripts/exam_runner.py`, `r1/tests/test_exam_qualify.py`, `r1/tests/test_exam_qualify_guard.py` |
| Files | v9 `files/` == live worktree (0 mismatches); live HEAD `7a386f8` with the delta uncommitted |

Delta hashes: `qualify.py d6564842…`, `exam_runner.py e4422a2a…`, `test_exam_qualify.py 64ff7d89…`,
`test_exam_qualify_guard.py 9a22a202…`.

## 2. BLOCKING: the fix does not match the retained STOP-4 evidence

The retained STOP-4 probe `/home/dowling/exam-x/work/r1_stagea_20261101_t7c3/olmo31_32b/stage-a/32768/qualification/probe_20261102T035958Z.json` (real, from the same `llamacpp_probe.py` that v9 would use) contains:

```
verdict = STOP
gpu_uuid = GPU-ab72fb4a-… (matches cfg)
server_log = …/probe_…/llama_server_41919.log   (inside the qualification attempt dir)
server_stop = None          <-- required by known_template_parse_failure
pins_match = None           <-- required by known_template_parse_failure
stop_reasons = ['RuntimeError: STOP: dedicated llama-server exited during start (rc=1)']
build = {… version: 0.7.0-dev …}   (top-level)
model_sha256 = 437635de…            (top-level)
binary_sha256 = b70f4882…
```

The server record `llama_server_41919.json` has `pid`, `start_ticks`, `build`, `model_path`, but
`returncode: None`, `stopped_utc: None`, `pins: None`; `runner.log` ends
`STOP: RuntimeError: STOP: dedicated llama-server exited during start (rc=1)`; the server log has the exact
`init: chat template parsing error: Unable to generate parser for this template` →
`Unknown (built-in) filter 'tojson' for type Undefined (hint: 'tools')` →
`llama_server: exiting due to model loading error` lines.

`v9/qualify.py:known_template_parse_failure()` requires
`pins_match['build'] is True` and `pins_match['model_sha256'] is True` and
`raw['server_stop'].returncode is not None`. With the real probe both `pins_match` and `server_stop` are
`None`:

- `pins = raw.get('pins_match') or {}` → `{}` → `any(pins.get(k) is not True for k in ('build','model_sha256'))` is True → **returns None**.
- Even if the pins were present, `not raw.get('server_stop')` → True → **returns None**.

I ran the v9 function on a real-shaped raw (server_stop None, pins_match None, top-level build/model pins,
stop_reasons rc=1, log with the real lines inside `out`): **`None`**. The same raw with the synthetic
`server_stop={'returncode':1}` and `pins_match={'build':True,'model_sha256':True}` returns the
`chat_template_parse_error` evidence. So `qualify.qualify` keeps `status = PREPARATION_STOP`,
`qualification_exit_code` returns 1, the runner sees a nonzero worker exit and STOPs — exactly the STOP-4
behaviour. **The t7d4 attempt with v9 as frozen would stop again at `olmo31_32b` and never reach the row /
continue path.**

This is a real defect, not a wording issue: the probe's "exited during start" path never populates
`server_stop`/`pins_match` (the probe code is not in the v9 delta, so t7d4 would produce the same shape), and
the retained STOP-4 evidence is the ground truth the fix must classify.

Required correction (before any ACCEPT):

1. Derive the server-exit evidence from what the probe actually retains on this path — the
   `dedicated llama-server exited during start (rc=1)` `stop_reasons` entry and the log's
   `exiting due to model loading error` — instead of `raw['server_stop']` (or make the probe populate the
   field on the start-failure path, with a test).
2. Derive the build/model pins from the probe's top-level `build`/`model_sha256` (and/or the server record)
   and compare them to the accepted `cfg['server']['build']`/binary SHA and the candidate's
   `quant_source.sha256`; do not rely on the unset `pins_match`.
3. Add a test that uses the **real retained STOP-4 probe shape** (a fixture copied from
   `probe_20261102T035958Z.json` + the real log lines, with `server_stop=None`, `pins_match=None`,
   top-level build/model, `stop_reasons` rc=1) and asserts `TEMPLATE_FAILURE` + exit 0; keep the negative
   tests (outside-dir / missing line / genuine unpinned build → `PREPARATION_STOP`).
4. Re-run the stop-4 classification on the real fixture and re-review; only then is the row/continue path
   reachable in the real t7d4 run.

## 3. What is sound if the preconditions are fixed

- The **candidate-level classification** is the right runbook class: a pinned-build chat-template parser
  incompatibility is a property of the candidate under the pinned build, not an offload/GPU/lease
  infrastructure failure. The evidence design (retained log inside the attempt dir + log SHA + explicit
  `chat template parsing error` + `exiting due to model loading error` + build/model pins + recorded server
  exit) is fail-closed: an infrastructure error cannot produce those lines and the recorded-exit checks;
  anything missing stays `PREPARATION_STOP`. The fail-closed direction is correct; the matching to the real
  evidence is what fails.
- **Row/continue semantics (question b) are sound in isolation:** `_stage_a_cooperative` writes a
  `passed:false, failure_classes:['template']` row with retained evidence and `prefill_not_attempted_reason`,
  breaks the ctx loop (no 16k fallback), never calls `runner.server` for that candidate, and continues to the
  next candidate; the `test_template_failure_candidate_row_continues_to_next_candidate` test proves the row
  and `served == ['tmpl_good']` (the failed candidate never started a server). The batch table/state semantics
  are preserved; the candidate's failure is a row, not a STOP. But in the real STOP-4 shape this branch is
  never reached because the worker returns `PREPARATION_STOP`.
- **No other semantics changed:** auth/lease/offload/parse/timeout/STOP handling, the 16k fallback for
  genuine offload failures, and the B1/B2 hard STOPs are unchanged; `paper_commit` must, however, be rebound
  to the v9 code commit because `r1/exam/qualify.py` and `r1/scripts/exam_runner.py` are runtime-checked
  paths (the launcher's ancestor+no-diff would otherwise fail) — see §6.

## 4. STOP-4 evidence and recovery (verified read-only)

- `batch_state.json` (attempt `r1_stagea_20261101_t7c3`): `status: STOPPED`,
  `stop_reason: "RuntimeError: STOP: root worker exit 1; …"`, seven completed entries (anchors +
  qwen25/qwen38/qwen36/gemma4/muse), interruption `olmo31_32b/stage-a/32768/qualification` rc=1; guardian
  `STOP.json` `lease_retained:true`, `retry_permitted:false`, guardian 2306409, utc 04:00:25Z.
- `muse_glimmer_30b` row: `passed:false`, `failure_classes:['grammar','template']`, `prompts:50` — the
  recorded candidate failures are plausible (its template also carries `tojson` risk tokens; the pin build
  rendered it, so its row is candidate-level, not a STOP).
- `olmo31_32b` qualification: `PREPARATION_STOP`, `footprint_mib:null`, `offload_route:null`,
  `stop_reasons:['RuntimeError: STOP: dedicated llama-server exited during start (rc=1)']`; no
  `stage_a_table.json` (the STOP ended the attempt; the seven rows are in `batch_state.completed`, not Stage A
  evidence).
- Recovery `r1_stop4_shutdown_20261102T062008Z/`: `before.txt` shows only the guardian 2306409 (the server
  exited at load; the worker exited) with the lock `FLOCK` by 2306409 on inode 56251186; the recovery ended
  the guardian; `after.txt` shows LOCK-FREE, lock size 0/inode 56251186/nlink 1, GPU 243 MiB/0 %. Current:
  guardian absent, `/proc/locks` free, lock metadata unchanged, 22/22 models verified (0 failed), GPU idle;
  the STOP-4 lease/batch files are unchanged (`lease_inheritance 6c4297fb…`, `runner 9cbbb5b6…`,
  `start 129c6caa…`, `STOP f457418d…`, `batch_state 93d7c687…`, matching the recovery `before` hashes). The
  STOP-4 batch is not resumed/reused and is not Stage A evidence.
- Template scan `r1_template_scan_20261102/summary.json`: per-model embedded-GGUF vs pinned-HF template SHA and
  risk tokens; `olmo31_32b` `hash_match:true` with `tojson`/`tools |`; many others carry `tojson` risk tokens
  (qwen36/qwen38/muse/devstral/nemotron/glm47/…); `devstral` hash differs. Hash inequality is a risk
  indicator only (as the Lead notes; qwen25's hash differs yet its render checks passed) — the fix correctly
  classifies from the retained server log, not the hash, once the real-shape preconditions are fixed.

## 5. Question (c): other candidates with similar templates

Recording a `template` row (excluded candidate) is runbook-consistent and preserves batch semantics. Whether
to accept the resulting reduced candidate coverage, repair the templates, or pin a newer llama.cpp build is an
**author decision**, not something this fix can resolve: the scan shows several candidates with `tojson`/`tools`
risk tokens, and the pinned build's parser is the limitation. A template repair or a new build pin would be a
separate reviewed change; the current attempt should record the rows and continue (after the §2 correction),
with the author deciding coverage separately.

## 6. Conditions (after the §2 fix is corrected, re-reviewed and ACCEPTed)

1. Fix `known_template_parse_failure` to use the real retained probe shape (top-level build/model pins +
   `stop_reasons` rc=1 / log exit) and add the real-shape test; re-review.
2. Commit the corrected delta; **rebind `paper_commit` to the v9 code commit** (runtime-checked paths changed:
   `r1/exam/qualify.py`, `r1/scripts/exam_runner.py`); clean TASL-7 checkout; rebuild the manifest (M1/M2/M3).
3. Fresh TASL-7 real-lock preflight under the corrected config/manifest, then the new `t7d4` attempt in new
   out/evidence dirs; 22/22 models verified; periodic GPU/server/lease/progress checks; B1/B2 remain STOP;
   the STOP-4 evidence stays untouched and is not reused.
4. If the olmo/other candidates hit the same template class, the new attempt records the rows and continues;
   the coverage decision (repair/new build pin) remains the author's.

## 7. NOT CHECKABLE in this review

- The `t7d4` behaviour after a corrected fix (not run); the real-shape test cannot exist until the fix is
  corrected.
- Whether the other candidates with `tojson`-risk templates would fail the pinned build (the scan is a risk
  indicator; only the retained logs of actual loads classify them).
- The future commit/binding/manifest; host-global/same-UID assumptions; B1/B2 on TASL-7 (STOP).

## 8. Final verdict

**`BLOCK`.** The design is right and the row/continue/tests are sound, but the frozen v9 does not classify
the actual STOP-4 evidence: the retained probe has `server_stop: None` and `pins_match: None`, which the new
`known_template_parse_failure` requires, so the real `olmo31_32b` template failure remains
`PREPARATION_STOP` and the t7d4 attempt would STOP again. Required: match the real retained probe shape
(top-level build/model pins + the `stop_reasons` start-exit + the log lines), add a real-shape test, re-review,
then commit/rebind and run the preflight and t7d4 under the §6 conditions.
