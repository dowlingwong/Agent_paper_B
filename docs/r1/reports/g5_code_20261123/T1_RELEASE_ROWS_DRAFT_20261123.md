# T1 release rows: drafts bound to the G.5 code (23 Nov 2026)

ENGINEERING_ONLY report. AI-assisted (Mac-desk agent, Claude). Branch `mac-t1-release-rows-20261123`, from
`mac-g5-code-main-20261123` @ `30e2d51a`, merged after review round 1 with that branch at `baf6be5d` (main `89899f76`
and the G5-MEM A row-check fix), and after review round 2 with that branch at `2582c898` (the row check refactored into
`g5_tasl.decision_row_checks`, accepted by the G.5-on-main review). §4 and §5 map the round-1 and round-2 findings to
their fixes. The features unit is cited at `mac-t1-features-20261123` @ `a5715142` (accepted, review record pending).
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
| Arms-frozen record | `r1/c3/arms_freeze.py` (on `main`): path `docs/r1/…md` (`RECORD_PATH_RE`), `check --record`; `t1` block (suites in `gate.SUITES`, modes, `d3_k6`, instances with train and dev per node), `g1b_summaries` = the T1 node set, `label_tables.g5` (re-hashed against the g5 receipt only with `--release-root g5=…`) | Test-row preconditions and command (draft §3), with two procedural STOPs no code makes |
| Freeze wait | `g5_tasl.py freeze-wait … --before-arms-frozen` (STOP 14) | Command before the record; its two limits (it uses the spec's date, not the note's; any `--stopped` node STOPs) |

## 2. Machine checks run

The script was scratch (`/tmp/docdev/b/check_rows.py`), run from the worktree with `python -I` and the worktree's
`r1.c3.release`. Its essential lines, enough to reproduce it:

```python
import re, sys; sys.path.insert(0, ".")
from r1.c3 import release as R
PREREG, SPLIT = "aa1a961b…7cc5", "b5967dd7…e569"            # the full values, as in the draft
COMMIT = "a9d8ff5e6964ae25730b266d854927d85dc99c94"
H7, HAR, HARMS = "1" * 64, "2" * 64, "3" * 64                 # stand-ins for unknown sha256s
P7 = "docs/r1/reports/g5_relcopy_YYYYMMDD/seven/summary.json"
PAR = "docs/r1/reports/g5_relcopy_YYYYMMDD/ar/summary.json"
ARMS = "docs/r1/reports/arms_frozen_YYYYMMDD/ARMS_FROZEN_YYYYMMDD.md"
seven = ["mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist",
         "mlgym_breakout_minatar", "mlgym_houseprice"]
g1b = {n: (P7, H7) for n in seven} | {"autoresearch_fixedtokens": (PAR, HAR)}
draft = open("docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md").read()
tmpl = dict(re.findall(r"<!-- (UNSEAL|TEST) -->\n```text\n(.*?)\n```", draft, re.S))
def fill(t, drop_ar=False):
    if drop_ar:
        t = t.replace("`autoresearch_fixedtokens`: `<AR_G1B_COPY_PATH>` (sha256 `<AR_G1B_COPY_SHA256>`); ", "")
    for a, b in (("<SEVEN_G1B_COPY_PATH>", P7), ("<SEVEN_G1B_COPY_SHA256>", H7), ("<AR_G1B_COPY_PATH>", PAR),
                 ("<AR_G1B_COPY_SHA256>", HAR), ("<ARMS_FROZEN_RECORD_PATH>", ARMS),
                 ("<ARMS_FROZEN_RECORD_SHA256>", HARMS)):
        t = t.replace(a, b)
    assert "<" not in t
    return t
u, t = fill(tmpl["UNSEAL"]), fill(tmpl["TEST"])
assert u == R.row_text("T1", "traindev", prereg=PREREG, split=SPLIT, commit=COMMIT, g1b=g1b)
assert t == R.row_text("T1", "test", prereg=PREREG, split=SPLIT, commit=COMMIT, arms_path=ARMS, arms=HARMS)
assert re.fullmatch(R.row_pattern("T1", "traindev"), u) and re.fullmatch(R.row_pattern("T1", "test"), t)
u7 = fill(tmpl["UNSEAL"], drop_ar=True)
assert u7 == R.row_text("T1", "traindev", prereg=PREREG, split=SPLIT, commit=COMMIT,
                        g1b={n: (P7, H7) for n in seven})
plan = ("## 10. Decisions\n\n### 24 November 2026 — T1 release (author)\n\n| ID | Decision |\n|---|---|\n"
        f"| R1-T1-LABELS-UNSEAL | {u} |\n| R1-T1-LABELS-TEST-RELEASE | {t} |\n\n## 11. Next\n")
rows = dict(R.author_rows(plan))
assert rows["R1-T1-LABELS-UNSEAL"] == u and rows["R1-T1-LABELS-TEST-RELEASE"] == t
for b, st in ((u.replace("the G.5 T1 tables", "both sources (sweep 1 and sweep 2)"), "traindev"),
              (u.replace(" No test label and no evaluation value is released by this row.", ""), "traindev"),
              (t.replace(", after the arms-frozen record", " after the arms-frozen record"), "test"),
              (u.replace(COMMIT, COMMIT[:12]), "traindev")):
    assert not re.fullmatch(R.row_pattern("T1", st), b)
```

