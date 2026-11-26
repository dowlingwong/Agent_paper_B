Reviewed base: origin/main `3024db3f8` (READY 82 at `7ab79a9d8` merged with 76a3c71f and 3024db3f); accepted at `4315ab29535c8844cae943fd1e17b738dc72b037`

# Independent review record — READY 82 (the P.4 phase-1 runner) on current main, updated for image v2.2 and R1-TRACKP-P4-RUNNER-DECISIONS

**Unit.** On `mac-trackp-p4-runner-20261122`, on top of READY 82's accepted `7ab79a9d8`: merges `4e26995a` (origin/main 76a3c71f) and `d7d5a32f` (origin/main 3024db3f, which carries the v2.2 report and review merged at ac981011 and the row R1-TRACKP-P4-RUNNER-DECISIONS); `9365c42a` (image v2.2: spec `image.digest` the GPU digest `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900…`, `image.row` R1-TRACKP-IMAGE-V22-B, `tag` and `build_record`; host config `trackp_htcondor_v2.json` GPU and CPU digests and tag of the one Actions run 45290856704; `p4_lib` refuses the v2 and v2.1 digests; `PLAN_ROWS` gains R1-TRACKP-P4-RUNNER-DECISIONS, R1-TRACKP-IMAGE-V22, R1-TRACKP-IMAGE-V22-B; `p4_switch` requires P5 to cite V21, V22 and V22-B as whole ids with the v2.2 records); `12fa43ee` (decision (1): `p4_phase1.check_env3_freeze` admits exactly `causal-conv1d==1.7.0` or `==1.7.0+LABEL` (PEP 440 local label, recorded in the job record and compared across jobs), every other line exact, direct references and the `causal_conv1d` spelling STOP; (2) tokenizers staged through the hub into `HF_HOME` (as built, now asserted); (3) `first_arm` must be `kev-0.8b`); `de6dd56d` (text reads as UTF-8 regardless of locale); `4315ab29` (review round 1 fixes: the note's `env3_freeze:` line names the admitted and STOP forms; the report discloses incidental terminal output from sealed-data files; `image.versions_sha256` procedure; `_read_record` seals a non-UTF-8 record as unreadable; `check_probe_hours` requires one `p4_estimate_hours: <arm> <hours>` line per spec arm in the probe record, equal to `estimate.hours`). `image.versions_sha256` stays `TODO_VERIFY_ON_HOST` (in no committed record; not derivable). The note draft stays unsigned. gate.py, gate_input_builder.py, release.py and the preregistration are unchanged. Authority: the user's message of 24 Nov 2026 (15:58), item 1.

**Full `r1/tests` suite** (`pytest -q -p no:cacheprovider -rfE r1/tests`, LightGBM off the path, fresh TMPDIR, sequential): base 3024db3f 58 failed / 3 errors / 3823 passed / 197 skipped; `de6dd56d` 58 / 3 / 3911; accepted tip `4315ab29` (rerun by the coordinating session after acceptance) 58 / 3 / 3912 / 197. `FULLSUITE_BASE_3024db3f.txt`, `FULLSUITE_P4_TIP.txt` and `FULLSUITE_P4_TIP_4315ab29.txt` byte-identical (61 entries): zero new failures.

**Process.** One independent reviewer, read-only, own detached worktrees, synthetic inputs only. Round 1 found the engineering sound but two text defects in the unit's own records (the note's `env3_freeze:` line still admitted wheels; the report claimed no sealed-data file had been read, contrary to the author's own account) and three minors; round 2 accepted.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `df616ec63` | NOT ACCEPTED (M1, M2; minors m1–m4) |
| 2 | `4315ab295` | ACCEPTED (minor m5) |

