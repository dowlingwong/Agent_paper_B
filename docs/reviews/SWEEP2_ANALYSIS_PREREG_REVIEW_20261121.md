Reviewed base: `95da769e72cfe5a865025f8cfe02d120da5e42af` (branch `mac-sweep2-prereg-20261121` over `main` `4aac5209`; accepted in round 4)

# Independent review record — sweep-2 C3 analysis preregistration draft (frozen: false)

**Unit.** `docs/r1/proposals/SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md` (revisions 1–4) on `mac-sweep2-prereg-20261121`
over `main` `4aac5209`. Authority: R1-BX-D8, R1-BX-D8-V3-A/B, R1-BX-D8-CONFIRM, R1-S2C3B-WDBC, D18, R1-MAIN-PROPOSER (b)/(e),
R1-MAIN-PROPOSER-ITEMS, R1-B2-DECOUPLE, R1-BX-D3; the queue of 20 Nov 2026, item 4 ("sweep-2 analysis preregistration
(split P3, gate v3, floors)"). The draft decides nothing: its author decisions (PRE-WDBC, PRE-SPLIT, PRE-MEM, PRE-JOINT,
PRE-SELECT, PRE-A2, PRE-DELTA, PRE-DUP, PRE-DIV, PRE-T1, PRE-SECONDARY, PRE-STAGE, PRE-POWER) carry options and
recommendations.

**Process.** One independent reviewer (a separate agent that did not write the draft) for all four rounds; it edited
nothing (scratch under `/tmp/prerev/` only), verified the gate's sha256, computed split overlaps from seeds and salts
only, and read no labels, results or secrets. Round 4 confirms the fixes made after the round-3 acceptance. The round
texts are reproduced below as delivered, as block quotes.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `0e68c1de (rev 1)` | CHANGES REQUESTED (1 blocking, 10 major, 10 minor) |
| 2 | `dc2a8a95 (rev 2)` | CHANGES REQUESTED (2 major, 7 minor) |
| 3 | `84fd832e (rev 3)` | ACCEPTED (3 minor) |
| 4 | `95da769e (rev 4)` | ACCEPTED (cosmetic notes) |

