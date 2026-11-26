Reviewed base: `61e8aed7` (branch `mac-d8-gate-v3-20261116`; accepted in round 1, confirmed in round 2 at `6aa9985c` / `84314a59`)

# Independent review record — M11 D8 gate v3 and the R1-BX-D8-CONFIRM v3 draft (16 November 2026)

**Unit.** Gate v3 in `r1/c3/gate.py` (R1-BX-D8-V3-A items 1–3, R1-BX-D8-V3-B items 4–5), its tests and report, and the
path-B CONFIRM draft `docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_V3_20261116.md`. Authority:
`author-decisions-20261116c` @ `65d8d5bb`.

**Process.** One independent reviewer (a separate agent that did not write the code), two rounds. The reviewer edited
nothing. The round texts are reproduced below as delivered.

| Round | Commits reviewed | Verdict |
|---|---|---|
| 1 | `61e8aed7` (gate v3, tests, report) and `2f51426b` (CONFIRM draft, test retargeting), diff from `65d8d5bb` | ACCEPTED (6 MINOR, 1 note) |
| 2 | `6aa9985c` (gate: round-1 minors) and `84314a59` (draft re-filled, report), diff from `2f51426b` | ACCEPTED |

Gate v3 as bound by the draft: `r1/c3/gate.py` @ `6aa9985c5069c67ab580e19c0d02898ae2c6686d`, SHA-256
`ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee`. The round-2 gate change adds reporting only.

---

## Round 1 (commits `61e8aed7`, `2f51426b`)

## Independent review: gate v3 (`61e8aed7`) and the R1-BX-D8-CONFIRM v3 draft (`2f51426b`), base `65d8d5bb`

No BLOCKING or MAJOR findings. Gate v3 implements V3-A items 1–3 and V3-B items 4–5 faithfully. Its (b2) bound reproduces `d8_skew_sim.py` @ `dc899aad`, apart from one labelled convention for ties (finding 1). The CONFIRM draft's row is the right one. I edited, committed and pushed nothing.

### What I checked and found correct
- **V3-A (1), V1n** (`gate.py:400-415`, `:452-457`): STOP only when the point test denominator of an IQM-eligible node is ≤ 0. A resample where an eligible node's denominator is ≤ 0 sets IQM* to −∞, is counted per node and then screened, so it has no effect on the bound, as V3-B says.
- **V3-A (2), eligibility** (`:304-309`, `:340-356`): paired z of oracle − A2 over train + dev pooled, ddof 1, z ≥ 3. The dev denominator must be ≥ δ_n. When sd = 0 the decision follows the sign of the mean, as the simulation's ±inf does. Every reason that applies is listed.
- **V3-A (3), split**: the gate requires the declared split to be exactly P3 (STOP otherwise) and the train, dev and test ids to be pairwise disjoint.
- **V3-B (4), (b2)**: checked line by line against sim lines 60–180:
  - per-node delta-method se, ddof 1 for var and cov, positive part;
  - ŝe uses the IQM weights on the sorted G;
  - se* is computed with gb = 0 where the denominator is ≤ 0, as the sim does;
  - the screen is identical (bad eligible node, se* not > 0, or non-finite t*) and holds t* at 1e12, the sim's BIG;
  - linear quantile at L;
  - when ŝe = 0 the bound is θ̂.
- **PoI and draws**: PoI uses all nodes. Ties count ½ (R1-BX-D8); the sim's `a > 0` counts them as 0, which matters only for ties. Seed 20261108, PCG64, and one draw per node in sorted node and instance order, unchanged from v2.
- **Holm**: the ranking key "passes at 97.5 % first" comes from the D8-SKEW declaration §2. The pass test is nested in L: the bound does not increase with L, and neither does the PoI bound. So the procedure equals Holm on the implied p-values. Neither the verdict nor the set of passing arms can depend on the arm labels.
- **V3-B (5), floor**: T0 ≥ 9 and T1 ≥ 3. A node below it is excluded from the IQM, kept in the PoI and reported (`below_test_floor`). Eligible nodes therefore always have n ≥ 3, so ddof 1 is safe, and n_test = 1 nodes appear only in the PoI.
- **Nothing dropped**: no node or resample is dropped silently.
- **CONFIRM row**: it is the parser's fixed template with commit `61e8aed79474d11b477132a36a3356714551db60` and SHA-256 `26de7381e653045594fbb74e88b4263848dc5be7feefff8de9400b56aeb02ed0`. I recomputed that SHA at `61e8aed7`, at `2f51426b` and in the worktree, and `gate.py` is unchanged between the two commits. The draft's claims about ancestry and identical bytes match `require_d8_confirmation`. Nothing in it is presented as decided by the author.
- **Report**: the v2 SHA `02fdbdd2…` at `da264a40`, the 90 tests, the 47 v2 tests and the four pre-existing failures are all correct. `agree.py` reproduces exactly: 444 comparisons, 444 agreements, 9 skipped, largest relative difference 2.2e-16.

