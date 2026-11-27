# Paper C — build runbook, phases P0–P10 (15 Nov 2026)

**AI-assisted (Claude, chat session).** Executes `BUILD_LIST.md`. Read with the plan (`proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`, rev 2) and its addendum (`PLAN_ADDENDUM_20261115.md`). Label for everything produced: **ENGINEERING_ONLY**. Nothing here is evidence.

**Executor.** The chat-session Claude (author, 15 Nov), working in its cloud clone of the repository and pushing new branches only. Mac files are read through the device shell, read-only. **Reviewer.** A freshly spawned independent agent per phase. It has not written the code under review.

**Tonight:** P0–P2, then PH (headroom census) if time allows. Order after that: P3 → P4 → P5 … P10.

---

## 0. Rules for every phase

### 0.1 Scope (addendum §C)

Paper C does not wait for Paper B's submission. Real-node phases are not part of this build runbook: each gets its own runbook, review and authorization. This build runbook is CPU-only:

- **Allowed:** files under `paperC/`, run on the Mac CPU.
- **Not allowed:**
  - SSH to any host;
  - GPU use;
  - proposer (LLM) calls;
  - worker runs on real nodes;
  - edits outside `paperC/`.
- **Read-only access to the rest of the repository is allowed**, including `git show <pin>:<path>` of other branches. Any code taken from another branch is **ported, not imported**, with its source path and pin recorded in the module docstring.

### 0.2 Branch and checkout

- Work on branch `paperc-build-20261115`, created from `paperc-scaffold-20261115`, in the executor's own checkout (the chat session's cloud clone). The Mac main checkout (currently on `exam-x-20261026`) and the other agents' worktrees are not touched.
- One commit per phase step, plus one commit per review round.
- Commit messages start with `paperC:`.

### 0.3 Environment

- Python ≥ 3.11 in `paperC/.venv`, which is git-ignored.
- Packages:
  - P0–P6: `numpy`, `scipy`, `pytest`;
  - from P7: `lightgbm`, `scikit-learn`;
  - from P8: `torch` (CPU wheel).
- Record `pip freeze` to `paperC/env/pip_freeze_<phase>.txt` whenever the package set changes.

### 0.4 Test command

```
PYTHONPATH=paperC/src paperC/.venv/bin/python -m pytest -q -p no:cacheprovider paperC/tests
```

`r1/tests` must stay untouched. Run it only if a phase touches shared files, which it should not.

### 0.5 Determinism

- Every stochastic function takes an explicit seed or `numpy.random.Generator`.
- Tests fix seeds.
- No wall-clock or host-dependent values in outputs.

### 0.6 Review loop

1. The executor finishes a phase and writes its line in `paperC/docs/BUILD_STATUS.md`: phase, commit, test count, open points.
2. The reviewer reads:
   - the diff;
   - the relevant plan and addendum sections;
   - this runbook's "Done when".
3. The reviewer runs the tests and writes `paperC/docs/reviews/BUILD_P<n>_REVIEW_20261115.md`, ending with the verdict **ACCEPT** or **NOT ACCEPTED** and numbered findings (BLOCKING / MAJOR / MINOR).
4. The executor fixes the findings and the reviewer re-checks. After 3 rounds without ACCEPT: STOP.

### 0.7 Delivery

- Push the branch (new branches only; the author allowed this on 15 Nov).
- If a push is not possible, write a git bundle and `READY.txt` (branch, head SHA, base SHA, review file) under `Claude outputs/`.

### 0.8 STOP — write `paperC/docs/STOP_<phase>_<date>.md` and wait for the author

Stop when any of these happens:
- a step needs anything excluded by §0.1;
- the plan and the Track S code disagree on a definition (world law, seed block, schema field) and the choice changes results;
- a Paper C seed block overlaps a Paper B block, or a Paper B block cannot be bounded from code;
- an E-SYN oracle check fails (for example, the null world shows a non-zero DP gain beyond tolerance);
- 3 review rounds pass without ACCEPT.

---

## P0 — Setup (≈ 20 min)

1. Fetch `origin/paperc-scaffold-20261115` and create `paperc-build-20261115` from it.
2. (Mac-local executors only: do this in a worktree under `.claude-worktrees/`.)
3. Create `paperC/.venv`, install the P0 packages and record `pip freeze`.
4. Run the test command (§0.4). The scaffold smoke test must pass.
5. Create `paperC/docs/BUILD_STATUS.md` with a header and the P0 line.

**Done when:** the smoke test passes in the worktree, and `git status` shows changes only under `paperC/`. No review is needed for P0.

