# Track S — independent review of the `tabular_mlp` STOP-3 submission (Phase 2 S1.1 cited + Phase 3 S0.4 on TASL-7 + TASL-7 pause drill)

**Independent review; written 14–15 Nov 2026 by a freshly spawned reviewer that had no part in the work.**
AI-assisted. Rounds 1–3 are recorded here; the operator answered every finding (commit `6aaa800e`, then
`94437415`) and this file is the final review. This file changes no pin, code, host state or run.

**Independence.** Every value below was re-derived from the runbook, the committed bytes, the TASL-7 host and the
copy-back — not from the operator's report. Where a statement rests only on the operator's record and cannot be
re-derived read-only (the 22:14Z precondition snapshot, the drill marker-touch time, the 22:22:57Z lease-free
observation, the 22:47Z end-state check), I say so explicitly. I did not accept any operator/phase conclusion as
evidence.

**Record reviewed (final).** `trackS-ops-20261030` at tip
`944374154b83008873395f31d771a9be3c738788` (fast-forward chain `7593ee5b` → `2ce10b8f` → `ce0da8cd` →
`ed48e978` → `6aaa800e` → `94437415`; `git rev-list --parents` and `merge-base --is-ancestor` verified);
operator worktree `.claude-worktrees/trackS-ops-20261030`, clean except this untracked review file. Report
`docs/r1/reports/TRACKS_S04_T7_TABULAR_20261114.md` (207 lines, sha256
**`469b8db1853deea2c521bff4fa111c00d0283f7593f89d3eca72e02f27ad7e9a`**); STATUS at tip (sha256
`f826d403aa6cdc62d9d7260be23597ddc3172b104741c750283f89cb228e5868`); copy-back
`results/r1/tracks/tabular_mlp/s04_t7_20261114/`. The amendments `6aaa800e` (Phase 2 + five MINOR answers) and
`94437415` (scratch-smoke row + `§9` cross-reference) touch only `docs/r1/STATUS.md` and the report — no
data/manifest/`SHA256SUMS`/script-under-test changes (verified by `git diff --name-status`; copy-back still 20/20).

