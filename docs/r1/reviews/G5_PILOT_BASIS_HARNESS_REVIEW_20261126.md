Reviewed base: origin/main `cdb8be91d` (rounds 1–2 on `f1f1b6511`); accepted at `a3523491` (code `f3b18e9c`), confirmed at `935f50ae`; revision-13 amendment (R1-TASL2-CPU, xc3 on main) accepted at `91dc84e5`, confirmed at `e94d4b3fb` (code `c8823ec8`)

# Independent review record — G.5: pilot_basis and P3 on the G.4b result and its dates (R1-BX-D14-G4B), harness commits filled with the recount tips, xc3 rules by import from READY 107, CUDA-IPC on TASL-7 audits, TASL-7 audit chunks in the dates tool; G.5 draft revision 12; revision 13: R1-TASL2-CPU (houseprice on TASL-2 CPUs 0-7 with a fixed-seed determinism gate) and the xc3 PASS verdicts pinned from main

**Unit.** On `mac-g5-pilot-basis-g4b-20261126`: `sweep2/t1_tasl/g5_tasl.py`, `g5_tasl_spec.json`, `g5_job.py`; tests `test_t1_g5_tasl.py`,
`test_t1_g5_job.py`; the G.5 authorization draft revision 12 (`approved: false`), a dated note in the T1 release rows draft, and the report
`docs/r1/reports/g5_code_20261123/G5_PILOT_BASIS_HARNESS_20261126.md`. Authority: R1-BX-D14-G4B, R1-XC3-FAIL-READING, R1-XC3-NOTE,
R1-G5-EXPANSION-JOIN, R1-G5-DIFF-RECOUNT, R1-G5-AUDIT-TWO-CARDS; the queue of 26 Nov 2026 (02:26), item 3. The unreviewed preparation
`mac-g5-pilot-basis-g4b-20261125` (`a9c23230`) was ported by hand, not merged, and is superseded.

**Process.** One independent reviewer for both rounds, read-only, no label, evaluation, sealed or secrets file opened, scratch moved to its
`_to_delete/`. Round 1 accepted with eight minors and four nits after recomputing the dates from the captured G.4b summaries (equal to
`dates_g5.json`), rerunning the harness pin checks and confirming the 0-day gain of TASL-7 audit chunks; the fixes were confirmed. After main moved to `cdb8be91` (four xc3 PASS verdicts; R1-TASL2-CPU: no R1 job on TASL-2
uses CPUs 8-11) the author merged main and amended the unit (revision 13): houseprice's TASL-2 set 8-15 replaced by 0-7, a houseprice-specific
fixed-seed determinism check gated by `check_cpuset_record`, a refusal of any TASL-2 set containing 8-11, the four xc3 verdicts pinned by
path and sha256, the dates tool's default TASL-7 node set read from main (all seven G5-7 nodes; still 0 days); the same reviewer accepted it
with three minors and two nits, and confirmed the fixes.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `cdb8be91` 59 failed, 4123 passed, 197 skipped, 3 errors;
code tip `c8823ec8` (docs `311f1b2b`) 59 failed, 4205 passed, 197 skipped, 3 errors (second run; the first had one extra timing-dependent
Track P failure, see the confirmation round); `FULLSUITE_PB2_BASE_cdb8be91_FAILED.txt` = `FULLSUITE_PB2_TIP_R13R1_311f1b2b_FAILED.txt` (62 entries;
earlier rounds on `f1f1b651`: `FULLSUITE_PB2_BASE_f1f1b651_FAILED.txt` = `FULLSUITE_PB2_TIP_R1_2888e44d_FAILED.txt`; main's extra failure `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks`
is pre-existing and outside this unit).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `a3523491` | ACCEPTED (minors m1–m8, four nits) |
| 2 | `935f50ae` | CONFIRMED |
| 3 | `91dc84e5` | ACCEPTED (revision 13; m-A1–m-A3, two nits) |
| 4 | `e94d4b3f` | CONFIRMED |

