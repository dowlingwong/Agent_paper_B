# ETP HTCondor preparation runbook — night of 13/14 November 2026

**Written 13 Nov 2026 by the chat session (Claude); AI-assisted; self-checked, not independently reviewed.** Start by having a freshly spawned independent reviewer read this file against the ETP wiki facts in §0.3. Begin after that review is *accepted*.

You are the **cluster agent** for Paper B (route R1). Your work happens on the ETP portal machines over SSH from the Mac. You may be the HoreKa agent's session or a new one. Report to the author in **Chinese**; write files and commits in **English**. The author is asleep: do not wait for answers. Put open questions into the question list (§7) and carry on with the next step.

**Goal for tonight.**
1. Move small-file directories from `/ceph/dwong` to `/work/dwong` safely.
2. Build a pinned container image.
3. Try it on the batch system with small probe jobs.
4. Record the queue times for every resource class.

No Paper B experiment, label, sweep or exam work runs on HTCondor tonight.

---

## 0. Ground rules

### 0.1 Access and windows

- The ETP machines (`deepthought.etp.kit.edu`, `portal1`, `bms1–3`) are reached over the **KIT VPN**. That is the same window as the HoreKa agent. Tailscale (TASL-2, TASL-7, used by the experiment agent) is off while the VPN is on. B1 runs unattended on TASL-7 meanwhile, so do nothing that needs Tailscale.
- Use the author's existing SSH configuration. List only the `Host` names (`grep -i '^Host ' ~/.ssh/config`) to find the alias for deepthought. **Never read key files or `~/.config/r1/secrets.env`.**
- If the VPN drops, stop at the next safe point, record where you were, and resume after reconnecting. A running batch job does not need your connection.
- Keep one SSH master connection: `ssh -fN <alias>` with `ControlPersist`, as for HoreKa. Do not open many parallel logins.

### 0.2 Standing rules

- **No deletion.** Nothing is deleted on any machine. Retire by moving into a `_to_delete/` folder next to the original, and say so in the report. Your own scratch files under `/work/dwong/htcondor_prep_20261114/` may be overwritten, never others.
- **Never touch what you did not start.** That covers other users' jobs, processes and files, and the author's running processes and jobs. Use `condor_rm` only on job IDs you submitted tonight, and only when a job of yours misbehaves.
- **Smoke first, review, then submit.** Every new job type follows three steps:
  1. a dry rendering of the JDL plus `condor_submit -dry-run`;
  2. a fresh independent reviewer checks the JDL, the executable and the plan;
  3. then one real job.
  Scale up only after that job's result is reviewed.
- **Independent review at every unit**, by a freshly spawned reviewer that gets the goal, this runbook, the inputs and the outputs, but not your conclusions. You never accept your own unit.
- **No Paper B data on the cluster tonight**: no sweep tables, no label seeds (C3 7001–7010; exam instances 9001 and up, audits 9101–9104 and 9201–9210), no exam outputs, no model weights other than the one named in §4.4.
- **Git.** Paper repository: branch `htcondor-prep-20261114` from `origin/docs/runbooks-14nov`. Never push `main`, `r1` or `exam-x-*`; never force-push. If you cannot push, write a bundle and a `READY.txt` under `~/Documents/agent_paper_B/Claude outputs/` (branch, SHA, review file).

### 0.3 Facts from the ETP wiki (check them; a mismatch is a question, not a STOP)

- **Submission.** From `bms1/2/3`, `portal1` or `deepthought` with `condor_submit`. Monitor with `condor_q`, `condor_q -analyze`, `condor_q -better-analyze`, `condor_history` and the job's event log.
- **Containers.** Jobs run in containers (`Universe = docker`, `docker_image = …`). Official images: `mschnepf/slc7-condocker`, `cverstege/alma9-gridjob`, `mschnepf/cs8-base`; any image the pool can pull may be used.
- **Resource ClassAds.** `RequestCPUs`, `RequestMemory` (MB), `request_disk` (kB), `+RequestWalltime` (s). Multi-core jobs are optimised for 1 and 8 cores.
- **Local vs remote.** `requirements = TARGET.ProvidesETPResources` gives `/work`, `/home` and `/ceph` (local ETP machines). `+RemoteJob = True` allows remote sites; remote jobs must not require `ProvidesETPResources`.
- **GPUs.**
  - `request_GPUs = N` (up to 8) needs `+RemoteJob = True`.
  - Select a type with `TARGET.GPUs_DeviceName =?= "…"`.
  - TOpAS: V100 32 GB (8), V100S (16) and A100-PCIE-40GB (24); it has `/ceph/srv` (`TARGET.ProvidesEtpCeph =?= True`).
  - NEMO2: L40S (36) and H200 (16), selected with `TARGET.CloudSite =?= "BwForCluster-Nemo2"`; it has no `/ceph/srv`.
