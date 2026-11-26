# R1 build runbook (steps L1–L14)

Companion to [RUNBOOK.md](RUNBOOK.md), §3 "Execution order". This file gives the specification for each local build step. Everything here runs on the Mac and produces `ENGINEERING_ONLY` output: none of it is evidence. Drafted 9 Oct 2026 by an AI agent (Claude) from the harness code at `da8dcbd`. Line numbers refer to that commit; check them before relying on them.

## 0. Conventions for every step

**Repositories**
- **Harness:** `~/Documents/autoresearch_harness`, branch `r1`. This covers all harness changes: hooks, actions, restore, adapters.
- **Paper B:** `~/Documents/agent_paper_B`. A new Python package `r1/` holds the analysis side: branch records, bootstrap, baselines, configurator, LLM side query, end-to-end script.
- R1 code pins the harness commit it runs against. It never imports from the legacy `experiment_scaffold/` at runtime; ported code is copied into `r1/`, and each copied file records its source.

**Default behaviour is sacred.** With the default controller (always `continue`) and no new flags, every existing harness test passes and campaigns produce the same trial records as before. "Same" means all `TrialRecord` fields are equal except `timestamp_*`, `wall_clock_seconds`, provenance IDs and paths under temporary directories. Every step keeps the L5 regression test green.

**Tests and commits**
- New behaviour gets a test that fails before the change and passes after.
- Harness tests use `unittest` style (the repo convention); new `r1/` tests use pytest.
- One commit per logical change. Never force-push or rewrite pushed history.

**Status.** Each step ends with a dated entry in `docs/r1/STATUS.md`: commits, checks, open questions.

**STOP.** Stop and report, instead of guessing, whenever a step needs a decision that is not recorded in PLAN §10.

---

## L1 — Housekeeping

1. **Paper B repo.** Commit the 9 Oct changes as one commit: "Archive old Paper B plans; adopt route R1 canonical plan". The commit contains the move of `docs/paper_split/` → `archive/old_b_2026-10-09/docs_paper_split/`, the new `docs/r1/`, the README banner and this runbook. Push.
2. **Paper A repo.** Its working tree holds a small uncommitted edit to `docs/paper_split/A_REVISION_PLAN_20261005.md`: the B pointer and §8. Leave it for the Paper A session and do not commit it here.
3. **Harness.**
   - `git switch -c r1` from `main` (`da8dcbd`).
   - Environment: `uv sync --extra dev` (`uv.lock` exists; Python ≥ 3.11), or an equivalent venv.
   - Run `pytest -p no:cacheprovider`. Record the pass/fail counts as the baseline. Pre-existing failures are recorded, not fixed.
   - Do not initialise the `harness/claw-code` submodule (D19 default: `LocalWorker`).
4. **Accept when:** both commits exist, and the harness test baseline is in STATUS.

## L2 — Build-time decisions (author)

The author records these in PLAN §10 before L5:

| ID | Default |
|---|---|
| D1 | Budget: compute (worker runs; worker-seconds on mixed nodes) plus an LLM-call cap. The trial-count budget stays available. |
| D3 | Core actions: continue, skip (E1), revise (E1), verify with demote (E2), stop (E0). |
| D4 | The keep rule is overridden only by verify's frozen response. |
| D14 | Repository layout as in §0. |
| D19 | Worker: `LocalWorker`. |
| D20 | Benchmarks: ML-research only (MLGym, MLAgentBench, MLE-bench Lite plus an OpenML pool). |

**Default if the author is unavailable:** the implementation agent stops after L3. L3 does not depend on these decisions.

## L3 — Harness defects (each with a failing-before / passing-after test)

1. **`prompt_manager` makes no LLM call** (`manager/prompt_manager.py`). It wraps the deterministic `select_bounded_objective`. Correct `CLAUDE.md` and the README wording, and add a docstring stating this. Mark it `deterministic=True`; L6 masks revise for deterministic managers.
2. **`ClawWorker` metric sign** (`worker/claw_worker.py` ≈ l. 277). The legacy path writes `1 - val_bpb` under `node_spec.metric_name`. Route it through the node's metric parser, or skip the conversion when `metric_name` is `val_bpb` (minimise). The test uses a fake log with `val_bpb`.
3. **`_current_best`** (`control_plane/campaign.py` l. 1136–1138):
   - Respect `node_spec.metric_direction` (min for `minimize`).
   - Count only records with `decision == KEPT`. Invalid records can carry metrics (≈ l. 1043).
   - Tests: a resume on a minimise node, and a resume where an invalid record has the highest metric.
