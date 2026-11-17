Reviewed base: `435513d2486cca21c514a3fa74bbcd5c1210c160` (branch `mac-e2-code-20261117`; accepted in round 3)

# Independent review record — e2 code unit (R1-B2-GO: B6 (a), B4 (a), B1 (a))

**Unit.** `r1/c3/audit.py` and its tests, `docs/r1/reports/E2_CODE_UNIT_20261117.md`, and Part 3 of
`docs/r1/proposals/AUTH_DRAFT_b2_20261104.md`, on `mac-e2-code-20261117` over `main` `26177d82`, with
`author-decisions-20261117b` @ `45fb94cc` and `ops-e1-replay-amend-20261117` @ `52992b22` merged (round 1, finding 2).
Authority: R1-B2-GO (`author-decisions-20261117b` @ `33c82351`, carried in `45fb94cc`).

**Process.** One independent reviewer (a separate agent that did not write the code), three rounds. The reviewer edited
nothing. The round texts are reproduced below as delivered, as block quotes, so that only this record's own closing
lines are read by `evidence_paper_provenance` as the acceptance (the round-2 text names an earlier commit).

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `7ea90eeb` (diff from `26177d82`) | NOT ACCEPTED (2 blocking, 1 major, 7 minor) |
| 2 | `fcd8f951` (diff from `7ea90eeb`, including the two merges) | ACCEPTED (3 minor) |
| 3 | `435513d2` (diff from `fcd8f951`: the round-2 minors) | ACCEPTED (no findings) |

---

## Round 1 (commit `7ea90eeb`)

