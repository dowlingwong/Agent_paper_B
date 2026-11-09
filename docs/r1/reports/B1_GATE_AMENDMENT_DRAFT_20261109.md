# B1 anchor gate — post-hoc amendment R4 (draft for the appendix, 9 Nov 2026)

**Status.** AI-assisted draft (Claude, Mac-local overnight agent, `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 4). It takes effect only if the independently reviewed diagnosis report `reports/B1_STOP_DIAGNOSIS_<date>.md` classifies the B1 STOP of run `6835_20261108_a` as **D with H1 supported** (the two random anchors cannot be ordered) under `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §4. A D verdict on H2 alone, a P verdict or a D7 failure is not covered and goes to the author (PLAN §10 `R1-EXAM-B1-ANCHOR-R4`). The numbers and statements marked ⟨…⟩ are filled in from that report; nothing here is a result, and no diagnosis finding is assumed.

## 1. Original criterion

- **RUNBOOK X.3** (Track X, discrimination check with anchors): random-valid < scripted on audited mean proposal increment, and `qwen2.5-coder:7b` reproduces its pilot duplicate rate within CI. "If the exam cannot order the anchors, STOP: it has no discriminating power."
- **Implementation** (`r1/scripts/exam_runner.py::anchor_gate`, frozen B1 checkout `68357d3d`): per-instance means of `delta_audit` for `scripted` and `random_valid` (12 instances = 3 nodes × instance seeds 9001–9004; audit seeds 9101–9104); `paired_instance_bootstrap(scripted, random_valid)` with 2000 resamples, seed 20261026, 95 % percentile interval; STOP if `difference_lower ≤ 0`; then the 7B duplicate-rate check against the pinned interval [0.4239, 0.5800].
- The criterion was fixed before Stage A. It was never exercised on real data before 8 Nov, because DRYRUN overrides it.

## 2. What happened

B1 run `6835_20261108_a` stopped on 8 Nov 2026 at 01:19:49 UTC with `STOP: random-valid < scripted cannot be shown; no discriminating power`, after all 36 anchor roots and before any candidate (`reports/B1_STOP_6835_20261108.md`). No candidate value existed at the stop.

Recomputed gate (diagnosis D1): point ⟨…⟩, 95 % interval [⟨…⟩, ⟨…⟩] for scripted − random_valid; per node (standardised by σ_joint): ⟨digits_mlp …⟩, ⟨openml_credit_approval …⟩, ⟨openml_ionosphere …⟩. 7B duplicate rate (D7): ⟨…⟩ against [0.4239, 0.5800].

## 3. Diagnosis (summary to be filled in)

Class ⟨D⟩ with hypotheses ⟨H1 / H2⟩ supported and H3 (power) ⟨supported / not supported / undetermined⟩ (`reports/B1_STOP_DIAGNOSIS_<date>.md`, review ⟨path of the accepted diagnosis review⟩). The code checks (`reports/B1_STOP_CODE_CHECKS_20261109.md`) found no engineering defect: both anchors' proposal laws, the value grid, the node configurations, the bootstrap and the gate statistic are identical to what Stage A accepted. Both anchors are random proposers: `scripted` is the E1b stand-in (one numeric symbol × a log-uniform factor in [1/3, 3], 30 % categorical switch on OpenML nodes) and `random_valid` draws a uniform active key and a uniform grid value. No pilot ever tested that one beats the other.

## 4. Amendment (R4)

- **Removed:** the anchor-ordering STOP. `scripted − random_valid` is still computed by the same code and recorded in the batch state as a descriptive field (`scripted_minus_random`, with `scripted_minus_random_role` = `descriptive_only (R1-EXAM-B1-ANCHOR-R4; ordering STOP removed post hoc)`). In the run outputs it is in `batch_state.json` (the anchor-gate record), not in `b1_summary_verified`; the B1 report reads it from there.
- **Kept unchanged:** the 7B duplicate-rate STOP and its pinned interval; all other B1 STOPs; the frozen B1 rule `x5_rule_v2` (which carries the ranking); seeds, budgets, pins and nodes.
- **Reported:** the three anchors' increments are shown descriptively next to the candidates in the B1 table.
- **Not done:** no replacement ordering gate was chosen. Any new ordering criterion chosen after seeing these anchors would not be a test.

**Reason.** The gate was meant to show that the exam can separate proposers. Two random proposers are not a meaningful pair for that purpose, and the diagnosis classified the stop as a design issue (class D, H1) and found no engineering defect ⟨and, if so found: the interval was not narrowed enough by more instances to change this — fill in from the H3 result⟩. The spread among the candidates under the frozen rule shows discriminating power more directly.

**Decision.** The author chose R4 on 9 Nov 2026, conditional on the diagnosis confirming a design issue (PLAN §10 `R1-EXAM-B1-ANCHOR-R4`). Code: branch `mac-b1-r4-20261109`, gate change @ `fb57c6a4`, configuration re-pin and exact restart checkout @ ⟨commit⟩; independent review ⟨path of the accepted R4 review⟩.

## 5. Appendix text (draft)

> **Post-hoc amendment to the anchor check (B1).** The pre-specified B1 procedure required that a random-valid proposer be shown to be worse than a scripted random proposer (paired instance bootstrap on the audited mean increment, lower 95 % bound above zero) before any candidate ran. In the first B1 run this check failed (scripted − random-valid: ⟨point⟩ [⟨lower⟩, ⟨upper⟩]; 12 instance pairs). A read-only diagnosis found no implementation defect and attributed the failure to the design of the check: both anchors are random proposers ⟨describe the difference found in the diagnosis⟩, and no pilot had established an ordering between them. After seeing these anchor results, and before any candidate had run, we removed the ordering as a stopping condition and report the anchors descriptively instead; the duplicate-rate check on qwen2.5-coder:7b was kept unchanged (⟨rate⟩, interval [0.4239, 0.5800]). The B1 run was restarted from scratch under a new run identifier; the stopped run is preserved. Table ⟨X⟩ lists the original check, its numbers and the amended procedure.
