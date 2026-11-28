# G.5 P11 engineering matrix — rerun on the repaired code

Task `compute/20261128-10` (reissue of `compute/20261128-09`), PLAN **R1-G5-P11**. Base `origin/main`
`f7dc4945f63e09d1a7b66207bbbc43f76997aa29` (repair `2f110e26` merged; review `fd3099ed` accepted).
ENGINEERING_ONLY: no G.5 label or evidence run, no sealed/test read, no note created.

**Result: the P11 engineering matrix now runs every scenario on the repaired code.** The primary matrix and the
C9/C15 pre-run seal path PASS; both nodes complete two campaign waves and all planned audit chunks; diagnostics
report no STOP; `baseline_failed = 0`; the TASL-7 audit chunk is claimed, run, registered and sealed on TASL-2;
the meter reads 0.885 worker GPU-h and 0.839 proposer GPU-h. The C14 `-infra` scenario records the expected STOP 7.
The four scenarios blocked on 28 Nov 05:10Z by another user's compute on the TASL-7 card — `-determinism`,
`-restart`, `-tar` and `-closeserver` — were run on the free TASL-7 card at 08:35–10:08Z and PASS their items:
C2/C4/C5 repeat, C7/C10 controlled restart, C15 tar failure and C15 close-server. The earlier refusal is kept in
`tasl7/g5-p11-20261128T033600Z-determinism.serve.log` as the record of that attempt. This record is now offered
for one fresh review of the complete item table; it is still ENGINEERING_ONLY.

## Environment and pins

