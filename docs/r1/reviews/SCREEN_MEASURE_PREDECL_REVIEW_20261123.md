**AI-assisted (Claude, independent reviewer subagent, 23 Nov 2026).** Tier E review (R1-PROCESS-TIERS). I did not write
the material reviewed.

# Review: R1-SCREEN-MEASURE pre-declaration, authorization note and code (drafts)

**Branch** `mac-screen-measure-20261123`, head `41d4e993` (base `author-minsub-20261122` @ `53e2fe41`). **Reviewed:**
`docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md` (below "PD"),
`docs/r1/authorizations/SCREEN_MEASURE_AUTHORIZATION_DRAFT_20261123.md` ("AN"), `r1/noise/screen_design.py`,
`screen_measure.py`, `screen_analysis.py`, `screen_seeds.py`, `screen_power.py`, `r1/tests/test_screen_measure.py`,
`results/r1/engineering/screen_measure_20261123/`. **Context read:** PLAN rows R1-SCREEN-MEASURE, R1-D3-CHOICES,
R1-PROCESS-TIERS, R1-E1-PILOT-ACCEPT, R1-SWEEP2-B2-GO, R1-THEORY-RHO (`author-minsub-20261122`);
`SCREENING_TEST_20261122.md` (`mac-screening-test-20261122`); `D3_PREDECLARATION_DRAFT_20261122.md` and
`r1/c3/d3_analysis.py` (`mac-d3-predecl-20261122`); `T4_FEEDBACK_PROPOSER.md` §5 (on `main` and on
`mac-theory-rho-20261122`). Nothing was run on a remote host; no smoke and no measurement was started; no sealed,
label, evaluation or test file was opened.

## Verdict: accepted after minor corrections

No finding blocks signing. Seven MINOR findings must be fixed (M1–M3 and M7 change code, so the pins of PD §11 and AN
change with them); the NITs are optional. The design is sound: the statistic, the resampling unit, the decision rule
and the power figures check out, and every number I re-derived matches the committed files, except the one range in
N3.

## Findings

### M1 (MINOR) — a failed run at the determinism seed is neither a STOP nor declared, and voids the analysis

- **Where.** `screen_measure.py` lines 320–335 (`handle`): a failed run (no metric or non-finite) is counted and
  returns before the determinism comparison, so a failed first-seed or repeat run at 3301 never STOPs.
  `screen_analysis.py` lines 287–289 (`table`): if either run at 3301 failed, the whole table is refused with
  "STOP: determinism check failed". PD §6.6 (lines 247–252) says failing seeds are dropped for the node and that a
  *mismatch* is a STOP; it says nothing about a failure at 3301.
- **Effect.** One transient failure among the 168 first-seed and repeat runs lets the run finish (about 50 min) and
  then makes it unanalysable, under a STOP label the runner never recorded.
- **Fix.** In `handle`, treat a failed run whose key is a repeat key as a STOP (for example
  `determinism_unverifiable <node> <config>`). Declare it in PD §6.6, PD §9 item 1 and the AN STOP list, and add a unit
  test.

### M2 (MINOR) — the analysis does not bind the run table to its manifest

- **Where.** `screen_analysis.py` `load_run`, lines 225–252. The runner writes `runs_sha256` into the manifest
  (`screen_measure.py` lines 397–398), but the analysis never compares it with the table it reads. In evidence mode it
  also does not check that the manifest carries the preflight record, harness commit `6adf3859` (clean), and every
  `edit_sets` entry `equal`. PD §6.7 lists what the script refuses; these checks are not on the list.
- **Effect.** The link between the evidence run and the analysed table rests on the operator alone.
- **Fix.** Refuse if `runs_sha256` is missing or differs from the table. In evidence mode, also refuse unless
  `preflight` is present, `harness.commit` = `6adf3859…` with `dirty` false, and all `edit_sets` values are `equal`.
  Add these refusals to PD §6.7 and to the tests.

### M3 (MINOR) — nothing checks that two configurations of a node are really different runs; one wrong activity key gives a false SHARED

- **Where.** The `identical_to` rule (`screen_design.py` lines 159–175) relies on the D25 active keys
  (`r1/c3/features.py` lines 70–90). `triple_partial` (`screen_analysis.py` line 85) detects identical members only
  *within* one triple.
