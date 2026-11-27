# Independent review — Expansion G.1b four-node result (`compute/20261126-10`)

**Verdict: NOT ACCEPTED.** The captures, hashes, note/spec binding and all D21 numbers check out; one material
correction is required. The report denies G.5 entry on a D21 ground that the pinned rows do not use (finding B1).
It does not overclaim a join and it does not hide the negative result — the defect is the opposite one.

Reviewer: independent session, no part in producing the deliverable. Reviewed branch
`compute-expansion-g1b-20261127` @ `2ef8e436bba935702f8afe4b6c701af417a45ec0` (one commit over
`origin/main` `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`; adds only the five files under
`docs/r1/reports/g1b_x_20261127/`), read-only against TASL-2. I did not write to the deliverable branch, the sealed
root or the assembly root, and I opened no label or evaluation row.

## 1. Hashes — report claims against the branch

All sha256 values claimed in the report's assembly table were recomputed from the branch blobs:

| File | sha256 (branch) | Report claim |
|---|---|---|
| `G1B_X_RESULT_20261127.md` | `8515e5427444394e77ebd39d82ebb22992bc859610f089c340a594bf7f916cfb` | (self, not claimed) |
| `summary.json` | `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` | same |
| `ASSEMBLY.json` | `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077` | same |
| `edits.json` | `5ad8f6ad2aa4b02d605a8f0e8d20301870b2460f475e493cd05bc1105df26f5c` | same |
| `SEAL_RECEIPT_titanic.json` | `13773f1541b2d84cb5545fb80601babf6e087ae9b535cc50849870c03de00207` | same |

The four `job_record_sha256` values in the report's table (`e1bc3229…`, `6d9a0ad8…`, `2c50d59a…`,
`ac23a7c1…`) and the four seal-receipt values (`897fadba…`, `2940254a…`, `96dad194…`, `13773f15…`) all match the
live sealed tree (section 5). The `runs.jsonl` digest `c23dec91…` claimed in the report matches the live assembly
`runs.jsonl`. `summary.json`'s `assembly_sha256` equals the `ASSEMBLY.json` file digest.

## 2. `summary.json` against `ASSEMBLY.json`

