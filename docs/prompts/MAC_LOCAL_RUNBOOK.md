# Local work on the Mac (route consolidation, framework code, manuscript) — agent runbook

**Written 26 Oct 2026 by the coordinating session (Claude) at the author's request; AI-assisted.** One implementation agent (Claude Code) on the author's Mac executes this runbook. It covers the paper-side work that needs no GPU and no LLM inference: reviewing and consolidating the technical route, fixing documented errors, a feasibility and timeline analysis for ICML 2027, the framework code that is still missing on the Mac side, and the ICML LaTeX manuscript. It runs alongside three remote agents (deepthought: C3 label sweep; zhixu portal: Track X proposer exam; TASL-7: Track P post-training) and must not interfere with them.

Authority: `docs/r1/PLAN.md` §10 (every dated row), `docs/r1/RUNBOOK.md`, `docs/r1/STATUS.md`. If this file and those disagree, they win; stop and report. **Only the author decides.** You propose; a decision exists only as a dated PLAN §10 row. You never adopt, never change a decided value, never write an authorization note.

---

## 0. Ground rules

- **Host.** The author's Mac only (`~/Documents/agent_paper_B`, harness `~/Documents/autoresearch_harness`). No LLM inference and no model training on the Mac (R1-COMPUTE as revised 24 Oct). CPU-only tests, tiny random-weight models, fake servers and LaTeX builds are fine. No SSH to the other hosts; never touch their work dirs.
- **Worktrees, not branch switches.** The main checkout is used by other agents. Create your own worktree: `git -C ~/Documents/agent_paper_B worktree add .claude-worktrees/local-<YYYYMMDD> -b local-<YYYYMMDD> origin/main`. Harness work, if any, in its own worktree on branch `r1-local-<YYYYMMDD>` from `r1`.
- **The harness pin is frozen.** Sweep 1 runs at harness `897d83c` (R1-DT-PIN). Any harness change goes on `r1-local-<date>` and is **not** merged into `r1` until the author decides (after sweep 1 or with an explicit PLAN row). A change that would alter campaign behaviour, ledgers or prompts at the pinned commit is out of scope here.
- **Shared code in this repo.** `r1/c3/` and `r1/c3/train/` are also edited by the Track P agent on `trackp-<date>`. Do not edit `r1/c3/train/`. For `r1/c3/env.py`, `control.py`, `serve.py`, `prior_model.py` coordinate through the coordinator (STOP and ask before editing). New code goes into new modules where possible.
- **Commits.** Small commits, author `Dowling Wong <wangdowling@gmail.com>`, messages ending with the attribution lines the coordinating session gives you; body says "AI-assisted". Push only your own `local-*` / `r1-local-*` branches. Never push `main` or `r1`, never force-push. The coordinating session reviews and merges.
- **Documents.** English. Edits that only make documents consistent with already-decided PLAN rows (marking superseded text, fixing stale references, correcting arithmetic) are yours. Anything that changes a decision, a threshold, a design choice or the paper's claims is a **proposal** in a separate file for the author.
- **Honesty.** Label AI-assisted work. Never invent numbers; every number in a document or the manuscript must trace to a committed file. Mark estimates as estimates.
- **Review loop at every STOP** (same as R1-EXAM-REVIEW): spawn a fresh, independent reviewer subagent that has not seen your work in progress; give it the task's goal, this runbook, the relevant PLAN rows, the branch and commit range and the "Done when" — not your conclusions. It writes `docs/r1/reviews/LOCAL_<task>_REVIEW_<date>.md`; you fix or answer each finding; the same reviewer re-checks and writes "accepted" or "not accepted". You never accept your own task.
- **Reporting.** After each accepted task: a STATUS entry on your branch (newest first) and a short message to the author: done, commits, checks, review verdict, open questions.

## 1. Subagents: when and how

Use subagents for independent, parallel, read-heavy or isolated pieces; keep decisions, merges and cross-document edits in the main agent.

| Use a subagent for | Why | Isolation |
|---|---|---|
| Independent reviewers at every STOP | The work must not grade itself | Fresh agent, no work-in-progress context |
| Per-document contradiction scans (L1) | Parallel, read-only | Read-only; returns a findings list |
| Independent proof audit of T2/T4 (L2) | Must not be anchored on existing derivations' prose | Give it the statements and assumptions only, then the proofs |
| Reproducing T3/T5 simulations (L2) | CPU, self-contained | Scratch dir; no repo writes |
| Bibliography and related-work extraction (L6) | Read-heavy | Writes only `papers/r1/refs/*.bib` drafts |
| Each Track G adapter (L4.1) | Independent code per benchmark | Own worktree each (`isolation: worktree`) |
| Test writing for new modules | Parallel | Same worktree as the module, after the module exists |

