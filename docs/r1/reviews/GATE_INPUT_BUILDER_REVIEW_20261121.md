Reviewed base: `471b6824` (the accepted P3 split unit on `mac-p3-split-20261121`, over published `main` `f6baf12c`); accepted at `f99467573c101a1d2249f7de33312023265e64ef` (`r1/c3/gate_input_builder.py` sha256 `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`)

# Independent review record — the gate-input builder (§3, PRE-MEM C, PRE-DUP A, PRE-DIV A)

**Unit.** On `mac-p3-split-20261121`: `r1/c3/gate_input_builder.py`, `r1/tests/test_gate_input_builder.py` and
`docs/r1/reports/gate_input_builder_20261121/GATE_INPUT_BUILDER_20261121.md`. Authority: the signed preregistration (R1-SWEEP2-PREREG)
§3, §4–§6, §9 and the decisions PRE-MEM C, PRE-DUP A, PRE-DIV A, PRE-A2 C, PRE-DELTA A, PRE-T1 A, PRE-WDBC B, PRE-SPLIT A; the
queue of 21 Nov 2026, item 2.

**Process.** One independent reviewer for all three rounds, read-only, synthetic data only, scratch under `/tmp/rev_gib/` moved to
its `_to_delete/`. Round 1 found one blocking issue (a missing label or evaluation row dropped silently instead of being refused),
three majors and ten minors, and judged one reading (an inert-mass override on A5) to change declared content; all were fixed in
`3a255fef` (A3/A5 now get only the rule layer). Round 2 accepted with three minors, fixed in `f9946757`; round 3 confirmed. During
round 1 the author's agent wrote unrelated next-unit changes into the same worktree; the reviewer read only committed bytes, and
later rounds ran on a clean tree.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ad71f905` | NOT ACCEPTED (B1; M1–M3; m1–m10) |
| 2 | `3a255fef` | ACCEPTED (3 minors) |
| 3 | `f9946757` | CONFIRMED |

**Open items.** The nine readings and the two author-matter conditions in the report are for the coordinating chat to confirm with the freeze; the reviewer judged all nine faithful in round 2. Interface condition (reading 8): a sweep-2 or G.5 evidence writer that admits divergent seeds must emit `divergent_seeds` with `k_evaluation`.

## Round 1 (`ad71f905`)

> **Verdict: NOT ACCEPTED.** There is one blocking finding. The §3 arithmetic is otherwise right: I checked it against an independent hand computation that included weights other than 1 and a weight-0 audit, and it matched exactly.
>
> Reviewed: `ad71f905` against `471b6824`, all files read via `git show ad71f905:`. The unit's tests give **20 passed** with the command you gave.
>
> **Not my change:** while I was reviewing, someone else modified the worktree `/tmp/pb/wt/p3`. Ten tracked files appeared modified at about 19:59–20:01 CET: `audit.py`, `env.py`, `ni_masking.py`, `offline_eval.py`, `train/sft_data.py` and five tests, adding `release.guard_raw_label_path` calls. When I ran pytest the tree was clean and HEAD was `ad71f905`. The builder file itself was not touched, and the `offline_eval` change is only inside `assemble`, so my results stand. I wrote nothing to the repository.
>
> **What is correct**
> - **Utility:** U = 20·Σwr/Σw per instance and mode, with r = Δ_true·keep − g·execute (`skip_credited_at_g`).
> - **Weights:** offline_eval's weights are computed per (source, node) stratum before any PRE-DUP drop, so kept weights are not recomputed. No-ops and within-campaign duplicates weigh 1, are never executed and have r = 0.
> - **g and the oracle:** g = 0.1·σ_node. The oracle uses `soft_label(pooled_node, k_label)` and `decisions` with the rule layer and tau floor.
> - **Δ_true** comes from the evaluation block for all three splits.
> - **A2** is fitted per node on the dev label block of the gate sources only. Test labels and evaluation values cannot reach A2, A3, A5 or the A2 fit; I confirmed the existing tests pass on this.
> - **PRE-DIV A thresholds** are right (k ≥ 3 of 5, k ≥ 2 of 3; divergent gives r = −g·execute).
> - **PRE-DUP A:** train and dev blocks are identical in the primary and secondary runs.
> - **Blocks and seeds:** P3 blocks come from the pinned split file, and the seed sets are checked per tier, including the K = 6 case.
> - **Gate v3.1 validity:** the output passes the gate's own `_validate`. It has seven T0 nodes in the primary run and eight in the sensitivity run, `suite` null for T0 and suites from `SUITES` for T1. With the NumPy pin check patched out in scratch, `G._evaluate` runs on all three outputs.
> - **Determinism:** shuffling rows inside each source does not change the output, and every sum runs in sorted order.
>
> ### Blocking
> **B1 — A missing test label or evaluation block is not refused. It becomes a statistical STOP that cannot be undone.** `gate_input_builder.py:243-247` drops any non-inert, non-duplicate row that has no label row ("not in the population"), and lines 215-221/250 raise the stratum ratio to compensate. Nothing is reported.
> - Reproduced on synthetic data: I removed the test label and evaluation rows. The builder and `_validate` both accept the input, every test series is ≡ 0, and the report still shows test counts of 9.
> - On an otherwise eligible synthetic world, the gate then STOPs with "nonpositive test oracle-A2 denominator on IQM nodes [all 7]". Under §4 that is a statistical STOP: it needs an author row and the run can never be repeated. A partial omission instead biases U silently.
> - offline_eval is only safe here because `verify_evidence_completion` runs first; the builder has no equivalent check.
> - **Fix:** sweep-2 evidence is a complete population (`audit.partition_population`, inclusion probability 1). By default, refuse any gate-source non-inert, non-duplicate row without a label row and an evaluation row. If sampled designs must stay possible, put them behind an explicit flag, refuse any node×split that has non-inert rows but no labelled ones, and report n_noninert and n_labelled per (source, node, split). Add a test for the missing test block.
>
> ### Major
> - **M1 — A frozen T1 node with no rows disappears silently** (line 352 loops only over `sorted(by_node)`). With `Tier1(suites={"mlab_cifar10":…})` and no rows for it, the node is not supplied and `t1_not_supplied == {}`. **Fix:** loop over `set(by_node) | set(t1.suites)` and report or refuse nodes without rows. PRE-T1 freezes the T1 set.
> - **M2 — The primary T0 set is hard-coded to seven nodes** (lines 67, 328, 429-431). PRE-WDBC B says the primary is "seven, or eight if the rerun gives 8/8, recorded in the arms-frozen record", but this file's sha256 is frozen before that. **Fix:** make the primary T0 set a required argument of `runs()` and `build()`, taken from the arms-frozen record. Report when the sensitivity run coincides with the primary.
> - **M3 — Reading 4 changes A5's beliefs and needs an author decision** (line 311; docstring lines 20-21).
>   - The no-op half (no-op → inert) is faithful: `arms.rule_skip` is the rule layer "A2 and above", and `decisions` already skips duplicates.
>   - The other half, zeroing and renormalising A5's inert mass on non-rule proposals, is A2/A3's prior override. C3_DESIGN §5 does not give it to A5, whose Stage-2 plug-in uses π = 1{b = inert}.
>   - **Fix:** either apply only the rule layer to A5, or have the author confirm the override and record A5's exact decision layer in the arms-frozen record. That should state whether the override comes before or after the dev calibration and the PRE-SELECT RPS.
>
> ### Minor
> - **m1 — Rows of an undeclared memory mode are silently ignored** (lines 386-387). I added `full_history` rows with labels and evaluations; they were accepted and had no effect. **Fix:** refuse undeclared modes unless `modes=` is given, or at least count them.
> - **m2 — Weight counts depend on how the caller packages sources** (lines 215-221). They are taken per `Source` object, not per stratum over the whole table. Splitting one stratum into train/dev and test `Source`s, as the PRE-STAGE partitions suggest, changed the weights in my sampled-stratum check (−0.002 vs −0.00214). The effect is zero when the population is complete. **Fix:** count across all gate sources by (source, node), or refuse a stratum that spans two `Source`s.
> - **m3 — DI-selected audits are handled differently from offline_eval.** `n_aud` counts DI-selected labels, while offline_eval's non-evidence path counts only random audits (line 220). `fit_a2` drops DI rows (line 274), while offline_eval trains on them with weight equal to the ratio. Evidence label rows carry no `audit_reason`, so this does not matter today. **Fix:** refuse `audit_reason` in evidence label rows, or mirror offline_eval.
> - **m4 — Reading 2 extends PRE-MEM C past its text** (lines 391-392). The signed rule applies the fallback "under PRE-DUP A"; the builder applies it in every block and for any cause, such as a missing campaign. The report's claim that it "does not occur" is unverified. **Fix:** allow the fallback only for test under `population="primary"` and refuse elsewhere, or get the author's confirmation.
> - **m5 — PRE-DUP also drops no-ops and within-campaign duplicates, and this reading is not listed** (line 372). It is the literal text and r = 0 for every series, but it rescales each instance's U and so the weighting across instances. **Fix:** add it to the report's readings.
> - **m6 — The A2 pooled fallback is an unlisted reading** (line 350; `arms.py:129`). A gate node with no labelled non-inert dev proposal gets the cross-node pooled constant, which goes beyond PRE-A2 C. **Fix:** refuse, or list it as a reading.
> - **m7 — A T0 node whose test block PRE-DUP empties raises an input refusal that nothing can fix** (lines 405-406). **Fix:** document it as a STOP-equivalent or ask the author.
> - **m8 — Label partial and divergent counts are not reported** (only the evaluation PRE-DIV counts are, lines 375-376). **Fix:** add them for §7.
> - **m9 — `divergent_seeds` is trusted without a cross-check** (lines 170-179; reading 8). A writer that leaves the field out under-counts partials. **Fix:** require a `k_evaluation` field equal to the number of seeds minus the divergent ones.
> - **m10 — The sources are not checked.** Several `gate=True` sources are allowed, so sweep 1 passed with `gate=True` by mistake would enter the test population, against PRE-MEM ("sweep 2 only"). Leaving sweep 1 out silently reduces PRE-DUP drops. **Fix:** check the gate sources' `row["source"]` against the declared set, and report which sources contributed repeat keys and how many.
>
> ### The eight readings
> 1. A2 fitted on the full dev population: **faithful**.
> 2. Mode fallback in every block: **goes beyond the text** (m4); narrow it or get author confirmation.
> 3. Sensitivity run uses the PRE-DUP primary population: **faithful**.
> 4. Override applied to A5: the no-op part is faithful; the inert-mass part **changes declared content and needs an author decision** (M3).
> 5. Label-divergent proposals never executed by the oracle: **faithful** (action target u = −g means skip).
> 6. T1 node with an empty block not supplied, T0 refused: **faithful**, since the gate forces it. But a frozen T1 node with no rows goes unreported (M1), and the T0 case cannot be fixed (m7).
> 7. Population = table rows, as offline_eval: **faithful**.
> 8. `divergent_seeds` field: **faithful as an interface condition**; add the cross-check (m9).
>
> ### Tests
> - **Renormalisation** (`test_pre_dup_renormalises_kept_weights`, :181-198): every ratio is 1, so it cannot tell kept weights from recomputed ones. Use a sampled stratum with ratio ≠ 1.
> - **Oracle by hand** (:102-123): it is independent of the builder, which is good, but all weights are 1 and sigma_cmp = sigma_node. Add ratio ≠ 1, a DI weight of 0 and sigma_cmp ≠ sigma_node; my scratch check did this and matched exactly.
> - **Evaluation values** (:144-148): the comment says evaluation values move realised values "not decisions", but the test only asserts that the oracle changed. Check that decisions are unchanged, for example U shifting by exactly 20·c·keep-share.
> - **Divergent counts** (:210): only the keys of `divergent_executed` are checked.
> - **Trivial assertion** (:245): `is not None` cannot fail.
> - **Order test** (:248-255): it does not permute sources or split a stratum across sources.
> - **Expected values from the builder:** the fallback and label-divergence tests take their expected values from the builder's own `modes=` path. That is consistent but not independent.
> - **Missing cases:** missing test blocks (B1); a frozen T1 node without rows; an undeclared mode; `runs()` with an 8/8 primary; the g = 0.05/0.2 runs; partial-label width (k_label = 3); the A3/A5 override; refusals for bad k_label, sigma mismatch, a no-op with an evaluation row, an evaluation row without a label row, and unused label rows.
>
> Scratch is in `/tmp/rev_gib/_to_delete/` (`checks/c1.py`–`c4.py` and `t/`). Nothing was deleted, and I opened no real data, sealed files or secrets.

## Round 2 (`3a255fef`)

> **Round 2 verdict: ACCEPTED.** Every round-1 finding is fixed in `3a255fef`. No blocking or major findings remain; three minor ones below. The worktree stayed clean throughout (HEAD `3a255fef`, empty status), and no apology was needed.
>
> **Tests:** 40 passed under `/tmp/tgport312` (NumPy 2.5.4) and 40 passed under `/tmp/np244` (NumPy 2.4.4). A synthetic `build()` output is byte-identical under both NumPy versions (same sha256).
>
> **How each round-1 finding now stands (checked in code and with my own synthetic checks):**
> - **B1, fixed:** a gate-source non-inert, non-duplicate row without its label row is refused (`gate_input_builder.py:265-266`), and so is one without its evaluation row (:182-183). A label row with `audit_reason` is refused (:158-159). All weights are therefore 1. The missing-test-block case now raises "complete population"; it is tested at :340-348.
> - **M1, fixed:** the node loop runs over by_node ∪ t1.suites ∪ t0_nodes (:369). A frozen T1 node without rows is reported as `["no rows"]`, and a T1 node lacking a train or dev instance is reported before the A2 check.
> - **M2, fixed:** `t0_nodes` is keyword-only with no default. `runs(primary_t0=)` accepts only the seven or all eight and sets `equals_primary`; both cases are tested.
> - **M3, fixed:** A3 and A5 get only the rule layer (no-op → inert), and their predictions are otherwise used as given (:296-305). I checked that an A3 prediction with inert mass on a non-no-op is honoured.
> - **m1, fixed:** undeclared modes are refused. Under `modes=` they are counted, and a mode outside the declared set is refused.
> - **m4, fixed:** the fallback is allowed only in the test block of the primary run (:417, :436). A mode with no rows is refused elsewhere; tested.
> - **m5:** listed as reading 9.
> - **m6:** no pooled fallback; the node is refused and the report lists it as an author matter.
> - **m7:** documented.
> - **m8:** label_partial and label_divergent are reported.
> - **m9:** `divergent_seeds` and `k_evaluation` must come together and agree; tested.
> - **m10:** source names are fixed, `sweep1` is required for T0, and the tier is checked per source. A `sweep1` row on a T1 node is refused; I checked that in scratch.
> - **m2 and m3:** no longer apply, since weights are 1 and DI rows are refused.
>
> **My independent checks:** A2 computed by hand (per-node mean of the dev non-inert soft labels, inert bin zeroed, then `rules.decide` with sigma_cmp) matches the builder to 7e-18 across train, dev and test. The per-mode secondary run works.
>
> **The nine readings:** all are now faithful to the signed text. Reading 4 (A5 as given plus the rule layer) follows `arms.rule_skip`, which is the rule layer for "A2 and above". The two author-matter conditions are correctly framed as refusals that no input fix can remove: PRE-DUP emptying a T0 test block, and a node with no labelled non-inert dev proposal.
>
> **Minor (none blocks acceptance):**
> 1. **A2 has no hand-computed test.** `r1/tests/test_gate_input_builder.py:167-184` only checks that A2 doesn't change when non-dev labels change. Add a test that computes A2 by hand; my scratch version matched to 7e-18.
> 2. **`primary_dev_population` skips the new source rules** (`gate_input_builder.py:498-513`). It does not require `sweep1` and does not check tiers, unlike `build`. Reuse the same source and tier validation there.
> 3. **Duplicated check:** the source-name check appears twice (`build` :349-351 and `_prepare` :206-208). Harmless; keep one.
>
> Scratch is in `/tmp/rev_gib/_to_delete/round2/` (`r2/c5.py` and `t2/`); round 1's is in `/tmp/rev_gib/_to_delete/`. Nothing was deleted, and only synthetic data was used.

## Round 3 (`f9946757`)

> **CONFIRMED** for `f9946757`. The three changes do what the round-2 minors asked for and change nothing else.
>
> **Tests:** 41 passed under `/tmp/tgport312` (NumPy 2.5.4) and 41 passed under `/tmp/np244` (NumPy 2.4.4). `TMPDIR` was under my scratch, and the worktree stayed clean (HEAD `f9946757`).
>
> **Builder sha256:** `git show f9946757:r1/c3/gate_input_builder.py | sha256sum` gives `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`, the value you stated.
>
> **The diff `3a255fef..f9946757`:**
> 1. **`test_a2_by_hand`** computes A2 without the builder or `arms`. It takes the mean of the dev non-inert soft labels, zeroes the inert bin and renormalises, then applies the rule layer and `rules.decide` with each row's sigma_cmp. It checks one train, one dev and one test instance at abs 1e-15. This is the same computation as my round-2 scratch check.
> 2. **`_check_sources` and `_source_row_ok`** are now shared by `build` and `primary_dev_population`.
>    - In `build`, the logic is unchanged: `need_sweep1` is `bool(t0_nodes)`.
>    - `primary_dev_population` now requires `sweep1` whenever T0 rows are present, and checks the tier of every row.
>    - Both new refusals are tested.
>    - `_prepare` still sets its own `tier`, which it uses for T1 handling and the per-row tier.
> 3. **The duplicate source-name check** is gone from `_prepare`. The only caller, `build`, still checks the names first.
>
> No new findings. Scratch is in `/tmp/rev_gib/_to_delete/round3/`; nothing was deleted.

---

Code-Commit: f99467573c101a1d2249f7de33312023265e64ef
Verdict: ACCEPTED

Accepted: `r1/c3/gate_input_builder.py` sha256 `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808` is the value for the preregistration's `gate_input_builder_sha256` field.
