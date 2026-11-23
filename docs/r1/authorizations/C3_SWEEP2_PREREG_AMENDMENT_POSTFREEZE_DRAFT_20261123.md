# Amendment to the sweep-2 C3 analysis preregistration: test reads declared before the arms freeze — DRAFT

**AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed.** Tier E (R1-PROCESS-TIERS): it needs a committed
independent review re-checked until it writes "accepted", then the author's signature, before it binds.

It implements PLAN row **R1-POSTFREEZE-READS** (author, 23 Nov 2026). That row is on the local branch
`author-minsub-20261122` @ `d3f03e2c`; it is not yet on `origin/author-minsub-20261122` (`53e2fe41`) or on `main`
(`89899f76`). The row must be on `main` before this amendment is signed, because `arms_freeze.check_record` looks up
cited rows in `main`'s PLAN.

It amends `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md` (signed and frozen; sha256
`aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`; its bytes are not changed), under PRE-SECONDARY.
"The preregistration" below means that file; "§n" without a file name means a section of it. Sections of this
amendment are written "A§n".

It decides nothing on its own. Every rule is quoted from a PLAN row, the preregistration, a cited code location or
another cited committed file. The choices that none of these settle are in A§12, each with a recommendation.

## A§0. What this amendment adds, and what it leaves unchanged

**Adds** (each **descriptive, without a verdict, without a Holm step**):

- (a) **A0 and A1 as per-node test rows** on the gate inputs of §4 step 6, with A1's constants frozen in the
  arms-frozen record (A§3).
- (b) **Two-sided 95 % intervals for every descriptive row** (A0, A1, A2, the oracle, the secondary arms of
  PRE-SECONDARY A as amended by ARMS-SECONDARY A, and the utility levels of A3 and A5), from the gate's own
  node-stratified instance-cluster bootstrap resamples (A§4).
- (c) **One-sided upper bounds of the IQM of gap closed of A3 and A5**, from the gate's own resamples (A§5).
- (d) **The dispersion estimate of T4 Proposition 7** with the frozen A3 and A5 forecasts against A2's constant
  threshold, on the proposals of the primary input's test instances, computed after the test release and reading no
  label (A§6).
- (e) **C1**: the operational definitions of the four control-error rates, its audit seeds and instances, its timing
  and its fallback (A§7).

**Leaves unchanged** (the reviewer checks each against the code and documents cited):

