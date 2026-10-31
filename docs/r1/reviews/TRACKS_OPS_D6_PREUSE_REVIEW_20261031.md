# Track S — D6 pre-use review: F1/F2 diagnostic extension and launch scripts

**Reviewer:** independent (fresh; not the author or the operator; no access to work in progress).
**Date:** 31 Oct 2026.
**Under review:** worktree `.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`, head
**`fc842b6d`** ("Track S D6: extend the diagnostic for the F1/F2 follow-ups (pre-use)"); diff
`79a38f7e..fc842b6d` (3 files, +119/−9).
**Runbook of record:** revision 3.3, sha256
`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`, read from
`docs/trackS-decisions-30oct` at `13badb0d` with
`git show 13badb0d:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`; section numbers below are that
revision.
**Labels:** `ENGINEERING_ONLY / DIAGNOSTIC`; not a phase, no `k`, no Phase 3. **I did not run a GPU job,
start a server, or run the diagnostic.**

## 1. Scope

I reviewed the three files added/changed by `fc842b6d`:

- `r1/tracks/ops/diag/cache_prompt_diag.py` — schema v2: new mode `absent` (no `cache_prompt` field),
  per-call and per-mode UTC timestamps, per-mode `request_example` and `modes_definition`,
  `first_call_cache_hits`/`misses`/`first_call_prompt_n_mean`, `usage_prompt_tokens_mean`, and a required
  `--resident-server-count` recorded in the output.
- `r1/tracks/ops/launch/tasl2_d6.sh` and `r1/tracks/ops/launch/tasl7_d6.sh` — new F1/F2 launch scripts.

I checked: whether `absent` sends exactly the pinned probe's `chat_payload` body; whether prompts, seeds
and the call schedule are still the pinned ones (`fixed_prompts`, `schedule(200, 3, 1, 0, 0)`); whether
`identity_rate`/`latency_stats`/`cpu_census` still come from the pinned module unchanged; whether the new
fields can silently misreport; whether the launch scripts' assertions work (pgrep pattern, `mapfile` under
`set -euo pipefail`, the `nvidia-smi` count); whether F1 makes no HTTP call before the run; whether the
flock rule is met; whether the out paths collide with the 30 Oct outputs; and whether `install.sh` updates
the installed copies. The only host-side process I started was a short `bash -c` `sleep` wrapper on TASL-7
(8 s, no GPU, no lock) to test `pgrep -f` matching; everything else on the hosts was read-only.

## 2. What I checked and how

### 2.1 Worktree, pins, installation

```
git rev-parse HEAD; git status --porcelain; git log --oneline -3
git diff --stat 79a38f7e..fc842b6d
git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests          # empty
git show 9bb64ba:r1/tracks/probes/determinism.py | sha256sum            # 081adb63…
sha256sum r1/tracks/probes/determinism.py                               # 081adb63…
sha256sum r1/tracks/ops/diag/cache_prompt_diag.py                       # 1b8409c7…
```

The worktree is clean at `fc842b6d`. The diff touches only the diagnostic and the two new launch scripts.
`git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests` is empty; the pinned probe is
byte-identical to `9bb64ba` (`081adb63…`). `cache_prompt_diag.py` does not exist at `9bb64ba` (it was added
on this branch), so the pinned probe is the only code being re-used.

Hosts (read-only):

```
ssh portal_zhixu / tasl7:
  git -C $R/work/Agent_paper_B rev-parse HEAD; git status --porcelain
  git -C $R/work/autoresearch_harness rev-parse HEAD; git status --porcelain
  git -C $R/opt/llama.cpp rev-parse HEAD; sha256sum $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf
  sha256sum $R/bin/cache_prompt_diag.py $R/bin/trks-diag; grep schema $R/bin/cache_prompt_diag.py
  ls -la $R/launch $R/out/<node>; find $R/out -name '*s01_diag_f*'
  tmux ls; ls -la ~/r1_locks; flock -n ~/r1_locks/gpu0.lock true; ss -ltn | grep 18101
```

| item | TASL-2 | TASL-7 |
|---|---|---|
| paper checkout | `9bb64ba`, `git status` 0 lines | `9bb64ba`, 0 lines |
| harness checkout | `115df37`, 0 lines | `115df37`, 0 lines |
| llama.cpp | `620d2225…` | `620d2225…` |
| GGUF sha256 | `509287f7…4d3c` | `509287f7…4d3c` |
| lease | free (`flock -n … true` succeeds) | free |
| `trks_llm` / port 18101 | absent / no listener | absent / no listener |
| installed diagnostic | **v1** `5012efc4…`, no `--resident-server-count` | **v1** `5012efc4…`, no such flag |
| installed `trks-diag` | `7ab8b5c9…` (unchanged) | `7ab8b5c9…` |
| `$R/launch` | only the 30 Oct `tasl2_diag_cache.sh` / `tasl2_s01.sh` | only the 30 Oct `tasl7_diag_cache.sh` / `tasl7_s01.sh` |
| `r1/tracks/ops/launch` in the host checkout | **does not exist** (checkout is at `9bb64ba`) | same |

`install.sh:16-20` copies `diag/trks-diag` and `diag/cache_prompt_diag.py` to `$R/bin`, so the
diagnostic/runner **will** be updated (v1 `5012efc4…` → v2 `1b8409c7…`). `install.sh` has **no step for
`launch/*.sh`**; the new D6 launch scripts would not be installed. The 30 Oct launch scripts in `$R/launch`
are byte-identical to the committed old scripts (`0d29c188…`, `58854080…`), i.e. they were copied by hand;
the D6 scripts need the same manual copy unless `install.sh` is extended. The hosts currently have the v1
diagnostic, which would reject `--resident-server-count` (fail-closed, but no run).

### 2.2 The diagnostic versus the pinned probe

Read line by line against `r1/tracks/probes/determinism.py` (pinned):

| pinned element | pinned probe | diagnostic | match |
|---|---|---|---|
| prompts | `fixed_prompts(n, node)[:n]` | `cache_prompt_diag.py:169` | yes |
| body | `chat_payload(prompt, seed, model, temperature=0.2, proposal_schema=…)` | `:170-171` | yes |
| schedule | `schedule(n, repeats, order_seed, 0, 0)` (serial, one client) | `:172` | yes |
| identity | `identity_rate(contents, repeats)` | `summarise`, imported at `:110` | yes |
| latency | `latency_stats(latencies)` | `summarise`, imported at `:110` | yes |
| CPU census | `cpu_census()` | `D.cpu_census()` at `:175,189` | yes |
| `/props`, GGUF hash | `server_props`, `sha256_path` | `D.…` at `:206,210` | yes |

The launch scripts pass `--n 200 --repeats 3 --order-seed 1`, so the schedule is
`schedule(200, 3, 1, 0, 0)`. I rebuilt that schedule locally and its head is
`(163,1), (7,2), (134,1), (86,0), (0,0), …`, identical to the `order_head` recorded in both 30 Oct
`s01_diag/cache_prompt.json` files. `request_example` is built from the same `payloads[0]` and (for
`true`/`false`) adds the same field (`:182-184`), so the body claim is checkable from the output.

