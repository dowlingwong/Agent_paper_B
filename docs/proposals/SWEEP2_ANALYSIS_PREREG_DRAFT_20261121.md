# Sweep-2 C3 analysis preregistration — draft for the author (frozen: false)

**Status: DRAFT. `frozen: false`. Nothing here is analysed or read.** Revision 4, after rounds 1–3 of the independent
review. The preregistration becomes binding when the author signs it and the coordinating chat commits the signed
copy to `main` as `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_<YYYYMMDD>.md`. Its sha256 is then cited by the
release rows that open the label tables to the analysis (§8), so that the analysis cannot start before it exists.

Written by the Mac-desk agent (Claude), AI-assisted, from published `main` `4aac5209` (PLAN as at `94db94bb` plus
R1-S2C3B-WDBC). It decides nothing on its own: §2 lists the author decisions, each with options and a
recommendation; every other rule is quoted from a PLAN row or from the pinned gate.

## 1. What is fixed elsewhere (quoted, not decided here)

| Source | Fixed |
|---|---|
| R1-BX-D8, confirmed by R1-BX-PROPOSED-CONFIRM (D8) | The primary criterion is the across-node aggregate: the IQM of gap closed and the probability of improvement (PoI) of A3 or A5 over A2, with node-stratified bootstrap CIs; per node, gap closed = (U_arm − U_A2) / (U_oracle − U_A2) on test instances with `y_eval`; U is the one-step utility scaled to a 20-run campaign; U_oracle is the noisy-oracle ceiling (TRACK_P §7.1); Holm over A3 and A5 at family-wise one-sided α = 0.05 (97.5 % for the first-ranked arm, 95 % for the second); the point IQM is reported against 0.1. The per-node table is secondary. |
| R1-BX-D8-V3-A | (1) A nonpositive point test denominator on an IQM-eligible node is a STOP; in a resample it sets that node's gap closed to −∞. (2) IQM-eligibility: the paired z of oracle − A2 over train + dev ≥ 3 and the dev denominator ≥ δ_n. (3) **Split P3 = 1/3 : 1/6 : 1/2 per tier, supplied by the caller and written into the analysis preregistration.** |
| R1-BX-D8-V3-B | (4) Pass rule (b2): the studentized node-stratified bootstrap lower bound of the IQM > 0 and the PoI lower bound > 0.5 (only the 97.5 % step was simulated). (5) **Per-tier test floor: T0 ≥ 9 and T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported.** T1 = 12 instances per node; the paper reports the gate's power — D8-PASS: mean two-arm power 0.36 at effect size 0.3 (μ ≥ 1), 0.26 on T1 × 6; its calibration comes from the positivity screen, which is disclosed; no post-hoc Johnson t. ("Effect size 0.3" is D8-PASS's g; it is not the run price g of §3.) |
| R1-BX-D8-CONFIRM | Gate `r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee`; T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, with the count disclosed; leave-one-suite-out needs at least one labelled T1 node per suite, otherwise leave-one-suite-out STOPs (the aggregate gate does not). Existing preregistration and analysis gates remain in force; sweep-2 label tables may be analysed from this row on. |
| R1-S2C3B-WDBC | At the launch commit the S2-C3b liveness was 7/8 (openml_wdbc failed only D28 `invalid_rate`); **the primary sweep-2 analysis uses the seven nodes that passed C3b, and openml_wdbc enters as a pre-declared sensitivity row (with / without)**; the C3b rerun at the new launch commit must reproduce exactly this result or give 8/8. |
| D18 | δ_n = max(0.002, 0.25 × median paired sd(Δ̂)) per node, in metric units; "the unit of the C3 gate, scaled to a 20-run campaign". The 18 Oct C3 gate row reads the gain "scaled to a 20-run campaign" against δ_n. |
| R1-MAIN-PROPOSER (b), (e); R1-MAIN-PROPOSER-ITEMS | Sweep 2: the eight sweep-1 nodes, 18 instances, W = 20, memory `append_only_summary` and `none`, `vary` split, the sweep-1 instance seeds, structure-only `manager_proposal/v1`, temperature 0.2 with the D26 seed, the Track X pick with thinking off (context 32,768, R1-SWEEP2-SETTINGS). (e): the B.7 gate and the A5/A6 evidence checkpoints use sweep 2; sweep 1 is added as a stratum; twin campaigns give the same (instance, incumbent, edit) the same label in both sources, so (1) **both sources use one instance → train/dev/test assignment**, (2) the cross-proposer table goes from one source's train partition to the other's test partition only, (3) duplicates are grouped across sources by (instance, incumbent hash, edit hash), (4) pooled intervals use an instance-cluster bootstrap. **Adopted (R1-MAIN-PROPOSER-ITEMS, "采用五项建议"):** pooled versus sweep-2-only training is chosen on validation before any test read; the P.3b exam set is drawn from the training partition. |
| R1-B2-DECOUPLE; R1-SWEEP1-CLASSIFY; R1-BX-D3; R1-BX-PROPOSED-CONFIRM (Track G E4, REVISIONS (c)) | Labels from seeds 7001–7005, the evaluation value from 7006–7010; 7006–7010 are never used for training, tuning or selection. K = 10 on T0. On T1, K = 10 unless the R1-BX-D3 check passes and is recorded in a PLAN row; then K = 6, labels 7001–7003, evaluation 7006–7008. Divergence (labels): a non-finite loss or no metric at the fixed budget; a divergent proposal enters no belief bin, its action target is u = −g; if only some seeds diverge, μ comes from the rest (partial); more than half diverging makes the proposal divergent. |
| TRACK_P §7.1 | U_oracle: the theory rule with the belief built from `y_train` of the **same** proposal, evaluated against `y_eval`. |
| Noise source | Both sweeps' tables pin `results/r1/noise/D28_REPAIR_20261027/summary.json` (sha256 `3d12ce05…4310`; `sweep2/s2_c2_lib.py` NOISE_PATH/NOISE_SHA), which covers all eight T0 nodes, including the three repaired under R1-D28-REPAIR (re-measured there) and openml_climate. |

