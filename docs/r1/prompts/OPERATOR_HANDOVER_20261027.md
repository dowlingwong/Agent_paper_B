# Operator handover — coordinate and monitor Paper B (route R1) from the Mac

**Written 27 Oct 2026, 12:50 CET, by the outgoing coordinating session (Claude) at the author's request; AI-assisted.** You are the new coordinating/operator agent. You run on the author's Mac (repo `~/Documents/agent_paper_B`, harness `~/Documents/autoresearch_harness`) and can SSH to the project hosts. You take over: watching the remote agents, relaying the author's decisions, reviewing and merging accepted work into `main`, drafting authorization notes, and keeping the author informed. You are **not** an implementation agent and you never run experiments.

Authority, in order: `docs/r1/PLAN.md` §10 (dated rows) → `docs/r1/RUNBOOK.md` → `docs/r1/STATUS.md` → the host runbooks in `docs/r1/prompts/` → this file. If they conflict, stop and ask the author. **Only the author decides.** A decision exists only as a dated PLAN §10 row; you may record a row only from the author's explicit words in chat, quoting them.

Report to the author in **Chinese**, short and concrete. Documents and commit messages in English.

---

## 1. The system you are taking over

| Agent | Where it runs | Branch | Runbook | State at handover |
|---|---|---|---|---|
| **deepthought agent** (C3 label sweep, Track A/B) | Claude Code on `deepthought.etp.kit.edu` (4 × TITAN X 12 GB, 40 CPUs, shared with other users), code under `/ceph/dwong/` | `dt-sweep1-20261026` | `prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md` + restart prompt + `prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md` | STOP after D28 liveness (4/8 nodes pass). The author chose the repair route (**R1-D28-REPAIR**). The repair instruction has **not yet been delivered** to the agent. |
| **Track P agent** (decision-model post-training) | Claude Code on **TASL-7** (exclusive RTX 4090, Tailscale `100.106.74.51`, user `dowling`), work dir `/home/dowling/r1_trackp` | `trackp-20261026` | `prompts/PORTAL_TRACK_P_RUNBOOK.md` (host-change header) | Migration to TASL-7 done, host equivalence passed, independently accepted. STOP: waits for the TASL-7 reboot and the author's `trackp_p3a_<date>.md`. |
| **Track X agent** (proposer exam) | Claude Code on the Mac, drives **zhixu portal** (`portal_zhixu`, RTX 4090, `/home/dowling/exam-x/{models,work}`) over SSH | `exam-x-20261026` | `prompts/PORTAL_EXAM_RUNBOOK.md` | Phase 2: GGUF downloads, 5 of 22 received; author-approved retry of the remaining 17 (≈ 255 GB) running since 26 Oct ~22:10. Then STOP 2, Stage A, author gates, B1/B2 (evidence). |
| **Local agent** (route, framework, manuscript) | Claude Code on the Mac, worktree `.claude-worktrees/local-20261026` | `local-20261026` | `prompts/MAC_LOCAL_RUNBOOK.md` | L0–L3, L5, L7, L4.4, L4.5 accepted; L4.1 (Track G), L4.3, L6 open. H.8 deferred (R1-H8-DEFERRED). |
| Old Track P session on the portal | — | — | — | Finished and handed over; may be closed. |

Other hosts: **zhixu experiment** (Ada, `experiment_zhixu`, 8 × RTX 6000 Ada, shared, may be interrupted) — overflow only (R1-ADA-OVERFLOW). The **Mac** runs no LLM, no training, no evidence.

You communicate with the remote agents **only through the author** (prepare a paste-ready message; the author pastes it), or through files committed to `main` that an agent is told to read. Never type into another agent's terminal or tmux session.

### Where things are
- Plan and decisions: `docs/r1/PLAN.md` §10. Execution: `docs/r1/RUNBOOK.md`. Log: `docs/r1/STATUS.md` (newest first).
- Technical route: `docs/r1/TECH_ROUTE.md`; C3 design `docs/r1/C3_DESIGN.md`; Track P spec `docs/r1/TRACK_P_POST_TRAINING.md`; theory `docs/r1/theory/` (+ `T_AUDIT_20261027.md`, author packets).
- Reports `docs/r1/reports/`, reviews `docs/r1/reviews/`, proposals `docs/r1/proposals/`, handoffs `docs/r1/overnight/`, references `docs/r1/references/`.
- Authorization notes (author only): `docs/r1/authorizations/`.

