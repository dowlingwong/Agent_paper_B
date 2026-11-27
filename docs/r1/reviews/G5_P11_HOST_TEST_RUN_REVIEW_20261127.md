# Independent review — G.5 P11 TASL-7 host-test run record (`g5-p11-hosttest-20261127`), 27 November 2026

- Date: 2026-11-27 (Europe/Berlin). Reviewer: a fresh independent reviewer that did not write the unit. Read-only:
  no run, retry, edit, push (except this review), delete, signal or host action was taken. The reviewed branch and
  captures were read from `origin`; the capture files were extracted to a local temp directory and hashed there.
- Unit reviewed: branch `origin/compute-g5-p11-hosttest-20261127` @ `afcf95392ffc2e1d6f3c645404f01d52fb4dbfa9`
  (parent/base `5c901d19e682dbd50556054b2ebfb9e8f2c50ea1`). It changes the P11 table
  [`G5_P11_HOST_TEST_RECORD_20261127.md`](../reports/g5_code_20261123/G5_P11_HOST_TEST_RECORD_20261127.md)
  (sha256 `be01fdc573dc0045c5c28ef71d79c103e0ad31100bb9742ceec292f07046f3c7`) and adds
  `P11_HOST_TEST_RUN_20261127/`, whose run record
  [`P11_HOST_TEST_RUN_20261127.md`](../reports/g5_code_20261123/P11_HOST_TEST_RUN_20261127/P11_HOST_TEST_RUN_20261127.md)
  has sha256 `4656fcacff22e38262c5a381f802a9303178f753d9ffd0ea33967ff95f179719`; `SHA256SUMS` itself hashes to
  `4782a7b2e097268a659cf64f2ddc07ee9535cab9a10a6ebb3411f19554f68da6`.
- Bindings read at `origin/main` `29099c4bac068355d0b5593b8ac9665e19f38049` (the current tip; the reviewed branch
  is based on `5c901d19`). In the files relevant here, between `5c901d19` and `29099c4b` only D.3 PLAN §10 rows
  changed; the P11 table, `sweep2/t1_tasl/g5_tasl.py`, `g4_tasl.py`, `g5_job.py` and `T1_TASL_PLAN.md` are
  unchanged. T1 plan sha256
  `fc5606ae75fa486a45af98d1ec848c0ae4ee342d55359024a5184046f0f2867c`; committed G.5 spec sha256
  `16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f`; author row `R1-G5-P11` is `e9c29a16`.
- Outcome: one MAJOR finding, six MINOR findings, no BLOCKING finding.

Verdict: CHANGES REQUIRED

## Findings

### MAJOR-1 — C7's second start time and C10's second span contradict the bound `server_record_restart.json`

`server_record_restart.json:87` records `"started_utc": "2026-11-27T01:27:44Z"`, and `server_end_restart.json:2`
records `"stopped_utc": "2026-11-27T01:30:09Z"` — a server span of **2 min 25 s**. The branch states a different
start and span:

- run record line 34: "start 2 `01:27:30Z`, stopped `01:30:09Z`" and line 35: "spans of 2 min 16 s and 2 min 39 s";
- P11 table line 39: "two clean starts (`01:25:10Z`–`01:27:26Z`, `01:27:30Z`–`01:30:09Z`)" and line 42:
  "two spans of 2 min 16 s and 2 min 39 s".

`01:27:30Z` appears in no capture; `2 min 39 s` is exactly `01:27:30Z`→`01:30:09Z`. The 14 s difference is
consistent with the pre-flight before `popen` in `g4_tasl.serve_spec` (the 19.6 GB GGUF hash), so `01:27:30Z` is
the `serve` command invocation, not the server start that `serve_spec` records in `started_utc`. The **first**
start is stated from `started_utc` (`01:25:10Z`), so the two spans use different clocks. This is a factual
contradiction with the very capture the record binds, in the C10 number the P11 table will cite.

Fix: state start 2 as `01:27:44Z` and the second span as `2 min 25 s` in both the run record and the table; or state
the command time explicitly and use the same convention for both starts. Nothing else in the restart/identity
conclusion changes.

### MINOR-1 — `/props n_ctx_slot` is not a field of the captured `/props`

`props_start.json` and `props_restart.json` have no `n_ctx_slot`; the value is
`default_generation_settings.n_ctx = 32768`. The run record line 32 and `health_latency.txt:8` attribute
"`n_ctx_slot 32768`" to `/props`. If the figure is from the server log, cite the log; otherwise write
`default_generation_settings.n_ctx`. The value is correct and the identity check in `g4_tasl.server_identity`
uses `n_ctx`, so this is wording, not a failed check.

