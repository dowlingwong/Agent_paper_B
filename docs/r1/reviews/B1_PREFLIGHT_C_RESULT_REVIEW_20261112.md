# Independent review — result of the one-shot B1 author gate + TASL-7 native preflight (`_c`)

- Date: 2026-11-12 (Europe/Berlin).
- Reviewer: fresh independent reviewer; did not run and did not write the reviewed unit. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was modified; only this review was written under `_xfer/`. TASL-7 was inspected read-only (`ls`, `stat`, `cat`, `sha256sum`, `git rev-parse`/`status --no-optional-locks`, `tmux ls`, `nvidia-smi`, non-blocking `flock` probe, `ps`, `pgrep`); no writes, signals, GPU work or server start.
- Unit reviewed: the one-shot execution of the filled `docs/r1/proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` for run HEAD `4b312844962e1106db04d5a60bf996fad0e3e514` (`_c` restart), judged against that document's PASS criteria. Earlier run-HEAD, staging and filled-script/transport reviews are context only.

## Artifacts and hash consistency — PASS

Local capture `/private/tmp/paper-b-final-host-preflight-capture-c-20261112.kthNod0i/` (0700, `wongdowling:wheel`, birth 21:25:12 CET; only the two expected files):

| File | Size | SHA-256 |
|---|---|---|
| `ssh.log` | 765 B (6 lines, no CR) | `9ade9f3f468dd11229e8b16137ca4b6fa85c7adb757c8fa0e3ef682ffa3b3508` |
| `ssh.exit` (`0\n`) | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

Remote CAP `/home/dowling/r1_b1_engineering/b1_final_gate_preflight_4b31_20261112_a` (0700, `dowling:dowling`; birth 2026-11-12 12:25:15 PT):

| File | Size | SHA-256 |
|---|---|---|
| `gate.log` | 611 B | `7d9b357ebbf7da40a632b65829982d0d8606645711dbb7d7852ad73de65c8678` |
| `gate.exit` (`0\n`) | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `preflight.log` | 1508 B | `306d8764164ce981d56ab2623ded1c2efef165ca826fb4d1f600809fde9a02a2` |
| `preflight.exit` (`0\n`) | 2 B | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |

Re-fetching the four remote files and hashing them locally reproduces exactly the four values printed in `ssh.log` lines 3–6, with the exact CAP paths. Timing is coherent: capture born 12:25:12 PT, CAP born 12:25:15, `gate.log` 12:25:17, OUT born 12:28:17, `preflight.exit` 12:28:18.78, local `ssh.exit` 21:28:19 CET (12:28:19 PT). Both remote exit records and local `ssh.exit` are 0; there is no dropped-SSH ambiguity.

## 1–2. Author gate — PASS

`gate.log` is 611 B, 4 lines, with exactly one `GATE_PASS` line:

`GATE_PASS 4b312844962e1106db04d5a60bf996fad0e3e514 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad python /home/dowling/exam-x/work/venv/bin/python prefix /home/dowling/exam-x/work/venv worker_python /home/dowling/exam-x/work/venv/bin/python3 threads 1 1 1`

Exactly three `node_source` lines are present (no more): `digits_mlp` `train.py` `4c0692ba3fe210e2dad18e18a1d7809e36af107be68ef18a0958f0abad8327e6`; both `openml_credit_approval/config.yaml` and `openml_ionosphere/config.yaml` `60e31d308bea7f2e956cedb58bf2e8a581fa640054e38dd791eb51fa1b012533`. I re-hashed those files in the pinned clean harness and got the same three digests. There is no `STOP`, `error`, traceback, exception or failure line.

The gate binding is genuine: at the staged checkout the worktree bytes of `r1/scripts/configs/exam_b1_v2.json`, `r1/exam/rules/x5_rule_v2.yaml` and `docs/r1/authorizations/trackx_b1_20261105.md` equal their `git show HEAD:` bytes; the rule file hashes to `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`; the committed note at HEAD has `"approved": true`, `"phase": "b1"`, the same `rule_sha256`, host `TASL-7` and the pinned GPU UUID, and describes this `_c` restart/truncation fix. The gate's HEAD literal is the reviewed run HEAD.

## 3. Native preflight — PASS

`preflight.log` is 1508 B: three JSON lines plus `PREFLIGHT_PASS: owned server exited and own lease descriptor closed`; no `STOP`/error.

