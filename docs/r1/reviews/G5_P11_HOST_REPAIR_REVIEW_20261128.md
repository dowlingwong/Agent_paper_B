# Independent tier-E review of the G.5 P11 host repair

Task `local/20261128-02` follow-up from `compute/20261128-09`. Base `989e8f22f0ef31349bf78762f6bfa40693668af4`.
Independent Codex reviewer `review_p11_repair` reviewed the code without writing it.

**Verdict: ACCEPTED** at `fd3099ed26576874c64a7bbf99f4bf70ec1e53f8`. There are no open findings.

- Extracted the exact harness classifier from `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`.
  Its `outcome.py` SHA-256 is `74f12f13cc9fac5e6704c07e4f804d50cd4f208fa2306137ea81a989c63db740`.
  Ran the base and candidate synthetic parents with isolated worker stubs at checksums 8 and 424.
  Both base cases reproduced `divergent/budget_not_reached`. Both candidate cases classified `ok` at
  `checksum / 4096`. The isolated result channel bytes matched base. Candidate stdout was `step 5\n`.
- Exercised the actual `g5_tasl.main` dispatch and both real close handlers with a synthetic `/proc`
  tree and scratch leases. Both commands refused a separate named worker PID, a live recorded PID,
  a wrong host and a held `flock`. Refusals wrote no receipt. With those checks satisfied the attempt
  handler wrote an infrastructure closure and the server handler wrote a `closed_at` record.
  The normal command-line scan and signed PLAN and note bytes matched base.
- `git diff --check` passed. The focused suite passed 109 tests with Python 3.11.5, clean desk harness
  `9bb416805175149eb87b71f28d77530572aa4bce`, fresh `TMPDIR` and `COPYFILE_DISABLE=1`.

```sh
python -B -m pytest -q -p no:cacheprovider -rfE \
  r1/tests/test_t1_g5_p11.py r1/tests/test_t1_g5_job.py r1/tests/test_t1_g5_seal.py
```

The tests used synthetic data without SSH. Actual TASL host coverage follows the reissued Compute matrix.
