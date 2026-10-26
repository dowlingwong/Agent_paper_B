# Portal host facts — 26 October 2026

AI-assisted execution record. ENGINEERING_ONLY. Phase 0 is **BLOCKED / INCOMPLETE**; no host fact is accepted and no exam has run.

## Scope and provenance

Authority: `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md`, Phase 0; PLAN §10 R1-EXAM-HOST. `git pull --ff-only origin main` returned “Already up to date”; paper base is `fad6dfe1601cfa2c83abd919066356b545cd42ba`. Work branch: `exam-x-20261026`, created from `main`. The same branch was created from harness `r1` at `6afdb0e9b800933dfbb682618b8909441f0f6495`. Existing untracked files were preserved.

The author resolved the previous context and host conflicts: 32,768-token primary probe, 16,384-token fallback for flagged CPU-pool rows; portal only for the entire exam. No Phase 1 implementation started.

## Access evidence

Local checks on 26 October 2026, completed by 00:39:30 UTC (01:39:30 Europe/Berlin):

| Command | Observed result |
|---|---|
| `ssh -G portal_zhixu` (selected fields) | `user dowling`, `hostname 100.120.160.70`, `port 22`; also confirmed directly in `~/.ssh/config` |
| `ssh -o BatchMode=yes -o ConnectTimeout=15 portal_zhixu 'hostname; id -un; printf "HOME=%s\n" "$HOME"; cat /etc/os-release; df -h; nvidia-smi; nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv; nproc; free -g; uptime; who'` | Initial sandbox attempt: `Operation not permitted`. Approved execution outside the sandbox: exit 255, `ssh: connect to host 100.120.160.70 port 22: Network is unreachable`. No remote command ran. |
| `route -n get 100.120.160.70` (outside sandbox) | Gateway `192.168.2.1`, interface `en0`; no Tailscale route observed |
| `command -v tailscale` | `/usr/local/bin/tailscale` |
| `tailscale status --json` (outside sandbox; selected non-secret status fields) | Version `1.102.4-t3caf7d9e7-g084ee3b64`; `BackendState: Stopped`; local `Online: false`; health: `Tailscale is stopped.` |

Interpretation: the local Tailscale connection is stopped and access to the configured portal address is unavailable. This does not establish any failure of portal hardware, SSH credentials, remote services, or remote networking. No VPN settings were changed.

## Phase 0 checklist

| Item | Status | Required command/evidence still pending on portal |
|---|---|---|
| 0.1 Host, OS, user, home, work directory | NOT COLLECTED | `hostname`, `id -un`, home, `cat /etc/os-release`, `df -h` |
| 0.2 GPU, memory, driver, CUDA, compute capability, processes | NOT COLLECTED | Both `nvidia-smi` queries from Phase 0 |
| 0.3 CPU and RAM | NOT COLLECTED | `nproc`, `free -g` |
| 0.4 Model storage, approximately 500 GB available | NOT COLLECTED | Candidate directory ownership and `df -h <dir>`; author confirms location |
| 0.5 GitHub, Hugging Face, OpenML reachability | NOT COLLECTED | `git ls-remote`, bounded HTTP HEAD requests from portal |
| 0.6 HF authentication and per-repository gates | NOT COLLECTED | CLI identity and repository HEAD checks; exact candidate repository identities must be verified, not guessed |
| 0.7 Python/uv, git, cmake, CUDA toolkit | NOT COLLECTED | Executable paths and versions |
| 0.8 Existing llama.cpp | NOT COLLECTED | Executable path, build/version if present |
| 0.9 GPU/CPU occupancy and exclusivity | NOT COLLECTED | `nvidia-smi`, `uptime`, `who`; a point-in-time idle check alone does not prove reservation |

No installations, downloads, licence acceptance, remote mutations, inference, or worker runs occurred. Neither model storage nor gated-licence requirements are established. The Phase 0 completion review cannot accept missing host facts; an independent reviewer is asked to verify the blocked record and access diagnosis.

## Required next step

Restore the Mac's Tailscale connection, then resume Phase 0 host collection. After collection, run the full independent review loop before the author confirms storage and accepts any required model licences. Do not advance to Phase 1 on the basis of this blocked report.
