# G.5 P11 refusal captures — independent review, 28 November 2026

- Date: 2026-11-28 (Europe/Berlin). Fresh, AI-assisted independent reviewer. I did not write the deliverable, the
  record section or the captures. This review was read-only apart from writing this file on the review branch; I did
  not amend, force-push, modify the deliverable branch, or take any host action.
- Deliverable: branch `compute-g5-p11-refusals-20261128` @
  `6dbf21b23ed7f211078486facefd9b73972f131c`, one commit on top of `origin/main`
  `a98d2eff1d2847e34f00effe66b53bc00467e936` (no force push).
- Task: `compute/20261127-32` (G.5 P11 host tests), disposition `compute/20261128-05` item 1.
- Review base: this file is committed on a new branch
  `compute-g5-p11-refusals-20261128-review`, created from the deliverable tip `6dbf21b2`; the deliverable branch is
  untouched.

Verdict: ACCEPTED

## Inputs and hashes checked

| File at `6dbf21b2` | sha256 |
|---|---|
| `docs/r1/reports/g5_code_20261123/G5_P11_HOST_TEST_RECORD_20261127.md` | `fc34c40b4b9ff0b93fc94716db9b944bea263fc80bbd091c4193929707201b8a` |
| `sweep2/t1_tasl/g5_tasl.py` | `800575983aa4cd0141244b719a2a71243cd8318eb8db67835475b97ac395ac51` |
| `P11_REFUSALS_20261128/SHA256SUMS` | `1dc5fe1f9af4340b9573a29ab23cbe04b8ee9f704472ca6eef66da366c42e891` |
| `P11_REFUSALS_20261128/seal-attempt.txt` | `da67898d8512b1ca665d3c89b12de51e42217ab82f332fc0552657e400f122a1` |
| `P11_REFUSALS_20261128/seal-node.txt` | `cd7eebea76c863fa81b9e26a5ac6ce2db2002b8f2cd700ae52a794b223b7e4c1` |
| `P11_REFUSALS_20261128/seal-run.txt` | `311a396d562b17dff5f36434bcedf6ad30fc9e41fa35f16e13b69f7f8d85498f` |
| `P11_REFUSALS_20261128/seal-server.txt` | `25a46476e146f9e0f50de0eb27077ed9ec31a48fbc65b904959a707175a8b06d` |
| `P11_REFUSALS_20261128/close-server.txt` | `0f6e41059aa02138c99ea737031032ace8a85ba39e5c21ef0a2880c31933f207` |
| `P11_REFUSALS_20261128/server-span.txt` | `29fc3e39988b7fb6d90ad80b4736f364fcbfa05c630bd4f6b34f5f8ab55c7d85` |
| `P11_REFUSALS_20261128/validate_launch.txt` | `f5284404d10fa0687e7226549073dbe036c6553ac17aedf8ac2059a00c9d96d5` |

`g5_tasl.py` is unchanged between `origin/main` and the deliverable tip (`git diff --stat origin/main...HEAD --
sweep2/t1_tasl/g5_tasl.py` is empty), so the gate examined below is the code the record names.

## Method

1. Branch scope: `git rev-list --parents`, `git diff --name-status`, `git diff --numstat`, and
   `git diff --unified=0 origin/main...HEAD` for the record.
2. Hashes: `shasum -a 256 -c SHA256SUMS` in the capture directory; file list compared with the directory listing;
   each capture re-hashed from the committed tree.
3. Captures: read all seven files and compared their command label, refusal text and `rc` with the appended table.
4. Code path: read `validate_spec` (lines 973–1059) and `part_3b2` (lines 3017–3045) in `sweep2/t1_tasl/g5_tasl.py`;
   checked the dispatch order up to the first `SE.*` call.
5. Independent reproduction: ran each of the seven named commands at the deliverable tip against
   `sweep2/t1_tasl/g5_tasl_spec.json` with a fresh nonexistent base path, recording stdout/stderr and `rc`; repeated
   the run under a Python audit hook that logged every `open`/`os.open` containing the marker path.
6. Statuses: read the whole record at the tip and the append-only diff, and checked the C2/C4/C5/C9/C14/C16 rows and
   the note-gated wording.

## Findings

**No BLOCKING, no MAJOR. Two MINOR observations, neither blocking.**

1. **Scope is append-only — PASS.** The commit has one parent, `a98d2eff`. The only modified file is the P11 record,
   and `git diff --unified=0` shows a single hunk, `@@ -65,0 +66,32 @@`, i.e. 32 added lines and 0 removed lines at
   the end of the file. The other eight paths are new files under `P11_REFUSALS_20261128/` (seven captures plus
   `SHA256SUMS`). `git diff --numstat` is `32/0` for the record and `3/0` for each capture (`7/0` for `SHA256SUMS`).
   No earlier text, status or reading in the record was changed.

