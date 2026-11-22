# Sweep-2 B.2 audit — precondition 2 output (D5), 22 November 2026

ENGINEERING_ONLY. No label or evaluation file was read. Working host: deepthought; paper checkout at the reviewed code
commit `db7f344d6ac372737444db5ab036d370543ea65f` (clean detached checkout; its `docs/PLAN.md` already carries
R1-BX-D8-CONFIRM-V31, so the D8 guard passes without an overlay at this step). Batch venv:
`/ceph/dwong/r1_prepare_20261025/venv`; `AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`
(e1 harness at `6adf3859`); `PYTHONDONTWRITEBYTECODE=1`; no `env.sh` PYTHONPATH.

Commands (run from the checkout):

```
python -B -m r1.c3.sweep2_batch extract --sealed /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a --paper-root <checkout>
python -B -m r1.c3.dataset build-sweep --index <checkout>/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json --paper-root <checkout> --out /work/dwong/s2_audit_20261122/table
python -B -m r1.c3.sweep2_batch counts --table /work/dwong/s2_audit_20261122/table
python -B -m r1.c3.sweep2_batch verify --index <index> --paper-root <checkout> --sealed /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a
```

Outputs (all rc 0; full logs in this directory):

| Value | Result |
|---|---|
| `sweep2_index_sha256` | `b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4` |
| `sweep2_extract_sha256` | `82c7605291cc07d5d06dc610c6f9a34e6e8d417e62cadb7de7ca59d7b103a4da` |
| `table_proposals_sha256` | `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` |
| `table_configs_sha256` | `de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` |
| batch files | 594 |
| counts | **eligible 2,500; duplicates 2,512; no-ops 0; proposals 5,012; unique configurations 1,064; seed runs 10,640** |
| `verify --sealed` | **`sealed_rederivation: equal`**; collection counts `3e29382b…b6ec7`; run id `s2ev-20261119-a` |
| build | `build.json` sha256 `bbb2a95cef1edfb1e3767eb66b841c54626235b1e3b719529e4b53f37d3dda92`; table in a new directory (created fresh) |
| projection | 10,640/4,660 × 23 min ≈ 52.5 min at 16 workers; deadline `max(10,800 s, 2.5×T)` = **10,800 s** (2.5×T ≈ 7,860 s) |

`EXTRACT.json` and the index are included here; the table itself (7.5 MB `proposals.jsonl`) stays on deepthought and is
bound by its sha256. Batch index `b4697c…` and extract `82c760…` match the values in `verify.log`.