- **Other rules.**
  - HTCondor sets `NVIDIA_VISIBLE_DEVICES` in a short UUID format; do not overwrite it.
  - `+RequestGPUMemoryMB` shares a physical GPU. **Never use it**: our runs need a whole GPU.
  - Files go via HTCondor transfer only if under 100 MB; larger data goes via `/ceph` mounts or xrootd (`root://ceph-node-j.etp.kit.edu//…`).
  - Fair-share priority applies. A job that started 6 times is held.
- **Accounting groups** (`accounting_group = …`): belle, cms.top, cms.higgs, cms.jet, cms.production, beamdump, ams. The tutorial uses `cms.higgs`. See §0.4.

### 0.4 Decisions made here (defaults; the author can change them in the morning)

- **A. Accounting group.** First check the author's own past jobs: `condor_history -limit 50 dwong -af AcctGroup AccountingGroup | sort | uniq -c`. Use the group they used. If there is none, submit without `accounting_group`. If the pool then rejects or holds the job for that reason, use the tutorial's `cms.higgs` for the CPU probes only, write that into the question list, and do not submit GPU jobs under a group the author has not used.
- **B. Image registry.** The image holds the environment only: no code, no model, no secret. Push it where the pool can pull it.
  - Prefer a registry the author is already logged in to on deepthought (check with `docker info` / `docker system info`, without reading credential files).
  - If none is usable, build and test locally on deepthought, keep the image as a `docker save` archive under `/work/dwong/htcondor_prep_20261114/images/`, and put "registry and namespace" into the question list. **Never run `docker login` yourself.**
- **C. Job limits tonight.**
  - At most 10 of your jobs queued or running at a time.
  - Walltime ≤ 3,600 s per probe.
  - GPU probes use one whole GPU each.
  - Total GPU use tonight ≤ 6 GPU-hours.

### 0.5 STOPs (stop that part, preserve, report; go on with independent parts)

- A step would delete or overwrite something not yours.
- A move would touch a directory that a running process or job uses, or that a pinned Paper B path names (§1.2).
- A copy's verification fails.
- Quota or disk space would drop below 15 % free on `/work` or `/ceph`.
- A job of yours behaves unexpectedly: runs on a GPU it did not request, writes outside its sandbox or `/work/dwong`, or exceeds its walltime. Hold it with `condor_hold <id>` and report.
- The author's or another user's job appears affected by anything you did.

## 1. Move small-file directories to `/work/dwong`

`/ceph` is slow with many small files; `/work` is better for them, and the author's `/work` quota has been tripled. Large files (models, archives, datasets kept as single large files) stay on `/ceph`.

### 1.1 Inventory (read-only)

1. Quotas and free space: `quota -s` (or the ETP quota command if `quota` is absent), `df -h /work /ceph /home`. Record them.
2. For each top-level entry under `/ceph/dwong` (one level deep), record:
   - total size;
   - file count;
   - the median and 90th-percentile file size;
   - the number of files under 64 KB;
   - whether it is a git repository or worktree, a Python venv or conda environment, a cache, data, models or results.

   Use `find -xdev`, run it at low priority (`nice -n 19 ionice -c3`), and write the results to `inventory.tsv`.
3. Which entries are in use:
   - processes: `pgrep -u dwong -a`, plus each process's `cwd` and open files under `/ceph/dwong` (`ls -l /proc/<pid>/cwd`, `ls -l /proc/<pid>/fd` for your own user only);
   - batch jobs: `condor_q dwong -af Iwd Cmd`;
   - for deepthought jobs started by other agents (C1, sweeps), check that no `tmux`, `screen` or `nohup` session of the author's runs from there.