**The gate's own conventions** (`gate.py` docstring; `M11_D8_GATE_V3_20261116.md` §3, "preregistration candidates",
all eight items), adopted as written: the t* = +∞ sentinel 1e12; ŝe = 0 ignores screened resamples; ties in G by a
stable sort over sorted node ids; the Holm ranking (first-level pass, then the composite tail share, then A3 before
A5); the split counts (`off_split`, `off_design_size`) are reported and never a STOP, while a declared split other than
P3 is a STOP and overlapping instance ids are refused; the train + dev z with z = 3 eligible; the added report fields;
the tie disclosure (PoI ties count ½; the calibration evidence covers continuous utilities only). Environment: NumPy
exactly 2.4.4 (checked), the recorded harness lock (`uv.lock` at `a3fedbb`, Python 3.13; not checked), seed 20261108,
PCG64, 2,000 resamples, linear quantiles; draws per node in sorted node order and sorted instance-id order.

## 2. Author decisions

### PRE-WDBC: the gate's T0 node set under R1-S2C3B-WDBC (recommendation: B)

The pinned gate STOPs unless the T0 nodes are exactly the eight of `gate.T0_NODES` (`_check_layout`), and the PoI
counts every supplied node; so the seven-node primary of R1-S2C3B-WDBC cannot be run on the pinned gate.
- **A:** an author row amending R1-S2C3B-WDBC for the C3 gate: the primary gate runs on all eight T0 nodes (the only
  scope the pinned gate accepts); the seven-node analysis is a descriptive row.
