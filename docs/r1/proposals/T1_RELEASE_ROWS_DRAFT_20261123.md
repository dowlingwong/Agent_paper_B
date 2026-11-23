# Draft T1 release rows R1-T1-LABELS-UNSEAL and R1-T1-LABELS-TEST-RELEASE, bound to the G.5 code — approved: false

**Status: DRAFT. `approved: false`.** These rows are not author decisions. Each takes effect only when the author
signs it and it sits, with its placeholders filled, in a dated author table of PLAN §10 on published `main`.
- Drafted by the Mac-desk agent (Claude), AI-assisted, 23 Nov 2026. The base is branch `mac-g5-code-main-20261123`
  (`30e2d51a`: the G.5 code, parts 3a, 3b-1 and 3b-2, merged with `main` `000ac3b1`), and the authority is checked
  against `main` `89899f76`.
- No label, evaluation value, sealed file or receipt partition was read. Nothing ran on a host.
- The rows follow the signed templates of `proposals/R1_LABEL_RELEASE_ROWS_DRAFT_20261121.md` (the release-step
  decisions of R1-SWEEP2-RELEASE-DECISIONS). They fill in what is known now, and bind each row to what the G.5 code
  checks.

## 0. Authority and models (on `main` `89899f76`, unless stated)

| Source | What it fixes here |
|---|---|
| R1-SWEEP2-PREREG (`authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, frozen, sha256 `aa1a961b…`) | **PRE-STAGE A:** until the test release row exists, readers get the train/dev label block only and no evaluation value of any instance. **PRE-T1 A:** one primary read; the T1 node set and its instances are frozen in the arms-frozen record; "No test partition of any tier is released before the arms-frozen record." **PRE-DELTA A:** the T1 σ_node comes from each node's G.1b summary, whose "path and sha256 [are] recorded in the T1 train/dev release row, before any training". §4 steps 2–5 give the order. §8 names the ids R1-T1-LABELS-UNSEAL and R1-T1-LABELS-TEST-RELEASE. |
| R1-SWEEP2-RELEASE-DECISIONS | **REL-SCOPE A:** PRE-STAGE A as signed. **REL-CODE A:** integrity checks live in `r1/c3/release_checks.py`, so registering the G.5 check changes that file, not `release.py`. **REL-T1-G1B:** PRE-DELTA's "on H200" reads "on the T1 host of R1-T1-HOST-TASL"; each summary is copied out of the sealed tree by a reviewed step, with its sha256, before the T1 train/dev row. |
| R1-S2-LABELS-TRAINDEV-RELEASE (the model for the train/dev row) | The T0 train/dev row in the exact template text, release step `r1/c3/release.py` @ `a9d8ff5e6964ae25730b266d854927d85dc99c94`. It has been carried out twice: sweep 2 (receipt `de95b218…`, `reports/release_20261122/S2_TRAINDEV_RELEASE_20261122.md`, review ACCEPTED) and sweep 1 after R1-SWEEP1-RELEASE-COMPAT(-SCOPE) (receipt `f06e37a9…`, `reports/release_20261122/SWEEP1_TRAINDEV_RELEASE_20261123.md`). Each report records only receipt hashes and counts, and the receipts are copied beside the reports. |
| R1-S2-LABELS-TEST-RELEASE (drafted, not yet a row) | The model for the test row: the same template, which cites the arms-frozen record. |
| R1-BX-D8-CONFIRM-V31 | The D8 confirmation that the release step and every reader of a `g5` partition require (`analysis_guard.require_d8_confirmation`). |
| R1-G1B-JOIN; R1-G5-DECISIONS-2 (G5-ARPEND A) | The seven nodes' G.1b summary is the joined row of `g1b-tasl-20261121-b`. Autoresearch's comes through the G5-ARPEND A completion record. |
| R1-ARMS-DECISIONS | The arms-frozen record is made by `r1/c3/arms_freeze.py` (merge `630398c6`), format `r1_c3_arms_frozen/v1`: one Markdown file under `docs/r1/` with one fenced JSON block, which `release.row_text` cites. ARMS-T1FEAT A: a reviewed CPU unit gives G.5 rows the features. |
| G.5 code, part 3b-2 (on the branch; `reports/g5_code_20261123/G5_CODE_3B2_20261123.md`, review ACCEPTED) | The locked two-stage assembly `g5_assemble.py`; the lock names and purposes in `g5_seal.py`; the integrity check `release_checks.g5_integrity`; the REL-T1-G1B copy step `g5_relcopy.py`. |

## 1. What the code requires of the two rows

**Text.** `r1/c3/release.py` `release_row("T1", stage)` takes the decision cell of the row on the committed PLAN and
requires `re.fullmatch(release.row_pattern("T1", stage), cell)`. `release.row_text("T1", stage, …)` renders the same
text. So the cell holds exactly the release sentence below, with nothing before or after it. Any context belongs in
another row or in the report, never in this cell.

**Place.**
- The row id is `release.ROWS[("T1", "traindev")]` = `R1-T1-LABELS-UNSEAL`, or `[("T1", "test")]` =
  `R1-T1-LABELS-TEST-RELEASE`.
- It sits in a table of PLAN §10 under a dated author heading (`### <d> <Month> <yyyy> … (author)`), with the header
  `| ID | Decision |` (`release.author_rows`, using `analysis_guard._author_heading` and `_decision_header`).
- Each id appears exactly once.

**Fields and what `release_row` checks for each:**
- `prereg`: must equal the committed, frozen preregistration's sha256. The release step also checks the
  preregistration's final block: `frozen: true`, `pre_stage: A`, the split-file line, and the gate and gate-input
  builder sha256s equal to the committed files. So the gate is bound through the preregistration, not through the
  row.
- `split`: must equal `p3_split.P3_SPLIT_SHA256` (`b5967dd7…`).
- `commit`: a full 40- or 64-hex object id. It must be an ancestor of HEAD and of `origin/main`, and it must hold
  `r1/c3/release.py`. The step that writes a partition must run that very file (`writing=True`). Readers bind each
  receipt to its own commit.
- Train/dev row only, the G.1b items: `` `<node>`: `<path>` (sha256 `<hex>`) ``, joined by `; `. Each path must be a
  committed regular file whose bytes have that sha256, and no node may be repeated. `row_text` writes the items sorted
  by node name; the pattern accepts any order.
- Test row only: `` after the arms-frozen record `<docs/r1/…md>` (sha256 `<hex>`) ``. The record must be committed
  with those bytes.

**What the G.5 code adds on top** (`g5_assemble.noise_by_node`, `derive`):
- The nodes the train/dev row names are the nodes assembled and released.
- For each of the seven nodes, the cited `(path, sha256)` must equal the spec's `noise_floor.seven` `copy` and
  `sha256`: one REL-T1-G1B copy of the joined `g1b-tasl-20261121-b` `summary.json`, cited once per node.
- For `autoresearch_fixedtokens` under G5-ARPEND A, the cited pair must equal the completion record's
  `noise_floor_copy` (`g5_tasl.check_ar_record`, run on `main`).
- Each cited summary must have the right schema and run id, label ENGINEERING_ONLY, and the node's D21 verdict
  `qualifies_D21: true` with a positive finite `sigma_joint`; otherwise STOP 5.
- The assembly writes the train/dev row's id and decision sha256 into `build.json` and the completion record. The row
  text therefore must not change between the train/dev and test stages.

## 2. R1-T1-LABELS-UNSEAL (the T1 train/dev row)

**Exact text** (the decision cell; one line). Values known now are filled in:
- the frozen preregistration (`aa1a961b…`);
- the P3 split file (`b5967dd7…`);
- the release-code commit `a9d8ff5e…`, which the T0 train/dev row cites. `r1/c3/release.py` is unchanged from it to
  `main` `89899f76` and on the G.5 code branch (§5).

<!-- UNSEAL -->
```text
Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`): the train and dev label blocks of the G.5 T1 tables, with the T1 nodes' G.1b noise summaries `autoresearch_fixedtokens`: `<AR_G1B_COPY_PATH>` (sha256 `<AR_G1B_COPY_SHA256>`); `mlab_cifar10`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlab_imdb`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlab_ogbn_arxiv`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlgym_breakout_minatar`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlgym_cifar10`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlgym_fmnist`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`); `mlgym_houseprice`: `<SEVEN_G1B_COPY_PATH>` (sha256 `<SEVEN_G1B_COPY_SHA256>`), partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `a9d8ff5e6964ae25730b266d854927d85dc99c94`. No test label and no evaluation value is released by this row.
```

**Placeholders:**
- `<SEVEN_G1B_COPY_PATH>`, `<SEVEN_G1B_COPY_SHA256>`: the reviewed REL-T1-G1B copy of the seven-node summary on
  `main`, for example under `docs/r1/reports/<dir>/`. These are exactly the signed G.5 spec's `noise_floor.seven.copy`
  and `.sha256`; `g5_tasl.py rel-copy --kind seven` prints them. The same pair is written for each of the seven
  nodes.
- `<AR_G1B_COPY_PATH>`, `<AR_G1B_COPY_SHA256>`: autoresearch's REL-T1-G1B copy, exactly the completion record's
  `noise_floor_copy` (G5-ARPEND A).

**Which nodes the row names.**
- Every T1 node of the G.5 table that has not STOPped, all at once (PRE-T1 A and the G.5 freeze wait, STOP 14).
- A node is left out only after a node STOP and an author row on it (G.5 draft §4, "After a node STOP", and STOP 14).
  The node STOP may be STOP 5 at the switch (D21 at G.1b; the node is declared with `seal-run --not-run`) or a STOP
  during its jobs. The item for that node is then removed from the cell.
- If autoresearch is left out, the cell starts at `` `mlab_cifar10`: … ``; it still matches the pattern (§4).
- A node named here that did not complete G.5 STOPs the assembly (one complete sealed attempt per job and chunk), so
  the cell must not name it.

**What it unlocks** (each is a lock in the code that names R1-T1-LABELS-UNSEAL):
- The access-logged reader of the sealed G.5 tree (`g5_seal.SealedTree`) for the purpose `assembly traindev:`, and,
  inside the release step's integrity context only, `release integrity traindev:` (`g5_seal.PURPOSES`, `require`).
- The assembly's train/dev stage (`g5_tasl.py assemble --stage traindev`; `g5_assemble.assemble` checks this row before
  it opens anything sealed). It writes:
  - the T1 table (`proposals.jsonl`, `build.json`), which is open after this row, as the signed note's
    `t1_table_readings` line says;
  - the evidence directory (`label_block.jsonl` for every instance of the named nodes, test included, at the label
    seeds only; `evidence_completion.json`). The evidence directory stays closed to everything but the release step.
- The release step's train/dev stage for source `g5` (`python -m r1.c3.release --stage traindev --source g5 …`). It
  writes `label_block.traindev.jsonl`, the P3 train and dev rows only, with `RECEIPT.json`. The receipt records the
  row, its decision sha256, the G.1b summaries and the integrity result.
- Readers of that partition: `release.traindev_labels(root, "g5")` and `open_partition` (arms training and selection,
  A2's fit, PRE-SELECT's base rates; `arms_freeze` reads only this).

**What it does not unlock:**
- any test label;
- any evaluation-seed value (the evaluation block is not written before the test row, and at this stage no
  evaluation-seed kind or value leaves the sealed reader, `g5_seal.reduce_rows`);
- the evidence directory's blocks read back whole (`g5_assemble.read_evidence` needs the test row);
- TASL-7's sealed server logs (`server log:` needs the test row);
- raw T1 blocks (`release.guard_raw_label_path` needs the T1 test row; a reader with an unknown tier needs both
  tiers' test rows).
- Track P reads the T1 train/dev labels only if the author says so in a row (G.5 draft §6).

**Preconditions** (records on `main` unless stated; checked before the row is added to PLAN):
1. The signed G.5 note `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md` (approved: true), binding the committed spec
   `sweep2/t1_tasl/g5_tasl_spec.json` by sha256, with its `t1_table_readings` line. The assembly takes the readings and
   the Δ̂ choice from this note; without it only `refuse` applies.
2. The G.5 table run and sealed on TASL-2:
   - every attempt sealed (`seal-attempt`), every named node sealed (`seal-node`), and the run sealed (`seal-run`, with
     `--not-run` for nodes the switch refused), with the K lock in `_run`;
   - both access logs pass STOP 11;
   - TASL-7's server seal done and its span registered on TASL-2 (`seal-server`, `server-span`; G.5 code notes).
3. No unresolved node STOP: every node STOPped at G.5 has an author row (G.5 draft §4, "After a node STOP", and
   STOP 14).
4. The seven-node REL-T1-G1B copy and its cross-check gate copy, with an accepted review naming both sha256s and the
   sealed path (`g5_tasl.check_seven_copy`). Under G5-ARPEND A, if autoresearch is named, the one completion record
   `docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md` with its review (`g5_tasl.py check-ar-record` passes).
5. The G.5 code, with `release_checks.g5_integrity` registered, on `main`. The G.5 files under `sweep2/` (`t1_tasl`,
   `g1b`, `g4`, `s2_c2_lib.py`) and the spec unchanged on `main` since the G.5 launch (the freeze that 3b-2 report §5
   item 6 asks for).
6. `git diff a9d8ff5e6964ae25730b266d854927d85dc99c94 origin/main -- r1/c3/release.py` empty. If `release.py` has
   changed, the row cites the published commit whose `release.py` the step will run, and REL-CODE A's limit applies:
   the T0 rows keep their own commit.
7. Before the freeze-wait date of the signed note (*(proposed)* 2026-12-18): the release must happen by then, or STOP
   14 goes to the author.

**Commands** (the cluster agent, on TASL-2, where the sealed tree is; from a clean checkout of published `main` that
holds the row; `<PY>` the paper checkout's interpreter; output directories outside every sealed tree):

```
git -C <PAPER> fetch -q origin && git -C <PAPER> status --porcelain          # empty; HEAD = origin/main
<PY> sweep2/t1_tasl/g5_tasl.py assemble sweep2/t1_tasl/g5_tasl_spec.json --stage traindev \
  --table <T1_TABLE_DIR> --evidence <T1_EVIDENCE_DIR> \
  --note docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md
