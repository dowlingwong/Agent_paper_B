# Direct ancestor–descendant test of the screening property (R1-D3-CHOICES (1))

**AI-assisted (Claude, subagent, 22 Nov 2026). Label `ENGINEERING_ONLY`.** Nothing here is evidence or an author decision. It asks for nothing to be run on a remote host. Branch `mac-screening-test-20261122`, based on `author-minsub-20261122`. Rows read first: R1-D3-CHOICES and R1-THEORY-RHO (PLAN §10) and `docs/r1/CURRENT.md`. Process tier: S (support code and a document). It needs one fresh-session review under `reviews/` before anyone relies on it (R1-PROCESS-TIERS). Nobody has reviewed it yet.

- Script: `r1/noise/screening_test.py`.
- Tests: `r1/tests/test_screening_test.py`, 13 unittest cases on synthetic data. Under the kernel model the pooled partial is about 0. Under the shared-component model it is above 0 and matches its closed form.
- Outputs: `results/r1/engineering/screening_test_20261122/design.json` (metadata only) and `run.json` (the test).

## 1. Data permissions (fixed before any data was opened)

What the test needs: for each triple g → p → c on one lineage (g an ancestor of p, p an ancestor of c), the error **of each configuration at each seed**, on seeds the three share. A mean paired difference per proposal is not enough, because the partial correlation is a property of errors at the seed level.