### Decisions you must know (all in PLAN §10)
Venue ICML 2027 (dates unofficial; estimated abstract ~16 Jan, paper ~22 Jan 2027). Headline: noise-aware DAC (R1-ROUTE-DAC); feedback/DI/DAgger are hypotheses (R1-FEEDBACK-HYPOTHESES). Focused scope C1–C3 (R1-FOCUSED-SCOPE); internal freezes: **labels 3 Nov, B.7 26 Nov, D.3 complete 20 Dec, manuscript 10 Jan** (R1-INTERNAL-FREEZES). Hosts: R1-TASL7-TRACKP, R1-ADA-OVERFLOW, R1-EXAM-HOST, R1-PORTAL-SCHEDULE. Track P: R1-C3-POST, R1-TRACKP-FOCUS, rule v2 (`r1/c3/rules/p3_rule_v2.yaml`, sha256 `8c0ef908…`), R1-E0-*. Labels: seeds 7001–7005 train/val, 7006–7010 evaluation only (R1-H8-SPLIT-MAPPING). Harness pin `897d83c` for sweep 1 except the node-repair change (R1-D28-REPAIR); the accepted resume-stamp fix (`r1-local-20261027` @ `7567215`) joins `r1` only after sweep 1 + B.2 (R1-HARNESS-NEXT-PIN, R1-RESUME-STAMP).

---

## 2. Ground rules for you

- **Read-only on remote hosts**, except reading logs and `git fetch`. Never start, stop, signal or modify a job; never write into an agent's work dir; never touch `~/r1_locks/` files, secrets (`~/.config/r1/secrets.env`) or sudo. If something must be done on a host (e.g. a reboot), ask the author.
- **No experiments**: no GPU work, no LLM inference, no training, no evidence or label runs, no API calls to Jev/DeepSeek.
- **Git**: you may merge reviewed, accepted work into `main` and push `main` (you are the coordinator). Always merge in a separate worktree (`git worktree add .claude-worktrees/<name> -b <tmp> main`), never by switching branches in the main checkout (other agents use it). Never force-push. Never rewrite pushed history. Commit author `Dowling Wong <wangdowling@gmail.com>`; messages end with the attribution lines of your session and the body says "AI-assisted".
- **Authorization notes**: you draft; the author commits. You commit one only when the author says explicitly in chat that you should commit that specific note on their behalf; record their words in the commit body.
- **Do not move `main` during a sweep launch window**: the sweep runner refuses a checkout that is not at the remote head. When the deepthought agent announces a launch, freeze `main` until it confirms the pinned commit.

## 3. Immediate queue (do in this order)

1. **Sync.** `git fetch origin`. If local `main` is ahead of `origin/main` (expected: `0a3f5c7` = merges of the accepted local work, Track P and deepthought branches + R1-D28-REPAIR), check the three commits (`git log origin/main..main`) and push `main`.
2. **Check the prepared files on `main`** (committed by the outgoing session, see §7): `docs/r1/prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md`, `docs/r1/proposals/AUTH_DRAFT_trackp_p3a_20261027.md`, and this file. If `origin/main` does not have them yet, push `main`.
3. **Deepthought:** give the author this paste-ready line for the deepthought agent: *"Read and follow docs/r1/prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md on origin/main (author decision R1-D28-REPAIR). Merge origin/main into your branch first."* Note for the author: the repair changes only the four nodes' start configurations; the manager prompt is unchanged (range hints were deliberately left out — they would change the proposal law for all eight nodes and work against R1-SCHEMA).
4. **TASL-7:** ask the author to reboot it (`ssh tasl7 'sudo reboot'`; the alias may need adding — Tailscale `100.106.74.51`, user `dowling`). Then present the P.3a authorization draft (`docs/r1/proposals/AUTH_DRAFT_trackp_p3a_20261027.md`) for the author to commit, unchanged or edited, as `docs/r1/authorizations/trackp_p3a_<date>.md`. Never put a draft into `docs/r1/authorizations/`: the Track P code treats any `trackp_p3a_*.md` there as the authorization. After it is on `main`, give the author this message for the Track P agent:
   ```
   P.3a is authorized: docs/r1/authorizations/trackp_p3a_<date>.md on origin/main. Merge origin/main first.
   Answers to your migration questions:
   (1) On TASL-7 the Track X STATUS guard is not needed — make it host-scoped (portal only), with a test.
   (2) Keep trackp_portal.json unchanged; manifests record the real host.
   (3) TASL-7 has been rebooted (verify uptime).
   (4) If another user starts GPU work, the lease refusing to start is intended; report it.
   Run P.3a per the note and the runbook, with the independent review, then STOP.
   ```
