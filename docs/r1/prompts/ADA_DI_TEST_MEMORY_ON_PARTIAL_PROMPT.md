# Prompt: memory-on DI diagnostic on the preserved partial rerun-2 arm A (PILOT; no GPU)

*Written 19 Oct 2026 by the coordinating session (Claude). The author authorised analysing the preserved, interrupted rerun-2 arm A for this diagnostic (PLAN §10, row dated 19 Oct). Give this whole file to the operator agent with SSH access to Ada (`ucrtasl`).*

---

You are the operator agent for Dowling Wong (author), Paper B route R1, `github.com/dowlingwong/Agent_paper_B`. Before starting, read:
- `docs/r1/reports/DI_TEST_E1B_20261019.md`, **including the 19 Oct addendum** ("record-reference effect");
- `docs/r1/reports/RERUN2_STOP_DIAGNOSIS_20261019.md`;
- `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` §5–6;
- PLAN §10 rows dated 18–19 Oct.

## Why

The memory-off DI diagnostic flagged a contrast, but the review addendum shows it is mainly a **record-reference shift**: after a verify promotion, the verify branch's recorded incumbent is ≈ 0.005 lower, so later Δ̂ are measured against a lower bar. The primary C3 proposer runs with memory `append_only_summary`. Its branch data already exist in the preserved rerun-2 arm A (memory on, D25 active keys, D26 seeds): 648 leaves, 7 failed. This task re-tests DI with **absolute metrics**, first on that memory-on data, then on the memory-off DT4 data.

## Ground rules

