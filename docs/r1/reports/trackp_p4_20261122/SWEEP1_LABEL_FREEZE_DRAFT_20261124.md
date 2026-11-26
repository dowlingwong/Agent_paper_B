# Sweep-1 label freeze record — draft report (24 November 2026, revision 3)

Unit: `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md`, key `approved: false`, for the author's signature
(P.4 phase-1 prerequisite P1). Prepared by the Mac-desk agent (Claude), AI-assisted, from published `main` `3024db3f`.
Revision 2 fixed the independent review of `3a23679ec` (NOT ACCEPTED: M1, m1–m7); revision 3 fixes the round-2
review of `b24eb2c96` (NOT ACCEPTED: M1, m1, m2). §7 maps each finding to its fix.
No label or evaluation value was read: the work used committed records (hashes, counts, ids) and the runner's code
only.

## 1. What the P.4 runner checks in this record

Runner branch `mac-trackp-p4-runner-20261122`, now at `de6dd56d6` (local branch; it moved `7ab79a9d8` → `4e26995a2`
→ `9365c42aa` → `d7d5a32f3` → `12fa43ee2` → `de6dd56d6` during this unit). Its `p4_lib.py`, `p4_switch.py`,
`p4_spec.json`, `p4_phase1.py` and the runner test changed since `7ab79a9d8`. The record checks are the same except
one addition at `de6dd56d6`: the job reads the record as UTF-8 whatever the locale (`_read_utf8`), and a non-UTF-8
record is a `ProtocolStop`. The record is UTF-8 with LF line ends. Line numbers below are at `de6dd56d6`.

| Where | Check |
|---|---|
| `p4_lib.validate_spec` (lines 233–238) | `labels.freeze_record.path` must match `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md` (a `TODO…` placeholder only when not at launch strength); `labels.freeze_record.sha256` must be 64 hex characters at launch strength (`_pin`). |
| `p4_lib.inputs`, job step 5 (lines 454–462) | The file at that path in the job's clone of `paper.commit` must exist and have exactly the spec's sha256. Its text must contain a line consisting of `approved:`, one space and `true` (regex with `re.M`, so no trailing space and no other text on the line), and the full block sha256 `cdae9c3f…9aca` (`SOURCE_BLOCK_SHA256`) anywhere; the text is decoded as UTF-8. Otherwise `ProtocolStop` "not a signed freeze of the block". Nothing else in the record is parsed. |
| `p4_lib.data_argv` (line 550) | Passes `--label-freeze <clone>/<path>` to `trackp.py sft-data`. |
| `sft_data.LabelBlockSource` (main) | The freeze path is passed through `refuse_evaluation_path` (no "evaluation" or "eval_block" in the name) and `analysis_guard.refuse_sealed` (no `r1_sealed` component); its path and sha256 go into the data manifest's provenance (`freeze`). |
| `p4_switch.check_binding` (line 117) | The signed P.4 note's `label_freeze:` line must contain the spec's freeze path and freeze sha256. `parse_note` requires the field, and `P_CITES` (line 47) requires `P1` to cite `C3_SWEEP1_LABEL_FREEZE_`. |
| `p4_lib.verify_launch_p4` (line 918 ff.) | Compares the launch checkout with `paper.commit` only outside `docs/` and the spec file: the record is not checked at launch, only in the job's clone. |

For the runner, "signed" therefore means: the `approved` key line reads true, the block hash is present, and the bytes
are those whose sha256 the spec pins. There is no front-matter parser, no `signed_by` check and no check of the other
bound values; those are for the author and the reviewer.

## 2. Source of every bound value

The record's §2 table gives file and field for each value. A mechanical check (`git grep` of every 64-hex and 40-hex
string of the record on `origin/main` `3024db3f`) finds each one in a committed record on main, **except three**.
These are not copied from a record. They are the sha256s of three committed, non-sealed files on main, and anyone
can reproduce them from GitHub:

| Value | Reproducible source on main | Blob id (unchanged at `94db94bb` and `3024db3f`) |
|---|---|---|
| Review sha256 `d62d09f102150f1909386587de5761fa9583013fe170216fe3ee7614c3f0014b` | `git show 3024db3f:docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md \| sha256sum` | `4a71ff9d3f89af6659e211acee47d8d955b5b4e2` |
| `SHA256SUMS` sha256 `1c1a95a0b14ce315f60fe5c682a8d9f9d108350f8902224fb0347ca77cfcc3f7` | `git show 3024db3f:docs/r1/reports/b2_audit_20261119/SHA256SUMS \| sha256sum` | `902a8fd44b295d4a718b251de590e90dab1fae1e` |
| `OUTPUT_SHA256SUMS` sha256 `af13b0f4cf886e5f53efee5fbcaed427dc67e874e9ff2a4a0cde94c618a90754` | `git show 3024db3f:docs/r1/reports/b2_audit_20261119/OUTPUT_SHA256SUMS \| sha256sum` | `e0d47c2c3b5d1cf8a14c4b6c0869e50fad0ad5cc` |