> Independent review: e2 code unit (R1-B2-GO), branch mac-e2-code-20261117 (eb9306b8, 62a5081e, 7ea90eeb over main 26177d82)
>
> I did not edit, commit or push anything. Scratch went only under /tmp/rv_e2/. I did not read secrets and used no server or SSH access.
>
> **Result:** the three replacements are written as ruled. But the evidence run cannot start on deepthought the way the report describes, because of two deadlocks. There is also one conflict with the e1 review that would make the evidence unusable later.
>
> ## What checks out (verified against the code)
>
> **Pinned hashes**
> - All six `E1_REPLAY_PINNED` sha256 values (summary.json, pins.json, REPORT.md, cases.jsonl, SHA256SUMS.txt, E1_AMEND_RUN_REVIEW) equal the bytes at 52992b22.
>
> **B6 (a)**
> - I built a scratch origin whose main merges ops-e1-replay-amend, author-decisions-20261117b and e2. On it, `replay_environment_basis` passes using the real published bytes.
> - The PLAN-row match, the 16/16 PASS at tolerance 0 under R1-E1-OPENML-AMEND, the review's last line and the runtime pins all hold.
> - `replay_environment_checks` calls `c3_env_replay.check_environment`. That function is the same as the one the reviewed run used: `git diff gh/main bbcfc4a9` does not touch it, its helpers (probe, canonical_packages, wrapper_target, parse_freeze) or the constants it uses.
> - It is called with the same arguments as e1: batch, plus batch/autoresearch_harness, which equals pins.harness.path.
> - The recorded values are compared correctly. pins.json takes package_list_sha256 from check_environment's `current_package_list_sha256` (via build_pins.py:111; replay_plan.json carries the same c09242ac…), so the format matches. Build, prefix, wrapper_target and newest dist-info mtime come from the same record.
>
> **B1 (a)**
> - `_published_bytes` fails closed when origin is unreachable. I also tested with real git: a stale fetched origin/main gives "origin/main is stale…".
> - It reads the published bytes, never the working tree.
> - The old guards (`_verify_published`, `evidence_paper_provenance`) are unchanged, so I found no way for unpublished or changed authority files to be accepted.
>
> **B4 (a)**
> - `_require_task_native_runtime_attestation` is removed from both the run and the consumption path.
> - `worker_runtime` and `validate_worker_records` are byte-unchanged.
> - `worker_runtime_basis` (with the limitation) is written into environment.json and evidence_completion.json (schema /3), and both are compared again on consumption.
>
> **Everything else unchanged**
> - Harness 6adf385, DEFAULT_SEEDS and the 7001–7005 / 7006–7010 split, partition_population and the population counts.
> - evidence_resources (at most 16 workers, below the CPU count), scratch, Ceph floors and output path.
> - The per-seed-run validity rules, STOP.json handling and the deadline.
> - The only diff hunks are the environment basis, the addendum and the completion schema.
>
> **Addendum guard**
> - It is an extra STOP, consistent with R1-B2-GO's precondition ("作者提交 B.2 授权补充文件（Part 3 填好）"), and the report discloses it.
> - It does not create a circular dependency: code commit, then review, then addendum.
>
> **Tests**
> - The five evidence modules: 65 passed (np244).
> - Whole r1/tests on e2: 29 failed, 2384 passed, 154 skipped, which matches the report.
> - I ran those same 29 tests on the unchanged base 26177d82 and all 29 failed. My full base run was cut off twice when the sandbox disk filled and the environment restarted, so I could not compare the full base pass count. The failing tests do not touch audit.py.
>
> **Part 3 facts**
> - These match: authorization 563374f6…, sidecar bb6d891c…, index 812468e2…, b713c42338c4…/b585b7275866…, 4,999 / 1,725 / 466 / 4,660 / 3,274, 40 CPUs (pins.host).
> - The command flags match the evidence-run CLI.
> - The ≥ 10 free cores rule and deepthought CPU follow R1-B2-GO.
>
> ## Findings
>
> **1. BLOCKING: the forced batch harness fails the unchanged clean-harness check (deadlock).**
> - audit.py:512-516 now requires `AR_HARNESS_ROOT` to be the e1 harness path, `<batch>/autoresearch_harness`.
> - audit.py:554-555 still refuses any `git status --porcelain --untracked-files=all` output.
> - The e1 record says that harness has untracked files. pins.json @52992b22, harness.pre_existing_untracked_note: "the six nodes/*/data_cache directories and paper/tables/artifact_completeness_report.txt were already untracked".
> - In a clone at 6adf385, only climate/sonar/bank/blood/credit_g/qsar ship a data_cache/.gitignore. Cache files for openml_breast_w, credit_approval, ionosphere and wdbc, and the report txt, show as `??`. The preflight log shows those four caches present and without a .gitignore.
> - So evidence_environment STOPs before any run. Moving or deleting those files is not allowed in the preserved batch and would remove the OpenML caches.
> - The operator can confirm read-only with `git -C <batch>/autoresearch_harness status --porcelain --untracked-files=all`.
> - Fix (needs the author, since it changes a STOP). Either:
>   - (a) accept tracked-clean plus an explicit allowlist of exactly the untracked paths e1 recorded, with the cache tree digests required to equal the e1 OFFLINE_MECHANISM_AUDIT values; or
>   - (b) drop the harness-path equality and supply the audited caches another reviewed way.
> - Add a test using the e1 harness state.
>
> **2. BLOCKING: PLAN.md byte-identity versus the code-commit checkout makes the report's merge order unrunnable.**
> - `evidence_paper_provenance` (audit.py:602-607) requires `HEAD == code_commit`.
> - `evidence_classification` (dataset.py:290) requires the local docs/r1/PLAN.md to be byte-identical to origin/main's.
> - Every commit on this branch has 26177d82's PLAN.md. Report step 1 (E2_CODE_UNIT:45) has the author merge R1-B2-GO into main, which changes PLAN.md. `replay_environment_basis` needs that row on main.
> - I reproduced it on the simulated main: the basis passes, then classification STOPs with "published origin/main differs from evidence authority: docs/r1/PLAN.md".
> - The report's claim (E2_CODE_UNIT:18) that the checkout "need not contain files published after it" is false for PLAN.md. PLAN.md changes on main several times a day.
> - Fix (procedural, no STOP change):
>   1. The author first merges R1-B2-GO and the e1 report into main.
>   2. Rebase e2 onto that main and review that exact commit.
>   3. Fast-forward main to it.
>   4. Freeze PLAN.md pushes until the audit starts, as c3_sweep1_20261027.md did for launch.
> - Correct the report and Part 3 to say this.
>
> **3. MAJOR: the pinned REPORT.md conflicts with the fixes the e1 review requires, and consumption checks main's latest bytes.**
> - E1_AMEND_RUN_REVIEW Minors 1–3 require REPORT.md and logs to be corrected "before the PASS is used in the paper".
> - `replay_environment_basis` requires the bytes at the latest origin/main to equal the 52992b22 pins, both at run time and inside `verify_evidence_completion` (audit.py:1033).
> - So if those fixes land on main before the audit, B.2 cannot start. If they land after, the B.2 evidence can never be consumed again.
> - Fix:
>   - require `git merge-base --is-ancestor 52992b22 <published>` and read the pinned files with `git show 52992b22:<rel>`;
>   - keep the PLAN row and review checks on origin/main;
>   - tell the author that corrections go in a separate erratum file.
>
> **4. MINOR (weakening versus main): the audit process's own package list is no longer tied to the reference.**
> - main required `installed == recorded['packages']`. The new code checks only `sys.version` (audit.py:545).
> - `package_list_sha256` (audit.py:587), the reference every worker_runtime record is checked against, is no longer tied to the e1 list c09242ac. Only the wrapper probe is, through the shared prefix.
> - Fix: normalize `installed` the way PROBE does (`re.sub('[-_.]+','-')`), compute `canonical_packages(...)`, and require it to equal `basis['interpreter']['package_list_sha256']`. Add a test.
>
> **5. MINOR: the disclosure is not "the replay's disclosure".**
> - Part 1 (i)(a) says the replay's disclosure is carried into every B.2 record. `ENVIRONMENT_BASIS_DISCLOSURE` (audit.py:99) paraphrases it.
> - It leaves out REPORT §9 item 2 (the batch .venv wrappers point to the shared venv) and item 3 (a bounded check of 16 evaluations, "not proof that every original dependency or all 288 roots were identical", nothing about LLM seed replay).
> - It names the amended identity basis that R1-E1-OPENML-AMEND requires to be disclosed, but does not explain it.
> - Fix: carry §9 items 1–3 in substance, and cite REPORT.md by path and sha256 in the disclosure.
>
> **6. MINOR: `r1.scripts.c3_env_replay` is imported too late for the provenance check.**
> - It is imported lazily (audit.py:510), after `evidence_paper_provenance` has checked the bytes of the loaded r1 modules (audit.py:613-626). So its bytes are not checked.
> - Fix: add it to the preload import at line 613.
>
> **7. MINOR: two gaps in checking.**
> - Consumption compares only `package_list_sha256` from `environment_checks_at_start` (audit.py:1034-1037). It should compare all five observed fields against the basis.
> - No host check, although R1-B2-GO fixes deepthought and the e1 driver checked HOST. Fix: add `platform.node().split('.')[0] == 'deepthought'`.
>
> **8. MINOR (tests): important cases are missing.**
> - `_published_bytes` is tested only on a non-git directory. There is no real-git test of a stale origin, or of published bytes being used rather than local ones.
> - No test checks `E1_REPLAY_PINNED` against 52992b22.
> - Every guard fixture stubs `_verify_published` and the harness git calls, which is why findings 1 and 2 were not caught.
> - Add: a real-git stale/published test, a pinned-bytes test (skip if the object is absent), an integration test of `evidence_classification` with the checkout at the code commit, and a harness test with untracked caches.
>
> **9. MINOR (Part 3, AUTH_DRAFT_b2_20261104.md):**
> - Line 53: the paper-code placeholder must say the full 40-character sha. The guard at audit.py:880 does a substring check on the full commit, so an abbreviated sha fails.
> - Line 54: "clean" contradicts the e1 record (see finding 1).
> - Lines 74-81:
>   - add `PYTHONDONTWRITEBYTECODE=1` / `python -B`, so the historical shared venv is left unchanged as in e1 A13;
>   - do not source the batch env.sh `PYTHONPATH=<batch>/agent_paper_B`, which the provenance sys.path allowlist would STOP on;
>   - add the merge order and PLAN freeze from finding 2;
>   - the date in the addendum file name is fixed by the agent (20261117).
> - Nothing in Part 3 presents an author decision as already made.
>
> **10. MINOR (report accuracy):**
> - E2_CODE_UNIT:18 and :45-48 should be corrected per findings 1–3.
> - The test counts are accurate.
>
> ## Notes
>
> - An accepting e2 review must contain the exact lines `Code-Commit: <40-character sha>` and `Verdict: ACCEPTED` (mixed case, as written), or `evidence_paper_provenance` refuses it. A last line of only `VERDICT: ACCEPTED` does not satisfy the guard.
> - Observation outside R1-B2-GO's scope: B.2 runs OpenML nodes with no worker network denial.
>
> VERDICT: NOT ACCEPTED