`absent` is exact: `run_mode` does `payload = dict(payloads[i])` and only sets `cache_prompt` when
`flag is not None` (`:91-93`). I exercised this with a monkeypatched `post_full`: with `flag=None` the
posted payload had keys `messages, model, response_format, seed, temperature` and **no** `cache_prompt`;
with `True`/`False` the field was present; the shared base payload was never mutated. The per-call copy
also means `request_example` is not contaminated.

`identity_rate`, `latency_stats` and `cpu_census` are the pinned functions, unchanged; the pinned module
is byte-identical to `9bb64ba`.

### 2.3 New fields and timestamps

- `first_call_cache_hits`: for each prompt, the first **successful** call (error entries are skipped,
  `:117-121`) with `tokens.prompt_n == 1`. This is the correct "first successful call" semantics, and it
  reproduces the 30 Oct cache-warmth evidence from the v1 raw files: digits `true` 200/200 hits (the
  control was pre-warmed), tabular `true` 197/200 hits, both `false` runs 0/200 hits. So the metric works
  for the F1 purpose.
- `tokens_evaluated_total` and per-call `tokens` keep both `timings.prompt_n` (evaluated) and
  `usage.prompt_tokens` (total), as D6 asks.
- `usage_prompt_tokens_mean` is a mean over successful calls; it equals 639.635 (digits) / 645.635
  (tabular) on the 30 Oct data, matching the prior report's cross-mode check.
- Timestamps: `utc()` is `%Y-%m-%dT%H:%M:%S.%fZ` (`:38-39`); `started` is taken before `run_mode`,
  `finished` after (`:179-181`); per-call `utc` is recorded after the response returns (`:103`); `run_utc`
  is at report build (`:201`). All are ISO-UTC. Error calls have no `utc` (only `order`, `prompt`,
  `repeat`, `error`), so the "per call" timestamp is per **successful** call.
- `request_example` and `modes_definition` are present per mode and at top level; `absent` records null
  `cache_prompt` in the summary, which is the right representation.
- `--resident-server-count` is `type=int, required=True` (`:156-157`) and is copied to the output
  (`:200`); it is an operator assertion, not a measurement.

The synthetic edge cases (same code, synthetic `res`) expose one bug: when **all** first-call
`prompt_n` values are missing, `first_call_prompt_n_mean` returns **0.0**, not `None`
(`:132-133`: `sum(...) / max(1, 0)`), while `first_call_cache_misses` counts each missing timing as a
miss. A prompt with no successful call at all is also excluded from `first_call_cache_misses`
(`len(pn_first) - hits`), so hits+misses can be less than `n_prompts`. Partial cache reuse
(`prompt_n > 1` but less than `usage.prompt_tokens`) is counted as a **miss**, which is the conservative
choice for "fully cached", but the comment at `:114-116` ("a first call that evaluated its full prompt is
a miss") does not say that; a reader can mistake `first_call_cache_hits` for "any cache reuse".

### 2.4 The launch scripts

Both scripts are the same apart from host/node/out paths (verified with `diff`). Per script:

- `set -euo pipefail`; `R=/home/dowling/r1_tracks`; `OUT=$R/out/<node>`; `PATH=$R/bin:$PATH` (`:7-9`).
- `pgrep -u "$(id -u)" -f "bin/llama-server"` into `pids`; require exactly one (`:14-15`).
- echo `resident_server_count=1 server_pid=… server_start=… utc=…` (`:17`).
- `apps=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l)`; require 1 (`:18-20`).
- `f1` → `$OUT/s01_diag_f1/cache_prompt_true_cold.json`, `--mode true`; `f2` →
  `$OUT/s01_diag_f2/plain_single_absent.json`, `--mode absent` (`:22-25`).
- `mkdir -p "$(dirname "$out")"` (`:26`), then `trks-diag` with `--n 200 --repeats 3 --order-seed 1
  --proposal-schema manager_proposal/v1 --resident-server-count 1 --host-label … --llama-build 620d2225…
  --llama-server-bin … --server-args "$BASE"` (`:28-33`).

The out paths do **not** collide with the 30 Oct `$OUT/s01_diag/cache_prompt.json`; neither host has an
`s01_diag_f1`/`s01_diag_f2` directory or a file with the new names. `mkdir -p "$(dirname "$out")"` is
correct.

`mapfile` under `set -euo pipefail` is fine on the hosts (bash 5.1.16): I ran
`mapfile -t pids < <(pgrep -f "no_such_proc_xyz" || true)` and it survived with `count=0`. The scripts
would not run under the Mac's bash 3.2 (`mapfile` is unavailable), but they are host scripts.

**The `pgrep` assertion is broken on both hosts.** I checked this live, read-only:

- TASL-2 currently has **two** Track P dry-run processes whose command lines contain
  `.../bin/llama-server` (`/home/dowling/r1_trackp/venvs/trackp-cpu/bin/python /tmp/r1_c3_dryrun_retry_…/bin/llama-server …`
  on ports 39705 and 60275; PIDs 2945752 and 3747685). `pgrep -u dowling -f "bin/llama-server"` returns
  **2** with no Track S server running. These are Track P's and must not be stopped (runbook §0.4
  ownership; D6 says Track P keeps priority). With one Track S server, the count would be at least 3
  (plus the wrapper below).
- On TASL-7, the count is 0 now. But the compliant way to start the server is
  `tmux new -d -s trks_llm $R/bin/trks-servers 1`, and `trks-servers:8-14` is
  `exec flock -n … bash -c '… $R/opt/llama.cpp/build/bin/llama-server … & … wait'`. `pgrep -f` matches
  the **full command line**, so the lock-holder `bash -c` (and, depending on `flock`, the `flock` argv)
  matches the pattern as well as the server. I reproduced exactly this on TASL-7: I started a
  non-exec-optimized `bash -c 'for i in 1; do sleep 8; done; wait # /home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server'`
  and `pgrep -af "bin/llama-server"` returned that wrapper (PID 1587671, `count=1`), although it was not
  a server. The `trks-servers` script has the same `for`/`wait` shape, so it will match.
- Consequence: on TASL-7 the assertion sees 2 (wrapper + server) and exits 1; on TASL-2 it sees at least
  4 and exits 1. The scripts can never reach `trks-diag`. If the operator instead starts `llama-server`
  directly to avoid the wrapper, the flock rule is violated (the lock is not held), and TASL-2 still has
  the two Track P matches. There is **no compliant startup** that satisfies the assertion as written.
- The same over-match means `server_pid` at `:16-17` can be a Track P pid or the wrapper, so the recorded
  "server start" is not the server's. The `nvidia-smi` check does not fix this: it counts lines and does
  not link the count to the `pid` or to port 18101.

