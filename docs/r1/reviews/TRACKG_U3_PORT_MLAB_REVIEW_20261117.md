Reviewed base: `1db684711bf868a85ddb243dc18b88c4daf6a506` (harness branch `mac-trackg-port-mlab-20261117b`; report at `8bce3ccd1280d8c2bb8c84c198129c1231f3903e` on `mac-trackg-u3-mlab-20261117b`; accepted in round 6)

# Independent review record — Track G U3 port kit, suite MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)

**Unit.** The port kit for the three MLAgentBench T1 candidates of the Ada census plan: `nodes/mlab_*/`, `configs/trackg/nodes/mlab_*.yaml`, `tests/trackg/test_port_mlagentbench.py` and the shared `tests/trackg/port_support.py` / `port_smoke_gpu.py` on the harness branch (base `717ad835`), and on the paper branch (base `main` `26177d82`) the port checklist's section F (`b715e110`, moved after section E) and the report `docs/r1/reports/TRACKG_U3_PORT_MLAB_20261117.md`. Round 1 reviewed the first harness branch `mac-trackg-port-mlab-20261117` (tip `fbecd13e`) and report branch `mac-trackg-u3-mlab-20261117` (`32a869c7`); the `…b` branches continue from them.

**Authority.** R1-TRACKG-PORT-OWNER and R1-TRACKG-LICENCES (`main` `26177d82`; `author-decisions-20261117b` @
`33c82351`); the user's queue of 17 Nov (item 4) on `author-decisions-20261117b` @ `45fb94cc`.

**Process.** Two independent reviewers (separate agents that did not write the code): one for round 1, one for rounds 2–6. Rounds 3–6 also reviewed changes shared with the autoresearch and MLGym kits after their reviews. The reviewers edited, committed and pushed nothing. The round texts are reproduced below
as delivered, as block quotes, so that only this record's closing lines are read as the acceptance.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | harness `fbecd13e`, report `32a869c7` | NOT ACCEPTED (4 major, 7 minor) |
| 2 | harness `b77e68a9`, report `0a9d6b8b` | ACCEPTED (4 minor, 4 notes) |
| 3 | harness `4659b837`, report `6cfa8cb4` | NOT ACCEPTED (1 major, 1 minor, 2 notes) |
| 4 | harness `b6345961`, report `bbd74de5` | NOT ACCEPTED (2 major, 1 minor) |
| 5 | harness `5563fa38`, report `91ca9a96` | ACCEPTED (2 minor, 1 note, text) |
| 6 | harness `1db68471`, report `8bce3ccd` | ACCEPTED (1 note) |

---

## Round 1 (harness `fbecd13e`, report `32a869c7`)

