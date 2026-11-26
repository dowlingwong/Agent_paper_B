Reviewed base: `334c89ce0e036022cd1f993830a84809092ca44c` (harness branch `mac-trackg-port-mlgym-20261117b`; report at `4c3d0624c53f01b2f1e09209689d513a946f705e` on `mac-trackg-u3-mlgym-20261117b`; accepted in round 6)

# Independent review record — Track G U3 port kit, suite MLGym (mlgym_cifar10, mlgym_fmnist, mlgym_houseprice, mlgym_breakout_minatar)

**Unit.** The port kit for the four MLGym T1 candidates of the Ada census plan: `nodes/mlgym_*/`, `configs/trackg/nodes/mlgym_*.yaml`, `tests/trackg/test_port_mlgym.py` and the shared `tests/trackg/port_support.py` / `port_smoke_gpu.py` on the harness branch (base `717ad835`), and on the paper branch (base `main` `26177d82`) the port checklist's section F (`b715e110`, moved after section E) and the report `docs/r1/reports/TRACKG_U3_PORT_MLGYM_20261117.md`. Round 1 reviewed the first harness branch `mac-trackg-port-mlgym-20261117` (tip `bfc4624`) and report branch `mac-trackg-u3-mlgym-20261117` (`f0861c0b`); the `…b` branches continue from them.

**Authority.** R1-TRACKG-PORT-OWNER and R1-TRACKG-LICENCES (`main` `26177d82`; `author-decisions-20261117b` @
`33c82351`); the user's queue of 17 Nov (item 4) on `author-decisions-20261117b` @ `45fb94cc`.

**Process.** Two independent reviewers (separate agents that did not write the code): one for round 1, one for rounds 2–6. The rounds also reviewed changes shared with the autoresearch and MLAgentBench kits after their reviews. The reviewers edited, committed and pushed nothing. The round texts are reproduced below
as delivered, as block quotes, so that only this record's closing lines are read as the acceptance.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | harness `bfc4624`, report `f0861c0b` | NOT ACCEPTED (1 major, 9 minor) |
| 2 | harness `44c7ee89`, report `e044894b` | NOT ACCEPTED (2 major, 5 minor, 3 notes) |
| 3 | harness `a6524e64`, report `fd863c24` | NOT ACCEPTED (3 minor, 4 notes) |
| 4 | harness `9c91e393`, report `b92c4f1e` | NOT ACCEPTED (1 minor, 2 notes) |
| 5 | harness `4b03541d`, report `68c44acb` | ACCEPTED (3 notes) |
| 6 | harness `334c89ce`, report `4c3d0624` | ACCEPTED (2 notes) |

---

## Round 1 (harness `bfc4624`, report `f0861c0b`)