### Tests
- **Target set** (NumPy 2.4.4): **99 passed**.
- **Wider `-k "d8 or gate or guard"`** (trackg venv, NumPy 2.5.3): 4 failed, 602 passed, 21 skipped. The same 4 fail at `65d8d5bb` (579 passed there): `test_c3_evidence_guards` ×2 and `test_trackx_lease_guardian` ×2. None is in a D8 file.
- **Mutation testing** (on a copy under /tmp): 16 mutations of `gate.py`, 13 caught by the tests. They include ddof 0 in var and in cov, unsorted ŝe, unsorted se*, nearest quantile, PoI on eligible nodes only, a changed seed, a dev-only z, a literal +inf, a T1 floor of 2, unsorted instance ids and a shifted θ̂.
  - The 3 that survived change nothing. Dropping the positive part has no effect because the numerator is the sample variance of a − G·d. Dropping the se* = 0 screen or the bad-resample screen has no effect because `isfinite` already catches those resamples.
- **Independence of the reference**: it copies the simulation's lines verbatim. It shares only the eligible set, the seed and the draw plumbing with the gate, not its arithmetic.

### Findings
1. **MINOR: the docstring's claim about ties is wrong** (`r1/c3/gate.py:78-79`). It says the stable sort keeps tied nodes in node-id order like "the simulation's `np.argsort` default". On this AVX-512 host the default argsort in NumPy 2.4.4 is not stable: it differed from `kind='stable'` on 17,217 of 20,000 random small vectors with ties. With tied G, which discrete utilities can produce, ŝe then differs from the sim's (example: k = 11, 0.20811 vs 0.20901). The sim's result on ties depends on the platform, so the stable sort is a legitimate convention, and report §3.3 describes it accurately. **Fix:** reword the docstring. It is part of the bound file, so the fix changes the SHA and the draft row then needs updating.
2. **MINOR: the split check only reads the label** (`gate.py:269-271`; report §3.5). At the design sizes P3 is exact (T0 6:3:9, T1 4:2:6), so no rounding rule is needed to check it. A P2 split labelled "P3" still runs: on T0 every node is then excluded by the floor, but T1 at 6:2:4 passes unnoticed, and `off_design_size` checks only totals. **Fix:** report an `off_split` list of nodes whose counts at the design size differ from P3.
3. **MINOR: the (b2) unit test never checks a passing bound** (`r1/tests/test_d8_gate_synthetic.py:284-301`). In 6 of its 7 tables, so many resamples are screened that the bound sits at about −1e11 (227 to 1,428 screened resamples). The seventh is about −0.09, and no case has a positive bound. The element-wise t* comparison still exercises the arithmetic, and `agree.py` covers passing cases (96 of 444 bounds > 0, 250 dominated by the sentinel), but `agree.py` is not a test. **Fix:** add one or two tables with a positive bound not dominated by the sentinel.
4. **MINOR: report §6 is an unfilled placeholder** (`docs/r1/reports/M11_D8_GATE_V3_20261116.md:94-96`), and §4 (line 85) points to it for the full-suite result. **Fix:** fill it in, or remove the reference.
5. **MINOR: the CONFIRM draft cites a review that does not exist yet, and came before it** (`docs/r1/proposals/R1_BX_D8_CONFIRM_DRAFT_V3_20261116.md:15-16`). It says the review "is recorded in" `reviews/M11_D8_GATE_V3_REVIEW_20261116.md`, which is absent at `2f51426b`. The draft was also committed before this review, while the author's instruction was "reviewed, then draft". This is harmless because §3.1 makes the draft conditional on the review. **Fix:** say "will be recorded".
6. **MINOR (disclosure): the calibration assumed continuous data.** D8-SKEW and D8-PASS had no tied utilities. The gate counts PoI ties as ½, where the sim's `a > 0` counted them as 0, and ties in G fall under finding 1. If U is discrete, the calibration evidence does not cover ties. **Fix:** say so in the report.
7. **Note, no change needed: implementation details that do not affect results.**
   - θ̂ comes from the loop in `_node_iqm` while IQM* comes from a dot product (`:423` vs `:469`). The sim uses the dot product for both; the difference is at rounding level (2.2e-16).
   - On realistic simulated tables a large share of resamples is screened, so the bound often collapses and the gate fails. That is the declared design ("calibration comes from the positivity screen"), not a defect.
   - Holding +∞ as 1e12 follows the sim rather than the row's literal "+∞". This is disclosed (report §3.1, draft §2) and differs only when ŝe is around 1e-12.