**Open items.** The author signs the items in draft §11.1 (S1–S14), among them S1 `cap_gpu_hours` (recommended A, TASL-7 audit hours inside
425, as rendered), S4 CUDA IPC, S9 the expansion addendum (open; a ninth T1 node conflicts with the frozen eight-node split file, PRE-SPLIT A),
and S13 the TASL-2 CPU schedule against the expansion G.1b (options (i) wait, (ii) operator flock on `cpus-0-3.lock`/`cpus-4-7.lock`, (iii)
accept the overlap; recommended (i) via (ii); the date costs given are upper bounds). Before houseprice's first TASL-2 job: its
`G5_TASL2_CPUSET_CHECK_mlgym_houseprice_<date>.json` PASS record on main (report §12.3). Operational: TASL-2's `harness_g5` at `cbf7a003`,
`harness_g5_ar` at `ccdb3774`, TASL-7's `harness_g5` at `cbf7a003`; the TASL-2 `pilot-basis` PASS before the signature; the G.4b seals stay in
place until G.5 is sealed. Outside this unit: `test_t1_tasl_xc3`'s alt-B case and the timing-dependent Track P test
`test_probe_attempts_are_sealed_gated_recorded_and_charged` need test-only fixes.

## Round 1 (`a3523491`)

> ## Round 1, `a3523491` (on main `f1f1b651`): ACCEPTED
>
> No BLOCKING or MAJOR findings; eight minors and four nits, none changing a value, a check outcome or a decision. Fix m1–m3 before the note is signed.
>
> ### Checked independently
> 1. **Values against main.** G.4b spec `56f8c293…`, signed note `df600e3f…` (approved, run `g4b-tasl-20261124-a`, harness `cbf7a003`), result `af74c536…`, corrigenda `3eca0732…`; spec now `1e29b595…`. Receipt and job-record sha256s match the captures and result §7; each pilot-summary sha256 equals its capture, which equals the job record's `summary` as JSON. Liveness matches result §4 and the captures. Desk recompute with `g4_tasl.recompute_dates` on the captured summaries with this spec's `dates_params`: with 2026-11-25 the whole JSON equals `dates_g5.json`; P7 216.9; with 2026-11-26 each date one day later. The corrigenda change nothing the unit uses; the `--today` re-anchor is superseded by R1-BX-D14-G4B.
> 2. **pilot_basis / P3.** Every mismatch refuses (17 refusal cases plus 24 validator refusals). TASL-2-only re-read sound (a TASL-7 chunk is claimable only after the TASL-2 job that passed P3 made the plan; small gap m5). Nothing in scope PENDING. STOP 3 not indicated (every `ran_of_valid` ≥ 0.6167). P7 tie enforced in `validate_spec`.
> 3. **Harness commits.** `cbf7a003`/`ccdb3774` descend from their pins and the reviewed engines and differ from `c1063f6b`/`e8d676a8` only by the review record; `g5_pin_check` 0; `measurement_path_check` passes (308 paths, closure 15, no engine file); `check_engines` passes.
> 4. **xc3 imports.** Identical behaviour and exception class; `g1b_crosscheck.py` unchanged; nothing new in a frozen closure; real-main reading A, note `…20261126.md`, row present, skip none, run `g1b-tasl-20261121-b-xc3-a`, `xc_spec_sha256` = `fc064ded…`.
> 5. **CUDA-IPC.** Under c12 TASL-7 fails closed (`check_c12(host=TASL-7)` refuses a null record in the switch and in `claim_chunk`); under acceptance the extended line goes into the note.
> 6. **Dates tool.** Faithful to READY 108 (chunk 0 taken under `claims_lock`, `g5_job.py:1391-1396`; E5 excluded; real `chunk_plan`); no double count (1590 runs vs 1589 for `mlab_cifar10`); 0-gain reproduced (at most two chunks per wave for the seven G5-7 nodes); "chunk 0 claimable" side note reproduced (16.07 h, labels 10 Dec).
> 7. **Draft revision 12.** §5 block equals a fresh render (55 lines, except `approved:`); `approved: false`; XC3-FAIL signed A; §11.1 options only.
> 8. **Expansion conflict real.** The frozen split file `r1/c3/splits/c3_p3_split_v1.json` (`b5967dd7…`, prereg line 301) lists exactly eight T1 nodes; PRE-SPLIT A; an author decision for the expansion unit.
> 9. **Tests.** g5_tasl 186, g5_job 52, g5_seal 40, features 30 (+1 skipped), tasl_g4 47, tasl_g4b 5, tasl_crosscheck 79, d7_diff_b 19, tasl_xc3 4 + 1 failed (pre-existing on main), g5_ar_projection 6. Full-suite lists identical (62).
> 10. **Scope.** Only the ten listed files; gate*, release.py, prereg, trackg/ untouched; no `approved: true`.
>
> `test_t1_tasl_xc3` failure: pre-existing on main; `r1/tests/test_t1_tasl_xc3.py:160` calls `check_xc_note` with the live `read_main`; main's row says A, so B is correctly refused. Fix in a small test-only unit: a fake `read_main` without the row, plus a case asserting B is refused against row A.
>
> ### Findings
> - **m1** pilot-summary sha256 comes from the captures; the result's `out.tar` sha256s (`5f9c2f2a…`, `5d0b48dd…`, `8661e5b8…`) are not bound. Bind `out_tar_sha256` from §7 (report needle check); record the TASL-2 `pilot-basis` PASS before signature.
> - **m2** the render test only checks each rendered line appears somewhere; assert the fenced block equals the render.
> - **m3** draft lines 81, 1546-1553, 1742 still call D7-DIFF B's O1 open; the recount review (`G5_DIFF_RECOUNT_REVIEW_20261124.md:32`) confirms both halves (`audit_g5.py:539-571`).
> - **m4** cap line "counted per the worker card (G5-TASL-GPUH A)" does not name TASL-7; name it, or have S1 state the reading.
> - **m5** a TASL-7 job does not run the main-side half of P3; run those checks on both hosts.
> - **m6** the G.4b seals must stay in place until G.5 is sealed (state in the operational note and S3).
> - **m7** `test_t1_g5_tasl.py:1313` reads live origin/main; use the `Main` fake.
> - **m8** merge-order wording: the branches share no files; "re-run the tests; re-render only if the spec or `note_lines` changed".
> - **nits:** draft §1 heading `44c3d80e`; §11.1 intro omits the mechanical fills; "every value from the committed result" vs captures; `pilot_basis` does not bind the result's review (`a04b490e`).

