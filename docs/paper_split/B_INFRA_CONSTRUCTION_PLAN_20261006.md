> Copied from the source repository at S = 4154f153, 7 October 2026; this draft plan v3.1 was
> uncommitted in the source working tree at S. The source copy is the historical one.

# Paper B infrastructure-construction plan, v3.1 — DAC framing with a post-trainable configurator

6 October 2026. **Status: DRAFT v3.1, prepared by an AI agent (Claude), revised
after an independent AI-assisted review of v3 (21 findings, §9); not adopted.**
Supersedes `B_INFRA_CONSTRUCTION_PLAN_20261005.md` (v1, committed) and the v2
revision that exists only as the project document
`reviews/2026-10-05_paper_b_infra_construction_plan.md`. v3 is re-based on what
is committed: since v2, the executor, the governance ledger, the copied
reliability schema and contract v3 have landed (`9de9c908`, merged in
`f463209d`).

Goal, unchanged: get the infrastructure ready so that the Paper B experiment —
*when should an executor agent spend its one verification*, framed as
budget-constrained dynamic algorithm configuration (DAC) with a learned,
post-trainable configurator — can run on the Ada server inside the P-B2
cutoffs (both runtime lanes qualified by **15 Nov 2026**; screen + pilot done,
route chosen, design frozen, budget authorised by **30 Nov 2026**).

This plan builds infrastructure. It does not change B's estimands, outcome U,
controllers, allocator, primary comparators, budget or gate sequence, and it
does not close the two scientific gates: task realism (OPEN_ITEMS B1) and the
design-ready re-review (B2). Where it needs something the adopted design does
not contain, it lists an author decision (§7) instead of assuming one.

**Basis.** MacBook Pro checkout `~/Documents/GitHub/agent-checkpoint-intervention`,
`main` = `origin/main` = `f463209d`, clean tree. Run for this plan on 6 Oct
(Python 3.13, CPU): `tests/control` **207 passed**; `smoke_b.py` **11/11**
engineering checks. External repositories read at `autoresearch_harness`
`da8dcbd` (4 Aug 2026), `Contrastive-LM/CLM` `d5f9ef0` (5 Oct 2026),
`jaredpalmer/kev` `5e42a7a` (5 Oct 2026). **Not checked:** anything on Ada;
the Hugging Face Hub (tags, revisions); a live Pi session; the other
checkout on the Mac mini.

**Naming.** Packages are `IP0`–`IP11` ("infrastructure package") so they do not
collide with the WP numbers of v1/v2. "Lane" always means the validator's
runtime lanes `one_step` and `sequential` (P-B2, OPEN_ITEMS B5). The executor
and encoder workstreams are called *tracks*.

---

## 0. Answers

### 0.1 Paper A / Paper B split — where it stands

| | State |
|---|---|
| Paper A (TMLR, Tier 1) | Per the 5 Oct records: reviewer items A-R1–A-R6 implemented, two AI-assisted review rounds patched, Ada packs for E-R3 (CPU) and E-R2 (one card) frozen and dry-run. Open: the two Ada runs, post-run text, final-commit release and supplement, author items (ETAAI public declaration, author list, final read). |
| Paper B (ICML 2027 target) | Analysis side complete on CPU; executor, ledger and contract v3 committed, **scripted backend only**. Blocked scientifically by B1 (attempt 1 failed realism; one attempt left under P-B1) and B2 (re-review, novelty verdict, BAVAR read). No model call has been made. |
| Repository split | **Phase 0 done**: B's work is committed and pushed (`f463209d`). **Phases 1–2 not done**: no `agent-verification-timing` repository on this machine. Phase 3 (removing B here) waits for A's submission. |
| Shared records | `STATUS.md`, `OPEN_ITEMS.md` have no entry for the 5–6 Oct B work; OPEN_ITEMS B6 still lists B-DAC4/5 as open. |

### 0.2 Can Paper B stand alone with the whole ecosystem it needs?

**Yes for everything that runs on CPU today. The live lane is copyable but
unproven, and four pieces of it do not exist yet.**

- Measured import closure (AST walk from `control/`, `experiments/paper_b/`,
  `tests/control/`, `launch_validator.py`): outside `control/`, B needs only
  `causal_branch/{__init__,types,branching,checkpoint,pi_fork}.py` and
  `adapters/{__init__,toy}.py`. `pi_fork` is new since the split checklist.
  No import of Paper A's measurement core.
- The live lane additionally needs, all present in this repository and
  copied rather than moved: the Pi stack (`adapters/pi_agent.py`, `pi_rpc`,
  `pi_models`, `model_client`, `tool_socket`, `registered_tools`,
  `history_retention`, `budget`, `runtime_identity`, `substrate_identity`,
  `d7_adjudicator`), `third_party/pi/` (21 MB), `experiment_scaffold/pi_extensions/`,
  the pinned Node runtime that `pi_agent.require_pinned_node` expects, and
  Paper A's server-start and card-availability scripts.
