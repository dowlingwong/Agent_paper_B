# Track X B2 — STOP 6 report template (15 November 2026)

**AI-assisted (Claude, Mac agent). Engineering unit. It is not an author decision and does not touch the B2 run.**
The unit adds a renderer for the STOP 6 report draft (`docs/r1/reports/PROPOSER_EXAM_<date>.md`, runbook Phase 6),
tested on synthetic fixtures.

- Branch: `mac-b2-stop6-report-20261115`, from `mac-b2-handoff-exec-20261115` @ `aeeab991`.
- Input formats: those of `mac-b2-code-20261114` @ `a2cd540c`.
- Files: `r1/scripts/b2_stop6_report.py` and `r1/tests/test_b2_stop6_report.py`.
- Nothing under the protected paths (`r1/exam`, `r1/scripts/exam_runner.py`, …) changes, so the B2 run HEAD's
  protected-path rule is unaffected.

## 1. Inputs

| File | What it is |
|---|---|
| `analysis.json` | The stdout of `python -m r1.exam.analyze b2 --batch <batch> --config <cfg> --rule r1/exam/rules/x5_rule_v2.yaml --rule-sha256 <sha>`: `_b2_summary_v2`, plus `execution_label` and `batch_verification` (grid, shas). |
| `b2_manifests.json` | The batch aggregate `{"label": "EXAM", "manifests": [...]}`. |
| `invalid_trials.json` | Schema `b2_invalid_trials/v1` (§2). Written by `derive-invalid` from the batch's roots. This is the hand-off §6 item "per candidate, mode and check the invalid-trial counts". |
| B1 analysis | The frozen `complete_batch_verifier.json` (sha256 `07cb62de…`) that the B2 analysis binds. The scripted anchor ran only in B1, so its μ̂ comes from this file. |

## 2. `invalid_trials.json` (`b2_invalid_trials/v1`)

`derive-invalid --batch <batch> --analysis analysis.json --out invalid_trials.json` covers exactly the verified grid
of the analysis: finalist × mode × node × instance. It reads each root's `root_trials.jsonl`, `b1_proposals.jsonl`
and `campaign_manifest.json`, and writes one row per root:
`{candidate, mode, node, instance_id, trials, invalid, classes, llm_calls}`.

A trial is invalid when its ledger decision is `failed_invalid`. Its class is read from the trial's last journal
row, as `validate_proposal_journal` does:
- a model-output rejection → `model_output:<check>`;
- otherwise a truncated reply → `truncated`, a context overflow → `context_overflow`, an unencodable reply →
  `unencodable_reply`;
- otherwise → `other_invalid`: a harness parse or precondition failure, or a trial with no journal row.

It refuses (`STOP: …`) when:
- the batch's `b2_manifests.json` is not the file the analysis verified;
- a root's invalid or trial count differs from its `diagnostics`;
- the model-output classes differ from the root's `proposal_journal.rejected_by_check`.

It can run on the host (read-only) or on a copy-back of the roots.

## 3. What `render` checks before printing anything

Each check refuses with `STOP: …`.

**Analysis**
- It is an EVIDENCE x5_rule/v2 B2 analysis, pending the author, with a verified grid.
- `b2_manifests.json` and the B1 analysis are byte-for-byte the files whose sha256 the analysis binds.
- The rule file in this checkout matches the analysis's rule sha256.

**Manifests and B1 finalists**
- The manifests are exactly the grid's finalists, in order.
- The B1 finalists equal the grid's finalists.

**Final Y**
- Every final-Y audit has ten finite metrics on seeds 9201–9210, and its `final_y` is their mean (abs. 1e-12).
- Each analysis row's `final_y` is the mean of its manifest's final audits and covers the grid.
- GPU-h agrees between the analysis row, the verified grid and the manifest.
- The ranking and `rule_top` follow final Y, with ties going to lower GPU-h.