### 1.2 Pinned paths

Paper B reports, authorizations and configs name paths under `/ceph/dwong` (for example the sweep-1 pin R1-DT-PIN-SWEEP1 on deepthought). In a clone of the paper repository, `git grep -n '/ceph/dwong'` across `origin/mac-int-20261107`, `origin/trackS-ops-20261030` and `origin/mac-b1-20261107`. Collect the named paths into `pinned_paths.txt`.

### 1.3 Plan (reviewed before anything moves)

Classify every entry in `MOVE_PLAN.md`:

| Class | Action |
|---|---|
| In use (§1.1 step 3) | **skip** |
| Named by a pinned path, or holding evidence (results, STOP scenes, captures, audit outputs, sweep ledgers) | **skip** |
| Python venv or conda environment | **skip**: relocating breaks absolute paths. Environments are rebuilt in the image (§3) |
| Large-file directories (median file ≥ 1 MB, or mostly models and archives) | **skip** |
| Git repositories and worktrees, caches (`pip`, `uv`, `huggingface` metadata, OpenML caches), source trees, small-file data | **move with a symlink back** (§1.4) |

List each entry with its size, file count and reason. A fresh independent reviewer checks the plan against `inventory.tsv` and `pinned_paths.txt` until *accepted*.

### 1.4 Move, one entry at a time

For entry `X`:

1. `rsync -aHAX --numeric-ids /ceph/dwong/X/ /work/dwong/X/`, run with `nice` and `ionice`.
2. Verify:
   - file count and total bytes are equal;
   - a SHA-256 manifest of every file is equal on both sides (`find … -type f -print0 | sort -z | xargs -0 sha256sum`);
   - for git repositories, `git -C … rev-parse HEAD`, `git status --porcelain` and `git worktree list` are equal before and after.
3. Make sure nothing has started using `X` since §1.1 (repeat that check).
4. Then: `mv /ceph/dwong/X /ceph/dwong/_to_delete/X.moved_20261114` and `ln -s /work/dwong/X /ceph/dwong/X`. The old path keeps working; the original stays complete in `_to_delete/` until the author removes it.
5. Check again: `git status` through the old path, and `ls` of the symlink.
6. Append the result to `MOVE_LOG.tsv`: entry, bytes, files, manifest SHA, verdict.

Any verification failure: do not rename. Leave both copies as they are, record it, and go to the next entry.

## 2. Pool facts (read-only)

Write everything to `POOL_FACTS.md`:

- `condor_version`;
- `condor_status -total`;
- free GPU slots on TOpAS: `condor_status -pool c03-001-140.gridka.de -constraint 'PartitionableSlot && TotalSlotGPUs>0 && State =?= "Unclaimed"' -af:t Name CPUs Memory Disk GPUs`. That is the wiki's collector; the GPU tutorial uses `f03-001-140-e.gridka.de`. Record which one answers;
- the GPU device names and driver versions as reported by the slots (`-af GPUs_DeviceName GPUs_DriverVersion CUDADriverVersion`, or whatever attributes exist);
- `condor_userprio -all` (only the author's own line and the group lines);
- the author's past accounting groups (§0.4 A).

## 3. The image

Write `r1/scripts/htcondor/docker/Dockerfile` and `r1/scripts/htcondor/docker/README.md` on your branch.

- **Base.** An AlmaLinux 9 / Rocky 9 CUDA development image, for example `nvidia/cuda:12.4.1-cudnn-devel-rockylinux9`. Choose the CUDA version from the lowest driver seen in §2: CUDA 12.4 needs driver ≥ 550; take 12.2 if a site is older. Do not use the SLC7 images: their glibc is too old for our Python 3.11 and 3.13 environments.
- **Contents.** Pinned, no network access needed at job time:
  - **Python environments, built with `uv`.**
    1. The harness environment from the harness `uv.lock` at `a3fedbb` (Python 3.13; NumPy 2.4.4). This is the environment the C3 gate and the CPU workers use.
    2. The Track S/Track P environment from the 65-package freeze (`TRACKS_HOST_FACTS_20261030` §0.5, SHA-256 `f1c818e5…`; Python 3.11).
    3. The Track P training packages from `docs/r1/overnight/trackp_code_20261026/pip_freeze_trackp-cpu.txt` plus the matching CUDA torch build. If a CUDA wheel version is not pinned anywhere, record the choice in the README as `proposed:`.
  - **llama.cpp** at `620d2225cc436ab0b001e3200e590e3b286ef9ab`, built with CUDA. Use the same build flags as `build-exam`; take the flags from TASL-7's `CMakeCache.txt` only if you can read them without SSH to TASL-7 (otherwise take them from the repo's exam documentation), with `CMAKE_CUDA_ARCHITECTURES="70;80;89;90"` (V100, A100, L40S/4090, H200). Record the binary's SHA-256. It will differ from TASL-7's binary; say so.
  - Basic tools: `git`, `rsync`, `jq`, `xrootd-client` (for `xrdcp`).
