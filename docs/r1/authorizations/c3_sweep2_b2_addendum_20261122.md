# Addendum to `c3_sweep2_20261119.md`: B.2 fresh-seed audits of sweep 2 (approved: true)

**Signed: published with `approved: true` by the coordinating chat on 22 November 2026 under the author's pre-authorization in R1-SWEEP2-B2-DECISIONS (filled addendum independently reviewed, `reviews/S2_B2_ADDENDUM_REVIEW_20261122.md`).** Prepared by the cluster agent
(AI-assisted) on 22 November 2026 under R1-SWEEP2-SETTINGS (2), R1-SWEEP2-B2-DECISIONS D1–D6 and the proposal
`proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md`. Host: deepthought, in the environment of the sweep-1 B.2 audit
(D1 A); harness `6adf3859` with the run-time equality check against `a3fedbbd` (D2 A); the e1 replay is the environment
basis (D3 A); a non-finite seed run is a STOP (D4 A); the batch and table were extracted and built on deepthought from
the reviewed code commit (D5); the worker-runtime probe with its limitation (D6 B4 (a)). The start row
`R1-SWEEP2-B2-GO` is published together with this addendum. R1-B2-DECOUPLE's "does not start" is lifted for this audit
only. No label or evaluation file was read to fill this addendum. On signature the coordinating chat flipped the key to `approved: true` and updated this heading/prose only; the reviewed facts and pins are unchanged.

```
approved: true
label: EVIDENCE
phase: c3_sweep2_b2
sweep2_run_id: s2ev-20261119-a
start_ruling: R1-SWEEP2-B2-GO
sweep2_index_sha256: b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4
sweep2_extract_sha256: 82c7605291cc07d5d06dc610c6f9a34e6e8d417e62cadb7de7ca59d7b103a4da
table_proposals_sha256: 379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9
table_configs_sha256: de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d
precondition2_review: docs/r1/reviews/S2_AUDIT_PRECONDITION2_REVIEW_20261122.md
parent_authorization: docs/r1/authorizations/c3_sweep2_20261119.md (sha256 349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a)
```

**Scope.** One complete EVIDENCE audit of the sweep-2 batch `s2ev-20261119-a`: every eligible proposal of both memory
modes and all eight nodes, with K = 10 fresh joint seeds, label seeds 7001–7005 and evaluation seeds 7006–7010. The
`openml_wdbc` sensitivity row of R1-S2C3B-WDBC is audited like every node; the analysis scope is the preregistration's.
Not authorized: training, tuning, threshold choice or selection on 7006–7010; any resume of a stopped audit; any other
batch.

**Pins.**

| Item | Value | Source |
|---|---|---|
| Paper code | `db7f344d6ac372737444db5ab036d370543ea65f` (accepted commit of `mac-s2-audit-20261121`), detached, `docs/` authority from published `main`, `r1/` clean | precondition 1 |
| Code review | `docs/r1/reviews/S2_AUDIT_UNIT_REVIEW_20261121.md` (`Code-Commit:` / `Verdict: ACCEPTED`) | precondition 1 |
| Harness | `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean at the e1 path; untracked files only as the e1 record; node, config, harness and worker code equal to `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (checked at run time) | D2, R1-B2-GO |
| Environment basis | R1-B2-GO B6 (a): the e1 replay report and its review; current-environment checks at audit start (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, `uv.lock` `dd42d018…`) | D3 |
| Worker runtime | R1-B2-GO B4 (a): per-run probe; its limitation is disclosed | D6 |
| Sweep-2 batch | index `b4697c…`, `EXTRACT.json` `82c760…` (files 594); collection counts `3e29382b4d31cef54b92d0cf77a0819b5dedda92aedd528b708f5030b88b6ec7`; sealed tree `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a` | precondition 2 |
| Table | `proposals.jsonl` `379b17ca…`, `configs.json` `de6d63b5…`, built from the index without a classification sidecar; the audit rebuilds the table and refuses any difference | precondition 2 |
| Audit design | K = 10; label seeds 7001–7005 and evaluation seeds 7006–7010; duplicates get no label; no-ops labelled by rule; completion schema `r1.c3_audit_completion/4`, `source: sweep2` | R1-B2-DECOUPLE, R1-SWEEP1-CLASSIFY |
| Expected population | **2,500 eligible, 2,512 duplicates, 0 no-ops; 1,064 unique configurations, 10,640 seed runs** | `sweep2_batch counts` |
| Precondition-2 review | `docs/r1/reviews/S2_AUDIT_PRECONDITION2_REVIEW_20261122.md` (`Verdict: ACCEPTED`, four pins) | precondition 2 |

