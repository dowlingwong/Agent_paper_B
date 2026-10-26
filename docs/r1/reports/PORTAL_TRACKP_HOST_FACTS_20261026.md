# Portal host facts for Track P — 26 October 2026

AI-assisted execution record (Claude Code, Track P agent, running on zhixu portal). ENGINEERING_ONLY. Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 0; PLAN §10 R1-TRACKP-RUNBOOK, R1-PORTAL-SCHEDULE. **Status: awaiting STOP 0 (independent review; author decisions below).** Nothing was installed; no model weights were downloaded; no GPU job ran; no secret was read. The only writes were the two clones in 0.8 and this report.

Collected 2026-10-26 ≈ 01:25–01:35 UTC (portal local clock shows 25 Oct ≈ 18:25; dates in names follow UTC, as the Track X report does). Evidence: [portal_trackp_host_facts_20261026/](portal_trackp_host_facts_20261026/) — `inventory.sh` (the read-only commands; a reviewer re-runs it with `bash inventory.sh > /tmp/x.txt`), `hf_repos.py` (anonymous Hub metadata, stdlib only), `inventory.txt` (transcript with exit codes).

Relation to Track X: `PORTAL_HOST_FACTS_20261026.md` on branch `exam-x-20261026` (Phase 0 accepted there, not on `main`) confirms the same host (`TASL-2`, uid 1008, RTX 4090, driver 535.309.01). It has no Track P repos, no API endpoints and no secrets check, and it found GitHub HTTPS access to the private repo not ready; that has changed (0.4). All facts below were re-collected.

## 0.1 Host, user, OS, work dir

| Fact | Value |
|---|---|
| Host / user | `TASL-2` / `dowling` (uid 1008); this is zhixu portal (same identity as the Track X report) |
| OS | Ubuntu 22.04.5 LTS, kernel 6.8.0-136-generic |
| CPU / RAM | 32 logical CPUs; 62 GiB RAM (57 GiB available), 2 GiB swap (almost fully used) |
| Disk | `/` on `/dev/nvme0n1p2`, 1.9 T, **837 G free** (≥ 150 GB requirement met; Track X will also place ≈ 500 GB of GGUFs on the same filesystem, which still leaves > 300 GB) |
| **Proposed Track P work dir** | **`/home/dowling/r1_trackp/`** (created for the clones in 0.8); planned layout: `Agent_paper_B/`, `autoresearch_harness/`, `models/` (HF downloads, Phase 2), `venvs/` (scratch and run venvs), `runs/` (checkpoints, logs). Awaiting author confirmation. Separate from Track X's proposed `/home/dowling/exam-x/`. |
| Other checkout | `/home/dowling/Agent_paper_B` (on `main` at `b5a7aec`, clean) exists; this session was started there. Not used for Track P work and not modified. |

## 0.2 GPU

NVIDIA GeForce RTX 4090, 24,564 MiB, **compute capability 8.9**, driver **535.309.01**, driver CUDA **12.2**. Processes: Xorg (401 MiB) and gnome-shell (18 MiB) only; the compute-apps query is empty; utilisation 0 %. Track X STATUS on `origin/main` shows no running evidence phase (Track X is at STOP 0 on its branch). No GPU job is planned before Phase 3.

## 0.3 Toolchain

| Item | Found | Consequence |
|---|---|---|
| Python | system `python3` **3.10.12** only; no 3.11/3.12; `ensurepip` missing (so `python3 -m venv` cannot bootstrap pip); no torch / transformers / huggingface_hub | Below the ≥ 3.11 requirement → `uv` is needed |
| `uv` | **not installed**; `astral.sh/uv/install.sh` and python-build-standalone releases reachable (200) | Phase 1 first step: install `uv` into `~/.local/bin` (user space, no sudo) and let it fetch Python 3.11/3.12. Needs author OK (an installation). |
| git / git-lfs / gh / tmux / flock | git 2.34.1, git-lfs 3.7.1, gh 2.94.0 (logged in as `dowlingwong`), tmux, util-linux flock 2.37.2 | OK |
| CUDA toolkit | `/usr/local/cuda-12.2`, nvcc 12.2.140 (not on PATH) — matches the driver | OK for building kernels against CUDA 12.x. PyTorch wheels for cu121/cu124 run on driver 535 (CUDA 12.2) only if the wheel's CUDA ≤ 12.2 driver capability or via minor-version compatibility; the cu12x choice is made in Phase 2 and verified by the bf16/DeltaNet smoke test. |
| PyTorch index / PyPI | `download.pytorch.org/whl/` 200, `pypi.org/simple/` 200 | Wheels installable |
| `huggingface-cli` / `hf` | not installed; no HF token anywhere (no `~/.cache/huggingface/token`, no `HF_TOKEN`) | Anonymous downloads suffice: every repo needed is public and un-gated (0.5) |