- **B (recommended): gate v3.1**, differing from v3 only in the T0 layout check: it accepts a T0 node set declared in
  the input (a subset of `T0_NODES`) and reports it. It **replaces** `r1/c3/gate.py` (the pin check and the guard bind
  that path), so the eight-node sensitivity run uses v3.1 too; a test shows v3.1 on all eight nodes reproduces v3's
  output on fixtures, identical except for the gate version, gate sha256, schema strings and the declared node-set
  field; v3.1 accepts an empty declared T0 set (used by leave-one-suite-out folds), with a test; the input schema becomes `r1_d8_gate_input/v3.1` (the declared node set added);
  independently reviewed, with its sha256 bound by an amended row that parses as a CONFIRM-type row, before any
  sweep-2 read. **Primary:** the T0 nodes that passed C3b at the
  launch commit (seven, or eight if the rerun gives 8/8), recorded in the arms-frozen record. **Sensitivity:** all
  eight. This keeps the author's row as written.
- **C:** run the gate only on eight nodes, call it the sensitivity row, and give the seven-node primary no gate
  verdict. Not recommended: it inverts R1-S2C3B-WDBC.

### PRE-SPLIT: one instance assignment for every evidence arm (recommendation: A)

P3 per tier: **T0** 18 instances per node → 9 test : 3 dev : 6 train; **T1** 12 → 6 : 2 : 4.
- **A (recommended): P3 is the only evidence split, for every arm, Track P included, and for both sources.**
  - Instance id (both tiers): `<node>__s<seed>` with the seed in decimal and no padding
    (`sft_data.instance_universe`); it is the gate's instance id. T0 hashes this string; T1 hashes G5-SPLIT's
    `<node>:<seed>` string (below).
  - **T0:** over the fixed design universe (8 nodes × the 18 sweep instance seeds of `e1b_collect._instance_seed`),
    per node, instances ordered by `sha256("c3_p3_split/v1:" + <instance id>)`; the first 9 are test, the next 3
    dev, the last 6 train. (The SFT builder reproduces it with split config salt `c3_p3_split/v1`, 9 test and 3
    validation per node; it cannot reproduce the T1 rule, so T1 builds read the split file.)
  - **T1:** as the G.5 draft's G5-SPLIT, quoted in full: over the 12 G.5 instance seeds 5101–5112 per node,
    instances ordered by `sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)`; the first 6 test, the next 2
    dev, the last 4 train.
  - Missing instances drop out without reassignment and are reported (`off_design_size`, `off_split`).
  - One generator writes one split file for both tiers; this preregistration and the G.5 note cite its sha256.
  - Consequences: A5's T0 training instances fall from the SFT split's 12 to 6 per node (plus sweep 1 under
    PRE-POOL); the P.3b exam set must lie within P3 train; the Track P runner switches its evidence builds to P3
    (P.4 draft, P4-P1SPLIT).
- **B: keep the Track P SFT split `trackp_sft/v1` for A5** (3 test, 3 validation, 12 train per node; values
  "proposed (Track P agent), to be confirmed by the author before any evidence use"). Not acceptable as evidence: an
  A5 trained on it and read on P3 test has trained on 5–7 of each node's 9 P3 test instances (5, 7, 6, 5, 6, 5, 6, 5
  in the order digits, breast_w, climate, credit_approval, ionosphere, sonar, wdbc, tabular; mean 5.6; computed by
  the reviewer from seeds and salts only).

### PRE-MEM: memory modes, sources and tiers in the gate input (recommendation: C)

Each T0 instance seed has two campaigns (`append_only_summary`, `none`); the gate takes one U per instance. C3_DESIGN
calls `append_only_summary` primary and `none` the contrast; H5 studies the gain by memory mode.
- **A:** pool both modes' proposals into one instance-level weighted mean (the instance is the cluster).
- **B:** `append_only_summary` only for the primary gate; `none` as a secondary gate run.
- **C (recommended):** U per instance = the mean of the two per-mode U values (each a 20-run value), so each mode
  weighs equally whatever its proposal count, and the instance stays the resampling unit; per-mode gate runs are
  reported as secondary (no verdict). If, under PRE-DUP A, one mode of an instance has no proposal of positive weight
  left, U is the other mode's U (reported); if neither has, the instance is left out (PRE-DUP).
- In every option: T1 enters with its mode(s) under G5-MEM (one mode under G5-MEM A, the same rule as T0 under B);
  the gate's test population is **sweep 2 only**; "sweep 1 as a stratum" means sweep 1 may enter training (PRE-POOL)
  and is reported in a separate descriptive table, never in the gate input.

