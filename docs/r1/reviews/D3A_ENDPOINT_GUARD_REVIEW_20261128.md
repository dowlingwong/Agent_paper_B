# D.3a endpoint identity guard — independent tier-E review

Reviewer: independent subagent (fresh clone; did not write the change). Date: 28 Nov 2026.
Task: `compute/20261128-23` (per-chunk server checks for the D.3a production template).
Method: fresh clone and fresh worktree of the deliverable tip, reading the guard, the driver,
the stub test and the record; independent re-execution of the unit/integration tests, the three
stub driver modes and the two seals on TASL-2 and on macOS; adversarial reading of the guard for
bypasses and of the record for overclaims. I did not modify the deliverable branch.

| Item | Value |
|---|---|
| Published base | `origin/main` `c66603ae8ac5f176ffe6a3b649cdb8b3d87d51de` |
| Deliverable branch | `compute-d3a-template-checks-20261128` @ `d617fd3299a24938621e5009846be943889fcd46` |
| Tip verified on GitHub | `git ls-remote --heads origin compute-d3a-template-checks-20261128` → `d617fd32…` |
| Earlier tips seen | `80dae9fc…` (first pass), `2f2e3981…` (SPID-0 seal fix) — both were fast-forwarded; this review is at `d617fd32` |
| Review branch | `compute-d3a-template-checks-20261128-review` (branched from `d617fd32`) |
| Hosts | macOS (worktree) and TASL-2 (fresh clone `/tmp/d3a_guard_review`, `git status --porcelain` empty) |
| Reference host state | TASL-2 RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; `~/r1_locks/gpu0.lock` present |

## Verdict

**ACCEPTED WITH MINORS.** No blocker. The template now proves, before every chunk, that the
endpoint is served by the server process the driver started on the leased card, and any mismatch
is a sealed infrastructure STOP (exit 90) taken before `r1.c3.d3.campaign_chunk` is imported. The
R1–R4 review minors are addressed (R1–R3 fixed; R4 is correctly out of the record). The residual
items below are non-blocking traceability/robustness notes.

## What the change does (and how I checked it)

Diff scope: `git diff --name-status c66603ae..d617fd32` is 14 paths — the new
`r1/c3/d3/endpoint_guard.py`, the new `r1/tests/test_d3_endpoint_guard.py`, the driver and its
stub test inside the record directory, the record, its captures and both `SHA256SUMS`. No signed
note, PLAN, manifest, launch JSON, ledger, seed, image/report code path or `r1/c3/d3/__init__.py`
changed. `captures/launch_ssh_dryrun.txt` is a capture, not the launch record.

**Guard (`r1/c3/d3/endpoint_guard.py`).** Every check is a `check(...)` that raises `EndpointStop`
on failure; there is no path that logs a mismatch and continues, no defaulting of an unread value,
and no CLI flag that skips a check. Order: lease path equals the manifest route; `observed.json`
UUID/lease/lease-path; server PID alive; the guard's inherited `--lease-fd` is the canonical lease
inode; a server fd is the same inode; listener PIDs on the manifest port are exactly `[server_pid]`
(an empty or unattributable `ss` result fails closed); `/props` `model_path`, `n_ctx`, `total_slots`
equal the manifest `server_argv`; the PID appears exactly once in `nvidia-smi --query-compute-apps`
and on the manifest UUID; `nvidia-smi -i <lease index>` equals the manifest UUID. `expected_route`
refuses a `--host`/`--port` that differs from the manifest argv, and the CLI returns 90 and writes
`r1_d3_endpoint_check/v1` with `ok=false` on any exception. Because the server must hold the
canonical lease inode, PID reuse by an unrelated process cannot satisfy the identity set, and a
listener owned by another user makes `ss` omit `pid=`, which is an `EndpointStop` rather than an
empty success.

**Driver (`production_driver.sh`).** `verify_endpoint "ready"` runs immediately after readiness and
`run_chunk_checked` calls `verify_endpoint "chunk_${tag}"` immediately before every
`r1.c3.d3.campaign_chunk` invocation, in both the single-chunk and the `CHUNK_ROWS` multi-chunk
paths. On failure `seal_scene` stops the started server, writes `STOP.json`
(`r1_d3_endpoint_stop/v1`), hashes the whole capture directory with `sha256sum` (falling back to
`shasum -a 256`), keeps the scene and exits 90. `set -uo pipefail` without `-e` is deliberate: each
step's status is captured explicitly. The lease fds 8/9 are opened and flocked by the wrapper, so a
STOP releases them at process exit.

