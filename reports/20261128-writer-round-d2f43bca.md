# Paper B Writer round at d2f43bca

Writer is idle. The research base is `d2f43bcae0df1087ac584ba4af910f890bfd57a9`,
the queue is `f5c20e9363fcd94b488bd6930d52319abf3daec3`, and the report
parent is `95ea6a404a4bb8ed7216332530f4b96ac638d701`. Runbook §3.4 is
pending an evidence release and a Writer card.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/f5c20e93/STATE.md#writer)

| Task ID | Delivery branch and tip | Review on record |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D re-check ACCEPT WITH MINOR. Corrections applied. The subsequent title and trim have no separate review verdict. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S ACCEPT WITH MINOR. Corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D re-check ACCEPTED. |

All four tips are ancestors of the research base. The restructure contains the
shared-card, proposal-budget and schedule changes from `writer/20261126-02`.
All 15 modified files in the assigned worktree match the published research
tree byte for byte. `git diff --check` passed. This round involved verification
only, so the review verdicts in the table apply to prior deliveries.

## Research question and measured evidence

Which control decisions improve the final configuration when every campaign
has the same budget? The published sweep-1 replay found that 3,274 of 4,999
proposals repeated an already evaluated configuration. That result establishes
that repeats were common and motivates measuring the cost of spending runs on
them. D.3 compares controllers on matched instances with 20 worker runs and
up to 80 manager calls per campaign. It measures the gain from the starting
configuration to the final one with an audit on ten fresh seeds. A0R versus A0
estimates the benefit of skipping repeats and detectable no-ops, A2 versus A0R
estimates what the noise-aware rule adds, and A3 and A5 versus A2 estimate what
the learned forecasts add. The campaign claims await paired estimates, 95%
intervals and the declared Holm decisions. The preregistered offline gate
separately measures the one-step gain on logged proposals.
[Sweep-1 replay counts](https://github.com/dowlingwong/Agent_paper_B/blob/d2f43bca/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 revision 5](https://github.com/dowlingwong/Agent_paper_B/blob/d2f43bca/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft checks

Standalone manuscript `main` and the research pin both resolve to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The two README build commands ran
in a clean scratch clone with the commit timestamp as `SOURCE_DATE_EPOCH`.
Ghostscript confirmed the page counts, and pages 1 and 8 were rendered and
inspected in both drafts. The references start on page 8.
[Published manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | latexmk exit | Last main-text page | Total pages | Local PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `4e49fa00a322592ed09ba045198f6c67ae8d677cba0a9178e7e06e0129a19e36` |
| Gate pass | 0 | 8 | 43 | `e3e4ba0889477996f9c406c8d9ad93b9f8902b855d002932b610d7e2b77f9d41` |

Both logs have nine existing overfull boxes and zero undefined references,
undefined citations or multiply defined labels. The final-paper build exited
12 at the unset gate switch. Placeholders remain for C1 rates, offline gate
estimates and verdict, audited D.3 effects and intervals, realized T1 scope,
and author wording. The manuscript still cites pre-declaration revision 4 in
the appendix. Its next assigned revision should cite the applicable frozen
revision after the launch binding is settled.

| Published source | SHA-256 |
|---|---|
| PLAN with §10 | `33587c266f61f83764ea26f0cba95b5f8e5133790b47d499a4d28b3693540a26` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Sweep-1 replay counts | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |
| G.5 primary launch note | `4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59` |

## Jobs and dependencies for the next round

| Lane | Last recorded state and next owner |
|---|---|
| G.5 main | Compute observed `c3_t1_labels_20261128` running from `2178bc6e` at 20:43–20:46 UTC. TASL-7 proposer PID `3096456`, TASL-2 wave-1 wrapper PID `1762417` and worker PID `1762429` for `mlab_cifar10/campaigns-wave1/attempt-1`. Compute checks its attempt and advances to `audits-wave1` after a clean completion. |
| G.5 addenda | Titanic, MetaMaze, ETTh1 and Forest Cover await the TASL-2 CPU sets and G.5 leases. The launch bases are `88edb84f`, `4ee43037`, `e9441f03` and `f96069d0`. No attempt IDs are recorded. |
| D.3a | `d3a-prod-20261128-a` is allocated and unused. R1-D3-REV6 authorizes the direct TASL-2 environment change. Local `20261128-18` prepares it for review, signature and freeze. Compute's endpoint guard is delivered and accepted with minors. Step (8), exact-launch P10/P11, P9 and publication remain ahead of a production start. |
| D.3 batch, D.3b and D.3c | The previous HTCondor job `760158.0` is closed. Compute records the next exact-request pool check at or after 21:16:04 UTC. D.3b awaits frozen arms and its authorization regardless of gate verdict. D.3c also needs G.5 completion and its own authorization. |
| P.4 phase 1 | Compute delivered verified signed spec commit `fcfd63f3f6e57c64c7f9c5a233a937dbfbbf6576`. Local fills P3 and the coordinator publishes before training. No training job ID is recorded. |
| Offline gate and Writer | The gate waits for released G.5 train/dev labels, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. Writer checks the queue for C1, gate or audited D.3 releases and dispatch. The next assigned edit fills the published evidence, builds both drafts and goes through fresh review before coordinator publication. |

[Compute launch and P.4 report](https://github.com/dowlingwong/Agent_paper_B/blob/1c4312e7/reports/20261128-43-g5-launch-p4-key.md) · [D.3a endpoint review](https://github.com/dowlingwong/Agent_paper_B/blob/b203f51d/reports/20261128-42-d3a-template-checks.md) · [Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/f5c20e93/AUTHOR.md)

Decided alone to use temporary writable Git metadata for the fetch and report
because the assigned worktree's shared `FETCH_HEAD` is write-restricted. Writer
has no active jobs and made no manuscript edits. No job was submitted and no
sealed partition was opened.
