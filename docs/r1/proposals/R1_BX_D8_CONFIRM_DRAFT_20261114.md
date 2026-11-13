# Draft for the author: the `R1-BX-D8-CONFIRM` row — 14 November 2026 (gate v2 after the author's answers to Q1–Q5)

**Draft only; AI-assisted. This is not an author decision and is not in `PLAN.md`.** It follows the author's answers to the 10 November questions Q1–Q5, given in the start message of 13 November; it supersedes `R1_BX_D8_CONFIRM_DRAFT_20261109.md`. It exists so that, once the gate code has passed independent review, the author can decide whether to confirm it. Nothing in the repository treats this file as authority: `analysis_guard.require_d8_confirmation` reads only `docs/r1/PLAN.md` §10 at the committed HEAD. Do not paste the row before the gate has an *accepted* independent review of the exact bytes named below; if the gate changes, the SHA changes and the row must be redrafted.

## The gate code the row would bind

| Item | Value |
|---|---|
| File | `r1/c3/gate.py` |
| Commit containing these bytes | `da264a40f929b114f7090da9d618402e74d94e3a` (branch `mac-m11-d8-v2-20261114`) |
| SHA-256 of `r1/c3/gate.py` | `02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873` |
| Git blob of `r1/c3/gate.py` | `232a2835feea785b77232261032d34c3d6dff060` |

Earlier drafts are superseded and must not be confirmed: commit `421a1c38…` / SHA-256 `a75e08d3…280e` (9 Nov, round 1), commit `fe453fcb…` / SHA-256 `007a484c…693c` (9 Nov, round 2) and commit `050cb9f0…` / SHA-256 `a078cf1f…6acd` (the accepted 9 Nov gate, `R1_BX_D8_CONFIRM_DRAFT_20261109.md`, before the author's answers).

`gate.py` now contains the whole statistic: the IQM and PoI are inlined (it no longer imports `d8_point_statistics.py`), and the NumPy version (`NUMPY_VERSION = '2.4.4'`), the eight T0 node ids and the three suite names are constants in it, each a STOP on mismatch. For the record only (the parser does not check it): `r1/c3/analysis_guard.py` SHA-256 `2f6a720e5f85a0f887f36f4ac367c8d77a2a036ae4a0e9127ac7e5046f61d213`. It **changed** in this version: its row pattern carries the new partial-T1 sentence below; nothing else in it changed.

Before confirming, re-check on the analysis checkout: `git show <commit>:r1/c3/gate.py | shasum -a 256` must print the SHA above, and the commit must be an ancestor of the checkout's HEAD (the guard verifies both). **The named commit must survive integration:** merge it, do not squash, rebase or cherry-pick it, or the commit id in the row will not be an ancestor and the guard will refuse. If the gate changes again (for example after the author answers the open question on Q4), the SHA changes and this row must be redrafted.

## What confirming would mean

The row adopts the gate as implemented: the R1-BX-D8 numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8), tier pooling, and the partial-T1 rule (R1-B7-PARTIAL-T1) for leave-one-suite-out. Because they are code paths or constants in the confirmed file, it also freezes every implementation convention that the PLAN rows left open (`docs/r1/reports/M11_D8_GATE_20261109.md`, "Implementation conventions", items 1–13, as changed by `docs/r1/reports/M11_D8_GATE_V2_20261114.md`; items 14–15 are new):

