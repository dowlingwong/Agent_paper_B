# Build batch 3: implement D24–D28 on the desktop, with an independent review (14 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to the implementation agent on the author's Mac.*

---

You are the implementation agent for Paper B, route R1. The author adopted decisions D24–D28 on 14 October 2026 (PLAN §10). Your job is to implement the **desktop part**: the code, tests, an offline check on committed data, and CPU smoke runs with the scripted proposer. Then have the work reviewed by an independent subagent, do one correction round, and report.

## Scope

**Desktop work, in this batch:**
- harness changes on branch `r1` (D24 summary fixes, D25 active keys, D26 seeded sampling, D27 novelty flags);
- R1 changes (collector manifest fields, scripted stand-in, E1 no-op skip arm, liveness checker and gate);
- an audit of every node for inert keys;
- an offline liveness check on the committed DT4 ledgers;
- liveness smoke runs with the scripted proposer on the Mac CPU.

**Not in this batch (needs the LLM, so Ada; separate prompt later):**
- the LLM liveness check on the five noise nodes;
- the LLM E1b rerun (memory on vs off).

## Read first

- `docs/r1/PLAN.md` §10, the rows **D24–D28** (14 Oct). They are the specification; where this prompt and a row disagree, the row wins.
- `docs/r1/reports/PROPOSER_DECISIONS_20261014.md` (facts 1–6 and the options).
- `docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md`.
- `docs/r1/RUNBOOK.md` §1 (ground rules).
- The harness `CLAUDE.md`.

## Hard rules

1. **No LLM calls, no GPU, no Ada.** Tests use stub LLMs. Live runs are allowed only with the scripted proposer on the Mac CPU, labelled ENGINEERING_ONLY, under `results/r1/engineering/`.
2. **Default paths stay byte-identical.** A node without an active-key declaration, `memory_mode="none"`, the scripted proposer and every existing manifest must produce the same records, events and prompts as before. The only exception is a documented new event type (see H4). Prove it with regression tests.
3. **Implement the rows as written.** If a row cannot be implemented as written, stop on that item, finish the others, and report the options. For example, if the pinned `langchain_ollama` cannot pass a per-call seed. Do not improvise a design choice the author did not make.
4. **No change to node metrics or run behaviour**, no history rewrite, no force-push. Do not touch `results/r1/pilot/`.
5. Every behaviour change has a test that fails before the change and passes after it. Label all work AI-assisted.

## Step 0: commit the pending planning files and record the baseline

Paper repo (`~/Documents/agent_paper_B`):

1. `git pull --ff-only`, then `git status --short`. Expect exactly these entries:
   - ` M docs/r1/PLAN.md`
   - ` M docs/r1/STATUS.md`
   - `?? docs/r1/reports/PROPOSER_DECISIONS_20261014.md`
   - `?? docs/r1/prompts/BUILD_BATCH3_PROMPT.md`
2. Review the diff, then commit with the message "Record author decisions D24–D28 and batch-3 prompt" and push.

Harness (`~/Documents/autoresearch_harness`):

1. `git checkout r1 && git pull --ff-only`.
2. Confirm that HEAD contains `9c4902d`.
3. Record both base commits.

Run the baselines and record their exact numbers. Known environmental failures are acceptable; new ones are not.

- **Harness:** `uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`.
- **Paper:** `make r1-test AR_HARNESS_ROOT=~/Documents/autoresearch_harness` and `make test`.

## Harness tasks (branch `r1`)

### H1 — D24: summary-line fixes (`memory/summarizer.py`)

- `_summary_line` shows the node's `metric_name`. Pass the spec, or the metric name, through `build_memory_context`.
- A metric of exactly 0.0 is shown, not skipped.
- `_best_strategy_line` respects `metric_direction`.
- **Tests:**
  - a minimise node;
  - a node whose first parsed metric is not the target (for example, `train_loss` before `val_score`);
  - a metric equal to 0.0;
  - `none` mode output unchanged.

