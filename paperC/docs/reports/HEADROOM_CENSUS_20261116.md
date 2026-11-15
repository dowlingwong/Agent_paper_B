# Headroom census on existing logs (runbook PH, 16 Nov 2026)

**AI-assisted (Claude, chat session). ENGINEERING_ONLY. Not evidence, not an author decision.** This is phase PH of `paperC/docs/BUILD_RUNBOOK.md` (BUILD_LIST B16; PLAN §10 R1-PAPERC-CENSUS-FIRST). The data are `paperC/census/census_v1.json`, produced by `python -m paperc.census`. All inputs are read from pinned commits; nothing was copied, run or changed.

## 1. Inputs

| Source | Pin | What is read | Nodes |
|---|---|---|---|
| Track S | `trackS-ops-20261030` @ `fab88fce` | <ul><li>S0.5 roots (A2-U, rep 0, W = 40)</li><li>S0.5b truncations (all 50 roots)</li><li>S0.4 rows: each executed proposal's campaign increment and its 5-seed fresh audit</li><li>S0.4 roots (audited start, after-trial-1 and terminal values)</li><li>σ_node from the manifests</li></ul> | `digits_mlp`, `tabular_mlp` |
| Paper B sweep 1 | `codex/coordinator-20261031` @ `10742f85` | <ul><li>Ledgers of the C3 label sweep: 7B proposer, 20 runs, memory `none` and `append_only_summary`, 18 instances per node and mode</li><li>σ_d from the sweep manifest (the D28 table, median sd_joint)</li></ul> | 8 CPU nodes |

**Not read:**
- **B1/B2 exam campaigns:** they live on TASL-7 (`~/exam-x/work`) and are not in the repository.
- **Sweep 2 and T1 (GPU) data:** they do not exist yet.
- **Fresh audits of sweep 1:** there are none, because Paper B's B.2 has not run.

**Checks:** the census reproduces every E1/E2 and budget number of the Track S two-node S0.5 summary (`TRACKS_S05_SUMMARY_20261115.md` §2, §4), and `test_census.py` asserts them. The suite has 78 tests, all passing.

Units are σ of the node: σ_node for Track S, σ_d for sweep 1. The price is Track S's g = 0.1 σ. "Near" means within ±0.5 σ.

## 2. Track S nodes (A2-U, with fresh audits)

| | `digits_mlp` | `tabular_mlp` |
|---|---|---|
| **E1** eligible decisions | 298 | 330 |
| V\* median; range across proposals | 2.70 σ; 0.036 σ | 4.15 σ; 0.018 σ |
| price / V\* | 0.037 | 0.024 |
| E1 decisions near the price | 0 % | 0 % |
| E1 skips | 57 % of E1 rows, all rule duplicates | 53 %, all rule duplicates |
| **E2** keep margins near 0 | 15.4 % (46 / 298) | 11.5 % (38 / 330) |
| E2 keep / discard / failed_invalid | 148 / 170 / 53 | 158 / 192 / 51 |
| **Keep quality** (S0.4; keep iff Δ̂ > 0) | n = 165 | n = 154 |
| false-keep rate (audit ≤ 0 among keeps) | 0.0 % | 1.5 % |
| missed-keep rate (audit > 0 among discards) | 16.7 % (clear-sign audits: 8.3 %) | 8.1 % (clear: 5.2 %) |
| corr(Δ̂, audit) | 0.94 | 0.90 |
| audited increments near 0 | 20 % | 7.8 % |
| **Winner's curse** (recorded − audited gain, per campaign, 10 campaigns) | −1.2 σ mean (sd 6.2 σ); recorded > audited in 20 % | −0.85 σ (sd 20.9 σ); 30 % |
| **Budget**: binding share at W = 8 / 10 / 12 / 20 | 1.00 / 1.00 / 0.94 / 0.04 | 1.00 / 1.00 / 1.00 / 0.16 |
| at W = 40: LLM cap reached; runs used | 100 %; 11–27 | 100 %; 14–22 |
| **Tails**: audited increment sd (robust) | 9.0 σ (3.8 σ) | 22.1 σ (13.4 σ) |
| audited increments beyond ±4 σ | 36 % | 65 % |

