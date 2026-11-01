# Track X Stage A — second attempt STOP 2 (`/proc` census gap misclassified as STOP)

Date: 2026-11-01 ~01:11 UTC (02:11 Europe/Berlin). Attempt:
`r1_stagea_20261101_b3d7f2` (manifest `35d2138322cd248fb0b378cc80e481b96814d6e7c527afa2a3487894109a14d3`),
checkpoint `9bfabe5` (route-(i) fix `5bf7065` + binding), real lock acquired 00:41:55 UTC.

## What worked before the STOP

- Anchors `random_valid` and `scripted` completed; `qwen25_coder_7b` completed with
  **route (i)** evidence: `servers/qwen25_coder_7b/exam_offload.json` =
  `full: true, line: full, route: log_line, offloaded 29/29, cpu_fallback_lines: []`;
  qualification `status: PASS, footprint_mib: 5784, offload_route: log_line`.
- `qwen38_27b` qualification and offload also showed route (i) (`offloaded 66/66`,
  `route: log_line`, no CPU-fallback); its descriptive replay reached request 152.
- The route-A footprint repair is therefore working in the real run; STOP 2 is unrelated to
  offload, cache/cold or lease/FD/OFD behaviour.

## STOP 2

The replay worker exited 1 with
`RuntimeError: STOP: unexpected executable census error for pid 3075253`
(`r1/exam/cache_proc.py:81`); the run stopped with `batch_state.status = STOPPED` and reason
`RuntimeError: STOP: root worker exit 1; see …/qwen38_27b/stage-a/32768`. Journals:
`d3_true_calls.jsonl` 761 lines with a `stop` event at sequence 152;
`d3_false_calls.jsonl` and `d3_non_generation_calls.jsonl` empty. No `stage_a.json` and no
`stage_a_table.json`: **this attempt is not Stage A evidence**.

Root cause: the executable census scanned unrelated `/proc` pids and raised a hard STOP for
ANY `OSError` other than ENOENT/EACCES. pid 3075253 most likely exited between the directory
listing and the `exe` read (transient race). The author's requirement is that unreadable
`/proc` PIDs are **recorded observation gaps**, not evidence of absence.

## Fix (independently reviewed scoped ACCEPT)

Code `0d9e4ed` (config binding `4722e10`), branch `codex/trackx-stagea-cooperative-20261031`:
`cache_proc.py` records plausible `/proc`-race errnos (ESRCH, ENOENT, EACCES, EPERM, EINVAL,
ENOTDIR, ELOOP) as gaps (`unreadable_executable_links`, `unreadable_executable_errnos`,
`unreadable_executable_samples`); any other errno still STOPs and now reports the errno code;
the exactly-one-owned-server count/start-tick check is unchanged and the owned server failing
to be visible still STOPs; `validate_census_snapshot` requires the gap fields; tests and
shared census fixtures updated. Relevant Mac CPU subset: **373 passed, 1 skipped**.
Review: `docs/r1/reviews/TRACKX_STAGEA_STOP2_FIX_REVIEW_20261101.md` (ACCEPT with conditions;
snapshot v5 `SHA256SUMS` `6a1607ec…f93fe`).

## Preserved site (not cleaned, signalled, resumed or counted as evidence)

- guardian **pid 2920661** holds the real flock (`/proc/locks`: FLOCK WRITE on inode
  120090387, `gpu0.lock` dev 66306 / inode 120090387 / size 0 / nlink 1 unchanged);
- preserved native server **pid 3005245** (`qwen38_27b`, ctx 32768) retains FD 4 →
  `gpu0.lock`; read-only guardian→server `kcmp(KCMP_FILE)` on FD 4 = **rc 0** (same OFD);
  ending the guardian alone would not free the lock while the server holds FD 4;
- `STOP.json` (`lease_retained: true`, `retry_permitted: false`,
  `completed_release: false`), SHA-256 `d1eddb9f…`; `batch_state.json` SHA-256 `b27373ce…`;
  run and lease evidence directories untouched; STOP-1 evidence unchanged; the stopped
  namespace fixture unchanged (mtime=ctime=1793446875).

## Required before any further attempt

The author must authorize (a) ending **both** the guardian and the preserved server after
evidence review (recorded action; the batch is never resumed or reused) and (b) a new,
separately identified Stage A attempt at a reviewed checkpoint. The new attempt must use
route (i) (`route: log_line`, no fallback), must show the census gap fields in every sample
(missing → STOP), and must STOP if an out-of-set census errno recurs.
