# M4 partial unit — answers to review round 1

Review: `/tmp/pb/reviews/REVIEW_M4_round1.md` (changes requested: 5 should-fix, 8 notes). Fixes are in one new commit on `mac-m4-20261109` on top of `e62db52d`; no history rewritten. `c3_label_sweep.py` and M3's files untouched. AI-assisted (Claude). **Round 2: pending.**

| # | finding | status | change |
|---|---|---|---|
| 1 | route (i) passes on a stale, appended log | **fixed** | `start()` records the log size before opening it for appending (`log_offset`, also in the two-GPU record); `offload()` on the two-GPU path reads only from that offset; `offload_check_dual` additionally reads only the last load (`last_load`: from the last `llama_model_loader: loaded meta data` line, else the last `load_tensors: offloading` line). Tests: `test_dual_route_i_reads_only_the_last_load_of_a_reused_log` (the reviewer's two-load log now gives `full=False`, devices `['CUDA0']`) and `test_fake_two_gpu_restart_with_a_reused_log_cannot_pass_on_the_old_load` (fixed port, log pre-filled with a two-card load, new load silent → not full). Mutation: dropping the offset or `last_load` fails exactly the corresponding test. Single-GPU path unchanged (offset only read on the dual path). |
| 2 | device selection not enforced by UUID | **fixed** | dual path only: each uuid must match `^(GPU|MIG)-[0-9A-Za-z-]+$` exactly; indices, whitespace, lower-case prefixes, empty suffixes and `/` are refused (nothing is stripped). Test `test_dual_requires_exact_gpu_or_mig_uuids` (8 cases) and a MIG positive case; mutation-checked. Legacy MIG forms with `/` would need an explicit decision. |
| 3 | conflicting overrides not refused | **fixed** | with `gpu_uuids`: `extra_args` holding `--tensor-split`, `-ts`, `--split-mode`, `-sm`, `--main-gpu`, `-mg`, `--device`, `-dev` (also `--flag=value`), or `env_extra['CUDA_VISIBLE_DEVICES']`, raise `ValueError`. Tests (10 + env case); mutation-checked. Single path not checked (unchanged; asserted). |
| 4 | B1/R4 separation not stated | **fixed (hand-off §6)** | the reviewer's four points: protected path and `fb57c6a4` lineage; never into `mac-b1-r4-20261109` or B1's checkout while B1 runs (not even an uncommitted copy); B1 harness stays `a3fedbb`, not `561f71f`; re-apply onto the B1-line file (`c8f8ae8a`), retarget the identity test, re-review and re-pin later. |
| 5 | Q3 inaccurate | **fixed (hand-off §4 Q3, §5)** | on deepthought route (i) can never pass (no offload line), so nothing passes until per-card footprints exist; `llamacpp_probe.py` is single-GPU; footprints must come from the DTQ tool or a dual-capable probe extension still to be written, or an offload-line build/verbosity setting. |
| 6 | weak "both cards" criterion | **open, deferred** | to be settled with the O5 pass criterion (minimum per-card share / split bounds); listed in hand-off §5. |
| 7 | `format(x,'g')` loses precision | **fixed** | `tensor_split_arg` (`repr` for floats, `str` for ints) used in argv and recorded as `tensor_split_arg`; round-trip test. |
| 8 | docstring calls per-pid rows a census | **fixed** | docstring says it is not the occupancy census of other processes (runner work, not done). The fake's `--query-gpu` still lists one card; to extend with the census tests. |
| 9 | commit-message wording | **corrected in hand-off §8** (commit not amended: no rewrite) | |
| 10 | identity test can silently skip | **fixed** | `pytest.fail` if `a15300ca` is missing; added `test_single_gpu_argv_literal` (no git needed). |
| 11 | harness defaults test does not exercise the summarizer under defaults | **acknowledged, not done** | needs a re-capture at `897d83c` with `APPEND_ONLY_SUMMARY` records; noted in hand-off §8. |
| 12 | R1-RESUME-STAMP not mentioned | **fixed (hand-off §5)** | the candidate does not include it; the row places the fix before C.3, not needed for sweep 2. |
| 13 | candidate worktree dirty | **fixed** | the untracked `paper/tables/artifact_completeness_report.txt` was removed from the scratch worktrees `/tmp/m3run/h-cand` and `/tmp/m3run/h-base` (both now clean). The harness branch itself is unchanged (`561f71f`). |

## Tests after the fixes

`AR_HARNESS_ROOT` = harness `a3fedbb`: `r1/tests/test_llama_server_instance.py r1/tests/test_llamacpp_offload_routes.py r1/tests/test_exam_observer.py r1/tests/test_llama_server_dual_gpu.py r1/tests/test_llamacpp_probe.py` → **97 passed** (base files 48 + probe 4 unchanged; dual-GPU file 45, was 21). No existing test changed.

## Round 2 (10 Nov; fixes by the Mac-local agent)

| # | Finding | Status | Change |
|---|---|---|---|
| 1 | Two-GPU check ignores CPU-fallback warnings printed before the load markers | **fixed** | `offload_check_dual` reads offload and buffer lines from `last_load(...)` but CPU-fallback lines from all text logged since this `start()`; a fallback found only there sets `full = False` and adds the reason. Test `test_dual_cpu_fallback_before_the_load_markers_is_still_a_stop` (route (i) and route (ii)); it fails on the round-1 code. |
| 2 (note) | `last_load` cut at an earlier meta line when the later load printed only an `offloading` line | **fixed** | cut at whichever marker comes last. Test `test_dual_later_load_with_only_an_offloading_line_drops_the_earlier_buffers`; it fails on the round-1 code. |
| 3 (note) | `log_offset` kept only on the object | **open, for the runner work** | an instance rebuilt from its record must restore `log_offset` from it before calling `offload()`; listed in hand-off §7. |
| 4 (note) | CPU-placement flags and `LLAMA_ARG_*` env not refused on the dual path | **fixed** | `-ot/--override-tensor`, `--cpu-moe/-cmoe`, `--n-cpu-moe/-ncmoe` added to the refused flags; `env_extra` keys `LLAMA_ARG_*` refused. Tests added. |

Tests: the same command → **104 passed** (dual-GPU file 52 tests). Single-GPU path unchanged (its byte-identity tests pass).
