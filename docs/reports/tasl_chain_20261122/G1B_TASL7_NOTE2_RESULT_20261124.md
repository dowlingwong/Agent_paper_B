# G.1b on TASL-7 under the second note — result (24 Nov 2026)

ENGINEERING_ONLY, AI-assisted (Claude, note2-tasl7-runner). Run and sealed by the experiment agent on TASL-7; no
label, evaluation or sweep-2 file was read. This memo records the run only: it does not compare or assemble (the lead
does that), and it commits and pushes nothing.

## Verdict

**PASS — three of three authorized TASL-7 nodes ran and sealed, attempt-1 each, one after another under the GPU lease,
with 0 STOPs (node, timing or infrastructure), 0 retries and 0 refusals.** 1,380/1,380 runs written, 1,370 successful,
10 divergent (the `mlab_cifar10` c4 `divergent:non_finite_loss` rows of the declared edit — an outcome row, not a job
failure; the record's `stop` is null and `stop_class` is null on all three attempts). Every written row carries
`isolation.effective: true`, `log_intact: true`, `waivers {}`, `exceptions []`. Total **6.9858 GPU-hours** of wall time
against the spec's 14.202 GPU-h estimate (sensitivity 21.3), within R1-G1B-CAP.

The "launch refuses at 34a5 because of the old cross-check spec" contingency **did not occur**: the strict launch gate
(note + P7 + both host records + `verify_launch_tasl`, the real `g1b_tasl.launch` path with the job stubbed) passed for
all three nodes from the 34a5 launch checkout, and the real launches followed it. Details in §2.

## 1. What was launched (identity)

| item | value |
|---|---|
| run_id | `g1b-tasl-20261121-b` |
| note | `docs/r1/authorizations/g1b_t1_tasl_20261123.md`, sha256 `d9477972357203e5538204286773192d2bc08a98aee729cbdfcdc51303051c46` |
| note on `origin/main` | byte-identical (`git show origin/main:…` sha256 equals the file sha256 above) |
| G.1b spec | `sweep2/t1_tasl/g1b_tasl_spec.json`, sha256 `7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7` (the re-issued spec the note binds) |
| `paper_commit` in the note/spec | `3c3f822aaa839958a8754ffdcfa09a51e7699107` |
| launch commit (launch checkout HEAD) | `34a5b1d66c51e0a210939d9d58b35dba0bc0ffe2` (the G.1b spec re-issue commit of R1-T1-DATA-MANIFEST; detached checkout `paper_note2`) |
| published main at launch | `3024db3f8c9aa806c5c3458426e55d63d09edcab` (origin/main = `git ls-remote origin main` at every node start) |
| harness | `c025f89aeafc2199bf3487b4bcaa16678273c702`, clean (only the two allowed `nodes/*/data` untracked links) |
| host / GPU | TASL-7 / `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, NVIDIA GeForce RTX 4090, driver 580.178.04, 24,564 MiB |
| lease | `~/r1_locks/gpu0.lock`, exclusive flock for the whole job; free before and after |
| envs | `torch312` (Python 3.12.16, freeze `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, 77 packages) for `mlab_cifar10` and `mlgym_cifar10`; `jax312` (Python 3.12.16, freeze `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1`, 68 packages) for `mlgym_breakout_minatar` |
| orchestrator python | `/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python` (`T1_TASL_ORCHESTRATOR_PYTHON`) |
| keys | `G1B_TASL_ENABLE_REAL=1` and `--enable` on each launch |
| launch checkouts on TASL-7 | `paper_main3024` (main `3024db3f`, for `check-note2`), `paper_note2` (detached `34a5b1d6`, for the launches) |

Launch checkout verification (`launch_checkout_verify.txt`): HEAD `34a5b1d6`, origin
`https://github.com/dowlingwong/Agent_paper_B.git`, origin/main `3024db3f`, tracked-clean; the only untracked file is
the signed note copied from `origin/main` into `docs/r1/authorizations/`; `git diff 3c3f822a HEAD` outside `docs/` and
`sweep2/t1_tasl/g1b_tasl_spec.json` is **empty**; the spec file is HEAD's committed file with sha256 `7ff3c95b…`;
`34a5b1d6` and `3c3f822a` are both ancestors of `origin/main`/HEAD.

## 2. Strict `check-note2` (from a checkout of main `3024db3f`, not from 34a5)

Run from `paper_main3024` (HEAD = origin/main = `3024db3f`), per the note's P7 step:

```
python sweep2/t1_tasl/g1b_crosscheck.py check-note2 sweep2/t1_tasl/g1b_crosscheck_spec.json \
  --note docs/r1/authorizations/g1b_t1_tasl_20261123.md \
  --verdict docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlab_cifar10_20261122.json \
  --verdict docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_cifar10_20261122.json \
  --verdict docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_breakout_minatar_20261122.json
```