**Record.** §4.1 lists the same conditions the code enforces, including "no other PID", the lease
fd 9 and the leased-card UUID; §7 states the stub-test and pytest results; §8 now carries the new
driver, guard, test and capture hashes, which all match the files (checked below). I found no
overclaim: the record says the executed proof is `endpoint_run.sh` and that the chunk branch was
not run, and the full-suite sentence says explicitly that it was run at code tip `0354083d` and
that the later commits add only the SPID-0 seal guard, record text and seals.

## Checks run (exact commands and results)

All at `d617fd32` unless stated.

**Seals, macOS worktree.**

```
cd docs/r1/reports/d3a_production_route_20261128 && shasum -a 256 -c SHA256SUMS
  -> exit 0, 43 lines OK
cd captures && shasum -a 256 -c SHA256SUMS
  -> exit 0, 34 lines OK
shasum -a 256 ../SHA256SUMS
  -> b30d03bc41f96227288e88dd6e850f3da4c4acc1a9d4726443fed8c5a0be695f
```

**Seals, TASL-2 fresh clone.**

```
git clone --branch compute-d3a-template-checks-20261128 \
  https://github.com/dowlingwong/Agent_paper_B.git /tmp/d3a_guard_review   # HEAD d617fd32
cd docs/r1/reports/d3a_production_route_20261128
LC_ALL=C sha256sum -c SHA256SUMS          -> exit 0, 43/43 OK
cd captures && LC_ALL=C sha256sum -c SHA256SUMS -> exit 0, 34/34 OK
```

**Unit/integration tests.**

```
# macOS worktree
AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness PYTHONPATH=$PWD \
  /Users/wongdowling/Documents/agent_paper_B-workers/compute/.venv/bin/python \
  -m pytest r1/tests/test_d3_endpoint_guard.py -q
  -> 22 passed, 1 skipped in 0.06s   (Linux-only integration skips)

# TASL-2 fresh clone
cd /tmp/d3a_guard_review && PYTHONPATH=$PWD /home/dowling/r1_tracks/venv/bin/python \
  -m pytest r1/tests/test_d3_endpoint_guard.py -q
  -> 23 passed in 0.53s
```

`bash -n` passes on `production_driver.sh` and `endpoint_guard_driver_test.sh`.

**Three stub modes, TASL-2.** `REAL_PYTHON=/home/dowling/r1_tracks/venv/bin/python bash
docs/r1/reports/d3a_production_route_20261128/endpoint_guard_driver_test.sh <mode>`:

| Mode | Observed |
|---|---|
| `success` | `mode=success rc=0`, `chunk_called=yes`, `stop_json=no`, `result=PASS` |
| `foreign` | `rc=90`, `chunk_called=no`, `stop_check=ready rc=90`, `endpoint_check_ready.json: ok=False failed=guard reason=listener_pid: …`, `seal=OK`, `result=PASS` |
| `bindfail` | `rc=90`, `chunk_called=no`, `stop_check=ready rc=90`, `failed=guard reason=server_alive: …`, `seal=OK`, `result=PASS` |

**Additional failure-path and multi-chunk checks (my own copy, not a repo change).** I patched a
copy of `endpoint_guard_driver_test.sh` in my temp clone so its `ss` stub returns the started PID on
the first call and a foreign PID on the second, then ran `success`:

```
rc=90, chunk_called=no, stop_check=chunk_01 rc=90, seal=OK
endpoint_check_ready.json: ok=True failed=None
endpoint_check_chunk_01.json: ok=False reason=listener_pid: …
```

This exercises the "server changes between the ready check and the chunk check" case: the guard
stops immediately before the first chunk, the chunk is not called, and the scene is sealed. After
the run `flock -n` on both test lease files succeeded (`gpu_lease_free`, `cpu_lease_free`), so a
STOP does not leave a lease held.

I also ran the unmodified test with `CHUNK_ROWS` set to two rows: `rc=0`, `chunk_called=yes`,
`endpoint_check_ready.json`, `endpoint_check_chunk_01.json` and `endpoint_check_chunk_02.json` all
present, and `status.log` shows `endpoint_check_pass` immediately before each `chunk_start`.

**Real host parsing (read-only).** On TASL-2, with a temporary listening socket, the real command
`ss -ltnp 'sport = :<port>'` parsed through `parse_ss_listeners` to exactly the process PID;
`HostProbe.lease_gpu_uuid('/home/dowling/r1_locks/gpu0.lock')` returned
`GPU-4d623e76-7587-ee15-a633-46f60d220d94`; the real (empty)
`nvidia-smi --query-compute-apps=…` output parsed to `[]`; and `nvidia-smi -i 0 --query-gpu=uuid`
returned the manifest UUID. I also confirmed bash propagates `exec 9>path` to an exec'd child
(`/proc/self/fd/9` resolves to the lease path), which the `server_lease_fd` check depends on. The
record's `captures/props.json` shows `model_path` equal to the manifest `-m`, `n_ctx: 32768` and
`total_slots: 1`, matching the guard's reads.

