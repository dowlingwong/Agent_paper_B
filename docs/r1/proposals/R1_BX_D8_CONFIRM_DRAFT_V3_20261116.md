# Draft for the author: `R1-BX-D8-CONFIRM` binding gate v3 (path B), 16 November 2026

**Draft only; AI-assisted (Claude, Mac agent).** It is not an author decision and is not in `PLAN.md`.
- **Supersedes** `R1_BX_D8_CONFIRM_DRAFT_20261116.md` (S2-M4) as the current draft. That file is kept unchanged, with
  its path A (gate v2) and its path-B template.
- **Authority read from:** `author-decisions-20261116c` @ `65d8d5bb`: R1-BX-D8, R1-BX-PROPOSED-CONFIRM (D8),
  R1-BX-D8-V3-A (items 1–3) and R1-BX-D8-V3-B (items 4–5). R1-BX-D8-V3-B says: "Gate v3 implements items 1–5, is
  independently reviewed, and is bound by R1-BX-D8-CONFIRM's SHA."
- **Analysis lock.** `analysis_guard.require_d8_confirmation` reads only `docs/r1/PLAN.md` §10 at the committed HEAD.
  The R1-BX-D8 lock stays in force until the author commits a matching row.

## 1. The row (path B, filled)

Gate v3 is `r1/c3/gate.py` @ `61e8aed79474d11b477132a36a3356714551db60` on `mac-d8-gate-v3-20261116`, SHA-256
`26de7381e653045594fbb74e88b4263848dc5be7feefff8de9400b56aeb02ed0`. Its review is recorded in
`reviews/M11_D8_GATE_V3_REVIEW_20261116.md`, and its report is `reports/M11_D8_GATE_V3_20261116.md`.

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `61e8aed79474d11b477132a36a3356714551db60`, sha256 `26de7381e653045594fbb74e88b4263848dc5be7feefff8de9400b56aeb02ed0`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

The text is the path-B template of the S2-M4 draft, fixed by the parser; only the commit and the SHA-256 are filled
in. The fence keeps the row inert in this file.

## 2. What the row binds, and what it does not name

- **Bound through the SHA:** every convention in gate v3, including V3-A items 1–3 and V3-B items 4–5:
  - V1n;
  - the train + dev z ≥ 3 eligibility with the dev denominator ≥ δ_n;
  - the declared P3 split and disjoint train, dev and test ids;
  - the (b2) studentized bound with the +∞ screen;
  - the test floor T0 ≥ 9, T1 ≥ 3;
  - the implementation conventions listed in the gate's docstring and in the report's §3, for example +∞ held as
    1e12 as in the simulation, and the ŝe = 0 rule.
- **Not named in the text:** the row's fixed wording says "implements R1-BX-D8 with the numbers confirmed in
  R1-BX-PROPOSED-CONFIRM (D8)" and does not mention V3-A or V3-B. Those rows are already in §10 and say that the
  CONFIRM SHA binds gate v3. Naming them in the row would need a matching change to `analysis_guard.py`'s fixed
  pattern, reviewed separately. This unit does not propose that change.
- **Not bound by the SHA:** the split assignment of instances, which the caller supplies and the analysis
  preregistration fixes (V3-A item 3). The gate checks only that P3 is declared and that the ids are disjoint.

## 3. Conditions before the author commits it

1. **Gate v3 accepted** by its independent review (see §1). If the review changes `gate.py`, the commit and SHA above
   change, and this draft is updated with them. `r1/tests/test_d8_confirm_draft_matches_parser.py` fails while the
   draft's SHA differs from the gate file's.
2. **Gate v3 reaches `main` by merge.** The named commit must be an ancestor of the HEAD that carries the row, with
   the same `gate.py` bytes. Squash, rebase or cherry-pick would give a different commit, and the guard would refuse
   the row. Pushing `main` is the author's decision.
3. **Placement** (the parser's rules, unchanged):
   - a table row in `PLAN.md` under `## 10.`, below a `###` heading with a date and an author marker, for example
     `### <d> November 2026 — C3 gate confirmation (author)`;
   - a header `| ID | Decision |` or `| ID | Author decision |`;
   - the first cell exactly `R1-BX-D8-CONFIRM`, and the second exactly the text above, with no added words;
   - exactly one such row in §10;
   - `PLAN.md` and `gate.py` committed and clean.
4. **Order relative to sweep 2.** The row must be committed before any sweep-2 label table is copied back for analysis
   or read by analysis code (R1-BX-D8). Collection and sealing do not need it.

## 4. Checks

- `r1/tests/test_d8_confirm_draft_matches_parser.py` reads this draft. It checks that the row names the current gate
  SHA and a commit with those bytes, and runs the real guard on the row in a synthetic repository.
- `r1/tests/test_d8_confirm_draft_v3_20261116.py` checks that the row is the S2-M4 path-B template with only the two
  values filled, that the fence keeps it inert, and that the real parser accepts it unfenced.
