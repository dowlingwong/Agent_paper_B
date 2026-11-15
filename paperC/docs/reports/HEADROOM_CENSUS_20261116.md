# Headroom census on existing logs (runbook PH; revised 16 Nov 2026 after review round 1)

**AI-assisted (Claude, chat session). ENGINEERING_ONLY. Not evidence, not an author decision.** This is phase PH of `paperC/docs/BUILD_RUNBOOK.md` (BUILD_LIST B16; PLAN §10 R1-PAPERC-CENSUS-FIRST).
- **Data:** `paperC/census/census_v1.json` (schema `paperc_census/v2`), produced by `python -m paperc.census`.
- **Method:** every input is read from a pinned commit; nothing was copied, run or changed.
- **Revision:** round 1 of the independent review (`reviews/BUILD_PH_REVIEW_20261116.md`) found four MAJOR gaps:
  - sources not read;
  - the trial-1 artefact;
  - the noise unit;
  - stakes.

  The conclusions below changed accordingly. §4 replaces the round-1 reading.

## 1. Inputs

Every file read, with its git object id, is in §7. In summary:

| Source | Pin | Content | Nodes | Status |
|---|---|---|---|---|
| Track S | `trackS-ops-20261030` @ `fab88fce` | <ul><li>S0.5 roots (A2-U, rep 0)</li><li>S0.5b truncations</li><li>S0.4 rows (campaign Δ̂ and 5-seed fresh audit per executed proposal)</li><li>S0.4 roots</li><li>all S0.4 + S0.5 roots for the trial-1 drop</li><li>S1.1 factorials</li></ul> | digits, tabular (S1.1 also breast_w) | read |
| Paper B sweep 1 | `codex/coordinator-20261031` @ `10742f85` | C3 label sweep ledgers: 7B proposer, 20 runs, 18 instances per node and memory mode | 8 CPU nodes | read, reported per mode |
| C1 noise floor | same | the D28 composite: per-edit `sd_joint`, `rho_joint`, `flip_emp`, `campaign_wrong`, `decision_regret` | 8 CPU nodes | read |
| C3 audit pilot | same | LLM proposals audited on 6 fresh seeds (random-selection rows) | digits, tabular, breast_w | read; older harness, tiny sample |
| E1b pilots | same | verify vs continue contrasts, naive oracle headroom | digits, ionosphere | read; PILOT, 6 instances |
| B1/B2 exam campaigns | TASL-7 `~/exam-x/work` | — | — | not in the repository, not read |
| sweep 2, T1 (GPU), fresh audits of sweep 1 | — | — | — | do not exist |

**Hosts:** the digits S0.4 rows come from TASL-2; every other Track S run is from TASL-7. A host effect is not tested.

**Keep rules differ between the Track S stages:**
- S0.4 kept iff Δ̂ > 0. The census checks that every logged action agrees (0 mismatches on both nodes).
- S0.5 kept iff A2-U's m̂ > 0.
- The keep-quality numbers come from S0.4; the E2 margins come from S0.5.
- The review computed that S0.5's rule applied to the S0.4 rows flips 0 (digits) and 4 (tabular) decisions, which does not change the reading. The census does not recompute this.

**Reproduction:** the census reproduces every E1, E2 and budget number of the Track S S0.5 summary, and `test_census.py` asserts them. The suite has 89 tests, all passing.

## 2. The trial-1 artefact (read first)

Every campaign executes and keeps trial 1 unconditionally, because there is no incumbent metric before it.

| | digits_mlp | tabular_mlp | OpenML nodes |
|---|---|---|---|
| Track S: audited y_after_trial1 − y_start | median −41 σ (−47 … −35), 60 campaigns | −63 σ (−84 … −44), 60 campaigns | — |
| Track S: audited y_terminal − y_start | median +1.7 σ | +0.8 σ | — |
| Sweep 1: trial-1 metric − C1 default metric | median −9.9 σ_d | −11.9 σ_d | −1.4 … +2.4 σ_d |
| Sweep 1: recorded gain after trial 1 | median 13.5 σ_d | 9.4 σ_d | 0 |

**What this means:**
- On digits and tabular, the gains recorded after trial 1 are mostly recovery from a bad first edit. The net gain over the start configuration is about 1–2 σ_node.
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

