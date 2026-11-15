# B2 execution plan — TASL-7 (15 November 2026)

**Run HEAD:** `8709dce792d45bbb5c05d9f7d239e19454efbb15` (branch `ops-b2-20261115`; author's three items on `mac-b2-handoff-exec-20261115` @ `aeeab991`). **Run ID:** `8709_20261115_b2`. **Output tree:** `/home/dowling/exam-x/work/b2_8709_20261115_b2`. **Operator:** DeepSeek Harness agent (AI-assisted). **Nothing of B1's `_a`/`_b`/`_c`/`_d` is moved, overwritten or deleted; Track S stays paused until B2 ends; the marker is created only after the HEAD review, the three-way base check, the post-review author gate and the re-reviewed occupancy/launch plan hold.**

## Bindings

| item | value |
|---|---|
| run HEAD | `8709dce792d45bbb5c05d9f7d239e19454efbb15` |
| reviewed base (`paper_commit`) | `37282ec37a715feaaea48dd621ae08678424accc` |
| staged checkout | `/home/dowling/r1_b1_engineering/b2_paper_final_<HEAD>/paper` (clean exact HEAD) |
| harness | `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`, clean) |
| venv (B1 `_d` frozen) | `/home/dowling/exam-x/work/venv` (Python 3.13.4; pins in `pins/venv_pins.txt`) |
| RUN_DIR | `/home/dowling/r1_b1_engineering/b2_handover_8709_20261115_b2` (created by `bootstrap.sh`) |
| local receipt STATUS | `$RUN_DIR/status-receipt.md` (bootstrap-created empty; the marker tool appends) |
| gate capture | `/home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_b` (post-review gate PASS; `_a` = pre-review dry run) |
| preflight capture/output | same capture dir; `--out /home/dowling/exam-x/work/b2_host_preflight_8709_20261115_a` (new direct child of `work_dir`) |
| marker | `~/r1_locks/trackx_evidence.active` (must be absent) |
| published STATUS | branch `mac-b1-20261107` (`docs/r1/STATUS.md`), clean separate checkout `.claude-worktrees/b1-status-20261115` (fcf52c09) |

## Order

