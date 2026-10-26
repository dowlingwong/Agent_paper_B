# Independent Phase 0 review — 26 October 2026

**Current verdict:** ACCEPTED for the resumed Phase 0 read-only inventory and decision package; **STOP 0 remains in force** for author storage/licence/identity decisions. See “Resumption acceptance and STOP 0” below. The initial blocked review is preserved as history.

AI-assisted independent review. ENGINEERING_ONLY. Reviewed branch `exam-x-20261026`, base `fad6dfe1601cfa2c83abd919066356b545cd42ba`, implementation `39731ce4919d0e7bf5aa63460855ab942756bb7d`. The reviewer inspected the committed diff and independently attempted access; the implementer's conclusions were not treated as evidence of host readiness.

## Criteria and scope

`docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md:23–33` requires facts 0.1–0.9, each tied to its command, followed by independent SSH rechecks and author licence/storage decisions. Its §0 review loop (`:14`) and PLAN §10 R1-EXAM-REVIEW (`docs/r1/PLAN.md:487`) require independent acceptance. PLAN R1-EXAM-HOST (`:489`) fixes portal-only execution and the 32,768/16,384 context probes. PLAN R1-HOSTS (`:455`) is an author declaration of hardware/exclusivity, not a substitute for live inventory and occupancy evidence.

The implementation diff adds only the 43-line `docs/r1/reports/PORTAL_HOST_FACTS_20261026.md`; it contains no code or data changes. All nine inventory rows explicitly say NOT COLLECTED (`:29–37`). The opening status (`:3`) and closing boundary (`:39–43`) explicitly preserve BLOCKED / INCOMPLETE and prohibit advancement to Phase 1.

## Independent checks

Checks completed by `2026-10-26 00:40:18 UTC`, from the author's Mac. No installation, download, inference, VPN-setting change or remote mutation was performed.

| Command | Independent result |
|---|---|
| `git branch --show-current`; `git rev-parse HEAD` | `exam-x-20261026`; `39731ce4919d0e7bf5aa63460855ab942756bb7d` |
| `git diff fad6dfe..39731ce --stat`; `git diff fad6dfe..39731ce -- docs/r1/reports/PORTAL_HOST_FACTS_20261026.md` | Only the host-facts report added, 43 lines; reviewed in full |
| `git diff --check fad6dfe..39731ce`; `git merge-base --is-ancestor fad6dfe 39731ce` | Both exit 0 |
| `git -C /Users/wongdowling/Documents/autoresearch_harness branch --show-current`; corresponding `rev-parse HEAD` | `exam-x-20261026`; `6afdb0e9b800933dfbb682618b8909441f0f6495`, consistent with reported harness base |
| `ssh -G portal_zhixu 2>/dev/null` (only user/hostname/port printed) | `user dowling`, `hostname 100.120.160.70`, `port 22` |
| `ssh -o BatchMode=yes -o ConnectTimeout=10 portal_zhixu 'hostname; id -un; nvidia-smi; nproc; free -g; uptime; who'` | Sandbox attempt: exit 255, `Operation not permitted`. Separately approved execution outside sandbox: exit 255, `ssh: connect to host 100.120.160.70 port 22: Network is unreachable`. No remote command ran. |
| `route -n get 100.120.160.70` (outside sandbox) | Gateway `192.168.2.1`, interface `en0` |
| `/usr/local/bin/tailscale status --json` piped to Python selecting only `BackendState` and `Health` (outside sandbox) | `{"BackendState": "Stopped", "Health": ["Tailscale is stopped."]}`; no full status JSON printed |

The independent access failure and stopped local Tailscale state reproduce the report's diagnosis. They establish a local access blocker, not remote hardware, credential or service failure. Host commands, per-repository HF checks and remote reachability tests could not be executed. No remote host value is independently verified. The report's historical `git pull` output and absence of remote actions before review are execution-record statements, not independently replayed events; nothing in the reviewed diff contradicts them.

## Findings

**MAJOR — Phase 0 completion blocker, accurately disclosed.** Report `:29–37` records all 0.1–0.9 as NOT COLLECTED. This fails the runbook's complete-inventory and SSH-recheck requirements (`PORTAL_EXAM_RUNBOOK.md:23–33`). No claim about GPU fit, toolchain, storage, occupancy, HF authentication or licence gates can be accepted. Resolution requires restored authorised connectivity, command-backed collection of every required item, and independent rechecks. This is an external execution blocker, not a concealed report defect; it cannot be fixed by changing a status label or inferring values from PLAN.

