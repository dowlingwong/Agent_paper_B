# Memory-on partial-arm DI diagnostic — 19 Oct 2026

AI-assisted by Codex. **PILOT, PARTIAL, not evidence.** File-only analysis of an interrupted arm that never passed its collection gate. No LLM calls, Ollama, GPU, worker runs, retries or resumption.

## Question and verdict

Does changing a recorded E2 decision alter subsequent absolute proposal metrics and terminal audited value, after subtracting an immediate-value proxy and an unchanged-point budget correction? For the preserved memory-on `tabular_mlp` subset the descriptive verdict is **violated in value terms**: the next-one absolute-metric contrast passes the combined distance criterion, and the exploratory value residual is −0.00122155 [−0.00222152, −0.000257005]. The memory-off re-analysis is **undetermined at this sample size**. These are diagnostic classifications under the definitions below, not causal identification of memory feedback, proof against Proposition 10(a), or evidence that A7 improves policy value. Sources: companion tables, memory-on/off “Distances and inference” and “Value residual”; [T4 §6](../theory/T4_FEEDBACK_PROPOSER.md).

## Data and snapshot provenance

The author explicitly authorised this exception for the preserved partial arm in [PLAN §10, 19 Oct](../PLAN.md). Source batch: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/`. Arm output: `agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/`; source ledgers: `r1_e1b_rerun2_A_work/{roots,branches}/`. The [snapshot](../../../results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/SNAPSHOT.md) contains 648 leaf summaries, 54 root summaries, 54 initial-audit summaries, the manifest, all 54 root and 648 branch trial ledgers, and small frozen incumbent anchors. It is 11,986,395 bytes (11.99 decimal MB). Snapshot commit: `d7a9dc3`; numerical input revision is the full hash recorded in the tables. Source-file SHA-256 hashes are in `sha256_manifest.txt`; stored-file hashes are in `stored_sha256_manifest.txt`. The source bytes were checked again after copying, and compressed ledgers were round-trip checked.

The seven failed leaves are all four `openml_breast_w__s235__b004__{continue,verify}__r{1,2}` leaves, plus `openml_ionosphere__s123__b008__continue__r1`, `continue__r2`, and `verify__r2`. All four leaves of each affected point are excluded, including the successful ionosphere verify r1 leaf. This leaves **160 points / 640 branches**: 54 tabular, 53 ionosphere and 53 breast-w points, with 18 instances per node. The exact failure list is in SNAPSHOT.md and the generated exclusion table. No failed leaf is repaired or substituted.

Memory is `append_only_summary`, D25 active-key filtering and D26 sampling seeds apply, the model is pinned qwen2.5-coder:7b at temperature 0.2, and the historical verify split is **fixed**. The later decision to use vary does not change these data. The frozen verify response can promote or demote. `digits_mlp` was excluded by its historical liveness result. Source: snapshot `manifest.json`; [STOP diagnosis](RERUN2_STOP_DIAGNOSIS_20261019.md), “Batch layout” and “Interpretation and recommendation”.

The memory-off comparator is the existing complete `E1b_20261013T151857Z` pilot, with 36 points / 144 branches, digits and ionosphere, six instances per node, and memory `none`. The PARTIAL label applies to the memory-on arm; both datasets remain PILOT and not evidence. Inputs are immutable Git blobs, including losslessly decompressed ledgers; the analyzer does not import or run the harness.

## Decisions changed

Counts below are **unique points**, with repetitions averaged before inference. Parentheses give point-repetition counts. Repeated continuations agree on the decision direction at every retained point.

| Dataset / node | Promotions | Demotions | Unchanged | Changed instances |
|---|---:|---:|---:|---:|
| Memory on / tabular_mlp | 9 (18) | 4 (8) | 41 (82) | 9 |
| Memory on / openml_ionosphere | 0 | 0 | 53 (106) | 0 |
| Memory on / openml_breast_w | 0 | 0 | 53 (106) | 0 |
| Memory off / digits_mlp | 6 (12) | 0 | 12 (24) | 4 |
| Memory off / openml_ionosphere | 0 | 0 | 18 (36) | 0 |

Source: generated “Decisions changed” and “Decision audit”. The value-eligible pool contains only tabular for memory on and only digits for memory off. Pool rows repeat those node estimates; they do not increase sample size. Zero changes on the OpenML nodes under this fixed-split response provide no changed-point DI comparison.

## Measures: why absolute metric

The primary outcome is the mean parsed `val_score` or `val_auc` over the next **k = 1 or 3 evaluated trials**, not delta relative to a branch-specific record. Unevaluated invalid proposals do not count toward k or change the replayed configuration. All retained branches have at least three evaluated post-point trials. Branch prefixes are checked against the root, configuration replay is anchored to the copied frozen incumbent, and the verify original decision must equal continue's decision. The primary comparisons follow the existing report: D_changed is mean paired cross-action absolute distance at changed points; D_null is the same-action repetition distance paired at those same points; D_unchanged is the cross-action distance at unchanged points. Signed differences are also retained in the JSON. See [the record-reference addendum](DI_TEST_E1B_20261019.md#addendum-19-oct-2026--record-reference-effect-coordinating-session-review-ai-assisted-by-claude).

Permutation reassigns changed labels across whole points within node; bootstrap resamples instances within node and carries their points together. Both use 9,999 draws and seed 20261019. A primary comparison must have both excesses positive, both one-sided p values below .05, both 95% interval lower bounds above zero, and Holm-adjusted max(p_null, p_unchanged) below .05. Holm includes both horizons for the evaluable node and its pooled duplicate: four comparisons per dataset, conservatively retaining the duplicate. Mechanism measures are exploratory. Permutation exchangeability is an assumption, not randomized identification.

For the value check, Y is mean terminal leaf audit metric, with common audit seeds within a point (collector `r1/headroom/e1b_collect.py`, `run_leaf`, uses `AUDIT_SEED_BASE + i` for every leaf). The paired difference is averaged over repetitions. Immediate value is +D̄ for a promotion and −D̄ for a demotion, where D̄ uses r = 2 verify pairs and is a **noisy proxy**. Budget correction is the mean unchanged-point Y_verify − Y_continue at the same node and budget index, requiring at least two distinct control instances; otherwise use all unchanged points of that node. Residual = paired audit difference − immediate proxy − budget correction. The instance bootstrap recomputes the control correction in each draw, propagating its uncertainty. It does not separately resample audit seeds or estimate the unobserved error of D̄.

This residual targets the continuation-value question in T4 Proposition 10(a), but terminal audited value under a hard run budget and this proxy subtraction are not a direct observation of the proposition's fixed-horizon optimal continuation value. Nonrandom changed-point selection and imperfect budget correction can also produce a residual. No equivalence margin was specified; failure to reject is classified as undetermined, never as proof that DI approximately holds.

## Results

### Absolute-metric contrasts

The table reports excesses in metric units with instance-cluster 95% intervals. Full per-node distances and secondary results are in [the companion tables](DI_TEST_MEMORY_ON_PARTIAL_20261019_tables.md).

| Dataset / node / k | D_changed / paired D_null / D_unchanged | Excess over paired null [95% CI] | Excess over unchanged [95% CI] | Holm p; combined criterion |
|---|---|---|---|---|
| On / tabular / 1 | .00231346 / .00108462 / .000549390 | .00122885 [.000319434, .00237500] | .00176407 [.000438745, .00332095] | .0036; met |
| On / tabular / 3 | .00167949 / .00129231 / .000270224 | .000387179 [−.0000270833, .00112963] | .00140926 [.000594189, .00223392] | .0008; not met |
| Off / digits / 1 | .00603550 / .00464250 / .00197308 | .00139300 [−.00185667, .00348213] | .00406242 [.00126086, .00689974] | .4796; not met |
| Off / digits / 3 | .00441050 / .00332711 / .00127667 | .00108339 [−.00185722, .00336617] | .00313383 [.0000772639, .00625210] | .4796; not met |

The memory-on next-three comparison fails the paired-null interval requirement despite its small permutation p value. The next-one signed verify-minus-continue mean is −0.000473077; next-three is −0.00102372. These distances therefore do not imply a benefit from verification.

### Record shift and value residual

Before the first post-point trial, changed-point recorded incumbent verify − continue is −0.000782692 for memory-on tabular and −0.005107 for memory-off digits; unchanged-point shift is zero on every node. Record shift is descriptive and is never a primary outcome. Source: generated “record_shift”.

| Dataset / eligible node | Audit difference | Immediate proxy | Budget correction | Residual [95% CI] |
|---|---:|---:|---:|---|
| On / tabular | −.000254647 | .000827885 | .000139019 | **−.00122155 [−.00222152, −.000257005]** |
| Off / digits | .00282425 | .00232142 | −.00000773611 | .000510569 [−.00258821, .00417810] |

There are 9,999 valid memory-on value-bootstrap draws and 9,987 memory-off draws; draws without an estimable changed/control contrast are omitted. The negative tabular residual means terminal value is lower than the immediate-proxy-plus-budget-correction prediction on these selected points. It does not isolate the memory channel or establish the optimal policy.

### Mechanism and ionosphere liveness

At all 26 changed tabular point-repetitions, the memory text shown before the first post-point evaluated trial differs between actions; it differs at none of the 82 unchanged pairs. The next proposal exactly repeats the changed edit in 7/26 continue branches and 1/26 verify branches; neither action exactly reverses it (0/26 each). “Repeat” requires the same key, old value and new value; “reverse” exchanges old and new. All first post-point trials in the copied memory-on branch ledgers have parsed metrics, so first evaluated and first attempted trials coincide here. Source: generated “mechanism”; ledger `extra.manager.worker_memory_context_text` and `structured_edit`.

At next three, tabular edited-key TV is .384615 at changed points, .256410 for paired null and .0609756 at unchanged points; excess-null interval [.0128205, .266667]. Active-novelty and duplicate contrasts also exceed both baselines descriptively, while signed-log-edit-size excess over null has an interval containing zero. These secondary results support an observable proposal change, but are unadjusted and include incumbent configuration as well as memory effects. Source: generated tabular secondary rows.

Ionosphere is **no longer metric-degenerate in the observed continuations**: its next-three metric-identical fraction is 1/6 (.166667), versus 1 in memory off (equal branch weight, delta exactly zero at recorded precision). This does not create changed decisions: fixed-split verify still changes none. Source: generated “Metric-identical fraction”.

## Memory-off re-analysis and side-by-side comparison

The absolute-metric re-analysis supersedes the old delta-based DI verdict for interpretation: digits has no primary combined rejection and its value-residual interval contains zero. Thus the memory-off verdict is **undetermined at this sample size**, consistent with the 19 Oct record-reference addendum. The historical report and default script outputs are preserved.

The shared node is **openml_ionosphere**. A node-matched descriptive comparison is possible, but neither dataset has changed points there, so a node-matched decision-dependence or value-residual contrast is unavailable.

| Ionosphere, next three | Memory on | Memory off |
|---|---:|---:|
| Retained points / instances | 53 / 18 | 18 / 6 |
| Changed points | 0 | 0 |
| D_unchanged | .000321280 | 0 |
| D_null over all points | .00153825 | 0 |
| Metric-identical fraction | .166667 | 1 |

The eligible tabular-versus-digits comparison is not node matched. Differences in node, D25 filtering, sampling seeds, initial configurations and memory prevent attribution of the cross-dataset difference to memory alone. Sources: manifests and generated node rows.

## Limitations

This is a **partial, interrupted arm**, never accepted by its collection gate; exclusion of failed points can select the sample. It uses the historical **fixed split**. Changed points are selected by verify outcome, **not randomized**. There are only 13 changed points in nine memory-on instances and six in four memory-off instances. **D̄ is a noisy r = 2 proxy** selected by the same verification outcome used to define changes; the cluster interval cannot remove that selection bias. There are **no proposal-level audits**; the terminal leaf audits do not identify the true quality of each subsequent proposal. The budget correction transfers an unchanged-point average to changed points, and the fallback threshold is an analyst definition. Common audit seeds reduce within-pair noise but do not create independent instances. Memory text changes together with incumbent configuration/value, so the memory mechanism is not isolated. All primary criteria and residual interpretations remain exploratory, not preregistered evidence.

## Deviations from the prompt

1. Raw trial ledgers alone occupy 51,833,959 bytes, exceeding 40 MB even after dropping event extracts. Every ledger is preserved losslessly as `.jsonl.gz`; event extracts are omitted. Raw source hashes and stored hashes are both retained. Memory text and LLM seed/latency already exist in the trial ledger. No large artifact was committed.
2. `memory_context_built` events contain metadata, not the displayed text. The text comes from `extra.manager.worker_memory_context_text`, as established in the STOP diagnosis.
3. The incomplete layout has no `points.json`. Points are derived from all leaf metadata and manifest noise, with failed/missing four-leaf groups excluded. Small frozen incumbent manifests/files were copied as additional anchors. Because event extracts are omitted, the new loader uses root-prefix, snapshot and original-decision checks rather than requiring a branch-commit event; the legacy path retains its original event check.
4. Unevaluated invalid proposals are skipped before replay and horizon selection. There are 44 such post-point records across all copied branch ledgers, including excluded leaves. No metrics are invented. A regression test covers a stale rejected proposal.
5. “Too few” controls is defined as fewer than two distinct instances at the node/budget index. Budget correction is re-estimated in every bootstrap draw. Holm includes the two pooled duplicate comparisons conservatively, yielding four evaluable tests per dataset.
6. “Approximately holds” requires an equivalence criterion not supplied here. The implementation returns undetermined when the combined positive-distance criterion and a nonzero value-residual interval are not both present in the same eligible group. A nonzero residual alone does not trigger the violated verdict.

## Verdict for C4 / A7 and validation

**C4:** the memory-on tabular diagnostic is **violated in value terms** under the stated exploratory rule; memory off remains undetermined. Keep the continuation-value question open for a controlled, proposal-audited design. **A7:** these partial observational results do not justify training, deployment, or a claim of policy-value improvement. No such work was performed.

The focused file-only suite passes **12 tests**, including pure record shift (legacy delta rejects, absolute metric does not), a true proposal shift (absolute metric detects it), whole-point failure exclusion, immutable compressed Git inputs, budget-correction fallback, invalid-proposal handling, and the frozen breast-w active-key exclusion. Old default Markdown and JSON were compared against the pre-change script at the same input revision and are **byte-identical** (Markdown SHA-256 `4bc3157a63b5ccb381ac2eddf663095d09f873ae2fcf0e18793fbede95964531`). An independent direct arithmetic check from the copied raw ledgers agrees with every reported primary distance and value-residual point estimate. All source and stored-file hashes were reverified after analysis. The full harness suite is outside this analysis-only change and was not run. Non-data files pass `git diff --cached --check`; copied raw data, including losslessly compressed JSONL, are exempt from whitespace normalization.

Reproduce each dataset with Python, numpy and pytest in an isolated analysis environment:

```sh
OPENBLAS_NUM_THREADS=1 python -m r1.diagnostics.di_test \
  results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014 \
  --outcome abs_metric --md /tmp/di_on.md --json /tmp/di_on.json
