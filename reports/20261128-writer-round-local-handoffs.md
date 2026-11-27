# Paper B writer round — 28 November 2026

Writer is idle. Published research base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`,
queue `20837ee4cd4a293bd3d760ca0d4d534d29372c1e`, and manuscript main and research pin
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The five existing cards are published.
The next result-table handoff is runbook §3 item 4, pending an assigned task ID and released evidence.

| Task ID | Delivered research branch and exact tip | Published merge | Recorded review |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

Paper B asks which decisions leave the search with a better final configuration at the same budget.
In the Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration already evaluated. This
measures how often repeats appear and motivates testing whether skipping them improves the final result.
D.3 matches starting points and instances at a cap of 20 worker runs and 80 manager calls, then compares
the final configuration against the start on ten fresh seeds. A0R versus A0 estimates the gain from
skipping repeats and detectable no-ops. A2 versus A0R estimates what the noise-aware decision rule adds.
A3 and A5 versus A2 estimate what the learned forecasts add. Paired effects, intervals and declared
Holm decisions will determine the claims. The offline gate separately measures one-step decision utility
on logged proposals. Campaign estimates and intervals, gate verdict and effects, full C1 rates, realised
T1 scope and evidence bindings remain placeholders.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/15fe05b0/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

## Tests and builds

Both drafts were rebuilt with the standalone repository's `latexmk` commands.

| Draft | Exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `1c480b2409b9c3de902d85e5ba019367a31619143324542200a8164635ba0202` |
| Gate-pass preview | 0 | 8 | 43 | `7135470f1ea6743a41c6fd7237c90975adb674aaa9ae4707e290551fbb5b39ba` |

Every page's extracted text and 100 dpi render matched the published pre-migration PDF. Pages 1 and 8
in both variants were inspected. References begin on page 8. Each log has nine existing overfull boxes
and zero unresolved citations, references or duplicate labels. The `FinalPaper` guard exits 12 at the
unset gate switch. Task ancestry and `git diff --check` passed. Review verdicts above are the existing
task reviews. This round produced a status report and verification.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| PRE-SPLIT v2 amendment | `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7` |
| Screening second re-issue, former deepthought route | `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9` |

## Handoffs and next checks

- **Local is idle after two accepted handoffs.** `local/20261127-31`, screening on deepthought2,
  is at `123d8bbeb1e8a57a906e59be4d82e98fda73300e`. Its tier-E review hash is
  `dc7b0d63bdda07377f2bf41fdc15b1f88cfe3b8d3aa5d19739a037722f1eaadb`. The reviewed draft note
  hash is `84381da7a74f9406b60383c4b07682a4baee6c549cd1551ca8090a0bdc8cebc0`.
  `local/20261128-01`, the G.5 expansion D6 copy variant for `g1b-x-tasl-20261126-a`, is at
  `e1e1a30903e64db7d22d945578d544766f861ea6` with accepted tier-E review hash
  `de2219e1a23b26ca45895274ffc14ec3b7f59439f709251ebaeac8c22001f391`.
  Check coordinator publication of both units, the approved screening note, and the Compute receipts
  for the strict screening preflight and independently reviewed D6 copy.
  [Local round report](https://github.com/dowlingwong/Agent_paper_B/blob/57d9deff7b8282e0e391b3475c9f9476602902ce/reports/20261128-local-round-15fe05b0.md)
- **Compute status.** Public `coord/compute` is still `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`.
  The local Compute pane displays “waiting for 1 background job” after its 22:35 CET report
  (`coord-compute` @ `ebb7354ba666aabdfd313f959059f8e8ee7899ca`). Live scheduler status remains
  unverified. Latest recorded screening attempt `SMEAS_EVIDENCE_20261127T2125Z` stopped at
  444/10,164 with zero failed rows. Check `compute/20261128-02` for the report gap and
  `compute/20261127-38` for the old retry closure, then the new deepthought2 stamp. D.3 step (8)
  waits for the screening outcome and any required SHARED disposition. Preflight IDs `760148`,
  `760149` and `760152` were removed unmatched. Check `compute/20261128-03` for the new job ID
  and `compute/20261128-04` for receipts on `759624`, `759625` and `760065`.
- **G.5 and the gate.** Check the P11 host tests under `compute/20261127-32` and
  `compute/20261128-05`, `compute/20261127-36` for the D6 copy, and `compute/20261127-33`
  for a fresh S14 attempt (previous `tasl2-cpuset-mlgym_houseprice-20261127` has two seals,
  three required). G.5 then needs the final binding, render, review and publication. The gate
  awaits labels, the train/dev release, reviewed consumer and preregistration bindings, frozen
  calibrated arms, proof checks and explicit test release.
- **P.4 and Paper C.** Ada P5 `p5_20261127_b/e0e` passed the smoke and missed the E0 tolerance with
  runs per second 25.86% below the October reference against a 10% allowance. Check
  `compute/20261128-01` for the same-code TASL-7 run ID and equivalence/timing disposition.
  Accepted equivalence and timing carry-forward are required for phase 1 and A5 SFT. E-INT
  `compute/20261127-28` still needs an eligible Ada lease and smoke receipt.
- **Writer next action.** Take the first ready result card from the published queue, branch from
  [manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5),
  use the signed release and audited extracts, rebuild both variants and obtain the required
  independent review. The coordinator publishes the manuscript and advances the research pin.

Decided alone to preserve the 15 modified paths in the assigned worktree. Each matches the published
pre-migration snapshot byte for byte. The linked Git directory refused the fetch write, so fetches
and this report used temporary writable Git metadata. The builds used a temporary archive of the
published standalone manuscript. No job was submitted and no sealed partition was opened.
