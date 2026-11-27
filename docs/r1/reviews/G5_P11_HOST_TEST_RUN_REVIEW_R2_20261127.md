# Re-review R2 — G.5 P11 TASL-7 host-test run record (`g5-p11-hosttest-20261127`), 27 November 2026

- Date: 2026-11-27 (Europe/Berlin). Reviewer: the same fresh independent reviewer, read-only. No run, retry, edit,
  push (except this review), delete, signal or host action was taken. The reviewed branch and captures were read
  from `origin`; the capture files were extracted to a local temp directory and hashed there.
- Unit re-reviewed: branch `origin/compute-g5-p11-hosttest-20261127` @
  `ba5f1e4a2386cb7066ec4908e34a04dde17cab97`, one new commit on top of `afcf9539` (no force push; base
  `5c901d19`). The P11 table
  [`G5_P11_HOST_TEST_RECORD_20261127.md`](../reports/g5_code_20261123/G5_P11_HOST_TEST_RECORD_20261127.md) now has
  sha256 `d7f0b6e61d04772a014cf1e7eec35d94aae02dbd103e45d4acf1c97379c630fe`; the run record
  [`P11_HOST_TEST_RUN_20261127.md`](../reports/g5_code_20261123/P11_HOST_TEST_RUN_20261127/P11_HOST_TEST_RUN_20261127.md)
  has sha256 `315db51448039d0abbd371b16104e4669fd98a1bf899c4e956e322bc5498a981`; `SHA256SUMS` hashes to
  `9e2f28e09cd26a687d3db5101e767c22b29c99dcc70217eac1ce2b767fe0938c`.
- Previous review: [`G5_P11_HOST_TEST_RUN_REVIEW_20261127.md`](G5_P11_HOST_TEST_RUN_REVIEW_20261127.md) (R1,
  `5ba7bbcb`), CHANGES REQUIRED on one MAJOR and six MINOR findings.
- Bindings re-read at `origin/main` `29099c4bac068355d0b5593b8ac9665e19f38049`; `T1_TASL_PLAN.md`, the committed
  G.5 spec and the G.5 code are unchanged since R1.
- Outcome: every R1 finding is resolved in the reviewed record. Two residual MINOR observations remain; neither is
  blocking.

Verdict: ACCEPTED

## Per-finding resolution

| # | R1 finding | Status at `ba5f1e4a` | Evidence |
|---|---|---|---|
| MAJOR-1 | C7 start 2 stated as `01:27:30Z` and C10 second span as 2 min 39 s, contradicting `server_record_restart.json` | **RESOLVED** | Run record lines 34–35 and table lines 39/42 now give start 2 `01:27:44Z`, stop `01:30:09Z`, spans 2 min 16 s / 2 min 25 s, and state the clock ("the recorded server process start, not the `serve` invocation 14 s earlier"). `server_record_restart.json:87` `started_utc` `01:27:44Z` and `server_end_restart.json:2` `stopped_utc` `01:30:09Z` reproduce 2 min 25 s. The logs corroborate: their last elapsed stamps are 2.16.103 (start) and 2.24.324 (restart). |
| MINOR-1 | `/props n_ctx_slot` is not a `/props` field | **RESOLVED in the run record; residual note in `health_latency.txt`** | Run record line 32 now says `/props default_generation_settings.n_ctx = 32,768`. The untouched capture note `health_latency.txt:8` still prints `n_ctx_slot 32768` under a `/props ->` label; see R2-MINOR-1. The value is real (also in the server log line 12), so this is a label, not a wrong number. |
| MINOR-2 | "identical `/props`" is not byte-identical | **RESOLVED** | Run record line 34 and table lines 39/42 now say "the same identity fields"; the two props files still differ only in `media_marker`. |
| MINOR-3 | `server_log_sha256` declared but the logs were not captured | **RESOLVED** | `server_log_start.txt` sha256 `eeda4c41…` and `server_log_restart.txt` sha256 `f81e90e1…` are in the branch and `SHA256SUMS`; each equals the corresponding `server_log_sha256` in `server_end_start.json` / `server_end_restart.json`. The pairs now bind the same record and log. |
| MINOR-4 | uncaptured 21,565 MiB figure and "empty after" | **RESOLVED** | The figure is removed. Run record line 32 says GPU memory used during the run "was observed but not captured"; `nvidia_smi_after.txt` is present (44 MiB used, 24,029 MiB free, 0 %, hashed `86a9cbca…`); the §1 GPU row now says `foreign_before` empty in both records and the after capture shows 44 MiB. See R2-MINOR-2 on "no compute app". |
| MINOR-5 | C10 label "(short span, 27 Nov)" ambiguous | **RESOLVED** | Table line 42 now reads `PARTIAL` (minutes, 27 Nov); the "What remains" column still says hours-long. |
| MINOR-6 | stale "No pin, spec, note or evidence file was changed" | **RESOLVED** | Table lines 63–65 now read "No pin, note or evidence file was changed; the run uses only an ENGINEERING copy of the spec with its `run_id` changed, and this branch adds captures." |

