# Independent review: sweep-2 integration of S2-C5 (merge `dd1e22be`)

Code-Commit: dd1e22be dd1e22be81fd52091b7d94d166804625d662838c

Reviewer: fresh, independent, read-only code reviewer (AI-assisted, Claude). I did not see how the merge was made. No branch was modified and nothing was pushed. I worked in a detached worktree at `dd1e22be` (`scratchpad/review_intc5`), which stayed clean through the tests. Afterwards I removed it with `git worktree remove` because the scratch volume ran out of space (see §4).

## Scope

- `dd1e22be` (`origin/int-sweep2-c5-20261119`) = merge of `origin/s2c5-switch-20261116` @ `ee2c2b5d` (2nd parent) into `origin/int-sweep2-20261118` @ `efc55ed8` (1st parent). The merge base of the two parents is `84a0dc30`.
- Target: `main` = `origin/main` = `dc3b428495f579b4d79779fb52eb3058554783ac` after `git fetch origin`. The merge base of `main` and `dd1e22be` is `50176481`.
- Binding rows were read on `origin/main:docs/r1/PLAN.md` §10: R1-SWEEP2-INTEGRATE (l.1316), R1-SWEEP2-AUTH (l.1299), R1-SWEEP2-MEASURED-GPU (l.1302), R1-SWEEP2-MEMORY (l.1303), R1-SWEEP2-LAYOUT-H200 (l.1284), R1-SWEEP2-IMAGE (l.1287) and R1-SWEEP2-SETTINGS (l.1207). For context I also read R1-SWEEP2-RESOURCES, R1-S2C3B-LAUNCH, R1-S2C3-ACCEPT and R1-S2C3-DRIVER.
- **`origin/author-decisions-20261119c` does not exist** after the fetch. Only `…20261119` and `…20261119b` exist, and neither contains a row R1-SWEEP2-INTEGRATE-AMEND. So I applied the fallback from the brief: the coordinating chat does the merge instead of the cluster agent, and the scheduler dry runs stay with the cluster agent.

## 1. Conflict resolution

`git diff 84a0dc30 ee2c2b5d` (everything the S2-C5 branch changed since the merge base) touches 5 files. `git diff efc55ed8 dd1e22be` shows that the merge adds only two files on top of the integration:

- `docs/r1/reviews/S2_C5_REVIEW_20261116.md`: new, taken as-is from the S2-C5 branch.
- `docs/r1/reports/sweep2_20261116/S2_C5_UNIT.md`: the S2-C5 text plus one added sentence about `layout_wall_hours`.

The three conflicted files are byte-identical to the integration side.

