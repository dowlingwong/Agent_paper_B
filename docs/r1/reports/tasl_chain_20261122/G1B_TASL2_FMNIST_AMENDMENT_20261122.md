# G.1b amendment run — `mlgym_fmnist` on TASL-2, run `g1b-tasl-20261121-b` — step 2 of the 22 Nov TASL chain — PASS (22 November 2026)

**Result: PASS.** The authorized G.1b amendment (`mlgym_fmnist` on TASL-2, signed note
`g1b_t1_tasl_20261122.md`) ran inside the wrapper's delegated user scope as **attempt-3** of the node, wrote
**460/460/460** runs with **0 divergent**, passed the determinism gate, met the harness-isolation gate on every row
(`effective: true`, `waivers {}`, `exceptions []`), and was **sealed** (`SEAL_RECEIPT.json`, rc 0). **No author STOP
occurred** — no node, timing, lease, foreign-GPU, harness, environment, data-manifest or cap STOP. ENGINEERING_ONLY;
no label, evaluation or sweep-2 file was read. AI-assisted (DeepSeek Harness agent `fmnist-amendment-runner`,
delegated by the lead).

Written uncommitted on the Mac ops worktree `ops-tasl-20261116` (baseline `3a5d388e`); the lead commits the memo and
this record. Nothing was committed or pushed; nothing was deleted; TASL-7, the G.4 pilot and the autoresearch AR job
were not touched.

## 1. Authority and inputs (all verified before any job)

- Published `main` for this delivery is `9f23fea8d7a3e14d0133d20c8b0f1702144fa409` (task input). During
  preparation and the run window the release track published docs/release-only advances on `main`
  (`9f23fea8` → `dc9ad88a` → `1402f466`, §6; the non-`docs/` diff is empty); the note, the two host-check records,
  the erratum record, the spec and the six PLAN authority rows the launch requires are identical at every one of
  those states, and `34a5b1d6` stays an ancestor (`PLAN.md` gained seven unrelated authority rows). The advance is
  therefore legitimate under `verify_launch_tasl` ("main may move on after the signature") and is disclosed, not
  hidden.
- Note: `docs/r1/authorizations/g1b_t1_tasl_20261122.md`, sha256
  `cea32f751c140b6b9a408122af3198f0d3fa6b51463be9bce237d59e9a101ce0`, byte-identical on `origin/main`
  (`approved: true`, `label: ENGINEERING_ONLY`, `labels_read: none`); binds `run_id: g1b-tasl-20261121-b`,
  `paper_commit: 3c3f822aaa839958a8754ffdcfa09a51e7699107`,
  `spec_sha256: 7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7`,
  `harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702`; P1–P6 `PASS`, P7 `PENDING` (so `launch` refuses a
  TASL-7 node — verified negatively, §1).
- Launch commit **`34a5b1d66c51e0a210939d9d58b35dba0bc0ffe2`**, whose parent is the paper commit `3c3f822a`; the
  diff `3c3f822a..34a5b1d6` outside `docs/` is exactly `sweep2/t1_tasl/g1b_tasl_spec.json` (1 file, +3/−3): the
  code, kits, envs and tests are the paper commit's. `34a5b1d6` is an ancestor of `origin/main`.
- Spec `sweep2/t1_tasl/g1b_tasl_spec.json` sha256
  `7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7` (validated, §1 below; cap projection within
  100 GPU-h; `mlgym_fmnist` projection 4.642 GPU-h).
- Host-check records on `origin/main` with the spec's declared sha256: TASL-2
  `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md` sha256 `681011b2…`; TASL-7
  `…/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md` sha256 `09945c15…`. P4's erratum record
  `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md` sha256 `9b40944b…` is on `main`
  byte-identically (verified; `publication-check` had passed before signature).