### 3.2 Sweep 1 with C1 (σ = σ_d; "paired" = C1's median paired sd of a fixed-seed difference)

| Node | σ_d | paired sd (σ_d) | C1 sign-flip rate (single seed) | C1 decision regret (median, σ_d) | near 0: in σ_d / in paired units | exact 0 | kept increment, median: σ_d / paired | price / V\*: noise 1 σ_d / paired noise | failed_invalid |
|---|---|---|---|---|---|---|---|---|---|
| digits_mlp | 0.0066 | 0.68 | 0.14 | 0.14 | 18 % / 7 % | 7 % | 2.1 / 3.1 | 0.02 / 0.02 | 5 % |
| tabular_mlp | 0.0036 | 0.087 | 0.11 | 0.02 | 12 % / 1 % | 0 % | 1.9 / 21 | 0.03 / 0.03 | 2 % |
| openml_climate | 0.0055 | 1.94 | 0.38 | 0.16 | 51 % / 64 % | 33 % | 0.88 / 0.45 | 0.59 / misspecified | 21 % |
| openml_ionosphere | 0.0424 | 0.15 | 0.20 | 0.04 | 87 % / 48 % | 38 % | 0.11 / 0.75 | misspecified / 2.2 | 24 % |
| openml_sonar | 0.0464 | 0.059 | 0.24 | 0.05 | 80 % / 53 % | 53 % | 0.18 / 3.1 | misspecified / 0.55 | 5 % |
| openml_wdbc | 0.0167 | 0.012 | 0.25 | 0.01 | 95 % / 71 % | 71 % | 0.11 / 8.9 | misspecified / 0.90 | 5 % |
| openml_credit_approval | 0.0146 | 0.021 | 0.27 | 0.03 | 98 % / 35 % | 35 % | 0.08 / 3.7 | misspecified / 2.4 | 7 % |
| openml_breast_w | 0.0062 | 0.002 | 0.60 | 0.006 | 99 % / 74 % | 74 % | 0.13 / 65 | misspecified / 1.0 | 6 % |

**Notes on the table:**
- **Misspecified** means the assumed noise sd is at least the observed increment sd, so a node-level forecaster has no prior variance to work with. No value is reported in that case.
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

1. **Stakes on the CPU nodes are small once the trial-1 artefact is set aside.**
   - The OpenML nodes keep increments of a median 0.08–0.18 σ_d. C1's decision regret is 0.006–0.16 σ_d, and E1b's naive oracle headroom is at most 0.16 σ_d.
   - Under memory `none`, 89–100 % of OpenML campaigns keep nothing after trial 1.
   - On digits/tabular, the campaigns' net audited gain over the start is about 1–2 σ_node; the rest is recovery.
2. **The largest observable effects are loop-design artefacts, not sequential control:**
   - the unconditional trial-1 keep: a drop of 35–84 σ_node, then recovery;
   - duplicate proposals: 80–85 % under `none`, 33–55 % under `append_only_summary`.

   Both are first-order. Paper B's rule layer already skips duplicates at no run cost; the cost is in LLM calls and proposal slots.
3. **E1 (screening).**
   - **digits/tabular:** inert. Price / V\* is 0.02–0.03 under every noise assumption.
   - **OpenML nodes:** the round-1 "∞" was an artefact of assuming 1 σ_d of noise.
     - With C1's paired noise, price / V\* is 0.55–2.4 on five nodes, inside a two-sided band (0.3–3) where screening can matter. Climate is misspecified under paired noise.
     - So E1 is formally decision-relevant there, but at Track S's arbitrary price of 0.1 σ_d and with tiny stakes.
     - Per-proposal discrimination is still not measurable without Paper B's C3 belief.
4. **E2 (acceptance).**
   - **digits/tabular:** with Track S audits, false keeps are 0–1.5 % and missed keeps 8–17 %. Most digits misses are ties worth about 0.4 σ. The C3 pilot disagrees (18–33 % false keeps), and both carry caveats. In comparison-noise units, 20–25 % of keep decisions are near the margin.
   - **OpenML:** in paired units, 35–74 % of comparisons are within ±0.5 of the noise; single-seed sign flips are 20–60 % on C1's standard edits. But the stakes are 0.1 σ_d per keep, and campaigns rarely keep anything.
   - The round-1 claim that "acceptance is largely a draw on noise" is withdrawn as stated. Decisions there are often wrong, but cheap to get wrong.
