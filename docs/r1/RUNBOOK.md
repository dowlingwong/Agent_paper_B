# Paper B (route R1) — runbook

Canonical plan: [PLAN.md](PLAN.md). Revised 12 October 2026 for R1-REFRAME, R1-INDEX and R1-GATE-FIRST (PLAN §1). This runbook says what to do, in which order, how to tell it is done, and where the author decides. Progress goes only into [STATUS.md](STATUS.md). Drafted 9 October 2026 by an AI agent (Claude); AI-assisted, not human review.

---

## 1. Ground rules (deliberately few)

1. **Authority.**
   - PLAN.md, this runbook and STATUS.md are the only planning documents.
   - Do not create new plan, decision-sheet or review files outside `docs/r1/`.
   - Phase-end reviews go to `docs/r1/reviews/`.
   - Archived files (`archive/old_b_2026-10-09/`) are history, never instructions.
2. **Decisions.** Only the author decides. A decision is recorded as a dated row in PLAN.md (§1 or §10) before work depends on it. Agents propose and never adopt.
3. **Evidence runs.**
   - A run produces evidence when its outcomes feed a claim: Phase 1 branch collection, Phase 3 deployment.
   - Each evidence run needs a short authorization note, `docs/r1/authorizations/<phase>_<date>.md`, which the author writes and commits himself.
   - Engineering runs, pilots and noise-floor measurements need no authorization. They are labelled `ENGINEERING_ONLY` or `PILOT` and never quoted as results.
4. **Pre-declaration.** The primary contrasts, sample sizes and analysis script for Phase 3 are committed, with a hash, before any Phase 3 outcome exists. Phase 1's headroom criterion is committed before branch collection.
5. **Honesty.**
   - AI-assisted work is labelled as such.
   - A box is ticked only when its acceptance condition has been checked.
   - A stopped run is reported as stopped.
6. **Repos.**
   - The harness work happens on branch `r1` of `autoresearch_harness` (D14, proposed default).
   - This repository pins the harness commit used by every run.
   - Never force-push, rewrite pushed history, or delete ledgers.
7. **Reviews.** One fresh-session AI-assisted review at the end of each phase, followed by one correction round. No reviews in between unless a STOP is hit.

## 2. Roles

| Role | Who | Does |
|---|---|---|
| Author | Dowling Wong | Decides; writes authorization notes; final read |
| Implementation agent | Any agent session given a phase prompt | Executes tasks, runs checks, updates STATUS |
| Coordinator | Planning session (Claude) | Writes phase prompts, reviews, keeps PLAN/RUNBOOK current |

## 3. Phases

Overview:
- **Phase 0**: foundations, noise floors, decisions.
- **Phase 1**: branch data and the headroom gate.
- **Phase 2**: configurator.
- **Phase 3**: deployment comparison.
- **Phase 4**: write-up and submission.

---

### Execution order: build locally first, then experiment (adopted 9 Oct 2026)

> **Revised order (12 Oct, R1-GATE-FIRST).** L1–L8 are done (STATUS); L2 is covered by the PLAN §10 decisions. E1 moves up, because it needs none of L9–L14 and it decides which nodes the rest is built for. L11 (configurator scaffold) is deferred until the E5 headroom gate passes. A theory track T1–T3 runs in parallel from now. The order is:
> E1 + T1 → L8b, L9, L10 (+ T2) → E1b (pilot headroom pre-check) → L12, L13, L14 (+ T3) → E2 STOP → E3–E5 → only if the gate passes: L11, E6 → E7, E8.

Detailed specification for L1–L14: [BUILD_RUNBOOK.md](BUILD_RUNBOOK.md). Agent prompts live in `docs/r1/prompts/`; the first is `BUILD_BATCH1_PROMPT.md` (L1, L3, L5, L6).

Steps L1–L14 run on the Mac (CPU, local Ollama model) and produce `ENGINEERING_ONLY` output only. Steps E1–E8 are the experiments. Each step finishes before the next one starts, unless a step says otherwise. Cross-references point to the phase tasks below.

**Local build**