### H2 — D25: node-declared active keys

- **Declaration.** Add an optional declaration to the node config (`configs/nodes/<node>.yaml`). For the OpenML template it is keyed by `model_type`, with dataset-level exclusions. Declare it for every `openml_*` node. Decide `imputer` per dataset from code or metadata already in the repo; do not download anything.
- **No hash drift.** If you add a field to `NodeSpec`, leave it out of `to_dict()` when it is empty, so that node-spec hashes and research-context hashes of undeclared nodes do not change. Test this.
- **Prompt.** The manager prompt (`ManagerStatus.current_constants` or `_prepare_context`) lists only the active keys when a declaration exists.
- **Validation before any worker run.**
  - A proposal that names an inactive key is rejected before any worker run.
  - Reuse the L6 E1 revise and skip machinery. Allow at most 2 revisions per trial, each charged to the LLM-call cap.
  - If the revisions are exhausted, the trial is `skipped` with reason `inactive_key` and no worker run.
  - Log an event `proposal_rejected_inactive_key`.
  - Put the revision limit in one named constant, and report its value.
- **Active set follows the current config.** When `model_type` changes, the active set changes with it.
- **Tests:**
  - ionosphere under `logistic_regression` shows exactly the declared active keys;
  - under `gradient_boosting` it shows its own keys;
  - an inactive-key edit spends no worker run;
  - an undeclared node's prompt is byte-identical to before.

### H3 — D26: seeded manager sampling

- Derive each call's seed deterministically from (campaign or instance id, trial index, repetition, revision attempt). Pass it to the Ollama call. Keep temperature at 0.2.
- Record `seed` in the `llm_call` event.
- **Tests (stub LLM):** the seed is passed, the seed is logged, and the derivation is stable.

### H4 — D27: novelty flags (record only)

- For every evaluated trial, compute the effective config with `build_effective_config` or its equivalent, and flag:
  - `config_equals_incumbent`;
  - `config_seen_before`;
  - `metric_identical_to_incumbent`.
- **Emit the flags as a separate event (`edit_novelty`)**, not as new fields in `TrialRecord`, so that ledgers stay byte-identical (hard rule 2).
- No decision changes.
- **Tests:** the three flags on constructed sequences, and default records unchanged.

### H5 — push the harness

Make focused commits (one per task where possible) and push branch `r1`.

## Paper tasks (`~/Documents/agent_paper_B`)

### P1 — D24 in the collector (`r1/headroom/e1b_collect.py`)

- `memory_mode` and the seed policy become manifest fields. If the field is absent, the value is `none`.
- Remove the literal `memory_mode="none"`.
- Verify, and test, that `resume_campaign` branch continuations use the same memory mode as their root. Check how the snapshot carries it, and fix this if it does not.

### P2 — D25 in the scripted stand-in

- `r1/headroom/scripted_manager.py` reads the node's declaration instead of `OPENML_ACTIVE`.
- **Golden test:** for the existing seeds (all instances of `E1b_20261012T161034Z`, repetitions 0–2, budget indices 1–20), the proposal sequence must be identical before and after. Generate the golden file **before** you change the code, and commit it with the test.

### P3 — D27 E1 skip arm

- Add a harness-heuristic controller `noop_skip` in `r1/controllers.py` (or `r1/baselines/`). At E1 it skips a proposal whose effective config equals the incumbent's or one already evaluated.
- Unit tests.
- Mark the arm "needs E1 branch data" for offline scoring.

### P4 — D28 liveness checker

- New module `r1/liveness/`:
  - **Input:** campaign ledgers.
  - **Criteria (PLAN D28):** at least one keep after trial 1; at least 50 % of trials with a metric different from the incumbent's; an invalid rate below 30 %.
  - **Output:** JSON and Markdown per node.
  - **CLI:** an `--offline <ledgers>` mode and a `--run` mode.
  - **`--run` mode:** short campaigns, 1–2 instances, W = 10, no branching, with a given manager and memory mode, using the same code path as the collector.
