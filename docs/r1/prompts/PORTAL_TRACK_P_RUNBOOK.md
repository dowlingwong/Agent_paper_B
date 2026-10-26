# Post-training pipeline (RUNBOOK Track P) — agent runbook for zhixu portal

**Written 26 Oct 2026 by the coordinating session (Claude) at the author's request; AI-assisted. Revised 26 Oct: the agent runs on zhixu portal itself.** One implementation agent (Claude Code), started by the author in a shell on zhixu portal, executes this runbook step by step. It writes the training code, sets up and pins the decision models, runs the P.0 spikes and the decision-model exam, and later the A5/A6 training. Every phase ends with a STOP and an independent review; the author decides where marked. Do not skip a STOP.

Authority: `docs/r1/PLAN.md` §10 (R1-C3-POST, R1-C3-CONTROL, R1-SOFT-SIGMA, R1-PORTAL-SCHEDULE, R1-JEV-RUNG, R1-RB-TEACHER, R1-TRACKP-RUNBOOK; also R1-C3-BASE, R1-COMPUTE, R1-DAC-INTERFACE, R1-EXAM-HOST), `docs/r1/RUNBOOK.md` Track P, and the technical specification `docs/r1/TRACK_P_POST_TRAINING.md` (cited below as "spec §n"). If this file and those disagree, they win; stop and report.

## Why the agent runs where it runs

| Work | Where | Reason |
|---|---|---|
| The agent itself, code, unit tests, git, reports | **zhixu portal**, in the author's account, in its own clone of the repos under the Track P work dir | Every GPU step of Track P runs on this card anyway; running the agent here removes the dependence on the Mac's Tailscale and SSH, keeps code, data, checkpoints and logs on one host, and keeps Track P fully apart from the Track X agent, which works in the Mac's checkout. |
| All GPU work (spikes, exam, training, the verbalized-baseline llama-server) | **zhixu portal**, long jobs inside `tmux` sessions named `r1p_*` | Jobs survive the agent's session ending. |
| API calls (Jev rung, DeepSeek demonstrations) | **zhixu portal** (fallback deepthought if the portal cannot reach an API) | Keys exist on one host only, next to the logs they produce. |
| Labels | Produced on **deepthought** (B.2), committed to `main` by the sweep runner, pulled here | One source of truth; sha256 checked on arrival. |
| Author | **Mac** (or anywhere): reads reports, writes PLAN rows and authorization notes | The Mac runs no Track P work (R1-COMPUTE). |

## 0. Ground rules for this agent

- **Host.** You run on zhixu portal (user `dowling`). Everything happens here: code, tests, GPU jobs, API calls. Never use deepthought GPUs or zhixu experiment for Track P, and never move work to the author's Mac. You have no access to the author's Mac; anything that must come from it (e.g. OpenML caches, if ever needed) is requested from the author.
- **Clones and branches.** Clone `https://github.com/dowlingwong/Agent_paper_B` (and the harness repository, if a Track P step needs harness changes or the pinned harness commit) into the Track P work dir chosen in Phase 0; work on `trackp-<YYYYMMDD>` created from `main` (harness: from `r1`). If the Track X agent ever keeps its own clone on this host, never touch it. Small commits, author `Dowling Wong <wangdowling@gmail.com>`, each message ending with the two attribution lines the coordinating session gives you. You may push your own `trackp-*` branches (GitHub authentication on the portal is set up by the author; if a push fails for lack of credentials, STOP and ask); never push `main` or `r1`, never force-push, never rewrite pushed history. Merges are done by the coordinating session after review.
- **Card schedule (R1-PORTAL-SCHEDULE).** Track X evidence phases (B1, B2) have priority on the 4090. Before any GPU job: (1) check `docs/r1/STATUS.md` on `origin/main` for a running Track X evidence phase — if one is running, do not start; (2) `nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv` shows no other compute process; (3) take the lease with `flock -n ~/r1_locks/gpu0.lock <command>` (create `~/r1_locks/` once). If the lock is held, wait or work on CPU-only steps; never kill or signal a process you did not start. Record start/end of every GPU job in the phase log.
- **Secrets.** Keys are read only from `~/.config/r1/secrets.env` on the portal (mode 600; variables `TYPESAFE_API_KEY`, `DEEPSEEK_API_KEY`), loaded inside the job (`set -a; . ~/.config/r1/secrets.env; set +a`). The file is on the same host as you: never `cat`, `grep`, print, log, commit or copy it or any key, and never pass a key on a command line (it would appear in `ps` and shell history); manifests record only "key present: yes/no". The author places the file; if it is missing when an API step starts, STOP.
- **Labels and seeds.** Training labels come only from audit seeds 7001–7005; evaluation values 7006–7010 are read only in P.4's final evaluation and later, never for training, model selection, thresholds or the exam. The P.3b exam set is a fixed, committed subset of the training partition. Jev or DeepSeek outputs are never labels.
- **Evidence labels.** Code, spikes and dry runs: ENGINEERING_ONLY / DRYRUN. P.3a (E0/E6) and P.3b feed model selection and the appendix: evidence runs that need the author's authorization note `docs/r1/authorizations/trackp_<phase>_<date>.md` before they start. P.4–P.6 likewise. You never write an authorization note.
- **Independent review loop at every STOP (mirrors R1-EXAM-REVIEW).** (1) Spawn a fresh, independent reviewer agent on this host (a subagent or a separate Claude Code session) that has not seen your work in progress; give it the phase's goal, this runbook, the PLAN rows above, the spec sections, the branch and commit range and the phase's "Done when" — not your conclusions. (2) The reviewer writes `docs/r1/reviews/TRACKP_<phase>_REVIEW_<date>.md` with findings. (3) You fix every finding or answer it in the review file. (4) The same reviewer re-checks and writes "accepted" or "not accepted". You never accept your own phase.
- **Honesty.** A stopped run is reported as stopped. A box is ticked only when its check passed. No number is carried over from model cards or papers into our tables.
- **Reporting.** After acceptance: a short report in `docs/r1/reports/`, a STATUS entry ("independently reviewed and accepted", with the review file), and a message to the author: what was done, commits, checks with results, the review verdict, what is not done, questions for the author.

