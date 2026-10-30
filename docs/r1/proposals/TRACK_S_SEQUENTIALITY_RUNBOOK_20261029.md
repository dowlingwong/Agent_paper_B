# Track S — Is the loop sequential? A discriminating experiment (proposal, revision 7.4, 29 Oct 2026)

**Status.** AI-assisted proposal (Claude, chat session), drafted at the author's request on 29 Oct 2026. **Not adopted, authorizes nothing, not evidence.** It becomes a plan only through dated rows in PLAN §10 and an authorization note under `docs/r1/authorizations/`. Hosts are decided (PLAN §10 R1-TRACKS-HOST and R1-TRACKS-HOST-2, 29 Oct); nothing else is.

**Provenance.**
- §1 comes from three independent read-only verification passes over this repo (`docs/c3-pool-28oct` at `cefa389`) and harness `r1` (`897d83c`).
- Six independent reviews: rev 1 → `proposals/TRACK_S_REVIEW_20261029.md`; rev 2 → `reviews/TRACK_S_REV2_REVIEW_20261029.md`; rev 3 → `reviews/TRACK_S_REV3_REVIEW_20261029.md`; rev 4 → `reviews/TRACK_S_REV4_REVIEW_20261029.md`; rev 5 → `reviews/TRACK_S_REV5_REVIEW_20261029.md` (REVISE, narrow); rev 6 → `reviews/TRACK_S_REV6_REVIEW_20261029.md` (**ACCEPT WITH MINOR CHANGES**: 0 BLOCKING, 0 MAJOR, 10 MINOR).
- Revision 6.1 applied all ten minor changes. **Revision 7** follows the S0.6 synthetic design study (`r1/tracks/ANALYSIS_NOTES.txt`, analysis branch `7a9cd6f`, FIXTURE) and the author's decision of 29 Oct to run Track S as a **one-way screen**. Revision 7.1 applies the twelve minor changes of the rev-7 confirmation review (`reviews/TRACK_S_REV7_REVIEW_20261029.md`: ACCEPT WITH MINOR CHANGES); see §11.

**What changed structurally.**
- **Revision 4** moved the decision from fork level to campaign level.
- **Revision 5** made it the standard DAC comparison: a tuned dynamic threshold family vs a tuned static rule, compared on fresh instances.
- **Revision 7** makes Track S a **one-way screen** (author, 29 Oct). The synthetic study showed that at an affordable budget the pipeline detects a sizeable dynamic gain, but almost never certifies its absence: P(route B) ≤ 0.13 even under a true null. Route B is removed. The outcomes are "a dynamic gain found" or "no gain above UB₉₅ found", with the sensitivity stated from the controls.

## 0. Why, and what it decides

**Why.** Paper B's headline is noise-aware DAC (R1-ROUTE-DAC). The revised theory (T4 Prop. 10(a′)) says that with a fixed run price g, no feedback (NF) and no information (NI), the myopic index rule using the Bayes posterior given the history is globally optimal, so the loop decouples into one-step decisions. Three problems follow:
- Everything trained or evaluated so far is one-step (§1, D3).
- The only sequential measurement sits behind the one-step C3 gate.
- The current comparator A2 ignores the history (§1, D6).

**What Track S decides.** Track S asks: **does a tuned state-dependent (dynamic) threshold policy beat the tuned static threshold rule, on whole campaigns?** This is the DAC question "dynamic policy vs best static configuration" (Biedenkapp et al. 2020; Adriaensen et al. 2022, JAIR).

| Channel | Mechanism | Outside Prop. 10(a′) because |
|---|---|---|
| Budget | Under a binding run budget the value of a run depends on the state | Hard budget (revision §5 R2) |
| Controller information | An executed result informs later forecasts; the duplicate filter learns the configuration | NI; controller side of NF-c |
| Manager feedback and incumbent change | What the manager sees; a keep changes the incumbent shown and the base of later increments | NF-a; NF-b; shared incumbent error (revision R1) |

**Outcomes** (§3; campaign level, per node, raw audited Y). Track S is a **one-way screen**: it can establish a dynamic gain, never its absence.
- **Route A:** at least one Holm-adjusted rejection of H₀: mean D ≤ 0, and not A-small.
  - If π\* is the budget member, word it as "a dynamic-knapsack threshold, explained by known OR theory".
  - If the matched-static secondary recovers at least half of the gain, word it as "a threshold-level shift found by the dynamic tuning", not as dynamics.
- **A-small:** a Holm-adjusted rejection, but UB₉₅ < δ_Y on every node with a rejection. The gain is real but below the margin. For the headline this is treated like "no gain found", and the significant gain is reported.
- **No gain found:** no rejection. Reported per node with three numbers side by side: UB₉₅, the S3e flip rate, and S0.6's P(correct member). Worded: "the selected dynamic member π\* did not beat the tuned static rule m\*; its mean gain is below UB₉₅ = …. On this node the S0.6 calibration detected a planted keep-feedback gain of … δ_Y with power … and an information-world gain of 2 δ_Y with power …. The budget channel, negative keep feedback and the information member itself are unprobed." Three rules apply to this outcome:
  - It is **not** evidence that the loop is one-step.
  - It bounds π\* only, not the four-member family (rev-7 m5).
  - **UB₉₅ < δ_Y is not an equivalence or negligibility result.** Under N0 a small UB₉₅ mostly reflects that π\* and m\* agree on 90–95 % of decisions, not that dynamics are absent (rev-7 m6).

  The sensitivity values are the **per-node** S0.6 values at the final n, not the FIXTURE study values (rev-7 m7).

**The author's four elements:**