**Open for the author.** The thirteen author decisions of §2 and the signature; under PRE-WDBC B, gate v3.1 with its
binding row; the release rows of §8; the reviewed units of §9 (split-file generator, release step and locks with the
integrity carve-out, gate-input builder, fold-analysis module, Track P's switch to P3). Round-4 cosmetic notes: PRE-SELECT
A "Per arm" could read "Per arm (A3, A5)"; one long line in PRE-WDBC B.

## Round 1 (`0e68c1de (rev 1)`)

> Reviewed base: 0e68c1de451c90707dcd0074300b69bd6f4cc943
>
> # Independent review: sweep-2 C3 analysis preregistration draft (round 1)
>
> - **File:** `docs/r1/proposals/SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md` (172 lines), branch
>   `mac-sweep2-prereg-20261121` @ `0e68c1de`. The diff against `4aac5209` adds only this file.
> - **Authority read:** `docs/r1/PLAN.md` at that commit: D18 (l. 417), R1-C3-POOL-EXAM (611), R1-SWEEP1-CLASSIFY (621),
>   R1-B2-DECOUPLE (678), R1-MAIN-PROPOSER (732), R1-BX-D3 (747), R1-BX-D8 (752), R1-BX-REVISIONS (759),
>   R1-BX-PROPOSED-CONFIRM (780), the 4 Nov 19:08 replies incl. R1-MAIN-PROPOSER-ITEMS (997) and its note (1005),
>   R1-BX-D8-V3-A (1208), R1-BX-D8-V3-B (1234), R1-BX-D8-CONFIRM (1252), R1-TRACKP-SFT-DUP (1288), R1-S2C3B-WDBC (1336).
> - **Code and documents read:** `r1/c3/gate.py`, `r1/c3/offline_eval.py`, `r1/c3/analysis_guard.py`,
>   `r1/c3/dataset.py` (`noise_table`), `r1/c3/train/sft_data.py`, `r1/scripts/configs/trackp_sft.json`,
>   `docs/r1/C3_DESIGN.md`, `docs/r1/TRACK_P_POST_TRAINING.md`, `docs/r1/reports/M11_D8_GATE_V3_20261116.md`,
>   `docs/r1/authorizations/c3_sweep2_20261119.md`, and the G.5 draft
>   (`/tmp/pb/wt/g1b`, `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` @ `c894d0f6`).
> - **Checks run:** `sha256sum r1/c3/gate.py` = `ffb70d7af9b8238107a4eb5621fc20fadd9f8ccd689edb0b2e33b877737434ee`. The
>   file is the same at HEAD and at `6aa9985c` (`git cat-file -p 6aa9985c:r1/c3/gate.py | sha256sum`), so it matches
>   R1-BX-D8-CONFIRM. `offline_eval.py` sha256 = `5990f384…`, as the draft says. I computed the overlap between the
>   Track P SFT split and the draft's T0 P3 rule with `/tmp/prerev/overlap.py`, which uses instance seeds and salts
>   only and reads no labels.
> - No label, result, evaluation block or secret was read.
>
> Summary: the §1 quotations are mostly accurate, and the M11 §3 list is complete. Leaving the SFT split for P3
> (PRE-SPLIT A) is the right direction. But the draft cannot be signed as it stands. Its T0 node set contradicts the
> signed sweep-2 analysis scope, and the pinned gate cannot run on that scope. It also leaves several
> verdict-relevant inputs unfixed: the seed block and fit set behind the train/dev utilities, δ_n scaling and its
> source, memory-mode pooling, partial-T1 timing and the dev-side duplicate rule. And its read lock has a hole through
> sweep 1's shared instances.
>
> ---
>
> ## Blocking
>
> ### B1. The 7-node primary scope of R1-S2C3B-WDBC is ignored, and the pinned gate cannot run on it
>
> - **Location:** §3 ("the eight T0 nodes of `gate.T0_NODES`"), §1 table (R1-S2C3B-WDBC absent), §4 step 6, §7.
> - **Evidence:**
>   - PLAN l. 1336 (R1-S2C3B-WDBC): "the **primary sweep-2 analysis uses the seven nodes that passed C3b**, and
>     openml_wdbc enters as a pre-declared sensitivity row (with / without)".
>   - The signed authorization `c3_sweep2_20261119.md` l. 77–78 repeats this.
>   - `gate.py` l. 50 says "A missing, extra or renamed T0 node is a STOP", and `_check_layout` (l. 327–333) raises
>     `GateStop` unless the T0 nodes are exactly the eight of `T0_NODES`, `openml_wdbc` included.
>   - The draft's header says it was written from "PLAN as at `94db94bb` plus R1-S2C3B-WDBC", yet it neither quotes
>     nor applies that row.
>   - Result: if the draft is signed as it stands, the primary verdict uses a node set that an author row excluded. If
>     the gate is fed the seven nodes instead, it STOPs.
>   - The PoI includes every supplied node, eligible or not (`_node_poi` over all nodes, l. 429–430), so no honest
>     input lets openml_wdbc "be present but not count".
>   - R1-S2C3B-WDBC also allows the C3b rerun to come out 8/8. The draft must say whether the 7-node primary still
>     holds in that case.
> - **Fix:** add an author decision (say PRE-WDBC) with options:
>   - **(a)** An author row amending R1-S2C3B-WDBC for the C3 gate: the primary gate runs on all eight T0 nodes, which
>     is the only scope the pinned gate accepts, and the 7-node analysis is a descriptive row.
>   - **(b)** A reviewed gate v3.1 that differs only in the T0 layout check (for example, it accepts a declared T0
>     subset listed in the input and reports it). It runs as primary on seven nodes and as the sensitivity on eight.
>     This needs a new sha, an amended CONFIRM-type row, and an `analysis_guard` binding before any sweep-2 read.
>   - **(c)** Run the gate only on eight nodes, call that "the sensitivity row", and declare that the primary 7-node
>     statistic has no gate verdict. Not recommended: it inverts R1-S2C3B-WDBC.
>   - Then list the extra gate runs in §4 step 6 and §7: 7-node and 8-node, each with the PRE-DUP primary and
>     secondary inputs.
>   - Add R1-S2C3B-WDBC to the §1 table.
>
> ---
>
> ## Major
>
> ### M1. The train/dev utilities feeding eligibility and selection are undefined (seed block, A2 fit set, oracle definition), and the natural implementation would use the evaluation seeds for selection
>
> - **Location:** §3 "Utilities", §2 PRE-POOL A and PRE-A5 A ("mean dev utility U"), §4 steps 2–3, §6.
> - **Evidence:**
>   - §3 gives Δ_true only for test ("Test utilities take Δ_true from the **evaluation** block"). It says nothing
>     about which block gives Δ_true for the train/dev U.
>   - Those train/dev U values are used twice: in the gate's train+dev z and dev denominator (V3-A (2), l. 1208;
>     `gate.py` l. 298–311), and in the PRE-POOL/PRE-A5 selection.
>   - `offline_eval.assemble` sets `delta_true` to the evaluation half for every row (l. 133–140, 199–224). So "with
>     offline_eval's population weights … and its primary run accounting" naturally yields dev U values built on
>     7006–7010.
>   - Selecting on those values is forbidden. R1-SWEEP1-CLASSIFY (l. 621) says "seeds 7006–7010 are never used for
>     training or selection of any evidence". R1-B2-DECOUPLE (l. 678) says "never C3/Track P training, tuning or
>     selection". TRACK_P §3.1 (l. 132) says the two blocks are "never mixed in any quantity used for … model
>     selection … or the oracle ceiling's construction".
>   - §6 forbids this as a STOP, but §2 and §3 then define the selection criterion only in terms that would trigger
>     it.
>   - The oracle is defined only by "the oracle's decisions use the label block only". TRACK_P §7.1 (l. 416) gives the
>     full definition: "theory rule with belief built from `y_train` of the **same** proposal, evaluated against
>     `y_eval`". The draft must say whether the same rule layer and g apply, and what the soft-label width is.
>   - On train/dev, if the oracle is valued against the label block, it is valued against the very values it decided
>     on. That inflates the denominator and makes eligibility lenient.
>   - A2's train-instance U is in-sample if A2 is fitted on train. C3_DESIGN l. 86–87 says A1, the base of A2, is
>     fitted on "dev campaigns", which would make A2's dev U in-sample too and conflicts with step 3, "Train each arm
>     on train".
> - **Fix:**
>   - (i) Step 2 releases the **label block only**, for train and dev instances. No evaluation-block value of any
>     instance is released before step 5.
>   - (ii) PRE-POOL and PRE-A5 select on criteria built from label-block quantities only (dev log score or RPS, or a
>     dev utility with Δ from the label block), stated as such.
>   - (iii) The gate's train and dev blocks (A2, oracle) are computed at step 5, after the arms are frozen, with the
>     same definition as test. The oracle's belief comes from the label block of the same proposal and its value from
>     the evaluation block. Then eligibility cannot feed back into arm choices, and it uses no evaluation seed before
>     freezing.
>   - (iv) State what A2 is fitted on (train only, per node), and say whether its train-instance U is in-sample or
>     cross-fitted. If this is not fixed by a row, make it an author decision.
>   - (v) Write out the oracle definition: TRACK_P §7.1, the same rule layer, the same g, the soft-label width
>     s = σ̂_node/√K_label.
>
> ### M2. Sweep 1's data on P3 test instances are not covered by the read lock
>
> - **Location:** §2 PRE-STAGE A, §4, §8.
> - **Evidence:**
>   - The release rows in §8 cover "the sweep-2 T0 tables" only.
>   - R1-MAIN-PROPOSER (e) (l. 732) states that twin campaigns give the same (instance, incumbent, edit) "the same label
>     in both sources", and that both sources share one instance assignment.
>   - Sweep 1's B.2 audit (R1-B2-GO, l. 1266) writes `evaluation_block.jsonl` (`audit.py` l. 1072).
>   - `analysis_guard.guard_table` waves sweep-1 tables through without any D8 or release check
>     (`_index_is_frozen_sweep1`, l. 180–188 and 224).
>   - So sweep 1's label and evaluation values for the P3 test instances can be read before the arms are frozen. Those
>     values include every twin pair that recurs in sweep 2's test population.
>   - Pooled training (PRE-POOL A) also loads sweep 1's tables through this unguarded path.
>   - Earlier ENGINEERING runs on sweep 1 (Track P SFT on the `trackp_sft/v1` split, whose 12 training instances
>     include 4–7 of each node's P3 test instances) may have shaped hyperparameters or defaults. The adopted item
>     "draw the P.3b exam set from sweep 2's training partition, or from sweep 1's with disclosure" (l. 1005, adopted at
>     l. 997) and TRACK_P l. 178 ("a fixed subset of the training partition and never overlaps the test instances")
>     tie the exam set to the split.
> - **Fix:**
>   - Extend PRE-STAGE A, §4 and §6 to **both sources**: the test-instance label and evaluation values of sweep 1 under
>     P3 are released only with the sweep-2 test row, and the readers enforce this as well.
>   - Add a §6 STOP for reading sweep 1's test-instance values before step 5.
>   - The arms-frozen record lists every earlier engineering use of sweep-1 data on P3 test instances, including the
>     exam-set provenance, for disclosure.
>   - The P.3b/E-exam set is redrawn from P3 train instances only.
>
> ### M3. PRE-POOL misstates its authority and offers a non-compliant option, and the PRE-POOL/PRE-A5 criterion is ill-defined
>
> - **Location:** §1 row R1-MAIN-PROPOSER (e) ("*(proposed)*"); §2 PRE-POOL and PRE-A5.
> - **Evidence:**
>   - The author adopted the five (h) items ("采用五项建议", R1-MAIN-PROPOSER-ITEMS, l. 997). Item 3 is "choose pooled
>     versus sweep-2-only training on validation before any test read" (l. 1005).
>   - The draft still labels this *(proposed)*, and its option B ("no choice to make") does not choose on validation.
>   - The recommended criterion is "the higher mean dev utility U … over all nodes". It averages U across nodes in
>     metric units, so nodes with large metric scales dominate. T1 nodes make this worse; `mlgym_breakout_minatar`
>     reports a return.
>   - The criterion's seed block is unspecified (see M1). It does not say which dev population applies under PRE-DUP
>     (G.5 draft l. 111–112: the validation-side members of train-seen groups leave the primary validation population
>     "where arms are selected").
>   - Dev holds 3 instances per T0 node and 2 per T1 node, so the criterion is very noisy.
>   - Track P has its own preregistered selection metric, dev/val RPS skill (TRACK_P §5.7 l. 309–313; §6.1 lr and
>     checkpoint by val RPS). C3_DESIGN l. 174 makes calibration "the primary model-selection criterion". PRE-A5 offers
>     neither as an option.
> - **Fix:**
>   - Cite R1-MAIN-PROPOSER-ITEMS, drop "(proposed)", and drop or reword option B. Any option must be a
>     validation-based choice made before the test read.
>   - Define a scale-free, label-block criterion: for example, the mean over nodes of the dev U/σ_node with Δ from the
>     label block, or the dev RPS skill. Name the dev population (PRE-DUP primary) and the tie rule.
>   - Offer RPS-skill-based selection as an option in PRE-A5, and say why dev utility is recommended over Track P's
>     own metric if it remains the recommendation.
>
> ### M4. "One U per (arm, instance)" is undefined with two memory modes, with sweep 1 "as a stratum", and with joint or per-tier training
>
> - **Location:** §3 ("both memory modes, 18 instances per node"; "U = 20 × the weighted mean … over the instance's
>   logged proposals").
> - **Evidence:**
>   - Each T0 instance seed has two campaigns, `append_only_summary` and `none` (R1-MAIN-PROPOSER (b); authorization
>     l. 50). The gate takes exactly one U per instance id per node (`r1_d8_gate_input/v3`, `_paired_block`, `_ids`
>     uniqueness).
>   - The draft silently pools both modes' proposals into one weighted mean. That is a scientific choice no row fixes.
>     C3_DESIGN l. 66 calls `append_only_summary` "primary" and `none` the "contrast", and H5 (l. 136) studies the gain
>     by memory mode.
>   - Alternatives include: the primary mode only; an average of the two per-mode U values; per-mode gates.
>   - T1 may have one mode (G5-MEM A, `history` only) or two (G5-MEM B).
>   - R1-MAIN-PROPOSER (e) says "The B.7 gate … use sweep 2. Sweep 1 is added as a stratum". The gate has no source
>     stratum, and the draft treats sweep 1 as training data only (PRE-POOL) without saying that this is how it reads
>     "stratum".
>   - Whether A3 and A5 are trained jointly across tiers, or per tier, is also unstated, and LOSO depends on it.
> - **Fix:** add an author decision (say PRE-MEM) with options and a recommendation, for example:
>   - (a) pool both modes' proposals into one instance-level weighted mean, with the instance as the cluster (consistent
>     with (e)(4));
>   - (b) `append_only_summary` only as primary, `none` as a secondary gate;
>   - (c) the mean of the two per-mode U values.
>   Then state how T1's mode(s) enter, state that the gate's test population is sweep 2 only, and state how "sweep 1 as
>   a stratum" is reported (a separate descriptive table). Fix whether training is joint across tiers.
>
> ### M5. δ_n and σ_node: the scaling and the per-node sources are not fixed
>
> - **Location:** §3 "δ_n: D18, from the node's noise floor (T0: the C1 table; T1: G.1b on H200)"; §3 "g = 0.1
>   σ_node".
> - **Evidence:**
>   - D18 (l. 417) gives δ_n "in metric units" and says that "It is also the unit of the C3 gate, scaled to a 20-run
>     campaign". That leaves open whether the δ_n passed to the gate is D18's δ_n or 20 × δ_n.
>   - `gate.py` l. 95 only says "in the same units as U". U is 20 × a per-proposal mean.
>   - The earlier code compared a 20-run gain with an unscaled δ_n (`offline_eval.py` l. 435–439: `gain_per20` beside
>     `noise[node]["delta_n"]`).
>   - A factor of 20 changes which nodes are IQM-eligible.
>   - The C1 table (`dataset.E1_SUMMARY` = `results/r1/pilot/E1_20261022T214606Z/summary.json`, l. 47) contains
>     `openml_blood_transfusion` but **not `openml_climate`**, a T0 node. `noise_table` deliberately gives no entry for
>     nodes the table does not cover (l. 85–87). openml_climate's floor comes from the D21 reserve run (l. 460, 470).
>   - Three T0 nodes (breast_w, sonar, wdbc) had their start configurations repaired after C1 (R1-D28-REPAIR, l. 595).
>     Whether C1's σ and δ_n still apply to them is a question for the author.
>   - For T1 the source is "G.1b joint σ" (G.5 draft l. 197), which is consistent. But R1-BX-REVISIONS (f) (l. 759)
>     ties a noise floor to the host that ran the table's runs.
>   - σ_node, which sets g and the oracle's soft-label width, has no source named for any tier.
> - **Fix:**
>   - State the scaling explicitly. Recommend D18's δ_n unscaled, compared with the 20-run dev denominator, as earlier
>     practice did; if the author wants 20 × δ_n, offer it as an option.
>   - Name, per node, the file and sha256 that supply δ_n and σ_node: the C1 table for seven T0 nodes; the reserve-run
>     file for openml_climate; G.1b per T1 node.
>   - Add a disclosure line for the repaired nodes, or an author decision on them.
>
> ### M6. PRE-DUP covers test only, conflicts with the G.5 draft and R1-TRACKP-SFT-DUP, and the renormalisation needs edge rules
>
> - **Location:** §2 PRE-DUP; §3 last sentence.
> - **Evidence and answer to the specific question:**
>   - Renormalising the remaining weights inside an instance keeps U = 20 × a weighted mean per logged proposal, which
>     is still a valid 20-run value. It is compatible with offline_eval's weights: those are
>     inverse-sampling-probability weights set per (source, node) stratum (`offline_eval.py` l. 47–52), and a
>     deterministic, key-based exclusion leaves them valid if they are **not** recomputed. The draft must say "not
>     recomputed".
>   - The draft has no rule for two edge cases: (a) an instance whose test proposals are all excluded, or (b) one whose
>     remaining weights sum to 0 (all DI-selected, weight 0). In either case U is undefined, and the claim "Instance
>     counts, and so the test floor, are unchanged" is false.
>   - Exclusion is not random. Step-1 proposals start from the shared baseline and recur across instances; the G.5
>     draft (l. 71–72) notes that all T1 instances make the same first proposal. So the primary estimand shifts to
>     later-campaign proposals, which should be disclosed.
>   - The G.5 draft (l. 108–113) also excludes validation-side members of train-seen groups from the primary
>     validation population "(where arms are selected)", and says "The sweep-2 analysis preregistration fixes this
>     rule before release". R1-TRACKP-SFT-DUP (l. 1288) does the same for Track P's validation population.
>   - PRE-DUP fixes neither the dev side nor which population the gate's train/dev blocks use. If the primary and
>     secondary runs use different dev blocks, their eligibility can differ.
>   - Under pooled training, "seen" must include both sources' train/dev keys, per (e)(3).
> - **Fix:**
>   - Extend PRE-DUP A to the dev side, matching G5-AUDIT and R1-TRACKP-SFT-DUP.
>   - State that the gate's train and dev blocks are identical in the primary and secondary runs. Recommend the full
>     population for the gate's eligibility blocks, so eligibility does not depend on PRE-DUP.
>   - State that the seen-set spans both sources' train/dev keys.
>   - Add the rule for an instance with no remaining positive weight: it is dropped from the primary input and
>     reported; the test floor applies as the gate computes it. Remove the "unchanged" claim.
>   - State that the weights are not recomputed.
>   - Define the key exactly (`node`, incumbent configuration hash, candidate configuration hash, as in
>     `sft_data.py` l. 47–49) and relate it to (e)(3)'s "(instance, incumbent hash, edit hash)".
>
> ### M7. Partial T1, nodes whose labels never arrive, and read timing are not preregistered
>
> - **Location:** §3 T1, §4, §7 ("Partial T1: the number of labelled T1 nodes").
> - **Evidence:**
>   - R1-BX-D8-CONFIRM (l. 1252) allows reading the gate "on T0 plus the available labelled T1 nodes" at B.7.
>   - The draft does not say:
>     - when the read happens;
>     - what makes a T1 node "labelled" (complete, or any test instances);
>     - what happens to a node after a G.5 node STOP (the G.5 draft l. 236–238 needs an author row and ≥ 3 labelled
>       test instances);
>     - whether a later read with more T1 nodes is allowed.
>   - §4's "A gate run is never repeated after its output is seen" forbids a later full-T1 read. That may be intended,
>     but then it should be stated as a decision.
>   - The order between tiers is not fixed. If T0's test is released and read while T1's train/dev is still arriving,
>     the arms trained later on T1 data are trained after a test read.
>   - The gate requires non-empty train, dev and test lists for every supplied node (`_ids`, l. 247–248). A node that
>     loses every dev instance cannot be supplied at all.
> - **Fix:**
>   - Fix the read rule. The T1 node set and its instances are frozen in the test-release row, before any test read,
>     and include exactly the nodes whose train/dev labels were used to freeze the arms.
>   - There is one primary gate read. A later read with more T1 nodes is either forbidden or preregistered as a
>     separate, secondary read with its own disclosure (author decision).
>   - The arms-frozen record follows all train/dev data of every included tier, and no test partition of any tier is
>     released earlier.
>   - A node without at least one train and one dev instance is reported and not supplied.
>   - Nodes that STOP at G.5 follow the G.5 rule.
>
> ### M8. Secondary analyses that read the test partition are not preregistered (LOSO, LONO, cross-proposer, sensitivities)
>
> - **Location:** §4 step 7, §7.
> - **Evidence:**
>   - LOSO is the "primary" generalisation test (TRACK_P §7.2, l. 425–426; PLAN l. 296). It needs arms retrained
>     without the held-out suite, but the draft names neither the LOSO statistic nor these fold arms, and the fold arms
>     are not in the arms-frozen record.
>   - LONO (C3_DESIGN l. 62; H2b l. 133, "expected main LM result"; TRACK_P l. 427) is absent.
>   - The cross-proposer table of R1-MAIN-PROPOSER (e)(2) is absent. It trains on one source's train partition and
>     reads the other's test partition, so it consumes the test partition.
>   - The g sensitivities (0.05 and 0.2 σ_node, "reported as sensitivities, no verdict") and the secondary arms and
>     controls of PRE-A5 also read test, but are not in step 6, or are not frozen in step 4.
> - **Fix:** for each of these, state the statistic, the training set, and whether it carries a verdict. Put all fold
>   arms, cross-proposer arms, secondary arms and controls in the arms-frozen record before step 5. List their runs in
>   §4 and §7, or declare explicitly that an item is out of scope and may not read test until a later signed
>   amendment.
>
> ### M9. Divergence on the evaluation seeds, and T1's K and seeds, are not handled
>
> - **Location:** §3, §1 row R1-B2-DECOUPLE; R1-BX-D3.
> - **Evidence:**
>   - The G.5 draft (l. 99–103) says: "Divergence on the evaluation seeds is part of the evaluation value `y_eval` and
>     is handled in the analysis preregistration".
>   - R1-BX-PROPOSED-CONFIRM REVISIONS (c) (l. 780) fixes divergence for labels (u = −g; partial if some seeds
>     diverge; divergent if more than half do). Nothing fixes it for Δ_true.
>   - The draft quotes only "K = 10 on T0". R1-BX-PROPOSED-CONFIRM D3 and Track G (E4) make T1 K = 6 (labels
>     7001–7003, evaluation 7006–7008) if the check passes. That changes the oracle's soft-label width and the seeds the
>     test release opens.
> - **Fix:** add the Δ_true rule for evaluation-seed divergence as an author decision with options (the mean over
>   non-divergent evaluation seeds; a divergent proposal valued at −g if executed; exclusion with a count). Add a
>   T1 seed line, conditional on R1-BX-D3's check, and a STOP for any use of 7004–7005 at K = 6.
>
> ### M10. The split specification leaves verdict-relevant freedom (universe, id format, off-size nodes) and delegates T1 to an unsigned draft
>
> - **Location:** §2 PRE-SPLIT A; §1 "adopted conventions".
> - **Evidence:**
>   - The bootstrap draws test instances "in sorted instance-id order" (`gate.py` l. 72). The lexical form of the
>     instance-id strings therefore changes the resamples and the bound. The draft does not fix the id format.
>   - The draft orders instances "per node" but does not say this is done over the fixed design universe (8 × 18 T0
>     seeds, `e1b_collect._instance_seed`), as `sft_data.py` l. 40–47 does. Without that, the assignment depends on
>     which instances a table holds.
>   - M11 §3 item 5 (report l. 74) says "no row fixes how their counts round" for off-size nodes. The draft adopts the
>     check but does not fix the rule.
>   - The T1 split is given only "as the G.5 draft's G5-SPLIT … its own salt". That rule is *(proposed)* in another,
>     unsigned note. The draft quotes neither the salt (`c3_t1_split/v1`) nor the seeds (5101–5112).
> - **Fix:**
>   - Fix the instance-id string, for example `<node>__s<seed>` with the seed in decimal and no padding, as in
>     `sft_data.instance_universe`. Use it both for hashing and as the gate's `instance_ids`.
>   - Order over the fixed design universe: T0 8 × 18; T1 the 12 G.5 seeds per node.
>   - State that missing instances drop out without reassignment. They are reported under
>     `off_design_size`/`off_split`.
>   - Quote the T1 rule in full. Say that one generator writes one split file for both tiers, and that both this
>     preregistration and the G.5 note cite its sha256.
>
> ---
>
> ## Minor
>
> 1. **§2 PRE-SPLIT, "puts 6 of the 9 P3 test instances of a node into training".** The draft's own rule, with the
>    actual seeds and salts, gives P3-test ∩ SFT-train = 6, 6, 7, 5, 5, 6, 4, 6 (digits, breast_w, climate,
>    credit_approval, ionosphere, sonar, wdbc, tabular; mean 5.6). Six is the expectation, not a per-node fact. State
>    the computed range, 4–7.
> 2. **§2 PRE-SPLIT B, "Violates 'one assignment'".** (e)(1) requires one assignment across the two **sources**, not
>    across arms. B is unacceptable because A5 would train on test instances, not because of (e)(1). Reword.
>    Separately, the SFT split was never author-fixed: `trackp_sft.json` says "Proposed values (Track P agent), to be
>    confirmed by the author before any evidence use".
> 3. **§2 PRE-SPLIT A, consequence not stated.** A5's T0 training instances fall from 12 to 6 per node (plus sweep 1
>    under PRE-POOL). The P.3b/E exam set must lie within P3 train (TRACK_P l. 178). Both should be stated.
> 4. **§1 row "R1-MAIN-PROPOSER (b)".** It omits the `vary` split, and it does not mention R1-SWEEP2-SETTINGS (context
>    32,768, l. 1207) or R1-S2C3B-WDBC (see B1).
> 5. **§1 "adopted conventions".**
>    - All eight M11 §3 items are listed correctly. But "the split check (… never a STOP)" is imprecise: a declared
>      split other than P3 is a `GateStop` (`gate.py` l. 273–276), and overlapping ids are refused (l. 301–304). Only
>      the count lists are never a STOP.
>    - Also adopt the recorded environment (the harness `uv.lock` at `a3fedbb`, Python 3.13; only NumPy is checked) and
>      the per-node draw order (gate docstring l. 70–73).
> 6. **§1 V3-B and §7, power.**
>    - "g = 0.3" in D8-PASS is an effect size, while g elsewhere in the draft is the run price. Rename one of them.
>    - Quote V3-B's qualifiers: μ ≥ 1; 0.26 on T1 × 6; "only the 97.5 % step was simulated"; "its calibration comes
>      from the positivity screen, which is disclosed".
>    - Whether the paper reports D8-PASS's simulated power or a power recomputed for the realised node configuration
>      is not fixed by V3-B. Make it an option.
> 7. **§2 PRE-STAGE B and §4/§6.**
>    - Under B the "release steps" of §4 and the first STOP of §6 have no referent. Say so, or condition those lines on
>      PRE-STAGE.
>    - T1 needs code locks anyway: the G.5 draft (§6) makes them a P5 code requirement, so PRE-STAGE applies to T0
>      only.
>    - Under A, name the mechanism. `label_block.jsonl` holds every instance, so a lock at partition level needs
>      partitioned copies with receipts, or a reader that filters by the split file before parsing any value.
>    - List what may be read before release: diagnostics, counts.
>    - Note that the locks forbid reads but cannot prevent them (the G.5 draft says the same of its receipts).
> 8. **§4 step 4.** "Nothing in it may change after step 5" should read "after it is committed (step 4); the test
>    release row cites the final sha256". The record should also carry:
>    - the split-file sha256;
>    - the δ_n/σ table shas;
>    - the gate-input builder sha;
>    - the label-table shas of both sources;
>    - the included T1 node list;
>    - the fold, secondary and control arms (M8).
>    In the signature block, `offline_eval_sha256: <the reviewed gate-input builder's sha256>` names the wrong module:
>    rename the field to `gate_input_builder_sha256`.
> 9. **§4, "A gate run is never repeated after its output is seen".**
>    - Distinguish input-validation refusals (`ValueError`/schema errors, raised in `_validate` before any statistic
>      is computed) from statistical STOPs (`_point`, l. 386–418, raised after test values are used).
>    - Say what follows a statistical STOP: it is reported as a STOP with no verdict, and any remedy needs an author
>      row and is disclosed.
> 10. **Terminology.** offline_eval's "duplicates" are earlier evaluated configurations within a campaign (weight 1;
>     A2+ skip them, l. 6–9, 47–48). PRE-DUP's are cross-instance key matches. Give them different names to avoid
>     misapplying weights.
>
> ## Notes
>
> - The gate sha256 is verified (`ffb70d7a…`) and identical at `6aa9985c`. The offline_eval sha prefix `5990f384…`
>   matches.
> - The §1 quotations of R1-BX-D8 (with R1-BX-PROPOSED-CONFIRM D8), V3-A (1)–(3), V3-B (4)–(5), CONFIRM and D18 are
>   otherwise accurate. Citing R1-BX-PROPOSED-CONFIRM (D8) beside R1-BX-D8 would show that the "(proposed
>   operationalisation)" was confirmed.
> - §6 contains the right evaluation-seed STOP. Once M1 is fixed, requirement (6) (7006–7010 never used for training or
>   selection) is met.
> - The T0 rule (salt `c3_p3_split/v1`, test first) is structurally consistent with G5-SPLIT (test first, its own
>   salt).
> - I could not verify the quoted queue phrase "so analysis can start the day the labels unlock" (19–20 Nov) in the
>   repository. It is harmless.
>
> VERDICT: CHANGES REQUESTED

