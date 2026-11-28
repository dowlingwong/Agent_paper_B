Verdict: CHANGES REQUIRED

# Independent tier-E re-check — D.3a P8 deepthought audit-host readiness

**Re-check of:** `5b737148db72d261501ae49764a3b2f6ba802348` on `compute-d3a-p8-host-20261128`.
**Base:** `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907` (unchanged).
**Previous delivery:** `99937b41c06f48758a4be199bfe977cc20db2d02`, reviewed in
`docs/r1/reviews/D3A_P8_HOST_REVIEW_20261128.md` (Verdict: CHANGES REQUIRED).
**Record:** `docs/r1/reports/d3a_p8_host_20261128/D3A_P8_HOST_20261128.md`, SHA-256
`72f2b9bdf65803c7b15f77acec13518bdad2048f7dac943e0eec1e273243ad17`.
**Review file:** this file. Its committed SHA-256 is recorded in the commit message and the reviewer's return.

The four requested corrections are present in the record and script and are arithmetically correct. One blocking defect
remains: `cotenancy.log`, the evidence file that `SHA256SUMS` and the record both bind, is not in the delivery. It is ignored by `.gitignore:3`
(`*.log`) and is absent from a clean checkout of `5b737148`; `shasum -c` therefore fails. The file is present only as
an untracked, ignored file in the preparer's worktree, which is why `shasum -c` passes there. This was also true at
`99937b41`: the first review ran `shasum -c` in that worktree and did not test the committed tree. The evidence set is
incomplete until the log is force-added, so the re-check does not accept.

## Finding

1. **`cotenancy.log` is not part of the delivery (blocking).**
   `git ls-tree -r 5b737148 -- docs/r1/reports/d3a_p8_host_20261128` lists only `D3A_P8_HOST_20261128.md`,
   `SHA256SUMS`, `host_env_harness.txt` and `p8_cotenancy.py`. `git check-ignore -v
   docs/r1/reports/d3a_p8_host_20261128/cotenancy.log` reports `.gitignore:3:*.log`. From a clean checkout of
   `5b737148`, `shasum -a 256 -c SHA256SUMS` returns `cotenancy.log: FAILED open or read` and exit 1; the other three
   entries are `OK`. In the preparer's worktree the same command returns all four `OK` because the ignored file is
   present there. The `SHA256SUMS` entry `4531be4f4254bfe63e031026d49d05e1cc6555e1a85c9c56fd94d119a198367e` matches that
   ignored file, so no hash change is needed once it is added. Fix: `git add -f
   docs/r1/reports/d3a_p8_host_20261128/cotenancy.log` (other `cotenancy.log` evidence files in this repository are
   tracked the same way), commit it, and re-run `shasum -a 256 -c SHA256SUMS` from a clean checkout of the delivery
   tip.

## The four corrections

| Previous finding | Status | Evidence at `5b737148` |
|---|---|---|
| 1. Co-tenancy formula and impossible values | fixed in the script; values correct | `p8_cotenancy.py:19` is `free = cpus - max(0.0, load - workers)`. Recomputed all 14 samples from the raw loads: pre-launch 5.93 → 34.07; during 6.82–15.65 → 40.00 in all 13 samples; all `ok`. The record table and result text match. The log file itself is finding 1. |
| 2. D.3a run-count expression | fixed | `126 instances × (10 start + 7 × 10 candidate)`, which evaluates to 10,080. |
| 3. HPO-REF row | fixed | `HPO-REF audit Y (126 × 2 × 10)` = 2,520 audit runs, 3.28 worker-h / 12 min. The note correctly separates the 5,040 HPO *worker* runs from the audit seed-run basis. |
| 4. B.2 report path | fixed | `docs/r1/reports/b2_audit_20261119/REPORT.md` exists; the report records 4,660 runs and a 1,364 s (22 min 44 s) wall time. |

## What I checked

- `git diff 99937b41..5b737148`: exactly three files changed — the record, `SHA256SUMS` and `p8_cotenancy.py`; no
  unrelated change.
- `shasum -c`: four `OK` in the preparer's worktree (where the ignored log is present); three `OK` and
  `cotenancy.log: FAILED open or read` in a clean checkout at `5b737148`.
- Recomputed all 14 co-tenancy samples with `40 - max(0, load1 - workers)`; no mismatch and every sample ≥ 10.
  The minimum is the pre-launch 34.07; every during sample is 40.00.
- Projection arithmetic, unchanged and correct: `1,364 s × 16 / 4,660 = 4.6833` worker-s/run; D.3a 10,080 →
  13.11 worker-h / 49 min; D.3b 2,520 → 3.28 / 12 min; 3,780 → 4.92 / 18 min; HPO-REF audit 2,520 → 3.28 / 12 min;
  secondary 13.11 × 3.6–7 = 47.2–91.8 worker-h, /16 = 2.95–5.74 h.
- Read-only SSH to `deepthought` at 2026-11-28T05:05Z: `deepthought`, 40 CPUs; Python 3.13.15, scikit-learn 1.8.0,
  NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1; harness `HEAD 9bb41680`, tree `c520138e`, clean, `uv.lock` `dd42d018…`;
  the six `git ls-tree` path ids match the record. The `host_env_harness.txt` capture is byte-identical to the first
  review (`fc571877…`).
- Scope and write-up: ENGINEERING_ONLY; no campaign, label or evaluation read is claimed; no reserved slot or completed
  campaign is claimed; code equality is still stated as by the shared commit, not a separate campaign deployment. No
  new path or hash error beyond finding 1.

## What I did not check

- I did not re-run the 65 s load; I recomputed the log values from its raw `load1` records.
- I did not launch a campaign or read any label, evaluation, campaign-ledger or audit output.
- I did not verify P7, the HPO-REF smoke, the intended GPU models, or the correctness of the `9bb41680` code beyond
  path/object identity.
- I did not modify the delivery branch, the host, or `main`.
