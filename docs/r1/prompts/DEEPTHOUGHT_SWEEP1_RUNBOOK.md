# Deepthought runbook — llama.cpp bring-up, liveness and C3 label sweep 1

**For:** an implementation agent running on the deepthought host, with a shell, git push to `origin`, and `tmux`.
**Written:** 25 Oct 2026 by the coordinating session (Claude), at the author's request. AI-assisted, not human review.
**Covers RUNBOOK steps:** A.11 → A.1b → A.6 → A.8 host smoke → A.7 → (A.9, author) → B.1 → B.2, plus the A.4 table build.
**Authority:** `docs/r1/PLAN.md` (§10 rows, especially the 24 and 25 Oct blocks), `docs/r1/RUNBOOK.md`, `docs/r1/STATUS.md`. If this file disagrees with PLAN, PLAN wins: stop and report the conflict.

---

## 0. Read before doing anything

1. `docs/r1/RUNBOOK.md` §1 (ground rules), §3 (hosts), §5 Phase A and B.
2. `docs/r1/PLAN.md` §10, the blocks dated 22, 23, 24 and 25 Oct.
3. The top five entries of `docs/r1/STATUS.md`.
4. Handoffs: `docs/r1/overnight/BATCH_A_24OCT_HANDOFF.md` (resume per root, watchdog, deepthought config) and `docs/r1/overnight/BATCH_B_25OCT_HANDOFF.md` (llama.cpp backend, fake server, host checklists and build recipes).
   - **Phases 0 and 1 do not depend on batch B.** If the batch B handoff is not yet on `origin/main`, read the rest and **start Phases 0 and 1 anyway**; they are self-contained in this runbook. Then STOP at the start of Phase 2 until batch B is merged and pushed.
   - From Phase 2 on, batch B is required. **Use the commands and flags documented in these handoffs and in each script's `--help`.** Where this runbook names a command and the handoff or `--help` says otherwise, the handoff and `--help` win; note the difference in your report.

The harness repository's `CLAUDE.md` is from an older project phase; ignore its plan pointers.

## 1. Ground rules (binding)