> Review: Track G U3 port kit for MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
> Harness branch mac-trackg-port-mlab-20261117 @ fbecd13e (base 717ad835). Report TRACKG_U3_PORT_MLAB_20261117.md @ 32a869c7 (branch mac-trackg-u3-mlab-20261117).
> Reviewer: an independent agent (Claude). I edited, committed and pushed nothing. Scratch files are only under /tmp/rv_mlab/. Running pytest may have written git-ignored `__pycache__` files in /tmp/pb/wt/tg-mlab and /tmp/pb/wt/tgv2.
>
> ## What I ran
> - Static tests, Python 3.13 (/tmp/trackg_venv): 9 passed, 3 skipped (the smoke tests).
> - Static tests, Python 3.12 (/tmp/tgport312): 9 passed.
> - Synthetic smoke for all three nodes, Python 3.12: 3 passed (208 s).
> - Whole `tests/trackg` directory, Python 3.13: 182 passed, 3 skipped. This matches the report.
> - Whole directory, Python 3.12: only `test_trackg_t0_identity::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit` fails. It also fails on the unchanged pin at /tmp/pb/wt/tgv2. This matches the report.
> - My own checks:
>   - every pair of declared edits applied in sequence with the harness `apply_diff`;
>   - a copy of the kit with `data` links in place, as they will be after setup;
>   - a demonstration of an edit that makes hidden optimizer updates;
>   - a check of DistilBERT parameter names.
>
> ## What checks out
> - **Specs (checklist A).**
>   - All three load in the strict loader.
>   - `editable_paths` is only `train.py`. `frozen_paths` covers the wrapper, `ar_fixed_loop.py`, `ar_data.py`, `prepare_data.py`, `requirements.txt`, `NOTICE.md`, `data/` and `representative_edits/`.
>   - Every committed file is in one of the two scopes. `allow_new_files` is false, so nothing can shadow a frozen import.
>   - `metric_regex` and `test_metric_regex` are anchored on `^AR_METRIC` and `^AR_TEST`.
>   - `loss_regex` and `steps_regex` match the frozen `step <n> loss <x>` lines. A NaN prints as `nan` and is caught.
>   - Selection is test-scored and on validation only. Determinism is at the defaults. `seed_env` is `AR_TRAIN_SEED` / `AR_SPLIT_SEED`. The budget is `kind: steps`, with no time words.
> - **Wrappers (checklist B).**
>   - `ar_fixed_loop.py` and `ar_data.py` are byte-identical across the three nodes, and across the MLGym and autoresearch branches too.
>   - `--steps` is checked against `AR_BUDGET_VALUE` and `AR_BUDGET_KIND`.
>   - The batch order is a seeded permutation that drops the last incomplete batch. The run fails if the step count falls short.
>   - Seeds are set before `train` is imported.
>   - The metric and test lines are printed only by the frozen wrapper, after training, validation first.
>   - Nothing sets `cudnn.benchmark`.
>   - Every run checks every data file's size and sha256 against the manifest.
>   - Data preparation is a one-off `setup_command` that writes outside the node and links it in as `data`.
> - **Splits.**
>   - cifar10: 45,000 / 5,000 by `np.random.RandomState(split_seed)`, with the suite's 10,000 test images sealed.
>   - imdb: 22,500 / 2,500 with 25,000 sealed.
>   - ogbn: the official split, with validation and test labels masked to -1 in `info`.
>   - Evaluation is plain argmax accuracy over the whole set. That is what the suites' `eval.py` scripts compute (suite cifar10 `eval.py` uses all 10,000 images; the ogbn Evaluator `acc` is the same).
> - **Fidelity, cifar10.** The LeNet, SGD (0.1, momentum 0.9), batch 128, cross-entropy and normalisation by 0.5/0.5 match the suite (`benchmarks/cifar10/env/train.py:8-48`). 1,950 steps equals the suite's 5 × 390. Over the 45k training split this is about 5.6 epochs; the step count is stated correctly.
> - **Fidelity, ogbn.** The MLP (hidden 16, batch norm, dropout 0), Adam at lr 1, batch 1,024 and the scheduler that is never stepped all match the suite (`ogbn-arxiv/env/train.py:76-82`). The change from 172 to 40 outputs is stated.
> - **Fidelity, imdb.** The suite's `train.py` is a skeleton with `model = None` (`imdb/env/train.py:11`), so the port-written baseline is justified. It is raised as open point 1.
> - **Edits (checklist C).**
>   - 4 per node, all in scope. They apply to the baseline, are not inert and do not duplicate one another.
>   - The manifests are complete and were committed in 6cf1f2f8, the first commit, before any run.
>   - Every sha256 in the report (3 manifests, 12 edits) matches the files. All commit SHAs, the base, the suite commit and date, and "adds files only" check out.
>   - Re-declaring the edits reproduces the manifests byte for byte under 3.12. Under 3.13 only the three AST-based hashes differ, as the report says.
> - **Smoke.** My cifar10 and ogbn smoke numbers match the report's tables exactly. The frozen-path diff is refused (`scope_violation`), the broken diff is `discarded_divergent` with `non_finite_loss`, the repeated baseline gives the same metric, and `not_forced` is `["dataloader_workers"]`.
> - **Licence.** The suite's `LICENSE` is the unfilled MIT template, as the report says.
>
> ## Findings
>
> **1. MAJOR — The documented deployment order makes the port tests fail.**
> - The report's Deployment section runs `setup_command` at step 3 (line 225), which creates `nodes/<node>/data`. It then runs the static tests at step 4 (line 226).
> - Three things then break:
>   - `tests/trackg/port_support.py:112` asserts `not (base / "data").exists()`.
>   - `frozen_files` (`port_support.py:74-77`) walks into the linked `data/`. `check_scope` then calls `read_text` on `.npy` files (`port_support.py:188`) and raises `UnicodeDecodeError`.
>   - `smoke_copy` (`port_support.py:219`) copies with `symlinks=False`. That copies the whole data directory as a real folder, and `link_data` then refuses with "exists and is not a link" (`ar_data.py:86-87`).
> - Reproduced in a copy with data links in place: 3 of 3 `test_static` fail, and `test_frozen_path_edit_refused[mlab_cifar10]` fails with `UnicodeDecodeError`.
> - **Fix:**
>   - Make the support module accept a symlinked `data`: skip it in the exists and stray-file checks, leave symlinked directories out of `frozen_files`, and copy with `symlinks=True` while ignoring `data` in `smoke_copy`.
>   - Put the static tests before setup in the deployment steps.
>   - Re-run the tests with links present.
>
> **2. MAJOR — Budget enforcement is overclaimed. An edit can make hidden optimizer updates and still score `ok`.**
> - The report says (line 92) "not the loop itself (no gradient accumulation, EMA or custom loops)… The budget therefore cannot be bypassed."
> - But `training_step` (called at `ar_fixed_loop.py:147-148`) is arbitrary code that receives the model. It can keep the optimizer it built in `build_optimizer` and step it, or return a custom optimizer whose `step()` makes k updates. EMA is also possible: a shadow copy updated in `training_step` and used in `predict_logits`.
> - Demonstrated on a scratch copy of mlab_cifar10: an edit that made 3 extra updates per counted step gave 80 updates in a 20-step run. The log was normal (`AR_STEPS completed=20`, `AR_METRIC …`), and the outcome would be `ok`.
> - This needs no adversarial intent. "Several passes per batch" or a SAM- or Lookahead-style optimizer are ordinary proposals, and they are "train longer" in disguise.
> - **Fix:**
>   - Count optimizer steps with `optimizer.register_step_post_hook` in `train_fixed_steps`, and fail with `EXIT_BUDGET_NOT_REACHED` (or a new code) if the count is not exactly the budget.
>   - Correct the report: the loop fixes the batches drawn and the updates it drives. In-process editable code can still change parameters by hand, patch `ar_fixed_loop`, forge lines, and read `data/*.npy` (including test labels; the ogbn masking to -1 is not a barrier). List these together as known limits for the coordinator.
>
> **3. MAJOR — ogbn-arxiv baseline: two real deviations from the suite are not stated.**
> - (a) Batch norm statistics:
>   - The suite trains the MLP on `batch.x` of a `NeighborLoader` subgraph, two hops with 30 neighbours each (`ogbn-arxiv/env/train.py:23-25, 119-120`). Its batch norm statistics and running stats therefore come from the 1,024 seed nodes plus their sampled neighbours, mostly non-training nodes.
>   - The port's batch norm sees only the 1,024 training seeds (`nodes/mlab_ogbn_arxiv/train.py:41-45`; batch `{"idx": tr_idx[pos]}` at `run_fixed_budget.py:65`).
>   - With Adam at lr 1, this changes training behaviour.
> - (b) Epoch structure:
>   - The suite's loader keeps the last partial batch: 89 batches per epoch, the last of 829 nodes.
>   - The port drops it (`ar_fixed_loop.py:125-132`): 88 full batches per epoch. 356 steps is then about 4.05 epochs of full batches, not "4 epochs × 89 batches" (report line 43).
> - The `train.py` docstring, `NOTICE.md` ("see its docstring for every difference") and the report name only the change from 172 to 40 outputs.
> - **Fix:** state both deviations in the report, `NOTICE.md` and the yaml description, or reproduce the suite's behaviour. If `train.py`'s docstring changes, re-declare and recommit the manifest; nothing is measured yet.
>
> **4. MAJOR — No pair of ogbn's declared edits can be combined, and no ogbn edit is likely to diverge.**
> - I applied each pair in sequence with the harness `apply_diff`. For ogbn, all 6 pairs are refused: every edit changes, or has as diff context, the same lines `HIDDEN` / `NUM_LAYERS` / `DROPOUT` / `LEARNING_RATE` (`train.py:23-26`).
> - For imdb, 3 of 6 pairs are refused: E1+E2, E1+E4 and E2+E4. E4's hunk includes the `LEARNING_RATE` line as context. cifar10 composes everywhere except E1+E4.
> - Checklist C.1, fourth bullet, asks for an edit likely to diverge or to interact with another, for S1.1. The plan runs S1.1 "on each T1 node" (`TRACK_G_RUNBOOK.md:95`). ogbn has neither kind of edit, and the report does not mention this.
> - The edits are frozen once measurement starts, so this has to be fixed now.
> - **Fix:**
>   - Rewrite ogbn's edits so that at least one interacting pair applies cleanly. For example, move `LEARNING_RATE` at least 4 lines away from the architecture constants in the baseline, or re-cut E3/E4 so their context avoids the LR line.
>   - Optionally add a likely-divergent edit.
>   - Re-declare, recommit, and add a pair-composability table to the report.
> - If S1.1 combines diffs by some other mechanism, say so in the report, and this finding drops to MINOR.
>
> **5. MINOR — Factual errors in the report.**
> - Line 3 says the kits "were independently reviewed (see `docs/r1/reviews/TRACKG_U3_PORT_MLAB_REVIEW_20261117.md`)". That file does not exist, and the report's own commit message says "Independent review pending".
> - Line 67 cites `declare_edits_output.txt` "kept with the bundle". No such file exists anywhere on the host.
> - The yaml states ogbn-arxiv's licence as ODC-BY as a fact (`mlab_ogbn_arxiv.yaml:80`), while the report says "to confirm" (line 213).
> - `NOTICE.md` writes "Copyright (c) the MLAgentBench authors", but the `LICENSE` holds the unfilled placeholder.
> - **Fix:** set "Review: pending" until a review is committed, then cite its verdict. Commit the declare-edits output or drop the reference. Align the licence wording.
>
> **6. MINOR — imdb's weight-decay description is wrong for DistilBERT.**
> - The filter `n.endswith(("bias", "LayerNorm.weight"))` (`nodes/mlab_imdb/train.py:32-36`) excludes only `embeddings.LayerNorm.weight`.
> - Every block's `sa_layer_norm.weight` and `output_layer_norm.weight` is decayed. I checked the parameter names with transformers 4.49.
> - The report (line 35), the docstring and the yaml all say "except on biases and LayerNorm".
> - **Fix:** correct the text, or fix the filter (for example `"norm" in n.lower()`) and re-declare.
>
> **7. MINOR — Run length and timeouts: an open point that should go to the author.**
> - cifar10 and ogbn runs take seconds, against R1-BX-D5's 1–2 minutes (report lines 29, 142). Start-up and data hashing dominate, so a timeout of 3× the measured run time is fragile on a shared Ada host.
> - The batch-size caps let a one-line hyperparameter edit multiply compute: cifar 4,096 is 32× the baseline, ogbn 90,941 (full batch) is 89×, imdb 128 is 8×.
> - A timeout is classified as `infrastructure_failure` (`outcome.py:136-137`). Such runs are rerun rather than deduplicated.
> - The checklist fixes the budget before the census.
> - **Fix:** list this under the report's open points for the author: keep the suite length or scale up toward the guideline. Consider tighter caps.
>
> **8. MINOR — A silent CPU fallback could mislead the census-host smoke.**
> - `pick_device` (`ar_fixed_loop.py:90-94`) quietly uses the CPU when CUDA is unavailable. The census plan §4.2 says "OOM/CPU fallback = STOP".
> - The test helper `limits()` (`port_support.py:237-240`) passes no GPU UUIDs, so the runner sets `CUDA_VISIBLE_DEVICES=""`, as seen in the smoke run records.
> - If the experiment agent reuses `ps.run_smoke` on Ada, which is the obvious route because Deployment step 5 (line 227) gives no driver, the runs go to the CPU and still pass.
> - **Fix:**
>   - Have the wrapper exit with a fixed message, added to `infrastructure_log_patterns`, when `CUDA_VISIBLE_DEVICES` is non-empty but CUDA is unavailable. A proposal cannot cause this, because `train` is imported after `pick_device`.
>   - Ship a GPU smoke command or driver that takes UUIDs.
>
> **9. MINOR — The shared data directory can be written by editable code during a run.**
> - Runs reach the data through an absolute link, and the editable code runs in the wrapper's process.
> - A proposal that writes into `data/` either breaks every later run or carries state from run to run:
>   - Changing a listed file makes verification exit with code 5, which is classified `divergent` / `nonzero_exit` (`ar_data.py:68-72`).
>   - Extra files are not checked, so cached files carry over between runs.
> - **Fix:** have `prepare_data.py` make the output directory read-only once the manifest is written, and document this.
>
> **10. MINOR — The imdb synthetic smoke is not reproducible.**
> - `imdb_data` builds the tiny `DistilBertModel(config)` without a seed (`tests/trackg/test_port_mlagentbench.py:55-57`).
> - My rerun gave a baseline of 0.4948 with test 0.505. The report's table (lines 179, 183) has 0.4956 and 0.46.
> - **Fix:** call `torch.manual_seed(0)` before building the model, or note that the imdb table varies between runs.
>
> **11. MINOR — Setup robustness. `prepare_data.py` was never exercised, as the report itself says.**
> - ogb 1.3.6 reloads its processed file with `torch.load` (`ogb/nodeproppred/dataset.py:70`). Under torch 2.6, which defaults to `weights_only=True`, this fails if setup is retried after a partial run. It also calls `input()` if the directory exists without a RELEASE file.
> - torchvision, ogb and datasets are unpinned. torchvision must be 0.21.x to match `torch==2.6.0`; installed separately, it upgrades torch.
> - **Fix:**
>   - Pin `torchvision==0.21.0` and `ogb==1.3.6`.
>   - Have `prepare_data.py` start from an empty raw directory, or use `weights_only=False` for that one load.
>   - Install the three requirements files in one resolver call.
>
> ## Summary
> The kit is carefully built. Specs, scopes, manifests, hashes and the frozen-path refusal all check out, and the tests pass in both environments. Four MAJOR findings remain:
> - the deployment steps as written make the port tests fail (1);
> - the step budget is not enforced against updates made inside `training_step`, while the report says it cannot be bypassed (2);
> - two undisclosed deviations in the ogbn baseline (3);
> - ogbn's declared edits contain no pair that can be combined, which S1.1 needs (4).
>
> Findings 3 and 4 touch `train.py` or the edits, so the manifests must be re-declared and recommitted before any measurement.
>
> VERDICT: NOT ACCEPTED

---

## Round 2 (harness `b77e68a9`, report `0a9d6b8b`)

