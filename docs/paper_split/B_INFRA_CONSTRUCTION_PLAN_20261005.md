> Copied from the source repository at S = 4154f153, 7 October 2026; this committed v1 plan is retained
> for provenance. The source copy is the historical one.

# Paper B infrastructure-construction plan — DAC framing with a post-trainable configurator

5 October 2026. **Status: DRAFT, prepared by an AI agent (Claude); not adopted.**
Goal: get every piece of infrastructure ready so that the Paper B experiment
("when should an executor agent spend its one verification?", framed as
budget-constrained dynamic algorithm configuration with a learned configurator)
can be run on the Ada server inside the P-B2 cutoffs (lanes qualified by
**15 Nov 2026**, screen + pilot done and design frozen by **30 Nov 2026**).

This plan builds infrastructure. It does not change B's estimands, primary
outcome U, controllers, allocator, comparators, budget, N1 evaluation or gate
sequence (RUNBOOK §12, §12.2a; `B_CONTROLLER_DESIGN_20260927.md`), and it does
not unblock the two scientific gates on its own: task realism (OPEN_ITEMS B1)
and the design-ready re-review (B2). Those gates are listed here only where the
infrastructure depends on them.

Sources read for this plan: `docs/paper_split/{OPEN_ITEMS,RUNBOOK,STATUS}.md`,
`B_DAC_CONFIGURATOR_AMENDMENT_20261004.md`, `B_READINESS_AUDIT_20261004.md`,
`B_CONTROLLER_DESIGN_20260927.md`, `TASK_REALISM_REPORT.md`,
`AB_REPO_SPLIT_CHECKLIST_20261005.md`, `A_REVISION_RECORD_20261005.md`,
`protocols/paper_a/ADA_RUNBOOK_20261005.md`, the `control/` and
`control/configurator/` packages, `protocols/paper_b/contract_v2.yaml`;
`github.com/dowlingwong/autoresearch_harness` at `da8dcbd` (clone);
`github.com/jaredpalmer/kev` and `github.com/Contrastive-LM/CLM` (READMEs);
`.agents/skills/typesafe-ai/SKILL.md`.

---

## 0. Answers to the three questions

**Do we already have the experiment framework?** Partly. The *analysis* side
exists and passes on CPU: paired tree records (`control/branch_tree.py`), the
shared two-phase hard-budget allocator, the proposed continuation-value rule
and its matched comparators (`control/timing.py`), the development/test
evaluation harness with family-cluster bootstrap and the N1 replay-discrepancy
grid (`control/evaluate_tree.py`), the contract and launch validator, and the
engineering smoke. The *run* side does not exist: the candidate-consistency
task fails its realism gate (F9), there is no live tooling (`run_screen.py`,
`bind_runtime_artifacts.py`), no real agent has been exercised through the
tree, no agent transcript is recorded, and all 34 runtime bindings in
`contract_v2.yaml` are null (readiness audit G1–G8).

**Do we have the harness / governance panel?** Yes, in a separate repository.
`autoresearch_harness` is the ETAAI control plane: a trial lifecycle state
machine, editable-scope enforcement, append-only JSONL trial and event ledgers,
keep/discard owned by the framework, provenance hashes, and paper-metric
exports. It also carries a `reliability` scaffold (schema version 1.0,
2026-08-01) with exactly B's vocabulary: `ControlAction`
{continue, verify, recover_*, escalate, abstain, terminate}, a
`ControllerPolicy` registry (never/always/periodic/random-matched/threshold/
myopic-VOI/oracle), sealed fault manifests with hidden-truth visibility
classes, independent adjudication records, group-isolated split manifests and
immutable training-view builders (SFT / recovery / outcome-only / process /
abstention). That scaffold is a typed skeleton with synthetic fixtures
(`configs/reliability/experiments/R1_P_synthetic.yaml`, two test files); it has
never run a real trajectory. Nothing in this repository imports it. So: the
governance *records* and *vocabulary* exist; the governance *of B's live tree*
does not.