- **The case that matters: `class_weight` under `random_forest` on `openml_climate`.** Suppose that key were inert in
  the node code at `6adf3859`. Then c35 ≡ c3. Triple c0>c3>c35 would be excluded (identical members), but c0>c5>c35
  would become the sibling triple (c0, c5, c3).
  - Its population partial under the kernel null (s = 0, product kernel, the design's E1 values 0.4741 and 0.8639) is
    **0.262** (my computation).
  - My simulation of that case (independent code, 200 replicates, B = 1,000; `activity_risk.py`, described below)
    gives **P(SHARED on climate) = 0.455**. That false SHARED would trigger the seventh-arm proposal.
- **Is the D25 map wrong?** Very likely not. A committed copy of the OpenML template
  (`results/r1/pilot/E1b_20261013T090510Z/interrupted_provenance/work/roots/openml_ionosphere__s103/node/benchmark.py`,
  lines 223–248, an older harness) passes `class_weight` to `RandomForestClassifier`, not to
  `GradientBoostingClassifier`, and `C` only to `LogisticRegression`. But nothing checks this at `6adf3859`.
- **The rule's reason is also understated.** PD §3 (lines 79–80) and the module docstring (lines 16–18) say an
  identical child "would add only identical vectors". In fact the rule is needed for validity: a child equal to a
  single edit turns a lineage into a sibling triple, whose partial is not zero under the null.
- **Fix.** In the analysis, refuse (a declared STOP) if two configurations of a node have bit-identical vectors over
  the complete seeds. In the engineering smoke, flag any child whose seed-999 metric is bit-identical to a parent's or
  to c0's (one seed cannot prove a difference, but an identity is a strong signal). State the validity reason in PD §3.

### M4 (MINOR) — the primary-triple restriction departs from the row's test, and the draft does not say so

- **The row's test.** R1-SCREEN-MEASURE adopts "the test of that report (pooled partial correlation …)". That report
  pools every eligible triple of a node (`SCREENING_TEST_20261122.md` §2.2, "Pooling within a node", and §4.2,
  "Analysis").
- **The draft's test.** It pools only the primary triples (PD §6.1 item 4, line 204; `node_test(select="primary")`).
  PD §6.3 cites the row for the verdict. The both-links rule appears only among the "proposed values with no row" (PD
  §12 item 5, lines 419–420), and the PD §1 table (line 31) presents the test as fixed by the row.
- **Effect.**
  - `digits_mlp`: nothing changes; all 18 triples are primary.
  - `openml_climate`: 2 of its 6 triples are kept.
  - The six other nodes become NOT_TESTED instead of entering the test with all their triples.
- **The choice itself is defensible and was made before any data.** Under the kernel every lineage partial is 0, so
  restricting the set cannot raise the false-SHARED rate; under the u + w model it raises power. It was fixed from E1
  values alone, in design commit `ba69ac1d`, before any measurement exists. Still, the author would be signing a test
  that departs from the row.
- **Fix.** State the departure in PD §1, §6.1 and §12 (item 1 or 5): "departs from the row's test, which pools all
  eligible triples; the all-triples reading is reported as secondary". Offer the all-triples primary test as an
  explicit alternative for the author.

### M5 (MINOR) — the argument for the both-links rule claims more than its model gives

- **(a) "Whatever the truth" is too strong.** PD §4 (lines 138–139) says the six nodes "could return NO_SHARED but not
  SHARED, whatever the truth". That holds only under the u + product-kernel model, and only at small shares.
  - The PD §4 table itself shows a `tabular_mlp` triple at 0.120 at s = 0.7891.
  - At the largest node-wide share consistent with E1 (s = 0.8783 on `tabular_mlp`), one triple (c0>c5>c15) reaches
    0.231 (my computation).
  - What does hold (my computation): with one node-wide share s at most the smallest E1 ρ of the node's links, the
    pooled all-triples mean is at most 0.052 on `tabular_mlp` and at most 0.013 on each of the five OpenML nodes.
- **(b) "Tends to 0" needs a qualifier.** PD §4 (line 121) and `screen_design.py` (docstring, lines 23–27) say the
  partial tends to 0 as either link's correlation tends to 1. This holds at a fixed share s below that link's ρ. If the
  shared component itself makes a link near-duplicate (s close to ρ), the partial does not vanish: for example 0.407
  for `openml_breast_w` c0>c5>c15 at s = 0.9991, a share that the node's other E1 values exclude. The exact form (my
  derivation, which matches the design's `reference_partial` to 5·10⁻⁷ on all 72 triples) is
  ρ(c, g | p) = [s/(1 − s)]·√(t_gp·t_pc), with t = (1 − ρ)/(1 + ρ), for ρ_gp, ρ_pc ≥ s.
- **(c) Name the model.** The model is the u + w model of the screening report §2.1. It is not T4 §5's u + v model
  (`mac-theory-rho-20261122`, "Scope of Corollary 9a": v fresh per run, so every pair of configurations has correlation
  ϱ). Under u + v a near-duplicate link means ϱ ≥ 0.95, and every triple's partial is ϱ/(1 + ϱ) ≈ 0.49. A single ϱ
  cannot reproduce E1's spread within a node (`digits_mlp` 0.5995–0.8551), which is why the extension is needed. The
  text should say this, so that "not tested by design" is not read as model-free.
- **Fix.** Replace the sentence in (a) with the computed statement and name the model as in (c). In PD §10 keep "not
  tested by design (no lineage of two non-near-duplicate edits)": that is a design fact and is accurate.

### M6 (MINOR) — the seed-disjointness claim is too broad

- **Where.** PD §5 (line 190) and AN P6 (line 77) say the block is disjoint from every seed namespace on every ref.
- **The declaration the claim misses.** Paper C's seed registry (`paperC/src/paperc/seeds.py`) is on
  `paperc-build-20261115`, `paperc-esyn-scaling-20261122`, `paperc-plan-amend-20261119` and two remote branches. It
  registers Paper B's noise-floor seeds as `SEED_BASE + s` with declared domain `COUNT_DOMAIN = 1000` (lines 59,
  154–155, 360). The joint block is therefore registered as [3001, 4001), which contains 3301–3420.
