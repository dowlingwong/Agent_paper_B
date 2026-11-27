# Paper B writer round close — 27 November 2026

Writer is idle at published base `c76e1b49e9926ea8024e336a6eef7deb1e367e08` and coordinator queue
`c682d06bfc79d0d826b32654dbfdb856a3543b7f`. All five writer cards are already on main.
The result-table handoff (next-phase runbook §3 item 4, no task ID yet) is pending authorised results.
No server job was submitted and no sealed evidence was read.

| Task | Delivery branch and tip | Review on record | Publication |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, fixes applied. The title and trim follow-up had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, fixes applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

Verified that each task tip is an ancestor of the published base. The earlier restructure and claim-sheet
entries in STATE precede the published merges above. This round has no new manuscript unit or review.

## Question, measurement and draft checks

Which decisions improve an autoresearch campaign under the same caps of 20 worker runs and 80 manager calls?
D.3 pairs the arms on fresh campaign instances. On ten new audit seeds it measures how much the final
configuration improves on the start, in units of the node's reference standard deviation. A0R − A0 estimates
what de-duplication and no-op skips add. A2 − A0R estimates what the noise-aware rule adds with those skips
in place. A3 − A2 and A5 − A2 estimate what each learned forecast adds. The intervals and declared decision
rules determine what the paper can claim. The offline gate separately measures one-step utility on logged
proposals. D.3 campaign effects and intervals, the offline gate verdict and estimates, C1 audit extracts,
and pending T1 and release bindings remain placeholders. D.3b runs after arms freeze under its own
authorisation regardless of the gate verdict.

| Published draft | Fresh build | Main text ends | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf`, rc 0 | p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Both rebuilt drafts matched every published page in extracted text. The rendered page 8 in each build
showed the transition from limitations to references. Both final logs had zero undefined citations,
undefined references or multiply defined labels and nine existing overfull boxes each. The
`FinalPaper` guard stopped at the unset gate outcome. `git diff --check` passed. The claim-to-table
sheet SHA-256 is `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to rebuild from a temporary copy of the assigned worktree after verifying all 27 paper
files and all 15 modified paths against published main byte for byte. The assigned worktree was preserved.
Fetches and reporting use temporary Git metadata because the linked metadata is read-only here.

## Next round

- **Screening ready for Compute.** `compute/20261127-22` is first in Compute's queue. The signed
  screening note at `c76e1b49` has SHA-256
  `96188e7c8d0ff92990f8ac821ad3608838cbb59226096064072a627061cd88e0` and the companion
  pre-declaration has SHA-256 `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
  Check the strict preflight and receipt for run `smeas-20261123-a`. The latest Compute report
  has no launch receipt for that ID. Any decision-node SHARED finding goes to the author before D.3 freeze.
- **D.3 blocked at revision 4 step (5).** Local `20261127-17` reports that the terminal repair passes
  at `2d88fe1b`. Full tier-E re-check **NOT ACCEPTED** and binding-only diff **ACCEPTED**.
  The production G1 summary has a schema mismatch with G7, and G6 does not emit the required per-keep
  audits. Review branch `mac-d3-r4-step5-repeat-20261127` @
  `9841e2c0bf3f04460915016327c90c859376ac95`, review SHA-256
  `47785eac7fe5bbf1bfbf3117974fab5660e23c8d4c39194eef30e2f099a9257b`.
  Check coordinator routing for the G1/G6/G7 integration, its reviewed merge, the next step-(5) re-check
  and screening disposition. Freeze and the authorised per-arm smoke precede campaign launches.
- **Running elsewhere, last verified sample 08:53 UTC from Compute `b4b33527`.** TASL-2 run
  `g1b-x-tasl-20261126-a` had ETTh1 and MetaMaze sealed, Forest Cover at 279/460 (PID `106573`,
  CPUs 4–7) and Titanic at 236/460 (PID `106578`, CPUs 12–15). Check remaining seals, assembly
  and determinism. Houseprice waiter `208315` exited before launch. Forest Cover held the outstanding
  lease for the houseprice retry and remaining TASL-2 P11 checks.
- **G.5 and offline gate pending.** G.5 waits for the remaining P11 checks, final rendering and bindings,
  accepted review and coordinator publication. The gate waits for eligible T1 labels, train/dev release,
  reviewed target-consumer and preregistration bindings, trained and calibrated frozen arms, and signed
  test releases. The writer resumes once the authorised D.3, gate and applicable C1 extracts arrive.
- **Ada and scheduler.** The original synthetic probe `trackp-p4-probe-20261125-a` finished with
  both 0.8B bases passing and both 4B bases at the signed OOM STOP. The author approved activation
  checkpointing for those two 4B arms at `c76e1b49`. Check `local/20261127-18` for the tier-E
  unit and the new Compute probe receipt before the phase-1 note. H200 `760065` and HTCondor
  preflight jobs `760148`, `760149`, `760152` were removed. Check `compute/20261127-12` for an
  eligible ETP L40S or TOpAS A100 match.