**Open items.** For the author, before signing the phase-1 note: (a) the incidental terminal output during authoring (report section "Incidental output from sealed-data files": two lines from `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json` showing a `delta_audit` field and its number; fifteen lines from `b2_audit_20261119/evaluation_block.jsonl` showing proposal ids, nodes and seeds, cut before `delta_evaluation`; three lines from `label_block.jsonl`, cut before any label value; nothing reused) — whether a record beyond the report is needed; (b) the env3 narrowing (direct references and the underscore spelling STOP) is ratified by signing the note's `env3_freeze:` line; (c) the CPU digest and tag in the host config were set with the GPU digest; (d) `first_arm` fixed to `kev-0.8b` (a P2 outcome without it STOPs). P5 still needs an independent review of the v2.2 run records (I2 759993, I3 759994, smoke 759997, E0 760000). Fields to fill: `image.versions_sha256` (HTCondor job with the staged-smoke header: `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt`, committed with the text), `paper.commit`, `host_config.sha256`, partition, receipt, freeze record path and sha256, `estimate.source`/`hours` (probe record lines). Nits not done: host config comment "I2/I3 redone on v2"; spec digest not cross-checked against host config `image.gpu`; host-side reads in `p4_switch`/`p4_render_jdl` not UTF-8-forced. m5: the commit body of `4315ab29` understates the incident; the report is complete.

## Round 1 (`df616ec63`)

