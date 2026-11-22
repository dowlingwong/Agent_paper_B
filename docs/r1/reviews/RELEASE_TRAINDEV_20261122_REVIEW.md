# Independent review — PRE-STAGE A train/dev label release (sweep 2 PASS, sweep 1 refused), 22 November 2026

Reviewer: `reviewer-release-traindev`, independent and read-only. Method: read-only `ssh` to deepthought and ceph
(`ls`, `stat`, `find`, `sha256sum`, `sha256sum -c`, `wc -l`, `git rev-parse/status/diff/reflog/log/show`, JSON
metadata parsing), hashing and line counts on the live copies, and comparison against the committed authority and
the published reports. **I did not open, read, print or copy any label row or evaluation value.** The released
file and the sealed blocks were touched only by `sha256sum`, `wc -l`, `stat` and `find`; the seal directory only by
hashing and `sha256sum -c` (a self-check). I did not re-run the audit or the release step, did not start or stop
any job, and nothing on deepthought or ceph was created, modified or deleted. The one recomputation I ran is the
**sweep-1 integrity replay check** (`r1.c3.audit._verify_replay`), which reads the table, the sweep index and the
classification sidecar only — no label block — and reports only the exception type/message (section 2). This file
is the only write. Review date 2026-11-22 (Europe/Berlin).

