Reviewed base: origin/main `3024db3f8`; accepted at `214fbf1de`

# Independent review record — the draft sweep-1 label freeze record `C3_SWEEP1_LABEL_FREEZE_20261124.md` (approved: false) for the P.4 phase-1 signature

**Unit.** On `mac-sweep1-freeze-record-20261124` (on origin/main `3024db3f8`): `docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md` (`approved: false`; the author signs it), in the format the P.4 runner checks (`p4_lib.validate_spec` path regex, `p4_lib.inputs` exact `^approved: true$` line and the full label-block hash, the pinned sha256 in the clone at `paper.commit`, `refuse_evaluation_path`/`refuse_sealed` on `--label-freeze`, `p4_switch.check_binding` of the note's `label_freeze:` line). It binds the sweep-1 B.2 audit `b2-ab79b4ce-20261119T002306Z` (label block `cdae9c3f…`, evaluation block `297fed47…`, `evidence_completion.json` `e28bee5e…`, `PASS.json`, `SHA256SUMS`, `OUTPUT_SHA256SUMS`, seed-journal manifest, report and review), the train/dev release receipt `f06e37a9…` and partition `6a6327a3…` (`reports/release_20261122/`), and the final verification step (the release step's `release_checks.sweep1_integrity`, `audit.verify_evidence_completion` with the sweep-1 compat replay builder inferred from the `release_checks_sha256` pin, PASS at 2026-11-23T09:23:16Z on deepthought, main `3522e59b`, release code `a9d8ff5e`); `audit_seal_sha256: not_applicable` (sweep 1 has no `AUDIT_SEAL.json`); errata E1–E4 carried over from the unmerged 20 Nov draft (`mac-sweep1-label-freeze-20261121` @ `dde24f6f`), which this record replaces; signing and post-signing binding rules (§8). Report `docs/r1/reports/trackp_p4_20261122/SWEEP1_LABEL_FREEZE_DRAFT_20261124.md`, with a proposed PLAN row R1-C3-SWEEP1-LABELS-FROZEN in R1-SWEEP2-LABELS-FREEZE's form. Authority: the user's message of 24 Nov 2026 (15:58), item 2.