1. seed 20261108 with `numpy.random.Generator(PCG64)`, the documented draw order, and **NumPy pinned to 2.4.4** (any other version STOPs); the named environment is the harness `uv.lock` environment at `a3fedbb` (Python 3.13, NumPy 2.4.4), recorded but not checked beyond NumPy;
2. linear-interpolation percentile lower bounds;
3. Holm ranking: an arm passing at 97.5 % ranks first, then the composite tail share, then A3 before A5 (the verdict cannot depend on arm labels);
4. **STOP on any nonpositive resampled or point test denominator** on an IQM-eligible node, or when no node is eligible. With the dev-z rule (item 14) and split sizes the plans allow (2–6 dev, 2–6 test instances), it falls to about 0.2 for 10 nodes at 5 test SE, mainly because about half the nodes are excluded almost regardless of their signal (v2 report §3);
5. a dev denominator exactly equal to δ_n is eligible (on that criterion);
6. gap closed as a ratio of means over test instances;
7. the fractional-edge 25–75 % IQM (briefing §1 option A);
8. PoI ties by exact floating-point equality;
9. the node layout: T0 = exactly the authorized sweep-1 set `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_climate` (climate substitutes for blood_transfusion, which failed D21: R1-DT-PIN-SWEEP1, `authorizations/c3_sweep1_20261027.md`, R1-D28-REPAIR), with no suite; T1 suites = `autoresearch`, `MLAgentBench`, `MLGym`; any deviation STOPs, including suite-less T1 nodes such as 1GC-7RC dataset tasks; the T1 node list itself is supplied by the caller;
10. **partial T1 for leave-one-suite-out only**: a suite without a labelled T1 node does **not** STOP the aggregate gate; the gate reports `t1_by_suite` and `t1_suites_without_labelled_node`. The per-suite condition is a precondition of each leave-one-suite-out fold and is applied where leave-one-suite-out is computed (no such code exists yet);
11. δ_n supplied by the caller in the 20-run-scaled utility units of U (D18), not checked;
12. strict input (exact node fields, no duplicate JSON keys, no NaN/Infinity, no overflow-sized values; an infinite gap closed fails closed with `ValueError`);
13. the executing gate file must be the checked `r1/c3/gate.py`;
14. **dev-z eligibility**: a node is IQM-eligible only if its dev denominator ≥ δ_n **and** its paired dev z ≥ 6, with d = oracle − A2 per dev instance and dev_z = mean(d) / (sd(d, ddof = 1) / √n_dev), with dev A2 and dev oracle paired by position (the caller's order; the dev split has no instance ids); n_dev < 2 is ineligible; sd(d) = 0 is eligible on this criterion only if mean(d) > 0; dev_z = 6 is eligible. Ineligible nodes are excluded from the IQM, kept in the PoI, and listed with their reasons (`delta_n`, `dev_z`, `dev_n`);
15. **no minimum number of test instances per node** (the Q4 STOP is not implemented: the plans give T1 nodes about 12 instances or fewer, so no node can reach 10 test instances; open question).

The row text names neither the dev-z rule nor the absence of a test minimum: both are bound only through the gate SHA (question list, D8-ROW).

Input provenance (utilities, oracle from the label-seed block only, dev/test split, scaling) remains the caller's and is not frozen by this row. Before pasting, the author should settle the open Q4 question (minimum test instances per node) in the v2 report; if it leads to a code change, this row is redrafted. From the row on, sweep-2 label tables may be analysed, subject to all other gates.

## Format constraints

The parser accepts the row only if all of these hold:

* it is a table row in `docs/r1/PLAN.md` under `## 10.`, below a `###` heading carrying a valid date and an author marker (e.g. `### 10 November 2026 (author)`), in a table whose header is `| ID | Decision |` or `| ID | Author decision |`;
* the first cell is exactly `R1-BX-D8-CONFIRM` (no date or suffix in that cell). **The 4 Nov template in `AUTHOR_DECISIONS_20261104.md` (`| R1-BX-D8-CONFIRM (date) | …`, with different wording) would be refused: do not paste the template, paste the row below;**
* the second cell is exactly the text below, with no added words;
* there is exactly one such row;
* the partial-T1 sentence is the new one; the 9 Nov wording ("Each suite must have at least one labelled T1 node, otherwise STOP.") is refused by the changed parser;
* both `PLAN.md` and `gate.py` are committed and clean, and the named commit is an ancestor of HEAD containing the same `gate.py` bytes.

## The row (for the author to paste only after the review is accepted)

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `da264a40f929b114f7090da9d618402e74d94e3a`, sha256 `02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

The decision text was checked against the accepted parser: `r1/tests/test_d8_confirm_draft_matches_parser.py` extracts the fenced row above, places it in a synthetic `PLAN.md` in a pytest-owned Git repository together with the gate bytes, and runs the real `require_d8_confirmation`. The test passes only while the draft and the committed gate agree.
