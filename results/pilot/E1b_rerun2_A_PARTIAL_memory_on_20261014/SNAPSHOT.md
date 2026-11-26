# Partial memory-on snapshot — 19 Oct 2026

AI-assisted by Codex. PILOT, PARTIAL, not evidence.

Authorised by PLAN section 10 on 19 Oct. Interrupted arm; collection gate never passed. Never resumed, retried or completed.

Source outputs: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z`.
Source ledgers and frozen incumbent anchors: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/r1_e1b_rerun2_A_work`.
Raw copied source hashes (including decompressed ledgers): `sha256_manifest.txt`.
Stored file hashes: `stored_sha256_manifest.txt`.
All copied source bytes were hashed before copying and checked again afterward; gzip round-trips verified.

## Deviations from the prompt

Raw trial ledgers alone total 51,833,959 bytes, exceeding 40 MB even with events omitted. All ledgers are therefore stored losslessly as `.jsonl.gz`; event extracts are omitted. Memory text and llm_call seed/latency are already in trial extra.manager. memory_context_built events themselves contain metadata, not text. Small frozen snapshot manifests/incumbents are also copied to retain the existing replay anchor check; no node/, art/, .venv or checkouts are copied. Original JSON and decompressed JSONL bytes are unchanged. This layout has no points.json; points are derived from leaf metadata and manifest noise.

## Failed leaves

- `openml_breast_w__s235__b004__continue__r1`
- `openml_breast_w__s235__b004__continue__r2`
- `openml_breast_w__s235__b004__verify__r1`
- `openml_breast_w__s235__b004__verify__r2`
- `openml_ionosphere__s123__b008__continue__r1`
- `openml_ionosphere__s123__b008__continue__r2`
- `openml_ionosphere__s123__b008__verify__r2`
