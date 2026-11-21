# Draft release rows of the sweep-2 analysis preregistration §8 (PRE-STAGE A) — approved: false

Drafted by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §8. **Not author decisions.** Each row,
once the placeholders are filled and it is added to a dated author table of PLAN §10, is what `r1/c3/release.py`
(`release_row`) requires before it writes or opens a partition; the text must match exactly
(`release.row_pattern`). The placeholders:

- `<PREREG_SHA256_AT_FREEZE>`: sha256 of the committed preregistration after the coordinating chat sets `frozen: true`
  (with `split_file` naming `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569` and `gate_input_builder_sha256` the reviewed builder's sha256). The release step
  refuses an unfrozen preregistration.
- `<RELEASE_CODE_COMMIT>`: the published commit whose `r1/c3/release.py` is the reviewed release step (it must be an
  ancestor of the running checkout with the same bytes).
- `<ARMS_FROZEN_RECORD_PATH>`, `<ARMS_FROZEN_RECORD_SHA256>` (test rows only): the committed arms-frozen record (§4
  step 4); the release step checks its bytes.

The P3 split-file sha256 is filled in: `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`.

## T0 (both sources: sweep 1 and sweep 2)

| ID | Decision |
|---|---|
| R1-S2-LABELS-TRAINDEV-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`): the train and dev label blocks of both sources (sweep 1 and sweep 2), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. No test label and no evaluation value is released by this row. |
| R1-S2-LABELS-TEST-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`), after the arms-frozen record `<ARMS_FROZEN_RECORD_PATH>` (sha256 `<ARMS_FROZEN_RECORD_SHA256>`): the test label blocks and every evaluation block of both sources (sweep 1 and sweep 2), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. |

## T1 (the G.5 tables; for the G.5 note, citing this preregistration)

| ID | Decision |
|---|---|
| R1-T1-LABELS-UNSEAL | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`): the train and dev label blocks of the G.5 T1 tables, partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. No test label and no evaluation value is released by this row. |
| R1-T1-LABELS-TEST-RELEASE | Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `<PREREG_SHA256_AT_FREEZE>`), after the arms-frozen record `<ARMS_FROZEN_RECORD_PATH>` (sha256 `<ARMS_FROZEN_RECORD_SHA256>`): the test label blocks and every evaluation block of the G.5 T1 tables, partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `<RELEASE_CODE_COMMIT>`. |

## What each row lets the release step do

- **Train/dev rows** (R1-S2-LABELS-TRAINDEV-RELEASE, R1-T1-LABELS-UNSEAL): write `label_block.traindev.jsonl` (the label rows
  of P3 train and dev instances, byte-identical lines) and its receipt, after the source's integrity check passes. No
  test label and no evaluation value leaves the release step; the evaluation block is opened only by the integrity
  check, which returns pass/fail, counts and hashes (§6 carve-out).
- **Test rows** (R1-S2-LABELS-TEST-RELEASE, R1-T1-LABELS-TEST-RELEASE): after the arms-frozen record, write
  `label_block.test.jsonl` and `evaluation_block.all.jsonl` and their receipt; from then on the raw-block locks of the
  tier open (`release.test_released`).

## Before the rows can be used (conditions, not decisions)

- A reviewed integrity check per source is registered in `release.INTEGRITY_CHECKS`. Today only `sweep1` (the sweep-1
  B.2 audit, `audit.verify_evidence_completion`) is registered. Sweep 2 and the G.5 tables have no labelled audit yet
  (sweep 2's B.2 needs its own authorization, R1-SWEEP2-SETTINGS (2)); their release STOPs until their check is
  reviewed and registered.
- The release step runs where the audit outputs live (the cluster), on a clean checkout of a published commit that
  contains the rows.
