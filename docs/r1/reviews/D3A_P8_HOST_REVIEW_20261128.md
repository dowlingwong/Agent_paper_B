Verdict: CHANGES REQUIRED

# Independent tier-E review — D.3a P8 deepthought audit-host readiness

**Task:** `compute/20261128-11` item 3 (D.3a P8 deepthought audit-host readiness).
**Reviewed delivery:** `99937b41c06f48758a4be199bfe977cc20db2d02`, branch `compute-d3a-p8-host-20261128`.
**Base:** `origin/main` `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907` (the delivery's parent; `git merge-base` is the base).
**Record:** `docs/r1/reports/d3a_p8_host_20261128/D3A_P8_HOST_20261128.md`, SHA-256
`d7a0375d38d93c8962908c4e0b7b6a5ceb82bbf0dfde1483ba7c10e07cc046ab`.
**Captures:** `host_env_harness.txt`, `cotenancy.log`, `p8_cotenancy.py`, `SHA256SUMS` in the same directory.
**Review file:** this file. Its committed SHA-256 is recorded in the commit message and the reviewer's return; a file
cannot carry its own final digest without changing it.

The host facts are reproducible and the P8 conclusion is supportable: the e1 interpreter and packages match, the audit
checkout is the declared clean D.3 pin with the declared path ids, the shared commit makes the campaign/audit code
identity hold by construction, and every co-tenancy sample leaves at least 10 of 40 cores free (pre-launch 33.81; during
at least 39.70). I nevertheless do not accept the record as delivered: its co-tenancy field does not implement the
convention it quotes and contains impossible values, and two projection labels do not state the quantities they
multiply. These are evidence-accuracy defects in a record whose purpose is to be cited for P8, so they need correction
and a regenerated `SHA256SUMS` before acceptance.

## Numbered findings

1. **The co-tenancy field does not follow the accepted convention and reports impossible capacity.** The record quotes
   the convention `free_for_others = 40 - max(0, load1 - 16)` (`D3A_P8_HOST_20261128.md` line 46), but
   `p8_cotenancy.py:19` computes `free = cpus - (load - workers)`, i.e. `40 - load + 16` during the run. From the raw
   `load1` values in `cotenancy.log`, 12 of the 13 `during` samples are wrong: they report 48.86, 47.67, 46.73, 45.63,
   44.78, 43.92, 43.53, 42.76, 42.06, 41.41, 40.74 and 40.20 "cores left to other users" on a 40-CPU host. Only the last
   sample (load 16.30 ⇒ 39.70) agrees with the convention. The record's table repeats the impossible high value
   (`48.86 → 39.70`). The two formulas coincide for load ≥ 16, so the `ok` flag is not wrong here; the defect is that
   the recorded `free_for_others` field is not the accepted quantity and exceeds the host's 40 CPUs. For the 16-worker
   phase the convention gives 40.00 for the first 12 samples and 39.70 for the last; the pre-launch sample (0 workers)
   is `40 - 6.19 = 33.81`. All are ≥ 10, so **the host conclusion is unchanged**, but the delivered log is not the
   accepted evidence. Fix the formula, regenerate the 65 s sample (or recompute the derived field from the raw loads
   with the discrepancy disclosed), correct the table to `40.00 → 39.70`, and regenerate `SHA256SUMS`.

2. **The D.3a run-count expression is an arithmetic error even though its total is right.** The row reads
   `7 arms × 126 instances × (10 start + 70 candidate)`. Literally that is `7 × 126 × 80 = 70,560`, not 10,080. The
   declared design is `126 × (10 start + 7 × 10 candidate) = 126 × 80 = 10,080`
   (`D3_PREDECLARATION_DRAFT_20261122.md` §11, line 733). The 10,080 is correct; the expression double-counts the seven
   arms. Write it as `126 instances × (10 start + 7 arms × 10 candidate)`.

3. **The HPO-REF row mixes the worker-run count with the audit-run basis.** 5,040 is the HPO-REF **worker** count
   (`2 methods × 20 charged worker runs × 126 instances`; §11 line 738), not the audit count. The audit projection in
   §7.2 is `2,520` HPO-REF audit runs ≈ 3.3 worker-h / 12 min (§11 line 734). The record applies the B.2 **audit**
   seed-run basis (4.68 worker-s/run) to the 5,040 worker runs. The arithmetic `5,040 × 4.683 / 3,600 = 6.55` and
   `6.55 / 16 = 24.6 min` is right, but the row is not the same quantity as the other audit rows. Use 2,520 audit runs
   (3.28 worker-h / 12 min) in the audit table; if the HPO worker CPU is intended, label it separately and derive its
   per-run figure from the HPO-REF smoke or measured worker times, not from the audit basis. This does not change the
   P8 host conclusion.

4. **One cited path does not resolve.** The projection basis cites `reports/b2_audit_20261119/REPORT.md`
   (`D3A_P8_HOST_20261128.md` line 58). The file is `docs/r1/reports/b2_audit_20261119/REPORT.md`; the cited path does
   not exist from the repository root. The report's facts are correct (4,660 runs; 00:27:38Z → 00:50:22Z = 1,364 s =
   22 min 44 s), but the path must be exact.

