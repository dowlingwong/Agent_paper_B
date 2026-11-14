# M4 partial hand-off (non-shared parts) — 9 November 2026

**Review: accepted in round 3 at `00e6cb20` (`reviews/MAC_M4_REVIEW_20261109.md`; answers `reviews/MAC_M4_REVIEW_ANSWERS_20261109.md`). The runner must always go through `offload()` (log text without load markers is read whole by `offload_check_dual`).** AI-assisted (Claude, overnight worker in the cloud container). Started under author line **A2** (`M4 可以先做不和 M3 共享的部分`), which is the author amendment (B) asked for in `MAC_M4_SCOPE_RECHECK_20261108.md`: only M4 parts that touch neither `r1/scripts/c3_label_sweep.py` nor any file M3 edits. No host, GPU, model, DTQ run, push or harness merge into `r1`. ENGINEERING_ONLY.

## 1. What was done

| M4 step | state | where |
|---|---|---|
| 2(e) two-GPU serving (`llama_server_instance.py` part) | **done**, fake-server tests | paper `mac-m4-20261109` @ `468282d1` |
| 1 harness pin candidate + "defaults unchanged" test | **done locally**; one failure-set difference found (§3) | harness branch `r1-local-m4-20261109` @ `561f71f` in the local clone `/tmp/pb/harness` (not pushed; patch copy in this directory) |
| 2(a) `llama_server_instance.py` part | **already present** at the base: `thinking_policy` (mode `off` with `off_switch` → `--chat-template-kwargs {"enable_thinking":false}`) and `extra_args` (`--jinja`, KV cache flags) exist; the wiring from the registry is in `c3_label_sweep.start_llamacpp` → not done (shared file) | — |
| 2(b)–(d), census of both cards in the runner | not done: `c3_label_sweep.py` | — |
| 3 config templates | not done: their fields are defined by the runner change 2(a)–(c) in `c3_label_sweep.py` | — |
| 4 DTQ tool | **blocked here**: it must reuse the Track S probe at paper `d10b05b7` (`r1/tracks/probes/determinism.py`), which is not in the local clone (`git cat-file` fails) | — |
| 5 tests for (a)–(d), 6 runbook | not done (depend on the above / on X.7) | — |

Paper base: `origin/mac-int-20261107` (`a15300ca`), because none of these parts depends on M3 code; rebase onto M3's accepted commit when M3 is accepted, as §M4 says.

## 2. Two-GPU serving (2(e))

