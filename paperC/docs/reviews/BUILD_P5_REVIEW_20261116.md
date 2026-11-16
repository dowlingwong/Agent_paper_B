# Build review — P5: decision-relevance check (round 1)

- **Reviewer:** independent reviewer (Claude subagent, AI-assisted). I had not seen this work before the review.
- **Commit:** `0c77ffc` on branch `paperc-build-20261115`. Diff read against `9fbd555`.
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

## Scope read

- Runbook P5 (`paperC/docs/BUILD_RUNBOOK.md`), and PH for how the census was to use P5's functions.
- Context:
  - plan addendum §B (`PLAN_ADDENDUM_20261115.md`): STOP 4 facts and §B.3, the decision-relevance check;
  - BUILD_LIST B10;
  - plan §6 (SPT-0 … SPT-3, the SPT-1 forks) and §7.0 (one common C3 belief);
  - census §3.1 (`HEADROOM_CENSUS_20261116.md`): the Track S E1/E2 numbers.
- Code:
  - `paperc/relevance.py` and `paperc/relevance_demo.py`;
  - context in `paperc/schema.py` (eligible / rule_forced / forced, fork rows, invalid candidates), `esyn/sim.py` (how rows, forecasts and `sigma_node` are written), `esyn/policies.py` (`Static` = N1) and `paperc/census.py` (`census_tracks`, the Track S margin definitions).
- Tests: `tests/test_relevance_p5.py`; for context, `tests/test_schema.py` (`valid_campaign`, `test_r2_failed_invalid_is_an_outcome_and_must_be_discarded`).
- Report and status: `docs/reports/RELEVANCE_ESYN_20261116.md`, and the P5 row of `BUILD_STATUS.md`.

## What I ran

Scratch work is in `/tmp/p5rev/`: `vscale.py`, `probe1.py`, `probe2.py` and `mkrows.py`, plus CLI probes run inline.

1. **Full suite:** 179 passed in 78 s. **P5 tests:** 4 passed in 3 s.
2. **Demo:** `python -m paperc.relevance_demo` ran in 24 s. `git status` was clean afterwards, so the committed report reproduces byte for byte.
3. **Scale and E2 checks on the demo's records** (`vscale.py`, the same N1 records as the demo, 50 campaigns per world):
   - V\*/σ_node quantiles per world;
   - policy-skip counts;
   - E2 shares against h = 0, against N1's own h, and against the raw-keep margin Δ̂ (findings 5 and 10).
4. **Edge cases of `relevance()`** (`probe1.py`):
   - NaN `v_star` or `sigma_node`;
   - a node with E1 rows only;
   - fork and forced rows;
   - an eligible E2 discard of an invalid candidate;
   - missing or mistyped fields;
   - a price mapping that lacks a node;
   - empty input;
   - policy skips;
   - zero, negative and empty bands;
   - rows with only another belief.
5. **Schema-valid campaign** (inline): `test_schema.valid_campaign()` with its invalid-candidate variant (finding 3).
6. **Mutation of the STOP 4 test** (`probe2.py`):
   - E1 rows moved inside the band;
   - a STOP 4 fixture with Track S-like E2 rows added;
   - an eval_allocation campaign with verify, reaudit and final rows;
   - `Transition` input against dict input;
   - a band edge (|z| = b exactly; inclusive, works).
7. **CLI probes** (inline, on 3 budget-world campaigns):
   - `--g` together with `--g-json`;
   - a row subset, with validation on;
   - the same file twice, with and without validation;
   - malformed `--bands`;
   - a missing output directory;
   - a bad JSON line;
   - an empty file;
   - no price;
   - `--help`.

## What is right

- **Per-row computation.** The core arithmetic is correct:
  - (V\* − g)/σ_node on eligible E1 rows;
  - (m̂ − h)/σ_node on eligible E2 rows;
  - inclusive band counts;
  - signed quantiles.
