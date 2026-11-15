# Build P2 — executor response to review round 1 (16 Nov 2026)

ENGINEERING_ONLY. Executor: chat-session Claude. Review: `BUILD_P2_REVIEW_20261115.md` (round 1, NOT ACCEPTED, 3 MAJOR / 6 MINOR). Tests after the fixes: 84 passed. `python -m paperc.seeds` regenerates the committed registry byte for byte.

| # | Finding | Change |
|---|---|---|
| 1 | report and status show the stale audit block and omit new blocks | `SEED_REGISTRY_CHECK_20261115.md` rewritten: audit block 10,000,000–11,000,000; every added block (oracle, S1.1, legacy audits, node default 42, e2e 999, RNG roots) listed as a difference from the prose; `BUILD_STATUS.md` updated |
| 2 | scan misses bare `SEED` | pattern `^[A-Z0-9_]*(SEED|_BASE)[A-Z0-9_]*$` (test `test_scan_name_matches_bare_seed`); the scan also reads worker-seed keywords and `seed` / `seed0` defaults and keywords ≥ 10; the three missed date keys and the simulators' RNG roots are registered through the declared `RNG_KEYS` table |
| 3 | seed 42, seed 999, legacy 33001–34999 missing; Paper C membership not enforced | `EXTRA_BLOCKS` (node default 42, legacy Track S audits) and a `SOURCES` entry for the e2e worker seed; `Registry.paper_c_check` and `campaign_prefix`; `check_campaign` now requires every seed in its own Paper C block and the `pc-` campaign prefix when given the registry (test in `test_seeds.py`) |
| 4 | domains are declarations | stated in the module docstring, the registry (`domains.note`) and the report |
| 5 | `unaccounted` checks only range ends | interval coverage: every range must be covered in full (`test_unaccounted_detects_new_constants_and_range_gaps`) |
| 6 | `function()` fragile | decorators, annotations and defaults stripped; compiled with `dont_inherit=True` and an explicit `annotations` flag (`test_function_compiles_in_isolation`) |
| 7 | `pc-` wording; not enforced | report says the prefix makes hash *inputs* distinct; enforced by `check_campaign`; the runner port must build `pc-` ids (noted in the report) |
| 8 | namespace exclusions unnamed; no Paper C training block | docstring names D26 seeds and ML/RNG seeds as out of scope; `paperc_train_seeds` 61000–62000 added |
| 9 | sources inline | declared tables `SOURCES`, `RNG_KEYS`, `EXTRA_BLOCKS`; `paper_b_blocks` reads exactly those |