| # | Step | Phase task | Done when |
|---|---|---|---|
| L1 | Housekeeping: one commit in this repo (archive plus `docs/r1`); harness branch `r1`; environment synced; existing harness tests green | 0.1 | Commits and a green baseline in STATUS |
| L2 | Author confirms the build-time defaults: D1 (compute budget plus LLM cap), D3 (core actions), D4 (keep override only through verify), D14, D19 (`LocalWorker`), D20 (benchmark scope) | 0.6 (early part) | Rows dated in PLAN §10 |
| L3 | Fix the four harness defects, each with a test | 0.2 | Tests fail before and pass after |
| L4 | Pin a local manager model (Ollama digest); LangGraph-manager smoke on `lr_synthetic`, first dry, then real | 0.4 (cost part) | Smoke ledger plus latency numbers |
| L5 | Decision hooks E0/E1/E2, `control_decision` event, `skipped` state, compute and LLM-call budget; regression test showing default behaviour is byte-identical | 0.3 | Regression test green |
| L6 | Actions: skip, revise, verify (fresh-seed re-run, frozen response, demote), stop; unit tests on `lr_synthetic` | new, completes 0.3 | Each action tested |
| L7 | Restore and branch machinery at E1/E2, including the bit-exact restore audit on CPU nodes | 1.2 (built early) | Audit reproduces original metrics |
| L8 | Benchmark adapters, local subset: 5 OpenML tasks; check the existing MLAgentBench adapter; 2–3 light MLGym tasks (install and CPU feasibility) | 1.1 (subset) | Smoke campaign per adapter |
| L8b | Noisy CPU nodes (D21, added 12 Oct): 2–4 SGD-trained small MLP / small CNN nodes on CPU where the training seed moves the metric, with training-seed and split-seed injection as in L3 | 0.4 / 1.1 | Smoke campaign per node; a changed seed changes the metric |
| L9 | Port B's branch-record schema and cluster bootstrap to trial-epoch sibling sets; leak tests | PLAN §8 | Tests green on fixtures |
| L10 | Offline baselines on a synthetic branch table: ρ, random, noise-aware threshold, PACE-style gate, racing-style rule, **the C2 index policy (from T2)**, harness heuristics, AWR-MLP, hindsight oracle; secondary: fixed schedules, risk-vs-advantage ridge | 1.4 (code) | Scores on the fixture |
| L11 | **Deferred until the E5 headroom gate passes (R1-GATE-FIRST).** Configurator scaffold: compact serialiser (≤ 512 tokens), late-fusion head on ModernBERT-large / Laya, Kev-0.8B wrapper; supervised Brier step, then a REINFORCE step with bounded-Brier reward; runs end-to-end on the Mac (MPS) | 2.2 (code) | Trains and evaluates on the fixture |
| L12 | LLM self-control side query (forked context), scored against the table | 1.4 (code) | Scores logged; manager context untouched |
| L13 | End-to-end dry run on one noisy CPU node: campaign with hooks → branches → table → index policy and baselines (a stub in place of the configurator) → short deployment → analysis script | — | One command reproduces it |
| L14 | Phase-0 build review (fresh session) and one correction round | §1 rule 7 | Review filed, fixes in |

**Theory track (added 12 Oct; runs in parallel, on the Mac)**

| # | Step | Done when |
|---|---|---|
| T1 | Formal model: the governed loop as noisy sequential selection with an incumbent (proposal law, m = J + η, keep-if-better, restore on non-keep). Literature map: ranking & selection, knowledge gradient (Frazier & Powell), racing (F-Race / irace), best-arm identification, PACE; what each assumes and where the loop departs | A note in `docs/r1/theory/` with the model and the map |
| T2 | Derivations: (i) the value of verify with r paired runs, and of a threshold z, as functions of \|Δ̂\|/σ_n, ϱ and remaining budget; (ii) the winner's-curse bias of `current_best` and the induced drop in acceptance of later true improvements; (iii) the resulting index policy (D23) | Statements with proofs; index policy implemented for L10 |
| T3 | Monte-Carlo simulator of the loop that checks T2's predictions, then calibrated with E1's measured σ_n and ϱ | Predicted and simulated error rates agree; plots regenerated by script |

**Experiments**

