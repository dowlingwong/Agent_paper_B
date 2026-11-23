# Independent review — sweep-1 PRE-STAGE A train/dev release receipt (23 November 2026)

Reviewer: `reviewer-sweep1-release`, independent and read-only. Method: read-only `ssh` to deepthought and ceph
(`ls`, `stat`, `find`, `sha256sum`, `wc -l`, `git rev-parse/status/reflog/log/show/ls-remote`, JSON metadata
parsing) and read-only inspection of the committed authority at `3522e59b`. **I did not open, read, print or copy
any label row or evaluation value.** The released file and the sealed role blocks were touched only by `sha256sum`,
`wc -l`, `stat` and `find`; the receipt and the completion record were read as metadata (hashes/counts/ids) only.
I did not re-run the release step or the audit, did not start or stop any job, and nothing on deepthought or ceph
was created, modified or deleted. This file is the only write. Review date 2026-11-23 (Europe/Berlin).

**Reviewed unit.** Report branch **`release-sweep1-20261123` @
`e3536d8391f9db8fef28178b5d6bd1421b1193fd`** (parent published main
`3522e59bf52e738c92981a1ffde67527059f071b`; one commit, two files, `+124` lines, nothing else). Pushed: remote
`refs/heads/release-sweep1-20261123` = `e3536d83`; remote `refs/heads/main` = `3522e59b`. Committed report
`docs/r1/reports/release_20261122/SWEEP1_TRAINDEV_RELEASE_20261123.md` (sha256 `0c8e1531…`) and receipt copy
`docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json` (sha256 `f06e37a9…`). Live release tree
`/work/dwong/s2_release_20261123/release_sweep1_traindev/sweep1/traindev/` (deepthought; two files only). Run
checkout `/work/dwong/s2_audit_20261122/paper`, HEAD = `origin/main` = published main `3522e59b`, tracked clean.
Interpreter `/ceph/dwong/r1_prepare_20261025/venv/bin/python3` (CPython 3.13.15). Sealed sweep-1 B.2 inputs
`/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/{table,output}`. Authority: `R1-S2-LABELS-TRAINDEV-RELEASE`
(PLAN §10, line 1365 at `3522e59b`), `R1-SWEEP1-RELEASE-COMPAT` + `R1-SWEEP1-RELEASE-COMPAT-SCOPE` (lines
1429/1436), release code `a9d8ff5e6964ae25730b266d854927d85dc99c94`.

## Bottom line

**ACCEPTED.** The receipt is internally consistent and binds the committed authority down to the byte; the live
receipt is the committed copy; the released partition is exactly the 869 train/dev label rows of sweep-1, with
**no test label and no evaluation value** released or written; the release ran from a tracked-clean checkout at the
published main with the reviewed v2-builder compatibility path; and the sealed table/audit are byte- and
mtime-unchanged. One **docs-only correction (M1)** must be made in the report before this branch is merged to main:
its authority line names a release row that exists nowhere (`R1-SWEEP2-LABELS-TRAINDEV-RELEASE`). The release facts
themselves are not affected — the binding row `R1-S2-LABELS-TRAINDEV-RELEASE` is correctly cited in the same line —
so this is a report-accuracy defect, not a release/authority defect. Residuals M2–M3 are non-blocking.

## 1. Receipt consistency — verified

Live `/work/…/release_sweep1_traindev/sweep1/traindev/RECEIPT.json` sha256
**`f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1`**, equal to the committed copy. Schema
`r1_c3_release_receipt/v2`; row `R1-S2-LABELS-TRAINDEV-RELEASE`; source `sweep1`; stage `traindev`; tier `T0`;
`integrity.pass = true`; `head` = `published` = `3522e59b`; `release_commit` = `a9d8ff5e`; `utc`
`2026-11-23T09:23:16Z` (= 10:23:16 CET, the file mtime).

