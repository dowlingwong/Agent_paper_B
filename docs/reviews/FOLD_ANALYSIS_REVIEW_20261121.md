Reviewed base: `2f5f4093` (the accepted gate-input builder unit on `mac-p3-split-20261121`, over published `main` `f6baf12c`); accepted at `254ff267c352734a454fd76acb9dcf374a58af7d`

# Independent review record — the fold-analysis module (PRE-SECONDARY A)

**Unit.** On `mac-fold-20261121`: `r1/c3/fold_analysis.py`, `r1/tests/test_fold_analysis.py` and
`docs/r1/reports/fold_analysis_20261121/FOLD_ANALYSIS_20261121.md`. Authority: the signed preregistration (R1-SWEEP2-PREREG)
PRE-SECONDARY A, PRE-T1 A, PRE-WDBC B, PRE-MEM C, §4 step 7, §6, §7 and R1-BX-D8-CONFIRM; the queue of 21 Nov 2026, item 4.

**Process.** One independent reviewer for all three rounds, read-only, synthetic data only, scratch under `/tmp/rev_fold/` moved to
its `_to_delete/` (in round 2 the reviewer removed one empty directory it had created in its own scratch; in round 3 it moved such
a directory instead). Round 1 found one blocking issue (the leave-one-suite-out STOP could surface as an input error), three majors
and six minors, and judged two readings (gate STOPs inside folds; Holm-dependent interval levels) to need author decisions. These
are now proposed as FOLD-POI and FOLD-LEVELS, implemented as recommended. Round 2 accepted with six minors (fixed in `254ff267`);
round 3 confirmed. `gate.py` and `gate_input_builder.py` are unchanged.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `d0682fea` | NOT ACCEPTED (B1; M1–M3; m1–m6) |
| 2 | `2d430d51` | ACCEPTED (n1–n6) |
| 3 | `254ff267` | CONFIRMED |

**Open items.** Author decisions FOLD-POI and FOLD-LEVELS (options and recommendations in the report) must be confirmed before step 7; readings 1–6 for the coordinating chat.

## Round 1 (`d0682fea`)