| Source | Has g–p–c triples on common seeds? | May it be read now? | Row or file | Opened? |
|---|---|---|---|---|
| E1 / noise-floor runs: `E1_20261012…`, `E1_20261022T214606Z` (PILOT, 30 joint seeds 3001–3030), `E1_remeasure_…`, `E1_D28_REPAIR_20261027` (the pinned noise source), `E1_D28_CLIMATE_…` | **No.** Each node has c0 and five single edits of c0 (`edits.json`, `e1_noise_floor.py`). These are siblings, which is the proxy geometry; there is no child of an edit. | Yes. PILOT, not sealed, seeds outside every protected block. R1-THEORY-RHO (5): before the check enters the paper, the author must still accept the 22 Oct data. | R1-THEORY-RHO (5); RUNBOOK §1 (PILOT is never a result) | Only `edits.json`, manifests and wall times. No metric. |
| T1 noise floors (G.1b) and the T1 pilot (G.4) | **No.** G.1b has c0 plus four declared single edits (R1-G1B-EDITS), siblings again. These are also GPU nodes, where the CPU CRN premise does not apply. | **No.** Sealed on the TASL hosts. Summaries leave the sealed tree only through a reviewed step, before the T1 train/dev row (R1-SWEEP2-RELEASE-DECISIONS, REL-T1-G1B). | `authorizations/g1b_t1_tasl_20261121.md`; R1-SWEEP2-RELEASE-DECISIONS | No |
| Sweep-1 B.2 fresh-seed audit (`docs/r1/reports/b2_audit_20261119/` on main): label seeds 7001–7005, evaluation seeds 7006–7010 | **In principle yes.** Each proposal's candidate *and* incumbent are run on the same joint seeds 7001–7010 for every proposal (`audit.py`: "K common fresh joint seeds"). So a kept proposal (g → p) and a later proposal from p (p → c) share seeds. | **No.** (a) Only `runs.jsonl` holds per-configuration, per-seed values. It sits in an evidence audit directory, and every file there is refused until the T0 test release row exists (`release.py` locks; prereg §6). (b) The released partition `label_block.traindev.jsonl` holds only `delta_label` and `se_label` per proposal (`audit.evidence_blocks`), so it cannot give the test. (c) R1-S2-LABELS-TRAINDEV-RELEASE exists, but no release receipt (`RECEIPT.json`, `label_block.traindev.jsonl`) exists on main or on any branch: the release step has not run. (d) Seeds 7006–7010 and test-instance labels stay sealed until the arms-frozen record (prereg §6, PRE-STAGE A). | Prereg `C3_SWEEP2_ANALYSIS_PREREG_20261121.md` §3, §6; `r1/c3/release.py`; R1-S2-LABELS-TRAINDEV-RELEASE; R1-SWEEP2-RELEASE-DECISIONS | No. No file in that directory was opened. |
| Sweep-2 fresh-seed audit (seeds 7001–7010, same design) | Same as sweep 1 | **No.** The audit is authorized (R1-SWEEP2-B2-GO), but no completion record is on main. The release STOPs until a sweep-2 audit is run and registered (R1-SWEEP2-RELEASE-DECISIONS). The same locks and the same means-only label rows apply. | R1-SWEEP2-B2-GO; R1-SWEEP2-RELEASE-DECISIONS; prereg §6 | No |
| Sweep-1 campaign tables (`results/r1/evidence/C3_sweep_*`) | Each trial runs once, on its campaign's seed. One configuration triple would have to recur across instances to give several seeds. | **Unclear, so not opened.** `analysis_guard.guard_table` passes the frozen sweep-1 index. But the rows carry `label: EVIDENCE`, which `evidence_boundary` marks as identifiable sweep evidence that needs a verified label-only boundary. | `r1/c3/analysis_guard.py`; `r1/c3/evidence_boundary.py` | No |
| 19 Oct C3 pilot audits (`results/r1/engineering/c3_audit_pilot_20261019T001338Z`, K = 6, seeds 7001–7006) | Per-seed candidate and incumbent metrics | **Unclear, so not opened.** No PLAN row covers it. Its seeds include 7006, an evaluation seed under K = 10. Any configuration it shares with a sweep proposal (at least the default c0, the first incumbent of every campaign) would show values at an evaluation seed. | Prereg §6 (no evaluation value before step 5); no row | No |
| Track S S0.5 (`results/r1/tracks/{digits_mlp,tabular_mlp}/s05_t7_*`), CPU nodes, ENGINEERING_ONLY | **Yes.** `s05b_truncated.jsonl` holds, per root, the incumbent of one campaign ledger cut at W = 8, 10, 12 and 20, with its value at each of the instance's five S0.5 audit seeds (`y_terminal_per_seed`). `audit_runs.jsonl` holds the start configuration c0 on the same seeds. Incumbents change only on keeps, so c0 → I_8 → I_10 → I_12 → I_20 is one lineage. Each instance has its own seeds, `200000 + 20 i + k`, which are outside every protected block. | **Yes.** R1-TRACKS-STOP4-END: all Track S data stays ENGINEERING_ONLY. It is disclosed only in the appendix, as the pilot findings that explain the stop, and is **never cited as a result**. Nothing seals or guards it. The scenes on the hosts stay untouched; this test reads only the copies in the repository. | R1-TRACKS-STOP4-END, R1-TRACKS-STOP4-CONSEQUENCES (9); RUNBOOK §1 | Yes (§3) |
| Track S S0.4 dev audits and S0.5 calibration audits (every executed proposal: candidate and incumbent on common seeds) | Yes on the hosts. In the repository copies the rows carry no configuration hashes, and the campaign ledgers (lineage) are only in `scratch/` on TASL-2 and TASL-7 (`TRACKS_RESOURCES_AND_SCENES_20261115.md`). | Reading is allowed (same rows), but the lineage cannot be rebuilt from the repository. | as above | Hashes, seeds and decisions only |
| E1b headroom pilot (`results/r1/pilot/E1b_*`), PILOT | **Some.** For each instance: c0 and the snapshot incumbents I_4, I_8 and I_12 (a leaf of that snapshot with no keep afterwards ends at the snapshot incumbent), plus final incumbents of leaves with keeps (descendants of I_b), all on audit seeds 5001–5006. **These six seeds are the same for every configuration of a node**, so the effective seed sample is six per node. | Yes. PILOT, not sealed, seeds outside every protected block. | R1-E1B-RERUN2; RUNBOOK §1 | Yes (§3; descriptive only) |

