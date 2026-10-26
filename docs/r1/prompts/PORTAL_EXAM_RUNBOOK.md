# Proposer exam (RUNBOOK Track X) — agent runbook for zhixu portal

**Written 26 Oct 2026 by the coordinating session (Claude) at the author's request; AI-assisted.** One implementation agent that can SSH into zhixu portal executes this runbook step by step. It fills the host facts, closes the code gaps, downloads and pins the models, and runs the exam. Every phase ends with a STOP that runs the **independent review loop** of §0 (author, 26 Oct): an independent reviewer agent reviews, this agent fixes, the independent agent accepts; then the agent reports and the author decides where marked. Do not skip a STOP.

Authority: `docs/r1/PLAN.md` §10 (R1-EXAM-POOL, R1-EXAM-FIT, R1-EXAM-CTX, R1-SCHEMA, R1-QUANT-SOURCE, R1-EXAM-PROTOCOL, R1-EXAM-REVIEW, R1-SKIP-DISPLAY) and `docs/r1/RUNBOOK.md` Track X. If this file and those disagree, they win; stop and report.

## 0. Ground rules for this agent

- **Hosts.** Code is written on the author's Mac (repos `~/Documents/agent_paper_B`, `~/Documents/autoresearch_harness`). Exam runs on **zhixu portal** (1 × RTX 4090 24 GB, exclusive). Never use deepthought or zhixu experiment for this exam. Never run LLM inference on the Mac (R1-COMPUTE).
- **Branches.** Work on `exam-x-<YYYYMMDD>` in both repos, created from `main` (paper) and `r1` (harness). Small commits, author `Dowling Wong <wangdowling@gmail.com>`, each message ending with the attribution lines your own session prescribes. You may push your own `exam-x-*` branches so the portal can pull them; never push `main` or `r1`, never force-push, never rewrite pushed history. Merges into `main`/`r1` happen only after the independent acceptance of that phase and are done by the coordinating session or the author.
- **Labels.** Code and dry runs: ENGINEERING_ONLY / DRYRUN. Stage A: ENGINEERING_ONLY. B1 and B2 feed the appendix, so they are evidence runs and need the author's authorization note `docs/r1/authorizations/exam_<phase>_<date>.md` before they start (RUNBOOK §1).
- **Isolation from C3.** Exam campaigns use only exam seeds (instances 9001–9099, audits 9101–9299). They must never enter a C3 table (Phase 1.5 adds the guard).
- **GPU lease (26 Oct, R1-PORTAL-SCHEDULE).** Wrap every GPU job on the portal in `flock ~/r1_locks/gpu0.lock …` (create `~/r1_locks/` once), so the Track P agent can see when the card is busy. Track X evidence phases keep priority; Track P never pre-empts them.
- **Honesty.** A stopped run is reported as stopped. A box is ticked only when its check passed. No numbers are invented or carried from the Round-7 Paper A exam.
- **Independent review loop at every STOP (R1-EXAM-REVIEW).** (1) Spawn a fresh, independent reviewer agent that has not seen your work in progress. Give it the phase's goal, this runbook, the relevant PLAN §10 rows, the branch and commit range, and the phase's "Done when" criteria — **not** your own conclusions. It re-runs the checks and tests itself, reads the diffs and outputs, and writes `docs/r1/reviews/EXAM_<phase>_REVIEW_<date>.md` with findings classed MAJOR / MINOR and a verdict. (2) You fix every MAJOR finding and either fix each MINOR one or state why not, in new commits. (3) The same reviewer (or a second fresh one, if the first cannot be resumed) checks the fixes and writes an acceptance section in the same file: ACCEPTED, or the remaining findings. Repeat (2)–(3) until ACCEPTED or until a finding needs an author decision, which is a STOP. The reviewer never edits code or data; you never mark your own phase accepted.
- **Reporting.** After acceptance: a short report in `docs/r1/reports/`, a STATUS entry ("independently reviewed and accepted", with the review file), and a message to the author: what was done, commits, checks with results, the review verdict, what is not done, questions for the author.

## Phase 0 — Host facts on zhixu portal (read-only; ~1 h)

