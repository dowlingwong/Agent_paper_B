**AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.**

# R1-SCREEN-MEASURE — pre-declaration of the direct screening measurement on the eight T0 nodes — DRAFT

Drafted by a subagent of the coordinating chat on branch `mac-screen-measure-20261123`, based on
`author-minsub-20261122` @ `53e2fe41` (PLAN.md sha256 `eb29d0e7353c3c963db33fac8a7f7772e957511eb23e70f0ae4787d14cf12b08`,
RUNBOOK.md `61a6ed9515c5070deb101f618460e9b9f4ff1c5eb1f63fcace07560d21f1a222`, CURRENT.md
`578b0f05a7957758abeede4b9b6e0558e679d8dae28f9c70f6459f03114e6048`). **Tier E** (R1-PROCESS-TIERS): before signing it
needs a committed independent review, re-checked until it writes "accepted". It decides nothing on its own. Every value
carries its source (a PLAN row, a signed note or a file with its path); a value with no source is marked **proposed**,
with its reasoning, and is fixed only by the author's signature. No PLAN row, preregistration, signed note or code guard
is changed; where a row cannot be implemented as written, the point is listed in §12.

**Data read to write it.** The pinned E1 inputs of §3 (`summary.json` files, `edits.json` files, and three E1
`runs.jsonl` files, parsed whole but used only for `node` and `wall_seconds`, for compute); the screening-test branch (report, review, scripts,
post-hoc power files); timing lines of `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md`; the D.3 branch's seed module;
file names (not contents) across all refs to place the scan's exclusions. No sealed partition, label block, evaluation
block, test partition, evidence audit directory or sweep evidence table was opened.

**How it becomes binding, in this order.** (1) The independent review of this document, the code of §11, its tests and
the authorization draft writes "accepted"; (2) the operator runs the engineering smoke of §8.4 on deepthought and its
record is cited in the note (any failure returns the unit to the drafter and the reviewer); (3) the author settles §12
and signs, by copying the authorization note with `approved: true` and the filled fields and publishing it, this
document (renamed without `_DRAFT`) and the reviewed code on `main`; (4) the operator launches as the note states.
If anything changes after (1), the reviewer re-checks the diff only and writes "accepted" before the signature.

## 1. Scope and authority

| Row or file | What it fixes here |
|---|---|
| R1-SCREEN-MEASURE (PLAN.md line 1418) | The measurement: all eight T0 nodes; c0, its five E1 single edits and the two-edit children c0 + e_i + e_j; 120 fresh joint seeds; the test of `SCREENING_TEST_20261122.md` (pooled partial correlation of child and grandparent given the parent, bootstrap interval, SHARED above 0.1, NO_SHARED below 0.1); tier E; host deepthought CPUs under the conditions of R1-SWEEP2-B2-GO; "If any node returns SHARED, the seventh D.3a arm of R1-D3-CHOICES (1) is proposed before the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) is final." |
| R1-E1-PILOT-ACCEPT (line 1417) | The 22 Oct E1 runs (`results/r1/pilot/E1_20261022T214606Z/`) may be cited as measured per-edit correlations, with their limits. |
| R1-THEORY-RHO (5) (line 1415) | A direct ancestor–descendant test replaces the sibling proxy before the check enters the paper. This measurement is that test. |
| R1-D3-CHOICES (1) (line 1416) | The seventh arm "A2 with a keep-count threshold correction" is proposed only if the direct test supports a shared component on a node; A1/A2 and the preregistration are not changed either way. |
| R1-SWEEP2-B2-GO (line 1391) | The host conditions: deepthought CPUs, the environment of the sweep-1 B.2 audit, B6 (a), B4 (a), B1 (a), harness `6adf3859` with the run-time equality check against `a3fedbbd`, one host for the table. |
| R1-PROCESS-TIERS (line 1411); RUNBOOK §1 | Tier E procedure; evidence runs need an authorization note; pre-declaration committed with its hash before any outcome exists. |

**Label.** The measurement run is `EVIDENCE` (RUNBOOK §1: its outcome feeds a claim). The smoke, the dry run and the
power simulation are `ENGINEERING_ONLY`. Run id **`smeas-20261123-a`** (*proposed*; no run has used it).

## 2. Nodes: all eight T0 nodes