- Per-run checkout: **`/home/dowling/r1_tracks/t1_tasl/paper_fmnist`** (new, separate; the old checkouts are
  untouched), cloned from `origin`, detached at `34a5b1d6`, `origin/main` freshly fetched, tracked tree clean
  (only the untracked signed note under `docs/r1/authorizations/`), the signed note copied byte-identically from
  `origin/main`. `origin/main` at launch preparation: `dc9ad88a64d0430b481661fd78f7bbda4aed19fa`.
  Harness checkout `/home/dowling/r1_tracks/t1_tasl/harness` at `c025f89a…`, clean except the allowed
  `nodes/*/data` links (the wrapper's own check requires exactly this).
- **Gate results on TASL-2 before launch** (all captured in `…_captures/inputs/launch_gate.log`):
  - `g1b_tasl.py validate … --launch` **PASS** (`ok: true`, run id `g1b-tasl-20261121-b`, within cap);
  - `check_note` **PASS** (fields bind the note's `paper_commit`, `spec_sha256`, `run_id`, `harness_commit`;
    P1–P6 PASS; P2 cites the TASL-2 record, P3 the TASL-7 record; `host_row` R1-T1-TASL-ENV);
  - `check_host_record` **PASS** for both hosts with the declared sha256s (`681011b2…`, `09945c15…`);
  - `verify_launch_tasl` **BINDING_OK**: `paper_commit 3c3f822a`, `head 34a5b1d6`, `main dc9ad88a`, spec path;
    `origin` is the spec's paper repository and `ls-remote` equals the fetched `origin/main`; the launch spec is
    HEAD's committed file; the PLAN rows (`R1-T1-HOST-TASL`, `R1-TRACKG-G3-EARLY`, `R1-G1B-CAP`, `R1-G1B-EDITS`,
    `R1-G1B-TIMEOUT`, `R1-T1-TASL-ENV`) are on published `main`;
  - dry `launch` (binding + note + host records, runner stubbed) **PASS**; negative gate: a **TASL-7** node is
    **refused** (`STOP: a TASL-7 node needs P7 PASS citing R1-T1-TASL-ENV`) — the note's scope is TASL-2 only, as
    disclosed.
- **Pre-launch host conditions** (captured in `…_captures/inputs/prelaunch.txt`, 2026-11-22T21:10:02Z): TASL-2,
  GPU `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (RTX 4090, driver 535.309.01, 24564 MiB) **353 MiB used, 0 %,
  no compute app**; GPU lease `~/r1_locks/gpu0.lock` **free** (`flock -n` `LEASE_FREE`, no holder); disk **352 GiB
  free** (≥ 20 GiB); no G.1b/noise-floor/t1_tasl process of the user. The node's two earlier attempts
  (attempt-1/2, first note) ended `stop_class: infrastructure` (the census-manifest mismatch the amendment fixes),
  so `next_attempt` correctly opened **attempt-3**; complete old attempts of the three sealed nodes refuse a new
  attempt and were left alone (§5).

## 2. The job

Command (exactly as authorized, from the checkout, inside the wrapper's delegated scope):

```
G1B_TASL_ENABLE_REAL=1 bash /home/dowling/r1_tracks/t1_tasl/paper_fmnist/sweep2/t1_tasl/t1_tasl_node.sh \
     g1b <checkout>/sweep2/t1_tasl/g1b_tasl_spec.json mlgym_fmnist \
     <checkout>/docs/r1/authorizations/g1b_t1_tasl_20261122.md --enable