- **Work autonomously inside engineering problems (added 25 Oct, author).** Build errors, instrumentation gaps, missing log lines, flaky measurements and similar ENGINEERING_ONLY problems are yours to diagnose, fix and retry, **up to 3 attempts per item, without waiting for the author**, as long as you (a) do not relax an acceptance criterion, (b) do not change a pinned value (GGUF, build, host, nodes, configs already decided), and (c) record every attempt. A STOP that waits for the author is reserved for the cases listed in §2 and the table at the end. **When one phase is blocked, continue with any later phase that does not depend on it** (dependencies are stated per phase), and stop only when nothing independent is left.
- **Only the author decides.** You propose; you never adopt. A decision exists only as a dated row in PLAN §10. Every **STOP** below means: finish the current unit cleanly, write the report, push your branch, and wait.
- **Evidence.** Sweep 1 (Phase 7) and its audits (Phase 8) are evidence runs. They need the author's authorization note `docs/r1/authorizations/c3_sweep1_<date>.md`, written and committed by the author on `origin/main`. **You never write or commit that note.** Everything before Phase 7 is ENGINEERING_ONLY or PILOT and is labelled as such.
- **Host scope.** Work on `deepthought.etp.kit.edu` (4 × GTX TITAN X 12 GB, compute capability 5.2, driver 525.147.05, 40 CPUs, ~503 GiB RAM; STATUS 12 Oct). `deepthought2.etp.kit.edu` (2 × L40S) is **out of scope** unless a PLAN row says otherwise. Do not move work to another host on your own.
- **Exclusive host, but be careful.** The author has this host to himself, but never stop, signal or disturb a process you did not start. Kill only processes whose pid, process group and command line match your own records.
- **One backend per table (D6, D15; R1-INFER-LLAMACPP).** Every proposal in sweep 1 comes from the same llama.cpp build, the same GGUF (same sha256) and the same host type. Never mix in Ollama or another host.
- **Honesty.** Label AI-assisted work. Tick a box only when its acceptance condition was checked. A stopped run is reported as stopped. Never quote PILOT or ENGINEERING_ONLY numbers as results.
- **Repos.** Never force-push, rewrite pushed history, or delete ledgers or anything under `results/` that is already committed. Do not commit to `main` yourself except through the sweep runner's own commit mechanism (which the author has accepted). Your own docs, configs and reports go on the branch `dt-sweep1-<yyyymmdd>` and are pushed there; the coordinator merges.
- **Writing.** All documents in English. Every commit message ends with:
  ```
  Co-Authored-By: <your model name> <noreply@anthropic.com>
  ```
  (or your agent's equivalent attribution), and the commit body says "AI-assisted".
- **Long jobs** run inside `tmux` (session names prefixed `r1_`), with all output teed to a log file under the batch directory, so nothing depends on your session staying alive.
- **Reporting.** At the end of every phase, append a dated entry to `docs/r1/STATUS.md` on your branch (newest first; the format is in RUNBOOK §7) and push the branch. Detailed reports go to `docs/r1/reports/<NAME>_<yyyymmdd>.md`.

## 2. Global STOP conditions (any phase)

STOP and report if any of these happens:
- a PLAN row conflicts with this runbook, or a file, flag or script **required by the current phase** does not exist (a file needed only by a later phase is not a reason to stop earlier);
- the GPU falls back to CPU, an OOM occurs, or llama-server reports fewer layers offloaded than the model has;
- a pinned value (GGUF sha256, llama.cpp build, harness pin, paper commit) does not match;
- the runner reports a STOP, or its automatic resume/watchdog limits are exhausted;
- a test that passed on the Mac fails here for a reason that is not environmental and already accepted;
- disk on `/ceph/dwong` drops below 50 GiB free;
- anything would require root, a package manager with sudo, or contacting another person (the admin is the author's job).

---

## Phase 0 — Orientation and host census (read-only, ~15 min)

**Purpose:** know exactly what this host offers before building anything.

1. Record, into `docs/r1/reports/DT_HOST_CENSUS_<date>.md`:
   - `hostname -f`, `uname -a`, OS release, `nproc`, `free -g`, `df -h /ceph/dwong /tmp $HOME`;
   - `nvidia-smi` (full) and `nvidia-smi --query-gpu=index,name,uuid,memory.total,memory.used,compute_cap,driver_version --format=csv`;
   - who else is on the GPUs right now (`nvidia-smi --query-compute-apps=pid,used_memory --format=csv`);
   - available CUDA toolkits: `ls -d /usr/local/cuda* 2>/dev/null`, `module avail cuda 2>&1 | head`, `which nvcc; nvcc --version`;
   - compilers and build tools: `gcc --version`, `cmake --version`, `git --version`, `tmux -V`;
   - Python: `which python3 uv conda; python3 --version`;
   - network reachability (HTTP status only): github.com, huggingface.co, pypi.org, www.openml.org;
   - existing checkouts under `/ceph/dwong/` (names and their HEADs only).
2. Commit the census on your branch and push.

**Done when:** the census exists and answers: which CUDA toolkit ≤ 12.0 is usable (or none), whether huggingface.co and openml.org are reachable, and how much disk is free.

## Phase 1 — A.11: build llama.cpp and prove GPU inference on a TITAN X (~1–2 h)

**Purpose:** the sweep host must run the manager model fully on GPU. Driver 525 supports CUDA ≤ 12.0, and the TITAN X is compute capability 5.2, so llama.cpp must be built here for that target.

1. **Toolkit.** Use an installed CUDA toolkit ≤ 12.0 if one exists. If none exists, install one **in user space** under `/ceph/dwong/opt/cuda-<ver>` (NVIDIA runfile with `--toolkit --silent --toolkitpath=...`, or a conda/micromamba env with `cuda-toolkit` ≤ 12.0). No sudo. Record exactly what you used.
2. **Build.** Clone llama.cpp to `/ceph/dwong/opt/llama.cpp`, check out a **recent tagged release** (record tag and commit), and build:
   ```
   cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_CUDA_COMPILER=<toolkit>/bin/nvcc
   cmake --build build -j 32 --target llama-server llama-cli
   ```
   If the current release no longer supports compute 5.2 or the chosen toolkit, try the newest release that does, and record why. Record `build/bin/llama-server --version`.
3. **Model.** Default: the official Qwen release `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`, file for **Q4_K_M** (R1-PROPOSER-QUANT), downloaded to `/ceph/dwong/models/`. Record the URL, file name and **sha256**. If huggingface.co is unreachable, STOP: the author provides the file. (The author may instead decide to reuse the GGUF blob behind the Ollama pilots' pinned `qwen2.5-coder:7b`; follow a PLAN row if one exists.)
4. **Probe** (ENGINEERING_ONLY), one card first. Once batch B is on `origin/main`, use its probe `r1/scripts/llamacpp_probe.py` (`--expect-build`, `--expect-sha256`; it implements both offload routes, the `-ngl 0` CPU control and a non-zero exit on STOP). **Measure with the sweep's settings, `-np 1 -c 8192`** (the default is 4 slots, which changes the memory footprint), and report the `footprint_mib` to pin. The server needs `LD_LIBRARY_PATH` with `/usr/local/cuda-11.8/lib64` and `/opt/rh/gcc-toolset-13/root/usr/lib64`; export it in the shell that later launches the runner too (the runner passes its environment to `llama-server`).
   - start `llama-server -m <gguf> --host 127.0.0.1 --port <free port> -ngl 999 -c 8192` on GPU 0 (`CUDA_VISIBLE_DEVICES=0`), log to a file;
   - **record loaded-state telemetry first** (`nvidia-smi` per-process memory for the server pid, GPU utilisation), before any acceptance check;
   - **full-offload acceptance (revised 25 Oct)** — either (i) the server log, at `--verbose` / `-lv 4` if needed, reports all layers offloaded (`offloaded N/N layers`), **or**, if this build does not print that line, (ii) both: the server pid holds at least 4.5 GiB on the target GPU while loaded (the GGUF is 4.36 GiB plus KV cache), **and** a CPU control run of the same request with `-ngl 0` is at least 2× slower in generation tokens/s than the GPU run. Record which route proved it;
   - probe scripts exit non-zero on STOP, so a wrapper can never report a stopped probe as passed;
   - one `/v1/chat/completions` request with `max_tokens: 1`, then a 20-request smoke with a realistic manager-size prompt: tokens/s for prompt and generation, latency per request;
   - determinism check: the same request with the same `seed` and temperature 0.2, three times; record whether outputs are identical;
   - repeat the load on GPU 1 with a second instance while GPU 0's is running (the exclusive host could run one instance per card later; RUNBOOK open question).
5. Write `docs/r1/reports/LLAMACPP_PROBE_DT_<date>.md` with all of the above and push.

**Done when:** full offload is shown on at least one TITAN X with usable throughput.
**STOP (author decides the sweep host)** if offload fails, the build cannot target compute 5.2 with a toolkit the driver supports, or throughput is so low that sweep 1 would take more than ~5 days on one card (state your estimate: ≈ 5,800 proposals; measure the mean output tokens per manager call from the smoke). The alternatives are zhixu portal (RTX 4090) or a PLAN change; do not switch yourself.

## Phase 2 — Repositories, environment, tests, data caches (~1 h)

**Purpose:** a clean, pinned, tested checkout that the sweep runs from.

**If batch B is not yet on `origin/main` (added 25 Oct):** do Phase 2 steps 3 (environment) and 5 (data caches, including fetching `openml_climate`) and run the step 4 tests on the current `origin/main`, then do Phase 3 (it needs neither batch B nor the LLM). Redo step 1, 2 and 4 once batch B arrives. STOP before Phase 4 until then.

1. Paper repo: fresh clone (or a clean existing one) of `Agent_paper_B` at `origin/main` under `/ceph/dwong/`. It must contain the merged llama.cpp backend (commit message mentions A.10 / batch B). If it does not, STOP: the batch is not merged or not pushed yet.
2. Harness: `autoresearch_harness` at the commit pinned by the paper repo's harness pin file for the C3 sweep (see the batch A/B handoffs); verify `git rev-parse HEAD` equals the pin.
3. Environment: the harness-locked environment (Python 3.13, the lock file's versions; the 22 Oct E1 manifest recorded scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.4). Build it with `uv` under `/ceph/dwong/`, not in a home directory if home is small. Record `python -VV` and `pip freeze | grep -iE "scikit|pandas|numpy|lightgbm|langchain|openai"`. **A different scikit-learn changes tree-model metrics** (STATUS 22 Oct), so versions must match the lock exactly.
4. Tests: the paper suite (`make r1-test AR_HARNESS_ROOT=<abs path> R1_PY=<venv python>`) and the harness suite. Compare with the known baseline (paper: all pass except `test_real_runner_desktop_dryrun`; harness: the accepted environmental failure set in the handoffs). New failures that are host-specific: record and STOP if they touch the runner, the backend or the C3 pipeline.
5. Data caches: `python -m r1.noise.check_caches` for the eight D21 nodes (`digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion`) and the reserve `openml_climate`. Missing OpenML caches: fetch them here if openml.org is reachable (the node's `benchmark.py` uses `fetch_openml(data_id=..., data_home=<node>/data_cache)`); otherwise list them in your report as an author action (the author fetches on the Mac and copies the cache).

**Done when:** pins verified, tests at baseline, all nine caches report `ok`.

## Phase 3 — A.1b: reserve node noise floor (PILOT, CPU only, ~30 min)

**Purpose:** `openml_climate` backs up the pool of eight (PLAN "D21 reserve", 23 Oct; R1-C1-FLOOR, 24 Oct).

1. Confirm its `NODE_INFO` values (rows, features, minority share) against the fetched data via `check_caches`; if they differ from the provisional values in `r1/c3/features.py`, correct them on your branch with a test.
2. Run the E1 noise floor for `openml_climate` with **the same protocol as the common 22 Oct run** (30 seeds per condition, the D21 rule, the same environment versions), scripted proposer only, no LLM. Use the E1 script's documented options; the 22 Oct manifest shows the exact invocation.
3. Report the verdict under the D21 rule (qualifies / does not qualify, with mean P(wrong), number of material edits, δ_n) as an addendum to `docs/r1/reports/NOISE_FLOOR_COMMON_20261022.md` or a new `NOISE_FLOOR_CLIMATE_<date>.md`. PILOT.

**Done when:** the verdict is reported. This phase does not block Phase 4–6.

## Phase 4 — A.6: finish the deepthought sweep config (~30 min)

**Purpose:** a complete, checked config for sweep 1 on this host.

1. Fill every `TODO_VERIFY_ON_HOST` / `TODO_VERIFY_ON_DEEPTHOUGHT` value in `r1/scripts/configs/c3_sweep_deepthought.json` from Phases 0–2: llama-server binary path, build string (format `version: 0.7.0-dev (build 1, commit 620d222)`), GGUF path and sha256, `footprint_mib` from the Phase 1 probe, port (free, not 11434 or a port another process uses), GPU id/uuid (one card for sweep 1 unless a PLAN row says otherwise), worker count (leave cores for audits: start with 24 workers of 40 and say why), `allowed_hosts`.
2. Settings already decided (25 Oct, batch B): watchdog **on**; resume limit 5, watchdog restart limit 3; `min_live_nodes` = 8; the Paper A check is "not applicable" on this host. Do not change them.
3. Run the runner's `--check-config` (no placeholders allowed). Commit the config on your branch, push.

**Done when:** `--check-config` passes on this host with no placeholders.

## Phase 5 — A.8 host smoke: watchdog and resume with the real server (ENGINEERING_ONLY, ~30 min)

**Purpose:** the dry runs used a fake server; prove the real one is supervised correctly here.

1. A short real run on one node (2 roots, W = 4), backed by the real llama-server and the real GGUF.
2. While a request is in flight, kill the llama-server process **you started** (by its recorded pid). Expected: the watchdog records the loss (time, signal, last requests), restarts the instance, re-runs the affected roots whole, and the run completes.
3. Then kill the runner itself (its tmux pane) mid-run and restart it with `--start <batch>`. Expected: completed roots kept, interrupted root re-run, interruption logged.
4. Report in `docs/r1/reports/WATCHDOG_SMOKE_DT_<date>.md`. Outputs are ENGINEERING_ONLY and must not be used as labels.

**Done when:** both scenarios recover as expected.

## Phase 6 — A.7: D28 LLM liveness on the eight nodes under llama.cpp (~2–4 h)

**Purpose:** the Ollama-era liveness verdicts do not carry over to the new backend (R1-INFER-LLAMACPP). Sweep 1 may only use nodes where the manager behaves sensibly.

1. Run the D28 liveness check with the LLM manager (`langgraph`, memory on, the configured liveness size; the D28 criteria are in PLAN §10, 14 Oct, and `r1/liveness/`) on all eight D21 nodes, with the sweep config's backend, GGUF and host.
2. Write the liveness manifest and `docs/r1/reports/LIVENESS_LLAMACPP_<date>.md`: per node, each D28 criterion with observed vs required.
3. **If every node passes:** go to the Phase 6b checklist.
   **If any node fails** (digits_mlp is the known risk: on 19 Oct it made no keep after trial 1 and repeated edits): do **not** repair it and do not drop it. Write a read-only diagnosis (what the proposals look like; inert, duplicate or invalid edits; whether it is the same failure as 19 Oct) and **STOP**. The author decides: repair, or replace with `openml_climate` if Phase 3 qualified it, or run with fewer nodes.

### Phase 6b — prepare the author's decision (A.9)

Write `docs/r1/reports/SWEEP1_READINESS_<date>.md` with:
- the pinned set: paper commit, harness pin, llama.cpp tag/commit/build string, GGUF file and sha256, environment versions, host, GPU uuid;
- the node list and liveness verdicts; the config file and its hash;
- the sweep size (8 nodes × 18 instances × 2 memory modes × W = 20 ≈ 5,800 proposals) and your time estimate from Phase 1's throughput, plus the audit cost (K = 10 fresh seeds 7001–7010, 5 label + 5 evaluation, per non-inert non-duplicate proposal);
- a **draft** of the authorization text for the author to edit and commit himself (clearly marked DRAFT).

Push and **STOP**. Phase 7 starts only when `docs/r1/authorizations/c3_sweep1_<date>.md` exists on `origin/main`, committed by the author, and its content matches the pinned set in the readiness report. If anything differs, STOP and report.

## Phase 7 — B.1: C3 label sweep 1 (EVIDENCE; authorization required; ~1–5 days)

**Purpose:** the labelled proposals that C3 is trained and gated on.

1. Pull `origin/main`; verify the authorization note and that every pin still matches. Re-run `--check-config`.
2. Launch with the runner's documented prepare/start commands (batch A/B handoffs) inside `tmux` session `r1_c3_sweep1`.
3. Monitor at least every few hours: progress per node and memory mode, watchdog events, resumes, GPU memory and offload, disk. Do not intervene in a running unit. If the runner STOPs, report; resume only with the runner's own `--start <batch>` and only within its built-in limits; never patch a unit.
4. Keep a monitoring log in the batch directory; summarise it in STATUS daily while the sweep runs.
5. The runner commits and pushes its outputs as designed. Do not edit them.

**Done when:** the runner reports completion, or a STOP is reported.

## Phase 8 — B.2: fresh-seed audits (EVIDENCE, CPU)

1. Run the audits as the runner/config defines them (K = 10, seeds 7001–7010, 5 label + 5 evaluation; duplicates get no label; no-ops labelled by rule). If the runner does not include audits, use the audit step documented in `docs/r1/overnight/C3_OFFLINE_HANDOFF.md` and the 22 Oct handoff, on CPU workers on this host.
2. Same environment versions as the sweep (scikit-learn exactly as locked).

**Done when:** every eligible proposal has its audit record; counts by kind (no-op, duplicate, other) reported.

## Phase 9 — A.4: build the C3 table; final report

1. `python -m r1.c3.dataset build-sweep --index <sweep index or batch dir> --out <dir>` (verify the flags with `--help`). It refuses inconsistent sweeps; if it refuses, STOP and report why.
2. Report `docs/r1/reports/C3_SWEEP1_<date>.md`: proposals by node and memory mode, kinds, labels, duplicate rate (C1 waste), runtime, interruptions and resumes, the table's location and hash. No gate verdict: the C3 gate (B.7) is the author's decision after the offline arms (B.3–B.5).
3. STATUS entry; push your branch; **STOP**. The coordinator takes over (offline arms A0–A3 on the Mac, A5 training on zhixu portal).

---

## Summary of STOPs that wait for the author

| After | Why |
|---|---|
| Phase 1 (only if offload or build fails, or throughput too low) | Choose the sweep host |
| Phase 2 (only if caches cannot be fetched here) | Author fetches data on the Mac |
| Phase 6 (only if a node fails liveness) | Repair / replace with climate / fewer nodes |
| Phase 6b (always) | Author writes and commits the sweep-1 authorization note |
| Phase 9 (always) | Hand back to the coordinator |