- **Does not exist yet** and must be written for B: a Pi extension registering
  B's three tools, B's system-prompt file, `endpoint_b.json`, and the
  Pi-backed executor path itself (IP2).
- Not part of B's ecosystem: the `autoresearch` package (schema already
  copied), Jev, the Titan server.
- To record in the new repository's `PROVENANCE.md`: licences of
  `third_party/pi`, the copied harness schema (MIT), Kev and CLM (Apache-2.0),
  and of any Kev replay data if `--replay` is used.

### 0.3 Do we have the framework / harness / governance panel?

| Layer | Have | Missing |
|---|---|---|
| Analysis (DAC evaluation) | paired tree records, two-phase hard-budget allocator, proposed rule + matched comparators, family-cluster bootstrap, N1 grid, configurator scaffold (serialiser, encoder slots, projector, shared heads) | B-TKV2 shrinkage baseline; configurator provenance in `matching_report`; descriptive reference policies (D-REF1) |
| Executor | `control/executor.py`: three-regime tree through an agent backend, chained fork at both checkpoints, one-verification guard, index-named branches, H₁/H₂ from session entries; `ScriptedCandidateAgent`; 11 tests | **the live path**: `PiBackend.run_turn` always raises, and the executor's session model (Python-written sessions inside the workspace, a scripted `checkpoint` entry, scripted entry types) does not match the Pi adapter (IP2) |
| Governance | `control/governance.py`: append-only ledger, deterministic ids, timing sidecar, row SHA-256, `validate_stream`, `export_tree`; harness schema copied verbatim at `da8dcbd`; 8 tests | adjudication of leaves, fault manifests for N1, table export |
| Contract | `contract_v3.yaml` (draft); validator accepts `b_v3` | all bindings `null`; one encoder block only; no field for a post-trained encoder; no pilot phase in the validator |
| Live tooling | Paper A's `panel_v2` pack as a template | `run_screen.py`, `bind_runtime_artifacts.py`, `ADA_RUNBOOK_B.md`, `reproduce-b` |
| Task | attempt 1 (failed realism), kept | attempt-2 design; generator with distinct families and a `posttrain` partition |

**On "governance panel".** `autoresearch_harness` is a control plane and a
record vocabulary, not a UI. Its `reliability` sub-package holds the event
schema, adjudication vocabulary, a policy registry (including an oracle and a
budget-matched random policy), training-view builders and a fault-injector
protocol. It hard-requires LangChain/LangGraph/pandas, has no dashboard, and
its executor is the LangGraph/claw-worker loop over ML-experiment edits. B
uses it as **schema + discipline** (already copied) and keeps its own Pi fork
executor. A visual panel, if wanted, is a read-only report over B's ledger
(IP9). Because the harness already names verify/continue policies and a
myopic-VOI policy, it belongs in the B2 novelty/overlap verdict.

### 0.4 Do we have a Jev-like configurator?

**A slot and two candidate bases. No bound model, no training data, no trained
configurator — and the bounded screen + pilot cannot produce enough data to
post-train one.** Jev is hosted and cannot be post-trained or reproduced
offline; it stays a reference point.

| | Kev (`jaredpalmer/kev`, Apache-2.0) | CLM (`Contrastive-LM/CLM`, Apache-2.0) |
|---|---|---|
| What it is | decision model: rank-16 LoRA + pointer head on Qwen3.5 (0.8B/4B/9B); full-weight Qwen3.8-27B | two contrastive encoders: frozen Qwen3-8B + 20M-parameter state/action heads |
| API | TypeSafe-compatible `POST /v1/systemone` (noul / choice / score) | also `POST /v1/systemone`; plus `/v1/rank` and raw embeddings |
| Probabilities | calibrated by a temperature stored in the checkpoint (2.41 for 4B) | softmax of scaled cosine; request-level temperature, default 1; **not calibrated** |
| Trained on (4B) | 12.6k base records (public classification + generated policy/rule data), then 5.2k real documents up to ~7k tokens, 6k skill records, 5.3k developer-tooling records; states up to 7,552 tokens | 60M Q&A pairs, 30M hard negatives, ~1M agent trajectories |
| Runs on | CUDA (L40S/H100 class); MLX on Apple Silicon (4B measured on a 32 GB Mac; 9B expected, not measured) | vLLM pooling server on an NVIDIA GPU + `clm-serve` |
| Over-length input | refuses (422) | truncates silently at 2,048 tokens by default |
| Post-training | `kev.train --data … --init_from …` (LoRA + head); temperature fitted **separately** by `scripts/calibrate_checkpoint.py` | `train/finetune.py --task choice` (Parquet typed decisions) — heads only |
| Pinning | Kev 1.0: Hub tag `v1.0` (a tag can move — pin the commit), 4B weights `139fdd94`, checksummed release | no release tag or lockfile; head fetched from `resolve/main`; `vllm>=0.6` unpinned — **we must pin all three** |

Design consequences:

