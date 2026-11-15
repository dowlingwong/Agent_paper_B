# B2 execution plan — TASL-7 (15 November 2026)

**Run HEAD:** `8709dce792d45bbb5c05d9f7d239e19454efbb15` (branch `ops-b2-20261115`; author's three items on `mac-b2-handoff-exec-20261115` @ `aeeab991`).
**Run ID:** `8709_20261115_b2`. **Output tree:** `/home/dowling/exam-x/work/b2_8709_20261115_b2`.
**AI-assisted** (DeepSeek Harness agent, cluster/ops role). **Nothing of B1's `_a`/`_b`/`_c`/`_d` is moved, overwritten or deleted; Track S stays paused until B2 ends; no marker is created before the HEAD review, the author gate, the three-way base check and the re-reviewed occupancy plan hold.**

## Bindings

| item | value |
|---|---|
| run HEAD | `8709dce792d45bbb5c05d9f7d239e19454efbb15` |
| reviewed base (`paper_commit`) | `37282ec37a715feaaea48dd621ae08678424accc` |
| staged checkout | `/home/dowling/r1_b1_engineering/b2_paper_final_<HEAD>/paper` (created clean at the exact HEAD) |
| harness | `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` (`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`) |
| venv (B1 `_d`) | `/home/dowling/exam-x/work/venv` (Python 3.13.4) |
| RUN_DIR | `/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2` (new, absent) |
| local receipt STATUS | `$RUN_DIR/status-receipt.md` (**not** the run checkout's tracked STATUS) |
| gate+preflight capture | `/home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_b` (post-review; `_a` kept as the pre-review dry run) |
| preflight output | `/home/dowling/exam-x/work/b2_host_preflight_8709_20261115_a` (new, direct child of `work_dir`, created by the preflight) |
| marker | `~/r1_locks/trackx_evidence.active` (must be absent now) |
| published STATUS branch | `mac-b1-20261107` (`docs/r1/STATUS.md`), clean separate checkout |

## Order (hand-off §5)

1. **Gates.** HEAD review accepted (independent reviewer, exact HEAD); author gate on that HEAD returns the HEAD (post-review re-run: `GATE_PASS 8709dce7… 53018aa7… phase b2`, capture `b2_final_gate_preflight_8709_20261115_b/gate.log`; the earlier `_a` run is the pre-review dry run); three-way base check (`Reviewed base:`, last `Accepted commit:`, READY.txt) — see OPEN QUESTION about READY.txt; occupancy check + this plan re-reviewed for this HEAD and run ID.
2. **Read-only site inventory → `$RUN_DIR/prechecks.log`** (`prechecks.sh`): GPU UUID/compute apps, `gpu0.lock` free, disk, `~/r1_locks` markers (Track X/P absent), watcher pane/PID/log position, collectors (`--stop-file`), `trks_llm`, P.3a, all `manifest.json` parents + sibling `STOP` state and hashes, predecessor `_d` retirement verified. A running collector that cannot stop within 1 h, a `FORCED` risk, P.3a running, or any ambiguity is a STOP (no marker).
3. **Create the marker first** (`create_marker.sh`, `b1_o2_marker.py create --phase b2`) into a new `$RUN_DIR`, with the local receipt STATUS. Empty/failed receipt = STOP.
4. **Publish the running STATUS** from a clean separate checkout of `mac-b1-20261107` (Mac side), commit as Dowling Wong, push without force, verify remote.
5. **Observe the watcher** (`~/r1_tracks/logs/watch.log`): `priority marker seen`, `servers stopped; lease released` (or confirm no collector/server was running); inventory STOP touches; `FORCED`/unexpected touch = STOP. Then: `nvidia-smi` no compute app, `flock -n ~/r1_locks/gpu0.lock true`, P.3a absent/paused.
6. **Host preflight** (`preflight.sh`, after step 5, idle GPU): `python -B -m r1.scripts.b1_host_preflight --head <HEAD> --out <new child of work_dir>`; both gate and preflight exits 0 + `PREFLIGHT_PASS`; owned server exited, lease released. Any failure = STOP with marker preserved.
7. **Launch** (`receipt.sh` → `start.sh`): `exec python -B -m r1.scripts.exam_runner b2 --config $PAPER/r1/scripts/configs/exam_b2_v2.json --out <output tree>`; environment of B1 `_d` (`AR_HARNESS_ROOT` = staged harness, `LLAMACPP_CACHE_PROMPT` unset, frozen venv, threads 1).
8. **Monitor every ≤30 min** until the runner exits: `batch_state.json`, `manifests`, journal invalid counts per candidate/mode/check, GPU/lease, log tail; record each capture in `$RUN_DIR/monitor/`. STOP = preserve + report, never retry.
9. **Retire** the marker with `b1_o2_marker.py retire` + receipt after normal completion (or record a stopped run), publish `B2 done`/`B2 stopped` on the STATUS branch, then hand back per hand-off §6 (manifests, batch_state, verified analysis, invalid-trial counts) and send the B2 report to independent review (STOP 6).