> # Review round 2: Track G U3 port kit, MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
>
> - **Harness branch:** `mac-trackg-port-mlab-20261117b` @ `b77e68a9971c789fbd550d0a2d0e56d4e94a01fd`. Base `717ad835`; round-1 tip `fbecd13`.
> - **Paper branch:** `mac-trackg-u3-mlab-20261117b`. Commits `b715e110` (checklist section F) and `0a9d6b8b` (report `docs/r1/reports/TRACKG_U3_PORT_MLAB_20261117.md`).
> - **Reviewer:** an independent agent (Claude), round 2.
> - **What I touched:** no repository was modified, committed or pushed. Scratch was only in `/tmp/rv_mlab2/`.
> - **Side effect:** the first pytest run, as specified, wrote git-ignored `__pycache__/` folders into `/tmp/pb/wt/tgb-mlab` (`nodes/mlab_*`, `src/autoresearch/**`, `tests/trackg`). I did not delete them, because they are outside my scratch area.
>
> ## Verdict: ACCEPTED
>
> All 11 round-1 findings are fixed. Finding 7 is correctly raised as open point 2.
>
> No new BLOCKING or MAJOR problem was found. The new findings are four MINOR and four NOTE. They need corrections to the report (and to one docstring), but no change to the edits, specs or manifests, so nothing needs re-declaring. I recommend fixing them in the report before the bundle is filed.
>
> ## What I ran
>
> **1. Port tests.** `tests/trackg/test_port_mlagentbench.py` (Python 3.12, torch 2.6.0 CPU, `TMPDIR=/tmp/rv_mlab2/tmp`): **15 passed** in 209 s. This matches the report.
>
> **2. Whole `tests/trackg` directory.** 187 passed, 1 failed. The failure is `test_trackg_t0_identity::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`, the known environment failure that round 1 also saw on the unchanged base. This matches the report.
>
> **3. Tests with `data` links in place (round-1 finding 1).** I made a `git archive` copy of the tip and linked synthetic data in as `nodes/*/data` for all three nodes. Static, manifest, scope and composability tests plus the cifar10 smoke: **13 passed**.
>
> **4. Hashes and composability.** I recomputed the sha256 of all 3 manifests and all 12 edits. Every value matches the report. I applied all 36 ordered pairs with the harness `apply_diff`, and the result matches the report's composability table exactly.
>
> **5. Smoke table.** I took the numbers from my test run's run records. All 27 rows of the three tables match the report exactly, including imdb, which is now seeded. The values I compared are outcome, reason, validation, test and `not_forced`.
>
> **6. Hidden-update demos.** I ran variants of `train.py` against the new optimizer step hook (mlab_cifar10, synthetic data, 20 steps). Each log was classified with the harness `classify_run` and the node's patterns (table below).
>
> **7. The `AR_INFRA` pattern.**
> - The real wrapper, run with `CUDA_VISIBLE_DEVICES=GPU-deadbeef` on a host without CUDA, gives `infrastructure_failure/infrastructure_log_pattern`, exit 6.
> - The same line printed after `AR_DEVICE` is classified `divergent/nonzero_exit`.
>
> **8. Reading checks.**
> - `prepare_data.py` for all three nodes, against the ogb 1.3.6 source in `/tmp/rv_mlab/dl/ogbsrc`.
> - Licence facts in `LICENCES.md` against U1 (`gh/ops-tasl-20261116`) and the suite checkout (`/tmp/suites/MLAgentBench` @ `5d71205c`, `LICENSE` unfilled template).
> - The PLAN rows on `gh/author-decisions-20261117b`:
>   - `R1-TRACKG-LICENCES` is at `33c82351`, an ancestor of the current tip `45fb94cc`;
>   - `R1-TRACKG-PORT-OWNER` is on `26177d82`.
> - Commit `b715e110` is identical on the autoresearch paper branch.
> - `ar_fixed_loop.py`, `ar_data.py`, `port_support.py` and `port_smoke_gpu.py` are byte-identical across the MLAB, MLGym and autoresearch branches, where each file exists.
> - The DistilBERT parameter names under transformers 4.49 (finding 6).
>
> ### Hidden-update and adversarial variants (cifar10, 20 steps)
>
> | Variant of `train.py` | Exit | Harness outcome |
> |---|---|---|
> | A. Round-1 demo: 3 extra `OPT.step()` calls in `training_step` | 3 | divergent / nonzero_exit ("the optimizer stepped 80 times for a budget of 20") |
> | B. `SGD` subclass whose single `step()` makes 4 manual updates | 0 | **ok** |
> | C. Clear `OPT._optimizer_step_post_hooks`, step 3×, restore | 0 | **ok** |
> | D. `type(OPT).step.__wrapped__(OPT)` 3× in `training_step` | 0 | **ok** |
> | E. Editable code prints the exact `AR_INFRA` line during training, exits 6 | 6 | divergent / nonzero_exit (correctly not infrastructure) |
> | E2. Same line to stderr at import time, exits 6 | 6 | divergent / nonzero_exit (`AR_DEVICE` precedes it) |
> | F. Editable code prints `No space left on device`, exits 1 | 1 | **infrastructure_failure** (harness default pattern) |
> | G. Subclass `K(SGD)` whose `step()` returns `super().step()`, after a throwaway `SGD` instance was created | 3 | divergent ("stepped 40 times for a budget of 20") |
> | G2. Same subclass, with no prior `SGD` instance | 0 | ok |
> | I. Baseline | 0 | ok |
>
> ## Round-1 findings
>
> | # | Sev. | Round-1 finding | Status | Evidence |
> |---|---|---|---|---|
> | 1 | MAJOR | Deployment order makes the port tests fail when `data` links exist | **Fixed** | `frozen_files` skips the symlink, and `committed_files` ignores the linked `data/`. `smoke_copy` and `composable_pairs` copy with `symlinks=True` and ignore `data`. 13/13 pass on a copy with links. The Deployment section puts the static tests before setup. |
> | 2 | MAJOR | Hidden optimizer updates still score `ok`; budget overclaimed | **Fixed** (residue in new 1) | The `isinstance(..., torch.optim.Optimizer)` check plus `register_step_post_hook` refuse the round-1 demo (A). The report drops "cannot be bypassed" and lists the known limits. Variants B, C and D still pass; B is not explicitly in the limits list (new finding 1). |
> | 3 | MAJOR | ogbn: undisclosed batch-norm and partial-batch deviations | **Fixed** | Both are stated in the `train.py` docstring, `LICENCES.md`, the yaml `description` and the report. The 4.05-epoch figure checks out: 90,941 = 88×1,024 + 829. |
> | 4 | MAJOR | No ogbn pair composes; S1.1 has no interaction pair | **Fixed** (residue in new 2) | `LEARNING_RATE` moved next to `build_optimizer`. ogbn E1+E3, E2+E3 and E3+E4 compose in both orders, and a new test checks the listed pairs. Two of the six pairs the report names for S1.1 are behaviourally inert (new finding 2), but genuine pairs remain for every node. |
> | 5 | MINOR | Report factual errors (review file, declare-edits output, licence wording, NOTICE copyright) | **Fixed** | Review reference: "once filed". The `declare_edits_output.txt` reference is gone. The yaml says ODC-BY "as OGB's page states, per U1 §4". `NOTICE.md` is replaced by `LICENCES.md`, which records the unfilled copyright template. |
> | 6 | MINOR | imdb weight-decay filter misses `sa_layer_norm` and `output_layer_norm` | **Fixed** | The filter now includes `"layer_norm.weight"`. Checked: the no-decay group is exactly `embeddings.LayerNorm.weight` and each block's `sa_layer_norm.weight` and `output_layer_norm.weight`, plus the biases. |
> | 7 | MINOR | Run length, timeouts and batch-size caps: an open point for the author | **Raised correctly** as open point 2 | One sentence in it oversteps (new finding 3). |
> | 8 | MINOR | Silent CPU fallback | **Fixed** | `pick_device` prints `AR_INFRA` and exits 6 before `train` is imported. The node pattern matches only when no `AR_DEVICE` line precedes it (verified both ways). `port_smoke_gpu.py` takes `--gpu-uuid`. See NOTE 7. |
> | 9 | MINOR | Shared data writable by editable code | **Fixed as asked** (claim too strong; new finding 4) | `ar_data.make_read_only` runs after the manifest is written. |
> | 10 | MINOR | imdb smoke not reproducible | **Fixed** | `torch.manual_seed(0)` before the tiny DistilBERT. My rerun reproduces the report's imdb rows exactly. |
> | 11 | MINOR | Setup robustness: pins, `torch.load` / `input()` on retry, resolver | **Fixed** | Pinned `torchvision==0.21.0`, `ogb==1.3.6` and `huggingface_hub==0.36.2`. A first run refuses a non-empty `--out` without a manifest, so ogb starts from a fresh root and never reaches its `input()` prompt or the `torch.load` of the processed file. Each `requirements.txt` says to install in one resolver call. Also added: the CIFAR md5 must equal the published `c58f3010…`; the imdb revision must start with U1's `e628166` unless the author passes `--accept-dataset-revision`; `--out` must lie under `$AR_TRACKG_DATA_ROOT`. |
>
> ## New findings
>
> ### 1. MINOR: one bypass class of the step hook is left out of the limits list, and the docstring claims more than holds
>
> **Location:**
> - `nodes/*/ar_fixed_loop.py`, `train_fixed_steps` docstring: "so editable code cannot add hidden steps of that optimizer".
> - Report, "Budget enforcement and its limits".
>
> **Failure scenario.**
> - The hook counts `step()` calls, not updates. Variant B, an `Optimizer` subclass whose single `step()` makes 4 updates, runs `ok` with `AR_STEPS completed=20`. This is the "custom optimizer whose `step()` makes k updates" that round 1 named explicitly.
> - The report's not-enforced list mentions "SAM- or Lookahead-style updates that do not go through the counted `step()`". A Lookahead or SAM optimizer written as the returned optimizer *does* go through the counted `step()`, and is still not caught. The list therefore describes the case the wrong way round.
> - Variants C (hiding the hooks) and D (calling `step.__wrapped__`) also pass. They are deliberate tampering with the optimizer's internals, which is close to "patching".
>
> **Fix.**
> - Add "an optimizer (or subclass) whose single `step()` makes several updates, e.g. Lookahead or SAM implemented inside `step()`" and "tampering with the optimizer's hook registry" to the not-enforced list in the report and the docstring.
> - Change "cannot add hidden steps" to "cannot add extra `step()` calls". This is a frozen-file docstring, so only the comment changes, and no manifest hash covers `ar_fixed_loop.py` contents beyond the spec. Alternatively, fix only the report.
>
> ### 2. MINOR: two of the six pairs named "interacting pairs for S1.1" are behaviourally inert
>
> **Location:**
> - Report, "Pair composability": "The interacting pairs for S1.1 are ogbn E1+E3 (learning rate × capacity) and E3+E4, imdb E1+E4 and E3+E4, cifar10 E1+E3 and E2+E3".
> - `tests/trackg/test_port_mlagentbench.py::INTERACTING`.
>
> **Failure scenario.**
> - **cifar10 E1+E3.** E3 replaces `SGD(lr=LEARNING_RATE)` with `Adam(lr=1e-3)`, so E1's `LEARNING_RATE = 0.05` is dead code.
> - **ogbn E3+E4.** E4's `build_model` constructs `SAGE(..., 128, ..., 0.5)` with hard-coded width and dropout, so E3's `HIDDEN`, `NUM_LAYERS` and `DROPOUT` are dead code.
> - I ran both on synthetic data (20 steps, seed 3). E1+E3 and E3 alone are identical to the last digit: loss 2.284024, val 0.1002, test 0.093333. cifar E4+E3 is also identical. E3+E4 and E4 alone are identical: loss 1.771162, val 0.0225, test 0.0175.
> - The diffs differ, so the code-state hashes differ and the harness will not deduplicate them. An S1.1 interaction run on these pairs would cost a run and report a spurious "E3 has no effect given E4" (or "E1 none given E3") interaction.
> - Genuine composing pairs remain:
>   - cifar10: E1+E2, E2+E3, E2+E4;
>   - ogbn: E1+E3, E2+E3;
>   - imdb: all five listed.
> - So the substance of round-1 finding 4 is met.
>
> **Fix.**
> - In the report, name only behaviourally active pairs for S1.1: for example cifar10 E2+E3 and E1+E2, ogbn E1+E3 and E2+E3, imdb as stated.
> - Mark cifar10 E1+E3 and E3+E4, and ogbn E3+E4, as "apply cleanly but one edit is inert after the other".
> - Optionally split `INTERACTING` in the test the same way. Neither the edits nor the manifests need to change.
>
> ### 3. MINOR: open point 2 sets an interim outcome rule that the harness does not implement and the port has no authority to set
>
> **Location:** report, open point 2: "Until you decide, **an over-compute timeout on these nodes is not an infrastructure failure** and is read as the proposal's cost, not re-run."
>
> **Failure scenario.**
> - `outcome.classify_run` classifies every timeout as `infrastructure_failure/timeout` before anything else (`src/autoresearch/trackg/outcome.py:126-127`). No per-node override exists: only `kill_exit_codes` and log patterns are configurable.
> - So the census records will say `infrastructure_failure`, and the campaign logic re-runs those runs.
> - A coordinator who reads the report will assume a rule that nothing applies. Changing outcome classes also belongs to the R1-BX outcome rules (REVISIONS (c)), not to a port report.
>
> **Fix.** Phrase it as a proposal for the author, for example: "Proposed, pending your decision: … The harness currently classes such a timeout as `infrastructure_failure` and re-runs it; applying the proposal needs either a harness change or a recorded manual reclassification." Alternatively, drop the sentence.
>
> ### 4. MINOR: "runs cannot change the data" is stronger than `make_read_only` provides
>
> **Location:**
> - `ar_data.make_read_only` docstring.
> - `prepare_data.py` docstrings (all three nodes).
> - Report, "Design common…/Data" and "Setup is unexercised".
>
> **Failure scenario.**
> - `make_read_only` clears the write bits. The run executes as the owner of the directory, so editable code can `os.chmod` the bits back and write.
> - As root, the bits do not apply at all: variant H, under uid 0, reports the data link as writable.
> - `verify` checks only the listed files. It does not check the permission bits or flag unlisted files, so a deliberately written cache file still carries over between runs.
> - Accidental writes, the round-1 scenario, are now blocked for a non-root user. That is what the fix was meant to do.
>
> **Fix.**
> - Reword to "accidental writes by a run fail; deliberate changes by in-process code (chmod back) are not prevented", and add this to the known-limits list.
> - Optionally, have `verify` warn when the data directory has write bits set or the run's uid is 0.
>
> ## Notes
>
> **5. NOTE: report inaccuracies, wording only.**
> - "The round-2 changes … to the run and setup commands" (Representative edits). Only `setup_command` changed. `run_command` is unchanged; the spec hash moved because of `setup_command`, `frozen_paths`, `infrastructure_log_patterns` and the description.
> - "the run fails with exit 3 (`budget_not_reached`, divergent)". The harness outcome is `divergent/nonzero_exit` with `returncode: 3`. The harness reason `budget_not_reached` is a different rule, the steps regex falling short.
> - The bundle line lists "the review record" as content of the paper branch, but no review file is there yet. This is consistent with "once filed".
>
> **6. NOTE (harness property, predates the port; for the coordinator): editable code can force an infrastructure re-run.**
> - The six harness default `infrastructure_log_patterns` (`No space left on device`, `Input/output error`, …) are unanchored.
> - Editable code that prints one of them gets `infrastructure_failure` and is re-run, not scored (variant F).
> - The port's own `AR_INFRA` pattern is correctly guarded against this. The defaults are not, and the report's limits list does not mention it.
> - Suggest adding it to the known limits in the "Design common" section, with the forged-line limit.
>
> **7. NOTE: `port_smoke_gpu.py --gpu-uuid` is optional.**
> - Omitting it gives a silent CPU run that still prints `CHECKLIST_E_PASSED`. The help text says "omit only for a CPU-only node", and none of the MLAB nodes is CPU-only.
> - Making it required when `SMOKE[node]["torch_node"]` is true would close the last route to the CPU fallback that round-1 finding 8 was about.
> - No port test exercises the `AR_INFRA` path. I verified it by hand, as in "What I ran", item 7.
>
> **8. NOTE: data hashes cannot be pinned in advance.**
> - ogbn-arxiv's download has no archive hash, and distilbert's hub revision is not pinned. Both are resolved and recorded at setup.
> - This matches checklist F as written: "For the remaining files, the census records the data manifest's sha256 when it first runs the setup, and later setups must reproduce it".
> - That comparison is procedural: no script checks a later setup against the recorded hash. Acceptable for this round; the census should record the three manifest hashes as the report says.
>
> ## Checked and correct
>
> - **Report facts.** Tip sha. Round-1 and round-2 commit ids. "Only adds files": `git diff --name-status 717ad835 b77e68a` has only `A` entries. Base `717ad835`. Suite HEAD `5d71205c…` and its unfilled MIT `LICENSE`. The PLAN row locations. `b715e110` is shared with the autoresearch paper branch.
> - **Hashes.** All 3 manifest sha256 and all 12 edit sha256 match the report.
> - **Re-declared manifests.** They reproduce byte for byte under 3.12 (test). The superseded copies equal the `fbecd13` manifests. The cifar10 diffs are unchanged. The imdb and ogbn diffs carry the same `+`/`-` lines with new context; ogbn E4 only reorders.
> - **Tables.** The pair-composability table matches 36 of 36 ordered pairs. The smoke table matches 27 of 27 rows.
> - **Shared files.** `ar_fixed_loop.py` and `ar_data.py` are byte-identical in all MLAB and MLGym nodes. `ar_data.py` and the shared test modules are byte-identical across the three suite branches.
> - **Checklist section F.** It covers the task's licence and provenance step: licence, source URL, dataset hash, and "datasets never redistributed — download script + hash only". It also follows U1 §10.
> - **`LICENCES.md`.** Each node's file agrees with U1 §4 and §7:
>   - CIFAR-10: unknown;
>   - IMDb: `license: other`, revision `e628166`;
>   - ogbn-arxiv: ODC-BY per OGB's page;
>   - MIT with the unfilled copyright line.
>   - Distilbert's Apache-2.0 is flagged as not covered by U1.
> - **`prepare_data.py` logic.** Read; no network was used.
>   - The `AR_TRACKG_DATA_ROOT` containment check, the refusal of a non-empty `--out` without a manifest, and the manifest written last and then made read-only.
>   - The re-run only verifies and re-links.
>   - torchvision checks the archive md5, and the pinned constant equals `CIFAR10.tgz_md5`.
>   - ogb on a fresh root downloads (about 81 MB, so no `decide_download` prompt), processes and saves, with no `torch.load` and no `input()`.
>   - imdb refuses a revision mismatch before downloading.
>
> ## Scratch
>
> - Scripts: `/tmp/rv_mlab2/scripts/` (`variants.py`, `pairs.py`, `inert.py`).
> - Demo node copies (`/tmp/rv_mlab2/demo/`) and the archive copy with links (`/tmp/rv_mlab2/copy/`) were removed after the runs; `demo/base` remains.
> - `/tmp/rv_mlab2/tmp` (pytest temp) has been emptied.

