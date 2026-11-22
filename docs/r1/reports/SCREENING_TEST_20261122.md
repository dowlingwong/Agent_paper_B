# Direct ancestor–descendant test of the screening property (R1-D3-CHOICES (1))

**AI-assisted (Claude, subagent, 22 Nov 2026). Label `ENGINEERING_ONLY`.** Nothing here is evidence or an author decision. It asks for nothing to be run on a remote host. Branch `mac-screening-test-20261122`, based on `author-minsub-20261122`. Rows read first: R1-D3-CHOICES and R1-THEORY-RHO (PLAN §10) and `docs/r1/CURRENT.md`. Process tier: S (support code and a document). It needs one fresh-session review under `reviews/` before anyone relies on it (R1-PROCESS-TIERS). Nobody has reviewed it yet.

- Script: `r1/noise/screening_test.py`.
- Tests: `r1/tests/test_screening_test.py`, 13 unittest cases on synthetic data. Under the kernel model the pooled partial is about 0. Under the shared-component model it is above 0 and matches its closed form.
- Outputs: `results/r1/engineering/screening_test_20261122/design.json` (metadata only) and `run.json` (the test). Correction round after the independent review (`docs/r1/reviews/SCREENING_TEST_REVIEW_20261122.md`, ACCEPT WITH MINOR): `posthoc.json` and `posthoc_option_a_k120.json`, written by `r1/noise/screening_posthoc.py`. These are post hoc and unreviewed.

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
| E1b headroom pilot (`results/r1/pilot/E1b_*`), PILOT | **Some.** For each instance: c0 and the snapshot incumbents I_4, I_8 and I_12 (a leaf of that snapshot with no keep afterwards ends at the snapshot incumbent), plus final incumbents of leaves with keeps (descendants of I_b), all on audit seeds 5001–5006. **These six seeds are the same for every configuration of a node**, so the effective seed sample is six per node. | Yes. PILOT, not sealed, seeds outside every protected block. **Disclosure** (review NOTE 3): E1b's instances are the P3 T0 instance-seed universe (R1-E1B-RERUN2, k = 0–17), so its values touch P3 test instances. They involve no label or evaluation seed, so prereg §6 does not bar them, and E1b decides nothing here. If this test is cited in the D.3 record, list E1b in the arms-frozen disclosure. | R1-E1B-RERUN2; RUNBOOK §1; prereg §6 | Yes (§3; descriptive only) |

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
- Git cannot date the change (review NOTE 1). Both rules predate `4b65f91c`; only the second is in that commit. The record is this paragraph and the fact that a metadata failure forced the change.
- The rule is correct only if two things in the Track S collector hold. Both are verified by the review on `origin/trackS-ops-20261030`:
  - `collect.calibration_rows` audits the candidate first (`r1/tracks/collect.py:1008-1009`);
  - `AuditCache` writes each (hash, seed) once (`:379-393`).
- The check that all 20 instances agree is a weak safeguard, because campaigns start alike.

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

At five seeds the per-triple partial is attenuated: its simulated mean is 0.31 when the population value is 0.37, and 0.21 when it is 0.24. The simulated sd of the pooled estimate is about 0.10 on digits and 0.08 on tabular.

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

§§1–2, the script, the tests and `design.json` were committed as **`4b65f91c`** before `run` was executed. Until then no audit value had been read; the only Track S files read were decisions, truncation trial counts, configuration hashes, seeds and file order. §§3–4 and `run.json` were added in a later commit. The script was not changed between the two commits.

"No audit value read" means none was used, printed or written (review NOTE 2):
- `design` parses whole rows of `s05b_truncated.jsonl` and `audit_runs.jsonl`, and of the E1b leaf files, value fields included.
- It uses only metadata from them, and `design.json` holds no value.
- I did not print or otherwise view any value before the run. Nothing but this statement records that.

Correction round: the docstring of `screening_test.py` was changed to describe the c0 rule actually used (review MINOR 1). That edit is a docstring only and changes no code path.

## 3. Results (`run.json`; script as at `4b65f91c`)

c0 was identified on both nodes by the §2.3 rule: all 20 primary instances agree, and c0 is present on all five seeds of each. Both nodes give the same hash, `3e5bf106…`. The configuration hash covers the parsed hyperparameters, and the two MLP nodes share their defaults; their values are measured per node.

### 3.1 Track S, primary (pre-specified decision)

