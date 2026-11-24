# Sweep-1 label-table freeze — record for the author's signature (approved: false)

**Status: DRAFT, not signed.** Until the author signs it, the sweep-1 label table is **not** frozen, and the P.4
runner refuses this file: its job checks the `approved` key line and the sweep-1 label block sha256
(`r1/scripts/htcondor/trackp_p4/p4_lib.py`, `inputs()`, branch `mac-trackp-p4-runner-20261122` @ `7ab79a9d8`).
On signature only the key lines marked "at signature" in the block below, this heading's "(approved: false)" and this
Status paragraph change. Every other byte stays as reviewed.

Prepared by the Mac-desk agent (Claude), AI-assisted, 24 November 2026, from published `main` `3024db3f`. Model:
R1-SWEEP2-LABELS-FREEZE (PLAN §10, 22 November 2026 (f)); no sweep-2 freeze record file exists. Every hash below is
copied from a committed record on `main`; the source of each is in §2. No label or evaluation value was read to
prepare this record.

```
approved: false
record: C3 sweep-1 label-table freeze (P.4 prerequisite P1; sweep-1 counterpart of R1-SWEEP2-LABELS-FREEZE)
label_status: EVIDENCE audit; the label table counts only after this signature
audit_attempt: b2-ab79b4ce-20261119T002306Z (second authorized sweep-1 B.2 EVIDENCE attempt; code ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74)
audit_output: results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z
sealed_at: /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/ (authoritative output paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z; full output copy output/)
audit_seal_sha256: TODO_VERIFY_ON_HOST (no AUDIT_SEAL.json is named in any sweep-1 record on main; see section 2)
audit_pass_record: docs/r1/reports/b2_audit_20261119/PASS.json sha256 cda7d15e3d935a7d25e267a80a18038ffb2ce1db2b8fdb4668b99052cd7dd999
evidence_completion_sha256: e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4
label_block_sha256: cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca
evaluation_block_sha256: 297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67
report: docs/r1/reports/b2_audit_20261119/REPORT.md (sha256 ef19cb421f5b6236ccf48b7ffa177605032a2fcc59c29eace624034703b80dc1)
review: docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md (VERDICT: ACCEPTED; four minors, carried as errata E1-E4)
release_receipt: docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json sha256 f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1
release_partition: sweep1/traindev/label_block.traindev.jsonl sha256 6a6327a3731dc2d874822e009f3b2d84fbf1a6cbabfef505c657f90b14fd7b2a
release_review: docs/r1/reviews/SWEEP1_TRAINDEV_RELEASE_REVIEW_20261123.md (VERDICT: ACCEPTED)
final_verification: PASS, 2026-11-23T09:23:16Z, deepthought; release step r1.c3.release --stage traindev --source sweep1 at published main 3522e59bf52e738c92981a1ffde67527059f071b (release code a9d8ff5e6964ae25730b266d854927d85dc99c94, release_checks sha256 c97b60e98f4bcd9ac731fd62a9d712dd8e8267a00b01c00f869f43dd4260cbbf); integrity check release_checks.sweep1_integrity -> audit.verify_evidence_completion(..., replay_builder=sweep1_compat.rebuild_v2_table); completion_sha256 e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4
not_label_sources: attempt b2-435513d2-20261118T012807Z (pre-worker STOP, preserved at /ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse)
errata: E1-E4 (section 5)
cotenancy_reading: other users' load (E2); signing adopts it
layout_flatten_gate: not satisfied by this record alone
signed_by: PENDING (at signature: the author)
signed_utc: PENDING (at signature)
author_instruction: PENDING (at signature: the author's instruction, verbatim)
```

## 1. The freeze