4. **Seed injection.**
   - The worker passes `AR_TRAIN_SEED` and `AR_SPLIT_SEED` as environment variables to `run_command`. Add them to `LocalWorker._run_command` and to the subprocess environment of every worker that runs nodes.
   - Nodes read them with their current constants as defaults: `lr_synthetic/train.py` (`RANDOM_SEED = 42`) and `openml_*/benchmark.py` (`SEED = 42`, a frozen file, so edit it in the node directory, not through the manager).
   - When the variables are unset, behaviour is identical (regression).
   - Seed variables are never in `editable_symbols`.
   - Tests: the same seed gives the same metric twice on `lr_synthetic`; different seeds give different metrics.

**Accept when:** four tests fail before and pass after, and the full suite is at least at the L1 baseline.

## L4 — Pinned local manager model

1. Install Ollama on the Mac. Choose a model, by default the harness's prior `qwen2.5-coder:7b` or a stronger current local coder model (author's choice, D15). Record the model digest (`ollama show --modelfile` or the API).
2. Smoke tests: `scripts/run_campaign.py --node lr_synthetic --manager langgraph_manager --budget 3 --dry-run --llm-stub`, then real, with `--budget 5` and `LocalWorker`.
3. Record per-call latency, tokens in and out, and parse failures.

**Accept when:** the smoke ledgers and a latency table are in STATUS. This is `PILOT` data, not evidence.

## L5 — Decision hooks and budgets

**Controller interface** (new module `control_plane/controller.py`):

```python
@dataclass(frozen=True)
class ControlView:      # what a controller may see
    epoch: Literal["E0", "E1", "E2"]
    budget_index: int
    ledger_prefix: tuple[TrialRecord, ...]   # records already appended
    current_best: float | None
    incumbent_stack_depth: int
    proposal: ManagerProposal | None         # E1, E2
    provisional: TrialRecord | None          # E2 only (decision not yet committed)
    budget: dict                             # remaining trials / runs / seconds / llm_calls
    node: NodeSpec

@dataclass(frozen=True)
class ControlDecision:
    action: str                 # "continue" | "skip" | "revise" | "verify" | "demote" | "stop"
    scores: dict[str, float]    # one score per feasible action (may be empty for rule-based)
    controller_version: str
    input_hash: str             # sha256 of the canonical ControlView serialisation

class Controller(Protocol):
    def decide(self, view: ControlView, mask: dict[str, bool]) -> ControlDecision: ...
```

`ContinueController` always returns `continue`. It is the default.

**Epochs in `run_real_campaign`** (and in `run_dry_campaign` for tests):
- **E0**: at the top of the loop, before `build_memory_context` (≈ l. 512).
- **E1**: after `_precondition_failure_result(...)` returns `None` and before `worker.run_trial` (≈ l. 585–590).
- **E2**: after `_record_from_worker_result(...)` builds the *provisional* record and before `store.append_many` (≈ l. 620–698).

E2 needs the split between evaluate and commit. The provisional record may be replaced, by L6's verify, before the single immutable append. Nothing may be appended twice, and the pending guard semantics stay unchanged.

**Mask.** Computed before each decision and recorded with it, following the feasibility rules in the problem spec §2.1 (`docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`).

**Events.** A new event type `control_decision` with payload `{epoch, action, scores, mask, controller_version, input_hash}`.
- Emitted for every non-default controller.
- The default `ContinueController` emits nothing unless `log_default_decisions=True`, which keeps the regression exact.
- Event types already in use are untouched.

**Budgets.** A new `ComputeBudget(max_worker_runs, max_worker_seconds, max_llm_calls)` next to the existing `BudgetState`. The campaign ends when any cap is reached. With only `--budget N` given, behaviour is unchanged. Count:
- every worker run, including verify re-runs;
- worker seconds;
- every LLM call: manager proposals, revisions, side queries.

**CLI.** `scripts/run_campaign.py` gains `--controller <module:Class>`, `--max-worker-runs`, `--max-worker-seconds`, `--max-llm-calls`. All are optional.

**Regression test (required).** On `lr_synthetic` with the dry worker, and with `LocalWorker` at fixed seeds, compare records produced with and without the hook code under the default controller. Compare field by field; the exclusions are as in §0.