Do **not** delegate: PLAN/RUNBOOK edits, choosing between proposals, merges, anything touching the pinned harness, the timeline proposal (L3) and the final consistency pass. Brief each subagent with: the goal, files to read, what is already ruled out, the exact output file, and that it must not edit anything else.

---

## Tasks (in priority order)

### L0 — Orientation and baseline (read-only; ~1 h)

Read: PLAN (all; §10 rows from 22 Oct onward in detail), RUNBOOK, STATUS (top 15 entries), `C3_DESIGN.md`, `TRACK_P_POST_TRAINING.md`, `theory/T1–T5`, `inputs/PROBLEM_SPEC_DRAFT_20261009.md`, `inputs/NOVELTY_*`, `prompts/{DEEPTHOUGHT_SWEEP1,PORTAL_EXAM,PORTAL_TRACK_P}_RUNBOOK.md`, `references/README.md`. Build a scratch venv outside the repos (Python 3.13 via `uv`) and record the test baselines of both repos (paper `make r1-test`; harness suite).

**Done when:** `docs/r1/reports/LOCAL_BASELINE_<date>.md` lists the test counts and failing IDs of both repos and the document inventory. No review needed.

### L1 — Technical-route review and consolidation (~1–2 days)

Goal: one clear, internally consistent, feasible description of the route that a reviewer could follow, and every stale or contradictory statement found.

1. **Contradiction scan** (subagents, one per document group: PLAN; RUNBOOK + host runbooks; C3_DESIGN + Track P spec; theory T1–T5; problem spec). Each returns a table: location, statement, conflicting statement or later PLAN row, severity (blocking / misleading / cosmetic), proposed fix. Known items to verify, not assume:
   - PLAN §1 R1-ROUTE says "DAC is related-work vocabulary only, not the headline framing", while the author asked on 25 Oct to frame the paper as a DAC problem and adopted R1-DAC-INTERFACE — **author decision needed** (proposal, not an edit).
   - PLAN §1 lists "the ICML 2027 route" as superseded, §9 still describes TMLR, but R1-VENUE-3 (24 Oct) made ICML 2027 the venue.
   - PLAN §7 configurator architecture (Kev/CLM, D16 deferred) is stale against R1-C3, R1-C3-BASE, R1-C3-POST; PLAN §9 milestones and RUNBOOK phase targets predate the venue change.
   - C3_DESIGN §5 A5/A6 definitions vs R1-C3-POST (belief/action decoupling, no greedy-bin deployment); C3_DESIGN §9 timeline.
   - RUNBOOK host table and rows vs R1-TASL7-TRACKP, R1-ADA-OVERFLOW, R1-EXAM-HOST.
2. **Consistency edits** (yours, after the scan): mark superseded text with a pointer to the PLAN row that supersedes it; fix stale references, host names and file paths; do not delete history.
3. **Technical route document** `docs/r1/TECH_ROUTE.md` (new; the "one place" for the route): problem and framing (both candidate framings shown until the author decides), contributions C1–C4 with the evidence each needs, the C2 theory in one page, the C3 ladder A0–A6 with the decoupled A6 and the R-B arm, labels and splits, decision-model exam, evaluation and the C3 gate, Track G role, the three-way comparison (LLM self-control vs trained configurator vs hybrid), compute and hosts, and a dependency graph of every remaining step. It cites PLAN rows by ID instead of restating decisions. Each section ends with "open decisions" if any.
4. **Proposals** `docs/r1/proposals/ROUTE_PROPOSALS_<date>.md`: every finding that needs the author, each with options, a recommendation and consequences.

**Done when:** the scan tables are committed (`docs/r1/reports/LOCAL_CONSISTENCY_SCAN_<date>.md`); every blocking/misleading item is either fixed by a consistency edit or listed in the proposals file; `TECH_ROUTE.md` exists and a reviewer can trace each claim in it to a PLAN row, a report or a theory file; the reviewer subagent accepts. **STOP L1** (author reads the proposals).

### L2 — Theory check support (~1–2 days; supports RUNBOOK A.2, which the author must do)

1. Independent proof audit (subagent) of T2 Propositions and T4 Propositions 6–10: restate each claim with its assumptions, re-derive or find the gap, classify (correct / correct with an added assumption / gap / wrong). Output `docs/r1/theory/T_AUDIT_<date>.md`. It is an aid for the author's own check, not a replacement.
2. Reproduce the T3/T5 simulations from committed code (CPU) and compare with the reported numbers; record mismatches.
3. Prepare a one-page **author proof-check packet** per proposition: statement, assumptions, where it is used in the paper, audit verdict, the 3 steps most worth checking by hand.

**Done when:** audit file, reproduction record, and packets committed; reviewer accepts. Never mark a proposition "checked by the author".

### L3 — Feasibility analysis and ICML timeline re-plan (~1 day; proposal)

