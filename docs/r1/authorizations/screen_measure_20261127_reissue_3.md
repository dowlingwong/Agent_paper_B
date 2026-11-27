# R1-SCREEN-MEASURE on deepthought2 — third re-issue, published

AI-assisted (Codex, local worker, 28 Nov 2026). The author signed the original note and adopted the companion
pre-declaration on 27 Nov 2026 under R1-SCREEN-MEASURE-SIGNATURE. R1-SCREEN-MEASURE-CHOICES (1)–(9) fixes
the design, with option (a) as primary and all triples reported as secondary.

The author signed the first re-issue under R1-SCREEN-MEASURE-REISSUE after the [worker-runtime STOP](../reports/screen_measure_stop_20261127/SCREEN_MEASURE_STOP_20261127.md).

The author signed the second re-issue under R1-SCREEN-MEASURE-REISSUE-2 after the
[27 November cache STOP](../reports/screen_measure_stop_20261127b/SCREEN_MEASURE_STOP_20261127B.md).
That re-issue and the subsequent deepthought retry scenes remain the records of those attempts.
The first co-tenancy STOP wrote 186 of 10,164 rows with zero failed runs, and R1-SCREEN-COTENANCY-INFRA
classifies the stopped attempts as infrastructure losses. No rows from them enter this analysis.

R1-SCREEN-DEEPTHOUGHT2 moves the full measurement to deepthought2, CPU only, at most 64 CPUs.
The coordinator published this re-issue on 28 Nov 2026 under R1-SCREEN-DEEPTHOUGHT2, which pre-authorises publication of the reviewed note (review `docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md`). The companion
pre-declaration and the design, seeds, run budget, analysis and statistical STOP rules carry over.
Compute confirms the deepthought retry ledger and that the prior attempt has ended before starting a
fresh attempt.

**How it launches.** On deepthought2, from a clean checkout at the exact reviewed `code_commit`,
an ancestor of published main. Use the shared e1-replayed batch environment and harness from
`docs/r1/reports/e1_replay_20261117/pins.json`, with batch wrappers first on `PATH` and
`PYTHONDONTWRITEBYTECODE=1`. The strict preflight checks publication and code provenance, the
original PLAN row and the deepthought2 placement row, the companion and cache hashes, the running
host, the e1 runtime and harness basis, harness equivalence to `a3fedbbd`, and the seed namespace.
The command uses the existing allowed CPU list to bind the whole process tree to 64 logical CPUs.
Preflight checks that affinity, the exact worker count, GPU visibility and free-core headroom. Record
any scheduler or cgroup CPU restriction before starting. During the run the same 60 s co-tenancy
guard uses whole-host capacity and load. The harness edit-set and per-run worker-runtime checks,
and the analysis provenance and completeness checks, still apply.

**Engineering outputs behind the pins** (published on main; ENGINEERING_ONLY):

| File (`results/r1/engineering/screen_measure_20261123/`) | sha256 |
|---|---|
| `design.json` (unchanged by the corrections) | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `power.json` (unchanged; reproduced with the corrected code) | `5d7a5dace40bdb78e734c371ebb7e812ca48cf5e68bc65b3f711f920b6e5a22c` |
| `power_all_triples.json` (the all-triples option, pre-declaration §12 item 1 (d); new) | `5f7ab03faa464c4ee144feddf269f219c7ccc539987d73f1ef6332fd2ac15de9` |
| `compute.json` (unchanged) | `207e6085ce42ddfccd328691fc22c71f51a55ac9d1e02611f047812f91ddfe63` |
| `seed_scan.json` (unchanged; 205 refs, 188 distinct trees; ref-list sha256 `391ddb28…a48a`) | `fb8357a6c0af63a2708057f3181c318f63c9d1f56c0dbee913ab4343d6d43ef5` |
| `dryrun/record.json` (stub dry runs, regenerated) | `84d36bfce0858c7035a83acb956c2bc021d6e9d94467edcc93291b024109e07f` |
| `tests.txt` (63 passed) | `0d7662618df433f9cf355a83e0de0470496e478abd2ed989642c8aa34c1e1cb1` |

## Key block

