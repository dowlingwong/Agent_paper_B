# Sweep-2 C3 analysis preregistration — draft for the author (frozen: false)

**Status: DRAFT. `frozen: false`. Nothing here is analysed or read.** The preregistration becomes binding when the
author signs it and the coordinating chat commits the signed copy to `main` as
`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_<YYYYMMDD>.md`. Its sha256 is then cited by the release rows
that open the label tables to the analysis (§8), so that the analysis cannot start before it exists, and it is
fixed "so analysis can start the day the labels unlock" (queue of 19–20 Nov).

Written by the Mac-desk agent (Claude), AI-assisted, from published `main` `4aac5209` (PLAN as at `94db94bb` plus
R1-S2C3B-WDBC). It decides nothing on its own: §2 lists the author decisions, each with options and a
recommendation; every other rule is quoted from a PLAN row or from the pinned gate.

## 1. What is fixed elsewhere (quoted, not decided here)

| Source | Fixed |
|---|---|
| R1-BX-D8 | The primary criterion is the across-node aggregate: the IQM of gap closed and the probability of improvement (PoI) of A3 or A5 over A2, with node-stratified bootstrap CIs; per node, gap closed = (U_arm − U_A2) / (U_oracle − U_A2) on test instances with `y_eval`; U is the one-step utility scaled to a 20-run campaign; U_oracle is the noisy-oracle ceiling (TRACK_P §7.1); Holm over A3 and A5 at family-wise one-sided α = 0.05 (97.5 % for the first-ranked arm, 95 % for the second); the point IQM is reported against 0.1. The per-node table is secondary. |
| R1-BX-D8-V3-A | (1) A nonpositive point test denominator on an IQM-eligible node is a STOP; in a resample it sets that node's gap closed to −∞. (2) IQM-eligibility: the paired z of oracle − A2 over train + dev ≥ 3 and the dev denominator ≥ δ_n. (3) **Split P3 = 1/3 : 1/6 : 1/2 per tier, supplied by the caller and written into the analysis preregistration.** |
| R1-BX-D8-V3-B | (4) Pass rule (b2): the studentized node-stratified bootstrap lower bound of the IQM > 0 and the PoI lower bound > 0.5. (5) **Per-tier test floor: T0 ≥ 9 and T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported.** T1 = 12 instances per node; the paper reports the gate's power (D8-PASS: mean two-arm power 0.36 at g = 0.3); no post-hoc Johnson t. |
| R1-BX-D8-CONFIRM | Gate `r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee`; T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, with the count disclosed; leave-one-suite-out needs at least one labelled T1 node per suite, otherwise leave-one-suite-out STOPs (the aggregate gate does not). Existing preregistration and analysis gates remain in force; sweep-2 label tables may be analysed from this row on. |
| D18 | δ_n = max(0.002, 0.25 × median paired sd(Δ̂)) per node, in metric units; the unit of the C3 gate, scaled to a 20-run campaign. |
| R1-MAIN-PROPOSER (e) | The B.7 gate, the A5/A6 evidence checkpoints and the C/D tables use sweep 2; sweep 1 is added as a stratum; choosing pooled training over sweep 2 alone is fixed on validation before any test read *(proposed)*. Twin campaigns give the same (instance, incumbent, edit) the same label in both sources, so: (1) **both sources use one instance → train/dev/test assignment**; (2) the cross-proposer table goes from one source's train partition to the other's test partition only; (3) duplicates are grouped across sources by (instance, incumbent hash, edit hash) for folds and deduplication; (4) pooled intervals use an instance-cluster bootstrap. |
| R1-B2-DECOUPLE; R1-BX-D3 | Labels from seeds 7001–7005, the evaluation value from 7006–7010; K = 10 on T0 (sweeps 1 and 2). |
| R1-MAIN-PROPOSER (b); `c3_sweep2_20261119.md` | Sweep 2: the eight sweep-1 nodes, 18 instances, W = 20, memory `append_only_summary` and `none`, the sweep-1 instance seeds, structure-only `manager_proposal/v1`, temperature 0.2 with the D26 seed, the Track X pick with thinking off. |

**The gate's own conventions** (`gate.py` docstring and `M11_D8_GATE_V3_20261116.md` §3, "preregistration
candidates"). This preregistration adopts them as written, so they are no longer open: the t* = +∞ sentinel 1e12; ŝe = 0
ignores screened resamples; ties in G by a stable sort over sorted node ids; the Holm ranking (first-level pass, then
the composite tail share, then A3 before A5); the split check (`off_split`, `off_design_size` reported, never a STOP);
the train + dev z with z = 3 eligible; the added report fields; the tie disclosure (PoI ties count ½; the calibration
evidence covers continuous utilities only). Environment: NumPy exactly 2.4.4, seed 20261108, PCG64, 2,000 resamples,
linear quantiles.