- **The known-share test** checks real counts.
- **Rule-forced rows** are excluded, including the first trial's E2 keep.
- **Verify, reaudit and final rows** are ignored. A missing forecast, `sigma_node`, `v_star`, `m_hat` or price raises a named error.
- **Price precedence** is implemented as documented (argument, then the forecast's `g`, then `env.constants["g"]`).
- **Varying prices** within a node are reported as `varies`.
- **Rule-skip share definition.** It matches the census's definition (skips over all E1 rows).
- **Input forms:** `Transition` input gives the same result as dict input.
- **CLI validation** runs by default and refuses invalid input.
- **Faithful STOP 4 data.** With the E1 situation of STOP 4 and E2 rows like Track S's, the module gives the right per-epoch result: "E1: no decision-relevant states" and E2 relevant (`probe2.py`). The logic is sound when the data are complete. The problems are in the cases it does not handle, in the empty-epoch label, and in the tests.

## Findings

### 1. MAJOR — fork rows are counted unweighted and duplicate root states

**Location:** `relevance.py:121–151`. `identity.branch_path`, `action.forced` and `fork.p_select` are never read.

**Why it matters:**
- `relevance()` claims to work on "any set of P1 records", but it counts every non-rule-forced row of every trajectory.
- A fork's first row is the parent's decision point at the same step. `check_campaign` requires the same counters and incumbent, so the row repeats a root state, once per arm and replicate. Later continuation rows are states reached through a forced action.
- Fork points are selected with a near-threshold oversample (`ForkDesign.oversample`, `p_select`; plan §6 SPT-3). Counting fork rows unweighted therefore inflates exactly the share P5 measures.
- `probe1.py` shows the effect: 2 root rows give a share of 0.50 within 0.25 σ; adding 4 forced fork-arm rows at the same root state gives 0.83. `n_e1_rows`, the rule-skip denominator, also counts them.
- The check is meant to run before SPT-2 (addendum §B.3). The natural input is SPT-1, which contains forks (plan §12: "60 forks × 2 arms × 20"), or Track S roots and leaves via B5. Either way the result would be biased, with no warning.

**Fix:**
- By default, use only root trajectories (`branch_path == []`).
- Report the number of fork rows and forced rows that were excluded.
- Optionally include continuation rows, dropping each fork's first (duplicated) row and weighting by 1/`p_select` (the P6 design weights).
- Declare whether forced rows on root trajectories (interventions) count. Counting them is defensible, since the state is real.
- Add a test with fork rows and with root interventions.

### 2. MAJOR — an epoch with no eligible rows is labelled "no decision-relevant states"; the STOP 4 fixture omits E2, so its report says the opposite of the real STOP 4 situation; the markdown assertion is vacuous

**Location:** `relevance.py:105` (`relevant = bool(len(z)) and …`) and `verdict()` (lines 81–89); docstring lines 16–17; `test_relevance_p5.py:38–53`.

**Why it matters:**

*Gate semantics.* Addendum §B.3 uses "no decision-relevant states" as a gate outcome: round A on that node "is reported as 'no decision-relevant states' and not run", and E2 "get[s] the same check". An epoch with **zero eligible rows was not assessed**. Causes include a behaviour policy that skips everything at E1, an export with no E2 rows, or a filtered record set. Absence of data is not evidence that states are far from the threshold. With the current label, a channel can be dropped by the gate on no data.

*The fixture.* In Track S, E2 **was** decision-relevant. Census §3.1 has 15.4 % (digits) and 11.5 % (tabular) of E2 margins within ±0.5 σ_node, and there were 371 and 401 E2 rows. The fixture has no E2 rows at all. Its generated report therefore reads "E2: no decision-relevant states (0 of 0 …)" for both nodes, which is the opposite of the STOP 4 situation. The runbook asks for the STOP 4 situation to be reproduced, and the verdict is per epoch, so the fixture should show "E1: none; E2: relevant". With E2 rows added, the module does this correctly (`probe2.py`: digits E2 15 % within 0.5 σ, tabular 8.7 %).

*The markdown assertion.* `md.count("no decision-relevant states") >= 2` is satisfied by the two empty-E2 lines alone. Moving every E1 row inside the band still leaves the count at 2 (`probe2.py`), so the assertion tests nothing. The `s.verdict()[0]` assertions do test E1.

**Fix:**
- Give empty epochs their own status, e.g. `relevant = None` and "E2: not assessed (no eligible rows)", distinct from "no decision-relevant states".
- Add E2 rows to the STOP 4 fixture with a Track S-like margin distribution, and failed-invalid discards if finding 3's rule is adopted.
- Assert "E1: no decision-relevant states" and "E2: relevant" per node in both the summary and the markdown.
- Count only the E1 verdict lines in the markdown assertion.

### 3. MAJOR — schema-valid E2 rows of invalid or divergent candidates either crash the module or are counted as decisions

**Location:** `relevance.py:128–151`. `state.candidate_invalid` and `state.candidate_divergent` are not read.

**Why it matters:**
- The P1 schema requires that an invalid or divergent candidate is discarded. It does **not** require that discard row to be rule-forced. `test_schema.test_r2_failed_invalid_is_an_outcome_and_must_be_discarded` accepts an eligible `rule="policy"` discard of an invalid candidate, with `m_hat = None`.
- On that schema-valid campaign, `relevance(rows, validate=True)` raises "an eligible E2 row has no m_hat" (checked inline). The module therefore fails on records that P1 accepts.
- If a loader instead fills `m_hat` (e.g. with the prior mean), the forced discard is silently counted as an E2 decision near the threshold (`probe1.py`: counted, `relevant = True`).
- On real data this matters: in Track S, 53 of 371 (digits) and 51 of 401 (tabular) E2 rows are failed_invalid (census §3.1). The census excluded them, by `margin is None`.

**Fix:**
- Treat an E2 row with `candidate_invalid` or `candidate_divergent` as not eligible for the margin, whatever its rule label, because the discard is forced by plan §3.1.
- Report the number of such rows per node.
- Add a test on `test_schema.valid_campaign()` with its invalid-candidate variant.

### 4. MINOR — policy skips are not reported, so "all E1 skips were rule duplicates" cannot be read from the output

**Location:** `relevance.py:128–131`, `NodeSummary`, and the markdown rule-skip column.

**Why it matters:**
- The STOP 4 situation has two parts: no state near the threshold, and **all skips rule duplicates**. The module counts only rule-forced skips over all E1 rows. Eligible E1 rows that the policy skipped appear nowhere.
- In the demo, the budget world shows a "rule-skip share" of 54.6 %. Its N1 also skipped 695 of 857 eligible rows (`vscale.py`), and the reader cannot see that.
- The column header does not state the denominator.
- The STOP 4 test does not assert that there are no policy skips.

**Fix:**
- Report E1 skips split into rule skips by rule, policy skips and forced skips.
- Report the rule share of skips alongside the rule-skip share of E1 rows, and label the denominators.
- Assert zero policy skips in the STOP 4 test.

### 5. MINOR — E2 margin: h is a single scalar, never tested away from 0; the demo measures E1 against N1's g but E2 against 0; Δ̂ is not offered

**Location:** `relevance.py` (`h: float`, `--h`); `relevance_demo.py:27–31`; `test_relevance_p5.py` (no test with h ≠ 0).

**Why it matters:**
- **Reading of the runbook.** h = 0 by default is a correct literal reading of "|m̂| (keep margin)". It matches Track S S0.5 (kept iff m̂ > 0) and the census.
- **The demo is inconsistent.** It takes N1's own g as the E1 price ("E1 shares measure how many proposals sit near N1's cut"), but N1's own h is non-zero in every world, from −0.70 σ in keep_feedback to +0.15 σ in information. In keep_feedback, 11.4 % of E2 rows lie within 0.25 σ of N1's h, against the reported 33.2 % within 0.25 σ of 0 (`vscale.py`). The report discloses "h = 0" but not that N1's cut differs.
- **Only one h.** g can be given per node, but h cannot.
- **Δ̂ is missing.** The rule logged in Paper B and in Track S S0.4 keeps on Δ̂, not m̂. The shares differ by a factor of about 2.5 (strict_null within 0.5 σ: 0.31 on Δ̂ against 0.76 on m̂). A reader of a report on such records should know which margin was used.

**Fix:**
- Accept h as a scalar or a node mapping, like g, with a `--h-json` option.
- In the demo, use N1's (g, h) for both epochs, or the declared economic thresholds (declared g, h = 0) for both, and say which.
- Optionally report the Δ̂ margin (`state.candidate_delta_hat`) as a secondary row.
- Add a test with h ≠ 0.

### 6. MINOR — silent NaN handling; the API defaults to `validate=False`

**Location:** `relevance.py:110` (default), lines 136 and 147–151, and `--json`.

**Why it matters:**
- A NaN `sigma_node` passes `not sig or sig <= 0`.
- A NaN `v_star` or `m_hat` gives z = NaN. That row counts as eligible but never within a band, and the quantiles become NaN.
- A node whose `sigma_node` is NaN is reported as "no decision-relevant states" (`probe1.py`). This is a silent wrong answer, and it points toward "do not run".
- The CLI validates by default, and the schema rejects non-finite values, but the API default is `validate=False`. That is the path the census or a B5 caller would take.
- `json.dumps` then writes `NaN`, which is not valid JSON.

**Fix:**
- Require `math.isfinite` on V\*, m̂, σ_node and the price, and raise `RelevanceInputError` otherwise.
- Use `json.dumps(..., allow_nan=False)`.
- Consider `validate=True` as the API default, so that API and CLI agree.

### 7. MINOR — raw `KeyError` and `TypeError` on malformed rows when `validate=False`

**Location:** `relevance.py:119–131`.

**Why it matters:** a missing `state.rule_forced`, a missing `action.rule` on a rule skip, or a string `sigma_node` surfaces as `KeyError` or `TypeError`, with no row identity (`probe1.py`).

**Fix:** wrap field access, and raise `RelevanceInputError` naming the campaign and the step.

### 8. MINOR — silent price sources

**Location:** `relevance.py:122`, CLI line 205.

**Why it matters:**
- A `--g-json` mapping that lacks a node, e.g. because of a typo, silently falls back to the forecast's g (`probe1.py`).
- Given both `--g` and `--g-json`, the CLI silently uses the mapping (checked).
- The report does not say which source supplied each node's price.

**Fix:**
- Make `--g` and `--g-json` mutually exclusive.
- Raise an error, or at least warn, when a mapping misses a node that has eligible E1 rows, or names an unknown node.
- Record the price source per node in the summary and the report.

### 9. MINOR — the verdict criterion is not stated in the report, and the JSON field `relevant` overstates it

**Location:** `markdown()` header; `EpochSummary.relevant` and `to_dict`.

**Why it matters:**
- The criterion is "at least one eligible row within the widest declared band". It is in the docstring but not in the report.
- It depends on `--bands`: with a band of 5, STOP 4 would read as relevant.
- `"relevant": true` is set by one row in a thousand.
- The verdict label is the same wording as the addendum's gate outcome. A reader may take `relevant: true` as passing the gate, which P5 does not set.

**Fix:**
- State the criterion and the bands in the report header, with one sentence that it is not the SPT-2 gate.
- Rename the field, e.g. `any_within_widest_band`, or add the gate placeholder explicitly.

### 10. MINOR — demo report wording on the V\* scale

**Location:** `relevance_demo.py:34–37` and the report's closing paragraph.

**Why it matters:**
- "V\* … about 0.05–0.4 sigma" fits the 5–95 % range of five worlds (0.04–0.43 σ).
- It does not fit information (95 % at 3.6 σ, maximum 19.4 σ) or interaction (95 % at 0.98 σ, maximum 3.7 σ) (`vscale.py`). The report's own table shows information at only 74.5 % within 1 σ.
- In the four worlds where g = 0, N1 never skips, because V\* = E[max(m̂, 0)] ≥ 0 (0 policy skips). "Near N1's cut" therefore cannot change N1's action there.

**Fix:**
- Qualify the range (5–95 %, five of seven worlds; name the two exceptions).
- Add one sentence on the g = 0 worlds.

### 11. MINOR — grouping only by node; no campaign counts or uncertainty

**Location:** `relevance.py:117–121`.

**Why it matters:**
- Campaigns, policies, W and suites are pooled per node, and the report does not list them. Duplicated campaigns would double n silently; Track S's S0.5 static rep-0 roots repeat the a2u roots (census §2).
- Shares are reported without an interval, and rows within a campaign are correlated. When the author sets the gating share, the report will need n campaigns and a cluster-aware interval.

**Fix:**
- List per node the number of campaigns, the policies, W and the tiers.
- Optionally offer `--by node,policy`.
- Add a campaign-cluster bootstrap or similar interval for each share. This is not needed for ACCEPT, but cheap now.

### 12. MINOR — report provenance and empty input

**Location:** `main()`, `markdown()`.

**Why it matters:**
- The report does not record its input files, their sha256, row counts or whether validation ran. The census does record its inputs.
- An empty input produces a header-only report and exits 0 (checked).

**Fix:**
- Add an inputs section: paths, sha256, rows read and the validation flag.
- On empty input, raise an error or write an explicit "no rows" line.

### 13. MINOR — CLI error handling

**Location:** `main()`.

**Why it matters:**
- These cases end in Python tracebacks:
  - `--bands "0.5,,1"` (ValueError);
  - empty bands (`max()` of an empty sequence);
  - a missing output directory;
  - a bad JSON line, reported with no file or line number.
- Negative bands are accepted.

**Fix:**
- Require bands to be non-empty and > 0.
- Report `file:line` on JSON errors.
- Print concise messages and exit with status 2.

### 14. MINOR — the tests are weak or missing in places

**Location:** `test_relevance_p5.py`.

**Weak tests:**
- `test_on_esyn_records_and_cli` asserts only `n_eligible > 0`, `0 ≤ share ≤ 1`, the node name in the markdown, and `n_eligible > 0` in the JSON. The JSON content is never compared with the API summary.
- The STOP 4 markdown assertion is vacuous (finding 2).

**Missing tests:**
- fork and forced rows (finding 1);
- invalid and divergent E2 rows (finding 3);
- exclusion of verify, reaudit and final rows (eval_allocation has them);
- h ≠ 0;
- a price mapping over several nodes;
- precedence when argument, forecast g and env g all exist and differ;
- NaN;
- `Transition` input (it works, but is untested);
- `markdown()` called with bands different from the summary's, which raises `KeyError` because `markdown()` defaults to `BANDS` instead of reading the bands from the summary.

**Fix:** add these cases. Have `markdown()` derive the bands from the summary.

### 15. MINOR — readiness for real records (B5 / SPT)

**Location:** the module docstring and the defaults.

**Why it matters:**
- **Fields.** The fields read exist in P1 rows: `identity.node` and `epoch`, `state.rule_forced`, `sigma_node` and `forecasts[belief].{v_star, m_hat, g}`, `action.action` and `rule`, and `env.constants.g`.
- **Default belief.** It is `a2u`. Paper C's common belief is the frozen C3 model (plan §7.0), and A2-U is a reference row only. A Paper C run with the default fails, loudly, on the missing belief.
- **No m̂ in Paper B records.** Paper B archives carry no m̂ unless B5 computes the belief post hoc. With findings 3 and 5, this means that on real records the E2 part depends on B5 choices that P5 does not document.
- **One price per run.** The STOP 4 facts were checked against both the run price and the static threshold. The module takes one price per run.

**Fix:**
- Require `--belief`, or default to the declared common belief.
- Document in the docstring what P5 expects from B5 for E2 rows: an m̂ for every eligible E2 row, and invalid discards flagged.
- Optionally accept several named thresholds per node (price, policy threshold).

## Summary

The arithmetic, the price precedence and the rule-forced exclusion are correct, and the demo reproduces. Three cases are not handled correctly:

- **Fork rows** are counted unweighted, which inflates shares on SPT-1 and Track S records, the inputs the gate is meant for.
- **Epochs without eligible rows** are given the gate's "no decision-relevant states" label. The STOP 4 fixture leaves out the E2 channel that Track S showed to be decision-relevant, and the test's markdown assertion is vacuous.
- **Schema-valid invalid-candidate E2 rows** make the module crash, or are counted as decisions.

Each has a small, concrete fix and a test to add. The minor findings mostly concern reporting: policy skips, the E2 threshold, price sources, provenance, NaN handling and the CLI.

Verdict: NOT ACCEPTED

---

## Round 2

- **Reviewer:** the same independent reviewer as round 1.
- **Commit:** `440cb20` on branch `paperc-build-20261115`. Diff read against `0c77ffc`.
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

### Scope read

- the response table, `BUILD_P5_RESPONSE_R1_20261116.md`;
- the rewritten `paperc/relevance.py` (all of it);
- `paperc/relevance_demo.py`;
- `tests/test_relevance_p5.py` (9 tests);
- the regenerated `docs/reports/RELEVANCE_ESYN_20261116.md`;
- the P5 row of `BUILD_STATUS.md`.

### What I ran

Scratch work is in `/tmp/p5rev/`: round 1's scripts, plus `probe3.py`, `probe4.py`, `probe5.py` and `probe5b.py`, and CLI probes run inline.

1. **Tests:** the full suite gave 184 passed in 80 s; the P5 tests gave 9 passed in 6 s.
2. **Demo:** `python -m paperc.relevance_demo` left `git status` clean, so the committed report reproduces byte for byte. I checked the note against the table:
   - the 95th percentiles of five worlds are ≤ 0.44;
   - information: 95th percentile 3.41, maximum 19.12, strength-16 follow-ups (`extra.py:139`);
   - interaction: maximum 3.71;
   - one policy skip in interaction.

   These numbers agree with round 1's `vscale.py`, e.g. keep_feedback E2 within 0.25 σ of N1's h is 11.4 %.
3. **Schema-valid inputs, with validation on** (`probe5.py`, `probe5b.py`):
   - the P1 invalid-candidate campaign is accepted, with 1 invalid discard counted and excluded;
   - `valid_campaign() + fork_continuation()`:
     - in root mode, 2 fork rows are excluded;
     - in weighted mode, the forced fork arm is excluded, and the continuation's execute row gets weight 1/0.6.
4. **Weighted forks and quantiles** (`probe3.py`):
   - the test's weighted share, (2+2+4)/(4+2+4), is reproduced;
   - a depth-2 fork;
   - p_select ∈ {0, −0.5, 2} with validation off;
   - counts in weighted mode;
   - `_wquantile` against `np.quantile(method="inverted_cdf")` on an integer-weight expansion: all 7 quantiles agree exactly;
   - one campaign only.
5. **Clustered interval** (`probe4.py`):
   - Monte Carlo coverage of the 95 % interval for a ratio share with campaign random effects, unequal rows per campaign, and optional 1/p weights, 2,000 replications per cell;
   - campaign_id against instance_id clustering, with 3 policies × 30 shared instances in the budget world.
6. **h, thresholds and the CLI** (`probe3.py`, inline):
   - NaN h through the API, `--h nan` and `--h-json`;
   - an h mapping that misses a node;
   - an extra-threshold mapping that misses a node;
   - `--threshold g=…` given together with `--g`;
   - a bad `--g-json`;
   - binary input;
   - `--out` naming a directory;
   - a missing input file;
   - a row subset;
   - an empty `--bands` element;
   - belief auto-detection;
   - how a not-assessed epoch is rendered.

### Round-1 findings, re-checked

| # | Round 1 | Round 2 status |
|---|---|---|
| 1 | MAJOR: forks counted unweighted | **Resolved.** Root-only is the default. Forced rows are excluded and counted, so the duplicated fork-arm row is gone in both modes. Fork rows are counted as excluded. Verified on a schema-valid fork campaign. The weighted mode has new MINOR issues (R2-2). |
| 2 | MAJOR: empty epoch labelled as the gate outcome; STOP 4 fixture without E2; vacuous assertion | **Resolved.** There are three statuses. The fixture now has E2 rows (45 of 300 within 0.5 σ, Track S-like). The STOP 4 test checks each node's markdown line for E1 "no decision-relevant states" and for an E2 verdict other than "no". The mutation now flips E1. A cosmetic residue remains (R2-6). |
| 3 | MAJOR: invalid / divergent E2 rows | **Resolved.** They are excluded whatever their rule label, counted (`n_invalid_discards`) and need no m̂. Verified on the P1 invalid-candidate campaign with validation on. |
| 4 | policy skips | **Resolved.** Policy skips and executes are reported per node, and the STOP 4 test asserts 0 policy skips. |
| 5 | h scalar; Δ̂ | **Resolved:** h as a number or a mapping; `e2_stat="delta_hat"`; the demo uses N1's own h; tests with h ≠ 0. Residue: h is not finite-checked, and a missing node defaults silently (R2-1). |
| 6 | NaN; validate default | **Resolved for record fields:** finite checks name the row, `validate=True` is the API default, and `allow_nan=False` is set. **Not resolved for h** (R2-1). |
| 7 | bare KeyError / TypeError | **Mostly resolved.** A non-dict sub-object still raises `AttributeError` with validation off, e.g. `action = "execute"` fails on `act.get` (R2-5). |
| 8 | silent price sources | **Resolved:** a source is recorded per node and threshold, and `--g` / `--g-json` are mutually exclusive. New threshold-fallback issues (R2-4). |
| 9 | verdict rule unstated | **Resolved:** the rule is in the report header and the docstring, and the JSON field is `any_within_widest_band` with a `status`. |
| 10 | demo wording | **Resolved;** checked against the table. |
| 11 | pooling; intervals | **Resolved in form:** campaigns, policies and W are listed, and the intervals are clustered. The cluster unit and small-K behaviour are open (R2-3). |
| 12 | provenance; empty input | **Resolved:** inputs with sha256, the validation flag, and exit 2 on empty input. |
| 13 | CLI tracebacks | **Mostly resolved:** bands are validated, output directories are created, and errors carry `file:line`. Some paths still end in tracebacks (R2-5). |
| 14 | weak tests | **Resolved for the listed gaps.** New gaps are in R2-7. |
| 15 | readiness | **Resolved:** the belief must be named or unique, the B5 requirements are in the docstring, and several E1 thresholds are supported. |

### New findings

**R2-1. MINOR — h is not finite-checked; an h mapping that misses a node silently uses 0**

**Location:** `relevance.py:233` and line 295; CLI `--h` and `--h-json`.

**Why it matters:**
- A NaN h gives z = NaN on every E2 row. The epoch is then reported as "no decision-relevant states (0 of n …)". This is round-1 finding 6's silent wrong answer, again pointing toward "do not run", now through the new h path.
- `--h-json` containing `{"esyn_budget": NaN}` (which `json.loads` accepts) exits 0 with that verdict.
- `--h nan --json …` first writes the markdown with the wrong verdict, then crashes in `json.dumps(allow_nan=False)`.
- An h mapping that lacks a node silently uses 0, and unlike g, no source is reported.

**Fix:**
- Check h with `_finite` (scalar and mapping values), once per node, before computing anything.
- Report the h source per node (argument / mapping / default 0). Alternatively, refuse a mapping that misses a node with eligible E2 rows.

**R2-2. MINOR — weighted fork mode: undocumented estimand, depth-2 weights, unguarded p_select, unweighted counts**

**Location:** `relevance.py:247–252`, and the counters at lines 259–264 and 275–276.

**Why it matters:**
- **Estimand.** With weights 1/p_select, the weighted share is a ratio of Horvitz–Thompson totals over the root states **plus** every counterfactual continuation state that would exist had every root step been forked. Each fork contributes arms × replicates × continuation policies (8 in plan §6 SPT-3) whole continuations, so these counterfactual states dominate. That is a well-defined population, but it is not the share among the behaviour policy's states. The docstring presents the weighting as a correction of the oversample, so a reader may take the weighted share as the root share de-biased. Root mode, the default, is correct.
- **Depth-2 forks.** They are weighted by their own p_select only (`probe3.py`: 0.25, against 0.40 with the product along the path). Depth-2 forks are extension-only in the plan, but nothing refuses them.
- **Unguarded p_select with validation off.** p_select = 0 raises a raw `ZeroDivisionError`. p_select = −0.5 gives a share of −1.0 silently, and p_select = 2 is accepted.
- **Unweighted counts.** In weighted mode, `n_e1_rows`, the rule-skip share and the policy skips and executes are unweighted and include continuation rows, while the shares are weighted.

**Fix:**
- State the weighted estimand in the docstring and the report header.
- Multiply p_select along `branch_path` (one fork design per level), or refuse `len(branch_path) > 1`.
- Require 0 < p_select ≤ 1 and raise `RelevanceInputError` otherwise.
- Either weight the skip counts, or label them as unweighted row counts.

**R2-3. MINOR — the clustered interval uses the wrong cluster when policies share instances, and is too narrow with few campaigns**

**Location:** `_summarise`, lines 139–145; cluster variable at line 265.

**Why it matters:**
- **The formula is the standard linearised (CR1) variance of a weighted ratio, and it is right.** Simulated coverage at nominal 95 % is 0.94 (unweighted) / 0.93 (weighted) with 50 campaigns, 0.89 / 0.90 with 10, and 0.82 / 0.83 with 5.
- **Wrong cluster.** The module clusters by `campaign_id`, but the schema declares `identity.instance_id` as "cluster id: one per campaign instance". Paper C runs several policies on the same instance seeds, and Track S's S0.5 static rep-0 roots duplicate the a2u roots. Rows from the same instance under different policies are then correlated. With 3 policies × 30 shared budget-world instances, the half-width is 0.020 clustered by campaign against 0.035 clustered by instance (E2: 0.060 against 0.106).
- **Degenerate cases.** One cluster gives a half-width of 6e-17, printed "± 0.0%". At shares of 0 or 1 the Wald half-width is 0, which is visible throughout the demo ("100.0% ± 0.0%").

**Fix:**
- Cluster by `instance_id`, or make the cluster key an argument with `instance_id` as the default, and say which in the header.
- Use a t quantile with k − 1 degrees of freedom.
- Print "—" when there are fewer than 2 clusters.
- State the boundary behaviour, or use a clustered Wilson or bootstrap interval. This matters once the author puts a gate on a bound.

**R2-4. MINOR — threshold fallbacks and overrides are silent**

**Location:** `relevance.py:224` and lines 277–285; CLI line 408.

**Why it matters:**
- An extra threshold, e.g. `static={"a": 0.002}`, that misses node b falls back to b's forecast g, i.e. **the run price**. The result is reported as "static = 0.001 (forecast)": a static-threshold row that silently measures the price.
- `--threshold g=0.5` silently overrides `--g 0.001` (price used: 0.5).
- In the API, `g=` is silently ignored when `thresholds=` is given.

**Fix:**
- Apply the forecast / env fallback to the `g` label only, and raise an error for other labels with no value.
- Reject the label `g` in `--threshold`.
- Raise an error when both `g` and `thresholds` are passed, unless `thresholds` lacks `g`.

**R2-5. MINOR — remaining tracebacks**

**Location:** `main()`, `relevance()`.

**Why it matters:** these cases still end in tracebacks instead of exit 2 and a message:
- an invalid `--g-json` or `--h-json` (`JSONDecodeError`);
- a non-UTF-8 input file (`UnicodeDecodeError`);
- `--out` naming a directory (`IsADirectoryError`: the write is outside the try);
- the JSON NaN crash of R2-1, which comes after the markdown has been written;
- with validation off, a non-dict `action`, `identity` or `state` (`AttributeError`).

**Fix:**
- Catch `ValueError`, which covers JSON and Unicode errors, and `AttributeError`.
- Build both outputs before writing either, and do the writing inside the try.

**R2-6. MINOR — not-assessed epochs render as 0 %**

**Location:** `_summarise`, line 147; the markdown table; `to_dict`.

**Why it matters:** an epoch with no eligible rows shows "0.0% ± 0.0% (0)" in every band column, and JSON `shares` of 0.0. The verdict says "not assessed", but a reader of the share table (or of the JSON `shares`) sees 0 %.

**Fix:** use `None` in the JSON and "—" in the table when `n_eligible == 0`.

**R2-7. MINOR — test gaps for the new code**

**Location:** `tests/test_relevance_p5.py`.

**Missing tests:**
- the clustered half-width against a hand-computed value (only `> 0` is asserted);
- weighted quantiles (`_wquantile`) against a reference;
- depth-2 forks and p_select outside (0, 1];
- non-finite h;
- the extra-threshold fallback;
- `--threshold g=`.

**Fix:** add these alongside R2-1 to R2-5.

### Summary

All three round-1 MAJOR findings are resolved and verified on schema-valid P1 campaigns:

- root-only forks and excluded forced rows;
- the three-way verdict, with a STOP 4 fixture that now has E2 rows like Track S's;
- invalid and divergent E2 discards excluded and counted.

The twelve round-1 MINOR findings are resolved or reduced to the residues above. Two of the new MINOR findings should be fixed before the module is used on real records, but they block nothing at this engineering stage:

- **R2-1:** a non-finite h still produces a silent "no decision-relevant states";
- **R2-3:** the intervals are clustered by campaign rather than by the schema's instance cluster.

The default root mode, the arithmetic, the weighted quantile and the ratio-variance formula are correct. No BLOCKER or MAJOR finding remains.

Verdict: ACCEPT

---

## Post-acceptance check

- **Reviewer:** the same independent reviewer.
- **Commit:** `4af6f81`. Diff read against `440cb20`; response table `BUILD_P5_RESPONSE_R2_20261116.md`.
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

### What I ran

Scratch work is in `/tmp/p5rev/`: `probe6.py` and `cov_low.py`, plus CLI probes run inline.

- **Tests:** 187 passed, including 12 P5 tests.
- **Demo:** it regenerates the committed report byte for byte (`git status` clean).
- **New tests:** I read them and checked the hand-computed interval independently: p = 0.5, se = √3/8 = 0.21651, n_eff = 5.333, t(0.975, 2) = 4.3027, Wilson half-width 0.44057.
- **Round-2 probes** rerun on the new code.
- **Coverage:** the executor's `/tmp/p5fix/cov.py` reproduces its numbers exactly (e.g. 0.952 / 0.942 / 0.944 at share 0.15, K = 5 / 10 / 50). I added low-prevalence cells and probed the boundary rule.

### R2 findings, re-checked

- **R2-1, resolved.** NaN, inf and boolean h are refused, as scalar or mapping values. A mapping that misses a node with eligible E2 rows is an error, and the h source is reported. `--h nan --json` and `--h-json` with NaN both exit 2 and write nothing.
- **R2-2, resolved.** The weighted estimand is stated in the docstring and the report header. Nested forks are refused. p_select ∈ {0, −0.5, 2} is refused. Counts are labelled as unweighted.
- **R2-3, resolved.** `instance_id` is the default cluster, and the header names the key. The interval is Wilson with n_eff and a t(k − 1) quantile, and there is no interval with fewer than 2 clusters. See PA-1 for the boundary rule.
- **R2-4, resolved.** An extra threshold that misses a node is an error; `--threshold g=` and `static=nan` are rejected; g given twice raises.
- **R2-5, resolved.** A bad `--g-json`, binary input, `--out` naming a directory, a missing input and an empty input all exit 2 with a message. A non-dict `action` raises `RelevanceInputError`.
- **R2-6, resolved.** In JSON, not-assessed shares, standard errors and intervals are null; in the table they show as "—".
- **R2-7, resolved.** The listed tests exist and assert real values.

### The Wilson / n_eff choice

**The interior rule is sound.** n_eff = p(1 − p)/se², capped at the row count, with a t(k − 1) quantile, is the usual design-effect Wilson interval. It fixes the small-K under-coverage of round 2: at share 0.15, coverage is 0.95 at K = 5 against 0.85 for the old Wald interval.

**PA-1. MINOR — the boundary rule n_eff = k is conservative, but it does not join up with the interior rule at sparse counts.**

*Non-monotone bound.* The upper bound is not monotone in the evidence (`probe6.py`; 50 clusters × 20 rows):

| hits in the band | upper bound |
|---|---|
| 0 | 7.47 % |
| 1 | 0.58 % |
| 2 | 1.17 % |
| 5 (all in one cluster) | 2.9 % |

Observing one near-threshold row lowers the upper bound thirteen-fold. The cause: with one hit, the CR1 se comes from a single cluster and gives n_eff ≈ n, while with zero hits n_eff = k.

*Under-coverage when hits are sparse.* In the same regime the interval under-covers (`cov_low.py`: K = 50, share 0.003, strong clustering, 1,000 replications):
- the upper bound lies at or above the truth in 92.2 % of samples, against 97.5 % nominal;
- two-sided coverage is 0.887;
- by contrast, at K = 10 most samples have 0 hits, so the conservative boundary rule dominates and coverage is 0.97.

The executor's 0.92–0.93 at share 0.03 (K = 10 and 50) is the same effect in milder form.

*Unequal cluster sizes.* At p ∈ {0, 1}, n_eff = k ignores them. One cluster of 191 rows plus nine of 1 row gives the same bound (33.9 %) as ten clusters of 20, although Kish's effective cluster count is 1.1 against 10.

*Why it matters.* The "no decision-relevant states" status now prints this upper bound, and a future gate may use a bound on a small share. Under such a gate, few hits would read as more certain than none.

*Fix* (before any gate uses a bound; not needed for engineering acceptance):
- Use Kish's effective number of clusters, (Σ m_c)² / Σ m_c² with m_c the cluster weight totals, in place of k.
- Use the same convention whenever the hits (or the misses) fall in fewer than a declared number of clusters, so that the bound is monotone across the boundary. A cluster bootstrap for sparse counts is an alternative.
- At minimum, state in the docstring and the report header that bounds from sparse counts are anti-conservative.

**Nit.** If the `--json` write fails, e.g. because the path is a directory, the markdown has already been written; the run still exits 2. Write both outputs to temporary files and rename them, or check both targets first.

No BLOCKER or MAJOR finding.

Verdict: ACCEPT
