**AI-assisted (Claude, chat session, 22 Nov 2026; subagent). DRAFT; not signed; not reviewed.**

# D.3 closed loop on T0 — pre-declaration of both stages (D.3a rule arms, D.3b learned arms) — DRAFT

Drafted by a subagent of the coordinating chat. Tier E (R1-PROCESS-TIERS): before signing it needs a committed independent review re-checked until it
writes "accepted". It decides nothing on its own. Every value below carries its source (a PLAN row, a signed note or a
file with its path); a value with no source on `main` is marked **proposed**, with its reasoning, and is fixed only by
the author's signature. Written on branch `mac-d3-predecl-20261122` over `author-minsub-20261122` @ `d9acb501`
(PLAN.md sha256 `75b5ae36afec1a36e233bf85d3b2e114b0d1134fc32e39c6feaf9e5ebec5b47b`). No label, test-partition or
evaluation-value file was opened to write it.

**What it implements.** R1-D3-MIN (one pre-declaration for both stages, committed with its hash before any D.3 run
starts; RUNBOOK §1 "Pre-declaration") as amended by R1-MINSUB-CHOICES (4) (six D.3a arms, the values listed there,
deepthought CPUs as the D.3 audit host). It replaces nothing: no PLAN row, preregistration, signed note or code guard is
changed. Where a row cannot be implemented as written, the point is listed in §13, not fixed here.

**How it becomes binding.** (1) Independent review accepted; (2) the author fills §13's choices and signs; (3) the
coordinating chat fills the sha256 placeholders of §14 that exist at signing (the A1/A2/LADDER constants file, §5.0),
sets `frozen: true`, and commits it; (4) its sha256 is written into the D.3a authorization note
(`D3A_AUTHORIZATION_DRAFT_20261122.md`) and into every D.3 outcome table header (§8). No D.3 campaign starts before (4).

---

## 1. Scope

| Item | Value | Source |
|---|---|---|
| Stages | **D.3a**: six rule arms, not conditional on the gate. **D.3b**: learned arms A3 and A5 (A6 only if it enters under RUNBOOK P.5), only if the gate passes. | R1-D3-MIN; R1-MINSUB-CHOICES (4) |
| Tier | T0 only; no T1 or T2 node | R1-D3-MIN; R1-SUBMISSION-CUTS |
| Proposer | `gemma4_31b`, thinking off (the Track X pick) | R1-D3-MIN; R1-MAIN-PROPOSER |
| What D.3a may read | the sweep-2 **dev label block** (through the A1/A2/LADDER constants, §5.0), the pinned noise source, the node specs; **no test label, no evaluation value, no T1 label** | R1-D3-MIN |
| What D.3 outputs may be used for | nothing that trains, tunes or selects any arm | R1-D3-MIN |
| Repetitions | **one** (rep 0) required; a second is optional | R1-D3-MIN. Whether rep 1 is run is fixed at signing (§13 item 3); default in this draft: not run |

## 2. Fixed design

