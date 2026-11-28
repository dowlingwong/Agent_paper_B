# Independent tier-E review of D.3 pre-declaration revision 6

**Verdict — ACCEPTED.** Reviewed the unsigned draft at
`280038a3bd3ac0424b2b3228770b6112d3a5abdc` on published base
`4196ec47171c4513b5905cc0c2f4d5d77691b621` for `local/20261128-18).
The TASL-2 environment replacement matches R1-D3-REV6 and the production route
record published through `c66603ae`. [PLAN §10](../PLAN.md#10-open-decisions) ·
[Production route record](../reports/d3a_production_route_20261128/D3A_PRODUCTION_ROUTE_20261128.md)

## Checks

- Compared the complete frozen rev 5 and draft rev 6 line by line and checked
  their bytes against Git. The six changed line groups cover the title and
  status, the changelog, the §2 environment row, the §7.2 host disclosure, the
  §10 campaign STOP clause and the §14 revision and draft state fields. The
  frozen rev 5 bytes are identical to the base. The 18.53% worker-failure STOP,
  seed blocks, contrasts, harness, constants and analysis pins are preserved.
  [Frozen revision 5](../authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md) ·
  [Revision 6 draft](../authorizations/D3_PREDECLARATION_DRAFT_20261128_R6.md)
- Matched Python 3.11.17, the resolved executable and both SHA-256 digests to
  the sealed engineering environment capture. Matched the venv invocation and
  the shim path to the driver at `c66603ae`, including its `PATH` and
  `PYTHONPATH` settings. Verified the environment capture against its nested
  SHA-256 manifest and the nested manifest against the route manifest.
  Confirmed the capture bytes remain identical at the published base.
  [Environment capture](../reports/d3a_production_route_20261128/captures/environment_20261128.txt) ·
  [Capture manifest](../reports/d3a_production_route_20261128/captures/SHA256SUMS)
- Confirmed that the deepthought audit remains on Python 3.13.15 and compared
  the four package versions to the recorded campaign environment. Both use
  scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3 and SciPy 1.17.1. The campaign
  STOP covers a mismatch in the §2 environment and preserves the other frozen
  STOP criteria.
- Confirmed the draft records `frozen: false`, `approved: false` and pending
  signature and freeze time. `git diff --check` passed. This documentation
  review used published engineering metadata and read no sealed evidence
  partition. The reviewed change is one Markdown file.

## Finding and re-check

The original tip `2d6c414f` stated the direct route and retained the inherited
placement summaries. The re-check at `280038a3` verified that the §2 row now
explicitly governs the proposer-host check and §14 placement summary. The
§6 campaign-image reference resolves to the shared environment in §2. The
D.3b sidecar choice remains open under its original terms. The minor wording
finding is closed.

| Object | SHA-256 |
|---|---|
| Frozen revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Reviewed revision 6 draft | `f4114d372c153fd3daf31819cf157adb9c9dc4df1d82538ec0597a77db5027e7` |
| Published environment capture | `3637c4c615d96da8b7aaf18fd2bc51bdb941c42f95fc957bf65b22e006152d21` |
| Campaign Python executable | `ff9b2ac4362b81c68622ffb1730f7138eb269177d9846399c521a44c5daffb0e` |
| Audit-package shim tree | `1737028cdd5868c30d331e6f80133e5ec3b1c76f3d4f95df9de960d67370ef07` |

Present the reviewed diff for the author's signature. The coordinator then
freezes it. Step (8) binds the frozen rev 6 digest in the D.3a note and outcome
headers before campaign launch.
