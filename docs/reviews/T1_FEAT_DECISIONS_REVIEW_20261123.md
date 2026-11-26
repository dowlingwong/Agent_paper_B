Reviewed base: origin/main `14f19a09`; accepted at `5cb82fa7fc3c437938b3db46fee2e4a32968740f`

# Independent review record — R1-T1-FEAT-DECISIONS before the G.5 launch: D6 A (G.1b run copies), D6-σ B (T1 σ_node by T0's definition), D9 B (assembly STOP on non-zero counts)

**Unit.** On `mac-t1-feat-decisions-20261123` (on origin/main `14f19a09`): `sweep2/t1_tasl/g5_relcopy.py` (D6 A: the reviewed REL-T1-G1B copy step also copies each G.1b run's `ASSEMBLY.json` and `runs.jsonl` beside the summary copy, after `refuse_sealed` on every source before any read, regular files only, the summary's `assembly_sha256` and ASSEMBLY's `runs_sha256` bound, counts checked for qualifying verdicts (a non-qualifying verdict without counts passes through), and a seed guard refusing any `*_seed` in 7001–7010; written through a sibling temp directory renamed into place only after verification, from the checked bytes); `g5_tasl.py` (spec `noise_floor.seven`/`ar` gain `assembly_copy`, `assembly_sha256`, `runs_copy`, `runs_sha256`; `run_copies` at every job start; `noise_precheck` at launch, before any job: σ_node and δ_n finite and > 0 from the copies on main; the launch requires R1-T1-FEAT-DECISIONS on main naming `D6 A`, `D6-σ B`, `D8 A`, `D9 B`, matched literally with both boundaries); `g5_noise.py` (`node_noise` core with finiteness checks; record `g5_t1_noise/2` taking its values from `noise_by_node`); `g5_assemble.py` (`noise_by_node` computes σ_node by T0's `dataset.noise_table` definition from the bound copies under spec `noise_floor.t1_sigma_node: "t0_definition"`; the `sigma_joint` path removed, `sigma_joint` still reported; `derive` STOPs on any non-zero `raw_state_missing` or `flag_mismatch` at train/dev, test and `verify_evidence`); `g5_tasl_spec.json` (unsigned; sha256 changes); tests in `test_t1_g5_seal.py`, `test_t1_features.py`, `test_t1_g5_tasl.py`; report `docs/r1/reports/arms_t1feat_20261123/T1_FEAT_DECISIONS_20261123.md`. `gate.py`, `gate_input_builder.py`, `release.py`, `release_checks.py`, `features.py`, `dataset.py` and the preregistration are unchanged. Authority: the user's message of 23 Nov 2026 (17:02) stating the decisions of the author row R1-T1-FEAT-DECISIONS (to be published on main); the ARMS-T1FEAT A report §5.

**Full `r1/tests` suite** (`pytest -q -p no:cacheprovider -rfE r1/tests`, `AR_HARNESS_ROOT` at `c025f89a`, fresh TMPDIR, LightGBM not on the path, runs sequential): base `14f19a09` 58 failed, 3 errors, 3778 passed, 197 skipped; author's code tip `94c54f58` 58 / 3 / 3792 / 197; accepted tip `5cb82fa7` (rerun by the coordinating session after acceptance) 58 / 3 / 3800 / 197. The failure lists `FULLSUITE_BASE_14f19a09.txt`, `FULLSUITE_TIP.txt` and `FULLSUITE_TIP_5cb82fa7.txt` are byte-identical (61 entries): zero new failures.

**Process.** One independent reviewer, read-only, own detached worktrees, synthetic data only. Round 1 found one major (the copy step refused any summary containing a node that failed fixed-seed determinism, whose verdict `g1b_lib.summarise` writes without counts, blocking the whole seven-node copy and so the launch) and seven minors; round 2 accepted with three nits.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `fa31b1548` | NOT ACCEPTED (M1; minors m1–m7) |
| 2 | `5cb82fa7f` | ACCEPTED (nits n1–n3) |

