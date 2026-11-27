# Build P5 — executor response to review round 1 (16 Nov 2026)

ENGINEERING_ONLY. Review: `BUILD_P5_REVIEW_20261116.md` (round 1, NOT ACCEPTED, 3 MAJOR / 12 MINOR). `relevance.py` was rewritten; the demo report regenerated; 184 tests pass.

| # | Finding | Change |
|---|---|---|
| 1 | forks counted unweighted | `forks="root"` (default) counts only root trajectories and reports the fork rows excluded; `forks="weighted"` adds continuation rows with weight 1 / `fork.p_select`; forced rows (fork arms, interventions) are never counted as decisions; shares, quantiles and intervals are weighted; test `test_forks_forced_rows_and_other_epochs` |
| 2 | empty epoch called "no decision-relevant states" | three statuses: "not assessed (no eligible rows)", "no decision-relevant states (0 of n within the widest band)", or the share within it with its interval; the STOP 4 fixture now includes E2 rows with Track S-like margins (45 of 300 within 0.5 σ) and asserts E1 "no decision-relevant states" and E2 relevant, per line of the markdown; a mutation (E1 rows moved inside the band) flips E1; `test_not_assessed_is_not_the_gate_outcome` |
| 3 | invalid / divergent E2 discards | E2 rows with `candidate_invalid` or `candidate_divergent` are excluded and counted (`n_invalid_discards`); they need no m̂; test |
| 4 | policy skips not reported | eligible E1 policy skips and executes per node in the summary and the report |
| 5 | single scalar h; raw margin | h is a number or a mapping node -> h; `e2_stat="delta_hat"` gives Paper B's raw-keep margin; the demo measures E2 against N1's own h; tests with h ≠ 0, a mapping and the raw statistic |
| 6 | NaN passes; API validate default | non-finite values are refused with the row's identity; `validate=True` is the API default too; `--json` is written with `allow_nan=False` |
| 7 | bare KeyError / TypeError | malformed rows raise `RelevanceInputError` naming campaign and step |
| 8 | silent price sources | price source counts per node and threshold (argument / mapping / forecast / env) in the summary and the report; `--g` and `--g-json` are mutually exclusive; a mapping missing a node falls back and the fallback is reported |
| 9 | verdict rule unstated; `relevant` | the rule is stated in the report header and the module docstring; the JSON field is `any_within_widest_band`, plus the `status` text |
| 10 | demo note | corrected: five worlds have a 95th percentile of (V\* − g)/σ ≤ about 0.45; information (95th about 3.4, max about 19) and interaction (tail to about 3.7) are the exceptions; N1 skips nothing or almost nothing in the four g = 0 worlds (now visible in the policy-skip column) |
| 11 | pooling; no intervals | per node the report lists campaigns, policies and W; every share has a 95 % interval clustered by campaign |
| 12 | no input provenance; empty input | the CLI report and JSON list every input file with row count and sha256 and the validation flag; empty input is an error (exit 2) |
| 13 | CLI tracebacks | bands are validated (positive, non-empty); output directories are created; non-JSON lines are reported with file and line number; input errors exit with code 2 and a message |
| 14 | weak tests | tests added for forks, forced rows, invalid E2 rows, verify / reaudit / final exclusion, h ≠ 0 and the raw statistic, multi-node prices and precedence, extra thresholds, NaN / inf, malformed rows, empty input, beliefs, `Transition` input, CLI content (inputs, sha, thresholds, JSON) and CLI errors; `markdown()` takes its bands from the summary |
| 15 | readiness | the belief must be named unless the rows carry exactly one non-privileged belief (no A2-U default); the docstring lists what the B5 loader must provide; several E1 thresholds per run (`thresholds=`, CLI `--threshold LABEL=VALUE`), e.g. the price and a static threshold as at STOP 4 |