## Round 2 (`935f50ae`)

> ## Confirmation round, `935f50ae` (main `f1f1b651`): CONFIRMED
>
> All of round 1's m1–m8 and the four nits are fixed; `git diff a3523491 935f50ae` contains only those fixes; nothing new. Six files changed (`g5_tasl.py`, `g5_tasl_spec.json`, `test_t1_g5_tasl.py`, the draft, the report, the new list); gate*, release.py, prereg, trackg/ untouched; no `approved: true`.
>
> - m1: `out_tar_sha256` `5f9c2f2a…`, `5d0b48dd…`, `8661e5b8…` each appear once in the result report on main and equal the captured `sealed_SHA256SUMS` lines; compared with the file at TASL-2 starts; S3 requires the TASL-2 `pilot-basis` PASS before signature; tests cover refusal and seal mismatch over all four keys.
> - m2: the fenced §5 block must equal the render line for line.
> - m3: O1 satisfied under (a), citing recount review line 32 and `audit_g5.py:539-571` at `cbf7a003`.
> - m4: `cap_gpu_hours` renders "425, counted per the worker card (G5-TASL-GPUH A), the hours of G.5 audit chunks on TASL-7 included (R1-G5-AUDIT-TWO-CARDS)"; S1 still offers A, B, C.
> - m5: `pilot_basis_main_check` (result, corrigenda, review, G.4b note on main by sha256, dates row) at TASL-7 starts; TASL-2 runs it then re-reads the seals; test `test_p3_main_half_runs_at_tasl7_job_starts`.
> - m6: seals stay in place, stated in four places. m7: `Main` fake. m8: wording.
> - Nits fixed; `pilot_basis.review` binds the result review (`a04b490e…`, contains the report sha256 and "Verdict: ACCEPTED").
> - Bindings on main: `pilot_basis_main_check` passes against `f1f1b651`; spec `b66ebb94…`; `validate_spec` passes; desk recompute equals `dates_g5.json`; P7 216.9; `g5_pin_check` 0; `measurement_path_check` 308 paths, closure 15, no engine file, both tips.
> - §5: 55 lines equal a fresh render except `approved:`; only `cap_gpu_hours` and `spec_sha256` changed.
> - Tests one file at a time: g5_tasl 190, g5_job 52, g5_seal 40, features 30 (+1 skipped), tasl_g4 47, tasl_g4b 5, tasl_crosscheck 79, d7_diff_b 19, tasl_xc3 4 + 1 failed (pre-existing on main), g5_ar_projection 6; list identical to base (62).

