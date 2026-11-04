# M11 independent early review — frozen prototype v2 (4 November 2026)

AI-assisted independent review by Codex. **Verdict: NOT ACCEPTED for M11 or B.7.** This review covers the frozen prototype `/private/tmp/paper-b-m11-review-v2-20261104`, based on `c76b38d`, against the Mac runbook M11, PLAN R1-BX-D7/D8/D13 and R1-BX-PROPOSED-CONFIRM. No real label data, model, GPU, remote host or Slurm was used. The review is an early assessment, not acceptance of this work, prior runs or author authorization.

## Blocking: required analysis readers remain unguarded

The four new modules do not change the existing `dataset`, `offline_eval`, `ni_masking`, and Track P readers. For example, `r1/c3/offline_eval.py:130-158` reads audit rows, and its existing `gate_verdict()` still produces the superseded per-node verdict. The proposed `load_sweep2_jsonl` is an opt-in helper and has no authority over those paths. Therefore there is no demonstrated guard before all sweep-2 label reads, no reliable sweep-1/sweep-2 source classification, and the legacy gate must not be used for B.7. Supply an audited source/provenance strategy and wire every relevant entry point with tests that check no label bytes are opened before the real decision row. Changes in shared or separately owned files must follow their ownership and review rules.

## Blocking: caller-controlled PLAN path is not author authority

`require_gate_confirmation(plan=...)`, `aggregate_gate(..., plan=...)`, `load_sweep2_jsonl(..., plan=...)` and `offline_welch_values(..., plan=...)` accept an arbitrary file path as the authority. The tests themselves create a temporary PLAN containing the current SHA and pass it in; any caller can do the same while the actual committed PLAN lacks the row. Checking the first cell and SHA is useful, but a user-provided local file does not prove a dated, author-committed decision. For a production reader bind the decision to the authoritative committed PLAN and protect the exact bytes and commit, with any test-only injection isolated from runtime entry points. A changed or uncommitted counterfeit row must fail. This is a safeguard defect even though the present call sites are only prototypes.

## Major: gate estimates and inference are not yet validated

`gate.py` correctly reports `verdict: NOT_AVAILABLE`, and eligibility is based on dev thresholds while excluded nodes remain in PoI; the synthetic fixtures exercise ties, fractional IQM and stable input ordering. But the proposed bootstrap p-value expression simplifies algebraically to the fraction of bootstrap point estimates at or below the null (e.g. `v - point <= -point` is `v <= 0`), despite being named "centered-bootstrap". It has not been demonstrated to be a calibrated one-sided null p-value or consistent with percentile bounds used in Holm ranking; the non-symmetric case and sequential Holm edge cases need reference tests and a predeclared treatment. The code also lets callers choose arbitrary `n_boot` despite the confirmed 2,000-resample protocol, and has no independently verified oracle or dev/test split provenance. Confirm the inference protocol and add a synthetic/reference comparison before using a statistical result. Resamples with nonpositive test oracle gap currently stop the entire calculation; determine and document a predeclared treatment rather than silently dropping them. These are WIP findings, not claims that existing published analyses are wrong.

## Major: train-only PCA and no-sealed-path checks trust caller statements

`MatchedView.fit` checks only a caller-provided `split == 'train'` marker; it does not bind rows or embeddings to a verified training partition or check for overlapping instances. A mislabeled test row passes. Require provenance and group/partition checks at the actual data assembly boundary; the synthetic assertion only demonstrates that explicitly marked `test` is rejected. `load_sweep2_jsonl` rejects a resolved path whose components include `r1_sealed`, but a copied or hard-linked sealed file outside that path can pass; exact source and approved analysis-copy provenance need separate verification. The worker explicitly identifies these components as unintegrated, so no release claim should be inferred.

## Other incomplete work

The standalone Welch function performs one-sided r=3 on independent samples, charges six runs and refuses a too-small budget. Whether existing incumbent measurements may be reused and their accounting are open. It is neither a complete offline arm nor integrated with the online controller; source/seed provenance is unverified. A0's `rho` should be checked under the actual main-table semantics before relabeling. The matched view has no pinned embedding provider, TabPFN regression API adapter, predictive distribution evaluation or class-cap record. No model should be loaded locally for these checks. The protective SHA must be finalized only after the implementation and independent review; the supplied SHA is not a confirmation pin.

## Frozen hashes and independent tests

