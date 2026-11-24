# Sweep-1 label freeze record — draft report (24 November 2026)

Unit: `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md`, key `approved: false`, for the author's signature
(P.4 phase-1 prerequisite P1). Prepared by the Mac-desk agent (Claude), AI-assisted, from published `main` `3024db3f`.
For independent review. No label or evaluation value was read: the work used committed records (hashes, counts, ids)
and the runner's code only.

## 1. What the P.4 runner checks in this record

Runner branch `mac-trackp-p4-runner-20261122`. It was at `7ab79a9d8` when this unit started and is now at `4e26995a2`,
a merge of `main` `76a3c71f` into it. The runner files (`p4_lib.py`, `p4_switch.py`, `p4_render_jdl.py`,
`p4_spec.json`, `p4_phase1.py`, the runner test) are byte-identical between the two; only `r1/c3/train/sft_data.py`
differs (main's D4B-contingency refusal, which does not touch the freeze path).

| Where | Check |
|---|---|
| `p4_lib.validate_spec` (lines 220–225) | `labels.freeze_record.path` must match `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_\d{8}\.md` (a `TODO…` placeholder only when not at launch strength); `labels.freeze_record.sha256` must be 64 hex characters at launch strength (`_pin`). |
| `p4_lib.inputs`, job step 5 (lines 429–437) | The file at that path in the job's clone of `paper.commit` must exist and have exactly the spec's sha256. Its text must contain a line consisting of `approved:`, one space and `true` (regex with `re.M`, so no trailing space and no other text on the line), and the full block sha256 `cdae9c3f…9aca` (`SOURCE_BLOCK_SHA256`) anywhere. Otherwise `ProtocolStop` "not a signed freeze of the block". Nothing else in the record is parsed. |
| `p4_lib.data_argv` (line 524) | Passes `--label-freeze <clone>/<path>` to `trackp.py sft-data`. |
| `sft_data.LabelBlockSource` (main) | The freeze path is passed through `refuse_evaluation_path` (no "evaluation" or "eval_block" in the name) and `analysis_guard.refuse_sealed` (no `r1_sealed` component); its path and sha256 are written into the data manifest's provenance (`freeze`). |
| `p4_switch.check_binding` (line 106) | The signed P.4 note's `label_freeze:` line must contain the spec's freeze path and freeze sha256. `parse_note` requires the field and `P1` to cite `C3_SWEEP1_LABEL_FREEZE_`. |

"Signed", for the runner, therefore means: the `approved` key line reads true, the block hash is present, and the
bytes are those whose sha256 the spec pins. There is no front-matter parser, no `signed_by` check and no check of the
other bound values; those are for the author and the reviewer.

## 2. Source of every bound value

All copied from committed records on `main` `3024db3f` (the cited files are unchanged since `76a3c71f`, where the unit started); none was computed. A mechanical check (`git grep` of each
64-hex and 40-hex string of the record on `origin/main`) finds every one in at least one committed file.

| Value | Source |
|---|---|
| Attempt `b2-ab79b4ce-20261119T002306Z`, output, retained attempt directory | `docs/r1/reports/b2_audit_20261119/PASS.json` (`attempt`, `out`, `ceph_attempt_dir`); `REPORT.md` §8 |
| Code commit `ab79b4ce…` | `START.json` `pins.paper_code_commit`; `REPORT.md` line 4 |
| `PASS.json` `cda7d15e…d999`, `evidence_completion.json` `e28bee5e…43b4`, label block `cdae9c3f…9aca`, evaluation block `297fed47…7f67`, `REPORT.md` `ef19cb42…0dc1` | `docs/r1/reports/b2_audit_20261119/SHA256SUMS` lines 10, 13, 11, 3, 14 (and `evidence_completion.json`, `PASS.json`, the receipt) |
| Counts and seeds; runs, plan, host-table, index and classification hashes | `PASS.json` `counts`; `evidence_completion.json` |
| Seed-journal manifest `85d9b6b2…` | `pins.json` `seed_journals.manifest_sha256` |
| Review and verdict | `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md` (VERDICT: ACCEPTED; MINOR-1 to MINOR-4) |
| Receipt `f06e37a9…65c1` | `docs/r1/reports/release_20261122/SWEEP1_TRAINDEV_RELEASE_20261123.md` line 26; release review §1 |
| Partition `6a6327a3…7b2a` | `RECEIPT_sweep1_traindev.json` `outputs`; release report line 33 |
| Final verification: command, host, checkout, interpreter | release report lines 5–20 |
| Final verification: UTC, check name, pass, completion sha256, `head`/`published` `3522e59b…`, release code `a9d8ff5e…`, `release_checks` sha256 `c97b60e9…` | `RECEIPT_sweep1_traindev.json` (`utc`, `integrity.*`, `head`, `published`, `release_commit`, `release_checks_sha256`) |
| Final verification: who | commit `e3536d83` (trailer "AI-assisted: DeepSeek Harness agent, 23 Nov 2026"); reviewer `reviewer-sweep1-release` in the release review |
| Final verification: what the check calls | `r1/c3/release_checks.py` `sweep1_integrity` on main; PLAN R1-SWEEP1-RELEASE-COMPAT and R1-SWEEP1-RELEASE-COMPAT-SCOPE |
| Errata E1–E4 | the review's MINOR-1 to MINOR-4 and traceability note; load samples from `REPORT.md` §3.1 |

**The final verification step.** It is the release step's integrity check of 23 November (receipt `utc`
2026-11-23T09:23:16Z, deepthought, published main `3522e59b`). That check *is* the sweep-1 compat verification:
`release_checks.sweep1_integrity` calls `audit.verify_evidence_completion(..., replay_builder=sweep1_compat.rebuild_v2_table)`.
The 22 November real-data call in `SWEEP1_RELEASE_COMPAT_20261122.md` was pre-guard, at unpublished commits, and the
report flags it as such; it is not the final verification. A new standalone run is not possible before the T0 test
release row: `verify_evidence_completion` on main calls `release.require_integrity_or_test_release("T0", …)`.

