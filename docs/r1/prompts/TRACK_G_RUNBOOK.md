# Track G runbook — real-task benchmarks, tiers T1 and T2 (rewritten 4 Nov 2026)

**Status.** Rewritten 4 Nov 2026 by the chat session (Claude), AI-assisted, after the author adopted `docs/r1/proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` in full (PLAN §10 R1-BX-D1 … D14, R1-BX-REVISIONS). The 27 Oct proposal this file used to hold (autoresearch plus MLGym only if a container existed by 10 Nov; evaluation/transfer only) is superseded; it is in git at `fa60704e`.

> **Reading old markers (4 Nov, 11:29).** The items listed in PLAN §10 R1-BX-PROPOSED-CONFIRM and R1-BX-PORTING-CONFIRM are decided, even where this file still says *(proposed)*. Anything else is still proposed or open.

**This file authorizes nothing.** RUNBOOK Track G (G.0–G.6) and the PLAN §10 rows govern. Census, porting and pilots are ENGINEERING_ONLY. The T1 sweep (G.5) and the T2 closed loop (G.6) are EVIDENCE and need the author's authorization notes.

**Who does what.**
- The **operator** (`OPERATOR_RUNBOOK_20261104.md`, phase O8) ports the task assets into harness nodes (review document §7), and runs the census, the smoke runs, the pilot, the sweep and the closed loop. *(proposed)* For porting it holds a scoped exception to "never edit code": new node assets only, on its own branch `ops-trackg-<date>`, each port independently reviewed before use (PLAN R1-BX-REVISIONS (h)).
- The **Mac agent** (`MAC_LOCAL_RUNBOOK_20261104.md`, task M10) writes the shared pieces the ports build on (node template, base metric parser with the divergence class, per-run working-copy runner), the harness diff support, the S1.1 analysis for diffs, the API-proposer provider, and drafts the T1/T2 selection and the authorization notes. It also recomputes the dates after the pilot.

## 1. Tiers and target

- **Target:** 12–16 real tasks from ≥ 3 suites and ≥ 5 domains (LM, vision, graph, tabular, time series, text classification, RL). Variants of one task do not count.
- **T0:** the 8 CPU nodes (testbed; single-parameter edits as the low-interaction condition).
- **T1 (label + evaluation):** autoresearch (short fixed-step variant); MLGym lighter tasks: CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task (to be checked against the MLGym task table in G.0); MLAgentBench light tasks (for example cifar10, imdb, ogbn-arxiv); *(4 Nov, R1-1GC-FALLBACK: 1GC-7RC is not a suite. Its public datasets — TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv, TinyImageNet, VOC — may be extra tasks; their tier, whether they count toward 12–16, and their fold role are open, fixed in G.3.)*.
- **T2 (evaluation only):** heavier MLGym and MLAgentBench tasks, chosen in the census (1GC-7RC extra tasks: see T1).
- **Not used:** RE-Bench, MLE-bench (hours per run, cannot be audited); DACBench (different problem type).
- The author fixes the T1/T2 lists after the census (G.3).

## 2. Integration principle

Use each suite's **task assets** — data, baseline script, evaluator — as a harness node. Do not use the suites' agent frameworks: our harness is the loop. Per node:
- a `NodeSpec` YAML under `configs/nodes/` in the harness, registered in `nodes/registry.py`, with `editable_paths` (what a diff may touch), `frozen_paths` (evaluator, data loader, metric code), the run command, metric and direction;
- a **fixed step or token budget** (never wall-clock): 1–2 min for label runs, up to about 5 min for closed-loop evaluation, on the table's GPU model;
- a metric parser that reports divergence as its own outcome (*proposed definition:* a non-finite loss, or no metric at the budget);
- a per-run working copy and resource limits (GPU by UUID, a CPU and memory cap, a timeout of 3 × the measured run time);
- test-scored tasks select on validation only (R1-TRACKG-ROLE).

## 3. Containers (R1-BX-REVISIONS (g))

