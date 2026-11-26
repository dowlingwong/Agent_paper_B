# Paper B (R1) — review of benchmarks and plan weaknesses, with proposed revisions

**Date:** 4 Nov 2026 · **Author of draft:** Claude (chat session) · **Status:** **ADOPTED IN FULL by the author, 4 Nov 2026 (chat):** all of D1–D14 in section 6, each at its recommended default, and the revisions in sections 2–5 and 8.

**For the coordinating agent:**
- Draft one PLAN §10 row per decision D1–D14, dated 4 Nov 2026, worded from section 6. The author commits them, or the author authorises you to commit them in his words.
- D3 (K = 6) is adopted **conditionally**: it takes effect only if the sweep-1 subsampling check passes (section 4). If the check fails, K stays 10 and you STOP for the author.
- D8 must be committed **before** any sweep-2 labels are analysed.
- Dates in section 5 / D14 are targets; recompute from measured throughput after the T1 pilot and report changes to the author before applying them.
- Then revise PLAN, RUNBOOK and both execution runbooks (Mac-local and server) per section 7.
- Routing follows the 4 Nov split (section 7):
  - Mac-local work → the Claude on the Mac;
  - all server experiments → the single SSH agent.

---

## 0. Summary

1. **The 8 CPU nodes cannot carry the paper's main evidence.**
   - Six of the eight share one OpenML logistic-regression template.
   - The pinned 7B manager edits almost only `max_iter` and `C`, so headroom is close to a one-knob monotone climb.
2. **The "three harder benchmarks" are three suites, not three nodes:** autoresearch (1 task), 1GC-7RC (7 tasks), MLGym (13 tasks).
   - Their adopted role is still only "proposed: evaluation/transfer".
   - Track G is not built.
   - So today **C3 is trained and gated on toy nodes only**.
3. **The deeper problem is where the labels come from, not the node count.** Some GPU tasks must become label nodes, and generalisation should be tested leave-one-suite-out.
4. **The single-parameter edit schema plus one-knob nodes makes the loop near-bandit by construction.** A Track S null would then be read as circular.
5. **Target:** 12–16 real tasks from ≥ 3 suites and ≥ 5 domains, with the CPU pool kept as a controlled testbed.
   - This is affordable only with short label runs, K = 6 audits and about 150 audited proposals per node (section 4).

---

## 1. Corrections to the 4 Nov chat explanation of the DAC/post-training setup

| # | Earlier statement | Problem | Correction |
|---|---|---|---|
| 1 | "Three harder benchmarks for evaluation and transfer" | Counted as three nodes | Three suites (1 + 7 + 13 tasks); role proposed, not adopted; Track G not built |
| 2 | Six of eight nodes are one-knob climbs | Did not say this pushes the problem toward a bandit by construction | See P3 |
| 3 | A causal decoder's `<decide>` readout is "about as good as bidirectional" | Overclaim: history tokens placed **before** the proposal cannot condition on it | Serialisation order matters; see P13 |
| 4 | "TabPFN ≈ Kev would be a clean finding" | Clean only under equal information; TabPFN sees hand features, Kev sees text; TabPFN classification has a class cap (verify for the version used) | See P7 |
| 5 | R-B "if time permits" | Contradicts the 23 Oct decision that the self-control vs trained vs hybrid comparison is a novelty pillar | See P10 |
| 6 | "~1k usable labels per sweep; extend if the learning curve asks" | More toy-node labels do not fix the domain problem | See P2 |

---

## 2. Issues and proposed revisions

Severity: **F** = fatal for ICML if unfixed; **M** = major; **m** = minor.

### P1 (F) — Main evidence sits on toy nodes
- **Problem:** six of eight nodes are one template with one effective knob. Comparable work evaluates on whole suites: MLGym-Bench (13 tasks), MLAgentBench (13), MLE-bench (75), RE-Bench (7).
- **Revision:** demote the CPU pool to a controlled testbed (theory validation, cheap Track S, ablations). Main tables move to real tasks (section 3).

### P2 (F) — Labels come only from toy nodes; GPU tasks are transfer-only
- **Problem:** a weak result on GPU tasks cannot be separated from domain shift; a strong one invites "why not train there?".
- **Revision:**
  - Part of the GPU tasks become **label nodes** (tier T1, section 3).
  - Primary generalisation test is **leave-one-suite-out** (train on two suites, test on the third).
  - LONO within the CPU pool becomes secondary.