---

## Round 3 (harness `4659b837`, report `6cfa8cb4`)

> # Review round 3: Track G U3 port kit, MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
>
> ## What was reviewed
>
> - Harness branch `mac-trackg-port-mlab-20261117b`, tip `4659b837b1279676a3ac151abb65a1b55bfbf12a`. This round's diff is `b77e68a9..4659b837`.
> - Paper branch `mac-trackg-u3-mlab-20261117b`, diff `0a9d6b8b..6cfa8cb4`. It contains the report, round 3, and the checklist with section F moved after section E.
> - My round-2 text is at `/tmp/tgsrc/reviews/mlab_r2.md`.
>
> Reviewer: an independent agent (Claude), round 3. I modified, committed and pushed nothing in any repository. Scratch was only in `/tmp/rv_mlab2/`.
>
> ## Verdict: NOT ACCEPTED
>
> The coder answered every round-2 finding and note. One leftover piece of wording remains (finding 2 below).
>
> The shared output hardening does what it was built to do: an `atexit` line and a `sys.stdout` replacement no longer get through. The shared data check also works: an unlisted file is refused.
>
> One new MAJOR finding (1) remains:
> - In all three wrappers, the editable `predict_logits` runs for the test set *after* the real `AR_METRIC` line has been written.
> - So a plain `print` in `predict_logits` appends a forged validation line.
> - The harness takes the last match, and the run scores the forged value as `ok`.
> - The report states that this kind of forgery is no longer possible.
>
> The fix is small:
> - reorder three frozen wrappers;
> - correct the limits text.
>
> The manifests do not hash frozen file contents, and the tests confirm that re-declaring reproduces them, so they would not need re-declaring.
>
> ## What I ran
>
> **Port tests.** `tests/trackg/test_port_mlagentbench.py` at `4659b837` (Python 3.12, torch 2.6.0 CPU, `TMPDIR=/tmp/rv_mlab2/tmp`): **15 passed**.
> - The synthetic-smoke run records give the same metrics as round 2 on all 27 rows. This confirms the report's statement that the smoke table is identical.
>
> **Forgery attacks.** Against the round-3 mlab_cifar10 wrapper, on synthetic data with a freshly written manifest (`setup_only=("torchvision_raw",)`), 20 steps. Each log was classified with the harness `classify_run` and the node's patterns.
>
> | Variant | Exit | Harness outcome |
> |---|---|---|
> | Baseline | 0 | ok 0.1044 |
> | `atexit` handler prints `AR_METRIC val_accuracy=0.999999` | 0 | ok **0.1044** (blocked by `os._exit`) |
> | `sys.stdout` replaced by a writer that rewrites `AR_METRIC` lines | 0 | ok **0.1044** (blocked: `emit` writes to the saved descriptor) |
> | `predict_logits` prints the forged line on the short last batch of an evaluation (`print`, during the val **and the test** pass) | 0 | **ok 0.999999**. Log tail: forged, real `0.104400`, forged (printed during the test pass), `AR_TEST` |
>
> **Data check.** Against `ar_data.verify`:
>
> | Planted file | Exit | Harness outcome |
> |---|---|---|
> | top-level `evil_cache.npy` | 5 | divergent ("files the manifest does not list") |
> | `.evil` (hidden file) | 5 | divergent |
> | `sub/evil.bin` | 5 | divergent |
> | `torchvision_raw/evil_cache.npy` (setup-only subdirectory) | 0 | ok (passes; see NOTE 4) |
>
> **Residual check after the proposed fix.** On a scratch copy of the wrapper, I computed both predictions before either `emit`. Then I ran a `predict_logits` that starts a daemon thread writing the forged line to fd 1 in a loop. In 3 of 5 runs, the forged value was the last match and the run scored 0.999999. Wrapper reordering therefore removes the plain-`print` route but not a concurrent thread (see finding 1).
>
> **Setup-only names against what each `prepare_data.py` leaves in `--out`:**
> - **cifar10:** everything besides the four arrays and the manifest is under `torchvision_raw/` (the archive and `cifar-10-batches-py/`). This matches `setup_only=("torchvision_raw",)`.
> - **ogbn:** ogb 1.3.6 downloads into `original_root` = `out/ogb_raw` and moves the extracted tree to `ogb_raw/ogbn_arxiv/` (`raw/`, `processed/`, `split/`, `mapping/`, `RELEASE_v1.txt`). This matches `("ogb_raw",)`.
> - **imdb:**
>   - `snapshot_download(local_dir=pretrained)` in huggingface_hub 0.36.2 keeps its metadata, locks, `.gitignore` and incomplete downloads under `local_dir/.cache/huggingface/`. This matches `("pretrained/.cache",)`.
>   - The dataset and xet caches go to `~/.cache`, outside `--out`.
>   - Any other file planted in `pretrained/` is refused, which is the right behaviour.
>
> **Other checks:**
> - `port_smoke_gpu.py --node mlab_cifar10` without `--gpu-uuid` now stops with "--gpu-uuid is required for mlab_cifar10".
> - The determinism shim writes its record at interpreter start, not at exit, so `os._exit` does not lose it. The new `not_forced` check passes on every executed record.
> - `ar_data.py` is byte-identical in all 7 nodes of the three suite branches. `ar_fixed_loop.py` is byte-identical in all 5 torch nodes. `port_support.py` and `port_smoke_gpu.py` are identical on all three branches.
> - The checklist change only moves lines: sorted line sets are equal.
> - `git diff --name-status 717ad835 4659b837` still lists added files only.
>
> ## Round-2 findings and notes
>
> | # | Sev. | Round-2 finding | Status | Evidence |
> |---|---|---|---|---|
> | 1 | MINOR | Step hook counts `step()` calls, not updates; limits list and docstring overclaimed | **Fixed** | The `ar_fixed_loop.train_fixed_steps` docstring and the report now say "calls, not updates". They list Lookahead and SAM written inside `step()`, tampering with the hook registry and the unwrapped `step`. They also document the `super().step()` double count. |
> | 2 | MINOR | Two named S1.1 pairs are behaviourally inert | **Fixed** | The report explains the inert pairs: cifar10 E1+E3 and E3+E4, ogbn E3+E4. `INTERACTING` is now cifar10 {E1+E2, E2+E3, E2+E4}, imdb unchanged, ogbn {E1+E3, E2+E3}, and the report's list matches it. |
> | 3 | MINOR | Open point 2 set an interim outcome rule | **Fixed** | Now worded as "Proposed, pending your decision", and it states that the harness classes every timeout as `infrastructure_failure` and re-runs it. |
> | 4 | MINOR | "Runs cannot change the data" overclaimed | **Mostly fixed** (residue in new finding 2) | Fixed in the `ar_data` module docstring, the `make_read_only` docstring and the report. The words remain in all three `prepare_data.py` files, both the docstring and the inline comment. |
> | 5 | NOTE | Report wording | **Fixed** | `run_command` wording corrected. Exit 3 is described as `divergent`/`nonzero_exit`. The bundle line now says "once the review is accepted". |
> | 6 | NOTE | Harness default infrastructure patterns are unanchored | **Addressed** | Listed in the report's known limits as a harness property that predates the port. |
> | 7 | NOTE | `--gpu-uuid` optional; `AR_INFRA` path untested | **Addressed** | `--gpu-uuid` is required except for `mlgym_houseprice`. The report states that no port test covers the `AR_INFRA` path (it was checked by hand in round 2). |
> | 8 | NOTE | Data hashes not pinnable in advance | **Addressed** | New open point 3 in the report. |
>
> ## New findings
>
> ### 1. MAJOR: editable code still runs after the real `AR_METRIC` line, so a plain `print` forges the selection metric; the report says this is no longer possible
>
> **Location:**
> - `nodes/mlab_cifar10/run_fixed_budget.py:52-55`, `nodes/mlab_imdb/run_fixed_budget.py:64-67`, `nodes/mlab_ogbn_arxiv/run_fixed_budget.py:67-70`. Each runs `emit(AR_METRIC …)` before `predict_classes`/`predict_split` on the test set, which calls the editable `predict_logits`.
> - The `ar_data` module docstring: "editable code cannot … add lines after them from an `atexit` handler. It can still print a forged line and exit before the wrapper prints its own."
> - The report, "Budget enforcement and its limits" and "Metric lines": "A diff could still print a forged line and end the process itself before the wrapper prints".
>
> **Failure scenario.**
> - A proposal's `predict_logits` prints `AR_METRIC val_accuracy=0.999999` once it sees the test set. A short final batch or a call counter is enough.
> - The line lands after the real `AR_METRIC` and before `AR_TEST`. `classify_run` uses `metrics[-1]` (`outcome.py`), so the run is `ok` with the forged value. Demonstrated on cifar10. imdb and ogbn have the same order.
> - The same applies to `raise SystemExit(0)` inside the test pass: `sys.exit` runs `atexit` handlers, the real `AR_METRIC` has already been written, and no `os._exit` follows.
> - This is exactly the "forged metric line after the real one" class that the shared round-3 change was meant to close. The report's limits text leads the coordinator and the S1 audit to look only for code that ends the process early, not for output in `predict_logits`.
> - The same order is visible in `/tmp/pb/wt/tgb-mlgym/nodes/mlgym_cifar10/run_fixed_budget.py:53-56`. I did not review that branch. I pass this on for the coordinator, because the change is shared.
>
> **Fix.**
> 1. In each wrapper, compute the validation and test predictions first. Then call `emit(AR_METRIC …)`, `emit(AR_TEST …)` and `finish()` with no editable call between them.
>    - These are frozen files, so the manifests stay as they are (the report says, and the tests confirm, that re-declaring reproduces them).
>    - Add a static check: in `run_fixed_budget.py`, no `predict_*` or `T.` call after the first `emit(`.
> 2. Correct the limits text in the `ar_data` docstring and the report. Something like this would work: "Editable code can still write a forged line before the wrapper's lines, or from a thread it started that runs concurrently with them. The harness takes the last match, so such a thread can win the race (shown on a reordered copy: 3 of 5 runs). Only a harness change closes this, such as rejecting a run with more than one `AR_METRIC` match or reading the result from a channel the editable code cannot write. That change is outside the port."
>    - Raise the harness option as an open point for the coordinator.
>
> ### 2. MINOR: the "runs cannot change the data" wording survives in `prepare_data.py`
>
> **Location:** `nodes/mlab_{cifar10,imdb,ogbn_arxiv}/prepare_data.py`. In each file the module docstring says "the directory is then made read-only, so runs cannot change the data", and the inline comment at the `make_read_only` call says "runs cannot change the shared data or leave files in it". Round-2 finding 4 named these files.
>
> **Failure scenario.** The frozen setup script tells the experiment agent the opposite of what `ar_data` and the report now say.
>
> **Fix.** Use the `ar_data` wording: "accidental writes by a run fail; the owner can restore the bits".
>
> ### 3. NOTE: the `finish()` static check is a substring test
>
> **Location:** `port_support.check_static`, the line `assert "finish()" in wrapper`.
>
> **Failure scenario.** A comment such as `# finish() is not needed` passes the check.
>
> **Fix.** Optional: check for `ar_data.finish()` as the last statement under `if __name__ == "__main__":`, or parse the AST. Together with finding 1, also check that `emit` calls come last.
>
> ### 4. NOTE: setup-only subdirectories still carry state between runs
>
> **Location:** `ar_data.unlisted_files`.
>
> **Failure scenario.**
> - A run that restores the write bits, or runs as root, can keep a cache under `torchvision_raw/`, `ogb_raw/` or `pretrained/.cache/`. The cache passes `verify`, as demonstrated with `torchvision_raw/evil_cache.npy`.
> - The same is true of anywhere outside the data directory that the user can write (`~/.cache`, `/tmp`).
> - The report's limits already cover "rewrite data and manifest together" and the owner restoring the bits. This channel is one more instance.
>
> **Fix.** Optional: in the limits text, add "files written under the setup-only subdirectories, or outside the data directory, are not checked".
>
> ## Scratch
>
> - Scripts: `/tmp/rv_mlab2/scripts/r3_attacks.py` and `/tmp/rv_mlab2/scripts/r3_thread.py`.
> - The working copies and synthetic data under `/tmp/rv_mlab2/r3/` were removed after the runs.
> - `/tmp/rv_mlab2/tmp` (pytest temp) has been emptied.

