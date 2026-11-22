# PRE-STAGE A train/dev label release — sweep 2 PASS (re-issued), sweep 1 refused (22 November 2026)

**No test label and no evaluation value was released.** This report records only receipt hashes and counts; the
train/dev label file was not opened beyond the receipt counts.

## Authority repair (disclosed)

The first sweep-2 release receipt (`RECEIPT_sweep2_traindev.json`, sha256
`d2747771fd043ea0f087285ed2b42583deaec799e16130b96ea834faa6effb7c`) was produced against main `38ae4a05`, but an
independent review found that the stale-PLAN T1-erratum merge `4b7452b6` had deleted three 22 Nov author PLAN
subsections from published main: **R1-G1B-AR-PY, R1-SWEEP2-B2-RETRY and R1-SWEEP2-LABELS-FREEZE**. The label-table
freeze is named in the B.2 addendum as a condition for the labels counting, so that receipt is **quarantined and not
used** (kept only as an audit record; its output has the same bytes as the re-issued one). The three subsections were
restored verbatim from `26532dd6:docs/r1/PLAN.md` on branch `fix-plan-freeze-20261122` @ `f93264fc` and published to
main; `R1-SWEEP2-LABELS-FREEZE` is present at the receipt's published commit below.

Authority: repaired published main `f93264fc` with R1-S2-LABELS-TRAINDEV-RELEASE (signed 21 Nov; release code
`a9d8ff5e…`), R1-SWEEP2-B2-RETRY and R1-SWEEP2-LABELS-FREEZE. Run from `/work/dwong/s2_audit_20261122/paper`, a
tracked-clean checkout at that main (audit/batch outputs untracked and unchanged), interpreter
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`, `AR_HARNESS_ROOT` the audited harness, `PATH=<venv>/bin`,
`PYTHONDONTWRITEBYTECODE=1`, `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`.

## Sweep 2 — SUCCESS (re-issued receipt)

Exact command:

```
python -B -m r1.c3.release --stage traindev --source sweep2 \
  --table /work/dwong/s2_audit_20261122/table \
  --audit /work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_audit_EVIDENCE_20261122T164726Z \
  --out /work/dwong/s2_release_20261122/release_sweep2_traindev_v2 \
  --paper-root /work/dwong/s2_audit_20261122/paper \
  --index /work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json
```

Receipt (copied here as `RECEIPT_sweep2_traindev_v2.json`, sha256
`de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c`):
- row `R1-S2-LABELS-TRAINDEV-RELEASE`; source `sweep2`; stage `traindev`; tier T0; schema
  `r1_c3_release_receipt/v2`; **integrity pass true**.
- prereg `aa1a961b…`; split `b5967dd7…`; release commit `a9d8ff5e…`; **published `f93264fc`** (freeze row present).
- counts: label rows **train 850, dev 422, test 1228**; **released_label_rows 1,272**; **evaluation_rows 0**;
  label kinds all `audit`. (test 1,228 is the P3 partition count; no test label is in the release file.)
- output `label_block.traindev.jsonl` sha256 `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82`.
- integrity completion `/4`: label block `9ab3cb26…`, evaluation block `1e3a0e7a…`, plan `4479b1dd…`, build
  `bbb2a95c…`, proposals `379b17ca…`, configs `de6d63b5…`, extract `82c760…`, index `b4697c…`; the sealed audit's
  completion sha is `f751681f…` and runs hash `cf57bf7e…` (the runs hash is in the sealed evidence, not in the
  release receipt's kept fields).

## Sweep 1 — REFUSED (reported, not worked around)

Inputs: table `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table`, audit `…/output`, index
`results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, classification
`results/r1/evidence/C3_sweep_classification_20261028.json`, same paper-root.

Result: `ReleaseStop: STOP: integrity check failed for sweep1 (ValueError)`; underlying
`r1.c3.audit._verify_replay` → `evidence table differs from full source replay: proposals.jsonl`. **No output or
receipt was written** (`release_sweep1_traindev` absent). The refusal was not bypassed and the table/release is left
for the author to resolve. The sweep-1 side of the train/dev release is therefore **not delivered**, so the P4-LABELS
A step / P4 phase-1 remains blocked.

## Earlier sweep-2 release attempts (disclosed)

Attempts with a table rebuilt in a **different** paper-root failed closed (`BatchError`: index not under that root;
then `ValueError`: completion/build mismatch). The valid re-issue above used the original audit table and index in the
audit checkout, brought to the repaired published main; release.py and all checks were unmodified. The old invalid
receipt (`d2747771…`, published `38ae4a05`) is retained only as a quarantined audit record.

## Status

- Sweep-2 release tree: `/work/dwong/s2_release_20261122/release_sweep2_traindev_v2/sweep2/traindev/` (receipt +
  1,272-row train/dev output; no evaluation file, no test-label file).
- Independent review: `docs/r1/reviews/RELEASE_TRAINDEV_20261122_REVIEW.md` (round 1 NOT ACCEPTED on the
  authority/freeze defect; fixes applied; round-2 confirmation appended, **ACCEPTED**).
- Main advanced to `5a85adf9` before the repair; the re-issued receipt is from repaired main `f93264fc`; both
  receipted main commits carry the release row, the repaired one also carries the freeze.
- Labels: test labels and all evaluation values stay sealed; no U4/U5 or training started; I2 759919 still waits.