**Open items.** For the author and whoever reviews and publishes R1-T1-FEAT-DECISIONS: the row must contain the strings `D6 A`, `D6-σ B` (ASCII hyphen, Greek σ U+03C3), `D8 A` and `D9 B`, or every G.5 launch STOPs; the row should state the PRE-DELTA reading (T1 σ_node and δ_n come from the `runs.jsonl` the sealed G.1b summary binds by sha256), which is deliberately not a launch term. Stale texts not edited here: the G.5 draft (§3 σ̂_node paragraph, §5 note block, old spec sha256), `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md:63-64` and its `reports/g5_code_20261123/` copy ("positive `sigma_joint` (STOP 5)"), and the ARMS-T1FEAT report's "not built" statements. The note's `t1_table_readings` line must be re-rendered (the `sigma_cmp` text changed). T0's `dataset.noise_table` has the same non-finite gap as m7 (reported, not changed). Nits n1–n3 (rename onto an empty directory, empty parents left on a STOP, a hidden partial directory after a hard kill). Cluster order: publish the row and merge; on the T1 host `g5_tasl.py rel-copy … --kind seven`, commit the five files with an independent review; fill the spec's `noise_floor.seven`, re-render the key lines, sign, launch; after R1-T1-LABELS-UNSEAL, the assembly and then `g5_noise.derive` on the committed copies.

## Round 1 (`fa31b1548`)