---

## P1 — Transition schema and mechanical checks (B1; plan §4.1–§4.2) (≈ 1.5–2 h)

**Module:** `paperC/src/paperc/schema.py`, schema id `spt_transition/v1`.

1. **Read first:**
   - plan §4.1, the field table;
   - Track S `r1/tracks/schema.py` at `trackS-ops-20261030` (`fab88fc`): `Provenance`, `RootRecord`, `LeafRecord`, `STATE_FEATURES`.

   Reuse Track S field names wherever they mean the same thing.
2. **Dataclasses**, one per plan §4.1 group: `Identity`, `EnvContext`, `PolicyInfo` (including `action_prob`, `eps`, `eps_seed`, `continuation_policy_id`), `ForkDesign` (`selection_rule`, `p_select`, `channel_arms`, `replicate`), `Seeds`, `State`, `Action`, `Outcome`, `EpisodeEnd`, `Terminal`, `Provenance`, and the row type `Transition`.
   - Required vs optional fields follow plan §4.1.
   - `divergent` is an outcome, never a truncation.
   - `eligible` vs `rule_forced` is a state flag.
3. **Validation and export:**
   - `to_json_schema()` writes `paperC/schemas/spt_transition_v1.json`;
   - `validate(row) -> list[str]` returns field-level errors.
4. **Campaign checks:** `check_campaign(rows, *, registry=None, behaviour=None) -> list[Violation]`, one check per plan §4.2 bullet:
   - budget conservation for runs and calls;
   - contiguous `step_index`;
   - exactly one terminal row per complete campaign, none for a truncated one;
   - next-state incumbent hash = keep outcome;
   - propensity replay (if a `behaviour` callable is given, it must reproduce action and probability);
   - design weights recomputable from `ForkDesign`;
   - no future-step field and no audit value inside `State` (a declared denylist of names plus a test that `State` has no such field);
   - seed keys not in the registry's Paper B blocks (only when a registry is passed; P2 provides it).
5. **Tests** in `paperC/tests/test_schema.py`:
   - a small generator of valid synthetic campaigns (in the test file, not in `src/`);
   - a valid campaign gives no violation;
   - **each check has one corruption that only it catches** (8+ tests);
   - the JSON schema validates a valid row and rejects a row with a missing required field.

**Done when:** tests pass, the JSON schema is committed, and the reviewer ACCEPTs. Every plan §4.1 field is either present or listed in the docstring as deliberately deferred, with the reason.

---

## P2 — Seed registry generated from code (B2; plan §11.1) (≈ 1–1.5 h)

**Module:** `paperC/src/paperc/seeds.py`. **Output:** `paperC/seeds/registry_v1.json`.

1. Declare a source table in the module: (branch, pin, path, symbol or function, how to bound it). Minimum sources:
   - Track S `r1/tracks/collect.py` at `fab88fc`: instance blocks, audit bases, `SELECTION_SEED`, `REP_BASE`;
   - `r1/headroom/e1b_collect.py` `_instance_seed`;
   - audit 7001–7010, G.1b 8001–8010 and exam 9001+/9101+/9201+, from the code that defines them in the canonical line.
2. **Extract values with `ast`** from `git show <pin>:<path>`. Do not import the modules.
   - A seed derived by a formula (for example a hash of node and index) is bounded by enumerating its declared domain.
   - If the domain cannot be bounded: STOP (§0.8).
3. **Reserve Paper C blocks** in a range disjoint from every Paper B block, with a margin, and write them to the registry. The chosen ranges go into `BUILD_STATUS.md` as a proposal for the author.
4. **Prose check:** compare the registry with plan §11.1 and list every difference in `paperC/docs/reports/SEED_REGISTRY_CHECK_20261115.md`.
5. **Tests:**
   - generation is reproducible (same JSON bytes on a second run);
   - no Paper C block intersects a Paper B block;
   - `check_campaign` from P1 flags a row whose (node, instance seed) lies in a Paper B block.

**Done when:** tests pass, the registry and check report are committed, and the reviewer ACCEPTs.

---

## PH — Headroom census on existing logs (B16; reframe proposal §4) (≈ 2–3 h)

Read-only on existing data; CPU only; outputs only under `paperC/`.

1. **Inputs.** List every input with its path, branch or host location, and sha256. Copy only what is on the Mac; data that live only on a host are listed as "not read" rather than fetched.
   - Track S S0.4/S0.5 (`results/r1/tracks/{digits_mlp,tabular_mlp}/…` on the Track S branches);
   - Paper B sweep 1 and its audited labels;
   - the C1 30-seed table;
   - the B1/B2 exam campaigns.
