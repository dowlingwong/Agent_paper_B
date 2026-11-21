Reviewed base: `15b7389e` (the accepted sweep-2 analysis preregistration branch `mac-sweep2-prereg-20261121`, over published `main` `4aac5209`); accepted at `b1151ba423096da4d9dd4b32632e6d309c7f5641` (gate v3.1 code at `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d`, `r1/c3/gate.py` sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`)

# Independent review record — gate v3.1 (PRE-WDBC option B) and the R1-BX-D8-CONFIRM-V31 row draft (approved: false)

**Unit.** On `mac-gate-v31-20261121`: `r1/c3/gate.py` replaced by gate v3.1 (a declared T0 node set; v3's output on the full
set otherwise), `r1/c3/analysis_guard.py` accepting the successor row `R1-BX-D8-CONFIRM-V31`, the frozen v3 file
`r1/tests/fixtures/gate_v3_6aa9985c.py` (sha256 `ffb70d7a…`), the body-diff fixture, `r1/tests/test_d8_gate_v31.py`, added
guard tests, re-pointed draft tests, and `docs/r1/proposals/R1_BX_D8_CONFIRM_V31_DRAFT_20261121.md`. Authority: the accepted
preregistration's PRE-WDBC option B and §9, R1-S2C3B-WDBC, R1-BX-D8, R1-BX-D8-CONFIRM, R1-BX-D8-V3-A/B; the queue of 21 Nov
2026, item 4. The row and the choice of option B are the author's.

**Process.** One independent reviewer for all three rounds, read-only, scratch under `/tmp/rev_gate/` moved to its
`_to_delete/`; it compared the frozen v3 file with v3.1 on its own randomized fixtures (NumPy 2.5.4 and the pinned 2.4.4).
Round 3 confirms a docstring-only fix after the round-2 acceptance. The round texts are reproduced below as delivered.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `af9c3ded + 6fa62ce5` | CHANGES REQUESTED (1 blocking, 1 major, 3 minor) |
| 2 | `80075908 + c4ee0779` | ACCEPTED (1 optional minor) |
| 3 | `31dab9ef + b1151ba4` | ACCEPTED (confirmation) |

**Open for the author.** PRE-WDBC (B recommended in the preregistration) and the row `R1-BX-D8-CONFIRM-V31`, which must reach
`main` in the same merge as commit `31dab9ef` (kept reachable: no squash or rebase). Until then every reader that
requires D8 confirmation STOPs on a checkout with gate v3.1, including three Track P tests in `r1/tests/test_trackp_sft.py`
(they pass with the row added, checked in a scratch copy). The fold-analysis module (leave-one-suite-out) that calls the
gate with a declared subset is a later unit.

## Round 1 (`af9c3ded + 6fa62ce5`)

> Verdict: CHANGES REQUESTED
>
> On the full eight-node set, v3.1 reproduces v3. The guard and the row draft are sound. There is one fail-open hole in the subset path, and the source-diff test checks nothing.
>
> **What I checked (read-only; scratch is in /tmp/rev_gate/_to_delete/)**
> - The fixture `r1/tests/fixtures/gate_v3_6aa9985c.py` is byte-identical to `git show 6aa9985c:r1/c3/gate.py`, and its sha256 is ffb70d7a… .
> - v3.1 `r1/c3/gate.py` has sha256 8e15816f… at both af9c3ded and 6fa62ce5.
> - The nine named test files pass: 386 passed on NumPy 2.5.4.
> - I wrote my own comparison of frozen v3 against v3.1 with all eight nodes declared (declared list shuffled; node order and instance-id order shuffled). It covered:
>   - tied utilities and A3 equal to A2;
>   - a node whose oracle equals A2 on every instance, so the train+dev differences have zero spread;
>   - weak and negative gaps, nodes below the test floor, and delta_n that makes nodes ineligible;
>   - partial T1, no T1 at all, and two T1 nodes in one suite.
> - Results: 150 seeds on NumPy 2.5.4 and 60 more on the pinned 2.4.4 showed no difference in any output field, in key order, or in PASS/FAIL. The "no eligible node" STOP, the "nonpositive test denominator" STOP, the T0-with-suite and bad-T1-suite STOPs, and the duplicate-node ValueError gave identical messages.
> - The only full-set message difference is in the T0 layout STOP itself ("exactly the declared set …"). That is inside the allowed layout change; I don't count it as a finding.
> - Declared-set checks all fail closed: field missing, not a list, non-string entries, duplicates, a node outside `T0_NODES`, a declared node not supplied, a supplied node not declared, and a v3-schema input. The empty set works.
>
> **Blocking**
>
> B1. `r1/c3/gate.py:349-361` (`_check_layout`): with a subset declared, a T0 node relabelled as T1 is accepted silently.
> - Input: `t0_nodes` = the seven nodes without `openml_wdbc`, plus `openml_wdbc` supplied with `"tier": "T1", "suite": "MLGym"`.
> - v3 STOPs on this. v3.1 runs it to a verdict (PASS in my run), with wdbc counted in the IQM, the PoI and the T1 stratum. Neither the T0 check nor the T1-suite check catches it.
> - This is exactly the scenario R1-S2C3B-WDBC excludes. It also breaks the docstring and the row text ("STOPs unless the T0 nodes supplied are exactly that set").
> - Fix: after the `t0 != declared` comparison (so the full-set STOP message stays v3's), add a STOP for any node of any tier whose id is in `T0_NODES` but not in `declared`, i.e. a T1 node with a T0 name. Add a test for it, including the empty-set case.
> - The gate sha then changes, so the draft's commit, sha and row must be regenerated.
>
> **Major**
>
> M1. `r1/tests/test_d8_gate_v31.py:179-182`: the source-diff guard test is vacuous.
> - The allowed-prefix tuple ends with `''`, and `c.startswith('')` is always True, so the test passes on any edit.
> - I confirmed this: changing `PRACTICAL_SIZE` to 0.2 and `SEED` to `1 + 20261108` in a copy still passes the assertion.
> - The bare `'raise ValueError('`, `'raise GateStop('` and `'declared'` prefixes would also let any raise, or any line starting with "declared", change.
> - Fix:
>   - Drop `''` and filter blank lines explicitly.
>   - Replace the prefix list with an exact expected set of removed and added lines (or an exact expected diff of the body after `from __future__`).
>   - Add a negative self-check that feeds a mutated source to the same function and requires it to fail.
>
> **Minor**
>
> m1. `test_d8_gate_v31.py:59` / `:108`: the reproduction fixtures are all easy cases (mean gap 1.5, every node eligible, every node at the test floor, one T1 node per suite), and there is only one STOP case.
> - The claim held under my broader comparison, but the tests themselves don't show it.
> - Fix: add parametrized eight-node cases for ties, ineligible nodes (z, delta_n, floor), partial T1, no T1, off-design sizes, and the nonpositive-denominator STOP.
>
> m2. `docs/r1/proposals/R1_BX_D8_CONFIRM_V31_DRAFT_20261121.md:30-34`: the merge-order note doesn't say that af9c3ded must survive the merge.
> - The guard requires the row's commit to be an ancestor of HEAD and to hold the same gate bytes. A squash or rebase merge would leave the row bound to an unreachable commit, and the guard would STOP. That fails closed, but it is confusing.
> - Fix: state "merge without squash or rebase, or regenerate the row with the merged commit".
>
> m3. `r1/tests/test_c3_analysis_guard.py:298`: the successor tests don't cover the cases that should not supersede.
> - These are a successor row under a non-author or undated heading, in an HTML comment, outside §10, or with a variant id such as `-V3.1`. In each case the v3 row should stay in force for v3 bytes and refuse v3.1 bytes.
> - I checked these by hand against the real PLAN and all behave correctly.
> - Fix: add assertions for them, plus a bold-id successor, which the guard accepts as intended.
>
> **Guard (r1/c3/analysis_guard.py:126-145): sound**
> - Successor rows go through the same §10, dated-author-heading, header, fence, comment and HTML filtering as the CONFIRM row.
> - Any well-placed successor row makes the v3 row irrelevant:
>   - exactly one exact-text successor matching the current gate sha is required;
>   - a malformed successor or two successors returns None (fail closed);
>   - v3 bytes with a successor present are refused.
> - So the two rows can never authorize different bytes, and with no successor the v3 path is unchanged.
> - Against the real PLAN: today v3.1 bytes give None and v3 bytes give 6aa9985c. With the draft row pasted under a `### 21 November 2026 — author decisions` table, v3.1 bytes give af9c3ded and v3 bytes give None.
>
> **Row draft: accurate**
> - Commit af9c3ded…6654 and sha 8e15816f… are correct, and the row matches the guard exactly.
> - It gives options A, B and C with A recommended, plus a merge-order note.
> - R1-S2C3B-WDBC is paraphrased faithfully, and nothing is presented as a decision.
> - After B1 the "differs only…" text stays accurate, but the commit and sha must be updated.
>
> **Changes to existing tests: justified**
> - `test_d8_gate_synthetic.py` now declares all eight nodes by default, and the version constants are updated. The new malformed-input cases are useful.
> - `test_d8_confirm_draft_v3_20261116.py` is re-pointed to the frozen v3 file, which is correct because the v3 draft binds the v3 bytes.
> - `test_d8_confirm_draft_matches_parser.py` is re-pointed to the v3.1 draft.
>
> **trackp_sft failures: the reasoning holds**
> - On this branch the Track P tests fail with exactly "STOP: exact affirmative R1-BX-D8-CONFIRM (or its successor …) with current gate SHA required". The real PLAN binds only the v3 sha, so the guard is doing its job.
> - I didn't rerun the 35/35 scratch-copy run. In-process, with the row added, the guard returns af9c3ded, and af9c3ded holds the v3.1 bytes, so the remaining checks should pass as long as the commit is an ancestor (see m2).

## Round 2 (`80075908 + c4ee0779`)

> Verdict: ACCEPTED
>
> Round 2 fixes all five round-1 findings (B1, M1, m1–m3). Gate v3.1 still gives the same output as v3 when all eight T0 nodes are declared, with the new check in place. Nothing is blocking. One optional minor (m4) is left.
>
> **How I checked**
> - Read-only. Scratch was moved to `/tmp/rev_gate/_to_delete/`, and the worktree is clean.
> - `r1/c3/gate.py` has sha256 `5e27c1c0…f011` at both 80075908 and c4ee0779, and c4ee0779 changes no code.
> - The nine test files: 400 passed on NumPy 2.5.4. `test_d8_gate_v31.py` and `test_d8_gate_synthetic.py`: 127 passed on the pinned NumPy 2.4.4.
>
> **B1 (relabelled T0 node): fixed**
> - The fix is at `gate.py:355-358`. It STOPs on any supplied node whose id is in `T0_NODES` but not declared, whatever its tier.
> - It sits after the `t0 != declared` comparison. With all eight declared it can never fire, so v3's full-set behaviour and messages are unchanged.
> - I re-ran my round-1 probe: `openml_wdbc` supplied as a T1 MLGym node, with the seven-node declaration, now STOPs. It used to give a PASS verdict.
> - The new test covers both the seven-node and the empty declaration.
>
> **Full-set reproduction: still holds**
> - I re-ran my independent comparison of the frozen v3 file against v3.1, with all eight declared: 150 seeds on NumPy 2.5.4 and 50 on 2.4.4. It covers ties, nodes ineligible on z, delta_n and the test floor, weak and negative gaps, partial T1, no T1, and two T1 nodes in one suite.
> - Zero differences in any output field or in key order.
> - STOP messages are identical for: the nonpositive test denominator, no eligible node, a T0 node with a suite, a bad T1 suite, and a duplicate node.
>
> **M1 (source-diff test): fixed**
> - `test_the_code_body_differs_from_v3_by_exactly_the_reviewed_lines` compares the full '-'/'+' line list of the code body exactly against `r1/tests/fixtures/gate_v31_body_diff.txt`. Whitespace and blank lines are kept, so any other change to the body fails it.
> - The docstring is exempt. That is safe: nothing can run before `from __future__`, so code can't hide there.
> - I read all 40 lines of the fixture. They are exactly the reviewed changes: the version and schema strings, `_declared_t0`, the layout check including the relabel STOP, and the `declared_t0_nodes` output field.
> - The negative test applies four constant changes (PRACTICAL_SIZE, SEED, ELIG_Z_MIN, N_RESAMPLES). It first asserts each original string is present, so it can't pass by not finding them.
>
> **m1 (harder cases): fixed**
> - I ran each new case through v3.1 and each produces what its name says: test_floor, delta_n, z ineligibility, `off_design_size`, the suites-without-T1 lists, ties, and a FAIL verdict for weak gaps.
> - Small nit: `_ineligible_z` also trips delta_n, because a zero dev denominator fails both, so z is never tested alone. My fuzz covers z on its own, so no change is needed.
>
> **m2 (merge note and draft): fixed**
> - The draft names commit 80075908 and sha 5e27c1c0, both correct. Its merge note now requires that commit to survive the merge (no squash or rebase) or the row to be regenerated.
> - There is exactly one candidate row.
> - I pasted it into the real PLAN under a `### 21 November 2026 — author decisions` table in §10:
>   - the guard returns 80075908 for the v3.1 bytes and None for the v3 bytes;
>   - 80075908 is an ancestor of c4ee0779.
> - The added sentence ("a T0 node outside the declared set is a STOP in any tier") is accurate.
>
> **m3 (guard placement tests): fixed**
> - A successor row under an undated heading, under a non-author heading, in an HTML comment, outside §10, or with id `R1-BX-D8-CONFIRM-V3.1` does not supersede: the v3 row stays in force and the v3.1 bytes are refused.
> - A bold id is accepted.
> - This matches what I checked by hand in round 1.
>
> **Minor (optional)**
>
> m4. `r1/c3/gate.py:5-11` and `:56-60`: the docstring doesn't mention the new relabel STOP. It still says only "a missing, extra or renamed T0 node against the declared set". Suggested fix: add "a `T0_NODES` id supplied in any tier but not declared is a STOP". Editing the docstring changes the gate sha, so the draft row would have to be regenerated again. I'd only do it if there is another code revision anyway; it is not required for acceptance.
>
> **trackp_sft**
> The reasoning from round 1 still holds. Without the row, the three Track P tests STOP at the guard as designed. With the row added, the guard returns the commit, and that commit holds the current gate bytes.

## Round 3 (`31dab9ef + b1151ba4`)

> Verdict: ACCEPTED
>
> The m4 change is docstring-only, the code is unchanged, and the regenerated row is accepted by the guard for the new gate bytes. I found nothing new.
>
> **What changed**
> - 31dab9ef edits only the module docstring of `r1/c3/gate.py`, in two places: lines 9-10 and 60-61. Both name the STOP for a `T0_NODES` id supplied in another tier without being declared. The wording matches what the code does.
> - Everything from `from __future__` onward is byte-identical to 80075908, which I accepted in round 2. So the body-diff fixture still holds, and so does my round-2 check that v3.1 gives v3's output on all eight nodes.
> - b1151ba4 changes no code under `r1/`.
>
> **Row binding**
> - `r1/c3/gate.py` has sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23` at both 31dab9ef and b1151ba4.
> - The draft contains exactly one candidate row. It names commit `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d` and that sha, and both are correct.
> - 31dab9ef is an ancestor of b1151ba4.
> - I pasted the row into the real `docs/r1/PLAN.md`, in a §10 table under `### 21 November 2026 — author decisions`. Results from the guard's `_confirmation_commit`:
>   - new bytes: returns 31dab9ef;
>   - round-2 v3.1 bytes (5e27c1c0): None;
>   - v3 bytes (ffb70d7a): None.
> - Against the real PLAN without the row, the new bytes get None. That is the expected lock until the author adds the row.
>
> **Tests**
> - The nine targeted files: 400 passed on NumPy 2.5.4.
> - `test_d8_gate_v31.py` and `test_d8_gate_synthetic.py`: 127 passed on the pinned NumPy 2.4.4.
>
> **Merge note**
> When this merges, commit 31dab9ef must stay reachable from `main`: no squash or rebase, or else regenerate the row with the merged commit. The draft already says this.
>
> Read-only throughout. Scratch is under `/tmp/rev_gate/_to_delete/`, and the worktree is clean.

---

Code-Commit: 31dab9efb94b7f187ec44cab1bc4a4ad63c1085d
Verdict: ACCEPTED

Accepted commit: `b1151ba423096da4d9dd4b32632e6d309c7f5641` (round 3; gate code `31dab9ef`, sha256 `a3f7d002…`).
