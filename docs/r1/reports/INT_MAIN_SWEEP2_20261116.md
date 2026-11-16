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
| 3 | `84471430` | `d3ce0d52`'s `offline_eval.py` and its regression test |
| 4 | `162e10cb` | merge `mac-m11-d8-v2-20261114` @ `e3c0921e` (+42), no conflicts |
| 5 | `f0d02cbf` | merge `author-sweephost-20261116` @ `fd275c53` (+541), 9 conflicts (§2) |
| 6 | `bc164b2e` | `r1/scripts/HARNESS_PIN_C3` → `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` |

In total 920 commits are added to `main`: 1,141 files changed, 266 of them under `r1/`.

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
  accumulates, as the author line's docstring warns. Imports are the union.
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

## 4. Not included, and open items for the author

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