| Host | Role | GPU | Driver | State at start |
|---|---|---|---|---|
| TASL-2 | worker / campaigns / audits / seals | RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` | 535.309.01 | empty card, CPUs 0-7 free; all CPU locks free |
| TASL-7 | proposer server and one audit chunk | RTX 4090 `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` | 580.178.04 | empty card, GPU lease free at the primary start |

- Clean checkout of `f7dc4945` in `~/r1_engineering/g5-p11/repo` on both hosts; `git status --porcelain` empty.
  Harness `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` in `~/r1_tracks/t1_tasl/harness_g5` on both hosts.
- `G5_TASL_ENABLE_REAL` unset for every command. Python 3.11.17 (orchestrator) and the pinned `torch312`
  environment 3.12.16 for the isolated worker.
- One shared UTC stamp `20261128T033600Z`; every scenario has its own spec and run tree. The primary spec is
  `g5-p11-20261128T033600Z-lease.json`, sha256
  `f5365e84ae6147c3a24e0f8169332286fae0ed6a192826ce459a282c3c2eddc5` on both hosts (byte-identical `p11-init`).
  `validate --launch --engineering` passed on both hosts.

## Primary `-lease` scenario

### Setup and server

`p11-init` produced byte-identical specs on TASL-2 and TASL-7. TASL-7 started the engineering server at
`2026-11-28T03:31:00Z`; `server_record.json` sha256
`27174cf70d6bf3215c2258430f166aee26a9867761ff0cc8ffe457731f2adb72`; server PID 2586631, wrapper PID 2586581.
`p11-probe` from TASL-2 passed: `/props` context 32,768, one slot, build `b1-620d222`, model
`google_gemma-4-31B-it-Q4_K_M.gguf`; health median 29.15 ms, p95 47.68 ms; one completion 0.202 s. The record
was copied byte-for-byte to TASL-2 `incoming/.../server-1.json` (same sha256).

After the C11 chunk, the primary server was restarted: `server-2` record sha256
`5a4e34eec084a510200c348405dd2e35baa3cfbd5495a9f3d1e835937f50389e`, PID 2595232, wrapper 2595178, started
`2026-11-28T03:55:39Z`; `p11-probe` passed again (health median 30.78 ms, p95 35.96 ms).

### Campaigns

| Node | Wave | Attempt | STOP | Proposals | Ran | Kept | Baseline failures | GPU-s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `mlab_imdb` | 1 | 1 | none | 80 | 40 | 40 | 0 | 74.0 |
| `mlgym_breakout_minatar` | 1 | 1 | none | 80 | 40 | 40 | 0 | 73.9 |
| `mlab_imdb` | 2 | 1 | none | 160 | 80 | 80 | 0 | 144.8 |
| `mlgym_breakout_minatar` | 2 | 1 | none | 160 | 80 | 80 | 0 | 144.2 |

Every wave's `diagnostics.json` has `stop: null`, `ledger_stops.baseline_failed: 0`, `invalid: 0`,
`infrastructure_final: 0`, `refused: 0`, `timed_out: 0`. The repaired synthetic parent writes the `step` line to
the run log and the two scores to the isolated channel; the pinned harness now reaches its budget.

### Audits and C2/C4/C5

The first audit call for each node wrote the wave plan; every later call ran the next chunk. `mlab_imdb` and
`mlgym_breakout_minatar` each have 3 wave-1 chunks and 2 wave-2 chunks.

| Node | Wave | Chunk | Kind | Planned runs | Label seeds ok | STOP | GPU-s |
|---|---|---|---:|---:|---:|---|---:|
| `mlab_imdb` | 1 | 0 | middle | 200 | 100 | none | 328.0 |
| `mlab_imdb` | 1 | 1 | middle (TASL-7) | 200 | 100 | none | 431.0 |
| `mlab_imdb` | 1 | 2 | final / E5 | 10 | 5 | none | 17.0 |
| `mlab_imdb` | 2 | 0 | middle | 200 | 100 | none | 324.5 |
| `mlab_imdb` | 2 | 1 | final / E5 | 200 | 100 | none | 327.3 |
| `mlgym_breakout_minatar` | 1 | 0 | middle | 200 | 100 | none | 325.0 |
| `mlgym_breakout_minatar` | 1 | 1 | middle | 200 | 100 | none | 328.0 |
| `mlgym_breakout_minatar` | 1 | 2 | final / E5 | 10 | 5 | none | 16.7 |
| `mlgym_breakout_minatar` | 2 | 0 | middle | 200 | 100 | none | 325.0 |
| `mlgym_breakout_minatar` | 2 | 1 | final / E5 | 200 | 100 | none | 325.8 |

Each chunk's `diagnostics.json` reports the plan hash, K = 10, the planned label/evaluation seed blocks, and
`stop: null`. `wave-checks` returned `stops: []` and `warnings: []` for both nodes in both waves. The attempt
archives contain the checked unit hashes, the re-materialization count and per-run isolation receipts; only
named JSON/JSONL members were inspected.

C5 uses the two census times and the actual run count: `started + 1800 + ceil(n * run_seconds * 1.5 * 1.25)`.

| Node | Wave | Chunk | n | started | formula deadline | recorded deadline |
|---|---|---:|---:|---|---|---|
| `mlab_imdb` | 1 | 0 | 200 | 03:35:45Z | 10:46:39Z | 10:46:39Z |
| `mlab_imdb` | 1 | 1 | 200 | 03:47:03Z | 10:57:57Z | 10:57:57Z |
| `mlab_imdb` | 1 | 2 | 10 | 03:56:45Z | 04:46:48Z | 04:46:48Z |
| `mlab_imdb` | 2 | 0 | 200 | 04:08:06Z | 11:19:00Z | 11:19:00Z |
| `mlab_imdb` | 2 | 1 | 200 | 04:13:31Z | 11:24:25Z | 11:24:25Z |
| `mlgym_breakout_minatar` | 1 | 0 | 200 | 03:41:19Z | 10:34:07Z | 10:34:07Z |
| `mlgym_breakout_minatar` | 1 | 1 | 200 | 03:57:07Z | 10:49:55Z | 10:49:55Z |
| `mlgym_breakout_minatar` | 1 | 2 | 10 | 04:02:40Z | 04:51:49Z | 04:51:49Z |
| `mlgym_breakout_minatar` | 2 | 0 | 200 | 04:19:09Z | 11:11:57Z | 11:11:57Z |
| `mlgym_breakout_minatar` | 2 | 1 | 200 | 04:24:44Z | 11:17:32Z | 11:17:32Z |

All ten columns match to the second; the remaining sub-second difference is the fractional start time not
carried in `started_utc`.

### C11 and C16 — TASL-7 chunk, mutual lease refusal

At `03:47:03Z` the claim for `mlab_imdb` wave 1 chunk 1 was written on TASL-2 (sha256
`13f0d5062280a7b452b1a26ebb51c9b0b46afb4546ac9ed568cd37a3bc571c28`); the claim, plan index and plan tar were
copied byte-for-byte to TASL-7 (hashes `13f0d506…`, `f097bdc0…`, `83cf1142…`).

- With the primary server holding `gpu0.lock`, the TASL-7 chunk command stopped at
  `STOP: the GPU lease /home/dowling/r1_locks/gpu0.lock is held by another job (no shared card)` (node log
  `mlab_imdb-20261128T034638Z-2589052.node.log`).
- The primary server was stopped and sealed; the chunk ran with the server down. The audit engine wrote
  `lease-ready`, then the second `g5 serve` attempt also stopped at the same lease refusal
  (`…033600Z.serve_during_chunk1.log`). `lease-continue` released the audit.
- The completed attempt was copied to TASL-2 `incoming/…/attempt-1`, registered and sealed:
  registration sha256 `47807f81cd1a508bc7fc8c77adc287f05492114c83cc69d49c057a9e1fccb0a8`; registration has the same cross-host PASS record as the claim
  (`G1B_XC3_SHORT_VERDICT_mlab_imdb_20261125.json`, `9cce9064…`); `finalize-remote` registered one attempt;
  `seal-attempt` wrote the attempt receipt and `out.tar` sha256 `33a47644…`.
- The resulting job record names the live TASL-7 RTX 4090, driver 580.178.04, the paper commit, both environment
  freezes and the delegated CPU set 0-7. This is the C16 end-to-end check.

### C6/C9/C15 — seal path, closed attempt, servers

- `seal-attempt` was run on every primary attempt (campaigns and audits, both waves); all returned rc 0 with no
  STOP. `seal-node` ended both nodes at "wave 2 checked"; `seal-run` copied the access log, K lock, refusals,
  logs and remote final; `p11-table-marker` wrote the release-negative-control marker.
- The `-closed` scenario prepared an interrupted attempt on TASL-2, ran `close-attempt`
  (`rc 0`, `STOP: closed without a job record: P11 synthetic interrupted attempt`, class `infrastructure`),
  captured the disk check, and sealed the attempt. The seal recorded `out_clear.tar` and the closed job record.
- `seal-server` sealed server-1 (span 949 s) and server-2 (span 2071 s); the receipts were copied to TASL-2 and
  `server-span` accepted both. The meter then read proposer 3020.0 s (2 registered, 0 open) and worker
  0.885 GPU-h.
- The C15 release negative control `python -m r1.c3.release --stage traindev --source g5 --table … --audit …
  --out …` exited non-zero at the P11 engineering refusal before opening evidence; the exact text is in
  `tasl2/…release_refusal.log`.

### C14 — `-infra` STOP 7

The `-infra` scenario ran its own server and an IMDb wave-1 campaign, then the first audit chunk. The audit
recorded one infrastructure row (seed 7001, through all retries) and stopped with
`STOP 7: final infrastructure failures in the audit chunk after the engine's reruns (a new attempt after
diagnosis)`; class `infrastructure`; 99 ok, 1 infrastructure. The attempt and server were sealed. This is the
expected STOP 7, not a host failure.

## Separate scenarios (28 Nov 08:35–10:08Z, TASL-7 card free)

All four use the same base `f7dc4945`, the same harness and the reviewed G.5 code; `G5_TASL_ENABLE_REAL` is unset.
The TASL-7 card had no foreign compute at any scenario start (checked each time; TASL-2's GPU was empty after the
P7 server stopped). Every server used the declared `-c 32768` q8_0 K/V argv and one slot.

### `-determinism` (C2/C4/C5 repeat) — PASS

Spec `g5-p11-20261128T033600Z-determinism` sha256
`1cc9f4d4e91fec02d7ef1ad257ee20065180babeb491217201e55c016cc865dc`.

- Server: PID 2748828, started 08:35:26Z, stopped 09:57:20Z, span **4,914 s**; `/props` 32,768 context, one slot.
- Campaigns: `mlab_imdb` and `mlgym_breakout_minatar`, wave 1, each 80 proposals, 40 ran, 40 kept, 0 invalid,
  0 infrastructure, 0 refused, 0 timed out, `stop: null`.
- Audits: three chunks each. `label_seed_runs` for chunks 0 and 1: 100 ok, 0 divergent, 0 infrastructure; final
  chunks 2: 5 ok, 0 divergent, 0 infrastructure. All `stop: null`.
- Fixed-seed repeat: each chunk's archive carries `out/audit/determinism.json` with
  `same_fixed_seed_outcomes` **200** (chunks 0, 1) and **10** (final chunk 2), and
  `out/audit-repeat/chunk_record.json` with `expected_runs 200`, `diffs_recounted 0`, `infrastructure_reruns 2`,
  `gate: noise_floor.check_effective ... effective:true`. The six repeat records agree.
- `wave-checks`: `stops: []`, `warnings: []` for both nodes.
- Seals: eight attempt receipts (two campaigns, six chunks), all rc 0. The server seal is
  `cd71834e…` record / `16f51e8d…` end / `c21576c6…` log; `server-span` rc 0.
- Meter: worker **0.791 GPU-h**, proposer 4,914 s (1 registered, 0 open, no gaps).

Node/run seals are not claimed for this scenario: `seal-node` correctly refuses a node that has no wave-2 checks
or node STOP, and the scenario deliberately runs wave 1 only. The primary `-lease` scenario covers node/run seals;
the determinism evidence is the six chunk repeat receipts.

### `-restart` (C7/C10) — PASS

Spec `g5-p11-20261128T033600Z-restart` sha256
`71571e3796d307c632d1afb20656faa8f81097146f13d5f01e690d32bc89ac18`.

- Server-1: PID 2758307 (record `8b768b1d…`), 09:58:06Z–09:58:39Z, span **33 s**; `p11-probe` PASS
  (32,768 context, one slot, build `b1-620d222`). The server was stopped at 09:58:39Z.
- `mlab_imdb` wave-1 campaign: `restart-ready` at **09:59:11Z**; with the server down `restart-continue` was
  written at **10:01:29Z**; the wrapper recorded
  `STOP 12: after the wave: <urlopen error [Errno 111] Connection refused> (re-run as a new attempt)` at
  **10:02:40Z**, class `infrastructure`.
- Server-2: restarted 10:02:19Z–10:02:46Z, span **27 s**, record `e8ed4127…`; `p11-probe` PASS again.
- The failed campaign attempt is sealed (`d38acd55…` job record, `49321120…` diagnostics, `d694b9d5…` out.tar);
  `server-span` accepted both server receipts. Meter: worker 0.059 GPU-h, proposer **60 s** (2 registered,
  0 open, no gaps).

The primary record's two clean starts and its stop/restart around the C11 chunk remain the C10 short-span
evidence; this scenario adds the controlled `restart-ready` → STOP 12 path. The hours-long part of C10 remains a
STOP 12 while the table runs, as R1-G5-P11 states.

### `-tar` (C15 tar failure) — PASS

Spec `g5-p11-20261128T033600Z-tar` sha256
`fed68f4c8b98cb6a1601c1fdf1496770d6c7cc2522d18ff43111d7ee1450a303`.

- The engine's `-tar` fixture left `out.tar` as a directory, so the real `tar -cf out.tar out` failed. The job
  recorded `STOP: out.tar could not be written; out/ kept for the seal`, class `infrastructure`, and kept the
  clear `out/` tree.
- `seal-attempt` sealed it as `out_clear.tar` with **1,130** clear files; archive sha256
  `07c6a35dffae71c5c27780c36115b6e4ae43affb17289e59531fca002ce187d9`; the seal receipt records
  `out_clear_files: 1130`, the job-record hash and the node log. The capture carries the archive listing, not
  the archive itself.
- Server: record `a94246b6…`, 10:03:49Z–10:05:35Z, span **106 s**; `p11-probe` PASS. Meter: worker 0.021 GPU-h,
  proposer 106 s (1 registered, 0 open).

### `-closeserver` (C15 close-server) — PASS

Spec `g5-p11-20261128T033600Z-closeserver` sha256
`324db598fa00e18e9ef2c6cbbe0a7a0ff4f6f814e10dfed46f48c663dfe8920f`.

- Server-1 (record `4154b044…`) had a normal end (21 s span) and was sealed by `seal-server`; it is the ordinary
  path, not the interruption.
- Server-2 (record `967801cc…`) was started 10:06:47Z, probed, then the wrapper and child were killed with
  `SIGKILL` before the wrapper could write an end record. `close-server` wrote a receipt with `closed: true`,
  `end_basis: closed_at`, reason `P11 engineering server interruption`, `stopped_utc` 10:07:07Z; `seal-server`
  then sealed it with span **20 s**. Both `server_end.json` and the seal receipt are in the capture.
- Meter: worker 0.0 GPU-h, proposer **41 s** (2 registered, 0 open, no gaps). The lease was free before
  `close-server`; `gpu0.lock` is free after it.


## Coverage against C1–C16

| Item | This run | Status |
|---|---|---|
| C2 | Both nodes, campaign + 3 audit chunks each, K = 10, re-materialization and isolation receipts; the `-determinism` scenario repeats the same fixed-seed claims: 200/200/10 same outcomes, 0 diffs, six repeat records agree | PASS |
| C4 | Per-wave and per-chunk diagnostics for both nodes | PASS |
| C5 | Ten primary chunk deadlines reproduce the declared formula; the `-determinism` chunks 0–2 also record the formula | PASS |
| C6 | Attempt, node, run and server seals; access log; closed attempt; the `-tar` seal writes `out_clear.tar` | PASS |
| C7 | Two primary server starts, probes and a stop/restart around the C11 chunk; the `-restart` scenario adds `restart-ready` → server down → STOP 12 → server-2 probe | PASS |
| C9 | Meter at W = 20, MEM A, K = 10, closed attempt; 425 GPU-h threshold | PASS |
| C10 | 3020 s primary proposer span with one restart; the `-restart` short span with both server identities and the interruption record; the hours-long/multi-day part remains STOP 12 while the table runs (R1-G5-P11) | PARTIAL (multi-day STOP 12) |
| C11 | Server-holds-lease and chunk-holds-lease mutual refusals | PASS |
| C14 | Real-engine harness, isolated worker, STOP 7 injection | PASS |
| C15 | `seal-attempt`/`seal-node`/`seal-run`, `seal-server`, `server-span`, noise pre-check; `-tar` `out_clear.tar` (1,130 files) and `-closeserver` abnormal end; assembly/release need the signed note | PASS (assembly/release not yet) |
| C16 | One full TASL-7 chunk claimed, run, registered and sealed on TASL-2 | PASS |

## Hashes that matter (new scenarios)

| Item | SHA-256 |
|---|---|
| `-determinism` server record / end / log | `cd71834e…` / `16f51e8d…` / `c21576c6…` |
| `-determinism` server span | 4,914 s; meter worker 0.791 GPU-h |
| `-restart` server-1 record / server-2 record | `8b768b1d…` / `e8ed4127…` |
| `-restart` campaign job record / diagnostics / out.tar | `d38acd55…` / `49321120…` / `d694b9d5…` |
| `-tar` `out_clear.tar` | `07c6a35dffae71c5c27780c36115b6e4ae43affb17289e59531fca002ce187d9` (1,130 files) |
| `-tar` server record / span | `a94246b6…` / 106 s |
| `-closeserver` server-1 / server-2 records | `4154b044…` / `967801cc…` |
| `-closeserver` server-2 end / seal | `bed5f477…` / closed true, 20 s |

## Files

`tasl2/` and `tasl7/` mirror the engineering roots; `SHA256SUMS` binds this record set. The attempt `out.tar`
archives stay on the hosts and are cited by their seal-receipt hashes; the record set carries the named JSON,
JSONL and log members only. The `-determinism` repeat members are extracted from the sealed `out.tar` as
`out/audit/determinism.json` and `out/audit-repeat/chunk_record.json`; the `-tar` member is the archive listing
and its sha256, not the archive.

## What happens next

One fresh review of the complete P11 item table. After acceptance, G.5 publication still waits on the local
render and the remaining note checks. No label, test or evaluation value was read; no tolerance, note, seed,
spec or request was changed. The four new scenarios ran on the free TASL-7 card; the earlier refusal record is
kept, not overwritten.

**Decided alone:** host placement (TASL-2 worker, TASL-7 proposer), the shared stamp and fresh IDs, stopping the
server for the C11 chunk, the `restart-ready`/`restart-continue` timing, killing the close-server wrapper and
child with `SIGKILL`, and stopping each scenario's server after its last job. No signed value was changed.
