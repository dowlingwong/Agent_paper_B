# Draft for the author: the `R1-BX-D8-CONFIRM` row — 9 November 2026

**Draft only; AI-assisted. This is not an author decision and is not in `PLAN.md`.** It exists so that, once the gate code has passed independent review, the author can decide whether to confirm it. Nothing in the repository treats this file as authority: `analysis_guard.require_d8_confirmation` reads only `docs/r1/PLAN.md` §10 at the committed HEAD. Do not paste the row before the gate has an *accepted* independent review of the exact bytes named below; if the gate changes, the SHA changes and the row must be redrafted.

## The gate code the row would bind

| Item | Value |
|---|---|
| File | `r1/c3/gate.py` |
| Commit containing these bytes | `421a1c38358c011c01292300a99d9081b945a9b0` (branch `mac-m11-d8-20261109`) |
| SHA-256 of `r1/c3/gate.py` | `a75e08d30949ef1122f0eb0fa78644678c92ef60952149f95b2906745458280e` |
| Git blob of `r1/c3/gate.py` | `f23557e1df716327fa0743a7fe4097c0b9051d84` |

For the record only (the parser does not check these): `r1/c3/d8_point_statistics.py` SHA-256 `0c90702e4d7ac17da258eeeaec2d392e55c24cb116f1a604c23f61fea617c8bb`, `r1/c3/analysis_guard.py` SHA-256 `b6ef5c3fb4aba3c2050781726c45369100429659371bc2ec086ae9a93bf8f87b`, NumPy 2.5.3 in the test environment of 9 Nov.

Before confirming, re-check on the analysis checkout: `git show <commit>:r1/c3/gate.py | shasum -a 256` must print the SHA above, and the commit must be an ancestor of the checkout's HEAD (the guard verifies both).

## What confirming would mean

The row adopts the gate as implemented: the R1-BX-D8 numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8), tier pooling, and the partial-T1 rule (R1-B7-PARTIAL-T1). It also fixes the implementation conventions that the PLAN rows left open, because they are constants in the confirmed file: seed 20261108 with NumPy PCG64, linear percentile lower bounds, arm ranking by composite percentile p-value with ties A3 then A5, and STOP on any nonpositive resampled oracle denominator (`docs/r1/reports/M11_D8_GATE_20261109.md`, "Implementation conventions"). From the row on, sweep-2 label tables may be analysed, subject to all other gates.

## Format constraints

The parser accepts the row only if all of these hold:

* it is a table row in `docs/r1/PLAN.md` under `## 10.`, below a `###` heading carrying a valid date and an author marker (e.g. `### 10 November 2026 (author)`), in a table whose header is `| ID | Decision |` or `| ID | Author decision |`;
* the first cell is exactly `R1-BX-D8-CONFIRM` (no date or suffix in that cell);
* the second cell is exactly the text below, with no added words;
* there is exactly one such row;
* both `PLAN.md` and `gate.py` are committed and clean, and the named commit is an ancestor of HEAD containing the same `gate.py` bytes.

## The row (for the author to paste only after the review is accepted)

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `421a1c38358c011c01292300a99d9081b945a9b0`, sha256 `a75e08d30949ef1122f0eb0fa78644678c92ef60952149f95b2906745458280e`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. Each suite must have at least one labelled T1 node, otherwise STOP. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

The decision text was checked against the accepted parser: `r1/tests/test_d8_confirm_draft_matches_parser.py` extracts the fenced row above, places it in a synthetic `PLAN.md` in a pytest-owned Git repository together with the gate bytes, and runs the real `require_d8_confirmation`. The test passes only while the draft and the committed gate agree.