```
approved: true
label: EVIDENCE
phase: r1_screen_measure
start_ruling: R1-SCREEN-MEASURE
run_id: smeas-20261123-a
labels_read: none
design_sha256: bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8
seed_block: 3301-3420
harness_commit: 6adf3859de66c4814fcf376eed59880fbd8eeaf7
code_commit: a7c2f8fb7b90b3237e61672c6b48112365dcdb24
code_review: docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md
predeclaration: docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_20261127.md sha256 a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585
sha256_screen_design: 3443c044cc8a779a75f46561667dfba744f71e81233f503ca81051c9541791b5
sha256_screen_measure: ae2d1688824ddbeb2b2c5a2e346822000aa3245730b531b0372d6c288ccabf11
sha256_screen_analysis: a54753e1b9cba5cf5605f83d7e53a97d98246aded14b4c97aecb9edc1a2ed089
sha256_screen_seeds: dff8252b46101b695c9a938d722c11f3c68f56fb3c388859350a03e5112f2c4e
sha256_screen_power: 8775c7ffd6e4722a8752aa90b63fde1e91f48db44c3b5652a927c85e078fd5dd
sha256_e1_noise_floor: a3fa508f0c16ec1cfb5b2afa0b37c8cfa6e9b965a8e5d90b6ab6e3c92a830b75
workers: 64
launch_host: deepthought2
data_cache_sha256: 3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07
host: deepthought2 CPUs only (R1-SCREEN-DEEPTHOUGHT2), using the e1 replay basis of R1-SWEEP2-B2-GO: B6 (a) the e1 replay at 52992b22 (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3, uv.lock dd42d018), B4 (a) the per-run worker-runtime probe with its limitation disclosed, B1 (a) authority files from published main; harness 6adf3859 clean with node, config, harness and worker code equal to a3fedbbd (checked at run time); one host for the table
design: 8 T0 nodes; c0, the five E1 single edits and the kept two-edit children, 84 configurations; 120 joint seeds 3301-3420 (train seed = split seed) plus one repeat per configuration at 3301; 10,164 harness runs; testable nodes digits_mlp (18 primary triples) and openml_climate (2); the other six NOT_TESTED by design (pre-declaration §4)
cotenancy: 64 workers bound to 64 eligible logical CPUs, CPU only; before launch host CPUs minus 1-min load minus 64 must be at least 10; during the run host CPUs minus max(0, 1-min load minus our running workers) must be at least 10, sampled every 60 s into cotenancy.log; a breach is a STOP
projection: historical engineering estimate 6.3–11.1 CPU-hours (results/r1/engineering/screen_measure_20261123/compute.json); log achieved concurrency and elapsed time on deepthought2
decision: any decision node SHARED returns to the author for the seventh D.3a arm; otherwise R1-THEORY-RHO (2) is final and D.3 step (8) proceeds on rev 4 (R1-D3-STEP8-HOLD)
P1: PASS - published PLAN on 15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a records R1-SCREEN-MEASURE and R1-SCREEN-DEEPTHOUGHT2 (published at 0bb81e26); the strict launch reads both rows from current origin/main.
P2: PASS - the staged pre-declaration is byte-identical to the reviewed draft at the path and sha256 in predeclaration; initial re-check ACCEPTED in docs/r1/reviews/SCREEN_MEASURE_PREDECL_REVIEW_20261123.md (sha256 637c0a5ed684e3fa9602f2afc078b5194165a6cb70c6b899b5371f9f7b9f3909); later cache and deadline edits accepted in docs/r1/reviews/SCREEN_MEASURE_DATACACHE_REVIEW_20261126.md (sha256 9861bba401d52b2428403580461f80ad8b7cc244166eb9fb2cbdf7124ca5092f). Publication with the signature is required before launch.
P3: REQUIRED AT LAUNCH - exact-code acceptance in docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md for a7c2f8fb7b90b3237e61672c6b48112365dcdb24. The strict launch checks that published review, the six code hashes and the imported code bytes.
P4: PASS - rebuilt cache at /work/dwong/screen_fix_20261127/data_cache_20261127T134927Z; its MANIFEST.json matches docs/r1/reports/screen_cache_rebuild_20261127/captures/cache_MANIFEST.json (sha256 1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21). All six OpenML caches were verified as fixed points under the pinned loader and the four pilot ARFF pins passed. Seed 999 smoke wrote 168/168, failed_runs 0, STOP null, edits verified on all eight nodes; manifest docs/r1/reports/screen_cache_rebuild_20261127/captures/manifest.json (sha256 3c6dd543314aa58b0e5dad266c18769f92c881befe8af9dc17e64f955f44d580), worker runtime docs/r1/reports/screen_cache_rebuild_20261127/captures/worker_runtime.jsonl (sha256 4633b06b663d0f8cd30d7ffea2238e8e75dec1169d613a27f086ff7a32180141), and record docs/r1/reports/screen_cache_rebuild_20261127/SCREEN_CACHE_REBUILD_20261127.md (sha256 800bf884ca2e60234fcd26644655145ebb03b7dfd676257c15263e182fcce8b1). All 168 runtime receipts matched the evidence interpreter and package identity. Independent review docs/r1/reviews/SCREEN_CACHE_REBUILD_REVIEW_20261127.md (sha256 01353a65d3e61f1e5f36aac03b2249aeb06ba9f0b1dfe68ebaa779aa49ea4398), ACCEPTED. The 37 identity flags are identical to the first smoke and the published reading below still applies.
P5: PASS - recorded environment basis B6 (a) docs/r1/reports/e1_replay_20261117/pins.json (sha256 72aff78d92eed58af0e3563e2207cf1ea1981bcd07f99fd4eb1d6b4350fb78f7); P4 smoke reports clean harness 6adf3859 and the pinned numerical library versions. Strict launch checks the environment basis, harness equivalence against a3fedbbd, and worker-runtime probe B4 (a).
P6: PASS - seeds 3301–3420 passed the static namespace check; the reviewed all-refs scan is results/r1/engineering/screen_measure_20261123/seed_scan.json (sha256 fb8357a6c0af63a2708057f3181c318f63c9d1f56c0dbee913ab4343d6d43ef5), with supplementary scans in the P2 review. The block is reserved for this measurement under R1-SCREEN-MEASURE-CHOICES (6) and checked again at launch.
P7: PASS - R1-SCREEN-MEASURE-CHOICES (1)–(9) settled on 23 Nov, recorded in the P1 PLAN snapshot. Option (a) stands. The primary test requires both links to have rho_joint strictly below 0.95; all triples are secondary. Item (5) fixes smeas-20261123-a, and item (9) requires signature on main before launch.
P8: REQUIRED AT LAUNCH - the historical deepthought smoke logged 31.9 free cores (docs/r1/reports/screen_cache_rebuild_20261127/captures/cotenancy.log, sha256 7504a1116ca585e953344ceca3d625c79a7cfc5ed719a5775d5f126be9436374). The strict launch samples deepthought2 independently and requires the 10-core floor after admitting the 64 workers.
```