- `r1/c3/gate.py`: `35714127cc15959d71a53576b8279754be9f997eae8a408ebb5dfc5c64ef0d37`
- `r1/c3/guarded_labels.py`: `e7543da5bafe5e16fe031323e4585842cd1a824def2b6f3674ac49f3dd645870`
- `r1/c3/matched_view.py`: `a3e9d1cf88a1517873eadb6fd6580afbf182d051d9e686993bc2dbc9e7938e98`
- `r1/c3/practitioner.py`: `3d73067f7b67e1665acac1fc29ba633a5e1db176d03f412e92091e6f668008da`
- `test_c3_aggregate_gate.py`: `d5c2b410c3ebf1c691ffa01fb5cca9a9ed25c9b9bb9cacc93806b3afe02a87bf`
- `test_c3_guarded_labels.py`: `1e27ab9116e49d57086880dc1da32740e6abbfc87df2d541c0fcb25dcb4ce548`
- `test_c3_matched_view.py`: `806a415ccccf05db9a275c5dcf33c6310c22970b6ae5af633dcde14d8b3e12e5`
- `test_c3_practitioner.py`: `6562433b9ab2ae38cca718b4cb730f2aa28288d49c48b4699881ef2ec8309a10`

The eight worker-working-tree files were byte-compared to the snapshot immediately before testing. `PYTHONDONTWRITEBYTECODE=1 /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q -p no:cacheprovider` on these four test files: **13 passed**. Tests exercise synthetic fixtures only and do not establish provenance, a live gate, or operational readiness. No code or source artifact was modified in the reviewer checkout.

## Same-reviewer re-check of frozen v3 — accepted only as a disabled synthetic draft

The same independent reviewer inspected `/private/tmp/paper-b-m11-review-v3-20261104` and independently ran the four synthetic test files using Python 3.11 from the local harness venv, with bytecode and pytest cache disabled: **11 passed**. All eight files in the worker tree were byte-compared with the snapshot immediately before tests. No real label, model, GPU or remote host was accessed.

- The caller-controlled PLAN bypass has been contained in the new entry points: `require_gate_confirmation()` unconditionally STOPs, and `aggregate_gate`, `load_sweep2_jsonl` and `offline_welch_values` stop before iterating or opening supplied inputs. This is a deliberate disabled stub, not a verified implementation of a committed author gate. No claim is made that old readers are protected.
- `MatchedView.fit` unconditionally stops before consuming rows or embeddings; this contains the unverified training-provenance issue but does not implement D13. The unsafe prototype bootstrap and provisional verdict have been removed; the required aggregate statistic and its inference are not implemented. Sealed provenance and source classification remain open.
- **Residual boundary:** public `welch_replicates` consumes supplied numeric samples and returns a keep decision without a PLAN or provenance check. It does not itself open a label table, but a caller could use it on real observations. Accept it only as a standalone synthetic engineering calculation; any integration with sweep-2 or other evidence data must be guarded before data are read and independently reviewed. The private `_summaries` and CDF helpers are also calculations, not analysis authorization.
- Existing `dataset`, `offline_eval`, `ni_masking`, and Track P readers remain unguarded. The old per-node gate remains present. The new disabled helpers must not be represented as guarding those paths. The frozen status is **M11 NOT READY; B.7 NOT READY**. A future usable implementation needs authenticated author decision provenance, verified source/split/oracle, accepted inference, all-reader integration, and a fresh review of the actual final bytes.

Frozen SHA-256 values:

| File | SHA-256 |
|---|---|
| `r1/c3/gate.py` | `4b9e06f0876b51d8e7b0c631b656d25b4840b059cc2ac0fe0021b505fb246d6a` |
| `r1/c3/guarded_labels.py` | `146dbf270575b877287fd8beb86087a9af8d2191fee6cdcdfba0af38721a8ee2` |
| `r1/c3/matched_view.py` | `5ef47720c790199ca37af86557a4bc5b9eef9f97bcf920975b483a211fdd1579` |
| `r1/c3/practitioner.py` | `274ba4d09abb4c6c7854b70d7ec84bcba1704f98b028dbd81e3c84e0137373aa` |
| `r1/tests/test_c3_aggregate_gate.py` | `503457c21e03cd67dc512c453a67fd4c7fc141e0292271dde0329ab9df55c5fc` |
| `r1/tests/test_c3_guarded_labels.py` | `fdb8d15a0fd9576b968dd065721b7fd5c01d2b8483749c75f3b38098e364f94d` |
| `r1/tests/test_c3_matched_view.py` | `d33a9b4124ab150dfad87874b0007f5daebcf19e1532f3de791c1b8a3bcc2b6e` |
| `r1/tests/test_c3_practitioner.py` | `8a5162b699353617400bb1d03b6542ddc9b0142236c1a7009679a222d8df6297` |
