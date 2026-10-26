# Portal host facts — 26 October 2026

AI-assisted execution record. ENGINEERING_ONLY. **Phase 0 inventory independently reviewed and accepted. STOP 0 remains in force for author disk-location, licence and unresolved Ornith-identity decisions.** No exam, inference, worker run, installation or model-weight download has run.

## Scope, provenance and earlier interruption

Authority: `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` Phase 0 and PLAN §10 R1-EXAM-HOST / R1-EXAM-REVIEW. Paper branch `exam-x-20261026` was created from `main` at `fad6dfe1601cfa2c83abd919066356b545cd42ba`; harness branch of the same name from `r1` at `6afdb0e9b800933dfbb682618b8909441f0f6495`. The author instructed this session to resume Phase 0 after reconnecting Tailscale and stop at STOP 0. No Phase 1 work is authorised by this report.

The initial SSH failure (`Network is unreachable`, Tailscale `Stopped`) is preserved in paper commits `39731ce` and `b7fc751` and the initial section of `../reviews/EXAM_0_REVIEW_20261026.md`. That initial review accepted only a blocked record. Following the author's reconnection, SSH succeeded. The new inventory supersedes the old NOT COLLECTED checklist; it does not erase the interruption.

Collected on the portal at **2026-10-26 01:08:59–01:10:49 UTC** (02:08:59–02:10:49 Europe/Berlin). Portal's local display was 25 October around 18:09; UTC timestamps are used for provenance. SSH: `ssh -o BatchMode=yes -o ConnectTimeout=15 portal_zhixu`; configured target `dowling@100.120.160.70:22`.

Evidence is in [portal_host_facts_20261026/](portal_host_facts_20261026/). The shell transcript includes exact commands and exit codes; HTTP Set-Cookie headers are redacted, trailing whitespace and blank EOF lines normalised. No credential values are recorded. Small public API metadata and one small model config were read; no weights were fetched.

## 0.1–0.4 — host, GPU, CPU and storage

| Item | Observed value | Command and evidence |
|---|---|---|
| 0.1 Host, account, OS | `TASL-2`; uid/gid 1008 `dowling`; home `/home/dowling`; Ubuntu 22.04.5 LTS | `hostname`, `id`, `printenv HOME`, `cat /etc/os-release`; `host_inventory.txt` |
| 0.1 Work location | `/home/dowling` is owned by `dowling:dowling`, mode `drwxr-x---`; writable by this account. Proposed future work directory `/home/dowling/exam-x/work` is **not created or approved**. No existing paper/harness checkout or `models`/`work` directory at the checked home paths | `stat -c '%A %U %G %n' /home/dowling`; `ls -ld /home/dowling/{models,work,agent_paper_B,autoresearch_harness}`; `test -w /home/dowling` exit 0; `host_inventory.txt`, `host_followup.txt`, `access_followup.txt` |
| 0.2 GPU | One NVIDIA GeForce RTX 4090; 24,564 MiB total; 436 MiB used; 23,747 MiB free reported; compute capability **8.9** | `nvidia-smi`; `nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version,compute_cap --format=csv`; `host_inventory.txt` |
| 0.2 Driver / driver-supported CUDA | NVIDIA **535.309.01**; `nvidia-smi` CUDA **12.2**. This display is driver capability, not proof of an installed compiler; toolkit independently checked below | Same commands |
| 0.2 GPU processes | Xorg PID 5763 (root, 401 MiB) and gnome-shell PID 5925 (`zhixu`, 18 MiB); compute-app query empty; GPU utilisation 0% | `nvidia-smi`; `nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv`; `ps -p 5763,5925 -o user,pid,comm`; `host_inventory.txt`, `host_followup.txt` |
| 0.3 CPU / RAM | `nproc`: **32** logical CPUs. RAM 67,116,290,048 bytes total, 61,419,044,864 available (62/57 GiB rounded by `free -g`). Swap 2,147,479,552 total, 2,132,398,080 used | `nproc`, `free -g`, `free -b`; `host_inventory.txt` |
| 0.4 Model filesystem | `/home/dowling` on `/dev/nvme0n1p2`, mounted `/`; 2,014,574,526,464 bytes total; **898,671,263,744 bytes available (836.95 GiB, about 899 GB)**, 54% used; `df -h` rounds available to 837G | `df -h`, `df -B1 /home/dowling`; `host_inventory.txt` |
| 0.4 File count / quota scope | 119,798,480 free inodes (5% used). `stat -f` identifies ext2/ext3-family filesystem; `quota` command absent, so per-user quota not verified. Filesystem capacity exceeds the runbook's approximately 500 GB estimate; no space reservation or future capacity guarantee | `df -i /home/dowling`; `stat -f -c 'filesystem=%T block_size=%S blocks_available=%a' /home/dowling`; `command -v quota`; `host_inventory.txt`, `access_followup.txt` |

