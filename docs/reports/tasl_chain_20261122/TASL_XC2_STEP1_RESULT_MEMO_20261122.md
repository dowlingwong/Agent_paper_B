# G.1b cross-host check rerun `g1b-tasl-20261121-b-xc2` — step 1 of the 22 Nov TASL chain — PASS (22 November 2026)

**Result: PASS.** The six default-part jobs (three TASL-7 nodes × both hosts) ran under the signed cross-check note
and were sealed; the three step-1 verdicts (`g1b_crosscheck.py compare --mode xc`) are **PASS**: every default and
default_repeat outcome of c0–c4 is present and bit-identical across the hosts, and both sides are deterministic.
No author STOP occurred. ENGINEERING_ONLY; no label, evaluation or sweep-2 file was read. AI-assisted (DeepSeek
Harness agent `xc2-runner`, delegated by the lead).

Written uncommitted on the Mac ops worktree `ops-tasl-20261116` (baseline `3a5d388e`); the lead commits the three
verdicts and this memo. Nothing was pushed; nothing was deleted.

## 1. Authority and inputs (all verified before any job)

- Note: `docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md`, sha256
  `e2bec61a03b5125d69a5cf745edc66721132eb5829e29cbe3633c215e19152d5` (blob `c4b3a831…`), from published
  `origin/main`; `approved: true`, `label: ENGINEERING_ONLY`, `labels_read: none`; binds
  `run_id: g1b-tasl-20261121-b-xc2`, `paper_commit: 34a5b1d66c51e0a210939d9d58b35dba0bc0ffe2`,
  `xc_spec_sha256: a9e6b4633a8cbe3f8356aab748ac61b09f410475b33b0c6191826adfd926d164`,
  `g1b_spec_sha256: 7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7`,
  `harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702`.
- Launch commit `b5824240b5cc8a75bd01bf2338890e7c0af6788b`, whose parent is the paper commit `34a5b1d6`; the diff
  `34a5b1d6..b5824240` outside `docs/` is exactly `sweep2/t1_tasl/g1b_crosscheck_spec.json` (verified empty after
  excluding that file): the code, kits, envs and tests are the paper commit's.
- Spec `sweep2/t1_tasl/g1b_crosscheck_spec.json` sha256 `a9e6b463…` (validated: run id, nodes
  `mlab_cifar10, mlgym_breakout_minatar, mlgym_cifar10`, hosts `TASL-7, TASL-2`, TASL-2 `jax312` addition);
  `g1b_tasl_spec.json` sha256 `7ff3c95b…`.
- Per-host checkout: **`/home/dowling/r1_tracks/t1_tasl/paper_xc2`** cloned from `origin`, detached at
  `b5824240`, `origin/main` freshly fetched, the signed note copied byte-identically from `origin/main` to
  `<checkout>/docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md` (untracked, sha256 `e2bec61a…`), tracked tree
  clean. `origin/main` at preparation: `f93264fcdf2e20e46c213d2f327dd10a52f37a6a` (publication commit
  `5a85adf9`); see §5 for its legitimate advance during the run. Harness checkout `/home/dowling/r1_tracks/t1_tasl/harness`
  at `c025f89a…` in both hosts, only the allowed `nodes/*/data` symlinks untracked.
- **`g1b_crosscheck.py validate` PASS** on both hosts (`ok: true`, run id, three nodes) and the **launch binding
  `verify_launch_tasl` PASS** on both hosts (re-verified at the end against `origin/main` `9f23fea8…`):
  `BINDING_OK` — `paper_commit 34a5b1d6`, `head b5824240`, `main 9f23fea8`, spec path; the note identity, both
  host-check records (`TASL-2` sha `681011b2…`, `TASL-7` sha `09945c15…`) and the derived specs for all six
  (node, host) pairs validated. Logs: `…_captures/inputs/verify_tasl7.log`, `verify_tasl2.log`,
  `verify_final_tasl7.log`, `verify_final_tasl2.log`.

## 2. The six default-part jobs