| S2-C5 branch change (since 84a0dc30) | in dd1e22be | evidence |
|---|---|---|
| walltime 12203 → 8735 | Kept, but derived: `math.ceil(1.5 * lib.MEASURED_GPU_CHUNK_SECONDS["NVIDIA H200"])` = ceil(1.5 × 5823) = ceil(8734.5) = **8735** (I ran the calculation) | `sweep2/s2_c5_switch.py:33`, `sweep2/s2_c2_lib.py:38` |
| disk 42460977 → 42460970 | Kept via `lib.EVIDENCE_DISK_KB` = 42460970 | `s2_c5_switch.py:33`, `s2_c2_lib.py:40` |
| memory 32000 | Kept via `lib.EVIDENCE_MEMORY_MB` = 32000 | `s2_c5_switch.py:34`, `s2_c2_lib.py:39` |
| chunks 16 | Kept as an exact integer match | `s2_c5_switch.py:34,95-101` |
| gpu_hours 41.72 → 25.88 (±0.05) | **Replaced** by the projection cap `0 < layout_gpu_hours ≤ 60`, plus a new cap `0 < layout_wall_hours ≤ 48` | `s2_c5_switch.py:102-108` |
| required JDL lines (42460970 / 8735 / frozen image) | Kept as `REQUIRED_JDL_LINES`. They are now matched as exact whole lines instead of substrings, and `periodic_hold = (NumJobStarts > 1)` is added | `s2_c5_switch.py:38-44,161-164` |
| frozen v1 image digest | Kept: `FROZEN_IMAGE = lib.FROZEN_IMAGE`, the same `sha256:69b06b35…05296` | `s2_c5_switch.py:32`, `s2_c2_lib.py:77` |
| `reviewed_jdl_sha256` check | Kept unchanged | `s2_c5_switch.py:154-156` |
| note parser hardening (duplicate field, NaN) | Kept and tightened: STOP on duplicate fields (:72-73), `math.isfinite` (:107), prefix must be `PASS — `/`PASS - ` (:81), P4 must cite R1-S2C3-ACCEPT (:83), exact `approved: true` (:85), exact `b2_audits` string (:91) | `s2_c5_switch.py:67-109` |
| template values 8735/42460970/32000/16 | Kept. The gpu/wall projections are reviewed placeholders | `sweep2/s2_c5_authorization.template.md:9-14` |
| test fixtures 8735/42460970/25.88 | Kept. The fixture adds `layout_wall_hours`, the H200 `requirements` line and `periodic_hold` | `r1/tests/htcondor/test_s2_c5_switch.py:13-24,37` |
| unit doc: H200 layout, `S2C5_SUBMISSIONS.jsonl` | Kept | `S2_C5_UNIT.md:12-13,19` |

**Conclusion.** The integration side is a strict superset of the S2-C5 branch's checks, with one deliberate replacement: the exact 25.88 GPU-h value became a ≤ 60 GPU-h cap plus a ≤ 48 h wall cap. That replacement is what R1-SWEEP2-AUTH and R1-SWEEP2-MEASURED-GPU prescribe. **No S2-C5 behaviour or check was lost.**

The integration side also adds two checks:

- `check()` requires the H200 `requirements` line (`s2_c5_switch.py:157-160`). `render_jdl.requirements` pins `GPUs_DeviceName =?= "NVIDIA H200"` whenever the spec carries an authorization (`sweep2/render_jdl.py:39-53`).
- `_verify_launch` must pass before `condor_submit` runs (`s2_c5_switch.py:177-239`).

## 2. Consistency with the binding rows

- **H200-only measured placement (MEASURED-GPU, LAYOUT-H200): PASS.**
  - The JDL `requirements` line must equal the H200-pinned render (:157-160).
  - `lib.validate_spec`, run inside `_verify_launch` (:227-228), rejects EVIDENCE unless `gpu_measured` is set, `layout_measured_chunk_s == 5823` and `walltime_s == ceil(1.5 × 5823)` (`s2_c2_lib.py:291-294`).
  - The walltime is fixed at 8735, so the switch fails closed for L40S or any unmeasured model.
- **Walltime / disk / memory (LAYOUT-H200, MEMORY, RESOURCES): PASS.** 8735 s / 42,460,970 kB / 32,000 MB are enforced in four places: the note (:95-101), the spec (:139-148), the required JDL lines (:38-44) and `validate_spec` (`s2_c2_lib.py:295-296`). 8735 s is within AUTH's 17,469 s walltime cap.
- **v1 image (IMAGE): PASS.** Checked in the note (:89-90), the JDL line (:42), the C3b record (:216) and `validate_spec` (`s2_c2_lib.py:299-300`).
- **Projection caps (AUTH, SETTINGS (5), MEASURED-GPU): PASS.** `layout_gpu_hours` must be in (0, 60] and `layout_wall_hours` in (0, 48], both finite (:102-108). `test_s2_c5_switch.py:89-94` covers NaN and a 49 h wall value.
- **Two-key switch, disabled by default: PASS.**
  - `submit` runs `check()`, then requires both `--enable` and `S2C5_ENABLE_REAL == "1"` before doing anything else (:245-247).
  - The repository sets neither key, the template has `approved: false` (template :5), and the merged tree has no `docs/r1/authorizations/c3_sweep2_*` note.
  - A one-shot marker `S2C5_SUBMIT_STARTED.json`, created with `open("x")`, blocks a second submission attempt (:251-258).
