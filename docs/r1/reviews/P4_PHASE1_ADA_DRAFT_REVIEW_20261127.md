# Independent tier-E review of the Ada P.4 phase-1 draft

Verdict: ACCEPTED for the blocked desk handoff

Reviewed `local/20261127-24` at `496689e08dea8a2590b5a73a37c20999cdc30bd1` against
`85b2421f95b53de3d5405504e7a217733fa4afa0`. The diff contains two Markdown files.
The draft remains unsigned with `approved: false`.

- The draft preserves the sweep-1 train/dev receipt, signed P3 split, synthetic-only test, and
  absence of evaluation-seed reads. The proposed `zli538` Ada venv route matches the reviewed host
  fill. It retains one leased card per arm, micro-batch 8, effective batch 16, and checkpointing
  for the two 4B arms only.
- The probe companion provides the full charge hashes required by the switch. I verified them
  against both charge files and the accepted probe JSON. Ten attempts totaled 3.091 GPU-h, rounded
  up to 3.10 GPU-h, including the zero charge for HTCondor job `760065` once. The projections agree
  at 20.57 GPU-h including startup, 23.67 GPU-h including probes, and 29.855 slot-hours.
- P2 still needs a published per-Kev E0/E4 disposition. The cited Unit B summary exists at
  `2287e492`, with the stated SHA-256, and is absent from published main. P3 still needs reviewed
  harness enforcement, exact launch pins, and removal of the runner's fixed 86,400-second stage and
  7,200-second synthetic-evaluator deadlines. P4 still needs the author's tick. P5 still needs
  reviewed Ada staged smoke and E0 equivalence, plus disposition of the earlier timing probes
  under the smoke/E0-before-timing requirement.
- The independent draft check passed receipt, probe, projection, Ada-only spec shape, and all four
  direct descriptor checks. The parser refused P2 and the existing binding check refused the unresolved
  harness line. `trackp.py --check-config` returned no placeholders and matched the recorded configuration
  digest. `git diff --check` passed. No job was submitted, host contacted, or label, test, or evaluation
  record opened.

The draft SHA-256 is `9a907ce195904d430fab6042d878873398363b13184617b34d4c4ee4cd128bf1`.
The probe companion SHA-256 is `59722b2767fc0ee56f5797a48d697e203d8e2c3795efe486a8516a8a20e39bc0`.
