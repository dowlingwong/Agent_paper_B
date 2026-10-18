# Paper B — noisy incumbent-relative acceptance in governed autoresearch loops (route R1)

Authoritative remote: [Agent_paper_B](https://github.com/dowlingwong/Agent_paper_B).
Target venue: TMLR, with an ICML-main-track quality bar (docs/r1/PLAN.md §9).

**Start here:** [docs/r1/PLAN.md](docs/r1/PLAN.md) (canonical plan and dated author
decisions), [docs/r1/RUNBOOK.md](docs/r1/RUNBOOK.md) (phases, gates) and
[docs/r1/STATUS.md](docs/r1/STATUS.md) (the only record of what is done).

## The question

An LLM manager proposes bounded edits to a training script, a worker trains, and a
control plane keeps an edit only if the noisy metric strictly beats the incumbent's
recorded value. R1 treats this loop as noisy sequential selection with an incumbent:

- **C1** — measured control errors: false keeps and discards, and wasted runs.
- **C2** — theory of acceptance under noise: Bayes keep threshold, value of verify,
  the winner's curse of `current_best`, and a proposer whose law depends on the ledger
  (`docs/r1/theory/`).
- **C3** — a learned per-proposal prior plugged into the C2 rule (pre-execution skip
  and a per-proposal keep threshold), compared against the C2 index policy.

All numbers in this repository so far are `PILOT` or `ENGINEERING_ONLY`; none is
evidence (RUNBOOK §1).

## Layout

| Path | What it is |
|---|---|
| `r1/` | R1 analysis code: noise pilot (`noise/`), headroom pilot (`headroom/`), theory code (`theory/`), liveness, branch schema, baselines, Ada/Deepthought runners (`scripts/`), tests (`tests/`). |
| `docs/r1/` | Plan, runbooks, status, theory notes (T1–T4), reports, reviews and agent prompts. |
| `results/r1/` | Committed pilot and engineering outputs (`pilot/`, `engineering/`). |
| `papers/` | Manuscript (not started; format open, PLAN R1-FORMAT). |
| `archive/old_b_2026-10-09/` | The retired route: plans (`docs_paper_split/`), manuscript (`paper_b_manuscript/`) and, since 18 Oct 2026, all its code, tests, protocols, release tooling and the vendored Pi tree (`code/`, with `PROVENANCE.md` and licences). Read-only history. |

Harness changes live on branch `r1` of the separate `autoresearch_harness`
repository (PLAN D14); R1 code runs against that checkout.

## Checks

```sh
make r1-test AR_HARNESS_ROOT=../autoresearch_harness   # R1 test suite
make r1-e2e                                            # R1 end-to-end smoke
make legacy-test LEGACY_PY=/path/to/python3.13         # old-route suites (212/6/12)
```

LLM workloads never run on the Mac (PLAN R1-COMPUTE); they run on Deepthought or Ada.