| node | eligible consecutive triples (instances) | excluded | pooled partial corr(c, g \| p) | 95 % interval | decision | mean marginal corr g–p / p–c / g–c |
|---|---|---|---|---|---|---|
| `digits_mlp` | 31 (17) | 0 | **+0.087** | [−0.116, +0.292] | **INCONCLUSIVE** | 0.37 / 0.81 / 0.38 |
| `tabular_mlp` | 38 (19) | 6 near-singular | **−0.223** | [−0.365, −0.079] | **NO_SHARED** | 0.64 / 0.99 / 0.62 |

The realised chain lengths equal the design-time counts from metadata (digits 2:3, 3:6, 4:8, 5:3; tabular 3:4, 4:8, 5:8).

### 3.2 Secondary (descriptive; no verdict)

| node | (a) all ordered triples | (b) with the rep-1 chains | (c) without c0 |
|---|---|---|---|
| `digits_mlp` | −0.040 [−0.199, +0.138], 68 triples | +0.096 [−0.058, +0.260], 41 | +0.085 [−0.200, +0.379], 14 |
| `tabular_mlp` | −0.001 [−0.178, +0.162], 103 | −0.179 [−0.299, −0.052], 56 | −0.405 [−0.615, −0.149], 19 |

**(d) E1b**, six audit seeds shared by every configuration of a node, seed bootstrap. Descriptive only.

| node | triples | pooled partial | interval |
|---|---|---|---|
| `digits_mlp` | 10 | +0.25 | [−0.45, +0.80] |
| `openml_ionosphere` | 7 | −0.65 | [−1.00, −0.33] |
| `openml_breast_w` | 2 | −0.94 | [−1.00, −0.47] |
| `tabular_mlp` | 4 (5 near-singular) | +0.13 | [−0.33, +1.00] |

With six shared seeds and a handful of dependent triples, these intervals mean little (§2.5). They are listed because the source is readable, not as findings.

### 3.3 Reading

1. **No node supports a shared component** under the pre-specified rule.

