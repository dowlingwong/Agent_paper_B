# Active Paper B contract: b_v2

`contract_v2.yaml` is the single active contract. `contract_v1.yaml` is retained
byte-for-byte as a historical draft and rejected by the active loader. Existing
b_branch_v1 record schema is explicitly bound; old data are not relabeled as v2.
All prospective real-study choices without author bindings remain null.

`validate_for_phase(contract, phase, lane)` returns refusal reasons. Supported
lanes are one_step and sequential. Engineering requires a hashed closed fixture
and ENGINEERING_ONLY, with model calls/external runtime disabled. Qualification
requires a frozen design, bounded resources, runtime/action/outcome definitions,
hash-bound pool and disjoint split manifest, and prior engineering evidence plus
explicit authorization bound to the same version, lane, phase and design hash.
It never requires its own future qualification report or a final scientific
sample count. The sequential lane is bound to the L10 closed tree fixture; see TREE_SCHEMA.md.

N1 replay allowance is {p: null, provenance: null, R: null} in the draft.
Qualification requires provenance and positive R. A hashed measurement plan may
leave p null while qualification measures it; a resolved allowance requires its
stated evidence/assumption provenance. Zero is never supplied by default.

pilot, main_collection and final_evaluation return `phase not yet implemented`.
Unknown versions, stale artifacts/designs, changed fixtures, cross-lane/phase
records and descendant leakage refuse. Synthetic positive tests are explicitly
fixtures, not author signatures or real qualification. This validator performs
no launch and does not independently authenticate the authority of a signer.

```sh
.venv/bin/python protocols/paper_b/launch_validator.py --phase engineering --lane one_step
.venv/bin/python protocols/paper_b/launch_validator.py --for-launch
```

The second command must refuse the canonical draft. Do not resolve its nulls
using engineering smoke numbers. A real launch still needs separate user
execution authorization; none is granted by this local implementation.