I also checked F1's "no HTTP call before the run" at code level: the diagnostic builds prompts/body/order
and calls `cpu_census` before `run_mode`; the first HTTP request is the first `post_full` chat completion;
`/props` is fetched only at report build (`:210`); `server_version` runs the local binary (`:57-64`);
`trks-servers` itself makes no HTTP call. So F1's first chat completion really is the first if the
operator has not sent one. The script does not verify that, and does not gate on the recorded first-call
hits (see M1).

### 2.5 Flock

The server is started by `bin/trks-servers`, which holds `flock -n ~/r1_locks/gpu0.lock` for the servers'
lifetime (runbook §0.4 and §11.3, lines 74-83 and 526-543). The diagnostic is an HTTP client; its GPU work
happens inside the server, which is under the lease. **The arrangement meets the author's rule in
substance when the server is started through `trks-servers`.** The launch script must **not** take the
lock itself: the lock is exclusive and already held by the server, so `flock ~/r1_locks/gpu0.lock
trks-diag …` would block forever (deadlock). What is missing is a cheap check that the lease is actually
held: `flock -n ~/r1_locks/gpu0.lock true` should **fail** (a holder exists), and/or the server pid should
have the lock file open in `/proc/<pid>/fd`. If that check succeeds (lock free), the server was started
outside `trks-servers` and the run is outside the lease — STOP. This is a control gap, not a reason to
wrap the diagnostic in `flock`.

### 2.6 Static checks

```
bash -n r1/tracks/ops/launch/tasl2_d6.sh     # OK (macOS bash 3.2 syntax check; hosts run 5.1.16)
bash -n r1/tracks/ops/launch/tasl7_d6.sh     # OK
python3 -m py_compile r1/tracks/ops/diag/cache_prompt_diag.py   # OK
```

`install.sh` runs `bash -n` on the runner and `python3 -m py_compile` on the diagnostic before `scp`; the
new files satisfy those. The installed diagnostic is still v1 on both hosts, so `install.sh` must be run
before the new launch script can work.

## 3. Findings

| id | severity | finding |
|---|---|---|
| **B1** | **BLOCKING** | The `pgrep -f "bin/llama-server"` assertion over-matches the `trks-servers` lock-holder `bash -c` wrapper on both hosts and the two Track P dry-run `llama-server` processes on TASL-2; the scripts exit with "expected exactly 1 … found 2/4" before any diagnostic call. The recorded `server_pid`/`server_start` can also be a wrapper or Track P pid. |
| **M1** | **MAJOR** | F1/F2 freshness is not enforced or gated: a server already used for a prior run (including F1's server reused for F2) produces a warm control, the script still prints DONE, and the server pid/start is only echoed to stdout (not in the artifact). This is exactly the S1 defect the follow-up is meant to remove. |
| **M2** | **MAJOR** | `install.sh` updates the diagnostic and runner but not the new launch scripts; both hosts still have the v1 diagnostic and no `*_d6.sh` in `$R/launch`, and the host checkout at `9bb64ba` has no `r1/tracks/ops/launch`. The reviewed launch script is not what would run without a manual copy, and the v1 diagnostic rejects `--resident-server-count`. |
| **M3** | **MAJOR** | The server/GPU assertions are not tied to the diagnostic's endpoint (18101), to each other, or to the lease: `pgrep` counts any matching command line, `nvidia-smi` counts lines, and nothing requires the counted pid to be the one serving 18101, the one holding `gpu0.lock`, or the one whose cmdline matches `BASE`. `server_args`/`gguf_sha256` in the JSON are claims, not measurements. |
| **m1** | **MINOR** | First-call metric edge cases: all-missing `prompt_n` gives `first_call_prompt_n_mean = 0.0` (not `None`); missing timings count as misses; prompts with no successful call are excluded from `first_call_cache_misses`; partial reuse is a "miss" but the comment does not say so. |
| **m2** | **MINOR** | The module docstring still says the only difference is one added `cache_prompt` field (`false`/`true`), does not describe `absent`, and its example omits the now-required `--resident-server-count`. `--mode both` now runs three modes (`false`, `true`, `absent`) while its name/old behaviour meant two. The output `purpose` is still the STOP-1 question; the F1/F2 phase is not recorded. |
| **m3** | **MINOR** | S4 is only partly closed: the output has `request_example`, `run_utc`, per-mode and per-call timestamps, but no script sha256, no payload/body hash, and no `followup`/`phase` (`f1`/`f2`) field. Error calls have no `utc`. |
| **m4** | **MINOR** | The output paths are fixed; a second run overwrites the prior raw file (`Path(args.out).write_text`), with no `[ -e "$out" ]` refusal or UTC-stamped path. The D6 rules say raw responses are kept. |
| **m5** | **MINOR** | The client runs in the foreground under the operator's ssh, not via `trks-run`/tmux as the runbook's probe convention does; an ssh drop kills the run and leaves the server and lease up. The script also does not check for full offload / server readiness before the first request; it only counts GPU apps. |
| **m6** | **MINOR** | `--resident-server-count` is an operator-supplied `int` copied into the JSON, not a measurement; the diagnostic cannot detect a wrong value. `apps=$(nvidia-smi … | wc -l)` counts lines, not unique pids, and a failing `nvidia-smi` under `pipefail` aborts with no diagnostic message; the count is not re-checked after the run. |
| **m7** | **MINOR** | The launch script does not re-check the priority markers (`trackx_evidence.active`, `trackp_evidence.active`, `$R/trks_drill.active`) at start, relying on the earlier `trks-servers` check and the watcher; it also does not re-check that the lease is held. This does not override priority, but a marker that appears between server start and the run is not seen by the script. |

No other pinned code is touched and the diagnostic itself is faithful to the pinned probe.

### B1 — the assertion cannot pass (BLOCKING)

`tasl2_d6.sh:14` / `tasl7_d6.sh:14`:

```bash
mapfile -t pids < <(pgrep -u "$(id -u)" -f "bin/llama-server" || true)
if [ "${#pids[@]}" -ne 1 ]; then echo "STOP: expected exactly 1 resident llama-server, found ${#pids[@]}" >&2; exit 1; fi
```

`pgrep -f` matches the whole command line, not the executable name. Two independent sources of extra
matches exist:

1. **Track P on TASL-2.** Live, with no Track S server:
   `pgrep -a -u dowling -f "bin/llama-server"` returns
   `2945752 /home/dowling/r1_trackp/venvs/trackp-cpu/bin/python /tmp/r1_c3_dryrun_retry_gfxlucss/bin/llama-server … --port 39705`
   and
   `3747685 … /tmp/r1_c3_dryrun_retry_za76rfeh/bin/llama-server … --port 60275`.
   The count is 2. These are Track P's idle dry-run processes (the 30 Oct review records them as expected
   and GPU-free); the D6 rules say Track P keeps priority and the runbook §0.4 says never kill a process
   you did not start. The operator must not stop them to make this assertion pass.
