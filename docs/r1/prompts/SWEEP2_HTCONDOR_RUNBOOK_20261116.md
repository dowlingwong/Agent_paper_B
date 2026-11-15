# Sweep 2 (and later sweeps) on HTCondor — work plan for the agents (16 November 2026)

**AI-assisted (Claude, coordinating chat). A work plan, not a decision.** Authority is PLAN §10 only. Every unit
below starts by checking that the rows it depends on exist on the author branch named in its gate (currently
`author-x7-20261116` or a descendant). If a required row is missing, STOP and report; do not proceed on this file.

## 0. What this plan is for

- **Host gate:** PLAN §10 row **R1-SWEEP-HOST-HTC** (to be signed). Until it exists, nothing here may launch an
  EVIDENCE job; engineering units (marked ENGINEERING) may proceed.
- **Scope:** C3 label sweeps from sweep 2 on — T0 sweep 2 (main C3 data with the pick, R1-MAIN-PROPOSER (b)),
  their B.2 audits, and later T1 label sweeps (R1-BX-D1/D5) — run as HTCondor jobs. LLM-backed label runs run on
  **NEMO2 L40S only**; CPU-only audits on **one pinned HTCondor CPU class**. Sweep 1 stays frozen as recorded
  (R1-B1-CORPUS-FREEZE); it is not rerun.
- **Fixed by existing rows (do not change):** pick `gemma4_31b`, thinking off (R1-EXAM-X7, R1-MAIN-PROPOSER);
  sweep-1 nodes, 18 instances, W = 20, memory `{append_only_summary, none}`, `vary` split, `manager_proposal/v1`,
  temperature 0.2 with the D26 seed, sweep-1 instance seeds; server flags exactly as in the exam
  (`--chat-template-kwargs {"enable_thinking":false}`, `--jinja`, q8_0 KV cache, context 16,384); `cache_prompt:
  false` on every call; audits K = 10 with seeds 7001–7005 (labels) / 7006–7010 (evaluation), never mixed, unless
  R1-BX-D3's K = 6 check has passed and is recorded; one GPU model per table (R1-SWEEP-HOST, R1-BX-D5).
- **Analysis lock:** R1-BX-D8 — no sweep-2 (T0 or T1) label table is copied back *for analysis* or read by any
  analysis code before the author row **R1-BX-D8-CONFIRM** exists. Raw outputs are stored sealed (`refuse_sealed`
  paths) until then. D8 is not confirmable yet (open question D8-SKEW).
- **Roles:** cluster agent = deepthought/HTCondor only; Mac agent = desk only (bundles + append-only READY.txt);
  experiment agent = TASL-7/TASL-2 only (not needed here). One operator per branch and per host. Each unit gets a
  fresh independent reviewer; reviewed base / three-way check as before; no force push; never push `main`, `r1`
  or `exam-x-*` (pushing `main` is the author's call, done on explicit instruction); nothing deleted (move aside to
  `_to_delete/`).

## 1. Prerequisites (all must hold before the EVIDENCE launch)

| # | Prerequisite | Owner |
|---|---|---|
| P1 | R1-SWEEP-HOST-HTC signed | author |
| P2 | **Published paper code.** Evidence code reads its authority from published `main` (`_verify_published`; sweep 1 ran at "`main` HEAD at launch"). `main` (60ec768e) lacks the sweep-2 code path. A reviewed integration branch carrying exactly what sweep 2 needs (S2-M2) is merged to `main` on the author's explicit instruction. | Mac → author |
| P3 | Authorization note `docs/r1/authorizations/c3_sweep2_<date>.md`, written and committed by the author (draft S2-M1) | Mac → author |
| P4 | L40S deployment check passed (S2-C3) | cluster |
| P5 | Timing pilot done and the job layout fixed (S2-C4) | cluster |
| P6 | Real submission enabled only for the authorized run ID (S2-C5) | cluster → author |
| P7 | Image digest frozen in the authorization (S2-C1) | cluster → author |

## 2. Mac agent units (desk only)

- **S2-M1 Authorization draft** for sweep 2 + its B.2 audits, in the format of `c3_sweep1_20261027.md`: scope,
  nodes, instances, seeds, memory modes, W, schema, noise source and SHA, audit seeds, host = HTCondor NEMO2 L40S
  (GPU-model and CPU-model requirements), image digest (from S2-C1), harness pin, llama.cpp commit `620d222`, pick
  GGUF SHA-256, `cache_prompt: false`, server flags, footprint, workers, provisional estimate (from S2-C4),
  boundaries and STOPs, the R1-BX-D8 sealing rule. `approved: false` until the author sets it.
