# TASL launch chain (a)–(c): publication record, 22 November 2026

Written by the coordinating chat (Claude, AI-assisted) under R1-T1-DATA-MANIFEST. That row lets the coordinating chat
publish the re-issued specs and notes once they are independently reviewed and their launch checks pass, without a
further author decision.

## Published

- **Erratum record.** `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`, byte-identical to the
  reviewed bytes (sha256 `9b40944b…`), with its review and an editorial addendum for the review's C1–C3 (commit
  `4b7452b6`).
- **AR-pin binding record.** The TASL-2 AR-pin host-check binding record (merge `e9c12a4a`). It is input to (d), not
  to (a)–(c).
- **The chain.** `mac-tasl-chain-20261122` @ `570ae410` (READY 83), merged without squash or rebase (merge
  `38ae4a05`). Launch commits: (a) `34a5b1d6`, (b) `b5824240`, (c) `6ad899e0`.
- **Signed notes.** Each passed `g1b_tasl_join.py publication-check` (the amendment with `--p4`) before
  publication, and its check function against its spec.

  | note | run | launch from | paper_commit | spec sha256 |
  |---|---|---|---|---|
  | `authorizations/g1b_t1_tasl_20261122.md` (amendment, `mlgym_fmnist` on TASL-2) | `g1b-tasl-20261121-b` | `34a5b1d6` | `3c3f822a` | `7ff3c95b…` |
  | `authorizations/g1b_xc_t1_tasl_20261123.md` (cross-check re-issue, full rerun) | `g1b-tasl-20261121-b-xc2` | `b5824240` | `34a5b1d6` | `a9e6b463…` |
  | `authorizations/g4_t1_tasl_20261123.md` (G.4 re-issue) | `g4-tasl-20261121-a` | `6ad899e0` | `b5824240` | `fd9c6e9d…` |

  The dates in the file names are identifiers. The first cross-check and G.4 notes already use 20261122.

## Superseded, not to be used again

- `docs/r1/authorizations/g1b_xc_t1_tasl_20261122.md` (first cross-check note, run `g1b-tasl-20261121-b-xc`), superseded
  by `g1b_xc_t1_tasl_20261123.md`. Its sealed TASL-7 `mlab_cifar10` attempt stays as an engineering record.
- `docs/r1/authorizations/g4_t1_tasl_20261122.md` (first G.4 note), superseded by `g4_t1_tasl_20261123.md`. No pilot job
  or server ran under it.

## Not yet published

- **Note 2** (the three TASL-7 nodes). It is published after the re-issued cross-check's three step-1 verdicts are
  PASS and committed, as R1-G1B-NOTE2-DECISIONS and R1-T1-DATA-MANIFEST say.
- **(d) and the third note** (autoresearch). These wait for the author's signature of the third note.
- **The seven-node G.1b assembly.** It needs the author row R1-G1B-JOIN (decision G1B-JOIN, READY 83).
