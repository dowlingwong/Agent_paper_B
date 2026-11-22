# PRE-STAGE A train/dev label release — sweep 2 PASS, sweep 1 refused (22 November 2026)

**No test label and no evaluation value was released.** This report records only receipt hashes and counts; the
train/dev label file was not opened beyond the receipt counts.

Authority: published main with R1-S2-LABELS-TRAINDEV-RELEASE (signed 21 Nov; release code `a9d8ff5e…`) and
R1-SWEEP2-LABELS-FREEZE; release row covers both sources. Run from `/work/dwong/s2_audit_20261122/paper`, a
tracked-clean checkout at published main (the audit/batch outputs remain untracked and unchanged), with
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`.

## Sweep 2 — SUCCESS

Command: `python -B -m r1.c3.release --stage traindev --source sweep2 --table <audit-checkout table> --audit
<C3_audit_EVIDENCE_20261122T164726Z> --out <release root> --paper-root <audit checkout at main> --index
<C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json>`.

Receipt (copied here as `RECEIPT_sweep2_traindev.json`, sha256
`d2747771fd043ea0f087285ed2b42583deaec799e16130b96ea834faa6effb7c`):
- row `R1-S2-LABELS-TRAINDEV-RELEASE`; source `sweep2`; stage `traindev`; tier T0; schema
  `r1_c3_release_receipt/v2`; integrity **pass true**.
- prereg `aa1a961b…`; split `b5967dd7…`; release commit `a9d8ff5e…`; published `38ae4a05…`.
- counts: label rows **train 850, dev 422, test 1228**; **released_label_rows 1,272**; **evaluation_rows 0**;
  label kinds train/dev/test all `audit`.
- output `label_block.traindev.jsonl` sha256 `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82`.
- completion `/4`: label block `9ab3cb26…`, evaluation block `1e3a0e7a…`, runs `cf57bf7e…`, plan `4479b1dd…`,
  build `bbb2a95c…`, proposals `379b17ca…`, configs `de6d63b5…`, extract `82c760…`, index `b4697c…`.

**Release-step refusals before the successful run (disclosed; no check was bypassed).** Attempts with a table
rebuilt in a *different* paper-root failed closed (`BatchError`: index not under that root; then `ValueError`:
completion/build mismatch). The successful run used the original audit table and index in the audit checkout itself,
brought to published main (tracked clean; untracked outputs unchanged); `release.py` and all checks were unmodified.

## Sweep 1 — REFUSED (reported, not worked around)

Command with source `sweep1`, table `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table`, audit
`…/output`, index `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, classification
`results/r1/evidence/C3_sweep_classification_20261028.json`.

Result: `ReleaseStop: STOP: integrity check failed for sweep1 (ValueError)`; the underlying integrity check failed in
`r1.c3.audit._verify_replay` with `evidence table differs from full source replay: proposals.jsonl`. **No output or
receipt was written** (`release_sweep1_traindev` absent). The refusal was not bypassed; the sweep-1 table/release
remains for the author to resolve (a genuine table-vs-current-source replay mismatch).

## Files / status

- Sweep-2 release tree: `/work/dwong/s2_release_20261122/release_sweep2_traindev/sweep2/traindev/` (receipt + output
  only; no evaluation/train/test label file beyond the 1,272-train/dev release).
- Independent review: `docs/r1/reviews/RELEASE_TRAINDEV_20261122_REVIEW.md` (pending at commit time; will be added
  after review).
- Labels: test labels and all evaluation values remain sealed; no U4/U5 or training started; I2 759919 still waits
  unchanged.
