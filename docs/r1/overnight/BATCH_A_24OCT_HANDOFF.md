# Phase A coding batch (A.4, A.5, A.8, A.6 draft) — handoff, 24–25 Oct 2026

**ENGINEERING_ONLY. AI-assisted (Claude), implementation agent; pending review.** Nothing here is evidence. No LLM call, no GPU, no SSH, no real Ollama; workers ran on CPU only, against the HTTP-only fake server. Nothing was pushed or merged. `docs/r1/PLAN.md` and `docs/r1/RUNBOOK.md` were not edited. Nothing under `results/` or any preserved ledger was modified (tests and dry runs write to temporary directories only).

## Branches and commits

| Repository | Branch | Base | Commits (oldest first) |
|---|---|---|---|
| paper (`agent_paper_B`) | `batch-a-24oct` | `main` @ `42c93f6` | `62571dc` A.4 · `c560ef9` A.5 + A.8 · `8fe3416` A.6 draft · (this handoff + STATUS entry) |
| harness | — (not changed) | `r1` @ `7305434` | none; `r1/scripts/HARNESS_PIN_C3` unchanged |

All changed files are under `r1/`, plus this file and `docs/r1/STATUS.md`.

## Environment and how the suites were run

- Linux VM on the Mac (aarch64, 4 cores, 3 GiB). Scratch venv **`/tmp/r1scratch/venv313`** (Python 3.13.16, by `uv`), not `$HOME/scratch`: the `/sessions` disk holding `$HOME` was full (77 MB free) and the Python download failed there. Packages: the harness lock exported with `uv export --frozen --extra dev` (scikit-learn 1.8.0, numpy 2.4.4, pandas 3.0.3, pytest 9.0.3, the harness-locked set) plus `lightgbm 4.7.0` so `test_c3_arms_eval.py` does not skip.
- Each VM shell call is limited to 180 s and kills its background processes. The paper suite took 98 s at baseline but about 180 s after this batch (two new 36 s dry-run tests), so after the changes it was run as **two `make r1-test` invocations** with complementary `PYTEST_ADDOPTS="-k ..."` selections. Command: `make r1-test AR_HARNESS_ROOT=$HOME/mnt/autoresearch_harness R1_PY=/tmp/r1scratch/venv313/bin/python` (venv first on `PATH`, a git identity in the environment for the fixture commits).
- Harness: `PYTHONPATH=src python -m pytest --continue-on-collection-errors -q -p no:cacheprovider tests`. Note: the harness suite rewrites the untracked `paper/tables/artifact_completeness_report.txt` (pre-existing, ignored as instructed).

## Test results

| Suite | Before (base heads) | After (`8fe3416`) |
|---|---|---|
| paper `r1/tests` | **296 passed, 1 failed** (97 s, one run) | **327 passed, 1 failed** (325 + 2 passed over two runs; 178 s total) |
| harness `tests` | **427 passed, 9 failed, 1 error** | identical (harness unchanged; same failing set) |

- New paper tests: +31 (`test_c3_sweep_table.py` 10, `test_c3_sweep_resume.py` 16, two dry-run tests in `test_c3_sweep_dryrun.py`, `test_c3_sweep_deepthought_config.py` 3). Nothing that passed before fails.
- Pre-existing paper failure: `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` (its fixture commits only working-tree changes to `r1/`; on a clean tree `git commit` has nothing to commit). With uncommitted `r1/` changes it gets further and fails in `--prepare` (`uv sync`), as the 19 Oct handoff says. Environmental, not fixed, not skipped.
- Pre-existing harness failures (the accepted environmental set): `test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`; three in `test_artifact_completeness_and_manifest.py` (`test_cli_passes_on_real_campaigns`, `test_all_referenced_files_exist`, `test_cli_reports_all_files_exist`); five `test_kdd_paper_sections.py::test_chunk_4_{1..5}_*`; collection error `test_legacy_noop_skip.py` (unvendored claw-code).
- The dry-run scenarios `interrupt` and `watchdog` passed 3 of 3 runs each after the final change (one earlier failure was a race in my check, fixed: see A.8).