> REVIEW: Track G U3 port kit, suite MLGym (mlgym_cifar10, mlgym_fmnist, mlgym_houseprice, mlgym_breakout_minatar)
>
> Scope: I checked harness branch mac-trackg-port-mlgym-20261117 (tip bfc4624, base 717ad835) and report branch mac-trackg-u3-mlgym-20261117 (f0861c0b). I compared them with the checklist at 16185b0b, census §3 on ops-tasl-20261116, and MLGym at 9d40c1b5. I edited, committed and pushed nothing. Scratch files are only under /tmp/rv_mlgym/.
>
> WHAT CHECKS OUT
>
> - **Branch.** The branch adds 54 files and modifies, deletes or renames none. 717ad835 is an ancestor. The working tree is clean. The commit SHAs and the tip match the report.
> - **Specs (checklist A).**
>   - All four YAMLs load in the strict loader.
>   - `allow_new_files: false`. The editable entries are files only. `run_fixed_budget.py` and the helpers are frozen.
>   - Every committed file is in one of the two scopes (test-checked).
>   - The metric and test regexes are anchored on `AR_METRIC`/`AR_TEST`. `loss_regex` and `steps_regex` match the lines the frozen code prints.
>   - Budgets are `kind: steps`. There are no time words in keys. Determinism is at the defaults. `seed_env` is `AR_TRAIN_SEED`/`AR_SPLIT_SEED`. Selection is validation-only, and the test metric names differ.
>   - The Breakout `steps_regex` on `AR_STEPS env_steps=` is correct, because 2,000,000/64 rounds up to 2,000,064 and the updates do not fall on the last step.
> - **Wrappers (checklist B).**
>   - `ar_fixed_loop.py` runs exactly `--steps` loop iterations, checks them against `AR_BUDGET_VALUE`, and exits 3 if the count is short.
>   - Seeds come from the environment. The metric and test lines are printed by frozen code after training. No `cudnn.benchmark = True` anywhere.
>   - Data is checked against a hashed manifest (exit 5), sits behind the frozen `data` link, and is prepared by a one-off `setup_command`.
>   - The split code does what the report says: image nodes split 45k/5k and 54k/6k by `RandomState(split_seed)`. House Prices uses a fixed 20 % test at `random_state` 42 and draws validation by the split seed. Breakout uses `fold_in` validation keys with a collision check against the test keys `PRNGKey(0..4)`.
> - **Fidelity to the suite.**
>   - The CNNs match MLGym.
>   - The Trainer defaults are written out correctly: AdamW 5e-5, betas 0.9/0.999, eps 1e-8, decay 0.01 with none on biases, `get_linear_schedule_with_warmup` with 500 warmup steps, clip 1.0, batch 64.
>   - 7,820 and 9,380 steps equal 10 × ceil(50,000/64) and 10 × ceil(60,000/64).
>   - The test-set evaluation and best-checkpoint reload were removed, and this is stated. Dropping the last incomplete batch is stated.
>   - House Prices: I ran the frozen wrapper on MLGym's real table (sha256 `1e18addf…929d41`, md5 `80ccab65…b5577`, both verified) with split seed 42. It printed `AR_TEST test_rmse=30340.111853`. That matches MLGym's `baseline_scores` value of 30340.111853413255 exactly.
>   - Breakout:
>     - `policy.py` differs from MLGym only in the three stated changes.
>     - `networks.py` and `helpers.py` are unchanged apart from docstrings, and `config.yaml` lacks only the three keys.
>     - The init and training keys (`rng_list[1]`/`rng_list[0]` from `PRNGKey(seed)`, default 42) match MLGym's first checkpoint.
>     - `evaluate_policy.rollout_batch` is MLGym's rollout (256 environments, 999 frames).
> - **Edits (checklist C).**
>   - Each node has 4 edits. All are in scope and apply. The sha256 values of every `E*.diff` and of all four `manifest.json` files match the report.
>   - The manifests are committed in 168acb5d, before any run. `measured: false`. Re-declaring reproduces them byte for byte under 3.12, and everything except the AST-based normalised hashes matches under 3.13.
>   - The House Prices E3×E4 interaction is declared.
> - **Tests.**
>   - Python 3.13 (`/tmp/trackg_venv`): `test_port_mlgym.py` gives 14 passed, 3 skipped (the torch and JAX smokes). The whole `tests/trackg` directory gives 187 passed, 3 skipped, as reported.
>   - Python 3.12 (`/tmp/tgport312`): `test_port_mlgym.py` gives 17 passed in 596 s. That includes the synthetic smoke for all four nodes. The report's 383.76 s is from another host.
>   - Every outcome, validation metric, sealed test value and `not_forced` entry in the report's four smoke tables is identical to my run records. The repeated baseline is bit-identical.
>   - `test_trackg_t0_identity::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit` also fails on the unchanged 717ad835 under 3.12, as the report says.
>   - The frozen-path test covers every committed frozen file, plus a new-file refusal.
> - **Report statements.** MLGym is CC BY-NC 4.0 (its LICENSE and README). The commit date is 10 Aug 2025. Breakout's `training_timeout`/`baseline_scores` and the 5-checkpoint protocol are as described.
>
> FINDINGS
>
> 1. **MAJOR – The image nodes' budget guarantee is overstated, and the slow-edit risk is not raised for them.**
>    - Report line 102 says a proposer cannot change the loop ("no gradient accumulation, EMA or custom loops") and that "the budget therefore cannot be bypassed". This is not true of the code:
>      - The editable `build_optimizer` creates the optimizer, so the editable `training_step` can keep a reference and call `optimizer.step()` itself, any number of times per loop step. `ar_fixed_loop.py:148-157` only calls `training_step` and then runs its own zero_grad/backward/step.
>      - `build_model` can return a module that keeps EMA weights and uses them in eval mode.
>      - `CONFIG["batch_size"]` may be up to `MAX_BATCH_SIZE = 4096` (`nodes/mlgym_cifar10/run_fixed_budget.py:21`, fmnist `:21`). That is 64× the baseline's samples per step within "7,820 steps".
>    - Such edits stay inside the editable scope. A slow edit hits the timeout, which is classified `infrastructure_failure` (`src/autoresearch/trackg/outcome.py:125-126`) and is "rerun, not deduplicated" (`runner.py:234`). That is exactly the hazard the report raises for House Prices as open point 2 (line 241), but the image nodes are not mentioned.
>    - Fix:
>      - (a) Correct line 102: loop iterations and batch order are fixed, but optimizer steps and compute per step are not bounded against in-process editable code.
>      - (b) Add the image nodes, and the batch-size cap, to the author's open point 2 on how timed-out edits are classified and rerun.
>      - (c) Optionally add a cheap guard: wrap `optimizer.step` in `train_fixed_steps` to count calls and exit 3 if the count is not exactly `budget`. Lower `MAX_BATCH_SIZE` (for example to 512), or justify 4096.
>
> 2. **MINOR – The status line claims a review that has not happened.** Report line 3 says the kits "were independently reviewed (see `docs/r1/reviews/TRACKG_U3_PORT_MLGYM_REVIEW_20261117.md`)". That file does not exist on the branch, and commit f0861c0b's own message says "Independent review pending". Fix: say "Review: pending" until a review is filed at that path, and then state its verdict.
>
> 3. **MINOR – A referenced file is missing.** Report line 77 cites "`declare_edits_output.txt` kept with the bundle". No such file exists in either worktree. Fix: commit the declare-script output, for example under `nodes/<node>/representative_edits/`, or remove the reference.
>
> 4. **MINOR – The licence open point misstates the current situation.** Report line 16 frames the CC BY-NC issue as arising only "if the harness repository is or becomes public, or is relicensed". The harness repository already has an MIT `LICENSE` at its root (`/tmp/pb/wt/tg-mlgym/LICENSE`, "MIT License, Copyright (c) 2026 Dowling_Wong"). Without a scoping note, the branch puts non-commercial files under an MIT repository licence today. The PPO files are also partly gymnax/gymnax-blines Apache-2.0 material (MLGym README §License). The node NOTICE.md mentions this, but the report does not. Fix: state the MIT/CC BY-NC conflict and the Apache-2.0 origin in the open point. Propose a remedy for the author, for example a licence-scope line in the root LICENSE/README excluding `nodes/mlgym_*`, or keeping these nodes outside the MIT tree.
>
> 5. **MINOR – Ada deployment trap: CPU fallback is silent, and Breakout's requirements pin a CPU JAX.**
>    - `nodes/mlgym_breakout_minatar/requirements.txt:4` pins `jax[cpu]==0.4.35`. Only the report prose (line 254) says to use `jax[cuda12]`.
>    - Neither `ar_fixed_loop.pick_device` (`ar_fixed_loop.py:90-94`) nor the Breakout wrapper (`run_fixed_budget.py:88-90`) refuses to run on CPU. A wrong GPU UUID or a CPU JAX install produces an `ok` run on CPU, which corrupts U2 timing and the 3× timeout basis. The census plan's rule is "OOM/CPU fallback = STOP".
>    - Fix: give the GPU host a `jax[cuda12]==0.4.35` requirements line, or a separate requirements file. In the wrappers, exit with a distinct `AR_ERROR` when `CUDA_VISIBLE_DEVICES` is non-empty but no GPU is visible, and tell the experiment agent to treat that as STOP.
>
> 6. **MINOR – The Breakout `not_forced` expectation does not hold on the prescribed environment.** The local smoke ran in an environment that has torch, so the shim forced the torch settings and Breakout showed only `dataloader_workers` (report table; `configs/trackg/nodes/mlgym_breakout_minatar.yaml:89` claims the opposite). On Ada, the report itself prescribes a separate JAX environment (line 254). There the shim records `torch_absent`, and `not_forced` will also list the cudnn, deterministic-algorithms and thread settings. Checklist E requires each extra entry to be explained. Fix: list the expected Breakout `not_forced` entries for a torch-free JAX environment in the report and the deployment steps. Note that threads are not bounded for XLA CPU work.
>
> 7. **MINOR – The known-limit disclosure is incomplete.** Report line 106 names forged lines and run-time patching. It does not name that editable code can read `AR_SPLIT_SEED` from the environment (the runner sets it, `runner.py:256-261`) and the task files through `data/` in the working directory. An edit could then fit on the validation rows: House Prices reads the whole CSV including validation, and the image nodes have `train_x.npy` including the validation images. That would inflate the selection metric. Fix: add this to the known limits. Optionally pop the seed variables from `os.environ` in the wrapper before `import train`, and/or have the harness flag diffs that mention `AR_SPLIT_SEED`, `data/`, `np.load` or `read_csv` in editable files.
>
> 8. **MINOR – House Prices seed semantics for the noise floor are not stated.**
>    - The training seed only reaches `build_model` (`nodes/mlgym_houseprice/train.py:21`). Ridge ignores it, so all baseline seed variance comes from re-drawing the 146-row validation set.
>    - With split seed 42 the validation RMSE is 30638 against a test RMSE of 30340.
>    - If G.1b fixes the split seed, the baseline noise floor is exactly zero.
>    - Fix: state this in the report as an open point for G.1b/D21 interpretation.
>
> 9. **MINOR – The image nodes lack checklist C's divergence/interaction edit, and the gap is not justified.**
>    - For cifar10 and fmnist, E2 (lr 1e-3) is the standard Adam rate and is unlikely to diverge.
>    - No edit is declared as interacting with another, for example E2×E3 (batch norm allows higher learning rates).
>    - Fix: state the intended interaction pair or why the task does not allow such an edit. Alternatively, declare a new manifest before any measurement; the old one is kept.
>
> 10. **MINOR – The consequence of changing Breakout's provisional budget is not stated.** Report line 54 says "the census measures it". Changing `run_budget.value` changes the spec hash, and the manifest records both `run_budget` and `node_spec_sha256` (enforced by `check_manifest`). So it requires re-declared edits and a new review (checklist A: "not changed afterwards without a new review"). The estimate is also uncertain: the PPO loop dispatches 31,251 separate jitted `get_transition` calls from Python, so dispatch overhead dominates. Fix: say this explicitly in the report and the deployment steps.
>
> VERDICT: NOT ACCEPTED

---

## Round 2 (harness `44c7ee89`, report `e044894b`)