## Phase 0 — Host facts for Track P (read-only; ~1 h)

You are on the portal; run every command locally. Reuse `docs/r1/reports/PORTAL_HOST_FACTS_<date>.md` from the Track X agent if it has been accepted; collect only what it lacks. Before the clone exists, read this runbook and the PLAN rows from GitHub (`https://github.com/dowlingwong/Agent_paper_B`, branch `main`). Record, without installing anything:

| # | Fact | How |
|---|---|---|
| 0.1 | Host, user, OS, a work dir for Track P with ≥ 150 GB free (models ≈ 40 GB, checkpoints, logs) | `hostname`, `id -un`, `df -h` |
| 0.2 | GPU, driver, CUDA version, compute capability 8.9, other processes | `nvidia-smi` and the CSV query |
| 0.3 | Python ≥ 3.11 or `uv`, git, a CUDA toolkit matching the driver; whether PyTorch CUDA wheels can be installed (pip/uv index reachable) | `which`, `--version`, `curl -sI https://download.pytorch.org/whl/` |
| 0.4 | Network from the portal: GitHub (clone and push), huggingface.co, `api.typesafe.ai`, `api.deepseek.com`, and the Anthropic endpoints your own session uses (HTTP status only, no key) | `curl -sI --max-time 10 <url>`; `git ls-remote https://github.com/dowlingwong/Agent_paper_B` |
| 0.5 | Hugging Face access to every Track P repo (identities verified on the Hub, not guessed): Kev 0.8B and 4B and their adapters (`jaredpalmer/kev`), Qwen3.5-0.8B-Base and -4B-Base, Laya (`NandhaKishorM/laya`), StartLux-Decision v1.1 Instant 0.8B / 2B / 4B; gated or licence-acceptance repos listed for the author; StartLux weights are CC BY-NC (research use only — recorded) | `huggingface-cli whoami`; HEAD per repo |
| 0.6 | `~/r1_locks/` exists or can be created; `flock` available | `which flock` |
| 0.7 | Secrets file present with mode 600 (do not read its contents) | `stat -c '%a %U' ~/.config/r1/secrets.env` |
| 0.8 | Where you will work: the Track P work dir; clone the repos there now (the only write in Phase 0) and create `trackp-<YYYYMMDD>`; record HEADs | `git clone`, `git rev-parse HEAD` |

Output: `docs/r1/reports/PORTAL_TRACKP_HOST_FACTS_<date>.md`. **STOP 0:** review loop (the reviewer re-runs the commands); the author accepts any gated licences and confirms the work dir.

## Phase 1 — Code (on the portal; CPU only, no GPU lease needed; ~3–4 days)