- `validated_models` has 16 unique entries, exactly the union of the model rows with `passed: true` in the sha-bound Stage A tables `r1_stagea_20261103_t7h8/stage_a_table.json` (`00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c`) and `r1_stagea_20261104_t7j10/stage_a_table.json` (`71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`), excluding the software anchors; set-for-set match, with `qwen25_coder_7b` last. The anchor's actual GGUF hashes to `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, the same SHA recorded by the server and by both Stage A tables.
- `gpu_before`: device 0, 23812.0 MiB free / 236.0 MiB used / 0.0%; current `nvidia-smi` reproduces these values. `gpu_loaded`: 18075.0 MiB free / 5973.0 MiB used, a 5737 MiB used-delta consistent with the 5732 MiB process row.
- `lock`: `{"contender_refused": true, "dev": 66306, "ino": 56251186}`; that dev/ino is the on-disk `/home/dowling/r1_locks/gpu0.lock`.
- `model` = `qwen25_coder_7b`; `offload.full` = `true`, `offloaded_layers` = 29, `total_layers` = 29, `route` = `log_line`, `cpu_fallback_lines` = `[]`, `reasons` = `[]`. The server log independently contains `load_tensors: offloaded 29/29 layers to GPU`, CUDA0 model buffer 4168.09 MiB, KV 952.00 MiB, `model loaded`, `listening on http://127.0.0.1:54653`, and `cleaning up before exit`; there is no inference request.
- Pinned identity/footprint: `gpu_uuid` = `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; `footprint_mib` = 5734, equal to the anchor's Stage A PASS-row qualification; the recorded row is 5732 MiB (2 MiB below the pinned footprint) and is accepted via the log-line route. `head` = `4b312844962e1106db04d5a60bf996fad0e3e514`; `lease_fd` = 4; `server_pid` = 3727607 with `server_start_ticks` 363003603. Final line is `PREFLIGHT_PASS`.

## 4. Post-run state — PASS

- No `llama-server` or `exam_runner` process remains (`pgrep -x` empty; `ps` match empty); `nvidia-smi --query-compute-apps` is empty; GPU is idle at 236/23812 MiB, 0%; port 54653 is not listening; `/proc/3727607` is absent.
- The lease is free: non-blocking `flock` probe returned 0, inode 56251186 unchanged, 0 B, mtime 2026-10-26.
- Owned server exited: `llama_server_54653.json` (2439 B, SHA `8dfdd59065d28ba8b23bc3d39add84dc1cf8154c2c7eb20b588b19a9bdc216e0`) records `stopped_utc 2026-11-12T20:28:18Z`, `returncode 0`, build `version: 0.7.0-dev (build 1, commit 620d222)`, the anchor model SHA, `pgid` = 3727607. `llama_server_54653.log` (16245 B, SHA `76f2068e5316f27f2482002006f64a8c903d364b68214f02a4b6b90007c054d8`, 207 lines) ends with cleanup/memory-breakdown, not a kill.
- `_to_delete/` retains two prior `server_record.*.json` versions (2379 B and 2300 B, 0600), both for PID 3727607, with the final record at the normal path; nothing was deleted.
- CAP is 0700 `dowling:dowling` with 0600 files; OUT is 0700 `dowling:dowling` with 0600 files and is a direct child of the configured `work_dir`; CACHE `/home/dowling/r1_b1_engineering/b1_final_gate_pycache_4b31_20261112_a` is absent.
- The run-HEAD staged checkout is detached at `4b312844962e1106db04d5a60bf996fad0e3e514` (tree `760cf663470026691bb8b7036a7195a271c1a864`), with zero lines from `git status --porcelain --untracked-files=all` and zero with `--ignored`. The harness is clean at `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`. The `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` and `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa` staged checkouts are clean at their own HEADs.
- The `_b` scene is untouched: `b1_fffa_20261111_b` and `b1_handover_fffa_20261111_b` retain mtimes 2026-11-11 05:51; the `_b` marker `/home/dowling/r1_locks/trackx_evidence.active` is still 82 B, SHA `23fa767be7346809d087d0a2352241e6042abdd04df2f198e476b8f39eab4c9a`, mtime 2026-11-11 03:01:56 PT, content `{"head": "fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa", "run_id": "fffa_20261111_b"}`.
- A full-home `find -newermt 12:24:30 ! -newermt 12:29:00` returned 13 entries: the 11 CAP/OUT files/dirs, plus the `r1_b1_engineering` parent (12:25:15) and `exam-x/work` parent (12:28:17) mtimes caused by creating CAP/OUT. No checkout, harness, model, Stage A table, older output or marker content was written.

## 5. Usability — PASS (precondition, not authority)

This is a genuine author-gate PASS and native-preflight PASS for exactly `4b312844962e1106db04d5a60bf996fad0e3e514`, against the reviewed rule, clean staged checkout and pinned harness. It is usable as a precondition for the `_c` O2 handover and launch, not as launch authority.

## Residual limits (non-blocking)

- R-1 Point-in-time: GPU/process/lock state is verified only at 2026-11-12 ~12:32 PT; a fresh census/no-preemption is still required at launch.
- R-2 No SSH keepalive: the transport sets only `ConnectTimeout=12`; completion rests on `ssh.exit` 0 plus the complete logs, both present. A future dropped session remains STOP.
- R-3 Marker still `_b`: the active marker names `fffa_20261111_b`; its retirement/replacement belongs to the later O2 handover, not this result.
- R-4 Post-run git metadata: the run checkout's `.git` directory mtime is 12:29:13 PT (about 54 s after `ssh.exit`), with no file inside `.git` newer than 12:28:19 and with HEAD (12:17:04), index (12:17:36) and refs unchanged; this is consistent with a transient index lock from a later read-only inspection, not a content write by the reviewed body. The 6835/fffa `.git` directory mtimes (12:31:21) likewise reflect later inspection; their index/HEAD mtimes precede the run. No tracked content, HEAD or ref changed.
- R-5 Offload route: acceptance uses the `offloaded 29/29` log line with no CPU-fallback line; the 5732 MiB row is 2 MiB below the pinned 5734 MiB footprint, so the log-line route is the accepting evidence.
- R-6 `_to_delete` naming is the record-retention area, not an outstanding deletion task.
- R-7 The transport's own rc is not stored; `ssh.exit` is the authoritative local record, and the capture stores remote hashes rather than copies of the logs (confirmed by re-hashing the live files).

VERDICT: accepted
