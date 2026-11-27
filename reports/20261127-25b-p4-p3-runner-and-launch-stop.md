# local/20261127-25 P3 — runner accepted and launch spec pending signature

for: coordinator

- Published base `83425c7008826c2a4edb5470c708d8ce083d13f3`.
  Runner branch `mac-p4-p3-runner-20261127` at `8c8b9fecf3c2d478ae4a2c6e9731565f349649cb`.
  Exact code and test commit `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`.
- Independent tier-E verdict **ACCEPTED**. Review
  `docs/r1/reviews/P4_P3_ADA_LAUNCH_REVIEW_20261127.md`, SHA-256
  `01d3f2eef9d3e3a6f15128adc23512bfd00aef4a84948e451fc5458d72fb33c5`.
- Ada-only draft branch `mac-p4-p3-ada-draft-20261127` at
  `82940a4988775eba6c8ed2d89de88f220af2e25f`, accepted for the **blocked draft handoff**.
  Exact spec-only commit `befb58c8b3f5b222a2cf8973e513b252235453fc` is **unsigned**.
- Spec `r1/scripts/htcondor/trackp_p4/p4_spec_ada_phase1_20261127.json`, SHA-256
  `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`.
  Draft `docs/r1/proposals/TRACKP_P4_PHASE1_ADA_NOTE_DRAFT_20261127.md`, SHA-256
  `33175a171482fffbfc72322e42c745581fac60574e98ac83930372419c060a23`.
- The stage and switch bind harness `897d83c8efa364ec2fdd37288241cc42e01d7274`.
  The job stages its clean checkout and selects it for both data builders and the synthetic evaluator.
  The 86,400 s Track P subprocess and 7,200 s synthetic evaluator deadlines are withdrawn.
  The git, staging, health and sampler helper guards remain (R1-NO-TIMEOUT (1) and (4)).

## Tests and checks

Serial full `r1/tests` used Python 3.12.8, pytest 9.2.0, torch 2.15.0, a clean harness at
`897d83c8`, LightGBM off the path and a new `TMPDIR` for each run.
Command `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.

| Checkout | Passed | Failed | Errors | Skipped | Subtests passed |
|---|---:|---:|---:|---:|---:|
| Base `83425c70` | 5,042 | 153 | 6 | 170 | 71 |
| Candidate `82940a49` | 5,044 | 153 | 6 | 170 | 71 |

The [159 failure/error IDs](20261127-25-p4-fullsuite-failure-ids.txt), including parameter
whitespace, match in both runs. SHA-256
`971c9517afff96ea8074f2e87f34bf597552b491835d07c44ed88a4b121a9718`.
Both torch files passed **215/215** (`r1/tests/test_trackp_p4_runner.py` and
`r1/tests/test_trackp_p4_direct.py`). Launch-strength spec validation, four Ada descriptor
renders, Ada config check, committed tree restriction and published input hashes passed.
The official draft parser refused at P3. The independent binding check refused at the missing
Ada smoke/E0 citation. The remaining bindings passed when isolating that citation with
an in-memory path fixture. `git diff --check` passed.

## Next

1. Merge the reviewed runner branch. P2 is already on published main at `523ccfbc`.
2. An authorized signer recreates the one-file spec commit with SSH signing, using code
   `0b465954` as its parent and preserving the reviewed spec bytes. The local session had no
   configured signing identity and its SSH agent held none. Record the signed tip and
   re-check P3 before publishing a launch spec. The draft branch carries the exact bytes for
   that handoff.
3. Route the Ada functional smoke and E0 parity using the pinned venv and staged kernels.
   Reuse the accepted timings only if review verifies that same kernel and runtime. Otherwise
   repeat the timings after parity. P5 is pending.
4. After those prerequisites, recommend the author sign the exact bound Ada-only note with
   the single-suite P4 logging exemption, one leased Ada card per arm, and Kev 0.8B first.
   The four arms, micro-batch 8 and effective batch 16 are as declared. The phase-1 projection
   is 23.67 GPU-h including the probe and 29.855 slot-hours.
   Use the exact published signed-spec checkout and `p4_switch.py submit --spec SPEC` only
   after note publication, strict checks and Compute's job and attempt-ledger check.

Decided alone: use a fresh per-job harness checkout. Preserve the common
spec template and put the Ada-only spec in its own one-file commit. Separate the publishable
runner from the unsigned launch candidate. No job was submitted.
