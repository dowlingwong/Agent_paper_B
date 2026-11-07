# Paper B (route R1) — status log

## 7 November 2026 — B1 audit directory preservation (AI-assisted)

The in-place preservation of audit work directories was independently accepted in `B1_AUDIT_PRESERVATION_R2_REVIEW_20261107.md` and integrated at `5f8b8f93`. B1 STOP quiescence, the pinned harness cleanup, storage capacity and full-suite execution remain open; `B1_STOP_QUIESCENCE_INVESTIGATION_20261107.md` records the independently reviewed STOP blocker. B1 has not started.

Five synthetic fixture cleanup removals were independently accepted at `bcded1c5` (review `B1_MAC_SUITE_FIXTURE_PRESERVATION_REVIEW_20261107.md`); full-suite and indirect cleanup remain open.

## 26 October 2026 — approved archival complete; same-source retry active (AI-assisted)

The independently reviewed one-time resolver archived six partials (**77,100,569,825 bytes**, full SHA before/after) and retained 17 history files, including the original STOP/logs. Journal: [https_short_stop_resolution.json](reports/exam_phase2_20261026/https_short_stop_resolution.json). Five verified GGUF files remain unchanged. Author-approved retry started with unchanged six-worker receiver, controller **1615560**, fresh `https_downloads_retry1.log` and PID file under portal `work/phase2/`. Remaining 17 artifacts total 255,100,593,248 bytes; after archival available space was 531,513,647,104 bytes. The 100 GB floor remains enforced. Executed recovery independently **ACCEPTED**: all six archived partials and 17 history files match full hashes; five completed artifact identities remain unchanged; six workers belong to the new controller. STOP 2 remains open (5/22 received). No real Stage A, B1 or B2 has started.

## 26 October 2026 — author approves short-transfer archival and retry (AI-assisted)

PLAN §10 R1-EXAM-TRANSFER-RETRY records direct author approval to archive all six retained partials with size/SHA records and retry the remaining files from the same immutable sources. All five verified artifacts and the original STOP/log history will be retained. Recovery utility is under independent review before portal mutation; no retry has started at this checkpoint. The 100 GB floor and STOP 2 independent receiving gate remain unchanged.

## 26 October 2026 — author approves native prefill reserve; new transport STOP (AI-assisted)

PLAN §10 R1-EXAM-PREFILL-RESERVE records the author's approval: keep declared context and fit math at 32,768, prefill 32,767 with n_predict 1; fallback context 16,384 with 16,383 prefill plus one generated token. Results retain requested and actual counts and the one-slot reserve. Independent engineering review accepted the implementation at `6ef8d30` (config `7ba7e2b`), including both-context early-load failures and fake-server end-to-end validation; code was transferred by SSH only. This closes the API clarification only; no real Stage A request has started.

A subsequent read-only receiving check found the direct HTTPS cohort stopped. Five artifacts have certificates; Nemotron's retained partial is 15,695,959,265 bytes against the pinned 25,477,403,616 bytes (9,781,444,351 short). The worker reported size/digest mismatch, shared cancellation stopped the cohort, and no matching transport processes remain. Six partials and the STOP marker are preserved. Free space: 531,517,050,880 bytes. Independent inspection/receiving is ongoing; no recovery or restart has been performed. STOP 2 remains open.

## 26 October 2026 — Phase 2 receiving ongoing; Stage A API clarification pending (AI-assisted)

Direct HTTPS receiving remains active with six bounded workers, full size/SHA checks and the approved 100 GB available-space floor. Latest checkpoint: 2/22 artifact certificates, 651,513,733,120 available bytes. The independent review remains pending; STOP 2 is not closed. CPU tokenizer reports reconcile 22/22 current template pins. The earlier HF/Xet CAS failure, library-deleted failed OLMo temporary, retained archives and reviewed transport recovery are documented in [Phase 2 report](reports/PORTAL_EXAM_PHASE2_20261026.md).

Pinned-server source inspection independently confirms rejection of prompt length equal to context, and first sampling even with n_predict 0. The author has been asked whether to adopt a one-slot reserve (32,767 prompt + one generated token at context 32,768; corresponding 16k fallback). This amendment has not been adopted. See [API conflict](reports/exam_phase2_20261026/PREFILL_API_CONFLICT.md). No real Stage A request, B1 or B2 has started.

## 26 October 2026 — author approves Stage A fourth memory-on prompt source (AI-assisted)

PLAN §10 R1-EXAM-PROMPT-SOURCE records the direct author approval to use the existing 14 Oct memory-on digits liveness ledgers as the fourth source. Rerun-2 memory-on covers three nodes; DT4 is entirely memory-off and will not be relabelled. Fifty source/hash-verified real memory-on prompts will be frozen before Stage A, after Phase 2 review. This closes the prompt-source clarification only; Phase 2 receiving/review remains in progress, with no Stage A or evidence run started.

## 26 October 2026 — author STOP 2 source amendment recorded; Phase 2 in progress (AI-assisted)

PLAN §10 R1-QUANT-SOURCE / R1-EXAM-SOURCE-STOP2 records the direct author decision: Qwen3-Coder-30B-A3B-Instruct uses the exact standard Unsloth Q4_K_M as a single source exception, labelled "source exception (unsloth)" in every table, fully pinned. Qwopus3.6-27B-v4 is removed as unavailable, no substitute; other-version GGUFs are not this candidate. Effective pool is 20 candidates plus three anchors, with OLMo Think separate. Finish all downloads and SHA checks before STOP 2 independent acceptance; no Phase 3 or evidence run has started.

## 26 October 2026 — exam Phase 1 merged into `main` / `r1` by the coordinating session

Harness `r1` fast-forwarded to `897d83c` (exam Phase 1; re-run in the coordinator's Linux VM env: 453 passed / 9 failed / 1 error, no failure outside the known environmental set). Paper `exam-x-20261026` (`ea6dd8c`, independently accepted at STOP 1) merged into `main`, which had meanwhile gained the Track P documents (`e09b399`, `b5a7aec`); PLAN §10 and STATUS conflicts resolved by keeping both sets of rows/entries. **Note for the author:** R1-EXAM-TRANSFER (no GitHub credentials on the portal; code via SSH bare repos) and R1-TRACKP-RUNBOOK (Track P agent clones from GitHub on the portal) differ on GitHub credentials on the portal; both agents must take the R1-PORTAL-SCHEDULE GPU lease. Not pushed (needs the author's credentials).

## 26 October 2026 — portal exam Phase 1 independently reviewed and accepted; STOP 1 (AI-assisted)

Completed runbook code gaps 1.1–1.10 on the Mac, with no LLM inference or model-weight downloads. Paper implementation `e6f42c0`, fixes `930687c` / `57f56e5` / `df1a6eb`, evidence `b3764a3`; harness `897d83c8efa364ec2fdd37288241cc42e01d7274`. Frozen rule bytes/hash committed at `4b9c656` before any B1 fixture data. Corrected storage remains `/home/dowling/exam-x/{models,work}`, with a 100 GB floor; no portal runtime install or code transfer occurred.

Fresh independent reviewer reran both full suites, the fake-server Stage A/B1 kill/resume pipeline and final focused checks; **ACCEPTED**, all three MAJOR and one MINOR findings resolved: [EXAM_1_REVIEW_20261026.md](reviews/EXAM_1_REVIEW_20261026.md). Broad checkpoint: paper 445 passed / 21 failed / 9 skipped (baseline 417 / 22 / 9); harness 454 passed / 8 failed / 1 collection error (baseline 448 / 8 / 1). Zero new failure/error IDs; one baseline paper watchdog failure passed in both after runs. Full suites launched at initial implementation; final fixes independently checked with 31 passing focused tests and counterexamples. Existing failures remain documented. All campaign outputs are synthetic DRYRUN fixtures.

Handoff: [EXAM_X_CODE_HANDOFF.md](overnight/EXAM_X_CODE_HANDOFF.md). Report and saved evidence: [PORTAL_EXAM_PHASE1_20261026.md](reports/PORTAL_EXAM_PHASE1_20261026.md). **STOP 1:** ready for author/coordinator merge; no protected branch merge/push, Phase 2 activity, scientific rule adoption or B1/B2 authorization inferred.

## 26 October 2026 — author STOP 0 decisions recorded; Phase 1 authorised (AI-assisted)

Recorded the author's direct STOP 0 decisions in PLAN §10 R1-EXAM-STORAGE / LICENCES / ORNITH / TRANSFER / USER-RUNTIME. Approved storage is `/home/dowling/exam-x/{models,work}` (author corrected the initial `/ceph` paths after a read-only portal check found `/ceph` absent); downloads/runs must stop below 100 GB available on that filesystem. Licences approved for research evaluation and publication, including Nemotron/Laguna OpenMDW-1.1 and LFM2.5 LFM 1.0. Ornith-31B is removed as not publicly released, no substitute; effective pool 21 candidates plus 3 anchors (OLMo Think remains a sensitivity). Ornith-35B maps to `ornith-ai/Ornith-1.0-35B`, with vendor GGUF Q4_K_M checked first in Phase 2. Code transfer uses Mac-to-portal SSH pushes to bare repositories under `/home/dowling/exam-x/work/`; no portal GitHub credentials. User-level uv/Python >=3.11 installation under `/home/dowling` is permitted, no sudo/system Python changes; installation not yet performed. Phase 1 is now authorised, with independent review at STOP 1; no later phase or evidence authorisation is inferred.

## 26 October 2026 — portal exam Phase 0 resumed, independently reviewed and accepted; STOP 0 (AI-assisted; ENGINEERING_ONLY)

The author restored Tailscale and authorised resuming Phase 0 only, with independent review and STOP 0 for disk/licence decisions. SSH to `portal_zhixu` succeeded. Inventory commits `57d8fc4` / `0791688`, formatting cleanup `d8d1035`; report: `reports/PORTAL_HOST_FACTS_20261026.md`, command transcripts and metadata under `reports/portal_host_facts_20261026/`. Same independent reviewer re-ran SSH checks and accepted the **read-only inventory and decision package**, with no remaining report corrections: `reviews/EXAM_0_REVIEW_20261026.md`, resumption acceptance. The initial failed attempt and blocked-record review remain preserved below/in Git history.

- **Host facts:** TASL-2, Ubuntu 22.04.5; RTX 4090, 24,564 MiB, driver 535.309.01, compute capability 8.9; 32 logical CPUs, about 62 GiB RAM. About 899 GB / 837 GiB available on the filesystem containing `/home/dowling`. No GPU compute applications at either sample; another user's desktop remains present. This establishes neither future reservation nor model fit.
- **Preparation gaps:** Python 3.10.12, no uv/HF CLI/visible llama-server in checked scope. CUDA toolkit 12.2 is installed outside PATH. Public GitHub works, but private paper repo HTTPS lacks credentials and SSH stops at an unknown host key. OpenML homepage HEAD 200, metadata API HEAD 412; cache-transfer plan unchanged.
- **HF/licence scope:** no token in the checked environment/cache scope. Twenty candidate base repositories plus OLMo Think and the 7B anchor report `gated=false`, with API/config HEAD 200; eventual GGUF weight access is not established. Custom terms are documented for Nemotron, LFM2.5 and Laguna. Ornith-31B remains unidentified; a vendor Ornith-35B repo is a documented possible mapping for the 35B-A3B label, not an adopted substitution.
- **Verification:** independent live host/network/per-repo rechecks; Python and shell syntax, all JSONL records and `git diff --check` passed. No installation, build, inference, worker run, weight download, credential/known_hosts change, merge or push was performed in this resumption.
- **STOP 0:** author to confirm proposed `/home/dowling/exam-x/{models,work}`, decide the licence package, and resolve Ornith identities/mapping. Paths were not created; no licence accepted. Phase 1 and all later phases remain unstarted.

## 26 October 2026 — portal exam Phase 0 blocked by local network access (AI-assisted; ENGINEERING_ONLY)

Updated `main` was verified at `fad6dfe` (R1-EXAM-HOST conflicts resolved). Created `exam-x-20261026` from paper `main` and harness `r1` (`6afdb0e`), preserving existing untracked files. Paper commit `39731ce` records the attempted host inventory in `reports/PORTAL_HOST_FACTS_20261026.md`. SSH to `portal_zhixu` (`dowling@100.120.160.70`) returned `Network is unreachable` outside the sandbox; local `tailscale status --json` reports `BackendState: Stopped`. No remote command ran; all host facts 0.1–0.9 remain uncollected. Phase 0 is incomplete, not accepted. Independent review (`reviews/EXAM_0_REVIEW_20261026.md`) reproduced the access blocker: ACCEPTED AS A BLOCKED EXECUTION RECORD ONLY; PHASE 0 NOT ACCEPTED / INCOMPLETE. One MAJOR completion blocker (missing host facts), no MINOR corrections; `git diff --check` passed. Restore the Mac's Tailscale connection before resuming the read-only inventory; the author storage/licence gate remains pending. No installation, inference, worker run, model download, Phase 1 implementation, merge, or push occurred.
## 26 October 2026 — Track P agent moved onto zhixu portal (AI-assisted; documents only)