I ran these three commands and got the values shown. The blob ids were checked with `git rev-parse <commit>:<path>`
at both commits. As corroboration only, the 20 Nov draft at `dde24f6f` gives the same values (lines 54, 302 and
103); `dde24f6f` is on an unpushed local branch (`git branch -r --contains dde24f6f` is empty), so it cannot be
checked from GitHub.

**The 18 Nov attempt's id.** No committed record uses the bare id `b2-435513d2-20261118T012807Z`. The records name the
attempt by its code (`435513d2`) and its directory `/ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse`
(`REPORT.md` line 18; `pins.json` `preserved_stop_dir.path`; `docs/r1/reports/b2_sweep1_20261118/PREFLIGHT_435513D2_STOP.md`).
Revision 3 of the record names it the same way. Earlier revisions used the bare id, which was this unit's
shorthand.

Other sources, in brief:
- **Audit records** (`docs/r1/reports/b2_audit_20261119/`): `SHA256SUMS` lines 3, 10, 11, 13, 14; `PASS.json`;
  `evidence_completion.json`; `START.json`; `pins.json` (`retained`, `output.seed_journals.manifest_sha256`);
  `REPORT.md` (line 4, lines 11–12, §3.1, §6, §8).
- **Release records:** `RECEIPT_sweep1_traindev.json`; `SWEEP1_TRAINDEV_RELEASE_20261123.md` lines 5–33.
- **Reviews:** `B2_AUDIT_RUN_REVIEW_20261119.md`, `SWEEP1_TRAINDEV_RELEASE_REVIEW_20261123.md` (§1, §2, M2); both
  ACCEPTED.
- **Code on main:** `r1/c3/release_checks.py` (`sweep1_integrity`), `r1/c3/audit.py` and `r1/c3/release.py`
  (`require_integrity_or_test_release`, `guard_raw_label_path`); PLAN R1-SWEEP1-RELEASE-COMPAT(-SCOPE).
- **Who ran the final verification:** commit `e3536d83` trailer ("AI-assisted: DeepSeek Harness agent, 23 Nov 2026")
  and the release review's reviewer id.

**`AUDIT_SEAL.json`.** Sweep 1 has none. `pins.json` `retained` lists the attempt directory, output, scratch and logs;
`REPORT.md` §8 lists the retained artifacts; neither names a seal file. `git grep AUDIT_SEAL` outside `docs/` and
`papers/` finds nothing at `ab79b4ce` or on main. The record binds the sweep-1 seal records (`PASS.json`,
`SHA256SUMS`, `OUTPUT_SHA256SUMS`) by sha256 and writes `audit_seal_sha256: not_applicable` with this reason. The
runner does not read that field.

**The final verification.** The release step's integrity check of 23 November (receipt `utc` 2026-11-23T09:23:16Z,
deepthought, published main `3522e59b`). The receipt records only `audit.verify_evidence_completion`; that it ran with
`replay_builder=sweep1_compat.rebuild_v2_table` is inferred from the `release_checks_sha256` pin, as the release
review states in §2 and records as its M2. The 22 November compat call ran before its guard existed, at unpublished
commits; it is not the final verification. A new standalone run is not possible before the T0 test release row.

## 3. Format check and tests

Scratch detached worktree `/tmp/p4frzdev/rw` of the runner branch at `de6dd56d6` (revision 3; revision 2 was checked at
`12fa43ee2` with the same results), the draft copied in, and the runner's
own functions called by an uncommitted script (`/tmp/p4frzdev/check_freeze.py`). The partition and receipt are
synthetic, as in `test_inputs_lay_out_and_check_the_transferred_files`, and the spec is the shipped `p4_spec.json`
with scratch fills, as the tests' `filled()`. Python `/tmp/tgport312/bin/python -I`.

| Input | `validate_spec(launch=True)` | path guards | `p4_lib.inputs` |
|---|---|---|---|
| Draft as committed (key `approved: false`) | PASS | PASS | **STOP** (`ProtocolStop`: "… is not a signed freeze of the block cdae9c3f…9aca (P1)") |
| Scratch copy, differing from the draft in exactly one line (the `approved` key flipped to true) | PASS | PASS | **PASS** |
| Scratch negative: flipped copy with the block hash removed | PASS | PASS | STOP (same message) |
| Scratch full signature edit (heading, Status, the four key lines of §8.3); no PENDING key line left | PASS | PASS | PASS |

