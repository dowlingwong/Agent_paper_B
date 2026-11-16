# S2-M2: integration branch for `main` with what sweep 2 needs (16 November 2026)

**AI-assisted (Claude, Mac agent).** This is unit S2-M2 of the sweep-2 work plan
(`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`, §1 P2 and §2). It is not an author decision. **Pushing this branch to
`main` is the author's call.** Authority is read from `author-sweephost-20261116` @ `fd275c53`.

- **Branch.** `int-main-sweep2-20261116`, from `origin/main` @ `60ec768e`.
- **Method.** `--no-ff` merges of the accepted lines, plus one small new commit, as chosen by the author on 16 Nov
  ("--no-ff merges"; S2-C2 wrapper later, with S2-C5; HARNESS_PIN_C3 → `a3fedbb`). No squash, rebase or cherry-pick of
  an accepted line, so every reviewed commit stays an ancestor. This matters for the D8 confirmation row, whose commit
  must be an ancestor of `main`.

## 1. What sweep 2 needs from `main`, and where it was

`main` @ `60ec768e` predates both later lines. The **mac-int line**, based on `main` except main's last three commits,
carries the evidence-path code. The **author line** carries every PLAN row and the exam work. The two lines never
merged with each other or with `main`.

| Need (work plan §2 S2-M2, PLAN) | Source | In this branch via |
|---|---|---|
| R1-SWEEP1-CLASSIFY runner and audit classification fix (labels from the authorization, not the index) | `9bab3d6f` line (`c3_label_sweep.py`, `audit.py`), in mac-int; M3's EVIDENCE audit path | merge 1 (mac-int), merge 2 (M3) |
| B.2 rules R1-SWEEP1-CLASSIFY / R1-B2-DECOUPLE: seed-block isolation, split label blocks, evidence plan | M3 `mac-m3-20261109` @ `ec6e30a9` (accepted, 2 rounds). Its five held `9bab3d6f` diffs were acknowledged by R1-B2-REPAIR-SCOPE-ACK (IT-2 review accepted) | merge 2 |
| IT-1 (a): M3 dry run records `sweep_index.path` | `mac-m3-dryrun-path-20261114` @ `129317d1` (accepted) | merge 2 (it contains M3) |
| R1-BX-D8 sealed readers and analysis lock (`refuse_sealed`, `guard_table`, `analysis_guard`), D8 gate v2 (`gate.py` @ `da264a40`, SHA `02fdbdd2…`) | mac-int line; `mac-m11-d8-v2-20261114` @ `e3c0921e` (accepted) | merges 1 and 3 |
| `offline_eval` guard order (guard before `build.json` is read) | integration trial's accepted fix `d3ce0d52` (code part) | new commit `84471430` (files taken unchanged) |
| PLAN §10 authority, including R1-SWEEP-HOST-HTC, R1-EXAM-X7, R1-MAIN-PROPOSER, R1-B2-REPAIR-SCOPE-ACK, R1-W2-3-STOP. `_verify_published` reads PLAN from published `main` | `author-sweephost-20261116` @ `fd275c53` (its PLAN.md is a superset of every other line's rows, checked by row id) | merge 4 |
| Pick registry entry and the registry document S2-C2's spec cites (`reports/exam_phase2_20261026/gemma4_31b.json`, sha256 `a04a0346…`) | author line | merge 4 |
| `cache_prompt: false` (harness `a3fedbb`) as the paper's sweep harness pin | none: `HARNESS_PIN_C3` was `6adf385` on `main` (sweep 1) and `897d83c8` before it | new commit `bc164b2e` |
| Thinking-off server flags, q8_0 KV, context, an owned server per job | the S2-C2 wrapper (`sweep2-cluster-20261116`) | **not included** (author: later, with S2-C5) |

**Commits.**

| # | Commit | What |
|---|---|---|
| 1 | `103f63f0` | merge `mac-int-20261107` @ `a15300ca` (+260 commits); PLAN conflict → mac-int's side, superseded in merge 4 |
| 2 | `793d8de7` | merge `mac-m3-dryrun-path-20261114` @ `129317d1` (+71); the trial's six conflicts, resolved exactly as in trial step 1 (`d317c7db`) |
| 3 | `84471430` | `d3ce0d52`'s `offline_eval.py` and its regression test (files re-applied: `d3ce0d52` itself is not an ancestor) |
| 4 | `162e10cb` | merge `mac-m11-d8-v2-20261114` @ `e3c0921e` (+42), no conflicts |
| 5 | `f0d02cbf` | merge `author-sweephost-20261116` @ `fd275c53` (+541), 9 conflicts (§2) |
| 6 | `bc164b2e` | `r1/scripts/HARNESS_PIN_C3` → `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` |

In total 921 commits are added to `main`, counting this report's commit: 1,141 files changed, 266 of them under
`r1/`. Nothing on `main` is deleted. The merges also bring a lot of content that is not on the sweep-2 path, such as
the exam line and the `_to_delete/` recovery files (11 base64 files).

**Notes on commits 2 and 4.**
- After commit 2, the `r1/` tree equals the trial's step-1 tree (`d317c7db`) except for IT-1's two files.
- After commit 4, the `r1/` tree differs from the trial's step 3 (`cf155f4a`) only by M4 (not merged), IT-1 and the
  `d3ce0d52` fix.

## 2. Conflicts of merge 5 (author line) and their resolutions — for review as code

- **`docs/r1/PLAN.md`.** The author branch's version is taken whole. `git diff fd275c53 HEAD -- docs/r1/PLAN.md` is
  empty.
- **`r1/c3/audit.py` (4 hunks).** Both lines rewrote `run_config`. The resolution keeps both behaviours:
  - from the author line: the safe node copy `_copy_audit_node`, B1's `preserve_node_outputs` / `stop_on_invalid`, and
    its no-deletion policy (work directories are preserved; `7db94bc9`, `5f8b8f93`);
  - from M3: the `worker_runtime` probe, the journal and `stop_on_failure`, with M3's positional caller unchanged.

  **Behaviour change for M3's path:** its `rmtree` of the work directory on success is dropped, so audit scratch now
  accumulates, as the author line's docstring warns.
  - `--required-scratch-bytes` and the floor in `monitor_evidence_resources` must be sized for the whole audit; this
    matters for S2-C7's job disk request.
  - Neither line has a unit test of the merged `stop_on_failure` / journal branch. The reviewer's probe covers it
    (4/4 pass); it should become a regression test in a later unit.

  Imports are the union.
- **`r1/tests/test_scripted_live_golden.py`.** The author line's retained `tmp_path` fixture, plus `main`'s
  historical-config replay and exact harness-commit assertion (`5cffed38`).
- **`docs/r1/RUNBOOK.md`.** A row-wise three-way merge: X.3 and X.4 from the author line, X.5–X.7 from mac-int. Each
  side had changed only its own rows.
- **`docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md`.** mac-int's 26 Oct paragraph plus the author line's 9 Nov bullets.
- **`docs/r1/STATUS.md`.** The union of both logs.
- **Historical add/add records** (`proposals/AUTH_DRAFT_trackx_b1_20261104.md`,
  `reports/MAC_OVERNIGHT_QUESTIONS_20261105.md`, `…_20261107.md`). The author (exam) line's version; the mac-int
  versions stay in first-parent history.

## 3. Tests

**Setup.**
- Full paper suite `r1/tests` on the tip and on the two parents of the last merges.
- `AR_HARNESS_ROOT` = harness `a3fedbb`; venv `/tmp/trackg_venv` (Python 3.13.18, NumPy 2.5.3, no torch, no network).
- Each run with its own `--basetemp`. The scratch each run created was removed after it.
- The failure ids are in `reports/int_main_sweep2_20261116/*.fail`.

| Checkout | Failed / passed / skipped |
|---|---|
| `main` @ `60ec768e` | 10 / 571 / 46 |
| mac-int line after merge 4 (`162e10cb`) | 24 / 1257 / 81 |
| author line `fd275c53` | 30 / 1377 / 83 |
| **tip `bc164b2e`** (run twice, identical failure sets) | **43 / 2176 / 154** |

- **No new failure.** Every failure at the tip also fails on one of the two parent lines.
- **Fixed by the integration.** Three author-line failures pass at the tip:
  - `test_c3_dataset.py::test_build_replays_without_violations_and_di_candidates`;
  - `test_c3_featurizer_online.py::test_online_features_hash_equal_the_dataset_rows`;
  - `test_scripted_live_golden.py::test_live_campaign_sequences_match_the_pre_change_golden`.
- **Main's failures persist.** All 10 of `main`'s failures are among the tip's.
- **Where the tip's 43 failures fall:**
  - 16: `test_exam_namespace_fixture_program.py`;
  - 9: `test_c3_sweep_table.py`;
  - 6: `test_c3_sweep_dryrun.py`;
  - 3: `test_d28_noise_binding.py`;
  - 2 each: `test_c3_evidence_guards.py` and `test_trackx_lease_guardian.py`;
  - 1 each: Track P soft label v2 (`lightgbm`), Track P exam synthetic, rerun2 batch4c, cooperative lease and control
    dry run.
- **Known causes.** The integration trial's report §5 explains the mac-int ones: D8-guard fixtures predating the
  guard, D28 liveness in the dry run, and single causes. Nothing here investigates or fixes them.
- **One process note.** A first author-line run was cut short when the disk filled, from earlier runs' leftover
  `/tmp/r1_*` test directories. It was discarded and rerun with cleanup.

## 4. What a push of this branch does and does not enable for sweep 2

**Collection.** The collection code is unchanged by this branch. `r1/headroom` (including `e1b_collect`, which S2-C2
calls), `branch`, `liveness`, `baselines`, `theory`, `harness.py` and `dryrun_guard` are byte-identical between
`60ec768e` and the tip. For collection, the push adds authority only:
- the PLAN rows that `_verify_published` reads from published `main`;
- the registry document;
- the pin file.

So S2-C3 and S2-C4 runs at paper `60ec768e` stay representative of the collector.

**B.2 audits and table builds.** These are **not runnable for sweep 2 from this `main`.** The B.2 rules that come with
M3 are sweep-1 code:
- `audit.evidence_run` starts with `_require_task_native_runtime_attestation()`, which always raises;
- `evidence_plan` → `dataset.evidence_classification` accepts only R1-SWEEP1-CLASSIFY, `c3_sweep1_20261027.md`, the
  sweep-1 index and the sweep-1 pins;
- the completion record hashes the sweep-1 authorization;
- `original_sweep_environment` requires the sweep-1 batch.

**More pushes to `main` will follow.** At least two:
1. the S2-C2 job wrapper with the S2-C5 real-submission switch, which sets `paper.evidence_ready`;
2. a sweep-2 audit and table binding (authorization, index, pins) together with the task-native runtime attestation,
   before S2-C7.

The author can push now, so that PLAN authority and the registry doc are published early, or push once later with
these.

**Side effects of a push.**
- **The `HARNESS_PIN_C3` change.** No sweep-2 code reads the pin file; S2-C2 checks its own harness commit. But the
  old deepthought runner (`c3_label_sweep.py`) would now always STOP on a real run: `check_heads` requires the harness
  at the pin (`a3fedbb`), while `DEEPTHOUGHT_AUTHORIZED_PINS` requires `6adf385`. Its dry run now uses `a3fedbb`. This
  is consistent with R1-SWEEP-HOST-HTC, under which sweeps no longer run on deepthought.
- **`_verify_published`.** After the push, every check must run from a checkout at the new `main`. Records pinned to
  paper root `60ec768e` (the W2 v3 rebuild, the S2-C2 example spec) cannot be re-verified from that root. A unit that
  runs these checks from `60ec768e` during the push window would STOP.
- **The sealed root.** `refuse_sealed` refuses only paths with an `r1_sealed` component, and S2-C2's sealed root
  `/ceph/srv/dwong/paperb/sweep2/` has none. For sweep-2 tables the lock is `guard_table` / `build_from_sweep`
  requiring R1-BX-D8-CONFIRM. That is adequate, but the sealed path itself is not refused.
- **Records citing files not on this branch.**
  - R1-B2-REPAIR-SCOPE-ACK cites the IT-2 review (`mac-answers-20261114` @ `e7f89096`, not merged).
  - `84471430` cites the trial review `5d8c0274`.
  - R1-W2-3-STOP cites `w2_runs_total_check.py` (W2 not merged; the featurizer here is still `c3_features/v2`).
  - R1-EXAM-X7 cites `reports/b2_exec_20261115/` (on `ops-b2-exec-20261115`).

  These records stay on their branches.

## 5. Not included, and open items for the author

- **Not merged.** These accepted lines are not on the sweep-2 path:
  - M4 (`mac-m4-20261109`);
  - W2 (`mac-w2-stoprule-20261114`);
  - M10 kit and v2;
  - Track P RL;
  - the HTCondor adapter (`mac-htcondor-20261114`, `htcondor-container-20261115`);
  - DTQ;
  - the D8-ALT/TEST/SKEW reports;
  - the sweep2-cluster wrapper.
- **The S2-C2 wrapper and the S2-C5 switch.** They need a second integration step once S2-C5 is accepted. S2-C2's spec
  will then set `paper.commit` to the `main` commit that carries this branch, and `evidence_ready` to `true`.
- **Gaps found by the S2-M1 review, to close in S2-C2 before EVIDENCE:**
  - the noise source is not bound: there is no `--e1-summary`, so the collector falls back to `E1_20261022`, which has
    no `openml_climate`;
  - the context differs between plan and exam (16,384 against 32,768);
  - the liveness and collection gates are not applied.
- **Unguarded scripts** (trial §5a). `r1/scripts/c3_audit_dryrun.py` and `c3_env_replay.py` read the frozen corpus
  without sealed-path checks.
- **Pushing to `main`.** On the author's instruction only, from a clean checkout of this branch's accepted tip, without
  a force push.