| Item | Value | Source |
|---|---|---|
| T0 node set | `digits_mlp`, `openml_breast_w`, `openml_climate`, `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `tabular_mlp` (seven) | R1-D3-MIN ("the PRE-WDBC primary set unless it says otherwise"); preregistration PRE-WDBC B and R1-S2C3B-WDBC (the seven nodes that passed S2-C3b at the sweep-2 launch commit; `openml_wdbc` failed only D28 `invalid_rate`, `SWEEP2_REPORT_20261121.md`). `openml_wdbc` is not run in D.3 (§13 item 6) |
| Memory mode | `append_only_summary` only | R1-MINSUB-CHOICES (4) |
| Run budget W | 20 worker runs per campaign, every arm; replicate and verify runs count | R1-MINSUB-CHOICES (4) ("as in sweep 2"); run accounting `r1/c3/accounting.py` (verify charged 2r) |
| LLM-call cap | **80 per campaign, every arm — proposed** (§3) | none on `main` (R1-MINSUB-CHOICES (4)); proposed here |
| Trial budget | equal to the LLM-call cap, so it never binds | `r1/c3/control.py` `c3_budgets` (review F6, D1) |
| Instances | 18 per node, the same 18 instance seeds on every node, 126 instances in all (§4) | R1-D3-MIN; R1-MINSUB-CHOICES (4) |
| Split policy (verify) | `vary` | PLAN §10 "Verify split policy"; sweep-2 authorization |
| Proposal schema | structure-only `manager_proposal/v1`, temperature 0.2 with the D26 seed | sweep-2 authorization ("Workers/training") |
| Server | `-c 32768 -ngl 999 -np 1`, `--jinja`, `--chat-template-kwargs` exactly `{"enable_thinking":false}`, q8_0 K/V, `cache_prompt` false on every call | sweep-2 authorization ("Server"); R1-SWEEP2-SETTINGS (1); R1-CACHEPROMPT-FALSE |
| Model file | `google_gemma-4-31B-it-Q4_K_M.gguf`, sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` | sweep-2 authorization ("Pick/model") |
| Image (proposer job) | v1 GPU image `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`, one digest for both stages | R1-SWEEP2-IMAGE (sweep 2's digest); keeping it for D.3 is **proposed** so that A0 is the sweep-2 design on fresh instances. D.3b's A5/A6 sidecar needs PyTorch/PEFT, which v1 is not recorded to carry: §12 gap G9 |
| Harness | `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (the sweep-2 pin) unless an arm needs a harness change (§12 gaps G3, G4); then a new reviewed pin, named in the D.3a note, with the audit equality check of §7.2 against it | sweep-2 authorization ("Harness/paper") |
| Proposer host | HTCondor, a GPU model with a measured D.3 chunk time (§11), not the TASL pair; one GPU model for both stages | R1-D3-MIN ("Hosts"); R1-SWEEP-HOST-HTC; R1-SWEEP2-MEASURED-GPU (H200 measured for sweep 2 only) |
| Worker runs | CPU of the proposer job, as in sweep 2 ("T0 worker training is CPU; the GPU affects proposal generation only") | sweep-2 authorization |
| Skip display | `one_line/v1`: a control-plane skip shows as one line, no metric; recorded in every manifest | R1-SKIP-DISPLAY; `r1/c3/control.py` `SKIP_DISPLAY` |
| Run price g | 0.1 σ_node (no sensitivity value in D.3) | PLAN §10 "g (22 Oct)"; `r1/c3/offline_eval.py` `G_PRIMARY` |
| Noise constants | σ_node, σ_cmp (local / structural), δ_n by `r1.c3.dataset.noise_table` on `results/r1/noise/D28_REPAIR_20261027/summary.json`, sha256 `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310` | preregistration PRE-DELTA and §1 "Noise source" |

## 3. The LLM-call cap — proposed: 80 per campaign (= 4 W), equal for all arms; fixed by the author's signature

**Why a cap matters here.** Sweeps 1 and 2 executed every proposal, so no proposal was ever skipped and no cap bound
(R1-MINSUB-CHOICES (4)). The sweep driver passed a trial budget of 2 W = 40 (`r1/headroom/e1b_collect.py`, `_run_root`:
`budget=runs * 2`, `ComputeBudget(max_worker_runs=runs)`); sweep 2 used 5,796 LLM calls for 5,760 trials
(`SWEEP2_REPORT_20261121.md`, `collection_counts.json`), about one call per trial. In D.3 the arms differ in how many
proposals they spend per run: A2 (and A3/A5/A6) skip rule-detected duplicates and no-ops, which costs a call and no run
(RUNBOOK H.4); FIXR3 and EGATE spend several runs per proposal. With a cap that binds, a skipping arm would end before
W and the arms would no longer be matched on runs, which is the comparison C3_DESIGN §6 states ("matched W = 20 runs
and matched LLM-call cap").

**Evidence on how many calls a skipping arm needs for W = 20 runs.**
1. *Sweep 2 (the D.3 proposer, both memory modes pooled).* 2,512 of 5,760 trials were duplicates (B.2 counts:
   2,512 duplicates, 2,500 eligible, 0 no-ops, 5,012 proposals; `reports/s2_audit_20261121/PRECONDITION2_20261122.md`;
   the other 748 trials are the 288 first trials and the 460 worker failures, `SWEEP2_REPORT_20261121.md`). If the
   proposal law did not change under skipping, A2 would execute 1 − 2,512/5,760 = 0.564 of its trials and need
   20 / 0.564 ≈ 35.5 calls. The per-mode split is not on `main`, so the `append_only_summary` value is unknown.
2. *Track X B1/B2 (same proposer, memory on, W = 20).* The pick's replayed-repeat share was 0.054 in B2 and at most
   0.125 in B1 (`reports/X7C_APPENDIX_20261116.md` §2), so with memory on the duplicate share may be much lower than the
   pooled sweep-2 value.
3. *Track S S0.5 (the 7B proposer, duplicates skipped, LLM cap 40, worker budget 40).* Every campaign ended at the 40-call
   cap; worker runs used 11–27 (digits) and 14–22 (tabular); E1 executed 318 of 747 and 350 of 749 decisions (per
   instance 0.28–0.68 and 0.35–0.57); 53 and 51 of 800 calls were invalid proposals
   (`reports/TRACKS_S05_SUMMARY_20261115.md` §4). At the worst per-instance execute share (0.28 of E1 decisions, about
   0.26 of calls) a skipping arm needs about 20 / 0.26 ≈ 77 calls for 20 runs.
4. *Precedents for 4 W.* Track X B1 ran with W = 20 and an author-bound LLM-call cap of 80 (R1-EXAM-B1-TRUNCATION-INVALID,
   "budgets (W = 20, LLM-call cap 80)"; `r1/exam/campaign.py` passes it as `ComputeBudget(max_llm_calls=...)`); the
   Track H dry run uses a cap of 4 W (`r1/scripts/c3_control_dryrun.py` `LLM_CAP = 4 * W`).

**Proposal.** Cap = 80 calls per campaign for every arm (every proposal, every D25 revision and every controller call
counts; `r1/c3/accounting.py`), trial budget = 80. Reasoning: with 80, W rather than the cap ends a skipping arm's
campaign unless fewer than about a quarter of its calls lead to a run, which covers both the pooled sweep-2 duplicate
share (≈ 35.5 calls expected) and the worst per-instance share seen under skipping in Track S (≈ 77 calls); a cap of 40
(the sweep trial budget, Track S's cap) would already bind at an execute share below one half. Cost: a campaign that
skips almost everything holds the GPU for up to four times as many calls as an A0 campaign (§11 worst case). The arms
that never skip (A0, A1 unless its constant screen skips, FIXR3, EGATE, LADDER) are unaffected. The analysis reports,
per arm, how many campaigns the cap ended (`ended_on`, §8). The value is in `r1/c3/d3_analysis.py` (`LLM_CALL_CAP`); a
different signed value changes that file's sha256, which §9 then re-pins.

## 4. Instances and seeds — proposed blocks, disjoint from every namespace in the repository

### 4.1 The declared seeds

| Use | Seeds | Rule |
|---|---|---|
| Deployment instances | **6201–6218** on every node | instance id `<node>__s<seed>` (seed in decimal, no padding; the gate's and split file's format, `r1/c3/p3_split.py`). 126 instance ids: `digits_mlp__s6201` … `digits_mlp__s6218`, `openml_breast_w__s6201` … `__s6218`, `openml_climate__s6201` … `__s6218`, `openml_credit_approval__s6201` … `__s6218`, `openml_ionosphere__s6201` … `__s6218`, `openml_sonar__s6201` … `__s6218`, `tabular_mlp__s6201` … `__s6218`. Instance index i = seed − 6201 (0–17) |
| Worker seed of every in-campaign run | train seed = split seed = the instance seed | as sweeps 1 and 2 (`e1b_collect._run_root`: `LocalWorker(..., train_seed=seed, split_seed=seed)`), so candidate and incumbent are compared on one common seed |
| Replicate runs (FIXR3, EGATE) | replicate j = 1…9 of instance i: **6500 + 10 i + j** (6501–6679); replicate j = 0 is the instance seed | every configuration of a campaign is replicated on the same seed list, so the incumbent's replicates exist when a candidate needs them |
| Proposer seed | D26: `manager_seed(campaign_id, budget_index, repetition, revision_attempt)`, sent as the llama.cpp request seed; the harness `campaign_id` is the **instance id**, the same for every arm; repetition 0 (rep 1 → 1) | `e1b_collect.seed_policy` ("llamacpp_seed"); RUNBOOK A.10. With the same instance id and seed stream, every arm sees the same first prompt and seed, so arms are paired until their first different decision (H200 runs are deterministic, R1-SWEEP2-RTE-DIAG) |
| Audit of Y | audit seed k = 1…10 of instance i: **6700 + 10 i + k** (6701–6880), shared by every arm and repetition on that instance, outside the campaign budget | PLAN §4 "Outcome" (common seeds across arms); per-instance blocks so that one audit error does not recur across instances (the Track S rule, `TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` "Seed blocks") |
| KG verify of A1/A2/A3/A5/A6, if it fires | the harness's `vary` verify seed derivation | not visible in this repository (§13 item 12) |

### 4.2 Disjointness

Checked by `r1.c3.d3_analysis.check_namespaces()` (`python -m r1.c3.d3_analysis namespaces`; test
`r1/tests/test_d3_analysis.py::NamespaceTest`), which refuses any overlap between the three D.3 blocks or with:

| Reserved namespace | Seeds | Source |
|---|---|---|
| Sweep 1 and 2 instance seeds = the P3 T0 split universe | 100 + 10 k + (Σ ord(node) mod 7), k = 0–17: values within 100–276 | `e1b_collect._instance_seed`; `p3_split.t0_instance_seed` (tested copy); preregistration PRE-SPLIT A |
| T1 G.5 instances = the P3 T1 split universe | 5101–5112 | `p3_split.T1_SEEDS`; PRE-SPLIT A |
| B.2 audits (sweeps 1, 2; T1) | 7001–7010 | `r1/c3/audit.py` `DEFAULT_SEEDS`; R1-B2-DECOUPLE |
| Exam (Stage A/B instances 9001–9099, audits 9101–9299; B2 instances 9011–9014, audits 9201–9210) | 9001–9303 | `r1/exam/namespace.py`; `sweep2/s2_c3b_lib.py` `EXAM_SEED_BLOCK`; R1-EXAM-B2-POWER-PLAN |
| G.1b proposed block | 8001–8010 | RUNBOOK G.1b; `sweep2/s2_c3b_lib.py` `G1B_SEED_BLOCK` |
| D21 noise floors (T0 and T1) | 1001–1030, 2001–2030, 3001–3030 | `r1/noise/e1_noise_floor.py` `SEED_BASE`; `r1/scripts/build_d28_noise_summary.py`; `authorizations/g1b_t1_tasl_20261121.md` |
| G.4 pilot | 4001–4003 | `authorizations/g4_t1_tasl_20261122.md` |
| E1b pilot audits | 5001–5006 | `e1b_collect.AUDIT_SEED_BASE`; R1-E1B-RERUN2 |
| S2-C3b prompt measurement | 6101–6108 | `sweep2/s2_c3b_lib.py` `PROMPT_MEASUREMENT_SEEDS` |
| Track S instances; audits | 30000–39999; 100000–799999 | `r1/tracks/collect.py` on branch `trackS-ops-20261030` |
| Engineering smoke | 999 | `r1/e2e.py` |

In addition, `git grep` over every local and remote ref found no instance id `__s<seed>` with a seed in any D.3 block
(22 Nov 2026). The S2-C3b liveness reused sweep instance seeds (R1-S2C3B-SEEDS); those lie in 100–276.

## 5. D.3a arms (six; R1-D3-MIN as amended by R1-MINSUB-CHOICES (4))

Common to all six: the design of §2, the seeds of §4, the run and call accounting of `r1/c3/accounting.py` (worker runs =
trials whose worker ran, plus replicate runs, plus 2 r per verify; LLM calls = every proposal, revision and charged
controller call). A trial whose proposal fails the harness precheck costs its call and no run. The first valid trial of
a campaign is kept without comparison (harness behaviour; `TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` B5) in every arm.
A campaign ends when W runs are spent (`ended_on = worker_runs`), when the cap is reached (`llm_call_cap`), or, for
FIXR3 and EGATE, when the runs left cannot fund the next replicate step (`no_fundable_candidate`).

### 5.0 The constants file (A1, A2, LADDER) — pinned at signing

One reviewed fitter (§12 gap G2) reads only the **receipted sweep-2 train/dev partition** released under
R1-S2-LABELS-TRAINDEV-RELEASE (release step `r1/c3/release.py`), selects the **dev** instances of the seven nodes by the
P3 split file (`r1/c3/splits/c3_p3_split_v1.json`, sha256 `b5967dd7…e569`), and writes one JSON file with, per node:
A1's and A2's fitted bin vectors and `prior_model.arm_digest`, the LADDER η and its search table, the σ values used, and
the input receipts' sha256s. Its sha256 is entered in §14 at signing. Rules:
- **Population (PRE-A2 C):** the full dev population of sweep 2 (both memory modes, all labelled proposals; duplicates
  have no label and do not enter), as `r1/c3/gate_input_builder.py` `_fit_a2` fits A2 for the gate. A test shows the
  fitter's per-node A2 vectors equal `_fit_a2`'s on the same rows. The comparison is per node, not by `arm_digest`: the
  gate's fit also covers T1 nodes, which changes the pooled vector, and the pooled fallback is never used here. A D.3
  node without a labelled non-inert dev proposal has no constant and is a STOP (as `_fit_a2` refuses it). Sweep 1 does
  not enter (PRE-A2 C: "A2 uses sweep 2 only").
- **Labels:** soft labels v2 (R1-SOFT-SIGMA: N(Δ_label, s²), s = σ̂_node/√5) from the label seeds 7001–7005 only.
- The arms-frozen record must carry exactly these per-node A1 and A2 constants for the seven nodes (R1-D3-MIN: "they …
  enter the arms-frozen record unchanged"); a different vector there is a STOP (§10).

### 5.1 A0 — Karpathy default (R1-BX-D7; C3_DESIGN §5 prac-1)

- **Rule:** execute every proposal, one run, keep iff Δ̂ > 0 (harness keep rule `default/v1`, no controller, no
  verify). This is the sweep-2 campaign design (`--new-campaign-versions`, `vary`), so A0 is renamed the Karpathy
  default, not duplicated (R1-BX-PROPOSED-CONFIRM (D7)).
- **Constants:** none. **Reads:** nothing beyond the campaign. **Charged:** one run per executed trial.
- **Implementation:** `e1b_collect.run_root` runs this design but hard-codes the sweep instance-seed law and
  `budget = 2 W` and sets no LLM cap: needs changes (§12 G1).

### 5.2 A1 — C2 index policy with a constant prior (D23; C3_DESIGN §5; R1-A1-VERIFY)

- **Rule:** at E1, from the node's constant forecast (π, μ, τ): execute iff (1 − π)·V(t*; μ, τ, σ_cmp) ≥ g
  (T4 Proposition 8, `rules.execute`); at E2 keep iff Δ̂ > t* = −μ σ_cmp²/τ² (Proposition 6, keep rule
  `bayes_threshold/v1` served from the same forecast); D23 KG verify with r = 2 (each verify charged 2 r = 4 runs), which
  R1-A1-VERIFY keeps although it is predicted not to fire at g = 0.1 σ_node when σ_cmp ≤ σ_node. No rule layer: duplicates
  are executed.
- **Constants:** A1's per-node bin vector from §5.0 (`arms.ConstantPrior`), moments by `labels.moments` with τ floor
  0.15 σ_node (`arms.TAU_FLOOR_Z`); σ_cmp per edit kind and σ_node from §2's noise constants.
- **A consequence to report, not to repair:** with a constant prior the E1 screen takes the same decision for every
  proposal on a node (R1-MINSUB-CHOICES (4) says this of the Ladder arm). If it skips on a node, A1's campaigns there end
  at the cap with no run and Y = 0. With sweep 2's 0 no-ops (π ≈ 0 for soft labels of non-no-op proposals,
  `labels.soft_label` puts no mass on the no-op bin) A1's constant equals A2's, and A1 differs from A2 only in executing
  duplicates.
- **Reads:** the constants file and the noise constants; no label at run time. **Charged:** runs and verify runs.
- **Implementation:** `r1/c3/control.py` `RuleController` with `prior_model.TableArmPrior(A1)` (`rule_layer` false for
  A1) and `c3_budgets(W, cap)`: usable as is for the decisions (exercised only in the Track H DRYRUN); the D.3 runner is
  missing (§12 G1).

### 5.3 A2 — A1 plus the rule layer (C3_DESIGN §5; D25, D27; PRE-A2 C)

- **Rule:** at E1 skip rule-detected no-ops and duplicates first (`skip_reason` `rule_noop` / `rule_duplicate`; the
  skipped proposal shows as one line, R1-SKIP-DISPLAY); for the rest, A1's screen, keep threshold and KG verify with A2's
  constant (`arms.RulesPrior`).
- **Constants:** A2's per-node bin vector from §5.0. **Reads:** as A1. **Charged:** a skip costs its call, no run.
- **Implementation:** `RuleController` + `TableArmPrior(A2)`: usable as is; runner missing (G1).

### 5.4 FIXR3 — fixed-r replication + test (R1-BX-D7; C3_DESIGN §5 prac-2)

- **Rule:** every executed proposal is run r = 3 times, on replicate seeds j = 0, 1, 2 of its instance (§4.1); keep iff a
  one-sided Welch t-test of mean(candidate) > mean(incumbent) rejects at α = 0.05, the incumbent's three runs being its
  own replicate runs on the same seeds (they exist because every configuration is replicated on the same list). The first
  valid trial is run three times and kept without a test. A candidate whose first replicate fails is invalid and costs
  one run. When fewer than 3 runs are left the campaign ends (`no_fundable_candidate`), so at most 1 + 5 proposals are
  executed (3 + 15 = 18 runs).
- **Constants:** r = 3, one-sided Welch test at α = 0.05, replicate runs counted against the budget
  (R1-BX-PROPOSED-CONFIRM (D7), confirming R1-BX-D7's proposed values). No rule layer, no screen.
- **Reads:** nothing beyond the campaign. **Charged:** all 3 runs of every executed proposal.
- **Memory display (proposed):** the trial's line shows the mean of its replicate metrics and the decision (§13 item 15).
- **Implementation:** missing (§12 G3).

### 5.5 EGATE — anytime-valid commit gate (PACE-style; PLAN §5 required list; R1-D3-MIN)

- **Rule (proposed construction):** for a candidate, paired differences d_j = m(candidate, seed j) − m(incumbent, seed j)
  on replicate seeds j = 0, 1, … (§4.1), oriented so that larger is better; S_n = Σ_{j<n} d_j, x_n = S_n / σ_cmp. The
  e-process is the one-sided normal mixture
  E_n = 2/√(n+1) · exp(x_n² / (2(n+1))) · Φ(x_n / √(n+1)),
  the mixture over λ ≥ 0 (half-normal weight) of exp(λ x_n − λ² n / 2). Under H0: E[d] ≤ 0 with σ_cmp-sub-Gaussian d_j it
  is a non-negative supermartingale, so by Ville's inequality the probability that it ever reaches 1/α is at most α.
  **Commit (keep) iff E_n ≥ 1/α = 20** for some n ≤ r_max; **discard** as soon as S_n ≤ 0, or at n = r_max without
  commit, or when the runs left cannot fund the next step. Discarding early only lowers the commit probability, so the
  α bound holds. Step j runs the candidate at seed j and, if the incumbent has no run at seed j, the incumbent too.
  The first valid trial is kept after one run without a test. With these constants a commit needs a mean d of at least
  3.26, 2.07, 1.63, 1.40, 1.24 σ_cmp at n = 1…5 (computed from the formula).
- **Constants (proposed):** α = 0.05; r_max = 5; σ_cmp per edit kind from §2's noise constants (not learned); no rule
  layer, no screen. This is PACE-*style*: PACE (arXiv 2606.08106) is recorded on `main` only as "statistical commit gate"
  (PLAN §3), and this draft does not claim to reproduce its statistic (§13 item 4).
- **Reads:** nothing beyond the campaign and the noise constants. **Charged:** every candidate and incumbent replicate run.
- **Implementation:** missing (§12 G4).

### 5.6 LADDER — Ladder margin rule, η per node by direct search on the dev label block (R1-MINSUB-CHOICES (4))

- **Rule:** execute every proposal (no screen: "with a constant prior a screen makes the same decision for every
  proposal"), one run, keep iff Δ̂ > η_node; no verify.
- **Search (proposed procedure; result pinned in §5.0's file):** per node, on the same dev rows as A1 (§5.0), maximise
  U_node(η) = Σ_p w_p · Δ_label,p · 1{Δ̂_p > η} over the grid η = c · σ_node, c ∈ {−3.00, −2.95, …, +3.00}
  (121 values), where Δ_label,p is the label-seed mean (7001–7005) of proposal p, Δ̂_p its logged in-campaign
  comparison and w_p its `offline_eval` weight (1 here: every eligible sweep-2 proposal was audited). The −g·execute term
  is the same for every η and is dropped. Ties: smallest |c|, then smallest c (c = 0 is A0's rule). The objective uses no
  evaluation value and no test label. Duplicates and first trials have no label and do not enter (disclosed).
- **Reads:** η from the constants file. **Charged:** one run per executed trial.
- **Implementation:** missing: the η search in the fitter (G2) and a keep-only controller (G5).

## 6. D.3b arms (only if the gate passes; R1-D3-MIN)

- **A3, A5:** exactly as frozen in the arms-frozen record (preregistration §4 step 4), through `RuleController` with the
  rule layer, the screen, the keep threshold and KG verify (r = 2) as in A2; A3 = `TableArmPrior(LGBMPrior)`, A5 =
  `SidecarPrior` against `r1/c3/serve.py` with the pinned adapter, head and calibration map; on a sidecar failure the
  fallback prior answers and `prior_unavailable` is logged (`control.py`). The sidecar costs compute only, no LLM call
  (RUNBOOK H.6).
- **A6:** enters only if trained under RUNBOOK P.5 after the gate passes, on the train and dev label blocks only, and
  frozen in its own record before D.3b starts; deployed as P.5 requires ("rule(belief) or the action head, never the
  greedy bin"). Optional under R1-SUBMISSION-MIN's 3 Jan rule.
- **Paired with D.3a:** the same 126 instances, seeds, repetitions, audit seeds and start configurations; the D.3a rows of
  A0 and A2 are the references (no rerun). D.3b runs on byte-identical pins (image, model file, server flags, GPU model,
  harness, paper code outside the D.3b controller units); any difference is listed in the D.3b note and decided by the
  author before launch (§13 item 13).
- **Needs its own authorization note** (R1-D3-MIN); not drafted here.

## 7. Outcome, audit and contrasts

### 7.1 Outcome Y

Y is "the fresh-seed audited improvement of the final incumbent over the start config, normalised per node" (PLAN §4).
Per campaign: the final incumbent is the configuration of the campaign's last kept trial (the start configuration if
none). y_raw = (1/10) Σ_k [m(final, a_k) − m(start, a_k)] over the instance's audit seeds a_1…a_10 (§4.1), each run with
train seed = split seed = a_k as `r1/c3/audit.py` runs audits, Δ oriented as the C3 audit orients it. If the final
configuration equals the start configuration, y_raw = 0 by rule (no audit). **Y = y_raw / σ_node** (normalisation
**proposed**: σ_node is the scale C3 already uses for z = Δ/σ_node; §13 item 10). Identical (node, configuration, seed)
runs are computed once and reused across the arms of an instance (cache; disclosed).

### 7.2 Audit: K = 10, seeds 6701–6880, host deepthought CPUs

K = 10 (R1-MINSUB-CHOICES (4)); no label/evaluation split, because Y trains nothing. Host: deepthought CPUs, which
R1-MINSUB-CHOICES (4) allows for the D.3 audit **under the conditions of R1-SWEEP2-B2-GO**, here applied as:
1. **One host:** every D.3 audit (both stages) on deepthought.
2. **Environment basis:** the e1 replay (R1-B2-GO B6 (a)), with the current-environment checks at audit start that the
   sweep-2 audit used (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, `uv.lock`
   `dd42d018…`; `authorizations/c3_sweep2_b2_addendum_20261122.md` "Pins"); a difference is a STOP.
3. **Harness-code equality:** the audit harness's node, config, worker and audited-library paths equal those of the D.3
   campaign harness pin (§2), checked at run time.
4. **Host difference disclosed:** campaigns on the HTCondor GPU job's CPUs, audits on deepthought; Python 3.13.18 in the
   v1 image against 3.13.15 in the e1 basis (R1-SWEEP2-B2-DECISIONS D3 A).
Operator protocol as in the sweep-2 audit: 16 workers, at least 10 of 40 cores free, `cotenancy.log`; a non-finite or
failed audit seed run is a STOP (D4 A of R1-SWEEP2-B2-DECISIONS).

### 7.3 Contrasts (every one of both stages)

| Family | Contrast (arm − reference) | Claim |
|---|---|---|
| D.3a | A1 − A0, A2 − A0, FIXR3 − A0, EGATE − A0, LADDER − A0 | each rule arm against the default (R1-D3-MIN; R1-MINSUB-CHOICES (4)) |
| D.3a | LADDER − A2 | a dev-tuned margin against the index policy with rules (R1-MINSUB-CHOICES (4)) |
| D.3b | A3 − A2, A5 − A2, A3 − A0, A5 − A0 | learned arms against the rule floor and the default (R1-D3-MIN) |
| D.3b | A6 − A5, only if A6 enters | decision-focused fine-tuning (R1-D3-MIN) |

**Design and statistic.** Paired by instance: for a contrast a − b, D_{n,s} = Y_{n,s}(a) − Y_{n,s}(b) (the mean over
repetitions if two are declared). Estimate: the node-equal-weighted mean D̄ = (1/7) Σ_n mean_s D_{n,s}. Standard error
(1/7)·√(Σ_n s_n²/m_n). Test: **two-sided** Student t with df = Σ_n (m_n − 1) = 119. Interval: 95 % t interval
(unadjusted) and, beside it, a node-stratified percentile bootstrap interval (instances resampled within node,
10,000 resamples, PCG64 seed 20261122, per node in node order a 10,000 × m_n index array; descriptive). Per node: mean,
sd, n (descriptive). Per arm: mean worker runs, mean LLM calls, `ended_on` counts, mean Y (descriptive).

**Sample size.** 126 paired instances per contrast (7 nodes × 18; one repetition). No closed-loop paired outcome
exists, so sd(D) has no source and no power is claimed. For a two-sided test at Holm's first step (α/6 = 0.0083) with
power 0.8 the minimal detectable effect is 0.310 · sd(D); at α = 0.05, 0.250 · sd(D) (normal approximation, computed).

**Multiplicity.** Holm step-down at family-wise α = 0.05 within each family: D.3a (six contrasts), D.3b (four, or five
with A6). The two stages are separate families because D.3b exists only if the gate passes. Per-node results are
descriptive. Two-sided and the family definitions are **proposed** (§13 item 2).

**If a stage does not run.** D.3b not run (gate not passed, stopped, or not started): its family is reported as
"not run" with the reason, and its contrasts are listed as not estimated (the script requires the reason). A6 not
entering: A6 − A5 is listed as not run. D.3a not run or stopped: §10.

## 8. Per-campaign outcome table: schema `r1_d3_outcome/v1`

One JSON file per stage, written by the outcome-table builder (§12 G7) from the campaign ledgers and the audit records;
the analysis refuses anything else (`d3_analysis.validate_table`).

```
{"schema": "r1_d3_outcome/v1",
 "stage": "D.3a" | "D.3b",
 "predeclaration_sha256": <64 hex: the signed file of this pre-declaration>,
 "noise_source_sha256": "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310",
 "sigma_node": {<each of the seven nodes>: <dataset.noise_table sigma_node>},
 "arms": D.3a ["A0","A1","A2","FIXR3","EGATE","LADDER"] | D.3b ["A3","A5"] or ["A3","A5","A6"],
 "repetitions": 1 | 2,
 "rows": [ one per campaign:
   {"campaign_id": "<stage>__<arm>__<node>__s<seed>__r<rep>",
    "stage", "arm", "node", "instance_id": "<node>__s<seed>", "instance_seed": 6201..6218, "repetition": 0 | 1,
    "memory_mode": "append_only_summary", "status": "complete",
    "y_raw": <finite float, metric units, §7.1>,
    "worker_runs": 0..20, "llm_calls": 0..80,
    "ended_on": "worker_runs" | "llm_call_cap" | "no_fundable_candidate",
    "audit_seeds": [the ten seeds of §4.1 for this instance],
    "start_config_hash": <64 hex>, "final_config_hash": <64 hex>} ]}
```

Refused before any statistic: any other key at either level; a stage, arm, node, seed, repetition, memory mode or audit
seed list other than declared; a campaign name other than the declared one; a non-complete status; a non-finite y_raw;
runs above W or calls above the cap; a design that is not exactly every (arm, node, seed, repetition) once; y_raw ≠ 0
where the final configuration equals the start; σ_node differing from `noise_table` on the pinned source; a
pre-declaration sha256 differing from the file given; for D.3b, a different pre-declaration, noise source, σ,
repetition count or start configuration than D.3a's. Input paths that name a label, evaluation, split, sweep-table or
`r1_sealed` file are refused before opening.

## 9. Analysis script

`r1/c3/d3_analysis.py`, sha256 **`e16e4f2e2a6e1e4464c6049cb640e877e8196379352fca215f7f0a8d5eb47f84`** (this branch);
tests `r1/tests/test_d3_analysis.py` (synthetic tables only), sha256
`4841414587c9828c5eb1ffc5a9aa2b2989d5aa50f23a371f22408a3043f2dedf`. Command:
`python -m r1.c3.d3_analysis analyse --d3a <table> (--d3b <table> | --d3b-not-run gate_not_passed|stopped|not_started)
--predeclaration <this file, signed> --out <new file>`. It reads only the tables, this file (for its sha256) and the
pinned noise summary (sha256-checked); it never overwrites an output. Its constants (nodes, arms, W, cap, seeds,
contrasts, α, bootstrap) are this document's; a change after signing is a STOP. An input refusal is fixed and the run
repeated, both recorded; the analysis is never repeated after its statistics are seen (preregistration §4, last
paragraph, applied here).

## 10. STOP rules

Retain everything; there is no automatic resume. **Before launch (each stage):** any precondition of the stage's note
missing; a pin of §2 or of the note differing; the constants file's sha256 differing from §14, or (D.3b) the
arms-frozen record's per-node A1/A2 constants for the seven nodes differing from the constants file (checked when the
record is committed). **During campaigns:** a pin, image, model file,
server-flag, `cache_prompt` or thinking-flag mismatch; thinking content in more than 1 % of calls (RUNBOOK B.1b);
parse failures above 0.2 (the sweep collection gate); a worker `runtime_error` other than the two proposal-induced
classes diagnosed in R1-SWEEP2-RTE-DIAG (a YAML `ParserError` from a truncated mapping value; `TypeError` from
`max_depth: null` at `benchmark.py:164`), which are counted as `invalid_config` failures (**proposed** pre-admission,
§13 item 14); the pooled worker-failure rate of a stage above 12.99 % (sweep 2's pooled 7.99 % + 5 pp; the form of
R1-SWEEP2-LAYOUT-AMEND's rule, which there is relative to sweep 1; **proposed**); a campaign over W runs or the cap; any seed outside §4's blocks
(other than harness verify seeds, §13 item 12); a chunk over its walltime; a killed or non-clean chunk, which is rerun
whole in a new directory with the old one moved aside and disclosed (as sweep 2); more than 1 % of A5/A6 forecasts
answered by the fallback prior (**proposed**); any read of a test label, an evaluation value or a T1 label by D.3 code;
any use of a D.3 output to train, tune or select an arm. **Audit:** §7.2's conditions; a failed or non-finite seed run;
co-tenancy breach. **Analysis:** the refusals of §8.

**Reported on a STOP:** the stage is reported as stopped, with the STOP record, the number of completed campaigns per
arm and node, and no contrast: no outcome table is built from a partial design and no statistic is computed from one.
Any remedy needs an author row and is disclosed. If D.3a stops, R1-SUBMISSION-MIN part (4) is reported as a STOP and C2
has no closed-loop evidence; if D.3b stops, its family is reported as `not_run: stopped`.

## 11. Compute

**Proposer GPU-hours (HTCondor).** Basis: the measured sweep-2 chunk on H200, 5,823 s for 18 campaigns at W = 20 (about
20 calls per campaign), i.e. 11.32 GPU-h per arm on seven nodes (R1-SWEEP2-MEASURED-GPU; sweep-2 authorization
"Layout"). Model (approximation): a chunk's time scales with the larger of its campaigns' calls and runs relative to 20.

| Stage | Expected | Worst case (cap binds) |
|---|---|---|
| D.3a | A0, A1, FIXR3, EGATE, LADDER at factor 1: 56.6 GPU-h; A2 at 35.5/20 (sweep-2 pooled duplicate share, §3): 20.1 GPU-h; **≈ 76.7 GPU-h** | A1 and A2 at factor 4: 90.6 GPU-h; the other four 45.3 GPU-h; **≈ 135.9 GPU-h** |
| D.3b | A3, A5 like A2: **≈ 40.2 GPU-h** (≈ 60.2 with A6) plus unmeasured sidecar compute | **≈ 90.6 GPU-h** (≈ 135.9 with A6) |

For comparison, sweep 2 (288 campaigns) projected 25.88 GPU-h; D.3a has 756 campaigns. The expected values rest on the
pooled sweep-2 duplicate share, which may not hold for `append_only_summary` or under skipping. Before the D.3a note is
signed, a 2-instance ENGINEERING smoke per arm on the GPU model to be used (working worker runs, `gates.worker` PASS)
replaces this model; walltime = 1.5 × the measured chunk time per arm (the R1-SWEEP2-MEASURED-GPU rule). A projection
above 140 GPU-h for D.3a is a STOP for the author (**proposed**, just above the worst case here).

**Audit CPU-hours (deepthought).** Basis: the sweep-1 B.2 audit ran 4,660 seed runs in 22 min 44 s with 16 workers
(`reports/b2_audit_20261119/REPORT.md`), 4.68 worker-seconds per run. Upper bounds (no reuse across arms): D.3a
126 × (10 start + 6 × 10) = 8,820 runs ≈ **11.5 worker-h, ≈ 43 min at 16 workers**; D.3b 2,520 runs (3,780 with A6)
≈ 3.3 (4.9) worker-h, ≈ 12 (18) min. The node mix differs from sweep 1's.

## 12. Implementation gaps (this branch; none is written here)

| Arm or unit | Exists on this branch | Status | Short spec of what is missing |
|---|---|---|---|
| G1 D.3 campaign runner (all arms) | `e1b_collect.run_root` (A0 design); `c3_control_dryrun.py` (DRYRUN wiring of `RuleController`) | **missing** for EVIDENCE | HTCondor job per (node, arm) chunk as sweep 2; explicit instance seeds 6201–6218; harness `campaign_id` = instance id; `c3_budgets(20, 80)` for every arm (A0 too); controller per arm; manifests with pins, skip display, seeds; no resume; tier E |
| A0 | `e1b_collect._run_root` | **needs changes** | instance seeds and cap from the runner instead of `_instance_seed` and `budget = 2 W` |
| A1, A2 | `control.RuleController`, `prior_model.TableArmPrior`, `arms.ConstantPrior/RulesPrior` | **usable as is** (decision logic) | only G1, G2; pass σ_cmp per edit kind from `noise_table` and verify r = 2 explicitly |
| G2 constants fitter (A1, A2, LADDER η) | `gate_input_builder._fit_a2` (fits A2 from the full gate input, after the test release) | **missing** | reads only the receipted sweep-2 train/dev partition; §5.0 and §5.6; test of equality with `_fit_a2`; output JSON pinned by sha256 |
| G3 FIXR3 | none | **missing** | §5.4: replicate runs on declared seeds (a harness change, e.g. a replicate-aware verify with explicit seeds and a Welch keep response, or a controller-owned replication path), incumbent replicate reuse, charging, memory line |
| G4 EGATE | none | **missing** | §5.5: e-process, futility discard, r_max, incumbent replicate runs on demand, charging; tests of the α bound by simulation |
| G5 LADDER controller | none (`RuleController` cannot keep at a fixed η without a prior) | **missing** | execute always; keep iff Δ̂ > η (e.g. a `KeepPrior` with μ = −η, τ = σ = σ_cmp gives t* = η under `bayes_threshold/v1`); no verify |
| A3 | `RuleController` + `TableArmPrior(LGBMPrior)` | **usable as is**; needs the frozen artefact | arms-frozen record (not yet) |
| A5 | `prior_model.SidecarPrior`, `r1/c3/serve.py` | **needs changes** | HTCondor co-residence of the sidecar with llama-server, an image with its stack (G9), pinned artefact loading; fallback accounting |
| A6 | `RuleController(greedy_bin=True)` | **needs changes** | the greedy-bin path contradicts RUNBOOK P.5 / R1-C3-POST ("never the greedy bin"); a rule(belief) or action-head path is needed |
| G6 Y audit | `r1/c3/audit.py` (B.2 proposal audits, seeds fixed to 7001–7010) | **missing** | final-vs-start audit on per-instance seeds 6701–6880, K = 10, cache across arms, §7.2 conditions, completion record; tier E |
| G7 outcome-table builder | none | **missing** | ledgers + audit records → §8 schema; `ended_on` from the completion event |
| G8 usage check | `r1/branch/matching.py` `matching_report`, `accounting.campaign_usage` | **usable as is** | — |
| G9 image for D.3b | v1 (sweep 2), v2.1 (Track P) | **open** | which image serves the A5/A6 sidecar beside the v1 proposer |

Every unit G1–G7 and the A5/A6 changes are tier E (R1-PROCESS-TIERS: the rule layer, the deployment controller, code
that writes or parses evaluation records, the D.3 analysis scripts): each needs a committed independent review re-checked
until accepted, before the stage's note can cite it.

## 13. Open for the author

1. **LLM-call cap** (§3): proposed 80 = 4 W, equal for all arms. Alternatives: 40 (the sweeps' trial budget; Track S),
   60. The signed value is written into `d3_analysis.LLM_CALL_CAP`, and §9 re-pins the sha256.
2. **Sidedness and families** (§7.3): proposed two-sided, Holm within each stage at α = 0.05. Alternative: one-sided for
   the C2 direction (A1, A2 better than A0), as the C3 gate is one-sided.
3. **Second repetition:** proposed not run. If wanted, `repetitions: 2` is fixed at signing and each instance's outcome
   is the mean of both; a rep 1 decided after any D.3 outcome exists is descriptive only.
4. **EGATE construction** (§5.5): proposed normal-mixture e-process, α = 0.05, r_max = 5, futility discard at S_n ≤ 0,
   σ = σ_cmp from the noise floor. Whether this is close enough to PACE's gate needs the PACE full text, which `main`
   does not summarise. Misspecified σ (true noise above σ_cmp) inflates false commits beyond α; disclosed.
5. **FIXR3** (§5.4): R1-BX-D7 says Welch (unpaired) although the replicates share seeds; a paired t-test would use the
   pairing. Kept as the row says.
6. **`openml_wdbc`:** not run in D.3 (R1-D3-MIN's default node set). A sensitivity row would add one node per arm.
7. **LADDER search** (§5.6): grid, objective and tie rule are proposed.
8. **Fit population** of A1/A2/LADDER: proposed both memory modes of sweep 2's dev instances (as `_fit_a2`), although
   D.3 runs `append_only_summary` only. It must equal what the arms-frozen record carries.
9. **Sweep-2 release:** R1-S2-LABELS-TRAINDEV-RELEASE exists; R1-SWEEP2-RELEASE-DECISIONS holds sweep 2's release until
   its audit is registered. Whether the release then needs a further author row, or only the receipt, is the author's
   call; D.3a cites the receipt either way.
10. **Y normalisation by σ_node** (§7.1): PLAN §4 says "normalised per node" without a scale.
11. **Projection STOP** (§11): proposed 140 GPU-h for D.3a.
12. **Harness verify seeds:** the `vary` verify seed derivation is in the harness, not in this repository; the
    implementer records it and the disjointness check (§4.2) is extended to it before signing.
13. **D.3b pins:** proposed byte-identical to D.3a's, or the difference is decided before launch.
14. **Pre-admitted runtime errors and the failure gate** (§10): proposed.
15. **Memory line of a replicated trial** (FIXR3, EGATE): proposed mean of the replicate metrics with the decision.
16. **Image** for D.3 (§2) and for the D.3b sidecar (G9).
17. **D.4 descriptive analyses** (C1 error rates per arm, T4 bound vs realised gain; RUNBOOK D.4) are not
    pre-declared here; they would need per-proposal audits of D.3 campaigns and their own declaration.
18. **Missing implementations**, each a reviewed unit before the stage's note: G1–G7 (D.3a), and A5/A6 changes and G9
    (D.3b), §12.

## 14. Key block

```
frozen: false
signed_by: <pending: author signature>
frozen_utc: <pending>
implements: R1-D3-MIN, R1-MINSUB-CHOICES (4)
d3_nodes: digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, tabular_mlp
memory_mode: append_only_summary
W: 20
llm_call_cap: 80 (proposed)
trial_budget: 80
instances_per_node: 18
instance_seeds: 6201-6218
replicate_seeds: 6500 + 10 i + j, j = 1..9 (6501-6679)
audit_seeds: 6700 + 10 i + k, k = 1..10 (6701-6880)
proposer_seed: D26 manager_seed(instance_id, budget_index, repetition, revision_attempt)
K: 10
repetitions: 1
d3a_arms: A0, A1, A2, FIXR3, EGATE, LADDER
d3b_arms: A3, A5; A6 only under RUNBOOK P.5
g: 0.1 sigma_node
noise_source: results/r1/noise/D28_REPAIR_20261027/summary.json sha256 3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310
split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
analysis_preregistration: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
analysis_script: r1/c3/d3_analysis.py sha256 e16e4f2e2a6e1e4464c6049cb640e877e8196379352fca215f7f0a8d5eb47f84
constants_file_sha256: <pending: §5.0, filled at signing>
audit_host: deepthought CPUs (R1-MINSUB-CHOICES (4), conditions of R1-SWEEP2-B2-GO)
proposer_host: HTCondor GPU with a measured D.3 chunk time
```