The draft contains the full block hash, and flipping the one key line is enough for the job's check to pass, so the
draft fails only on the signature. No flipped copy was written to the repository. The draft's sha256 at this commit
was `a6789f4f…fb6c`. That value is for this check only and is not the one to bind: signing changes the bytes (§5).

`AR_HARNESS_ROOT=/tmp/pb/wt/t1h python -m pytest -q r1/tests/test_trackp_p4_runner.py` in the same worktree:
**88 passed** at `de6dd56d6` (87 passed at `12fa43ee2` in revision 2).

## 4. What the author checks before signing

1. **No open field.** The record has no `TODO_VERIFY_ON_HOST`. The only PENDING fields are the three signature
   fields. Record §8.2: it is not signed while any other field holds either.
2. **The bound values** against the records (record §2), including the three values copied from the 20 Nov draft
   (§2 above).
3. **The final verification:** accept the 23 Nov release-step integrity check (PASS) as the final verification that P1
   asks for, including that its compat replay builder is inferred from the `release_checks_sha256` pin.
4. **Errata E2:** signing adopts the other-users reading of the co-tenancy rule. If the author does not adopt it, the
   record is not signed.
5. **Replacement:** the record states that it replaces the unmerged 20 Nov draft (`dde24f6f`), and that only this
   file is signed. The flatten gate is fixed as "not satisfied by this record alone"; that draft's D1-B is not
   offered.
6. **The signature edit** is limited to what record §8.3 lists.

## 5. How the spec binds the record's sha256 after signing

1. **Signature (author; the coordinating chat edits).** The heading's "(approved: false)", the Status paragraph, and
   the key lines `approved` (false to true), `signed_by`, `signed_utc` and `author_instruction` change. The file is
   published on `main` at the same path; that commit is the signing commit. The filename date stays `20261124`: the
   runner accepts any eight digits, and a rename would add a path change to the spec and the note.
2. **sha256 (the Mac-desk agent or the coordinating chat, after the signing commit exists).**
   `git show <signing commit>:docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md | sha256sum`, or the same at
   `paper.commit` if the file is unchanged between the two. It goes into `p4_spec.json` `labels.freeze_record.sha256`
   (with `labels.freeze_record.path` set to this path, replacing the `TODO` placeholders) and into the P.4 note's
   `label_freeze:` line. At the same time the partition and receipt pins (`6a6327a3…`, `f06e37a9…`) go into the
   spec's `labels.partition_sha256` and `labels.receipt_sha256` and the note's `labels:` and `label_receipt:` lines.
3. **Paper commit.** The job clones `paper.commit` and checks the record there, so `paper.commit` must be the signing
   commit or a later commit holding the same bytes. The spec file is excluded from the launch binding's tree
   comparison, so it can be updated after `paper.commit`; the note's `spec_sha256` then pins it.
4. **Later edits.** An erratum or withdrawal published after `paper.commit` does not stop a job. The job still reads
   the signed bytes at `paper.commit`, and `verify_launch_p4` ignores `docs/`. Record §8.5 (procedural; not enforced
   by the runner; adopted by the signature) therefore requires the coordinating chat to report such a change to the
   author before any further P.4 submission. A run that is to use the changed record
   needs a new spec (a new `paper.commit` and freeze sha256) and a new note.

**Proposed PLAN row** (R1-SWEEP2-LABELS-FREEZE is a PLAN row; the sweep-1 freeze gets one too, added after the
signing commit; the id and wording are for the author):

| ID | Decision |
|---|---|
| R1-C3-SWEEP1-LABELS-FROZEN | The sweep-1 label table is the audit `b2-ab79b4ce-20261119T002306Z`, the second authorized sweep-1 B.2 EVIDENCE attempt (output `results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z`, retained at `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/`): `evidence_completion.json` sha256 `e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4`, label block `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca`, evaluation block `297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67`; report `reports/b2_audit_20261119/REPORT.md` and review `reviews/B2_AUDIT_RUN_REVIEW_20261119.md` on main. This is the author's label-table freeze, signed in `authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md` (sha256 `<at the signing commit>`), which replaces the unmerged 20 Nov draft. The 18 Nov attempt at code `435513d2` (directory `b2-435513d2-20261118T012807Z.veDjse`) is not a label source. Final verification: the 23 Nov release-step integrity check, PASS. The labels stay sealed except as released by R1-S2-LABELS-TRAINDEV-RELEASE (train/dev; receipt `f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1`) and, after the arms-frozen record, R1-S2-LABELS-TEST-RELEASE; copies of the raw blocks committed under `docs/r1/reports/b2_audit_20261119/` are not read before that row. It does not by itself satisfy the R1-LAYOUT-FLATTEN labels-freeze gate. |

The runner's `PLAN_ROWS` does not require this row; it is the record of the decision in PLAN §10.

## 6. Points of uncertainty

