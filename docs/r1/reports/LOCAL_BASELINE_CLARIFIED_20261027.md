# Clarified-scope local baseline and comparisons — 27 October 2026

AI-assisted engineering test outcomes only; no scientific evidence, labels, remote jobs or authorization. This supplements rather than overwrites `LOCAL_BASELINE_20261027.md`. PLAN R1-LOCAL-TEST-SCOPE permits existing CPU test sklearn fits and node subprocesses; the earlier incident is closed within scope after clarification, with its observations and unknowns retained.

## Harness

Fresh isolated harness clones at `897d83c8efa364ec2fdd37288241cc42e01d7274`, baseline and repeat; same venv PATH makes subprocess Python resolve NumPy. CPU and offline settings and exact commands are in the retained `harness-before-run.sh` / `harness-after-run.sh`. Both tests report 443 passed, 19 failed, 1 collection error, 55 subtests passed and no skips. The exact JUnit outcome-ID multiset is identical (`harness-after-comparison.json`). Ten failures report sandbox loopback `PermissionError`; nine concern missing historical report/ledger/figure/section files; the uninitialized claw-code submodule causes the collection error. No claim that these suites passed, or that this test rerun establishes remote readiness. Logs and JUnit are retained in `local_baseline_clarified_20261027/`.

## Paper baseline

At paper `1f5c27ed0731917d52a3f58b07ea2e1633b78c11`, `make r1-test` under corrected venv PATH: 510 passed, 55 failed, 34 skipped and 2 deselected. Fifty-two failures report permission errors, one process-discovery assertion has unproven cause, and two are recorded byte-identity failures. Separately, permitted tiny random-weight unit files report 8 passed, 1 failed (missing `kev`), 39 skipped (empty offline tokenizer cache). The main run intentionally ignored those two files and three synthetic campaign/label-style integration files; the selected tiny files were subsequently checked separately. Two individual cases were deselected for a >10-minute risk and a real desktop dry-run respectively. Exact collected excluded IDs, command, environment and results are retained; this is a restricted baseline, not a full-suite pass.

The paper comparison and independent review are pending. The paper subprocess had a 590-second outer limit, not a verified per-test timeout; all reported completed runs finished within the bound, and the explicitly long test was excluded. CPU settings and offline flags were operator-recorded; they do not independently establish accelerator non-use in every subprocess. The corrected harness run records a per-test timeout. No blanket inference is made about prior failures or subprocess histories.
