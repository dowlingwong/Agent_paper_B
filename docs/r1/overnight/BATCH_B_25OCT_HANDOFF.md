# Batch B (A.10: C3 label sweep on llama.cpp) — handoff, 25 Oct 2026

**ENGINEERING_ONLY. AI-assisted (Claude), implementation agent; pending review.** Nothing here is evidence. No LLM call, no GPU, no SSH, no real llama.cpp or Ollama: every server in tests and dry runs is an HTTP-only fake; workers ran on CPU in the Linux VM on the Mac. Nothing was pushed or merged. `docs/r1/PLAN.md` and `docs/r1/RUNBOOK.md` were not edited. Nothing under `results/` or any preserved ledger was touched (tests and dry runs write under `TMPDIR=/tmp/r1scratch/tmp` only).

Decision implemented: PLAN §10 R1-INFER-LLAMACPP (25 Oct) and RUNBOOK A.10. The author's answers to batch A's open questions are applied (item 7).

## Branches and commits

| Repository | Branch | Base | Commits (oldest first) |
|---|---|---|---|
| paper (`agent_paper_B`) | `batch-b-25oct` | `main` @ `3d3ec48` | `d560490` runner/instance/fake/dry run/collector (items 1–5 paper side) · `607f78e` configs, Paper A n/a, config and llama.cpp dry-run tests (items 6–7) · `adab041` load probe for A.11 (item 8 helper) · (this handoff + STATUS entry) |
| harness (`autoresearch_harness`) | `batch-b-25oct` | `r1` @ `7305434` | `264011e` llamacpp provider: `/v1` base URL, no-key placeholder, no hidden client retries (item 5) |

**The harness changed, so `r1/scripts/HARNESS_PIN_C3` now pins `264011ea2d17fa9070b8c711625db92f8409dd4b`** (was `4d68c54`, which predates the 22–23 Oct D21 node commits as well). A launch from the merged paper `main` needs the harness branch merged into `r1` and pushed first (the launcher checks out the pin from the harness remote). All paper changes are under `r1/`, plus this file and `docs/r1/STATUS.md`. The checkouts are back on `main` (paper) and `r1` (harness).

## Environment and how the suites were run

- Linux VM on the Mac (aarch64, 4 cores, 3 GiB), venv `/tmp/r1scratch/venv313` (Python 3.13.16, harness lock + lightgbm), `TMPDIR=/tmp/r1scratch/tmp` (the `$HOME` disk is full), a git identity in the environment for fixture commits.
- Paper: `make r1-test AR_HARNESS_ROOT=$HOME/mnt/autoresearch_harness R1_PY=/tmp/r1scratch/venv313/bin/python`, split with `PYTEST_ADDOPTS="-k ..."` into complementary selections (each VM call ≤ 180 s): (A) everything except the dry-run, rerun-2, resume and llama-server-instance files; (B) `rerun2 or c3_sweep_resume or llama_server_instance`; (C1, C2) the three Ollama dry runs; (D1) the llama.cpp dry run from the deepthought config; (D2) the llama.cpp interrupt and watchdog dry runs.
- Harness: `PYTHONPATH=src python -m pytest --continue-on-collection-errors -q -p no:cacheprovider tests` (it rewrites the untracked `paper/tables/artifact_completeness_report.txt`, ignored as instructed).

## Test results

| Suite | Before (`3d3ec48` / `7305434`) | After (`adab041` / `264011e`) |
|---|---|---|
| paper `r1/tests` | **327 passed, 1 failed** (269 + 55 + 3; re-run here) | **359 passed, 1 failed** (280 + 73 + 1 + 2 + 1 + 2 over six calls) |
| harness `tests` | **427 passed, 9 failed, 1 error** | **434 passed, 9 failed, 1 error** (identical failing set, diffed) |

- New paper tests: +32 (`test_llama_server_instance.py` 18, `test_e1b_collect_llamacpp.py` 4, `test_llamacpp_probe.py` 4, `test_c3_sweep_deepthought_config.py` +2 net, `test_paper_a_status.py` +1, `test_c3_sweep_dryrun.py` +3). New harness tests: +7 (`tests/stage2/test_r1_llamacpp_provider.py`). Nothing that passed before fails.
- Remaining paper failure: the known environmental `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` (uncommitted `r1/` changes make it fail in `--prepare`, a clean tree at its fixture commit; as in batch A).
- Harness failing set unchanged (accepted environmental set): ClawWorker deterministic extraction; three artifact-completeness tests; five `test_kdd_paper_sections` chunk tests; collection error `test_legacy_noop_skip.py`.
- Ollama path: all its tests and its three end-to-end dry runs (`retry` + `permanent`, `interrupt`, `watchdog`) still pass; `c3_sweep_ada.json` is unchanged and validates as `backend: ollama`.