- The final-verification reading (record §4) is this unit's interpretation of P1's "final verification PASS". It
  follows from the code and records, but the author or reviewer may prefer a fresh release-step run.
- Three bound hashes are sha256s of committed files on main, taken with `git show`, not values copied from a record
  (§2). Their blobs are unchanged since `94db94bb`.
- The release report names no operator; "DeepSeek Harness agent" comes from the commit trailer only.
- E2: the review counts four of the seven runtime samples below 10 idle cores; the load figures in `REPORT.md` §3.1
  give five. The record states both.
- The record sits under `docs/r1/authorizations/` while unsigned, as requested; earlier drafts of signed records lived
  under `docs/r1/proposals/`. The runner refuses it unsigned.
- Record §8.5 (the coordinating chat reports a later erratum or withdrawal to the author before further
  submissions) is procedural. The runner does not enforce it; signing adopts it.

## 7. Review of `3a23679ec`: findings and fixes

| Finding | Fix (record = `C3_SWEEP1_LABEL_FREEZE_20261124.md`) |
|---|---|
| M1: signature edit list incomplete; TODO left for the author | `audit_seal_sha256` is now `not_applicable` with the reason (record key block; §1 table; §2 row). The Status paragraph lists `approved` among the four key lines that change. New rule §8.2: the record is not signed while any field other than the three signature fields holds `TODO_VERIFY_ON_HOST` or PENDING. No `TODO_VERIFY_ON_HOST` remains. |
| m1: "any later edit STOPs the job" wrong; sha256 taken from `origin/main` | Record §8.4: the sha256 is taken at the signing commit (or at `paper.commit`). Record §8.5 and report §5.4 now say what happens: a later erratum or withdrawal does not reach a job, so it goes to the author before further submissions, and a new spec and note are needed. |
| m2: runner tip and test status out of date | Report §1 had tip `12fa43ee2` and its line numbers (now `de6dd56d6`, revision 3). Report §3: the format check was re-run at `12fa43ee2`, and the runner test ran with `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`: 87 passed. |
| m3: E4 wording | E4 now says "no pre-existing label table was read", and that the consumption pass read the block the audit had just written. |
| m4: material from `dde24f6f` | E2 restored: the estimate basis (exactly 16 added; parent and probe ignored), seven operator samples because `resource_monitor` did not sample CPU, five of seven. Rule 3 restored: an unclear evaluation use is a STOP, plus the R1-BX-D3 gate-stability note. Rule 4: the force-add past `.gitignore` line 49 note. Review sha256 `d62d09f1…`, `SHA256SUMS` `1c1a95a0…` and `OUTPUT_SHA256SUMS` `af13b0f4…` are bound (key block, §2), with their source (report §2). Proposed PLAN row: report §5. Record §8.1: D1-B not offered. |
| m5: replacement of the 20 Nov draft | Status section and the key `replaces:` say that this record replaces `dde24f6f`'s draft and that only this file is signed. |
| m6: replay builder inferred, not recorded | Record §4 and the key `final_verification:` separate what the receipt records from what is inferred from the `release_checks_sha256` pin, citing release review §2 and M2. |
| m7: `pins.json` field path | Record §2: `pins.json` `output.seed_journals.manifest_sha256`. |

**Round 2 (review of `b24eb2c96`).**

| Finding | Fix |
|---|---|
| M1: three hashes cited only from the unpushed `dde24f6f` | Record §2 (SUMS and Review rows): the source is now `git show 3024db3f:<path> \| sha256sum`, with the blob ids `902a8fd4…`, `e0d47c2c…` and `4a71ff9d…`, unchanged since `94db94bb`. `dde24f6f` is kept as corroboration, marked "(unpushed local branch)". The record's preamble now says these three are sha256s of committed, non-sealed files, taken with `git show`, not values copied from a record. Report §2 gives the commands and blob ids. |
| m1: record §8.5 status and party | §8.5 is headed "(procedural; not enforced by the runner; signing adopts this rule)" and names the coordinating chat as the party that reports a later erratum or withdrawal to the author. Report §5.4 and §6 match. |
| m2: proposed PLAN row form | Report §5's row now follows R1-SWEEP2-LABELS-FREEZE: the attempt and output, the retained path, the three hashes, the report and the review, the signed file, the attempt that is not a label source, and the closing clause on what stays sealed until the test release row. Verification of the attempt id: committed records name the 18 Nov attempt only by code `435513d2` and directory `b2-435513d2-20261118T012807Z.veDjse`, never by the bare id. The row and the record (key `not_label_sources`, §1 and its table) now use that form (report §2). |
| (no finding) runner moved again to `de6dd56d6` | Report §1 and §3 updated: the new UTF-8 read of the record, the line numbers, the format check re-run (draft as committed fails only on the signature; flipped copy and full signature simulation pass), runner test 88 passed. |