| Receipt field | Value in receipt | Independently recomputed |
|---|---|---|
| `decision_sha256` | `860a50e2…` | `860a50e2…` = sha256 of the `R1-S2-LABELS-TRAINDEV-RELEASE` decision cell; row present exactly once in PLAN §10 (line 1365) |
| `prereg_sha256` | `aa1a961b…` | `aa1a961b…` = file `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md` |
| `split_sha256` | `b5967dd7…` | `b5967dd7…` = `r1/c3/splits/c3_p3_split_v1.json` = `p3_split.P3_SPLIT_SHA256` |
| `builder_sha256` | `f67ee5e7…` | `f67ee5e7…` = `r1/c3/gate_input_builder.py` (prereg's pinned builder) |
| `gate_sha256` | `a3f7d002…` | `a3f7d002…` = `r1/c3/gate.py` (gate v3.1) |
| `release_checks_sha256` | `c97b60e9…` | `c97b60e9…` = `r1/c3/release_checks.py` at `3522e59b` |
| `release_commit` | `a9d8ff5e…` | ancestor of HEAD and of remote main; `release.py` at that commit = `02b94721…` = `release.py` at `3522e59b` |
| `inputs.proposals_sha256` | `b713c423…` | `b713c423…` (live `table/proposals.jsonl`) |
| `inputs.label_block_sha256` | `cdae9c3f…` | `cdae9c3f…` (live `output/label_block.jsonl`) |
| `outputs["label_block.traindev.jsonl"]` | `6a6327a3…` | `6a6327a3…` (live output, 869 lines) |

Running the published row check itself from the merged tree (`r1.c3.release.release_row("T0","traindev")`)
reproduces exactly the receipt's row fields `{row id, decision_sha256, prereg_sha256, builder_sha256, gate_sha256,
split_sha256, release_commit}`. The preregistration's final fenced block is `frozen: true`, `pre_stage: A`, pins
the split/builder/gate hashes and the signed decisions, and ends the document.

**Counts (receipt, no values).** `label_rows` train **593** / dev **276** / test **856** (sum **1,725** =
`integrity.completion.counts.eligible` = sealed `label_block.jsonl` line count 1,725); `released_label_rows`
**869** = 593 + 276 = live output line count **869**; `evaluation_rows` **0**; every `label_kinds` entry is
`audit`. The full receipt is metadata only: ids, counts, seeds (`7001–7005` label, `7006–7010` evaluation) and
sha256s — no label or evaluation value.

**Integrity block.** `check` = `audit.verify_evidence_completion`, `completion_sha256` = `e28bee5e…` =
sha256 of the live sealed `evidence_completion.json` (`r1.c3_audit_completion/3`, `label: EVIDENCE`). All 13
completion fields kept in the receipt (`schema`, `label`, `build_sha256`, `proposals_sha256`, `configs_sha256`,
`plan_sha256`, `label_block_sha256`, `evaluation_block_sha256`, `index_sha256`, `classification_sha256`,
`counts {duplicates 3274, eligible 1725, noops 0}`, `label_seeds`, `evaluation_seeds`) are **exactly equal** to the
live completion record. The completion digests were also re-derived from the live files: build `c14a68ae…`,
proposals `b713c423…`, configs `b585b727…`, plan `4fd46e1f…`, label block `cdae9c3f…`, evaluation block
`297fed47…`, index `812468e2…`, classification `bb6d891c…` — all equal.

## 2. Release path — verified

- **Checkout/authority.** `/work/dwong/s2_audit_20261122/paper`: HEAD `3522e59b`, `refs/heads/main` `3522e59b`,
  `refs/remotes/origin/main` `3522e59b`; `git status --porcelain --untracked-files=no` empty (tracked clean). The
  reflog records the reset to `origin/main` at **10:21:20 CET**, i.e. before the receipt's 10:23:16 CET; no commit
  and no HEAD move after. The untracked audit/batch outputs (`audit_20261122T*.pid`,
  `results/r1/evidence/C3_audit_EVIDENCE_20261122T*`, `results/r1/evidence/C3_sweep2_batch_…`) all have 22 Nov
  mtimes — unchanged by the release, as the report says.
- **Command/inputs.** The report's command matches `r1.c3.release`'s CLI and the live paths that exist; the same
  sealed table/audit and paper root are the ones in the refusal diagnosis. `s2_release_20261122/` contains the
  earlier sweep-2 releases and no sweep-1 output (the 22 Nov attempt wrote nothing, as recorded).
- **Compat v2 builder used (R1-SWEEP1-RELEASE-COMPAT option A + SCOPE).** The sealed `build.json` records
  `commit = ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74`, `label = EVIDENCE`, `n_proposals = 4999`, classification
  sha `bb6d891c…`, sweep-index sha `812468e2…`, `table_sha256` equals the live proposals/configs hashes. The
  receipt records the published `release_checks.py` sha (`c97b60e9…`) whose `sweep1_integrity` unconditionally
  passes `sweep1_compat.rebuild_v2_table` (isolated `git archive` of the `ab79b4ce` tree) and refuses any sealed
  `build.json` not from that commit; a v3 replay is known to fail (diagnosis), so `integrity.pass = true` on this
  code is only reachable through the reviewed compat path. No weaker field-level exception exists in the published
  code.
- **Sealed inputs unchanged.** Hashes now: `proposals.jsonl b713c423…`, `configs.json b585b727…`, `build.json
  c14a68ae…`, `label_block.jsonl cdae9c3f…`, `evaluation_block.jsonl 297fed47…`, `evidence_completion.json
  e28bee5e…`, `plan.jsonl 4fd46e1f…`; index `812468e2…` and classification `bb6d891c…` at the cited paths. Mtimes:
  table files **19 Nov 01:24**, audit files **19 Nov 01:27–01:50**, index/classification **22 Nov 01:21** — all
  before the 23 Nov run; table/output directory mtimes also 19 Nov. No workaround is visible in the release path:
  no dirty tracked file, no shadowed module (`_published_clean` checks the plain modules beside `release.py`), no
  output reuse (fresh `--out`; no `*.partial` remains), no env bypass in `release.py`/`release_checks.py`/
  `sweep1_compat.py`, and the receipt binds the published authority and release code.

## 3. No leakage — verified

- Release tree is exactly `RECEIPT.json` + `label_block.traindev.jsonl` (full `find`, no other files, no
  directories beyond `sweep1/traindev`, no symlinks, no `*.partial`); no test-label and no evaluation file exists
  under the release root.
- The output is a fresh regular file (separate inode from the sealed label block, nlink 1) of **869 lines**
  (328,291 bytes) = `released_label_rows` = train 593 + dev 276; `release.py` writes
  `parts["train"] + parts["dev"]` only at stage `traindev`, and `open_partition` re-checks P3 membership for
  readers.
- The sealed test-label and evaluation blocks stay where they were (unchanged hashes/mtimes, 1,725 lines each);
  the receipt/report contain only counts and sha256s. The integrity check does open `runs.jsonl` /
  `evaluation_block.jsonl` internally, as §6 permits, but the step records only pass, counts and hashes.
- The report itself contains no label or evaluation value (counts, hashes and commit ids only).

## 4. Report accuracy and push readiness

Every factual claim checked holds: published main `3522e59b`; `release code a9d8ff5e` and `release.py` identity;
row/source/stage/tier/schema; receipt sha `f06e37a9…`; train/dev/test counts 593/276/856; released 869; evaluation
0; output sha `6a6327a3…`; sealed inputs unmodified; only train+dev released; no test/eval file; and the status
sentence about the earlier sweep-2 receipt (`de95b218…`, train 850/dev 422, released 1,272 — live
`/work/dwong/s2_release_20261122/release_sweep2_traindev_v2/sweep2/traindev/` matches). Branch/hygiene: single
commit on published main, two docs files only, worktree clean, remote branch = `e3536d83`, published main =
`3522e59b`, commit trailer consistent with the repo convention. The branch is ready to merge **after** M1 and the
appended review commit.

## Findings

### M1 (required, docs-only, before merge). The report's authority line names a release row that does not exist

Report line 5–6: "Authority: published main **`3522e59b`** (R1-SWEEP1-RELEASE-COMPAT + SCOPE,
R1-S2-LABELS-TRAINDEV-RELEASE, release code `a9d8ff5e…`, **R1-SWEEP2-LABELS-TRAINDEV-RELEASE**)."
`R1-SWEEP2-LABELS-TRAINDEV-RELEASE` occurs **nowhere**: 0 hits in the whole tree at `3522e59b`, 0 hits anywhere in
`git log --all -S`, and only in this report's commit. The row that actually authorizes the release,
`R1-S2-LABELS-TRAINDEV-RELEASE`, is correctly named earlier in the same line (and is the receipt's `row_id`), so
the release's authority is sound; the extra name is a typo that would send a reader of the permanent record to a
non-existent decision. Fix: delete that token, or replace it with an existing row it presumably meant (e.g.
`R1-SWEEP2-RELEASE-DECISIONS`, PLAN §10 line 1366, which records the release-step decisions REL-CODE A / REL-SCOPE
A and the freeze). A follow-up docs-only commit on this branch is sufficient.

### M2 (non-blocking). The receipt does not directly record the compatibility replay builder

A reader of `RECEIPT.json` alone must reconstruct that the v2 builder was used from the `release_checks_sha256`
pin plus `build_sha256` → `build.json.commit = ab79b4ce`; the report and the accepted compat review give the chain,
and the commitment is sound, but a future receipt schema (v3, a reviewed change to `release.py`) could record the
replay builder/commit explicitly. No action for this release.

### M3 (non-blocking). One status sentence is not receipt-verifiable

"The release did not start U4/U5 or P.4 training" is consistent with everything observed (the release step's only
writes are the two release files; no training output appeared), but it is a statement about other campaigns, not
something the receipt can prove. It can stand as a disclosure; nothing contradicts it.

## Push readiness

The branch at `e3536d83` (pushed; parent published main `3522e59b`) is a clean two-file docs commit and the
receipt/report package is accepted. It is ready to merge once (i) M1 is corrected (docs-only), and (ii) this
appended review is committed into the branch. No code, job, sealed-data or authority change is required;
test labels and evaluation values remain sealed (no test-release row), and sweep-1 train/dev is delivered alongside
sweep-2's.

VERDICT: ACCEPTED