<PY> -B -m r1.c3.release --stage traindev --source g5 \
  --table <T1_TABLE_DIR> --audit <T1_EVIDENCE_DIR> --out <T1_RELEASE_ROOT>
```

- Do not pass `--paper-root`, `--index` or `--classification` for `--source g5`.
- Then copy `<T1_RELEASE_ROOT>/g5/traindev/RECEIPT.json` into the repository as
  `docs/r1/reports/release_<YYYYMMDD>/RECEIPT_g5_traindev.json`. Its report records only receipt hashes and counts
  (row, source, stage, tier, integrity pass, prereg, split, release commit, published commit, the G.1b summaries, the
  label-row counts per split, `released_label_rows`, `evaluation_rows` 0, the output sha256). The report gets an
  independent review, as for the sweep releases.
- Nobody opens `label_block.traindev.jsonl` beyond the receipt counts in that report.

**STOPs** (each returns to the author; nothing is retried by other means, and outputs are kept):
- **The row** (`release_row`, `ReleaseStop`):
  - absent or not unique;
  - text not exactly the pattern;
  - another preregistration or split sha256, or the preregistration not frozen;
  - the release commit not a published ancestor, or the running `release.py` not that commit's;
  - a G.1b summary repeated, missing, not committed or changed;
  - the D8 confirmation missing;
  - HEAD changing during the step.
- **The assembly** (`g5_assemble`):
  - the note not on `main` byte-identically, not approved, binding another spec, or with another `t1_table_readings`
    line;
  - a cited summary not the spec's seven-node copy or the completion record's copy;
  - a named node without a qualifying D21 verdict (STOP 5);
  - the run not sealed, or an access log failing STOP 11;
  - not exactly one complete sealed attempt per job and chunk, or a sealed attempt ending in an author STOP;
  - a node spec at the G.5 commit not matching `node_spec_sha256`;
  - the nodes audited at different K, or K not the sealed K lock's;
  - fewer than half the label seeds left after candidate and parent divergence;
  - under `refuse`, a proposal that diverged or timed out in its campaign;
  - an output directory inside a sealed tree, or one that already exists.
- **The release step** (`release.release`):
  - a checkout that is not clean, or whose authority and release code differ from `origin/main`;
  - the G.5 code or spec differing from `origin/main` (`g5_integrity`);
  - the integrity re-derivation not byte-identical (reported by exception type only);
  - an evaluation block present before the test row;
  - a table instance outside the split file, or a label row outside the table;
  - the output or a `.partial` existing.
- **The procedure:** any read of a test label or of an evaluation value (PRE-STAGE A; STOP 11 of the G.5 note).

## 3. R1-T1-LABELS-TEST-RELEASE (the T1 test row)

**Exact text** (the decision cell; one line):

<!-- TEST -->
```text
Release under PRE-STAGE A of the frozen sweep-2 analysis preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, sha256 `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`), after the arms-frozen record `<ARMS_FROZEN_RECORD_PATH>` (sha256 `<ARMS_FROZEN_RECORD_SHA256>`): the test label blocks and every evaluation block of the G.5 T1 tables, partitioned by the P3 split file (sha256 `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`) with the release step `r1/c3/release.py` @ `a9d8ff5e6964ae25730b266d854927d85dc99c94`.
```

**Placeholders:**
- `<ARMS_FROZEN_RECORD_PATH>`: the committed arms-frozen record. It must match `docs/r1/[A-Za-z0-9_./-]+\.md`, the
  form of `release.row_pattern` and of `arms_freeze.RECORD_PATH_RE`.
- `<ARMS_FROZEN_RECORD_SHA256>`: its sha256 as committed.
- These are the values `release.row_text("T1", "test", …, arms_path=, arms=)` takes. The same record is the one the T0
  test row cites: there is one arms-frozen record, holding both T0 and T1 (`t0_nodes`, `t1`).

**Order.** This row comes only after the arms-frozen record (preregistration §4 step 4; PRE-T1 A: "No test partition
of any tier is released before the arms-frozen record"):
1. R1-T1-LABELS-UNSEAL, the g5 train/dev receipt and its report;
2. the arms trained and selected on train/dev;
3. the freeze-wait check (STOP 14);
4. the arms-frozen record committed;
5. this row.

The T1 train/dev release must be done before this row is on PLAN. `release_checks.g5_integrity` chooses its stage
with `release.test_released("T1")`, so once this row exists the integrity check runs the test-stage re-derivation.

**What it unlocks** (each is a lock in the code that names R1-T1-LABELS-TEST-RELEASE):
- The sealed reader for `assembly test:`, `release integrity test:` (inside the integrity context) and `server log:`
  (TASL-7's sealed `llama-server.log`).
- The assembly's test stage. It re-derives the table and label block, refuses any byte difference, reads the
  evaluation seeds, and writes `evaluation_block.jsonl` and `evidence_completion_test.json`.
- The release step's test stage for `g5`: `label_block.test.jsonl` and `evaluation_block.all.jsonl`, with their
  receipt, from the same label block and table as the train/dev receipt.
- `release.builder_source(root, "g5", table)` for the gate input (both partitions).
- `g5_assemble.read_evidence` for both blocks.
- The T1 raw-block locks (`release.test_released("T1")` true). Readers with an unknown tier also need the T0 test row
  (REL-SCOPE A).

**Preconditions:**
1. R1-T1-LABELS-UNSEAL on `main`, unchanged; the g5 train/dev receipt written and published with its reviewed report.
2. The arms-frozen record committed on `main` at `<ARMS_FROZEN_RECORD_PATH>`, and `python -m r1.c3.arms_freeze check
   --record <ARMS_FROZEN_RECORD_PATH>` passing. In the record:
   - `t1.suites` names the frozen T1 nodes (with suites in `gate.SUITES`): exactly the nodes R1-T1-LABELS-UNSEAL
     released and the arms used, each with at least one train and one dev instance (PRE-T1 A);
   - `t1.instances` lists the frozen instances;
   - `t1.modes` names the one memory mode `history` (G5-MEM A, R1-G5-MEM-E4), and `t1.d3_k6` is false unless the note
     was amended to K = 6 after a K-check row (P4 of the G.5 note);
   - `g1b_summaries` covers exactly that node set, with the same committed copies the train/dev row cites;
   - `label_tables.g5` binds the g5 train/dev receipt, partition, label block and table sha256s.
3. The freeze-wait check passed before the record (`g5_tasl.py freeze-wait … --before-arms-frozen`, every un-STOPped
   node released and none STOPped), or an author row freezes the arms without a node (STOP 14).
4. The table and evidence directories unchanged since the train/dev stage; the G.5 code and spec still equal
   `origin/main`; `release.py` still at the cited commit.

**Commands** (on TASL-2, as in §2, from a clean checkout of published `main` that holds this row):

```
<PY> sweep2/t1_tasl/g5_tasl.py freeze-wait sweep2/t1_tasl/g5_tasl_spec.json --today <YYYY-MM-DD> \
  --released <nodes released by R1-T1-LABELS-UNSEAL> --stopped <nodes STOPped at G.5, STOP 5 included> --before-arms-frozen
                                    # run before the arms-frozen record is committed, not after this row
