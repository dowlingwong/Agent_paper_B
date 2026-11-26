# Report — G.5 copy review verdict line and P11 host-test record (`compute/20261127-03`)

**Result: PASS for both items.** The REL-T1-G1B copy review now carries the exact `Verdict: ACCEPTED` line the
switch requires, with a fresh independent reviewer's confirmation; the P11 host-test record lists existing evidence
for C1–C16 and names what remains. No test, job, GPU lease, label or evaluation value was used for either item.

## 1. B3 — copy review verdict line

- **Branch:** `compute-g5-copy-verdict-line-20261127`
- **Tip:** `e6d6d50d245445fc1147ba6c47b7976105e10128`
- **Base:** `origin/main` `47df6f55`
- **Changed file:** `docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md`, sha256
  `b067c35c929d841f9f98f20c98aa22322e1235f9d1c65d529d22c8ce089fec0a` (was
  `0939aee57dce8d57081b7b5948a684d1ddfb0925c1785ae01e941ee8c591885e`)
- **Diff:** one line, `verdict: ACCEPTED` → `Verdict: ACCEPTED`; 138 lines before and after; every other byte
  identical. All nine needles `check_g1b_copy` requires remain present.
- **Reviewer confirmation:** `docs/r1/reviews/REL_T1_G1B_COPY_VERDICT_LINE_CONFIRMATION_20261127.md` sha256
  `a85d388d9817464528579d61107acf60ee3b9fec6f4b977938a95adb1c1831f1` — verdict `ACCEPTED`.
- **Test:** `python -m pytest -q -p no:cacheprovider r1/tests/test_t1_g5_seal.py -k seven` →
  **1 passed, 39 deselected** in the branch checkout; the reviewer also ran the real review text through
  `S._review_names` and `S.check_g1b_copy` with the nine needles, no `Stop`, and
  `S.VERDICT_ACCEPTED.search(text)` matches once.

The spec's review path is unchanged, so the local worker can re-render with the new review sha256. The review's
substance and verdict are unchanged.

## 2. P11 host-test record

- **Branch:** `compute-g5-p11-host-tests-20261127`
- **Tip:** `f40e5eef97b36ad4aee7a9389403eee7a080cd3f`
- **Base:** `origin/main` `47df6f55`
- **Record:** `docs/r1/reports/g5_code_20261123/G5_P11_HOST_TEST_RECORD_20261127.md` sha256
  `e0634a5b70afc0865f5ed7ab3105311eace20878ca7aef6536d70e66d7d8df8e`

It is one table for C1–C16, each with status (`COVERED`, `PARTIAL`, `NOT COVERED`, `REPLACED`), the existing
record path and full sha256, or `NOT COVERED`, and what remains. At `main` `47df6f55`:

- **Covered:** C3 (G.4b timing plus the G.5 pilot-basis), C8 (G.4b duplicate rate), C13 (`g5_pin_check` rc 0 on
  both checkouts).
- **Replaced:** C12 (the signed CUDA-IPC acceptance line, P1/S4 (a)).
- **Partial:** C6, C7, C9, C10, C11, C14, C15.
- **Not covered:** C1 as a whole, C2, C4, C5, C16.

Under the coordinator's option (b), the remaining pre-publication runs are C2, C4, C5, C6 (G.5 seal), C7 (restart),
C9, C10 (short span and restart), C11 (mutual refusal), C14 (real engine), C15 (pre-run seal parts) and C16. The
record runs nothing; the author's P11 decision is the gate.

## What I changed

Only the two documentation branches above. No code, spec, pin, note, sealed file, label or evidence value was
changed. No host was entered for these items.

## What happens next

- Coordinator: merge the verdict-line branch (docs only, tier D), then the local worker re-renders G.5 with the new
  review sha256; send the P11 record to the author with the P10/S9 sheet.
- After the author's P11 row is on `main`, a task file should name the exact smoke attempts and hosts for the
  remaining C items.

**Decided alone:** to preserve the review's lower-case verdict nowhere (one capitalisation only) and to add the
reviewer's confirmation as a separate file rather than editing the review further; to mark predecessor records
`PARTIAL` unless they exercise the item as worded.
