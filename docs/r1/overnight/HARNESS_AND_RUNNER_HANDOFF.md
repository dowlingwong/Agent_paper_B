# Harness changes and C3 label-sweep runner — overnight handoff (19 Oct 2026)

**ENGINEERING_ONLY. AI-assisted (Claude).** Nothing here is evidence. No LLM, GPU, SSH or real Ollama was used; workers ran on CPU only in tests and the desktop DRYRUN. Nothing was pushed. `docs/r1/STATUS.md` and `docs/r1/PLAN.md` were not edited.

## Branches and commits

| Repository | Worktree / branch | Base | Commits (oldest first) |
|---|---|---|---|
| harness | `.claude-worktrees/r1-c3-prep`, branch `overnight/r1-c3-prep` | `r1` @ `411c605` | `6d22bf4` D4 action versions · `74463f1` split default · `4d68c54` transport retry |
| paper | `.claude-worktrees/c3-sweep-runner`, branch `overnight/c3-sweep-runner` | `main` @ `a312f89` (fast-forwarded) | `d9297a1` collector observability · `cda8030` dedicated Ollama · `2ae662a` C3 runner + launcher · `9e276b7` dry run · (this handoff) |

`r1/scripts/HARNESS_PIN_C3` = `4d68c54875654cf9986daa1cf36d609adb48ef45` (harness branch head).

## 1. Harness — D4 action versions (`6d22bf4`)

New `src/autoresearch/control_plane/action_versions.py`; changes in `campaign.py`, `decision.py`, `snapshot.py`; tests `tests/stage2/test_r1_d4_action_versions.py` (18).

- **Bayes threshold keep rule** `bayes_threshold/v1` (run-free, default off): keep iff Δ̂ > t*, t* = −μσ²/τ². `run_real_campaign(..., action_versions=ActionVersions.new_campaign(keep_rule="bayes_threshold/v1"), keep_prior=...)`, where `keep_prior` is a constant `KeepPrior(mu, tau, sigma[, sigma_t|sigma_s], source)` or a callable receiving the leak-safe E2 `ControlView` (per-proposal prior). The rule (version, prior, threshold, Δ̂, default decision, applied) is recorded in the `decision_made` event and in `extra.keep_rule`. Invalid trials stay `failed_invalid`; the first valid metric is kept as before.
- **Verify posterior-mean response** `posterior_mean/v1`: keep iff E[Δ | Δ̂, D̄] > 0 under T2 §1 with the campaign split policy (`"fixed"` needs σ_t or σ_s; σ_t = 0 degenerates to Δ̂ only). Checked against numpy Gaussian conditioning (50 random cases, both policies). `mean_delta/v1` ("D̄ > 0") stays.
- **verify_failed**: `original_stands/v1` (new-campaign default) — when every pair fails the original decision stands, response `verify_failed`, `verify_failed: true`, incumbent not marked verified. `veto/v1` is the historical behaviour.
- **Backward compatibility.** `run_real_campaign` without `action_versions` is byte-for-byte the old path (verify split defaults to `"fixed"`; no new record/event keys). `ActionVersions.legacy()` reproduces it exactly (test compares records of a verify campaign with `None` and with `legacy()`). `ActionVersions.from_manifest()` reads a manifest without `action_versions` as legacy (top-level `verify_split_policy` honoured, default `"fixed"`). Snapshots write `action_versions` only when declared; `resume_campaign` re-applies them (test: verify-failed policy on resume) and accepts `keep_prior`. Missing prior or a split contradicting the declaration fails at campaign start, never mid-trial.

## 2. Harness — verify split default `"vary"` (`74463f1`)

`declare_new_campaign(manifest)` writes `verify_split_policy: "vary"` and the full `action_versions` (split `vary`, `original_stands/v1`, `default/v1`, `mean_delta/v1`) into a **new** manifest and refuses to rewrite one that declares something else. `resolve_verify_split_policy()` / `from_manifest()` / `read_snapshot()` read a missing field as `"fixed"`. Tests: `tests/stage2/test_r1_split_default.py` (4). The existing harness test asserting the old `run_real_campaign` default `"fixed"` still passes, by design.