**Host, resources and command.**
- deepthought, CPUs only, in the e1-replayed batch venv; 16 workers, at least 10 of 40 cores free (checked before
  launch; fewer workers only with the number recorded). This co-tenancy rule is the operator protocol recorded in
  `cotenancy.log`; a breach during the run is a STOP.
- New scratch `/tmp/r1_c3_audit_EVIDENCE_<stamp>`; new output `results/r1/evidence/C3_audit_EVIDENCE_<stamp>`; Ceph
  ≥ 50 GiB free and the operator's file-count reserve.
- Projection: `T = 10,640 / 4,660 × 23 min ≈ 52.5 min` at 16 workers plus setup/verification (hashing the sealed
  `work/` trees and rebuilding the table); deadline `max(10,800 s, 2.5 × T) = 10,800 s` (2.5 × T ≈ 7,877 s).
- Command, from the paper checkout at the code commit in the batch venv, `AR_HARNESS_ROOT` = e1 batch harness,
  batch wrappers first on `PATH`, `PYTHONDONTWRITEBYTECODE=1`, no batch `env.sh` `PYTHONPATH`:
  `python -B -m r1.c3.audit evidence-run --source sweep2 --table <host table> --paper-root <checkout> --index <index> --out results/r1/evidence/C3_audit_EVIDENCE_<stamp> --workers 16 --deadline 10800 --code-commit db7f344d6ac372737444db5ab036d370543ea65f --code-review docs/r1/reviews/S2_AUDIT_UNIT_REVIEW_20261121.md --addendum docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md --scratch-root /tmp/r1_c3_audit_EVIDENCE_<stamp> --required-scratch-bytes 17179869184 --ceph-reserve-files 2000`.
- The code reads this addendum and the start row from `origin/main`; it refuses unless `approved: true`, the four pins
  equal the index/`EXTRACT.json`/table used, the precondition-2 review is on `origin/main` with `Verdict: ACCEPTED`
  and the four pins, and `R1-SWEEP2-B2-GO` is exactly one author row naming the run id, R1-SWEEP-HOST-HTC,
  R1-B2-DECOUPLE and B6 (a), B4 (a), B1 (a).

**Precondition 3: harness objects.** Fetch `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` into the batch harness repository (`git fetch origin a3fedbbd…`, objects only; the worktree and its untracked e1 state stay unchanged). The audit checks that both commits are present and that the listed node/config/harness/worker/audited-library paths are equal.

**Pass rule.** Every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and
incumbent; both blocks are written and match recomputation; `evidence_completion.json` (schema `/4`, `source: sweep2`)
binds the batch, table, plan, blocks, environment, sweep-2 authorization and this addendum; counts by kind equal the
plan's. Labels count only after an independent review of the run and the author's label-table freeze.

**STOPs.** Retain everything; there is no automatic resume.
- Any guard failure: the four pins/counts or the table differ from this addendum; the start row or authority bytes differ on `origin/main`; the precondition-2 review is missing or changed; the code review is missing; the D8/start-row guards refuse.
- Harness-equivalence difference; an untracked harness file outside the e1 record; a current-environment check differing from the e1 replay basis.
- Resource or co-tenancy breach (the 16-workers/≥10-free-cores rule is the operator protocol recorded in `cotenancy.log`; a breach is a STOP).
- Any failed, missing, non-finite or file-changing seed run; the deadline passes; an interruption; any use of 7006–7010 outside the evaluation block.