| # | Step | Phase task | Gate |
|---|---|---|---|
| E1 | **Now first.** Noise-floor and cost pilot (`PILOT`): σ_n separately for the training seed and the split seed, ϱ, determinism, run cost, LLM latency, on local nodes, the L8b noisy nodes and light benchmark tasks | 0.4 | Answers question 1: which CPU nodes have enough noise |
| E1b | Pilot headroom pre-check (`PILOT`, not evidence): a small branch table on the 1–2 noisiest nodes from E1; hindsight oracle minus the best simple baseline (noise-aware threshold or PACE-style gate) | 0.4b (new) | Answers question 2. A clear fail goes straight to E2 with the fallback |
| E2 | **STOP:** the author sets the remaining decisions, D21 (noise nodes), the practical target (D18) and the headroom criterion, and checks the premise with E1 and E1b | 0.6 | Premise holds, or the fallback paper |
| E3 | Scale the pool: 10–20 OpenML tasks plus MLGym light tasks; noise rows | 1.1 | — |
| E4 | Pre-declare; authorization note; branch collection on development instances | 1.3 | Authorization |
| E5 | Offline baselines and LLM self-control on the real table; **headroom gate** | 1.4–1.5 | Gate passes, or the fallback paper |
| E6 | **Only if the E5 gate passes:** build L11, then D16 decided with data; train the configurator families; offline evaluation and ladder; select candidates by the pre-fixed rule | 2.1–2.4 | Selection rule |
| E7 | Pre-declare Phase 3; authorization; deployment on held-out instances and benchmarks (MLAgentBench, MLE-bench Lite subset; autoresearch on GPU) | 3.1–3.2 | Authorization |
| E8 | Analysis, ablations, transfer; manuscript; rerun the novelty sweep; TMLR | 3.3, Phase 4 | Quality-bar checklist (PLAN §9) |

**Compute** (revised 12 Oct)
- **Mac** (M1 Pro, 16 GiB): code, docs, tests, T1–T3, and CPU-only pilots with the scripted proposer (E1, E1b-scripted), analysis, E2. **No LLM runs on the Mac** (R1-COMPUTE, 12 Oct).
- **deepthought** (deepthought2.etp.kit.edu; code under `/ceph/dwong/`; many CPU cores, large RAM and storage, 4 × TITAN 12 GB): every LLM-backed run with the pinned 7B manager: L4 re-pin, L12 live smoke, the E1b LLM rerun, E3–E5 at scale (parallel CPU workers, one pinned manager instance per TITAN); MLGym light tasks if Docker or Podman is available there; LLM self-control side queries; Phase 2 small-model training if the gate passes. Batch prompt: `docs/r1/prompts/DEEPTHOUGHT_BATCH1_PROMPT.md`.
- **Ada** (`ucrtasl`, shared 8 × RTX 6000 Ada 48 GB, one card under the co-tenant rule; tooling must survive periodic server loss): the stronger-manager deployment check (D22) if it is an open model; the autoresearch GPU noise pilot and deployment; the MLE-bench Lite held-out subset; any model above about 4B.
- The branch data for one table come from one manager backend (D6, D15). A pilot on the Mac and a collection on deepthought use different backends, so the pilot stays `PILOT`.

### Phase 0 — Foundations and noise floors (target ~31 Oct 2026)

Nothing in Phase 0 is evidence for a claim. It produces the numbers on which the decisions rest.

#### 0.1 Repositories

- **Harness clone.** It exists at `~/Documents/autoresearch_harness` (cloned 9 Oct at `da8dcbd`; submodules not initialised). Create branch `r1` from `main` and record the base commit in STATUS. Initialise the `harness/claw-code` submodule only if D19 requires `ClawWorker`.
- **Lost ledgers.** The original ledgers are lost (PLAN §1, R1-LEDGERS). Record the SHA-256 of the surviving aggregate tables in the workshop-paper repo (`tables/*.csv`) as historical context, and quote none of them as R1 evidence.
- **Legacy code in this repository.** For each legacy item listed in PLAN §8, decide whether to move it to `archive/old_b_2026-10-09/code/` now or after Phase 1. Moving one is allowed only if no carried-over module and no kept test imports it. Record the decision.
- **First commit in this repository.** Commit the 9 Oct archive move and the new `docs/r1/` files as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Accept when:** STATUS records the harness base commit, the aggregate-table hashes and the legacy-code decision, and the first commit exists.