## 3. Harness — bounded LLM transport retry (`4d68c54`)

New `src/autoresearch/llm/transport_retry.py`; `LangGraphManager(transport_retry=...)`; `campaign._propose_logged`. Tests `tests/stage2/test_r1_transport_retry.py` (11), including a real `ChatOllama` client against a local HTTP server that drops the first request.

- Up to 3 attempts, backoff 2 s / 4 s; retried classes: `runner_terminated` ("llama runner process no longer running"), `unexpected_eof`, `connection_refused`, `connection_reset`, `connection_aborted`, `server_disconnected` (httpx `RemoteProtocolError`), `connect_error`, `read_error`/`write_error`, `server_5xx`. Timeouts, 4xx and everything else are not retried (`non_retryable`, raised at once).
- Same messages and same D26 seed on every attempt (asserted for stubs and over HTTP).
- Every attempt (index, error class, seconds, error text) goes into the `llm_call` payload as `transport_attempts` with `transport_retry_policy: bounded_transport_retry/v1`. A final failure re-raises the original exception carrying the attempt log and seed; `run_real_campaign` first emits an `llm_call_failed` event (not an `llm_call`, so call/parse-failure counters are unaffected).
- Parse failures happen after a successful response and are never retried by this mechanism (test).
- Compatibility: `transport_retry=None` / `LEGACY_POLICY` (1 attempt) keeps the old payload and behaviour. The harness class default is 3 attempts, but the paper collector passes the manifest's value and **a manifest without `manager.transport_max_attempts` means 1 attempt** (`e1b_collect.transport_policy`), so historical manifests replay unchanged.

## 4. Paper — collector observability (`d9297a1`)

`r1/headroom/e1b_collect.py`, `r1/scripts/deepthought_batch1_resume.py`, `r1/liveness/__main__.py`; tests `r1/tests/test_collector_observability.py` (7).

- A failed leaf keeps its historical fields (`integrity`, `error` = `repr(exc)`, the reset `cost_worker_runs`) and adds `error_class`, `error_message`, `traceback`, `failed_utc` (UTC, microseconds), `failure_stage`, partial ledger/event paths and record count, and — when the harness attached them — `transport_attempts` and `llm_seed`. Successful leaves are unchanged.
- A failed root campaign or start audit writes `failures/<kind>__<instance>.json` before the exception propagates. Opt-in `--root-failures record` keeps the other roots running; a recorded failed root is never retried automatically on `--resume`.
- The shared `collect()` writes `collection_failures.json` before its "collection failures" gate raises (old-format leaves are marked "no failure timestamp recorded", never given an invented time).
- Roots-only mode for C3: `--roots-only` (empty `--points`, `--reps 0`), `--audit-seeds 0` skips start audits, `--new-campaign-versions` (calls `declare_new_campaign`; requires `--verify-split-policy vary`), `--transport-max-attempts`, `--extra-manifest`. The manifest is written up front only for these new-style runs; default invocations behave as before. `r1.liveness --run` gains `--transport-max-attempts` and persists root failures.

## 5. Paper — dedicated Ollama instance per batch (`cda8030`)

`r1/scripts/ollama_instance.py` (`OllamaInstance`): own `OLLAMA_HOST` port (refuses a port in use), `OLLAMA_MODELS` under the batch directory (optionally seeded from a pinned models directory by hard links, else a copy; otherwise `ollama pull`), `OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_NUM_PARALLEL=1`, `CUDA_VISIBLE_DEVICES=<selected uuid>`, own process group, health check on `/api/version`, record `<batch>/ollama_instance_<port>.json` (pid, pgid, port, models dir, version, start/stop times, return code), `stop()` signals only its own process group after checking it. `r1/scripts/c3_fake_ollama.py` is the HTTP-only fake (honours `OLLAMA_HOST`, refuses on Ada and outside a marked DRYRUN directory, fault injection `drop` / `runner_error` / `exit` over chat calls). Tests `r1/tests/test_ollama_instance.py` (6), including "stopping one instance never touches another".

