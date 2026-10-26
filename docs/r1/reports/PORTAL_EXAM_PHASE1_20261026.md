# Portal exam Phase 1 — implementation and review record

26 October 2026. AI-assisted. ENGINEERING_ONLY / DRYRUN. STOP 1; independent verdict pending.

Author decisions are recorded in PLAN §10 and STATUS: corrected `/home/dowling/exam-x/{models,work}` storage, stop below 100 GB available, research/publication licence approval, unreleased Ornith-31B removal without substitution, vendor Ornith-35B mapping, SSH bare-repository transfer from the Mac, and optional user-level uv/Python installation. The effective registry is 21 candidates and three anchors plus the declared OLMo Think sensitivity.

Phase 1 implementation covers runbook gaps 1.1–1.10. The handoff is `docs/r1/overnight/EXAM_X_CODE_HANDOFF.md`; baselines, dependency export and public vendor metadata are in `docs/r1/reports/exam_phase1_20261026/`. The outcome-blind rule was committed at `4b9c656` before any B1 fixture data; no real B1 data exists. Paper implementation `e6f42c0`, review fixes `930687c`, regression `57f56e5`, reporting correction `df1a6eb`. Harness implementation/pin `897d83c8efa364ec2fdd37288241cc42e01d7274`.

A fresh reviewer independently inspected both repositories and reran tests and the fake pipeline. Initial review found three MAJOR issues: zero-audit candidates aborted analysis, B2 could re-enable thinking disabled by Stage A, and phase inputs lacked content binding. The corrections retain unrankable diagnostics, enforce thinking eligibility, and verify author/config-bound Stage A/B1 hashes before any campaign roots. Additional regression tests cover these counterexamples and changed completed-root evidence. The MINOR reporting correction exposes A4 coverage, failed queries and fixed descriptive calibration bins; no-effect evaluation is explicitly pending an author outcome definition.

No model weights were downloaded, no LLM inference ran, and no portal runtime was installed or transferred. All campaign results generated in Phase 1 are synthetic DRYRUN fixtures; CPU regression suites and loopback fake servers are engineering checks. No protected branch was merged or pushed. Phase 2 remains unstarted.

Full-suite results, exact failure comparison and independent acceptance will be appended after completion.