`LlamaServerInstance(..., gpu_uuids=[u1, u2], tensor_split=[a, b])`:
- validation: exactly two distinct uuids (no comma), two positive finite weights, both or neither, and never together with `gpu_uuid`;
- environment `CUDA_VISIBLE_DEVICES=u1,u2`; argv adds `--split-mode layer --tensor-split a,b` right after `-np 1`;
- the record gains `gpu_uuids`, `tensor_split`, `split_mode` **only** for two-GPU serving;
- `offload_check_dual` (used by `offload()` when `gpu_uuids` is set): route (i) an `offloaded N/N` line, no CPU fallback **and** non-zero model buffers on two CUDA devices; route (ii), when the build prints no offload line (deepthought's v0.7.0 at default verbosity), the server pid listed by nvidia-smi on **each** card at its pinned per-card footprint `[f1, f2]`; a partial line or CPU fallback is a STOP; the per-card nvidia-smi rows are recorded either way;
- the fake llama-server accepts the two flags, prints `CUDA0`+`CUDA1` buffers when `--tensor-split` is given, and lists one nvidia-smi row per uuid of a comma-separated `CUDA_VISIBLE_DEVICES`; its single-GPU output is unchanged.

**Single-GPU path unchanged:** `test_single_gpu_argv_and_env_equal_the_base_commit` loads `llama_server_instance.py` from `a15300ca` via `git show` and asserts identical `argv` and `env()` for three single-GPU configurations (default; `gpu_uuid`; `gpu_uuid` + `--jinja` + thinking off); a fake-server test asserts the single-GPU record has no new keys.

Tests (`AR_HARNESS_ROOT` = harness `a3fedbb`): `r1/tests/test_llama_server_instance.py r1/tests/test_llamacpp_offload_routes.py r1/tests/test_exam_observer.py` baseline **48 passed, 0 failed**; after, with the new `test_llama_server_dual_gpu.py`, **69 passed, 0 failed** (48 + 21 new; no existing test changed). `test_llamacpp_probe.py`: 4 passed before and after. (`test_exam_observer.py` copies one node directory into pytest's temp dir and runs an in-process fake campaign; it does not copy the harness tree.) Not run: tests that drive `c3_label_sweep` dry runs.

## 3. Harness pin candidate (step 1)

`origin/r1` (`897d83c`) is an ancestor of `a3fedbb`, so "merge `cacheprompt-20261031` @ `a3fedbb`" is a fast-forward: the candidate **is** `a3fedbb` (the B1 pin), plus one test-only commit `561f71f`:

- `tests/stage2/test_r1_defaults_unchanged.py` + `tests/stage2/fixtures/r1_defaults_bodies_897d83c.json`: request bodies of the manager path (`llamacpp`, `llamacpp` with `manager_proposal/v1`, `ollama`) and the side-query path (`llamacpp`, `ollama`) against a stand-in server with every new setting unset, compared with golden bodies captured at `897d83c` by the same capture code. Result at the candidate: **`ollama` bodies byte-identical; `llamacpp` bodies equal the old bytes with exactly `,"cache_prompt":false` added and nothing else**. Run against `897d83c` itself the `llamacpp` assertion fails as it should (no field there) and the other two pass.
- The M4 text says "the request body equals the old body byte for byte". For `llamacpp` that cannot hold and must not: PLAN **R1-CACHEPROMPT-FALSE** (31 Oct) and R1-EXAM-CACHE-REV require explicit `cache_prompt: false` on every request. The dated rows win; the test encodes the exact allowed difference.

**Full harness suite** (uv-synced env from `uv.lock`: Python 3.11.18, sklearn 1.8.0; outbound network blocked by a dead proxy during the runs):

| | passed | failed | errors | subtests passed |
|---|---|---|---|---|
| `origin/r1` 897d83c | 452 | 10 | 1 | 55 |
| candidate (first run, before the new test) | 478 | 12 | 1 | 53 |
| candidate `561f71f` (second run) | 482 | 11 | 1 | 53 |

Common failures (both): collection error `tests/test_legacy_noop_skip.py` (`src.autoresearch_worker` missing); `test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`; four in `test_artifact_completeness_and_manifest.py`; five in `test_kdd_paper_sections.py`. (`test_checked_in_report_contains_all_plan_campaigns` passed on the second candidate run only because the first run had written `paper/tables/artifact_completeness_report.txt` into the worktree: state-dependent, not a code difference.)

**Failure-set difference:** two new subtest failures, `tests/stage2/test_r1_l8.py::TestOpenmlPool22Oct::test_dataset_json_and_template_files` for `openml_sonar` and `openml_blood_transfusion`: the test requires each pool node's `config.yaml` to equal the template byte for byte, and harness `6adf385` ("Apply predeclared D28 start configurations", part of the candidate since it is not in `origin/r1`) changed those configs (`C: 0.15` → `0.01` etc.). The cause is the predeclared D28 change, not Track S or `cache_prompt`. See question Q1.

The commit is only in the local clone; a copy is `docs/r1/reports/M4_HARNESS_PIN_CANDIDATE_20261109.patch` (sha256 `aaae7bb0f4e34a4b5c77f372bb8663a1b98f82bea11b5e88ddd24aece8ed466e`; `git am` onto `a3fedbb`). Not merged into `r1` (R1-HARNESS-NEXT-PIN).

## 4. Open questions

- **Q1 (harness L8 template test vs D28 configs).** Options: (a) a harness test-only fix on the candidate that exempts the D28-predeclared configs (compare against the recorded D28 values instead of the template); (b) accept the two subtests as known failures of the next pin and list them; (c) revisit D28. **Recommend (a)**, as a separate small reviewed harness commit; the D28 values are predeclared and must not move.
- **Q2 (DTQ tool).** Needs paper `d10b05b7` (Track S probe) in the working clone. Recommend fetching that commit (or the branch that carries it) before starting step 4.
- **Q3 (2(e) offload proof on deepthought).** *Corrected 10 Nov.* Deepthought's llama.cpp build prints no offload line at default verbosity (§2), so route (i) can **never** pass there; until per-card footprints exist, **no** route can pass and O5 cannot be met. O5 on deepthought therefore needs either per-card footprints `[f1, f2]` for the exact configuration (GGUF, split, context 16,384, q8_0 KV), measured by the DTQ tool (step 4) or by a dual-capable extension of the probe that is still to be written (`r1/scripts/llamacpp_probe.py` is single-GPU: one `--gpu`, one floor), or a verbosity/build setting that prints the offload line (checked by the operator against the pinned build). Listed under §5.

## 5. Not done / next

- Per-card footprints for 2(e) route (ii), or an offload-line setting, for deepthought (Q3); a minimum per-card share criterion (review note 6) to be fixed together with the O5 pass criterion.
- The harness candidate does **not** include the R1-RESUME-STAMP fix: that row schedules the fix on `r1-local-*` for a new `r1` pin "after sweep 1 and B.2, before C.3"; sweep 2 does not need it (R1-MAIN-PROPOSER (c) names `a3fedbb` plus any R1-HARNESS-NEXT-PIN fixes). Add it in a separate reviewed commit before C.3.

2(a)–(d) wiring in `c3_label_sweep.py`, census of both cards in the runner, configs (step 3), DTQ tool (step 4), the runner fake-server tests, the sweep-2 runbook (step 6). All wait for M3 acceptance (rebase) or are blocked as above.

## 6. B1 / R4 separation (added 10 Nov, review finding 4)

1. `r1/scripts/llama_server_instance.py` is a **B1 protected path**: `r1/exam/runtime.py` requires B1's pinned `paper_commit` (`fb57c6a4` in `exam_b1_v2.json` on `mac-b1-r4-20261109`) to be an ancestor of HEAD and the working-tree diff of this file against it to be empty. `fb57c6a4` is not an ancestor of `a15300ca` or of this branch; the B1 line carries a newer version of the file (blob `c8f8ae8a`, with lease-FD, `start_ticks` and record-preservation code) than mac-int (`466a7348`), on which this change is built.
2. Merging `mac-m4-20261109` into `mac-int-20261107` does not affect B1 (B1 cannot run from mac-int). This branch, or mac-int after that merge, must **never** be merged or cherry-picked into `mac-b1-r4-20261109` or into the checkout B1 runs from while any config pinned to the B1 line is live, and no uncommitted copy of the file may sit in that checkout: the guard would STOP B1 (and the file would conflict).
3. B1's harness checkout stays at exactly **`a3fedbb`**. The candidate `561f71f` is test-only but a different HEAD; using `/tmp/m3run/h-cand` (or any checkout of `561f71f`) as B1's `AR_HARNESS_ROOT` would STOP B1. Keep it a separate worktree.
4. When the lines converge (after B1/B2), the two-GPU change must be re-applied onto the B1-line file, `BASE_COMMIT` of the byte-identity test retargeted to that commit, re-reviewed, and any later exam config re-pinned.

## 7. Round-1 code fixes (10 Nov)

- Route (i) reads only the current start's part of the appended log (`log_offset` recorded at `start()`, stored in the two-GPU record) and, within it, only the last load (`last_load`).
- Round 2: CPU-fallback lines are read from everything logged since `start()` (they precede the load markers); `last_load` cuts at the last marker of either kind; CPU-placement flags and `LLAMA_ARG_*` env are refused on the dual path. Open for the runner work: an instance rebuilt from its record must restore `log_offset` from it.
- Two-GPU uuids must match `^(GPU|MIG)-[0-9A-Za-z-]+$` exactly (no index, no whitespace, nothing stripped); legacy `MIG-GPU-…/x/y` forms with `/` are refused (would need an explicit decision).
- With `gpu_uuids`, `extra_args` containing `--tensor-split/-ts`, `--split-mode/-sm`, `--main-gpu/-mg`, `--device/-dev` (also `--flag=value`) and `env_extra['CUDA_VISIBLE_DEVICES']` are refused.
- Notes: the split is written with round-trip precision (`tensor_split_arg`, also recorded); the docstring no longer calls the per-pid rows a census; the git-based single-GPU identity test fails (not skips) if `a15300ca` is missing, and a literal single-GPU argv test was added.
- Single-GPU path still byte-identical to `a15300ca` (argv, `env()`); single-GPU inputs are not subject to the new checks.

## 8. Corrections to §2–§3 wording

- The commit message of `468282d1` says the git-loaded test compares "argv, environment and record keys"; it compares argv and `env()`. Record keys are covered by the separate fake-server test (no dual keys on single-GPU records).
- §3: the candidate worktree's untracked `paper/tables/artifact_completeness_report.txt` (written by the first suite run) was removed on 10 Nov; the second-run pass of `test_checked_in_report_contains_all_plan_campaigns` was state-dependent, as stated.
- Harness test coverage (review note 11): the defaults test uses `MemoryMode.NONE` with no records, so the summarizer's display changes under defaults are covered by inspection only (`skip_display=None` → `shown = records`), not by the byte test. Extending it with `APPEND_ONLY_SUMMARY` records needs a re-capture at `897d83c`; not done.
