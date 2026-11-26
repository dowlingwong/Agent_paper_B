Reviewed base: `08d065077d40087114452697d5d596e66a0578be` (harness branch `mac-trackg-port-ar-20261117b`; report at `432dbcfb8594b42d19217a3e5f65baf048b111c4` on `mac-trackg-u3-ar-20261117b`; accepted in round 8)

# Independent review record — Track G U3 port kit, suite autoresearch (autoresearch_fixedtokens)

**Unit.** The port kit for the autoresearch T1 candidate of the Ada census plan: `nodes/autoresearch_fixedtokens/`, `configs/trackg/nodes/autoresearch_fixedtokens.yaml`, `tests/trackg/test_port_autoresearch.py` and the shared `tests/trackg/port_support.py` / `port_smoke_gpu.py` on the harness branch (base `717ad835`), and on the paper branch (base `main` `26177d82`) the port checklist's section F (`b715e110`, moved after section E) and the report `docs/r1/reports/TRACKG_U3_PORT_AUTORESEARCH_20261117.md`. Round 1 reviewed the first harness branch `mac-trackg-port-ar-20261117` (tip `5eac980`) and report branch `mac-trackg-u3-ar-20261117` (`9222655b`); the `…b` branches continue from them.

**Authority.** R1-TRACKG-PORT-OWNER and R1-TRACKG-LICENCES (`main` `26177d82`; `author-decisions-20261117b` @
`33c82351`); the user's queue of 17 Nov (item 4) on `author-decisions-20261117b` @ `45fb94cc`.

**Process.** Two independent reviewers (separate agents that did not write the code): one for round 1, one for rounds 2–8. Rounds 4–8 also reviewed changes shared with the MLAgentBench and MLGym kits after their reviews; rounds 4–8 each confirmed changes made after the previous acceptance. The reviewers edited, committed and pushed nothing. The round texts are reproduced below
as delivered, as block quotes, so that only this record's closing lines are read as the acceptance.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | harness `5eac980`, report `9222655b` | NOT ACCEPTED (4 major, 8 minor) |
| 2 | harness `4f705e5e`, report `03e34a23` | NOT ACCEPTED (3 major, minor and notes) |
| 3 | harness `735aacca`, report `5d8382f0` | ACCEPTED (6 minor, 2 notes) |
| 4 | harness `d6e64927`, report `a7de1f39` | ACCEPTED (2 minor, 1 note) |
| 5 | harness `b3a08ff0`, report `ab9a944f` | ACCEPTED (3 minor) |
| 6 | harness `07bb2bc6`, report `bc1ef956` | ACCEPTED (1 minor, 1 note) |
| 7 | harness `51d53e5c`, report `70fee30c` | ACCEPTED (1 minor) |
| 8 | harness `08d06507`, report `432dbcfb` | ACCEPTED (1 minor) |

---

## Round 1 (harness `5eac980`, report `9222655b`)

