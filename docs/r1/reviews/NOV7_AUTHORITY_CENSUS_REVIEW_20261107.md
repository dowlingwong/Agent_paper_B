# Independent review: 7 November authority record and TASL-7 census

AI-assisted (Codex). **R2 ACCEPTED for decision-record and read-only-census documentation only.** This is not acceptance of the final combined B1 checkout, author note, any host mutation, GPU qualification or launch. The review did not contact a host, invoke Slurm, run a model, use a GPU, or conduct an experiment.

## R1 finding and correction

The first census report summarized the two SSH invocations and their filters rather than recording the exact commands. Prompt §0.5 requires commands to be recorded for every host action. The implementer added the two exact local command lines, including SSH options, remote filters and redirections, local output captures and hash commands. R2 checked those lines against the tool-call transcript; the original output copies and hashes remain unchanged.

## Checked decision and input bytes

- `docs/r1/PLAN.md` candidate SHA-256 `8bdd57da88f514422214aad0285bce0ae1cdfa01c7e7451d32c9561b183287ba`; the decision cells in the added dated §10 author subsection quote the user's pasted wording, including the 00:45, 00:49 and 00:55 Chinese utterances, Q1 and the conditional Q0 approval. Q2's fixed detailed rule and its conditional fallback are referenced to the imported prompt; their outcome is not invented in these rows. The subsection states that all §0.3 conditions remain necessary and that B2/X.7/sweep 2 are not authorized by the prompt.
- Imported `docs/r1/prompts/MAC_OVERNIGHT_PROMPT_20261107.md` SHA-256 `4c4a2e6dfdaa8f12ea14399de23bdf73a1f019fbb14a5726822203fe03cbfedb` equals the file at the fetched `origin/docs/runbooks-04nov` branch. Formatting differs from the pasted text, but the reviewed operative §0 instructions agree; the attachment itself is the direct user request. The amended PLAN content passes the B1 branch's `_x5_author_row` parser for rule SHA `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad` when tested read-only; this is not a committed-HEAD or full author-gate test.
- The existing integration checkout still has the historical draft note with the old rule hash; the separately retained B1 branch's newer unsigned draft uses the reviewed rule hash. Both have `approved: false`. The final combined checkout must select and review the correct current draft and its bindings; this review accepts neither candidate as the final note.

## Checked census evidence and scope

- Final report `docs/r1/reports/TASL7_READONLY_CENSUS_20261107.md` SHA-256 `03a48f20f3279ac2d6f2731a5fcda4aab4a64383e9288335e8fd0379dac8fc76`. Output files `tasl7_census_20261107/census.txt` and `status.txt` SHA-256 `eb80db805009161b19460af3e53e88688faa4bd8c33c1da83f8393fc9a9133c1` and `1dacda12c0e51ddd6e28ad6cca5b1487c5c63021af3995c8fc20fbbb7677221a` respectively match the report and the local copies of SSH output.
- The listed GPU UUID, 236/24,564 MiB, 585 GiB available, empty compute-app listing, existing `trks_watch`, absent listed priority marker and presence of other-user agent processes appear in the retained outputs. Their observations are point-in-time; absent `fuser` output does not prove lock availability, and the other users' session identities and host ownership are not established. The report correctly retains a host-mutation STOP until safe ownership/occupancy clarification and a fresh reviewed preflight. The STATUS excerpts are historical snapshots, not current phase authority.

**Remaining:** obtain and review the author-fixed Q2 result; address all B1-path tests and restore the specified fake kill/resume coverage; satisfy the independently reviewed final-checkout, TASL-7 qualification, safe handover, author-gate and host preflight conditions in prompt §0.3. Only then may the final note be approved and a separate launch proceed. Q2 fallback, if invoked, requires its specific evidence and disclosure. No absence of author reply changes these conditions.
