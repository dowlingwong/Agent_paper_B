# Track S — Phase 2 (S1.1) and Phase 3 (S0.4 + pause drill) on TASL-2, 9 November 2026 — **STOP 3**

**Written 9 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent); AI-assisted.**
**ENGINEERING_ONLY.** Not a result. Phase 3 on TASL-2 ended at a **STOP** under the 2 % failed-units rule; Phase 4+
not started and nothing later is authorised by this report.

**Authority.** Operator runbook O3 (`prompts/OPERATOR_RUNBOOK_20261104.md`, branch `docs/runbooks-09nov`);
Track S operator runbook **rev 3.3** at docs commit `13badb0`, sha256
`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` (rev 3.4/3.5 not of record),
Phase 2 and Phase 3; PLAN §10 R1-TRACKS-* and **R1-TRACKS-S01-RERUN**; author STOP-1 **decision (a)** of
9 Nov (recorded in `docs/r1/reports/TRACKS_S01_RERUN_20261109.md` §9 and the 9 Nov STATUS entries).
Scope tonight: **TASL-2 only** (`digits_mlp`), `k = 1` from STOP 1 (clause (b)); TASL-7 untouched; no Track P,
no B1; no pin/GGUF/flag change; append-only watcher/server logs; new output dirs; no deletion except the
drill's own watcher-created STOP files (recorded first).

**Pins:** paper `d10b05b738fc0e0dba54e0e692c248bedf095482` (detached, clean), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (clean), llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`
(`v0.7.0-dev`, build 11669), GGUF sha256
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`. The S0.4 manifest records them itself
(`sessions[*].provenance`: `paper_commit`, `harness_commit`, `manager_gguf_sha256`, `llama_build`,
`host=TASL-2`, `gpu=GPU-4d623e76-…`, `harness_dirty=false`, `paper_dirty=false`) — this closes the pin-provenance
gap noted for the probe JSON (reviewer MINOR 2).

**State before Phase 3** (`2026-11-09T01:16Z`): TASL-2 reachable; no tmux server beyond `trks_watch`; lease free;
no llama-server / GPU compute app; no priority or drill marker; no stale STOP under `$R/out`; `s04` did not
exist in `out/` or `scratch/`; disk 184 G free (90 % used); watcher running.

## 1. Phase 2 — S1.1 interaction check (`digits_mlp`): existing record cited, no re-run

The 30 Oct S1.1 record `results/r1/tracks/digits_mlp/s11/digits.json` (sha256
`b4e364811dd9bf8ccbd2f4f6d011bf084bb01352a77ccc8520518b5e3a4c6174`; identical sha256 on the host at
`$R/out/digits_mlp/s11/digits.json`) is cited as **pin-independent node-data analysis**, because the S1.1
code path is **identical** between the pins under which it was produced (`9bb64ba` / harness `115df37`) and the
current pins (`d10b05b7` / harness `a3fedbb`):

- `git diff 9bb64ba d10b05b7 -- r1/tracks/probes/s1_factorial.py` is **empty** (probe unchanged).
- Its paper dependencies are unchanged: `r1/c3/audit.py` (`run_config`) and `r1/harness.py` both have an empty
  diff; `r1/c3/prior_model.py` changed but is **not** on the S1.1 path (`run_config` imports only
  `r1.harness`, `autoresearch.manager.base.ManagerProposal`, `autoresearch.nodes.registry.load_registered_node`,
  `autoresearch.worker.local_worker.LocalWorker`).
- The harness `115df37..a3fedbb` diff touches only `control_plane/campaign.py` (+3 lines in the LLM
  `_propose_logged` error record), `llm/langchain_client.py`, `llm/providers.py`, `manager/langgraph_manager.py`
  and a test. The S1.1 path's harness modules (`nodes/registry.py`, `nodes/spec.py`, `manager/base.py`,
  `worker/local_worker.py`, `worker/base.py`, `worker/seeds.py`, `common/logging.py`) and the node assets
  `nodes/digits_mlp` are **unchanged**; `control_plane/campaign.py` is not imported by the CPU-only S1.1 path
  (the 3 added lines are in LLM proposal-error logging, unused by S1.1).