---

## Round 2 (commit `fcd8f951`)

> # Independent review, round 2 — e2 code unit (R1-B2-GO)
>
> Branch `mac-e2-code-20261117` at `fcd8f951e60b9c739030dbd0344a43e6862bfd04`. This round covers the changes since round 1 (`7ea90eeb`): merges `88e26d31` and `f0870dd3`, and the fix commit `fcd8f951`.
>
> I did not edit, commit or push anything in any repository. Scratch went only under /tmp/rv_e2 and was cleaned afterwards. I did not run the whole r1/tests suite; the coordinator runs it and compares.
>
> ## Merges (no changes outside the unit)
>
> - `45fb94cc` and `52992b22` are both ancestors of `fcd8f951`, and `26177d82` is too, so main can be fast-forwarded.
> - Every path that differs between `26177d82` and `fcd8f951`, apart from the five unit files (audit.py, the evidence tests, the E2 report and AUTH_DRAFT), has exactly the blob of `45fb94cc` or of `52992b22`.
> - Every file those two commits changed relative to `26177d82` is present in `fcd8f951` with the same blob, so nothing was dropped.
> - docs/r1/PLAN.md equals `45fb94cc`'s.
> - So the merges bring only upstream content, and nothing outside the unit changed.
>
> ## Round-1 findings, checked against the code
>
> **1. Batch harness versus the clean check: fixed.**
> - `evidence_environment` (audit.py:637-639) now requires the tracked files to be clean (`status --untracked-files=no`). It then calls `harness_untracked_state` (audit.py:584). That function lists untracked, non-ignored files with `ls-files --others --exclude-standard -z`.
> - It allows only files under `nodes/<six OpenML>/data_cache/` plus `paper/tables/artifact_completeness_report.txt`. Anything else is a STOP. Each of the six cache trees must have the `c3_env_replay.tree_digest` recorded in summary.json `post_run.source_caches` at 52992b22.
> - I checked that the e1 mechanism's `verify_source_caches` used the same algorithm (e1_openml_offline.tree_digest @ bbcfc4a9 is byte-identical and includes .gitignore/.gitkeep). Those post-run digests also equal the replay_plan `harness.data_caches_sha256`.
> - Ignored cache contents (climate, sonar) are not listed but are still covered by the tree digest. A missing cache produces the empty digest and STOPs.
> - **Order.** The check runs in `evidence_environment` before `import_harness()` (audit.py:644). The order in evidence_run is provenance, then addendum, then environment, then plan, then `run_config`. So nothing reads or copies the caches before the check.
> - **No bypass through a `.py` in a cache.** Any file under a cache changes the tree digest, so such a file would have to have been there, with identical bytes, at e1. The pinned node code does not import from data_cache.
> - **Gitignored files elsewhere** are treated as before: the old `--untracked-files=all` check did not see them either. The ignored-executable check on src/ is unchanged. Copying ignored node files is old behaviour that e1 shared.
> - This narrows a STOP to the state the e1 run accepted. The report flags it for the author. Part 3 (Harness row and STOPs) states it, so the author's signed addendum, which the code requires, records the decision. See the condition below.
>
> **2. PLAN.md versus the checkout at the code commit: resolved by the merges plus the stated procedure.**
> - I simulated it with a scratch bare origin, main fast-forwarded to `fcd8f951` and a checkout at `fcd8f951`. `replay_environment_basis` passes on the real published bytes, and `dataset.evidence_classification` passes.
> - I then added a commit on main with the addendum and a REPORT.md erratum, not touching PLAN.md, and kept the checkout at `fcd8f951`. Both still pass.
> - The report (step 1) and Part 3 (Paper code row) state the fast-forward and the PLAN.md freeze until the audit starts.
>
> **3. The pinned e1 report files: fixed.**
> - `_pinned_e1_bytes` (audit.py:492) reads each pinned file with `git show 52992b22…:<rel>`, after `merge-base --is-ancestor` against the published main. Both steps fail closed.
> - The PLAN row is still read from published main.
> - The erratum simulation above passes, and Part 3 carries the erratum guidance.
>
> **4. Audit-process package list: fixed.**
> - The process's own distributions are now normalised exactly as PROBE does (`re.sub('[-_.]+','-')`, lower-case).
> - `canonical_packages(...)` must equal the basis `c09242ac…`.
>
> **5. Disclosure: fixed.**
> - `ENVIRONMENT_BASIS_DISCLOSURE` (audit.py:109) cites the REPORT.md path, sha256 and commit.
> - It carries §9 items 1–3 in substance (amended identity basis, wrapper topology, bounded scope including the 288 roots and LLM seed replay), plus the harness's untracked state.
>
> **6. Late import of c3_env_replay: fixed.**
> - `r1.scripts.c3_env_replay` is imported before the provenance scan of r1 module bytes.
>
> **7. Consumption checks and host: fixed.**
> - Consumption compares all five fields observed at audit start and the harness cache digests with the basis.
> - A host check `platform.node()` short name == `deepthought` is in place on the run path only, so consumption does not depend on the host.
>
> **8. Tests: largely fixed.**
> - The basis tests now use a real git checkout with a bare origin. They cover: an erratum on main, changed bytes at the e1 commit, the e1 commit not on main, a stale fetch, published versus working-tree bytes, the real pins against 52992b22 (it ran here, not skipped), the e1 harness state being accepted, and a stray file or changed cache STOPping.
> - Evidence modules: **72 passed** (np244, TMPDIR under /tmp/rv_e2). The basis module has 26 tests, as the report says.
> - The skipped end-to-end classification test is acceptable given my simulation above.
>
> **9 and 10. Part 3 and report text: fixed.**
> - Full 40-character sha, "tracked-clean" wording with the untracked list, `PYTHONDONTWRITEBYTECODE=1 python -B`, no env.sh PYTHONPATH, merge order, PLAN freeze, the new STOPs.
> - The flags still match the CLI.
> - The report's claims match the code.
>
> ## Remaining findings (none BLOCKING or MAJOR)
>
> **1. MINOR: a symlinked directory inside a cache is accepted without being hashed.**
> - `tree_digest` does not descend into symlinked directories (Python 3.13 `rglob`), and the listed symlink falls under an allowed path.
> - I reproduced it in scratch: a symlink to an outside directory containing a `.py` under `nodes/openml_wdbc/data_cache/` passes `harness_untracked_state`. A symlinked file is caught, because its content enters the digest.
> - `_copy_audit_node`'s `copytree` follows symlinks, so the outside content would be copied into each audit node.
> - Impact is low. A symlink cannot stand in for an existing cache directory or file without changing the digest, so the pinned OpenML loader still reads the audited bytes.
> - The e1 mechanism's `_walk_cache` refused any symlink, so this check is slightly weaker than the e1-accepted state.
> - Fix: refuse any listed untracked path whose `lstat` is a symlink, and walk each cache with `os.walk(followlinks=False)` refusing symlinks, as `_walk_cache` does.
>
> **2. MINOR: the cache digests are checked only at the start.**
> - e1 re-verified its source caches after the run.
> - Fix: call `harness_untracked_state(harness, basis)` again after the pool drains, before `evidence_completion.json` is written.
>
> **3. MINOR (tests): the new consumption comparison is not tested on its own.**
> - The consumption tests change fields inside the published basis, so the existing `environment_basis != basis` check fires first.
> - Add a case with an unchanged basis and a changed recorded `environment_checks_at_start` field or `harness_untracked.data_caches_sha256`.
>
> **Observation.**
> - The new package-list equality assumes the audit process sees the same distributions as e1's probe did (same venv, same cwd type, no extra PYTHONPATH dist-info). If it does not, the run fails closed with a STOP.
>
> ## Conditions outside the code
>
> - The coordinator's whole-suite comparison must show no new failures against the base.
> - The author's signed B.2 addendum must carry Part 3's Harness row and STOP list. That is the author's acceptance of the narrowed untracked-file STOP (finding 1).
> - The merge order and PLAN.md freeze must be followed as written.
>
> Code-Commit: fcd8f951e60b9c739030dbd0344a43e6862bfd04
> Verdict: ACCEPTED
>
> VERDICT: ACCEPTED

