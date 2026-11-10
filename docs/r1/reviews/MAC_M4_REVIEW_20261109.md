# Independent review of the M4 partial unit (mac-m4-20261109), 9–10 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not write the unit). Status: rounds 1–2 changes requested; round 3 **accepted** at `00e6cb20`. Rounds copied verbatim below.

---

## Round 1

# Independent review — M4 partial (non-shared parts), round 1 — 10 Nov 2026

Reviewer: fresh independent agent (cloud container, read only; scratch under `/tmp/pb/scratch_rev_m4/`). AI-assisted (Claude).

**Unit.** Paper `mac-m4-20261109` in `/tmp/pb/wt/m4` (base `a15300ca` = `origin/mac-int-20261107`): `468282d1` (two-GPU serving) and `e62db52d` (hand-off + harness patch copy). Harness `r1-local-m4-20261109` @ `561f71f0` = `a3fedbb` + one test-only commit (worktree `/tmp/m3run/h-cand`).
**Spec.** `MAC_OVERNIGHT_RUNBOOK_20261109.md` §3 (A2: only parts not touching `c3_label_sweep.py`), `MAC_LOCAL_RUNBOOK_20261104.md` §M4 steps 1 and 2(e), PLAN R1-CACHEPROMPT-FALSE, R1-HARNESS-NEXT-PIN, R1-MAIN-PROPOSER (c)/(g), R1-BX-REVISIONS (f).

## What I checked and reproduced

