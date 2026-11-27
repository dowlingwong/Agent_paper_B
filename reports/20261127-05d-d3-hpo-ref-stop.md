# local/20261126-05 item 3 — D.3 HPO reference (STOP before G10 integration)

- Task: `local/20261126-05`, item 3. Base `bd406db9`. Published branch `mac-d3-hpo-ref-20261127` @ `666320c95fa13c78e8c95054f86c03fd4ef98b3b` (code `f7070c45`).
- Independent review: **NOT ACCEPTED** as tier-E G10. Synthetic review ran 21 passes, one skip (ConfigSpace unavailable). The seven configuration spaces matched the pinned harness definitions. The existing full suite recorded base 181 failed / 4421 passed / 161 skipped / 3 errors and code tip 181 / 4442 / 162 / 3, with identical failing IDs.
- Engineering findings: the SMAC3 2.4 import does not expose the checked `__version__`; pin the environment and check installed distribution metadata. Allocate a fresh SMAC output directory per attempt instead of the default output and `overwrite=True`. Require a declared outcome when SMAC provides no incumbent. The independent review did not exercise a real SMAC backend.
- Dependency: the G10 CPU runner needs the G1 rendered-file start/config hash contract and the G6 terminal audit. The current callback-only path defaults to canonical JSON hashing, which does not satisfy the analysis start-hash parity check.
- Next: after G1/G6 interfaces are available, wire the production runner, finish the SMAC pin and attempt handling, and re-check on the real backend with synthetic inputs. Record the final environment hash when pinned. R1-STEP-ORDER (2)(c) keeps this optional unit off the mandatory D.3a/b path.

Decided alone: retain the existing candidate and record the missing production entry points as pending. No evidence run or sealed read.