0. **Deliver the reviewed exec files** (Mac → host, after `bootstrap.sh`): `deliver.sh` copies `prechecks.sh`, `inventory_after.sh`, `create_marker.sh`, `postwatch_check.sh`, `preflight.sh`, `start.sh`, `receipt.sh`, `publish_status.sh`, `pins/expected.txt`, `pins/venv_pins.txt` into `$RUN_DIR` with no-clobber `set -C`, verifies each SHA-256 and writes `delivered-receipt.txt`. `bootstrap.sh` creates `$RUN_DIR` (0700, fresh) and the **empty** receipt STATUS (the marker primitive opens it O_APPEND without O_CREAT) and three subdirs; no marker.
1. **Prechecks** (`prechecks.sh`, fail-closed): expected GPU UUID, disk ≥100 GB, lease (`flock -n gpu0.lock`; labelled a lease check, not part of the read-only census), locks and `*.active` markers absent, watcher identity (`pgrep`, `tmux list-panes`, watcher script SHA-256, `watch.log` line position), no Track S collectors, no `trks_llm`, no P.3a, no GPU compute app, full process census, manifest/STOP inventory with `find` traversal errors treated as STOP, explicit sibling STOP presence/absence per manifest, predecessor `_d` retirement record, STATUS-source hashes. It writes `PRECHECKS_PASS` and `prechecks/prechecks.ok` only when every check holds; any STOP exits non-zero with no `.ok`.
2. **Marker first** (`create_marker.sh`): requires `prechecks.ok`, an **empty owned regular** receipt STATUS, marker absent, clean exact HEAD; calls `b1_o2_marker.py create --phase b2`, validates the receipt (`run_id`, `head`, dev/ino, 64-hex sha) and then runs `inventory_after.sh` (post-marker inventory).
3. **Publish the running STATUS** (`publish_status.sh`, Mac): clean separate checkout at `mac-b1-20261107` equal to origin; marker receipt present on the host; append the exact heading `## 2026-11-15 — Track X B2 running` + run/HEAD lines; commit as Dowling Wong; `git push origin HEAD:refs/heads/mac-b1-20261107` (**no force**); verify the remote SHA equals the commit. A dirty/advanced checkout, failed push or mismatch is a STOP with the marker preserved; no force, no retry.
4. **Observe the watcher, then the handover check** (`postwatch_check.sh`): `watch.log` grows and contains `priority marker seen`; `FORCED` is a STOP; `servers stopped; lease released` (or no `trks_llm` running) expected; every touched STOP is a sibling of a known `manifest.json`; no GPU compute app; `flock -n gpu0.lock` free; P.3a absent; marker still present. Writes `postwatch/postwatch.ok` only on PASS.
5. **Host preflight** (`preflight.sh`): environment hygiene (all inherited `PYTHON*`/`GIT_*` unset), CAP/OUT/CACHE/PAPER/HARNESS/PY symlink and existence checks, `prechecks.ok`, `postwatch.ok`, marker present, exact `GATE_PASS <HEAD> <rule-sha>` line and `gate.exit` 0, harness pin and clean, **frozen-venv pin check** (`pins/venv_pins.txt`: Python 3.13.4, prefix, openai 2.36.0, langchain_openai 1.2.1, langchain_core 1.3.3, langgraph 1.1.10, pydantic 2.13.4, pydantic_core 2.46.4, httpx 0.28.1, pytest 9.0.3, numpy 2.4.4, scikit-learn 1.8.0), no compute app and lease free; runs `python -B -m r1.scripts.b1_host_preflight --head <HEAD> --out <new child>` with **no-clobber** capture; requires `PREFLIGHT_PASS` **and** rc 0, then re-checks no compute app and lease free; writes `preflight.ok`; exits with the preflight rc.
6. **Launch** (`receipt.sh` → `start.sh`): refuses if `b2.log`/`b2.exit` exist (no retry) or the batch tree exists; re-checks `prechecks.ok`, post-marker inventory, `postwatch.ok`, `preflight.ok`, `preflight.exit` 0, `PREFLIGHT_PASS`, exact `GATE_PASS` line, marker receipt `run_id`/`head`, P.3a absent, no compute app, clean exact HEAD, harness pin; unsets `LLAMACPP_CACHE_PROMPT`; `exec python -B -m r1.scripts.exam_runner b2 --config <run checkout>/r1/scripts/configs/exam_b2_v2.json --out <output tree>`; log footer `B2_EXIT=<rc>` and `b2.exit`.
7. **Monitor every ≤30 min** until the runner exits (separate `monitor/` captures): `batch_state.json`, manifests, journal invalid counts per candidate/mode/check, GPU/lease, log tail. A STOP is preserved and reported, never retried. Track S/P stay paused.
8. **After the run** (or a stopped run): retire the marker with `b1_o2_marker.py retire` + receipt under a reviewed post-run unit; publish `B2 done`/`B2 stopped` on the STATUS branch; hand back per hand-off §6 (manifests, batch_state, verified analysis, invalid-trial counts) and send the B2 report to independent review (STOP 6). Malformed retirement is a STOP (marker preserved).

## STOP conditions (preserve, report, no retry)

Any prechecks STOP (lease busy, marker present, watcher missing/ambiguous, collectors/`trks_llm`/P.3a running, GPU mismatch or compute app, disk <100 GB, traversal error, missing predecessor retirement); empty/failed marker receipt; STATUS checkout dirty/advanced/push failure; `FORCED` or an unexpected touched path; missing `POSTWATCH_PASS`; preflight rc≠0 or missing `PREFLIGHT_PASS`; dirty/mismatched run checkout; batch path exists; any launch-condition mismatch. A failed write, empty receipt, missing log/exit record or inconsistent HEAD is a STOP; nothing is retried, nothing is deleted, and the marker is not retired on an abnormal stop.

## Three-way base and gate (closed)

`reviews/B2_CODE_UNIT_REVIEW_20261114.md` `Reviewed base:` and last `Accepted commit:` = `37282ec3…`; the Mac `Claude outputs/READY.txt` item 26 `Reviewed base:` = `37282ec3…` (SHA-256 `0ad9dd6f…`, record in `READY_RECORD.md`); config `paper_commit` = `37282ec3…`. Post-review author gate on the staged checkout: `GATE_PASS 8709dce7… 53018aa7… phase b2` in the `_b` capture.
