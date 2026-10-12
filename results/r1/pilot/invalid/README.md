# Invalid pilot runs (kept for provenance; never analysed as data)

- `E1b_20261012T154045Z`: collected with harness `423addd` (plus uncommitted L12 edits). Branch leaves are invalid because of the L7 resume defect fixed in harness `f0dcd6a`:
  - after a discarded candidate, the continuation started from the discarded files;
  - verify's re-runs were not charged to the branch's compute budget.

  The rerun is `results/r1/pilot/E1b_<later stamp>/`.
