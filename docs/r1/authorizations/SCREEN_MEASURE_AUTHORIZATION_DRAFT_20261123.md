**AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.**

# R1-SCREEN-MEASURE on deepthought — authorization note (direct screening measurement; EVIDENCE) — DRAFT, approved: false

This file is the note in the key-block format that `r1/noise/screen_measure.py` `key_block` parses: the fields are the
`key: value` lines inside the one fenced block under the heading "Key block"; no key may appear twice, every line in that
block must be a field or blank, and a field still holding `<…>` refuses the launch. Prepared by a subagent of the
coordinating chat on branch `mac-screen-measure-20261123` over `author-minsub-20261122` @ `53e2fe41`, to be independently
reviewed together with the pre-declaration `docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md` and
the code it pins (tier E, R1-PROCESS-TIERS).

**On signature** the author copies this file to `docs/r1/authorizations/screen_measure_<YYYYMMDD>.md` with these edits:
- `approved: true`;
- `code_commit` and `code_review` filled with the reviewed code commit and its review;
- `predeclaration` filled with the signed pre-declaration's path (renamed without `_DRAFT`) and its sha256;
- P2–P4 and P7 completed with their citations;

and publishes the note, the signed pre-declaration, the R1-SCREEN-MEASURE row and the reviewed code on `main`. The
runner reads the note, the pre-declaration and PLAN.md from the freshly fetched `origin/main` (R1-B2-GO B1 (a)), so the
operator's checkout of the code commit need not contain them.

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
design; co-tenancy before launch and every 60 s during the run; the per-run worker-runtime probe.

**Engineering outputs behind the pins** (committed on the branch; ENGINEERING_ONLY):

| File (`results/r1/engineering/screen_measure_20261123/`) | sha256 |
|---|---|
| `design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `power.json` | `5d7a5dace40bdb78e734c371ebb7e812ca48cf5e68bc65b3f711f920b6e5a22c` |
| `compute.json` | `207e6085ce42ddfccd328691fc22c71f51a55ac9d1e02611f047812f91ddfe63` |
| `seed_scan.json` (205 refs, 188 distinct trees; ref-list sha256 `391ddb28…a48a`) | `fb8357a6c0af63a2708057f3181c318f63c9d1f56c0dbee913ab4343d6d43ef5` |
| `tests.txt` (37 passed) | `1ae357703a493352273e55d9315c8265d893e7be13c4cc387eea5b9d2f4a4841` |

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
code_commit: <40-hex reviewed code commit>
code_review: <docs/r1/reviews/SCREEN_MEASURE_REVIEW_<date>.md, with Code-Commit and Verdict: ACCEPTED>
predeclaration: <docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_<YYYYMMDD>.md> sha256 <sha256 of the published file>
sha256_screen_design: d5f8b68eac0449e168fae92c095b17bf96a1f30252c844f783d02ffb331add92
sha256_screen_measure: 2aa5b0b98a917474abf4ece8d38e456364dc014cfbb3b0bb97c5987443d04037
sha256_screen_analysis: bb090531c5d762890ccedd375939f7317587c187233d8eea2813456dc9370fda
sha256_screen_seeds: dff8252b46101b695c9a938d722c11f3c68f56fb3c388859350a03e5112f2c4e
sha256_screen_power: 38eaa7c4944f5f3af70fa121bd8abbf4189293c76bcf9ec3d459d6a914254960
sha256_e1_noise_floor: a3fa508f0c16ec1cfb5b2afa0b37c8cfa6e9b965a8e5d90b6ab6e3c92a830b75
workers: 16
deadline_seconds: 10800
host: deepthought CPUs only (R1-SCREEN-MEASURE), in the environment of the sweep-1 B.2 audit under R1-SWEEP2-B2-GO: B6 (a) the e1 replay at 52992b22 as the environment basis (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3, uv.lock dd42d018), B4 (a) the per-run worker-runtime probe with its limitation disclosed, B1 (a) authority files from published main; harness 6adf3859 clean with node, config, harness and worker code equal to a3fedbbd (checked at run time); one host for the table
design: 8 T0 nodes; c0, the five E1 single edits and the kept two-edit children, 84 configurations; 120 joint seeds 3301-3420 (train seed = split seed) plus one repeat per configuration at 3301; 10,164 harness runs; testable nodes digits_mlp (18 primary triples) and openml_climate (2); the other six NOT_TESTED by design (pre-declaration §4)
cotenancy: workers 1-16 and at most this note's value; at least 10 cores left to other users, before launch cpus - 1-min load >= 10, during the run cpus - (load - our running workers) >= 10 sampled every 60 s into cotenancy.log (the convention of docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md); a breach is a STOP
projection: 2,975 s at 16 workers (the sweep-1 B.2 audit's measured throughput on deepthought with the runtime probe; 1,411 s on the E1 D28 deepthought basis); 6.3-11.1 CPU-hours (results/r1/engineering/screen_measure_20261123/compute.json)
decision: any decision node SHARED -> the coordinating chat proposes the seventh D.3a arm of R1-D3-CHOICES (1) before the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) is final (R1-SCREEN-MEASURE)
P1: <PASS or not> - R1-SCREEN-MEASURE published on main (one row, naming deepthought and R1-SWEEP2-B2-GO; checked by the code)
P2: <PASS or not> - pre-declaration independently reviewed and accepted: <review path>; published on main with the sha256 in the predeclaration field
P3: <PASS or not> - code reviewed and accepted at code_commit (<review path>, Code-Commit and Verdict: ACCEPTED), merged to main; the sha256 above equal to the files at code_commit; unit tests r1/tests/test_screen_measure.py pass at code_commit
P4: <PASS or not> - engineering smoke on deepthought (run --engineering-smoke, seed 999, 168 runs, ENGINEERING_ONLY, output outside results/r1/screen_measure/): no STOP, edit sets equal, every edit applied and verified, determinism held; record <path> sha256 <sha256>
P5: PASS when checked by the code - environment basis B6 (a), harness 6adf3859 clean, a3fedbbd objects present in the batch harness repository (as precondition 3 of the sweep-2 B.2 addendum), worker-runtime probe B4 (a)
P6: PASS - seed block 3301-3420 disjoint from every reserved namespace on every ref (results/r1/engineering/screen_measure_20261123/seed_scan.json; checked again by the code at launch)
P7: <PASS or not> - the author has settled pre-declaration §12 items 1-8
P8: PASS when checked by the code - co-tenancy before launch
```

