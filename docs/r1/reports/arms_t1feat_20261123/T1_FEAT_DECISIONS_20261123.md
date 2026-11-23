# R1-T1-FEAT-DECISIONS: D6 A, D6-σ B and D9 B built; the launch row check (23 Nov 2026)

ENGINEERING_ONLY report. AI-assisted (Mac-desk agent, Claude). Branch `mac-t1-feat-decisions-20261123`, from
origin/main `14f19a09` (READY 91, 92 and 96 on main: the G.5 code, the T1 features and the follow-ups).
- Nothing was run on a host. No server was contacted.
- No label, evaluation value, sealed file or real ledger was read. Tests use synthetic G.1b runs, synthetic copies and
  the synthetic G.5 world of `test_t1_g5_seal.py`.
- `gate.py`, `gate_input_builder.py`, `release.py`, `release_checks.py`, `r1/c3/features.py`, `r1/c3/dataset.py` and
  the frozen preregistration are unchanged.

**Authority.** The author's row **R1-T1-FEAT-DECISIONS** records the decisions of the ARMS-T1FEAT A report
(`T1_FEATURES_20261123.md` §5): D1–D4 A and D8 A (as built, no change); D6 A (amending REL-T1-G1B's copy list);
D6-σ B; D7 (a T1 prompt form for A5: a separate unit, not this one); D9 B. **The row is not on main yet.** This unit
takes the decisions from the coordinator's instruction. PLAN §10 on published main wins over this report: if the
published row differs, this code must be changed before the launch. Until the row is published, the G.5 switch
STOPs every job (§4).

## 1. What changed, per decision

| Decision | Change | Where |
|---|---|---|
| D1–D4 A, D8 A | None (as built). D8 A is one of the terms the switch requires in the row (§4) | — |
| **D6 A** | The REL-T1-G1B copy step also copies the G.1b run's `ASSEMBLY.json` and `runs.jsonl` beside the summary copy, with their sha256s. The switch checks them on main for the seven-node copy and for autoresearch's | `g5_relcopy.py`, `g5_tasl.py` (`run_copies`, `check_g1b_copy`, `validate_spec`, `apply_options`), the spec |
| **D6-σ B** | T1's σ_node is T0's definition, computed from the bound `runs.jsonl` copies, selected by the spec field `noise_floor.t1_sigma_node: "t0_definition"`. The 3b-2 `sigma_joint` path is **removed** | `g5_assemble.noise_by_node`, `g5_noise.py`, `g5_tasl.TABLE_READINGS`, the spec |
| **D9 B** | The assembly STOPs on any non-zero `raw_state_missing` or `flag_mismatch` count, in both stages and in the release step's re-derivation | `g5_assemble.derive` (`D9_COUNTS`, `D9_STOP`) |
| D7 | Not in this unit | — |
| (launch) | The switch requires R1-T1-FEAT-DECISIONS on main, naming `D6 A`, `D6-σ B`, `D8 A`, `D9 B` | `g5_tasl.launch` (`T1_FEAT_ROW`, `T1_FEAT_TERMS`) |

### 1.1 D6 A: the copy step and its binding

**What the copy step does** (`g5_tasl.py rel-copy <spec> --kind seven|ar --summary <sealed summary.json> --dest
docs/r1/reports/<dir>`, i.e. `g5_relcopy.copy_summary`). For each G.1b run (the seven-node run
`g1b-tasl-20261121-b` and autoresearch's `g1b-ar-tasl-20261122-a`; one run directory each):
- It runs every check of the reviewed step as before (sealed tree, schema, run id, nodes, the summary bound to
  `ASSEMBLY.json` and `runs.jsonl`, the cross-check gate for the seven nodes).
- It applies `refuse_sealed`'s check (`g5_noise._refuse_sealed`, a tested copy of
  `r1.c3.analysis_guard.refuse_sealed`) to the summary, `ASSEMBLY.json` and `runs.jsonl`. `ASSEMBLY.json` and
  `runs.jsonl` must be regular files (no symlink).
- It parses `runs.jsonl` with `g5_noise.g1b_rows`. A record whose seed lies in 7001–7010 is a STOP. "Seed" means
  `seed`, `train_seed`, `split_seed` or any other `*_seed` integer field. The STOP names the file only. Nothing is
  copied.
- For every node of the summary, the edit count and every edit's paired-seed count from `runs.jsonl`
  (`g5_noise.edit_stats`) must equal the summary's `n_edits` and `paired_joint_n`. This is what `g5_noise.derive`
  checks later on the copies; a summary verdict without them is a STOP.
- Only then does it write into `<dest>/`: `summary.json`, `ASSEMBLY.json`, `runs.jsonl` (byte-identical, re-hashed
  after writing), `crosscheck_gate.json` (seven nodes) and `COPY_RECORD.json`.

**What `COPY_RECORD.json` now holds** besides the earlier fields:
- `assembly_copy`, `assembly_sha256`, `runs_copy`, `runs_sha256`, `sealed_assembly_path`, `sealed_runs_path`;
- the authority line, which names R1-T1-FEAT-DECISIONS D6 A;
- `spec_fields` with the four new `noise_floor.seven.*` fields (or `spec_fields_under_arpend_b` with
  `noise_floor.ar.*`);
- `review_must_name`, which now also lists the two copies and their sha256s.

**The binding chain.** The summary copy's `assembly_sha256` is sha256(`ASSEMBLY.json`), and that file's
`runs_sha256` is sha256(`runs.jsonl`). So the summary sha256, which the train/dev row records (PRE-DELTA), pins
both copies. The chain is checked:
- at copy time (`check_source`);
- at every G.5 job start (`check_g1b_copy` → `run_copies`), on published main;
- at every read (`g5_noise.node_delta`, called by `g5_assemble.noise_by_node`).

**Where the paths and sha256s are recorded:**
- **Seven nodes:** the spec's `noise_floor.seven` gains `assembly_copy`, `assembly_sha256`, `runs_copy`,
  `runs_sha256`. They are PENDING now and filled from `COPY_RECORD.json`'s `spec_fields` before the signature, like
  the summary's fields.
  - `validate_spec`: the two sha256 fields must be sha256s (PENDING allowed before launch). At launch, the two paths
    must be `ASSEMBLY.json` and `runs.jsonl` beside the summary copy.
  - `check_g1b_copy` at the switch: the two files are on main, bound by the chain, equal to the spec's four fields,
    and named with their sha256s in the same accepted review as the summary.
- **Autoresearch under G5-ARPEND A** (the option in the spec): the spec's `noise_floor.ar` keeps the PENDING marker
  for the four new fields too (`apply_options` sets it).
  - The completion record's format is **not** changed. Its `noise_floor_copy` names the summary copy, and the run
    copies are the files beside it.
  - `check_ar_record` → `check_g1b_copy` checks them on main, by the chain, and requires the copy's review
    (`noise_floor_copy_review`) to name both paths and sha256s.
  - `g5_assemble.noise_by_node` takes the four fields from that check's result.
- **Autoresearch under G5-ARPEND B:** the same four fields in the spec's `noise_floor.ar`.

**Release checks.** `release_checks.py` (`G5_PATHS`, `g5_integrity`) and `release.py`'s train/dev row check are not
changed:
- `release.py` already checks each cited summary's bytes against the row's sha256 and requires them published and
  clean.
- The run copies are pinned by that summary through the chain. `g5_integrity` re-derives the table through
  `noise_by_node`, which re-checks the chain on every read. A changed copy therefore makes the integrity check fail.
- `G5_PATHS` covers the G.5 code and spec, not data under `docs/`. The summary copies were never in it either.

### 1.2 D6-σ B: σ_node by T0's definition

**The rule.** `dataset.noise_table`'s rule:
- σ_node is the median `sd_joint` over material edits, or over all edits with an sd if none is material;
- "material" is as in `e1_report`: resolved (|Δ̂_J| > 2 se, or Δ̂_J ≠ 0 when se = 0) and |Δ̂_J| ≥ 0.002;
- per edit, the sd (numpy, ddof 1) of m(c_k, s) − m(c0, s) over the joint seeds, from successful runs with a metric,
  with at least three paired seeds.

**Where it is computed.** `g5_noise.node_delta` computes it, together with D18's δ_n, from one node's bound run. This
is the code the ARMS-T1FEAT unit already had (`edit_stats`, then `sigma_node_t0_definition`); it is reused, not
duplicated.

**One value, by construction.**
- `g5_assemble.noise_by_node` (the table's σ_node) calls `node_delta` on the committed copies beside each cited
  summary copy. Its σ_node is `sigma_node_t0_definition`.
- `g5_noise.derive` no longer computes anything itself. It takes every value from `noise_by_node`, so the record's
  σ_node and δ_n are the very values the table uses.
- σ_node enters the table bytes as the rows' `sigma_node` and `sigma_cmp`, the soft-label width
  (`soft_parameters.sigma_node`), the features' `recorded_gain_z`, and `build.json`.
- `derive` also refuses a record whose σ_node is not the T0-definition value (a guard; it cannot fail as built).

**The spec field.** `noise_floor.t1_sigma_node: "t0_definition"`. `validate_spec` and `noise_by_node` refuse any other
value, including a missing one.

**The old `sigma_joint` path is removed**, not merely unreachable: `noise_by_node` has no branch that reads the
summary's `sigma_joint` for σ_node. The summary's `sigma_joint` is still reported for disclosure:
- in `build.json` (`nodes.<node>.sigma_joint`);
- in the noise record.

**STOP 5 now reads:** "a qualifying G.1b verdict (`qualifies_D21`)". A node without a positive σ_node by T0's
definition is a separate STOP. A run whose paired differences are all equal, for example, has sd 0.

**What `build.json` carries per node now** (table bytes):
- `sigma_node` and `sigma_node_rule: "t0_definition"`;
- `sigma_joint` (disclosure);
- `delta_n`, `median_paired_sd`, `sigma_node_t0_definition`, `n_material_edits`, `n_edits`, `n_edits_with_sd`,
  `paired_joint_n`;
- the summary path and sha256, and `assembly_copy`, `assembly_sha256`, `runs_copy`, `runs_sha256`.

No absolute path is included: `node_delta` no longer returns `run_dir`, so the table bytes do not depend on where the
checkout lies.

**The noise record** is now schema `g5_t1_noise/2` (`/1` carried `sigma_joint` as σ_node; none was written). It adds
`t1_sigma_node`, `decisions_row`, and the per-node fields above. `builder_noise` refuses a `/1` record.

**`derive`'s `run_dirs` argument** is now optional. If it is given, each directory must be the copy directory beside
the node's summary copy. Under D6 A no other directory is read.

**The note's `t1_table_readings` line** changes with D6-σ B (`g5_tasl.TABLE_READINGS["sigma_cmp"]`). It now reads
"sigma_cmp = sigma_node (dataset.noise_table's definition, the median joint paired sd over material edits, on the
node's G.1b runs.jsonl copied beside its summary; R1-T1-FEAT-DECISIONS D6-sigma B)". The G.5 draft anticipated this
("under B the spec gains a field and the line may change, so the spec and the line are re-issued before the
signature").

**The gate input end to end.** `gate_input_builder.build` refuses "a node whose table rows carry another σ_node". The
test builds a T0 + T1 gate input with the frozen builder from the assembled synthetic table and `derive`'s record,
and the refusal does not fire. A record carrying the summary's `sigma_joint` instead is refused ("table sigma_node
differs from the noise source").

### 1.3 D9 B: STOP on a non-zero count

`g5_assemble.derive` STOPs after each node's rows if `raw_state_missing` or `flag_mismatch` is not 0. The reason is a
fixed text with the node and the names of the non-zero counts only, no count and no value:

> STOP (R1-T1-FEAT-DECISIONS D9 B): {node}: {counts} is not 0: the ledgers are not shaped as the harness writes them
> (raw code states in every run record; the harness's inert and duplicate verdicts agreeing with the code-state
> fields); the assembly does not go on

`derive` runs in the train/dev stage, in the test stage (before the evaluation block is written) and in
`verify_evidence` (the release step's integrity check). Nothing is written on the STOP. `build.json` still carries the
two counts per node (always 0 in a table that exists).

**Test fixtures.** The synthetic campaign ledgers of `test_t1_g5_seal.py` are now shaped as the harness writes them:
raw code states in every run record, and a duplicate that repeats an evaluated, non-incumbent state (step 2's). Under
D9 B the earlier shapes would STOP every assembly test. Those shapes stay available (`raw=False`,
`dup_of_incumbent=True`) for the D9 tests. One assertion changed with this: the duplicate's `candidate_hash` is now
step 2's state.

## 2. Files

| File | Change |
|---|---|
| `sweep2/t1_tasl/g5_relcopy.py` | D6 A: copies `ASSEMBLY.json` and `runs.jsonl`; seed guard; count check; `refuse_sealed` on every source; record fields and needles |
| `sweep2/t1_tasl/g5_noise.py` | `g1b_rows` (seed guard), `T1_SIGMA_NODE`, `AUDIT_SEEDS`; `node_delta` used by the table; `derive` takes every value from `noise_by_node`; schema `/2`; the import of `g5_assemble` moved into `derive` (g5_assemble now imports g5_noise) |
| `sweep2/t1_tasl/g5_assemble.py` | `noise_by_node`: D6 A copies and D6-σ B; `derive`: D9 B STOP; docstring |
| `sweep2/t1_tasl/g5_tasl.py` | `run_copies`, `check_g1b_copy` (copies on main, review needles), `validate_spec` (`t1_sigma_node`, the four fields), `apply_options` (the AR marker), `TABLE_READINGS["sigma_cmp"]`, `T1_FEAT_ROW` / `T1_FEAT_TERMS` and the launch check |
| `sweep2/t1_tasl/g5_tasl_spec.json` | `noise_floor.t1_sigma_node: "t0_definition"`; the four D6 A fields in `noise_floor.seven` (PENDING) and `noise_floor.ar` (the G5-ARPEND A marker). The spec sha256 changes (it is unsigned) |
| `r1/tests/test_t1_g5_seal.py` | synthetic G.1b copies (`g1b_runs`, `g1b_copy`); ledgers shaped as the harness writes them; copy-step tests |
| `r1/tests/test_t1_features.py` | D9 B tests; T1 noise tests rewritten for D6 A / D6-σ B |
| `r1/tests/test_t1_g5_tasl.py` | the launch world with run copies and the R1-T1-FEAT-DECISIONS row; new row, spec and validation tests |
| this report, `FULLSUITE_BASE_14f19a09.txt`, `FULLSUITE_TIP.txt` | new |

## 3. What the cluster must run, and when

`sweep2/t1_tasl` and the spec freeze on main at the G.5 launch (3b-2 report §5 item 6). This unit must therefore be
on main **before** the launch, with the published row.

**Before the G.5 launch:**
1. The author publishes **R1-T1-FEAT-DECISIONS** on main. Its text must contain the literal strings `D6 A`,
   `D6-σ B`, `D8 A` and `D9 B` (§4). This unit is merged to main.
2. **The seven-node copy step on the T1 host** (the host of R1-T1-HOST-TASL that holds `sealed_g1b`), from a clean
   checkout of main that contains this unit:
   `python sweep2/t1_tasl/g5_tasl.py rel-copy sweep2/t1_tasl/g5_tasl_spec.json --kind seven --summary <sealed summary.json> --dest docs/r1/reports/<dir>`.
   It writes `summary.json`, `crosscheck_gate.json`, `ASSEMBLY.json`, `runs.jsonl` and `COPY_RECORD.json`. A seed in
   7001–7010, a count mismatch or a broken binding is a STOP, and nothing is written.
3. **Commit the copies** (all five files) and have them reviewed independently. The review must name every entry of
   `review_must_name`: the summary, gate, `ASSEMBLY.json` and `runs.jsonl` copies with their sha256s, and the sealed
   path. It must read `Verdict: ACCEPTED`.
4. **Fill the spec's `noise_floor.seven`** from `COPY_RECORD.json`'s `spec_fields` (now nine fields, including the
   four new ones). The other signature fills follow as already planned. Re-render the note's key lines
   (`g5_tasl.py key-lines`): `t1_table_readings` and the spec sha256 have changed. Then sign the note and launch.

**Autoresearch under G5-ARPEND A** (after the launch, before autoresearch's first G.5 job, as already planned):
- The same copy step with `--kind ar`, then commit and review as above. The review must also name the `ASSEMBLY.json`
  and `runs.jsonl` copies with their sha256s.
- The completion record cites the summary copy as before; no new line is needed.
- The switch STOPs autoresearch's jobs until the run copies are on main and so reviewed.

**After the G.5 runs:**
1. **The train/dev assembly** after R1-T1-LABELS-UNSEAL (`g5_tasl.py assemble --stage traindev …`). σ_node is read
   from the committed copies. A non-zero D9 count is a STOP.
2. **`g5_noise.derive` on the copies.** It needs the train/dev row, which cites the summary copies, so it runs after
   R1-T1-LABELS-UNSEAL is on PLAN. Under D6 A it reads only committed files. It is a CPU step on any clean checkout of
   main and needs no host access. There is no CLI. For example:
   `python -c "import sys; sys.path.insert(0, 'sweep2/t1_tasl'); import json, g5_assemble as A, g5_noise as N, g5_tasl as S; from pathlib import Path; from r1.c3 import release as R; spec = S.load_spec(Path(A.SPEC_REL)); rec = N.derive(spec, R.release_row('T1', 'traindev'), ar_record=A.default_ar_record(spec, Path(A.SPEC_REL))); print(N.write_record(rec, 'docs/r1/reports/<dir>/T1_NOISE_<date>.json'))"`.
3. **The record:** commit it, have it reviewed, and cite its sha256 in the arms-frozen record. Build the gate input's
   `noise` with `merge_noise(dataset.noise_table(<pinned T0 source>), builder_noise(…))`.

## 4. The launch row check

`g5_tasl.launch` now calls `plan_row("R1-T1-FEAT-DECISIONS", read_main, terms=("D6 A", "D6-σ B", "D8 A", "D9 B"))`
after the decisions and E4 row checks. It adds the row to the rows the launch binding checks on `origin/main`.

**How `plan_row` matches.** The row's line must occur exactly once on published main's PLAN, read as UTF-8. Each term
is matched literally in the row text without its id cell, and may not run on into a letter or digit. So:
- `D6-σ B` needs the ASCII hyphen-minus and the Greek small sigma U+03C3.
- `D6-sigma B`, `D6–σ B` (en dash), `D6‑σ B` (U+2011), `D6-ς B`, `D6-Σ B`, `D6 σ B` and `D6-σ B2` all STOP, as do
  `D6 AB`, `D6A` and `D9B`. The tests check each of these.
- A wording mismatch fails closed: the launch STOPs, and the terms (`T1_FEAT_TERMS`) or the row are adjusted before
  the launch.

**What the coordinator gave and what was checked.** The coordinator's instruction named R1-ARMS-DECISIONS among the
rows the launch checks. It does not:
- The switch checks the spec's `decisions_row` and `e4_amendment_row` with `plan_row`. These are filled at the
  signature with R1-G5-DECISIONS-2 and R1-G5-MEM-E4.
- It also checks the fixed `PLAN_ROWS` (existence only, through the launch binding).
- R1-T1-FEAT-DECISIONS is added as a constant, since its id is fixed, not as a spec field.

`D8 A` is a term beyond the three examples given. D8 A sets `memory_on`, which is table bytes, so the launch checks it
too. Drop it if the author prefers.

**On this checkout's PLAN the row is absent, so the launch STOPs until it is published.**
`test_t1_feat_decisions_row_on_this_checkouts_plan` passes before and after publication. Before, it expects the STOP.
After, it requires the published row to pass the term check. `test_main_decision_rows_pass_the_switch_row_checks`
(the real PLAN) still passes.

## 5. The frozen preregistration's wording

PRE-DELTA (sources, both options) reads: "T0 δ_n and σ_node from the pinned noise source … by `dataset.noise_table`'s
definitions (σ_node: median sd_joint over material edits; δ_n: D18); T1 from each node's sealed G.1b summary on H200
(path and sha256 recorded in the T1 train/dev release row, before any training, since σ_node sets the soft-label width
and g)". REL-T1-G1B already reads "on H200" as "on the T1 host of R1-T1-HOST-TASL", copied out of the sealed tree.

**The definition: now literal for both tiers.**
- Under D6-σ A, T1 used the summary's `sigma_joint`. "By `dataset.noise_table`'s definitions" was then read as
  attaching to the T0 clause only, a reading that was reviewed but never signed.
- Under D6-σ B, T1's σ_node follows `dataset.noise_table`'s σ_node definition exactly, and δ_n is D18 as before.

**The source: not literal, and needs the author's reading in the row.** PRE-DELTA says T1 comes "from each node's
sealed G.1b summary". The summary carries no median paired sd, so neither δ_n (D18; true under D6-σ A as well) nor
σ_node by T0's definition can be read from summary fields. Both are computed from the G.1b run's `runs.jsonl`, which
the summary binds by sha256 through `ASSEMBLY.json`. The train/dev row still records each summary's path and sha256,
as PRE-DELTA requires, and that pins the run copies. Whether "from each node's sealed G.1b summary" covers values
derived from the run the summary binds is an author reading. Suggested wording for R1-T1-FEAT-DECISIONS: PRE-DELTA's
T1 clause reads "from each node's G.1b summary and the run it binds by sha256 (REL-T1-G1B copies)". The
preregistration itself is not changed and must not be.

**Other texts that are now stale.** They are not edited here; they belong to their own units:
- **G.5 draft** (`proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md`):
  - §3 states "σ̂_node is the G.1b `joint` σ … open under decision D6-σ";
  - §5's rendered note block shows the old `t1_table_readings` line and the old spec sha256;
  - the table of PENDING values says the readings line is open under D6-σ.
  
  Under D6-σ B the soft-label width s = σ̂_node/√K_label uses T0's σ_node definition.
- **T1 release rows draft** (`g5_code_20261123/T1_RELEASE_ROWS_DRAFT_20261123.md`), "Which summaries": "D21 verdict
  and positive `sigma_joint` (STOP 5)". It now reads: a qualifying D21 verdict, and a positive σ_node by T0's
  definition from the copied run.
- **ARMS-T1FEAT report** (`T1_FEATURES_20261123.md`), §3 and §5: "the 3b-2 default … is not changed here",
  "`builder_noise` does not use it", "not built". These are superseded by this report; that report is left as
  reviewed.

## 6. Tests

Targeted runs, one file at a time (Python 3.12, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, `PYTHONDONTWRITEBYTECODE=1`, a
private `TMPDIR`; LightGBM from `/tmp/armsdev/pylib` for `test_t1_features.py` only):

| File | Base `14f19a09` (collected) | Tip |
|---|---|---|
| `r1/tests/test_t1_g5_tasl.py` | 109 | 113 passed |
| `r1/tests/test_t1_g5_seal.py` | 32 | 33 passed |
| `r1/tests/test_t1_features.py` | 19 | 28 passed |
| `r1/tests/test_t1_g5_job.py` | — | 37 passed |
| `r1/tests/test_t1_tasl_g1b.py` | — | 45 passed |
| `r1/tests/test_gate_input_builder.py` | — | 41 passed |
| `r1/tests/test_c3_release.py` (release step, `release_checks`) | — | 43 passed |
| `r1/tests/test_c3_sweep2_audit.py`, `test_c3_sweep2_d4b.py` (`release_checks` users) | — | 28, 75 passed |
| `r1/tests/test_c3_features.py`, `test_c3_dataset.py` | — | 9, 4 passed |

**What the new and changed tests check:**
- **Copy binding (D6 A).** `test_rel_t1_g1b_copy_seven_passes_the_switch_check` checks:
  - both copies are byte-identical, the sha256s are recorded, and the record's spec fields and review needles are
    right;
  - `check_seven_copy` passes on them;
  - it STOPs on a missing run copy, a changed run copy, a review that omits a run sha256, and spec fields that name
    other copies.

  `test_rel_t1_g1b_copy_refusals_and_ar` covers autoresearch's copy, and `test_m5_launch_under_arpend_b` checks the
  run copies and review at an autoresearch job start under G5-ARPEND B.
- **Seeds 7001–7010 and sealed paths.**
  - `test_rel_t1_g1b_copy_d6a_refusals` covers the copy step: seeds 7001, 7006 and 7010 in `train_seed`,
    `split_seed` and `seed`, with nothing written; also a paired-count mismatch, a missing `n_edits`, a symlinked
    `runs.jsonl` and an `r1_sealed` sealed root.
  - `test_noise_refuses_a_g1b_run_with_an_audit_seed` covers every read, in `derive` and in `noise_by_node` (four
    seed fields); 7000 and 7011 pass.
  - `test_noise_refuses_an_r1_sealed_copy`: an `r1_sealed` path is refused before any read.
- **σ_node equality (D6-σ B).**
  - `test_noise_d18_and_t0_sigma_match_e1_report_and_are_bound_to_the_copy`: σ_node equals `noise_table`'s rule on
    `e1_report`'s edits; it is not `sigma_joint`; it equals `noise_by_node`'s value; there is no absolute path; the
    schema is `/2`.
  - `test_t0_sigma_equals_dataset_noise_table_on_a_t0_node`: g5_noise's σ_node, δ_n and median equal
    `dataset.noise_table`'s own output on `e1_report`'s summary of the same synthetic run. Three runs are used,
    including one with sd 0.
  - `test_noise_refusals`: `t1_sigma_node` missing or other; spec copy fields other; a changed run; a missing copy;
    counts; `n_edits`; σ_node 0; `run_dirs` other than the copy directory.
- **The table and the gate input end to end.**
  - `test_t0_plus_t1_gate_input_with_the_frozen_builder`: rows, `sigma_cmp`, soft labels and `build.json` carry T0's
    σ_node. The frozen builder accepts the record, and refuses a record that carries `sigma_joint`.
  - In `test_t1_g5_seal.py`, `test_assembly_traindev_then_test` asserts σ_node = 2⁻⁶ (exact, from dyadic synthetic
    runs), not `sigma_joint`.
- **D9 B.**
  - `test_d9_b_traindev_stage_stops_on_a_non_zero_count`: three cases; the exact fixed reason; nothing is written.
  - `test_d9_b_flag_mismatch_of_an_executed_row_the_fields_call_seen_stops`.
  - `test_d9_b_test_stage_and_integrity_check_stop_too`: the test stage STOPs before the evaluation block, and so
    does `verify_evidence`.
  - The two tests that relied on counts being reported were changed: the base fixture now gives 0/0, and the
    converse-direction test now expects the STOP.
- **The launch row check.**
  - `test_t1_feat_decisions_row_is_checked_at_launch` on fixture PLANs: the row absent, twice, each term missing or
    misspelt (including the Unicode variants of §4), and present.
  - `test_t1_feat_decisions_row_on_this_checkouts_plan`, on the real PLAN.
- **The spec.** `test_spec_carries_the_t1_feat_decisions_fields` and
  `test_launch_validation_wants_the_run_copies_beside_the_summary_copy`.

## 7. Full `r1/tests` suite: base and tip

Same invocation as the G.5 merge unit (`G5_CODE_MAIN_MERGE_20261123.md`): `/tmp/tgport312/bin/python -m pytest -q -p
no:cacheprovider -rfE r1/tests`, with `AR_HARNESS_ROOT` set to a harness checkout at `c025f89a`,
`PYTHONDONTWRITEBYTECODE=1` and a fresh, emptied `TMPDIR` per run. LightGBM was not on the path, as in that unit. The
two runs were one after the other, never in parallel.

| Run | Commit | Result |
|---|---|---|
| base | origin/main `14f19a09` (clean detached worktree, removed afterwards) | 58 failed, 3 errors, 3778 passed, 197 skipped |
| tip | FULLSUITE_TIP_RESULT | FULLSUITE_TIP_COUNTS |

The failure lists (FAILED and ERROR node ids, sorted) are `FULLSUITE_BASE_14f19a09.txt` and `FULLSUITE_TIP.txt`
beside this report. FULLSUITE_COMPARISON. The 61 base entries are the same set as the earlier G.5 runs'
(`FULLSUITE_BRANCH_baf6be5d_FAILED.txt`): environment-dependent tests on this desk.

## 8. Open points for the author or the coordinator

1. **The row's wording.** The launch requires `D6 A`, `D6-σ B`, `D8 A` and `D9 B` literally (§4). If R1-T1-FEAT-DECISIONS is
   worded differently, adjust `T1_FEAT_TERMS` (or the row) before the launch.
2. **PRE-DELTA's "from each node's sealed G.1b summary"** (§5): an author reading in the row is suggested, so that
   computing σ_node and δ_n from the run the summary binds is stated.
3. **Stale texts** (§5): the G.5 draft's σ_node paragraph and note block, and the T1 release rows draft's STOP 5
   wording. The draft owner should re-render the note block with `key-lines` after the spec fill.
4. **The note's `noise_floor` key line** is unchanged. It names the summary and gate copies with their sha256s, not
   the run copies. The note binds the spec sha256, which carries the four new fields, and the run copies are pinned
   by the summary's sha256. Adding them to the line would change the draft's note format, so it was not done.
5. **The data in git.** The `runs.jsonl` copies (both G.1b runs) will be committed under `docs/r1/reports/`.
   - Per the harness `trackg/noise_floor.py` at `c025f89a`, they hold validation metrics only. Its docstring reads:
     "rows carry the validation metric only; the sealed test value stays in the run record and is not copied".
   - `ASSEMBLY.json` carries job metadata (sealed attempt paths, GPU uuid, timing).
   - The copy review should confirm the seeds (the copy step enforces "not in 7001–7010"; it does not require every
     seed to be in the G.1b blocks) and the size.
6. **The D9 reason** carries the node and the count names but not the counts. The counts remain in `build.json` of
   any table that exists, where they are always 0.
7. **`g5_noise.derive` has no CLI.** §3 gives a one-line call. Whether a CLI subcommand is wanted is open (not
   built).