**Leak test.** The `ControlView` builder must raise if it is given any audit metric, a future record, or a sibling-branch outcome. Test this with deliberately poisoned inputs.

**Accept when:** the regression and leak tests are green, the full suite is at baseline, and the CLI flags are documented.

## L6 — Actions

| Action | Epoch | Behaviour | Ledger / state | Mask |
|---|---|---|---|---|
| `skip` | E1 | The proposal is not executed; the workspace is unchanged. | New `TrialDecision.SKIPPED` and terminal `TrialState.SKIPPED` (transition PROPOSED → SKIPPED). `TrialRecord` validation accepts skipped records with no metric, `execution_status=FAILED`, `validity_status=VALID`, `failure_category=None`, and `extra.control`. The record is appended like any other. Count skipped separately in the reporting, metrics, similarity and summariser modules that enumerate decisions. Under a compute budget, skip uses no worker run. | the proposal passed its precondition |
| `revise` | E1 | Calls the manager once more with structured feedback (`extra.revision_feedback`, e.g. "repeated direction", "step too large"), then proceeds with the revised proposal. | Both proposals are recorded in `extra.control.revision`. Counts one LLM call. | the manager is an LLM manager (not deterministic); no revision yet this trial; LLM cap not reached |
| `verify` | E2 | **Paired fresh-seed re-runs.** Run the candidate at `r` seeds; restore the incumbent's editable files from the snapshot and run them at the same seeds; re-apply the candidate. Verify hashes after each swap. **Frozen response rule:** keep iff the mean paired Δ > 0 in the node's direction. Verify can veto a keep or rescue a discard. | `extra.control.verify = {r, seeds, candidate_metrics, incumbent_metrics, mean_delta, response, original_decision}`. On rescue or keep, `current_best` = the candidate's original single-run metric; the rule is documented and the author may change it. Each re-run consumes worker runs. | trial is valid; seed injection supported; enough compute left for `2r` runs |
| `demote` | E0 | Reverts the last *unverified* keep. Restores the previous incumbent's editable files and its `current_best`. | Incumbent stack: a snapshot of the editable files pushed on every keep. Emits `incumbent_demoted` with both hashes. No trial record is written. | an unverified keep exists on the stack |
| `stop` | E0 | Ends the campaign. | Emits `campaign_stopped_by_controller` with the remaining budget. | `t ≥ t_min` (config; default 3) |

**Tests**
- One test per action, plus the masks.
- A scripted controller that issues each action once across a 6-trial `lr_synthetic` campaign.
- The verify swap leaves the workspace hash equal to the candidate's after the run.
- Skipped records round-trip through `TrialRecord.from_mapping`.

**Accept when:** all action tests pass, the L5 regression still passes, and the full suite is at baseline.

## L7 — Restore and branching at E1 / E2

- **Snapshot.** `CampaignSnapshot` holds:
  - the bytes of the editable files;
  - a declared list of non-editable node-state paths per node (default: `artifacts/`, `results.tsv`, `experiment_memory.jsonl`, `.autoresearch_artifacts/`, `run.log`, plus any cache the node writes);
  - the ledger prefix;
  - an explicit `current_best` and incumbent stack;
  - the budget states;
  - the seed counters;
  - the manager config (model digest, temperature);
  - the controller identity.
- **Restore.** `restore(snapshot, into=<new isolated node directory>)` copies the node into a fresh directory, then continues the campaign from the epoch with a given first action followed by a given policy for horizon `h`. Branches never share writable paths.
- **Restore audit.** On CPU-deterministic nodes, replaying the original action from the restored state must reproduce the original metric bit-for-bit. Write `restore_audit.json` with per-layer hashes and the reproduction result. A mismatch is a finding: report it, never "fix" it by tolerance.
- **Accept when:** the audit passes on `lr_synthetic` and one OpenML node, and sibling branches are isolated (a test that writes in one branch and checks the other).

## L8 — Benchmark adapters (local subset)

1. **OpenML template node.** Parameterise `openml_credit_g` by OpenML dataset ID: spec, `train.py`, metric parser, splits with `AR_SPLIT_SEED`. Add 5 datasets, small binary-classification ones with seconds per run.
2. **MLAgentBench.** Check that the existing `mlagentbench_vectorization` adapter runs with `LocalWorker` and seeds.
3. **MLGym.** Clone `facebookresearch/MLGym`, read its README, and check whether 2–3 light tasks run on the Mac (CPU; is Docker required?). Write an adapter only if feasible; otherwise record the blocker and what is needed (GPU, Docker).
4. Register each node and mark held-out benchmarks as `held_out: true`.