## 3. Sweep 1 (all 8 CPU nodes, observed increments at the default seed, no audits)

| Node | σ_d | comparisons | near 0 | exact 0 | near 0, excl. exact 0 | keep share | keeps within (0, 1 σ] | sd (robust) | price / V\* (robust) | failed_invalid | duplicates | beyond ±4 σ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 0.0066 | 269 | 18 % | 7 % | 12 % | 50 % | 24 % | 11.2 (3.7) | 0.02 (0.06) | 5 % | 59 % | 39 % |
| `tabular_mlp` | 0.0036 | 258 | 12 % | 0 % | 12 % | 45 % | 35 % | 10.7 (4.8) | 0.03 (0.06) | 2 % | 59 % | 45 % |
| `openml_climate` | 0.0055 | 160 | 51 % | 33 % | 27 % | 14 % | 50 % | 1.55 (0.52) | 0.59 (∞) | 21 % | 63 % | 3 % |
| `openml_sonar` | 0.0464 | 215 | 80 % | 53 % | 57 % | 15 % | 88 % | 0.66 (0.0) | ∞ | 5 % | 64 % | 0 % |
| `openml_ionosphere` | 0.0424 | 161 | 87 % | 38 % | 79 % | 15 % | 100 % | 0.34 (0.16) | ∞ | 24 % | 61 % | 0 % |
| `openml_wdbc` | 0.0167 | 239 | 95 % | 71 % | 81 % | 8 % | 100 % | 0.38 (0.0) | ∞ | 5 % | 59 % | 0 % |
| `openml_credit_approval` | 0.0146 | 157 | 98 % | 35 % | 96 % | 20 % | 100 % | 0.17 (0.08) | ∞ | 7 % | 69 % | 0 % |
| `openml_breast_w` | 0.0062 | 222 | 99 % | 74 % | 95 % | 12 % | 92 % | 0.25 (0.0) | ∞ | 6 % | 62 % | 0 % |

**Notes on these columns:**
- "Comparisons" counts valid, non-duplicate trials after the first.
- **"price / V\*"** comes from a node-level forecaster: one normal law fitted to the node's observed increments, measurement sd 1 σ.
  - ∞ means V\* ≈ 0. Under that forecaster the expected improvement of an average proposal is below the price, so the myopic rule would skip everything.
  - Per-proposal discrimination cannot be measured without a per-proposal forecaster (Paper B C3).
- **Failure categories:** `invalid_config` on the OpenML nodes, `proposal_precondition_failed` on digits/tabular. Both are now in the schema's `failure_category`.
- **Caveat on σ:** σ_d is the seed sd of a configuration's metric (median sd_joint), not the sd of a paired fixed-seed difference. If seed effects are shared between candidate and incumbent, the true comparison noise is smaller. So "within 1 σ" is an approximate scale, not a measured error rate.

## 4. What the census shows

**Two regimes, and they want different controllers.**

1. **Heavy-tail regime: `digits_mlp`, `tabular_mlp`.**
   - **Increments are broad and mostly bad.** sd 9–22 σ; 36–65 % beyond ±4 σ, chiefly broken or degraded edits.
   - **Screening is inert.** Under A2-U or any node-level forecaster, price / V\* ≈ 0.02–0.06: trying is almost free relative to its option value, so screening (E1) has nothing to decide.
   - **Acceptance is mostly right.**
     - Measured against fresh audits, false keeps are 0–1.5 %. There is no positive winner's curse: recorded gains sit about 1 σ *below* audited ones on average.
     - Missed keeps are 8–17 % (5–8 % with a clear audit sign).
   - **Remaining headroom is modest and specific:** the 12–15 % of keep decisions near the margin, the missed keeps (a verify action could recover them), and the budget, which binds at W ≤ 12.
