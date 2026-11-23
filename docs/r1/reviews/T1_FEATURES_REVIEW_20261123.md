Reviewed base: `30e2d51a` (the G.5 code on main 000ac3b1), merged forward to `2582c898` (READY 91's code); accepted at `a5715142`, confirmed at `b033050e0e48feda04e89d6a9a62c28c49d85169`

# Independent review record — ARMS-T1FEAT A: featurizer-v3 features for the G.5 (T1) table rows, the T1 noise derivation (δ_n, D18) and the suite-name mapping

**Unit.** On `mac-t1-features-20261123`: `sweep2/t1_tasl/g5_features.py` (the T1 featurizer: the v3 field list, a test pinning it to `r1.c3.features.FEATURES`; T1 node codes 11–18 after T0's 0–10, the tier carried by the node code; `SUITE_NAMES` and `tier1_suites()`; 18 fields with no T1 source as NaN (numeric) or −1 (categorical); four code-state counterparts; `budget_frac_left` in manager calls; `memory_on` 1.0 for `history` as a declared mapping), `sweep2/t1_tasl/g5_noise.py` (δ_n = D18, max(0.002, 0.25 × median paired sd), from the G.1b run's `runs.jsonl` with `e1_report`'s definitions, bit-identical, bound by sha256 copy → `assembly_sha256` → `ASSEMBLY.json` → `runs_sha256` → `runs.jsonl`, every read through a copy of `analysis_guard.refuse_sealed`; also reports σ_node by T0's definition for decision D6-σ, unused by the builder), changes to `g5_assemble.py` (features filled per ledger and re-derived byte-identically at the test stage; a not-run duplicate's code state from the top level, then the diff provenance, then the parent for a no-op; `build.json` adds `featurizer`, each node's `gate_suite`, `raw_state_missing` and `flag_mismatch` counted in both directions) and `g5_tasl.py` (`IMPORT_SOURCES`), `r1/tests/test_t1_features.py` (19) and the report `docs/r1/reports/arms_t1feat_20261123/T1_FEATURES_20261123.md`. `r1/c3/features.py`, `dataset.py`, `gate.py`, `gate_input_builder.py` and the preregistration are unchanged; the T0 featurization is byte-identical (golden `ffe94da0…97a1`). Authority: R1-ARMS-DECISIONS (ARMS-T1FEAT A) on main `89899f76`; the user's queue of 23 Nov 2026 (14:02), item 4.

**Process.** One independent reviewer, read-only, synthetic data only (no secrets, sealed data, labels or evaluation values). Round 1 found no blocking issue and four majors (the `memory_on` mapping for `history` undeclared; the T0/T1 σ_node difference presented as a note, not a decision; decisions dated to the assembly instead of the G.5 launch; the assembly stopping on real not-run duplicates, whose code state the harness writes only in the diff provenance) and six minors. Round 2 accepted with two optional points; both (a converse `flag_mismatch` test, an `r1_sealed` refusal test) were added with the merge of READY 91's `2582c898` and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `2530d8e6` | NOT ACCEPTED (M1–M4; minors m1–m6) |
| 2 | `a5715142` | ACCEPTED (optional m1–m2) |
| 3 | `b033050e` | ACCEPTED (confirmation) |

**Open items (author decisions, report §5).** Before the G.5 launch (the features are table bytes and `sweep2/t1_tasl` is frozen from launch to the T1 test release), with any code on main: D1 NaN/−1 for the 18 fields without a T1 source (review: accept); D2 the four code-state counterparts (accept); D3 `budget_frac_left` in manager calls (accept); D4 what `invalid_so_far` counts (accept); D6-σ the T1 σ_node definition (A `sigma_joint` as built, the 3b-2 default; B T0's definition, which needs a `noise_by_node` change and a spec field on main before launch); D8 `memory_on` for `history` (1.0 as built, or NaN); D9 `flag_mismatch` as a count (as built) or a STOP. D5 is decided by R1-ARMS-DECISIONS. D6 the source of T1 δ_n (A, recommended: a reviewed copy of `runs.jsonl` and `ASSEMBLY.json` beside the summary copy, with an author row amending REL-T1-G1B's copy list; B derive on the host against the sealed tree; C a proxy, not D18, rejected unless the preregistration is amended), before the gate-run noise is built (before launch under D6-σ B). D7 a T1 prompt for A5 (`serialize.py` handles only T0 structured edits): without a T1 A5 input `gate_input_builder.TEST_SERIES` keeps T1 out of the read; before the arms-frozen record. The arms-frozen record has no T1 noise slot (`arms_freeze.check_record` pins `noise_source` to the T0 file). Cluster: on the real table `raw_state_missing` and `flag_mismatch` should be 0 for every node.

## Round 1 (`2530d8e6`)

> Reviewed base: 2530d8e6aa6c39fda0422c4013e986f90b86884d (one commit on 30e2d51a6f74c9562943c23a5e4c35a1bbd92a1b; it merges cleanly with origin/main 89899f76)
>
> ## Summary
>
> The code does what the instruction asks, and every claim I could check holds:
> - **No T0 regression.** `r1/c3/features.py`, `dataset.py`, `gate.py`, `gate_input_builder.py`, `arms.py`, `r1/noise/e1_report.py` and the preregistration are byte-identical to 30e2d51a. These r1 files also match origin/main. `FEATURIZER_VERSION` is still `c3_features/v3`. I recomputed the T0 golden at both commits and got `ffe94da0…97a1` each time.
> - **The T1 features are causal.** They read only the lines of steps < n, plus step n's pre-run code-state hashes. The leakage test is not vacuous.
> - **Node codes, suites and missing fields are right.** The T1 codes are 11–18. The suite map is complete against `gate.SUITES` and against all eight node specs (I checked the harness at c025f89).
> - **The missing-value convention is safe.** There are 18 fields with no T1 source. NaN and −1 pass through `arms.feature_matrix` and LightGBM. They never reach the gate input: the builder uses features only for the A2 fit, so the gate's refusal of NaN is never triggered.
> - **The noise derivation is D18.** δ_n is computed exactly as `dataset.noise_table` and `e1_report` define it, with the same seed ordering, so it is bit-identical. The sha256 chain is sound: summary copy → `assembly_sha256` → ASSEMBLY.json → `runs_sha256` → runs.jsonl, plus the count checks against `n_edits` and `paired_joint_n`. σ_node is the table's value by construction. The builder gets the right form.
> - **The assembly change is sound.** The test-stage re-derivation is still byte-identical. The new build.json fields carry no label or evaluation information. Both modules are in `IMPORT_SOURCES` and under `G5_PATHS`.
>
> **Test runs** (one file at a time, with AR_HARNESS_ROOT=/tmp/pb/wt/t1h):
>
> | File | Result |
> |---|---|
> | test_t1_features | 15 passed |
> | test_t1_g5_seal | 30 passed |
> | test_t1_g5_job | 23 passed |
> | test_t1_g5_tasl | 107 passed |
> | test_c3_features | 9 passed |
> | test_gate_input_builder | 41 passed |
> | test_c3_dataset | 4 passed |
>
> The author's skips and the one dataset failure come from their environment having no harness checkout. Without AR_HARNESS_ROOT, `test_build_replays_without_violations_and_di_candidates` fails identically at 30e2d51a and at the tip ("historical harness object 411c6054…:nodes/digits_mlp/train.py unavailable"). With the harness it passes on both.
>
> What stops acceptance is a gap in the decision list and its timing, plus one real defect the author found but left unscheduled (see M4). There is no blocking defect in the unit's own code.
>
> ## Findings
>
> No B findings.
>
> **M1 — `memory_on` = 1.0 for `history` is an unlisted semantic choice.**
> - Where: `g5_features.featurize_ledger` (`memory_mode != "none"`) and report §2, which labels it "same as T0".
> - Problem: R1-G5-MEM-E4 (on main) says T1's `history` mode is "different from both T0 modes". Mapping it to 1.0 treats it as T0's `append_only_summary`. That is a choice about frozen table bytes, and it is not in D1–D7.
> - Failure scenario: the author signs D1–D7 without knowing this choice exists. In the leave-one-suite-out folds the held-out nodes have unseen node codes, so `memory_on` decides which T0 rows they get grouped with.
> - Fix: add a D8 (1.0 as built, or NaN) and correct the "same as T0" label.
>
> **M2 — The T0/T1 σ_node difference is presented as a note, but it is a decision that this unit makes cheap.**
> - Where: report §3, "Two things to note", and `g5_noise`.
> - Problem: PRE-DELTA's "by `dataset.noise_table`'s definitions" grammatically attaches to the T0 clause, so reading T1's σ_node as `sigma_joint` is a reviewed reading, not a signed one. σ_node scales `recorded_gain_z`, the soft-label width and g, all in table bytes. `g5_noise` now reads the bound runs.jsonl, so T0's definition (median `sd_joint` over material edits, falling back to all edits) can be computed for T1 at no cost.
> - Failure scenario: one joint A3 model sees `recorded_gain_z` and labels in a unit that differs between tiers by a node-dependent factor of about √(2(1−ρ)), and nobody signed that.
> - Fix: put it to the author as a decision, together with D6: σ_node = `sigma_joint` as built, or T0's definition from the same bound runs.jsonl. The 3b-2 code is not changed here.
>
> **M3 — The decision deadline is wrong.**
> - Where: report §5, "must be settled before the G.5 train/dev assembly".
> - Problem: by the 3b-2 report §5 item 6, `sweep2/t1_tasl` is frozen on main from the G.5 launch until the T1 test release, and this report's own §6 item 4 says the same. So D1–D4, D8 and the σ_node decision must be final, and the code on main, before the launch, not before the assembly.
> - Fix: say "before the G.5 launch".
>
> **M4 — The assembly path is tested only on an unrealistic fixture, and the duplicate defect is left without an owner.**
> - Where: `test_assembly_rows_carry_features_and_re_derive_byte_identically` asserts `flag_mismatch == 12` and `raw_state_missing == len(rows)`. The defect is in `g5_assemble.node_rows`: `cand = run.get("code_state_sha256") …`.
> - Problem: the 3b-2 fixture's duplicate repeats the incumbent's state (the harness would call that inert), puts not-run states at the top level, and has no raw states. I probed the assembly with realistic records: code state only in the `diff` provenance, as `runner.run` writes it, with the duplicate repeating an evaluated, non-incumbent state. The assembly STOPs at the first real duplicate ("a duplicate without its code state").
> - Failure scenario: the code is frozen at launch, so if this is not fixed first, the real G.5 assembly STOPs and cannot be repaired without breaking the freeze.
> - Fix:
>   - Land the one-line fallback before launch, preferably in this unit: `run.get("code_state_sha256") or (run.get("diff") or {}).get("code_state_sha256")`, mirroring `_states`. It is semantically neutral: it is the same normalised state the harness's duplicate verdict uses, and the repeat key's definition does not change.
>   - Add a realistic-record assembly test that asserts `flag_mismatch == 0` and `raw_state_missing == 0`.
>
> **m1 — The authority section is stale.** R1-ARMS-DECISIONS is on main (89899f76). The ARMS-T1FEAT A it signs, the readiness report §3 item 7, already fixes "the tier carried by the node code" and "fields that do not apply set to NaN". Cite the row, mark D5 as decided by it, and note that only D1's −1 categorical convention is new.
>
> **m2 — The "same as T0" labels hide offsets.**
> - T0's first trial is accepted without a comparison and counted in `keeps_so_far`; the T1 baseline is not. At the same `budget_index`, T0 `keeps_so_far` is at least 1, while T1's can be 0.
> - T0's `active_seen_before` excludes divergent states (no metric); T1's includes them (the harness rule).
> - Disclose both in the §2 table.
>
> **m3 — One test assertion is vacuous.** The "tiny floor" check in `test_noise_d18_matches_e1_report_and_is_bound_to_the_copy` builds the floored value itself. Test the floor through `derive`, with a low-noise synthetic run.
>
> **m4 — D7's consequence is understated.** `gate_input_builder.TEST_SERIES` requires A5 predictions for every T1 test proposal. Without a T1 A5 input, T1 cannot be in the read at all. Say so.
>
> **m5 — `flag_mismatch` checks only one direction, and the count-versus-STOP policy is not listed.** Also count executed (`RAN`) rows that have `active_equals_incumbent` or `active_seen_before` equal to 1. Add the count-versus-STOP policy to the decision list.
>
> **m6 — `g5_noise` reads run directories without `analysis_guard.refuse_sealed`** (T0's `noise_table` calls it). Under D6 B, either add the guard or state that `derive` runs on an assembled, unsealed directory.
>
> ## Rulings on D1–D7
>
> - **D1: accept.** NaN for numeric fields and −1 for categorical. LightGBM treats negative categorical values as missing, and T0 already uses −1 in `new_cat_code`. The alternative is fairly stated.
> - **D2: accept.** I checked against `diff_support`, `runner` and `campaign_v2_diff` at c025f89:
>   - Inert means normalised state equal to the incumbent's.
>   - Duplicate means the state is in `by_state`: the baseline plus executed, non-infrastructure runs.
>   - `infrastructure_failure_final` is not registered.
>
>   Disclose the T0 difference from m2.
> - **D3: accept.** It is consistent with the signed G5-W A, and it gives 1/W at n = W, like T0.
> - **D4: accept.** It is consistent with v3's treatment of control-plane skips.
> - **D5: already decided** by R1-ARMS-DECISIONS. Record that, and disclose the consequence for the leave-one-suite-out folds: held-out codes are unseen, so they carry no tier signal.
> - **D6: A is acceptable, with an author row amending REL-T1-G1B's copy list, decided together with M2.**
>   - G.1b runs.jsonl holds validation metrics only (the `noise_floor` docstring).
>   - The G.1b seeds (1001–1030, 2001–2030, 3001–3030, plus default runs) are disjoint from the label and evaluation seeds 7001–7010, so the copy leaks nothing.
>   - B is workable (m6).
>   - C is not D18; reject it unless the preregistration is amended.
> - **D7: correct.** It must be settled before the arms-frozen record (m4).
>
> ## Rulings on the flagged issues
>
> 1. **Where a not-run duplicate's code state lives:** confirmed real by the probe. Fix it before launch, as in M4.
> 2. **σ_node defined differently in T0 and T1:** not this unit's code to change, but it must become an explicit author decision before launch (M2).
> 3. **D18's 0.002 floor in metric units:** apply it as preregistered. The same 0.002 metric-unit threshold (`MIN_EFFECT`) already decided which T1 nodes qualified in G.1b, so it is consistent. It binds only on very low-noise nodes, and whether it binds is visible from the record's median.
>
> Housekeeping: the base worktree at /tmp/t1frev/base is removed. Scratch, including the probe test, is in /tmp/t1frev/_to_delete/. /tmp/pb/wt/t1feat, /tmp/pb/repo and /tmp/pb/wt/t1h were not modified.
>
> VERDICT: NOT ACCEPTED (M1 memory_on mapping not declared; M2 σ_node definition must be an author decision bundled with D6; M3 decisions must be final before the G.5 launch, not the assembly; M4 the assembly STOPs on real not-run duplicates: land the fallback with a realistic-record test before launch)

## Round 2 (`a5715142`)

> Reviewed base: a5715142fb2597bacbb7315027df80a0fa3352de (round 2. The diff reviewed is 2530d8e6..a5715142: merge c50fca7c plus fix commit a5715142.)
>
> ## Summary
>
> The four round-1 M findings are fixed and the six m findings are addressed. I verified the author's summary point by point. I found no new defects.
>
> **The merge does not touch this unit.** The only difference between c50fca7c and baf6be5d is this unit's six original files. The merge also brings the main side, including `arms_freeze.py`, but none of that touches this unit's code, so there is no interaction. `r1/c3/features.py`, `dataset.py`, `gate.py` and `gate_input_builder.py` are still unchanged.
>
> **Tests.** I ran the seven files one at a time at the tip, with AR_HARNESS_ROOT set. All pass, matching the author's counts:
>
> | File | Result |
> |---|---|
> | test_t1_features | 17 passed |
> | test_t1_g5_seal | 30 passed |
> | test_t1_g5_job | 23 passed |
> | test_t1_g5_tasl | 108 passed |
> | test_c3_features | 9 passed |
> | test_gate_input_builder | 41 passed |
> | test_c3_dataset | 4 passed |
>
> ## Verification of the fixes
>
> - **M4 (fixed).** `g5_assemble.node_rows` now reads the candidate state from the top-level field, then the `diff` provenance, then the parent state for a no-op. This matches `g5_features._states` in substance.
>   - `test_assembly_on_realistic_records` uses records shaped as `runner.run` writes them: code state only in `diff`, raw states everywhere, and a duplicate of an evaluated state that is not the incumbent. It asserts `flag_mismatch` 0, `raw_state_missing` 0, the duplicate's `candidate_hash` and a byte-identical test stage.
>   - I reverted the one line in my own scratch worktree. The test then fails with exactly the round-1 STOP ("a duplicate without its code state"), so the test is not vacuous.
> - **M1 (fixed).** D8 is added (1.0 as built, or NaN). §2 and the module docstring now call `memory_on` a declared mapping, not "same as T0".
> - **M2 (fixed).** D6-σ is added beside D6, with no recommendation, and the 3b-2 default is unchanged.
>   - The new `sigma_node_t0_definition` and `n_material_edits` replicate `dataset.noise_table`'s rule (median `sd_joint` over material edits, falling back to all edits). They also replicate `e1_report`'s material test: resolved, or Δ ≠ 0 when se = 0, and |Δ| ≥ 0.002.
>   - Both are tested for exact equality against `e1_report.summarise`. `builder_noise` does not use them.
>   - δ_n stays bit-identical: same arrays, same seed order, same `_sd`.
> - **M3 (fixed).** §5 now says the decisions must be final, and their code on main, before the G.5 launch, and gives the reason (the freeze). D6 is due before the noise is built, and D7 before the arms-frozen record.
> - **m1.** R1-ARMS-DECISIONS (89899f76) is cited. D5 is marked decided, and only D1's −1 convention is described as new.
> - **m2.** The `keeps_so_far` offset and the `active_seen_before` difference (divergent states count as seen) are disclosed in the report and the docstring.
> - **m3.** The vacuous assertion is replaced by `test_noise_d18_floor_through_derive`. It uses a low-noise run, and δ_n comes out at 0.002 through `derive`, with the median checked against `e1_report`.
> - **m4.** D7 now states the consequence: `TEST_SERIES` requires A5 predictions for every non-inert T1 test proposal, so without a T1 A5 input, T1 is not in the read.
> - **m5.** `flag_mismatch` now also counts executed rows whose fields say inert or seen before, and D9 lists count versus STOP.
>   - I probed it with realistic ledgers where step 3 executes onto step 2's evaluated state. The count comes out at 12, one per campaign, with `raw_state_missing` 0.
> - **m6.** Every `g5_noise` read goes through `analysis_guard.refuse_sealed`. I probed it: an `r1_sealed` run directory raises RuntimeError before anything is read.
>
> ## Findings
>
> No B or M findings.
>
> - **m1 (optional, non-blocking): two guards are probed but not tested in the repository.** Both work, but nothing in the repo would catch a regression. Consider adding a test for the converse direction of `flag_mismatch` and one for `g5_noise`'s `refuse_sealed`.
> - **m2 (cosmetic): `g5_noise._refuse_sealed` inserts REPO_ROOT into `sys.path` as a side effect.** It is harmless, because `g5_noise` is not on the release-check import path.
>
> ## Rulings
>
> My round-1 rulings are now written into §5 as "Review ruling", with correct attribution, and I stand by them:
> - D1–D4: accept.
> - D5: decided by R1-ARMS-DECISIONS.
> - D6: A is acceptable, with an author row amending REL-T1-G1B. B is workable. C is rejected unless the preregistration is amended.
> - D7: correct.
> - D6-σ, D8 and D9 are fairly framed author decisions. The defaults are unchanged and the alternatives are stated with their cost.
>
> The flagged issues are resolved as follows:
> - **Not-run duplicates:** fixed and tested.
> - **σ_node:** now decision D6-σ.
> - **The 0.002 floor:** applied as preregistered.
>
> Housekeeping: my scratch worktree is removed and `git worktree list` shows nothing under /tmp/t1frev. Scratch is in /tmp/t1frev/_to_delete/. The folder had disappeared between rounds, so I recreated it. The reviewed worktree was not modified.
>
> VERDICT: ACCEPTED

## Round 3 (`b033050e`)

> Reviewed base: b033050e0e48feda04e89d6a9a62c28c49d85169 (confirmation round; diff a5715142..b033050e)
>
> ## Summary
>
> The new commit does what the author says, and the merge is clean and does not touch this unit. Round 2 stands: accepted.
>
> ## The merge (50771398)
>
> - **Clean.** It differs from its main-side parent 2582c898 by exactly this unit's six files.
> - **This unit's files are unchanged by it.** The unit's code and test files are identical to a5715142.
> - **The only shared file is `g5_tasl.py`,** and the merge adds just the two `IMPORT_SOURCES` entries for `g5_features` and `g5_noise`.
> - **No interaction** with the `decision_row_checks` refactor: `test_t1_g5_tasl` passes, 108 tests.
>
> ## The new commit
>
> **`g5_noise._refuse_sealed`.** It is now a line-for-line copy of `analysis_guard.refuse_sealed`: same `None` skip, `expanduser`, lexical plus symlink-resolved check, case-insensitive match, same message. The `sys.path` side effect is gone.
>
> **`test_flag_mismatch_counts_an_executed_row_the_fields_call_seen`.** Not vacuous.
> - `repeat_step=6` makes step 6 execute step 2's discarded state.
> - The test asserts that row's features (seen before = 1, equal to incumbent = 0) and the counts `{"raw_state_missing": 0, "flag_mismatch": 12}`, one per ledger.
> - The new parameter defaults to `None`, so `test_assembly_on_realistic_records` is unchanged.
>
> **`test_noise_refuses_an_r1_sealed_run_directory`.** Not vacuous.
> - `derive` on a run directory under `r1_sealed` raises before any `read_bytes` under it. The test tracks `Path.read_bytes`, which is how `node_delta` reads.
> - Both functions give the same verdict on six paths, including a symlink into the seal and upper-case `R1_SEALED`, and they do not refuse a plain path.
>
> **Report §9** accurately describes the two additions.
>
> ## Tests
>
> Run at the tip, one file at a time, with AR_HARNESS_ROOT=/tmp/pb/wt/t1h. All pass:
>
> | File | Result |
> |---|---|
> | test_t1_features | 19 passed |
> | test_t1_g5_seal | 30 passed |
> | test_t1_g5_job | 23 passed |
> | test_t1_g5_tasl | 108 passed |
> | test_c3_features | 9 passed |
> | test_gate_input_builder | 41 passed |
>
> ## Findings
>
> None: no B, M or m findings.
>
> ## Rulings
>
> My round-2 rulings are unchanged:
> - D1–D4: accept.
> - D5: decided by R1-ARMS-DECISIONS.
> - D6: A is acceptable, with an author row amending REL-T1-G1B.
> - D6-σ, D8 and D9: open for the author before the G.5 launch.
> - D7: correct.
>
> The flagged issues are resolved:
> - **Not-run duplicates:** fixed and tested.
> - **σ_node:** now decision D6-σ.
> - **The 0.002 floor:** applied as preregistered.
>
> Housekeeping: no worktrees were created this round and the reviewed worktree is clean. Scratch is in /tmp/t1frev/_to_delete/t_r3.
>
> VERDICT: ACCEPTED

---

Code-Commit: b033050e0e48feda04e89d6a9a62c28c49d85169
Verdict: ACCEPTED

Accepted at `a5715142`, confirmed at `b033050e`.