- **periodic_hold on NumJobStarts > 1: PASS.** It is a required exact JDL line (:43). `render_jdl.render` emits it together with its reason and subcode (`render_jdl.py:83-85`), and `_verify_launch` requires the JDL to equal the canonical render byte-for-byte (:235-239).
- **SETTINGS (32k server settings):** bound through `server_settings_sha256(spec)` against the sealed C3b record (:217). This merge does not change it.
- **AUTH launch-commit rule / S2C3B-LAUNCH:** this merge does not change it. `_verify_launch` (:177-239) checks:
  - local `origin/main` matches `ls-remote`;
  - the checkout is tracked-clean at the spec commit;
  - the spec commit descends from main;
  - the authority paths are byte-identical to main;
  - the required rows are published;
  - a hash-sealed C3b 8/8 record exists at the exact pins;
  - the staged bytes equal the checkout.

## Findings

### Blockers
None.

### Majors
None.

### Minors
- **m1. The S2-C5 unit doc understates the integrated gate.** Documentation only; behaviour is correct.
  - `docs/r1/reports/sweep2_20261116/S2_C5_UNIT.md:10` still says "author-committed note", and :23-25 say "the author does". Under R1-SWEEP2-AUTH the cluster agent fills the note and the coordinating chat publishes it to `main`, as template :3 already says.
  - The gate list (:8-16) omits the launch verification that the integrated `submit` requires:
    - published-main freshness;
    - a launch commit that descends from main and has identical authority files;
    - the hash-sealed C3b 8/8 record at the exact pins (`--liveness-record`);
    - staged-byte identity and the canonical render;
    - the one-shot marker;
    - the H200 `requirements` line.
  - At :13, "25.88 GPU-h" still reads like an accepted layout value. The code only applies the ≤ 60 cap (the parenthetical added in the merge explains this).
  - The Tests paragraph (:29-31) describes the pre-integration test set.
- **m2. The projections are capped but not cross-checked** against the layout (16 × 5823 s / 3600 = 25.88 GPU-h; serial wall ≤ 25.88 h). An inflated projection below the cap passes. R1-SWEEP2-AUTH sets only bounds, so this is not a rule violation, but the note reviewer has to verify both numbers by hand.
- **m3. Stale dry-run artifacts with the superseded layout** (12203 s / 42,460,977 kB) remain in the tree:
  - `sweep2/dryrun/s2_c2_spec.json:101-102`
  - `sweep2/dryrun/s2_c2_eng_example.jdl:11,13`
  - `sweep2/dryrun/s2_c2.dryrun.txt:30,52`
  - `sweep2/dryrun/c3b/s2_c3b_lib.py:162-163` (also its `stage/` copy)
  - `sweep2/dryrun/replay/spec.replay.openml_ionosphere.json:135-136`

  They are historical and never staged: `stage_c2` copies from `sweep2/`, and `_verify_launch` compares the staged bytes with `sweep2/`. The live `sweep2/*.py` and `*.json` contain no 12203 or 42460977 (`sweep2/s2_c3b_lib.py:162` already says 8735/42460970/32000). The tree does contain no scheduler dry run for the integrated commit (see P1).
- **m4. About 15 MB of unique JSON reaches `main`.** It comes from the integration side and was not introduced by `dd1e22be`:
  - `sweep2/s2_c3_inputs/stage_a_table_t7h8.json` (10.1 MB) and `stage_a_amendment_table_t7j10.json` (4.5 MB);
  - copies under `sweep2/dryrun/replay/S2C3_IN_*` with the same blob ids (9d089cca…, 7d53716e…), so git stores each only once;
  - `openml_cache_t7_20261009.tar.gz` (68 KB).

  These are declared, sha-pinned R1-S2C3-DRIVER inputs (PLAN l.1224). Flagged for awareness only.

