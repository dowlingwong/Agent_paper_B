# Track P Unit B on TASL-7 with D2 — RESULT (19 November 2026)

**Status: COMPLETE (rc 0), one GPU session, one host (TASL-7).** Authority: `R1-TRACKP-D2` (main
`de3de54f`), `R1-TRACKP-UNITB` (now naming D2 in place of D), `R1-TRACKP-TASL2-HOST` (TASL-2 fallback
only; not used). Code: D2 `8309b69e81837fb9719fa01b28f0dde94975e4f9` detached on TASL-7, from C2''
`9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e` (review round 3 `ACCEPTED`, 0 BLOCKING/MAJOR, 3 MINOR
documentation-only; review records in `docs/r1/reviews/TRACKP_P3A_D2_CODE_REVIEW*_20261119.md`), runner blob
sha `d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750`, child `5679ce1b…`. D2's host
profile is TASL-7 (`580.178.04`), the attempt-1 host; boot-id equality is replaced by artifact verification
(the attempt-1 boot id is recorded, current `713ca10b…`, `boot_id_required: false`).

## Run

- Root: `/home/dowling/r1_trackp/runs/p3a_attempt2_20261119T011430Z` (TASL-7; 188 K; 528 G free),
  journal 8 events: campaign_start → marker_begin rc0 → DRYRUN unit_start/complete → EVIDENCE
  unit_start/complete → marker_end rc0 → **complete**.
- Command (detached D2, frozen venv): `trackp_p3a_guarded.py --root … --probes-only --base
  qwen3.5-4b-base --attempt1-root /home/dowling/r1_trackp/runs/p3a_operator_20261027 --a3-short
  --authorization-amend-sha256 cd867e95…`; harness `897d83c8…` clean; frozen venv `trackp-gpu` freeze
  sha `50238e5a…` (121 lines); config `049bafed…`; no STOP.
- **Preflight artifact verification (real host):** journal sha `1e73e80f…` (81 events), the four
  `EVIDENCE/<base>/final/manifest.json` + every listed saved/model file re-hashed, archive
  `p3a_attempt1_final_saved_20261117T0015Z.tar.gz` sha `fa2437ee…` (328,136,435 B), attempt-1 lease log
  sha `69505091…` (111 lines; TASL-7 global path); current boot id recorded/disclosed
  (`713ca10b-ec21-413c-b61f-30da4a7b1e96`), attempt-1 boot `2c9bb104…` recorded, `boot_id_matches_attempt1:
  false`, `boot_id_required: false`; driver snapshot `580.178.04` (kernel+packages) in `pins.driver`.
- **GPU accounting:** DRYRUN kev-0.8b n=8: 17.7276 GPU-s, A3 `pass: true` (`v2_budget`), A4 pass true,
  A3_descriptive skipped marker `R1-P3A-OOM-OPTION3`; EVIDENCE qwen3.5-4b-base n=100: 162.2841 GPU-s, A3
  `pass: true`, A4 pass true, A3_descriptive skipped. Campaign total **130,925.3907 GPU-s = 36.368 h**
  (attempt-1 130,745.3790 + 180.0117 new lease; remaining 8.632 h to the 45 h STOP / 60 h cap);
  `gpu_seconds_total` and budget in the journal complete event.
- Marker begin/end rc0; the **TASL-7 global** lease log (`/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl`)
  grew 111 → 117 lines (six attempt-2 entries), while the captured **run-root** `gpu_lease_log.jsonl` has 4
  lines and the attempt-1 snapshot has 111 lines; GPU 43 MiB / 0 % after; no leftover process. The
  only extra file is the operator log dir `runs/p3a_attempt2_20261119T011430Z.parent/` (bash `${ROOT}.parent`
  mistake; kept, not deleted).
- Captures: `reports/trackp_unitb_tasl7_d2_20261119T011430Z/` (journal, DRYRUN/EVIDENCE reports,
  manifests, runner manifests, attempt-1 provenance snapshot, lease log, operator log, SHA256SUMS).

## Scope statement

This is Unit B's probes-only EVIDENCE unit on its attempt-1 host; one host per table (TASL-7). The D2
TASL-2 fallback is implemented and CPU-tested but **not** used here. No evidence run outside Unit B,
no noise floor/D21/D28, no deletion, no force push, no HTCondor/deepthought.