2. **The `trks-servers` wrapper on both hosts.** The compliant startup is
   `tmux new -d -s trks_llm $R/bin/trks-servers 1`; `trks-servers:8-14` runs
   `exec flock -n ~/r1_locks/gpu0.lock bash -c '… $R/opt/llama.cpp/build/bin/llama-server … & … wait'`.
   The `bash -c` (and possibly the `flock` argv) contains the literal `bin/llama-server` and stays alive
   for the server's lifetime, so `pgrep -f` counts it. I reproduced this on TASL-7 with a `bash -c` of the
   same `for`/`wait` shape: `pgrep -af "bin/llama-server"` returned the wrapper (PID 1587671). Starting
   the server directly instead would avoid the wrapper but would leave the lease unheld, violating the
   D6 flock rule, and on TASL-2 the two Track P matches remain.

So on TASL-7 the count is at least 2 and on TASL-2 at least 4; the script exits 1 before `trks-diag`.
The same over-match means `pid=${pids[0]}` can be the wrapper or a Track P process, so the echoed
`server_pid`/`server_start` is not reliable evidence of the server.

**Fix:** assert the server on the diagnostic's endpoint and tie it to the GPU pid, e.g. use
`ss -ltnp 'sport = :18101'` (or `/proc/*/exe` + the pinned absolute binary path) to get the listener pid,
require exactly one, require that pid to be the single `nvidia-smi --query-compute-apps=pid` entry, and
require its cmdline to match `BASE`. An anchored path pattern such as
`^/home/dowling/r1_tracks/opt/llama\.cpp/build/bin/llama-server( |$)` would exclude the wrapper and the
Track P Python processes, but it would not prove the port; the port/pid link is the safer assertion.
Do **not** use `pgrep -x llama-server`: on TASL-2 it also returns the two Python-wrapped Track P
processes (their comm is `llama-server`).

### M1 — freshness is not enforced (MAJOR)

The scripts' comments say "one freshly started server, no prior call" (`:3-6`), but nothing verifies it.
F1 is a control whose whole point is a **cold** server; F2 is the plain S0.1 probe, whose server was cold.
If the operator reuses the F1 server for F2 (the natural reading of "one server per host"), F2's first
calls are all warm; the F2 artifact will show `first_call_cache_hits = 200` and the script still prints
`D6 f2 DONE` and exits 0. If F1 is run on a server that already served a completion, the same happens to
F1. The diagnostic records the evidence (`first_call_cache_hits`, `first_call_cache_misses`,
`first_call_prompt_n_mean`, `usage_prompt_tokens_mean`, `started_utc`/`finished_utc`), but the launch
script never reads the JSON back. The `server_start` is only on stdout (`:17`), not in the artifact; the
JSON's `resident_server_count` is the hardcoded 1, not a measurement.

**Fix:** write the server pid/start and the check timestamp to the output directory (or add
`--server-pid`/`--server-start` and record them in the JSON), require a **fresh server per phase**
(restart `trks_llm` between F1 and F2; F1 cold, F2 cold to match S0.1), and after the run parse the JSON:
STOP if F1's `first_call_cache_hits != 0` (and, for F2, if the metric shows the same prompts were already
cached). The `first_call_prompt_n_mean` versus `usage_prompt_tokens_mean` is useful corroboration, but a
cold run can have partial prefix reuse between prompts, so use it as a warning, not the only gate.

### M2 — the reviewed launch script is not installed (MAJOR)

`install.sh:15-20` copies `diag/trks-diag` and `diag/cache_prompt_diag.py` only. Both hosts still have
the v1 diagnostic (`5012efc4…`, schema v1, no `--resident-server-count`) and `$R/launch` contains only the
30 Oct scripts; the host checkout is at `9bb64ba` and has no `r1/tracks/ops/launch`. The new launch
scripts are therefore not on the hosts and are not installed by `install.sh`. The prior 30 Oct procedure
copied the old launch scripts by hand (the `$R/launch/tasl*_diag_cache.sh` hashes match the committed old
files), so the manual path exists, but it is not documented for D6 and the v1 diagnostic will reject the
new required flag if the operator runs the launch script before `install.sh`.

**Fix:** before F1/F2, (a) run `install.sh` on both hosts (it updates `$R/bin/cache_prompt_diag.py` to
`1b8409c7…` and `$R/bin/trks-diag` stays `7ab8b5c9…`), (b) copy the matching `tasl{2,7}_d6.sh` to
`$R/launch/`, `chmod +x`, and `sha256sum` it against the committed file (`123e1107…` / `76e12bd0…`), and
(c) record those hashes in the report. Alternatively extend `install.sh` to install the per-host launch
script, so the reviewed file is the one that runs.

### M3 — the assertions are not tied to the 18101 server, the GPU pid, or the lease (MAJOR)

Even after the pgrep pattern is fixed, the script can pass with the wrong object: a server on another
port, a different `llama-server` process, or a foreign GPU process whose pid is not the server. The
`nvidia-smi` check counts lines (`wc -l`) and never compares the pid to `pid`; `pgrep` never checks the
port; `BASE`/`--server-args` is only recorded, not compared with `/proc/<pid>/cmdline` or the server's
`/props`. The flock rule is met in substance only because `trks-servers` holds the lease for the server's
lifetime; the script does not check that the counted server is the lease holder. It also must not wrap
the diagnostic in `flock` (the exclusive lock is already held by the server; a second `flock` would
block). Add: the 18101 listener pid is the single GPU compute pid; the pid holds `gpu0.lock` (or a
non-blocking `flock -n … true` fails, proving a holder); the pid's cmdline matches `BASE` and its
GGUF/build match the pins. If any check fails, STOP.

### m1 — first-call metric edge cases (MINOR)

From synthetic `summarise` calls: all first-call timings missing → `first_call_prompt_n_mean: 0.0`
(should be `None`); missing timing counts as a miss; a prompt with no successful call is absent from
`first_call_cache_misses`; a partial reuse (`prompt_n` 375/684) counts as a miss but the comment only
mentions "evaluated its full prompt". Define "fully cached hit" explicitly, record a count of prompts
with a first successful call, and make the all-missing case `None`. For F1, a cold server can still have
partial prefix reuse between prompts, so do not treat a lower `first_call_prompt_n_mean` alone as warmth.

### m2 — docstring, `both`, and the missing phase label (MINOR)

The docstring (`:11-16`) says the only difference from the pinned probe is one added field, `false` for
the test and `true` for the control; that is no longer true for `absent` (F2). The usage example
(`:22-25`) omits the required `--resident-server-count`; running it fails. `--mode both`
(`:154-155`, `:173`) now expands to `MODES = ("false", "true", "absent")`, three modes, whereas the name
and the 30 Oct behaviour meant two; if `both` is kept, say so or add `all` and keep `both = false+true`.
The output `purpose` (`:193`) is still the STOP-1 question; add a `followup`/`phase` field (`f1`/`f2`)
so the F1/F2 artifact is self-describing.

