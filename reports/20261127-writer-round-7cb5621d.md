# Paper B writer round close — 27 November 2026

Writer is idle at published base `7cb5621dc26853540acfbef3acd3ccd9f243089c`
and coordinator queue `88205a9183e3de8d2010e8d31eec4a9dda182611`. All five assigned
cards are on main. The result-table handoff in the next-phase runbook §3.4 has no card ID
and waits for authorised results. No evidence placeholder was filled.

| Task | Deliverable branch and tip | Review on record | Published merge |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and eight-page trim were a follow-up without a separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

All four deliverable tips are ancestors of the published base. The STATE rows for the restructure
and claim-to-table sheet still cite earlier delivery tips. The published T5 correction gives
simulated changes in campaign gain. The appendix placeholder asks for the size of a
keep-threshold shift on `digits_mlp`, so the corrected gain figures do not fill that field.

## Question and evidence

Which control decisions improve an autoresearch campaign under the same 20 worker runs and
80 manager calls? D.3 pairs arms on fresh campaign instances. On ten new audit seeds, it
measures how much the final configuration improves on the starting configuration, in units
of each node's reference standard deviation. A0R − A0 estimates the gain from de-duplication
and skipping no-ops. A2 − A0R estimates what the noise-aware rule adds once those skips
are in place. A3 − A2 and A5 − A2 estimate what each learned forecast adds. The paired
effects and intervals, with the declared within-family decisions, determine what the paper
can claim. The offline gate separately tests one-step utility on logged proposals. D.3b
follows arms freeze and its own authorisation regardless of the gate verdict. Campaign
effects and intervals, gate estimates and verdict, C1 audit extracts, and outstanding T1
and release fields remain placeholders.

## Draft checks

| Published draft | Fresh build | Main text ends | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf`, rc 0 | p. 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Extracted text matched the published PDF in both builds. Rendered page 8 in each and checked
the transition from limitations to references. The logs have zero undefined citations,
undefined references or multiply defined labels and nine existing overfull boxes each.
`FinalPaper` stopped at the unset gate outcome as expected. `git diff --check` passed.
The claim-to-table sheet SHA-256 is `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to rebuild from temporary copies of the assigned worktree after confirming
that all 27 paper files and all 15 locally modified paths match published main byte for byte.
The assigned worktree's linked Git metadata is read-only, so fetch and report publication
used a temporary Git directory. This report introduces no manuscript unit for review.
No cluster job was submitted and no sealed data was read.

## Next round

- **Screening STOP.** `compute/20261127-22`, authorised run `smeas-20261123-a`, stopped at the
  worker-runtime probe in attempt `SMEAS_EVIDENCE_20261127T1032Z`. Strict preflight passed and
  the `python`/ `python3` path comparison failed. Compute records zero of 10,164 runs and no
  live process. STOP record branch `compute-screen-measure-stop-20261127` @
  `30781f0b8a65c0653585dbb897a1fde6d3d072eb`, record SHA-256
  `1edf4b30c87417063714cccb48465994a0370cff5621e9367ca1cb1e01910169`. Check coordinator and
  author disposition of the signed command or reviewed probe binding before any new attempt.
  The signed note and companion SHA-256 still match PLAN:
  `96188e7c8d0ff92990f8ac821ad3608838cbb59226096064072a627061cd88e0` and
  `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
- **D.3 freeze blocked.** Revision 4 step (5) confirmed the G1 terminal fix. Full review was
  **NOT ACCEPTED** because production G1 summaries failed G7's schema and G6 omitted per-keep
  audits. The binding-only diff was **ACCEPTED**. The published review SHA-256 is
  `47785eac7fe5bbf1bfbf3117974fab5660e23c8d4c39194eef30e2f099a9257b`.
  `compute/20261127-23` delivered integration at `1bd7f3d6d724a9d2653fd06807e639a5ef4f4129`;
  focused tests 156 passed with 18 subtests, independent review and full-suite base comparison
  pending per Compute. Check accepted integration, reviewed merge and the repeat step (5),
  then screening disposition, revision 4 freeze, authorised per-arm smoke and stage authorisations.
- **Running elsewhere.** Compute `461fdec79c3a4fcc1816207e7a73936dada94fa1` at 11:40 UTC
  records TASL-2 expansion `g1b-x-tasl-20261126-a`: ETTh1 and MetaMaze sealed, Forest Cover PID
  `106573` in joint runs on CPUs 4–7, Titanic PID `106578` in the split stage on CPUs 12–15.
  Check the remaining seals, assembly and per-node determinism. Forest Cover holds the CPU
  lease needed by the houseprice rerun `compute/20261127-15`, whose waiter exited before launch.
- **G.5 and offline evidence blocked.** The combined P11 record and final render, binding,
  review and publication are outstanding. Compute also reports that its current P11 command
  refuses the unfilled launch `run_id`. Check the coordinator's route for that validation
  before rerunning the TASL-2 P11 checks. The gate then waits for eligible T1 labels, the
  train/dev release, reviewed target-consumer and preregistration bindings, trained and
  calibrated frozen arms, and signed test releases. Writer resumes when the authorised
  result extracts arrive, including the applicable C1 release.
- **Ada and scheduler idle for these tasks.** Probe `trackp-p4-probe-20261125-a` is complete.
  The two 0.8B bases passed and the two 4B bases reached the signed OOM STOP. Check
  `local/20261127-18` for the reviewed 4B checkpointing unit, then Compute's new synthetic
  probe receipt before the phase-1 note. H200 `760065` and HTCondor preflight jobs
  `760148`, `760149`, `760152` were removed. `compute/20261127-12` still has no match
  on an eligible ETP L40S or TOpAS A100.
