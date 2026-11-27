# D.3 G2 constants fit — artifact review — 27 Nov 2026

Fresh, independent tier-E review (it fixes keep/execute decisions) of the artifact produced by task
`compute/20261127-17`. The reviewer did not produce the artifact and did not modify the reviewed branch.

- **Target branch:** `origin/compute-d3-g2-constants-20261127` @ `79b0a0ce224ba47b9bd7717c093e19d3e09fbb1b`,
  based on `origin/main` `bad59593460a135ddbbf83d7a8c48eb64fc8a97f` (merge-base = base; the branch adds only
  the record, the captures and the artifact).
- **Unit record:** `docs/r1/reports/d3_g2_20261127/D3_G2_CONSTANTS_FIT_20261127.md`.
- **Artifact:** `docs/r1/reports/d3_g2_20261127/d3_constants.json`
  sha256 `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`.
- **Reviewer:** independent tier-E subagent (OpenCode compute session; no role in the fit or the fitter).

## Method

Read-only. The reviewed branch was checked out detached into a scratch worktree; the artifact was copied to
deepthought and verified with a clean, detached `origin/main` checkout at `bad59593`
(`/work/dwong/d3_g2_paper_20261127`, `git status` clean) and the arms-freeze venv
`/work/dwong/screen-smoke-20261127/venv/bin/python`. The released inputs were hashed in place on deepthought
and the receipt inspected; the code path in `r1/c3/d3_constants.py`, `r1/c3/arms_freeze.py`,
`r1/c3/release.py`, `r1/c3/dataset.py` and `r1/c3/analysis_guard.py` on `origin/main` was read. An
independent full re-fit was run and the 121-row LADDER table of the artifact was recomputed from the released
label/table rows without using the fitter's search code. No repository file was modified and nothing was
pushed to `main` or a coordinator branch.

## Per-check results

### 1. Artifact sha256 and `check` re-parse — PASS

- `sha256sum` of the branch's `d3_constants.json` (local and deepthought copy):
  `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`, the expected value.
- `python -B -m r1.c3.d3_constants check <artifact>` (rc 0) re-parses the file, re-derives each node's
  LADDER choice from its own 121-row search table, and prints
  `"sha256": "4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93"` with
  `ladder_c` = `digits_mlp -1.3`, `openml_breast_w 0.3`, `openml_climate 2.85`,
  `openml_credit_approval -0.1`, `openml_ionosphere -0.05`, `openml_sonar -0.75`, `tabular_mlp -0.8`
  — identical to `captures/check.stdout` and to the record.
- Independent re-fit from the same clean checkout and the same released inputs (fresh `mktemp` output path,
  rc 0) wrote a file with the same sha256 and `cmp` rc 0 (byte-identical). This confirms both the record's
  determinism claim and that the committed bytes are what this code and these inputs produce.

### 2. Released inputs, receipt, toolchain and pins — PASS

Hashed in place on deepthought, all as receipted:

| Input | sha256 (verified) |
|---|---|
| `sweep2/traindev/RECEIPT.json` | `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` |
| `sweep2/traindev/label_block.traindev.jsonl` | `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82` |
| table `proposals.jsonl` | `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` |
| table `configs.json` | `de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` |
| table `build.json` | `bbb2a95cef1edfb1e3767eb66b841c54626235b1e3b719529e4b53f37d3dda92` |

- Receipt: stage `traindev`, source `sweep2`, `counts.label_rows` train 850 / dev 422 / test 1228,
  `counts.released_label_rows` 1272, `counts.evaluation_rows` 0, `integrity.pass` true;
  `outputs["label_block.traindev.jsonl"]` = `7487b6…`; `inputs.proposals_sha256` = `379b17…`;
  `split_sha256` = `b5967dd7…`. All match the record and the artifact.
