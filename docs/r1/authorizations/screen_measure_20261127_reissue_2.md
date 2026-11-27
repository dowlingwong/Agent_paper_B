# R1-SCREEN-MEASURE on deepthought — second re-issue draft

AI-assisted (Codex, local worker, 27 Nov 2026). The author signed the original note and adopted the companion
pre-declaration on 27 Nov 2026 under R1-SCREEN-MEASURE-SIGNATURE. R1-SCREEN-MEASURE-CHOICES (1)–(9) fixes
the design, with option (a) as primary and all triples reported as secondary.

The author signed the first re-issue under R1-SCREEN-MEASURE-REISSUE after the [worker-runtime STOP](../reports/screen_measure_stop_20261127/SCREEN_MEASURE_STOP_20261127.md).

This second re-issue awaits author signature after the [27 November cache STOP](../reports/screen_measure_stop_20261127b/SCREEN_MEASURE_STOP_20261127B.md) at 12:59 CET, with `<reissue2_stamp>` set to a fresh UTC launch stamp distinct from `20261127T1032Z` and `20261127T1155Z`.

The companion is a byte-identical copy of the reviewed draft, with its historical draft wording retained.
After the coordinator publishes both files and the exact-code review on `main`, Compute checks the
publication and runs the strict preflight from `code_commit`.

