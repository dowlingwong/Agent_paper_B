# Paper B readiness audit: is the experiment framework ready to run?

2026-10-04, working tree of `~/Documents/GitHub/agent-checkpoint-intervention`
(branch `local-work-2026-09-26`, HEAD `c5a8638d` plus the uncommitted
configurator scaffold). Checks were re-run on CPU (Python 3.12 venv built from
`requirements.lock`). This is an engineering audit, not a design review.

**Verdict: not ready to run the experiment or any configurator fitting.** The
analysis side of controller design v2 is implemented and passes its CPU tests.
The *run* side is not ready:

- the task fails its realism gate;
- the live tooling (F10) does not exist;
- no real agent path has been exercised;
- no agent transcripts are recorded;
- every runtime binding in the contract is still null.

## 1. What exists and passes on CPU

| Component | File(s) | Check run 4 Oct |
|---|---|---|
| Proposed continuation-value rule, repeated-myopic, BAVAR-inspired VOI, constant-reserve ablation, fixed regimes, matching report | `control/timing.py` | `tests/control` 188/188 pass |
| Shared two-phase hard-budget allocator | `control/allocator.py` | in the 188 |
| Evaluation harness: development/test split, allocator re-run per bootstrap draw, family-cluster bootstrap, Bonferroni readings, N1 p-grid, m ≤ 3 | `control/evaluate_tree.py` | in the 188 |
| `b_branch_v2` records, lineage checks, three-regime tree through the real filesystem fork path | `control/branch_tree.py` | in the 188 |
| Engineering smoke (one-checkpoint path) | `experiments/paper_b/smoke_b.py` | 11/11 engineering checks pass |
| Candidate-consistency live task (attempt 1), mock provider | `experiments/paper_b/task_cc_live/` | runs; see §2 |
| Contract v2 + launch validator | `protocols/paper_b/contract_v2.yaml`, `launch_validator.py` | validator used by the fixture driver |
| Configurator scaffold (serialiser, Kev/CLM encoder slots, projection, shared heads) | `control/configurator/` | 22/22 new tests pass (B_DAC_CONFIGURATOR_AMENDMENT_20261004.md) |

## 2. What blocks a run

| # | Gap | Evidence | Owner / gate |
|---|---|---|---|
| G1 | **Task realism fails** (F9: R1 and R4 for the typical behaviour) | Re-ran `cc_live_realism.py --families 8` on 4 Oct. For the typical behaviour, the now/later/never-best family counts are 0/5/3 and `verify_gain_max = −0.040`; R1 and R4 are False, all other checks True. Matches TASK_REALISM_REPORT. | OPEN_ITEMS B1: attempt 2 under P-B1 (one attempt, frozen criteria, failure stops this setup) |
| G2 | **F10 live tooling absent** (`run_screen.py`, `bind_runtime_artifacts.py`) | Files do not exist. There is no `--mode live` refusal, no pre-dispatch caps and no dry run. | W, only after G1 passes |
| G3 | **No real agent path exercised.** The live task uses the toy `MockModelProvider`; the Pi runtime needs a Node build and a model endpoint | `cc_live_run_task.py` PI_PATH_NOTE | X (Ada) |
| G4 | **No transcript / history capture.** `execute_tree_v2` records workspace hashes only. No agent messages or tool calls are stored per branch or checkpoint. | `branch_tree.py` | W: B-DAC4. Needed by any text configurator (Kev or CLM). Also useful for auditing the telemetry configurator. |
| G5 | **Contract bindings null** (34 `null` fields): model/artifact hashes, harness commit, task generator, evaluator, verifier, split manifest, ceilings, qualification report, freeze commit | `contract_v2.yaml` | X/D at qualification |
| G6 | **Design-ready review not closed.** R2 fix commits not independently re-reviewed against the 27 Sept "design-ready: no"; novelty verdict pending; BAVAR preprint unread | OPEN_ITEMS B2 | W (separate session) + D |
| G7 | **B-TKV1/B-TKV2 design items open** (offline vs online budget; shrinkage baseline) | OPEN_ITEMS B3 | W |
| G8 | **Configurator decisions open** (D-DAC1–6) and contract v3 fields | amendment §6 | D, before the pilot |

## 3. Shortest path to a first real run

1. **G1.** Write the attempt-2 task design. Freeze it before running:
   - where verification gains diagnostic value beyond refitting;
   - where waiting trades information against delay;
   - the thresholds.

   Then run F9 once. If it fails, P-B1 applies.
2. **G4 and G8**, in parallel with step 1. Add history capture to the tree
   driver and task adapter. Decide D-DAC1–6. Freeze the Kev question set or
   the CLM variant.
3. **G6.** Independent R2 re-review and the novelty verdict.
4. **G2.** Build F10 with CPU tests, including the live refusal and caps.
5. **G3/G5 (Ada, authorised).** Bind Devstral and the encoder artifacts, then
   qualify both lanes by **15 Nov** (P-B2).
6. **Bounded screen (96 leaves), then pilot (384 leaves).** Fit the
   configurator heads on development families only, choose the route and
   freeze the design by **30 Nov**.

Configurator "fine-tuning", in the sense of fitting heads, starts at step 6.
Before that, only scripted trees exist, and they are not evidence.