**MINOR — None requiring correction.** The report correctly distinguishes declared exclusivity from a point-in-time occupancy check (`:37`) and does not invent gated-repository requirements (`:34`). Its proposed network restoration (`:43`) is a next step for the authorised operator, not permission for this reviewer to change VPN settings.

## Acceptance and verdict

**ACCEPTED AS A BLOCKED EXECUTION RECORD ONLY.** The committed report accurately communicates the independently reproduced access blocker and missing evidence. No report correction is required for that limited purpose.

**PHASE 0 NOT ACCEPTED / INCOMPLETE.** STOP 0 remains in force. This review does not authorise Phase 1, any installation, download, licence acceptance or model run. After access is restored, collect and independently review the full inventory before the author confirms the disk location and accepts any required gated licences. A STATUS entry must qualify acceptance as acceptance of the blocked record; it must not state that Phase 0 was completed or independently accepted.

---

## Resumption review — 26 October 2026, 01:12–01:14 UTC

The author restored connectivity and explicitly authorised resuming Phase 0 and independent review, then stopping for storage/licence decisions. This section reviews `b7fc751..d8d1035` (inventory `57d8fc4`, HF evidence `0791688`, whitespace-only cleanup `d8d1035`) and supersedes the initial completion verdict above without deleting its historical record. The same runbook Phase 0 and PLAN §10 R1-EXAM-HOST / R1-EXAM-REVIEW criteria apply; R1-EXAM-POOL and R1-EXAM-CTX remain binding. No later phase was reviewed or run.

### Independent evidence

I inspected the scripts before execution, the updated report and added transcripts/JSON. The changed files are the report and its supporting collection scripts/outputs; no experiment code, weights or data are changed. `git diff --check b7fc751..d8d1035` passed. Independently parsing all four Python files, all JSONL records (24 discovery, 28 access, 6 follow-up) and `bash -n host_inventory.sh` passed. These validate syntax/record structure, not the truth of the measurements; the live checks below establish reproducibility.

All remote checks used `ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=yes portal_zhixu`, outside the sandbox with approval. The commands read host state only. No host-key update, credentials change, VPN change, installation, build, model download or inference was performed.

| Inventory / independent commands | Result and comparison |
|---|---|
| 0.1: `date -u`, `hostname`, `id`, `printenv HOME`, `cat /etc/os-release`, `stat -c '%A %U %G %n' /home/dowling`, `test -w /home/dowling`; explicit `ls -ld` of the report's home checkout/model/work paths | `2026-10-26 01:12:29 UTC`; `TASL-2`; uid/gid 1008 `dowling`; `/home/dowling`; Ubuntu 22.04.5 LTS. Home owned by dowling, mode `drwxr-x---`, writable exit 0. Listed checkout/model/work paths absent. Confirms report `:19–20`; proposed child paths are not approved or created. |
| 0.2: `nvidia-smi`; `nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version,compute_cap --format=csv`; `nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv` | RTX 4090, 24,564/436/23,747 MiB total/used/free; driver 535.309.01; driver CUDA 12.2; capability 8.9; 0% utilisation. Xorg PID 5763 and gnome-shell PID 5925 use 401/18 MiB. No compute applications. Confirms report `:21–23`; NVIDIA's reported values are preserved without inventing a reconciliation. |
| 0.3: `nproc`, `free -b` | 32 logical CPUs; 67,116,290,048 RAM bytes total, 61,422,325,760 available; swap 2,147,479,552 total, 2,131,468,288 used. Total matches; changing available/swap counters are expected observations, not reproduction failures. |
| 0.4: `df -B1 /home/dowling`, `df -i /home/dowling`, `stat -f -c 'filesystem=%T block_size=%S blocks_available=%a' /home/dowling`, `command -v quota` | `/dev/nvme0n1p2` mounted `/`, 2,014,574,526,464 bytes total, 898,671,403,008 available, 54% used; 119,798,467 free inodes. ext2/ext3 family, block size 4096. `quota` absent. Confirms approximately 899 GB available, exceeding the inventory estimate; no reservation or per-user quota claim. |
| 0.5: bounded `git ls-remote` for public llama.cpp and the named private paper repo; private Git SSH with `StrictHostKeyChecking=yes`; `curl --connect-timeout 8 --max-time 12 -sSI` for HF, OpenML homepage and `/api/v1/json/data/31` | Public llama.cpp HEAD again `d854d98bae598388ecea1ed84396587e5edc326d`; private HTTPS fails for disabled username prompt; private SSH stops at unknown GitHub host key. HF homepage 200, OpenML homepage 200, OpenML API HEAD 412. Confirms report `:34–41`. No access configuration changed. |
| 0.6: independent anonymous Python `urllib.request` GET to `https://huggingface.co/api/models/<repo>` and HEAD to `https://huggingface.co/<repo>/resolve/<returned-sha>/config.json`, timeout 15 seconds, four workers; exact 24 repositories listed in `hf_access.py` plus `ornith-ai/Ornith-1.0-35B` | All 22 identified table repositories again return API 200, `gated=false`, and versioned config HEAD 200; licence fields and revisions match committed evidence. Both unresolved Ornith guesses return API 401 and main config HEAD 401. The extra vendor 35B repo returns 200, MIT, `gated=false`, revision `5df2ed3f675c7beaa490328cc70bb573b65fb660`. No repository was substituted. |
| 0.6 follow-up: inspected `hf_followup.py` and `ornith35_check.py` streamed to remote `python3 -`; independent presence-only check of HF token environment-variable names and conventional token files; `importlib.util.find_spec('huggingface_hub')` | Organisation listing and third-party `base_model` corroborate possible 35B mapping. Vendor config independently confirms `Qwen3_5MoeForConditionalGeneration`, 256 experts, 8 active. Neither token variable is present; neither checked token file exists; Hub module absent. No token values were read or transmitted by these reviewer checks. |
| 0.7–0.8: `command -v` for python3/python3.11/python3.12/uv/git/cmake/gcc/g++/nvcc/llama-server/huggingface-cli/hf; installed tools' `--version`; explicit `/usr/local/cuda-12.2/bin/nvcc --version`; `readlink -f /usr/local/cuda`; bounded home `find` as in `host_inventory.sh`; explicit llama path probes | Python 3.10.12; git 2.34.1; cmake 3.22.1; gcc/g++ 11.4.0. CUDA toolkit 12.2/V12.2.140 exists outside PATH; symlink resolves to cuda-12.2. No uv, Python 3.11/3.12, HF CLI or llama-server on checked PATH; no bounded-home build match. `/home/zhixu/llama.cpp` is permission denied, so its contents remain unknown. Report `:101–103` correctly limits absence claims to visible paths. |
| 0.9: `uptime`, `who`, `ps -eo user,pid,pcpu,pmem,comm --sort=-pcpu` (first 16 lines), GPU commands above | Load 1.09/1.19/1.18; 46 days uptime; zhixu graphical/tmux sessions remain. Root service lifetime CPU 35.0%; no GPU compute co-tenant at this sample. Report `:107–109` accurately retains desktop occupancy and distinguishes observation from future reservation. |