Result: **exit 0, strict PASS** — `{"mode": "strict", "p7": "PASS", "xc_note":
"docs/r1/authorizations/g1b_xc_t1_tasl_20261123.md"}`, verdicts for the three nodes
(`check_note2_context.txt`, `check_note2_main3024.txt`). The cross-check spec in that checkout is the re-issued
`a9e6b4633a8cbe3f8356aab748ac61b09f410475b33b0c6191826adfd926d164` (binds the G.1b spec `7ff3c95b…`, run
`g1b-tasl-20261121-b-xc2`). The three verdict files match the note's P7 sha256s exactly:

| node | verdict file | sha256 |
|---|---|---|
| mlab_cifar10 | `G1B_XC2_STEP1_VERDICT_mlab_cifar10_20261122.json` | `e5264c0b4f03d29b1e01f7348ca9a7e0aa4bbf5af4638f070963c08743b55987` |
| mlgym_cifar10 | `G1B_XC2_STEP1_VERDICT_mlgym_cifar10_20261122.json` | `cbd4b05f664e237654558f91c0d89583a15d3dadbefdcdde7202afb4171efb29` |
| mlgym_breakout_minatar | `G1B_XC2_STEP1_VERDICT_mlgym_breakout_minatar_20261122.json` | `29fe460eab12544a5e24964651a095ffa28e9d4c1314d3d4b9eaaddefcb6ca0a` |

Why not from 34a5: the 34a5 tree's `g1b_crosscheck_spec.json` is the pre-reissue one
(`2521f7d28f5d0b062d91a55bfaf853c8b6dd04a307c94a9d04f99a049471e5f3`, binding the old G.1b spec `060aac91…`,
`paper.commit ea34b1ab`), so `load_xc` there refuses before P7 can be checked. `check-note2` therefore ran from main
`3024db3f` as instructed.

**Launch gate (all three nodes, real `g1b_tasl.launch` with the job stubbed, `launch_gate.txt`):** exit 0; each node
returned `{"ok": true, "launch": {"paper_commit": "3c3f822aaa839958a8754ffdcfa09a51e7699107", "head":
"34a5b1d66c51e0a210939d9d58b35dba0bc0ffe2", "main": "3024db3f8c9aa806c5c3458426e55d63d09edcab", "spec":
"sweep2/t1_tasl/g1b_tasl_spec.json"}}`, i.e. `check_note` (note on origin/main, spec sha256, run_id, harness commit,
P1–P6 PASS, P7 PASS citing R1-T1-TASL-ENV), both keys, both hosts' host-check records and `verify_launch_tasl` all
passed at 34a5. No workaround was needed or used.

## 3. Pre-launch state (TASL-7, before the first launch)

`preflight.txt` (`2026-11-24T17:17:30Z`): GPU idle (0 % util, 44 MiB used, **no compute processes**), GPU UUID/model/
driver as in the note; lease **free** (`flock -n`); disk 470 GiB available (1.9 T, 74 % used); Yama `ptrace_scope` 1;
`/usr/local/cuda-12.2` present; RAM 62 GiB (59 available); load 0.01; harness at `c025f89a` clean; no
`runs/g1b-tasl-20261121-b` and no `sealed_g1b/g1b-tasl-20261121-b` existed (nothing to collide with); `_refusals` empty
throughout. Heavy I/O was not run beside the jobs; the nodes ran one after another (lease order: `mlab_cifar10`,
`mlgym_cifar10`, `mlgym_breakout_minatar`).

## 4. Runs and seals — the three attempts

All three are `attempt-1`; the drives ran the documented command form
`G1B_TASL_ENABLE_REAL=1 bash <checkout>/sweep2/t1_tasl/t1_tasl_node.sh g1b <spec> <node> <note> --enable` and each was
sealed with `g1b_tasl.py seal <attempt> <spec> --node <node>` (`<spec>` = the launch checkout's
`sweep2/t1_tasl/g1b_tasl_spec.json`).

| node | env | start (UTC) | end (UTC) | wall | GPU-h | runs written / successful / divergent | determinism |
|---|---|---|---|---|---|---|---|
| mlab_cifar10 | torch312 | 2026-11-24T17:17:34Z | 2026-11-24T18:04:29Z | 2,816 s (0h46m56s) | 0.7822 | 460 / 450 / 10 | true |
| mlgym_cifar10 | torch312 | 2026-11-24T18:04:31Z | 2026-11-24T19:34:42Z | 5,412 s (1h30m12s) | 1.5033 | 460 / 460 / 0 | true |
| mlgym_breakout_minatar | jax312 | 2026-11-24T19:34:45Z | 2026-11-25T00:16:45Z | 16,921 s (4h42m01s) | 4.7003 | 460 / 460 / 0 | true |
| **total** | | | | **25,149 s (6h59m09s)** | **6.9858** | **1,380 / 1,370 / 10** | |

