# D.3 G2 constants fitter review — 27 Nov 2026

Task `local/20261127-06`. Independent tier-E review by a fresh Codex agent. Candidate
`7d7cf02632ed94f835bed562dc28a5ca94b57f39` was **NOT ACCEPTED** because the CLI could open symlinked
table or partition files before checking the concrete paths. The re-check of
`e95cb1d4fdd5d67e0bd3cdbe6170e9d56e546345` is **ACCEPTED**.

- The seven-node dev fitter reuses the A1/A2 implementation. LADDER evaluates the 121 declared thresholds
  with a strict comparison, the declared weights and the tie rule. The pinned table, configuration, split,
  noise and train/dev receipt bindings match revision 4.
- All expected table, metadata, receipt and partition files are checked before the loaders. The
  release partition directory cannot redirect. The table provenance guard runs before the proposal bytes
  are opened. The artifact check guards its input before reading. Tests use synthetic sentinels to
  exercise the pre-open refusals.
- Fit from the stable, reviewed sweep-2 table and train/dev release. Table parsing and hashing are separate
  reads, so keep the staged inputs stable throughout the fit. Compare the toolchain with the arms-freeze
  process. Record the generated artifact and its SHA for the coordinator before revision 4 is frozen.

The reviewer checked code and synthetic test definitions. The worker ran 19 focused synthetic tests.
No evidence data was opened.
