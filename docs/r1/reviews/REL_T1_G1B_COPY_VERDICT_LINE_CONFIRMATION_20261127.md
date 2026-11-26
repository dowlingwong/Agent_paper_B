# REL-T1-G1B copy review — verdict-line confirmation

**Reviewer statement.** I am a fresh, independent reviewer. I did not write this change and had no part in
producing it. This review was read-only: I ran no commit, push or write to the repository or the checkout.

**Branch / base.** Checkout of `compute-g5-copy-verdict-line-20261127` over base `47df6f55`. The fix is one
change to `docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md`; the diff is 1 file, +1/−1.

**Diff (only the verdict line):**
```
@@ -135,4 +135,4 @@
 I changed nothing except writing this review file.

-verdict: ACCEPTED
+Verdict: ACCEPTED
```

**Content unchanged.** Base and branch files are 138 lines each; everything before the final line is
byte-identical. The only difference is `verdict:` → `Verdict:` on the last line.

**Regex (branch file, Python `re.M`).**
- `^Verdict: ACCEPTED\s*$` → **1 match** (PASS, exactly once).
- `^verdict: ACCEPTED\s*$` → **0 matches** (old form gone).

**Needles required by `check_g1b_copy` / `_review_names` (substring test).** All PASS:
- `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/summary.json`
- `945abc0a7ced28a7ffa27905c3282b7ad4b25ed6f9c49de01ca7c595491e7a67`
- `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/summary.json`
- ASSEMBLY copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/ASSEMBLY.json`
- ASSEMBLY sha256 `e4056710beff92b4e0628372831632c9a54d070be1c41497e990eb45924236dd`
- runs copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/runs.jsonl`
- runs sha256 `1f56c0681d3a6cbd8005b3ee45da4ef2680d9354c869a0d16433b72afc971385`
- gate copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/crosscheck_gate.json`
- gate sha256 `00ee68c28aa2f9fcebd0b858d85df21a1baa3175b492eb5bfef0b074b073c8e2`

The four paths/hashes are the ones `run_copies`/`gate_for` derive for this copy; each named hash also
matches the actual file on disk. `g5_tasl_spec.json` still carries `PENDING` placeholders in this checkout;
those values are the ones the switch will consume at publication, and the placeholder state is pre-existing
and untouched by this diff.

**Test / static checks (branch checkout, no network).**
`python -m pytest -q -p no:cacheprovider r1/tests/test_t1_g5_seal.py -k seven` → **1 passed, 39 deselected**.
Because that test builds a synthetic review, I additionally ran the real review through the switch code:
`S._review_names(review, needles, read)` and `S.check_g1b_copy(...)` with the nine needles above both
completed without a `Stop`, and `S.VERDICT_ACCEPTED.search(text)` is True.

**Conclusion.** The change is exactly the one-line capitalisation of the verdict, all required naming
survives, and the switch's verdict regex now matches once.

Verdict: ACCEPTED