**Reviewed unit.** Report branch **`release-traindev-20261122` @ `fbe5db766d5169577982b7e3fec6d81fbf5aaddd`**
(parent published main `5a85adf91`), a two-file commit adding
`docs/r1/reports/release_20261122/S2_TRAINDEV_RELEASE_20261122.md` (sha256 `b7758579…`) and
`docs/r1/reports/release_20261122/RECEIPT_sweep2_traindev.json` (sha256 `d2747771…`); nothing else.
Live release tree on deepthought `/work/dwong/s2_release_20261122/release_sweep2_traindev/sweep2/traindev/`
(two files only). Run checkout `/work/dwong/s2_audit_20261122/paper` (audit checkout, at published main
`38ae4a05` during the run; current HEAD `5a85adf9`, tracked clean). Interpreter
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`; audited harness
`/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness` @
`6adf3859` (clean, untracked data caches only). Sealed sweep-2 audit
`/ceph/srv/dwong/paperb/sweep2_audit/s2ev-20261119-a_20261122T164726Z/`. Sweep-1 inputs
`/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/{table,output}`.

## Bottom line

**NOT ACCEPTED — one blocker (B1), and the branch is not ready to push.** The release facts themselves verify:
the sweep-2 receipt is internally consistent and binds the sealed audit; the released partition is the
1,272 train/dev label rows with **no** evaluation value and **no** test label; the sweep-1 refusal is genuine (I
reproduced the exact `ValueError` on the original sealed inputs), wrote no output and was not worked around. The
counts, hashes, split consistency and audit seal all check out independent of the report (sections 1–3).

The blocker is **authority**: the report's authority line ("published main with R1-S2-LABELS-TRAINDEV-RELEASE …
and R1-SWEEP2-LABELS-FREEZE") is **false**. `R1-SWEEP2-LABELS-FREEZE` is not in `docs/r1/PLAN.md` at the run's
published commit `38ae4a05`, nor at current remote main `5a85adf9`, and the string occurs nowhere under
`docs/r1` on main. It was on main for seven minutes and was then **deleted by an unrelated publication commit**
(4b7452b6, below), six minutes before the release ran. The sweep-2 B.2 addendum makes the independent review of
the run **and the author's label-table freeze** a condition for labels counting (addendum line 68, sha256
`2e5a6a6d…`); a report that says the freeze is on published main, when it is not, cannot be pushed as the record
of an authorized release.

The same revert also removed **`R1-SWEEP2-B2-RETRY`** (the row amending the B.2 audit protocol under which the
sweep-2 audit attempt 3 ran) and **`R1-G1B-AR-PY`** from PLAN on main (collateral, see B1). This is a repository
regression larger than this release; it must be repaired before the release report is published.

## BLOCKER

### B1. The report's authority is not on published main: `R1-SWEEP2-LABELS-FREEZE` (and two other signed rows) were reverted from PLAN on main seven minutes before the release

**Observed state.**
- `| R1-SWEEP2-LABELS-FREEZE |` in `docs/r1/PLAN.md`: **0** at `38ae4a05` (the receipt's `head` and `published`),
  **0** at current remote main `5a85adf9`, **0 rows anywhere under `docs/r1` on main**.
- Same for the two other 22 Nov author rows: `R1-SWEEP2-B2-RETRY` and `R1-G1B-AR-PY` are **0** in PLAN at
  `38ae4a05` and at `5a85adf9`.
- All three were present in PLAN at `26532dd6` (`| R1-SWEEP2-LABELS-FREEZE |` = 1, etc.).

**Cause (verified).**
- `26532dd6` "docs(r1): R1-SWEEP2-LABELS-FREEZE", committed 20:45:25 CET, records the author signing the freeze
  in chat ("签 LABELS-FREEZE + 推 main", committed on their behalf). It added the (f) subsection (PLAN became
  `3bd2f265…`; the (d) `R1-G1B-AR-PY` and (e) `R1-SWEEP2-B2-RETRY` subsections were already present in its parent
  `6c5ba97b`).
- `4b7452b6` "docs(r1): publish the T1 data-manifest erratum record …", committed **20:52:54 CET**, has parent
  `26532dd6` and its `docs/r1/PLAN.md` blob is **`87e65145…`, byte-identical to the stale branch copy at
  `ac298f25`** (the ops-t1-data-manifest branch base). Its PLAN diff is **18 deletions and nothing else** — the
  three whole authored subsections (d) `R1-G1B-AR-PY`, (e) `R1-SWEEP2-B2-RETRY`, (f) `R1-SWEEP2-LABELS-FREEZE`.
  The commit message says the published files were "copied unchanged … every file compared byte-for-byte with
  that commit"; PLAN was copied from the stale branch base and the three newer author rows were collateral.
- `38ae4a05` (20:52:55) and `5a85adf9` (21:00:10) inherited that PLAN; remote `origin/main` is `5a85adf9` today.

**Timeline around the release (audit-checkout reflog, read-only).** `20:59:12` fetch `origin/main` →
`38ae4a05`; `20:59:14` checkout `main` (= `38ae4a05`); `19:59:42Z = 20:59:42 CET` receipt written (live receipt and
label file mtimes `20:59:42.58`/`.53` CET); `21:00:39` fetch → `5a85adf9`; `21:00:45` reset to `origin/main`.
So the release ran **against a main from which the freeze row had been deleted six minutes earlier**, not against a
main carrying it. The `release.py` checks do not test for the freeze row (they check the release row, the frozen
preregistration, D8, the source integrity check, and a clean checkout equal to `origin/main` on the published
paths), which is why the step ran; but the authority claimed by the report is not there. `38ae4a05` was the
current published main at run time: `38ae4a05` is a descendant of `26532dd6`, all 11 `PUBLISHED_PATHS` blobs are
byte-identical between `38ae4a05` and `5a85adf9`, and the later main is docs-only, so the run's "published main"
claim is otherwise correct.

**Why it blocks.** The B.2 addendum (`docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md`, sha256
`2e5a6a6d…`, bytes unchanged at main) says: "Labels count only after an independent review of the run and the
author's label-table freeze." The review of the run exists (`docs/r1/reviews/S2_B2_AUDIT_RUN_REVIEW_20261122.md`,
accepted), but the author's label-table freeze is **not on main**. The release report's authority sentence is
therefore a false statement about the repository, and the release cannot be presented as authorized against
published main. The same missing state also makes the accepted B.2 audit report's line "the row is on current
main" (about `R1-SWEEP2-B2-RETRY`) currently false.

**Required fix (before push).**
1. Restore the three signed 22 Nov subsections verbatim to `docs/r1/PLAN.md` on main: the text is recoverable from
   `26532dd6:docs/r1/PLAN.md` (blob `3bd2f265…`; the parent of `4b7452b6`). The author signatures are already
   recorded (`52f4e3e5` R1-G1B-AR-PY 15:40 CET, `c870179d` R1-SWEEP2-B2-RETRY 17:48 CET, `26532dd6` freeze
   20:45 CET); no new author decision is needed. Publish that repair commit, re-fetch, and confirm all three rows
   are present at `origin/main` in the tree (not merely in history).
2. Re-issue the release from the repaired main so the receipt's `published` commit carries the freeze at step
   time: check out the audit checkout to the repaired main, and run the same release command into a **fresh out
   root** (the receipt schema lets one release be written once per output directory; the current tree is
   retained). This is the clean, cheap path (~30 s, CPU, no label values leave the step) and removes the need for
   an "authority was absent at run time" disclosure.
3. Correct the report's authority line to name the repaired published commit and the restored freeze row (with
   its exact text/decision sha if the report continues to cite it), or state explicitly that the run-time main did
   not carry the freeze and that the author's signed freeze was published afterwards, together with the author's
   confirmation that it governs the label table. The current sentence must not be pushed either as it stands.
4. Add this review file to the branch and, after the fixes, a round-2 confirmation may be appended (a data
   re-derivation is not needed — the partition and seal are unchanged; only the authority bookkeeping and the
   statement are).

## Checks — what passed

### 1. Receipt internal consistency — PASS

All receipt fields that name a hash were recomputed from the live/sealed/committed bytes and match. The receipt
copy in the report worktree is byte-identical to the live receipt (`sha256 d2747771fd043ea0f087285ed2b42583de
aec799e16130b96ea834faa6effb7c` both).

| Receipt field | Value | Source recomputed | Match |
|---|---|---|---|
| `schema` / `row_id` / `source` / `stage` / `tier` | `r1_c3_release_receipt/v2`, `R1-S2-LABELS-TRAINDEV-RELEASE`, `sweep2`, `traindev`, `T0` | receipt, PLAN row | yes |
| `decision_sha256` | `860a50e2…` | sha256 of the second cell of the unique PLAN row at `38ae4a05`/main | **yes** |
| `prereg_sha256` | `aa1a961b…` | `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md` at `38ae4a05` | **yes** |
| `builder_sha256` | `f67ee5e7…` | `r1/c3/gate_input_builder.py` at `38ae4a05`/main | **yes** |
| `gate_sha256` | `a3f7d002…` | `r1/c3/gate.py` at `38ae4a05`/main | **yes** |
| `release_checks_sha256` | `628be81a…` | `r1/c3/release_checks.py` at `38ae4a05`/main | **yes** |
| `split_sha256` | `b5967dd7…` | `r1/c3/splits/c3_p3_split_v1.json` at `38ae4a05`/main | **yes** |
| `release_commit` / `head` / `published` | `a9d8ff5e…` / `38ae4a05…` / `38ae4a05…` | `a9d8ff5e` is an ancestor of `38ae4a05` and of current main; `r1/c3/release.py` at `a9d8ff5e` = running = main (`02b94721…`) | **yes** |
| `inputs.label_block_sha256` | `9ab3cb26…` | sealed audit `label_block.jsonl` (2,500 rows) and checkout copy | **yes** |
| `inputs.proposals_sha256` | `379b17ca…` | original audit table `/work/dwong/s2_audit_20261122/table/proposals.jsonl` | **yes** |
| completion `build/configs/extract/index/plan/label/eval/proposals` | `bbb2a95c/de6d63b5/82c760/b4697c/4479b1dd/9ab3cb26/1e3a0e7a/379b17ca…` | all recomputed from the audit tree and the sealed copy | **yes** |
| completion `label_seeds` / `evaluation_seeds` | 7001–7005 / 7006–7010 | sealed `evidence_completion.json` | **yes** |
| completion `counts` | 2500 eligible / 2512 duplicates / 0 no-ops | sealed completion, binding and audit report | **yes** |
| `integrity.completion_sha256` | `f751681f…` | sha256 of sealed `evidence_completion.json` (checkout and ceph copies) | **yes** |
| `integrity.pass` / `check` | `true` / `audit.verify_evidence_completion(source='sweep2')` | receipt; `release_checks.py` = pinned `628be81a…` | **yes** |
| `outputs["label_block.traindev.jsonl"]` | `7487b627…` | live released file (`/work/dwong/.../label_block.traindev.jsonl`) | **yes** |

Counts are mutually consistent: label rows **train 850 + dev 422 + test 1,228 = 2,500**; released
= **1,272 = 850 + 422**; evaluation rows **0**; all label kinds `audit`. The released file has exactly
**1,272 lines** and **505,043 bytes**; receipt and label file mtimes both `20:59:42` CET. The live release tree
contains **only** `RECEIPT.json` and `label_block.traindev.jsonl` — no evaluation block, no test label file, no
`.partial` directory anywhere in `/work/dwong/s2_release_20261122`.

**Independent split-consistency check (metadata only, no label values).** From the sealed audit's
`plan.jsonl` (2,500 eligible-proposal rows; fields `proposal_id`, `node`, …), mapping each proposal's instance
through the committed P3 split file (`r1/c3/splits/c3_p3_split_v1.json`, `b5967dd7…`) gives
**train 850 / dev 422 / test 1,228, 0 unknown** — the receipt's split counts exactly. This is the plan side of the
partition; the release step itself re-derives the same membership from the 2,500 label rows under the pinned
`release.py` (which refuses any row outside the P3 split), and the 1,272 released rows are the `train`+`dev`
partition of that block. I did not verify the row-level membership by opening label rows (sealed); the receipt's
`completion` object and the pinned code path are the evidence, and the receipt's counts are consistent with both
the audit plan and the 2,500-row label block.

### 2. Sweep-1 refusal — PASS (genuine, written nothing, not worked around)

- The refusal recorded in the report is mechanically the code's: `release.py` (pinned `02b94721…`) catches any
  exception from the registered check, records only its type name, and raises
  `ReleaseStop(f"STOP: integrity check failed for {source} ({failure})")` (`release.py:530–536`); nothing is
  written before the check passes (writes happen only after the check, into a `*.partial` directory that is
  renamed at the end). With `sweep1` the registered check is `release_checks.sweep1_integrity` →
  `audit.verify_evidence_completion` → `_verify_replay` (audit.py:508–525); the specific message
  "evidence table differs from full source replay: proposals.jsonl" is raised at audit.py:524.
- **I reproduced the failure independently**: with the original sweep-1 table
  `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table` (proposals `b713c423…`, configs `b585b727…`, build
  `c14a68ae…`), the pinned sweep index (`results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, sha256
  `812468e2…` = `analysis_guard.SWEEP1_INDEX_SHA`), the classification sidecar
  (`results/r1/evidence/C3_sweep_classification_20261028.json`, `bb6d891c…` = the build's classification sha), the
  audit checkout at main as paper root, and the audited harness (`AR_HARNESS_ROOT=.../autoresearch_harness` @
  `6adf3859`), `_verify_replay` returned
  **`ValueError | evidence table differs from full source replay: proposals.jsonl`** in 14.8 s. No label block is
  read by that check.
- No sweep-1 output or receipt exists: `/work/dwong/s2_release_20261122/release_sweep1_traindev` is absent; the
  release root has only the sweep-2 tree; no `*.partial` and no other `RECEIPT.json` under
  `/work/dwong/s2_release_20261122` (`find` checks). The sweep-1 table/audit inputs are untouched in /ceph.
- There is no sign of a workaround: `r1/c3/release.py` and `r1/c3/release_checks.py` in the run checkout equal the
  pinned/published bytes; the checkout was tracked-clean at the published main during the run; the failed sweep-1
  attempt left nothing to inspect or resume. Reporting a failed integrity check by its type and leaving the table
  to the author is exactly what §6/`release.py` require.
- The earlier **sweep-2** refusals are also consistent with the code and disclosed: a rebuilt table in another
  paper root fails `sweep2_batch.verify` (index must be at the batch directory of the paper root) or the
  completion/build binding; the residual `/work/dwong/s2_release_20261122/table` (proposals `379b17ca…`, configs
  `de6d63b5…`, but build `b8531c60…`) is exactly such a rebuilt table and was **not** the successful input: the
  receipt's `completion.build_sha256` is `bbb2a95c…`, the original audit table
  `/work/dwong/s2_audit_20261122/table/build.json`, so the successful run used the original audit table under the
  audit root, as the report says.

### 3. Labels sealed — PASS (no test label, no evaluation value released)

- The release tree contains only `label_block.traindev.jsonl` (1,272 rows) and `RECEIPT.json`; no
  `evaluation_block*`, no `label_block.test.jsonl`, no `label_block.jsonl`. `counts.evaluation_rows = 0`.
- `test: 1228` in the receipt is a **partition count** of the sealed label block (the P3 test instances), not
  released rows: `released_label_rows = train + dev = 1,272`, and the receipt's `outputs` names only the traindev
  file.
- The test-release row is absent from main (`| R1-S2-LABELS-TEST-RELEASE |` = 0 in PLAN at `38ae4a05` and at
  current main; likewise `R1-T1-LABELS-UNSEAL` = 0), so the partition-reading locks still hold and the test labels
  and all evaluation values remain sealed in the audit.
- The committed report contains only hashes and counts (read in full; two added files only); no label or
  evaluation value appears in it, and the release branch commit adds no data file.
- I did not open the released or sealed label rows, so I cannot and do not claim a row-level audit of the 1,272
  lines; what is verified is the receipt binding (section 1), the exact output hash/count, and the code path that
  produces only `train`+`dev` lines.

### 4. Rules / authority / hygiene — partial: B1 as above, everything else PASS

- **Release row on main.** `| R1-S2-LABELS-TRAINDEV-RELEASE |` is present exactly once in PLAN at `38ae4a05` and
  at current main; its text cites the frozen prereg `aa1a961b…`, the split `b5967dd7…` and the release code
  `a9d8ff5e…`, and the receipt's `decision_sha256 860a50e2…` is the sha256 of that exact cell.
- **Pinned release code.** `a9d8ff5e` is an ancestor of `38ae4a05` and of current `origin/main`;
  `git show a9d8ff5e:r1/c3/release.py` = `r1/c3/release.py` at the run checkout / current main
  (`02b94721…`), which is what `release.py`'s own `_published_clean`/`release_row` enforce.
- **Frozen preregistration.** The prereg's final fenced block at `38ae4a05` says `frozen: true`, pins
  `split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd7…`, `gate_sha256 a3f7d002…`,
  `gate_input_builder_sha256 f67ee5e7…`, the signed decisions, `frozen_utc 2026-11-21T21:41:44Z`, and ends the
  document — equal to the receipt's bindings.
- **Clean checkout at published main.** The run checkout's reflog shows the fetch to `38ae4a05` at 20:59:12 and
  the checkout at 20:59:14, with the receipt at 20:59:42; `release.py` itself refuses a dirty tracked tree or a
  difference from `origin/main` on its published paths, so the step's pass attests them. The checkout is still
  tracked-clean (0 lines `git status --porcelain --untracked-files=no`) with the untracked audit/batch outputs
  preserved (`C3_audit_EVIDENCE_*`, `C3_sweep2_batch_s2ev-20261119-a`, PIDs) — no output was lost or rewritten.
- **No code/PLAN edits in the report commit.** `fbe5db76` adds only the two report files; `git show --stat` = 2
  files, 132 insertions. No change to `r1/`, PLAN, prereg or any authority file.
- **Audit evidence untouched (sealed hashes).** Sealed copy and checkout copy both:
  `AUDIT_SEAL.json 55fdb225…` (the frozen `R1-SWEEP2-LABELS-FREEZE` seal), `evidence_completion.json f751681f…`,
  `label_block.jsonl 9ab3cb26…` (2,500 rows), `evaluation_block.jsonl 1e3a0e7a…` (2,500 rows), plus
  `runs.jsonl cf57bf7e…`, `plan.jsonl 4479b1dd…`, `environment.json 8aed5ca9…`, `resources.json be5c66ac…`,
  `index b4697c…`, `extract 82c760…`; `sha256sum -c SHA256SUMS` in the sealed directory passes (1,074 entries,
  exit 0). The batch directory used by the check is the untracked `s2ev-20261119-a` batch (EXTRACT/index pinned) and
  is unchanged.
- **Interpreter/env.** The report states the approved venv interpreter; the sweep-2 integrity pass also implies
  the audit's environment basis and harness binding (`AR_HARNESS_ROOT` → `6adf3859`, checked in audit.py:635–638
  and 1385–1393) matched, because a mismatch raises before `pass: true`. (Minor m2: the report's command omits
  `AR_HARNESS_ROOT`, `PATH`, `PYTHONDONTWRITEBYTECODE` and the thread variables; a reproducer needs them.)
