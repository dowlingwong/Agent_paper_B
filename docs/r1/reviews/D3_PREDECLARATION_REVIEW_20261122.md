**AI-assisted independent review (Claude, fresh session, subagent), 22 Nov 2026.** Tier E (R1-PROCESS-TIERS).
Under review: `ec1cbfcf` (`r1/c3/d3_analysis.py`, `r1/tests/test_d3_analysis.py`) and `be4d0d9a`
(`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` = PD, `docs/r1/authorizations/D3A_AUTHORIZATION_DRAFT_20261122.md` = AN),
on `d9acb501`, branch `mac-d3-predecl-20261122`. No label, test-partition, evaluation-value or sealed file was opened.

# D.3 pre-declaration and D.3a note drafts: review

## Verdict: REVISE (1 MAJOR, 9 MINOR, 10 NOTE)

The draft is careful and nearly complete. The MAJOR finding is that the code inventory misses an existing PACE-style gate
in the repository, which changes what the author is asked to choose for EGATE.

## What was checked and found correct

- **Pins:** the sha256 values in PD §9/§14 match the files on disk. `d3_analysis.py` is `e16e4f2e…7f84`, the tests file
  `48414145…dedf`, PLAN `75b5ae36…` (equal at `d9acb501`), the preregistration `aa1a961b…`, the split file `b5967dd7…`
  and the noise summary `3d12ce05…`. The tests pass: `pytest r1/tests/test_d3_analysis.py` gives 23 passed.
- **Completeness against R1-D3-MIN and R1-MINSUB-CHOICES (4):** every listed item is fixed with a source or marked
  proposed: node set, memory mode, W, cap, 18 instances with ids, seeds, the audit's K/seeds/host, all contrasts
  (including LADDER − A0 and LADDER − A2), sample sizes, multiplicity, the script, and the LADDER objective, procedure
  and constants pin. A6 is handled as RUNBOOK P.5 and R1-D3-MIN say (PD:246-248, PD:412).
- **Seeds:** `check_namespaces()` passes. A search of all 129 local and remote refs for `__s<seed>` in the three blocks
  found nothing. Every numeric range in PLAN, RUNBOOK and `authorizations/` (1001–3030, 4001–4003, 5001–5006,
  5101–5112, 6101–6108, 7001–7010, 8001–8010, 9001–9303, 30000–39999, 100000–799999) is in the reserved list. The code
  constants in `r1/` and `sweep2/` show no other block. The sweep universe is 100–276. 6201–6218, 6501–6679 and
  6701–6880 collide with nothing that could be checked (the harness verify seeds could not be; see NOTE 8 and below).
- **Statistics:** the minimum detectable effect (MDE) is right: (z₀.₉₉₅₈₃ + z₀.₈)/√126 = 0.310, and 0.250 at α = 0.05.
  df = 7 × 17 = 119. The e-process formula is the correct closed form of the half-normal mixture of
  exp(λx − λ²n/2). The commit thresholds 3.26/2.07/1.63/1.40/1.24 σ reproduce. The script's Holm step-down,
  stratified SE and bootstrap draw order match PD §7.3.
- **Numbers** trace to the files cited and the arithmetic holds: 2,512/5,760 → 0.564 → 35.5 calls, 748 = 288 + 460
  (`SWEEP2_REPORT_20261121.md:33,48`; `PRECONDITION2_20261122.md:27`); Track S 0.28 × 747/800 = 0.26 → 77 calls
  (`TRACKS_S05_SUMMARY_20261115.md:109-119`); 5,823 s × 7/3,600 = 11.32 GPU-h per arm → 76.7 and 135.9; 1,364 s ×
  16/4,660 = 4.68 worker-seconds per run (`b2_audit_20261119/REPORT.md:20`), 8,820 runs ≈ 11.5 worker-hours;
  7.986 + 5 = 12.99 %. The 0.054/0.125 shares, the cap-80 precedent and the runtime-error classes also trace.
- **D.3b pairing:** `check_pair` plus the full-design check enforce the same instances, start configuration, sigma,
  pre-declaration and repetitions.

## Findings