### PRE-JOINT: training across tiers (recommendation: A)

- **A (recommended):** each arm is one model over all nodes of both tiers (node and tier as features), as
  `offline_eval` trains all nodes together; leave-one-suite-out retrains it without the held-out suite.
- **B:** one model per tier.

### PRE-SELECT: the validation criterion for PRE-POOL and PRE-A5 (recommendation: A)

Adopted: pooled versus sweep-2-only training is chosen on validation before any test read (R1-MAIN-PROPOSER-ITEMS).
The gate takes one A5 series (`gate.SERIES`); R1-C3-POOL-EXAM carries both Kev sizes and the Qwen control.
- **A (recommended): the mean over nodes, each node weighted equally, of the dev RPS skill against one common
  reference per node — the base rate of that node's own P3 train label block (sweep 2 for T0, G.5 for T1)** — so every variant (pooled or
  sweep-2-only, either Kev base) is scored against the same denominator. Dev population: the PRE-DUP primary dev
  population (the full dev population under PRE-DUP B); label block only. Calibration is C3_DESIGN's primary
  model-selection criterion and Track P's own selection metric (TRACK_P §5.7). Per arm: pooled versus sweep-2-only;
  for A5, also the Kev base (0.8B or 4B). Ties (to 1e-9): sweep-2-only; then the smaller base.
- **B:** the mean over nodes of the dev utility U / σ_node with Δ from the label block. Closer to the gate's
  statistic, but noisy at 3 dev instances per T0 node and 2 per T1 node.
- The other Kev base and the controls are secondary rows (§4 step 7), frozen with the arms.

### PRE-A2: what A2 is fitted on (recommendation: C)

A2 = A1 + rules; A1 is a constant (π, μ, τ) per node, fitted on "dev campaigns" (C3_DESIGN §5, part of the ladder
that R1-C3 fixes).
- **C (recommended): as C3_DESIGN** — A1's constants per node from the **dev** instances' label block; A2's train and
  test U are out of sample, its dev U in sample (it enters the eligibility z and the dev denominator; disclosed). No
  amendment.
- **A:** from the **train** instances' label block (dev and test out of sample, train in sample). Amends the ladder's
  fit set: needs an author row.
- **B:** cross-fitted over train + dev by instance. Amends the ladder's fit set: needs an author row.
- In every option A2 uses **sweep 2 only**; PRE-POOL applies to A3 and A5. Under C, A2 is fitted and scored on the
  same dev data, so with a proper score sweep-2-only would win or tie by construction; choosing it in advance is
  disclosed.

### PRE-DELTA: the δ_n compared with the 20-run dev denominator (recommendation: A)

- **A (recommended): D18's δ_n unscaled**, compared with the 20-run dev denominator and the 20-run gain, as the 18 Oct
  gate row reads ("the gain … scaled to a 20-run campaign, reaches δ_n") and as `offline_eval` compared them.
- **B:** 20 × δ_n. Fewer nodes become eligible.
- Sources (both options): T0 δ_n and σ_node from the pinned noise source (`D28_REPAIR_20261027/summary.json`,
  sha256 `3d12ce05…4310`) by `dataset.noise_table`'s definitions (σ_node: median sd_joint over material edits; δ_n:
  D18); T1 from each node's sealed G.1b summary on H200 (path and sha256 recorded in the T1 train/dev release row,
  before any training, since σ_node sets the soft-label width and g).

### PRE-DUP: cross-instance repeats in the gate and in selection (recommendation: A)