Command (per node, inside its delegated scope, from the host's `paper_xc2` checkout, with
`G1B_TASL_ENABLE_REAL=1` and `T1_TASL_ORCHESTRATOR_PYTHON=<torch312 python>`):

```
bash <checkout>/sweep2/t1_tasl/t1_tasl_node.sh xc \
     <checkout>/sweep2/t1_tasl/g1b_crosscheck_spec.json <node> \
     <checkout>/docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md <TASL-7|TASL-2> --enable
```

Each node ran sequentially on its host under the GPU lease; the two hosts ran concurrently (no lease overlap on a
host). On rc 0 the attempt was sealed with
`g1b_tasl.py seal <attempt> <runs>/<run id>/_specs/<node>.json --node <node>` (derived specs under
`runs/g1b-tasl-20261121-b-xc2-TASL-7/` and `…-TASL-2/`). Run ids: `g1b-tasl-20261121-b-xc2-TASL-7` and
`g1b-tasl-20261121-b-xc2-TASL-2` (as the note's jobs line).

| host | node | attempt | job start–end (UTC) | wall s | runs written/success/divergent | c0 median wall s | 4090/Ada ratio | max wall s | deadline s |
|---|---|---|---|---|---|---|---|---|---|
| TASL-7 | `mlab_cifar10` | 1 | 20:45:32–20:46:33 | 61 | 10/10/0 | 5.945 | 0.4835 | 6.160 | 20570 |
| TASL-7 | `mlgym_cifar10` | 1 | 20:46:34–20:48:31 | 117 | 10/10/0 | 11.181 | 0.3524 | 12.380 | 47389 |
| TASL-7 | `mlgym_breakout_minatar` | 1 | 20:49:44–20:55:44 | 360 | 10/10/0 | 36.731 | 0.5997 | 36.731 | 88123 |
| TASL-2 | `mlab_cifar10` | 1 | 20:50:19–20:51:56 | 97 | 10/10/0 | 5.608 | 0.4560 | 5.984 | 20570 |
| TASL-2 | `mlgym_cifar10` | 1 | 20:51:57–20:54:16 | 139 | 10/10/0 | 10.408 | 0.3280 | 11.900 | 47389 |
| TASL-2 | `mlgym_breakout_minatar` | 1 | 20:54:17–20:59:21 | 304 | 10/10/0 | 30.305 | 0.4948 | 30.562 | 88123 |

GPU (both hosts): `NVIDIA GeForce RTX 4090`, 24564 MiB, TASL-7 `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`
(driver 580.178.04), TASL-2 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (driver 535.309.01). Lease per job:
`/home/dowling/r1_locks/gpu0.lock`, held by the job's process (TASL-7 pids 493115, 493641, 494796; TASL-2 pids
452962, 454497, 456417), free before and after. Environments: `torch312` on both hosts for `mlab_cifar10` and
`mlgym_cifar10`, `jax312` for `mlgym_breakout_minatar` (TASL-2 via the cross-check spec's `env_python_additions`);
TASL-7 carries its `XLA_FLAGS` host setting, TASL-2 does not (as the note discloses). Every part is the default
part only: 10 rows ((4 edits + 1) × 2 conditions), as the job record's `crosscheck_default_part: true` states.

Seal results — all six sealed, `sha256sum -c SHA256SUMS` OK, no infrastructure/node/timing stop
(`stop: null`, `stop_class: null`), derived-spec sha256 equals the job record's `spec_sha256`, `attempt-1` only:

| host | node | sealed path (host) | sealed files sha256 (receipt / job_record / out.tar / node.log) | SHA256SUMS sha256 |
|---|---|---|---|---|
| TASL-7 | `mlab_cifar10` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-7/mlab_cifar10/attempt-1` | `4867cc7ce845…` / `f2149f81eb11…` / `d104929c0a83…` / `8e120d8f798c…` | `3e948769bfad…` |
| TASL-7 | `mlgym_cifar10` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-7/mlgym_cifar10/attempt-1` | `6129a725f0e9…` / `5c7b3e93862e…` / `f51aa43f7ec5…` / `f7ba91acece7…` | `8ac53af0b8d2…` |
| TASL-7 | `mlgym_breakout_minatar` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-7/mlgym_breakout_minatar/attempt-1` | `accee249d5bf…` / `fe5c5c5d83c7…` / `6b1e1a0d88e0…` / `527b45d56f1d…` | `c0a8f94eacf8…` |
| TASL-2 | `mlab_cifar10` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-2/mlab_cifar10/attempt-1` | `23f058641ca7…` / `c863ea61f64c…` / `593dc29b5bcb…` / `315503e8953a…` | `1d3991811bb8…` |
| TASL-2 | `mlgym_cifar10` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-2/mlgym_cifar10/attempt-1` | `00733a0d1c04…` / `f30edd055eb6…` / `cbe1bfd83197…` / `b5c201dabda5…` | `f6e8a720f446…` |
| TASL-2 | `mlgym_breakout_minatar` | `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-2/mlgym_breakout_minatar/attempt-1` | `347f690280bf…` / `13409befcbcc…` / `8fa40e1a6848…` / `670404c244d8…` | `442f82cb7563…` |

Full hashes are in `<capture>/TASL-7/<node>.sealed.sha256` and `<capture>/TASL-2/<node>.sealed.sha256`; the
sealed copies (`SEAL_RECEIPT.json`, `job_record.json`, `node.log`, `SHA256SUMS`, `out.tar`) and the derived specs
are in the capture set. (Host roots above are `/home/dowling/r1_tracks/t1_tasl`; `…` abbreviates that prefix.)

## 3. Step-1 verdicts — three PASS

`g1b_crosscheck.py compare --mode xc <checkout spec> --node N --a <TASL-7 sealed> --b <TASL-2 sealed> --out <path>`,
run from the TASL-7 `paper_xc2` checkout (b5824240) with `torch312` python; the TASL-2 sealed attempts were
transferred byte-identically to `/home/dowling/r1_tracks/t1_tasl/captures/xc2_20261122/peer_TASL-2/…` on TASL-7
(their `SHA256SUMS` verified on arrival; `compare` binds `job_record.json` by sha256, so the copy is the TASL-2
attempt — its job-record hashes are the TASL-2 originals). The verdict files are preserved byte-exactly:

| node | verdict | verdict path (repo-relative, uncommitted) | sha256 |
|---|---|---|---|
| `mlab_cifar10` | **PASS** | `docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlab_cifar10_20261122.json` | `e5264c0b4f03d29b1e01f7348ca9a7e0aa4bbf5af4638f070963c08743b55987` |
| `mlgym_cifar10` | **PASS** | `docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_cifar10_20261122.json` | `cbd4b05f664e237654558f91c0d89583a15d3dadbefdcdde7202afb4171efb29` |
| `mlgym_breakout_minatar` | **PASS** | `docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_breakout_minatar_20261122.json` | `29fe460eab12544a5e24964651a095ffa28e9d4c1314d3d4b9eaaddefcb6ca0a` |

Each verdict: `schema g1b_tasl_crosscheck_verdict/1`, `mode xc`, `crosscheck_run_id g1b-tasl-20261121-b-xc2`,
`g1b_run_id g1b-tasl-20261121-b`, `g1b_spec_sha256 7ff3c95b…`, `harness_commit c025f89a…`, `complete: true`,
`reason: null`, `on_stop: null`, both sides `deterministic: true`, attempt 1. Side bindings (run id / derived-spec
sha256 / job-record sha256): `mlab_cifar10` TASL-7 `g1b-tasl-20261121-b-xc2-TASL-7` / `2c542d6e…` / `f2149f81…`,
TASL-2 `…-TASL-2` / `af30beb0…` / `c863ea61…`; `mlgym_cifar10` TASL-7 `fed22d0d…` / `5c7b3e93…`, TASL-2
`73254656…` / `f30edd05…`; `mlgym_breakout_minatar` TASL-7 `d764ec20…` / `fe5c5c5d…`, TASL-2 `6a50c785…` /
`13409bef…`.

The compared default-part outcomes (`_outcome`: `["ok", metric]`; the repeat row is identical in every case):

| node | c0 | c1 | c2 | c3 | c4 |
|---|---|---|---|---|---|
| `mlab_cifar10` | 0.5184 | 0.5848 | 0.5646 | 0.5528 | 0.1004 |
| `mlgym_cifar10` | 0.4836 | 0.5492 | 0.6976 | 0.6508 | 0.4564 |
| `mlgym_breakout_minatar` | 20.838281 | 32.725781 | 30.654688 | 6.979687 | 6.95 |

All ten (node × host) sides wrote exactly the expected 10 rows with 0 divergent; no config failed on either side; the
default_repeat equals the default on every config on every side.

## 4. What was kept, and what was not done

- Old sealed attempts kept, untouched: TASL-7 `sealed_g1b/g1b-tasl-20261121-b-xc-TASL-7/mlab_cifar10/attempt-1`
  (SEAL_RECEIPT sha256 `0695daf8…`) and its unsealed old xc attempt in `runs/…-b-xc-TASL-7/mlgym_cifar10/attempt-1`;
  TASL-2 `sealed_g1b/g1b-tasl-20261121-b/{mlab_imdb,mlab_ogbn_arxiv,mlgym_houseprice}/attempt-1` (receipts
  `afc4445c…`, `76000bae…`, `1f1b6f83…`) and the old runs-tree attempts (`g1b-tasl-20261121-b/mlgym_fmnist`
  attempt-1/2, `g1b-tasl-20261121-a/…`); the earlier `g1b-tasl-20261121-a`/`-b` trees are listed in
  `<capture>/TASL-7/trees.txt`, `<capture>/TASL-2/trees.txt`, `<capture>/…/old_attempts.txt`.
- Not run: no G.1b amendment (`mlgym_fmnist`), no G.4 pilot, no autoresearch AR job; no `compare --mode preassembly`,
  no `assemble`/`summarise` (step 2 and the assembly are later chain steps).
- Track P untouched: no Track P path was read or written; the only new host paths are
  `/home/dowling/r1_tracks/t1_tasl/paper_xc2`, `runs/g1b-tasl-20261121-b-xc2-{TASL-7,TASL-2}/`,
  `sealed_g1b/g1b-tasl-20261121-b-xc2-{TASL-7,TASL-2}/`, `captures/xc2_20261122/`, `logs/xc2_*`. No deletion.
  No commit and no push (the verdicts/memo are written uncommitted for the lead).

## 5. Deviations and disclosures (all preserved, nothing retried silently)

1. **Legitimate concurrent publication of `main` during the first pass.** The first pass began with
   `origin/main = f93264fc` (the state the task names, via publication `5a85adf9`). During it, the chain's second
   delivery was published on `main`: `f93264fc` → `5d5ca7b4` → `9f23fea8` (commit
   `9f23fea8 docs(r1): R1-G1B-JOIN (option A) and the signed third G.1b note…`; the launch-table/report/spec-support
   /third-note delivery (d) — not this run's files). Because each job's launch gate re-checks *live* `origin/main`
   against the checkout's fetched `origin/main`, two launches refused at the gate before creating an attempt:
   TASL-7 `mlgym_breakout_minatar` (20:48:31Z) and TASL-2 `mlab_cifar10` (20:48:33Z), both
   `STOP: fetch published main before launch; local origin/main differs or could not be verified`, wrapper rc 4,
   `attempt=none` (no attempt consumed, no refusal record — the launch gate runs before `run_node_job`). Node logs
   and first-pass statuses are kept in `<capture>/TASL-7/launch_refusals/` and `<capture>/TASL-2/launch_refusals/`.
   The remedy is the gate's own: re-fetch `origin/main` and launch again. The signed note and both host-check
   records are **byte-identical** at `f93264fc` and at `9f23fea8` (note `e2bec61a…`, host records `681011b2…` /
   `09945c15…`); the launch spec and the checkout (code `= 34a5b1d6` outside docs/spec) are unchanged; `main` may
   move on after the signature by design (`verify_launch_tasl`). After the re-fetch and re-verification the binding
   passed (`BINDING_OK`, §1) and the remaining jobs launched. Net effect: TASL-7 `mlab_cifar10` and `mlgym_cifar10`
   launched against `f93264fc`; TASL-7 `mlgym_breakout_minatar` and all three TASL-2 jobs launched against
   `9f23fea8`. The launch binding is not an input to the sealed job record or to the verdict (which binds run id,
   derived-spec sha256, harness pin, receipt, record and rows); the final re-verification at `9f23fea8` is captured.
2. **Comparison host and the peer copy.** Both hosts' sealed attempts are needed by `compare`; the TASL-2 attempts
   were transferred to TASL-7 (byte-identical, `SHA256SUMS` verified; `<capture>/TASL-7/peer_transfer_check.txt`)
   and the comparison ran there. The verdicts' `sides.TASL-2.sealed` field therefore records that peer path
   (`/home/dowling/r1_tracks/t1_tasl/captures/xc2_20261122/peer_TASL-2/…`); the TASL-2 attempts' authoritative
   sealed paths remain `…/sealed_g1b/g1b-tasl-20261121-b-xc2-TASL-2/<node>/attempt-1` and their job-record sha256s
   are identical in both places. The comparison verdict core (everything except the read location) is unaffected.
3. **One driver failed to start on the first attempt for TASL-2** (a `scp` invocation aborted by a missing local
   `timeout` utility); no host state was changed by it and the driver was then copied and started normally. The
   first-pass driver logs for both hosts are captured.
4. TASL-7 `mlab_cifar10` and `mlgym_cifar10` sealed in the first pass; the refused `mlgym_breakout_minatar` and all
   three TASL-2 nodes were resumed in a second pass that fetches `origin/main` before each launch. All six final
   sealed attempts are `attempt-1`; there is no attempt-2.

## 6. Host end state (captured after the run)

TASL-7 and TASL-2 both idle: `nvidia-smi --query-compute-apps` empty, lease `~/r1_locks/gpu0.lock` free, no
`g1b`/`noise_floor`/`t1_tasl`/`xc2` process of the user, disk 490 GiB (TASL-7) / 352 GiB (TASL-2) free:
`<capture>/TASL-7/postrun_state.txt`, `<capture>/TASL-2/postrun_state.txt`.

## 7. Captures

`docs/r1/reports/tasl_chain_20261122/TASL_XC2_STEP1_RESULT_MEMO_20261122_captures/` — 104 payload files
plus a `SHA256SUMS`:
`inputs/` (this run's input hashes, checkout-setup and launch-binding logs, the driver and comparison scripts),
`TASL-7/` and `TASL-2/` (preflight and post-run host state, per-node `record.json` summaries, the sealed files and
derived specs, `sealed.sha256`, `sha256sum -c` results, `trees.txt`, `old_attempts.txt`, `spec_sha_binding.txt`,
driver logs/statuses, `launch_refusals/`), `verdicts/` (byte-identical copies of the three verdicts), `compare/`
(the comparison log), `SHA256SUMS` (sha256 over every capture file; the file's own sha256 is
`b86e991e3addc1f05e206785e2f0baa0bf02c4bf8dc5f18189c07ad76bc2b8c8`; `sha256sum -c` passes). All host-side evidence lives on the two hosts under `/home/dowling/r1_tracks/t1_tasl/` as listed in §2.

## 8. Reproduce

1. On each host: clone `origin`, fetch `origin/main`, `git checkout --detach b5824240`; copy
   `docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md` from `origin/main`.
2. `g1b_crosscheck.py validate <spec>`; check the note and the launch binding (`verify_launch_tasl`), §1.
3. For each host and node: the wrapper command of §2; then `g1b_tasl.py seal <attempt> <derived spec> --node <node>`.
4. Transfer TASL-2's sealed attempts to the comparison host; `compare --mode xc` per node (§3).