## 0.4 Network (HTTP status, no keys)

| Endpoint | Status | Reading |
|---|---|---|
| github.com | 200 | reachable |
| `git ls-remote https://github.com/dowlingwong/Agent_paper_B` | OK (main = `b5a7aec`) | repo is **private**; `gh` credential helper works; `gh api` reports push permission |
| `git push --dry-run origin trackp-20261026` | OK (`[new branch]`) | push of `trackp-*` will work |
| `autoresearch_harness` (public) | clone OK | |
| huggingface.co | 200; `resolve` of a weight file redirects to `us.aws.cdn.hf.co` → 200 | downloads work |
| api.typesafe.ai | 404 at `/` | host reachable (TLS + HTTP answer); real path per docs is a Phase 1.9 matter |
| docs.typesafe.ai/api | 307 | reachable |
| api.deepseek.com | 401 at `/` | reachable (auth required, as expected) |
| api.anthropic.com | 404 at `/` | reachable; this session itself runs through it |

## 0.5 Hugging Face repos (identities verified on the Hub, anonymous)

All checks are anonymous API metadata plus a HEAD of a pinned `config.json` (adapter repos have none → 404 is expected). No weights fetched.

| Role | Hub repo | Revision observed (main) | Licence | Gated | Size | Notes |
|---|---|---|---|---|---|---|
| Kev-0.8B (adapter + pointer head) | `jaredpalmer/kev-0.8b` | `bf75a6a8848e…` | Apache-2.0 | no | 0.07 GB | Tag `v1.0` = `788ddbdd6571`; adapter and `head.pt` LFS oids identical at `main` and `v1.0`. LoRA r = 16 on q/k/v/o, MLP and DeltaNet (`in_proj_qkv/a/b/z`, `out_proj`); `base_revision` = `dc7cdfe2…` (= Qwen3.5-0.8B-Base main) |
| Kev-4B | `jaredpalmer/kev-4b` | `6cfce5c2fa4b…` | Apache-2.0 | no | 0.16 GB | Tag `v1.0` = `591dcb5bd6d0`; weights identical to `main`; `base_revision` = `1001bb4d…` (= Qwen3.5-4B-Base main). Other tags (`qwen3`, `night2-du-release`, …) are older/alternative versions, not used |
| Qwen control / Kev base 0.8B | `Qwen/Qwen3.5-0.8B-Base` | `dc7cdfe2ee41…` | Apache-2.0 | no | 1.77 GB | |
| Qwen control / Kev base 4B | `Qwen/Qwen3.5-4B-Base` | `1001bb4d826a…` | Apache-2.0 | no | 9.34 GB | |
| Laya | **`convaiinnovations/laya-typed-decisions`** | `e929ae5cf69b…` | Apache-2.0 | no | 0.85 GB | ModernBERT-large, 421M, **1,024 context** — the checkpoint RUNBOOK Track P describes. See discrepancy D1 |
| (Laya English base, not proposed) | `convaiinnovations/laya` | `7b928d828b7b…` | Apache-2.0 | no | 2.37 GB | 512 context per the Laya README; listed only to separate it from the typed-decisions checkpoint |
| StartLux Instant 0.8B | `startlux-models/StartLux-Decision-v1.1-0.8B-Instant` | `6496ae641cc7…` | **CC BY-NC 4.0** | no | 1.77 GB | See D2 |
| StartLux Instant 2B | `startlux-models/StartLux-Decision-v1.1-2B-Instant` | `f1e6cd147dda…` | **CC BY-NC 4.0** | no | 4.57 GB | |
| StartLux Instant 4B | `startlux-models/StartLux-Decision-v1.1-4B-Instant` | `416088f77cfc…` | **CC BY-NC 4.0** | no | 9.34 GB | |

Total download for Phase 2 ≈ 28 GB. **No repo is gated or requires licence acceptance; no HF login is needed.** StartLux weights are CC BY-NC 4.0: research, non-commercial use only — recorded here; the author confirms this is acceptable for the paper.