- the gate (`r1/c3/gate.py`, v3.1, sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`) and the
  gate-input builder (`r1/c3/gate_input_builder.py`, sha256
  `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`), both bound in the preregistration's final
  block; the split file; the primary verdict; the PRE-DUP secondary run; the PRE-WDBC sensitivity run;
- every §2 decision, the §3 definitions, the §4 order, the §5 floors and eligibility, the §6 STOPs;
- the fold analyses and secondary recomputes of PRE-SECONDARY A as implemented in `r1/c3/fold_analysis.py` with
  FOLD-POI A and FOLD-LEVELS A (R1-FOLD-DECISIONS): their outputs are not changed or extended here;
- arm training, selection and calibration (PRE-POOL, PRE-JOINT A, PRE-SELECT A, R1-ARMS-DECISIONS): no arm is
  selected, tuned or calibrated on anything this amendment computes;
- **the power statement follows PRE-POWER A unchanged; the closed-loop arms' constants follow the signed D.3 note**
  (both quoted from R1-POSTFREEZE-READS).

**Not added:** the cross-proposer table (still out of scope under PRE-SECONDARY A); any offline test read of A6
(R1-SUBMISSION-CUTS); offline test rows of the D.3a reference arms (fixed-r replication, the commit gate, the Ladder
margin rule; R1-MINSUB-CHOICES (4) says the last needs a signed amendment; see A§12 item 10).

## A§1. What was read

| Source | Where | Used for |
|---|---|---|
| R1-POSTFREEZE-READS, R1-CONTROLS-ROW, R1-CONTROLS-NEG-DROP, R1-PROOF-POLICY, R1-SCREEN-MEASURE-CHOICES | PLAN, local `author-minsub-20261122` @ `d3f03e2c` | the task; C1's controls; Proposition 7's check status |
| R1-SUBMISSION-MIN, R1-ARMS-FREEZE-CUTOFF, R1-D3-MIN, R1-SUBMISSION-CUTS, R1-MINSUB-CHOICES | PLAN, same branch (section "22 November 2026 (d)"; not on `main`) | dates, scope, A1's constants in D.3 |
| R1-SWEEP2-PREREG, R1-S2-LABELS-TRAINDEV-RELEASE, R1-SWEEP2-RELEASE-DECISIONS, R1-FOLD-DECISIONS, R1-SWEEP2-LABELS-FREEZE, R1-ARMS-FEATURIZER, R1-ARMS-DECISIONS, R1-G5-DECISIONS-2, R1-G5-MEM-E4 | PLAN on `main` @ `89899f76` (the newest rows are R1-ARMS-DECISIONS, R1-G5-DECISIONS-2, R1-G5-MEM-E4) | the frozen analysis, the secondary arms, the T1 mode |
| The preregistration | `main` | everything below |
| Code: `gate.py`, `gate_input_builder.py`, `fold_analysis.py`, `offline_eval.py`, `arms.py`, `rules.py`, `labels.py` (via `arms`), `audit.py`, `release.py`, `arms_freeze.py`, `features.py`, `dataset.py`, `duplicate_report.py` | `r1/c3/` on `main` @ `89899f76` | definitions, line citations |
| `C3_OFFLINE_PILOT_20261019.md` | `docs/r1/reports/` on `main` | the arms of the sweep-1 offline pilot |
| `T0_ARMS_READINESS_20261123.md` | `docs/r1/reports/arms_readiness_20261123/` on `main` | how A0, A1, A2 stand in the arms freeze |
| Sweep-1 B.2 audit review `B2_AUDIT_RUN_REVIEW_20261119.md`; sweep-2 B.2 audit report `S2_B2_AUDIT_REPORT_20261122.md` and its review `S2_B2_AUDIT_RUN_REVIEW_20261122.md` | `docs/r1/reviews/`, `docs/r1/reports/sweep2_20261116/` on `main` | C1's audited populations (counts only) |
| Train/dev release reports `S2_TRAINDEV_RELEASE_20261122.md`, `SWEEP1_TRAINDEV_RELEASE_20261123.md` and committed receipts | `docs/r1/reports/release_20261122/` on `main` | C1's fallback |
| `papers/r1/sections/problem.tex` (control errors, lines 44–52), `results.tex` (§C1 lines 33–82 with `tab:c1`; §C3 lines 84–146 with `tab:ladder`), `setup.tex` (arms, lines 71–94), `appendix.tex` (`prop:app-gap`, lines 247–256; `prop:app-rules`, lines 258–265) | local `mac-manuscript-20261122` @ `a93c1cea` | C1's four rates; the tables that receive the rows |
| `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` §3 | local `mac-proofcheck-ai-20261123` @ `79f6442f` | Proposition 7, its reading and status |
| `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` §5.0–§5.3, §10 | local `mac-d3-predecl-20261122` @ `a24a55bf` | A1's constants file, A0/A1/A2 in D.3 |
| `docs/r1/reports/CONTROLS_POSITIVE_20261123.md` §1 | local `mac-controls-pos-20261123` @ `25d5a510` | the audit statistic and the readings the positive control uses |

The drafter opened no label block, evaluation block, receipted partition, sweep table, run log or audit evidence
directory. Directory listings were read only to locate reports.

## A§2. Conventions shared by (a)–(d)

**Inputs.** The three gate inputs of §4 step 6 (primary, PRE-DUP secondary, PRE-WDBC sensitivity), as built by
`gate_input_builder.runs` (`gate_input_builder.py:489–502`) and committed with their sha256s in step 6; the builder's
`Source` objects for the gate sources from `release.builder_source` (`release.py:657–675`), which opens the test
partitions and therefore exists only after the test release row; the frozen arms' predictions (arms-frozen record,
`predictions` pin of each arm, `arms_freeze.py:550`); the noise constants of PRE-DELTA. "The primary input" is the
step-6 primary gate input; its T0 node set is the arms-frozen record's (`fold_analysis._primary`,
`fold_analysis.py:67–84`).

**Population.** Every series here is computed on exactly the population of the gate input it is reported with: the
test block's instances, memory modes and proposals after PRE-DUP (the builder's filter, `gate_input_builder.py:424–428`),
PRE-MEM C's per-mode mean and fallback (`:436–467`), PRE-DIV A (`:336–338`), sweep 2 only as the T0 test population
and G.5 in its declared mode(s) for T1 (PRE-MEM; R1-G5-MEM-E4: `history` only). Weights are the builder's (all 1 in
the complete evidence population, `gate_input_builder.py:16–20`).

**Utility.** §3 unchanged: per series, instance and mode, U = 20 × Σ w r / Σ w with r = Δ_true × keep − g × execute
(`skip_credited_at_g`; `CAMPAIGN_RUNS = 20`, `offline_eval.py:85`), g = 0.1 σ_node (`G_PRIMARY`, `offline_eval.py:80`),
Δ_true from the evaluation block. Per instance the modes combine by PRE-MEM C. "In σ_node units" divides a node's
value by that node's σ_node from the PRE-DELTA source.

**The gate's bootstrap, reused.** The gate resamples **test instances within each node** (node-stratified; the
instance is the resampling unit, as PRE-MEM C and R1-MAIN-PROPOSER (e)(4) require): `gate._bootstrap`
(`gate.py:463–511`) draws, for each node in sorted node-id order over its test instances in sorted instance-id order,
one `integers(0, n, size=(2000, n))` array from `numpy.random.Generator(PCG64(20261108))`, and uses that one array
for every series of the node (`gate.py:468–477`). Constants: `N_RESAMPLES = 2000`, `SEED = 20261108`,
`RNG = PCG64`, `QUANTILE_METHOD = 'linear'`, `TSTAR_INF = 1e12`, `LEVELS = (0.975, 0.95)` (`gate.py:136–142`).
The fold-analysis module already reuses these resamples by calling `gate._validate`, `gate._point` and
`gate._bootstrap` after `analysis_guard.require_d8_confirmation` and `gate._require_pins`
(`fold_analysis.fold_statistics`, `fold_analysis.py:120–161`). This amendment reuses them the same way:

1. The new code calls `gate._validate`, `gate._point` and `gate._bootstrap` on the committed gate input, after the
   D8 confirmation and the pin check, exactly as `fold_statistics` does.
2. Because `gate._bootstrap` returns t* and PoI resamples for A3 and A5 only, the new code re-derives the index
   arrays with the gate's constants and draw order (same generator, same seed, nodes in sorted order, one
   `integers(0, n_test, size=(2000, n_test))` per node) and applies them to every other series. It first recomputes
   A3's and A5's t*, screened mask and PoI resamples from the re-derived indices and requires them to equal
   `gate._bootstrap`'s output exactly (bitwise); otherwise it refuses before any descriptive statistic. This binds
   "the gate's own resamples" to the gate's code rather than to a copy.
3. It recomputes the gate's point IQM, PoI, lower bounds and per-node gap closed for A3 and A5 and requires them to
   equal the committed step-6 gate output exactly. This is not a new gate run: no verdict is computed, re-read or
   changed (§4: "a gate run is never repeated after its statistics are seen").

**If the gate input STOPs** (no IQM-eligible node, or a nonpositive test denominator on an eligible node:
`gate._point`, `gate.py:413–447`): every IQM-based quantity here is reported as that STOP, and the PoI and utility
rows are still reported, as FOLD-POI A does for folds.

**Binding to the committed inputs.** Every item (a)–(d) takes the committed step-6 input(s) by path and sha256 and
recomputes from the `Source`s only what it adds. Where it recomputes A2 or the oracle for a check, they must equal the
committed input's test series and instance ids exactly (the check of `fold_analysis._bind`, `fold_analysis.py:105–117`);
any difference is an input refusal (§4).

## A§3. (a) A0 and A1 as per-node test rows

The gate reads only the oracle, A2, A3 and A5 (`gate.SERIES`, `gate.py:147`; the builder's `TEST_SERIES`,
`gate_input_builder.py:87`). A0 and A1 are defined here exactly as `offline_eval` defines them, which is how the
sweep-1 offline pilot ran them (`C3_OFFLINE_PILOT_20261019.md` line 12: "A0 (ρ), A1 (constant prior per node), A2 (A1
+ D25/D27 rules)") and how the manuscript describes them (`setup.tex` lines 83–85: A0 "Execute every proposal once;
keep if the observed increment is positive"; A1 "A constant (π, μ, τ) per node; closed-form screening and keep
thresholds").

### A§3.1 Definitions

Notation per proposal p of the population (A§2): Δ̂_p is the table's logged campaign comparison `delta_hat` (the
ledger's `delta_vs_best`, `features.py:550–552`); σ_p is the edit's comparison noise `sigma_cmp` (local or structural,
from the PRE-DELTA noise source; `dataset.py:81–83`, `:102–104`); g_p = 0.1 σ_node.

| | A0 — the default rule (Karpathy default, R1-BX-D7) | A1 — the index policy with a constant forecast (D23; C3_DESIGN §5) |
|---|---|---|
| Code | `offline_eval.rho` (`offline_eval.py:287–291`); `arms.py:7` | `arms.ConstantPrior` (`arms.py:84–99`); `offline_eval.decisions(P, rows, g_units, rule_layer=False)` (`offline_eval.py:269–279`; A1 has no rule layer, `:412`) |
| Execute | a_p = 1 for every proposal | a_p = 1{(1 − π_n) V(t*_p; μ_n, τ_n, σ_p) ≥ g_p} (Proposition 8; `rules.execute`, `rules.py:50–52`) |
| Keep | k_p = 1{Δ̂_p > 0} | k_p = a_p · 1{Δ̂_p > t*_p}, t*_p = −μ_n σ_p² / τ_n² (Proposition 6; `rules.decide`, `rules.py:102–112`) |
| Constants | none | one 12-bin vector c_n per node: the weighted mean soft label of node n's **dev** label block of the gate source (sweep 2 for T0, G.5 for T1), over the full dev population of both T0 memory modes (T1: its declared mode) — exactly the rows `gate_input_builder.fit_a2` fits A2 on (`gate_input_builder.py:296–304`): no-ops with the inert soft label, audit labels with `soft_label(Δ_label, None, σ_node, "pooled_node", k_label)` (`:281–285`), weights 1; within-campaign duplicates and divergent labels have no soft label and do not enter. (π_n, μ_n, τ_n) = `arms.prior_moments(c_n)` (`labels.moments` with the τ floor 0.15 σ_node, `arms.py:29`, `:187–190`). This is PRE-A2 C's fit set for A1 ("A1's constants per node from the dev instances' label block"). |
| Rule layer | none | none: no-ops and within-campaign duplicates are decided by the same rule (no forced inert belief, no forced skip) |
| Verify | none | none. The D23 KG verify is a closed-loop action; the offline evaluation has a single logged Δ̂ per proposal and no verify (`C3_OFFLINE_PILOT_20261019.md` line 93: "The A1 index policy has no KG-verify component (D23 verify is outside this one-step evaluation)"). D.3a's A1 keeps it (D.3 draft §5.2). |
| Reads, for decisions | the table's Δ̂ only | the table's Δ̂ and σ_cmp, and the frozen c_n (derived from the released dev label block) |
| Reads, for value | the evaluation block (Δ_true) | the evaluation block (Δ_true) |

**Consequence to report, not to repair** (from the D.3 draft §5.2 and the audit counts of A§7.2): both sweeps' T0
tables have no no-op (sweep 1: 0 of 4,999 proposals, `B2_AUDIT_RUN_REVIEW_20261119.md` lines 89–90; sweep 2: 0, with
2,500 eligible and 2,512 duplicates, `S2_B2_AUDIT_REPORT_20261122.md` line 17), and a non-no-op soft label puts no
mass on the no-op bin, so on T0 c_n equals A2's per-node vector except for the no-op bin, which A2 zeroes
(`arms.RulesPrior._noninert`, `arms.py:116–120`). On T0, A1 therefore differs from A2 only in that it executes
within-campaign duplicates. With a constant forecast, A1's screen takes the same execute decision for every
non-duplicate proposal of a node and edit kind.

**Realised value.**

- Audited (non-no-op, non-duplicate) proposal: Δ_true from the evaluation block; PRE-DIV A: if more than half of its
  evaluation seeds diverge, r_p = −g_p a_p, counted per arm (as `gate_input_builder._series_rewards`, `:336–338`);
  at most half: the mean over the rest, counted as partial.
- No-op: Δ_true = 0, so r_p = −g_p a_p.
- **Within-campaign duplicate** (A0 always executes it; A1 may): `offline_eval`'s convention (`offline_eval.py:6–9`,
  `:198–209`): if kept, Δ_true is its audit value when audited, otherwise the logged Δ̂_p as a proxy, counted and
  reported (`duplicates_kept`, `duplicates_kept_with_logged_proxy`, `offline_eval.py:416–417`). No duplicate is audited
  in the evidence population (`audit.evidence_blocks`, `audit.py:1026–1028`; the builder refuses label or evaluation
  rows on a duplicate, `gate_input_builder.py:271–274`), so a kept duplicate always takes the proxy. If not kept,
  r_p = −g_p. On a bit-exact node the default rule cannot keep a duplicate (`appendix.tex` `prop:app-rules` (iii);
  R1-CONTROLS-NEG-DROP), so A0's proxy count is expected to be 0 there; A1 can keep one only when t*_p < Δ̂_p ≤ 0,
  i.e. when μ_n > 0. The proxy is a campaign-seed value from the table, not an evaluation-seed value. See A§12 item 6.

### A§3.2 Frozen in the arms-frozen record

R1-D3-MIN: "A1's constants are those fitted under PRE-A2 C on the dev label block; they are pinned by sha256 in the
pre-declaration and enter the arms-frozen record unchanged." The record carries (A§9): A0's rule identifier; A1's and
A2's per-node vectors for every node of the PRE-WDBC sensitivity T0 set (all eight) and of the frozen T1 set, written
by the reviewed constants fitter (the D.3 draft's gap G2, whose output must equal `fit_a2`'s per node by a test,
D.3 draft §5.0); and, for the seven D.3 nodes, the requirement that these vectors equal the D.3 constants file (the
D.3 draft's STOP in §10). The vectors of openml_wdbc and of the T1 nodes are fitted by the same fitter on the same
rule (per node, so they do not change the seven nodes' vectors; no pooled fallback is used, `gate_input_builder.py:24–26`).

### A§3.3 Population and inputs

A0 and A1 are computed on each of the three step-6 gate inputs (primary, PRE-DUP secondary, PRE-WDBC sensitivity),
on that input's test block and population (A§2). The primary input's rows are the ones in the ladder table; the other
two are reported beside their gate runs. The code recomputes A2 and the oracle on the same items with the builder's
own `_series_rewards` (`gate_input_builder.py:319–339`) and `fit_a2`, and refuses unless they and the instance ids
equal the committed input's test block exactly (A§2).

### A§3.4 What each per-node row reports

Per node of the input and per arm X ∈ {A0, A1}: n_test (instances); mean U_X / σ_node; mean (U_X − U_A2) / σ_node; the
probability of improvement over A2, PoI_X = share of test instances with U_X > U_A2, ties ½ (the gate's `_wins`,
`gate.py:393–394`); on IQM-eligible nodes of the gate, gap closed G_X = mean(U_X − U_A2) / mean(U_oracle − U_A2) with
its delta-method se (`gate._node_se`, `gate.py:402–410`), exactly as `gate._point` computes them for A3 and A5
(`gate.py:435–443`); the execution and keep rates; duplicates executed, kept, and kept with the logged proxy; divergent
proposals executed. Intervals: A§4.

## A§4. (b) Intervals for every descriptive row

### A§4.1 Which rows

- A0 and A1 (A§3), on each of the three step-6 inputs;
- A2 and the oracle (gate series), as utility levels;
- A3 and A5 as utility levels (their IQM of gap closed and PoI keep the gate's own one-sided lower bounds, plus the
  upper bounds of A§5; nothing else is added to them);
- the secondary arms in this read, as ARMS-SECONDARY A (R1-ARMS-DECISIONS) amends PRE-SECONDARY A: "the other Kev
  base, both Qwen controls, A4, and TabPFN in-context only if its version decision and a reviewed adapter land before
  the arms-frozen record". PRE-SECONDARY A already allows their per-node test table; this amendment adds intervals and
  the aggregate statistics below (A§12 item 9). Each secondary arm's test series is computed by the **frozen builder
  unchanged**, called on the primary input's sources and T0 set with that arm's frozen predictions supplied as both
  `"A3"` and `"A5"` (`gate_input_builder.build`, `:348–486`); its series is the test block's `"A3"` series, and the
  code requires the `"A3"` and `"A5"` series to be equal and A2, the oracle and the instance ids to equal the
  committed primary input's (A§2).

The fold analyses and the g and per-mode recomputes keep their declared outputs (`fold_statistics`: point values and
both levels' lower bounds); this amendment adds no interval to them.

### A§4.2 Statistics and intervals

All resamples are the gate's (A§2): the same 2,000 index arrays per node for every series, so differences between
series are paired. Nodes are fixed, so every interval covers instance noise for these nodes only (as the gate's
bounds do, `gate.py:33–34`). Two-sided 95 % means the linear quantiles at 0.025 and 0.975 over the 2,000 resamples
(`numpy.quantile(..., method='linear')`, the gate's `QUANTILE_METHOD`).

| Statistic, per series X | Point | Interval |
|---|---|---|
| per node: ū_X,n = mean over test instances of U_X / σ_node,n | as stated | percentile, from the node's resampled means |
| per node: d̄_X,n = mean (U_X − U_A2) / σ_node,n (X ≠ A2) | as stated | percentile |
| per node: PoI_X,n against A2, ties ½ (X ≠ A2) | `gate._wins` mean | percentile |
| per node: gap closed G_X,n on IQM-eligible nodes (X ∉ {A2, oracle}) | as `gate._point` | none; its delta-method se `gate._node_se` is reported, as the gate's own per-node table does |
| aggregate: Ū_X = node-equal mean of ū_X,n over the input's nodes, and per tier (the "U … averaged over nodes" of `tab:ladder`) | as stated | percentile, from the resampled node means |
| aggregate: IQM_X of G_X,n over the gate's IQM-eligible nodes (`gate._node_iqm`; X ∉ {A2, oracle}) | as `gate._point` computes it for A3 | studentized, the gate's construction (`gate.py:451–456`, `:480–507`, `:523–527`) with X in place of the arm: lower end θ̂ − q₀.₉₇₅(t*⁺) ŝe, upper end θ̂ − q₀.₀₂₅(t*⁻) ŝe; t*⁺ holds `TSTAR_INF` on screened resamples (the gate's convention), t*⁻ holds −`TSTAR_INF` there (A§12 item 7); both ends equal θ̂ if ŝe = 0; the number of screened resamples is reported, and an end is reported as not finite when the quantile reaches a sentinel (A§5.1) |
| aggregate: PoI_X = node-equal mean of PoI_X,n over all nodes of the input (`gate._node_poi`; X ≠ A2) | as stated | percentile |

A2's rows are ū and Ū only (its gap closed and PoI against itself are degenerate). The oracle's gap closed is 1 on
every IQM-eligible node by construction and carries no interval. The IQM uses the gate's eligibility and is undefined
when the gate input STOPs (A§2).

## A§5. (c) One-sided upper bounds of the IQM of gap closed of A3 and A5

### A§5.1 Definition

On the **primary input** only, for X ∈ {A3, A5}: θ̂_X is the gate's point IQM of gap closed and ŝe_X its delta-method
se (`gate._point`, `gate.py:449–459`); t*_b (b = 1, …, 2,000) are the gate's studentized resamples from
`gate._bootstrap` (`gate.py:493–509`), and the screened resamples are those the gate sets to `TSTAR_INF` (an eligible
node's resampled denominator nonpositive, ŝe* = 0, or a non-finite t*; `gate.py:499–507`), identified by the
re-derived mask of A§2 step 2. Let t*⁻ equal t* except −`TSTAR_INF` on screened resamples. The one-sided upper bound
at level L is

  UB_L(X) = θ̂_X − Q_{1−L}(t*⁻) · ŝe_X,  with Q the linear quantile over the 2,000 resamples; UB_L(X) = θ̂_X if ŝe_X = 0.

It is the upper end of the same studentized construction whose lower end is the gate's bound
(θ̂ − Q_L(t*) ŝe, `gate._lower_iqm`, `gate.py:523–527`). The gate holds a screened resample at +∞ because that is the
conservative direction for a lower bound; for an upper bound the conservative direction is −∞ (a screened resample
from a nonpositive denominator has IQM* = −∞ in the gate, `gate.py:489–501`, i.e. t* = −∞). With m screened
resamples, the linear quantile reaches a sentinel when m ≥ ⌊1999 (1 − L)⌋ + 1 (50 at L = 0.975, 100 at L = 0.95);
UB_L is then reported as "no finite upper bound", with m.

### A§5.2 Levels

**Both arms at L = 0.975 and at L = 0.95; the text quotes L = 0.975.** Reasons:

1. The Holm levels are 97.5 % for the first-ranked arm and 95 % for the second (`LEVELS`, `gate.py:142`), but the
   ranking is a function of the data (`gate._holm_decision`, `gate.py:542–575`). A descriptive bound should not take
   its level from a data-dependent ranking.
2. A one-sided 97.5 % bound for each of the two arms gives simultaneous coverage of at least 95 % for both upper
   bounds by Bonferroni, i.e. the gate's family-wise α = 0.05 (`FAMILY_ALPHA`, `gate.py:141`), whatever the ranking.
3. Reporting both levels for both arms is what FOLD-LEVELS A chose for the fold analyses ("both arms at 97.5 % and
   95 %"), so the paper's bounds read alike.

### A§5.3 Use

Descriptive, in both outcomes of the gate. The bound may be stated beside the practical size 0.1 (`PRACTICAL_SIZE`,
`gate.py:143`; the §1 row "the point IQM is reported against 0.1"); no pass or fail is attached to it, and it changes
neither the verdict nor the Holm step. It is not computed if the primary gate input STOPs.