> REVIEW: Track G U3 port kit, suite autoresearch (node autoresearch_fixedtokens)
> Harness branch mac-trackg-port-ar-20261117 @ 5eac980 (base 717ad835); report on mac-trackg-u3-ar-20261117 @ 9222655b (base main 16185b0b). Reviewer: an independent agent (Claude). Nothing was edited, committed or pushed. Scratch files are only under /tmp/rv_ar/.
>
> WHAT CHECKS OUT (verified against the code and the sources, not the report)
>
> - **SHAs and scope.** Every SHA the report cites resolves as stated: 5eac980263…, 9fb6b483…, 717ad835, 16185b0b. The branch only adds 16 files and changes no existing harness file.
> - **Node spec (checklist A).**
>   - The strict loader accepts it.
>   - Scopes: `train.py` is editable. Frozen are the wrapper, `ar_budget.py`, `ar_data.py`, `prepare.py`, `prepare_data.py`, requirements, NOTICE, `data/` and `representative_edits/`. `allow_new_files: false`.
>   - No frozen script sits in an editable directory: the only editable entry is a single file.
>   - `metric_regex` is `^AR_METRIC val_bpb=(\S+)$`, anchored. The direction is minimize.
>   - `loss_regex` matches train.py's real progress lines. I confirmed this against the baseline run.log.
>   - Not test-scored, which is correct: autoresearch has no test split.
>   - Determinism is at the defaults. `seed_env` names two different variables. `kind: tokens`, 32,768,000, and no time-word keys.
> - **Fidelity to the source.** The harness's prepare.py is byte-identical to `nodes/autoresearch-macos/prepare.py`. The train.py diff against the harness copy contains exactly the changes listed in the docstring: token schedule, fetch per micro-step, seeding moved to the wrapper, newline progress lines, final evaluation moved to the wrapper, allocator setting removed.
> - **Wrapper.**
>   - It runs train.py in-process and enforces "served == --tokens". I triggered exit 3 by editing train.py to run one step fewer.
>   - It checks `AR_BUDGET_VALUE` and seeds from `AR_TRAIN_SEED`.
>   - It prints `AR_METRIC` after train.py returns, from frozen code only.
>   - Evaluation matches the suite: `prepare.evaluate_bpb` with `DEVICE_BATCH_SIZE`, under the same bf16 autocast as upstream.
>   - No `cudnn.benchmark` anywhere. No test leakage under the baseline code: the train loader excludes `shard_06542`.
>   - The data manifest is verified on every run. Data go through a symlink, and setup is a one-off step.
> - **Representative edits (checklist C).**
>   - E1 to E4 are in scope, apply cleanly, are not inert and are not duplicates.
>   - They were committed together with `manifest.json` in 9fb6b48, before any run.
>   - The diff and manifest sha256 values in the report match the files. Manifest sha256: 05124871…ef7ba.
>   - Re-declaring under Python 3.12 reproduces the manifest byte for byte. Under 3.13 only the three AST-normalised code-state fields differ, so the report's Python-version finding is real.
> - **Tests.**
>   - Python 3.13 harness env: the port test file gives 5 passed, 1 skipped (the smoke). The whole `tests/trackg` gives 178 passed, 1 skipped, as the report says.
>   - Python 3.12 port env, full file including the synthetic smoke: 6 passed (384 s on a contended CPU).
>   - The smoke metrics reproduce the report's table exactly: 2.187568, 2.185285, 2.193791, 2.192003, 2.203346. The repeated baseline is identical, the broken diff is divergent (`non_finite_loss`), the frozen diff is refused with `scope_violation`, and `not_forced` is `[dataloader_workers]`.
>   - Whole `tests/trackg` under 3.12: only `test_trackg_t0_identity::…byte_identical…` fails, and it fails the same way on the unchanged base `/tmp/pb/wt/tgv2` @ 717ad83. That matches the report.
>   - `port_support.py` is identical on the ar, mlab and mlgym branches (sha 3258c351…).
> - **Budget estimate is plausible.** `estimate_flops` gives 5.66e7 FLOP/token at depth 4, so 1.86e15 FLOP in total, which is about 62 s at 30 TFLOP/s effective. It is still only an estimate.
> - **Tokenizer determinism.** Training it three times on the same shards gave identical `tokenizer.pkl` and `token_bytes.pt` bytes.
>
> FINDINGS
>
> 1. **MAJOR. The validation split is an unbudgeted training source inside train.py, and the run counts as `ok`.**
>    - Evidence: `nodes/autoresearch_fixedtokens/ar_budget.py:27-28` (`if split != "train": return loader`) passes the "val" loader through unchanged at any time. train.py already imports the public `make_dataloader` (`train.py:44`).
>    - I demonstrated it in a copy of the smoke node (`/tmp/rv_ar/adv/a`): after the budgeted loop, train.py trained one more optimizer step on 131,072 tokens from `make_dataloader(..., 'val')`. The wrapper printed `AR_TOKENS consumed=65536` and `AR_METRIC`, and exited 0.
>    - Why it matters: `shard_06542` is the only metric data (there is no test split). This path escapes the token budget and trains on the evaluation set while looking like ordinary API use. The report (line 30 and §Known limit) presents the budget as enforced by the loader and lists only forged lines and patched functions as limits.
>    - Fix:
>      - In `ar_budget`, add a frozen flag that the wrapper sets around `runpy.run_path`. While it is set, `make(..., split="val")` raises `BudgetExhausted` (or a distinct exception, so the run is divergent). The wrapper clears the flag before `evaluate_bpb`.
>      - Add a synthetic test that a train.py requesting "val" fails.
>      - State the remaining in-process limits in the report (finding 8).
>
> 2. **MAJOR. `prepare_data.py` accepts a partial download silently and can wedge itself.**
>    - Evidence: `prepare.py:123-128`. `download_data` only prints "ok/len shards ready" and never raises on failed shards.
>    - `prepare_data.py:39-46` then trains the tokenizer on whatever shards exist and writes a manifest of the files present. That manifest still claims `num_shards: 10` (line 43).
>    - The wrapper's and setup's required list (`run_fixed_budget.py:56-57`, `prepare_data.py:48`) contains only the validation shard and the tokenizer.
>    - Consequences:
>      - With 9 of 10 training shards, the census and G.1b get a different tokenizer, data stream and baseline, and the run still verifies as `ok`.
>      - If the validation shard fails, the manifest is already written (`open("x")`), so every rerun just fails verification (exit 5). Recovery needs a deletion or a new directory.
>      - Pre-existing extra shards in `--out` (for example a reused `~/.cache/autoresearch`) are also taken silently.
>    - Fix:
>      - Before tokenizer training, require exactly `data/shard_00000…00009.parquet` plus `shard_06542.parquet`. Otherwise stop without writing a manifest.
>      - Refuse an `--out` that holds any other parquet file.
>      - Add all 11 shard names to the required list in both scripts.
>      - Write the manifest only after the tokenizer sanity check.
>
> 3. **MAJOR. With a token budget, ordinary model-size proposals will be classed as `infrastructure_failure` (timeout), and the report does not raise this.**
>    - Evidence: the editable train.py sets the model size (`DEPTH`, `ASPECT_RATIO`), while the budget fixes only tokens. The runner timeout is 3 × the measured baseline run (checklist D). `outcome.py:127-128` classes a timeout as `infrastructure_failure`, which is re-run and not deduplicated (`runner.py`, register step).
>    - From `estimate_flops`, training FLOPs relative to the baseline are about 2.5× for E2 (depth 6) and about 4.9× for depth 8, which is upstream autoresearch's own default and the most likely proposal.
>    - Such proposals overrun the 3× timeout and R1-BX-D5's ~5 min closed-loop bound. They would then be recorded as infrastructure failures and re-run, not labelled as the proposal's effect.
>    - The report's open point 1 (line 179) only says that compute "varies".
>    - Fix: raise it as an open point for the author with these numbers, and propose one of the following:
>      - a frozen compute cap, for example the wrapper or `ar_budget` refusing, with a distinct non-zero exit (so the run is divergent), a model whose `num_flops_per_token` or parameter count exceeds k× the baseline;
>      - a FLOP budget in place of a token budget;
>      - a node-specific timeout basis set from the largest allowed configuration.
>    - Until the author decides, state that over-compute timeouts are not infrastructure failures.
>
> 4. **MAJOR. Real deviations of the baseline from the suite are not stated, and the reason given for choosing the fork is inaccurate.**
>    - Evidence, upstream `/tmp/suites/autoresearch/train.py` @ 228791f against the fork baseline:
>      - `DEPTH` 8 → 4;
>      - `TOTAL_BATCH_SIZE` 2^19 → 2^16;
>      - `DEVICE_BATCH_SIZE` 128 → 16;
>      - `WINDOW_PATTERN` "SSSL" → "L";
>      - upstream's NaN fast-fail (`math.isnan(...) or > 100`) reduced to `> 100` (`train.py:655`);
>      - torch 2.9.1/cu128 (upstream `pyproject.toml:16`) → 2.6.0;
>      - FA3 → SDPA with an explicit mask.
>    - The report (line 18) calls depth 4 / width 256 "autoresearch's small GPT" and names only the SDPA change.
>    - Report line 9 says upstream's FA3 kernels are "Hopper-oriented". In fact upstream loads `varunneal/flash-attention-3` on Hopper and `kernels-community/flash-attn3` on other GPUs (upstream `train.py:20-24`). The real obstacles are hub access at import time, the `kernels` package and the torch 2.9.1 pin.
>    - Mitigation worth stating: upstream's README (lines 71-79) recommends exactly this kind of reduction (DEPTH 4, "L", smaller batch) for small compute.
>    - Fix: list every fork-versus-upstream delta in the report and NOTICE, cite the README guidance as the reason, and correct the FA3 rationale.
>
> 5. **MINOR. The report claims artefacts that do not exist.**
>    - Line 3 says the port "was independently reviewed (see `docs/r1/reviews/TRACKG_U3_PORT_AUTORESEARCH_REVIEW_20261117.md`)". No such file exists, and the commit message says "Independent review pending".
>    - Line 56 cites `declare_edits_output.txt` "kept with the bundle". No such file exists in either worktree.
>    - Fix: say "Review: pending" until a review is filed, and either commit the script output or drop the reference.
>
> 6. **MINOR. The source history is misstated.**
>    - Report line 9 and `NOTICE.md:5` say only the platform check changed at d075bb3.
>    - `git diff fb405e1 717ad835 -- nodes/autoresearch-macos/prepare.py` shows that d075bb3 also added the `AUTORESEARCH_CACHE_DIR` override (prepare.py:50-53). The port depends on that local change. So the frozen prepare.py is the harness's modified copy, not the fork's file.
>    - Fix: state both changes.
>
> 7. **MINOR. The allocator setting does nothing under the pinned torch.**
>    - Evidence: `run_command` (yaml:32) sets `PYTORCH_ALLOC_CONF`. The torch 2.6.0 libraries contain only `PYTORCH_CUDA_ALLOC_CONF`; I checked `libc10_cuda.so` and `libtorch_cuda.so` by string search.
>    - Under the requirements' torch==2.6.0 the setting has no effect, the same as the fork. It becomes active on torch ≥ 2.9, so memory behaviour could differ between Ada and L40S if their torch versions differ.
>    - Report line 41 implies it is effective.
>    - Fix: use `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (read by both versions), or drop it and say so. Either way, pin one torch version for both hosts.
>
> 8. **MINOR. The list of known in-process limits is incomplete, and one hole is cheap to narrow.**
>    - Demonstrated: train.py setting `ar_budget._served = TRAIN_TOKENS` with zero steps ran `ok` (`/tmp/rv_ar/adv/b`).
>    - From reading the code: train.py can `print("AR_METRIC val_bpb=…"); sys.exit(0)`. The `SystemExit` propagates out of `runpy.run_path` (`run_fixed_budget.py:76`), skipping the budget check and the real metric line. The parquet files can also be read directly.
>    - Fix:
>      - Catch `BaseException` around `runpy.run_path` and `fail(EXIT_BAD_EDITABLE_API)`.
>      - Keep the counter out of a writable module global, for example in a closure.
>      - List the remaining limits in the report.
>
> 9. **MINOR. No data source revision is recorded, which matters across hosts.**
>    - `BASE_URL` ends in `resolve/main` (prepare.py:56), and `prepare_data.py:43` records only that URL. The common-design text (report line 91, "the source revision") does not hold for this node.
>    - Separate setups on Ada and on the L40S host could therefore produce different data and tokenizers.
>    - Fix: resolve and record the HF dataset commit at setup, or copy the prepared directory to the L40S host. After the census, pin the expected `data_manifest.json` sha256 in the wrapper.
>
> 10. **MINOR. The setup command needs a guard.** With `AR_TRACKG_DATA_ROOT` unset, `setup_command` (yaml:31) writes to `/autoresearch_fixedtokens`. Fix: have `prepare_data.py` refuse an `--out` outside a set data root, or check the variable in the command.
>
> 11. **MINOR. Report wording.**
>     - Line 35: the fork's "loss > 100 → exit 1" does not catch NaN (`nan > 100` is false). NaN is caught by `loss_regex` or by a non-finite `val_bpb`.
>     - The licence is "MIT" as stated in the README of both upstream and the fork. Neither has a LICENSE file or copyright line; NOTICE should say so for U1.
>     - The local torch was 2.6.0+cu124 run on CPU.
>     - The report should note that changing the budget after the census means a new spec hash and a new manifest. Both the `run_budget` and `node_spec_sha256` fields are in the manifest.
>
> 12. **MINOR. Test coverage is thinner than the report implies.**
>     - Nothing tests the wrapper's exit-3 path or `BudgetExhausted`. I verified exit 3 by hand.
>     - `not_forced == ["dataloader_workers"]` is asserted only for the per-edit records, not for the smoke-campaign records shown in the report's table.
>     - Fix: add synthetic tests for an under-budget run (exit 3), an over-request, and a val request after finding 1.
>
> VERDICT: NOT ACCEPTED

---

## Round 2 (harness `4f705e5e`, report `03e34a23`)

> # Review round 2: Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: NOT ACCEPTED**
>
> What was reviewed:
> - Harness branch `mac-trackg-port-ar-20261117b` at tip `4f705e5e` (base `717ad835`; round-2 commits `38854b9e` and `4f705e5e`).
> - Paper branch `mac-trackg-u3-ar-20261117b`: `b715e110` (checklist section F) and `03e34a23` (report).
>
> Reviewer: an independent agent (Claude), round 2. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, scripts in `scripts/`.
>
> ## What checks out (verified against the code)
>
> - **SHAs.** Every SHA in the report resolves as stated: `9fb6b483`, `5eac9802`, `38854b9e`, tip `4f705e5e0f7d…`, base `717ad835`.
>   - The branch only adds files; no existing harness file changes.
>   - R1-TRACKG-PORT-OWNER is on `26177d82`. R1-TRACKG-LICENCES is on `author-decisions-20261117b` @ `33c82351`, an ancestor of the branch's current head `45fb94cc`.
> - **Tests.** The given command (Python 3.12, torch 2.6.0+cu124, CPU) gives **12 passed in 259.5 s**, as the report says.
> - **Edits manifest.** `manifest.json` has sha256 `088e80f6…6106`, as stated.
>   - E1–E4 have the stated hashes and are unchanged since round 1.
>   - The only manifest change is `node_spec_sha256`.
>   - The round-1 manifest (`05124871…`) is kept under `superseded/`.
> - **Wrapper and budget.** The wrapper matches the report: exits 3, 7, 8 and 4, a closure counter, `BaseException` caught around `runpy.run_path`, and validation opened only after `train.py` returns.
>   - A probe that catches `ValidationRequested` or `BudgetExhausted` inside `train.py` gets no data beyond the budget. The refusal does not depend on the exception propagating.
> - **Fork-versus-upstream deltas** (in `LICENCES.md` and the report) are correct against upstream `228791fb`:
>   - DEPTH, TOTAL_BATCH_SIZE, DEVICE_BATCH_SIZE, WINDOW_PATTERN;
>   - the NaN fast-fail;
>   - SDPA instead of FA3;
>   - torch 2.9.1/cu128.
>   - The FA3 hub-repo rationale is now correct.
> - **`prepare_data.py`.**
>   - It requires exactly the 11 shards before tokenizer training.
>   - It refuses an `--out` that already holds parquet files, and an `--out` outside `$AR_TRACKG_DATA_ROOT`. The setup command also tests the variable.
>   - The manifest is written after the tokenizer.
>   - The dataset revision is checked against U1's `915333b` and recorded.
>   - `REQUIRED_FILES` agrees between the wrapper and setup (tested).
> - **Licence record.** `LICENCES.md` matches U1 §2 and §7:
>   - README-only MIT, no LICENSE file, GitHub `license: null`;
>   - card MIT, with corpus provenance undocumented;
>   - about 1.0 GB;
>   - no data committed (now tested statically).
> - **Checklist section F** covers what the user asked for: licence, source URL, dataset hash, never redistributed, download script plus hash only.
>
> ## Round-1 findings: status
>
> | # | Round-1 finding (sev.) | Status in round 2 |
> |---|---|---|
> | 1 | Val split usable as unbudgeted training data (MAJOR) | **Fixed for the API route.** `make_dataloader(...,'val')` exits 8 and is tested. Other routes remain; see new findings 1 and 4. |
> | 2 | Partial download accepted, setup can wedge (MAJOR) | **Fixed.** Exact shard set, no manifest on failure, reuse refused, manifest last. Recovery after a failure needs a manual move-aside, and the error message says so. |
> | 3 | Over-compute proposals become `infrastructure_failure` (MAJOR, may be raised as an open point) | **Correctly raised** as open point 1, with numbers and options a/b/c. Its interim rule cannot be applied by the harness (new finding 10). |
> | 4 | Baseline deltas from upstream unstated; FA3 rationale wrong (MAJOR) | **Fixed** (`LICENCES.md`, report). Small device-portability deltas are unlisted (new finding 11, NOTE). |
> | 5 | Report cites non-existent artefacts (MINOR) | **Fixed.** "once filed"; the `declare_edits_output.txt` reference was removed. |
> | 6 | d075bb3 history misstated (MINOR) | **Fixed.** |
> | 7 | Allocator variable inert under torch 2.6 (MINOR) | **Fixed.** `PYTORCH_CUDA_ALLOC_CONF`, plus open point 3 (one torch for both hosts). |
> | 8 | In-process limits incomplete; `sys.exit` skip; writable counter (MINOR) | **Partly fixed.** `BaseException` is caught and the counter is a closure. The limits list is still materially inaccurate: forgery does not need to fail (new finding 1). |
> | 9 | No data revision recorded (MINOR) | **Fixed, with a caveat.** The pin relies on the `fork` start method (new finding 5). The manifest sha256 is not yet pinned (it is planned after the census). |
> | 10 | Setup writes to `/autoresearch_fixedtokens` if the variable is unset (MINOR) | **Fixed** (tested). |
> | 11 | Report wording: NaN, licence file, torch build, budget change (MINOR) | **Fixed.** |
> | 12 | Tests for exits 3/7/over-request, `not_forced` on smoke records (MINOR) | **Mostly fixed.** Exits 3/7/8/4 are tested. `not_forced` is still asserted only for the per-edit E1–E4 records (new finding 7). |
>
> ## New findings
>
> ### 1. MAJOR: a forged metric ends `ok` with every wrapper check passed, but the report says forging needs a failure
>
> **Location.**
> - `run_fixed_budget.py` (end of `main`, docstring "Known in-process limits").
> - Report §Budget enforcement, "Remaining in-process limits … print forged `AR_` lines before failing … The checks and the line order narrow these".
> - `outcome.py:182`: the classifier takes the **last** `AR_METRIC` match, and for `kind: tokens` it never consults `AR_TOKENS` (no `steps_regex`, `budget_steps=None`).
>
> **Demonstrated.** Each probe ran on a synthetic copy through the real wrapper and was classified with `outcome.classify_run` and the node's regexes:
> - `atexit.register(lambda: print("AR_METRIC val_bpb=0.100000"))` after consuming the budget gives exit 0. The log has `AR_TOKENS consumed=512`, then the real `AR_METRIC val_bpb=2.232539`, then the forged line. Outcome: **`ok 0.1`**.
> - `sys.stdout` replaced by a filter that rewrites `AR_METRIC val_bpb=\S+` gives the wrapper's own line printed as `0.100000`. Outcome: **`ok 0.1`**.
> - `print("AR_METRIC val_bpb=0.100000"); os._exit(0)` with zero training gives no `AR_TOKENS` line, exit 0. Outcome: **`ok 0.1`**.
>
> **Failure scenario.** The first two forge the value *after* all budget checks have passed, so "line order" gives no protection. The third is the `sys.exit` case of round-1 finding 8, unchanged in effect. None of them "fails".
>
> **Fix.**
> - **(a)** Take `wfd = os.dup(1)` before `runpy.run_path`. Write `AR_TOKENS` and `AR_METRIC` with `os.write(wfd, …)`, not `print`. End `main` with `os._exit(0)` straight after the metric write. This skips `atexit` handlers, bypasses a replaced `sys.stdout`, and kills late threads.
> - **(b)** Correct the limits list: say that a forged line followed by `os._exit(0)` is classified `ok` and cannot be stopped in-process, and that the `AR_TOKENS` line is informational only (the harness does not check it for token budgets).
> - **(c)** The full fix, for the author to weigh: run `train.py` in a child process that hands back the model's `state_dict`, and evaluate in the parent.
>
> ### 2. MAJOR: a run can change the shared data persistently; `verify` ignores extra files and trusts a rewritable manifest; read-only is only a deterrent
>
> **Location.**
> - `ar_data.verify` checks only the files the manifest lists.
> - `prepare.list_parquet_files` / `_document_batches("train")` train on **every** parquet file in `data/` except `shard_06542`.
> - `ar_data.make_read_only` (`4f705e5e`); `prepare_data.py` comment "runs cannot change the shared data or leave files in it"; report "the directory is then made read-only".
> - Every working copy links the same data directory (`runner.py` copies with `symlinks=True`).
>
> **Demonstrated** (`scripts/ro_test.py`, on a copy owned by uid 65534, run as that uid after `make_read_only`):
> - a plain write is refused (EACCES);
> - after `os.chmod(dir, 0o755)`, which the owner may always do, a copy of the validation shard planted as `data/shard_00010.parquet` passes `verify` with an unchanged manifest digest. `list_parquet_files()` then includes it in the training split;
> - replacing `shard_06542.parquet` and rewriting `data_manifest.json` also passes `verify`. Only the printed `AR_DATA manifest_sha256` changes, and nothing compares it.
> - As root, which is how the tests here ran, the permission bits do not apply at all.
>
> **Failure scenario.**
> - One proposal's `train.py` (deliberate or a stray "cache the data" edit) writes into `data/`.
> - Every later run, including baselines and the census, then trains on the validation text, or is evaluated on altered data.
> - Nothing flags it, and it is not attributed to the run that caused it.
> - This is worse than the in-process limits, which affect only one run, and it is not in the report's limits list.
>
> **Fix.**
> - `verify` must refuse any file under the data directory that the manifest does not list (exact set under `data/` and `tokenizer/`).
> - After the census, pin the expected manifest sha256 in the frozen wrapper, or have the census record and compare it per run. Until then, the experiment agent should compare `AR_DATA manifest_sha256` across runs.
> - On Ada, prefer data owned by a different user or a read-only bind mount.
> - State the remaining limit in the report and soften the "cannot change" comment.
>
> ### 3. MAJOR: the "frozen metric" is computed by editable model code; an honest-looking edit can leak the targets
>
> **Location.**
> - `prepare.evaluate_bpb` calls `model(x, y, reduction='none')`, so the per-token loss comes from the editable `GPT.forward`.
> - Attention causality is the editable `is_causal=True` at `train.py:130`.
> - Report and spec: "the frozen files hold … the metric".
>
> **Demonstrated** (wrapper plus classifier):
> - a model whose `forward` returns zero loss in eval mode gives **`ok 0.0`**;
> - a model that uses only the inputs `x` but looks one position ahead (crude non-causal attention, no use of `y`) gives **`ok 0.017881`**, against 2.23 for the same tiny model without the peek.
> - A one-token edit `is_causal=True` → `False` runs `ok` with no diff refusal. At 8 CPU steps it was not yet distinguishable (1.9496 against 1.9511 baseline). At the full 500-step budget, bidirectional attention on next-token prediction is expected to learn to copy, and to give a spuriously large "improvement".
>
> **Failure scenario.**
> - An LLM proposal such as "use bidirectional/full attention" or "remove the mask for speed" is recorded as the best edit and kept by the loop.
> - Its labels contaminate Paper B's control data.
> - This weakness is inherited from upstream autoresearch, but the port presents the metric as frozen.
>
> **Fix.**
> - Add a frozen causality probe in the wrapper before `evaluate_bpb`. On one validation batch, compare `model(x)` logits at positions ≤ t with those on a copy of `x` whose positions > t are perturbed. Any difference means exit with its own code (divergent).
> - Check that `model(x, y, 'none')` equals cross-entropy computed in frozen code from `model(x)` logits, within tolerance. This catches zero or forged losses and the use of `y`.
> - At minimum, state this in the limits and tell the census/G.1b to flag implausible `val_bpb` drops.
>
> ### 4. MINOR: further validation and unbudgeted routes are not in the limits list; exits 7/8 are not guaranteed
>
> **Demonstrated** (all `ok` with the baseline metric; the extra data simply went unused):
> - `prepare._document_batches("val")` leaked 128 validation documents;
> - `_document_batches("train")` served 528 unbudgeted training documents;
> - `importlib.reload(prepare)` restores the original `make_dataloader` and leaked 256 validation tokens;
> - the closure route leaked 256 validation tokens (already listed);
> - a non-daemon thread waits for `validation_open` and runs while `evaluate_bpb` runs, so it could train on validation during evaluation;
> - catching `ValidationRequested` or `BudgetExhausted` inside `train.py` gives exit 0 instead of 8 or 7. This is harmless, since no data are served, but the report's "→ exit 7 / exit 8" holds only if the exception propagates.
>
> **Fix.**
> - Add these routes to the limits list.
> - Optionally, while `train.py` runs, swap `prepare._document_batches` for a guard that only the budgeted loader may pass.
> - `os._exit` at the end (finding 1a) also ends stray threads.
>
> ### 5. MINOR: the dataset-revision pin depends on the multiprocessing start method
>
> **Location.** `prepare_data.py` sets `prepare.BASE_URL` in the parent. `prepare.download_data` downloads in a `multiprocessing.Pool`.
>
> **Demonstrated** (`/tmp/rv_ar2/mp`): a patched module global reaches the workers under `fork`, but is `resolve/main` under `spawn` and `forkserver`.
> - `fork` is the default on Linux for Python ≤ 3.13.
> - `forkserver` is the default on Linux from Python 3.14, and `spawn` on macOS.
> - There, the shards would silently come from `main` while the manifest records the pinned revision.
>
> **Fix.** Call `prepare.download_single_shard(i)` in-process in a loop, or force `multiprocessing.set_start_method("fork")` before downloading. Optionally check each shard against the hub's LFS sha256 at that revision, so the hashes are pinned in advance, as checklist F prefers.
>
> ### 6. MINOR: "identical on the three branches" is not true at the current tips
>
> **Location.** Report §Design common: "one shared `tests/trackg/port_support.py`, identical on the three branches"; "`ar_data.py`, identical in all nodes".
>
> **Evidence.**
> - The ar and mlab `…b` branches have `port_support.py` with sha `1fba4cb1…` and `ar_data.py` with sha `4da22f03…`.
> - `mac-trackg-port-mlgym-20261117b` @ `bfc4624` (no round-2 commits) still has `port_support.py` `3258c351…` and `ar_data.py` `c81c6536…`, which lacks `make_read_only`.
> - `port_smoke_gpu.py` imports `test_port_mlgym`.
>
> **Fix.** Synchronise before bundling, or word the claim as a condition. Once all nodes share one tree, the `SHARED_FROZEN` identity check will otherwise fail.
>
> ### 7. MINOR: residue of round-1 finding 12
>
> **Location.** `check_smoke` asserts `not_forced == ["dataloader_workers"]` only for the per-edit E1–E4 records. It does not assert it for the smoke-campaign baseline, broken or E1 records, nor for the repeat baseline B2. The report's test list and checklist E imply it is checked for the run records generally.
>
> **Fix.** Assert it for `baseline`, `broken`, `first` and `repeat` as well.
>
> ### 8. NOTE: `LICENCES.md` paraphrases MIT rather than carrying a licence text
>
> U1 §2 says "A licence text should be copied into the port kit". The paraphrase also refers to "the copyright notice", which does not exist upstream.
>
> **Fix.** Include the standard MIT text verbatim, with "no copyright holder named upstream; text supplied by the port as the README's 'MIT' declaration", or label the paragraph explicitly as a summary.
>
> ### 9. NOTE: section F is placed between D and E
>
> The checklist now reads A, B, C, D, F, E. This is cosmetic; consider renumbering or moving F after E.
>
> ### 10. NOTE: the open-point-1 interim rule cannot be enforced by the harness
>
> "Until you decide, an over-compute timeout … must be read as the proposal's cost, not re-run". The runner classifies a timeout as `infrastructure_failure` and re-runs it automatically.
>
> **Fix.** Say explicitly that the experiment agent must handle this by hand (or by a node change) before G.1b. It does not affect the census of E1–E4: E2 is about 2.5× the baseline, inside the 3× timeout.
>
> ### 11. NOTE: smaller fork deltas are not listed
>
> The fork also changes:
> - device selection (MPS/CPU paths);
> - where `torch.compile` is applied (the model only on CUDA; the fused optimizer steps compiled in the constructor instead of by decorator);
> - dtype/device casts of the optimizer's scalar tensors.
>
> Behaviour on CUDA should be equivalent, but one line in `LICENCES.md` would make the list complete.
>
> ## Summary
>
> The four round-1 MAJORs are fixed or correctly raised as an open point, and the report's descriptions of the code are accurate apart from the points above.
>
> Acceptance is blocked by three new MAJORs, which are about metric and data integrity rather than the round-1 items:
> - **Finding 1.** A forged metric is classified `ok` even after every check passes. Cheap narrowing: os-level write plus `os._exit`.
> - **Finding 2.** A run can contaminate the shared data for every later run, undetected. Exact-set verify plus a pinned manifest digest.
> - **Finding 3.** The metric's loss and causality are editable. Frozen causality and cross-entropy checks.
>
> For each, the fix is either a small frozen-code change or an honest statement in the limits list for the author to accept. Findings 4–7 are small.

---

## Round 3 (harness `735aacca`, report `5d8382f0`)

> # Review round 3: Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> All three round-2 MAJORs are fixed. What remains is either listed in the report or a wording gap. The new findings below are MINOR or NOTE. I recommend fixing findings 1–3 and 8 before the census; each is a few lines of frozen code or report text.
>
> **This verdict covers the committed tips only.** After all my checks had finished (the last log is at 05:28), the harness worktree showed **uncommitted** changes by someone else, not by me: `ar_data.py`, `prepare_data.py`, `run_fixed_budget.py` and `port_support.py`, modified at 05:29–05:30, while a separate wrapper run was in progress. They are not reviewed here. From a glance at the diff they appear to reword the limits (the thread race of finding 8) and to move `finish()`. Once committed, they need a short delta check.
>
> **What was reviewed:**
> - Harness branch `mac-trackg-port-ar-20261117b` @ `735aaccaf433…` (round 3 diff `4f705e5e..735aacca`).
> - Paper branch `mac-trackg-u3-ar-20261117b` @ `5d8382f0` (report round 3; checklist section F moved after E).
>
> Reviewer: an independent agent (Claude), round 3. No repository was changed. Scratch is only under `/tmp/rv_ar2/`; `tmp/` was emptied at the end. The probes are in `probes/` (the round-2 set plus new ones), their logs in `adv/*.log`, and the probe driver is `scripts/run_probes.py`. The driver runs each probe through the real round-3 wrapper on a synthetic copy and classifies it with the harness's `classify_run` and the node's regexes.
>
> ## Checks that pass
>
> - **Tests.** The given command (Python 3.12, torch 2.6 CPU) gives **16 passed in 537 s**. This matches the report; the time is longer here because my probes ran in parallel.
> - **Smoke table.** The run records of the test smoke match the report's table: baseline 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, repeat baseline 2.18766, broken diff `non_finite_loss`. `not_forced` is `[dataloader_workers]` on every executed record.
> - **Manifest.** It is unchanged (`088e80f6…`) and the test reproduces it, as the report says.
> - **Frozen metric for an honest model.** On the real `train.py` (1 step, CPU, eager), the wrapper's frozen metric and the original `prepare.evaluate_bpb` give the same model **bit-identical** values: 2.1876603331644993 both, difference 0.000e+00. The check was a scratch copy of the wrapper that computes both.
> - **Shared files across branches.** All three `…b` tips now share `port_support.py` (`e2a8ebf3…`), `port_smoke_gpu.py` (`347e3a4b…`) and `ar_data.py` (`53cfd13b…`).
> - **`LICENCES.md`** carries the standard MIT text with a bracketed copyright line, plus the small fork differences.
> - **Checklist.** Section F now follows E, with its content unchanged.
>
> ## Round-2 findings: status
>
> | # | Round-2 finding (sev.) | Status | Evidence |
> |---|---|---|---|
> | 1 | Forged metric ends `ok` after all checks (MAJOR) | **Fixed** for `atexit` and stdout; the `os._exit` residual is listed. A thread race remains (new finding 8). | An `atexit` line gives `ok 2.232539` (the wrapper's value, the forged line is absent). A `sys.stdout` rewrite filter also gives `ok 2.232539`. A forged line plus `os._exit(0)`, or `ar_data.emit` forged plus `os._exit`, still gives `ok 0.1`; both are now stated in the report as a limit, including that `AR_TOKENS` is not read for token budgets. |
> | 2 | Shared data changeable, extra files ignored (MAJOR) | **Fixed**; the residual is listed. | A planted `shard_00010.parquet` makes the next run exit 5 ("files the manifest does not list"). Owner chmod and manifest rewrite are stated as not prevented, with the Ada mitigation (another owner or a read-only mount, then pin the digest). See new finding 2 on which run gets blamed. |
> | 3 | Metric computed by editable model; look-ahead leaks (MAJOR) | **Fixed**, with a residual. | A zero edited loss gives `ok 2.232812`: the loss is ignored. A one-ahead peek model gives **exit 9** (logits changed by 20). Residuals: new findings 1 and 3–5. |
> | 4 | Other routes unlisted; exits 7/8 not guaranteed (MINOR) | **Fixed.** | Catching the refusal gives exit 8 ("and caught the refusal"). `_document_batches`, `reload`, the closure (including flipping `validation_open`, no violation recorded) and threads all still work, and all are listed. |
> | 5 | Revision pin depends on start method (MINOR) | **Fixed.** | `set_start_method("fork", force=True)` before the download; leftover `.tmp` files stop the setup. |
> | 6 | "Identical on three branches" false (MINOR) | **Fixed.** | See the hashes above. |
> | 7 | `not_forced` not checked everywhere (MINOR) | **Fixed.** | Now checked on every executed torch record and on the repeat baseline. |
> | 8 | MIT paraphrase (NOTE) | **Fixed.** | — |
> | 9 | Section F order (NOTE) | **Fixed.** | — |
> | 10 | Interim timeout rule unenforceable (NOTE) | **Fixed.** | Reworded as a proposal that needs a harness change or a recorded manual reclassification. |
> | 11 | Small fork deltas (NOTE) | **Fixed.** | — |
>
> ## New findings
>
> ### 1. MINOR: the causality probe is skipped whenever any logit is non-finite, so `-inf` masking turns it off
>
> **Location.** `run_fixed_budget.py`, `causality_probe`:
> ```python
> if not torch.isfinite(base.float()).all():
>     return  # a non-finite metric follows; nothing to compare
> ```
>
> **Demonstrated** (`probes/p_ninf_peek.py`). The one-ahead peek model from round 2 also sets one never-targeted vocabulary logit to `-inf`. Result: exit 0, **`ok 0.017881`**, against 2.23 for the honest stand-in.
>
> **Why it passes.** The comment's premise holds only for NaN. A NaN anywhere in a row makes that row's cross-entropy NaN, so the metric is non-finite. A `-inf` in a column that is never a target leaves the cross-entropy finite. Masking unused or reserved tokens to `-inf` is a common, honest-looking trick.
>
> **Fix.** Return early only on NaN, and compare in a way that treats equal infinities as equal, for example `d = (a - b).abs(); d[a == b] = 0`. Add the `-inf` peek model to `EVALUATED` in the tests.
>
> ### 2. MINOR: a planted file is blamed on the runs after it, not on the run that planted it
>
> **Location.** `ar_data.verify` is called only at the start of a run (`run_fixed_budget.py` before `train.py`). The spec's `infrastructure_log_patterns: []`.
>
> **Demonstrated** (`adv/w_plant`, a private data copy).
> - Run 1's `train.py` copies the validation shard to `data/shard_00010.parquet`. Run 1 then ends **`ok`** with its normal metric.
> - Run 2, an unchanged stand-in, exits 5. The harness classifies exit 5 as `divergent nonzero_exit`.
> - Every later run, baselines included, gets the same `divergent` label until someone repairs the directory. The contamination is now loud, but the labels go to innocent proposals.
> - Accidental writes are blocked by the read-only bits for a non-root owner, so this needs a deliberate chmod; hence MINOR.
>
> **Fix.**
> - Call `ar_data.verify(...)` again after `train.py` returns and before evaluation, so the run that planted the file fails itself with exit 5.
> - Declare an infrastructure pattern such as `'^AR_ERROR data '`, so that a corrupted data directory is classed `infrastructure_failure`, which also STOPs the loop, rather than `divergent`.
>
> ### 3. MINOR: the probe tolerance is loose for an exact property, and the measured difference is not recorded
>
> **Location.** `CAUSAL_ATOL = 0.05`; `PROBE_CUTS`.
>
> **Reasoning.**
> - For a causal model, the logits before the cut are a deterministic function of the earlier tokens alone. The ops are per row: projection GEMMs of a fixed shape, causal SDPA that skips or zeroes masked keys, RMS norm, rotary embeddings.
> - Under the spec's `deterministic_algorithms: true` and `:4096:8`, with the same compiled graph and the same shapes, the expected difference on GPU is **exactly 0**, not merely small. So bf16 or compile noise is not a reason for the 0.05 tolerance, and a tighter tolerance would not cause false refusals of honest causal models.
> - Conversely, 0.05 lets through a weak leak. A leak that moves the correct token's logit by up to 0.05 is worth up to about 0.05 nats per token, which is roughly 0.015–0.02 bpb at around 4 bytes per token. That is the size of real edit effects (the smoke edits differ by 0.002–0.015).
> - In practice a fully trained non-causal model is expected to move logits far beyond 0.05 and be caught. A real `is_causal=False` edit was **not** caught after 1 step (exit 0, 2.188013 against 2.187660), because the zero-initialised projections keep the leak negligible early on.
>
> **Fix.**
> - Print the probe's maximum difference on every run (`AR_INFO causal_max_diff=…`), and have the census confirm that it is 0, or of the order of 1e-6, on the GPU for the baseline and E1–E4.
> - Then lower the tolerance to about 1e-3.
> - If GPU differences turn out not to be 0, record the observed value and set the tolerance from it.
>
> ### 4. MINOR: the evaluation data and the metric's own torch calls can still be swapped with one line; the report's wording undersells this
>
> **Demonstrated.**
> - `prepare.VAL_FILENAME = "shard_00000.parquet"` in `train.py` gives `ok 2.223328`, against the baseline's 2.232539. The evaluation read a **training** shard, because the closure's loader resolves `prepare`'s module globals at call time. Only `get_token_bytes`, `MAX_SEQ_LEN` and `EVAL_TOKENS` are bound in advance.
> - `torch.nn.functional.cross_entropy` patched to return `orig * 0` gives **`ok 0.0`**: `frozen_bpb` looks up `F.cross_entropy` at call time.
> - Patching `ar_data.emit` gives `ok 0.1`.
> - All of these are deliberate edits, visible in the diff and in the same class as the listed "patch the wrapper's or prepare's functions".
>
> **Fix.**
> - Cheap and closes the `prepare` cases: snapshot `dict(vars(prepare))` before `runpy.run_path`, and restore it with `vars(prepare).update(snapshot)` just before `open_validation()`. This also undoes `importlib.reload(prepare)`, because the functions share that module dict.
> - Bind `F.cross_entropy` (and `emit`/`finish`) to locals before `train.py` runs.
> - Widen the limits wording to "functions or module globals of the wrapper, `ar_data`, `prepare` or torch".
>
> ### 5. MINOR: a model that updates its own weights inside `forward` trains on the validation shard during evaluation; this is not in the limits list
>
> **Demonstrated.** In `probes/p_dyneval.py`, a model runs a few SGD steps on each evaluation batch inside `forward` (`torch.enable_grad()` overrides the wrapper's `no_grad`). It passes the probe (`ok 2.232508`), because its small updates stay below 0.05. `p_dyneval_late.py` starts updating only after the probe's four calls and also passes (`ok 2.232570`).
> - Test-time training or dynamic evaluation is a known LM technique that an LLM proposer could plausibly offer as an honest edit. It is unbudgeted training on the metric data.
> - With a larger learning rate the probe would probably refuse it, but under the misleading message "not causal".
>
> **Fix.** Before the probe, take a checksum of `model.state_dict()` (parameters and buffers); compare it after the evaluation, and between the probe's calls. Any change exits with its own code. Also add stateful `forward` to the limits list.
>
> ### 6. MINOR: the editable contract changed from upstream, and the proposer is not told
>
> **Location.**
> - Upstream's `evaluate_bpb` contract is `model(x, y, reduction='none')`. The wrapper now requires `model(x)` to return full `(B, T, vocab)` logits; otherwise it exits 4 (divergent).
> - The editable `train.py` docstring does not say this, and `train.py` is unchanged in round 3.
>
> **Failure scenario.**
> - A common nanoGPT-style edit returns `logits[:, [-1], :]` when `targets is None`. That edit is harmless under upstream, but here it gets a `divergent` label.
> - Also, edits that change the training loss (label smoothing, z-loss, a softcap only in the loss branch) are now scored by true cross-entropy, not by their own loss. This is better, but it differs from upstream's semantics.
>
> **Fix.**
> - State both points as deviations from upstream in the report and in `LICENCES.md`'s delta list.
> - Make the contract visible to the proposer: in whatever it reads (a frozen note), or in the `train.py` docstring. Changing `train.py` needs a re-declaration of the manifest, because the code-state hashes cover it.
>
> ### 7. NOTE: the probe roughly triples evaluation's peak logits memory
>
> The probe holds `base` and `model(altered)` (each B·T·V fp32, 1 GiB at B=16) plus the difference slices, so the transient is about 3.5× one logits tensor. This is fine for the baseline on an L40S. For large `DEVICE_BATCH_SIZE` edits, compute the difference one cut at a time on the `[:, :cut]` slices and free them between cuts.
>
> ### 8. MINOR: a thread started by `train.py` can still have the last metric line; the committed report understates this
>
> **Location.**
> - `ar_data.emit` writes the wrapper's line, then `finish()` calls `os._exit(0)`.
> - The harness takes the last `AR_METRIC` match (`outcome.py`).
> - Committed report: "So an `atexit` handler cannot add a line after the wrapper's …". The limits list mentions only "keep a background thread running into the evaluation".
>
> **Demonstrated** (`probes/p_threadrace.py`, against a clean `git archive` of `735aacca`):
> - a daemon thread waits until validation opens, then writes `AR_METRIC val_bpb=0.100000` to fd 1 in a loop;
> - 3 runs gave `ok 2.232539` once and **`ok 0.1` twice**: the forged line landed after the wrapper's line, before `os._exit`;
> - this is deliberate code (`threading`, `AR_METRIC` in the diff), in the same class as the listed forged-line-plus-`os._exit` case.
>
> **Fix.**
> - In the report, state that such a thread can decide the metric. The uncommitted worktree text appears to do this.
> - Narrow it in the wrapper: just before the first result line, `os.dup2` `/dev/null` onto fds 1 and 2, so other writers' output goes nowhere, and write only to the saved descriptor.
> - Optionally, in the harness, refuse a run whose log has more than one metric match.
>
> ## Summary
>
> The round-3 fixes do what the report says:
> - the metric is frozen and equals `evaluate_bpb` exactly for an honest model;
> - look-ahead models are refused;
> - an `atexit` line or a stdout rewrite no longer reaches the metric line;
> - refusals stick even when caught;
> - planted files are detected;
> - the download is pinned;
> - tests and the shared files are in sync.
>
> The report's limits list is accurate for what it names. Findings 4–5 add routes it should name. Findings 1–3 are cheap hardening of the new probe and the data check, and I recommend them before the census measurements. None of them changes the declared edits or the manifest, except finding 6 if `train.py`'s docstring is used.

---

## Round 4 (harness `d6e64927`, report `a7de1f39`)

> # Review round 4: Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> The round-3 findings are fixed, deferred to an open point, or remain only for editable code that runs after a guard. No change in round 4 breaks an honest run.
>
> Two report claims are now wrong or too strong:
> - the model contract is said to be shown to the proposer, but it is not (finding 2);
> - three guards are stated without exceptions, although code that runs after them can defeat them (finding 1).
>
> I recommend fixing both before the census. They are MINOR because every bypass I found needs deliberate code.
>
> **What was reviewed:**
> - Harness `mac-trackg-port-ar-20261117b` @ `d6e64927f0c6…` (diff `735aacca..d6e64927`). I checked the worktree was clean at the start and ran the probes on a `git archive` of `d6e64927`.
> - Paper `mac-trackg-u3-ar-20261117b` @ `a7de1f39`.
>
> Reviewer: an independent agent (Claude), round 4. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, scripts `scripts/run_probes.py` and `scripts/two_runs.py`. `tmp/` was emptied at the end. Each probe runs through the real wrapper on a synthetic copy and is classified with the harness's `classify_run`. For the data probes, the node's new infrastructure pattern was included.
>
> ## Checks that pass
>
> - **Tests.** The given command gives **19 passed in 645 s**, as the report says.
>   - The smoke records are unchanged: baseline 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, repeat baseline 2.18766, broken diff `non_finite_loss`.
>   - `AR_INFO causal_probe_max_change=0` on every `ok` run of the smoke, and `nan` on the broken one, as the report says.
> - **Manifest.** `manifest.json` has sha256 `f8435b20…87d2`, as stated. The round-2 manifest (`088e80f6…`) is kept as `superseded/manifest_round2.json`.
> - **No regression for honest runs.**
>   - Restoring `prepare`'s attributes is a no-op for a `train.py` that does not touch `prepare`.
>   - The frozen tokenizer is the same one the setup trained.
>   - The second data check costs one more hash pass over the roughly 1 GB of data per run, a few seconds.
>   - The fingerprint is a float64 sum and sum of squares per tensor. It is unchanged for a model that does not write to its weights. It costs a transient float64 copy of each tensor, which is small for this model.
>   - The baseline stand-in gives the same value as in round 3 (2.232539), with probe change 0.
> - **Infrastructure pattern** `\A(?:(?!AR_DEVICE ).*\n)*?AR_ERROR data `, checked with `classify_run`:
>   - A start-of-run data failure, which happens before `AR_DEVICE`, is classed `infrastructure_failure`.
>   - An `AR_ERROR data …` printed after `AR_DEVICE` is not; this is the only place `train.py` output can appear, since `train.py` runs after `AR_DEVICE`. So `train.py` cannot forge the pattern.
>   - The post-train message `AR_ERROR train.py changed the data:` cannot match it.
>   - It ran in linear time on a 100,000-line log.
>
> ## Round-3 findings: status
>
> | # | Round-3 finding | Status | Evidence (round-4 probes) |
> |---|---|---|---|
> | 1 | `-inf` turns the probe off | **Fixed** | The `-inf` look-ahead model now exits 9 (change 20). Equal infinities count as equal; the probe skips only on NaN. A test was added. |
> | 2 | Planted file blamed on later runs | **Fixed** for writes during `train.py` | A planting `train.py` now exits 5 with "train.py changed the data:" (`divergent`). The next run's start-of-run failure is `infrastructure_failure`. The residual is a write from code that runs after the second check (new finding 1b). |
> | 3 | Probe tolerance loose, change not recorded | **Deferred to open point 4**, acceptably | `AR_INFO causal_probe_max_change` is printed on every run (0 in the CPU smoke). The tolerance is to be tightened from the census measurement. |
> | 4 | `prepare` globals, torch call, `emit` patchable | **Fixed** for patches made during `train.py` | The `VAL_FILENAME` swap now gives the baseline value 2.232539 (was 2.223328). The `cross_entropy` patch gives 2.232539 (was 0.0). The `emit` patch still gives `ok 0.1` (listed). The residual is a re-patch after the restore (new finding 1a). |
> | 5 | Self-updating `forward` | **Fixed** for parameters and buffers | Both self-updating probes, early and late, now exit 10. The residual is a `state_dict` override or state outside parameters and buffers (new finding 1c). |
> | 6 | Model contract not told to the proposer | **Not fixed**: the claimed fix does not reach the proposer | A model returning only the last position exits 4, as described. The contract is in the yaml `description`, which the harness prompt does not include (new finding 2). |
> | 7 | Probe memory (NOTE) | Not addressed (acceptable) | — |
> | 8 | Thread decides the metric | **Fixed** for threads writing to fds 1 and 2 | 2 of 2 thread-race runs scored the wrapper's 2.232539 (was 0.1 in 2 of 3). The residual is a thread writing through its own copy of the output descriptor (new finding 3). |
>
> ## New findings
>
> ### 1. MINOR: the new guards run before the last editable code; the model's own methods and threads run after them, and the report now states the guards without exceptions
>
> **Location.** `run_fixed_budget.py` `main()`. After the second data check and the restore of `prepare`, the wrapper calls the model's methods:
> - `model.eval()`;
> - `model.state_dict()`, inside `weights_fingerprint`;
> - `model.parameters()`;
> - `forward` on every evaluation batch.
>
> All of these are editable, and threads started by `train.py` keep running.
>
> **(a) Re-patching after the restore.**
> - A model class whose `eval()` sets `prepare.VAL_FILENAME = "shard_00000.parquet"` gave `ok 2.215119`. The same class with `eval()` doing nothing gave 2.232812, so the evaluation read a training shard.
> - A thread that waits for `validation_open` and then sets the same attribute gave `ok 2.223328`, the training-shard value.
>
> **(b) Writing the data after the second check.** A model whose `eval()` copies the validation shard to `data/shard_00010.parquet`:
> - run 1 (the planting run) ends **`ok`**;
> - run 2, an honest stand-in, is `infrastructure_failure` ("AR_ERROR data directory holds files the manifest does not list").
> - In the v2-diff campaign, an infrastructure failure that is not a timeout is rerun `max_infra_reruns` times, then recorded as `infrastructure_failure_final`, and the campaign goes on (`campaign_v2_diff.py`, `run_with_retries`). Every later step therefore burns its reruns and no step is evaluated. Nothing STOPs, and the run that caused it is not identified.
>
> **(c) The fingerprint is bypassed.**
> - A model that overrides `state_dict()` to return `{}`, and runs SGD on each evaluation batch after the probe's calls, gave `ok`.
> - A model that keeps learned "fast weights" in a plain tensor attribute, not a parameter or buffer, updated across evaluation batches, gave `ok 2.229179`.
> - `state_dict()` also leaves out non-persistent buffers.
>
> **Report.** Round 4 removed "keep a background thread running into the evaluation" from the limits list. It now states:
> - "prepare's module attributes are restored … (undoing, e.g., a changed `VAL_FILENAME` …)";
> - "a model that updates itself in `forward` cannot train on the validation shard";
> - "a run that changes them fails itself".
>
> Each holds only for code that runs before the guard.
>
> **Fix** (all in the frozen wrapper, cheap):
> - Switch the model to eval mode without calling its methods: `for m in torch.nn.Module.modules(model): m.training = False`.
> - Fingerprint through the unbound base methods `torch.nn.Module.named_parameters(model)` and `torch.nn.Module.named_buffers(model)`; this also covers non-persistent buffers.
> - After the evaluation and before `seal()`: check that every value in `vars(prepare)` is still the snapshot's object, and run `ar_data.verify` a third time. That makes (a) and (b) fail the run that did them.
> - Restore the limits item: "editable code that runs during the evaluation (the model's methods, threads) can re-patch `prepare` or the frozen tokenizer, write the data after the checks, or keep state outside parameters and buffers".
> - Optionally, the experiment agent should STOP the campaign at the first start-of-run `AR_ERROR data`.
>
> ### 2. MINOR: the model contract is in the yaml `description`, but the harness never shows the description to the proposer
>
> **Location.**
> - `src/autoresearch/trackg/manager_v2_diff.py:81–103`, `build_prompt`, at base `717ad835` and unchanged by the port. It includes the node name, metric, direction, budget, the editable files and the history. It does not include `spec.description`.
> - Report: "now stated in the node's yaml description, which the proposer sees".
>
> **Failure scenario.** The proposer never sees the contract. An edit that returns only the last position's logits when `targets is None` (shown here: exit 4, `divergent`) is still likely and still labelled divergent. Round 4 re-declared the edits only for a text that has no effect on proposals.
>
> **Fix.** Either put the contract in `train.py`'s module docstring, which the prompt shows; that changes the editable baseline, so the edits must be re-declared once more. Or ask the coordinator to add `description` to `build_prompt` (a harness change). Either way, correct the report's sentence.
>
> ### 3. NOTE: the seal does not stop a thread that copied the output descriptor itself
>
> A thread with its own `os.dup(1)`, taken in `train.py` before the seal, writing `AR_METRIC val_bpb=0.100000` in a loop, won 1 of 3 runs (`ok 0.1`); a variant with a 1 ms sleep won 0 of 2. The listed limit "write to the saved descriptor itself" names only `ar_data`'s copy. The report's "a thread `train.py` started can no longer print into the log" is too strong.
>
> **Fix.** Word it as "… unless it holds its own copy of the output descriptor". Open point 5, refusing a run with more than one metric line, would close this.
>
> ## Summary
>
> The round-4 code does what the commit says for code that runs during `train.py`:
> - a `-inf` look-ahead model is refused;
> - patches of `prepare` and of `cross_entropy` made in `train.py` no longer reach the metric;
> - a model that changes its parameters or buffers during the evaluation is refused (exit 10);
> - a run that plants data during `train.py` fails itself;
> - the infrastructure pattern cannot be forged from `train.py`;
> - threads writing to stdout or stderr can no longer forge the metric line;
> - the tests pass and the honest metric is unchanged.
>
> The remaining gaps all need deliberate code, and their fixes are a few lines each:
> - **Finding 1:** model methods and threads that run after the guards.
> - **Finding 2:** the contract the proposer cannot see, which is the only claim with practical effect on honest proposals.
> - **Finding 3:** wording of the seal.

---

## Round 5 (harness `b3a08ff0`, report `ab9a944f`)

> # Review round 5: Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> **What was reviewed:**
> - Harness `mac-trackg-port-ar-20261117b` @ `b3a08ff0743f…` (diff `d6e64927..b3a08ff0`). The worktree was clean; the probes ran on a `git archive` of `b3a08ff0`.
> - Paper `mac-trackg-u3-ar-20261117b` @ `ab9a944f` (diff `a7de1f39..ab9a944f`).
>
> Reviewer: an independent agent (Claude), round 5. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, drivers `scripts/run_probes.py` and `scripts/two_runs.py`. `tmp/` was emptied at the end.
>
> **Summary of the verdict.** All three round-4 findings are answered. The contract now reaches the proposer through `train.py`'s docstring, and the data and `prepare` are re-checked after the evaluation. The new threat model in the common section is accurate in substance: it no longer claims the metric is tamper-proof, and it names the harness changes that would close the rest.
>
> Three new MINOR findings:
> 1. One code claim is false: the "unbound `nn.Module` methods" still dispatch to methods the model can override.
> 2. One deliberate forgery route, a dispatch mode, is neither closed nor listed.
> 3. The new `prepare` identity check can refuse an **honest** run on the GPU host if any warning is attributed to `prepare.py` during the evaluation. It is shown here by simulation and is a one-line fix.
>
> I recommend fixing finding 3 before the census; findings 1 and 2 are a few lines each.
>
> ## Checks that pass
>
> - **Tests.** The given command gives **21 passed in 609 s**, as the report says.
>   - The smoke records are unchanged: baseline and repeat 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, broken diff `non_finite_loss`.
>   - `causal_probe_max_change` is 0 on every `ok` run, `nan` on the broken one.
> - **Manifest.** It has sha256 `d8f89c32…`, as stated; the round-3 manifest (`f8435b20…`) is kept as `superseded/manifest_round3.json`, and the diffs are unchanged.
> - **Contract.** `train.py`'s docstring now states it. The stale "evaluates with `prepare.evaluate_bpb`" sentence is gone. `build_prompt` shows the editable files, so the proposer sees the contract.
> - **Report facts against the code:**
>   - The runner opens `run.log` with `"wb"` (no `O_APPEND`) and starts the run with `start_new_session=True`, which matches the threat model's "seek in the log" and "forked child" items.
>   - `torch._C.DisableTorchFunction()` exists in torch 2.6 and wraps all the frozen arithmetic.
>   - `plain_logits` refuses a non-`torch.Tensor` output.
>   - The seal writes the newline.
>
> ## Round-4 findings: status
>
> | # | Round-4 finding | Status | Evidence (round-5 probes) |
> |---|---|---|---|
> | 1a | Re-patching `prepare` after the restore | **Fixed**, residual listed | A model with an `eval()` override that swaps `VAL_FILENAME` now gives 2.232812, the same as the control without the swap, because `eval()` is no longer called. A thread re-patch gives exit 4, "prepare's attributes changed during the evaluation". A *temporary* swap undone before the final check still scores the training shard (`ok 2.223328`); the threat model lists exactly this. |
> | 1b | Planting data after the second check | **Fixed** | The `eval()`-override plant no longer runs: both runs ok, data untouched. Planting from `forward` during the evaluation now fails the planting run itself (exit 5, "train.py changed the data:"); the next run is `infrastructure_failure`. Planting during `train.py` behaves the same way. |
> | 1c | Fingerprint bypass | **Fixed for the `state_dict()` override** (exit 10); residuals | The plain-attribute fast-weights model still gives `ok 2.229179`; this is listed. A new bypass through `_named_members` is described in new finding 1. |
> | 2 | Contract not visible to the proposer | **Fixed** | It is in `train.py`'s docstring, and the edits were re-declared. The last-position-only model exits 4. |
> | 3 | Seal wording / own `dup` of fd 1 | **Fixed** (wording) | The report and threat model now say a descriptor obtained before the seal can still write. The thread race on fd 1 gave the wrapper's value in 2 of 2 runs. |
>
> Other round-2 and round-3 probes re-run, all as expected:
>
> | Probe | Result |
> |---|---|
> | `-inf` look-ahead | exit 9 |
> | `cross_entropy` patch | 2.232539 |
> | `VAL_FILENAME` swap during `train.py` | 2.232539 |
> | caught validation refusal | exit 8 |
> | `atexit` line, stdout filter | 2.232539 |
> | late self-updating model | exit 10 |
> | `emit` patch | `ok 0.1` (listed) |
>
> ## New findings
>
> ### 1. MINOR: the "unbound `nn.Module` methods" still call methods the model can override
>
> **Location.**
> - `run_fixed_budget.py`: `weights_fingerprint` (`nn.Module.named_parameters(model)` and `named_buffers`), the eval-mode loop (`nn.Module.modules(model)`), and `next(nn.Module.parameters(model))`.
> - Report: "use the unbound `nn.Module` methods (parameters and all buffers), not the model's own overrides".
>
> **Why.** In torch 2.6:
> - `Module.modules` calls `self.named_modules()`;
> - `Module.parameters` calls `self.named_parameters()`;
> - `Module.named_parameters` and `named_buffers` call `self._named_members(...)`, which calls `self.named_modules(...)`.
>
> All of these go through `self` and reach the model's overrides.
>
> **Demonstrated.**
> - **Fingerprint bypass.** A model whose `_named_members` returns nothing when called from `weights_fingerprint` (an `inspect.stack()` check), and which runs a gradient step on each evaluation batch after the probe, gave **`ok 2.232727`**. The same class without updates gives 2.232812, so the weights changed and the fingerprint (empty before, empty after) did not see it.
> - **Eval mode not reaching submodules.** A model whose `named_modules` leaves out its `Dropout` kept that dropout in training mode during the evaluation (`training: True` printed from `forward`).
> - Both need deliberate code.
>
> **Fix.** Walk the module tree through the instance dicts, which no method override can intercept:
> - `d = vars(m)`; recurse into `d["_modules"]`;
> - fingerprint `d["_parameters"]` and `d["_buffers"]`;
> - set `d["training"] = False`.
>
> Or reword the claim and add "overrides of `named_modules` / `_named_members`" to the threat model.
>
> ### 2. MINOR: a `TorchDispatchMode` left active by `train.py` forges the metric; it is neither closed nor listed
>
> **Location.** The frozen arithmetic runs under `torch._C.DisableTorchFunction()`, which disables `__torch_function__` subclasses and modes but not `__torch_dispatch__` modes.
>
> **Threat model.** It says the port closes "a tensor subclass or torch-function mode inside the frozen arithmetic". The list of what remains does not name dispatch modes ("patch frozen modules at run time" is a different thing).
>
> **Demonstrated** (`probes/p_dispatch.py`). At the end of `train.py`, a `TorchDispatchMode` that returns zeros for `aten.nll_loss_forward` is entered and never exited. Result: exit 0, **`ok 0.0`**, probe change 0.
>
> **Fix.**
> - Cheap: before the evaluation and again before the final arithmetic, require `torch._C._len_torch_dispatch_stack() == 0` and `torch._C._len_torch_function_stack() == 0`, and exit with its own code otherwise. Both are 0 in a clean process; I checked.
> - Also add "an active dispatch mode" to the threat model.
> - A mode entered *during* the evaluation from the model's own code (`forward`) would still work; that belongs in the list too.
>
> ### 3. MINOR (affects honest runs): the post-evaluation identity check of `prepare` fails if any warning is attributed to `prepare.py` during the evaluation on a host without an import-time warning
>
> **Location.** `run_fixed_budget.py`, after the evaluation:
> ```python
> if any(vars(prepare).get(k, object()) is not v ...) or set(vars(prepare)) != set(prepare_snapshot): fail(4, ...)
> ```
> Earlier, the restore also deletes keys that were not in the snapshot.
>
> **Mechanism.** Python's `warnings.warn` creates `__warningregistry__` in the globals of the frame it attributes the warning to, even when the warning is filtered.
> - On this CPU test host, `prepare.verify_env()` warns at import ("No GPU detected"). The registry therefore already exists in the snapshot, and the check passes. **The CPU tests cannot show the problem.**
> - On the CUDA host there is no import warning. The first warning attributed to a line of `prepare.py` during the evaluation adds the key, and an honest run then ends **exit 4 → `divergent`**. If the warning recurs, every run fails, including the baseline, which STOPs the campaign as `baseline_failed`.
>
> **Demonstrated by simulation** (`adv/w_warnsim`, a scratch copy of prepare.py changed in two ways):
> - the import warning was removed, as on the CUDA host;
> - one `FutureWarning` was added in `get_token_bytes`, standing in for a library warning attributed to `prepare.py` (for example `torch.load`'s `weights_only` FutureWarning in torch 2.4–2.5).
>
> With the honest baseline stand-in, the run ended with "AR_ERROR prepare's attributes changed during the evaluation", exit 4. Whether the pinned torch 2.6 CUDA build or pyarrow emits such a warning on Ada is not known from here. It would show at once in the census baseline, so the risk is a failed census, not silently wrong labels.
>
> **Fix (one line).** Leave dunder names out of the restore and the check, for example compare `{k: v for k, v in vars(prepare).items() if not k.startswith("__")}`. Or create `prepare.__dict__.setdefault("__warningregistry__", {})` before the snapshot.
>
> ## Report and threat model: accuracy
>
> - The threat model is accurate apart from:
>   - the "unbound methods … not the model's own overrides" sentence (finding 1);
>   - the missing dispatch-mode item (finding 2).
> - The deliberate-only residuals I could still demonstrate are named in it:
>   - a temporary `VAL_FILENAME` swap undone before the final check;
>   - plain-attribute learned state;
>   - a forged line followed by an early exit;
>   - an `emit` patch;
>   - a descriptor obtained before the seal.
> - It correctly says these need the harness to close (separate process, `O_APPEND` log or a pipe, process-group kill, refusing more than one metric match), and that until then the declared-edit review and the S1 audit must read proposals for such code.
> - "21 passed (20 in the full run …)" matches my run: 21 passed.
>
> ## Summary
>
> Round 5 fixes what round 4 asked for:
> - the proposer now sees the contract;
> - `eval()` / `state_dict()` overrides and threads re-patching `prepare` are caught;
> - data planted during the evaluation fails the run that planted it.
>
> The report now describes the in-process threat model honestly. What remains:
> - **Finding 3:** a latent false failure of honest runs on the GPU host. One-line fix; recommended before the census.
> - **Finding 1:** an inaccurate claim, plus a deliberate bypass of the fingerprint and of eval mode.
> - **Finding 2:** a deliberate dispatch-mode forgery, closable with a stack-length check.

---

## Round 6 (harness `07bb2bc6`, report `bc1ef956`)

> # Review round 6 (confirmation): Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> **What was reviewed:**
> - Harness `mac-trackg-port-ar-20261117b` @ `07bb2bc68748…` (diff `b3a08ff0..07bb2bc6`). The worktree was clean; the probes ran on a `git archive` of `07bb2bc6`.
> - Paper `mac-trackg-u3-ar-20261117b` @ `bc1ef956` (diff `ab9a944f..bc1ef956`).
>
> Reviewer: an independent agent (Claude), round 6. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, driver `scripts/run_probes.py`. `tmp/` was emptied at the end.
>
> **Summary of the verdict.** All three round-5 findings are fixed, and every earlier probe behaves as before. There are two new findings:
> 1. **MINOR:** the new mode check refuses an honest `train.py` that calls `torch.set_default_device(...)`.
> 2. **NOTE:** a deliberate `__dict__` property defeats the "no overridable method is called" claim.
>
> Neither blocks. I recommend fixing finding 1 before the census, because it mislabels an honest edit as `divergent`.
>
> ## Checks that pass
>
> - **Tests.** The given command gives **23 passed in 595 s**, as the report says.
>   - The smoke records are unchanged: baseline and repeat 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, broken diff `non_finite_loss`.
>   - `causal_probe_max_change` is 0 on all 7 `ok` runs, `nan` on the broken one.
> - **Manifest.** It is unchanged (`d8f89c32…`); round 6 changes only frozen files and tests.
> - **Leading newline in `emit`.** Each wrapper line is now preceded by an empty line. The anchored `metric_regex` (multiline) and the classifier are unaffected: the baseline classifies `ok 2.232539`.
> - **Report against the code.** The round-6 report text matches the code: the mode check, the dict-based module walk, dunder names left out of the `prepare` check, and the newline before each emitted line. The threat model now names modes entered only while the model's own code runs, patches of torch or numpy, and `setsid` children, and does not claim closure for them.
>
> ## Round-5 findings: status
>
> | # | Round-5 finding | Status | Evidence (round-6 probes) |
> |---|---|---|---|
> | 1 | "Unbound `nn.Module` methods" still reach model overrides | **Fixed** | The model hiding its tensors through `_named_members` while updating its weights now exits **10** (was ok 2.232727). The `named_modules` override no longer keeps its `Dropout` in training mode (`training: False` printed from `forward`). |
> | 2 | Dispatch mode left active forges the metric | **Fixed** | The `TorchDispatchMode` zeroing `nll_loss_forward` now exits **4**, "a torch function or dispatch mode is active during the frozen evaluation" (was ok 0.0). |
> | 3 | `__warningregistry__` could refuse an honest run on the GPU host | **Fixed** | The same simulation as in round 5 (no import warning, plus one warning attributed to `prepare.py` during the evaluation) now gives exit 0, `ok 2.232539`, the honest value (was exit 4). |
>
> Earlier probes re-run, all unchanged:
>
> | Probe | Result |
> |---|---|
> | look-ahead, `-inf` look-ahead | exit 9 |
> | `cross_entropy` patch | 2.232539 |
> | `VAL_FILENAME` swap during `train.py` | 2.232539 |
> | thread re-patch | exit 4 |
> | `state_dict` override with self-updating `forward` | exit 10 |
> | late self-updating model | exit 10 |
> | last-position-only model | exit 4 |
> | caught validation refusal | exit 8 |
> | `atexit` line, stdout filter, thread race on fd 1 | 2.232539 |
> | zero edited loss | ignored (2.232812, the model's honest value) |
>
> The listed residuals still behave as the threat model says:
>
> | Probe | Result |
> |---|---|
> | temporary `VAL_FILENAME` swap undone before the final check | `ok 2.223328` |
> | plain-attribute fast weights | `ok 2.229179` |
> | `emit` patch | `ok 0.1` |
> | forged line plus `os._exit` | `ok 0.1` |
>
> ## New findings
>
> ### 1. MINOR (affects honest runs): `torch.set_default_device(...)` in `train.py` is refused as "a torch function mode"
>
> **Location.** `run_fixed_budget.py`, `no_active_modes`: `torch._C._len_torch_function_stack()` must be 0.
>
> **Demonstrated** (`probes/p_default_device.py`). An otherwise honest stand-in that ends with `torch.set_default_device("cpu")` exits **4**, "a torch function or dispatch mode is active during the frozen evaluation", and is classed `divergent`.
> - `set_default_device` installs a `torch.utils._device.DeviceContext`, which is a torch-function mode. It stays on the stack (`_len_torch_function_stack()` is 1 after the call).
> - A proposal using it (for example `torch.set_default_device(device)`, common in some codebases) would be labelled divergent although it is legitimate.
> - A temporary `with torch.device("meta"):`, as in the baseline, is popped and is fine.
>
> **Fix.**
> - The frozen arithmetic already runs under `torch._C.DisableTorchFunction()`, which also disables torch-function **modes**, so the function-stack test is redundant for it. Either:
>   - check only the dispatch stack; or
>   - allow `DeviceContext` entries on the function stack (`torch.overrides._get_current_function_mode_stack()`).
> - Add a test with `set_default_device`.
> - If the function-mode check is kept, say in `train.py`'s contract docstring that no torch-function or dispatch mode, including `set_default_device`, may be left active.
>
> ### 2. NOTE: `vars(module)` honours a class-level `__dict__` property, so "no overridable method of the model is called" is too strong
>
> **Location.** `module_tree` / `module_tensors` and the eval-mode loop use `vars(module)`.
>
> **Demonstrated** (`probes/p_dictprop_dyn.py`). A model class defines `__dict__` as a property. It returns the real dict to `nn.Module` itself, but a fake dict with no submodules and one dummy parameter when called from `module_tree` / `module_tensors`. The model then takes a gradient step on each evaluation batch after the probe. Result: **`ok 2.232727`**; the weights changed and exit 10 did not fire.
> - This is deliberate code (`__dict__ = property`, an `inspect` stack check), in the same class as the listed run-time patches.
>
> **Fix.** Read the real instance dict through the base class's descriptor, which a subclass cannot override: `REAL = torch.nn.Module.__dict__["__dict__"]` (a `getset_descriptor`) and `REAL.__get__(module)`. Use it in `module_tree`, `module_tensors` and for setting `training`. Or soften the report's sentence to "no method of the model is called (a deliberately overridden `__dict__` is not detected)".
>
> ## Summary
>
> Round 6 fixes all three round-5 findings, confirmed by re-running the probes:
> - hidden tensors are refused (exit 10);
> - `Dropout` gets eval mode;
> - a dispatch mode is refused (exit 4);
> - the honest warning simulation now passes.
>
> There are no regressions in the earlier probes or the tests.
>
> Remaining:
> - **Finding 1 (MINOR):** an honest `set_default_device` edit is refused. Small fix; recommended before the census.
> - **Finding 2 (NOTE):** a deliberate `__dict__` property defeats the dict-based module walk. One-line fix, or a wording change.

---

## Round 7 (harness `51d53e5c`, report `70fee30c`)

> # Review round 7 (confirmation): Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> **What was reviewed:**
> - Harness `mac-trackg-port-ar-20261117b` @ `51d53e5cdc55…` (diff `07bb2bc6..51d53e5c`). The worktree was clean; the probes ran on a `git archive` of `51d53e5c`.
> - Paper `mac-trackg-u3-ar-20261117b` @ `70fee30c` (diff `bc1ef956..70fee30c`).
>
> Reviewer: an independent agent (Claude), round 7. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, driver `scripts/run_probes.py`. `tmp/` was emptied at the end.
>
> **Summary of the verdict.** Both round-6 items are fixed: the honest `set_default_device` stand-in runs `ok`, and the `__dict__`-property model is caught. There are no regressions for honest runs or in the earlier probes.
>
> There is one new MINOR finding. Allowing torch-function modes reopens a deliberate route: a mode left active by `train.py` runs inside the frozen **data path** of the evaluation (the validation loader and `get_token_bytes`), which is outside the `DisableTorchFunction` block. A forged `ok 0.0` is shown below. Round 6 had blocked this by refusing all function modes. The fix is to wrap the data path as well, a few lines; I recommend it before the census. It is not blocking, because it needs deliberate code of a kind the threat model already tells the declared-edit review and the S1 audit to look for (`TorchFunctionMode`, `__torch_function__`).
>
> ## Checks that pass
>
> - **Tests.** The given command gives **24 passed in 576 s**, as the report says.
>   - The smoke records are unchanged: baseline and repeat 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, broken diff `non_finite_loss`.
>   - `causal_probe_max_change` is 0 on all 7 `ok` runs, `nan` on the broken one.
> - **Manifest.** It is unchanged; only frozen files and tests changed.
> - **Report.** The round-7 text matches the code: the dispatch-only mode check, `nn.Module`'s own `__dict__` descriptor, and the new `set_default_device` test.
> - **Threat model on `torch.library`.** Replacing "a mode entered only while its own code runs" with "an aten kernel through `torch.library`" is correct:
>   - after `model(x)` returns, `plain_logits` checks the dispatch-mode stack before the frozen arithmetic;
>   - no editable code runs between that check and the arithmetic;
>   - mode stacks are per thread, so a mode entered and left inside `forward` cannot reach the arithmetic;
>   - a dispatch mode left active is refused at the pre-evaluation fingerprint check. A variant that enters a dispatch mode in `train.py` and leaves it from `forward` exits 4 there, before the loader runs.
>
> ## Round-6 findings: status
>
> | # | Round-6 finding | Status | Evidence (round-7 probes) |
> |---|---|---|---|
> | 1 | Honest `torch.set_default_device(...)` refused (MINOR) | **Fixed** | The same stand-in now gives exit 0, `ok 2.232539`, the honest value (was exit 4). A test was added. |
> | 2 | `__dict__` property fakes the module walk (NOTE) | **Fixed** | The same model (fake dict shown only to `module_tree` / `module_tensors`, gradient steps during the evaluation) now exits **10** (was ok 2.232727). |
>
> Earlier probes re-run, all unchanged:
>
> | Probe | Result |
> |---|---|
> | dispatch mode zeroing `nll_loss` | exit 4 |
> | `_named_members` hiding | exit 10 |
> | `named_modules` override | dropout in eval mode (`training: False`) |
> | look-ahead, `-inf` look-ahead | exit 9 |
> | thread re-patch of `prepare` | exit 4 |
> | `state_dict` override with self-updating `forward` | exit 10 |
> | caught validation refusal | exit 8 |
> | last-position-only model | exit 4 |
> | `atexit`, stdout filter, thread race on fd 1, `cross_entropy` patch | 2.232539 |
>
> ## New findings
>
> ### 1. MINOR: a torch-function mode left active by `train.py` forges the metric through the evaluation's data path (regression from allowing function modes)
>
> **Location.** `run_fixed_budget.py`, `frozen_bpb`. These run **outside** `torch._C.DisableTorchFunction()`:
> - `token_bytes = get_token_bytes(device=device)`;
> - `val_loader = make_dataloader(...)`;
> - every `next(val_loader)`, which executes `prepare`'s packing code: `torch.tensor`, `copy_` into the batch buffer.
>
> Only the probe comparison, `logits.float()` and the cross-entropy sums are inside it. Since round 7, `no_active_modes` no longer refuses function modes.
>
> **Demonstrated** (`probes/p_fnmode_targets.py`). At the end of `train.py`, a `TorchFunctionMode` is entered and left active. After `prepare`'s `copy_(…, non_blocking=True)` into the batch buffer, it overwrites the target half with one token `TSTAR`. The model is causal (constant logits with 50 on `TSTAR`), so the probe passes. Result: exit 0, **`ok 0.0`**. The same model without the mode gives 12.161007.
> - The threat model says "a torch-function mode inside the frozen arithmetic (it runs with torch-function dispatch disabled)" is closed. That is true for the arithmetic, but the validation targets and `token_bytes` that feed it can be rewritten.
> - In round 6 this route was blocked, because any function mode was refused before the evaluation.
>
> **Fix.**
> - Run the data path with torch-function dispatch disabled too:
>   - `with torch._C.DisableTorchFunction():` around `get_token_bytes(...)` and `make_dataloader(...)`;
>   - around each `x, y, _ = next(val_loader)`; the generator's body runs inside `next`.
> - Leave `model(x)` outside, so an honest `set_default_device` still applies to the model.
> - This also stops a leftover `set_default_device("cuda")` from moving the loader's CPU buffers.
> - Add the mode above to `EVALUATED` in the tests, expecting the honest value or a refusal.
> - Alternatively, refuse function modes other than `torch.utils._device.DeviceContext`.
>
> ## Summary
>
> Round 7 fixes the round-6 finding and note without regressions:
> - the `set_default_device` stand-in is `ok` with the honest value;
> - the `__dict__`-property model is refused (exit 10);
> - all earlier probes and the 24 tests behave as before.
>
> The one new MINOR finding is a deliberate-code route reopened by allowing function modes. It is fixed by wrapping the evaluation's data path in `DisableTorchFunction`, and I recommend that before the census.

---

## Round 8 (harness `08d06507`, report `432dbcfb`)

> # Review round 8 (confirmation): Track G U3 port kit, suite autoresearch (node `autoresearch_fixedtokens`)
>
> **Verdict: ACCEPTED**
>
> **What was reviewed:**
> - Harness `mac-trackg-port-ar-20261117b` @ `08d065077d40…` (diff `51d53e5c..08d06507`). The worktree was clean; the probes ran on a `git archive` of `08d06507`.
> - Paper `mac-trackg-u3-ar-20261117b` @ `432dbcfb` (diff `70fee30c..432dbcfb`).
>
> Reviewer: an independent agent (Claude), round 8. No repository was changed. Scratch is only under `/tmp/rv_ar2/`: probes in `probes/`, logs in `adv/*.log`, driver `scripts/run_probes.py`. `tmp/` and the scratch tree were removed at the end.
>
> **Summary of the verdict.** The round-7 finding is fixed:
> - my function mode that rewrites the targets now leaves the honest value;
> - a mode aimed at `token_bytes` has no effect;
> - the two new tests fail against the round-7 wrapper and pass against the round-8 one.
>
> There are no regressions. One new MINOR finding: introspecting the wrapper's stack frame from `forward` (`sys._getframe`) still rewrites the targets or the byte counts in place. This is deliberate code. It is not in the threat model or its list of names to look for, and a cheap narrowing exists.
>
> ## Checks that pass
>
> - **Tests.** The given command gives **26 passed in 557 s**, as the report says.
>   - The smoke records are unchanged: baseline and repeat 2.18766, E1 2.185491, E2 2.193558, E3 2.191957, E4 2.202521, broken diff `non_finite_loss`.
>   - `causal_probe_max_change` is 0 on all 7 `ok` runs, `nan` on the broken one. The honest metric is unchanged by the extra copies.
> - **The new tests detect the bug.** On a scratch copy of the full tree at `08d06507` with `run_fixed_budget.py` replaced by the round-7 version (`51d53e5c`), the two new cases **fail**, both with `assert 0.0 > 1.0`:
>   - `rewrites_targets_through_a_function_mode`;
>   - `writes_into_the_loader_buffer`.
>   - `sets_the_default_device` passes there.
>   - With the round-8 wrapper, all pass. So the tests do detect the regression they guard against.
> - **Costs.** The per-batch copies (`x`, `y`, `model_input`; about 256 KiB each at B=16, T=2048) are negligible.
> - **Report.** The text matches the code: the data path and the probe inputs are under `DisableTorchFunction`, and the model gets copies. The threat-model additions are accurate as stated:
>   - a training-time mode or patch can hide a non-finite loss;
>   - an ordinary `torch.nan_to_num(loss)` edit changes the divergent class;
>   - more names were added to look for.
>   - For this node, the loss lines are printed by the editable `train.py` itself (no frozen loss log), so an edit can hide a NaN loss even more simply. The shared sentence still holds.
>
> ## Round-7 finding: status
>
> | # | Round-7 finding | Status | Evidence (round-8 probes) |
> |---|---|---|---|
> | 1 | A torch-function mode left active rewrote the targets through the data path (MINOR) | **Fixed** | My target-rewriting mode now gives `ok 12.161007`, identical to the same constant model without the mode (was `ok 0.0`). A mode that multiplies the vocab-sized integer tensor (`token_bytes`) by 100 has no effect (`ok 2.232539`, the baseline). An honest `set_default_device` stand-in is still `ok 2.232539`. A dispatch mode is still refused (exit 4). |
>
> Earlier probes re-run, all unchanged:
>
> | Probe | Result |
> |---|---|
> | `__dict__` property, `_named_members` hiding, `state_dict` override | exit 10 |
> | late self-updating model | exit 10 |
> | look-ahead, `-inf` look-ahead | exit 9 |
> | thread re-patch of `prepare` | exit 4 |
> | caught validation refusal | exit 8 |
> | last-position-only model | exit 4 |
> | `atexit`, stdout filter, thread race on fd 1, `cross_entropy` patch | 2.232539 |
>
> ## New findings
>
> ### 1. MINOR: a model can rewrite the wrapper's targets or byte counts in place through stack-frame introspection; the threat model and its names to look for do not mention it
>
> **Location.**
> - `run_fixed_budget.py`, `frozen_bpb`: `y` (now a copy) and `token_bytes` are locals of the frame that calls `model(model_input)`.
> - From `forward`, `sys._getframe()` / `inspect` / `gc.get_objects()` reach them, and `fill_` / `mul_` change them in place before the frozen arithmetic reads them.
>
> **Demonstrated.** In both probes the model walks `f_back` to the `frozen_bpb` frame and writes into its locals:
> - `p_frames.py`: a causal constant model calls `f_locals["y"].fill_(TSTAR)` on every call. Result: **`ok 0.0`** (the same model scores 12.161007 honestly).
> - `p_frames_tb.py`: honest predictions, but `f_locals["token_bytes"].mul_(100)` once. Result: **`ok 0.022328`** (honest 2.232539).
> - The probe passes in both, and no check fires.
> - This is deliberate code, in the same class as the listed run-time patches of frozen modules. The threat model's list, though, covers patching modules, torch or numpy, not reaching into the wrapper's live locals. The names to look for omit `sys._getframe`, `f_back`, `f_locals`, `inspect`, `gc.get_objects` and `gc.get_referrers`.
>
> **Fix.**
> - Narrowing, cheap:
>   - before `model(...)`, take a digest of `y` (e.g. `hashlib.sha256(y.cpu().numpy().tobytes())`) and, once, of `token_bytes`, under `DisableTorchFunction`;
>   - after `model(...)` returns, recompute and compare before the cross-entropy; any change exits with its own code.
>   - Alternatively, keep `y` and `token_bytes` as immutable `bytes` and rebuild the tensors only after `model(...)` returns.
>   - Under Python 3.12, `f_locals` writes do not rebind a running frame's locals, so in-place mutation is the route, and a digest catches it. Under 3.13 (PEP 667), rebinding is possible too, which is one more reason for the census to run Python 3.12.
> - Report: add "introspect the wrapper's frames or the garbage collector to change its live tensors (targets, byte counts)" to the threat model, and add `sys._getframe`, `f_back`, `f_locals`, `inspect`, `gc.get_objects` / `gc.get_referrers` to the names to look for.
>
> ## Summary
>
> Round 8 closes the round-7 data-path route, and the new tests demonstrably guard it: they fail against the round-7 wrapper. There are no regressions, and the honest metric and the smoke values are unchanged.
>
> The one new MINOR finding (frame introspection rewriting `y` or `token_bytes`) needs deliberate code. It can be narrowed with a per-batch digest check and should be named in the threat model.

---

## Changed after acceptance (text only)

Round 8, finding 1 (from `forward`, frame introspection reaches the wrapper's live `y` and `token_bytes` and changes them in place) is answered as disclosure in commit `5fb552d3`, which adds to the threat model's list of what stays possible: "reach the wrapper's own live objects through frame introspection (`sys._getframe`, `inspect`, `gc`) and change them in place — for example the evaluation targets or byte counts while `model(x)` runs", and adds `sys._getframe`, `f_back`, `f_locals`, `inspect`, `gc.get_objects` / `gc.get_referrers` to the reading aid. The code narrowing the reviewer suggested (immutable copies of the targets and byte counts, rebuilt after each model call) is not applied; it is a candidate for the census-time frozen change together with the probe tolerance (open point 4). The census should run Python 3.12 (under 3.13 frame locals can also be rebound).

## For the author and the coordinator (from the report)

The report's open points: compute per token is editable while the budget fixes tokens (a proposal on timeouts, pending a decision); the dataset revision pin; one torch for both hosts; the causality probe's tolerance (tighten after the census measures the change); the harness changes that would close the in-process threat model. Nothing was measured; the kit is ENGINEERING_ONLY.

Code-Commit: 08d065077d40087114452697d5d596e66a0578be
Verdict: ACCEPTED

Accepted commit: `08d065077d40087114452697d5d596e66a0578be` (harness, round 8); report `432dbcfb8594b42d19217a3e5f65baf048b111c4`.
