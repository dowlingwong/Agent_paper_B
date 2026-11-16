# A1 template-check amendment implemented (v16b) — normal Stage A semantics update

Date: 2026-11-04. Code `e996af8` + config binding `96f1146` (`paper_commit=e996af8`), after
the design review (design approval with conditions, `251f18a7…`) and the scoped code review
(ACCEPT with conditions, `90609c9b…`; v16b snapshot `SHA256SUMS` `55770d1b…`, 64 entries /
62 files; subset 408 passed / 1 skipped).

## A1 amendment (applies to normal Stage A runs, not just M1)

The Stage A template check now passes when either
1. the server `/apply-template` render is **byte-equal** to the pinned HF render, or
2. the HF render is the server render prefixed by **exactly one** tokenizer BOS token, and
   `ids(hf) == [bos_id] + ids(served)` **and** the pinned build's own `/tokenize` of the
   served text equals those HF ids.

The rule is applied to the 5 fixed checks **and all 50 frozen prompts**; `template_check_evidence`
records `a1_version=A1`, `byte_equal`, `prefix_token`/`prefix_token_id`, `tokens_equal`,
`server_tokenize`, `method`, lengths. Any other difference remains a `template` failure.
Cold-cache/offload/parse/seed/grammar/lease/D3 are unchanged. The t7h8 Stage A evidence was
measured under the old byte-only code and is **not retroactively changed**; its template rows
stand as recorded. The amendment is scoped to the template check.

## Declared amendment measurement (M1) and B1 eligible-set logic

M1 attempt `r1_stagea_20261104_t7i9` is a **separate, declared** measurement (new dirs,
same host/guardian/preflight/binary/prompts) with
`--only random_valid,scripted,qwen25_coder_7b,gemma4_31b,gemma4_26b_a4b,gemma4_12b,laguna_xs21,olmo31_32b,devstral_small2_24b,ministral3_14b --amendment A1 --amendment-reason "author Option A: A1 amendment measurement of BOS-artifact candidates and declared repairs"`.
Its declaration is recorded in `batch_state.amendment_measurement` (models, reason, build,
prompts, code commit, guardian manifest digest, declared repair SHAs). M1 is **not** spliced
into the t7h8 table and is not Stage A evidence; it requires its own receiving review.

For B1 eligibility (author's decision, with the reviews): the 8 t7h8 PASS candidates +
`random_valid`/`scripted`/`qwen25_coder_7b` anchors remain the Stage A PASS set; the four
BOS-artifact candidates (`gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`, `laguna_xs21`) and the
three repaired models (`olmo31_32b`, `devstral_small2_24b`, `ministral3_14b`) enter only if
their M1 rows pass under A1; `lfm25_24b_a2b`/`muse_glimmer_30b` (genuine grammar),
`gpt_oss_20b`/`rico03_qwen36_27b`/`olmo31_32b_think` (grammar) and `nemotron35_30b_a3b`
(offload) remain excluded. If an M1 row fails (e.g. the olmo repair does not start), it is
excluded and the build-pin diagnostic route applies under policy (c), not a template edit.

## Declared repairs (SHA-pinned, effective from M1, carried with the model)

*Heading changed 4 Nov 2026 by the Mac-local agent per PLAN §10 R1-EXAM-A1-M1-REQUIREMENTS (1) (author, 16:39: "把报告里的"M1-only"改成"M1 起生效，随模型延续""); it read "M1-only". A repaired model that enters B1 through M1 keeps the same SHA-pinned repair template in B1, B2 and every later sweep.*

`olmo31_32b` guarded-`tools` template `5d275f78…` (declared deviation from pinned `49a944c9…`;
byte-equal 5/5 + 50/50 renders, pinned parser generation OK); `devstral_small2_24b` pinned HF
template `a0c0ed8a…`; `ministral3_14b` pinned HF template `2f545122…` (both token-equal
5/5 + 50/50). Registry `template_repair` entries carry schema/file/sha256/original/validation
artifact (`56d06c5b…`)/author declaration/reason; the replay server and qualification probe
share `--chat-template-file`; the launcher pins the template files and registry.

B1/B2, P.3a and B.2 remain STOP; t7h8 evidence and STOP1–8 are untouched; no STOPped batch is
reused.
