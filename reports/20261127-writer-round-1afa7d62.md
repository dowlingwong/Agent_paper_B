# Paper B writer round at 1afa7d62

Writer is idle. The research base is `1afa7d62ffd98709a100de6e725d123cbc272a73` and the
coordinator queue is `ac90b07d6265e7d49fac98865313ad4c36fdc447`. All five writer cards in
`tasks/writer` have published deliveries. The next writer item is the result-table handoff
in runbook §3 item 4. It awaits released evidence and a card. The published manuscript
branch is [paper_B_manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, which matches the research submodule pin.

| Task ID | Task branch and tip | Published merge | Review on record |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

## Measurement and claims

The paper asks which control decisions improve a campaign's final configuration when each arm gets
20 worker runs and at most 80 manager calls. Sweep 1 logged 3,274 repeated configurations among
4,999 proposals. That measured frequency motivates testing duplicate skipping. D.3 pairs campaigns
on fresh instances and measures the final configuration's gain over the start on ten fresh audit
seeds. A0R minus A0 measures the effect of skipping duplicates and detectable no-ops. A2 minus A0R
measures the gain from adding the noise-aware decision rule. A3 and A5 each compared with A2 measure
the contribution of their forecasts to campaign gain. The paired estimates, intervals and signed
decision rules determine the claims that can be made. The preregistered offline gate measures
one-step decision utility on logged proposals. [Published Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/1afa7d62/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

D.3 effects, intervals and outcome wording, the gate verdict and estimates, full C1 audit rates,
realized T1 scope and evidence bindings are still placeholders. The published G.5 expansion binding
enables per-node launch and release checks. It contributes no released G.5 labels or campaign result.

## Draft checks

| Draft | Fresh `latexmk` exit | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `4e23c217977eff19622190fdebf4f4195a74c629fb4fb512627aea003ada1571` |
| Gate-pass preview | 0 | 8 | 43 | `963e00fa94c6603dae0e22785da39d5fcc26b9d7bd55c5f2ea03e1a19a6a67af` |

All pages in both builds match the published research snapshots in extracted text and raster output.
Pages 1 and 8 were inspected in each variant. References start on page 8. The logs have nine existing
overfull boxes per draft and no undefined citations, undefined references or duplicate labels.
The `FinalPaper` guard stops at the unresolved gate switch (exit 12). Task ancestry and
`git diff --check` passed. This was a verification round with no new manuscript or code change,
so it has no new review verdict or code-suite run.

Verified published SHA-256 values:

- Claim-to-table sheet `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.
- Frozen D.3 revision 4 `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`.
- Signed PRE-SPLIT v2 amendment `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.
- Signed screening note, second re-issue `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9`.
- G.5 expansion binding re-check, ACCEPTED at tier E, `8c398d2e614c79f38d2cd876a78cf4661704f188513f6a25288d2041c1aef836`.

Decided alone to preserve all 15 modified paths in the assigned worktree after checking that each matches
published main byte for byte. The sandbox denied the linked worktree's FETCH_HEAD write. Fetch and reporting
used temporary Git metadata, and the build used an archive of the pinned standalone manuscript. No evidence
job was submitted and no sealed evidence was read.

## Next checks

- **Screening and D.3.** The latest reported screening scene `SMEAS_EVIDENCE_20261127T1550Z`
  (tmux `smeas_reissue2`) stopped at 186/10,164 runs, zero failed. STOP manifest SHA-256
  `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9`.
  Check `compute/20261127-35` for a new stamp and a strict preflight with at least ten free deepthought
  cores. D.3 step (8) waits for the screening result and any required SHARED decision. HTCondor
  preflight jobs `760148`, `760149` and `760152` were removed unmatched. Check for an eligible matched
  layout, the per-arm smoke and the D.3a/b authorizations. D.3b also needs frozen arms.
- **G.5.** The base note awaits combined P11 (`compute/20261127-32`), a fresh accepted houseprice S14
  (`compute/20261127-33`), final binding, check and review. The earlier houseprice scene
  `tasl2-cpuset-mlgym_houseprice-20261127` has two of three seals. A fresh run ID is pending.
  All four expansion G.1b nodes sealed with determinism PASS in `g1b-x-tasl-20261126-a`. The per-node
  switch is published at `1afa7d62`. Check `compute/20261127-36` for the reviewed D6 copy, then
  the author P10 declarations and each node's signed and checked launch binding.
- **Ada.** The latest Local pane poll reported Ada P5 E0 active as `p5_20261127_b/e0e`, PID `5542`.
  Check `compute/20261127-33` for accepted equivalence and timing receipts and phase-1 note publication.
  H200 request `760065` was removed unmatched. Paper C's E-INT card `compute/20261127-28` waits for
  the development smoke and an eligible Ada lease. No E-INT run ID is recorded.
- **Writer.** The offline gate is unread. Check the completed eligible G.5 labels, train/dev release, reviewed
  target consumers and preregistration bindings, trained and calibrated frozen arms, proof checks and test
  release. C1 waits for the applicable post-freeze release. Branch from the published manuscript tip for the
  next routed result card, bind each changed cell to its released source, rebuild both drafts and obtain
  independent review. The coordinator publishes the manuscript revision and advances the research pin.

Job status is from the queue and the fetched reports through Compute `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`
and Local `a51597b5e740a9daaf8551da9d4c9c3d6d69689c`.
