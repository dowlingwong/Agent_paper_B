# B2 start receipt — TASL-7 (15 November 2026)

**Run ID:** `8709_20261115_b2`. **Run HEAD:** `8709dce792d45bbb5c05d9f7d239e19454efbb15` (branch `ops-b2-20261115`; based on `mac-b2-handoff-exec-20261115` @ `aeeab991`). **Output tree:** `/home/dowling/exam-x/work/b2_8709_20261115_b2`. **Operator:** DeepSeek Harness agent (AI-assisted).

## Gates (all closed before the marker)

| gate | evidence |
|---|---|
| exact-HEAD independent review | `reviews/B2_RUN_HEAD_REVIEW_20261115.md` — **VERDICT: ACCEPTED** |
| three-way reviewed base | code-unit review `Reviewed base:` and last `Accepted commit:` = `37282ec3…`; config `paper_commit` = `37282ec3…`; Mac `Claude outputs/READY.txt` item 26 `Reviewed base:` = `37282ec3…` (file SHA-256 `0ad9dd6f…`; `READY_RECORD.md`) |
| author gate on the staged checkout | `GATE_PASS 8709dce7… 53018aa7… phase b2` (capture `b2_final_gate_preflight_8709_20261115_b/gate.log`, `gate.exit`=0; pre-review `_a` run kept as a dry run) |
| occupancy + launch sequence review | `reviews/B2_OCCUPANCY_LAUNCH_REVIEW_20261115.md` — rounds 1–8, final **VERDICT: ACCEPTED** |
| B2 host preflight | capture `…/_b/`: `preflight.log` ends `PREFLIGHT_PASS: owned server exited and own lease descriptor closed`, `preflight.exit`=0; phase b2, 16 validated models, `qwen25_coder_7b` anchor, build `llama-server 620d222`, full offload 29/29 layers, 5,732 MiB GPU; post-checks no compute app + `flock -n gpu0.lock` free; `$RUN_DIR/preflight.ok` = `PREFLIGHT_OK` |

## Handover (marker first, per hand-off §5)

| step | evidence |
|---|---|
| bootstrap | `$RUN_DIR/bootstrap-receipt.txt`; four subdirs + empty owned receipt STATUS |
| deliver (pinned) | `$RUN_DIR/delivered-receipt.txt`: exec commit `78cec9ee…` (then the reviewed B2-preflight patch at `246e8e3e…`), 11 files with SHA-256, UTC; local `delivered-receipt.local.txt` in the exec worktree |
| prechecks | `PRECHECKS_PASS` in `$RUN_DIR/prechecks/prechecks.log`; GPU UUID, disk, lease, markers, watcher identity (pane 1388760/cmd bash, script `cf6884…`, watch.log position), no collectors/`trks_llm`/P.3a, no compute app, manifest/STOP inventories, venv+harness pins |
| marker | `$RUN_DIR/marker-receipt.json`: `run_id=8709_20261115_b2`, `head=8709dce7…`, dev/ino/sha recorded; local receipt STATUS `## 2026-11-15 — Track X B2 running` |
| STATUS publication | branch `mac-b1-20261107` @ `524f0a8a` (no force, remote verified); receipt `/tmp/b2_status_receipt_8709_20261115_b2.txt` (marker receipt SHA-256 recorded) |
| watcher | `watch.log`: `2026-11-15T16:28:39Z priority marker seen (/home/dowling/r1_locks/trackx_evidence.active): pausing`; no `FORCED`; no collectors/`trks_llm` were running |
| postwatch | `POSTWATCH_PASS`; fresh inventory; the watcher created the 4 STOP files beside the 4 known manifests (`tabular_mlp/s04`, `tabular_mlp/s05`, `digits_mlp/s05`, `smoke`) and nothing else; no STOP disappeared; no compute app; lease free |
| B2 preflight invocation | `b2_host_preflight.py` (reviewed round 8) reuses `b1_host_preflight.run` with the B2 `check_inputs`; installed with `preflight.sh` (`8513aa8c…`), old files preserved (`preflight.sh.delivered-a202f632`, `preflight.sh.patched-345e84dd`, `b2_host_preflight.py.v1-unvalidated`), recorded in `$RUN_DIR/patched-preflight.txt` |
| launch | `nohup bash "$RUN_DIR/receipt.sh"` → `exam_runner b2 --config …/exam_b2_v2.json --out /home/dowling/exam-x/work/b2_8709_20261115_b2`; runner pid recorded in `batch_state.json`; `gpu0.lock` held by the runner; first root `gemma4_31b/b2/off/digits_mlp__s9011` in progress; server interval started |

## Evidence preserved from failed attempts (no deletion)

- `/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2.attempt-20261115T162312Z` (first bootstrap/deliver/prechecks; prechecks passed, marker blocked by empty `.ok`)
- `…/_b/preflight.log.attempt-20261115T163156Z`, `preflight.exit.attempt-…` (stale noclobber evidence), and the failed 16:41 attempt kept as `…/preflight.log.attempt-20261115T164156Z` / `preflight.exit.attempt-…`
- smoke dirs `/home/dowling/r1_b1_engineering/b2_smoke_prechecks.s8cf4W5M` and `…prechecks2.1dMwtvLo` (prechecks end-to-end smoke, rc=0)

**First monitor capture:** `$RUN_DIR/monitor/…/capture.txt`; `batch_state.json` status `RUNNING`, `server_intervals` has the `gemma4_31b/b2/off` interval open.
