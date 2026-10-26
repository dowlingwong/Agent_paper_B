# Deepthought A.8 host smoke: watchdog and resume with the real llama-server — 26 October 2026

AI-assisted (Claude, implementation agent on deepthought). **ENGINEERING_ONLY, never evidence.**
The outputs of these runs are smoke-scale and **must not be used as labels**.
Authority: the restart prompt Phase 5, `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phase 5 (RUNBOOK A.8),
PLAN §10 R1-INFER-LLAMACPP, R1-SCHEMA, R1-DT-PIN.

## Why a new driver was needed

`r1/scripts/c3_sweep_dryrun.py` proves the supervision logic against a **fake** llama-server, and
its `check_watchdog` asserts fake-server specifics (a `fault=sigterm` marker in the server log and
`serve` events in `fake_calls.jsonl`). Phase 5 asks for the **real** server. The real server is also
not reachable through the dry run's CLI, which puts a fake `llama-server`, a fake `nvidia-smi` and a
fake `ps` on `PATH`.

`r1/scripts/c3_host_smoke.py` (new, on this branch) therefore reuses the dry run's **isolation** —
temporary clones of both repositories, local bare remotes pushed to instead of GitHub, an isolated
tmux socket, a marked temporary root under the system temporary directory, `R1_C3_SKIP_SUITES` — and
replaces the fakes with the host's own: the `llamacpp` block, `gpu_uuid`, binary and GGUF come
straight from `r1/scripts/configs/c3_sweep_deepthought.json`, and `nvidia-smi` and `ps` are the real
ones, so the pins, `/health`, `/v1/models`, `/props`, the one-token probe and the full-offload check
all run against a real server on a real TITAN. Only the isolated `tmux` wrapper is kept on `PATH`.
No fault is injected (there is no fake to inject into): the script kills a real process by the pid
the batch itself recorded, after checking that pid, process group and command line match that record.

## Scale and pins

| Item | Value |
|---|---|
| Config | `r1/scripts/configs/c3_sweep_deepthought.json` (the completed Phase 4 file, no placeholders) |
| Backend / schema | `llamacpp`; `proposal_schema = manager_proposal/v1` (R1-SCHEMA) |
| Binary / build | `/ceph/dwong/opt/llama.cpp/build-gcc13/bin/llama-server`; `version: 0.7.0-dev (build 1, commit 620d222)` |
| GGUF / sha256 | `/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf`; `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` |
| Card / port / footprint | TITAN index 1, `GPU-2516f262-6a75-eee3-26ee-b2e8d908c07d`; port 18083; `footprint_mib` 5253 |
| Smoke scale | one node `digits_mlp`, 2 instances (2 roots), **W = 4**, 2 workers, memory `append_only_summary` only |
| Harness pin in the batch | `897d83c8efa364ec2fdd37288241cc42e01d7274` |

The runner refuses `runs != 20` outside a guarded DRYRUN (`C3_DESIGN §4`), so a W = 4 run is only
possible under `R1_DRYRUN=1`. That guard controls scale, remotes and the temporary root; it does
**not** force a fake server. This smoke is therefore a guarded-scale run of the real stack: real
binary, real GGUF, real card, real schema-constrained requests.

## Scenario 1 — watchdog: the real server killed mid-request (**passed**, 194.5 s)

1. The batch's own server was started by the runner (pid 626154, pgid 626154, port 18083).
2. Once the sweep phase was collecting, the script waited for an **in-flight request** — a
   `launch_slot_` line in the server's own log with no matching `release` — and sent **SIGTERM** to
   pid 626154 after checking pid, process group and command line against the batch's record.
3. The watchdog recorded the loss and restarted the instance; the affected roots were re-run whole;
   the batch completed with `stop_reason: null`.

| Check | Observed |
|---|---|
| Loss recorded | one `runner_lost` record; `kind: unresponsive`, 3 consecutive failed `/health` checks, `last_healthy_utc` `23:00:32.966Z` ≤ `detected_utc` `23:00:47.968Z` |
| Loss attributed to the killed instance | `runner_event.instance.pid` = 626154 = the pid the script killed |
| Server log captured | 20 tail lines in the record, showing the cancelled in-flight task |
| Instance stopped | `stopped_instance.returncode` 1, `stopped_utc` `23:00:48Z`, no SIGKILL needed |
| Restart | `service_restarts[0]`: reason `runner_lost`, generation 1, new pid 627042 |
| Roots re-run whole | `digits_mlp__s104`, `digits_mlp__s114`; `root_failures_moved` empty |
| Completion | all four phases completed; 2/2 roots, 0 root failures |
| Full offload | `gpu_offload_load_probe.json`, `gpu_offload_load_probe_r1.json` (the restarted server) and `gpu_offload_append_only_summary_collection.json` all `full: true`, route `gpu_memory` |
| Schema | `manager_proposal/v1` in the run manifest **and** in the sweep index; manager `llamacpp/r1-manager`, kind `langgraph`; 8 LLM calls, **0 parse failures** (rate 0.0 against the configured maximum 0.2) |

### Finding: the real server's loss is classified `unresponsive`, not `server_exited`

The first run of this check failed on an assertion of mine, copied from the dry run's
`check_watchdog`: `kind == 'server_exited'`, `signal == 'SIGTERM'`, `returncode == -15`. The real
llama-server **handles SIGTERM itself** — its log shows `cleaning up before exit...` and then
`stop: cancel task, id_task = 405` — and exits on its own with return code 1, several seconds later.
The watchdog's `/health` poll therefore sees three failed checks and records the loss as
`unresponsive` before the process-exit detector sees an exit. Signal and return code are `null` in
that record.

This is correct behaviour of both the server and the watchdog, and the recovery is complete, so the
check was corrected to accept any of the recorded loss kinds (`server_exited`, `unresponsive`,
`model_missing`) and to **report** which one happened, while still asserting the timestamps, the
attribution to the killed pid, the captured server log, the restart and the completion. Nothing in
the runner or the config was changed. Two attempts were used on this item (the first run, with one
node, additionally needed the scale change in the next paragraph).

**For the coordinator:** the fake-server `watchdog` dry run only ever exercises the
`server_exited` / SIGTERM / −15 path, because the fake dies from the signal. The real server's
`unresponsive` path is exercised for the first time here. Both end in the same recovery.

### Finding: liveness at smoke scale is not D28

The first attempt used the dry run's two nodes (`digits_mlp`, `openml_breast_w`) at 1 instance ×
W = 4. The runner stopped cleanly at its liveness gate: *"only 1 nodes passed D28 liveness (< 2);
the author decides"*. `digits_mlp` passed all three criteria (active novelty 1.0, invalid rate 0.0,
two keeps after trial 1); `openml_breast_w` failed **only** `keep_after_trial_1` (0 keeps with
`budget_index > 1`) on its single 4-trial root. That is a smoke-scale artefact of a criterion that
needs at least one keep in a very short campaign, not a D28 verdict: real D28 uses 2 instances ×
W = 10 per node. The smoke was then run on one node, as the runbook specifies. The real D28 result
for all eight nodes is Phase 6.

## Scenario 2 — resume after the runner is killed mid-campaign (**passed**, 182.4 s)

The dry run's own `Interrupter` was used unchanged: once one root had completed and another was in
progress, it SIGKILLed the runner's process group (runner, collector and workers — not the server),
then restarted with `--start <batch>`.

| Check | Observed |
|---|---|
| Interruption recorded | one `process_restart` record; `INTERRUPTION` in `sweep_append_only_summary.log`; `interruptions.jsonl` written in the run directory |
| Completed root kept byte for byte | `digits_mlp__s104`: root JSON and `root_trials.jsonl` sha256 identical before and after |
| Interrupted root re-run whole | `digits_mlp__s114`: archived under `work/interrupted/01/roots/` and `provenance/ledgers/interrupted/01/`, final ledger a fresh contiguous campaign from `budget_index` 1 |
| Orphaned server | stopped with SIGTERM only after the check *"alive; pid, owner, process group and command line (binary, `--port`, `-m`) match"* |
| Completion | all phases completed, `stop_reason: null`, 2/2 roots, 0 root failures |
| Full offload | all three reports `full: true`, route `gpu_memory` |
| Schema | `manager_proposal/v1` in manifest and index; 8 LLM calls, 0 parse failures |

## The pinned build does enforce per-request `json_schema`

Phase 2 could confirm from `--help` only that this build has `-j, --json-schema`. Whether it honours
a per-request `response_format: {"type": "json_schema", ...}` on `/v1/chat/completions` — what the
harness actually sends — was checked directly on an idle TITAN (index 2), with its own server on
port 18085, one prompt that deliberately invites prose, same seed and temperature, twice:

| Request | Result |
|---|---|
| no `response_format` | 1,035 characters, begins `### Reasoning\n\nIn machine learning, hyper-parameters are settings that control t…`, **not JSON** (`Expecting value: line 1 column 1`) |
| `response_format = manager_response_format()` | 842 characters, **valid JSON**, keys exactly `new_value, objective, old_value, param, rationale, summary`, every value a string |