### m3 — S4 is only partly closed (MINOR)

The output now has `request_example`, `run_utc`, per-mode `started_utc`/`finished_utc` and per-call `utc`,
which is the main S4 fix. It still has no script sha256, no payload/body hash, and no `followup`/`phase`
label; error calls have no `utc`. Add `script_sha256` (hash of `cache_prompt_diag.py`), a payload hash
(or the full request for the first call), and the phase label; record `utc` for error entries too.

### m4 — fixed output paths overwrite raw evidence (MINOR)

The paths `$OUT/s01_diag_f1/cache_prompt_true_cold.json` and `$OUT/s01_diag_f2/plain_single_absent.json`
are fixed, and `Path(args.out).write_text` overwrites. A second run (or a mistaken rerun after a partial
run) destroys the first raw file. The 30 Oct diagnostic had the same property, but D6 explicitly keeps
raw responses; add `[ -e "$out" ] && { echo STOP; exit 1; }` or a UTC-stamped attempt directory.

### m5 — foreground client and readiness (MINOR)

The diagnostic is run directly (`trks-diag …`, `:28`), not through `trks-run`/tmux, although the runbook's
probe convention (§0.9/Phase 1) uses `trks-run` so an ssh drop does not kill the probe. The 30 Oct
diagnostic also ran directly, so this is a resilience gap, not a rule violation. The script also does not
wait for/confirm full offload or the listener; it counts GPU apps, which can be 0 while the model is
still loading, and it does not re-check after the run. Run it in a tmux session and check the server log
for `offloaded N/N` + `listening` before the first request.

### m6 — the resident count is an assertion, not a measurement (MINOR)

`--resident-server-count` is a required `int` and is copied to `resident_server_count` (`:200`); the
diagnostic never counts anything. If the launch script's assertion is wrong or bypassed, the JSON still
says 1. The `nvidia-smi` check is a line count and is not re-run after the diagnostic. Either measure the
count/pid in the diagnostic (or a sidecar) or state in the report that the value is operator-asserted.

### m7 — priority markers are not re-checked (MINOR)

`trks-servers` checks the Track X/P markers and the drill marker at server start (`trks-servers:5-7`,
runbook §0.4), and `trks-watch` handles a marker that appears later. The launch script itself does not
re-check them. A marker that appears between server start and the run would not be seen by the script
(the watcher would stop the server and the run would fail, so priority is not overridden). Add the same
three-file check at script start for a clear STOP message.

## 4. Checklist mapping to the author's D6 rules

| # | D6 rule | Result |
|---|---|---|
| 1 | Diagnostic, not a phase: `k` unset, Phase 3 not started | **PASS** — the code sets no k and starts no phase; the launch scripts only run the diagnostic. |
| 2 | No pinned code change | **PASS** — `determinism.py` is `081adb63…` at `9bb64ba` and at HEAD; `git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests` is empty; hosts are clean at paper `9bb64ba` / harness `115df37`. |
| 3 | Reuse the committed diagnostic code | **PASS** (code) / **PARTIAL** (install) — the launch scripts call `trks-diag` → `$R/bin/cache_prompt_diag.py`; the hosts still have v1 and `install.sh` must be run (M2). |
| 4 | F1: control-only `cache_prompt: true` on a freshly started server, no prior call, one server per host | **FAIL** — the server assertion cannot pass (B1: wrapper + Track P), and coldness is not verified/gated (M1). |
| 5 | F1 uses the pinned prompts/seeds/`chat_payload`/serial schedule (`order_seed 1`, `url_index 0`, `client 0`) | **PASS** — `D.fixed_prompts`, `D.chat_payload`, `D.schedule(200,3,1,0,0)`; the rebuilt order head matches the 30 Oct files. |
| 6 | F2: plain S0.1 serial probe, **no** `cache_prompt` field, one resident server, otherwise exactly as S0.1 | **PASS** (body/schedule) — the monkeypatched `run_mode` shows no `cache_prompt` for `absent`; `identity_rate`/`latency_stats`/`cpu_census` are pinned. **PARTIAL** on "otherwise as S0.1": a fresh server is not enforced (M1), and the one-server assertion is broken (B1). |
| 7 | A new launch script must be committed and reviewed before use | **COMMITTED** (`fc842b6d`) and reviewed here; **NOT ACCEPTED** (this review). It is not installed by `install.sh` (M2). |
| 8 | Keep raw responses and record per call `prompt_n` vs `usage.prompt_tokens`, first-call cache hits, resident server count, timestamps | **PASS with notes** — `contents` per prompt, `calls[].tokens` (both counts), `first_call_cache_hits`/`misses`/mean, `resident_server_count`, per-call/per-mode `utc`; the count is operator-asserted (m6), the first-call edge cases (m1) and error-call timestamps (m3) are notes. |
| 9 | Every GPU job runs under `flock ~/r1_locks/gpu0.lock` | **PASS in substance** if the server is started via `trks-servers` (the server is the only GPU compute and holds the lease for its lifetime; the diagnostic is an HTTP client). The script must **not** take the lock (deadlock) and should add a held-lock assertion (M3). |
| 10 | Track X (TASL-2) and Track P (TASL-7) keep priority | **PASS-with-note** — `trks-servers` checks the markers at start and `trks-watch` handles later ones; the launch script does not re-check (m7). The two Track P processes on TASL-2 are the direct cause of B1; they must not be stopped. |
| 11 | Out paths do not collide with the 30 Oct outputs; `mkdir -p` correct | **PASS** — `$OUT/s01_diag_f1/…` and `$OUT/s01_diag_f2/…` vs the 30 Oct `$OUT/s01_diag/cache_prompt.json`; neither host has the new paths; `mkdir -p "$(dirname "$out")"` is correct. |
| 12 | `bash -n` both scripts, `py_compile` the diagnostic, installed copies updated | **PASS** for `bash -n` and `py_compile`; **FAIL/PARTIAL** for install: `install.sh` updates the diagnostic/runner but not the launch scripts (M2). |

## 5. Limitations

- I did not run F1/F2, start a server, or send any request; the pgrep result is from live read-only
  process inspection plus a short `bash -c` `sleep` reproduction on TASL-7 (no GPU, no lock). The
  `trks-servers` wrapper was not started (that would take the lease); its command string is taken from the
  committed template (`trks-servers:8-14`) and the runbook §11.3, and the matching behaviour of a
  `for`/`wait` `bash -c` with the same path was reproduced directly.
- The author's D6 decision text is relayed through the task statement (there is no D6 decision artifact in
  this worktree); the checklist above maps to the rules as stated in the task. The runbook of record
  (revision 3.3) was read at `13badb0d`.
- I did not verify the host's tty/ssh history or run the 4.6 GB GGUF hash on the Mac; the host hashes are
  from the hosts. The 30 Oct `s01_diag` data are the v1 files; the v2 edge-case behaviour is from
  synthetic `summarise` calls against the committed code, not a live v2 run.