- **Why this is not a collision.** That is Paper B's own E1 joint-seed namespace, the protocol this measurement reuses,
  and no run has used 3301–3420 (my supplementary scans, under "Verified" below).
- **Why the scan missed it.** The scan's REACH pattern (`screen_seeds.py` line 72: integers 3031–3420 on lines
  mentioning "seed") cannot see a declaration of the form base + domain.
- **Fix.** Qualify PD §5 and AN P6: the block is disjoint from every seed used and from every reserved block, and lies
  inside the noise-floor domain that Paper C's registry declares for Paper B. Add to PD §12 item 6 that Paper C's
  registry should list 3301–3420 explicitly, or narrow the noise floor's declared domain, so that a future E1 run with
  more than 300 joint seeds cannot reach the block.

### M7 (MINOR) — the runner's STOP paths and the evidence preflight have no unit tests

- **What is untested.** In the test file the stub runs never fail. No test covers:
  - in `execute`: the failure-fraction STOP (`screen_measure.py` lines 323–327), the run-exception STOP (389–391), the
    determinism STOP (332–335), the deadline (362–364, 377–379) or the co-tenancy breach (338–346);
  - `preflight_evidence` (257–306): a placeholder, a field mismatch, the workers bound, the pre-declaration sha256, the
    PLAN row count.
- **Why it matters.** The engineering smoke exercises only the success path, and this is tier-E code that computes
  every STOP.
- **Fix.** Add tests with a fake `run_fn` (in-process and through the pool), a monkeypatched `cotenancy` and a stubbed
  `audit`, and regenerate `tests.txt`.

### NITs

- **N1.** PD §9 (lines 351–354) says each STOP "writes the manifest with its reason and exits 3". A pre-launch STOP
  instead raises `RunStop`, `ValueError` or `SystemExit` before the output directory exists (`screen_measure.py`
  194–209, 257–306, 437–472): exit status 1 and no manifest. Say so.
- **N2.** A worker-runtime mismatch raises inside the run (`r1/c3/audit.py` 210–215), so it is recorded as
  `run_exception …`, not under its own reason (PD §9 item 5). Either record it under its own reason or state this.
- **N3.** PD §8.1 (line 313), basis A, says "per node 0.82–0.97 s". The 0.97 is `openml_qsar_biodeg` (0.974 s), not
  a T0 node. Over the T0 nodes measured in that run, the means are 0.815–0.914 s (`compute.json`).
- **N4.** PD §4 (lines 145–146) says the six nodes' edit sets "hold at most one non-near-duplicate symbol".
  `openml_ionosphere` has `C ×2` at 0.9244 besides `model_type`; it is untestable because `C` is inactive under a tree
  model. Suggested wording: "no two non-near-duplicate edits combine into a distinct child".
