# Draft for the author: the `R1-BX-D8-CONFIRM` row — 9 November 2026 (redrafted after review round 1)

**Draft only; AI-assisted. This is not an author decision and is not in `PLAN.md`.** It exists so that, once the gate code has passed independent review, the author can decide whether to confirm it. Nothing in the repository treats this file as authority: `analysis_guard.require_d8_confirmation` reads only `docs/r1/PLAN.md` §10 at the committed HEAD. Do not paste the row before the gate has an *accepted* independent review of the exact bytes named below; if the gate changes, the SHA changes and the row must be redrafted.

## The gate code the row would bind

| Item | Value |
|---|---|
| File | `r1/c3/gate.py` |
| Commit containing these bytes | `fe453fcb463cafb6475cf6bda67caa392128ed64` (branch `mac-m11-d8-20261109`) |
| SHA-256 of `r1/c3/gate.py` | `007a484ca0852fb663ee4a20df653f830388e5ef193a9d02be3e41b8b3d9693c` |
| Git blob of `r1/c3/gate.py` | `2859f38e39db4aad93949978506824c03935b8a8` |

The round-1 draft named commit `421a1c38…` and SHA-256 `a75e08d3…280e`; those bytes are superseded and must not be confirmed.

`gate.py` now contains the whole statistic: the IQM and PoI are inlined (it no longer imports `d8_point_statistics.py`), and the NumPy version (`NUMPY_VERSION = '2.4.4'`), the eight T0 node ids and the three suite names are constants in it, each a STOP on mismatch. For the record only (the parser does not check it): `r1/c3/analysis_guard.py` SHA-256 `b6ef5c3fb4aba3c2050781726c45369100429659371bc2ec086ae9a93bf8f87b` (the authority mechanism, unchanged).

Before confirming, re-check on the analysis checkout: `git show <commit>:r1/c3/gate.py | shasum -a 256` must print the SHA above, and the commit must be an ancestor of the checkout's HEAD (the guard verifies both). **The named commit must survive integration:** merge it, do not squash, rebase or cherry-pick it, or the commit id in the row will not be an ancestor and the guard will refuse. If the gate changes again (for example after the author's answers in the report's "Questions for the author"), the SHA changes and this row must be redrafted.

## What confirming would mean

The row adopts the gate as implemented: the R1-BX-D8 numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8), tier pooling, and the partial-T1 rule (R1-B7-PARTIAL-T1). Because they are code paths or constants in the confirmed file, it also freezes every implementation convention that the PLAN rows left open (`docs/r1/reports/M11_D8_GATE_20261109.md`, "Implementation conventions", items 1–13):

1. seed 20261108 with `numpy.random.Generator(PCG64)`, the documented draw order, and **NumPy pinned to 2.4.4** (any other version STOPs);
2. linear-interpolation percentile lower bounds;
3. Holm ranking: an arm passing at 97.5 % ranks first, then the composite tail share, then A3 before A5 (the verdict cannot depend on arm labels);
4. **STOP on any nonpositive resampled or point test denominator** on an IQM-eligible node, or when no node is eligible. This STOP is likely in practice: the probability is ≈ 0.5 or more with about 10 eligible nodes near 5 test standard errors (report, "Whole-gate STOP probability"; author question Q3);
5. a dev denominator exactly equal to δ_n is eligible;
6. gap closed as a ratio of means over test instances;
7. the fractional-edge 25–75 % IQM (briefing §1 option A);
8. PoI ties by exact floating-point equality;
9. the node layout: T0 = exactly `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion`, with no suite; T1 suites = `autoresearch`, `MLAgentBench`, `MLGym`; any deviation STOPs, including suite-less T1 nodes such as 1GC-7RC dataset tasks; the T1 node list itself is supplied by the caller;
10. **partial T1 as a whole-gate STOP**: a suite without a labelled T1 node STOPs the aggregate gate. The R1-B7-PARTIAL-T1 consequence attaches the condition to leave-one-suite-out; the row text below states it for the gate;
11. δ_n supplied by the caller in the 20-run-scaled utility units of U (D18), not checked;
12. strict input (exact node fields, no duplicate JSON keys, no NaN/Infinity, no overflow-sized values);
13. the executing gate file must be the checked `r1/c3/gate.py`.

Input provenance (utilities, oracle from the label-seed block only, dev/test split, scaling) remains the caller's and is not frozen by this row. The report lists six questions (Q1–Q6) whose answers should come before the row is pasted. From the row on, sweep-2 label tables may be analysed, subject to all other gates.

## Format constraints

The parser accepts the row only if all of these hold:

* it is a table row in `docs/r1/PLAN.md` under `## 10.`, below a `###` heading carrying a valid date and an author marker (e.g. `### 10 November 2026 (author)`), in a table whose header is `| ID | Decision |` or `| ID | Author decision |`;
* the first cell is exactly `R1-BX-D8-CONFIRM` (no date or suffix in that cell). **The 4 Nov template in `AUTHOR_DECISIONS_20261104.md` (`| R1-BX-D8-CONFIRM (date) | …`, with different wording) would be refused: do not paste the template, paste the row below;**
* the second cell is exactly the text below, with no added words;
* there is exactly one such row;
* both `PLAN.md` and `gate.py` are committed and clean, and the named commit is an ancestor of HEAD containing the same `gate.py` bytes.

## The row (for the author to paste only after the review is accepted)

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `fe453fcb463cafb6475cf6bda67caa392128ed64`, sha256 `007a484ca0852fb663ee4a20df653f830388e5ef193a9d02be3e41b8b3d9693c`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. Each suite must have at least one labelled T1 node, otherwise STOP. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

The decision text was checked against the accepted parser: `r1/tests/test_d8_confirm_draft_matches_parser.py` extracts the fenced row above, places it in a synthetic `PLAN.md` in a pytest-owned Git repository together with the gate bytes, and runs the real `require_d8_confirmation`. The test passes only while the draft and the committed gate agree.
