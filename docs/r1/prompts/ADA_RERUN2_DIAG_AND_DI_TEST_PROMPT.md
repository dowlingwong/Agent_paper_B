# Prompt: rerun-2 stop diagnosis on Ada, `digits_mlp` liveness diagnosis, and the C4 DI test on existing E1b data

*Written 18 Oct 2026 by the coordinating session (Claude) at the author's request. Give this whole file to the operator agent that has SSH access to Ada (`ucrtasl`).*

---

You are an operator agent working for Dowling Wong (the author) on Paper B, route R1, repository `github.com/dowlingwong/Agent_paper_B`. Read `docs/r1/PLAN.md` §10 (rows dated 18 Oct 2026), `docs/r1/C3_DESIGN.md` §7 and `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` §6 before you start. They define why these tasks exist.

## Ground rules (all tasks)

- **Read-only on every existing batch directory, log and result.** Never modify, move, resume or re-run anything under `/data1/dowling/tmp/`. Never retry an interrupted phase.
- **No LLM calls, no Ollama server, no GPU use, no worker runs.** All three tasks are pure analysis of files that already exist.
- Never touch other users' processes or files.
- Labels: everything you produce is `ENGINEERING_ONLY` (Tasks 1 and 2) or `PILOT` (Task 3). None of it is evidence. Say "AI-assisted" and name yourself in every report.
- **Work in a fresh clone.** Create a new scratch directory `/data1/dowling/tmp/r1_diag_ENGINEERING_ONLY_<UTC timestamp>/` and clone `Agent_paper_B` there, at `main` (it must contain commit `b64229d` or later). Set a repository-local git identity: `git config user.name "Dowling Wong"` and `git config user.email "wangdowling@gmail.com"`. Add your own `Co-Authored-By:` trailer to every commit.
- Python ≥ 3.10 with `numpy` (and `scipy` if you need it) is enough. You do **not** need the harness checkout or the harness venv.
- **STOP and report, rather than improvise**, if: a path below does not exist; the data contradict the descriptions here; or a task would need anything forbidden above.

## Task 1 — why did R1-E1B-RERUN2 stop? (read-only, ENGINEERING_ONLY)

