# Merge review: `trackp-20261026` → `main` (26 Oct 2026)

Coordinating session (Claude), at the author's request; AI-assisted. Branch tip `6f67717` (45 commits from `b5a7aec`), merged onto `main` at `8311df6` (Track X Phase 1 merged). Phases 0–4 were each independently reviewed and accepted on the portal (`docs/r1/reviews/TRACKP_{0..4}_REVIEW_20261026.md`); this review covers what the merge changes in shared code and documents, not a re-review of the phases.

## Scope checked

- **Conflicts.** One: `docs/r1/STATUS.md` (both sides added entries at the top). Resolved by keeping both blocks, Track X entries first, then Track P; no text changed.
- **Existing code touched by the branch:** `r1/c3/labels.py`, `offline_eval.py`, `prior_model.py`, `serve.py` and three existing tests. Every `soft_label` caller on `main` and on the branch was listed: the only production caller (`offline_eval.assemble`) passes `sigma_mode` explicitly and defaults to v1 (`se_audit`); a v1-style call with `se` under the new default raises instead of silently changing width. No other caller exists on `main` (Track X Phase 1 added none).
- **v1 reproduction.** `offline_eval.assemble` on the 19 Oct pilot table (627 rows, both `seed_split` settings) was run with `main`'s code and with the branch's code (`sigma_mode="se_audit"`) in the same environment: soft labels identical (sha256 of rows equal for both settings).
- **RPS.** `losses.rps`/`metrics.rps` = ½[(p₀−y₀)² + (1−y₀)·mean_{k=1..10}(Q_k−R_k)²]. Its expectation over hard outcomes drawn from y equals 2·RPS(p, y) + a term free of p, so it is proper; normalised by 1/(K−1) with K = 11 ordered bins, in [0, 1].
- **Secrets.** `jev_client.py` and `rb_demos.py` read keys from the environment only; logged request headers carry `Bearer <redacted>`; no key or token string in the tree. Jev refuses non-versioned model IDs; the demo writer refuses peak hours and receives no label or audit fields.
- **Guards.** Evaluation-seed columns are refused outside the P.4 final evaluation with its authorization note; the GPU lease takes `flock` on `~/r1_locks/gpu0.lock`, checks `nvidia-smi` and the Track X STATUS heading.
- **Large files.** `r1/c3/train/data/e0_v1.jsonl.gz` (0.8 MB, hashed, the committed E0 set). Nothing larger added.

## Tests run here (Linux VM, Python 3.12, numpy 2.4.4, scipy 1.17.1, lightgbm 4.7.0; no torch, no harness checkout)

`r1/tests/test_c3_*.py` + `test_trackp_*.py`: 175 passed, 27 skipped, 11 failed, 9 collection errors.
- The 9 errors are modules that import torch or the harness (not installable here: no disk, PyTorch index blocked).
- 9 of the failures (`test_c3_sweep_dryrun`, `test_c3_prior_model::…a4…`, `test_c3_dataset::…replays…`, `test_c3_control_dryrun`) fail identically on `main` in this environment (harness absent): environmental.
- 2 Track P failures, both environment-dependent, neither a code defect:
  - `test_trackp_soft_label_v2::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical` compares against a hash computed on the portal; here both `main` and the branch give the same (different) hash — see "v1 reproduction" above.
  - `test_trackp_exam_synthetic::…regenerates_byte_identically`: one of 4,000 items differs, its **hard** label, by one bin — an m that lands on a bin edge resolves differently across platforms. The committed file and its sha256 remain the source of truth (`load` verifies the hash).

The portal agent and its reviewers ran the full suites with torch on the portal (paper 559 passed; failing set unchanged from the baseline).

## Findings (minor; for the Track P agent, not blocking)

1. Make the two environment-pinned tests portable: compare v1 against `main`'s code path (or a stored row table) instead of a platform hash, and define the hard-label tie rule at bin edges (e.g. round m before binning, or nudge exact-edge draws) so regeneration is platform-independent.
2. `run.track_x_running` must also honour the evidence marker `~/r1_locks/trackx_evidence.active` (R1-PORTAL-SCHEDULE amendment of 26 Oct), with the marker authoritative.
3. The E0 width failure in the DRYRUN is not a ceiling artefact: the module reports that a perfect predictor reaches width slope 0.98 on this grid. The open questions are the E0 training budget, head-fit learning rate and learning-rate grid (author decisions pending before P.3a evidence).

## Verdict

**Accepted for merge.** No conflict beyond STATUS; shared-code changes are backward compatible and reproduce v1 exactly; findings 1–2 go to the Track P agent.