## 6. Paper — C3 label-sweep runner (`2ae662a`)

`r1/scripts/c3_label_sweep.py`, `r1/scripts/c3_label_sweep_launch.sh` (`--prepare` / `--start`, tmux `r1_c3_sweep`), `r1/scripts/c3_prepare_check.py`; tests `r1/tests/test_c3_label_sweep.py` (10).

- Design per PLAN §10 (R1-E1B-RERUN2 revision, R1-C3, D21, verify split, D24, D26, D28, co-tenancy, Paper A coordination) and C3_DESIGN §4: root campaigns only, memory modes `append_only_summary` (primary) and `none` (contrast, D28-exempt via the memory-on verdict), split `"vary"` + new-campaign action versions, W = 20 (enforced outside DRYRUN), D26 seeds (LangGraphManager), transport retry 3, nodes and instances from a JSON config (defaults: the five D21 nodes, 18 instances, 4 workers).
- Phases in `batch_state.json` (completed phases skipped, interrupted = STOP): `preconditions` → `liveness` → `sweep_append_only_summary` → `sweep_none` → `index`.
- **Paper A coordination**: `paper_a_check.command` (argv or string) must exit 0 and print as its last line JSON with `"paper_a_live_waiting_for_card": false`. Missing command, non-zero exit, unparseable output, `true` or a missing key all refuse the launch, *before* card selection or any Ollama start (tested). The verdict is recorded in the state and each sweep manifest.
- GPU: `gpu_rows`, `gpu_census`, `check_gpu`, `assert_full_offload` and the footprint/margin constants are loaded from `deepthought_batch1_resume.py` (AST extraction, no side effects); card selection, census before each collector session, full-offload checks after loading and after each sweep.
- Gates write `collection_checks.json` (roots, failures, LLM calls, failed calls, retried calls with attempt logs, parse failures, split, action versions) and on failure `collection_failures.json` **before** raising. A dead model service ends the session loop instead of resuming into it.
- Outputs (existing layout): `results/r1/engineering/liveness_c3_<UTC>/`, `results/r1/pilot/C3_sweep_<mode>_<UTC>/` (`manifest.json` with `roots_only`, `c3_label_sweep` block, `roots/`, `failures/` if any, `provenance/ledgers/roots/<instance>/root_{trials,events}.jsonl`), and `results/r1/pilot/C3_sweep_index_<UTC>.json` (`r1.c3_sweep_index/1`).
- **Audit hook**: the index is the input contract for `r1/c3/audit.py` (another agent): per memory mode the run dir, manifest and ledger directory, eligible/excluded nodes, harness commit, `audit.status = pending`. The runner runs no audit.
- The runner writes no STATUS.md entry (operator task); it writes `c3_sweep_summary.json` in the batch directory.

## 7. Paper — desktop dry run (`9e276b7`)

`r1/scripts/c3_sweep_dryrun.py`, test `r1/tests/test_c3_sweep_dryrun.py`, record `results/r1/engineering/c3_sweep_dryrun_20261019T011527Z/` (DRYRUN; both scenarios passed in 65.6 s).

Run it (desktop only; refused on Ada):

```bash
export PATH=$HOME/scratch/hv313/bin:$PATH      # node run commands call python3
export AR_HARNESS_ROOT=<harness checkout containing the HARNESS_PIN_C3 commit>
python r1/scripts/c3_sweep_dryrun.py --scenario both [--keep] [--out DIR]
```

It builds a source fixture (HEAD + working-tree `r1/`), bare remotes, real `--prepare`/`--start` clones (suites skipped, `R1_C3_SKIP_SUITES=1`, DRYRUN only; interpreter via `--python`, wrapper venv), copies the ignored OpenML caches from an existing harness checkout, fakes `nvidia-smi`/`ps`/`ollama`/Paper A status on PATH, and uses an isolated tmux socket. Fixture: nodes `digits_mlp` + `openml_breast_w`, 2 instances, W = 6, liveness 1 × W = 4.