**Proposed storage for the author's decision:** `/home/dowling/exam-x/models`, with code/work under `/home/dowling/exam-x/work`. These are new child paths of the verified writable home directory and have not been created. No alternative disk was selected: `/data` and `/scratch` are absent, `/mnt` is root-owned. The GPU's reported total/used/free values are reproduced as returned rather than forced to sum; actual fit and free-margin acceptance belong to Stage A.

## 0.5 — network and repository access

| Check | Observed result | Command and evidence |
|---|---|---|
| GitHub public Git | PASS; llama.cpp HEAD returned `d854d98bae598388ecea1ed84396587e5edc326d` (observation only, **not an adopted build pin**) | `timeout 25 env GIT_TERMINAL_PROMPT=0 git ls-remote https://github.com/ggml-org/llama.cpp.git HEAD`; `host_inventory.txt` |
| Paper repo via HTTPS | NOT READY; exit 128, `could not read Username ... terminal prompts disabled` | Same `git ls-remote` on `https://github.com/dowlingwong/Agent_paper_B.git`; `host_inventory.txt` |
| Paper repo via SSH | NOT READY; exit 128, unknown GitHub ED25519 host key under strict checking. Authentication was not reached; no host key was accepted and no key/token was copied | `timeout 20 env GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=yes" git ls-remote git@github.com:dowlingwong/Agent_paper_B.git HEAD`; `access_followup.txt` |
| Hugging Face | PASS for public homepage and identified metadata/config endpoints; homepage HTTP 200 | `curl --connect-timeout 8 --max-time 20 -sSI https://huggingface.co`; Python API / HEAD checks below; `host_inventory.txt`, `hf_access.jsonl` |
| OpenML homepage | HTTP 200 at the checked time, contrary to the runbook's expected unreachability. This is only a homepage HEAD response | `curl --connect-timeout 8 --max-time 20 -sSI https://www.openml.org`; `host_inventory.txt` |
| OpenML API | HTTP **412 Precondition Failed** to a data-31 metadata HEAD probe; this neither proves working dataset downloads nor proves all OpenML traffic unreachable | `timeout 15 curl --connect-timeout 8 --max-time 12 -sSI https://www.openml.org/api/v1/json/data/31`; `access_followup.txt` |

Discrepancy documented without changing the cache plan: Phase 2 still transfers and checks the Mac's OpenML caches. Private repo access must be configured before the portal can pull merged code; Phase 0 did not alter credentials, known_hosts, SSH configuration or network settings.

## 0.6 — Hugging Face authentication, repository identities and licences

`command -v huggingface-cli`, `command -v hf` both returned no executable; `/usr/bin/python3` reports `huggingface_hub_installed=False`. Consequently `huggingface-cli whoami` could not run. The read-only fallback `hf_access.py` checked existing `HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` and conventional cached token locations (respecting HF_HOME, HF_TOKEN_PATH and XDG_CACHE_HOME): **no token found in that scope**. No identity or author licence acceptance is verified. No token was created, copied or logged.

No Phase 1 registry exists yet. The table is a **Phase 0 access inventory**, not the final registry, quant source, admissibility list or candidate selection. Public discovery queried the names in RUNBOOK Track X (`hf_discover.py` / `hf_discover.jsonl`); exact API queries, observed revisions and versioned config HEAD URLs are preserved in `hf_access.jsonl`. Representative Instruct/BF16 base repositories were used where the runbook gives a family label. Final identity and GGUF source binding remain Phase 1–2 work.

For every identified repository below, the API reported `gated=false` and a **versioned `config.json` anonymous HEAD returned 200**. A public config check is not a weight-download check or legal licence acceptance. Inaccessible guessed names are kept separate and are not classified as gated on the strength of HTTP 401 alone.