### P3 (F) — Edit schema makes the problem near-bandit by construction
- **Problem:** one parameter per proposal (schema in harness `llm/providers.py`) on nodes with one effective knob means edits barely interact, so the NF part "an edit's increment does not depend on earlier keeps" holds almost automatically. A Track S null would then be read as "the environment could not show sequentiality" and the "when DAC reduces" argument as circular.
- **Revision:**
  - Allow code-level diffs on GPU nodes (autoresearch already edits any part of `train.py`).
  - Keep the single-parameter schema on CPU nodes as an explicit **low-interaction condition**. The two conditions then become an NF contrast rather than a confound.
  - Run the S1.1 edit–edit interaction measurement on GPU nodes; report per-node interaction strength as a covariate ("distance from NF").
  - Harness changes needed: diff application, inert/duplicate detection for diffs, provenance. Draft, review and pin before any GPU sweep.

### P4 (F) — Track S runs only on two CPU nodes, and S0.1 has not passed
- **Problem:** conclusions on `digits_mlp` / `tabular_mlp` do not generalise, and the S3 forks may not finish before January.
- **Revision:**
  - Add 1–2 GPU nodes to Track S: autoresearch (short fixed-step variant) and one RL-type task with high noise and interacting edits.
  - Declare a **fallback date** in PLAN: if Track S has no campaign-level result by that date, the DAC-reduction argument rests on the theorem plus synthetic controls, and the paper says so explicitly.

### P5 (M) — Single proposer
- **Problem:** the main data come from the Track X pick only, with the 7B as second source. Reviewers will ask whether results hold for another proposer.
- **Revision:** add one API proposer in **closed-loop evaluation only** on T1/T2 nodes. Only Track S needs seed-replayable sampling; closed-loop evaluation does not.

### P6 (M) — Missing practitioner baselines
- **Revision:** the main table must contain:
  - **Karpathy default:** always execute, single run, keep if Δ̂ > 0;
  - **Fixed-r replication + test:** racing style, keep by a t-test at a declared level.
- Add them to the ladder if absent. They show the gain in terms practitioners use.

### P7 (M) — TabPFN vs Kev is not information-matched
- **Revision:**
  - Define a shared feature view: hand features + proposal-text embedding reduced by PCA.
  - Run TabPFN and Kev once under equal information, in addition to their native inputs.
  - Use TabPFN in regression mode and bin its predictive distribution, to avoid the classification class cap (verify the cap for the version used).

### P8 (M) — The C3 gate statistic is weak
- **Problem:** "≥ δ_n on ≥ 2 of 8 nodes" has multiplicity issues and does not scale to more nodes.
- **Revision:**
  - Primary criterion: across-node aggregate (IQM of gap closed and probability of improvement, with node-stratified bootstrap CIs). Per-node table secondary.
  - Commit it to PLAN **before any sweep-2 labels are analysed**, so it counts as preregistered.

### P9 (M) — Node screening induces selection bias
- **Problem:** the D21 rule keeps only nodes where noise causes misjudgement; reviewers can say the tasks were chosen to favour the method.
- **Revision:**
  - Report the screening funnel (screened / qualified, per suite).
  - Evaluate non-qualifying nodes in an appendix to show the controller does not hurt when noise is low (it should approach greedy).

### P10 (M) — R-B role is inconsistent; "RL" wording is risky
- **Problem:** R-A is cost-sensitive classification (decision-focused learning); calling it RL invites criticism. R-B being optional contradicts the three-way comparison being a pillar.
- **Revision:**
  - The self-control arm of the three-way comparison is **A4**: the Track X pick, zero-shot, isotonic-calibrated. It does not depend on R-B.
  - R-B becomes an optional "trained self-control" ablation.
  - In the paper, only R-B is called RL; R-A is "decision-focused fine-tuning".

### P11 (m) — autoresearch uses a wall-clock budget
- **Problem:** a fixed wall-clock budget makes outcomes depend on GPU model and co-tenancy. Mixing TITAN/4090/Ada or sharing cards contaminates the noise.
- **Revision:** labels use a **fixed step/token budget**; one GPU model per table (consistent with the 24 Oct "no mixing hosts within one table" rule).

### P12 (m) — Soft-label width assumes homoscedastic Gaussian noise
- **Problem:** fine on CPU nodes; RL and LM training often have heavy tails and occasional divergence.
- **Revision:** estimate noise per GPU node; record divergence as a separate outcome class, not folded into the mean.

### P13 (m) — Serialisation order for causal decision models
- **Revision:**
  - Place the proposal **after** the history, immediately before `<decide>`.
  - Add an E6 probe comparing history-first vs proposal-first.

---

## 3. Benchmark plan

**Target:** 12–16 real tasks, ≥ 3 suites, ≥ 5 domains (LM, vision, graph, tabular, time series, text classification, RL). Variants of the same task do not count toward the total.