Find the SSH alias for zhixu portal in `~/.ssh/config` on the Mac (the Ada server is `experiment_zhixu`; the portal alias is not recorded — ask the author if it is not obvious). Then record, without installing anything:

| # | Fact | How |
|---|---|---|
| 0.1 | Hostname, OS, user, home and a work dir with space | `hostname`, `cat /etc/os-release`, `df -h` |
| 0.2 | GPU: name, memory, driver, CUDA version, compute capability (expect 8.9), other processes on the card | `nvidia-smi`, `nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv` |
| 0.3 | CPU cores, RAM (workers and audits run on the CPU) | `nproc`, `free -g` |
| 0.4 | Free disk where models will live: need ≈ 500 GB for ~24 GGUF files | `df -h <dir>` |
| 0.5 | Network: GitHub (clone/pull), huggingface.co (downloads), openml.org (expected unreachable; caches come from the Mac) | `git ls-remote`, `curl -sI https://huggingface.co`, `curl -sI https://www.openml.org` |
| 0.6 | Hugging Face auth and **gated models**: which registry repos require licence acceptance (Gemma 4, possibly Muse Glimmer, OLMo, Nemotron). The author must accept those licences on huggingface.co; list them. | `huggingface-cli whoami`; HEAD request per repo |
| 0.7 | Toolchain: python ≥ 3.11 or `uv`, git, cmake, a CUDA toolkit for building llama.cpp | `which`, `--version` |
| 0.8 | Existing llama.cpp builds on the host, if any | `which llama-server`, `llama-server --version` |
| 0.9 | Is anyone else using the card or its CPU (portal is exclusive to the author; confirm) | `nvidia-smi`, `uptime`, `who` |

Output: `docs/r1/reports/PORTAL_HOST_FACTS_<date>.md` with every value and the command that produced it. **STOP 0:** review loop on the host-facts report (the reviewer re-runs the commands over SSH); then the author accepts gated licences and confirms the disk location.

## Phase 1 — Code gaps (on the Mac; no GPU, no LLM; ~2–3 days)

Read first: PLAN §10 rows named above, RUNBOOK Track X and Track H, `r1/scripts/llama_server_instance.py`, `r1/scripts/c3_label_sweep.py`, `r1/scripts/c3_fake_llama_server.py`, `r1/scripts/llamacpp_probe.py`, `r1/c3/{audit,prior_model,control}.py`, harness `src/autoresearch/manager/langgraph_manager.py`, `src/autoresearch/llm/providers.py`, and `archive/old_b_2026-10-09/code/experiment_scaffold/src/causal_branch/round5_titan_exam.py` (machinery to port). Build a scratch venv outside the repos (earlier batches: Python 3.13 via `uv`); record the test baseline of both repos before changing anything.

