# Track G runbook — real-task benchmarks, tiers T1 and T2 (rewritten 4 Nov 2026)

**Status.** Rewritten 4 Nov 2026 by the chat session (Claude), AI-assisted, after the author adopted `docs/r1/proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` in full (PLAN §10 R1-BX-D1 … D14, R1-BX-REVISIONS). The 27 Oct proposal this file used to hold (autoresearch plus MLGym only if a container existed by 10 Nov; evaluation/transfer only) is superseded; it remains in git history.

**This file authorizes nothing.** RUNBOOK Track G (G.0–G.6) and the PLAN §10 rows govern. Census, porting and pilots are ENGINEERING_ONLY. The T1 sweep (G.5) and the T2 closed loop (G.6) are EVIDENCE and need the author's authorization notes.

**Who does what.**
- The **Mac agent** (`MAC_LOCAL_RUNBOOK_20261104.md`, task M10) writes the node specs, parsers, diff support and tests, and drafts the T1/T2 selection and the authorization notes.
- The **operator** (`OPERATOR_RUNBOOK_20261104.md`, phase O8) runs the census, host smoke runs, the pilot, the sweep and the closed loop.

## 1. Tiers and target

- **Target:** 12–16 real tasks from ≥ 3 suites and ≥ 5 domains (LM, vision, graph, tabular, time series, text classification, RL). Variants of one task do not count.
- **T0:** the 8 CPU nodes (testbed; single-parameter edits as the low-interaction condition).
- **T1 (label + evaluation):** autoresearch (short fixed-step variant); 1GC-7RC lighter tasks: TinyShakespeare, Forest Cover, ETTh1, AG News, possibly ogbg-molhiv; MLGym lighter tasks: CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task (check against the MLGym task table).
- **T2 (evaluation only):** 1GC-7RC TinyImageNet and VOC; optional fourth suite: MLAgentBench light tasks (cifar10, imdb, ogbn-arxiv).
- **Not used:** RE-Bench, MLE-bench (hours per run, cannot be audited); DACBench (different problem type).
- The author fixes the T1/T2 lists after the census (G.3).

## 2. Integration principle

Use each suite's **task assets** — data, baseline script, evaluator — as a harness node. Do not use the suites' agent frameworks: our harness is the loop. Per node:
- a `NodeSpec` YAML under `configs/nodes/` in the harness, registered in `nodes/registry.py`, with `editable_paths` (what a diff may touch), `frozen_paths` (evaluator, data loader, metric code), the run command, metric and direction;
- a **fixed step or token budget** (never wall-clock): 1–2 min for label runs, up to about 5 min for closed-loop evaluation, on the table's GPU model;
- a metric parser that reports divergence (non-finite loss, or no metric at the budget) as its own outcome;
- a per-run working copy and resource limits (GPU by UUID, a CPU and memory cap, a timeout of 3 × the measured run time);
- test-scored tasks select on validation only (R1-TRACKG-ROLE).

## 3. Containers (R1-BX-REVISIONS (g))

In order of preference:
1. **No container.** Port the task natively into the harness venv. Most T1 candidates are plain PyTorch scripts.
2. **Docker where it exists:** on deepthought the author is in the `docker` group. On the 4090 hosts, check `groups`, `docker info` and `podman --version` first.
3. **Apptainer** where Docker is unavailable, without admin help:
   - `apptainer pull <name>.sif docker://<image>`;
   - `apptainer exec --nv --containall --bind <per-run copy>:<path> <name>.sif …`, or `--writable-tmpfs`;
   - `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` under `/ceph/dwong/`;
   - record the `.sif` sha256 in provenance, like a GGUF.
4. Never ask for `docker` group membership. If deepthought2 is ever needed, ask for rootless Podman (subuid/subgid entries for `dwong`) or Apptainer.

*Open:* the author's 4 Nov check found Apptainer and Singularity, no Podman and no subuid/subgid entries, on a host still to be named. The author confirms the host with `hostname`; if it was deepthought, the check is repeated on deepthought2. deepthought2 is not a run host unless a PLAN row adds it.

## 4. Steps

### G.0 — Census (operator; Ada first; ENGINEERING_ONLY)

