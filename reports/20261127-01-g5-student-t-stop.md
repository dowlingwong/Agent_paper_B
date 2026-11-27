# local/20261127-01 — G.5 Student-t soft labels (STOP before render)

- Task: `local/20261127-01`. Base `6684e840`. Published task branch `mac-g5-student-t-20261127` @ `b9bc00fc75d77d9609d2dd4473a5ca7dd0b98185` (code `ad3ec948`).
- Review: fresh tier-E re-check of the existing unit **NOT ACCEPTED**. The fitted-label consumers and the Student-t scale need an author decision.
- Results: the branch validates and renders `tails_nu` and carries it to assembly. SFT rejects these extra fields. The gate-input builder and arms freeze still compute Gaussian soft targets for those rows. The frozen gate preregistration expressly specifies the Gaussian oracle and binds `gate_input_builder.py` sha256 `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`.
- Tests at the existing tip: Gaussian and Student-t unit tests passed. The recorded full suite was base 181 failed / 4247 passed / 161 skipped / 3 errors, tip 184 / 4263 / 161 / 3. Three added assembly tests failed in the seal environment and all 44 seal tests passed with the short temp path. That full-suite run has three additional failing IDs.
- Additional engineering finding: the autoresearch declaration parser accepts a matching numeric prefix in a different token (e.g. `nu = 5e1` or `nu = 5xyz` for 5). Re-check a complete number token and round-trip its displayed value if arbitrary degrees of freedom are supported.

## Author decision before publication

1. **Recommended**: keep the declared degrees of freedom and use the Student-t throughout T1 soft targets, including the gate's oracle and A2 fit. Amend the preregistration and replace the specific builder pins after code review. Engineering cost is a consumer wiring/schema change, focused tests that exercise the real consumers, and a base/tip full-suite comparison. It needs no new evidence collection.
2. Use Student-t for T1 training targets while keeping the preregistered gate oracle Gaussian, with the distinction recorded as part of the protocol. This avoids changing the gate builder and uses a different target across the two stages.
3. For either scope, **recommend sd matching**: for width `s` and degrees of freedom `nu`, scale the Student-t by `s * sqrt((nu-2)/nu)`. The other reading uses `s` as scale, increasing the sd by `sqrt(5/3)` for the two declared nodes. Both are feasible in code and give different bin masses.

Suggested row text for option 1 and sd matching:

> R1-G5-TAILS-CONSUMERS: For T1 soft targets generated from G.5, use each node's declared tail law in SFT, the arms-frozen training and constant fits, and the preregistered gate's oracle and A2 fit. For a Student-t node, match the declared Gaussian-width interpretation as a standard deviation and use scale s sqrt((ν−2)/ν). R1-G5-TAILS node choices and ν values stand. Publish the revised preregistration builder bindings after independent review and before arms freeze or a gate read. The Gaussian path remains byte-identical.

Next: coordinator routes the decision for the author. Until the scope and scale are signed and the engineering unit passes tier E, leave the G.5 render and formal labels pending. P11 engineering checks follow `compute/20261127-08` in parallel and do not wait for the rendered note.

Decided alone: stop the render at this review, retain the candidate branch for the follow-up, and raise the two evidence choices together. No sealed labels or evaluation partition was read.