2. **Noise-dominated regime: the six OpenML nodes.**
   - **Increments are small against the seed noise.** sd 0.17–1.55 σ.
   - **Many edits do not change the metric at all.** 33–74 % of increments are exactly 0.
   - **Keeps happen inside the noise.** 51–99 % of comparisons lie within ±0.5 σ, and 50–100 % of keeps are within one σ of zero.
   - **This is where acceptance and evaluation control (verify, re-audit, final selection) should matter most.** The keep decision there is largely a draw on noise, and a kept configuration's recorded value is likely optimistic.
   - **That is inferred, not measured:** sweep 1 has no fresh audits, so false-keep rates and the winner's curse on these nodes are unknown.
   - **Screening under a node-level forecaster is degenerate the other way:** V\* ≈ 0 < g, so everything would be skipped. `openml_climate` (price / V\* ≈ 0.6) is the only node near the boundary.

**Also visible:**
- **Duplicates are about 60 % on every node.** The 7B proposer repeats itself, and all E1 skips on the Track S nodes are rule duplicates. This is proposer-side headroom, the reframe's option C (steering). It is not something a gate can exploit.
- **Invalid runs reach 21–24 % on `openml_climate` and `openml_ionosphere`.** That makes them a separate failure channel.

## 5. Placement on the headroom map

| Node | E1 axis: price / V\* | E2 axis: near-margin mass (excl. exact 0) | Keeps within 1 σ | Measured keep quality | Regime |
|---|---|---|---|---|---|
| `digits_mlp` | 0.02–0.06 (inert) | 0.12–0.15 | 0.24 | false keeps ≈ 0, missed 17 % | heavy tail |
| `tabular_mlp` | 0.02–0.06 (inert) | 0.12 | 0.35 | false keeps 1.5 %, missed 8 % | heavy tail |
| `openml_climate` | 0.6 (boundary) | 0.27 | 0.50 | not measured | mixed; high invalid share |
| `openml_sonar` | ∞ | 0.57 | 0.88 | not measured | noise |
| `openml_ionosphere` | ∞ | 0.79 | 1.00 | not measured | noise; high invalid share |
| `openml_wdbc` | ∞ | 0.81 | 1.00 | not measured | noise; 71 % exact zeros |
| `openml_credit_approval` | ∞ | 0.96 | 1.00 | not measured | noise |
| `openml_breast_w` | ∞ | 0.95 | 0.92 | not measured | noise; 74 % exact zeros |

## 6. Proposal for the author (R1-PAPERC-CENSUS-FIRST: the choice is the author's)

1. **Channel for the confirmatory core (A):** acceptance and evaluation control. The census finds no decision-relevant E1 state on any CPU node under the forecasters available today. E1 joins only when a per-proposal forecaster exists (Paper B C3) or on the GPU tier.
2. **Nodes:**
   - **Noise-dominated pair for the confirmatory tests:** `openml_credit_approval` and `openml_ionosphere`. They have the highest near-margin mass without being dominated by exact zeros. Alternate: `openml_sonar`.
   - **Heavy-tail contrast** with measured keep quality: `digits_mlp`. This is where the missed-keep and budget channels can be tested and a null is expected for false keeps.
   - **Boundary node** (descriptive): `openml_climate`.
3. **Prerequisite before any collection:** fresh-seed audits of sweep-1 keeps (and of final incumbents) on the chosen OpenML nodes, to turn the inferred noise-driven acceptance into measured false-keep rates and a measured winner's curse.
   - It is CPU-only and cheap: a run takes seconds.
   - It overlaps with Paper B's B.2 (sweep-1 audits). Either B.2 runs first and Paper C reuses it, or Paper C runs a small declared audit on its own seed block (`paperc_audits`).
4. **Thresholds** that would define "decision-relevant", proposed:
   - E2 near-margin mass (excluding exact zeros) ≥ 0.10;
   - for E1: price / V\* ≥ 0.3, or sd(V\*) / g ≥ 1 under the deployed forecaster.
   - On these numbers every CPU node passes for E2, and none passes for E1.
5. **Steering (C):** the 60 % duplicate rate is the largest single inefficiency the census sees. It stays an extension, but it deserves a cheap descriptive check: how much of the budget duplicates consume under each memory mode.
6. **The GPU tier (B)** gets the same census once T1 data exist (HoreKa / HTCondor). It is not possible yet.

After the author's choice, R1-PAPERC-CORE is written with the chosen nodes and channels (R-C3).
