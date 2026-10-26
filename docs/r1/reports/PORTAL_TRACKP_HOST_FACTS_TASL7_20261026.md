# Track P Phase 0 on TASL-7 — host facts (26 Oct 2026)

AI-assisted (Claude Code, Track P agent running on TASL-7). ENGINEERING_ONLY. Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`, host-change header, migration step (1); PLAN §10 R1-TASL7-TRACKP. The script is `tasl7_trackp_host_facts_20261026/inventory.sh`, the portal's Phase 0 script with only its header comment changed. Its full transcript is `inventory.txt`, collected at 22:33 UTC. The portal facts for comparison are in `PORTAL_TRACKP_HOST_FACTS_20261026.md`.

Writes in Phase 0 were limited to the clones (0.8) and `~/r1_locks/` (0.6). Nothing was installed in Phase 0, no secrets file was read, and there was no GPU job.

| # | Fact | TASL-7 | Portal (TASL-2), for comparison |
|---|---|---|---|
| 0.1 | Host, user, OS | `TASL-7`, `dowling` (uid 1011), Ubuntu 22.04.5, kernel 6.8.0-138. AMD Ryzen 9 7900X, 24 logical CPUs, 62 GiB RAM. Tailscale `tasl-7` (100.106.74.51). | TASL-2, Ubuntu 22.04.5, 32 CPUs, 62 GiB |
| 0.1 | Disk / work dir | `/` (nvme0n1p2) 1.9 T, **965 G free** (≥ 150 GB). Work dir **`/home/dowling/r1_trackp/`**, the same path as on the portal, so every configured path is unchanged. | `/home/dowling/r1_trackp/`, ≈ 899 GB free |
| 0.1 | Other users | `tianyu` and `jiachenl` have login sessions on the host; `gdm` runs a desktop. No compute process of theirs is on the GPU (below). R1-TASL7-TRACKP says the node is exclusive to the author, so the GPU-lease precondition (no foreign compute process) is still checked before every job. | another user's desktop |
| 0.1 | Pending reboot | `/var/run/reboot-required` dated **6 Oct 2026**, packages libc6 and linux-image 5.15.0-194/-198. Uptime 25 days. The coordinating session asked the author for a reboot before long runs; this is **not done**. | — |
| 0.2 | GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, compute capability **8.9**, **driver 580.178.04 / CUDA 13.0**. Only Xorg (167 MiB) and gnome-shell (12 MiB), both graphics; the compute-apps query is empty. | RTX 4090, driver 535.309.01 / CUDA 12.2 |
| 0.3 | Python / uv | System `python3` 3.10.12 (`venv` and `ensurepip` present). No 3.11/3.12, no `uv`, no torch/transformers/huggingface_hub. | 3.10.12, no `ensurepip` |
| 0.3 | Toolchain | git 2.34.1, git-lfs 3.0.2, gh 2.102.0, tmux, flock (util-linux 2.37.2), gcc/g++ 11.4.0. CUDA toolkits **11.7 and 12.2** in `/usr/local/cuda-*`; `nvcc` is not on PATH and there is no `/usr/local/cuda` link. | toolkit 12.2 outside PATH |
| 0.3 | Package indexes | download.pytorch.org/whl 200, pypi.org/simple 200, astral.sh 200, python-build-standalone 200 | same |
| 0.4 | Network | github.com 200, huggingface.co 200, api.typesafe.ai 404 (root, no key), docs.typesafe.ai/api 307, api.deepseek.com 401 (no key), api.anthropic.com 404 (root). Every endpoint is reachable. | same codes |
| 0.4 | GitHub | `git ls-remote` works for both repos (paper `main` = `fc3e0da`, harness `r1` = `897d83c`). `gh` is logged in as `dowlingwong`; the paper repo is private with push permission. `git push --dry-run` to `trackp-20261026` succeeds, and the real push of `f3567e9` succeeded. | no credentials on the portal at first |
| 0.5 | Hugging Face | No token (whoami 401), which is not needed. Every Track P repo's Hub metadata (sha, gated, licence, files, sizes) is **identical to the portal's Phase 0 record** apart from `last_modified` (diff empty). All repos are public and un-gated. StartLux is CC BY-NC 4.0 (research use only). | same |
| 0.5 | Hub download path | The Xet transfer client (`hf_xet`, part of the pinned venv) stalled at 0 bytes on TASL-7. Plain HTTPS from `us.aws.cdn.hf.co` works, so Phase 2 downloads use `HF_HUB_DISABLE_XET=1`. This is a runtime setting; no package changed. | — |
| 0.6 | Lock | `flock` is available; `~/r1_locks/` created (empty). The Track X marker `trackx_evidence.active` is not present on TASL-7 and, per the header, is not needed. | same |
| 0.7 | Secrets | `~/.config/r1/secrets.env` is **absent**. It is needed only from Phase 7 (Jev) and Phase 9 (DeepSeek), and the author places it. | absent at Phase 0 |
| 0.8 | Clones | Paper `/home/dowling/r1_trackp/Agent_paper_B` on `trackp-20261026` (`471f93f`, merged with `origin/main` `fc3e0da` → `af158f1`; the STATUS conflict was resolved by keeping both entries unchanged). Harness `/home/dowling/r1_trackp/autoresearch_harness` on `trackp-20261026` = `r1` = `897d83c` = `HARNESS_PIN_C3`. Worktree `/home/dowling/r1_trackp/equiv_8e13e77` (detached, paper `8e13e77`) for the host-equivalence run. | — |

## Differences from the portal that matter for Track P

1. **Driver 580 / CUDA 13.0 instead of 535 / 12.2.** The pinned torch 2.6.0+cu124 runs through the driver's backward compatibility, which is less of a stretch than on the portal. bf16 kernels are not guaranteed bit-identical across drivers. That is why the host-equivalence check exists.
2. **24 CPUs instead of 32.** This affects data-loader and L-BFGS head-fit wall time, not results.
3. **Pending reboot since 6 Oct.** This is for the author to schedule. A reboot during a run would kill it; Track P runs are resumable per checkpoint.
4. **Other login users.** The node is declared exclusive. The lease still checks for foreign compute processes.

## Questions for the author

1. Confirm the work dir `/home/dowling/r1_trackp/` on TASL-7 (the same path as on the portal).
2. When will you reboot TASL-7, and should it happen before the P.3a runs?
3. Is it intended that `tianyu` and `jiachenl` have sessions on the "exclusive" node? If they may use the GPU, the lease will refuse to start while they do.