- **Read-only on the preserved batch** `B = /data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/`. Copy files out; never write inside B; never resume, retry or complete the arm.
- **No LLM calls, no Ollama, no GPU, no worker runs.** File analysis only.
- Labels: **PILOT, PARTIAL, not evidence.** The arm was interrupted and never passed its collection gate. Say this in every output, and say "AI-assisted" with your name.
- **Stop rule (the author's revised rule, still in force):** if an analysis definition here conflicts with the data, follow the data, document it under "Deviations from the prompt", and continue. Stop only for the safety rules above, or a push that still conflicts after one `git pull --rebase`.
- Work in your existing diagnostic clone `/data1/dowling/tmp/r1_diag_ENGINEERING_ONLY_20261018T223815Z/repo` after `git pull` (it must contain `1840efe` or later), or a fresh clone. Use the same repository-local git identity as before, plus your own `Co-Authored-By:` trailer.

## Step 1 — snapshot the partial memory-on data into the repository

- Source:
  - arm output `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/` (leaves, roots, audits, manifest);
  - ledgers `B/r1_e1b_rerun2_A_work/roots/<instance>/root_trials.jsonl` and `B/r1_e1b_rerun2_A_work/branches/<leaf>/branch_trials.jsonl`.
- Destination: `results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/`, with the same sub-layout as `results/r1/pilot/E1b_20261013T151857Z/` (`leaves/`, `roots/`, `audits/`, `manifest.json`, `provenance/ledgers/{roots,branches}/…`).
- Copy `*_trials.jsonl` for all roots and branches. From `*_events.jsonl`, keep only a compact extract: `memory_context_built` text and `llm_call` seed/latency fields, one JSONL per root or branch. Do not copy `node/`, `art/`, `.venv` or checkouts.
- Add `SNAPSHOT.md` stating:
  - source paths;
  - SHA-256 of every copied source file (written to `sha256_manifest.txt`);
  - the 7 failed leaves (list them);
  - that the arm was interrupted and that this is a PILOT diagnostic snapshot, authorised on 19 Oct.
- `*.jsonl` is ignored by `.gitignore`, so add these files with `git add -f`, as the E1b provenance ledgers were.
- **Size check:** if the snapshot exceeds 40 MB, drop the event extracts first and say so. Do not commit large artifacts.

## Step 2 — extend the DI script to absolute metrics

Extend `r1/diagnostics/di_test.py`. Do not fork it; keep the existing outputs byte-identical under the default options.
- **`--outcome abs_metric` (new primary).** Per branch, the mean **parsed metric** of the next k = 1 and k = 3 evaluated trials after the point. Compute all distances (D_changed, paired D_null, D_unchanged), inference (point-label permutation within node, instance cluster bootstrap, Holm over the primary comparisons) and the combined decision rule exactly as in the existing report.
- **Record shift, reported separately.** verify − continue recorded incumbent value before the first post-point trial, for changed and unchanged points. Never use Δ̂ relative to branch-specific records as a primary outcome.
- **Value check (exploratory).** Y = mean of the leaf's audit metrics (common audit seeds across branches, so Y is paired within a point). For changed points:

  residual = (Y_verify − Y_continue) − (immediate value of the changed decision) − (budget cost of verify)

  - **Immediate value:** for a promotion, + the verify mean paired delta D̄ of the promoted candidate; for a demotion, − D̄. State that D̄ (r = 2) is a noisy proxy.
  - **Budget cost:** the mean (Y_verify − Y_continue) over unchanged points of the same node and budget index (or node, if too few).
  - Report the residual with an instance cluster bootstrap interval. **This is the quantity T4 Proposition 10(a) is about.** A residual near 0 means the continuation value does not depend on the decision.
- **Mechanism (secondary), as before:** edited-key TV, signed log edit size, active novelty, duplicates. Add one memory-specific measure: whether the memory text shown before the first post-point trial differs between the branches (it should, since it reports kept edits and the best value), and whether the next proposal repeats or reverses the changed edit.
- Make the layout loader accept both the DT4 layout and the new snapshot layout.
- Add tests in `r1/tests/test_di_test.py`:
  - a fixture with a pure record shift and no proposal change: `abs_metric` must not reject; Δ̂ would;
  - a fixture with a true proposal shift: `abs_metric` must detect it.

## Step 3 — run both datasets

1. **Memory on (primary):** `E1b_rerun2_A_PARTIAL_memory_on_20261014`.
   - Nodes: those present (expected `tabular_mlp`, `openml_ionosphere`, `openml_breast_w`; `digits_mlp` was excluded by liveness).
   - Exclude every point that has any failed leaf (all four of its leaves), and list the excluded points.
   - Report per node and pooled. Report decision changes per node and direction (promotion / demotion).
   - Check whether ionosphere is non-degenerate now that D25 applies; report its metric-identical fraction.
2. **Memory off (re-analysis):** `E1b_20261013T151857Z` with `--outcome abs_metric`. This updates the 19 Oct verdict on the correct outcome.
3. **Side by side:** memory on vs memory off, on the nodes they share, if any. Otherwise report separately and say that a node-matched comparison is not possible.

Note: rerun-2 used the `"fixed"` split (the `"vary"` decision came later), and its frozen verify response may promote or demote. State both.

## Outputs

- `docs/r1/reports/DI_TEST_MEMORY_ON_PARTIAL_<YYYYMMDD>.md` and `_tables.md`. Sections: question; data and snapshot provenance; decisions changed; measures (why absolute metric); results (abs-metric distances, record shift, value residual, mechanism); memory off re-analysis; limitations; verdict for C4 / A7.
- **Verdict:** one of "DI approximately holds in value terms", "violated in value terms", or "undetermined at this sample size". Base it on the value residual and the abs-metric contrast, not on Δ̂.
- **Limitations to state:** partial, interrupted arm; `"fixed"` split; selection of changed points by verify outcome (not randomised); D̄ as a noisy proxy; no proposal-level audits.
- A dated entry at the top of `docs/r1/STATUS.md`.
- Commit the snapshot directory, script, test, reports and STATUS. Run `git diff --cached --check` (whitespace) on the non-data files; data files are copied byte-for-byte and are exempt, so state that. Push to `origin main`.
- Reply to the author with: the snapshot size and excluded points; decision changes by direction; the abs-metric contrast and value residual with intervals (memory on and memory off); the verdict; the commit hash.
