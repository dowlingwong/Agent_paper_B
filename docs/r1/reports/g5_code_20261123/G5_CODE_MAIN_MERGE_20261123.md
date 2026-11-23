# G.5 code on top of main without READY 86 (23 Nov 2026)

AI-assisted (Claude). ENGINEERING_ONLY.

## What this is

READY 86 (the Mac desk's sweep-1 release fix, branch `mac-sweep1-release-compat-20261123` @ `fbbac887`) is
superseded: the cluster agent's own R1-SWEEP1-RELEASE-COMPAT implementation (`r1/c3/sweep1_compat.py` with a
`replay_builder` hook in `audit.verify_evidence_completion`; R1-SWEEP1-RELEASE-COMPAT-SCOPE) is on main `3522e59b`,
and the sweep-1 train/dev release passed with it (receipt `f06e37a9…`, train 593 / dev 276; main `000ac3b1`). READY 90
(`mac-g5-code-3b2-20261123` @ `459b2161`) contains READY 86 through the merge `b7b6e9cf` and so conflicts with main in
`r1/c3/release_checks.py`.

This branch, `mac-g5-code-main-20261123`, starts from READY 90's tip and merges origin/main `000ac3b1` with a merge
commit (`30e2d51a`), resolved as follows:

| File | Result |
|---|---|
| `r1/c3/release_checks.py` | main's file byte for byte (`_sweep1_compat_published`, `sweep1_integrity` with `sweep1_compat.rebuild_v2_table`, `_sweep2_batch_published`, `sweep2_integrity`), plus: one docstring sentence naming `g5_integrity`; `import subprocess` (used by the G.5 block); the G.5 block (`G5_PATHS`, `G5_SPEC`, `_g5_git`, `_g5_unpublished`, `_g5_published`, `g5_integrity`); `"g5": g5_integrity` in `INTEGRITY_CHECKS` |
| `r1/tests/test_c3_sweep1_release_compat.py` (READY 86's test) | removed |
| `docs/r1/reports/release_20261123/SWEEP1_RELEASE_COMPAT_20261123.md`, `docs/r1/reviews/SWEEP1_RELEASE_COMPAT_REVIEW_20261123.md` (READY 86's report and review) | removed |
| everything else of main (`audit.py`, `sweep1_compat.py`, `test_c3_release.py`, `test_sweep1_release_compat.py`, PLAN, records) | main's, unchanged |
| all G.5 code and tests (parts 3a, 3b-1, 3b-2; READY 84's draft) | kept unchanged |

`git diff origin/main -- r1/c3/` shows only `release_checks.py`, and only the additions listed above. No READY 86 symbol
(`_sweep1_compat_replay`, `normalize_provenance`, `probe_builder`, `SWEEP1_TABLE_COMMIT`, `checkout_bytes`,
`child_harness_root`, `SWEEP1_CLASSIFICATION_REL`) remains in code. The historical G.5 review records that mention
READY 86's test counts are left as they were written.

## Full r1/tests suite against main's baseline

Both runs on the Mac desk's container, one after the other, with `/tmp/tgport312/bin/python -m pytest -q
-p no:cacheprovider -rfE r1/tests`, `AR_HARNESS_ROOT` set to a harness checkout at `c025f89a`, `PYTHONDONTWRITEBYTECODE=1`
and a fresh `TMPDIR`:

| Run | Commit | Result |
|---|---|---|
| baseline | origin/main `000ac3b1` | 55 failed, 3530 passed, 196 skipped |
| this branch | `30e2d51a` | 55 failed, 3705 passed, 196 skipped |

The two failure lists (`FULLSUITE_BASELINE_000ac3b1_FAILED.txt`, `FULLSUITE_BRANCH_FAILED.txt` beside this report) are
identical: **zero new failures**. The 175 additional passes are the G.5 tests (parts 3a, 3b-1, 3b-2 and the dates
fix). The 55 baseline failures are environment-dependent on this desk (historical harness objects, host tools, lease
guardian stdout handling) and differ from the cluster's own baseline (80 failed / 3360 passed in its environment).

## Update: main 89899f76 and the E4 row check (commits `ecfd86a5`, `baf6be5d`)

origin/main moved to `89899f76` (READY 87's arms readiness merged as `630398c6`; R1-ARMS-DECISIONS, R1-G5-DECISIONS-2,
R1-G5-MEM-E4). `ecfd86a5` merges it, without conflicts; `git diff origin/main -- r1/c3/` still shows only the G.5 block
of `release_checks.py`.

`baf6be5d` fixes the switch's G5-MEM A row check: it required the E4 amendment row itself to name "G5-MEM", which
main's R1-G5-MEM-E4 does not (it is tied to G5-MEM A by R1-G5-DECISIONS-2's "G5-MEM A (…; with R1-G5-MEM-E4)"), so
every G.5 job would have STOPped. The decisions row must now name every decision's option and, under G5-MEM A, cite the
E4 row id; the E4 row must name "E4" and "memory modes". A new test runs both checks against this checkout's PLAN.
(Added with the G.5 follow-ups, `G5_FOLLOWUPS_20261123.md` item 6: these two term checks alone do not refuse one row
serving as both, since `plan_row` strips only the id cell; `decision_row_checks` now refuses
`decisions_row == e4_amendment_row` under G5-MEM A explicitly.)

Full `r1/tests` again, same environment and procedure:

| Run | Commit | Result |
|---|---|---|
| baseline | origin/main `89899f76` | 58 failed, 3567 passed, 196 skipped, 3 errors |
| this branch | `baf6be5d` | 58 failed, 3743 passed, 196 skipped, 3 errors |

The failure and error lists (`FULLSUITE_BASELINE_89899f76_FAILED.txt`, `FULLSUITE_BRANCH_baf6be5d_FAILED.txt`) are
identical: **zero new failures**. The six entries new against the 000ac3b1 baseline are `test_c3_arms_freeze.py`
(merged into main with READY 87), which need LightGBM; this desk's interpreter has none, so they fail on main too. The
176 additional passes are the G.5 tests (175 as before, plus the new row-check test).