```

The wrapper (invoked by a small driver, `…_captures/inputs/driver.sh`, that fetches `origin/main`
immediately before the launch, records the exit code and runs the seal; its only permitted infrastructure retry was
never triggered) ran the node through
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, `taskset` on cpus **0-7**, with
`AR_TEST_CGROUP_PARENT` set to that scope; the job's own checks confirm `memory.max=8589934592`,
`memory.swap.max=0`, affinity `[0..7]`, Yama `ptrace_scope 1`, non-root uid 1008, harness at the pin and the
torch312 freeze equal to the census freeze (Python 3.12.16, 77 packages, freeze `d2e70fe4…`).

- **Attempt:** `attempt-3` (`attempt.json`: pid 474032, TASL-2, 2026-11-22T21:10:48Z), lease held by pid 474032.
- **Data manifest, corrected:** setup wrote `AR_DATA manifest_sha256=24cb3448…` (`runs/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/out/setup.log`), equal
  to the re-issued spec's `mlgym_fmnist.data_manifest_sha256`
  `24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32` (the census value `8d28287b…` was the
  erratum's `source.datasets` provenance value; the data arrays are byte-identical). This is exactly the STOP the
  first note's two attempts hit; under the amendment the check passes.
- **Parts** (all `rc 0`, `stop: null`, `stop_kind: null`):

| part | expected | written | successful | stop |
|---|---|---|---|---|
| default | 10 | 10 | 10 | null |
| train | 150 | 150 | 150 | null |
| split | 150 | 150 | 150 | null |
| joint | 150 | 150 | 150 | null |

- Timeout basis `census_slowest_x3` = 40.795 s, timeout 122.385 s; no run reached it (max wall per part 13.2 s).
  Node deadline 51 039 s (not approached).

## 3. Result at a glance

| | |
|---|---|
| Run window (UTC) | 2026-11-22T21:10:48Z → 22:41:26Z |
| Wall | **1 h 30 m 38 s = 5 438 s = 1.5106 h** |
| GPU-hours (lease, the whole job) | **1.5106 GPU-h** (projection 4.642; measured 4090/Ada ratio ≈ 0.33) |
| Runs | **460 expected / 460 written / 460 successful / 0 divergent** |
| Determinism gate | **passed** (`deterministic: true`, `divergent_configs_at_default: []`; every c0–c4 `default` equals its `default_repeat`) |
| Isolation gate | **460/460 rows** `isolation.effective: true`, `waivers {}`, `exceptions []`, `log_intact: true` (checked over every written row) |
| STOPs | **none** (`stop: null`, `stop_class: null`; no refusal, no timing STOP, no cap STOP) |
| 4090/Ada ratio (c0 median wall / census `run_seconds` 34.376) | default 0.3398 (11.681 s), train 0.3347 (11.506 s), split 0.3326 (11.434 s), joint 0.3274 (11.255 s) |
| Foreign-GPU checks | 9/9 empty (`before the job`, before/after each of the four parts) |
| Cap | this job 1.5106 GPU-h; G.1b on TASL-2 so far 5.5506 (first note's three sealed nodes + the two fmnist aborts) + 1.5106 = **7.0612 GPU-h ≤ 100** (R1-G1B-CAP) |

## 4. Seal

`g1b_tasl.py seal <attempt-3> <spec> --node mlgym_fmnist` (rc 0) copied the attempt to
`/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/` (no overwrite) and wrote
`SEAL_RECEIPT.json` binding the record and the wrapper log:

| file | sha256 |
|---|---|
| `SEAL_RECEIPT.json` | `8784aac72380457843abe9758ea462d679a4f0c79a01def0b2ab330e6eacc7ab` |
| `job_record.json` | `5476148acbbdd15d1afcf675c94b5b3cf03269af35673a5a3a6942d3ef4d55ef` |
| `SHA256SUMS` | `dc0687f55f325fd7d5e4e075fb3e9c258b8f28a6eab072c9a1bdb9999e91c912` |
| `node.log` | `981994bbc99ac7573b5663e062d855d6137894fd49770d3015621503eb71b5a2` |
| `out.tar` (not copied to the captures) | `a180c6e555e7806dc5ddfceb468c41a0a6b559733d4b86769a52385127e39756` |

Receipt: `schema g1b_tasl_seal_receipt/1`, `run_id g1b-tasl-20261121-b`, `node mlgym_fmnist`, `host TASL-2`,
`attempt 3`, `stop: null`, `stop_class: null`, `job_record_sha256 5476148a…`, `node_log_sha256 981994bb…`,
`sealed_utc 2026-11-22T22:41:26Z`. `sha256sum -c SHA256SUMS` passes **rc 0 in both the sealed directory and the
runs attempt directory**; the sealed copy is byte-identical to the runs-tree attempt (`…_captures/run/seal_verify.txt`).
The job record: `spec_sha256 7ff3c95b…`, `harness_commit c025f89a…`, `label ENGINEERING_ONLY`, runs
`{expected 460, written 460, successful 460, divergent 0}`, GPU identity `RTX 4090 / GPU-4d623e76… /
driver 535.309.01`, host TASL-2 (kernel 6.8.0-149-generic, uid 1008), cgroup 8 GiB / swap 0.

## 5. What was kept, and what was not done

- **Old sealed attempts untouched.** Before/after hashes are byte-identical for all three old sealed TASL-2
  attempts of the run — `sealed_g1b/g1b-tasl-20261121-b/mlab_imdb/attempt-1` (receipt `afc4445c…`),
  `…/mlab_ogbn_arxiv/attempt-1` (`76000bae…`), `…/mlgym_houseprice/attempt-1` (`1f1b6f83…`), 15 files in all
  (receipt, job record, node log, `out.tar`, `SHA256SUMS`) — and for the two old unsealed `mlgym_fmnist`
  infrastructure attempts (attempt-1 `job_record` `8c2fe155…`, `attempt.json` `af0015b6…`; attempt-2
  `job_record` `571b5403…`, `attempt.json` `25d4572a…`), 19 compared files, all `SAME`
  (`…_captures/inputs/untouched_confirmed.txt`). The old sealed attempts keep the old spec sha256 `060aac91…`;
  attempt-3 carries the re-issued `7ff3c95b…` (the G1B-JOIN assembly question, not this run's to decide).
- **Track P archive untouched.** `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (size 4096, mtime
  2026-11-17 15:42:26) and the lease logs `_attempt1_gpu_lease_log.jsonl` (sha `69505091…`) and
  `gpu_lease_log.jsonl` (sha `a0433998…`) have identical size/mtime/ctime and sha256 before and after; nothing under
  `/home/dowling/r1_trackp` was written.
- **TASL-7 untouched** (no job, no path written; its host record is cited only); **no G.4 pilot**, **no autoresearch
  AR job**, **no `compare`/`assemble`/`summarise`** (step 2 is this one node; the assembly needs G1B-JOIN).
- No deletion anywhere; no cgroup/tmp/`/dev/shm` leftovers; **no commit and no push** (this memo and the captures are
  written uncommitted for the lead).