**Process.** One independent reviewer, read-only, own detached worktrees of the unit and of the runner branch at each runner commit (`7ab79a9d8`, `d7d5a32f3`, `12fa43ee2`, `de6dd56d6`), synthetic partition and receipt, no label or evaluation contents opened, no hash computed from sealed data. Round 1 found one major (the record's signing instructions contradicted an unresolved `TODO_VERIFY_ON_HOST` field) and seven minors; round 2 found one major (three bound hashes cited only from an unpushed commit) and two minors; round 3 accepted with no findings.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `3a23679ec` | NOT ACCEPTED (M1; minors m1–m7) |
| 2 | `b24eb2c96` | NOT ACCEPTED (M1; minors m1–m2) |
| 3 | `214fbf1de` | ACCEPTED |

**Open items.** For the author: sign only this record (it replaces `dde24f6f`); the signature changes the heading, the Status paragraph and the four key lines (`approved`, `signed_by`, `signed_utc`, `author_instruction`) and nothing else, and no field may hold `TODO_VERIFY_ON_HOST` or PENDING other than the three signature fields; signing adopts the "other users' load" co-tenancy reading (E2, five of seven samples below 10 idle cores) and the §8.5 procedural rule (a later erratum or withdrawal does not stop a job, which reads the record at `paper.commit`; the coordinating chat reports it to the author before any further P.4 submission). After signing: the record's sha256 is taken at the signing commit (or `paper.commit` if unchanged) and goes into `p4_spec.json` `labels.freeze_record.sha256` and the note's `label_freeze:` line; `paper.commit` must be at or after the signing commit. The proposed PLAN row R1-C3-SWEEP1-LABELS-FROZEN is for the author. Three bound hashes (`d62d09f1…`, `1c1a95a0…`, `af13b0f4…`) are sha256s of committed non-sealed files reproducible with `git show 3024db3f:<path> | sha256sum`, not copied from a record. Style: lines 239, 247–248 long; "T0 test release row" vs the row's "after the arms-frozen record".

## Round 1 (`3a23679ec`)

> Reviewed base: 3a23679ec (mac-sweep1-freeze-record-20261124; one commit on 3024db3f8)
>
> ## Summary
> Not accepted, because of one blocking problem (M1): the record's own signing instructions contradict its unresolved TODO field. The format, the bound values and the choice of final verification are all correct. The runner's checks were reproduced at three runner commits.
>
> ## What I verified
> **1. Format: PASS.** My own script (`p4_lib.validate_spec(launch=True)`, `sft_data.refuse_evaluation_path`, `analysis_guard.refuse_sealed`, `p4_lib.inputs`, `p4_switch.parse_note`, `check_binding`; synthetic partition and receipt) at runner commits `7ab79a9d8`, `d7d5a32f3` and `12fa43ee2`, identical results: the draft as committed passes the spec check, path guards and binding, and `inputs` STOPs only with "not a signed freeze of the block cdae9c3f…"; a copy with only line 15 changed to `approved: true` passes; a full simulated signature passes; a flipped copy without the block hash STOPs; `approved: true ` with a trailing space STOPs; a wrong sha256 on the note's `label_freeze:` line STOPs in `check_binding`. The record checks are the same in all three commits (path regex, `^approved: true$` with `re.M`, `SOURCE_BLOCK_SHA256` anywhere, sha256 in the clone, `check_binding` needles); only line numbers moved. No accidental "signed" match: only line 15 begins with `approved:`; other mentions are mid-line (lines 1, 6, 205) or backticked (4, 206). Runner tests: 78 passed at `d7d5a32f3`, 87 at `12fa43ee2`.
>
> **2. Bound values: all correct.** Every 40/64-hex string occurs in committed files on `3024db3f` (unchanged since `76a3c71f`): `SHA256SUMS` lines 3, 10, 11, 13, 14; `PASS.json`; `evidence_completion.json`; `START.json` pin `ab79b4ce…`; seed-journal manifest `85d9b6b2…` (466 files); receipt `git show | sha256sum` = `f06e37a9…` with `inputs.label_block_sha256` `cdae9c3f…`, `outputs` `6a6327a3…`, `utc` 2026-11-23T09:23:16Z, `head`/`published` `3522e59b`, `release_commit` `a9d8ff5e`, `integrity.completion_sha256` `e28bee5e…`; `release_checks.py` at `3522e59b` = `c97b60e9…`; release report lines; both reviews ACCEPTED; merges `dc3b4284`, `a454d6db`. No label or evaluation block opened; no hash computed from sealed data.
>
> **3. Final verification: correctly identified.** `sweep1_integrity` at `3522e59b` runs `verify_evidence_completion(..., replay_builder=sweep1_compat.rebuild_v2_table)` inside `integrity_context` after the `_sweep1_compat_published` guard; the 22 Nov call at `6f713ede`/`b2b7489a` predates the guard (its own report, lines 56–63). "No fresh run before the T0 test row" is right (`require_integrity_or_test_release("T0")`; `R1-S2-LABELS-TEST-RELEASE` not in PLAN; the prereg's §6 carve-out). Nuance: the pinned code at `ab79b4ce` has no such gate, so that path is blocked by policy, not code.
>
> **4. Model fidelity: good.** Every R1-SWEEP2-LABELS-FREEZE item mapped; no sweep-2 freeze record file exists. `AUDIT_SEAL.json` looks sweep-2 only (no code at `ab79b4ce` or main writes it; `pins.json` `retained` and `REPORT.md` §8 list the attempt directory without it); very likely but not proven by a committed record.
>
> **5. The earlier draft.** `dde24f6f` would fail the runner (path under `proposals/` fails the regex; `frozen: true` and no `approved:` line, `inputs` STOPs; its fresh-clone verification is barred by PRE-STAGE A). Report §4.5 tells the author to sign only one.
>
> **6–7. Scope, co-tenancy, binding.** The 5-of-7 count is correct (9.55, 7.54, 9.40, 9.40, 9.29); the review's 4 is a miscount. The other-users reading is within the earlier draft's ruling R1. Who flips the key, the spec and note updates, and `paper.commit` containing the file are correct; no `.gitattributes`.
>
> ## Findings
> **M1 — record lines 6–7, 21, 66, 85, 203–207 (report §4.1 vs §5.1).** Line 6 and §8 step 2 say only the heading, Status paragraph, `approved`, `signed_by`, `signed_utc` and `author_instruction` change at signature and "every other byte stays as reviewed", but §8 step 1 has the author resolve `audit_seal_sha256: TODO_VERIFY_ON_HOST` (three lines). Line 6 also omits the `approved` line (line 15 is not marked "at signature"). Following §8.2 literally publishes a signed record with the TODO, which the runner accepts; resolving it while signing signs unreviewed bytes. Fix: fill the field now as "none" with the committed evidence, or add a revise → confirmation review → sign step and refuse to sign while any `TODO_VERIFY_ON_HOST` remains; list `approved` in line 6.
>
> **m1 — line 211, report §5.4.** "Any later edit STOPs the job" is wrong: the job checks the record in its clone at `paper.commit`, and `verify_launch_p4` leaves `docs/` out; a later erratum or withdrawal does not stop it. §8.3 should take the sha256 at `paper.commit` (or the signing commit), not `origin/main`.
> **m2 — report §1, §3.** Runner "now at `4e26995a2`, files byte-identical" is out of date (`d7d5a32f3`, `12fa43ee2` changed `p4_lib.py`, `p4_switch.py`, `p4_spec.json` and the test; record checks unchanged, line numbers off); "the runner test could not run" is untrue with `AR_HARNESS_ROOT` set.
> **m3 — §5 E4 (line 170).** "The audit read none" reintroduces an ambiguity the earlier review's N4 removed; say "no pre-existing label table was read".
> **m4 — material from `dde24f6f` dropped.** E2's estimate basis (exactly 16 added load; parent and probe processes ignored; only 7 operator samples since `resource_monitor` did not sample CPU), required by that review's B1 fix; the seed-role STOP and R1-BX-D3 gate-stability note; the `.gitignore` force-add tracking note; the review sha256 `d62d09f1…` and `SHA256SUMS`/`OUTPUT_SHA256SUMS` sha256s `1c1a95a0…`/`af13b0f4…`; the proposed PLAN row citing the signed file; §8 step 1 does not say D1-B is no longer offered.
> **m5.** The record does not itself say it replaces the 20 Nov draft; signing `dde24f6f` on 2026-11-24 would collide with this file name.
> **m6 — line 31, §4.** The replay builder is stated as recorded fact; the receipt records only `audit.verify_evidence_completion`; the builder is inferred from the `release_checks_sha256` pin (release review §2, M2). Cite that.
> **m7 — §2 line 93.** The manifest is at `pins.json` `output.seed_journals.manifest_sha256`.
>
> **Note for the runner author:** `inputs()` reads the record with `read_text()` and no encoding; under a forced ASCII locale the signed record's UTF-8 dashes raise `UnicodeDecodeError` instead of a STOP (reproduced).
>
> ## Cleanup
> Four worktrees removed; scratch in `/tmp/frzrev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`b24eb2c96`)

> Reviewed base: b24eb2c96 (on 3a23679ec; main 3024db3f8; runner tip 12fa43ee2)
>
> ## Summary
> Not accepted, for one small reason: the record names an unpushed commit as the only source of three bound hashes. Everything else from round 1 is fixed, and the format still passes the runner.
>
> ## What I verified
> **Runner format check at `12fa43ee2`** (own script, synthetic partition and receipt): the draft as committed passes the spec check, path guards and `parse_note`/`check_binding`, and `inputs` STOPs only on "not a signed freeze"; a copy with only line 20 flipped passes; a full simulated signature passes; a flipped copy without the block hash STOPs; a trailing space after `true` STOPs; a wrong freeze sha256 on the note STOPs in `check_binding`. The `replaces:` key and `not_applicable` value break nothing; only line 20 starts with `approved:` (lines 1, 4, 6, 7, 238 mid-line). No `TODO_VERIFY_ON_HOST` field left; PENDING only in the three signature fields (line 236 is prose). `test_trackp_p4_runner.py`: 87 passed. Report line numbers at `12fa43ee2` correct.
>
> **Round-1 fixes:** M1 (`not_applicable` with evidence: `git grep AUDIT_SEAL` outside `docs/` and `papers/` finds nothing at `ab79b4ce` or main; §8.2; `approved` listed); m1 (§8.4 sha256 at the signing commit or `paper.commit`); m3, m6, m7 fixed; m4 (E2 basis, rule 3 with the R1-BX-D3 note, rule 4's `.gitignore` note: line 49 is `*.jsonl`, both blocks tracked on main); m5 fixed.
>
> **The three restored hashes are fine as values**: `d62d09f1…`, `1c1a95a0…`, `af13b0f4…` are the sha256 of `docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md`, `docs/r1/reports/b2_audit_20261119/SHA256SUMS` and `.../OUTPUT_SHA256SUMS`, all committed and not sealed. `git show <c>:<path> | sha256sum` gives the bound value at `94db94bb`, `dc3b4284` and `origin/main`; blob ids identical at `94db94bb` and main (`902a8fd4…`, `e0d47c2c…`, `4a71ff9d…`).
>
> ## Findings
> **M1 — record §2 rows at lines 95 and 106 (and line 16).** The only cited source for three hashes is `dde24f6f` plus "unchanged since `94db94bb`", with no reproducible command; `git branch -r --contains dde24f6f` returns nothing (local only). Once signed on main, a GitHub reader cannot check them. Fix: cite `git show 3024db3f:<path> | sha256sum`, blob unchanged since `94db94bb`; keep `dde24f6f` as corroboration noted as unpushed; adjust line 16.
>
> **m1 — record §8.5 (lines 245–250).** The erratum rule reads as settled procedure; only the report says it is not enforced; unclear whether signing adopts it. Fix: "(procedural; not enforced by the runner)" and name the coordinating chat.
>
> **m2 — report §5, proposed R1-C3-SWEEP1-LABELS-FROZEN.** Shorter than R1-SWEEP2-LABELS-FREEZE: omits the "sealed at" path, the report and review, "attempt `b2-435513d2-20261118T012807Z` is not a label source", and the closing clause on what stays sealed until the test release row. Not blocking.
>
> ## Cleanup
> Worktrees removed; scratch in `/tmp/frzrev/_to_delete/round2/`. Nothing committed or pushed.
>
> VERDICT: NOT ACCEPTED

## Round 3 (`214fbf1de`)

> Reviewed base: 214fbf1de (on b24eb2c96; main 3024db3f8; runner tip de6dd56d6)
>
> ## Summary
> Accepted. Both round-2 findings and the PLAN-row point are fixed, and the author's naming correction checks out. At runner tip `de6dd56d6` the unsigned draft fails only on the signature, and the copy with the key flipped passes.
>
> ## Format check at `de6dd56d6`
> Own script, synthetic partition and receipt. Draft as committed (sha256 `a6789f4f…`): spec check, path guards and `parse_note`/`check_binding` pass; `inputs` STOPs only with "not a signed freeze of the block cdae9c3f…". Copy with only line 21 flipped: PASS. Full simulated signature: PASS. Negative cases: no block hash STOPs; trailing space STOPs; wrong freeze sha256 on the note STOPs in `check_binding`. Only line 21 starts with `approved:`. No `TODO_VERIFY_ON_HOST` field; PENDING only in the three signature fields. The runner changed only how the record is read (`_read_utf8(fpath, ProtocolStop)`); the regex, the key check, the block hash and the needles are unchanged. The round-1 UTF-8 note is resolved: under `LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0` the draft STOPs on the signature and the flipped copy passes. `test_trackp_p4_runner.py`: 88 passed.
>
> ## The round-2 findings
> - **M1 fixed.** Record §2 cites `git show 3024db3f:<path> | sha256sum` for the three hashes; reproduced `1c1a95a0…`, `af13b0f4…`, `d62d09f1…`; blob ids `902a8fd4`, `e0d47c2c`, `4a71ff9d` identical at `94db94bb` and `3024db3f`; all committed, none sealed; `dde24f6f` kept as corroboration, marked unpushed; the preamble states the exception; every other hash still found on main.
> - **m1 fixed.** "(procedural; not enforced by the runner; signing adopts this rule)", naming the coordinating chat.
> - **m2 fixed.** R1-C3-SWEEP1-LABELS-FROZEN now has R1-SWEEP2-LABELS-FREEZE's form (audit, output and retained path; completion, label and evaluation hashes; report and review; "the author's label-table freeze" citing the signed file; the attempt that is not a label source; sealed except as released by R1-S2-LABELS-TRAINDEV-RELEASE and, after the arms-frozen record, R1-S2-LABELS-TEST-RELEASE), plus the final verification and the flatten non-claim.
> - **Naming correction verified.** `b2-435513d2-20261118T012807Z` never appears alone on main; the directory `/ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse` is named in `REPORT.md` line 18, `pins.json` `preserved_stop_dir.path` and `PREFLIGHT_435513D2_STOP.md`.
>
> ## Findings
> No major and no minor findings. Style only: record lines 239 and 247–248 run past the usual width; the record body says "a T0 test release row" while the PLAN row adds "after the arms-frozen record" (consistent; could share wording).
>
> ## Cleanup
> Worktrees removed; scratch in `/tmp/frzrev/_to_delete/round3/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

---

Code-Commit: 214fbf1de
Verdict: ACCEPTED

Accepted at `214fbf1de`.
