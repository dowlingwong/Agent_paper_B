# G.1b TASL-2 result — addendum (22 November 2026)

The authoritative result report is `G1B_TASL2_RESULT_20261121.md` (monitor memo; reviewed
`G1B_TASL2_RESULT_REVIEW_20261121.md` sha `7d3ca0f9…`, ACCEPTED engineering/result evidence with minor conditions).
The byte-identical `_MONITOR.md` duplicate was moved to `_to_delete/`; the canonical path is unique.

Corrections/evidence for the review's minor conditions:
- Retention: the capture tree actually contains the sealed `out.tar` and `out/` trees (the report's "not copied"
  line is conservative/wrong); SHA256SUMS binds them.
- Monitor restarts: three `MONITOR_START` records and the 22:44:47/22:48:44 baseline are disclosed here; 77 polls is
  an aggregate with max gap 305 s, not a single uninterrupted loop.
- One of 61 GPU samples showed a `[No data]` PID (its own engine); the "only own python" wording is narrowed.
- The 16 h is the monitor's own deadline, not a spec/note wall limit.
- Census evidence added: `G1B_TASL2_RESULT_20261121_captures/census_manifests/` (census/produced fmnist and
  cifar10 manifests + `DATA_MANIFEST_COMPARISON.md`); captures SHA256SUMS updated.
- G4 absence claim is supported by checked host roots (no G4 runs/records/logs/processes/leases; signed note and
  checkout present), not a general proof of absence.
Scope remains: 3/4 TASL-2 nodes sealed, fmnist data STOP, no 4-node/release-grade row; XC/G4 STOP record stands.