- The run-tree/sealed trees gained only `runs/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/` and
  `sealed_g1b/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/`; all other trees are as they were (`…_captures/inputs/postrun.txt`).

## 6. Host end state (captured 2026-11-22T22:43:14Z)

TASL-2 idle: GPU `353 MiB, 0 %`, `nvidia-smi --query-compute-apps` empty, lease `~/r1_locks/gpu0.lock` **free**,
disk 351 GiB free, no G.1b job process (the only `pgrep` match is the capture shell itself), harness clean at
`c025f89a…` (only the allowed `nodes/*/data` links), checkout `paper_fmnist` at `34a5b1d6` tracked-clean with the
untracked note (`…_captures/inputs/postrun.txt`). Final launch-binding re-verification at the then-current
`origin/main 1402f466…`: **BINDING_OK**, `check_note` PASS (`spec_sha256 7ff3c95b…`), both host records PASS with
`681011b2…` / `09945c15…` (`…_captures/inputs/verify_final.log`) — the published `main` advanced again during the
run window (§1), and the note/host records stayed byte-identical.

## 7. Captures

`docs/r1/reports/tasl_chain_20261122/G1B_TASL2_FMNIST_AMENDMENT_20261122_captures/` — 24 payload files (the sealed attempt's own `SHA256SUMS` included) plus a
`SHA256SUMS` (own sha256 `c1f44f960515fefa26265051c2d4bbeae8133c50007ccb3ffb911a727a6c6b25`; `sha256sum -c` passes):

| path | contents |
|---|---|
| `sealed/` | `SEAL_RECEIPT.json`, `job_record.json`, `SHA256SUMS`, `node.log` (the sealed attempt; **no `out.tar`**) |
| `run/` | `attempt.json`, `setup.log` (the corrected `24cb3448…` manifest), `chunk_record.json` + `default_runs.jsonl` (default part), `driver.log`, `status`, `seal_verify.txt` (host-side `sha256sum -c` rc 0 in both locations) |
| `inputs/` | `prelaunch.txt`, `baseline.txt`, `launch_gate.log` (validate/check-note/host-record/binding/dry-launch), `verify_final.log` (end re-verify), `isolation_check.txt` (460/460 rows), `postrun.txt`, `endstate_extra.txt` (scope/cgroup gone, `/dev/shm` empty), `untouched_confirmed.txt`, `trackp_pre.txt`, `attempt_json_post.txt`, `driver.sh`, `signed_note_g1b_t1_tasl_20261122.md`, `g1b_tasl_spec.json` |

Host-side originals remain on TASL-2 under `/home/dowling/r1_tracks/t1_tasl/` (`paper_fmnist`,
`runs/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/`, `sealed_g1b/g1b-tasl-20261121-b/mlgym_fmnist/attempt-3/`,
`logs/g1b_fmnist_20261122.{driver.log,status}`, `captures/fmnist_20261122/`).

## 8. Reproduce

1. On TASL-2: clone `origin`, fetch `origin/main`, `git checkout --detach 34a5b1d6`; copy
   `docs/r1/authorizations/g1b_t1_tasl_20261122.md` from `origin/main` (byte-identical, sha256 `cea32f75…`).
2. `g1b_tasl.py validate sweep2/t1_tasl/g1b_tasl_spec.json --launch`; the launch gate of §1 (note, both host
   records, `verify_launch_tasl`) — all captured in `inputs/launch_gate.log`.
3. The wrapper command of §2 (`G1B_TASL_ENABLE_REAL=1 … t1_tasl_node.sh g1b <spec> mlgym_fmnist <note> --enable`),
   then `g1b_tasl.py seal <attempt-3> <spec> --node mlgym_fmnist`.
4. Verify `sha256sum -c SHA256SUMS` in the sealed and runs attempt directories; compare the old attempts/Track P
   hashes with the captures.

## 9. What this does and does not establish

- **Establishes (EVIDENCE, ENGINEERING_ONLY):** `mlgym_fmnist` completed all 460 declared runs of the re-issued
  spec on TASL-2's RTX 4090 under the signed amendment, with 0 divergent rows, the determinism gate passed, the
  isolation gate `effective: true` with empty waivers/exceptions on every row, the corrected data manifest
  (`24cb3448…`) accepted, no timeout and no STOP, and a hash-bound sealed attempt (`5476148a…` record,
  `8784aac7…` receipt) — in 1 h 30 m 38 s (1.5106 GPU-h), within the projection and the 100 GPU-h cap.
- **Does not establish:** the seven-node G.1b row/assembly (needs the author's G1B-JOIN decision, because the old
  sealed nodes carry spec `060aac91…` and this one `7ff3c95b…`), any TASL-7 node (note 2 and its P7 cross-host
  check are later steps), the cross-check/G.4/AR work, or any release-grade D21 statement by itself.
