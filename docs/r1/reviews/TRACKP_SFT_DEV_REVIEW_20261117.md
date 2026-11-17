Reviewed base: `bccd4301413ea46a3253bbf193963298a8d817b6` (branch `mac-trackp-sft-dev-20261117`; accepted in round 4)

# Independent review record — Track P SFT pipeline (R1-TRACKP-SFT-DEV)

**Unit.** The Stage S data builder, label sources, runner, CLI commands and configs (`r1/c3/train/sft_data.py`,
`r1/c3/train/sft.py`, `r1/scripts/trackp.py`, `configs/r1/trackp_sft.json`, `configs/r1/trackp_htcondor_v2.json`,
the `dataset.sweep_replay_inputs` refactor, `HashBagModel`) with their tests, and the report
`docs/r1/reports/TRACKP_SFT_DEV_20261117.md`, on `mac-trackp-sft-dev-20261117` over `main` `26177d82` with
`mac-w2-v3-rebuild-20261115` merged (`47e50b22`, the accepted W2 v3 rebuild, reviewed separately and outside this
scope). Authority: R1-TRACKP-SFT-DEV; queue of 17 Nov on `author-decisions-20261117b` @ `45fb94cc`.

**Process.** One independent reviewer for rounds 1 and 2 and one for rounds 3 and 4 (separate agents that did not
write the code). The reviewers edited nothing (in round 4 one `git checkout --detach` was attempted by mistake,
blocked, and changed nothing). The round texts are reproduced below as delivered, as block quotes, so that only this
record's own closing lines are read as the acceptance (rounds 2 and 3 name earlier commits).

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `6e872386` (diff from `47e50b22`) | NOT ACCEPTED (2 blocking, plus major and minor findings) |
| 2 | `b8668703` (diff from `6e872386`) | ACCEPTED (observations, none blocking) |
| 3 | `a26c0211` (diff from `b8668703`: the round-2 minors) | ACCEPTED (2 minor, 2 notes) |
| 4 | `bccd4301` (diff from `a26c0211`: the round-3 findings) | ACCEPTED (1 note) |

**Full `r1/tests` suite** (coordinator, Python 3.12 / torch 2.6 environment; failures are environmental —
transformers without the Qwen3.5 classes, no Hugging Face access): base `26177d82` 54 failed, 2,404 passed;
`a26c0211` 54 failed, 2,506 passed, 195 skipped, the same 54 failing tests; `bccd4301`: 54 failed, 2,506 passed, 195 skipped, the same 54 failing tests as on base.

---
## Round 1 (commit `6e872386`)