## Round 2 (`dc2a8a95 (rev 2)`)

> Reviewed base: dc2a8a95c93b8a7b10fb22fdbc456c9bdae0a037
>
> # Independent review: sweep-2 C3 analysis preregistration draft, round 2
>
> - **File:** `docs/r1/proposals/SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md`, revision 2 (292 lines), at `dc2a8a95`. The diff
>   against `0e68c1de` touches only this file (+246/−126).
> - **Checked again:** `r1/c3/gate.py` sha256 `ffb70d7a…37434ee` (unchanged).
> - **Read in addition to round 1:**
>   - `results/r1/noise/D28_REPAIR_20261027/summary.json` (structure and sha only)
>   - `sweep2/s2_c2_lib.py`
>   - `r1/c3/dataset.py` (`sweep_replay_inputs`)
>   - `r1/c3/audit.py` (`verify_evidence_completion`)
>   - `r1/c3/analysis_guard.py` (`require_d8_confirmation`)
>   - `r1/scripts/build_d28_noise_summary.py`
>   - `docs/r1/reports/M11_D8_PASS_20261116.md`
>   - PLAN rows: the 18 Oct C3 gate (l. 421), R1-C3 (ladder) (l. 420), R1-TRACKP-SFT-DEV (l. 1277)
> - **Script:** `/tmp/prerev/overlap2.py` recomputes the SFT/P3 overlap under revision 2's T0 key. It uses seeds and salts
>   only.
> - No label, evaluation block, result for seeds 7001–7010, or secret was read.
>
> ## Status of the round-1 findings
>
> | Round 1 | Status in revision 2 |
> |---|---|
> | B1 (R1-S2C3B-WDBC vs the T0 pin) | **Resolved** as author decision PRE-WDBC with options A/B/C. Some implementation detail is still open (Minor 3). |
> | M1 (train/dev utilities, seed blocks, oracle, A2) | **Resolved.** §3 gives one definition for every split. Step 2 releases only the train/dev label block. The train/dev blocks of the gate are built at step 5. Selection uses the label block only. The oracle is written out. PRE-A2 is added (Minor 6). |
> | M2 (sweep 1 not locked) | **Resolved in scope** (PRE-STAGE covers both sources; §6; step 4 disclosure; exam set). **New:** the start of the lock and its scope collide with authorized activities (Major N1). |
> | M3 (PRE-POOL authority, criterion) | **Resolved**, apart from the skill reference (Major N2). |
> | M4 (memory modes, sources, tiers) | **Resolved** (PRE-MEM, PRE-JOINT). One edge case is open (Minor 5). |
> | M5 (δ_n scaling, sources) | **Resolved** (PRE-DELTA). The pinned noise source is verified (Notes). T1 timing is open (Minor 7). |
> | M6 (PRE-DUP dev side, edge rules) | **Resolved.** |
> | M7 (partial T1, timing) | **Resolved** (PRE-T1). |
> | M8 (secondary test reads) | **Resolved in scope** (PRE-SECONDARY). Which code computes LOSO/LONO is open (Minor 4). |
> | M9 (evaluation-seed divergence; T1 K) | **Resolved** (PRE-DIV; §3 K line; §6 STOP). |
> | M10 (split specification) | **Resolved**, apart from one sentence that does not hold for T1 (Minor 2). |
> | Minors 1–10 | Resolved, except that the overlap figures are now stale (Minor 1). |
>
> ---
>
> ## Major
>
> ### N1. Start date and scope of the read STOP and the partition lock are not defined, and they collide with an authorized row and with the audit verification code
>
> - **Location:** §6, first STOP ("A label value of a test instance, or any evaluation value, read before step 5 —
>   sweep 1 included"); §2 PRE-STAGE A ("readers open only receipted partitions").
> - **Evidence:**
>   - R1-TRACKP-SFT-DEV (PLAN l. 1277) authorizes ENGINEERING SFT runs now on the sweep-1 table. It also says that
>     "sweep-1 B.2 的 label block 出来后接入". That label block covers every instance, P3 test instances included. Once
>     signed, the draft's STOP would either make these authorized runs a STOP with no transition rule, or be read as not
>     applying until step 2. The second reading leaves the window open between signature and release.
>   - `audit.verify_evidence_completion` (`audit.py` l. 1099–1170) re-derives and compares both role blocks from
>     `runs.jsonl` and `evaluation_block.jsonl`. `offline_eval._verify_evidence_inputs` (l. 108–117) calls it whenever
>     evidence is consumed. That verification reads evaluation values of every instance, and that conflicts with "no
>     evaluation value of any instance" before step 5 and with "readers open only receipted partitions".
>   - A procedure that must "actually prevent test reads before arms are frozen" needs a defined start date and a
>     defined exception for machine integrity checks.
> - **Fix:**
>   - (i) The STOP and the lock apply from the signature. From then on they narrow R1-TRACKP-SFT-DEV: engineering runs use
>     only the P3 train/dev label partitions. Reads before the signature are disclosed in the arms-frozen record, as step
>     4 already provides.
>   - (ii) Add a carve-out. Integrity verification (`verify_evidence_completion` and its equivalent for sweep 2) runs
>     inside the release step, by reviewed code that emits only pass/fail, counts and hashes. Its receipt replaces the
>     verification at consumption time for partitioned readers. No value is printed or stored outside the sealed tree.
>   - (iii) Name this exception in §6, so that the audit pipeline itself is not a STOP.
>
> ### N2. PRE-SELECT A compares RPS skills with different references, so the recommended pooled-versus-sweep-2-only choice is ill-defined
>
> - **Location:** §2 PRE-SELECT A ("the mean over nodes of the dev RPS skill (against the training base rate)").
> - **Evidence:**
>   - PRE-POOL compares two variants of each arm: one trained on sweep 2 alone, one on sweep 1 + sweep 2.
>   - "The training base rate" is a different distribution for each variant, so the two skills
>     1 − RPS/RPS_ref have different denominators.
>   - A variant can therefore win partly because its own reference is worse, not because its dev predictions are better.
>   - The same problem arises for A5's 2 × 2 choice (pool × Kev base).
>   - The node weighting (equal per node, including T1 nodes) is also left implicit.
>   - "On the PRE-DUP primary dev population" has no referent under PRE-DUP B.
> - **Fix:**
>   - Use one common reference per node for every candidate. For example, use the base rate of the **sweep-2 P3 train**
>     label block per node, or compare mean dev RPS directly (it lies in [0, 1] and is scale-free).
>   - State equal weight per node across both tiers.
>   - Add "the full dev population under PRE-DUP B".
>
> ---
>
> ## Minor
>
> 1. **§2 PRE-SPLIT B: overlap figures are stale.** Revision 2 changed the T0 key to
>    `sha256("c3_p3_split/v1:" + "<node>__s<seed>")`. The figures "4–7 … (6, 6, 7, 5, 5, 6, 4, 6)" were computed under
>    round 1's key (`"c3_p3_split/v1:<node>:<seed>"`). Under the revision-2 key, P3-test ∩ SFT-train is 5, 7, 6, 5, 6,
>    5, 6, 5 for digits, breast_w, climate, credit_approval, ionosphere, sonar, wdbc and tabular. That is a range of 5–7,
>    mean 5.6 (`/tmp/prerev/overlap2.py`). Replace the figures. The conclusion (B leaks test instances into A5) stands.
> 2. **§2 PRE-SPLIT A: one sentence does not hold for T1.** "The same string is hashed and is the gate's instance id"
>    is false there: G5-SPLIT hashes `<node>:<seed>`, not `<node>__s<seed>`. State that the T0 hash string is the
>    instance id, that T1 hashes per G5-SPLIT, and that the gate's instance id is `<node>__s<seed>` in both tiers. Note
>    also that the SFT builder (`sha256(salt:instance)`) cannot reproduce the T1 rule, so a Track P read of T1 needs the
>    split file, not the builder's salt.
> 3. **§2 PRE-WDBC B: implementation details are missing.**
>    - `_require_pins` binds `r1/c3/gate.py`, and `analysis_guard.require_d8_confirmation` binds that path's committed
>      sha to an affirmative CONFIRM-type row (l. 129–175). v3.1 therefore replaces v3 for **every** run, the 8-node
>      sensitivity included. Require a test that v3.1, given all eight T0 nodes, produces output identical to v3 (apart
>      from the version and sha fields).
>    - The new row must satisfy `_confirmation_commit`'s parser. Readers fail closed between the gate commit and the
>      row; say so.
>    - A declared node-set field changes the input contract. Name the schema (for example `r1_d8_gate_input/v3.1`) and
>      correct §9's "`r1_d8_gate_input/v3`".
> 4. **§2 PRE-SECONDARY A: LOSO/LONO tooling is unnamed.** The pinned gate STOPs on any T0 set other than the eight. It
>    cannot compute "the gate's IQM and PoI" for a held-out suite of T1 nodes, or LONO's per-node gap closed. Name the
>    code: v3.1 with a declared (possibly empty) T0 set, or a separate reviewed descriptive module. Say whether
>    eligibility applies. Say whether fold arms reuse the primary PRE-SELECT choices or are selected per fold on fold
>    dev data.
> 5. **§2 PRE-MEM C × PRE-DUP: one edge case has no rule.** An instance may have one mode with no remaining
>    positive-weight proposal and the other mode intact. Give the rule: for example, the instance takes the remaining
>    mode's U, disclosed, or the instance is left out.
> 6. **§2 PRE-A2: the options amend an author-fixed ladder without saying so.** A1's fit set ("dev campaigns") belongs
>    to the C3_DESIGN §5 ladder that R1-C3 (ladder) fixes (PLAN l. 420). Options A and B amend it. Say so. Either add
>    an option C "as designed (dev)", stating its consequence (A2's dev U in sample, which enters the dev denominator and
>    the B selection), or give the reason it is not offered.
> 7. **§2 PRE-DELTA: T1 σ timing is too late.** T1 σ_node is needed before training: it sets the soft-label width and g
>    in the decisions. Fix the G.1b summary's path and sha256 at step 2. The arms-frozen record already lists it. "Recorded
>    in the T1 test release row" is too late as the point where it is fixed. Keep it there only as a citation.
>
> ## Notes
>
> - **Verified:**
>   - The noise source is pinned in `sweep2/s2_c2_lib.py` (l. 49–50) and in the sweep-1 index. Its sha256 `3d12ce05…34310`
>     matches the file.
>   - The file covers all eight T0 nodes, openml_climate included, and was built from the repaired-node and climate
>     re-measurements (`build_d28_noise_summary.py`).
>   - Its edit records carry `sd_joint` and `material`, so `dataset.noise_table`'s definitions apply.
>   - `dataset.sweep_replay_inputs` uses this pinned source for sweep tables.
> - **Verified:** `sft_data.dup_key`, `sft_data.instance_universe` and `rules.decide` exist.
> - **Verified:** the SFT builder with salt `c3_p3_split/v1` and 9 test / 3 validation reproduces the T0 P3 assignment.
> - **Verified:** the G5-SPLIT quotation matches the G.5 draft (l. 161–162).
> - **Verified quotations:** the 18 Oct gate (l. 421), R1-MAIN-PROPOSER-ITEMS, the K/seed line, the divergence rule, and
>   the V3-B qualifiers. In D8-PASS, g is the true gap closed under the alternative (report l. 37, l. 48), so "effect
>   size 0.3" is a fair rendering.
> - The adopted-conventions paragraph is now precise, and it includes the environment and the draw order.
> - Requirement (6) (7006–7010 never used for training or selection) is met by §3, step 3 and §6.
>
> VERDICT: CHANGES REQUESTED

## Round 3 (`84fd832e (rev 3)`)

> Reviewed base: 84fd832edbd59148aea51912883c13c32f15db3e
>
> # Independent review: sweep-2 C3 analysis preregistration draft, round 3
>
> - **What I read:** `git diff dc2a8a95 84fd832e`, which changes only
>   `docs/r1/proposals/SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md` (+51/−25). I re-read the changed sections in context:
>   PRE-WDBC, PRE-SPLIT, PRE-MEM, PRE-SELECT, PRE-A2, PRE-DELTA, PRE-SECONDARY, §6 and §9.
> - **Gate checksum:** `r1/c3/gate.py` sha256 is still `ffb70d7a…37434ee`.
> - **Worktree:** clean. No labels, results or secrets were read.
>
> ## Status of the round-2 findings
>
> | Round 2 | Status |
> |---|---|
> | N1 (start date and scope of the read STOP; collision with R1-TRACKP-SFT-DEV and the audit verification) | **Resolved.** §6 now opens with "From the signature on". From then it narrows R1-TRACKP-SFT-DEV's ENGINEERING runs to the sweep-1 label block of P3 train/dev instances. Reads made before the signature are disclosed in the arms-frozen record. `verify_evidence_completion` gets an integrity carve-out: before step 5 it runs only inside the release step, through reviewed code that outputs pass/fail, counts and hashes. The carve-out is repeated in the first STOP bullet and listed in §9. |
> | N2 (PRE-SELECT reference) | **Resolved.** Every variant is scored against one common reference per node (the base rate of the sweep-2 P3 train label block). Nodes are weighted equally. The dev population is stated for both PRE-DUP options. |
> | Minor 1 (stale overlap figures) | Resolved. The figures are now 5, 7, 6, 5, 6, 5, 6, 5, matching `/tmp/prerev/overlap2.py`. |
> | Minor 2 (T1 hashing) | Resolved. The gate id is `<node>__s<seed>` in both tiers. T1 hashes `<node>:<seed>`. The builder reproduces T0 only, and T1 builds read the split file. |
> | Minor 3 (v3.1 details) | Resolved: v3.1 replaces `gate.py`, the eight-node reproduction test exists, the schema is `v3.1`, and the binding row is CONFIRM-type. One wording point remains (Minor 1 below). |
> | Minor 4 (fold-analysis tooling) | Resolved: the module is named, eligibility applies, and fold selection is on the fold's dev instances. One detail remains (Minor 2 below). |
> | Minor 5 (PRE-MEM C × PRE-DUP) | Resolved (other mode's U; instance left out if neither mode has any). |
> | Minor 6 (PRE-A2 amendment status) | Resolved. Option C ("as C3_DESIGN") is recommended and needs no amendment. Options A and B are marked as amendments that need an author row. One consequence remains unstated (Minor 3 below). |
> | Minor 7 (T1 σ_node timing) | Resolved. It is recorded in the T1 train/dev release row before training. |
>
> No blocking or major finding remains. The three minors below can be fixed in the signed copy without another review
> round.
>
> ## Minor
>
> 1. **PRE-WDBC B: "byte for byte" cannot hold literally.** The reproduction test says v3.1 "reproduces v3's output
>    byte for byte". But the output carries `gate_version`, `protocol.gate_sha256`, the schema and the new declared
>    node-set field. These differ between v3 and v3.1 by construction.
>    - **Fix:** "identical except for `gate_version`, `protocol.gate_sha256`, the schema strings and the declared
>      T0-set field".
> 2. **PRE-SECONDARY, leave-one-suite-out under v3.1: the empty T0 set is not covered.** Each held-out suite's
>    statistic covers only that suite's T1 nodes, so the fold-analysis module calls v3.1 with an **empty** declared T0
>    set. The v3.1 description says "a subset of `T0_NODES`" but does not say whether the empty set is accepted.
>    - **Fix:** state that v3.1 accepts an empty declared T0 set (tested), or that the module handles leave-one-suite-out
>      itself and checks the result against the gate's statistics.
> 3. **PRE-A2 C × PRE-SELECT: A2's pooled-versus-sweep-2-only choice is degenerate.** Under the recommended C, A1/A2's
>    constants are fitted on the dev label block. PRE-SELECT then scores A2's variants on that same dev population,
>    in sample. RPS is a proper scoring rule, so the constant fitted to the evaluated set (sweep-2-only) wins or ties by
>    construction. The "choice on validation" for A2 is therefore moot.
>    - **Fix:** under C, state that A2 is sweep-2-only by declaration, with PRE-POOL applying to A3 and A5 only, and
>      disclose the reason.
>
> ## Notes
>
> - PRE-SELECT A's reference ("sweep-2 P3 train label block") also covers T1. PLAN uses "sweep-2 (T0 or T1) label
>   table" (R1-BX-D8, l. 752), so this is consistent. Writing "the node's own P3 train label block (sweep 2 for T0, G.5
>   for T1)" would remove any doubt.
> - Under PRE-A2 C, A2's in-sample dev U makes the dev denominator (oracle − A2) smaller, so eligibility becomes
>   stricter (conservative). The draft discloses this.
> - The pinned noise source, the T0/T1 split rules, the gate pin and the evaluation-seed rules were verified in rounds
>   1–2. This revision leaves them unchanged.
>
> VERDICT: ACCEPTED

## Round 4 (`95da769e (rev 4)`)

> Reviewed base: 95da769e72cfe5a865025f8cfe02d120da5e42af
>
> # Independent review: sweep-2 C3 analysis preregistration draft, round 4 (confirming the round-3 minors)
>
> **What I checked.** I read `git diff 84fd832e 95da769e`. It changes only
> `docs/r1/proposals/SWEEP2_ANALYSIS_PREREG_DRAFT_20261121.md`, with 7 lines added and 3 removed. I re-read the
> surrounding text of each hunk. The sha256 of `r1/c3/gate.py` is still `ffb70d7a…37434ee`, and the worktree is clean.
> I read no labels, results or secrets.
>
> ## Round-3 minors
>
> | Round 3 | Status |
> |---|---|
> | 1. v3.1 reproduction "byte for byte" | **Resolved.** It now reads "identical except for the gate version, gate sha256, schema strings and the declared node-set field". These are exactly the fields that must differ. |
> | 2. Empty declared T0 set for leave-one-suite-out | **Resolved.** The draft now says "v3.1 accepts an empty declared T0 set (used by leave-one-suite-out folds), with a test". |
> | 3. A2's pooled-versus-sweep-2-only choice is degenerate under PRE-A2 C | **Resolved.** The draft now says "In every option A2 uses sweep 2 only; PRE-POOL applies to A3 and A5", and the reason is disclosed under C. |
> | Note (PRE-SELECT reference for T1) | **Adopted.** It now reads "the node's own P3 train label block (sweep 2 for T0, G.5 for T1)". |
>
> I found nothing new in this diff.
>
> ## Notes (optional, for the signed copy)
>
> - PRE-SELECT A still says "Per arm: pooled versus sweep-2-only". Since PRE-A2 now restricts PRE-POOL to A3 and A5,
>   "Per arm (A3, A5)" would match it. The meaning is already clear from PRE-A2's new line.
> - The new v3.1 sentence in PRE-WDBC B runs past the file's usual line width. This is cosmetic only.
>
> VERDICT: ACCEPTED

---

Code-Commit: 95da769e72cfe5a865025f8cfe02d120da5e42af
Verdict: ACCEPTED

Accepted commit: `95da769e72cfe5a865025f8cfe02d120da5e42af` (round 4; draft revision 4).