The sweep-1 label table is the audit `b2-ab79b4ce-20261119T002306Z`, the second authorized sweep-1 B.2 EVIDENCE
attempt (R1-B2-GO, the signed addendum `docs/r1/authorizations/c3_b2_addendum_20261117.md`, R1-B2-ADDENDUM /
R1-B2-ADDENDUM-FIX / R1-B2-PIN-FIX2; code `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74`), output
`results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z`, retained at
`/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/` (authoritative output in the attempt checkout under
`paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z`, full output copy under `output/`):
`evidence_completion.json` sha256 `e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4`, label block
`cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca`, evaluation block
`297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67`; report `reports/b2_audit_20261119/REPORT.md` and
review `reviews/B2_AUDIT_RUN_REVIEW_20261119.md` on main. This is the author's "separate label-table freeze" named in
the B.2 report (`REPORT.md` lines 11–12) and in R1-B1-CORPUS-FREEZE ("Fresh-seed soft-label tables are frozen
separately after the audit"). The 18 Nov attempt `b2-435513d2-20261118T012807Z` is not a label source. The train and
dev labels are released as the receipted partition of R1-S2-LABELS-TRAINDEV-RELEASE (receipt `f06e37a9…65c1`,
partition `6a6327a3…7b2a`, §3); the test labels and the evaluation block are released only by a T0 test release row
(R1-S2-LABELS-TEST-RELEASE, not yet on main).

**Sweep-1 equivalents of the sweep-2 row's items.**

| R1-SWEEP2-LABELS-FREEZE item | Sweep-1 value |
|---|---|
| audit attempt | `b2-ab79b4ce-20261119T002306Z` (no retry, no resume; the 18 Nov attempt stopped before any worker ran) |
| output | `results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z` |
| seal path ("sealed at") | `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/` (the retained attempt directory; the release step read `table/` and `output/` under it) |
| `AUDIT_SEAL.json` sha256 | `TODO_VERIFY_ON_HOST`: no sweep-1 record on main names an `AUDIT_SEAL.json`. The sweep-1 audit's committed seal records are `PASS.json` (`cda7d15e…d999`), `SHA256SUMS` (14 files) and `OUTPUT_SHA256SUMS` (476 outputs) in the report directory |
| `evidence_completion.json` sha256 | `e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4` |
| label block | `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca` |
| evaluation block | `297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67` |
| report | `docs/r1/reports/b2_audit_20261119/REPORT.md` |
| review | `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md` (VERDICT: ACCEPTED) |
| attempts that are not label sources | `b2-435513d2-20261118T012807Z` |
| release rows | R1-S2-LABELS-TRAINDEV-RELEASE (train/dev, receipted, §3); a T0 test release row (test labels, evaluation block) |

## 2. Bound values and their sources

All on published `main` `3024db3f` (unchanged since `76a3c71f`). "SUMS" is `docs/r1/reports/b2_audit_20261119/SHA256SUMS`.

| Value | Bound as | Source on main |
|---|---|---|
| Attempt id | `b2-ab79b4ce-20261119T002306Z` | `PASS.json` `attempt`; `REPORT.md` §8 |
| Code commit | `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` | `START.json` `pins.paper_code_commit`; `REPORT.md` line 4 |
| Output | `…/paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z` | `PASS.json` `out`; `REPORT.md` §8 |
| Retained attempt directory | `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z` | `PASS.json` `ceph_attempt_dir`; `REPORT.md` §8 |
| `AUDIT_SEAL.json` sha256 | `TODO_VERIFY_ON_HOST` | not in any committed sweep-1 record |
| `PASS.json` sha256 | `cda7d15e3d935a7d25e267a80a18038ffb2ce1db2b8fdb4668b99052cd7dd999` | SUMS line 10 |
| `evidence_completion.json` sha256 | `e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4` | SUMS line 13; `PASS.json` `evidence_completion_sha256`; receipt `integrity.completion_sha256` |
| Completion schema | `r1.c3_audit_completion/3` | `evidence_completion.json` `schema`; `PASS.json` |
| Label block sha256 | `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca` | SUMS line 11; `evidence_completion.json` `label_block_sha256`; receipt `inputs.label_block_sha256`; `p4_lib.SOURCE_BLOCK_SHA256` |
| Evaluation block sha256 | `297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67` | SUMS line 3; `evidence_completion.json` `evaluation_block_sha256` |
| Rows and seeds | 1,725 label rows (seeds 7001–7005) and 1,725 evaluation rows (seeds 7006–7010), K = 10; 4,999 proposals: 1,725 eligible, 3,274 duplicates, 0 no-ops | `PASS.json` `counts` |
| Raw runs / plan | `runs.jsonl` `a7610f39be9453985123de49b5a953cfe091dcdc4c98e93ea56557b9d1593fc9`; `plan.jsonl` `4fd46e1f6900bfbd9bc7b1def94a0221335526e38ce5a68a900fbcd0e19ddf3c` | `evidence_completion.json` `runs_sha256`, `plan_sha256` |
| Seed journals | 466 files, manifest `85d9b6b25dec2167e51603e90602a6ecc737dbe3bae648a1a77d2faa7792288e` | `pins.json` `seed_journals.manifest_sha256` |
| Host table | `proposals.jsonl` `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4`; `configs.json` `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df`; `build.json` `c14a68aec5ce8e408923930b63ba057503f14bd82b6e1f077879c3deb03a48ee` | `evidence_completion.json` |
| Sweep-1 index / classification | `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab` / `bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc` | `evidence_completion.json` |
| Report | `REPORT.md` sha256 `ef19cb421f5b6236ccf48b7ffa177605032a2fcc59c29eace624034703b80dc1` | SUMS line 14 |
| Review | `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md`, VERDICT: ACCEPTED (no blocker, no major, four minors) | the review, "Bottom line" and last line; merged in `dc3b4284` |
| Release receipt sha256 | `f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1` | `docs/r1/reports/release_20261122/SWEEP1_TRAINDEV_RELEASE_20261123.md` line 26; release review §1 |
| Partition sha256 | `6a6327a3731dc2d874822e009f3b2d84fbf1a6cbabfef505c657f90b14fd7b2a` | receipt `outputs["label_block.traindev.jsonl"]`; release report line 33 |
| Release review | `docs/r1/reviews/SWEEP1_TRAINDEV_RELEASE_REVIEW_20261123.md`, VERDICT: ACCEPTED | the review, last line; merged in `a454d6db` |

## 3. The train/dev release this record binds

- **Receipt.** `docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json` (the committed copy of the live
  `RECEIPT.json`; the release review §1 found them equal), sha256 `f06e37a9…65c1`. Schema
  `r1_c3_release_receipt/v2`; row `R1-S2-LABELS-TRAINDEV-RELEASE`; source `sweep1`; stage `traindev`; tier T0;
  `inputs.label_block_sha256` = `cdae9c3f…9aca` (the block frozen here); `inputs.proposals_sha256` =
  `b713c423…d57c4`; `integrity.pass` true.
- **Partition.** `label_block.traindev.jsonl`, sha256 `6a6327a3…7b2a`; 869 released rows (train 593, dev 276); 856
  test rows not released; evaluation rows 0 (receipt `counts`).
- **What a reader checks.** The P.4 job pins the partition and receipt sha256 from its spec (`labels.partition_sha256`,
  `labels.receipt_sha256`) and requires the receipt's source block to be `cdae9c3f…9aca` (`p4_phase1.check_partition`);
  `LabelBlockSource` re-checks the receipt bindings (`release.open_partition`).

## 4. Final verification

The final verification of the frozen audit is the **release step's integrity check** of 23 November 2026, the one
recorded in the receipt bound in §3. It is the same run as the "sweep-1 compat" verification: the release step's
sweep-1 integrity check is `release_checks.sweep1_integrity`, which calls
`audit.verify_evidence_completion(table, <audit>/label_block.jsonl, paper_root, index, classification,
replay_builder=sweep1_compat.rebuild_v2_table)` (R1-SWEEP1-RELEASE-COMPAT option A; R1-SWEEP1-RELEASE-COMPAT-SCOPE
(1) names the `replay_builder` parameter). That call re-derives both role blocks from the raw runs and binds the
completion record (`release_checks.py` docstring; `audit.py`).

- **What was run** (`SWEEP1_TRAINDEV_RELEASE_20261123.md` lines 12–20):
  `python -B -m r1.c3.release --stage traindev --source sweep1 --table /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table --audit /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/output --out /work/dwong/s2_release_20261123/release_sweep1_traindev --paper-root /work/dwong/s2_audit_20261122/paper --index /work/dwong/s2_audit_20261122/paper/results/r1/pilot/C3_sweep_index_20261028T033315Z.json --classification /work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep_classification_20261028.json`
- **Where and at what code.** deepthought, from the checkout `/work/dwong/s2_audit_20261122/paper` at published main
  `3522e59bf52e738c92981a1ffde67527059f071b`, tracked clean; interpreter `/ceph/dwong/r1_prepare_20261025/venv/bin/python3`
  (release report lines 5–8; release review §2). Release code `a9d8ff5e6964ae25730b266d854927d85dc99c94`;
  `release_checks.py` sha256 `c97b60e98f4bcd9ac731fd62a9d712dd8e8267a00b01c00f869f43dd4260cbbf` (receipt).
- **When.** Receipt `utc` `2026-11-23T09:23:16Z`.
- **By whom.** The release report names no operator. The commit that recorded it (`e3536d83`, author field "Dowling
  Wong", 2026-11-23 10:23:53 +0100) carries the trailer "AI-assisted: DeepSeek Harness agent, 23 Nov 2026". The
  independent review is by `reviewer-sweep1-release` (read-only; `SWEEP1_TRAINDEV_RELEASE_REVIEW_20261123.md`).
- **Result.** PASS: receipt `integrity.check` `audit.verify_evidence_completion`, `integrity.pass` true,
  `integrity.completion_sha256` `e28bee5e…43b4`, equal to the frozen completion record; the 13 kept completion fields
  equal the live completion record (release review §1). The review also found the sealed table and audit files
  byte- and mtime-unchanged (release review §2).
- **Not the final verification.** The 22 November real-data call of `release_checks.sweep1_integrity` in
  `SWEEP1_RELEASE_COMPAT_20261122.md` ran at the unpublished commits `6f713ede`/`b2b7489a`, before the
  `_sweep1_compat_published` guard existed; the report itself records that caveat. It is superseded by the 23 Nov
  release-step run.
- **Why not a separate run now.** On `main`, `audit.verify_evidence_completion` calls
  `release.require_integrity_or_test_release("T0", …)`, which refuses outside the release step's integrity check until
  the T0 test release row exists (PRE-STAGE A, §6 integrity carve-out; `r1/c3/release.py`
  `require_integrity_or_test_release`). A new verification before that row is therefore only a new release-step run
  (new `--out`), which writes a new receipt.

## 5. Errata (from the review's four minors) and the co-tenancy reading

`REPORT.md` stays byte-identical; these correct or complete it and change no frozen value.

- **E1 (MINOR-1).** `REPORT.md` (header and §8) gives the preserved 18 Nov directory's `paper/.git/` mtime as
  "(00:18Z)". The review observed `2026-11-19T00:52:06Z`. The substantive statement stands: all files keep their
  18 Nov mtimes, `.git/index` was not rewritten, and no other directory changed. The review's traceability note: the
  committed `REPORT.md` was edited after the retained `assemble.log` run, so the retained assembly script and log do
  not reproduce the committed bytes.
- **E2 (MINOR-2), the co-tenancy reading.** The addendum's runtime rule is about other users' load. `REPORT.md` §3.1
  gives seven raw 1-min load samples (29.72, 30.45, 32.46, 30.60, 30.60, 30.71, 28.64) that include the audit's 16
  workers. Read as idle cores (40 − load) they are below 10 in five of the seven samples (the review counts four).
  Read as cores not used by other users (40 − (load − 16)) they are 23.54–27.36, so no STOP. At launch the review
  reads the rule by R1-B2-GO's footprint rule (40 − 16 = 24 ≥ 10) with the launch check 40 − 15.39 = 24.61, not the
  literal 40 − 15.39 − 16 = 8.61. The review accepted the other-users reading. **Signing this record adopts it.**
  Under the idle-core reading the runtime rule would have stopped the audit; if the author does not adopt the
  other-users reading, this record is not signed.
- **E3 (MINOR-3).** The interpreter basis records the e1 canonical package-list hash `c09242ac…`; every
  `worker_runtime` record carries `a089bbf1…`, the audit's JSON-normalised package-list hash. The two functions
  canonicalise names differently; both bind the same venv (`validate_worker_records` and the start checks). Not a
  contradiction.
- **E4 (MINOR-4).** No label table existed before this audit, and the audit read none. Every label value in the label
  block was produced by this audit from its own raw runs; the table, plan and raw runs carry no label field.

## 6. Rules (the signature adopts them)

1. **Identity.** The sweep-1 label table is exactly the bytes with sha256 `cdae9c3f…9aca`; the sha256 is the identity,
   not the path. A consumer checks it before use; a mismatch is a STOP.
2. **Reading.** Consumers read sweep-1 labels only through receipted partitions (PRE-STAGE A): train/dev through the
   receipt of §3, test labels and the evaluation block only after a T0 test release row. Copies of the raw blocks are
   committed under `docs/r1/reports/b2_audit_20261119/`; reading them before that row is a STOP
   (`release.guard_raw_label_path`).
3. **Seed roles.** Seeds 7006–7010 (the evaluation block, the 7006–7010 rows of `runs.jsonl` and of the seed journals)
   are never used for C3 or Track P training, tuning or selection, nor for retraining (R1-B2-DECOUPLE; the addendum's
   Scope; R1-MAIN-PROPOSER (e)). Evaluation uses stay as the PLAN rows allow; this record grants no exception
   (R1-BX-D3). Integrity verification (§4) is not a use.
4. **No edits; retention.** Nothing in `docs/r1/reports/b2_audit_20261119/` is edited; corrections go into dated errata
   of this record. The retained attempt directory (with `table/` and `output/`), the authoritative output, the seed
   journals and the preserved 18 Nov STOP directory are kept and never deleted. A byte-preserving `git mv` under the
   R1-LAYOUT-FLATTEN path map is not an edit.
5. **Disclosures carried.** Those of the corpus freeze (`C3_B1_CORPUS_FREEZE_20261031.md`) and of `REPORT.md` §6: the
   environment basis is the e1-replay current-state observation, not a launch-bound freeze; the worker-runtime probe
   does not attest the task process itself.

## 7. Scope and non-claims

- Sweep 1 only: no sweep-2 or T1 label table (sweep 2 is R1-SWEEP2-LABELS-FREEZE).
- No authorization to train. P.4 phase 1 needs its own signed note (`trackp_p4_<date>.md`); this record is its P1
  together with the receipt of §3.
- It does not settle R1-BX-D3 and does not, by itself, satisfy the R1-LAYOUT-FLATTEN labels-freeze gate.
- It changes no frozen value of `C3_B1_CORPUS_FREEZE_20261031.md`.

## 8. Signature and the P.4 binding

1. The author resolves every `TODO_VERIFY_ON_HOST` above, checks §2 against the cited records, and accepts §4 as the
   final verification and §5 E2.
2. On the author's instruction the coordinating chat changes only: the heading's "(approved: false)"; the Status
   paragraph; in the key block, `approved` from false to true, `signed_by`, `signed_utc` and `author_instruction`.
   It publishes the file on `main` at this path.
3. After that commit, and not before, the sha256 of the published file's bytes (`git show origin/main:<this path> |
   sha256sum`) goes into the P.4 spec's `labels.freeze_record.sha256` (with `labels.freeze_record.path` = this path)
   and into the P.4 note's `label_freeze:` line. The spec's `paper.commit` must contain this file at that sha256 (the
   job checks it in its clone). Any later edit of this file changes the sha256 and STOPs the job.
