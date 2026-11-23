# Amendment to the sweep-2 C3 analysis preregistration: test reads declared before the arms freeze — DRAFT

**AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed.** Tier E (R1-PROCESS-TIERS): it needs a committed
independent review re-checked until it writes "accepted", then the author's signature, before it binds. Revised after
the review `docs/r1/reviews/C3_PREREG_AMENDMENT_POSTFREEZE_REVIEW_20261123.md` (not accepted: M1, m1–m9, n1–n15);
the answers are in A§R.

It implements PLAN row **R1-POSTFREEZE-READS** (author, 23 Nov 2026), which is on `origin/author-minsub-20261122` @
`d3f03e2c` and on the merge-ready branch `author-minsub-mergeready-20261123` @ `055cacc5`, which fast-forwards `main`
(`89899f76`). That row and ten other rows this amendment cites are **not on `main` yet**: R1-SUBMISSION-MIN,
R1-ARMS-FREEZE-CUTOFF, R1-D3-MIN, R1-SUBMISSION-CUTS, R1-PROCESS-TIERS, R1-MINSUB-CHOICES, R1-PROOF-POLICY,
R1-CONTROLS-ROW, R1-CONTROLS-NEG-DROP and R1-SCREEN-MEASURE-CHOICES (all on `055cacc5`; checked by grep on both PLAN
versions). R1-S2-LABELS-TEST-RELEASE is absent by design (a future release row). **These rows must be on `main`
before this amendment is signed**, for a procedural reason: the amendment takes its authority from R1-POSTFREEZE-READS
and quotes the others, and a signed note may cite only rows that are in force. `arms_freeze.check_record` does not
look up R1-POSTFREEZE-READS today (it checks only the `REQUIRED_DECISIONS` and `fold_arms` rows,
`arms_freeze.py:731–753`); unit 2 (A§8) adds that check for the record's `amendments` entry.

It amends `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md` (signed and frozen; sha256
`aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`; its bytes are not changed), under PRE-SECONDARY.
"The preregistration" below means that file; "§n" without a file name means a section of it. Sections of this
amendment are written "A§n".

It decides nothing on its own. Every rule is quoted from a PLAN row, the preregistration, a cited code location or
another cited committed file. Every choice that none of these settle is **proposed**, not decided: it is listed in
A§12 with its options and a recommendation, and the text uses the recommendation, marked "(proposed; A§12 item n)".

## A§0. What this amendment adds, and what it leaves unchanged

**Adds** (each **descriptive, without a verdict, without a Holm step**):

- (a) **A0 and A1 as per-node test rows** on the gate inputs of §4 step 6, with A1's constants frozen in the
  arms-frozen record (A§3).
- (b) **Two-sided 95 % intervals for every descriptive row** (A0, A1, A2, the oracle, the secondary arms of
  PRE-SECONDARY A as amended by ARMS-SECONDARY A, and the per-node rows and utility levels of A3 and A5), from the
  gate's own node-stratified instance-cluster bootstrap resamples (A§4).
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
margin rule; R1-MINSUB-CHOICES (4) says the last needs a signed amendment; see A§12 item 21).

## A§1. What was read

| Source | Where | Used for |
|---|---|---|
| R1-POSTFREEZE-READS, R1-CONTROLS-ROW, R1-CONTROLS-NEG-DROP, R1-PROOF-POLICY, R1-SCREEN-MEASURE-CHOICES | PLAN, local `author-minsub-20261122` @ `d3f03e2c` | the task; C1's controls; Proposition 7's check status |
| R1-SUBMISSION-MIN, R1-ARMS-FREEZE-CUTOFF, R1-D3-MIN, R1-SUBMISSION-CUTS, R1-MINSUB-CHOICES | PLAN, same branch (section "22 November 2026 (d)"; not on `main`) | dates, scope, A1's constants in D.3 |
| R1-SWEEP2-PREREG, R1-S2-LABELS-TRAINDEV-RELEASE, R1-SWEEP2-RELEASE-DECISIONS, R1-FOLD-DECISIONS, R1-SWEEP2-LABELS-FREEZE, R1-ARMS-FEATURIZER, R1-ARMS-DECISIONS, R1-G5-DECISIONS-2, R1-G5-MEM-E4 | PLAN on `main` @ `89899f76` (the newest rows are R1-ARMS-DECISIONS, R1-G5-DECISIONS-2, R1-G5-MEM-E4) | the frozen analysis, the secondary arms, the T1 mode |
| The preregistration | `main` | everything below |
| Code: `gate.py`, `gate_input_builder.py`, `fold_analysis.py`, `offline_eval.py`, `arms.py`, `rules.py`, `labels.py` (via `arms`), `audit.py`, `release.py`, `arms_freeze.py`, `features.py`, `dataset.py`, `duplicate_report.py` | `r1/c3/` on `main` @ `89899f76` | definitions, line citations |
| `C3_OFFLINE_PILOT_20261019.md` | `docs/r1/reports/` on `main` | the arms of the 19 Oct offline pilot (`offline_eval`) |
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
`gate._point`, `gate.py:413–447`) (proposed; A§12 item 20): every IQM-based quantity here is reported as that STOP;
the point PoI and point utility rows are still reported, **without intervals**. `gate._bootstrap` needs `_point`'s
summary, so neither step 2's bitwise check of the re-derived draws nor step 3's check against the committed output can
run, and no interval would be bound to the gate's own resamples. This extends to these rows what FOLD-POI A decided
for folds (`fold_statistics` reports a point PoI only, `fold_analysis.py:143–147`).

**Binding to the committed inputs.** Every item (a)–(d) takes the committed step-6 input(s) by path and sha256 and
recomputes from the `Source`s only what it adds. Where it recomputes A2 or the oracle for a check, they must equal the
committed input's test series and instance ids exactly (the check of `fold_analysis._bind`, `fold_analysis.py:105–117`);
any difference is an input refusal (§4).

## A§3. (a) A0 and A1 as per-node test rows

The gate reads only the oracle, A2, A3 and A5 (`gate.SERIES`, `gate.py:147`; the builder's `TEST_SERIES`,
`gate_input_builder.py:87`). A0 and A1 are defined here exactly as `offline_eval` defines them, which is how the
19 Oct offline pilot ran them (`C3_OFFLINE_PILOT_20261019.md` line 12: "A0 (ρ), A1 (constant prior per node), A2 (A1
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
| Constants | none | one 12-bin vector c_n per node: the weighted mean soft label of node n's **dev** label block of the gate source (sweep 2 for T0, G.5 for T1), over the full dev population of both T0 memory modes (T1: its declared mode) — exactly the rows `gate_input_builder.fit_a2` fits A2 on (`gate_input_builder.py:296–304`): no-ops with the inert soft label, audit labels with `soft_label(Δ_label, None, σ_node, "pooled_node", k_label)` (`:281–285`), weights 1; within-campaign duplicates and divergent labels have no soft label and do not enter. (π_n, μ_n, τ_n) = `arms.prior_moments(P, rows)` with every row's P = c_n (σ_node taken from the rows; `labels.moments` with the τ floor 0.15 σ_node, `arms.py:29`, `:187–190`). This is PRE-A2 C's fit set for A1 ("A1's constants per node from the dev instances' label block"). |
| Rule layer | none | none: no-ops and within-campaign duplicates are decided by the same rule (no forced inert belief, no forced skip) |
| Verify | none | none. The D23 KG verify is a closed-loop action; the offline evaluation has a single logged Δ̂ per proposal and no verify (`C3_OFFLINE_PILOT_20261019.md` line 93: "The A1 index policy has no KG-verify component (D23 verify is outside this one-step evaluation)"). D.3a's A1 keeps it (D.3 draft §5.2). |
| Reads, for decisions | the table's Δ̂ only | the table's Δ̂ and σ_cmp, and the frozen c_n (derived from the released dev label block) |
| Reads, for value | the evaluation block (Δ_true) | the evaluation block (Δ_true) |

**Consequence to report, not to repair** (the D.3 draft §5.2 states it; the audit counts are in A§7.1): both sweeps'
T0 tables have no no-op (sweep 1: 0 of 4,999 proposals, `B2_AUDIT_RUN_REVIEW_20261119.md` lines 89–90; sweep 2: 0,
with 2,500 eligible and 2,512 duplicates, `S2_B2_AUDIT_REPORT_20261122.md` line 17), and `labels.soft_label` puts no
mass on the no-op bin for a non-no-op proposal (D.3 draft §5.2), so on T0 c_n has no mass on that bin and equals A2's
per-node vector in arithmetic (A2 zeroes the bin and renormalises, `arms.RulesPrior._noninert`, `arms.py:116–120`;
the renormalisation can change the last bits, which is one reason A§9 stores both vectors). On T0, A1 therefore
differs from A2 only in that it executes within-campaign duplicates. With a constant forecast, A1's screen takes the
same execute decision for every proposal of a node and edit kind (σ_cmp differs by edit kind).

**A structural sign on T0, to be stated with the rows.** Per proposal, A1 − A2 is 0 except on within-campaign
duplicates, where it is a_p (k_p Δ_true,p − g_p) − 0. Under the proposed kept-duplicate value (the logged Δ̂_p,
A§12 item 11), and on a bit-exact node, a duplicate's logged Δ̂_p ≤ 0 (`appendix.tex` `prop:app-rules` (iii); T4 §1
lists all CPU nodes as bit-exact; the sweep-1 table replay found 0 repeat-metric violations,
`B2_AUDIT_RUN_REVIEW_20261119.md` line 93), so the difference is ≤ 0. Then U_A1 ≤ U_A2 on every T0 test instance,
A1's T0 PoI against A2 is at most 0.5 and its T0 gap closed at most 0. The same holds under the Δ_true = 0
alternative. These are consequences of the definitions, not measurements, and `tab:ladder` should say so.

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
  i.e. when μ_n > 0. The proxy is a campaign-seed value from the table, not an evaluation-seed value. See A§12 item 11.

