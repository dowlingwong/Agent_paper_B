# Build batch 4: F3 fix, D28 revision, and the E1b rerun-2 entrypoints (desktop, 14 Oct 2026)

*Written by Claude (coordinating session) at the author's request. Hand this whole file to the implementation agent on the author's Mac.*

---

You are the implementation agent for Paper B, route R1. Implement three PLAN §10 rows from 14 October:

- **D27 (F3 fix)**;
- **D28 (revised criterion 2)**;
- **R1-E1B-RERUN2**: build and test its entrypoints, but do not run them.

Then have the work reviewed by an independent subagent, do one correction round, and report. The Ada execution follows in a separate prompt (`ADA_E1B_RERUN2_PROMPT.md`), which uses exactly the entrypoints you build here.

## Read first

- PLAN §10: the rows of 14 Oct, both tables (D24–D28; D27 (F3 fix), D28 (revised criterion 2), R1-E1B-RERUN2). The rows are the specification; where this prompt and a row disagree, the row wins.
- `docs/r1/reviews/BUILD_REVIEW_20261014.md`, especially F3, F5 and the Resolution section.
- `docs/r1/prompts/BUILD_BATCH3_PROMPT.md` (the batch-3 rules carry over).
- `docs/r1/prompts/ADA_DT4_RERUN_PROMPT.md`, `r1/scripts/ada_rerun_dt4.py` and `r1/scripts/deepthought_batch1_resume.py` (the runner pattern to reuse).
- The DT4 lesson: the runner stopped because a generated Markdown file failed `git diff --check`. **Every path that commits generated files must be tested end-to-end in a temporary git repository.**

## Hard rules

These carry over from batch 3: no LLM calls, no GPU, no Ada. Default paths stay byte-identical. Implement the rows as written, or stop on that item and report. Every behaviour change gets a fail-before/pass-after test. No history rewrite. Do not touch `results/r1/pilot/`. Label the work AI-assisted.

## Step 0: commit and baseline

1. Paper repo: `git pull --ff-only`. `git status --short` must show exactly:
   - ` M docs/r1/PLAN.md`
   - ` M docs/r1/STATUS.md`
   - `?? docs/r1/prompts/BUILD_BATCH4_PROMPT.md`
   - `?? docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`
2. Review the diff, commit it as "Record 14 Oct decisions after batch-3 review; batch-4 and Ada rerun-2 prompts", and push.
3. Harness: `git checkout r1 && git pull --ff-only`. HEAD must be `0f2d9e9` or a descendant of it.
4. Record both base commits and the baseline test numbers: harness suite, `make r1-test` (absolute `AR_HARNESS_ROOT`, venv interpreter) and `make test`.

## H6: D27 F3 fix (harness, branch `r1`)

- The `edit_novelty` event payload gains:
  - `effective_config_sha256`;
  - `active_config_sha256`, the projection on the node's active keys for the current configuration (on undeclared nodes it equals the full configuration);
  - `active_config_equals_incumbent`;
  - `active_config_seen_before`.
- The existing three flags keep their meaning, but `config_seen_before` now also covers configurations evaluated before a resume.
- The E2 snapshot stores the seen-hash sets (full and active) at capture time, and `resume_campaign` seeds both sets from them.
- A snapshot without these sets (older format) resumes with `seen_before_resume: "unknown"`, recorded in the first `edit_novelty` event after the resume. Never treat it silently as an empty set.
- **`TrialRecord` bytes do not change.** Prove it with the existing record test.
- **Tests:**
  - the reviewer's F3 reproduction (`lr_synthetic`: evaluate `LEARNING_RATE=0.002`, resume, propose it again) now yields `config_seen_before=True`, and fails on `0f2d9e9`;
  - active vs full hashes on a declared node: an inert-key change gives the same active hash and a different full hash;
  - an old-format snapshot gives `"unknown"`;
  - default records are unchanged.
- Push `r1`.

## P6: D28 revised criterion 2 (paper, `r1/liveness/`)

- Criterion 2 becomes **active-key novelty**: at least 50 % of evaluated trials must have `active_config_equals_incumbent=False` and `active_config_seen_before=False`.
  - "Evaluated" means a worker run happened. Skipped trials, including `inactive_key` skips, are not evaluated.
  - Report the inactive-key rejections as a separate count.