- **Offline acceptance test** on the committed DT4 ledgers (`results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/`):
  - `openml_ionosphere` must **FAIL**;
  - `digits_mlp` must **PASS**.
  - Commit this as a test.
- **Scripted smoke on the Mac CPU:**
  - `--run` with the scripted proposer on the five noise nodes (`digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`);
  - output `results/r1/engineering/liveness_scripted_<UTC>/`;
  - label ENGINEERING_ONLY.

### P5 — D28 gate in the runner

- Add a reusable gate, for example `require_live(nodes, manifest)` in `r1/liveness/`.
- The batch runner library calls it before any LLM-backed collection, and it raises a `STOP:` on failure.
- Wire it into `r1/scripts/deepthought_batch1_resume.py` ahead of collection, so future E1b runs use it.
- Test it with stubbed results.
- Do not create or launch any Ada batch.

### A1 — node audit for inert keys

- For every registered node (`configs/nodes/*.yaml` together with its code), list each editable symbol as active or inert, with file and line, under each relevant configuration.
- Write the results to `docs/r1/reports/NODE_KEY_AUDIT_20261014.md` (ENGINEERING_ONLY).
- Flag every node with inert keys that has no declaration yet. Do not fix those nodes beyond the `openml_*` template unless the fix is the same declaration mechanism. If it is not, list them for the author.

## Independent review (required)

When every task is done and every suite is green, spawn **one subagent with a fresh context**. It must not see your reasoning or your notes. Give it only:

- the PLAN §10 rows D24–D28;
- `PROPOSER_DECISIONS_20261014.md`;
- the diffs `harness <base>..<head>` and `paper <base>..<head>`;
- the test logs (baseline and final);
- the checklist below.

The reviewer **must not edit code**. It writes `docs/r1/reviews/BUILD_REVIEW_20261014.md`. Every finding is MAJOR or MINOR and carries a file:line reference and a concrete failure scenario.

**Reviewer checklist:**

1. Each of D24–D28 is implemented as written, with nothing extra and nothing missing.
2. Default-path byte-identity: undeclared nodes, `memory_mode="none"`, the scripted proposer and old manifests. Are the regression tests real, or could they pass vacuously?
3. Information leaks: the memory summary and prompts expose only the validation metric. Check that no test or audit metric, sibling outcome or future record reaches the manager.
4. D25: no worker run is spent on an inactive key; the revision limit and the LLM-cap accounting are correct; the active set updates after a `model_type` change; node-spec hashes of undeclared nodes are unchanged.
5. D26: seeds are deterministic, are logged, and differ across repetitions and revision attempts.
6. D27: the flags are correct on edge cases (first trial, after a keep, after a restore), and records are unchanged.
7. D24/P1: branch continuations get the same memory mode as their root.
8. P2: the golden file was generated from pre-change code, and it covers OpenML categorical switches.
9. P4: the criteria match D28 exactly; the offline test uses the committed ledgers; ionosphere fails for the right reason.
10. Tests fail before and pass after (spot-check by reverting at least two changes).

Then do **one correction round**. Fix the MAJOR findings, and fix MINOR findings where it is cheap. Re-run all suites. Append a "Resolution" section to the review: each finding marked fixed (with commit) or not fixed (with reason). There is no second review round; anything left open goes to the author.

## Finish

1. Push both repos.
2. Write one STATUS entry (newest first) containing:
   - base and head commits of both repos;
   - test numbers before and after;
   - the liveness results (offline DT4 and scripted smoke);
   - the audit headline;
   - the review summary (counts of MAJOR and MINOR findings, fixed and open);
   - every deviation, and every item stopped under rule 3.
3. Report to the author in a few lines: what was built, what the review found and how it was resolved, what is open, and confirmation that the batch is ready for the Ada step (LLM liveness, then E1b rerun).
