# STOP scene — S0.4 on TASL-2 (digits_mlp), 9 Nov 2026 — NOT a completed phase

This directory is the copied-back **STOP scene** of Track S Phase 3 S0.4 (ENGINEERING_ONLY), not a
completed S0.4. Do not treat it as a finished dev-campaign set and do not overwrite it with a later run.

- S0.4 (10 instances, k = 1) committed **5/10 roots** (s30001, s30004, s30006, s30007, s30009).
- The other **5 instances** (s30000, s30002, s30003, s30005, s30008) failed on a **deterministic
  pinned-code stale-edit `r1.c3.features.ReplayError`** raised in `r1/tracks/a2u.py` `replay()` (known
  issue recorded in `docs/r1/reports/TRACKS_HOST_FACTS_20261030.md` §5.1; not fixed by the operator).
- Retry exhaustion after the retry session: **exhausted = 3** (s30000, s30002, s30003; 3 attempts each,
  `--max-retries 2` = 3 attempts); eligible = 5 committed + 0 leaves + 3 exhausted = 8, so the failure
  rate is **3/8 = 37.5 % > 2 %** → **STOP** per Track S operator runbook rev 3.3 §0.6/§10.
- Dry-run plan at the STOP: `roots_todo: 2` (s30005, s30008 at 2 attempts), `leaves_todo: 0`,
  `exhausted: 3`.
- liveness, fit_prior and `a2u_prior.json` were **not run** (the phase stopped before them).
- Full report: `docs/r1/reports/TRACKS_PHASE3_20261109.md`.