Read first: spec §2–§7, RUNBOOK Track P and Track H, `r1/c3/{labels,rules,features,dataset,prior_model,serve,env,offline_eval}.py`, the Track H handoff `docs/r1/overnight/TRACK_H_25OCT_HANDOFF.md`. Build a scratch venv outside the repos (`uv`); record the test baseline of both repos before changing anything. Unit tests use tiny random-weight models (e.g. `hf-internal-testing` tiny configs) on **CPU only** (`CUDA_VISIBLE_DEVICES=""`), so they never need the GPU lease and never disturb a Track X run.

| # | Gap | Done when |
|---|---|---|
| 1.1 | **`r1/c3/train/model.py`** — `DecisionModel` protocol (spec §2.5): `forward(batch) -> {"belief_logits": [N, 12], "action_logit": [N] or None}`, `save`/`load` of adapter + heads with sha256. Wrappers `PointerWrapper` (Kev), `HeadWrapper` (Laya, StartLux), `BinTokenWrapper` (Qwen control, reserved `<b0>…<b11>`, `<exec>`, `<skip>`), `ReasonThenBinWrapper` (P.6). Belief-head forms softmax-12 and cumulative-11 (spec §2.3). | Tests on tiny models: shapes, save→load identical logits, sha256 recorded |
| 1.2 | **Serialisation** `r1/c3/train/serialize.py`: one template from the leak-guarded view (`features_from_view` inputs only; no audit, sibling or future fields), ≤ 1,024 tokens for every tokenizer in the pool (truncation rule declared and tested), fixed bin names and order. | Leak test reusing Track H's; length test per tokenizer |
| 1.3 | **Losses and metrics** `r1/c3/train/losses.py`, `metrics.py`: RPS (bins 1–11 cumulative + bin-0 Brier), CE, cost-sensitive BCE for the action, smoothed-rule ablation loss (spec §6.3); RPS skill vs base rate, all-bins and top-1 ECE, PIT, width ratio, action/rule disagreement. | Tests against hand-computed values |
| 1.4 | **Soft label v2 (R1-SOFT-SIGMA)** in `r1/c3/labels.py`: `soft_label(..., sigma_mode="pooled_node")` with s = σ̂_node/√K_label from the C1 30-seed table; version string recorded in every table; the old se_audit path kept, selectable, default switched to v2 for new tables only. **Action target** `u` per spec §3.5 (keep from `rules.keep` under the A1 constant prior and the logged Δ̂, g = 0.1 σ_node). | Tests; an existing pilot table rebuilt under v1 is byte-identical |
| 1.5 | **Tree packing** `r1/c3/train/packing.py` (spec §2.4): 4D mask + tree-depth position ids; automatically off for models that reject it. | Test on a tiny full-attention model: packed logits = unpacked logits (≤ 1e-5 fp32) |
| 1.6 | **Training CLI** `r1/scripts/trackp.py` with subcommands `spike`, `e0`, `probes`, `exam`, `sft`, `a6`, `rb`; one config `r1/scripts/configs/trackp_portal.json` with every host value as `TODO_VERIFY_ON_HOST`; resumable (checkpoint per ¼ epoch, resume without repeating completed steps); manifest per run with base revision, adapter/heads sha256, data-manifest hash, seed, git commits, GPU-lease log; refuses evaluation seeds before P.4 eval and refuses any `TODO_VERIFY_ON_HOST`. | Dry run on tiny models, including a kill-and-resume |
| 1.7 | **E0 generator and E6 probes** `r1/c3/train/exam_synthetic.py` (spec §5.5–5.6): (m, s) grid with held-out cells, distractor fields in the real serialisation; probes A1–A5 with their pass criteria. | Tests; generator output hashed and committed |
| 1.8 | **Exam analysis and frozen rule** `r1/c3/train/exam_analyze.py`; rule file `r1/c3/rules/p3_rule_v1.yaml` implementing spec §5.7, committed with its sha256 before any P.3b data exists. | Tests on synthetic results |
| 1.9 | **Jev client** `r1/c3/jev_client.py` (R1-JEV-RUNG): TypeSafe's official API (base `https://api.typesafe.ai`, path and request schema per `https://docs.typesafe.ai/api`; the `typesafe-ai` skill may help), a **versioned model name** pinned in the config (e.g. `jev-1.14.0`; never `jev-latest` or `jev-preview`), 11 yes/no questions per state, one per bin edge, as one request; monotone CDF → 12 bins; three repeats per state; full request/response JSON logged to `results/track_p/jev/<date>/calls.jsonl` with the model version the API returns; key from the environment only. A fake server for tests. | Tests with the fake server; a version mismatch between config and response is a STOP |
| 1.10 | **Demonstration writer** `r1/c3/rb_demos.py` (R1-RB-TEACHER): DeepSeek API, model `deepseek-flash` (expected to resolve to DeepSeek-V4.1-Flash-1017), input = the same serialised view the decision model sees, a fixed instruction asking for a short analysis (≤ 256 tokens) of whether the edit will help, **no labels or audit fields**; logs prompts, outputs and the returned model version to `results/track_p/rb_demos/<date>/calls.jsonl`; runs only in off-peak hours (outside 01:00–04:00 and 06:00–10:00 UTC on weekdays). Needed only for Phase 9; may be finished later. | Tests with a fake server; leak test on the prompt |
| 1.11 | **Sidecar loader** for H.5 (`r1/c3/serve.py` real loader replacing `FakeLoader`), reading P.7 pins. | Test with a tiny model; timeout fallback unchanged |