Discrepancies with RUNBOOK Track P ("Facts checked 25 Oct"):
- **D1 — Laya identity.** RUNBOOK and the runbook name `NandhaKishorM/laya`. On the Hub that name returns 401 (no such public model); it is the **GitHub** repository (200) holding the code and the fine-tuning notebooks. Its README links the weights to `convaiinnovations/*`; the 1,024-context typed-decisions checkpoint is `convaiinnovations/laya-typed-decisions`. Proposed: pin that repo for Laya; record `NandhaKishorM/laya` (GitHub) as the code source. Author to confirm.
- **D2 — StartLux org and serving.** The RUNBOOK names `StartLuxLabs/StartLux-Decision`: that is the GitHub code repo (200); the weights are under the Hub org `startlux-models`. The StartLux README says Instant models are served through a vLLM plugin and that StartLux-Prism (their own engine) needs Python 3.12 and a **CUDA 13 driver** and does not support v1.1 Instant. The portal driver is 535 / CUDA 12.2. Consequence for Phase 3: the "compare with the vLLM-plugin path" check may not be runnable here unless vLLM with the plugin works on CUDA 12.x; the plain-transformers training forward (the actual P.0 requirement) is unaffected.
- **D3 — Kev pin.** The Kev README calls the `v1.0` tags the release ("Kev 1.0"); they carry the same adapter/head bytes as `main`. Proposed: pin the `v1.0` tag's commit (`788ddbdd…`, `591dcb5b…`) in the Phase 2 registry.

## 0.6 GPU lease

`flock` present (`/usr/bin/flock`). `~/r1_locks/` does **not** exist yet; the home dir is writable, so it can be created (will be created at the first GPU step, as the runbook says "create once"). The Track X agent is asked to use the same lock file (`PORTAL_EXAM_RUNBOOK.md` §0).

## 0.7 Secrets file

`~/.config/r1/secrets.env` is **absent** (`stat` exit 1; `~/.config/r1/` does not exist). Not needed until Phase 1.9/1.10 tests (which use fake servers) — it is first needed at the Phase 7 Jev rung and Phase 9 demonstrations. The author places it (mode 600, owner `dowling`).

## 0.8 Clones and branches

| Repo | Path | Branch | Created from | HEAD |
|---|---|---|---|---|
| Agent_paper_B | `/home/dowling/r1_trackp/Agent_paper_B` | `trackp-20261026` | `origin/main` | `b5a7aeca62b98c0e33699dd4a26e1cd7e63febc8` (before this report's commit) |
| autoresearch_harness | `/home/dowling/r1_trackp/autoresearch_harness` | `trackp-20261026` | `origin/r1` | `264011ea2d17fa9070b8c711625db92f8409dd4b` |

**Finding H1 — harness pin not on GitHub.** `main`'s `r1/scripts/HARNESS_PIN_C3` = `6afdb0e9b800933dfbb682618b8909441f0f6495` (Track H). After `git fetch --all` the harness remote has only `main` and `r1` (`264011e`), and `git cat-file -t 6afdb0e…` fails: the commit is not on GitHub (the Track X report used a harness `r1` at `6afdb0e`, presumably from the Mac checkout). The Track H harness branch (`track-h-25oct` → `r1`) appears not to have been pushed. Phase 1 code is mostly in this repo, but harness-side work and any test that checks the pin need it pushed to `r1`. Both clones have `user.name`/`user.email` set locally to `Dowling Wong <wangdowling@gmail.com>`.

## Questions for the author (STOP 0)

1. Confirm the work dir `/home/dowling/r1_trackp/` (≥ 150 GB free: 837 G now).
2. Confirm Laya = `convaiinnovations/laya-typed-decisions` (D1) and Kev pinned at the `v1.0` tags (D3).
3. Confirm StartLux CC BY-NC 4.0 (research use) is acceptable; note D2 (vLLM-plugin comparison may be impossible on driver 535).
4. Allow installing `uv` in user space (`~/.local/bin`) at the start of Phase 1 (Python 3.10 on the host is below the ≥ 3.11 requirement).
5. Place `~/.config/r1/secrets.env` before Phase 7 (not blocking Phase 1).
6. Harness (H1): `main` pins harness `6afdb0e`, which is not on GitHub (`origin/r1` = `264011e`). Please push the Track H harness commits to `r1` (or say which base `trackp-*` in the harness should use). The harness clone's `trackp-20261026` is currently at `264011e` and will be rebased onto the pushed `r1` before any harness change.
