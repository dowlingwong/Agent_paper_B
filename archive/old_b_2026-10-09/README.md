# Archive: old Paper B route (archived 9 October 2026)

Everything here belongs to the Paper B route that came before route R1: the two-checkpoint verification-timing study and the candidate-consistency task. It is kept for provenance only, and **none of it has authority**. The canonical plan is `docs/r1/PLAN.md`.

## Contents

`docs_paper_split/` is the complete former `docs/paper_split/` directory, as it stood in the working tree on 9 Oct 2026, including the uncommitted RUNBOOK §19–§20, OPEN_ITEMS §B7–§B8 and `B_PROMPTS_20261009.md`. It contains:

- the runbook;
- the open items;
- the status and validation logs;
- the decision sheets;
- the design documents;
- the reviews and prompts;
- the claims ledger, scope and prior disclosure;
- the task realism reports.

`paper_b_manuscript/` is the old manuscript, *When to Spend a Verification Budget under Replay Uncertainty* (ICML 2027 target, two-checkpoint verification timing), moved here from `papers/paper_b/` on 13 October 2026, with its build products, `legacy/` and `archive/B1_20260927/` subfolders unchanged. It reports no result. The R1 manuscript will go in `papers/r1/` (RUNBOOK Phase 4).

## Dangling references

After the 13 Oct move, `scripts/make_release.py`, `scripts/check_release_independence.py`, `release/paper_b_manifest.json`, `PROVENANCE.md` and `docs/r1/PLAN.md` §8 still name `papers/paper_b/...`; those names refer to `paper_b_manuscript/` here. `scripts/release_provenance.py` checks `papers/paper_b/main.tex` in a historical source commit, where it still exists. `make paper-b` was repointed to the new path.


Some code docstrings, `protocols/paper_b/*.yaml` and `scripts/make_release.py` still name `docs/paper_split/...` paths. Those names refer to the files in this archive. The old release tooling (`make release-b`, `check-release-b`) belongs to the old route and is not maintained.

## Carried over to R1

What R1 carried over, and why: `docs/r1/PLAN.md` §8.
