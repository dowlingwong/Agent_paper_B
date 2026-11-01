# Track X Stage A — scoped review of the STOP-1 fix (route A: restore route (i))

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. Host access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`grep`/`/proc`/point-in-time
`nvidia-smi`); the local test runs and `git` reads are as before.

**Verdict: `ACCEPT` (scoped to the STOP-1 route-A fix), with the conditions in §6.** The delta is minimal and
correct: route (i) is restored by pinning `-lv 4` in the exact exam server argv, route precedence in
`offload_check` puts the log line first, partial lines and CPU-fallback lines still STOP, no tolerance or
memory-floor weakening was introduced, the qualification and preflight use the same argv, the fake-server
change is test-double-only, and the real pinned build's lv4 diagnostic log shows `offloaded 29/29` with no
fallback lines and no generation. The 8 `test_llamacpp_offload_routes.py` failures are pre-existing Mac
desktop failures (verified identically on base `1be426f`: 8 failed / 17 passed, same names).

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v4` |
| `SHA256SUMS` SHA-256 | `6354e8b28363f2a534c10fccbff397bcc00c66d97e645d7fb255745d1b71e5be` — **verified**; 53/53 entries OK (51 `files/` + `tracked.patch` + `README.md`) |
| Base | published C4 `9418d75ef6b78bb1fd2ec90b9c47d72b62acacb4`; config `paper_commit=82dfaf5` |
| Delta vs C4 | `tracked.patch` = 4 tracked files (`runtime.py`, `qualify.py`, `scripts/c3_fake_llama_server.py`, `tests/stagea_lease_preflight.py`, 5068 bytes) + 1 new untracked test (`tests/test_exam_offload_evidence.py`) |
| Everything else | v4 `files/` == live worktree (0 mismatches); the config (`dfe694a4…`) and launcher (`df988cc2…`) are the already-accepted C4 bytes; all other accepted v3/C4 files are unchanged. The live worktree is at `9418d75` with the v4 delta uncommitted (4 modified tracked + the new test untracked), as expected before the commit |

Delta hashes (SHA-256):
```
3dda01830b7a6604143c3793059fc5c28174518a2114bef9d3127a89399caffa  files/r1/exam/runtime.py
1a80f554f7a95c33cfd90c008559ba9d4c8f8a0e5bb3dd20b83d4d43b8555098  files/r1/exam/qualify.py
e99caae99c215dc16ecce5e1870dd6cee434d71b93319aedc9b0de399193e40f  files/r1/scripts/c3_fake_llama_server.py
a267844d80d18d90a3ebe052a2e1b3b217f204af458d22e46629bfffbfae3c80  files/r1/tests/stagea_lease_preflight.py
c06e010f21758b6ef9e28481374c6cb2e917d5d7a68030c08b7499ad5b3cfeef  files/r1/tests/test_exam_offload_evidence.py
```

## 2. (a) Route (i) is really taken; no floor relaxation; partial/CPU-fallback still stop

- `runtime.EXAM_SERVER_ARGS = ['--jinja','--cache-type-k','q8_0','--cache-type-v','q8_0','-lv','4']`;
  `ExamRunner._server` uses `list(EXAM_SERVER_ARGS)`; `qualify.qualify` passes
  `--server-extra-args json.dumps(list(EXAM_SERVER_ARGS))`; the lease preflight uses
  `list(EXAM_SERVER_ARGS)`. The server argv therefore carries `-lv 4` on the exam, qualification and
  preflight paths.
- `offload_check` (`r1/scripts/llama_server_instance.py`) order: **CPU-fallback line → `full=False`** first;
  then `line == 'full'` → `full=True, route='log_line'`; then `line == 'partial'` → `full=False`; only when
  the line is absent does it use route (ii) (`used_mib >= footprint_mib`). So route (i) is taken whenever the
  log carries `offloaded N/N layers to GPU` with N>0 and N==N, and the memory floor is **not** consulted on
  that path. The floor code is unchanged; no tolerance was added.
- Partial (`offloaded 28/29`) is recorded as `partial` → `full=False`, route None. A CPU-fallback line forces
  `full=False` even when the log also has an `offloaded N/N` line. Both are pinned by
  `test_exam_offload_evidence.py::test_partial_route_one_line_still_stops` and the existing offload-route
  tests.
- The 2 MiB below-floor case is now covered by
  `test_real_lv4_log_passes_route_one_even_below_the_old_memory_floor`: a real-shaped lv4 log with
  `offloaded 29/29` + CUDA0 buffers and `apps` reporting 5782 vs a 5784 footprint yields
  `full=True, route='log_line'`. This is exactly the STOP-1 scenario.

## 3. (b) `-lv 4` cannot suppress the evidence the check relies on; cache/cold/prompt bytes untouched

- Verbosity 4 is **higher** than the default, so it adds lines and cannot remove the warning/error lines the
  check relies on. The `CPU_FALLBACK_RE` patterns (`no usable GPU found`, `--gpu-layers option will be
  ignored`, `ggml_cuda_init: failed`, `no CUDA-capable device`, `CUDA driver version is insufficient`) are
  already logged at default verbosity when they occur; lv4 does not hide them. The diagnostic lv4 log
  contains none of them (grep empty), while containing the offload line.
- The `OFFLOAD_RE` (`offloaded (\d+)/(\d+) layers to GPU`) still matches the lv4 line
  (`load_tensors: offloaded 29/29 layers to GPU`); the buffer lines (`CUDA0 model buffer size = 4168.09 MiB`,
  `CUDA0 KV buffer size = 952.00 MiB`) also parse (`GPU_BUFFER_RE`/`KV_BUFFER_RE`). No line-format change
  breaks the parser.
- `-lv 4` is a server CLI flag only. The v4 delta does not touch request payloads, the frozen prompts, the
  cold-true-first/`cache_prompt:false` recorder, seeds, schema mode or the qualification/PASS semantics.
  The same model, ctx 32768, q8_0 KV, `-ngl 999` full-offload requirement and cold/cache gate apply; only the
  offload *evidence route* changes (route (i) log line instead of route (ii) floor).

## 4. (c) Qualification path uses the same args and its own route-(i) evidence

- `qualify.qualify` now passes `EXAM_SERVER_ARGS` to `llamacpp_probe`; the probe's `LlamaServerInstance`
  receives `-lv 4`; the probe's `offload_check` sees the route-(i) line and sets `route='log_line'`; the
  `--exam-stage-a` branch requires `offload['full']` and the served alias, sets `result['route']`, and
  `verdict='FULL_GPU_OFFLOAD'` only with a route. `qualification.json` therefore records `offload_route`; the
  pinned `footprint_mib` continues to come from the measured used-MiB (`footprint_mib_to_pin`).
- `test_exam_offload_evidence.py::test_qualification_passes_the_same_pinned_args_to_the_probe` captures the
  probe argv and asserts `--server-extra-args` equals `EXAM_SERVER_ARGS` (and the qualification returns PASS).
- **Precision note (non-blocking):** the code does not *hard-require* the qualification's route to be
  `log_line`; it accepts route (ii) if the line is ever absent (the same conservative fallback as before).
  With `-lv 4` the line is present, so route (i) is used. The Lead's phrase "its own route-(i) evidence is
  required before pinning" is therefore slightly stronger than the code; if route (i) is to be mandatory,
  add an explicit `offload_route == 'log_line'` STOP in the qualification path (optional hardening, §6.6).

## 5. (d) Fake-server change is test-double-only; (e) diagnostic and failures

- `r1/scripts/c3_fake_llama_server.py` is referenced only by the dry-run/test double (the
  `llama_server_instance` docstring) and by tests; it is not imported by the production exam path. The change
  adds acceptance of the real binary's verbosity flags (`-lv`/`--verbosity`/`--log-verbosity` with a value;
  `-v`/`--verbose`/`--log-verbose` as booleans) and ignores them. It is test scaffolding so the fake accepts
  the real `EXAM_SERVER_ARGS` instead of `SystemExit`ing; it changes no production behaviour and no fake log
  content.
- **Diagnostic (TASL-2, read-only, 2026-11-01T00:37Z)**: `r1_stagea_diag_offload_20261101_lv/` contains
  `server_lv4.log` (207 lines; line 140 `load_tensors: offloaded 29/29 layers to GPU`, line 142
  `CUDA0 model buffer size = 4168.09 MiB`, line 166 `CUDA0 KV buffer size = 952.00 MiB`), `server_lv5.log`
  (5218 lines, same route-(i) line), `summary_lv4.json`, `summary_lv5.json`, `diagnostic.json`
  (`has_offloaded_ratio: true`, gpu row 5782 MiB for the diagnostic server pid). The lv4 log has **no**
  CPU-fallback-pattern line and **no** chat/completion/generation request line (only load/prompt-cache
  configuration lines). It is load-only diagnostic evidence, **not** a Stage A run (no `stage_a.json`,
  `d3_true_calls.jsonl`, `d3_false_calls.jsonl` or Stage A table in that directory).
- **Site recovered / lock free (read-only)**: the old preserved guardian 2576846 and native server 2611135 are
  gone (`/proc/<pid>` absent); `/proc/locks` has no line for the lock inode 120090387; `gpu0.lock` is
  dev 66306 / inode 120090387 / nlink 1 / size 0 (unchanged); GPU point-in-time `438 MiB used, 23745 MiB
  free, 0 %` (idle). The STOP-1 evidence is unchanged from the receiving review
  (`STOP.json 2d38fece…`, `batch_state.json aa2e953b…`), so the recovered site did not alter the STOP batch.
- **Pre-existing failures**: `r1/tests/test_llamacpp_offload_routes.py` on v4 = **8 failed, 17 passed**; the
  same file on a throwaway base `1be426f` extraction = **8 failed, 17 passed**, with the **identical 8 test
  names**. The test file is byte-identical between base and v4. So they are pre-existing Mac-desktop
  environment failures (no `nvidia-smi`/fake GPU), not regressions. The relevant subset on v4 (including the
  new test) is **370 passed, 1 skipped** — matching the claim.

## 6. Conditions

1. **Commit the delta** (runtime/qualify/c3_fake/preflight/new test) as the new code commit; verify the
   committed tree matches the accepted v4 `files/` (the five delta hashes above; the config/launcher stay the
   C4 bytes; all other accepted files unchanged). The live worktree currently has the delta uncommitted at
   `9418d75`.
2. **Rebind `paper_commit`** to the new code commit in a separate config-binding commit; verify the only
   config change is `paper_commit`, the launcher's ancestor + no-diff over the runtime-checked paths is empty
   between the new code commit and the final HEAD, the run checkout is clean at the final commit, and the
   manifest pins the accepted code/config/launcher/tests. Conditions M1/M2 carry over.
3. **Fresh real-lock preflight** with the new argv (`-lv 4`) in a new evidence directory: verify the preflight
   server log contains the route-(i) line with no CPU-fallback line, the FD/OFD chain (guardian→runner,
   runner→server kcmp rc 0, FD dev/ino/exact set, ppid/start ticks), zero generation, and the
   validated-completion release; verify the manifest pins the new accepted bytes; M3 (interpreter/venv/deps)
   carries over.
4. **New, separately identified Stage A attempt** (new output/evidence; the STOP-1 batch is not resumed,
   reused or relabelled; the diagnostic is not Stage A evidence): verify the attempt's server record log and
   `exam_offload.json` show `route: 'log_line'`, `full: true`, `offloaded 29/29`, no `cpu_fallback_lines`; and
   the qualification/`qualification.json` records its route. If route (ii) is used because the line is
   absent, the attempt must STOP (the 5782/5784 floor issue would recur) — route (i) is the point of the fix.
5. **Record the authorization**: the code comment cites `R1-EXAM-OFFLOAD-ROUTE`; record the author's route A
   first / B fallback decision and the PLAN/authorization row in the coordinator docs before the new attempt.
6. **Non-blocking hardening**: if route (i) is to be mandatory for the qualification (not just produced),
   add an explicit `offload_route == 'log_line'` requirement; keep the lv4 server log with the new attempt's
   evidence (the server record already points to its log).

## 7. NOT CHECKABLE in this scoped review

- The real preflight/Stage A route-(i) evidence and the new attempt's behaviour (not yet run).
- The diagnostic's historical diagnostic-lease acquisition (the logs do not record the lock; the lock is free
  now and the old pids are gone); the diagnostic is load-only and not Stage A.
- The future commit/binding hashes and the final run manifest (not yet committed/run; M1).
- Same-UID non-interference and host-global single-server (author assumption / NOT_CHECKABLE; carry over).
- Real Stage A request/response/cache evidence (not yet produced; the cold/cache gate is unchanged by this
  delta).

## 8. Final verdict

**`ACCEPT`** of the frozen v4 STOP-1 route-A fix, with the §6 conditions. Route (i) is genuinely restored by
the pinned `-lv 4` argv and takes precedence in `offload_check`; no floor/tolerance was relaxed; partial and
CPU-fallback evidence still STOP; the qualification and preflight use the same argv; the fake-server change is
test-double-only; the real pinned build's lv4 diagnostic log proves the route-(i) line appears with no fallback
and no generation; the lock is free and the STOP-1 site is untouched. The fix does not reopen the v3/C4
acceptance; it addresses only the footprint-floor STOP evidence route.