---

## Round 3 (commit `435513d2`)

> # Independent review, round 3 — e2 code unit (R1-B2-GO)
>
> Branch `mac-e2-code-20261117` at `435513d2486cca21c514a3fa74bbcd5c1210c160`. This round covers the diff `fcd8f951..435513d2`, which touches five files: audit.py +22 lines, three test modules, and one line of the report.
>
> I did not edit, commit or push anything. Scratch went only under /tmp/rv_e2 and was cleaned. I did not run the whole suite; the coordinator is appending that comparison to the record.
>
> ## The three round-2 minors
>
> **1. Symlinks in the harness: fixed.**
> - `harness_untracked_state` (audit.py, after the stray-path check) refuses any symlink in three places:
>   - among the listed untracked paths and `E1_UNTRACKED_FILES`;
>   - at the root of any of the six `data_cache` trees;
>   - anywhere inside them (`os.walk(followlinks=False)`, checking both dirs and files).
> - This closes the case I reproduced in round 2: a symlinked directory that was neither listed nor hashed.
> - The checks run before the digest comparison. That comparison still runs before `import_harness`, and before any node or cache copy.
> - New test: a symlinked directory inside a cache STOPs, and a symlinked report file STOPs.
>
> **2. Cache digests checked again after the run: fixed.**
> - After the worker pool drains and the final resource sample, `evidence_run` calls `harness_untracked_state(harness_root, environment_basis)` again. It compares the result with the digests recorded at the start.
> - Any exception or difference writes STOP.json and raises before `validate_worker_records`, `evidence_blocks` and the completion record. So no label or evaluation block is written.
> - The surrounding `evidence_scratch` handler writes STOP.json only if it is absent, so the specific reason is kept.
> - The parametrized test goes through the real `evidence_run` path. It asserts the STOP reason and that no `label_block.jsonl` exists, and in the pass case it asserts that the check ran on `harness_root`.
>
> **3. The new consumption comparison tested on its own: fixed.**
> - With the basis unchanged, the test alters only `environment_checks_at_start.wrapper_target`, then only `harness_untracked.data_caches_sha256`.
> - In each case it re-hashes environment.json in the completion record, so the earlier digest check passes, and the refusal comes from the e1-replayed-basis comparison.
> - It then restores the record before the existing rewrite checks.
>
> ## Regressions
>
> - The audit.py change is purely additive: two blocks. No existing check was removed or loosened.
> - Harness pin, K = 10, the seed split, population handling, resources and every earlier STOP are unchanged. So are the round-1 and round-2 fixes (merges, pinned e1 commit, package list, host, provenance preload, disclosure).
> - The report's added sentence matches the code.
> - Evidence modules: **74 passed** (np244, TMPDIR under /tmp/rv_e2, `AR_HARNESS_ROOT` = harness pin).
> - The worktree is clean.
>
> ## Findings
>
> None BLOCKING, MAJOR or MINOR.
>
> Observation: the `os.walk` has no `onerror`, so an unreadable subdirectory would be skipped silently. The files under it would then be missing from `tree_digest`, so the digest comparison still STOPs. No change needed.
>
> ## Conditions outside the code (unchanged from round 2)
>
> - The coordinator's whole-suite comparison must show no new failures against the base.
> - The author's signed B.2 addendum must carry Part 3's Harness row and STOP list. That is the author's acceptance of the narrowed untracked-file STOP.
> - Main must be fast-forwarded to the accepted commit, and PLAN.md frozen on main until the audit has started.
>
> Code-Commit: 435513d2486cca21c514a3fa74bbcd5c1210c160
> Verdict: ACCEPTED
>
> VERDICT: ACCEPTED