## P4 identity flags

The [first smoke reading](../reviews/SCREEN_MEASURE_SIGNATURE_REVIEW_20261127.md) covers the same 37 flags below. Equal
metrics at seed 999 are recorded at the configuration-pair level. The analysis
retains its STOP on bit-identical metric vectors across the measurement seeds.

| Node | Count | Configuration pairs | Reading |
|---|---:|---|---|
| `digits_mlp` | 9 | `c1=c0`, `c5=c0`, `c12=c0`, `c12=c1`, `c15=c0`, `c15=c1`, `c15=c5`, `c24=c2`, `c25=c2` | Discrete-metric ties are plausible. The E1 single edits tied at 2–4 of 30 seeds. Child tie rates were unmeasured. |
| `openml_breast_w` | 9 | `c1=c0`, `c2=c0`, `c5=c0`, `c15=c0`, `c15=c1`, `c15=c5`, `c25=c0`, `c25=c2`, `c25=c5` | E1 C and class_weight ties were common (22/30 and 26/30). The flagged children use these edits. |
| `openml_climate` | 0 | None | No flag on any configuration, including the decisive c35 versus c3 comparison. |
| `openml_credit_approval` | 1 | `c15=c1` | The child adds class_weight, which tied at 9/30 E1 seeds at the baseline. |
| `openml_ionosphere` | 1 | `c15=c1` | The child adds class_weight, an E1 near-duplicate link (rho_joint 0.9907) that tied at 3/30 E1 seeds at the baseline. Its child tie rate was unmeasured. |
| `openml_sonar` | 3 | `c5=c0`, `c15=c1`, `c25=c2` | These comparisons add class_weight, which tied at 20/30 E1 seeds at the baseline. |
| `openml_wdbc` | 10 | `c1=c0`, `c2=c0`, `c3=c0`, `c5=c0`, `c15=c0`, `c15=c1`, `c15=c5`, `c25=c0`, `c25=c2`, `c25=c5` | Nine comparisons involve C or class_weight (E1 ties at 9/30 and 16/30). The c3=c0 random-forest comparison also tied at 2/30 repaired E1 joint seeds. This node is descriptive. |
| `tabular_mlp` | 4 | `c4=c0`, `c12=c1`, `c25=c5`, `c45=c5` | The ALPHA edits tied at 5/30 and 11/30 E1 seeds and had nonzero E1 mean differences. The child comparisons add an ALPHA edit. |