**Do we have a Jev-like configurator?** A slot, not a model. Jev itself is
TypeSafe's hosted System One model (the `typesafe-ai` skill is in
`.agents/skills/`); it cannot be post-trained by us and is not reproducible
offline, so it is a reference point, not a component. Two open substitutes are
already stubbed as encoder slots in `control/configurator/encoder.py`:

| | Kev (jaredpalmer/kev, Apache-2.0) | CLM (Contrastive-LM/CLM, Apache-2.0) |
|---|---|---|
| Output | calibrated probabilities to typed noul / choice / score questions over a document | contrastive state and action embeddings; softmax over candidate actions |
| Backbone | Qwen family, 0.8B / 4B / 9B / 27B | frozen Qwen3-8B, last-token pooling + 20M-parameter head (`CLM-v0.1-8B`) |
| Context | 8,192 tokens validated (27B: 65,536) | 2,048 tokens default |
| Runs on | CUDA, **MLX (Mac)**, local HTTP server | vLLM pooling server (GPU) + `clm-serve` API |
| Post-training | rank-16 LoRA on JSONL (request + label); "10–20 % held out"; example gain 67.7→73.6 % on 1,050 records | `train/finetune.py`: head retraining on a frozen encoder; adapters for agentic traces and typed decisions |
| Domain | general document classification | post-trained on 1M agent trajectories |

Both slots refuse to run without a complete pinned binding and no network
call, and both are exercised only through fakes (22 CPU tests). No encoder has
read a real transcript, because no transcript exists (G4).

---

## 1. Definition of "infrastructure ready"

The experiment is ready to run when all of the following hold, each verified
by a command that is recorded in `VALIDATION.md`:

- **R-1 Records.** Every branch and every checkpoint produce a
  `DecisionHistory` (agent messages, tool calls, tool results, observations,
  checkpoint markers; no outcome, grade or hidden-test field), lineage-checked
  (H₂ ⊇ H₁, later/never share H₂), content-addressed, and mirrored as
  harness-compatible reliability events in an append-only ledger.
- **R-2 Live lane.** `run_screen.py` executes a frozen 96-leaf screen against a
  bound Devstral endpoint on Ada with: `--mode live` refused unless the
  contract is fully bound and an authorisation record exists; pre-dispatch
  caps (leaves, tokens, wall-clock, paid API = 0); a CPU dry run with a
  scripted model; resume after an operator stop; sealed design SHA-256.
- **R-3 Encoder lane.** The chosen primary encoder (D-DAC2) and its ablation
  encode saved transcripts offline with a pinned revision, a frozen question
  set or head hash, a cache keyed by (encoder fingerprint, text sha256), and
  an end-to-end CPU test that fits heads on development families only.
- **R-4 Contract.** `contract_v3.yaml` carries the configurator block, the
  encoder binding, the model/harness/task/evaluator/verifier/split hashes, the
  ceilings and the qualification report; `launch_validator.py --for-launch`
  passes for the screen phase and refuses every later phase.
- **R-5 Governance.** The ledger reproduces the paper-facing numbers
  (`evaluate_with_configurator` from ledger exports equals the live report),
  and a `matching_report` fails if two controllers ever saw different feature
  maps.
- **R-6 Post-training lane (extension; see §4, WP6).** A labelled decision set
  from outside every evaluation family, with a leakage audit, and a
  reproducible Kev-LoRA or CLM-head training run that writes a new pinned
  encoder revision. Not on the critical path.
- **R-7 Reproduction.** A `make reproduce-b` that rebuilds the screen report
  from the ledger in a clean clone of the B repository, with hashes matching.

---

## 2. Target architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │  B repository (agent-verification-timing)        │
                    │                                                  │
 task generator ──► │  branch_tree (now / continue→later,never)        │
 (attempt 2)        │      │  Pi runtime fork (pi_fork, history_retention)
                    │      ▼                                           │
                    │  DecisionHistory capture  ──► reliability-event  │
                    │  (B-DAC4)                     ledger (WP3)       │
                    │      │                                           │
                    │      ▼                                           │
                    │  serialiser ─► encoder slot ─► projector ─► heads│
                    │  (configurator; Kev on Mac / CLM on Ada)         │
                    │      │                                           │
                    │      ▼                                           │
                    │  allocator + evaluate_tree (unchanged)           │
                    │      │                                           │
                    │      ▼                                           │
                    │  matching_report, reproduce-b, release-b         │
                    └─────────────────────────────────────────────────┘
      Ada host: Devstral endpoint (B-owned port) · CLM pooling server · screen/pilot
      Mac:      Kev MLX offline encoding · analysis · tests
      Titan:    optional Kev-4B/9B CUDA encoding; not required
