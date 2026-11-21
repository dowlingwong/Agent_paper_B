Reviewed base: `cff56ae855e39cbbb272ffda5473f759a6a565c5` (branch `mac-trackp-p4-20261120` over `main` `94db94bb`; accepted in round 4)

# Independent review record — Track P P.4 test evaluator and the phase-1 P.4 authorization draft (approved: false)

**Unit.** `r1/c3/train/sft_test_eval.py`, `r1/tests/test_trackp_sft_test_eval.py` and
`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` (revisions 1–3) on `mac-trackp-p4-20261120` over `main`
`94db94bb`. Authority: RUNBOOK P.4, R1-C3-POOL(-EXAM), R1-C3-CONTROL, R1-CONTROL-READOUT, R1-TRACKP-SFT-DEV,
R1-TRACKP-SFT-DUP (heldout_excludes_seen), R1-MAIN-PROPOSER (e), R1-BX-D8-V3-A/B, R1-TRACKP-TASL2-HOST, R1-QTORCH-AMEND;
the queue of 20 Nov 2026, item 4 (P.4 SFT authorization draft and the test evaluator that applies the exclusion list).
The draft decides nothing: its author decisions (P4-PHASE1-TEST, P4-P1SPLIT, P4-ARMS, P4-HOST, P4-LC, P4-CAP) carry
options and recommendations; it is now scoped to phase 1 (sweep-1 ENGINEERING readiness) and lists what the evidence
note must decide.

**Process.** One independent reviewer (a separate agent that did not write the unit) for all four rounds; it edited
nothing in the worktree (scratch under `/tmp/p4rev/`), ran the suite and mutation checks in its own clone, computed
split overlaps from instance names and salts only, and read no label or evaluation values. In round 1 it removed one
scratch directory of its own, which it disclosed; from round 2 on it moved scratch to `/tmp/p4rev/_to_delete/`.
Round 4 confirms the test added after the round-3 acceptance. The round texts are reproduced below as delivered, as
block quotes.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `26c1cf43 (rev 1)` | NOT ACCEPTED (3 blocking, 7 major, 8 minor) |
| 2 | `75901a8e (rev 2)` | NOT ACCEPTED (1 blocking, 5 minor) |
| 3 | `ef600c5b (rev 3)` | ACCEPTED (1 minor) |
| 4 | `cff56ae8 (tests)` | ACCEPTED |

**Open for the author and the runner unit.** The six phase-1 decisions; prerequisites P1–P7 (the signed sweep-1 freeze,
P.3a records, the reviewed P.4 runner unit with the P3 split-file binding, the ledger directory per table, gradient
checkpointing behind `sft_gradient_checkpointing`, the bootstrap interval, the per-suite logging tick); the host tests of
§10. Reviewer notes n1–n4 (runner conventions: ledger directory, a write-ahead intent entry, a positive test for reads on
different material, the split-file binding when the build is not over the full universe).

## Round 1 (`26c1cf43 (rev 1)`)

