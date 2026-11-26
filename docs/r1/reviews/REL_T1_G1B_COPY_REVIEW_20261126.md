# REL-T1-G1B seven-node copy — independent review

Date: 26 November 2026
Unit: commit `2a9a3800` on `compute-rel-t1-g1b-copy-20261126` (one commit over `origin/main` `54082a05`)
Task: `compute/20261126-05` (`tasks/compute/20261126-05-rel-t1-g1b-copy.md`)

## Independent reviewer statement

I am a fresh, AI-assisted review session. I did not write the unit, the copy step, the spec or the
sealed data. This review was read-only apart from writing this file. I did not modify the copies, the
copy record, the specs, the code, any pin, or any sealed source, and I did not commit or push.

## Inputs and their sha256

Branch tip: `2a9a3800` (`docs(r1): REL-T1-G1B seven-node copy of g1b-tasl-20261121-b (ENGINEERING_ONLY)`).
Base: `origin/main` `54082a05`.

Copy unit under review:

| File | sha256 |
|---|---|
| `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/summary.json` | `945abc0a7ced28a7ffa27905c3282b7ad4b25ed6f9c49de01ca7c595491e7a67` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/ASSEMBLY.json` | `e4056710beff92b4e0628372831632c9a54d070be1c41497e990eb45924236dd` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/runs.jsonl` | `1f56c0681d3a6cbd8005b3ee45da4ef2680d9354c869a0d16433b72afc971385` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/crosscheck_gate.json` | `00ee68c28aa2f9fcebd0b858d85df21a1baa3175b492eb5bfef0b074b073c8e2` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/COPY_RECORD.json` | `343a1004c68244fbaba6f98f582ace93adada13422a2f7fb200bf0ca2fa3dbb6` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/stdout.txt` | `37ccaf5220ab239b85a3b6ee9c092faed3eccd561507a57615f07b961aef25fb` |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/stderr.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty) |
| `docs/r1/reports/g5_rel_t1_g1b_20261126/STAGING.json` | `bdc5ae04b76f1332a11cecabd037bf3bb57f60f54492ae71cd63aad268d5e83f` |

The five copy hashes are exactly the values named in the task. `stdout.txt` is 3589 bytes and
`stderr.txt` is empty, consistent with rc 0.

Sealed sources read on TASL-2 (`ssh -o BatchMode=yes dowling@100.120.160.70`), read-only:

- staged (what the copy step read): `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/{summary.json,ASSEMBLY.json,runs.jsonl,crosscheck_gate.json}`
- original official joined dir (provenance): `/home/dowling/r1_tracks/t1_tasl/joined_seven_official_20261125/{summary.json,ASSEMBLY.json,runs.jsonl,crosscheck_gate.json}`

All four files hash to the four values above in both remote directories.

## Verification method and commands (read-only)

Run in this worktree; the only remote commands were `cat`/`ls`/`find` over SSH (no writes).

1. Recomputed hashes: `shasum -a 256 seven/{summary.json,ASSEMBLY.json,runs.jsonl,crosscheck_gate.json,COPY_RECORD.json} stdout.txt stderr.txt STAGING.json`.
2. Byte-identity to the sealed source and the original joined dir:
   `diff -q <branch file> <(ssh … cat /home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/<file>)`
   and the same against `/home/dowling/r1_tracks/t1_tasl/joined_seven_official_20261125/<file>`
   — all eight comparisons (4 files × 2 remote dirs) reported no difference.
3. Binding, from the files themselves in Python: summary `assembly_sha256` vs the sha256 of
   `ASSEMBLY.json`; `ASSEMBLY.json` `runs_sha256` vs the sha256 of `runs.jsonl`; gate
   `assembly_json_sha256` / `runs_jsonl_sha256` vs the same two; gate `schema`, `nodes`,
   `g1b_spec_sha256`, `crosscheck_run_id`; `COPY_RECORD.json` vs `stdout.txt` as JSON.
4. Seed hygiene: parsed every line of `runs.jsonl`, collected every key named `seed` or ending
   `_seed` and every numeric value of any key, and checked for 7001–7010 (the `g5_noise.AUDIT_SEEDS`
   range); also a raw `grep -oE '(^|[^0-9])(700[1-9]|7010)([^0-9]|$)'`. Recursively scanned the summary
   for `label`/`eval`/`test` keys with non-empty values.
5. Staging: compared the staged dir's four hashes and file list (4 files, no symlinks, mtimes
   preserved to 25 Nov 03:01) and checked `STAGING.json`'s provenance hashes against the committed
   records on `origin/main`.
6. Scope: `git diff --stat origin/main`, `git diff --name-status origin/main...HEAD`,
   `git show 2a9a3800 --stat`, `git status --porcelain=v1`.
7. Documentation: read `sweep2/t1_tasl/g5_relcopy.py` (docstring plus `check_source`/`_write_copies`),
   `sweep2/t1_tasl/g5_tasl.py` (`rel-copy` dispatch at 2882–2901, `check_g1b_copy` at 1552), and
   §3 of the G.5 draft revision 13, `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md`
   (section starts at line 877; the sealed-root sentence is at line 955).

## Findings

**No BLOCKING, no MAJOR.**

The five copy files exist with exactly the required sha256. Each is byte-identical to the staged
sealed source and to the original official joined directory on TASL-2, so the staging added no
change to any sealed attempt. The hash chain holds end to end: summary → `ASSEMBLY.json` →
`runs.jsonl`, and the gate binds the same `ASSEMBLY.json` and `runs.jsonl` with the cross-check
spec's nodes/run and the G.1b spec sha256. `COPY_RECORD.json` has schema `g5_rel_t1_g1b_copy/1`,
label `ENGINEERING_ONLY`, run `g1b-tasl-20261121-b`, exactly the seven nodes, the sealed paths and
all four copy paths/sha256, plus the `spec_fields` and `review_must_name` lines. No record in
`runs.jsonl` carries an audit seed (7001–7010); all seed values are 1001–1030, 2001–2030,
3001–3030, or absent, and no label or evaluation value appears in the summary, assembly or runs.
The branch diff adds only the eight files of this unit (no code, spec, pin or other report change).
The staging is the procedure documented in draft §3, its bytes are exact, and it added one new
directory of four files under `sealed_g1b` without touching any sealed attempt directory.

MINOR notes (informational; none requires a change):

- **m1 — staging wording.** `STAGING.json`'s `what` says the joined, gated "run directory" is
  written under `sealed_g1b`, while the command and `files` map show only the four copy-step inputs
  were staged; the original dir's `edits.json` and `floor_by_node.json` were not staged. This is
  transparent and sufficient for the copy step, but "run directory" is slightly broader than what
  was copied.
- **m2 — stdout is JSON-equal, not byte-equal, to `COPY_RECORD.json`.** Both parse to the same
  object (same keys, same values), but the CLI prints the in-memory record in insertion order while
  `COPY_RECORD.json` is written with `sort_keys=True`, so `cmp` reports a difference from byte 5.
  The task's "stdout matches `COPY_RECORD`" holds; a later byte comparison should not be read as a
  mismatch.
- **m3 — no literal `labels_read: none` field.** That marker is defined for authorization records
  (`g1b_tasl_authorization.template.md`; the `want` maps in `g1b_tasl.py`/`g1b_crosscheck.py`), not
  for the `g5_rel_t1_g1b_copy/1` record or the G.1b summary. The copies correctly carry
  `label: ENGINEERING_ONLY`, and a recursive scan found no label, test or evaluation field with a
  value. The labels-not-read property is therefore established, but not by a literal `labels_read`
  key inside the five copy files.
- **m4 — task-text staleness.** The task text names main `95249de3`; the published `origin/main`
  used here is `54082a05`. This is task-text drift, not a unit defect: the staged files match the
  committed records on `origin/main` (`summary.json`, `ASSEMBLY.json`, `crosscheck_gate.json`) and
  the four hashes match the values the task itself requires.

## Required naming paragraph

The seven-node summary copy is `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/summary.json`, sha256
`945abc0a7ced28a7ffa27905c3282b7ad4b25ed6f9c49de01ca7c595491e7a67`, taken byte-identically from
the sealed source `/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/summary.json`
(itself byte-identical to the official joined directory
`/home/dowling/r1_tracks/t1_tasl/joined_seven_official_20261125/summary.json`). Beside it are the
`ASSEMBLY.json` copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/ASSEMBLY.json` (sha256
`e4056710beff92b4e0628372831632c9a54d070be1c41497e990eb45924236dd`, from
`/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/ASSEMBLY.json`), the
`runs.jsonl` copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/runs.jsonl` (sha256
`1f56c0681d3a6cbd8005b3ee45da4ef2680d9354c869a0d16433b72afc971385`, from
`/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/runs.jsonl`), and the
cross-check gate copy `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/crosscheck_gate.json`, sha256
`00ee68c28aa2f9fcebd0b858d85df21a1baa3175b492eb5bfef0b074b073c8e2`, from
`/home/dowling/r1_tracks/t1_tasl/sealed_g1b/joined_seven_official_20261125/crosscheck_gate.json`.
The gate copy names exactly the three TASL-7 nodes `mlab_cifar10`, `mlgym_cifar10` and
`mlgym_breakout_minatar` for cross-check run `g1b-tasl-20261121-b-xc2` and G.1b spec sha256
`7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7` (the spec the copy step checked:
`sweep2/t1_tasl/g1b_tasl_spec.json`, bound by `sweep2/t1_tasl/g5_tasl_spec.json` and the cross-check
spec `sweep2/t1_tasl/g1b_crosscheck_spec.json`, sha256
`a9e6b4633a8cbe3f8356aab748ac61b09f410475b33b0c6191826adfd926d164`). The summary/`ASSEMBLY.json`/
`runs.jsonl` binding holds: the summary's `assembly_sha256` is the `ASSEMBLY.json` sha256
`e4056710…`, that file's `runs_sha256` is the `runs.jsonl` sha256 `1f56c068…`, and the gate's
`assembly_json_sha256` and `runs_jsonl_sha256` are those same two values. The copy record is
`docs/r1/reports/g5_rel_t1_g1b_20261126/seven/COPY_RECORD.json`, sha256
`343a1004c68244fbaba6f98f582ace93adada13422a2f7fb200bf0ca2fa3dbb6`.

I changed nothing except writing this review file.

Verdict: ACCEPTED