**Authority read.** Track S operator runbook rev 3.3 — blob at
`13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, sha256
`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`, 641 lines (§0.1–§0.8, Phase 1, Phase 2,
Phase 3 incl. §3.0/§3.0b, §10, §11.3/§11.4; the file is docs-branch content, read from the commit object because
the worktree does not carry it). PLAN §10 `R1-TRACKS-A2U-STALE` and `R1-CACHEPROMPT-FALSE`; author STOP-1 decision
(a) and STOP-3 decision (a) (STATUS 9/11 Nov; `reports/TRACKS_PHASE3_20261109.md` §11); the digits TASL-7 S0.1
result `reports/TRACKS_S01_TASL7_RESULT_20261113.md` (k=2 method); the accepted host-move record
`reports/TRACKS_DIGITS_HOSTMOVE_20261112.md`.

## 1. Provenance and commits — PASS

- Linear fast-forward chain as above; commit times (CET): `2ce10b8f` 23:14:55, `ce0da8cd` 23:27:15, `ed48e978`
  23:49:33, `6aaa800e` 00:04:38 (15 Nov), `94437415` 00:08:13. `7593ee5b` is an ancestor; local reflog shows only
  these commits; no reset/rewrite in this phase.
- `origin/trackS-ops-20261030` and `tasl7` bare `trackS-ops-20261030` are both **`94437415`** (`git ls-remote`
  re-checked after each amendment). No force-push: every update was a fast-forward on the recorded chain.
- Record contents:
  - `2ce10b8f`: only `r1/tracks/ops/launch/tasl7_tabular_s04_20261114.sh` (81 lines, sha
    `2c1c1d52ec7879c87d55c9bb71f541c0223cf09b97356ec2cd2333cc827536c7`; worktree = committed blob). **The S0.4
    launcher did not change in any amendment.**
  - `ce0da8cd`: only the S0.1 re-run launcher (66 lines, then sha `e76945b9…`); **superseded unrun** by `6aaa800e`'s
    revision, final sha **`0f3d05befb05d7736e39fd9704906218371f1228b8f48a5450f9ab8e265fa520`** (81 lines).
  - `ed48e978`: report + STATUS + 20-file copy-back (23 files, +5315/−0).
  - `6aaa800e`/`94437415`: only `docs/r1/STATUS.md` (the Phase-2 bullet etc.; final STATUS sha `f826d403…`) and the
    report (final 207 lines, sha `469b8db1…`), plus the S0.1-launcher clarification in `6aaa800e` (`0f3d05be…`).
    `git diff --name-status ed48e978..94437415` = STATUS + report + the S0.1 launcher only; the copy-back tree and
    its `SHA256SUMS` are untouched (see §8).
- TASL-2: `ssh portal_zhixu` returns `connect to host 100.120.160.70 port 22: Operation timed out` (re-verified);
  no TASL-2 push is possible or attempted, and the deferred TASL-2 bare-repo push is recorded in report §10 and
  the STATUS entry. Local `refs/remotes/tasl2/trackS-ops-20261030` is still the old `78a1b65e…`.

### 1.2 The S0.1 re-run launcher is committed but not executed

Verified on TASL-7: no `$R/launch/tasl7_tabular_s01_20261114.sh`, no `out/tabular_mlp/s01_t7_20261114`, no
`logs/*s01t*`/`logs/*s01_t7_20261114*`, no scratch `s01_t7_20261114`, no `trks_s01t_*` session (only
`trks_watch`). The unit (sha `0f3d05be…`) is queued for the next phase, not run.

## 2. Preconditions as recorded (22:14Z) — consistent with everything re-checkable; source is operator record

Report §1 records lease FREE, tmux only `trks_watch`, no `trks_llm`/collector/llama-server/GPU compute app, no
priority/drill markers, old scenes preserved, new dirs absent, 526 G free, B2 draft not armed, and a full
old-scene preservation table. The 22:14Z snapshot itself has no machine-readable capture; what I re-derived:

- New dirs **are fresh**: TASL-7 birth times `out/tabular_mlp/s04_t7_20261114` and
  `scratch/tabular_mlp/s04_t7_20261114` = `2026-11-14 14:15:15.213 -0800` = **22:15:15Z** (created by the launcher
  itself; no earlier artifacts).
- Old scenes: see §9 (full table independently re-hashed; no Nov-14 mtime inside any old scene).
- Lease/compute/markers: the launch log records `lease: HELD` with only our server pid after start (`800412`,
  5202 MiB) — consistent with free-before-start; the launcher's marker/foreign-compute/lease guards would have
  refused otherwise, and it ran.
- Disk **526 G free (71 %)** re-checked. Disk and GPU idle are not permanently attributable to 22:14Z; they match.
- Pins now: `trks-status` `OK paper 8237fd02…`, `OK harness a3fedbb…`, `OK llama.cpp 620d2225…`, GGUF
  `OK 509287f7…`, `paper tracked-file modifications: 0`; `git status --porcelain` empty in
  `work/Agent_paper_B` and `work/autoresearch_harness` (harness HEAD `a3fedbb…`).
- B2: `origin/mac-b2-handoff-20261114` tip `2120956c3fdeb4767b894b7cb70e52afde490ad8`; the branch's
  `docs/r1/proposals/B2_HANDOFF_DRAFT_20261114.md` states **"DRAFT, NOT ARMED"**; no `~/r1_locks/*.active` marker
  on TASL-7. "Not armed" holds.

## 3. Launcher — deployed == committed; guards and command verified

- Host `$R/launch/tasl7_tabular_s04_20261114.sh` sha256 `2c1c1d52…` = committed blob at `2ce10b8f` = worktree file;
  `bash -n` OK both sides; structurally the reviewed `tasl2_s04r2_20261111.sh` with node/host/dir/session
  substitutions (diff checked line by line).
- Guards present: priority/drill markers; duplicate `trks_s04_t7` session; existing `--out`/`--work` without the run
  manifest (resumable only with `$NEW/manifest.json`); foreign GPU compute when no `trks_llm` of ours is up; lease
  free; fresh `k=1` server via `trks-servers 1`; bounded 900 s readiness poll on `127.0.0.1:18101/v1/models`;
  pid/GPU/lease logging. **The S0.4 launcher has no HEAD/dirty guard**; the report (after the fix) says so, and
  states correctly that `bin/trks` (sha `26a240fa…`) only injects `PIN`/`PROBE_PIN` flags. Pin evidence = the
  manifest/roots provenance + the precondition `trks-status` check.
- Exact collector command (copied `trks_s04_t7.cmd`, matching runbook Phase 3):
  `trks collect --phase S0.4 --node tabular_mlp --instances 10 --label ENGINEERING_ONLY --deadline 28800
  --stop-file $R/out/tabular_mlp/s04_t7_20261114/STOP --out … --work $R/scratch/tabular_mlp/s04_t7_20261114`,
  session `trks_s04_t7`, `TRKS_PORT=18101` (k=1).
- Launch log: 22:15:15Z start → 18101 ready 22:15:17Z, pid 800412; resume 22:23:47Z → ready 22:23:49Z, pid 803220.
  Two collector `rc=0` lines (22:22:26Z, 22:43:11Z).

## 4. S0.4 result — all stated numbers re-derived — PASS

Manifest (sha256 `82ab48ff…`, 2 sessions):

| session | window (Z) | done (roots/forks/leaves/failed/exhausted) | status |
|---|---|---|---|
| #0 | 221517–222226 | 2 / 0 / 0 / 0 / 0 | `paused` (drill) |
| #1 | 222350–224311 | 8 / 0 / 0 / 0 / 0 | `complete` |

- **Total 10 committed roots, 0 failed, 0 exhausted**; 10 distinct `root_id` (s30000–s30009, all `status=ok`); no
  duplicate `root_id`; `s04_rows.jsonl` 154 rows with **no duplicate (instance, budget_index)**; `deadline_hit=false`
  in both sessions; `audit_runs` 215 + 655 = **870**.
- File hashes (host == copy): `roots.jsonl` `321fb1cf…`, `audit_runs.jsonl` `4601df1e…`, `s04_rows.jsonl`
  `62b86291…`, `manifest.json` `82ab48ff…`, `a2u_prior.json` `ba8f7783…`.
- **No `failed_units.jsonl`, no STOP** in the run dir; `find $R/out -name STOP` → none.
- Dry run (`trks_s04t_dry.log`): `roots_todo=0, forks_known=0, leaves_todo=0, exhausted=0`, `rc=0` at 22:46:45Z.
- **≤2 % rule: 0/(10+0+0) = 0.0 %** — passes.
- Manifest/root provenance: `paper_commit 8237fd02…`, `harness_commit a3fedbb…`,
  `manager_gguf_sha256 509287f7…`, `llama_build 620d2225…`, `host=TASL-7`,
  `gpu=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, `paper_dirty=false`, `harness_dirty=false`, label
  `ENGINEERING_ONLY`, `manager.kind=langgraph`, `cache_prompt=false`, `obs_inflation=1.0`.
- The collector log has no `STOP`/`Traceback`/`ReplayError`/transport lines and ends with the `complete` manifest
  record (`roots 8`).

## 5. TASL-7 pause drill — explicitly accepted as recorded, with one stated caveat

Verified against `logs/watch.log`, the collector exit file, `logs/STOP_FILES.s04t_20261114T222237Z.txt`, the drill
record and the final roots/rows:

- marker `touch $R/trks_drill.active` at **22:19:30Z** (operator-recorded time; see caveat); watcher
  `priority marker seen (…/trks_drill.active): pausing` **22:19:37Z** → reaction **7 s** (≤~1 min). Consistent with
  the watcher's 60 s poll phase (previous `marker gone` 10:16:36Z → the 22:19:36/37 poll).
- First root committed ~22:19:15Z (root_meta mtime; report says 22:19:16Z), so the ≥1-root precondition was met
  before the marker.
- Collector exit **22:22:26Z `rc=0`**; `done = {roots 2, forks 0, leaves 0, failed 0, exhausted 0, deadline_hit
  false, status "paused"}`.
- Watcher **"servers stopped; lease released" 22:22:37Z**; **no `FORCED`** line in `watch.log`; observed lease
  FREE / no llama-server / no `trks_llm` / no listener at **22:22:57Z** (operator-observed, ~20 s graceful
  shutdown).
- **Pause latency:** marker→watcher "servers stopped; lease released" = **3 m 07 s**; marker→observed lease-free =
  **3 m 27 s** (report labels both correctly; the runbook's step-6 "marker to lease released" is 3 m 07 s by the
  watcher's own line, 3 m 27 s by observation).
- Watcher STOP files **recorded before deletion** at 22:23:09Z: 3 paths, each `size=0`, sha256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — `out/digits_mlp/s05_t7_20261113/STOP`,
  `out/smoke/STOP`, `out/tabular_mlp/s04_t7_20261114/STOP` (inodes recorded). Those are exactly the three
  `manifest.json` directories under `$R/out` at the time, so the "every manifest dir" rule was applied completely.
- Marker removed 22:23:09Z; watcher `marker gone` **22:23:37Z**; **0 STOP files remain**; resume **22:23:47Z**
  (fresh k=1 pid 803220); roots grew **2 → 3** (s30002 mtime 22:26:12Z; waiter log 22:26:32Z `roots=3
  s04_rows=54`); final 10 distinct roots / 154 distinct `(instance, budget_index)`; `exhausted = 0`.
- **The digits S0.5 scene was not altered by the drill STOP:** all eight run-tree data files in
  `out/digits_mlp/s05_t7_20261113/` are byte-identical to the accepted S0.5 copy-back's `SHA256SUMS`
  (`audit_runs` `93939187…`, `forks` `bf638fa6…`, `leaves` `427faff6…`, `manifest` `68a0d6e0…`, `roots`
  `039b6955…`, `s05_calibration` `2e4c9a8c…`, `s05b_truncated` `cd296fd8…`, `_to_delete/STOP.retired…`
  `e3b0c442…`); only the scene directory mtime changed and the transient STOP is gone. `out/smoke/` still matches
  its committed copy (manifest `4aa160b1…`, roots `c6c8e656…`, s04_rows `619206dd…`, audit `37798e38…`,
  failed_units `a1d35488…`, failures `ff12d223…`).
- `FORCED` count 0. **Drill record: PASS.**

**Caveat (not a defect):** the marker-touch time (22:19:30Z) and the 22:22:57Z lease-free observation are
operator-recorded; the marker file is deleted, so they cannot be re-derived. They are consistent with the watcher
poll phase, the watcher log and the surviving artifacts, and all gate-relevant facts (7 s reaction, `paused`
manifest, no FORCED, lease released, STOPs recorded/deleted, resume invariants) are independently evidenced.

## 6. Phase 2 (S1.1) — existing record cited, no re-run; claim independently re-derived

Report §2 (and the STATUS bullet) now cites `results/r1/tracks/tabular_mlp/s11/tabular.json` sha256
**`5ac5154bf5aca6cbe84a9ed3f901b383b38b04f6ccc0ae47826964da4ac90eaa`** (9688 B, 30 seeds 37001–37030, `vary`,
ENGINEERING_ONLY; host `$R/out/tabular_mlp/s11/tabular.json` byte-identical — verified), with the 30 Oct
interactions and t-95 % CIs: HIDDEN_UNITS×BATCH_SIZE **+0.002647** [+0.001756, +0.003537];
HIDDEN_UNITS×LEARNING_RATE_INIT **−0.002659** [−0.003637, −0.001681]; BATCH_SIZE×LEARNING_RATE_INIT
**+0.004889** [+0.004049, +0.005730] (plus sd/se/bootstrap/main). I re-derived the pin-independence argument
myself:

- `git diff 9bb64ba 8237fd02 -- r1/tracks/probes/s1_factorial.py` is empty; the file's imports are stdlib +
  `numpy`/`scipy` only.
- `r1/c3/audit.py` and `r1/harness.py` are unchanged between those pins; `r1/c3/prior_model.py` changed
  (`d10b05b7`) but is not on the `run_config` path.
- On TASL-7, `git diff --name-only 115df37 a3fedbb` in `work/autoresearch_harness` touches **only**
  `control_plane/campaign.py` (3 added lines, `cache_prompt` in the LLM proposal-error record), `llm/*`,
  `manager/langgraph_manager.py` and a test; the seven S1.1-path harness modules and `nodes/tabular_mlp` are
  unchanged.
- Same host TASL-7 (move to a different host does not change node data; the report says so), third-party packages
  frozen (tracked in Phase 0 `pip_freeze.txt`).

S1.1 is stated as **descriptive and not a gate**; no re-run was made and no new `s11` directory created. This
closes the round-1 MAJOR.

## 7. liveness — PASS, numbers and gate semantics verified

`liveness/liveness.json` (`9ef2cdde…`): `pass=true`, `failed_criteria=[]`, `n_trials=400`, evaluated **173**,
novel **164** (0.9479769 → **0.948 ≥ 0.5**), `invalid_rate` **0.0225 < 0.3**, `keep_after_trial_1` **68 ≥ 1**,
`inactive_key_rejections=0`, `novelty_source=events`, source host TASL-7 / phase S0.4 / ENGINEERING_ONLY,
`generated_utc 20261114T224647Z`. The criteria are exactly the pinned code's
(`8237fd02:r1/liveness/check.py`: `NOVELTY_MIN=0.50`, `INVALID_RATE_MAX=0.30`, keep with `budget_index>1`), and the
phase returns 3 on failure (`collect.py:liveness_phase`), so the gate semantics match the runbook's
"liveness passes / D28 fails → STOP". 400 trials = 10 roots × W 40.

## 8. fit_prior and copy-back — PASS

- `a2u_prior.json` (821 B) sha256
  **`ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f`**; `sigma_node=0.0019`,
  `obs_inflation=1.0`, `meta.sources.s04_rows_sha256 = 62b86291…` = the run's `s04_rows.jsonl`; `stats.local`:
  rows 154, instances 10; `mu0=-0.0010202055015325802`, `tau0=0.000285`, `sigma_cmp=0.016842950361112007`,
  `tau_w=0.025258113052665` — all match report §7. `schema=tracks_a2u_prior/v2`, ENGINEERING_ONLY.
- After the fix the report no longer claims a fit_prior dry-run; it states liveness/fit_prior were run directly as
  CPU phases (no per-phase invocation log), with the only copied dry run being the S0.4 one. That is accurate.
- Copy-back: 20 payload files + `SHA256SUMS` (20 lines); `shasum -a 256 -c SHA256SUMS` → **20/20 OK**; host==copy
  for all **18** run-tree/log files (5 run tree + 4 `liveness/` + 9 `host_logs/`), re-checked after the
  amendments on both sides. The 2 further files (`operator_capture/drill_record.md`, `operator_capture/waiter_s04t.log`)
  are Mac-side captures — exactly the report's "18/18". Old tabular scenes were not copied into/over this dir.

## 9. Old-scene preservation — explicitly verified, no writes

Host old scenes (mtimes UTC, converted from host local −0800) and sha256, all checked against the committed Mac
copies and the recorded 30 Oct values; the amended report now carries this full table:

| scene | files / mtime | sha256 |
|---|---|---|
| `tabular_mlp/s01` | serial 10-30 10:20:21, concurrent 10-30 10:46:36 | `31d463c4…`, `d65c4c81…` |
| `tabular_mlp/s01_diag` | 10-30 11:48:28 | `44078998…` |
| `tabular_mlp/s01_diag_f1` | 10-31 01:27:54 | `a08d45ae…` |
| `tabular_mlp/s01_diag_f2` | 10-31 01:34:34 | `f6a19631…` |
| `tabular_mlp/s11/tabular.json` | 10-30 10:52:39 | `5ac5154b…` |
| `tabular_mlp/s01_rerun_INVALID…` (**31 Oct**) | serial 10-31 11:20:50, concurrent 10-31 11:21:28 | `8ca4740e…`, `81b72cc5…` |
| `tabular_mlp/inputs` | empty dir, 10-30 10:13:46 | — |
| `out/smoke` | 10-30 01:17:18–01:24:38 | `4aa160b1…`, `c6c8e656…`, `619206dd…`, `37798e38…`, `a1d35488…`, `ff12d223…` |
| `scratch/tabular_mlp/smoke` | 56 files (55 excl. `__pycache__`), files 10-30 00:56:21–01:24:38, dir 01:24:38 | observed host hashes, e.g. `roots/…s30000/root_trials.jsonl` `a161a3e7…`, `root_events.jsonl` `90006403…`, `node/train.py` `b29adf67…`; `$WORK` is host-only per runbook §0.8 and was not copied back |

`out/tabular_mlp/` itself has mtime 22:15:15Z only because the new `s04_t7_20261114/` subdirectory was created; no
file inside an old scene has a Nov-14 mtime and no old-scene file changed. The drill's transient STOP was created
and deleted in the three manifest dirs only, and the digits S0.5 scene's eight data files are byte-identical to its
accepted copy-back. **Preservation holds.**

## 10. Report/STATUS accuracy and the k caveat — PASS after the amendments

The recorded **k caveat** is present and correct in report §9 and the STATUS entry: tabular has **no new-pin
S0.1** (the only valid tabular S0.1 is the Oct-30 old-pin run, serial **0.870** / cross **0.875**, STOP; the 13 Nov
STATUS correction about the aborted TASL-7 attempt is separate and consistent); **S0.4 ran k=1**; the **S0.1 re-run
at k=2** is queued and its launcher `0f3d05be…` is **committed but not run**; **k=2 only if identity is 100 % on
both URLs and `cross_server_identity`**; **any identity <100 % is a STOP for the author, no k=1 fallback**; **no
S0.5 until both the STOP-3 review and the S0.1 review are accepted**. The report also records the amendment
provenance correctly (author's instructions relayed by the Lead on 14 Nov 23:11 CET and ~23:2x CET; no separate
author artifact/verbatim/PLAN row; the S0.4-then-S0.1 order deviates from the runbook's Phase 1→3 order as
instructed; k remains unset; S0.4 one-process caveat noted) and records **§3.0b as OPEN** (does not block STOP 3;
gates Phase 6 / 0.3(c) on TASL-7).

Also verified: B2 NOT ARMED; TASL-2 down and the bare-push deferral recorded; TASL-7 drill closed; old scenes
preserved; host end state idle. The submission is correctly labelled ENGINEERING_ONLY, "not a result", and does not
authorise S0.5. **No overclaim remains.**

## 11. Host end state and scope — PASS

At 23:09:01Z on TASL-7: tmux only `trks_watch` (created Oct 30); no `~/r1_locks/*.active`, no
`trks_drill.active`; no `llama-server`, no collector, no `trks_llm`; no listener on 1810x; no STOP under `$R/out`;
`flock -n ~/r1_locks/gpu0.lock true` succeeds; `trks-status` OK for all four pins and 0 paper modifications; disk
526 G free. A `find $R -newermt` sweep shows only the reviewed run/drill artifacts; no extra host writes. No
S0.5/S0.1 execution, no B2/X.7/sweep 2 artifacts; TASL-2 unreachable and untouched; no self-acceptance.

## 12. Findings record and resolutions

### BLOCKING
None.

### Round-1 MAJOR, now FIXED
- **MAJOR-1 — Phase 2 (S1.1) missing from the STOP-3 submission.** Runbook rev 3.3 Phase 2 requires it to be
  reported with the result and reviewed together with Phase 3. **Resolution `6aaa800e`:** report §2 and the STATUS
  bullet now cite the existing tabular S1.1 record (`s11/tabular.json` sha `5ac5154b…`, 30 seeds, the three
  interactions + CIs) with the pin-independence argument; descriptive, not a gate. I re-derived the code-path and
  harness claims independently (§6). **FIXED.**

### Round-1 MINORs, all FIXED/ANSWERED
- **MINOR-1 (pin-check wording):** report §3 now states the S0.4 launcher has no HEAD/dirty guard, that
  `bin/trks` only injects flags, and that pin evidence is the manifest/roots provenance + `trks-status`. **FIXED.**
- **MINOR-2 (§3.0b):** recorded as **OPEN** (not performed; no helper call; no author permission requested; does
  not block STOP 3; gates Phase 6 / 0.3(c) on TASL-7). **FIXED.**
- **MINOR-3 (fit_prior dry-run claim):** claim removed; report states liveness/fit_prior were run directly as CPU
  phases, no fit_prior dry-run artifact claimed. **FIXED.**
- **MINOR-4 (old-scene evidence):** full path/sha256/mtime table added (incl. `out/smoke` and
  `scratch/tabular_mlp/smoke`), `inputs` noted empty, the INVALID scene labelled 31 Oct, transient-STOP note added.
  The round-1 scratch-smoke row was wrong (30 files / "committed copies"); **`94437415`** corrects it to 56 files,
  the real mtime range, host-observed hashes and the `$WORK`-host-only basis — re-verified against TASL-7. Also a
  stale "k caveat §8" became §9. **FIXED.**
- **MINOR-5 (k amendment provenance/order):** recorded precisely (Lead relays, dates, no separate author artifact,
  deviation from Phase 1→3 order as instructed, k unset, one-process caveat). **ANSWERED.**
- **Non-blocking note (S0.1 launcher):** the unrun unit now clarifies the offset ordering and refuses unless exactly
  two llama-server processes are on 18101/18102 (k=2); new sha `0f3d05be…`. Still not run and not yet
  reviewer-accepted — its execution and the k decision remain the next phase.

### Residual, non-blocking notes
- The 22:14Z precondition snapshot, the drill marker-touch time, the 22:22:57Z lease-free observation and the
  22:47Z end-state check are operator record (not machine captures); they are consistent with every surviving
  artifact, and the reviewer itself re-verified the durable state at 22:51–23:09Z.
- The S0.4 launcher could gain the explicit HEAD/dirty guard for reuse; not required here because the run
  provenance is independently established.

## 13. What acceptance means

- **STOP 3 is accepted as a submission**: the `tabular_mlp` S0.4 on TASL-7 at pin `8237fd02` is 10 roots / 0
  failed / 0 exhausted at k=1, with the TASL-7 pause drill passed as recorded, liveness PASS on the recorded gate,
  the fit_prior recorded with the correct parameters and source hash, the copy-back verified 20/20 (host==copy
  18/18), the old scenes preserved, and the report/STATUS now complete and accurate (including the Phase 2
  citation and the k caveat).
- **This is ENGINEERING_ONLY and descriptive, not a result.** It is not an S0.5 authorization: S0.5 still waits for
  the `tabular_mlp` S0.1 re-run at k=2, its independent review, and the author's k decision; §3.0b remains open and
  gates Phase 6 / 0.3(c) on TASL-7. No B2/X.7/sweep 2.

Verdict: accepted