## Round 3 (`91dc84e5`)

> ## Amendment review (revision 13, R1-TASL2-CPU and xc3 on main), `91dc84e5` (main `cdb8be91`): ACCEPTED
>
> No BLOCKING or MAJOR; three minors, two nits; none changes switch behaviour. Scope `git diff 6ca4dfa8 91dc84e5` (the main merge `6ca4dfa8` clean, no conflict resolution): `g5_tasl.py`, `g5_job.py` (2 lines), spec, two test files, draft revision 13, report §12, two lists; gate*, release.py, prereg, trackg/ unchanged; `approved: false`.
>
> 1. R1-TASL2-CPU (PLAN line 1541) covers TASL-2 only; stability record `9dca2cf3…` bound; only houseprice had a TASL-2 set with 8-11 (8-15).
> 2. `g5_job.run_job` calls `G.gpu_lease(w["lease"])` unconditionally (CPU nodes included), `~/r1_locks/gpu0.lock` on TASL-2, so G.5 TASL-2 jobs are serialised among themselves; G.1b's `run_node_job` takes no lease for a CPU node (`g1b_tasl.py:833`) and the expansion's CPU jobs take only `cpus-*.lock` (m-A2).
> 3. Keeping 8-15 in the node entry for TASL-7 is consistent (node fields equal the signed G.1b spec; houseprice's xc3 TASL-7 attempt ran with affinity 8-15 and passed bit-identically).
> 4. No path gives a houseprice TASL-2 job 8-15: the `g5` wrapper's `cpus` query defaults to TASL-2 (0-7; `--host TASL-7` gives 8-15); `worker_shim` sets the replacement on TASL-2; `check_affinity` STOPs a manual 8-15 start; a `g5t7` start on TASL-2 fails `host_identity`.
> 5. Determinism check sound: `cpuset_spec` differs from the signed G.1b spec only in `run_id`, `nodes` and the `cpuset_check` block and passes `validate_spec(launch=True)`; the reference attempt (`15b7beea…`, spec `060aac91`) is like-for-like (houseprice entry and TASL-2 host block identical to `7ff3c95b`); budget 9.486 s per run vs measured ≤ 5.895 s (TASL-2) / 5.686 s (TASL-7); `check_cpuset_record` requires one PASS record on main at every houseprice TASL-2 start and refuses on `cdb8be91`; §12.3 holds `gpu0.lock`, `cpus-0-3.lock`, `cpus-4-7.lock` with `flock -n`; lease names unchanged on `mac-g1b-expansion-20261126c` (`cpus-<set>.lock`; metamaze 0-3, forestcover 4-7, titanic 12-15, etth1 16-31).
> 6. xc3 pins match main byte-for-byte (`9cce9064…`, `b42e485c…`, `cb2ac690…`, `6c7da440…`), each `g1b_tasl_crosscheck_verdict/1`, short, PASS, run `g1b-tasl-20261121-b-xc3-a`, the only four such files outside captures; `xc3_reading` A, skip none; `default_tasl7_nodes` all seven; recompute 0 claimable TASL-7 GPU-h.
> 7. §5 equals a fresh render (57 lines, except `approved:`); spec `16b39b47…`; `validate_spec` passes.
> 8. Tests one file at a time: g5_tasl 221, g5_job 52, g5_seal 40, features 30 (+1 skipped), tasl_g4 47, tasl_g4b 5, tasl_crosscheck 79, d7_diff_b 19, tasl_xc3 4 + 1 known, g5_ar_projection 6; lists identical (62).
>
> ### Findings
> - **m-A1** the `tasl2_cpuset_check` line says "the TASL-2 lease held"; the code takes no lease for a CPU node; the line should name `gpu0.lock` and, while expansion jobs run, `cpus-0-3.lock` and `cpus-4-7.lock`.
> - **m-A2** the `tasl2_cpus` line's "jobs sharing CPUs never overlap" holds only among G.5 jobs; reword, pointing to S13's schedule.
> - **m-A3** S13's option (i) does not state its cost (G.5 TASL-2 start delayed by up to ~6 days, against R1-G5-EXPANSION-JOIN's "as soon as signed"; nothing ends expansion jobs at 2 Dec); (ii) works as an operator flock without code.
> - nit: `check_cpuset_record` should recompute `check_spec_sha256` from `cpuset_spec(...)`.
> - nit: `test_xc3_pass_on_published_main_makes_all_seven_eligible` reads live origin/main; use a `Main` fake.

