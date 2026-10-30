# Track S S0.3 code acceptance (independent, read-only), 29 Oct 2026

AI-assisted review (Claude). Paper `trackS-20261029` @ 1a02168; harness `trackS-20261029` @ 115df37 (f8bc222, 115df37 over 6adf385). Spec: runbook rev. 7.3.
Tests: paper `r1/tests/test_tracks_*.py` **135 passed**; harness `tests/stage2/test_r1_track_s_arms.py` **14 passed**.
Scratch end-to-end: `/tmp/trackS_e2e/e2e.sh` (full D2 sizes: 15×20 statics → `analyze select` → 4 centred members × 40 → π\* → S3e n = 300 with π\*, m\*, matched static, exact placebo (10), descriptive placebo (15) → `analyze analyze`).
- P2+ concentrated (0.012, W 10): m\* `static:0,-0.00165`, π\* = keep+ (the right channel), mean D 0.00228, LB 0.00087, **route A**, placebos pass.
- N0 (W = cap): **no gain found** (mean D −0.00035, UB 0.00016).

**Verdict: REVISE (narrow).** 0 BLOCKING, 6 MAJOR, 9 MINOR. S0.1 may start once MAJOR 6 is fixed. The other MAJOR items have to be fixed before S0.5b, S0.8 and S3e.

## Earlier review (1 BLOCKING, 6 MAJOR, 9 MINOR): all resolved
- **Resolved:** B1 (phase-keyed, disjoint audit blocks), M1, M2, M3 (rev-7 worlds; the e2e run selects keep+ on P2+), M4, M5, M6, m1, m2, m4, m5, m6, m8 and m9 are fixed and tested.
- **m3** is resolved only in part: `llama_build` "unknown" is still accepted (`collect.py:617–627, 1430`).
- **m7** is resolved, but see MAJOR 6.

## Q1. Phase coverage
Each of these has a tested code path with the declared parameters:
- **Phases:** S0.4, fit_prior, S0.5 (policy/rep pairs, calibration rows with strata), S0.5b truncation, S0.7 and S3e.
- **Tuning grid:** 15 statics including g = 0, on 20 instances; 4 centred members on 40 paired instances, the first 20 shared.
- **Seeds and verify:** seed and audit blocks are disjoint and bounds-checked. Verify is refused.
- **Operators and r:** ≥ for execute and > for keep. r = runs_left/W − proposals_left/N_cap. The collector, the oracle and the simulator agree to 1e-12.
- **Placebos and Holm:** exact and descriptive placebos, Holm by p, and the three outcomes plus "not run".

Gaps: the S0.5b decision quantities (MAJOR 5), n = 300 (MAJOR 4), and the π′ and A2-U secondaries (MINOR).

## Q2. End to end
It works: the outcome is A on P2+ and "no gain found" on N0. No checked-in test covers collector → analysis. The glue had to be done by hand: concatenating `roots.jsonl` from separate out-dirs into `dev_roots.jsonl` and `campaign_roots.jsonl`, and using a separate out-dir per placebo (MINOR 1).

## MAJOR
**1. S3e audit noise is shared across instances.**
- Real-node audits use salt 0 (`collect.py:331`) and the same 5 seeds 33401–33405 for all 300 instances (`:107–111`). Each configuration therefore carries one fixed audit error over the whole S3e sample.
- The MLP nodes have about 3 keys, and their configurations recur. So mean D contains a config-frequency × audit-error term that does not shrink with n, and the paired t ignores it.
- The term is comparable to δ_Y when the configuration × split sd is a few 1e-3: tabular's split sd under `vary` is 0.0123.
- S0.6 does not model it: synthetic audits are salted per instance (`synthetic.py:134`). Under N0 this can inflate route A.
- The runbook text ("mean over K = 5 audit seeds from the S3e audit block") permits it, so this is an **author decision**.
- *Fix:* draw per-instance audit seeds from an S3e block of size n·K, shared by every policy on that instance (pairing is kept), and record them. Do the same for tune.

**2. The repetition conventions conflict.**
- The collector counts from 0 (`collect.py:1233`; `schema.py:143`). `analyze.rep_of` returns `int(rep or 1)` (`analyze.py:1090–1091`), so collector reps 0 and 1 both become 1, and the descriptive placebo needs collector rep 2.
- Checked: the natural `--rep 1` second repetition gives exact placebo **STOP** (15 mismatches) and descriptive "missing", which voids S3e.
- *Fix:* one convention, with a test on collector output.

