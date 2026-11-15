# W2 v3 Track P data rebuild — execution record (deepthought, 15–16 Nov 2026)

**Authority.** Author rows `R1-W2-3-STOP`, `R1-B2-REPAIR-SCOPE-ACK`, `R1-SWEEP1-CLASSIFY` (`author-ack-w23-20261115`
@ `b0c8a48d`); the author's main-merge decision (16 Nov 2026 ~00:1x CET) with **`main = 60ec768e`** (fast-forward
`36b89773 → 60ec768e`, no force; merge of `b30cc950` via `--no-ff` carrying the 90d9b7fe evidence-path moves, the
`R1-SWEEP1-CLASSIFY` PLAN row, the classification review and the sidecar `bb6d891c…`). Unit reviewed by
`docs/r1/reviews/W2_3_REBUILD_REVIEW_20261115.md` (rounds 1–3, final **ACCEPTED** at `7c85ff4e`).

**Result: REBUILD_OK — PASS.** New versioned table built with `c3_features/v3` + `trackp_prompt/v2`, label
**EVIDENCE**, from the read-only sweep-1 ledgers; no v1 table overwritten, no data deleted, no retry after STOP.

## 1. Execution context (recorded per author)

| item | value |
|---|---|
| paper root | `/work/dwong/htcondor_prep_20261114/w2_paper_main_60ec768e` — clean worktree at `60ec768e`; `git rev-parse HEAD = 60ec768ee909bfaa3dfa6f5ef6ba0d8d60f5c70`; `git ls-remote origin refs/heads/main` = same SHA; worktree clean; authority files byte-identical to published main (the reviewed code's `_verify_published` enforces this and passed) |
| code checkout | `/work/dwong/htcondor_prep_20261114/w2_v3` at the reviewed code commit `d8aa9561…` (the unit's own pin), `git status` clean before and after |
| unit | branch `w2-3-rebuild-unit-20261115` @ **`e2544f24`** (accepted logic; two post-acceptance bug fixes, see §4); reviewed copy SHA-256 `2420602f…`, run copy `dfbfddfd…`; the only difference is the author-directed `PAPER_ROOT=` line |
| harness | `AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/autoresearch_harness` @ **`6adf3859…`** = the index's `launch_provenance.harness_commit` (read-only) |
| W2-3 evidence | `w2_3_check_20261115.json` SHA-256 `b11217d0…`: PASS, 288/288 ledgers × 20 worker runs, 0 differing |
| environment | python 3.12.2, numpy 1.26.4, ≥2 GiB df preflight (147,423,232 kB free recorded) |
| exact command | `python3 -B -m r1.c3.dataset build-sweep --index <paper-root>/results/r1/pilot/C3_sweep_index_20261028T033315Z.json --paper-root <paper-root> --classification <paper-root>/results/r1/evidence/C3_sweep_classification_20261028.json --out /work/…/tables/c3_features_v3_20261115T232007Z` |

## 2. Output (new versioned directory; v1 untouched)

`/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z` (842 KiB)

| file | SHA-256 |
|---|---|
| `proposals.jsonl` | `d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5` |
| `configs.json` | `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` |
| `build.json` | `7f56619c2cc5ef2145ace44350baac3bc7906433e279a284e9627a2452e1b643` |
| `manifest.json` | `661f0fd83c14f44b5bba79b3714003f0a094d1899f221762f77ef73e0fcdf04b` |

`sha256sum -c SHA256SUMS` → all OK. Manifest: `featurizer_version = c3_features/v3`,
`prompt_version = trackp_prompt/v2`, `code_commit = d8aa9561…`, paper root and sweep-index/classification/evidence
paths+SHAs, `table = {label: EVIDENCE, n_proposals: 4999, n_configs: 302, replay_checks_total: {rows: 5813,
proposals: 4999, zero_delta_violations: 0, repeat_metric_violations: 0, skipped_invalid: 526, no_edit_rows: 0}}`,
`sweep_index.sha256 = 812468e2…`, `table_sha256` (EVIDENCE-only) for `proposals.jsonl`/`configs.json`, environment,
exact build command, the no-v1/v2-mixing statement, the budget-line disclosure and the v1-never-overwritten policy.
The code's own `_verify_published` and `_verify_original_blobs` passed (authority bytes = published main; evidence
trees byte-identical to their original sweep commits).

**Sources (classification remap):** `c3_20261028T033315Z_append_only_summary` → `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z` (commit `224c2483…`), `c3_20261028T033315Z_none` →
`results/r1/evidence/C3_sweep_none_20261027T224356Z` (commit `259722c…`), both `runs=20`, `label=PILOT` (the
index's historical label — a runner defect per R1-SWEEP1-CLASSIFY; the table label is EVIDENCE through the
classification sidecar).

## 3. Verification performed

1. Pin pre-checks (checkout HEAD/clean, paper-root authority files + SHA `812468e2…`/`bb6d891c…`, W2-3 evidence
   `b11217d0…`, paper-root HEAD = `ls-remote main` = `60ec768e`, ≥2 GiB free) — all passed before any build.
2. `build-sweep` exit 0; table files non-empty; manifest written and verified (versions, EVIDENCE label, counts,
   replay-checks cross-check, classification/evidence SHAs, file set, `table_sha256` present).
3. `SHA256SUMS` written, `|| stop`, and self-checked with `sha256sum -c` before `REBUILD_OK` (all OK).
4. No-v1-token scan of the table files (clean); `git -C <code checkout> status --porcelain` empty after the build
   (no tracked-file or `__pycache__` write: `-B`/`PYTHONDONTWRITEBYTECODE=1`).
5. `REBUILD_OK` written exclusively: `featurizer=c3_features/v3 prompt=trackp_prompt/v2 label=EVIDENCE`.

## 4. Post-acceptance corrections and preserved attempts (transparency)

The accepted unit needed two small fixes, both discovered on the first deepthought runs and committed on the
unit branch (no data affected; the table itself was rebuilt cleanly afterwards):

- `9bdc7c35` — `PAPER_ROOT` was assigned after `SWEEP_INDEX="$PAPER_ROOT/…"`, so `set -u` aborted before any
  output ("PAPER_ROOT: unbound variable"). Fixed by moving the assignment up.
- `e2544f24` — the R5 cross-check assumed `replay_checks_total` is the integer 5760; it is the per-kind totals
  dict (rows 5813, proposals 4999, …). Fixed to assert `ledgers=288`, `runs_total=20`, `differing=0` and
  `288×20 ≤ rows ≤ 288×40`, and `proposals == n_proposals`. The first R5-failing run had already produced a
  byte-identical table (same file SHAs) and was preserved.

Preserved (moved aside, never deleted): `tables/c3_features_v3_20261115T231908Z.attempt-20261115T232002Z` and
`logs/rebuild_20261115T231825Z.attempt-…`, `logs/rebuild_20261115T231908Z.attempt-…`; the final clean run is
`tables/c3_features_v3_20261115T232007Z` / `logs/rebuild_20261115T232007Z`.

## 5. Read-only / no-deletion compliance

The sweep-1 ledgers and the paper-repository authority files were read only (the paper root is a clean worktree
under `/work`, `origin/main` fetched; `/ceph` sweep data untouched); the code checkout is a clean `d8aa9561`
checkout; no v1 table is referenced as output; no file was deleted; on STOP the partial directories were kept and
moved aside with a suffix; the `r1_sealed` refusal and the code's sealed-path guards were in force.

## 6. Next steps (gated; no training starts here)

- The table is the input for Track P prompt sets (`trackp_prompt/v2`); downstream Track P training remains blocked
  by the author's Q-TORCH gates (L40S/H200 `trackp_gpu_smoke.py` parity + one E0 equivalence job + v2 digest
  approval) and the other standing gates. The synthetic exam `trackp_e0/v1` keeps the v1 budget line (W2-4 open).
- The table manifest and `build.json` record the versions and provenance needed for the rebuild disclosure
  (feature version v3, prompt version v2, budget-line change, no v1/v2 mixing in the Track P table).
- Evidence copies in the repository: `reports/w2_3_rebuild_20261115/run_20261115T232007Z/` — **self-contained**
  (`manifest.json`, `build.json`, `proposals.jsonl`, `configs.json`, `SHA256SUMS` (verifies all four with
  `sha256sum -c`), `build.stdout`, empty `build.stderr`, the executed script copy `run_rebuild.executed.sh`
  (SHA-256 `dfbfddfd…`) and its one-line diff `run_rebuild.executed.diff` against the reviewed copy). The executed
  copy differs from the reviewed script only in the author-directed `PAPER_ROOT=` line.
