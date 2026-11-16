# Paper C — build status

ENGINEERING_ONLY. One line per phase, written by the executor (chat-session Claude). Runbook: `BUILD_RUNBOOK.md`.

| Phase | Commit | Tests | Review | Notes |
|---|---|---|---|---|
| P0 | (this commit) | 1 passed | not required | branch `paperc-build-20261115` from `paperc-scaffold-20261115` @ `b963170`; cloud clone; Python 3.13.18 venv `paperC/.venv` (git-ignored); freeze `env/pip_freeze_P0.txt` |
| P1 | `2f0f804` + round-2 minors | 73 passed (with P2) | **ACCEPT** (round 2; `reviews/BUILD_P1_REVIEW_20261115.md`) | round-1 fixes and round-2 minors 20–27 in `reviews/BUILD_P1_RESPONSE_R1_20261115.md`; `failed_invalid` added as `Outcome.failure_category` |
| P2 | `bbb40d1` → round-1 fixes | 86 passed | **ACCEPT** (round 2; `reviews/BUILD_P2_REVIEW_20261115.md`); round-1 fixes and round-2 minors in `reviews/BUILD_P2_RESPONSE_R1_20261116.md` | `paperc/seeds.py` (declared `SOURCES` / `RNG_KEYS` / `EXTRA_BLOCKS`, full completeness scan), `seeds/registry_v1.json`, `reports/SEED_REGISTRY_CHECK_20261115.md`; Paper C blocks proposed: instances 50000–60000, RNG keys 60000–61000, training seeds 61000–62000, audits 10,000,000–11,000,000, campaign prefix `pc-` |
| PH | `cb2e837` → round-1 fixes | 90 passed | round 1 NOT ACCEPTED (4 MAJOR, 8 MINOR) → `41a9205`; round 2 NOT ACCEPTED (1 MAJOR: C1 paired unit, 4 MINOR) → `8e4946b`; **round 3 ACCEPT** (4 MINOR, fixed: `reviews/BUILD_PH_RESPONSE_R3_20261116.md`) | `paperc/census.py` (schema `paperc_census/v2`: + C1 paired noise, C3 audit pilot, E1b pilots, S1.1 interactions, trial-1 drop, per-mode stats, stakes), report rewritten; deviation: reads raw ledgers through small adapters, not P1 records (P1 rows from Paper B ledgers = B5 loader) |
| P3 | (this commit) | 122 passed, 1 xfailed | review round 1 pending | steps 1–6 + B17: `paperc/esyn/` (`worlds.py` pinned port, `extra.py` 7 worlds, `sim.py` simulator writing P1 rows, `policies.py`, `families.py`, `dp.py` exact budget DP, `oracle.py` certified oracle, `table.py`); `esyn/oracle_table_v1.json`; `reports/ESYN_ORACLE_TABLE_20261116.md`; schema: optional `State.candidates` (B17); 6 of 7 channel worlds certified, information positive but uncertified |
