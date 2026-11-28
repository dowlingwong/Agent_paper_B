Verdict: ACCEPTED

# Independent tier-E final re-check — D.3a P8 deepthought audit-host readiness

**Re-check of:** `4fb1fae3b49ca64698eac51369c6a97dbf26611d` on `compute-d3a-p8-host-20261128`.
**Previous deliveries:** `5b737148db72d261501ae49764a3b2f6ba802348` (reviewed in
`D3A_P8_HOST_RECHECK_20261128.md`, CHANGES REQUIRED) and `99937b41c06f48758a4be199bfe977cc20db2d02` (first review,
CHANGES REQUIRED).
**Base:** `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907` (unchanged).
**Record:** `docs/r1/reports/d3a_p8_host_20261128/D3A_P8_HOST_20261128.md`, SHA-256
`72f2b9bdf65803c7b15f77acec13518bdad2048f7dac943e0eec1e273243ad17`.
**Review file:** this file. Its committed SHA-256 is recorded in the commit message and the reviewer's return.

I accept the delivery. The only blocking finding of the previous re-check — `cotenancy.log` was ignored by
`.gitignore` and absent from the committed tree — is fixed. `git diff 5b737148..4fb1fae3` contains exactly one
addition, `docs/r1/reports/d3a_p8_host_20261128/cotenancy.log` (14 lines), and nothing else. The log is now tracked
at blob `b2ba4cbffd94e20b225e7b0de098e9648a855659`; its file SHA-256 is
`4531be4f4254bfe63e031026d49d05e1cc6555e1a85c9c56fd94d119a198367e`, equal to the `SHA256SUMS` entry. A clean
detached checkout of `4fb1fae3` (not the preparer's worktree) passes `shasum -a 256 -c SHA256SUMS` on all four
entries.

## Verification of the final tip

- `git ls-tree -r 4fb1fae3 -- docs/r1/reports/d3a_p8_host_20261128` now lists the five files: the record,
  `SHA256SUMS`, `cotenancy.log`, `host_env_harness.txt` and `p8_cotenancy.py`.
- Clean checkout: `cotenancy.log: OK`, `host_env_harness.txt: OK`, `p8_cotenancy.py: OK`,
  `D3A_P8_HOST_20261128.md: OK`; exit 0.
- Recomputed all 14 samples from the tracked log against `40 - max(0, load1 - workers)`: pre-launch 5.93 → 34.07;
  during 6.82–15.65 → 40.00 in all 13 samples; every sample `ok` and ≥ 10; zero mismatches.
- The four earlier corrections remain in place and unchanged from the previous re-check: the script's formula
  (`p8_cotenancy.py:19`), the D.3a expression (`126 × (10 start + 7 × 10 candidate) = 10,080`), the HPO-REF audit
  row (`126 × 2 × 10 = 2,520` runs, 3.28 worker-h / 12 min, with the 5,040 worker runs separated), and the B.2
  path (`docs/r1/reports/b2_audit_20261119/REPORT.md`).
- The record (`72f2b9bd…`), script (`9dec37f6…`) and host/environment capture (`fc571877…`) have the same hashes as
  in the previous re-check; the final commit changes no content other than adding the log.
- The record remains ENGINEERING_ONLY: no campaign, label or evaluation read; no reserved slot; no completed
  campaign; harness equality is stated as by the shared campaign commit, not a separate deployment.
- The previously verified host facts (deepthought, 40 CPUs, Python 3.13.15, scikit-learn 1.8.0 / NumPy 2.4.4 /
  pandas 3.0.3 / SciPy 1.17.1, `uv.lock` `dd42d018…`, harness `HEAD 9bb41680`, tree `c520138e…`, clean, and the
  six path ids) are unchanged in the capture and were re-read read-only on the host during the previous re-check.

## What I did not check

- I did not re-run the 65 s load; I recomputed the tracked log's values from its raw `load1` records.
- I did not launch a campaign or read any label, evaluation, campaign-ledger or audit output.
- I did not verify P7, the HPO-REF smoke, the intended GPU models, or the correctness of the `9bb41680` code beyond
  path/object identity.
- I did not modify the delivery branch, the host, or `main`.