- **N5.** `screen_analysis.py` 142–144: a resample in which every eligible triple is undefined is dropped without
  being counted, so the interval is then taken over fewer than B means. Count and report such resamples.
- **N6.** `screen_measure.py` 451: the smoke manifest records `seeds` = 3301–3420 although the smoke runs at 999
  (recorded under `seeds_smoke`). Record 999 in `seeds` for the smoke.
- **N7.** The scan searches no `*.jsonl`, no `*.csv` and no JSON outside the five name patterns (`screen_seeds.py`
  73–74). Its grep did read non-excluded operational records, for example
  `docs/r1/reports/b1_d_20261113_evidence/completion_usage.txt`; that directory holds no evidence marker, label,
  evaluation or test file. State this coverage in PD §5. My supplementary scans (below) found no use of the block.
- **N8.** The report's §4.2 expected "about 4–8 children" per OpenML node; exact activity gives 3. One sentence in PD
  §3 keeps the claim "design as recommended there" transparent.
- **N9.** PD §8.2 (line 323) says "every condition is checked by code at launch". That is true for the row's
  conditions. The scratch and Ceph monitoring of the B.2 addendum is not replicated (each run's scratch is a per-run
  `/tmp` directory, removed afterwards). Say so.

## The drafter's eight points

1. **Partial correlation and the both-links rule.** Verified in algebra and code (closed form in M5). With
   exchangeable links (a = b = 0) the partial is s/(1 + s). With one link at 0.95, the other at 0.82 and s = 0.7082 it
   is 0.1222, as PD §4 says. `build_node` sets `primary = not (near_gp or near_pc)`, failing closed on a missing ρ. The
   design regenerates byte-identically: 18 primary triples on `digits_mlp`, 2 on `openml_climate`, 0 elsewhere.
   Caveats: M4 and M5.
2. **Seeds.** Verified, with the qualification in M6.
   - The static check passes, and the D.3 blob `b20cf020` is still current at that branch's head `a4053eac`.
   - The sweep universe is 90 seeds in 100–275. The D.3 blocks are 6201–6218, 6301–6302, 6311–6329, 6501–6679 and
     6701–6880. The G.4 allow-list 4001–4099 is in `sweep2/g4/g4_lib.py` line 140.
   - I checked the listed hits by reading the scan file. Their classification is right: none is a seed in the block.
3. **Primary decision.** It matches the row (a seed bootstrap of the node-level equal-weight mean, B = 2,000, the 0.1
   threshold, the 97.5 % reading beside it), except for the triple set (M4).
   - Resampling unit: seeds, jointly across all configurations of a node, with one index draw per resample. Under
     common random numbers the seed is the independent draw of the whole error vector, so this is the right unit.
   - Error rate of a false SHARED exactly at the threshold: 0.0325 (`digits_mlp`) and 0.025 (`openml_climate`), both
     reproduced. One-sided nominal is 0.025; the Monte Carlo standard error is 0.009.
4. **Power table.** Re-run in full (400 replicates, B = 2,000): `power.json` is identical apart from timings. The
   bounds 0.196 (power 0.745) and 0.146 (power 0.087) are reproduced (0.1961 and 0.1455). Independent code agrees
   within Monte Carlo error (see "Verified").
5. **Child rules.** Fixed in code before any run and implemented (`same_symbol`; `identical_to` through the D25 active
   keys). The exclusions per node are as in PD §3. Caveat: M3.
6. **Compute.** Re-run: identical (10,164 runs; 2.4, 6.3 and 11.1 CPU-hours; T = 2,975 s; deadline 10,800 s). The
   inputs from the B.2 review (lines 120, 125, 179–180) and the addendum's deadline rule (line 54) are as cited. For the
   MLP nodes, basis B uses the pooled OpenML mean, as disclosed.
7. **E1 edit check.** `check_edit_sets` runs before any harness run, in both the smoke and the evidence mode, and
   raises on any difference. The exit semantics are in N1.
8. **No sealed reads; no guard change; no C3 reader.**
   - The diff from `53e2fe41` touches no file under `r1/c3/`.
   - No walker in `r1/c3/` reads `results/r1/screen_measure/`.
   - The run table is not named `runs.jsonl` (`release.RAW_NAMES`), and its rows carry no `label`.
   - The analysis refuses sealed paths, paths named after label, evaluation or test blocks, and evidence-marker
     directories.

## The author's §12 items: are they presented correctly?

