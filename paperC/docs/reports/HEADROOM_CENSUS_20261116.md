# Headroom census on existing logs (runbook PH; revised 16 Nov 2026 after review rounds 1 and 2)

**AI-assisted (Claude, chat session). ENGINEERING_ONLY. Not evidence, not an author decision.** This is phase PH of `paperC/docs/BUILD_RUNBOOK.md` (BUILD_LIST B16; PLAN §10 R1-PAPERC-CENSUS-FIRST).
- **Data:** `paperC/census/census_v1.json` (schema `paperc_census/v2`), produced by `python -m paperc.census`.
- **Method:** every input is read from a pinned commit; nothing was copied, run or changed.
- **Revision:** round 1 of the independent review (`reviews/BUILD_PH_REVIEW_20261116.md`) found four MAJOR gaps:
  - sources not read;
  - the trial-1 artefact;
  - the noise unit;
  - stakes.

  The conclusions below changed accordingly. §4 replaces the round-1 reading.
- **Revision 3:** round 3 ACCEPTED; its four minor findings (distinct-campaign counts, edit-noise wording, per-edit-class keeps, unit labels) are fixed in place.
- **Revision 2:** round 2 found that the C1 "paired sd" of revision 1 applied the pairing twice (C1's `sd_joint` already is the sd of a paired difference). Every paired-unit number and the E1 and E2 readings for the OpenML nodes were redone (§3.2, §4.3, §4.4, §5).

## 1. Inputs

Every file read, with its git object id, is in §7. In summary:

| Source | Pin | Content | Nodes | Status |
|---|---|---|---|---|
| Track S | `trackS-ops-20261030` @ `fab88fce` | <ul><li>S0.5 roots (A2-U, rep 0)</li><li>S0.5b truncations</li><li>S0.4 rows (campaign Δ̂ and 5-seed fresh audit per executed proposal)</li><li>S0.4 roots</li><li>all S0.4 + S0.5 roots for the trial-1 drop</li><li>S1.1 factorials</li></ul> | digits, tabular (S1.1 also breast_w) | read |
| Paper B sweep 1 | `codex/coordinator-20261031` @ `10742f85` | C3 label sweep ledgers: 7B proposer, 20 runs, 18 instances per node and memory mode | 8 CPU nodes | read, reported per mode |
| C1 noise floor | same | the D28 composite: per edit `sd_joint` (sd over 30 joint seeds of the paired difference candidate − start), `flip_emp`, `campaign_wrong`, `decision_regret`; per node the start configuration's own seed sd | 8 CPU nodes | read |
| C3 audit pilot | same | LLM proposals audited on 6 fresh seeds (random-selection rows) | digits, tabular, breast_w | read; older harness, tiny sample |
| E1b pilots | same | verify vs continue contrasts, naive oracle headroom | digits, ionosphere | read; PILOT, 6 instances |
| B1/B2 exam campaigns | TASL-7 `~/exam-x/work` | — | — | not in the repository, not read |
| sweep 2, T1 (GPU), fresh audits of sweep 1 | — | — | — | do not exist |

**Units:** the sweep's σ_d is itself a paired unit. It equals the median `sd_joint` over the node's *material* C1 edits on all 8 nodes, and a test asserts this. Track S's σ_node is the median over all five edits, so tabular's σ_d is 1.87 σ_node; on digits the two agree.

**Hosts:** the digits S0.4 rows come from TASL-2; every other Track S run is from TASL-7. A host effect is not tested.

**Keep rules differ between the Track S stages:**
- S0.4 kept iff Δ̂ > 0. The census checks that every logged action agrees (0 mismatches on both nodes).
- S0.5 kept iff A2-U's m̂ > 0.
- The keep-quality numbers come from S0.4; the E2 margins come from S0.5.
- The review computed that S0.5's rule applied to the S0.4 rows flips 0 (digits) and 4 (tabular) decisions, which does not change the reading. The census does not recompute this.

**Reproduction:** the census reproduces every E1, E2 and budget number of the Track S S0.5 summary, and `test_census.py` asserts them. The suite has 90 tests, all passing.

## 2. The trial-1 artefact (read first)

Every campaign executes and keeps trial 1 unconditionally, because there is no incumbent metric before it.

| | digits_mlp | tabular_mlp | OpenML nodes |
|---|---|---|---|
| Track S: audited y_after_trial1 − y_start (over 30 distinct trial-1 outcomes) | median −41 σ (−47 … −35) | −63 σ (−84 … −44) | — |
| Track S: audited y_terminal − y_start (over 40 distinct campaigns) | median +1.7 σ | +0.7 σ | — |
| Sweep 1: trial-1 metric − C1 default metric | median −9.9 σ_d | −11.9 σ_d | −1.4 … +2.4 σ_d |
| Sweep 1: the start configuration's own seed sd | 1.5 σ_d | 3.4 σ_d | 0.55 … 7.3 σ_d (climate 7.3) |
| Sweep 1: recorded gain after trial 1 | median 13.5 σ_d | 9.4 σ_d | 0 |

**Caveats on the table:**
- **Independence.** Each node has 60 root rows. The 20 S0.5 static rep-0 roots repeat the a2u roots' actions and terminal values (S0.5 summary §4), so 40 campaigns are distinct. Rep 1 shares trial 1 with rep 0, so there are 30 distinct trial-1 outcomes, one per instance. The medians above are over these distinct sets. Counting all 60 rows gives the same drop medians, but tabular's net gain would read 0.8 σ instead of 0.7 σ.
- **Seeds.** The sweep row compares the trial-1 metric at instance seeds with the C1 default at the C1 seed. Measured against the start configuration's own seed sd, the digits and tabular drops are still clear. The OpenML row is within seed variation and shows no trial-1 effect either way.

**What this means:**
- On digits and tabular, the gains recorded after trial 1 are mostly recovery from a bad first edit. The net gain over the start configuration is 1.7 σ_node on digits and 0.7 σ_node on tabular.
- **The keep-quality numbers below (§3) are conditional on this artefact.** The large, easy recovery increments make keep decisions look reliable.
- Paper B lists the trial-1 unconditional keep as an open item.
- A guarded first acceptance (compare trial 1 with the start configuration) is a channel candidate in its own right, and a confound for any digits/tabular comparison.

## 3. Results per source

### 3.1 Track S (digits_mlp, tabular_mlp; σ = σ_node)

| | digits_mlp | tabular_mlp |
|---|---|---|
| **E1:** eligible decisions; V\* median; V\* range across proposals | 298; 2.70 σ; 0.036 σ | 330; 4.15 σ; 0.018 σ |
| price / V\*; E1 decisions near the price | 0.037; 0 % | 0.024; 0 % |
| E1 skips (all rule duplicates) | 57 % of E1 rows | 53 % |
| **Comparison noise** sd(Δ̂ − Δ_audit): plain (robust) | 3.0 σ (1.5 σ) | 9.8 σ (2.6 σ) |
| **E2:** margins within ±0.5 σ / within ±0.5 × robust comparison noise | 15.4 % / 20.1 % | 11.5 % / 25.2 % |
| E2 keep / discard / failed_invalid | 148 / 170 / 53 | 158 / 192 / 51 |
| **Keep quality** (S0.4; keep iff Δ̂ > 0) | | |
| false keeps (audit ≤ 0 among keeps) | 0 / 75 | 1 / 68 (1.5 %) |
| missed keeps (audit > 0 among discards) | 15 / 90 (16.7 %): 11 of them are exact ties (Δ̂ = 0); median audited value 0.42 σ, maximum 2.1 σ | 7 / 86 (8.1 %): no ties; median 0.83 σ, one of 41.7 σ |
| corr(Δ̂, audit) | 0.94 | 0.90 |
| **Selection bias of keeps** (Δ̂ − Δ_audit) | | |
| per keep, mean ± se | −0.16 ± 0.43 σ | −0.12 ± 1.34 σ |
| per campaign, mean ± se (10 campaigns) | −1.2 ± 2.0 σ | −0.8 ± 6.6 σ |
| correlation with the number of keeps | 0.19 | 0.69 |
| reading | no winner's curse detected; underpowered | same |
| **Audited increments:** positive share; beyond +4 σ / below −4 σ | 55 %; 14.5 % / 21.8 % | 48 %; 22.1 % / 42.9 % |
| **Budget:** binding share at W = 8 / 10 / 12 / 20 | 1.00 / 1.00 / 0.94 / 0.04 | 1.00 / 1.00 / 1.00 / 0.16 |
| **S1.1 pairwise interactions** (3 pairs each; every CI excludes 0) | 0.86, −0.54, 1.24 σ | 1.39, −1.40, 2.57 σ |

**Notes on the table:**
- **Selection-bias measure.** It is Σ over keeps of (Δ̂ − Δ_audit) on the S0.4 audit seeds. It cancels any shared offset of the recorded trial-1 value, so it is not the incumbent-value curse itself.
- **Shadow price.** It is undefined, because V\* is constant across proposals. A binding W changes where a campaign stops, not any decision (S0.5 summary §4). W matters here only as the price of verify runs.

### 3.2 Sweep 1 with C1 (σ = σ_d, the material-edit median of C1's paired sd; "all-edit" = the median over all five C1 edits)

| Node | σ_d | all-edit paired sd in σ_d (range over edits) | C1 sign-flip rate (single seed) | C1 decision regret (median, σ_d) | near 0: σ_d / all-edit | exact 0 | kept increment, median: σ_d / all-edit | price / V\*: noise σ_d / all-edit | failed_invalid |
|---|---|---|---|---|---|---|---|---|---|
| digits_mlp | 0.0066 | 1.00 (0.80–1.67) | 0.14 | 0.14 | 18 % / 18 % | 7 % | 2.1 / 2.1 | 0.02 / 0.02 | 5 % |
| tabular_mlp | 0.0036 | 0.54 (0.01–1.75) | 0.11 | 0.02 | 12 % / 7 % | 0 % | 1.9 / 3.4 | 0.03 / 0.03 | 2 % |
| openml_climate | 0.0055 | 3.72 (0.97–14.5) | 0.38 | 0.16 | 51 % / 83 % | 33 % | 0.88 / 0.24 | 0.59 / misspecified | 21 % |
| openml_ionosphere | 0.0424 | 0.38 (0.13–1.06) | 0.20 | 0.04 | 87 % / 61 % | 38 % | 0.11 / 0.29 | misspecified / misspecified | 24 % |
| openml_sonar | 0.0464 | 0.29 (0.07–2.16) | 0.24 | 0.05 | 80 % / 65 % | 53 % | 0.18 / 0.62 | misspecified / 0.75 | 5 % |
| openml_wdbc | 0.0167 | 0.09 (0.04–1.45) | 0.25 | 0.01 | 95 % / 80 % | 71 % | 0.11 / 1.2 | misspecified / 0.97 | 5 % |
| openml_credit_approval | 0.0146 | 0.20 (0.06–1.11) | 0.27 | 0.03 | 98 % / 58 % | 35 % | 0.08 / 0.38 | misspecified / misspecified | 7 % |
| openml_breast_w | 0.0062 | 0.037 (0.02–1.16) | 0.60 | 0.006 | 99 % / 74 % | 74 % | 0.13 / 3.5 | misspecified / 1.06 | 6 % |

**Notes on the table:**
- **Misspecified** means the assumed noise sd is at least the observed increment sd, so a node-level forecaster has no prior variance to work with. No value is reported in that case.
- **Edit-dependent noise.** The noise of one paired comparison varies widely across a node's five standard edits (range column). The low end comes from edits that barely change the model, so their paired noise is near zero (tabular `ALPHA`; `class_weight` on wdbc, sonar and breast_w). On the OpenML nodes other than climate, the review places the high end at `model_type` edits. One node-level unit therefore brackets the noise rather than measuring it, and the increments are a zero-inflated mixture.
- **Robust sd.** It is degenerate (MAD = 0) on the nodes with more than 50 % exact zeros.
- **Failure categories.** `invalid_config` on the OpenML nodes; `proposal_precondition_failed` on digits, tabular and wdbc (4).

**Per memory mode.** Duplicates are by patch hash; Track S counts configuration-level duplicates.

| Node | duplicates: none / summary | comparisons per campaign: none / summary | keeps after trial 1 per campaign: none / summary | campaigns with no keep after trial 1: none / summary |
|---|---|---|---|---|
| digits_mlp | 80 % / 39 % | 2.9 / 12.0 | 1.5 / 6.0 | 33 % / 0 % |
| tabular_mlp | 85 % / 33 % | 1.9 / 12.4 | 0.7 / 5.8 | 44 % / 0 % |
| openml_climate | 81 % / 44 % | 1.4 / 7.5 | 0.06 / 1.2 | 94 % / 39 % |
| openml_ionosphere | 80 % / 43 % | 1.5 / 7.4 | 0.11 / 1.2 | 89 % / 39 % |
| openml_sonar | 82 % / 45 % | 2.6 / 9.3 | 0.06 / 1.8 | 94 % / 17 % |
| openml_wdbc | 81 % / 37 % | 2.8 / 10.4 | 0.00 / 1.0 | 100 % / 28 % |
| openml_credit_approval | 83 % / 55 % | 1.4 / 7.3 | 0.06 / 1.7 | 94 % / 33 % |
| openml_breast_w | 83 % / 42 % | 2.5 / 9.8 | 0.06 / 1.4 | 94 % / 11 % |

### 3.3 C3 audit pilot and E1b pilots (older harness or PILOT; small samples)

| | digits_mlp | tabular_mlp | openml_breast_w | openml_ionosphere |
|---|---|---|---|---|
| C3 pilot: false keeps (Δ̂ > 0, audit ≤ 0) | 2 / 11 | 7 / 21 | 0 / 7 | — |
| C3 pilot: missed keeps (Δ̂ ≤ 0, audit > 0) | 4 / 13 | 20 / 48 | 29 / 47 | — |
| E1b: always-verify minus continue (three pilots) | −0.09, +0.14 σ_d | — | — | −0.03, 0.00, −0.02 σ_d |
| E1b: naive oracle minus continue | +0.03, +0.16 σ_d | — | — | +0.01, 0.00, +0.02 σ_d |

**Reading.** The C3 pilot's false-keep rates (18 %, 33 %) contrast sharply with Track S's 0–1.5 %.
- The pilot is an older harness on other node versions with a tiny sample.
- Track S's numbers carry the trial-1 artefact.
- So keep quality on digits/tabular is uncertain, not established.

## 4. What the census shows (revised)

1. **Stakes.**
   - **OpenML nodes other than climate:** small. Kept increments are a median 0.08–0.18 σ_d; C1's decision regret is 0.006–0.05 σ_d; E1b's naive oracle headroom on ionosphere is at most 0.02 σ_d (on digits 0.16 σ_d). Under memory `none`, 89–100 % of OpenML campaigns keep nothing after trial 1.
   - **openml_climate:** kept increments 0.88 σ_d, but 21 % failed_invalid and the noisiest edits (up to 14.5 σ_d).
   - **digits/tabular:** confounded. The net audited gain over the start (1.7 and 0.7 σ_node) comes from campaigns that spent their budget recovering from trial 1. It is a lower bound for a guarded loop, not a stakes measurement.
2. **The largest observable effects are loop-design artefacts, not sequential control:**
   - the unconditional trial-1 keep: a drop of 35–84 σ_node, then recovery;
   - duplicate proposals: 80–85 % under `none`, 33–55 % under `append_only_summary`.

   Both are first-order. Paper B's rule layer already skips duplicates at no run cost; the cost is in LLM calls and proposal slots.
3. **E1 (screening).**
   - **digits/tabular:** inert. Price / V\* is 0.02–0.04 under every noise assumption, including A2-U's (0.037 / 0.024).
   - **OpenML nodes: not determinable from node-level fits.**
     - With the material-edit unit (σ_d), five of the six nodes are misspecified. With the all-edit unit, three are (credit_approval, ionosphere, climate) and the other three give 0.75–1.06.
     - The answer depends on the unit. The noise depends on the edit, and the increments are zero-inflated, so a normal node-level forecaster does not describe them.
     - Settling E1 there needs a per-proposal forecaster (Paper B's C3 belief) and a declared real run price. Track S's 0.1 σ is arbitrary.
     - Revision 1's "inside the band on five nodes" is withdrawn.
4. **E2 (acceptance).**
   - **digits/tabular:**
     - With Track S audits, false keeps are 0–1.5 % and missed keeps 8–17 %. Most digits misses are ties worth about 0.4 σ.
     - The C3 pilot disagrees (18–33 % false keeps), and both carry caveats.
     - In comparison-noise units, 20–25 % of keep decisions are near the margin.
   - **OpenML:**
     - 58–83 % of comparisons lie within ±0.5 of the all-edit paired noise, and single-seed sign flips are 20–60 % on C1's standard edits.
     - On climate, ionosphere, credit_approval and sonar, the median kept increment is 0.24–0.62 of the all-edit paired noise, i.e. **inside the noise**.
     - The review checked this per edit class. On those four nodes, almost all kept edits change `C` (20/22, 29/32, 24/25, 33/33), and the median kept increment is about 0.3–0.9 of C1's noise for `C` edits. The census does not recompute this split.
     - On wdbc (1.2) and breast_w (3.5), the median kept increment is above the all-edit noise, but those nodes have 71–74 % exact zeros and edit-dependent noise.
     - Revision 1's withdrawal of "keeps inside the noise" is reversed for those four nodes.
     - The stakes reading stands: each keep is worth about 0.1 σ_d, and campaigns rarely keep anything. Acceptance there is often wrong, but cheap to get wrong. "Often wrong" is inferred from C1's standard edits; sweep-1 keeps were never audited (§6.2a).
5. **Incumbent interaction.**
   - On digits and tabular, the S1.1 factorials find 2×2 interactions among standard edits of 0.5–1.4 σ_d (digits 0.86, −0.54, 1.24 σ_d; tabular 0.74, −0.75, 1.37 σ_d). All CIs exclude 0, and the sizes are comparable to main effects.
   - This shows that the mechanism exists at main-effect scale. Its value to a controller over a campaign is unmeasured.
   - On breast_w, `max_iter` has no effect at all, which explains its exact zeros.
6. **Budget.** It binds at W ≤ 12 on the Track S nodes. Its shadow price is undefined while proposals are indistinguishable. Budget is a price for verify, not a channel by itself.
7. **Selection caveat.** The OpenML nodes entered Paper B's pool through D21's "P(wrong) ≥ 0.10" rule, so the noisy-regime finding is partly true by construction.

## 5. Placement on the headroom map (stakes and interactions in σ_d; E2 shares in Track S comparison noise for digits/tabular, in all-edit paired noise for OpenML)

| Node | E1: price / V\* | E2: near-margin share | Stakes: kept increment, median | Interaction (S1.1) | Main caveat |
|---|---|---|---|---|---|
| digits_mlp | 0.02–0.04 (inert) | 20 % (Track S comparison noise) | 2.1 σ_d; net campaign gain 1.7 σ_d | exists, 0.5–1.2 σ_d | trial-1 artefact; keep quality disputed (Track S vs C3 pilot) |
| tabular_mlp | 0.02–0.04 (inert) | 25 % (Track S comparison noise) | 1.9 σ_d; net 0.36 σ_d | exists, 0.7–1.4 σ_d | same |
| openml_ionosphere | not determinable (misspecified in both units) | 61 % | 0.11 σ_d (0.29 of all-edit noise) | not measured | low stakes; 24 % invalid |
| openml_credit_approval | not determinable (misspecified in both units) | 58 % | 0.08 σ_d (0.38) | not measured | low stakes |
| openml_sonar | not determinable (σ_d misspecified; all-edit 0.75) | 65 % | 0.18 σ_d (0.62) | not measured | low stakes; 53 % exact zeros |
| openml_wdbc | not determinable (σ_d misspecified; all-edit 0.97) | 80 % | 0.11 σ_d (1.2) | not measured | 71 % exact zeros |
| openml_breast_w | not determinable (σ_d misspecified; all-edit 1.06) | 74 % | 0.13 σ_d (3.5) | none (`max_iter` inert) | 74 % exact zeros |
| openml_climate | not determinable (σ_d 0.59; all-edit misspecified) | 83 % | 0.88 σ_d (0.24) | not measured | 21 % invalid; edit noise up to 14.5 σ_d |

## 6. Proposal for the author (revised; the choice is the author's)

1. **No confirmatory node choice yet.** The census cannot rank the nodes for sequential headroom. The two regimes fail in opposite ways:
   - digits/tabular may have stakes, but they are confounded by the trial-1 artefact and keep quality is disputed;
   - the OpenML nodes have hard decisions, with kept increments inside the noise and almost no stakes.
2. **Measure before collecting**, on CPU, cheaply, on a Paper C seed block. Both steps can share the audit runs; part (a) overlaps with Paper B's B.2.
   - **(a)** Fresh-seed audits of sweep-1 keeps and final incumbents on digits, tabular, credit_approval and ionosphere. This turns the inferred keep quality into measured false-keep and missed-keep rates and a measured winner's curse.
   - **(b)** A small run with a **guarded first acceptance**, comparing trial 1 with the start configuration, on digits and tabular, to remove the trial-1 artefact before judging E2 there.
3. **Channel candidates for the core (A); the order is a proposal:**
   - **incumbent interaction:** the mechanism exists on digits/tabular, but its control value is unmeasured. E-SYN gets the interaction world first, so the control value can be bounded in simulation before any collection;
   - **acceptance under noise** with verify / re-audit, judged with stakes, not only near-margin mass;
   - **E1 on OpenML** only with a per-proposal forecaster and a declared real run price.
4. **Raise the priority of the GPU tier (B).** On the OpenML nodes the stakes are small, and on digits/tabular they are confounded. A T1 census (HoreKa / HTCondor) is the next source that can show headroom.
5. **Thresholds, proposed:**
   - E1 relevance is a two-sided band, 0.3 ≤ price / V\* ≤ 3, under the deployed per-proposal forecaster and a declared real price; node-level fits do not qualify;
   - E2 relevance needs both near-margin share ≥ 0.10 in the node's own paired-noise unit, stated per edit class where the noise is edit-dependent, **and** a stakes floor, for example a median kept increment ≥ 0.5 σ_d or decision regret ≥ 0.1 σ_d.
6. **Steering (C) and loop design:**
   - duplicate load is 80 % without memory and about 40 % with summary memory;
   - the trial-1 keep is first-order;
   - both are cheap, descriptive checks and possible extensions.

After the measurements in point 2, R1-PAPERC-CORE is written with the chosen nodes and channels (R-C3).

## 7. Files read (git object ids)

| Ref | Path | Git object |
|---|---|---|
| `10742f85` | `results/r1/engineering/c3_audit_pilot_20261019T001338Z/audits.jsonl` | `7a198626a996` |
| `10742f85` | `results/r1/engineering/c3_audit_pilot_20261019T001338Z/proposals.jsonl` | `3f67ba5bd3cc` |
| `10742f85` | `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z/manifest.json` | `92329c9a5229` |
| `10742f85` | `results/r1/evidence/C3_sweep_none_20261027T224356Z/manifest.json` | `90f003ee3b7b` |
| `10742f85` | `results/r1/evidence/C3_sweep_none_20261027T224356Z/provenance/ledgers` (tree) | `ea87ff6debdd` |
| `10742f85` | `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z/provenance/ledgers` (tree) | `0edf6c59251f` |
| `10742f85` | `results/r1/noise/D28_REPAIR_20261027/summary.json` | `bd7fcef67891` |
| `10742f85` | `results/r1/pilot/E1b_20261012T161034Z/analysis.json` | `7652bac8dc60` |
| `10742f85` | `results/r1/pilot/E1b_20261013T151857Z/analysis.json` | `07cb52db437a` |
| `10742f85` | `results/r1/pilot/E1b_vary_ionosphere_20261012/analysis.json` | `087c8a58caaf` |
| `fab88fce` | `results/r1/tracks/digits_mlp/s04_rerun20261111/{manifest.json, roots.jsonl, s04_rows.jsonl}` | `90c7762de4f5`, `0f59d8777562`, `94848dd5f1f2` |
| `fab88fce` | `results/r1/tracks/digits_mlp/s05_t7_20261113/{manifest.json, roots.jsonl, s05b_truncated.jsonl}` | `1fc1a3fe6461`, `82af73503b2f`, `a72b779b98e0` |
| `fab88fce` | `results/r1/tracks/tabular_mlp/s04_t7_20261114/{manifest.json, roots.jsonl, s04_rows.jsonl}` | `e1cb428f0e0e`, `35d429a006c3`, `103a11c23006` |
| `fab88fce` | `results/r1/tracks/tabular_mlp/s05_t7_20261114/{manifest.json, roots.jsonl, s05b_truncated.jsonl}` | `ab5514187641`, `294571a70f13`, `53f7ed37922a` |
| `fab88fce` | `results/r1/tracks/{digits_mlp/s11/digits.json, tabular_mlp/s11/tabular.json, openml_breast_w/s11/breast_w.json}` | `1dc0a000aa44`, `2879794a2860`, `195ff10552c2` |
