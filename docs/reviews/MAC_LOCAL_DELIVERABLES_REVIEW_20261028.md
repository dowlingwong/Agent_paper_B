# Independent review: TabPFN pin, A1-ctx note, NI masking code, manuscript sections (28 October 2026)

AI-assisted independent review (Claude). The reviewer did not produce the deliverables. No file under review was edited. Severity labels: **[B]** blocking (fix before acceptance), **[m]** minor.

## What was run

- `python3 -m pytest -q r1/tests/test_c3_ni_masking.py r1/tests/test_c3_arms_eval.py` in the repository snapshot: **15 passed** (5.1 s).
- Extra false-positive probe (scratch script outside the repository): the null fixture `synth(False, seed=s)` for s = 0…19, instance mode, k = 3, 300 bootstrap draws. Result: 0/20 pooled flags and 0/40 per-node flags. The mean masked − full RPS was −0.0011 (sd 0.0007). The trivial null is clean. Its limits are in finding N5.
- `latexmk -pdf` in a copy of the paper tree: built (6 pages) with **0 warnings**, no undefined references or citations, and no LaTeX errors. The extracted PDF text and metadata contain no author, institution, host or repository names.
- Every wheel citation in the TabPFN proposal was checked against `tabpfn_whl/x/`, the PyPI JSON and both Hugging Face cards (fetched 28 Oct).

## Verdicts

| # | Deliverable | Verdict |
|---|---|---|
| 1 | `TABPFN_PIN_PROPOSAL_20261028.md` | **Accepted with fixes** (minor only) |
| 2 | `A1_CTX_IMPLEMENTATION_NOTE_20261028.md` | **Accepted with fixes** (3 blocking for the implementation plan) |
| 3 | `r1/c3/ni_masking.py` + `r1/tests/test_c3_ni_masking.py` | **Not accepted** (fixable; 3 blocking) |
| 4 | `papers/r1/sections/{problem,theory,setup}.tex` + `main.tex` preamble | **Accepted with fixes** (11 blocking, all sentence-level) |

---

## 1. TabPFN pin proposal: Accepted with fixes

**Verified correct:**
- version 9.2.0, uploaded 2026-10-12, Python ≥ 3.10, torch ≥ 2.5, Apache-2.0;
- the wheel sha256 matches both PyPI and the local file;
- `settings.py:37–38` (default V3_5);
- `model_loading.py:213–223` (v3.5 source, default file `tabpfn-v3.5-20260909.safetensors`) and the multitask comment at 210–211;
- `constants.py:31–39` (versions);
- `model_loading.py:558–570` (licence acceptance for v2.5 and later only) and `458–460` (direct download for v2 only);
- `errors.py:31–53` (`TABPFN_TOKEN` steps);
- `regressor.py:2344–2365` (`get_embeddings`);
- `finetuning/finetuned_regressor.py:155` (`FinetunedTabPFNRegressor`);
- v2 default file `tabpfn-v2-regressor.ckpt` (`model_loading.py:119`);
- both HF card statements (v3.5 licence wording, 20,000-feature limit, no paper; v2 `priorlabs-1-1`, Hollmann et al., *Nature* 2025, doi 10.1038/s41586-024-08328-6).

| ID | Sev | Location | Finding | Why it matters | Exact fix |
|---|---|---|---|---|---|
| T1 | m | Facts table, "Scale" row | `regressor.py:441` is not "sub-sampling only above 50,000 rows". It is the **v2.5 pre-training limit** note ("50_000 samples/rows, 2_000 features"). The default `SUBSAMPLE_SAMPLES` is `None`, i.e. no subsampling (`inference_config.py:213–216`). `regressor.py:184` says TabPFN-3+ supports up to 1,000,000 rows. The v2 config limits are 10,000 rows and 500 features (`inference_config.py`, `_get_v2_config`, around line 522–524). | Wrong citation. The conclusion (≈2,000 rows is well inside) still holds, but the v2 limit is the binding one and is not stated. | Replace the row with: "No subsampling by default (`inference_config.py:213`). Pre-training limits: v2 10,000 rows / 500 features (`inference_config.py` `_get_v2_config`); v2.5 50,000 / 2,000 (`regressor.py:439–443`); TabPFN-3+ up to 1,000,000 rows (`regressor.py:184`); v3.5 card 20,000 features." |
| T2 | m | Gating row; "What the author has to do" 2 | A **Hugging Face** account and token may also be needed. `browser_auth._get_license_name` (line 147 ff.) queries the HF API with the user's HF token "so gated repos resolve correctly" and raises if the user has no HF access. The gated-repo error (`errors.py:56–74`) tells the user to accept the HF terms and set `HF_TOKEN`. The v3.5 card does not say whether the repo is HF-gated. The licence check also contacts the Prior Labs licence server at download (`verify_token`, `check_license_accepted`), and `save_token` writes the key to `~/.cache/tabpfn/auth_token`. | The author's to-do list may be incomplete. The secret also ends up on disk outside `secrets.env`. | Add to step 2: "an HF account with the repo's terms accepted and `HF_TOKEN` available, if the repo is HF-gated; network access from TASL-7 to `ux.priorlabs.ai` and its API at first download; after download, delete or chmod 600 `~/.cache/tabpfn/auth_token`." |
| T3 | m | Options A, "For" | "Strongest available tabular model" is not supported by anything checked. | Unsupported claim in a decision document. | Use "newest release and package default". |
| T4 | m | Option B/C; v2 licence row | The v2 licence has an "additional attribution requirement", but the proposal does not say what it requires. The card only links `priorlabs.ai/tabpfn-license/`, which was not read. | Compliance obligations of option B/C are unknown. | Read the licence page and state the attribution text that must appear in the paper or code release. |
| T5 | m | Option A/C | The fine-tuning rung creates a **derivative** of the v3.5 weights. The licence restricts derivatives and outputs to non-commercial, non-production use, and its wording ("limited internal evaluation") may restrict *redistributing* fine-tuned weights or predictions with the paper's artifacts. | This affects artifact release and reproducibility, not just running the rung. | Add to "What the author has to do" 2: "confirm whether fine-tuned v3.5 weights and its predictions may be released with the code; if not, release only v2 artifacts." |
| T6 | m | Option C, "Against" | "~2,000 rows fine-tune in minutes on a 4090" is an unmeasured estimate. | It is presented as fact. | Mark it as an estimate ("expected; not measured"). |
| T7 | m | Proposed pin, last bullet | `Settings` reads `TABPFN_*` variables from a `.env` in the working directory (`settings.py:27–29`, `env_file=".env"`). A stray `TABPFN_MODEL_VERSION` or `TABPFN_MODEL_CACHE_DIR` could silently change the run. | This strengthens the "set `model_version` explicitly" rule. | Add: "Record `tabpfn.settings` (model_version, cache dir) in every manifest, and pass `model_version` and the checkpoint path explicitly." |
| T8 | m | "What R1-TABPFN needs" | The regression target is not stated. TabPFN regresses a scalar, so the target is presumably z = Δ_label/σ_node on the 5 label seeds. Its predictive distribution then includes label noise, whereas the other arms' soft labels fix the width (pooled σ/√K or se_audit). | Comparability of RPS across arms. | State the target and the bin-integration rule, and note the width difference as an open design point for R1-TABPFN. |
| T9 | m | Facts, `regressor.py:151–172` | Off by one: `logits` is at line 173. | Citation accuracy. | Change to `151–173`. |