- Artifact provenance fields: `source.receipt_sha256` = `de95b2…`,
  `source.traindev_partition_sha256` = `7487b6…`, `source.label_block_sha256` = `9ab3cb26…`
  (the receipt's *raw* label-block input hash, correctly taken from the receipt and not opened),
  `source.proposals_sha256` / `configs_sha256` as above; `split_file.sha256` = `b5967dd7…` (equals the
  receipt's `split_sha256`); `noise_source.sha256` = `3d12ce05…` equals the repo's
  `results/r1/noise/D28_REPAIR_20261027/summary.json` and the pin in the fitter.
- Exactly the seven D.3 nodes (`digits_mlp`, `openml_breast_w`, `openml_climate`,
  `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `tabular_mlp`); the table's eighth T0 node
  (`openml_wdbc`) enters nothing.
- Toolchain in the artifact: Python 3.13.15, NumPy 2.4.4, SciPy 1.17.1, interpreter
  `/work/dwong/screen-smoke-20261127/venv/bin/python` — verified by running the venv, and matching the
  record.
- `fitter.sha256` = `5ad96059245bf5a65b0f462f73e74028c77fec8d7dabfa5d0e4f74d0c329b027`, equal to
  `git show origin/main:r1/c3/d3_constants.py | sha256sum` at `bad59593`;
  `a1a2_fitter.sha256` = `fc44e71e…` (main's `arms_constants.py`);
  `gate_input_builder.sha256` = `f67ee5e7…` (main's `gate_input_builder.py`, also the receipt's
  `builder_sha256`). `fitter.code_commit` = `bad59593460a135ddbbf83d7a8c48eb64fc8a97f`, the base.

### 3. Input discipline — PASS

- `_fit_cmd` runs `refuse_input_path` and `refuse_sealed` on the output, table and release root **before**
  anything is opened, then guards each staged file (no symlinks, no sealed paths, receipt/table names not
  test/evaluation blocks); the train/dev partition is checked not to be a symlink redirect.
- Labels come only from `AF.load_traindev` → `release.traindev_labels` → `open_partition(<root>/sweep2/traindev)`,
  which opens only `label_block.traindev.jsonl` from the receipted train/dev partition and pins the receipt
  sha256; `load_traindev` refuses a receipt that is not `stage=traindev`, not the source, or that counts
  evaluation rows; `check_label_rows` refuses any evaluation field, any evaluation seed, and any P3 test
  instance. The release root on deepthought contains only `sweep2/traindev/{RECEIPT.json,label_block.traindev.jsonl}`
  — no test partition exists there.
- The released label file itself (scanned independently): 1,272 rows, kind `audit` only, seeds all within
  `{7001,7002,7003,7004,7005}`, no evaluation field, no evaluation seeds. The table `proposals.jsonl`
  (5,012 rows) carries no label or evaluation key. `dataset.load_table` reads only the label-free
  `build.json` metadata (through `analysis_guard.guard_table`) and `proposals.jsonl`.
- Sub-claim spot check: `rows.A1` (e.g. `digits_mlp` 59 of 114 dev rows) is smaller than `rows.dev` because
  duplicate dev rows carry no soft label; the counts reconcile exactly with the released table (dev rows,
  duplicates) and with the documented selection.
- `pytest -q r1/tests/test_d3_constants.py`: **19 passed** (6.52 s) on the reviewed checkout.
- No test label, evaluation block, evaluation value, or sealed file was read by the fit or by this review.

### 4. Captures and record accuracy — PASS (with minor wording notes)

- `captures/SHA256SUMS` verifies from the report directory (`shasum -a 256 -c captures/SHA256SUMS`): all
  seven entries OK, including `d3_constants.json` and its own `sha256.txt`, and the two empty stderr files
  (`e3b0c442…`). `sha256.txt`, `fit.stdout`, `check.stdout` and `repeat_fit.stdout` agree with the record
  (same artifact sha256, same `ladder_c`, distinct `out` paths for the two fits).
- The record does not overstate: it labels the output an ENGINEERING/ANALYSIS artifact, says explicitly that
  the fit is not a frozen pre-declaration and that revision 4 §14 `constants_file_sha256` is filled later by
  the coordinator. It reports PASS on the fit only, not a decision outcome. Its substantive numbers
  (counts, hashes, c values, toolchain, fitter pin, commit) match what was verified above.
- Minor wording (non-blocking, see findings): there is no SHA256SUMS *outside* `captures/`; and "uses only
  rows whose source hashes match" describes whole-file pinning, not per-row hash matching.

### 5. Validity / reproducibility — PASS

The artifact is a valid, reproducible output of the reviewed fitter `5ad96059…` at `bad59593`, from exactly
the receipted train/dev release and pinned table, under the recorded toolchain. An independent re-fit
reproduced it byte-for-byte and an independent recomputation of all seven 121-row LADDER tables from the
released rows matched every `U` and `keeps` value, including each tie-broken `c` and `eta = float(c) * sigma`.
No finding makes the artifact invalid or unreproducible.

## Findings

1. **Minor (record wording, non-blocking).** "the artifact hash is in the record and in the report's outer
   `SHA256SUMS`" — the only SHA256SUMS is `captures/SHA256SUMS`; it does list `d3_constants.json`, but with
   a path relative to the report directory, so the `-c` check must run from
   `docs/r1/reports/d3_g2_20261127/` (verified there). No integrity gap; suggest correcting the wording at
   the next touch.
2. **Minor (record wording, non-blocking).** "uses only rows whose source hashes match" — the fitter pins and
   re-hashes the whole released inputs (receipt, partition, table, configs, split, noise); there is no
   per-row source-hash filter. The claim is stronger than the mechanism, though the mechanism is sufficient.
3. **Observation (no action required).** `rows.A1` < `rows.dev` for every node because duplicate dev rows
   carry no soft label. The record does not explain this; the counts were independently reconciled with the
   released table and the code's documented selection.

None of these touches the artifact's bytes, provenance, fit result, or the input-discipline conclusion, so
they do not block the coordinator's use of `4f5f686b…` in revision 4 ¶14.

Verdict: ACCEPTED