**Thinking-on rerun**
- The rerun exists exactly for the grid's two-mode finalists and covers the grid.
- The analysis's descriptive rows are the manifests' rerun means.

**Invalid trials**
- The rows cover the grid exactly once.
- Each row's classes add up to its `invalid`.
- The per-candidate totals equal the manifest's `diagnostics.invalid` and `trials`.

**Not rendered**
- Schema-free sensitivity rows are refused. They are separately gated, and this template does not render them.

## 4. What it renders

0. **Inputs.** Every input with its sha256, the batch state, run HEAD, rule and grid.
1. **Finalist and the rule pick.** With one finalist, the text says that this finalist is the rule pick whatever its
   B2 score, and that there is no second proposer among the finalists. For B2 now that is `gemma4_31b`
   (authorization note of 15 Nov).
2. **B2 final audited Y (the ranking quantity).**
   - Per node: n, mean and a Student-t 95 % CI over instances.
   - Pooled over nodes (labelled as not used by the rule).
   - The ranked table with verified GPU-h.
3. **μ̂ against the scripted anchor.**
   - B1: μ̂ and the cluster interval for the scripted anchor and each finalist, the point difference, and whether
     the finalist is below the anchor. Descriptive; not a rule quantity.
   - B2: the finalist's audited mean increment per node and pooled, using the same bootstrap as B1 μ̂
     (`analyze.bootstrap_mean`, with the rule's seed and resamples).
   - The text states that no anchor ran in B2, and that the B1 and B2 values come from different instances and audit
     seeds.
4. **D28.** Per finalist:
   - the B2 thinking-off status (decides eligibility; scope `thinking_off_roots_only`);
   - the descriptive thinking-on D28;
   - the B1 D28.
5. **Invalid trials.** Per candidate × mode × class, and per node (thinking off) with LLM calls.
6. **Thinking-on rerun, in its own section.** Per node: thinking-on mean, CI, and the thinking-off mean on the same
   node. Marked "never enters the ranking".
7. **Other manifest diagnostics.**
8. **For the author.** X.7 (a), (b) and (c), listed as pending. With one finalist, (b) has no other finalist to
   choose, and the author decides how B.6 proceeds.

## 5. Tests (`r1/tests/test_b2_stop6_report.py`, 29 passed)

- The analysis fixture is produced by the real `analyze._b2_summary_v2` on synthetic manifests: one finalist with a
  rerun, 3 nodes, n = 4. So the template is tested against the code's own output shape.
- Covered:
  - all sections render;
  - per-node final Y and B2 μ̂ are recomputed independently in the test (`analyze.bootstrap_mean`);
  - the B1 difference is right;
  - the invalid-trial tables are right;
  - a Student-t check;
  - a two-finalist case (ranking order; no single-finalist sentence).
- 19 tamperings, each refused with its own message.
- Further refusals: a missing scripted-anchor row, a B1 finalist mismatch, and rule bytes that differ from the
  analysis sha.
- `derive-invalid`, on a synthetic batch of 24 roots:
  - the classes come out right, including a revision followed by a rejection, and a trial with no journal row;
  - a root whose diagnostics disagree is refused;
  - a root whose journal summary disagrees is refused.

Command: `/tmp/trackg_venv/bin/python -m pytest -q r1/tests/test_b2_stop6_report.py`.

## 6. Limits

- **`derive-invalid` does not re-verify roots.** It relies on the analysis having been produced by
  `verify_b2_batch`, which the analysis's `batch_verification` attests. It only cross-checks counts against each
  root's own manifest.
- **No precision-against-plan line.** The template does not compare the achieved per-node CI half-width with the
  power plan's target (1 · σ_node,j). σ_node is not among the inputs. The reviewer can add the line from
  `b2_power_plan.json`.
- **The draft is not the report.** STOP 6 still needs the review loop: the reviewer recomputes every table from the
  manifests. X.7 is decided by the author.
