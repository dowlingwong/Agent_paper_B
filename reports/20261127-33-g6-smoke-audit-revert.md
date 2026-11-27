# G6 smoke audit path removed — review ACCEPTED (`compute/20261127-31`)

**Result: `audit_seeds` refuses the engineering smoke seeds again; the G6 audit no longer carries a Y path the
frozen pre-declaration excludes.** Focused tests pass, the full suite is base=tip with identical failure IDs, and
the independent tier-E review is ACCEPTED.

- **Task:** `compute/20261127-31` (the coordinator's correction after the D.3 smoke merge `35c42b81`).
- **Deliverable branch:** `compute-g6-smoke-audit-revert-20261127` @ `345f4c97dc9b6f2db2336ba9ceea53726f12cbde`
  (base `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`), pushed. Three files: `r1/c3/d3/audit.py`,
  `r1/tests/test_d3_audit_g6.py`, `r1/tests/test_d3_smoke_engineering.py` (+14/−21).
- **Review:** `compute-g6-smoke-audit-revert-review-20261127` @
  `6eadf6555d7be5c0b5f640ff3cf38886f592db2b`; **ACCEPTED**, no code fix required.
  `docs/r1/reviews/G6_SMOKE_AUDIT_REVERT_REVIEW_20261127.md` sha256
  `a4d0c9260d5bd6db5a962b7e8e192edca0a36471a708d1c76714dfcbd3f91a01`.

## What changed

- `SMOKE_AUDIT_SEED_BASE` and the `6301-6302 → 6391-6410` branch are removed.
- `audit_seeds(s)` accepts only `6201-6218` and raises `AuditStop("instance seed … is outside 6201-6218")`
  otherwise. `6201 → 6701-6710`, `6218 → 6871-6880`; `6301`, `6302`, `6200`, `6219` all raise.
- The two tests now assert the refusal; no assertion is loosened elsewhere.
- `r1/scripts/d3_smoke_engineering.py` stays as the 27 Nov engineering record. Its `audit` subcommand now
  necessarily stops at `AuditStop` (it was never an evidence path); no campaign or analysis code imports it.
  Its docstring still mentions the historical audit path (non-blocking review minor).

## Tests

- Focused, with a clean harness at `9bb416805175149eb87b71f28d77530572aa4bce`:
  `AR_HARNESS_ROOT=<9bb41680> .venv/bin/python -m pytest -q r1/tests/test_d3_audit_g6.py r1/tests/test_d3_smoke_engineering.py`
  → **17 passed** (same at base).
- Operator full suite, base `c80f83bc` and tip `345f4c97`, Python 3.12.8, same harness:
  **119 failed, 5,032 passed, 164 skipped, 3 errors, 71 subtests passed**, identical sorted FAILED/ERROR IDs
  (122 IDs, sha256 `e23e215a56912201018779cc9f0d13b23bf0c364bee3043a0a89014e06c4453a`).
- Independent reviewer full suite (its own clean worktrees, `--tb=no`):
  **117 failed, 5,034 passed, 164 skipped, 3 errors, 71 subtests passed**, identical base/tip IDs
  (sha256 `29557901deee7bcb8ece0882bca8b7fddf347d6a79df84c26f6890c1d7b1acdb`). The two-run difference is
  environmental (two tests), not code: in both runs the base and tip sets are byte-identical, so there are
  **zero new failures**.

## What happens next

- The coordinator merges the branch; no pinned D.3 hash changes (`d3_analysis.py` untouched) and the frozen
  pre-declaration's `audit_seeds` text is restored in code.
- G6 is ready for the D.3 pre-declared smoke (`openml_climate`, 6301-6302, no Y) and for campaign audits; the
  27 Nov engineering smoke remains a record only.
- Non-blocking review minors (docstring, old report wording) are left as historical text; no evidence path
  depends on them.

Decided alone: to keep `r1/scripts/d3_smoke_engineering.py` unchanged as the card requires, and to record both
the operator's and the reviewer's full-suite numbers rather than pick one.
