# Rerun-2 STOP diagnosis and digits_mlp liveness — 19 Oct 2026

AI-assisted by Codex. ENGINEERING_ONLY; not evidence. Analysis of preserved files only. No LLM, GPU, worker runs, retries or experiment changes.

## Scope and source anchors

`B` below means `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse`. Diagnostic checkout: `/data1/dowling/tmp/r1_diag_ENGINEERING_ONLY_20261018T223815Z/repo`. Input main: `bf52f5c`; stopped paper liveness commit `b2e5cc3`, harness `411c6054c8505f93a6429e2f9eed526952793882` (B/batch_state.json, steps.liveness.commit and harness_head_at_launch). Historical batch launch paper HEAD was `b2ba344`, before the liveness commit (same source, paper_head_at_launch).

## Diagnosis

**Observed immediate cause: the shared Ollama runner received SIGTERM during proposal requests, producing five “llama runner process no longer running” errors and two “unexpected EOF” errors; seven branch leaves failed and the runner refused acceptance. The sender/reason for SIGTERM is not recorded, so the underlying termination cause remains undetermined.** Sources: exact failed-leaf records below; B/ollama_serve.log lines 4094–4099 and 8006–8013; B/runner.log final FINISHED record.

Classification, ranked: **(c) manager/LLM service availability** is directly supported (transport/service loss before worker execution). **(e) other: unidentified signal source** is the unresolved underlying cause. **(a) runner observability defect** is secondary: the collector catches the exception as `repr(exc)` and resets leaf counters; collection checks are written only after a failure-free gate. No traceback or failed-request timestamp is persisted. There is no affirmative evidence here for missing packages, permissions or disk errors, parse failure, inactive-key loops, OOM, CPU fallback or a co-tenancy threshold crossing as the terminal cause. This is absence of evidence, not proof those causes are impossible. Sources: failed-leaf/event audit below; pinned `r1/headroom/e1b_collect.py` `run_leaf`; pinned `r1/scripts/deepthought_batch1_resume.py` `collect`; saved GPU census and Ollama excerpts below.

**C3 impact: possible even with roots only.** The observed failures happened during branch continuation, but they are failures of the shared proposal service, not branch-state restoration. A root campaign calling that service can suffer the same loss. Removing branches reduces exposure and removes these specific continuation sites; it does not establish a fix. Memory mode and split policy do not repair a terminated model server. This is an engineering inference from the final `memory_context_built` events and identical service errors in both actions, not a tested prediction.

## Batch layout (depth at most 4)

The following inventory was obtained by enumerating the existing tree to depth 4; repetitive checkout/cache descendants are collapsed by parent. No existing files were written. The complete enumerated list is retained only in the new scratch directory (`batch_tree_depth4.txt`).

```text
/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/
  runner.log; E1b_rerun2_A_20261014T141051Z.log; ollama_serve.log
  batch_state.json; prepare.json; setup_checks.json; env.sh
  gpu_census.jsonl; gpu_wait.jsonl; gpu_offload_probe.json; gpu_after_ollama_stop.txt
  liveness.log; harness_tests.log; paper_tests.log; uv_sync.log; *_identity*.log
  agent_paper_B/ (historical checkout; arm outputs are below results/r1/pilot/)
  autoresearch_harness/ (pinned historical checkout and .venv; read as source only)
  liveness_work/ (preserved root campaigns)
  r1_e1b_rerun2_A_work/
    roots/<instance>/root_trials.jsonl; root_events.jsonl; node/; art/
    branches/<leaf>/branch_trials.jsonl; branch_events.jsonl; artifacts/; .autoresearch_artifacts/
```

Arm output: `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z`. Observed 648 leaves, 54 root summaries and 54 start-audit summaries; 7 failed leaves. Only roots, manifest, leaves and audits exist in this incomplete output. `collection_checks.json`, analysis and the committed provenance archive were not produced. The runner raises before writing checks; this is a reporting-order consequence, not missing evidence to recreate. Sources: directory inventory; B/runner.log; pinned collect function excerpts below.

## Every failed leaf

The pending request is localized by its last request-start/memory event and the matching server SIGTERM. The exception can arrive after termination; its leaf-specific timestamp was not saved and must not be inferred from copied trial timestamps or rounded wall_seconds. All times below are UTC (server log uses −07:00).

