# Track X Stage A — template failure map (t7h8) and repair recommendation

Date: 2026-11-04. Diagnostic (not Stage A evidence) on TASL-7: for the nine
template-class models, llama-server `--jinja` `/apply-template` rendering was compared with
the pinned HF tokenizer rendering on the **5 fixed template checks and all 50 frozen
prompts**. Artifact: `~/exam-x/work/r1_template_diff_20261104/render_diff.json`
SHA-256 `c2a9d6c6a7916d36873b463568021b7899789e03f963335f2dfd28dfaeeb32f4` (per-model servers+logs in the same directory; script
`~/exam-x/work/template_render_diff2.py`, venv Python; runbook flock held; no Stage A
evidence produced or modified).

## Findings

1. **BOS-prefix artifact (6 models)** — `gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`,
   `laguna_xs21`, `lfm25_24b_a2b`, `muse_glimmer_30b`: for every fixed and frozen prompt
   the server rendering is **exactly the HF rendering minus the leading special token**
   (`<bos>`, `〈|EOS|〉`, `<|startoftext|>`, `<|begin_of_text|>`). Token-level checks:
   `tokenizer(hf_render, add_special_tokens=False) == [bos_id] + tokenizer(served_render)`
   for gemma4 and lfm25; for laguna/muse the HF tokenizer adds the special token itself and
   the id sequences are equal. So these are **functionally identical prompts**; the Stage A
   byte-equality template check flags them because llama.cpp omits the BOS from
   `/apply-template` output and adds it at tokenization.
2. **GGUF-vs-pinned-template mismatch (2 models)** — `devstral_small2_24b` (server renders
   the minimal `[INST]…[/INST]` form, HF renders the pinned system-prompt template;
   served 79 vs HF 1922 chars) and `ministral3_14b` (served 2517 vs HF 2475; different
   template text). Their embedded GGUF template hash also differs from the pinned HF
   template hash (earlier scan). Genuine template mismatch.
3. **Pinned-build parser generation failure (1 model)** — `olmo31_32b`: with
   `--no-warmup` the server starts and renders **byte-equal on 5/5 fixed and 50/50 frozen
   prompts**; the Stage A failure is llama.cpp 620d222 failing automatic tool-parser
   generation at init for its `tools | tojson` template.
4. **Grammar-only (3)** — `gpt_oss_20b`, `rico03_qwen36_27b`, `olmo31_32b_think`
   (sensitivity): no template repair addresses these.
5. **Grammar + template (2)** — `lfm25_24b_a2b`, `muse_glimmer_30b`: the template part is
   the BOS artifact (1); the `grammar` failure remains a genuine model-level exclusion.
6. **Offload (1)** — `nemotron35_30b_a3b` (32k OOM + 16k retry): fit class, unrelated.

## Consequence

The Stage A receiving verdict accepted the recorded exclusion rows under the author's
template policy. This map shows that **4 candidates previously excluded as `template` are
token-identical at the prompt level** (`gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`,
`laguna_xs21`; `lfm25`/`muse` also have genuine grammar failures and would stay excluded),
and that `olmo31_32b` renders correctly but hits a parser-generation limitation.

## Recommendation (author decision required; no protocol or template change made)

1. **Protocol amendment (reviewed, before B1):** change the Stage A template check from
   byte-equality to **token-sequence equality with explicit BOS handling** (or treat a
   leading-special-token-only difference as equal when the token sequences match). Then
   re-measure the four BOS-artifact candidates in a new, declared measurement (new attempt
   or reviewed amendment run) so their PASS/exclusion status is evidence-backed, not inferred.
   `lfm25`/`muse` keep their grammar exclusion.
2. **Targeted (b) repairs** (each SHA-pinned, declared, independently reviewed, measured in a
   new declared measurement): `olmo31_32b` — guarded-`tools` template that keeps the 5/50
   renders byte-equal and lets llama.cpp generate its parser; `devstral_small2_24b`,
   `ministral3_14b` — serve the pinned HF template via `--chat-template` and validate 5/50
   token-equal renders.
3. **(c) build pin** only if the olmo repair fails: build the candidate commit on TASL-2 and run
   the 22-model parse/render diagnostic screen (no exam evidence) before any re-pin.
4. **B1/B2 remain STOP** until the eligible-candidate set is frozen by the author and the
   template-policy amendment is reviewed; keep the t7h8 evidence and STOP1–8 untouched; do
   not splice amended/repair measurements into the t7h8 table.