#### 0.2 Harness defects (fix or rule out, each with a test)

Each defect below is from the problem spec, Appendix A.

1. `prompt_manager` makes no LLM call (`manager/prompt_manager.py:19`). Make the documentation true. Any arm or analysis that claims LLM behaviour must use `langgraph_manager`.
2. `ClawWorker`'s legacy path writes `1 − val_bpb` under `node_spec.metric_name` (`worker/claw_worker.py:277`). Fix it. The historical autoresearch trials cannot be checked, because their ledgers are lost; tell the author, because it bears on the workshop paper's reported autoresearch numbers.
3. `_current_best` on resume ignores `metric_direction` and counts invalid trials (`control_plane/campaign.py:1043, 1136–1138`). Fix it, and add a resume test on a minimise node with an invalid high metric.
4. Seed injection: training seeds are hard-coded per node. Add a per-run seed parameter for every node and benchmark adapter. Where a seed also fixes the data split, add a separate split seed.

- **Accept when:** each item has a failing-before / passing-after test, and the harness test suite passes.

#### 0.3 Decision hooks (behaviour-preserving)

- **Epochs.** Add E0, E1 and E2 hooks to `run_real_campaign`. Split "evaluate" from "commit" so that an E2 action can precede the immutable ledger append.
- **New event and state.** Add a `control_decision` event carrying input hash, action, scores and version, and a terminal `skipped` trial state that is still ledgered.
- **Budget accounting.** Add compute accounting (worker runs and seconds) and an LLM-call counter, per D1.
- **Default unchanged.** With the default controller (always continue), a campaign's records must equal those of the unmodified harness. Prove this with a regression test on a dry-run node and one CPU node at fixed seeds.
- **Accept when:**
  - the regression test passes;
  - the hooks expose (Z, M, epoch) per PLAN §7 without exposing forbidden inputs;
  - a leak test fails if the projection is given audit or future data.

#### 0.4 Noise-floor and cost pilot (`PILOT`)

**For each existing CPU node, the L8b noisy nodes, 2–3 candidate OpenML additions and 2–3 light MLGym / MLAgentBench tasks (no ResNet):**
- **Determinism.** Same config and same seed, run twice: is the metric bit-identical? Run on CPU nodes, and on GPU nodes too.
- **σ_n.** The baseline metric across ≥ 10 seeds, measured **separately** for the training seed (split fixed) and the split seed (training seed fixed).
- **ϱ.** The across-seed correlation between the baseline and 5 typical single edits drawn from existing ledgers, at ≥ 10 shared seeds.
- **Run cost.** Worker wall time.

**For the manager:**
- latency and tokens per call for the pinned local model (D15) and for one API model;
- the cost of a side query.

**Output:**
- `docs/r1/reports/NOISE_FLOOR_<date>.md`;
- the misclassification rates of the default keep rule implied by the measured σ_n and ϱ (this replaces the illustrative 36 %).

**Accept when:** the report covers every node with numbers and their uncertainty, and the generating script is committed. The report ends with a node table that answers question 1 (R1-GATE-FIRST): which CPU nodes have enough training-seed or split-seed noise for the default rule to err at a non-trivial rate, and under which split policy.

#### 0.4b Pilot headroom pre-check (`PILOT`; added 12 Oct, R1-GATE-FIRST)

This answers question 2 before any model is built. It is not evidence; it decides whether building is worth it.
- On the 1–2 noisiest nodes from 0.4, use the L7 branch machinery to collect a small branch table: a few roots, the core actions, a short horizon h.
- Score on it: the hindsight oracle, the noise-aware threshold, the PACE-style gate and, once T2 exists, the C2 index policy.
- Report oracle minus the best simple baseline per node, with cluster-bootstrap intervals, in `docs/r1/reports/HEADROOM_PILOT_<date>.md`.
- **Accept when:** the report exists and its script is committed. A clear shortfall against the practical target goes to 0.6, with the fallback paper (PLAN §3) as the default.

