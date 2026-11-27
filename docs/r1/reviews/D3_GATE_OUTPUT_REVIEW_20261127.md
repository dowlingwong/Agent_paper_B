# D.3 gate-output unit review

Task `local/20261127-14`. Tier E. Independent reviewer was a separate Codex review agent with no implementation edits.
Published base `66cc33f2a1e717ee517f79646a597305621f7ba3`.

## Initial review

**NOT ACCEPTED** at `8e5c8bbac969547e2270b78c4c5f141a60724dff`.
The reviewer reproduced each issue with synthetic data. The initial focused suite passed 11 tests.

| Finding | Reproduction |
|---|---|
| B1 | Substituting a valid PRE-DUP full input and its supplied hash for the primary input passed capture and exported the full-population utility. The draft input format alone could not identify the population. |
| B2 | A string in `node_counts` and a missing arm lower-bound field passed report validation and point binding. |
| B3 | The preflight accepted a UTF-8 BOM that the pinned gate refused after the one-shot capture directory had been created. The corrected input then hit the duplicate-attempt guard. |

## Independent re-check

**ACCEPTED** at `090ad389cdc826407f067106e17981cf8cf6d458`.

- B1 is closed by the step-5 builder's named staging receipt, the fixed input locations on published main, and the same input hashes checked across all three committed step-6 captures.
- B2 is closed by nested v3.1 validation and the checks of derived metadata and point results.
- B3 is closed by strict UTF-8 parsing before any attempt directory is created.
- Both published author release rows and their shared committed arms-frozen record are checked before opening input. The A§4.2 point utility uses the primary input's test series in sigma-node units for A2, A3 and A5 on the seven D.3 nodes. The descriptive step computes neither a bootstrap nor a gate verdict.
- An exact archived checkout passed 57 tests in `test_d3_gate_output.py` and `test_gate_input_builder.py`. A separate mixed T0/T1 synthetic gate report passed validation. `git diff --check` passed.

**Diff-only re-check ACCEPTED** at `f522ea45de24fef854db2cf2bee378474195f4dd`.
The final change resolves the published blob before opening the committed checkout copy. Synthetic probes verified that missing publication stops before the checkout copy is opened and mismatched bytes stop before use. The exact archived checkout passed all 16 focused tests. `git diff --check` passed.

Final module SHA-256 `59d15d465edca1fb274cfe715653473949f8abeeb9d79adf9d8540ea471a77ab`.
The pinned gate SHA-256 is `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`.
The builder at this base has SHA-256 `0feed789e5e98b005995b4e0e933f3ef33ef1efcede02591e4f2df29bbf62c6e`.
Both source files are byte-identical to the base. All reviews used synthetic data only.