- **GPU hours: none.** The release step is a CPU-only partition/copy/hash step; no GPU job, scheduler record or
  GPU-hour claim exists for it, and the audit it consumes was CPU-only on deepthought (accepted in the B.2 audit
  review). Nothing in this review required or observed a GPU allocation.

### 5. Verdict

**NOT ACCEPTED** as a pushable record: **B1** above (authority claim false; the author's label-table freeze is
not on published main because of the 4b7452b6 revert, and the run therefore ran against a main without the
freeze; the same revert dropped `R1-SWEEP2-B2-RETRY` and `R1-G1B-AR-PY`). The release's scientific content and
the receipt are sound, the labels are sealed, and the sweep-1 refusal is genuine and correctly reported; the
blocker is the missing published authority and the false statement about it, plus the repository regression it
exposes.

**Non-blocking corrections to fix while repairing B1** (they do not change the release facts):
- **m1.** The report's bullet "completion `/4`: … runs `cf57bf7e…` …" lists `runs_sha256` as if the receipt's
  embedded completion subset contained it; it does not (`release_checks.COMPLETION_KEEP` keeps schema, blocks,
  proposals, build, configs, plan, counts, seeds, index, classification, source, extract — not `runs_sha256` or
  `environment_sha256`). The hash `cf57bf7e…` is correct and is in the sealed `evidence_completion.json` pinned by
  `completion_sha256 f751681f…`; reword the bullet (or cite the sealed completion record) so the receipt excerpt
  is literal.
