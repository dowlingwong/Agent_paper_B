# Paper B writer round close — 27 November 2026

Writer is idle on published base `96eb63da4c7877ad3829ee7a907f53b9e5cf6451`. The refreshed
queue at `coord/coordinator` `667c2c3951bfad3cc7989d47b8073b7501f5db7f` has no ready writer
card. All five assigned cards are published. The result-table handoff (next-phase runbook §3,
item 4) has no task ID and waits on authorised evidence. No new manuscript unit or review this round.

| Task | Task branch and tip | Review on record | Published merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. Title and eight-page trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

All four task tips and their merges are ancestors of the published base.

## Question and evidence

Which decisions improve autoresearch campaigns under the same caps of 20 worker runs and 80
manager calls? Replay in Sweep 1 found 3,274 duplicates in 4,999 proposals. That observation
motivates the de-duplication comparison. D.3 pairs arms on fresh campaign instances and uses
ten fresh audit seeds to measure final improvement over the start in units of each node's
reference standard deviation. A0R − A0 estimates what de-duplication and no-op skips add.
A2 − A0R estimates what the noise-aware rule adds with the skip rules in place. A3 − A2 and
A5 − A2 estimate what each learned forecast adds under that controller. The paired effects,
intervals and declared within-family decisions determine which gains the paper can claim.
The offline gate separately measures one-step utility on logged proposals. D.3b requires
frozen arms and its own authorisation and proceeds under either gate verdict. Campaign and
gate effects, intervals and readings, C1 audit extracts, and outstanding T1 and evidence
bindings remain placeholders.

## Draft checks

| Published draft | Fresh build | Main text ends | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf`, rc 0 | p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Both fresh builds matched the corresponding published PDF in extracted text. Rendered page 8
of each and confirmed the transition from limitations to references. Both final logs have
zero unresolved citations, references or multiply defined labels. Nine pre-existing overfull
boxes remain in each. The `FinalPaper` guard stopped at the unset gate outcome, rc 12.
`git diff --check` passed. The claim-to-table sheet SHA-256 is
`23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to rebuild from temporary copies of the assigned worktree. Its 27 paper files
and the claim sheet match published main byte for byte, including its 15 modified paths.
The linked Git metadata is read-only here, so fetch and reporting used temporary metadata.
The assigned checkout was preserved. No server job was submitted and no sealed data was read.

## Next round

- **Screening STOP and signed re-issue.** `compute/20261127-22` stopped at the runtime
  probe with 0 of 10,164 runs in attempt `SMEAS_EVIDENCE_20261127T1032Z` under
  `smeas-20261123-a`. No live process was recorded. STOP record on `6cf3ca70`,
  SHA-256 `1edf4b30c87417063714cccb48465994a0370cff5621e9367ca1cb1e01910169`.
  The original signed note and companion still hash to
  `96188e7c8d0ff92990f8ac821ad3608838cbb59226096064072a627061cd88e0` and
  `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
  R1-SCREEN-MEASURE-REISSUE on `96eb63da` records the author's approval of the `python3`
  command. Check `local/20261127-21` for the new note, accepted exact-diff re-check and
  SHA-256, then coordinator publication and Compute's strict preflight and fresh attempt ID.
- **D.3 freeze pending.** The G1 launchers are on main at `cd9af2af`. Compute's newer report
  `51dcef4a` records `compute/20261127-23` as independently ACCEPTED at review
  `dc76484d8b09565930da9ba335f53c69c4e5e81f`, delivery `39df5b9256ce69fad96659ab8217d452bd0211bd`.
  Compute reports 157 focused passes and 18 subtests with zero new full-suite failure IDs.
  Its unit record SHA-256 is `28a724e7cdc00cf713017976d771f74d852e68cbd8a6bdf05ac36cdf4b4f426c`.
  Check coordinator merge and Local's repeat of rev 4 step (5). The previous full re-check
  was NOT ACCEPTED and the binding-only diff was ACCEPTED. Screening measurement and
  disposition, freeze, the authorised per-arm smoke and stage authorisations precede
  the campaign runs.
- **Running elsewhere, last recorded at 11:40 UTC by Compute `51dcef4a`.** TASL-2 run
  `g1b-x-tasl-20261126-a`: Forest Cover PID `106573`, joint part, CPUs 4–7, 79 run files;
  Titanic PID `106578`, 109 of 150 split runs, CPUs 12–15. ETTh1 and MetaMaze were sealed.
  Check the two remaining seals, assembly and per-node determinism. The houseprice waiter
  exited before launch. Its retry `compute/20261127-15` waits for Forest Cover's CPU lease.
- **G.5 and offline evidence pending.** Remaining TASL-2 P11 checks
  (`compute/20261127-05` with `-08`) need the CPU leases and a valid pre-run spec route.
  The current launch validator refuses the unfilled `run_id`. Check combined P11, final
  bindings and render, accepted review and coordinator publication. The gate then waits for
  eligible T1 labels, the train/dev release, reviewed target consumers and preregistration
  bindings, trained and calibrated frozen arms, and signed test releases. Fill D.3, gate and
  C1 tables from the applicable authorised outputs.
- **Ada and scheduler idle or pending for these tasks.** The first Ada probe
  `trackp-p4-probe-20261125-a` ended with two 0.8B passes and two 4B OOM STOPs. Local's
  accepted checkpointing unit `585ed0d04bebfe1d6235d69b4bfe18207250ac39` specifies the
  new probe `trackp-p4-probe-20261127-b`. Check its merge, Compute dispatch, an empty Ada
  lease and the receipt before the phase-1 note. H200 `760065` and HTCondor preflight jobs
  `760148`, `760149` and `760152` were removed. `compute/20261127-12` still has no
  eligible L40S or A100 match. Idle IDs `759624` and `759625` belong to other work.