## Launch, analysis and outputs (instructions; not key-block fields, because the stamp is known only at launch)

- **Launch** (on deepthought, as above): `python -B -m r1.noise.screen_measure run --evidence --out results/r1/screen_measure/SMEAS_EVIDENCE_<stamp> --workers 16 --deadline 10800 --tmp /tmp/r1_smeas_EVIDENCE_<stamp> --paper-root <checkout> --note docs/r1/authorizations/screen_measure_<YYYYMMDD>.md --code-commit <code_commit> --code-review <code_review>`.
- **Analysis** (after a run without STOP): `python -B -m r1.noise.screen_analysis results/r1/screen_measure/SMEAS_EVIDENCE_<stamp> --out results/r1/screen_measure/SMEAS_EVIDENCE_<stamp>/analysis.json` — exactly the pre-declared test, B = 2,000;
  it refuses anything else.
- **Outputs:** new directory results/r1/screen_measure/SMEAS_EVIDENCE_`<stamp>`/ (design.json, lineage_runs.jsonl, worker_runtime.jsonl, cotenancy.log, manifest.json with the run table's sha256, then analysis.json); scratch new /tmp/r1_smeas_EVIDENCE_`<stamp>`; committed unchanged by the operator after the run.

STOPs (each returns to the author; outputs are kept; nothing is resumed, patched or silently retried):
- before launch: any field above differing from the run, or still a placeholder; the pre-declaration's sha256, the PLAN
  row or the code review missing or different on `origin/main`; the environment basis, host, harness, untracked-file
  state or harness equality failing; the seed block meeting a namespace; the harness's E1 edits differing from the
  design; the output or scratch directory existing; fewer than 10 cores left to other users;
- during the run: a determinism mismatch at seed 3301; an edit not applied, a pre-applied edit missing, a declared value
  not read back or any other symbol changed by a run; more than 1 % of the planned runs failed; a run raising an
  exception; a worker-runtime probe mismatch; a co-tenancy breach; the deadline (10,800 s);
- at any time: any label, evaluation, test-partition, sealed or sweep-evidence file opened (none is needed).