1. **Two testable nodes.** Correct as a statement of fact. Option (a) already embeds the both-links rule, so the
   all-triples test of the row is missing as an option (M4).
2. **PILOT correlations on four nodes.** Correct. I checked that for the three repaired nodes the accepted 22 Oct
   values of the pre-repair nodes give the same classification (`C` 0.982–0.997, `class_weight` 0.9975–0.9990, the
   switches 0.24–0.72). The item could add that the `openml_climate` power figures also rest on PILOT values.
3. **`openml_wdbc` as a decision node.** Correct; it is NOT_TESTED by design, so the choice cannot change the
   decision.
4. **Multiplicity.** Correct, including the need to recompute power at 97.5 %.
5. **Proposed values.** The list is correct, but it should present the both-links rule as a departure from the row
   (M4).
6. **D.3 seed list.** Correct as far as it goes; it should also cover Paper C's registry (M6).
7. **Smoke on deepthought.** Correctly flagged as needing the author's word.
8. **Compute above the row's estimate.** Correct; the figures are verified.
9. **C3 guards.** Correct; verified as under point 8 above.

## What I verified, and how

- **Tests.** `python3 -m pytest -q r1/tests/test_screen_measure.py -p no:cacheprovider` passed 37 of 37 in 4.5 s.
  The D.3-blob test ran; it did not skip.
- **Pins.** I computed the sha256 of the five modules, of the test file and of the noise source, and of
  `e1_noise_floor.py`, which is identical to `53e2fe41`. I also hashed `design.json`, `power.json`, `compute.json`,
  `seed_scan.json` and `tests.txt`. All equal PD §11 and AN. The header sha256 of PLAN, RUNBOOK and CURRENT at
  `53e2fe41`, and the PLAN line numbers, are correct. The later `author-minsub-20261122` commits add no row that
  touches this unit.
- **Design.** `python -m r1.noise.screen_design` regenerates `design.json` byte-identically (sha256 `bbc98b87…`; 84
  configurations, 72 triples, 20 primary, 10,164 runs). The ρ values equal the noise source, and the noise source
  equals the 22 Oct `summary.json` (`eabc2f5c…`) for the four nodes it takes from that file.
- **Algebra.** I derived the closed form in M5 and compared it with `reference_partial` on all 72 triples (largest
  difference 5·10⁻⁷, from rounding to six decimals).
- **Power, independent re-implementation.** Own covariance construction, partials and percentile seed bootstrap; it
  imports nothing from `r1.noise` (`/tmp/rev_smeas/indep_power.py`; 200 replicates, B = 1,000).
  - `digits_mlp`: kernel P(NO_SHARED) 0.895; at the threshold P(SHARED) 0.035; s = 0.5995: 0.77; s = 0.6552: 0.96.
  - `openml_climate`: kernel P(NO_SHARED) 0.25; at the threshold P(SHARED) 0.025; s = 0.4741: 0.075; s = 0.664: 0.50.
  - All agree with `power.json` within Monte Carlo error.
- **Activity-failure scenario (M3).** `/tmp/rev_smeas/activity_risk.py` is the same code with c35 set equal to c3
  under s = 0.
- **Reproducing the two reviewer scripts.** They are local and not committed, because this review writes only its own
  file. Each one-line description above is enough to rebuild it. The same numbers also follow from
  `screen_power.lineage_covariance` and `screen_analysis.node_test`, after overwriting c35's simulated vector with
  c3's.
- **Compute.** Re-run: identical. B.2 review lines 120, 125 and 179–180, and addendum line 54, checked.
- **Stub dry runs.** Reproduced. Both `lineage_runs.jsonl` files have the sha256 recorded in `dryrun/record.json`.
  Both engineering analyses are byte-identical to the committed ones. The evidence-mode refusal is reproduced.
- **Seeds: evidence-marker directories.** A names-only scan of all 188 distinct trees for evidence-marker files finds
  only `docs/r1/reports/b2_audit_20261119` and `docs/r1/reports/sweep2_20261116/s2_b2_audit_20261122`. The scan
  excludes both.
- **Seeds: supplementary scan of run records.** On all refs, `git grep -l` over `*.jsonl`, `*.json` and `*.csv` for a
  key containing "seed" with a value in 3301–3420 found no file. The protected paths and every `runs.jsonl` were
  excluded.