| Element | Where |
|---|---|
| (1) Harder benchmark | S1: the most favourable affordable nodes, replicated synthetic controls, and a GPU extension outside the decision |
| (2) Hard budget | S2: W chosen so that it binds; a budget member in the dynamic family (its sensitivity is unmeasured: no calibratable P0 world) |
| (3) Myopic vs non-myopic | S0.7 tunes the static rule and four mean-centred dynamic members; S3e compares them on fresh instances (one-way) |
| (4) Feedback ablation via branching | S4: ghost and controller-only arms at the same forks, and a prompt-level display ablation |

## 1. Verified starting facts (29 Oct)

Paths: `apb/` is this repo at `docs/c3-pool-28oct`; `h/` is `autoresearch_harness@r1:src/autoresearch/`. All rows were confirmed again by the rev-3 reviewer (10 spot-checks).

### Design and theory

| # | Finding | Evidence |
|---|---|---|
| D1 | **The online estimand is a hard budget, not a price.** V^π is audited Y at matched worker runs W and LLM-call cap; `c3_budgets` makes both bind. The fixed g appears only in the theory and the offline gate. | PLAN:118–121; `r1/c3/control.py`:170–183, 351–363; `r1/c3/offline_eval.py`:23–28 |
| D1′ | Under a binding hard budget, the optimal execute rule has a state-dependent threshold (stochastic/dynamic knapsack). Example: N = 2, K = 1, V* ∈ {1, 3}; the optimum is 2.5, the best static g 2.25. | verifier arithmetic; cite stochastic-knapsack literature and Arlotto & Gurvich (2019), to be checked before citing |
| D1″ | Verify spends 2r runs (`h/control_plane/campaign.py`:718–740). **But the C3 controller's KG verify never fires at g = 0.1 σ_node, r = 2 when σ_cmp ≤ σ_node**, so in practice verify does not make W bind. | `r1/c3/control.py`:16–23 and its test |
| D2 | Actions: E0 continue/stop/demote; E1 continue/skip/revise; E2 continue/verify. **E2 has no keep/discard action**: keep acts only through the Bayes threshold, so a forced keep needs new code. | `h/control_plane/campaign.py`:429–433; `h/control_plane/controller.py`:264–270 |
| D3 | Every trained arm learns from one-step per-proposal targets, and nothing does multi-step credit assignment. TRACK_P:386 over-claims a DAgger shift as "evidence of the sequential (DAC) structure". | `r1/c3/env.py`:8, 27; TRACK_P:153–157, 386; C3_DESIGN:84–88 |
| D5 | The DI pilot's "violated in value terms" verdict was withdrawn in the same report; audited residual +0.00004. | `reports/DI_TEST_MEMORY_ON_PARTIAL_20261019.md`:127–133 |
| **D6** | **A2 forecasts one constant per node for every non-rule proposal** (A1's node mean, with π = 1 on rule-detectable inert proposals). Its V*_n is therefore constant per (node, edit kind), it ignores the history, and it is not the theorem's Bayes-myopic rule. A3 (LightGBM on history features) is history-aware but needs labels. | `r1/c3/arms.py`:10–12, 122–131; `r1/c3/control.py`:213–226 |

### Harness

| # | Finding | Evidence |
|---|---|---|
| H1 | Only `one_line/v1` is declared as a skip display. "Off" shows a generic `decision=skipped; metric=missing` line, and no mode hides skips. Duplicate and no-op skips are also labelled "predicted no gain". | `h/memory/summarizer.py`:27–51, 100–103, 181–185 |
| H1′ | Under memory `none` too, the prompt shows the current best metric, the incumbent's editable values and a "budget index" (consumed trials + 1). Skip and ghost therefore share that index and the LLM seed. | `h/manager/langgraph_manager.py`:55–71, 122–141; `h/control_plane/budget.py`:24–25 |
| H3 | A duplicate is a config equal to an earlier *evaluated* config; the seen-set grows only from executed rows (NF-c fails by construction). A filtered duplicate spends an LLM call and a trial slot. | `r1/c3/features.py`:390–391, 402–411, 423 |
| H4 | `resume_campaign` takes `first_action`, `policy`, `horizon`, `worker`, `manager` and `keep_prior` only; **there is no arm-override hook**. The replayed E1 run is debited and its configuration enters the harness novelty set. Controller state is not snapshotted. | `h/control_plane/snapshot.py`:836–848, 895–905, 976–982 |
| H4′ | The worker seed is fixed per campaign; verify and audit seeds are deterministic. The manager seed already takes a `repetition` argument, so r = 2 needs no new seeding code. LLM determinism has been checked on 3 serial requests only, on deepthought. | `h/manager/langgraph_manager.py`:55–71; `reports/LLAMACPP_PROBE_DT_20261025.md`:17 |
| H5 | "N proposals, at most K runs" = trials N with `max_worker_runs = K`. | `h/control_plane/budget.py`:10–125 |
| H6 | The proposal schema allows one parameter per proposal. | `h/llm/providers.py`:23–27 |
| H7 | The existing C3 feature `budget_frac_left` is **trial-indexed** (1 − (b−1)/runs_total), so at cap 40 and W = 10 it goes negative and is identical in skip and ghost. Track S computes budget features from `worker_runs_remaining`. | `r1/c3/features.py`:257, 385; `h/control_plane/budget.py`:112 |
| H8 | On the MLP nodes the manager edits HIDDEN_UNITS, BATCH_SIZE and LR (about 3 keys, ≈ 5 executions per key per campaign). | `LIVENESS_LLAMACPP_20261026.md`:78–79 |

### Benchmarks (sweep 1 has no data yet; pilots only)

| # | Finding | Evidence |
|---|---|---|
| B1 | Six of the eight sweep-1 nodes share one OpenML template that starts from logistic regression. The 7B manager edits almost only `max_iter` and `C`; repaired nodes are close to a one-knob monotone climb. | `nodes/openml_breast_w/benchmark.py`:39–62, 222–247; `LIVENESS_LLAMACPP_20261026.md`:76–83 |
| B1′ | No node has a measurement of edit–edit interaction. T4 §8 concerns seed effects, not edits. | `T4_FEEDBACK_PROPOSER.md`:125 |
| B2 | σ_node (median paired sd Δ̂): digits 0.0066, tabular 0.0019, breast_w 0.0007 (σ_joint 0.0038). 727 of 841 rule-detectable pilot proposals were duplicates, and **the duplicate share rises with campaign length** (51–66 % with memory on). At a cap of 40, about 14–20 non-rule proposals are expected per campaign. Both MLP nodes' D21 split policy is `fixed`, and **these σ values are fixed-split**: under `vary`, tabular's split sd is 0.0123 against σ_train 0.0029, so tabular is not "lower noise" under Track S's `vary` split. Track S's σ_d and sizing use S0.5 measurements under `vary`. | `NOISE_FLOOR_COMMON_20261022.md`:105–113; `DUPLICATE_RATE_PILOT_20261022.md`:28–38 |
| B3 | The DI pilot had 0 changed decisions on breast_w and ionosphere (fixed split plus logistic regression). | `DI_TEST_*_20261019.md`; `E2_STOP_MEMO_20261012.md`:29 |
| B4 | Harder benchmarks are not runnable yet: autoresearch is a stub, 1GC-7RC is removed, MLGym has no container, `mlagentbench_vectorization` is excluded, and `ResNet_trigger` needs private data. | `reviews/LOCAL_AUTORESEARCH_STUB_REVIEW_20261027.md`; PLAN:409, 540 |
| B5 | Trial 1 is kept without comparison; early gains partly recover from a degraded first incumbent (digits liveness max Δ +0.217). | `LIVENESS_LLAMACPP_20261026.md`:76 |
| B6 | The deepthought manager latency was 7.26 s per call (GTX TITAN X). **4090 latency has not been measured**; Track S runs on TASL-2 (zhixu portal) and TASL-7 (R1-TRACKS-HOST-2). At 29 Oct both 4090s were idle (236–436 MiB used, 0 % utilisation, low CPU load; 270 GiB and 917 GiB free disk). | `LLAMACPP_PROBE_DT_20261025.md`:16; author's host census 29 Oct |

## 2. Preconditions (S0) — in this order; STOP until each is done

**Seed blocks.** There are five disjoint instance-seed blocks: S0.4 prior, S0.5 pilot, S0.7 tuning, S3a forks, S3e fresh. S3e also has its own audit-seed block. All campaigns of one instance share one instance-level seed key, covering LLM, worker, verify and audit seeds, whichever policy they run, so that runs pair exactly. **E2 verify is disabled for every Track S policy**, which is a declared choice: cheaper grid prices could make KG verify fire and spend 2r runs (D1″).

| # | Step | Host | Done when |
|---|---|---|---|
| S0.1 | **LLM determinism, latency, host census, separately on each host.** Replay 200 manager calls from fixed prompts and seeds under (a) 1 server with `n_slots = 1` and (b) 2 concurrent servers with `n_slots = 1` each. Record per-call identity, mean and p95 latency, and the free CPU cores. | TASL-2, TASL-7 | 100 % within-host identity in the chosen setting; else STOP |
| S0.2 | **Author decisions** (PLAN §10; see the decision memo). | Mac | Rows committed |
| S0.3 | **Code** with CPU fixture tests and an independent review: <br>• the arm-override hook, ghost and controller-only arms, forced E2 keep/discard, displays; <br>• A2-U; <br>• the **`static` and `dynamic` policy families** (§3), with a test that zero coefficients reproduce `static` exactly, and a test on the D1′ example that the budget term **lowers** the execute threshold when runs are plentiful (after a skip); <br>• instance-level seed keys, with a test that two policies taking identical decisions write byte-identical ledgers; <br>• a verify-off flag; <br>• the tuning and campaign phases; <br>• the fork collector; <br>• π′ (secondary), with the A2-U index and the E2 margin among its features, plus a test that π′ restricted to the index reproduces A2-U at some g; <br>• synthetic nodes (≥ 200 end-to-end replications); <br>• the analysis; <br>• the S0.1 probe and S1.1; <br>• arm-invariance tests 1–5 and the mechanical budget check. | container / Mac; fresh review agent | All tests pass; review accepted |
| S0.4 | **Prior fit (ENGINEERING_ONLY).** Per node on its host: 10 instances under "execute every non-rule proposal" at W = cap (40), K = 5 audits. Fit A2-U's hierarchical prior and variances. | digits: TASL-2; tabular: TASL-7 | Prior file with sha256 |
| S0.5 | **Pilot (ENGINEERING_ONLY)** at W = cap under A2-U, at the declared g = 0.1 σ_node. Per node, **≥ 20 instances, each run twice** with different policies (A2-U at g = 0.1 σ_node and at g = 0.3 σ_node), plus 10 instances run twice under the same policy with different LLM repetitions. Measure: <br>(i) binding shares for W ∈ {8, 10, 12, 20}, by truncating the ledgers at W runs; <br>(ii) σ_D between policies and between repetitions, and its one-sided 80 % upper confidence limit (χ²); <br>(iii) **A2-U calibration**: coverage of 80 % predictive intervals (audit noise included) for the next same-group audited Δ, with ≥ 100 predictions, stratified by prior group count (0, 1–2, ≥ 3). The gate is coverage in [0.70, 0.90] overall and in every stratum with ≥ 20 predictions. Else revise the inflation factor once and re-check; else STOP. <br>(iv) Calls and audit runs per campaign. <br>(v) A **fork-noise pilot**: 30 forks (skip vs execute), giving per-fork noise for matching the synthetic controls. | per node on its host | Numbers in the pre-declaration |
| S0.5b | **Fix W, units, n.** <br>• W is the largest value in {8, 10, 12, 20} that binds in ≥ 50 % of pilot campaigns on both primary nodes. <br>• σ_cmp,vary is the median paired sd of Δ̂ under `vary`, from the pilot. It is the unit of every threshold grid (rev-5 MA-3). <br>• Recompute σ_D at the chosen W from the pilot ledgers truncated at W (exact: the prompt has no runs-left field and the loop stops at W). **Each truncated final incumbent gets K = 5 audits.** Report the one-sided 80 % UCL. <br>• **n = 300 per node (fixed, rev 7.2).** The sizing formula ⌈(2.93 · σ_D,UCL / δ_Y)²⌉ is reported only as the minimum detectable effect. In the FIXTURE S0.6 run under the 7.1 rules, the selection noise from tuning made n = 110 too weak: P2+ power was 0.43 (diffuse) and 0.54 (concentrated). At n = 300 it was 0.75 and 0.92, with N0 at 1/200. 2.93 = z₀.₉₅ + z₀.₉₀ (≈ 83 % power under Holm with one null node, ignoring selection noise). <br>• **Fallback:** a node whose projected S0.7 + S3e time exceeds 4 days drops from the decision. This is decided here, before any outcome, and never later. | Mac | Values in the pre-declaration |
| S0.6 | **Synthetic calibration (no LLM; before tuning).** Run the whole pipeline (S0.7 design → S3e test at n) **≥ 200 times per control**, with noise matched to the pilot's campaign-level σ_D and to the pilot's between-policy sd (S0.5's two A2-U prices); the dev between-configuration sd does not exist yet at this point (rev-7 m11). After S0.7 the controls are re-run once with the dev between-configuration sd, and both tables are reported. <br>• **Null N0** (zero oracle gain for every member: non-binding W, independent values, no information, no feedback). **STOP** if the route-A rate is ≥ 19 of 200 (exact one-sided binomial p < 0.01). <br>• **Positive controls** whose planted best-member oracle gain over the best static rule is calibrated by large replication (10⁴ per member, ±5 %): **P2+** (budget-dependent keep feedback), diffuse and concentrated, at δ_Y; **P1-diffuse** (information) at 2 δ_Y. <br>• **Not calibratable** (study, 29 Oct): P0 (budget channel), P2− and P1-concentrated have no world variant with a best-member gain of δ_Y. They are reported as **unmeasured sensitivity**, not as passed controls. <br>• Report power (Clopper–Pearson), P(correct selection), the realised gain of the selected member and the **achieved** oracle gain whenever ±5 % of the target cannot be reached; with fixed members, P2+ diffuse reached only about 0.90 δ_Y in the study (rev-7 m7). These numbers state the screen's sensitivity per node and gate nothing except the N0 STOP. <br>• If n changes at S0.8, S0.6 is re-run at the final n. | container | Calibration table in the pre-declaration |
| S0.7 | **Tuning** (dev seed block; design D2 of the study). <br>• *Static family:* `static:g,h`, **15 configurations**: g ∈ {0, 0.05, 0.1, 0.2, 0.4} σ_cmp,vary × h ∈ {−0.25, 0, +0.25} σ_cmp,vary, on 20 paired dev instances each. g = 0 means "execute every non-rule proposal". m\* is the configuration with the highest mean audited Y. If m\* lands at g = 0.4, extend once to 0.8 on dev, before S0.8. <br>• *Dynamic family:* **4 fixed-size, mean-centred single-channel members** at m\*'s (g, h), on **40** paired dev instances each: budget (b_budget = +1 σ_cmp,vary), information (b_info = +0.5), keep+ (h_budget = +0.5 σ_cmp,vary), keep− (h_budget = −0.5 σ_cmp,vary). π\* is the member with the highest mean audited Y. <br>• Total: 300 + 160 = **460 campaigns per node**. <br>• Flip rate (overall, E1, E2) and the winner's-curse report: **descriptive only**. | per node on its host | m\*, π\*, r̄₁, τ̄, r̄₂, flip rates in the pre-declaration |
| S0.8 | **Pre-declaration**: §3 in full, the S0.5–S0.7 numbers, with σ_D,UCL taken as the maximum of the S0.5b value and the S0.7 dev estimate. **n is final here** (S0.6 is re-run if n changed). Also: the π′ refit rule (full-data refit, λ by inner CV, sha256), the analysis-script hash. Committed **before any S3a or S3e outcome**. | Mac (author commits) | Hash in PLAN §10 |
| S0.9 | **Authorization note** for S3e (evidence) and S3a. | Mac (author) | Note committed |

**Arm-invariance tests (S0.3):**
1. Skip, ghost and controller-only show byte-identical prompts and seeds until the first controller divergence.
2. Ghost leaks no metric or delta to the summariser, the features or the novelty set.
3. The seen-set rules for ghost and controller-only hold.
4. A/A: a fork that takes the root's action reproduces the root.
5. Post-fork worker seeds are keyed by trial and identical across arms, and the editable files are restored after ghost and controller-only runs.

**Mechanical budget check:** an E1 fork at W = 2 on a synthetic node, where skip and ghost must differ by a declared minimum.

## 3. Base controller, policy families, estimands and decision rule (to be pre-declared)

**Units.** Y is the audited terminal metric of the final incumbent, the mean over K = 5 audit seeds from the S3e audit block, in **raw metric units**. This is a declared departure from PLAN:118. Pairing within an instance removes the start level.

**Base controller A2-U** (Bayes-myopic **under a declared model**; it is not the deployed C3 rule):
- **Model.** A hierarchical normal model of the audited increment, with groups (key, sign of the step).
- **Prior.** From S0.4.
- **Update.** The group mean is updated from executed Δ̂ in that group, with the observation variance σ_cmp² multiplied by a declared inflation factor.
- **Predictive sd** τ_pred = √(τ_n² + τ_w²).
- **Rules.** Rule skips as in A2. Index V̂*_n = (1 − π) V(t*; μ_n, τ_pred, σ_cmp). Keep margin m̂_n = the Bayes posterior mean of the increment.
- **Calibration** is gated in S0.5 (iii).

**Policy families** (the action space is unchanged; only the thresholds vary).
- r = runs_left/W − proposals_left/N_cap, from worker runs (H7). proposals_left includes the current proposal, and r is evaluated before the decision; the D1′ test pins this.
- τ_pred,n is A2-U's predictive sd.
- r̄₁ and τ̄ are the means over m\*'s eligible E1 dev decisions; r̄₂ is the mean over its E2 dev decisions. All three are fixed after S0.7.

| Family | Execute iff | Keep iff |
|---|---|---|
| `static:g,h` | V̂*_n ≥ g | m̂_n > h |
| `dynamic:g0,b_budget,b_info,h0,h_budget,r̄₁,τ̄,r̄₂` | V̂*_n + b_info · (τ_pred,n − τ̄) ≥ g0 − b_budget · (r − r̄₁) | m̂_n > h0 − h_budget · (r − r̄₂) |

- **Mean-centring** (rev 7, from the study) gives a member approximately the same average threshold as m\*, which strongly limits wins by a level shift. This is what removed the N0 false positives (26/200 → 4/200 in simulation). The centring is only approximate: the centres are means over m\*'s states, and at g\* = 0 the threshold is clipped, because V̂\* ≥ 0 means members can only skip more. The **matched-static secondary is the guard** against level-shift wins (rev-7 m8).
- **Comparison operators are pinned:** execute uses **≥** (so that g = 0 with V̂\* = 0 executes, as declared); keep uses **>**. Code, analysis notes and tests must agree, with a test at g = 0 (rev-7 m9).
- With b_budget > 0 the execute threshold falls when runs are plentiful.
- Zero coefficients reproduce `static` exactly (tested).

**Primary estimand (S3e; one per decision node).** Fresh instances i = 1…n (S3e block), each run under π\* and under m\* with the same instance seed key and LLM repetition 1. **The exact placebo runs first** (below), so a rare non-determinism stops the track before any primary outcome exists. D_i = Y_i(π\*) − Y_i(m\*). The estimand is mean D, with a one-sided 95 % t-interval.

**Decision rule (one-way screen).** Precedence: A > A-small > no gain found. The decision nodes are the primary nodes that survive the S0.5b fallback. **If no node survives, the outcome is "Track S not run"**, with the reason (rev-7 m4).
- **A:** at least one Holm-adjusted rejection of H₀: mean D ≤ 0 (one-sided, Holm by p-value), and not A-small.
- **A-small:** at least one Holm-adjusted rejection, but UB₉₅ < δ_Y on every node with a rejection.
- **No gain found:** no rejection; UB₉₅ is reported per node with the S0.6 sensitivity statement (§0).

**Margins and sizing.**
- δ_Y = max(0.002, 0.5 σ_node) in raw metric units: digits 0.0033, tabular 0.0020. δ_Y serves the A-small wording and the reported minimum detectable effect.
- **n = 300 fresh instances per node** (rev 7.2; see S0.5b).

**Placebos (S3e).**
- **Exact:** on 10 instances, m\* runs twice with the same repetition, and D must be exactly 0. Any non-zero D is a STOP.
- **Descriptive:** on ≥ 15 instances, m\* runs with a second LLM repetition. The z-score is reported; STOP only if |z| > 3.5.

**Secondary (declared; exploratory; cannot move the route):**
- **Matched static** (rev-5 MA-2): the static rule at π\*'s realised mean effective thresholds on its dev campaigns, run on **all n instances**, with a CI. If it recovers at least half of π\*'s point gain over m\*, the A wording becomes "a threshold-level shift";
- the best member of each other channel, for channel attribution;
- binding shares under m\* and π\*;
- π′ (the fork-learned continuation-aware rule; "one iteration of rollout-based approximate policy iteration");
- m\* vs A2-U at the declared g (the cost of a mis-set price);
- fork-level channel contrasts;
- S4a;
- S1.1;
- the winner's-curse report from S0.7.

## 4. S1 — Benchmarks and controls

| Role | Node | Notes | Host |
|---|---|---|---|
| **Primary 1** | `digits_mlp` | σ_node 0.0066 (fixed split); ≈ 2.5 s per run | TASL-2 |
| **Primary 2** | `tabular_mlp` | σ_node 0.0019 (fixed split); under `vary` its split sd is 0.0123, so n may exceed n_max (it then runs at 300 and the minimum detectable effect is reported) | TASL-7 |
| Synthetic N0 (null), P2+ (keep feedback, δ_Y), P1-diffuse (information, 2 δ_Y); P0, P2− and P1-concentrated documented as not calibratable | in-process worker + scripted manager | §2 S0.6; noise matched to S0.5 | container |
| S1.1 only | `openml_breast_w` | max_iter × C | any CPU |
| Extension (outside the decision) | `autoresearch_linux` | after Track G | — |

**Settings for every phase:**
- `"vary"` split;
- LLM cap 40 and W from S0.5b;
- verify off;
- deployed starts, with trial 1 excluded from forks;
- one pinned GGUF and llama.cpp build;
- memory `append_only_summary` with the deployed skip display;
- each node entirely on its host.

**S1.1 (NF-b):** a 2 × 2 factorial at 30 seeds under `vary`. Pairs: HIDDEN_UNITS × BATCH_SIZE, HIDDEN_UNITS × LR and BATCH_SIZE × LR on the MLP nodes; max_iter × C on breast_w.

## 5. S2 — Hard budget

- **W** is fixed in S0.5b, so that the budget binds in ≥ 50 % of campaigns. This is a declared departure from the deployment's W = 20. If no W binds, the result is reported as "the budget does not bind in this loop". W is then set to the deployment value, 20, and the budget member is dropped from the dynamic family before S0.6.
- **Budget channel.** It is the budget member of the dynamic family. No synthetic world gave it a calibratable gain (S0.6), so its sensitivity is unmeasured.

## 6. S3 — Forks (attribution; secondary) and decision campaigns (S3e); S4 — feedback

**S3a — Forks** (S3a block; F = 150 per node; descriptive).
- **Roots** run under m\*.
- **Fork points:** a uniform sample, plus an oversample at m\*'s thresholds, with IPW weights. Duplicates, no-ops and trial 1 are not eligible.
- **E1 arms:** skip and execute at every fork. On a random third, also ghost and controller-only, with r = 2 on that third.
- **E2 arms:** keep and discard.
- **Channel contrasts:** Δ_B = C_skip − C_ghost; Δ_I = C_ctrl − C_ghost; Δ_F = C_exec − C_ctrl; E2: Q_keep − Q_discard. Here C = Y − immediate, and immediate = 1{kept} × the fresh-seed audited increment over the branch's own incumbent, using the same audit seeds.
- **π′:** f̂ is fitted on total Q differences, with features including V̂*, m̂ and the budget terms. π′ is a full-data refit, then frozen, and enters S3e as a secondary on a declared subset of instances.

**S3e — Decision campaigns:** §3. Matched static runs on all n instances. On a declared subset of 30 instances, also run the other secondaries: the other channels' members (two campaigns), π′, and A2-U at the declared g.

**S4a — Prompt-level display ablation:** unchanged. A campaign-level display comparison runs only if S4a shows a divergence.

**Cut:** U_split, S3c, the online S3d as a separate phase, and the DP candidate (the budget member replaces it).

## 7–8. (Merged into §6; S5 moved to C3.)

## 9. Hosts, cost and schedule

**Hosts (R1-TRACKS-HOST, -2).**

| Host | Work | Priority |
|---|---|---|
| TASL-2 (zhixu portal) | `digits_mlp`: S0.1, S0.4, S0.5, S0.7, S3a, S3e, S4a | Track X evidence first |
| TASL-7 | `tabular_mlp`: same | Track P evidence first |
| container / Mac | code, S0.6, analysis, S1.1 for breast_w | — |
| deepthought | none | — |

**Cost per node** (LLM calls; ≈ 40 calls per campaign is an **upper bound**, since a binding W ends a campaign early; worker runs and K = 5 audits run on the host CPUs in parallel with the LLM):

| Item | Count | Calls |
|---|---|---|
| S0.4 | 10 campaigns | ≈ 0.4k |
| S0.5 | 60 campaigns + 30 forks | ≤ 3.0k |
| S0.7 | 15 × 20 + 4 × 40 = 460 campaigns | ≤ 18.4k |
| S3a | 150 forks × ≈ 4 leaves × ≈ 20 calls, plus E2 | ≈ 14k |
| S3e | 3n (π\*, m\*, matched static) + 25 placebo + 30 × 4 secondary campaigns, n = 300 | ≤ 41.8k |
| S4a | — | ≈ 1k |
| **Total** | | n = 300: ≤ 79k (+ ≈ 2.4k if the g = 0.8 extension fires) |

**Wall time per node.** Worker runs are serial inside a campaign: about W runs plus 5 audits, ≈ 40 s of CPU per campaign on digits. Running at least 2 campaigns per LLM server interleaves CPU and LLM time, so the LLM stays the bottleneck while there are enough CPU cores. Wall ≈ calls × L / 2 servers:

| Latency L | n = 300 per node |
|---|---|
| 1.5 s | ≤ 17 h |
| 3 s | ≤ 33 h |
| 7 s | ≤ 77 h |

The tabular per-run time is measured in S0.1/S0.5. If it exceeds ≈ 10 s, CPU becomes the bottleneck, and the S0.5b projection uses the CPU time.

**Fallback:** decided only at S0.5b, from projections (§2). Pre-emption by Track X or Track P pauses a node; it never drops a node after outcomes exist.

**Schedule (realistic):**

| Step | Time |
|---|---|
| S0.3 code, review and fixes | 3–5 days |
| S0.1–S0.5, S0.7 | 1.5–2.5 days per host |
| S0.6 | hours |
| Pre-declaration and authorization | author |
| S3a + S3e | 1–2 days per host |

If both hosts stay free, the decision falls at **≈ 15–23 Nov**.

## 10. STOPs and limitations

**STOP** if any of these happens:
- the S0.1 identity check fails;
- any invariance, mechanical or fixture test fails;
- the S0.5 calibration gate fails twice;
- S0.6 N0 route-A count ≥ 19 of 200;
- the exact placebo gives D ≠ 0;
- the descriptive placebo gives |z| > 3.5;
- a node fails D28 liveness;
- a fork's controller rebuild differs from the root.

**Limitations (stated in any write-up):**
- **One-way screen.** Track S cannot show that the loop is one-step. "No gain found" bounds π\* only, and its sensitivity is the per-node S0.6 power. In the FIXTURE S0.6 run with the final simulator (trial 1 aligned with the harness; analysis commit `d82496e`) at n = 300, **only P2+ concentrated calibrated**: 1.04 δ_Y, power 0.86 [0.80, 0.90], P(correct member) 0.90, N0 at 2/200. **P2+ diffuse** reached at most 0.80 δ_Y and **P1-diffuse** at most 0.56 × 2 δ_Y, so neither calibrated and both are unmeasured, as are the budget channel and P2−. A "no gain found" result therefore rests on a single calibrated control. The budget channel and negative keep feedback are unmeasured.
- **Policy class.** Every conclusion is restricted to the declared four-member dynamic family and its tuning budget. π\* is "a tuned parametric dynamic threshold, selected among four fixed-coefficient single-channel members", not a learned DAC policy. A richer dynamic policy might find gains this family misses. The S0.6 power covers only the calibratable controls: keep feedback at δ_Y and information at 2 δ_Y.
- **Base controller.** A2-U is a declared Bayes-myopic model, not the deployed C3 rule.
- **Instances** are seeds of two CPU nodes with one 7B proposer.
- **Noise** is frozen within a campaign.
- **Budget.** W is chosen to bind, so it departs from the deployment.
- **Verify** is disabled.
- **Arms.** The ghost and controller-only arms are instruments, not policies.

## 11. Review record

**Revisions 1 → 4:** see the earlier reviews and the revision-4 §11.

**Revision 4 → 5** (`reviews/TRACK_S_REV4_REVIEW_20261029.md`):

| Finding | Severity | Resolution in revision 5 |
|---|---|---|
| BL-1: a weak π′ makes B automatic; the S0.6 guard is circular | BLOCKING | The primary candidate is now a **tuned dynamic family**, tuned by value with the same budget as the static rule. The static member is excluded from π\*. B requires a flip rate ≥ 10 % and S0.7 power LB ≥ 0.6, with P1 and P2 gains **fixed at δ_Y in advance** (diffuse and concentrated variants) and noise matched to an S0.5 fork pilot. B is worded with the family and the tuning budget. π′ becomes secondary (§2, §3) |
| BL-2: FPR gate, power multiplier and placebo fail by construction | BLOCKING | STOP only on a **significant** FPR excess (≥ 18 of 200). n uses 2.90 σ_D,UCL. Exact same-repetition placebo; the different-repetition placebo is descriptive, with STOP at |z| > 3.5 (§2, §3) |
| MA-1: m\* selection not executable; order | MAJOR | Explicit order S0.4 → S0.5 (W = cap, truncation) → S0.5b → S0.6 on-policy tuning campaigns per configuration → S3. m̃ dropped. Disjoint seed blocks (§2) |
| MA-2: A and B both hold | MAJOR | A takes precedence; the **A-small** outcome is treated like B for the headline (§0, §3) |
| MA-3: σ_D sizing | MAJOR | ≥ 20 pairs; 80 % UCL; n_max = 300; nodes above n_max support A only; cost rows for σ_D = 0.02 (§2, §3, §9) |
| MA-4: π′ must nest m\* | MAJOR | π′'s features include V̂*, m̂ and the budget terms, with a nesting test. The primary family nests static by construction (§2, §3) |
| MA-5: no test of "budget alone" | MAJOR | The b_info = 0 secondary (§3) |
| mi-1: seed keys and blocks | MINOR | Instance-level seed key; five disjoint blocks plus an S3e audit block (§2) |
| mi-2: cost formula | MINOR | Cost table redone (§9) |
| mi-3: S1.1 pairs | MINOR | Fixed (§4) |
| mi-4: calibration gate details | MINOR | Stratified, audit noise included, ≥ 100 predictions, declared g (§2) |
| mi-5: verify | MINOR | Verify off for all policies (§2) |
| mi-6: deployed π′ | MINOR | Full-data refit, λ by inner CV, sha256 (S0.8) |
| mi-7: fallback timing | MINOR | Decided only at S0.5b; pre-emption pauses (§2, §9) |
| mi-8: interval type | MINOR | One-sided 95 % t-intervals (§3) |
| mi-9: over-engineering | MINOR | U_split, S3c, separate S3d and DP cut; F reduced to 150 (§6) |

**Revision 5 → 6** (`reviews/TRACK_S_REV5_REVIEW_20261029.md`):

| Finding | Severity | Resolution in revision 6 |
|---|---|---|
| BL-1: the budget term points the wrong way; no budget control; N0 not null once fixed | BLOCKING | Threshold g0 − b_budget · r with b_budget > 0, plus a unit test on D1′; h_budget two-sided; positive control P0 for the budget channel; nulls defined by zero oracle gain (N0 at non-binding W) (§2, §3) |
| MA-1: selection noise; the gate can only fail after tuning | MAJOR | The same paired dev instances for every configuration; the dynamic family cut to 4 single-channel members; S0.6 calibration moved **before** tuning, with one pre-declared resize (20 → 40); synthetic noise matched to the campaign-level σ_D (§2) |
| MA-2: A may be a static shift | MAJOR | Two-sided h grid; b_info multiplies τ_pred (varies within a campaign, no indicator); matched-static secondary, with "threshold-level shift" wording if it recovers ≥ half the gain (§3) |
| MA-3: σ units from the wrong split | MAJOR | Grids in σ_cmp,vary from the pilot; δ_Y stays the pre-declared substantive margin (§2) |
| MA-4: B undefined when one node is A-only | MAJOR | B is decided and worded per B-eligible node (n ≤ n_max); needs at least one (§3) |
| mi-1: flip-rate definition | MINOR | Defined on π\*'s dev states, eligible decisions only (§2 S0.7) |
| mi-2: Holm for A-small; precedence | MINOR | Holm-adjusted rejections; A > A-small > B > inconclusive (§3) |
| mi-3: σ_D at the chosen W | MINOR | Recomputed from truncated ledgers; maximum with the S0.7 dev estimate before S0.8 (§2) |
| mi-4: placebo order | MINOR | The exact placebo runs first (§3) |
| mi-5: costs | MINOR | Calls per campaign marked as an upper bound; S0.3 3–5 days; table updated (§9) |
| mi-6: the all-zero member | MINOR | No longer exists: the dynamic family has only non-static members (§2) |
| mi-7: binding share | MINOR | Reported in S3e (§3) |
| mi-8: DAC wording | MINOR | "Tuned parametric dynamic threshold" (§10) |

**Revision 6 → 6.1** (`reviews/TRACK_S_REV6_REVIEW_20261029.md`, ACCEPT WITH MINOR CHANGES). All ten minor items applied:

| Item | Resolution |
|---|---|
| 1. Static g grid narrowed | Restored g = 0.4, with one pre-declared extension to 0.8 if m\* lands on the edge (S0.7) |
| 2. Power-gate scope | Per B-eligible node in S0.6 too, as in §3 |
| 3. Oracle gains | Large-replication evaluation (10⁴ campaigns per member, ±5 % of δ_Y); N0 ≤ 0, P's = δ_Y (S0.6) |
| 4. S3e cost; resize in the totals | Cost rows and totals recomputed (§9) |
| 5. n final at S0.8 | n and B-eligibility frozen at S0.8; S0.6 re-run if n changes |
| 6. P(CS) and false-B rate | Reported in S0.6; synthetic between-configuration sd matched to the pilot |
| 7. r convention | proposals_left includes the current proposal, evaluated before the decision; pinned in the D1′ test (§3) |
| 8. Truncated-incumbent audits; wall time | K = 5 audits in S0.5b; wall time recomputed with serial in-campaign worker runs (§9) |
| 9. Matched-static CI | Matched static runs on all n instances, with a CI (§3, §6) |
| 10. Wording; no-binding case; flip-rate split | π\* "selected among four fixed-coefficient single-channel members"; W = 20 if none binds (§5); flip rate split into E1 and E2 (S0.7) |

**Revision 6.1 → 7** (S0.6 design study, `ANALYSIS_NOTES.txt`, FIXTURE; author decision 29 Oct):

| Finding of the study | Resolution |
|---|---|
| N0 gave route A 26/200 times: the lowest static g was above the N0 optimum, so members won by a level shift | g = 0 added to the static grid; dynamic terms mean-centred (N0 → 4/200) |
| No affordable design passed every control; P(B) ≤ 0.13 even under a true null, because centred members agree with m\* on 90–95 % of decisions, which defeats the flip gate | **Route B removed; Track S is a one-way screen** (author, 29 Oct). The flip rate is descriptive |
| P0, P2− and P1-concentrated: no world variant with a calibratable best-member gain of δ_Y | Reported as unmeasured sensitivity; not used as controls |
| Magnitude grids and racing did not beat 4 fixed members with more dev instances | Design D2: 15 static × 20 + 4 members × 40 = 460 campaigns |
| Multiplier | 2.93 = z₀.₉₅ + z₀.₉₀ (≈ 83 % power under Holm with one null node); N0 STOP at ≥ 19 of 200 |
| The info member is harmful in P1 (the τ bonus also rewards large noisy follow-ups) | Kept as declared. Reason (corrected in 7.1, rev-7 review q4): fitting a member to a planted synthetic mechanism would be circular and would inflate the claimed sensitivity. Dilution costs almost nothing, because a member at about −5 δ_Y is almost never selected. Consequence: the information channel is effectively unprobed, and a null result for the info member says nothing about the channel |

**Revision 7 → 7.1** (`reviews/TRACK_S_REV7_REVIEW_20261029.md`, ACCEPT WITH MINOR CHANGES; 0 BLOCKING, 0 MAJOR, 12 MINOR). All applied:
- m1, m2: leftover route-B wording removed (§0, §4).
- m3: the analysis code is reduced to the three outcomes, with a test, before the S0.8 hash (S0.3).
- m4: "Track S not run" if no node survives.
- m5, m6: "no gain found" bounds π\* only and is not an equivalence result; it is printed next to the flip rate and P(correct member).
- m7: per-node sensitivity, and the achieved oracle gain is reported.
- m8: centring described as approximate; matched static is the guard.
- m9: operators pinned (≥ execute, > keep), with a test at g = 0.
- m10: multiplier relabelled.
- m11: S0.6 matched to the pilot, then re-run after S0.7.
- m12: cost row and g = 0.8 extension.
- q4: the info-member rationale is corrected.

**Revision 7.2 → 7.3:** the simulator's trial 1 is aligned with the harness (never rule-detectable, kept without comparison). The final FIXTURE S0.6 run at n = 300 calibrates only P2+ concentrated (power 0.86); P2+ diffuse and P1-diffuse do not calibrate. The sensitivity statements are updated (§10). The world designs for P2+ diffuse and P1 may be revisited before S0.8, but only to make them calibratable; the runbook's rules do not change.

**Revision 7.1 → 7.2** (FIXTURE S0.6 run under the 7.1 rules; `scratchpad/s06_v71*`). At the formula's n = 110 for digits, P2+ power was 0.43 / 0.54 and P1-diffuse could not be calibrated. At n = 300, P2+ power was 0.75 / 0.92, with N0 at 1/200. **S3e n is therefore fixed at 300 per node**, and the formula only reports the minimum detectable effect. The final S0.6 is still re-run with pilot-matched noise before S0.8.

The runbook is accepted. Next: the S0.3 code acceptance and the author's decisions (S0.2, D10).

