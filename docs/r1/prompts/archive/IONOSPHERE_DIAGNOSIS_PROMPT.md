# Prompt: diagnose the degenerate ionosphere result of the DT4 LLM rerun (14 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to an agent that runs on the author's Mac, with read access to Ada as `experiment_zhixu`.*

---

You are the implementation agent for Paper B, route R1. This is a **read-only diagnosis**. Do not fix anything. Your output is one report, the script that generates its tables, and one STATUS entry.

## What is known

In the DT4 rerun (`results/r1/pilot/E1b_20261013T151857Z`, PILOT; pinned `qwen2.5-coder:7b`; harness `9c4902d`), on `openml_ionosphere`, at all 18 E2 decision points (6 instances × trials 4, 8, 12):

- the observed increment Δ̂ is exactly 0.0000;
- `n_keeps` is 1, so the incumbent never changed from the start configuration;
- every leaf has Y = 0, ρ = 0 [0, 0], and verify changes no leaf.

The start configuration is:

```
model_type: logistic_regression, C: 0.15, max_depth: 5, n_estimators: 100,
learning_rate: 0.05, class_weight: balanced, scaler: standard,
imputer: most_frequent, max_iter: 1000
```

The scripted proposer on the same node and seeds (`results/r1/pilot/E1b_20261012T161034Z`) found real gains: ρ = +0.019.

On `digits_mlp` under the same LLM, Δ̂ is identical at trials 4, 8 and 12 of the same instance (e.g. `s104`: −0.0084; `s154`: −0.0111), and the two repetitions mostly give identical leaves. That suggests the LLM re-proposes the same edit and decodes deterministically.

**Working hypothesis (unconfirmed):** the LLM mostly edits keys that do nothing under `model_type: logistic_regression` (`max_depth`, `n_estimators`, `learning_rate`, possibly others), so the metric is bit-identical and the strict keep rule never fires. The diagnosis must confirm or refute this with evidence. Do not assume it.

## Hard rules

1. **No LLM calls and no GPU.** No new campaigns, no `e1b_collect`, no change to the harness, the manager, prompts, nodes, PLAN or RUNBOOK.
2. **At most 10 CPU worker runs**, label ENGINEERING_ONLY, and only for question Q2c below. Run them on the Mac with `LocalWorker` and the node's default seeds; write them under `results/r1/engineering/ionosphere_diag_<UTC>/`. Never run them inside the DT4 collection directories.
3. **Read-only on existing data.** Do not modify anything under `results/r1/pilot/` or on Ada. On Ada you may only read files in `B=/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS`.
4. Report facts with their source (file and line or field). Separate **established** (shown by data or code) from **inferred**. Label the work as AI-assisted. Propose fixes, but do not choose or implement one; the author decides.

## Sources

- Repository: `~/Documents/agent_paper_B` (pull first; HEAD should include `13f93f5`).
  - Committed collection: `results/r1/pilot/E1b_20261013T151857Z/`, including `records.jsonl`, `points.json`, `roots/`, `leaves/`, `audits/` and `provenance/ledgers/{roots,branches}/**/*.jsonl` (root trials, branch trials, branch events).
  - Snapshots: `provenance/snapshots/openml_ionosphere__s*/E2_b{004,008,012}/` (editable files and the incumbent at each decision point).
  - Scripted comparison: `results/r1/pilot/E1b_20261012T161034Z/` (same layout).
- Harness: `~/Documents/autoresearch_harness`. Read the code **at commit `9c4902d`** (`git show 9c4902d:<path>`, or a worktree at that commit). Do not check it out over the working tree.
- Ada, only if the committed ledgers lack the edit contents or the LLM payloads: `$B/r1_e1b_llm_work/` (per-trial `.autoresearch_artifacts/trial-*/patch.diff`, `run.log`, and `events.jsonl` with `llm_call` events).

## Questions

**Q1. What did the LLM propose on ionosphere?**
For every trial in the 6 root ledgers, and in the branch ledgers after each decision point, tabulate:

- instance, trial index, `proposal_summary`;
- the edited key(s) with old → new values (from the ledger, the snapshot diff or `patch.diff`);
- validity or invalid status, the parsed metric, the incumbent metric, Δ̂, and keep or discard.

Summarise across roots:

- counts by edited key;
- the share of trials whose metric is bit-identical to the incumbent's;
- the share of invalid trials;
- the number of distinct proposals per root, and the longest run of an identical proposal.

**Q2. Are those edits inert under `logistic_regression`?**

- **(a)** From the harness node code at `9c4902d`: which config keys reach the model when `model_type` is `logistic_regression`? List every key with "used" or "ignored", and cite file and line.
- **(b)** Did the LLM ever change `model_type`, `C`, `class_weight`, `scaler`, `imputer` or `max_iter`? If it did, what happened to the metric?
- **(c)** Only if (a) leaves doubt: run up to 10 CPU runs on the start configuration with one inert-candidate key changed at a time, at the default seeds, and show that the metric is (or is not) bit-identical.

**Q3. What does the manager see?**
From the LangGraph manager code and prompt template at `9c4902d`, and from one recorded `llm_call` payload if one is available:

- Is `model_type` shown?
- Is the LLM told which keys apply to the current model?
- Does the history it sees show that earlier edits left the metric unchanged?
- Is there any instruction that discourages structural changes?

Quote the relevant prompt lines briefly.

**Q4. Is decoding deterministic?**
Find the manager's sampling settings (temperature, top-p, seed, Ollama options) at `9c4902d`. Then:

- Do identical ledger prefixes give identical proposals across the two repetitions of a branch?
- Repeat the Q1 repetition statistics for `digits_mlp`, for comparison.

**Q5. How does the scripted proposer differ?**
For the same 6 ionosphere roots in `E1b_20261012T161034Z`, give the counts by edited key and the keep rate, so the two proposal laws can be compared on the same node.

**Q6. Does anything else explain Δ̂ = 0?**
Rule out, or confirm, each of:

- a metric-parsing default;
- an incumbent read error;
- an edit that is never applied (patch present, file unchanged);
- the worker reusing a cached result.

Cite the evidence for each.

## Outputs

1. `r1/diagnostics/ionosphere_llm_diag.py`: reads only the sources above and prints, or writes, the Q1, Q4 and Q5 tables. Re-running it must reproduce the tables.
2. `docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md`, labelled ENGINEERING_ONLY and AI-assisted, with these sections:
   - Summary: 3–5 lines, with the verdict on the hypothesis;
   - Q1–Q6 with evidence;
   - Implications for E1b, E3 and the OpenML pool;
   - Fix options for the author, each with its cost and what it changes about the proposal law. Examples to consider (not prescriptions):
     - expose only the keys that are active for the current `model_type`;
     - tell the manager which keys are active;
     - surface "metric unchanged" in the history;
     - set a sampling temperature and seed for the manager (a D15-scope decision);
     - leave it as is and treat inert edits as part of the proposer.
3. A STATUS entry at the top of `docs/r1/STATUS.md`: date, what was examined, the verdict, and where the report is. No decision is recorded; the decisions belong to the author.

## Finish

```sh
cd ~/Documents/agent_paper_B
git status --short     # only the new script, the report, STATUS, any results/r1/engineering/ionosphere_diag_* and this prompt
git add <those paths>
git diff --cached --check
git commit -m "Diagnose degenerate ionosphere result of the DT4 LLM rerun (ENGINEERING_ONLY)" -m "<your attribution trailer>"
git push origin main
```

Then report to the author in a few lines: the verdict, the two or three facts that decide it, and the fix options. Do not pick one.