## What I checked independently

- `shasum -a 256 -c SHA256SUMS` in the record directory: all four entries `OK`; the record's SHA-256 is the
  `d7a0375d…` above.
- Read-only SSH to `deepthought` as `dwong` (2026-11-28T04:57–04:59Z; no writes, no host changes):
  - `deepthought`, `nproc` 40, `MemTotal` 503 GiB, 457 GiB available — matches the record.
  - `/ceph/dwong/r1_prepare_20261025/venv/bin/python`: Python 3.13.15; scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3,
    SciPy 1.17.1 — matches.
  - `/work/dwong/d3-audit-harness-20261128`: `HEAD = 9bb416805175149eb87b71f28d77530572aa4bce`, tree
    `c520138e36ae46d6fb27715ff3a37748d5324ad8`, `git status --porcelain` empty, `uv.lock` SHA-256
    `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` — matches.
  - `git ls-tree` at that HEAD: `configs` `7f8de4ed…`, `src/autoresearch/nodes` `711ba50d…`,
    `src/autoresearch/worker` `563e7afd…`, `src/autoresearch/evaluation` `36c2c347…`, `src/autoresearch/llm`
    `85c96dac…`, `src/autoresearch` `e574c7d3…` — all six match the record. `git diff 9bb41680 9bb41680 -- configs
    src/autoresearch/nodes src/autoresearch/worker` is empty.
  - The e1 batch copies under `/ceph/dwong/r1_prepare_20261025/` (`autoresearch_harness/uv.lock` and the four
    `r1_c3_sweep_ENGINEERING_ONLY_*` copies) all have `uv.lock` SHA-256 `dd42d018…`, supporting "identical in the audit
    checkout and the preserved e1 batch".
  - The campaign pin `9bb41680` is bound by `D3_PREDECLARATION_DRAFT_20261122.md` §2, and the v1 image
    `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…` with Python 3.13.18 vs audit 3.13.15 is the disclosed difference
    in PLAN `R1-SWEEP2-B2-DECISIONS` D3 A and §7.2(4).
- Co-tenancy: recomputed the pre-launch sample with `40 - load1` (0 workers) and the during samples with
  `40 - max(0, load1 - 16)`. Pre-launch 33.81; during 40.00 for loads 7.14–15.80 and 39.70 at 16.30. All ≥ 10. The
  reported field is wrong for 12 of the 13 during samples, as finding 1 records.
- Projection, recomputed from the stated basis: `1,364 s × 16 / 4,660 = 4.6833` worker-s/run. D.3a 10,080 →
  13.11 worker-h / 49.2 min; D.3b 2,520 → 3.28 / 12.3 min; 3,780 → 4.92 / 18.4 min; HPO-REF 5,040 → 6.55 / 24.6 min;
  secondary 13.11 × 3.6–7 = 47.2–91.8 worker-h, /16 = 2.95–5.74 h. The record's rounded figures (13.11, 49 min, 3.28,
  12 min, 4.92, 18 min, 6.55, 25 min, ≈47–92, ≈3.0–5.7 h) are arithmetically correct; findings 2 and 3 concern the
  quantities labelled, not the multiplication.
- Scope: the record says ENGINEERING_ONLY, no campaign, no proposal audit, no label or evaluation read. It does not
  claim a reserved slot ("it is a projection, not a reserved slot") and does not claim a completed campaign. The 16
  workers were a 65 s load test, not a campaign. `pgrep` on the host found no Paper B audit process (only the system
  `auditd`/`kauditd`).
- Write-up: the record does not assert that the campaign harness was separately deployed; it says the campaign pin is
  the same commit, so the code is identical by construction, which is the correct basis. The path in finding 4 is the
  only citation that does not resolve.

## What I did not check

- I did not re-run the 65 s co-tenancy load or otherwise load the host; I recomputed the log from its raw `load1`
  values only.
- I did not launch a campaign or a proposal audit, and I did not read any label, evaluation, campaign-ledger or audit
  output.
- I did not verify P7, the HPO-REF smoke, the intended GPU models, or the correctness of the `9bb41680` code beyond
  path/object identity.
- I did not independently inspect the installed SciPy in the v1 campaign image; I relied on the shared `uv.lock` and the
  B.2/PLAN records for the "same versions" statement.
- I did not re-run the e1 replay; I relied on the published addendum for its 16/16 result.
- I did not modify the delivery branch, the host, or `main`.