5. **Incumbent interaction.**
   - On digits and tabular, the S1.1 factorials find pairwise interactions of 0.5–2.6 σ_node, all with CIs excluding 0. This is the one non-myopic channel the census measures directly.
   - On breast_w, `max_iter` has no effect at all, which explains its exact zeros.
6. **Budget.** It binds at W ≤ 12 on the Track S nodes. Its shadow price is undefined while proposals are indistinguishable. Budget is a price for verify, not a channel by itself.
7. **Selection caveat.** The OpenML nodes entered Paper B's pool through D21's "P(wrong) ≥ 0.10" rule, so the noisy-regime finding is partly true by construction.

## 5. Placement on the headroom map

| Node | E1: price / V\* (paired noise) | E2: near-margin share (noise unit) | Stakes: kept increment, median | Measured interaction | Main caveat |
|---|---|---|---|---|---|
| digits_mlp | 0.02 (inert) | 20 % (comparison noise) | 2.1 σ_d; net campaign gain ≈ 1.7 σ_node | yes, 0.5–1.2 σ | trial-1 artefact; keep quality disputed (Track S vs C3 pilot) |
| tabular_mlp | 0.03 (inert) | 25 % (comparison noise) | 1.9 σ_d; net ≈ 0.8 σ_node | yes, 1.4–2.6 σ | same |
| openml_ionosphere | 2.2 (in band) | 48 % (paired) | 0.11 σ_d | not measured | low stakes; 24 % invalid |
| openml_credit_approval | 2.4 (in band) | 35 % (paired) | 0.08 σ_d | not measured | low stakes |
| openml_sonar | 0.55 (in band) | 53 % | 0.18 σ_d | not measured | low stakes; 53 % exact zeros |
| openml_wdbc | 0.90 (in band) | 71 % | 0.11 σ_d | not measured | 71 % exact zeros |
| openml_breast_w | 1.0 (in band) | 74 % | 0.13 σ_d | none (max_iter inert) | 74 % exact zeros |
| openml_climate | misspecified | 64 % | 0.88 σ_d | not measured | 21 % invalid; paired noise above observed spread |

## 6. Proposal for the author (revised; the choice is the author's)

1. **No confirmatory node choice yet.** The census cannot rank the nodes for sequential headroom. The two regimes fail in opposite ways:
   - digits/tabular have stakes, but those are confounded by the trial-1 artefact and keep quality is disputed;
   - the OpenML nodes have hard decisions with almost no stakes.
2. **Measure before collecting**, on CPU, cheaply, on a Paper C seed block. Both steps can share the audit runs; part 1 overlaps with Paper B's B.2.
   - **(a)** Fresh-seed audits of sweep-1 keeps and final incumbents on digits, tabular, credit_approval and ionosphere. This turns the inferred keep quality into measured false-keep and missed-keep rates and a measured winner's curse.
   - **(b)** A small run with a **guarded first acceptance**, comparing trial 1 with the start configuration, on digits and tabular, to remove the trial-1 artefact before judging E2 there.
3. **Channel priority for the core (A):**
   - **incumbent interaction:** measured on digits/tabular; E-SYN gets the interaction world first;
   - **acceptance under noise** with verify / re-audit, judged with stakes, not only near-margin mass;
   - **E1 on OpenML** only with a per-proposal forecaster and a declared real run price.
4. **Raise the priority of the GPU tier (B).** The CPU stakes are small. A T1 census (HoreKa / HTCondor) is the next source that can show headroom.
5. **Thresholds, proposed:**
   - E1 relevance is a two-sided band, 0.3 ≤ price / V\* ≤ 3, under the deployed forecaster and a declared real price;
   - E2 relevance needs both near-margin share ≥ 0.10 in the node's own noise unit **and** a stakes floor, for example a median kept increment ≥ 0.5 σ_d or decision regret ≥ 0.1 σ_d.
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
