# local/20261127-09 unit 2 — G.5 tail laws in SFT, arms and gate, with preregistration draft

for: coordinator

- Assembly base `82a22977cf98e01783ba00e2b93ec2e74779f6e8`; separate consumer branch `mac-g5-tails-consumers-20261127` @ `681f15d71581a086f10859633bcb152aceaeaaac`. Independent tier-E **ACCEPTED** at `94b1decd` for the runtime code and unsigned amendment. The subsequent synthetic fold fixture supplies its declared law and verifies preservation through folds. See `docs/r1/reviews/G5_TAILS_CONSUMERS_REVIEW_20261127.md`.
- Publish the integrated reviewed code candidate, `mac-g5-s9-split-v2-20261127` @ `f5e3827b22d6e14651e2bc038e442669b52203ef`, with the amended binding after the remaining publication checks. The separately reviewed branch is the consumer source unit. Its draft hashes describe that branch. The integrated branch has both units' exact bindings; use its hashes for publication. This distinction matters because the S9 release and split changes touch the same builder and release paths.
- Synthetic audit labels produce the same sd-matched Student-t bins in SFT, arms training, the gate oracle and A2. Gaussian evaluation stays on the existing implementation. The initial seven declarations are fixed. A noninitial T1 node takes its tail law from the receipted G.5 build. Primary and fold inputs carry that law, and conflicting metadata is refused.
- The historical T0 train/dev receipt verifies the builder from the original published release commit. Future release rows cite the original preregistration SHA-256 plus the separate, exact, published amendment SHA-256, both written to the receipt. The gate verdict code and D8 guard retain their prior bindings. The draft is `frozen: false`.

## Verification

The pre-fixture full consumer run against the tested assembly tip had six added failing or error IDs, all the synthetic fold fixture without its autoresearch law. No production guard was relaxed. Independent re-check returned 6 passed and 1 skipped in that module after the fixture correction. The targeted integrated run returned 181 passed and 1 skipped; the fold, release and S9 re-check returned 80 passed and 1 skipped.

Full `r1/tests` ran serially with `hupdate`, clean harness pin `a3fedbbd`, fresh separate `TMPDIR` values,
`COPYFILE_DISABLE=1` and LightGBM off the path. Command `python -m pytest -q -p no:cacheprovider -rfE
--continue-on-collection-errors r1/tests`.

| Checkout | Failed | Passed | Skipped | Errors |
|---|---:|---:|---:|---:|
| Published base `e153df24` | 76 | 4,867 | 162 | 3 |
| Exact integrated tip `f5e3827b` | 76 | 4,931 | 162 | 3 |

The complete set of 79 failing or error test IDs is identical, including the embedded spaces in two parameter IDs.
Sorted newline-delimited list SHA-256 `1f8ae808ccf8ae3cd17503991f7d23a16055c77f55af01e33f74558ac7599256`.

## Bindings and next action

- Standalone draft `docs/r1/proposals/G5_TAILS_PREREG_AMENDMENT_DRAFT_20261127.md` SHA-256 `bb800439fc7ce9f5c266d14fdfcd26c4176c8c26d7c924d261cdc0fd9ca3a603`; standalone builder SHA-256 `af339af450b108529f45b9b572fdb9903d6e7546b752536c035381d7adcf62be`.
- Integrated draft at the same path SHA-256 `794452834accc15da7ed0bd24ba179616b92b6870858749dfb7b1b10d4f787b8`; integrated builder SHA-256 `0feed789e5e98b005995b4e0e933f3ef33ef1efcede02591e4f2df29bbf62c6e`; release SHA-256 `db073ebcde4c3d6081dc694375c1cf75d1a389732bcca110b681a5dd7e8544f7`. The integrated draft carries all eight exact source digests.
- After integration, bind the final code at its published commit, obtain the approved exact tail amendment/PLAN binding and complete the PRE-SPLIT and release requirements. Use the post-freeze reads amendment's A§13 pending code fields for the reviewed integrated `arms_constants.py` (`ec0c8aa5b180ef6d878361ac1f9caad0560674c67fdf3c7429b048ee6251f7ef`) and `arms_freeze.py` (`2676cff80a52f727d9a30576124956010d22836e08663ef76cadeb1b12c18ecd`) before freezing the record. Validate the exact arms-frozen record before the test release names it. The order is approved train/dev release, T1 SFT and arms preparation under the amended law, frozen arms and authorized test release, then the one gate read. D.3 G2 uses its separately reviewed original pin.

Decided alone: retained release and code provenance separately, preserved the historical reader, and coordinated shared-file hashes at the reviewed S9 integration. No real labels, evaluation values or test blocks were opened. No job was submitted.