Summary: the only readable sources with ancestor–descendant triples on common seeds are **Track S S0.5** (`digits_mlp`, `tabular_mlp`) and **E1b**. The audits that will decide C1 and C3 (sweep 1 and sweep 2) would be the best source, because their incumbent/candidate pairs chain on shared seeds. They cannot be used now: their per-seed values sit in locked evidence directories until the test release, and the released label rows hold only means. No OpenML node is covered by a readable source with independent seed sets.

## 2. Design (committed before the run; commit SHA in §2.6)

### 2.1 Quantity

Take g → p → c on one lineage, evaluated on common seeds.
- Under the kernel of T4 Proposition 9 and T2 Proposition 4(a), ε | e ∼ N(ϱe, σ_c²) applied link by link, the errors form a Gaussian Markov chain. Then corr(e_c, e_g | e_p) = 0 for **any** number of edits per link.
- Under e = u + w, with u shared by every configuration at a seed and w following the kernel along the lineage, corr(g, p) = s + (1 − s)r₁, corr(p, c) = s + (1 − s)r₂ and corr(g, c) = s + (1 − s)r₁r₂. The partial correlation is positive.
- With one edit of the same kind per link, the partial is the T5 sibling partial: 0.24 at s = 0.708 and 0.37 at s = 0.789, both at ϱ = 0.82 (unit test `test_t5_calibration_values`).
- With longer links (r^k → 0), it tends to s/(1 + s).

So the null is the same for the one-edit geometry and for longer links. The links here are one or more *kept* edits, not exactly one.

The audit seeds are fresh: they were not used for any keep decision. The test is therefore about the structure of the error field over (configuration, seed). It is not distorted by the selection of incumbents.

### 2.2 Statistic

- **Centring:** each configuration's values are centred by its own mean over the common seeds. This removes its true value.
- **Per triple:** the sample partial correlation corr(c, g | p).
- **Exclusions:** a triple is dropped (and counted) if any member has zero spread, if |corr(g, p)| ≥ 0.999 or |corr(p, c)| ≥ 0.999 (partial undefined), or if two members have identical value vectors (the same configuration, e.g. a revisit). Under CRN on CPU, identical configurations give identical vectors.
- **Pooling within a node:** the equal-weight mean of the eligible per-triple partials.
- **Interval:** 95 % percentile bootstrap with 2,000 resamples, generator seed 20261122.
  - Track S: resample instances, each with all its triples. Each instance has its own seeds and its own campaign.
  - E1b: resample the six shared seeds jointly across all triples.
- **No pooling across nodes:** each node gets its own verdict, as R1-D3-CHOICES (1) asks ("on a node").

### 2.3 Chains

**Track S, primary.** Per instance, the root with policy `a2u` and rep 0. Its chain is [c0, I_8, I_10, I_12, I_20]:
- consecutive repeats are removed (an incumbent unchanged between two cut points);
- an element with a missing audit value is dropped, which keeps the ancestor order;
- the triples are the consecutive ones, (chain[k], chain[k+1], chain[k+2]).

The `static` rep-0 root of the same instance has the same action sequence (R1-TRACKS-STOP4-END finding (2)). Identical chains count once.

How c0 is identified: in calibration order (`collect.calibration_rows`, candidate first, then incumbent), c0 is the **second distinct configuration hash** among the `audit_runs.jsonl` rows on an instance's seeds. All 20 primary instances must agree, and c0 must be present on all their seeds. Otherwise c0 is left out.
- A first rule ("the only hash audited on every instance") failed on metadata. Six hashes (digits) and five (tabular) are audited on all instances, because campaigns start alike.
- It was replaced before any audit value was read. Both rules use only hashes, seeds and file order.

