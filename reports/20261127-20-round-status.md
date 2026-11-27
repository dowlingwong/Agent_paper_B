# Round status — 27 Nov 2026, 10:20–11:40 UTC

`origin/main` moved `2d88fe1b` → `840ad01d` → `cd9af2af` (revision 4 step (5) repeat: G1 terminal
repair PASS; full step-5 review **NOT ACCEPTED** on the runner→audit→table integration; the
screening note signed; the D.3 G1 launchers merged with reviews R1–R4). `origin/coord/compute` before this report: `b4b33527`. No evidence campaign, no GPU job, no
label/evaluation read this round.

## 1. STOP — screening evidence run (`compute/20261127-22`)

**Result: STOP at the first worker-runtime probe; 0 of 10,164 runs written.** Strict preflight
passed; the scene is kept; no retry, no patch.

- **Cause:** expected `worker_python` `/ceph/dwong/r1_prepare_20261025/venv/bin/python`, observed
  `/ceph/dwong/r1_prepare_20261025/venv/bin/python3`. Prefix, four library versions and the package
  list `a089bbf1…` are equal; both are symlinks to the same interpreter. The probe compares
  `sys.executable` literally, and the launch used `python` while the worker command is `python3`.
- **Scene:** `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1032Z/`
  (manifest `0e811389…`, design `29396f5b…`, empty `lineage_runs.jsonl`, cotenancy `ca179471…`),
  scratch `/tmp/r1_smeas_EVIDENCE_20261127T1032Z` (empty).
- **Deliverable:** `compute-screen-measure-stop-20261127` @ `30781f0b8a65c0653585dbb897a1fde6d3d072eb`;
  record `docs/r1/reports/screen_measure_stop_20261127/SCREEN_MEASURE_STOP_20261127.md` sha256
  `1edf4b30c87417063714cccb48465994a0370cff5621e9367ca1cb1e01910169`.
- **Decision needed (author/coordinator):** re-issue the note/command with the same interpreter name,
  or a reviewed probe change comparing `worker_python_realpath` (environment checks unchanged), then
  a new `SMEAS_EVIDENCE_<stamp>` run. Screening stays unmeasured; the seventh-arm decision is not
  reached.

## 2. Delivered

| Task | Result | Branch / tip | Review |
|---|---|---|---|
| `compute/20261126-02` (+ `cluster/20261126-02`) — D.3 G1 launchers: one chunk argv, HTCondor and direct SSH, job-side hardware probe | **ACCEPTED, merged `cd9af2af`** | `compute-d3-launchers-20261127` @ `ead7375aed06518045384176e72e66ae974a9936` | `compute-d3-launchers-review-20261127` @ `acc43a3a29e0bfc8bb07bd2881af6c1a9d4a6d53` (R4; R1/R2/R3 history) |
| `compute/20261127-23` — D.3 runner→audit→table integration: G7 summary from production records, per-keep G6 audits, table assembly | **ACCEPTED** | `compute-d3-integration-20261127` @ `39df5b9256ce69fad96659ab8217d452bd0211bd` (reviewed code `d8cfd7d0`) | `compute-d3-integration-review-20261127` @ `dc76484d8b09565930da9ba335f53c69c4e5e81f` (R2) |
| `compute/20261127-19` — Ada P.4 probe record review (task 21) | **done, merged** | `compute-p4-ada-probe-20261127` @ `4e51adef`; review `60958144` | merged `ebc28ec0` |

### Launcher unit (`compute/20261126-02`)

- `r1/c3/d3/launch.py`, `probe.py`, `launch_htcondor.py`, `launch_ssh.py`, and a small
  `campaign_chunk.py` entry/end-sampler addition. Both launchers pass the same
  `python -m r1.c3.d3.campaign_chunk --launch … --out … --manifest … --observed …`; the reviewed
  HTCondor request is exact and refuses edits; the SSH launcher takes `gpu<index>.lock` for the whole
  chunk; the job probes the actual card/host (HTCondor records its assigned worker; SSH records the
  leased host).
- **Tests:** 17 new; focused 47 passed; full suite at the accepted tip 114 failed / 5,003 passed /
  163 skipped / 3 errors, the same 117 failure/error ids as base `2d88fe1b` — zero new.
- **Unit record:** `docs/r1/reports/d3_g1_20261127/D3_G1_LAUNCHERS_UNIT_20261127.md` sha256
  `9c457819be1b44e5e0c1934c5919035ab2afd071e74262fc7c578bc36d8ee5e8`.
- **Minor notes (accepted):** per-UUID lease falls back to index 0 (only `gpu<index>.lock` parsed);
  exact SSH host comparison refuses alias/FQDN differences (launch host must equal the probe
  hostname); a few refusal/lease paths are covered by manual checks rather than tests.

### D.3 integration (`compute/20261127-23`)

- G1 now writes the exact `SUMMARY_KEYS` `summary.json` from the ledger/events/recorder captures
  (start/final hashes, `last_keep_run`, mechanism counts, compute fields) and `keeps/keep-<run>.json`
  for every kept incumbent. G6 audits every keep on the declared seeds with the shared cache and
  writes `Y_keep.jsonl` + six-key `g7_rows.jsonl`. A new `assemble.py` builds the G7 table directly
  from production output. G7 and `d3_analysis.py` are byte-identical to the reviewed source.
