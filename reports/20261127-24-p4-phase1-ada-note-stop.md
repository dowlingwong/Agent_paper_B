# local/20261127-24 — Ada P.4 phase-1 draft and pre-signature STOP

for: coordinator

- **Base** `85b2421f95b53de3d5405504e7a217733fa4afa0`.
- **Branch** `mac-p4-phase1-ada-note-20261127` at `68ed7514609d4d88f4b52b5ddb59a515a2d8dac5`.
  Independent tier-E review **ACCEPTED for the blocked desk handoff** at
  `496689e08dea8a2590b5a73a37c20999cdc30bd1`.
- **Draft** `docs/r1/proposals/TRACKP_P4_PHASE1_ADA_NOTE_DRAFT_20261127.md`, SHA-256
  `9a907ce195904d430fab6042d878873398363b13184617b34d4c4ee4cd128bf1`.
- **Probe binding companion** `docs/r1/reports/trackp_p4_probe_ada_20261127b/P4_ADA_PROBE_BINDING_20261127.md`,
  SHA-256 `59722b2767fc0ee56f5797a48d697e203d8e2c3795efe486a8516a8a20e39bc0`. It supplies the exact charge
  lines missing from the abbreviated Markdown report, using the reviewed probe JSON.
- **Review** `docs/r1/reviews/P4_PHASE1_ADA_DRAFT_REVIEW_20261127.md`, SHA-256
  `97018c8e3db9ceb56721fd44532d8382bade125a06d223f899aafd9e7e05e23d`.

The unsigned draft binds the reviewed `zli538` Ada venv, host config, signed sweep-1 freeze and
train/dev receipt, and the four estimated arm times (2.52 / 6.79 / 2.51 / 6.75 GPU-h).
The two 4B arms use activation checkpointing at micro-batch 8 and effective batch 16. Jobs
including startup project 20.57 GPU-h. Together with the 3.10 GPU-h probe charge, including zero
for removed HTCondor job `760065` once, the total is 23.67 GPU-h and 29.855 slot-hours.
The 40 GPU-h and 64 slot-hour figures are reporting thresholds.

**Checks.** Receipt, host config, freeze, published probe hashes, charge files and projection
verified. All four canonical Ada direct descriptors rendered. The metadata-only preview spec
passed `validate_spec(..., launch=True)` shape validation. Preview SHA-256
`3f46939164e8abfdffea2bbbbb72e962778341165ef2871d3fdafa5f6bbf7d5a`.
The draft parser correctly returned `STOP: prerequisite P2 is not recorded as PASS`. Given the
preview spec pins, the current binding check separately returned
`STOP: note harness_commit must contain 'none'`. The reviewer independently reproduced the checks
and verified `trackp.py --check-config`. `git diff --check` passed. This is a documentation-only unit.

**Pending before signature.**

1. **P2** — publish the per-Kev P.3a E0 verdict and E4 hard-limit disposition. The named Unit B
   summary is on `ops-tasl-20261116` at `2287e4926fe0895b0a55b3a6a61c9afadc701307`; the coordinator
   can route a release-safe disposition.
2. **P3** — route a separately reviewed launch unit to bind and stage the harness actually imported
   by `sft-data` (recommended pin `897d83c8efa364ec2fdd37288241cc42e01d7274` after checking both paths),
   and apply R1-NO-TIMEOUT to the 86,400 s Track P subprocess and 7,200 s synthetic-evaluator
   deadlines. Preserve helper guards. Then fill the exact code and spec pins.
3. **P4 and placement** — recommend that the author tick the single-suite logging exemption for
   this phase and approve the Ada-only venv route with one leased card per arm job.
4. **P5** — request the staged Track P smoke with bound kernels and E0 equivalence on the admitted
   Ada venv. Require accepted reviews and resolve the smoke/E0-before-timing sequence through a
   reviewed carry-forward of the timings, or repeat the timing probes after parity. The CUDA
   matmul and completed fit probes alone do not satisfy P5.

Bring the reviewed, fully bound note to the author once these checks are ready. The coordinator
owns final publication. Compute's re-probe `trackp-p4-probe-20261127-b` is complete and both 4B
arms are sealed. No phase-1 job is active in the latest receipt.

Decided alone: wrote the full-hash companion so the published reviewed probe records keep their
bytes. Used an Ada-only preview for the draft checks and left the launch pins pending. No job
was submitted and no sealed partition was opened.
