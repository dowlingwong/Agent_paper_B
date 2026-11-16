# Appendix section draft — "Track S pilot findings" (15 November 2026)

**Status.** Draft for the paper appendix. AI-assisted (Claude, Mac agent), written at the author's request after the
STOP 4 decision (PLAN §10 `R1-TRACKS-STOP4-END`; draft row `proposals/PLAN_ROW_R1-TRACKS-STOP4-END_DRAFT_20261115.md`).
Not an author decision.

**Revision of 16 November 2026 (per-decision wording).** The author's proof check is now recorded (PLAN §10
`R1-T4-PROOF-CHECK`). Its consequence clause lets this section be revised to the per-decision wording of
Proposition 8′, parts 2–3, with no campaign-level conclusion (`R1-TRACKS-STOP4-CONSEQUENCES` item 5). This revision does
that, and changes nothing else:
- §A.x.2 states Proposition 8′ decision by decision, and adds the scope limits the proof check sets;
- the campaign-level sentences elsewhere are reworded as statements about decisions, or as descriptions of what the
  pilot records show;
- the conditions for manuscript use and the sources are updated.

No number changes. Whether and where the section enters the manuscript is the author's decision.

**Conditions for manuscript use.**
- **Numbers.** Every number below comes from ENGINEERING_ONLY pilot runs. RUNBOOK §1 says such runs are never quoted as
  results. The section therefore presents them as a disclosure of why a planned experiment was stopped, and draws no
  result from them.
- **Theory.** The reading uses Proposition 8′ of `proposals/T4_PROP10_REVISION_20261028.md`, whose main conclusion
  and proof the author approved with errata (`R1-T4-PROOF-CHECK`). The hold of `R1-TRACKS-STOP4-CONSEQUENCES` item 5
  therefore no longer applies. The same row sets the condition this revision meets:
  - only per-decision wording, from Proposition 8′ parts 2–3;
  - no campaign-level conclusion.
  The errata change part 4 and §1 of the proposition, not parts 2–3. The section uses part 4 only for the no-op and
  duplicate case, where the corrected wording is used.

**Sources.**
- Two-node S0.5 summary `reports/TRACKS_S05_SUMMARY_20261115.md` (accepted at `74808c0a`), with its scripts and JSON in
  `results/r1/tracks/s05_summary/`.
