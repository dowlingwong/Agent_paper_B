# E1 noise-floor and cost pilot — 12 October 2026

**Label: `PILOT`. Not evidence, and not to be quoted as a result (RUNBOOK §1, rule 3).** This report covers RUNBOOK 0.4 / E1, run by an AI agent (Claude) at the author's request. The proposed node verdicts below are for the author's D21 decision at the E2 STOP; nothing has been adopted.

- **Raw data:** `results/r1/pilot/E1_20261012T145353Z/` (`runs.jsonl`: 1,952 runs; `edits.json`; `manifest.json`; `summary.json`).
- **Generator:** `python -m r1.noise.e1_noise_floor --seeds 10 --workers 4`. Because the shell is time-boxed, it was run in resumable chunks with `--resume … --deadline 150`.
- **Tables:** `python -m r1.noise.e1_report <run dir> --md docs/r1/reports/NOISE_FLOOR_20261012_tables.md`. The full per-edit table is in that file.
- **Harness:** branch `r1` at `b55209f` plus the L8b working-tree changes, which were later committed unchanged as `423addd`. The manifest records `dirty: true` for that reason.
- **Host:** the Linux VM on the author's Mac (aarch64, 4 cores, 3 GiB). Wall times were measured with 4 parallel workers, so they overstate per-run cost.

## Design

For each node: the baseline c0 and up to five typical single edits c1…c5.
- **Python-constant nodes:** each edit takes an editable numeric symbol ×0.5 or ×2, drawn with a seed fixed per node.
- **OpenML nodes:** C ×0.5 and ×2, both model-type switches, and the class-weight switch.

Every configuration ran under three seed conditions with 10 seeds each:
- **train:** training seed varied, split at the node default;
- **split:** split seed varied, training seed at the node default;
- **joint:** both varied together.

Each configuration also ran twice at the node's default seeds, to check determinism. Paired differences d_s = m(c_k, s) − m(c0, s) use identical seeds.

What is estimated:
- **Δ̂_J:** the mean joint-condition difference, the estimate of J(c_k) − J(c0).
- **sd(Δ̂):** the noise of one campaign comparison (σ_d in T2).
- **P(wrong) = Φ(−|Δ̂_J|/sd):** the error rate of the default keep rule on that edit (T2, Proposition 1).
- **Material edit:** |Δ̂_J| > 2 se and |Δ̂_J| ≥ 0.002 metric units.

**Proposed D21 rule (not adopted):** a node qualifies when it has at least 2 material edits with mean P(wrong) ≥ 0.10. **Proposed split policy:** `"vary"` when sd_train/sd_joint < 0.5 over the material edits, or over the baseline when the node has no material edit.

## Node summary

| Node | σ_train | σ_split | σ_joint | material edits | mean P(wrong), material | sd_train/sd_joint | proposed D21 | proposed verify split |
|---|---|---|---|---|---|---|---|---|
| `digits_mlp` (new, L8b) | 0.0063 | 0.0075 | 0.0125 | 5 of 5 | 0.16 | 0.65 | qualifies | `fixed` |
| `tabular_mlp` (new, L8b) | 0.0032 | 0.0125 | 0.0153 | 3 of 5 | 0.10 | 0.56 | qualifies (borderline) | `fixed` |
| `openml_breast_w` | 0.0000 | 0.0049 | 0.0030 | 2 of 5 | 0.16 | 0.39 | qualifies | `vary` |
| `openml_ionosphere` | 0.0000 | 0.0367 | 0.0437 | 2 of 5 | 0.16 | 0.06 | qualifies | `vary` |
| `openml_wdbc` | 0.0000 | 0.0068 | 0.0080 | 2 of 5 | 0.16 | 0.11 | qualifies | `vary` |
| `openml_credit_approval` | 0.0000 | 0.0080 | 0.0169 | 2 of 5 | 0.09 | 0.15 | more seeds needed | `vary` |
| `openml_diabetes` | 0.0000 | 0.0336 | 0.0317 | 0 of 5 (3 unresolved, noisy) | – | 0.00 | more seeds needed | `vary` |
| `lr_synthetic` | 0.0001 | 0.0152 | 0.0099 | 0 of 5 | – | 0.01 | does not qualify | `vary` |
| `mlp_synthetic` | 0.0001 | 0.0013 | 0.0016 | 0 of 5 | – | 0.06 | does not qualify | `vary` |
| `mlagentbench_vectorization` | 2.42 | 2.23 | 2.29 | baseline only | – | – | does not qualify (timing metric; not bit-identical) | – |
| `openml_credit_g` | – | – | – | – | – | – | **not measured:** no local data cache; OpenML is blocked from the VM | – |

