Reviewed base: origin/main `f1f1b6511`; accepted at `a3523491` (code `f3b18e9c`), post-acceptance fixes confirmed at `935f50ae5` (code `f0e5f2c3`)

# Independent review record — G.5: pilot_basis and P3 on the G.4b result and its dates (R1-BX-D14-G4B), harness commits filled with the recount tips, xc3 rules by import from READY 107, CUDA-IPC on TASL-7 audits, TASL-7 audit chunks in the dates tool; G.5 draft revision 12

**Unit.** On `mac-g5-pilot-basis-g4b-20261126`: `sweep2/t1_tasl/g5_tasl.py`, `g5_tasl_spec.json`, `g5_job.py`; tests `test_t1_g5_tasl.py`,
`test_t1_g5_job.py`; the G.5 authorization draft revision 12 (`approved: false`), a dated note in the T1 release rows draft, and the report
`docs/r1/reports/g5_code_20261123/G5_PILOT_BASIS_HARNESS_20261126.md`. Authority: R1-BX-D14-G4B, R1-XC3-FAIL-READING, R1-XC3-NOTE,
R1-G5-EXPANSION-JOIN, R1-G5-DIFF-RECOUNT, R1-G5-AUDIT-TWO-CARDS; the queue of 26 Nov 2026 (02:26), item 3. The unreviewed preparation
`mac-g5-pilot-basis-g4b-20261125` (`a9c23230`) was ported by hand, not merged, and is superseded.

**Process.** One independent reviewer for both rounds, read-only, no label, evaluation, sealed or secrets file opened, scratch moved to its
`_to_delete/`. Round 1 accepted with eight minors and four nits after recomputing the dates from the captured G.4b summaries (equal to
`dates_g5.json`), rerunning the harness pin checks and confirming the 0-day gain of TASL-7 audit chunks; the fixes were confirmed.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `f1f1b651` 59 failed, 4123 passed, 197 skipped, 3 errors;
code tip `f0e5f2c3` (docs `2888e44d`) 59 failed, 4174 passed, 197 skipped, 3 errors; `FULLSUITE_PB2_BASE_f1f1b651_FAILED.txt` =
`FULLSUITE_PB2_TIP_R1_2888e44d_FAILED.txt` (62 entries; main's extra failure `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks`
is pre-existing and outside this unit).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `a3523491` | ACCEPTED (minors m1–m8, four nits) |
| 2 | `935f50ae` | CONFIRMED |

**Open items.** The author still signs the items in draft §11.1 (S1–S12): S1 `cap_gpu_hours` (recommended A, TASL-7 audit hours inside the
425 GPU-h cap, as now rendered), S2 216.9 GPU-h, S3 P3/P7 text (the TASL-2 `pilot-basis` PASS recorded first; the G.4b seals stay in place until
G.5 is sealed), S4 CUDA IPC (C12 on both hosts or the extended acceptance line), S5 TASL-7 schedule, S6 the freeze-wait date, S7 STOP
thresholds, S8 unchanged lines, S9 the expansion addendum (open; a ninth T1 node conflicts with the frozen eight-node split file, PRE-SPLIT A,
an author decision), S10–S12. Operational: TASL-2's `harness_g5` must be at `cbf7a003` and `harness_g5_ar` at `ccdb3774` before G.5 starts.
The `test_t1_tasl_xc3` alt-B case needs a test-only fix (fake `read_main`).

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

---

Code-Commit: f0e5f2c3
Verdict: ACCEPTED

Accepted 26 Nov 2026.