#### 0.5 Aggregate-table review (optional, `PILOT`)

The per-trial ledgers are lost. From the surviving aggregate tables, note only what helps plan the pilot: the invalid and keep rates per campaign and the failure taxonomy. These numbers are context, never results. Skip this step if 0.4 already covers it.

#### 0.6 STOP — decisions (author)

**Inputs:** 0.4, 0.5 if done, and the open-decision table in PLAN §10.

**The author decides:**
- D1–D11, D14, D15, D19 and D20;
- D18, the practical target, stated as a minimum improvement in Y and as a reduction in the false-keep/discard rate at matched compute;
- the Phase 1 headroom criterion.

Record each decision in PLAN §10 with the date.

**Also decide:** D21 (noise nodes) from 0.4; whether the 0.4b pre-check leaves enough headroom to build any model, and if not, the fallback paper (R1-GATE-FIRST); whether the node pool needs the OpenML expansion (D10). If C1's error rates are tiny on every node, R1's premise weakens. The author then decides between continuing, narrowing to the nodes where errors are large, or stopping.

**Phase-0 review:** one fresh-session AI-assisted review of 0.2–0.5 plus one correction round.

---

### Phase 1 — Branch data and the headroom gate (target ~15 Dec 2026)

#### 1.1 Benchmark adapters and instance pool (D20)

Add harness adapters for the D20 benchmarks: MLGym tasks, the existing MLAgentBench adapter, the MLE-bench Lite subset (held out) and the OpenML pool. Each adapter needs a node spec, a seed path, a metric parser and validity rules. Run the 0.4 determinism and σ check on each.

**Accept when:** every adapter passes a smoke campaign and has noise-floor rows. Held-out benchmarks are marked as held out in the registry.

#### 1.2 Restore and branch machinery, with a restore audit

- **Restore.** Restore a campaign at an E1 or E2 state. That covers the editable files, the non-editable node state, the ledger prefix with `current_best` restored explicitly, the seeds, and a pinned manager model.
- **Siblings.** Run every feasible action as a sibling, each followed by ρ for horizon h (D7).
- **Restore audit.**
  - On CPU-deterministic nodes, replaying the original action from the restored state must reproduce the original metric bit-for-bit.
  - Use Paper A's paired-reference route: a fresh reset plus a ledger replay.
  - Record p's provenance as `validated`, `structural` or `sensitivity`. Never call a sensitivity value measured.
- **Accept when:** the audit report shows reproduction rates per node; branch records validate against the adapted `schema.py`; the leak tests pass.

#### 1.3 Pre-declare the headroom criterion, then collect branch data (evidence; authorization required)

- Commit the headroom criterion (from 0.6) and the collection plan before collecting: instances, epochs sampled per campaign, R, h, and compute.
- Collect on development instances only. Held-out benchmarks (D20) are never branched or trained on, and autoresearch is not branched.
- **Accept when:** the authorization note exists; the collection completes or stops under its stated rules; the manifest is committed.

#### 1.4 Baselines and LLM side queries on the branch table

- **Offline scoring.** Every baseline in PLAN §5 that can be scored offline is scored on the full-information table.
- **LLM self-control.** Its side queries are run at the branched states, on forked contexts, and scored against the same leaves.
- **Arms not offline-scorable.** Arms that are not one-step decisions (e.g. stop) are marked deployment-only.

#### 1.5 Headroom gate (STOP)

Compute the hindsight-oracle value minus the best simple baseline (noise-aware threshold, PACE-style gate, the C2 index policy, harness heuristics) per node, with cluster-bootstrap intervals.

- **Gate passes** (criterion from 1.3 met) → Phase 2.
- **Gate fails** → the author chooses one of:
  1. the fallback paper (C1 + C2 theory; PLAN §3);
  2. adding one extension action (scope or fidelity), with its own new pre-declared gate;
  3. stopping.

Also report the LLM self-control's offline value against the oracle and the baselines. This is the first real signal for C3.

**Phase-1 review** at the end, as in Phase 0.

---

### Phase 2 — Configurator (target ~31 Jan 2027)