- Criteria 1 and 3 are unchanged. Keep one constant per threshold.
- **Legacy ledgers** (no `edit_novelty` events, e.g. DT4): reconstruct the active-key configuration of each trial by replaying the recorded `structured_edit` from the start configuration, applying keeps and restores, and projecting with the node's current declaration. The report states `novelty_source: events | replayed`.
- **Offline acceptance on the committed DT4 ledgers:**
  - `openml_ionosphere` must FAIL on criteria 1 and 2;
  - for `digits_mlp`, report the computed verdict and the three numbers, and pin them in the test after an **independent recomputation** (a second, simple script or notebook cell). Do not force a PASS: DT4 ran with memory off, so a novelty FAIL there may be correct.
- **Gate:** the gate consumes only LLM-backed (`manager_kind: langgraph`), memory-on liveness manifests. A collection whose manifest says `memory_mode: none` and `arm_role: contrast` is exempt and reuses the memory-on verdict for node eligibility (PLAN D28). Test both cases.
- **Scripted smoke (Mac CPU, ENGINEERING_ONLY):** rerun `--run` with the scripted proposer on the five noise nodes on the new code, into `results/r1/engineering/liveness_scripted_<UTC>/`, with ledgers force-added as in batch 3. Report the `openml_wdbc` verdict under the new criterion.

## P7: R1-E1B-RERUN2 entrypoints (paper; build and test, do not run)

### `r1/scripts/ada_e1b_rerun2.py` (Ada-only)

**Reuse.** Reuse the helpers in `deepthought_batch1_resume.py` (pin, co-tenancy card selection, `check_gpu`, `assert_full_offload`, commit with whitespace check, push verification), loaded the way `ada_rerun_dt4.py` loads them. Generalise `finish()` so its STATUS title and labels name this batch, not "Remote batch 1".

**Phases.** Each phase is checkpointed in `batch_state.json`. A completed phase is never redone. An interrupted phase is a STOP for the author, never retried automatically.

1. **Preconditions:**
   - the PLAN rows `R1-E1B-RERUN2`, `D28 (revised criterion 2)` and `R1-COMPUTE (GPU co-tenancy, 13 Oct)` are present;
   - the paper and harness checkouts are at their origin heads, and the harness head is recorded;
   - the model digest is pinned;
   - a GPU card is chosen under co-tenancy;
   - Ollama runs with `OLLAMA_KEEP_ALIVE=-1`;
   - the model is fully offloaded (`size_vram = size`), with telemetry saved.
2. **LLM liveness** (memory on, seeded): the four rerun nodes, 2 instances, W = 10. Commit the manifest and reports under `results/r1/engineering/liveness_llm_<UTC>/`. Eligible nodes are those that pass; STOP if fewer than 2 pass.
3. **Arm A**: LLM, `append_only_summary`, on the eligible nodes, through the gate.
4. **Arm B**: LLM, `none`, on the same eligible nodes, gate-exempt as a declared contrast.
5. **Arm C**: scripted stand-in on the same eligible nodes (CPU; no gate).
6. For each arm:
   - collection checks: 0 collection failures; for A and B, parse failures ≤ 20 %;
   - `e1b_analyze` (tables via `--md`);
   - commit the results directory and the tables;
   - the committed-data regeneration check (sha256 of `analysis.json`).
7. **Comparison:** `r1/headroom/e1b_compare.py` over the three committed runs (below); commit its report.
8. **`finish`:** a STATUS entry; push.

**Design constants** come from the PLAN row: 18 instances, W = 20, points 4/8/12, r = 2, 2 repetitions, audit seeds 5001–5006, `"fixed"` split. Write them into each run's manifest, together with `arm` (`A`/`B`/`C`), `arm_role` (`primary`/`contrast`/`reference`) and `memory_mode`.

**Card.** One card and one Ollama instance; workers as in DT4 (4).

**Runtime.** Before running, print the compute estimate: number of leaves and expected LLM calls per arm.

### `r1/scripts/ada_e1b_rerun2_launch.sh`

It runs on Ada and must:

- create a new batch directory under `/data1/dowling/tmp/`;
- fresh-clone the paper repo at `origin/main`;
- fresh-clone the harness at the head pinned in `r1/scripts/HARNESS_PIN_RERUN2`, a file you create containing the batch-4 harness head, then `uv sync`;
- reuse the pinned model files at `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/ollama_models` and `/usr/local/bin/ollama`;
- write `env.sh`, setting `R1_EXECUTOR` / `R1_COAUTHOR` for the launching agent;
- start tmux `r1_e1b_rerun2`.