Terminology: a **repeat** is a proposal whose key (node, incumbent configuration hash, candidate configuration hash;
`sft_data.dup_key`) also occurs on another instance; offline_eval's "duplicates" are earlier evaluated configurations
within a campaign (weight 1; A2+ skip them) and are unchanged here. (e)(3)'s grouping key adds the instance; the
cross-instance key drops it, which is what makes the repeat visible.
- **A (recommended):**
  - The gate's primary **test** input leaves out test proposals whose key occurs on any train or dev instance of
    either source; the secondary run keeps the full test population. Inside an instance, the remaining proposals
    keep their offline_eval weights (**not recomputed**) and are renormalised, so U stays 20 × a weighted mean.
  - An instance with no remaining proposal of positive weight is left out of the primary input and reported; the test
    floor applies as the gate computes it (counts may fall).
  - The primary **dev** population used for selection (PRE-SELECT) leaves out dev proposals whose key occurs on a train
    instance (as G5-AUDIT and R1-TRACKP-SFT-DUP).
  - The gate's **train and dev blocks are the full populations in both runs**, so eligibility does not depend on
    PRE-DUP.
  - Disclosure: repeats concentrate on early-campaign proposals (all instances start from the same baseline), so the
    primary estimand weighs later-campaign proposals more.
- **B:** the full populations only.

### PRE-DIV: divergence on the evaluation seeds (recommendation: A)

The G.5 draft leaves this to the preregistration; R1-BX-PROPOSED-CONFIRM REVISIONS (c) fixes it for labels only.
- **A (recommended), mirroring the label rule:** Δ_true is the mean over the non-divergent evaluation seeds when at
  most half diverge (marked partial, counted); when more than half diverge, the proposal is divergent: its realised
  value is r = −g × execute (no gain whether kept or not), counted per arm.
- **B:** divergent proposals are left out of U (weights renormalised), with counts.

### PRE-T1: partial T1 and timing (recommendation: A)

- **A (recommended): one primary gate read.** The T1 node set and its instances are frozen in the arms-frozen record:
  exactly the T1 nodes whose train/dev labels were released and used to freeze the arms; a node needs ≥ 1 train and
  ≥ 1 dev instance to be supplied (otherwise reported, not supplied); nodes that STOP at G.5 follow the G.5 rule. No
  test partition of any tier is released before the arms-frozen record. A later read with more T1 nodes is not
  allowed.
- **B:** as A, plus one preregistered secondary read when all T1 labels exist, with new arms frozen first (trained on
  the then available train/dev), reported beside the primary with its own disclosure and no verdict.

### PRE-SECONDARY: analyses that read test (recommendation: A)

- **A (recommended):** in scope, each descriptive (no verdict), each arm frozen in the arms-frozen record:
  - the PRE-DUP secondary run and the PRE-WDBC sensitivity run (each gate run with its own output);
  - g = 0.05 and 0.2 σ_node: the gate statistics recomputed (no verdict);
  - per-mode runs (PRE-MEM C or B);
  - leave-one-suite-out: per held-out suite, the IQM and PoI over that suite's nodes with fold arms retrained without
    that suite (STOPs if a suite has no labelled T1 node, R1-BX-D8-CONFIRM);
  - leave-one-node-out within T0: per held-out node, its gap closed with fold arms retrained without it;
  - both computed by a reviewed fold-analysis module (§9) that calls the gate's statistics with a declared node
    subset (v3.1 under PRE-WDBC B; under A or C, its own code checked against the pinned gate on the full node set);
    eligibility applies as in the gate; fold arms are selected by PRE-SELECT on the fold's dev instances;
  - the secondary arms (the other Kev base, the Qwen controls, A4, TabPFN rows): per-node test table.
  - **Out of scope:** the cross-proposer table of (e)(2); it may not read test until a later signed amendment.
- **B:** only the gate runs (primary, PRE-DUP secondary, PRE-WDBC sensitivity); everything else waits for an
  amendment.

### PRE-STAGE: staged release, for both sources (recommendation: A)

R1-BX-D8-CONFIRM opens the sweep-2 tables to analysis; it does not order reads. Sweep 1's tables are not guarded at
all (`analysis_guard` passes the frozen sweep-1 index), and sweep 1's twin proposals carry the same labels.
- **A (recommended):** a code lock for **both sources**: until the test release row exists, readers get the label
  block of train and dev instances only and no evaluation value of any instance. Mechanism: the release step writes
  partitioned copies (train/dev label block; then test label block and every evaluation block) with receipts, and
  readers open only receipted partitions. What may be read before release: counts, divergence diagnostics without
  values. A lock forbids reads; it cannot prevent a deliberate read, which is a STOP.
