# Sweep-1 label freeze record — draft report (24 November 2026, revision 2)

Unit: `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md`, key `approved: false`, for the author's signature
(P.4 phase-1 prerequisite P1). Prepared by the Mac-desk agent (Claude), AI-assisted, from published `main` `3024db3f`.
Revision 2 fixes the independent review of `3a23679ec` (NOT ACCEPTED: M1, m1–m7; §7 maps each finding to its fix).
No label or evaluation value was read: the work used committed records (hashes, counts, ids) and the runner's code
only.

## 1. What the P.4 runner checks in this record

Runner branch `mac-trackp-p4-runner-20261122`, now at `12fa43ee2` (local branch; it moved `7ab79a9d8` → `4e26995a2`
→ `9365c42aa` → `d7d5a32f3` → `12fa43ee2` during this unit). Its `p4_lib.py`, `p4_switch.py`, `p4_spec.json`,
`p4_phase1.py` and the runner test changed since `7ab79a9d8`, but the record checks did not; only their line numbers
moved. Line numbers below are at `12fa43ee2`.

| Where | Check |
|---|---|
| `p4_lib.validate_spec` (lines 233–238) | `labels.freeze_record.path` must match `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md` (a `TODO…` placeholder only when not at launch strength); `labels.freeze_record.sha256` must be 64 hex characters at launch strength (`_pin`). |
| `p4_lib.inputs`, job step 5 (lines 443–451) | The file at that path in the job's clone of `paper.commit` must exist and have exactly the spec's sha256. Its text must contain a line consisting of `approved:`, one space and `true` (regex with `re.M`, so no trailing space and no other text on the line), and the full block sha256 `cdae9c3f…9aca` (`SOURCE_BLOCK_SHA256`) anywhere. Otherwise `ProtocolStop` "not a signed freeze of the block". Nothing else in the record is parsed. |
| `p4_lib.data_argv` (line 538) | Passes `--label-freeze <clone>/<path>` to `trackp.py sft-data`. |
| `sft_data.LabelBlockSource` (main) | The freeze path is passed through `refuse_evaluation_path` (no "evaluation" or "eval_block" in the name) and `analysis_guard.refuse_sealed` (no `r1_sealed` component); its path and sha256 go into the data manifest's provenance (`freeze`). |
| `p4_switch.check_binding` (line 117) | The signed P.4 note's `label_freeze:` line must contain the spec's freeze path and freeze sha256. `parse_note` requires the field, and `P_CITES` (line 47) requires `P1` to cite `C3_SWEEP1_LABEL_FREEZE_`. |
| `p4_lib.verify_launch_p4` (line 905 ff.) | Compares the launch checkout with `paper.commit` only outside `docs/` and the spec file: the record is not checked at launch, only in the job's clone. |

For the runner, "signed" therefore means: the `approved` key line reads true, the block hash is present, and the bytes
are those whose sha256 the spec pins. There is no front-matter parser, no `signed_by` check and no check of the other
bound values; those are for the author and the reviewer.

## 2. Source of every bound value

The record's §2 table gives file and field for each value. A mechanical check (`git grep` of every 64-hex and 40-hex
string of the record on `origin/main` `3024db3f`) finds each one on main, **except three**, which the review (m4)
asked to bind and which no record on main carries:

| Value | Source |
|---|---|
| Review sha256 `d62d09f102150f1909386587de5761fa9583013fe170216fe3ee7614c3f0014b` | the committed 20 Nov draft at `dde24f6f`, lines 54 and 302 |
| `SHA256SUMS` sha256 `1c1a95a0b14ce315f60fe5c682a8d9f9d108350f8902224fb0347ca77cfcc3f7` | the same draft, line 103 |
| `OUTPUT_SHA256SUMS` sha256 `af13b0f4cf886e5f53efee5fbcaed427dc67e874e9ff2a4a0cde94c618a90754` | the same draft, line 103 |

That draft records them as checked at main `94db94bb`; the three files are unchanged on main since `94db94bb`. As a
cross-check only (not as the source), `git show origin/main:<file> | sha256sum` of the three committed files (none of
them sealed data) gives the same three values.

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

Scratch detached worktree `/tmp/p4frzdev/rw` of the runner branch at `12fa43ee2`, the draft copied in, and the runner's
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
was `aa3459ac…51d5`. That value is for this check only and is not the one to bind: signing changes the bytes (§5).