1. **Both servers accept the same request shape**, so one client can drive
   both. They are **not** interchangeable: CLM embeds each option text alone
   (so nouls must be statements and score levels full sentences), rejects
   unknown model names, is uncalibrated, and truncates. A question set must be
   written for both and checked on both before it is frozen (IP6).
2. **CLM's `--task clm` (state→action InfoNCE) is not usable for the
   verification decision**: with two action texts almost every in-batch
   negative equals the positive. Only `--task choice` is in scope.
3. **CLM's `docs/FINETUNING.md` is an agent-loop prompt**, not a
   specification; the data contract is `train/adapters.py` and the script's
   arguments. Nothing in that document is executed as instructions.
4. **Data.** Screen + pilot give 80 roots, at most 160 decision points, all in
   evaluation families. Kev's own guidance is that ~400 records gave a gain
   inside the noise and ~1,000 a measurable one. A post-training collection of
   ~1,000 decision points is ~500 roots ≈ 3,000 leaves ≈ 4M generated tokens
   at the planning figures (≈1,350 tokens and ≈12 s per leaf) — six times the
   screen + pilot leaf cap. **A post-trained configurator is therefore a
   separately authorised collection after the 30 Nov freeze, not something the
   current budget can deliver.** Until then the plan delivers the pipeline and
   its proof on scripted data.

In the repository today: `KevBinding`/`KevEncoder` (posts to `/v1/systemone`
with a draft five-question set, tested through a fake), `CLMBinding`/`CLMEncoder`
(embeddings + head; only its refusal is tested), `MockEncoder`, `EmbeddingCache`.

---

## 1. What the DAC framing requires of the infrastructure

| DAC element | Paper B object | Infrastructure | Status |
|---|---|---|---|
| Instance distribution | template families | generator with distinct families; split manifest (development / test / posttrain) | attempt 2 open |
| Target algorithm | executor agent (Devstral-Small-2-24B via Pi) | bound endpoint, Pi-backed executor | missing |
| State | H₁, H₂ ⊇ H₁ | capture at both checkpoints, lineage checks, serialiser | scripted path only |
| Configuration space | {continue, verify} × 2, ≤ 1 verify | guard + allocator | done |
| Reward | U (hidden-test accuracy) | evaluator; sealed outcomes in the ledger | code done; attempt-1 task only |
| Cross-instance constraint | B = floor(0.25·N) | shared allocator at analysis time | done |
| Offline data | paired leaves per root, ≥ 2 stochastic repetitions | tree executor + ledger + **stochastic decoding** | scripted only; decoding undecided |
| Configurator | encoder → projector → heads → allocator | bound encoder, frozen question set, cache | slot only |
| Configurator training | L0 heads; L1/L2 encoder post-training | label map, posttrain partition, leakage audit, trainers, contract fields | missing |
| Generalisation test | held-out families, cluster bootstrap | `evaluate_tree`, `matching_report` | done; provenance missing |

Three levels of "training the configurator":

- **L0 (primary design):** frozen encoder; fit projector + ridge heads on
  development families.
- **L1:** post-train Kev (LoRA + pointer head, then refit the temperature) on
  the frozen question set.
- **L2:** retrain CLM heads on the same labels (`--task choice`).

L1/L2 are "post-train a Jev-like configurator". They use a third partition
(`posttrain`) disjoint from development and test families.

---

## 2. Definition of "infrastructure ready"

Each item closes with a recorded command in `VALIDATION.md`.

| ID | Ready when | Today |
|---|---|---|
| R-0 Executor | one root runs all three regimes through the scripted backend on CPU **and** through Pi + Devstral on Ada, with the same lineage invariants | CPU half done |
| R-1 Records | every branch and checkpoint yields a lineage-checked history and a deterministic ledger row, for both backends | scripted only |
| R-2 Live tooling | `run_screen.py --mode live` runs the frozen screen (96 leaves + 32 integrity controls); refuses without a qualified contract, authorisation, matching design hash and a free card; caps declared before dispatch | missing |
| R-3 Encoder track | primary encoder and ablation encode saved histories offline from pinned artefacts into the on-disk cache, one backend and dtype per encoder | missing |
| R-4 Contract | `launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase qualification --lane one_step --for-launch` and the same with `--lane sequential` both pass on the frozen, bound contract; `--phase pilot` refuses until IP10 implements it | draft, all null |
| R-5 Governance | ledger export reproduces tree records and the configurator report; `matching_report` fails on any feature-map difference | export done; provenance missing |
| R-6 Post-training track | posttrain partition, sealed label map, leakage audit, one reproducible L2 run and one L1 run on scripted data, each producing a pinned artefact the encoder slot loads and the contract can name | missing |
| R-7 Reproduction | `make reproduce-b` rebuilds the screen report from ledger + cache + contract with no model call, hashes equal | missing (IP9) |
| R-8 Standalone | all of the above pass in a fresh clone of the B repository | repository missing |

R-6 proves a pipeline. Whether a post-trained configurator *helps* is the
subject of IP11, which needs data that only a separately authorised
collection can supply (§0.4).

---

## 3. Packages

