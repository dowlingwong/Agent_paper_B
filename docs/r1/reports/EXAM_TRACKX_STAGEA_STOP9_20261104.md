# Track X Stage A amendment measurement — STOP 9 (A1 non-generation journal coverage)

Date: 2026-11-04 ~14:07 UTC. Attempt `r1_stagea_20261104_t7i9` (declared M1 amendment
measurement, TASL-7, new dirs, manifest `f91ace2f…`, real lock 14:02:34Z).

## What happened

Two software anchors completed; the first real model `qwen25_coder_7b` stage-a worker
STOPped with `ValueError: STOP: D3 local journal non-generation request/check coverage
incomplete` (`cache_order.py`). The A1 amendment added the 50 frozen `/apply-template`
checks (plus `/tokenize` fallbacks for BOS-prefix checks), but `cache_order` still required
the legacy 6-row non-generation whitelist (1 prefill `/tokenize` + 5 fixed template checks).
This is an A1 integration defect, not a model/lease/offload issue. **No M1 Stage A evidence
exists** (2 anchors only, table absent, lease STOP.json retained); t7i9 is not reused.

## Recovery

Under the author's standing authorization the preserved `qwen25_coder_7b` server (pid
377926) and the guardian (pid 376576) were ended; LOCK-FREE (inode 56251186, size 0,
nlink 1), GPU idle. Evidence `~/exam-x/work/r1_stop9_shutdown_20261104T142243Z/`.

## Fix (independently reviewed: v17 + v17b)

- `stage_a.py` records the exact expected non-generation rows (`nongen_expected`) for the
  5 fixed and 50 frozen A1 checks; the `/tokenize` fallback row is expected only when A1
  actually attempted the endpoint (`fallback_tokenize_row` gate).
- `cache_order.py` validates the declared rows with the unchanged canonical route+body
  equality, coverage count, sequence and cross-journal ordering; the legacy `None` path
  keeps the 6-row whitelist (non-A1 runs unchanged).
- Committed `ab74203` (config binding `74a0790`, `paper_commit=ab74203`); reviews
  `docs/r1/reviews/TRACKX_STAGEA_STOP9_NONGEN_REVIEW_20261104.md` (ACCEPT with conditions;
  v17 `2d86425d…`) and the v17b gating fix (snapshot `4fef681e…`, 410 passed/1 skipped).

## Relaunch

Fresh TASL-7 real-lock preflight passed (manifest `2a8fa22b…`; checkpoint recorded with
code `74a0790`, binary/prompts pins). The declared M1 measurement was relaunched as the
**new attempt `r1_stagea_20261104_t7j10`** at 14:28:22Z (manifest `64a2712c…`,
`amendment_measurement` = A1 / 10 models / code `ab74203` / manifest digest / repair SHAs),
same host, reviewed guardian (pid 386549) holding the real `gpu0.lock`, same `--only
random_valid,scripted,qwen25_coder_7b,gemma4_31b,gemma4_26b_a4b,gemma4_12b,laguna_xs21,olmo31_32b,devstral_small2_24b,ministral3_14b --amendment A1` declaration. Its result requires
the M1 receiving review before any B1 eligibility decision.

B1/B2, P.3a and B.2 remain STOP; t7h8 evidence and STOP1–8 untouched; no STOPped batch reused.