### Process note (not a code finding)
- **P1. Scheduler dry runs.** R1-SWEEP2-INTEGRATE lists the scheduler dry runs among the integration steps. No AMEND row exists, so under the fallback they stay with the cluster agent. The tree has no `condor_submit -dry-run` record for the integrated commit. The cluster agent should record one before the sweep-2 note's P6 is set to PASS. Whether that has to happen before or after the merge into `main` is for the coordinating chat to decide.

## 3. Tests: `r1/tests/htcondor`

Command, run in the worktree at `dd1e22be`: `AR_HARNESS_ROOT=/tmp/claude-0/-home-claude/381b2f1b-01d8-56ab-a219-11b65d0f8a2d/scratchpad/harness_a3fedbb python3 -B -m pytest -q -p no:cacheprovider r1/tests/htcondor`

Result: **377 passed in 10.88 s** (0 failed, 0 errors, 0 skipped). The worktree stayed clean.

## 4. Full suite: base (main `dc3b4284`) vs cand (main + `dd1e22be`)

**Result: no regression. The FAILED/ERROR sets are identical.**

My first attempt was aborted: the volume holding `/tmp` filled up during the runs, and those partial logs (`pytest_base.txt` / `pytest_cand.txt` at 8192 bytes, full of disk-full `OSError` entries) are void. The coordinating chat traced the cause to about 26 GB of test temp folders in `/tmp`, cleared them, and re-ran both suites one after the other with `AR_HARNESS_ROOT=…/scratchpad/harness_a3fedbb`. I did not run the suites again. I checked their output independently, as follows.

- **Base:** main `dc3b4284`, worktree `scratchpad/wt_t19_base`, log `scratchpad/pytest_base_final.txt`. Summary: `34 failed, 2459 passed, 156 skipped, 53 subtests passed in 273.70s`, `exit 1`.
- **Cand:** worktree `scratchpad/wt_t19_cand`, log `scratchpad/pytest_cand.txt`. Summary: `34 failed, 2745 passed, 156 skipped, 53 subtests passed in 281.15s`, `exit 1`. HEAD is `e270160d`, with HEAD^1 = `dc3b4284` (main) and HEAD^2 = `dd1e22be81fd…`, so this is exactly main + `dd1e22be`.
- **Comparing the test-id sets:** I took every `^(FAILED|ERROR) ` line, cut off the reason text and sorted the ids. Base and cand each have 34 FAILED and 0 ERROR, and `diff` of the two id sets is empty.
  - The 34 failures are all in test files that exist on main: `test_exam_namespace_fixture_program` (16), `test_c3_sweep_dryrun` (6), `test_exam_b1_truncation` (3), `test_collector_observability` (2), `test_trackx_lease_guardian` (2), and 1 each in `test_c3_control_dryrun`, `test_cooperative_lease`, `test_rerun2_batch4c`, `test_trackp_exam_synthetic` and `test_trackp_soft_label_v2`.
  - None of the failures is in `r1/tests/htcondor` or in any test the merge adds.
- **Other counts:** cand has 286 more passing tests (the tests the integration adds), and the skipped count (156) and subtests (53) are the same.
- **Disk-full check:** the only "ENOSPC" text in either log is the test name `test_fixture_event_retries_short_writes_and_fails_on_enospc`. Neither log has a real disk-full error.
- **Worktree state:** after the runs, `git status --porcelain` shows 65 entries in each worktree, all of them deleted tracked `__pycache__/*.pyc` files. The two worktrees show the same thing, so this does not differ between base and cand.

All 34 failures already occur on `main`. The merge introduces no new failure or error.

During the first attempt I freed space only by deleting my own files: my review worktree and three temporary text files.

## 5. Sweep-2 note draft: changes needed to pass the integrated `parse_note`

The file is `docs/r1/authorizations/c3_sweep2_20261119.md` on `origin/sweep2-auth-20261119` @ `61a3a625`. I did not edit it. I ran the integrated `s2_c5_switch.parse_note` on the committed bytes, then applied the fixes one at a time and re-ran it after each. On the unmodified file the first STOP is `authorization note lacks required field 'layout_wall_hours'`.

