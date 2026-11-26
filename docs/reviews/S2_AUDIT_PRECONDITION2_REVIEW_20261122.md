# Independent precondition-2 review — sweep-2 B.2 audit output (D5): batch, table, counts, `verify --sealed`

Reviewed base: `9c2979a2` (published `main`). Output commit: `dcb74c94` on `s2-audit-addendum-20261122`
(worktree `.claude-worktrees/s2-audit-addendum-20261122`; only the five precondition-2 files are added).
Code under test: `db7f344d6ac372737444db5ab036d370543ea65f` (accepted at `db7f344d` by
`docs/r1/reviews/S2_AUDIT_UNIT_REVIEW_20261121.md`; `r1/c3/sweep2_batch.py`, `r1/c3/audit.py`, `r1/c3/dataset.py`,
`r1/c3/analysis_guard.py`, `r1/c3/release_checks.py` are byte-identical at `db7f344d`, `9c2979a2` and `dcb74c94`).
Reviewer: independent reviewer (`reviewer-s2-precond2`), read-only. Date: 22 November 2026.

**Scope.** `docs/r1/reports/s2_audit_20261121/PRECONDITION2_20261122.md` and its `precondition2/` directory
(extract.log, build.log, counts.log, verify.log, `C3_sweep2_index_s2ev-20261119-a.json`, `EXTRACT.json`,
`build.json`, `SHA256SUMS`), against the live artifacts on deepthought and the code at `db7f344d`. This review may
be cited in the addendum key block as `precondition2_review`. ENGINEERING_ONLY: no write was made to the repository,
git, or deepthought; no sweep-2 label exists or was opened.

**Method.** Recomputed every sha256 from the bytes (both the checked-in copies and the files on deepthought);
re-ran `counts` and `verify --sealed` on deepthought myself in the batch venv/harness environment; compared my
outputs byte-for-byte with the recorded logs; inspected the code paths that produce each value; checked the
checkout, D8 guard, venv, harness and table timestamps.

## Four pins (independently recomputed; all match)

| Pin (addendum key) | Value | Recomputed from |
|---|---|---|
| `sweep2_index_sha256` | `b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4` | `<checkout>/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json` (deepthought) and the checked-in copy — both `sha256sum` equal |
| `sweep2_extract_sha256` | `82c7605291cc07d5d06dc610c6f9a34e6e8d417e62cadb7de7ca59d7b103a4da` | `.../C3_sweep2_batch_s2ev-20261119-a/EXTRACT.json` (deepthought) and the checked-in copy — both equal |
| `table_proposals_sha256` | `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` | `/work/dwong/s2_audit_20261122/table/proposals.jsonl` |
| `table_configs_sha256` | `de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` | `/work/dwong/s2_audit_20261122/table/configs.json` |

`precondition2/SHA256SUMS` verifies (`shasum -a 256 -c`: all 7 entries OK). `build.json` (checked-in copy) is
byte-identical to the table's `/work/dwong/s2_audit_20261122/table/build.json`, sha256
`bbb2a95cef1edfb1e3767eb66b841c54626235b1e3b719529e4b53f37d3dda92`.

**Batch location.** The index, `EXTRACT.json` and all 594 batch files are under the checkout at
`/work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/` (596 files including
the index and `EXTRACT.json`; 16 chunk manifests and 578 `sweeps/` files), created `22 Nov 01:45` into a
fresh evidence directory. `verify` refuses any index outside `<paper-root>/C3_sweep2_batch_s2ev-20261119-a`, and
the running checkout is the paper root, so the batch is where the audit will read it.

