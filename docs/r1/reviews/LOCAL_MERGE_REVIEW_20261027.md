# Merge review: accepted work from `local-20261026` → `main` (27 Oct 2026)

Coordinating session (Claude), at the author's request ("验收的东西审一遍合进main"); AI-assisted. Source: branch `local-20261026` at `fa87d79` (H.8 deferred, Track G narrowed). Taken as a path-selective commit, not a merge commit, so the excluded paths can still arrive by a later merge once accepted.

## Taken (158 paths)

- All of `docs/r1/`: PLAN §10 rows of 26–27 Oct (R1-TRACKP-RUNBOOK-SCOPE … R1-H8-DEFERRED, R1-TRACKG-SCOPE), historical annotations in PLAN/RUNBOOK/C3_DESIGN/theory/host runbooks, `TECH_ROUTE.md`, Track P spec corrections (R1-BIN-EDGES, R1-RPS-CANONICAL, R1-RA0-RULE, R1-HARD-LABEL-ABLATION, R1-FOCUSED-SCOPE), proposals, reports, reviews, handoffs, the theory audit and author packets, the sweep-1 resume-stamp note, `templates/DEPLOYMENT_PREDECLARATION.md`, `prompts/TRACK_G_RUNBOOK.md`.
- Code accepted under L4.4/L4.5: `r1/predeclaration.py`, `r1/tests/test_predeclaration.py`, `r1/tests/test_harness_governance_fixture.py`.
- Checked: the Track P spec now matches the code (`labels.EDGES`, `losses.rps`); T2/T4 claims are unchanged (annotations only); no file over 0.5 MB; nothing outside `docs/` and the three code files.

## Not taken (left on the branch)

- `papers/r1/`, `Makefile` and `pyproject.toml` targets (L6 manuscript draft, unaccepted pending the author's proof check and citation gaps).
- `r1/analysis/`, `r1/tests/test_pilot_figures.py` (L4.3, unaccepted).
- The new `@pytest.mark.skip` markers in `r1/tests/test_c3_env.py`, `test_c3_prior_model.py` and `test_trackp_soft_label_v2.py`. They disable Track H's H.1/H.8 acceptance tests and the soft-label v1 reproduction test on the reasoning that the 19 Oct pilot "must never be training data". Those tests reproduce committed engineering numbers (fitting LightGBM on the pilot table as the 19 Oct gate code does); they are regression tests, not Track P training or evidence. Proposed clarification for the author: the pilot restriction in R1-H8-SPLIT-MAPPING concerns Track P training and evaluation evidence, not existing regression tests.
- The H.8 implementation (already reverted on the branch at `fa87d79`; preserved on `local-h8-20261027`).

## Checks run here (Linux VM, Python 3.12, numpy 2.4.4, scipy 1.17.1; no torch, no harness checkout)

`test_predeclaration.py`, `test_c3_labels.py`, `test_trackp_soft_label_v2.py`: 24 passed, 1 failed — the known environment-pinned hash test (`test_existing_pilot_table_rebuilt_under_v1_is_byte_identical`, see `TRACKP_MERGE_REVIEW_20261026.md`). `test_harness_governance_fixture.py` needs the harness and was not run here; it was accepted under L4.5 on the Mac.

**Verdict: accepted for main** with the exclusions above.
