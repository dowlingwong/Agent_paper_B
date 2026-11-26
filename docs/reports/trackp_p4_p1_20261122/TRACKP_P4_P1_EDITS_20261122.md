# Track P P.4 phase 1: the draft edits of R1-TRACKP-P4-DECISIONS (revision 4.2)

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, on `mac-trackp-p4-p1-20261121`. The branch is the
reviewed draft line `mac-trackp-p4-h200-20261121` @ `3eeccf9a` (revision 4.1, accepted at `3b65dfec`) merged with
published `main` `adeccc29`. This is item 4 of the queue of 21 Nov 2026 (22:44). It is desk work: no host was used
and no label file was opened.

## What changed

**`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` (revision 4.2).** The edits follow the
decision list `TRACKP_P4_PHASE1_DECISIONS_20261121.md` on `main` and R1-TRACKP-P4-DECISIONS (all eight decisions as
recommended).
- §1: the base is now published `main` `adeccc29`. New rows:
  - R1-SWEEP2-PREREG (PRE-SPLIT A and PRE-STAGE A; prereg sha256 `aa1a961b…`, split file `b5967dd7…`);
  - R1-S2-LABELS-TRAINDEV-RELEASE;
  - R1-TRACKP-P4-DECISIONS;
  - R1-TRACKP-IMAGE-V21: P.4 runs in image v2.1. The v2 smoke failed `kernels_bound`.

  "What exists now" is updated for the I2/I3 v2 results, the failed v2 smoke and v2.1, the micro-batch change, and
  the P3 and release locks now on `main`.
- §2: each decision is marked decided.
  - P4-P1SPLIT: the A text is rewritten as "the P3 split file is the assignment (`split_file`)". The salt-mode wording
    ("salt `c3_p3_split/v1` … over the fixed universe") is dropped. B is marked not buildable on real labels.
  - New P4-LABELS section, with A, the receipted sweep-1 train/dev partition, decided.
  - P4-MB 8, P4-LC "250, 500 and full".
  - P4-CAP arithmetic under P3: ≈ 0.83 h per 0.8B base; training ≈ 9.9 GPU-h (4B = 5 × 0.8B) or ≈ 14.9 GPU-h (8 ×);
    with startup and probe ≈ 14 to ≈ 19 GPU-h. A repeated 4B job (≈ 6.6 GPU-h at 8 ×) fits the 40 GPU-h cap.
- §3: the data line names the receipted partition and the split file.
- §4: a new STOP for a label source that is not the receipted sweep-1 train/dev partition, whether the raw block, a
  partition without a valid receipt, another source or stage, or a different sha256. The split STOP names the split
  file. The image STOP names v2.1.
- §7:
  - P1 gains the train/dev release receipt.
  - P3 binds `split_file` and `LabelBlockSource` on the receipted partition.
  - P5: image v2.1 (diagnostic job, I2/I3 rerun, smoke and E0 rerun unchanged, then the probe at micro-batch 8).
  - P6 and P8 read PASS.
- §8 key values: `labels:` points to the partition, with `label_receipt:`, and `source_label_block:` is read only by
  the release step. The split, `split_file`, arms, learning curve, micro-batch, job layout and test read are filled
  per the decisions. `image:` and `versions_sha256:` now point to v2.1, still to be filled with its digest. The cap
  line now carries the projection.
- §10: the cluster tests now name image v2.1.

**`r1/scripts/configs/trackp_htcondor_v2.json`.** `sft.micro_batch` 16 → 8, with a comment citing P4-MB A. This
changes the host-config sha256 that the note records.

## Not changed

- The protocol, the evaluator (`sft_test_eval.py`) and §9.
- No desk-time code path reads the host config's micro-batch. At run time `trackp.py sft-dev` reads `sft.micro_batch`
  from its `--config` file, so the SFT probe and the P.4 runner unit (P3) use the new value.
- The test `test_htcondor_config_runs_the_qtorch_checks_and_skips_the_portal_schedule` does not pin the micro-batch.

## Before signature

The prerequisites of §7 are still open:
- P1: the sweep-1 label freeze and the train/dev release receipt;
- P2: the per-base P.3a records;
- P3: the P.4 runner unit;
- P5: the cluster's image v2.1, its H200 smoke and E0, and the SFT probe;
- P7: the config check.

The placeholders in §8 are filled from those records.

## Round-1 revisions (review of 22 Nov)

- **M1.** The freeze STOP now applies to the receipt's source block. The label-source STOP separates what
  `LabelBlockSource` refuses from what the job must check: the note's `labels:` and `label_receipt:` sha256 values
  and the frozen source block. P1 and P3 carry these pins.
- **M2.** The merge with `main` brought in the release lock and the P3 gate. As a result, three of the 48 evaluator
  tests failed. `r1/tests/test_trackp_sft_test_eval.py` now uses the same two fixtures as `test_trackp_sft.py`.
  `test_trackp_sft_test_eval.py` and `test_trackp_sft.py` pass together: 83 tests (48 + 35).
- **Minors 1–11.**
  - Decided wording replaces the stale proposed/recommended text.
  - The identity STOP names the receipted partition and the receipt.
  - The release command is given in full.
  - The job needs a full clone with `origin/main` fetched.
  - The host config's v2 image fields are listed for update in P7.
  - R1-TRACKP-IMAGE-V21 is carried in full: the diagnosis STOP, no other dependency change, the wheel question.
  - E0 runs on v2.1 for the first time.
  - P8 cites `e5e452a0`.
  - The universe is now the split file's instances of the table's nodes.
  - §1 now cites R1-SWEEP2-RELEASE-DECISIONS and notes that the receipt rule holds until the test row.
  - This report's wording on the micro-batch reader is corrected.