## 6. Verdict

The diagnostic code itself is a faithful extension of the pinned probe: `absent` is exactly the pinned
`chat_payload` body, the prompts/seeds/schedule are the pinned ones, `identity_rate`/`latency_stats`/
`cpu_census` are unchanged, and the new token/timestamp/first-call fields largely do what D6 asks (with
the edge-case notes in m1/m3). The **launch path is not usable as committed**: B1's `pgrep` assertion
counts the `trks-servers` wrapper on both hosts and the two Track P dry-run `llama-server` processes on
TASL-2, so it exits before any diagnostic call and can also record the wrong server pid; M1 leaves F1/F2
freshness ungated (a warm control would still print DONE); M2 leaves the hosts on the v1 diagnostic and
does not install the new launch scripts; and M3 does not tie the assertions to the 18101 server, the GPU
pid, or the lease. These require a corrected launch script (and an install/copy step) and a fresh review
before F1/F2 may run; the diagnostic code can be carried forward with the m1/m2/m3 fixes.

REVIEW VERDICT: NOT ACCEPTED

---

## Round 2 — re-review after `0c6f43e6` (31 Oct 2026)

**Reviewer:** independent (fresh; not the author or the operator). **Under review:** worktree
`.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`, head **`64a13270`** (the round-1 review)
on the remediation **`0c6f43e6`** atop `fc842b6d`; `git show 0c6f43e6` (4 files, +209/−54:
`cache_prompt_diag.py` +72, `install.sh` +9, each `tasl{2,7}_d6.sh` +91/−27). Pins: paper `9bb64ba`,
harness `115df37`, llama.cpp `620d2225`, GGUF `509287f7…4d3c`; runbook 3.3. **I did not run a GPU job, a
server, or the diagnostic.** Host access was read-only (`ssh portal_zhixu`, `ssh tasl7`): `git`,
`sha256sum`, `ss`, `nvidia-smi --query-compute-apps=pid`, `ps`, `grep`, `wc`, `df`, `tmux ls`, and the
round-1 `flock -n … true` lease probe; I started no process and wrote nothing. One synthetic Python test of
the diagnostic's `run_mode`/`summarise` with a fake `post_full` (no HTTP, no GPU) checked the `absent` body
and the first-call metrics.

### 2.1 Worktree, hashes, static checks, pins

```
git rev-parse HEAD                      # 64a13270
git status --porcelain                  # clean
git diff 9bb64ba..HEAD -- r1/tracks/probes r1/harness r1/tests   # empty
sha256sum r1/tracks/probes/determinism.py                         # 081adb63… (also at 9bb64ba)
bash -n r1/tracks/ops/launch/tasl{2,7}_d6.sh; bash -n r1/tracks/ops/install.sh   # OK
python3 -m py_compile r1/tracks/ops/diag/cache_prompt_diag.py                    # OK
sha256sum .../tasl2_d6.sh .../tasl7_d6.sh .../cache_prompt_diag.py .../install.sh
  # cce9bfdf…, c75956f5…, 1ef268eb…, 38ec70e8…
```

The diff is confined to the diagnostic, `install.sh` and the two launch scripts; `determinism.py` is
`081adb63…` at `9bb64ba` and at HEAD (and on both hosts). The two launch scripts differ only in
host/node/out paths (diff lines 2, 11-12, 64-65). `trks-diag` is unchanged (`7ab8b5c9…`); `trks-servers`
is `124316b5…`, byte-identical to the installed host copy.

Hosts (read-only): TASL-2/TASL-7 paper `9bb64ba` (`git status` 0 lines), harness `115df37`, llama.cpp
`620d2225`, GGUF `509287f7…4d3c`; no `trks_llm` tmux session; no listener on 18101;
`nvidia-smi --query-compute-apps=pid` empty; `flock -n ~/r1_locks/gpu0.lock true` succeeds (lease free);
no `.active` priority markers; installed `$R/bin/cache_prompt_diag.py` still **v1** `5012efc4…` and
`$R/launch` only the 30 Oct scripts; `install.sh` has not been run (so F1/F2 cannot run yet). The host
checkout at `9bb64ba` has no `r1/tracks/ops/launch`; `install.sh` reads `$here/launch/*.sh` from the
worktree and `scp`s them to `$R/launch`, so this is handled. Track P on TASL-2: listeners on 39705
(pid 2945752) and 60275 (pid 3747685), comm `llama-server`, `/proc/<pid>/exe` = `…/python3.12`, not on
18101; not touched.

### 2.2 B1 — the identification chain

```
ss -H -ltnp 'sport = :18101' | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2
readlink -f /proc/<pid>/exe            # must end in llama-server
nvidia-smi --query-compute-apps=pid    # exactly one line, equal to <pid>
tr '\0' ' ' </proc/<pid>/cmdline       # must contain --port 18101
```

On iproute2 5.15.0 on both hosts a same-user listener renders as
`LISTEN 0 5 127.0.0.1:39705 0.0.0.0:* users:(("llama-server",pid=2945752,fd=3))`; the extraction returned
2945752; `ss -H -ltnp 'sport = :18101'` is empty (rc 0) with no listener. The script no longer uses
`pgrep`; the port scopes the match to 18101, so the `trks-servers` `bash -c` wrapper (not a listener) and
Track P's 39705/60275 listeners cannot match. Even if a Python-wrapped listener were on 18101,
`readlink -f /proc/<pid>/exe` = `…/python3.12` would fail the `*/llama-server` case. The GPU pid equality
and the `--port 18101` cmdline check tie the listener to the single GPU process. B1's old failure cannot
reproduce. Residuals: N5 (no explicit "exactly one listener" count; `head -1`) and N6 (zero-listener
silent abort).

### 2.3 M3 — the lease

Line 43 asserts the lease is held: `flock -n "$HOME/r1_locks/gpu0.lock" true && { …exit 1; }` — held →
`flock -n` exits 1 → the `&&` list is skipped and the script continues; free → `flock -n` exits 0 → STOP.
I verified this shell semantics on both hosts' bash 5.1.16 (`false && { echo STOP; exit 1; }; echo SURVIVED`
→ `SURVIVED`; `true && { … }` → `STOP`, rc 1). It never takes the lock (no `flock` without `-n`). After
the stop (line 82) `flock -n … true || { STOP }` — free → continue, held → STOP; verified. The counted pid
must be the listener and the single GPU compute pid (lines 46-53). Residual: the holder is not tied to the
pid, but `trks-servers` cannot acquire the lock if a foreign holder exists, in which case the script never
reaches the listener checks and STOPs on the wait; acceptable.

### 2.4 M1 and B2 — the freshness gate is vacuous and always fails