- `mlab_cifar10`'s 10 divergent rows are all c4 (`divergent:non_finite_loss`: 3 train, 6 split, 1 joint) — the declared
  c4 edit's outcome, recorded as divergent by the engine, not a stop; the job record has `stop: null`, `stop_class: null`,
  the determinism gate is `true` (c0–c4 default/default_repeat outcomes identical), and the run counts are exactly the
  spec's 460.
- Per-part writes were 10 / 150 / 150 / 150 on every node, all parts `rc 0`, no `stop`, no `stop_kind`.
- No node reached its deadline or timeout (`deadline_s`: 20,570 / 47,389 / 88,123 s; timeout basis
  `census_slowest_x3`: 13.347/35.948/61.781 s → 40.041/107.844/185.343 s). The 4090/Ada timing ratios recorded per part
  were ~0.48–0.49 (`mlab_cifar10`), ~0.353–0.355 (`mlgym_cifar10`) and ~0.587–0.622 (`mlgym_breakout_minatar`), i.e. the
  card was faster than the census Ada times, not slower.

**Effective isolation (checked over every written row of every attempt, `TASL-7/<node>.isolation.json`):**
`isolation.effective: true` 460/460, `log_intact: true` 460/460, `waivers {}`, `exceptions []` on each node; the job
records also carry the delegated scope `MemoryMax=8G`/`MemorySwapMax=0`, affinity 0-7, non-root uid 1011, and
`foreign_checks: []` before/after every part.

### Seal receipts and sealed files (sha256)

| node | SEAL_RECEIPT.json | job_record.json | out.tar | node.log | SHA256SUMS |
|---|---|---|---|---|---|
| mlab_cifar10 | `4a1a1e2fb16901655878c6d9a453a3a52a51598859dfbaf71dc049a5a9227fe0` | `d07eb4f272a074c1de247cff831269f68be3c4e250ba6431a6d8bd6f1060c93e` | `eb30fb24efb35f1072d8242a8e09d8d645dd4d5fd0683ce1d1c67326ed22d432` | `99912af24f3f94319dd9a5a45869f0e73b6c87d641dfc414b19c4f8d6e97d34f` | `b6e4d2d08391a281f2b62144ec6d148c8bf8554274ca06ca1f95eb4398d0072a` |
| mlgym_cifar10 | `22b690a7d55bf3823c3ffac62fa3f19be0795b982252ec8c71bc04152faa1354` | `1663b2baae1b143690b5070ddbf85bb927e26c95904ff2ea990d9d03fa460362` | `f886b59b9afe9b75ae3e69c6de03c31b2b29f84a85dacac7909ac268d048a446` | `ac073eac786cf6cf38b72a9d8cf3a342a2504b39187256769e5af43c3045e2ca` | `9b35cc0a9bb683ee545833eb647560b32a143f958474a5392adc65ebb9b8b145` |
| mlgym_breakout_minatar | `887b102cbfcf706229a13e02e0f9faf6713cd813edd5e037b43266372d03f7bd` | `c8a8d8582a92fdc4f996f66e64676197e473f03f9c800506749e462be1ba2e1e` | `156ee4d638480ffa43c26d85271ce08b992365c15947a961b6523d703c278e45` | `902513efc344531c0c769c59889b998aa88b144843232f8b9c9ab6c5622e6659` | `8fe703aaee9f4cc7d2c17ef68e1023dcd38d95b25b3603611d082739717da2e4` |

`sha256sum -c SHA256SUMS` verifies **OK** in each sealed directory (`sealed_verify.txt`); each receipt's
`job_record_sha256`/`node_log_sha256` equal the files above and `stop`/`stop_class` are null. Sealed paths (TASL-7):

- `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-b/mlab_cifar10/attempt-1`
- `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-b/mlgym_cifar10/attempt-1`
- `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/g1b-tasl-20261121-b/mlgym_breakout_minatar/attempt-1`

Unsealed run directories (kept, not deleted): `/home/dowling/r1_tracks/t1_tasl/runs/g1b-tasl-20261121-b/<node>/attempt-1`
with `out/`, `job_record.json`, `out.tar`, `SHA256SUMS`; the wrapper logs are in
`/home/dowling/r1_tracks/t1_tasl/runs/g1b-tasl-20261121-b/_logs/` and are bound by the seals. Driver log/status:
`/home/dowling/r1_tracks/t1_tasl/logs/g1b_note2_tasl7_20261124.{log,status}` (`CHAIN_DONE 2026-11-25T00:16:45Z`).