---

## Whole-suite comparison (run by the unit's author, as the reviewer asked)

`r1/tests` in the Python 3.12 / torch 2.6 environment (`/tmp/tgport312`), `AR_HARNESS_ROOT` = a harness checkout at `a3fedbb`,
separate `TMPDIR`:
- base `26177d82`: 54 failed, 2,404 passed, 195 skipped;
- `435513d2`: 54 failed, 2,436 passed, 195 skipped.

The two failure sets are identical (no new failure); the extra passes are the unit's new tests. The 54 failures are
environment failures of this machine (no network to Hugging Face, transformers 4.49 without the Qwen3.5 classes, exam
and lease fixtures).

## Conditions outside the code (from rounds 2 and 3)

- The author fast-forwards `main` to the accepted commit; `docs/r1/PLAN.md` is not changed on `main` until the audit
  has started.
- The author's signed B.2 addendum carries Part 3's Harness row and STOP list; signing it accepts the narrowed
  untracked-file STOP (the e1-recorded OpenML caches and report file, bound by the e1 post-run tree digests).

---

Code-Commit: 435513d2486cca21c514a3fa74bbcd5c1210c160
Verdict: ACCEPTED

Accepted commit: `435513d2486cca21c514a3fa74bbcd5c1210c160` (round 3).