**STOP 1:** handoff `docs/r1/overnight/TRACKP_CODE_HANDOFF.md` with test counts before/after; review loop (the reviewer re-runs both test suites and the tiny-model dry run); after acceptance the coordinating session merges and pushes; then update your clone from `main`.

## Phase 2 — Environment, downloads and pins on the portal (~½ day)

| # | Step | Done when |
|---|---|---|
| 2.1 | Update the clone from the merged `main`; create one run venv (`uv`), PyTorch with CUDA for sm_89, transformers, peft, accelerate, the linear-attention kernels Qwen3.5's DeltaNet layers need (install what the Qwen3.5 model card / transformers version requires; record versions), ModernBERT support; `pip freeze` committed to the run log. | bf16 matmul and one DeltaNet forward run on the GPU |
| 2.2 | Download every Phase 0.5 repo at a resolved revision; record repo @ revision, files, sizes, sha256 in `r1/c3/train/registry.yaml`. Kev adapters: the released ones named in the Kev README. | Registry committed; all sha256 verified after download |
| 2.3 | Fill `trackp_portal.json` (no `TODO_VERIFY_ON_HOST` left). | `--check-config` passes |

**STOP 2:** review loop (the reviewer re-checks revisions and sha256).

## Phase 3 — P.0 spikes (ENGINEERING_ONLY; ≈ 1 day per base; GPU lease required)

For each base — Kev-0.8B, Kev-4B, Qwen3.5-0.8B-Base, Qwen3.5-4B-Base, Laya, StartLux Instant 0.8B / 2B / 4B — run `trackp.py spike`: load; forward one 12-option question; attach LoRA (r = 16; DeltaNet projections included on Qwen3.5 bases); 100-example toy SFT with soft targets on both outputs; save → reload → identical belief and action probabilities; sha256; peak VRAM and step time at 1,024 tokens, batch 8, gradient checkpointing; tree-packing acceptance (expected to fail on Qwen3.5 hybrids — recorded, not a failure). StartLux: show a training forward in plain transformers with the correct bidirectional prompt mask (compare its logits with the vLLM-plugin path on 20 prompts, if that path can be run; record the difference).

Output: `docs/r1/reports/TRACKP_P0_SPIKES_<date>.md`, one row per base. **STOP 3:** review loop; then the **author decides the StartLux rung** (trainable candidate or inference-only zero-shot rung) in a PLAN row.

## Phase 4 — P.1/P.2 toy batch on every family (ENGINEERING_ONLY; ~½ day)

The same 64-example toy batch trains for 50 steps on every family that passed P.0, both outputs, through the shared loop; loss decreases; save/reload identical. **STOP 4:** review loop.

## Phase 5 — P.3a label-free exam (evidence; ~1 day; GPU lease)

Requires the authorization note `trackp_p3a_<date>.md`. Run first as a DRYRUN on one model, then for every candidate that passed P.0:
- **E0** (spec §5.5): frozen backbone head fit, then 200 LoRA steps, soft labels; the hard-label contrast run; held-out-cell RPS, width slope, mean slope. **Superseded 26 Oct by E0 protocol v2 (R1-E0-PROTOCOL, spec §5.5):** a fresh LayerNorm + linear belief head for every model, both stages to convergence on held-out validation cells (≤ 2,000 steps), lr grid, width slope vs the label's own std; A3 per R1-A3-BUDGET; thresholds set by the author after the v2 DRYRUN.
- **E6** (spec §5.6): A1–A5 with their criteria; A1/A2 only for models with packing.

