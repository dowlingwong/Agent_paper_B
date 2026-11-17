# Track P SFT — cross-split duplicate rule R1-TRACKP-SFT-DUP, 17 Nov 2026

**Authority.** PLAN `R1-TRACKP-SFT-DUP` (`main` = `50176481`): held-out val and test exclude the duplicates of the
training set as the **primary** result; the full held-out populations, duplicates included, are reported as the
**secondary** result; pilot sizes train 1,176 / val 47 / test 74 of 262 labelled test proposals; sweep 2 uses the
same rule. Earlier unit: `docs/r1/reports/TRACKP_SFT_DEV_20261117.md` §3 (1). AI-assisted (Claude);
**ENGINEERING_ONLY** — nothing here is evidence.

**Branch.** `mac-trackp-sft-dup-20261117`, from `main` = `50176481`.

## 1. What changed

| piece | change |
|---|---|
| `r1/c3/train/sft_data.py` | new policy `heldout_excludes_seen` (`DECIDED_DUPLICATE_POLICY`), the default; the two earlier policies (`drop_from_train`, `exclude_from_heldout`) are refused unless the label source is synthetic; val rows whose (node, incumbent, candidate) key occurs on a train instance are written with split `val_seen` instead of being dropped; `splits.json` gains `cross_split_duplicates` and `heldout_populations` and lists the test proposals the primary test population leaves out; manifest counts gain `val_seen` and `val_full`; `load_sft_data(..., secondary=True)` also returns the `val_seen` rows (default call unchanged: train and primary val) |
| `r1/c3/train/sft.py` | `run_stage_s(..., val_secondary=...)`: early stopping, temperature and the `selected` metrics use the primary val rows only; with secondary rows the report adds `selected_full_heldout` and `selected_full_heldout_temperature_scaled` (primary + `val_seen`, same checkpoint, same temperature), `n_val_secondary_only`, `heldout_rule`, and saves `pred_val_seen_logits.npy` |
| `r1/scripts/trackp.py` | `sft-dev` loads the secondary rows and passes them, and the data's policy, to the runner |
| (review round 1, M1) | `load_sft_data` reads the data's policy from `splits.json` (absent = the earlier default `drop_from_train`) and refuses any policy but the decided one unless the labels are synthetic; the Stage S report records `cross_split_duplicates` and writes `heldout_rule` only for the decided policy |
| `r1/scripts/configs/trackp_sft.json` | `cross_split_duplicates: heldout_excludes_seen`, with the rule as a comment |

**The rule as implemented.**

- Train: every labelled row of a train instance (no drops).
- Val, primary: rows of val instances whose key does not occur on any train instance. Used for early stopping,
  temperature scaling and lr selection (`select_lr` reads the best primary val RPS).
- Val, secondary: all labelled rows of val instances (primary + `val_seen`). Reported only.
- Test, primary: test proposals whose key occurs on no train **and no val** instance. Val is used for selection, so a
  test pair seen on a val instance is not unseen either; this reading also gives the decision's 74 of 262.
- Test, secondary: every proposal of the test instances.
- Test instances still contribute no row to the data directory; `splits.json` carries their names and the excluded
  proposal ids. No test evaluator exists yet (P.4 is a later unit); it must read the list for the primary number and
  use all test proposals for the secondary one.

`selected` keeps its meaning (primary val), so `select_lr` and earlier report readers are unchanged.

## 2. Verification

- `r1/tests/test_trackp_sft.py` + `r1/tests/test_trackp_cli.py`: 34 passed, 9 skipped (CPU, torch 2.6.0, Python 3.12);
  after review round 1: 35 passed, 9 skipped (load-time policy refusal, also through `sft-dev`; stronger
  equality of runs with and without the secondary rows).
  New tests: the decided policy (every train row kept, primary val free of train keys, `val_seen` ⊆ train keys,
  counts and test exclusion list equal to `exclude_from_heldout`, `splits.json` fields, both `load_sft_data` forms);
  refusal of the two earlier policies with a real label block; Stage S with secondary rows (selection on primary val
  only, the secondary metric keys, `pred_val_seen_logits.npy`, and the primary metrics identical to a run without
  secondary rows). The two tests that check `drop_from_train` behaviour now ask for it explicitly.
- Full `r1/tests` suite: see §4.
- **Real-ledger smoke (ENGINEERING; synthetic labels, whitespace token counter).** `sft-data` logic on the sweep-1
  `c3_features/v3` table (the same table and replay as the earlier unit's smoke), with the config's splits block:

  | count | value |
  |---|---|
  | labelled (eligible) proposals | 1,725 |
  | train rows | **1,176** |
  | val rows, primary | **47** |
  | val rows seen on a train instance (`val_seen`) | 240 |
  | val rows, full (secondary) | 287 |
  | labelled test proposals (secondary) | 262 |
  | of which the pair occurs on a train/val instance | 188 → primary labelled test **74** |
  | test-instance table rows listed as seen (all rows, labelled or not) | 674 |

  These reproduce the decision's sizes. A hash-bag Stage S run of 370 steps on CPU completed; its primary `selected`
  metrics are identical to the earlier unit's `exclude_from_heldout` smoke (same rows, same seed), and the report
  carries the secondary full-val metrics next to them. None of these numbers is evidence.

## 3. Points for the author

1. **"Seen" for test includes val.** The PLAN row says "duplicates of the training set"; the code also excludes test
   pairs that occur on a val instance, because val selects the checkpoint, temperature and lr. Only this reading
   reproduces the decision's 74; with train only, the primary labelled test population would be 77 (review round 1).
   If only train should count, it is a one-line change (`seen = keys["train"]`).
2. **No test evaluator yet.** The exclusion list is written but only a future P.4 evaluator will apply it.
3. **lr selection uses primary val only.** The secondary full-val metric is never used to select anything.
4. **"Seen" uses every table row of a train/val instance**, labelled or not; on sweep 1 this gives the same
   populations as labelled rows only (47 / 74); on sweep 2 the two could in principle differ.

## 4. Full suite

Full `r1/tests` (Python 3.12 / torch 2.6 environment) at `11599ae6`: 54 failed, 2,541 passed, 195 skipped; on base
`50176481` in the same environment: 54 failed, 2,538 passed, 195 skipped — the same 54 failing tests (no Qwen3.5
classes in transformers 4.49, no Hugging Face access); no new failure. With the round-1 fixes (`480031a7`): 54 failed,
2,542 passed, 195 skipped, the same 54 failing tests.