**How it launches.** On deepthought, from a clean paper checkout at exactly `code_commit` (an ancestor of published
`main`), in the e1-replayed batch venv of the sweep-1 and sweep-2 B.2 audits, with `AR_HARNESS_ROOT` = the e1 batch
harness (`/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`, the
`harness.path` of `docs/r1/reports/e1_replay_20261117/pins.json`, which `audit.replay_environment_checks` requires),
batch wrappers first on `PATH`, `PYTHONDONTWRITEBYTECODE=1`, as in the sweep-2 B.2 addendum's command. The code checks:
this note on `origin/main` with every field below; the pre-declaration's sha256 on `origin/main`; exactly one
R1-SCREEN-MEASURE row on `origin/main` naming deepthought and R1-SWEEP2-B2-GO; the reviewed code commit and its review
(`audit.evidence_paper_provenance`); the environment basis, host, harness and its untracked state
(`audit.evidence_environment`); the harness equality with `a3fedbbd` (`audit.sweep2_harness_equivalence`); the seed block
(`screen_seeds.check_block`); the code sha256 below against the running files; the harness's E1 edit sets against the
design; co-tenancy before launch and every 60 s during the run; the per-run worker-runtime probe. The analysis checks
again, before any statistic, that the run table's sha256 equals the manifest's `runs_sha256` and that the manifest
carries the preflight record, harness `6adf3859` clean and `edit_sets` `equal` on every T0 node (review M2).

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
approved: false
label: EVIDENCE
phase: r1_screen_measure
start_ruling: R1-SCREEN-MEASURE
run_id: smeas-20261123-a
labels_read: none
design_sha256: bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8
seed_block: 3301-3420
harness_commit: 6adf3859de66c4814fcf376eed59880fbd8eeaf7
code_commit: c12136d664ae588a2539b76b2602e36742979ce8
code_review: docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md
predeclaration: docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_20261127.md sha256 a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585
sha256_screen_design: 3443c044cc8a779a75f46561667dfba744f71e81233f503ca81051c9541791b5
sha256_screen_measure: ba05e1a4a1ff5ee643e749e60fbd6e3aa4e6681209ef2f5af940e6cafd4fdb69
sha256_screen_analysis: a54753e1b9cba5cf5605f83d7e53a97d98246aded14b4c97aecb9edc1a2ed089
sha256_screen_seeds: dff8252b46101b695c9a938d722c11f3c68f56fb3c388859350a03e5112f2c4e
sha256_screen_power: 8775c7ffd6e4722a8752aa90b63fde1e91f48db44c3b5652a927c85e078fd5dd
sha256_e1_noise_floor: a3fa508f0c16ec1cfb5b2afa0b37c8cfa6e9b965a8e5d90b6ab6e3c92a830b75
workers: 16
data_cache_sha256: 3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07
host: deepthought CPUs only (R1-SCREEN-MEASURE), in the environment of the sweep-1 B.2 audit under R1-SWEEP2-B2-GO: B6 (a) the e1 replay at 52992b22 as the environment basis (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3, uv.lock dd42d018), B4 (a) the per-run worker-runtime probe with its limitation disclosed, B1 (a) authority files from published main; harness 6adf3859 clean with node, config, harness and worker code equal to a3fedbbd (checked at run time); one host for the table
design: 8 T0 nodes; c0, the five E1 single edits and the kept two-edit children, 84 configurations; 120 joint seeds 3301-3420 (train seed = split seed) plus one repeat per configuration at 3301; 10,164 harness runs; testable nodes digits_mlp (18 primary triples) and openml_climate (2); the other six NOT_TESTED by design (pre-declaration §4)
cotenancy: workers 1-16 and at most this note's value; at least 10 cores left to other users, before launch cpus - 1-min load >= 10, during the run cpus - (load - our running workers) >= 10 sampled every 60 s into cotenancy.log (the convention of docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md); a breach is a STOP
projection: 2,975 s at 16 workers (the sweep-1 B.2 audit's measured throughput on deepthought with the runtime probe; 1,411 s on the E1 D28 deepthought basis); 6.3-11.1 CPU-hours (results/r1/engineering/screen_measure_20261123/compute.json)
decision: any decision node SHARED -> the coordinating chat proposes the seventh D.3a arm of R1-D3-CHOICES (1) before the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) is final (R1-SCREEN-MEASURE)
P1: PASS - one R1-SCREEN-MEASURE row in published docs/r1/PLAN.md at 98c571d22251a9d57a6d157950bd5ac8c340e17b (file sha256 f429bce0b5bed5f8450dcfda278001d4842c5f0f15226b70385376f31a9d69d5), naming deepthought and R1-SWEEP2-B2-GO. Checked again on published main at launch.
P2: PASS - the staged pre-declaration is byte-identical to the reviewed draft at the path and sha256 in predeclaration; initial re-check ACCEPTED in docs/r1/reviews/SCREEN_MEASURE_PREDECL_REVIEW_20261123.md (sha256 637c0a5ed684e3fa9602f2afc078b5194165a6cb70c6b899b5371f9f7b9f3909); later cache and deadline edits accepted in docs/r1/reviews/SCREEN_MEASURE_DATACACHE_REVIEW_20261126.md (sha256 9861bba401d52b2428403580461f80ad8b7cc244166eb9fb2cbdf7124ca5092f). Publication with the signature is required before launch.
P3: PASS - published cache-fix code c12136d664ae588a2539b76b2602e36742979ce8, exact-code review docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md (sha256 594b7dfd2f4317f09e7dda5ca12230bf575f2a7bc0a3639969ed82f71124d524). The six code pins match this checkout and the new smoke manifest. The review independently reproduced 83 screening tests.
P4: PASS - rebuilt cache at /work/dwong/screen_fix_20261127/data_cache_20261127T134927Z; its MANIFEST.json matches docs/r1/reports/screen_cache_rebuild_20261127/captures/cache_MANIFEST.json (sha256 1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21). All six OpenML caches were verified as fixed points under the pinned loader and the four pilot ARFF pins passed. Seed 999 smoke wrote 168/168, failed_runs 0, STOP null, edits verified on all eight nodes; manifest docs/r1/reports/screen_cache_rebuild_20261127/captures/manifest.json (sha256 3c6dd543314aa58b0e5dad266c18769f92c881befe8af9dc17e64f955f44d580), worker runtime docs/r1/reports/screen_cache_rebuild_20261127/captures/worker_runtime.jsonl (sha256 4633b06b663d0f8cd30d7ffea2238e8e75dec1169d613a27f086ff7a32180141), and record docs/r1/reports/screen_cache_rebuild_20261127/SCREEN_CACHE_REBUILD_20261127.md (sha256 800bf884ca2e60234fcd26644655145ebb03b7dfd676257c15263e182fcce8b1). All 168 runtime receipts matched the evidence interpreter and package identity. Independent review docs/r1/reviews/SCREEN_CACHE_REBUILD_REVIEW_20261127.md (sha256 01353a65d3e61f1e5f36aac03b2249aeb06ba9f0b1dfe68ebaa779aa49ea4398), ACCEPTED. The 37 identity flags are identical to the first smoke and the published reading below still applies.
P5: PASS - recorded environment basis B6 (a) docs/r1/reports/e1_replay_20261117/pins.json (sha256 72aff78d92eed58af0e3563e2207cf1ea1981bcd07f99fd4eb1d6b4350fb78f7); P4 smoke reports clean harness 6adf3859 and the pinned numerical library versions. Strict launch checks the environment basis, harness equivalence against a3fedbbd, and worker-runtime probe B4 (a).
P6: PASS - seeds 3301–3420 passed the static namespace check; the reviewed all-refs scan is results/r1/engineering/screen_measure_20261123/seed_scan.json (sha256 fb8357a6c0af63a2708057f3181c318f63c9d1f56c0dbee913ab4343d6d43ef5), with supplementary scans in the P2 review. The block is reserved for this measurement under R1-SCREEN-MEASURE-CHOICES (6) and checked again at launch.
P7: PASS - R1-SCREEN-MEASURE-CHOICES (1)–(9) settled on 23 Nov, recorded in the P1 PLAN snapshot. Option (a) stands. The primary test requires both links to have rho_joint strictly below 0.95; all triples are secondary. Item (5) fixes smeas-20261123-a, and item (9) requires signature on main before launch.
P8: PASS - recorded smoke start had 31.9 of 40 cores available to other users, load1 8.1 and zero study workers; docs/r1/reports/screen_cache_rebuild_20261127/captures/cotenancy.log (sha256 7504a1116ca585e953344ceca3d625c79a7cfc5ed719a5775d5f126be9436374). Strict launch rechecks the current 10-core margin.
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

