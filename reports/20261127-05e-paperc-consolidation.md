# local/20261126-05 item 5 — Paper C consolidation (DONE)

- Task branch `mac-paperc-consolidated-20261127` @ `2d0df77a21861bb3f6b7d59c89751670eb4cb5d6`. Started at published main `5c901d19`, updated to published base `29099c4bac068355d0b5593b8ac9665e19f38049`.
- Source tips retained as ancestors: E-SYN `f8176760f286d78c2575b8972158276093f9a6a0`, theory `33c2a012df087e4662b89ed44154078a1ff92973`, real-loop skeleton `24ac2e3f13443b5eedc6167ddf1905bf8814265d`. The scaffold, build and addendum branch histories are also contained.
- Independent review **ACCEPTED** at `70bac48b`, recorded in `docs/r1/reviews/PAPERC_CONSOLIDATION_REVIEW_20261127.md`. Later base updates preserved the source files and left PLAN additions-only against the newer main. PLAN adds 45 verbatim lines and 18 unique author decision IDs. Five whitespace findings came from the inherited reviewed content.
- SHA-256 at final tip: PLAN `1de64beded0023491b36a394014a62d3ddcb30c079a05b6df277f5e32f06922f`; Paper C seed registry `15ed0260952ace21c635c4c06dadbbe3bf41c8a4a557f9cce30f8842c495f0f9`.

Full `r1/tests` regression at published base `29099c4bac068355d0b5593b8ac9665e19f38049` and a temporary integration of this exact tree, the G2 fitter, and the D.3 namespace checker at `19369c29`. Both runs used harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, fresh short TMPDIRs, LightGBM off the path, `COPYFILE_DISABLE=1` and `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`. Base 76 failed / 4817 passed / 162 skipped / 3 errors. Integrated 76 / 4843 / 162 / 3. **Zero new failures**, 79 failing IDs match, list SHA-256 `1f8ae808ccf8ae3cd17503991f7d23a16055c77f55af01e33f74558ac7599256`. The 26 additions are 19 G2 tests and 7 namespace checks.

Paper C tests used the same local environment at E-SYN source `f8176760` and the consolidated tree, excluding four archived-census replay cases that would reopen historical records. Source 234 passed / 4 failed. Consolidated 278 passed / 4 failed. The failing IDs matched exactly. Three cases need the LightGBM environment and the P9 committed-output reproduction uses the older study toolchain. The 44 newly included skeleton cases passed.

Next: the coordinator reviews publication authority for the 22 November author rows and refreshes the Paper C canon status at publication. The planned CPU measurements still need their own runbooks, independent reviews and authorizations. R1-PAPERC-CORE remains open.

Decided alone: keep the source histories and exact file bytes, preserve all published PLAN text, and use a temporary merged test checkout for the full regression. No historical-label replay, new empirical run, or sealed read.