**1. MAJOR — the EGATE inventory is wrong, and §13 item 4 leaves out the existing PACE-style gate.**
- PD:221-222 says PACE is recorded on `main` "only as 'statistical commit gate'"; PD:408 lists EGATE's code as "none".
- What exists: `r1/baselines/responses.py:19-46` has `PaceStyleGate`, "PACE-style; after arXiv 2606.08106, not a
  reproduction". It is a betting e-process (Waudby-Smith & Ramdas) on clipped paired differences, with α = 0.1,
  clip = 0.05 metric units and max_pairs = 8. It has a test (`r1/tests/test_l10_baselines.py:55-66`) and is noted in
  `reviews/BUILD_REVIEW_20261012.md:31` as needing a `verify:pace` action version.
- Why it matters: that gate is valid without a known variance; its null is on the clipped mean. The draft's normal
  mixture needs a known σ. The author is asked to choose EGATE's construction without seeing this option.
- **Fix:** in G4, list `PaceStyleGate` and its test. In §13 item 4, give both constructions with their constants,
  their nulls and assumptions, and the cost of each in runs within W = 20, and say which is recommended and why.
  Correct PD:221-222.

**2. MINOR — replicate-run charging is described as existing when it does not.**
- PD:133-134 says `r1/c3/accounting.py` counts "plus replicate runs". It does not: `accounting.py:33-39` counts
  trials whose worker ran plus 2r per verify. PD:415 still marks G8 "usable as is".
- Nothing shows that the harness `ComputeBudget(max_worker_runs=20)` would stop on replicate runs that the controller
  issues.
- **Fix:** mark G8 "needs changes" (count FIXR3/EGATE candidate and incumbent replicate runs). Add to the G3/G4 spec
  that every replicate run is charged against the same W counter, which refuses an unfundable step. Correct PD:133-134.

**3. MINOR — EGATE's α claim needs its qualifier where the claim is made.**
- PD:213-216 states the Ville bound under "σ_cmp-sub-Gaussian d_j". But σ_cmp is the median over edits of per-edit
  `sd_joint` (`r1/c3/dataset.py:97-104`), so the assumption fails for about half of the edits by construction.
  §13 item 4 (PD:432) discloses misspecification only generally.
- **Fix:** state at PD:213-216 that the bound holds only if σ ≥ the edit's true paired sd. Say it fails for about half
  of edits by construction, so the paper does not claim α control for this arm. If finding 1 is resolved in favour of
  `PaceStyleGate`, say so instead.

**4. MINOR — FIXR3/EGATE edge cases are unspecified, so G3/G4 would have to invent rules.**
- PD:199-200: "at most 1 + 5 proposals" is false once failures occur (a failed first replicate costs one run, so
  3 + 1 + 1 + 15 = 20 allows eight executed proposals).
- No rule covers: a failure of replicate 2 or 3 (FIXR3); a failed candidate or incumbent replicate (EGATE); a Welch
  test with zero variance on both sides (possible with discrete metrics).
- **Fix:** add one sentence per case to §5.4/§5.5 (e.g. any failed replicate makes the candidate `failed_invalid`,
  charged for the runs it used; an incumbent replicate failure is a STOP; zero pooled variance means no keep). Reword
  the "at most" sentence.

**5. MINOR — the constants fitter reads more than PD §5.0 says.**
- PD:142-143 says the fitter "reads only the receipted sweep-2 train/dev partition".
- That partition holds only `label_block.traindev.jsonl` (`r1/c3/release.py:649-653`). Node, no-op and duplicate
  flags, weights and LADDER's Δ̂_p (PD:232) come from the sweep-2 proposal table. That table is D8-guarded
  (`analysis_guard.guard_table`) and also holds test-instance rows (in-campaign Δ̂, not labels).
- The function is `fit_a2` (`gate_input_builder.py:296`), not `_fit_a2` (PD:148, PD:406, PD:437).
- **Fix:** declare the table read, filtered to the P3 dev instances before use; check the table's sha256; fix the name.

**6. MINOR — signing order is ambiguous.**
- PD:17-20 step (3) fills "the sha256 placeholders of §14 that exist at signing". But R1-D3-MIN pins A1's constants by sha256 in the pre-declaration, and §10 (PD:357-358) STOPs on a mismatch. A
  placeholder filled after signing would change the signed file's hash.
- **Fix:** state that signing waits for the constants file, so it comes after the sweep-2 audit registration, the
  release and G2. Also state that no field changes after `frozen: true`. AN's P3-before-P4 order already matches.

**7. MINOR — the script does not bind the declared repetitions or A6's entry, although PD:334-335 says it refuses
undeclared repetitions.**
- `d3_analysis.py:221-223` accepts 1 or 2 from the table itself, and `:218-220` accepts either D.3b arm list. So a rep 1 added after outcomes exist (PD:428-429: "descriptive only") could be analysed as primary, and dropping
  A6 would shrink the Holm family.