Owners: **W** any agent, **D** author, **X** Ada access. Status against
`f463209d`.

**Critical path to the 15 Nov gate:** IP0 → IP1 (decisions + task) → IP2
(Pi-backed executor) → IP5 (live tooling, endpoint, decoding, binder) →
IP6 steps 1–3 (primary encoder bound: the validator requires it) → IP7 step 1
(posttrain partition in the split manifest: the validator requires it) → IP10
(qualification of both lanes). B2 (author) runs in parallel and is also on
the path.

### IP0 — Records and repository (W, then D)

1. Add the 5–6 Oct entries to `STATUS.md` and `VALIDATION.md` (207 tests,
   smoke 11/11) and update OPEN_ITEMS B6.
2. Fix the dangling reference: `executor.py:3` and `cc_live_agent.py:3` cite
   `docs/paper_split/B_INFRA_RUNBOOK_20261005.md`, which is not in the
   repository. Commit it from the machine that holds it, or re-point both.
3. Create `agent-verification-timing` from snapshot `S = f463209d` following
   `AB_REPO_SPLIT_CHECKLIST_20261005.md` Phases 1–2, adding
   `causal_branch/pi_fork.py` to the "code B imports" list and the items of
   §0.2 to the live-lane list.
4. B-only Makefile, `PROVENANCE.md` (with licences), B copies of the shared
   records, an import-allowlist test replacing `check_split.py`.

Done when, in a fresh clone of the new repository: `tests/control` passes
(207), `smoke_b.py` 11/11, `make paper-b` builds, and
`launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase
qualification --lane <each lane> --for-launch` refuses for the expected
reasons (draft status, null bindings).

### IP1 — Decisions and the task (D + W)

**IP1a decisions** — §7. All before any pilot outcome exists.

**IP1b task attempt 2** (P-B1: one attempt). `ATTEMPT2_DESIGN.md`, sealed
with SHA-256 before running, must contain — in addition to where verification
has diagnostic value and where waiting trades information against delay —
the things later packages depend on:

- **family count and a distinctness rule.** Attempt 1 alternates two sklearn
  tables, so "families" share almost all rows and feature names; no leakage
  audit can pass on that. State how families differ and the near-duplicate
  metric and threshold the audit will use.
- **three partitions** (development / test / posttrain) with disjoint family
  ids, and the number of families in each.
- **ground-truth fields** the generator records per root for state labels
  (e.g. whether a shift occurred, whether the candidate is stale), or the
  statement that no such labels will be used.
- **the realism harness.** If the realism run moves from the attempt-1 runner
  (behaviours careless / typical / careful) to the executor's scripted agent
  (typical / greedy / careless), declare the change and the behaviour set
  here; otherwise keep the attempt-1 runner.

Then run realism once. If R1–R9 fail, P-B1 applies and this plan stops; IP0,
the ledger, the encoder track and the exporters remain usable for a redesign.

### IP2 — Pi-backed executor (W on CPU, X on Ada)

The scripted half is done (`9de9c908`). The live half is a redesign of the
backend seam, not a one-method fill-in: the executor writes child sessions in
Python inside the parent's `.session/` directory, while `PiAgentAdapter`
refuses a fork source inside the child session directory and a fork target
that already holds a session (`pi_agent.py:782-791`), has no stop argument
(turns end on settle, timeout or budget), builds its tool executor from one
`ToolBridge` and a required `regime_id`, and writes the launch directory into
the system prompt.

1. **Interface note (first, half a day).** Read `pi_rpc`, `registered_tools`,
   `tool_socket`, `pi_extensions/` and how `experiments/paper_a/panel_v2`
   drives a single fork; record the real Pi session entry format from an
   existing session. Output: a one-page note fixing the choices below.
2. **Move session handling behind the backend.** The backend, not the
   executor, owns: where sessions live, how a child is forked, what the
   checkpoint id is, and how entries are read. Scripted backend: today's
   behaviour. Pi backend: Pi's native fork into a fresh per-branch session
   directory (`run_turn(fork_session=…, fork_child_session_id=…)`), checked
   with `pi_fork.verify_fork`; the checkpoint is the settled leaf entry id.
   The session directory moves out of the workspace for the Pi backend, so
   the checkpoint record binds the workspace tree hash **and** the session
   prefix digest explicitly.
3. **History translator.** `history_from_session` accepts only the scripted
   entry shapes. Add a translator from real Pi entries to `HistoryEvent`s,
   with a recorded real session as a test fixture.
4. **Tools.** A B Pi extension registering `fit_candidate`,
   `verify_candidate`, `submit_candidate`; a `ToolBridge`-shaped wrapper that
   routes into `ToolHandlers`, so the one-verification guard is the same code
   on both backends.
5. **Arm blindness.** Pass an arm-blind `launch_cwd`; branch directory names
   that map one-to-one to regimes must not reach the system prompt. Fold the
   checkpoint-2 arrival notice into the turn's prompt instead of appending a
   hand-written user entry.