- **Seeds: PILOT and engineering run tables.** A second names-only scan, of `runs.jsonl` under `results/r1/pilot`,
  `results/r1/engineering` and `results/r1/noise` (paths containing "evidence" excluded), found no file.
- **Seeds: re-running the drafter's scan.** I re-ran `python -m r1.noise.screen_seeds scan` on this repository
  (7 min 48 s; 205 refs, 188 distinct trees). The ref list has moved since the drafter's scan (ref-list sha256
  `9f6ec5cb…` against the file's `391ddb28…`), but the result is the same: identical listed hits (123 token hits, 21
  seed-context hits, same path and text), the same hex-only counts (944 and 11), the same five E1 manifests with no
  span meeting the block, and the same static check.
- **The design matches its sources.** The children follow the report's §4.2 recommendation with exact activity. The
  decision mapping follows the row: INCONCLUSIVE and NOT_TESTED fall under "otherwise". The T4 §5 model is compared
  in M5.

## What I could not verify

- **The harness at `6adf3859`.** No checkout was available. So I could not check:
  - that `candidate_edits` reproduces the declared edit sets on all eight nodes;
  - that `r1.c3.features.apply_edit` writes a pre-applied edit in the same form as the harness worker would;
  - that `class_weight` is active under `random_forest` in the node code at that commit (M3; checked only in an
    older committed copy).
- **On deepthought:** the per-run time of the MLP nodes, and the preflight against the real environment.
- **The realised correlation of a link applied on a parent other than c0** (PD "Not determined here").
- **The engineering smoke**, which this review was not allowed to run.

---

## Re-check round (23 Nov 2026)

