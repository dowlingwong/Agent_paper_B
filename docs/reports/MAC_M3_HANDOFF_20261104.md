# M3 hand-off — B.2 prerequisites (worker result, for independent review)

**4 November 2026. Mac-local worker (Claude), MAC_LOCAL_RUNBOOK_20261104 task M3; AI-assisted. This is a worker result to be reviewed, not accepted work.** Branch `mac-b2-20261104`, based on `codex/b2-repair-20261031` @ `f98e315e`. Not pushed.

## 1. Commits

| Commit | Content |
|---|---|
| `eacaf595` | Six stale test fixtures inherited from b2-repair (tests only; §4) |
| `7bf11d9c` | `r1/scripts/c3_env_replay.py` (replay driver) and its tests; `r1/scripts/c3_audit_dryrun.py` and its tests; `r1/c3/audit.py`: population partition factored into `partition_population` (behaviour unchanged) |
| `00447132` | Replay tests isolated from LLM modules imported by other tests; resource-check test |
| `aaf8cb60` | Gate table, dry-run report, e1 and e2 drafts |
| *(this file)* | Hand-off |

Untouched (verified with `git diff f98e315e HEAD`):
- `results/`;
- `r1/c3/env.py`, `control.py`, `prior_model.py`;
- `r1/c3/train/`;
- `r1/scripts/c3_label_sweep.py`;
- `docs/r1/PLAN.md`, `STATUS.md`, `RUNBOOK.md`;
- the harness.

## 2. Gate table summary (`reports/MAC_B2_GATES_20261104.md`)

- **Replay (e1).**
  - A4 offline execution remains OPEN. OpenML replay is refused before scheduling until an independently reviewed offline mechanism exists; the other gate entries remain subject to review.
  - Case selection, configuration recovery, patch verification and seed binding (A3–A6) are also verified on the frozen corpus.
  - A14–A16 are the author's note and the operator's run.
  - The e1 note cannot authorize execution yet: the OpenML offline mechanism and its independent review remain open (R1-B2-REPLAY-GO).
- **B.2 (e2).**
  - Closed: B2 (original-file mapping), B3 (complete plan), B5 (non-venv/version STOP), B9–B10 (split blocks, K = 10 design, duplicate and no-op rules), B13, B16, B17. B11 is closed within its stated, non-global scope.
  - Host: B7 (Ceph and scratch numbers), B8 (guard tests on deepthought), B14 (replay result).
  - **Open by design, needs the author:**
    - B1: review and publication. The guards require `origin/main`, which has neither the classification row nor `results/r1/evidence/`.
    - B4: task-native runtime attestation. Every EVIDENCE run and every consumption stops on it.
    - B6: no launch-bound freeze, and no code path accepting a passed replay instead.
  - Author: B15 (e2), B18 (the five files).
  - Open, not a B.2 condition: B12 (trusted label-only loader, before P.3b) and B19 (fake-service integration; environmental failures here).
- **Consequence:** even with e1 passed and e2 given, `r1.c3.audit evidence-run` on this branch stops at B4 and B6. The e2 draft lays out the author's choices. Implementing the chosen option is follow-up code with its own review.

## 3. Dry runs (`reports/MAC_M3_DRYRUNS_20261104.md`)

Both ran on a Git clone of `7bf11d9c` in session scratch, a copy of the frozen layout. The originals were only read.

- **Replay plan.** 16 cases (8 nodes × budget indices 1, 2). Every recovered configuration reproduces the ledger `patch_hash` and the archived `patch.diff`, and every archived original `run.log` carries the recorded token. The environment checks are deferred to the host.
- **Audit plan.**
  - Population: 4,999 proposals = 0 rule no-ops + 3,274 duplicates (no label) + 1,725 eligible, with counts by node and by memory mode.
  - Workload: 466 unique configurations, 4,660 seed runs.
  - Design: K = 10, label seeds 7001–7005 and evaluation seeds 7006–7010, disjoint.
  - Block rules hold on the real population, checked with synthetic placeholder metrics.

## 4. Tests before and after

Environment: Linux cloud workspace (not the Mac); `/home/claude/venv-r1` (Python 3.13); harness `897d83c` via `AR_HARNESS_ROOT`; `CUDA_VISIBLE_DEVICES=""`; HF offline. Command: `python -m pytest -q -p no:cacheprovider r1/tests`.

| Run | Commit | Result |
|---|---|---|
| base | `f98e315e` | 17 failed, 722 passed, 84 skipped |
| after | `00447132` (later commits change docs only) | 11 failed, 764 passed, 84 skipped |

- After = base − 6 fixed. **No new failure.**
- +42 passing tests: 31 in `test_c3_env_replay.py`, 5 in `test_c3_audit_dryrun.py`, and the 6 fixed.
- The remaining 11 are exactly the 11 environmental failures that M1 also recorded on the coordinator:
  - `test_c3_sweep_dryrun.py` (6): the fixture's `git cat-file -e 6adf385^{commit}` exits 128 in its harness copy;
  - `test_c3_control_dryrun.py` (1): "no data cache for openml_breast_w";
  - `test_rerun2_batch4c` (1);
  - three Track P byte-identity tests under these library versions.