- **Tests:** seven step-(5) cases through production G1 summary/G6 audit/G7 `build_row`; a full
  882-row table written to the production disk layout, assembled by `assemble.build`, reloaded and
  `D3.analyse`d. Focused: 157 passed + 18 subtests. Full suite at the code tip `d8cfd7d0`:
  **114 failed / 4,988 passed / 163 skipped / 3 errors**, 117 ids; base `840ad01d`: 115 / 4,984 /
  163 / 3, 118 ids — the tip's ids are a strict subset (one base-only TASL GPU-lease timing test),
  **no new failure id**. R2 **ACCEPTED** (remaining minors only).
- **Unit record:** `docs/r1/reports/d3_integration_20261127/D3_RUNNER_AUDIT_TABLE_20261127.md`
  sha256 `28a724e7cdc00cf713017976d771f74d852e68cbd8a6bdf05ac36cdf4b4f426c`.
- **Named placeholders for review:** `infra_attempts = 1` (G7 requires ≥ 1; no retry counter in G1)
  and `proposer_gpu_seconds = 0.0` (the proposer server's card time is not measured per campaign).

## 3. Running elsewhere / blocked

| Item | State at 11:40 UTC | Next check |
|---|---|---|
| Expansion G.1b (`compute/20261126-10`) | ETTh1 sealed 00:34Z, MetaMaze sealed 06:36Z. Forest Cover is in its **joint** part, `out/joint/runs` 79 files, pid **106573** (cpus 4-7). Titanic split 109/150, pid **106578** (cpus 12-15), joint still to start. No STOP. | Seal each on exit; `assemble`/`summarise` after all four. Forest Cover ~2 h, Titanic ~4 h at the observed rates. |
| Houseprice CPU-set (`compute/20261127-15`) | **not run.** The driver waited on `cpus-4-7`; Forest Cover entered joint (~2 h), so I stopped the waiter after 28 min; no run root or sealed run was created (the day's run id is still free). | Rerun `run_cpuset_check.sh` with a new `CAP` after Forest Cover seals; then P11 TASL-2 items. |
| G.5 P11 TASL-2 (`compute/20261127-05`) | **blocked** on the published G.5 note. At `main` `2d88fe1b`, `python3 sweep2/t1_tasl/g5_tasl.py validate sweep2/t1_tasl/g5_tasl_spec.json --launch` returns `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`. TASL-7 part is merged (`ba5f1e4a`, review `f87a17cc`). | Published G.5 note, then C2/C4/C5/C6/C9/C14/C15 pre-run and C11 chunk side. |
| D.3 HTCondor preflight (`compute/20261127-12`) | still **no match**: deepthought2 L40S `Start = false`; TOpAS A100 `175` `Start = false`, `167/179` undefined; two idle `dwong` jobs (`759624/759625`) are not ours. Request not edited. | Watch `condor_status`; do not edit the request. |
| `compute/20261126-06` G.5 campaigns | blocked on the published G.5 note. | note publication. |
| `compute/20261126-09` D.3 per-arm smoke | blocked on revision 4 freeze / the integration review. | merge of `compute/20261127-23`, then rev-4 freeze, then the smoke. |
| P.4 4B re-probe | 4B option A is signed; no task names the re-probe yet. | coordinator priority after the screening STOP. |

**Idle/active capacity:** TASL-2 GPU free (353 MiB, no compute process); TASL-7 GPU free at the last
sample (591 MiB, no compute process); Ada cards 0/2/6/7 empty (1/3/4/5 shared by another user);
deepthought 446 GiB available, no D.3 jobs. Active IDs: TASL-2 pids 106573/106578 (expansion,
CPU-only). The screening run left no process; scratch is empty.

## 4. Decided alone

To stop the houseprice waiter rather than reproduce the known 1-hour helper timeout while Forest
Cover's joint part has ~2 h to run; to leave the expansion untouched and seal only on node exit; to
put the D.3 summary/per-keep work in G1/G6 and a new assembly module, leaving G7/analysis untouched;
to treat the screening `python`/`python3` probe mismatch as a STOP (the note names it) and not retry
it or edit the signed command; to use the seven production cases as the integration test's case
checks while repeating them across the full design only for G7's exact coverage check.

## 5. Next round checks

1. `ssh tasl2 'ps -p 106573,106578'`; on each exit seal the attempt; when all four are sealed run
   `assemble` and `summarise` with the note's spec and report the per-node verdicts and summary sha256.
2. After Forest Cover seals, rerun the houseprice check with a new capture directory; then the P11
   TASL-2 items once the G.5 note is published.
3. Coordinator/author decision on the screening STOP (probe realpath vs command name; the
   coordinator's 12:01 state says the re-issue is with the author, A recommended); then a new
   `SMEAS_EVIDENCE_<stamp>` run. Do not retry the stopped scene.
4. Coordinator merges the integration unit (`39df5b92`; reviewed code `d8cfd7d0`, review
   `dc76484d`); then the local worker repeats revision 4 step (5). The launchers are already merged
   (`cd9af2af`).
5. Watch `condor_status` for a runnable L40S/A100; do not edit the request.

**Task ids this report covers:** `compute/20261126-02`, `compute/20261127-22`, `-23`; `-19` was
already merged. **Reports:** `20261127-19-screen-measure-stop.md`, this round status.