| RUNBOOK label / role | Queried base repository | Declared licence metadata | API / config HEAD |
|---|---|---|---|
| Qwen3.8-27B | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | apache-2.0 | 200 / 200 |
| Qwen3.6-27B | [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) | apache-2.0 | 200 / 200 |
| Gemma 4 31B | [google/gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it) | apache-2.0 | 200 / 200 |
| Muse Glimmer 30B | [meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) | apache-2.0 | 200 / 200 |
| OLMo 3.1 32B Instruct | [allenai/Olmo-3.1-32B-Instruct](https://huggingface.co/allenai/Olmo-3.1-32B-Instruct) | apache-2.0 | 200 / 200 |
| OLMo Think sensitivity | [allenai/Olmo-3.1-32B-Think](https://huggingface.co/allenai/Olmo-3.1-32B-Think) | apache-2.0 | 200 / 200 |
| Devstral Small 2 24B | [mistralai/Devstral-Small-2-24B-Instruct-2512](https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512) | apache-2.0 | 200 / 200 |
| Ornith-1.0-31B (unresolved guess) | [ornith-ai/Ornith-1.0-31B](https://huggingface.co/ornith-ai/Ornith-1.0-31B) | UNKNOWN | 401 / 401 at main (follow-up) |
| Qwen3.6-35B-A3B | [Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) | apache-2.0 | 200 / 200 |
| Gemma 4 26B-A4B | [google/gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it) | apache-2.0 | 200 / 200 |
| Nemotron 3.5 Lightning | [nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16) | openmdw-1.1 | 200 / 200 |
| GLM-4.7-Flash | [zai-org/GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) | mit | 200 / 200 |
| LFM2.5-24B-A2B | [LiquidAI/LFM2.5-24B-A2B](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B) | lfm1.0 | 200 / 200 |
| Laguna XS 2.1 | [poolside/Laguna-XS-2.1](https://huggingface.co/poolside/Laguna-XS-2.1) | openmdw-1.1 | 200 / 200 |
| Ornith-1.0-35B-A3B (unresolved guess) | [ornith-ai/Ornith-1.0-35B-A3B](https://huggingface.co/ornith-ai/Ornith-1.0-35B-A3B) | UNKNOWN | 401 / 401 at main (follow-up) |
| Qwen3-Coder-30B-A3B | [Qwen/Qwen3-Coder-30B-A3B-Instruct](https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct) | apache-2.0 | 200 / 200 |
| gpt-oss-20b | [openai/gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b) | apache-2.0 | 200 / 200 |
| Qwen3.5-9B | [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | apache-2.0 | 200 / 200 |
| Gemma 4 12B | [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) | apache-2.0 | 200 / 200 |
| Ornith-1.0-9B | [ornith-ai/Ornith-1.0-9B](https://huggingface.co/ornith-ai/Ornith-1.0-9B) | mit | 200 / 200 |
| Ministral 3 14B (Instruct representative) | [mistralai/Ministral-3-14B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512) | apache-2.0 | 200 / 200 |
| Community fine-tune; provenance not audited | [rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled](https://huggingface.co/rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled) | apache-2.0 | 200 / 200 |
| Community fine-tune; provenance not audited | [skiboyvv/Qwopus3.6-27B-v4](https://huggingface.co/skiboyvv/Qwopus3.6-27B-v4) | apache-2.0 | 200 / 200 |
| 7B manager anchor | [Qwen/Qwen2.5-Coder-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) | apache-2.0 | 200 / 200 |

The random-valid and scripted anchors are software baselines with no HF repo, gated weights or HF login requirement.

**Ornith identity discrepancy:** public searches found no `Ornith-1.0-31B` result. Guessed `ornith-ai/Ornith-1.0-31B` and `ornith-ai/Ornith-1.0-35B-A3B` both return API / config HEAD 401; nonexistence, private access and a licence gate cannot be distinguished from these responses. Organisation listing instead exposes `ornith-ai/Ornith-1.0-35B`. A third-party quant's `base_model` also points there. Direct vendor metadata and config confirm that repository exists, is `gated=false`, declares MIT and has `Qwen3_5MoeForConditionalGeneration` architecture (256 experts, 8 active). Config HEAD 200 at revision `5df2ed3f675c7beaa490328cc70bb573b65fb660`. This is a **possible name mapping**, not an authorised substitution. Evidence: `hf_followup.jsonl`, `ornith35_check.json`.

**Licence decision package:** no confirmed HF login gate was observed among the 22 identified repositories above (20 of the 22 candidates plus OLMo Think and the 7B anchor). Two candidate base identities remain unresolved as labelled, with the 35B mapping evidence provided separately. The author's expected Gemma/Muse/OLMo gates did not appear on the tested metadata/config endpoints; do not invent acceptance requirements from model-family names. The author still owns licence approval, especially the declared custom terms:

- Nemotron: metadata `license=other`, `license_name=openmdw-1.1`, [declared terms](https://openmdw.ai/license/1-1/).
- LFM2.5: metadata `license=other`, `license_name=lfm1.0`, [repository licence](https://huggingface.co/LiquidAI/LFM2.5-24B-A2B/blob/3fcfdbfa1a1b6d8166846a6323e69f1e1254440d/LICENSE).
- Laguna: metadata `license=openmdw-1.1`, [repository](https://huggingface.co/poolside/Laguna-XS-2.1).
- Gemma metadata declares Apache-2.0 and includes a [vendor licence link](https://ai.google.dev/gemma/docs/gemma_4_license). This report records those fields; it does not interpret or reconcile licence terms for the author.

Final GGUF source repo access and actual download authentication must be checked when the source registry is resolved in Phase 2. No licence was accepted during Phase 0.

## 0.7–0.8 — toolchain and existing llama.cpp

| Tool | Observed path and version | Command / scope |
|---|---|---|
| Python | `/usr/bin/python3`, **3.10.12**; `python3.11` and `python3.12` absent on checked PATH | `command -v`, `python3 --version`; `host_inventory.txt` |
| uv | Not on PATH, no `/home/dowling/.local/bin/uv`, no match in the bounded home scan | `command -v uv`; explicit path check; bounded `find` |
| git | `/usr/bin/git`, **2.34.1** | `git --version` |
| cmake | `/usr/bin/cmake`, **3.22.1** | `cmake --version` |
| C/C++ | `/usr/bin/gcc`, `/usr/bin/g++`, **11.4.0** | `gcc --version`, `g++ --version` |
| CUDA toolkit | `/usr/local/cuda-12.2/bin/nvcc`, **12.2 / V12.2.140**; `/usr/local/cuda` resolves to `/usr/local/cuda-12.2`; `nvcc` is absent on the non-interactive PATH | Explicit `nvcc --version`, `readlink -f`; `host_followup.txt` |
| llama.cpp / llama-server | No server on PATH or at `/usr/local/bin/llama-server`, `/usr/bin/llama-server`; no `llama.cpp` or `llama-server` found under `/home/dowling` within depth 5 (excluding .cache/.git/node_modules). Selected `/opt/llama.cpp`, `/usr/local/src/llama.cpp`, `/home/zhixu/llama.cpp` probes returned no visible match. **No build/version pin available** | `command -v llama-server`; `find` in `host_inventory.sh`; explicit path probes in follow-up |

The search is bounded to visible paths and does not establish absence throughout other users' homes or restricted directories. Python >=3.11 or uv is **not ready in the checked environment**. The compiler exists, but no CUDA build, compute-capability probe kernel or inference was run; build support will be tested in its authorised phase. No tool was installed.

## 0.9 — occupancy and exclusivity

`uptime` reported 46 days up, load **1.18 / 1.22 / 1.18** over 32 logical CPUs. `who` showed existing `zhixu` graphical and tmux sessions plus the inventory's own `dowling` SSH session. `ps -eo user,pid,pcpu,pmem,comm --sort=-pcpu` showed a root service `ninjarmm-linage` at 35.0% CPU, Xorg 1.8%, other services and desktop processes. These are `ps` lifetime averages, not a bounded live CPU utilisation measurement. `nvidia-smi` found no compute workload; Xorg and gnome-shell occupy the card as reported above.

PLAN's exclusive compute assignment is the governing allocation. The live observation supports **no GPU compute co-tenant at the sampled instant**, not an empty host or proof of a future exclusive reservation. Another user's desktop is present. No process or desktop was interrupted, and no card was reset. Occupancy and fit margin must be checked again before any later launch; the current free-memory observation is not a Stage A fit pass.

## STOP 0 — decisions and remaining boundaries

Independent reviewer verdict: **ACCEPTED — Phase 0 read-only inventory and its decision package, with the disclosed unresolved identities and negative readiness checks.** See the resumption section of [EXAM_0_REVIEW_20261026.md](../reviews/EXAM_0_REVIEW_20261026.md), reviewing implementation through `d8d1035`. No remaining MAJOR report correction or MINOR correction is required.

Stop for the author to:

1. Confirm model/code storage, proposed `/home/dowling/exam-x/{models,work}` on the observed filesystem, or specify another location.
2. Review and approve the licence package, supply any needed gated-repository access, and resolve the Ornith-31B identity / confirm the proposed Ornith-35B name mapping. No candidate is silently dropped, replaced or marked eligible.

Private GitHub pull access and a Python >=3.11 / uv environment are recorded preparation gaps. No access configuration or installation occurred. No Phase 1, model download, build, Stage A, B1 or B2 began. The independent review must be read together with this report; inventory acceptance does not accept licences, reserve disk, establish model fit or authorise the next phase.
