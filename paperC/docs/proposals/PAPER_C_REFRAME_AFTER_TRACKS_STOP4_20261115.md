# Paper C — what to do after Track S STOP 4 (proposal, 15 Nov 2026)

**AI-assisted (Claude, chat session), written at the author's request. Proposal only; it becomes binding through an author row.** Sources:
- Track S two-node S0.5 summary, `docs/r1/reports/TRACKS_S05_SUMMARY_20261115.md` on `mac-tracks-stop4-end-20261115` @ `795e518b`, §2–§5;
- PLAN §10 R1-TRACKS-STOP4-END and R1-TRACKS-STOP4-CONSEQUENCES.

## 1. What STOP 4 actually showed

On `digits_mlp` and `tabular_mlp`, with A2-U, run price g = 0.1 σ_node, and W = 40 and 12 (S0.5 summary §4):

1. **Proposals were indistinguishable to the forecaster.** The fitted prior has τ0 on its floor because τ_A2 < τ_w. V\* varied by 0.036 σ_node (digits) and 0.018 σ_node (tabular) across all eligible proposals.
   - This is structural, not a fluke of these runs. τ_A2 comes from A2's 12-bin soft labels, whose tails stop at ±4 σ_node, so τ_A2 is a few σ_node at most.
   - The audited increments have an sd of about 9 σ_node (digits) and 22 σ_node (tabular): heavy tails, mostly edits that break or degrade the run.
2. **The run price was far below the option value of trying.** V\* ≈ 0.4 · τ_w²/√(τ_w² + σ_cmp²) ≈ 2.7–4.1 σ_node against g = 0.1 σ_node.
   - Discard catches the downside (E2), so executing a bad edit costs only g.
   - As a result, every non-duplicate proposal was executed, and every E1 skip was a rule duplicate.
3. **A binding budget created no decisions.** W = 12 bound in 94–100 % of campaigns, but with interchangeable proposals any 12 are as good as any other 12. Truncated campaigns were prefixes of the same action sequences. The budget member of the dynamic family could not flip any E1 decision.
4. **The keep decision (E2) is real.**
   - m̂ ranged from −0.108 to 0.114 (p05–p95, digits) and from −0.055 to 0.034 (tabular).
   - 46 / 298 and 38 / 330 E2 decisions lay within ±0.5 σ_node of the keep margin.
   - Keep / discard / failed_invalid counts were 148 / 170 / 53 and 158 / 192 / 51.

**General lesson.** Screening (E1) matters only when two conditions hold together:
- **discrimination:** the forecaster spreads V\* across proposals, measured by sd(V\*) relative to the price;
- **a price comparable to the upside:** g / V\* is not small. The run cost can be real (expensive runs) or a shadow price (a binding budget together with discrimination).

Cheap CPU runs scored by a coarse forecaster sit in the corner where screening is inert. That corner is a finding, not a failure: it is the condition under which Paper B's reduction to one-step decisions is harmless for E1.

## 2. Options