- An intermediate full run at `7bf11d9c` showed 8 replay tests failing only inside the full suite. Other tests had imported `autoresearch.manager.langgraph_manager`, which the driver's LLM guard correctly treats as a STOP. `00447132` isolates the replay tests from that; the driver is unchanged.

### The six inherited failures: diagnosis and fix (all stale tests; no code was wrong)

| Test | Cause | Fix | Why the test, not the code |
|---|---|---|---|
| `test_c3_launch_provenance::test_manifest_mismatch_or_missing_is_a_stop` | The fixture builds the runner with `object.__new__`, so there is no `label` attribute. b2-repair's `check_launch_manifest` reads `self.label` for the EVIDENCE check. | Set `runner.label = 'ENGINEERING_ONLY'`, as `__init__` always does. | `__init__` always sets `label`. The production path cannot lack it. |
| `test_c3_launch_provenance::test_each_sweep_passes_the_original_launch_provenance[append_only_summary]`, `[none]` | The stub `lambda out: None` does not accept b2-repair's new keyword `engineering_liveness`. | The stub accepts the keyword. The test now also asserts that the resumed liveness manifest is checked with `engineering_liveness=True`. | The keyword is the intended interface (`9bab3d6f`), and the sweep path passes it correctly. |
| `test_c3_evidence_guards::test_evidence_environment_rejects_harness_import_spoof`, `…_rejects_wrong_locked_sklearn` | The test stubbed `audit.importlib.import_module` (the **global** `importlib`) and only then called `monkeypatch.setattr('r1.harness.import_harness', …)`. pytest resolves dotted targets with `importlib.import_module`, so the test crashed in setup and never reached the code. In a full session, harness modules imported by other tests would also trip the import check first. | Patch the `r1.harness` module object first, remove already-loaded `autoresearch*` modules for the test, and stub `import_module` last. | The fixture's own ordering made it crash before the code ran. With the ordering corrected, both assertions hold against the unchanged `evidence_environment`. |
| `test_c3_evidence_seed_isolation::test_evidence_missing_completion_cannot_be_consumed` | It expected `FileNotFoundError`. Since `7df307be`, consumption stops first on the missing task-native attestation (`ValueError`). Since `007a8d1c`, a mixed `audits.jsonl` path is refused outright. | Assert the attestation STOP. Then, with only the attestation bypassed, assert the `audits.jsonl` refusal, and finally the `FileNotFoundError` for a `label_block.jsonl` that has no completion record. | `7df307be` added the earlier STOP deliberately and updated a sibling test but not this one. The test's intent (missing completion is never consumed) is kept and still checked. |

## 5. The five out-of-scope changes of `9bab3d6f` (packet (a); in M3's scope by the author's 4 Nov 16:13 ruling; not changed)

All five come from one commit, `9bab3d6f`, and none was modified later on the branch. `git log 9bab3d6f..HEAD` on these paths shows no commits.

| File | Change | Behaviour change for **unmarked** rows | Tests |
|---|---|---|---|
| `r1/c3/train/run.py` | (1) `EVAL_COLUMNS` also matches the exact keys `delta_true`, `delta_audit_all`, `se_audit`, `candidate_metrics`, `incumbent_metrics`. (2) `_keys` also walks lists and tuples, depth-bounded at 6. (3) `guard_rows` first refuses any row that `is_identifiable_sweep_evidence` (marker `_evidence_seed_split: True`, `decision_id: R1-SWEEP1-CLASSIFY` or `label: EVIDENCE`, searched to depth 6, including `.meta`), unless `purpose == 'p4_final_eval'` and a P.4 note exists. | **Yes.** A row with no evidence marker but with one of the five keys, at any depth including inside lists, is now refused for every purpose except `p4_final_eval`, where it was accepted before. Keys nested in lists are now seen for the old patterns too. In-repo callers: `Trainer` only. No in-repo Track P code builds rows with these keys (searched `r1/c3/train`, `r1/scripts/trackp*.py`); external Track P tables carrying `delta_true` etc. would now be refused. | `test_c3_evidence_other_boundaries.py`: `test_trackp_guard_rejects_identifiable_sweep_training`, `…_eval_aliases_even_in_prompt_meta` ×5, `…_evaluation_fields_in_nested_sequences` ×2, `…_sequence_cycles_are_bounded`. Also `test_trackp_trainer.py` (existing). |
| `r1/c3/train/trainer.py` | `Trainer(..., purpose='p4_final_eval')` raises `TrackPStop` (a training interface is never the P.4 evaluator), then `guard_rows` as before. | Only for `purpose='p4_final_eval'`, which no in-repo caller passes. | `test_trainer_rejects_p4_even_with_authorization_and_accepts_synthetic_e0` (also checks that a synthetic E0 row is still accepted). |
| `r1/c3/env.py` | `OfflineBanditEnv.__init__` calls `refuse_unverified_sweep_rows(rows, 'OfflineBanditEnv')` before anything else. | **None**: only marked rows are refused. | `test_env_and_prior_reject_identifiable_sweep_rows` (both splits); `test_c3_env.py` (existing). |
| `r1/c3/control.py` | `fit_awr_direct` materialises `rows`, refuses marked rows, and widens the refused `value_key` set from `{"delta_true"}` to `{"delta_true", "delta_audit_all", "se_audit", "candidate_metrics", "incumbent_metrics"}`. | **Yes, narrowly.** `value_key='delta_audit_all'` (and the other three) is now refused for any rows, marked or not; before, only `delta_true` was. The default `delta_label` is unaffected. In-repo caller: `c3_control_dryrun.py`, which uses the default. | `test_awr_rejects_even_when_alias_is_supplied`; `test_c3_direct_arms.py::test_awr_training_never_reads_the_evaluation_half` (existing). |
| `r1/c3/prior_model.py` | `TableArmPrior.fit` materialises `rows` and refuses marked rows. | **None.** | `test_env_and_prior_reject_identifiable_sweep_rows`; `test_c3_prior_model.py` (existing). |