- **Not in the image:** code checkouts (they come from `/work` or by transfer), models, data, credentials.
- **Build** on deepthought (the author is in its `docker` group). Tag the image `r1-htc:20261114-<short SHA of the Dockerfile>`. Record the image ID and size.
- A fresh reviewer checks the Dockerfile and the build log until *accepted*. Then push it (§0.4 B).

## 4. Probe jobs and queue times

Work under `/work/dwong/htcondor_prep_20261114/` with one directory per probe. Each probe:
- prints `hostname`, `nproc`, the CPU model, `free -g`, `df -h` of `/work`, `/ceph`, `/ceph/srv`, `/cvmfs` and the job scratch, `env | grep -E 'NVIDIA|CUDA|_CONDOR'`, and `nvidia-smi -L` plus `nvidia-smi` (GPU jobs);
- exits 0.

Each JDL has its own `log = probe.log`, `output` and `error`, `+RequestWalltime = 1800` (3600 for §4.4), and explicit CPU, memory and disk requests.

### 4.1 First wave — official image (works before our image exists)

| ID | Image | Where | Requirements and attributes |
|---|---|---|---|
| P1 | `cverstege/alma9-gridjob` | local CPU | `requirements = TARGET.ProvidesETPResources`, 1 CPU, 2 GB |
| P2 | same | local CPU, 8 cores | as P1 with `RequestCPUs = 8`, 16 GB |
| P3 | same | remote CPU | `+RemoteJob = True`, 1 CPU, 2 GB |
| P4 | same | TOpAS A100 | `+RemoteJob = True`, `request_GPUs = 1`, `requirements = TARGET.GPUs_DeviceName =?= "NVIDIA A100-PCIE-40GB"` |
| P5 | same | TOpAS V100S | as P4 with `"Tesla V100S-PCIE-32GB"` |
| P6 | same | NEMO2 L40S | `+RemoteJob = True`, `request_GPUs = 1`, `requirements = TARGET.CloudSite =?= "BwForCluster-Nemo2" && TARGET.GPUs_DeviceName =?= "NVIDIA L40S"` |
| P7 | same | NEMO2 H200 | as P6 with `"NVIDIA H200"` |

Steps:
1. Dry-run and review all seven JDLs once, as one unit.
2. Submit P1 alone and look at its result.
3. Then submit P2–P7 together.

### 4.2 Queue-time record

Write `queue_times.tsv` with one row per job: `probe, cluster.proc, submit_utc, execute_utc, end_utc, wait_s, run_s, site, host, gpu_name, evictions, holds, exit`.

Take the times from the job event log: event 000 submit, 001 execute, 005 terminated, 004 evicted, 012 held. Fill `site` and `host` from `condor_history -af MachineAttrCloudSite0 LastRemoteHost` (or whichever attributes exist; record which ones you used).

A probe still idle after 4 hours stays queued. Note it as `>4h (still idle at <time>)`. Run `condor_q -better-analyze <id>` and save the output. Do not remove it unless it blocks your 10-job limit.

### 4.3 Second and third waves (queue-time sampling)

Resubmit P1, P3, P4 and P6 unchanged about 3 hours and about 6 hours after the first wave, if the VPN window allows. This shows how the wait varies over the night. Add the rows to the same table.

### 4.4 Our image — after §3 is accepted and pushed (or loadable)

