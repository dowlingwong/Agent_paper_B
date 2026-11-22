# G.1b TASL dry-run addendum — residues archived (21 November 2026)

The reviewed dry-run report (`G1B_TASL_DRYRUN_20261121.md`, sha `38866e0f…`) is unchanged; this addendum
records the post-review hygiene and the EVIDENCE status.

- **M2 closed.** The two dry-run attempts were moved out of the real run namespace on their hosts, no deletion:
  TASL-2 `runs/g1b-tasl-20261121-a/mlab_ogbn_arxiv/attempt-1` → `runs_dryrun_20261121/g1b-tasl-20261121-a/mlab_ogbn_arxiv/attempt-1`
  and `sealed_g1b/...` → `sealed_dryrun_20261121/...`; TASL-7 likewise for `mlgym_breakout_minatar`. The real
  `runs/g1b-tasl-20261121-a/<node>/attempt-1` and `sealed_g1b/...` paths are now absent, so a future full G.1b with
  this run_id is not blocked by a complete sibling attempt; the archived dry-run copies remain under the
  `*_dryrun_20261121` roots (records only, not a G.1b row).
- Capture count clarification: the bundle has 156 files = 155 payload + `SHA256SUMS`; the top-level manifest
  verifies 151/151 and the four nested manifests 2/2 each (per the review).
- The earlier 10:31Z spec-validation aborts (before a node attempt was created; zero attempts/lease) are recorded
  here as harmless aborts, not attempts.
- **B1 remains open for EVIDENCE:** no TASL-7→TASL-2 crosscheck job exists in the pinned code/spec, no signed
  G.1b note, and no launch-commit staging on main. This package is engineering preparation only; EVIDENCE G.1b is
  blocked until B1 is implemented/reviewed and the signed note is on main.
