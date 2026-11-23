# Sweep-1 PRE-STAGE A train/dev release — PASS (23 November 2026)

**No test label and no evaluation value was released.** Only receipt hashes and counts are recorded.

Authority: published main **`3522e59b`** (R1-SWEEP1-RELEASE-COMPAT + SCOPE, R1-S2-LABELS-TRAINDEV-RELEASE, release
code `a9d8ff5e…`, R1-SWEEP2-LABELS-TRAINDEV-RELEASE). Run on deepthought from the audit checkout at
`3522e59b` (tracked clean; audit/batch outputs untracked and unchanged), interpreter
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`.

## Command (same sealed inputs as the refused attempt; new out directory)

```
python -B -m r1.c3.release --stage traindev --source sweep1 \
  --table /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table \
  --audit /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/output \
  --out /work/dwong/s2_release_20261123/release_sweep1_traindev \
  --paper-root /work/dwong/s2_audit_20261122/paper \
  --index /work/dwong/s2_audit_20261122/paper/results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
  --classification /work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep_classification_20261028.json
```

## Result

- **PASS**, release step wrote the receipt; no refusal, nothing worked around.
- Receipt (copied here as `RECEIPT_sweep1_traindev.json`, sha256
  **`f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1`**):
  - row `R1-S2-LABELS-TRAINDEV-RELEASE`; source `sweep1`; stage `traindev`; tier T0; schema
    `r1_c3_release_receipt/v2`; **integrity pass true**.
  - published **`3522e59b`**; release commit `a9d8ff5e…`; prereg/split as bound by the release row.
  - counts from the receipt only: label rows **train 593, dev 276, test 856**;
    **released_label_rows 869**; **evaluation_rows 0**; all label kinds `audit`.
  - output `label_block.traindev.jsonl` sha256
    **`6a6327a3731dc2d874822e009f3b2d84fbf1a6cbabfef505c657f90b14fd7b2a`**.
- The release step's integrity check replayed the sealed table with the v2 builder at `ab79b4ce` (compat path) and
  verified classification/index sha256; the sealed table/audit were not modified. The train/dev output is train+dev
  only (869 rows); no test-label or evaluation file was written.
- Validated by the v2/builder compat unit merged as R1-SWEEP1-RELEASE-COMPAT; no new release failure.

## Status

- Sweep-1 train/dev release: **delivered**; combined with the earlier sweep-2 receipt
  (`de95b218…`, train 850/dev 422, released 1,272) both sources' train/dev partitions now exist.
- Independent review of this receipt: pending on the report branch; labels/evaluation stay sealed. No U4/U5 or
  P.4 training was started by this release.