**Test status on this branch:**
- all 13 tests in `test_c3_evidence_other_boundaries.py` pass;
- `test_c3_direct_arms.py`, `test_trackp_trainer.py`, `test_c3_env.py` and `test_c3_prior_model.py` pass (42 + the 3 AWR tests in a targeted run);
- none of these tests is in the after-failure set.

**Review status:** their only review (`C3_EVIDENCE_GUARDS_REVIEW_20261028`) is BLOCK for B.2 launch and says the marker guards are not a proof of global isolation. This hand-off makes no acceptance claim.

**Overlap:** `trackS-ops-20261030` also changes `prior_model.py` (explicit `cache_prompt`). Not merged here; packet (a) already notes the three-way merge.

## 6. Deviations

1. **Tests ran in the Linux cloud workspace, not on the Mac.** The same exception M1 recorded (packet (k)); this is the environment the coordinator assigned.
2. **The dry runs used a Git clone of the worktree in session scratch as "a copy of the frozen corpus layout"**, not a plain file copy. History is needed for the tree and original-blob checks. The originals were only read.
3. **`r1/c3/audit.py` was edited** (refactor only: `partition_population` extracted from `evidence_plan`, with the same logic and messages). It is not a listed shared file. Covered by the existing `evidence_plan` tests, all of which pass.
4. **Replay comparison on the emitted token.** The draft says to compare "as emitted", with "original recorded precision". The driver compares the replayed log's token with the token in the **archived original `run.log`** (verified against its archive hash), and also requires float equality with the ledger value. This is my reading of "as emitted" and needs the reviewer's check.
5. **One worker for the replay.** The draft does not set a worker count. 16 runs of about 2 s each do not need parallelism, and serial execution makes "STOP at first mismatch, no retry" exact.
6. **OpenML data cache.** The driver copies the node directory from the batch harness as the `ccb4712` collector did. The cache-presence check cannot prove offline execution; every real replay containing OpenML cases currently STOPs before scheduling. The 16-case plan includes OpenML cases. An offline enforcement mechanism and independent review remain open; a dry run does not clear this gate.
7. **The full fake-service integration** that [AS] mentions (the fixture cloned the previous HEAD) was not repaired. The sweep dry-run failures are in the base set and are environmental here (B19).

## 7. Open questions (STOP items for the author or the integrator)

- **Q1 (B1, publication target).** The guards bind EVIDENCE authority to `origin/main`. R1-HANDOVER-04NOV and the runbook forbid agents to push `main`. Does the author publish the classification and review to `main` before B.2, or should the guards point to an author-pinned branch? This is a code change, which I did not make.
- **Q2 (B4 and B6).** What replaces (i) the missing launch-bound freeze, and (ii) the task-native attestation, once the replay passes? The options are in `proposals/AUTH_DRAFT_b2_20261104.md` Part 1. I did not implement any of them, because each would relax a STOP written in response to a BLOCK review.
- **Q3 (minor).** The replay draft quotes the 28 Oct package-list SHA256 `c09242ac…` without its serialization format. The driver records its own canonical `name==version\n` list and hash, and carries `c09242ac…` only as a reference, not as a check. If the author wants it as a check, the 28 Oct format must be recovered from the deepthought agent's records.
- **Q4.** `C3_B2_REPLAY_LLM_SCOPE_REVIEW_20261031` was written against `origin/ops/c3-sweep1-classify-20261028` @ `007a8d1c` and cites an attachment path on the author's Mac. Neither is on this branch. I used the review as committed on `mac-int-20261104`.

## 8. What the operator gets after acceptance

- **e1 (replay), once the OpenML offline gate is closed and the code independently accepted:** the accepted commit; `python -B -m r1.scripts.c3_env_replay --dry-run …` first, then the run, per `proposals/AUTH_DRAFT_c3_replay_20261104.md`.
- **e2 (B.2):** only after the e2 choices and the follow-up code for B1, B4 and B6.