---

## Round 4 (harness `b6345961`, report `bbd74de5`)

> # Review round 4: Track G U3 port kit, MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
>
> ## What was reviewed
>
> - **Harness branch:** `mac-trackg-port-mlab-20261117b`, tip `b63459611689090203d104365872ed0b480e8eab`. This round's diff is `4659b837..b6345961`.
> - **Paper branch:** `mac-trackg-u3-mlab-20261117b`, diff `6cfa8cb4..bbd74de5` (the report, round 4).
> - **Previous review:** my round-3 text is at `/tmp/tgsrc/reviews/mlab_r3.md`.
>
> Reviewer: an independent agent (Claude), round 4. I modified, committed and pushed nothing in any repository. Scratch was only in `/tmp/rv_mlab2/`.
>
> ## Verdict: NOT ACCEPTED
>
> The round-3 MAJOR finding is fixed for the route I demonstrated. A `print` in `predict_logits` during the test pass no longer wins, and neither does a thread that writes whole lines to fd 1. The wording finding and both notes are fixed.
>
> Two new MAJOR findings remain. Each lets a proposal score a forged selection metric as `ok`, and each has a one-line fix that I tested on a scratch copy. Neither fix needs the manifests re-declared, because they hash no frozen file contents.
>
> 1. **An unterminated line breaks the real result line.**
>    - Editable code writes a forged line followed by an unterminated fragment.
>    - `seal()` flushes the fragment into the log.
>    - The real `AR_METRIC` is then appended to that fragment on the same line, so it no longer matches the anchored regex.
>    - The forged line is then the last match. This is deterministic, and needs no thread and no descriptor tricks.
>    - A thread that simply calls `print()` in a loop gets the same effect by chance: it won 2 of 3 runs, and 4 of 6 counting a repeat.
>    - This finding comes from this round's change.
> 2. **A tensor subclass returned by `predict_logits` rewrites the frozen accuracy.**
>    - The subclass's `__torch_function__` runs editable code inside the frozen `argmax`, `==` and `mean`.
>    - In my demonstration, the frozen wrapper itself printed `AR_METRIC val_accuracy=1.000000`. It was the only match, and no forgery of the log was involved.
>    - This has existed since round 1. **I missed it in rounds 1–3.**
>
> ## What I ran
>
> **Port tests.** `tests/trackg/test_port_mlagentbench.py` at `b6345961` (Python 3.12, torch 2.6.0 CPU): **15 passed**. The synthetic-smoke metrics on all 27 rows match rounds 2 and 3.
>
> **Attacks.** Against the round-4 mlab_cifar10 wrapper, on synthetic data, 20 steps. Logs went to a file opened `"w"`; the runner opens `run.log` with `"wb"`, which behaves the same. Each log was classified with the harness `classify_run` and the node's patterns. Thread variants ran 3 times.
>
> | Variant (editable `train.py`) | Exit | Harness outcome |
> |---|---|---|
> | Baseline | 0 | ok 0.1044 |
> | `print(forged)` in `predict_logits` during the test pass (round-3 attack) | 0 | **ok 0.1044**, blocked (the real line comes last) |
> | `raise SystemExit(0)` during the test pass, plus an `atexit` forged line | 0 | ok **0.999999**. This is the documented "end the process before the wrapper prints" limit; the log has only the forged match |
> | Daemon thread, `os.write(1, forged + "\n")` in a loop (round-3 thread attack) | 0 | **ok 0.1044**, 3/3 blocked by `seal()` |
> | Daemon thread, `print(forged, flush=True)` in a loop | 0 | **ok 0.999999 in 2/3** (a repeat: 2/3). The log shows `AR_METRIC val_accuracy=0.999999AR_METRIC val_accuracy=0.104400` as one line (finding 1) |
> | **`sys.stdout.write(forged + "\nZ")` once, during the test pass (no thread)** | 0 | **ok 0.999999**. The real line became `ZAR_METRIC val_accuracy=0.104400` (finding 1) |
> | **Same with `os.write(1, forged + b"\nZ")`** | 0 | **ok 0.999999** (finding 1) |
> | Daemon thread writing through its own `os.dup(1)`, taken before `seal()` | 0 | ok 0.1044 3/3 (lost the race here; nothing prevents it) |
> | Daemon thread writing to `ar_data._OUT_FD` | 0 | ok 0.1044 3/3 (lost the race here; documented limit) |
> | Daemon thread that reopens the log by path (`readlink /proc/self/fd/1`, `O_APPEND`) | 0 | **ok 0.999999, 3/3** (finding 3) |
> | **`predict_logits` returns `logits.as_subclass(_Liar)`, where `_Liar.__torch_function__` makes `==` return all True** | 0 | **ok 1.0**. A single, genuine `AR_METRIC val_accuracy=1.000000` from the frozen wrapper (finding 2) |
> | Planted `evil_cache.npy`, `.evil`, `sub/evil.bin` | 5 | divergent (refused) |
> | Planted `torchvision_raw/evil_cache.npy` | 0 | ok (documented limit) |
>
> **Proposed fixes, on a scratch copy of the node (`/tmp/rv_mlab2/r3/fixnode`, since removed):**
> - Fix for finding 1: one line in `seal()`, `os.write(_OUT_FD, b"\n")` after the two `dup2` calls. Both partial-line variants then give ok 0.1044, `thread_print_stdout` gives 0.1044 in 3/3, and `thread_oswrite_fd1` gives 0.1044 in 3/3.
> - Fix for finding 2: in `ar_fixed_loop.predict_classes`, `if type(logits) is not torch.Tensor: fail(EXIT_BAD_EDITABLE_API, …)`. The subclass variant then gives exit 4, divergent; the baseline is unchanged at ok 0.1044.
>
> **Static check (round-3 note 3).** I applied the new `check_static` logic to mutated copies of the cifar10 wrapper:
>
> | Mutation | Result |
> |---|---|
> | none (the tip) | pass |
> | a `T.predict_logits(...)` call inserted between the two emits | caught |
> | `ar_data.finish()` only in a comment | caught |
> | `seal()` removed | caught |
>
> **Other checks:**
> - The `prepare_data.py` and `ar_data` wording no longer says "cannot change".
> - `ar_data.py` is byte-identical in all 7 nodes of the three suite branches. `ar_fixed_loop.py` is byte-identical in all 5 torch nodes. `port_support.py` and `port_smoke_gpu.py` are identical on all three branches.
> - The branch still only adds files relative to `717ad835`.
> - `git diff 4659b837 b6345961` does not touch `representative_edits/` or `configs/`.
>
> ## Round-3 findings
>
> | # | Sev. | Round-3 finding | Status | Evidence |
> |---|---|---|---|---|
> | 1 | MAJOR | Editable `predict_logits` ran after the real `AR_METRIC`; a plain `print` forged the metric | **Fixed for that route; residual in new finding 1** | Both evaluations and both accuracies now come before `seal()`, `emit`, `emit`. The round-3 `print` attack and the whole-line thread attack are blocked. An unterminated fragment written before `seal()` still breaks the real line. |
> | 2 | MINOR | "Runs cannot change the data" in `prepare_data.py` | **Fixed** | All three files now say "accidental writes by a run fail (the owner can restore the write bits; see ar_data)". |
> | 3 | NOTE | `finish()` check was a substring test | **Fixed** | A regex anchored to `main()` under `__main__`. The mutation tests above are caught. |
> | 4 | NOTE | Setup-only subdirectories and paths outside the data directory carry state | **Fixed** (documented) | In the `ar_data` docstring, the report's limits list and the Data section. |
>
> ## New findings
>
> ### 1. MAJOR: an unterminated line written before `seal()` breaks the real `AR_METRIC` line, so a forged earlier line wins
>
> **Location:** `nodes/*/ar_data.py`, `seal()` and `emit()`. The report, "Metric lines": "editable code cannot … print a line after them from its evaluation code or a thread".
>
> **Failure scenario.**
> - During the test pass, `predict_logits` runs `sys.stdout.write("AR_METRIC val_accuracy=0.999999\nZ")` once (or the same with `os.write(1, …)`).
> - `seal()` flushes the buffer to fd 1, so the log ends in `…0.999999\nZ`. Only then does it redirect fd 1.
> - `emit` writes the real line to the saved descriptor, directly after `Z`. The log line `ZAR_METRIC val_accuracy=0.104400` does not match the anchored `^AR_METRIC val_accuracy=(\S+)$`, so the forged line is the last, and only, match.
> - The run is `ok` 0.999999 in every attempt. It is deterministic, takes one write, and needs no thread or descriptor manipulation. It is the kind of line the round-3 fix was meant to stop.
> - A thread that just calls `print()` in a loop hits the same failure by chance: Python writes the text and the newline separately, so `seal()` can flush a line without its newline. It won 4 of 6 runs.
> - The harness option the report proposes for the coordinator does not help here. Refusing a run with more than one metric match would see a single match.
>
> **Fix.**
> - In `seal()`, after `os.dup2(devnull, 2)`, add `os.write(_OUT_FD, b"\n")` so that any partial line is terminated before the result lines. Alternatively, have the first `emit` start with `"\n"`.
> - Tested on a scratch copy: both partial-line variants and the `print`-thread variant then score the real value in every run.
> - Add a regression test: a synthetic run whose editable code leaves an unterminated fragment must score the real metric.
> - `ar_data.py` is shared with the MLGym and autoresearch branches. The MLGym Breakout wrapper, which inlines its finish, should get the same newline.
>
> ### 2. MAJOR: a tensor subclass returned by `predict_logits` runs editable code inside the frozen metric computation
>
> **Location:**
> - `nodes/*/ar_fixed_loop.py`, `predict_classes`: `torch.is_tensor(logits)` accepts subclasses, and the code then calls `logits.float().argmax(dim=1)`.
> - `accuracy`: `(pred.to(labels.device) == labels).double().mean().item()`.
> - `nodes/mlab_ogbn_arxiv/run_fixed_budget.py`, `predict_split`, which has the same check.
>
> **Failure scenario.**
> - `predict_logits` returns `torch.Tensor.as_subclass(logits, _Liar)`, where `_Liar.__torch_function__` makes `eq` return all True.
> - Through `__torch_function__`, the frozen `argmax`, `==`, `mean` and `item` all dispatch to editable code.
> - The frozen wrapper itself prints `AR_METRIC val_accuracy=1.000000` and `AR_TEST test_accuracy=1.000000`. The run is `ok` 1.0 with one genuine match. No log forgery is involved, so neither `seal()` nor a harness one-match rule would catch it.
> - The report's limits list does not cover it. It is not "patching the wrapper": the frozen code calls the editable object as designed.
> - This has been possible since round 1. I missed it in rounds 1–3.
>
> **Fix.**
> - In `predict_classes`, and in ogbn's `predict_split`, refuse anything but a plain tensor before any operation on it: `if type(logits) is not torch.Tensor: fail(EXIT_BAD_EDITABLE_API, "predict_logits must return a plain torch.Tensor")`.
> - Tested on a scratch copy: the subclass variant then gets exit 4, `divergent`, and the baseline is unchanged.
> - Add a static or synthetic test.
> - `ar_fixed_loop.py` is shared with the MLGym torch nodes. The MLGym non-torch nodes (House Price estimator, Breakout network) should be checked for the same pattern, where an editable object's methods compute values the frozen metric uses.
> - Optionally, apply the same check to the `training_step` loss. A subclass loss can run code in `backward()`, but that falls under the existing "manual updates" limit.
>
> ### 3. MINOR: the limits text still overstates what `seal()` stops
>
> **Location:**
> - The report, "Budget enforcement and its limits", "Metric lines" and open point 5.
> - The `ar_data` module docstring: "a thread the editable code started can no longer print into the log", and "A harness change would close the rest (for example refusing a run with more than one metric match)".
>
> **Failure scenario.**
> - **Reopened log.** `seal()` redirects fds 1 and 2 only. A thread that reopened the log beforehand (by path, via `/proc/self/fd/1`) or kept its own `os.dup(1)` still writes into the log.
> - **Overwritten real line.** The runner opens `run.log` with `"wb"`, so the real lines are written at fd 1's file offset. The thread's `O_APPEND` writes land after them at end of file. The forged value is then the last match (3/3 runs).
> - **Single forged match.** "Print a forged line and end the process before the wrapper prints" leaves exactly one, forged, match (`SystemExit(0)` plus `atexit`: ok 0.999999). Refusing more than one match therefore does not close it, and neither does it close finding 1 without the newline fix.
>
> **Fix.**
> - List "any other descriptor or file handle to the log obtained before `seal()` (its own `dup(1)`, the log reopened by path)" next to "the saved descriptor".
> - State the harness option precisely: refusing more than one match catches concurrent writers once finding 1 is fixed, but not an early exit with a single forged line. Closing that would also need, for example, a result channel the editable code cannot open, which is outside the port.
>
> ## Scratch
>
> - Scripts: `/tmp/rv_mlab2/scripts/r4_attacks.py`, `r4_partial.py`, `r4_only.py` and `r4_subclass.py`.
> - The working copies, the synthetic data and the scratch fix copy under `/tmp/rv_mlab2/r3/` were removed after the runs.
> - `/tmp/rv_mlab2/tmp` (pytest temp) has been emptied.