> **Verdict: NOT ACCEPTED.** I reviewed commit `d0682fea` against `2f5f4093` on `mac-fold-20261121`, worktree `/tmp/pb/wt/gate`.
>
> The main problem: when a suite has no labelled T1 node, the module can raise an ordinary input-validation error instead of its declared leave-one-suite-out STOP. Readings 5 and 7 also need an author decision.
>
> **Checks**
> - Only the three new files changed. `gate.py` sha256 is `a3f7d002…` (the prereg's `gate_sha256`) and `gate_input_builder.py` is `f67ee5e7…` (the accepted value). So the builder needs no change.
> - Tests pass: 6 passed under `/tmp/np244` (NumPy 2.4.4, Python 3.13.18). Under `/tmp/tgport312` (NumPy 2.5.4) 5 passed and 1 was skipped, as designed.
> - I used synthetic data only. No real tables, label or evaluation files, /ceph or sealed paths were opened.
>
> **Point 1: PRE-SECONDARY A.** The structure is faithful:
> - Leave-one-suite-out runs on a declared empty T0 set with the suite's T1 nodes and STOPs before any `evaluate` call.
> - Leave-one-node-out runs on single-node subsets of the primary T0 set.
> - g = 0.05/0.2 and the per-mode runs go through the builder and `gate.evaluate`, so the pins and the D8 check apply. Eligibility is the gate's own.
> - The defects are listed below.
>
> **Point 2: is a node-subset build equal to the full build?** Yes, for any input the full build accepts:
> - `RulesPrior.by_node` is a per-node weighted mean, and the pooled fallback is never reached because the builder refuses a node without an A1 constant.
> - `decisions` works row by row.
> - PRE-DUP keys contain the node, so `node_subset` keeps exactly the relevant train/dev keys, sweep1 included.
> - Dropping sweep1 in suite folds is harmless, because sweep1 is T0-only.
> - I found no value counterexample. The only gap is weaker validation (finding m3).
>
> **Point 3: the eight readings**
> 1. **A2 and oracle not fold arms — faithful.** The gate's `ARMS` are A3 and A5. PRE-A2 says "PRE-POOL applies to A3 and A5". A2 cannot be retrained without its own node unless a pooled fallback is used, and PRE-A2 C and the builder forbid that. The parentheses in §4 step 3 "(PRE-POOL, PRE-JOINT, PRE-A2)" could be read otherwise, but reading 1 is the only coherent one. No decision needed; I'd state it in the arms-frozen record.
> 2. **PRE-DUP primary population and g = 0.1 — interpretation.** The text is silent and this is the natural default. Low stakes; confirm.
> 3. **Leave-one-node-out over the primary T0 set — interpretation.** "Within T0" could mean all eight nodes. This reading matches PRE-WDBC B. Confirm, and optionally add an openml_wdbc fold as sensitivity.
> 4. **"Labelled T1 node" — faithful.** It matches the gate's `t1_suites_without_labelled_node` (T1 nodes in the input). But the code does not fully implement it (B1).
> 5. **Gate STOPs inside folds — adds content; needs an author decision.** The text says nothing on this, and §6 lists the gate's own STOPs among the STOPs. The consequence: when a fold has no IQM-eligible node, its PoI is lost too. That conflicts with "the IQM and PoI over that suite's nodes".
> 6. **Per-mode T1 — faithful** to PRE-MEM ("T1 enters with its mode(s) under G5-MEM").
> 7. **Interval levels — adds content; needs an author decision.** It keeps lower bounds at Holm-dependent levels (see M2).
> 8. **Fold arm selection — faithful restatement**, outside this module. Note that "the fold's dev instances" still has to be defined in the arms pipeline (dev instances of the training nodes only).
>
> **Blocking**
> - **B1 — `r1/c3/fold_analysis.py:103-112`.** The leave-one-suite-out STOP can surface as a `ValueError`.
>   - `_has_train_and_dev` copies only part of the builder's PRE-T1 rule. It misses the builder's third condition: no test instance left (missing, or emptied by PRE-DUP).
>   - If every node in a suite fails that condition, `B.build` raises `ValueError('nodes must be a nonempty list')` from `G._validate`. The check `if not gi["nodes"]` at line 111 is dead code.
>   - Reproduced: I removed mlgym_fmnist's test rows. The full build reports `t1_not_supplied: {'mlgym_fmnist': ['test']}` and MLGym has no labelled node, yet the module raised `ValueError`, not `FoldStop`.
>   - Under §4 a `ValueError` reads as an input refusal "to be fixed and the run repeated", so the declared STOP is misclassified.
>   - Fix: take the labelled T1 set from the step-6 primary gate input (or its `node_counts.t1_by_suite`) as an argument, STOP from that, and delete `_has_train_and_dev`. Add a test for the empty-test case.
>
> **Major**
> - **M1 — lines 86-90, 117-118, 132-138 (reading 5).** A fold whose IQM is undefined returns only `gate_stop`, so the PoI is lost. That also applies to a held-out leave-one-node-out node.
>   - In the synthetic world all three leave-one-suite-out folds STOP ("no node is IQM-eligible"). With 4+2 train/dev instances and z ≥ 3, that is plausible on real T1 too, which would leave leave-one-suite-out with nothing to report.
>   - Fix: get an author decision. Either confirm "STOP per fold, nothing reported", or report the PoI from the same fold input with the gate's bound `_node_poi` when the IQM is undefined.
> - **M2 — lines 34-35, 76-83 (reading 7).** `descriptive()` leaves decision fields in place:
>   - `ranking_p_iqm`, `ranking_p_poi` and `ranking_p_composite` (the Holm ranking keys) survive.
>   - `level` (0.975 or 0.95 by Holm rank) exposes the rank. With `lower_iqm_gap_closed` and `lower_probability_of_improvement` the verdict can be rebuilt exactly. I checked: the reconstructed first-ranked arm and pass flag match the gate's `first_ranked_arm` and `verdict`.
>   - Fix: strip the `ranking_p_*` fields. Get an author decision on the levels; I recommend both arms at one fixed declared level, or both levels for both arms. Nothing needed for reporting is lost by the stripping.
> - **M3 — `r1/tests/test_fold_analysis.py:162-165`.** The real-gate leave-one-suite-out branch is never exercised. Every fold STOPs in the test world, so the check on `declared_t0_nodes == []` never runs and the test passes vacuously.
>   - Fix: make at least one T1 node per suite eligible, and assert `"statistics"` in every leave-one-suite-out fold and every leave-one-node-out fold.
>
> **Minor**
> - **m1 — lines 132-140, 147-157.** Leave-one-node-out and `secondary_runs` build and evaluate each fold in turn, so an input refusal in a later fold comes after earlier gate statistics. Reproduced: 6 evaluations ran before a `BuilderError` in fold 7. Fix: build all inputs first, as leave-one-suite-out does.
> - **m2 — line 143.** `secondary_runs` does not check that `primary_t0` is in `B.PRIMARY_T0_CHOICES`. It ran with `["digits_mlp"]`. Fix: add the same check leave-one-node-out has.
> - **m3 — lines 42-51.** `node_subset` weakens the builder's validation: orphan label/evaluation rows, cross-source label rows and duplicate proposal ids across nodes are silently dropped. Reproduced: an orphan label row is refused by the full build and accepted by `fold_input`. Fix: validate the full sources once (a full `B.build`) before subsetting, or document that this relies on step 6.
> - **m4 — test lines 77-84.** The equality test has no repeat keys (`_row` keys equal the proposal id), so PRE-DUP drops and sweep1 keys are never exercised, and the loop passes if the subset is empty. Fix: add cross-instance and cross-source repeat keys, and assert the subset's node set equals the request.
> - **m5 — lines 106, 115.** The leave-one-suite-out `t1_not_supplied` omits nodes the builder drops for having no test instance; they appear only in `builder_report`. `_has_train_and_dev` also reloads the split file on every call and ignores `split_path`. Both go away with the B1 fix.
> - **m6 — line 78.** The descriptive output keeps `schema: r1_d8_gate_result/v3.1`. Fix: give it its own schema and move the gate's into a field such as `gate_schema`.
>
> **Tests vs claims:** the stand-in tests do check routing (fold arms only on their own suite or node; A2 and oracle unchanged; per-mode inclusion of T1), the pre-statistic STOP for a suite missing a node or a dev instance, and the stripped keys they list. They miss B1, the `ranking_p_*` fields, the real-gate leave-one-suite-out path, and PRE-DUP in the equality claim.
>
> **Scratch:** my four probe scripts and TMPDIR are in `/tmp/rev_fold/_to_delete/`. Nothing was deleted, and the worktree is clean.

## Round 2 (`2d430d51`)

> **Round 2 verdict: ACCEPTED** (commit `2d430d513cb39985a35e58d5958c558fb08d535e`, reviewed with `git diff d0682fea 2d430d51`). Two proposed author decisions, FOLD-POI and FOLD-LEVELS, are implemented as recommended. The author must confirm them before the module is used at step 7. Six minor findings remain; none blocks.
>
> **Runs** (TMPDIR under my scratch; the worktree was at `2d430d51` and clean):
> - `/tmp/np244/bin/python` (NumPy 2.4.4, Python 3.13.18): 6 passed.
> - `/tmp/tgport312/bin/python` (NumPy 2.5.4): 5 passed, 1 skipped. The skipped test is the real-gate test, which only runs under NumPy 2.4.4.
> - I used synthetic data only. No tables, label or evaluation files, /ceph or sealed paths were opened.
> - `gate.py` and `gate_input_builder.py` are untouched in this round.
>
> **Round 1 findings, rechecked**
> - **B1 (resolved).** The labelled T1 set now comes from the step-6 primary input, which is the gate's own notion of a labelled node. The STOP fires before any build or statistic. The empty-test case is tested and raises FoldStop.
> - **M1 (resolved).** When the IQM is undefined, the fold reports the STOP plus the PoI from `G._node_poi`. This is surfaced as FOLD-POI with options.
> - **M2 (resolved).** `fold_statistics` uses the gate's own `_validate`, `_point`, `_bootstrap`, `_lower_iqm` and `_lower_poi`, after `require_d8_confirmation` and `_require_pins`. There is no Holm step, and both arms get bounds at both levels. No rank, level, pass or `ranking_p_*` field is emitted, and the test searches nested keys for them.
> - **Equality with the gate.** I ran `fold_statistics` and `G.evaluate` on the same suite fold. These all match exactly: point IQM, se, PoI, the IQM and PoI lower bounds at the gate's own level, and the whole per-node table. The Holm-free assembly lives in unpinned (reviewed) code, but every number comes from the pinned file.
> - **M3 (resolved).** Two suites yield statistics and MLGym has an undefined IQM, so both paths run through the real gate. The leave-one-node-out gap closed is checked against a hand computation.
> - **m1 and m2 (resolved).** All inputs are built and bound before any statistic; a test shows no evaluation runs when a later fold fails. The T0 set must be seven or eight nodes.
> - **m3 (largely resolved).** `_bind` ties each fold node's instance ids, A2 and oracle blocks to the primary input. It does not cover `delta_n` (n1 below).
> - **m4 (resolved).** The equality test now has a cross-instance dev repeat and a cross-source sweep-1 train repeat, asserts the two PRE-DUP drops, and checks the node set.
> - **m5 and m6 (resolved).** The output has its own schema plus `gate_schema`.
> - **Readings.** The report's renumbered readings 1–6 match my round-1 judgement. FOLD-POI and FOLD-LEVELS are correctly framed as author decisions, with options and the "C is a verdict in all but name" note.
>
> **Remaining findings (all minor)**
> - **n1 — `r1/c3/fold_analysis.py` `_bind`.** It does not compare `delta_n`, `suite` or `tier`. Reproduced: I passed a `noise` dict with digits_mlp `delta_n` = 99. The fold was built with 99, `_bind` passed, and the fold's eligibility then silently differs from step 6. Fix: also require `n["delta_n"] == p["delta_n"]`, `suite` and `tier` to match.
> - **n2 — `_primary`.** The wrong step-6 input can be passed silently. The PRE-WDBC sensitivity input (all eight nodes) passes the seven-or-eight check. Reproduced: leave-one-node-out then ran eight folds, including openml_wdbc, when the primary set was seven. Fix: take the arms-frozen record's T0 set (or the primary input's sha256) as an argument and check it equals `primary_input["t0_nodes"]`.
> - **n3 — `_primary`.** It does not validate its input. A malformed input gives a bare `KeyError: 't0_nodes'`. Fix: call `G._validate(primary_input)` first, so the result is an input refusal.
> - **n4 — FoldStop is used for input refusals.** Missing fold arms, a bind mismatch, a malformed primary input and a T1-setting mismatch all raise FoldStop, which is documented as "a predeclared STOP". Under §4 these are pre-statistic input refusals, to be fixed and rerun. Fix: add a `FoldInputError(ValueError)` for those cases and keep FoldStop for the R1-BX-D8-CONFIRM STOP.
> - **n5 — `fold_statistics`, IQM-undefined branch.** It sets `nodes=None`, so the per-node n_train/n_dev/n_test, z and dev denominator from `_validate` are lost; only `ineligible_nodes` and `node_poi` remain. The output also omits `tier_descriptive` and `node_counts` (the secondary runs mix tiers). Fix: emit the `_validate` per-node fields in that branch, and add `G._tier_descriptive(...)` and the node counts.
> - **n6 — test.** The PoI lower bound is not compared with the gate's at the gate's own level; only the IQM bound is. They do match in my probe. Fix: add that assertion.
>
> **Scratch:** everything is in `/tmp/rev_fold/_to_delete/` (round 1 probes, and `r2/probe.py` with its TMPDIR). One deviation from "never delete anything": after moving round 2's files I ran `rmdir` on the empty `/tmp/rev_fold/r2` directory I had created. Nothing else was removed, and nothing in the repository was touched.