> Reviewed base: df616ec63 (mac-trackp-p4-runner-20261122; READY 82 at 7ab79a9d8 merged with 76a3c71f and 3024db3f, updated for image v2.2)
>
> ## Summary
> The engineering is sound: both merges are faithful; all v2.2 values match the committed records; the env3 check, the P5 whole-id matching, the `first_arm` check, the HF_HOME staging and the UTF-8 handling work, and every launch placeholder is refused; the tests pass. Two text defects in the unit's own records block acceptance.
>
> ## What I checked
> **1. Merges.** `4e26995a` (parents `7ab79a9d8`, `76a3c71f`) and `d7d5a32f` (parents `9365c42a`, `3024db3f`) change no runner path relative to the branch parent and differ from the main parent only in runner paths. Tip vs `3024db3f`: 14 paths (runner files, host config, note draft, report, earlier review, two full-suite lists); everything else identical. The review record of `7ab79a9d8` unchanged.
>
> **2. v2.2 values.** GPU `49dd9900…5949`, CPU `a3b3a074…46b8`, tag `20261124-v2.2-667bb9c2`, Actions run 45290856704, build-log `fe872a3e…3312`, jobs 759993/759994/759997/760000 match the report and review in spec, host config and note; the refused v2.1 digest `31478d99…` matches `V21_IMAGE_006FC315.md`. The VERSIONS.txt sha256 is absent from every committed record (report, review, `09cb79e4`, `a20bd02e`, probe scripts; no raw outputs committed) and cannot be derived (`build_utc=$(date …)` at `667bb9c2`). `validate_spec(launch=True)` refuses `paper.commit`, `image.versions_sha256`, `host_config.sha256`, partition, receipt, freeze path, freeze sha and `estimate.source` in turn; a wrong value would STOP at the identity step. Who fills it is unspecified (m1).
>
> **3. env3 check.** Probes: v2.2 freeze reordered → `identical`, label null; `+cu124torch2.6` → `causal_conv1d_only`, label recorded; `1.7.1`, two causal lines, missing line, `einops` changed, `@ file://…1.7.0…whl`, `causal_conv1d==1.7.0`, BOM, a comment line, empty input → STOP; CRLF → `identical` (with a label `causal_conv1d_only`); blank lines and trailing spaces tolerated. The v2.2 build fails unless its sorted freeze equals the pin, so the actual image gives `identical`. The narrowing is the author's decision: the direct-reference STOP is well supported by (1) ("checked against 1.7.0"; a direct reference has no version field; the v2.2 review round 1 treated a direct-URL line as a defect), though the earlier admission was defensible; the underscore STOP does not follow from (1) (about the version, not the name), but changes nothing in practice (uv prints `causal-conv1d`). Both fail closed and do not affect v2.2.
>
> **4. (2) and (3).** `stage()` curls the weights, then `serialize.load_tokenizer` with `HF_HOME=<job>/hf` and the hub online; later steps offline (`offline_env`); tested. `validate_spec` requires `first_arm == kev-0.8b` and `kev-0.8b` in `arms`; a P2 outcome without it STOPs and returns to the author — the right fail-closed result.
>
> **5. P5 checks.** `_cites`: V22-B alone does not cite V22; `V22.`, `(V22)`, `` `V22` `` do; `V22B`, `XR1-…` do not. Non-row needles still substring-match. P6/P8 now whole ids (stricter, harmless). `check_binding` requires `R1-TRACKP-P4-RUNNER-DECISIONS` in `env3_freeze:`. The draft parses; tests cover each missing row.
>
> **6. UTF-8.** All job-side reads (`p4_lib.py`, `p4_phase1._rows`) use UTF-8; host-side reads in `p4_switch.py:184,210,211` and `p4_render_jdl.py:80,100,125` are not covered (nit, predates the unit). `errors="replace"` hides nothing that matters; pre-existing nit: `image_freeze_sha256` hashes decoded, newline-normalised text. The locale test is sound and ran without skipping.
>
> **7. Host config.** Binding GPU, CPU and tag from one Actions run is correct. Readers on main (`trackp.py`, `trackp_sft.json` comment, `test_trackp_sft.py:593`) do not read the changed fields; JDLs carry their own digests; `trackp.py --check-config` identical apart from the canonical sha; neither old sha is pinned elsewhere.
>
> **8. TODO fields.** All listed and refused at launch strength, except `estimate.hours` once `estimate.source` is filled (m3).
>
> **10. Full suite.** Lists identical (61: 58 FAILED, 3 ERROR), all outside the unit; 3911 − 3823 = 88 = the runner test file; `df616ec6` docs only.
>
> **11. Tests.** test_trackp_p4_runner 88; test_trackp_sft 35; test_trackp_sft_test_eval 48; test_trackp_p3 23.
>
> ## Findings
> **M1 — `TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md:66`.** The `env3_freeze:` line's first sentence still says "(a local label such as +cu12torch2.6… or a wheel of that version admitted)" while the appended text and `check_env3_freeze` STOP on any wheel reference; the test marks it signable and the report says it "states decision (1)". The author could sign a note authorising wheel references that the code refuses. Fix: delete "or a wheel of that version admitted", state the two STOP forms, test that the line does not contain "wheel".
>
> **M2 — `TRACKP_P4_RUNNER_20261122.md:268-269`.** "No label or evaluation file read" is contradicted by the author's own account of a broad `git grep` printing truncated lines from `b2_audit_20261119/label_block.jsonl` and `evaluation_block.jsonl`. No effect on the code (on the author's account, only proposal ids and seeds, no value; nothing in the diff depends on block content). The record is inaccurate on exactly what governance tracks, and the slip is undisclosed. Fix: a factual disclosure; the author decides whether a further record is needed. (I did not open either file; one `git grep -l` listed both names only.)
>
> **m1 — `p4_spec.json:13`.** Who fills `image.versions_sha256`, and how, is unspecified. Suggest the cluster runs `sha256sum /opt/r1/VERSIONS.txt` inside the digest-pinned image on NEMO2 and commits the VERSIONS.txt text with its sha (or commits the captures of 759994/759997/760000), then fills the spec in the launch commit.
> **m2 — `p4_lib.py:744-750`.** `_read_record` on a non-UTF-8 record now raises `Stop` (was None → sealed as unreadable), so `seal()` refuses; contradicts the docstrings (reproduced with `b'{"a": "\x97"}'`). Low risk. Fix: catch `Stop` and return None, or update the docstring.
> **m3 — `p4_lib.py:263-269`.** `estimate.hours` is listed TODO but not enforced once `estimate.source` is filled (conservative 8× case).
> **m4 — `p4_phase1.py:73-76, 88-99`.** Ratify the narrowing explicitly, especially the underscore spelling.
>
> **Nits.** Host config comment "I2/I3 redone on v2" (line 2); `image.tag`/`build_record` unchecked and the spec digest not cross-checked with host config `image.gpu` (pre-existing); `local_label` in `comparable()` redundant and untested; commit `9365c42a` says "on main 76a3c71f" with values from `ac981011` (explained); report lines 28-34, 142-143 describe the old admission without a superseded note.
>
> ## Housekeeping
> Worktrees removed; scratch in /tmp/p4u1rev/_to_delete/. Nothing committed or pushed; full suite not rerun.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`4315ab295`)