## New findings (both MINOR, neither blocking)

### R2-MINOR-1 (residual of MINOR-1) — `health_latency.txt:8` still labels `n_ctx_slot` as `/props`

The run record is corrected, but the capture note still says
`/props -> build_info b1-620d222, total_slots 1, n_ctx_slot 32768, model …`. The captured `/props` has no
`n_ctx_slot`; the field is `default_generation_settings.n_ctx`, while `n_ctx_slot = 32768` is the server-log line
(`server_log_start.txt:12`, `server_log_restart.txt:12`). A one-line correction of the note (or citing the log for
`n_ctx_slot`) closes it. It does not affect the run record's now-correct claim.

### R2-MINOR-2 (residual of MINOR-4) — "no compute app" is inferred, not captured

`nvidia_smi_after.txt` is one GPU-usage line (name, total, used, free, utilisation), not a
`--query-compute-apps` listing. The run record's "the after capture shows 44 MiB used and no compute app" (line 32)
infers the second clause from the 44 MiB. Either add the compute-apps query or say "44 MiB used, consistent with no
compute process". The 44 MiB figure itself is captured and correct.

## The six checks, re-run

| # | Check | Result |
|---|---|---|
| 1 | All captured sha256 values recompute; `server_record`/`server_end` pairs bind the same record/log; the two starts have identical `/props` identity; argv, binary hash, build and GGUF hash match the spec and plan §6 | **PASS** |
| 2 | No overclaim: C7 restart + identity, C10 minutes, C11 server-holds-lease; item 6 is "PASS for the declared server configuration", not "full offload"; during-run memory explicitly not captured | **PASS** |
| 3 | The G.5 note-dependent paths refuse for the right reason (unchanged code and spec) | **PASS** |
| 4 | No G.5 label/evidence row, sealed attempt, test/evaluation read or fabricated note; engineering run id; dirs outside `sealed_g5_proposer` | **PASS** |
| 5 | The table update is consistent with the original statuses and P11 option (b), and does not upgrade an item beyond its evidence | **PASS** |
| 6 | The run-record hash table matches the capture files; `SHA256SUMS` recomputes for all entries | **PASS** |

1. **Hashes and bindings — PASS.** `shasum -a 256 -c SHA256SUMS`: **10/10 OK**. The record/end pairs bind:
   `server_end_start.json` `server_record_sha256` `e9593d7b…` = sha256 of `server_record_start.json`;
   `server_end_restart.json` `server_record_sha256` `900a837d…` = sha256 of `server_record_restart.json`. The log halves now bind too:
   `eeda4c41…` and `f81e90e1…` equal the two `server_log_sha256` values. The `/props` identity fields match on both
   starts (`build_info` `b1-620d222`, `default_generation_settings.n_ctx` 32768, `total_slots` 1, model path/alias);
   only `media_marker` differs. The argv is exactly `server_argv(spec, 8095)`; binary
   `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`, build
   `version: 0.7.0-dev (build 1, commit 620d222)`, GGUF
   `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` (19,598,489,952 B) and manifest
   `a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170` all equal the spec and plan §6 item 6.
2. **No overclaim — PASS.** C7 says "PASS for the restart and identity, not for an audit phase"; C10 stays
   `PARTIAL` at minutes and names the hours/multi-day remainder; C11 stays `PARTIAL` with the audit-chunk side
   named. Item 6 now reads "**PASS for the declared server configuration**" and records the declared argv and
   `/props`; it no longer claims "full offload", and it says the during-run GPU memory was observed but not
   captured. The after capture and the two logs are cited. No new overclaim is introduced (R2-MINOR-2 is an
   inference in one clause).