---

## Round 5 (harness `5563fa38`, report `91ca9a96`)

> # Review round 5: Track G U3 port kit, MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
>
> - **Harness branch:** `mac-trackg-port-mlab-20261117b`, tip `5563fa38626ef590be832b6fcc3af385f7d9d4c6`. This round's diff is `b6345961..5563fa38`.
> - **Paper branch:** `mac-trackg-u3-mlab-20261117b`, diff `bbd74de5..91ca9a96` (the report, round 5, with the threat model).
> - **Previous review:** my round-4 text is at `/tmp/tgsrc/reviews/mlab_r4.md`.
> - **Reviewer:** an independent agent (Claude), round 5.
> - **What I touched:** I modified, committed and pushed nothing in any repository. Scratch was only in `/tmp/rv_mlab2/`.
>
> ## Verdict: ACCEPTED
>
> Both round-4 MAJOR findings are fixed, and I reproduced each fix against the tip:
> - The partial-line attack and the `print`-thread attack now lose to the real line.
> - A tensor subclass returned by `predict_logits` is refused in `ar_fixed_loop.predict_classes`, and in ogbn's `predict_split`.
> - A torch-function mode left active no longer changes the frozen accuracy.
>
> Round-4 finding 3, which said the limits text claimed too much, is answered by the threat model. The threat model is accurate in what it claims the frozen code closes. Its list of what stays possible is incomplete in two ways that matter to the S1 audit, which uses the keyword list as its grep list:
> - a torch *dispatch* mode, or a patch to torch itself, still rewrites the frozen accuracy as a single genuine line;
> - its proposed "kill the process group" remedy already exists in the runner.
>
> Those are new findings 1 and 2, both MINOR. They are fixes to the report's text only and do not hold back acceptance.
>
> ## What I ran
>
> **Port tests.** `tests/trackg/test_port_mlagentbench.py` at `5563fa38` (Python 3.12, torch 2.6.0 CPU): **21 passed**. This matches the report. The synthetic-smoke metrics on all 27 rows are identical to rounds 2–4.
>
> **Attacks against the round-5 wrappers.** Synthetic data, 20 steps. Logs went to a file opened `"w"`, as the runner opens `run.log` with `"wb"`. Each log was classified with the harness `classify_run` and the node's patterns.
>
> | Variant (editable `train.py`) | Node | Exit | Harness outcome |
> |---|---|---|---|
> | Baseline | cifar10 | 0 | ok 0.1044 |
> | `print(forged)` in `predict_logits` during the test pass | cifar10 | 0 | ok **0.1044** (real line last) |
> | One `sys.stdout.write(forged + "\nZ")` during the test pass (round-4 finding 1) | cifar10 | 0 | ok **0.1044** (the newline from `seal()` ends the `Z` line) |
> | Daemon thread, `print(forged)` in a loop (3 runs) | cifar10 | 0 | ok **0.1044** in 3/3 (a partial forged line is glued to the end-of-run `AR_DATA` line instead) |
> | Daemon thread, `os.write(1, forged)` in a loop (3 runs) | cifar10 | 0 | ok **0.1044** in 3/3 |
> | `predict_logits` returns a `torch.Tensor` subclass that rewrites `eq` (round-4 finding 2) | cifar10 | 4 | divergent ("must return a plain torch.Tensor") |
> | Same subclass | ogbn | 4 | divergent ("must return a plain torch.Tensor of shape (400, 40)") |
> | `TorchFunctionMode` that rewrites `eq`, entered and left active | cifar10 | 0 | ok **0.1044** (blocked by `DisableTorchFunction`) |
> | **`TorchDispatchMode` that rewrites `aten.eq.Tensor`, entered and left active** | cifar10 | 0 | **ok 1.0**: a single genuine `AR_METRIC val_accuracy=1.000000` (new finding 1) |
> | **`torch.Tensor.__eq__` replaced at run time** | cifar10 | 0 | **ok 1.0**: a single genuine line (new finding 1) |
> | `planted.npy` written into `data/` during training | cifar10 | 5 | divergent ("the editable code changed the data: … ['planted.npy']") |
> | A `Z` written before every loss line, plus a NaN loss from step 5 | cifar10 | 0 | divergent / `budget_not_reached` (the hidden loss lines also hide the step lines, so the run still fails) |
>
> **Other checks:**
> - `ar_data.py` is byte-identical in all 7 nodes of the three suite branches. `ar_fixed_loop.py` is byte-identical in all 5 torch nodes. `port_support.py` is identical on the three branches.
> - `git diff b6345961 5563fa38` does not touch `train.py`, `representative_edits/` or `configs/`, and the manifests reproduce (test).
> - The branch still only adds files relative to `717ad835`.
> - New tests:
>   - `check_output_seal` runs a partial line plus a writing thread into a log file.
>   - `check_plain_tensor_metric` checks that the subclass is refused and that the accuracy under a subclass stays correct.
>   - `check_plain_tensor_metric` exercises `ar_fixed_loop` only, not ogbn's own `predict_split`. I checked that function by hand (row above).
>
> ## Round-4 findings
>
> | # | Sev. | Round-4 finding | Status | Evidence |
> |---|---|---|---|---|
> | 1 | MAJOR | A partial line left before `seal()` swallowed the real `AR_METRIC` | **Fixed** | `seal()` writes `b"\n"` to the saved descriptor after the `dup2` calls. Both the partial-line variant and the `print`-thread variant score the real value (3/3). A regression test was added. |
> | 2 | MAJOR | A tensor subclass from `predict_logits` ran editable code inside the frozen accuracy | **Fixed** | `type(logits) is torch.Tensor` is required in `predict_classes` and ogbn's `predict_split`. `argmax`, `cat` and `accuracy` run under `torch._C.DisableTorchFunction()`. Subclass: exit 4 (cifar10, ogbn). Torch-function mode: no effect. The training loss must also be a plain tensor. A test was added. |
> | 3 | MINOR | The limits text overstated what `seal()` stops | **Answered by the threat model** | Listed as still possible: an early exit, descriptors obtained before the seal (the saved descriptor, its own `dup`, the log reopened by path), seeks in the non-`O_APPEND` log, forked children, run-time patches and direct data reads. The harness remedies are an open point for the coordinator, which now says that refusing more than one match alone does not catch an early exit. Accurate except for new findings 1 and 2. |
>
> ## New findings
>
> ### 1. MINOR: the threat model omits torch dispatch modes and patches to torch itself, which still rewrite the frozen accuracy as one genuine line
>
> **Location:**
> - Report, "What the frozen code guarantees, and what it does not (threat model)". It says the frozen code closes "a tensor subclass or torch-function mode inside the frozen arithmetic".
> - Its "still possible" list names "patch frozen modules at run time".
> - Its audit keyword list: `os._exit`, `os.fork`, …, `importlib`, ….
> - The comments in `ar_fixed_loop.py` ("no `__torch_function__` subclass or mode of the editable code").
>
> **Failure scenario.**
> - **Dispatch mode.** `predict_logits` enters a `torch.utils._python_dispatch.TorchDispatchMode` and leaves it active. Its `__torch_dispatch__` replaces the result of `aten.eq.Tensor` with all True. `DisableTorchFunction` does not reach the dispatcher-level mode stack, so the frozen `accuracy` returns 1.0, and the frozen wrapper itself prints `AR_METRIC val_accuracy=1.000000` (ok 1.0, one match).
> - **Patch to torch.** Replacing `torch.Tensor.__eq__` gives the same result.
> - **Why it matters.** Neither is a "frozen module". Neither matches any keyword in the audit list, and a one-match harness rule would not catch either. An auditor grepping for the listed keywords would miss both, though they are as short as the subclass attack the port now refuses.
>
> **Fix.** Text only:
> - Add "a torch dispatch mode, or a patch to torch or numpy themselves (e.g. `torch.Tensor.__eq__ = …`)" to the "still possible" list.
> - Add `TorchDispatchMode`, `__torch_dispatch__`, `_python_dispatch`, `torch.library` and assignments to `torch.`/`np.` attributes or `setattr(torch…` to the audit keywords.
> - Narrow the `ar_fixed_loop` comment to "torch-function subclass or mode".
>
> No in-process fix closes these. That matches the report's stance that closing them needs the harness: a separate process for the editable code.
>
> ### 2. MINOR: the "kill the process group" remedy already exists; the actual gap is a child that leaves the session, or the moment before the kill
>
> **Location:** report, the threat model ("fork a child that writes after the wrapper has exited … kill the process group when the wrapper exits") and open point 5.
>
> **Failure scenario.**
> - After a normal exit, `WorkingCopyRunner._execute` already calls `_kill_leftovers(proc.pid)`. That function SIGKILLs every process in the run's process group *and session* (`runner.py:289-291`, `_run_members`).
> - A forked child therefore survives only if it calls `setsid()` and so leaves the session (the `_run_members` docstring says so). It can also write in the short interval between the wrapper's exit and the scan.
> - As written, the open point asks the coordinator for a harness change that exists already, and leaves out the one that would help: killing the cgroup, or tracking descendants rather than the session.
>
> **Fix.** Text only. Reword to: "a child that calls `setsid()` escapes the runner's post-exit kill of the group and session (and any child can write before that kill runs); closing it needs a cgroup or a descendant-tracking kill".
>
> ### 3. NOTE: "the run that changed them fails itself" holds only for changes made before its end-of-run check
>
> **Location:** report, Data: "Every wrapper checks the data again after the editable code has run … so the run that changed them fails itself; a start-of-run exit 5 therefore means an earlier run changed them, and the experiment agent should STOP the campaign there and find that run."
>
> **Failure scenario.**
> - A thread, or a child that calls `setsid()`, can change the data after the end-of-run `verify`, while the result lines are being written. That run is `ok`, and the next run fails at start.
> - The STOP rule is right. The run to find may be the last run that *passed*, not one that failed.
>
> **Fix.** Optional: add "(or, for code that changes them after that check — a thread or an escaped child — the last run before the failing one)".
>
> ## Scratch
>
> - Scripts: `/tmp/rv_mlab2/scripts/r5_attacks.py` (built on `r4_only.py`).
> - The working copies and synthetic data under `/tmp/rv_mlab2/r3/` were removed after the runs.
> - `/tmp/rv_mlab2/tmp` (pytest temp) has been emptied.

