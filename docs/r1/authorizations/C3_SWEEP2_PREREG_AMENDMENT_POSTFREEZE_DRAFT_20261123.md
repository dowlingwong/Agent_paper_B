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
`predictions` pin of each arm, `arms_freeze.py:551`); the noise constants of PRE-DELTA. "The primary input" is the
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
