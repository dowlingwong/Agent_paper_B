# Track S — independent review of Phase 2 (S1.1) and Phase 3 (S0.4 + pause drill) on TASL-2, STOP 3

**Reviewer.** Fresh independent reviewer (DSH teammate `track-s-reviewer-p3`). I did not see the
operator's work in progress and I did not take its report, STATUS entry, commit messages or conclusions as
evidence. I re-read the authority documents, re-derived every number from the copied-back JSONs and the host
files, and re-verified the pins, launch script, logs, drill timeline, copy-back fidelity and host state
directly on TASL-2 (`ssh portal_zhixu`, read-only). I did not start/stop/signal anything, did not write on
any host, did not touch TASL-7 and did not run any Track S phase. The only file I wrote is this review.

**Artifacts under review.**
- Operator worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackS-ops-20261030`,
  branch `trackS-ops-20261030`, tip **`ced1e209ec3e756acfd6f0f47b365b3a4d227719`** (clean at review start;
  this review file is the only uncommitted change).
- Compose chain: **`ced1e209e`** (report + STATUS + S0.4 copy-back) → **`bde000f58`** (launch script) →
  **`8eb6b3024`** (author STOP-1 decision (a), the base of this phase) → **`5f2912a08`** (STOP 1 record).
  `ced1e209e` is a fast-forward, two-commit descendant of `8eb6b3024`; `bde000f58` is the launch-script
  commit the task names.
- `docs/r1/reports/TRACKS_PHASE3_20261109.md` (221 lines) and the 9 Nov `docs/r1/STATUS.md` entry.
- `results/r1/tracks/digits_mlp/s04/` — the STOP scene (`roots.jsonl`, `s04_rows.jsonl`,
  `audit_runs.jsonl`, `failed_units.jsonl`, `manifest.json`, `failures/*.json` ×13, `host_logs/`,
  `SHA256SUMS`, `STOP_STATUS.md`); Phase 2 citation of
  `results/r1/tracks/digits_mlp/s11/digits.json`.

**Authority read by me, not relayed.**
- Track S operator runbook **rev 3.3** at docs commit **`13badb0`**, sha256
  `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` (verified with
  `git show 13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`): §0.1–§0.8, Phase 2, Phase 3
  (3.0, the S0.4/liveness/fit_prior commands, "Done when", STOP 3), §10, §11.3/§11.4.
- Operator runbook O3 at `origin/docs/runbooks-09nov`, sha256
  `e27b36752a5f22a645a070c7720084ea8f157f176dca3b867aea8c54de34f867` (identical to the local copy).
- PLAN at `origin/docs/runbooks-09nov:docs/r1/PLAN.md`, sha256
  `0754adfb03cda6d51c4941dd58a54f6b2c9e9a5d0e89e10c8e3eaaf4c817d8fc`: row **R1-TRACKS-S01-RERUN**
  (line 779, clause (b), rev 3.3 at `13badb0` governs) and **R1-CACHEPROMPT-FALSE** (lines 720–724), and
  the R1-TRACKS-* rows.
- The author's 9 Nov scope (verbatim, as relayed to the operator): "S0.1 重跑允许用新会话名，只追加 watcher
  和 server 日志，在 TASL-2 上按 O3 执行。今晚 TASL-7 不跑 Track P。" and the STOP-1 decision (a) recorded in
  `8eb6b3024` ("继续 Phase 2/3"; future probe pins must write answer text + paper/harness versions).

All times UTC; the host's local clock is PST (UTC−8) and its `ls`/`stat` timestamps were converted.

## 1. Scope

In scope: tip/push provenance and commit contents; the Phase 2 S1.1 "identical code path, cite the 30 Oct
record" claim; Phase 3 setup (`k = 1`, launch script, readiness); the 3.0 pause drill; the S0.4 sessions,
dry-run plans, the 2 % STOP and the genuinely-unfinished state; the root cause of the deterministic
`ReplayError`; the deliberate non-run of liveness/fit_prior/`a2u_prior`; host end state, evidence
preservation and copy-back fidelity; and the scope boundary (Phase 4, Track P, B1, TASL-7).

Out of scope: any later phase, any code/pin/GGUF/flag change, any TASL-7 action (must not be touched), B1.
The TASL-7 half of the pause drill and 3.0b are recorded as open items, not executed.

## 2. Evidence checked

### 2.1 Provenance, commits, pushes, worktree

| Check | Result |
|---|---|
| tip / ancestry | `ced1e209e`; parent **`bde000f58`**, grandparent **`8eb6b3024`**; `5f2912a08` is STOP 1. Linear: a fast-forward descendant of `8eb6b3024`, two commits ahead. |
| origin ref | `git ls-remote origin` = **`ced1e209e…`**; `origin/trackS-ops-20261030` = `ced1e209e` |
| TASL-2 bare repo | `git --git-dir /home/dowling/r1_tracks/remotes/Agent_paper_B.git rev-parse refs/heads/trackS-ops-20261030` = **`ced1e209e…`** |
| normal push only | local tracking reflogs for both `origin/` and `tasl2/` show `…@{1}: update by push` on `8eb6b3024` then `…@{0}: update by push` on `ced1e209e`; every entry is `update by push`, none `forced-update`; no other branch pushed. |
| worktree | `git status --porcelain` empty at review start (this file is the only uncommitted change afterwards) |
| `bde000f58` contents | adds only `r1/tracks/ops/launch/tasl2_s04_20261109.sh`; file sha256 **`70160a986548f175e51fe90ce29b32eb47afa4f5b2dd7724bd5064e40c3c4617`**, identical on the host at `$R/launch/`; committed `2026-11-09T02:17:46+01:00` = **`01:17:46Z`**, i.e. **before** the host copy (`01:18:29Z`) and the first collector (`01:18:37Z`) |
| `ced1e209e` contents | adds `docs/r1/reports/TRACKS_PHASE3_20261109.md`, the +9-line STATUS entry, the 31-file `s04/` copy-back (30 hashed entries + `SHA256SUMS`; incl. `STOP_STATUS.md`, `host_logs/`, 13 failure JSONs); no `r1/` code change; no pin/GGUF/flag change |
| commit time | `ced1e209e` committed `2026-11-09T02:46:16+01:00` = **`01:46:16Z`**, after the last evidence event (`01:43:32Z`) |

The commit split matches the runbook's "commit the launch script, then run": the launch script was committed
43 s before the host copy and 51 s before the first session; the evidence/report commit came ~3 min after
the last activity.

### 2.2 Phase 2 — S1.1 cited, not re-run: the code-path claim re-derived

I re-ran the diffs myself in the paper repo and in the harness checkout
(`.claude-worktrees/harness-cacheprompt`, HEAD `a3fedbb…`; both old and new commits resolve locally):

| Path | `9bb64ba..d10b05b7` |
|---|---|
| `r1/tracks/probes/s1_factorial.py` | **empty diff** |
| `r1/c3/audit.py` (`run_config`) | **empty diff** |
| `r1/harness.py` | **empty diff** |
| `r1/c3/features.py` (`apply_edit`, imported by the probe's `design`) | **empty diff** |
| `r1/tracks/__init__.py`, `r1/tracks/probes/__init__.py`, `r1/__init__.py`, `r1/c3/__init__.py` | empty diffs |
| the probe's package path | `trks s11` → `python -m r1.tracks.probes.s1_factorial`; `run_pair` imports only `r1.c3.audit.run_config` and `r1.harness.import_harness`; `design` imports `r1.c3.features.apply_edit`; `run_config` imports only `r1.harness`, `autoresearch.manager.base.ManagerProposal`, `autoresearch.nodes.registry.load_registered_node`, `autoresearch.worker.local_worker.LocalWorker` |

The paper diff `9bb64ba..d10b05b7` does touch `r1/c3/prior_model.py` (+26/−4), `r1/exam/observer.py` (4
lines), `r1/tracks/collect.py` (17 lines), `r1/tracks/probes/determinism.py`, and tests — **none of these
is on the S1.1 path**: `prior_model.py` and `observer.py` are not imported by `features.py`, `audit.py`,
`r1/harness.py`, or `s1_factorial.py`; `collect.py` and `determinism.py` are the S0.1 collector path.

Harness `115df37..a3fedbb` changes exactly 5 files: `control_plane/campaign.py` (**+3 lines only** — I read
the hunk: a comment plus a two-line conditional adding `cache_prompt` to the failed-LLM-call error record in
`_propose_logged`), `llm/langchain_client.py`, `llm/providers.py`, `manager/langgraph_manager.py`, and
`tests/stage2/test_r1_cache_prompt.py`. The seven modules on the S1.1 path (`nodes/registry.py`,
`nodes/spec.py`, `manager/base.py`, `worker/local_worker.py`, `worker/base.py`, `worker/seeds.py`,
`common/logging.py`) and the node assets `nodes/` (incl. `nodes/digits_mlp`) are **unchanged**. The CPU-only
S1.1 path does not import `control_plane/campaign.py`; walking the imports above reaches only unchanged
modules. The operator's claim is **correct**.

The cited record is `results/r1/tracks/digits_mlp/s11/digits.json`, sha256
**`b4e364811dd9bf8ccbd2f4f6d011bf084bb01352a77ccc8520518b5e3a4c6174`** on both the Mac and the host
(host mtime 30 Oct 03:52, no new `s11` directory/file tonight). 30 seeds 37001–37030, split `vary`; the
three interactions and CIs in the report are exactly the JSON's (+0.005664 [+0.002967, +0.008361];
−0.003528 [−0.006133, −0.000924]; +0.008171 [+0.005268, +0.011074]). The 30 Oct Phase 1 report
(`TRACKS_PHASE1_20261030.md`, lines 15 and 156–184) records that these ran on TASL-2 under the then-pins
paper `9bb64ba` / harness `115df37`. So the citation is acceptable under the task-4 scope ("re-run into a
NEW output only if the s1 code path differs"), and there is no re-run and no new output.

Caveat (MINOR 2): the committed s11 JSON carries only `schema/label/node/split/seeds/results` — no pin
provenance — so its validity rests entirely on this git-derived code-path identity plus the same host. That
is exactly what I verified; it just should not be mis-described as self-provenanced.

### 2.3 Phase 3 setup — pins, `k = 1`, launch script, readiness

Host pins (read-only, each checkout `git status --porcelain` empty): paper
**`d10b05b738fc0e0dba54e0e692c248bedf095482`**, harness
**`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`**, llama.cpp
**`620d2225cc436ab0b001e3200e590e3b286ef9ab`** (`llama-server --version` = `0.7.0-dev (build 11669,
commit 620d2225c)`), GGUF sha256
**`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`**. The S0.4 manifest records the same
pins for all three sessions, with `harness_dirty=false`, `paper_dirty=false`, `host=TASL-2`,
`gpu=GPU-4d623e76-…`, `manager.cache_prompt=false`, `label=ENGINEERING_ONLY`, `server_url=…:18101/v1`.

The launch script `tasl2_s04_20261109.sh` (sha `70160a98…`) starts the `k = 1` server on 18101 only if
absent, waits (≤900 s) for `/v1/models`, then runs the exact rev-3.3 Phase 3 command via `trks-run`:

```
trks-run trks_s04 18101 collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/digits_mlp/s04/STOP --out $OUT/digits_mlp/s04 --work $WORK/digits_mlp/s04
```

The recorded `logs/trks_s04.cmd`, `trks_s04_dry.cmd` and `trks_s04_dry2.cmd` show exactly this command (the
dry runs differ only by `--dry-run`). Launch log: server start `01:18:37Z`, `/v1/models` ready `01:18:39Z`,
pid **689778**, lease **HELD**; resume start `01:29:15Z`, ready `01:29:17Z`, pid **776276**, lease HELD;
third launch `01:41:21Z` saw `tmux trks_llm already running (resume path)`, ready 0 s, pid 776276, lease
HELD. `llama_18101.log` shows the two S0.4 server-init blocks consistent with this: the first block's last
LLM activity is at relative 6 m 12 s = `01:24:51Z` (after which the paused unit finished on CPU and the
collector exited at `01:27:50Z`, then the watcher killed the server), and the second block runs
`01:29:15Z`→`01:43:23Z` (14 m 08 s, the resume/retry server).

### 2.4 Phase 3.0 — pause drill on TASL-2: PASSED, with the claimed latency verified

The host artifacts reproduce the drill step by step (the watcher was already running: `trks_watch` session
created `2026-11-08T23:58:08Z`, `watch.log` "watch started" `23:58:08Z`, same poll grid):

| Step | Evidence |
|---|---|
| pre-drill ≥1 root, lease held | root `s30001`'s root work dir was last written at **`01:20:07.405Z`** (commit-time proxy; `s30004` not until `01:24:49Z`), so the distinct-root count at `01:23:21Z` was **1**; server pid 689778 held the lease |
| `touch $R/trks_drill.active` | operator-noted **`01:23:21Z`** (the marker file is deleted, so this time is not independently recoverable; see §3 MINOR 4) |
| watcher sees the marker | `watch.log`: `2026-11-09T01:24:08Z priority marker seen (/home/dowling/r1_tracks/trks_drill.active): pausing` — 47 s later, within the ~1 min expectation; **86 × 60 s** after the watcher start |
| collector exits after the current unit | `logs/trks_s04.exit` line 1 `2026-11-09T01:27:50Z rc=0`; manifest `sessions[0].done = {roots:2, failed:3, exhausted:0, status:"paused"}` |
| servers stopped, lease released, no FORCED | `watch.log` `2026-11-09T01:28:08Z servers stopped; lease released` (**90 × 60 s** after watch start); `grep -c FORCED watch.log` = **0**; no `trks_llm`; the 18101 server was killed after the collector exited (the next init block is the resume) |
| watcher's STOP files recorded before deletion | watcher touches `STOP` in every manifest dir under `$R/out`: exactly `$R/out/smoke/STOP` and `$R/out/digits_mlp/s04/STOP` (the only two manifest dirs); both empty (`sha256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), mtime `01:24:08Z` = the watcher's seen second (report records both before deletion); the collector's `paused` status independently proves the `s04/STOP` existed; both dirs' mtimes are **`01:29:09.133782Z`**, the `find … -delete` time |
| marker removed / "marker gone" | `$R` directory mtime **`01:28:19.073780Z`** = the reported marker removal; `watch.log` `2026-11-09T01:29:08Z marker gone: resume by hand (…)` (**91 × 60 s**) |
| resume | STOP deletion `01:29:09Z`; server restart `01:29:15Z` (new pid 776276); same launch script re-run; collector `01:29:17Z` (manifest `sessions[1]`), command identical |
| resume invariants | distinct `root_id` 2 → **5** (`s30006` `01:31:14Z`, `s30007` `01:33:21Z`, `s30009` `01:38:07Z`); `root_id` duplicates: **none**; `s04_rows.jsonl` 77 rows with **77 unique (instance, budget_index)** pairs (5 committed instances only); `exhausted = 0` in the resume session and in the `01:40:15Z` dry run |

**Pause latency (marker → lease released), computed by me:** `01:23:21Z → 01:28:08Z` = **287 s = 4 m 47 s**
(the report's number is exact). The independently observable span, "priority marker seen" → "servers
stopped", is `01:24:08 → 01:28:08` = **240 s = 4 m 00 s**; the 47 s difference is within the watcher's
60 s poll interval (its polls fall at `23:58:08Z + n × 60 s`), and the operator-noted touch time is
consistent with it. The watcher's three lines are on that exact 60 s grid, which is strong internal
corroboration.

The drill followed rev 3.3 §3.0 steps 1–6: count/lease/`tmux` recorded, own drill marker only, expected
watch line, `rc=0` + `paused`, servers stopped + lease free + no FORCED, marker removed and "marker gone"
waited for, `find $R/out -name STOP -delete` then servers then the same launch script, and the step-5
invariants recorded. There is **no deviation** from the runbook in the drill itself. One evidence
limitation: the marker-touch time and "recorded before deletion" are only in the operator's report (no
persisted `STOP_FILES` record was saved); every other step is independently corroborated by filesystem
timestamps, `watch.log`, `trks_s04.exit` and the manifest.

### 2.5 S0.4 — sessions, dry-run plans, the 2 % STOP, unfinished state

| # | start–end (UTC) | rc | `sessions[n].done` | status |
|---|---|---|---|---|
| 1 (paused by drill) | `01:18:39–01:27:50` | 0 | roots **2**, failed **3**, exhausted **0** | `paused` |
| 2 (resume) | `01:29:17–01:39:27` | 0 | roots **3**, failed **5**, exhausted **0** | `complete` |
| 3 (retry per §0.6) | `01:41:21–01:43:23` | 0 | roots **0**, failed **5**, exhausted **3** | `complete` |

All three `trks_s04.exit` lines are `rc=0` (no exit-3 STOP path). The two dry runs use the identical
command plus `--dry-run` (`trks_s04_dry` `01:40:15Z rc=0`, `trks_s04_dry2` `01:43:32Z rc=0`):

| dry run | roots_todo | leaves_todo | exhausted |
|---|---|---|---|
| after #2 | **5** | 0 | 0 |
| after #3 | **2** | 0 | **3** |

So the phase is genuinely unfinished: `roots_todo = 2` is not 0 (only 5/10 instances committed:
`s30001, s30004, s30006, s30007, s30009`; `s30005`, `s30008` still have one retry left; `s30000`, `s30002`,
`s30003` are exhausted). No duplicate `root_id`; `s04_rows.jsonl` has 77 rows, all 77 `(instance,
budget_index)` pairs unique and covering only the 5 committed instances; `failed_units.jsonl` has 13 lines
(attempts, not units).

**2 % arithmetic (recomputed):** exhausted = 3 (s30000, s30002, s30003; 3 attempts each under
`--max-retries 2`); committed roots = 5; committed leaves = 0; rate = `3 / (5 + 0 + 3)` = **0.375 = 37.5 % >
2 %** → **STOP** under §0.6 and §10. The STOP is not sensitive to the two pending units: even if both
committed on a further retry, `3 / (7 + 3)` = 30 %; if both exhausted, `5 / (5 + 5)` = 50 %. No further
retry was made after #3, which is correct because the 2 % rule had already stopped the phase.

### 2.6 Root cause — the deterministic pinned-code `ReplayError`

All 13 failed attempts are the same class and the same mechanism, at the **same trial on every retry** for
each affected instance:

| unit | attempts | trial (all attempts) | message |
|---|---|---|---|
| s30000 | 3 | **13** | `stale edit: HIDDEN_UNITS is '2048', edit expects '1024'` |
| s30002 | 3 | **11** | same |
| s30003 | 3 | **12** | same |
| s30005 | 2 | **12** | `stale edit: HIDDEN_UNITS is '4096', edit expects '2048'` |
| s30008 | 2 | **20** | same as s30005 |

The tracebacks are genuine and match the **pinned** code exactly: I checked every frame against
`git show d10b05b7:…` / `git show a3fedbb:…` — `collect.py:1626` (`session → run_root`), `collect.py:842`
(`run_real_campaign`), `campaign.py:1862` (`_controller_hook`), `campaign.py:283`
(`controller.decide(view, mask)`), `a2u.py:632` (`decide`), `a2u.py:686` (`_e2_detail`), `a2u.py:539`
(`forecast`), `a2u.py:313` (`replay`), `features.py:352` (`featurize`), `features.py:340`
(`candidate → apply_edit`), `features.py:342` (wraps into `ReplayError`), `features.py:154` (raises the
stale-edit `ValueError`). `a2u.py` has no `except` around the replay/forecast path (its only handlers are
unrelated, lines 191/618), so the root unit is logged to `failed_units.jsonl` and retried; the collector's
session loop catches the generic exception. The host checkouts are clean, the manifest records
`harness_dirty=false` / `paper_dirty=false`, no code/pin/GGUF/flag change was made, and no further retry
followed the STOP.

The known-issue reference **does document this class**: `TRACKS_HOST_FACTS_20261030.md` §5.1, "A stale
manager proposal crashes A2-U's E2 forecast (pinned code; not fixed by me)", describes the same
`decide → _e2_detail → forecast → replay → featurize → candidate` path, the same uncaught `ReplayError`, the
same harness-side graceful precondition path (`PROPOSAL_PRECONDITION_FAILED`) that the controller does not
use, and the same `failed_units.jsonl` symptom. One qualification (MINOR 3): §5.1 calls the event
**stochastic** ("temperature 0.2: the re-run recovered"); under the current pins (`cache_prompt: false`,
fixed seed) the retries are **deterministic**, so the retry mitigation no longer applies.

**Classification: pinned-code defect — not an operator error and not an environment fault.** It is a
robustness gap in pinned `r1/tracks/a2u.py` (a live-but-stale manager proposal is a sanctioned consistency
check in `features.py` but is not tolerated by the controller's forecast, unlike the harness's own
precondition guard). The operator applied the runbook correctly (retry once, then STOP; no code change,
which §0.2/§10 forbid without an author PLAN row).

### 2.7 Deliberate non-run of liveness / fit_prior / `a2u_prior`, and the STOP state

The runbook Phase 3 order is S0.4 → `liveness` → `fit_prior`, each "after `trks_s04` has exited 0 with
status `complete`", and the phase's "Done when" requires the liveness pass and a recorded
`a2u_prior.json`. §0.6/§10 make more than 2 % failed units a STOP. S0.4 is not complete (`roots_todo = 2`),
the 2 % rule has already stopped the phase, and an `a2u_prior` built from 5/10 instances would be an invalid
prior. **Not running liveness/fit_prior/a2u_prior is required by the runbook and correct**; a downstream CPU
check on incomplete data would not un-stop the phase, and the runbook sequences them after completion.
No `s04/liveness*`, no `a2u_prior.json`, no `s05*` exists on the host or in the copied-back tree.

**The STOP state is correct:** Phase 3 is incomplete on TASL-2 (S0.4 5/10, no liveness, no prior), STOP 3
is reached and not self-accepted, and no Phase 4 work is authorised. The consequence for STOP 3 is recorded
in §4.

### 2.8 Host end state, evidence preservation, copy-back fidelity

Read-only checks on TASL-2 (repeated at `01:49–02:01Z`, stable):

| Check | Result |
|---|---|
| `tmux ls` | only `trks_watch` (pane command `/home/dowling/r1_tracks/bin/trks-watch`); `trks_llm` gone |
| lease | `flock -n ~/r1_locks/gpu0.lock true` succeeds → **FREE** |
| GPU / servers | `nvidia-smi --query-compute-apps` empty; `pgrep -x llama-server` empty; no `python -m r1.tracks.collect` |
| ports | no 18101/18102 listener |
| locks / markers | only `gpu0.lock` in `~/r1_locks`; no priority marker, no `$R/trks_drill.active` |
| STOP files | `find $R -name STOP` = **none** |
| disk | 184 G free, 90 % used |
| watch.log | 6 lines (3 old starts + 3 drill lines), sha256 **`2e74bc6969d8b4e8a90e61f83d31b2932b51ab15d54994ea9ba66825de1787aa`** = host = copy-back |
| old evidence | s11 `b4e36481…`; s01 serial `65388dfa…`, concurrent `005cadb3…`; s01_rerun serial `44556b00…`, concurrent `ec9fcb4f…`; smoke `manifest 5a9a555f…`, `roots a904d3db…`, `audit_runs 65461d5e…`, `s04_rows d944431b…`; s01_diag `4ada2f72…` — **all identical to the committed copies**, mtimes Oct 29/30 and 8 Nov; the 31 Oct INVALID re-run directory still has its 31 Oct mtimes (04:20–04:21 PST) — untouched |
| write audit | pre-existing files changed tonight are the append-only `logs/watch.log` and `logs/llama_18101.log` (expected), plus git objects in `remotes/Agent_paper_B.git` from the push, ignored `__pycache__` written by running Python in the pinned checkouts, and `.git/index` mtimes that read-only git queries (including mine) may refresh; no tracked file content changed (both checkouts `git status` empty); no evidence file was rewritten; `out/digits_mlp/s04` is new |
| copy-back | `sha256sum -c s04/SHA256SUMS` = all 30 **OK**; host hashes equal the copied hashes for `manifest.json 13d6afb9…`, `roots.jsonl 22c5c936…`, `s04_rows.jsonl 2341f3a0…`, `failed_units.jsonl f7072d02…`, `audit_runs.jsonl d9a4a409…`, `trks_s04.log bb893518…`, and all `host_logs/` + 13 `failures/` files |
| TASL-7 | not contacted (out of scope; must not be touched). No TASL-7 artifact appears in the commits or on TASL-2; "nothing written on TASL-7" is therefore **not independently verifiable tonight** and is recorded as a scope limitation, with no contrary evidence |

The s04 STOP scene is labelled (`STOP_STATUS.md` says it is not a completed S0.4 and must not be
overwritten); a later completed S0.4 must use a new `--out`/`--work` directory.

### 2.9 Scope boundary

- **Phase 4 not started:** no `s05`, no Phase 4 log/artefact on the host or in the commit; the report and
  the branch contents say so, and there is no Phase 4 authorisation.
- **No Track P:** no `trackp_evidence.active`, no Track P artefact on TASL-2 or in the commit; TASL-7 was
  not used (author scope).
- **No B1:** no B1 artefact in this worktree/commit or on TASL-2; B1 is a different worktree/task and cannot
  be confirmed from TASL-2 alone.
- **TASL-7 pause drill (3.0) not run, 3.0b open:** recorded in the report/STATUS as open. Implications:
  3.0b does **not** block STOP 3 but gates Phase 6 on TASL-7; the TASL-7 half of the 3.0 drill belongs to
  the `tabular_mlp` Phase 3, so Phase 3 is complete only for the TASL-2 node — the TASL-7 node's Phase 3
  (drill + 3.0b) remains open and must be done before its Phase 4/6.

## 3. Findings

No **BLOCKING** and no **MAJOR** finding. Four **MINOR** items, all documentary / evidence-basis; none
changes the STOP decision, the arithmetic, the pins, or the host state.

### MINOR 1 — Report §2 calls the third launch a "server start"
**Location:** `docs/r1/reports/TRACKS_PHASE3_20261109.md` §2 ("Readiness (all three starts): server start
`01:18:37Z` / `01:29:15Z` / `01:41:21Z`"). **Required fix/answer:** say the third entry is a **collector
start / readiness check against the still-running server** (pid 776276, already up since `01:29:15Z`; the
launch log says "tmux trks_llm already running (resume path)"), or label the entries "server/collector
start". The same paragraph already says pid 776276 was used by "resume and retry", so this is an internal
wording inconsistency only.

### MINOR 2 — "same frozen venv" is imprecise for the harness
**Location:** report §1 ("Same host (TASL-2) and the same frozen venv"). **Required fix/answer:** record
that the venv's third-party packages are frozen (I verified host Python 3.11.17 with numpy 2.4.6, scipy
1.17.1, scikit-learn 1.9.1, pandas 3.1.0, matching the committed Phase 0 `pip_freeze.txt`), but
`autoresearch_harness` is an **editable install** (`__editable__.autoresearch_harness-0.2.0.pth` →
`$R/work/autoresearch_harness/src`), so the effective harness code follows the checkout (now `a3fedbb`),
not a frozen copy. The citation remains valid because I verified the S1.1-path harness modules are
unchanged between `115df37` and `a3fedbb` (§2.2); the report should give that as the actual basis.

### MINOR 3 — The known-issue citation is stale on "stochastic"
**Location:** report §4.2 and `TRACKS_HOST_FACTS_20261030.md` §5.1. **Required fix/answer:** record that
under the current pin the failure is **deterministic** across retries (same trial/message), whereas §5.1's
"stochastic … the re-run recovered" describes the pre-`cache_prompt:false` observation. This matters for the
author: the 30 Oct "accept retries for now, quantify the rate on S0.4" decision is now answered — the rate
is 5/10 affected instances / 3 exhausted and retries do not recover — so the STOP requires a code
fix/new pin rather than another retry round. No edit to the historical host-facts record is needed; a
qualifying sentence in the STOP-3 report (and the author decision record) is.

### MINOR 4 — Two drill timestamps are only in the report; save a STOP-file record next time
**Location:** report §3, STOP-file table and the "touch" row. **Required answer:** confirm the STOP-file
record (paths, size 0, `e3b0c442…`, mtime `01:24:08Z`) was taken before the `01:29:09Z` deletion (the
mtimes and the collector's `paused` status are consistent with that), and note that the `01:23:21Z`
marker-touch time is operator-noted (the marker is deleted, so it cannot be recovered). The 4 m 47 s pause
latency depends on that noted time; the independently observable "seen → lease released" span is 4 m 00 s
and the 47 s difference is within the watcher's 60 s poll interval. For future drills consider writing a
small `STOP_FILES.txt` (paths + sha256 + mtime) next to `watch.log` before deletion so the record is
durable. No action is required for this STOP 3's verdict.

## 4. Explicit judgment on the S0.4 2 % STOP, the author decision, and the STOP-3 consequence

**The S0.4 STOP is correct.** 3 exhausted units over (5 committed roots + 0 committed leaves + 3 exhausted)
= `3/8 = 37.5 % > 2 %` per §0.6/§10; the retry path was followed once (session #3) and the rule then
stopped the phase; the phase is genuinely unfinished (`roots_todo = 2`, only 5/10 committed); no code, pin,
GGUF or flag was changed; no further retry was made. The cause is a **pinned-code defect** (A2-U's
uncaught `ReplayError` on a live-but-stale manager proposal), not an operator error and not an environment
issue; the operator behaved correctly throughout.

**The STOP state is correct.** `liveness`, `fit_prior` and `a2u_prior.json` were correctly **not** run on
incomplete data, and Phase 4 was not started. Phase 3 on TASL-2 is therefore incomplete and must not be
signed off as complete; the TASL-2 half of the 3.0 drill passed, while the TASL-7 half and 3.0b remain open
(3.0b does not block STOP 3 but gates TASL-7 Phase 6; the TASL-7 drill belongs to the `tabular_mlp` Phase 3).

**Author decision now needed.** Because §0.2 forbids changing pinned code without an author PLAN row, the
author must choose one of:
1. **Fix the pinned code under a new pin and a new PLAN §10 row** — make A2-U tolerate a live-but-stale
   proposal (e.g., catch `ReplayError`/`ValueError` in the replay/forecast path and fall back to the
   no-features path, as the harness's `PROPOSAL_PRECONDITION_FAILED` path does), commit the new paper (and
   harness, if needed) pin, re-run S0.4 in a **new `--out`/`--work` directory** (preserving this STOP scene),
   then resume Phase 3 at `liveness`/`fit_prior`; **or**
2. **Another author ruling** (e.g., accept a documented exception, change the S0.4 screen, or re-scope the
   phase).

The author should also treat the S0.4 figure as a screen (5/10 instances affected; 3 of the 5 failed
units exhausted, 2 with one retry left), per the host-facts §5.1 rule-of-three discussion, before S0.7/S3e,
and record the deterministic (rather than stochastic) nature of the failure under the current pin (MINOR 3).

**Consequence recorded for STOP 3:** the operator's STOP-3 submission is accepted as a **correct STOP**
(evidence reproducible, STOP correctly raised, no self-acceptance); the S0.4 2 % STOP stands; Phase 3 is not
complete on TASL-2 and the TASL-7 half/3.0b are open; Phase 4 (and anything later) must not start until the
author rules and a fixed-code S0.4 re-run completes in a new directory.

## 5. Acceptance checklist

| Requirement | Status | Evidence |
|---|---|---|
| Tip `ced1e209e`, fast-forward descendant of `8eb6b3024`; origin and TASL-2 bare at `ced1e209e`; normal pushes; worktree clean | **PASS** | §2.1 (parent `bde000f58`; `ls-remote`, bare-ref, `update by push` reflogs) |
| Launch script committed before use, same sha256 in commit and host | **PASS** | §2.1/§2.3 (`bde000f58`, `70160a98…`, `01:17:46Z` < `01:18:29Z`) |
| Report + STATUS + S0.4 copy-back committed; no code/pin change | **PASS** | §2.1 (`ced1e209e`, 33 files) |
| Pins on host and in the manifest: paper `d10b05b7`, harness `a3fedbb`, llama.cpp `620d2225`, GGUF `509287f7…`, dirty=false | **PASS** | §2.3 |
| Phase 2 claim: S1.1 code path identical between the old and current pins; no re-run | **PASS** | §2.2 (all relevant diffs empty; harness diff only LLM-path files; `campaign.py` +3 only) |
| Pause drill: marker seen, `rc=0` + `paused` (roots 2, failed 3, exhausted 0), servers stopped/lease released, no FORCED, lease free, no compute, STOP files recorded before deletion, markers, resume | **PASS** | §2.4 (timings, 60 s grid, dir mtimes `01:29:09Z`, `$R` mtime `01:28:19Z`, server blocks) |
| Pause latency 4 m 47 s | **PASS** | §2.4 (computed 287 s; observable span 240 s + 47 s within the 60 s poll) |
| Resume invariants: roots 2→5, no duplicate `root_id`, no duplicate `(instance, budget_index)` (77/77), exhausted 0 | **PASS** | §2.4/§2.5 |
| S0.4 sessions and dry-run plans exactly as reported; genuinely unfinished | **PASS** | §2.5 (manifest sessions, `01:40:15Z`/`01:43:32Z` dry runs) |
| 2 % arithmetic 3/(5+0+3) = 37.5 % > 2 % → STOP; no further retry | **PASS** | §2.5 |
| Root cause: same trial/message on retries; pinned-code traceback; no local modification; no code/pin change; known issue documents the class | **PASS** | §2.6 (13 attempts, per-unit counts, line-by-line pin check, clean checkouts) |
| liveness/fit_prior/a2u_prior deliberately not run — required and correct; STOP state correct | **PASS** | §2.7 |
| Host end state clean; old evidence untouched; copy-back faithful | **PASS** | §2.8 (`SHA256SUMS` all OK; hashes vs committed copies) |
| Phase 4 not started; no Track P; no B1; TASL-7 drill not run, 3.0b open; implications recorded | **PASS** | §2.9 |
| Review loop at STOP 3 (independent reviewer) | **PASS** | this file |

## 6. Verdict

Every number in the STOP-3 report that can be checked is exact: the tip and pushes are fast-forward and
normal, the launch script was committed before use and executed verbatim, the pins and the clean checkouts
are as declared, the 3.0 pause drill reproduces end to end (marker/hold/pause/lease/STOP-recording/resume;
4 m 47 s = 287 s computed, no FORCED), the resume invariants hold (2→5 roots, no duplicates, exhausted 0),
the S0.4 sessions and both dry-run plans are as reported, the 2 % rule gives 3/8 = 37.5 % > 2 % and the
phase is genuinely unfinished, and the deterministic `ReplayError` is a pinned-code defect whose traceback
lines match `d10b05b7`/`a3fedbb` exactly with no code/pin change. The Phase 2 "identical S1.1 code path"
claim is correct on all four paper files and all seven harness modules, and the `campaign.py` +3-line claim
is exact. The host is left clean and the earlier evidence is preserved; the copy-back verifies. The four
MINOR items are documentary (one is the pre-existing known-issue "stochastic" wording) and do not affect the
STOP, the arithmetic or the pins; the operator should answer/fix them in the follow-up commit. The S0.4
STOP stands and the author decision in §4 is now required.

**Verdict: accepted**