- **Fix:** add a `REPETITIONS` constant fixed at signing, like `LLM_CALL_CAP`, and refuse other values. Require the
  D.3b note to state, before launch, whether A6 enters, and have the outcome-table builder write it.

**8. MINOR — the engineering smoke's instances are not declared.**
- PD:390-392 and AN P7 (AN:52) require a 2-instance smoke per arm but give no seeds.
- **Fix:** name its seeds outside all three D.3 blocks (e.g. a sweep instance seed or a new reserved block added to
  `check_namespaces`). Say its outputs are ENGINEERING_ONLY and may set only walltime and the projection.

**9. MINOR — §13 omissions.**
- Items 2 (sidedness), 6 (`openml_wdbc`) and 3 (once finding 7 is fixed) change `d3_analysis.py` constants and
  therefore its sha256 pin. Only item 1 says so.
- Item 9 and the G9 part of item 16 have no recommended value. Item 4 should add the finding-1 option, and the
  edge-case rules of finding 4 should appear as choices.
- **Fix:** add these points.

**10. MINOR — the D.3a note is missing preconditions.**
- No P item extends `check_namespaces` to the harness `vary` verify seeds (PD §13 item 12). No P item requires `d3_analysis.py` (this pinned sha) and its tests to pass at the launch commit. P4 covers only the
  pre-declaration.
- `layout_chunks: 42` (AN:42) assumes one repetition.
- **Fix:** add P items for both; make `layout_chunks` depend on the signed repetitions.

## Notes

- **NOTE 1** PD:386: "≈ 60.2 with A6" should read 60.3 (3 × 20.10).
- **NOTE 2** PD:298-300: sd(D) is the within-node sd, assumed equal across nodes. With a t reference the MDE is 0.314.
  For D.3b, Holm's first step is α/4, giving an MDE of 0.297. Say so.
- **NOTE 3** PD:293: df = Σ(m_n − 1) assumes equal within-node variances (a pooled df). This is acceptable as declared;
  Satterthwaite would be the unequal-variance alternative. Descriptive mention only.
- **NOTE 4** `d3_analysis.py:350-353`: if se = 0 and the estimate ≠ 0, p = 0 and Holm rejects. The PD does not state
  this; declare it.
- **NOTE 5** `validate_table` does not check that `ended_on` agrees with the counts (`worker_runs` = W ⇔
  `worker_runs`; `llm_calls` = cap ⇔ `llm_call_cap`) or that `no_fundable_candidate` occurs only for FIXR3/EGATE
  (PD:137-138). These are cheap checks to add.
- **NOTE 6** PD:103: "train seed = split seed = the instance seed" for every in-campaign run reads as including
  replicate runs. State that replicate j runs with train = split = its replicate seed.
- **NOTE 7** The harness `campaign_id` is the instance id for every arm and repetition (PD:105). Its ledgers and
  `*_pending.json` guards are keyed by it, so the G1 spec should require a separate ledger root per (arm, repetition).
- **NOTE 8** `check_namespaces` hard-codes most reserved intervals (`d3_analysis.py:109-124`); only T1, exam and
  7001–7010 are cross-checked against modules in the tests. Import the rest (noise-floor `SEED_BASE`, e1b
  `AUDIT_SEED_BASE`, `PROMPT_MEASUREMENT_SEEDS`, `G1B_SEED_BLOCK`) to prevent drift.
- **NOTE 9** `load_table` (`:281-287`) reads the whole file before validating, and refusal messages echo header keys
  and row values. Only filenames are screened (`:171-189`). Write the output with `open(..., "x")` rather than
  `exists()` then `write_text` (`:450-463`).
- **NOTE 10** AN's key block omits the house fields of `c3_sweep2_20261119.md` (`layout_request_disk_kb`,
  `layout_request_memory_mb`, `layout_wall_hours`). Add them as `<pending>`. Nothing in AN is presented as signed:
  `approved: false`, every P item is PENDING, and the hash placeholder is present (AN:24).

## Could not check

- The harness `vary` verify-seed derivation, and whether the harness counts controller-issued replicate runs against
  `max_worker_runs`: `autoresearch` is not installed here (PD §13 item 12; finding 2).
- The per-memory-mode duplicate share, and any sealed or label content (not opened by design).
- The PACE full text.
- Whether the R1-BX-D8 confirmation that the fitter's table read needs is in place.
