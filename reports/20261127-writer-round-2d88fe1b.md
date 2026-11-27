# Paper B writer round close · 27 November 2026

Writer is idle. Published base `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`, queue
`coord/coordinator` @ `042c19304718a7a218f0b5fafbb363c94e747bff`. All five writer cards are
published. The result-table handoff in runbook §3 item 4 has no task ID yet and waits for released
results. This check updates the handoff after the coordinator merged the D.3 G1 fix.

| Task | Delivery branch and tip | Review on record | Publication |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Manuscript verification

Which decisions improve the final result of an autoresearch campaign under the same caps of 20 worker
runs and 80 manager calls? D.3 pairs arms on the same instances and measures how much the final
configuration improves on the start over ten fresh audit seeds, scaled by the node's reference standard
deviation. The paired estimates and intervals for A0R − A0 measure what the rule layer adds. A2 − A0R
measures what the noise-aware rule adds after de-duplication. A3 − A2 and A5 − A2 measure what each
learned forecast adds. The preregistered offline gate tests whether learned forecasts improve one-step
utility on logged proposals. Claims about the measured effects wait on the corresponding estimates and
intervals. The D.3, offline gate, C1 and pending T1 evidence fields remain placeholders.

| Published draft | Fresh build | Last main-text page | Total pages | Published SHA-256 |
|---|---|---|---|---|
| `main_draft_gate_not_passed.pdf` | `latexmk -pdf`, rc 0 | 8 | 44 | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `main_draft_gate_passed.pdf` | `latexmk -pdf` with `DraftGatePassed`, rc 0 | 8 | 43 | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

The extracted text of each rebuild matches its published PDF. Page 8 in both rebuilds was rendered
and checked at the transition to references. Both logs have zero undefined citations, undefined
references or multiply defined labels and nine existing overfull boxes. `FinalPaper` stopped at the
unset gate outcome. `git diff --check` passed. The published claim-to-table sheet SHA-256 is
`23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to verify all 15 locally modified paths against published main byte for byte and build
from a temporary archive of that exact base. Temporary Git metadata was used because the assigned
worktree's shared Git metadata is read-only. There was no new manuscript unit, task branch or review.
No job was submitted and no sealed partition was accessed. The coordinator owns publication to main.

## Next round

- **D.3 evidence pending.** `compute/20261127-20` delivered `compute-d3-g1-final-20261127` @
  `ff244366b7168a210a302b37deda5438f83c9e6e` with accepted review `d5acf3ab`, merged at `2d88fe1b`.
  Compute recorded 161 focused passes, 18 subtests and identical full-suite failure/error IDs at base
  and tip. The prior full step (5) verdict remains NOT ACCEPTED. Check `local/20261127-17` for the
  repeat at the merged pin, including both reproductions, full review and diff re-check. Screening
  still needs signature, publication and measurement. Rev 4 freeze, per-arm smoke and stage
  authorisations precede campaign launch. D.3b also needs frozen arms.
- **TASL-2 expansion running in the last recorded sample** (`coord/compute` @ `b4b33527`, 08:53 UTC).
  In `g1b-x-tasl-20261126-a`, ETTh1 and MetaMaze were sealed. Forest Cover PID `106573` (279/460,
  CPUs 4–7) and Titanic PID `106578` (236/460, CPUs 12–15) were running. Check the remaining seals,
  assembly and determinism decisions under `compute/20261126-10`. Houseprice waiter `208315` exited
  before launch. The houseprice retry and remaining TASL-2 P11 checks need CPUs 0–7. Forest Cover
  held the remaining lease in that range.
- **Offline gate and C1 pending.** G.5 waits for the remaining P11 checks, final render and binding,
  accepted review and note publication. The gate waits for eligible-node labels, T1 train/dev release,
  reviewed target-consumer and preregistration bindings, trained and calibrated frozen arms, and the
  signed test releases. Fill the result fields only after the applicable authorised extracts arrive,
  including the C1 extract under its post-freeze rules.
- **Ada and HTCondor.** The Ada engineering probe `trackp-p4-probe-20261125-a` finished. Both 0.8B
  bases passed and both 4B bases reached the signed out-of-memory STOP at micro-batch 8. The 4B route
  waits on the author and the P.4 phase-1 note still needs its harness binding. H200 request `760065`
  and D.3 preflight jobs `760148`, `760149` and `760152` were removed after no match. Check
  `compute/20261127-12` for the next eligible L40S or A100 match.