The per-invocation part is right: the log is rotated (line 34), the script starts its own
`tmux new -d -s trks_llm "$R/bin/trks-servers 1"` (line 37), waits for
`listening on http://127.0.0.1:18101` and `offloaded 29/29 layers` (38-40), refuses an existing output (31),
and the diagnostic records a measured `server` block (pid/exe/cmdline/sha256/start, lines 217, 236, 252)
and refuses when `completions_before != 0` (218-220). Both greps match this build: the 30 Oct logs on both
hosts contain `srv llama_server: listening on http://127.0.0.1:18101` and
`load_tensors: offloaded 29/29 layers to GPU`.

**But the completion count is not logged by this build.** The pinned `tools/server/server-http.cpp:53`
defines `log_server_request`, and line 181 is
`// srv->set_logger(log_server_request); // TODO @ngxson : this is too spamy, no very useful; improve it in the future`
— the logger is not installed and there is no flag to enable it. The 30 Oct `llama_18101.log` covers the
1200-call `s01_diag` run (`cache_prompt.json` 1200 calls; log mtime 04:47:58 TASL-2 / 04:48:28 TASL-7;
build `620d2225`, `--verbose`) yet contains **0** occurrences of `chat/completions`, `POST`, `request:`
and `/v1/` on both hosts (TASL-2: 6,468,112 lines / 496,417,811 bytes; TASL-7: 6,677,873 lines /
510,512,002 bytes). Therefore:

- `before=$(grep -c '/chat/completions' "$LOG" || true)` is always 0 → the cold gate is a no-op;
- the diagnostic's `completions_before` is always 0 → its refusal never triggers;
- `after=$(…)` is always 0 → line 74's `[ "$after" -gt 0 ]` **always STOPs** after a successful 600-call
  diagnostic; the script exits 1 and never reaches `echo "D6 $phase DONE"`; only the JSON survives;
- the artifact's `server.completions_before/after` are always 0, i.e. the claimed "measured completion
  counts" are false.

This is **B2 (BLOCKING)**. The actual freshness is still guaranteed in substance (each invocation starts a
new `llama-server`, and the pre-start checks ensure none exists), but the implemented gate does not measure
anything and the wrapper's postcondition is always false. Fix: use a real signal — e.g. record a script
start UTC and require `server.start_lstart` (already recorded) to be after it, and/or gate on the
artifact's `first_call_cache_hits`/`first_call_prompt_n_mean` for F1 (read the JSON back), or a server-side
counter that this build exposes — and remove/replace the `after` check; do not record `completions_*` as a
measurement unless it is one.

### 2.5 M2 — install

`install.sh` now copies `$here/launch/*.sh` to `$tmp/launch`, `bash -n`s each, `scp`s them to
`$host:$R/launch/`, `chmod +x`es them and prints their sha256s (lines 20-22, 25-26). It reads the
worktree, not the host checkout at `9bb64ba`, so the missing `r1/tracks/ops/launch` on the hosts is
irrelevant; the reviewed `tasl{2,7}_d6.sh` (`cce9bfdf…`/`c75956f5…`) will be installed and their hashes
printed. The hosts still have v1 and no D6 scripts until the operator runs it — a required pre-run step,
not a defect. Residuals: N3 (both host-specific scripts land on both hosts) and N4 (the old
`tasl*_diag_cache.sh` call `trks-diag` without the new required flags).

### 2.6 Disposition of the round-1 findings