(`PREREG` and `SPLIT` are written in full in the script; they are shortened here only for the page.) Results after the
round-1 revision (the row texts did not change):

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
3. **ARMS-T1FEAT A** (R1-ARMS-DECISIONS): the features are table bytes, written by the assembly under the features unit
   (`mac-t1-features-20261123` @ `a5715142`). Its deadlines (its report §5): D1–D4, D6-σ, D8, D9 final with the code
   on `main` before the G.5 launch; D5 decided by R1-ARMS-DECISIONS; D6 before the gate run's noise (before the launch
   under D6-σ B); D7 (a T1 A5 input) before the arms-frozen record, else a STOP to the author (draft §2 precondition 0;
   §3 Order step 2 and precondition 3). The arms-frozen record is not committed while freeze-wait fails or STOPs, and
   A3 is retrained with g5 once T1 is released (draft §3, Order).
3a. **T1 σ_node and δ_n:** the row cannot cite `runs.jsonl` copies; D6 binds through the summary's hash chain. Under
   D6 A an author row amends REL-T1-G1B's copy list. The arms-frozen record has no T1 noise slot (`check_record` pins
   `noise_source` to the T0 file), so the noise record's binding is either an `arms_freeze` change or procedural,
   through `g5_noise.builder_noise(sha256=…, raw=…)`. PRE-DELTA's "recorded in the row" is met directly for σ_node only
   under D6-σ A; otherwise, and for δ_n under D6 A/B, transitively; under D6 C not at all. The draft proposes an author
   note (draft §5 item 3a).
4. **The freeze of the G.5 files on `main`** (3b-2 report §5 item 6) needs a PLAN row or a coordinator rule. The code
   does not enforce it (`_g5_unpublished` compares HEAD with `origin/main`); the draft adds an explicit
   `git diff --quiet <G5_LAUNCH_COMMIT> origin/main -- sweep2/t1_tasl sweep2/g1b sweep2/g4 sweep2/s2_c2_lib.py` before
   each stage.
5. **Two limits of the `freeze-wait` CLI**, noted for the cluster agent:
   - it uses the spec's date and does not read a date moved in the note;
   - with `--before-arms-frozen` it STOPs on any `--stopped` node, so a node STOP always goes to the author.
   Changing either is a code change. None is made here.
6. **Ordering.** The T1 train/dev release must be done before R1-T1-LABELS-TEST-RELEASE is on PLAN. After that row
   lands, `g5_integrity` runs the test-stage re-derivation.
