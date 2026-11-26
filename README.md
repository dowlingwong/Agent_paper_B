# Agent Paper B — AutoML as dynamic algorithm configuration

> Local layout preview. Use the [path map](docs/PATH_MIGRATION.md) to browse this checkout. Use the main checkout for experiment runs.

An LLM proposes edits to a training setup. A control policy decides which edits to evaluate, keep or verify
under worker-run and manager-call budgets. Worker evaluations are noisy. Independent fresh-seed audits measure
the improvement of the final configuration over the start.

| Project | Current question | Start here |
|---|---|---|
| Paper B | At a matched budget, what do de-duplication, noise-aware rules and proposal-level learning each buy? | [Paper B plan](canon/PAPER_B_PLAN.md) and [manuscript](papers/) |
| Paper C | When is budget-aware one-step control enough, and when do current actions change future search enough to justify a longer horizon? | [Paper C plan](canon/PAPER_C_PLAN.md) and the [development branch](https://github.com/dowlingwong/Agent_paper_B/tree/paperc-esyn-scaling-20261122/paperC) |

## Start here

- [Canonical plans, compute and agent roles](canon/README.md)
- [Next-phase AutoML as DAC runbook](docs/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md)
- [Documentation index](docs/README.md) and the [dated decisions in PLAN §10](docs/PLAN.md#10-open-decisions)
- [Live task queue and state](https://github.com/dowlingwong/Agent_paper_B/tree/coord/coordinator)

The dated PLAN decisions govern execution. The short files in `canon/` summarize them. The next-phase runbook
defines the work sequence from design through audit and writing. Signed evidence notes, reports and reviews
live in `docs/`.

## Status as of 26 Nov 2026

Both T0 sweeps are audited and their train/dev labels are released. The offline gate is unread and the
matched-budget D.3 campaigns are pending. By the 26 Nov decision, frozen A3 and A5 run in D.3b regardless of
the offline gate outcome. The eight T1 noise floors are sealed and the G.5 label runs are in preparation.
Paper C is at the controlled-environment and development-census stage. Its chosen interaction-rich census
candidate is fixed-memory, variable-length sequence training.

## Repository layout

| Path | Purpose |
|---|---|
| [`canon/`](canon/README.md) | Paper plans, compute inventory and agent SOUL files |
| [`docs/`](docs/README.md) | Runbooks, authorizations, reports, reviews and decision history |
| [`papers/`](papers/) | Paper B LaTeX source |
| [`paperb/`](paperb/), [`sweep2/`](sweep2/), [`tools/`](tools/) | Experiment and audit code, batch wrappers and tools |
| [`results/`](results/) | Committed outputs and provenance with evidence class recorded |
| [`archive/`](archive/README.md) | Historical paper route, manuscript and legacy code |
| [`_to_delete/`](docs/recovery/c3-fixtures-20261031/README.md) | Staged historical files, some of which are pinned recovery inputs |

Host deployments use the pinned [autoresearch harness](https://github.com/dowlingwong/autoresearch_harness).
[COMPUTE.md](canon/COMPUTE.md) records host capabilities, availability snapshots and the current routing.
Use the project's published branch and signed launch note when an experiment requires them.

## Checks

```bash
make r1-test AR_HARNESS_ROOT=../autoresearch_harness
make r1-e2e
make legacy-test LEGACY_PY=/path/to/python3.13
```

For branch retirement and archive provenance see [the hygiene audit](docs/reports/REPO_HYGIENE_AUDIT_20261126.md)
and [BRANCHES.md](docs/BRANCHES.md).