---

## 2. A1-ctx and context ablation note: Accepted with fixes

**Verified correct:**
- A1's LONO fallback: `ConstantPrior.predict` returns `self.by_node.get(r["node"], self.pooled)` (`arms.py:98–99`), and `pooled` is the weighted mean over all training rows. In `instance` folds, A1 is the node's own mean over the other campaigns.
- A3's descriptor features: `features.py:371–372`.
- λ = ∞ ⇒ B = 0 ⇒ p_ctx = p̄ = A1's pooled fallback (exact, if p̄ is computed as in `ConstantPrior.fit`).
- The node block is exactly three lines (`serialize.py:89–94`).
- `edit_text` prints the file (`serialize.py:112`).
- `MAX_TOKENS = 1024` and `PROMPT_VERSION = "trackp_prompt/v1"` (`types.py:26–27`).

| ID | Sev | Location | Finding | Why it matters | Exact fix |
|---|---|---|---|---|---|
| A1 | **B** | §2 "no rule layer, mirroring A1"; code plan 2 | `offline_eval.evaluate` chooses the rule layer **by arm name**: `decisions(P, rows, gu, rule_layer=(a != "A1"))` (`offline_eval.py:362`). An arm named `"A1-ctx"` would get the rule layer, so its duplicates would be force-skipped. That contradicts the note's definition. | A1-ctx would silently be "A2-ctx" in every reported value. | In the code plan, add: "change `offline_eval.py:362` to `rule_layer=(a not in NO_RULE_ARMS)` with `NO_RULE_ARMS = {"A1", "A1-ctx"}`, and add a test that A1-ctx executes duplicates." |
| A2 | **B** | §3 neutral line | "Values below are standardised by the node's noise level (z units)" is false for the template. `incumbent_lines` prints the **raw** metric (`Incumbent metric: {fmt(current_best)}`) and raw configuration values. Only the history increments and the recorded gain are in z. | The ablation prompt would state something false to the model. | Use: `Node: not shown. Changes in the history and the recorded gain are in units of the node's noise level (z); higher is better.` (Under option (b), also drop the raw metric.) |
| A3 | **B** | §3 "What changes" | The note removes the `Memory:` line as part of the "context" block. But §2 of the same note says memory mode "is a campaign setting, not a node property" and keeps it as an input to A1-ctx. Removing it also confounds the ablation: the decision model loses memory-mode information, which nothing else in the prompt carries. | The ablation would no longer isolate the node context. | Remove only the `Node:` and `Metric:` lines and keep `Memory: …` byte-identical. Say so in the paper. |
| A4 | m | §1 last bullet; §3 | The node block shows more than "the same descriptors, plus metric, sigma_node and the memory mode": its first token is the **node name** (`Node: {node} (…)`). | The ablation removes an explicit identity cue as well as descriptors. The reading in §3 ("tests whether the explicitly stated context (descriptors and noise level) helps") must include the name. | §1: "shows the node name, family, rows, features, classes, minority share, metric name, σ_node and memory mode". §3 reading: "tests whether the stated node name, descriptors and noise level help". |
| A5 | m | §3 "What it does and does not test" | The file path does not identify the node. Edit paths are `train.py` (MLP template) or `config.yaml` (OpenML template): they reveal the **family**, as the configuration keys already do. The residual node-identifying cues are the raw incumbent metric and the incumbent's numeric values. | Option (b)'s path neutralisation buys little. The raw metric is the cue that matters. | Replace with: "The file path and configuration keys reveal the family; the raw incumbent metric and the incumbent's values can identify the node." Make option (b) "drop the raw `Incumbent metric` value (the z-scaled recorded gain stays)". |
| A6 | m | §2 Descriptors / Model | In LONO folds the descriptors are degenerate. When `digits_mlp` is held out, every training node has `n_classes = 2`: the standardised column is 0/0, and the held-out value lies outside the training range. With one MLP node left, the family one-hot has a single non-zero row. With ≈7 training nodes and 7–8 inputs, B can interpolate the node means. Climate's minority share (0.085) extrapolates far outside the others (0.30–0.50). | The ridge model is not well specified at the fold level: it can give NaNs or extreme log-linear tilts. | Specify: zero-variance columns set to 0; held-out descriptors clipped to the training range; drop `n_classes` (it only separates digits); p̄ floored at 1e-6 per bin before the log; λ grid stated explicitly, with ∞ implemented as B = 0, not as a large number. |
| A7 | m | §2 model, "inner leave-one-node-out" | Nested CV hygiene is not specified: p̄ and the descriptor standardisation must be refitted inside every inner fold. | Otherwise the inner selection leaks across inner folds. | Add one sentence saying so. |
| A8 | m | §2 test plan, bullet 2 | "Nodes whose means are unrelated to the descriptors: the inner selection must pick λ = ∞" is not a guaranteed property. With finite samples, a finite λ can win the inner CV by chance, so the test would be flaky or false. "Never worse than the fallback in the inner selection" is true only as an inner-CV score statement, not out of sample. | A test that asserts something the method does not guarantee. | Make the test either (a) identical node laws (descriptors vary, labels drawn from one law) with a 1-SE rule toward λ = ∞, asserting B = 0; or (b) assert the outer RPS is within a tolerance of the fallback's. |
| A9 | m | §2 "A1-ctx therefore varies across instances but is constant within a campaign" | Mixed terminology. In the code, "instance" means a campaign (`node__sN`), and A1-ctx is constant across all campaigns of a node (per memory mode). In the DAC sense, instance = node. The same note later uses "cluster bootstrap over instances" in the code sense. | Readers will misread the claim. | "A1-ctx varies across nodes (and memory modes) and is constant across the campaigns of a node." Use "campaign" for the code's instance throughout. |
| A10 | m | §3 Run | One extra Stage S training run at one training seed: the RPS difference then confounds the ablation with training-seed variance, which an instance bootstrap does not capture. | It can produce a spurious ablation effect. | Train ≥ 2 seeds for both templates, or report the main A5 run's seed-to-seed RPS spread next to the difference. |
| A11 | m | §3 code plan | `node_lines` is shared with `exam_synthetic` (`serialize.py:81`). | Changing it changes the exam prompts. | Add a separate `node_lines_ctxoff()` and leave `node_lines` untouched. Also tag the training cache by prompt version. |
| A12 | m | §3 Run, cost line | "3.3 GB peak and 0.8 s per step" has no source. | Unverifiable here. | Cite the P.0 record (file and row). |
| A13 | m | §1 | `climate` descriptors are marked **PROVISIONAL** in `features.py:61–64` at cefa389 (feature count and minority "to be confirmed"). | A1-ctx (and A3, and the prompt) use them, and climate is in sweep 1. | Add an open item: "confirm climate's rows, features and minority with `check_caches.py` before fitting A1-ctx". |
| A14 | m | (aside, not in the note's scope) | `serialize.POOL` still lists the Laya and StartLux tokenizers, and `MAX_TOKENS` is "Laya's limit". Both families were removed from the decision-model pool. | The length rule for the new template is checked against tokenizers no longer in scope. | Raise with the Track P owner; not a fix to this note. |

---

## 3. NI masking code and tests: Not accepted (fixable)

**Verified correct:**
- both arms are cross-fitted on identical folds, because `OE.crossfit` builds the groups once for all arms;
- LightGBM is deterministic (seed 0);
- the RPS evaluation mask uses soft ≠ None, `eval_weight` > 0 and not `rule_skip`, so DI-changed audits (weight 0), no-ops and duplicates are excluded;
- the utility uses the rule layer for both arms, `delta_true` from the **evaluation** half (7006–7010) and 20× scaling, as in `offline_eval`;
- the bootstrap clusters are `instance` (node and seed, both memory modes together), consistent with `offline_eval`;
- signs: RPS is masked − full and utility is full − masked, so positive means "full better" for both;
- `evidence_against_NI` is the lower RPS CI > 0.

No evaluation seed enters training: soft labels use 7001–7005 (`split_audit`).

| ID | Sev | Location | Finding | Why it matters | Exact fix |
|---|---|---|---|---|---|
| N1 | **B** | Module docstring "Reading"; `evidence_against_NI` (l. 120–121); `main()` "reading" | **The test is not the T4 §3/§6 test, and the flag's name overclaims.** T4 requires both forecasters to be given the **whole** proposal history x_{1:n}, and states that results can proxy for x_{1:n−1} and help a forecaster that sees less "even under (NI)". Here neither arm sees x_{1:n}: both see a lossy summary (counts, last-edit flags, budget). The positive fixture `synth(True)` shows this. It is observationally identical to an NI-*holding* loop in which θ is encoded in an earlier proposal that the features do not summarise, and the test flags it. Second, a positive also arises when (NF-b) fails: the increments depend on the incumbent, and the incumbent depends on keeps (T4 §8: non-interaction fails on `digits_mlp`). The docstring's claim that the test is "conservative" is also wrong. Retained result-dependent features bias it toward zero, but the lossy summary biases it toward false positives, so the direction of the bias is undetermined. | The output key and the "reading" string will be quoted as "evidence against NI" when they mean something weaker. | Rename the key to `results_add_predictive_value` (keep `evidence_against_NI` out of outputs). Replace the reading with: "A masked-minus-full RPS interval above zero means that past results improve this forecaster beyond the retained summary of the proposal history. It is evidence against (NF ∧ NI) *only to the extent that the retained features summarise x_{1:n}*. An interval containing zero does not establish (NI). The direction of the bias is undetermined: incumbent-relative features leak results into the masked arm (toward zero), and the history summary is incomplete (toward false positives)." Optionally strengthen the masked arm with proposal-only history features (e.g. last *proposed* value per key, proposal counts per key over all trials, valid or not), which are functions of x_{1:n} alone. |
| N2 | **B** | `run_test` l. 99–101 | **The RPS is scored against the training-half label.** `soft` is built from `split_audit(a)[0]`, i.e. seeds 7001–7005 (`offline_eval.py:177–187`). The utility correctly uses the evaluation half. When a (candidate, incumbent) pair recurs across campaigns (same start configuration, same audit seeds, bit-exact nodes), the held-out row's scoring target equals a training row's label, *including its audit noise*. There is also no edit-hash grouping in the folds (finding P8). The full arm has incumbent-identifying features (`recorded_gain_z` pins the incumbent's metric, hence the incumbent on bit-exact nodes), so it can memorise pair-specific label noise better than the masked arm. That is a mechanism for a **spurious positive**. | The evidence flag rests on RPS, and the seed split exists precisely to prevent this (C3_DESIGN §4: shared seeds made the pilot gate "pass" spuriously). | Score RPS against an evaluation-half soft label. In `ni_masking`, re-read the audits, build `soft_eval = soft_label(ev["delta_audit"], …)` from `split_audit(a)[1]` with the same `sigma_mode`, and use it in `rps(...)`. Or add `soft_eval` to `OE.assemble`. Also report the RPS with folds grouped by `(node, candidate_hash, incumbent_hash)` as a robustness row. (The same label-half scoring exists in `offline_eval.evaluate`'s `log_score`; report it there separately, since it is pre-existing.) |
| N3 | **B** | `OUTCOME_FEATURES` comment and module docstring (l. 12–16, 28–33) | The set is correct as the **direct** outcome features, and complete in that sense: `last_key_delta_z`, `last_key_kept`, `keeps_so_far`, `trials_since_keep`, `recorded_gain_z`, `invalid_so_far`. But by the docstring's own definition ("features computed from revealed results, or from decisions that depend on revealed results"), more retained features qualify. (i) **Incumbent-dependent through keeps:** `old_num`, `log_ratio`, `direction`, `model_type_code` (the incumbent's `model_type`, `features.py:365`), `active_key` (the candidate's model type is the incumbent's unless edited), `cfg_equals_incumbent`, `active_equals_incumbent`, `active_seen_before` (also seeded with incumbent projections, l. 425–427), `full_seen_before`, `same_edit_count` and `reverse_of_last_key_edit` (both use the incumbent's old value). (ii) **Validity-dependent:** `observe()` returns before updating any history on invalid or skipped rows (l. 406–411), so `key_edit_count`, `same_edit_count`, `reverse_of_last_key_edit`, `active_seen_before` and `full_seen_before` count *valid* trials only. That is a result, since `invalid_so_far` is masked as one. The docstring lists only 5 retained incumbent-relative features and calls the edit counts "proposal history". | The reader is told the masked arm sees "the proposal history" when it sees result-dependent features. | Keep the set, but rename it `DIRECT_OUTCOME_FEATURES`. List the retained result-dependent features (both groups above) in a second tuple `RETAINED_RESULT_DEPENDENT` that is written to the output JSON. Correct the docstring sentence to "the remaining features include proposal-history counts over *valid* trials and incumbent-relative edit features; both depend on results". |
| N4 | m | per-node `evidence_against_NI` | A 95 % flag per node across 8 nodes and 2 modes, with no multiplicity control. | One per-node flag will be over-read. | State in the docstring and output that the primary reading is pooled, instance mode, and that per-node intervals are descriptive. Or report Holm-adjusted per-node flags. |
| N5 | m | tests | (a) `test_detects_information_when_results_predict_increments` tests "results add value beyond the retained features", not NI failure (see N1). Rename it. (b) The false-positive test is a trivial null: the outcome feature is noise independent of everything, at one seed. My 20-seed probe gave 0 flags, so the null is clean, but it does not exercise the realistic nulls: (i) outcome features **correlated** with retained features but carrying no extra information (e.g. `keeps_so_far` ≈ f(`budget_index`), `recorded_gain_z` a deterministic function of the proposals); (ii) recurring (candidate, incumbent) pairs with shared label-half noise, which would have caught N2. (c) Untested: `main()` end to end (assemble with seed split, `--sigma-mode`, JSON keys); the eval mask excluding weight-0 DI-changed rows; LONO with ≥ 3 nodes. | The tests do not cover the failure modes that matter. | Add: `test_no_flag_when_outcome_features_are_functions_of_retained_features`; `test_no_flag_under_recurring_pairs_with_shared_label_noise` (it must pass after the N2 fix and fail before); a 10-seed loop asserting ≤ 2 pooled flags on the null; a tiny-table `main()` test. |
| N6 | m | `main()` | It does not call `OE.table_noise(table)`, unlike `offline_eval.main`, so it skips the pinned noise-source sha256 check. | Integrity parity with the gate script. | Call `OE.table_noise` and include `noise_source` in the output, as `offline_eval.main` does. |
| N7 | m | `--sigma-mode` default `se_audit` | This matches `offline_eval.assemble` and the A3 used by the gate. Track P labels use `pooled_node` (R1-SOFT-SIGMA), and the RPS depends on the soft-label width. | Which width is primary for the NI test is undeclared. | Add a sentence: "primary = the width of the A3 arm in the gate run (`se_audit` at cefa389); `pooled_node` is a sensitivity". Or require the flag explicitly. |
| N8 | m | docstring l. 1 | It cites `docs/r1/proposals/T4_PROP10_REVISION_20261028.md`, which is not in the repository at cefa389 (the file is in `outputs/t4/`). | Dangling reference. | Commit the revision at that path, or cite where it is. |
| N9 | m | `_summary` | When `w.sum() <= 0`, it omits `n_instances`, so the schema is inconsistent. | Downstream readers may raise KeyError. | Always return `n_instances`. |

---

## 4. Manuscript sections: Accepted with fixes

Build clean (0 warnings, no undefined references or citations). No anonymity leaks in the text or the PDF metadata. The 10(c) slope is correct: φ(0)(1 − 1/√2) = 0.39894 × 0.29289 = 0.11685, so "≈ 0.117" matches T4's "≈ 0.1168". It is also consistent with the β = 1000 row (116.85 + αφ(0) − g/2 = 116.997). The V(t; μ, τ, σ) formula matches T2 Prop 1 / T4 Prop 6 (checked by derivation). Prop 1(i)/(ii) matches 8′.1–8′.3. The Gaussian part matches T4 §1 / Prop 6. The theorem bullets match 10(a′).1–3 apart from the points below.

| ID | Sev | Location | Finding | Why it matters | Exact fix |
|---|---|---|---|---|---|
| P1 | **B** | theory.tex l. 42–47 (NF) | "In practice this requires three things" states (NF-a)–(NF-c) as **necessary**. T4: "(NF) holds if (NF-a)–(NF-c) hold and U ⊥ W" (sufficient), "these are also the ways it typically fails". The third bullet also drops part of (NF-c): "the same under every policy, **and filtered proposals do not use up the horizon**" (or the no-re-proposal alternative). | It misstates the theorem's hypothesis, which is the specific check the brief asked for. | "It holds if the following hold (sufficient, not necessary) and $U$ is independent of $W_{1:N}$:" … third bullet: "no-op and duplicate status that is a function of $x_{1:n}$ alone, the same under every policy, with filtered proposals not using up the horizon (or no earlier effective configuration re-proposed within the horizon)". Second bullet: "…and a joint law of the comparison noises that does not depend on the incumbent's identity or history." |
| P2 | **B** | theory.tex l. 62 (contrapositive) | (a) "one-step configuration" must be the **Bayes** one-step policy with the exact V*_n. A learned, miscalibrated one-step configurator can be beaten even when (NF) ∧ (NI) hold. (b) T4: "This failure is necessary, not sufficient … Nothing here says that RL in particular is needed." Neither qualifier is in the text. | Overclaim at the paper's central reading. | "The contrapositive: a policy can beat the Bayes one-step policy only if (NF) or (NI) fails. This is necessary, not sufficient, and nothing here says that RL in particular is needed. When either fails, the loss can be unbounded:" |
| P3 | **B** | theory.tex l. 84 (masking implication) | "under (NI), showing a forecaster the executed results … should not improve it" drops "(NF) and", drops **Bayes**, and drops "given the whole proposal history x_{1:n}". T4 explicitly warns that a forecaster seeing less than x_{1:n} can gain from results even under (NI). | It overstates what the masking test can show, and it is inconsistent with the script (N1). | "Under (NF) and (NI), the Bayes forecast given the whole proposal history $x_{1:n}$ gains nothing from executed results; a forecaster given less of the history can gain from results even under (NI)." |
| P4 | **B** | theory.tex l. 87; setup.tex l. 54–58 | "We report both checks" / "We also report the two checks" states as decided something T4 §6–§7 leaves open ("proposals only; nothing here is authorized"; "Decide which of the §6 tests enter the plan"). TECH_ROUTE also moves the C4 A/B work to the appendix or later. The forced-decision test also covers only the **keep channel** of (NF-a). | It claims a protocol the author has not adopted. | Replace with "We plan two checks \TBD{author decision on which T4 §6 tests enter the plan}". For the forced-decision bullet, add: "(this tests only the keep channel of (NF), not execute-vs-skip or what is displayed)". |
| P5 | **B** | theory.tex l. 30 | "Proposition 1 gives the optimal configuration θ_n in closed form … c_n = g and t_n = t*_n" omits r_n. The verification budget is outside Prop 1 and Theorem 1: J_g has no verification cost, and T4 R1(ii) calls KG verify an information action outside 10(a′). | It overclaims the scope over the three-parameter configuration defined in problem.tex. | "…gives $c_n=g$ and $t_n=t^*_n$ for $r_n=0$; verification ($r_n>0$) is an information action outside these results." In problem.tex l. 10 add "(not priced in $J_g$ below)". |
| P6 | **B** | theory.tex l. 52 / problem.tex l. 12–13 | The theorem holds "under the setting of §1", which includes "**execution reveals only H_n**; any other run output that predicts later increments (absolute metric, learning curves, wall time, crashes) must be included in H_n". problem.tex says only "An execution reveals $H_n$". The real loop also reveals the absolute metric and crashes. | It is a hypothesis of the theorem the real loop can violate. | problem.tex: "An execution reveals $H_n=\Delta_n+\eta_n$; we treat every other run output that could predict later increments (absolute metric, crashes, wall time) as part of $H_n$." |
| P7 | **B** | theory.tex l. 67 (Prop 2(a)) | "feedback, with (NI) intact". T4 10(b): "(NI) holds under each policy's law; there is no common law to state it under." | Imprecise in a way the re-review specifically corrected. | "(a) *feedback*, with (NI) holding under each policy's law: …" |
| P8 | **B** | setup.tex l. 27 | "Splits are by campaign, **with edit-hash grouping**". No edit-hash grouping exists anywhere in `r1/` at cefa389 (grep). `offline_eval.folds_by_instance` folds by seed rank within node, mod k. This also matters for N2. | The paper states a protocol the gate code does not run. | Either implement grouping in `OE.crossfit` (folds by connected components of (node, candidate_hash, incumbent_hash) over seeds) before the gate run, or change the text to "Splits are by campaign seed (all nodes trained together; a seed's campaigns in both memory modes share a fold), plus LONO" with \TBD{edit-hash grouping}. |
| P9 | **B** | setup.tex l. 22 | "width set by the pooled node noise" is true for Track P (R1-SOFT-SIGMA, σ_node/√K). But `offline_eval.assemble` defaults to `se_audit`, and `offline_eval.main` has no option, so A1–A3 and the gate use the per-proposal audit SE. | A factual inconsistency with the repository on a gate arm. | Either switch `offline_eval` to `pooled_node` for sweep-1 tables (and say so), or write "…width $\sigma_{\mathrm{node}}/\sqrt{5}$ for the decision models; the tabular arms use the audit standard error \TBD{align}". |
| P10 | **B** | setup.tex l. 52 (gate) | T4 R4: the 20-run scaling "has **no guaranteed sign relation** to the campaign gain … and the manuscript says so", and "whether '20-run' means 20 proposals or 20 executed runs must be stated". In code it is 20 × the mean per **logged proposal** (`offline_eval.py:26–29`). | A required statement from the source of truth is missing. | "…scaled to 20 logged proposals (one proposal per run in the sweep, where every proposal is executed). Outside (NF)∧(NI) this scaled one-step gain has no guaranteed sign relation to the campaign gain; it is a declared gate quantity, not an estimate of it." |
| P11 | **B** | setup.tex l. 30 | "All non-default arms use the same decision rules (Proposition 1) and differ only in the forecast." This is false for A6 (a learned execute-or-skip head) and for A1 (no rule layer, KG verify per D23/R1-A1-VERIFY). A2 also differs from A1 by the rule layer, which is a decision override, not a forecast. | A false methods statement. | "A1–A5 use the closed-form rules of Proposition 1 (A2 and later add the rule layer; A1 keeps KG verification) and differ only in the forecast; A6 replaces the screening rule by a learned action head." |
| P12 | **B** | problem.tex l. 27 and l. 47 vs setup.tex l. 17 | DAC mapping clash. With "instance = node", "audited … on **held-out instances**" (the primary estimand) and "learned on training nodes and **evaluated on held-out nodes**" describe LONO. But the primary estimand in TECH_ROUTE/C3_DESIGN uses held-out *campaign* instances, and the C3 gate is judged on the `instance` (campaign-seed) split, with LONO reported without a verdict (`offline_eval.py:52–60`). | Inconsistent across sections and with the design. | problem.tex l. 27: "…on held-out campaigns…". l. 47: "A configuration policy is learned on training campaigns and evaluated on held-out campaigns of the same nodes (primary) and on held-out nodes (transfer), as in contextual DAC benchmarks." |
| P13 | **B** | setup.tex l. 17 | "Each node has 18 campaigns, one per start seed … run under two memory modes". The sweep has 18 instances **per node per memory mode** (`dataset.sweep_sources`: one manifest per mode, nodes × instances ledgers each), i.e. 36 campaigns per node. All campaigns share the start configuration; the seed is the campaign seed. | It misstates the data size by a factor of 2. | "Each node has 18 campaign seeds, each run under both memory modes (36 campaigns per node, $W=20$ worker runs each)." |
| P14 | m | problem.tex l. 45 vs setup.tex l. 35 | The per-instance level is defined as "a function of node descriptors only", but A1 (fitted on the node's own labelled campaigns) is listed as per-instance. | Inconsistent taxonomy. | problem.tex: "…set once per instance, either fitted on that instance's own campaigns or predicted from its descriptors…". |
| P15 | m | theory.tex l. 72 | "probe value α = 1". α is the probe's **scale** (Δ₁ = αθ); its immediate value is αφ(0) ≈ 0.40 < g. The setting (N = 2, fixed proposals, non-interacting edits) is not given. | Clarity of the numbers. | "With probe scale $\alpha=1$ (immediate value $\alpha\phi(0)\approx0.40<g=0.5$), later-edit scale $\beta$ and noise $\kappa\beta$, $\kappa=1$, the exact optimality gap grows linearly in $\beta$ with slope $\phi(0)(1-1/\sqrt2)\approx0.117$ ($N=2$, fixed non-interacting proposals; bounded if $\kappa=0$)." |
| P16 | m | theory.tex l. 19; l. 56 | "the immediate gain over always executing" / "its gain over always executing" leave out the keep rule of the comparator (T4: "always execute, keep by 8′.1"). | Precision. | Add "(and keeping by (i))". |
| P17 | m | theory.tex l. 54 | "the forecast depends on the history only through the proposals" is vague. T4 part 1 states it for both m_n and V*_n. | Precision. | "$m_n=\mathbb{E}[\Delta_n\mid x_{1:n},H_n]$ and $V^*_n=\mathbb{E}[m_n^+\mid x_{1:n}]$." |
| P18 | m | theory.tex l. 27 | The Gaussian keep rule holds on $\{H_n\ne0\}$ (on $\{H_n=0\}$ every k has value 0), and it needs a continuous comparison law on $I_n^c$. | Matches T4 §1 exactly. | Append "on $\{H_n\neq0\}$; on $\{H_n=0\}$ every keep decision has value 0". |
| P19 | m | theory.tex l. 33 (bias) | It states $\varrho_n<1$ and omits $\xi_n\perp(\mathcal F_n,e,\Delta_n)$ and $\sigma_{c,n}=\sigma\sqrt{1-\varrho_n^2}>0$ (T4 Prop 9: $\varrho_n\in[0,1)$). The TBD covers part of this. This mathematical result also sits outside any theorem environment. | Precision; the result cannot be referenced. | Put it in a `proposition` environment with $\varrho_n\in[0,1)$, $\sigma_{c,n}>0$ and $\xi_n$ independent of $(\mathcal F_n,e,\Delta_n)$. Add: "this noise model is not the independent-noise model of Proposition 1's closed form" (T4 R1). |
| P20 | m | setup.tex l. 52 | "cluster bootstrap over campaigns": the code clusters by `instance` = node × seed, which pools a seed's two memory-mode campaigns. | Accuracy. | "over campaign seeds (a seed's campaigns in both memory modes form one cluster)". |
| P21 | m | setup.tex l. 10–12 | The qualification rule is vague ("non-trivial rate"). The D21 rule is a mean default-rule error rate ≥ 10 % on material edits with a minimum edit count (`e1_report.py:32, 142`), using joint-seed noise, not "training-seed or split-seed". "Left no headroom" as the cause of the D28 failures is not in the facts given (they failed D21). σ_node is the median joint-seed SD *of the paired difference* (`e1b_collect.node_noise`). "Pre-registered reserve" is stronger than "pre-declared". The two other screened candidates (credit-g, qsar-biodeg) are not mentioned. | Factual precision and transparency. | "A node qualifies if the default keep rule errs on at least 10 % of material edits (D21)… σ_node is the median joint-seed SD of the paired difference over material edits… Four candidate nodes failed this rule; after a pre-declared start-configuration repair three qualified, and the fourth was replaced by a pre-declared reserve node." Add a sentence or TBD on all screened candidates. |
| P22 | m | setup.tex l. 20 | "Non-inert, non-duplicate proposals are audited". If any stratum is subsampled (the code supports random audits with inverse-probability weights, `offline_eval.py:45–50`), say so. | Accuracy of the estimand. | Add "all" or "a random sample, weighted by inverse sampling probability". |
| P23 | m | setup.tex l. 15, 41, 43 | No citations for Qwen2.5-Coder, Qwen3.5, llama.cpp, TabPFN (Hollmann et al. 2025), Kev, LightGBM or OpenML. Also: if Kev is released by, or affiliated with, the authors, naming it may break anonymity. Its provenance is not visible in the repository (only `kev` package code). | Completeness; possible anonymity risk. | Add the citations. Confirm that Kev is a public third-party release, or anonymise it. |
| P24 | m | setup.tex l. 52 | "C3 gate", "index policy" and "practical threshold" are internal terms, undefined in the paper. | Readability. | Rename to "offline gate"; define δ_n (D18) where it first appears; define "index policy" or drop the name. |
| P25 | m | problem.tex l. 10 vs theory.tex l. 40 | Notation clash: $W$ is the run budget, and $W_n$ is the exogenous tuple. | Readability. | Rename the exogenous tuple $\omega_n$ (or $Z_n$). |
| P26 | m | problem.tex l. 13 | "comparison noise with node-level scale σ_node", but the rules use the per-comparison σ_n (σ_cmp in code). σ_node only standardises. | Consistency with theory and code. | "…with per-comparison scale $\sigma_n$; increments are standardised by the node-level $\sigma_{\mathrm{node}}$." |
| P27 | m | theory.tex l. 60; appendix.tex | "proof in the appendix", but the appendix holds TBDs named in **T4 numbering** ("Proposition 6…10"), while the manuscript has Proposition 1, Theorem 1 and Proposition 2. | Cross-reference mismatch. | Rename the appendix TBDs with `\ref{prop:onestep}`, `\ref{thm:reduction}`, `\ref{prop:failures}`. |
| P28 | m | main.tex l. 4–6 | Separate counters give "Proposition 1, Theorem 1, Proposition 2". The ICML template convention is a shared counter. | LaTeX quality. | `\theoremstyle{plain}\newtheorem{theorem}{Theorem}[section]\newtheorem{proposition}[theorem]{Proposition}` (add `lemma` or `corollary` the same way if P19 is adopted). |
| P29 | m | setup.tex l. 15 | "JSON-schema-constrained decoding" is visible in `r1/exam` (`manager_response_format()['json_schema']`). It is not confirmed here for the sweep-1 manager path. | Unverified fact. | Confirm from the sweep-1 manifest, or mark TBD. |
| P30 | m | problem.tex l. 27 | "relaxation of the hard budget $\sum_n a_n\le W$". T4 states the expectation constraint $\mathbb{E}[\sum a_n]\le W$ for weak duality. | Precision. | "…the Lagrangian relaxation of the budget constraint $\mathbb{E}[\sum_n a_n]\le W$". |
| P31 | m | theory.tex l. 75 | The scope paragraph should also cover freed runs that are re-spent (T4 R2: "or with freed runs re-spent"). Optionally note R6: offline evaluation of skipping is optimistic for a Bayes controller under (NF), and its sign is undetermined for learned forecasters. | Completeness of scope. | Add "or when freed runs are re-spent". Optionally add R6 to the setup's offline-gate paragraph. |

---

## Summary of blocking items

- **NI code (N1–N3):**
  - rename the flag and correct the reading; it is not evidence against NI as built;
  - score RPS on the evaluation-half label (7006–7010), and add the recurring-pair grouping row;
  - document the retained result-dependent features;
  - add the realistic-null and shared-label-noise tests.
- **A1-ctx note (A1–A3):** the name-based rule layer in `offline_eval.py:362`; a false neutral prompt line; the memory line removed although the note calls it a campaign setting.
- **Manuscript (P1–P13):**
  - (NF) components stated as sufficient, with the full (NF-c);
  - the contrapositive (Bayes; necessary, not sufficient; not RL);
  - the masking implication (Bayes, whole x_{1:n}, (NF) and (NI));
  - checks stated as planned, not reported;
  - r_n outside the closed form;
  - "execution reveals only H_n";
  - the 10(b) (NI) wording;
  - edit-hash grouping not implemented;
  - soft-label width differs between Track P and the gate arms;
  - the R4 sign caveat and proposals vs runs;
  - the false "same decision rules" sentence;
  - held-out instances vs held-out nodes;
  - 18 seeds × 2 memory modes.
- **TabPFN:** nothing blocking.

---

## Re-review

Re-review of the revised deliverables at the same paths (28 Oct 2026). AI-assisted (Claude), independent of the authoring session. No file under review was edited.

**What was run.**
- `python3 -m pytest -q r1/tests/test_c3_ni_masking.py r1/tests/test_c3_arms_eval.py`: **20 passed** (11.3 s).
- `latexmk -pdf` on a fresh copy: **7 pages**, 0 LaTeX or BibTeX warnings, no undefined references or citations, no overfull boxes. There are 10 underfull hboxes, 5 of them in the setup's gate paragraph (cosmetic).
- Fetched `huggingface.co/jaredpalmer/kev-0.8b` (Kev citation) and `huggingface.co/Prior-Labs/TabPFN-v2-reg/blob/main/LICENSE.txt` (TabPFN T4).
- Checked the wheel README (`METADATA` lines 158–164).
- `grep` for every rule-layer decision in `r1/c3/`.

### Verdicts

| # | Deliverable | Verdict |
|---|---|---|
| 1 | NI code + tests | **ACCEPTED** (minor notes R-N1–R-N3, non-blocking) |
| 2 | A1-ctx note | **NOT ACCEPTED**: one remaining blocking item (R-A1), a one-line addition to the code plan |
| 3 | TabPFN proposal | **ACCEPTED** (minor notes R-T1–R-T2) |
| 4 | Manuscript | **ACCEPTED** (all blocking items resolved; minor items R-P1–R-P8; R-P1 is a newly introduced undefined symbol and should be fixed in the next pass) |

### 1. NI code: resolution of N1–N9

| Finding | Status | Evidence |
|---|---|---|
| N1 | Resolved | The flag is `results_add_predictive_value`. `READING` and the docstring carry the corrected reading: summary-sufficiency caveat, undetermined bias direction, (NF-b) channel. The end-to-end test asserts `evidence_against_NI` is absent from the output. |
| N2 | Resolved | `with_eval_soft` builds `soft_eval` from `split_audit(a)[1]` (7006–7010), with the same width rule. `run_test` refuses to run without it, scores against it by default and records `scored_against`. The new `pair_grouped` mode exists. `test_label_half_scoring_flags_shared_label_noise_and_eval_half_does_not` demonstrates the artefact and its removal. |
| N3 | Resolved | `DIRECT_OUTCOME_FEATURES` / `RETAINED_INCUMBENT_DEPENDENT` / `RETAINED_VALIDITY_DEPENDENT` match my lists exactly, are asserted to exist and to be disjoint from the masked set, and are written to every output block. |
| N4 | Resolved | `primary_reading` is in the output; the docstring states that per-node blocks are descriptive. |
| N5 | Resolved | New tests: 10-seed null (≤ 2 flags); masked features as deterministic functions of retained ones (`last_key_delta_z = f(key_code)`, `keeps_so_far = f(budget_index)`); recurring pairs; pair-fold invariant; eval-half seeds; `main()` end to end. |
| N6 | Resolved | `main()` calls `OE.table_noise` and reports `noise_source`. |
| N7 | Resolved | `PRIMARY_SIGMA_MODE = "se_audit"`, and `sigma_mode_role` is in the output. |
| N8 | Not verifiable here | The snapshot holds only `r1/`. The coordinator states the file is on main. |
| N9 | Resolved | `_summary` always returns `n_instances`. |

No new errors found: weights, eval mask, signs, clusters and seed roles are unchanged and correct.

Minor notes (non-blocking):
- **R-N1 (`pair_grouped_folds` diagnostics).** On real tables every campaign of a node starts from the same start configuration, so early (candidate, incumbent) pairs probably recur and link all of a node's campaigns into one component. The greedy fold assignment would then hold out whole nodes, making `pair_grouped` a leave-nodes-out transfer test rather than a leakage check. Fix: write the number of components, the largest component's row share and the per-fold node composition to the output. If a node collapses into a single component, label the `pair_grouped` block "degenerate: equivalent to node hold-out".
- **R-N2 (wording).** `READING` says "evidence against (NF) and (NI)". The docstring's "(NF) ∧ (NI)" is the intended meaning. Use "against the conjunction (NF) ∧ (NI)" in `READING` too.
- **R-N3 (citation path).** The docstring cites `docs/r1/reviews/MAC_LOCAL_DELIVERABLES_REVIEW_20261028.md`, but this review is at `outputs/c3prep/REVIEW_MAC_LOCAL_DELIVERABLES_20261028.md`. Commit it under the cited name, or change the citation. The same applies to the A1-ctx note and the TabPFN proposal.

### 2. A1-ctx note: resolution of A1–A14

| Finding | Status |
|---|---|
| A1 | **Partly resolved.** See R-A1. The offline path (`offline_eval.py:362` → `NO_RULE_ARMS`) and test 3(c) are in the code plan, but the online path is not. |
| A2 | Resolved. The neutral line now says only the history changes and the recorded gain are in z. |
| A3 | Resolved. The `Memory:` line stays byte-identical. |
| A4–A5 | Resolved. The node name is listed. Path and keys reveal the family; the raw metric and config values can identify the node; option (b) drops the raw metric. |
| A6 | Resolved. `n_classes` is dropped; zero-variance columns are set to 0; descriptors are clipped; p̄ is floored; ∞ is implemented as B = 0. |
| A7 | Resolved. p̄ and the standardisation are refitted inside every inner fold. |
| A8 | Resolved. The 1-SE rule toward λ = ∞ is used, and the test uses identical label laws. |
| A9 | Resolved. Terminology paragraph added; "constant across the campaigns of a node". |
| A10 | Resolved. Two training seeds per template, plus the main run's seed spread. |
| A11 | Resolved. `node_lines_ctxoff()` is added, and the cache is tagged by prompt version. |
| A12 | Resolved by citation (`docs/r1/reports/TRACKP_P0_SPIKES_20261026.md`; not in this snapshot, so not verified). |
| A13 | Resolved. Open item 4: confirm climate's descriptors. |
| A14 | Raised for the Track P owner. |

- **R-A1 [B]: rule layer by name in the online path.** `r1/c3/prior_model.py:120` sets `TableArmPrior.rule_layer = self.name != "A1"`. `control.py:141` reads `prior.rule_layer` for online decisions, and `control.py:305` then force-skips no-ops and duplicates. The note says A1-ctx runs "in the online pilot if A1 runs there", so online it would silently receive the rule layer: the defect of A1 again, in the second location. Exact fix: add to code plan item 2 "and `prior_model.py:120` → `self.rule_layer = self.name not in NO_RULE_ARMS` (one shared constant, imported from `offline_eval` or `arms`)". Add `"A1-ctx": ContextPrior` to `prior_model.ARM_CLASSES`. Extend `arm_digest` (it assumes either an LGBM model or `pooled`/`by_node`) to cover `ContextPrior`. Extend test 3(c) to the online `TableArmPrior` path.

### 3. TabPFN proposal: resolution of T1–T9

T1, T2, T3 and T5–T9 are resolved as specified; the scale row, gating row, settings row, design-point section and author steps were all checked against the wheel.

T4 is handled correctly as an explicit author step (step 3), since the text could not be fetched in the authoring session.

Minor notes:
- **R-T1 (the v2 licence file is `LICENSE.txt` and is retrievable).** The wheel README (`METADATA:164`) names `huggingface.co/Prior-Labs/TabPFN-v2-reg/blob/main/LICENSE.txt`; the authoring session tried `LICENSE`. I fetched it. §10 "Additional attribution" requires three things whenever you distribute or make available the Work, any Derivative Work, or a product containing the weights:
  - (A) provide a copy of the licence;
  - (B) prominently display "Built with PriorLabs-TabPFN" on each related website, UI, blog post, about page or product documentation;
  - name any distributed model created, trained, fine-tuned or distilled from the weights or outputs so that it begins with "TabPFN".

  Internal benchmarking and testing without external communication is exempt. The fix: replace step 3 with these three obligations, have the author confirm the text, and note in option B/C that releasing a fine-tuned v2 model requires a "TabPFN…" name and the attribution line.
- **R-T2.** Option B says "Apache-2.0-based licence … reproducible by anyone". Add "with the §10 attribution and naming obligations" so the claim is complete.

### 4. Manuscript: resolution of P1–P31

All blocking findings are resolved:
- **P1:** sufficient-not-necessary wording, full (NF-c), joint noise law.
- **P2:** Bayes one-step; necessary, not sufficient; not RL.
- **P3:** (NF) and (NI); Bayes; whole x_{1:n}; the less-history caveat.
- **P4:** "We plan corresponding checks" + TBD; keep-channel caveat; the setup's checks are now a TBD.
- **P5:** "for r_n = 0"; verification lies outside.
- **P6:** problem.tex and the theorem preamble.
- **P7:** "(NI) holding under each policy's law".
- **P8:** the folds as the code builds them + TBD for pair grouping.
- **P9:** both widths stated + TBD.
- **P10:** 20 logged proposals, the no-sign-relation sentence, plus R6.
- **P11:** the corrected arms sentence.
- **P12:** held-out campaigns primary, nodes for transfer.
- **P13:** 18 seeds × 2 modes = 36 campaigns.

The minor findings are resolved or explicitly deferred by TBD:
- **Resolved:** P14–P20; P23 (citations added, Kev verified as a public Apache-2.0 third-party release); P24–P28; P30; P31.
- **P21:** mostly resolved (see R-P3).
- **P22, P29:** explicit TBDs.

The 10(c) paragraph matches T4: N = 2, scale α, immediate value αφ(0) ≈ 0.40 < g, slope 0.117, bounded at κ = 0. δ_n matches `dataset.py:83` (D18). The shared theorem counter works.

Remaining minor items (non-blocking):

| ID | Location | Finding | Exact fix |
|---|---|---|---|
| R-P1 | theory.tex l. 32 (Prop. `prop:bias`) | **New:** $\mathcal{F}_n$ is undefined in the manuscript; only $\mathcal{O}_n$ is defined in problem.tex. | Add "where $\mathcal{F}_n\supseteq\mathcal{O}_n$ is the full ledger history before trial $n$ (all earlier proposals, decisions and recorded metrics)", or restate with $\mathcal{O}_n$ if the proof check allows it. |
| R-P2 | setup.tex l. 65 (R6 sentence) | T4 R6 is for a Bayes **myopic** controller, and the bias is **zero under (NI)**. Both qualifiers are missing. | "…optimistic for a Bayes myopic controller under (NF), and unbiased under (NI)…". |
| R-P3 | setup.tex l. 13, l. 15 | (a) D21 is a **mean error probability** of the default rule ≥ 10 % over material edits (`e1_report.py:32, 142`), not a share of edits. (b) "failed a pre-collection liveness check because their start configuration left no headroom" adds a cause. The D28 liveness criteria are a keep after trial 1, ≥ 50 % novel active configurations and < 30 % invalid (`r1/liveness/__init__.py`). | (a) "if the default keep rule's mean error rate over its material edits is at least 10 %". (b) Name the criterion actually failed (e.g. "no keep after trial 1"), or drop the "because" clause. |
| R-P4 | setup.tex l. 28–30 (merged seed sentence) | "the last five … are also used for task-level joint-seed retraining in the audit" suggests that only the evaluation half retrains the task, but every audit seed is a task retraining run. "An earlier engineering pilot used seeds 7001–7006 on other proposals" is an internal detail that will puzzle readers. | "…give the evaluation value (each audit seed retrains the task on fresh joint seeds)". Move the pilot sentence to the reproducibility appendix, or drop it. |
| R-P5 | setup.tex l. 35 | "for the tabular arms it is the audit standard error" also covers TabPFN, which regresses a scalar and has no soft-label width (TabPFN proposal, design point). | "for A1–A3 it is the audit standard error; TabPFN regresses the label-half z directly \TBD{R1-TABPFN width point}". |
| R-P6 | refs, `kev2026` | The title "Kev: Small Decision Models" is not the card's. The card recommends "Kev-0.8B: a calibrated decision model on Qwen3.5-0.8B" (Palmer, 2026), with its own BibTeX; first published 2026-09-24. | Use the card's BibTeX entry. Add the Kev-4B card URL if 4B is cited. |
| R-P7 | setup.tex l. 67 | Five underfull hboxes (badness up to 10000) from the inline δ_n formula in a narrow column. | Set δ_n as a short display, or move the formula to a footnote. |
| R-P8 | setup.tex l. 30 | "The evaluation seeds are excluded from every decision-model training, tuning or selection step" states as fact a boundary whose loader guard is still TBD. | "…are to be excluded…; the loader guard that enforces this is \TBD{…}", or keep the sentence once the guard is merged. |

### Summary

- **NI code:** accepted.
- **TabPFN proposal:** accepted. Optionally replace author step 3 with the §10 text quoted in R-T1.
- **Manuscript:** accepted. Fix R-P1 (a newly introduced undefined $\mathcal{F}_n$) in the next pass.
- **A1-ctx note:** not accepted until the code plan also changes `prior_model.py:120` (the online rule-layer-by-name path), covers it in `ARM_CLASSES`/`arm_digest` and extends test 3(c). Nothing else is outstanding.

---

## Final check

Final acceptance check of the post-re-review fixes (28 Oct 2026). AI-assisted (Claude), independent. No file under review was edited.

**What was run.**
- `pytest r1/tests/test_c3_ni_masking.py r1/tests/test_c3_arms_eval.py`: **20 passed**.
- Fresh `latexmk -pdf`: **7 pages**, 0 warnings, 0 overfull boxes, no undefined references.
- No anonymity strings found in the PDF text.

| # | Deliverable | Verdict |
|---|---|---|
| 1 | NI code + tests | **ACCEPTED** |
| 2 | A1-ctx note | **ACCEPTED** |
| 3 | TabPFN proposal | **ACCEPTED** |
| 4 | Manuscript | **ACCEPTED** |

How each re-review item was resolved:
- **R-A1 (blocking):** resolved. Code plan item 2 defines one `NO_RULE_ARMS = frozenset({"A1", "A1-ctx"})` in `arms.py`. It changes both `offline_eval.py:362` and `prior_model.py:120`, citing `control.py:141/305`. It adds `"A1-ctx": ContextPrior` to `ARM_CLASSES` and extends `arm_digest` (λ, B, p̄, standardisation). Test 3(c) covers both the offline and online paths (`TableArmPrior("A1-ctx").rule_layer is False`; a `RuleController` does not force-skip a duplicate).
- **R-N1:** resolved. `fold_diagnostics` (folds, fold row counts, largest fold share, campaigns, folds per node, `degenerate`) is written for `pair_grouped`, and the test covers both the non-degenerate and the fully linked case.
- **R-N2:** resolved ("the conjunction (NF) ∧ (NI)" in both the docstring and `READING`).
- **R-N3:** resolved by committing the review at the cited path.
- **R-T1/R-T2:** resolved. §10 is in the facts table, option B and author step 3.
- **R-P1:** resolved. $\mathcal{O}_n$ replaces $\mathcal{F}_n$.
- **R-P2:** resolved.
- **R-P3:** resolved. The D21 wording is now the mean wrong-decision probability. The liveness clause matches liveness criterion 1 in `r1/liveness/__init__.py`; I did not read PLAN R1-D28-REPAIR.
- **R-P4:** resolved. Every audit seed is a task retraining, and the pilot sentence is gone.
- **R-P5:** resolved. A1–A3 use the audit SE, and TabPFN has its own TBD.
- **R-P6:** resolved. The Kev title matches the card.
- **R-P7:** resolved. δ_n is a display, and the gate paragraph's underfull boxes are gone.
- **R-P8:** resolved ("are to be excluded" + TBD).

Optional notes (non-blocking; no action needed for acceptance):
- **F1 (manuscript, `prop:bias`).** With $\mathcal{O}_n$ in place of $\mathcal{F}_n$, the statement also needs $\varrho_n$ and $\sigma_{c,n}$ to be $\mathcal{O}_n$-measurable (T4 Prop. 9 has them $\mathcal{F}_n$-measurable). Add "($\varrho_n,\sigma_{c,n}$ $\mathcal{O}_n$-measurable)", or leave it to the author's proof check, which the section TBD already requires.
- **F2 (NI code).** `degenerate` is set only when *every* node falls in one fold. A partial collapse is visible in `folds_per_node` but not flagged. Consider adding `n_nodes_single_fold`.
- **F3 (TabPFN, step 3).** It reads §10 conservatively. Its trigger is distributing or making available the weights, a derivative, or a product containing them; merely reporting v2 results in a paper may not trigger it. The conservative reading is harmless, so keep it unless the author wants to narrow it.
- **F4 (manuscript build).** There are 26 underfull hboxes, now mostly from URLs in the bibliography (cosmetic). A `\sloppy` or `\raggedright` bibliography, or `\usepackage[hyphens]{url}`, would clear most of them.