6. **Seed and decoding plumbing** per D-DEC1 (IP5 step 1).
7. **Checks before any Ada time.** (a) CPU, no Node: unit tests of the
   translator and the bridge wrapper. (b) CPU with the pinned Node, no model:
   `PiAgentAdapter.rpc_handshake` and a fork/verify round on a recorded
   session. A replay-only fake Pi is **not** sufficient evidence for fork or
   session semantics.
8. **Ada:** one root, three regimes, Devstral; the lineage invariants of the
   CPU tests hold; the ledger validates and its export equals the tree records.

New scripted-backend entry points go in **new files**: `smoke_b.py` is pinned
by SHA-256 as the engineering fixture in both contracts and must not be edited
without re-pinning.

### IP3 — Analysis completions (W; D for D-REF1)

1. **B-TKV2**: context-conditioned shrinkage baseline, development-only
   fitting, under the same matching report.
2. **Reference policies (if D-REF1 is adopted, descriptive only):** per-root
   oracle upper bound and a budget-matched random policy, reported beside the
   comparators and never used for selection.
3. `matching_report` provenance (encoder fingerprint, serialiser fingerprint,
   projector digest, feature keys); fails on any difference (B-DAC6).

### IP4 — Governance ledger (mostly done)

Done (`9de9c908`): verbatim schema copy with provenance, deterministic
adapter, round-trip and tamper tests. Remaining (W): write the ledger from
`run_screen.py`; record the schema's upstream commit in contract v3; lineage
checks on Pi-format sessions (IP2 step 3).

### IP5 — Live tooling on Ada (W, then X)

Gate: OPEN_ITEMS B2 says the F10 tooling is built "only after B1 passes".
Building the model-free parts earlier needs the waiver D-F10; without it this
package starts after the realism run.

1. **Decoding (D-DEC1).** The E0 Devstral binding has temperature 0.0, and
   the design requires ≥ 2 stochastic repetitions per leaf. Decide B's
   temperature and the per-repetition seed rule, and how the seed reaches
   llama-server (the adapter has no seed parameter today). Only the GGUF and
   the server build are reused from E0.
2. `protocols/paper_b/endpoint_b.json`. Ports: the E0 file assigns
   18081/18082 to its two workers and A's runbook describes them as "Paper B
   and a foreign tenant" — **confirm ownership on the host before binding**;
   A's E-R2 holds 18083.
3. `experiments/paper_b/run_screen.py`: modes `dry` (scripted, CPU), `smoke`,
   `live`; `--integrity-controls 32`; `--enforce-budget-caps` (512 terminal
   leaves, 2M generated tokens, 10 h, 20 accelerator-hours, 10 GiB, zero new
   spend); resumable; deferred stop on SIGTERM; writes the ledger.
4. **Cap accounting (D-CAP1).** The 512 leaves are fully allocated (96 screen
   + 384 pilot + 32 controls). State whether the Ada single-root run (IP2
   step 8), the smoke and the qualification runs draw on a separately declared
   engineering allowance or on the 512; the tool enforces whichever is adopted.
5. `protocols/paper_b/bind_runtime_artifacts.py` (fills contract v3 from the
   running endpoint and the repository; refuses on mismatch).
6. B-TKV1: `budgets.offline_collection` / `budgets.online_verification`.
7. `protocols/paper_b/ADA_RUNBOOK_B.md`.

Done when: `--mode dry` completes on CPU with ledger and report; `--mode live`
refuses on the unbound contract (tested); the Ada smoke returns its leaves
with histories.

### IP6 — Encoder track (W; X for CLM)

1. **Measure before choosing (input to D-DAC2).** Run Kev-4B on Kev's own
   `evals/agents-ood-v1` (373 agent-log records) and on ten scripted B
   transcripts; record accuracy/Brier, latency and token counts on the Mac.
2. **Question set written for both models, then frozen (D-DAC3).** Statement
   form for nouls; full-sentence level descriptions for scores; checked on a
   Kev server and a CLM server before the SHA-256 is taken. One serialiser
   `max_chars` for both.
3. **Bind Kev (primary).** `kev.serve --run jaredpalmer/kev-4b@<commit>`;
   record the resolved weights revision and checkpoint hash (the server's
   `/v1/models` reports the requested run, not the resolved revision); fix the
   serving backend **and dtype** in the fingerprint (bf16 and fp32 paths
   differ in the probabilities). The request's `model` field is a label for
   Kev; pinning is by revision and hash.
4. **Client.** One typed-question client for both servers, with per-server
   settings: CLM model name (`clm-latest` or a named head — unknown names are
   rejected), CLM request temperature, and **client-side token counting** so
   truncation at 2,048 tokens is measured rather than assumed. Keep
   `CLMEncoder` (embeddings + head) as the embedding variant and add a first
   real test of its request path.
5. **Bind CLM on Ada (ablation; one card).** Pin the Qwen3-8B revision, the
   head file hash and the vLLM version; set the pooling server's memory
   fraction high enough for 8B weights (the script default is 0.35 of the
   card).
