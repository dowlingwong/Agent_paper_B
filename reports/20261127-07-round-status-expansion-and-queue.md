# Round status — expansion ETTh1 sealed; three G.1b nodes running; independent work delivered

**Round start base:** `origin/coord/compute` `a7346712`; `origin/main` `bd406db9`. **Time:** 27 Nov 2026 ~00:50Z
(01:50 CET). No evidence run, no GPU job this round beyond the already-launched CPU G.1b nodes.

## 1. Expansion G.1b (`compute/20261126-10`) — one of four nodes finished and sealed

| Node | State | Attempt | Evidence |
|---|---|---|---|
| `gc7rc_etth1` | **finished 00:34:07Z** (460/460 successful, 0 divergent, determinism true, `stop: null`) | `attempt-1` | sealed at `/home/dowling/r1_tracks/t1_tasl_x/sealed_g1b/g1b-x-tasl-20261126-a/gc7rc_etth1/attempt-1`; `job_record.json` sha256 `2c50d59acbf1d224ddbc35927318237be2f4ebdaf76ff7d5cb4632092394aca2`; `out.tar` sha256 `7c48fb633e284b6dd9d22358672f89770e161a436fa836a611557b7376cf60af`; seal receipt written 00:37:08Z |
| `mlgym_metamaze` | running, pid 106579 | `attempt-1` | CPU set 0-3; train phase |
| `gc7rc_forestcover` | running, pid 106573 | `attempt-1` | CPU set 4-7; train phase |
| `mlgym_titanic` | running, pid 106578 | `attempt-1` | CPU set 12-15; train phase |

All four launched 22:53:26Z; no node STOP. The three running nodes are in `train`; no attempt directory has a
`stop`. Next: seal each on completion, then `assemble` (one sealed attempt per node) and `summarise`; report the
per-node verdicts and summary sha256. `assemble` refuses while any node is missing, so it is not run yet.

## 2. Delivered or decided this round

| Task | Result | Branch / tip |
|---|---|---|
| `compute/20261127-04` + `cluster/20261126-02` (G1) | G1 snapshot core delivered; full G1 blocked by the verify-seed collision and the FIXR3/EGATE integration gap | `compute-d3-g1-snapshot-20261127` @ `51cf07f7` |
| `compute/20261127-07` (screening smoke) | **STOP** at `data-cache`: sklearn 1.8 stores the correct ARFF as `<id>.gz`; `check_pilot` classifies by suffix | `compute-screen-smoke-stop-20261127` @ `33767535` |
| `compute/20261126-03` (rows (g)) | acknowledged; no separate deliverable | — |
| `compute/20261127-02` item 2 (survey redaction) | finished and reported earlier; `compute-resource-survey-20261126` @ `58e6bbeb` (merged `909fdc59`) | — |
| `compute/20261127-03` (G.5 copy verdict + P11 table) | finished and reported earlier; branches `compute-g5-copy-verdict-line-20261127` @ `e6d6d50d`, `compute-g5-p11-host-tests-20261127` @ `f40e5eef` (both merged) | — |
| `cluster/20261126-01` (torch tests) | FAIL (1 test), reported earlier; no branch | — |

## 3. Blocked, with the dependency the next round should check

| Task | Blocked on | Check next round |
|---|---|---|
| `compute/20261127-01` houseprice CPU-set | `cpus-0-3.lock` and `cpus-4-7.lock` held by MetaMaze and Forest Cover | whether those two expansion nodes have finished; then run `run_cpuset_check.sh` |
| `compute/20261127-05` G.5 P11 host tests | no `docs/r1/authorizations/c3_t1_labels_*.md` on `main`; the G.5 note is unpublished, and the TASL-2 items need 0-7 | whether the G.5 note is published and the 0-7 leases are free |
| `compute/20261127-06` Ada P.4 venv | `dowling@100.79.185.61` denies this session's key (via the tasl2 jump); `zli538` is another user's account and was not used | an Ada key/route for the `dowling` account, or a host decision |
| `compute/20261126-06` G.5 campaigns | the published G.5 note (local render/review) | note publication |
| `compute/20261126-07` P.4 probe | the Ada venv and `local/20261127-02` (missing-runs STOP) | those two |
| `compute/20261126-09` D.3 per-arm smoke | G1 adapter, `local/20261126-05` item 1, `local/20261126-03` | G1 decisions + the local units |
| `compute/20261127-05` / G1 decisions | coordinator/author: verify-seed rule and FIXR3/EGATE | a decision row or task |

## 4. Idle capacity (last observation 23:42Z; no new sample this round)

TASL-7's 4090 was empty (24,029 MiB free, 0 compute apps); Ada had two empty 48 GB cards (0 and 2). The ETP pool
still advertised no H200/H100/A100 and no NEMO2 GPU; `760065` remained Idle. No reservation was taken.

## 5. What was decided alone

To seal ETTh1 immediately on completion and not touch the three running nodes; to STOP the screening cache build at
the first defect instead of editing the reviewed fix or switching to the 26 Nov environment; to implement the G1
counting/parity core and stop before the adapter rather than choose the verify-seed or FIXR3/EGATE integration; to
leave Ada untouched after the `dowling` key was refused.
