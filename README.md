# Agent Paper B — AutoML as dynamic algorithm configuration

An LLM proposes edits to a training setup. A control policy decides which edits to evaluate, keep or verify
under worker-run and manager-call budgets. Worker evaluations are noisy. Independent fresh-seed audits measure
the improvement of the final configuration over the start.

| Project | Current question | Start here |
|---|---|---|
| Paper B | At a matched budget, what do de-duplication, noise-aware rules and proposal-level learning each buy? | [Paper B plan](canon/PAPER_B_PLAN.md) and [manuscript](https://github.com/dowlingwong/paper_B_manuscript) |
| Paper C | When is budget-aware one-step control enough, and when do current actions change future search enough to justify a longer horizon? | [Paper C plan](canon/PAPER_C_PLAN.md) and the [development branch](https://github.com/dowlingwong/Agent_paper_B/tree/paperc-esyn-scaling-20261122/paperC) |

## Start here

- [Canonical plans, compute and agent roles](canon/README.md)
- [Next-phase AutoML as DAC runbook](docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md)
- [Documentation index](docs/r1/README.md) and the [dated decisions in PLAN §10](docs/r1/PLAN.md#10-open-decisions)
- [Live task queue and state](https://github.com/dowlingwong/Agent_paper_B/tree/coord/coordinator)

The dated PLAN decisions govern execution. The short files in `canon/` summarize them. The next-phase runbook
defines the work sequence from design through audit and writing. Signed evidence notes, reports and reviews
live in `docs/r1/`.

## Start the Paper B workers

This guide assumes the Mac checkout already has the locally provisioned launcher at
`tools/start_workers.py`. From that checkout, run `python3 tools/start_workers.py`. The launcher fetches `origin`, creates a separate
worktree for each worker beside the repository under `agent_paper_B-workers/`, and sends each worker an initial
prompt to read the published queue. Worktrees start from `origin/main`. Workers put deliverables on task branches
and reports on their role branches. Later launches reuse live sessions and worktrees. The launcher locates the
recorded Coordinator even under another tmux name, or resumes that same Claude session with Remote Control.
The coordinator breaks the [next-phase runbook](docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md#7-dispatch-and-run-the-queues)
into task cards and keeps one ordered queue per role in `STATE.md`. Workers take the next ready card immediately
after a task and check again every 30 minutes when idle.

| Role | Model | Reasoning effort | Client and session |
|---|---|---|---|
| Coordinator | Claude Opus 5.5 | Session setting | Claude Code, `paperb-coordinator` |
| Compute | DeepSeek Flash (`deepseek/deepseek-flash`) | Provider default | OpenCode, `paperb-compute` |
| Local / Implementer | GPT-6.2 Sol (`gpt-6.2-sol`) | High | Codex CLI signed in with ChatGPT, `paperb-local` |
| Writer | GPT-6.2 Sol (`gpt-6.2-sol`) | High | Codex CLI signed in with ChatGPT, `paperb-writer` |
| Design | Selected for each handoff | Session setting | Existing writer or coordinator workflow |

Configure Claude Code sign-in, connect [DeepSeek in OpenCode](https://api-docs.deepseek.com/quick_start/agent_integrations/opencode/),
and sign in with ChatGPT in Codex CLI before launching. `codex login status` shows the active sign-in method.
For a handoff, `python3 tools/start_workers.py --stop-legacy` waits for the old Local and Writer turns and their
subagents to finish, checks their worktrees are clean and panes detached, and exits both Claude workers. Start
the replacements with `python3 tools/start_workers.py --role local --role writer`. The launcher reuses their
worktrees. Use `--role compute` to start or retry Compute. Use `--compute-model`, `--local-model` or
`--writer-model` to select the corresponding client's model ID.

Use `tmux attach -t paperb-compute` from a normal terminal or `tmux switch-client -t paperb-compute` from inside
tmux. Press `Ctrl-b` then `s` to switch sessions, or `Ctrl-b` then `d` to detach. A worker pane stays available
after the client exits, so you can inspect startup errors. Use the Coordinator's session name from the launch output.

To see the same coordinator in **Claude App → Code**, run `/remote-control Paper B Coordinator` inside its
Claude session, then confirm the session appears under that name from the same Claude account.

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
| [`docs/r1/`](docs/r1/README.md) | Runbooks, authorizations, reports, reviews and decision history |
| `papers/manuscript/` | Submodule pin for the reviewed Paper B revision in [paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript) |
| [`papers/r1/`](papers/r1/) | Paper B manuscript snapshot from before the migration |
| [`r1/`](r1/), [`sweep2/`](sweep2/), [`tools/`](tools/) | Experiment and audit code, batch wrappers and tools |
| [`results/r1/`](results/r1/) | Committed outputs and provenance with evidence class recorded |
| [`archive/`](archive/README.md) | Historical paper route, manuscript and legacy code |
| [`_to_delete/`](docs/r1/recovery/c3-fixtures-20261031/README.md) | Staged historical files, some of which are pinned recovery inputs |

Host deployments use the pinned [autoresearch harness](https://github.com/dowlingwong/autoresearch_harness).
[COMPUTE.md](canon/COMPUTE.md) records host capabilities, availability snapshots and the current routing.
Use the project's published branch and signed launch note when an experiment requires them.

Writer and Overleaf use [paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript) directly. With access to the manuscript repository,
run `git submodule update --init -- papers/manuscript` to check out the exact revision recorded here.

## Checks

```bash
make r1-test AR_HARNESS_ROOT=../autoresearch_harness
make r1-e2e
make legacy-test LEGACY_PY=/path/to/python3.13
```

For branch retirement and archive provenance see [the hygiene audit](docs/r1/reports/REPO_HYGIENE_AUDIT_20261126.md)
and [BRANCHES.md](docs/r1/BRANCHES.md).