| Node | Instance | Point | Action | Rep | Pending trial | Last request event | Server termination window | Category | Exact error | Leaf source | Event source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openml_breast_w | openml_breast_w__s235 | 4 | continue | 1 | 19 | 2026-10-14T16:17:04Z | 2026-10-14T16:17:05.902–16:17:06.014Z | collection_failure | ResponseError('llama runner process no longer running: -1 ') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_breast_w__s235__b004__continue__r1.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r1/branch_events.jsonl:186` |
| openml_breast_w | openml_breast_w__s235 | 4 | continue | 2 | 18 | 2026-10-14T16:17:03Z | 2026-10-14T16:17:05.902–16:17:06.014Z | collection_failure | ResponseError('llama runner process no longer running: -1 ') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_breast_w__s235__b004__continue__r2.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r2/branch_events.jsonl:173` |
| openml_breast_w | openml_breast_w__s235 | 4 | verify | 1 | 16 | 2026-10-14T16:17:05Z | 2026-10-14T16:17:05.902–16:17:06.014Z | collection_failure | ResponseError('llama runner process no longer running: -1 ') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_breast_w__s235__b004__verify__r1.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r1/branch_events.jsonl:147` |
| openml_breast_w | openml_breast_w__s235 | 4 | verify | 2 | 13 | 2026-10-14T16:17:02Z | 2026-10-14T16:17:05.902–16:17:06.014Z | collection_failure | ResponseError('an error was encountered while running the model: unexpected EOF') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_breast_w__s235__b004__verify__r2.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r2/branch_events.jsonl:108` |
| openml_ionosphere | openml_ionosphere__s123 | 8 | continue | 1 | 15 | 2026-10-14T15:11:00Z | 2026-10-14T15:11:01.954–15:11:01.991Z | collection_failure | ResponseError('llama runner process no longer running: -1 ') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_ionosphere__s123__b008__continue__r1.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r1/branch_events.jsonl:82` |
| openml_ionosphere | openml_ionosphere__s123 | 8 | continue | 2 | 14 | 2026-10-14T15:11:01Z | 2026-10-14T15:11:01.954–15:11:01.991Z | collection_failure | ResponseError('llama runner process no longer running: -1 ') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_ionosphere__s123__b008__continue__r2.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r2/branch_events.jsonl:69` |
| openml_ionosphere | openml_ionosphere__s123 | 8 | verify | 2 | 9 | 2026-10-14T15:10:59Z | 2026-10-14T15:11:01.954–15:11:01.991Z | collection_failure | ResponseError('an error was encountered while running the model: unexpected EOF') | `B/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z/leaves/openml_ionosphere__s123__b008__verify__r2.json:1` | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__verify__r2/branch_events.jsonl:4` |

### Per-leaf artifact and ledger inspection

#### openml_breast_w__s235__b004__continue__r1

Final event `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r1/branch_events.jsonl:186`:

```json
{"campaign_id": "openml_breast_w__s235", "event_id": "937ace5bc9e541b4", "event_type": "memory_context_built", "payload": {"compressed_chars": 2138, "mode": "append_only_summary", "repeated_bad_count": 14}, "timestamp": "2026-10-14T16:17:04Z", "trial_id": "openml_breast_w__s235-trial-019"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_breast_w__s235-trial-019`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r1/branch_trials.jsonl:18`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r1/.autoresearch_artifacts/trial-018/run.log`.

```text
NODE=openml_breast_w
MODEL=logistic_regression
VAL_AUC=0.992351
VAL_ACC=0.980952
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r1/.autoresearch_artifacts/trial-018/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.5
+C: 10
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_breast_w__s235__b004__continue__r2

Final event `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r2/branch_events.jsonl:173`:

```json
{"campaign_id": "openml_breast_w__s235", "event_id": "301753b88df248a5", "event_type": "memory_context_built", "payload": {"compressed_chars": 2027, "mode": "append_only_summary", "repeated_bad_count": 13}, "timestamp": "2026-10-14T16:17:03Z", "trial_id": "openml_breast_w__s235-trial-018"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_breast_w__s235-trial-018`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r2/branch_trials.jsonl:17`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r2/.autoresearch_artifacts/trial-017/run.log`.

```text
NODE=openml_breast_w
MODEL=logistic_regression
VAL_AUC=0.992351
VAL_ACC=0.980952
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__continue__r2/.autoresearch_artifacts/trial-017/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.5
+C: 10
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_breast_w__s235__b004__verify__r1

Final event `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r1/branch_events.jsonl:147`:

```json
{"campaign_id": "openml_breast_w__s235", "event_id": "fceedb7cb06d4c94", "event_type": "memory_context_built", "payload": {"compressed_chars": 1771, "mode": "append_only_summary", "repeated_bad_count": 11}, "timestamp": "2026-10-14T16:17:05Z", "trial_id": "openml_breast_w__s235-trial-016"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_breast_w__s235-trial-016`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r1/branch_trials.jsonl:15`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r1/.autoresearch_artifacts/trial-015/run.log`.

```text
NODE=openml_breast_w
MODEL=logistic_regression
VAL_AUC=0.992351
VAL_ACC=0.980952
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r1/.autoresearch_artifacts/trial-015/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.5
+C: 10
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_breast_w__s235__b004__verify__r2

Final event `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r2/branch_events.jsonl:108`:

```json
{"campaign_id": "openml_breast_w__s235", "event_id": "a477f89548d544ad", "event_type": "memory_context_built", "payload": {"compressed_chars": 1415, "mode": "append_only_summary", "repeated_bad_count": 8}, "timestamp": "2026-10-14T16:17:02Z", "trial_id": "openml_breast_w__s235-trial-013"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_breast_w__s235-trial-013`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r2/branch_trials.jsonl:12`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r2/.autoresearch_artifacts/trial-012/run.log`.

```text
NODE=openml_breast_w
MODEL=logistic_regression
VAL_AUC=0.992351
VAL_ACC=0.980952
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b004__verify__r2/.autoresearch_artifacts/trial-012/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.5
+C: 10
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_ionosphere__s123__b008__continue__r1

Final event `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r1/branch_events.jsonl:82`:

```json
{"campaign_id": "openml_ionosphere__s123", "event_id": "d0fa6f305a554bf8", "event_type": "memory_context_built", "payload": {"compressed_chars": 1694, "mode": "append_only_summary", "repeated_bad_count": 12}, "timestamp": "2026-10-14T15:11:00Z", "trial_id": "openml_ionosphere__s123-trial-015"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_ionosphere__s123-trial-015`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r1/branch_trials.jsonl:14`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r1/.autoresearch_artifacts/trial-014/run.log`.

```text
NODE=openml_ionosphere
MODEL=logistic_regression
VAL_AUC=0.874613
VAL_ACC=0.849057
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r1/.autoresearch_artifacts/trial-014/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.3
+C: 1.5
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_ionosphere__s123__b008__continue__r2

Final event `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r2/branch_events.jsonl:69`:

```json
{"campaign_id": "openml_ionosphere__s123", "event_id": "55c06d1d4d4f4466", "event_type": "memory_context_built", "payload": {"compressed_chars": 1571, "mode": "append_only_summary", "repeated_bad_count": 11}, "timestamp": "2026-10-14T15:11:01Z", "trial_id": "openml_ionosphere__s123-trial-014"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_ionosphere__s123-trial-014`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r2/branch_trials.jsonl:13`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r2/.autoresearch_artifacts/trial-013/run.log`.

```text
NODE=openml_ionosphere
MODEL=logistic_regression
VAL_AUC=0.879257
VAL_ACC=0.830189
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__continue__r2/.autoresearch_artifacts/trial-013/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.3
+C: 1.0
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```
#### openml_ionosphere__s123__b008__verify__r2

Final event `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__verify__r2/branch_events.jsonl:4`:

```json
{"campaign_id": "openml_ionosphere__s123", "event_id": "46f9153083034352", "event_type": "memory_context_built", "payload": {"compressed_chars": 954, "mode": "append_only_summary", "repeated_bad_count": 6}, "timestamp": "2026-10-14T15:10:59Z", "trial_id": "openml_ionosphere__s123-trial-009"}
```

No `proposal_created`, `worker_started` or completed trial record follows for `openml_ionosphere__s123-trial-009`. Therefore the failed request has no worker `run.log`, no `patch.diff`, and no ledger `failure_category` / `worker_failure_message` row. The leaf error is the terminal evidence; `cost_worker_runs: 0` is the exception handler’s reset value and does **not** mean this branch executed zero earlier workers. Source: leaf JSON; event suffix; pinned run_leaf exception handler.

Last completed ledger row `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s123__b008__verify__r2/branch_trials.jsonl:8`: decision `discarded`, failure_category `degraded_metric`, worker_failure_message `None`. Its worker artifacts describe a prior completed trial, not the failed request.

raw_log_ref: `B/r1_e1b_rerun2_A_work/roots/openml_ionosphere__s123/art/trial-008/run.log`.

```text
NODE=openml_ionosphere
MODEL=logistic_regression
VAL_AUC=0.883901
VAL_ACC=0.830189
STATUS=success
```

patch_ref: `B/r1_e1b_rerun2_A_work/roots/openml_ionosphere__s123/art/trial-008/patch.diff`.

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 0.3
+C: 0.9
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```

## Exact server and runner evidence

`B/ollama_serve.log:1968`

```text
time=2026-10-14T07:38:04.335-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:4094`

```text
time=2026-10-14T08:11:01.954-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:4096`

```text
time=2026-10-14T08:11:01.954-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:4099`

```text
time=2026-10-14T08:11:01.991-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:6018`

```text
time=2026-10-14T08:44:08.494-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:8006`

```text
time=2026-10-14T09:17:05.902-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:8008`

```text
time=2026-10-14T09:17:05.902-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:8010`

```text
time=2026-10-14T09:17:05.903-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```
`B/ollama_serve.log:8013`

```text
time=2026-10-14T09:17:06.014-07:00 level=WARN source=server.go:510 msg="llama runner process no longer running" sys=15 string="signal: terminated"
```

The first and third SIGTERM windows have no failed-leaf match in the final leaf records; the seven terminal leaf errors align with the second and fourth windows. A recurrent interval is suggestive of lifecycle interference, but neither a timer nor the signal sender can be identified from these files. No external process was inspected or touched. Source: server timestamps above and failed-leaf/event audit.

`B/runner.log:40`

```text
RUN ['/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/autoresearch_harness/.venv/bin/python', '-m', 'r1.headroom.e1b_collect', '--resume', '/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z', '--workers', '4']
```
`B/runner.log:41`

```text
RUN ['/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/autoresearch_harness/.venv/bin/python', '-m', 'r1.headroom.e1b_collect', '--resume', '/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/agent_paper_B/results/r1/pilot/E1b_rerun2_A_20261014T141051Z', '--workers', '4']
```

The historical `--resume` commands shown above are the collector’s recorded phase progression, not actions taken in this diagnosis. No historical phase was resumed.

`B/agent_paper_B/r1/scripts/deepthought_batch1_resume.py:216`

```text
    if failures:
```

`B/agent_paper_B/r1/scripts/deepthought_batch1_resume.py:217`

```text
        raise RuntimeError('STOP: collection failures; no leaf retries permitted')
```

`B/agent_paper_B/r1/scripts/deepthought_batch1_resume.py:242`

```text
    (out / 'collection_checks.json').write_text(json.dumps(check, indent=2) + '\n')
```

`B/agent_paper_B/r1/headroom/e1b_collect.py:207`

```text
    except Exception as exc:  # noqa: BLE001 - a failed leaf is an integrity status, never a utility
```

`B/agent_paper_B/r1/headroom/e1b_collect.py:208`

```text
        status, err, executed, runs, audit, n_keeps, final_files = "collection_failure", repr(exc), None, 0, [], 0, {}
```

| Saved UTC | Selected free MiB | Required free MiB |
| --- | --- | --- |
| 20261014T140731Z | 48427 | 7352 |
| 20261014T140742Z | 43233 | 2048 |
| 20261014T142806Z | 43113 | 2048 |
| 20261014T163129Z | 29386 | 2048 |

Source: `B/gpu_census.jsonl`. All saved samples exceed the threshold; sampling is sparse and does not cover each failure instant. Full offload was checked before collection (`B/gpu_offload_probe.json`; `B/batch_state.json`, gpu_offload). The post-collection offload check was never reached after the failure gate; no claim of continuous full offload is made. Server reload lines describe available 46.9 GiB and required 5.2 GiB (B/ollama_serve.log:1971–1974, 6021–6024); VRAM-recovery warnings occur **after** SIGTERM and do not establish that memory pressure caused it.

## Other invalid trials (not the terminal collection failure)

Below are all root invalid trials and branch-local invalid trials after their fork point, excluding copied prefixes. They are retained by the campaign as failed_invalid; they are not additional collection-failure leaves. Exact worker messages and log excerpts distinguish stale edit preconditions from configuration execution errors.

| Ledger campaign/leaf | Trial | Category | Exact worker_failure_message | UTC end | Source |
| --- | --- | --- | --- | --- | --- |
| openml_breast_w__s105__b004__continue__r2 | 20 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.3 | 2026-10-14T15:48:01Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s105__b004__continue__r2/branch_trials.jsonl:20` |
| openml_breast_w__s115__b004__continue__r1 | 11 | invalid_config | exit code 2 | 2026-10-14T15:49:41Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r1/branch_trials.jsonl:11` |
| openml_breast_w__s115__b004__continue__r1 | 18 | invalid_config | exit code 2 | 2026-10-14T15:50:06Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r1/branch_trials.jsonl:18` |
| openml_breast_w__s115__b004__continue__r2 | 12 | invalid_config | exit code 2 | 2026-10-14T15:49:52Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r2/branch_trials.jsonl:12` |
| openml_breast_w__s115__b004__continue__r2 | 13 | invalid_config | exit code 2 | 2026-10-14T15:49:55Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r2/branch_trials.jsonl:13` |
| openml_breast_w__s115__b004__verify__r1 | 11 | invalid_config | exit code 2 | 2026-10-14T15:49:57Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__verify__r1/branch_trials.jsonl:11` |
| openml_breast_w__s115__b004__verify__r2 | 12 | invalid_config | exit code 2 | 2026-10-14T15:50:04Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__verify__r2/branch_trials.jsonl:12` |
| openml_breast_w__s115__b004__verify__r2 | 13 | invalid_config | exit code 2 | 2026-10-14T15:50:07Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__verify__r2/branch_trials.jsonl:13` |
| openml_breast_w__s115__b008__continue__r1 | 11 | invalid_config | exit code 2 | 2026-10-14T15:50:29Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__continue__r1/branch_trials.jsonl:11` |
| openml_breast_w__s115__b008__continue__r1 | 18 | invalid_config | exit code 2 | 2026-10-14T15:50:50Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__continue__r1/branch_trials.jsonl:18` |
| openml_breast_w__s115__b008__continue__r2 | 12 | invalid_config | exit code 2 | 2026-10-14T15:50:33Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__continue__r2/branch_trials.jsonl:12` |
| openml_breast_w__s115__b008__continue__r2 | 13 | invalid_config | exit code 2 | 2026-10-14T15:50:37Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__continue__r2/branch_trials.jsonl:13` |
| openml_breast_w__s115__b008__verify__r1 | 11 | invalid_config | exit code 2 | 2026-10-14T15:50:41Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__verify__r1/branch_trials.jsonl:11` |
| openml_breast_w__s115__b008__verify__r2 | 12 | invalid_config | exit code 2 | 2026-10-14T15:50:45Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b008__verify__r2/branch_trials.jsonl:12` |
| openml_breast_w__s125__b004__continue__r1 | 14 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:52:05Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s125__b004__continue__r1/branch_trials.jsonl:14` |
| openml_breast_w__s125__b004__continue__r2 | 20 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:52:29Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s125__b004__continue__r2/branch_trials.jsonl:20` |
| openml_breast_w__s125__b004__verify__r1 | 14 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:52:15Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s125__b004__verify__r1/branch_trials.jsonl:14` |
| openml_breast_w__s135__b008__verify__r2 | 12 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:55:13Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s135__b008__verify__r2/branch_trials.jsonl:12` |
| openml_breast_w__s185__b008__continue__r2 | 18 | proposal_precondition_failed | structured edit precondition failed for max_iter: expected 1700, found 1000 | 2026-10-14T16:06:33Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s185__b008__continue__r2/branch_trials.jsonl:18` |
| openml_breast_w__s205__b008__continue__r2 | 13 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.9 | 2026-10-14T16:10:43Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s205__b008__continue__r2/branch_trials.jsonl:13` |
| openml_breast_w__s205__b008__verify__r2 | 13 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.9 | 2026-10-14T16:10:57Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s205__b008__verify__r2/branch_trials.jsonl:13` |
| openml_breast_w__s215__b004__continue__r1 | 15 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:12:22Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b004__continue__r1/branch_trials.jsonl:15` |
| openml_breast_w__s215__b004__verify__r1 | 15 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:12:32Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b004__verify__r1/branch_trials.jsonl:15` |
| openml_breast_w__s215__b008__continue__r1 | 12 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:12:58Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b008__continue__r1/branch_trials.jsonl:12` |
| openml_breast_w__s215__b008__continue__r2 | 18 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:13:21Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b008__continue__r2/branch_trials.jsonl:18` |
| openml_breast_w__s215__b008__verify__r1 | 12 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:13:12Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b008__verify__r1/branch_trials.jsonl:12` |
| openml_breast_w__s215__b008__verify__r2 | 15 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T16:13:24Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s215__b008__verify__r2/branch_trials.jsonl:15` |
| openml_breast_w__s235__b008__continue__r2 | 19 | invalid_config | exit code 2 | 2026-10-14T16:17:48Z | `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s235__b008__continue__r2/branch_trials.jsonl:19` |
| openml_ionosphere__s113__b004__continue__r1 | 15 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.3 | 2026-10-14T15:08:02Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s113__b004__continue__r1/branch_trials.jsonl:15` |
| openml_ionosphere__s113__b004__verify__r1 | 15 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.3 | 2026-10-14T15:08:12Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s113__b004__verify__r1/branch_trials.jsonl:15` |
| openml_ionosphere__s153__b004__continue__r1 | 9 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:16:37Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s153__b004__continue__r1/branch_trials.jsonl:9` |
| openml_ionosphere__s153__b004__verify__r1 | 9 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:16:52Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s153__b004__verify__r1/branch_trials.jsonl:9` |
| openml_ionosphere__s213__b012__continue__r1 | 20 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.6 | 2026-10-14T15:32:49Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s213__b012__continue__r1/branch_trials.jsonl:20` |
| openml_ionosphere__s233__b012__continue__r1 | 18 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.9 | 2026-10-14T15:37:28Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s233__b012__continue__r1/branch_trials.jsonl:18` |
| openml_ionosphere__s243__b008__verify__r1 | 10 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.3 | 2026-10-14T15:39:00Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s243__b008__verify__r1/branch_trials.jsonl:10` |
| openml_ionosphere__s263__b004__continue__r1 | 13 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.9 | 2026-10-14T15:42:42Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s263__b004__continue__r1/branch_trials.jsonl:13` |
| openml_ionosphere__s263__b004__verify__r1 | 13 | proposal_precondition_failed | structured edit precondition failed for C: expected 1.0, found 0.9 | 2026-10-14T15:42:54Z | `B/r1_e1b_rerun2_A_work/branches/openml_ionosphere__s263__b004__verify__r1/branch_trials.jsonl:13` |
| tabular_mlp__s182__b004__continue__r1 | 12 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:10Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:12` |
| tabular_mlp__s182__b004__continue__r1 | 17 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:30Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:17` |
| tabular_mlp__s182__b004__continue__r1 | 18 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:34Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:18` |
| tabular_mlp__s182__b004__continue__r1 | 19 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:38Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:19` |
| tabular_mlp__s182__b004__continue__r1 | 20 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:42Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:20` |
| tabular_mlp__s182__b004__continue__r1 | 22 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:46Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:22` |
| tabular_mlp__s182__b004__continue__r1 | 23 | proposal_precondition_failed | structured edit precondition failed for ALPHA: expected 1e-3, found 1e-4 | 2026-10-14T14:45:47Z | `B/r1_e1b_rerun2_A_work/branches/tabular_mlp__s182__b004__continue__r1/branch_trials.jsonl:23` |
| openml_breast_w__s115 | 10 | invalid_config | exit code 2 | 2026-10-14T14:22:44Z | `B/r1_e1b_rerun2_A_work/roots/openml_breast_w__s115/root_trials.jsonl:10` |
| openml_breast_w__s235 | 11 | invalid_config | exit code 2 | 2026-10-14T14:26:37Z | `B/r1_e1b_rerun2_A_work/roots/openml_breast_w__s235/root_trials.jsonl:11` |

Example invalid_config: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r1/branch_trials.jsonl:11`. Structured edit `{"new": "1000", "old": "1", "path": "config.yaml", "symbol": "C", "type": "config_value"}`.

raw_log_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r1/.autoresearch_artifacts/trial-011/run.log`

```text
NODE=openml_breast_w
STATUS=failed
FAILURE_CATEGORY=invalid_config
FAILURE_MESSAGE=C=1000.0 outside allowed range [0.001, 100.0]
```

patch_ref: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s115__b004__continue__r1/.autoresearch_artifacts/trial-011/patch.diff`

```text
--- a/config.yaml
+++ b/config.yaml
@@ -1,5 +1,5 @@
 model_type: logistic_regression
-C: 1
+C: 1000
 max_depth: 5
 n_estimators: 100
 learning_rate: 0.05
```

Example proposal_precondition_failed: `B/r1_e1b_rerun2_A_work/branches/openml_breast_w__s105__b004__continue__r2/branch_trials.jsonl:20`. Structured edit `{"new": "1.2", "old": "1.0", "path": "config.yaml", "symbol": "C", "type": "config_value"}`.

raw_log_ref: `.`

```text
(recorded artifact absent)
```

patch_ref: empty ledger reference (no artifact path recorded)

```text
(recorded artifact absent)
```

## Minimal fix proposal and desktop test (not implemented)

The confirmed failure requires keeping the **owned model service alive for the whole collection**, and establishing which component sends SIGTERM before changing a lifetime policy. Do not assume that increasing a timeout or adding retries fixes it. The runner already sets `OLLAMA_KEEP_ALIVE=-1` and warms the model with `keep_alive: -1` (pinned `r1/scripts/ada_e1b_rerun2.py`, preconditions); investigate request-level/lifecycle ownership against the recorded terminations. Root-only C3 must retain this as an unresolved service prerequisite.

The minimal code hardening is to persist the exception type/message, UTC time, stage, partial ledger paths and partial run count when a proposal request fails, and to write collection checks before raising the terminal STOP. Keep no-retry behavior and never convert a failed leaf to an accepted result. This repairs diagnosability and containment, not the unidentified SIGTERM source. Sources: quoted exception handler and check-writing order.

A desktop fixture can inject an Ollama-like transport exception after several successful mocked proposals, under concurrent branches and a root-only campaign. Assert: the current failed request never starts a worker; previous records remain intact; exact error, time and stage are saved; checks list every failed leaf; the runner stops before analysis/next arms; no retry/resume is scheduled. A fake service-lifetime/clock fixture can also terminate the owned stub mid-request. It would catch loss-handling and observability defects before Ada, but cannot discover an external SIGTERM sender. No such fix or run was implemented here.

## digits_mlp liveness

### digits_mlp__s104

| Trial | Structured edit | val_score | Incumbent before | Delta | Decision | Trial source | Memory source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | HIDDEN_UNITS: 32 → 64 | 0.977716 | None | None | kept | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:1` | M1 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:3`) |
| 2 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.977716 | -0.013928000000000051 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:2` | M2 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:16`) |
| 3 | HIDDEN_UNITS: 64 → 128 | 0.969359 | 0.977716 | -0.008357000000000059 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:3` | M3 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:29`) |
| 4 | MAX_ITER: 40 → 100 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:4` | M4 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:42`) |
| 5 | ALPHA: 1e-4 → 1e-3 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:5` | M5 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:55`) |
| 6 | ALPHA: 1e-4 → 1e-3 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:6` | M6 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:68`) |
| 7 | ALPHA: 1e-4 → 1e-5 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:7` | M7 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:81`) |
| 8 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.977716 | -0.013928000000000051 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:8` | M8 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:94`) |
| 9 | ALPHA: 1e-4 → 1e-6 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:9` | M9 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:107`) |
| 10 | MAX_ITER: 40 → 100 | 0.977716 | 0.977716 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:10` | M10 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_events.jsonl:120`) |

The memory_context_built event records mode/length/count but not its text. Exact text below is from the same trial’s `extra.manager.worker_memory_context_text`; the event reference above anchors its construction. This resolves the prompt’s assumption that events contain the text.

#### M1 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:1`

```text
(empty context)
```

#### M2 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:2`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
```

#### M3 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:3`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
```

#### M4 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:4`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
```

#### M5 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:5`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
```

#### M6 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:6`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
digits_mlp__s104-trial-005: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
```

#### M7 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:7`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
digits_mlp__s104-trial-005: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
```

#### M8 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:8`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
digits_mlp__s104-trial-005: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-007: decision=discarded; summary=reduce-alpha-1e-5; metric=0.977716; delta=0.0
```

#### M9 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:9`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
digits_mlp__s104-trial-005: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-007: decision=discarded; summary=reduce-alpha-1e-5; metric=0.977716; delta=0.0
digits_mlp__s104-trial-008: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
```

#### M10 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s104/root_trials.jsonl:10`

```text
digits_mlp__s104-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.977716; delta=None
digits_mlp__s104-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.969359; delta=-0.008357000000000059
digits_mlp__s104-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.977716; delta=0.0
digits_mlp__s104-trial-005: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.977716; delta=0.0
digits_mlp__s104-trial-007: decision=discarded; summary=reduce-alpha-1e-5; metric=0.977716; delta=0.0
digits_mlp__s104-trial-008: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.013928000000000051
digits_mlp__s104-trial-009: decision=discarded; summary=reduce-alpha-1e-6; metric=0.977716; delta=0.0
```

### digits_mlp__s114

| Trial | Structured edit | val_score | Incumbent before | Delta | Decision | Trial source | Memory source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | HIDDEN_UNITS: 32 → 64 | 0.972145 | None | None | kept | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:1` | M1 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:3`) |
| 2 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.972145 | -0.008357000000000059 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:2` | M2 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:16`) |
| 3 | HIDDEN_UNITS: 64 → 128 | 0.966574 | 0.972145 | -0.005570999999999993 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:3` | M3 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:29`) |
| 4 | MAX_ITER: 40 → 100 | 0.972145 | 0.972145 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:4` | M4 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:42`) |
| 5 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.972145 | -0.008357000000000059 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:5` | M5 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:55`) |
| 6 | ALPHA: 1e-4 → 1e-3 | 0.972145 | 0.972145 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:6` | M6 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:68`) |
| 7 | ALPHA: 1e-4 → 1e-3 | 0.972145 | 0.972145 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:7` | M7 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:81`) |
| 8 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.972145 | -0.008357000000000059 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:8` | M8 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:94`) |
| 9 | ALPHA: 1e-4 → 1e-3 | 0.972145 | 0.972145 | 0.0 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:9` | M9 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:107`) |
| 10 | BATCH_SIZE: 64 → 128 | 0.963788 | 0.972145 | -0.008357000000000059 | discarded | `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:10` | M10 (`results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_events.jsonl:120`) |

