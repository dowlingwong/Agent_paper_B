# G.5 P11 host run — TASL-7 proposer (`C7`, `C10` short, `C11`; T1 plan §6 items 6–7)

**ENGINEERING_ONLY.** 27 November 2026, 01:25–01:30 UTC, by the compute agent (DeepSeek). No G.5 label run, no
evidence row, no sealed attempt, no label or evaluation read, no `main` push. Task
`compute/20261127-05` with `compute/20261127-08`; base `origin/main` `5c901d19`. This record is a capture set for
the P11 host-test table; it does not replace the signed G.5 note.

The G.5 code paths that require a signed note (the literal `t1_tasl_node.sh g5` switch and the real engine) were
**not** run and must not be fabricated. This run exercises the host-side conditions the T1 plan §6 names: the
resident GGUF server on TASL-7, its identity on both starts, the Tailscale listener, and the lease refusal.

## 1. Environment

| Field | Value |
|---|---|
| Host | TASL-7, `tasl-7.tail119748.ts.net`, uid `dowling` |
| Code | clean clone of `https://github.com/dowlingwong/Agent_paper_B.git` at `5c901d19e682dbd50556054b2ebfb9e8f2c50ea1` |
| Python | `/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python` (Python 3.12.16) |
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 580.178.04, UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; `foreign_before` empty in both server records and the after capture shows 44 MiB used (`nvidia_smi_after.txt`) |
| Binary | `/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server`, sha256 `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`; `version: 0.7.0-dev (build 1, commit 620d222)` |
| Build manifest | sha256 `a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170`; `ldd` has no llama library outside the build directory |
| Model | `google_gemma-4-31B-it-Q4_K_M.gguf`, 19,598,489,952 B, sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` |
| Server argv | `-c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --no-webui --host tasl-7.tail119748.ts.net --port 8095` |
| Lease | `/home/dowling/r1_locks/gpu0.lock` held by the server for its life; free before and after |
| Engineering root | `/home/dowling/r1_engineering/p11_hosttest_20261127/`; server dirs under `/home/dowling/r1_tracks/t1_tasl/proposer_g5/g5-p11-hosttest-20261127/server-{1,2}` |
| Spec copy | `g5_tasl_spec.json` at `5c901d19` with only `run_id` set to `g5-p11-hosttest-20261127`; sha256 `2302bd182d90013c37966b940998a8ae1001dd3c2059a387f1d6002c378b3bad`. It is not a launch-valid spec (the note and the remaining PENDING fields are not filled) and was used only to drive `g4_tasl.serve_spec`. |

## 2. Result

| Item | Result | Evidence |
|---|---|---|
| T1 plan §6 item 6 — server, context 32,768 in 24 GB, q8_0 KV, `/props` | **PASS for the declared server configuration** | The server started twice with the declared argv (`-ngl 999`, `-c 32768`, q8_0 K/V); `/props` `default_generation_settings.n_ctx` = 32,768, `total_slots` 1, `build_info` `b1-620d222`, GGUF file name as declared. GPU memory used during the run was observed but not captured; the after capture shows 44 MiB used and no compute app. |
| T1 plan §6 item 7 — Tailscale reachability, latency, bind to the Tailscale address only | **PASS** | From TASL-2, five `/health` probes: 0.126, 0.033, 0.029, 0.032, 0.032 s; `/props` returned the same identity. From TASL-7, `127.0.0.1:8095` was refused (curl rc 7), so the listener is on the Tailscale address, not localhost. |
| C7 — server stop/restart with identity re-checked | **PASS for the restart and identity**, not for an audit phase | Start 1 `01:25:10Z`, `SIGTERM` at `01:27:26Z`, server rc 0, clean `server_end.json`; start 2 `01:27:44Z` (the recorded server process start, not the `serve` invocation 14 s earlier), stopped `01:30:09Z`, rc 0. Both starts have the same identity fields (`build_info`, `total_slots`, `n_ctx`, model file name) and both `server_record`/`server_end` pairs bind their log and record. No G.5 audit chunk ran on TASL-7, so the "around audit phases" part is not exercised. |
| C10 — proposer link short span | **PARTIAL** | Two clean server spans of 2 min 16 s and 2 min 25 s over Tailscale, not the "hours" short span; the multi-day span and a restart handled as an infrastructure STOP remain for the table. |
| C11 — lease: a running server keeps a second G.5 job out | **PARTIAL** | While the server held `gpu0.lock`, `flock -n /home/dowling/r1_locks/gpu0.lock` returned rc 1; after the stop it returned 0. The audit-chunk side (the chunk's own lease refusal) was not run because the G.5 switch requires the signed note. |

## 3. What was not run, and why

- **C2, C14, C9 (real audit runner / real engine / GPU-hour meter).** The literal `t1_tasl_node.sh g5` path calls
  `g5_tasl.py`, whose first gate requires a `g5_tasl_labels/v1` spec and a signed note. The spec on `main` is
  `label: EVIDENCE` with `PENDING` fields; there is no signed G.5 note. Fabricating one is forbidden, so the real
  engine was not started. This is the same fail-closed refusal the 23 Nov engine smoke recorded.
- **C4, C5 (per-wave diagnostics, K = 10 audit-chunk deadlines).** These need a real smoke campaign/audit chunk, not
  the host server. The 23 Nov fake-engine smoke covers the job-side diagnostics mechanism at an older code; the
  current-code run waits for a signed note or a synthetic engine setup.
- **C6, C15 (seal paths).** The `g5_tasl.py seal-*` commands call `validate_spec(launch=True)` before sealing, which
  refuses the unsigned spec. The 23 Nov smoke exercised the seal/assembly mechanism at `76a3c71f`; the current-code
  seal run waits for the same gate or a purpose-built synthetic spec.
- **C16.** Needs the first TASL-7 G.5 audit chunk after the note.

## 4. Hashes of this capture set

| File | sha256 |
|---|---|
| `server_record_start.json` | `e9593d7b2c476fba58613ec98aed05065db4b62838b91d5e42c523ab2aa07ec6` |
| `server_end_start.json` | `db624b4869cf5a65cfd6107e1e1a8051f99d0ff811ccb4ab198dafd8b81e9805` |
| `server_log_start.txt` | `eeda4c41d2428d1d6c9e25544cd930c1e2326c76c3c9a34e101c9281711953b3` (matches `server_end_start.json`) |
| `server_record_restart.json` | `900a837d692ea8f04ce395120e83245ed9d0bdef6227e4b0c66db6cb539a5c66` |
| `server_end_restart.json` | `45f7f3b8c6be2e5df279765918880e4290530a9511267282939b742c3132a6f8` |
| `server_log_restart.txt` | `f81e90e1220336ae0eefc569a46b6cd5dbb7dd24f529ece89bd719f693885989` (matches `server_end_restart.json`) |
| `props_start.json` | `2e01392a88ac80a224c43373c11aae8f4c032bb01531f93943ead0cce46c7eed` |
| `props_restart.json` | `152a071fac02f4444a4abf651fb4dbb6d69effd561a466399699861e71706937` |
| `health_latency.txt` | `e1c49ea2f4bf2c8315280c542fb3d41abb0e755016896b210670cc7865506d5b` |
| `nvidia_smi_after.txt` | `86a9cbca9bef0126dad28b3f655519b43b220f6a71d3815d69b64897a6193307` |

## 5. What happens next

The remaining P11 items (C2, C4, C5, C6, C9, the hours part of C10, the audit-chunk side of C11, C14, the pre-run
seal parts of C15, C16) need either the signed G.5 note or a purpose-built synthetic smoke spec that the G.5 switch
accepts. The coordinator should name which route it wants; no note was created. The TASL-7 card is free and the
lease is released.