These are the minimal changes, in the order the parser reaches them. With all five applied, `parse_note` accepts the draft (verified).

1. **Add `layout_wall_hours: <reviewed projection>`** to the key block, after line 24 (`layout_gpu_hours: 25.88`). It must be a finite number in (0, 48]. For H200-only placement the serial upper bound is 25.88 h; the actual value depends on concurrency and is the reviewed projection.
2. **Line 28 (P2):** change `P2: STOP — …` to `P2: PASS — …`. The value must start with `PASS — ` or `PASS - `. Per R1-SWEEP2-INTEGRATE it should cite this integration (`dd1e22be`, or its merge into `main`) and this review. The current text ("published main de3de54f has no sweep2/ path…") has to be replaced, not just given a new prefix.
3. **Line 29 (P3):** change `P3: DRAFT — …` to `P3: PASS — this note`.
4. **Line 32 (P6):** change `P6: STOP — …` to `P6: PASS — …`. It should cite the integrated S2-C5 switch at `dd1e22be` and this review, and say that launch-commit C3b is required. The current text cites `888f7ff4` "not on published main".
5. **Line 15:** change `approved: false` to `approved: true` (exactly lowercase `true`), within R1-SWEEP2-AUTH's bounds.

These lines already pass and can stay as they are:

- `label: EVIDENCE`, `run_id: s2ev-20261119-a`, and the `image` line (frozen v1 digest);
- `layout_request_walltime_s: 8735`, `layout_request_disk_kb: 42460970`, `layout_request_memory_mb: 32000`, `layout_chunks: 16`;
- `layout_gpu_hours: 25.88` (≤ 60);
- `b2_audits: none (this authorization carries no B.2 audits)` (exact string) and `d8_lock: true`;
- P1, P4, P5 and P7, which already start with `PASS — `; P4 cites `R1-S2C3-ACCEPT`.

The extra field `phase: c3_sweep2` is harmless: it is neither required nor duplicated.

Two pitfalls for whoever edits the note:

- The parser reads every `key: value` line in the whole file, not only the key block. Today the prose has no other line starting with `word:`. A later prose line such as `Note: …` or `P2: …` would be parsed, and would STOP if it duplicates a key.
- The prose on line 3 also contains the text `approved: false` (in backticks, mid-line). Edit line 15 itself, not the first occurrence of the string.

Beyond `parse_note`, listed for completeness:

- The note must be committed byte-identically on `origin/main` (`s2_c5_switch.py:54-58,124-125`).
- The spec must pin its basename and sha256 and match the run_id, image and layout.
- The wrapper's `resolve_label` (`s2_c2_lib.py:328-340`) reads only `approved`, `label` and `run_id`, so the same edits satisfy it.
- The prose should agree with the PASS fields. The header (lines 3-10: "Draft, not an authorization", "not launch-ready: P2 and P6 are STOP") and the scope text that says P2/P6 are not on main need updating. The parser does not check this.

## 6. Safety of the merge into `main`

- **No conflicts:** `git merge-tree --write-tree dc3b4284 dd1e22be` is clean (tree `cf92a45e`).
- **Changes vs `main`:** 184 files added and 1 modified, nothing deleted. The modified file is `.gitignore`, which gains three lines that un-ignore the two pinned replay `prompts.jsonl` inputs.
- **Authority files unchanged:** both `git diff dc3b4284 <merged>` and `git diff 50176481 dd1e22be` are empty for `docs/r1/PLAN.md`, `docs/r1/authorizations/`, `results/r1/evidence/C3_sweep_classification_20261028.json` and `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`. The merge adds no `c3_sweep2_*` note.
- **Large files:** see m4 (existing integration content). No other added file is larger than about 120 KB.
- **Switch stays disabled:** the tree has no enable key and no approved note.

Verdict: ACCEPTED WITH MINORS