In order of preference:
1. **No container.** Port the task natively into the harness venv. Most T1 candidates are plain PyTorch scripts.
2. **Docker where it exists:** on deepthought the author is in the `docker` group. On the 4090 hosts, check `groups`, `docker info` and `podman --version` first.
3. **Apptainer** where Docker is unavailable, without admin help. *Open:* Apptainer is confirmed only on deepthought2, which is not a run host; check `which apptainer singularity` on the 4090 hosts and Ada in G.0.
   - `apptainer pull <name>.sif docker://<image>`;
   - `apptainer exec --nv --containall --bind <per-run copy>:<path> <name>.sif …`, or `--writable-tmpfs`;
   - `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` under `/ceph/dwong/`;
   - record the `.sif` sha256 in provenance, like a GGUF.
4. Never ask for `docker` group membership. If deepthought2 is ever needed, ask for rootless Podman (subuid/subgid entries for `dwong`) or Apptainer.

*Resolved 4 Nov (R1-APPTAINER-HOST):* the check (Apptainer and Singularity present; no Podman; no subuid/subgid entries) was on **deepthought2**; no repeat is needed. On deepthought the author is in the `docker` group. deepthought2 is not a run host unless a PLAN row adds it.

## 4. Steps

### G.0 — Availability and raw cost (operator; Ada first; ENGINEERING_ONLY) *(4 Nov 13:45, R1-T1-HOREKA: the whole T1 tier moves to HoreKa 2 H100; Ada is the whole-table fallback)*

Before G.0 starts on Ada, the O0 census of Ada checks Paper A occupancy (no Paper B GPU launch while a Paper A campaign waits for a card) and the co-tenancy margin. Per candidate task:
1. **Licence and availability:** the repository, its licence, and the licence of each dataset. 1GC-7RC is not used: **MLAgentBench is the third suite** (R1-1GC-FALLBACK, adopted 4 Nov 12:45); check MLAgentBench's task-asset licences instead.
2. **Raw cost:** the suite's own baseline script at a candidate step count, on each GPU model available: RTX 6000 Ada (first), RTX 4090, TITAN X. Record wall time, peak VRAM, and CPU and RAM use. No code beyond the suite's own script and a step-count argument; where a script has no such argument (autoresearch has a wall-clock budget), its raw cost is measured after G.1, at the fixed-step wrapper.

### G.1 — Porting (operator ports; Mac shared pieces first)

0. The porting exception is confirmed (R1-BX-PORTING-CONFIRM, 4 Nov).
1. The Mac agent's M10 step 0 delivers the shared pieces at a reviewed commit.
2. The operator ports each task on `ops-trackg-<date>`: data preparation, the fixed-step wrapper, the metric parser, the `NodeSpec`, resource limits, and **3–5 representative edits declared as diffs before any measurement** (committed with a hash).
3. Each port is reviewed by a fresh agent before use.
4. A stub-manager smoke campaign per node on the census host. Done when scope enforcement rejects an edit to a frozen path and the smoke manifest is complete.

### G.1b — Census measurements (operator; Ada first; ENGINEERING_ONLY) *(4 Nov 13:45, R1-T1-HOREKA: the whole T1 tier moves to HoreKa 2 H100; Ada is the whole-table fallback)*

Per ported node:
1. **Determinism:** the same seed twice; record whether outputs are bit-identical.
2. **Noise floor:** 10 training seeds × the declared representative edits plus the baseline, on one GPU model. *(proposed)* Seeds 8001–8010, disjoint from the audit seeds 7001–7010, the sweep instance seeds and the exam's 9001+. Record σ̂ for the training seed and, where it exists, the split seed, and the tail shape (the largest |z| and the excess kurtosis).
3. **D21 verdict** under the 22 Oct rule.
4. **D28 liveness** with the main proposer (once X.7 names it and G.2 is pinned), using code-level diffs: 2 instances × W = 10.
5. Shared or co-tenanted cards: the R1-COMPUTE co-tenancy rule; Ada work is resumable per unit.

Output: `docs/r1/reports/TRACKG_CENSUS_<date>.md`, one row per candidate, plus the screening funnel per suite (R1-BX-D12). Copy raw records back under `results/r1/trackg/census/`.

### G.2 — Harness diff support (Mac; R1-BX-D4)

