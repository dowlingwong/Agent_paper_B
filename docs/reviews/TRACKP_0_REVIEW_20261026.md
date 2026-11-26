# Track P Phase 0 review — 26 October 2026

- Reviewer: independent subagent (Claude Code, on zhixu portal `TASL-2`); had not seen the implementation agent's work in progress.
- Date: 2026-10-26 ≈ 01:30–01:40 UTC (portal local 25 Oct ≈ 18:30 PDT).
- Phase: Track P Phase 0, "Host facts for Track P" (`docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, table 0.1–0.8, Output, STOP 0).
- Commit range: `b5a7aec..870e6de` on `trackp-20261026` (1 commit, 4 files: the report, `inventory.sh`, `hf_repos.py`, `inventory.txt`).
- Deliverable: `docs/r1/reports/PORTAL_TRACKP_HOST_FACTS_20261026.md` and `docs/r1/reports/portal_trackp_host_facts_20261026/`.
- Also read: PLAN §10 R1-TRACKP-RUNBOOK, R1-PORTAL-SCHEDULE, R1-C3-POST, R1-C3-CONTROL, R1-JEV-RUNG, R1-RB-TEACHER; RUNBOOK Track P "Facts checked 25 Oct"; `TRACK_P_POST_TRAINING.md` base-model rows.

## What I re-ran

1. `bash docs/r1/reports/portal_trackp_host_facts_20261026/inventory.sh > /tmp/trackp0_review/inventory.txt` (01:30:02 UTC). Diff against the committed transcript: identical except disk bytes (±10 MB), the `trackp-20261026` ref now existing on GitHub (`870e6de`), the push dry-run now "Everything up-to-date", and the clone HEAD now `870e6de`. All expected.
2. Own commands: `hostname`, `id`, `/etc/os-release`, `df`, `free`, `nvidia-smi` (+ both CSV queries: RTX 4090, 535.309.01, CUDA 12.2, compute_cap 8.9, compute-apps empty), `command -v`/`--version` for python3/uv/git/git-lfs/gh/flock/nvcc, `/usr/local/cuda-12.2` nvcc 12.2.140, `curl -sI` status codes (github 200, huggingface 200, api.typesafe.ai 404, docs.typesafe.ai/api 307, api.deepseek.com 401, api.anthropic.com 404, pytorch index 200, PyPI 200), `git ls-remote` of both repos, `gh api` repo permissions.
3. Hugging Face Hub API (anonymous, metadata only; no weights): `/api/models/<repo>?blobs=true`, `/refs`, `/revision/v1.0`, author listings for `jaredpalmer`, `startlux-models`, `convaiinnovations`, `StartLuxLabs`, `NandhaKishorM`; small JSON files only (`adapter_config.json`, `provenance.json`, `config.json`, `encoder/config.json`, `README.md`).
4. GitHub API: `repos/jaredpalmer/kev`, `repos/StartLuxLabs/StartLux-Decision`, `repos/NandhaKishorM/laya` (all 200) and their READMEs; `repos/dowlingwong/autoresearch_harness/commits/6afdb0e…` (422, not found) and branches (`main`, `r1` only).
5. PyTorch wheel index listings (`download.pytorch.org/whl/<cuXXX>/torch/`, HTML only).
6. Clones: branches, upstreams, reflogs, local `user.*` config, HEADs, `git cat-file -t 6afdb0e…`, `r1/scripts/HARNESS_PIN_C3`, `git diff --check`; `git show origin/exam-x-20261026:` Track X report and `origin/main:docs/r1/STATUS.md`.
7. Ground-rule checks: `find ~ -newermt '2026-10-25 18:00'` (outside the clones), absence of `~/.cache/huggingface`, `~/.local/bin/uv`, `~/r1_locks`, `~/r1_trackp/{models,venvs}`; `stat` of `~/.config/r1/secrets.env` (absent). No secret contents were read.

## Confirmed

- 0.1: `TASL-2`, `dowling` uid 1008, Ubuntu 22.04.5, kernel 6.8.0-136, 32 CPUs, 62 GiB RAM, 837 G free on `/` (≥ 150 GB met). Work dir `/home/dowling/r1_trackp/` holds only the two clones.
- 0.2: all values exact; only Xorg/gnome-shell on the card; Track X has no running evidence phase on `origin/main` (STOP 0 on its branch).
- 0.3: Python 3.10.12 only, no `ensurepip`, no uv, no torch/transformers/huggingface_hub; git 2.34.1, git-lfs 3.7.1, gh 2.94.0, flock 2.37.2; CUDA 12.2 toolkit off PATH.
- 0.4: all status codes reproduced; private repo, push permission true; push of `trackp-*` works (branch now on GitHub at `870e6de`).
- 0.5: every repo identity, `main` sha, licence (Apache-2.0 ×6, CC BY-NC 4.0 ×3), gated = false, private = false, and size reproduced. Total ≈ 27.9 GB. Kev `v1.0` tags (`788ddbdd6571`, `591dcb5bd6d0`) carry the same adapter/head LFS sha256 as `main` (0.8B: `9b908623…`/`f400bd12…`; 4B: `90e81735…`/`dd633435…`); `provenance.json` `base_revision` = Qwen3.5-0.8B-Base `dc7cdfe2…` and Qwen3.5-4B-Base `1001bb4d…` (both = Hub `main`); LoRA r = 16 with DeltaNet targets. D1 correct: `NandhaKishorM/laya` is Hub 401 / GitHub 200; `convaiinnovations/laya-typed-decisions` is ModernBERT-large (28 layers, hidden 1024), 421M, 1,024 context per its README. StartLux 0.8B/2B/4B Instant exist under `startlux-models`; `StartLuxLabs/StartLux-Decision` is GitHub 200 / Hub 401. No HF token present; none needed.
- 0.6: flock present, `~/r1_locks` absent, home writable.
- 0.7: secrets file absent (`stat` exit 1) — honestly recorded.
- 0.8: Agent_paper_B `trackp-20261026` from `origin/main` `b5a7aec` (reflog: clone → checkout → rename from `trackp-20261025`), upstream `origin/trackp-20261026`; harness `trackp-20261026` = `origin/r1` `264011e`, upstream `r1`, not pushed. H1 confirmed: `HARNESS_PIN_C3` = `6afdb0e…` is not on GitHub (`cat-file` fails; GitHub API 422).
- Ground rules: nothing installed, no weights downloaded, no GPU job, no secret read; commit `870e6de` authored and committed by `Dowling Wong <wangdowling@gmail.com>` with the attribution line; only `trackp-20261026` pushed (`trackp-20261025` never reached GitHub); `/home/dowling/Agent_paper_B` untouched (clean at `b5a7aec`).

## Findings

1. **Minor — Kev repo name not listed as a discrepancy.**
   Claim: the report maps "Kev" to `jaredpalmer/kev-0.8b` / `kev-4b` without comment; D1–D3 cover only Laya, StartLux and the Kev pin.
   Observed: the runbook 0.5 and RUNBOOK Track P name `jaredpalmer/kev`; on the Hub that name is 401 (no such model), it is the GitHub code repo (200). The weights are `jaredpalmer/kev-0.8b` / `kev-4b` (the Kev README links them). The README also says GitHub release `kev-1.0` carries the 0.8B/4B checkpoints with SHA-256 checksums.
   Fix: add a D-entry (as for D1/D2): `jaredpalmer/kev` = GitHub code; Hub repos `jaredpalmer/kev-0.8b`, `jaredpalmer/kev-4b`; note that the `kev-1.0` release checksums can cross-check the Phase 2 sha256.

2. **Minor — PyTorch/CUDA wheel statement is wrong and unclear.**
   Claim (0.3, CUDA toolkit row): "PyTorch wheels for cu121/cu124 run on driver 535 (CUDA 12.2) only if the wheel's CUDA ≤ 12.2 driver capability or via minor-version compatibility".
   Observed: the `cu121` index tops out at torch 2.5.1 and `cu124` at 2.6.0. Current torch 2.14.1 ships only as `cu126` and `cu130` (`cu128` tops at 2.11.0, `cu129` at 2.13.0). `cu130` needs a newer driver than 535. On this host `cu126` works only through CUDA minor-version compatibility (runtime 12.6 on a 12.2 driver).
   Fix: rewrite the sentence with these facts. Record as a Phase 2 risk that the torch/transformers version Qwen3.5 needs may force `cu126` under minor-version compatibility, which the 2.1 smoke test must confirm, or a driver upgrade (author decision).

3. **Minor — D2 overstates the CUDA 13 requirement and leaves out the relevant serving versions.**
   Claim: StartLux-Prism "needs Python 3.12 and a CUDA 13 driver".
   Observed: the StartLux README says to install Prism with Python 3.12 and a CUDA 13 driver, but also that "StartLux-Prism's README covers CUDA 12 drivers". Either way, Prism does not support v1.1 Instant, so Prism is irrelevant here. The path that matters for the P.0 comparison is the vLLM plugin (`pip install -e '.[vllm]'`, vLLM 0.31.0; 0.19.1 also supported), and the report does not say which vLLM/CUDA versions that path needs.
   Fix: correct the Prism sentence and give the vLLM plugin versions as the thing to check in Phase 2/3. Optional, informational: the v1.1 Instant `config.json` declares `Qwen3_5ForConditionalGeneration` (the same hybrid DeltaNet architecture as the Qwen3.5 bases). That matters for the P.0 "bidirectional prompt mask in plain transformers" check.

4. **Minor — Laya alternative-repo row is incomplete.**
   Claim: `convaiinnovations/laya` is "Laya English base, not proposed … listed only to separate it from the typed-decisions checkpoint".
   Observed: that repo also contains `typed-decisions/model.safetensors` with the same LFS sha256 (`4fa56de72383…`) as `convaiinnovations/laya-typed-decisions/model.safetensors`.
   Fix: say so in the row. The proposed pin (`laya-typed-decisions`) can stay, and the identical blob in the umbrella repo becomes a cross-check.

5. **Minor — several claims are not covered by the evidence a reviewer is told to re-run.**
   Claim: "a reviewer re-runs it with `bash inventory.sh`".
   Observed: these claims appear nowhere in `inventory.sh` / `hf_repos.py` / `inventory.txt`:
   - GitHub 200 and Hub 401 for `NandhaKishorM/laya` and `StartLuxLabs/StartLux-Decision` (only the Hub 401 for Laya is captured);
   - Kev `v1.0` vs `main` LFS identity and `provenance.json` `base_revision`;
   - the weight-file `resolve` redirect to `us.aws.cdn.hf.co` → 200;
   - `HARNESS_PIN_C3` and the failing `git cat-file` for `6afdb0e`;
   - the Track X STATUS check on `origin/main`;
   - "gh logged in as `dowlingwong`";
   - the StartLux README facts.

   I re-verified all of them independently, and they are correct apart from findings 3 and 4. Separately, the stated collection window "≈ 01:25–01:35 UTC" runs past the commit time (01:29:30 UTC; transcript stamped 01:27:49).
   Fix: add these commands to `inventory.sh` (or a second script) and re-generate the transcript, and correct the collection window.

6. **Minor — clarify who changed the global git/gh config.**
   Claim: "The only writes were the two clones in 0.8 and this report."
   Observed: outside the clones, `~/.gitconfig` (gh credential helper), `~/.config/gh/config.yml` and `hosts.yml` were modified 18:16–18:19 PDT, and `~/.bashrc` at 18:23 PDT. All of this was before the clones (18:26), and it is consistent with the author setting up GitHub auth and Claude Code as the runbook says. I did not read `hosts.yml`.
   Fix: state in the report that these were set up by the author (or say what the agent ran), so the "only writes" claim is unambiguous.

No blocking findings: 0.1–0.8 are all covered, the numbers reproduce, and the ground rules were respected. The author's decisions (work dir, Laya/Kev pins, StartLux CC BY-NC, `uv` install, secrets file, harness pin H1) are correctly left open for STOP 0.

Verdict: pending fixes

## Implementation agent's response (26 Oct)

1. Kev name — fixed: new D4 in the report (GitHub `jaredpalmer/kev` vs Hub `kev-0.8b`/`kev-4b`; Phase 2 cross-checks against the `kev-1.0` release checksums); author question 2 updated.
2. PyTorch wheels — fixed: the wrong sentence replaced by Phase 2 risk R1 (cu121 ≤ 2.5.1, cu124 ≤ 2.6.0, cu128 ≤ 2.11.0, 2.14.1 only cu126/cu130; cu130 impossible on driver 535; cu126 via minor-version compatibility, runtime-JIT kernels a risk); author question 4 updated.
3. D2 — fixed: CUDA 13 statement removed; vLLM plugin (vLLM 0.31.0 / 0.19.1) named as the relevant path; Instant configs = `Qwen3_5ForConditionalGeneration` noted with its consequence for the bidirectional mask.
4. Laya row — fixed: `convaiinnovations/laya` `typed-decisions/model.safetensors` has the same sha256 (`4fa56de7…`) as the proposed repo; stated in the row.
5. Evidence — fixed: `followup.sh` / `followup.txt` added covering the listed claims (plus wheel index, Laya duplicate, StartLux architecture); collection window corrected (01:25–01:29 UTC first run; follow-up after review).
6. Pre-session writes — fixed: a sentence in the header names the three files and times and attributes them to the author's setup before the session; not done by this agent.

## Re-check (26 Oct 2026, ≈ 02:05 UTC)

Reviewer: the same independent subagent. Range re-checked: `b5a7aec..f08e5e4` (new commit `f08e5e4`, authored and committed by `Dowling Wong <wangdowling@gmail.com>` with the attribution line; GitHub `trackp-20261026` = `f08e5e4`; harness `trackp-20261026` still `264011e`, not pushed).

What I re-ran: `bash followup.sh > /tmp/trackp0_review/followup.txt`. Apart from the timestamp it is identical to the committed `followup.txt`. The two non-zero exits are the expected failures for the missing harness pin: `git cat-file` 128, and `gh api` 422 → exit 1. I also read the report diff `870e6de..f08e5e4` and checked `docs/vllm_bidirectional.md` in `StartLuxLabs/StartLux-Decision` (it exists).

1. Kev name: **fixed.** D4 matches what I see: `jaredpalmer/kev` is GitHub 200 / Hub 401, the weights are in `kev-0.8b` / `kev-4b`, and the `kev-1.0` release page returns 200. Author question 2 is updated.
2. PyTorch wheels: **fixed.** Risk R1 matches the index: cu121 → 2.5.1, cu124 → 2.6.0, cu126 → 2.14.1, cu128 → 2.11.0, cu130 → 2.14.1. The driver thresholds (≥ 560 for 12.6, ≥ 580 for 13.x) are right. Author question 4 is updated, and nothing is decided.
3. D2: **fixed.** The CUDA 13 overstatement is removed. The vLLM plugin (0.31.0 / 0.19.1) is named as the relevant path. The `Qwen3_5ForConditionalGeneration` / `qwen3_5` architecture is reproduced, and its consequence for the mask is stated correctly.
4. Laya row: **fixed.** Both files have sha256 `4fa56de72383…a24e`.
5. Evidence: **fixed.** Every claim listed in finding 5 is now reproduced by `followup.sh`: code-repo statuses, Kev `v1.0` = `main` bytes, `base_revision` from `training_config.json`, the weight redirect to `us.aws.cdn.hf.co` (200), the harness pin missing, the Track X STATUS headings, the `gh` login, the wheel index and the StartLux README lines. The collection window is corrected to 01:25–01:29 UTC plus a follow-up. Note: `followup.sh` runs `git fetch` in the clones. That only writes refs inside the clones, which the ground rules allow.
6. Pre-session writes: **fixed.** The header names the three files and their mtimes (I reproduced them) and attributes them to the author's setup. I cannot verify who made the changes, but the timing (before the clones and before this session's own files) supports the statement.

No new findings. The author decisions for STOP 0 stay open, correctly: work dir, Laya/Kev pins, StartLux CC BY-NC, R1/uv, the secrets file, and harness pin H1.

Verdict: accepted — Phase 0 read-only host-facts inventory (0.1–0.8) is complete and reproducible, and every review finding is resolved; acceptance does not cover the author's STOP 0 decisions listed above.
