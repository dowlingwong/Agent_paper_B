# Track X Stage A — scoped review of the STOP-2 fix (/proc executable-census gaps)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. Host access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`grep`/`/proc`/
point-in-time `nvidia-smi`); tests and `git` reads as before.

**Verdict: `ACCEPT` (scoped to the STOP-2 census-gap fix), with the conditions in §7.** The delta is minimal
and correct: only plausible `/proc` race errnos become recorded observation gaps, any other errno still STOPs
with its code, the exactly-one-owned-server count/identity check and `observed` identity are unchanged,
`host_global_single_server` stays `NOT_CHECKABLE`, the new gap fields are recorded and digest-covered and are
required by `validate_census_snapshot`, and no cache/cold/lease/offload semantics changed. The STOP-2 evidence
is accurately preserved (guardian + native server retain the same lock FD/OFD; the attempt is not Stage A
evidence). One precision/residual item (the exact STOP-2 errno is not in the old evidence; the fix covers the
plausible race set and the next run will record the actual errno) and one optional hardening are noted.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v5` |
| `SHA256SUMS` SHA-256 | `6a1607ec1f629c8f69e7b7ce180101af9585cbb77cf279601972fec2d97f93fe` — **verified**; 53/53 entries OK (51 `files/` + `tracked.patch` + `README.md`) |
| Base | published route-(i) fix `5bf7065` + config binding `9bfabe5` (branch `codex/trackx-stagea-cooperative-20261031`) |
| STOP-2 delta vs v4 | `r1/exam/cache_proc.py`, `r1/tests/test_exam_cache_proc.py`, `r1/tests/exam_census_fixture.py`, `r1/tests/test_exam_cache_order.py`; the config difference vs v4 is only the already-published `paper_commit: 82dfaf5 → 5bf7065` binding |
| Everything else | v5 `files/` == live worktree (0 mismatches); live HEAD `9bfabe5` with the STOP-2 delta uncommitted (4 modified tracked); the route-A files are byte-identical to the accepted v4 hashes |

Delta hashes (SHA-256):
```
df0cce0957d3b0f52aa2993a7b221b8613225dcb94fa07985ee5dc9b73b8ba05  files/r1/exam/cache_proc.py
8c3be26fea763d632ae8ce5424339d8bd5a7c949afdd913b68b77a521c79158c  files/r1/tests/test_exam_cache_proc.py
05d74a1ca5f03f209dd92f2d46d91b98237fece97ebf942b0bb87b216724bebb  files/r1/tests/exam_census_fixture.py
7379fc6a7309190e2b716e673f7358c98c181348fa676589f5a1d43d3488dfc6  files/r1/tests/test_exam_cache_order.py
f540f1f8a65cd329118dd7d42f87b5c81fdfa70632073ecb7967ccda8fcfb7e4  files/r1/scripts/configs/exam_portal.json  (paper_commit=5bf7065)
```

## 2. The STOP-2 failure (verified from the preserved evidence)

Attempt `r1_stagea_20261101_b3d7f2` (guardian 2920661, runner 2920668, manifest `35d21383…a14d3`): anchors
and `qwen25_coder_7b` completed with route-(i) evidence (`servers/qwen25_coder_7b/exam_offload.json`:
`full: true`, `line: "full"`, `route: "log_line"`, `offloaded 29/29`, no fallback; qualification
`offload_route: "log_line"`), then `qwen38_27b` loaded with route-(i) evidence
(`offloaded 66/66`, CUDA0 model 15713.95 MiB, KV 1088.00 MiB, `route: "log_line"`, no fallback) and stopped
during its descriptive replay:

- `qwen38_27b/stage-a/32768/runner.log`: `r1/exam/cache_descriptive.py:108 true_replay` →
  `:58 sample_now` → `stage_a.py:306 census` → `cache_proc.py:81 sample_llama_server_processes` →
  `RuntimeError: STOP: unexpected executable census error for pid 3075253`.
- `d3_true_calls.jsonl`: 761 lines; final line event `stop`, sequence 152, error
  `"RuntimeError: STOP: unexpected executable census error for pid 3075253"`; `d3_false_calls.jsonl` and
  `d3_non_generation_calls.jsonl` are empty (the true replay stopped before the false/non-generation phases).
- `batch_state.json`: `status: STOPPED`, `stop_reason: "RuntimeError: STOP: root worker exit 1; …"`,
  `in_progress` = qwen38 dir, qwen38 server interval open. No `stage_a_table.json`, no
  `qwen38_27b/…/stage_a.json`; the only completed entries are the two software anchors and qwen25.
- Guardian `STOP.json`: `lease_retained: true`, `retry_permitted: false`, `completed_release: false`,
  reason `runner ended rc=1; descendants/completion not proven`.

So **the attempt is not Stage A evidence** (partial, STOPPED, no table, no completed second model), and the
route-(i) fix was working (both loaded models have `route: log_line`).

## 3. (a) Tolerated errnos cannot mask a foreign/second server or the owned one

- `sample_llama_server_processes` still builds `matched` only from pids whose `/proc/<pid>/exe` is readable and
  whose executable basename is `llama-server`; it then requires `len(matched) == 1`, `matched[0].pid ==
  identity.pid`, and `matched[0].process_start_ticks == current` — **unchanged**. A *readable* second or
  foreign `llama-server` still makes `matched` length 2 → STOP (existing
  `test_extra_server_and_pid_reuse`).
- A pid whose `exe` read fails with a tolerated errno is put in `unreadable` (gap), not in `matched`; it is
  **not** counted as absent. If the **owned** server's own `exe` read fails, `matched` no longer contains it
  → `len(matched) != 1` → STOP; the tolerance cannot make the census pass without the owned server.
- `observed` still must be exactly one entry equal to the identity (pid/start ticks/executable);
  `count == 1`; `host_global_single_server == "NOT_CHECKABLE"`; `unobserved_same_uid_calls` unchanged.
  The gaps are separately counted/disclosed: `unreadable_executable_links`,
  `unreadable_executable_errnos`, `unreadable_executable_samples`; `inaccessible_executable_links` and
  `missing_executable_links` remain. The census digest covers all of these fields (it hashes every key except
  `snapshot_sha256`), and `validate_census_snapshot` recomputes it.
- Consequence (intended by the author requirement): a foreign server whose `/proc/<pid>/exe` is unreadable is
  a **disclosed gap**, not a second-server detector; `host_global_single_server` remains `NOT_CHECKABLE` and
  the scope string still says inaccessible/other-namespace/between-sample gaps are unobserved. This is the
  correct cooperative-level semantics, not a masking of a *visible* server.
- Test: `test_transient_unreadable_link_is_a_recorded_gap_not_a_stop` (foreign pid 126, ESRCH → gap count 1,
  errnos ['ESRCH'], sample pid 126, `validate_census_snapshot` accepts, `NOT_CHECKABLE`); the visible
  extra-server STOP is covered by the unchanged `test_extra_server_and_pid_reuse`.

## 4. (b) Only plausible `/proc` race errnos are tolerated; EIO-like errors still STOP with the code

- `CENSUS_GAP_ERRNOS = {ESRCH, ENOENT, EACCES, EPERM, EINVAL, ENOTDIR, ELOOP}`. `ENOENT`/`EACCES`/`EPERM` are
  already handled by the `FileNotFoundError`/`PermissionError` branches (`missing_executable_links` /
  `inaccessible_executable_links`); the new `unreadable` list covers `ESRCH`, `EINVAL`, `ENOTDIR`, `ELOOP`
  and any generic tolerated-errno `OSError`.
- Any other errno still raises
  `RuntimeError('STOP: unexpected executable census error for pid <pid> (errno <n> <CODE>)')` — now including
  the errno/code. Test: `test_unexpected_census_errno_still_stops_with_the_errno` (EIO → match
  `unexpected executable census error.*EIO`).
- Precision/residual: the **old** STOP-2 message did not record the errno, so the exact errno of pid 3075253
  is **not in the preserved evidence**; the fix's coverage of this specific failure is inferred from the
  transient-pid scenario (exited/unreadable `/proc/<pid>/exe`). The next run will record
  `unreadable_executable_errnos`, so the actual race errno becomes visible; if the same census STOP recurs
  with an errno outside the tolerated set it will still STOP and report the code (see §7.2).

## 5. (c) No cache/cold/lease/offload semantics changed

- The v5 tracked delta is only `cache_proc.py` + the two test fixtures + the cache-proc tests; the config
  change is the already-published `paper_commit` binding. The route-(i) fix, `runtime.py`, `qualify.py`,
  `llama_server_instance.py`, `llamacpp_probe.py`, `cooperative_lease.py`, `cache_runtime.py`,
  `cache_descriptive.py`, `cache_false.py`, `cache_nongen.py`, `cache_order.py`, `stage_a.py` are byte-identical
  to the accepted v4 hashes (verified). The cache/cold gate, request bodies, prompts, seeds and offload route
  are untouched; the census samples simply gain three gap fields, which the cache modules validate.
- The STOP-2 attempt itself demonstrates the route-(i) fix worked on both loaded models (`route: log_line`).

## 6. (d) Preservation of the STOP-2 site (verified read-only)

Observed 2026-11-01T01:14:51Z (UTC), kernel `6.8.0-136-generic`:

- Guardian **2920661** (`python`, state S) and preserved native server **3005245** (`llama-server`, state S)
  alive; both have `/proc/<pid>/fd/4 → /home/dowling/r1_locks/gpu0.lock`, and a scan of each fd table shows
  fd 4 is the only descriptor to the lock.
- `/proc/locks`: `FLOCK ADVISORY WRITE 2920661 103:02:120090387 0 EOF` — the guardian holds the real flock.
- Read-only `kcmp(KCMP_FILE)` from an unrelated same-UID process on FD 4:
  `kcmp(server, guardian, 4, 4) = rc 0`, `kcmp(guardian, server, 4, 4) = rc 0`, `kcmp(server, server, 4, 4) =
  rc 0`; negatives fd 3 → rc 2 and 4-vs-3 → rc 1. The guardian and preserved server share the same OFD.
- `gpu0.lock` unchanged: dev 66306, inode 120090387, nlink 1, size 0.
- No file under the run root is newer than `STOP.json` (no retry/resume marker); the STOP-1 evidence is
  unchanged (`STOP.json 2d38fece…`, `batch_state.json aa2e953b…`); the stopped namespace fixture is unchanged
  (`mtime = ctime = 1793446875`, mode 700). The qwen25 server record is stopped (`stopped_utc` set); the
  qwen38 record is preserved (`stopped_utc: null`).
- Evidence hashes recorded: STOP-2 lease `start.json bd9bf472…`, `runner.json e8731fa4…`,
  `lease_inheritance.json 92829357…`, `STOP.json d1eddb9f…`; out `batch_state.json b27373ce…`,
  `qwen25 exam_offload 37d9e726…`, `qwen38 exam_offload 74efc56d…`, `qwen38 lease_inheritance c00f3748…`,
  `qwen38 server record 44a58cdd…`, `d3_true_calls.jsonl 8923be63…`, `runner.log 4132000d…`,
  `qwen25 qualification 9a0b11a8…`.

## 7. Conditions

1. **Commit/bind:** commit the STOP-2 delta (cache_proc + tests/fixtures) as the new code commit; rebind
   `paper_commit` to it in a separate config-binding commit; verify the only config change is `paper_commit`,
   the launcher's ancestor+no-diff over the runtime-checked paths is empty, the run checkout is clean, and the
   manifest pins the accepted bytes (M1/M2 carry over; M3 for interpreter/venv/deps).
2. **New run:** the census samples in the new run must carry the gap fields
   (`unreadable_executable_links`, `unreadable_executable_errnos`, `unreadable_executable_samples`); if they
   are missing, STOP. If `unreadable_executable_links > 0`, inspect the recorded errnos; only the tolerated
   race errnos are expected; if the census STOP recurs with an errno outside `CENSUS_GAP_ERRNOS`, STOP and
   investigate (the code does this and reports the code). Route (i) must be used (`exam_offload.json`
   `route: log_line`, `full: true`, no fallback); if route (ii) is used, STOP.
3. **Recovery/authorization:** the STOP-2 preserved site (guardian 2920661 + server 3005245) must be kept
   until the author separately authorizes recovery and a new separately identified attempt; both share one OFD
   on FD 4, so ending the guardian alone will not release the lock — an authorized, recorded action must end
   both after evidence review. The STOP-2 batch/evidence must not be resumed, reused or counted as Stage A
   evidence; the STOP-1 evidence and the stopped namespace fixture remain untouched.
4. **Optional hardening:** `validate_census_snapshot` requires the new fields but does not cross-check their
   internal consistency (e.g., `len(unreadable_executable_samples) <= unreadable_executable_links`, errno
   names in `CENSUS_GAP_ERRNOS`, sample schema `{pid, errno, error}`). The reviewed sampler produces
   consistent values and the digest covers them; adding the cross-check would make a forged/inconsistent
   journal fail closed.
5. The exact STOP-2 errno remains unknown from the preserved evidence (see §4); the new run's gap fields are
   the way to confirm the race errno.

## 8. NOT CHECKABLE in this scoped review

- The exact errno of the STOP-2 failure (not recorded by the old message; inferred race).
- The new run's actual census behaviour and gap errnos (not yet run).
- The future commit/binding hashes and the final run manifest (not yet committed/run; M1).
- Same-UID non-interference and host-global single-server (author assumption / NOT_CHECKABLE; carry over).
- Real Stage A request/response/cache evidence (the STOP-2 attempt is partial; not Stage A evidence).

## 9. Final verdict

**`ACCEPT`** of the frozen v5 STOP-2 census-gap fix, with the §7 conditions. The fix tolerates only plausible
`/proc` race errnos as recorded, digest-covered observation gaps, keeps the exactly-one-owned-server
count/identity check and `observed` identity unchanged, keeps `host_global_single_server` NOT_CHECKABLE, still
STOPs on EIO-like errors with the code, and changes no cache/cold/lease/offload semantics. The STOP-2 evidence
shows the failure was the census STOP (not route/offload), the preserved guardian and native server retain the
same lock FD/OFD, and the attempt is not Stage A evidence.
