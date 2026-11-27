# Paper B writer round close · 27 November 2026

Writer is idle at research base `1f1b5d412e45f13243b7232206ae762657ddb333`. The coordinator queue at
`4dea2050195cd146e61beb389d7bbed21c245c60` has no runnable writer card. The next writer item is the result
tables (runbook §3 item 4). It remains pending released evidence and has no task ID. Git ancestry confirms
the earlier deliveries, including the title and trim and the claim-to-table sheet.

| Task | Delivery branch and tip | Review on record | Published merge |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The later title and trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Question, method, result and claim

Which control decisions improve the end of an autoresearch campaign at the same caps of 20 worker runs and
80 manager calls, and by how much? In the published Sweep 1 replay, 3,274 of 4,999 proposals repeated a
configuration. That observation motivates testing the duplicate-skip rule. D.3 compares arms on matched new
campaign instances and measures how much the final configuration improves on the starting configuration
over ten fresh audit seeds, in units of the node's reference standard deviation. A0R − A0 measures what
skipping duplicates and detectable no-ops adds to the default rule. A2 − A0R measures what the noise-aware
one-step rule adds after those skips. A3 − A2 and A5 − A2 measure what each learned forecast adds. The paired
effect estimates, intervals and declared Holm decisions determine which campaign gains the paper can claim.
The separate offline gate tests one-step utility on logged proposals. D.3b follows arms freeze and its own
authorization under either gate verdict.

The D.3 effects and intervals, offline verdict and effects, C1 rates, realized T1 populations, hardware
and release references remain placeholders. The SGM citation and author approval fields also remain open.

## Both drafts verified

[Manuscript main](https://github.com/dowlingwong/paper_B_manuscript) and the research submodule pin
resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Draft | Build | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---:|---:|---|
| Gate not passed | `latexmk` exit 0 | 8 | 44 | `5596075826c3f1787e211965babbe3bb0376532b91a9de52996a467ff957117e` |
| Gate passed | `latexmk` exit 0 | 8 | 43 | `01b32d2373affb169de00fee333f6edbbc6f4bef430205655ef0591aaaa1ab0c` |

Extracted text matched the published snapshots on every page. Visual checks covered the opening, result tables
and transition to references on pages 1, 7 and 8. Both logs had no undefined citations, undefined references
or duplicate labels. Nine existing overfull boxes remain per draft. The `FinalPaper` check stopped at the
unset gate switch (exit 12). `git diff --check` passed. This round adds a coordination receipt only.
The recorded delivery reviews above still apply.

| Published input or receipt | SHA-256 |
|---|---|
| Sweep 1 replay, `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` | `f39f112c9687f63c6a8c05013b917af847ff1f03a470404942e4fdfea5ac27ea` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 pre-declaration rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Signed second screening re-issue | `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9` |
| Screening STOP manifest, as recorded by Compute | `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9` |

Decided alone to fetch and report with temporary writable Git metadata because the linked worktree's
Git directory rejected the fetch. All 15 modified paths in the assigned worktree matched published main.
They were preserved. The builds used a temporary export of the pinned standalone manuscript. No server
was accessed, no job was submitted and no sealed partition was read.

## Next checks

Status is from the coordinator queue and the latest Compute and Local receipts at
`17a20d28dc2e2b2857fbb634b42f54bbfd417ae8` and `039406281aaf7fcc3032f2d87d7df2f8bdbdb834`.

| Lane | Recorded status and next dependency |
|---|---|
| Screening STOP | `compute/20261127-30`, run `SMEAS_EVIDENCE_20261127T1550Z`, deepthought tmux `smeas_reissue2`, stopped at 15:51:53 UTC. The guard measured 9.87 free CPU cores against the required 10. The run wrote 186 of 10,164 records with zero failures. Compute preserved the scene and reports no analysis. The coordinator routed the retry decision to the author. If authorized, a new run requires a fresh stamp and strict preflight. |
| Expansion G.1b running elsewhere | `compute/20261126-10`, TASL-2 run `g1b-x-tasl-20261126-a`. Titanic PID `106578` was at 84/150 joint runs at 15:33 UTC. ETTh1, MetaMaze and Forest Cover are sealed. Check the Titanic exit and seal, then assembly and per-node determinism before eligible G.5 addenda. |
| Houseprice, Ada P5 and P11 dispatched to Compute | `compute/20261127-33` owns the houseprice and Ada P5 reruns after the reviewed fixes merged. The earlier houseprice run `tasl2-cpuset-mlgym_houseprice-20261127` stopped with two of three required attempts. Ada P5 `compute/20261127-29` stopped at the lease pre-check before GPU work. Check the sequence with Compute, then look for a fresh houseprice attempt, Ada P5 smoke and E0 on the same leased card, and the remaining P11 host records under `compute/20261127-32`. No fresh IDs are recorded. The P.4 phase-1 note waits for accepted P5 and E0 records, timing and the signed spec fill. |
| D.3 blocked | R1-D3-STEP8-HOLD keeps step (8) and campaigns pending on the screening result. If a decision node returns SHARED, the extra arm goes to the author before binding. Check the G6 engineering smoke correction under `compute/20261127-31`, then the declared per-arm smoke and stage authorizations. Prior engineering run `d3-smoke-engineering-20261127-a` provides no campaign evidence. D.3b also requires the frozen arms. HTCondor jobs `760148`, `760149` and `760152` were removed unmatched. Check for an eligible ETP L40S or TOpAS A100 match. |
| G.5 and the offline gate blocked | G.5 waits for the accepted combined P11 host record, final binding and accepted render. Check the houseprice S14 record and the reviewed expansion addenda. The gate follows completed G.5 labels, the train/dev release, reviewed consumer and preregistration bindings, trained and calibrated frozen arms, the required proof checks and signed test releases. The prior P.4 H200 request `760065` was removed unmatched. |
| Paper C E-INT pending on Ada | `compute/20261127-28` awaits staging and engineering smoke on a separate eligible Ada card under Paper B priority. No job ID is recorded. |
| Writer result fill pending | Resume when the authorized D.3, offline gate and C1 extracts arrive. Fill only their supported estimates and intervals and apply the declared readings. |

Publication to main belongs to the coordinator.