| id | round-1 finding | disposition | evidence (Round 2) |
|---|---|---|---|
| **B1** | `pgrep -f "bin/llama-server"` over-matches the wrapper and Track P; the script exits before `trks-diag` | **FIXED** | No `pgrep`; port-scoped `ss` listener → `/proc/<pid>/exe` `*/llama-server` → single `nvidia-smi` pid → cmdline `--port 18101` (lines 46-55). `ss` shape/extraction verified on iproute2 5.15; the wrapper is not a listener; Track P is on 39705/60275 and its exe is python3.12. Residuals N5/N6. |
| **M1** | Freshness not enforced or gated; a warm server still prints DONE | **STILL OPEN** | The fresh-server-per-invocation, log rotation, listening/offload wait, out-file refusal and measured `server` block are in place, and F1/F2 cannot share a server. But the cold gate and the diagnostic's refusal count `/chat/completions`, which this build never logs (B2): `before` is always 0, `completions_before/after` in the artifact are always 0, and the post-run `after > 0` check always STOPs. |
| **M2** | `install.sh` does not install the launch scripts; hosts have v1 | **FIXED** | `install.sh` now `scp`s `launch/*.sh`, `chmod +x` and prints sha256s; reads the worktree (host checkout's missing `ops/launch` irrelevant). Hosts still v1 until the operator runs it. Residuals N3/N4. |
| **M3** | Assertions not tied to 18101, the GPU pid or the lease | **FIXED** | Listener pid == single GPU compute pid, exe and `--port` cmdline checks; lease **asserted held** (`flock -n … true` must fail; semantics tested on bash 5.1), never taken; release verified after the stop. |
| **m1** | All-missing first-call `prompt_n` gives a phantom `0.0`; counts ambiguous | **FIXED** | `first_call_prompt_n_mean` is `None` when nothing was observed; `first_call_prompt_n_observed`/`_missing` are recorded; synthetic test: all-missing → `None`, observed 0/missing 2; mixed → hit 1, miss 1, observed 2/missing 1, mean 188.0. Residual: the comment still does not say partial reuse counts as a miss; prompts with no successful call are not in observed+missing (derivable as `n_prompts - observed - missing`). |
| **m2** | Docstring/example omit `absent`/`--resident-server-count`; `both` = 3 modes; no phase label | **STILL OPEN** | Example and `absent` description added; `phase_label` recorded (240). But the docstring (14-16) still says "the only difference … false … true", and line 23 says "`both` is the 30 Oct pair" while `MODES = ("false","true","absent")` and `--mode both` runs all three (215). Minor. |
| **m3** | No script sha, payload hash, phase label; error calls have no UTC | **FIXED** | `script_sha256` (242), per-mode `payload_sha256` (243-244), `phase_label` (240), error-call `utc` (106-107), per-call `utc` (111), per-mode started/finished (225-227). |
| **m4** | Fixed output paths overwrite raw evidence | **FIXED** | The launch script refuses an existing output before it starts the server (31). Residual: the diagnostic run directly still `write_text`s (266); the reviewed path is safe. |
| **m5** | Foreground client; no readiness/offload check | **FIXED** | Waits for `listening` and `offloaded 29/29 layers` (38-40, both strings verified in the hosts' logs); the EXIT trap runs on SIGHUP/SIGTERM in a lab test and stops the session; it is still foreground (not `trks-run`/tmux), a residual resilience note only. |
| **m6** | Resident count is an assertion, not a measurement | **FIXED** | The artifact now carries a measured `server` block (pid/exe/cmdline/sha256/start/log) and the launch script measures the listener + GPU count; `resident_server_count` itself is still the hardcoded 1 (note). |
| **m7** | Priority markers not re-checked | **FIXED** | Lines 24-26 check the Track X/P and drill markers at start; the loop semantics were tested on bash 5.1 (survives when all absent). |

### 2.7 New findings

| id | severity | finding |
|---|---|---|
| **B2** | **BLOCKING** | The freshness gate/post-run check counts `/chat/completions` in the server log, but the pinned build disables request logging (`server-http.cpp:181`, commented out); 0 occurrences in the 6.4M/6.7M-line 30 Oct logs that cover 1200 completions. The cold gate is a no-op, the diagnostic's `completions_before` refusal never fires, `server.completions_before/after` are always 0 (false "measured" evidence), and the launch script **always** STOPs after a successful diagnostic (`after=0`), exits 1 and never prints `D6 … DONE`. |
| **N1** | **MAJOR** | `trap 'cleanup' EXIT` is armed at line 21, before the `tmux has-session -t trks_llm` check at 27; `cleanup()` unconditionally `tmux kill-session -t trks_llm`. The "STOP: a trks_llm session already exists" path (and a marker path with such a session) therefore **kills the server it just refused to touch** — a server this invocation did not start, contrary to runbook §0.4. Fix: arm the trap only after `tmux new` succeeds (e.g. a `started=0/1` flag), or kill only the pid/session this script created. |
| **N3** | MINOR | `install.sh` copies **both** host-specific `tasl{2,7}_d6.sh` to **both** hosts; running the wrong one on a host uses the other node's prompts and writes `$R/out/<other-node>/…` with the wrong `--host-label` (no host guard in the script). Copy only the matching script, or add a `HOST_LABEL` guard. |
| **N4** | MINOR | The v2 diagnostic makes `--server-pid/--server-log/--phase-label` required; the still-installed/synced 30 Oct `tasl{2,7}_diag_cache.sh` call `trks-diag` without them and now fail with an argparse error (the 30 Oct STOP-1 control cannot be reproduced with the installed scripts). Document/update or make the new flags optional. |
| **N5** | MINOR | The listener identification takes `head -1` of the `pid=` matches and never requires exactly one; if `ss` shows several `users:(…)` on 18101 (SO_REUSEPORT), a non-GPU second listener could be silently ignored while the GPU pid equality passes. Count the matched pids and require exactly one. |
| **N6** | MINOR | Zero-listener behaviour after the "listening" check: `pid=$(ss … \| grep -o … \| head -1 \| cut …)` and `exe=$(readlink -f …)` are bare command substitutions under `set -euo pipefail`; if the listener vanished, `grep`/`readlink` return non-zero and the script aborts **silently**, so the explicit `STOP: no listener pid` (47) is unreachable. Verified on TASL-2: the zero-listener snippet exits 1 with no output. Add `\|\| true` and keep the explicit check. |
| **N7** | MINOR | The diagnostic's `server_facts` reads the whole server log into memory (≈250 MB for a 600-call F1/F2 run) to count a string that is never present (B2); the log rotation also keeps every old 250-500 MB log. Harmless on these hosts (265 GB free on TASL-2, 908 GB on TASL-7) but wasteful; fix together with B2. |
| **N8** | MINOR | After `cleanup; trap - EXIT` (77), the wait loop (78-80) and the `STOP: port still listening` (81) run with the trap disarmed and no explicit `kill "$pid"`; a server that survives `tmux kill-session` is detected but left running. Add a `kill "$pid"` fallback before the STOP (the pid is measured). |

No other pinned code is touched, no `k`/phase is set, and the hosts are idle at the pins.

### 2.8 D6 checklist

| # | rule | result |
|---|---|---|
| 1 | Diagnostic, not a phase; `k` unset; Phase 3 not started | **PASS** — no k/phase; only the follow-up outputs. |
| 2 | No pinned-code change | **PASS** — `determinism.py` `081adb63…` at `9bb64ba`/HEAD/hosts; `9bb64ba..HEAD` probes/harness/tests empty. |
| 3 | Reuse the committed diagnostic | **PASS** — `trks-diag` → `$R/bin/cache_prompt_diag.py`; `install.sh` updates it (hosts still v1). |
| 4 | F1 cold control, no prior call, one server | **FAIL** — B2 (vacuous gate, always-STOP wrapper); the fresh-server-per-invocation part is correct. |
| 5 | F1 pinned prompts/seeds/body/schedule | **PASS** — `D.fixed_prompts`, `D.chat_payload`, `D.schedule(200,3,1,0,0)`; `order_head` matches the 30 Oct file. |
| 6 | F2 plain S0.1, no `cache_prompt`, one resident server | **PASS on body/schedule** — synthetic `absent` posts `messages, model, seed, temperature` only; pinned `identity_rate`/`latency_stats`/`cpu_census`; **freshness gate broken (B2)**. |
| 7 | New launch script committed and reviewed before use | **COMMITTED** (`0c6f43e6`) and reviewed here; **NOT ACCEPTED**. |
| 8 | Keep raw responses; per call prompt_n vs usage; first-call hits; resident count; timestamps | **PASS with notes** — `calls[].tokens` has both counts, per-call/mode UTC, first-call hits/misses/observed/missing/mean; the completion counts are false (B2); `resident_server_count` is asserted (m6 note). |
| 9 | Every GPU job under `flock ~/r1_locks/gpu0.lock` | **PASS** — server via `trks-servers` holds it; the script asserts, never takes; release verified. |
| 10 | Track X/Track P keep priority | **PASS** — markers checked at start; the identification chain cannot match the Track P listeners; they were not touched. |
| 11 | Out paths do not collide; `mkdir -p` correct | **PASS** — no `s01_diag_f1/f2` on either host; the launch script refuses an existing file. |
| 12 | `bash -n`, `py_compile`, installed copies updated | **PASS static**; `install.sh` syncs the launch scripts; the hosts must be updated (operator step) before use. |

### 2.9 Verdict

The rewrite does fix B1 (the port-scoped listener → exe → GPU-pid → cmdline chain), M3 (the lease is
asserted held, never taken, and its release is verified), M2 (`install.sh` now syncs the launch scripts)
and most of the minors; the diagnostic's `absent` body, pinned prompts/schedule, imports, first-call
metrics and hashes are correct. But the M1 freshness gate added in this commit is not a measurement: the
pinned llama.cpp build disables request logging (`server-http.cpp:181`), so the `/chat/completions` count is
always 0 — the cold gate and the diagnostic's refusal are vacuous, `server.completions_before/after` are
false evidence, and the launch script's post-run check **always** STOPs after a successful diagnostic
(exit 1, no DONE). In addition, the EXIT trap is armed before the `trks_llm`-exists check and
unconditionally kills that session, so the refusal path kills a server the invocation did not start.
F1/F2 must not run until the gate is replaced with a real signal and the trap is armed only after the
script starts its own session; the remaining items are minor. The code can be carried forward once B2 (and
N1) are fixed.

REVIEW VERDICT: NOT ACCEPTED
