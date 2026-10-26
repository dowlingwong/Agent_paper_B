# Portal exam Phase 1 — implementation and review record

26 October 2026. AI-assisted. ENGINEERING_ONLY / DRYRUN. STOP 1; independently reviewed and accepted.

Author decisions are recorded in PLAN §10 and STATUS: corrected `/home/dowling/exam-x/{models,work}` storage, stop below 100 GB available, research/publication licence approval, unreleased Ornith-31B removal without substitution, vendor Ornith-35B mapping, SSH bare-repository transfer from the Mac, and optional user-level uv/Python installation. The effective registry is 21 candidates and three anchors plus the declared OLMo Think sensitivity.

Phase 1 implementation covers runbook gaps 1.1–1.10. The handoff is `docs/r1/overnight/EXAM_X_CODE_HANDOFF.md`; baselines, dependency export and public vendor metadata are in `docs/r1/reports/exam_phase1_20261026/`. The outcome-blind rule was committed at `4b9c656` before any B1 fixture data; no real B1 data exists. Paper implementation `e6f42c0`, review fixes `930687c`, regression `57f56e5`, reporting correction `df1a6eb`. Harness implementation/pin `897d83c8efa364ec2fdd37288241cc42e01d7274`.

A fresh reviewer independently inspected both repositories and reran tests and the fake pipeline. Initial review found three MAJOR issues: zero-audit candidates aborted analysis, B2 could re-enable thinking disabled by Stage A, and phase inputs lacked content binding. The corrections retain unrankable diagnostics, enforce thinking eligibility, and verify author/config-bound Stage A/B1 hashes before any campaign roots. Additional regression tests cover these counterexamples and changed completed-root evidence. The MINOR reporting correction exposes A4 coverage, failed queries and fixed descriptive calibration bins; no-effect evaluation is explicitly pending an author outcome definition.

No model weights were downloaded, no LLM inference ran, and no portal runtime was installed or transferred. All campaign results generated in Phase 1 are synthetic DRYRUN fixtures; CPU regression suites and loopback fake servers are engineering checks. No protected branch was merged or pushed. Phase 2 remains unstarted.

## Validation

| Checkpoint | Before | After implementation | Independent rerun |
|---|---|---|---|
| Paper full suite | 417 passed / 22 failed / 9 skipped | 445 passed / 21 failed / 9 skipped; 698.12 s | 445 passed / 21 failed / 9 skipped; 696.16 s |
| Harness full suite | 448 passed / 8 failed / 1 collection error | 454 passed / 8 failed / 1 collection error; 97.37 s | 454 passed / 8 failed / 1 collection error; 95.39 s |
| Final focused exam suite | New tests | core/observer 30 passed, final standalone dryrun PASS | 31 passed including fake-server integration; 48.86 s |

Full-paper suites launched at `e6f42c0`; subsequent review fixes were verified separately by final focused tests and independent counterexamples. Exact issue-ID comparison found **zero added failures/errors** in either repository. Harness issue IDs are unchanged; the paper baseline `test_c3_sweep_dryrun_watchdog_restarts_a_killed_runner` failure passed in both after runs. This does not establish a causal repair of a timing-dependent test. Existing Mac/legacy-fixture failures remain visible rather than reported as an all-green suite. Logs, comparison JSON and final dryrun summary are saved under `exam_phase1_20261026/`. The frozen rule digest still matches. `--check-config --allow-placeholders` passes.

**Independent verdict: ACCEPTED**, all three MAJOR findings and one MINOR finding resolved. Review: `docs/r1/reviews/EXAM_1_REVIEW_20261026.md`. This is Phase 1 engineering acceptance. Stopped at STOP 1 for coordinator/author merge and subsequent phase direction; Phase 2 and evidence gates remain in force.