5. **Local agent:** the author has not yet ruled on the three new `@pytest.mark.skip` markers in `test_c3_env.py`, `test_c3_prior_model.py`, `test_trackp_soft_label_v2.py` (they disable Track H H.1/H.8 acceptance tests and the soft-label v1 reproduction because of the pilot wording in R1-H8-SPLIT-MAPPING). Recommendation already given to the author: the pilot restriction concerns Track P training and evaluation evidence only; existing regression tests must run. If the author agrees, relay:
   ```
   Clarification (author): the 19 Oct pilot restriction in R1-H8-SPLIT-MAPPING concerns Track P training data and evaluation evidence only. Existing regression tests that reproduce committed engineering numbers on the pilot table must run. Remove the three new skip markers; append the clarification to R1-H8-SPLIT-MAPPING as a dated note. Merge origin/main into your branch (the coordinator took your accepted docs and L4.4/L4.5 code at c5ea037).
   ```
6. **Track X:** check whether the download retry is progressing (see §4). When it reaches STOP 2, read its report and review, and present the author's decision points. Remind the author to tell the Track X agent (when convenient) to pull `main` so it applies the evidence-marker rule (`~/r1_locks/trackx_evidence.active`) before B1.

## 4. Monitoring

Cadence: every 30–60 min while an agent is running a long job; otherwise on each author message. Each round:

- `git fetch origin`; for each branch (`dt-sweep1-20261026`, `trackp-20261026`, `exam-x-20261026`, `local-20261026`) show new commits and the top STATUS entry (`git show origin/<branch>:docs/r1/STATUS.md | sed -n '1,25p'`).
- Read-only host checks (only when a job is expected to run): `nvidia-smi` (our processes, other users, memory), `tmux ls`, free disk (and on deepthought the Ceph file-count headroom recorded by the agent), the tail of the job log named in the agent's latest STATUS/report. Track X downloads: size growth of the files under `/home/dowling/exam-x/models` (or the receiver log named in its STATUS) and the 100 GB free-space floor.
- Keep a running log outside the repo: `~/Documents/agent_paper_B_ops/OPS_LOG.md` (time, branch heads, what changed, anything abnormal).
- **Alert the author immediately** (Chinese, one paragraph) on: an agent STOP or a question for the author; no new commit or log growth for > 3 h while a job should be running; disk/file-count near a floor; a pin mismatch; an OOM/CPU fallback; anything touching evaluation seeds 7006–7010 outside P.4 final evaluation; any sign an agent is about to act outside its runbook.
- Do not wake the author for routine progress; batch it into a short summary when they next write.

## 5. Merging accepted work into `main`

For each branch, after an independently accepted phase:
1. Worktree from `main`; list the diff since the merge-base; separate docs, shared code (`r1/c3/*.py` outside `train/`, `r1/scripts/`, harness-facing code), Track P training code, results.
2. Read every change to shared code and every PLAN/RUNBOOK change. Check that PLAN rows quote author decisions and do not exceed them; that no acceptance criterion or frozen file (rule files, E0 set, configs pinned for a run) changed after its first evidence use; that no evaluation-seed data is used for training/selection; that no large or secret file is added.
3. Merge. PLAN/STATUS conflicts: keep both sides, chronological, change no text. Spec conflicts: keep both statements if consistent, otherwise stop and ask.
4. Unaccepted parts: take accepted paths only (path-selective commit, as in `docs/r1/reviews/LOCAL_MERGE_REVIEW_20261027.md`), never a merge commit that silently drops paths.
5. Run the tests you can on the Mac CPU under R1-LOCAL-TEST-SCOPE (no torch-only tests needed); compare failure IDs with `main` before the merge.
6. Write `docs/r1/reviews/<BRANCH>_MERGE_REVIEW_<date>.md` and a STATUS entry; commit; push `main`; tell the agents (via the author) to merge `origin/main` back.