### Fail-before evidence (new or changed tests on the previous code)

- **Harness** (`test_r1_llamacpp_provider.py` on `r1` @ `7305434`): 9 failed, 1 passed. Five fail with `openai.OpenAIError: Missing credentials` (the `llamacpp` provider could not even build its client without `OPENAI_API_KEY`); the base-URL test fails on `http://127.0.0.1:8085` ≠ `.../v1` (three sub-cases) and the default `http://localhost:8080`. **Hidden retries**, shown with a key set in the environment on the old code: a server that drops the first request saw **2 requests** while the harness logged **1 attempt with `error_class: null`** (the OpenAI client's own `max_retries=2` retried silently, outside the D26-seeded, logged retry). After: 2 requests and 2 logged attempts (`server_disconnected`, then success), same seed.
- **Paper** (code commits removed, new tests kept): `test_llama_server_instance.py` collection error (`cannot import name 'llama_server_instance'`, 18 tests); `test_e1b_collect_llamacpp.py` 3 of 4 fail (no `check_manager_model`; `pickle.loads` of the recorded `openai.APIConnectionError` raises `TypeError: APIConnectionError.__init__() takes 1 positional argument but 2 were given`; `--manager-model` unknown); the fourth (picklable exceptions re-raised unchanged) is a characterization test and passes before and after; deepthought/portal config tests 4 fail (no portal file, Ollama backend, 7 not 9 open values, no n/a command); `test_paper_a_status.py` n/a test fails (unknown flag); the three llama.cpp dry-run tests fail (no `--backend`, no fake server); `test_llamacpp_probe.py` collection error (module missing).
- **Found by the llama.cpp `permanent` dry run** before the collector fix: the collector died with `concurrent.futures.process.BrokenProcessPool: A child process terminated abruptly` — one root failing with the OpenAI client's exception broke the whole process pool, so no failure records for the other roots and no clean STOP. After the fix: 4 recorded root failures (`openai.APIConnectionError`, attempts `server_disconnected` / `connection_refused`), clean STOP as on the Ollama path.

## Items

### 1. Server instance manager — done (`d560490`)

`r1/scripts/llama_server_instance.py`, `LlamaServerInstance` (the counterpart of `ollama_instance.py`):

- argv `llama-server -m <gguf> --host 127.0.0.1 --port <p> -ngl <n> -c <ctx> --alias <alias> -np 1 [extra_args]`, started in its own session/process group, stdout+stderr to `<batch>/llama_server_<port>[_r<g>].log`. **`-np 1`** (one slot) is the flag for deterministic per-request seeds: requests are never batched with each other and each request's `seed` drives its own sampling (llama-server takes `seed` per request on `/v1/chat/completions`). The environment is stripped of every `LLAMA_ARG_*` variable and `LLAMA_API_KEY` (llama.cpp reads them as silent defaults), so the recorded argv is the whole configuration; removed names are recorded.
- Record `<batch>/llama_server_<port>[_r<g>].json`: label, backend, binary, argv, pid, pgid, port, URL and OpenAI base URL, model path, model sha256, alias, `-ngl`, `-c`, slots, GPU, removed env names, the build (`--version` output and parsed line), the server's own command line read back from `/proc` after it is healthy, start/healthy/stop times, return code. Restart generations name `_r<g>` files and never overwrite earlier ones.
- `stop()` signals only its own process group after checking the PID still leads it. **Orphans** (`orphan_matches` / `stop_orphan`): signalled only if the pid is alive, owned by this user (real uid from `/proc/<pid>/status`), still in the recorded process group, and its command line equals the recorded argv — binary (directly, or as the script of an interpreter's shebang), `--port`, `-m` path and every other argument. Anything else returns `action: none`. Tests: wrong port, wrong model, a changed argument, a wrong group, an unrelated live process of ours, and a fully matching process whose owner is another uid are all left alone; the matching one is stopped.

### 2. Pinning and checks — done (`d560490`)

- Before **every** start (first and restarts): `llama-server --version` must print exactly the pinned `version: <n> (<commit>)` line (`llamacpp.build`), and the GGUF's sha256 must equal `llamacpp.model_sha256`; otherwise STOP (each check recorded in `batch_state.json` → `llamacpp_pin_checks`, with the hashing time).
- After the start: `/health` 200 (llama-server answers 503 while loading); `/v1/models` must list the alias; `/props` must report the pinned GGUF path where the build reports `model_path`; a one-token completion (`max_tokens` 1, `seed` 0); a process on the selected card (`nvidia-smi -q -x`, as for Ollama).
- **Full GPU offload**: the server log must contain `offloaded N/N layers to GPU` with N > 0, a `CUDA<k> model buffer size` line, and no CPU-fallback line (`no usable GPU found`, `--gpu-layers option will be ignored`, `ggml_cuda_init: failed`, `no CUDA-capable device`, `CUDA driver version is insufficient`). Anything else is a STOP ("CPU fallback is never accepted"). Checked at load (`gpu_offload_load_probe[_r<g>].json`) and again after each collection (`gpu_offload_<mode>_collection.json`), which also re-checks the alias and the process.
- GPU census as before (`check_gpu` → `gpu_census.jsonl`); the co-tenancy margin uses `llamacpp.footprint_mib` (measured by the probe) instead of Ollama's 7B constant.

### 3. Runner and watchdog — done (`d560490`)

- Config `"backend": "ollama" | "llamacpp"` (default `ollama`, so `c3_sweep_ada.json` and any historical config mean what they meant) and a `llamacpp` block: `binary`, `model_path`, `model_sha256`, `model_alias`, `build`, `port`, `n_gpu_layers`, `ctx_size`, `footprint_mib`, `extra_args`, `start_timeout`. Validated: absolute paths, 64-hex sha, the version-line format, integer port ≥ 1024, `extra_args` may not repeat managed flags; pins and footprint never defaulted; `TODO_VERIFY*` values left to the placeholder check (a draft validates with `--allow-placeholders`, a launch refuses).
- Collectors and liveness get `--manager-model llamacpp/<alias>` and `LLAMACPP_BASE_URL=http://127.0.0.1:<port>/v1`. `r1/headroom/e1b_collect.py` and `r1/liveness/__main__.py` take `--manager-model` (recorded in the manifest's manager block; resume reads it from the manifest; seed policy `llamacpp_seed`); without it nothing changes. The sweep manifests record the server (port, pid, model path, sha256, alias, `-ngl`, `-c`, argv) and the build; the sweep index gains a `manager` block (backend, model, sha256, build) on the llama.cpp path only.
- Watchdog: `server_exited` (exit status / signal) unchanged; `unresponsive` = `/health` not 200 for `unresponsive_checks` polls; `model_missing` = the alias absent from `/v1/models` for `model_checks` polls. Loss handling, restarts and the A.5 resume semantics (completed roots kept, affected roots re-run whole, transport-class failures of that session moved aside) are the existing code, unchanged; the server-log request lines (`srv  log_server_r: request: POST ...`) are quoted in the loss record.
- Collector fix found on this path: `run_root` re-raises a failure whose exception cannot be pickled (the OpenAI client's `APIConnectionError`) as `RootCampaignFailed` (message names the original class and the failure record), after recording the original class, traceback and attempt log; picklable exceptions are re-raised unchanged.

### 4. Fake server for dry runs — done (`d560490`, `607f78e`)

- `r1/scripts/c3_fake_llama_server.py`: `--version` line on stderr; `/health` (503 "Loading model" for 0.3 s, then 200), `/v1/models` (alias), `/props` (`model_path`, slots, `n_ctx`), `/v1/chat/completions` (OpenAI response, `seed` logged; chat only under `/v1`); a llama.cpp-worded load log with `offloaded 29/29 layers to GPU` and a `CUDA0 model buffer` line (`C3_FAKE_LLAMA_OFFLOAD=cpu` or `=<k>` for CPU fallback / partial offload); request log lines in llama-server's format; the fake Ollama's fault injection (`drop`, `exit`, `runner_error`, `sigterm`, `freeze`, `unload`), once per DRYRUN root. Same DRYRUN guards (refused on Ada, marked root).
- `c3_sweep_dryrun.py --backend llamacpp` (or `--base-config` of a llama.cpp config): the fake behind a shebang wrapper on PATH (so the orphan check sees the recorded argv), a fixture GGUF whose sha256 and the fake's build line are the pins. Checks added for the llama.cpp path: pins verdicts, record argv/cmdline, full offload at load and after collection, alias and `model_path`, the one-token probe, `/v1/chat/completions` only, the manager model and `llamacpp_seed` in every manifest, the index `manager` block, no `LLAMA_ARG_*` reaching the server. `--base-config` now accepts a host draft: only open host values are replaced (workers, `gpu_uuid`, `allowed_hosts`, the `llamacpp` block), the Paper A n/a command runs as is, and nothing may remain open.
- Dry runs passing on the llama.cpp path (each a test): **deepthought config, `retry` + `permanent`** (89 s; drop → retried with the same seed, 1 retried call, restart refused, Paper A `not_applicable`, 29/29 layers; permanent exit → 4 recorded root failures, clean STOP); **kill-and-resume** (SIGKILL of the runner's process group mid-sweep, `--start` again: completed roots kept byte for byte, the others re-run whole, the orphaned llama-server stopped by SIGTERM after "pid, owner, process group and command line match", generation 1 pinned and fully offloaded); **watchdog** (server SIGTERM at chat call 14 → `server_exited`, `SIGTERM`, rc −15, the fatal `request: POST /v1/chat/completions ... fault=sigterm` line among the last requests, restart, affected roots re-run whole, batch finished). The interrupt scenario passed 3 of 3 extra runs.

### 5. Harness side — done (`264011e` on harness `batch-b-25oct`; pin updated)

- `providers.py`: the `llamacpp` base URL is normalised to end in `/v1` (`ChatOpenAI` appends `/chat/completions`; llama-server's OpenAI routes are under `/v1`); default `http://localhost:8080/v1`. One existing assertion (`test_provider_resolver.py`, llamacpp default) updated accordingly.
- `langchain_client.py` (`llamacpp` only): placeholder API key when none is set, and `max_retries=0` so the bounded transport retry is the only retry and every attempt is logged.
- Checked with the real `ChatOpenAI` against an HTTP stand-in: the D26 seed is in every request body and in the `llm_call` record; usage tokens are recorded; transport classification is like Ollama's: dropped connection → `server_disconnected`, refused → `connection_refused`, HTTP 5xx → `server_5xx`; `APITimeoutError` and 4xx are not retried. `transport_retry.py` needed no change (it follows the exception's cause chain to the httpx error).

### 6. Configs — done (`607f78e`)

- `r1/scripts/configs/c3_sweep_deepthought.json`: `backend: llamacpp`, the Ada design unchanged (eight D21 nodes, 18 instances, W = 20, both memory modes, liveness 2 × W = 10, gates, retry 3, audit K = 10). `n_gpu_layers` 999 (all), `ctx_size` 8192 and alias `r1-manager` are proposals (open question 2). **Nine `TODO_VERIFY_ON_HOST` values:** `workers`, `gpu_uuid`, `llamacpp.binary`, `llamacpp.model_path`, `llamacpp.model_sha256`, `llamacpp.build`, `llamacpp.port`, `llamacpp.footprint_mib`, `allowed_hosts[0]`. `--check-config` refuses (rc 2); with `--allow-placeholders` it passes and lists the nine.
- `r1/scripts/configs/c3_sweep_portal.json`: new draft for zhixu portal (RTX 4090 24 GB), the same design and the same nine open values; its comment says it is the alternative sweep host if the TITAN X cannot run llama.cpp on the GPU, and that one table never mixes hosts.
- `c3_sweep_ada.json`: unchanged (historical Ollama config).

### 7. Author's answers to batch A — applied (`607f78e`)

| Question (batch A) | Applied |
|---|---|
| Watchdog default | `watchdog.enabled: true` in both real configs (runner default stays off, so fixture/historical configs are unchanged) |
| Restart limits | `resume.max_restarts` 5, `watchdog.max_restarts` 3 (both configs) |
| `min_live_nodes` | 8 in the deepthought and portal configs (Ada config unchanged at 2) |
| Paper A check on deepthought / portal | `python3 r1/scripts/paper_a_status.py --not-applicable "<reason>"` → `verdict: not_applicable`, `"paper_a_live_waiting_for_card": false`; the runner records verdict `clear`. Guard: the mode refuses (verdict `unknown`, so the runner refuses) on the Paper A host `ucrtasl`, without a reason, or combined with `--config` |
| Interruption during commit/push | Left as an accepted STOP (no code change) |
| One manager per TITAN (question 3) | Open; nothing implemented; see "What a per-card split would need" |

### 8. Host checklists and build recipes — done (below; probe helper `adab041`)

`r1/scripts/llamacpp_probe.py` runs the runner's own server code on the host (build line, GGUF sha256, dedicated server on one card, `/health`, `/v1/models`, `/props`, a one-token completion, offload from the server log, the server's GPU MiB from `nvidia-smi`, stop) and writes `probe_<UTC>.json` plus the server log under `--out`; exit 0 only for full GPU offload (and matching pins when `--expect-*` are given). It gives the values for `llamacpp.build`, `model_sha256` and `footprint_mib`. Tested against the fake (full; CPU fallback, partial offload and a wrong pin are not accepted).

## Deviations

1. `paper_a_status.py --not-applicable` is not literally "always": it refuses on `ucrtasl` (and without a reason or with `--config`), so a host config copied to zhixu experiment can never clear a launch there.
2. `llamacpp.footprint_mib` is a ninth open value (not in the list given): the co-tenancy margin needs the llama.cpp model's measured footprint; it is read from the probe, never guessed. The placeholder marker in the deepthought config changed from `TODO_VERIFY_ON_DEEPTHOUGHT` to `TODO_VERIFY_ON_HOST`.
3. Added beyond the brief: the load probe script; the collector's picklable re-raise (a bug the llama.cpp `permanent` dry run exposed); the dry run's `--base-config` now takes host drafts.
4. In the dry-run driver, the `permanent` scenario disables the watchdog when the base config enables it (the deepthought draft does): with the watchdog on, the one-shot server exit is recovered rather than ending in the STOP that scenario checks (a first run on the deepthought draft did complete with `stop_reason: null`; not examined further). The watchdog scenario covers recovery.
5. The `interrupt` dry-run check (shared with the Ollama path) no longer requires an archived partial ledger for a re-run root that had not logged a trial when the runner was killed (a root started by a freed worker between the snapshot and the kill). One llama.cpp interrupt run failed with an assertion message of only `openml_breast_w__s105`; three assertions in that loop print just the root id, and this race is the explanation that fits the timing (two workers; a root freed by a completion starts the next one), but it was **not reproduced** in three further runs, so the cause is inferred, not shown. The runner's behaviour for such a root (move the directory, re-run whole) is unchanged; the completed-root byte-identity checks are unchanged. A root with logged trials at the kill must still have its partial ledger archived.
6. `batch_state.json` gains a `backend` key on both paths (record only); the Ollama path is otherwise unchanged (its record keys stay `ollama` / `previous_ollama`).
7. The harness fix (placeholder key, no client retries) is limited to `llamacpp`; `vllm` and `lm_studio` have the same missing-key behaviour and were not changed.

## Open questions for the author

1. **Question 3 (open): one manager per TITAN.** Not implemented. See the next section for what each option would need.
2. **Context size.** `ctx_size` 8192 is a proposal. The Ollama-era runs used Ollama's default context for the model; memory-on prompts near W = 20 have not been measured in tokens. llama-server rejects a request that exceeds the context (a non-retryable 4xx, so the root would be recorded as failed rather than silently truncated). Measure the longest liveness prompt before fixing the value.
3. **Bit-repeatability of same-seed retries.** `-np 1` plus the per-request seed gives one slot and one seed per request. llama-server's prompt cache (`cache_prompt`, on by default) can change numerics between two identical requests (different batch shapes during prompt processing). If the bounded retry must reproduce the original proposal bit for bit, the harness would send `cache_prompt: false` (an `extra_body` field); not done here.
4. **Which GGUF.** The pinned file (model, Q4_K_M, source) and its alias are the author's choice; the configs carry `r1-manager` as a neutral alias. PLAN says D28 liveness is re-run under llama.cpp; that needs the chosen GGUF.
5. **Build pin format.** The pin is the exact `version: <n> (<commit>)` line of `llama-server --version` (build number and short commit). PLAN says "build commit"; if the full 40-character commit is wanted, record `git rev-parse HEAD` of the source tree with it (the build recipe logs both).
6. **TITAN X support.** Whether the llama.cpp revision you pick still builds for sm_52 with CUDA 12.0 and runs its kernels on the TITAN X is unknown until A.11; the probe decides (full offload and a one-token answer). If not, zhixu portal is the alternative (`c3_sweep_portal.json`), as a whole-table choice.
7. **Harness merge.** `264011e` must be merged into harness `r1` and pushed before a launch from the merged paper `main` (pin file). Should `vllm` / `lm_studio` get the same key/retry treatment?

## What a per-card split would need (question 3; not built)

The runner drives one dedicated server on one card per batch. Two ways to use four TITANs, both one host type and one pin (D6, D15):

- **(a) Four batches, one per card.** Needs: a configurable tmux session name in the launcher (fixed `r1_c3_sweep` today; e.g. `R1_C3_SESSION`) and distinct batch directories; four configs (or one config plus a per-shard override) with distinct `gpu_uuid` and `llamacpp.port` and disjoint node subsets (2 nodes each); per-shard liveness, with the D28 "pool < 8" rule (`min_live_nodes`) applied to the union of the four shards by the operator or a small aggregation step, since each shard sees only 2 nodes (`min_live_nodes` would be 2 per shard); `workers` per shard ≈ a quarter of the usable cores; the sha256 pass reads the GGUF four times (fine on 40 cores). Afterwards four indexes: the A.4 adapter builds one table per index (distinct source names), concatenated. The restart/watchdog logic is per batch already.
- **(b) One multi-instance runner.** Needs: N `LlamaServerInstance`s (one per card, distinct ports); the collector must assign each root a base URL (today one `LLAMACPP_BASE_URL` per collector process: e.g. a per-job environment in `run_root`, or N collectors over a node or instance partition); the watchdog over N instances with per-instance loss, restart and "affected roots" bookkeeping (roots bound to the lost instance); one index. More code, one table directly.
- Not an option: one llama-server with `-np 4` on one card, which batches requests together (determinism stance of `-np 1`), or one server split over four cards (12 GB each is enough for a 7B Q4_K_M; splitting adds inter-card traffic for no gain).

## Host checklist — deepthought (read-only; fills the nine TODO values)

Host per the brief: `deepthought.etp.kit.edu` (4 × GTX TITAN X 12 GB, compute capability 5.2, driver 525.147.05, 40 CPUs; STATUS 12 Oct). Run as `dwong` in a shell on the host. Nothing here starts a server, loads a model or touches a GPU job; the only file written is the log. Paths under `/ceph/dwong` follow batch 1; adjust if your layout differs.

```bash
S=/ceph/dwong/llamacpp_setup; mkdir -p "$S/logs"
LOG="$S/logs/checklist_deepthought_$(date -u +%Y%m%dT%H%M%SZ).log"
{
echo "== 1. host identity -> allowed_hosts (runner compares platform.node().split('.')[0])"
hostname -f; python3 -c "import platform; print(platform.node().split('.')[0])"
echo "== 2. CPUs, memory, load -> workers"
nproc; free -g; uptime
echo "== 3. GPUs -> gpu_uuid (one TITAN per batch); driver and the highest CUDA it supports (header)"
nvidia-smi
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
echo "== 4. toolchain for the build (CUDA <= 12.0 for driver 525; gcc <= 12 for CUDA 12.0)"
command -v nvcc && nvcc --version; ls -d /usr/local/cuda* /opt/cuda* 2>/dev/null
(module avail cuda) 2>&1 | head -20
gcc --version | head -1; g++ --version | head -1; ls /usr/bin/g++-* 2>/dev/null
cmake --version | head -1; git --version; ldd --version | head -1; python3 --version
df -h /ceph/dwong
echo "== 5. network for downloads (toolkit, source, GGUF)"
for u in https://github.com https://developer.download.nvidia.com https://huggingface.co; do
  printf '%s ' "$u"; curl -sS -o /dev/null -w '%{http_code}\n' --max-time 10 "$u" || echo unreachable; done
echo "== 6. existing llama.cpp builds -> llamacpp.binary"
command -v llama-server; find /ceph/dwong -maxdepth 5 -name llama-server -type f 2>/dev/null
echo "== 7. GGUF files -> llamacpp.model_path (sha256 is printed by the probe, step 3 of the recipe)"
find /ceph/dwong -maxdepth 5 -name '*.gguf' -size +500M -printf '%p %s bytes\n' 2>/dev/null
echo "== 8. port -> llamacpp.port (nothing may listen there)"
ss -ltn | grep -E ':(18481|18482|18483|18484)\b' || echo 'no listener on 18481-18484'
echo "== 9. Paper A: the config's not-applicable command (from the merged paper main)"
cd /ceph/dwong/agent_paper_B && git log --oneline -1 && \
  python3 r1/scripts/paper_a_status.py --not-applicable "check from deepthought" | tail -1
echo "== 10. launch prerequisites (as in batch A): batch root, remotes, tools, OpenML caches"
ls -ld /ceph/dwong/tmp; command -v uv tmux
git ls-remote git@github.com:dowlingwong/Agent_paper_B.git refs/heads/main
git ls-remote git@github.com:dowlingwong/autoresearch_harness.git refs/heads/r1
ls -d /ceph/dwong/autoresearch_harness/experiments/r1/pilot/L8_20261009T152916Z/nodes/openml_*/data_cache 2>/dev/null
} 2>&1 | tee -a "$LOG"
echo "log: $LOG"
```

Fill-in map: `allowed_hosts[0]` ← 1; `workers` ← 2 (roots share one manager, so more workers mostly queue on it; batch A's Ada config used 4); `gpu_uuid` ← 3 (an idle TITAN); `llamacpp.binary` ← recipe step 2; `model_path`, `model_sha256`, `build`, `footprint_mib` ← the probe JSON (recipe step 3); `port` ← 8. Then, at the merged main: `python3 r1/scripts/c3_label_sweep.py --config r1/scripts/configs/c3_sweep_deepthought.json --check-config` must exit 0 with no `UNRESOLVED` line (with the harness venv's python if `python3` is older than 3.9).

## Build recipe — llama.cpp with CUDA for the TITAN X (sm_52), then the one-token probe

Every step appends to a log under `$S/logs`. Steps 1–2 write only under `$S`.

```bash
S=/ceph/dwong/llamacpp_setup; mkdir -p "$S/logs"; T=$(date -u +%Y%m%dT%H%M%SZ)

# 1. CUDA toolkit <= 12.0 (the 525 driver supports up to CUDA 12.0; 12.0 still targets sm_52).
#    Skip if step 4 of the checklist found a 12.0 (or 11.x) nvcc. Otherwise a user-space, toolkit-only install
#    (no driver, no root). Check the file name on NVIDIA's CUDA Toolkit Archive page for 12.0.1 first.
{
cd "$S"
wget -nv https://developer.download.nvidia.com/compute/cuda/12.0.1/local_installers/cuda_12.0.1_525.85.12_linux.run
sha256sum cuda_12.0.1_525.85.12_linux.run
mkdir -p "$S/tmp"
sh cuda_12.0.1_525.85.12_linux.run --silent --toolkit --toolkitpath="$S/cuda-12.0" --tmpdir="$S/tmp"
"$S/cuda-12.0/bin/nvcc" --version
} 2>&1 | tee -a "$S/logs/cuda_toolkit_$T.log"

# 2. llama.cpp from source at a recorded revision, server only, CUDA for sm_52.
#    If gcc is newer than 12, add -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-12 (or g++-11).
#    If cmake asks for libcurl, add -DLLAMA_CURL=OFF.
{
export CUDA_HOME="$S/cuda-12.0" PATH="$S/cuda-12.0/bin:$PATH"
git clone https://github.com/ggml-org/llama.cpp "$S/llama.cpp" || git -C "$S/llama.cpp" fetch --tags
cd "$S/llama.cpp" && git checkout <REVISION_CHOSEN_BY_THE_AUTHOR> && git rev-parse HEAD && git describe --tags --always
cmake -S . -B build-cuda120-sm52 -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52 \
      -DCMAKE_CUDA_COMPILER="$CUDA_HOME/bin/nvcc" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_BUILD_RPATH="$CUDA_HOME/lib64"
cmake --build build-cuda120-sm52 --config Release -j 16 --target llama-server
ldd build-cuda120-sm52/bin/llama-server | grep -Ei 'cuda|cublas|not found'   # no "not found" lines
build-cuda120-sm52/bin/llama-server --version
} 2>&1 | tee -a "$S/logs/llamacpp_build_$T.log"
#    The "version: <n> (<commit>)" line printed last is llamacpp.build; the binary path is llamacpp.binary.
#    The build RPATH points at the user-space toolkit's libcudart/libcublas, so the runner (which sets no
#    LD_LIBRARY_PATH) can start it; keep $S/cuda-12.0 in place.
#    Do not pass -fa on: flash attention needs a newer GPU than compute capability 5.2.

# 3. One-token load probe of the pinned GGUF on ONE idle TITAN (the runner's own checks; stops its server).
#    Run in the merged paper checkout; output: $S/logs/probe/probe_<UTC>.json + the server log.
cd /ceph/dwong/agent_paper_B && \
python3 -m r1.scripts.llamacpp_probe \
  --binary "$S/llama.cpp/build-cuda120-sm52/bin/llama-server" \
  --model <ABSOLUTE_PATH_TO_THE_Q4_K_M.gguf> --gpu <GPU-UUID of an idle TITAN> --port 18481 \
  --ctx 8192 --ngl 999 --out "$S/logs/probe" 2>&1 | tee -a "$S/logs/probe_console_$T.log"
#    Accept only "VERDICT FULL_GPU_OFFLOAD" (exit 0): offloaded N/N layers, a CUDA0 model buffer, no CPU fallback.
#    From probe_<UTC>.json: build.version_line -> llamacpp.build; model_sha256 -> llamacpp.model_sha256;
#    server_gpu_mib -> llamacpp.footprint_mib. Anything else: RUNBOOK A.11 says the author picks another host.
```

## Host checklist and build recipe — zhixu portal (alternative sweep host)

One RTX 4090 24 GB (compute capability 8.9), exclusive (R1-HOSTS). Its driver, CUDA, OS, paths and SSH alias are not recorded in this repository; set `S` to a directory you own there (`<PORTAL_WORKDIR>` below). Same rules: read-only checklist (log only), then the build and the probe, each logging.

```bash
S=<PORTAL_WORKDIR>/llamacpp_setup; mkdir -p "$S/logs"
LOG="$S/logs/checklist_portal_$(date -u +%Y%m%dT%H%M%SZ).log"
{
hostname -f; python3 -c "import platform; print(platform.node().split('.')[0])"   # -> allowed_hosts
nproc; free -g; uptime                                                              # -> workers
nvidia-smi                                                                          # driver; header = highest CUDA supported
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,driver_version,compute_cap --format=csv   # -> gpu_uuid
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv
command -v nvcc && nvcc --version; ls -d /usr/local/cuda* 2>/dev/null; gcc --version | head -1; cmake --version | head -1
df -h "$S"; command -v llama-server uv tmux; find "$HOME" -maxdepth 4 -name '*.gguf' -size +500M 2>/dev/null
for u in https://github.com https://developer.download.nvidia.com https://huggingface.co; do
  printf '%s ' "$u"; curl -sS -o /dev/null -w '%{http_code}\n' --max-time 10 "$u" || echo unreachable; done
ss -ltn | grep -E ':18481\b' || echo 'no listener on 18481'                       # -> llamacpp.port
} 2>&1 | tee -a "$LOG"; echo "log: $LOG"
```

Build: as for deepthought with `-DCMAKE_CUDA_ARCHITECTURES=89` and any CUDA toolkit the driver supports (12.x; the `nvidia-smi` header gives the maximum), e.g. `build-cuda-sm89`, logged to `$S/logs/llamacpp_build_<UTC>.log`; then the same probe with `--binary "$S/llama.cpp/build-cuda-sm89/bin/llama-server"` and the 4090's UUID, accepting only `FULL_GPU_OFFLOAD`. The paper checkout path in the probe command and the `allowed_hosts` / batch root follow from the checklist. If both hosts pass, note that a labelled table still uses one host type only.

## Files

- New: `r1/scripts/llama_server_instance.py`, `r1/scripts/c3_fake_llama_server.py`, `r1/scripts/llamacpp_probe.py`, `r1/scripts/configs/c3_sweep_portal.json`, `r1/tests/test_llama_server_instance.py`, `r1/tests/test_e1b_collect_llamacpp.py`, `r1/tests/test_llamacpp_probe.py`; harness `tests/stage2/test_r1_llamacpp_provider.py`.
- Changed: `r1/scripts/c3_label_sweep.py`, `r1/scripts/c3_sweep_dryrun.py`, `r1/scripts/paper_a_status.py`, `r1/scripts/configs/c3_sweep_deepthought.json`, `r1/scripts/HARNESS_PIN_C3`, `r1/headroom/e1b_collect.py`, `r1/liveness/__main__.py`, `r1/tests/test_c3_sweep_deepthought_config.py`, `r1/tests/test_c3_sweep_dryrun.py`, `r1/tests/test_paper_a_status.py`; harness `src/autoresearch/llm/providers.py`, `src/autoresearch/llm/langchain_client.py`, `tests/test_provider_resolver.py`.
- Unchanged by design: `r1/scripts/ollama_instance.py`, `r1/scripts/c3_fake_ollama.py` (imported by the llama.cpp fake for its fault markers and DRYRUN proposals), `r1/scripts/c3_label_sweep_launch.sh`, `r1/scripts/configs/c3_sweep_ada.json`.