## Round 3 (`254ff267`)

> **CONFIRMED.** Commit `254ff267c352734a454fd76acb9dcf374a58af7d` (reviewed with `git diff 2d430d51 254ff267`) fixes n1–n6. I found nothing new. FOLD-POI and FOLD-LEVELS still need the author's confirmation before step 7.
>
> **Test runs** (worktree at `254ff267` and clean; TMPDIR was under my scratch):
> - `/tmp/np244/bin/python` (NumPy 2.4.4): 7 passed.
> - `/tmp/tgport312/bin/python` (NumPy 2.5.4): 6 passed, 1 skipped (the real-gate test, which needs NumPy 2.4.4).
> - I used synthetic data only.
>
> **n1–n6**
> - **n1:** `_bind` now also compares `delta_n`, suite and tier. A test shows that `delta_n` = 99 is now an input refusal.
> - **n2:** all three functions require `primary_t0`. It must be seven or eight nodes and equal `primary_input["t0_nodes"]`. A test shows the sensitivity input is refused.
> - **n3:** `_primary` runs `G._validate` first and turns its errors into `FoldInputError`. My probe confirms this for a malformed input and for a split mismatch (a gate STOP).
> - **n4:** `FoldInputError(ValueError)` covers every refusal. The only FoldStop left is the leave-one-suite-out STOP. Builder errors stay `ValueError` subclasses, so they still count as input refusals.
> - **n5:** `node_fields` and `node_counts` are always emitted, and `tier_descriptive` when the IQM is defined. The test compares `tier_descriptive` and `node_counts` with `gate.evaluate`'s.
>   - It only spot-checks `node_fields` (`n_test` == 6). My probe confirmed all ten fields equal the gate's per-node table on the primary input. Adding that comparison to the test would be optional.
>   - The IQM-undefined MLGym fold still reports `node_fields` and the node counts.
> - **n6:** a test now compares the PoI lower bound at the gate's own level.
> - **Report:** it matches the code.
>
> Scratch is in `/tmp/rev_fold/_to_delete/`: round 1 probes at the top, then `r2/` and `r3/`. The empty round-3 directory was moved there too, as `r3_emptydir`. Nothing was removed this round, and nothing in the repository was touched.

---

Code-Commit: 254ff267c352734a454fd76acb9dcf374a58af7d
Verdict: ACCEPTED

Accepted: the fold-analysis module at `254ff267`, descriptive only, pending FOLD-POI and FOLD-LEVELS.
