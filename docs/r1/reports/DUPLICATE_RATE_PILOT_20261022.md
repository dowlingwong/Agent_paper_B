# Duplicate and no-op rate of LLM proposals — pilot, 22 Oct 2026

**PILOT. AI-assisted (Claude), implementation agent on branch `c3-prep-22oct`.** Not evidence. Small, partly PARTIAL and partly pre-D25 data; the numbers check the C1 reporting pipeline (PLAN §10, "Duplicates (22 Oct)") and are not a C1 result.

## What was run

- Proposal table rebuilt from the committed root ledgers with `python -m r1.c3.dataset build --out results/r1/engineering/c3_duplicate_rate_20261022` (the same three sources as the 19 Oct pilot: DT4 `E1b_20261013T151857Z`, memory `none`, W = 20; the PARTIAL memory-on rerun-2 arm A, W = 20; the 14 Oct liveness run, memory on, W = 10). 1,400 ledger rows → 1,323 proposals; replay checks 0 violations. Apart from the new `noop_kind` field the table is identical, row for row, to the uncommitted 19 Oct table in `c3_split_recheck_20261019/`.
- Report: `python -m r1.c3.duplicate_report --table results/r1/engineering/c3_duplicate_rate_20261022` → `duplicate_rate.json`, `duplicate_rate.md` in that directory (`proposals.jsonl` is git-ignored and reproducible from the command above).
- No LLM, worker, GPU or network use. File-only, under 2 s.

## Definitions (PLAN §10, 22 Oct)

- **No-op, inactive edit:** the edit changes only keys that are inactive for the node's current model (Δ = 0).
- **No-op, incumbent repeat:** the candidate's active configuration equals the incumbent's (Δ = 0).
- **Duplicate:** the candidate's active configuration equals an earlier evaluated, non-incumbent configuration of the same campaign; its result is known from the ledger.
- **Wasted runs under ρ:** ρ executes every proposal, one run each, so every no-op and duplicate costs one run that the rule layer (A2+) would save. Trial 1 (no incumbent comparison) and the 3 invalid trials are not proposals of the table and are not counted.

## Table

| Source | Node | Memory | Campaigns | Proposals | No-op: inactive edit | No-op: incumbent repeat | Duplicate | Other | No-ops | Duplicates | Wasted runs under ρ (per campaign) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dt4 | digits_mlp | none | 6 | 114 | 0 | 0 | 88 | 26 | 0.0 % | 77.2 % | 88 = 77.2 % (14.7) |
| dt4 | openml_ionosphere | none | 6 | 114 | 114 | 0 | 0 | 0 | 100.0 % | 0.0 % | 114 = 100.0 % (19.0) |
| liveness | digits_mlp | append_only_summary | 2 | 18 | 0 | 0 | 8 | 10 | 0.0 % | 44.4 % | 8 = 44.4 % (4.0) |
| liveness | openml_breast_w | append_only_summary | 2 | 17 | 0 | 0 | 6 | 11 | 0.0 % | 35.3 % | 6 = 35.3 % (3.0) |
| liveness | openml_ionosphere | append_only_summary | 2 | 18 | 0 | 0 | 9 | 9 | 0.0 % | 50.0 % | 9 = 50.0 % (4.5) |
| liveness | tabular_mlp | append_only_summary | 2 | 18 | 0 | 0 | 8 | 10 | 0.0 % | 44.4 % | 8 = 44.4 % (4.0) |
| rerun2A | openml_breast_w | append_only_summary | 18 | 340 | 0 | 0 | 209 | 131 | 0.0 % | 61.5 % | 209 = 61.5 % (11.6) |
| rerun2A | openml_ionosphere | append_only_summary | 18 | 342 | 0 | 0 | 225 | 117 | 0.0 % | 65.8 % | 225 = 65.8 % (12.5) |
| rerun2A | tabular_mlp | append_only_summary | 18 | 342 | 0 | 0 | 174 | 168 | 0.0 % | 50.9 % | 174 = 50.9 % (9.7) |
| **all** | **all** | **append_only_summary** | 62 | 1095 | 0 | 0 | 639 | 456 | 0.0 % | 58.4 % | 639 = 58.4 % (10.3) |
| **all** | **all** | **none** | 12 | 228 | 114 | 0 | 88 | 26 | 50.0 % | 38.6 % | 202 = 88.6 % (16.8) |
| **all** | **all** | **all** | 74 | 1323 | 114 | 0 | 727 | 482 | 8.6 % | 55.0 % | 841 = 63.6 % (11.4) |

## Reading

- Rule-detectable proposals are the majority: 841 of 1,323 proposals (63.6 %) would be skipped by the rule layer; in the 20-run memory-on campaigns of rerun-2 arm A that is 9.7–12.5 runs per campaign. Almost all of them are **duplicates** (727); the no-ops (114) are all inactive edits from one stratum.
- **Memory on** (`append_only_summary`, rerun-2 arm A, 18 campaigns per node): duplicates are 51–66 % of proposals (tabular 50.9 %, breast-w 61.5 %, ionosphere 65.8 %). The liveness campaigns (W = 10) show 35–50 %, consistent with shorter campaigns offering fewer earlier configurations to repeat (2 campaigns per node; not a tested difference).
- **Memory off** (DT4): `digits_mlp` repeats an earlier evaluated configuration in 77.2 % of proposals; DT4 `openml_ionosphere` proposals are 100 % inactive edits (the 14 Oct ionosphere diagnosis: `n_estimators` / `max_depth` under `logistic_regression`). DT4 (13 Oct) predates the D25 decision (14 Oct), under which an inactive-key proposal is rejected before any worker run; in data collected under D25 such proposals would not appear as executed proposals, so the inactive-edit count of newer data understates what the proposer proposes.
- No incumbent repeats occurred in this table: every no-op was an inactive edit, and every return to an evaluated configuration was to a non-incumbent one.
- **Comparison with the literature:** the memory-on duplicate rates here (51–66 %) are of the same order as, and at the upper end of, the 28–63 % repeated proposals reported by "Visible but Not Avoided" (arXiv 2610.15738; figure as recorded in PLAN §10, not re-read for this report), but their setting is deterministic — a repeat there returns the identical result — whereas here a repeat is detected on the active configuration of a noisy node, and its logged result is one noisy draw.

## Limitations

- PILOT data: the memory-on source is the PARTIAL rerun-2 arm A (interrupted batch, analysed under the 19 Oct authorisation); DT4 has 6 campaigns per node; liveness campaigns are W = 10. Nothing here is the C1 measurement, which needs the C3 label sweep.
- Duplicate detection is within one campaign and on the node's declared active keys (D25 projection; MLP nodes: every key). It is exact for these deterministic-config replays (0 repeat-metric violations), but a "duplicate" in this sense is not a bit-identical worker run on nodes where the split seed varies.
- No confidence intervals are given; campaigns are the natural cluster for any later interval.
