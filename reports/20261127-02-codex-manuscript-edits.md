# writer/20261127-02 — manuscript readings, budget accounting and G.5 soft targets

**Delivered, Tier D.** Base `6aee0eb34a9c8bae4c9c24d93b261d24a76a8403`. Task branch
`writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae`.
The merge-tree check against published main `6aee0eb3` was clean.

## Result

1. At the matched worker-run and manager-call caps, the campaign comparison asks how much each control decision changes fresh-seed audited gain. The results point to the component contrasts and their intervals. The budget curve gives the mean and count of campaigns reaching each checkpoint, per arm and node in the method.
2. The templates report a supported campaign gain alongside an offline non-pass, with per-node agreement, estimates, intervals and design power. A one-step gain with no demonstrated campaign benefit over A2 is worded as such. The A2–A0 interval and any supported loss are reported under the no-gain reading.
3. The component-contrast prompt uses favourable Holm decisions for attribution and calls for the uncertainty in the one-step contrast when only the rule layer shows a gain. The signed attribution and gate-STOP branches are retained.
4. The method and deviations record R1-G5-TAILS-CONSUMERS: all T1 soft targets use each node's declared distribution, with Student-t scale matched to its declared standard deviation. The unfilled declarations, release references and measured effects stay in placeholders.
5. Adopted from `dc453c2bdafeff5f970ffac7de8d626064d90bd0`: qualify the strength of the outcome wording, show both budget caps and report the curve denominators. Left out the extra “practically meaningful” decision threshold, the replacement of the existing reading switches and the removal of the signed offline–online finding. Kept the original claim scope and the declared contrast families.

No evidence read or job submission was needed. Decided alone: put the T1 target detail in the methods appendix and the deviations table, keep the main-text attribution prompt short, and use temporary Git metadata and build directories because the assigned checkout's Git metadata is write-restricted.

## Builds, tests and review

| Published branch file | Build | SHA-256 |
|---|---|---|
| `papers/r1/build/main_draft_gate_not_passed.pdf` | rc 0, main text ends on p. 8, 44 total pages | `ba8a47f830fb0246a0cbd0f2cd7b08215033171d529d6a6b76956340bc92d27e` |
| `papers/r1/build/main_draft_gate_passed.pdf` | rc 0, main text ends on p. 8, 43 total pages | `36059705e89c2a7ba934db9bbcfc46db36902b0a8180467c0064fe4d08784b96` |

Both `latexmk -pdf` builds were visually checked at the p. 8 transition. The changed results table, budget figure and soft-target text were rendered and checked. No undefined citations, undefined references, duplicate labels or new overfull lines. The gate-STOP preview built at 38 pages. The rule-layer-only with gate-pass preview built at 43 pages and showed both the de-duplication clause and the offline reading. The final build guard stopped at the unresolved gate switch. `git diff --check` passed. The task changes LaTeX and PDFs only.

Fresh independent Codex agent review **ACCEPTED on re-check** of the four LaTeX source files in the branch. First pass requested retaining the signed difference in the offline and campaign decisions. The re-check confirmed that wording, the signed attribution and STOP cases, budget caps, curve denominators, T1 target scope and preserved evidence placeholders. The writer checked the PDFs.

## Next

Coordinator can merge this branch. At queue `9cb5093c` the other writer cards are already on main, including
`writer/20261126-02` with the restructure. Result tables remain pending released D.3 and gate outputs and the
applicable C1 release. The offline gate waits for G.5 labels and T1 train/dev release, reviewed target consumers and
preregistration bindings, trained and calibrated frozen arms and the test release. D.3 waits for screening,
reviewed constants and runner work, frozen rev 4 and the authorised per-arm smoke. D.3b also waits for frozen arms.

Compute's last report (`372d2099`) had ETTh1 sealed and the TASL-2 expansion jobs MetaMaze PID 106579, Forest
Cover 106573 and Titanic 106578 still running. Houseprice waiter PID 208315 timed out before any run and awaits
the 0–7 leases. H200 request `760065` was idle. The queue routes Ada preparation to `compute/20261127-13`,
the D.3 engineering preflight to `compute/20261127-12` and the screening smoke repeat to
`compute/20261127-14`. Check the corresponding reports for launch IDs and status next round.