`AR_HARNESS_ROOT=/tmp/pb/wt/t1h python -m pytest -q r1/tests/test_trackp_p4_runner.py` in the same worktree:
**87 passed**.

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
   the signed bytes at `paper.commit`, and `verify_launch_p4` ignores `docs/`. Record §8.5 therefore requires that
   such a change be reported to the author before any further P.4 submission. A run that is to use the changed record
   needs a new spec (a new `paper.commit` and freeze sha256) and a new note.

**Proposed PLAN row** (R1-SWEEP2-LABELS-FREEZE is a PLAN row; the sweep-1 freeze gets one too, added after the
signing commit; the id and wording are for the author):

| ID | Decision |
|---|---|
| R1-C3-SWEEP1-LABELS-FROZEN | The sweep-1 label table is frozen by the signed `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md` (sha256 `<at the signing commit>`): audit `b2-ab79b4ce-20261119T002306Z`, `evidence_completion.json` `e28bee5e…`, label block `cdae9c3f…9aca`, evaluation block `297fed47…`; train/dev released by receipt `f06e37a9…`; final verification the 23 Nov release-step integrity check, PASS. It replaces the unmerged 20 Nov draft. It does not by itself satisfy the R1-LAYOUT-FLATTEN labels-freeze gate. |

The runner's `PLAN_ROWS` does not require this row; it is the record of the decision in PLAN §10.

## 6. Points of uncertainty

- The final-verification reading (record §4) is this unit's interpretation of P1's "final verification PASS". It
  follows from the code and records, but the author or reviewer may prefer a fresh release-step run.
- Three bound hashes come from the committed but unmerged 20 Nov draft, not from main (§2). They match a cross-check
  on main's files.
- The release report names no operator; "DeepSeek Harness agent" comes from the commit trailer only.
- E2: the review counts four of the seven runtime samples below 10 idle cores; the load figures in `REPORT.md` §3.1
  give five. The record states both.
- The record sits under `docs/r1/authorizations/` while unsigned, as requested; earlier drafts of signed records lived
  under `docs/r1/proposals/`. The runner refuses it unsigned.
- Record §8.5 (a later erratum or withdrawal goes to the author before further submissions) is a proposed rule. The
  runner does not enforce it.

## 7. Review of `3a23679ec`: findings and fixes

| Finding | Fix (record = `C3_SWEEP1_LABEL_FREEZE_20261124.md`) |
|---|---|
| M1: signature edit list incomplete; TODO left for the author | `audit_seal_sha256` is now `not_applicable` with the reason (record key block; §1 table; §2 row). The Status paragraph lists `approved` among the four key lines that change. New rule §8.2: the record is not signed while any field other than the three signature fields holds `TODO_VERIFY_ON_HOST` or PENDING. No `TODO_VERIFY_ON_HOST` remains. |
| m1: "any later edit STOPs the job" wrong; sha256 taken from `origin/main` | Record §8.4: the sha256 is taken at the signing commit (or at `paper.commit`). Record §8.5 and report §5.4 now say what happens: a later erratum or withdrawal does not reach a job, so it goes to the author before further submissions, and a new spec and note are needed. |
| m2: runner tip and test status out of date | Report §1 now has tip `12fa43ee2` and its line numbers. Report §3: the format check was re-run at `12fa43ee2`, and the runner test ran with `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`: 87 passed. |
| m3: E4 wording | E4 now says "no pre-existing label table was read", and that the consumption pass read the block the audit had just written. |
| m4: material from `dde24f6f` | E2 restored: the estimate basis (exactly 16 added; parent and probe ignored), seven operator samples because `resource_monitor` did not sample CPU, five of seven. Rule 3 restored: an unclear evaluation use is a STOP, plus the R1-BX-D3 gate-stability note. Rule 4: the force-add past `.gitignore` line 49 note. Review sha256 `d62d09f1…`, `SHA256SUMS` `1c1a95a0…` and `OUTPUT_SHA256SUMS` `af13b0f4…` are bound (key block, §2), with their source (report §2). Proposed PLAN row: report §5. Record §8.1: D1-B not offered. |
| m5: replacement of the 20 Nov draft | Status section and the key `replaces:` say that this record replaces `dde24f6f`'s draft and that only this file is signed. |
| m6: replay builder inferred, not recorded | Record §4 and the key `final_verification:` separate what the receipt records from what is inferred from the `release_checks_sha256` pin, citing release review §2 and M2. |
| m7: `pins.json` field path | Record §2: `pins.json` `output.seed_journals.manifest_sha256`. |