- Author decision (R1-TRACKP-RUNBOOK revised): the Track P agent runs on zhixu portal itself, not on the Mac over SSH. `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` updated: placement table, host and clone rules (own clone on the portal, `trackp-<date>` branches pushed with the portal's GitHub credentials), secrets on the same host (never read or passed on a command line), Phase 0 checks GitHub push and the agent's own endpoints, Phase 1 code and CPU-only tests on the portal, reviewers on the same host. RUNBOOK Track P execution line and hardware note aligned.
- Needed from the author before Phase 0: start Claude Code on the portal; GitHub authentication on the portal (clone of the private repo, push of `trackp-*`); `~/.config/r1/secrets.env`.

## 26 October 2026 — Track P revised and adopted; portal agent runbook for Track P (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): R1-C3-POST (Track P revised: belief/action decoupling, decision-model exam P.3a/P.3b, reasoning arm P.6, bounded-score RL rewards), R1-C3-CONTROL (Qwen3.5-0.8B/4B-Base control), R1-SOFT-SIGMA (pooled σ̂ in the soft label), R1-PORTAL-SCHEDULE (Track X evidence first on the 4090; GPU lease), R1-JEV-RUNG (official TypeSafe API, version pinned and logged), R1-RB-TEACHER (DeepSeek-V4.1-Flash-1017 demonstrations), R1-TRACKP-RUNBOOK.
- RUNBOOK: Track P replaced; C.1 and B.5 rows aligned; host rule for the GPU lease added.
- New: technical specification `docs/r1/TRACK_P_POST_TRAINING.md`; reading list `docs/r1/references/` (Jev architecture reconstruction, calibration notebook notes; three paper PDFs still to be added by hand — arXiv/ACL are not reachable from the agents' sandboxes); agent runbook `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` (Phase 0 host facts, Phase 1 code, Phase 2 pins, Phase 3 P.0 spikes, Phase 4 toy batch, Phase 5 P.3a, Phase 6 label gate, Phase 7 P.3b, Phase 8 A5, Phase 9 A6 and R-B).
- `PORTAL_EXAM_RUNBOOK.md` §0: one added line asking the Track X agent to take the same GPU lease.
- **Open for the author:** StartLux rung after P.0; Track H.8 `OfflineBanditEnv` action = bin must become execute/skip before P.5 uses it; place `~/.config/r1/secrets.env` (TYPESAFE_API_KEY, DEEPSEEK_API_KEY) on the portal; start Tailscale on the Mac (the Track X agent found it stopped).

## 26 October 2026 — exam execution decisions; portal agent runbook (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): R1-EXAM-CTX (32k), R1-SCHEMA (structure-only `json_schema` in exam and sweeps, before sweep 1), R1-QUANT-SOURCE (vendor Q4_K_M, else bartowski; GSQ-RCO out), R1-EXAM-RUNBOOK.
- New agent runbook `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md`: Phase 0 host facts, Phase 1 code gaps (schema, thinking control, random-valid anchor, A4 observer, exam namespace guard, registry and fit estimator, ported Round-7 machinery, exam runner, analysis with a pre-committed rule, config), Phase 2 downloads and pins, Phase 3 Stage A, Phase 4 author gate, Phase 5 B1, Phase 6 B2.
- Later the same night: author adopted X.2–X.6 with the two amendments (R1-EXAM-PROTOCOL), required an independent review loop at every exam phase (R1-EXAM-REVIEW), and decided Q10 (R1-A1-VERIFY: A1 unchanged; non-firing verify reported as a confirmed prediction). Runbook updated accordingly.

## 25 October 2026 — Track H: DAC control interface, Mac steps H.1–H.9 (AI-assisted; ENGINEERING_ONLY / DRYRUN; reviewed and accepted 26 Oct)

Acceptance by the coordinating session (Claude), 26 Oct. Re-ran in the Linux VM: harness 446 passed / 10 failed / 1 error (the known environmental set, unchanged from the baseline); paper 439 passed / 1 skipped / 1 failed (known `test_real_runner_desktop_dryrun`) plus `test_c3_control_dryrun` (1 passed). Read the harness diff (defaults byte-identical: `detail`/`events` only when set, `skip_display` only when declared, re-screen only for controllers that opt in) and the RuleController, featurizer v2, KG-verify and AWR changes. Accepted. Author answers recorded: H.4 line keeps the trial id and summary prefix; D25 inactive-key skips keep their old line; "identical information set" means identical declared access. **Open for the author (Q10):** at the declared g = 0.1 σ_node and r = 2, KG verify can never pay (VoI < 0.4 σ_cmp ≤ 2rg), so A1's verify is vacuous on these nodes; the control dry run used r = 1, campaigns use the declared r. Merge order: harness `track-h-25oct` → `r1` first (pin `6afdb0e`), then this branch → `main`.


- **Review round (26 Oct; still pending review).** Coordinator review asked for six fixes, all done on the same branches: F1 AWR trains on the label half only (`bd45aea`); F2 control-plane skips no longer count in `invalid_so_far` (featurizer v2; tables byte-identical) (`fab1a9c`); F3 `RuleController` verifies at E2 with D23's KG rule and `posterior_mean/v1`, A1 equals the index-policy arm including verify (`7053f42`); F4 the hybrid re-screens its revision once (harness opt-in hook `6afdb0e`, paper `9aafb55`); F5 LLM self-control at E1/E2 by flag (`bdf1ce3`, test fix `6c7b19c`); F6 W and the LLM cap bind, the trial budget never does, `matching_report` flags violations (`4ae8a1b`). Pin → `6afdb0e` (`2523e0c`). New DRYRUN manifest `results/r1/engineering/c3_control_dryrun_20261025T231516Z` (`a19b447`), all 14 checks pass. Finding: at g = 0.1 σ_node with r = 2 KG verify can never fire (VoI < 0.4 σ_cmp ≤ 2rg); the dry run used r = 1 and still no verify fired. Tests: paper 446 / 1 skipped / 1 failed (known); harness 446 / 10 / 1 (same failing set).

Implementation agent (Claude) on branch `track-h-25oct` in both repositories (paper from `bf45424`, harness from `r1` `264011e`); not merged, not pushed. No LLM, GPU, SSH, real llama.cpp/Ollama or model weights; fake servers and fake sidecars only. Details, deviations and questions: `docs/r1/overnight/TRACK_H_25OCT_HANDOFF.md`.
- **Harness `2604a97`:** `ControlDecision.detail` and whitelisted controller events (`prior_unavailable`); R1-SKIP-DISPLAY `one_line/v1` in the memory summary, `campaign_started` and snapshots. Defaults unchanged.
- **H.2 (`ffac687`):** one featurizer `features_from_view` for the online controller and `dataset.build`; pilot table byte-identical; online features from real `ControlView`s hash-equal all 1,323 pilot rows; leak tests.
- **H.1 (`211552a`):** `PriorModel`/`Forecast`; wrapped A1–A3 reproduce `offline_eval` on the 19 Oct pilot table bit for bit; A4 typed questions. NGBoost variant not in the code base, not added.
- **H.3/H.6 (`5de18eb`):** `RuleController` for every arm (rule skips first, Prop. 8 skip, one cached forecast serves E2's Bayes keep, full decision records, A4 charged to the LLM cap); A1 equals the constant-prior index policy on a scripted campaign.
- **H.4 (`afda1ce`):** skipped proposals shown as one line without a metric; manifests record `skip_display`.
- **H.5 (`2046f97`):** stdlib sidecar with sha256 pin and `FakeLoader` (real loader = Track P.2); 1 s timeout → A1 fallback + `prior_unavailable`.
- **H.7 (`801f6e1`):** AWR direct arm, LLM self-control, hybrid (a proposal); `matching_report` checks instances, W, LLM cap, information set.
- **H.8 (`bc6fc10`):** `OfflineBanditEnv` (Gymnasium API, optional); reproduces `offline_eval` one-step values (rel. 1e-12).
- **H.9 (`7ada947`, `2647fab`):** desktop DRYRUN, 2 nodes × 10 arms, SIGKILL mid-campaign and resume, all checks pass: `results/r1/engineering/c3_control_dryrun_20261025T224515Z/summary.json`.
- **Pin (`8ef8f8f`):** `HARNESS_PIN_C3` → `2604a97`, which is not on harness `r1` yet: merge harness `track-h-25oct` into `r1` before this branch reaches `main`, or a sweep launch STOPs.
- **Tests:** paper 383 passed / 1 skipped / 1 failed → 435 / 1 / 1 (same known failure); harness 433 / 10 / 1 → 443 / 10 / 1 (same failing set).
- **Questions for the author:** H.4 line wording (trial id + summary prefix); which skips get the line; meaning of "identical information set"; hybrid definition; online trial budget vs W; `invalid_so_far` semantics; A4 calibration data; A6 τ_node; LLM self-control epochs.

## 25 October 2026 — exam located; Tracks X, H, P added to the RUNBOOK (AI-assisted; documents only)

- **Exam located.** The model "exam" is the Round-7 candidacy exam of the Paper A repo (`agent-checkpoint-intervention`, `paper/appendices/C_protocol.tex`; `round10/CANONICAL_EXAM_RESULTS.md`; evidence `evidence/round7-blackwell-grouped/run/`), completed 4 Sep 2026; a code copy is in `archive/old_b_2026-10-09/code/.../round5_titan_exam.py`. Assessment (coordinating session): sound machinery, but it measures a tool-using coding agent on a different task and hardware, is confounded by submission-format conformance, and is an eligibility screen only. Not evidence for R1; machinery to be ported (Track X.1).
- **Author decisions** R1-EXAM-POOL and R1-DAC-INTERFACE recorded (PLAN §10). RUNBOOK gains Track X (proposer exam on zhixu portal), Track H (DAC interface) and Track P (post-training); host rule on proposer size updated.
- **Finding for R1-C3-BASE:** StartLux-Decision publishes no training code and its Instant models use bidirectional prompt attention via a vLLM plugin, so "fits TRL GRPO directly" is unverified (P.0 spike decides). Kev's trainer takes hard labels only and has no RL code (soft-label patch needed).
- **Decisions needed:** adopt the Track X protocol (X.2–X.6); H.4 skip display in manager memory; P.1 Qwen3.5-Base control rung; Track P as a whole.
- Evening: author decided H.4 (R1-SKIP-DISPLAY) and the Q4_K_M basis of the fit estimate (R1-EXAM-FIT); Track X revised after an audit (B1 screen on audited proposal increments, B2 finalists, roles separated, A4 self-forecast, 32k context proposed; prompt lengths measured: max 1,345 tokens). Branch `track-h-25oct` (rebased on `main` `a8aa001`), not merged.
## 25 October 2026 — batch B: A.10, C3 label sweep ported to llama.cpp (AI-assisted; ENGINEERING_ONLY; reviewed and merged)

Review by the coordinating session (Claude), 25 Oct. Found before merge: the runner accepted GPU offload only from the `offloaded N/N layers` log line, which llama.cpp v0.7.0 does not print on deepthought (probe report on branch `dt-sweep1-20261025`); fixed in `8122600` with the author's two-route acceptance. Re-ran the offload/instance/probe tests (57 passed) and the three llama.cpp dry runs (3 passed). Fast-forward merged into main. Harness `batch-b-25oct` fast-forwarded into `r1` and pushed (`origin/r1` 4012897 → 264011e; this also published `7305434`, the `openml_climate` node, which had not been on origin). Deepthought agent runbook added as `docs/r1/prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md`.

Implementation agent (Claude) on branch `batch-b-25oct` in both repositories (paper from `main` `3d3ec48`; harness from `r1` `7305434`); not merged, not pushed. No LLM, GPU, SSH, real llama.cpp or Ollama; fake servers only. Details, fail-before evidence, host checklists and build recipes: `docs/r1/overnight/BATCH_B_25OCT_HANDOFF.md`.
- **Runner (`d560490`):** config `backend` (`ollama` default, historical path unchanged; `llamacpp`): dedicated `llama-server` per batch (`r1/scripts/llama_server_instance.py`), GGUF sha256 and `llama-server --version` line pinned before every start, `/health`, `/v1/models`, `/props`, one-token probe, full GPU offload from the server log (CPU fallback or partial offload = STOP), census as before; watchdog via `/health` and `/v1/models`; orphans stopped only if pid, owner, process group and command line match; A.5 resume unchanged. Collectors/liveness take `--manager-model llamacpp/<alias>`. Fixed: a root failing with the OpenAI client's unpicklable exception broke the collector's process pool.
- **Fake server and dry runs:** `c3_fake_llama_server.py`; `c3_sweep_dryrun.py --backend llamacpp`. Passing on the llama.cpp path: the deepthought config (retry + permanent), kill-and-resume, watchdog (server SIGTERM).
- **Harness (`264011e`, pin updated in `HARNESS_PIN_C3`):** `llamacpp` base URL gets `/v1`; no API key needed; no hidden OpenAI-client retries (before: a dropped request was retried silently, outside the logged D26-seeded retry). Seed reaches the request and the `llm_call` record; connection errors classified like Ollama's.
- **Configs (`607f78e`):** deepthought on llama.cpp with nine `TODO_VERIFY_ON_HOST` values; new zhixu portal draft; author's answers applied (watchdog on, limits 5/3, `min_live_nodes` 8, Paper A check "not applicable" via `paper_a_status.py --not-applicable`, refused on `ucrtasl`). Ada config unchanged.
- **A.11 helper (`adab041`):** `python3 -m r1.scripts.llamacpp_probe` — one-token load probe with the runner's own checks; gives `build`, `model_sha256`, `footprint_mib`.
- **Review fix (`8122600`):** on deepthought, llama.cpp v0.7.0 (commit 620d222) printed no `offloaded N/N layers` line at default verbosity (report on `dt-sweep1-20261025`), so the log-only check would STOP every real start. Now full offload passes by route (i) the N/N line (partial N/M = STOP) or route (ii) the server pid on the configured GPU with ≥ the pinned `footprint_mib` (refused if unset); CPU fallback stops both; the route is recorded. The probe records loaded telemetry before any assertion, adds a `-ngl 0` CPU control (≥ 2× slower) for route (ii), exits 1 on STOP and reports the footprint to pin. No verbosity flag added (not verifiable offline). Build pin format `version: 0.7.0-dev (build 1, commit 620d222)`; the working deepthought build recipe is in the handoff.
- **Tests:** paper 327 passed / 1 failed → 359 passed / 1 failed → 384 passed / 1 failed after the review fix (same known `test_real_runner_desktop_dryrun`); harness 427 passed / 9 failed / 1 error → 434 / 9 / 1 (same failing set).
- **Questions for the author:** one manager per TITAN (open; options and their needs in the handoff); `ctx_size` 8192 is a proposal (prompt lengths unmeasured); bit-repeatable same-seed retries would need `cache_prompt: false`; which GGUF is pinned; build pin = the `version:` line (or also the full commit); harness `264011e` must reach `r1` before a launch.

## 24–25 October 2026 — Phase A coding batch: A.4, A.5, A.8, A.6 draft (AI-assisted; ENGINEERING_ONLY; reviewed and merged)

Review by the coordinating session (Claude), 25 Oct: re-ran the new table, deepthought-config and resume tests (12 passed + 1 skipped; 16 passed) and the three end-to-end dry runs including kill-and-resume and the watchdog (3 passed, 134 s; they need TMPDIR on a disk with free space). Read the orphan-stop code: a process is signalled only if pid, process group, port and models directory match the batch record; another user's process is never signalled. Fast-forward merged into main. The open questions in the handoff are for the author.

Implementation agent (Claude) on branch `batch-a-24oct` (paper repo, from `42c93f6`); not merged, not pushed; harness unchanged. No LLM, GPU, SSH or real Ollama. Details, fail-before evidence and the deepthought checklist: `docs/r1/overnight/BATCH_A_24OCT_HANDOFF.md`.
- **A.4 (`62571dc`):** `python -m r1.c3.dataset build-sweep --index <index or batch dir> --out DIR` builds the C3 table from a completed sweep. On fixture indexes over the 19 Oct pilot ledgers it reproduces `build()` byte for byte, and the 19 Oct split-recheck rows apart from the 22 Oct `noop_kind` field.
- **A.5 (`c560ef9`):** an interrupted sweep phase resumes on `--start <batch>`: completed roots kept, started roots re-run whole (partial attempts archived), each interruption logged (batch, step and runner logs, sweep directory). The orphaned Ollama of the batch is stopped only after pid, process group and environment match. Dry run: SIGKILL mid-campaign, then restart → batch completes, completed roots unchanged.
- **A.8 (`c560ef9`, opt-in):** watchdog for the dedicated Ollama (exit/signal, unresponsive, model unloaded): records the loss, restarts the instance, re-runs affected roots. Dry run: server SIGTERM mid-request → recorded and recovered. Deepthought smoke not done (needs the host).
- **A.6 draft (`8fe3416`):** `r1/scripts/configs/c3_sweep_deepthought.json` with seven `TODO_VERIFY_ON_DEEPTHOUGHT` values; the runner refuses such values at launch; `--check-config --allow-placeholders` passes locally.
- **Tests:** paper 296 passed / 1 failed → 327 passed / 1 failed (same known `test_real_runner_desktop_dryrun`); harness 427 passed / 9 failed / 1 error, unchanged.
- **Questions for the author:** which host is deepthought (RUNBOOK says deepthought2 with TITANs; STATUS 12 Oct says deepthought2 has L40S, deepthought has TITAN X); TITAN X on driver 525 has no demonstrated Ollama offload; one manager per TITAN needs four batches or a multi-instance runner; the Paper A check on deepthought; watchdog default; `min_live_nodes` 2 vs the planned eight nodes.

## 24 October 2026 — author decisions recorded; runbook rewritten

Recorded by an AI agent (Claude, coordinating session) at the author's request. No experiment ran.

- PLAN §10, new 24 Oct block: R1-C3-BASE (Kev and StartLux main, Laya rung, ≤ 4B), R1-HOSTS, R1-COMPUTE (revised: Mac as last resort only), R1-SWEEP-HOST (deepthought; no mixing hosts within one table), R1-C1-FLOOR (common 30-seed run accepted as the C1 table), R1-VENUE-3 (ICML 2027; only the venue changes), R1-BENCH-HARD (autoresearch, 1GC-7RC, MLGym added; role open), R1-PROPOSER-QUANT (Q4_K_M; ceiling ≈ 27B dense to 35B-A3B MoE).
- RUNBOOK.md rewritten for the post-18 Oct plan (route A ladder, C3 gate, D21 pool of eight): Phases A–E, Track G, host table, immediate queue. The 12 Oct L/E step lists are superseded; their completed work stays recorded below.
- C3_DESIGN §5 A5 row: base models per R1-C3-BASE. README venue line updated.
- Next (RUNBOOK §5 queue): coding batch A.4 / A.5 / A.8 on the Mac; A.1b climate fetch (author's terminal: the agent VM cannot reach OpenML); A.6 → A.7 → A.9 → sweep 1 (deepthought; the agent VM cannot reach it).


## 22–23 October 2026 — common 30-seed noise floor over ten nodes (accepted); D21 pool = 8

AI-assisted: run and report by a Claude subagent; verified, merged (`8aa9a5f`) and wired in by the coordinating session (Claude). PILOT pending the author's acceptance as the C1 noise-floor table (`reports/NOISE_FLOOR_COMMON_20261022.md`; `results/r1/pilot/E1_20261022T214606Z/`). No LLM, GPU or SSH.
- **Run:** 5,520 runs, 0 failures, 0 missing metrics; 30 seeds per condition on every node; 21.6 min on 4 workers. Environment: harness-locked venv (Python 3.13.16, scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.4), recorded in the manifest. Determinism re-check identical. The 12 Oct E1 runs reproduce bit-for-bit (1,152/1,152); the 22 Oct `credit_approval` re-measurement under scikit-learn 1.9.1 differs on tree models, verdict unchanged.
- **D21 rule applied as adopted** (≥ 2 material edits, mean P(wrong) ≥ 0.10, σ_joint > 0, 30 seeds; bootstrap reported only). Verdicts re-derived independently from the raw runs by the coordinating session: identical. `e1_report`'s extra label "more seeds needed" is not part of the rule; such nodes are reported as "does not qualify".
- **Qualify (8):** `digits_mlp` (mean P(wrong) 0.101; bootstrap 0.48), `tabular_mlp` (0.125), `openml_breast_w` (0.233), `openml_ionosphere` (0.195; δ_n 0.004), `openml_wdbc` (0.174), `openml_credit_approval` (0.229), `openml_sonar` (0.196; δ_n 0.0032), `openml_blood_transfusion` (0.103; bootstrap 0.48). **Do not qualify:** `openml_credit_g` (1 material edit; its C ×0.5 edit at Δ̂ = 0.00195 is just below 0.002), `openml_qsar_biodeg` (0). Pool = 8, exactly the PLAN target, no margin; two nodes are borderline.
- **Wired in (`main`):** `r1/c3/dataset.py` `E1_SUMMARY` → the common run (newly built C3 tables use its σ_node and δ_n; the 19 Oct pilot table keeps its build-time values, so the pilot gate numbers are unchanged); sweep `D21_NODES`, liveness `DEFAULT_RUN_NODES` and `r1/scripts/configs/c3_sweep_ada.json` → the eight nodes (`nodes_pending` emptied); `e1b_collect` now defaults to this run. Tests: 296 passed (tests pinned to the 12 Oct E1 now name it explicitly; a new test checks the default source).
- **Sweep size:** 8 nodes × 18 instances × 2 memory modes × W = 20 (was 5 nodes in the config) — about 5,800 manager proposals before liveness exclusions.

## 22 October 2026 — author adopts the D21 rule (30 seeds) and the pool extension

Recorded by an AI agent (Claude, coordinating session). No experiment ran. PLAN §10 rows "D21 rule", "D21 uniform application", "D21 pool" and "D21 common measurement" (22 Oct): 30 seeds for every node; ≥ 2 material edits with mean P(wrong) ≥ 0.10; bootstrap reported, not decisive; applied to all nodes including the original five; `credit_approval` added, `diabetes` dropped; candidates `credit_g`, `sonar`, `blood_transfusion`, `qsar_biodeg` (OpenML IDs verified). Next: build the three new harness nodes (subagent), author fetches four data caches on the Mac, then one 30-seed run over ten nodes.

## 22 October 2026 — C3 preparation batch and 30-seed noise re-measurement (accepted, merged)

AI-assisted: two Claude subagents in separate worktrees; reviewed, corrected and merged by the coordinating session (Claude). No LLM, Ollama, GPU or SSH. Merges `06f5faa` (code, ENGINEERING_ONLY) and `554ba3e` (noise, PILOT) on `main`. Tests: 290 passed (baseline 248), 1 deselected (known environmental dry-run test).
- **Gate at the declared g only.** `offline_eval` computes g ∈ {0.1 (primary), 0.05, 0.2} σ_node; `gate_verdict` is the only verdict (g = 0.1, primary run accounting, instance split). On the 19 Oct pilot it reproduces the old 0.1σ values exactly: digits +0.0051 [0.0018, 0.0086], tabular +0.0016 [−0.0008, 0.0037], breast-w −0.0006 → fail. Not a gate decision (tiny pilot).
- **Run accounting.** Primary as decided. Freed-run sensitivity: the subagent's uncapped variant scaled with 1/exec-rate (digits +0.039); replaced at acceptance by an LLM-call cap c × W (c = 1 = primary; c = 2 reported: digits +0.0103 [0.0037, 0.0172], tabular +0.0033 [−0.0017, 0.0073], breast-w −0.0012; c = ∞ upper bound). PLAN row wording corrected (literal replay impossible: one proposal per run in root ledgers).
- **C1 duplicate rate** (`r1/c3/duplicate_report.py`; `reports/DUPLICATE_RATE_PILOT_20261022.md`, PILOT): 841/1,323 rule-detectable; memory-on duplicates 51–66 % (9.7–12.5 wasted runs per 20); DT4 digits memory-off 77 %; all 114 no-ops are inactive-key edits on ionosphere.
- **DI audited mode** (`di_test.py --immediate audited`): default outputs byte-identical. PILOT: memory-on tabular residual −0.00122 → +0.00004 [−0.00120, 0.00093] with audits (13/13 points); memory-off digits +0.00051 → −0.00003. Both undetermined; audit noise is not in the CI.
- **Audits K = 10** (7001–7010, 5 label + 5 evaluation); K = 6 pilot audits still split 3 + 3.
- **Paper A coordination** (`r1/scripts/paper_a_status.py`): refuses unless evidence shows Paper A running on its card or finished; its Ada config has null entries that must be verified read-only on Ada first (handoff lists 7 checks).
- **Sweep config** `r1/scripts/configs/c3_sweep_ada.json`: 5 D21 nodes, 18 instances × W = 20 × both memory modes, own Ollama port 11481, K = 10; `--check-config` passes; desktop DRYRUN passed (`results/r1/engineering/c3_sweep_dryrun_20261022T103215Z/`). Ionosphere kept (passed D28 on 14 Oct; the 19 Oct exclusion concerns only the DI-test pool). A node that fails D28 is dropped from both memory modes; for digits the memory-off choice stays with the author.
- **Acceptance fix:** the C3 pipeline did not know `openml_wdbc` or `openml_credit_approval`; added, with the D25 projection read per node (imputer active on credit-approval) and checked against the harness configs; original node codes unchanged (rebuilt pilot table byte-identical).
- **Noise re-measurement** (`results/r1/pilot/E1_remeasure_20261022T100942Z/`, `reports/NOISE_REMEASURE_20261022.md`, PILOT): 1,104 runs, 0 failures, 300 s. Under E1's (still unadopted) D21 rule, `credit_approval` qualifies (mean P(wrong) 0.09 → 0.24; bootstrap 0.87); `diabetes` has no material edit (bootstrap 0.03). δ_n = 0.002 (floor) on both. Tree-model metrics differ from E1 under scikit-learn 1.9.1; logistic regression reproduces bit-for-bit. Acceptance fix: the comparison script wrote temporary paths; now byte-reproducible.
- **Post-merge fix (`4ae3b8a`):** `e1b_collect`'s default E1 glob also matched `E1_remeasure_*` (two nodes only), so `digits_mlp` lost its noise entry and 3 tests failed on `main`; it now matches full `E1_<timestamp>` runs only. After the fix: 290 passed on `main`.
- **Open for the author:** (1) add `credit_approval` to D21, drop `diabetes`; (2) pool is 6 of ≥ 8 — fetch `credit_g` on a networked machine and choose 2–3 further OpenML datasets; (3) re-measure the five D21 nodes at 30 seeds for a common footing (~15 CPU-min); (4) adopt or amend E1's D21 threshold (mean P(wrong) ≥ 0.10 over ≥ 2 material edits).
- **Still to do before the Ada sweep:** adapter from the sweep index to `dataset.build`; read-only Ada checks (Paper A config, seeded models path, port); `digits_mlp` repair and D28.

## 22 October 2026 — author decisions before the first C3 label sweep

Recorded by an AI agent (Claude, coordinating session). No experiment ran. All rows are in PLAN §10, dated 22 Oct.
- **Duplicates (option A):** confirms the 19 Oct duplicate ≠ no-op split; duplicates are excluded from learned-arm training and evaluation; new: C1 reports the duplicate rate as wasted runs.
- **g (option A):** g = 0.1 σ_node primary, {0.05, 0.2} σ_node declared sensitivity; the gate is judged at the primary value only. C3_DESIGN §1 updated.
- **Run accounting (option A):** skips credited at g; freed runs not re-spent in the primary analysis; replay as sensitivity.
- **Node pool:** credit_approval and diabetes after a 30-seed `"vary"` re-measurement; credit_g after fetching its cache; 2–3 more OpenML datasets if fewer than 8 qualify.
- **`digits_mlp`:** repair, do not exclude; out of memory-on collection until D28 passes.
- **Next:** implementation batch (classification of kinds through labels and arms, g and run accounting in the gate, audited-outcome mode for `di_test.py`, Paper A status command, sweep config) and the noise re-measurement, run by subagents and accepted by the coordinating session.

## 19 Oct 2026 — partial memory-on absolute-metric DI diagnostic

AI-assisted by Codex. **PILOT, PARTIAL, not evidence.** The authorised preserved arm snapshot is 11.99 MB, with lossless compressed ledgers and source SHA-256 manifests; two whole failed points are excluded. No experiment was resumed and no LLM, GPU or worker was run. Memory-on tabular has nine promotion points and four demotion points; its next-one absolute-metric contrast passes the combined diagnostic rule and the value residual is −0.00122155 [−0.00222152, −0.000257005]. Verdict: **violated in value terms**, limited to this exploratory partial diagnostic. Memory-off absolute-metric re-analysis: **undetermined at this sample size**, residual .000510569 [−.00258821, .00417810]. The shared ionosphere node has no changed points in either dataset. These results do not justify A7 training/deployment. See [report](reports/DI_TEST_MEMORY_ON_PARTIAL_20261019.md) and [tables](reports/DI_TEST_MEMORY_ON_PARTIAL_20261019_tables.md). The default legacy outputs remain byte-identical; focused file-only regression suite: 12 passed.

Newest entry first. Only this file says what is done.

## 19 Oct 2026 — rerun-2 diagnosis, digits liveness, and E1b DI diagnostic

AI-assisted by Codex; ENGINEERING_ONLY / PILOT; not evidence. Author-authorized file-only diagnosis in the fresh Ada clone, incorporating addendum `bf52f5c` and the later observed-record/revised-stop-rule instructions. No LLM, GPU, worker runs, retries or writes to preserved results.

- **Task 1 (ENGINEERING_ONLY):** all seven collection-failure leaves coincide with Ollama runner SIGTERM during proposal requests (five runner-unavailable errors, two unexpected EOFs). Signal sender/reason is not recorded. Failures occurred in branches, but shared-service loss can also affect root-only C3. Proposed lifetime/observability fixes and a mocked desktop fixture only; no fix implemented. Report: `reports/RERUN2_STOP_DIAGNOSIS_20261019.md`.
- **Task 2 (ENGINEERING_ONLY):** digits memory-on has no keep after trial 1; 10 later ties and 8 worse scores, with repeated edits. Keep the node as a candidate with proposer/liveness repair; retain its exclusion from memory-on collection until it passes the existing D28 gate. A lucky-incumbent or causal memory explanation is not identified. Same report, “digits_mlp liveness”.
- **Task 3 (PILOT):** observed decision changes are 12 promotions at six digits points, zero demotions; digits has 24 unchanged point-repetitions, ionosphere 36 unchanged. The next-three mean-delta distance exceeds paired null by 0.00495217 (95% cluster interval [0.00123811, 0.00968352]) and unchanged by 0.00607417 ([0.00227162, 0.0107627]); adjusted exploratory p=0.0006. The requested empirical DI criterion flags a memory-off deviation; conditional-law identification and A7 benefit remain undetermined. Ionosphere is excluded from the eligible pool. No scripted per-trial control exists; none was regenerated. Reports: `reports/DI_TEST_E1B_20261019.md`, `reports/DI_TEST_E1B_20261019_tables.md`.
- Deterministic committed-input CLI: `r1/diagnostics/di_test.py`; synthetic/integrity tests: `r1/tests/test_di_test.py` (5 passed). Full r1 suite not run: harness unavailable in the isolated analysis environment. Diagnostic artifacts remain ENGINEERING_ONLY / PILOT, not scientific acceptance, deployment approval or authorization for the proposed memory-on follow-up.







## 19 October 2026 — duplicate ≠ no-op split implemented

Recorded by an AI agent (Claude, coordinating session), at the author's decision (PLAN §10, 19 Oct). ENGINEERING_ONLY.
- **Theory:** T4 §1 now has separate no-op (I_n) and duplicate (D_n) events. Corollary 8a is revised, with a new part (iii): under ρ a duplicate can never be kept, because the record is monotone.
- **Code:** `r1/c3/` gains `noop`, `duplicate`, `rule_skip` and `known_metric` (`inert` remains the alias of `noop`). Duplicates are excluded from training and skipped by the rule layer. Offline evaluation charges an A1/A0 keep of a duplicate its audited Δ or the logged proxy, and counts such keeps. C3 tests: 39 passed, including a new duplicate test.
- **Pilot re-check** (`results/r1/engineering/c3_split_recheck_20261019/`; table rebuilt from the same ledgers, same audits).
  - 1,323 proposals: 727 duplicates, 114 no-ops, 482 other.
  - The maximum Δ̂ over the duplicates is exactly 0, as Corollary 8a(iii) predicts.
  - The gate quantity is unchanged in substance (not passed). At g = 0.1σ: digits +0.0051 [0.0018, 0.0086]; tabular +0.0016 [−0.0008, 0.0037]; breast-w −0.0006.
  - A1 (no rule layer) keeps up to 92 duplicates at g = 0, because a positive constant prior gives t* < 0. This is the failure the rule layer prevents.

## 19 October 2026 — overnight build merged (ENGINEERING_ONLY)

AI-assisted: four Claude subagents worked overnight, coordinated and merged by the coordinating session (Claude). Each worked in its own git worktree; the merges are `86380c2`, `e249a0f`, `d59d77b` and `3c84170` on `main`, and harness `r1` was fast-forwarded to `4d68c54`. No LLM, GPU, SSH or Ollama was used; workers ran on CPU only. Nothing here is evidence. After merging, the new C3/T5/DI/runner tests pass on `main` (113, with Python 3.13 in the VM).
- **C3 offline pipeline** (`r1/c3/`; handoff `docs/r1/overnight/C3_OFFLINE_HANDOFF.md`; report `docs/r1/reports/C3_OFFLINE_PILOT_20261019.md`).
  - Built: T4 rules; 12-bin soft labels; features with ledger replay; CPU audits; arms A1–A3; offline one-step evaluation; the C3 gate.
  - Pilot: 166 proposals audited (672 runs, 0 failures; ≈ 4.7 run-seconds per proposal).
  - Gate quantity on this tiny sample: not passed. Digits passes but has only 6 instances; tabular +0.0021 [−0.0002, 0.0040]; breast-w ≈ 0. Sharing audit seeds between labels and evaluation makes the gate pass spuriously, so separate seeds are required.
- **T5 simulation** (`docs/r1/theory/T5_SIMULATION.md`; `results/r1/engineering/T5_20261019T004918Z/`).
  - Propositions 7–9 are confirmed in the model (Proposition 7 realised/predicted ratio 0.98–1.02 under DI). Under DI, myopic acceptance is never beaten; under the modelled violations it loses ≤ 0.54 δ_n.
  - Only audited increments over each branch's own incumbent are a clean DI outcome.
  - C3 headroom in the model: memory-on oracle 1.35–2.4 δ_n; a calibrated predictor keeps 0.76–1.06 δ_n; an uncalibrated one is worse than the constant prior.
  - The sign of route D depends on whether the suppressed bold edits are good: it must be measured.
- **DI verdict revised:** the memory-on "violated in value terms" is withdrawn as proxy selection bias (addendum to `DI_TEST_MEMORY_ON_PARTIAL_20261019.md`). Both memory modes are undetermined.
- **Novelty full text** (`docs/r1/inputs/NOVELTY_FULLTEXT_20261019.md`): no threat to the core. Pre-execution skipping and re-proposal of rejected candidates are published, so those claims are narrowed (C3_DESIGN §10). Quotes were read via a summarising fetch tool and a mirror; check each against the PDF before the manuscript.
- **Harness and runner** (`docs/r1/overnight/HARNESS_AND_RUNNER_HANDOFF.md`).
  - Harness: D4 action versions (Bayes keep rule, posterior-mean verify, `verify_failed` keeps the original decision); `"vary"` default for new manifests; bounded transport retry. All are backward-compatible: legacy records are identical when the options are unset.
  - Paper: collector observability; dedicated Ollama instance per batch; the C3 label-sweep runner with a Paper A coordination gate (refuses unless Paper A is not waiting for a card); a desktop dry run with fault injection (retry and permanent-loss scenarios passed).
  - Tests: harness 421 passed, 10 pre-existing environmental failures; paper 193 passed, 1 pre-existing failure.
- **Open:**
  1. Author decision: duplicates of earlier non-incumbent configurations are not zero-increment (727 of 841 rule-inert proposals). The inert ⇒ Δ = 0 wording in T4 §1, the labels and the A0/A1 value levels must distinguish "duplicate (known result)" from "inactive edit (Δ = 0)".
  2. Declare g before the gate.
  3. Model the runs freed by skipping in the 20-run scaling.
  4. Add an audited-outcome mode to `di_test.py`.
  5. Before an Ada C3 sweep: write the real Paper A status command and the sweep config (pinned models dir, nodes, GPU); make sure the OpenML data caches exist in the batch harness; repair and re-check `digits_mlp` (D28). The SIGTERM source is still unknown.

## 19 October 2026 — DI review; memory-on partial-arm diagnostic authorised

Recorded by an AI agent (Claude, coordinating session).
- **Review of `DI_TEST_E1B_20261019` (Codex, `7b81e1c`).** The flagged memory-off contrast in next-3 mean Δ̂ (+0.0047 at the 12 changed point-repetitions, all promotions) is mainly a record-reference shift: the verify branch's record is 0.0051 lower after a promotion. In absolute metric the signed shift is +0.0016. Addendum and `r1/diagnostics/di_record_shift.py` committed in `1840efe`. Verdict: undetermined, not "violated".
- **Rerun-2 stop (Codex diagnosis):** the shared Ollama runner received SIGTERM (source unknown); 7 of 648 arm-A leaves failed. It can also affect root-only C3 sweeps. Proposed fixes before the C3 label sweep: a dedicated Ollama instance per batch (own port and model dir); bounded retries for transport-level LLM request failures, logged in the ledger; tracebacks and timestamps persisted by the collector.
- **`digits_mlp`:** keep conditionally; repair the proposer and re-run D28 before use.
- **Author rule (PLAN §10, R1-COMPUTE Paper A coordination):** no Paper B GPU launch on Ada while a Paper A live campaign there is waiting for an idle card. CPU-only and file-only work is unaffected; otherwise wait or use Deepthought.
- **Author authorisation (PLAN §10, 19 Oct):** snapshot and analyse the preserved partial arm A (memory on) as a PILOT DI diagnostic, using absolute metrics and a value-residual check. Prompt `docs/r1/prompts/ADA_DI_TEST_MEMORY_ON_PARTIAL_PROMPT.md`.

## 18 October 2026 — add-on placement: B joins C2, D becomes C4

Recorded by an AI agent (Claude, coordinating session). The author agreed that route B (the T4 theory of the gain) is part of C2, with its empirical checks reported alongside C3, and that route D becomes **C4 (secondary): proposer feedback** — the DI test on forced-decision branch pairs plus the debiased-memory A/B. PLAN §3 (current-contributions box) and §10 (R1-C4), `C3_DESIGN.md` §7 and the README were updated. No experiment ran.

## 18 October 2026 — author adopts the open Phase 0 decisions, the C3 ladder and the C3 gate

Recorded by an AI agent (Claude, coordinating session). The author adopted every recommendation put to them on 18 Oct (D4 amendment allowed; D21 node set plus pool extension to ≥ 8 nodes; `"vary"` split on every node; D18 δ_n; D23 constant-prior KG index policy as arm A1; R1-E1B-RERUN2 converted into the C3 label sweep), and fixed C3 as route A with the A0–A6 ladder and the C3 gate. All are PLAN §10 rows dated 18 Oct. No experiment ran.

- **Next actions:**
  1. read the rerun-2 collection-failure cause on Ada;
  2. implement the D4 action versions (Bayes threshold; posterior-mean verify response; `verify_failed` keeps the original decision) and the `"vary"` default on the harness branch `r1`;
  3. build the audit pipeline and the C3 label sweep;
  4. run the DI test on the existing E1b LLM branch pairs;
  5. extend the node pool (D21);
  6. diagnose `digits_mlp` liveness.

## 18 October 2026 — C3 route adopted; legacy code archived; T4 theory and C3 design drafted (ENGINEERING_ONLY)

AI-assisted by Claude (coordinating session) at the author's request. Nothing here is evidence. Uncommitted working-tree changes on the author's Mac; no commit or push was made.

- **Author decision R1-C3** recorded in PLAN §10: C3 is the learned per-proposal prior under the C2 rule. Design proposal `docs/r1/C3_DESIGN.md`.
- **RUNBOOK 0.1 legacy code:** moved with `git mv` to `archive/old_b_2026-10-09/code/` (list in PLAN §10). `r1/` imports none of it (checked by grep). Legacy suites before the move, from the root: 212 / 6 / 12 OK; after the move, via `make legacy-test`: 212 / 6 / 12 OK. Both runs used Python 3.13.15 in a scratch uv venv with `requirements.lock`, because the Mac's `.venv` is not usable from the Linux shell. The root `Makefile`, `README.md`, `pyproject.toml` (testpaths → `r1/tests`) and `.gitignore` paths were updated; `archive/old_b_2026-10-09/code/Makefile` keeps the test targets. The old `paper-b`, `smoke-b`, `release-b` and `check-release-b` targets were not carried over. `make r1-test` was not run: the harness checkout is not reachable from this session.
- **Theory T4** (`theory/T4_FEEDBACK_PROPOSER.md`, Propositions 6–10): per-proposal Bayes rule under a ledger-dependent proposer; exact gain of a per-proposal over a constant prior; screening under a run price; winner's curse for every adaptive proposer; decision independence ⇒ myopic optimality, with a counterexample. The closed forms of Propositions 7 and 9 were checked against Monte Carlo (agreement to MC error). The proofs are unchecked by the author.
- **Offline premise check for C3** (ENGINEERING_ONLY; script on the Mac VM at `~/scratch/offline_a.py`, not committed):
  - 39–77 % of LLM trials repeat an evaluated configuration; 9–14 % are bit-identical to the incumbent;
  - informative increments differ by edit type (`digits_mlp` `BATCH_SIZE` −0.012, n = 94; `HIDDEN_UNITS` +0.004, n = 181);
  - with memory on, 24 % of informative proposals improve.

  Small samples; single-campaign Δ̂.
- **Novelty sweep part 2** (`inputs/NOVELTY_SWEEP_PART2_20261018.md`, AI-assisted, abstract-level): no work combines an LLM proposer, noisy incumbent-relative acceptance and a learned per-proposal prior. The nearest 2026 works are SAGE (2609.36043), FOREAGENT (2601.05930) and Beneath the Diff (2609.00077). C2-i (Bayes threshold) and C2-ii/v (verify VoI) are classical and are to be presented as instantiations. C3_DESIGN §10 was revised accordingly.
- **Still open:** D18, D21, D23, the D4 amendment, the verify split policy, the C3 gate, and whether to re-run or redesign R1-E1B-RERUN2 (stopped 14 Oct on collection failures; cause not yet read from the Ada logs).

## 14 October 2026 — R1-E1B-RERUN2 (PILOT): stopped

AI-assisted execution by Codex (AI-assisted). All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/`.
- **Harness:** `411c6054c8505f93a6429e2f9eed526952793882`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `2, GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154, NVIDIA RTX 6000 Ada Generation, 48427`; `{"full_offload": true, "host": "ucrtasl", "keep_alive": -1, "probe_tokens_max": 1, "size": 5560907776, "size_vram": 5560907776}`.

- **preconditions:** `{"completed": true, "completed_utc": "20261014T140742Z", "started_utc": "20261014T140727Z"}`
- **liveness:** `{"commit": "b2e5cc3ce5570e9a0da9cec67f5da8b9c4795ab6", "completed": true, "completed_utc": "20261014T141051Z", "eligible_nodes": ["tabular_mlp", "openml_ionosphere", "openml_breast_w"], "excluded_nodes": ["digits_mlp"], "out": "/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/agent_paper_B/results/r1/engineering/liveness_llm_20261014T140742Z", "started_utc": "20261014T140742Z", "verdicts": {"digits_mlp": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 12, "novelty_source": "events", "observed": 0.6, "required": ">= 0.5", "seen_before_trials": 8}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 0, "required": "at least 1 keep with budget_index > 1"}}, "openml_breast_w": {"active_novelty_fraction": {"equals_incumbent_trials": 1, "evaluated_trials": 20, "novel_trials": 13, "novelty_source": "events", "observed": 0.65, "required": ">= 0.5", "seen_before_trials": 7}, "invalid_rate": {"observed": 0.05, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 1, "required": "at least 1 keep with budget_index > 1"}}, "openml_ionosphere": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 11, "novelty_source": "events", "observed": 0.55, "required": ">= 0.5", "seen_before_trials": 9}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 3, "required": "at least 1 keep with budget_index > 1"}}, "tabular_mlp": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 12, "novelty_source": "events", "observed": 0.6, "required": ">= 0.5", "seen_before_trials": 8}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 3, "required": "at least 1 keep with budget_index > 1"}}}}`
- **arm_A:** `{"completed": false, "started_utc": "20261014T141051Z"}`

**STOP:** RuntimeError: STOP: collection failures; no leaf retries permitted

E1b rerun-2 phases are accepted only where the phase entry explicitly records completion. Partial outputs are preserved; no completed phase was re-run and no interrupted phase was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 14 October 2026 — batch 4c: launch repairs and real-runner desktop dry run (DRYRUN; review resolved)

AI-assisted implementation by Codex at the author's explicit request, including approval to execute the complete `BUILD_BATCH4C_PROMPT.md` and then start a fresh Ada batch. Production design, PLAN rows and harness pin remain unchanged. Base: paper `42f454c` (coordination documents; prior launch base `69b2bbd`); harness `411c6054c8505f93a6429e2f9eed526952793882`. Implementation/tests/evidence commit: `bb7a12c02717566ebe8338287f9f9b55afe97beb`, pushed. Independent review and its single correction round are complete; the new Ada batch has not yet been started.

- **X1:** The runner reads and validates `R1_OLLAMA_MODELS` before touching a GPU or starting a server; no missing directory or unset variable proceeds. A compiled merged-module global-name guard mirrors the exec loader and detects `MODELS` in the original `69b2bbd` sources and an injected missing global.
- **X2/X3/X5:** The launcher requires `R1_GIT_NAME` and `R1_GIT_EMAIL`, configures both fresh clones repository-locally, validates `GIT_COMMITTER_IDENT`, checks both branch pushes with `--dry-run`, installs `uv sync --extra dev`, records the pytest version and identity/setup checks in `prepare.json`, and rechecks identity/push permission at `--start`. It prints a self-check summary. It discovers Ada's already-installed `uv` in the prior batch toolchain when SSH PATH omits it; no manual package install is needed.
- **X4:** `rerun2_dryrun.py` launches the real launcher and real runner with a fake Ollama HTTP server, fake GPU census including a co-tenant, actual CPU workers, real fresh Git clones, real commits/pushes to temporary bare remotes, and an isolated tmux socket. DRYRUN requires `R1_DRYRUN=1`, a marked temporary root and local temporary remotes; it is refused on Ada and cannot push to `origin` in DRYRUN mode. The harness remains untouched.
- **Fail-before/pass-after:** Baseline paper tests: 144 passed. Five targeted regressions fail at `69b2bbd`; the before-fixes real entrypoint fixture stops on `MODELS` before inference (`results/r1/engineering/rerun2_dryrun_20261014T131354Z/`). Pre-review full `make r1-test`: **153 passed in 351.20 s**; final post-correction full suite: **158 passed in 399.89 s**; final nested clone suite: **157 passed, 1 skipped** (only recursive integration suppressed). Legacy suites with the harness interpreter: **212 / 6 / 12 passed**. Raw logs, including intermediate fixture failures and the initial wrong-interpreter legacy check, are preserved in `results/r1/engineering/batch4c_test_logs_20261014/`.
- **Passing end-to-end fixture:** `results/r1/engineering/rerun2_dryrun_20261014T135521Z/summary.json`, **DRYRUN**, elapsed **348.14 s** (pre-review passing fixture `...133616Z`, 319.61 s, also preserved). Preconditions, liveness, A, B, C, comparison and STATUS all completed. Six generated commits are present in the local bare remote; each arm's committed/regenerated analysis hashes match; fake chat calls carry integer D26 seeds; D25 inactive-key rejection occurred; restarting the completed batch refuses. No real model or GPU was used on the Mac.
- **Fixture deviations required by unchanged code:** two instances per node instead of one (`evaluate_arms` requires at least two for cross-fitting); W=6 rather than W=4, with E2 at 2 (`point_features` requires remaining budget `2*r=4` for verify). Two nodes (`digits_mlp`, `openml_breast_w`), one repetition, one audit seed. Liveness uses one instance and four worker runs only in guarded DRYRUN. An isolated loopback port replaces 11434 because the Mac's existing service already occupies 11434. Production stays at four prescribed nodes, 18 instances, W=20, E2 4/8/12, r=2, two repetitions and six audit seeds; production port remains 11434.
- **Unexercised production paths:** real Ollama inference/model files, real GPU offload/OOM/free-memory loss and wait-for-card, the two other production nodes, full scale/latency, real GitHub transport/authentication or non-fast-forward recovery, interrupted-phase recovery and long-duration monitor intervention. The one-repetition fixture cannot exercise leaf-split headroom; that calculation retains its existing unit coverage. Engineering checks do not establish node eligibility or scientific conclusions for the future Ada run.
- **Preservation:** Old Ada batch `..._20261014_nH08fo` was not resumed. Its STOP logs/state/census/env and staged STATUS patch were copied with a SHA-256 manifest into `stop_20261014T104505Z_preserved/`; the author's directly authorized repository-local Git identity repair was applied there, but its staged STOP entry was not committed or pushed. A fresh batch is required after this build/review.
- **Ada test portability:** Before fresh preparation, desktop integration was explicitly excluded on physical Ada (DRYRUN must be refused there), and pure guard fixtures were made host-independent. Simulated Ada test module: **13 passed, 1 skipped**; complete nonrecursive unit suite: **157 passed, 1 skipped**. Only tests changed; actual Ada preparation remains the host-specific gate.
- **Independent review:** `docs/r1/reviews/BUILD_REVIEW_20261014c.md` plus Resolution. One MAJOR (separate push URLs could bypass the local-only DRYRUN boundary) and two MINOR findings (module/class global-name coverage; direct liveness CLI output/work containment) were fixed in one correction round with negative regressions. No open MAJOR remains. Final full suite and DRYRUN passed after correction. Ada launch is the next authorized action; engineering success does not establish real-node eligibility.

## 14 October 2026 — rerun-2 first launch stopped before any inference (engineering defects)

Reported by the Ada operator agent (AI-assisted); recorded here by an AI agent (Claude, coordinating session). Not evidence; no experiment ran.

- Batch `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_nH08fo/` on Ada.
  - `--prepare` passed its classification only after the operator installed `pytest` into the batch venv by hand: the launcher runs `uv sync` without `--extra dev`.
  - `r1-test`: 144 passed. Every harness failure was in the accepted set.
- **STOP** at `r1/scripts/ada_e1b_rerun2.py:156`: `NameError` on `MODELS`. The runner never reads `R1_OLLAMA_MODELS`, although `env.sh` exports it. In DT4 this name was defined inside `ada_rerun_dt4.py`, not in the shared helpers.
- `finish()` then could not commit its STATUS entry because the fresh Ada clone has no git author identity. The entry stays staged in that clone and was not pushed. This is the same gap the DT4 recovery hit (repository-local identity), and it was never added to the launcher.
- No Ollama server, liveness check or arm ran. Our tmux sessions are gone and the port is free. The batch directory stays as evidence; it is not resumed.
- Systemic cause: this is the third Ada stop caused by runner paths that the desktop stub tests did not execute (DT4 tables whitespace, `MODELS`, git identity). Fix batch: `docs/r1/prompts/BUILD_BATCH4C_PROMPT.md`, which adds an end-to-end desktop dry run of the real runner against a fake Ollama and a fake `nvidia-smi`. `ADA_E1B_RERUN2_PROMPT.md` is updated (git identity passed in; no manual environment changes on Ada).

## 14 October 2026 — batch 4b: second Ada accepted-failure ID in the rerun-2 launcher (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) per `docs/r1/prompts/BUILD_BATCH4B_PROMPT.md`; no LLM calls, no GPU, no Ada. Commit: paper `75d6911` → `f7879db` (branch `main`). One change: the rerun-2 launcher's accepted-failure set gains exactly `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` (PLAN §10, row R1-COMPUTE (Ada environmental test exception 2)), beside the missing-`/bin/zsh` exception of 12 Oct. The launcher's Ada-only host guard scopes the set as before; every other failure still refuses `--start`, and no pattern/file/class matching was added. The harness is untouched, so `HARNESS_PIN_RERUN2` stays `411c6054c8505f93a6429e2f9eed526952793882`.

- **Tests.** Paper `r1/tests`: 141 → **144 passed**; `make test` 212 / 6 / 12 OK before and after. Fail-before: `test_ada_exceptions_are_accepted_and_start_proceeds` fails at head `7272d77` (`prepare.json.ok=False`); the patch makes it pass.
- **The four stub tests (all pass).** (a) `test_ada_exceptions_are_accepted_and_start_proceeds` — the zsh and fresh-checkout tests classified environmental on Ada, so `--prepare` records no unexpected failure and `--start` proceeds; (b) `test_ada_exceptions_are_refused_off_ada` — the same prepare.json off `ucrtasl` is refused; (c) `test_a_third_test_in_the_same_file_is_still_refused` — a sibling in the same `TestCompletenessCLI` class is refused; (d) `test_prepare_refuses_a_nonzero_exit_without_parsed_failures` — the F8 behaviour is kept.
- **Next:** `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md` is ready to hand over; it can be run unchanged.

## 14 October 2026 — author approves a second Ada test exception before rerun-2

Planning only; recorded by an AI agent (Claude) at the author's request.

- Batch-4 review findings F7–F11 are already fixed (review Resolution). The one item still worth fixing before Ada is the launcher's accepted-failure set. The 12 Oct Ada DT0 run failed `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` on a fresh checkout (it passes on the Mac), so `--start` would refuse.
- **Adopted** (PLAN §10): accept exactly that test ID as environmental on Ada, together with the missing-`/bin/zsh` exception. Patch prompt: `docs/r1/prompts/BUILD_BATCH4B_PROMPT.md`. Afterwards, `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md` is handed over unchanged.

## 14 October 2026 — batch 4: D27 F3 fix, D28 revised criterion 2, R1-E1B-RERUN2 entrypoints (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) at the author's request per `docs/r1/prompts/BUILD_BATCH4_PROMPT.md`; no LLM calls, no GPU, no Ada batch created or launched. Commits: paper `5f650be` → `a8956ca` (branch `main`; P6 `271fc16`, P7 `9dd245c`, correction round `0cb76a3`, review `a8956ca`); harness `0f2d9e9` → `411c605` (branch `r1`; H6 `ed55297`, correction `411c605`). Independent fresh-context review: `docs/r1/reviews/BUILD_REVIEW_20261014b.md` (+ Resolution). `r1/scripts/HARNESS_PIN_RERUN2` = `411c6054c8505f93a6429e2f9eed526952793882`, on `origin/r1`.

- **Tests.** Harness: 380 passed / 8 failed / 1 error before → **389 passed / the same 8 failed / 1 error** after (the 9 IDs are the known environmental set; the launcher classifies exactly these plus the Ada `/bin/zsh` exception). Paper `r1/tests`: 109 → **141 passed**; `make test` 212 / 6 / 12 OK before and after. Fail-before shown in both repos: the new paper tests at base `5f650be` gave 5 failed / 3 collection errors, and at harness `0f2d9e9` the F3 scenario printed `config_seen_before: false` and the new D27 tests could not import the corrected helpers.
- **D27 (F3 fix).** `edit_novelty` gains `effective_config_sha256`, `active_config_sha256` (active-key projection; equal to the full configuration on undeclared nodes), `active_config_equals_incumbent` and `active_config_seen_before`. E2 snapshots store the full and active seen-hash sets at capture time and `resume_campaign` seeds them; an old-format snapshot resumes with `seen_before_resume: "unknown"` recorded on the first `edit_novelty` event, never a silent empty set. `TrialRecord` bytes unchanged (existing record test; review re-verified base-vs-head byte identity). The reviewer's lr_synthetic reproduction now yields `config_seen_before: true` and fails at `0f2d9e9`. Correction round: the configuration now covers **every editable symbol**, not only the narrow `build_effective_config` map (review F7); `HIDDEN_UNITS`/`ALPHA`/`LEARNING_RATE_INIT` edits on the MLP nodes are visible to the flags and hashes, and the E1-snapshot resume counts the replayed captured trial among the seen configurations (review F9).
- **D28 (revised criterion 2).** Criterion 2 is active-key novelty over evaluated trials (skipped trials, including `inactive_key` skips, are excluded; inactive-key rejections are a separate count); legacy ledgers without events are scored by replaying structured edits from the node's start configuration, projected with the node's current declaration; the report states `novelty_source: events | replayed`. The gate accepts only LLM-backed, memory-on liveness manifests; a memory-off `contrast` collection reuses the memory-on verdict and cannot bypass the gate with a scripted or memory-off manifest. The collector now persists root event streams (and the liveness runner archives them), so new runs are scored from events. **Offline DT4:** `openml_ionosphere` FAIL on criteria 1 and 2 (0 keeps after trial 1; novelty 0/120; invalid 0.0); `digits_mlp` FAIL on novelty only (32/120 novel; 11 keeps after trial 1; invalid 0.0), pinned after a raw-constants independent recomputation. **Scripted smoke** on the corrected harness, `results/r1/engineering/liveness_scripted_20261014T084101Z/` (ledgers force-added): digits_mlp PASS 20/20, tabular_mlp PASS 20/20, openml_breast_w PASS 19/20, openml_ionosphere PASS 18/20, **openml_wdbc PASS 19/20 (the old metric-difference criterion scored it FAIL at 7/18)**. The pre-correction smoke `...075806Z` is kept as the F7 evidence.
- **R1-E1B-RERUN2 entrypoints (built and tested, not run).** `r1/scripts/ada_e1b_rerun2.py`: six phases checkpointed in `batch_state.json` — preconditions (PLAN rows, both checkouts at origin heads, digest pin, co-tenancy card, `OLLAMA_KEEP_ALIVE=-1`, full offload with telemetry), LLM liveness (memory on, 2 instances, W=10; fewer than 2 eligible nodes is a STOP), arms A/B/C, per-arm analysis/commit/regeneration check, comparison, finish. A completed phase is skipped on restart; an interrupted phase is a STOP for the author and is never retried; a completed batch refuses to re-finish (review F10). Arm A is gated by the memory-on manifest; arm B is the declared memory-off contrast; arm C is scripted and ungated. `ada_e1b_rerun2_launch.sh`: `--prepare` (fresh paper clone at `origin/main`, fresh harness clone at `HARNESS_PIN_RERUN2`, `uv sync`, harness suite + `make r1-test`, `prepare.json` with per-failure acceptance classification incl. the Ada missing-`/bin/zsh` exception; a non-zero exit with no parsed failures is refused, review F8) and `--start` (refuses an existing `r1_e1b_rerun2` or any `r1_ollama_*` session, or unaccepted failures). `e1b_compare.py`: per arm and node/ALL ρ, `always_verify − ρ`, `kg_index − ρ`, `margin_threshold − ρ` with instance-cluster bootstrap CIs, best simple baseline, naive and leaf-split headroom, verify-changes-leaf share, mean verify − continue; the memory effect `(always_verify − ρ)_B − (always_verify − ρ)_A` as a shared-draw paired instance bootstrap; C1 waste counters (active novelty, inactive-key rejections, `config_seen_before` rate, LLM calls, parse failures); PILOT report with a Bonferroni readings template (m per-node memory-effect contrasts stated). Compute estimate printed before running: 72 roots and 864 leaves per arm; ~11,808 expected LLM calls per LLM arm (roots 20 each + branches' mean remaining budget 12).
- **Review.** One MAJOR (F7: novelty dropped real editable constants — `digits_mlp` was wrongly failed at 7/20 and the Ada gate could have excluded a live node) and four MINOR findings (F8 launcher exit codes, F9 E1-resume seen set, F10 finish checkpointing, F11 lexicographic manifest pick); all five fixed in one correction round (harness `411c605`, paper `0cb76a3`). The review re-derived the committed smoke, confirmed byte-identical records, the DT4 regeneration, the gate fail-before and the end-to-end commit check.
- **Deviations / open items.** (1) An untracked stray `uv.lock` at the paper repository root (and an empty partial `.venv`) was moved aside to the session temp directory; all suites ran with the harness venv interpreter and an absolute `AR_HARNESS_ROOT` (`make` does not expand `~`). (2) The launcher's batch-root/binary/pinned-batch/remote paths gained `R1_RERUN2_*` environment overrides (Ada defaults unchanged) so `--prepare`'s classification is testable off Ada. (3) The P6 commit message and the superseded smoke carry the pre-correction digits/tabular numbers; this entry and the review Resolution supersede them. (4) Ada remains unverified locally: if the 12 Oct extra harness failure (`TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns`) still occurs at the pin, `--start` refuses by design and the operator reports. Open author decisions unchanged: the D4 amendment, D18, D21, D23 and the verify split policy.
- **Next:** hand over `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`; it starts `--prepare` from this prompt's entrypoints.

## 14 October 2026 — author decisions after the batch-3 review

Planning only; recorded by an AI agent (Claude) at the author's request. No code and no runs.

- **Adopted** (PLAN §10, 14 Oct, after the batch-3 review): the D27 F3 fix via config hashes in `edit_novelty` and in E2 snapshots (no `TrialRecord` change); D28 criterion 2 revised to active-key novelty, with the memory-off contrast arm exempt from the gate; R1-E1B-RERUN2 (4 nodes, 18 instances, arms A = LLM memory on, B = LLM memory off, C = scripted on the new harness).
- **Not decided**: the D4 amendment (run-free acceptance rules). It is not in the rerun. D18, D21, D23 and the verify split policy are also still open.
- Consequence of the batch-3 F1 fix, recorded here: the scripted proposal sequence is unchanged, but on declared nodes an inert draw is now skipped without a worker run, so the 12 Oct scripted E1b is not byte-reproducible on the new harness. That is why arm C reruns it.
- Next: `docs/r1/prompts/BUILD_BATCH4_PROMPT.md` (desktop: F3, D28 revision, rerun entrypoints), then `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`.

## 14 October 2026 — batch 3: D24–D28 desktop implementation, review and correction (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) at the author's request per `docs/r1/prompts/BUILD_BATCH3_PROMPT.md`; no LLM calls, no GPU, no Ada batch created or launched. Commits: paper `0a3f284` → `e4d31d5` (branch `main`); harness `9c4902d` → `0f2d9e9` (branch `r1`). Independent fresh-context review: `docs/r1/reviews/BUILD_REVIEW_20261014.md` (+ Resolution).

- **Built (harness).** D24 summary fixes (node `metric_name`, a metric of exactly 0.0 is shown, best-strategy respects `metric_direction`, a missing node metric never leaks another parsed metric). D25 node-declared active keys: optional `active_keys` on `NodeSpec` omitted from `to_dict()` when empty (undeclared hashes unchanged), all seven `openml_*` nodes declared (model_type-keyed; `class_weight` omitted under `gradient_boosting`; `imputer` excluded where the committed feature metadata shows no categorical columns), the LLM prompt lists only active keys, a proposal naming an inactive key is rejected before any worker run, revised at most 2 times (`MAX_INACTIVE_KEY_REVISIONS`, each charged to the LLM-call cap), else skipped with reason `inactive_key` (event `proposal_rejected_inactive_key`). D26 deterministic Ollama seed from (campaign, trial index, repetition, revision attempt), passed at model construction and recorded in `llm_call`; temperature stays 0.2. D27 record-only `edit_novelty` event (`config_equals_incumbent`, `config_seen_before`, `metric_identical_to_incumbent`); `TrialRecord` bytes unchanged. Post-review fix: `ManagerStatus` stays unfiltered — the D25 filter applies only to the prompt — so the scripted proposal law is untouched.
- **Built (paper).** `e1b_collect` takes `memory_mode` and the seed policy from the manifest (no literal; absent field = `none` for historical runs); branch continuations inherit the root's mode from the snapshot (verified); `scripted_manager` reads the node declaration (numeric pool = active ∩ allowed_ranges, order preserved) with two goldens generated from pre-change code (direct replay; live `run_real_campaign` path). `noop_skip` E1 controller (skips no-op/duplicate edits; marked as needing E1 branch data for offline scoring). `r1/liveness/`: D28 checker (`--offline`/`--run`, JSON + Markdown per node) and `require_live` gate wired into `deepthought_batch1_resume.collect` before any collector call; the gate accepts only an LLM-backed (`manager_kind: langgraph`) liveness manifest.
- **Tests.** Harness: **349 passed, 8 failed, 1 error** before → **380 passed, same 8 failed, 1 error** after (the failures/error are pre-existing environmental: generated paper assets absent; `harness/claw-code` submodule not initialised). Paper: `r1/tests` **75** → **109 passed**; `make test` **212 / 6 / 12 OK** before and after. Every behaviour change was shown to fail on the base code (harness base + new tests: 5 failed, 2 collection errors; paper base + new tests: 4 failed, 3 collection errors); the review independently re-ran these spot checks.
- **Liveness results.** Offline DT4 ledgers (`results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots`, committed): `openml_ionosphere` **FAILS** (0 keeps after trial 1; 0/114 trials metric-different; invalid 0.0) and `digits_mlp` **PASSES** (11 keeps; 92/114 = 0.807; invalid 0.0) — committed acceptance test. Scripted smoke on the five noise nodes (`results/r1/engineering/liveness_scripted_20261014T072114Z`; 2 instances, W = 10, no branching; re-run on the corrected harness): `openml_wdbc` **FAILS** `metric_diff_fraction` (7/18), `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere` PASS. The scripted verdicts are not the D28 check for LLM collection; the gate rejects `manager_kind != langgraph`, so the Ada LLM liveness run must be performed before LLM-backed collection.
- **Audit headline.** `docs/r1/reports/NODE_KEY_AUDIT_20261014.md`: all 15 registered nodes audited. OpenML declarations match the template code; `imputer` is inert on ionosphere/wdbc/breast_w/diabetes (feature metadata), active on credit_approval; `class_weight` is inert under `gradient_boosting`. Flagged for the author: `imputer` on `openml_bank_marketing`/`openml_credit_g` (no in-repo metadata; declared active), `resnet_trigger` (fast-search env and MPS-cap inert keys, no declaration; not the same mechanism), `autoresearch_linux` (registered config, no node directory).
- **Review summary.** 1 MAJOR + 5 MINOR. Fixed: F1 (MAJOR: D25 filtering in the campaign status silently changed the scripted live proposal sequence for existing seeds; fixed by filtering only the LLM prompt, with a live-campaign golden that fails on the reviewed head `ff61911` and passes on `0f2d9e9`), F2 (unguarded `revision_attempt` kwarg), F5 (scripted smoke not re-derivable; gate could consume a scripted manifest), F6 (Anthropic-backed manager raised). Open: F3 (`config_seen_before` is blind to configs evaluated before a resume; a fix needs a record-level config hash and an author decision), F4 (dry campaigns emit no `edit_novelty`; no workspace to compare — would be vacuous).
- **Deviations.** (1) Environment: system `python3` is 3.14 without pytest/numpy; all suites ran with the harness venv interpreter (`make r1-test ... R1_PY=…`, `make test PYTHON=…`) and `make r1-test` needs an absolute `AR_HARNESS_ROOT` (make does not expand `~`). (2) The harness H2–H4 work is one commit, not three (the changes interleave in `campaign.py`/`langgraph_manager.py`). (3) D26 adds the revision attempt to the seed derivation (per the batch prompt) and skips seeding for providers without a seed API (Anthropic). (4) `edit_novelty` is the documented new event type; `llm_call` payloads additionally carry `seed` (required by D26). No item was fully stopped under rule 3; the two open review findings and the three audit flags are recorded above for the author.
- **Next.** Ready for the Ada step: the LLM liveness check (memory on) on the five noise nodes, then the LLM E1b rerun. The runner gate requires a `manager_kind: langgraph` liveness manifest (produced by `python -m r1.liveness --run --manager langgraph …`).












## 14 October 2026 — author adopted D24–D28 (proposer decisions)

Planning only; recorded by an AI agent (Claude) at the author's request. No code and no runs.

- Finding behind the decisions: memory was switched off by R1's own collector (`r1/headroom/e1b_collect.py`, `run_root`: `memory_mode="none"` as a literal), not by a harness default and not by any PLAN row. Under `none` the LangGraph prompt still prints the AVOIDANCE RULE over a history that does not exist. Details: `docs/r1/reports/PROPOSER_DECISIONS_20261014.md`.
- **Adopted** (PLAN §10, 14 Oct): D24 memory `append_only_summary` (primary; `none` as E1b contrast), D25 node-declared active keys, D26 seeded manager sampling, D27 no-op/duplicate flags plus an E1 skip arm, D28 node liveness check as a runner STOP.
- Next: desktop implementation per `docs/r1/prompts/BUILD_BATCH3_PROMPT.md` with an independent review; then the liveness check and the LLM E1b rerun on Ada (separate prompt).
- Still open: D18, D21, D23, the D4 amendment, the verify split policy, and the trial-1 unconditional-keep item.

## 14 October 2026 — ionosphere LLM diagnosis (read-only, ENGINEERING_ONLY)

AI-assisted diagnosis by opencode (deepseek-v4.1-flash) at the author's request; no LLM calls, no GPU, no worker runs, no code change to harness/manager/prompts/nodes/PLAN/RUNBOOK. PILOT data only; not evidence. No decision recorded.

- **Examined.** LLM run `results/r1/pilot/E1b_20261013T151857Z` (6 ionosphere roots, 72 branches, `provenance/ledgers/`, snapshots, `points.json`); scripted run `results/r1/pilot/E1b_20261012T161034Z`; harness `9c4902d` (node `benchmark.py`, `langgraph_manager.py`, `metric_parser.py`, `decision.py`, `summarizer.py`); Ada `r1_e1b_llm_work/` per-trial `patch.diff`/`run.log` (read-only).
- **Verdict: the working hypothesis is confirmed.** On ionosphere the LLM edits only `n_estimators` and `max_depth`, which `_build_model` ignores under `logistic_regression` (`benchmark.py:225-231`), so the metric is bit-identical to the incumbent on 114/114 root and 720/720 branch trials; the strict keep rule (`delta > 0`) never fires after trial 1. 840 trials, 6 keeps (first valid metric per root), 0 invalid, Δ̂ = 0. The scripted proposer edits only active keys and keeps 18/66 root trials (ρ = +0.0189 vs LLM 0). Decoding is not deterministic (temperature 0.2, no seed): 3/72 branch pairs agree across repetitions.
- **Ruled out:** metric-parsing default, incumbent read error, unapplied edit, cached worker result (see Q6).
- **Report:** `docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md`; reproducible tables `r1/diagnostics/ionosphere_llm_diag.py`. Fix options listed for the author (expose only active keys; annotate active keys; surface "metric unchanged"; set manager temperature/seed; or leave as is). **Decisions remain open.**

## 13 October 2026 — DT4 rerun: commit-only recovery

AI-assisted recovery by Codex, authorized by the author (PLAN §10, R1-COMPUTE DT4 commit-only recovery). PILOT; not evidence.

- Cause of the stop: generated tables ended with a blank line, failing `git diff --cached --check`. The runner stopped before committing anything. Fix: `0a7a8328eb219243ebb205c366a3e68e6b1733f8` (`e1b_analyze.markdown` emits one trailing newline through main; regression `r1/tests/test_e1b_markdown.py`).
- No re-collection or inference. Collection `results/r1/pilot/E1b_20261013T151857Z`: 144 leaves, 12 audits, 1,440 LLM calls, 0 collection and 0 parse failures; wall time 28.3 min; Ada GPU 1 (`GPU-aa340032-6f94-9783-8f3d-50a15da47a6f`), no co-tenants observed, minimum free memory 43,145 MiB; load offload `size_vram = size = 5,560,907,776` bytes.
- Regenerated `analysis.json` is byte-identical to the runner's: sha256 `d0d5979ac2cff458b95865fb27bd3c2ea973f215e59b15ea78a881ac9b84caca`. Tables differ only in trailing newline; report text unchanged. Artifacts committed/pushed `52894f32eacd900b51d53482efa131ac5b3d948e`.
- Committed-data regeneration: match; original, recovered and regenerated sha256 `d0d5979ac2cff458b95865fb27bd3c2ea973f215e59b15ea78a881ac9b84caca`. Record `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/recovery/regeneration.json`.
- Gap: after-collection offload check passed, but telemetry was not saved; logging fixed for future runs in `0a7a832`. No telemetry recreated.
- Stopped-state provenance: `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/recovery/`; runner's stopped STATUS entry retained below.
- Local validation: 75 R1, 212 control, 6 release and 12 standalone tests passed. Installed author-approved `hypothesis==6.112.1` in existing local test venv with dependencies attrs 26.1.0 and sortedcontainers 2.4.0; used that interpreter for make test after system Python lacked dependencies. Fresh Ada clone lacked Git identity; configured repository-local identity from the existing Mac author settings before committing. No rejected push, history rewrite, data change, GPU use or interference with other users.
- E2 decisions remain open. L11 is not built.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Claude (runner) on Ada, started by the author. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/`.
- **Harness:** `9c4902d0d8776f18a081e1ff2478d651fc7096c1`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, NVIDIA RTX 6000 Ada Generation, 48427`; `{"full_offload": true, "host": "ucrtasl", "keep_alive": -1, "probe_tokens_max": 1, "size": 5560907776, "size_vram": 5560907776}`.

- **DT1:** `{"commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`
- **DT2:** `{"commit": "7f8128312f70d8b20e9dd7613c8ee7ba27e73392", "completed": true, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/agent_paper_B/results/r1/engineering/L12_live_20261013T090417Z", "summary": {"accepted": true, "actual_worker_runs": 10, "call_errors": 0, "caps": {"llm_calls": 12, "worker_runs": 10}, "charged_llm_calls": 4, "control_events": 6, "decision_action_distribution": {"continue": 4, "verify": 2}, "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364", "disallowed_actions": 0, "event_llm_calls_sum": 4, "harness": {"branch": "r1", "commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "dirty": false}, "host": "ucrtasl", "label": "ENGINEERING_ONLY", "missing_llm_calls": 0, "model": "qwen2.5-coder:7b", "parse_failures": 0, "queried_action_distribution": {"continue": 2, "verify": 2}, "side_queries": 4, "utc": "20261013T090418Z"}}`
- **DT3:** `{"checks": {"collection_failures": 0, "label": "ENGINEERING_ONLY", "leaves": 2, "llm_calls": 8, "manager_kind": "langgraph", "parse_failures": 0, "proposal_examples": ["increase-hidden-units-64", "increase-batch-size-128", "increase-hidden-units-128", "increase-batch-size-128", "increase-hidden-units-128"]}, "commit": "48f8d8900bf688f8f4beec126cc6b9df408a075b", "completed": true, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/agent_paper_B/results/r1/engineering/E1b_llm_smoke_20261013T090434Z"}`
- **DT4:** `{"checks": {"collection_failures": 0, "label": "PILOT", "leaves": 144, "llm_calls": 1440, "manager_kind": "langgraph", "parse_failures": 0, "proposal_examples": ["increase-hidden-units-64", "increase-hidden-units-128", "increase-hidden-units-256", "increase-batch-size-128", "increase-batch-size-128"]}, "completed": false, "headroom": {"ALL": {"best_simple": "always_verify", "contrast_ci": {"always_verify - rho": [-0.00012251157407406135, 0.0014056759259259604], "awr_mlp - rho": [-1.934027777777958e-05, 0.0013154027777778077], "harness_heuristic - rho": [-0.00012251157407406135, 0.0014056759259259604], "kg_index - rho": [-0.00017409722222220224, 0.0013154027777778077], "margin_threshold - rho": [-0.00017409722222220137, 0.00027081944444445893], "oracle_leafsplit - always_verify": [-1.934027777777958e-05, 0.0001740972222222018], "oracle_leafsplit - rho": [-2.578703703703944e-05, 0.0014066434027778078], "oracle_naive - always_verify": [0.0, 0.0001805439814814621], "oracle_naive - rho": [0.0, 0.0014079327546296528], "random_matched - rho": [-0.00017409722222220224, 0.0006963888888889174], "ridge_advantage - rho": [-0.00017409722222220224, 0.0013154027777778077]}, "headroom_leafsplit": 5.1585648148140886e-05, "headroom_naive": 6.44791666666606e-05}, "digits_mlp": {"best_simple": "always_verify", "contrast_ci": {"always_verify - rho": [-0.0002579166666666424, 0.002695287037037121], "awr_mlp - rho": [-3.868055555555916e-05, 0.0026308055555556153], "harness_heuristic - rho": [-0.0002579166666666424, 0.002695287037037121], "kg_index - rho": [-0.0003481944444444045, 0.0026179120370370956], "margin_threshold - rho": [-0.00034819444444440274, 0.0005416388888889179], "oracle_leafsplit - always_verify": [-3.868055555555916e-05, 0.00034819444444440274], "oracle_leafsplit - rho": [-5.157407407407888e-05, 0.002785564814814883], "oracle_naive - always_verify": [0.0, 0.00036108796296292246], "oracle_naive - rho": [0.0, 0.0028113518518519207], "random_matched - rho": [-0.0001547499999999813, 0.001379884259259315], "ridge_advantage - rho": [0.0, 0.0012380277777777806]}, "headroom_leafsplit": 0.00010317129629628177, "headroom_naive": 0.0001289583333333212}, "openml_ionosphere": {"best_simple": "rho", "contrast_ci": {"always_verify - rho": [0.0, 0.0], "awr_mlp - rho": [0.0, 0.0], "harness_heuristic - rho": [0.0, 0.0], "kg_index - rho": [0.0, 0.0], "margin_threshold - rho": [0.0, 0.0], "oracle_leafsplit - rho": [0.0, 0.0], "oracle_naive - rho": [0.0, 0.0], "random_matched - rho": [0.0, 0.0], "ridge_advantage - rho": [0.0, 0.0]}, "headroom_leafsplit": 0.0, "headroom_naive": 0.0}}, "out": "/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/agent_paper_B/results/r1/pilot/E1b_20261013T151857Z", "report": "/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/agent_paper_B/docs/r1/reports/HEADROOM_PILOT_20261013_llm.md"}`

**STOP:** CalledProcessError: Command '['git', 'diff', '--cached', '--check', '--', '.', ':!results/r1/**', ':!experiments/r1/**']' returned non-zero exit status 2.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 13 October 2026 — launcher updated for GPU co-tenancy; DT4 rerun prepared

AI-assisted ENGINEERING_ONLY code change by Claude at the author's request; no runs. The author authorized a fresh DT4 attempt on Ada (PLAN §10, R1-COMPUTE DT4 rerun).

- `r1/scripts/deepthought_batch1_resume.py`:
  - card selection (`gpu_rows`) is now by free memory: footprint 5,304 MiB (DT1 `size_vram`) + 2,048 MiB margin;
  - `check_gpu` logs a census of every card (free memory, process owners) to `gpu_census.jsonl` and STOPs only when free memory is below the margin (footprint + margin before loading, margin alone after); other users' processes no longer cause a STOP;
  - new `assert_full_offload`: STOP unless `size_vram = size`;
  - a memory check before every collection session;
  - DT4 moved unchanged into `run_dt4(meta, version)`, plus a full-offload check after collection; the report's deviation note now describes co-tenancy;
  - executor label and commit co-author are configurable (`R1_EXECUTOR`, `R1_COAUTHOR`; defaults unchanged).
- New `r1/scripts/ada_rerun_dt4.py` (Ada-only; preconditions: DT1–DT3 complete and the interrupted DT4 preserved in the previous batch, duplicate-launch hold confirmed, both PLAN rows present, checkout at origin/main, a permanent `dt4_rerun_claim`) and `r1/scripts/ada_dt4_rerun_launch.sh` (fresh clone in a new batch directory, reuses the DT1 harness venv and pinned model files, tmux `r1_dt4_rerun`). Ollama runs with `OLLAMA_KEEP_ALIVE=-1`, so the model is never unloaded and reloaded onto a fuller card mid-run.
- `r1/tests/test_gpu_process_census.py` rewritten for the new rule (7 tests). The test "other user on card is rejected" is replaced by "allowed and logged".
- Checks (device VM, Python 3.13.15): `r1/tests` without the three harness-dependent files **58 passed**; `make test` control 212, release 6, standalone 12, all OK. The three harness-dependent R1 test files were not run here (no harness checkout in this environment); they do not import the changed scripts.
- `docs/r1/prompts/DEEPTHOUGHT_BATCH1_PROMPT.md` hard rule 1 now states the co-tenancy rule.
- **Not run yet.** The launch needs the author's Ada login: `bash r1/scripts/ada_dt4_rerun_launch.sh` on `ucrtasl` after these commits are on origin/main.

## 13 October 2026 — author decision: GPU co-tenancy allowed; latency descriptive

Planning only; no code and no runs. Recorded by an AI agent (Claude) at the author's request.

- **Author decision** (PLAN §10, R1-COMPUTE GPU co-tenancy): a card may be shared with other users when its free memory is enough; LLM latency is descriptive only. This replaces the idle-card / no-other-user condition of the earlier R1-COMPUTE rows. The other rules stay: pinned model, verified GPU offload with CPU fallback a STOP, no disturbance of other users, duplicate-launch prevention, no Mac LLM.
- **Agent-proposed default, for the author to confirm or change:** "enough" = free memory ≥ measured footprint + 2 GiB (≈ 7.2 GiB for the pinned 7B), checked at selection and before each step.
- RUNBOOK §3 (compute map, Ada bullet, new GPU-sharing bullet) and 0.4 (latency is descriptive, logged with a GPU census) updated to match.
- **Consequences.** The DT2/DT3 note that no exclusive-use claim is made needs no further action. The DT4 STOP was triggered only by the old ownership rule, so the decision removes that cause. A DT4 rerun still needs an explicit go from the author, as the DT4 entry says.
- The launcher and the batch prompt were updated afterwards (next entry).

## 13 October 2026 — old manuscript archived (RUNBOOK 0.1, legacy item)

AI-assisted housekeeping by Claude at the author's request; no runs, no evidence.

- Moved `papers/paper_b/` unchanged (sources, build products, `legacy/`, `archive/B1_20260927/`) to `archive/old_b_2026-10-09/paper_b_manuscript/`. `papers/` is now empty; the R1 manuscript goes in `papers/r1/` (RUNBOOK Phase 4).
- Repointed `make paper-b` (root `Makefile`) and the paths in `README.md`; documented the move and the remaining dangling `papers/paper_b/...` names (release scripts, `release/paper_b_manifest.json`, `PROVENANCE.md`, PLAN §8) in `archive/old_b_2026-10-09/README.md`. PLAN was not edited.
- No kept test reads the manuscript: `tests/release/test_provenance.py` builds its own fixture repo, and `scripts/release_provenance.py` reads `main.tex` from a historical source commit. `make test` after the move (Python 3.13.15): control 212, release 6, standalone 12 — all OK.
- The old release tooling (`make release-b`, `check-release-b`) still points at the old path and stays unmaintained, as before.

## 13 October 2026 — DT2/DT3 complete; DT4 stopped on GPU ownership conflict

AI-assisted ENGINEERING_ONLY smoke checks and interrupted PILOT; not evidence.

- Continuation selected Ada GPU 0 after its free-card census at 09:03:58 UTC. Exact pinned 7B digest verified; offload probe records size_vram 5560907776 and owned Ollama with 29 GPU layers. DT1 was not repeated. Deepthought permanent migration holds remain.
- DT2 committed/pushed `7f81283`: four side queries (two continue, two verify), zero parse/disallowed/call errors. Independently read six control events: every event has llm_calls and sum 4 reconciles with accounting/controller log. Ten worker runs, four LLM calls within caps 10/12. Output `results/r1/engineering/L12_live_20261013T090417Z/`.
- DT3 committed/pushed `48f8d89`: independently verified continue/verify leaves, zero collection failures, langgraph manager, eight LLM calls with zero parse failures and LLM proposal summaries. Output `results/r1/engineering/E1b_llm_smoke_20261013T090434Z/`.
- DT4 started at 09:05:10 UTC. Independent monitoring subsequently found root-owned PID 1625292 on selected GPU 0 alongside our Ollama. Its process start time precedes our Ollama start; the saved free-card census does not establish when it allocated GPU memory. GPU ownership during DT2/DT3 therefore has a limitation; no exclusive-use claim is made.
- Hard STOP enforced at 09:17:35 UTC: stopped only our continuation process tree and dedicated Ollama; NVIDIA census confirms our model process absent and the root-owned job untouched. Claims/results retained. Partial DT4 `results/r1/pilot/E1b_20261013T090510Z/` and interrupted work/log/state/offload/census bytes archived in `interrupted_provenance/`. No DT4 headroom bracket is accepted or analyzed. Monitoring paused; no failed/interrupted campaign retry.
- Author input needed for any further DT4 execution; a new attempt would require an explicit decision and reliable exclusive GPU allocation. E2 decisions remain open, fixed splits retained, no L11.

## 13 October 2026 — Any-idle-Ada continuation authorized

AI-assisted ENGINEERING_ONLY setup; DT1 remains the accepted PILOT.

- Author now permits **one idle Ada GPU for unstarted DT2–DT4**, instead of waiting for GPU 0. Recorded in PLAN §10, pushed `05af1c1`; selector implementation pushed `fded5fe`. No model, node, seed, budget or analysis design changed.
- Census: Ada GPU 2 (`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`) had no compute or graphics processes; the other seven cards were occupied. Selection is rechecked immediately before serving, and the chosen UUID stays fixed for the continuation.
- The old GPU-0-only waiting checkpoint had no campaign steps or claim. It now has a permanent migration hold, and only our waiting tmux session `r1_ada_DT2_DT4_census_20261013` was stopped. All earlier claims, stopped states and results remain intact; Deepthought launchers remain disabled.
- Fresh continuation path: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_idle_20261013_khbc3ro5/`. It may execute only unstarted DT2–DT4 after pin and actual GPU offload checks on the selected card. DT1's ten calls are never repeated. Same exact pinned 7B model, one card, no other users disturbed, no API/larger model/Mac inference, PILOT/ENGINEERING_ONLY only; no E2 decisions or L11.
- **Post-launch census:** GPU 2 became occupied (PID 1445397) before allocation; all eight cards now have processes. The current continuation is alive, scans all cards every 60 seconds, has no claim and has not loaded a model or started DT2–DT4. It will select and pin one genuinely idle card when available. Census JSON is preserved in the new checkpoint.

## 13 October 2026 — Ownership-census race repaired; DT2–DT4 still unstarted

AI-assisted ENGINEERING_ONLY launcher repair; harness defaults unchanged.

- After DT1 staging recovery, the separate checkpoint successfully loaded the pinned model and generated only its one-token offload probe. Before DT2 it stopped when a GPU PID exited between `nvidia-smi` and `ps`. No DT2–DT4 campaign or collection had started; no failed model/collection is retried.
- Launcher repair (`beb62b2`, fixture `d255907`, merged/pushed `fb10c1f`) accepts a disappeared PID only after a fresh census proves it absent, then rechecks all remaining process owners. Unknown live owners and other users remain STOP conditions. CPU mocks: 2 failed/1 passed before repair; **all 68 R1 tests passed after**. Logs: `results/r1/engineering/GPU_census_regression_20261013/`.
- Both prior stopped states and permanent claims are retained. A fresh checkpoint for only the unstarted DT2–DT4 phases is `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_census_20261013_ly8t2_9l/`; same node/seed/budget/model design and Ada GPU 0 only. DT1's original 10 calls are not repeated. Model pin and actual offload are revalidated before campaigns.
- DT1 remains accepted and committed in harness `9c4902d`. No E2 decision, L11, API/larger model or Mac inference. PILOT/ENGINEERING_ONLY only.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_20261013_pqaq4qvv/`.
- **Harness:** `9c4902d0d8776f18a081e1ff2478d651fc7096c1`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, NVIDIA RTX 6000 Ada Generation, 48427`; `{}`.

- **DT0_ADA:** `{"acceptance": "Known environment failures plus author-approved missing-zsh exception", "completed": true, "tests": {"accepted": false, "deepthought_shutdown": "Unconfirmed: direct and portal SSH timeouts on both hosts", "duplicate_launch_prevented": false, "finished_utc": "2026-10-12T19:47:51.375022+00:00", "gpu_offload_verified": false, "harness_failures": ["FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist", "FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance", "ERROR tests/test_legacy_noop_skip.py"], "harness_head": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "harness_summary": "10 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 33.58s", "harness_tests_exit": 1, "host": "ucrtasl", "inference_started": false, "label": "ENGINEERING_ONLY", "model_loaded": false, "paper_failures": [], "paper_head": "b246a4fd3d63c4b70b153995ad793abbf71d8a15", "paper_summary": "65 passed in 3.83s", "paper_tests_exit": 0, "prepared": true, "python": "Python 3.11.17", "started_utc": "2026-10-12T19:46:59.335607+00:00", "stop_reason": "Previously passing ClawWorker deterministic extraction test fails on Ada because /bin/zsh is absent", "uv_sync_exit": 0}}`
- **AUTHOR_EXCEPTION:** `{"commit": "0f25a18", "completed": true, "model_unchanged": true}`
- **DT1:** `{"commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`

**STOP:** CalledProcessError: Command '['ps', '-o', 'user=', '-p', '762418']' returned non-zero exit status 1.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 13 October 2026 — DT1 verified and committed; unstarted DT2–DT4 checkpoint

AI-assisted PILOT/ENGINEERING_ONLY execution; not evidence.

- **DT1 accepted:** Ada GPU 0 became unoccupied and the guarded runner started once. Ollama 0.9.2 served the exact pinned `qwen2.5-coder:7b` digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`. GPU offload verified before latency: `size_vram = 5560907776`, an owned process on the selected card, and server log confirms **29/29 layers offloaded**.
- **Latency:** 10 calls, 0 parse failures; median **820.871 ms**, mean **814.598 ms**, range **773.400–848.010 ms**. Independently checked event count, parse flags, CSV row count, pin and offload records. Harness commit `9c4902d` pushed and remote HEAD verified; data `experiments/r1/pilot/L4dt_20261013T011936Z/`.
- Original runner stopped during artifact staging (`git diff --cached --check`), before DT2. Raw generated CSV/log/patch whitespace caused the failure, not a model or collection failure. Every original artifact byte was preserved and hash-checked; only source changes are subject to whitespace checks. No extra DT1 call or harness behavior change occurred.
- The original stopped attempt, its state and permanent claim remain intact. Checkpoint scripts (`6826979`, `27184cc`, pushed) may continue **only unstarted DT2–DT4**, after rechecking GPU 0, the existing duplicate-prevention record and model pin/offload. They cannot rerun DT1 or any started DT2/DT3/DT4 step.
- New checkpoint logs: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_20261013_pqaq4qvv/`; original provenance remains `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`. No claim is cleared. Same planned nodes, seeds, budgets and manager; one GPU and no API/larger model. The known missing-zsh exception remains; E2 decisions remain open and L11 is unbuilt.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`.
- **Harness:** `cbbd5fb2421ea65ccda8a0da2bd7340533488b36`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, NVIDIA RTX 6000 Ada Generation, 48424`; `{"host": "ucrtasl", "probe_tokens_max": 1, "size_vram": 5560907776, "verified_before_DT1": true}`.

- **DT0_ADA:** `{"acceptance": "Known environment failures plus author-approved missing-zsh exception", "completed": true, "tests": {"accepted": false, "deepthought_shutdown": "Unconfirmed: direct and portal SSH timeouts on both hosts", "duplicate_launch_prevented": false, "finished_utc": "2026-10-12T19:47:51.375022+00:00", "gpu_offload_verified": false, "harness_failures": ["FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist", "FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance", "ERROR tests/test_legacy_noop_skip.py"], "harness_head": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "harness_summary": "10 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 33.58s", "harness_tests_exit": 1, "host": "ucrtasl", "inference_started": false, "label": "ENGINEERING_ONLY", "model_loaded": false, "paper_failures": [], "paper_head": "b246a4fd3d63c4b70b153995ad793abbf71d8a15", "paper_summary": "65 passed in 3.83s", "paper_tests_exit": 0, "prepared": true, "python": "Python 3.11.17", "started_utc": "2026-10-12T19:46:59.335607+00:00", "stop_reason": "Previously passing ClawWorker deterministic extraction test fails on Ada because /bin/zsh is absent", "uv_sync_exit": 0}}`
- **AUTHOR_EXCEPTION:** `{"commit": "0f25a18", "completed": true, "model_unchanged": true}`
- **DT1:** `{"completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`

**STOP:** CalledProcessError: Command '['git', 'diff', '--cached', '--check']' returned non-zero exit status 2.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 12 October 2026 — Deepthought duplicate-launch prevention confirmed

AI-assisted ENGINEERING_ONLY shutdown; no inference or evidence.

- SSH to both Deepthought hosts recovered. The old shared batch had no `runner_claim` and no `batch_state.json` on either host; no old runner had launched.
- Atomically created a permanent migration hold in `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z/runner_claim/`, with ENGINEERING_ONLY ownership provenance for Ada migration. The claim is retained and must never be cleared.
- Stopped only our dedicated `r1_auto_resume_20261012` launch-watcher session on each host. Both stop commands returned zero; the sessions are absent. Other users' jobs and other tmux sessions were untouched.
- Provenance and the confirmed `duplicate_launch_prevented: true` marker are committed in `results/r1/engineering/Deepthought_shutdown_20261012T200109Z/`. The marker is copied to the fresh Ada batch after syncing this commit, allowing its existing GPU-0-only watcher to proceed when that card has no process.
- This completes the duplicate-prevention prerequisite. Ada must still wait for unoccupied GPU 0, verify the exact pinned 7B model and demonstrate actual GPU offload before DT1 latency and DT2–DT4. The missing-zsh environmental exception remains in force; all other rules and open E2 decisions remain unchanged.

## 12 October 2026 — Ada continuation authorized; waiting on both launch prerequisites

AI-assisted ENGINEERING_ONLY setup; no inference or evidence.

- The author explicitly accepted the Ada missing `/bin/zsh` deterministic-extraction failure as environmental; recorded in PLAN §10 at pushed commit `0f25a18`. The recorded suite remains Paper B **65 passed**, harness **347 passed, 10 failed, 1 error**. Only the recorded environment failure set is accepted; all other STOP rules remain.
- Pushed `ef34671`: Ada-only watcher, fixed to GPU 0 UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`; host/path guards and actual runtime provenance. New scripts compile; no harness behavior was changed. The private fresh checkouts and environment remain under `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`.
- Dedicated Ada tmux `r1_ada_wait_20261012` checks every 60 seconds. It must observe both an unoccupied GPU 0 and a verified `deepthought_disabled.json` before creating one permanent `ada_runner_claim` and invoking DT1–DT4. It never selects another card or clears a claim.
- **GPU 0 became occupied:** user `vla-reasoning` now holds the selected card (PIDs 116617, 117775, 117778, 117779, 117780 at census). Their jobs were untouched.
- **Duplicate prevention is still pending:** direct IPv4 SSH to both Deepthought hosts timed out again. No claim was cleared or overwritten and no Ada model was loaded. Shutdown-only monitoring continues for the old shared claim/launchers; the separate Ada experiment monitor has been re-enabled under the author's exception.
- **DT1–DT4 remain unstarted.** Once both waiting gates pass, the runner must verify `qwen2.5-coder:7b` digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`, then demonstrate Ollama `size_vram > 0` and an owned process on selected GPU before the latency campaign or later steps. GPU offload has not yet been tested.
- No additional author decision is needed for the known missing-zsh failure. Other test regressions, model digest changes, CPU fallback or unrecorded experiment decisions remain STOP conditions. E2 decisions remain open; L11 is unbuilt. All outputs remain PILOT or ENGINEERING_ONLY.

## 12 October 2026 — Ada migration preparation: hard STOP before inference

AI-assisted ENGINEERING_ONLY preparation; no empirical evidence.

- Author authorized Ada GPU 0 for DT1–DT4, fresh checkouts and tests, pinned-model GPU offload, and prevention of duplicate Deepthought runs. Recorded in PLAN §10, commit `b246a4f` (pushed). Ada path/host guards and the duplicate-launch prerequisite were committed as `0d9874b` (pushed); harness code was unchanged.
- Fresh checkouts and private uv/Python environment: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`. Paper B test HEAD `b246a4f`; harness HEAD `cbbd5fb`. uv 0.13.0, managed Python 3.11.17. Existing Ada checkouts were preserved.
- Ada GPU 0: NVIDIA RTX 6000 Ada, UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`, no processes at census, about 47 GiB free. Seven other cards were occupied. No GPU process or Ollama server was started by this preparation.
- Tests: Paper B **65 passed**. Harness **347 passed, 10 failed, 1 error**, four subtests passed. Nine failures and the collection error are the recorded missing paper/artifact/submodule set. The artifact-report existence test returns to its initial failure on a fresh checkout; the prior passing result was already documented as a generated-report flake.
- **New failure / hard STOP:** `tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`, previously passing on Deepthought, raises `FileNotFoundError: [Errno 2] No such file or directory: /bin/zsh` on Ada. Under batch hard rule 5, this stops DT1–DT4 before inference. No harness fix, shell substitution, submodule initialization or test retry was attempted.
- Preserved logs and exact test identities: `results/r1/engineering/DT0_Ada_20261012T194751Z/`. Copies remain in the remote engineering scratch directory.
- **Duplicate prevention remains unconfirmed:** direct IPv4/default SSH to both Deepthought hosts and the existing portal jump routes timed out. Their prior shared claim and tmux launchers could not be inspected or disabled. Ada inference was therefore withheld; there is no Ada/Deepthought duplicate launch by this preparation.
- **DT1–DT4:** unstarted on Ada; model digest has not been checked through a serving instance, and actual GPU offload has not been demonstrated. The pinned 7B model and all other rules remain unchanged. No headroom bracket is available. No E2 decision was recorded; L11 remains unbuilt.
- **Needs author / infrastructure:** disposition of the missing-zsh environmental failure under the hard STOP rule, and working SSH access to reserve the old shared claim and stop the old launch watchers before any Ada inference.

## 12 October 2026 — Deepthought batch 1 automatic resumption armed

AI-assisted ENGINEERING_ONLY preparation; model workloads remain PILOT or ENGINEERING_ONLY.

- Author amendment in PLAN §10 (`12db087`): monitor both authorized hosts without the previous one-hour deadline, and resume DT1–DT4 on an unoccupied GPU. The previous stopped attempt and all results are preserved.
- Both hosts are checked every 60 seconds from dedicated tmux watchers. A shared atomic claim permits one runner only. No other user's session or process is changed.
- Fresh logs and runtime state: `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z/`. The pinned `qwen2.5-coder:7b` digest stays `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; no API or larger model.
- The runner first loads at most one probe token and requires Ollama `size_vram > 0` plus a process on the selected card before DT1 latency or DT2–DT4. GPU ownership is rechecked before every step. The older host's CUDA compatibility remains unqualified until that check passes.
- Latest census: Deepthought has another user's PID 1674140 on all four cards despite 0 percent utilization; Deepthought2 has other users' processes on both cards. No model has been started by this resumption at the time of this entry.
- DT0 and its regression baselines remain as recorded below. DT1–DT4 completion requires the runner's acceptance checks and subsequent status entry; no headroom bracket is available yet. E2 decisions remain open; L11 is not built.

## 12 October 2026 — Deepthought batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **DT0:** deepthought2; Paper B `d55043c`, harness baseline `4e8fd69`; uv environment installed. Harness: 9 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 52.87s. Paper B: 64 passed. OpenML credit-g cache filled successfully.
- **DT0 environment:** Deepthought2 has 128 logical CPUs, about 1 TiB RAM, two NVIDIA L40S GPUs (46,068 MiB each), driver 570.211.01; nvidia-smi reports CUDA capability 12.8. Docker daemon access is denied; no Podman is installed.
- **Authorized fallback:** `deepthought.etp.kit.edu` (PLAN §10 author follow-up, commit `ae14877`); 40 CPUs, 503 GiB RAM, four GTX TITAN X GPUs (12,288 MiB each), driver 525.147.05. The fallback was checked without disturbing its occupied GPUs.
- **Fallback CUDA compatibility is unqualified:** current [Ollama hardware documentation](https://docs.ollama.com/gpu) requires driver 570+ for compute capability 5.0–6.2; GTX TITAN X is 5.2. The installed runtime must demonstrate actual GPU offload before DT1 is accepted; no driver upgrade was attempted.
- **Harness repair:** `0e8a817` (pushed): explicit zero `llm_calls` in emitted control decisions. Regression: failed before, 9 targeted tests passed after; full suite: 8 failed, 349 passed, 1 warning, 1 error, 4 subtests passed in 34.21s. No newly failing tests; the artifact-report existence flake accounts for one prior failure becoming a pass.
- **Preserved engineering logs:** `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e/` (environment JSON, suite logs, OpenML log, GPU census/wait, official standalone Ollama runtime).
- **Model manifest preflight:** registry manifest SHA256 matches the author pin `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`. No inference is implied by this check.

- **COLLECTOR_REPAIR:** `{"commit": "63778d35c1a4aecf91ceb10514e8ae7e333112b7", "completed": true, "reason": "Retain branch directories and ledgers after auditing", "regression": "new test failed before; all 65 R1 tests passed after"}`
- **HOST_AUTHORIZATION:** `{"commit": "ae1487788c5e93bf007629accfdfdc1403b799fb", "completed": true, "decision": "Author permits deepthought.etp.kit.edu if a GPU is idle"}`
- **DT5_FEASIBILITY_PRECHECK:** `{"commit": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "completed": true, "out": "/ceph/dwong/autoresearch_harness/experiments/r1/pilot/MLGym_dt_20261012T183511Z", "reason": "Deepthought2: Docker daemon permission denied. Deepthought: Docker daemon cannot be reached. Neither host exposes Podman in PATH.", "status": "blocked", "task_runs": 0}`
- **DT2_SCRIPT_PREPARATION:** `{"checks": "Compilation and ChatOllama/LLMSelfController constructor preflight passed; no invoke, zero model calls", "commit": "ee6eab2d4ef4cd2a7df52cf8515ff60605b2324b", "completed": true, "live_run_completed": false, "script": "r1/scripts/l12_live_smoke.py"}`

**STOP:** RuntimeError: No GPU became idle within the one-hour availability window; other users were undisturbed

DT1–DT4 are accepted only where the step entry above explicitly records completion. Uncompleted steps produced no accepted LLM headroom bracket. L12 smoke script preparation is not a live run.

- **DT5 task runs not performed:** Deepthought2 denies access to its Docker daemon; Deepthought cannot reach its Docker daemon. Podman is absent from PATH on both hosts. The PILOT precheck JSON and its commit are listed above. No MLGym clone or adapter was created.
- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. The existing fixed split policy was retained. L11 was not built.

## 12 October 2026 (evening) — steps 1–6 of the revised order; E2 STOP prepared

Executed by an AI agent (Claude) at the author's request. Outputs are PILOT or ENGINEERING_ONLY: no evidence. The work ran in the Linux VM on the Mac (4 cores, 3 GiB, Python 3.11, environment outside the repos). That VM cannot reach Ollama, so no LLM call was made anywhere.

### Harness (`autoresearch_harness`, branch `r1`; not pushed)

| Commit | What |
|---|---|
| `423addd` | **L8b:** noisy CPU nodes `digits_mlp` and `tabular_mlp` (sklearn MLP; training and split seeds injected independently); `mlp_synthetic` seed injection with unchanged defaults. 5 tests. |
| `f0dcd6a` | **L7 fix, found while debugging E1b.** A resumed E2 trial did not restore the incumbent after a discard, dropped verify's evidence, did not charge verify's re-runs, and did not push keeps onto the stack. Every branch dataset collected with earlier code is invalid. 2 tests. |
| `c686517` | **L12:** `ControlDecision.llm_calls`; controller LLM calls are charged to the LLM-call cap. Default records and events are unchanged. 3 tests. |
| `4e8fd69` | **L14 review fixes:** resumed E1 charges its run and the revise call; the resume mask respects compute headroom; the new nodes no longer print `test_score`, which the worker would have parsed into the ledger. 2 tests. |

Suite (Linux VM): **347 passed, 9 failed, 1 error**. The failures and the error are the pre-existing environmental set.

### Paper B (`r1/` package; this repo)

- **E1 (step 1):** `r1/noise/`. 1,952 runs over 11 nodes. Report `reports/NOISE_FLOOR_20261012.md`, tables `reports/NOISE_FLOOR_20261012_tables.md`, data `results/r1/pilot/E1_20261012T145353Z/`.
  - Five nodes qualify under the proposed D21 rule.
  - The OpenML logistic-regression nodes have zero training-seed noise.
  - `openml_credit_g` was not measured: there is no data cache and OpenML is blocked from the VM.
- **T1 (step 1′):** `theory/T1_MODEL.md` (model and literature map; 11 citations checked against their sources).
- **L8b (step 2):** see the harness table.
- **L9 (step 3):** `r1/branch/` (r1_branch_v1 schema, sibling table, instance-cluster bootstrap, `matching_report`).
- **T2 (step 3):** `theory/T2_DERIVATIONS.md` and `r1/theory/acceptance.py` (Propositions 1–5, Monte-Carlo-checked). D23 proposal in §7.
- **L10 (step 4):** `r1/baselines/` (ρ, always, random-matched, margin threshold, harness heuristic, KG index, ridge advantage, AWR-MLP, naive and leaf-split oracles; PACE-style and racing responses implemented but not scored).
- **E1b (step 5):**
  - Main run `results/r1/pilot/E1b_20261012T161034Z/` and sensitivity run `results/r1/pilot/E1b_vary_ionosphere_20261012/`.
  - Report `reports/HEADROOM_PILOT_20261012.md`.
  - The first E1b run is kept in `results/r1/pilot/invalid/` and was never analysed (L7 defect).
  - Headroom ceiling: +0.0006 (`"fixed"`, both nodes) and +0.0025 (`"vary"`, ionosphere). The scripted proposer stood in for the LLM.
- **L12:** `r1/llm_control.py` (forked side query; stub-LLM tests only).
- **L13:** `r1/controllers.py`, `r1/e2e.py`, `make r1-e2e`. One run in `results/r1/engineering/E2E_20261012T163133Z/` (produced before the L14 label fix, so its manifest still says PILOT).
- **T3 (step 6):** `theory/T3_SIMULATION.md`, `r1/theory/simulate.py`, data `results/r1/engineering/T3_20261012T161444Z/`.
- **L14 (step 6):** `reviews/BUILD_REVIEW_20261012.md`. A fresh-session AI review found 6 MAJOR and 14 MINOR findings. One correction round followed; the items still open are listed in the review.
- **Tests:** `make r1-test` → 64 passed.
- **E2 STOP (step 7):** `reports/E2_STOP_MEMO_20261012.md`. **The author decides.** The memo proposes:
  - the premise C1 holds;
  - verify-based C3 fails the pre-check;
  - L11 is not built yet;
  - next: an overnight LLM rerun of E1b on the Mac, a D4 amendment for run-free acceptance rules, then Phase 1 or the fallback paper.

### Not done, and why

- No LLM ran: the VM cannot reach Ollama. The E1b LLM rerun is a Mac command in the headroom report.
- Not pushed: neither repo.
- PACE was not scored: it needs its own `verify:pace` action version (D4).
- The E1 skip/revise and E0 stop/demote branches were not collected.

## 12 October 2026 — plan revised: R1-REFRAME, R1-INDEX, R1-GATE-FIRST

Planning only; no code and no runs. Author decisions of 12 Oct recorded in PLAN §1 and §10; PLAN §2, §3, §5, §6, §7, §9 and RUNBOOK §3 updated to match. Drafted by an AI agent (Claude) at the author's request.

- **R1-REFRAME.** The headline is incremental acceptance under noise. C2 is now B's own theory: the value of verify and of a raised threshold as functions of |Δ̂|/σ_n, ϱ and remaining budget; the winner's-curse bias of `current_best` and the stagnation it causes; built on ranking & selection, knowledge gradient, racing and best-arm identification. New theory track T1–T3 in the RUNBOOK.
- **R1-INDEX.** The primary contrasts are learned arms vs the C2 index policy (KG-style or PACE-style, D23). LLM self-control stays, with a stronger manager at least as a deployment check (D22). Baselines split into required and secondary.
- **R1-GATE-FIRST.** Before any model is built: E1 (noise per training seed and split seed, node selection D21) and a new E1b / 0.4b pilot headroom pre-check. D16 and L11 are deferred until the gate passes. Fallback = C1 + C2.
- **Compute map** added to RUNBOOK §3: the Mac, deepthought (many CPU cores, 4 × TITAN 12 GB) and Ada (shared 8 × RTX 6000 Ada).
- **Not committed.** The edits are in the working tree only.
- **New open decisions:** D21 (noise nodes), D22 (stronger manager), D23 (index policy).
- **Still open from 9 Oct:** the four batch-2 questions (Docker for MLGym, held-out OpenML nodes, the `lr_synthetic` split policy, `mlagentbench_vectorization`).

## 9 October 2026 — build batch 2: L4, L7, L8

All output is ENGINEERING_ONLY or PILOT: no evidence. Harness work is on
branch `r1` (now pushed), three commits on top of `3c80b53`:
`3a9f203` (L4), `1a2983b` (L7), `b55209f` (L8). Paper B: `9ff6f2a` (batch-2
prompt + PLAN §10 rows).

### Machine and baseline

- Apple M1 Pro, 16 GiB RAM, macOS 26.6.2 (build 25G83).
- Ollama 0.40.2 running locally. D15 model `qwen2.5-coder:7b` already present
  (no download): digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`,
  Q4_K_M, 7.6B params, Apache-2.0.
- Step-0 baseline (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **321 passed, 8 failed, 1 error, 4 subtests**. The
  8 failures are the same environmental set as Linux (3 artifact-manifest,
  5 KDD paper-section) and the error is the `src.autoresearch_worker`
  collection error. Linux batch 1 reported 9 failures; on macOS the
  artifact-report existence test passes because the report is already on disk.

### L4 — pinned local manager model (`3a9f203`)

- Files: `manager/langgraph_manager.py` (per-call latency/usage telemetry in
  `proposal.extra["llm_call"]`), `control_plane/campaign.py` (emits an
  `llm_call` event; default controllers emit nothing new),
  `scripts/run_campaign.py` (`--worker claw|local`, default claw),
  `scripts/r1_llm_latency.py` (new), `tests/stage2/test_r1_l4.py` (4 tests).
- Smoke tests, both on `lr_synthetic`:
  - dry-run with `--llm-stub`: 3 trials, no Ollama, no `llm_call` telemetry.
  - real `--budget 5` with the pinned model and `LocalWorker` (on a copied
    node): 5 trials, 3 kept, `net_gain` ~0.00085.
- PILOT latency (5 real calls, `PILOT` table; output in
  `experiments/r1/pilot/L4_20261009T151754Z/`):

  | metric | min | median | mean | max |
  |---|---|---|---|---|
  | latency (ms) | 5943 | 6203 | 7296 | 12003 |
  | prompt tokens | 611 | 620 | 618 | 620 |
  | completion tokens | 83 | 88 | 86.6 | 88 |

  Parse failures: 0/5. Side note: the model is deterministic only in
  structure; sampling at temperature 0.2 varied the proposals.

### L7 — restore and branching (`1a2983b`)

- Files: new `control_plane/snapshot.py` (`CampaignSnapshot`, capture, write/
  read, `restore_snapshot`, `SnapshotRecorder`, `FirstActionThenPolicy`,
  `resume_campaign`, `run_restore_audit`); `control_plane/campaign.py` gains
  an optional `snapshot_hook` (None by default) invoked at E0/E1/E2 and
  `initial_current_best` / `initial_incumbent_stack`; `nodes/spec.py` gains
  `branch_state_paths` (declared per node, defaults in the module);
  new `scripts/r1_branch.py`; `tests/stage2/test_r1_l7.py` (7 tests).
- Snapshot contents: editable bytes, the declared non-editable node-state
  paths (`artifacts`, `results.tsv`, `experiment_memory.jsonl`,
  `.autoresearch_artifacts`, `run.log`, node-declared caches), ledger prefix,
  explicit `current_best` and incumbent stack (verified flags), budget and
  compute-budget states, train/split seeds, manager config, controller
  identity, and the epoch-local proposal (E1) / provisional record and worker
  result (E2). Every layer has a SHA-256 hash in `manifest.json`.
- Restore copytree's into a fresh isolated dir with its own ledger and events;
  E1/E2 resume uses the captured proposal and does **not** re-call the manager.
  Forced first actions are honoured; infeasible ones are rejected to
  `continue` (F6 semantics), which the branch CLI showed for
  revise/verify/demote/stop at E1.
- **Restore audit** (exact equality, never a tolerance). Output in
  `experiments/r1/pilot/L7_20261009T152619Z/`:

  | node | epoch | original metric | replayed metric | reproduced | editable/node_state/ledger hashes match |
  |---|---|---|---|---|---|
  | lr_synthetic | E1 | 0.922558 | 0.922558 | yes | yes/yes/yes |
  | openml_breast_w | E1 | 0.990338 | 0.990338 | yes | yes/yes/yes |

- Branch CLI smoke (`scripts/r1_branch.py`, snapshot at lr_synthetic E1,
  h=1) wrote `branch_manifest.json`; siblings are isolated (test writes in one
  branch, checks the other).

### L8 — benchmark adapters (`b55209f`)

- Files: new `nodes/openml_template/` and five node dirs
  (`openml_breast_w`, `openml_credit_approval`, `openml_diabetes`,
  `openml_ionosphere`, `openml_wdbc`); five `configs/nodes/openml_*.yaml`;
  `nodes/registry.py` registers them; `nodes/spec.py` gains `held_out`;
  `nodes/mlagentbench_vectorization/train.py` reads `AR_SPLIT_SEED` for the
  random problem; `tests/stage2/test_r1_l8.py` (4 tests).
- Adapter table (PILOT output in
  `experiments/r1/pilot/L8_20261009T152916Z/L8_adapters.json`):

  | node | OpenML id | rows | feats | licence | determinism | 3-trial smoke | blocker |
  |---|---|---|---|---|---|---|---|
  | openml_breast_w | 15 | 699 | 9 | Public | deterministic (0.993156) | kept/discarded/discarded | — |
  | openml_credit_approval | 29 | 690 | 15 | Public | deterministic (0.909670) | kept/discarded/discarded | — |
  | openml_diabetes | 37 | 768 | 8 | Public | deterministic (0.829667) | kept/kept/discarded | — |
  | openml_ionosphere | 59 | 351 | 34 | Public | deterministic (0.984520) | kept/discarded/discarded | — |
  | openml_wdbc | 1510 | 569 | 30 | Public | deterministic (0.997642) | kept/discarded/discarded | — |
  | mlagentbench_vectorization | — | — | — | MIT | **not** deterministic: `speed_score = 1/runtime` is timing-based (24.61 vs 23.85) | kept/discarded/discarded | none; seed injection added for the random problem |

- Held-out marking: `held_out` is a `NodeSpec` field (default false) and is
  serialised; no node is marked held out yet (MLAgentBench stays a dev node,
  as the author noted; the MLE-bench Lite subset is not added in this batch).
- **MLGym feasibility** (`experiments/r1/pilot/L8_20261009T152916Z/mlgym_feasibility.json`):
  cloned `facebookresearch/MLGym` to
  `~/Documents/third_party/MLGym` (CC-BY-NC-4.0; 20 task configs). Every task
  runs inside a Docker/Podman container (`dockerfiles/mlgym.dockerfile`,
  per-task conda). **Blocker: neither Docker nor Podman is installed or
  running on this Mac.** No adapter written. Removing the blocker needs
  Docker Desktop (or Podman + a Linux VM); then light CPU tasks
  (`titanicSurvival`, `3SATTime`, game-theory tasks) could be attempted,
  subject to dataset downloads and agent/model configuration.

### Checks

- Full suite after batch 2: **336 passed, 8 failed, 1 error, 4 subtests** =
  the Step-0 baseline + 15 new tests (L4 4, L7 7, L8 4), with the identical
  8-failure / 1-error set. The L5 golden regression and every batch-1 test
  stay green.
- Default behaviour: `snapshot_hook` is None by default, `initial_*` default to
  the previous derivation, and no new event is emitted for deterministic
  managers.

### Not done, and why

- The `SnapshotRecorder` snapshots only the first matching epoch by default;
  E0 snapshots store no proposal (there is none at E0).
- `resume_campaign` rebuilds `LocalWorker` and deterministic / LangGraph
  managers from the manifest; a manager with an injected stub LLM must be
  passed back in (tests do this).
- The openml nodes need a one-time OpenML fetch (network); the pilot copies
  carry `data_cache`, so re-runs are offline.

### Open questions for the author

1. MLGym needs Docker or Podman; installing one is a system change. Proceed?
2. Should any of the five OpenML nodes be held out, or is the whole OpenML pool
   training/dev (per PLAN §6, the held-out benchmarks are MLAgentBench and the
   MLE-bench Lite subset)?
3. `lr_synthetic` verify: the pilot shows training-seed noise ≤ 1e-4 while
   split-seed noise is ~0.01. Under the default `"fixed"` split policy,
   lr_synthetic verify will mostly measure the candidate difference. Confirm
   `"fixed"` remains the choice for this node.
4. `mlagentbench_vectorization`'s `speed_score` is timing-based. Keep it as a
   dev node, or exclude it from branch/label collection where determinism is
   required?

## 9 October 2026 — batch 1 review and fixes

All ENGINEERING_ONLY. Seven review findings on harness branch `r1` (at
`201e025`) fixed, one commit each, then `r1` merged into harness `main`.
Tests ran in a Linux VM (Python 3.11.16, env built outside the repo; the
macOS `.venv` was not touched).

### Findings and commits (harness)

- **F1 (MAJOR) revise ignored its feedback — `8086f97`.** E1 `revise` now
  calls `propose_next_trial(..., revision_feedback=feedback)`.
  `LangGraphManager` adds a REVISION REQUEST block to the prompt and records
  `extra.revision_feedback` only when feedback is given; the default prompt is
  byte-identical (golden sha256 test). `revise` is also masked out for
  managers whose `propose_next_trial` lacks the keyword, so it cannot fall
  back to a plain resample. This answers open question 4 of the previous
  entry: the feedback channel is the `revision_feedback` keyword.
- **F2 (MAJOR) verify could run unseeded — `5ec9e9d`.** The E2 mask uses
  `hasattr(worker, "run_trial_at_seed")` (real and dry loops), and
  `_run_worker_at_seed` raises `SeedInjectionUnsupportedError` instead of
  falling back to `run_trial`.
- **F3 (MAJOR) demote could revert verified keeps — `ddba025`.** The mask
  input is now `top_of_stack_unverified`; `_perform_demote` pops exactly the
  top entry and refuses an empty stack or a verified top.
- **F4 (MAJOR) coupled seeds — `81c5bd5`.** `lr_synthetic` builds its dataset
  from `AR_SPLIT_SEED` and trains with `AR_TRAIN_SEED` (both default 42);
  `openml_*` `SPLIT_SEED` defaults to 42 independently. `_run_verify` and
  `run_real_campaign` take `verify_split_policy` (`"fixed"` default, or
  `"vary"`), recorded as `extra.control.verify.split_policy`.
  `LocalWorker.run_trial_at_seed(split_seed=None)` now keeps the worker's
  configured split seed, so "fixed" really re-runs on the campaign's split.
- **F5 (MINOR) LLM calls counted for deterministic managers — `04ba041`.**
  Proposals count against `max_llm_calls` only when
  `not getattr(manager, "deterministic", False)`, in both campaign loops.
- **F6 (MINOR) infeasible choice crashed the campaign — `6756d68`.**
  `_require_feasible` is gone. A masked-out or epoch-unsupported action emits
  `control_decision_rejected` `{epoch, action, mask}` and the trial continues.
- **F7 (MINOR) docs — `d9b4401`.** Docstrings (`run_real_campaign`,
  `run_dry_campaign`, controller module, `ComputeBudget`, `seeds`), the README
  R1 section and `CLAUDE.md` updated. `run_dry_campaign` is documented as
  continue-only; its `NotImplementedError` message now says so.

New tests: `tests/stage2/test_r1_review_fixes.py` (21 tests). Every finding
has at least one test that failed on the pre-fix code and passes after it. A
few companion tests guard behaviour that was already right and pass on both:
the F1 golden default prompt, the F2 mask with a seeded worker, the F3
single-top demote, and F5 counting for an LLM manager. Two existing tests
were adapted:
- `test_r1_l6.py`: the mask test uses the renamed keyword. The six-trial
  scripted run now demotes at trial 4 and verifies at trial 5, because a
  demote right after a verified keep is no longer feasible.
- `test_r1_defects.py` L3.4: with the dataset now fixed, train seeds 7 and 8
  give the same `lr_synthetic` val_score (0.921357). The different-seed check
  uses train seed 100 and tests the split seed separately.

### Checks (Linux VM)

| Run | Passed | Failed | Errors |
|---|---|---|---|
| Baseline, `r1` at `201e025` | 299 | 9 | 1 |
| After fixes, `r1` at `d9b4401` | 320 | 9 | 1 |
| `main` after merge (`3c80b53`) | 320 | 9 | 1 |

- The failures and the error are identical across all three runs and are
  environmental: the 9 failures are the same set as the macOS baseline (missing
  untracked ledgers, figures and paper sections; `/bin/zsh`), and the error is
  the `src.autoresearch_worker` collection error.
- **The L5 golden-fixture regression (`test_r1_l5.py`) passes on Linux**, at
  baseline and after every fix. The fixture was not edited.
- The tree of `main` after the merge is identical to `r1`.

### Merge and push

- Harness merge commit on `main`: **`3c80b53`** ("Merge r1: R1 build batch 1
  (L3, L5, L6) with review fixes"); `r1` is checked out again.
- `git push origin main r1` **failed**: `fatal: could not read Username for
  'https://github.com': terminal prompts disabled`. The VM has no GitHub
  credentials, and none were configured. Push both branches from the Mac.
- This STATUS commit's own push is attempted right after it is made; the
  result is in the session reply. It is expected to fail the same way.

### Observation for the author

- On `lr_synthetic` the training seed now barely moves the metric (≤ 1e-4 on
  val_score, often 0 at 6 dp), while the split seed moves it by about 0.01.
  Under the default `"fixed"` policy, verify's paired deltas on this node
  will therefore be almost entirely the candidate-versus-incumbent difference,
  with little seed noise. Choose whether `lr_synthetic` verify should use
  `"vary"`.

## 9 October 2026 (night) — build batch 1: L3, L5, L6

All ENGINEERING_ONLY: no evidence. Harness work is on branch `r1` of
`~/Documents/autoresearch_harness`, based on `da8dcbd` (7 commits, not pushed).

### L3 — the four harness defects (one commit each)

- **c4efce7** `prompt_manager`: added `deterministic = True` and a docstring
  stating it makes no LLM call; corrected `CLAUDE.md` and the `README.md`
  layout comment. Test: `TestPromptManagerIsDeterministic` (2 tests).
- **6e670dc** `ClawWorker`: the legacy path no longer stores `1 - val_bpb`
  under a `val_bpb` node's metric name (minimise nodes keep the raw sign;
  AUC-style nodes still convert). Test: `TestClawWorkerMetricSign`.
- **f446429** `_current_best`: now respects `metric_direction` and counts only
  `KEPT` records. Tests: `TestCurrentBestOnResume` (minimise resume; invalid
  high metric ignored).
- **bf3df0d** Seed injection: new `worker/seeds.py`; `LocalWorker` and
  `ClawWorker` pass `AR_TRAIN_SEED` / `AR_SPLIT_SEED` to node subprocesses;
  `nodes/lr_synthetic/train.py` and both `nodes/openml_*/benchmark.py` read
  them with 42 as the default. Tests: `TestSeedInjection` (same seed
  reproduces, different seed changes the metric; seed vars are not editable
  symbols).

Files changed: `src/autoresearch/manager/prompt_manager.py`,
`src/autoresearch/worker/{claw_worker,local_worker,seeds}.py`,
`src/autoresearch/control_plane/campaign.py`, `nodes/lr_synthetic/train.py`,
`nodes/openml_credit_g/benchmark.py`, `nodes/openml_bank_marketing/benchmark.py`,
`CLAUDE.md`, `README.md`, `tests/stage2/test_r1_defects.py`.

### L5 — decision hooks and budgets (bb15e01)

- New `control_plane/controller.py`: `ControlView`, `ControlDecision`,
  `Controller` protocol, default `ContinueController`, `build_control_view`
  (leak-refusing) and `compute_mask`.
- E0/E1/E2 hooks in `run_real_campaign` (and E0/E1/E2 in `run_dry_campaign`),
  with the E2 evaluate/commit split before the single immutable append.
- New `control_decision` event; the default controller emits nothing.
- New `ComputeBudget(max_worker_runs, max_worker_seconds, max_llm_calls)` next
  to `BudgetState`; with only `--budget N` behaviour is unchanged.
- CLI: `--controller`, `--max-worker-runs`, `--max-worker-seconds`,
  `--max-llm-calls` (documented in `README.md`).
- Tests (written first, against the unmodified code):
  `test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`
  compares every non-excluded `TrialRecord` field against a golden fixture
  (`tests/stage2/fixtures/l5_default_records.json`) captured from the
  unmodified harness, for a dry campaign and a fixed-seed `LocalWorker`
  campaign; `TestControlViewLeak` (4 tests) rejects audit metrics, future
  records and sibling outcomes.

### L6 — actions (efca691, 201e025)

- `TrialDecision.SKIPPED` + `TrialState.SKIPPED` (PROPOSED → SKIPPED) with
  `TrialRecord` validation for skipped records (no metric, execution FAILED,
  validity VALID, no failure category, `extra.control`).
- `skip`, `revise`, `verify` (paired fresh-seed re-runs, frozen response rule,
  veto/rescue, hash-checked swaps), `demote` (incumbent stack) and `stop`;
  masks per problem spec §2.1.
- Skipped counted separately in `evaluation/metrics.py`, `memory/similarity.py`
  and `reporting/export_figures.py`; `summarizer.py` handles it via
  `decision.value`.
- Tests: `test_r1_l6.py` (10 tests) — one per action, the masks, the
  `TrialRecord.from_mapping` round-trip for skipped records, and a scripted
  controller issuing each action once across a 6-trial `lr_synthetic`
  campaign (with `LangGraphManager` + an injected stub LLM, no Ollama).

### Checks

- **Full harness suite** (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **299 passed, 9 failed, 1 error, 2 subtests
  passed**. L1 baseline was 277/9/1, so +22 new tests and **the same 9 failed
  and 1 error**. The failures are the pre-existing ones listed in the L1 entry
  below.
- **Default behaviour.** The L5 regression is green after every commit; the
  default `ContinueController` adds no record fields and no events.
- **New tests by name:** `test_r1_defects.py` (7), `test_r1_l5.py` (5),
  `test_r1_l6.py` (10). Full list in the session reply.
- **README dry-run:** `scripts/run_campaign.py --node lr_synthetic
  --campaign-id smoke --budget 3 --dry-run` runs cleanly. The `smoke` ledger
  already holds the 3 records from the L1 baseline check, so it resumes
  (`records_written=0`); a fresh id (`r1_check`) writes 3. A fresh run with
  `--max-worker-runs 2` stops after 2, confirming the compute cap.

### Not done, and why

- The `r1` harness branch is **not pushed**. Only the Paper B repo push was
  requested (L1). Say the word and I will push it.
- `run_dry_campaign` still raises for non-`continue` actions; the actions are
  implemented in `run_real_campaign`, which the L6 tests exercise. The runbook
  only asks for the dry path to carry the E0/E1/E2 hooks.
- `verify` re-runs use a synthetic (non-ledger) budget index and a no-edit
  proposal; the incumbent is restored from the pre-trial editable snapshot.
  The verify budget is measured but the per-run wall time is passed as 0.
- There is a pre-existing test-order flake: `test_artifact_completeness...`
  writes `paper/tables/artifact_completeness_report.txt`, and once that file
  exists one pre-existing failure flips to a pass (8 vs 9 failures). It is not
  caused by R1 code; I report the clean-tree count (`9 failed`).

### Open questions for the author

1. Push the harness `r1` branch to `origin`?
2. The runbook's verify rule sets `current_best` to the candidate's original
   single-run metric on a rescue or keep. On a rescue this can *lower*
   `current_best` (a rescued discard had a worse metric than the incumbent).
   Confirm that is intended, or change the rule.
3. `t_min` (stop threshold, default 3) and `verify_runs` (default 2) are
   function parameters only. Add `--t-min` / `--verify-runs` CLI flags?
4. `revise` records a fixed structured feedback string; the manager interface
   (`propose_next_trial(status, memory_context, node_spec)`) has no feedback
   argument, so the manager does not yet consume it. Confirm the intended
   feedback channel for L12.

## 9 October 2026 (evening) — build batch 1: L1

**L1 — Housekeeping.**
- **Paper B commit.** One commit, "Archive old Paper B plans; adopt route R1 canonical plan": the deletion of `docs/paper_split/`, the new `archive/old_b_2026-10-09/` and `docs/r1/`, the `README.md` banner, and the dated author decisions in PLAN §10 (D1, D3, D4, D14, D19, D20 — "decided 9 Oct 2026 by the author"). Pushed.
- **Harness.** Branch `r1` created from `main` at `da8dcbd` (the base commit). `uv sync --extra dev` succeeded. The `harness/claw-code` submodule is **not** initialised (D19).
- **Baseline test result** (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`): **277 passed, 9 failed, 1 error, 2 subtests passed**. Pre-existing, recorded not fixed:
  - `tests/test_artifact_completeness_and_manifest.py` ×4 (missing checked-in campaign report / manifest entries);
  - `tests/test_kdd_paper_sections.py` ×5 (the `paper/kdd_aae_2026/sections/*.md` files are absent);
  - `tests/test_legacy_noop_skip.py` error (imports `src.autoresearch_worker` from the uninitialised `harness/claw-code` submodule).