- `run_id` is `g1b-x-tasl-20261126-a` in both.
- The four jobs are exactly `mlgym_metamaze`, `gc7rc_forestcover`, `gc7rc_etth1`, `mlgym_titanic` (set-equal to the
  summary's four verdicts), each `attempt: 1`, `stop_class: null`, `infrastructure_attempts_not_used: []`, and each
  job's `spec_sha256` is `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`.
- `ASSEMBLY.json` does not itself carry run counts or start times, so the "460 runs each / zero divergent" claim
  cannot be checked from it alone. It is correct, but only against the live job records: all four read
  `expected 460, written 460, successful 460, divergent 0`, and all four `started_utc` are `2026-11-26T22:53:27Z`
  (section 5). No divergence in the summary either (`divergent.rows = 0` and every `by_config` count 0).
- `screening_funnel` is `measured 4, qualified 0, failed_determinism 0`, as reported.

## 3. D21 verdicts — report against `summary.json`

Recomputed each verdict from the summary fields, using the pinned constants in `sweep2/g1b/g1b_lib.py`
(`SEEDS_PER_CONDITION = 30`, `D21_MIN_MATERIAL_EDITS = 2`, `D21_MIN_EFFECT = 0.002`,
`D21_MIN_MEAN_P_WRONG = 0.10`) and the summary's own `checks`:

| Node | n_material / 4 | mean P(wrong) (full) | σ_joint (full) | Summary `checks` | qualifies |
|---|---|---|---:|---|---|
| `mlgym_metamaze` | 3 | `0.024397228859466213` | `1.5079643556876912` | seeds T, ≥2 T, P≥0.10 F, σ>0 T | false |
| `gc7rc_forestcover` | 4 | `0.04986125834617813` | `0.0012512664577442553` | seeds T, ≥2 T, P≥0.10 F, σ>0 T | false |
| `gc7rc_etth1` | 3 | `0.09274020061373567` | `0.011064208240159312` | seeds T, ≥2 T, P≥0.10 F, σ>0 T | false |
| `mlgym_titanic` | 0 | `NaN` | `0.026066300845450183` | seeds T, ≥2 **F**, P≥0.10 F, σ>0 T | false |

The report's rounded values (3/4, 0.0244, 1.5080; 4/4, 0.0499, 0.001251; 3/4, 0.0927, 0.01106; 0/4, NaN, 0.02607)
round correctly from these, and its "deterministic yes / divergent 0 / qualifies no" columns match. The Titanic NaN
is the rule's own behaviour (`d21_qualify` returns `nan` when no material edit has a finite `p_wrong`), and the report
states it as "NaN (no material edit)" — exactly right. The report's "misses by 0.0073" for ETTh1 is
`0.10 − 0.0927402 = 0.0072598`, correctly rounded. Median wall times also match: 59.684, 98.2685, 12.764, 151.379 s.

## 4. Note and spec pin

- `docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` on `origin/main`: sha256
  `16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539` — the report's value; the note reads
  `approved: true`, `label: ENGINEERING_ONLY`, `labels_read: none`, `run_id: g1b-x-tasl-20261126-a`, and
  `spec_sha256: d0dce058…`.
- `sweep2/t1_tasl/g1b_tasl_x_spec.json` on `origin/main` hashes to exactly
  `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`. `g1b_lib`'s job records bind the same value.
- The note's `paper_commit` is `e81e0a34ce97dade1e79027a0ea8c86b277e6f7e`; the report's launch checkout
  `7d0279d8a677582f4f6e5892461bf7138e78fd66` is an ancestor of `origin/main`, and its diff against
  `e81e0a34` outside `docs/` and the spec file is empty — i.e. it is the docs-only launch commit the note's launch
  rule allows. The note was published at 22:47 UTC and the jobs started at 22:53 UTC, so the "note on main before
  launch" ordering holds.
- `ASSEMBLY.json` also carries `spec_json_sha256 = 0fc29a2e…` (the canonical-JSON digest, a different field from
  the file digest). The report quotes only `spec_sha256`; that is correct, but the two should not be conflated.

## 5. Live read-only check (TASL-2)

`ssh tasl2` succeeded. I used only `ls`, `sha256sum`, `wc -l`, and the metadata files `SEAL_RECEIPT.json` /
`job_record.json`; no `out/runs.jsonl` row or label table was opened.

- `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/`: `ASSEMBLY.json` `b4c90ec6…`, `edits.json`
  `5ad8f6ad…`, `summary.json` `67355b66…`, `runs.jsonl` `c23dec91…` (1,840 lines = 4 × 460).
- `/home/dowling/r1_tracks/t1_tasl_x/sealed_g1b/g1b-x-tasl-20261126-a/<node>/attempt-1/`: all four
  `SEAL_RECEIPT.json` and `job_record.json` digests match the report's table exactly.
- Job records: `runs = {expected 460, written 460, successful 460, divergent 0}`, `stop = null`,
  `stop_class = null`, `device = cpu`, `hostname = TASL-2`, `spec_sha256 = d0dce058…` for all four; started
  `2026-11-26T22:53:27Z`; CPU sets 0-3, 4-7, 16-31, 12-15 as reported; Titanic sealed `2026-11-27T18:31:03Z`, the
  other three on 27 Nov (00:37, 07:05, 15:29), consistent with "Titanic was the last node".

## Findings

### B1 (blocking) — the G.5 consequence is stated backwards

The report says: "No expansion node qualifies under D21, so no node joins G.5 through an S9 addendum. G.5's
eligible set is unchanged; the seven primary T0 nodes and the existing G.5 table are unaffected." That is not what
the pinned rows say:

- **R1-T1-D21-SCOPE** (PLAN §10): "D21 does not select T1 nodes for C3: every T1 node that passed U2, G.1b
  fixed-seed determinism and, where run, the cross-host check enters G.5 … regardless of its D21 value; no other
  threshold is introduced."
- **R1-T1-NODE-EXPANSION**: "A candidate whose G.1b completes with determinism PASS by 2 Dec 2026 enters G.5 under
  R1-T1-D21-SCOPE."
- **R1-G5-EXPANSION-JOIN** and **R1-G5-S9 (3)**: each joining node enters by an addendum note "once its G.1b
  completes with determinism PASS".
- The note this report cites says the same in its own `cutoff:` line (stop null + determinism PASS → G.5 addendum),
  and the runbook §2 order 2B that the report cites says "Passing expansion nodes join by addendum under S9."
- `docs/r1/proposals/G5_EXPANSION_ADDENDUM_TEMPLATE_20261127.md` names these exact four nodes: `mlgym_titanic` and
  `mlgym_metamaze` enter the arms and primary gate, `gc7rc_etth1` and `gc7rc_forestcover` are labelled descriptively.
- Precedent: in the official seven-node G.1b assembly (`docs/r1/reports/g5_rel_t1_g1b_20261126/seven/summary.json`)
  5 of 7 nodes do not qualify under D21, yet all are G.5 nodes; D21 is funnel reporting, not a gate.

All four expansion nodes have `stop: null` and determinism PASS. Under the pinned rows they are therefore
*eligible* and enter G.5 by addendum (subject to the addendum switch/reader and its publication, not to D21). The
sentence also labels the primary set "the seven primary **T0** nodes"; the seven-node assembly is **T1**, and the
G.5 table is extended by the addenda, not unaffected.

This is the opposite of an overclaim: the report declines an entitlement the plan grants. It needs a corrected
"What happens next" (and the corresponding opening sentence) that (a) reports D21 as the funnel statistic it is,
(b) states that the four nodes are eligible to join G.5 by addendum with determinism PASS, naming the two MLGym
nodes for the arms/gate and the two 1GC nodes as descriptive, and (c) does not claim G.5 eligibility is unchanged.
If the coordinator instead intends D21 to gate entry, that is an author/PLAN decision (§10 row) and must be recorded
before the report asserts it; the report as written cites no such row.

### Minors (fix or note in a correction round; none changes a number)

1. **`summary.json` is not strict JSON.** `mean_p_wrong_material` for Titanic is a bare `NaN`
   (`g1b_lib.summarise` writes `json.dumps(..., default=str)` with `allow_nan=True`). Python and `jq` accept it;
   Node/RFC-8259 parsers reject it. The file digest is bound, so do not hand-edit it — either keep it and say
   "Python-JSON with NaN" in the report, or fix the writer for future runs.
2. **Missing provenance header.** The report has task and launch commit but no base `origin/main` commit, branch name,
   checkout path, or the usual AI-assisted line. Recent reports carry these; add them in the correction.
3. **"bit for bit" is too strong.** `determinism_check` compares the `("ok", metric)` outcome tuple, not raw output
   bits; "each repeat returns the same outcome and metric" is exact.
4. **"R1-STEP-ORDER step 1 is now complete".** R1-STEP-ORDER (1) is the list of withdrawn date rules; the
   node-set rule is (2)(a). Retarget the citation.
5. **Pre-attempt launch refusals are not mentioned.** The run-root logs show one refused launch per node at
   `22:52:49Z` ("origin … is not the spec's paper repository"), then the successful launch at `22:53:26Z`. It created
   no attempt and used up nothing, so "Attempt 1" and "nothing resumed" remain true; one sentence of disclosure
   would make the record complete.
6. **The 460/460 and start-time claims are not captured in the branch.** `ASSEMBLY.json` has no run counts or
   `started_utc`; those facts are only in the live `job_record.json`. Consider capturing the four job records (or a
   counts line) with the report, as was done for the Titanic receipt.
7. **Only the Titanic seal receipt is captured.** The other three receipt digests in the report are correct (I
   checked them live) but are not reproducible from the branch. Capture all four, or state that the three are
   live-only.

### Observations (no action required)

- `summary.json`'s `gpu_model` reads "NVIDIA GeForce RTX 4090" although every device is `cpu` and every
  `gpu_uuid` is null; it is the spec's constant. The report does not repeat it, but a reader of the summary could be
  misled.
- The note's heading still says "(draft, approved: false)" while its machine line is `approved: true`;
  `check-note-x` reads the machine line and passes. Cosmetic, on `main`, outside this branch.
- The "Decided alone" line is appropriate: it claims only the sequencing of seal → assemble → summarise after
  Titanic's rc 0 and its 460/460 written runs, and "no run was resumed or edited", which the single attempt per node
  supports. One nit: "at the note's pin" conflates `paper_commit e81e0a34` with the docs-only launch checkout
  `7d0279d8`; name both.

## What I could not verify

- The task id `compute/20261126-10` (task board not in this repository).
- The actual paper checkout commit used on TASL-2: `job_record.json` binds `spec_sha256` and the harness commits but
  not a paper checkout commit, and no paper checkout sits under `/home/dowling/r1_tracks/t1_tasl_x/`. The reported
  `7d0279d8` is consistent with the note's launch rule but not bound by the capture.
- The note bytes used at launch: the job record carries `note_rule` but no note sha; I verified the published note
  on `main`, not the file the launcher read.
- Re-derivation of D21 from the raw run rows: I did not open `runs.jsonl` or any sealed outcome row. The summary is
  internally consistent with the pinned rule and matches the report; an independent recomputation from the rows
  remains the one check not done here.
