# Proposal (for independent review, not yet executed): template-check amendment, amendment measurement, and repair templates

Author decision: **Option A** (4 Nov) — prepare the protocol amendment draft, the targeted
measurement plan and the three repair-template drafts; all go to independent review before
execution. No protocol, template, registry or code change has been made yet.

## 1. Why (evidence)

The post-Stage-A diagnostic (,
SHA-256 `c2a9d6c6a7916d36873b463568021b7899789e03f963335f2dfd28dfaeeb32f4`) showed:

- six `template` rows are a **BOS-prefix artifact**: for `gemma4_31b`, `gemma4_26b_a4b`,
  `gemma4_12b`, `laguna_xs21`, `lfm25_24b_a2b`, `muse_glimmer_30b` the llama-server render is
  the HF render minus its single leading special token, and the token ids are identical
  (`ids(hf) == leading_token + ids(served)`); llama.cpp adds that token at tokenization;
- `olmo31_32b` renders byte-equal (5/5 fixed, 50/50 frozen) with `--no-warmup`; its Stage A
  failure is llama.cpp 620d222 failing tool-parser generation at init;
- `devstral_small2_24b` and `ministral3_14b` genuinely serve a different (GGUF-embedded)
  template than the pinned HF template.

## 2. Proposed protocol amendment A1 (template check)

For each fixed template check message (the frozen 5; optionally all 50 frozen prompts), with
`hf = hf_render(spec, messages)` (pinned template, pinned HF tokenizer) and
`served = server /apply-template(...)` (same messages, `add_generation_prompt`,
`chat_template_kwargs {\"enable_thinking\": mode != \"off\"}`):

- `byte_equal`: `served == hf` (unchanged current criterion);
- `token_equal`: only allowed when `hf = P + served` for a **single leading special token**
  `P` that is the token's own BOS/start token (candidate `P` set: `tokenizer.bos_token`,
  `tokenizer.additional_special_tokens` start markers actually present as the HF render
  prefix), and tokenizing `hf` (add_special_tokens=False) equals
  `[ids(P)] + tokenizing(served, add_special_tokens=False)`;
- check passes iff `byte_equal or token_equal`; any other difference remains `template`
  failure. Per-check evidence records `byte_equal`, `prefix_token`, `tokens_equal`,
  `method` and both heads.
- The runner writes `template_check_evidence` in the Stage A row; the template failure class
  is raised only under the amended rule.

The amendment is scoped to the template check only; cold-cache, offload, parse, seed,
grammar, lease and D3 checks are unchanged.

## 3. Proposed amendment measurement M1 (new, declared, not spliced)

A new, separately identified attempt `r1_stagea_20261104_t7i9` (new out/evidence dirs, same
host TASL-7, same guardian/preflight/M1 procedure, same pinned promptset/binary/models) runs
**only** the seven affected models:

- BOS-artifact re-measure (4): `gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`, `laguna_xs21`;
- repair validation (3): `olmo31_32b`, `devstral_small2_24b`, `ministral3_14b`.

Runner gains an explicit `--only <ids>` subset filter (validated against the registry and
recorded in `batch_state.amendment_measurement` = {id, reason, amendment: A1, models,
build, prompts}); the table is an *amendment-measurement* table, kept separate from the t7h8
Stage A table; B1 eligibility would be decided by the author/reviewer from t7h8 + M1 with
disclosure (no row is copied into t7h8). `lfm25`/`muse` are not re-measured (genuine
`grammar` exclusions); grammar-only and offload rows are unaffected.

## 4. Repair templates (declared, SHA-pinned)

| model | repair | file SHA-256 | validation (this draft) |
|---|---|---|---|
| `olmo31_32b` | guard `tools` (`tools is defined and tools is not none`; `tools is not defined or tools is none or length == 0`) so llama.cpp's parser generation succeeds without changing no-tools rendering | `5d275f78a64ad01740b8b65ff5554e624062229348b4f95c930c45a7db820466` | server **starts** (warmup/parser generation OK); renders **byte-equal 5/5 + 50/50** to pinned HF |
| `devstral_small2_24b` | serve the pinned HF template (`a0c0ed8a…`) via `--chat-template-file` instead of the GGUF-embedded template | `a0c0ed8a45c2c75c85fd756316a10419b90eb4f3dbe64d00f5c0b8ad4de5209a` | server starts; **token-equal 5/5 + 50/50** (BOS-prefix only; byte 0) |
| `ministral3_14b` | serve the pinned HF template (`2f545122…`) via `--chat-template-file` | `2f545122222db8bb43ca0ea0c49e9185320a8670f7d35575b0da0eb48b1e8970` | server starts; **token-equal 5/5 + 50/50** (BOS-prefix only; byte 0) |

Validation artifact: `~/exam-x/work/r1_repair_drafts_20261104/validation/validation.json`
SHA-256 `56d06c5b013e7956fe0f171c0adfc819db0e69fc7a2faf9b045e03c091ffdd08`; per-model servers+logs in the same directory; script
`~/exam-x/work/validate_repairs.py` (venv Python, runbook flock, diagnostics only).
Each repair is declared in PLAN/authorization, pinned in the registry/launcher manifest and
measured in the M1 attempt; the Stage A template check remains against the pinned HF template
(the repaired render must satisfy the amended rule).

## 5. Implementation deltas (to be frozen and reviewed before execution)

1. `r1/exam/stage_a.py`: amended template check + per-check evidence (helper tokenizes with
   the pinned tokenizer; cached per spec).
2. `r1/scripts/exam_runner.py`: `--only` subset filter, `amendment_measurement`
   declaration validation/recording, manifest/config pins.
3. `r1/exam/runtime.py`: per-spec `chat_template_file` (path + SHA-256 from the registry
   repair declaration) appended as `--chat-template-file`; the qualification probe passes
   the same flag; the launcher pins the template files and the registry change.
4. `r1/exam/registry.yaml`: `template_repair` entries for the three models (file, sha,
   declaration) with the template files under `r1/exam/templates/repairs/`.
5. Tests for the amended check (byte, BOS-prefix token-equal, non-prefix mismatch,
   non-special prefix rejection), the subset filter, the runtime/probe template plumbing,
   and the registry/manifest validation.

## 6. Risks / limits

- Token equality depends on tokenizer correctness (the Mistral tokenizer prints a known
  regex warning; the pinned revisions/HF cache are unchanged and were used for both sides).
- Only a **single leading special token** is tolerated, and only when it tokenizes to the
  prefix ids; no other divergence passes.
- Repairs change template delivery only (no weights/no other models); every repaired row is
  measured in M1.
- B1/B2 remain STOP until the author freezes the eligible set; t7h8 evidence and STOP1–8
  reports stay untouched; no STOPped batch is reused.
