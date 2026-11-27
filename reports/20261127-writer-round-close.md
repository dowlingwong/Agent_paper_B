# Paper B writer round close · 27 November 2026

Published base `7f6f802382ccb77a2d2ba3cd9435183c1792effc`. Queue `coord/coordinator` at
`d05d3d7a3a6007b32006fcdfd5c2b379d398a7fd`. Writer is idle. Deliverables for all five writer cards are on `main`.
The result-table handoff remains pending the authorised evidence releases. No cluster job was submitted and no
sealed evidence was read.

| Task | Delivery branch and tip | Review | Publication |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425` | Restructure re-check ACCEPT WITH MINOR, corrections recorded. See the original and title-and-trim reports. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37b` | ACCEPT WITH MINOR, corrections recorded. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36` | ACCEPTED on independent re-check. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae`, base `6aee0eb34a9c8bae4c9c24d93b261d24a76a8403` | ACCEPTED on independent re-check. | `e153df24` |

## Manuscript verification

D.3 asks what each control decision buys at the same cap of 20 worker runs and 80 manager calls.
Matched campaigns measure final improvement over the start on ten fresh audit seeds. The paired estimates
and intervals for A0R − A0, A2 − A0R and A3/A5 − A2 support claims about the rule layer, the noise-aware
one-step policy and the learned forecast, respectively. The offline gate tests one-step utility on logged
proposals. The campaign, gate and C1 estimates and intervals remain placeholders, as do the outstanding
T1 and evidence bindings. The claims wait for those measurements.

| Published draft | Fresh build | Main text | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `papers/r1/build/main_draft_gate_not_passed.pdf` | rc 0 | ends p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `papers/r1/build/main_draft_gate_passed.pdf` | rc 0 | ends p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Both `latexmk -pdf` builds reproduced the text of every published page. The page-8 transition was rendered
and inspected in both versions. The final logs have no unresolved references, citations or duplicate labels.
Existing appendix overfull lines remain. The `FinalPaper` guard stopped at the unset gate outcome, as expected.
`git diff --check` passed. No code change required the `r1/tests` suite or a fresh review.

Decided alone to verify the published source and preserve the assigned worktree. Its 15 modified paths all match
published `main`. The shared Git metadata is read-only under the workspace permissions, so fetch and reporting
used temporary Git metadata. Builds used temporary copies of the published paper source.

## Next round

- **Running elsewhere.** Latest Compute report `db2f5195`, sample 05:36 UTC. TASL-2 expansion
  `g1b-x-tasl-20261126-a` was running MetaMaze PID `106579`, Forest Cover PID `106573` and Titanic PID `106578`.
  ETTh1 was sealed. Check the remaining seals, assembly and determinism before routing eligible nodes to G.5.
- **Blocked on leases and publication.** Houseprice waiter PID `208315` timed out before any run. Compute
  `20261127-15` and the remaining TASL-2 P11 checks wait on CPU leases 0–3 and 4–7. G.5 publication waits on those
  checks, final binding and accepted review. The offline gate follows completed labels, the T1 train/dev release,
  reviewed target-consumer and preregistration bindings, the frozen arms, and the signed test releases.
- **Compute ready or idle.** Ada synthetic probe card `compute/20261127-19` is ready with the reviewed host
  config on `main`. The Compute report has no probe job ID yet. The separate H200 request `760065` was last
  recorded idle. D.3 HTCondor preflight jobs `760148`, `760149` and `760152` were removed. Check for a runnable
  ETP L40S or TOpAS A100 match.
- **D.3 and writer.** Check the screening signature, publication and measurement, the remaining rev 4 fields
  and complete independent review, then the frozen pre-declaration and authorised per-arm smoke. G1/G6 and
  the gate-output unit are published. HPO-REF is in the coordinator's checks. D.3b also requires the frozen arms.
  Resume result tables when signed releases and audited extracts become available, including the applicable C1
  release. Continue to use the declared interpretation for each outcome.
