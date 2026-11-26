# A1-ctx and the context ablation — implementation note (28 October 2026)

AI-assisted (Claude, chat session), for PLAN §10 **R1-CONTEXT-BASELINE**. **Proposal only.** This note changes no code under `r1/`; the author approves before implementation. It is grounded in `r1/c3/arms.py`, `r1/c3/features.py`, `r1/c3/offline_eval.py` and `r1/c3/train/serialize.py` at `main` `cefa389`.

This version was revised after the independent review (`docs/r1/reviews/MAC_LOCAL_DELIVERABLES_REVIEW_20261028.md`): blocking findings A1–A3 are fixed and minor findings A4–A14 are addressed. **Terminology:** a *campaign* is one run of the loop on one node, from one start seed in one memory mode; the code calls it an "instance". In the DAC sense, the instance is the node.

## 1. What exists today

**A1** (`arms.ConstantPrior`) is the weighted mean 12-bin soft label of a node's training proposals, inert ones included. When a node has no training rows (leave-one-node-out, LONO), it falls back to the **pooled** mean over the training nodes (`arms.py:98–99`). So in campaign folds A1 is a per-node prior fitted on that node's other campaigns, while in LONO folds it is a single constant. Neither is conditioned on the node's descriptors.

**Node descriptors** (`features.NODE_INFO`): rows, features, classes, minority share, metric and family (mlp or openml) for all 11 nodes, plus `sigma_node` from the noise table. A3 already sees `rows_log`, `n_features`, `n_classes` and `minority` (`features.py:371–372`). The prompt's node block (`serialize.node_lines`, `serialize.py:89–94`) shows the node **name**, the family, rows, features, classes, minority share, metric name and σ_node in two lines, and the memory mode in a third line.

**Climate** descriptors are marked **PROVISIONAL** in `features.py:61–64` (feature count and minority share "to be confirmed"). Climate is in sweep 1.

## 2. A1-ctx: the context-only rung

**Definition.** For every proposal of node j, the forecast is a 12-bin distribution p_ctx(d_j). It depends on node j **only through its descriptor vector d_j** (and on the memory mode, see below). It is fitted on the training nodes of the fold and never sees a row of node j. It uses no proposal features and no history. A1-ctx therefore varies across nodes and memory modes and is constant across the campaigns of a node.

**Decisions.** The same rules as A1: `rules.decide` for execute and keep, plus KG verify online. **No rule layer**, mirroring A1. This needs a code change, because `offline_eval.evaluate` chooses the rule layer by arm name: `decisions(P, rows, gu, rule_layer=(a != "A1"))` at `offline_eval.py:362`. An arm named `"A1-ctx"` would otherwise silently get the rule layer and skip duplicates (see the code plan).

**Descriptors d_j**, standardised across the training nodes of the fold:
- log rows;
- n_features;
- minority share;
- family (one-hot, mlp or openml);
- log σ_node.

`n_classes` is dropped: it only separates digits (10 classes) from the rest, so it has zero variance whenever digits is held out. Memory mode is a campaign setting, not a node property, and enters as a separate binary input (`memory_on` on the C3 rows).