The memory_context_built event records mode/length/count but not its text. Exact text below is from the same trial’s `extra.manager.worker_memory_context_text`; the event reference above anchors its construction. This resolves the prompt’s assumption that events contain the text.

#### M1 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:1`

```text
(empty context)
```

#### M2 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:2`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
```

#### M3 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:3`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
```

#### M4 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:4`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
```

#### M5 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:5`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
```

#### M6 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:6`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
digits_mlp__s114-trial-005: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
```

#### M7 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:7`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
digits_mlp__s114-trial-005: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
```

#### M8 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:8`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
digits_mlp__s114-trial-005: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
digits_mlp__s114-trial-007: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
```

#### M9 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:9`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
digits_mlp__s114-trial-005: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
digits_mlp__s114-trial-007: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
digits_mlp__s114-trial-008: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
```

#### M10 — `results/r1/engineering/liveness_llm_20261014T140742Z/ledgers/digits_mlp__s114/root_trials.jsonl:10`

```text
digits_mlp__s114-trial-001: decision=kept; summary=increase-hidden-units-64; metric=0.972145; delta=None
digits_mlp__s114-trial-002: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-003: decision=discarded; summary=increase-hidden-units-128; metric=0.966574; delta=-0.005570999999999993
digits_mlp__s114-trial-004: decision=discarded; summary=increase-max-iter-100; metric=0.972145; delta=0.0
digits_mlp__s114-trial-005: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-006: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
digits_mlp__s114-trial-007: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
digits_mlp__s114-trial-008: decision=discarded; summary=increase-batch-size-128; metric=0.963788; delta=-0.008357000000000059
digits_mlp__s114-trial-009: decision=discarded; summary=increase-alpha-1e-3; metric=0.972145; delta=0.0
```

### Memory-off comparison

| Instance | Trials | First edit | First val_score | Keeps after first | Best val_score | Source |
| --- | --- | --- | --- | --- | --- | --- |
| digits_mlp__s104 | 20 | {'new': '64', 'old': '32', 'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'type': 'python_constant'} | 0.977716 | 0 | 0.977716 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s104/root_trials.jsonl` |
| digits_mlp__s114 | 20 | {'new': '128', 'old': '64', 'path': 'train.py', 'symbol': 'BATCH_SIZE', 'type': 'python_constant'} | 0.941504 | 5 | 0.977716 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s114/root_trials.jsonl` |
| digits_mlp__s124 | 20 | {'new': '64', 'old': '32', 'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'type': 'python_constant'} | 0.955432 | 3 | 0.983287 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s124/root_trials.jsonl` |
| digits_mlp__s134 | 20 | {'new': '64', 'old': '32', 'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'type': 'python_constant'} | 0.963788 | 1 | 0.972145 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s134/root_trials.jsonl` |
| digits_mlp__s144 | 20 | {'new': '64', 'old': '32', 'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'type': 'python_constant'} | 0.980501 | 2 | 0.994429 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s144/root_trials.jsonl` |
| digits_mlp__s154 | 20 | {'new': '64', 'old': '32', 'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'type': 'python_constant'} | 0.972145 | 0 | 0.972145 | `results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots/digits_mlp__s154/root_trials.jsonl` |

### Interpretation and recommendation

**Keep with a change to the proposer/liveness validation, not to the threshold.** Retain digits as a candidate node; keep it excluded from memory-on collection until a separately authorized repaired-proposer liveness check passes the existing D28 gate. The concrete candidate change is to make the summary explicitly identify already-evaluated active configurations and their measured outcomes, and direct the proposer away from repeating known non-improving edits; test a bounded diverse proposal sequence before deploying it. This is a recommendation, not an implementation or authorization for a new run. Sources: repeated ALPHA/BATCH_SIZE/MAX_ITER edits in the tables; D28 row in PLAN §10.

The two trial-1 incumbents are 0.977716 and 0.972145, both from HIDDEN_UNITS 32 → 64. Of 18 later trials, 10 tie and 8 are worse; none improves. Drops range from 0.005571 to 0.013928. The proposals are not all inert: training losses change and the batch/hidden-unit edits alter validation score, while several ALPHA/MAX_ITER changes tie at the printed metric precision. There are 12 novel configurations across 20 evaluations, 8 seen-before evaluations and invalid rate 0 (digits_mlp.json, criteria). This is a mixture of plausible but unsuccessful edits, repeated candidates and score-insensitive edits, not universally broken workers. Sources: per-trial tables; `results/r1/engineering/liveness_llm_20261014T140742Z/digits_mlp.json`.

Trial 1 is strong, but “unusually lucky” is not identified. Memory-off first scores range from 0.941504 to 0.980501, and both memory-on scores lie inside that range. Memory-off s104 already starts at 0.977716 and also has no later keeps; memory-off s114 starts at 0.941504 and improves five times. Four of the six memory-off roots improve after trial 1; two do not. The comparison changes first edits, harness version, sampling-seed behavior, budget and proposer context, so it is not a randomized estimate of memory’s effect or of winner’s-curse bias. T4 Proposition 9 is compatible with selection bias but these unaudited draws cannot establish it. Sources: memory-off table and live ledger metadata; T4 §5.

The exact summaries already show discarded outcomes, yet the manager repeats ALPHA and BATCH_SIZE edits. This establishes repetition **despite** visible failure history; it does not show that the summary causally steers the model toward those edits. No memory-on/off paired intervention was performed. Sources: M5–M10 in each campaign and their corresponding edits.

## Deviations from the prompt

1. The scripted run has no per-trial branch ledgers; the authorized addendum drops that DI control. No regeneration occurred. See the companion DI report.
2. The LLM verify response permits promotion as well as demotion. The author authorized observed-record definitions: all observed decision changes are promotions. See the companion DI report.
3. The stopped arm lacks collection_checks.json; the pinned runner raises before writing it. Failure enumeration uses preserved leaves and work ledgers, and never regenerates the missing result.
4. memory_context_built contains metadata, not summary text; the trial’s manager extra carries the text. Both sources are cited.
5. No exact failed-request timestamp/traceback was persisted. Request-event and server termination timestamps are reported rather than fabricated exception-time precision. SIGTERM source remains unknown.
6. Author follow-up permits resolving analysis-definition conflicts from data and documenting them, while retaining all safety rules. No experiment was resumed or retried.

## Preservation check

Every file read by this report builder was SHA-256 hashed before analysis and verified unchanged afterward. The hash manifest is retained in the fresh diagnostic scratch directory (`diagnosis_input_sha256.json`); it is not a new experimental result. No source logs, results, workers or existing batch directories were written.