| | Option | What changes | For | Against |
|---|---|---|---|---|
| **A** | **Acceptance and evaluation control** (E2-centred) | The controlled actions become: keep/discard; **verify** (re-measure a near-margin candidate with extra seeds, paid in runs); **re-audit the incumbent** (against the shared incumbent error and the winner's curse); **final selection** among the top candidates at campaign end. E1 stays only where §4's relevance check passes | E2 is measured to be decision-relevant. Noise is large (Paper B C1). The sequential structure is real: a keep changes the incumbent that every later comparison uses, and early wrong keeps compound. Strong non-RL comparators exist (sequential tests, racing, knowledge gradient, OCBA, budget-aware margins), which makes Q3 sharp. It is the governed harness's own invariant: the control plane owns keep/discard | One-step KG verify did not fire at the declared g in Paper B (A1), so verify is only relevant at a binding budget or at the end of a campaign. Must be checked before collection (§4) |
| **B** | **Make screening matter: broaden to expensive runs** | GPU tasks (T1/T2: autoresearch, 1GC-7RC, MLGym) with run price set from real GPU time and wall-clock budgets. A forecaster with per-proposal skill (Paper B's C3 text belief), with heavy-tail handling (a hurdle model: P(break or degrade), then the conditional increment) | Puts real loops in the corner where E1 can matter. HoreKa 2 H100 and the ETP HTCondor GPUs now exist, so a powered GPU tier is affordable in a way it was not in plan rev 2 (§12: ≈ 0.85 GPU-h per campaign at 2-minute runs) | Depends on C3 skill, which is unknown until Paper B's Track P. Costly. A null is possible again |
| **C** | **Steer instead of gate** | The controller chooses what the proposer is asked to do next (explore a new key, refine around the incumbent, revise, repair), i.e. DAC on the proposer's mode | If the value lies in *what* is proposed rather than in filtering, this is where it is. The harness already has a `revise` path (LangGraph manager `revision_feedback`) | Large new action space; attribution is harder; the plan listed "revise as an action" as not planned (§3.3) |
| **D** | **Characterisation frame: when does sequential control pay?** | The paper's spine becomes a map of headroom over measured parameters: g/V\*, sd(V\*), noise σ_cmp/τ, keep-margin mass, feedback strength, edit interaction. E-SYN gives the gains over this map; real nodes are placed on it from their logs; real campaigns run where the map predicts headroom, plus one predicted-null node as a control | Every outcome is reportable. Track S's null becomes a data point. The diagram can be built and tested before costly collection | On its own it can read as descriptive; it needs A or B for a confirmatory result |

## 3. Recommendation

**Use D as the frame, A as the confirmatory core, B as the broadening tier, and C as an extension.** Start with a headroom census on data that already exist (§4) before building anything costly.

Restated questions:
- **Q1.** Does non-myopic **acceptance and evaluation control** beat the tuned static acceptance rule on whole campaigns? Round B′ actions: keep/discard, verify, re-audit, final selection. E1 is added only on nodes that pass the relevance check.
- **Q2–Q5.** As in the plan.
- **Q3 comparators** gain sequential testing (an SPRT-style rule), racing, KG/OCBA verify, and budget-aware margins.
- **OPD (M4)** is unchanged.
- **The map (D)** becomes a named output: the headroom over the measured parameters, with real nodes placed on it.

## 4. First step: headroom census on existing logs (new build item B16, runbook phase PH)

For every node with logged campaigns or labels, compute:
- **E1 relevance:** g/V\* and sd(V\*)/g under the best available forecaster; the share of eligible E1 decisions within ±0.5 σ_node of the price.
- **E2 relevance:** the distribution of the keep margin m̂ and its mass within ±0.5 σ_node of 0; the **false-keep rate** (keeps whose fresh-seed audited Δ ≤ 0) and the **missed-keep rate**.
- **Incumbent error:** recorded vs re-audited incumbent value (winner's curse), and how it grows with the number of keeps.
- **Budget:** binding share at the planned W, and the shadow price implied by the forecaster's spread.
- **Heavy tails:** share of failed_invalid and degraded runs, and the tail mass beyond ±4 σ_node.

**Inputs that already exist:**
- Track S S0.4/S0.5 (`results/r1/tracks/{digits_mlp,tabular_mlp}/…`);
- Paper B sweep 1 and its audited labels (10 seeds per audited proposal, 8 CPU nodes);
- the C1 30-seed noise table;
- the B1/B2 exam campaigns with the candidate proposers (they ran on Paper B's CPU nodes);
- the T1 census, when it exists.

CPU only, read-only on those data. **Output:** one table per node and a first placement on the map. **Decision after the census:** which nodes and channels enter SPT collection.

## 5. Changes to the build

New items:
- **B16** headroom census;
- **B17** evaluation-allocation actions (verify, re-audit, final selection) in E-SYN worlds and later in the SPT runner;
- **B18** sequential-testing comparators (SPRT-style, racing, KG/OCBA verify, budget-aware margins);
- **B19** a heavy-tail-aware forecaster (hurdle/mixture) for the GPU tier.

Runbook:
- phase **PH** (census) goes after P2;
- P3's E-SYN suite adds worlds where verify and re-audit have known value (a shared incumbent error world, a near-margin noise world).

## 6. A note for Paper B

The same structural point, that soft-label bins capped at ±4 σ_node understate the spread of heavy-tailed increments, applies wherever Paper B computes V\* from a 12-bin belief. It does not affect RPS or ECE. It may affect E1 values in the closed loop. Worth one check in Paper B's C3 analysis.

## 7. Author decisions requested

- **R-C1.** Adopt the frame (D + A core + B broadening + C extension)?
- **R-C2.** Run the census (B16/PH) first and fix the node and channel list from it?
- **R-C3.** Once R-C1 is decided, the core-scope row R1-PAPERC-CORE is rewritten to match and committed.
