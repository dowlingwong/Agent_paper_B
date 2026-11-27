# Round status — P11 host run, D.3 revision 6c, Ada venv; expansion and houseprice still running

**Round start:** `origin/coord/compute` `0cdaeb0a`; `origin/main` `5c901d19` (later `8b01ef6a`, then
`29099c4b`). **Time:** 27 Nov 2026, 01:19–01:55 UTC. No evidence campaign, no G.5 label, no sealed read.

## Delivered this round

| Task | Result | Branch / tip |
|---|---|---|
| `compute/20261127-05` with `-08` (G.5 P11 host tests) | TASL-7 server run PASS; record **ACCEPTED** with two MINOR notes | `compute-g5-p11-hosttest-20261127` @ `ba5f1e4a`; review `compute-g5-p11-hosttest-review-20261127` @ `f87a17cc` |
| `compute/20261127-09` item 2 (D.3 G1/G6 revision 6c) | revision 6c-3 **ACCEPTED FOR CODE** | `compute-d3-g1-design-r6c-20261127` @ `c1832cf6`; review `compute-d3-g1-design-r6c-review-20261127` @ `354f5ed5` |
| `compute/20261127-06` with `-11` (Ada P.4 venv) | PASS: freeze 121/121 equal to the lock; torch CUDA smoke 0.53 s on an empty card | `compute-ada-p4-venv-20261127` @ `ef146a64` |
| `compute/20261127-10` (no force push) | acknowledged; this round used new commits only | — |
| `compute/20261126-03` / rows (g) | still acknowledged; no new deliverable | — |

Details are in the separate reports `20261127-08-g5-p11-host-run.md`, `20261127-09-d3-rev6c.md` and the Ada record.

## Still running or waiting

| Item | State | What the next round checks |
|---|---|---|
| Expansion G.1b (`compute/20261126-10`) | `gc7rc_etth1` **finished 00:34:07Z and sealed**; `mlgym_metamaze` (pid 106579, ~150/460 train runs), `gc7rc_forestcover` (pid 106573, ~65), `mlgym_titanic` (pid 106578, ~53), all CPU-only on TASL-2 sets 0-3 / 4-7 / 12-15 | node completion, then `seal`, `assemble`, `summarise`; no GPU used |
| Houseprice CPU-set (`compute/20261127-01`) | driver started `01:32:50Z` on TASL-2, waiting for `cpus-0-3.lock`/`cpus-4-7.lock`; no run root created; capture `/home/dowling/r1_engineering/cpuset_20261127_20261127T013250Z`, driver pid 208315 | whether MetaMaze and Forest Cover finished; if the driver timed out after 1 h, rerun it; no scene consumed |
| G1 core review (`compute/20261127-09` item 1) | independent reviewer running the full `r1/tests` base/tip check (`51cf07f7`); tip log shows 100 failed / 4344 passed vs base 100 / 4328 — same failing set to be confirmed; review branch not pushed by the round end | the review branch tip and verdict; the coordinator merges on ACCEPTED |
| Screening smoke (`compute/20261127-07`) | STOP at `data-cache` stands; local fix `mac-screen-arff-content-20261127` @ `cb684870` is pushed but not merged and no repeat task is on `coord/coordinator` | whether the fix is merged and a repeat card is issued |
| G.5 campaigns (`compute/20261126-06`) | blocked on the published G.5 note | note publication |
| D.3 per-arm smoke (`compute/20261126-09`) | blocked on the G1 adapter, G2 constants and local units | those dependencies |

## Resource samples (read-only)

- **TASL-7:** 4090 24,029 MiB free, 0 compute apps, load 0.04; the P11 server was stopped and `gpu0.lock` is free.
- **Ada:** cards 0 and 2 empty (48,427 MiB free each); cards 1/3/4/5 shared (14.7 GB free), 6/7 21 GB free; load
  12.4; `ssh ada_server` logs in as `zli538` (uid 1008), not `dowling`. The venv is under
  `/data1/zli538/paperb_p4_20261127/`; no other user's file was touched.
- **ETP pool:** 441 Claimed / 22 Unclaimed / 1 Owner; GPU slots only 2 × TITAN X (deepthought) and 1 × L40S
  (deepthought2); **no H200/H100/A100/NEMO2 GPU**; `760065` (P.4 T1) still Idle.

## What was decided alone

To run the TASL-7 host test through `g4_tasl.serve_spec` with an engineering `run_id` rather than fabricate a G.5
note; to take Ada's empty card 2 for a 0.53 s torch smoke; to use CPython 3.12.10 (3.12.15 unavailable through the
host `uv`) and keep the package lock exact; to leave the two MINOR P11 wording notes in place after the ACCEPTED
review rather than change the accepted captures.

## Queue / next round

1. Expansion node completions → seals → `assemble`/`summarise`; report per-node determinism.
2. G1 core review verdict (`51cf07f7`); then the G1 code unit from revision 6c (replicate driver, recorder API,
   chunk branch, integration test).
3. Houseprice CPU-set run when the 0-3/4-7 leases are free.
4. P.4 probe (`compute/20261126-07`) now has a venv; it needs its own task/note, the `trackp_ada_v1.json` host
   fill and the calling-account decision.
5. Screening smoke repeat once the local fix is on `main` and a task is issued.
6. G.5 campaigns remain blocked on the G.5 note; D.3 per-arm smoke on G1/G2/local units.