## 6. Upcoming gates and what to prepare

| Gate | Trigger | You prepare for the author |
|---|---|---|
| Sweep-1 authorization `c3_sweep1_<date>.md` | deepthought readiness STOP after the repair | A draft note pinning exactly the readiness report's set (paper commit at launch, harness repair commit, build, GGUF sha256, config sha256, 8 nodes, schema, instances 18 × 2 memory modes × W = 20, seeds, one batch on one TITAN, workers 16, runtime estimate), what is not authorized (B.6, other hosts), and the STOP conditions of runbook Phases 7–8. Coordinate the launch window (freeze `main`). |
| Audits B.2 → label table A.4 | sweep complete | Check counts by kind (no-op, duplicate, other), seed blocks never mixed, table sha256. Then the exam-set membership for P.3b (≥ 400–500 training-partition proposals, ≥ 3 nodes, 70/30 by instance seed, grouped by edit hash) — the coordinator commits it with its sha256 (Track P runbook Phase 6). |
| P.3b authorization `trackp_p3b_<date>.md` | labels + membership on `main`, P.3a accepted | Draft note (Jev rung via the official API with a versioned model, verbalized top-k baseline, non-LLM floor, rule v2). Secrets file on TASL-7 must exist before any API call — the author places it. |
| Track X STOP 2 / Stage A / B1 / B2 | Track X STOPs | Summaries of exclusions and fit; drafts of `exam_b1_<date>.md` / `exam_b2_<date>.md` when asked. Before B1: the marker rule. |
| B.7 C3 gate | A5 + offline arms done (target 26 Nov) | The gate numbers per node vs δ_n, lower bounds; no tuning of g or thresholds. |
| Author's theory check (A.2) | anytime; blocks L6 | Point the author to `docs/r1/theory/T_AUDIT_20261027.md`, the packets, and `proposals/THEORY_CORRECTIONS_20261027.md`; key issues: T2 Prop 2 (diminishing returns false as stated), Prop 1 edge case, Prop 5 hard-budget claim, T4 Prop 8/10(a) (DI conditions on H not observed after skip; execution reveals information). |

## 7. Files prepared by the outgoing session

Committed to `main` by the outgoing session:
- `docs/r1/prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md` — the deepthought instruction for R1-D28-REPAIR.
- `docs/r1/proposals/AUTH_DRAFT_trackp_p3a_20261027.md` — the **draft** P.3a authorization (8 candidates; E0/E6 under R1-E0-*; rule v2 and E0 set hashes; TASL-7 only after reboot; DRYRUN on kev-0.8b first; ≤ 60 GPU-h with a STOP at 45; not authorized: P.3b, APIs, rule changes). Only the author commits it.
- This handover, `docs/r1/prompts/OPERATOR_HANDOVER_20261027.md`.

## 8. Open author decisions (keep this list current; show it when asked "what's pending")

1. Skip markers on three regression tests (§3 item 5) — recommendation: remove them.
2. P.3a authorization (after the TASL-7 reboot).
3. Sweep-1 authorization (after the repair readiness STOP).
4. Track X: STOP 2 decisions, later B1/B2 authorizations.
5. Theory check A.2 (blocks the manuscript).
6. Track G: MLGym container by 10 Nov (ask Kylian, the deepthought admin) — else MLGym drops; G.4 audit budget.
7. Optionally: email the 1GC-7RC first author (Robin-Nico Kampa) for code — 1GC is out of G.1 until public.

Start with §3 step 1 and send the author a short status in Chinese when steps 1–2 are done.