> Reviewed base: 4315ab295 (parent df616ec63; main 3024db3f)
>
> ## Summary
> All five round-1 findings are fixed and nothing new blocks. The disclosure copies no value. One fact goes back to the author.
>
> **Scope.** `git diff --stat df616ec63 4315ab295`: exactly the note draft, the report, `p4_lib.py`, `p4_spec.json`, `p4_switch.py` and the runner test (+147/−12). The merge and non-runner-path results of round 1 hold.
>
> **Tests.** test_trackp_p4_runner 89 passed, none skipped; test_trackp_sft 35; test_trackp_p3 23.
>
> ## Round-1 findings
> - **M1 fixed.** Note line 67 admits exactly `causal-conv1d==1.7.0` or `causal-conv1d==1.7.0+LABEL` (PEP 440 local label, recorded) and names the STOP forms (`@ file://…`/`@ https://…` even to 1.7.0, the `causal_conv1d` spelling, any other version or operator, a malformed label, a removed or added line, any other difference); no "wheel", no `<…>`; the note's STOP list (line 87) matches; the test checks the text and that the code refuses both forms. Signing ratifies the narrowing (settles m4).
> - **M2 fixed** (checked from the report and diff only; no data file opened). The section "Incidental output from sealed-data files" gives the exact command, the files and line counts, which fields were visible and where each line was cut, that nothing was reused or reopened, and an author question. No value is copied: no `delta_audit` number, seed list, `proposal_id` or node value in the report, note, tests or commit message; the only literal is `"label_kind": "audit"`, a record type.
> - **m1 fixed.** `image.versions_sha256_comment` and the report: `sha256sum && cat /opt/r1/VERSIONS.txt` in an HTCondor job with the staged-smoke header and the digest-pinned image; commit the text with its sha (or the 759994/759997/760000 captures); fill in the launch commit; not the I2 CPU-image value. Still refused at launch strength.
> - **m2 fixed.** `p4_lib.py:744-751` catches `Stop` and returns None; tested (sealed unreadable, unverified, walltime charged, bytes kept).
> - **m3 fixed.** `check_probe_hours` runs inside `check()` (so in `submit()`). Probes: correct lines pass; CRLF passes; `0.830` equals `0.83`; an out-of-spec arm is ignored; missing, duplicate (including one quoted in a code fence), indented, bullet, backticked, table-row, scientific-notation and unit-suffixed lines STOP. Fails closed.
>
> ## Judging the m3 format
> Reasonable and not scientific (ties the cap projection to a committed record; changes no protocol or scientific value). No test-plan conflict visible yet (`mac-trackp-p4-testplan-20261124` at `df616ec63` with no commits; no ref contains `p4_estimate_hours` outside this runner). The plan should emit one bare `p4_estimate_hours: <arm> <hours>` line per arm and say how hours derive from seconds per step.
>
> ## Nits not done
> Host-config comment and digest cross-check left undone, for acceptable reasons.
>
> ## New minor
> **m5.** The body of `4315ab295` says "ids/seeds, cut before values"; the report also discloses a `delta_audit` number shown from `b1_manifests.json`. The report is complete; not blocking.
>
> ## Points for the coordinator
> 1. The incident was wider than first reported: two lines from `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json` showed a `"delta_audit"` field and its number (an audit outcome value). The code does not depend on it; the report discloses it. Whether this, or the `evaluation_block` seed lists, needs a record beyond the report is the author's decision, to be answered before the note is signed.
> 2. In round 1 one of my `git grep -l` runs listed `b1_manifests.json` and both block files by name only; I opened none.
>
> ## Housekeeping
> Worktree removed; scratch in /tmp/p4u1rev/_to_delete/. Nothing committed or pushed; full suite not rerun.
>
> VERDICT: ACCEPTED

---

Code-Commit: 4315ab29535c8844cae943fd1e17b738dc72b037
Verdict: ACCEPTED

Accepted at `4315ab29`.