## 5. STOPs, retries, refusals

**None.** Every `t1_tasl_node.sh` call returned 0 on the first try; no node/timing STOP, no infrastructure STOP (so no
retry was exercised), no refusal record (`runs/g1b-tasl-20261121-b/_refusals` does not exist), no
`close-attempt`/`seal` failure. The first timed-out run rule was never met (no engine timeout rows).

## 6. Post-run state and constraints honoured

`endstate_clean.txt` (`2026-11-25T00:18:44Z`; the earlier `endstate.txt` is superseded — its `pgrep` lines matched the
capture command itself): 0 driver/job/engine processes, 0 user systemd scopes left, GPU idle (44 MiB, 0 % util), no
compute processes, **lease free**, disk 469 GiB available, harness/pins unchanged at `c025f89a` (only the allowed data
links untracked).

- **No commit and no push.** `paper_note2` HEAD is still `34a5b1d6` (0 new commits since launch), tracked-clean, only the
  untracked signed note in `docs/r1/authorizations/`; `paper_main3024` is at `3024db3f`; `origin/main` is still
  `3024db3f` (local = `ls-remote`). Nothing was committed, pushed or published from TASL-7.
- **Nothing deleted.** The old sealed attempts are all kept and untouched: `g1b-tasl-20261121-a/` (its
  `mlgym_breakout_minatar` tree), `g1b-tasl-20261121-b-xc-TASL-7/` (1 sealed attempt), `g1b-tasl-20261121-b-xc2-TASL-7/`
  (3 sealed attempts), and the earlier TASL-7 run trees; the Track P archive `/home/dowling/r1_trackp` is present
  (11 entries) and untouched.
- **TASL-7 only.** Every command ran on TASL-7 (`ssh -o BatchMode=yes tasl7`); no TASL-2 job, no G4/AR job, no
  label/evaluation/sweep-2 file was opened.
- **No compare/assemble.** `g1b_crosscheck.py compare`, `g1b_tasl.assemble` and `summarise` were not run (the lead
  assembles); the three sealed attempts are the input they need.

## 7. Captures

Directory: `docs/r1/reports/tasl_chain_20261122/G1B_TASL7_NOTE2_RESULT_20261124_captures/` (small, no `out.tar`):

- `check_note2_context.txt`, `check_note2_main3024.txt` — strict `check-note2` from main `3024db3f` (context shas + output).
- `launch_checkout_verify.txt` — paper_note2 HEAD/origin/status/code-diff/spec checks at `34a5b1d6`.
- `launch_gate.txt` — `validate --launch` and the stubbed-run launch binding for the three nodes.
- `preflight.txt`, `endstate_clean.txt` (and the superseded `endstate.txt`) — GPU/lease/disk/process state before/after.
- `sealed_verify.txt` — `sha256sum -c SHA256SUMS` and the sealed-file sha256s on TASL-7.
- `g1b_note2_driver.sh`, `g1b_note2_launch_gate.py`, `note2_capture.py` — the exact driver/gate/capture scripts used.
- `g1b_note2_tasl7_20261124.log`, `.status` — driver log and status (`CHAIN_DONE`), wrapper logs included per node.
- `TASL-7/<node>.summary.json`, `.job_record.json`, `.SEAL_RECEIPT.json`, `.node.log`, `.isolation.json`,
  `.sealed.sha256`, `.sealed.SHA256SUMS` — per-node evidence; the full job records and wrapper logs are included.

`SHA256SUMS` in this directory lists the captures' sha256s (the memo file is not in it).

## 8. Reproduce (operator reference, TASL-7)

```
B=/home/dowling/r1_tracks/t1_tasl; P=$B/paper_note2
export G1B_TASL_ENABLE_REAL=1 T1_TASL_ORCHESTRATOR_PYTHON=$B/envs/torch312/bin/python
git -C $P fetch origin main                      # origin/main must equal git ls-remote origin main
bash $P/sweep2/t1_tasl/t1_tasl_node.sh g1b $P/sweep2/t1_tasl/g1b_tasl_spec.json <node> \
     $P/docs/r1/authorizations/g1b_t1_tasl_20261123.md --enable
$B/envs/torch312/bin/python $P/sweep2/t1_tasl/g1b_tasl.py seal \
     $B/runs/g1b-tasl-20261121-b/<node>/attempt-1 $P/sweep2/t1_tasl/g1b_tasl_spec.json --node <node>
```

`<node>` in lease order: `mlab_cifar10`, `mlgym_cifar10`, `mlgym_breakout_minatar`. Prepared by the TASL-7 runner
(note2-tasl7-runner), 25 Nov 2026; the date in the file name is the identifier used by the chain.