It must refuse to start if that tmux session or an `r1_ollama_*` session of ours already exists.

It has two modes:

- **`--prepare`** creates the batch directory, both clones and the venv, then runs the harness suite and `make r1-test` there. It writes `prepare.json` with the heads and test numbers, and starts nothing.
- **`--start <batch dir>`** refuses unless `prepare.json` exists and shows no test failure outside the accepted environmental set. That set is the known harness failures plus the author-approved Ada missing-`/bin/zsh` exception (PLAN §10, 12 Oct). Only then does it start tmux.

### `r1/headroom/e1b_compare.py`

Inputs: the three run directories. Output: a Markdown report and JSON with the following, per node and for ALL.

- **Per arm:**
  - ρ;
  - `always_verify − ρ`, `kg_index − ρ` and `margin_threshold − ρ`, with instance-cluster bootstrap CIs;
  - best simple baseline;
  - naive and leaf-split headroom with CIs;
  - share of points where verify changes the leaf;
  - mean verify − continue.
- **Memory effect:** `(always_verify − ρ)_B − (always_verify − ρ)_A`, as a paired instance-cluster bootstrap with shared draws, the same instances in both arms.
- **Waste (C1):**
  - active-novelty fraction;
  - inactive-key rejections;
  - `config_seen_before` rate;
  - LLM calls and parse failures per arm.
- **Labels:** the report is labelled PILOT and carries no interpretation beyond a fixed "readings" template:
  - supported if the adjusted lower bound is > 0;
  - inconclusive if the interval spans 0;
  - opposite if the adjusted upper bound is < 0.
  - Bonferroni over the per-node primary contrasts, with the count stated.

### Tests (stubs; no LLM, no GPU)

- phase order and checkpointing, including that a completed phase is skipped on restart;
- an interrupted phase gives a STOP;
- the eligible-node filter, and a STOP with fewer than 2 nodes;
- the arm-B gate exemption, and arm A gated;
- manifest fields;
- the launcher's refusal conditions (shell test with stubs);
- `e1b_compare` on real committed fixtures: DT4 (`E1b_20261013T151857Z`, LLM memory off) as "B" against scripted `E1b_20261012T161034Z` as "C" on their two shared nodes, with the paired-bootstrap path exercised;
- **an end-to-end commit test:** generate every Markdown and JSON the runner commits, from the fixtures, into a temporary git repo, and run the runner's own `commit()` including `git diff --cached --check`.

## Independent review (required)

When everything is green, spawn **one fresh-context subagent**. It must not see your reasoning or notes. Give it only:

- the PLAN rows of 14 Oct;
- review F3 and F5 from `BUILD_REVIEW_20261014.md`;
- both diffs (`base..head`);
- the test logs;
- this checklist.

It writes `docs/r1/reviews/BUILD_REVIEW_20261014b.md`, edits no code, and rates each finding MAJOR or MINOR with a file:line reference and a failure scenario.

**Checklist:**

1. Each row is implemented as written.
2. `TrialRecord` bytes are unchanged, and the default paths are byte-identical.
3. The F3 reproduction is fixed. Old snapshots give `"unknown"`, never a silent empty set.
4. Active vs full hashing is correct when `model_type` changes mid-campaign.
5. The novelty denominator excludes skipped trials. The legacy replay reproduces an independent recomputation on the DT4 ledgers.
6. The gate accepts only LLM memory-on manifests. The arm-B exemption cannot be used to bypass the gate for arm A, for example by mislabelling the manifest.
7. The runner never retries an interrupted phase, never re-runs a completed one, and all its commits pass the whitespace check (end-to-end test present and non-vacuous).
8. `e1b_compare`: the paired bootstrap shares draws across arms by instance, the Bonferroni count is stated, and there is no interpretation beyond the template.
9. The launcher pins the harness head and cannot start twice.
10. Fail-before/pass-after spot checks on at least two changes.

Then do **one correction round**: fix the MAJOR findings, and fix MINOR findings where it is cheap. Re-run the suites and append a "Resolution" section to the review.

## Finish

1. Push both repos.
2. Write one STATUS entry with:
   - commits;
   - test numbers before and after;
   - the offline DT4 liveness verdicts under the new criterion;
   - the scripted smoke verdicts, including `openml_wdbc`;
   - the compute estimate for the rerun;
   - the review summary;
   - deviations and open items.
3. Report to the author in a few lines. Include the `HARNESS_PIN_RERUN2` value and confirm that the Ada prompt can be handed over.