- **S2-M2 Integration branch for `main`.** List every commit sweep 2 needs that is not on `main` (at least: the
  R1-SWEEP1-CLASSIFY runner/audit classification fix, `cache_prompt` false, thinking-off server flags, q8_0 KV,
  context 16,384, pick registry entry, R1-BX-D8 sealed readers, and the B.2 rules R1-SWEEP1-CLASSIFY /
  R1-B2-DECOUPLE). Build `int-main-sweep2-<date>` from `origin/main` with exactly those, run the tests, independent
  review (scope: sweep-2 path only), bundle. The author decides the push to `main`.
- **S2-M3 Hand-off for the cluster agent** in the B2 hand-off style: config, prechecks, job layout (from S2-C4),
  submission order, monitoring, copy-back into sealed storage, STOP list, report template (counts only; no label
  read).
- **S2-M4** (already queued) D8-SKEW simulation; then a draft **R1-BX-D8-CONFIRM** row for the author.
- **S2-M5** X.7(c) appendix: C3 premises vs proposer strength from existing B1/B2 data; report a null if nothing
  differs beyond CI.

## 3. Cluster agent units (deepthought / HTCondor)

- **S2-C1 Image for sweep 2.** Propose freezing the v1 GPU image `ghcr.io/…r1-htc@sha256:69b06b35…` (proven by I3)
  for the whole sweep, unless the author approves v2 before launch. One digest per table; record it.
- **S2-C2 Sweep job wrapper (ENGINEERING until P1–P7).** One job = one (node, memory mode) chunk of campaigns
  (or a smaller chunk if S2-C4 shows walltime limits), resumable (A.5 semantics). In the job: fetch the GGUF and
  check its SHA-256; start an owned `llama-server` with the exam flags; run the harness campaigns with worker runs on
  the job's CPUs; record per campaign the host, GPU name/UUID, driver, CPU model, image digest, harness and paper
  commits, label string. Requirements pin the GPU model to L40S and the CPU model to one class (from `condor_status`;
  record it). Outputs go to a sealed `/ceph/srv/dwong/paperb/sweep2/<run_id>/` path; nothing reads labels. Label
  string comes from the authorization (EVIDENCE only with a matching authorization; the R1-SWEEP1-CLASSIFY defect
  must be shown fixed by a test). Reviewed dry-run JDL; tests.
- **S2-C3 L40S deployment check (ENGINEERING).** The pick was selected on a 4090; sweep 2 deploys it on L40S.
  Pre-declare criteria before running, then replay B2's 12 thinking-off roots (3 nodes × seeds 9011–9014, B2 rule
  and settings) on L40S and compare with the B2 EVIDENCE values: per-instance final_y, parse failures, invalid /
  duplicate / no-op rates, server throughput. Not bitwise identity — a broken-stack check. Reviewed report.
- **S2-C4 Timing pilot (ENGINEERING).** One node × 2 instances × both memory modes on L40S: wall time per
  campaign, queue wait, GPU memory, walltime limits, GGUF fetch time; propose the job layout and the total estimate.
- **S2-C5 Real-submission switch.** A reviewed change that enables real submission only for the authorized run ID
  and image digest; default stays dry-run.
- **S2-C6 Sweep-2 EVIDENCE launch** after P1–P7: submit, monitor (≤ 30 min), resume only by the reviewed rule, no
  ad-hoc retries; sealed copy-back with SHA256SUMS; sweep index; run report with counts only. STOP and preserve on
  any guard failure.
- **S2-C7 B.2 audits** as CPU jobs on the pinned CPU class, seed blocks as fixed; sealed. If sweep 1's B.2 audits
  have not run yet, propose running them on the same CPU class for comparability (author decides).
- **S2-C8 Later: T1 label sweeps**, once Track G nodes qualify and R1-BX-D5 budgets are fixed: same pattern, GPU
  worker runs co-located with the server on the L40S (48 GB), one GPU model per table.

Running units already in flight continue: c3_features/v3 rebuild (paper root at `main` 60ec768e), image v2
(no digest switch before author approval).

## 4. STOP conditions (in addition to each unit's own)

- Any required PLAN row or authorization missing or different from what the unit cites.
- A job lands on a GPU other than L40S or a CPU outside the pinned class (one host type per table).
- GGUF SHA mismatch, server flags or `cache_prompt` differing from §0, label string not matching the authorization.
- Any code path reading sweep-2 labels before R1-BX-D8-CONFIRM.
- Pushing `main` without the author's explicit instruction.
