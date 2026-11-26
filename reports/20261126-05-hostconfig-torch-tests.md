# Report — P.4 host-config fill: torch tests (FAIL, 1 failure)

**Task:** `cluster/20261126-01`.
**Result: FAIL — 1 failed, 179 passed** on the branch tip; the same test fails on the publication result.
The fill is **not** publishable under the task's zero-failures condition until the failure is fixed.

- **Branch tip tested:** `p4-hostconfig-fill-20261126` @ `021c4eec198ee31e5c150cd49de4fd72a46eba08`
- **Branch base:** `f1f1b651` (merge base); `main` at the first run `54082a05`, at re-verification `47df6f55`
- **Test host:** deepthought, clean checkout `/work/dwong/p4-hostconfig-check-20261126/repo` (detached at the tip;
  `git status` clean before and after)
- **Environment:** Python 3.12.2 (Anaconda), `torch 2.5.1+cu121`; harness at
  `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (`r1/scripts/HARNESS_PIN_C3`), clean;
  `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`
- **Command:** `python -m pytest -q -p no:cacheprovider r1/tests/test_trackp_p4_runner.py r1/tests/test_trackp_sft.py`
- **Re-verified:** 27 Nov 2026 ~00:42Z on the same checkout: **179 passed, 1 failed in 62.42 s**, identical id.

## Counts

| Tree | Result |
|---|---|
| Branch tip `021c4eec` | **179 passed, 1 failed** (180 tests) |
| `main` `54082a05` | **192 passed, 0 failed** (192 tests) |
| Publication result (`54082a05` + merge of the fill) | **191 passed, 1 failed** (192 tests) |

The branch is based on older `main`; current `main` has newer `p4_lib.py`/test code. The merge is clean; the same
test fails with the filled config.

**Failure id:** `r1/tests/test_trackp_p4_runner.py::test_trackp_runs_the_clone_script_from_the_job_directory`

## Cause (confirmed by a controlled revert)

The test calls `L.trackp(..., ["sft-select", "--runs", <missing>, ...])` and expects a `ProtocolStop`. With the filled
config the call proceeds into `SFT.select_lr`, which reads `<missing>/stage_s/sft_report.json` and raises
`FileNotFoundError` (rc 1). `p4_lib.trackp` classifies rc 1 as an infrastructure `Stop`, not the expected
`ProtocolStop` (rc 2 with `STOP:`). With the TODO config `trackp.py` refuses earlier with a protocol STOP, so the
test passes.

Controlled check in a temporary merge worktree:
- restore `r1/scripts/configs/trackp_htcondor_v2.json` from `main` (20 `TODO_VERIFY_ON_HOST` values) → the single
  test **passes**;
- re-apply the branch's filled config (1 TODO left) → the single test **fails** again.

So the failure is exposed by filling the config, not by a wrong filled value: a valid config lets `sft-select` reach
a missing runs directory, where a protocol STOP is expected but the code crashes. The fix is code/test work (treat a
missing runs path as `STOP:` with rc 2, or give the test a real runs fixture), not another edit of the fill.

## What I changed

Nothing in the branch or in `main`. The test runs used temporary worktrees outside the repository:
`/work/dwong/p4-hostconfig-check-20261126/repo` (branch tip, untouched), a harness clone
`/work/dwong/p4-hostconfig-check-20261126/autoresearch_harness` at `a3fedbbd`, a current-main worktree
`/work/dwong/p4-hostconfig-main-20261126`, and a merge worktree `/work/dwong/p4-hostconfig-merge-20261126`. The
failing log is kept at
`/work/dwong/p4-hostconfig-check-20261126/tmp_pytest/test_trackp_runs_the_clone_scr0/job/out/logs/000_sft-select.log`
(sha256 `93d62311fd2dc0aa84f744befd4f47f000cb7f7933326e4d7e77fb1206904c34`; it shows the `FileNotFoundError`).

## What happens next

Do **not** publish the fill on this evidence. The local worker (test owner) can fix the missing-runs handling or the
test, then the two files are rerun; if they pass on the merge result, the coordinator can publish under
R1-AUTONOMY (3). The fill's six `TODO_VERIFY_ON_HOST` replacements and the `causal_conv1d` line are not implicated
by this failure; the branch's review remains valid for the values.

**Decided alone:** to re-run the two files on the unchanged branch tip to confirm the first result; to change
nothing, since the task says zero failures are the publication condition.

**Needs:** a local-worker code/test fix (missing `--runs` path as `STOP:` rc 2, or a real runs fixture), then a
re-run of the same two files on the merge result.