```

Principles carried over from design v2 and the amendment:

1. **No encoder weights are updated on evaluation families.** Fitting the
   configurator means fitting the projector and the shared ridge heads on
   development families; encoder post-training is a separate lane (WP6) on
   data from outside every evaluation split.
2. **Matched information and capacity.** Every controller sees the same
   feature map; the matching report is the guard.
3. **Harness as record keeper, not as executor.** We do not port the tree onto
   `autoresearch_harness`'s claw worker. The tree keeps the Pi fork path that
   Paper A's E-R2 panel already uses on Ada. The harness contributes its event
   schema, ledger discipline and adjudication vocabulary through an adapter.
4. **Frozen before run.** Task design, question set, feature set, projection
   and thresholds are sealed with SHA-256 before any pilot outcome exists
   (D-DAC1–6, P-B1).

---

## 3. Gap analysis

| Gap (readiness audit id) | What exists | What is missing | Work package |
|---|---|---|---|
| G1 task realism | generator, verifier, realism runner, frozen R1–R9 | attempt-2 design where verification has diagnostic value beyond refitting for the *typical* behaviour | WP2 (design, D + W) |
| G2 live tooling | E-R2's `panel_v2` driver on Ada (proxy, smoke, authorise, live, resume, SIGTERM stop) for Paper A | B equivalents `run_screen.py`, `bind_runtime_artifacts.py`; live refusal; caps | WP4 |
| G3 real agent path | Pi stack (`pi_fork`, `pi_rpc`, `model_client`, `registered_tools`, `history_retention`), Devstral deployment pattern (`replay_panel_v2_endpoint.json`, port 18083) | B endpoint file on its own port; task adapter from `cc_live_run_task.py` to the Pi runtime | WP4 |
| G4 transcript capture | `history_retention.py` stores raw Pi session JSONL by digest; `branch_tree` stores hashes only | `DecisionHistory` per branch and checkpoint; lineage check; serialiser input | WP3 |
| G5 contract bindings | `contract_v2.yaml`, `launch_validator.py` | `contract_v3.yaml` with configurator block; binding script | WP4, WP5 |
| G6 design-ready review | R2 fix commits exist | independent re-review; novelty verdict; BAVAR read | gate, not infra (§6) |
| G7 B-TKV1/2 | — | offline vs online budget separation; shrinkage baseline | WP5 (fields), design D |
| G8 D-DAC1–6 | amendment §6 | decisions | §5 |
| governance | harness control plane + reliability scaffold in another repo | adapter, ledger, adjudication of leaves | WP3, WP7 |
| post-training | Kev LoRA and CLM head-retraining tooling upstream | labelled set, leakage audit, run scripts, pinned outputs | WP6 |
| repository | `AB_REPO_SPLIT_CHECKLIST_20261005.md` | the B repository itself; uncommitted scaffold | WP0 |

---

## 4. Work packages

Owner codes as in OPEN_ITEMS: **W** any agent, **D** author decision,
**X** Ada access or another external step. "Done when" is the test that
closes the item; each closure adds a VALIDATION.md row.

### WP0 — Commit the scaffold and create the B repository (W, then D)

Prerequisite for everything else; `AB_REPO_SPLIT_CHECKLIST_20261005.md` has
the file lists and the copy commands.

1. Commit the uncommitted B work in this repository: `control/configurator/`,
   `tests/control/test_configurator.py`,
   `experiments/paper_b/configurator_scripted.py`, the two B docs and the
   shared-doc edits. (Note: the shared docs also hold the A revision's
   uncommitted lines; commit both sets, or let the A session commit first.)
2. Push `main`; record snapshot `S`.
3. Checklist Phases 1–2: create `~/Documents/agent-verification-timing` from
   `S` with the same relative layout; copy the Pi stack and `third_party/pi/`;
   B-only Makefile (`paper-b`, `smoke-b`, `release-b`, `check-release-b`,
   `test`); `PROVENANCE.md`; B copies of the shared records.
4. Add `autoresearch_harness` as a dependency of the B repository: pin to a
   commit (`da8dcbd` or later) and install as `autoresearch` via `uv`
   (`pyproject.toml` exists there). Do **not** copy its source.

Done when: in a fresh clone of the B repository, `tests/control` (188 incl.
22 configurator) and `tests/release` pass, `smoke_b.py` reports 11/11,
`launch_validator.py --for-launch` refuses every phase, `make paper-b` builds,
`import autoresearch.reliability` works.

Phase 3 (removing B from this repository) waits until Paper A is submitted.

### WP1 — Adopt the framing and freeze the configurator decisions (D)

Decisions, recorded in a dated `B_DECISIONS_20261005.md` and as RUNBOOK §15
"adopted":

| ID | Decision | Recommendation (from the amendment unless noted) |
|---|---|---|
| D-DAC1 | DAC as framing vocabulary, two declared deviations (budget-coupled instances; two-step binary action), no method claim | adopt |
| D-DAC2 | primary encoder slot | **Kev-4B as primary, CLM `clm_state_head` as ablation.** Reason: Kev runs offline on the Mac from saved transcripts, so the encoder lane does not compete for Ada cards with the executor and qualifies without X access; its typed questions make the configurator inspectable; its 8k context fits a serialised H₂ without truncation. CLM's 2k context forces aggressive truncation of H₂. |
| D-DAC3 | freeze the Kev question set (`KEV_QUESTIONS_DRAFT`: staleness, shift suspicion, candidate quality, expected verification gain, progress) | freeze after WP3 produces ten real development transcripts to sanity-read against; before attempt 2 runs |
| D-DAC4 | primary feature set | `telemetry+embedding`; `telemetry` and `embedding` as ablations |
| D-DAC5 | projection | `standardize` for Kev; PCA k = 8 for CLM |
| D-DAC6 | Kev size | 4B (validated 8k context; runs on a 32 GB Mac in MLX) |
| **D-DAC7** (new) | post-training scope: is encoder post-training (WP6) (a) out of the primary design, run only as an extension with its own authorisation; (b) in the primary design with an external training set; or (c) dropped | (a). The data scale (≤ 80 original roots in 40 families) cannot support it inside the evaluation; an external set can, but it is a second study. |
| **D-DAC8** (new) | governance integration depth: (a) ledger + adjudication adapter only; (b) also run the executor under the harness control plane (scope enforcement, keep/discard) | (a) for the screen and pilot. (b) would replace the Pi fork path that E-R2 already exercises and is not needed for B's estimand. |

Choosing any of these after seeing pilot outcomes is a forking path.

### WP2 — Task attempt 2: realism before tooling (D + W; critical path)

Not infrastructure, but WP4–WP5 cannot be qualified without a task that
passes R1–R9, and P-B1 allows exactly one attempt.

1. Write `experiments/paper_b/task_cc_live/ATTEMPT2_DESIGN.md`: where
   verification gains diagnostic value beyond refitting for a competent fit;
   where waiting trades information against delay; the frozen thresholds
   (R1–R9 unchanged unless a change is justified before the run). Seal with
   SHA-256.
2. Implement the generator and verifier changes; keep attempt 1 unchanged in
   the tree as the recorded failure.
3. Run `cc_live_realism.py` once on CPU with the scripted behaviours.

Done when: the realism report passes all nine checks for every behaviour, or
P-B1's failure disposition applies and this plan stops at WP0/WP3 (both still
useful for a later redesign).

### WP3 — Decision-history capture and the governance ledger (W)

B-DAC4 plus the harness adapter.

1. `control/history.py`: `DecisionHistory` record — allowlisted event kinds
   (task, assistant, tool_call, tool_result, observation, checkpoint), the
   checkpoint step, root/template/family ids (redacted later by the
   serialiser), raw sha256, and the Pi session digest from
   `history_retention`. Built from the Pi session JSONL at fork time, so the
   same bytes that the checkpoint layer already binds are what the encoder
   reads.
2. `branch_tree.execute_tree_v2`: emit `h1` at checkpoint 1 for every root and
   `h2` at checkpoint 2 for the continue branch; store them beside the
   `b_branch_v2` records; extend the lineage checks: H₁ is a prefix of H₂;
   later and never cite the same `h2` digest; no event after the decision
   step.
3. `control/governance.py`: adapter that writes each tree event as an
   `autoresearch.reliability.schema.events.ReliabilityEvent` with parent
   links and integrity hashes: proposal (root), action_request/result
   (verify/continue), state_snapshot (workspace hash), verifier_request/result,
   terminal_outcome (U) with visibility `sealed_test_outcome`, and
   `adjudication` for the evaluator's validity verdict. Append-only JSONL under
   `results/paper_b/<run>/ledger/`. `export` reproduces the tree records from
   the ledger.
4. Tests (CPU, scripted model): histories captured on the fixture trees;
   transplanted H₂ rejected; outcome fields absent from every history;
   ledger round-trip equals the tree records; `evaluate_with_configurator`
   on ledger-derived histories equals the direct run.
5. Generate ten development transcripts with the scripted model for D-DAC3.

Done when: the tests pass and `smoke_b.py` writes a ledger.

### WP4 — Live lane on Ada: F10 tooling, B endpoint, contract v3 (W, then X)

Template: Paper A's `experiments/paper_a/panel_v2/` and
`protocols/paper_a/ADA_RUNBOOK_20261005.md` (dry run → smoke → authorise →
live → resume/stop), which were reviewed and dry-run on 5 Oct.

1. `protocols/paper_b/endpoint_b.json`: Devstral-Small-2-24B, the same
   deployment as `replay_panel_v2_endpoint.json`, on a **B-owned port**
   (not 18083), temperature and seeding as the contract says, `paid_api = 0`.
2. `experiments/paper_b/run_screen.py`: modes `dry` (scripted model, CPU),
   `smoke` (≤ 8 leaves on the real model), `live` (frozen 96-leaf screen).
   `live` refuses unless: contract v3 fully bound, authorisation record
   present, design SHA-256 matches, caps declared (leaves, tokens, wall-clock,
   paid API = 0), free card confirmed. Resumable; operator stop by SIGTERM;
   per-root workspace paths; condition names never reach the model (the
   E-R2 blocker finding).
3. `experiments/paper_b/bind_runtime_artifacts.py`: fills contract v3 from the
   running endpoint (model id and revision, weights hash, tokenizer hash,
   server build, decoding params), the harness commit, task-generator and
   evaluator hashes, the split manifest; refuses on any mismatch with the
   endpoint file.
4. `protocols/paper_b/contract_v3.yaml`: v2 plus the configurator block from
   the amendment §5, `offline_budget` / `online_budget` fields (B-TKV1), and
   `ledger_schema: reliability-1.0`. Migration test from v2; validator updated.
5. `protocols/paper_b/ADA_RUNBOOK_B.md`: sync, environment check, dry, smoke,
   authorise, screen, bring results back, failure handling, do-not list.
   Reserve a card and a port that do not collide with A's E-R2.

Done when: `run_screen.py --mode dry` completes end to end on CPU with a
ledger and a report; `--mode live` refuses on an unbound contract (tested);
the Ada smoke (X) returns ≤ 8 leaves with captured histories and a bound
contract.

### WP5 — Encoder lane: bindings, question set, matching (W; X for CLM)

1. Kev: pin a Hugging Face revision of Kev-4B; install the MLX runtime on the
   Mac; `scripts/encode_histories.py` reads serialised texts, calls the local
   Kev server, writes vectors to the cache keyed by (fingerprint, sha256);
   `KevBinding` filled; question-set JSON frozen with a digest (D-DAC3).
   Smoke on the ten WP3 transcripts; record latency and token counts.
2. CLM (ablation; X): vLLM pooling server for Qwen3-8B on one Ada card,
   `CLM-v0.1-8B` head downloaded and hashed; `CLMBinding` filled;
   `backbone_raw` served from the same server. Smoke on the same transcripts.
   Record the truncation rate at 2,048 tokens.
3. B-DAC6: `matching_report` gains encoder fingerprint, serialiser
   fingerprint, projector digest and feature keys; fails on any difference
   between controllers.
4. `evaluate_with_configurator` reads the cache; a test proves that a changed
   question set or head hash invalidates the cache.

Done when: both slots encode the WP3 transcripts offline and the matching
report passes with real vectors; bindings recorded in contract v3.

### WP6 — Post-training lane for the configurator (W + D; extension, D-DAC7)

What "post-train a Jev-like configurator" can mean here, in order of cost:

| Level | What is trained | Data | Tooling | Where |
|---|---|---|---|---|
| L0 (primary design) | projector + ridge heads | development families of the screen/pilot | existing `heads.py` | Mac |
| L1 | Kev rank-16 LoRA on the frozen question set | labelled decision records from **outside** every evaluation family | Kev's JSONL format + its training skill (Modal or local CUDA) | Modal or Titan/Ada |
| L2 | CLM head retraining (20M params) on paired (state, action) contrasts | same external set, as agentic traces | `train/finetune.py` | Ada |

Infrastructure for L1/L2:

1. **External labelled set.** Sources that never touch evaluation families:
   (a) scripted-behaviour trees from attempt 2's *development-only* families
   with the paired leaf contrast as the label (several hundred decisions are
   cheap on CPU); (b) fault-injected runs through the reliability scaffold's
   injectors (malformed tool arguments, stale memory, flaky verifier), labelled
   by the sealed manifest; (c) optionally, verification-decision records
   derived from the ETAAI campaign ledgers (1,355 governed trials) if a
   "verify-worth" label can be defined for a keep/discard trial without
   leaking B's task — a design question, not assumed.
2. **Training views.** Use `autoresearch.reliability.training` view builders
   (outcome-only, process-supervised, abstention) so each example records
   source run ids, split, dedup cluster and builder hash.
3. **Leakage audit.** A test that no task template, family, repository or
   near-duplicate trace crosses into evaluation splits (the reliability
   package already states this rule; implement the check).
4. **Training scripts.** `scripts/posttrain_kev.py` (writes Kev JSONL, calls
   the LoRA trainer, registers the adapter as a new `KevBinding` revision) and
   `scripts/posttrain_clm_head.py` (writes trace adapters, runs
   `finetune.py`, hashes the new head). Each emits a training manifest.
5. **Gate.** A post-trained encoder enters the evaluation only as an extra
   encoder revision under the same matching report, with its own
   authorisation record, after the primary design is frozen (30 Nov).

Done when: one end-to-end L1 run on the scripted external set produces a
pinned adapter that the encoder slot loads, and the leakage audit passes.
No claim is made about its usefulness until the pilot.

### WP7 — Governance panel: adjudication, fault injection, reporting (W)

1. **Adjudication of leaves.** Wrap the U evaluator's validity decisions as
   `AdjudicationRecord`s (accepted / rejected / ambiguous /
   insufficient_evidence / verifier_failure); ambiguous stays ambiguous.
2. **Fault injection for N1.** Map B's replay-discrepancy allowance (design
   v2 §B3; `control/replay_validity.py`) onto the reliability fault manifests
   so a discrepancy injection is sealed, block-randomised, hidden from the
   policy view and reported with a no-fault control.
3. **Reporting.** `scripts/export_b_tables.py` from the ledger: screen and
   pilot summaries, matching report, cost ledger (offline vs online budgets).
   Optional read-only dashboard over the ledger; not required.

Done when: ledger exports reproduce the tree report byte for byte; a sealed
fault manifest round-trips through the N1 grid on the fixture trees.

### WP8 — Qualification, screen, pilot (X + D)

Against P-B2: both lanes qualified by **15 Nov**; screen (96 leaves) → pilot
(384 leaves), route chosen, design frozen, budget authorised by **30 Nov**.

1. Qualify the executor lane: WP4 smoke on Ada, bound contract, qualification
   report written into contract v3.
2. Qualify the encoder lane: WP5 on real screen transcripts.
3. Screen: fit heads on development families only; matching report; N1 grid;
   route decision COMBINE / CORE_ONLY / narrow report.
4. Pilot; freeze; authorise the main budget.

---

## 5. Decisions needed from the author (D)

1. D-DAC1–6 as recommended, or alternatives (WP1).
2. D-DAC7 post-training scope and D-DAC8 governance depth (WP1).
3. Approve committing the uncommitted B work and creating the B repository
   (WP0), including the name `agent-verification-timing`.
4. Which host holds which piece: Kev on the Mac; CLM and Devstral on Ada; the
   Titan server only if a CUDA Kev run is wanted.
5. Confirm the Ada port and card reservation for B so A's E-R2 panel is not
   disturbed.

## 6. Gates that are not infrastructure

These must close before results count, in parallel with WP0–WP5:

- B1 task realism (WP2), with P-B1's one-attempt rule.
- B2: independent re-review of the R2 fix commits; novelty verdict on
  `B_NOVELTY_MEMO.md`; a by-hand read of the BAVAR preprint.
- B-TKV2 shrinkage baseline specified with development-only fitting.

## 7. Timeline (critical path in bold)

| Week | Items |
|---|---|
| 6–12 Oct | **WP0** commit + B repo; **WP1** decisions; **WP2** attempt-2 design sealed; WP3 history capture |
| 13–19 Oct | **WP2** realism run (stop rule applies); WP3 ledger adapter + tests; WP5 Kev offline on the Mac |
| 20–26 Oct | **WP4** F10 tooling, contract v3, dry run; WP7 adjudication + fault mapping; B2 re-review (separate session) |
| 27 Oct–2 Nov | **WP4** Ada smoke (X); WP5 CLM pooling server (X); matching report with real vectors |
| 3–15 Nov | **WP8** qualification of both lanes; WP6 scripted external set + leakage audit |
| 16–30 Nov | **WP8** screen → pilot → route → freeze; WP6 L1 run only after the freeze |

Slack: one week before 15 Nov, none before 30 Nov. If WP2 fails, stop per
P-B1; WP0, WP3 and WP7 remain usable for any later redesign.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Attempt 2 fails realism | P-B1 disposition; no tuning against the result; keep infrastructure task-agnostic (histories, ledger, encoder lane) |
| Ada cards unavailable (shared host) | Kev lane needs no card; CLM is an ablation and can be dropped; reserve one card and a port early |
| Encoder reads condition names or outcomes | serialiser allowlist and redaction already tested; add the same guard to the ledger export; E-R2's finding (condition names via tool-error paths) must be checked in B's task adapter |
| H₂ exceeds CLM's 2,048 tokens | serialiser's deterministic truncation; record truncation rate; Kev primary |
| Post-training leaks evaluation families | leakage audit as a test; external set built only from development families and synthetic faults; D-DAC7 keeps it an extension |
| Two sessions editing the shared records | WP0 commits first; after the B repository exists, B records live there |
| Harness pinned at a KDD snapshot | pin the commit; vendor nothing; adapter tests isolate B from upstream changes |

## 9. Non-goals

- No change to U, the controllers, the allocator, the comparators or N1.
- No general DAC benchmark, no optimality theorem, no "why not RL" method
  contribution beyond the two-step fitted-Q equivalence already stated.
- No live-agent prevalence claim; no real-agent result before the Ada runs.
- No port of the tree onto the harness's claw worker (D-DAC8 (a)).
- No use of Jev itself as a component.

## 10. Validation to record when each WP closes

| WP | Commands |
|---|---|
| WP0 | fresh-clone `tests/control`, `tests/release`, `smoke_b.py`, `launch_validator.py --for-launch`, `make paper-b` |
| WP3 | `tests/control/test_history.py`, `test_governance.py`; `smoke_b.py` ledger |
| WP4 | `run_screen.py --mode dry`; refusal tests; contract v3 migration test |
| WP5 | encoder smoke logs; cache-invalidation test; matching report |
| WP6 | leakage audit; training manifest; adapter load test |
| WP7 | ledger-export equality; fault round-trip |
| WP8 | qualification reports; screen report; freeze SHA-256 |