- Same host (TASL-2); the venv's **third-party packages are frozen** (Python 3.11.17; numpy 2.4.6,
  scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0, matching the committed Phase 0 `pip_freeze.txt`). But
  `autoresearch_harness` is an **editable install** (`__editable__.autoresearch_harness-0.2.0.pth` →
  `$R/work/autoresearch_harness/src`), so the effective harness code follows the checkout (now
  `a3fedbb`), not a frozen copy. The citation therefore rests on the **verified code-path identity** above
  (the S1.1-path harness modules and node assets are unchanged between `115df37` and `a3fedbb`), not on a
  "frozen venv" claim.

Therefore **no re-run was made** and no new `s11` directory was created. Record (30 seeds 37001–37030,
`vary` split, `n = 30`, ENGINEERING_ONLY):

| pair | levels | interaction | sd | se | t-95 % CI | bootstrap-95 % CI | main A | main B |
|---|---|---|---|---|---|---|---|---|
| HIDDEN_UNITS × BATCH_SIZE | 32/64 × 64/128 | **+0.005664** | 0.007222 | 0.001319 | [+0.002967, +0.008361] | [+0.003064, +0.008078] | +0.013417 | −0.008217 |
| HIDDEN_UNITS × LEARNING_RATE_INIT | 32/64 × 1e-3/0.002 | **−0.003528** | 0.006976 | 0.001274 | [−0.006133, −0.000924] | [−0.005942, −0.001207] | +0.008821 | +0.004735 |
| BATCH_SIZE × LEARNING_RATE_INIT | 64/128 × 1e-3/0.002 | **+0.008171** | 0.007774 | 0.001419 | [+0.005268, +0.011074] | [+0.005478, +0.010864] | −0.006964 | +0.010585 |

S1.1 is reported with the result and is **not a gate**.

## 2. Phase 3 setup — servers `k = 1` and readiness gate

Committed launch script `r1/tracks/ops/launch/tasl2_s04_20261109.sh` (commit `bde000f58`; sha256
`70160a986548f175e51fe90ce29b32eb47afa4f5b2dd7724bd5064e40c3c4617` on host and Mac), run as
`ssh portal_zhixu bash /home/dowling/r1_tracks/launch/tasl2_s04_20261109.sh`. It starts the `k = 1` server in
`tmux trks_llm` (`$R/bin/trks-servers 1`, port **18101** only) if absent, waits (bounded, 900 s) for
`http://127.0.0.1:18101/v1/models` to answer with `r1-manager`, then launches the collector as its own tmux
session `trks_s04` via `trks-run`. Re-running the same script after a pause resumes S0.4.

Readiness across the three S0.4 launches. The first two are **fresh server starts** (`01:18:37Z`,
`01:29:15Z`); the third (`01:41:21Z`) is a **collector start / readiness check against the still-running
server** — the launch log says "tmux trks_llm already running (resume path)", pid **776276** was already up
since `01:29:15Z`, and no new server was started. `/v1/models` was ready at `01:18:39Z` / `01:29:17Z` /
`01:41:21Z` (≈0–2 s). Server pids: **689778** (first, fresh) and **776276** (started fresh at resume
`01:29:15Z`, then reused by the retry collector). Lease **HELD** before every collector call; server command
line recorded in `host_logs/trks_s04.cmd` and the manifest provenance. The exact collector command (rev-3.3 Phase 3):

```
trks-run trks_s04 18101 collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/digits_mlp/s04/STOP --out $OUT/digits_mlp/s04 --work $WORK/digits_mlp/s04
```

## 3. Phase 3.0 — pause drill on TASL-2: **PASSED**

Run exactly as rev 3.3 §3.0, on Track S's own drill marker. Timestamps UTC.

| Step | Observation |
|---|---|
| Pre-drill (`01:23:21Z`, once ≥1 root committed) | distinct committed `root_id`s = **1**; tmux = `trks_llm`, `trks_s04`, `trks_watch`; `flock -n ~/r1_locks/gpu0.lock true` **fails** (lease held); GPU compute app = server pid 689778; **0** `FORCED` in `watch.log` |
| `touch $R/trks_drill.active` | **01:23:21Z** |
| `watch.log` "priority marker seen (…/trks_drill.active): pausing" | **01:24:08Z** (47 s later, within ~1 min) |
| `trks_s04` exits | **01:27:50Z**, `trks_s04.exit` = `2026-11-09T01:27:50Z rc=0` |
| manifest `sessions[-1].done.status` | **`"paused"`** (done: roots=2, failed=3, exhausted=0) |
| `watch.log` "servers stopped; lease released" | **01:28:08Z** |
| After pause | only `trks_watch`; `flock …` **succeeds** (lease free); no GPU compute app; no llama-server; **no** `FORCED` line |
| **Pause latency (marker → lease released)** | **4 m 47 s = 287 s** |