## 9 October 2026 (15:45) — build runbook and first prompt

Added `docs/r1/BUILD_RUNBOOK.md`, a per-step specification for L1–L14 written against the harness at `da8dcbd`, and `docs/r1/prompts/BUILD_BATCH1_PROMPT.md`, which covers L1, L3, L5 and L6 with the L2 defaults in an editable block. Nothing has been implemented yet.

## 9 October 2026 (15:30) — execution order adopted

RUNBOOK §3 gains the local-first order: build steps L1–L14 on the Mac, then experiments E1–E8. The next step is L1.

## 9 October 2026 (15:20) — configurator: encoder proposal

PLAN §7 is revised. The proposed primary is now a ModernBERT-family encoder decision model (Laya checkpoint vs plain ModernBERT-large), with late fusion of numeric features. Training is supervised, then an RL step with an RLCR-style bounded proper-score reward. Kev moves to the decoder comparison. D16 stays open.

## 9 October 2026 (afternoon) — format, benchmarks, configurator proposal

- **Author decisions:**
  - No manuscript format is fixed yet (R1-FORMAT).
  - ResNet-trigger is removed; experiments and configurator training use agent benchmarks across the board (R1-BENCH).
- **New open decision D20:** the benchmark set and scope. The proposal is in PLAN §6.
- **PLAN §7 gains** a verified candidate table and a proposed primary: Kev typed decision model; CLM, generative LLM and tabular as ablations. D16 stays open for discussion.