ICML 2027 dates are not yet official; planning estimate abstract ~16 Jan 2027, full paper ~22 Jan 2027 (check icml.cc before relying on it; record the date you used). RUNBOOK targets (Phase D ~28 Feb, E ~31 Mar) predate the venue change.

1. **Critical path**: from STATUS and the three remote runbooks, list every remaining step with host, estimated duration (cite the source of each estimate: measured, projected, or guessed), dependency and owner (agent or author).
2. **Compute budget** per host until the deadline: deepthought (sweep 1, audits, B.6, C.2, deployment manager), zhixu portal (Track X), TASL-7 (Track P, 4B arms), Ada overflow (Track G, LONO, replicates). State utilisation and the single-points-of-failure.
3. **Scope options**: what to cut or move to the appendix if the path does not fit (e.g. B.6 second sweep, R-B arm, MLGym, C4 A/B), with the effect on each contribution and on the PLAN §9 quality bar.
4. **Risk register**: top risks (label headroom, C3 gate failing, digits_mlp liveness, Track G container access, ICML date) with early signals and fallbacks (the C1 + C2 fallback paper).

Output `docs/r1/proposals/ICML_REPLAN_<date>.md` (dated milestones per phase, one Gantt-style table). **Done when:** every duration has a source label; the reviewer re-derives the critical path from STATUS and agrees within a day per phase. **STOP L3** — the author adopts a plan (PLAN row); only then does the coordinator re-date the RUNBOOK.

### L4 — Experiment framework on the Mac side (~3–5 days; code; parallel subagents)

Each item on `local-<date>` (paper) or `r1-local-<date>` (harness), with tests, CPU only.

1. **Track G adapters (RUNBOOK G.1)** — nobody owns Track G yet. Harness autoresearch node check/update (5-min `train.py`, `val_bpb`), 1GC-7RC light tasks (T1 TinyShakespeare, T5 Forest Cover, T6 ETTh1, T7 AG News; `train.py` + locked `prepare.py`), MLGym light tasks (adapter only; container question is G.2 for the author). One subagent per benchmark in its own worktree. **Smoke = fake/stub training** (no real GPU run on the Mac): the node loads, proposals validate, a stub run returns a metric, a campaign of 3 trials completes. Then write `docs/r1/prompts/TRACK_G_RUNBOOK.md` (G.2–G.5 for the remote hosts: G.3 noise floors on Ada under R1-ADA-OVERFLOW, G.5 transfer) as a **proposal** for the author. These are harness changes: they stay on `r1-local-<date>` (not at the sweep pin).
2. **Track H follow-ups** (coordinate first; STOP and ask before touching shared modules): `OfflineBanditEnv` action = execute/skip with the 12-bin belief as forecast (needed before Track P.5); the online controller attaching `row["prompt"]` for the real sidecar. Tests showing old behaviour unchanged where not intended to change.
3. **Analysis pipeline**: a script that regenerates every table and figure from committed data (`make r1-figures`), starting with C1 (noise-floor table, wasted-run rates) and the C3 offline gate (B.3/B.7 inputs from the 19 Oct pilot table as a stand-in); output LaTeX macros (`papers/r1/generated/numbers.tex`) and figure PDFs so the manuscript never contains a hand-typed number.
4. **Pre-declaration scaffold (D.2)**: a template for the deployment pre-declaration (contrasts H1–H5 incl. the three-way comparison, instances, sample sizes, matched W and LLM-call cap, analysis script, hash). Content is the author's; you build the file structure and the hashing tool.
5. **Governance/harness audit** (read-only first): list open harness issues from STATUS and reviews (the environmental failing-test set, the generated-report flake, the `ClawWorker` sign question, anything flagged "follow-up"), classify each as code defect / environment / documentation, propose fixes. Code defects are fixed only on `r1-local-<date>` and only if they do not change behaviour at the sweep pin; otherwise they go into the proposals file.

**Done when (per item):** tests added and passing; both suites at baseline (no new failing IDs); a handoff note `docs/r1/overnight/LOCAL_<item>_HANDOFF.md`; reviewer accepts.

### L5 — Decision-model training route: feasibility review (~1 day; proposal)