#### 2.1 STOP — architecture (author, D16)

Reached only if the 1.5 gate passes (R1-GATE-FIRST). L11 is built at this point.

Discuss PLAN §7 with the Phase 1 data in hand: data scale, label noise, latency. Fix:
- the families to train (a is required);
- the model sizes;
- the training stack;
- the compute.

#### 2.2 Train

**Families**
- **(a) Tabular and AWR-MLP:** cross-fitted by instance.
- **(b) Small LM:**
  - SFT on full-information labels;
  - GRPO on counterfactual-table rewards;
  - online RL on CPU nodes only if the ladder test (2.3) says greedy deployment underperforms.
- **(c) Frozen encoder plus heads:** as an ablation.

**Rules**
- Fitting uses development instances only.
- Held-out instances and nodes are never touched.
- Every model is versioned with its training-data manifest hash.

#### 2.3 Offline evaluation and the ladder

On development folds, report:
- Q^ρ prediction quality;
- offline policy value against the oracle;
- the L0 vs greedy-deployment gap on a few CPU instances.

Deployment here is a pilot, not evidence. Decide whether RL is needed (§5.5 of the problem spec).

#### 2.4 Select deployment candidates

Choose at most 2 configurators plus the hybrids, by a rule fixed before 2.3 results exist (e.g. best offline value in family b, with a fallback to a). Record the rule and the choice.

**Phase-2 review** at the end.

---

### Phase 3 — Deployment comparison (target ~28 Feb 2027)

#### 3.1 Pre-declaration

Commit, with a hash, before any outcome exists:
- the primary contrasts: configurator − C2 index policy and H1 − C2 index policy; secondary: configurator vs LLM self-control, including the stronger manager (D22);
- the held-out instances;
- the number of campaigns per instance per arm, from Phase 1–2 variance;
- compute C and the caps;
- the audit seeds;
- the analysis script;
- the decision readings: supported, practically large, equivalent, inconclusive.

#### 3.2 Run (evidence; authorization required)

All arms run on held-out instances and held-out benchmarks at matched compute, with autoresearch on GPU as far as the compute allows. Common audit seeds are used across arms.

#### 3.3 Analysis

- The primary contrasts, read as pre-declared.
- C1's error rates under each arm.
- An action ablation that removes each action in turn.
- The transfer check: held-out node; a second manager model as a descriptive check.
- The ladder.
- Harm events: false keep, false discard, wasted run.

**Phase-3 review** at the end.

---

### Phase 4 — Write-up and submission (target ~31 Mar 2027)

- **Manuscript.** A new manuscript in `papers/r1/`. The template is chosen at this point (R1-FORMAT). The old `papers/paper_b/` stays legacy.
- **Theory.** C2's derivations get proofs, an AI-assisted audit, and the author's own check.
- **Novelty.** Rerun the novelty sweep (PLAN §3) and update the related-work section.
- **Disclosure and anonymity.**
  - Disclose the ETAAI workshop paper on the same harness (non-archival).
  - Prepare an anonymised harness copy for review.
  - Cite Paper A anonymously.
- **Submission.** TMLR submission package, after the PLAN §9 quality-bar checklist passes item by item.

---

## 4. If something fails

| Situation | Response |
|---|---|
| Phase 0 noise floors make default-rule errors negligible on every node | 0.6 STOP: the author decides whether to narrow, add nodes or stop. No result is spun into a premise it does not support. |
| Restore audit cannot reproduce on a node | That node is excluded from branch data, or p is a declared sensitivity value only. It never counts as validated. |
| Headroom gate fails | 1.5 options; the fallback paper is complete on its own. |
| Learned configurator does not beat the C2 index policy, family (a) or the PACE-style gate | Report it. The C3 claim narrows to whatever the data supports. |
| LLM self-control is as good as the configurator | Report it; this is a finding, not a failure. |
| Compute shortfall on GPU nodes | Autoresearch deployment is reduced and labelled. The CPU-node evidence carries the primary claims. |

## 5. Reporting

Each implementation session ends with a STATUS entry:
- the date;
- tasks done, with commits;
- checks, with results;
- what is not done and why;
- decisions needed, phrased as questions for the author.