- `retry`: chat call 14 is dropped mid-request → resent with the same seed (fake log), 1 retried call recorded, batch completes, liveness/sweeps/index commits on the bare remote, manifests declare `roots_only`, `"vary"`, `original_stands/v1`, `transport_max_attempts = 3`; restart refused ("already finished").
- `permanent`: the fake server exits at chat call 14 → 4/4 roots of the first sweep fail, each with traceback, `httpx.ConnectError` class, UTC time and a 3-attempt log (`server_disconnected`, `connection_refused`); `collection_checks.json` and `collection_failures.json` written; STOP recorded; the dedicated server is gone and tmux ends.

## Test results (final, chunked runs on the desktop VM)

- Harness worktree (`PYTHONPATH=<worktree>/src`, hv313 first on PATH): **421 passed, 9 failed, 1 collection error** — all ten pre-existing and in the launchers' accepted environmental set (unvendored claw-code `test_legacy_noop_skip`, claw/zsh test, three artifact-completeness tests, five KDD paper-section tests). Baseline before any change: 388 passed with the same 9 + 1. New tests: +33.
- Paper `r1/tests` (`AR_HARNESS_ROOT=<harness worktree>`): **193 passed, 1 failed** — the pre-existing `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` (its fixture commits only working-tree changes to `r1/`, so on a clean checkout `git commit` has nothing to commit; it also needs `uv sync` and > 180 s). Baseline: 169 passed with the same failure. New tests: +24.
- Without hv313 first on PATH, node workers call a system `python3` without scikit-learn and 6 further harness tests fail; this is environmental.

## Before an Ada launch (open items)

1. **Author review and merge.** Merge `overnight/r1-c3-prep` into harness `r1` and push; then `HARNESS_PIN_C3` must equal the pushed `r1` head (update the file if the merge creates a new commit). Merge `overnight/c3-sweep-runner` into paper `main` and push.
2. **Paper A coordination command.** Write the real check (e.g. reading `results/paper_a/replay_panel_v4/live_20261018T234416Z` state in `agent-checkpoint-intervention`, branch `paper-a-v4-ada`) that prints `{"paper_a_live_waiting_for_card": false}` only when Paper A has its card and is computing, or has finished/stopped. Put it in the config (`paper_a_check.command`). Without it the runner refuses, by design.
3. **Config file** (`R1_C3_CONFIG`): nodes (default D21; PLAN asks to diagnose `digits_mlp`'s 14 Oct D28 failure before memory-on use — the liveness gate will exclude it if it still fails), instances (18), `ollama.binary` (`/usr/local/bin/ollama`), `ollama.seed_models_from` (e.g. the pinned batch-1 `ollama_models`, so no network pull), `gpu_uuid` (`auto`).
4. **OpenML data caches** are git-ignored and absent from fresh clones; the openml nodes fail every run without them (seen on the desktop). Make sure the Ada batch harness has `experiments/r1/pilot/L8_20261009T152916Z/nodes/<node>/data_cache` (or the nodes can fetch), and consider a preflight that refuses when a cache is missing.
5. `--prepare` on Ada runs both suites; the accepted set equals rerun-2's. Then `--start`.
6. **Not fixed: the SIGTERM sender** of 14 Oct remains unidentified. The dedicated instance (own port, models dir and process group) plus bounded retry reduce exposure and make the next loss diagnosable; they do not prove the cause is gone. A permanent loss still STOPs the batch, with records.
7. The D4 versions are implemented and tested in the harness but not used by the sweep (root campaigns, `ContinueController`); they are for A1+ arms. The posterior-mean response under `"fixed"` needs σ_t/σ_s in the prior.
8. Audit stage (`r1/c3/audit.py`) consumes `C3_sweep_index_*.json`; the K = 6 fresh-seed audits and soft labels are not part of this runner.
9. The runner does not write STATUS.md; record the batch in STATUS after it finishes.