**Accept when:** each adapter has passed a 3-trial smoke campaign, or has a recorded blocker.

## L9 — Branch records and bootstrap (Paper B repo, `r1/`)

- Port from the legacy `experiment_scaffold/src/causal_branch/control/`: `schema.py`, `branch_tree.py` (records, leak-safe projection, integrity status), `evaluate.py` / `bounds.py` (cluster bootstrap with shared draws, Hoeffding radius), and `controllers.py`'s `matching_report`.
- Adapt to **trial-epoch sibling sets.** A record is keyed by instance, campaign, epoch and action, and holds `R` continuations, the outcome `Y` (fresh-seed audit, normalised per node), integrity status and cost.
- The cluster is the instance.
- Tests: the leak tests from the old suite, adapted; a bootstrap on a synthetic table with a known answer.

## L10 — Offline baselines (on a synthetic branch table)

Implement in `r1/baselines/` against the L9 table format:
- ρ;
- fixed schedules;
- random at matched realised budget;
- a noise-aware threshold;
- a **PACE-style anytime-valid commit gate**: read arXiv 2606.08106's method first; if its details are not accessible, implement an e-value / mixture-martingale test on the paired verify differences and label it "PACE-style";
- harness heuristics (repeated-bad, doom-loop skip);
- an **AWR-MLP** (d3rlpy or a small torch implementation);
- a risk-ranked vs advantage-ranked ridge;
- the two-step continuation-value rule, ported from the old `timing.py`;
- a hindsight oracle (headroom only).

Each baseline is scored with one shared spending rule and a matched-budget evaluation.

**Accept when:** all baselines run on the fixture and `matching_report` passes.

## L11 — Configurator scaffold (Paper B repo, `r1/configurator/`)

- **Serialiser:** a compact text view of at most 512 tokens (proposal summary and rationale, short ledger narrative, epoch) plus a numeric feature vector (Δ/σ̂, remaining budget, failure counts, verify history, index). It obeys the allowlist and the no-future rule. Ported from the old `configurator/serialiser.py` rules.
- **Models:**
  - (i) `answerdotai/ModernBERT-large` with our late-fusion head (pooled text plus numeric MLP → masked action logits plus per-action scores);
  - (ii) the Laya checkpoint (`convaiinnovations/laya`) with the same late-fusion adapter;
  - (iii) a Kev-0.8B wrapper using its `choice` API;
  - a stub model for tests.
- **Training:**
  1. supervised cross-entropy plus Brier on full-information labels;
  2. REINFORCE with a group-mean baseline, reward = normalised table value of the sampled action + β·(1 − Brier), a bounded proper score (RLCR, arXiv 2507.16806; never call it "RLCD");
  3. temperature recalibration.
- **Hardware:** Mac MPS, falling back to CPU.
- **Accept when:** each model trains for a few steps on the fixture, inference latency is under about 1 s per decision, and the output matches the L5 `ControlDecision`.

## L12 — LLM self-control side query

`r1/llm_control.py` sends the manager model a side query on a **forked** context: the manager's own prompt plus the proposal or result plus the masked action menu plus the remaining budget. The model returns JSON `{action, scores}`.

- The query is never appended to the manager context.
- Its tokens count against the LLM cap.
- A parse failure falls back to `continue` and is logged.

**Tests:** the manager context is byte-identical before and after a side query (stub LLM); a malformed reply is handled.

## L13 — End-to-end dry run on `lr_synthetic`

A single command (`make r1-e2e` in the Paper B repo) runs:
1. a short campaign with hooks;
2. branches at sampled epochs;
3. the table;
4. a tiny configurator (stub or ModernBERT for 2 steps);
5. a short deployment with the learned controller;
6. the analysis script with bootstrap output.

Output goes to `results/r1/engineering/<UTC>/` with an `ENGINEERING_ONLY` banner.

**Accept when:** the command reproduces the run from a clean checkout.

## L14 — Build review

One fresh-session AI-assisted review of L3–L13. It checks:
- the default-behaviour regression;
- leak tests;
- no double appends;
- action semantics against this runbook;
- restore-audit honesty;
- that `ENGINEERING_ONLY` labels are present.

Then one correction round. The review goes to `docs/r1/reviews/BUILD_REVIEW_<date>.md`.
