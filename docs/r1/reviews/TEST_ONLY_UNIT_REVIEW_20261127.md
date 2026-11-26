# Review: test-only unit, local/20261126-05 item 2 (27 Nov 2026)

**Unit.** Branch `mac-test-only-20261127` @ `d5fb99cb`, base `main` `47df6f55`. The diff touches two test files only: `r1/tests/test_t1_tasl_xc3.py` and `r1/tests/test_trackp_p4_runner.py`.

**Reviewer.** An independent reviewer (Claude subagent) who did not write the unit. It changed nothing. The author of the unit transcribed this record from the hand-back.

## The xc3 alt-B case

**Cause confirmed.**
- `main`'s PLAN holds R1-XC3-FAIL-READING ("The xc3 note carries xc3_fail: A.").
- At base, the B note is refused by `g1b_crosscheck.py:577-581`. Running base's version of the test gives 1 failed, 4 passed.

**The fake row is well formed.**
- It matches the line filter (`:590`) and contains exactly one `XC3_FAIL_ROW_SENTENCE` match.
- So the test runs the real agreement branch rather than skipping it.

**The test is not weakened; it is stronger.**
- A new negative case runs the B note against an A row and expects a refusal.
- The signed A note is still checked against real `main`.

**Run:** 5 passed.

## The P.4 probe-charge test

**The flake is already gone on current main.**
- It predates P4-T1CHARGE. With T1's fixed 0.5 h, the total is at least 2.0 h (the killed attempt) + 0.5 h, whatever the receipts' elapsed time.
- So `probe_over_2_gpu_h` (`p4_lib.py:1926`) is always True.

**The unit's derived assertion copies the code's formula.** That is weak but hides nothing.

**Run:** with torch (`~/anaconda3/envs/hupdate/bin/python`) the test gives 1 passed (`charged` 2.5006).

**A fixed clock would break the probe** (zero step time). It is not needed.

## Minor findings

1. The comment is wrong for current main. Restore `is True`, optionally with `charged >= 2.5`.
2. The derived assertion would not catch a change to the threshold. The False boundary (≤ 2.0 h) is exercised nowhere.
3. The card asks for a "fixed clock"; the unit took the review's alternative. The report should say so.
4. `match="PLAN row"` would also match the malformed-row refusal. Use `match="says xc3_fail: A"`. `G.Stop` against `X.Stop` is style only.

Verdict: ACCEPTED WITH MINORS

## Author's response

- **Minor 1:** fixed. The test asserts `charged >= 2.5` and `probe_over_2_gpu_h is True`, with the comment explaining why it is deterministic.
- **Minor 4:** fixed. `pytest.raises(X.Stop, match="says xc3_fail: A")`.
- **Minor 3:** stated in the report.
- **Minor 2:** left as before this unit. No False-boundary test is added; that is outside the card.

After the fixes: `test_t1_tasl_xc3.py` 5 passed; the P.4 test 1 passed with torch.