- **Scope (A2).** Changed files `a15300ca..HEAD`: `r1/scripts/llama_server_instance.py`, `r1/scripts/c3_fake_llama_server.py`, `r1/tests/test_llama_server_dual_gpu.py`, two docs. `c3_label_sweep.py` untouched. No overlap with M3's list (`git -C /tmp/pb/wt/m3 diff --name-only 478d1d32 HEAD`: only `r1/c3/offline_*`, `r1/tests/test_m3_*`, M3 hand-off); M3 code does not import `llama_server_instance` or the fake. M3's `llama_server_instance.py` is the same blob as the M4 base (`466a7348`), so the planned rebase onto M3 is conflict-free for this file.
- **Authors / deletions.** All three commits: author and committer `Dowling Wong <wangdowling@gmail.com>`. No file deleted; no existing test modified.
- **Paper tests.** The given command: **73 passed** (69 + 4 probe tests; the base-commit comparison test ran, it did not skip). The wider set (`test_c3_label_sweep`, `test_c3_launch_provenance`, `test_c3_sweep_resume` + the five modules) at HEAD and at `a15300ca` (exported with `git archive`): the same 3 failures (pre-existing `test_c3_launch_provenance` TypeError at `c3_label_sweep.py:1400`), 103 passed in both. So the fake-server change does not weaken or break other tests. Not run (whole-tree copies): the sweep/control/exam dry-run tests.
- **Single-GPU byte identity.** By inspection of the diff: with `gpu_uuids=tensor_split=None`, `validate_dual` returns `(None, None)`, `dual_args(None)==[]`, the `env()` branch is `elif`, the record update and `offload_check_dual` are behind `if self.gpu_uuids`. argv, env, record and offload path are identical; the new test compares argv and `env()` with the base module loaded from git. Confirmed.
- **Harness fixture provenance.** I re-ran the test's `capture()` against an export of `897d83c` (`git archive`) with the uv venv of `/tmp/m3run/h-base`: the result equals `fixtures/r1_defaults_bodies_897d83c.json` exactly (all five cases). The candidate passes the test (3/3); at `897d83c` the llamacpp assertion fails and the other two pass, as the hand-off says.
- **Harness assertion vs PLAN.** `ollama` bodies byte-identical; `llamacpp` bodies = old bytes with exactly `,"cache_prompt":false` inserted before the final brace. That is the one difference R1-CACHEPROMPT-FALSE requires (default false, `LLAMACPP_CACHE_PROMPT` scrubbed from the env by the test). Correct reading of "byte for byte" given the dated PLAN row. The D26 seed (`2371956663`) is unchanged, so the opt-in `seed_key` default is covered.
- **Patch copy.** sha256 `aaae7bb0…466e` as stated; `git am` onto `a3fedbb` in a scratch clone gives a tree identical to `561f71f0`.
- **Harness failure set.** Full suite on clean exports (`--continue-on-collection-errors`): `897d83c` 452 passed / 10 failed / 1 error (after subtracting the copied-in new test); candidate 481 / 12 / 1. Difference = exactly the two `test_r1_l8.py` `openml_sonar` / `openml_blood_transfusion` subtests (plus the state-dependent `test_checked_in_report_contains_all_plan_campaigns`, which fails in a clean tree on both runs of mine — consistent with the hand-off's first candidate run). I confirmed `6adf385` is not in `origin/r1` and `897d83c` is an ancestor of `a3fedbb` (fast-forward).

## B1 / R4 separation (asked explicitly)

Facts: `exam_b1_v2.json` (R4 branch `mac-b1-r4-20261109` @ `4ddc820e`) pins `paper_commit` `fb57c6a4` and `harness_commit` `a3fedbb`. `r1/exam/runtime.py:150-152` requires `paper_commit` to be an ancestor of HEAD and `git diff --name-only <paper_commit> -- … r1/scripts/llama_server_instance.py …` (a **working-tree** diff) to be empty, and harness `rev-parse HEAD == harness_commit`. R4 HEAD's `llama_server_instance.py` is blob `c8f8ae8a` = `fb57c6a4`'s. `fb57c6a4` is **not** an ancestor of `a15300ca` (nor of M3); mac-int's file (`466a7348`) is an older line that lacks the B1/Stage-A lease-FD, `start_ticks` and B1 record-preservation code.

Consequences:
1. Merging `mac-m4-20261109` into `mac-int-20261107` changes nothing B1 depends on: B1 does not and cannot run from mac-int (the ancestor check already fails there), and no config on mac-int pins a commit whose `llama_server_instance.py` would now differ (`exam_portal.json` is `TODO_VERIFY_ON_HOST`).
2. M4 (or mac-int after the merge) must **not** be merged or cherry-picked into `mac-b1-r4-20261109` or into whatever checkout B1 runs from while any config pinned to the B1 line is live: the guard would STOP (and the merge would conflict in this file anyway). Not even an uncommitted copy of the file may sit in that checkout.
3. B1's harness checkout must stay at exactly `a3fedbb`; `561f71f` is test-only but a different HEAD, so using `/tmp/m3run/h-cand` as B1's `AR_HARNESS_ROOT` would STOP B1. Keep it a separate worktree, as now.
4. When the two lines converge (after B1/B2), the dual-GPU change has to be re-applied onto the B1-line file (`c8f8ae8a`), the byte-identity test retargeted to that commit, re-reviewed, and any later exam config re-pinned.

## Findings

1. **should-fix — route (i) can pass on a stale log.** `r1/scripts/llama_server_instance.py:255,262` (with `:413` opening the log in append mode). `offload_report` takes the *last* `offloaded k/N` line but collects buffer lines from the *whole* log, and `offload_check_dual` counts devices from all of them. When a log file is reused (same port and generation, e.g. a retry after a failed start with a fixed port), an earlier two-card load satisfies "model buffers on two CUDA devices" for a new load that went to one card. Reproduced in scratch: earlier `CUDA0+CUDA1` lines, then `offloaded 29/29` + `CUDA0 4168 MiB` only, gives `full=True, route='log_line', devices=['CUDA0','CUDA1']`. That is a false "two-card" proof, and it breaks the "one serving configuration per source" provenance. **Fix:** evaluate the buffer lines of the last load only (lines after the last `llama_model_loader: loaded meta data` / last offload line, or record the log size at `start()` and parse only from that offset). Add a test with a two-load log.
2. **should-fix — device selection is not enforced to be by UUID.** `:224-227` accepts any non-empty comma-free strings: `gpu_uuids=['0','1']` passes and gives `CUDA_VISIBLE_DEVICES=0,1`. Indices depend on `CUDA_DEVICE_ORDER` (CUDA's default FASTEST_FIRST is not nvidia-smi's PCI order), which is exactly what UUID pinning avoids. Route (i) would then pass on cards nobody named. Leading or trailing whitespace is also passed through (`' GPU-a,GPU-b '`). **Fix:** for the new dual path only, require `^(GPU|MIG)-[0-9A-Za-z-]+$` after an exact-match strip check (refuse rather than strip). This leaves the single path unchanged.
3. **should-fix — conflicting overrides are not refused on the dual path.** `:339,352`. `extra_args` containing `--tensor-split/-ts`, `--split-mode/-sm`, `--main-gpu/-mg` or `--device/-dev` is appended after `dual_args`, so llama.cpp's last-wins parsing serves a different split while the record says `tensor_split=[a,b], split_mode='layer'`. Reproduced: argv ends `… --tensor-split 1,1 --tensor-split 3,1 --split-mode row`. Likewise `env_extra={'CUDA_VISIBLE_DEVICES': …}` overrides the two UUIDs while `record['gpu_uuids']` keeps them. **Fix:** with `gpu_uuids` set, raise `ValueError` if `extra_args` holds any of those flags, or if `env_extra` holds `CUDA_VISIBLE_DEVICES`. Dual path only; add tests.
4. **should-fix (hand-off) — B1 separation and lineage are not stated.** `docs/r1/reports/MAC_M4_PARTIAL_HANDOFF_20261109.md` §§1, 5 do not say that `llama_server_instance.py` is a B1 protected path, that the branch must stay out of the B1/R4 checkout, that B1's harness must stay at `a3fedbb` (not `561f71f`), or that the B1 line carries a different version of this file that the dual change will have to be ported onto. **Fix:** add the four points of "B1 / R4 separation" above.
5. **should-fix (hand-off) — Q3 is inaccurate.** Hand-off :25, :57. §2 says deepthought's v0.7.0 prints no offload line at default verbosity, so on deepthought route (i) can never pass. "Until then only route (i) can pass" therefore means nothing can pass there. Also, `r1/scripts/llamacpp_probe.py:63,159-166` is single-GPU only (one `--gpu`, one floor), so "measured with the probe" is not possible as written. **Fix:** say that O5 on deepthought needs per-card footprints `[f1, f2]` for the exact (GGUF, split, ctx 16,384, q8_0 KV) configuration, measured by the DTQ tool (step 4) or a dual-capable probe extension that is still to be written, or else a verbosity/build setting that prints the offload line. List this under "remains".
6. **note — weak "both cards" criterion.** `:229-231,255`. Any positive split weight is accepted and any buffer > 0 MiB counts, so `tensor_split=[1, 1e-9]`, or a 0.5 MiB `CUDA1` buffer, passes as two-card serving (reproduced). Consider a minimum per-card share, e.g. each card's model buffer ≥ some fraction of the total, or bounds on the split ratio, to be declared with the O5 criterion.
7. **note — `format(x, 'g')` loses precision.** `:239`: `[1234567, 0.123456789]` gives argv `1.23457e+06,0.123457`, while the record keeps the raw values. Harmless for ratios like `1,1` or `0.6,0.4`, but the record and the served value can differ. Use `repr`/`'.17g'`, or record the argv string as `tensor_split_arg`.
8. **note — the docstring overstates the census.** `:247` "(the census of both cards)": only the server pid's rows are recorded. No other-process occupancy check is done on either card. The hand-off correctly lists the runner's two-card census as not done; reword the docstring so nobody mistakes this for the §M4 2(e) occupancy census. The fake's `--query-gpu` (`c3_fake_llama_server.py:313`) still lists one card, which the later census tests will need to extend.
9. **note — wording of the commit message.** `468282d1` says "argv, environment and record keys equal the base commit (a test loads the base module from git and compares)". The git-loaded comparison covers argv and `env()` only; record keys are checked by "no dual keys" on the fake. Both are true by inspection, but the claim is broader than the test. Fix it in the hand-off if the commit message is not amended.
10. **note — the byte-identity test can silently vanish.** `r1/tests/test_llama_server_dual_gpu.py:41` skips when `a15300ca` is not in the clone (a shallow clone or exported tree on a host). Consider failing instead (or hard-coding the expected single-GPU argv as a literal next to the git comparison), and retarget `BASE_COMMIT` when rebasing (finding 4, point 4).
11. **note — harness test coverage.** `tests/stage2/test_r1_defaults_unchanged.py:76` uses `MemoryMode.NONE` with no records, so the candidate's summarizer change (`shown`, `reason/v1`, `hidden/v1`) is not exercised under defaults, although the manager body embeds that memory text. By inspection the default path (`skip_display=None` → `shown = records`) is unchanged. A case with `APPEND_ONLY_SUMMARY` and a few records, one of them a control-plane skip, would make the "defaults unchanged" claim cover it. The fixture would need re-capturing at `897d83c`.
12. **note — open item missing from the hand-off.** R1-MAIN-PROPOSER (c) describes the next pin as `a3fedbb` "and any R1-HARNESS-NEXT-PIN fixes". The R1-RESUME-STAMP fix is due "before C.3", so it is not needed for sweep 2, but the hand-off should say explicitly that the candidate does not include it, and why.
13. **note — the candidate worktree is dirty.** `/tmp/m3run/h-cand` has untracked `paper/tables/artifact_completeness_report.txt` (from the first suite run), which makes `test_checked_in_report_contains_all_plan_campaigns` pass spuriously. Remove it before any further failure-set comparison. I did not touch it.

Everything else in the hand-off checks out: test counts (48 → 69, 21 new; probe 4/4), the failure-set table and its cause (D28 configs from `6adf385`), the patch sha, Q1/Q2, and what remains. Q1 (a) is a reasonable recommendation.

## Required for acceptance

Findings 1–3 (small code changes plus tests, dual path only, with the single-GPU identity test still green) and findings 4–5 (hand-off text). Notes 6–13 are at the implementer's discretion; 6 should be settled together with the O5 pass criterion.

VERDICT: changes requested

---

## Round 2

# Independent review — M4 partial (non-shared parts), round 2 — 10 Nov 2026

Reviewer: the same independent agent as round 1 (cloud container, read only; scratch under `/tmp/pb/scratch_rev_m4/`). AI-assisted (Claude).

**Unit.** Paper `mac-m4-20261109` @ `bf5a9b4d` (one new commit on `e62db52d`; author and committer Dowling Wong <wangdowling@gmail.com>; no history rewritten, no file deleted). Answers: `docs/r1/reviews/MAC_M4_REVIEW_ANSWERS_20261109.md`. Hand-off §4 Q3 and §§5–8 updated. Harness `r1-local-m4-20261109` is unchanged at `561f71f`.

## Re-checks

- **Scope.** `a15300ca..bf5a9b4d` touches only `llama_server_instance.py`, `c3_fake_llama_server.py` (unchanged since round 1), the dual-GPU test and docs. `c3_label_sweep.py` and every file M3 edits are untouched.
- **Tests.** The given command: **97 passed**, as claimed. Only `test_llama_server_dual_gpu.py` changed among the tests. `test_c3_label_sweep` / `test_c3_launch_provenance` / `test_c3_sweep_resume`: the same 3 pre-existing failures as at `a15300ca`, 51 passed. Worktree clean after the runs.
- **Single-GPU identity.** Still byte-identical. `validate_dual` returns before any new check when `gpu_uuids` and `tensor_split` are both None. `log_offset` is set and used only under `if self.gpu_uuids`. The single path's `offload()` is untouched. The identity test now fails instead of skipping, and the literal-argv test passes.
- **R1-S1, stale log.** Fixed for the case I reported. My two-load log now gives `full=False, devices=['CUDA0']`. The fake restart test (fixed port, log pre-filled with a two-card load, new load silent) reads only from `log_offset` and fails as it should. I verified the mutation claim by reasoning: without the offset, `last_load` cuts at the old `loaded meta data` line and the old two-card buffers pass.
- **R1-S2, UUIDs.** Fixed. The exact regex, with nothing stripped, refuses indices, whitespace, lower-case and `/`. MIG positive case tested. The legacy MIG `/` form is flagged as open; that is fine.
- **R1-S3, overrides.** Fixed. Both `--flag value` and `--flag=value` forms of `-ts/-sm/-mg/-dev` are refused, as is `env_extra['CUDA_VISIBLE_DEVICES']`, on the dual path only.
- **R1-S4, R1-S5, hand-off.** §6 states the four B1/R4 separation points accurately: blob ids, `fb57c6a4` not in the lineage, harness to stay at `a3fedbb`, port later. Q3 is now correct: nothing can pass on deepthought until per-card footprints exist, and the probe is single-GPU.
- **Notes.** Note 7: `tensor_split_arg` round-trips and is recorded. Note 8: docstring fixed. Note 9: corrected in hand-off §8. Note 10: done. Note 12: stated in §5. Note 13: `/tmp/m3run/h-cand` and `/tmp/m3run/h-base` are clean (`git status` empty), and `h-cand` is still at `561f71f`. Notes 6 and 11 are deferred and listed in §5/§8. Acceptable.

## Findings

1. **should-fix — the `last_load` fix drops CPU-fallback lines on the dual path (regression introduced in this round).** `r1/scripts/llama_server_instance.py:264-275,286`. `offload_check_dual` now runs `offload_report` on `last_load(log_text)`, which starts at the last `llama_model_loader: loaded meta data` line. llama.cpp prints its fallback messages (`warning: no usable GPU found …`, `ggml_cuda_init: failed …`, `no CUDA-capable device`) during backend init, **before** the model loader. The repository's own fake does the same: `c3_fake_llama_server.py` prints the warning before the meta line in `cpu` mode. So on the dual path these lines are now cut away, and the documented rule "a partial line or CPU fallback is a STOP whatever the memory" no longer holds. Reproduced in scratch (`probe2.py`):
   - fallback line, then a meta line, then `offloaded 29/29` with `CUDA0` + `CUDA1` buffers: dual `full=True`, `cpu_fallback_lines=[]`. The single-GPU `offload_check` on the same text gives `full=False`.
   - route (ii): fallback line, then a meta line, no offload line, pid listed on both cards at footprint: dual `full=True`.

   In practice a real fallback would usually also produce `offloaded 0/N` or no per-card memory, so the chance of a false pass is low. But this is a STOP check, the regression is new, and the round-1 test only catches it because it appends the fallback line at the end. **Fix (small):** take `cpu_fallback_lines` from the whole since-offset text and only the offload and buffer lines from `last_load`. For example, compute `offload_report` on both texts and merge, or pass the full text for the fallback scan. Add a test with the fallback line *before* the meta line; the fake in `C3_FAKE_LLAMA_OFFLOAD=cpu` mode with `--tensor-split` produces exactly that order.
2. **note — the `last_load` cut can still reach back into an earlier load.** `:274`: `cut = meta if meta >= 0 else offl`. If the earlier load printed a meta line and the later one printed only `load_tensors: offloading …`, the cut lands in the earlier load. Reproduced: the old two-card buffers plus the new one-card load give `full=True`. Within one start's log (`log_offset`) a llama-server process loads once, so this is defence-in-depth only. Cutting at whichever marker comes last (`max(meta, offl)`; the offload and buffer lines follow the `offloading` line) would make it right. This can be folded into the fix for finding 1.
3. **note — `log_offset` lives only on the object.** `offload()` reads `self.log_offset`. An instance rebuilt from a saved record (resume/adoption) without `start()` reads from 0. The value is in the record (`log_offset`), so a later runner change can restore it. Worth a line in the runner work (2(b)–(e)).
4. **note — other overrides the offload proof does not catch.** `extra_args` like `--override-tensor/-ot …=CPU`, `--cpu-moe/-cmoe` and `--n-cpu-moe/-ncmoe` keep tensors on the CPU while `offloaded N/N` can still print. `env_extra` `LLAMA_ARG_*` entries (for example main-gpu or device) are not stripped, because `env_extra` is applied after the `LLAMA_ARG_` scrub. A `--device`-type restriction would still be caught by the two-card proof. Consider refusing these on the dual path, or listing them as operator checks for O5.

Notes 6 and 11 from round 1 remain open, as the hand-off records.

## Required for acceptance

Finding 1: one small change plus one test. Finding 2 can ride along. Everything else from round 1 is resolved or explicitly deferred.

VERDICT: changes requested

---

## Round 3

# Independent review — M4 partial (non-shared parts), round 3 — 10 Nov 2026

Reviewer: the same independent agent as rounds 1–2 (cloud container, read only; scratch under `/tmp/pb/scratch_rev_m4/`). AI-assisted (Claude).

**Unit.** Paper `mac-m4-20261109` @ `00e6cb20` (one commit on `bf5a9b4d`; author and committer Dowling Wong <wangdowling@gmail.com>; no history rewritten, no file deleted). Answers: round-2 section of `docs/r1/reviews/MAC_M4_REVIEW_ANSWERS_20261109.md`. Harness `r1-local-m4-20261109` unchanged at `561f71f`.

## Re-checks

- **Scope.** `a15300ca..00e6cb20` still touches only `llama_server_instance.py`, `c3_fake_llama_server.py`, `test_llama_server_dual_gpu.py` and docs. `c3_label_sweep.py` and M3's files are untouched.
- **Tests.** The given command gives **104 passed**, as claimed. `test_c3_label_sweep` / `test_c3_launch_provenance` / `test_c3_sweep_resume` give the same 3 pre-existing failures as at `a15300ca` (51 passed). Worktree clean after the runs. Only the dual-GPU test file changed among the tests.
- **Single-GPU path.** Still byte-identical. Every new line is behind `gpu_uuids` (`validate_dual` returns early; `offload_check_dual` is used only on the dual path). The git-loaded identity test and the literal-argv test pass.
- **Finding 1 (round 2), fallback lines before the load markers.** Fixed. `offload_check_dual` takes `cpu_fallback_lines` from all text since `start()`; a line found only there sets `full=False` and adds the reason. My reproductions now behave correctly (`probe2.py`):
  - `no usable GPU found` before the meta line, then `29/29` with two-card buffers: `full=False`, fallback line recorded;
  - the same with `ggml_cuda_init: failed …`: `full=False`;
  - route (ii) with the fallback before the meta line and both cards at footprint: `full=False`.

  The new test covers route (i) and route (ii) and keeps a positive control (no warning → full).
- **Note 2 (round 2), cut position.** Fixed. With `cut = max(meta, offloading)`, my earlier-meta / later-offloading-only log gives `full=False`. The new test covers it.
- **Note 4 (round 2), extra overrides.** Fixed. `-ot/--override-tensor` (including the `=` form), `--cpu-moe/-cmoe`, `--n-cpu-moe/-ncmoe` and any `LLAMA_ARG_*` key in `env_extra` are refused on the dual path. Re-ran the round-1 override probes (`probe3.py`): indices, whitespace, `CUDA_VISIBLE_DEVICES` in `env_extra`, `--tensor-split`, `--split-mode=row`, `-ot` and `LLAMA_ARG_MAIN_GPU` are all refused. `tensor_split_arg` gives `1234567,0.123456789`.
- **Stale log through the real path.** Through `offload()`, a previous two-card load followed by a one-card load (with llama.cpp's markers) gives `full=False`, both with the recorded `log_offset` and with offset 0 (the `last_load` cut alone is enough).
- **Note 3 (round 2).** Left open for the runner work. Hand-off §7 says an instance rebuilt from its record must restore `log_offset`. Acceptable for this partial unit.

## Remaining notes (non-blocking)

1. **note** — Text with **no** load markers is still read whole (`last_load` returns all of it). My round-1 synthetic log (two loads, only `offloaded` lines, no `loaded meta data` / `offloading` markers) still passes when handed straight to `offload_check_dual`. Through `offload()` this is covered by `log_offset`, and a real llama.cpp build that prints `offloaded N/N` also prints the `offloading` line in the same function. So no fix is needed; the runner should always go through `offload()` (or pass since-offset text).
2. **note** — Small bookkeeping: hand-off line 3 still says "round 2 pending" and the answers file header says "Round 2: pending". The commit message credits the coordinator while the answers table says "fixes by the Mac-local agent". Update the status lines when recording this review.
3. **carried open items**, recorded in the hand-off: round-1 note 6 (minimum per-card share, to be settled with the O5 criterion), note 11 (harness defaults test under `APPEND_ONLY_SUMMARY`), round-2 note 3 (`log_offset` restore in the runner), legacy MIG `/` forms, Q1–Q3, and everything in §5 (2(a)–(d) wiring, census of both cards, configs, DTQ tool, runbook), which waits for M3 acceptance and the rebase.

## Separation reminder (unchanged from round 1, recorded in hand-off §6)

Merging into `mac-int-20261107` does not affect B1. Never merge or copy this change into `mac-b1-r4-20261109` or B1's checkout while configs pinned to the `fb57c6a4` line are live. B1's harness stays at `a3fedbb`, not `561f71f`. Re-apply onto the B1-line file and retarget `BASE_COMMIT` when the lines converge.

VERDICT: accepted