**STOP files created by the watcher — recorded before deletion (runbook resume step):**

| path | size | sha256 | mtime |
|---|---|---|---|
| `$R/out/smoke/STOP` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-11-09 01:24:08Z |
| `$R/out/digits_mlp/s04/STOP` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-11-09 01:24:08Z |

**Record-before-delete confirmation (reviewer MINOR 4).** The STOP-file record above was taken at
`01:28:19Z`–`01:28:2xZ`, i.e. **before** the `find $R/out -name STOP -delete` at `01:29:09Z`; the table's
mtimes (`01:24:08Z`, the watcher poll that touched them) and the collector's `done.status = "paused"` are
consistent with that ordering. The **`01:23:21Z` marker-touch time is operator-noted** — the marker has been
deleted, so it cannot be recovered from the host; the pause latency **4 m 47 s = 287 s** rests on that noted
time. The independently observable "priority marker seen → servers stopped; lease released" span is
`01:24:08Z → 01:28:08Z = **4 m 00 s**`, and the extra 47 s is the marker sitting until the watcher's next
60 s poll. **Forward instruction for the next drill:** write a small `STOP_FILES.txt` (paths + sha256 + mtime)
next to `watch.log` **before** deleting the STOP files so the record is durable on the host.

**Resume:** `rm $R/trks_drill.active` at **01:28:19Z**; `watch.log` "marker gone: resume by hand…" at
**01:29:08Z**; then `find $R/out -name STOP -delete` (0 remaining); servers restarted `k = 1` (pid 776276,
`01:29:15Z`); same S0.4 command re-run (`01:29:17Z`). **Resume invariants:** distinct `root_id` count grew from
**2** at the pause to **5**; **no duplicate `root_id`**; **no duplicate `(instance, budget_index)`** in
`s04_rows.jsonl`; `exhausted = 0` at the resume check. The drill passed on TASL-2.

## 4. Phase 3 — S0.4 dev campaigns: **STOP under the 2 % failed-units rule**

### 4.1 Sessions and dry-run plans

| session | start–end (UTC) | rc | done (that session) | status |
|---|---|---|---|---|
| `trks_s04` #1 (paused by drill) | 01:18:39–01:27:50 | 0 | roots 2, failed 3, exhausted 0 | `paused` |
| `trks_s04` #2 (resume) | 01:29:17–01:39:27 | 0 | roots 3, failed 5, exhausted 0 | `complete` |
| `trks_s04` #3 (retry per §0.6) | 01:41:21–01:43:23 | 0 | roots 0, failed 5, **exhausted 3** | `complete` |

Runbook §0.6 completion check (identical command with `--dry-run`; new sessions `trks_s04_dry` at
`01:40:15Z` and `trks_s04_dry2` at `01:43:32Z`):

| dry run | `roots_todo` | `leaves_todo` | `exhausted` |
|---|---|---|---|
| after session #2, `trks_s04_dry` | **5** | 0 | 0 |
| after session #3, `trks_s04_dry2` | **2** | 0 | **3** |

So S0.4 is **not finished** (dry-run `roots_todo` never reached 0): only **5/10 instances** committed
(s30001, s30004, s30006, s30007, s30009); 5 remain (s30005 and s30008 still have one retry left; s30000,
s30002, s30003 are exhausted).

### 4.2 Root cause (pinned code; known issue; no code change made)

