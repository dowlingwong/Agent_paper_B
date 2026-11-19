# Moved aside — non-evidence duplicate staging directory (Track G U2, mlgym_fmnist)

Original path (inside the reports tree):
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS_MOVED_ASIDE/`

Reason: this directory is a wrong-timestamp staging copy (`035909Z` instead of the real fmnist evidence
`035842Z`). It contains **only** copies of this node's `static/` and `scripts/` files — all eight are
byte-identical (sha256) to the corresponding files in
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035842Z/` — and **no run evidence**
(no `run_record.json`, no logs, no captures). It is therefore not evidence and must not be committed as a
result directory.

Disposition (19 November 2026, record-corrections pass; per the accepted review
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` shared finding S2): **moved, not deleted**, out of
`docs/r1/reports/` so it cannot be mistaken for a result and so the reports tree contains exactly the five
reviewed node result directories. Preserved here for provenance only.

The eight duplicate files (sha256-equal to the fmnist result directory):
- `scripts/README.txt`, `scripts/_patch2_verifier_s002_fix.py`, `scripts/_patch3_mid_watcher_fix.py`,
  `scripts/compute_sampler_max.py`, `scripts/run_node.sh`, `scripts/verify_u2_records.py`
- `static/README.txt`, `static/static_mlgym_20261119T033511Z.log`

No GPU/U2 run was performed for this directory; it is not a smoke and not a retry.