| ID | Where | What it checks |
|---|---|---|
| I1 | local CPU, `ProvidesETPResources` | Inside our image: the three Python environments import (`python -c` with the version of each pinned package checked against the lock or freeze); `/work/dwong` and `/ceph/dwong` are readable and writable inside the job (write only under `/work/dwong/htcondor_prep_20261114/`) |
| I2 | local CPU | **Determinism across hosts.** Run the pinned worker's synthetic tabular CPU test that gave `0.922225` twice on TASL-7. The source is the reviewed one-shot command at paper commit `e5dc8c67…` (command SHA-256 `1be4ae33…`), with its scope and settings in `reviews/B1_TASL7_REAL_WORKER_RESULT_REVIEW_20261107.md` and `B1_TASL7_WORKER_ONCE_60EC_REVIEW_20261107.md` on `origin/mac-b1-20261107`. Run it in the harness environment (Python 3.13, NumPy 2.4.4, scikit-learn 1.8.0), from `git archive` copies of the exact paper and harness commits under `/work/dwong/htcondor_prep_20261114/code/`, twice in one job, with OMP, MKL and OpenBLAS threads at 1 and no GPU visible. Adapt only the paths in that command, and list every change in the review. Report both values and whether they equal `0.922225`. A difference is a finding, not a STOP: it tells us whether C3 labels can be computed on this pool |
| I3 | TOpAS A100 (`ProvidesEtpCeph`) | `torch.cuda.is_available()`, the device name, and a 1-minute matmul. Then `llama-server --version`, then load **only** `qwen25_coder_7b`'s GGUF read from `/ceph/srv` (if the author has a `/ceph/srv/dwong` directory with it) or copied by `xrdcp` into the job scratch. Record the load time, generate one short completion with `cache_prompt: false`, and stop the server inside the job. If the GGUF is not available on `/ceph/srv` or by xrootd, skip the model part and put "/ceph/srv directory and model copy" into the question list. Never copy a model from TASL-7 tonight |
| I4 | NEMO2 L40S | As I3 without the model part (no `/ceph/srv` there): only CUDA, torch and `llama-server --version` |

Same discipline: dry-run, review, I1 alone, then I2–I4. Add all rows to `queue_times.tsv`.

## 5. Optional side task — only if line W2 (§8) is in your start message

On deepthought, run `r1/scripts/w2_execute_all_identity_check.py` from `origin/mac-w2-budget-20261109` (clean detached checkout under `/work/dwong/htcondor_prep_20261114/w2/`) **read-only** on the sweep-1 `root_trials.jsonl*` files named by R1-DT-PIN-SWEEP1.
- Capture the exit code and output.
- Read nothing else from those files.
- Do not open any label table, and do not read seed-labelled analysis outputs.
- A difference is reported, not fixed.

## 6. Report and delivery

Write `docs/r1/reports/HTCONDOR_PREP_20261114.md`:
- the inventory summary;
- the move log: moved, skipped and why;
- the pool facts;
- the image (Dockerfile SHA, image ID, CUDA, llama.cpp SHA, registry state);
- the probe table with queue times: the median and the range per resource class;
- I2's determinism result;
- what works and what does not;
- a recommendation for each Paper B workload: C3 T0 audits (CPU), Track P training, T1 GPU labels, X.7.

Commit the TSV files under `docs/r1/reports/htcondor_prep_20261114/`. A fresh reviewer checks the report until *accepted*. Push, or deliver as a bundle with `READY.txt`.

Short Chinese message to the author when done or at 06:00 CET, whichever comes first. **Disconnect the VPN-dependent work by 05:30 CET**, so that the author can switch back to Tailscale for B1's end.

## 7. Question list

Write `docs/r1/reports/HTCONDOR_QUESTIONS_20261114.md`. Each question gets its context, options, a recommendation and a paste-ready answer.

## 8. Lines the author may paste into your start message

Act on a line only if it appears in the start message.

- **W2:** `W2：由 cluster agent 在 deepthought 上对 sweep 1 的 root_trials 只读运行 w2_execute_all_identity_check，结果回报；如有差异 STOP 交我决定。`
- **ACCT:** `HTCondor accounting_group 用 <组名>。`