- **B:** procedure only (§4 followed and recorded). Then §4's release steps are attested, not enforced, and §8's rows
  are not needed.

### PRE-POWER: which power the paper reports (recommendation: A)

- **A (recommended):** D8-PASS's simulated power as V3-B quotes it, with its qualifiers.
- **B:** a power recomputed for the realised node configuration (numbers of eligible nodes per tier), by the D8-PASS
  simulation code, declared now and run after the gate.

## 3. Definitions

- **Utility.** Per arm, instance and memory mode, U = 20 × the weighted mean, over the campaign's logged proposals, of
  the realised one-step value r = Δ_true × keep − g × execute, with `offline_eval`'s weights (no-ops and within-campaign
  duplicates 1; randomly audited non-inert proposals N_noninert / N_audited of their (source, node) stratum;
  DI-selected audits 0) and its primary run accounting (`skip_credited_at_g`). Δ_true comes from the **evaluation**
  block (PRE-DIV for divergence) for train, dev and test alike; decisions use beliefs built from the label block only.
  g = 0.1 σ_node primary. Per instance, the modes combine by PRE-MEM.
- **Oracle.** The theory rule (`rules.decide`, the same rule layer and g as the arms) with the belief built from the
  same proposal's label block (soft label N(Δ_label, s²), s = σ̂_node/√K_label, R1-SOFT-SIGMA), evaluated against
  Δ_true.
- **A2.** PRE-A2. **A3, A5.** Trained on train, selected on dev (PRE-SELECT), calibrated on dev.
- **K and seeds.** T0: K = 10, labels 7001–7005, evaluation 7006–7010. T1: the same unless the R1-BX-D3 check row
  exists; then labels 7001–7003, evaluation 7006–7008, and any use of 7004–7005 or 7009–7010 is a STOP.
- **δ_n, σ_node.** PRE-DELTA.

## 4. Procedure (in this order)

1. Commit this preregistration (signed), the split file (PRE-SPLIT) and, under PRE-WDBC B, gate v3.1 with its row.
2. Release the label block of train and dev instances, both sources, the tiers available (PRE-STAGE).
3. Train every arm on train (PRE-POOL, PRE-JOINT, PRE-A2), including fold arms and secondary arms (PRE-SECONDARY);
   select on dev (PRE-SELECT); fit calibration on dev. Label block only.