6. **Contract and validator.** Add a `clm_systemone` slot and an
   `ablation_encoders` block (the validator allows `kev`, `clm_state_head`,
   `backbone_raw` and one encoder block today); fingerprint fields: backbone
   revision, head hash, `max_tokens`, backend, dtype, question-set hash.
7. `scripts/encode_histories.py` (ledger histories → serialiser → encoder →
   on-disk `EmbeddingCache`) and the `EmbeddingCache.load` round-trip test.

Done when: both models encode the same transcripts offline from pinned
artefacts, the matching report passes with real vectors, and the contract
names every encoder used.

### IP7 — Post-training track (W + D; extension under D-PT1)

1. **Partition** (critical path for qualification): `posttrain` families in
   the split manifest, from the attempt-2 generator.
2. **Label map, sealed with SHA-256 before any run.** For every question:
   - the formula. For the outcome-derived question "verifying at this
     checkpoint is worth it", the map names the comparator (never; later; or
     the better of both), the threshold (gain target 0.02 U unless stated
     otherwise), and the estimate used (mean over the leaf's repetitions);
   - the rule for roots that do not reach checkpoint 2;
   - the discretisation thresholds for score questions;
   - the source for state labels (generator ground truth, IP1b), or their
     removal from the set;
   - a missing-label rule: Kev requires a label on every question of every
     record, CLM skips unlabelled questions — so a record with any undefined
     label is dropped for both, to keep the two training sets identical.
3. **Exporters from the ledger.**
   - `export_kev_jsonl.py`: one request per decision point in Kev's shape
     (`state`, `questions` with a `label` inside each question); held-out
     split **by family**.
   - `export_clm_choice.py`: Parquet under `<dir>/<workflow>/train*.parquet`
     and `test*.parquet`; rows `id`, `state`, `questions`, `gold` =
     `{qid: {"label", "probabilities"}}`; **`id` = family id**, because the
     trainer splits validation by `id`.
   - No state→action exporter (§0.4, consequence 2).
4. **Leakage audit**: no family, template or near-duplicate serialised text
   (metric and threshold from IP1b) crosses the three partitions; labels never
   appear in `state`.
5. **Trainers**, each writing a manifest (data hash, base revision, seed,
   command, output hash):
   - **L2** `scripts/posttrain_clm_head.py`: `finetune.py --task choice
     --data <dir> --init-ckpt <pinned head> --embed-url <server>
     --served-model-name <name>` (without the last two the script starts its
     own vLLM and collides with the pooling server); `--loss softce`
     (softmax over each question's own options) suits a fixed question set
     better than the default InfoNCE. A head trained on "state + question" texts is valid for the
     typed-question slot only, not for the embedding variant.
   - **L1** `scripts/posttrain_kev.py`: `kev.train --data <jsonl> --base
     Qwen/Qwen3.5-4B-Base --init_from <pinned Kev> --max_state <≥ longest
     history> --batch 1 --accum 8 --dtype bf16 --checkpointing 1 --device
     cuda` (the default `--max_state` is 384 tokens and longer records are
     dropped), **then** `scripts/calibrate_checkpoint.py` on held-out
     posttrain families — a new checkpoint otherwise serves temperature 1.0
     against 2.41 for the frozen model, which changes the feature scale.
     Anti-forgetting is optional and has prerequisites: `--anchor` needs
     `--anchor_w` and a targets file built by `kev.anchors`; `--replay` needs
     `--suite` and its Hub data. One 48 GB card: the model card reports
     24.6 GB peak for short states and 47.7 GB at 7,552-token states with
     batch 2, so batch 1 and a capped `--max_state` are required.
6. **Contract and validator fields for a post-trained encoder.** Today the
   validator requires `encoder_weights_updated: false` and `fitted_on:
   development_families_only`. Add an explicit block (trained on posttrain
   families only; training-manifest hash; leakage-audit hash) and the
   validator rule that accepts it.
7. **Sizing and authorisation.** From the smoke and screen costs, compute the
   records, families, tokens and accelerator-hours for a target of ≥ 1,000
   labelled decision points; present it as a separate budget item (D-PT3).

D-PT2 (order): build L2 first because it is head-only and cheap, with its
limits stated — it needs the Ada vLLM stack, it post-trains the *ablation*
encoder rather than the recommended primary, and a few hundred scripted
decisions will overfit a 20M-parameter head. L1 follows.

Done when (pipeline proof only): on the scripted posttrain set, one L2 run
and one L1 run each yield a pinned artefact that the encoder slot loads and
the contract can name, and the leakage audit passes.

### IP8 — Governance completion (W)

Adjudication records with deterministic ids; B-written fault injectors for
N1 implementing the harness protocol, sealed and block-randomised with a
no-fault control; `scripts/export_b_tables.py`; optional static ledger report
(D-GOV2).

### IP9 — Reproduction (W)

`make reproduce-b`: inputs = ledger, `EmbeddingCache` file, frozen design
hash, contract v3, `requirements.lock`; rebuilds the report with no model or
encoder call; compares hashes. Tested first on a scripted dry run.

### IP10 — Qualification, screen, pilot (X + D)

1. Qualification checks of the launch specification §2 for **both lanes**
   (`one_step`, `sequential`), on the engineering pool, through the Pi
   backend; frozen and bound contract; R-4 commands pass.
2. Encoder track qualified on the **smoke and scripted transcripts** (screen
   transcripts do not exist before the gate).
3. **15 Nov go/no-go**: both lanes qualified **and** B1 **and** B2 closed;
   otherwise retarget beyond ICML 2027 (P-B2).
4. Screen (96 leaves + 32 controls) → route → **implement the validator's
   pilot phase** (it refuses today) → pilot (384) → freeze → authorise.

### IP11 — Evaluating a post-trained configurator (after the freeze; D-PT3)

1. Collect posttrain-family trees under the separately authorised budget.
2. L1 and L2 runs on that data; temperature refit; manifests.
3. Compare, on **test families** and under one matching report: frozen
   encoder vs post-trained encoder, with the telemetry-only and raw-backbone
   controls. State in advance what difference counts and that the result may
   be null. Scripted-to-Devstral shift is avoided by training on Devstral
   trees; if only scripted data is available, the comparison is not run.

---

## 4. Order and dates

| Week | Work | Ada |
|---|---|---|
| 6–12 Oct | **IP0**; **IP1a** decisions; **IP1b** design sealed; **IP2** steps 1–5; IP6 step 1 | A: E-R3 (CPU) |
| 13–19 Oct | **IP1b** realism run (stop rule); **IP2** steps 6–7; **IP6** steps 2–3; IP3 | A: E-R2 smoke + panel (runs first) |
| 20–26 Oct | **IP5** steps 1–7 (earlier parts only under D-F10); **IP7** steps 1–4; IP6 step 4, 7; B2 re-review session | — |
| 27 Oct–2 Nov | **IP2** step 8 + **IP5** Ada smoke; IP8; IP9; D: novelty verdict, BAVAR read | B: one card |
| 3–9 Nov | **IP10** steps 1–2; IP6 step 5–6 (CLM); IP7 step 5 L2 on scripted data | B qualification; CLM server, one card |
| 10–15 Nov | **IP10** step 3 — **go/no-go 15 Nov** | — |
| 16–30 Nov | IP10 step 4; IP7 step 5 L1, steps 6–7 | screen, pilot |
| after freeze | IP11 (if D-PT3 authorises it) | separate budget |

There is no slack before 15 Nov. IP2 is the largest engineering item and the
least certain; the date is otherwise decided by IP1b's single attempt and the
author's B2 items.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Attempt 2 fails realism | P-B1; the infrastructure is task-agnostic |
| Pi chained fork at checkpoint 2 has never run; session model mismatch | IP2 step 1 note; Node-on-CPU fork check before Ada; small smoke before any screen |
| Temperature-0 decoding makes repetitions uninformative | D-DEC1 before `endpoint_b.json` is written |
| Leaf cap already fully allocated | D-CAP1 before any Ada run |
| Ada cards unavailable (shared host) | Kev needs no card; CLM is an ablation; A's E-R2 first |
| Question set favours one model | written for both, checked on both before freezing |
| Kev feature scale changes after post-training | temperature refit is part of L1; dtype fixed in the fingerprint |
| Post-training leaks evaluation families | third partition; family-level splits in both exporters; audit |
| Too little data to post-train | sized and authorised separately (IP7 step 7, D-PT3); no usefulness claim from scripted data |
| Records drift between machines | IP0 steps 1–2; push before switching machines |
| Upstream moves (CLM and Kev both changed on 5 Oct) | pin commits and hashes; never serve an unpinned artefact |

## 6. Non-goals

No change to U, controllers, allocator, primary comparators or N1. No DAC
benchmark, optimality claim or RL method claim. No `autoresearch` package
dependency and no port onto its executor. No Jev as a component. No Titan
server. No real-agent claim before the Ada runs. No claim that a post-trained
configurator helps before IP11.

## 7. Decisions needed from the author

Identifiers D-DAC1–6 keep the meaning of the 4 Oct amendment; D-PT1 and
D-GOV1 keep the meaning of plan v2 (v1 called them D-DAC7/D-DAC8).

| ID | Decision | Recommendation |
|---|---|---|
| D-DAC1 | DAC as framing vocabulary, two declared deviations | adopt |
| D-DAC2 | primary encoder | **Kev-4B primary, CLM ablation**, confirmed only after IP6 step 1. For: runs offline on the Mac, calibrated, inspectable. Against: CLM is the model trained on agent trajectories; Kev-4B's long-state training is documents and developer tooling, not agent logs. |
| D-DAC3 | one question set and one `max_chars` for both models | freeze after IP6 step 2 |
| D-DAC4 | primary feature set | `telemetry+embedding`; each alone as ablations |
| D-DAC5 | projection | `standardize` for typed-question features; PCA k = 8 for raw embeddings |
| D-DAC6 | Kev size | 4B; 9B only if measured latency on the Mac is acceptable |
| D-PT1 | post-training scope | extension after the freeze; not in the primary analysis |
| D-PT2 | which level to build first | L2, then L1 (limits in IP7) |
| D-PT3 (new) | authorise a posttrain collection (~3,000 leaves, ~4M tokens at planning figures) and IP11 | decide after the screen gives real costs |
| D-GOV1 | governance depth | copied schema + ledger + adjudication; no harness executor |
| D-GOV2 | visual panel | default no; static report if wanted |
| D-DEC1 (new) | B's decoding temperature and per-repetition seed rule | required; temperature > 0 with recorded seeds |
| D-CAP1 (new) | do smoke / single-root / qualification leaves count toward the 512? | declare a small separate engineering allowance |
| D-F10 (new) | may model-free tooling (`run_screen --mode dry`, binder) be built before B1 passes? | yes for model-free parts only; otherwise IP5 slips a week |
| D-REF1 (new) | add descriptive oracle and budget-matched random references | adopt as descriptive only |
| — | approve creating `agent-verification-timing` from `f463209d`; Ada reservations and port ownership; whether any Modal spend is ever authorised (default no) | |

## 8. What was verified, and what was not

Verified by running or reading on 6 Oct: test and smoke results; the import
closure; the stub and the adapter's fork refusals (`pi_agent.py:780-791`);
validator lanes, phases, slot allowlist and v3 rules; E0 temperature 0.0;
the executor's two-repetition requirement; the `smoke_b.py` fixture pin; Kev's
default `--max_state` 384, separate calibration script and 4B training
stages; CLM's Parquet loader and noul text construction; licences; harness
dependencies and reliability contents.

Not verified: the real Pi session entry format and `default_executor`
signature (the vendored Pi and three Pi modules were not read for this plan —
IP2 step 1 exists for that reason); Hub tags and revisions; Ada state, lease
and port ownership; the Mac's memory; Paper A's status beyond its 5 Oct
records; per-leaf token and time figures, which are planning values.

## 9. Review disposition (v3 → v3.1)

Independent AI-assisted review of v3, 6 Oct 2026 (not a human review). The
load-bearing findings were re-checked against the sources before applying.

| # | Finding | Disposition |
|---|---|---|
| 1 | Delegating `PiBackend` to the adapter does not work as described (fork refusals, no stop argument, entry shapes, tool bridge, launch directory, arrival message; replay fake insufficient) | IP2 rewritten as a backend-seam redesign with an interface note first and a Node-on-CPU check |
| 2 | "Both lanes" redefined; no screen phase in the validator | lanes = `one_step`/`sequential`; R-4 as concrete commands; pilot phase implemented in IP10 |
| 3 | E0 binding has temperature 0 vs stochastic repetitions | D-DEC1; IP5 step 1; IP2 step 6 |
| 4 | Kev: no temperature fit in `kev.train`; `--max_state` 384; anchor/replay prerequisites; `--base` | §0.4; IP7 step 5 (L1 command and calibration step) |
| 5 | CLM exporters: Parquet, `gold` shape, split by `id`, embed flags; `--task clm` degenerate | IP7 steps 3, 5; transitions exporter dropped |
| 6 | One typed-question slot is wire-compatible but not equivalent | §0.4 consequence 1; IP6 steps 2–6 |
| 7 | Contract cannot register a post-trained encoder | IP7 step 6 |
| 8 | 512-leaf cap fully allocated; 32 controls omitted | D-CAP1; R-2; IP5 steps 3–4 |
| 9 | No data plan or evaluation for post-training | §0.4 consequence 4; IP7 step 7; IP11; D-PT3 |
| 10 | Critical path and ordering (validator prerequisites; encoder qualified on screen transcripts; F10 gated on B1) | critical path restated; IP10 step 2; D-F10 |
| 11 | Leakage audit cannot pass with the attempt-1 generator | IP1b design contents |
| 12 | Label definitions underspecified | IP7 step 2 |
| 13 | Kev-4B training data misdescribed; `agents-ood-v1` available | §0.4 table; D-DAC2; IP6 step 1 |
| 14 | Missing: B-TKV2, reference policies, `reproduce-b`, standalone closure items, pinning, licences | IP3; IP9; §0.2; §0.4 pinning row; IP6 steps 3, 5 |
| 15 | Editing `smoke_b.py` breaks the fixture pin | IP2 closing note |
| 16 | IP0 validator check was vacuous | IP0 done-when names contract and lanes |
| 17 | Port ownership unsupported | IP5 step 2 |
| 18 | "send `kev-latest`" vs "never serve latest"; CLM path untested | IP6 steps 3–4; §0.4 last paragraph |
| 19 | "L2 first" caveats | IP7, D-PT2 |
| 20 | Hardware specifics | IP6 step 5; IP7 step 5 |
| 21 | Numbering and id collisions; "done" overstated in §1; realism harness change | IP naming; §1 statuses; §7 id note; IP1b |