- Diff application inside the per-run working copy, refusing any hunk outside `editable_paths`.
- **Inert detection:** the diff leaves the executed code unchanged (empty after whitespace and comment normalisation, or an AST equal to the incumbent's).
- **Duplicate detection:** a normalised diff hash and a hash of the resulting code state, against every evaluated state of the campaign.
- **Provenance:** diff text, its hash, files touched, and the resulting code-state hash in the trial record.
- Schema `manager_proposal/v2-diff` *(proposed name)*; the T0 path `manager_proposal/v1` is unchanged and byte-identical (tested).
- The S1.1 edit–edit interaction analysis for diffs (per-node interaction strength as a covariate).
- Independent review; pinned in the RUNBOOK pin table before any GPU sweep.

### G.3 — T1/T2 selection (author)

From the census: the T1 and T2 lists. Already fixed on 4 Nov: ~~the T1 label runs on Ada; the proposer on deepthought two-card serving if O5 qualifies it, otherwise a 4090 (R1-BX-PROPOSED-CONFIRM)~~ — since 13:45 (R1-T1-HOREKA) the whole T1 tier, proposer included, runs on HoreKa 2 H100, with Ada as the whole-table fallback. One GPU model per label table; σ̂ for a table comes from a floor measured on that GPU model. PLAN §10 row.

### G.4 — T1 pilot (operator; ENGINEERING_ONLY)

On 2–3 T1 nodes: a short sweep-2-shaped run with the main proposer, thinking off, `cache_prompt: false`. Measure throughput (proposals per hour, run time), diff liveness, duplicate, inert and divergence rates, and prompt lengths with code context. **Then the Mac agent recomputes the R1-BX-D14 dates from these numbers and reports any change to the author before applying it.**

### G.5 — Sweep 2, T1 part (operator; EVIDENCE; needs the author's note)

- W = 20; about 12 campaigns per T1 node; memory `append_only_summary` and `none` as on T0 *(proposed)*.
- About 150 audited proposals per node. K = 10, unless an author row puts R1-BX-D3's K = 6 into force (then labels 7001–7003 and evaluation 7006–7008, *proposed*).
- The label table is copied back for analysis only after **R1-BX-D8-CONFIRM**.
- The S1.1 edit–edit interaction measurement on each T1 node; per-node interaction strength reported as a covariate.
- STOPs: as B.1b, plus a divergence rate above the census rate by more than a factor of 2 *(proposed)*, a scope violation, or a pin mismatch.

### G.6 — Closed loop on T1 and T2 nodes (operator; EVIDENCE; part of D.3)

The main proposer and the API proposer (R1-BX-D6), plus the non-qualifying nodes for the R1-BX-D12 appendix. The API provider and its request log are Mac code (M10). API calls go only from the host the authorization note names, under the secrets rule; every request and response is logged with the returned model version.

## 5. Cost (rough; calibrated by G.4)

About 40 GPU-h per T1 node at 2-minute runs and K = 6: noise floor (5 edits × 10 seeds) about 2, sweep-2 executions (about 12 campaigns × W = 20) about 8, audits (150 × 6) about 30. At K = 10 the audits take about 50. About 400 GPU-h for 10 T1 nodes, and about 600 with T2.

## 6. Open questions for the author

1. ~~1GC-7RC~~ Settled 4 Nov 12:45: not public; MLAgentBench is the third suite (R1-1GC-FALLBACK).
2. ~~Which GPU model runs the T1 label table, and where is the proposer served?~~ HoreKa 2 H100 for the whole T1 tier, Ada as whole-table fallback (R1-T1-HOREKA, 4 Nov 13:45). *(Earlier: Ada for T1 label runs;* the proposer on deepthought (two TITANs) if O5 passes, else a 4090 (R1-BX-PROPOSED-CONFIRM).
3. ~~Which host was the Apptainer check run on?~~ deepthought2 (R1-APPTAINER-HOST).
4. ~~Memory modes and the campaign count per T1 node~~ both modes, about 12 campaigns (R1-BX-PROPOSED-CONFIRM).
5. Whether the main proposer's diff competence suffices (first measured in G.0 step 6 and G.4).