> Reviewed base: 26c1cf43 (branch mac-trackp-p4-20261120; base main 94db94bb; PLAN/RUNBOOK checked at df58bcd5, identical to 94db94bb for both files)
>
> # Independent review, round 1: Track P P.4 test evaluator, tests, and authorization draft
>
> Reviewer: independent read-only reviewer (Claude), 21 Nov 2026. AI-assisted.
>
> Scope:
> - `r1/c3/train/sft_test_eval.py`
> - `r1/tests/test_trackp_sft_test_eval.py`
> - `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`
>
> Sources I checked them against:
> - `r1/c3/train/sft_data.py`, `r1/c3/train/sft.py`
> - PLAN.md and RUNBOOK.md at df58bcd5
> - `docs/r1/TRACK_P_POST_TRAINING.md` (the spec)
> - TASL-2 trial commit f557f985 (origin/ops-tasl-20261116)
> - Unit B result commit 2287e492
> - the sweep-1 freeze review on mac-sweep1-label-freeze-20261121
>
> What I ran:
> - The suite as instructed in the worktree: **56 passed**.
> - 26 mutations of the evaluator, run in a scratch clone (/tmp/p4rev/clone, `git clone --shared`). Results are in /tmp/p4rev/mutation_results.json.
> - A fixture probe: /tmp/p4rev/clone/r1/tests/test_zz_probe_rev.py, which exists only in the scratch clone.
>
> What I did not do:
> - I read no real label values and no evaluation values. The only check on the label block was its sha256, read from the committed SHA256SUMS.
>
> ## Summary
>
> The core exclusion logic of the evaluator is correct:
> - policy `heldout_excludes_seen`;
> - a key counts as seen if it appears on any table row of a train or val instance;
> - the recomputed list is compared with `splits.json`;
> - primary = labelled test proposals minus that list;
> - secondary = all labelled test proposals.
>
> The metric function is the Stage S `val_metrics`, and the base rate is computed from the training rows. Reading discipline for the label block is sound.
>
> The unit still cannot be accepted, for three reasons:
> 1. Three scientific-content choices in the draft are made silently, and they conflict with PLAN §10 or the spec:
>    - a phase-1 test read on the test partition that phase 2 shares;
>    - label-seed rather than `y_eval` test targets;
>    - a phase-2 split and data composition that conflict with the C3 gate's preregistered split.
> 2. The budget misstates a trial fact.
> 3. Several of the evaluator's own guarantees ("one read per arm", prompt binding, temperature binding) are weaker than the draft says. The tests leave the base rate, the "labelled or not" rule and the temperature application unchecked.
>
> ---
>
> ## Blocking
>
> ### B1. Phase 1 recommends a real-label test read on the test partition that phase 2 will use
>
> **Where:** draft:41-45 ("the test evaluator runs, and its numbers are ENGINEERING_ONLY"), draft:98-99, draft:115.
>
> **Problem.**
> - R1-MAIN-PROPOSER (e) says both sources use **one instance → train/dev/test assignment**.
> - Twin campaigns share instance seeds and audit seeds, so the same (instance, incumbent, edit) gets **the same label in both sources**.
> - (e) also says pooled versus sweep-2-only training "is fixed on validation **before any test read**". That clause is marked *(proposed)*, and the draft itself quotes it at draft:21 and draft:47-48.
> - The SFT builder's assignment is a fixed hash over the instance universe, so sweep-1 test instances are sweep-2 test instances.
> - A phase-1 test read on real sweep-1 labels therefore reveals test performance on the evidence test partition. It also happens before the phase-2 pooled-vs-sweep-2-only choice, the arm choice and the lr choice.
>
> Labelling the numbers ENGINEERING_ONLY does not undo that exposure. The draft offers this read inside the recommended option without naming the consequence. Option B's framing ("saves a few GPU-hours") also leaves out this cost of option A.
>
> **Fix.**
> - Remove the real-label test read from phase 1. In phase 1, exercise the evaluator only on synthetic labels, or on a synthetic test-like split.
> - If the author wants a phase-1 test read, make it a separate author decision (for example P4-PHASE1-TEST). State plainly that it uses up the phase-2 test partition before the pooled-vs-sweep-2-only choice.
> - Add a STOP: "any real-label test read before the phase-2 arm, data variant (pooled or sweep-2-only), lr, seed set, checkpoint and temperature are fixed".
>
> ### B2. Test targets: label-seed soft labels, where the spec declares `y_eval`; decided silently for the evidence phase
>
> **Where:** sft_test_eval.py:28-30 (and :211, `SD.soft_target` on the label-seed records); draft:139-140, draft:141-143 (the phase-2 CLI wiring), draft:186.
>
> **Problem.**
> - Spec §7.1 is headed "**Offline (test instances, `y_eval` only)** — Belief: RPS skill, NLL, all-bins and top-1 ECE, PIT histogram, width ratio". `y_eval` is the same construction on seeds 7006–7010 (spec §3.4).
> - R1-B2-DECOUPLE limits 7006–7010 to "B.2 task-level joint-seed retraining **and evaluation**, never C3/Track P training, tuning or selection". Evaluation on them is allowed.
> - The evaluator hard-codes the label seeds 7001–7005 as the test target and presents "no value from 7006–7010 is read" as a property of the phase-2 evidence number.
> - That is right for phase 1 under R1-TRACKP-SFT-DEV. For phase 2 it changes the declared test target, with no author decision.
>
> **Fix.**
> - Add an author decision P4-TARGET with a recommendation:
>   - (a) Phase 2 per spec §7.1: test belief metrics against `y_eval`. This needs a separately guarded evaluation-block path that runs only after the arm is fixed, in its own process, with its own review.
>   - (b) Amend spec §7.1 by a PLAN row to label-seed targets, and say why.
> - Keep the label-seed path for phase 1 only, and label it "phase-1 / ENGINEERING target" in the report (`test_target: y_train label seeds`).
>
> ### B3. Phase-2 split and data composition conflict with the C3 gate's preregistration, in which A5 is a gate arm
>
> **Where:** draft:87-91 ("Protocol (unchanged …)": split 8 nodes × 18 instances; 3 test, 3 validation per node), draft:46-48 (phase 2 = sweep 2 + sweep 1 stratum), draft:170-187 (key values cover phase 2).
>
> **Problem.**
> - R1-BX-D8 makes **A5 one of the two gate arms** ("pass if, for A3 or A5 … the lower bound of the IQM gap closed is > 0").
> - R1-BX-D8-V3-A (3): the gate split per tier is **P3 = 1/3 : 1/6 : 1/2**, provided by the caller and written into the analysis preregistration.
> - R1-BX-D8-V3-B (5): T0 needs **≥ 9 test instances per node**.
> - The SFT split is 12 : 3 : 3 per node. An A5 evidence checkpoint trained on it would be trained on most of the gate's test instances. And with 3 test instances per node, every T0 node falls below the gate's floor.
> - R1-BX-D8-CONFIRM pools T0 and T1 with tier as a stratum (gate read on CPU + T1 labels, R1-BX-D14). Phase 2 in the draft has no T1 labels and no tier stratum.
>
> **Fix.**
> - Either restrict this authorization to phase 1 and put phase 2 in a separate note,
> - or add an author decision P4-SPLIT that reconciles the A5 evidence split with the gate's preregistered split and with (e)1. It must also fix the phase-2 data composition: T0 sweep 2, sweep 1 as a stratum, and T1 labels with tier as a stratum.
>
> In either case, add a STOP: "the A5 evidence split differs from the C3 gate's preregistered split".
>
> ---
>
> ## Major
>
> ### M1. Budget: a misstated trial fact, an impossible learning-curve point, and unstated multipliers
>
> **Where:** draft:30-32, draft:76-85.
>
> **Problems.**
> 1. **Trial steps.** The draft says the trial "ran in 159 s (370 steps …)". Commit f557f985 records `total_steps 370`, but the run **early-stopped at step 126** (best step 90). So 159 s covers about a third of a full run.
>    - Real labels can stop later. A run that does not stop early would take roughly 7–8 min at 0.8B.
>    - On the draft's own 5× assumption that gives about 5.5 h (0.8B) + about 27 h (4B) ≈ 33 GPU-h. That is close to the proposed 40 GPU-h cap, not "about 13".
> 2. **Learning curve.** The curve is 250/500/1k/**2k**, but phase 1 has **1,176** training rows (R1-TRACKP-SFT-DUP). The 2k point cannot be run. Capping it at 1,176, or dropping it, is a silent protocol choice. The draft also does not say whether rule no-ops count as "examples".
> 3. **"4B bases: unmeasured".** P.3a trained qwen3.5-4b-base (and the Kev bases) on a 24 GB 4090 (attempt-1 native runs; campaign lease total about 130,925 GPU-s, Unit B 2287e492). Those E0-path records give real 4B step times and memory, with gradient checkpointing. The draft should cite them and not rely only on the parameter ratio.
> 4. **Phase-2 multiplier.** The "2–3×" leaves out:
>    - training both the pooled and the sweep-2-only variants, which doubles the lr grid;
>    - T1 labels (see B3);
>    - any leave-one-suite-out or LONO fold retraining (spec §7.2; R1-BX-D1 makes leave-one-suite-out primary).
>
>    Peak memory "16.5 GB" also misstates 16,511 MiB (= 16.1 GiB, 17.3 GB).
>
> **Fix.**
> - Restate the trial as "126 of 370 planned steps (early stop), 159 s wall".
> - Give the arithmetic for both an early-stopped run and a full 5-epoch run.
> - Size the cap on the full-run case, or say explicitly that it depends on early stopping.
> - Make the 2k point an author choice: cap at the full training set, or omit it in phase 1.
> - Cite the P.3a 4B timings.
> - List each phase-2 multiplier.
>
> ### M2. P4-HOST omits the main mitigation for the 4B memory risk
>
> **Where:** draft:65-68, draft:113.
>
> **Problem.** Trial finding 1 (f557f985) says `_stage_s` never calls `enable_gradient_checkpointing()`, although the host config sets `gpu.gradient_checkpointing: true` and the E0 path applies it. Enabling it "likely fit[s] micro-batch 8". 4B bases already trained on the 4090 in P.3a through the E0 path.
>
> The draft treats "OOM at micro-batch 1" as a STOP that moves the **whole table** to H200. That H200 path is "not ready now" and needs I2/I3, a smoke test, E0 equivalence and an HTCondor job. The decision is framed without the cheapest option, which is protocol-neutral.
>
> **Fix.**
> - Add option A′: a reviewed code unit that enables gradient checkpointing in the SFT path. It is a host-fit knob: the effective batch, loss and lr stay the same, and it is recorded in the manifest.
> - Run the memory probe with and without it.
> - Make the whole-table move to H200 the fallback only after A′ fails.
>
> ### M3. P4-ARMS option A can drop a control arm, which PLAN says is always carried
>
> **Where:** draft:54-55 ("minus any base whose P.3a record shows an E0 failure or an E4 hard limit").
>
> **Problem.**
> - R1-C3-POOL-EXAM applies the E0/E4 exclusion to the **Kev sizes** ("both Kev sizes go on … unless one fails E0 or an E4 hard limit; **the Qwen control is carried as before**").
> - R1-C3-CONTROL says "always carried as an ablation arm".
> - The draft's wording applies the exclusion to the controls as well.
>
> **Fix.** Limit the exclusion to kev-0.8b and kev-4b. State that the controls are always carried. If a control cannot be trained, that is a STOP for the author, not a silent drop.
>
> ### M4. "One test read per arm" is not enforced, and predictions are not bound to the arm's checkpoint or temperature
>
> **Where:** sft_test_eval.py:33, :189-190, :251; :167 (the header is trusted); :271-289; draft:98, draft:115.
>
> **Problem.**
> - The evaluator refuses only a non-empty `out_dir`. The same arm, or any number of checkpoints or temperatures for it, can be evaluated again into another directory.
> - `temperature`, `arm` and `model` in the predictions file are free-form and never checked:
>   - against `best/temperature.json`, which R1-TEMPERATURE fits on primary val;
>   - or against the selected run's `sft_report.json` or best-checkpoint manifest.
> - `predict_test` takes `temperature` from the caller.
> - Stage S reports metrics both before and after scaling, but one predictions file yields only one of the two. Reporting both would take two reads.
>
> The draft's STOP "A second test read of the same arm (the evaluator writes once)" says more than the code does.
>
> **Fix.**
> - Have `predict_test` take the selected run directory. It reads T from `best/temperature.json` and records the sha256 of `best/manifest.json`, `temperature.json` and `sft_report.json`. It writes the **logits** with T.
> - Have `evaluate_test` check those hashes and compute the raw and the T-scaled metrics in one read.
> - Add a test-read ledger keyed by (data sha, arm id, best-manifest sha) that refuses a second entry.
> - Or reword the STOP to say that the one-read rule is enforced by the P.4 runner (prerequisite P3), and name the mechanism.
>
> ### M5. `replay_test_prompts` drops the feature binding between each prompt and its table row
>
> **Where:** sft_test_eval.py:258-268. Compare sft_data.py:34-35 and :489-491.
>
> **Problem.**
> - The builder ties each replayed prompt to its table row by checking `features_hash(feats) == features_hash(table_row["features"])`. The sft_data docstring calls this "which binds each prompt to its table row".
> - `replay_test_prompts` throws away the replayed features (`replayed[pid][0]`) without that check.
> - It also takes `table_rows` from the caller, unpinned, instead of loading them with the data manifest's table pins.
>
> Prompts replayed from another build, featurizer state or ledger set with the same ids would pass, and so would the predictions made from them.
>
> **Fix.**
> - Take `table_dir` and load it with `SD.load_table(table_dir, pins=manifest["table"]["sha256"])`.
> - Check `features_hash` for every replayed test proposal, and refuse on any mismatch.
> - Record the replay inputs (index sha) in the predictions header, and check them in `evaluate_test`.
> - Add a test with one tampered feature.
>
> ### M6. The tests do not discriminate on the points that matter
>
> **Where:** the test file. Mutation results (/tmp/p4rev/mutation_results.json): 26 mutations, **9 survived**.
>
> | Mutation | Result | Why |
> |---|---|---|
> | Base rate replaced by uniform (M3) or by train+val rows (M4) | survives | test:128-134 takes the expected base from `TE.read_data_dir` itself, so the check is circular |
> | "Seen" from labelled rows only (M19); exclusion list limited to labelled rows (M25) | survives | test:95-104 is **vacuous**. In the fixture `hit` is empty (probe: 0 such keys; 1 excluded proposal; 0 unlabelled in the list; one node). The test also checks only the builder's `splits.json`, never the evaluator. |
> | `predict_test` ignores the temperature (M21) | survives | test:250 checks only the recorded `doc["temperature"]` |
> | Policy check removed (M5); `sweep` not compared (M7); completion sha not compared (M8) | survives | no test |
> | Sum tolerance loosened to 0.6 (M9) | survives | the only sum case is [0.5]×12; draft:144-145 claims "a loose probability check" mutation is caught |
> | `open("w")` instead of `open("x")` (M26) | survives | masked by the out_dir check (acceptable defence in depth) |
>
> Killed: primary = secondary, "seen" from train only, provenance on `kind` only, the shape/negativity/extra-id checks, the pins, the sha binding, suite-on-secondary, the evaluation-path refusal, and others.
>
> The fixture has one node, so `by_node` and `by_suite` are trivial, and the branch "groups present only among the excluded" (:228-230) is never run.
>
> **Fix.**
> - Compute the expected base rate from the training rows in `rows.jsonl` independently. Assert that skill against that vector is 0, and that skill against uniform is not 0.
> - Build a fixture with a test key that appears only on an unlabelled (`duplicate`) train or val row. Assert that the **evaluator** excludes it, and that M19/M25 fail.
> - Assert `predict_test` probabilities equal `softmax(predict_logits/T)`.
> - Add refusal tests for the policy check (a tampered `splits.json` plus a consistent manifest), the sweep mismatch and the completion-sha mismatch.
> - Add a test with a sum of 1 ± 1e-3.
> - Use a two-node fixture with one node present only among the excluded proposals.
> - Correct draft:144-145.
>
> ### M7. What the RL gate's "significantly" means, and phase-2 test reporting, are undefined
>
> **Where:** draft:15, draft:97; the evaluator returns point estimates only.
>
> **Problem.**
> - RUNBOOK P.4's RL gate needs "RPS skill > 0 **significantly**". The draft does not say on which population (primary val or primary test) or with which interval.
> - R1-MAIN-PROPOSER (e)4 requires an **instance-cluster bootstrap** for pooled intervals.
> - (e)3 groups cross-source duplicates by (instance, incumbent hash, edit hash). In a pooled table the twin proposals of a test instance appear once per source with the same label. The evaluator neither stratifies by source nor deduplicates them, so they would be counted twice.
> - Spec §7.2 (leave-one-suite-out primary, LONO secondary) is not addressed. The evaluator lists `holdout_nodes` but does not report held-out nodes separately from in-distribution test instances.
>
> **Fix.**
> - State the gate population and the test (instance-cluster bootstrap, B, level).
> - For phase 2, add to the evaluator: the source stratum, within-test cross-source grouping by the (e)3 key, the instance-cluster bootstrap CI for RPS skill, and separate metrics for held-out-node and in-distribution test.
> - Or record these as P3 runner-unit requirements in the draft.
>
> ---
>
> ## Minor
>
> ### m1. The exclusion list is recomputed, but the split it depends on is trusted
>
> **Where:** sft_test_eval.py:105-124.
>
> **Problem.**
> - The recomputation uses the **recorded** `splits.json` instances and the shared `SD.dup_key`. A consistently regenerated `splits.json` and manifest would pass.
> - The evaluator also skips checks that `load_sft_data` makes: the `prompt_version`/`featurizer_version` check, and the duplicate-`proposal_id` check on the table.
>
> **Fix.**
> - Recompute the assignment with `SD.assign_splits(union_of_recorded_instances, splits["config"], universe=union)` and compare it with the recorded lists.
> - Check `universe.sha256` and `n`.
> - Refuse duplicate table ids.
> - Check the two version fields.
>
> ### m2. A new gate is introduced as if it were existing
>
> **Where:** draft:46-47, draft:110-111.
>
> **Problem.** "Released to Track P by an author row (the sweep-2 analysis preregistration fixes when)", together with the STOP "a sweep-2 label read before the author row that releases sweep-2 labels to Track P", is a new gate. R1-TRACKP-SFT-DEV says "sweep 2 的 label 到位后直接开训" (train directly once the sweep-2 labels are in place), and R1-BX-D8-CONFIRM allows sweep-2 label tables to be analysed now. No PLAN row ties a Track P release to the preregistration.
>
> **Fix.** Mark it *(proposed, new gate)* and give the reason. Or drop it and cite the existing D8-CONFIRM and preregistration gates.
>
> ### m3. Per-suite logging precondition
>
> **Where:** draft:162-165; sft_test_eval.py:213.
>
> **Problems.**
> - No per-suite logging branch exists in any ref.
> - The draft names it as if it existed, gives no owner or unit, and makes it N/A for phase 1 on its own authority. Defensible, since T0 is one suite, but not stated as a choice.
> - A `suite_of` mapping silently maps unmapped nodes to "unassigned".
>
> **Fix.**
> - Say that the branch is still to be written, and by which unit.
> - Make "N/A for phase 1" an explicit author tick.
> - In the evaluator, refuse unmapped nodes when a mapping is given.
>
> ### m4. Citations
>
> **Where:** draft:159.
>
> **Problem.** `TRACKP_UNITB_TASL7_D2_RESULT_20261119.md` is only on origin/ops-tasl-20261116 (2287e492), not on main.
>
> **Fix.** Cite the branch and commit. (The "16.5 GB" correction is in M1.)
>
> ### m5. RUNBOOK P.4 says "temperature / isotonic recalibration"
>
> **Where:** draft:15, draft:18.
>
> **Problem.**
> - The draft silently drops "isotonic". That is correct under R1-TEMPERATURE, but it should say so.
> - R1-CONTROL-READOUT's secondary bin-token readout row for the Qwen controls is missing from the per-arm report list (draft:97).
>
> **Fix.** Cite R1-TEMPERATURE for dropping isotonic. Add the secondary readout row for the controls.
>
> ### m6. P4-HOST B for an EVIDENCE table
>
> **Where:** draft:69-71.
>
> **Problem.** R1-TRACKP-TASL2-HOST lists TASL-2 and TASL-7 as the Track P evidence-table hosts. R1-QTORCH-AMEND and R1-HTC-QTORCH permit cluster training after the checks.
>
> **Fix.** State whether phase-2 evidence on H200 also needs an author row naming H200 as an evidence host.
>
> ### m7. Robustness details
>
> **Where:** sft_test_eval.py:163, :148, :188-191, :250.
>
> **Problems.**
> - A non-numeric prediction entry raises a bare `ValueError`, not a `TestEvalError`.
> - `data_dir` and `out_dir` are not passed through `refuse_sealed`.
> - NaN metrics (all-inert groups) are written as bare `NaN` in JSON.
>
> **Fix.** Wrap the conversion in `TestEvalError`. Call `refuse_sealed(data_dir, out_dir)`. Write null for NaN.
>
> ### m8. R1-TRACKP-SFT-DUP wording
>
> **Where:** draft:20.
>
> **Problem.** The PLAN text excludes held-out proposals that duplicate "the training set" (训练集). The builder and the evaluator exclude test keys seen on train **or val**. This is reasoned in the builder docstring, which is on main.
>
> **Fix.** State this interpretation explicitly in draft §1 or §5.
>
> ---
>
> ## Notes
>
> - **n1.** The base rate is computed in float64 from `rows.jsonl`. Stage S uses float32 tensors. The difference is negligible, but worth knowing if the two are compared to 1e-7.
> - **n2.** Rule no-ops are in both populations with the inert target, as in Stage S val; this is consistent. Unlabelled `duplicate` rows are in the exclusion list but in neither population; this is also consistent with the builder. Suggest reporting `n_rule_noop` per population, because no-ops are trivially predictable and raise the skill.
> - **n3.** The header field `created_utc` is read (sft_test_eval.py:167) but never written by `predict_test`.
> - **n4.** Facts that check out:
>   - the RUNBOOK P.4 contents, apart from isotonic;
>   - the R1-C3-POOL / POOL-EXAM quotes;
>   - the R1-TRACKP-SFT-DUP sweep-1 numbers (1,176 / 47 / 74 of 262);
>   - the R1-TRACKP-SFT-DEV paraphrase;
>   - R1-MAIN-PROPOSER (e), as far as the draft quotes it;
>   - R1-TRACKP-TASL2-HOST, R1-QTORCH-AMEND, R1-TRACKP-I3-H200, R1-LR-GRID, R1-TEMPERATURE;
>   - the trial's model, lr, seed, micro-batch OOM and 159 s;
>   - TASL-2 host equivalence (R1-TRACKP-D2: passed 17 Nov);
>   - the label-block sha `cdae9c3f…9aca` (committed SHA256SUMS);
>   - the freeze draft accepted (review 5a8fa2f2 on dde24f6f);
>   - `NOT_YET["sft"]` naming `trackp_p4_<date>.md`;
>   - the count of 21 tests.
> - **n5.** Reading discipline:
>   - No evaluator path opens `runs.jsonl`, the evaluation block or a sealed file. Labels go through `LabelBlockSource`; the table through `load_table` with its D8 and sealed guards. Predictions are refused by name, and the data directory files are fixed names.
>   - Binding the label source to the data manifest (kind, sha256, seed, shift_z, sweep, completion sha) is sound, though partly untested (M6).
>   - The Mac-scope rule is respected: CPU tests only, tiny models.
> - **n6.** Reviewer housekeeping: I removed one scratch directory that I had created myself (/tmp/p4rev/base, an early copy that could not run the D8 guard). Nothing outside /tmp/p4rev was written or removed.
>
> VERDICT: NOT ACCEPTED

## Round 2 (`75901a8e (rev 2)`)

> Reviewed base: 75901a8e15654c4a090fbcf951e4f93844b6184b
>
> # Independent review, round 2: Track P P.4 test evaluator, tests, and phase-1 authorization draft
>
> Reviewer: independent read-only reviewer (Claude), 21 Nov 2026. AI-assisted.
>
> Scope: `r1/c3/train/sft_test_eval.py`, `r1/tests/test_trackp_sft_test_eval.py`, and
> `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` at 75901a8e, reviewed against my round-1 findings
> (`/tmp/p4rev/review_r1.md`, base 26c1cf43).
>
> ## What I checked
>
> **Sources:**
> - `sft_data.py`, `sft.py`, `trainer.py`, and `trackp.py` (the `_stage_s` layout and `data_sha256`).
> - PLAN at 94db94bb and at 4aac5209. The only difference between the two is the added R1-S2C3B-WDBC row, as the draft says.
> - The sweep-2 preregistration draft: `mac-sweep2-prereg-20261121` @ 0e68c1de, PRE-SPLIT.
> - The trial at f557f985: its `captures/data_splits.json` holds instance names only, no labels.
> - `TRACKP_SFT_DUP_20261117.md` on `mac-trackp-sft-dup-20261117`, which is the source of "train only gives 77".
>
> **Tests:** in the worktree, `test_trackp_sft.py` plus `test_trackp_sft_test_eval.py` give **70 passed**.
>
> **Mutations:** I ran 33 mutations of the evaluator in my scratch clone (`/tmp/p4rev/clone`, checked out at 75901a8e). 25 were killed and 8 survived. The log is `/tmp/p4rev/mutation_results_r2.txt` and the script is `/tmp/p4rev/scripts/mutate2.py`.
>
> **Split check:** I recomputed instance assignments from instance names and salts only, with no label data (see B1).
>
> **No real label or evaluation value was read.** Nothing was deleted: my round-1 probe test file was moved to `/tmp/p4rev/_to_delete/`. The scratch clone's module was restored after the interrupted mutation run, and the clone is clean.
>
> ## Round-1 findings: status
>
> | R1 finding | Status at 75901a8e |
> |---|---|
> | B1 (phase-1 test read) | **Resolved.** P4-PHASE1-TEST A is recommended. `evaluate_test` refuses real labels on ENGINEERING_ONLY data (sft_test_eval.py:404-407). The STOP is at draft:143. The refusal is mutation-tested (N14 killed). See B1 below for a related split issue. |
> | B2 (test target) | **Resolved for phase 1.** The report records `test_target` (:73-74, :429). P4-TARGET is deferred to the evidence note with `y_eval` recommended (draft:237-239). |
> | B3 (phase-2 split and composition) | **Resolved by scope.** The note is phase 1 only (draft:5-7). §9 lists the evidence-note items. The new P4-P1SPLIT introduces a new blocking issue (B1 below). |
> | M1 (budget) | **Resolved.** Trial facts are corrected (draft:33-37): 126 of 370 steps, 159 s, 16,511 MiB. I checked the arithmetic: 1.26 s/step; 7.8 min per full run; B ≈ 13.5 full-run equivalents per base ≈ 21 GPU-h; A ≈ 12.8 equivalents at 3.9 min ≈ 10 GPU-h; 8× sensitivity ≈ 31.5 GPU-h. P4-LC handles the learning curve. P.3a and Unit B are cited with branch and commit. |
> | M2 (gradient checkpointing) | **Resolved** (P4-HOST A′). See m3. |
> | M3 (controls) | **Resolved.** Controls are always carried, and a control failure is a STOP (draft:72-74, :150). |
> | M4 (one read, binding) | **Resolved in substance.** The run binding covers the sha256 of `sft_report.json`, `best.json`, `temperature.json` and the `best/` tree. T comes from `best/temperature.json`. Raw and scaled metrics come from one logits file. The ledger is keyed by arm or checkpoint. Residuals are in m1 and m2. |
> | M5 (replay binding) | **Resolved.** The table is pinned, `features_hash` is checked per proposal, and the index is checked (:462-485). Test gaps are in m4. |
> | M6 (tests) | **Largely resolved.** The base rate is now independent and also checked against uniform (N3/N4 killed). The unlabelled train-duplicate fixture works (N9 killed). Temperature, policy, sweep and completion are tested (N5-N8, N10, N11 killed). New survivors are in m4. |
> | M7 (RL gate) | **Resolved for phase 1** as readiness only (draft:129-132). The evidence gate is in §9. |
> | m1–m8 | **Resolved**: split recomputation, gate marked proposed/new, per-suite tick, citation, isotonic and bin-token readout, H200 row in §9, robustness fixes, and the "seen" reading with the 77 source. |
>
> ---
>
> ## Blocking
>
> ### B1. P4-P1SPLIT A does not reproduce the preregistration's P3 assignment, so its stated guarantee is false
>
> **Where:** draft:62-65 (also draft:224); sft_data.py:430; sft_test_eval.py:184.
>
> **What the draft says.** "The builder's split config becomes salt `c3_p3_split/v1`, 9 test and 3 validation per node, which reproduces the preregistration's P3 ordering (sha256 of `c3_p3_split/v1:<instance id>`). No sweep-1 label of a P3 test instance enters phase-1 training or validation."
>
> **Why that is wrong.**
> - The preregistration (PRE-SPLIT A, `SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md`:46-48) orders instances by `sha256("c3_p3_split/v1:" + <node> + ":" + <instance seed>)`.
> - The builder hashes `f"{salt}:{inst}"` with `inst = "<node>__s<seed>"` (sft_data.py:430).
> - These are different strings, so the two orderings differ.
> - The draft restates the preregistration's key as `<instance id>`. That is not what the preregistration says.
>
> **What the recomputation shows.** I recomputed both orderings over the 144 universe instances (names from the trial's `data_splits.json`; my code reproduces the recorded `trackp_sft/v1` split exactly).
>
> With the builder's key and salt `c3_p3_split/v1`:
> - the builder's test set equals the P3 test set on **no** node;
> - 2–4 P3 test instances per node fall in the builder's **train** set;
> - 0–2 P3 test instances per node fall in its **val** set.
>
> Val is read on real labels in phase 1: early stopping, temperature, and the reported val metrics and RL-gate quantities. So option A as specified would read and report model performance on evidence (P3) test instances. P4-PHASE1-TEST A exists to prevent exactly that.
>
> Option B's text (draft:66-68) also understates the cost. Besides the 4–7 P3 test instances per node in train (I confirm 4–7), `trackp_sft/v1` val contains **1–3 P3 test instances per node**, and those are read every evaluation.
>
> The evaluator's `_check_assignment` recomputes with `SD.assign_splits`, so it would accept the wrong (builder-key) assignment and reject the correct one.
>
> **Fix.**
> 1. In the P.4 runner unit (P3), make the split key exactly the preregistration's. Options:
>    - a `key` field in the split config, such as `"node:seed"`, used by both `assign_splits` and `_check_assignment`;
>    - or accept the signed P3 split file as input and bind it by its sha256.
>
>    Alternatively, have the preregistration adopt `<salt>:<instance id>` through its own review.
> 2. Add a test that rebuilds the preregistration's P3 assignment from its stated formula and checks it against the builder's instance lists.
> 3. Correct draft:62-65 to say that this needs a code change, not only a config change.
> 4. Add to option B that its val set holds 1–3 P3 test instances per node, which phase-1 val reads would expose.
> 5. Add a STOP: "the phase-1 instance lists differ from the signed P3 split file (or its recomputation)".
> 6. List the key change explicitly among the P3 items at draft:204-206.
>
> ---
>
> ## Major
>
> None.
>
> ## Minor
>
> ### m1. The ledger key lets a rebuilt data directory reread the test
>
> **Where:** sft_test_eval.py:320-329, :451-456; draft:178-179, :206.
>
> **Problem.**
> - The ledger is keyed on `sft_data_sha256`. A data directory rebuilt from the same table, labels and split (for example with another output path, which changes the manifest bytes) gets a new key, so the same checkpoint can be read again.
> - The ledger path is chosen by the caller.
> - The check and the append are not atomic.
>
> This matters only under P4-PHASE1-TEST B or in the evidence phase.
>
> **Fix.**
> - Key the entries on (table `proposals.jsonl` sha, label sha256, `splits.json` instances sha) plus the arm or the best-tree sha.
> - Fix one ledger path per table in the runner unit, as P3 already says.
> - Take a file lock around the check and the append.
>
> ### m2. Prediction binding to the checkpoint is a declaration
>
> **Where:** sft_test_eval.py:488-504.
>
> **Problem.** `predict_test` records the run's hashes but does not itself load the model from `run_dir/best`. The caller loads it.
>
> **Fix.** Have the runner unit load the model from `run_dir/best` inside `predict_test`, or check the loaded adapter and heads hashes against `best/record.json`.
>
> ### m3. The gradient-checkpointing trigger turns it on everywhere
>
> **Where:** draft:84-88, :125, :227.
>
> **Problem.** A′ makes gradient checkpointing apply "when the host config sets `gpu.gradient_checkpointing: true`". The portal and TASL configs already set it to true (trial finding 1). Once the code change lands, it would be on for every base and every table using that config, not only after a 4B base fails at micro-batch 1.
>
> **Fix.**
> - Use a dedicated switch, such as `sft.gradient_checkpointing`, set per table and recorded in the key values.
> - State that all arms of one table use one setting.
>
> ### m4. Mutation survivors (all small and fail-closed in practice)
>
> **Where:** the test file. Mutation IDs refer to `/tmp/p4rev/mutation_results_r2.txt`.
>
> | Mutation | What was removed or weakened |
> |---|---|
> | N19 | the `sft_report_sha256` comparison |
> | N26 | "real labels need a sweep index" |
> | N27 | replay with an unpinned table |
> | N28 | replay without the label-source check |
> | N29 | the replay-side sweep-index check (the evaluate-side check, N20, is killed) |
> | N31 | refusal of a non-positive temperature |
> | N32 | the ledger ignoring the data sha (cross-data reads are untested) |
> | N33 | the exclusion list recomputed from labelled test rows only (no fixture has an unlabelled test row on the list) |
>
> N22 (the replay `ids_sha256` comparison) also survives. It is redundant with the exact-coverage check of the logits keys, so this is acceptable.
>
> **Fix.**
> - Add one refusal test each for N19, N26, N27, N28, N29 and N31.
> - Add a fixture with an unlabelled (`duplicate`) test row whose key is seen in train (N33).
>
> ### m5. Small-run time estimate
>
> **Where:** draft:107-113.
>
> **Problem.** The 1.26 s/step figure folds model load and the step-0 evaluation into the per-step cost. For the short learning-curve runs and the about-590-row option A runs, that fixed overhead weighs more, so the estimate is slightly low. The cap of 40 GPU-h still covers it with margin.
>
> **Fix.** One sentence noting this.
>
> ## Notes
>
> - **n1.** The phase-1 refusal keys on `label_status` beginning with `ENGINEERING_ONLY`. `sft_data.LABEL_STATUS` is a constant with that prefix. The evidence runner must change the builder's status, or `evaluate_test` will refuse evidence data. Worth a line in §9.
> - **n2.** Facts I verified:
>   - 4aac5209 = 94db94bb + R1-S2C3B-WDBC;
>   - PRE-SPLIT A text (apart from the key restatement in B1);
>   - "train only gives 77" (`TRACKP_SFT_DUP_20261117.md`:69);
>   - the trial facts and the budget arithmetic;
>   - P3 per tier = 6 : 3 : 9 for T0;
>   - Unit B at `ops-tasl-20261116` @ 2287e492;
>   - the run-directory layout the evaluator expects (`stage_s/{sft_report.json, best.json, best/temperature.json}`; `data_sha256` = sha256 of `sft_data.json` bytes, `trackp.py` `_stage_s`) matches the code.
> - **n3.** The reading discipline still holds:
>   - The new paths (`run_record`, logits, ledger, replay) open only fixed or named files, each passed through `refuse_sealed`.
>   - Label reads still go through `LabelBlockSource`.
>   - A test spies on `open` and confirms that no evaluation or `runs.jsonl` file is touched.
>
> VERDICT: NOT ACCEPTED

## Round 3 (`ef600c5b (rev 3)`)

> Reviewed base: ef600c5bada61f85519027abc425514a0c9b7d1b
>
> # Independent review, round 3: Track P P.4 test evaluator, tests, and phase-1 authorization draft
>
> Reviewer: independent read-only reviewer (Claude), 21 Nov 2026. AI-assisted.
>
> Scope: `git diff 75901a8e ef600c5b`, which touches three files:
> - `r1/c3/train/sft_test_eval.py`
> - `r1/tests/test_trackp_sft_test_eval.py`
> - `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`
>
> I checked the diff against my round-2 findings (`/tmp/p4rev/review_r2.md`) and against the sweep-2 analysis preregistration at revision 4.
>
> ## What I checked
>
> **Tests.** `test_trackp_sft.py` plus `test_trackp_sft_test_eval.py` give **83 passed**. The evaluator file collects 48 tests, which matches draft §5.
>
> **Preregistration.** The PRE-SPLIT A text at revision 4 (`mac-sweep2-prereg-20261121` @ `95da769e`, `SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md`:55-79) orders instances by `sha256("c3_p3_split/v1:" + <instance id>)`, where the instance id is `<node>__s<seed>`. Its review record `15b7389e`, `SWEEP2_ANALYSIS_PREREG_REVIEW_20261121.md`:659-661, gives "Verdict: ACCEPTED, Accepted commit 95da769e (round 4)".
>
> **Split recomputation, from instance names and salts only (no labels).** I used the 144 universe instances.
> - Under the revision-4 formula, the builder's key (`salt + ":" + instance`, sft_data.py:430) is the same string as the preregistration's, so the two assignments are identical.
> - Option B's overlap with the P3 test set, per node in the order digits, breast_w, climate, credit_approval, ionosphere, sonar, wdbc, tabular:
>   - train: 5, 7, 6, 5, 6, 5, 6, 5
>   - val: 2, 2, 2, 3, 2, 3, 2, 1
>
>   This matches the figures at draft:70-74 exactly.
>
> **Mutations.** 21 mutations in my scratch clone at ef600c5b. They are my round-2 survivors, six new ones aimed at the round-3 changes, and a regression sample. **16 killed, 5 survived.** The 5 survivors, all discussed below, are:
> - two redundant checks (N22, N32);
> - two that only make the ledger stricter (R2, R5);
> - one test gap (R6).
>
> The log is `/tmp/p4rev/mutation_results_r3.txt` and the script is `/tmp/p4rev/scripts/mutate3.py`.
>
> **Housekeeping.** I read no real label or evaluation value and deleted nothing. The scratch clone is clean after the run, and the worktree was not touched.
>
> ## Round-2 findings: status
>
> | R2 finding | Status at ef600c5b |
> |---|---|
> | **B1** (P3 key) | **Resolved.** |
> | m1 (ledger) | **Resolved.** |
> | m2 (checkpoint binding) | **Resolved.** |
> | m3 (gradient checkpointing switch) | **Resolved.** |
> | m4 (mutation survivors) | **Resolved.** |
> | m5 (overhead) | **Resolved.** |
>
> **B1 (P3 key).** The accepted revision 4 of the preregistration now uses `salt:instance id`, so the builder reproduces P3 exactly.
> - draft:62-69 cites `95da769e` and quotes the formula.
> - `test_the_p3_assignment_is_the_preregistration_formula` re-implements the formula over the 8 × 18 design universe and checks it against `assign_splits`. It also checks the unpadded `<node>__s<seed>` id format.
> - The binding to the signed P3 split file appears as a runner-unit item (P3, draft:215-216), a STOP (draft:153) and a key value (`split_file`).
> - Option B now states both its train and its val overlaps, and that phase-1 validation would read labels of evidence test instances.
>
> **m1 (ledger).**
> - The ledger is now keyed on the test material: the table hashes, the label identity and the `splits.json` sha (`material_key`, :325-329), not the data manifest.
> - It has a fixed name, `trackp_p4_test_reads.jsonl`, and anything else is refused (:409-410).
> - The check and the append happen under `fcntl.flock(LOCK_EX)`, followed by `fsync` (:427-440).
> - The cross-rebuild test passes, and mutations R1 and R3 are killed.
>
> **m2 (checkpoint binding).** `predict_test` now loads the model itself through `loader(run_dir/"best")`. It takes `run_record` before and after loading and refuses if the two differ (:526-528). A test uses a loader that changes the weights mid-load; mutation R4 is killed.
>
> **m3 (gradient checkpointing switch).** The switch is now the draft's own per-table key `sft_gradient_checkpointing`. The host's `gpu.gradient_checkpointing` explicitly does not switch it (draft:91-93, key values).
>
> **m4 (mutation survivors).** Each round-2 survivor now has a test: N19, N26, N27, N28, N29, N31 and N33 are all killed. N22 (the replay `ids_sha256` comparison) still survives; it is redundant with the exact-coverage check of the logits keys, as noted in round 2.
>
> **m5 (overhead).** The note is added (draft:115-116).
>
> ---
>
> ## Blocking
>
> None.
>
> ## Major
>
> None.
>
> ## Minor
>
> ### m1. "A second read of the same arm with a different checkpoint" is untested
>
> **Where:** `r1/tests/test_trackp_sft_test_eval.py`, `test_one_test_read_per_arm_and_per_checkpoint`.
>
> **Problem.** Mutation R6 limits the ledger refusal to the same best checkpoint, and it survives. The "another directory, same arm" case reuses the same run, so the refusal by arm id alone is never exercised. The code is correct (`e.get("arm") == arm or …`).
>
> **Fix.** Add a case that retrains or alters `best/` under the same arm id, then evaluates. Expect "one test read per arm".
>
> ## Notes
>
> - **n1. Ledger edge cases.**
>   - The ledger file name is fixed, but its directory is still chosen by the caller. "One per table" therefore depends on the runner unit fixing that path, as draft P3 says.
>   - The ledger entry is written after `test_report.json`. A crash between the two leaves a report with no entry; the non-empty output directory then blocks only that one directory.
>
>   Optionally, write an intent entry before computing.
> - **n2. Ledger strictness.** Mutations N32, R2 and R5 make the ledger key coarser: material ignored, labels dropped, table dropped. They survive because they only make the ledger refuse more often (fail-closed). No test checks that a read on *different* test material is allowed. This is acceptable; one positive test would pin it down.
> - **n3. Evaluator recomputation.** `_check_assignment` recomputes with `assign_splits` over the union of the recorded instances. Under P4-P1SPLIT A this equals P3 only when the build used the full design universe. The runner's binding to the signed split file (P3, STOP) covers a build without the universe.
> - **n4. Reading discipline still holds.** The new ledger, lock and loader paths open only the fixed ledger file and `run_dir/best`, both passed through `refuse_sealed`. No path reads evaluation-seed files, `runs.jsonl` or sealed files. Phase 1 still refuses real-label test reads (N14 killed).
>
> VERDICT: ACCEPTED

## Round 4 (`cff56ae8 (tests)`)

> Reviewed base: cff56ae855e39cbbb272ffda5473f759a6a565c5
>
> # Independent review, round 4 (confirmation): Track P P.4 test evaluator — round-3 minor m1
>
> Reviewer: independent read-only reviewer (Claude), 21 Nov 2026. AI-assisted.
>
> ## Scope
>
> `git diff ef600c5b cff56ae8` changes only tests: 11 lines added to `r1/tests/test_trackp_sft_test_eval.py`, in `test_one_test_read_per_arm_and_per_checkpoint`. Nothing changed under `r1/c3/` or `docs/` (`git diff --quiet ef600c5b cff56ae8 -- r1/c3 docs`). The evaluator and the authorization draft are therefore as accepted in round 3 (`/tmp/p4rev/review_r3.md`).
>
> ## What I checked
>
> **Tests.** `test_trackp_sft.py` plus `test_trackp_sft_test_eval.py` give **83 passed**.
>
> **The new test lines.** They now:
> 1. change `best/` under the **same** arm id;
> 2. re-predict, which binds the logits to the new checkpoint;
> 3. expect "one test read per arm";
> 4. let **another** arm on **another** checkpoint read once, with the ledger then holding 2 entries.
>
> **Mutations,** run in my scratch clone at cff56ae8 (log `/tmp/p4rev/mutation_results_r4.txt`, script `/tmp/p4rev/scripts/mutate4.py`):
>
> | Mutation | Result | Meaning |
> |---|---|---|
> | R6 (ledger refuses only on the same checkpoint) | **KILLED** (survived in round 3) | round-3 m1 is resolved |
> | N15 (ledger keyed on the arm id only) | KILLED | |
> | R3 (material key is the data-manifest sha) | KILLED | |
> | R7 (ledger check removed) | KILLED | |
>
> N16 from the round-2 set no longer applies to the round-3 code, so R7 replaces it.
>
> The new positive case (another arm on another checkpoint is allowed, and the ledger then holds 2 entries) also guards against a ledger that refuses everything. Before this change no test checked that a legitimate read is allowed.
>
> **Housekeeping.** No label or evaluation values were read and nothing was deleted. The scratch clone is clean after the run, and the worktree was not touched.
>
> ## Findings
>
> - **Blocking:** none.
> - **Major:** none.
> - **Minor:** none. Round-3 m1 is resolved.
> - **Notes:** round-3 notes n1–n4 still stand. They concern runner-unit conventions (the ledger directory, a write-ahead intent entry, a positive test for reads on different material, and the split-file binding) and do not block.
>
> VERDICT: ACCEPTED

---

Code-Commit: cff56ae855e39cbbb272ffda5473f759a6a565c5
Verdict: ACCEPTED

Accepted commit: `cff56ae855e39cbbb272ffda5473f759a6a565c5` (round 4; draft revision 3, evaluator with 48 tests).
