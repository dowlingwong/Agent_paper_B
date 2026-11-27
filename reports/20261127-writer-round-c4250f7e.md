# Paper B writer round check · 27 November 2026

Published base `c4250f7ea26a97e0f3c7b475613287864110a14c`. Checked the writer queue on
`coord/coordinator` at `324f6ad4b0406f075934dea9b59af99b58315424`. Writer is idle.
All five cards are published. The remaining result-table handoff has no task ID and waits for released evidence.

| Task | Delivery branch and tip | Recorded review | Publication |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425` | Restructure re-check ACCEPT WITH MINOR; corrections recorded. The title and trim follow-up had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37b` | ACCEPT WITH MINOR; corrections recorded. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36` | ACCEPTED on independent re-check. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a4` | ACCEPTED on independent re-check. | `e153df24` |

Verified that all four delivery tips are ancestors of the published base. The worktree's 15 modified paths
match that base byte for byte. The checks used temporary Git metadata and a temporary copy of the published paper.
This round changed no manuscript source, signed file, or task branch. No new review or code test was required.
No server job was submitted and no sealed evidence was read.

## Manuscript checks

At the same cap of 20 worker runs and 80 manager calls, D.3 asks which control decisions improve a campaign's
final result. Each paired campaign's outcome is the gain from its starting to its final configuration, audited
on ten fresh seeds and scaled by the node's reference standard deviation. The estimate and interval for
A0R − A0 support the claim about the rule layer, A2 − A0R the claim about the noise-aware decision rule, and
A3/A5 − A2 the claim about adding a learned forecast. The offline gate measures one-step utility on logged proposals.
The manuscript keeps the D.3, offline gate, C1 and T1 evidence fields as placeholders. Claims about their measured
effects wait for authorised estimates and intervals.

| Draft | Fresh build | Main text | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf` rc 0 | ends p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` rc 0 with `DraftGatePassed` | ends p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

The extracted text of both rebuilds matched the corresponding published PDFs. Visual inspection confirmed the
page-8 transition to references in both. The final logs show no undefined citations, undefined references or
multiply defined labels. Nine existing overfull lines remain in each build. The `FinalPaper` build stopped
at the unresolved gate-outcome switch as expected. `git diff --check` passed.
The published claim-to-table sheet SHA-256 is `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

## Next round

- **D.3 result tables pending.** The complete revision 4 step-(5) review was NOT ACCEPTED. The binding-only diff
  was ACCEPTED. The coordinator published the STOP as a record at `c4250f7e`. The harness and replicate routes
  can disagree about which configuration the terminal audit uses. Check `compute/20261127-20` for the reviewed
  G1 correction, then `local/20261127-16` for the renewed step-(5) review. Screening authorisation and measurement
  are independent prerequisites for the freeze. After freeze, the per-arm smoke and stage authorisations precede
  campaign evidence collection. D.3b also waits for frozen arms. Check the signed releases and audited extracts
  before filling the D.3 and C1 tables.
- **Running elsewhere in the latest recorded sample.** At 05:36 UTC, Compute reported TASL-2 expansion
  `g1b-x-tasl-20261126-a` with MetaMaze PID `106579`, Forest Cover `106573` and Titanic `106578` still
  running. ETTh1 was sealed. Check the remaining seals and determinism decisions. Houseprice waiter
  `208315` timed out before starting a run. Its retry and the remaining TASL-2 P11 checks wait on the
  applicable CPU leases, including 0–3 and 4–7.
- **Probe and scheduler.** Ada P.4 probe card `compute/20261127-19` has a preparation branch at `e066dc6d`.
  Neither the queue nor the latest Compute report at `db2f5195` records a probe launch ID. Check the
  forthcoming receipt before treating it as launched. The separate H200 request `760065` was last reported
  idle. D.3 preflight jobs `760148`, `760149` and `760152` were removed after no match. Compute owns any
  further capacity checks.
- **Offline results pending.** G.5 needs the remaining host checks, final reviewed bindings and note publication.
  The gate then waits for eligible-node labels, the T1 train/dev release, reviewed target-consumer and
  preregistration bindings, trained and calibrated frozen arms, and the signed test releases. Resume the
  writer result-table handoff after the applicable releases.

Decided alone to verify the published drafts without modifying the assigned worktree and to append this round
check to the existing reports.