- **m2.** Give the exact reproducible command and environment: the `--table` is
  `/work/dwong/s2_audit_20261122/table`, `--paper-root` `/work/dwong/s2_audit_20261122/paper`, `--audit`
  `results/r1/evidence/C3_audit_EVIDENCE_20261122T164726Z`, `--index`
  `results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json`, `--out`
  `/work/dwong/s2_release_20261122/release_sweep2_traindev`, with `AR_HARNESS_ROOT` as above,
  `PATH=<venv>/bin`, `PYTHONDONTWRITEBYTECODE=1` and the four thread variables = 1. The placeholders in the
  current report do not identify which table (the only receipts-consistent one is the original audit table, build
  `bbb2a95c…`).
- **m3.** Disclose the downstream state: the sweep-1 side of the row is **not** delivered, so anything that wants
  the receipted **sweep-1** train/dev partition (e.g. Track P P4 phase 1, `P4-LABELS A`, which names the receipted
  sweep-1 train/dev partition) remains blocked until the author resolves the sweep-1 replay mismatch; the report
  says the sweep-1 table is left for the author but does not connect it to that dependency.
- **m4.** Disclose that main advanced to `5a85adf9` (authored 21:00:10, fetched 21:00:39, checkout reset
  21:00:45) within a minute of the receipt, and that all 11 `release/published` code and authority files are
  byte-identical between `38ae4a05` and `5a85adf9` (so the receipt remains valid under the later tip); the
  receipt's `published` value already names `38ae4a05`.
- **m5.** The receipt does not record the input roots (`table_dir`, `audit_dir`, `paper_root`, out root) — a
  schema property, not a run error; the corrected report's exact command (m2) covers it.

**Limitations of this review.** I did not open label rows; split membership is verified from the receipt, the
pinned release code and the audit plan metadata (which agree), not from the released rows. I did not re-run the
sweep-2 integrity check (it reads the sealed label/evaluation blocks and the audit run log; the accepted B.2 audit
review covers those bytes, and the receipt binds the same completion sha). I did not review the sweep-2 collection
or any downstream analysis.

---

VERDICT: NOT ACCEPTED