### MINOR-2 — "identical `/props`" is not byte-identical

The two props captures differ in one leaf only, the random per-boot `media_marker`
(`props_start.json` `…gajSx…` vs `props_restart.json` `…JZ75…`); every identity field equals
(`build_info` `b1-620d222`, `default_generation_settings.n_ctx` 32768, `total_slots` 1, `model_path`,
`model_alias`, `model_ftype`). Say "identical identity fields" rather than "identical `/props`"
(run record line 34; table lines 39 and 42).

### MINOR-3 — the log half of the record/log binding is declared but not captured

`server_end_start.json` and `server_end_restart.json` carry `server_log_sha256`
(`eeda4c41…` and `f81e90e1…`), but the two `llama-server.log` files are not in the capture set or `SHA256SUMS`.
The record-hash half recomputes (check 1); the log half cannot be checked from the branch. Either add the logs
(or their first/last lines plus hash) to the capture set, or state that they remain on TASL-7. Run record line 34
says the pairs "bind their log and record".

### MINOR-4 — uncaptured GPU-memory and "after" observations

Run record line 32 claims "GPU used 21,565 MiB / 24,564 MiB (88 %)"; line 19 claims the GPU was "empty before and
after". No file in the capture set records used memory, and `server_record_*.json` has only `foreign_before`
(`"foreign": []`); `serve_spec` writes no after-check. Add the `nvidia-smi` capture or label these as operator
observations. The `-ngl 999` argv, the 19.6 GB GGUF and the served `/props` support the §6 item 6 PASS
qualitatively; the specific figure and the "after" state do not.

### MINOR-5 — C10's table label "(short span, 27 Nov)" is ambiguous

The run is 2–3 minutes; the P11 option (b) "short span" is hours. The row's "What remains" column already says
"hours-long", and the status stays `PARTIAL` (correct), but the parenthetical reads as if the short span were met.
Use "(minutes, 27 Nov)".

### MINOR-6 — "no spec … was changed" is stale after the update

Table lines 63–65 still end "No pin, spec, note or evidence file was changed." The update created an engineering
spec copy with `run_id` changed (run record line 26, sha256 `2302bd18…`) and added evidence files. Say "no
committed spec, pin or note changed; the engineering spec copy is not a launch spec."

## The six checks

| # | Check | Result |
|---|---|---|
| 1 | Captured sha256 values recompute; `server_record`/`server_end` pairs bind the same record/log; the two starts have identical `/props` identity; argv, binary hash, build and GGUF hash match the spec and plan §6 | **PASS** (with MINOR-1/2/3) |
| 2 | No overclaim: C7 is restart + identity, not "around an audit phase"; C10 is minutes, not hours/multi-day; C11 is server-holds-lease, not the audit-chunk side; all said explicitly | **PASS** |
| 3 | The G.5 note-dependent paths refuse for the right reason | **PASS** |
| 4 | No G.5 label/evidence row, sealed attempt, test/evaluation read or fabricated note; engineering run id cannot be a G.5 label id; dirs outside `sealed_g5_proposer` | **PASS** |
| 5 | The table update is consistent with the original statuses and P11 option (b), and does not upgrade an item beyond its evidence | **FAIL** (MAJOR-1; statuses themselves are correctly kept `PARTIAL`) |
| 6 | The hash table in the run record matches the capture files; the three "see `SHA256SUMS`" entries are present and correct | **PASS** |

### 1. Hashes, bindings, argv, binary, build, GGUF — PASS

- `shasum -a 256 -c SHA256SUMS` in the capture directory: all **7/7 OK**.
- Pair binding: `server_end_start.json` `server_record_sha256` `e9593d7b…` equals the sha256 of
  `server_record_start.json`; `server_end_restart.json` `server_record_sha256` `900a837d…` equals the sha256 of
  `server_record_restart.json`. Each end also carries a distinct `server_log_sha256` (MINOR-3: logs not captured).
- `/props` identity: `build_info` `b1-620d222`, `default_generation_settings.n_ctx` 32768, `total_slots` 1,
  `model_path` `…/google_gemma-4-31B-it-Q4_K_M.gguf`, `model_alias` `gemma4_31b` on both starts. `media_marker`
  differs (MINOR-2).
- argv: the recorded array is exactly `server_argv(spec, 8095)` built from `g5_tasl_spec.json` — binary
  `/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server`, `-m` the pinned GGUF, `--alias gemma4_31b`,
  `-c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} --cache-type-k q8_0
  --cache-type-v q8_0 --no-webui`, `--host tasl-7.tail119748.ts.net`, `--port 8095`.
