# Paper C measurement (a) — fresh-seed audits of Sweep 1 incumbents

Draft for review and authorization under R1-PAPERC-MEASURE-FIRST and R1-PAPERC-ROWS-CONFIRMED.

## Pre-declaration

Replay all 18 Sweep 1 roots per node and memory mode for `digits_mlp`, `tabular_mlp`,
`openml_credit_approval` and `openml_ionosphere`. Use the index and classification in
R1-SWEEP1-CLASSIFY. Reconstruct the complete sequence of retained configurations, including
the first valid unconditional keep, from recorded start files and the authenticated structured
edits. Use the final incumbent even when it equals the start. If an input root is incomplete
or a kept edit does not replay, stop and retain the input and diagnostics.

Use ten joint train and split seeds per root. Allocate blocks beginning at 10,900,000 from
`paperc_audits`, with the root order fixed by node name and instance seed. Both memory modes
use the same block for the same root. Audit each unique root/configuration pair once. The
start, preceding incumbent, kept candidate and terminal incumbent use matched seeds.
The seed reservation check includes the Paper C registry, Paper B D.3 declarations and the
verify-seed addition. Paper B label and evaluation partitions are outside this launch.

Use the mean of paired validation-metric differences per retained edge and per terminal-versus-start
comparison. Report medians, denominators, missed or invalid audits, and the share of paired
keeps with mean increment at or below zero. Give the first unconditional keep its own stratum.
Report the median recorded-minus-fresh paired gain for subsequent keeps as the winner's-curse
diagnostic. The executed scope cannot estimate missed keeps from unmeasured discarded candidates.
Report memory modes separately. For the node stakes reading, use the frozen C1 median
decision regret and material-edit paired noise from the census, and give the median fresh
increment over post-first retained edges in the same units. The criterion is median retained
increment at least 0.5 σ_d or C1 decision regret at least 0.1 σ_d. Core inclusion depends on
the coordinator's synthesis after both measurements and the remaining relevance conditions.
The OpenML rows serve as descriptive controls.

## Operator procedure

1. From the reviewed Paper B code pin, prepare the plan against the classified Sweep 1 checkout
   with `PYTHONPATH=paperC/src python -m paperc.incumbent_audits prepare --paper "$PAPER" --out "$PLAN"`.
   Record the byte hash, root and job counts, peak scratch estimate and the expected CPU-hours
   in the authorization. Review the pre-declaration, code and tests before signature.
2. Compute stages the Sweep 1 harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` and the
   authenticated OpenML caches used for the Sweep 1 compatibility replay. Verify their
   hashes against the launch note. Use deepthought, at most 16 workers, and keep at least 10
   of 40 logical CPUs free. Record the host, dependency freeze, CPU occupancy, cache paths
   and file hashes before running. Give the attempt fresh scratch and output paths.
3. After publication of the signed note on `origin/main`, from the exact clean code commit
   run `PYTHONPATH=paperC/src python -m paperc.incumbent_audits run --paper "$PAPER" --plan "$PLAN" --scratch "$SCRATCH" --out "$OUT"`.
   Seal the plan, per-attempt rows, summary, host/runtime record and checksums. An invalid
   seed result or incomplete audit is a STOP with the raw scene preserved. Report actual
   compute and the next decision to the coordinator.

## Authorization note draft

The coordinator renders the signed note at `docs/r1/authorizations/paperc_measure_a_20261127.md`
once the exact plan, code and environment have accepted reviews. PLAN §10 binds the note before launch.

```text
task: local/20261127-19a
approved: false
paper_commit: TODO
plan_sha256: TODO
workers: TODO
signed_by: TODO
```