The eight nodes are `r1/c3/p3_split.py` `T0_NODES` (a tested copy of `gate.T0_NODES`): `digits_mlp`, `openml_breast_w`,
`openml_climate`, `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `openml_wdbc`, `tabular_mlp`.

**`openml_wdbc` is a decision node (primary for this measurement), and the seven-node reading is reported beside it.**
Reasons: R1-SCREEN-MEASURE names "all eight T0 nodes" and decides on "any node", and a pre-declaration cannot narrow an
author row. PRE-WDBC (R1-SWEEP2-PREREG) and R1-S2C3B-WDBC demote `openml_wdbc` because of the proposer's liveness
(`invalid_rate` 0.30 in C3b), which does not bear on the harness's error structure under common random numbers; this
measurement uses no proposer. R1-D3-CHOICES (2) runs no `openml_wdbc` in D.3, but the arm question concerns the
mechanism on the CPU testbed, not one node. In this design `openml_wdbc` has no primary triple (§4), so it is NOT_TESTED
by design and cannot change the decision; the analysis also reports the decision over the seven PRE-WDBC nodes
(`decision_seven_nodes`). See §12 item 3.

## 3. Configurations per node

**Sources.** The five single edits of each node, and each edit's `rho_joint` (the correlation of m(c0, s) and m(c_k, s)
over the 30 joint seeds 3001–3030, `r1/noise/e1_report.py` line 11), come from the noise source both sweeps and the D.3
draft pin, `results/r1/noise/D28_REPAIR_20261027/summary.json` (sha256 `3d12ce05…34310`), in the order of the edits file
it cites for the node:

| Nodes | Edits file (sha256) | Status of the data |
|---|---|---|
| `digits_mlp`, `tabular_mlp`, `openml_ionosphere`, `openml_credit_approval` | `results/r1/pilot/E1_20261022T214606Z/edits.json` (`a37adfa3…a6f6`) | **accepted** (R1-E1-PILOT-ACCEPT); aarch64 VM, harness `4012897a`. The noise source's values for these four nodes equal the 22 Oct `summary.json` (sha256 `eabc2f5c…3513793`), checked. |
| `openml_breast_w`, `openml_sonar`, `openml_wdbc` | `results/r1/pilot/E1_D28_REPAIR_20261027/edits.json` (`2e232470…78c3`) | **PILOT**, no acceptance row: the D21 re-measurement of the repaired nodes (R1-D28-REPAIR changed their start configuration, so the 22 Oct runs measure an older node); deepthought, harness `6adf3859`. |
| `openml_climate` | `results/r1/pilot/E1_D28_CLIMATE_20261027/edits.json` (`5331765d…25f2`) | **PILOT**, no acceptance row: the reserve node's D21 measurement (not in the 22 Oct run); deepthought, harness `6adf3859`. |

The PILOT correlations are used as a design input only (to classify links before any run); no PILOT value is quoted as a
result. For `openml_breast_w`, `openml_sonar` and `openml_wdbc` the accepted 22 Oct values of the pre-repair nodes give
the same classification (C ×0.5, C ×2 and `class_weight` at 0.98–0.999, both model-type switches below 0.95). See §12
item 2.

**Configurations.** c0 (the node default), c_k = c0 + e_k for the five edits, and every two-edit child
c_ij = c0 + e_i + e_j with i < j (all ten pairs of the five edits), after two exclusion rules **written before any
run** (`r1/noise/screen_design.py` `build_node`):

- `same_symbol`: e_i and e_j set the same symbol, so no configuration holds both;
- `identical_to:<id>`: the child's active projection (the D25 active keys of `r1/c3/features.py` for its `model_type`;
  every symbol on the MLP nodes) equals that of c0, a single edit or an earlier child, so it is the same configuration
  (identical metrics under CRN on CPU) and would add only identical vectors.

All valid pairs are taken, not a selection: the row asks for children c0 + e_i + e_j, every valid pair gives each single
as parent in as many triples as possible and both lineage orders of each child, and no pair is chosen by expected
outcome. No configuration is excluded after this design is pinned; a configuration that fails in the engineering smoke
(§8.4) STOPs the unit before signing.

| Node | Edits (E1 `rho_joint`) | Children kept | Configs | Triples | Primary |
|---|---|---|---|---|---|
| `digits_mlp` | e1 `LEARNING_RATE_INIT 1e-3 → 0.002` 0.7689; e2 `MAX_ITER 40 → 80` 0.8175; e3 `HIDDEN_UNITS 32 → 16` 0.5995; e4 `HIDDEN_UNITS 32 → 64` 0.7084; e5 `BATCH_SIZE 64 → 32` 0.8551 | c12, c13, c14, c15, c23, c24, c25, c35, c45 (c34 same symbol) | 15 | 18 | 18 |
| `tabular_mlp` | e1 `MAX_ITER 40 → 20` 0.9689; e2 `ALPHA 1e-4 → 5e-05` 1.0000; e3 `BATCH_SIZE 64 → 32` 0.9872; e4 `ALPHA 1e-4 → 0.0002` 1.0000; e5 `HIDDEN_UNITS 32 → 16` 0.8783 | c12, c13, c14, c15, c23, c25, c34, c35, c45 (c24 same symbol) | 15 | 18 | 0 |
| `openml_breast_w` | e1 `C 0.01 → 0.005` 0.9991; e2 `C 0.01 → 0.02` 0.9986; e3 `model_type → random_forest` 0.7011; e4 `model_type → gradient_boosting` 0.4896; e5 `class_weight balanced → null` 0.9994 | c15, c25, c35 | 9 | 6 | 0 |
| `openml_climate` | e1 `C 0.15 → 0.075` 0.9913; e2 `C 0.15 → 0.3` 0.9927; e3 `model_type → random_forest` 0.4741; e4 `model_type → gradient_boosting` 0.3228; e5 `class_weight balanced → null` 0.8639 | c15, c25, c35 | 9 | 6 | 2 |
| `openml_credit_approval` | e1 `C 0.15 → 0.075` 0.9959; e2 `C 0.15 → 0.3` 0.9947; e3 `model_type → random_forest` 0.8841; e4 `model_type → gradient_boosting` 0.8146; e5 `class_weight balanced → null` 0.9995 | c15, c25, c35 | 9 | 6 | 0 |
| `openml_ionosphere` | e1 `C 0.15 → 0.075` 0.9577; e2 `C 0.15 → 0.3` 0.9244; e3 `model_type → random_forest` 0.3358; e4 `model_type → gradient_boosting` 0.2779; e5 `class_weight balanced → null` 0.9907 | c15, c25, c35 | 9 | 6 | 0 |
| `openml_sonar` | e1 `C 0.01 → 0.005` 0.9802; e2 `C 0.01 → 0.02` 0.9806; e3 `model_type → random_forest` 0.6636; e4 `model_type → gradient_boosting` 0.1994; e5 `class_weight balanced → null` 0.9985 | c15, c25, c35 | 9 | 6 | 0 |
| `openml_wdbc` | e1 `C 0.01 → 0.005` 0.9912; e2 `C 0.01 → 0.02` 0.9929; e3 `model_type → random_forest` 0.6785; e4 `model_type → gradient_boosting` 0.5455; e5 `class_weight balanced → null` 0.9978 | c15, c25, c35 | 9 | 6 | 0 |
| **all** | | | **84** | **72** | **20** |

On every OpenML node the seven other pairs are excluded the same way: c12 and c34 `same_symbol`; c13, c23 `identical_to:c3`
and c14, c24 `identical_to:c4` (C is not active under a tree model); c45 `identical_to:c4` (`class_weight` is not active
under gradient boosting). Model types are `logistic_regression` in every c0 (the edits files). Runs: 84 × 120 seed runs
plus one repeat per configuration at seed 3301 = **10,164 harness runs** (design file
`results/r1/engineering/screen_measure_20261123/design.json`; canonical design sha256
**`bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8`**, `screen_design.design_sha256`).

## 4. Lineage triples, near-duplicate links, primary and secondary

**Triples.** Each kept child gives two lineages from c0: (g, p, c) = (c0, c_i, c_ij), whose g → p link applies e_i and
whose p → c link applies e_j, and (c0, c_j, c_ij), the other way round.

**Near-duplicate link (defined now, before any run).** A link is near-duplicate if its edit has E1 `rho_joint` ≥ 0.95
in the pinned data of §3, or has no `rho_joint` (fail closed). The threshold 0.95 is the one the screening test's
post-hoc split used (`SCREENING_TEST_20261122.md` §3.3) and the one the task brief suggests.

**Primary triples: neither link near-duplicate.** Secondary: every other triple.

Why both links, not only p → c (the superseded draft rule, commit `8a52327f`): under e = u + w, u shared by every
configuration at a seed (share s) and w with the product kernel, the population partial is
ρ(c, g | p) = (gc − gp·pc)/√((1 − gp²)(1 − pc²)) with gp = s + (1 − s)r_gp, pc = s + (1 − s)r_pc,
gc = s + (1 − s)r_gp·r_pc. It is **symmetric in the two links and tends to 0 as either link's correlation tends to 1**: a
near-duplicate parent carries the shared component of its neighbour almost exactly, so conditioning on it removes it.
`screen_design.py` writes, for every triple, its population partial under the two reference shares of the row's power
figures (s = 0.7082 and 0.7891, `screening_test.py` `POWER_SHARES`), from the E1 correlations of its two links
(`reference_partial` in `design.json`):

| Node | Primary triples | Population partial of primary triples at s = 0.7082 | Largest population partial of any triple at s = 0.7891 |
|---|---|---|---|
| `digits_mlp` | 18 | 0.215–0.363, mean 0.295 | 0.441 |
| `openml_climate` | 2 (c0>c3>c35, c0>c5>c35) | 0.271 | 0.347 |
| `tabular_mlp` | 0 | — | 0.120 |
| `openml_ionosphere` | 0 | — | 0.088 |
| `openml_wdbc` | 0 | — | 0.043 |
| `openml_sonar` | 0 | — | 0.035 |
| `openml_breast_w` | 0 | — | 0.022 |
| `openml_credit_approval` | 0 | — | 0.014 |

With one link at 0.95 and the other at 0.82, the population partial at s = 0.7082 is 0.122, near the threshold 0.1. On
the six nodes without a primary triple, every triple has a near-duplicate link and a population partial below 0.1 at the
first reference share: they could return NO_SHARED but not SHARED, whatever the truth. Under the superseded rule they
would have entered the primary test with 1–4 such triples each. The Track S post-hoc finding that near-duplicate links
gave negative partials (`SCREENING_TEST_20261122.md` §3.3, post hoc, unreviewed) points the same way; it is not used as
a reason here, only noted.

**Consequence: two testable nodes.** `digits_mlp` (18 primary triples, 15 configurations) and `openml_climate` (2
primary triples on 4 configurations). The other six nodes are **NOT_TESTED by design**: their E1 edit sets hold at most
one non-near-duplicate symbol (`model_type` on the OpenML nodes, `HIDDEN_UNITS` on `tabular_mlp`), and every child that
combines a model-type switch with another edit is either identical to the switch or carries a near-duplicate
`class_weight` link. They are still run and analysed descriptively (secondary readings, §6.5). See §12 item 1.

## 5. Seeds and disjointness

**Block: 3301–3420 (120 joint seeds), training seed = split seed = s**, the same 120 seeds for every configuration of
every node; one repeat of every configuration at seed 3301 (determinism); the engineering smoke at seed 999 only. The
block is the one proposed in `SCREENING_TEST_20261122.md` §4.2; its first half was checked by that report's review.

**Static check** (`r1/noise/screen_seeds.py` `check_block`, run by the runner before an evidence run; output in
`results/r1/engineering/screen_measure_20261123/seed_scan.json` → `static_check`). The block is 120 distinct integers and
meets none of:

- every interval of `RESERVED_SEED_NAMESPACES` in `r1/c3/d3_analysis.py` (branch `mac-d3-predecl-20261122` @ `a4053eac`,
  blob `b20cf020`), copied into `screen_seeds.py`; the unit test parses the blob with `ast` and requires equality:
  the sweep instance universe (90 seeds in 100–275, by `p3_split.t0_instance_seed`), 5101–5112, 7001–7010, 9001–9303,
  8001–8010, 1001–1030, 2001–2030, **3001–3030**, 4001–4003, 5001–5006, 6101–6108, 30000–39999, 100000–799999, 999;
- the D.3 blocks of that module: instances 6201–6218, smoke 6301–6302, smoke replicates 6311–6319 and 6321–6329, replicates
  6501–6679, audits 6701–6880;
- the G.4 pilot allow-list **4001–4099** (`sweep2/g4/g4_lib.py`, `sweep2/t1_tasl/g4_tasl.py`), which the scan below
  found and the D.3 list does not carry (`ADDITIONAL_NAMESPACES`).

**All-refs scan** (`python -m r1.noise.screen_seeds scan --repo <repo> --out …/seed_scan.json`; committed with this
unit). Every distinct tree of every ref (heads, remotes, tags; 205 refs, 188 distinct trees, ref-list sha256 in the
file) is searched with `git grep` in code, documents, configurations and manifest-like JSON for (i) any integer
3301–3420 and (ii) any line mentioning "seed" with an integer in 3031–3420 (a range or base that could reach the
block); every E1-style manifest (`seed_bases` + `seeds_per_condition`) on any ref is expanded to its spans. Protected
paths are excluded by pathspec and never read (sweep evidence, the two evidence audit directories found by file name on
all refs — `docs/r1/reports/b2_audit_20261119` and `docs/r1/reports/sweep2_20261116/s2_b2_audit_20261122` — and any
`r1_sealed`, label, evaluation or test block path), as are this unit's own files. Result (details in the file):

- **E1-style manifests:** five, every span ends at 3010 or 3030; none meets the block.
- **Seed-context hits (ii):** 21 listed, 11 counted as hex-only. The listed ones are 3001–3030 blocks (E1, G.1b, the D.3
  list, a test, and a concurrent branch's `r1/noise/controls_positive.py`), other blocks (G.4 4001–4099, T1 5101–5112),
  this block's own proposal and its review (`SCREENING_TEST_20261122.md`, `SCREENING_TEST_REVIEW_20261122.md`), a
  four-character digest fragment, and counts (3,274 duplicates in a release review; completion-token sums in a Track X
  usage file). None uses a seed in 3301–3420.
- **Bare-token hits (i):** 123 listed, 944 counted as hex-only. The listed ones are file sizes in tree and inventory
  captures (49), third-party changelog and test-file numbers under `archive/` (40), UUID and boot-id fillers in test
  fixtures (10), ports in socket listings (8), and 16 others: test counts (3), SSH forward ports (3), download progress
  sizes (2), a file size (1), a table count (1), completion-token sums (1), a five-character digest fragment (1), and this
  block's proposal and review (4). None is a seed.

So 3301–3420 is disjoint from every seed namespace in the repository on every ref at the time of the scan. The D.3
pre-declaration (another branch) should add 3301–3420 to its `RESERVED_SEED_NAMESPACES` (§12 item 6).

## 6. The primary test (`r1/noise/screen_analysis.py`)

### 6.1 Statistic, per node

1. Each configuration's metric vector over the node's complete seeds is centred by its own mean (removes the true
   value; a no-op inside a correlation, stated for clarity).
2. Per triple, the sample partial correlation corr(c, g | p) over the common seeds (`triple_partial`, the same rule as
   `screening_test.triple_partial`).
3. **Exclusions** (fixed on the full sample): a member with zero spread; |corr(g, p)| ≥ 0.999 or |corr(p, c)| ≥ 0.999
   (partial undefined); two members with identical value vectors; non-finite values. Excluded triples are counted by
   reason.
4. **Pooling:** the equal-weight mean of the eligible primary triples' partials. No pooling across nodes (R1-D3-CHOICES
   (1): "on a node"). Equal weights on r (not Fisher z), as the screening test and its review (NOTE 4) chose.

### 6.2 Interval and resampling unit

**95 % percentile bootstrap over seeds, all configurations of a node resampled jointly with the same seed indices;
B = 2,000; `numpy.random.default_rng(20261123)`; all B × 120 seed indices drawn in one call.** The triples share members
(c0 is in every triple, each parent in up to four, each child in two), so triple partials are dependent and resampling
triples or configurations would treat dependent units as independent. Under CRN every configuration of a node is run at
the same seeds, and each seed is one independent draw of the whole error vector over configurations; the seed is the
independent unit, and resampling it jointly keeps every cross-configuration dependence. (The screening test's
instance-cluster bootstrap does not apply: there is one seed set per node.) In a resample, an eligible triple whose
partial is undefined or near-singular is left out of that resample's mean (the number is reported).

### 6.3 Verdict and decision

- **SHARED** if the interval lies entirely above 0.1; **NO_SHARED** if entirely below 0.1; **INCONCLUSIVE** otherwise
  (R1-SCREEN-MEASURE).
- **NOT_TESTED**, with its reason: no primary triple in the design; no eligible primary triple; fewer than 108 complete
  seeds; c0 dropped.
- **Decision** (R1-SCREEN-MEASURE): if any of the eight decision nodes is SHARED, the coordinating chat proposes the
  seventh D.3a arm of R1-D3-CHOICES (1) before the D.3 pre-declaration is signed (`PROPOSE_SEVENTH_D3A_ARM`); otherwise
  R1-THEORY-RHO (2) is final (`R1_THEORY_RHO_2_FINAL`). INCONCLUSIVE and NOT_TESTED fall under "otherwise", as the row
  is worded. The decision over the seven PRE-WDBC nodes is reported beside it.

### 6.4 Multiplicity

**Per-node 95 % intervals decide; no correction in the decision** (*proposed*). Reasons: R1-SCREEN-MEASURE adopts the
screening test with its 95 % power figures; a SHARED leads only to a proposal the author decides on, not to an arm
change; and only two nodes can return SHARED. The family-wise rate of a false SHARED is simulated (§7): 0 of 400 per
node under the kernel, and 0.057 over the two testable nodes when both sit exactly at the threshold (mean population
partial 0.10). The Bonferroni reading over the testable nodes of the design (m = 2, 97.5 % intervals) is reported beside
the decision (`verdicts_bonferroni`, `decision_bonferroni`), never decisive. See §12 item 4.

### 6.5 Secondary readings (reported, never decisive)

All eligible triples of every node (near-duplicate links included), with their 95 % interval; the triples of the
superseded p → c-only rule; the eligible triples split by their realised correlations (both corr(g, p) and corr(p, c)
below 0.95 against the rest); the seven-node decision; the Bonferroni reading. These carry no verdict in the decision and
are labelled as descriptive wherever reported.

### 6.6 Failures and determinism

- A configuration with failed or non-finite runs at more than 6 of the 120 seeds is dropped with its triples (c0 dropped
  → NOT_TESTED); otherwise the failing seeds are dropped for the whole node (*proposed*: 5 % per configuration; the node
  needs ≥ 108 complete seeds, 90 %).
- The runner STOPs above 1 % failed runs of the plan (§9), so these rules apply only below that.
- Every configuration's repeat at seed 3301 must equal its first run bit for bit (the E1 determinism property, report
  `NOISE_FLOOR_COMMON_20261022.md`); otherwise STOP.

### 6.7 What the script refuses

`screen_analysis.analyse` computes only the statistic above and refuses (`AnalysisRefused`) before any statistic:
a path with an `r1_sealed`, sealed, label-block, evaluation-block or test-block component, or inside a directory holding
an evidence marker (`evidence_completion.json`, `evidence_binding.json`, `label_block.jsonl`, `evaluation_block.jsonl`);
a manifest whose schema, run id or design sha256 differs; seeds other than exactly 3301–3420; a run that ended in a STOP;
in evidence mode anything but an `EVIDENCE` table from the harness (`stub: false`), or B ≠ 2,000; in engineering mode
anything but an `ENGINEERING_ONLY` table; a run row with other keys; a run outside the design, twice, or missing; an
edited run whose edit was not applied or whose declared values were not read back; a determinism mismatch; an unknown
triple selection. It has no option for another threshold, level, triple set or resampling unit. Its unit tests cover
every refusal (`r1/tests/test_screen_measure.py`).

## 7. Power with the actual lineage structure

**Command and output:** `python -m r1.noise.screen_power power --out results/r1/engineering/screen_measure_20261123/power.json`
(400 replicates per scenario; the declared `node_test` with B = 2,000 on 120 seeds; design `bbc98b87…`). Model: all
configurations of a node simulated jointly from e = μ + u + w, u shared at a seed with share s, w with the product kernel
over the declared edits, each edit's marginal correlation set to its E1 `rho_joint` (r_w = max(0, (ρ − s)/(1 − s))); s = 0
is the kernel of T4 Prop. 9 / T2 Prop. 4(a), under which every design triple has population partial 0. Nodes are
simulated independently. Monte Carlo standard errors are in the file (at most 0.025).

| Node | Scenario | s | Mean population partial (primary) | P(SHARED) | P(NO_SHARED) | P(INCONCLUSIVE) |
|---|---|---|---|---|---|---|
| `digits_mlp` | kernel | 0 | 0 | 0.000 | 0.910 | 0.090 |
| | at the threshold | 0.4329 | 0.10 | 0.033 | 0.022 | 0.945 |
| | largest s consistent with E1 (= min ρ of its primary links) | 0.5995 | 0.196 | 0.745 | 0.000 | 0.255 |
| | partial 0.24 (row's lower effect) | 0.6552 | 0.24 | 0.973 | 0.000 | 0.028 |
| | reference share | 0.7082 | 0.295 | 0.995 | 0.000 | 0.005 |
| | partial 0.37 (row's upper effect) | 0.7705 | 0.37 | 1.000 | 0.000 | 0.000 |
| | reference share | 0.7891 | 0.390 | 1.000 | 0.000 | 0.000 |
| `openml_climate` | kernel | 0 | 0 | 0.000 | 0.247 | 0.752 |
| | at the threshold | 0.3826 | 0.10 | 0.025 | 0.028 | 0.948 |
| | largest s consistent with E1 | 0.4741 | 0.146 | 0.087 | 0.003 | 0.910 |
| | partial 0.24 | 0.6640 | 0.24 | 0.530 | 0.000 | 0.470 |
| | reference share | 0.7082 | 0.271 | 0.670 | 0.000 | 0.330 |
| | partial 0.37 | 0.8076 | 0.37 | 0.963 | 0.000 | 0.037 |
| | reference share | 0.7891 | 0.347 | 0.925 | 0.000 | 0.075 |
| six other nodes | any | — | — | 0 (NOT_TESTED with probability 1) | 0 | 0 |

Decision level, P(at least one SHARED among the two testable nodes): kernel 0.000; both at the threshold 0.057; both at
partial 0.24: 0.987; at the largest consistent shares: 0.767.

**Against the row's figures** ("0.95 at p = 0.24; 0.82 for NO_SHARED under the kernel", from 18 triples of the
`digits_mlp` geometry with every link at 0.82): on `digits_mlp` with its own correlations the test is at least as strong
(0.973 at mean partial 0.24; 0.910 NO_SHARED under the kernel). On `openml_climate`, with two triples, it is weak (0.530;
0.247). On the other six nodes it cannot test. **Caveat:** a share above the smallest E1 correlation of a node's primary
links gives that edit a model correlation above its measured `rho_joint`; below that bound the largest mean partial the
model allows is 0.196 on `digits_mlp` and 0.146 on `openml_climate`, where the power is 0.745 and 0.087. The row's
effect sizes 0.24 and 0.37 are therefore reachable in this model only with marginal correlations above the E1 values
(on `digits_mlp`, `HIDDEN_UNITS 32 → 16` at 0.5995).

## 8. Compute, host and conditions

### 8.1 Compute (`python -m r1.noise.screen_power compute`; `results/r1/engineering/screen_measure_20261123/compute.json`)

10,164 harness runs (1,815 on each MLP node, 1,089 on each OpenML node) plus 168 smoke runs at seed 999.

| Basis (measured) | Per-run wall | CPU-hours | Elapsed at 16 workers |
|---|---|---|---|
| A. E1 22 Oct, `results/r1/pilot/E1_20261022T214606Z/runs.jsonl` (sha256 `03aa9ee1…0a22`), aarch64 VM, 4 workers | 0.871 s pooled (per node 0.82–0.97 s) | 2.4 | 550 s |
| B. E1 D28, `results/r1/pilot/E1_D28_REPAIR_20261027/runs.jsonl` (`49018a99…c1e4`) and `…E1_D28_CLIMATE_20261027/runs.jsonl` (`b75d5b32…ddbb`), **deepthought**, harness `6adf3859`, ~16 concurrent runs, no runtime probe | 2.221 s pooled (2.05–2.46 s) | 6.3 | 1,411 s |
| C. Sweep-1 B.2 audit, **deepthought**, 16 workers, one runtime probe per run (as this runner makes): 4,660 runs, wall sum 18,381.8 s, elapsed 1,364 s (`docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md` lines 120, 125, 179–180) | 3.945 s; 3.416 runs/s | 11.1 | **2,975 s (≈ 50 min)** |

R1-SCREEN-MEASURE's "about 3.5 CPU-hours at one worker" was 14,000 runs × 0.9 s; with the actual 10,164 runs basis A gives
2.4 CPU-hours, but the deepthought bases give 6.3–11.1 CPU-hours (under an hour at 16 workers). **Deadline 10,800 s**
(the sweep-2 B.2 addendum's rule max(10,800 s, 2.5 T) with T = 2,975 s).

### 8.2 Host and the R1-SWEEP2-B2-GO conditions

deepthought CPUs only (R1-SCREEN-MEASURE). Every condition is checked by code at launch (`screen_measure.preflight_evidence`):

| Condition (R1-SWEEP2-B2-GO / its addendum) | Check |
|---|---|
| Host deepthought, in the environment of the sweep-1 B.2 audit; B6 (a) the e1 replay as the environment basis | `audit.evidence_environment` (host name, e1 replay report and review at `52992b22`, current-environment checks, Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3, `uv.lock` `dd42d018…`) |
| Harness `6adf3859`, clean, untracked files only as the e1 record; node, config, harness and worker code equal to `a3fedbbd` | `audit.evidence_environment`; `audit.sweep2_harness_equivalence`; the runner also refuses a harness other than `6adf3859` or dirty |
| B4 (a): the per-run worker-runtime probe, its limitation disclosed | `audit.worker_runtime` before every run; records in `worker_runtime.jsonl` |
| B1 (a): authority files byte-identical on published main | the note, the pre-declaration and PLAN.md are read from the freshly fetched `origin/main` (`audit._published_bytes`) |
| Reviewed, published paper code | `audit.evidence_paper_provenance` (HEAD = code commit, ancestor of published main, review `Code-Commit:` / `Verdict: ACCEPTED`, every imported `r1` module equal to the commit) |
| One host for the table | one run directory, one host; no resume |
| 16 workers, at least 10 of 40 cores left to other users (sweep-2 B.2 addendum) | workers 1–16 and at most the note's value; before launch cpus − 1-min load ≥ 10; during the run, sampled every 60 s, cpus − (load − our running workers) ≥ 10, the convention of the accepted B.2 run review; a breach is a STOP |

### 8.3 Outputs

A new directory `results/r1/screen_measure/SMEAS_EVIDENCE_<stamp>/` on deepthought with `design.json`,
`lineage_runs.jsonl`, `worker_runtime.jsonl`, `cotenancy.log` and `manifest.json` (with the run table's sha256); scratch
in a new `/tmp/r1_smeas_EVIDENCE_<stamp>`. The analysis output `analysis.json` beside it. Both are committed by the
operator, unchanged, after the run.

### 8.4 Engineering smoke before signing (ENGINEERING_ONLY)

`run --engineering-smoke` on deepthought, at the harness and in the environment above: every one of the 84
configurations once at seed 999 plus its repeat (168 runs), with the edit-set equality check (the harness's E1 edits must
equal the declared ones on every node), the edit checks and the determinism check. Output outside
`results/r1/screen_measure/`; never a result. A failure returns the unit to the drafter and the reviewer.

## 9. STOP rules

Each stops submitting, lets the runs in flight finish, writes the manifest with its reason and exits 3. A STOPped run is
reported as stopped, never resumed, patched or analysed; the outputs are kept. Before launch (no run made): any
precondition of §8.2 or of the note failing; the seed block meeting a namespace; the harness's E1 edits differing from
the declared ones; the output or scratch directory existing. During the run:

1. a determinism mismatch at seed 3301;
2. an edit not applied by the harness; a pre-applied edit not in the node copy; a declared value not read back after the
   run; any other symbol changed by the run;
3. more than 1 % of the 10,164 planned runs failed (no metric or non-finite);
4. a run raising an exception;
5. a worker-runtime probe mismatch;
6. a co-tenancy breach;
7. the deadline (10,800 s).

## 10. What is reported, and what enters the paper

Reported in the measurement's report (tier E): per node the verdict and its reason, the estimate, the 95 % interval, the
eligible and excluded triples by reason, the failures and dropped seeds; the decision and the seven-node decision; the
secondary readings labelled descriptive; this pre-declaration's deviations, if any; the host and environment record.

In the paper (as the direct test that R1-THEORY-RHO (5) requires): the design (nodes, edits, children, seeds, host), the
per-node verdicts with estimates and intervals for `digits_mlp` and `openml_climate`, and the statement that the other
six nodes were **not tested by design** (no lineage of two non-near-duplicate edits in their E1 edit sets) — never that
the screening property holds there. An INCONCLUSIVE or NO_SHARED is not described as evidence that the kernel holds on
T0. A SHARED on a node is reported with its estimate as a limitation of the kernel assumption (R1-THEORY-RHO (2)–(3)).
The limits: one host and one harness; edits one or two steps from c0; near-duplicate links excluded from the test; four
nodes' link classification rests on PILOT correlations (§3). The sibling proxy (`check_kernel_e1.py`) is not cited as a
result.

## 11. Code, outputs and pins

| File | sha256 |
|---|---|
| `r1/noise/screen_design.py` | `d5f8b68eac0449e168fae92c095b17bf96a1f30252c844f783d02ffb331add92` |
| `r1/noise/screen_measure.py` | `2aa5b0b98a917474abf4ece8d38e456364dc014cfbb3b0bb97c5987443d04037` |
| `r1/noise/screen_analysis.py` | `bb090531c5d762890ccedd375939f7317587c187233d8eea2813456dc9370fda` |
| `r1/noise/screen_seeds.py` | `dff8252b46101b695c9a938d722c11f3c68f56fb3c388859350a03e5112f2c4e` |
| `r1/noise/screen_power.py` | `38eaa7c4944f5f3af70fa121bd8abbf4189293c76bcf9ec3d459d6a914254960` |
| `r1/noise/e1_noise_floor.py` (unchanged from `53e2fe41`) | `a3fa508f0c16ec1cfb5b2afa0b37c8cfa6e9b965a8e5d90b6ab6e3c92a830b75` |
| `r1/tests/test_screen_measure.py` | `2722ca3045ffbd249585b3480eb9f3f0c34a3c474f3cdf4882f8d9668dbe3184` |
| design (canonical JSON, `screen_design.design_sha256`) | `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8` |
| noise source `results/r1/noise/D28_REPAIR_20261027/summary.json` | `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310` |

Engineering outputs (committed, `results/r1/engineering/screen_measure_20261123/`): `design.json`, `power.json`,
`compute.json`, `seed_scan.json`, `dryrun/` (stub runs at s = 0 and s = 0.7082 through the runner and the engineering
analysis: the kernel stub gives `digits_mlp` NO_SHARED and `openml_climate` INCONCLUSIVE, the s = 0.7082 stub
`digits_mlp` SHARED; the evidence-mode analysis refuses the stub table), `tests.txt` (test output). Their sha256 are in the
authorization draft.

## 12. Open for the author

1. **Only two of the eight nodes can be tested within R1-SCREEN-MEASURE's configuration set.** On `tabular_mlp` and the
   five OpenML nodes other than `openml_climate`, no lineage c0 → c_i → c_ij has two links below 0.95, so the test cannot
   show a shared component there (§4). Options: (a) run as declared (the decision then rests on `digits_mlp` and, weakly,
   `openml_climate`; the six nodes give descriptive secondary data); (b) a row that adds, on those nodes, second-step
   edits that are active under the switched model (for example a tree-model hyperparameter under c_rf) or a second
   non-near-duplicate MLP edit, which needs their near-duplicate status from new single-edit data, a revised design, power
   and compute, and a new review; (c) run only the two testable nodes (this narrows the row and needs a row). The draft
   implements (a).
2. **PILOT correlations decide the link classification on four nodes.** `openml_breast_w`, `openml_sonar`, `openml_wdbc`
   (D28 repair) and `openml_climate` (reserve) have no accepted single-edit data for their current configuration;
   R1-E1-PILOT-ACCEPT covers only the 22 Oct run. Only `openml_climate`'s two primary triples depend on it
   (`class_weight` 0.8639, `model_type → random_forest` 0.4741, measured on deepthought at harness `6adf3859`). Accept
   their use as a design input, or decide otherwise.
3. **`openml_wdbc`** is a decision node here because the row names all eight nodes (§2); it is NOT_TESTED by design, so
   the choice cannot change this decision. Confirm, or make it a sensitivity node.
4. **Multiplicity:** per-node 95 % decides, Bonferroni (97.5 %, m = 2) reported (§6.4). If the author prefers the
   Bonferroni level for the decision, the power figures of §7 must be recomputed at 97.5 % before signing.
5. **Proposed values with no row:** run id `smeas-20261123-a`; the near-duplicate threshold 0.95 and the both-links
   rule; the failure rule (> 6 of 120 seeds per configuration, ≥ 108 complete seeds per node, STOP above 1 %);
   B = 2,000 with generator seed 20261123; output under `results/r1/screen_measure/`.
6. **D.3 seed list:** the D.3 pre-declaration (`mac-d3-predecl-20261122`) should add 3301–3420 and, if its author agrees,
   the G.4 allow-list 4001–4099 to `RESERVED_SEED_NAMESPACES`. Not changed here.
7. **The engineering smoke** (§8.4) is a harness run on deepthought before signing; this draft assumes R1-SCREEN-MEASURE's
   host permission covers it as part of this measurement. If not, it needs the author's word.
8. **Compute is larger than the row's estimate** (6.3–11.1 CPU-hours on deepthought against "about 3.5"), still under an
   hour at 16 workers (§8.1).
9. **C3 guards.** `r1/c3/evidence_boundary.py` treats any row labelled `EVIDENCE` as identifiable C3 sweep evidence. The
   measurement's run rows carry no label field (its manifest does), its table is named `lineage_runs.jsonl` rather than
   the `runs.jsonl` that `r1/c3/release.py` locks, and no C3 reader reads `results/r1/screen_measure/` (the only
   `os.walk` / `glob` users in `r1/c3/` walk data caches, runtime trees and sweep-2 batch output). No guard change is
   proposed.

**Not determined here.** Whether the harness at `6adf3859` produces exactly the declared E1 edit sets on all eight nodes
(no harness checkout was available to this drafter; the runner checks it at the smoke and at launch, a difference is a
STOP); the per-run time of the two MLP nodes on deepthought (not measured there; basis B uses the OpenML mean); whether
the children's configurations run without error (first run at the smoke); how the correlation of a link applied on a
parent other than c0 (for example `class_weight` under a random forest) compares with its E1 value at c0 (the realised
split of §6.5 reports it).
