# Paper C measurement (b) — guarded first acceptance

Draft under R1-PAPERC-MEASURE-FIRST and R1-PAPERC-ROWS-CONFIRMED. The proposer is an open
decision in measurement (b). Recommend the Track X pick, `gemma4_31b` with thinking off,
to align this development measurement with the later node relevance screen.

## Pre-declaration

Use `digits_mlp` and `tabular_mlp`. Propose six new roots per node, with at most 20 candidate
worker runs and 80 proposer calls per root. Charge one additional CPU evaluation of the
unedited start configuration at the root's train/split seed. No proposer call is used for
that evaluation. Initialize the published harness's `initial_current_best` with its finite
validation metric. Trial one uses the strict comparison to that incumbent and a tie is
discarded. If a candidate is invalid or fails to improve, the start configuration remains
the incumbent. Subsequent decisions use the existing default strict-improvement rule.

The existing Paper C real instance reservation 50,000–59,999 is fully occupied by the
recorded E-SYN identifier domain. Propose extending the worker/instance reservation for
this unit to 62,000–62,011, inclusive. Assign 62,000–62,005 to digits and 62,006–62,011 to
tabular. Accept this extension in the launch row before using the integers. The run
checks the registry, newer D.3 declarations, and verify-seed interval. Propose ten
fresh joint audit seeds per root starting at 10,901,000, keeping the measurement (a)
block separate. Pair the start and each retained configuration at those fresh seeds.

Record the start measurement, first candidate and decision, charged run and call counts,
each subsequent keep, ledger identity and terminal snapshot. Record audit pairing and
the number of invalid jobs. Report the first acceptance rate and paired terminal gain
versus start, as well as the median increment over retained edges assessed with the
fresh-seed audits. For the stakes reading use σ_d and frozen C1 regret in the same units.
The node meets the stakes floor if median increment is at least 0.5 σ_d or the C1 regret
is at least 0.1 σ_d. The result is development evidence for the node screen.

## Procedure

Build on the harness pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`
under R1-PAPERC-HARNESS-PIN-SET. On deepthought stage the clean paper and harness
checkouts, the reviewed proposer backend and environment, and an isolated output root.
Use up to 16 CPU workers while keeping at least 10 of 40 CPUs free. Verify the
proposer identity and thinking setting before any new calls. Run the baseline
and candidate sequence in separate node copies at the same campaign seed.
Refuse a non-finite start metric, a first ledger comparison against a different
incumbent, a kept tie, or inconsistent charging. Preserve the scene and report a STOP.

Seal the raw root receipts, checked ledgers, retained configuration hashes, paired audit
rows and the summary. Route both measurement reports to the coordinator for R1-PAPERC-CORE.

## Authorization draft

Propose one decision covering the proposer, run and call budgets, seed extension and launch
conditions. Review the exact launch driver and synthetic replay first. The authorized note
needs the launch commit and review, exact seed registry and run spec hashes, proposer revision
and runtime identity, resource limits and sealed output location.

```text
task: local/20261127-19b
approved: false
paper_commit: TODO
spec_sha256: TODO
proposer: TODO
signed_by: TODO
```