## Launch, analysis and outputs

After the coordinator publishes the exact-code review and this note, Compute checks the attempt
ledger, scheduler CPU entitlement, the shared e1 environment and cache visibility on deepthought2.
Record the three thread-limit settings from the command in the launch receipt. Run the command on
that host after those checks. It uses a new UTC stamp for the checkout, output and scratch directories.

```bash
(
  set -eu
  test "$(hostname -s)" = deepthought2
  CODE=a7c2f8fb7b90b3237e61672c6b48112365dcdb24
  DEPLOY=/work/dwong/screen_measure_20261127/paper_c12136d6
  CACHE=/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z
  BATCH=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw
  STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  CHECKOUT="/work/dwong/screen_measure_20261127/paper_dt2_$STAMP"
  OUT="results/r1/screen_measure/SMEAS_EVIDENCE_$STAMP"
  SCRATCH="/tmp/r1_smeas_EVIDENCE_$STAMP"
  test ! -e "$CHECKOUT"
  test ! -e "$SCRATCH"
  test -f "$CACHE/MANIFEST.json"
  git -C "$DEPLOY" fetch origin refs/heads/main:refs/remotes/origin/main
  git -C "$DEPLOY" merge-base --is-ancestor "$CODE" origin/main
  git -C "$DEPLOY" worktree add --detach "$CHECKOUT" "$CODE"
  cd "$CHECKOUT"
  test ! -e "$OUT"
  STATUS=$(git status --porcelain)
  test -z "$STATUS"
  export AR_HARNESS_ROOT="$BATCH/autoresearch_harness"
  export PATH="$AR_HARNESS_ROOT/.venv/bin:$PATH"
  export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
  export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
  unset PYTHONPATH
  test "$(command -v python3)" = "$AR_HARNESS_ROOT/.venv/bin/python3"
  CPUSET=$(python3 -B -c 'import os; print(",".join(map(str, sorted(os.sched_getaffinity(0))[:64])))')
  taskset --cpu-list "$CPUSET" python3 -B -m r1.noise.screen_measure run --evidence \
    --out "$OUT" --workers 64 --tmp "$SCRATCH" --paper-root "$CHECKOUT" \
    --note docs/r1/authorizations/screen_measure_20261127_reissue_3.md \
    --code-commit "$CODE" --code-review docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md \
    --data-cache "$CACHE"
)
```

- **Analysis** (after a run without STOP, from the same checkout and batch environment):
  `python3 -B -m r1.noise.screen_analysis "$OUT" --out "$OUT/analysis.json"` with `OUT` set to the recorded new
  run directory. Use the pre-declared test, B = 2,000. The analysis refuses a table whose SHA-256 differs
  from the manifest, missing preflight or harness/edit-set checks, and configurations with bit-identical
  metric vectors across the measurement seeds (reviews M2, M3).
- **Outputs:** preserve the new run directory and its design, lineage and runtime records, co-tenancy samples,
  manifest and analysis when eligible. Compute reports the attempt stamp, runtime and hashes. The old attempts
  stay in their original directories.

STOPs (each returns to the author, including a deepthought2 co-tenancy STOP; outputs are kept;
nothing is resumed, patched or silently retried):
- before launch: missing or unsigned publication, a key field or hash mismatch, a missing PLAN row or review,
  an environment, host, cache, harness or seed namespace refusal, an edit-set mismatch, an existing output
  or scratch directory, a CPU-affinity or GPU-visibility mismatch, or inadequate co-tenancy headroom.
  A pre-launch refusal raises before the output directory is created (exit status 1; console receipt);
- during the run (manifest written with the reason, exit status 3): a determinism mismatch at seed 3301, or a failed
  run at seed 3301, first run or repeat (`determinism_unverifiable`, review M1); an edit not applied, a pre-applied edit
  missing, a declared value not read back or any other symbol changed by a run; more than 1 % of the planned runs
  failed; a run raising an exception; a worker-runtime probe failure or mismatch (`worker_runtime`, review N2); a
  co-tenancy breach (no deadline: R1-NO-TIMEOUT (1));
- at any time: any label, evaluation, test-partition, sealed or sweep-evidence file opened (none is needed).