### Fail-before evidence (new tests on the previous code)

- **A.4:** all 10 tests fail on the old `dataset.py` (`AttributeError: build_from_sweep`; `build()` had no `e1_summary`).
- **A.5 / A.8:** all 18 fail with the runner, `ollama_instance.py`, fake server and launcher stashed (new tests and new dry-run driver kept). Behavioural failures among them: an interrupted sweep phase raised `PhaseInterrupted: STOP: phase sweep_none was interrupted ...; author decision required (no automatic retry)`; `port_is_free` reported a port with only TIME_WAIT connections as busy; the launcher truncated `runner.log`; the `watchdog` dry run never finished (the old runner refused the `watchdog` key, the batch timed out at 120 s); the `interrupt` dry run could not proceed. The rest fail for missing API (`resume_interrupted`, `restart_service`, `RunnerWatchdog`, `orphan_matches`, `OllamaInstance(generation=...)`).
- **A.6:** all 3 fail on the old runner: a `TODO_VERIFY` value was accepted (`DID NOT RAISE Stop`), and `--check-config` exited 0 on the draft.

## A.4 — sweep index → `dataset.build` (done, `62571dc`)

- `python -m r1.c3.dataset build-sweep --index <C3_sweep_index_<UTC>.json | batch dir> --out DIR [--paper-root DIR] [--e1-summary FILE] [--source-name MODE=NAME ...]`; Python: `build_from_sweep()`. Given the batch directory, it reads `batch_state.json` (index phase must be completed) and uses `<batch>/agent_paper_B` as the paper root (the recorded absolute index path is used if it exists, else the same file name under `results/r1/pilot/`). Given an index file under `<paper>/results/r1/pilot/`, the paper root is inferred.
- One source per memory mode, named `c3_<index UTC>_<memory mode>` (no `:`; proposal ids and `--quota` use it as separator). Rows come from the same replay and `row_of` as `build()`, so the table format is unchanged; `build.json` adds a `sweep_index` block (path, sha256, label, nodes, excluded nodes, instances, W, harness commit, audit seeds) and each source's manifest sha256, commit and collection-time noise source. Default noise: `dataset.E1_SUMMARY` (the common 30-seed run).
- Refuses: wrong index schema; recorded root failures or `collection_failures.json`; manifest memory mode / W / instances different from the index (and, for real sweep manifests with a `c3_label_sweep` block, the node list); ledger count ≠ nodes × instances; a root without `roots/<instance>.json` start files (no fallback to today's node files); an unfinished batch.
- `build()` was refactored (shared replay/write helpers) and takes an optional `e1_summary`; its three output files are byte-identical to the previous code on the pilot sources (checked by running the old and new module).
- Check on the 19 Oct pilot: fixture indexes over `dt4` (memory none) and `rerun2A` (memory on) — the same collector layout as a sweep — reproduce `build()`'s `proposals.jsonl` and `configs.json` byte for byte (12 Oct E1 noise, the build-time source). Against the 19 Oct split-recheck table on disk (`results/r1/engineering/c3_split_recheck_20261019/proposals.jsonl`, git-ignored, Mac only): identical bytes for all `dt4` and `rerun2A` rows apart from the `noop_kind` field added on 22 Oct; that test skips where the file is absent. End to end: the `interrupt` and `watchdog` dry runs build a table from the finished batch directory with one command (40 proposals, two sources).

## A.5 — resumable sweep per campaign root (done, `c560ef9`)

- Restart = run `c3_label_sweep_launch.sh --start <batch>` again on the same batch. An interrupted **sweep** phase resumes (config `resume.sweeps`, default **on**; `resume.max_restarts` 5). Liveness, preconditions and index stay STOP when interrupted (liveness is a gate: re-running it after an interruption would be a retry of a gate).
- On resume: completed roots (`roots/<instance>.json`) are kept and never re-run; every other root with work on disk is re-run **whole**: its partial directory is moved to `<work>/interrupted/<n>/roots/` (archived to `provenance/ledgers/interrupted/<n>/` with the run) and the collector runs it from trial 1. A root record truncated by the kill is moved to `<sweep>/interrupted/<n>/roots/`. Recorded root failures stand (never retried, as before).
- Logged in `<batch>/interruptions.jsonl`, the step log, `runner.log` (the launcher now appends instead of truncating) and `<sweep>/interruptions.jsonl` (committed with the sweep): schema `r1.c3_sweep_interruption/1`, phase, times, roots kept / re-run / moved, the service restart.
- Before resuming the runner: refuses while a process of an earlier runner of this batch is alive (runner, collector or liveness whose command line names the batch); stops this batch's orphaned Ollama only if pid, process group and environment (`OLLAMA_HOST` port, `OLLAMA_MODELS`) match its record; re-checks both heads, re-runs the Paper A check, card selection, digest, load probe and offload; starts a new dedicated instance (`ollama_instance_<port>_r<n>.json`, models directory reused).
- `port_is_free` now probes with `SO_REUSEADDR`: a stopped server's TIME_WAIT connections no longer block a restart on the same port; a listening socket is still refused.
- Collection gates count only the final roots; when attempts were re-run, `collection_checks.json` gains `interrupted_attempts` (root attempts, their LLM calls, interruptions).
- Fault injection (desktop dry run `--scenario interrupt`): after the first sweep has a completed root and a root in progress, the runner's whole process group is SIGKILLed (runner, collector, workers; the server survives as an orphan, as after a preemption), then `--start` again. Checked: batch finishes; completed roots' records and ledgers are byte-identical before and after; the resumed session's `jobs_before` = expected − kept; interrupted roots have a fresh ledger from budget index 1 and their partial attempt archived; the orphan was stopped (SIGTERM) and generation 1 started; the interruption is in all logs and in the sweep commit.
- **Uninterrupted runs:** the `retry` dry run with the old and the new code produces the same 40 committed files; after normalising run-specific values (paths, pids, ports, random event ids, timestamps, and which root received the dropped request) there is no difference. Literal byte identity across two runs is impossible (timestamps), so this is the comparison made.

## A.8 — Ollama runner watchdog (done, `c560ef9`; opt-in)

- Config `watchdog` (default `enabled: false`; enabled in the deepthought draft): `poll_seconds` 5, `health_timeout` 10, `unresponsive_checks` 3, `model_checks` 3, `max_restarts` 3. While a collector session runs, the runner polls its dedicated instance and detects: **server_exited** (process ended; exit status and signal name), **unresponsive** (`/api/version` failed N consecutive polls), **model_unloaded** (pinned model absent from `/api/ps` N consecutive polls: the model runner is gone while the server lives, the 14 Oct pattern).
- On a loss: stops the collector's process tree (SIGTERM, then SIGKILL), records the loss in the interruption log (detection time, last healthy poll, exit status / signal, the collector's pids, the server log's last 5 request lines and its signal / "no longer running" lines, the last LLM event with its seed and transport attempts), stops the instance (recording its return code), re-runs the Paper A check and card selection, starts a new instance and resumes per A.5. Root failure records written during that session whose last transport attempt has a transport-class error are moved to `<sweep>/interrupted/<n>/failures/` and those roots re-run whole; other failures stand. Over `max_restarts`: STOP, with the loss recorded first.
- Fake server: faults fire once per DRYRUN root (so a restarted server does not repeat them); new faults `sigterm` (the server SIGTERMs itself mid-request), `freeze` (all later requests hang) and `unload` (`/api/ps` empty, chats get the runner error); each request is printed as a `[GIN]`-style line in the serve log.
- Tests: unit (stub instance: all three kinds, thresholds, counter reset); real fake server for `sigterm`, `freeze`, `unload`; dry run `--scenario watchdog`: server SIGTERM at chat call 14 → recorded `server_exited`, `SIGTERM`, return code −15, `fault=sigterm` among the last requests, two roots re-run whole, generation 1 started, batch finished with all roots and no root failures. A first version of the check required the fatal request to be the *last* logged one and failed once (another worker's call was served between the fault and the signal); the record now keeps the last 5 requests and the check looks among them.
- Not done here: a smoke on deepthought with a real injected runner kill (RUNBOOK A.8 "then deepthought smoke"; needs the host).

## A.6 — deepthought sweep config (draft, `8fe3416`)

- `r1/scripts/configs/c3_sweep_deepthought.json`: the Ada design unchanged (eight D21 nodes, 18 instances, W = 20, both memory modes, liveness 2 × W = 10, gates, transport retry 3, audit K = 10 split 5 + 5); the manager pin is a runner constant, so it is the same digest as the Ada config. Resume on; watchdog enabled (proposal).
- **`TODO_VERIFY_ON_DEEPTHOUGHT` (7 values):** `workers`, `paper_a_check.command`, `gpu_uuid`, `ollama.binary`, `ollama.seed_models_from`, `ollama.port`, `allowed_hosts[0]`.
- Runner: `load_config` refuses any `TODO_VERIFY*` value, so a draft can never be launched. `--check-config --allow-placeholders` validates everything else and lists the open values on stderr; locally it passes (rc 0, `UNRESOLVED (7): ...`), and without the flag it refuses (rc 2). The Ada config still passes `--check-config` unchanged.
- One manager per TITAN is **not** expressible: the runner drives one dedicated instance on one card per batch (open question 3).

## Deviations

1. Scratch venv in `/tmp/r1scratch/venv313`, not `$HOME/scratch` (the `$HOME` disk was full).
2. After the changes, the paper suite was run as two `make r1-test` calls (180 s per VM call); totals are summed above.
3. The watchdog is **opt-in** (default off) so that existing configs and the existing `retry` / `permanent` dry runs behave exactly as before; resume is **on by default** (it changes only what happens on a restart of an interrupted batch, which used to be a STOP).
4. "Byte-identical to the existing pilot table": the existing 19 Oct table predates `noop_kind` (22 Oct), so identity holds apart from that field; against today's `build()` on the same inputs it is byte-identical.
5. Harness not changed, so there is no harness branch.

## Open questions for the author (design, not naming)

1. **Which host is "deepthought"?** RUNBOOK §3 gives deepthought2.etp.kit.edu with 4 × TITAN 12 GB. STATUS (12 Oct, DT0) records deepthought2 = 128 CPUs, 2 × L40S, driver 570, and deepthought.etp.kit.edu = 40 CPUs, 4 × GTX TITAN X 12 GB, driver 525.147.05. `allowed_hosts` and `gpu_uuid` depend on it.
2. **TITAN X offload is unqualified.** STATUS 12 Oct: Ollama documents driver ≥ 570 for compute capability 5.0–6.2; the TITAN X is 5.2 on driver 525, and GPU offload there was never demonstrated. The runner STOPs unless `size_vram = size`. A one-token offload probe on deepthought should come before A.7; if it fails, R1-SWEEP-HOST needs revisiting.
3. **Four TITANs with one manager each.** The runner has one dedicated instance per batch. Options: (a) four batches, one per card, with disjoint node subsets (2 nodes each), distinct ports, a configurable tmux session name in the launcher (fixed `r1_c3_sweep` today) and one index each; the A.4 adapter builds one table per index (distinct source names), concatenated afterwards; liveness then runs per shard; (b) a multi-instance runner whose collector spreads roots over instances. Both keep one host type per table. Not decided or built here.
4. **Paper A check on deepthought.** The runner requires a command; the Paper A coordination rule (19 Oct) concerns zhixu experiment. Should deepthought use a recorded "not applicable on this host" command, or a real check?
5. **Defaults.** Watchdog on by default (and in the Ada config)? Are `resume.max_restarts` = 5 and `watchdog.max_restarts` = 3 acceptable?
6. **Which units does a runner loss affect?** Implemented: roots in progress when the collector is stopped, plus roots whose failure record (written in that session) ends in a transport-class error. Roots that completed between the loss and its detection (at most one poll, 5 s) are kept: each of their calls succeeded, possibly after the bounded same-seed retry. The stricter alternative re-runs every root that completed after the last healthy poll.
7. **`min_live_nodes` = 2** (both configs) while B.1 plans eight nodes and RUNBOOK §6 says a pool below 8 is an author decision. With 2, the runner continues with fewer nodes (recorded, not silent). Set it to 8 for sweep 1?
8. **`workers` on deepthought.** Parallel roots share the one manager (`OLLAMA_NUM_PARALLEL=1`), so more workers mostly queue on it; the Ada config uses 4.
9. Known limit: an interruption during a sweep's commit/push step is not resumed automatically (local head ahead of remote → STOP at restart).

## Deepthought checklist (read-only; fills the seven TODO values)

Run on the sweep host, as `dwong`. Nothing here writes, starts a model or touches a GPU job.

```bash
# 1. Host identity -> allowed_hosts (the runner compares platform.node().split('.')[0])
hostname -f; python3 -c "import platform; print(platform.node().split('.')[0])"
nproc; free -g; uptime                                   # -> workers (cores, current load)

# 2. GPUs -> gpu_uuid (one TITAN per batch), driver vs open question 2, co-tenancy
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,driver_version,compute_cap --format=csv
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv

# 3. Ollama binary -> ollama.binary (batch 1 used a standalone runtime under its batch directory)
command -v ollama; ls -l /ceph/dwong/r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e/ 2>/dev/null
find /ceph/dwong -maxdepth 4 -path '*ollama_runtime/bin/ollama' 2>/dev/null
<binary> --version

# 4. Pinned model files -> ollama.seed_models_from (a models dir; or null to pull from the registry)
find /ceph/dwong -maxdepth 5 -path '*manifests/registry.ollama.ai/library/qwen2.5-coder/7b' 2>/dev/null
sha256sum <models dir>/manifests/registry.ollama.ai/library/qwen2.5-coder/7b
#    must print dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364 (the runner refuses otherwise)

# 5. Port -> ollama.port (integer; nothing may listen there)
ss -ltn | grep -E ':(11481|11434)\b' || echo 'no listener on 11481/11434'

# 6. Paper A on this host? -> paper_a_check.command (open question 4)
tmux ls 2>/dev/null; ps -u "$USER" -o pid,args | grep -i 'paper_a\|replay_panel' | grep -v grep

# 7. Launch prerequisites (not config keys): batch root, remotes, tools
df -h /ceph/dwong; ls -ld /ceph/dwong/tmp                  # export R1_C3_BATCH_ROOT=... (default is the Ada path /data1/dowling/tmp)
git ls-remote git@github.com:dowlingwong/Agent_paper_B.git refs/heads/main
git ls-remote git@github.com:dowlingwong/autoresearch_harness.git refs/heads/r1
command -v uv tmux

# 8. OpenML caches (git-ignored; the batch clone must get them before --start, as the dry run copies them)
ls -d /ceph/dwong/autoresearch_harness/nodes/openml_*/data_cache \
      /ceph/dwong/autoresearch_harness/experiments/r1/pilot/L8_20261009T152916Z/nodes/openml_*/data_cache 2>/dev/null
cd /ceph/dwong/agent_paper_B && AR_HARNESS_ROOT=/ceph/dwong/autoresearch_harness \
  /ceph/dwong/autoresearch_harness/.venv/bin/python -m r1.noise.check_caches \
  --nodes openml_breast_w openml_ionosphere openml_wdbc openml_credit_approval openml_sonar openml_blood_transfusion
#    loads each cache from a temporary copy with the network disabled; exit 0 = all six load and match

# 9. After filling the seven values (workers and port as integers, paper_a_check.command as argv list or string),
#    at the merged main in /ceph/dwong/agent_paper_B:
/ceph/dwong/autoresearch_harness/.venv/bin/python r1/scripts/c3_label_sweep.py \
  --config r1/scripts/configs/c3_sweep_deepthought.json --check-config
#    must exit 0 and print no "UNRESOLVED" line on stderr
```

`--check-config` does not check the host, card, binary, models or port; the runner checks those at launch (host, card margin, port free, digest, offload) and STOPs on any mismatch.