4. Commit the **arms-frozen record**: per arm, the code commit, checkpoint and calibration sha256s, the PRE-SELECT
   choices with their dev values; the T0 node set (PRE-WDBC) and the T1 node set (PRE-T1); the split-file, noise-source
   and G.1b summary sha256s; the gate (or v3.1) and gate-input builder sha256s; the label-table sha256s of both
   sources; and every earlier engineering use of sweep-1 data on P3 test instances (Track P SFT on `trackp_sft/v1`,
   the exam set's provenance), for disclosure. Nothing in it changes after it is committed; the test release row cites
   its sha256.
5. Release the test label blocks and every evaluation block (both sources). Build the gate inputs: train, dev and test
   blocks by the §3 definitions, primary and secondary (PRE-DUP).
6. Run the gate: primary, PRE-DUP secondary, PRE-WDBC sensitivity. Commit inputs, outputs and their sha256s.
7. The PRE-SECONDARY analyses.

An input refusal (schema or validation error, raised before any statistic) is fixed and the run repeated, with both
recorded. A statistical STOP (raised after test values are used) is reported as a STOP with no verdict; any remedy
needs an author row and is disclosed. A gate run is never repeated after its statistics are seen.

## 5. Floors and eligibility (as the gate applies them)

- Test floor per node: T0 ≥ 9, T1 ≥ 3 test instances; below it, a node is out of the IQM, in the PoI, reported.
- Eligibility: train + dev paired z of oracle − A2 ≥ 3, and the dev denominator ≥ δ_n (PRE-DELTA).
- No eligible node: STOP. A nonpositive point test denominator on an eligible node: STOP.
- Reported per node: n_train, n_dev, n_test, the floor, z, the denominator, the eligibility reasons, `off_split`,
  `off_design_size`, and instances left out under PRE-DUP.

## 6. STOPs

**From the signature on** *(proposed; the signature makes it the author's rule)*: the read STOP below applies, and it
narrows R1-TRACKP-SFT-DEV's ENGINEERING runs to the sweep-1 label block of P3 train and dev instances; reads made
before the signature (Track P SFT on `trackp_sft/v1`, the exam set) are disclosed in the arms-frozen record.
**Integrity checks** (`audit.verify_evidence_completion`, which `offline_eval` calls and which opens `runs.jsonl` and
`evaluation_block.jsonl`) are a carve-out: before step 5 they run only inside the release step, by reviewed code
that outputs pass/fail, counts and hashes, never a value.

- A label value of a test instance, or any evaluation value, read before step 5 — sweep 1 included (except the
  integrity carve-out).
- An arm trained, tuned or selected on test, or on any evaluation-seed value.
- The arms-frozen record missing or changed after it is committed.
- A gate whose sha256 differs from the bound one (R1-BX-D8-CONFIRM, or the v3.1 row), or NumPy other than 2.4.4.
- A split that differs from the signed split file.
- Under T1 K = 6, any use of seeds 7004–7005 or 7009–7010.
- The gate's own STOPs (§5) and the leave-one-suite-out STOP.

## 7. Reporting

- The primary verdict; the PRE-DUP secondary and PRE-WDBC sensitivity runs; the per-node table; per-tier descriptive
  statistics; the t1_by_suite counts and the suites without a labelled T1 node; the number of labelled T1 nodes.
- The PRE-SECONDARY analyses, each marked descriptive.
- The power (PRE-POWER); the tie disclosure if utilities tie; partial and divergent counts (PRE-DIV); the PRE-DUP
  disclosure; sweep 1 as a descriptive stratum (PRE-MEM).

## 8. Release rows this preregistration needs (proposed ids; under PRE-STAGE A)

- **R1-S2-LABELS-TRAINDEV-RELEASE** (train/dev label blocks of both sources) and **R1-S2-LABELS-TEST-RELEASE**
  (test label blocks and every evaluation block), each citing this preregistration's sha256 (the test row also the
  arms-frozen record's).
- **R1-T1-LABELS-UNSEAL** and **R1-T1-LABELS-TEST-RELEASE** for T1, as in the G.5 draft, citing this preregistration.
- Under PRE-WDBC B: the row binding gate v3.1's sha256.

## 9. What remains to build (reviewed units before step 2)

- The split-file generator (both tiers) and its sha256.
- Gate v3.1 (PRE-WDBC B), with the eight-node reproduction test.
- The fold-analysis module (PRE-SECONDARY).
- The release step's integrity checks that output only pass/fail, counts and hashes (§6 carve-out).
- The release step and the partition-reading locks for both sources (PRE-STAGE A).
- The gate-input builder: the §3 definitions, PRE-MEM, PRE-DUP, PRE-DIV, train/dev/test blocks after step 5, in
  `r1_d8_gate_input/v3` (`v3.1` under PRE-WDBC B).
- The Track P runner's switch to P3 (P.4 draft) and the exam set redrawn within P3 train.

```
frozen: false
split_file: <path and sha256>
pre_wdbc: <A | B | C>
pre_split: <A | B>
pre_mem: <A | B | C>
pre_joint: <A | B>
pre_select: <A | B>
pre_a2: <A | B | C>
pre_delta: <A | B>
pre_dup: <A | B>
pre_div: <A | B>
pre_t1: <A | B>
pre_secondary: <A | B>
pre_stage: <A | B>
pre_power: <A | B>
gate_sha256: ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee <or the v3.1 sha256 under PRE-WDBC B>
gate_input_builder_sha256: <the reviewed builder's sha256>
signed_by: <author>
frozen_utc: <set at signature>
```