*AI-assisted (Claude, independent reviewer subagent, 23 Nov 2026).* I re-checked the diff `d5a62ecb..77485065` (10
commits by the drafter; the PD's "Response to review"). As before: local only, no remote host, no smoke, no sealed
file. To assess the M3 refusal I read the per-seed metrics of the E1 joint runs: the accepted 22 Oct run, and the
PILOT D28 runs for the four nodes that run covers. I used them only to count seeds at which two configurations have
identical metrics, as a design check; no value from them is a result.

### Verdict: accepted

Every MINOR and NIT finding of the first round is fixed as asked. The drafter's new finding on the all-triples option
is correct, and it corrects my first-round bounds argument (see 2 below). The pins match and the dry runs reproduce.
The fixes introduce no MAJOR or MINOR defect. Six NITs follow (R2-N1 to R2-N6). R2-N3 corrects a sentence that is now
false and should be applied before signing. Applying any of them as written needs no further re-check.

### 1. The first-round findings

| Finding | Fixed as asked? | What I checked |
|---|---|---|
| M1 | Yes | `handle` returns `determinism_unverifiable` for a failed run at a repeat key, before the failure-rate check. The analysis separates "unverifiable" from "mismatch". PD §6.6, §9 item 1 and the note's STOP list agree. Tests cover the first run and the repeat, in-process and through the pool. |
| M2 | Yes | `load_run` refuses a missing or different `runs_sha256` in both modes. In evidence mode it requires a non-empty `preflight`, `harness.commit` = `6adf3859…` with `dirty` false, and `edit_sets` `equal` on all eight nodes. The runner writes exactly these fields (`harness_commit` returns `dirty` as a bool, `r1/harness.py` 40–41), so a genuine evidence run passes. |
| M3 | Yes; scope in R2-N1 | `identical_configs` runs on every node before any statistic. The smoke records `identity_flags`. The validity reason is stated in PD §3 and the design docstring. |
| M4 | Yes | Declared as a departure in PD §1, §6.1 item 4, §6.3, §10 and §12 item 5. The all-triples test is offered as §12 item 1 (d), with its power. One sentence carries over my wrong claim (R2-N3). |
| M5 | Yes | The model is named, the condition for "tends to 0" is given, and the closed form is included with a unit test. On the example value: my 0.407 was computed at s equal to the exact smallest ρ, 0.9990983, which I wrote rounded as 0.9991. At s = 0.9991 the value is 0.4076 (`shared_lineage_partial`, recomputed). So the PD's "0.408 at s = 0.9991" is correct as written; no change needed. |
| M6 | Yes | PD §5, §12 item 10 and note P6. I re-checked the Paper C citations: `COUNT_DOMAIN = 1000`, the `noise_floor` base-count entry, and the same declaration on the four other branches named. |
| M7 | Yes | `RunnerStopTest` (each STOP reason asserted, manifest written with it, in-process and pool), `PreflightTest` (stubbed `audit`, cotenancy and published-main reader) and `SmokeModeTest` are present. 63 tests pass. |
| N1–N9 | Yes, all nine | N3: the range is now 0.815–0.914 s. N4: wording changed and `openml_ionosphere`'s `C ×2` named. N5: `bootstrap_empty_resamples`. N6: the manifest's `seeds` = [999] for the smoke. N2: `WorkerRuntimeStop` → `worker_runtime …`, with its own test. N1, N7, N8, N9: text. |

### 2. The drafter's new finding on the all-triples option: confirmed

My first-round bounds (≤ 0.052 on `tabular_mlp`, ≤ 0.013 on the OpenML nodes) are bounds on the population mean over
**all** of a node's triples. The test pools only the **eligible** triples. My M5 (a) text used the bounds as though
they limited what an all-triples test could return. The drafter is right that they do not.

- **The pooled triples.** On `tabular_mlp`, both edits 2 and 4 are `ALPHA` (E1 ρ 0.99999), so the 12 triples with an
  `ALPHA` link fail the 0.999 near-singularity rule on the sample. In my independent simulation every replicate kept
  exactly 6 triples. My closed form gives the remaining six (c0>c1>c13, c0>c3>c13, c0>c1>c15, c0>c5>c15, c0>c3>c35,
  c0>c5>c35) partials of 0.073, 0.073, 0.231, 0.231, 0.147 and 0.147 at s = 0.8783, mean **0.1502**. The mean over
  all 18 is 0.0516.
- **The power.** `power_node(tabular_mlp, 0.8783, 400, seed 20268130, "all")` reproduces P(SHARED) = **0.2075**
  exactly (and mean estimate 0.148). My independent code (no `r1.noise` import; 200 replicates, B = 1,000) gives 0.18,
  which agrees within Monte Carlo error.
- **Presentation.** PD §4 now states the bound correctly as a bound on the all-triples mean, gives the 0.150 and 0.21,
  and labels all of it as a statement about the u + w model. §12 item 1 (d) and its "Reading it" paragraph lay out the
  trade-off. I checked every number in that table against `power_all_triples.json`, including the decision-level
  0.0025 and 0.799 against 0.000 and 0.767. The choice between primary-only and all-triples is therefore presented
  correctly, apart from R2-N3, R2-N4 and R2-N5.
- **For the rationale.** `tabular_mlp` is NOT_TESTED by the declared test even though, within the model at its
  E1-consistent share, its pooled eligible triples exceed 0.1 on average. That is a cost of the 0.95 near-duplicate
  cut, and it is now visible to the author. It is an author decision, not a defect.

### 3. Pins and reproduction

- **sha256 at `77485065`.** All entries of PD §11 and of the note's key block and output table equal the files:
  - the five modules, `e1_noise_floor.py` and the test file;
  - the noise source and the design sha256 `bbc98b87…`;
  - `design.json`, `power.json`, `power_all_triples.json` (`5f7ab03f…`), `compute.json`, `seed_scan.json`,
    `dryrun/record.json` (`84d36bfc…`) and `tests.txt` (`0d766261…`).
- **Unchanged files.** `design.json`, `power.json`, `compute.json` and `seed_scan.json` are byte-unchanged in the diff.
- **Tests.** 63 pass locally in 8.4 s.
- **Regenerated with the corrected code.** The design is byte-identical, and the compute projection is identical.
  `power` reproduces `power.json` apart from timings (full run, 400 replicates).
- **Stub dry runs.** Both regenerate with the recorded `lineage_runs.jsonl` sha256. Both engineering analyses are
  byte-identical to the committed ones. The manifests differ only in the start and finish timestamps. The
  evidence-mode refusal is reproduced.
- **Scope of the diff.** It touches no file under `r1/c3/` and not `PLAN.md`.

### 4. New defects from the fixes

- **`determinism_unverifiable`, `worker_runtime`, M2, the in-process exception path:** no defect found. The new STOP
  reasons fire only where intended. `WorkerRuntimeStop` wraps only the probe call, not the imports, and is picklable
  through the pool. The M2 checks accept the manifest the runner actually writes.
- **Can the M3 refusal STOP a legitimate design?** In principle yes; in practice the probability is small (R2-N1).
  - The `ALPHA` edits on `tabular_mlp` are not the risk. In the accepted 22 Oct run their metric equals c0's at 5 and
    11 of the 30 joint seeds, so all 120 seeds identical is negligible.
  - The largest observed rate is `openml_breast_w` `class_weight` against c0: 26 of 30 seeds (D28 PILOT). Its
    posterior-predictive probability of 120 identical seeds (uniform prior) is 2.8·10⁻⁴. Summed over all single-edit
    pairs on all eight nodes it is 2.9·10⁻⁴ (my computation).
  - Child pairs such as c15 against c1 are unmeasured but plausibly of the same order. So the total is of order
    10⁻³.

### Remaining findings (all NIT)

- **R2-N1 (NIT) — M3 refusal scope.**
  - *As written,* `screen_analysis.analyse` refuses the whole table if any two configurations of any node are
    bit-identical. A legitimately identical pair on a node that cannot affect the decision (an untested OpenML node,
    whose AUC is rank-based and often unchanged by near-duplicate edits) would void `digits_mlp` and `openml_climate`
    too.
  - *The case for the global scope.* The OpenML nodes share one template, so an inert key on one node bears on
    `openml_climate`.
  - *Optional fix.* STOP only for pairs among the configurations of the decisive test's triples (`digits_mlp`: all
    15; `openml_climate`: c0, c3, c5, c35; under §12 (d), those of the eligible triples). Report other identities and
    drop the affected triples from the secondary readings.
  - *If kept,* state in PD §6.7 the risk estimated above (of order 10⁻³).