2. **Per-node quantities.**
   - **E1:** g/V\* and sd(V\*)/g under A2-U and under the best available per-proposal forecaster; the share of E1 decisions within ±0.5 σ_node of the price.
   - **E2:** the keep-margin distribution and its mass within ±0.5 σ_node; false-keep and missed-keep rates against fresh-seed audits where they exist.
   - **Incumbent:** recorded vs re-audited incumbent value (winner's curse) as a function of the number of keeps.
   - **Budget:** binding share at the planned W, and the implied shadow price.
   - **Tails:** failed_invalid / degraded share and tail mass beyond ±4 σ_node.
3. **Code.** `paperc/census.py`, built on P1 records via small adapters per source, plus P5's relevance functions. Tests on fixtures, including the Track S STOP 4 numbers (S0.5 summary §4) as a known-answer case.
4. **Report.** `paperC/docs/reports/HEADROOM_CENSUS_<date>.md`: one table per node and a first placement on the headroom map. It ends with a proposal for which nodes and channels enter SPT collection; the choice itself is the author's (R-C2).

**Done when:** the report reproduces the S0.5 summary's E1/E2 numbers on the Track S inputs, all available sources are covered or listed as missing, and the reviewer ACCEPTs.

---

## P3 — E-SYN worlds and oracles (B3; plan §5, §3.5) (≈ 2–3 h; may continue tomorrow)

**Package:** `paperC/src/paperc/esyn/`, with modules `worlds.py`, `dp.py`, `oracle.py`.

1. **Port the Track S world model** from `trackS-ops-20261030` @ `fab88fc`:
   - `r1/tracks/worlds.py` (worlds N0, P0, P1, P2±; variants `diffuse` / `concentrated`), together with the parts of `simulate_controls.py` it mirrors (`World`, `VARIANTS`, `Stream`, `theta_table`, propose/forecast/update);
   - port only what the worlds need, and record the pin in the docstring.
2. **Equivalence test:** load the pinned originals from `git show` into a temporary directory inside the test, then compare campaign values and decisions on shared seeds, as Track S's own `test_tracks_worlds.py` does. Skip with a clear message if git is unavailable.
3. **New worlds:**
   - **incumbent interaction**: the increment of an edit depends on which earlier edits are in the incumbent, through a declared pairwise interaction matrix;
   - **shared incumbent error**: the recorded incumbent value carries a persistent error e shared by later comparisons until re-audit, as in the T4 revision's shared-latent case;
   - **strict null**: every channel off;
   - **evaluation-allocation worlds** (B17, if R-C1 adopts the reframe): verify, re-audit and final selection have a known value under a declared noise and shared-incumbent-error model.

   Each world declares which channel is on, as data.
4. **Exact DP** (`dp.py`):
   - backward induction for worlds whose decision state is finite after a declared discretisation, at minimum the budget world (state: trials left, runs left; known proposal-value law);
   - output: the optimal policy table and its value.
5. **Certified oracle** (`oracle.py`) for the other worlds, following Track S `oracle.certify`:
   - choose the best static policy on a selection seed block;
   - evaluate the members on a disjoint block;
   - size n from a pilot so that every 95 % half-width is ≤ 5 % of the planted gain;
   - fail if n_max is reached.
6. **Tests:**
   - in the **strict null** world, the DP/oracle gain over the best myopic rule is 0 within tolerance;
   - in each channel world, the gain is > 0 and its sign is as declared;
   - DP and the certified oracle agree on the budget world within tolerance;
   - campaigns write valid P1 records (`check_campaign` gives no violation).

**Done when:** tests pass, a table of oracle gains per world (`paperC/docs/reports/ESYN_ORACLE_TABLE_<date>.md`) is committed, and the reviewer ACCEPTs.

---

## P4 — Policy interface and non-RL ladder on E-SYN (B4; plan §7.0–§7.1) (≈ 2 h)

1. `paperc/policies.py`:
   - a `Policy` protocol: `act(state, rng) -> (action, prob)`, plus `name` and `version`;
     - *amendment of 16 Nov 2026 (P4 review): the implemented signature is `act(obs) -> (action, prob, selected)`, where `obs` is the decision-time view of the state and `selected` names the configuration on `final` rows; instead of an `rng` object, a stochastic policy reads a uniform keyed by the row's logged `eps_seed`, so that `check_campaign` replays it from the record;*
   - N0 (execute-all);
   - N1 (static thresholds (g, h), tuned by grid on dev seeds with a declared tuning budget);
   - N2 (myopic one-step rule with g tuned on dev);
   - N2b (single-step cost-sensitive action head on per-proposal outcomes);
   - N3 (non-myopic threshold members, ported from Track S's dynamic family at the pin);
   - N4 (budget DP from P3);
   - reference rows: the oracle, and random at matched realised budget.
2. **One belief for every arm** (plan §7.0): on E-SYN this is the world's own forecaster, passed in, never re-fitted per arm.
3. `paperc/runner.py`:
   - runs a policy on an E-SYN world for a set of instance seeds from the P2 registry's Paper C block;
   - writes P1 records;
   - returns paired terminal Y.
4. **Tests:**
   - in the null world, N2 is equivalent to the DP policy;
   - in the budget world, N4 matches DP within tolerance;
   - N1's tuning never touches test seeds;
   - every record passes `check_campaign`.

**Done when:** tests pass, a gain table (per world: each rung's gain over N1 with a 95 % CI, and its gap to the oracle) is committed, and the reviewer ACCEPTs.

---

## P5 — Decision-relevance check (B10; addendum §B.3) (≈ 1 h)

`paperc/relevance.py`. On any set of P1 records it reports:
- the share of eligible E1 decisions with |V\* − g| ≤ b · σ_node, for declared bands b (0.25, 0.5, 1.0);
- the same for E2 with |m̂| (keep margin);
- the distribution of V\* − g;
- the rule-skip share.

Add a CLI that writes a markdown report.

**Tests:**
- a synthetic record set with known shares;
- the Track S STOP 4 situation (all V\* − g ≈ 2.6–4.1 σ, all skips rule duplicates) reproduced as a fixture is reported as "no decision-relevant states".

**Done when:** tests pass and the reviewer ACCEPTs. The share threshold that gates SPT-2 is **not** set here; it goes to the author as a proposal.

---

## P6 — Fork design and go/no-go statistics (B8; plan §6) (≈ 2 h)

1. Fork selection: uniform, plus a near-threshold oversample, with `p_select` logged. Implement design weights 1/p_select.
2. τ̂² = (between-fork variance of fork Q differences) − (mean within-fork s.e.²), from r = 2 continuations per arm under 2 continuation policies.
   - *amendment of 16 Nov 2026 (P6 build): τ̂² is computed for two fork differences, the total Q difference `q` (plan §6) and the continuation difference `d` (`q` minus the forked candidate's own increment if kept, Track S's C = y_terminal − immediate). The null-world property of step 4 holds for `d` only, and only with continuation policies whose later decisions do not depend on the bookkeeping that differs between the arms (runs left, keeps so far, incumbent measurements), such as static thresholds on the belief; a budget-aware continuation (a Track S dynamic member) makes `d` non-zero even in `strict_null`. In `strict_null`, `q` still varies with the one-step value that the myopic rule already uses. τ̂² is reported pooled over E1 and E2 forks and per epoch; the pooled value includes the difference between the epochs' mean differences. Which difference, and which pooling, carries the go/no-go floor is left to the author's pre-declaration;*
3. Cross-fitted N6 improvement value on held-out forks.
4. **Validation on E-SYN:**
   - the null world gives τ̂² ≈ 0 with correct interval coverage over repeated simulations;
   - channel worlds detect heterogeneity;
   - design-weighted means are unbiased against the oracle.

**Done when:** tests pass, a coverage report is committed, and the reviewer ACCEPTs.

---

## P7 — Off-policy evaluation (B6; plan §6.1) (≈ 2–3 h)

FQE (primary; LightGBM and linear), per-decision weighted DR (check), IPW for population contrasts only, and support diagnostics (per-cluster action counts against the ≥ 30 target, ESS against the ≥ 200 target).

**Validation on E-SYN** against exact policy values: bias, RMSE and CI coverage for 3+ target policies under a behaviour mixture of P4 rungs × ε ∈ {0, 0.1, 0.25}.

On the isolated macOS arm64 checkout, the LightGBM wheel uses the LLVM OpenMP runtime bundled with the pinned scikit-learn wheel. Export the library directory and invoke Python directly so the loader path reaches the process and its workers.

```sh
paperc_platlib=$(paperC/.venv/bin/python -c 'import sysconfig; print(sysconfig.get_path("platlib"))')
export DYLD_LIBRARY_PATH="$paperc_platlib/sklearn/.dylibs"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
PYTHONPATH=paperC/src paperC/.venv/bin/python -m paperc.ope_validation
PYTHONPATH=paperC/src paperC/.venv/bin/python -m pytest -q -p no:cacheprovider paperC/tests
```

**Done when:** the validation report is committed, and the reviewer ACCEPTs.

---

## P8 — Learners (B7; plan §7.1–§7.2) (≈ 3 h)

N6 (regression on fork Q differences, one improvement step), R0 (FQI with LightGBM, γ = 1, time-to-go in both resources), R1 (IQL with a small MLP, CPU, γ = 1).

All three train on E-SYN behaviour-mixture logs and are selected on dev seeds by the plan's fixed rule.

**Tests:**
- where support exists, they recover a declared share of the DP gain;
- with deliberately removed support, the support diagnostics flag the gap rather than the learner silently extrapolating.

**P8 E-SYN benchmark.** Use the short budget law from the P7 control with eight slots and four runs. The reference
gap uses the transported P4 N1 thresholds and the exact DP value. Report the within-world best static Bayes-keep
value separately. Declare a 10% mean recovery floor on this engineering benchmark. Use three fixed candidate
settings per method and the highest supported paired mean gain on dev, with ties in grid order. Average the three
fit seeds at the selected setting on disjoint test roots. The paired intervals concern test-root variation holding
the fitted policies fixed. N6 uses the training mixture roots and their design-sampled forks under one fixed N1
continuation. R0 and R1 use the observed keep-forecast potential with zero absorbing potential and the original
audited terminal reward as their return. The validation module records the independent logging, support, dev and
test ranges and the deliberately unsupported case.

Run `python -m paperc.learner_validation` in the P8 venv with the P7 library path and thread limits above. PyTorch
training and inference use CPU tensors. The P7 loader supplies completed E-SYN E1/E2 episodes.

**Done when:** tests pass, a table is committed, and the reviewer ACCEPTs.

---

## P9 — Statistics (B9; plan §11) (≈ 2 h)

Paired campaign estimands, Holm across nodes, the two-part decision (one-sided superiority + TOST at δ, each at α = 0.025), and a whole-pipeline power simulator (train → tune → select → test) on E-SYN.

**Tests:**
- known-answer cases for TOST and Holm;
- the power simulator reproduces a closed-form case.

**P9 engineering design.** Pair by node, instance and start configuration. Average matched audits within manager
repetition, then average repetitions within each campaign for a fixed artifact. Compute one-sided paired t
superiority and TOST with each side at 0.025. Use the larger TOST side p-value, with Holm across the declared
nodes separately for superiority and TOST. Keep unavailable nodes in the family with p = 1. Keep statistical
rejection separate from the predeclared zero-effect equivalence power gate at 0.80.

Recollect, refit and dev-select the P8 methods independently in each of 12 two-node synthetic repetitions. Freeze
each selected artifact at its prespecified fit seed before drawing the test roots. Use the short-budget law and
δ equal to 10% of its exact DP-minus-best-myopic gap. Test the raw data and use two independent paired test
blocks for a variance-matched planning case at zero and at +2δ. The difference of the two blocks divided by
√2 is centered conditional on the selected artifacts and preserves the paired campaign variance. A separate
known-variance Normal check validates the test implementation against closed-form power. Report exact binomial
Monte Carlo intervals and dev-minus-test effects. This specification is for E-SYN engineering validation.

Run `python -m paperc.power_validation` with the P8 CPU venv, library path and thread limits.

**Done when:** tests pass and the reviewer ACCEPTs.

---

## P10 — Distillation on E-SYN: M1 and M4a (B12; addendum §A) (≈ 2 h)

1. **Teacher:** the dev-best of {N6, R0, R1} from P8.
2. **Student:** a smaller MLP with the same state view (information principle).
3. **M1:** distillation on behaviour-mixture states.
4. **M4a:** the student runs its own campaigns on training seeds and gets the teacher's action distribution at every visited eligible state. Reverse KL is primary, forward KL a sensitivity. Teacher queries and student campaigns are matched between M1 and M4a.
5. **Worlds:** the null world, and the keep-feedback world (P2+), where the student's actions shift the state distribution.
6. **Report:**
   - M4a − M1 and student − teacher on test seeds;
   - the teacher's support at the student's states (§A.5 of the addendum).

**Done when:** the report is committed and the reviewer ACCEPTs.

---

## After P10

B5 (loader and exporters; needs Paper B revision W1), B11 (real-loop SPT runner), B13 (real-node collection) and B14 (LM routes on GPU) each get their own runbook, independent review and author authorization. They are not part of this build runbook. The executor stops after P10, or earlier at any STOP, and reports in `BUILD_STATUS.md`.