> Reviewed base: fa31b1548 (mac-t1-feat-decisions-20261123; base 14f19a09)
>
> ## Summary
> Not accepted, because of one blocking defect in the D6 A copy step (M1). Everything else checks out apart from minor points.
>
> ## What I checked and found correct
> - **Files changed.** `git diff --stat 14f19a09 fa31b1548` touches exactly the 11 files the report lists; `gate.py`, `gate_input_builder.py`, `release.py`, `release_checks.py`, `features.py`, `dataset.py` and the preregistration are untouched; the spec sha256 change is disclosed.
> - **D6-σ B matches T0's definition.** `g5_noise.edit_stats` and `node_delta` agree line by line with `r1/noise/e1_report.summarise` and `r1/c3/dataset.noise_table`: paired keys (`train_seed`, `split_seed`), success and metric not None, last write wins; at least 3 paired seeds; sd ddof 1; se = sd/√n; resolved |Δ| > 2se or Δ ≠ 0 when se = 0; material also |Δ| ≥ 0.002; median over material edits, falling back to all edits with an sd.
> - **σ_node is one value end to end**: `noise_by_node` → table rows' `sigma_node`/`sigma_cmp`, `featurize_ledger(sigma_node=…)` (`recorded_gain_z`), the soft-label width, `build.json`, `g5_noise.derive`. The frozen builder's σ_node check passes (exact float equality after the JSON round trip); a record carrying `sigma_joint` is refused.
> - **Edge cases stop**: no edit with an sd STOPs in `node_delta`; zero or non-finite σ_node STOPs in `noise_by_node`.
> - **Binding chain sound**: `g1b_lib.summarise` writes `assembly_sha256`, kept by `g1b_tasl.summarise`; ASSEMBLY.json carries `runs_sha256`; re-checked at the switch (`run_copies`, published main, review naming both files), in train/dev and test assembly, and in `verify_evidence`. A swap between launch and release breaks a sha256, so leaving `G5_PATHS`/`g5_integrity` unchanged is safe. Run copies are read once into memory, checked and written from memory.
> - **Seed guard complete**: harness `noise_floor.row_of` at `c025f89a` and `2d09f9a9` writes only `train_seed` and `split_seed` as integer seed fields (`run_id` repeats them as text); the guard stops before anything is written.
> - **Nothing label-bearing copied**: runs.jsonl validation metrics only; ASSEMBLY.json job metadata (absolute sealed G.1b paths and GPU uuids disclosed).
> - **D9 B**: STOPs at train/dev, at test (before the evaluation block is written) and in `verify_evidence`; fixed message, no numbers. The reshaped ledgers did not weaken earlier tests; old shapes drive the D9 tests.
> - **Launch row check**: literal, σ as U+03C3; variant tests stop; the row is absent from `14f19a09` so the launch STOPs until published; "D8 A" is in the user's list.
> - **Full-suite lists**: `FULLSUITE_BASE_14f19a09.txt` and `FULLSUITE_TIP.txt` byte-identical (61 lines, sorted), also identical to the G.5 merge unit's list; the invocation matches; +14 passes match the new tests.
> - **Targeted tests** (one at a time, all passing): test_t1_g5_tasl 113; test_t1_g5_seal 33; test_t1_features (with lightgbm) 28; test_t1_g5_job 37; test_t1_tasl_g1b 45; test_gate_input_builder 41; test_c3_release 43; test_c3_sweep2_audit 28; test_c3_sweep2_d4b 75; test_c3_features 9; test_c3_dataset 4.
>
> ## Findings
> **M1 (blocking) — `sweep2/t1_tasl/g5_relcopy.py:96-102` (`check_source`).** The new loop STOPs if any node's verdict lacks `n_edits`/`paired_joint_n`, but `sweep2/g1b/g1b_lib.py` `summarise` (~805-808) writes exactly that shape for a node that failed determinism or was stopped by the harness (`{"qualifies_D21": False, "reason": "fixed-seed determinism failed", "determinism", "divergent"}`). If one non-TASL-7 seven-node node (e.g. `mlab_imdb`) fails determinism, `rel-copy --kind seven` STOPs for the whole summary and the launch cannot proceed without a code change; likewise a non-deterministic AR run can no longer be copied to record `d21_verdict: does_not_qualify`. Reproduced on the `sealed_g1b_run` fixture; the base step would have copied it. Expected, not hypothetical (G.5 draft item 5 ~542; XC-NONDET A). `test_rel_t1_g1b_copy_d6a_refusals` locks the defect in. Fix: check the counts only for `qualifies_D21: true` verdicts (or where `n_edits` is present); `node_delta` re-checks on every read of a cited node.
>
> ## Minor
> - **m1** `g5_relcopy.py` ~78 vs ~86: the summary is read before `refuse_sealed`; the report claims the check precedes every read. Move it before the read.
> - **m2** `copy_summary` (~136-165): a STOP after writing starts (sha re-check, gate copy, OSError) leaves a partial `<dest>/` that blocks a rerun; "nothing written on a STOP" holds only inside `check_source`. Pre-existing: the recorded summary sha256 comes from a third read, and `copyfile` reads again (mitigated by the switch's chain check).
> - **m3** Stale list incomplete: `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md:63-64` still says "positive finite `sigma_joint`; otherwise STOP 5"; only the `reports/g5_code_20261123/` copy is flagged.
> - **m4** The PRE-DELTA reading is presented correctly but not enforced: `T1_FEAT_TERMS` does not require it; add a term or make it an explicit item for the row's reviewer.
> - **m5** `g5_tasl.py:950-963` `plan_row`: no check on the preceding character, cannot see negation ("D6 A not taken" passes); state the limit next to "fails closed".
> - **m6** The launch does not check σ_node > 0 by T0's definition; a qualifying node with σ_node = 0 would spend its GPU campaign and STOP only at assembly. The run copies are on main at launch, so a pre-check is cheap.
> - **m7** (pre-existing, as in `noise_table`) A NaN median gives δ_n = 0.002 silently; worth a finite check in `node_delta`.
>
> ## Report accuracy
> Accurate apart from m1–m3.
>
> ## Cleanup
> Worktree removed; scratch in `/tmp/t1fdrev/_to_delete/`. Nothing committed or pushed; no sealed data, labels or evaluation values read.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`5cb82fa7f`)