2. **`SHA256SUMS` verifies for every listed file — PASS.** `shasum -a 256 -c SHA256SUMS` reports `OK` for all seven
   entries and exits 0. The directory contains exactly those seven files plus `SHA256SUMS`; no listed file is missing
   and no unlisted capture is present. The hashes above recompute from the committed blobs at `6dbf21b2`.

3. **Every capture shows the exact refusal and `rc=2`, and matches the table — PASS.** Each file has the same three
   lines: a command label (`=== seal-attempt ===`, etc.), `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`, and
   `rc=2`. The appended table's six item rows and the extra `validate … --launch` control row carry exactly that
   text and `rc` 2. I re-ran the named commands at the tip with a fresh nonexistent base
   (`…/p11ref_repro_nonexistent_*`) and got the same text and `rc=2` for `seal-attempt`, `seal-node`,
   `seal-run`, `seal-server`, `close-server` and `server-span`, and for the `validate --launch` control. The
   `close-server` reproduction included its required `--reason` argument; with valid arguments the result is the
   `STOP`, not an argparse error. No command in the table is invented and no result is substituted.

4. **The refusal precedes every attempt/server path — PASS, with a wording caveat.** In `part_3b2`
   (`sweep2/t1_tasl/g5_tasl.py:3017–3038`) the order is: lazy imports, `check_import_sources()`, `load_spec(spec_path)`,
   `validate_spec(spec, launch=True)`, and only then the `SE.seal_attempt` / `SE.seal_node` / `SE.seal_run` /
   `SE.seal_server` / `SE.close_server` / `SE.register_server_span` calls. `validate_spec` tests the schema/label and
   then the `run_id` at lines 982–984; the committed spec's `run_id` is
   `PENDING: c3_t1_labels_YYYYMMDD (the signed note's date)`, so `RUN_ID.fullmatch` fails and `Stop` is raised before
   any of those `SE.*` calls. `load_spec` (`g5_tasl.py:263–273`) reads only the spec path (it does not read a note or
   an attempt/server directory when `note_path` is `None` and the spec has no `_addendum`; the committed spec has
   none). Among repo-local paths, the audit-hook run observed only `g5_tasl_spec.json` and the local `__pycache__`
   modules, and **zero** accesses containing the nonexistent marker path. This supports both claims in the record: the nonexistent
   attempt/server/receipt paths were never touched, and no smoke attempt, sealed file, label or evaluation value was
   created or read.
   - **MINOR-1 (wording).** The record says each command "refuses **before** reading or writing any path". Literally,
     the command does read the committed spec (`load_spec`, line 3024) and imports module files before the refusal.
     The parenthetical "(the nonexistent paths were never touched)" and the substantive claim are correct; a future
     edit should say "before reading or writing any of the item paths" to avoid the absolute wording. This does not
     affect the evidence or the statuses.

5. **No PASS is claimed for the gate-blocked items — PASS.** The append adds no status upgrade. C2, C4, C5 and C16
   remain `NOT COVERED`; C9 and C14 remain `PARTIAL`; C6 and C15 remain `PARTIAL`; the earlier C7/C11/C10 text is
   unchanged. The new section explicitly says C2, C4, C5, C9, C14 and C16 are "still gate-blocked, so not run" and
   leaves C10's hours-long span and the audit-chunk side of C11 for the table (STOP 12). The seal/server commands are
   recorded as "checked at publication", with the exact refusal, not as PASS. The earlier TASL-7 evidence is described
   as unchanged and still standing for C7 and the server side of C11, consistent with the original `PARTIAL`/PASS
   wording.

6. **STOP/over-claim check — PASS.** The record's `STOP: run_id must be c3_t1_labels_<YYYYMMDD>` matches the code,
   the captures and the reproduction; `rc=2` matches `main`'s `except Stop` return. The `validate … --launch` row is
   explicitly labelled "control only, not a host test", so it is not used as a substitute for the six item commands
   and does not contradict the disposition. No other STOP or unsupported PASS claim was found.
   - **MINOR-2 (evidence scope).** The capture files contain only the command label, refusal and `rc`; they do not
     record the full argv, spec path, host, timestamp or shell transcript, so on their own they do not bind the
     refusal to the exact table invocation or to the stated TASL-2 checkout
     (`paperB_cpuset_20261128T001400Z`). My re-run at the tip closes the command-behaviour gap; the host/checkout
     sentence remains a host-side claim not independently verifiable from this branch. This is a limitation of the
     capture format, not an incorrect result, and is not blocking.

## Reading

The deliverable does what disposition `compute/20261128-05` item 1 asks: it appends the re-check to the accepted
record, captures one refusal per item command with `rc=2`, and leaves the note-dependent items as "checked at
publication" rather than claiming PASS. The code path confirms the refusal is the `run_id` gate before any item path
is used, and the hashes and statuses are consistent. The two MINOR observations are wording/evidence-scope points;
neither changes a status or an item's disposition. **ACCEPTED.**