**Context.** STATUS (14 Oct, top entries) records that the rerun-2 batch passed preconditions and LLM liveness, started arm A at `20261014T141051Z`, and then stopped with `RuntimeError: STOP: collection failures; no leaf retries permitted`.
- Batch: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/`
- Runner: `r1/scripts/ada_e1b_rerun2.py`; launcher: `r1/scripts/ada_e1b_rerun2_launch.sh`
- Paper commit `b2e5cc3`; harness `411c6054c8505f93a6429e2f9eed526952793882`

**Do:**
1. List the batch directory tree (depth ≤ 4) and identify the logs, runtime state, `gpu_census.jsonl`, and arm-A outputs.
2. Find every failed leaf or campaign of arm A. For each one, record:
   - the node, instance, branch point, action and repetition;
   - the failure category and the exact error text or traceback (from collection checks, worker `run.log`, `patch.diff`, ledger `failure_category` / `worker_failure_message`, and the runner log);
   - the time of failure.
3. Classify the root cause into one of:
   - (a) harness or runner defect;
   - (b) worker environment (missing package, path, permissions, disk);
   - (c) manager/LLM (parse failure, D25 inactive-key rejection loop, timeout);
   - (d) resource (OOM, GPU memory fell below the co-tenancy threshold, Ollama CPU fallback);
   - (e) other.

   Give the evidence for the classification. If more than one cause, rank them.
4. State whether the cause would also hit the **C3 label sweep** that replaces rerun-2 (PLAN §10, "R1-E1B-RERUN2 (revision)"): root campaigns only, no branching, memory `append_only_summary` and `none`, `"vary"` split, W = 20. Root campaigns only matter here: if the failure is in branch collection, say so explicitly.
5. Propose the minimal fix and a test that would have caught it **before** Ada. The test should be a desktop dry-run fixture like `r1/scripts/rerun2_dryrun.py`, or a unit test. Do not implement the fix.

**Output:** `docs/r1/reports/RERUN2_STOP_DIAGNOSIS_<YYYYMMDD>.md`. Quote paths and exact error lines. Every claim must cite the file it comes from.

## Task 2 — why did `digits_mlp` fail D28 liveness with memory on? (read-only, ENGINEERING_ONLY)

**Context.** `results/r1/engineering/liveness_llm_20261014T140742Z/` (committed in the repo): `digits_mlp` had 0 keeps after trial 1 (criterion 1 failed), novelty 0.60, invalid rate 0.

**Do.** From `ledgers/digits_mlp__*/root_trials.jsonl` and `root_events.jsonl`, tabulate per trial:
- the structured edit (symbol, old → new);
- the parsed `val_score`, the incumbent's value and Δ̂;
- the decision;
- the memory-summary text shown to the manager (`memory_context_built` events).

Then answer:
- Are the proposals plausible but all slightly worse, or degenerate (repeats, inert keys, directions that always hurt)?
- Is the trial-1 incumbent unusually high (a lucky first draw), as T4 Proposition 9 would predict?
- Does the memory summary steer the manager toward the same edits?

Compare with the DT4 memory-off root campaigns on `digits_mlp` (`results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__*`), which did keep after trial 1. Recommend one of: keep the node; keep it with a change (state the change); or exclude it.

**Output:** a section "digits_mlp liveness" in the same report file as Task 1.

## Task 3 — C4 DI test on the existing E1b branch data (PILOT; no GPU; can start immediately)

**Question.** T4 Proposition 10 calls the proposer *decision-independent* (DI) if the law of future proposals does not depend on the keep/discard decision, given the history. Under DI, trial-by-trial acceptance is optimal; without it, a learned policy (online RL, arm A7) can beat it. We test DI on decisions that the control plane **forced** to differ at **identical histories**.

**Data (committed in the repo).**
- **LLM run** `results/r1/pilot/E1b_20261013T151857Z/`:
  - pinned `qwen2.5-coder:7b`, temperature 0.2, no sampling seed (decoding is not deterministic), **memory mode `none`**;
  - nodes `digits_mlp` and `openml_ionosphere`, 6 instances each, E2 points at budget index 4, 8 and 12 (`points.json`: 36 points);
  - at each point, branches `continue` and `verify` (r = 2, frozen response "D̄ > 0", which can demote a keep), each with repetitions `r1` and `r2` (`leaves/`: 144 files);
  - per-branch ledgers: `provenance/ledgers/branches/<instance>__b<point>__<action>__<rep>/branch_trials.jsonl` and `branch_events.jsonl`; roots under `provenance/ledgers/roots/`.
- **Scripted run** `results/r1/pilot/E1b_20261012T161034Z/`: same design with the seeded scripted proposer. Use it as the **calibration control**. Its proposal law depends on the history only through the incumbent configuration, so DI with respect to value-relevant quantities should hold up to that.

**Design.**
1. **Where did the decision actually differ?** For each point and repetition, determine whether the verify branch changed the decision on the point's trial relative to the continue branch. Verify can only demote a keep, so a change happens only where the trial at the point was kept and verify rejected it. Read this from the branch trial/event records (the decision on the trial at `budget_index` = point, and any verify/demote events). Report the number of changed and unchanged point-repetitions per node.
2. **Contrasts on the proposals after the point** (the trials with budget index > point, within each branch):
   - **D_changed:** continue-rX vs verify-rX at points where the decision changed.
   - **D_null (nondeterminism baseline):** continue-r1 vs continue-r2 and verify-r1 vs verify-r2 at the same points. Same decision, different decoding draws.
   - **D_unchanged:** continue-rX vs verify-rX at points where the decision did not change.

   DI is violated in the data if D_changed exceeds D_null **and** D_unchanged.
3. **Outcome measures**, for the next k = 1, the next k = 3, and all remaining trials:
   - **value-relevant (primary):** mean Δ̂ of the subsequent trials relative to their own incumbent, and the fraction with Δ̂ > 0, i.e. the quality of the future proposal law;
   - **mechanism (secondary):** total-variation distance between edited-key distributions; signed log edit size; fraction of active-key-novel configurations (replay structured edits from the snapshot configuration, as in D28's legacy replay); duplicate fraction; fraction of metric-identical trials.
4. **Inference.** Pair contrasts by point. Use a permutation test that shuffles the changed/unchanged labels across points within a node, and a cluster bootstrap by instance for intervals. Report effect sizes in metric units and relative to σ_d. Report per node and pooled.
5. **Caveats to state explicitly:**
   - **`openml_ionosphere` LLM data are degenerate.** 100 % of trials are metric-identical, because the edits touched keys that logistic regression ignores (`docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md`). Report it separately, and exclude it from the pooled value-relevant result.
   - **Memory mode `none`.** These data test DI only for the memory-off proposer, which reads little of the ledger. The primary C3 proposer (memory `append_only_summary`) has **no branch data yet**. State this as the main limitation and specify the smallest memory-on branch run that would answer it: nodes, points, repetitions and expected number of changed points. Do not run it.
   - Few changed points; single-campaign Δ̂ (no audits).

**Implementation.**
- Add `r1/diagnostics/di_test.py` with a CLI: `python -m r1.diagnostics.di_test <run dir> --md <report tables file> --json <out>`. It must be deterministic (fixed bootstrap seed), read only committed files, and regenerate every number in the report.
- Add `r1/tests/test_di_test.py` with a small synthetic fixture: one case where DI holds by construction (the test must not reject) and one where the post-decision proposal law shifts (the test must detect it).
- Run the new test file with pytest. Run the full `r1/tests` only if the harness is available in your clone's environment; otherwise state that it was not run.

**Output:**
- `docs/r1/reports/DI_TEST_E1B_<YYYYMMDD>.md`: question, data, design, results tables, caveats, and a one-paragraph verdict for the C4 / A7 decision (DI approximately holds / violated / undetermined at this sample size). Include the proposed memory-on follow-up.
- Tables file: `docs/r1/reports/DI_TEST_E1B_<YYYYMMDD>_tables.md`.

## Finish

1. In your clone, add a dated entry at the top of `docs/r1/STATUS.md` ("AI-assisted …; ENGINEERING_ONLY / PILOT; not evidence") summarising Tasks 1–3, with paths and the verdicts.
2. Commit only the new or changed files of this prompt: the two reports, the tables, the script, the test and STATUS. Run `git diff --cached --check` first. Push to `origin main`. If the push is rejected as non-fast-forward, `git pull --rebase` once; if that conflicts, STOP and report.
3. Reply to the author with:
   - the root cause of the rerun-2 stop, in one line, and whether it affects the C3 label sweep;
   - the `digits_mlp` recommendation;
   - the DI verdict, with the key numbers;
   - the commit hash.