## Launch, analysis and outputs (instructions; not key-block fields, because the stamp is known only at launch)

- **Launch** (on deepthought, as above): `python3 -B -m r1.noise.screen_measure run --evidence --out results/r1/screen_measure/SMEAS_EVIDENCE_<reissue2_stamp> --workers 16 --tmp /tmp/r1_smeas_EVIDENCE_<reissue2_stamp> --paper-root <checkout> --note docs/r1/authorizations/screen_measure_20261127_reissue_2.md --code-commit c12136d664ae588a2539b76b2602e36742979ce8 --code-review docs/r1/reviews/SCREEN_MEASURE_CACHE_LAYOUT_REVIEW_20261127.md --data-cache /work/dwong/screen_fix_20261127/data_cache_20261127T134927Z`.
- **Analysis** (after a run without STOP): `python -B -m r1.noise.screen_analysis results/r1/screen_measure/SMEAS_EVIDENCE_<reissue2_stamp> --out results/r1/screen_measure/SMEAS_EVIDENCE_<reissue2_stamp>/analysis.json` — exactly the pre-declared test, B = 2,000;
  it refuses anything else, including a table that does not match the manifest's `runs_sha256`, a manifest without the
  launch record (preflight, harness `6adf3859` clean, edit sets equal), and two configurations of a node with
  bit-identical metric vectors (a STOP; review M2, M3).
- **Outputs:** new directory results/r1/screen_measure/SMEAS_EVIDENCE_`<reissue2_stamp>`/ (design.json, lineage_runs.jsonl, worker_runtime.jsonl, cotenancy.log, manifest.json with the run table's sha256, then analysis.json); scratch new /tmp/r1_smeas_EVIDENCE_`<reissue2_stamp>`; committed unchanged by the operator after the run.

STOPs (each returns to the author; outputs are kept; nothing is resumed, patched or silently retried):
- before launch: any field above differing from the run, or still a placeholder; the pre-declaration's sha256, the PLAN
  row or the code review missing or different on `origin/main`; the environment basis, host, harness, untracked-file
  state or harness equality failing; the seed block meeting a namespace; the harness's E1 edits differing from the
  design; the output or scratch directory existing; fewer than 10 cores left to other users. These raise before the
  output directory is created: exit status 1 and no manifest (the console output is the record; review N1);
- during the run (manifest written with the reason, exit status 3): a determinism mismatch at seed 3301, or a failed
  run at seed 3301, first run or repeat (`determinism_unverifiable`, review M1); an edit not applied, a pre-applied edit
  missing, a declared value not read back or any other symbol changed by a run; more than 1 % of the planned runs
  failed; a run raising an exception; a worker-runtime probe failure or mismatch (`worker_runtime`, review N2); a
  co-tenancy breach (no deadline: R1-NO-TIMEOUT (1));
- at any time: any label, evaluation, test-partition, sealed or sweep-evidence file opened (none is needed).
