# Stage A prompt-source prerequisite audit

26 October 2026. Read-only preparation audit; no Stage A inference, final prompt selection or freeze performed.

`PORTAL_EXAM_RUNBOOK.md` Phase 3 step 4 requires "50 frozen manager prompts" from "real memory-on ledgers" across at least four nodes, naming rerun-2 and DT4 as sources. The committed source inventory differs:

- `results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/ledgers/roots/` contains memory-on roots for three nodes: `openml_breast_w`, `openml_ionosphere`, `tabular_mlp`.
- DT4 `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/` has twelve roots, all `memory_mode: none`, on digits and ionosphere. These cannot be relabelled as memory-on.
- Existing real LLM liveness collection `results/r1/engineering/liveness_llm_20261014T140742Z/` has two memory-on roots per node, ten trials each, including `digits_mlp`. Manifest pins harness `411c6054c8505f93a6429e2f9eed526952793882`, Ollama 7B, `append_only_summary`, ENGINEERING_ONLY. This is existing source material, not a new inference run.

A local read-only reconstruction audit used original root start files/kept-edit replay, the logged memory text, status, current editable constants and production prompt builder. All tested rerun-2 prefixes and all nine memory-bearing digits prompts (trials 2–10 of the first sorted liveness root) exactly match their original recorded context SHA256. No prompt content was invented to match a hash.

Concrete proposed resolution for author approval: retain memory-on as the filter; use rerun-2 on the three nodes plus the existing digits memory-on liveness source for the fourth. Select fifty prompts by fixed node/root/trial order, before Stage A, with recorded source hashes. Do not use DT4 memory-off rows as memory-on. The exact source exception requires an author response before this final prompt set is frozen or used. The Phase 2 download/build/cache work is independent of this prerequisite.

**Author decision received 26 October:** "Use existing memory-on liveness digits." Recorded in PLAN R1-EXAM-PROMPT-SOURCE and STATUS. Source clarification resolved; no final set has yet been frozen or used.
