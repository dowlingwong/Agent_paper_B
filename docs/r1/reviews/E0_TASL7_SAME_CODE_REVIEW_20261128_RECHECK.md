# Verdict: CHANGES REQUIRED

Recheck of task `compute/20261128-01`, PLAN row `R1-P4-E0-SAME-CODE-REFERENCE`.
Rechecked tip: `compute-p5-tasl7-e0-20261128` @ `1d2153bdf18a97fdaa63020ceabe08131959add9` (one new commit on
top of the previously reviewed `e611835b5a1e237f0a1aa924fb8d63ec14235f81`; base `a98d2eff1d2847e34f00effe66b53bc00467e936`).
Independent, read-only recheck in a fresh detached worktree at
`/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/e0tasl7review/recheck/tip`; no host login, no
run, no GPU job, no label read. This file is a new commit on the existing review branch; the earlier review is
`docs/r1/reviews/E0_TASL7_SAME_CODE_REVIEW_20261128.md`.

## Bottom line

Required findings 1 and 2 are correctly fixed: `gpu_lease.jsonl` is now committed and `SHA256SUMS` verifies for
every listed file, and `comparison_e0e.json` now has correctly oriented `reference_ada` / `candidate_tasl7` keys
with unchanged numbers. The wording fixes for findings 3–6 are accurate. **One new factual error was introduced by
the relabel: the record's "Files" section still cites `comparison_e0e.json` as `46805e6c…`, but the relabelled file
is now `715248d7…` and `SHA256SUMS` carries the new hash.** That is a one-line record fix. The scientific result
and the STOP are unchanged.

## 1. Branch scope, 12 files and the checksum file

`git diff --name-status e611835b..1d2153bd` is exactly four entries and nothing outside the record directory:

```
M  docs/r1/reports/trackp_p5_tasl7_20261128/E0_TASL7_SAME_CODE_20261128.md
M  docs/r1/reports/trackp_p5_tasl7_20261128/SHA256SUMS
M  docs/r1/reports/trackp_p5_tasl7_20261128/comparison_e0e.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/gpu_lease.jsonl
```

`git diff --name-status a98d2eff..1d2153bd` is 12 additions, all under
`docs/r1/reports/trackp_p5_tasl7_20261128/`; no code, config, `.gitignore` or other repository file changed.
`git diff --check a98d2eff..1d2153bd` exits 0.

The record directory now has exactly 12 tracked files. `shasum -a 256 -c SHA256SUMS` in that directory exits **0**
and reports `OK` for all 11 listed files (the twelfth file is `SHA256SUMS` itself, which it does not list):

```
ada_reference_e0e_report.json: OK          e0e_report.json: OK
comparison_e0e.json: OK                    gpu_after.txt: OK
comparison_existing_comparator.json: OK    gpu_before.txt: OK
e0_config_ref_tasl7.json: OK               gpu_lease.jsonl: OK
E0_TASL7_SAME_CODE_20261128.md: OK         p5_compare_ada.py: OK
e0e_manifest.json: OK
```

`gpu_lease.jsonl` is committed with sha256
`f71fa1e50cd8141e074a5a92e563f8737f19a5ef0ff4edc1b2032d69fdfe4114`, the hash the previous review found in the
author's worktree and the hash `SHA256SUMS` lists. Its two lines are the expected `start` at `2026-11-28T00:11:43Z`
and `end` at `2026-11-28T00:40:07Z`, card 0, UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, both with
`other_processes {count: 0, memory_mib: 0}`, matching the manifest's `gpu_lease` array. **Finding 1 is closed.**

## 2. `comparison_e0e.json` labels and numbers

The new diff against `e611835b` changes only the descriptive key names (`ada -> candidate_tasl7`,
`reference -> reference_ada`); no numeric value changes. I remapped the keys of
`comparison_existing_comparator.json` (`ada -> candidate_tasl7`, `reference -> reference_ada`) and compared the
whole objects: `criteria` exact-equal **True**, `descriptive` exact-equal **True**, `equivalent` `false` in both.

The orientation is now correct:

- `descriptive["lora.best_step"] = {"candidate_tasl7": 1800, "reference_ada": 1900}` — TASL-7 is 1800, Ada is
  1900, matching the reports.
- `descriptive["head_fit.test"]["candidate_tasl7"]["rps"] = 0.017788195808623557` (TASL-7) and
  `…["reference_ada"]["rps"] = 0.01691933993296356` (Ada), matching `e0e_report.json` and the Ada report.