---

## Round 6 (harness `1db68471`, report `8bce3ccd`)

> # Review round 6 (confirmation): Track G U3 port kit, MLAgentBench (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv)
>
> - **Harness branch:** `mac-trackg-port-mlab-20261117b`, tip `1db684711bf868a85ddb243dc18b88c4daf6a506`. This round's diff is `5563fa38..1db68471`.
> - **Paper branch:** `mac-trackg-u3-mlab-20261117b`, diff `91ca9a96..8bce3ccd` (the report, round 6).
> - **Previous review:** my round-5 text is at `/tmp/tgsrc/reviews/mlab_r5.md`.
> - **Reviewer:** an independent agent (Claude), round 6. I modified, committed and pushed nothing in any repository. Scratch was only in `/tmp/rv_mlab2/`.
>
> ## Verdict: ACCEPTED
>
> Both shared code changes do what the report says:
> - A torch dispatch mode or a torch-function mode left active now stops the run with exit 4 before the frozen argmax and accuracy.
> - Every line that `emit` writes now starts with a newline, so a partial line can no longer hide a NaN loss.
>
> A patch to torch itself still produces a wrong but genuine result line, as stated. The threat model now lists that, and it also lists overriding an aten kernel through `torch.library`, which I added as a test variant.
>
> All three round-5 text findings are answered accurately. I found no regressions. One NOTE on wording remains.
>
> ## What I ran
>
> **Port tests.** `tests/trackg/test_port_mlagentbench.py` at `1db68471` (Python 3.12, torch 2.6.0 CPU): **21 passed**. This matches the report. The synthetic-smoke metrics on all 27 rows are identical to rounds 2–5.
>
> **Attacks against the round-6 cifar10 wrapper.** Synthetic data, 20 steps, log to a file. Each log was classified with the harness `classify_run` and the node's patterns.
>
> | Variant (editable `train.py`) | Exit | Harness outcome |
> |---|---|---|
> | Baseline | 0 | ok 0.1044 |
> | `TorchDispatchMode` rewriting `aten.eq.Tensor`, left active (round-5 finding 1) | **4** | divergent ("a torch function or dispatch mode is active during the frozen evaluation") |
> | `TorchFunctionMode` rewriting `eq`, left active | **4** | divergent (same message; in round 5 it was already harmless) |
> | `torch.Tensor.__eq__` replaced at run time | 0 | ok **1.0**: a single genuine line. Stays possible, and is listed in the threat model ("patch torch or numpy themselves (for example `torch.Tensor.__eq__ = …`)") |
> | `torch.library.Library("aten", "IMPL").impl("eq.Tensor", all_true, "CPU")` | 0 | ok **1.0**: a single genuine line. Covered by "patch torch" and the `torch.library` reading-aid keyword |
> | Tensor subclass from `predict_logits` | 4 | divergent (unchanged) |
> | One `sys.stdout.write(forged + "\nZ")` during the test pass | 0 | ok 0.1044 (real line last) |
> | Daemon thread, `print(forged)` in a loop, 3 runs | 0 | ok 0.1044 in 3/3 |
> | A `Z` written before every loss line, plus a NaN loss from step 5 | 0 | **divergent / non_finite_loss**. The log shows `step 10 loss nan` on its own line; in round 5 this run was `budget_not_reached` |
>
> **Other checks:**
> - `torch._C._len_torch_dispatch_stack()` also counts infra modes: `FunctionalTensorMode` and `FakeTensorMode` each give 1. So `no_active_modes()` sees those too.
> - ogbn's `predict_split` calls `L.no_active_modes()` before its argmax (read).
> - The leading newline in `emit` adds a blank line before each loss and result line. None of the node's patterns is affected: all are `^…$`, and the `AR_INFRA` pattern only looks at lines printed before `AR_DEVICE`. The baseline-log check in the smoke passes.
> - `ar_data.py` is byte-identical in all 7 nodes of the three suite branches. `ar_fixed_loop.py` is byte-identical in all 5 torch nodes. `port_support.py` is identical on the three branches.
> - `5563fa38..1db68471` does not touch `train.py`, `representative_edits/` or `configs/`. The branch still only adds files relative to `717ad835`.
>
> ## Round-5 findings
>
> | # | Sev. | Round-5 finding | Status | Evidence |
> |---|---|---|---|---|
> | 1 | MINOR | The threat model omitted dispatch modes and patches to torch | **Fixed** (partly by code) | Dispatch and function modes are now refused (exit 4; tested above and by a new test). The threat model lists patches to torch or numpy and the reading-aid keywords (`TorchDispatchMode`, `__torch_dispatch__`, `_python_dispatch`, `torch.library`, assignments to `torch.`/`np.` attributes, `setattr(torch`), and says the keywords are "a reading aid … not a filter". The `accuracy` docstring says a patch to torch is not detected. |
> | 2 | MINOR | "Kill the process group" already exists; the gap is `setsid` | **Fixed** | The threat model and open point 5 now name the runner's existing kill of the process group and session, a child that calls `setsid()`, writes made before that kill, and a cgroup or descendant kill as the remedy. |
> | 3 | NOTE | "The run that changed the data fails itself" holds only before its end-of-run check | **Fixed** | The Data text adds "unless the change came after that check (a thread or an escaped child), in which case it is the last run before the failing one". |
>
> ## New findings
>
> ### 1. NOTE: one "still possible" item in the threat model is harmless as written
>
> **Location:** report, threat model: "…or enter a mode only while its own code runs inside the evaluation, which rewrites the frozen arithmetic so that the wrapper prints a single genuine but wrong line".
>
> **Detail.**
> - A mode that is active only while `predict_logits` runs, and exited before it returns, does not reach the frozen argmax or accuracy. Those run afterwards, and `no_active_modes()` confirms that both stacks are empty.
> - All such a mode can change is the logits that `predict_logits` returns, and the editable code controls those anyway. The real route to perfect logits is "read the task data directly", which the list already has.
> - The item errs on the conservative side and misleads nobody about a closure, but it describes a mechanism that does not work.
>
> **Fix.** Optional: drop the item, or reword it as "produce its logits from the task labels (read directly)".
>
> ## Scratch
>
> - Scripts: `/tmp/rv_mlab2/scripts/r6_attacks.py` (built on `r5_attacks.py`).
> - The working copies and synthetic data under `/tmp/rv_mlab2/r3/` were removed after the runs.
> - `/tmp/rv_mlab2/tmp` (pytest temp) has been emptied.

---

## Not changed after acceptance

Round 6's note (one "still possible" item of the threat model, a mode entered only while `predict_logits` runs, describes a route that cannot reach the frozen arithmetic) is left as written: it overstates a risk and claims no protection.

## For the author and the coordinator (from the report)

The report's open points: imdb's port-written baseline; run length, batch caps and the timeout classification (a proposal, pending a decision); data hashes known only after the census setup; data licences as U1 records them; the harness changes that would close the in-process threat model (separate process with a result channel, `O_APPEND` or pipe log, a cgroup kill, refusing more than one metric match). Nothing was measured; the kit is ENGINEERING_ONLY.

Code-Commit: 1db684711bf868a85ddb243dc18b88c4daf6a506
Verdict: ACCEPTED

Accepted commit: `1db684711bf868a85ddb243dc18b88c4daf6a506` (harness, round 6); report `8bce3ccd1280d8c2bb8c84c198129c1231f3903e`.