## 2. Author decisions

### PRE-SPLIT: one instance assignment for the gate and for Track P (recommendation: A)

P3 per tier: **T0** 18 instances per node → 6 train : 3 dev : 9 test; **T1** 12 → 4 : 2 : 6. R1-MAIN-PROPOSER (e)
requires one assignment for both sources. Two existing splits differ from P3:
- `r1/c3/offline_eval.py` (sha256 `5990f384…`) cross-fits by instance (K-fold; every instance is held out once). That
  is not a train/dev/test split and cannot feed the gate.
- The Track P SFT split (`trackp_sft/v1`: 3 test, 3 validation, 12 train per T0 node) puts 6 of the 9 P3 test
  instances of a node into training. An A5 arm trained on it and evaluated on P3 test would have seen test instances.

Options:
- **A (recommended): P3 is the only evidence split.** Per node, instances are ordered by
  `sha256("c3_p3_split/v1:" + <node> + ":" + <instance seed>)`; T0: the first 9 are test, the next 3 dev, the last 6
  train; T1: as the G.5 draft's G5-SPLIT (first 6 test, next 2 dev, last 4 train, its own salt). The same assignment
  serves sweep 1 and sweep 2 (the same instance seeds) and every arm, A5 included. The SFT split `trackp_sft/v1` stays
  for ENGINEERING runs only; the P.4 runner unit switches Track P evidence runs to P3 (a reviewed change). The signed copy
  records the assignment and its sha256.
- **B: keep the SFT split for Track P and P3 for the other arms.** Violates "one assignment" and leaks test instances
  into A5. Not acceptable as evidence.

### PRE-DUP: duplicates across instances in the gate (recommendation: A)

The same (node, incumbent hash, candidate hash) can occur on a train/dev instance and on a test instance. Its
label-seed label is then in an arm's training data, and its test utility uses the evaluation seeds of the same pair.
- **A (recommended):** the gate's primary run uses the test proposals whose key does not occur on any train or dev
  instance (as R1-TRACKP-SFT-DUP for Track P); a secondary run on the full test population is reported beside it.
  Instance counts, and so the test floor, are unchanged; only proposals drop out.
- **B:** the full test population only. Simpler; the gain then includes recall of pairs seen in training.

### PRE-POOL: pooled (sweep 1 + sweep 2) versus sweep-2-only training (recommendation: A)

R1-MAIN-PROPOSER (e) proposes choosing it on validation before any test read.
- **A (recommended):** per arm, train both variants on their train instances, and keep the one with the higher mean dev
  utility U (20-run scale, g = 0.1 σ_node) over all nodes; ties go to sweep-2-only. The choice is recorded in the
  arms-frozen record (§6) before the test read.
- **B:** sweep-2-only for every arm (no choice to make; sweep 1 enters only as a reported stratum).

### PRE-A5: which A5 enters the gate (recommendation: A)

The gate takes one A5 series (`gate.SERIES` = A2, oracle, A3, A5). R1-C3-POOL-EXAM sends both Kev sizes on to P.3b
and A5 and carries the Qwen control; C3_DESIGN lists further A5 bases.
- **A (recommended):** the Kev base (0.8B or 4B) with the higher mean dev utility, chosen before the test read; the
  other Kev base and the controls are reported as secondary rows, not tested.
- **B:** pre-declare Kev-4B.

### PRE-STAGE: staged release of the sweep-2 tables (recommendation: A)

R1-BX-D8-CONFIRM lets the sweep-2 tables be analysed from that row on; it does not order train/dev reads before test
reads.
- **A (recommended):** the readers refuse test-instance labels and evaluation values until a test release row exists
  that cites this preregistration's sha256 and the arms-frozen record's sha256 (§4, §8). A new restriction on top of
  R1-BX-D8-CONFIRM, enforced in code.
- **B:** procedure only (§4 is followed and recorded, no code lock). Fewer rows; the order is then attested, not
  enforced.

## 3. Data entering the analysis

- **T0:** the sweep-2 B.2-style audit's label and evaluation blocks (once audited, frozen and released), the eight T0
  nodes of `gate.T0_NODES`, both memory modes, 18 instances per node. Sweep 1 enters per PRE-POOL.
- **T1:** the G.5 label table, released by R1-T1-LABELS-UNSEAL (train and dev) and R1-T1-LABELS-TEST-RELEASE (test).
  Partial T1 is read as R1-BX-D8-CONFIRM says.