**`build.json` binds the index and the table.** `build.json.sweep_index.sha256` =
`b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4` (the index), its path is
`/work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json`
("on the new batch dir under the checkout"), and`commit` = `db7f344d…`; `build.json.table_sha256` reads exactly the
two table pins above; the two source manifests bind the batch mode manifests (`bfe689bd…`, `09e7816b…`, equal to
`EXTRACT.json`'s entries), and `n_proposals` = 5,012, `n_configs` = 855, `replay_checks_total` consistent. There is
no `classification` sidecar, as sweep 2 requires. The table directory is new: `/work/dwong/s2_audit_20261122/table`
was created `22 Nov 01:45:50` inside the fresh audit root (paper checkout `01:22`), holds exactly
`proposals.jsonl`, `configs.json`, `build.json` (all `01:45`), and no earlier table exists at that path.
(The `out` directory is recorded only in the report narrative; `dataset build */build.json` has no `out` field.
That is an observation, not a defect: the audit uses `--table` and the pins, and it re-derives the table itself.)

## Counts (independent re-run)

```
python -B -m r1.c3.sweep2_batch counts --table /work/dwong/s2_audit_20261122/table
```
under `/ceph/dwong/r1_prepare_20261025/venv`, `AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`,
`PYTHONDONTWRITEBYTECODE=1`, returns

```
{"noops": 0, "duplicates": 2512, "eligible": 2500, "proposals": 5012, "unique_configs": 1064, "seed_runs": 10640}
```

— byte-identical to `counts.log` (`diff` empty). A second, independent recomputation over
`proposals.jsonl` + `configs.json` using `arms.is_noop`/`arms.is_duplicate` gives the same partition
(0 / 2,512 / 2,500 of 5,012; 1,064 distinct `(node, hash)` pairs over the 2,500 eligible rows; all eligible hashes
present in `configs.json`; `seed_runs = 1,064 × 10`). This is the plan the audit's own
`evidence_resources` would compute (`audit.py:815-821`), and it is exactly the expected-population line the
addendum asks to fill: **2,500 eligible, 2,512 duplicates, 0 no-ops; 1,064 unique configurations, 10,640 seed
runs.** `build.log` agrees (`n_proposals: 5012`, `zero_delta_violations` 0, `repeat_metric_violations` 0,
`skipped_invalid` 496, `no_edit_rows` 0); 496 skipped records are replay-invalid rows, not table rows.

## `verify --sealed` (independent re-run)

```
python -B -m r1.c3.sweep2_batch verify \
  --index /work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json \
  --paper-root /work/dwong/s2_audit_20261122/paper \
  --sealed /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a
```

returns (rc 0):

```
{"index_sha256": "b4697c…b7460b4", "extract_sha256": "82c760…103a4da", "run_id": "s2ev-20261119-a",
 "files": 594, "collection_counts_sha256": "3e29382b4d31cef54b92d0cf77a0819b5dedda92aedd528b708f5030b88b6ec7",
 "sealed_rederivation": "equal"}
```

My stdout is byte-identical to `verify.log` (`diff` empty). `sealed_rederivation: equal` means the batch was
re-derived from the sealed tree without writing (`extract(write=False)` + full byte comparison), so the checked-in
index/`EXTRACT.json` are exactly what the documented `extract` command produces from the canonical sealed tree
now. The collection counts hash is the published, pinned file (`3e29382b…b6ec7`), and `verify` also checks each
chunk's `job_record_sha256` and the admitted-record set against it; both passed.

## Sealed tree, no copy, no label

- The batch was read from `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/` (readable; 97 MB, 15,149 files, 16
  chunk dirs). That is the only directory named `s2ev-20261119-a` on the host (`find` over `/ceph/srv/dwong`,
  `/work/dwong`, `/ceph/dwong`), and the code refuses any path that does not resolve to the `SEALED_RUN_DIR`
  constant (live refusal check plus `_no_links` symlink refusal); so no alternative copy can have been used
  silently. No sealed data was copied into the repository: the table stays on deepthought and is bound by sha256.
- No sweep-2 label or evaluation file exists yet, and none was opened. The sealed chunks and the batch contain no
  file whose name suggests a label or evaluation file (`find` for `*label*`/`*evaluat*`/`*sealed*` under the sealed
  tree: none); `EXTRACT.json`'s 594 entries are only `chunks/…/manifest.json` and `sweeps/…/{ledgers,roots}`
  outputs of copied ledgers/start files. The table fields used are proposal features and logged metrics.
- **Disclosure for the record:** a `grep` I ran over the historical sweep-1 B.2 report directory
  (`docs/r1/reports/b2_audit_20261119/`) — to source the 4,660-run figure — additionally matched two lines of that
  directory's already-published `label_block.jsonl`, because the search literal `4660` occurs inside an `se_label`
  value. Those are historical sweep-1 rows, carry no sweep-2 information, and were not used; the four pins and all
  counts above are fixed by the batch and table bytes, independent of any label value.

## Checkout and provenance

- Paper checkout `/work/dwong/s2_audit_20261122/paper`: detached HEAD **`db7f344d6ac372737444db5ab036d370543ea65f`**,
  tracked-clean (`git status --porcelain` shows only the expected untracked batch output
  `results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/`; `r1/` clean).
- **D8 guard state passes.** `docs/r1/PLAN.md` at `db7f344d` carries `R1-BX-D8-CONFIRM-V31` naming gate
  `31dab9ef…`, gate sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`; `r1/c3/gate.py` at
  `db7f344d` and `31dab9ef` hashes to exactly that, and `31dab9ef` is an ancestor of `db7f344d`. My `counts` and
  `verify --sealed` runs both execute `require_d8_confirmation()` and passed it (no overlay needed at this step;
  the pinned authority docs bytes — authorization `349e502b…`, published collection counts `3e29382b…`, D28 noise
  summary `3d12ce05…` — are committed at `db7f344d` and identical to `main`).
- Batch venv `/ceph/dwong/r1_prepare_20261025/venv` (Python 3.13.15; scikit-learn 1.8.0, NumPy 2.4.4, pandas
  3.0.3, SciPy 1.17.1 — the D3 basis), and harness
  `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness` at
  **`6adf3859de66c4814fcf376eed59880fbd8eeaf7`**, tracked-clean (untracked `data_cache/` and the artifact report
  only, as the e1 record); the e1 replay report records this path and commit. (The sweep-2 pin `a3fedbbd…` is not
  yet fetched into that repository — precondition 3, not a defect of this output.)
- **Extraction/build commands match the draft's precondition 2.** The report's four commands use the draft's exact
  subcommands, flags and canonical sealed path, run from the checkout with `PYTHONDONTWRITEBYTECODE=1` / `python -B`,
  no `env.sh` PYTHONPATH, and the batch/table paths the artifacts show. The outputs are consistent with those
  commands: extract.log records the batch dir + `files: 594` + both hashes; build.log records 5,012 proposals;
  build.json binds index/table/commit; counts.log and verify.log are the complete JSON above. **No log contains
  `STOP`,** and none is truncated.

## Projection and deadline

`T = 10,640 / 4,660 × 23 min = 52.515 min = 3,150.9 s ≈ 52.5 min` at 16 workers (sweep-1 B.2 basis: 4,660 =
466 × 10 seed runs in 22 min 44 s, `b2_audit_20261119` START 00:27:38Z → PASS 00:50:22Z). Then
`2.5 × T = 7,877.3 s ≈ 131.3 min ≈ 2 h 11 min`, so `deadline = max(10,800 s, 2.5 × T) = 10,800 s` and
`10,800 ≥ 2.5 × T` hold; the projection is also below the 2 h threshold that would require reporting to the author
before launch. The report's deadline value (10,800 s) is correct.

## Findings

**MINOR 1 (only finding).** The report writes `2.5×T ≈ 7,860 s`; the exact value from its own formula is
`7,877 s` (131.3 min). It does not change the deadline (`max(10,800, 7,877) = 10,800 s`), and it is not one of the
key-block pins or counts. In the addendum fill-in record it as `2.5×T ≈ 7,877 s` (or `≈ 7.9 ks`).

No blocking or major discrepancy was found. The four pins, the counts, the `verify --sealed` result and the
collection-counts hash all reproduce exactly; the addendum-fill values (four full sha256s and
`2,500 eligible, 2,512 duplicates, 0 no-ops; 1,064 unique configurations, 10,640 seed runs`) are correct.

## What I did not do

Read-only throughout: no repository, git or deepthought write; no `extract`/`build-sweep` re-run (they write), no
table rebuild; no label, evaluation or sealed-output file opened for analysis. The `counts` and `verify --sealed`
re-runs write nothing (`write=False`; `PYTHONDONTWRITEBYTECODE=1`), and the working tree here is unchanged apart
from this review file.

Code-Commit: db7f344d6ac372737444db5ab036d370543ea65f
Verdict: ACCEPTED

Accepted: the sweep-2 batch (index `b4697c49…b7460b4`, `EXTRACT.json` `82c76052…103a4da`), the table
(`proposals.jsonl` `379b17ca…02197d9`, `configs.json` `de6d63b5…ab0f4d`), the counts and the `verify --sealed`
result at output commit `dcb74c94`; the addendum may cite this file as `precondition2_review` and fill in the four
pins and the counts above.