Output: `docs/r1/reports/TRACKP_P3A_<date>.md` and the appendix figure data (soft vs hard). **STOP 5:** review loop (the reviewer recomputes slopes and pass/fail from the run outputs); models that fail E0 are disqualified per spec §5.7.

## Phase 6 — Wait for labels and freeze the exam set (no GPU)

Proceed only when (a) `origin/main` carries ≥ 400–500 training-partition labels from B.2 (soft label v2) with a committed sha256; (b) the coordinating session has committed the exam-set membership (`exam_member`, ≥ 3 nodes, 70/30 split by instance seed, grouped by edit hash) with its sha256; (c) `p3_rule_v1.yaml` is committed with its sha256 in a PLAN row; (d) the authorization note `trackp_p3b_<date>.md` exists. Pull the label table on the portal and verify its sha256. If the table cannot reach the portal through git, ask the author to copy it (deepthought → portal) and verify the sha256 on arrival.

## Phase 7 — P.3b labelled exam (evidence; ~2–3 days; GPU lease; Track X B1/B2 must not be running)

1. **Zero-shot rungs (E1):** each candidate's native decision interface; the control via bin-token logits; the verbalized top-k baseline with the current manager GGUF (`qwen2.5-coder:7b`, the Track X anchor, already pinned) served by the pinned llama.cpp build (a second instruct model only if the author adds one); the **Jev rung** via `jev_client.py` (keys from the secrets file; model version pinned and logged; three repeats).
2. **E2** frozen probe; **E3** short LoRA SFT (300 steps × 3 seeds, identical recipe for all); **E4** engineering numbers; **E5** ECE after temperature scaling; the non-LLM floor (frozen embedding + ordinal logistic regression; GBDT on hand features).
3. Run `exam_analyze.py` with the committed rule → ranking, tied set, finalists; then **E7** (softmax-12 vs cumulative-11) on the top two.

Output: `docs/r1/reports/TRACKP_P3B_EXAM_<date>.md` (appendix table). **STOP 7:** review loop (the reviewer recomputes the ranking and tied set from the run outputs and checks the rule hash); then the **author confirms the finalists and head form** in a PLAN row. If no LLM beats the floor significantly, STOP and escalate.

## Phase 8 — P.4 A5 SFT (evidence; = B.5; GPU lease)

Requires the full B.2 label table and the authorization note `trackp_p4_<date>.md`. Finalists + Qwen control (0.8B and 4B): spec §6.1 recipe, 3 seeds; learning curve 250/500/1k/2k; final evaluation on test instances with evaluation seeds only; RL gate (spec §6.2) recorded. Output: the A5 table for B.5, `docs/r1/reports/TRACKP_A5_<date>.md`, and P.7 pins. **STOP 8:** review loop; the author decides whether B.7 runs.

## Phase 9 — P.5 A6 and P.6 reasoning arm (evidence; only after B.7 passes; GPU lease)

- **P.5:** arms R-A0, R-A1, R-A2, R-A3 per spec §6.3; the GRPO unit test first (cosine ≥ 0.95); rollback rule; deployment as rule(belief) or action head, never the greedy bin. Needs the H.8 amendment (action = execute/skip) accepted first.
- **P.6:** demonstrations with `rb_demos.py` (off-peak; ≈ 500 examples; cost logged), warm-up SFT, then GRPO per spec §6.4 on the generative bases only; ablation without analysis.

Each needs its own authorization note. **STOP 9:** review loop; reports `docs/r1/reports/TRACKP_A6_<date>.md`, `TRACKP_RB_<date>.md`; P.7 pins updated.

## Timing (against Track X, PORTAL_EXAM_RUNBOOK)

| Window | Track X on the card | Track P |
|---|---|---|
| 26 Oct – ~29 Oct | Phase 0–1 (host facts; code on the Mac): card free | Phase 0–1 (code on the portal, CPU only); Phase 2 as soon as Phase 1 is merged |
| ~29 Oct – ~1 Nov | Phase 2–3 (downloads; Stage A, ~1 day of GPU) | Phase 3 spikes in the gaps around Stage A; Phase 4 |
| ~2 Nov – ~10 Nov | B1, B2 (evidence; card busy) | No GPU work; Phase 5 analysis, Phase 1.10–1.11 code, Phase 6 preparation |
| ~10 Nov onwards | Done | Remaining Phase 3–5, Phase 7 once labels exist, Phase 8 for B.5 (~22 Nov) |

If Track X runs long, Track P waits; it never pre-empts a Track X evidence run.