> Reviewed base: 5cb82fa7f (on fa31b1548)
>
> ## Summary
> Accepted. All round-1 findings are fixed. Nothing blocking remains; three small nits are listed at the end.
>
> ## Scope check
> `git diff --stat fa31b1548 5cb82fa7f` shows 8 files: `sweep2/t1_tasl/{g5_assemble,g5_noise,g5_relcopy,g5_tasl}.py`, `r1/tests/test_t1_{features,g5_seal,g5_tasl}.py` and the report. Nothing else changed, so rerunning the full suite on the final tip is sufficient.
>
> ## The fixes, checked
> **M1 fixed.** `check_source` skips a node only when `qualifies_D21 is not True` and both counts are missing. A qualifying verdict always goes through the count check (probe: `{"qualifies_D21": true}` without counts STOPs, as does one count alone). A passed-through node is `does_not_qualify` everywhere (`is True` throughout), STOP 5 at the switch, and never read by `noise_by_node` (cited qualifying nodes only; `node_noise` requires counts). The seed guard still covers its runs (`g1b_rows` reads every record). My round-1 scenario now copies with `d21_verdict: does_not_qualify`.
>
> **m1 fixed.** `_refuse_sealed` runs on the summary, ASSEMBLY.json, runs.jsonl and crosscheck_gate.json before any is opened; only lstat symlink checks come earlier.
>
> **m2 fixed.** `mkdtemp(dir=target.parent)` and `os.rename` in the same directory (same filesystem, atomic); `dest` still goes through `_rel_ok` (probe: `docs/r1/reports/../../x` refused); symlink checks on `target` and its parents run first; cleanup is `shutil.rmtree(work)` of the step's own temp dir; `target.exists()` checked before writing and before the rename; every file from the checked bytes, summary sha256 = `sha(raw)`. Probe: a STOP injected while writing runs.jsonl leaves nothing; a rerun works.
>
> **m3, m4 fixed.** The proposals draft is listed as stale; the PRE-DELTA reading is an explicit item for the row's reviewer with a sound reason.
>
> **m5 fixed.** `(?<![A-Za-z0-9])` preceding boundary; the negation limit stated; real-PLAN row tests pass.
>
> **m6 fixed.** `noise_precheck` runs in `launch` after `check_seven_copy` (or `check_ar_record` / `check_g1b_copy`) and STOP 5, before the freeze wait and any job (the runner is never called). It reads only through `read_main`. It uses `node_noise` and `check_usable`, the same core as `node_delta` and `noise_by_node`, on bytes pinned through the summary. The new launch-context entry is unchecked by `g5_job`; no side effects.
>
> **m7 fixed.** `node_noise` STOPs on a non-finite paired sd, median or σ_node; `check_usable` also requires δ_n finite and > 0. Finite values byte-identical: `fa31b1548`'s `node_delta` vs the new one, `json.dumps(sort_keys=True)` on four synthetic runs including sd 0, identical. `test_t0_sigma_equals_dataset_noise_table_on_a_t0_node` and the e1_report tests pass. T0's gap reported, not changed.
>
> ## Targeted tests at `5cb82fa7f`
> test_t1_g5_tasl 115; test_t1_g5_seal 36; test_t1_features (with lightgbm) 31 (2 numpy warnings from the deliberate ±inf inputs); test_t1_g5_job 37; test_t1_tasl_g1b 45; test_gate_input_builder 41; test_c3_release 43.
>
> ## Nits
> - **n1** On Linux `os.rename` onto an empty directory succeeds; an empty `<dest>` created between the second `exists()` and the rename would be replaced silently (nothing lost).
> - **n2** Parent directories created by `mkdir(parents=True)` are not removed on a STOP (at worst an empty directory).
> - **n3** A hard kill would leave a hidden `.<name>.partial-*` directory under `docs/r1/reports/`, visible as untracked.
>
> ## Cleanup
> Worktree removed; scratch in `/tmp/t1fdrev/_to_delete/`. Nothing committed or pushed; no sealed data, labels or evaluation values read.
>
> VERDICT: ACCEPTED

---

Code-Commit: 5cb82fa7fc3c437938b3db46fee2e4a32968740f
Verdict: ACCEPTED

Accepted at `5cb82fa7`.
