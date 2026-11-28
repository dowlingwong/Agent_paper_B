# Paper B writer round at adbd7020 — 28 November 2026

Writer is idle. The published research base is `adbd7020b174e9f1c6fecde01544842645bcdb77`.
The queue is `d57c42962fc711a8bab2b4f7217cf7fb641b010d`. All five writer cards have published
deliveries. The next handoff is runbook §3 item 4, result tables. It awaits released evidence and
an assigned task ID. The [standalone manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
is at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, matching the published research pin.

| Task ID | Published research delivery branch and tip | Merge | Recorded review |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

## Question, measurement and claim

Which decisions leave an AutoML search with a better final configuration at the same budget, and by how much?
In the Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration already evaluated. The tally
motivates testing a rule that skips repeats and detectable no-ops. The current draft still marks this
tally for verification. [Published Sweep 1 replay, §2](https://github.com/dowlingwong/Agent_paper_B/blob/adbd7020/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md#2-b2-audit-plan)

D.3 compares controllers on the same starting configurations and instances with up to 20 worker runs
and 80 manager calls per arm. Ten fresh seeds measure how much the final configuration improves over the
start. A0R versus A0 estimates what skipping repeats and detectable no-ops adds. A2 versus A0R estimates
what the noise-aware decision rule adds. A3 and A5 versus A2 estimate what the learned forecasts add.
The paired effects, intervals and declared Holm decisions will support the campaign claims. The offline
gate separately measures one-step decision utility on logged proposals. Campaign estimates, intervals
and decisions, the gate verdict and effects, full C1 audit rates, realised T1 scope and evidence bindings
remain placeholders. [Frozen D.3 rev 4](https://github.com/dowlingwong/Agent_paper_B/blob/adbd7020/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md)

## Both drafts rebuilt from the standalone pin

| Draft | latexmk exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `fb6192fcabb6609355adc0f54f7b527fbf2b79960d860afc38e2e5e0f0837bbc` |
| Gate-pass preview | 0 | 8 | 43 | `3f6307b24feec3dbf4ffb5583f4c72f744f1309faa9325cf60632b7d69f3e714` |

Extracted text and 100 dpi page renders match the published pre-migration PDFs for every page. Pages
1 and 8 were inspected in both variants. References begin on page 8. Each compiler log records nine
existing overfull box warnings and zero undefined references, undefined citations or duplicate labels.
The `FinalPaper` guard exits 12 with the gate switch unset. Task-tip ancestry and `git diff --check`
passed. The reviews above cover the published deliveries. This round produced a status report, so there
is no new manuscript revision or review verdict.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Signed PRE-SPLIT v2 | `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7` |
| Published deepthought2 screening note, third re-issue | `55779a6cfeea13cce99989f6e9680a48a96f0fc5fbc4f4476222cf73d767af9b` |
| Accepted deepthought2 screening review | `dc7b0d63bdda07377f2bf41fdc15b1f88cfe3b8d3aa5d19739a037722f1eaadb` |
| Published houseprice S14 record | `2447e4363976b6d5565f4b49efa079d35989f8cf8a284bb8190f6a43e4665c61` |
| Accepted houseprice S14 re-check | `ac6eac6d83d6d514800fc1bf338e260dbf3ff20746ec04101933fc638c4b2c84` |
| Reviewed P11 refusal record verdict | `d8e4e559cdde4bbc858196880759d151379b3b02245214692b65361490136d5f` |

## Work elsewhere and next dependencies

- **Screening is running per the last Compute receipt.** `compute/20261128-06` launched on deepthought2
  after strict preflight. Stamp `SMEAS_EVIDENCE_20261128T001405Z`, launch PID `3697711`.
  The 00:28 UTC receipt records 277 of 10,164 rows and zero failed. Check for completion, the declared
  analysis and an accepted review. Eight old deepthought attempts are closed with scenes preserved.
  D.3 step (8) waits for the screening result and author disposition if a decision node returns SHARED.
  [Compute launch receipt](https://github.com/dowlingwong/Agent_paper_B/blob/c08a60c45351cda39aec22c0684ee3e4cf4d3fcc/reports/20261128-07-screen-dt2-launch.md)
- **D.3 batch preflight is blocked.** The `compute/20261128-03` check found `Start=false` on the ETP
  L40S and TOpAS A100. There is no new job ID. Earlier `760148`, `760149` and `760152` were removed
  unmatched. Under `compute/20261128-04`, `759624` and `759625` were removed after Idle checks,
  and `760065` was withdrawn. Check for a startable slot, a new preflight ID and in-job checks on the
  pinned image and inputs. The later per-arm smoke and campaign authorizations have their own checks.
  D.3b also needs frozen arms.
  [Published preflight](https://github.com/dowlingwong/Agent_paper_B/blob/adbd7020/docs/r1/reports/d3_preflight_20261128/D3_HTCONDOR_PREFLIGHT_20261128.md)
- **TASL-7 E0 is running per the last Compute receipt.** `compute/20261128-01`, run
  `p5_e0_ref_20261128/e0e`, PID `2289540`, was at 1,008 of 2,000 LoRA steps at 00:28 UTC.
  Check the completed comparison against Ada `p5_20261127_b/e0e`, accepted equivalence and reviewed
  timing disposition before the Ada phase-1 note and A5 SFT. The E-INT development census,
  `compute/20261127-28`, still awaits the bound run instructions, eligible Ada lease and smoke receipt.
  [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/c08a60c45351cda39aec22c0684ee3e4cf4d3fcc/reports/20261128-06-round-status.md)
- **G.5 final render and launch are blocked on P11.** The houseprice S14 rerun
  `tasl2-cpuset-mlgym_houseprice-20261128` passed with three sealed attempts and is published.
  The accepted P11 note-gated refusal record documents the refusals. Local `20261128-02` owns the
  engineering smoke path for the outstanding pre-publication checks, followed by Compute host checks
  and tier-E review. Local `20261126-08` then needs the final commit binding, render and review.
  The expansion D6 copy `compute/20261127-36` waits for publication of reviewed code `35849909`.
  Check the existing ledger before copying `g1b-x-tasl-20261126-a`. The gate waits for G.5 labels,
  train/dev release, reviewed target consumers and preregistration bindings, frozen calibrated arms,
  proof checks and explicit test release.
  [Local STOP](https://github.com/dowlingwong/Agent_paper_B/blob/d50a8d5dfe2a4333c25191ca1f15342e33693a67/reports/20261128-08-g5-render-p11-stop.md)
  [Corrected P11 task](https://github.com/dowlingwong/Agent_paper_B/blob/d57c42962fc711a8bab2b4f7217cf7fb641b010d/tasks/local/20261128-02-g5-p11-engineering-smoke.md)
- **Writer is idle.** On the first ready result card, branch from published manuscript main, populate
  the tables from signed releases and audited extracts, rebuild both variants and obtain independent
  review. The coordinator publishes the reviewed manuscript and advances the research pin.

Decided alone to keep the 15 modified paths in the assigned checkout as found. Each matches the
published pre-migration snapshot byte for byte. The linked Git directory refused the fetch write,
so the fetch and report used temporary writable Git metadata. Builds ran from a temporary archive of
the pinned manuscript. The running statuses are from Compute receipts. This round submitted zero jobs
and opened zero sealed partitions.
