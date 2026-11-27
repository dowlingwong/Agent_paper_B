# Paper B writer round close — 27 November 2026

Writer is idle. All five assigned cards are published at base
`ebc28ec073e75adea472af96316d93cea78736fe`. The queue at
`cf599e6851eb76ce724292cc3569c8176b46d375` has no new writer card. The result-table
handoff (§3 item 4, no task ID yet) is pending the authorised releases. No evidence placeholder was filled.

| Task | Published task branch and tip | Recorded review | Merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Draft verification

Which decisions improve an autoresearch campaign at the same caps of 20 worker runs and 80 manager
calls? D.3 pairs campaigns on the same instances and measures the final configuration's gain over the
start on ten fresh audit seeds, in units of the node's reference standard deviation. Paired effects and
intervals for A0R − A0 measure what the rule layer adds, A2 − A0R measures what the noise-aware rule adds
after de-duplication, and A3/A5 − A2 measures what learned forecasts add. The offline gate measures
one-step utility on logged proposals. Its verdict and the campaign contrasts each have their declared
reading. Estimates and intervals for D.3, the gate and C1 remain placeholders, along with pending T1
evidence fields.

| Published draft | Fresh build | Main text | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf` rc 0 | ends p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` with `DraftGatePassed`, rc 0 | ends p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Fresh rebuilds from the published source matched every published page in extracted text. Rendered
page 8 in each draft and inspected the transition to references. Both final logs have zero undefined citations,
undefined references or duplicate labels, and nine existing overfull boxes each. The `FinalPaper`
guard refused the unset gate outcome as expected. `git diff --check` passed. The claim-to-table sheet
SHA-256 is `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to rebuild from a temporary archive of published main. The assigned worktree was
checked in place. Its 15 modified paths match published main byte for byte. Temporary Git metadata
handled fetch and this report because the shared metadata is read-only. There is no new manuscript unit or review in this round. No server job
was submitted and no sealed partition was accessed.

## Next round

- **D.3 evidence.** The prior full rev 4 step (5) review was NOT ACCEPTED. The binding-only diff was
  ACCEPTED. Compute's terminal snapshot fix (`compute/20261127-20`, branch
  `compute-d3-g1-final-20261127` @ `ff244366b7168a210a302b37deda5438f83c9e6e`) has an
  ACCEPTED independent re-check at `d5acf3ab` and awaits the coordinator's merge. Compute reported
  161 focused passes, 18 subtests and zero new full-suite failure IDs. Local repeats step (5) under
  `local/20261127-16` after that merge. The accepted screening note at `b2360a7a` still needs the
  author's signature, publication and the measurement. Rev 4 freeze, per-arm smoke and stage
  authorisations precede campaign launch. D.3b also requires frozen arms.
- **TASL-2 expansion, last recorded 08:53 UTC (`coord/compute` @ `b4b33527`).** In run
  `g1b-x-tasl-20261126-a`, ETTh1 and MetaMaze are sealed. Forest Cover PID `106573` (279/460,
  CPUs 4–7) and Titanic PID `106578` (236/460, CPUs 12–15) were running. Check both seals, then
  assembly and the determinism decisions under `compute/20261126-10`. Houseprice waiter `208315`
  timed out before launch. The houseprice retry and the remaining TASL-2 P11 checks need the 0–7
  leases. Forest Cover is the remaining lease holder for that range.
- **Gate and C1 evidence.** G.5 awaits the remaining host checks, final binding, accepted review
  and coordinator publication. The gate follows eligible-node labels, T1 train/dev release, reviewed
  target-consumer and preregistration bindings, trained and calibrated frozen arms, and the signed
  test releases. Fill result tables after the applicable authorised extracts, including C1.
- **Ada and scheduler.** Engineering probe `trackp-p4-probe-20261125-a` is complete. Both 0.8B
  bases passed and both 4B bases hit the signed OOM STOP at micro-batch 8. Record
  `compute-p4-ada-probe-20261127` @ `4e51adef` and accepted re-check `60958144` are published at
  `ebc28ec0`. Check `compute/20261127-21`, the author's 4B route decision and the phase-1
  note's harness binding. No probe job remains active. H200 job `760065` and D.3 preflight jobs
  `760148`, `760149` and `760152` were removed after no match. Check `compute/20261127-12`
  for the next eligible L40S or A100 match.