Cleanup: I removed the temporary worktree of `65d8d5bb` with `git worktree remove` and all my /tmp temp files. `/tmp/pb/wt/gv3` is clean.

VERDICT: ACCEPTED

### Author's response to round 1 (commits `6aa9985c`, `84314a59`)

1: the ties docstring is corrected (NumPy's default argsort is not stable on every platform; tied G can give a
different ŝe from the simulation's). 2: new constant `DESIGN_SPLIT` and output field `off_split`, listing nodes at the
design size whose counts are not P3; report §3.5. 3: the (b2) equality test adds two high-signal tables with positive
bounds and no screened resample. 4: §6 is filled after the base-versus-tip full-suite comparison (the reviewer was
asked not to treat the placeholder as a finding in round 2). 5: the draft is re-filled with `6aa9985c` / `ffb70d7a…`,
and its review citation is reworded. 6: report §3.8 discloses that the calibration evidence did not cover ties.

---

## Round 2 (commits `6aa9985c`, `84314a59`)

## Round 2 (confirmation): gate v3 @ `6aa9985c`, CONFIRM draft @ `84314a59`, compared with `2f51426b`

All of the round-1 minors you listed are fixed. The gate change only adds reporting, the new tests are meaningful, and the draft row is correct. I made no edits or commits, and removed my temporary directory.

**Gate change: reporting only.** I read every line of the `r1/c3/gate.py` diff between `2f51426b` and `6aa9985c`:
- It adds a constant `DESIGN_SPLIT`, which evaluates to `{T0: (6, 3, 9), T1: (4, 2, 6)}`.
- It adds a top-level output field `off_split`. This lists nodes at their design size whose train : dev : test counts differ from P3.
- It adds `protocol.design_split`.
- It rewrites the ties docstring. The new wording is accurate: NumPy's default argsort is not stable on every platform, so with exactly tied G the simulation's se can differ from the gate's.

No function that computes validation, eligibility, point statistics, bootstrap, bounds or Holm changed. The verdict and bounds therefore cannot change.

**New tests are meaningful.**
- The (b2) equality test adds two high-signal tables (seeds 21 and 22, μ = 6, g = (0.8, 0.5)). For both, it asserts that 0 < bound < θ̂ and that no resample is screened. So the equality with the simulation's code is now checked on passing bounds that are not dominated by the 1e12 sentinel, which was my round-1 gap.
- The new `off_split` test turns a design-size T1 node into P2 counts 6 : 2 : 4 labelled P3. It checks the exact `off_split` entry and that `off_design_size` stays empty.
- The counts test now checks that off-size nodes appear only under `off_design_size`, and pins `DESIGN_SPLIT`.

**CONFIRM draft row.** It is the parser's path-B template with commit `6aa9985c5069c67ab580e19c0d02898ae2c6686d` and sha256 `ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee`. I recomputed that SHA from `gate.py` at `6aa9985c`, at `84314a59` and in the worktree, and it matches. `61e8aed7` is an ancestor of `6aa9985c`. The template test and the real-guard test in a synthetic repository both pass. The draft's wording "accepted in round 1 … confirmed in round 2" is consistent with this review.

**Report.** The new 93-test count is right (90 + 2 new table cases + 1 new test). §3.3, §3.5 and the new §3.8 ties disclosure are accurate. As you asked, I did not treat the §6 placeholder as a finding.

**Target tests** (`/tmp/np244/bin/python`, NumPy 2.4.4, worktree at `84314a59`, clean): 102 passed.

No BLOCKING, MAJOR or new MINOR findings.

VERDICT: ACCEPTED

---

Accepted commit: `61e8aed7` (round 1), confirmed at `6aa9985c` / `84314a59` (round 2). Gate v3 bound by the CONFIRM
draft: `6aa9985c`, SHA-256 `ffb70d7a…`.