- **Utilities:** the gate takes one U per (arm, instance) (`r1_d8_gate_input/v3`). U = 20 × the weighted mean of the
  realised one-step value r = Δ_true × keep − g × execute over the instance's logged proposals, with
  `offline_eval`'s population weights (no-ops and duplicates weight 1; randomly audited non-inert proposals
  N_noninert / N_audited of their stratum; DI-selected audits weight 0) and its primary run accounting. Test
  utilities take Δ_true from the **evaluation** block; the oracle's decisions use the **label** block only (`gate.py`
  docstring). g = 0.1 σ_node primary (0.05 and 0.2 reported as sensitivities, no verdict). Under PRE-DUP A the excluded
  proposals leave the instance's weighted mean (the remaining weights are renormalised), so U stays a 20-run value.
- **δ_n:** D18, from the node's noise floor (T0: the C1 table; T1: G.1b on H200).

## 4. Procedure (in this order)

1. Commit this preregistration (signed) and the split file.
2. Release train and dev (the release rows of §8). Build the gate inputs on train/dev only.
3. Train each arm on train; select hyperparameters, PRE-POOL and PRE-A5 on dev; fit any calibration on dev.
4. Commit the **arms-frozen record**: per arm, the code commit, checkpoint and calibration sha256s, the PRE-POOL and
   PRE-A5 choices, and the dev metrics. Nothing in it may change after step 5.
5. Release test (the test release row cites the arms-frozen record's sha256). Compute the test utilities.
6. Run `gate.py` (the pinned sha256) once on the primary input and once on the secondary input (PRE-DUP). Commit the
   inputs, outputs and their sha256s.
7. Leave-one-suite-out, if each suite has a labelled T1 node; otherwise its STOP is reported.

A gate run is never repeated after its output is seen. An error found after step 6 is corrected in a dated erratum that
reports both runs.

## 5. Floors and eligibility (as the gate applies them)

- Test floor per node: T0 ≥ 9, T1 ≥ 3 test instances; below it, a node is out of the IQM, in the PoI, reported.
- Eligibility: train + dev paired z of oracle − A2 ≥ 3, and the dev denominator ≥ δ_n.
- No eligible node: STOP (the IQM is undefined). A nonpositive point test denominator on an eligible node: STOP.
- These are reported per node: n_train, n_dev, n_test, the floor, z, the denominator, the eligibility reasons, and
  `off_split` / `off_design_size`.

## 6. STOPs

- A label or evaluation value read before its release step.
- An arm trained, tuned or selected on test, or on the evaluation seeds of train/dev proposals.
- The arms-frozen record missing or changed after the test release.
- A gate whose sha256 differs from R1-BX-D8-CONFIRM's, or NumPy other than 2.4.4.
- A split that differs from the signed split file.
- The gate's own STOPs (§5) and the leave-one-suite-out STOP.

## 7. Reporting

- The primary verdict (PRE-DUP primary), the secondary run, the per-node table, per-tier descriptive statistics, the
  t1_by_suite counts and the suites without a labelled T1 node.
- The gate's power (D8-PASS: mean two-arm power 0.36 at g = 0.3 on T1 × 12), as R1-BX-D8-V3-B asks.
- The tie disclosure if the utilities tie.
- Partial T1: the number of labelled T1 nodes.

## 8. Release rows this preregistration needs (proposed ids; under PRE-STAGE A)

- **R1-S2-LABELS-TRAINDEV-RELEASE** and **R1-S2-LABELS-TEST-RELEASE** for the sweep-2 T0 tables, each citing this
  preregistration's sha256 (the test row also the arms-frozen record's). R1-BX-D8-CONFIRM opened the sweep-2 tables to
  analysis as a whole; these rows only order the reads. Under PRE-STAGE B they are not needed.
- **R1-T1-LABELS-UNSEAL** and **R1-T1-LABELS-TEST-RELEASE** for T1, as in the G.5 draft, citing this preregistration.

## 9. What remains to build (a reviewed unit before step 2)

- The P3 split file generator and its sha256.
- The gate-input builder: arms trained on P3 train, selected on dev, test utilities from the evaluation block, the
  primary/secondary populations of PRE-DUP, in `r1_d8_gate_input/v3`.
- The P.4 runner's switch of Track P evidence runs to P3 (PRE-SPLIT).
- The release-row locks in every reader.

```
frozen: false
split: <the P3 split file path and sha256>
pre_split: <A | B>
pre_dup: <A | B>
pre_pool: <A | B>
pre_a5: <A | B>
pre_stage: <A | B>
gate_sha256: ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee
offline_eval_sha256: <the reviewed gate-input builder's sha256>
signed_by: <author>
frozen_utc: <set at signature>
```
