# Review: post-freeze reads amendment to the sweep-2 C3 analysis preregistration (draft of 23 Nov 2026)

**AI-assisted (Claude, independent reviewer subagent, 23 Nov 2026).** Tier E review (R1-PROCESS-TIERS). I did not
write the material under review.

- Reviewed: `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_DRAFT_20261123.md`, branch
  `mac-postfreeze-reads-20261123` @ `a97ec3fa` (based on `origin/main` @ `89899f76`; the branch adds only this file).
- Against: PLAN row R1-POSTFREEZE-READS (`author-minsub-20261122` @ `d3f03e2c`, which `git ls-remote` shows is now
  the head of `origin/author-minsub-20261122`); the rows named in the task; the signed preregistration (sha256
  `aa1a961b…7cc5`, verified); the code on `main` @ `89899f76`; the manuscript on `mac-manuscript-20261122` @
  `a93c1cea`; T4 on `mac-proofcheck-ai-20261123` @ `79f6442f`; the D.3 draft on `mac-d3-predecl-20261122` @
  `a24a55bf`; the positive control on `mac-controls-pos-20261123` @ `25d5a510`.

## Verdict: **not accepted**

There is one MAJOR finding. Several choices that R1-POSTFREEZE-READS does not settle are written as decided and are
missing from A§12, although the draft says (line 16–17) that every unsettled choice is listed there. Fixing this means
listing those choices; no rule needs to change. The code citations, the reuse of the gate's resamples, the upper-bound
construction and its sentinel rule, the C1 formulas and the lock design are correct, apart from the minor points
below. Once M1 is fixed and the MINOR findings are corrected or answered, I expect to accept on re-check.

## Findings

### MAJOR

**M1. Author choices written as decided and not listed in A§12** (draft lines 16–17, 265–273, 247, 187–191,
213–220, 229–237, 331–334, 117–119, 409–414, 458–463, 538–543, 383–387).
The task (check 1) and the draft's own front matter both require every choice beyond the row to be shown to the author
as a choice. A§12 item 9 lists two such choices (aggregates for A0, A1 and the secondary arms; intervals for C1). The
following are not listed:

1. **Levels of (c)** (A§5.2, lines 265–273): "both arms at L = 0.975 and at L = 0.95; the text quotes L = 0.975". This
   comes with reasons, but the row gives no level. The choice sets the number the paper quotes.
2. **Which input (c) is computed on** (A§5.1, line 247): "on the primary input only". The row does not say.
3. **Which inputs the rows are computed on** (A§3.3 lines 187–191; A§4.1 lines 213–217): A0 and A1 on all three step-6
   inputs, but the secondary arms on the primary input only.
4. **Interval type per statistic** (A§4.2 table, lines 229–237): percentile intervals for utility means, differences
   and PoI; the studentized construction only for the IQM; no bootstrap interval for per-node gap closed (delta-method
   se only). The row says "by the gate's instance-cluster bootstrap", and the gate itself uses both constructions, so
   the assignment is a choice.
5. **No interval for (d)** (A§6.3, lines 331–334), together with the pooled summary (node-equal mean, per tier, median
   and range, lines 328–329). The row's (b) asks for intervals "for every descriptive row", so leaving (d) without one
   is at least an author choice. The reason given is sound, but it should be presented as a recommendation.
6. **Reporting when the gate input STOPs** (A§2, lines 117–119): "the PoI and utility rows are still reported, as
   FOLD-POI A does for folds". FOLD-POI A is an author decision about folds, so extending it to these rows is a new
   choice (see also m1).