OPENBLAS_NUM_THREADS=1 python -m r1.diagnostics.di_test \
  results/r1/pilot/E1b_20261013T151857Z \
  --outcome abs_metric --md /tmp/di_off.md --json /tmp/di_off.json
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python -m pytest -q r1/tests/test_di_test.py
```

The companion tables concatenate the two generated Markdown reports with heading levels shifted to sit under dataset headings. JSON stays in diagnostic scratch; reproduction records exact input revision and input hashes. A later commit changes revision metadata, not the input blobs or numerical estimates.


## Addendum, 19 Oct 2026 — the "violated in value terms" verdict is withdrawn (coordinating-session review; AI-assisted by Claude)

Two independent checks indicate that the memory-on value residual (−0.00122 [−0.00222, −0.00026]) is the selection bias of the immediate-value proxy, not a decision-dependence effect:
1. **Fresh, selection-free audits** of the 13 changed candidates and their incumbents (C3 offline pilot, `docs/r1/reports/C3_OFFLINE_PILOT_20261019.md` §3; `results/r1/engineering/c3_audit_pilot_20261019T001338Z/di_candidate_audits.json`). The proxy mean immediate value is +0.00083; the audited value is −0.00044. Substituting the audit moves the residual to **+0.00004** (memory-off digits: +0.00051 → −0.00003). The verify direction agreed in sign with the audit at only 7 of 13 points. These are point estimates, without a bootstrap.
2. **Simulation under DI** (`docs/r1/theory/T5_SIMULATION.md`, check 5): with r = 2 and the fixed split, the D̄ proxy alone produces an expected residual of about −0.8 to −1.9 × 10⁻³ at tabular scale.

**Revised verdict:** memory on, undetermined, with no evidence of a value-relevant violation; memory off, undetermined. T5 also shows that only **audited increments over each branch's own incumbent** are free of the record-reference and proxy artefacts (flag rate 0 under DI). Neither Δ̂ nor absolute metrics are. Any future DI test (the C4 memory-on run) must use them. `r1/diagnostics/di_test.py` still needs an audited-outcome mode.
