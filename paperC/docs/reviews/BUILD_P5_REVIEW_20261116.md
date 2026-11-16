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