**Review execution limitation:** automatic approval review rejected execution of the original `hf_access.py` because its optional authentication path reads HF credentials and sends them to huggingface.co. I completed the public checks with an independent anonymous script that neither reads credentials nor sends Authorization, and checked credential presence separately without reading values. Nothing required for this Phase 0 inventory remains blocked by that rejection; authenticated access and legal licence approval are not established by this review. The implementer's recorded `token_present=false` is consistent with the independent absence checks.

### Resumption findings

**MAJOR — Initial missing-inventory blocker resolved for the inventory deliverable.** Live SSH now succeeds and independently reproduces the host, network, toolchain and HF observations. Every 0.1–0.9 category now has command-backed facts, including observed failures and explicit unknowns. No remaining MAJOR report correction is required.

**MINOR — No correction required; decision caveats retained.** Two Ornith candidate identities remain unresolved (report `:80–82`), and API/config access does not prove access to eventual GGUF weight objects (`:49`, `:89`). This is an explicitly disclosed author decision package, not a complete model registry or licence determination. The 35B mapping must not silently replace either candidate. CLI absence, missing Python >=3.11/uv, private Git access failure, unknown user quota and desktop occupancy are measured preparation gaps; installing or fixing them is outside this Phase 0 authorisation. A point-in-time absence of GPU compute jobs supports inventory acceptance, not future exclusivity or model fit. These limits are already stated in the report and do not require speculative repairs during read-only collection.

### Resumption acceptance and STOP 0

**ACCEPTED — Phase 0 read-only inventory and its decision package, with the disclosed unresolved identities and negative readiness checks.** This is independent acceptance of the collected inventory, beyond the initial acceptance of a blocked record. It does not assert that every candidate identity is resolved or that every tool/access check passes.

**STOP 0 remains in force.** The author must confirm storage (`/home/dowling/exam-x/{models,work}` is proposed only), approve the licence package and resolve the Ornith identities/mapping. This review does not accept licences, establish GGUF source/download access, reserve capacity, certify exclusivity or fit, or authorise Phase 1 or any later phase. The initial blocked record remains preserved above. No author gate has been crossed by this review.