- Per-node run records `reports/TRACKS_S05_T7_RESULT_20261114.md` and `reports/TRACKS_S05_T7_TABULAR_20261114.md`.
- Operator runbook rev 3.3 (`prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, `13badb0d`).
- T4 (`theory/T4_FEEDBACK_PROPOSER.md`, Proposition 8 and Corollary 8a) and the Proposition 8′ proposal, revision 3
  (errata applied; `mac-t4-errata-20261116`).
- PLAN §10 `R1-T4-PROOF-CHECK`, `R1-TRACKS-STOP4-END`, `R1-TRACKS-STOP4-CONSEQUENCES`.

Everything from the next heading down is the draft text.

---

## A.x Track S pilot findings

**What was planned.** Track S was a screen whose design, settings and outcome framing were fixed in advance
(`R1-TRACKS-ADOPT`, `R1-TRACKS-S02`, `R1-TRACKS-FRAMING`). Its formal pre-declaration (S0.8) was to follow the pilot
and was never made. It would compare a tuned state-dependent (dynamic) threshold policy, with members acting on
E1 and on the E2 keep, against the best tuned static threshold, on two CPU nodes (`digits_mlp`, `tabular_mlp`) with a
pinned local manager. The base forecaster was A2-U, a hierarchical normal model per (key, sign) with a predictive
variance, gated by a calibration check before any evidence run (`R1-TRACKS-S02`).

**What happened.** Track S stopped after its pilot (S0.5), before any evidence run, by the author's decision
(`R1-TRACKS-STOP4-END`). It produced no campaign-level result, and the planned evidence phases did not run. This
section therefore makes no campaign-level claim of any kind. The
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

### A.x.2 What Proposition 8′ says about a single decision at a low run price

Proposition 8′ (the one-step, or index, theorem) is a statement about one decision at a given history. It needs no
independence condition. Its E2 part (part 1) fixes the value used by parts 2–3:
- **E2.** After an execution, keep iff the posterior mean m_n > 0. The best expected keep value is
  V\*_n = E[m_n⁺ | O_n].

Parts 2–3, at a single E1 decision:
- **Part 2 (E1).** Executing pays V\*_n − g in expectation and skipping pays 0. So execute iff V\*_n > g.
- **Part 3 (gain at that history).** Relative to "always execute, then keep by part 1", the gain at that history is
  (g − V\*_n)⁺.

Call the run price **low at a decision** when g < V\*_n there. At such a decision:
- part 2 says to execute;
- part 3 says that screening this decision gains nothing: (g − V\*_n)⁺ = 0;
- skipping it gives up V\*_n − g > 0 in expectation, whether the skip comes from a forecaster or from a dynamic
  threshold;
- the only part of the decision that carries value is the E2 keep.

**No-op and duplicate decisions.** A proposal that the rules detect as a no-op or a duplicate before it runs has
V\*_n = 0 on a bit-exact node, as both pilot nodes are (PLAN §3, l. 93 at `8709dce7`: restore is bit-exact on the CPU
nodes; STATUS, L7). For g > 0, skipping it is then strictly better than executing it (T4 Corollary 8a; Proposition 8′
part 4 as corrected). The gain of that skip at that decision is g.

So if the price is low at every decision whose proposal is not a rule-detectable no-op or duplicate, then decision by
decision, the E1 rule executes each such proposal, and each decision's remaining value lies in its E2 keep. Any value a
dynamic E1 rule could add at a decision must come from budget or information effects that Proposition 8′ does not
cover.

Three limits apply (`R1-T4-PROOF-CHECK`):
- **Per decision only.** These are statements about each decision at its history. They say nothing about a
  campaign's total value, and this section draws no campaign-level conclusion.
  - Under the author's incumbent-error model (option (ii) of the proposal's remark R1), the actual loop lies outside
    the scope of the campaign-level Proposition 10(a′). Campaign gains are reported as measured, and Track S measured
    none.
- **The Bayes quantity.** Under that model, V\*_n is computed conditional on the posterior of the incumbent's error e.
  A2-U does not model e (`R1-TRACKS-S02` (g)), which is one more reason its index is not V\*_n (§A.x.4).
- **Fixed price.** Proposition 8′ uses a fixed price with both actions always feasible. It does not cover a binding
  hard budget, whose opportunity cost depends on the remaining budget and the incumbent (proposal §5, R2).

### A.x.3 What the pilot shows

In the pilot, **A2-U's index** (not the Bayes V\*_n) exceeded g at every eligible E1 decision, on both nodes:

| | `digits_mlp` | `tabular_mlp` |
|---|---|---|
| A2-U's V\* − g over eligible E1 decisions | 2.58–2.61 σ_node | 4.04–4.06 σ_node |
| Range of A2-U's V\* over all eligible (non-duplicate) E1 decisions | 0.036 σ_node | 0.018 σ_node |
| Decisions below, or within ±0.5 σ_node of, g or the static threshold | 0 of 298 | 0 of 330 |
| E1 skips per policy, all rule-detected duplicates | 429 | 399 |
| Instances on which the two policies took identical action sequences | 20 of 20 | 20 of 20 |
| … and identical results at each truncation W = 8/10/12/20 | 20 of 20 | 20 of 20 |
| Between-policy sd of the campaign outcome (S0.5b at W = 12; at the cap) | 0; 0 | 0; 0 |
| E2 keep / discard / invalid proposal (each policy) | 148 / 170 / 53 | 158 / 192 / 51 |
| E2 margins m̂ (5th–95th percentile); within ±0.5 σ_node of 0 | −0.108 to 0.114; 46 | −0.055 to 0.034; 38 |

**Interpretation, under A2-U's index and its m̂.**
- E1 was trivial: every valid proposal that was not a duplicate was executed, by both policies. (Per policy, 53 and 51
  proposals were invalid and never reached E1; each campaign's 40 calls are accounted for.)
- E2 was not trivial: m̂ spread widely around 0, and many keep decisions were close to it.
- The two policies differ only in their E1 rule, and that rule took the same action at every E1 decision. So their
  action sequences coincided (the table above). This is a description of the pilot records, not a statement about the
  value of either policy over a campaign.

**Budgets.**
- At W = 40, every campaign ended at the 40-call LLM cap. The worker budget was never exhausted (at most 27 of 40
  runs).
- At W = 12, the worker budget bound in 94 % (digits) and 100 % (tabular) of the 50 S0.5b roots per node (both
  policies, including the 10 second repetitions).
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

The gate fixed in the design before the pilot (design S0.5 (iii)) required the 80 % intervals to cover between 70 % and 90 % of audited increments, overall and in
every stratum of the group's history length n_group with at least 20 predictions. A2-U failed it on both nodes:

| n_group stratum | `digits_mlp` (n) | coverage | `tabular_mlp` (n) | coverage |
|---|---|---|---|---|
| 0 | 65 | 0.538 | 57 | 0.368 |
| 1–2 | 89 | 0.674 | 95 | 0.653 |
| ≥ 3 | 144 | 0.944 | 178 | 0.831 |
| overall | 298 | 0.775 | 330 | 0.700 |

- For a group's first proposals, and for groups with one or two earlier results, the intervals were too narrow on
  both nodes. On `digits_mlp` they were too wide for groups with three or more earlier results.
- A2-U's V\* values are therefore not validated estimates of the Bayes quantity V\*_n in Proposition 8′.

So we do not claim:
- that E1 screening is trivial for these nodes in truth;
- anything about A2-U as a forecaster or controller beyond the gate failure and the descriptive account of its pilot
  behaviour in §A.x.3; in particular nothing about its accuracy, about the true V\*_n, or about how it would behave on
  other nodes or with other priors;
- any comparison between dynamic and static thresholds, or any of the outcomes Track S was designed to decide.

What the pilot shows is narrower:
- with this forecaster at this price, the E1 rule did not discriminate between proposals, and so the two policies
  coincided;
- with A2-U's index in place of V\*_n, every E1 decision of the pilot policies was in the configuration that
  Proposition 8′ parts 2–3 describe for a low price at that decision: each valid non-duplicate proposal executed, and
  only its E2 keep left as a decision. Whether the price is low for the true V\*_n is not established.

Offline recalibrations were explored after the pilot (summary §6). They were not pre-declared, are exploratory and
support no statement here.

### A.x.5 Disclosures

- **The stop was decided after seeing the data.** The author chose to end Track S after the pilot data, and its
  summary, had been seen. The summary set out three options: revise A2-U's prior or variance structure and repeat
  S0.4/S0.5; change the run price or budgets; or narrow Track S (an E2-only comparison, dropping a node, or ending
  before evidence). It recommended the first, with fallbacks declared in advance. The author chose to end Track S. No
  evidence run had started.
- **Host.** `digits_mlp` was planned for TASL-2 and moved to TASL-7 after TASL-2 became unreachable on 12 November
  2026. Its S0.4 rows, which A2-U's prior was fitted from, come from TASL-2. Its S0.5 pilot ran on TASL-7. A
  partial S0.5 attempt on TASL-2 (last seen with 4 committed roots) was preserved and not used.
- **Order.** On the author's instruction (relayed by the coordinating agent; no PLAN row), `tabular_mlp`'s
  determinism check (S0.1) was run after its S0.4 and before S0.5.
- **Pause.** The `digits_mlp` S0.5 ran in two sessions. It paused on 13 November after 22 roots, on a STOP file whose
  origin is not evidenced. After one failed resume attempt that ended before any server started, it resumed on
  14 November with a byte-identical command.
- **Concurrency.** The number of concurrent manager servers was fixed by measurement at k = 2 on both nodes.
- **Inspection.** All pilot data and their independent reviews are in the repository (see Sources). No pilot
  unit failed, none was recorded as exhausted, and no unit was dropped.