**3. The primary D averages m\*'s repetitions.**
- `per_instance_means` averages over reps (`analyze.py:1098–1114`). With the descriptive placebo in `campaign_roots.jsonl`, D on those 15 instances is π\*(rep 1) − mean(m\* rep 1, rep 2). That is not the declared estimand.
- Checked: mean D moves from 0.00262 to 0.00228.
- *Fix:* the primary uses the primary repetition only.

**4. Sizing is still rev 7.1.**
- `plan_sizing` sets `n_run_target = min(formula, 300)` (`analyze.py:1464–1472`), and `simulate_controls --n-campaign` defaults to the formula.
- Checked in the e2e run: n planned 69, MDE reported at 69, and the warning "S0.6 must be re-run (300 ≠ 69)".
- *Fix:* n fixed at 300 in `SizingDecl`; MDE and the freeze check at 300; warn if n < 300; S0.6 default n = 300.

**5. The S0.5 / S0.5b decision computations have no code.**
- Missing: the W choice (≥ 50 % binding on both nodes, from `s05b_truncated.jsonl`), σ_cmp,vary (median paired sd of Δ̂ under `vary`), σ_D between policies and between repetitions with the χ² 80 % UCL at the chosen W, and the calibration gate ([0.70, 0.90] overall and in every stratum with ≥ 20 predictions, with one inflation revision).
- The building blocks exist (`a2u.coverage`, `analyze.sigma_D_ucl`).
- *Fix:* an `s05b_summary` CLI with tests.

**6. The S0.1 probe cannot see cache-order nondeterminism.**
- Repeats run in the same order (`determinism.py:148–158`), so prompt i always follows prompt i−1. This masks KV/prompt-cache-dependent differences, and it does not exercise the planned two campaigns per server.
- The payload adds `max_tokens = 512` (`:42–43`); the harness sends none.
- The report records no GGUF sha256, llama.cpp build or server arguments.
- *Fix:* permute the order per repeat (with a recorded seed), add `--clients-per-url 2`, match the harness payload, and record provenance.

## MINOR
1. There is no `assemble` step or test from collector out-dirs to the analysis inputs, and how to run the placebos is undocumented.
2. The π′ handoff is broken. The analysis writes `tracks_policy/v1` (`analyze.py:1043–1065`), but `pi_prime:` loads only `tracks_score_model/v1` (`a2u.py:407`). The S0.3 nesting test is missing.
3. The secondary "m\* vs A2-U at the declared g" is not in the analysis, and `a2u` campaigns are ignored.
4. `analyze_s3e` combines the dev labels into the S3e label (`analyze.py:1560–1561`). The primary can therefore never be EVIDENCE while S0.7 is ENGINEERING_ONLY. `--label` is not validated (`collect.py:1506`).
5. `test_tracks_worlds.py:25` loads the analysis from the external `/home/claude/work/apb_analysis` and skips silently without it. It should load from the repo.
6. The "S3e flip rate" is computed on dev states (`flip_rate_S3e_dev`). Rename it or compute it on fresh π\* decisions.
7. Leftover route-B and stale text: `analyze.py:1346` ("B condition"), `:1169` ("12-configuration grid"), references to `ANALYSIS_NOTES.txt`, and line 1 of `ANALYSIS_NOTES.md`.
8. `host` is not a resume key (`MANIFEST_KEYS`, `collect.py:1194`). The ordering "exact placebo first" is not enforced.
9. The S0.5 `--rep` applies to every instance; the 10-instance repetition subset needs its own out-dir.

## Q3. Silent bias of the primary estimand
- Pairing is otherwise exact: same seed key, worker and split seed, start files, LLM seed base and audit seeds per instance, and byte-identical ledgers for identical rules. This was tested.
- Dev and S3e instance blocks are disjoint, with an overlap check. Audit blocks are disjoint across phases.
- The outcome logic matches §3.
- Remaining risks: MAJOR 1 (audit-noise sharing), MAJOR 3 (rep averaging) and MAJOR 2 (pairing or false STOP). Provenance labels err conservative (MINOR 4).

## Q4. First host run (S0.1 on TASL-2 / TASL-7)
- The probe CLI (serial and concurrent) and the collector CLI with llama.cpp wiring are present: `--manager llamacpp`, `seed_key`, transport retry, optional grammar, and refusal without GGUF, build and host.
- Resumability is present: commit marker, dedupe, retry cap, truncated-line repair and deadline.
- Server launch (`-np 1`) is up to the operator.
- Required before S0.1: **MAJOR 6**.
