# Sweep-1 train/dev release refusal — diagnosis and fix decision (22 November 2026)

**Read-only diagnosis; no sealed table, audit, label block or evaluation block was modified or opened for values.**
The refusal under R1-S2-LABELS-TRAINDEV-RELEASE remains: `ReleaseStop: STOP: integrity check failed for sweep1
(ValueError)` → `r1.c3.audit._verify_replay` → `evidence table differs from full source replay: proposals.jsonl`.
The step was not bypassed.

## Which code produced the sealed table

- Sealed table: `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table/`; `build.json` records
  `commit = ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` (the B.2 audit commit), `replay_checks = 288`,
  `n_proposals = 4999`, proposals `b713c423…`, configs `b585b727…`.
- That code is **featurizer v2**: `FEATURIZER_VERSION = "c3_features/v2"` and
  `budget_frac_left = 1 − (b−1)/runs_total` (trial-indexed).

## Which code the replay uses

- Published main at diagnosis: `dc9ad88a64d0430b481661fd78f7bbda4aed19fa` (current remote main; the user-named
  `9f23fea8` was superseded while the diagnosis was running). Its `r1/c3/features.py` is **v3**
  (`FEATURIZER_VERSION = "c3_features/v3"`) with `budget_frac_left = 1 − worker_runs_used/runs_total`
  (R1-SEQ-BUDGET-FIELDS / W2 worker-run budget); on execute-all ledgers v2 and v3 agree, but differ where the sweep-1
  ledger prefix contains control-plane skips, precheck rejections or verify re-runs.
- Replay command used this checkout with its own (unmodified) `r1.c3.dataset.build_from_sweep`, the pinned index
  (`C3_sweep_index_20261028T033315Z.json`, sha `812468e2…`) and classification sidecar (`bb6d891c…`), writing only
  to `/tmp`.

## Diff (proposals only; no label/evaluation value opened)

- sealed proposals sha `b713c423…`; main replay `d0048567…`; both 4,999 lines; **the same 4,999 keys**
  (node, proposal_id), no added/removed proposal.
- **116 records differ; exactly one field differs: `features.budget_frac_left`.**
- Examples of (sealed v2, replay v3): (0.05, 0.4), (0.05, 0.1), (0.15, 0.2), (0.30, 0.35), (0.35, 0.40);
  first differing line 31, `digits_mlp/...:s114:t020`.
- `configs.json` is byte-identical (`b585b727…`); all other fields (including the candidate/incumbent config
  identity, partition-relevant fields and all feature fields except `budget_frac_left`) are equal. The 15 apparent
  extra field diffs are NaN≠NaN artifacts in naive comparison and are not real.
- Source data are identical between the B.2 audit root and the replay checkout (both sweep source dirs byte-identical;
  manifests `f18f8a8b…`/`50530673…`). **This is a code/feature-version difference, not a data difference.**

## Commits on main that changed the replay path since ab79b4ce

All are ancestors of main `dc9ad88a`; all touch `r1/c3/features.py`:

| Commit | Date (CET) | What |
|---|---|---|
| `81924e14` | 2026-11-09 02:26 | W2 budget fields from worker runs (R1-SEQ-BUDGET-FIELDS); `budget_frac_left` becomes worker-run indexed |
| `6b779fe3` | 2026-11-09 02:41 | W2 review round 1; sets `FEATURIZER_VERSION = c3_features/v3`, hidden-result arms |
| `5db5b67d` | 2026-11-09 02:50 | W2 review round 2; validation/wording |
| `3ce2c8b7` | 2026-11-14 11:11 | W2 budget line by worker runs; trackp_prompt/v2 |

(`6e872386` Track P SFT also touches `dataset.py` but does not change these sweep-1 proposal fields.)

## Decision proposal (options and recommendation)

**Option A (recommended): replay with the audit's own builder, under REL-CODE A.** Change only
`r1/c3/release_checks.py` so the sweep-1 integrity check runs `build_from_sweep`/the feature builder at the table's
recorded code commit `ab79b4ce` (pinned, no network; e.g. a reviewed in-repo compatibility builder or a checked-out
builder worktree whose tree hash is pinned), while `release.py`, the table, the audit and the release-row authority
stay unchanged. This preserves the sealed table exactly and verifies it against the code that produced it; it is a
reviewed code change (`REL-CODE A`) and requires an author row/independent review. It is the narrowest fix and does
not relax any data/identity check.

**Option B (not recommended): rebuild the sweep-1 table at current main and re-audit/re-bind.** This would replace the
sealed table and its B.2 audit provenance, cost another audit, and change the very artifact the release row binds.

**Option C (not recommended): add a reviewed field-level exception** excluding `features.budget_frac_left` from the
proposal comparison. It is weaker than A (it admits a known code drift instead of replaying the producing code) and
would need a separate justification for every future featurizer change.

**Recommendation: A**, with the code change reviewed independently before use; until then the sweep-1 train/dev
release stays refused and P.4-LABELS A / P.4 phase-1 remains blocked. No label or evaluation value is released by this
diagnosis.
