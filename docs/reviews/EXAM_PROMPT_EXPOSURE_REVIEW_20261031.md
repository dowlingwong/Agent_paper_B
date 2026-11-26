# Independent review: recovered Track X prompt exposure

31 October 2026. Read-only investigation. No model invocation, upload, freeze, or modification of source records. This review contains no prompt text.

## Verdict

**STOP; author interpretation required.** The retained historical rerun-2 records establish that 21 of the 50 recovered prompt contexts were used in later manager calls in historical continue and verify branches. The historical source manager is `ollama/qwen2.5-coder:7b`, explicitly permitted by the author as a source-manager exception, but PLAN `R1-EXAM-PROMPT-HISTORICAL-ANCHOR` separately says that subsequent evaluation must not have used the prompts. Whether these historical branches fall within the permitted historical source exposure or the separately prohibited subsequent evaluations is an author decision; this review does not resolve that ambiguity. If the prohibition includes these branches, the condition fails.

**NOT CHECKABLE — other exam-candidate exposure.** The available checks do not establish that no other candidate or subsequent unlogged evaluation used any context. A missing retained result is not proof of non-execution. **NOT CHECKABLE — global selection independence.** The recovered selection code uses fixed node quotas and ordering by root seed and budget index rather than output fields, but available records cannot establish that the human selection process was uninfluenced by other exam outputs.

## Authority and data

- `/private/tmp/paper-b-coordinator-20261031/docs/r1/PLAN.md`, lines 650 and 661: freeze gate and historical-anchor clarification.
- `/Users/wongdowling/Documents/agent_paper_B_ops/trackx-prompt-recovery-20261031/candidate_bundle_UNFROZEN/prompts.jsonl`: 50 rows, SHA-256 `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`. Each prompt's SHA-256 was compared with retained `extra.manager.context_sha256` values, then source-root and branch call metadata were compared.
- `/Users/wongdowling/Documents/agent_paper_B_ops/trackx-prompt-recovery-20261031/candidate_bundle_UNFROZEN/source_map.json` binds derivative source ledgers to original historical roots. The historical campaign manifest is `/Users/wongdowling/Documents/agent_paper_B/results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/manifest.json`.
- Branch comparison covers local `results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/ledgers/branches/**/branch_trials.jsonl.gz`. The source comparison uses the candidate bundle's five derivative ledgers. The 50 unique context digests were derived from the recovered prompts.

## Matched later calls

For a matching branch record to count below, its context digest had to match a recovered prompt, its raw response SHA-256 or call seed had to differ from its source-root record, its `timestamp_start` had to be strictly later than source-root `timestamp_start`, and `llm_call.completion_tokens` had to be positive. All 62 changed-call records satisfied both the timestamp and completion conditions. The tuple `(context SHA, seed, raw response SHA, timestamp_start)` was distinct for every one of the 62; proposal IDs alone are not unique call identifiers. Context counts are deduplicated across branches.

| Node | Distinct recovered contexts | Continue records | Verify records |
|---|---:|---:|---:|
| openml_breast_w | 8 | 12 | 11 |
| openml_ionosphere | 7 | 10 | 11 |
| tabular_mlp | 6 | 10 | 8 |
| Total | 21 of 50 | 32 | 30 |

Per-role unique context counts: breast 8 continue and 8 verify; ionosphere 7 and 7; tabular 6 and 5. There were also 252 context-matching branch records whose seed and raw response SHA were equal to the source root; these were not counted as new calls on that basis. Some branch ledgers retain inherited root records. Equality on these two fields alone does not prove every such record is a copy.

## Reproducible example

Recovered row `tabular_mlp__s102-trial-009` has prompt SHA-256 `a22a2b5ce565e9b6caa9c27c4990636820c804d9e31f3c429451910a96164186`.

- Source root: `/Users/wongdowling/Documents/agent_paper_B/results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/ledgers/roots/tabular_mlp__s102/root_trials.jsonl.gz`, matching derivative `candidate_bundle_UNFROZEN/ledgers/tabular_mlp__s102.jsonl`. Start `2026-10-14T14:11:23Z`, seed `2612997041`, completion tokens `96`, raw response SHA-256 `fcb625aa531e8b21990a4d199c40f49b9ffb5a61f23a9d7436266434fab7d3a2`.
- Later verify branch: `/Users/wongdowling/Documents/agent_paper_B/results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/ledgers/branches/tabular_mlp__s102__b008__verify__r2/branch_trials.jsonl.gz`. Start `2026-10-14T14:29:14Z`, seed `1596242317`, completion tokens `100`, raw response SHA-256 `f3848d231f88940d6e97920c5185ec3cbce79f23f6c74abc254162b7b4c3f107`. Its manager context SHA is identical to the recovered prompt and root. Both records reuse `proposal-85888226cea09459`, demonstrating why proposal ID alone does not establish call identity.

## Bounded search and limits

Read-only portal inventory covered `/home/dowling/exam-x` and a scan of JSONL and JSONL.gz files no larger than 100 MB under `/home/dowling/exam-x/work/agent_paper_B/results`, extracting retained context SHA and trial identifiers for comparison. The result tree includes source and branch records; matching trial IDs alone are not evidence of the same call. The October 28 local historical coordinator session and local Git history were inspected for preparation and selection context. Portal inventory and this bounded log scan do not cover other hosts, omitted or deleted records, ad hoc calls, non-JSONL logs, or missing prompt hashes. They cannot prove all calls were logged. The branch counts above come from the retained local rerun-2 branch files, not a claim about every host or every later evaluation.

The source campaign stopped partially and its artifacts must retain their existing historical labels. This review does not approve a freeze, change the prompt bytes, or authorize Stage A.