Read `TRACK_P_POST_TRAINING.md`, the Track P reports (P.0 spikes, toy batch, E0 v2 DRYRUN, decisions review) and the PLAN rows R1-C3-POST onward. Produce `docs/r1/proposals/TRACKP_FEASIBILITY_<date>.md`:
- label budget vs expected effect: with ≈ 2,000 labels (≈ 1,400 train), what RPS-skill difference between finalists is detectable (paired bootstrap power, using the pilot table's spread as the stand-in, stated as such);
- GPU-hours per stage on TASL-7 (from the measured E0 v2 numbers, scaled and labelled as estimates) against the ICML plan (L3);
- which stages are essential for the claims (A5, R-A0/R-A1) and which are optional (R-A2/R-A3 ablations, R-B, E7), and what each optional stage would add to the paper;
- spec errors or ambiguities found (as corrections for the Track P agent, not edits to `r1/c3/train/`).

**Done when:** every estimate carries its source; reviewer accepts. **STOP** — author decides scope.

### L6 — ICML 2027 manuscript skeleton (`papers/r1/`; ~2–3 days; parallel subagents)

1. **Template**: ICML 2027 style files are not released yet; use the latest official ICML style (2026) from icml.cc as a placeholder, record its source URL and date, and plan the swap (one `\usepackage` line). Anonymous submission mode on. `latexmk` build target in the Makefile (`make paper`).
2. **Structure** (section files under `papers/r1/sections/`): abstract; introduction (problem, why noise matters, contributions C1–C4, the three-way comparison); problem formulation (governed loop, actions, estimands, DAC/contextual-bandit relation — written so either framing decision fits); theory (C2: acceptance under noise, winner's curse, index policy; T4 results as statements with proofs in the appendix); method (C3 predictor and rule, decision models, decoupled post-training); experimental setup (nodes, Track G benchmarks, arms, matching, statistics, pre-declaration); results (placeholders driven by `generated/numbers.tex`; no fake numbers — use `\TBD{}` macros that fail the final build); related work; limitations; appendices (proofs, proposer exam, decision-model exam, compute and reproducibility, AI-assistance disclosure, workshop-paper overlap).
3. **Bibliography** (subagent): BibTeX from `references/README.md`, `inputs/NOVELTY_*`, PLAN §3 neighbours (Harness-MDP, Centaur, PACE, COTA, PrimeScientist, Rehearse, SAGE, FOREAGENT, …), the DAC literature (Biedenkapp et al. 2020; Adriaensen et al. 2022 JAIR; Eimer et al. 2021 DACBench; Shala et al. 2020; Biedenkapp et al. 2022), ranking & selection / KG / racing / best-arm identification, calibration (Tian et al. 2023; Damani et al. 2025; Yue et al. 2025). Every entry verified against its source (title, authors, venue, year); unverifiable entries marked `% UNVERIFIED`.
4. **Text**: draft only the sections whose content is decided (formulation, theory statements, setup); everything depending on open decisions or results is an outline with `\TBD{}`. Paper A is cited anonymously.
5. **Checks**: build with zero LaTeX errors and zero undefined references/citations (except `\TBD`); page count reported against the ICML limit; anonymity grep (author names, KIT, ETP, repo URLs, Tailscale addresses) passes.

**Done when:** `make paper` builds the PDF; checks pass; reviewer accepts (it rebuilds from a clean clone).

### L7 — Final consistency pass and handoff

After the author's decisions on L1/L3/L5 proposals land as PLAN rows: update `TECH_ROUTE.md` and the manuscript outline to match, rerun the consistency scan on changed files, and write `docs/r1/overnight/LOCAL_HANDOFF_<date>.md` (what exists, where, what is pending the author). Reviewer accepts.

---

## STOP points that wait for the author

| STOP | After | Author decides |
|---|---|---|
| L1 | route review | framing (DAC headline or not), other route proposals |
| L3 | timeline re-plan | the ICML plan and scope cuts (PLAN row) |
| L5 | Track P feasibility | Track P scope (which stages are in the paper) |
| L4.1 | Track G adapters | Track G runbook adoption, G.2 container access, G.4 role of the new nodes |
| L4.5 | harness audit | which harness fixes to merge into `r1`, and when |

Everything else continues without waiting: when one task is at a STOP, work on the next independent task.

## Acceptance summary

| Task | Main artefact | Accepted when |
|---|---|---|
| L0 | `reports/LOCAL_BASELINE_<date>.md` | baselines recorded |
| L1 | `TECH_ROUTE.md`, consistency scan, route proposals | every claim traceable; blocking items fixed or proposed; reviewer accepts |
| L2 | `theory/T_AUDIT_<date>.md`, packets | audit per proposition; simulations reproduced or mismatches recorded; reviewer accepts |
| L3 | `proposals/ICML_REPLAN_<date>.md` | sourced durations; critical path re-derived by the reviewer |
| L4 | code on `local-*` / `r1-local-*`, handoffs | tests pass, no new failing IDs, sweep pin untouched; reviewer accepts |
| L5 | `proposals/TRACKP_FEASIBILITY_<date>.md` | sourced estimates; reviewer accepts |
| L6 | `papers/r1/`, `make paper` | clean build, no undefined refs, anonymity check; reviewer rebuilds from a clean clone |
| L7 | updated route doc, handoff | consistency re-scan clean; reviewer accepts |