**Secondary, all descriptive, no verdict:**
- (a) all ordered triples i < j < k of each chain;
- (b) the rep-1 chains (static, 10 instances) added;
- (c) chains without c0;
- (d) E1b per node, triples from the chain [c0, I_4, I_8, I_12] plus branch triples (ancestor, I_b, F) for each distinct final incumbent F of a leaf with keeps, with the seed bootstrap.

E1b never decides anything: with six seeds shared by every configuration, its power at p = 0.37 is 0.08–0.24 (§2.5).

### 2.4 Decision rule (pre-specified)

For each Track S node, on the primary statistic:
- **SHARED** if the 95 % interval lies entirely above **0.1**;
- **NO_SHARED** if it lies entirely below 0.1;
- **INCONCLUSIVE** otherwise.

There is no multiplicity correction over the two nodes. Under the kernel model the simulated chance of SHARED is ≤ 0.002 per node (§2.5), so the family-wise false-positive rate stays below 0.01.

Mapping to R1-D3-CHOICES (1), written as the recommendation §4 will give:
- SHARED on **either** node: recommend proposing the seventh D.3a arm ("A2 with a keep-count threshold correction") before D.3 is signed.
- Otherwise the row's "otherwise" branch applies: R1-THEORY-RHO (2) stands.
- If any node is INCONCLUSIVE, §4 says so, gives the power, and offers the measurement of §4.2 for an author who wants a decisive answer before signing.

### 2.5 Power for the data available (`design.json`; metadata only, no audit value)

How the chain structure was obtained:
- keeps from the roots' `decisions`;
- the trials in each truncation from `s05b_truncated.jsonl`;
- c0 found by the rule in §2.3.

Simulation settings: the u + w model at T5's `digits_mlp` calibration, ϱ = 0.82 per link, K = 5 seeds per instance, 500 replicates, the same bootstrap and rule.

| node | instances | chain lengths (count) | consecutive triples (expected) | kernel s = 0: P(SHARED) / P(NO_SHARED) | s = 0.708 (p = 0.24): P(SHARED) | s = 0.789 (p = 0.37): P(SHARED) |
|---|---|---|---|---|---|---|
| `digits_mlp` | 20 | 2:3, 3:6, 4:8, 5:3 | 31 | 0.000 / 0.21 | 0.24 | 0.61 |
| `tabular_mlp` | 20 | 3:4, 4:8, 5:8 | 44 | 0.002 / 0.23 | 0.28 | 0.82 |

At five seeds the per-triple partial is attenuated: its simulated mean is 0.31 when the population value is 0.37, and 0.20 when it is 0.24. The simulated sd of the pooled estimate is about 0.10 on digits and 0.08 on tabular.

What the test can do:
- **Detect a shared component of the size the E1 proxy suggests** (p ≈ 0.37), with probability about 0.6 on digits.
- **Rarely detect the proxy's lower end** (p ≈ 0.24).
- **Rarely certify its absence:** P(NO_SHARED | kernel) is about 0.2.

It is a one-way screen. INCONCLUSIVE is the most likely outcome unless the effect is near the E1 point estimate.

E1b (secondary; upper bounds, because c0 has no recorded hash and is taken as distinct from I_4):

| node | instances | chain + branch triples (upper bound) | P(SHARED) at p = 0.37 |
|---|---|---|---|
| `digits_mlp` | 16 | 1 + 9 | 0.18 |
| `openml_ionosphere` | 36 | 0 + 13 | 0.24 |
| `openml_breast_w` | 18 | 0 + 4 | 0.08 |
| `tabular_mlp` | 18 | 3 + 6 | 0.14 |

### 2.6 Commit

Design, script and tests are committed in the commit that adds this section. Its SHA is recorded in §3, which was written after that commit.

## 3. Results

*Not run yet. Filled in after the design commit.*

## 4. What it means for R1-D3-CHOICES (1)

*Written after §3.*