So the schema is enforced by the server, not merely requested, and it is exactly the
structure-only `manager_proposal/v1` contract (six string fields; D25 key and value validity stays
the model's). Record: `schema_check.json` in the local work directory. **R1-SCHEMA is operational on
this host.**

## Footprint pin

`footprint_mib` was pinned at 5253 from the Phase 4 probe. The batch B handoff (open question 7b)
warned that a later start differing by a few MiB would STOP. Observed here: every server start in
both scenarios, and the Phase 6 server, reported **exactly 5253 MiB** for the server pid on the card
(route `gpu_memory`). The pin is reproducible on this host at `-np 1 -c 8192`. It remains an author
decision whether to pin a slightly lower value for margin.

## Co-tenancy during the smoke

Other users' processes were on the cards throughout and are logged, never signalled (PLAN §10,
13 Oct). At the start of Phase 2, TITAN index 0 carried 3,989 MiB of three other users' work; by the
start of Phase 6 a fourth user held 1,170 MiB on **all four** TITANs and index 0 was at 6,377 MiB.
TITAN index 1 still had 11,111 MiB free, well above the co-tenancy need of
5253 + 2048 = 7,301 MiB. **This host is not exclusive in practice**, which matters for a multi-day
sweep: if a co-tenant's job grows, the runner's co-tenancy check STOPs. Reported, not acted on.

## Verdict

Both A.8 host-smoke scenarios pass with the real llama-server, the real GGUF and R1-SCHEMA on:
the watchdog detects a server lost mid-request, restarts it and re-runs the affected roots whole;
a runner killed mid-campaign resumes, keeping completed roots byte for byte and re-running the
interrupted root whole. Full GPU offload is proven at every load and after collection, by route (ii)
against the pinned footprint.

Records (local disk, not pushed): `/tmp/r1_sweep1_dwong_20261026/smoke_watchdog_03/summary.json`,
`/tmp/r1_sweep1_dwong_20261026/smoke_interrupt_01/summary.json`, the copied batch logs beside them,
and `/tmp/r1_sweep1_dwong_20261026/logs/smoke_*.log`.