- **R2-N2 (NIT) — expected smoke flags.** PD §8.4 expects flags only for the `tabular_mlp` `ALPHA` edits. The E1
  joint runs show identity at one seed far more often:
  - `openml_breast_w`: `class_weight` 26/30, `C` 22/30;
  - `openml_sonar` `class_weight` 20/30; `openml_wdbc` `class_weight` 16/30 and `C` 9/30;
    `openml_credit_approval` `class_weight` 9/30;
  - `openml_climate` `C` 6–7/30; `digits_mlp` 2–4/30 per edit (discrete metric); `tabular_mlp` `ALPHA` 5/30 and
    11/30.

  So several flags are likely at seed 999, possibly on `digits_mlp` too. State these rates in §8.4 so each flag is
  read against them. Make only a flag among the decisive configurations that these rates do not explain return the
  unit; the case it exists for is `openml_climate` c35 against c3.
- **R2-N3 (NIT; apply before signing) — "raises power".**
  - *Where.* PD §6.1 item 4 says "under the u + w model it raises power (§4)". This is my first-round wording (M4),
    and the drafter's own §12 (d) table shows it is not true in general.
  - *Where it holds:* at the reference shares (`openml_climate` 0.670 against 0.050 at s = 0.7082) and on
    `openml_climate` at its E1-consistent share (0.087 against 0.0075).
  - *Where it fails:* on `tabular_mlp` the restriction removes a P(SHARED) of 0.21, and at every node's largest
    E1-consistent share the decision-level P(at least one SHARED) is 0.767 against 0.799 for all triples.
  - *Replace with:* "under the u + w model it raises power on `openml_climate` and at the reference shares, leaves
    `digits_mlp` unchanged, and gives up `tabular_mlp` (P(SHARED) 0.21 for the all-triples test at its largest
    E1-consistent share) and the NO_SHARED readings on `openml_ionosphere`, `openml_sonar` and `openml_wdbc`; at every
    node's largest E1-consistent share the decision-level P(at least one SHARED) is 0.767 against 0.799 (§12 item
    1 (d))".
- **R2-N4 (NIT) — §12 item 1, first sentence.** "so the test cannot show a shared component there" should read "so
  the declared (primary-triples) test has no triple there". Option (d) shows that an all-triples test could, on
  `tabular_mlp`.
- **R2-N5 (NIT) — §12 item 1 (d), consequences.**
  - "A Bonferroni reading would use m = 8": under (d), `openml_breast_w` and `openml_credit_approval` are NOT_TESTED
    with probability 0.9975 and 1.000 (`power_all_triples.json`). Define m: nodes with a design triple (8) or nodes
    with an eligible triple.
  - Under (d) the note's `design` field ("testable nodes digits_mlp … and openml_climate …; the other six NOT_TESTED
    by design") also changes. Add it to the list of edits that (d) requires.
- **R2-N6 (NIT) — PD header.** The PD and the note still say the corrections "need the reviewer's re-check of the diff
  before signing". With this round, cite this section instead.