All 13 failed attempts are the **same deterministic pinned-code failure** already recorded in
`docs/r1/reports/TRACKS_HOST_FACTS_20261030.md` §5.1 ("A stale manager proposal crashes A2-U's E2 forecast
(pinned code; not fixed by me)"). Traceback (from `s04/failures/root__tracks_S04_digits_mlp__s30000.json`):

```
r1/c3/features.py:154 apply_edit -> ValueError: stale edit: HIDDEN_UNITS is '2048', edit expects '1024'
  raised from r1/c3/features.py:340 candidate
r1/tracks/a2u.py:632 decide -> _e2_detail -> 686 forecast -> 539 replay -> 313
  -> r1.c3.features.ReplayError:  trial 13: stale edit: HIDDEN_UNITS is '2048', edit expects '1024'
```

The stale `old` value is raised by `r1/c3/features.apply_edit` and is **not caught** in `r1/tracks/a2u.py`, so
the whole root unit is logged to `failed_units.jsonl` and retried. The retries are deterministic: each retried
attempt fails at the **same trial with the same message** (e.g. s30000 at trial 13 all three times, s30002 at
trial 11 all three times, s30003 at trial 12 all three times). Per the operator rules, **no code was edited**;
this needs an author decision (see §5).

**Deterministic under the current pin — the 30 Oct "retries for now" assumption no longer holds.**
`TRACKS_HOST_FACTS_20261030.md` §5.1 recorded this class as "stochastic … the re-run recovered", and the
30 Oct decision was to accept retries for now and quantify the rate on S0.4. Under the current pins (explicit
`cache_prompt: false`) every retry reproduces the failure at the **same trial with the same message**
(s30000 t13 ×3, s30002 t11 ×3, s30003 t12 ×3, s30005 t12 ×2, s30008 t20 ×2), so **retries do not recover**;
the S0.4 rate is **5/10 instances affected and 3 units exhausted**. The 30 Oct question is therefore answered:
the STOP calls for a **pinned-code fix under a new pin/PLAN row** (A2-U to tolerate a live-but-stale proposal,
e.g. catch `ReplayError`/`ValueError` in the replay/forecast path and fall back) or another author ruling —
**not another retry round**. No edit is made to the historical host-facts record; this report and the
author-decision record carry the qualifying sentence.

Attempt counts (`failed_units.jsonl`, `--max-retries 2` ⇒ 3 attempts allowed):
s30000 **3**, s30002 **3**, s30003 **3** (all exhausted), s30005 **2**, s30008 **2**.

### 4.3 The 2 % rule (rev 3.3 §0.6) and the STOP

`failed units are permanently failed units … exhausted`; rate = Σ exhausted / Σ (committed roots + committed
leaves + exhausted), over the phase's shards. For this single-shard S0.4:
**exhausted = 3** (s30000, s30002, s30003), **committed roots = 5**, **committed leaves = 0**
(no forks/leaves), so **3 / (5 + 0 + 3) = 37.5 % > 2 % → STOP** (runbook §0.6 and §10 "More than 2 % failed
units in a phase → STOP"). The retry path of §0.6 was followed once (session #3); the rule now stops the phase,
so no further retry was made.

Also checked and clean: **no duplicate `root_id`**; **no duplicate `(instance, budget_index)`** in
`s04_rows.jsonl` (77 rows); `roots.jsonl` has exactly 5 committed roots; `s04_rows.jsonl` covers only the 5
committed instances.

## 5. Not run, and open items

- **liveness (D28) and `fit_prior` / `a2u_prior.json` were NOT run.** The runbook Phase 3 order is
  S0.4 → liveness → fit_prior, and §0.6/§10 stop the phase at the 2 % rule. Running `fit_prior` on 5/10
  instances would produce a prior from an incomplete dev-campaign set, so it was deliberately not created.
- **Phase 3.0 pause drill on TASL-7: not run** (TASL-7 out of scope tonight per the author; no Track P, no
  Track S on TASL-7 until O1). Recorded **OPEN**.
- **Phase 3.0b Track P integration check (TASL-7): not run**, **OPEN**; per the Lead it does not block STOP 3
  but gates Phase 6 on TASL-7.
- The overall Phase 3 "pause drill on both hosts" is therefore complete on TASL-2 only; the TASL-7 half and
  3.0b remain open for a later TASL-7 window.

## 6. Host end state (TASL-2, verified `2026-11-09T01:44:37Z`)

`trks_llm` stopped (only the session this phase started); `trks_watch` **left running**; lease
**LOCK-FREE**; **no** GPU compute app; **no** 18101/18102 listener; **no** llama-server; only `gpu0.lock` in
`~/r1_locks` (no priority/drill marker); **0** STOP files under `$R/out`; `watch.log` 6 lines (the original 3
plus the drill's 3, append-only); disk 184 G free, 90 % used. Old Oct-30/31 and STOP-1 evidence untouched; the
only pre-existing files appended are the append-only watcher/server logs.

## 7. Evidence copied back (under `results/r1/tracks/digits_mlp/`)

- `s04/` — the **STOP scene**: `roots.jsonl`, `s04_rows.jsonl`, `audit_runs.jsonl`, `failed_units.jsonl`,
  `manifest.json`, `failures/*.json` (13 attempt tracebacks), plus `host_logs/` (launch log, `trks_s04.*`,
  `trks_s04_dry.*`, `trks_s04_dry2.*`, `watch.log`). 528 KB; `SHA256SUMS` verifies; a `STOP_STATUS.md` at its
  root states it is a STOP scene, not a completed S0.4. **A later completed S0.4 must use a new directory and
  must not overwrite this STOP scene.**
- Key hashes (all recorded in `s04/SHA256SUMS`): `roots.jsonl` `22c5c936…`, `s04_rows.jsonl` `2341f3a0…`,
  `failed_units.jsonl` `f7072d02…`, `manifest.json` `13d6afb9…`, `audit_runs.jsonl` `d9a4a409…`,
  `host_logs/trks_s04.log` `bb893518…`.
- Phase 2: no new output (existing `results/r1/tracks/digits_mlp/s11/digits.json`, sha256 `b4e36481…`,
  cited in §1; unchanged).

## 8. STOP 3 — what the independent reviewer must check

1. The pins on the host and in the S0.4 manifest provenance; the two committed launch scripts
   (`bde000f58` / `064fa470…` for STOP 1) and that they were committed before use.
2. The drill: marker time, the 3 `watch.log` lines, `rc=0`, `done.status = "paused"`, lease released, no
   `FORCED`, the recorded STOP files (paths + sha256) before `find … -delete`, the resume invariants, and the
   pause latency.
3. That S0.4 was **not** actually finished: the two dry-run plans (`roots_todo 5` then `2`) and the 2 % rule
   arithmetic **3/(5+0+3) = 37.5 % > 2 %**; the deterministic `ReplayError` tracebacks and the per-unit attempt
   counts; no code/pin change was made.
4. That liveness / fit_prior / `a2u_prior.json` were deliberately not run on incomplete data, and that no Phase 4
   started.
5. Phase 2: the code-path identity argument and the cited S1.1 record (no re-run).
6. Host end state (lease free, no compute/listener, watcher running, no markers/STOP), evidence preservation,
   copy-back fidelity and hashes, commits/pushes (fast-forward only), and the open TASL-7 drill/3.0b items.

## 9. Status

- **STOP 3 reached. Not self-accepted.** The author/coordinating session decides how to handle the S0.4 2 % STOP
  (the known pinned-code stale-edit `ReplayError`): fix the pinned code under a new pin/PLAN row and re-run S0.4
  into a new directory, or another ruling. The operator did not change the code or the pin.
- Phase 4+ **not started**; no Phase 4 authorisation is implied by this report.
- Recorded forward instruction from the STOP-1 author decision (a) still stands: a future probe pin change must
  write the answer text and paper/harness version identifiers into the result file (not implemented here; no pin
  change made).

## 10. STOP 3 review record (independent review, accepted) and MINOR answers

- **Reviewer:** fresh independent reviewer (`track-s-reviewer-p3`), file
  `docs/r1/reviews/TRACKS_OPS_PHASE3_REVIEW_20261109.md` (397 lines, sha256
  `2a2cfae2d25d5d5fb46e2eb13297e675eb24bd19b25b42248a618bea1525ec2d`). **Verdict: accepted** —
  0 BLOCKING, 0 MAJOR, 4 MINOR (documentary). The reviewer re-verified the tip and pushes, the pins, the
  pause drill end to end, the 2 % arithmetic, the deterministic root cause, the deliberate non-run of
  liveness/fit_prior, the host state and the copy-back.
- **MINOR 1 (third launch called a "server start") — fixed in §2.** The `01:41:21Z` entry is now stated as a
  **collector start / readiness check against the already-running server** (pid 776276, started fresh at the
  resume `01:29:15Z`; launch log "tmux trks_llm already running (resume path)"); no new server was started.
- **MINOR 2 ("same frozen venv" imprecise for the harness) — fixed in §1.** The venv's third-party packages
  are frozen (Python 3.11.17; numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0, matching the
  committed Phase 0 `pip_freeze.txt`), but `autoresearch_harness` is an **editable install** from
  `$R/work/autoresearch_harness/src` (now `a3fedbb`), so the effective harness follows the checkout. The
  citation basis is the **verified S1.1-path code identity** between `115df37` and `a3fedbb`, not the venv.
- **MINOR 3 (stale "stochastic" citation) — answered in §4.2.** Under the current pin the stale-edit failure
  is **deterministic across retries** (same trial/message), unlike `TRACKS_HOST_FACTS_20261030.md` §5.1's
  pre-`cache_prompt:false` "stochastic … the re-run recovered" wording. This answers the 30 Oct "accept
  retries for now, quantify the rate on S0.4" decision: **5/10 instances affected, 3 units exhausted, and
  retries do not recover**, so the STOP requires a **pinned-code fix under a new pin/PLAN row** (or another
  author ruling), not another retry round. No edit was made to the historical host-facts record; this report
  and the author-decision record carry the qualifying sentence.
- **MINOR 4 (durable STOP-file record) — answered in §3.** The record was taken **before** the `01:29:09Z`
  deletion (`01:28:19Z`–`01:28:2xZ`; mtimes `01:24:08Z` and the collector's `paused` status are consistent).
  The `01:23:21Z` marker-touch time is **operator-noted** (the marker was deleted; the 4 m 47 s pause latency
  rests on it), while the independently observable "seen → lease released" span is `01:24:08Z → 01:28:08Z =
  4 m 00 s`, the extra 47 s being inside the watcher's 60 s poll. **Forward instruction for future drills:**
  save a small `STOP_FILES.txt` (paths + sha256 + mtime) next to `watch.log` **before** deleting the STOP
  files.

## 11. Author ruling at STOP 3 (11 November 2026): option (a)

The author answered STOP 3 (relayed by the Lead on 11 Nov 2026), verbatim:

> Track S STOP 3：选 (a)。等 Mac agent 的 A2-U 修复审查通过、新 pin 和 PLAN 行提交后，在新目录跑 S0.4，10 个 instance 全部重跑，然后接 liveness 和 fit_prior。旧的 s04 STOP 现场不动。

**Interpretation.** Option **(a)** is accepted: once the Mac-local agent's **A2-U fix** has passed its independent
review and the **new paper pin** and **dated PLAN §10 row** are committed and bind the fix commit, S0.4 is
re-run on TASL-2 in a **new `--out`/`--work` directory** — **all ten instances re-run from the start** (no
resume of this stopped scene) — and then `liveness` and `fit_prior` follow. **The existing `s04` STOP scene is
left untouched** (it is preserved under `results/r1/tracks/digits_mlp/s04/` and must not be overwritten).

**Operator obligations when the fix is relayed (not yet — the fix is not on origin at the time of this
recording).** Verify the fix branch/tip and that its independent review says accepted; verify the new paper pin
and the dated PLAN §10 row are committed and bind the fix commit; do not change the pin or code itself. Then:
fresh `k = 1` server (port 18101) with the readiness poll, the **same Phase-3 S0.4 command with
`--instances 10`** into new directories (e.g. `s04_r2_20261111`), append-only watcher/server logs, new session
names; after S0.4 exits 0 with status `complete` **and** the dry run shows `roots_todo = 0` / `leaves_todo = 0`
/ `exhausted` within the 2 % rule, run `liveness` and then `fit_prior`
(`--sigma-node 0.0066 --obs-inflation 1.0 --prior $OUT/a2u_prior_r2_20261111.json`), record the prior sha256,
stop the servers, verify the host state, copy back, write the rerun report + STATUS, and stop for a fresh
independent review. The 3.0 pause drill is **not repeated** for this rerun unless the Mac agent's material
changes the server/watcher path (decision to be recorded in the rerun report and flagged for the reviewer).
Phase 4 is **not** authorised by this ruling.