7. **C1 definitional choices** (A§7.4, lines 409–414 and 458–463):
   - no PRE-DUP exclusion and no weights;
   - the denominators of FK and MK (share of keeps; share of discards). This matches `results.tex` line 72 ("Our
     false-keep rate is a share of keeps"), but manuscript text is tier D, not a decision, and the conditional-on-truth
     rate that line 72 contrasts with is the obvious alternative;
   - record bias in σ_node units (as the `tab:c1` caption has it);
   - the C1 bootstrap leaves out resamples with a zero denominator. The gate's convention is "counted and reported,
     never dropped" (`gate.py:35–37`), so this cannot be described as "the gate's conventions" without a qualifier.
8. **Procedural rules not in the row** (A§11, lines 538–543): if the amendment is unsigned by 20 Dec, (a)–(d) are
   omitted and "C1's definitions need their own signed declaration"; and the attestation at signing. Both are
   reasonable, but both are new rules.
9. **Time zone of the fallback date** (A§7.2, lines 383–387): "by 3 Jan 2027" is read as the end of 3 Jan UTC, with the
   code refusing before 4 Jan UTC. The ICML dates of R1-SUBMISSION-MIN are anywhere-on-earth.

*Fix:* add these to A§12, either as new items or as sub-items of item 9, each with its options and a recommendation.
The text may keep using the recommendation.

### MINOR

**m1. The STOP case of A§2 is not specified for the intervals** (lines 105–119).
When `gate._point` raises (`gate.py:413–447`), `gate._bootstrap` cannot be called because it needs `summary`. So
step 2's bitwise check of the re-derived draws against `_bootstrap` cannot run. Step 3's check against the committed
gate output cannot run either, because that output is a STOP. The draft says the PoI and utility rows "are still
reported", but not whether their (b) intervals are then computed from the re-derived draws without the check, or
omitted. FOLD-POI A reports a point PoI only (`fold_analysis.py:143–147`).
*Fix:* say which, and if intervals are kept, how the re-derivation is validated (for example on another step-6 input
that does not STOP, or on a fixture). This belongs in A§12 (see M1.6).

**m2. The check that the record's A2 vectors equal `fit_a2`'s output has no stated place or consequence** (A§9 line
505–506; A§6.3 lines 317–321; A§8 unit 4).
"So that step 6 can check `fit_a2`'s output against them" reads as a new check inside step 6, which is the gate run.
A§0 says the §4 order is unchanged. Meanwhile (d) takes "A2's constant threshold" from the record's vectors, but unit 4
has no test that these equal the vectors `fit_a2` produced at step 6.
*Fix:*
- Put the check in units 3 or 4, after step 6.
- State that a mismatch refuses (d) (and A1's rows if it concerns A1) and never touches the gate run.
- Say whether equality is bitwise or within a tolerance. `fit_a2` fits on rows sorted by `proposal_id`
  (`gate_input_builder.py:292`), and `_wmean`'s summation order follows row order (`arms.py:79–81`), so bitwise
  equality needs the same row order in unit 1.

**m3. Unit 2's test list contradicts itself** (A§8 row 2, line 475).
It says "existing tests pass unchanged" and also that "a record without the new fields … is refused". The existing
fixture `_record()` (`r1/tests/test_c3_arms_freeze.py:432`) has no `amendments` or `rule_arms` field, so with the new
required fields, every existing test that expects a pass would fail.
*Fix:* "existing tests pass with the fixture extended by the new fields only". Alternatively, require the new fields
only when the record carries `amendments`.

**m4. The record-bias chain check** (A§7.4 (3), lines 422–437).
- (a) "A failure is an input refusal." Under §4, an input refusal is fixed and the run repeated. A real chain break in
  a logged campaign cannot be fixed by repeating the run.
  *Fix:* give such a campaign no B_c and count it, as the draft already does for a campaign with a kept duplicate.
  Since the check is label-free and the tables are readable now, run it before the test release, so the set of
  campaigns left out is fixed before any audit value is read.
- (b) The Σ Δ̂ telescoping needs Δ̂_p = metric_p − current_best_before_p (with the sign as logged) for every kept p.
  `features.py:550–557` only reads these fields; it does not establish the identity.
  *Fix:* add this label-free identity to the chain check.
- (c) The Σ Δ^aud telescoping rests on the evidence cache holding exactly one run per (node, config hash, seed), and
  on every row having complete 5 + 5 values. The draft supports the first with "table above" (the A§7.1 counts).
  *Fix:* cite `audit.py:25`, `:1052–1066` (the key set is exact and has no duplicates) and `:1006`, `:1034`. Also have
  unit 5 refuse a label or evaluation row that is not complete: `k_label` ≠ 5, or `divergent_seeds` present. Both
  sweeps' audits ran under D4 A, so no such row should exist; the code should still say so rather than assume it.

**m5. The "rows not on `main`" follow-up is incomplete, and the paragraph at lines 6–9 is stale and partly
inaccurate.**
- Lines 6–8 say the row is "not yet on `origin/author-minsub-20261122` (`53e2fe41`)". `git ls-remote origin
  author-minsub-20261122` now returns `d3f03e2c`. It is on origin, but not on `main`.
- Besides R1-POSTFREEZE-READS and the 22 Nov (d) rows, the amendment cites other rows that are also absent from `main`
  @ `89899f76` (checked by grep):
  - R1-CONTROLS-NEG-DROP (A§3.1);
  - R1-PROOF-POLICY (A§6.1);
  - R1-PROCESS-TIERS (line 3 and A§8; it sits in the 22 Nov (d) section, but the follow-up's list omits it);
  - R1-CONTROLS-ROW and R1-SCREEN-MEASURE-CHOICES (A§1).

  R1-S2-LABELS-TEST-RELEASE is also absent, but it is a future release row by design.
- The reason given at lines 8–9 ("because `arms_freeze.check_record` looks up cited rows in `main`'s PLAN") is not
  accurate today. `check_record` looks up only the `REQUIRED_DECISIONS` rows and the `fold_arms` rows, in the
  checkout's PLAN or the supplied `plan_text` (`arms_freeze.py:731–753`). It does not look up R1-POSTFREEZE-READS.
- *Fix:* update the paragraph; list every cited row that is not on `main`; and either make unit 2 check the
  `amendments` entry's PLAN row the way `REQUIRED_DECISIONS` are checked, or give the procedural reason instead.

**m6. The attestation covers C1 statistics only, while the row says "before any audit value is read"** (A§11,
lines 541–543; A§7).
Train/dev label values have already been released for both sweeps. Sweep 1's were read for Track P SFT under
R1-TRACKP-SFT-DEV; the preregistration (§6) requires those reads to be disclosed in the arms-frozen record. Both
sweeps' train/dev labels are inputs to arm training. The sweep-1 B.2
run review compared the label and evaluation rows with a recomputation (`B2_AUDIT_RUN_REVIEW_20261119.md` line 109).
The definitions can precede any C1 computation, but they cannot precede every read of an audit value.
*Fix:*
- Say so.
- Have the attestation also disclose earlier reads of audit values for other purposes.
- Note that `problem.tex` line 52 ("fixed before audit values are read") needs this qualification.

**m7. Root ledgers for the wasted-run share are not pinned, and their location is not stated** (A§7.4 (4), A§8
unit 5, A§11).
Sweep 1's root ledgers are committed (`results/r1/evidence/C3_sweep_{append_only_summary,none}_20261027T*/
provenance/ledgers/roots`). Sweep 2's are not on `main`. Unit 5 says it reads "the root ledgers named by the tables'
build provenance", but requires no sha256 check, and the A§11 lock table has no row for ledgers.
*Fix:*
- Require each ledger to match the sweep index or manifest that `build.json` pins.
- State where sweep 2's ledgers are read.
- Add a lock-table row (label-free; readable now).

Also define what happens to a table proposal whose `decision` is neither `kept` nor `discarded`, if any exists:
count it, report it and keep it out of FK and MK. Make it explicit whether it counts as invalid for WR; WR's
definition of invalid (`skipped` or no parsed metric) would not include it.

**m8. A§12 item 2 omits a consequence relevant to the choice** (lines 554–555).
openml_wdbc is outside the primary set because it failed D28 `invalid_rate` (R1-S2C3B-WDBC). That is a wasted-run
property, so excluding it from the pooled C1 row lowers the pooled wasted-run share by construction.
*Fix:* state this beside the options. This does not imply either recommendation.

**m9. A§12 item 6 omits an option and a consequence** (lines 566–568; A§3.1 lines 152–173).
- *Option:* a kept within-campaign duplicate can be given an evaluation-seed value without new runs.
  - The duplicate's configuration appears earlier in the same campaign as an audited candidate or incumbent, and
    evidence runs are unique per (node, config hash, seed).
  - So Δ_eval(C vs current incumbent) = Δ_eval(C vs I_j) + Σ_{kept between} Δ_eval.
  - This holds on bit-exact nodes, and to the extent that the active-projection identity behind `is_duplicate` implies
    identical runs.
  - It departs from `offline_eval` and needs new code. That is a reason against it, but it should be listed.
- *Consequence:* on T0, A1 − A2 consists only of duplicate terms a_p (k_p Δ̂_p − g_p), and a duplicate's logged
  Δ̂_p ≤ 0 on bit-exact nodes (`prop:app-rules` (iii)). So under the recommended proxy, and under the Δ_true = 0
  alternative, U_A1 ≤ U_A2 on every T0 instance. A1's T0 PoI against A2 is then at most 0.5 and its gap closed at most
  0. Readers of `tab:ladder` should be told this is structural, not measured.

### NIT

- **n1.** A§7.4 cites `features.py:517–570`, but the file has 569 lines (`replay_campaign` is 517–569).
  `row_worker_runs` is 313–342, not 313–341.
- **n2.** The follow-up cites "`T0_ARMS_READINESS_20261123.md` §3". The A0, A1 and A2 inventory rows are in §1
  (lines 26–29); §3 is the author decisions. The substance is correct (see "Follow-ups" below).
- **n3.** A§5.1 (line 259): "IQM* = −∞ in the gate … i.e. t* = −∞". In code, `se_iqm` is NaN on those rows
  (`gate.py:502–505`), so t* is NaN until screened. The conclusion still holds: −∞ is the natural and conservative
  value for an upper end. Reword.
- **n4.** `arms.prior_moments(c_n)`: the signature is `prior_moments(P, rows)`, with σ_node taken from the rows
  (`arms.py:187–190`).
- **n5.** A§7.2: `guard_raw_label_path` with its default `tier=None` requires both tiers' test rows
  (`release.py:403–412`, `:442–448`). C1 would pass `tier="T0"`; say so.
- **n6.** "Exactly" (A§7.3, A§7.4 (3)) holds in arithmetic. Numerically it holds up to rounding, so unit 5's identity
  and telescoping tests need a stated tolerance.
- **n7.** A§4.1 says A2 and the oracle, and A3 and A5, are reported "as utility levels". The A§4.2 table applies the
  d̄ and PoI rows to every series X ≠ A2. Say which statistics A3, A5 and the oracle get.
- **n8.** r_c is defined as the incumbent of the first table proposal. "After trial 1" is the normal case; if trial 1
  is invalid it is the first valid trial. This applies to A§12 item 3 and the manuscript follow-up as well.
- **n9.** On T0, c_n equals A2's vector mathematically. Bitwise they may differ in the last bits, because
  `RulesPrior._noninert` renormalises (`arms.py:116–120`). Storing both, as A§9 does, is the right choice.
- **n10.** A§12 item 5 gives a recommendation but no explicit alternative.
- **n11.** A§12 item 10: adding the Ladder margin rule would also put its η in the arms-frozen record (R1-D3-MIN:
  "an arm reads test only if it is in the arms-frozen record").
- **n12.** The D.3 draft's G2 spec filters to "the P3 dev instances of the seven nodes" (D.3 draft §5.0). Unit 1 fits
  all eight T0 nodes and the G.5 T1 nodes. If one unit is to serve both, the D.3 text needs aligning.
- **n13.** For the manuscript, not the amendment: `results.tex` line 142 says the campaign-level reading needs (NF)
  and (NI). T4 Corollary 7a and A§6.1 say (NF).
- **n14.** Unit 2 / A§3.2: refusing a record whose vectors differ from a pinned D.3 constants file makes D.3
  consistency a precondition of the record, and so of the gate read. State that this is an input refusal, fixable
  before any test read, consistent with D.3 draft §10.
- **n15.** Unit 3's bitwise test should include an IQM-ineligible node ordered before an eligible one. Every node,
  eligible or not, consumes generator state in `_bootstrap` (`gate.py:475–477`).

## Check 1: faithfulness to R1-POSTFREEZE-READS

| Row item | Draft | Assessment |
|---|---|---|
| (a) A0, A1 per-node test rows, frozen in the record | A§3, A§9 | Faithful. A0 = `offline_eval.rho`. A1 = `ConstantPrior` + `decisions(rule_layer=False)`, fitted on `fit_a2`'s dev rows (PRE-A2 C). The record carries A0's rule id and A1/A2 vectors. "No verify offline" is a necessary consequence of the one-step evaluation and is stated. Inputs used beyond the row: M1.3. |
| (b) two-sided 95 % intervals, gate's instance-cluster bootstrap | A§2, A§4 | Faithful in mechanism: same generator, seed, order and per-node draws, applied to every series. The choice of construction per statistic and the omissions are author choices: M1.4–5. |
| (c) one-sided upper bounds of A3/A5's IQM from the gate's resamples | A§5 | Correct construction (see check 2). Level and input are choices: M1.1–2. The −1e12 sentinel is listed (item 7). |
| (d) T4 Prop. 7 dispersion estimate; frozen A3/A5 against A2's constant threshold; primary input's test proposals; after the test release; no label | A§6 | Faithful. The formula equals `rules.gap_bounds`' upper element (`rules.py:81–91`) and `offline_eval`'s `prop7_upper_mean` (`:460–476`), on the gate's population. The denominator is listed (item 8). The missing interval and the pooled form are choices: M1.5. |
| C1: definitions, seeds, instances, timing, fallback | A§7 | Faithful to the row's seeds (7001–7010; partial 7001–7005), instances (all audited T0 instances; partial = train + dev), timing (after the T0 test release row) and fallback date. The additions are partly listed (items 1–5, 9(ii)) and partly not: M1.7–9. |
| "power follows PRE-POWER A; closed-loop constants follow the signed D.3 note" | A§0 | Quoted unchanged. |

## Check 2: correctness against the code

**Citations.** I checked every file, function and line range in A§1–A§9 against `main` @ `89899f76`. All are correct
except n1 (two end lines). The sha256s of the preregistration, `gate.py`, `gate_input_builder.py`, the noise summary
and both committed receipts match. So do the report and review line numbers cited for counts:
- `B2_AUDIT_RUN_REVIEW_20261119.md` lines 83, 89–90, 93, 109, 120;
- `S2_B2_AUDIT_REPORT_20261122.md` lines 17, 29, 30, 33;
- `SWEEP1_TRAINDEV_RELEASE_20261123.md` lines 25–30, 42;
- `S2_TRAINDEV_RELEASE_20261122.md` line 37;
- `DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` line 46.

**Claimed behaviours.**

*offline_eval and arms*
- `offline_eval.rho` executes all proposals and keeps iff Δ̂ > 0 (`:287–291`).
- A1 uses `rule_layer=False` (`:412`).
- The kept-duplicate proxy is the logged Δ̂ when the duplicate is not audited (`:198–209`), counted in `:416–417`.
- `ConstantPrior` averages every labelled row (no-ops included). `RulesPrior` drops rule-skipped rows and zeroes and
  renormalises bin 0 (`arms.py:84–120`).
- `labels.soft_label` puts no mass on bin 0 for a non-no-op (`labels.py:56`, `p[1:]` only).
- So on T0, with 0 no-ops (both sweeps), A1's vector equals A2's and A1 differs from A2 only on duplicates. Correct.

*Builder and audit*
- No duplicate is audited (`audit.py:1026–1028`), and the builder refuses label or evaluation rows on a duplicate
  (`gate_input_builder.py:271–274`).
- `fit_a2` takes dev rows with a soft label (`:296–304`): no-ops (inert) and audit labels. Duplicates and divergent
  labels have none.

*Gate*
- `gate._bootstrap` creates `Generator(PCG64(20261108))` and draws one `integers(0, n, size=(2000, n))` per node. It
  iterates over all nodes, eligible or not, in sorted node order and sorted instance-id order (`_validate` sorts both,
  `gate.py:274–275`, `:336`). The same draw serves A2, the oracle, A3, A5 and the PoI.
- Re-deriving those arrays and applying the gate's own `_node_se`, `_iqm_weights` and stable argsort reproduces t*,
  the screened set (t* = `TSTAR_INF`) and the PoI resamples bitwise under the pinned NumPy (`_require_pins`).
- `_bootstrap` does not return the screened mask, but it is recoverable as `tstar == TSTAR_INF`, and the draft
  re-derives it.
- The constants (`gate.py:136–143`) are as stated.

*Upper bound*
- UB_L = θ̂ − Q_{1−L}(t*⁻)·ŝe is the upper end of the bootstrap-t construction whose lower end is the gate's
  θ̂ − Q_L(t*)·ŝe (`gate.py:523–527`).
- Putting screened resamples at −1e12 can only lower Q_{1−L} and so raise UB. It is therefore conservative, and the
  gate's +1e12 array would be anti-conservative for an upper end. This holds for both kinds of screening (a
  nonpositive denominator, or se* = 0 / non-finite).
- The "no finite upper bound" rule is right. With the linear quantile over 2,000 resamples (index 1999·q), the
  sentinel enters Q_{0.025} exactly when m ≥ 50, and Q_{0.05} exactly when m ≥ 100; the same thresholds hold for the
  upper quantiles of the gate's lower end. I confirmed this numerically on synthetic data (NumPy 2.5.3; the `linear`
  method is unchanged from 2.4.4).
- The Bonferroni claim of A§5.2 (two one-sided 97.5 % bounds give ≥ 95 % joint coverage) is correct.

*Release, fold analysis and record*
- `rules.gap_bounds` (`rules.py:81–91`) is the bound of `prop:app-gap` (`appendix.tex` 247–254), term by term.
- `audit.paired` (`audit.py:391–398`) and `split_audit` (`:413–418`) with complete 5 + 5 rows (`:1006`, `:1034–1035`)
  give Δ^aud = (Δ_label + Δ_eval)/2 (see n6).
- `release.open_partition` (`:602–647`) re-checks the receipt, its row and P3 membership. `builder_source`
  (`:657–675`) opens the test partition, so it needs the test row. Sweep 1 has test partitions under the T0 row
  (`release.py:75–79`, `release()` accepts `sweep1`/`test`).
- `fold_statistics` (`fold_analysis.py:120–161`) calls the gate's private functions in the way the draft describes.
- `arms_freeze.REQUIRED_TOP` and `ARM_FIELDS` are at `:542–550`; `required_arms` (`:610–619`) does not include A0, A1
  or A2.

## Check 3: the four C1 rates against the manuscript

`problem.tex` (a93c1cea) lines 44–52 and `results.tex` lines 33–82 define the four rates in words.

| Rate | Draft (A§7.4) | Match |
|---|---|---|
| FK | #{kept, Δ^aud ≤ 0} / #{kept} over audited proposals | "kept candidates whose audited increment is not positive"; `results.tex` 72 says "a share of keeps". Matches. The denominator is a choice (M1.7). |
| MK | #{discarded, Δ^aud > 0} / #{discarded} | "discarded candidates whose audited increment is positive". Matches; the denominator is the analogous choice. |
| RB | mean over campaigns of Σ_{kept}(Δ̂ − Δ^aud)/σ_node | "the recorded gain of the incumbent minus its audited gain", in σ_node units (`tab:c1` caption). Matches, with the reference made explicit. |
| WR | Σ worker runs on no-op, duplicate and invalid rows / Σ worker runs, from root ledgers via `row_worker_runs` | "runs spent on no-ops, duplicates and invalid proposals". Matches (m7). |

**Telescoping.** The record-bias telescoping is correct, given:
- the chain check, extended by the Δ̂ identity (m4 b);
- one run per (node, config hash, seed) in the evidence cache (`audit.py:25`, `:1052–1066`);
- complete 5 + 5 rows (`:1006`, `:1034`).

Under these, Σ_{K_c} Δ̂_p = recorded(final) − recorded(r_c), and Σ_{K_c} Δ^aud_p is the ten-seed paired mean of
m(final) − m(r_c), because consecutive kept pairs share the middle configuration's runs per seed.

**"From the configuration after trial 1".** This is right. Trial 1 is a manager edit with its own patch, kept without
comparison:
- `c3_env_replay.py:281–284`;
- Track S runbook line 90 (B5);
- `duplicate_report.py:7–8` ("trial 1 … not proposals of the table").

So the start configuration is never audited, and RB can only be measured from r_c (n8 covers the edge case where
trial 1 is invalid).

## Check 4: locks

**Nothing in the amendment can be satisfied by an earlier read**, with two exceptions that the row itself creates or
allows, and that the draft handles:

1. **The partial C1.** Its data (train/dev label blocks) are readable now. It is guarded only by the C1 code's date
   check, and the attestation covers deliberate reads (m6).
2. **(d).** It is label-free, so an earlier computation is not a §6 STOP. It is declared after the test release and
   disclosed as a deviation if computed earlier. This is consistent with the row.

The other items need the test partitions, which open only with a receipt bound to the test release row (§4 step 5;
PRE-STAGE A; `open_partition`, `builder_source`).

**The sweep-1 raw blocks on `main`.** I did not open any file in `docs/r1/reports/b2_audit_20261119/`; I listed only
its file names with `git ls-tree`.
- The directory holds files named `label_block.jsonl` and `evaluation_block.jsonl` (in `release.RAW_NAMES`) and the
  evidence markers `evidence_completion.json` and `evidence_binding.json`. So `guard_raw_label_path` refuses any path
  in it before the test rows (`release.py:80–81`, `:415–448`).
- After the T0 row, that guard no longer refuses. A§7.2 therefore requires the C1 code to open only receipted
  partitions, and unit 5's tests include refusing "any raw block or evidence-directory path". That is sufficient if
  implemented as written.
- No part of the amendment uses those blocks: counts come from the reviews and reports listed above.
- Units 1, 3 and 4 take labels only through `traindev_labels`, `builder_source` or the committed step-6 inputs.

## Check 5: no change to verdict, gate, arm selection or preregistered statistic

**Confirmed.**
- The branch changes no code; `git diff 89899f76 a97ec3fa` touches only the draft.
- The gate and builder bytes and their sha256s are unchanged.
- The step-6 runs are recomputed only to check equality.
- The secondary arms' series come from additional `build` calls with other predictions. These do not alter the
  committed inputs, and `build` computes no statistic.
- `arms` in the record is unchanged. No arm is fitted, selected or calibrated on anything the amendment computes.

**Effects on preconditions (not on statistics).** Unit 2 adds refusal conditions to the arms-frozen record (n14), and
m2 asks that the record-vs-`fit_a2` check be placed outside step 6.

## Check 6: the drafter's follow-ups

| Follow-up | Correctly stated? |
|---|---|
| Rows not on `main` (signing needs them there) | Correct for the rows it names, but incomplete, and the lines 6–9 paragraph is stale and its reason inaccurate (m5). |
| `T0_ARMS_READINESS` says A0 "not in this read", A1 and A2 "nothing to freeze", while the amendment needs their vectors in the record; no step in `arms_freeze.py` or the T0 arms runbook | Correct in substance: the report's lines 26–29 say this, and grep finds no A0, A1, A2 or `rule_arms` handling in `arms_freeze.py` or `DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md`. The section is §1, not §3 (n2). |
| `results.tex` "is descriptive and is not part of the preregistration" must change; the TBDs answered | Correct (`results.tex` line 142; the `tab:ladder` caption TBD at line 90; "Effect sizes" line 139; `problem.tex` 52; `results.tex` 36). The `tab:c1` caption TBD (line 39) is also answered by A§7.4 and item 2. `tab:ladder`'s "final list of secondary rows" is settled by ARMS-SECONDARY A, not by the amendment. |
| Record bias is relative to the configuration after trial 1; the manuscript should say "over the first incumbent" | Correct (check 3; n8 for the edge case). |
| Wasted-run share needs root ledgers (invalid rows are not table rows) | Correct: `replay_campaign` drops `skipped`/metric-less rows (`features.py:540–542`). It should add the pinning and location point of m7. |

## Check 7: the 11 open items (A§12)

| # | Presented correctly? | Complete? |
|---|---|---|
| 1 Headline reading | Yes | Mostly; the FK and MK denominators are a related unlisted choice (M1.7). |
| 2 Pooled node set | Yes | No: the wdbc / wasted-run consequence is missing (m8). |
| 3 Record bias | Yes | Yes (the per-keep mean is the secondary; n8). |
| 4 WR in the partial version | Yes | Yes. |
| 5 Row after 3 Jan | Yes | No explicit alternative (n10). |
| 6 Kept duplicates | Yes | No: the evaluation-seed telescoping option and the structural sign of A1 − A2 on T0 are missing (m9). |
| 7 Sentinel at upper ends | Yes; the alternative is correctly called not conservative (check 2) | Yes. |
| 8 Dispersion denominator | Yes | Yes. |
| 9 Additions beyond the row | Yes for the two listed | No: M1. |
| 10 Ladder margin rule | Yes | Should note η would enter the record (n11). |
| 11 When the code is bound | Yes | The fallback (a CONFIRM-type row before the test release) cannot serve units 1 and 2: the record must already carry the A1/A2 vectors and the new fields when it is committed. If those units are not bound by then, A1's rows and the record-based input of (d) are lost. Say so. |

## What I verified and how

- I read the draft, the preregistration, the PLAN rows named in the task (`d3f03e2c` and `main`), the code modules
  cited, the manuscript sections cited, the T4 §3 status and reading, D.3 draft §5.0–5.3, §10 and §12, positive
  control §1, the arms readiness report and the T0 arms runbook.
- I recomputed sha256s with `sha256sum` and checked branch heads with `git ls-remote`.
- I checked PLAN row presence with grep on both PLAN versions.
- I checked the quantile thresholds with a short NumPy script on synthetic data.

## What I could not verify

- **Table fields in the sealed sweep-1 table.** Whether every sweep-1 table row carries `incumbent_hash`,
  `candidate_hash`, `metric` and `current_best_before` in the v2 builder's output. `dataset.row_of` on `main` writes
  them, but I did not open the sealed table.
- **Decision values.** Whether any table proposal has a decision other than `kept` or `discarded` (m7). This needs the
  tables or ledgers, which I did not read.
- **Sweep-2 ledgers.** Where sweep 2's root ledgers are kept and how they are pinned (not on `main`).
- **Bitwise reproducibility.** Bitwise reproduction under NumPy 2.4.4, which I did not run. I reasoned it from the
  code.
- **Actual reads.** Whether any C1-like statistic or audit value has already been computed or read beyond what the
  committed reports and reviews show (m6).
