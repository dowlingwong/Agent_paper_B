# writer/20261127-01 — external sources and 27 November decisions

**Delivered, Tier D.** Base `8b01ef6a7d2e0687f96022c2f48f12e999d78ef9`. Task branch
`writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769`.
A three-way merge check against published `main` `29099c4b` was clean.

## Result

1. Both NeurIPS abstracts support the qualitative findings. OpenReview returned a verification challenge on both PDFs, so the introduction and related-work appendix drop the reported figures. The claim sheet records the two sources, scope and removal.
2. The labelling method gives the seven signed T1 tail choices and their pre-label basis. The T1 expansion text separates eligible MLGym nodes in the arms and gate from separately reported 1GC tasks.
3. The design gives the eight D.3a contrasts and five D.3b contrasts (six with A6), Holm at 0.05 within each, and the declared first-step sensitivity in units of the assumed paired-difference standard deviation. The headline follows the signed attribution rule and handles a statistical gate STOP without a verdict.
4. The deviations table gives the five 27 November rows, including the staged P11 host checks and the disjoint D.3 verify-seed requirement. The author settled the design; the frozen pre-declaration, pin and hashes still wait on its required checks.
5. All missing campaign, gate, T1 label and C1 evidence remains in placeholders. No sealed data was read and no experiment or server job was submitted.

## Builds and hashes

| Deliverable or source | Check | SHA-256 |
|---|---|---|
| `papers/r1/build/main_draft_gate_not_passed.pdf` | rc 0, main text ends on page 8, 44 total pages | `d1645eda6d56e8987e48f72609101a4b398c1ac577447ed2a71ee891a5805097` |
| `papers/r1/build/main_draft_gate_passed.pdf` | rc 0, main text ends on page 8, 43 total pages | `d974f6aeb25827ca8fe54f7410366768618c4b15236612997ccf689a2f5a295f` |
| `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md` | source audit and decisions checked | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| D.3 pre-declaration revision 4 draft cited by R1-D3-PREDECL-R4 | source at `bd406db9`, hash matched | `bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` |

Both drafts built using `latexmk -pdf -interaction=nonstopmode -halt-on-error`; the passed draft sets
`-usepretex='\def\DraftGatePassed{}'`. References start on page 8 in both. No missing citation, missing reference
or duplicate label in the final compiler logs. Visual review covered the changed main-text readings, tables and
appendix design. Pre-existing appendix line overflow remains. Also built and checked the gate-STOP preview
(38 pages), D.3b stopped (42 pages), and rule-layer-only with gate non-pass (44 pages). The final-paper build
stopped at the unset gate switch as expected. `git diff --check` passed. Manuscript and bibliography only, so the
`r1/tests` suite was outside this unit.

## Independent review

Fresh agent, **ACCEPTED on re-check**. First pass requested preserving the learning clause and tier reference in
the rule-layer-only interpretation, using descriptive mechanism language, identifying component contrasts
without overstating attribution, and tightening T1 eligibility, P11 and D.3b STOP wording. All were addressed
before re-check. The verdict covered the manuscript sources and claim sheet. The writer verified the PDF builds.

Decided alone: remove the two figures once the PDF checks were blocked; retain the abstract-supported descriptions;
put the statistical design detail in the appendix; use a temporary Git directory with the assigned worktree so
Git could fetch and commit under the workspace permissions.

## Next

Coordinator can merge the task branch. The writer queue was refreshed at `coord/coordinator` `96fbfd2d`.
The three 26 November writer cards are already published through `4490a0a9`. No other writer card is ready.
Result tables wait for the release rows and audited output. The primary gate additionally waits for G.5 labels and
the train/dev release, arm selection, calibration and the arms-frozen record. D.3a waits for the screening evidence,
G1/G2 and verify-seed work, final review and the frozen pre-declaration, and the per-arm smoke. D.3b also waits for
the frozen arms. G.5 publication waits for the Student-t scope/scale decision, the reviewed label path and final
render and host checks.

The latest compute report (`coord/compute` `c962d831`) records expansion `g1b-x-tasl-20261126-a` on TASL-2.
ETTh1 was sealed. MetaMaze (PID 106579), Forest Cover (106573) and Titanic (106578) were still running.
Houseprice CPU-set driver PID 208315 was waiting for TASL-2 CPU-set leases. Pool P.4 job `760065` was idle.
Screening smoke remains at its data-cache STOP pending merge of `cb684870` and the compute repeat card.