| Tier | Role | Candidates (cost per run to be verified one by one) |
|---|---|---|
| T0 controlled testbed | Theory validation, Track S, ablations, low-interaction condition | The current 8 CPU nodes |
| T1 label + evaluation | Train C3, gate, leave-one-suite-out | autoresearch (short fixed-step variant); 1GC-7RC lighter tasks: TinyShakespeare, Forest Cover, ETTh1, AG News, possibly ogbg-molhiv; MLGym lighter tasks: CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task (check against the MLGym task table) |
| T2 evaluation only | Closed-loop transfer, API proposer | 1GC-7RC TinyImageNet, VOC; optional 4th suite: MLAgentBench light tasks (cifar10, imdb, ogbn-arxiv) |
| Not recommended | — | RE-Bench, MLE-bench (hours per run, cannot be audited); DACBench (different problem type) |

**Integration principle:** use the suites' **task assets** (data, baseline script, evaluator) as harness nodes. Do not use their agent frameworks. Our harness is the loop, and all nodes then share one runner, provenance and audit path. This also removes most of the need for containers (section 8).

**Per candidate, the server agent records:** run time at the fixed budget on each GPU model, VRAM, determinism, a 10-seed noise floor on 3–5 representative edits, D21 verdict, D28 liveness with the main proposer.

---

## 4. Cost model (rough; calibrate with a pilot)

With the current K = 10 and 5-minute runs, auditing alone costs about 125 GPU-h per node, which is infeasible. Three levers:

1. **Short label runs** (1–2 min, fixed steps). 5-minute runs only for closed-loop evaluation.
2. **K = 6** (3 label + 3 evaluation seeds), with soft-label width from each node's own σ.
   - **Validate first on existing data:** subsample sweep-1 K = 10 audits to K = 6 and check label and gate stability. CPU only, a few hours.
3. **≈ 150 audited proposals per T1 node.**

Assuming 2-minute runs and K = 6:

| Per T1 node | Runs | GPU-h |
|---|---|---|
| Noise floor (5 edits × 10 seeds) | 50 | ~2 |
| Sweep-2 executions (~12 campaigns × W = 20) | ~240 | ~8 |
| Audits (150 × 6) | 900 | ~30 |
| **Total** | | **~40** |

10 T1 nodes ≈ 400 GPU-h; with T2 closed-loop evaluation ≈ 600 GPU-h.

**Hosts:**
- 2× RTX 4090: partly available; Track X holds TASL-2 until ~15 Nov.
- 4× TITAN 12 GB (deepthought): exclusive, slower. A model can be served across two TITANs, so the main proposer could run there and free 4090 time for task runs and Track P.
- 8× RTX 6000 Ada (shared, interruptible): resumable work only; the sweep already resumes per root.
- One GPU model per label table (P11).

---

## 5. Timeline and cuts (proposal)

Current freezes: B.7 26 Nov, D.3 20 Dec, manuscript 10 Jan, ICML abstract ≈ 16 Jan.

**Track G becomes the critical path and must start now**, not after B.7.

| Item | Proposal |
|---|---|
| B.6 CPU-node extension | Cut; replaced by T1 GPU nodes |
| R-B | Optional ablation (P10) |
| Stage D (DAgger) | One round on 1–2 T1 nodes only |
| GPU-node noise floors and liveness | Start on Ada while Track X holds TASL-2 |
| B.7 gate | Move to ≈ 8 Dec, aggregate criterion (P8), on CPU + T1 labels |
| D.3 closed loop | Move to ≈ 3 Jan |
| Manuscript | 10 Jan unchanged; writing runs in parallel from early Dec |
| Track S fallback date | ≈ 15 Dec (P4) |

The coordinating agent should recompute these dates from measured throughput after the T1 pilot.

---

## 6. Author decisions (each with a recommended default)

| ID | Decision | Recommended | Why |
|---|---|---|---|
| **D1** | Role of GPU tasks | Part become **label nodes** (T1); the rest evaluation only (T2); primary generalisation = leave-one-suite-out | Answers the domain-shift objection directly (P2) |
| **D2** | Benchmark scope | 12–16 real tasks from autoresearch, 1GC-7RC, MLGym; MLAgentBench only if cheap; CPU pool kept as T0 | Matches field norms; three suites allow leave-one-suite-out |
| **D3** | Audit seeds | K = 6 (3 + 3), **conditional on** the sweep-1 subsampling check | Halves audit cost; checkable on existing data |
| **D4** | Edit schema on GPU nodes | Code-level diffs on GPU nodes; single-parameter kept on CPU nodes as the low-interaction condition | Removes "bandit by construction" and turns it into an NF contrast (P3) |
| **D5** | Label budget | Fixed step/token budget; one GPU model per table | Wall-clock budgets mix hardware into noise (P11) |
| **D6** | Second proposer | One API proposer, closed-loop evaluation only; preferably not DeepSeek-V4.1-Flash, since it writes the R-B warm-up demonstrations | Generality across proposers (P5) |
| **D7** | Practitioner baselines | Add Karpathy-default greedy and fixed-r replication + t-test | Cheap, most interpretable for reviewers (P6) |
| **D8** | C3 gate | Aggregate IQM / probability of improvement with stratified bootstrap; committed before sweep-2 analysis | Multiplicity-safe, scales with nodes (P8) |
| **D9** | Self-control arm and wording | A4 is the self-control arm; R-B optional; R-A called decision-focused fine-tuning | Keeps the three-way comparison without depending on R-B (P10) |
| **D10** | Track S scope | Add 1–2 GPU nodes; fallback date ≈ 15 Dec | Generality and schedule safety (P4) |
| **D11** | Cuts | B.6 cut; Stage D on 1–2 nodes; R-B optional | Frees time for Track G |
| **D12** | Screening transparency | Report the funnel; evaluate non-qualifying nodes in an appendix | Pre-empts selection-bias criticism (P9) |
| **D13** | TabPFN comparison | Add an information-matched comparison; TabPFN in regression mode | Makes "forecaster is a commodity" testable (P7) |
| **D14** | Dates | B.7 ≈ 8 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan unchanged | Fits Track G on the critical path |