> # Independent review: Track P SFT pipeline (R1-TRACKP-SFT-DEV), commit 6e872386 vs 47e50b22
>
> Reviewer: independent code reviewer (AI-assisted, Claude). Scope: `git diff 47e50b22 6e872386` only (9 files). The merge 47e50b22 is out of scope. No file in the repository was modified. Scratch files are under `/tmp/rv_sft/`.
>
> **Verdict: NOT ACCEPTED**
>
> There are two blocking findings:
>
> - **F1.** The new Track P loaders do not enforce R1-BX-D8 or the `r1_sealed` refusal.
> - **F2.** P.4 `sft` used to STOP unconditionally (`NOT_YET`). It now runs as soon as an authorization note exists, and it does not check which labels it is given. With a note in place, an EVIDENCE-labelled run trains on synthetic labels or on sweep-1 labels without complaint.
>
> The rest of the unit is in good shape: the label-block reader, prompt binding, soft labels, splits, Stage S runner and the dataset refactor all check out. Both blocking fixes are small.
>
> ## What I verified (and how)
>
> - **Tests.** `r1/tests/test_trackp_sft.py`: **26 passed** (Python 3.12, torch 2.6 CPU). The five `build_from_sweep` test files (`test_c3_audit_dryrun`, `test_c3_evidence_guards`, `test_c3_sweep_table`, `test_d28_noise_binding`, `test_d8_sweep2_reader_refusal_matrix`): **220 passed, 1 skipped**.
> - **dataset.py refactor (checklist 6).**
>   - I read it line by line. The order of checks is unchanged; `refuse_sealed` now runs twice on the same inputs, which has no side effects; every returned value that `build_from_sweep` uses matches what the old code used.
>   - I rebuilt the sweep-1 table at **6e872386** through the refactored code with `build_from_sweep`, using the committed index and classification, into `/tmp/rv_sft/table_rebuild`. It reproduced `proposals.jsonl` `d0048567…` and `configs.json` `b585b727…` byte for byte. These are the pins in `trackp_sft.json`, which also match `W2_3_REBUILD_RUN_20261115.md` @ `2989f383`. **Behaviour-identical: confirmed.**
> - **Real-ledger `sft-data`.** I ran it through the CLI (synthetic labels, whitespace tokenizer) on that rebuild into `/tmp/rv_sft/sftdata`. It replayed all 4,999 proposals, and every one was bound to its table row by `features_hash`. Counts (1,725 labelled; 262 test rows withheld; 756/189 dropped; 378 train; 140 val) match the report and `/tmp/sftwork/real/smoke2.log`.
> - **Split counts.** I recomputed both duplicate policies with independent code and got the report's numbers.
> - **`campaign_prompts` vs `features.replay_campaign`.** Both use the same row filter (`decision == "skipped"` or no parsed metric, then `featurize_view is None`). The `ReplayView` construction is the same, and `_row_edit` has the same body in both. The `NodeContext` matches (`strict=True` start files, the node sigma, runs, memory mode). The proposal-id format `f"{source}:{instance}:t{b:03d}"` is the same. `instance=` only feeds error messages. **Exact.**
> - **Soft labels.** `labels.soft_label(delta, None, sigma_node, sigma_mode="pooled_node", k_label=5)` gives s = σ_node/√5, as R1-SOFT-SIGMA requires. Rule no-ops are one-hot on bin 0. The label's `sigma_node` must equal the table's. **Correct.**
> - **Stage S vs spec §6.1/§4.** Checked: RPS + CE; lr must be on {1e-5, 3e-5, 1e-4}; new heads at 1e-3; released heads at the adapter lr (`new_head_parameters`); token rows at 1e-4; AdamW; cosine with `int(0.05·total)` warm-up; micro-batch × accumulation = 16 (enforced); ≤ 5 epochs; evaluation every round(¼ · steps/epoch); early stopping on `val_rps` with patience 2; the best checkpoint is loaded back; temperature is fitted on val by soft-label cross-entropy after the best checkpoint is loaded.
> - **Val metrics.** These are computed on val instances' `y` only, which is the label-seed soft label. RPS skill uses the training base rate. I checked RPS, NLL, ECE, PIT and the width ratio against `metrics.py`. **Correct.**
> - **No path to the 7006–7010 seeds.** Within the SFT data and training path, nothing calls `verify_evidence_completion` or opens `evaluation_block.jsonl`, `runs.jsonl` or `audits.jsonl`. The test's `open` spy is meaningful: it also asserts that the label block and completion *were* opened. Table and output rows are scanned with `EVAL_COLUMNS`, and `Trainer` still runs `guard_rows`. Remaining gaps are in F5 and F13.
>
> ## Findings
>
> ### F1 — blocking — Track P loaders bypass R1-BX-D8 and `r1_sealed`
>
> - **Where:**
>   - `r1/c3/train/sft_data.py:382` (`load_table`)
>   - `r1/c3/train/sft_data.py:155–232` (`LabelBlockSource`)
>   - `r1/scripts/trackp.py:299–306` (`cmd_sft_data`)
> - **What R1-BX-D8 requires.** PLAN R1-BX-D8 says that every reader of sweep-2 label tables, "the Track P loaders" included, refuses to run without the exact `R1-BX-D8-CONFIRM` row. `test_d8_sweep2_reader_refusal_matrix.py` currently says the inventory "found no Track P loader of sweep-2 tables". This commit adds one, and explicitly for sweep 2 (`--label-sweep sweep2`).
> - **What the code does instead:**
>   - `sft_data.load_table` hashes and reads `proposals.jsonl` without calling `analysis_guard.guard_table`, which `dataset.load_table` does call.
>   - `LabelBlockSource` reads label values without any D8 check.
>   - Neither calls `refuse_sealed`.
> - **Probe.** `/tmp/rv_sft/scripts/test_probe_d8.py`, with `require_d8_confirmation` patched to STOP and a table whose `build.json` has unknown, sweep-2-like provenance:
>   - `dataset.load_table` refuses.
>   - `sft_data.load_table` opens 81 rows.
>   - `LabelBlockSource(sweep="sweep2").label_records()` reads 66 label values.
>   - A label block under `…/r1_sealed/…` is read, and a table under `…/R1_SEALED/…` is opened.
> - **CLI ordering.** In `cmd_sft_data` the table is hashed and read (line 299) *before* `sweep_replay_inputs` (line 305), the only place that can trigger the D8 check. With `--table-pin none --labels synthetic`, any table is read first. With `--sweep <sweep-1 index> --labels <sweep-2 label_block> --label-sweep sweep2`, no D8 check runs at all. The sweep-2 labels are read at line 306, and the run only fails afterwards, with "not in the table".
> - **Fix:**
>   - Call `guard_table(table_dir, table_dir/'proposals.jsonl', table_dir/'configs.json')` at the top of `sft_data.load_table`, before any hashing.
>   - In `LabelBlockSource.__init__`, call `refuse_sealed` on the label block, completion and freeze paths.
>   - For `sweep="sweep2"` (better: whenever the completion's `index_sha256` is not `SWEEP1_INDEX_SHA`), call `require_d8_confirmation()` before the first read.
>   - Add `sft_data.load_table` and `LabelBlockSource(sweep2)` to the D8 refusal matrix: build.json-only opens before the refusal, and the refusal must name R1-BX-D8-CONFIRM.
>
> ### F2 — blocking — P.4 `sft` became an EVIDENCE trainer with no label-provenance check
>
> - **Where:**
>   - `r1/scripts/trackp.py:363–365` (`cmd_sft = _stage_s`)
>   - `r1/scripts/trackp.py:324–360`
>   - `r1/c3/train/sft_data.py:93` (`LABEL_STATUS`)
> - **What changed.** Before this commit, `sft` was a hard `NOT_YET` STOP ("needs the full B.2 label table and … trackp_p4 note"). Now the authorization note is the only gate.
> - **Probe.** `/tmp/rv_sft/scripts/test_probe_cli.py`, with `authorization_note` returning a path and the base and lease stubbed: `sft --evidence EVIDENCE` on a **synthetic-label** data directory exits 0 and writes:
>   - `manifest.json` with `evidence_label: "EVIDENCE"`;
>   - `report.data.labels: "synthetic"`;
>   - `report.data.label_status: "ENGINEERING_ONLY (R1-TRACKP-SFT-DEV) … not used for any evidence"`.
> - **What is missing.** Nothing refuses any of the following under EVIDENCE:
>   - synthetic labels;
>   - sweep-1 labels, which R1-MAIN-PROPOSER (e) and spec §3.7 keep ENGINEERING_ONLY until sweep 2 exists;
>   - an unpinned table;
>   - a whitespace-tokenizer build;
>   - a label block whose `verify_evidence_completion` was never run. The data manifest itself says "not run in this process".
> - **Why this matters for the boundary.** The builder strips the evidence markers from rows, so `guard_rows`' "verified label-only boundary" check passes. But nothing verified the boundary. `evidence_boundary.py` warns about exactly this ("cannot identify a row whose origin markers have been removed … callers must validate source artifacts").
> - **Fix (either option):**
>   - Keep `sft` on `cmd_not_yet` in this ENGINEERING unit. This is the simplest, and matches the PLAN row's "readiness only".
>   - Or, in `cmd_sft` when the evidence label is not DRYRUN, require all of:
>     - (a) `manifest.labels.kind == "label_block"` and `sweep == "sweep2"`;
>     - (b) a table pin record for that sweep, plus `table_matches_audit_table is True`;
>     - (c) pool tokenizers;
>     - (d) an external verification record from a separate `verify_evidence_completion` run, bound to the completion sha256 and checked here;
>     - (e) a data `label_status` that is not the R1-TRACKP-SFT-DEV constant. Make `LABEL_STATUS` depend on the source rather than hard-coding it.
>   - Also refuse `--steps` and `--eval-every` overrides under EVIDENCE (see F12).
>
> ### F3 — should-fix — the split assignment depends on which instances are in the table; the "pure function" claim is wrong
>
> - **Where:**
>   - `r1/c3/train/sft_data.py:357–377`
>   - docstring at lines 37–40
>   - report §1.3 ("depends on the instance name only, so sweep 2 … gets the same assignment")
> - **What happens.** Instances of a node are ranked by hash, and the cut takes the first 3 as test and the next 3 as val. Adding or removing one instance therefore moves other instances between splits.
> - **Probe.** On the real sweep-1 instances, dropping the test instance `digits_mlp__s154` moves `digits_mlp__s244` from val to test, and `digits_mlp__s224` from train to val.
> - **Failure scenario.** R1-MAIN-PROPOSER (e)1 requires one instance → train/dev/test assignment for both sources. If a sweep-2 campaign fails or is excluded (R1-SWEEP2-ANY-GPU makes heterogeneous campaigns plausible), sweep 1 and sweep 2 disagree on an instance's split. The pooled or cross-proposer use then leaks the shared label (same instance, incumbent and edit, hence the same label) from one source's train set into the other's test set.
> - **Fix:**
>   - Assign from a fixed instance universe: the authorization's node × 18 seed list, carried in `trackp_sft.json`.
>   - Or add `--splits-from <splits.json>`, verify an identical assignment for every instance present, and refuse any unknown instance.
>   - Record the universe's sha in `splits.json`, and correct the docstring and report.
>
> ### F4 — should-fix — the HTCondor host config is not "usable unchanged"
>
> - **Where:**
>   - `r1/scripts/configs/trackp_htcondor_v2.json`
>   - report §4
>   - `r1/c3/train/run.py:138–147` (pre-existing lease code that the new claim relies on)
> - **Problems:**
>   - **(a) Missing sections.** R1-QTORCH-AMEND requires a Track P smoke and an E0 equivalence check on v2 per GPU model *before* training. The HTCondor config's own comment says the same. But the config has no `spike`, `toy_batch`, `e0` or `e3` sections. `trackp.py --config …htcondor_v2.json spike --tiny …` crashes with `KeyError: 'spike'`, and `e0` crashes with `KeyError: 'e0'` (both reproduced).
>   - **(b) Lease depends on git.** `gpu_lease` → `track_x_running` runs `git fetch origin main`. That call has a 60 s timeout, and `TimeoutExpired` is not caught, so a hang gives a traceback. It then needs `git show origin/main:docs/r1/STATUS.md` to succeed. On an HTCondor job without a git checkout that carries an `origin/main` ref, every `sft-dev` STOPs. The report does not mention this. The Track X portal check is also irrelevant on an exclusive HTCondor slot.
>   - **(c) Wrong GPU architecture.** `venv.causal_conv1d` says "built … sm_89", copied from the portal. H200 is sm_90, and the string is not a `TODO_VERIFY_ON_HOST` placeholder, so the cluster agent is not prompted to check it.
> - **Fix:**
>   - Copy `spike`, `toy_batch`, `e0`, `e3` and `kev_temperature` from `trackp_portal.json`.
>   - Mark `causal_conv1d` as `TODO_VERIFY_ON_HOST`.
>   - Either document that the job's checkout must be a git clone with a fetched `origin/main` (and catch `TimeoutExpired`), or add a host field (e.g. `"lease": "htcondor_slot"`) that replaces the Track X/STATUS check with the slot's exclusivity. Keep the `nvidia-smi` and flock checks.
>
> ### F5 — should-fix — `LabelBlockSource` does not bind the label block to the sweep or the table, and misses one sibling check
>
> - **Where:** `r1/c3/train/sft_data.py:171–232`
> - **Problems:**
>   - **(a) No sweep binding.** The completion carries `index_sha256` and `classification_sha256`, but they are neither checked against the `--sweep` index and `--classification` that the prompts replay, nor kept in the provenance (`keep` at line 221). `--label-sweep sweep1|sweep2` is an unchecked string: a sweep-2 block can be recorded as sweep 1 and vice versa.
>   - **(b) Mismatch allowed.** `table_matches_audit_table` can be `False` and the build proceeds. That is acceptable for ENGINEERING, but see F2(b) for EVIDENCE.
>   - **(c) Mixed-file sibling not refused.** `verify_evidence_completion` refuses a label block that sits next to `audits.jsonl`, the mixed file. This reader only refuses a *path* named `audits.jsonl`. The report's wording ("refuses … a mixed audits.jsonl") overstates this.
>   - **(d) Double read.** `sha256_file(self.path)` and then `read_text()` read the file twice (TOCTOU). The same pattern appears in `load_table` and `load_sft_data`.
> - **Fix:**
>   - Check `completion["index_sha256"]` against the sweep index sha, and derive `sweep1`/`sweep2` from it (sweep 1 iff it equals `SWEEP1_INDEX_SHA`) instead of trusting the flag. Check `classification_sha256` when a classification is given, and keep both in the provenance.
>   - Refuse when `(parent/'audits.jsonl').exists()`. `exists()` does not open the file.
>   - Read the bytes once, then hash and parse those same bytes.
>
> ### F6 — should-fix — two CLI test assertions pass for the wrong reason
>
> - **Where:** `r1/tests/test_trackp_sft.py:431–432`, `:415–420`
> - **Line 431.** The `sft-dev --base kev-0.8b --evidence EVIDENCE` assertion (`== 2`) passes because `R.check_environment` STOPs first ("kev: installed commit None is not the pinned 2074cc4…"), not because of the `sft-dev is ENGINEERING_ONLY` refusal. With `check_environment` patched out, the intended refusal does fire (probe), so the code is right and the test is vacuous.
> - **Line 415.** The comment says "pool tokenizers are required for real labels". The third `sft-data` call actually hits "an unpinned table is for synthetic dry runs only", so `_tokenizers`' refusal is never exercised.
> - **Elsewhere.** No STOP message is asserted anywhere in the CLI test.
> - **Fix:**
>   - Patch `check_environment` (and `authorization_note` where relevant), and assert the STOP text on stderr with `capsys`.
>   - Add a case with a pinned real-label path and `--tokenizers whitespace`.
>   - Add tests for F1, F3 and F5 (D8 refusal, split stability against the instance universe, sibling `audits.jsonl`).
>
> ### F7 — should-fix — factual errors and gaps in the unit report (`docs/r1/reports/TRACKP_SFT_DEV_20261117.md`)
>
> - **(a) §1.3, splits.** "The assignment depends on the instance name only" is false; see F3.
> - **(b) §2 and the `trackp_sft.json` `pin_comment`, rebuild commit.** Both say the local rebuild was "at main `26177d82`". The rebuild's `build.json` records commit `47e50b22`, and `26177d82` alone lacks `c3_features/v3`, so it could not produce these hashes. I re-confirmed the claim's substance at 6e872386 (see above). Fix the wording to `47e50b22` plus the refactor, or to 6e872386.
> - **(c) §2 table and §3(1), duplicate counts.**
>   - The "674" test proposals are counted over **all 822** test-instance table rows, 560 of which are unlabelled duplicates.
>   - Of the 262 **labelled** test proposals, 188 share a pair with train or val, so under `exclude_from_heldout` the labelled test population is **74** (about 9 per node).
>   - This number is what the author needs for the open decision and should be stated. Under `drop_from_train` the 188 stay in test, and the matching train and val rows are dropped.
> - **(d) §1.4, ablation.** "`loss: "rps"` for the CE-off ablation". Spec §6.1's ablation is "CE only"; see F8.
> - **(e) §1.2, who resolves the sweep.** It says "`sweep_prompts` resolves the sweep with `dataset.sweep_replay_inputs`". In fact the caller (`cmd_sft_data`) does, and `sweep_prompts` does not repeat `_replay_sources`' ledger-level `refuse_exam` or `refuse_sealed(manifest.json)` (F13). "The code path of `build-sweep`" is therefore only partly true.
> - **(f) §3(1), "both policies keep every pair inside one split of the data actually used".** Under `exclude_from_heldout` this holds only if a future P.4 evaluator honours `splits.json:test_proposals_seen_in_train_or_val`. No code in this commit consumes the list. Say so explicitly.
> - **(g) §3(5), host `sft` section.** The portal config does have an `sft` section (`effective_batch`, `max_epochs`, `warmup_frac`, `eval_every_frac`, `patience`, `seeds`). `_stage_s` reads only `micro_batch` from it and silently ignores the rest. See F15.
>
> ### F8 — minor — the spec's Stage S ablation is CE-only; the code offers RPS-only
>
> - **Where:** `r1/c3/train/sft.py:94–95, 113`
> - **Fix:** Accept `loss: "ce"`, giving `soft_ce` mean only. Keep `"rps"` if wanted, but label it as an extra.
>
> ### F9 — minor — some error paths give tracebacks instead of STOP (exit 1 instead of 2)
>
> - **Where:**
>   - `r1/scripts/trackp.py:297` (an unknown `--table-pin` raises `KeyError`)
>   - `:384–396` (only `SFTDataError` is converted)
>   - `sft-select` is not wrapped at all
> - **Cases that escape as tracebacks:**
>   - `json.JSONDecodeError` from a malformed label block or completion;
>   - `KeyError` on a malformed table row;
>   - `RuntimeError("STOP: resume with a different training config")` when `sft-dev` is rerun into the same `--run-dir` with another lr;
>   - `ValueError` from `select_lr` (unequal seed counts).
> - **Fix:** Wrap all four `sft*` commands. Convert `SFTDataError`, `ValueError`, `KeyError`, `json.JSONDecodeError`, and `RuntimeError` messages starting with "STOP" into `TrackPStop`.
>
> ### F10 — minor — a resumed run is not bound to its data directory
>
> - **Where:** `r1/c3/train/sft.py:107–112`
> - **Problem.** `Trainer.resume` checks only `TrainConfig.digest()`, which does not include the data. Rerunning `sft-dev --data <other dir>` into an existing run directory silently resumes training on different rows, and `report.json` then names only the new data.
> - **Fix:** Put the data directory's `sft_data.json` sha256 into `TrainConfig.extra`, so the digest changes and resume STOPs.
>
> ### F11 — minor — `sft-select` does not check what it compares, and carries no label status
>
> - **Where:** `r1/c3/train/sft.py:133–146`, `r1/scripts/trackp.py:368–373`
> - **Problem.** `select_lr` does not check that runs share one data sha and one protocol, or that seeds are distinct (two seed-0 runs count as two seeds). Its output does not carry the data `label_status`. A `selected_lr` computed on sweep-1 ENGINEERING data could then be carried into sweep-2 training. The PLAN row says outputs are "not used for any … selection or tuning".
> - **Fix:**
>   - Read each run's `report.json` `data.sft_data_sha256` and `protocol`, and require them to be equal.
>   - Require distinct seeds, and three of them per spec §4.
>   - Copy `label_status` into the output and print it.
>
> ### F12 — minor — protocol overrides are accepted on real runs
>
> - **Where:** `r1/scripts/trackp.py:345` (`max_steps=args.steps`, `eval_every_steps=args.eval_every`)
> - **Problem.** On non-tiny `sft-dev` and `sft`, these silently depart from §6.1 (≤ 5 epochs, ¼-epoch evaluation). They are recorded in the train-config digest but not flagged.
> - **Fix:** Refuse both flags unless `--tiny`, or at least unless the evidence label is ENGINEERING_ONLY. Write `protocol_deviation: true` into the report.
>
> ### F13 — minor — `sweep_prompts` does not repeat `_replay_sources`' EXAM and sealed checks at ledger level
>
> - **Where:** `r1/c3/train/sft_data.py:317–339`
> - **Problem.** `_replay_sources` runs `refuse_exam(records)`, `refuse_exam(inst)` and `refuse_sealed(d, d/'manifest.json')`. `sweep_prompts` runs only `refuse_sealed(d)`. The index and manifest checks still happen via `sweep_sources`, and an exam ledger would end up as a stray prompt and be refused, but only after it has been read and replayed.
> - **Fix:** Call the same `refuse_exam` checks per ledger before replay.
>
> ### F14 — note — LONO folds put other nodes' test instances in test too
>
> - **Where:** `r1/c3/train/sft_data.py:368–376`
> - **Problem.** With `holdout_nodes`, the other nodes still lose their 3 test instances each, and `splits.json` does not separate "held-out node" from "in-distribution test". The future evaluator must filter by node. Leave-one-suite-out (primary since R1-BX-D1) is not implemented; T1 data does not exist yet, so this is acceptable for this unit, but it should be listed.
>
> ### F15 — note — two sources of truth for the Stage S protocol
>
> - **Where:** `trackp_portal.json` → `sft` vs `trackp_sft.json` → `train`
> - **Problem.** The portal's `sft.effective_batch`, `max_epochs` and the other protocol values are ignored.
> - **Fix:** Drop them from the host config, or have `_stage_s` refuse a host `sft` key other than `micro_batch`/`comment` when it disagrees.
>
> ### F16 — note — other observations (no action required for this unit)
>
> - **Step-0 candidate.** The step-0 evaluation makes the untrained model a best-checkpoint candidate. This is inherited `Trainer` E0 behaviour; for a released Kev pointer head it can be selected. Disclose this in the report.
> - **Run-log item missing.** Spec §4 lists "mass on bin tokens (BinTokenWrapper)", which the eval hook does not log, and the model does not expose it. Decision-utility and action terms are rightly absent.
> - **Gate folds differ.** `offline_eval` (the gate) uses instance cross-fitting folds (`folds_by_instance`), while the SFT pipeline uses a fixed 3/3/12 split. P.4 and B.7 will have to reconcile them. Out of scope here.
> - **DRYRUN on a real base.** `sft --evidence DRYRUN --base …` runs a real-base P.4 Stage S without the note. This is the same pattern as the other phases, and the output is labelled DRYRUN.
> - **B.2 format.** `audit.evidence_run` is currently hard-blocked by `_require_task_native_runtime_attestation`, and B.2 is at STOP. The reader targets today's `evidence_blocks` row format and accepts any `r1.c3_audit_completion/*` schema; the test fixture uses `/3`. If B.2's eventual writer changes the label row schema, the reader fails closed (unknown fields), which is the right direction.
> - **Report numbers confirmed.** The table pins, the authority commit (`45fb94cc` exists; its PLAN carries R1-TRACKP-SFT-DEV and R1-QTORCH-AMEND, and the image digests in the HTCondor config match), the 466 audit configurations ((node, hash) jobs over the 1,725 eligible proposals), "26 tests" and the smoke counts are all confirmed.
> - **Not re-run.** The report's statement about 11 `test_trackp_model.py` failures that also occur on the base commit, and the full suite.
>
> ## Minimum to reach ACCEPTED
>
> 1. Fix F1: D8 and `r1_sealed` in `sft_data.load_table` and `LabelBlockSource`, with tests in the D8 refusal matrix.
> 2. Fix F2: either keep `sft` as `NOT_YET` in this unit, or add the EVIDENCE preconditions listed there, with tests.
> 3. Correct the report (F7) and the split docstring (F3). Fixing F3's mechanism can wait for the sweep-2 unit, but the false claim must go now.
> 4. Make the CLI tests assert the STOP reasons (F6).
>
> F4, F5 and F8–F13 should be fixed before the cluster agent or the experiment agent run this code on real labels.
>
> ## Scratch artefacts
>
> - `/tmp/rv_sft/scripts/test_probe_d8.py` and `/tmp/rv_sft/probe_d8.txt`: F1 probe.
> - `/tmp/rv_sft/scripts/test_probe_cli.py` and `/tmp/rv_sft/probe_out.txt`: F2 and F6 probe.
> - `/tmp/rv_sft/table_rebuild/`: sweep-1 table rebuilt at 6e872386; hashes equal the pins.
> - `/tmp/rv_sft/sftdata/`: real-ledger `sft-data` run through the CLI.

---

## Round 2 (commit `b8668703`)

> # Independent review, round 2: Track P SFT pipeline (R1-TRACKP-SFT-DEV), b8668703 vs 6e872386
>
> Reviewer: independent code reviewer (AI-assisted, Claude).
> Scope: `git diff 6e872386 b8668703` (8 files), checked against the round-1 findings in `/tmp/rv_sft/review_r1.md`, plus a search for regressions and new problems.
> Repository untouched: `git status` is clean and HEAD is `b866870354ee9dafb8ab054a4a15e98b94566154`. Scratch files are under `/tmp/rv_sft/`.
>
> Code-Commit: b866870354ee9dafb8ab054a4a15e98b94566154
>
> **Verdict: ACCEPTED**
>
> ## What I ran
>
> ### Tests
>
> - `test_trackp_sft.py` plus the five `build_from_sweep` / D8 test files: **281 passed, 1 skipped**.
>   - `test_trackp_sft.py` alone: **31 passed**.
>   - D8 refusal matrix: 197 cases. The 30 cases for the new `sft_data` readers all pass.
> - Related Track P tests (`test_trackp_cli`, `test_trackp_trainer`, `test_trackp_serialize`, `test_trackp_losses_metrics`, `test_trackp_e0_v2`): 45 passed, 7 failed, 27 skipped.
>   - All 7 failures are the same environmental `ImportError`: this env's transformers has no `Qwen3_5TextConfig`.
>   - The error is raised at `tiny.py:31`, which this branch does not change. They are not regressions.
> - Not run: the full suite (the coordinator runs it). I have not verified the report's full-suite numbers.
>
> ### Real-ledger CLI rerun at b8668703
>
> - I ran `sft-data` on my sweep-1 rebuild from round 1, whose hashes equal the pins. Output is in `/tmp/rv_sft/sftdata2`.
> - Universe: 144 instances, `configured instance universe`, sha `0bf613f5…`.
>   - The configured universe (8 nodes × 18 via `e1b_collect._instance_seed`) equals the table's 144 instances exactly.
>   - Split sizes are 24 / 24 / 96.
> - The split assignment is identical to round 1, and `rows.jsonl` is byte-identical to round 1 (sha `785478a9…`).
> - The new counts `labelled_test_proposals` 262 and `labelled_test_seen_in_train_or_val` 188 match my round-1 independent recount.
>
> ### Probes
>
> - **D8 and `r1_sealed` probe** (`/tmp/rv_sft/scripts/test_probe_d8_r2.py`, output in `probe_d8_r2.txt`), with D8 patched to STOP:
>   - refused: `sft_data.load_table` on a table with sweep-2-like provenance;
>   - refused: `LabelBlockSource` with the `sweep2` flag;
>   - refused: `LabelBlockSource` with the `sweep1` flag but a sweep-2 completion;
>   - refused (`r1_sealed`): a label block under `r1_sealed` and a table under `R1_SEALED`;
>   - refused: `--label-freeze runs.jsonl`;
>   - read normally: a valid sweep-1 block (66 records).
> - **HTCondor config, dry runs:**
>   - `spike` now gets past `cfg["spike"]`. It stops later only because `hashbag` is not a spike family; see N3.
>   - `sft --tiny` STOPs with the "not enabled in this unit" text.
>   - `sft-dev --tiny` completes: the report carries `data_sha256`, `label_status`, `protocol_deviation`, and `micro_batch` 8 (the tiny default).
> - **D8 already confirmed here:** `require_d8_confirmation()` passes in this checkout, because PLAN carries an `R1-BX-D8-CONFIRM` row. So a deepthought table copied to another host with this checkout is not refused off-host; its provenance check is satisfied. The report's "elsewhere copy it" instruction holds for this checkout.
>
> ## Round-1 findings: status
>
> | # | round-1 finding | status | verification |
> |---|---|---|---|
> | F1 | D8 / `r1_sealed` in the new loaders | **fixed** | See the four bullets after the table. |
> | F2 | P.4 `sft` became an EVIDENCE trainer | **fixed** | `"sft": cmd_not_yet`, with the preconditions spelled out; `cmd_sft` is removed. The CLI test asserts "not enabled in this unit" even with an authorization note patched in. |
> | F3 | split depends on which instances the table holds | **fixed** | `assign_splits(..., universe=)` orders the universe, not the table, and refuses table instances outside it. `cmd_sft_data` passes the configured universe for every pinned table. `splits.json` records the universe source, n and sha. A stability test drops instances one at a time. Real data reproduces round 1 exactly. Dry runs without a pin are labelled "the table's instances (dry run; not a fixed universe)". |
> | F4 | HTCondor config not usable unchanged | **fixed** | The `spike`/`toy_batch`/`e0`/`e3`/`kev_temperature`/`jev`/`rb_demos` sections equal the portal's (the test asserts it). `causal_conv1d` is `TODO_VERIFY_ON_HOST`. With `"lease": "htcondor_slot"`, `_lease` passes `status_text=""`, so `track_x_running("")` is False and nothing runs `git fetch` or `origin/main`. The marker, flock and `nvidia-smi` checks remain. |
> | F5 | label block not bound to its sweep; sibling check missing | **fixed** | Index and classification hashes are compared against the replayed index/classification. The sweep is derived from `index_sha256` and must equal the flag. A missing `index_sha256` is refused. A sibling `audits.jsonl` is refused. Bytes are read once and the same bytes are hashed and parsed (also in `load_table` and `load_sft_data`). Both hashes are kept in the provenance. Each case is tested. |
> | F6 | vacuous CLI assertions | **fixed** | Every STOP is asserted by its stderr text. `check_environment` is patched to raise `AssertionError` if it is reached, so the `sft-dev --evidence EVIDENCE` refusal is now proven to come first (it moved into `main` ahead of the environment check). New cases: whitespace tokens with real labels; unknown pin. |
> | F7 | report errors | **fixed** | Universe wording, the `47e50b22` rebuild wording, the 262 / 188 / 74 table, CE-only ablation, the resolver attribution, the exclusion list being advisory, the host `sft` section, and new open points 7 and 8. The changed claims I checked against code and data are all accurate. |
> | F8 | CE-only ablation | **fixed** | `loss: "ce"` uses `soft_ce`; there is a test against an analytic value; unknown losses are refused. |
> | F9 | tracebacks instead of STOP | **fixed** | All three live SFT commands are wrapped: `TrackPStop` passes through; `ValueError`/`KeyError` (including `JSONDecodeError` and `SFTDataError`) become STOP; `RuntimeError` becomes STOP only if it starts with "STOP". The resume-with-another-lr case is tested through the CLI. |
> | F10 | resume not bound to the data | **fixed** | `TrainConfig.extra = {"sft_data_sha256": …}`; a resume on other data STOPs (tested). |
> | F11 | `sft-select` checks | **fixed** | It requires one data sha, protocol and label status across runs, no protocol deviation, three distinct seeds per lr, and no duplicate seed. The label status is carried into the output and printed. |
> | F12 | protocol overrides on real runs | **fixed (as offered)** | Overrides are recorded as `protocol_deviation`, and `sft-select` refuses deviating runs. They are still allowed on `sft-dev`; that is acceptable now that `sft` is "not yet". |
> | F13 | ledger-level exam/sealed checks | **fixed** | Same `refuse_exam` (source, manifest, instance, records) and `refuse_sealed(d, d/manifest.json)` as `_replay_sources`, all before replay. |
> | F14 | LONO held-out nodes | **fixed** | `splits.json` has a `holdout_nodes` list. |
> | F15 | two sources of protocol truth | **fixed** | Host `sft` keys other than `micro_batch`/`comment` must equal `trackp_sft.json` or the run STOPs. The portal's values agree. |
> | F16 | notes | **addressed** | Step-0 candidacy, bin-token mass and gate folds are now disclosed in the report and the `sft.py` docstring. |
>
> How F1 was fixed:
>
> - `sft_data.load_table` calls `guard_table(table_dir, proposals, configs)` before reading any bytes.
> - `LabelBlockSource.__init__` calls `refuse_sealed` on all three paths.
> - `require_d8_confirmation()` runs before any file read for `sweep="sweep2"`. It also runs before the label block is read whenever the completion's `index_sha256` is not `SWEEP1_INDEX_SHA`.
> - `cmd_sft_data` resolves the sweep before it touches the table. Both readers are in the D8 matrix with `label_block.jsonl` in `LABEL_FILES`, and pass. The new unit test also asserts that neither `label_block.jsonl` nor `proposals.jsonl` is opened before the refusal.
>
> ## New observations (none blocking)
>
> - **N1 — note — completion read before the D8 check in one case.**
>   - Where: `sft_data.py`, `LabelBlockSource._load`.
>   - What: with `sweep="sweep1"` and a non-sweep-1 completion, the completion JSON is read before `require_d8_confirmation()`. The completion holds hashes and counts only (no label values), like `build.json` for tables, and the label block itself is still guarded.
>   - Suggestion: if you want the strictest reading of the matrix rule ("nothing but metadata"), document the completion as metadata in the matrix docstring.
> - **N2 — minor — classification binding is optional.**
>   - Where: `trackp.py`, `cmd_sft_data`.
>   - What: the classification binding applies only if `--classification` is given. The pin record names the sweep-1 classification, but nothing makes it mandatory. Without it, a label block's `classification_sha256` goes unchecked and `sweep_replay_inputs` runs without the sidecar.
>   - Suggestion: when `pin_record["classification"]` is set, require `--classification` to resolve to that path, or at least to that sha.
> - **N3 — minor — `--family hashbag` reaches non-SFT commands.**
>   - What: `spike --tiny --family hashbag` ends in an `AttributeError` traceback (`HashBagModel` has no `describe`).
>   - Suggestion: restrict `hashbag` to `sft-dev` in `_build`, or make argparse refuse it elsewhere.
> - **N4 — minor — `select_lr` accepts a partial grid.**
>   - What: `select_lr` does not require every lr of `protocol["lr_grid"]` to be present, so a grid with one lr missing still "selects". This does not matter under R1-TRACKP-SFT-DEV, where no selection is used.
>   - Suggestion: add the check before any later evidence use.
> - **N5 — note — broad error conversion.**
>   - What: `_sft_errors` turns every `ValueError`/`KeyError` into a STOP (exit 2) with the exception type in the message. This is fail-closed, but a genuine bug will also look like a STOP; the type name in the message keeps it diagnosable.
> - **N6 — trivial — style.**
>   - Where: `trackp.py` around `NOT_YET` / `_sft_errors`.
>   - What: missing blank lines before `def _sft_errors` and two stray blank lines where `cmd_sft` was removed (PEP 8, E302/E303).
> - **N7 — note — unverified numbers.** I did not verify the report's full-suite figures (54 failed / 2,471 passed, the same 54 as the base) or the "197 passed" for the whole matrix; the 30 new-reader matrix cases passed here.
>
> ## Conclusion
>
> Every round-1 finding is fixed. The two blocking findings are closed:
>
> - **F1:** the new loaders now enforce R1-BX-D8 and `r1_sealed`, with matrix coverage.
> - **F2:** P.4 `sft` is back to "not yet".
>
> No regression found: the `build_from_sweep` tests, the D8 matrix and the Track P CLI tests pass, the real-ledger output is byte-identical to round 1, and the dataset refactor accepted in round 1 is unchanged.
>
> I found nothing in the SFT data or training path that opens or ingests evaluation-seed data (7006–7010). The remaining observations (N1–N7) are minor and can go into the next unit.
>
> ## Scratch artefacts
>
> - `/tmp/rv_sft/scripts/test_probe_d8_r2.py` and `/tmp/rv_sft/probe_d8_r2.txt`: D8 / `r1_sealed` / freeze probes against b8668703.
> - `/tmp/rv_sft/sftdata2/`: real-ledger `sft-data` through the CLI at b8668703.
> - `/tmp/rv_sft/sftdev_htc/`: `sft-dev --tiny` with the HTCondor config.
> - `/tmp/rv_sft/table_moved/`: off-host copy check (not refused, because D8 is confirmed in this checkout).

---

## Round 3 (commit `a26c0211`)

> # Independent review, round 3: Track P SFT follow-up (round-2 minors), a26c0211 vs b8668703
>
> Code-Commit: a26c02113a508ac2b8b4a84cd11abe6dc26e07ef
>
> **Verdict: ACCEPTED**
>
> Reviewer: independent code reviewer (AI-assisted, Claude).
>
> Scope: `git diff b8668703 a26c0211`, 3 files, +18 / −2:
> - `r1/c3/train/sft.py`
> - `r1/scripts/trackp.py`
> - `r1/tests/test_trackp_sft.py`
>
> I checked each change against the round-2 "New observations" (`/tmp/tgsrc/reviews/sft_r2.md`), looked for regressions, and checked the report `docs/r1/reports/TRACKP_SFT_DEV_20261117.md` against the changed code.
>
> The repository is untouched: `git status` is clean. Scratch files were only under `/tmp/rv_sft3/`.
>
> ## What I ran
>
> - **`r1/tests/test_trackp_sft.py`** (the only test file the diff touches), with the given command (`TMPDIR=/tmp/rv_sft3/tmp`, `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin`, `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider`): **31 passed**.
> - **Related files:** `test_trackp_cli.py` and `test_d8_sweep2_reader_refusal_matrix.py`: **197 passed, 9 skipped**. The skips are in `test_trackp_cli`, which needs the environment.
> - **Searches:** no other test uses `--family hashbag`, `select_lr` or `--table-pin`, so the new refusals cannot break other tests.
> - **Full suite:** not rerun by me. The coordinator reports 54 failed / 2,506 passed / 195 skipped at a26c0211, with the same 54 failing test ids as base `26177d82`.
> - **Probe `/tmp/rv_sft3/scripts/probe_r3.py`** on `select_lr`, output in `/tmp/rv_sft3/probe_r3.txt`:
>
>   | input | result |
>   |---|---|
>   | full grid | selects 1e-4 |
>   | one lr missing | refused with "not the whole grid" |
>   | protocol without `lr_grid` | selects; the check is skipped (see F2) |
>   | grid as JSON strings | selects |
>   | CLI `float("3e-5")` vs JSON `3e-05` | equal, so the exact float comparison is safe |
>
> - **Code reading:**
>   - `cmd_sft_data`, `dataset.sweep_replay_inputs` and `evidence_classification`;
>   - the `LabelBlockSource` classification check (`sft_data.py:216`);
>   - the `main()` order of checks;
>   - the PLAN row `R1-SWEEP1-CLASSIFY`;
>   - the `trackp_sft.json` table pin.
>
> ## Round-2 observations: status
>
> | # | round-2 observation | status | verification |
> |---|---|---|---|
> | N1 | completion read before D8 in one case (note) | not addressed (optional) | Unchanged. It was a documentation-only suggestion and the label block is still guarded. Fine to leave. |
> | N2 | classification binding optional | **fixed** | See "How N2 is fixed" after the table. |
> | N3 | `--family hashbag` reaches non-SFT commands | **fixed** | See "How N3 is fixed" after the table. |
> | N4 | `select_lr` accepts a partial grid | **fixed** | Runs must cover exactly the sorted `protocol["lr_grid"]`. `protocol` is already required to be identical across runs, so taking it from `reports[0]` is sound. The test `runs[3:]` asserts the refusal, and my probe confirms it. The check is skipped when the report's protocol has no `lr_grid`; see F2 (note). |
> | N5 | broad `ValueError`/`KeyError` to STOP conversion (note) | not addressed (optional) | Unchanged. It was a note, not a requested change. |
> | N6 | PEP 8 blank lines around `NOT_YET` / `_sft_errors` and where `cmd_sft` was removed | **not fixed**, although the commit message says "blank lines" | See F1. |
> | N7 | unverified full-suite numbers (note) | n/a | The coordinator's run covers it. |
>
> ### How N2 is fixed
>
> - `cmd_sft_data` now STOPs when `pin_record["classification"]` is set and `--classification` is absent. The check runs before the sweep, the table or labels are read.
> - Only presence is required, not the pinned path or sha. That is still sufficient, because a given sidecar always goes through `evidence_classification`. That function requires `decision_id == R1-SWEEP1-CLASSIFY`, the sweep-1 index, and a PLAN `R1-SWEEP1-CLASSIFY` row that contains the sidecar's own relative path and sha256.
> - That PLAN row names `results/r1/evidence/C3_sweep_classification_20261028.json`, sha `bb6d891c…`. This is the same path as the pin's `classification`, so only the pinned sidecar can pass.
> - With real labels, `LabelBlockSource` then compares the completion's `classification_sha256` with it. A missing value is also refused, because `None != sha`.
> - The CLI test asserts the "pass --classification" STOP. The pinned-mismatch test was adjusted to pass a sidecar; `sweep_replay_inputs` is stubbed in that test.
>
> ### How N3 is fixed
>
> - `main()` raises `TrackPStop` for `--tiny --family hashbag` with any command other than `sft-dev`. The check runs before the config load, the authorization check and the environment check.
> - Without `--tiny`, `--family` is ignored by `_build`, so no other path reaches `HashBagModel`.
> - `sft --tiny --family hashbag` now STOPs with "serves sft-dev only" instead of "not enabled in this unit". It is still a STOP (exit 2), so P.4 stays closed.
> - The test asserts the STOP for `spike`, and the `sft-dev --tiny --family hashbag` end-to-end run still passes.
>
> ## Findings
>
> No BLOCKING or MAJOR findings.
>
> ### 1. MINOR — N6 not done, but the commit message says it is
>
> - **Location:** `r1/scripts/trackp.py`. The diff makes no whitespace change in this file.
>   - Lines 389–392: four blank lines between `cmd_sft_dev` and `cmd_sft_select` (E303).
>   - Around line 410: the `NOT_YET = {…}` closing brace is followed directly by `def _sft_errors` with no blank line (E302).
> - **Failure scenario:** cosmetic only. A reader of the history (the commit subject ends "…; blank lines") would assume it was done, and a linter run would flag both spots.
> - **Fix:**
>   - Remove two of the four blank lines at 389–392.
>   - Add two blank lines before `def _sft_errors`.
>   - Or drop "blank lines" from the record of what was done.
>
> ### 2. NOTE — the grid check is skipped when the report has no `lr_grid`
>
> - **Location:** `r1/c3/train/sft.py:169–171` (`if grid and sorted(by_lr) != grid`).
> - **Failure scenario:** a report whose `protocol` lacks `lr_grid` (hand-made or older) skips the whole-grid check. Then one lr with three seeds "selects", as my probe shows.
> - **Why this is a note:** reports written by `run_stage_s` always carry the merged protocol (`{**DEFAULT_PROTOCOL, **protocol}`), which always has `lr_grid`. So real runs are covered.
> - **Fix (optional, before any evidence use):** raise if `lr_grid` is missing or empty, or fall back to `DEFAULT_PROTOCOL["lr_grid"]`. The test fixture `_report` already carries `lr_grid`, so a strict version would not break the tests.
>
> ### 3. MINOR — the report does not reflect the three new requirements
>
> Location: `docs/r1/reports/TRACKP_SFT_DEV_20261117.md`, which was not touched by a26c0211.
>
> - **§1.1, lines 32–33:** "…and the index the prompts replay (and the classification, when given)". For a pinned table, which real labels require, the classification is now mandatory. "When given" now reads as optional.
>   - Fix: "(and the classification sidecar, which a pinned table requires)".
> - **§1.4, lines 81–83:** the list of `select_lr` requirements ("one data directory, one protocol and one label status …, no protocol deviation, and three distinct seeds per lr") does not mention the new "covers the whole lr grid".
>   - Fix: add "every lr of the protocol's grid".
> - **§2, lines 95–98:** the list of CLI refusals asserted by STOP text does not mention the two new ones (a pinned table without `--classification`, and `--family hashbag` outside `sft-dev`).
>   - Fix: add both to the list.
>   - The "31 passed" count is still correct, because no test functions were added.
> - **Still correct:**
>   - The §4 run commands already pass `--classification`, so they work unchanged with the new STOP. So does the module docstring example at `trackp.py:30`.
>   - The `HashBagModel` row (line 24) and the "Offline dry run" line (line 193) use hashbag with `sft-dev` only, so they stay true.
>
> ### 4. NOTE — stale STOP text in `cmd_sft_dev` (outside this diff)
>
> - **Location:** `r1/scripts/trackp.py:386–387`.
> - **What:** the message says "P.4 evidence runs use `sft` with its authorization note", but `sft` is "not yet" in this unit.
> - **Why this is a note:** the text cannot be reached through the CLI, because `main()` refuses first with "P.4 evidence runs are a later unit". It is noted only for consistency.
> - **Fix (optional):** reuse the `main()` wording.
>
> ## Conclusion
>
> The three code changes are correct, minimal and tested. They close N2, N3 and N4:
> - **N2:** an absent classification is refused. A given one can only be the PLAN-bound pinned sidecar, through `evidence_classification`.
> - **N3:** hashbag is limited to `sft-dev`.
> - **N4:** a partial lr grid is refused.
>
> No regression found: `test_trackp_sft.py` has 31 passed, and the D8 matrix plus `test_trackp_cli` have 197 passed and 9 skipped. The coordinator's full-suite failures are the same 54 as on base.
>
> What remains is cosmetic and documentation:
> - N6 was not actually applied (F1).
> - The report misses the three new requirements (F3).
> - There are two notes (F2, F4).
>
> None of these blocks acceptance.
>
> ## Scratch artefacts
>
> - `/tmp/rv_sft3/scripts/probe_r3.py`: the `select_lr` probe.
> - `/tmp/rv_sft3/probe_r3.txt`: its output.
> - `/tmp/rv_sft3/tmp`: cleaned after the run.

---

## Round 4 (commit `bccd4301`)

> # Independent review, round 4: Track P SFT, answers to round 3 (bccd4301 vs a26c0211)
>
> Code-Commit: bccd4301413ea46a3253bbf193963298a8d817b6
>
> **Verdict: ACCEPTED**
>
> Reviewer: independent code reviewer (AI-assisted, Claude).
>
> Scope: `git diff a26c0211 bccd4301`, 4 files:
> - `r1/c3/train/sft.py`
> - `r1/scripts/trackp.py`
> - `r1/tests/test_trackp_sft.py`
> - `docs/r1/reports/TRACKP_SFT_DEV_20261117.md`
>
> I checked the diff against round-3 findings F1–F4 (`/tmp/rv_sft3/review_r3.md`).
>
> The repository is untouched: HEAD is `bccd4301` on `mac-trackp-sft-dev-20261117`, and `git status` is clean. I tried one `git checkout --detach`, by mistake; it was blocked by the permission system and changed nothing. The worktree was already at bccd4301. Scratch files were only under `/tmp/rv_sft3/`.
>
> ## What I ran
>
> - **`r1/tests/test_trackp_sft.py` and `r1/tests/test_trackp_cli.py`**, with the same command as round 3 (`TMPDIR=/tmp/rv_sft3/tmp`, `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin`, `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider`): **31 passed, 9 skipped**.
>   - The 31 passes are all `test_trackp_sft.py`.
>   - The 9 skips are the environment-dependent `test_trackp_cli` cases, as in round 3.
> - **Round-3 `select_lr` probe** (`/tmp/rv_sft3/scripts/probe_r3.py`), rerun at bccd4301:
>
>   | input | result |
>   |---|---|
>   | full grid | selects 1e-4 |
>   | one lr missing | refused with "not the whole grid" |
>   | protocol without `lr_grid` | **now refused** with "the runs' protocol has no lr_grid" |
>   | grid as JSON strings | selects |
>
> - **Searches:**
>   - No test or doc still asserts or quotes the old `sft-dev` STOP text ("use `sft` with its authorization note").
>   - The changed spots in `trackp.py` now have the PEP 8 spacing.
> - **Full suite:** not rerun by me.
>
> ## Round-3 findings: status
>
> | # | round-3 finding | status | verification |
> |---|---|---|---|
> | F1 | MINOR: N6 blank lines not applied | **fixed** | See "How F1 is fixed" after the table. |
> | F2 | NOTE: grid check skipped without `lr_grid` | **fixed** | See "How F2 is fixed" after the table. |
> | F3 | MINOR: report misses the new requirements | **fixed** | See "How F3 is fixed" after the table. |
> | F4 | NOTE: stale `cmd_sft_dev` STOP text | **fixed** | The text now reads "P.4 evidence runs are a later unit", identical to the `main()` refusal. No test depended on the old wording. |
>
> ### How F1 is fixed
>
> - The four blank lines between `cmd_sft_dev` and `cmd_sft_select` are now two.
> - Two blank lines were added between the `NOT_YET` closing brace and `def _sft_errors`.
>
> ### How F2 is fixed
>
> - `(protocol or {}).get("lr_grid") or []` handles a missing, `None` or empty grid. The `A or []` binds inside the generator's iterable, as intended.
> - An empty grid now raises `ValueError("…has no lr_grid…")`, which the CLI converts to a STOP through `_sft_errors`.
> - The new test covers it: three seeds of one lr with `protocol={"loss": "rps+ce"}` is refused with "no lr_grid". The `**more` override of `"protocol"` in `_report`'s dict literal works.
> - Order is unchanged:
>   1. same data, protocol and label status across runs;
>   2. no protocol deviation;
>   3. no duplicate seeds;
>   4. the grid present and covered;
>   5. three seeds per lr.
>
>   So the CLI test's `sft-select` on a deviating run still stops with "deviates from the protocol".
> - Real runs are unaffected, because `run_stage_s` always writes the merged protocol with `lr_grid`.
>
> ### How F3 is fixed
>
> - **§1.1:** now says the pinned table requires the classification sidecar, and that `sft-data` STOPs without `--classification` when the pin names one. This matches `cmd_sft_data`.
> - **§1.4:** now lists "a protocol with an `lr_grid`, every lr of that grid", which matches `select_lr`.
> - **§2:** the list of asserted STOPs now adds the two new ones. Both are asserted in `test_cli_dry_run_end_to_end`: a pinned table without `--classification`, and `--tiny --family hashbag` outside `sft-dev`.
> - **Full-suite line:** it adds "At `a26c0211`: 54 failed, 2,506 passed, 195 skipped, the same 54 failing tests as on base". This matches the coordinator's figures given to me in round 3; I did not rerun the suite.
> - "31 passed" is still correct, because the new check is inside the existing `test_select_lr`.
>
> ## New findings
>
> None at BLOCKING, MAJOR or MINOR level.
>
> ### 1. NOTE — the full-suite figure is for a26c0211, not bccd4301
>
> - **Location:** report §2, the full-suite line.
> - **What:** the line gives the figure at `a26c0211`. bccd4301 changes code: `select_lr` gets stricter, and a STOP string changes. No test outside `test_trackp_sft.py` uses `select_lr` or the changed string, so a different full-suite result is not expected.
> - **Fix (optional):** the coordinator's next full-suite run at bccd4301 can confirm it. The report is accurate as written, because it names the commit.
>
> ## Conclusion
>
> All four round-3 findings are addressed correctly, and no regression was introduced:
> - `test_trackp_sft.py`: 31 passed.
> - `test_trackp_cli.py`: 9 skipped, for the environment.
> - The probe confirms the new `lr_grid` refusal.
>
> The report now matches the code at every point this round touched.
>
> ## Scratch artefacts
>
> - `/tmp/rv_sft3/review_r4.md`: this review.
> - `/tmp/rv_sft3/scripts/probe_r3.py`: the probe, reused.
> - `/tmp/rv_sft3/tmp`: cleaned after the run.

---

## Open points for the author

The report's §3 lists them; among them the cross-split duplicate policy (`drop_from_train`, the default here, or
`exclude_from_heldout`, with their counts on the sweep-1 rebuild), and P.4 `sft`, which stays "not yet" in this unit.

---

Code-Commit: bccd4301413ea46a3253bbf193963298a8d817b6
Verdict: ACCEPTED

Accepted commit: `bccd4301413ea46a3253bbf193963298a8d817b6` (round 4).
