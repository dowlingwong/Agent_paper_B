# Draft for the author: `R1-BX-D8-CONFIRM` after D8-TEST and D8-SKEW (16 November 2026)

**Draft only; AI-assisted (Claude, Mac agent).** This is unit S2-M4 of the sweep-2 work plan
(`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`). It is not an author decision and is not in `PLAN.md`.
- **Supersedes:** `R1_BX_D8_CONFIRM_DRAFT_20261114.md` as the current draft. That file is kept, and its row is
  reproduced unchanged as path A below.
- **Authority read from:** `author-sweephost-20261116` @ `fd275c53`.
- **Analysis lock:** `analysis_guard.require_d8_confirmation` reads only `docs/r1/PLAN.md` §10 at the committed
  HEAD. The lock (R1-BX-D8) stays in force until the author commits a matching row.

## 1. Where things stand

The 14 Nov draft binds **gate v2**:
- `r1/c3/gate.py` @ `da264a40f929b114f7090da9d618402e74d94e3a`;
- SHA-256 `02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873`;
- unchanged on every later M11 branch;
- `da264a40` is an ancestor of the S2-M2 integration branch `int-main-sweep2-20261116`, so a row naming it would
  pass the guard's ancestry check on a `main` that took that branch.

Since then, two accepted synthetic units bear on the v2 conventions. The row does not name these conventions, but its
SHA binds them:

| Convention in gate v2 (14 Nov draft, items) | Finding | Recommendation (for the author) |
|---|---|---|
| Item 4: STOP on any nonpositive point **or resampled** test denominator on an eligible node | D8-TEST (`reports/M11_D8_TEST_SIDE_20261115.md`, accepted at `1d34de18`): this STOP fires often with 2–9 test instances and costs power | **V1n**: STOP only on a nonpositive point denominator; a nonpositive resampled node denominator sets that node's G\* = −∞ before the IQM |
| Item 14: eligibility = dev denominator ≥ δ_n **and** dev z ≥ 6 | **Author, 14 Nov:** "D8：暂不确认。Q2 的 dev z ≥ 6 … 不采用为最终规则" (D8 not confirmed for now; dev z ≥ 6 not adopted as the final rule). The author asked for alternatives: (i) train + dev instances, (ii) a D21 σ_node threshold (`reports/M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md`) | **R1**, alternative (i): paired z of d on **train + dev** ≥ 3 (δ_n kept, non-binding in the simulations). R2, alternative (ii), was found not calibratable until σ_node is on the instance scale |
| Split sizes (not in the gate; the caller supplies them) | D8-TEST | lean **P3 = 1/3 : 1/6 : 1/2**; keep P2 = 1/2 : 1/6 : 1/3 if Track P training instances bind |
| Item 2: percentile bootstrap lower bound of the IQM (pass rule (a)) | D8-SKEW (`reports/M11_D8_SKEW_20261115.md`, accepted at `4d87d9c8`; simulated **with V1n and train + dev z ≥ 3**, not with v2's settings). Under left-skewed data (a) false-passes up to 0.24 per arm, and the PoI conjunct gives no protection. Under the declared rule only the studentized (b2) is calibrated, because of its +∞ screen, at mean two-arm power 0.29. The numerator t-test (c) is closest among the rest (≤ 0.083 per arm) at power 0.84. Under symmetric noise the PoI conjunct is what keeps (b1) and (d), and partly (a), calibrated | the author's choice: (b2) as declared, (c), or a further declared unit (D8-SKEW report §4) |
| Item 15: no minimum test instances per node (Q4) | **Author, 14 Nov: Q4 "d→c"**: first fix the train/dev/test proportions, then set a per-tier minimum the plans can reach | per-tier floors tied to the split (D8-TEST §4): P3 T0 ≥ 9, T1 ≥ 6 (≈ 12 instances per node) or ≥ 3 (≈ 6); P2 T0 ≥ 6, T1 ≥ 4 or ≥ 2. A floor is gate code, so it belongs in v3 |

## 2. The author's two paths

### Path A: confirm gate v2 as it is (reverses the author's 14 Nov ruling)

The row below is the 14 Nov row, unchanged. It is kept so that the row mechanics stay checked, but **confirming it
would reverse the author's 14 Nov ruling**: "D8 not confirmed for now; dev z ≥ 6 not adopted as the final rule". It
also leaves Q4's chosen per-tier floor ("d→c") unimplemented.

It would adopt every v2 convention: the resampled-denominator STOP, dev z ≥ 6, no test floor and the percentile rule.
The disclosures it would then need:
- its STOP rate at small test sizes (D8-TEST);
- the skew false-pass risk. D8-SKEW measured this only under V1n and train + dev z ≥ 3, not under v2's settings. Under
  left skew the PoI conjunct gives no protection; under symmetric noise PoI carries the calibration of (b1) and (d),
  and partly of (a).

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `da264a40f929b114f7090da9d618402e74d94e3a`, sha256 `02fdbdd2d92b290ae1db82cc0c881d5dd43f591bb51c10c1fe89117acfd9c873`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

### Path B: decide the conventions, change the gate, then confirm (consistent with the 14 Nov ruling; recommended by the two reports)

1. **The author commits a decision row** in the same §10 block or an earlier one, using the draft below.
2. **An M11 gate-v3 unit** changes `gate.py` accordingly, as in D8-TEST §5:
   - `ELIG_Z_MIN` = 3 on train + dev;
   - the V1n bootstrap convention;
   - the chosen interval or pass rule;
   - the per-tier test floor chosen under Q4 ("d→c").

   It is independently reviewed, and it updates the parser test.
3. **This file is redrafted** with v3's commit and SHA-256. The row text stays the template below. The commit must
   reach `main` by merge (no squash, rebase or cherry-pick), or the guard refuses it.

The R1-BX-D8 row fixes the IQM of gap closed, with node-stratified bootstrap CIs, as the primary criterion, and
R1-BX-PROPOSED-CONFIRM (D8) confirmed "pass if the IQM lower bound is > 0 and the PoI lower bound is > 0.5". Choosing
D8-SKEW (c), a numerator test as the pass decision with the IQM as effect size only, departs from all three. It needs
an explicit amendment of both rows in the decision row, not only a gate change. (b2) keeps the IQM lower bound as the
pass criterion and changes only how the interval is formed.

**Coupled items.**
- Under (b2) the declared +∞ screen already fails any resample with a nonpositive eligible-node denominator, so item
  (1)'s bootstrap clause has no further effect.
- Under (c) the gap-closed bootstrap is not the decision, so item (1) only governs the point STOP.
- The split (item 3) is supplied by the caller, not by `gate.py`. The CONFIRM row's SHA does not bind it; the
  decision row and the analysis preregistration do. The floors (item 5) are tied to the split.

**Decision-row draft (path B; the author fills one option per bracket).**

```
| R1-BX-D8-V3 | C3 gate conventions, decided before R1-BX-D8-CONFIRM: (1) test side: [V1n — STOP only on a nonpositive point test denominator of an IQM-eligible node; a nonpositive resampled node denominator sets that node's gap closed to −∞ before the IQM | V1 — as V1n, but such a resample sets the IQM to −∞ | V2 — tier-pooled denominator, STOP on a nonpositive point or resampled tier denominator, amending R1-BX-D8's per-node gap closed]; (2) eligibility, replacing dev z ≥ 6 (not adopted, 14 Nov): [paired z of oracle − A2 on train + dev ≥ 3, with the dev denominator ≥ δ_n | a D21 σ_node threshold, after σ_node is put on the instance scale]; (3) split per tier, supplied by the caller and fixed in the analysis preregistration: [P3 1/3 : 1/6 : 1/2 | P2 1/2 : 1/6 : 1/3]; (4) pass rule under D8-SKEW: [(b2) studentized bootstrap lower bound of the IQM, with the declared convention that a resample with a nonpositive eligible-node denominator counts as +∞ in t* | (c) node-stratified Student-t test on the node-equal mean of A_arm − A2 over eligible nodes' test instances, IQM gap closed reported as effect size only, amending R1-BX-D8 (primary criterion and its bootstrap CIs) and R1-BX-PROPOSED-CONFIRM (D8)'s pass rule | (a) percentile, disclosed]; (5) per-tier test floor (Q4 "d→c"), for the split in (3): [P3: T0 ≥ 9, T1 ≥ 6 | P3: T0 ≥ 9, T1 ≥ 3 | P2: T0 ≥ 6, T1 ≥ 4 | P2: T0 ≥ 6, T1 ≥ 2]. Items (1), (2), (4) and (5) are implemented in gate v3, independently reviewed, and bound by R1-BX-D8-CONFIRM's SHA. |
```

**Confirmation-row template (path B).** The text is fixed by the parser. Only `<commit>` (40 or 64 hex digits) and
`<sha256 of gate.py>` change.

```
| R1-BX-D8-CONFIRM | Gate code `r1/c3/gate.py` @ `<commit>`, sha256 `<sha256 of gate.py>`, implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |
```

Under (c), "implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8)" would no longer be literally
true. The parser accepts no other wording, so (c) also needs a matching change to `analysis_guard.py`'s row pattern,
reviewed with gate v3, and the template above changes with it.

## 3. Format constraints

These come from `r1/c3/analysis_guard.py`, `_confirmation_commit`, unchanged since the 14 Nov draft.
- **Placement.** A table row in `PLAN.md` under `## 10.`, below a `###` heading with a valid date and an author
  marker (e.g. `### <d> November 2026 — C3 gate confirmation (author)`).
- **Table header.** `| ID | Decision |` or `| ID | Author decision |`.
- **Cells.** The first cell is exactly `R1-BX-D8-CONFIRM`. The second is exactly the text of one of the rows above,
  with no added words.
- **Uniqueness.** Exactly one such row in §10.
- **Ancestry.** `PLAN.md` and `gate.py` committed and clean. The named commit is an ancestor of HEAD and carries the
  same `gate.py` bytes.

**Checks.**
- `r1/tests/test_d8_confirm_draft_matches_parser.py` already runs the real guard on the 14 Nov row in a synthetic
  repository.
- `r1/tests/test_d8_confirm_draft_20261116.py` checks two things. Path A here is byte-identical to that row. The
  path-B template, with the current commit and SHA substituted, is accepted by the real parser function.

## 4. Order relative to sweep 2

- The confirmation row must be committed **before** any sweep-2 label table is copied back for analysis or read by
  analysis code (R1-BX-D8).
- Sweep-2 collection and sealing do not need it (R1-SWEEP-HOST-HTC; sealing rule in the S2-M1 draft).
- Path B adds an M11 v3 unit and its review, but it does not delay the sweep itself.