---

## 7. Routing (per the 4 Nov two-runbook split)

**Mac-local (Claude on the Mac):**
- PLAN §10 rows for adopted decisions (drafts for the author).
- RUNBOOK revision: Track G as critical path, new dates, cuts.
- Harness changes: diff-level edits (D4), fixed-step budgets (D5), practitioner baselines (D7), gate statistic code (D8), TabPFN information-matched view (D13), serialisation order and E6 probe (P13).
- Sweep-1 K = 10 → 6 subsampling check (D3), CPU only.
- Manuscript wording changes (D9, P9).

**Server agent (SSH to all hosts):**
- Per-candidate cost/noise/liveness census (section 3) — Ada first.
- Porting suite task assets into harness nodes; container-free where possible (section 8).
- T1 pilots, then sweep 2 on T1 nodes; audits.
- Track S GPU extension (D10).
- Closed-loop evaluation on T2 with the API proposer (D6).

Every phase keeps the existing protocol: an independent fresh agent reviews; the executing agent fixes.

---

## 8. Container access (deepthought vs deepthought2)

- The author is in the `docker` group on **deepthought**, not on **deepthought2**.
- Being in the `docker` group is effectively root on that host, so admins are often reluctant to grant it; do not request it as the first option.

Order of preference:

1. **Avoid containers:** port task assets natively into harness venvs (section 3). Most T1 candidates are plain PyTorch scripts. Isolation for code-level diffs can be handled with a per-run working copy and resource limits.
2. **Run container-dependent work on deepthought**, where docker access exists, or on the 4090 hosts if Docker/Podman is available there (check `groups`, `docker info`, `podman --version`).
3. **On deepthought2, check what exists without admin help:** `which apptainer singularity podman` and `grep "^$USER:" /etc/subuid /etc/subgid`. Apptainer can run Docker images without root (`apptainer exec docker://…`). Rootless Podman works if subuid/subgid entries exist.
4. **If deepthought2 is still needed, ask Kylian for rootless Podman** (subuid/subgid entries for `dwong`) **or Apptainer**, not for `docker` group membership.

**Check result (author, 4 Nov):** on the host checked, `/usr/bin/apptainer` and `/usr/bin/singularity` exist; Podman is absent; `dwong` has no subuid/subgid entries. The author must confirm whether this host is deepthought or deepthought2 (`hostname`); if it was deepthought, repeat the check on deepthought2.

- **Apptainer is the container route where Docker is unavailable.** No admin request is needed. Rootless Podman is not possible without subuid/subgid entries, and it is not needed.
- Apptainer usage notes for the server agent:
  - Pull Docker images rootless: `apptainer pull <name>.sif docker://<image>`; run with `apptainer exec --nv` for GPU.
  - Images are read-only: use `--writable-tmpfs` or bind a per-run working copy (`--bind`); use `--containall` (or `--cleanenv`) to keep the host environment out.
  - Set `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` under `/ceph/dwong/` to avoid the home quota.
  - Record the `.sif` sha256 in provenance, like GGUF files.
- MLGym's own framework drives Docker/Podman; under section 3 only its task assets are used, so this does not matter. If a task's environment is only shipped as a Docker image, run it through Apptainer.

---

## 9. Sources

- karpathy/autoresearch (fixed 5-minute wall-clock training budget): https://github.com/karpathy/autoresearch
- MLGym (13 tasks): https://arxiv.org/abs/2502.14499
- MLAgentBench (13 tasks): https://www.emergentmind.com/topics/mlagentbench
- MLE-bench (75) and RE-Bench (7), survey: https://arxiv.org/pdf/2506.08800
- 1GC-7RC: arXiv 2605.17046