## 3. Format check result

Scratch detached worktree `/tmp/p4frzdev/rw` of the runner branch (`4e26995a2`), the draft copied in, and the
runner's own functions called by an uncommitted script (`/tmp/p4frzdev/check_freeze.py`; the partition and receipt
are synthetic, as in `test_inputs_lay_out_and_check_the_transferred_files`; the spec is the shipped `p4_spec.json`
with scratch fills, as the tests' `filled()`). Python `/tmp/tgport312/bin/python -I`.

| Input | `validate_spec(launch=True)` | path guards | `p4_lib.inputs` |
|---|---|---|---|
| Draft as committed (key `approved: false`) | PASS | PASS | **STOP** (`ProtocolStop`: "… is not a signed freeze of the block cdae9c3f…9aca (P1)") |
| Scratch copy, differing from the draft in exactly one line (the `approved` key flipped to true) | PASS | PASS | **PASS** (`label_freeze` = the path and that copy's sha256) |
| Scratch negative: flipped copy with the block hash removed | PASS | PASS | STOP (same message) |

The draft contains the full block hash (asserted), and flipping the one key line is enough for the job's check to
pass, so the draft fails only on the signature. The flipped copy was never written to the repository. The draft's
sha256 at this commit was `a40f9739…0249`. That is for this check only: it is not the value to bind, because
signing changes the bytes (§5).

`pytest -k "inputs_lay_out or shipped_spec"` on the runner test could not run in this environment: the test module's
fixtures (from `test_trackp_sft`) need the harness checkout (`AR_HARNESS_ROOT`). The runner functions were therefore
called directly, as above.

## 4. What the author checks before signing

1. **`TODO_VERIFY_ON_HOST` fields** (one): `audit_seal_sha256`. No sweep-1 record on main names an
   `AUDIT_SEAL.json`; the sweep-1 audit's seal records are `PASS.json`, `SHA256SUMS` and `OUTPUT_SHA256SUMS`. The
   operator confirms on deepthought whether `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/` holds an
   `AUDIT_SEAL.json`. If it does, the sha256 goes in (from a committed record); if not, the field reads "none" with
   that reason. Either way this is resolved before signing, and the record then gets a confirmation review.
2. **The bound values** against the records in §2 (the record's own §2 table gives file and field for each).
3. **The final verification**: that the 23 Nov release-step integrity check (PASS) is accepted as the final
   verification that P1 asks for. The 20 Nov draft (below) planned a separate full run at signature instead; under
   PRE-STAGE A that is now only possible as a new release-step run.
4. **Errata E2**: signing adopts the other-users reading of the co-tenancy rule. If the author does not adopt it, the
   record is not signed.
5. **Which record to sign.** A sweep-1 freeze draft already exists on the unmerged branch
   `mac-sweep1-label-freeze-20261121` (`docs/r1/proposals/C3_SWEEP1_LABEL_FREEZE_DRAFT_20261120.md`, revision 5 at
   `dde24f6f`, independent review ACCEPTED at round 5, `5a8fa2f2`). It uses a `frozen:` key (not `approved:`), plans
   its final verification as a fresh-clone run at signature, and carries author ruling R1 (the same co-tenancy reading
   as E2 here) and decision D1 (layout-flatten gate). This record is written in the format the P.4 runner accepts and
   binds the 23 Nov receipt, which the 20 Nov draft predates. It takes over the errata and the other-users reading,
   and states the flatten gate as "not satisfied by this record alone" (the 20 Nov draft's recommended D1-A). The
   author signs one of the two, not both.
6. That nothing else is open in the key block: `signed_by`, `signed_utc` and `author_instruction` are filled at
   signature; every other line stays.

## 5. How the spec binds the record's sha256 after signing

Signing changes the file's bytes, so the sha256 can only be taken after the signed file is published:

1. **Signature (author; coordinating chat edits).** Only the heading's "(approved: false)", the Status paragraph and
   the key lines `approved` (false to true), `signed_by`, `signed_utc` and `author_instruction` change. The file is
   published on `main` at the same path (the filename date stays `20261124`; the runner accepts any eight digits, and
   renaming would only add a path change to the spec and note).
2. **sha256 (Mac-desk agent or coordinating chat, after that commit is on `main`).** `git show origin/main:docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md | sha256sum`.
   This value goes into `p4_spec.json` `labels.freeze_record.sha256` (with `labels.freeze_record.path` set to this
   path, replacing the `TODO` placeholders) and into the P.4 note's `label_freeze:` line (path and sha256). The
   partition and receipt pins (`6a6327a3…`, `f06e37a9…`) go into the spec's `labels.partition_sha256` and
   `labels.receipt_sha256` and the note's `labels:` and `label_receipt:` lines at the same time.
3. **Paper commit.** The job clones `paper.commit` and checks the record there, so `paper.commit` must be the signing
   commit or a later commit on `main`. The spec file itself is excluded from the launch binding's tree comparison
   (`verify_launch_p4`), so it can be updated after `paper.commit`; the note's `spec_sha256` then pins it.
4. **Afterwards.** Any later edit of the record changes its sha256: the job STOPs (`inputs`) until the spec and the
   note are redone. Errata after signature therefore need a new P.4 spec and note.

## 6. Points of uncertainty

- The final-verification reading (§2, §4.3) is this unit's interpretation of P1's "final verification PASS". It
  follows from the code and records, but the author or reviewer may prefer a fresh release-step run.
- `AUDIT_SEAL.json` for sweep 1 probably does not exist (no record and no code at `ab79b4ce` names it); not verified.
- The release report names no operator; "DeepSeek Harness agent" comes from the commit trailer only.
- E2: the review counts four of seven runtime samples below 10 idle cores; the load figures in `REPORT.md` §3.1 give
  five. The record states both.
- This record sits under `docs/r1/authorizations/` while unsigned, as requested; earlier drafts of signed records
  lived under `docs/r1/proposals/`. The runner refuses it unsigned, so this has no effect on a job.