## Round 4 (`e94d4b3f`)

> ## Revision-13 confirmation, `e94d4b3f` (main `cdb8be91`): CONFIRMED
>
> All five fixes (m-A1, m-A2, m-A3, both nits) are in place; `git diff 91dc84e5 e94d4b3f` contains nothing else. Files: `g5_tasl.py`, `test_t1_g5_tasl.py`, draft, report §13, list `FULLSUITE_PB2_TIP_R13R1_311f1b2b_FAILED.txt`; spec unchanged (`16b39b47…`); `g5_job.py`, gate, release, prereg, trackg/, Track P untouched; `approved: false`.
>
> - m-A1: `tasl2_cpuset_check` names `~/r1_locks/gpu0.lock` by flock (a CPU node's G.1b job takes no lease) plus `cpus-0-3.lock` and `cpus-4-7.lock` while expansion jobs run; names from `expansion_leases()` over `EXPANSION_CPU_SETS` (0-3, 4-7, 12-15, 16-31), matching `mac-g1b-expansion-20261126c` (`g1b_tasl.py:222-230`); note text only.
> - m-A2: "G.5 jobs sharing CPUs never overlap one another"; the expansion's CPU jobs take only `cpus-<set>.lock`; overlap governed by S13.
> - m-A3: facts match the c-branch prep report §5.4 (Forest Cover 16.400 h / 24.475 h, latest start 30 Nov 23:31, deadline 36.81 h; MetaMaze 7.131 h / 10.572 h, 1 Dec 13:25, 21.59 h); conflict with R1-G5-EXPANSION-JOIN noted; no code ends expansion jobs; (i)–(iii) open; recommendation (i) via (ii)'s flock.
> - Nit 1: `check_cpuset_record` recomputes `check_spec_sha256` from `cpuset_spec(...)` (two tamper cases). Nit 2: the real-main xc3 test uses a `Main` from checkout files and checks XC3-FAIL A.
> - S13 arithmetic recomputed (label days = ceil(5 + 1 + 0 + (216.9 + extra)/24) from 2026-11-26): 0 → labels 12 Dec, B.7 15 Dec; +16.4 h → no move; +24.475 h → 13 Dec / 16 Dec; +6 days → 18 Dec / 21 Dec; all match.
> - §5 equals a fresh render (57 lines, except `approved:`); only `tasl2_cpus` and `tasl2_cpuset_check` changed.
> - Tests one file at a time: g5_tasl 221, g5_job 52, g5_seal 40, features 30 (+1 skipped), tasl_g4 47, tasl_g4b 5, tasl_crosscheck 79, d7_diff_b 19, tasl_xc3 4 + 1 known, g5_ar_projection 6; 311f1b2b list identical to base (62).
> - Nits (wording): the date costs are upper bounds (the wait may overlap the model's prerequisite days); §13.1 line 654 "+6 days on top" should read "+6 days in total".
> - Outside the verdict: `test_trackp_p4_runner.py::test_probe_attempts_are_sealed_gated_recorded_and_charged` (line 2009) depends on real elapsed time (`p4_lib.py:1098-1100`, `:795`): runs under ~0.18 s round to 0.0 h, the charge is exactly 2.0 and `probe_hours > 2.0` (`:1572`) is False; code correct; test-only fix: monkeypatch `L.time.time` in `probe_world`, or assert against `ceil_hundredth(charged) > 2.0`.

---

Code-Commit: c8823ec8
Verdict: ACCEPTED

Accepted 26 Nov 2026.
