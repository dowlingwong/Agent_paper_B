# Track X Stage A — COMPLETE on TASL-7 (attempt r1_stagea_20261103_t7h8)

Date: run 2026-11-03T20:25:49Z → lease released 2026-11-04T12:44:31Z (16 h 18 m), one
continuous guardian lock on TASL-7. Code `3b3283f` (bounded GPU-quiescence wait at the
qualification boundary) + config binding `19b8f33` (`paper_commit=3b3283f`), clean checkout.
Stage A manifest `95bfc8b6…` (187 pinned files); preflight manifest `5f440643…`.

## Outcome

`batch_state.json` COMPLETE, 24 rows = 2 software anchors + 20 candidates + `qwen25_coder_7b`
model anchor + `olmo31_32b_think` sensitivity. The reviewed guardian released the lease only
after its own validated completion: `lease_release.json` `released: true`,
`reason: validated_completion`, `records_verified: 43`, and the completion names **43 server
records** — every `llama_server_*.json` under the run root, including the failed-start
qualification probes. No `STOP.json` was written. After release the guardian exited and the
lock is free (`gpu0.lock` inode 56251186, size 0, nlink 1); GPU idle; 22/22 models verified.

Evidence hashes: `batch_state.json` `ae6adef5…`; `stage_a_table.json` `00ab143d…`;
lease `start.json` `a6f54d3d…`, `lease_inheritance.json` `2e1a90d9…`,
`lease_completion.json` `5836c654…`, `lease_release.json` `415eb713…`; preflight checkpoint
`~/exam-x/work/r1_stagea_preflight_lease_20261103_t7h8/checkpoint.json` (M1: checkpoint
`19b8f33`, code-file hashes, binary `b70f4882…`, prompts `70872a77…`).

## Candidate results (Stage A)

- **PASS (8 candidates)**: `glm47_flash` (p50 0.84 s), `ornith10_35b` (0.85), `ornith10_9b`
  (0.98), `qwen35_9b` (0.98), `qwen36_27b` (3.04), `qwen36_35b_a3b` (0.89), `qwen38_27b`
  (3.09), `qwen3_coder_30b_a3b` (0.63). Anchors `random_valid`, `scripted`,
  `qwen25_coder_7b` PASS (qwen25 p50 0.75 s).
- **`template` failures (7)**: `devstral_small2_24b`, `gemma4_12b`, `gemma4_26b_a4b`,
  `gemma4_31b`, `laguna_xs21`, `ministral3_14b`, `olmo31_32b` (pinned-build parser startup).
- **`grammar` + `template` (2)**: `lfm25_24b_a2b`, `muse_glimmer_30b`.
- **`grammar` only (3)**: `gpt_oss_20b`, `rico03_qwen36_27b`, `olmo31_32b_think`
  (sensitivity).
- **`offload` (1)**: `nemotron35_30b_a3b` — evidenced 32k OOM mechanical-failure row and a
  16k retry that also failed (model does not fit on the 24 GB card at either context).
- Every replay `servers/*/exam_offload.json`: `full: true`, `route: log_line`, no CPU
  fallback (20 replay servers: `nemotron` and `olmo31_32b` failed at qualification and have
  no replay record).
- Thinking policy held: always-on models ran with the 2,048-token budget; the switchable ones
  ran thinking-off primary rows.

## Fixes validated live in this run

- STOP-6 real-shape OOM classification: evidenced 32k OOM row + 16k retry.
- STOP-7 failed-start lease proof: both failed starts (`olmo31_32b`, nemotron 32k/16k) carry
  `lease_inheritance` (SAME-OFD, `kcmp_same_ofd: true`), `stopped_utc`, `returncode`; the
  guardian's final validation accepted all 43 records and released the lease.
- STOP-8 bounded GPU-quiescence wait: the 16k retry proceeded after the 32k teardown without a
  spurious "GPU not available" STOP.

## International review: Stage A receiving verdict

Independent receiving review (`docs/r1/reviews/TRACKX_STAGEA_RECEIVING_T7H8_20261104.md`,
SHA-256 `141c1dd3…`): **ACCEPT (with conditions)**. The reviewer independently verified the
release (43/43 records covered, 0 uncovered/extra, 0 digest mismatches, 0 survivors; three
failed-start probes carry the SAME-OFD proof), the batch/table hashes, the manifest/M1
evidence, the candidate outcomes and the STOP-6/7/8 validations, and classified **`t7h8` as
the Stage A evidence set** (t7c3/t7d4/t7e5/t7g7 were STOPped; t7f6's batch is COMPLETE but
its completion validation STOPped, so it is engineering evidence only with no validated
release; none reused).

Conditions: (a) produce the template failure map + 5/50-prompt render-diff analysis (targeted
byte-equal repairs and any build-pin remain separate author decisions; no template/build
change is authorized by the review); (b) B1/B2 remain STOP (also P.3a/B.2) and B1 needs the
author's separate authorization, the eligible-candidate set and the template-policy decision;
(c) retain the t7h8 evidence and STOP1–8 reports, no STOPped-batch reuse/relabel; (d) record
the environment/M3 with this report; (e) keep the completion report on the coordinator docs
branch and the template policy in PLAN.

## Environment / M3

- Runner argv (from `lease/start.json`): `/home/dowling/exam-x/work/venv/bin/python
  /home/dowling/exam-x/work/agent_paper_B/r1/scripts/exam_runner.py stage-a --config
  …/r1/scripts/configs/exam_portal.json --out …/r1_stagea_20261103_t7h8`.
- Batch `template_reference_versions`: transformers `5.20.2`, jinja2 `3.1.6`, tokenizers
  `0.23.3` (the versions used for the pinned-template render checks).
- Manifest pins (M1 checkpoint): binary `b70f4882…`, prompts `70872a77…`, code-file hashes
  incl. v15 `exam_runner eeec5e9a…` and v14b `llama_server_instance b697fc44…`.
- HF cache on TASL-7 `~/exam-x/work/hf` (model/tokenizer artifacts for the pinned revisions);
  venv `/home/dowling/exam-x/work/venv` (Python 3.13.4); 22/22 GGUF verified.

## Next (per the author's decisions)

1. Independent **Stage A receiving review** (request sent with the evidence above).
2. **Template failure map** + per-model render-diff evidence (frozen 5 prompts and all 50
   frozen prompts; llama.cpp `--jinja` vs pinned HF rendering), to decide targeted
   byte-equal repairs (priority `olmo31_32b` → `gemma4_31b`) or build-pin diagnostics.
3. B1/B2, P.3a and B.2 remain STOP; no STOPped batch is used as evidence.