| # | Gap | Done when |
|---|---|---|
| 1.1 | **Structured output (R1-SCHEMA).** Harness `llamacpp` provider can send `response_format: {"type": "json_schema", ...}` with schema `manager_proposal/v1`: an object with the six string fields the manager prompt already asks for, `rationale` first, then `summary`, `objective`, `param`, `old_value`, `new_value`; all `type: string`, **no enum of keys or values** (D25 validation stays the model's job). Off by default (historical byte-identical); when on, the schema version is recorded in every manifest and `llm_call` record. Under the schema, a parse failure is recorded as `parse_failed` and counted (no silent heuristic fallback to the default objective); the free path keeps its historical behaviour. | Harness tests; fake-server test that the request carries the schema and that a malformed reply is recorded, not replaced |
| 1.2 | **Thinking control.** `llama_server_instance` and the exam config express a per-model thinking policy: off (template switch, e.g. `enable_thinking=false` via chat-template kwargs), on with a token budget, or always-on with a budget; use what the pinned build supports (`llama-server --help`: reasoning budget/format flags). Reasoning text is kept out of the parsed proposal and its token count is recorded. | Tests with the fake server; flags recorded in the manifest |
| 1.3 | **Random-valid anchor proposer** (harness manager): uniform over the node's active keys and a declared value grid per key, seeded by (instance, trial); never an inactive key. | Tests: determinism, only active keys |
| 1.4 | **A4 self-forecast observer** for exam campaigns: after each executed proposal, one side query (Track H `ManagerQuestionPrior` / `chat_client`) asks the manager for P(Δ > 0) and P(no effect) of its own edit; recorded, charged to the LLM-call cap, never used by a decision (the controller always continues). | Test: decisions and ledgers identical with and without the observer except the recorded answers |
| 1.5 | **Exam namespace guard.** Exam manifests carry `label: EXAM` and seeds in 9001–9299; `r1.c3.dataset.build`/`build-sweep` and the C3 sweep runner refuse any such campaign. | Tests |
| 1.6 | **Registry and fit estimator** `r1/exam/registry.yaml` + `r1/exam/fit.py`: the **21 candidates and 3 anchors** of RUNBOOK Track X after the author removed unreleased Ornith-31B at STOP 0 (R1-EXAM-ORNITH), with HF base repo, quant source per R1-QUANT-SOURCE (to be filled in Phase 2), licence, gated flag, chat-template source, thinking policy, vendor sampling. `fit.py` estimates admissibility from the Q4_K_M file size + KV at 32,768 (R1-EXAM-CTX) from `config.json` (2 × attention layers × KV heads × head dim × ctx × 1 byte at q8_0; sliding-window layers at their window; DeltaNet/Mamba layers as fixed state) + 1.5 GiB ≤ 23.5 GiB (R1-EXAM-FIT), and states which numbers came from which config field. | Unit tests on 3 hand-checked configs |
| 1.7 | **Port the Round-7 machinery** into `r1/exam/`: licence blockers, Wilson interval, paired (template → instance) bootstrap, occupancy check, frozen-rule digesting. Adapt the quantization blocker to R1-QUANT-SOURCE. Carry their tests. | Ported tests pass |
| 1.8 | **Exam runner** `r1/scripts/exam_runner.py`: one dedicated `llama-server` per candidate (sha256 + build pin, full offload, alias), subcommands `stage-a`, `b1`, `b2`, resumable per campaign root (reuse the C3 sweep runner's resume and watchdog), per-candidate manifest, refusal on any `TODO_VERIFY_ON_HOST`. CPU workers and audits as in the C3 sweep, exam seeds only. | Fake-server end-to-end dry run: 2 fake candidates + the 3 anchors, Stage A and a 1-instance B1 on 2 nodes, one kill-and-resume |
| 1.9 | **Analysis** `r1/exam/analyze.py` for Stage A, B1 (finalist rule) and B2. The rule is a file `r1/exam/rules/x5_rule_v1.yaml` committed with its sha256 **before** any B1 data exists. | Tests on synthetic manifests |
| 1.10 | **Config** `r1/scripts/configs/exam_portal.json` with every host value as `TODO_VERIFY_ON_HOST`; ctx 32,768, q8_0 KV, `n_gpu_layers` 999, temperature 0.2 + D26 seed, schema on. | `--check-config --allow-placeholders` passes |

**STOP 1:** handoff `docs/r1/overnight/EXAM_X_CODE_HANDOFF.md` with test counts before/after; review loop (the reviewer re-runs both test suites and the fake-server dry run); after acceptance the code is merged and pushed, then pulled on the portal.

## Phase 2 — Build, download and pin on the portal (~1 day, mostly downloads)

| # | Step | Done when |
|---|---|---|
| 2.1 | Pull the merged code on the portal; build llama.cpp at one pinned commit with CUDA for compute capability 8.9 (`CMAKE_CUDA_ARCHITECTURES=89`); record the `llama-server --version` line. | Build line recorded in the config |
| 2.2 | **Resolve the GGUF source per candidate (R1-QUANT-SOURCE):** the vendor's own Q4_K_M if the vendor publishes one; otherwise **bartowski**'s imatrix Q4_K_M; gpt-oss-20b at native MXFP4. If neither exists for a candidate, do not substitute another quantizer: list it for the author. Record repo @ revision, file name, size, sha256. Non-uniform research quants (e.g. ISTA-DASLab GSQ-RCO IQ types) are not Q4_K_M and are out of the pool. | Registry filled; missing ones listed |
| 2.3 | Download to the Phase-0 location; verify sha256 after download. | All sha256 match |
| 2.4 | Run `fit.py` on every candidate (estimate at 32k). | Fit table |
| 2.5 | Copy the OpenML caches for the exam nodes from the Mac (the portal cannot reach openml.org); check them as the C3 sweep does. | Cache check passes |

**STOP 2:** review loop (the reviewer re-checks every sha256, source and fit estimate); report the registry and the fit table.

## Phase 3 — Stage A (RUNBOOK X.2; ENGINEERING_ONLY; ~1 day)

For every candidate and anchor model:
1. **Fit probe:** start `llama-server` (ctx 32,768, q8_0 KV, all layers on GPU); prefill a 32k-token prompt; record peak VRAM, full offload by the runner's two routes, free memory ≥ 1 GiB. A model that fits only at 16k: re-probe at 16,384 and flag "CPU-pool rows only".
2. **Template check:** `--jinja` render vs the HF chat template on 5 fixed prompts, byte-equal.
3. **Grammar after thinking:** with thinking on and the schema on, the grammar must constrain only the final answer, not the reasoning. If it does not, the model runs thinking-off and is flagged.
4. **50 frozen manager prompts** replayed from real memory-on ledgers (the three rerun-2 memory-on nodes plus existing memory-on digits liveness ledgers from 14 Oct; author correction R1-EXAM-PROMPT-SOURCE, DT4 is memory-off; ≥ 4 nodes; the prompt set and its sha256 are committed first): parse rate free and with schema, active-key validity rate, D26 seed reproducibility (two calls identical at temperature 0.2), latency p50/p95, prompt/completion/reasoning tokens.
5. Failure classes kept apart: offload, template, parse, grammar, timeout. One template repair per model is allowed, declared in the report before Phase 5.

**STOP 3:** review loop on the Stage A table; then the author confirms exclusions.

## Phase 4 — Author gate (no agent work)

Before Phase 5 the author must have (a) adopted the X.2–X.6 protocol (**done 26 Oct, R1-EXAM-PROTOCOL**); (b) recorded the sha256 of the accepted `r1/exam/rules/x5_rule_v1.yaml` in a PLAN §10 row; (c) written the authorization note for B1. If any is missing, wait.

## Phase 5 — B1 screen (RUNBOOK X.3–X.4; evidence; ~3–4 days)

- Anchors first (X.3): random-valid, scripted, `qwen2.5-coder:7b`. If random-valid < scripted on audited mean increment cannot be shown, STOP: the exam has no discriminating power.
- Every admissible candidate: three nodes (`digits_mlp` if D28 passes on llama.cpp, else `tabular_mlp`; `openml_credit_approval`; `openml_ionosphere`), instances 9001–9004, W = 20, memory `append_only_summary`, `"vary"` split, temperature 0.2 + D26, schema on, A4 observer on. **Thinking (R1-EXAM-PROTOCOL):** primary mode is thinking off for every model that can switch it off; those models also run thinking on (budget 2,048) on one node (`openml_credit_approval`), and the mode with the higher audited μ̂ is used in B2; always-thinking models run with a 2,048-token budget. Audits: every non-inert, non-duplicate proposal on seeds 9101–9104.
- One llama-server per candidate; one candidate at a time; resumable; interruptions logged.

**STOP 5:** B1 manifests; run `analyze.py b1` with the committed rule; review loop (the reviewer recomputes the finalists from the manifests and checks the rule hash); report the finalists.

## Phase 6 — B2 finalists (RUNBOOK X.6; evidence; ~1–2 days)

The number of instances per node is computed from the B1 variance by the declared rule, written into a PLAN row by the author, and authorized before B2 starts. Finalists on fresh instances 9011+; final audited Y on seeds 9201–9210; plus a Track G node only if G.1 and G.3 are done and the author adds it. Top 3 rerun once in the other thinking mode.

**STOP 6:** B2 report `docs/r1/reports/PROPOSER_EXAM_<date>.md`; review loop (the reviewer recomputes every table from the manifests); then the author decides X.7 (D22 proposer, B.6 manager, appendix).

## Timing

The 4090 is also the B.5 training card (~22 Nov). Target: Phase 1 done ~29 Oct, Phase 2–3 ~1 Nov, B1 ~6 Nov, B2 ~10 Nov. If B1 runs long, stop at the end of a candidate and report; do not cut instances to save time without an author decision.