2. **`digits_mlp` is inconclusive.** The interval contains 0 and contains 0.1.
   - The point estimate, +0.09, is well below the E1 sibling proxy's +0.37.
   - *Post hoc and approximate* (normal approximation to the design simulation's mean and sd, not pre-specified): an estimate this low or lower has probability about 0.01 under the T5 target calibration (p = 0.37; simulated mean 0.31, sd 0.10), about 0.11 under its lower end (p = 0.24; mean 0.21, sd 0.10), and about 0.21 under the kernel model (upper tail).
   - **That comparison depends on the model.** The reference simulation puts ϱ = 0.82 on every link. The realised digits links differ: the mean g–p correlation is 0.37, because c0 → I_8 spans several keeps, and the mean p–c is 0.81. So the target calibration is *not supported* by these data, but only against a reference whose link geometry differs from the data. It is not shown to be less likely.
   - **Split by link kind** (post hoc, unreviewed; `posthoc.json`; the review computed the same split):

     | links | triples | mean partial |
     |---|---|---|
     | p and c clearly differ (r_pc < 0.95) | 23 | **+0.17** |
     | near-duplicate links (r_pc ≥ 0.95) | 8 | **−0.14** |

     The first group is the geometry that matters. It is under-represented, and the primary estimate mixes two kinds of link that point in opposite directions. +0.17 at K = 5 with 23 triples is compatible with a modest shared component, and also with none.
   - The all-triples secondary (−0.04) mixes link kinds in the same way, so it does not add an independent signal.

3. **`tabular_mlp` gives NO_SHARED, with a negative partial.** Screening fails there too, but in the other direction from a shared component. The u + w model cannot represent this.
   - The E1 sibling proxy on tabular was also negative: −0.16 [−0.29, +0.02].
   - **The verdict comes almost entirely from near-duplicate links** (post hoc; `posthoc.json`). 36 of the 38 eligible triples have p–c correlation ≥ 0.95, and 6 more were excluded at 0.999. Triples that start at c0 average −0.04 (19); triples of later incumbents only average −0.41 (19).
   - It is not a small-sample bias. Under the null, a 5-point partial is Uniform(−1, 1), which is symmetric, and the exclusions select on |r|, not on sign (review MINOR 3).
   - A smoothly varying error field across tiny edits gives negative partials on near-duplicate links: the error of p is then close to an average of the errors of g and c.
   - So tabular's NO_SHARED says little about lineages of **distinct** edits, which is the geometry that matters. Not interpreted further here.

4. **Why the proxy and the direct test may differ on digits** (not decided):
   - (i) noise: the 30-seed proxy interval is [+0.24, +0.51], against 5 seeds × 17 instances here;
   - (ii) a shared component specific to sibling edits of the same hyperparameter family (two of the five E1 edits change `HIDDEN_UNITS`), which lineages through kept edits do not carry;
   - (iii) differences between hosts and harnesses: the E1 PILOT ran on an aarch64 VM at harness `4012897a`, while Track S S0.5 ran on TASL-7 at harness `a3fedbb`, the sweep-2 pin.

**Scope.**
- Two of the eight T0 nodes.
- The links are one or more kept edits, not exactly one.
- The proposer is the Track S manager (llama.cpp, `append_only_summary`), not the sweep-2 proposer. This matters only through which configurations are visited.
- Track S data are ENGINEERING_ONLY and, by R1-TRACKS-STOP4-END, never cited as a result. So this test **cannot** be the direct test that R1-THEORY-RHO (5) requires before the ϱ check enters the paper. It can only inform the D.3 arm question.

## 4. What it means for R1-D3-CHOICES (1): recommendation, not a decision

### 4.1 Recommendation

**Do not propose the seventh D.3a arm now, and run the §4.2 measurement before D.3 is signed.**

Under the pre-specified mapping (§2.4), no node returned SHARED, so the row's "otherwise" branch formally applies: R1-THEORY-RHO (2) stands. A1/A2, the preregistration and the six arms are unchanged, as the row already provides either way.

What changed after the review (MINOR 2–3): the first half of the recommendation stands; the second half is now firmer.
- Neither node's verdict speaks to the geometry that matters, lineages of distinct edits.
  - On digits, those links are 23 of 31 triples. Taken alone they give +0.17 (post hoc).
  - On tabular, NO_SHARED rests on near-duplicate links.
- The existing data therefore neither support nor rule out a shared component where the threshold correction would act.
- I previously offered the §4.2 measurement as optional, for an author who wanted a decisive answer. I now recommend running it before signing. Its design is exactly the geometry that matters, and it is cheap (§4.2).
- If it returns SHARED on a node, the seventh arm should be proposed then, before signing, as R1-D3-CHOICES (1) provides.

Qualifications the author should weigh:
- The test is underpowered on `digits_mlp`: P(SHARED) was 0.24 at p = 0.24 and 0.61 at p = 0.37, and the outcome was INCONCLUSIVE. This is not evidence that the screening property holds there. The T5 target calibration is not supported, but only against a reference whose link geometry differs from the data (§3.3).
- The manuscript's scope statement for R1-THEORY-RHO (2) ("Gaussian approximation … the deployed rule is then conservative") should not imply that the kernel holds on the T0 nodes.
  - A negative-direction failure rests on Track S, which R1-TRACKS-STOP4-END and CONSEQUENCES (9) bar from use as a result even without numbers, and on the unaccepted E1 PILOT data (R1-THEORY-RHO (5)).
  - So the manuscript cannot name it as a finding. At most it can mention it as a possibility, and only once R1-THEORY-RHO (5) is met by citable data.
- None of this enters the paper as evidence (§3.3, Scope).

There are two ways to get the decisive answer.

### 4.2 Option A: the smallest new measurement (draft; `ENGINEERING_ONLY`; nothing run)

- **What.** Single-edit lineages on common seeds, on one CPU host. Per node:
  - c0;
  - the five E1 single edits e_i;
  - every child c_ij = c0 + e_i + e_j where e_j changes a different symbol from e_i and is active in c0 + e_i. On OpenML nodes, `C` is inactive once `model_type` is not logistic regression (`OPENML_ACTIVE`), so such children equal their parent and are skipped.
  - On `digits_mlp` that is 9 children, giving 18 lineage triples (c0, c0 + e_i, c_ij), via e_i or via e_j. OpenML nodes give about 4–8 children each.
- **Seeds.** **120 joint seeds** (train seed = split seed; 60 at the least) from a fresh block outside 7001–7010, the E1 blocks, 5001–5006, the Track S blocks and the D.3 seed blocks; for example 3301–3420.
  - The review found 3301–3360 clear of `RESERVED_SEED_NAMESPACES` (`r1/c3/d3_analysis.py` @ `mac-d3-predecl-20261122`), of the D.3 blocks and of the sweep instance universe. 3361–3420 needs the same check.
  - If Option A is adopted, the block is added to `RESERVED_SEED_NAMESPACES`. Every configuration of a node is re-run on that host, including c0 and the single edits, because cross-host determinism is not guaranteed.
- **Power.** All figures are simulated, unreviewed and recorded with their calls.

  | model | seeds | P(SHARED) at p = 0.24 | P(SHARED) at p = 0.37 | P(NO_SHARED) under the kernel model | record |
  |---|---|---|---|---|---|
  | first figure: independent lineages from c0, **upper bound** | 60 | 0.86 | 1.00 | 0.91 | `posthoc.json` `power_report_call`, `power_e1b([3]*18, 60, s, nsim=100, n_boot=300)` |
  | first figure, upper bound | 30 | 0.64 | 0.98 | 0.66 | same, k = 30 |
  | **actual overlap structure** | 30 | 0.47 | 0.92 | 0.28 | `posthoc.json` `power_option_a` |
  | actual overlap structure | 60 | 0.73 | 1.00 | 0.59 | `posthoc.json` `power_option_a` |
  | actual overlap structure | **120** | **0.95** | **1.00** | **0.82** | `posthoc_option_a_k120.json` (command inside) |

  Notes on the figures:
  - The first figure treats the 18 triples as independent lineages from a shared c0. It does not model shared members: each c_ij appears in two triples, and each c0 + e_i is the middle of up to four. So it is optimistic.
  - The review reproduced 0.85 instead of 0.86 with the default 200 bootstrap resamples. The report's call used 300 and reproduces 0.86.
  - The actual-structure rows simulate the 15 configurations jointly, with every triple on common seeds:
    - null: a symbol-Hamming kernel corr = r^d, which makes every partial in both triples of a child zero at once;
    - alternative: plus a shared component (`screening_posthoc.power_option_a`; 200 replicates at 30 and 60 seeds, 100 at 120).
  - **Recommended: 120 seeds.**

- **Analysis.** `screening_test.triple_partial` with the seed bootstrap and the §2.4 rule, pre-specified as here.
- **Cost.** E1 (22 Oct) measured about 0.9 s of *wall time* per run, under parallel load on a 4-CPU VM (manifest note). The figures below are runs × 0.9 s on one worker:
  - `digits_mlp`: 15 configurations × 120 seeds = 1,800 runs, about 27 minutes (13.5 at 60 seeds);
  - all eight T0 nodes: about 14,000 runs, about 3.5 hours (1.75 at 60 seeds). Budget twice that for slower cores.
- **Host.** deepthought CPUs, the T0 audit host (CURRENT §4; R1-MINSUB-CHOICES (4)). Not the Mac (R1-COMPUTE as revised 24 Oct) and not the TASL pair (T1 table).
  - No row covers this run. It needs an author row naming the host, the seed block and the label.
  - It would run as a tier-S unit: one fresh-session review of the runner before launch.
- **If it is meant to replace the sibling proxy in the paper** (R1-THEORY-RHO (5)), it must instead be an evidence-tier plan: a tier-E pre-declaration with this rule, then a launch binding.

### 4.3 Option B: more power from existing Track S data (no new compute)

- **What.** Copy, read-only, the S0.4 and S0.5 campaign ledgers (`/home/dowling/r1_tracks/scratch/<node>/…/root_trials.jsonl`) from TASL-2 and TASL-7. With them, the lineage of every audited proposal can be rebuilt: the S0.4 dev audits and the S0.5 calibration audits, roughly 300 proposals per node, each with candidate and incumbent on common seeds. That adds many triples on `digits_mlp` and `tabular_mlp`, still at K = 5.
- **Who.** It needs the experiment agent with host access. R1-TRACKS-STOP4-CONSEQUENCES (4) requires a reviewed read-only inventory of TASL-2 before other use, and the scenes must stay untouched (read-only copy).
- **Limit.** The result would still be ENGINEERING_ONLY and never citable, and it still covers only two nodes. Option A is cheaper to reason about and covers all T0 nodes.

### 4.4 Not opened because their status was unclear or forbidden

- **Forbidden:**
  - the sweep-1 B.2 evidence audit directory `docs/r1/reports/b2_audit_20261119/` (no file opened);
  - the sweep-2 audit;
  - G.1b and G.4 outputs (sealed).
- **Unclear:**
  - the 19 Oct C3 pilot audits (`c3_audit_pilot_20261019T001338Z`, seeds 7001–7006, which include an evaluation seed);
  - the sweep-1 campaign tables (`results/r1/evidence/C3_sweep_*`, rows labelled EVIDENCE).

A ruling on these two could make the sweep audits' lineage usable after the test release. The sweep audits themselves are the best long-run source.