7. **The TASL-2 environment** for the assembly and the release step (`<PY>`, importing `r1.c3` and the G.5 code) is
   not yet recorded; the cluster agent names it in the release report.
8. (Withdrawn after the merge of `baf6be5d`.) The first version of this report said the switch's E4-row check refused
   R1-G5-MEM-E4. At `baf6be5d` the check is the decisions row for the eight options plus the E4 row id, and the E4 row
   for "E4" and "memory modes"; both rows on `main` pass. That fix was accepted by the G.5-on-main review (record pending) and is `g5_tasl.decision_row_checks` since `2582c898`.

## 4. Review round 1 (NOT ACCEPTED, no blocking finding): findings and fixes

The row texts are unchanged; the machine checks of §2 still pass.

| Finding | Fix (draft section) |
|---|---|
| **M1** features and release order | §2 precondition 0 (ARMS-T1FEAT unit merged on `main` before the G.5 launch, its decisions signed before the launch (corrected in round 2, §5); why a featureless table cannot feed the arms); §3 Order (A3 retrained with g5 once T1 is released; the arms-frozen record not committed while freeze-wait fails or STOPs; the coordinating chat holds it); §5 item 3 rewritten. |
| **M2** δ_n | §5 item 3a: the row cannot cite `runs.jsonl` copies; D6 binds through the summary's hash chain or the arms-frozen record and a reviewed noise record; met transitively for δ_n under D6 A/B, not under C; an author note proposed; citing more files needs a `release.py` change and a new release commit. |
| **M3** arms-record check | §3 Commands: `arms_freeze check --record … --release-root g5=<T1_RELEASE_ROOT> --artefact-root …` on TASL-2; two procedural STOPs (`t1.suites` against the released node set; `g1b_summaries` against the row's pairs). |
| **M4** freeze | §2 precondition 5 and §5 item 4: `_g5_unpublished` compares HEAD with `origin/main` and does not see a change on `main`; the explicit `git diff --quiet <G5_LAUNCH_COMMIT> origin/main -- …` check before each stage; the spec bound by `spec_sha256`. |
| **m1** note unchanged | §3 precondition 4 (precondition 5 after round 2) and the freeze-wait bullet: any amendment of the note must come before the train/dev assembly. |
| **m2** commands | §2 Commands: `cd <PAPER>`, the clean and HEAD = `origin/main` tests, the environment and thread variables, how `check_seven_copy` is run (no CLI; a one-liner with the switch's function) and `check-ar-record`. |
| **m3** gate citation | §5 item 6: the difference from G.5 draft §6 item 1, for the author. |
| **m4** script | §2 above: its essential lines. |

## 5. Review round 2 (NOT ACCEPTED, no blocking finding): findings and fixes

Merged `mac-g5-code-main-20261123` @ `2582c898` first (merge `55716fa3`). The row texts are unchanged; the machine
checks of §2 still pass.

| Finding | Fix (draft section) |
|---|---|
| **M1** precondition 0 against the features unit's deadlines | §2 precondition 0 restated with the unit's report §5 deadlines (D1–D4, D6-σ, D8, D9 final with code on `main` before the launch; D5 decided; D6 before the gate-run noise, before the launch under D6-σ B; D7 before the arms-frozen record). §3: D7 added to the Order (step 2) and as precondition 3, a STOP to the author if unsettled. §5 item 3 and this report's §3 item 3 updated. |
| **M2** point 3a | (a) σ_node met directly only under D6-σ A; (b) the REL-T1-G1B amendment row named under D6 A; (c) no T1 noise slot in `arms_freeze.check_record` (it pins `noise_source` to the T0 file): either an `arms_freeze` change or a procedural binding through `g5_noise.builder_noise(record, sha256=…, raw=…)`. |
| **m1** arms check on two hosts | §3 Commands: the check may be split, `--release-root g5=…` on TASL-2 and `--artefact-root …` where the artefacts live; both must pass. |
| **m2** `-B` | The `check_seven_copy` one-liner runs with `-I -B`. |