3. **Note-dependent paths — PASS.** Unchanged: `g5_tasl.py` `launch` (`:2748`) and `part_3b2` (`:2878`) call
   `validate_spec(launch=True)`; on the committed spec it raises `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`.
   The committed spec is `label: EVIDENCE` with PENDING fields and there is no signed G.5 note, so C2/C14/C9,
   C4/C5, C6/C15 and C16 are correctly left unrun.
4. **No G.5 label/evidence row, sealed attempt, test/evaluation read or note — PASS.** The new commit changes only
   the P11 table, the run record, `SHA256SUMS` and the three new captures; `docs/r1/PLAN.md`, `sweep2/` and
   `canon/` are untouched. The run id `g5-p11-hosttest-20261127` is not a `c3_t1_labels_<YYYYMMDD>` id; the server
   records carry `ENGINEERING_ONLY` / `g4_tasl_server_record/1`; the server dirs are under `proposer_g5`, outside
   `sealed_g5_proposer`; the run root is under `r1_engineering`.
5. **Table update consistent — PASS.** C7/C10 now carry the captured times and spans; C10 is "(minutes, 27 Nov)";
   all three edited rows stay `PARTIAL`; the "Reading" section still lists C10's hours-long span and C11's
   audit-chunk side as remaining; the closing sentence distinguishes the engineering spec copy from committed
   files. No item is upgraded beyond its evidence.
6. **Hash table matches — PASS.** The §4 table now lists all ten capture files; each hash equals `SHA256SUMS`, and
   `SHA256SUMS` recomputes. The three former "see `SHA256SUMS`" entries are now explicit and correct.

## Reviewed sha256s

| File | sha256 |
|---|---|
| `G5_P11_HOST_TEST_RECORD_20261127.md` | `d7f0b6e61d04772a014cf1e7eec35d94aae02dbd103e45d4acf1c97379c630fe` |
| `P11_HOST_TEST_RUN_20261127/P11_HOST_TEST_RUN_20261127.md` | `315db51448039d0abbd371b16104e4669fd98a1bf899c4e956e322bc5498a981` |
| `P11_HOST_TEST_RUN_20261127/SHA256SUMS` | `9e2f28e09cd26a687d3db5101e767c22b29c99dcc70217eac1ce2b767fe0938c` |
| `P11_HOST_TEST_RUN_20261127/server_log_start.txt` | `eeda4c41d2428d1d6c9e25544cd930c1e2326c76c3c9a34e101c9281711953b3` |
| `P11_HOST_TEST_RUN_20261127/server_log_restart.txt` | `f81e90e1220336ae0eefc569a46b6cd5dbb7dd24f529ece89bd719f693885989` |
| `P11_HOST_TEST_RUN_20261127/nvidia_smi_after.txt` | `86a9cbca9bef0126dad28b3f655519b43b220f6a71d3815d69b64897a6193307` |
| `P11_HOST_TEST_RUN_20261127/server_record_start.json` | `e9593d7b2c476fba58613ec98aed05065db4b62838b91d5e42c523ab2aa07ec6` |
| `P11_HOST_TEST_RUN_20261127/server_end_start.json` | `db624b4869cf5a65cfd6107e1e1a8051f99d0ff811ccb4ab198dafd8b81e9805` |
| `P11_HOST_TEST_RUN_20261127/server_record_restart.json` | `900a837d692ea8f04ce395120e83245ed9d0bdef6227e4b0c66db6cb539a5c66` |
| `P11_HOST_TEST_RUN_20261127/server_end_restart.json` | `45f7f3b8c6be2e5df279765918880e4290530a9511267282939b742c3132a6f8` |
| `P11_HOST_TEST_RUN_20261127/props_start.json` | `2e01392a88ac80a224c43373c11aae8f4c032bb01531f93943ead0cce46c7eed` |
| `P11_HOST_TEST_RUN_20261127/props_restart.json` | `152a071fac02f4444a4abf651fb4dbb6d69effd561a466399699861e71706937` |
| `P11_HOST_TEST_RUN_20261127/health_latency.txt` | `e1c49ea2f4bf2c8315280c542fb3d41abb0e755016896b210670cc7865506d5b` |

## What was not checked

No host was contacted: TASL-7/TASL-2 bytes were not re-read from the hosts; the review is of the committed capture
set plus the code, spec and plan on `origin`. The two server logs are the complete files whose hashes match the
`server_end_*.json` fields; they contain startup and shutdown lines, not request lines. No sealed, test or
evaluation data was read.

## Review-file hash

A file cannot contain its own sha256; the hash of this file as committed is reported in the hand-off message.