## 9 October 2026 (later) — venue, ledgers, harness clone

- **Author decisions:**
  - TMLR is the primary venue, with an ICML main-track quality bar (PLAN §9; D17 closed).
  - The original 1,355-trial ledgers are lost (D12 closed). Only aggregate tables survive, in the workshop-paper repo.
- **Harness clone.** `dowlingwong/autoresearch_harness` was cloned to `~/Documents/autoresearch_harness` at `da8dcbd`. The folder the author connected, `~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation`, is the workshop-paper repo (camera-ready; also the harness's submodule), not the harness code.
- **Note for the author.** Because the ledgers are lost, the `ClawWorker` `1 − val_bpb` sign issue cannot be checked for the workshop paper's autoresearch trials.
- **New default D14:** harness work on branch `r1` of that clone (confirm).
- **New open decision D19:** worker backend.

## 9 October 2026 — route R1 adopted; old plans archived; canonical plan written

- **Author decisions** (PLAN §1):
  - R1-ROUTE
  - R1-VENUE: rolling journal; TMLR recommended, to be confirmed as D17
  - R1-CARRY
  - R1-ARCHIVE
  - R1-PLAN
- **Archive.** All of the old `docs/paper_split/` moved to `archive/old_b_2026-10-09/docs_paper_split/`. The move includes the uncommitted §19 and §20 additions of 9 Oct and the 9 Oct prompt pack. Legacy code and the old manuscript stay in place for now (PLAN §8; RUNBOOK 0.1 decides).
- **New files:**
  - `docs/r1/PLAN.md`
  - `docs/r1/RUNBOOK.md`
  - this STATUS
  - `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`
  - `docs/r1/inputs/NOVELTY_SWEEP_20261009.md`

  The two inputs are AI-assisted subagent outputs and were not independently reviewed. In the sweep, three arXiv entries were spot-checked against their abstract pages (2607.05458, 2603.24647, 2608.21027). COTA's "0.5B" size is not stated on its arXiv page.
- **Not committed.** The file moves were made in the working tree with `mv`; nothing is committed yet. The first Phase 0 session commits them as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Next:** Phase 0 (RUNBOOK §3). The first prompt covers 0.1–0.3.
- **Open:**
  - D1–D12 and D14–D18 (PLAN §10);
  - the configurator architecture discussion (D16);
  - venue confirmation (D17).