Re-running the existing comparator still gives exit status **1** and an output byte-identical to
`comparison_existing_comparator.json` (sha256 `e85aa0032e075edf7931806622e39bd588b65052a963576f5e8278519387b58c`).
The criteria are unchanged: width delta `+0.0021793164792374142` (pass, 0.05 abs), mean delta
`−0.0014910816855873144` (pass, 0.05 abs), RPS relative `0.1909135626876941` (fail, 0.10 rel).

**Required residue.** The record's "Files" paragraph (line 72) still says
`comparison_e0e.json` "(same numbers, reference/candidate labels corrected, `46805e6c…`)". The relabelled file's
actual sha256 is `715248d7870a0a90075be5caf50f97fc1beb799793fadc90b844a7f87d54120e`; `SHA256SUMS` line 2 carries
`715248d7…`. The `46805e6c…` value is the pre-relabel hash at `e611835b`. The prose hash and the checksum file now
disagree. Replace `46805e6c…` with `715248d7…` (the only occurrence in the record directory). This is a factual
error in the record, so the recheck cannot be accepted until it is corrected.

## 3. Corrected wording

- **Three config leaves.** Verified by flattening both files: `e0_config_ref_tasl7.json` differs from
  `r1/scripts/configs/trackp_portal.json` at exactly `comment`, `e0.final.max_steps 6000 -> 2000`, and
  `e0.final.patience 10 -> 5`. The record now states all three; accurate.
- **E0 recipe identical.** `e0`, `head_lr`, `lora`, `lr_grid`, `token_lr` and the Kev adapter/base revisions are
  still exactly equal to `docs/r1/reports/trackp_p5_ada_20261127/e0_config_ref.json`; accurate.
- **Stale `host` descriptor.** The config's `host` field does still read "TASL-2 (zhixu portal)" because it is
  inherited from `trackp_portal.json`; the manifest records hostname TASL-7 and the lease records the matching
  card UUID. The record now says exactly this; accurate (with the caveat in finding 3 below).
- **Tolerance arithmetic.** `10 % × 1.4383536969300546e-4 = 1.4383536969300548e-5`, and the observed gap is
  `2.7460122868593255e-5`. The record's "1.438e-5 absolute" tolerance and "2.746e-5 absolute" observed gap are
  correct.
- **Python version.** The record now says TASL-7 `3.12.15` and Ada `3.12.10`. The Ada value is from the Ada
  record; the TASL value is from the pinned config's `venv.python` (`/home/dowling/r1_trackp/venvs/trackp-gpu`,
  `3.12.15`), not from an independent runtime probe. The required torch/transformers/peft pins still match.

## 4. STOP unchanged

The result table is unchanged: `width_slope_vs_label` 0.902956 (Ada) vs 0.905136 (TASL-7), `mean_slope`
1.014162 vs 1.012671, `rps` 1.438354e-4 vs 1.163752e-4, `equivalent: false`, exit 1. The record still says no
tolerance was widened, the reference was not changed, no better-value re-run was substituted, and the run is not a
parity timing carry-forward. The lease span is still 28 min 24 s (1,704 s = 0.4733 GPU-h). The STOP disposition is
unchanged.

## Residual observations

1. **Required — stale hash (above).** Update `46805e6c…` to `715248d7…` in the record's Files paragraph.
2. **Minor — `sft` is not a host/runtime/directory field.** The record says the other differing fields are
   "host/runtime and directory fields (`sft`, `venv`, `image`, `direct`, lease, paths)". The `sft` block is a
   training configuration block (unused by E0), not a host/runtime or directory field. The substantive claim
   ("not the E0 recipe") is correct; suggest "host/launcher/runtime and directory fields, plus the unused `sft`
   block".
3. **Observation — the lease identifies the card, not the hostname.** The record says "the manifest and the lease
   record TASL-7". The lease records `gpu_uuid GPU-ab72fb4a-…`, which matches the manifest's TASL-7 card; the
   hostname comes from the manifest, not the lease. Acceptable shorthand, but precise wording is "the lease
   records the same card UUID as the TASL-7 manifest".
4. **Observation — "empty card".** The captures show 44 MiB total idle device use, not 0 MiB; the zero is
   foreign-process memory, which the record qualifies correctly. No change needed.

## STOP disposition

**The RPS criterion remains a real STOP: 1.163752e-4 vs Ada 1.438354e-4 is 19.09 % below, against a 10 % relative
tolerance, so `equivalent: false` and the Ada phase-1 note's `ada_smoke_e0` line and A5 SFT remain gated; no
tolerance, reference or result may be changed to turn the miss into a pass.**

## Limits

- No host access; the manifest, report, lease, config, comparator and comparison were verified from the committed
  copies only. The training was not re-run; only the comparator was re-run.
- The TASL-7 Python version is taken from the pinned config, not from a runtime capture.
