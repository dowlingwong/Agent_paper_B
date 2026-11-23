# T1 release rows: drafts bound to the G.5 code (23 Nov 2026)

ENGINEERING_ONLY report. AI-assisted (Mac-desk agent, Claude). Branch `mac-t1-release-rows-20261123`, from
`mac-g5-code-main-20261123` @ `30e2d51a`.
- Unit: `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md` (`approved: false`), which drafts R1-T1-LABELS-UNSEAL
  and R1-T1-LABELS-TEST-RELEASE.
- Docs only: no code changed. Nothing ran on a host. No label, evaluation value, sealed file or receipt partition was
  read.
- Authority checked against `origin/main` `89899f76`.

## 1. Mapping to the code

| Requirement | Code | How the draft meets it |
|---|---|---|
| Exact row text | `r1/c3/release.py` `row_pattern("T1", stage)` (fullmatch on the decision cell), `row_text` | Each draft text is the `row_text` sentence. The cell holds nothing else (§1 of the draft). |
| Row ids | `release.ROWS[("T1","traindev")]`, `[("T1","test")]`; `g5_seal.UNSEAL_ROW`, `TEST_ROW` | `R1-T1-LABELS-UNSEAL`, `R1-T1-LABELS-TEST-RELEASE`, as the G.5 note's `release_rows` line names them |
| Place on PLAN | `release.author_rows` (dated author heading in §10, header `ID \| Decision`), exactly once | Stated (draft §1); checked with a synthetic table (§2 below) |
| Bindings | `release_row`: prereg = frozen file's sha256; split = `P3_SPLIT_SHA256`; commit a published ancestor whose `release.py` the writer runs; T1 train/dev: each G.1b summary committed with its sha256, no node twice; test: arms-frozen record committed with its sha256 | prereg `aa1a961b…` and split `b5967dd7…` filled; commit `a9d8ff5e…` proposed (`release.py` unchanged since; draft §5 item 1); G.1b and arms-record fields as placeholders of the required form |
| Which summaries | `g5_assemble.noise_by_node`: the seven nodes' pair = spec `noise_floor.seven` copy and sha256; autoresearch under G5-ARPEND A = the completion record's `noise_floor_copy`; D21 verdict and positive `sigma_joint` (STOP 5) | Placeholders `<SEVEN_G1B_COPY_*>` (one pair, written for each of the seven nodes) and `<AR_G1B_COPY_*>`; node set rule (draft §2) |
| The two stages | `g5_tasl.py assemble --stage traindev\|test --table --evidence --note` (`g5_assemble.assemble`: the train/dev row before anything sealed is opened; the test stage needs both rows and re-derives byte-identically) | Commands and preconditions per row (draft §2, §3) |
| Locks and purposes | `g5_seal.PURPOSES`: `assembly traindev:` and `release integrity traindev:` (UNSEAL); `assembly test:`, `release integrity test:`, `server log:` (TEST, with UNSEAL); `require`, `release_lock` = `release.release_row("T1", stage)`; `g5_assemble.read_evidence` (both blocks need TEST) | "What it unlocks" and "does not unlock" per row |
| Integrity check | `release_checks.g5_integrity`: G.5 paths and spec equal to `origin/main`; stage from `release.test_released("T1")`; `verify_evidence` inside `integrity_context` | Preconditions (the G.5 code on `main`, files frozen); the ordering note (train/dev release before the test row is on PLAN) |
| Release step | `python -m r1.c3.release --stage … --source g5 --table --audit --out`; `SOURCES["g5"] = "T1"`; D8 confirmation for `g5`; test stage needs the train/dev receipt under the same root | Commands; "no `--paper-root/--index/--classification` for g5"; same `--out` root |
| Readers | `release.traindev_labels`, `open_partition`, `builder_source`; raw locks `guard_raw_label_path` and `require_integrity_or_test_release` (unknown tier needs both test rows) | Listed per row |
| Arms-frozen record | `r1/c3/arms_freeze.py` (on `main`): path `docs/r1/…md` (`RECORD_PATH_RE`), `check --record`; `t1` block (suites in `gate.SUITES`, modes, `d3_k6`, instances with train and dev per node), `g1b_summaries` = the T1 node set, `label_tables.g5` | Test-row preconditions (draft §3) |
| Freeze wait | `g5_tasl.py freeze-wait … --before-arms-frozen` (STOP 14) | Command before the record; its two limits (it uses the spec's date, not the note's; any `--stopped` node STOPs) |

## 2. Machine checks run

The script is `/tmp/docdev/b/check_rows.py`, scratch, run with the worktree's `r1.c3.release`. It reads the draft's two
fenced texts and fills the placeholders with stand-ins of the right form. Results:

```
UNSEAL equals release.row_text: True
TEST equals release.row_text: True
UNSEAL fullmatch row_pattern: True | TEST fullmatch row_pattern: True
UNSEAL g1b items parsed: 8 True
UNSEAL (seven nodes only) equals row_text: True
UNSEAL (seven nodes only) fullmatch: True
author_rows finds both, text exact: True True
negative controls refused: [True, True, True, True]
```

The negative controls are: the T0 phrase in place of "the G.5 T1 tables", the last sentence dropped, the comma before
"after the arms-frozen record" dropped, and a 12-hex commit. The checks on the filled values (committed bytes,
ancestry, the frozen preregistration, the D8 row) need the rows on a PLAN with real files, and are not exercised here.

## 3. Open items

1. **Values not yet known:**
   - the seven-node REL-T1-G1B copy path and sha256 (the signed spec's `noise_floor.seven`), after the seven-node
     G.1b row is assembled under R1-G1B-JOIN and copied;
   - autoresearch's copy, from its completion record;
   - the arms-frozen record's path and sha256.
2. **The release-code commit** `a9d8ff5e…`: valid only while `r1/c3/release.py` is unchanged on `main`.
3. **ARMS-T1FEAT A** (R1-ARMS-DECISIONS): the T1 table has no features, and the arms code refuses rows without them.
   Until that unit is reviewed, T1 labels can be released but not used to freeze arms, so they would not be in the
   record. PRE-T1 A then freezes whatever T1 set the record names.
4. **The freeze of the G.5 files on `main`** (3b-2 report §5 item 6) needs a PLAN row or a coordinator rule. Without
   it, a change makes `g5_integrity` refuse the release (fail-closed).
5. **Two limits of the `freeze-wait` CLI**, noted for the cluster agent:
   - it uses the spec's date and does not read a date moved in the note;
   - with `--before-arms-frozen` it STOPs on any `--stopped` node, so a node STOP always goes to the author.
   Changing either is a code change. None is made here.
6. **Ordering.** The T1 train/dev release must be done before R1-T1-LABELS-TEST-RELEASE is on PLAN. After that row
   lands, `g5_integrity` runs the test-stage re-derivation.
7. **Not these rows, but upstream of them.** `g5_tasl.launch` checks the E4 row with `plan_row(e4_amendment_row,
   terms=("E4", "G5-MEM"))`. R1-G5-MEM-E4's text on `main` contains "E4" but not "G5-MEM" (checked with the code's own
   `plan_row`). As the code stands, no G.5 job runs under G5-MEM A, so there would be no T1 table to release.
