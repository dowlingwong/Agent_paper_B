# Appendix section draft — "Track S pilot findings" (15 November 2026)

**Status.** Draft for the paper appendix. AI-assisted (Claude, Mac agent), written at the author's request after the
STOP 4 decision (`R1-TRACKS-STOP4-END`, draft row `proposals/PLAN_ROW_R1-TRACKS-STOP4-END_DRAFT_20261115.md`). Not an
author decision.

**Conditions for manuscript use.**
- **Numbers.** Every number below comes from ENGINEERING_ONLY pilot runs. RUNBOOK §1 says such runs are never quoted as
  results. The section therefore presents them as a disclosure of why a planned experiment was stopped, and draws no
  result from them.
- **Theory.** The reading uses Proposition 8′ of `proposals/T4_PROP10_REVISION_20261028.md`. Under `R1-T4-DI-FIX`
  that proposition enters the manuscript only after the author's proof check, which the PLAN does not yet record.
  Until then this section cannot go into the manuscript as written.

**Sources.**
- Two-node S0.5 summary `reports/TRACKS_S05_SUMMARY_20261115.md` (accepted at `74808c0a`), with its scripts and JSON in
  `results/r1/tracks/s05_summary/`.
- Per-node run records `reports/TRACKS_S05_T7_RESULT_20261114.md` and `reports/TRACKS_S05_T7_TABULAR_20261114.md`.
- Operator runbook rev 3.3 (`prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, `13badb0d`).
- T4 (`theory/T4_FEEDBACK_PROPOSER.md`, Proposition 8 and Corollary 8a) and the Proposition 8′ proposal.

Everything from the next heading down is the draft text.

---

## A.x Track S pilot findings

**What was planned.** Track S was a pre-registered screen (`R1-TRACKS-ADOPT`). It would compare a tuned dynamic
execution threshold with the best tuned static threshold, on two CPU nodes (`digits_mlp`, `tabular_mlp`) with a
pinned local manager. The base forecaster was A2-U, a hierarchical normal model per (key, sign) with a predictive
variance, gated by a calibration check before any evidence run (`R1-TRACKS-S02`).

**What happened.** Track S stopped after its pilot (S0.5), before any evidence run, by the author's decision
(`R1-TRACKS-STOP4-END`). It produced no campaign-level result, and the planned evidence phases did not run. The
decision to stop was taken after the pilot data had been seen. It is not one of the outcomes declared in advance
(`R1-TRACKS-FRAMING`).

### A.x.1 Pilot set-up

- **Instances and policies.** 20 pilot instances per node. Each instance was run under two policies:
  - A2-U at the declared run price g = 0.1 σ_node;
  - a static rule: execute iff V\* ≥ 0.3 σ_node, keep iff m̂ > 0.

  In addition, 10 instances per node had a second repetition of the static rule.
- **Budgets.** Pilot campaigns had a cap of 40 LLM calls and a worker budget of W = 40 runs. The prefixes were then
  read at W ∈ {8, 10, 12, 20}.
- **Calibration audits.** Every eligible E1 decision of A2-U received a calibration audit. Its 80 % predictive
  interval was checked against the audited increment: 298 predictions on `digits_mlp`, 330 on `tabular_mlp`.
- **Pins and hosts.** σ_node is the node's noise constant (`R1-C1-FLOOR`): 0.0066 (digits) and 0.0019 (tabular).
  The manager, llama.cpp build, harness and paper code were pinned. Both pilots ran on one host (TASL-7).

### A.x.2 What Proposition 8′ says about a low run price

Proposition 8′ (index theorem; no independence condition) has two parts at every history:
- **E2.** After an execution, keep iff the posterior mean m_n > 0. The best expected keep value is
  V\*_n = E[m_n⁺ | O_n].
- **E1.** Executing pays V\*_n − g and skipping pays 0. So execute iff V\*_n > g. Relative to always executing, the gain
  at that history is (g − V\*_n)⁺.

Call the run price **low** when g lies below V\*_n at every history. Then:
- the E1 rule executes every proposal except those whose V\*_n is 0, namely rule-detectable no-ops and duplicates
  (T4 Corollary 8a);
- the screening gain (g − V\*_n)⁺ is 0 throughout;
- the only decision left that carries value is the E2 keep.

In this regime a forecaster's E1 index cannot change what is executed, however it is built, as long as it stays above
g. A dynamic threshold that moves within that range cannot change it either.

Two limits apply:
- The statement is about one step at a time. A campaign-level statement needs Proposition 10(a′) and its conditions.
- Proposition 8′ uses a fixed price with both actions always feasible. It does not cover a binding hard budget, whose
  shadow price depends on the remaining runs (proposal §5, R2).

### A.x.3 What the pilot shows

In the pilot, the run price was low in the sense above **for A2-U's own index**, on both nodes:

| | `digits_mlp` | `tabular_mlp` |
|---|---|---|
| A2-U's V\* − g over eligible E1 decisions | 2.58–2.61 σ_node | 4.04–4.06 σ_node |
| Range of V\* across all proposals | 0.036 σ_node | 0.018 σ_node |
| Decisions below, or within ±0.5 σ_node of, g or the static threshold | 0 of 298 | 0 of 330 |
| E1 skips per policy, all rule-detected duplicates | 429 | 399 |
| Instances on which the two policies took identical action sequences | 20 of 20 | 20 of 20 |
| … and identical results at each truncation W = 8/10/12/20 | 20 of 20 | 20 of 20 |
| Between-policy sd of the campaign outcome (S0.5b at W = 12; at the cap) | 0; 0 | 0; 0 |
| E2 keep / discard (each policy) | 148 / 170 | 158 / 192 |
| E2 margins m̂ (5th–95th percentile); within ±0.5 σ_node of 0 | −0.108 to 0.114; 46 | −0.055 to 0.034; 38 |

**Interpretation.**
- E1 was trivial: every proposal that was not a duplicate was executed, by both policies.
- E2 was not trivial: m̂ spread widely around 0, and many keep decisions were close to it.
- The two policies differ only on E1, so they produced the same campaigns.

**Budgets.**
- At W = 40, every campaign ended at the 40-call LLM cap. The worker budget was never exhausted (at most 27 of 40
  runs).
- At W = 12, the worker budget bound in 94 % (digits) and 100 % (tabular) of the campaigns.
- Neither pilot policy used the budget state, so the binding budget changed where campaigns stopped, not what they
  decided.

**Why A2-U's index was nearly constant.**
- A2-U's fitted prior set the between-group spread τ0 to its floor (0.15 σ_node) on both nodes. Its rule is
  τ0² = max(τ_A2² − τ_w², floor²), and A2's prior spread τ_A2 was smaller than the estimated within-key spread τ_w.
  τ_A2 comes from A2's binned soft labels, whose bins span a few σ_node: it was 2.9 and 3.4 σ_node. τ_w was 7.5 and
  13 σ_node.
- With τ0 at the floor, the posterior mean barely moves from the prior mean, and the predictive sd is about τ_w.
  V\* is then about 0.4 · τ_w² / √(τ_w² + σ_cmp²) for every proposal, which is far above 0.1 σ_node.

### A.x.4 A2-U failed its calibration gate; no claim is made about A2-U

The pre-declared gate required the 80 % intervals to cover between 70 % and 90 % of audited increments, overall and in
every stratum of the group's history length n_group with at least 20 predictions. A2-U failed it on both nodes:

| n_group stratum | `digits_mlp` (n) | coverage | `tabular_mlp` (n) | coverage |
|---|---|---|---|---|
| 0 | 65 | 0.538 | 57 | 0.368 |
| 1–2 | 89 | 0.674 | 95 | 0.653 |
| ≥ 3 | 144 | 0.944 | 178 | 0.831 |
| overall | 298 | 0.775 | 330 | 0.700 |

- For a group's first proposals, the intervals were too narrow on both nodes. On `digits_mlp` they were too wide for
  groups with three or more earlier results.
- A2-U's V\* values are therefore not validated estimates of the Bayes quantity V\*_n in Proposition 8′.

So we do not claim:
- that E1 screening is trivial for these nodes in truth;
- anything about A2-U as a forecaster or controller beyond the gate failure itself;
- any comparison between dynamic and static thresholds, or any of the outcomes Track S was designed to decide.

What the pilot shows is narrower:
- with this forecaster at this price, the E1 rule did not discriminate between proposals, and so the two policies
  coincided;
- that is the pattern Proposition 8′ predicts whenever the index used for E1 exceeds g at every history.

Offline recalibrations were explored after the pilot (summary §6). They were not pre-declared, are exploratory and
support no statement here.

### A.x.5 Disclosures

- **The stop was decided after seeing the data.** The author chose to end Track S after the pilot data, and its
  summary, had been seen. The alternatives were to revise A2-U and repeat the pilot, or to narrow the comparison to
  E2. No evidence run had started.
- **Host.** `digits_mlp` was planned for TASL-2 and moved to TASL-7 after TASL-2 became unreachable on 12 November
  2026. Its S0.4 rows, which A2-U's prior was fitted from, come from TASL-2. Its S0.5 pilot ran on TASL-7. A
  partial S0.5 attempt on TASL-2 (last seen with 4 committed roots) was preserved and not used.
- **Order.** On the author's instruction, `tabular_mlp`'s determinism check (S0.1) was run after its S0.4 and
  before S0.5.
- **Concurrency.** The number of concurrent manager servers was fixed by measurement at k = 2 on both nodes.
- **Inspection.** All pilot data and their independent reviews are in the repository (see Sources). No pilot
  unit failed, none was recorded as exhausted, and no unit was dropped.