**Full-suite comparison: accepted, not re-run.** I read
`captures/endpoint_guard/full_suite_compare.txt`: base `c66603ae` 53 failed / 4888 passed, tip
`0354083d` 52 failed / 4912 passed, 3 errors at both, one base-only flaky `FAILED` and zero
tip-only IDs. I did not re-run the 3.5-minute suite. The residual point is that the capture has no
command line and no full FAILED/ERROR ID lists, so "zero tip-only" is taken on trust from the
capture rather than reproduced.

## R1–R4 disposition

- **R1 — fixed.** `captures/launch_ssh_dryrun.txt` now shows
  `launch(launch_path="/home/dowling/…/launch_A0_digits_mlp_r0.json", out_dir=…)` as the first
  positional. I did not re-render the launch script (no bearing on the guard).
- **R2 — fixed and verified.** The record now says the environment block was appended at
  `19:33:44Z` (file mtime). On TASL-2 the host file's mtime is `2026-11-28 11:33:44.3246` local
  (UTC+8) = `19:33:44Z`.
- **R3 — fixed.** `captures/cache_staging.txt` has a two-line header with the 19:27–19:34Z
  provenance and states honestly that the staging command line was not retained.
- **R4 — not a record defect.** The record correctly defers the root `SHA256SUMS` hash to the
  `coord/compute` report. At this tip the root hash is `b30d03bc…`; the Compute handoff can state
  it verbatim. Non-blocking.

## Residual minors (non-blocking)

1. **STOP evidence collapses the per-check detail.** The CLI's exception path starts a fresh
   `GuardResult` and records only `failed="guard"`, `observed=null`, with the check name surviving
   only in the `reason` text. The observed listener list (the foreign PID) is therefore not in
   `endpoint_check_<tag>.json`, `guard.log` or `STOP.json` (confirmed in my chunk-time run). An
   operator sees *that* the listener was wrong but not *which* process answered. Recording the
   observed value in the stop record would make the scene self-contained.
2. **`seal_scene` waits without a timeout.** `kill -TERM` then `wait "$SPID"` has no timeout or
   `kill -KILL` fallback; a server that ignored SIGTERM would hang the STOP with the lease still
   held and no `STOP.json`. The started binary is `llama-server`, which exits on TERM, so this is
   low likelihood.
3. **Point-in-time guard.** There is an unavoidable window between the guard's exit and the
   chunk's first request; if the server died in that window a foreign process could bind the freed
   port. The server is a child holding the lease inode, so accidental takeover is implausible, and
   the card asked for a check before each chunk, which is delivered.
4. **Production checkout precondition.** The driver imports the guard with
   `"$PYTHON" -m r1.c3.d3.endpoint_guard` from the `$REPO` working directory (`PYTHONPATH` is the
   audit shim, not the repo). A production checkout pinned to the pre-guard commit `c3a48405` would
   fail closed with exit 90 at the first check. The final launch binding must pin a paper commit
   that contains `r1/c3/d3/endpoint_guard.py`; the record does not say this.
5. **Full-suite capture provenance** (see above): counts and a two-line ID diff only, no command
   and no full ID lists.
6. **`endpoint_guard_driver_test.sh` seal check is Linux-only.** It calls `sha256sum -c`
   unconditionally, so on macOS it prints `seal=FAIL` even when the seal is correct. The script is
   documented as the Linux engineering test and the captures are from TASL-2, so this is cosmetic.
7. **`CHUNK_ROWS` treats any non-empty line as a row.** A comment or header line would be passed to
   `campaign_chunk` as a launch path. Acceptable for a driver-owned tab file.

None of these lets a foreign responder reach the chunk, weakens fail-closed behaviour, or blocks
the engineering review.

## What I did not verify

- I did not re-run the 3.5-minute full `r1/tests` suite; I accepted
  `captures/endpoint_guard/full_suite_compare.txt` (see the provenance note).
- I did not re-render the `launch_ssh` dry-run script or re-derive its hash, and did not re-check
  the resource-basis, proxy/P7 or campaign-manifest numbers from the earlier review — none is
  touched by this diff.
- I did not start a real `llama-server` or run a GPU workload. The live-server specifics (the
  server holding fd 9, real `/props` under the manifest argv) are evidenced by the prior endpoint
  capture (`captures/props.json`, the prior review's fds 8/9 observation) and by the synthetic
  tests, not by a new endpoint start.
- I read no label or evaluation partition, no credential file, and changed nothing outside this
  review file.
