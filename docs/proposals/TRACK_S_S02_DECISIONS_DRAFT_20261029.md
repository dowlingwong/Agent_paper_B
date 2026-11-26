# Track S — author decisions needed (S0.2): options and recommendations (draft, 29 Oct 2026)

AI-assisted draft (Claude, chat session). **Nothing here is decided.** Each item becomes a decision only as a dated PLAN §10 row committed by the author. The recommended rows are written so they can be pasted as they are.

**Context.** The current runbook is **revision 7**, `proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`. It is a one-way screen with design D2. The author chose the one-way screen on 29 Oct, after the synthetic design study showed that "no sequential gain" cannot be certified at an affordable budget. Revision 6.1 had been accepted by the sixth independent review; revision 7 is under a short confirmation review. Hosts are already decided (R1-TRACKS-HOST, -2).

## Summary table

| # | Decision | Recommendation |
|---|---|---|
| D1 | Adopt Track S (rev 7, one-way screen, design D2) as a plan | **Adopt** (one-way screen already chosen by the author) |
| D2 | Base controller | **A2-U** (Bayes-myopic under a declared hierarchical model) |
| D3 | Budget regime | **LLM cap 40; W from the pilot** (the largest of {8, 10, 12, 20} that binds in ≥ 50 % of campaigns; 20 if none binds) |
| D4 | Margins | **δ_Y = max(0.002, 0.5 σ_node)** in raw metric units: digits 0.0033, tabular 0.0020 |
| D5 | Split policy | **`vary`** for every Track S run (a declared departure from the MLP nodes' D21 `fixed`) |
| D6 | E2 verify | **Off** for every Track S policy |
| D7 | Duplicates and horizon | **Deployment rule:** a filtered duplicate spends a trial slot and an LLM call |
| D8 | Incumbent-error model (T4 revision R1) | **Not needed for Track S; keep open** for the theory proof check |
| D9 | Nodes, n_max, fallback | **digits_mlp (TASL-2), tabular_mlp (TASL-7); n_max = 300; fallback fixed at S0.5b** |
| D10 | What each outcome means for Paper B's framing | **The mapping below** (one-way), declared before any outcome |
| D11 | Wording corrections independent of Track S | **Correct TRACK_P:386** and **state that A2 is not the theorem's myopic rule** |
| D12 | Code delivery for the private repo | **Give the session access to `Agent_paper_B`**, or allow deletions in the local folder |

## Details

### D1 — Adopt Track S
- **Options:**
  - (a) Adopt rev 6.1.
  - (b) Do not run it, and decide the framing on theory alone.
  - (c) Run only the cheap parts: S1.1, S4a and the synthetic calibration.
- **Why (a).** It is the only option that tests the DAC headline before post-training spend, and it costs about 1–3 days of 4090 time per node. Option (b) leaves a DAC paper whose implementation is a contextual bandit with no evidence either way, which a DAC reviewer would flag. Option (c) cannot decide anything.
- **Risk.** Code, review and pilots take about 1–1.5 weeks of calendar time. The decision falls around 15–23 Nov if both hosts stay free. **What the screen can do:** detect a keep-feedback gain of about δ_Y (power ≈ 0.75) or an information gain of about 2 δ_Y (power ≈ 0.6). **What it cannot do:** prove that no gain exists, or measure the budget channel's sensitivity.

### D2 — Base controller A2-U
- **Options:**
  - (a) A2-U: a hierarchical normal model per (key, sign of the step), with predictive variance, a calibration gate and a declared model.
  - (b) A2: a constant per node.
  - (c) A3/A5: learned and history-aware.
- **Why (a).**
  - A2 ignores the history, so the information channel can never show up, and A2 is not the theorem's myopic rule.
  - A3/A5 need sweep labels that do not exist yet, and would tie Track S to the C3 timeline.
  - A2-U needs only S0.4's ten dev campaigns.
- **Cost.** A2-U is not the deployed rule, so Track S speaks to "a Bayes-myopic rule under a declared model". That is stated as a limitation.

### D3 — Budget regime
- **Options:**
  - (a) Deployment W = 20.
  - (b) Choose W so that it binds.
- **Why (b).** At cap 40 with 51–66 % duplicates and KG verify silent, W = 20 probably never binds. The budget channel would then be untestable, and element (2) of the author's request would be empty.
- **Cost.** A departure from deployment, which is declared. If no W binds, that is itself the finding, and W = 20 is used.

### D4 — Margins
- **Options:**
  - (a) max(0.002, 0.5 σ_node), using the fixed-split σ_node of the noise-floor table.
  - (b) Margins tied to `vary` noise (≈ 0.5 σ_joint, about 0.005–0.006).
  - (c) D18's 0.002 metric-unit margin.
- **Why (a).**
  - It is a substantive effect size, declared now, independent of any Track S data.
  - (b) would make route B easier, because noisier runs would give a bigger margin.
  - (c) has the wrong units: it is a 20-run one-step quantity.
- **Consequence.** Tabular's margin is small (0.0020) while its `vary` noise is large, so tabular will probably need n > 300 and support route A only. Route B would then be decided on digits alone. That is acceptable and pre-declared (n_max, B-eligibility).

### D5 — Split policy `vary`
- **Why.**
  - Under `fixed`, logistic-regression nodes reproduce verify exactly (the DI-pilot failure).
  - For the MLPs, `vary` makes the audited Y average over split noise, which is closer to generalisation.
- **Cost.** A declared departure from the MLP nodes' D21 policy, and larger noise (hence larger n). Recommended anyway, because Y must not depend on a single frozen split.

### D6 — Verify off
- **Why.** KG verify never fires at the declared g, but cheaper grid prices could make it fire and spend 2r runs. That would mix a verify policy into the static-vs-dynamic comparison.
- **Cost.** Track S does not study verify. It is studied elsewhere (C2).

### D7 — Duplicates consume horizon
- **Why.** This is what the deployed loop does, and Track S should measure the deployed loop's structure.

### D8 — Incumbent-error model (R1)
- **Why defer.** Track S measures empirically and does not need the model. The shared incumbent error appears inside the keep and feedback channels.
- The decision belongs to the T4 proof check: whether Prop. 10(a′) is stated for re-measured incumbents (option i) or with a shared latent error (option ii, which puts the loop outside the theorem).
- **My recommendation for the theory, separately:** option (ii). It is the honest model of the current loop, and it makes Track S's empirical answer the relevant one.

### D9 — Nodes, n_max, fallback
- **Why.** The MLP nodes are the most favourable affordable nodes: several knobs, the most keeps, cheap runs. One node per host keeps every table single-host.
- n_max = 300 caps a node's S3e at about 42k LLM calls.
- The fallback is decided only at S0.5b, before any outcome.

### D10 — Framing consequences (declare before any outcome; one-way screen)

| Track S outcome | Paper B framing | RL arms (R-B, A7) |
|---|---|---|
| **A**, information or keep channel | Keep the **noise-aware DAC** headline; "a tuned dynamic threshold beats the tuned static rule" becomes a main result | Justified; keep |
| **A**, budget member | "Noise-aware **budget-coupled** index control", explained by known OR theory; DAC as the formal frame | Optional; appendix |
| **A** worded as a threshold-level shift (matched static recovers ≥ half) | No dynamic claim; report it as a tuning result | Not needed |
| **A-small** or **no gain found** | "Noise-aware DAC **and when it reduces to one-step decisions**", carried by the theorem, its failure examples and the synthetic controls. Track S is reported as "no dynamic gain above UB found, sensitivity …". **Never** "the loop is one-step" | Not needed; drop or appendix; C3 carries the method |

**Why declare now.** It stops the framing from being chosen after the result. Under the one-way screen it also keeps a null result from being over-read.

### D11 — Wording corrections (regardless of Track S)
- TRACK_P:386 calls a DAgger proposer shift "evidence of the sequential (DAC) structure". Recommend rewording it to "evidence of state-distribution shift; not a policy-value gap".
- C3_DESIGN and PLAN should state that A2 (constant prior) is not the Bayes-myopic rule of T4 Prop. 10(a′), because it ignores the history. This matters for how C3's comparator is described in the paper.

### D12 — Code delivery
- The harness branch `trackS-20261029` is pushed to GitHub, and further pushes follow after code review.
- `Agent_paper_B` is private and not reachable from this session. **Options:**
  - (a) Grant the Claude GitHub app access to `dowlingwong/Agent_paper_B`; I then push the branches directly.
  - (b) Allow deletions in the local `agent_paper_B` folder; git writes need lock-file removal, and I then fetch the branches into your local repo for you to push.
  - (c) I leave a git bundle in `.claude-worktrees/_snapshots/`, and you or the coordinator fetch it.
- **Recommend (a).**

## PLAN §10 rows (paste after deciding)

```
| R1-TRACKS-ADOPT (<date>) | Track S runbook revision 7 (`proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`; a one-way screen, design D2; the author chose the one-way screen on 29 Oct after the synthetic design study) is adopted as a plan. Evidence runs (S3a, S3e) still require an authorization note (S0.9) after the pre-declaration (S0.8). |
| R1-TRACKS-S02 (<date>) | Track S settings: (a) base controller A2-U (hierarchical normal model per (key, sign), predictive variance, S0.5 calibration gate; not the deployed C3 rule); (b) LLM cap 40, W = the largest of {8, 10, 12, 20} that binds in ≥ 50 % of pilot campaigns on both nodes, else 20; (c) δ_Y = max(0.002, 0.5 σ_node) in raw metric units (digits 0.0033, tabular 0.0020), a declared departure from PLAN:118's normalisation; (d) `vary` split for every Track S run, a declared departure from the MLP nodes' D21 `fixed`; (e) E2 verify off for every Track S policy; (f) duplicates consume a trial and an LLM call (deployment rule); (g) the incumbent-error model (T4 revision R1) is not needed by Track S and stays open for the proof check; (h) primary nodes digits_mlp (TASL-2) and tabular_mlp (TASL-7), n_max = 300 per node, fallback decided only at S0.5b. |
| R1-TRACKS-FRAMING (<date>) | Framing consequences of the Track S one-way screen, declared before any outcome: A on the information or keep channel → keep the noise-aware DAC headline and the RL arms; A on the budget member → "budget-coupled index control", RL arms optional; A worded as a threshold-level shift → no dynamic claim; A-small or no gain found → "noise-aware DAC and when it reduces to one-step decisions", carried by theory and controls, never claiming the loop is one-step; RL arms not needed. |
| R1-WORDING-29OCT (<date>) | TRACK_P:386 reworded ("state-distribution shift; not a policy-value gap"); C3_DESIGN and PLAN state that A2 is not T4 Prop. 10(a′)'s Bayes-myopic rule. |
```