**Numerical hygiene** (LONO folds have about 7 training nodes):
- columns with zero variance in a fold are set to 0;
- held-out descriptors are clipped to the training range of the fold (climate's minority share 0.085 lies well below the others, 0.30–0.50);
- p̄ is floored at 1e-6 per bin before the logarithm.

**Model.** The forecast is

  log p_ctx(d) = log p̄ + B·d − log Z(d)

where:
- p̄ is the pooled weighted mean soft label of the training nodes, i.e. exactly A1's LONO fallback, computed as in `ConstantPrior.fit`;
- B (12 × |d|) is fitted by weighted soft-label cross-entropy on the training rows, with ridge penalty λ‖B‖²;
- Z(d) normalises.

λ is chosen by an inner leave-one-node-out over the training nodes from the explicit grid {0.1, 1, 10, 100, ∞}. Here ∞ is implemented as B = 0, not as a large number, so the fallback is always a candidate. A one-standard-error rule picks the largest λ within one standard error of the best inner score. Inside every inner fold, p̄ and the descriptor standardisation are refitted on the inner training nodes only. Row weights are those of A1 (inverse audit-sampling probabilities).

**Where it is reported.**
- Next to A1 in both `instance` (campaign) and `lono` modes of `offline_eval.evaluate`. In campaign folds A1-ctx is expected to be weaker than A1, which sees the node's own data. In LONO it is the meaningful per-instance rung.
- In the offline-gate tables as a reference row; it is not part of the gate rule.
- In the online pilot if A1 runs there, using the deployment-time `NodeContext`: descriptors and σ_node are known before the campaign.

**Code plan (after approval).**
1. `r1/c3/arms.py`: a new class `ContextPrior` (name `"A1-ctx"`) with `fit(rows)` / `predict(rows)`, the same interface as `ConstantPrior`. `ARMS` and the default arms of `offline_eval.crossfit` stay unchanged, so existing outputs and tests do not move.
2. **Rule layer by name — two places, both changed to one shared constant.** Define `NO_RULE_ARMS = frozenset({"A1", "A1-ctx"})` once, in `r1/c3/arms.py`.
   - **Offline:** `r1/c3/offline_eval.py:362`, change `rule_layer=(a != "A1")` to `rule_layer=(a not in NO_RULE_ARMS)`, and add an opt-in `--with-context-rung` flag that adds `"A1-ctx"` to the arms passed to `evaluate`.
   - **Online:** `r1/c3/prior_model.py:120`, change `TableArmPrior.rule_layer = self.name != "A1"` to `self.name not in NO_RULE_ARMS`. The online controller reads this value (`control.py:141`) and uses it to force-skip no-ops and duplicates (`control.py:305`), so without the change A1-ctx would silently get the rule layer in the online pilot.
   - Also add `"A1-ctx": ContextPrior` to `ARM_CLASSES` (`prior_model.py:101`), and extend `arm_digest` to cover `ContextPrior`'s fitted parameters (λ, B, p̄, standardisation).
3. Tests (fixture-only) in `r1/tests/test_c3_context_prior.py`:
   - (a) synthetic nodes whose mean increment depends linearly on one descriptor: in LONO, A1-ctx beats the pooled fallback;
   - (b) nodes with identical label laws (descriptors vary, labels drawn from one law): the one-standard-error rule selects λ = ∞ and B = 0;
   - (c) A1-ctx executes duplicates (no rule layer), both offline (`offline_eval.evaluate`) and online (`TableArmPrior("A1-ctx").rule_layer is False`, and a `RuleController` with an A1-ctx prior does not force-skip a duplicate);
   - (d) no held-out row enters fitting;
   - (e) zero-variance and out-of-range descriptors give finite forecasts.
4. Before fitting on sweep data: confirm climate's rows, features and minority share with `r1/noise/check_caches.py`. This is an open item, because climate is in sweep 1 and its descriptors are provisional.

## 3. The context-aware vs context-oblivious prompt ablation

**What changes.** A second template version, `trackp_prompt/v1-ctxoff`. Only the first two node-block lines change: the `Node: …` line with the name and descriptors, and the `Metric: …; noise level sigma_node = …` line. They are replaced by one fixed line:

  `Node: not shown. Changes in the history and the recorded gain are in units of the node's noise level (z); higher is better.`

The `Memory: …` line stays byte-identical: memory mode is a campaign setting, and removing it would also take memory-mode information away from the model. Everything else is byte-identical too (budget line, incumbent lines, history lines, proposal, question and options), and the target is unchanged.

**What it does and does not test.** The ablation removes the node's **name, descriptors and noise level**. It does not make the model identity-blind:
- the file path (`train.py` for the MLP template, `config.yaml` for the OpenML template) and the configuration keys reveal the model family;
- the **raw incumbent metric** and the incumbent's configuration values can identify the node.

Two options:
- **(a) Primary, cheapest:** change the two node-block lines only. The paper says the ablation tests whether the stated node name, descriptors and noise level help.
- **(b) Stronger:** also drop the raw `Incumbent metric` value (the z-scaled recorded gain stays).

**Author decision: (a) or (b).**

**Run.**
- Kev-0.8B, Stage S (A5), same labels, splits and hyperparameters as the main A5 run; only the template version differs.
- **Two training seeds per template**, so that the template difference is not confounded with training-seed variance. Report the main A5 run's seed-to-seed RPS spread next to the difference.
- Evaluated in campaign and LONO folds. Report the RPS difference on the evaluation-half label with a cluster bootstrap over campaign seeds, and the decision utility at the primary g.
- Kev-4B only if the B.7 timeline allows (R1-CONTEXT-BASELINE).
- Cost: two extra Stage S trainings of Kev-0.8B. P.0 measured about 3.3 GB peak and 0.83 s per step on a 4090 (`docs/r1/reports/TRACKP_P0_SPIKES_20261026.md`, results table, row `kev-0.8b`).

**Code plan (after approval).**
- Add a separate `serialize.node_lines_ctxoff()` and leave `node_lines` untouched, because `exam_synthetic` uses it.
- `serialize_view` gains `context: bool = True`. With `False`, it uses `node_lines_ctxoff()` and records `prompt_version = "trackp_prompt/v1-ctxoff"`.
- Tag the training cache by prompt version.
- Re-check the 1,024-token length rule for the new template; it is shorter.
- The changes stay within `r1/c3/train/`, so they go through the Track P agent's branch with independent review.

**Raise with the Track P owner (outside this note).** `serialize.POOL` still lists the Laya and StartLux tokenizers, and `MAX_TOKENS = 1024` is "Laya's limit". Both families left the decision-model pool under R1-C3-POOL, so the length rule is still checked against tokenizers that are no longer in scope.

## 4. Open for the author

1. Approve A1-ctx as defined: descriptors, ridge model with inner LONO and the one-standard-error rule, no rule layer.
2. Prompt-ablation option (a) or (b).
3. Whether A2-ctx (A1-ctx plus the rule layer) is also wanted.
4. Confirm climate's descriptors before any fit.