> # Review round 2: Track G U3 port kit, suite MLGym
>
> **Verdict: NOT ACCEPTED** (2 MAJOR, 5 MINOR, 3 NOTE)
>
> ## What was reviewed
>
> - Harness branch `mac-trackg-port-mlgym-20261117b` in `/tmp/pb/wt/tgb-mlgym`, tip `44c7ee895db90b9be667a1c7639f4ea5bc97829f`. The base is `717ad835`, the round-1 tip is `bfc4624`, and the round-2 commits are `165788af` and `44c7ee89`.
> - Paper branch `mac-trackg-u3-mlgym-20261117b` in `/tmp/pb/wt/u3b-mlgym`: commits `b715e110` and `e044894b`, on top of `26177d82`.
> - Compared against: the round-1 review, U1 and the census on `gh/ops-tasl-20261116`, the PLAN rows on `gh/author-decisions-20261117b`, and MLGym at `/tmp/suites/MLGym` (`9d40c1b5`, 10 Aug 2025).
> - Nothing in any repository was modified, committed or pushed. Scratch was only under `/tmp/rv_mlgym2/`. `tmp/` there has been emptied; the adversarial scripts are in `adv/` and the results of the last batch are in `adv_results.txt`.
>
> ## Checks that pass
>
> - **Tests.** `test_port_mlgym.py` under Python 3.12 (`/tmp/tgport312`): **21 passed** in 737 s. The whole `tests/trackg` directory without the smokes: 189 passed and 1 failed. The failure is `test_trackg_t0_identity::…byte_identical_to_the_base_commit`, as the report says. With the 4 smokes this gives 193 passed and 1 failed, matching the report.
> - **Branch scope.** The branch only adds files: none is modified or deleted relative to `717ad835`, and every path is under `nodes/mlgym_*/`, `configs/trackg/nodes/` or `tests/trackg/`.
>   - `port_support.py`, `port_smoke_gpu.py`, `ar_data.py` and `ar_fixed_loop.py` are byte-identical on `tgb-mlgym`, `tgb-mlab` and `tgb-ar`.
>   - `b715e110` is in the history of the other two `u3b` branches. R1-TRACKG-LICENCES is in `33c82351`, which is an ancestor of `author-decisions-20261117b`.
> - **Hashes.** All 4 manifest sha256 values and all 16 `E*.diff` sha256 values in the report match the files. The superseded round-1 manifests differ from the new ones only in `node_spec_sha256`.
> - **Composability table.** I recomputed `composable_pairs` for all 12 ordered pairs of each node, and the table is exact:
>   - cifar10, fmnist and houseprice: every pair applies except E1/E2 (refused).
>   - breakout: E1+E2, E1+E4 and E2+E4 are refused in both orders.
> - **Smoke tables.** Every outcome, validation value, sealed test value and `not_forced` entry in the four tables equals my run records.
> - **Licence and provenance.**
>   - `LICENCES.md` matches U1 §3: CC BY-NC 4.0; the Apache-2.0 parts from gymnax and gymnax-blines; CIFAR-10 "license: unknown"; Fashion-MNIST MIT; Kaggle terms with no licence claimed.
>   - The U1 revisions `0b27149` and `531be5e` appear in `prepare_data.py` and in U1 line 305.
>   - The House Prices table is 460,676 B and its sha256 `1e18addf…a5f929d41` was re-verified on MLGym's file.
>   - Checklist F has the required content and now sits after section E.
> - **Optimizer-step guard.** A `training_step` that calls the returned optimizer's `step()` gives `AR_ERROR the optimizer stepped 60 times for a budget of 30`, exit 3, `divergent/nonzero_exit`.
> - **GPU check.** A fake GPU UUID gives `AR_INFRA …`, exit 6, `infrastructure_failure`. Printing the same `AR_INFRA` line from editable code (without seeking) is not classed as an infrastructure failure.
> - **Forging classes now closed** (each shown on synthetic data through the real `WorkingCopyRunner`): a forged line printed in `predict_logits`, an `atexit` print, a `sys.stdout` wrapper that rewrites the result line, and a thread printing through `sys.stdout`. In each case the outcome is the real value.
> - **Data directory.** A planted file in the shared data directory is refused (exit 5).
> - **Setup scripts (read only, no network here).** `--out` must lie under `$AR_TRACKG_DATA_ROOT`. A non-empty directory without a manifest is refused. The hub revision is checked before download. The manifest is written last, then the directory is made read-only, and the hashes are re-checked on a re-run.
>
> ## Round-1 findings
>
> | # | Round-1 finding | Status |
> |---|---|---|
> | 1 MAJOR | Budget guarantee overstated; slow-edit risk not raised for the image nodes | **Fixed.** The claim is corrected (report l. 95–106). A post-step hook counts `step()` calls and exits 3, confirmed by the adversarial run. Open point 2 covers the batch cap of 4,096 and the classification of timeouts. Residuals (a second optimizer, which I confirmed passes as `ok`; updates inside `step()`) are disclosed. |
> | 2 | Status line claimed a review that had not happened | **Fixed** ("see … once filed"). |
> | 3 | Missing `declare_edits_output.txt` | **Fixed** (the reference is removed). |
> | 4 | MIT/CC BY-NC conflict and Apache-2.0 origin | **Fixed.** The report has a licence section with remedies (a)–(c), and each node's `LICENCES.md` has a scope note. |
> | 5 | Silent CPU fallback; Breakout pins a CPU JAX | **Fixed** (`AR_INFRA` in both wrappers, `requirements_gpu.txt`, a STOP instruction). See new finding 5: the JAX requirements still cannot run the wrapper. |
> | 6 | Breakout's `not_forced` in a torch-free environment | **Fixed.** The list in the report and the yaml matches `determinism.py` lines 58–63 and 153. |
> | 7 | Split seed and data readable by editable code | **Fixed** as a disclosure (l. 101–105). The optional mitigations were not taken, which is acceptable. |
> | 8 | House Prices seed semantics | **Fixed** (l. 64–68, open point 4). |
> | 9 | No divergence or interaction edit on the image nodes | **Fixed.** E2×E3 is declared, and the reason no image edit diverges is given. See NOTE 8. |
> | 10 | Consequence of changing Breakout's budget | **Fixed** (l. 76–78, deployment step 5). |
>
> ## New findings
>
> ### 1. MAJOR — A forked child process or a thread holding its own copy of fd 1 still writes a forged `AR_METRIC` after the real one, and `lseek` forces an infrastructure STOP. The report says this cannot happen.
>
> **Where.** `ar_data.seal`/`emit`/`finish` (shared by all nodes) and the inline copies in `nodes/mlgym_breakout_minatar/run_fixed_budget.py`. Report l. 92–93 ("threads of the editable code cannot print into the log") and l. 170 ("…print a line after them from its evaluation code or a thread"). Report l. 297–299 on the `AR_INFRA` pattern ("the same text printed later by editable code is not classed as an infrastructure failure. Treat such a run as a STOP").
>
> **Failure scenario.** I tested this on synthetic `mlgym_cifar10` with a budget of 30, through `WorkingCopyRunner`:
>
> - **`fork_child`.** At import, `train.py` forks a child. The child polls `os.getppid()` and writes `AR_METRIC val_accuracy=0.999999` to its inherited fd 1 the moment the wrapper exits.
>   - The log ends `…AR_METRIC val_accuracy=0.098000 / AR_TEST … / AR_METRIC val_accuracy=0.999999`.
>   - The outcome is **`ok 0.999999`**. The runner's `leftover_processes_killed: true` came too late.
> - **`thread_owndup`.** At import, a daemon thread takes `os.dup(1)` and loops writing the forged line.
>   - It won the race between `emit` and `os._exit`.
>   - The outcome is **`ok 0.999999`**. `seal()` only redirects descriptors 1 and 2, not a copy the editable code took.
> - **`infra_lseek`.** In `build_model`, `os.lseek(1, 0, 0)` followed by writing the `AR_INFRA` text puts that line at the top of the log. This works because the runner opens `run.log` with `"wb"`, without `O_APPEND`, and the offset is shared. The `\A(?:(?!AR_DEVICE ).*\n)*?AR_INFRA…` pattern matches, and the outcome is **`infrastructure_failure`**. Under the report's own rule, that proposal STOPs the census.
> - **Truncation.** A surviving child can also `ftruncate` the log and rewrite it with a single forged metric line. My single attempt lost the race, but nothing prevents it. A truncated and rewritten log would also defeat open point 7's proposed rule of refusing runs with more than one metric match.
>
> The known-limit lists (l. 99–100, l. 172, `ar_data` docstring) name the saved descriptor and patching, but not child processes, descriptors the editable code duplicated itself, or seeking within the log. The code is shared, so the sibling kits are affected the same way.
>
> **Fix.**
>
> - **Port level (all wrappers):**
>   - Call `prctl(PR_SET_CHILD_SUBREAPER, 1)` (via `ctypes`) before importing the editable code.
>   - Just before `seal()`, SIGKILL and reap every descendant process (walk `/proc` by ppid until none remain).
>   - In `seal()`, `dup2` `/dev/null` over every descriptor whose `(st_dev, st_ino)` equals the log's, except the saved one.
>   - Anchor the infrastructure pattern at the end of the log as well (`…unavailable\n?\Z`): the wrapper exits right after printing it, so a line placed earlier by editable code no longer matches.
> - **Report:**
>   - Correct l. 92–93, 170 and 297–299.
>   - Add child processes, self-duplicated descriptors and seek/truncate to the known limits.
>   - In open point 7, add that the harness should open the log with `O_APPEND` or read it through a pipe, SIGKILL the session and fix the log length when the wrapper exits (before parsing), and then refuse runs with more than one metric match.
>
> ### 2. MAJOR — Editable `predict_logits` can forge both accuracies through the frozen metric code with a tensor subclass or a global `TorchFunctionMode`
>
> **Where.** `ar_fixed_loop.predict_classes` and `accuracy`, shared by both image nodes and the MLAgentBench torch nodes. Report l. 104 relies on diff keywords (`AR_SPLIT_SEED`, `data/`, `np.load`, `read_csv`) to make such exploits visible.
>
> **Failure scenario.**
>
> - `subclass_eq`: `predict_logits` returns `model(x).as_subclass(_T)`, where `_T.__torch_function__` turns `Tensor.__eq__` into all-True.
> - The shape check passes, and the frozen `(pred == labels).double().mean()` runs through `_T`.
> - The outcome is **`ok 1.0`**, with `AR_TEST test_accuracy=1.000000` in the sealed record.
> - The diff contains none of the audit keywords and prints nothing.
> - Entering a `torch.overrides.TorchFunctionMode` once at import (`M().__enter__()`) has the same effect on plain tensors (checked in isolation: accuracy 1.0).
>
> **Fix.**
>
> - In `predict_classes`, require `type(logits) is torch.Tensor`; do the same for `loss` in `train_fixed_steps`.
> - Compute `argmax`, the comparison and `.item()` under `with torch._C.DisableTorchFunction():`. In isolation this restored the true accuracy (0.25) for both the subclass and the mode.
> - Name `TorchDispatchMode` as the remaining in-process limit.
> - Re-declare the manifests if their code-state hashes change; the manifest test will show whether they do.
>
> ### 3. MINOR — Data changed by one run is charged to the next run as `divergent`
>
> **Where.** The `nodes/mlgym_{cifar10,fmnist,houseprice}/run_fixed_budget.py` wrappers check the data only once, before the editable code runs. Exit 5 is not an infrastructure pattern. Report l. 180.
>
> **Failure scenario.**
>
> - `plant_by_run`: `predict_logits` runs `chmod` on `data/` and writes `cache.npy` there. That run is **`ok 0.098`**.
> - The next unchanged baseline is **`divergent/nonzero_exit` (rc 5)**, "directory holds files the manifest does not list".
> - From then on, every run in the campaign is charged as `divergent` to whichever proposal it was.
> - The shared `ar_data` docstring describes a post-run re-check with its own prefix, and the autoresearch node uses one (`prefix="AR_ERROR train.py changed the data:"`). The MLGym wrappers do not.
>
> **Fix.**
>
> - Call `ar_data.verify(..., prefix="AR_ERROR train.py changed the data:")` after both evaluations and before `seal()`, so the run that made the change is the one that fails.
> - In the report and the deployment steps, say that a pre-import exit 5 / `AR_ERROR data` is classed `divergent` and must be treated as a STOP. Alternatively, add an infrastructure pattern anchored before the editable import.
>
> ### 4. MINOR — Editable code can hide a NaN loss, so a divergent run is classed `ok`
>
> **Where.** `ar_fixed_loop.train_fixed_steps` prints the loss lines through `print`, which editable code can replace. The divergence class and the image nodes' `steps_regex` (`^step (\d+) loss`) both read those lines, while `AR_STEPS` goes through `emit` but is not used.
>
> **Failure scenario.**
>
> - `hide_nan_loss`: the loss is multiplied by NaN, and a `sys.stdout` wrapper rewrites `loss nan` as `loss 1.0`.
> - The outcome is **`ok 0.1012`** instead of `divergent/non_finite_loss`.
> - The report only claims that the result lines resist replacement of `sys.stdout`.
>
> **Fix.**
>
> - Write the loss lines through `ar_data.emit`. At minimum, when the running mean is non-finite, write that line through `emit`, or exit with a distinct code.
> - Optionally move `steps_regex` to `^AR_STEPS completed=(\d+)$`. This is a spec change, so the edits must be re-declared.
> - Otherwise, disclose the limit.
>
> ### 5. MINOR — The prescribed JAX environment for Breakout cannot run the wrapper: `tqdm` (and `pytest` for the smoke) is missing
>
> **Where.** `nodes/mlgym_breakout_minatar/requirements.txt` and `requirements_gpu.txt`. `run_fixed_budget.py` (`import tqdm`) and `policy.py` line 25 (`import tqdm`). `tests/trackg/port_smoke_gpu.py` imports `test_port_mlgym`, which imports `pytest`. Report deployment steps 3 and 5.
>
> **Failure scenario.**
>
> - None of the pinned packages pulls in `tqdm`. I computed the dependency closure from the installed metadata of `jax`, `flax`, `optax`, `chex`, `gymnax`, `tensorflow-probability`, `dotmap`, `PyYAML` and `numpy`.
> - The local smoke passed only because the torch environment has `tqdm` through `huggingface_hub`, `transformers` and `peft`.
> - In the torch-free environment from `requirements_gpu.txt`, every Breakout run would fail with `ModuleNotFoundError`, classed `divergent/nonzero_exit`.
> - `port_smoke_gpu` would not start without `pytest`.
>
> **Fix.** Pin `tqdm` (the locally used 4.70.1) in both Breakout requirements files. Add `pytest` to them or to deployment step 3.
>
> ### 6. MINOR — The House Prices data source is not reconciled with R1-TRACKG-LICENCES
>
> **Where.** `nodes/mlgym_houseprice/prepare_data.py` (`URL` = MLGym's copy on raw.githubusercontent.com), `LICENCES.md`, and the report (l. 57–62, 306, deployment step 4).
>
> **Failure scenario.**
>
> - R1-TRACKG-LICENCES says: "Kaggle House Price 由使用者自行下载并遵守比赛条款" (the user downloads the Kaggle House Prices data themselves and follows the competition rules).
> - Checklist F says each dataset is fetched "from its source URL".
> - The kit instead fetches MLGym's redistributed copy. Neither the report nor `LICENCES.md` says how this meets the decision.
> - U1 notes that the copy's identity with Kaggle's `train.csv` was not checked.
>
> **Fix.** Add an open point for the author. Either accept MLGym's copy explicitly, or make the Kaggle download, under Kaggle's rules, the documented route through `--from-file`. The pinned sha256 and md5 would then confirm byte identity, or show a difference.
>
> ### 7. MINOR — Wrong hash suffix in the report
>
> **Where.** Report l. 60: "`1e18addf…5929d41`".
>
> **Problem.** The pinned sha256 ends `…8f692a5f929d41`, so the last 7 characters are `f929d41`; `5929d41` is not a suffix of it. The md5 abbreviation is correct.
>
> **Fix.** Write `1e18addf…f929d41`, or the full hash.
>
> ### 8. NOTE — The interaction pair is declared only in the report
>
> The S1.1 pairs (E2×E3 for the image nodes and Breakout, E3×E4 for House Prices) are not recorded in the frozen node. The manifest has no field for them, and the test's `INTERACTING` table lists every composing pair. At the next re-declaration, record the declared pair next to the manifest or in the yaml's `notes`, so it is frozen together with the edits.
>
> ### 9. NOTE — House Prices accepts any table when the manifest says `synthetic: true`
>
> `run_fixed_budget.py` lines 74–78 skip the pinned-hash check for a synthetic manifest and print only `AR_DATA synthetic table`. This can only be reached by rewriting the manifest, which is a disclosed limit. Still, on the census host, gate the bypass on a test-only environment variable, or add a deployment check that no log contains `AR_DATA synthetic`.
>
> ### 10. NOTE — Smaller points
>
> - **Breakout compute.** `epoch_ppo` and `n_minibatch` in the editable `config.yaml` also multiply the gradient updates per environment step. Open point 2 names only the network and `num_train_envs`.
> - **Apache-2.0 text.** The Apache-2.0 licence text for the gymnax-derived parts is linked, not included. This follows MLGym's own practice, but Apache-2.0 §4(a) asks for a copy.
>
> ## Summary
>
> Round 2 fixes all ten round-1 findings, and every hash, commit id, table value and test count in the report checks out. Two new MAJOR problems block acceptance. Both are in the shared frozen code, so the sibling kits are affected too:
>
> - the result lines can still be forged after the real ones, through a forked child process or a thread holding its own copy of fd 1, and the report claims otherwise;
> - a tensor subclass or a global `TorchFunctionMode` returned or entered by editable code forges both accuracies through the frozen metric code.
>
> Both have small fixes in the shared code. Findings 3–7 are also needed before deployment, in particular the missing `tqdm`, which would make every Breakout run fail on Ada.

---

## Round 3 (harness `a6524e64`, report `fd863c24`)

> # Review round 3: Track G U3 port kit, suite MLGym
>
> **Verdict: NOT ACCEPTED** (0 MAJOR, 3 MINOR, 4 NOTE)
>
> The round-2 MAJORs are answered: finding 1 by disclosure, which I accept as the coordinator framed it, and finding 2 by code. What blocks acceptance is three MINOR findings with small fixes:
>
> - the dispatch-mode check that the MLAgentBench copy of `ar_fixed_loop.py` already has is missing here;
> - a partial line still hides a NaN loss;
> - the threat model has four inaccuracies.
>
> ## What was reviewed
>
> - **Harness:** `/tmp/pb/wt/tgb-mlgym`, `44c7ee89..a6524e64` (tip `a6524e641e01972da2c3790a30aca2689f22528a`).
> - **Report:** `/tmp/pb/wt/u3b-mlgym`, `e044894b..fd863c24`.
> - Both worktrees are clean. Nothing was modified, committed or pushed. Scratch was only under `/tmp/rv_mlgym2/`, and `tmp/` there has been emptied.
>
> ## Checks run
>
> - **Tests.** `test_port_mlgym.py` under Python 3.12 gave **26 passed** (684 s), which matches the report.
>   - The four manifests still reproduce under 3.12, with no re-declaration needed.
>   - The smoke runs reproduce every outcome, validation value and sealed test value in the report's four tables.
> - **Shared files.** `port_support.py`, `port_smoke_gpu.py` and `ar_data.py` are byte-identical across the mlgym, mlab and ar worktrees. `ar_fixed_loop.py` is not; see finding 1.
> - **Attacks.** I re-ran the round-2 attacks and four new ones on synthetic `mlgym_cifar10` (budget 30) through the real `WorkingCopyRunner`. Results are in `/tmp/rv_mlgym2/adv_r3.txt`.
>
> | Attack | Round 2 | Round 3 |
> |---|---|---|
> | forged line printed in `predict_logits` / `atexit` print / `sys.stdout` rewrite / thread printing via `sys.stdout` | real value | real value |
> | partial line left before the result line (new) | — | real value (`seal` newline works) |
> | `step()` inside `training_step` | exit 3 | exit 3 |
> | second optimizer | `ok` (disclosed) | `ok` (disclosed) |
> | tensor subclass from `predict_logits` | **`ok 1.0`/test 1.0** | exit 4, `divergent` (fixed) |
> | global `TorchFunctionMode` (new) | — | real value (fixed) |
> | global `TorchDispatchMode` (new) | — | **`ok 1.0`, `AR_TEST test_accuracy=1.000000`** (finding 1) |
> | NaN loss hidden by a `sys.stdout` filter | **`ok`** | `divergent/non_finite_loss` (fixed) |
> | NaN loss hidden by a partial-line prefix plus clean forged step lines (new) | — | **`ok 0.1012`** (finding 2) |
> | run plants `data/cache.npy` | run `ok`, the next run is blamed | the planting run fails itself with exit 5 (`AR_ERROR the editable code changed the data:`); the next start exits 5, which the report now treats as a STOP (fixed) |
> | fake GPU UUID | `infrastructure_failure` | `infrastructure_failure` |
> | forked child writes after the wrapper exits | **`ok 0.999999`** | **`ok 0.999999`** (now disclosed) |
> | thread with its own `dup(1)` | **`ok 0.999999`** | real value this time (a race; disclosed) |
> | `lseek` puts `AR_INFRA` at the top of the log | **`infrastructure_failure`** | **`infrastructure_failure`** (now disclosed) |
> | `AR_INFRA` printed by editable code | `ok` | `ok` |
>
> ## Round-2 findings
>
> | # | Round-2 finding | Status |
> |---|---|---|
> | 1 MAJOR | Forged result line via a forked child, an own `dup` or `lseek`; the report claimed closure | **Answered by disclosure.** The threat model (report l. 181) and open point 8 replace the claims of closure and name these routes and the harness changes that would close them. The routes are still open: I re-demonstrated the fork and the `lseek`. The remaining inaccuracies are in finding 3. |
> | 2 MAJOR | Tensor subclass or global `TorchFunctionMode` forges the accuracy | **Fixed for both.** `type(...) is torch.Tensor` checks, argmax and accuracy under `DisableTorchFunction`, and a new test. The dispatch-mode residual is finding 1. |
> | 3 MINOR | Data changed by one run blamed on the next run | **Fixed.** A re-check runs before `seal` with a distinct prefix, and a start-of-run exit 5 is treated as a STOP (report l. 189). |
> | 4 MINOR | NaN loss hidden by replacing `sys.stdout` | **Partly fixed.** The loss lines now go through `emit` and that attack is caught. The partial-line variant still hides it (finding 2). |
> | 5 MINOR | `tqdm` and `pytest` missing for Breakout | **Fixed.** `tqdm==4.70.1` is pinned in both files; `pytest` and `PyYAML` are added in deployment step 3. |
> | 6 MINOR | House Prices data source vs R1-TRACKG-LICENCES | **Fixed** (open point 4). |
> | 7 MINOR | Hash typo | **Fixed** (`…a5f929d41`). |
> | 8 NOTE | Interaction pairs declared only in the report | Not done, as stated. Remains a NOTE. |
> | 9 NOTE | House Prices synthetic mode | **Fixed** (open point 9). |
> | 10 NOTE | Breakout `epoch_ppo`/`n_minibatch`; Apache-2.0 text | `epoch_ppo`/`n_minibatch` **fixed** (open point 2). The Apache-2.0 text is not addressed; this stays a low NOTE. |
>
> ## New findings
>
> ### 1. MINOR — A global `TorchDispatchMode` still forges both accuracies, and MLGym's `ar_fixed_loop.py` lacks the guard its MLAgentBench copy has
>
> **Where.** `nodes/mlgym_{cifar10,fmnist}/ar_fixed_loop.py` (`predict_classes`, `accuracy`). Report l. 175 ("`ar_fixed_loop.py` is byte-identical in every node", in the section common to the three kits) and the threat model at l. 181.
>
> **Failure scenario.**
>
> - `train.py` enters a `TorchDispatchMode` at import (`_D().__enter__()`) whose `__torch_dispatch__` makes `aten.eq.Tensor` return ones.
> - `DisableTorchFunction` does not reach dispatch modes. The run gives **`ok 1.0` with `AR_TEST test_accuracy=1.000000`**.
> - The MLAgentBench branch (`tgb-mlab`, `5563fa3`) already adds `no_active_modes()`. It refuses with exit 4 when `torch._C._len_torch_dispatch_stack()` or `_len_torch_function_stack()` is non-zero, and it is called in `predict_classes` and `accuracy`.
> - The five torch nodes therefore now carry two different `ar_fixed_loop.py` files: `24058df1…` on mlab and `9b11569a…` on mlgym.
> - The threat model does not list dispatch modes among the remaining routes. Round 2 asked for them to be named.
>
> **Fix.**
>
> - Take the mlab version of `ar_fixed_loop.py`, so the copy is identical in all five nodes again.
> - Add a dispatch-mode case to `check_plain_tensor_metric`.
> - In the threat model, name what the guard still does not detect: patches of torch itself, which the mlab docstring already mentions.
>
> ### 2. MINOR — A NaN loss can still be hidden with a partial line, despite the loss lines going through `emit`
>
> **Where.** `ar_data.emit` (shared) as used for the loss lines in `ar_fixed_loop.train_fixed_steps`, Breakout's `on_update` and House Prices' `step 1 loss`. Report l. 99–100 ("loss lines go through `emit` (finding 4)").
>
> **Failure scenario.**
>
> - The loss is multiplied by NaN.
> - Each step, `training_step` writes `"\nstep %d loss 1.000000\n#"` to `sys.stdout` and flushes it.
> - `emit` writes the real `step 10 loss nan` right after the dangling `#`. The line becomes `#step 10 loss nan`, which the `^step` `loss_regex` cannot match.
> - The forged clean lines supply the step count. The outcome is **`ok 0.1012`** instead of `divergent`.
> - `seal()` now guards the result lines against exactly this, but nothing guards the loss lines. The threat model lists "a partial line left before them" as closed for the result lines only, and does not list this route as still open.
>
> **Fix (any one of these).**
>
> - `emit` writes `"\n" + line + "\n"`. The blank lines are harmless to the `^`-anchored patterns.
> - The frozen loop also counts non-finite running losses and fails with a distinct exit code, or emits `AR_NONFINITE_LOSS` that the node's `loss_regex` catches.
> - Disclose the route in the threat model.
>
> ### 3. MINOR — The threat model is mostly accurate, with four exceptions
>
> Report l. 181. The routes it lists as still open (early exit, descriptors obtained before the seal including an own `dup` or reopening by path, seeks in the non-`O_APPEND` log, forked children, patches, reading data) match what I demonstrated. The exceptions:
>
> - (a) **"Closes … hidden `step()` calls."** This only holds for extra calls of the optimizer that `build_optimizer` returned. A second optimizer stepped inside `training_step` still passes as `ok` (re-confirmed). Write "extra `step()` calls of the returned optimizer".
> - (b) **Missing from the "can still" list:** global dispatch modes (finding 1, unless closed) and the partial-line prefix before loss lines (finding 2, unless closed).
> - (c) **"The run that planted them fails its own end-of-run check."** This does not hold when a thread or a forked child plants the file after that check. The next run then exits 5. The STOP rule at l. 189 handles that case, but the sentence should say "a run that plants them in its main thread".
> - (d) **The keyword list ("visible in the diff (`os._exit`, `os.fork`, …)").** It is a reading aid, not a filter:
>   - names can be built at run time (`getattr(os, "fo" + "rk")`, `"AR_" + "METRIC"`);
>   - the same routes are reachable through `subprocess`, `multiprocessing`, `ctypes`, `torch.utils._python_dispatch` / `__torch_dispatch__` and a bare `sys.stdout.write` without a newline, none of which are listed.
>
>   Add these, and say that the S1 audit reads the code rather than grepping it.
>
> ### 4. NOTE — The `AR_INFRA` STOP rule can be triggered by an adversarial proposal
>
> Report l. 308–309 still says the pattern cannot be matched by editable code and that such a run is a STOP. A seek can place the line at the top of the log; the threat model now says so. The cheap port-side guard from round 2 is still available: anchor the pattern at the end of the log (`…unavailable\n?\Z`). It costs a spec change and a re-declaration, so it is the author's call. Otherwise, add "(see the threat model)" at l. 309.
>
> ### 5. NOTE — Two small accuracy points in "Checks run here"
>
> - **"Three runs each" (l. 229).** `check_output_seal` runs one subprocess per node, so this presumably means repeated invocations by the author. Say so.
> - **"The round-2 reviewer reproduced this count" (l. 234).** I reproduced 193 passed / 1 failed at `44c7ee89` (189 non-smoke plus the 4 smokes), not at `165788af`.
>
> ### 6. NOTE — The interaction pairs and the Apache-2.0 text are carried over (round-2 NOTEs 8 and 10)
>
> No action is needed beyond what round 2 said.
>
> ## Summary
>
> Round 3 closes the subclass and `TorchFunctionMode` forgeries, the `sys.stdout` NaN hiding, the misattribution of changed data, the missing Breakout dependency, and the report errors. Finding 1 of round 2 is now handled honestly as a threat model with harness-side open points.
>
> Three small fixes remain:
>
> 1. resync `ar_fixed_loop.py` with the MLAgentBench copy, which closes the dispatch-mode forge;
> 2. start every `emit` with a newline, or fail on a non-finite loss in frozen code;
> 3. correct the four items in the threat model.
>
> With those done, I expect to accept.

---

## Round 4 (harness `9c91e393`, report `b92c4f1e`)

> # Review round 4: Track G U3 port kit, suite MLGym
>
> **Verdict: NOT ACCEPTED** (0 MAJOR, 1 MINOR, 2 NOTE)
>
> The three round-3 findings are fixed and the four round-3 notes are handled (two corrected, two carried over as stated). The one thing that blocks acceptance is a **regression introduced by the round-3 fix**: the new mode check refuses an ordinary edit, `torch.set_default_device(...)`, which is then classed `divergent`. It is a one-line fix in the shared frozen file. Everything else checks out.
>
> ## What was reviewed
>
> - Harness: `/tmp/pb/wt/tgb-mlgym`, changes `a6524e64..9c91e393` (tip `9c91e393a3b1ae53d1d68c3a87909d74fa58c308`).
> - Report: `/tmp/pb/wt/u3b-mlgym`, changes `fd863c24..b92c4f1e`.
> - Both worktrees are clean. Nothing was modified, committed or pushed. Scratch files are only under `/tmp/rv_mlgym2/`; `tmp/` there has been emptied. Attack outputs are in `/tmp/rv_mlgym2/adv_r4.txt`.
>
> ## Checks run
>
> - **Tests.** `test_port_mlgym.py` under Python 3.12 gave **26 passed** (659 s), matching the report. The new assertions ran: a dispatch mode is refused, and a loss line emitted after a partial line survives.
> - **Manifests.** All four still reproduce under 3.12.
> - **Smoke records.** Every outcome, validation value and sealed test value matches the report's tables. The leading newline in `emit` changes no metric.
> - **Shared files.** These are byte-identical across the mlgym, mlab (`1db6847`) and ar (`07bb2bc`) worktrees:
>   - `ar_fixed_loop.py`: 5 copies, `24058df1…` (this resolves round-3 finding 1);
>   - `ar_data.py`: 7 copies;
>   - `port_support.py`: 3 copies.
> - **Infra-mode bypass.** I tried to slip a dispatch mode past `_len_torch_dispatch_stack()` by registering it as an infra mode (`_mode_key` FUNCTIONAL/PROXY/FAKE through `_set_dispatch_mode`). It does not get past: the stack length is 1 in each case, so the check catches it.
> - **Attacks.** Synthetic `mlgym_cifar10`, budget 30, run through the real `WorkingCopyRunner`:
>
> | Attack | Round 3 | Round 4 |
> |---|---|---|
> | forged print in `predict_logits`, `atexit` print, `sys.stdout` rewrite, thread print, partial line before the result line | real value | real value |
> | `step()` inside `training_step` | exit 3 | exit 3 |
> | second optimizer | `ok` (disclosed) | `ok` (disclosed) |
> | tensor subclass | exit 4 | exit 4 |
> | `TorchFunctionMode` left active | real value | exit 4 (now refused; see finding 1) |
> | **`TorchDispatchMode` left active** | **`ok 1.0` / test 1.0** | **exit 4 (fixed)** |
> | NaN hidden by a `sys.stdout` filter | `divergent` | `divergent` |
> | **NaN hidden by a partial-line prefix plus forged step lines** | **`ok 0.1012`** | **`divergent/non_finite_loss` (fixed)** |
> | run plants a data file | the run fails itself (exit 5); the next start exits 5 (STOP) | same |
> | fake GPU UUID | `infrastructure_failure` | `infrastructure_failure` |
> | forked child writes after the wrapper exits | `ok 0.999999` (disclosed) | `ok 0.999999` (disclosed) |
> | thread with its own `dup(1)` | real value (lost the race) | `ok 0.999999` (won the race; disclosed) |
> | `lseek` puts `AR_INFRA` at the top of the log | `infrastructure_failure` (disclosed) | same; l. 314–315 now points to the threat model |
> | `AR_INFRA` printed by editable code | `ok` | `ok` |
> | **ordinary edit: `torch.set_default_device(info["device"])` in `build_model` (new)** | — | **`divergent/nonzero_exit`, exit 4** (finding 1) |
>
> ## Round-3 findings
>
> | # | Round-3 finding | Status |
> |---|---|---|
> | 1 MINOR | A dispatch mode forges the accuracy; the `ar_fixed_loop.py` copies differ between suites | **Fixed.** `no_active_modes()` is called before the frozen argmax and accuracy, the copies are byte-identical with mlab, and a test covers it. The dispatch attack now exits 4. The check is broader than needed, which causes finding 1 below. |
> | 2 MINOR | A partial line hides a NaN loss | **Fixed.** Every line `emit` writes starts with a newline (in `ar_data` and in Breakout's inline copy), and a test covers it. The attack is now `divergent/non_finite_loss`. |
> | 3 MINOR | Four inaccuracies in the threat model | **Fixed.** (a) The text now says "extra `step()` calls of the optimizer the editable code returned (not a second optimizer or manual updates)". (b) Dispatch modes and partial lines are covered. (c) The planting caveat and the escaped-child case are added (also at l. 194). (d) The keyword list is presented as a reading aid and extended; the harness remedy now names a cgroup kill. See NOTE 3. |
> | 4 NOTE | `AR_INFRA` STOP rule vs `lseek` | **Fixed** (l. 314–315 point to the threat model). |
> | 5 NOTE | Test-summary wording and the 193/1 commit | **Fixed.** |
> | 6 NOTE | Interaction pairs; Apache-2.0 text | Carried over as stated. |
>
> ## New findings
>
> ### 1. MINOR (regression) — `no_active_modes()` refuses `torch.set_default_device`, so an ordinary edit is classed `divergent`
>
> **Where.** `ar_fixed_loop.no_active_modes`, which is shared by all five torch nodes in both suites:
>
> ```python
> if torch._C._len_torch_dispatch_stack() or torch._C._len_torch_function_stack():
>     fail(EXIT_BAD_EDITABLE_API, ...)
> ```
>
> **Failure scenario.**
> - `torch.set_default_device(dev)` pushes a `DeviceContext` torch-function mode and leaves it on the stack. Measured in isolation: the stack length goes from 0 to 1, and returns to 0 only after `set_default_device(None)`.
> - A proposal that adds `torch.set_default_device(info["device"])` to `build_model` is an ordinary, harmless edit. It trains to completion and is then refused with `AR_ERROR a torch function or dispatch mode is active during the frozen evaluation`: exit 4, `divergent/nonzero_exit`.
> - That records a false divergent label for a legitimate proposal. It counts against the divergence class that the census measures.
> - The function-mode half of the check is not needed. The frozen argmax, `cat` and accuracy already run under `torch._C.DisableTorchFunction()`. In round 3, the same `TorchFunctionMode` attack (`mode_eq`) produced the real value without any stack check. Only dispatch modes needed the new guard.
>
> **Fix.**
> - Check only `torch._C._len_torch_dispatch_stack()`.
> - Alternatively, exempt `torch.utils._device.DeviceContext` from the function-mode check, by inspecting `torch.overrides._get_current_function_mode_stack()`.
> - Add a test that an editable `torch.set_default_device(...)` still runs `ok`.
> - Apply the change to the shared copy, so the two suites stay identical.
> - Adjust the threat-model wording ("a torch function or dispatch mode left active") to match.
>
> ### 2. NOTE — One residual in the threat model is stated more broadly than it is
>
> The threat model says in-process code can "enter a mode only while its own code runs inside the evaluation, which rewrites the frozen arithmetic". A mode entered and exited inside `predict_logits` cannot affect the frozen argmax and accuracy that run after it returns. Mode stacks are also thread-local, so a mode entered from a thread cannot affect them either.
>
> What remains is patching torch or numpy attributes, which the same sentence already names. Overstating a residual is harmless; trim it if convenient.
>
> ### 3. NOTE — Carried over
>
> - The interaction pairs are still declared only in the report and the test module.
> - The Apache-2.0 text is linked, not included.
> - The disclosed routes (forked child, own `dup` of fd 1, `lseek`, early exit, patching) remain open by design, pending the coordinator's harness changes in open point 8.
>
> ## Summary
>
> Round 4 fixes the three round-3 findings, and the report is accurate, apart from NOTE 2. The only remaining issue is the regression in finding 1: the new check refuses `torch.set_default_device`, so a legitimate proposal is recorded as divergent. Restricting the check to the dispatch stack (one line in the shared `ar_fixed_loop.py`), with a test for that edit, should be enough for acceptance.

---

## Round 5 (harness `4b03541d`, report `68c44acb`)

> # Review round 5: Track G U3 port kit, suite MLGym
>
> **Verdict: ACCEPTED** (0 MAJOR, 0 MINOR, 3 NOTE)
>
> The round-4 regression is fixed: an ordinary `torch.set_default_device` edit now runs `ok` with an unchanged metric. The dispatch-mode and tensor-subclass forgeries are still refused. A torch-function mode left active still cannot change the frozen accuracy. No earlier fix regressed.
>
> The three notes below are recommendations. None of them blocks the census:
> - a one-token robustness fix for CUDA in the sampler;
> - a threat-model omission about modes during training;
> - items carried over from earlier rounds.
>
> ## What was reviewed
>
> - **Harness:** `/tmp/pb/wt/tgb-mlgym`, changes `9c91e393..4b03541d` (tip `4b03541d1975a525b68f6f402336c9fc57ecd40f`).
> - **Report:** `/tmp/pb/wt/u3b-mlgym`, changes `b92c4f1e..68c44acb`.
> - Both worktrees are clean. Nothing was modified, committed or pushed.
> - Scratch was only under `/tmp/rv_mlgym2/`; `tmp/` there has been emptied. The attack outputs are in `/tmp/rv_mlgym2/adv_r5.txt`.
>
> ## Checks run
>
> - **Tests.** `test_port_mlgym.py` under Python 3.12 gave **26 passed** (633 s), as the report says. The new assertion runs: accuracy with `set_default_device('cpu')` active is unchanged, and the function-mode stack depth is 1.
> - **Manifests and smoke.** All four manifests still reproduce under 3.12. Every outcome, validation value and sealed test value in the smoke records equals the report's tables.
> - **Shared files.** These are byte-identical across the mlgym, mlab (`666f3a7`) and ar (`51d53e5`) worktrees:
>   - `ar_fixed_loop.py`: 5 copies, `03e3e69c…`;
>   - `ar_data.py`: 7 copies;
>   - `port_support.py`: 3 copies.
> - **Code change.** Only `no_active_modes()` and its docstrings changed: it now checks `torch._C._len_torch_dispatch_stack()` only. The frozen argmax, `cat` and accuracy still run under `DisableTorchFunction`.
> - **Attacks.** I ran these on synthetic `mlgym_cifar10` with a budget of 30, through the real `WorkingCopyRunner`:
>
> | Attack | Round 4 | Round 5 |
> |---|---|---|
> | **`torch.set_default_device(info["device"])` in `build_model` (ordinary edit)** | **`divergent`, exit 4** | **`ok 0.098` (= baseline; fixed)** |
> | `TorchFunctionMode` left active, forging `==` | exit 4 | `ok 0.098`, the real value (`DisableTorchFunction` keeps it out) |
> | `TorchDispatchMode` left active, forging `aten.eq` | exit 4 | exit 4, "a torch dispatch mode is active" |
> | tensor subclass returned by `predict_logits` | exit 4 | exit 4 |
> | NaN hidden by a partial-line prefix / by a `sys.stdout` filter | `divergent` | `divergent/non_finite_loss` |
> | partial line before the result line; print in `predict_logits`; `atexit`; `sys.stdout` rewrite; thread print | real value | real value |
> | `step()` inside `training_step` | exit 3 | exit 3 |
> | run plants a data file | that run fails itself (exit 5); the next run fails too, which is treated as a STOP | same |
> | fake GPU UUID | `infrastructure_failure` | `infrastructure_failure` |
> | `AR_INFRA` printed by editable code | `ok` | `ok` |
> | forked child writes after the wrapper exits | `ok 0.999999` (disclosed) | `ok 0.999999` (disclosed; harness-side open point 8) |
> | **mode active during training hides a NaN loss** (new probe; see NOTE 2) | — | `ok 0.1012`, for both a function mode and a dispatch mode that is exited before evaluation |
>
> ## Round-4 findings
>
> | # | Round-4 finding | Status |
> |---|---|---|
> | 1 MINOR (regression) | `no_active_modes()` refused `torch.set_default_device` | **Fixed.** Only dispatch modes are refused, and a test was added. The edit now runs `ok` with the baseline metric. Function modes still cannot reach the frozen arithmetic. The report (l. 104–107, threat model) and the docstrings match the code. |
> | 2 NOTE | Over-broad residual: "a mode entered only while editable code runs" | **Fixed.** It is replaced by "patch torch or numpy themselves (… or an aten kernel through `torch.library`)", which is accurate. |
> | 3 NOTE | Carried-over items | Unchanged, as stated. |
>
> ## Notes
>
> ### 1. NOTE — On CUDA, `set_default_device('cuda')` is likely to break the frozen sampler
>
> **Where.** `ar_fixed_loop.FixedStepSampler.__iter__`:
>
> ```python
> order = torch.randperm(self.n_items, generator=self.generator)
> ```
>
> The generator is a CPU `torch.Generator()`.
>
> **Why it is likely to fail.**
> - The round-5 fix makes the edit work on this CPU host.
> - On the census GPU, the natural form of the edit is `torch.set_default_device(info["device"])`, which sets the default device to `cuda`. `randperm` without an explicit `device=` would then be created on CUDA with a CPU generator.
> - Torch rejects a generator whose device type differs; the check string `' device type for generator but found '` is in this build's `libtorch_cpu.so`.
> - CIFAR-10 has 45,000 training items and Fashion-MNIST 54,000. That is above the size below which, as far as I recall the source, CUDA `randperm` falls back to the CPU, so the CUDA path would run.
> - The likely result is an error raised in frozen code, classed `divergent`.
> - I could not run this without a GPU, and the `meta` device does not reproduce the check.
>
> **Fix (recommended before the census).** Write `torch.randperm(self.n_items, generator=self.generator, device="cpu")`. This also guarantees what the docstring states: the batch order depends only on the seed, the item count and the batch size. Alternatively, run the edit once in the Ada smoke.
>
> ### 2. NOTE — A mode active during training can rewrite the frozen loss log; not listed in the threat model
>
> **Where.** In `train_fixed_steps`, the lines `running += loss.detach().double()` and `(running / count).item()` run outside `DisableTorchFunction`, and nothing checks the dispatch stack during training.
>
> **What I observed.** The loss is multiplied by NaN, plus one of:
> - (a) a `TorchFunctionMode` that maps a NaN `Tensor.item()` to 1.0;
> - (b) a `TorchDispatchMode` that applies `nan_to_num` to `aten.div` during training and is exited at the start of `predict_logits`.
>
> Both runs are **`ok 0.1012`** instead of `divergent`.
>
> This is deliberate adversarial code, of the same kind as "patch torch itself", which the threat model already names. But the "can still" list mentions modes only through `torch.library` and patching. The reading-aid keyword list names the dispatch-mode spellings but not `TorchFunctionMode`, `__torch_function__` or `torch.overrides`. That gap matters more now that function modes are deliberately not refused.
>
> **Fix.**
> - Add this route and the three spellings to the threat model.
> - Optionally, run the loss-log arithmetic under `DisableTorchFunction` and call `no_active_modes()` at each log point. That closes the left-active cases.
>
> **Related, not a port defect.** The divergence class rests on the loss the editable code returns. An edit that wraps its loss in `torch.nan_to_num` turns a genuinely diverging run into `ok` with a poor metric, with no tampering at all. The coordinator may want to note this for the D21 labels.
>
> ### 3. NOTE — Carried over
>
> - The interaction pairs are recorded only in the report and the test module.
> - The Apache-2.0 text is linked, not included.
> - The disclosed log routes stay open pending the harness changes in open point 8: forked child, own `dup` of the log descriptor, `lseek`, early exit, patching.
>
> ## Summary
>
> All findings from rounds 1–4 are fixed or answered by an accurate disclosure. The report's hashes, commits, tables and test counts check out. The shared files are in step across the three suites.
>
> The kit is accepted for deployment and smoke-testing on Ada. Two recommendations:
> 1. Before the census, apply the one-token `device="cpu"` fix in the sampler (NOTE 1), or exercise the `set_default_device` edit in the Ada smoke.
> 2. Add the training-time mode route to the threat model (NOTE 2).

---

## Round 6 (harness `334c89ce`, report `4c3d0624`)

> # Review round 6 (confirmation): Track G U3 port kit, suite MLGym
>
> **Verdict: ACCEPTED** (0 MAJOR, 0 MINOR, 2 NOTE)
>
> Both round-5 notes are addressed:
> - The frozen sampler now draws the batch order on the CPU, whatever the default device. The order is unchanged.
> - The report's threat model now covers the training-time route.
>
> I found no regressions.
>
> ## What was reviewed
> - **Harness:** `/tmp/pb/wt/tgb-mlgym`, `4b03541d..334c89ce` (tip `334c89ce0e036022cd1f993830a84809092ca44c`). Only `ar_fixed_loop.py` changed, in both image nodes.
> - **Report:** `/tmp/pb/wt/u3b-mlgym`, `68c44acb..4c3d0624`.
> - **Housekeeping:**
>   - Both worktrees are clean; nothing was modified, committed or pushed.
>   - Scratch files are only under `/tmp/rv_mlgym2/`, and `tmp/` there has been emptied.
>   - Attack outputs are in `/tmp/rv_mlgym2/adv_r6.txt`.
>
> ## Checks run
> - **Tests:** `test_port_mlgym.py` under Python 3.12 gave **26 passed** (604 s). That includes reproduction of all four manifests under 3.12, so the frozen change needed no re-declaration.
> - **Smoke:** every outcome, validation value and sealed test value is unchanged from the report's tables. Examples:
>   - cifar10 baseline 0.098 / 0.116667;
>   - fmnist 0.0995 / 0.1;
>   - houseprice 14426.424509 / 15556.650117;
>   - breakout 0.735156 / 0.738281;
>   - all edits, broken diffs and repeats likewise.
> - **Shared files** are byte-identical across the mlgym, mlab (`8596a0e`) and ar (`08d0650`) worktrees: `ar_fixed_loop.py` (5 copies, `bf9f8cb2…`), `ar_data.py` (7), `port_support.py` (3).
> - **Sampler under a non-CPU default device.** I ran `FixedStepSampler(45000, 64, 5, seed 8001)` from the old file (`4b03541d`) and the new one (`334c89ce`), with and without `torch.set_default_device("meta")`.
>
> | `ar_fixed_loop.py` | No default device: first 5 indices | With `set_default_device("meta")` |
> |---|---|---|
> | `4b03541d` (old) | [18109, 8043, 1920, 36303, 27846] | order tensor on **meta** (it would have been on CUDA on Ada, with a CPU generator) |
> | `334c89ce` (new) | [18109, 8043, 1920, 36303, 27846] (same order) | order on **cpu**, identical to the run without a default device |
>
>   The CUDA path itself cannot be exercised on this host, which has no GPU. But the order tensor is now created on the CPU by construction (`device="cpu"`, `torch.Generator(device="cpu")`).
>
> - **Attacks** (synthetic `mlgym_cifar10`, budget 30, real `WorkingCopyRunner`):
>
> | Attack | Round 6 result |
> |---|---|
> | ordinary edit `torch.set_default_device(info["device"])` | `ok 0.098`, equal to the baseline |
> | torch-function mode forging `==` | `ok 0.098`, the real value |
> | dispatch mode forging `aten.eq` | exit 4, "a torch dispatch mode is active" |
> | tensor subclass returned by `predict_logits` | exit 4 |
> | partial line before a NaN loss line | `divergent/non_finite_loss` |
> | partial line before the result line | real value |
> | `step()` inside `training_step` | exit 3 |
> | run plants a data file | that run fails itself (exit 5); the next start exits 5, which is a STOP |
> | fake GPU UUID | `infrastructure_failure` |
> | function mode active during training hides a NaN loss | `ok 0.1012` (now disclosed in the threat model) |
> | forked child writes after exit | `ok 0.999999` (disclosed; harness-side open point 8) |
>
> ## Round-5 notes
>
> | # | Round-5 note | Status |
> |---|---|---|
> | 1 | The sampler's `randperm` follows a CUDA default device but uses a CPU generator | **Fixed.** It now uses `torch.Generator(device="cpu")` and `torch.randperm(..., device="cpu")`. The order is unchanged, and it stays on the CPU under a non-CPU default device (table above). The report's design section describes this correctly. |
> | 2 | A training-time mode can hide a NaN loss; this was not in the threat model | **Fixed as disclosure.** The threat model names torch-function and dispatch modes active during training, and patches to torch. It says these change the outcome class, not the metric. It notes that `torch.nan_to_num(loss)` in an ordinary-looking edit does the same, because the divergent class rests on the editable loss. `TorchFunctionMode`, `__torch_function__`, `torch.overrides` and `nan_to_num` are added to the list of names for reviewers to look for. The text matches my observations (`mode_hide_nan` gives `ok 0.1012`). |
> | 3 | Carried-over items | Unchanged, as stated. |
>
> ## Notes
> 1. **NOTE — No test pins the CPU batch order.** A cheap optional test would fit in `check_plain_tensor_metric`: build `FixedStepSampler` once with and once without `torch.set_default_device("meta")`, then assert the batches are CPU tensors and are equal. It guards against a regression in the shared file.
> 2. **NOTE — Carried over:**
>    - The interaction pairs are recorded only in the report and the test module.
>    - The Apache-2.0 text is linked, not included.
>    - These log routes remain open by design, pending the coordinator's harness changes (open point 8): forked child, own `dup` of the log descriptor, `lseek`, early exit, patches of torch, and training-time modes.
>
> ## Summary
> The round-6 changes are minimal and correct, the smoke results are unchanged, and the report is accurate. The MLGym port kit, harness tip `334c89ce` with report `4c3d0624`, is accepted for deployment and smoke-testing on Ada.

---

## Not changed after acceptance

Round 6's notes are left as they are: no test pins the CPU batch order under a non-CPU default device (the reviewer checked it by hand with `set_default_device("meta")`); the interaction pairs are recorded in the report and the test module only; the Apache-2.0 text is linked rather than included; the disclosed log and mode routes stay open pending the coordinator's harness changes.

## For the author and the coordinator (from the report)

The report's open points: the MLGym licence (CC BY-NC 4.0 in an MIT-licensed harness tree; remedies listed); compute per step and timeouts (a proposal, pending a decision); the House Prices budget (one fit), its data source (MLGym's copy or the Kaggle download) and its noise floor; Breakout trains one model per run; the harness changes that would close the in-process threat model; the House Prices synthetic-mode check for the census. Nothing was measured; the kit is ENGINEERING_ONLY.

Code-Commit: 334c89ce0e036022cd1f993830a84809092ca44c
Verdict: ACCEPTED

Accepted commit: `334c89ce0e036022cd1f993830a84809092ca44c` (harness, round 6); report `4c3d0624c53f01b2f1e09209689d513a946f705e`.