Per candidate task:
1. **Licence and availability:** the repository, its licence, and the licence of each dataset. In particular, check whether the 1GC-7RC repository (arXiv 2605.17046) is public now; R1-TRACKG-SCOPE found it was not. If it is still not public, **STOP** for the author (rebuild from the paper and public data, disclosed; or MLAgentBench as the third suite).
2. **Run cost** at a candidate fixed budget on each GPU model available: RTX 6000 Ada (first), RTX 4090, TITAN X. Record wall time, peak VRAM, and CPU and RAM use.
3. **Determinism:** the same seed twice; record whether outputs are bit-identical.
4. **Noise floor:** 10 seeds × 3–5 representative edits plus the baseline, on one GPU model. Record σ̂ for the training seed and, where it exists, the split seed, and the tail shape (the largest |z| and the excess kurtosis).
5. **D21 verdict** under the 22 Oct rule.
6. **D28 liveness** with the main proposer (once X.7 names it), using code-level diffs: 2 instances × W = 10.
7. Shared or co-tenanted cards: the R1-COMPUTE co-tenancy rule; Ada work is resumable per unit.

Output: `docs/r1/reports/TRACKG_CENSUS_<date>.md`, one row per candidate, plus the screening funnel per suite (R1-BX-D12). Copy raw records back under `results/r1/trackg/census/`.

### G.1 — Porting (Mac code; operator smoke)

The Mac agent writes the node specs, parsers and tests against fake runs. The operator runs a stub-manager smoke campaign per node on the census host. Done when scope enforcement rejects an edit to a frozen path and the smoke manifest is complete.

### G.2 — Harness diff support (Mac; R1-BX-D4)

- Diff application inside the per-run working copy, refusing any hunk outside `editable_paths`.
- **Inert detection:** the diff leaves the executed code unchanged (empty after whitespace and comment normalisation, or an AST equal to the incumbent's).
- **Duplicate detection:** a normalised diff hash and a hash of the resulting code state, against every evaluated state of the campaign.
- **Provenance:** diff text, its hash, files touched, and the resulting code-state hash in the trial record.
- Schema `manager_proposal/v2-diff` *(proposed name)*; the T0 path `manager_proposal/v1` is unchanged and byte-identical (tested).
- Independent review; pinned in the RUNBOOK pin table before any GPU sweep.

### G.3 — T1/T2 selection (author)

From the census: the T1 and T2 lists, the T1 label-run GPU model, and the proposer host (deepthought two-card serving if O5 qualifies it; otherwise a 4090). One GPU model per label table; σ̂ for a table comes from a floor measured on that GPU model. PLAN §10 row.

### G.4 — T1 pilot (operator; ENGINEERING_ONLY)

On 2–3 T1 nodes: a short sweep-2-shaped run with the main proposer, thinking off, `cache_prompt: false`. Measure throughput (proposals per hour, run time), diff liveness, duplicate, inert and divergence rates, and prompt lengths with code context. **Then the coordinating agent recomputes the R1-BX-D14 dates and reports any change to the author before applying it.**

### G.5 — Sweep 2, T1 part (operator; EVIDENCE; needs the author's note)

- W = 20; about 12 campaigns per T1 node; memory `append_only_summary` and `none` as on T0 *(proposed)*.
- About 150 audited proposals per node. K = 6 (labels 7001–7003, evaluation 7006–7008, *proposed*) only if R1-BX-D3's check has passed; otherwise K = 10.
- The S1.1 edit–edit interaction measurement on each T1 node; per-node interaction strength reported as a covariate.
- STOPs: as B.1b, plus a divergence rate above the census rate by more than a factor of 2 *(proposed)*, a scope violation, or a pin mismatch.

### G.6 — T2 closed loop (operator; EVIDENCE; part of D.3)

The main proposer and the API proposer (R1-BX-D6). API calls go only from the host the authorization note names, under the secrets rule; every request and response is logged with the returned model version.

## 5. Cost (rough; calibrated by G.4)

About 40 GPU-h per T1 node at 2-minute runs and K = 6: noise floor (5 edits × 10 seeds) about 2, sweep-2 executions (about 12 campaigns × W = 20) about 8, audits (150 × 6) about 30. At K = 10 the audits take about 50. About 400 GPU-h for 10 T1 nodes, and about 600 with T2.

## 6. Open questions for the author

1. Is the 1GC-7RC repository public now? If not, rebuild its tasks or switch to MLAgentBench as the third suite.
2. Which GPU model runs the T1 label table, and where is the proposer served?
3. Which host was the Apptainer check run on?
4. Memory modes and the campaign count per T1 node (proposed: as T0, about 12 campaigns).
5. Whether the main proposer's diff competence suffices (first measured in G.0 step 6 and G.4).
