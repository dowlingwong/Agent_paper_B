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
- otherwise → `other_invalid:<category>`, by the harness `failure_category` of the ledger row (parse or precondition
  failure, runtime error, missing metric, …; `none` if absent).

Before reading a root it checks a sha256 chain back to what the analysis verified:
- `batch_state.json` = the analysis's `batch_state_sha256`;
- the root's `campaign_manifest.json` = that state's `completed[key].sha256`;
- `root_trials.jsonl` and `b1_proposals.jsonl` = the manifest's `evidence_hashes`.

The output records `batch_manifests_sha256` and `batch_state_sha256`.

It refuses (`STOP: …`) when:
- any link of that chain fails;
- a root's invalid or trial count differs from its `diagnostics`;
- the model-output classes differ from the root's `proposal_journal.rejected_by_check`;
- a flagged last journal row (truncated, overflow, unencodable or rejected) sits on a trial that is not `failed_invalid`.

It can run on the host (read-only) or on a copy-back of the roots.

## 3. What `render` checks before printing anything

Each check refuses with `STOP: …`.

**Analysis**
- It is an EVIDENCE x5_rule/v2 B2 analysis, pending the author, with a verified grid.
- `b2_manifests.json` and the B1 analysis are byte-for-byte the files whose sha256 the analysis binds.
- The rule file in this checkout matches the analysis's rule sha256.

**Manifests and B1 finalists**
- The manifests are exactly the grid's finalists, in registry order.
- The B1 finalists equal the grid's finalists as a set. B1 lists them by μ̂, the grid by registry order.

**Final Y**
- Every final-Y audit has ten finite metrics on seeds 9201–9210, and its `final_y` is their mean (abs. 1e-12).
- Each analysis row's `final_y` is the mean of its manifest's final audits and covers the grid.
- GPU-h agrees between the analysis row, the verified grid and the manifest.
- The ranking and `rule_top` follow final Y, with ties going to lower GPU-h.

**Thinking-on rerun**
- The rerun exists exactly for the grid's two-mode finalists and covers the grid.
- The analysis's descriptive rows are the manifests' rerun means.

**Invalid trials**
- The file declares this batch: its `batch_manifests_sha256` and `batch_state_sha256` equal the analysis's. `render` cannot see the roots, so this checks the declaration, not the per-row content (§6).
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
   - B1: μ̂ and the cluster interval for the scripted anchor and each finalist, and the point difference. The text
     says whether the point estimate is below the anchor's, whether the two 95 % intervals overlap, and that the
     comparison is unpaired and descriptive, not a rule quantity.
   - B2: the finalist's audited mean increment per node and pooled, using the same bootstrap as B1 μ̂
     (`analyze.bootstrap_mean`, with the rule's seed and resamples).
   - The text states that no anchor ran in B2, that the B1 and B2 values come from different instances and audit
     seeds, and that per-node intervals rest on few clusters.
4. **D28.** Eligibility, D28 included, was decided in B1 at STOP 5. Per finalist:
   - the B2 thinking-off status, recorded and verified but not used by the B2 ranking (scope `thinking_off_roots_only`);
   - the descriptive thinking-on D28;
   - the B1 D28, which decided eligibility.
5. **Invalid trials.** Per candidate × mode × class, and per node (thinking off) with LLM calls, which include the
   A4 observer calls.
6. **Thinking-on rerun, in its own section.** Per node: thinking-on mean, CI, and the thinking-off mean on the same
   node. Marked "never enters the ranking".
7. **Other manifest diagnostics.**
8. **For the author.** RUNBOOK X.7, quoted verbatim, and the rule pick for (a). Nothing in the draft decides
   (a), (b) or (c).

## 5. Tests (`r1/tests/test_b2_stop6_report.py`, 42 passed)

- The analysis fixture is produced by the real `analyze._b2_summary_v2` on synthetic manifests: one finalist with a
  rerun, 3 nodes, n = 4, and thinking-on audited proposals that must stay out of B2 μ̂. So the template is tested
  against the code's own output shape.
- Covered:
  - all sections render, with the D28, anchor and X.7 wording;
  - per-node final Y and B2 μ̂ are recomputed independently in the test (`analyze.bootstrap_mean`, thinking off only);
  - the B1 difference is right;
  - the invalid-trial tables are right;
  - a Student-t check;
  - a two-finalist case (ranking order; no single-finalist sentence);
  - an exact final-Y tie that goes to the lower GPU-h, with the B1 finalists in another order than the grid.
- 25 tamperings of the four inputs are each refused, among them rule version, pending flag, schema-free rows,
  descriptive source, GPU-h type, rerun coverage, and the invalid file's batch-state binding.
- Further refusals: unreadable JSON, a missing scripted-anchor row, a B1 finalist mismatch, and rule bytes that differ
  from the analysis sha.
- `derive-invalid`, on a synthetic batch of 24 roots with a batch state and evidence hashes:
  - the classes come out right, including a revision followed by a rejection, a trial with no journal row, and
    `other_invalid:runtime_error`;
  - refused: a changed batch state, a root manifest not recorded in the state, a ledger that does not match its
    evidence hash, root diagnostics that disagree, a journal summary that disagrees, and a flagged journal row on a
    valid trial.

Command: `/tmp/trackg_venv/bin/python -m pytest -q r1/tests/test_b2_stop6_report.py`.

## 6. Limits

- **`derive-invalid` does not re-verify roots in full.** It checks only the sha256 chain from the verified batch
  state to the files it reads, and cross-checks counts against each root's own manifest. The full verification is
  `verify_b2_batch`, which the analysis attests.
- **`render` cannot detect an edit of `invalid_trials.json` made after `derive-invalid`** that keeps the
  per-candidate totals, such as moving trials between modes or nodes. `derive-invalid` is deterministic, and §0
  prints the file's sha256. The STOP 6 reviewer therefore re-runs `derive-invalid` on the roots and compares the
  sha256.
- **No precision-against-plan line.** The template does not compare the achieved per-node CI half-width with the
  power plan's target (1 · σ_node,j). σ_node is not among the inputs. The reviewer can add the line from
  `b2_power_plan.json`.
- **The draft is not the report.** STOP 6 still needs the review loop: the reviewer recomputes every table from the
  manifests. X.7 is decided by the author.