- Identities: binary `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`; build
  `version: 0.7.0-dev (build 1, commit 620d222)`; GGUF `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`
  (19,598,489,952 B); build-directory manifest `a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170`;
  GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, driver 580.178.04. All equal the spec, and T1 plan §6 item 6
  asks exactly `-ngl 999 -np 1`, ctx 32,768, q8_0 KV and the 19.6 GB GGUF.

### 2. No overclaim — PASS

The run record says C7 is "**PASS for the restart and identity**, not for an audit phase" and "No G.5 audit chunk
ran on TASL-7, so the 'around audit phases' part is not exercised" (line 34); C10 is "**PARTIAL**", "not the
'hours' short span", with the multi-day span and restart-as-infrastructure-STOP left for the table (line 35);
C11 is "**PARTIAL**" with "the audit-chunk side … was not run because the G.5 switch requires the signed note"
(line 36). The table keeps all three at `PARTIAL` and names the same remainders. The explicit bounds the task
requires are present. The wrong C10 duration (MAJOR-1) does not turn "minutes" into "hours"; it is an accuracy
defect in a row that is otherwise correctly partial.

### 3. Note-dependent paths refuse — PASS

The literal `t1_tasl_node.sh g5` path runs `g5_tasl.py run`, which enters `launch` (`g5_tasl.py:2748`) and calls
`load_spec` then `validate_spec(spec, launch=True)` (`:2770`); the `seal-*` commands enter `part_3b2`
(`:2878`) and call `validate_spec(spec, launch=a.cmd != "rel-copy")` (`:2886`). On the committed spec this raises
`STOP: run_id must be c3_t1_labels_<YYYYMMDD>` (reproduced locally) before any note or engine work; the committed
spec is `label: EVIDENCE` with PENDING fields and there is no signed G.5 note. The branch names that refusal and
does not claim a run. C2/C14/C9, C4/C5, C6/C15 and C16 are therefore correctly left unrun.

### 4. No G.5 label/evidence row, sealed attempt, test/evaluation read or fabricated note — PASS

The branch changes only the P11 table and the new `P11_HOST_TEST_RUN_20261127/` directory; `docs/r1/PLAN.md`,
`sweep2/` and `canon/` are untouched. The run id `g5-p11-hosttest-20261127` is not a `c3_t1_labels_<YYYYMMDD>`
id; both server records carry `"label": "ENGINEERING_ONLY"` and schema `g4_tasl_server_record/1`; the server
directories are `/home/dowling/r1_tracks/t1_tasl/proposer_g5/g5-p11-hosttest-20261127/server-{1,2}`, outside
`sealed_g5_proposer`; the run root is `/home/dowling/r1_engineering/p11_hosttest_20261127/`. No note file is added.
The spec copy's run id is also not of the label form, and the record says the copy is not launch-valid.

### 5. Table update consistent with the original statuses and P11 option (b) — FAIL

The three edited rows keep `PARTIAL`, and the "Reading" section still lists C10's hours-long span and C11's
audit-chunk side as remaining: that part is correct and is not an upgrade. The update fails consistency on the
evidence in two places: (a) C7/C10 repeat a second-start time and span that contradict `server_record_restart.json`
(MAJOR-1); (b) C10's "(short span, 27 Nov)" reads as if the option (b) short span (hours) had been shown when the
run is 2–3 minutes (MINOR-5). Correcting both makes the row consistent; no status change is needed.

### 6. Run-record hash table matches the capture files — PASS

The four explicit hashes in §4 equal `SHA256SUMS` (`server_record_start` `e9593d7b…`, `server_end_start`
`db624b48…`, `server_record_restart` `900a837d…`, `server_end_restart` `45f7f3b8…`). The three "see `SHA256SUMS`"
files are present and correct: `props_start.json` `2e01392a…`, `props_restart.json` `152a071f…`, `health_latency.txt`
`e1c49ea2…`.

## What was not checked

No host was contacted: TASL-7/TASL-2 bytes were not re-read from the hosts, and the review is of the committed
capture set plus the code, spec and plan on `origin`. The `server_log_sha256` values cannot be recomputed without
the logs (MINOR-3); the 21,565 MiB figure and the "after" GPU state cannot be checked without a capture
(MINOR-4). No sealed, test or evaluation data was read.

## Review-file hash

A file cannot contain its own sha256; the hash of this file as committed is reported in the hand-off message.
