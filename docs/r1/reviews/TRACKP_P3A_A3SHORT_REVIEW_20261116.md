# Independent review — Track P P.3a A3-short execution delta (`3833d93e`)

Independent reviewer (fresh subagent, read-only; CPU-only checks; transcribed here by the operator
because the reviewer did not write a file). Reviewed bytes: branch `trackp-p3a-code-20261116`,
commit `3833d93e` (single parent `b9ad6f8f`), files `r1/c3/train/exam_run.py` (+21/−8),
`r1/scripts/trackp.py` (+16/−1), new `r1/tests/test_trackp_p3a_a3_short.py` (+139). Not pushed at review
time; author/committer Dowling Wong. Authority: `trackp_p3a_20261027.md` + amendment
`trackp_p3a_amend_20261104.md` (option 3), accepted Unit A plan/review (`TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md`).

## Verdict: ACCEPTED — no BLOCKING, no MAJOR; 5 MINOR

- **Scope/hygiene PASS:** exactly 3 files; no W2-3/v3/v2/M13/order/config/rule/E0/data/model/harness
  change; no deletion; `git diff --check` clean; pinned non-finite STOPs intact; `exam_run.py:290–295`
  is the descriptive 2k/8k block at the pin.
- **Semantics PASS:** `probes(..., a3_short=False)` refuses (`ValueError`) before probe construction when
  `a3_short` is used without counters (v1 0/2k/8k path can never be shortened); with counters, flag-on
  records exactly `{"skipped":"R1-P3A-OOM-OPTION3","levels":[2000,8000],"pass":None}` and never calls the
  descriptive `E.a3_probe`/`_a3_rps`; A3 budget rows/A4/A5/A1/A2 unchanged; flag-off call-for-call and
  output-identical to the base (verified by loading both modules in one CPU process with identical stubs,
  for `counters=None` and a 4-fraction counters dict).
- **CLI PASS:** `--a3-short` only on `probes`, forwarded; refused (rc 2) without `--budget` or with
  `--tiny`, before config/env/GPU work.
- **Tests PASS:** `pytest r1/tests/test_trackp_p3a_a3_short.py -q` → 8 passed (repeated with a different
  hash seed); mutation checks (ignore flag / remove both guards / always skip) each fail the suite.
- **MINOR:** (1) test fixture uses one `frac 0.0` rather than all four `A3_FRACS` (statically guaranteed by
  `A3_FRACS=(0.0,0.25,0.5,1.0)`; optional fixture improvement); (2) `trackp.py:226` reads `args.tiny`
  directly (all subparsers add it today); (3) marker constant duplicated in the runner unit (values equal;
  runner fails closed on mismatch); (4) `e0 --with-probes` still calls `X.probes` without `a3_short` (not
  reachable in the authorized Unit B); (5) P.3a-report disclosure of the 2k/8k omission remains a Unit B /
  STOP-5 obligation.

**Safe to base Unit B on as the A3-short execution delta.** Unit B additionally needs the probes-only
runner accepted, delivery of the exact reviewed commit to TASL-7, and the run authorization.