<PY> -m r1.c3.arms_freeze check --record <ARMS_FROZEN_RECORD_PATH>
<PY> sweep2/t1_tasl/g5_tasl.py assemble sweep2/t1_tasl/g5_tasl_spec.json --stage test \
  --table <T1_TABLE_DIR> --evidence <T1_EVIDENCE_DIR> \
  --note docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md
<PY> -B -m r1.c3.release --stage test --source g5 \
  --table <T1_TABLE_DIR> --audit <T1_EVIDENCE_DIR> --out <T1_RELEASE_ROOT>
```

- Use the same `--note`, the same table and evidence directories, and the same `--out` root as at the train/dev stage:
  the test stage opens `<T1_RELEASE_ROOT>/g5/traindev`.
- The receipt goes to `docs/r1/reports/release_<YYYYMMDD>/RECEIPT_g5_test.json`, with a report of hashes and counts
  and an independent review.
- `freeze-wait` uses the spec's date (`key_values.freeze_wait_release_date`); the CLI does not read the note. If an
  author row has moved the date in the note, the operator compares with the note's date by hand. This is a limit of
  the code, recorded in the report.
- `freeze-wait --before-arms-frozen` STOPs (STOP 14) whenever `--stopped` is not empty. A node STOPped at G.5 therefore
  always goes to the author before the arms-frozen record, even when the train/dev row has left it out.

**STOPs:**
- **The row:** as in §2, plus the arms-frozen record missing or changed (`release_row`); PRE-T1 A's "No test partition
  of any tier is released before the arms-frozen record".
- **The assembly:**
  - the table, `build.json` or label block not what the sealed tree gives now;
  - an evaluation seed where only the parent diverged;
  - an evaluation block that already exists.
- **The release step:**
  - no train/dev receipt under the same root, or one from another label block or table;
  - the integrity re-derivation of the evaluation block not byte-identical;
  - an evaluation row outside the table.
- **The arms-frozen record** failing `arms_freeze check`, or changed after it is committed (preregistration §6).

## 4. Machine checks of the two texts (run on this draft)

`/tmp/docdev/b/check_rows.py` (scratch, outside the repository) reads the two fenced blocks of this file and fills the
placeholders with stand-in values: all-`1`, `2` and `3` hex for the unknown sha256s, and paths of the required forms.
It then checks:
- each text equals `release.row_text("T1", stage, …)` for the same values, and matches `re.fullmatch(row_pattern)`;
- the G.1b items parse into eight nodes, the split file's eight T1 nodes, and a seven-node variant without
  autoresearch still matches and equals `row_text`;
- `release.author_rows` finds both rows, with exact text, in a dated author table (`### 24 November 2026 — T1 release
  (author)`, `| ID | Decision |`);
- four altered texts are refused: the T0 phrase, a missing final sentence, a missing comma before "after the
  arms-frozen record", and a short commit.

The result is in the report (`reports/g5_code_20261123/T1_RELEASE_ROWS_DRAFT_20261123.md` §2). The code checks the
filled values themselves (committed bytes, ancestry, frozen preregistration) only when the rows are on PLAN, so they
are not exercised here.

## 5. Open points (for the coordinator and the author; nothing here is decided)

1. **The release-code commit.** `a9d8ff5e…` is proposed because `r1/c3/release.py` is byte-identical from it to `main`
   `89899f76` and to the G.5 code branch, and the T0 rows cite it. If `release.py` changes before the T1 release, the
   T1 rows cite the new published commit (REL-CODE A).
2. **The seven-node copy path.** It is not known until the REL-T1-G1B copy is made and reviewed. It must be the signed
   spec's `noise_floor.seven.copy`, which the note binds by the spec's sha256.
3. **T1 features (ARMS-T1FEAT A).** The T1 table carries `features: {}`, and the arms code refuses rows without the
   full feature set. Until the CPU unit of ARMS-T1FEAT A is reviewed, T1 can be released (this row) but cannot be used
   to train arms, so it would not be in the arms-frozen record. That is arms work, not these rows.
4. **The freeze of the G.5 files on `main`** from launch to the T1 test release (3b-2 report §5 item 6) has no PLAN row
   or coordinator rule yet. Without it, a change to those files on `main` makes `g5_integrity` refuse. That refusal is
   fail-closed: it blocks the release, it does not corrupt it.
5. **The T0 test row** (R1-S2-LABELS-TEST-RELEASE) cites the same arms-frozen record. The two test rows may sit in one
   author table. Readers of unknown tier open only when both exist.