σ values are the sd of the baseline metric over 10 seeds. Every node except `mlagentbench_vectorization` reproduced its metric bit-for-bit at fixed seeds.

## What the pilot says

1. **Question 1 (R1-GATE-FIRST) has a provisional answer.** Five CPU nodes have real, decision-relevant noise under the proposed rule: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere` and `openml_wdbc`. Two more (`openml_credit_approval`, `openml_diabetes`) need more seeds before their edits resolve. On `openml_diabetes` the paired sd of a model-type switch is 0.025 against effects that 10 seeds cannot sign, so the default rule is close to a coin flip there.
2. **`lr_synthetic` and `mlp_synthetic` are not usable noise nodes.** On both, every typical edit moves J by less than 0.0003 (`mlp_synthetic` sits at AUC 0.9994). No decision there carries a material consequence, whatever the noise.
3. **The default rule errs on about one decision in six on material edits.** Mean P(wrong) is 0.16 on four qualifying nodes and 0.10 on `tabular_mlp`, and the share of the available gain lost to wrong decisions is 0.08–0.17.
   - At the campaign's own default seeds, 1 of 20 resolved decisions was wrong: on `openml_ionosphere`, the gradient-boosting switch has Δ̂_J = +0.029 ± 0.024, but the campaign seeds show −0.014.
   - Most edits are small, so most single errors cost little. That is why the regret share is lower than the error rate.
   - Caveat (L14 review): P(wrong) here is a plug-in from Δ̂_J on edits *selected* by |Δ̂_J| > 2 se. With 10 seeds, that selection caps it at Φ(−2/√10) ≈ 0.26. It is a rough figure, not an estimate with a stated error.
4. **Verify under the default `"fixed"` split policy is worthless on the OpenML logistic-regression nodes, and weak on the others.**
   - The training seed does not move logistic regression at all: σ_train = 0.0000 on all five OpenML nodes, so `"fixed"` verify re-runs reproduce Δ̂ exactly.
   - For the model-type edits, the training-seed share of the paired noise (sd_train/sd_joint) has per-node medians of 0.06–0.39; per edit it ranges from 0.04 to 0.46.
   - On `digits_mlp` and `tabular_mlp` it is 0.56–0.65, so `"fixed"` recovers about half of the value of `"vary"` (T2, Proposition 3).

   This bears directly on the 9 Oct decision to keep `"fixed"` for every node. The author may want to revisit it per node at E2.
5. **ϱ depends on the kind of edit.**
   - Small hyperparameter edits have ϱ_joint ≥ 0.95, so a campaign comparison is precise relative to the edit's size.
   - Model-type switches have ϱ_joint = 0.39–0.85, so the comparison noise is often close to that of two independent runs.

   The illustrative ϱ = 0.5 assumed in PLAN §2 holds for structural edits only.
6. **Run cost.** About 1.1–1.5 s per run on these CPU nodes (14.9 s on `mlp_synthetic`), measured under 4-way parallel load in the VM.

## Caveats

- **The two seed effects are not additive.** On every material `digits_mlp` edit, sd_joint² < sd_train² + sd_split². T2's additive split of σ_d into a training part and a split part is therefore only an approximation. From 12 Oct (v2), E1b uses the median sd_joint as σ_d (L14 review, finding 14).
- The edits are hand-specified "typical" edits, not LLM proposals. The proposal law (μ₀, τ) that T2's index needs must come from real campaigns, not from this table.
- Ten seeds per condition cannot resolve effects below about 2·sd/√10. "Unresolved" means the effect is not known, not that it is zero.
- Seeds were drawn as fixed integer blocks (1001+, 2001+, 3001+), not at random.
- `openml_credit_g` needs a one-time OpenML download on the Mac, which this VM cannot do.
- Wall-clock figures are not usable as cost estimates for planning on deepthought.