### A§3.2 Frozen in the arms-frozen record

R1-D3-MIN: "A1's constants are those fitted under PRE-A2 C on the dev label block; they are pinned by sha256 in the
pre-declaration and enter the arms-frozen record unchanged." The record carries (A§9): A0's rule identifier; A1's and
A2's per-node vectors for every node of the PRE-WDBC sensitivity T0 set (all eight) and of the frozen T1 set, written
by the reviewed constants fitter (the D.3 draft's gap G2, whose output must equal `fit_a2`'s per node by a test,
D.3 draft §5.0); and, for the seven D.3 nodes, the requirement that these vectors equal the D.3 constants file (the
D.3 draft's STOP in §10). A record that fails this is an input refusal of the record (fixed before any test read,
and before the gate read, which needs the record); it is consistent with the D.3 draft's §10. The vectors of
openml_wdbc and of the T1 nodes are fitted by the same fitter on the same rule (per node, so they do not change the
seven nodes' vectors; no pooled fallback is used, `gate_input_builder.py:24–26`).

### A§3.3 Population and inputs

A0 and A1 are computed on each of the three step-6 gate inputs (primary, PRE-DUP secondary, PRE-WDBC sensitivity)
(proposed; A§12 item 17), on that input's test block and population (A§2). The primary input's rows are the ones in the ladder table; the other
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

- A0 and A1 (A§3), on each of the three step-6 inputs (proposed; A§12 item 17);
- A2 and the oracle (gate series);
- A3 and A5 (gate series): their per-node rows and utility levels get intervals here; their aggregate IQM of gap
  closed and PoI keep the gate's own one-sided lower bounds, plus the upper bounds of A§5, and nothing else;
- the secondary arms in this read, as ARMS-SECONDARY A (R1-ARMS-DECISIONS) amends PRE-SECONDARY A: "the other Kev
  base, both Qwen controls, A4, and TabPFN in-context only if its version decision and a reviewed adapter land before
  the arms-frozen record", on the primary input only (proposed; A§12 item 17). PRE-SECONDARY A already allows their
  per-node test table; this amendment adds intervals and the aggregate statistics below (proposed; A§12 item 14). Each
  secondary arm's test series is computed by the **frozen builder
  unchanged**, called on the primary input's sources and T0 set with that arm's frozen predictions supplied as both
  `"A3"` and `"A5"` (`gate_input_builder.build`, `:348–486`); its series is the test block's `"A3"` series, and the
  code requires the `"A3"` and `"A5"` series to be equal and A2, the oracle and the instance ids to equal the
  committed primary input's (A§2).

The fold analyses and the g and per-mode recomputes keep their declared outputs (`fold_statistics`: point values and
both levels' lower bounds); this amendment adds no interval to them.

### A§4.2 Statistics and intervals

Which statistics each series gets (proposed; A§12 item 18):

| Series | Per node: ū, d̄, PoI | Per node: gap closed | Aggregate: Ū | Aggregate: IQM of gap closed | Aggregate: PoI |
|---|---|---|---|---|---|
| A0, A1, secondary arms | all three, with intervals | point and se | with interval | point, two-sided interval | point, interval |
| A3, A5 | all three, with intervals | point and se (the gate's) | with interval | the gate's point and lower bounds; A§5's upper bounds | the gate's point and lower bounds |
| oracle | all three, with intervals | 1 by construction | with interval | 1 by construction | point, interval |
| A2 | ū only | — | with interval | — | — |

The interval type per statistic in the next table is also proposed (A§12 item 18). All resamples are the gate's
(A§2): the same 2,000 index arrays per node for every series, so differences between
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
| aggregate: IQM_X of G_X,n over the gate's IQM-eligible nodes (`gate._node_iqm`; X ∉ {A2, oracle}) | as `gate._point` computes it for A3 | studentized, the gate's construction (`gate.py:451–456`, `:480–507`, `:523–527`) with X in place of the arm: lower end θ̂ − q₀.₉₇₅(t*⁺) ŝe, upper end θ̂ − q₀.₀₂₅(t*⁻) ŝe; t*⁺ holds `TSTAR_INF` on screened resamples (the gate's convention), t*⁻ holds −`TSTAR_INF` there (A§12 item 12); both ends equal θ̂ if ŝe = 0; the number of screened resamples is reported, and an end is reported as not finite when the quantile reaches a sentinel (A§5.1) |
| aggregate: PoI_X = node-equal mean of PoI_X,n over all nodes of the input (`gate._node_poi`; X ≠ A2) | as stated | percentile |

A2's rows are ū and Ū only (its gap closed and PoI against itself are degenerate). The oracle's gap closed is 1 on
every IQM-eligible node by construction and carries no interval. The IQM uses the gate's eligibility and is undefined
when the gate input STOPs (A§2).

## A§5. (c) One-sided upper bounds of the IQM of gap closed of A3 and A5

### A§5.1 Definition

On the **primary input** only (proposed; A§12 item 16), for X ∈ {A3, A5}: θ̂_X is the gate's point IQM of gap closed and ŝe_X its delta-method
se (`gate._point`, `gate.py:449–459`); t*_b (b = 1, …, 2,000) are the gate's studentized resamples from
`gate._bootstrap` (`gate.py:493–509`), and the screened resamples are those the gate sets to `TSTAR_INF` (an eligible
node's resampled denominator nonpositive, ŝe* = 0, or a non-finite t*; `gate.py:499–507`), identified by the
re-derived mask of A§2 step 2. Let t*⁻ equal t* except −`TSTAR_INF` on screened resamples. The one-sided upper bound
at level L is

  UB_L(X) = θ̂_X − Q_{1−L}(t*⁻) · ŝe_X,  with Q the linear quantile over the 2,000 resamples; UB_L(X) = θ̂_X if ŝe_X = 0.

It is the upper end of the same studentized construction whose lower end is the gate's bound
(θ̂ − Q_L(t*) ŝe, `gate._lower_iqm`, `gate.py:523–527`). The gate holds a screened resample at +∞ because that is the
conservative direction for a lower bound; for an upper bound the conservative direction is −∞ (proposed; A§12
item 12). For a resample with a nonpositive eligible-node denominator the gate sets IQM* = −∞ and leaves se* as NaN
(`gate.py:489–505`), so its t* is undefined until screened; −∞ is the limit of (IQM* − θ̂)/se* as IQM* → −∞ for any
positive se*, and the conservative value for an upper end. With m screened
resamples, the linear quantile reaches a sentinel when m ≥ ⌊1999 (1 − L)⌋ + 1 (50 at L = 0.975, 100 at L = 0.95);
UB_L is then reported as "no finite upper bound", with m.

### A§5.2 Levels

**Proposed (A§12 item 15): both arms at L = 0.975 and at L = 0.95; the text quotes L = 0.975.** Reasons for the
recommendation:

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

## A§6. (d) The dispersion estimate of T4 Proposition 7

### A§6.1 What is estimated

T4 Proposition 7 (`T4_FEEDBACK_PROPOSER.md` §3; `appendix.tex` `prop:app-gap`, lines 247–254) gives, for one
proposal with τ_n > 0 and π_n < 1 and any pre-execution threshold t̃, the loss of keeping with t̃ instead of the
per-proposal threshold t*_n, and the upper bound

  gap_n ≤ (1 − π_n) τ_n² (t*_n − t̃)² / (2√(2π) s_n³),  s_n² = τ_n² + σ_n²,  t*_n = −μ_n σ_n² / τ_n².

T4 §3 ("Reading") says the upper bound "needs only predicted (μ_n, τ_n) and the measured σ_n, so a pilot predictor …
gives an estimate (not a bound: the proposition bounds the gap in terms of the true (μ_n, τ_n)) of how much any better
predictor could still add". The estimate below is that reading, with the frozen A3 and A5 forecasts, against A2's
constant threshold. **It is an estimate, not a bound**: with fitted (μ, τ) its error is not controlled, and a forecast
that is too smooth understates the spread of the per-proposal thresholds (`results.tex`, paragraph "The dispersion
bound, as an estimate"; `appendix.tex` line 256). It covers the keep threshold only, at fixed execution decisions;
screening lies outside it. Its campaign-level reading (Corollary 7a) needs (NF), which the loops do not satisfy, so it
is read per proposal and scaled like U. Check status of Proposition 7 at drafting: AI-checked under R1-PROOF-POLICY,
not author-checked (T4 §3 status line, branch `mac-proofcheck-ai-20261123`); the computation does not depend on the
status, the manuscript's wording does.

### A§6.2 Population

The proposals of the **primary input's test instances**, exactly as the builder used them for the primary input's
test U: the PRE-DUP primary test population, in the modes PRE-MEM C kept for each instance (A§2; the same items as
A§3.3). Nodes: the primary input's nodes (the primary T0 set and the supplied T1 nodes). openml_wdbc and the PRE-DUP
secondary population are not used.

### A§6.3 Formula

For X ∈ {A3, A5}, node n, test instance i of the primary input, mode m, and each proposal p of the population of
(i, m):

- b_p = 0 if p is a no-op or a within-campaign duplicate (`arms.rule_skip`, `arms.py:67–69`): A2, A3 and A5 all skip
  it, so its keep threshold is never applied (and a no-op has π = 1).
- Otherwise: (π_p, μ_p, τ_p) = `arms.prior_moments([P_X(p)], [row_p])` of X's frozen 12-bin prediction for p (after the builder's rule
  layer, which leaves a non-no-op prediction unchanged; `gate_input_builder._rule_layer`, `:307–316`); (π̄_n, μ̄_n,
  τ̄_n) = `arms.prior_moments([a2_n], [row_p])` of A2's per-node vector a2_n from the arms-frozen record (A§9; σ_node
from the row for the τ floor); σ_p = p's `sigma_cmp`;
  t*_p = `rules.bayes_threshold(μ_p, τ_p, σ_p)`; t̃_p = `rules.bayes_threshold(μ̄_n, τ̄_n, σ_p)`, which is A2's keep
  threshold as A2 applies it (constant per node and edit kind; `offline_eval.decisions` → `rules.decide`);
  b_p = the upper element of `rules.gap_bounds(t̃_p, π_p, μ_p, τ_p, σ_p)` (`rules.py:81–91`), i.e. the bound above.
  This is the quantity `offline_eval`'s theory check already computes as `prop7_upper_mean` (`offline_eval.py:460–476`),
  here on the gate's population and with the frozen arms.
- Per instance and mode, scaled like U (§3): B_X(i, m) = 20 × Σ_p w_p b_p / Σ_p w_p over all proposals of the
  population of (i, m), rule-skipped proposals included in the denominator with b_p = 0 (A§12 item 13).
- Per instance: the mean of B_X(i, m) over the modes the builder kept for i (PRE-MEM C, with its fallback).
- **Per node:** D_X(n) = mean over the primary input's test instances of n of B_X(i), divided by σ_node,n.
- **Pooled** (proposed; A§12 item 19): the node-equal mean of D_X(n) over the primary input's nodes, also per tier;
  the median and range over nodes are reported beside it.

Reported per node with it: the number of population proposals, the number of non-inert non-duplicate proposals, and
the mean of b_p / σ_node,n over the latter (the per-proposal form of the theory check). No interval is attached
(proposed; A§12 item 19): an
instance resampling would cover neither the forecast's own error nor the distance between the estimate and the true
bound, so an interval would look more precise than the estimate is.

### A§6.4 Timing and reads

**Reads no label and no evaluation value.** Its inputs are: the table rows of the population reduced to `node`,
`proposal_id`, the no-op and duplicate flags, `sigma_node` and `sigma_cmp` (as `offline_eval.crossfit` strips rows
before a model sees them, `offline_eval.py:254–261`); X's frozen predictions; A2's per-node vectors from the
arms-frozen record (derived from the released dev label block and frozen; the only label-derived input, and not a
label of any proposal the estimate is computed on), which unit 3 has checked against `fit_a2` after step 6 (A§8; a
mismatch refuses (d) and never touches the gate run); the noise constants; and, from the step-6 build, the list of
population proposal ids per (instance, mode), which carries no value. **Computed after the test release row** of every
tier in the primary input (`release.test_released("T0")`, and `"T1"` if T1 nodes are supplied; `release.py:373–378`)
and after the primary input is committed in step 6; the code refuses otherwise. The reason for the order is that the
estimate then cannot inform the arms freeze or any choice made before the gate: the arms are frozen in the record the
test release row cites. The same formula computed earlier is not this estimate; since it reads no label it is not a
§6 STOP, but it is disclosed as a deviation.

## A§7. (e) C1: operational definitions, audit seeds and instances

R1-SUBMISSION-MIN (1): "C1: control errors measured from the fresh-seed audits of sweep 1 and sweep 2 on T0 (two
proposers)". The four rates are those of `problem.tex` lines 44–51; this section writes them as exact formulas, which
`problem.tex` line 52 asks to be "fixed before audit values are read". C1 is not a C3 statistic and reads no arm.

### A§7.1 Data

| | Sweep 1 (S1, the 7B manager) | Sweep 2 (S2, the main proposer) |
|---|---|---|
| Table (B.2 audit population) | `proposals.jsonl` sha256 `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4` (`B2_AUDIT_RUN_REVIEW_20261119.md` line 83) | `proposals.jsonl` sha256 `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` (`DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` line 46; `S2_B2_AUDIT_REPORT_20261122.md` line 33) |
| Proposals by kind | 4,999 proposals: 0 no-ops, 3,274 within-campaign duplicates, 1,725 audited (review lines 89–90) | 0 no-ops, 2,512 duplicates, 2,500 audited (report line 17) |
| Label / evaluation rows | 1,725 / 1,725 (review line 109) | 2,500 / 2,500 (report line 30) |
| Audit runs | 4,660 rows, 466 configurations × seeds 7001–7010 (review line 120) | 10,640 = 1,064 configurations × 10 (report line 29) |
| Train/dev release receipt (committed copy) | `RECEIPT_sweep1_traindev.json`, sha256 `f06e37a9…65c1`; label rows train 593, dev 276 (`SWEEP1_TRAINDEV_RELEASE_20261123.md` lines 25–30) | `RECEIPT_sweep2_traindev_v2.json`, sha256 `de95b218…d2d9c`; train 850, dev 422 (`SWEEP1_TRAINDEV_RELEASE_20261123.md` line 42; `S2_TRAINDEV_RELEASE_20261122.md` line 37) |

Both sweeps used the default loop (`results.tex` line 36). Both T0 tables carry σ_node from the pinned noise source
(§1, "Noise source"). C1 uses no feature, so R1-ARMS-FEATURIZER's v3 derivation is not needed; it reads the sealed
sweep-1 table as released.

### A§7.2 Audit seeds, instances, timing and fallback

- **Full C1 (the declared version).** Instances: every instance of the eight T0 nodes in each sweep's table (the 18
  sweep instance seeds per node of PRE-SPLIT's T0 design universe: train, dev and test alike), both memory modes.
  Seeds: all ten, labels 7001–7005 (label block) and evaluation 7006–7010 (evaluation block). Read **only** through
  receipted partitions after the T0 test release row (R1-S2-LABELS-TEST-RELEASE): per source (`sweep1`, `sweep2`),
  `label_block.traindev.jsonl` of the traindev partition and `label_block.test.jsonl` and `evaluation_block.all.jsonl`
  of the test partition, by `release.open_partition` with each receipt's sha256 pinned (`release.py:602–647`). Never a
  raw block, a run log or a B.2 evidence directory: `release.guard_raw_label_path`, called with `tier="T0"`, refuses
  them until the T0 test release row (`release.py:442–448`; with its default `tier=None` it would require the test rows
  of both tiers, `:403–412`), and after it the C1 code still opens only receipted partitions. (Copies of the
  sweep-1 raw blocks are committed under `docs/r1/reports/b2_audit_20261119/`; reading them is not a C1 input, and
  before the test release row it is a §6 STOP.) **Computed after the test release row**; the code refuses unless
  `release.test_released("T0")`.
- **Fallback (partial).** If no T0 test release row exists by the end of 3 January 2027, read anywhere on earth (UTC−12;
  proposed; A§12 item 10), i.e. by 2027-01-04T12:00Z: the train and dev instances
  only (P3: 6 train and 3 dev per T0 node), the label seeds 7001–7005 only, from the two traindev partitions above;
  every C1 table and figure is marked "partial: label seeds 7001–7005 only; train and dev instances only". The code
  refuses the partial mode before 2027-01-04T12:00Z or once the T0 test release row exists. What happens if the row
  appears after 3 January: A§12 item 5.
- C1's outputs are not used to train, tune or select any arm, and C1 reads no arm.

### A§7.3 The audit statistic, and how δ_n enters

**Audited increment.** The paired mean over the common fresh joint seeds (train seed = split seed = s;
`audit.py:3–6`), `audit.paired` (`audit.py:391–398`): Δ^aud_p = (1/10) Σ_{k=1..10} [m(candidate_p, 7000 + k) −
m(incumbent_p, 7000 + k)]. Every T0 evidence audit result has k = 10 (`audit.py:1006`) and exactly five paired values
in each half (`audit.py:1033–1035`); the label block holds the paired mean over 7001–7005 and the evaluation block over
7006–7010 (`audit.split_audit`, `audit.py:413–418`; `:1039–1045`). Hence, in arithmetic, **Δ^aud_p = (Δ_label,p +
Δ_evaluation,p) / 2**, computed from the two released rows; numerically the two sides agree up to rounding, and unit
5's test of this identity against `audit.paired` over ten seeds (synthetic data) states its tolerance. Unit 5 refuses
any label or evaluation row that is not complete (`k_label` ≠ 5, a label kind other than `audit` on an audited
proposal, `divergent_seeds` present, or `k_evaluation` ≠ 5): both sweeps' audits required complete rows, so none should
exist, and the code checks rather than assumes it. In the partial version Δ^aud_p = Δ_label,p. Sign convention: positive is an improvement, as
`offline_eval` uses Δ_true (keep iff Δ̂ > 0; r = Δ_true × keep). No standard error or test enters the definitions
(A§12 item 1).

**δ_n (PRE-DELTA A).** D18's δ_n unscaled, in metric units, per node, from the pinned noise source
(`results/r1/noise/D28_REPAIR_20261027/summary.json`, sha256 `3d12ce05…4310`) by `dataset.noise_table`
(`dataset.py:84`, `:105`): the δ_n of the gate and of the positive control's reading R-δ. It enters C1 in two places
only: the secondary readings and the near-zero share below. Record bias is in σ_node units from the same source.

### A§7.4 The four rates

Notation, for sweep s, T0 node n and the instance set of A§7.2: the campaigns c (instance × memory mode); P, the
table proposals of these campaigns (trial ≥ 2 with a parsed metric; `features.replay_campaign`, `features.py:517–569`);
A ⊂ P, the **audited proposals**: P without no-ops (`arms.is_noop`) and within-campaign duplicates
(`arms.is_duplicate`); for p ∈ A, kept_p ⇔ the table's logged decision is `"kept"` and discarded_p ⇔ `"discarded"`
(`features.py:552`; the default loop's own decision). #{·} counts proposals. No weights (complete population) and no
PRE-DUP exclusion (a cross-instance repeat is a decision of the default loop like any other) (proposed; A§12 item 6).
A table proposal whose decision is neither `"kept"` nor `"discarded"`, if any exists, is counted and reported, enters
neither FK nor MK, and for WR counts as wasted only if it is a no-op or a duplicate (it has a parsed metric, so it is
not invalid in WR's sense) (proposed; A§12 item 6).

The denominators of FK and MK (shares of keeps and of discards) are proposed (A§12 item 7).

1. **False-keep rate** ("kept candidates whose audited increment is not positive"):
   FK = #{p ∈ A : kept_p and Δ^aud_p ≤ 0} / #{p ∈ A : kept_p}.
2. **Missed-keep rate** ("discarded candidates whose audited increment is positive"):
   MK = #{p ∈ A : discarded_p and Δ^aud_p > 0} / #{p ∈ A : discarded_p}.
   Within-campaign duplicates are not audited and enter neither rate. Kept duplicates are counted and reported
   (expected 0 on bit-exact nodes, `prop:app-rules` (iii)).
3. **Record bias** ("the recorded gain of the incumbent minus its audited gain"), in σ_node units (proposed; A§12
   item 8). For campaign c, let K_c be its kept proposals in budget order and r_c the incumbent of its first table
   proposal (`incumbent_hash`): the configuration kept at the campaign's first valid trial — normally trial 1, which
   the harness keeps without comparison (`proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` line 90, B5); if trial
   1 is invalid, the first valid trial — so its own increment over the start configuration was never audited. Then
   **B_c = Σ_{p ∈ K_c} (Δ̂_p − Δ^aud_p) / σ_node,n** (B_c = 0 if c has no keep), and **RB = the mean of B_c over the
   campaigns** of the node. Why this is the stated quantity, over r_c, under the chain check below:
   - Σ_{K_c} Δ̂_p is the recorded metric of the final incumbent minus that of r_c, because for each kept p,
     Δ̂_p = metric_p − current_best_before_p (`delta_vs_best` and `current_best_before`, `features.py:550–557`; the
     identity the repository's fixtures use, `r1/tests/test_c3_sweep2_audit.py:57`), and current_best_before of a
     kept proposal is the metric of the previous one;
   - Σ_{K_c} Δ^aud_p is the ten-seed paired mean of m(final incumbent) − m(r_c), because each audit run is keyed by
     (node, configuration hash, seed) (`audit.py:25`) and the evidence cache holds exactly one run per key, with no
     duplicate and no missing key (`audit.evidence_cache`, `audit.py:1052–1066`), and every result is complete
     (`:1006`, `:1034`): the incumbent's run at seed s in the audit of a kept proposal is the candidate's run at s in
     the audit of the previous kept proposal. (In arithmetic; numerically up to rounding, n6 of the review.)

   **Chain check** (label-free; reads tables and ledgers only). For each campaign: every proposal before the first keep
   has incumbent r_c; for consecutive kept proposals, `incumbent_hash` of the later equals `candidate_hash` of the
   earlier and its `current_best_before` equals the earlier's `metric`; and for each kept proposal Δ̂_p equals
   metric_p − current_best_before_p as logged (exact equality of the logged values, proposed; A§12 item 8). A
   campaign that fails any part, or whose K_c holds a proposal outside A (a kept duplicate), gets **no B_c**; it is
   counted and reported, not refused. **The chain check runs before the test release row**, and its output (campaign
   ids and counts, no values) is committed, so the set of campaigns left out of RB is fixed before any audit value is
   read for C1. Secondary: the per-keep mean of (Δ̂_p − Δ^aud_p) / σ_node,n over kept p ∈ A (A§12 item 3).
4. **Wasted-run share** ("runs spent on no-ops, duplicates and invalid proposals"): WR = Σ_c W_c / Σ_c R_c with
   R_c = Σ over the rows ρ of c's root ledger of `features.row_worker_runs(ρ)` (`features.py:313–342`: one run for a row
   whose worker ran, none for a precheck rejection or a control-plane row) and W_c the same sum over rows that are
   (i) table proposals flagged no-op or within-campaign duplicate, or (ii) invalid: `decision == "skipped"` or no parsed
   metric (`features.parsed_metric`), the rows `replay_campaign` counts as `skipped_invalid` (`features.py:540–542`;
   sweep 1: 526 such rows, review line 93). It reads ledgers and tables only, no audit value. Runs by kind and invalid
   rows that cost no run are reported beside it. Instance set: A§12 item 4.
   **Ledgers** (also used by the chain check). Sweep 1: the committed root ledgers under
   `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z/provenance/ledgers/roots` and
   `results/r1/evidence/C3_sweep_none_20261027T224356Z/provenance/ledgers/roots` (144 campaign directories each).
   Sweep 2: the root ledgers of the sweep-2 batch named by the sweep-2 sweep index (`b4697c49…`,
   `S2_B2_AUDIT_REPORT_20261122.md` line 32); they are not on `main`, and unit 5's run record states the host path.
   Binding: the ledgers are located through the sweep index that the table's `build.json` pins, with the index's
   sha256 checked; since `dataset.py`'s index reader checks manifests (launch provenance, noise, runs, instances,
   `dataset.py:377–423`) but no per-ledger sha256, unit 5 also replays the ledgers with the table builder's own replay
   and requires the replayed proposals to equal the pinned `proposals.jsonl` rows and the replay counts (rows,
   `skipped_invalid`) to equal those recorded in `build.json` (sweep 1: 5,813 rows, 4,999 proposals, 526 skipped
   invalid, review lines 92–93); it records every ledger's sha256 in its output. A mismatch is an input refusal.

**Secondary readings with δ_n:** FK_δ = #{kept_p, Δ^aud_p < δ_n} / #{kept_p} (kept without an audited gain of the
practical size); MK_δ = #{discarded_p, Δ^aud_p ≥ δ_n} / #{discarded_p}; and the **near-zero share**
Z = #{p ∈ A : |Δ^aud_p| < δ_n} / #A, which shows how much the threshold-0 readings rest on increments the audit
places within δ_n of zero. The positive control's readings R-0 and R-δ at K = 10 and K = 5
(`CONTROLS_POSITIVE_20261123.md` §1.2) are the detection notions that match the threshold-0 and δ_n readings of the
full and partial versions.

**Aggregation.** Per node and sweep, both memory modes together (the rows of `tab:c1`; openml_wdbc as its own row,
marked as the sensitivity node, as `tab:c1` has it). **Pooled row:** FK and MK as ratios of the summed counts over
the pooled node set; RB as the mean of B_c over all its campaigns; WR as the ratio of summed runs. Pooled node set:
A§12 item 2.

**Intervals** (proposed; A§12 item 14). Per sweep, a node-stratified instance-cluster bootstrap with the gate's
generator, seed, resample count and draw order:
`numpy.random.Generator(PCG64(20261108))`, 2,000 resamples, for each node in sorted order one
`integers(0, n, size=(2000, n))` draw over its n instances in sorted instance-id order; an instance carries both its
campaigns with all their proposals and ledger rows; every statistic, node and pooled, is recomputed from the same draws;
two-sided 95 % linear-quantile percentile intervals. A resample in which a rate's denominator is 0 is left out for that
rate and counted (proposed; A§12 item 9). This departs from the gate's own rule for resamples it cannot use, which
are "counted and reported, never dropped" (`gate.py:35–37`).

## A§8. Code to write or reuse: reviewed tier-E units before the test release

In the style of §9. Each new or changed unit is tier E (R1-PROCESS-TIERS: gate and fold-analysis code, code that
reads label or evaluation records, the arms-frozen record), with a committed independent review re-checked until it
writes "accepted". Their sha256s are entered in this amendment's final block (A§13) before the arms-frozen record
(A§12 item 22).

| # | Unit | New or changed | For | What it does | Required tests (synthetic data only) |
|---|---|---|---|---|---|
| 1 | A1/A2 constants fitter | new; the D.3 draft's gap G2 (one unit serves D.3 and this amendment) | (a), (d) | Per node, `arms.ConstantPrior` and `arms.RulesPrior` on the rows `fit_a2` uses (A§3.1), from `release.traindev_labels` (sweep 2 for the eight T0 nodes; G.5 for the frozen T1 nodes) and the released tables through `guard_table`, rows filtered to P3 dev instances first (D.3 draft §5.0); writes one JSON with the per-node vectors, the σ values and the receipt, table and split-file sha256s | rows are passed in `proposal_id` order, as `fit_a2` receives them (`gate_input_builder.py:292`; `arms._wmean` sums in row order, `arms.py:79–81`), and the per-node A2 vectors equal `gate_input_builder.fit_a2`'s on the same rows **bitwise**; per-node vectors do not change when other nodes are added; no pooled fallback; refusal of test or evaluation rows |
| 2 | `r1/c3/arms_freeze.py` | changed | (a), (d), binding | The record gains the fields of A§9; `check_record` checks them, including the `amendments` entry's PLAN row (R1-POSTFREEZE-READS) the way it checks `REQUIRED_DECISIONS` (`arms_freeze.py:731–742`); every existing check unchanged; `arms` still equals `required_arms` (A0 and A1 are not added to it) | the existing tests pass with their fixture (`_record()`, `r1/tests/test_c3_arms_freeze.py:430`) extended by the new fields only; a record without the new fields, citing an absent row, with a wrong constants sha256, with vectors differing from the constants file, or (when the D.3 constants file is pinned) differing from it for a D.3 node is refused (an input refusal of the record, fixable before any test read) |
| 3 | `r1/c3/descriptive_rows.py` | new | (a), (b), (c) | After step 6: recomputes `fit_a2` and `ConstantPrior` on the step-6 sources' dev rows (in `proposal_id` order) and requires them to equal the record's A2 and A1 vectors bitwise — a mismatch refuses (d) and A1's rows and never touches the gate run; A0 and A1 test series on the three step-6 inputs (population as A§2; A2 and the oracle recomputed with `_series_rewards` and bound to the committed input); secondary arms' series through the frozen builder (A§4.1); the gate's resamples re-derived and checked against `gate._bootstrap`; the A§4 statistics; the A§5 upper bounds, after checking the recomputed gate statistics against the committed gate output; on a gate-input STOP, point rows only (A§2) | A0 equals `offline_eval.rho` + `rewards`, A1 equals `ConstantPrior` + `decisions(rule_layer=False)`, kept-duplicate proxy as `offline_eval`; A2/oracle reproduction equals the builder's for all three populations (PRE-DUP fallback and left-out instances, a T1 node, T1 under K = 6); re-derived resamples reproduce `gate._bootstrap`'s t*, screened count and PoI bitwise, on a fixture that includes an IQM-ineligible node ordered before an eligible one (every node consumes generator state, `gate.py:475–477`); the record-vector check refuses a one-ulp difference; upper bound mirrors the gate's lower bound on a symmetric fixture; sentinel rule at m = 49/50 (L = 0.975) and 99/100 (L = 0.95); refusals without the test release row, with an altered step-6 input or gate output |
| 4 | `r1/c3/dispersion_estimate.py` | new | (d) | A§6.3 on rows reduced as A§6.4, with the frozen predictions, A2's vectors from the record (used only after unit 3's record-vector check passed) and the population ids from unit 3 | equals `rules.gap_bounds`' upper element per proposal; equals `offline_eval`'s `prop7_upper_mean` on a fixture where the populations coincide; refuses a row carrying a label, evaluation or outcome field other than the flags; refuses before the test release row |
| 5 | `r1/c3/c1_rates.py` | new | (e) | A§7 from receipted partitions (pinned receipts), the released tables and the root ledgers bound as in A§7.4 (4); a label-free **chain-check mode** run and committed before the test release row (A§7.4 (3)); full and partial modes with their guards; the bootstrap | the ten-seed identity against `audit.paired` and the telescoping identity on a synthetic campaign with shared runs, each to a tolerance the unit states; chain-check cases (each failure gives no B_c and is counted); refusal of incomplete label or evaluation rows (A§7.3); ledger binding (a replay that differs from the pinned table or from `build.json`'s counts is refused); rates and record bias against hand-computed fixtures; wasted runs against `features.row_worker_runs`; bootstrap reproducible; refusals: full mode without the T0 test row, partial mode before 2027-01-04T12:00Z or with the row, any raw block or evidence-directory path |

**Reused unchanged:** `gate.py` (`_validate`, `_point`, `_bootstrap`, `_node_iqm`, `_node_poi`, `_node_se`, `_wins`,
`_lower_iqm`, constants), `gate_input_builder.py` (`build`, `runs`, `_prepare`, `_check_sources`, `_declared_modes`,
`_series_rewards`, `fit_a2`, `_rule_layer`, `Source`, `Tier1`), `fold_analysis.py` (the `_bind` check and the
`fold_statistics` pattern), `offline_eval.py` (`rho`, `decisions`, `rewards`, `CAMPAIGN_RUNS`, `G_PRIMARY`), `arms.py`,
`rules.py`, `labels.py`, `release.py` (`builder_source`, `open_partition`, `traindev_labels`, `test_released`),
`audit.py` (`paired`), `features.py` (`row_worker_runs`, `parsed_metric`, `replay_campaign`), `dataset.py`
(`load_table`, `noise_table`). Units 3–5 each have a CLI that writes its outputs and a `SHA256SUMS` under
`results/r1/evidence/`, committed with a tier-E report.

## A§9. What the arms-frozen record must additionally contain

Beyond §4 step 4 and the fields `arms_freeze.check_record` already requires (`REQUIRED_TOP`, `arms_freeze.py:542–544`):

- **`amendments`**: this amendment's path and sha256, as frozen (A§13), and its PLAN row (R1-POSTFREEZE-READS), which
  unit 2 looks up in PLAN. The test release row cites the record's sha256, so it binds the amendment too.
- **`rule_arms.A0`**: the rule identifier `r1.c3.offline_eval.rho` (execute every proposal; keep iff Δ̂ > 0); no
  constants.
- **`rule_arms.A1`** and **`rule_arms.A2`**: per node, the 12-bin vector, for all eight T0 nodes (the PRE-WDBC
  sensitivity set) and every node of the frozen T1 set; the fitter's path, sha256 and code commit; the constants
  file's path and sha256; the traindev receipt sha256s it read (sweep 2; G.5); the fit population ("dev label block,
  full dev population, gate sources"); for A1, "no rule layer; no verify offline".
- **`rule_arms.d3_constants`**: the D.3 constants file's path and sha256 if it is pinned by then; the A1 and A2
  vectors of the seven D.3 nodes must equal it (R1-D3-MIN; D.3 draft §10). If the D.3 pre-declaration is not yet
  signed, the field is null and the D.3 pre-declaration must later pin the same vectors.

Nothing else in the record changes. A2's vectors are recorded so that (d) reads no label; unit 3 checks them, and
A1's, against `fit_a2` and `ConstantPrior` after step 6 (A§8), outside the gate run.

## A§10. What is reported where

| Item | Output | Manuscript place (branch `mac-manuscript-20261122`) |
|---|---|---|
| (a) A0, A1 | per-node rows on the primary input, with intervals; the same on the PRE-DUP secondary and PRE-WDBC sensitivity inputs | aggregates in `tab:ladder` (rows A0, A1, "not tested"); per-node rows in an appendix table beside the gate's per-node table |
| (b) intervals | per-node and aggregate statistics of A§4.2 for every row of A§4.1 | `tab:ladder` (U, IQM gap closed, PoI with intervals for descriptive rows), `fig:ladder`; per node in the appendix |
| (c) upper bounds | UB₀.₉₇₅ and UB₀.₉₅ of A3 and A5, with screened counts | results §C3, paragraph "Effect sizes" (both outcomes); `tab:ladder` beside the lower bounds |
| (d) dispersion estimate | D_A3(n), D_A5(n), pooled and per tier, with the counts of A§6.3 | results §C3, paragraph "The dispersion bound, as an estimate"; `tab:app-dispersion` |
| (e) C1 | FK, MK, RB, WR per node and sweep, pooled row, intervals; FK_δ, MK_δ, Z; kept duplicates and left-out campaigns; "partial" if the fallback applies | `tab:c1`, `fig:c1`, results §C1; the δ_n readings and Z in an appendix table |

Every output is labelled descriptive and carries this amendment's sha256.

## A§11. Lock check: nothing here can be satisfied by an earlier read

| Item | What it reads | Earliest moment its inputs exist | Guard | Could an earlier read satisfy it? |
|---|---|---|---|---|
| A1, A2 constants | the released dev label block (no test label, no evaluation value) | now (both traindev partitions are released, A§7.1) | `release.traindev_labels` with pinned receipts | not a test read; allowed before the record (§4 step 3) |
| (a) A0, A1 rows | Δ_true of test proposals from the evaluation block; the A1 constants | the test release row (§4 step 5) | the test partition opens only with a receipt bound to the test row (`release.open_partition`, `builder_source`); the committed step-6 input is required; `release.test_released` | no: without the test partition there is no Δ_true; a value from any other path is a §6 STOP and is not an input the code accepts |
| (b) intervals | test series of every row | step 6 | as (a); the committed gate output is required | no |
| (c) upper bounds | the gate's resamples on the committed primary input and the committed gate output | step 6 | `require_d8_confirmation`, `_require_pins`, the equality check with the committed output | no |
| (d) dispersion | no label and no evaluation value | its inputs exist at the arms freeze, but the declared population is the committed step-6 primary input's | `release.test_released` for every tier of the input; the committed step-6 input is required | no: an earlier computation is not the declared estimate; it is not a §6 STOP (no label read) but is disclosed as a deviation |
| (e) C1, full | test label blocks and every evaluation block of both sweeps | the T0 test release row | receipted partitions only; `release.test_released("T0")` | no; raw blocks or evidence directories are refused by `guard_raw_label_path` before the row and are never C1 inputs |
| (e) C1, partial | traindev label blocks (label seeds) | now | the code refuses before 2027-01-04T12:00Z and once the T0 test row exists | the data are readable now; computing C1 from them earlier is not the declared fallback and is disclosed (see the attestation below) |
| (e) C1 chain check; WR | tables and root ledgers (no label, no evaluation value) | now | ledger binding of A§7.4 (4) | the chain check is meant to run before the test release (A§7.4 (3)); WR is computed with the rest of C1 and is not restricted by the lock |

None of the items is used to train, tune, select or calibrate an arm, and all of (a)–(d) and the full C1 come after
the arms-frozen record, which the test release row cites. **No verdict, gate, arm selection or preregistered
statistic changes:** the gate and builder files and their sha256s are untouched; the three step-6 gate runs, the Holm
step and the verdict are computed as before and only checked for equality; the fold and secondary-run outputs are
unchanged; `arms` in the record is unchanged.

**Signing order.** R1-POSTFREEZE-READS requires signature before the arms-frozen record, which is committed no later
than 20 December 2026 (R1-ARMS-FREEZE-CUTOFF). The consequence of a missed signature is not in the row (proposed;
A§12 item 23): (a)–(d) are not computed (they would be test reads outside PRE-SECONDARY's scope) and are listed as
omissions in the deviations table, and C1's definitions need their own signed declaration before any C1 statistic is
computed.

**What has already been read** (m6 of the review). The definitions can precede every computation of a C1 statistic,
but not every read of an audit value. Before this draft, audit values were read for other purposes:
- sweep 1's label block, by the Track P SFT engineering runs (R1-TRACKP-SFT-DEV, which excludes the evaluation block;
  disclosed in the arms-frozen record under §4 step 4 and §6);
- both sweeps' train/dev label blocks, by arm training, selection and calibration (§4 step 3), and by the D.3
  constants fitter, as released (A§7.1);
- both audits' label and evaluation values, by the independent run reviews that recomputed the blocks from the run
  logs (`B2_AUDIT_RUN_REVIEW_20261119.md` line 109; `S2_B2_AUDIT_RUN_REVIEW_20261122.md` lines 31 and 65);
- inside the release step, by the integrity checks, which output only pass/fail, counts and hashes (§6 carve-out).
None of these, as far as the committed reports show, computed one of the four rates. The drafter read no label or
evaluation value.

**Attestation at signing** (proposed; A§12 item 24): the coordinating chat records that no C1 statistic (any of the
four rates or their δ_n readings, on any instance set) has been computed from a label or evaluation block of either
sweep before the signature, or discloses any that was; and it lists any read of audit values for other purposes
beyond those above. The manuscript's `problem.tex` line 52 needs the matching qualification (follow-ups, A§12).

## A§12. Open for the author

Each item is a choice that R1-POSTFREEZE-READS, the preregistration and the code do not settle. Each is **proposed,
not decided**: the text above uses the recommendation, and the author's signature settles it (or the author picks
another option, and the text changes before signing).

*C1 (e).*

1. **C1's headline reading.** *Recommended:* threshold 0 (the wording of `problem.tex`: "not positive", "positive")
   as the headline; the δ_n readings and the near-zero share as declared secondaries. *Alternative:* δ_n as the
   headline. A per-proposal t-test reading (the positive control's R-t) is not recommended: it would make the rates
   depend on the audit's own se at five or ten seeds.
2. **Pooled C1 row's node set.** *Options:* the seven primary T0 nodes (PRE-WDBC primary set) with the eight-node
   value beside it; or all eight nodes (C1 is not the gate). *Consequence to weigh:* openml_wdbc is outside the primary
   set because it failed the D28 `invalid_rate` check (R1-S2C3B-WDBC); that is a wasted-run property, so leaving it
   out of the pooled row lowers the pooled wasted-run share by construction. *Recommended:* the seven nodes, with the
   eight-node value printed beside every pooled cell so that the difference is visible; openml_wdbc keeps its own row.
3. **Record bias.** *Recommended:* the mean of B_c over all campaigns (B_c = 0 without a keep) as the headline, the
   per-keep mean as secondary. *Alternative:* the mean over campaigns with at least one keep. The reference is the
   configuration kept at the first valid trial (normally trial 1) in every option; the manuscript should say so.
4. **Wasted-run share in the partial version.** *Recommended:* all instances, in both versions (it reads no audit
   value, so the lock does not restrict it). *Alternative:* train and dev instances only, so the partial table uses
   one instance set.
5. **If the T0 test release row appears after 3 January 2027.** *Recommended:* the full C1 replaces the partial one
   whenever the row exists before the full-paper deadline (22 January 2027, R1-SUBMISSION-MIN); the same code
   computes both, and the partial one stays in the appendix. *Alternative:* once the fallback date passes, the partial
   C1 is the submission's C1 whatever happens later, and the full C1 waits for a later version. Fixing either now
   removes a choice that could otherwise be made after seeing partial values.
6. **C1 population and weighting.** *Recommended:* all audited proposals, no PRE-DUP exclusion and no weights (the
    population is complete; a cross-instance repeat is a decision of the default loop like any other); a table
    proposal whose decision is neither kept nor discarded is counted, kept out of FK and MK, and counted as wasted in
    WR only if it is a no-op or a duplicate. *Alternative:* count each (node, incumbent hash, candidate hash) key once,
    as PRE-DUP does for the gate, which would weight later-campaign decisions more.
7. **Denominators of FK and MK.** *Recommended:* FK as a share of keeps and MK as a share of discards (the reading of
    `problem.tex` and of `results.tex` line 72, "a share of keeps"; manuscript text is not a decision). *Alternative:*
    rates conditional on the audited truth: the share of audited non-positive candidates that were kept, and the share
    of audited positive candidates that were discarded (the denominator `results.tex` line 72 contrasts with). The
    alternative could be reported as a secondary at no extra cost.
8. **Record-bias units and the chain check's equality.** *Recommended:* σ_node units (as `tab:c1`'s caption has it),
    and exact equality of the logged values in the chain check's Δ̂ identity (failures counted, known before the test
    release). *Alternatives:* δ_n or metric units; a stated tolerance for the Δ̂ identity.
9. **C1 resamples with a zero denominator.** *Recommended:* left out for that rate and counted (A§7.4). *Alternative:*
    no interval for a rate in any cell where some resample has a zero denominator. Neither is the gate's rule
    ("counted and reported, never dropped", `gate.py:35–37`), which has no analogue for a ratio with an empty
    denominator.
10. **Time zone of the fallback date.** *Recommended:* the end of 3 January 2027 anywhere on earth
    (2027-01-04T12:00Z), the convention of the ICML dates in R1-SUBMISSION-MIN; it gives the test release the most time.
    *Alternatives:* the end of 3 January in UTC (the first draft's reading) or Europe/Berlin.

*C3 rows (a)–(d).*

11. **Kept within-campaign duplicates under A0 and A1.** *Options:* (i) `offline_eval`'s convention, the logged Δ̂ as
   a proxy, counted; (ii) Δ_true = 0; (iii) an evaluation-seed value without new runs: the duplicate's configuration C
   occurs earlier in the same campaign as an audited candidate or incumbent, and evidence runs are unique per (node,
   configuration hash, seed), so Δ_eval(C vs the current incumbent) = Δ_eval(C vs I_j) − Σ Δ_eval over the proposals
   kept between that occurrence and the duplicate (I_j being C's incumbent at its audited occurrence); this holds on
   bit-exact nodes and to the extent that the active-projection identity behind `is_duplicate` implies identical runs;
   it departs from `offline_eval` and needs new code. *Consequence:* under (i) and (ii), U_A1 ≤ U_A2 on every T0
   instance by construction (A§3.1), so A1's T0 PoI against A2 is at most 0.5 and its gap closed at most 0; under
   (iii) the sign is measured. *Recommended:* (i), because the row asks for A0 and A1 as the code defines them, with
   the structural sign stated beside the rows.
12. **Screened resamples at the upper end of an interval or bound.** *Recommended:* −`TSTAR_INF` (A§5.1), the
   conservative direction for an upper end. *Alternative:* the gate's +`TSTAR_INF` array as is, which is not
   conservative for an upper end.
13. **Denominator of the dispersion estimate.** *Recommended:* all population proposals, rule-skipped ones at b_p = 0,
   so the estimate has U's 20-proposal scale and can be read beside the gate's numbers; the per-non-inert mean is
   reported beside it. *Alternative:* non-inert proposals only, as `offline_eval`'s theory check.
14. **Additions beyond the row's letter.** (i) Aggregates (Ū, IQM of gap closed, PoI) for A0, A1 and the secondary arms,
   which the row names as per-node rows; (ii) intervals for C1, which the row does not name. *Recommended:* include
   both: `tab:ladder` and `tab:c1` need them, and R1-SUBMISSION-MIN asks for "effect sizes with intervals for every
   arm". *Alternative:* per-node rows only, and C1 as point values.
15. **Levels of (c), and which one the text quotes.** *Recommended:* both arms at 97.5 % and at 95 %, the text quoting
    97.5 % (A§5.2: the Holm ranking is data-dependent; two one-sided 97.5 % bounds give joint 95 % coverage by
    Bonferroni; FOLD-LEVELS A reports both levels). *Alternatives:* each arm at the Holm level the gate assigned it
    (97.5 % for the first-ranked, 95 % for the second); or 95 % for both.
16. **Which input (c) uses.** *Recommended:* the primary input only (the input that carries the verdict).
    *Alternative:* also the PRE-DUP secondary and PRE-WDBC sensitivity inputs, beside their gate runs.
17. **Which inputs each row uses.** *Recommended:* A0 and A1 on all three step-6 inputs (they are cheap and complete
    the per-node tables of each gate run); the secondary arms on the primary input only (PRE-SECONDARY A allows their
    per-node test table without naming inputs; one input keeps that table small). *Alternatives:* every row on the
    primary input only; or every row on all three inputs.
18. **Statistics per series and the interval type per statistic** (A§4.2). *Recommended:* percentile intervals for
    utility means, differences and PoI; the gate's studentized construction for the IQM of gap closed; no bootstrap
    interval for per-node gap closed, only its delta-method se, as the gate's own per-node table reports; A3 and A5
    get per-node intervals and utility-level intervals, while their aggregate IQM and PoI keep the gate's bounds plus
    (c). *Alternatives:* percentile intervals for every statistic, the IQM included; or studentized per-node gap closed
    intervals (the gate's per-node se is available in each resample).
19. **The dispersion estimate's summary.** *Recommended:* no interval (an instance resampling covers neither the
    forecast's error nor the distance to the true bound), and a node-equal mean pooled summary, per tier, with the
    median and range. *Alternatives:* a percentile interval over the gate's resamples, labelled as instance noise only;
    an IQM over nodes as the pooled summary, matching the gate's aggregate.
20. **Reporting when a gate input STOPs.** *Recommended:* IQM-based quantities reported as the STOP; point PoI and
    point utility rows still reported, without intervals (A§2), extending FOLD-POI A from folds to these rows.
    *Alternatives:* intervals for the PoI and utility rows from re-derived draws validated only on a fixture or on
    another step-6 input that does not STOP; or nothing reported for that input beyond the STOP.
21. **The Ladder margin rule.** R1-MINSUB-CHOICES (4) says an offline test read of it needs a signed amendment.
    *Recommended:* not added here (the row does not ask for it). *Alternative:* add it as a third rule row with A0's
    population; its pinned η per node would then also enter the arms-frozen record (R1-D3-MIN: "an arm reads test only
    if it is in the arms-frozen record").

*Procedure.*

22. **When the code is bound.** *Recommended:* units 1–5 reviewed and their sha256s entered in A§13 before the
    arms-frozen record, which pins the frozen amendment. *Fallback for units 3–5 only:* a CONFIRM-type author row
    binding a unit's sha256 before the test release row; a unit bound by neither is not run, and its item is listed as
    an omission. Units 1 and 2 have no fallback: the record must carry the A1/A2 vectors and the new fields when it is
    committed, so if either is not bound by then, A1's rows and the record-based input of (d) are lost (listed as
    omissions).
23. **If this amendment is not signed before the arms-frozen record.** *Recommended:* (a)–(d) are not computed and
    are listed as omissions; C1's definitions need their own signed declaration before any C1 statistic is computed.
    *Alternative:* a late signature before the test release row keeps (b)–(e) and loses only A1's frozen constants
    (so A1's rows); (a) A0's rows need no constants and could be kept too.
24. **The attestation at signing** (A§11). *Recommended:* the coordinating chat attests that no C1 statistic has been
    computed and lists reads of audit values for other purposes beyond those A§11 names. *Alternative:* no attestation;
    the arms-frozen record's existing disclosures (§4 step 4) stand alone.

**Follow-ups outside this amendment** (none is a conflict with the preregistration; each needs action elsewhere):

- **Rows on `main`.** The eleven rows listed at the top must reach `main` (for example by fast-forwarding to
  `author-minsub-mergeready-20261123` @ `055cacc5`) before signing.
- **Arms readiness and the record writer.** `T0_ARMS_READINESS_20261123.md` §1 (lines 26–29) lists A0 as "not in this
  read" and A1 and A2 as having nothing to freeze. Under this amendment A0 and A1 are read descriptively and the record
  carries A1's and A2's vectors (A§9), as the D.3 draft's §5.0 and §10 already require for the seven D.3 nodes.
  Neither `arms_freeze.py` nor `DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` has a step for them yet (units 1 and 2).
- **D.3 draft alignment.** The D.3 draft's G2 fitter filters to "the P3 dev instances of the seven nodes" (§5.0).
  Unit 1 fits all eight T0 nodes and the frozen T1 nodes; if one unit serves both, the D.3 text says so (its seven
  vectors are unchanged, since each node's vector uses only that node's rows).
- **Manuscript (tier D; not edited here).**
  - `results.tex`, paragraph "The dispersion bound, as an estimate" (line 142): "is descriptive and is not part of the
    preregistration" changes once this is signed; the same paragraph says the campaign-level reading needs (NF) and
    (NI), while T4 Corollary 7a and A§6.1 say (NF).
  - The TBDs of `tab:ladder`'s caption (line 90), the "Effect sizes" paragraph (line 139), `tab:c1`'s caption
    (line 39), `results.tex` line 36 and `problem.tex` line 52 are answered by A§4, A§5 and A§7 and by A§12.
  - Record bias: "the recorded gain of the final incumbent over the first incumbent (the configuration kept at the
    first valid trial)" (A§7.4 (3)).
  - **Proposed qualifying text for `problem.tex` line 52** (m6): "The operational definitions of the four rates, and
    the audit seeds and instances they use, were fixed in a signed amendment of the preregistration before any of the
    rates was computed. Audit values had been read before that for other purposes: the label values of training and
    development instances to train, select and calibrate the arms, the label values of sweep 1 for an engineering
    run of the fine-tuning pipeline, and both audits' label and evaluation values by the independent reviews that
    recomputed them; none of these computed a rate."
- **Ledgers.** The wasted-run share counts invalid proposals, which are not rows of the B.2 tables, so C1 reads the
  sweeps' root ledgers (label-free; A§7.4 (4), A§11).

## A§R. Response to review

Review `docs/r1/reviews/C3_PREREG_AMENDMENT_POSTFREEZE_REVIEW_20261123.md` (@ `104730e2`, not accepted). One line per
finding; commits on `mac-postfreeze-reads-20261123`.

| Finding | Response | Commit |
|---|---|---|
| M1 | Fixed. Every choice beyond the row is now an A§12 item with options and a recommendation, written as proposed (items 6–10 and 12–24 are new or extended; items renumbered 1–24 in reading order); the text marks each use "(proposed; A§12 item n)", and the front matter says so. | `fdd70bab`, `987b7676`, `73c753ac`, `a35edce0`, `19e082bc` |
| m1 | Fixed. On a gate-input STOP the PoI and utility rows are points only, without intervals, because neither binding check can run; listed as item 20 with the alternatives. | `fdd70bab` |
| m2 | Fixed. The record-vector check is in unit 3, after step 6, bitwise (unit 1 fits in `proposal_id` order, as `fit_a2`); a mismatch refuses (d) and A1's rows and never touches the gate run; unit 4 uses the vectors only after that check. | `fdd70bab`, `73c753ac` |
| m3 | Fixed: the existing tests pass with the fixture extended by the new fields only. | `73c753ac` |
| m4 | Fixed. (a) A chain failure gives no B_c and is counted, not refused; the chain check runs before the test release and its output is committed. (b) The Δ̂ identity is part of the check. (c) Citations added (`audit.py:25`, `:1006`, `:1034`, `:1052–1066`); unit 5 refuses incomplete label or evaluation rows. | `987b7676` |
| m5 | Fixed. The header names `origin/author-minsub-20261122` @ `d3f03e2c` and `author-minsub-mergeready-20261123` @ `055cacc5`, lists all eleven cited rows absent from `main`, says they must be on `main` before signing, gives the procedural reason, and unit 2 now checks the `amendments` entry's row. | `7429a9bb`, `73c753ac` |
| m6 | Fixed. A§11 discloses the earlier reads of audit values (Track P SFT on sweep 1; arm training and the constants fitter on train/dev; both run reviews' recomputation; the release integrity checks); the attestation covers "no C1 statistic computed" plus other reads; proposed qualifying text for `problem.tex` line 52 is in the follow-ups (manuscript not edited). | `7429a9bb`, `73c753ac` |
| m7 | Fixed. Ledger locations stated (sweep 1 committed paths; sweep 2 from its batch via index `b4697c49…`), bound by the index sha256 plus a replay that must reproduce the pinned table and `build.json`'s counts; a lock-table row added; non-kept/discarded decisions defined (item 6). | `987b7676`, `73c753ac` |
| m8 | Fixed: item 2 states that leaving openml_wdbc out lowers the pooled wasted-run share by construction; the recommendation now prints the eight-node value beside every pooled cell. | `a35edce0` |
| m9 | Fixed: item 11 adds the evaluation-seed option (with the sign written as Δ_eval(C vs I_j) − Σ kept increments; the review's "+" is a sign slip) and the structural U_A1 ≤ U_A2 on T0, also stated in A§3.1. | `fdd70bab`, `a35edce0` |
| n1 | Fixed (517–569; 313–342). | `987b7676` |
| n2 | Fixed (§1, lines 26–29). | `7429a9bb` |
| n3 | Fixed (IQM* = −∞ and se* = NaN; −∞ as the limit and the conservative value). | `fdd70bab` |
| n4 | Fixed (`prior_moments(P, rows)`). | `fdd70bab` |
| n5 | Fixed (`tier="T0"`). | `987b7676` |
| n6 | Fixed (arithmetic identity; unit 5 states its tolerance). | `987b7676`, `73c753ac` |
| n7 | Fixed (a table of statistics per series in A§4.2). | `fdd70bab` |
| n8 | Fixed (first valid trial; also in item 3 and the follow-ups). | `987b7676`, `a35edce0` |
| n9 | Fixed (stated in A§3.1). | `fdd70bab` |
| n10 | Fixed (item 5 has an alternative). | `a35edce0` |
| n11 | Fixed (item 21: η would enter the record). | `a35edce0` |
| n12 | Fixed (follow-up: D.3 text alignment). | `7429a9bb` |
| n13 | Fixed (follow-up for the manuscript). | `7429a9bb` |
| n14 | Fixed (an input refusal of the record, fixable before any test read; A§3.2 and unit 2). | `fdd70bab`, `73c753ac` |
| n15 | Fixed (unit 3's bitwise test includes an ineligible node before an eligible one). | `73c753ac` |
| Item 11 (check 7) | Fixed: the CONFIRM-row fallback is limited to units 3–5; units 1–2 have none, and the loss is stated (item 22). | `a35edce0` |

No finding is declined.

## A§13. Final block

```
amends: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
plan_row: R1-POSTFREEZE-READS
status: DRAFT
frozen: false
constants_fitter_sha256: <pending: unit 1>
arms_freeze_sha256: <pending: unit 2>
descriptive_rows_sha256: <pending: unit 3>
dispersion_estimate_sha256: <pending: unit 4>
c1_rates_sha256: <pending: unit 5>
open_items: 1-24 <pending: author>
signed_by: <pending>
frozen_utc: <pending>
```
