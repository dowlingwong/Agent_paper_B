Reviewed base: `668099b6` (paper: merge of published `main` `4aac5209` into the reviewed H200 G.1b/G.4 line `c894d0f6`) and `a69c8ef` (harness, the reviewed G.1b/G.4 pin line); accepted at paper `021dbc260d87c900e6afe18a8a712e72c04693d1` with harness `c025f89aeafc2199bf3487b4bcaa16678273c702`

# Independent review record — T1 on the TASL pair: G.1b and G.4 as direct host runs, G.5 draft rev 6 (ENGINEERING_ONLY)

**Unit.** Paper branch `mac-t1-tasl-20261121`: `sweep2/t1_tasl/` (`g1b_tasl.py`, `g4_tasl.py`, `t1_tasl_node.sh`, the two specs, the
dates params, `g5_projection_tasl.py`, the authorization templates, `T1_TASL_PLAN.md`), `r1/tests/test_t1_tasl_g1b.py`,
`r1/tests/test_t1_tasl_g4.py`, and the G.5 authorization draft re-targeted to the TASL pair (revision 6, `approved: false`).
Harness branch `mac-trackg-t1-tasl-20261121`: `--gpu-uuid` for direct host runs and CPU-only chunks (`68438477`,
`af480809`), then `stop_on_timeout` and the CPU-only-node check (`c025f89a`). Authority: R1-T1-HOST-TASL (branch
`author-decisions-20261121` `e5e452a0`), R1-TRACKG-G3-EARLY, R1-TRACKG-AR-U2-TASL2, R1-G1B-CAP, R1-HARNESS-ISOLATION; the
queue of 21 Nov 2026, item 1. Author decisions it leaves open: R1-G1B-EDITS (460 vs 552 runs), R1-G1B-TIMEOUT,
R1-T1-TASL-ENV (drafted separately), G5-TASL-GPUH and G5-SLOT.

**Process.** One independent reviewer (a separate agent that did not write the unit) for all five rounds, read-only,
scratch under `/tmp/rev_t1tasl/` moved to its `_to_delete/`. Rounds 3–5 confirm small fixes made after the round-2
acceptance. The round texts are reproduced below as delivered, as block quotes.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `eae2db87 + harness af480809` | CHANGES REQUESTED (1 blocking, 3 major, 10 minor) |
| 2 | `9c3a5eb5 + harness c025f89a` | ACCEPTED (4 minor) |
| 3 | `2f7c9ccc` | ACCEPTED (confirmation; 2 optional) |
| 4 | `77fa8634` | ACCEPTED (confirmation; 1 optional nit) |
| 5 | `021dbc26` | ACCEPTED (confirmation; closes the unit) |

**Open.** The author rows R1-G1B-EDITS, R1-G1B-TIMEOUT and R1-T1-TASL-ENV; the host check reports on `main` (P2/P3);
the host tests of `T1_TASL_PLAN.md` §6; the cross-host default check of the rows draft §3a, if chosen (not built); the
reviewer's optional follow-up (close-attempt could also match the attempt path built from the spec); the full harness
`tests/trackg/` suite was not run to completion by the reviewer (the noise_floor, gpu_identity and pilot subset passed).

## Round 1 (`eae2db87 + harness af480809`)

> Verdict: CHANGES REQUESTED
>
> Scope: paper repo eae2db87 vs 668099b6 (sweep2/t1_tasl/*, two test files, G.5 draft rev 6) and harness a69c8ef..af480809. Tests pass: paper 616 passed / 1 skipped; harness 79 passed. All changes were read-only. Scratch files are in /tmp/rev_t1tasl/_to_delete/ and both worktrees are clean.
>
> What I verified by running or reading code:
> - Pins: census 76f1d7ba, report sha256 146b1114…92d7 and harness af480809 all match the spec.
> - The six existing nodes match the reviewed H200 spec. The houseprice pins (88d359f2…, 73ee5597…, manifest f26332ff…, 4 edits) match the census and the harness.
> - All seven B1 baseline times match the U4 census table. The "slowest" values match the slowest executed census record among B1/B2/E1–E4.
> - `validate` gives 28.262 GPU-h (41.644 at ratio 1.5), within the cap of 100.
> - The pre-pilot dates come out at 166.9 GPU-h, labels done 4 Dec, B.7 7 Dec (1 day of slack); 9 Dec at ran share 0.8 or at 120 s per call. With every parent re-run (no reuse) it is 188.3 GPU-h. All of these match the plan and the draft.
> - `g1b_tasl_node.sh` works when run with a stub systemd-run (log, NODE_EXIT, exit codes).
>
> ## Blocking
>
> **B1 — the G.4 build check can never pass** (`g4_tasl.py:307` together with `:345–351`). `serve` requires the `--version` line to equal `version: <expected_build>`. `server_identity` then requires `/props` `build_info == expected_build`. In llama.cpp these two strings never match:
> - `common/build-info.cpp.in` builds `/props` `build_info` as `"b" + BUILD_NUMBER + "-" + COMMIT`, e.g. `b11669-620d2225c`.
> - `--version` prints `version: 0.7.0-dev (build 11669, commit 620d2225c)`, which is the form of the H200 `expected_build`.
>
> So either `serve` or every worker job STOPs. The tests hide this because the fake server echoes the same `BUILD` string (`test_t1_tasl_g4.py:137`).
>
> Fix: compare `/props` `build_info` against `f"b{build_number}-{commit}"`, parsed from the `--version` line (`llama_server_instance.parse_version`), or add a separate `expected_props_build` field. Make the fake server return the real `b<N>-<commit>` form.
>
> ## Major
>
> **M1 — the timing STOP comes late** (`g1b_tasl.py:445–450, 528–529`). `timing_check` runs only after a whole part has finished, and a timed-out run is still written as a `divergent:timeout` row (`noise_floor.run_chunk`). One part is up to 150 runs. If the 4090 is slow, every later run can also hit 3×basis before the part ends (imdb: 150 × 195 s ≈ 8 h), limited only by the deadline. The plan (§3) says "any run that reaches the declared timeout is a STOP". Fix: since the harness is being changed in this unit anyway, add a chunk flag (e.g. `stop_on_timeout: true`) that makes `run_chunk` raise `NoiseFloorStop` right after writing the timeout row, and map that stop to `stop_class: timing`. Add a test that the engine stops after the first timeout.
>
> **M2 — one failed node forces a re-run of the whole table** (`g1b_tasl.py:469–470`; `g1b_tasl_node.sh:16–17`; `assemble` at 606–615).
> - `job_dir` is created before the lease and the host checks. A busy lease or a transient foreign process uses up `<run_id>/<node>`.
> - The wrapper's log also uses up the node: any refusal before the run (missing `G1B_TASL_ENABLE_REAL`, note not on main) leaves `<node>.node.log` behind. I reproduced this: the second launch gives "exists (no overwrite)", rc 3.
> - `assemble` needs one `run_id` and one spec sha256 for all seven nodes. A new `run_id` means a new spec, so a new signed note, and all seven nodes run again (~28 GPU-h).
> - R1-TRACKG-AR-U2-TASL2 records foreign processes invading Ada within minutes, so this will happen.
>
> Fix: take the lease and run all host/GPU/foreign/scope/harness/env checks before `mkdir`. Write refusals before the run to `<run_id>/_refusals/<node>-<utc>.json`. Let a node have attempt directories (`<node>/attempt-N`); `assemble` takes exactly one complete attempt and lists the others. The wrapper should write to a log per attempt.
>
> **M3 — the host-check precondition is not verified** (`g1b_tasl.py:235–238`, `g4_tasl.py:159–160`). R1-T1-HOST-TASL says "STOP if the host checks fail". The code only checks that `isolation_host_check.record` is a non-empty string (a `TODO:` string passes) and that the sha256 is 64-hex at launch. Nothing reads the report, checks its sha256 or its verdict, and the note's P2/P3 are free text. Fix: at launch, read the record at the launch commit (on main), check its sha256 and a READY/PASS verdict line, refuse a placeholder record, and require P2/P3 to cite the record path.
>
> ## Minor
>
> - **m1 — wrong per-host figure in the plan** (`T1_TASL_PLAN.md` §3): it says "TASL-2 15.0 h"; the code gives 14.06 h (TASL-7 14.2 h is right).
> - **m2 — G5-TASL-GPUH B is not well posed** (draft §2.9). It says "167 + the campaign hours; cap B would need raising". The campaign hours are 39.4, so the total is ≈206 GPU-h at share 0.6, still within 230. But §2.10 says the server holds TASL-7 "for the table's span", which would make option B ≈2×167. Say which span is meant and give the numbers for 0.6 and 0.8. (The 30–40 % saving in G5-SLOT B checks out: audits are 70 % of the GPU-h, so splitting them over two cards saves about 35 %.)
> - **m3 — G.4 has no wrapper**. No script starts the scope and `taskset` for `run-node`; the operator has to build it by hand (plan §5), so no `<node>.node.log` is ever produced for `seal` to bind. Nothing checks CPU affinity in either job (`host_identity` records it but never compares it with `node_cpus`). Fix: add `g4_tasl_node.sh`, and refuse a run when affinity ≠ the declared cpus. Also check that the houseprice cpus do not overlap its host's cpus.
> - **m4 — some unexpected errors crash without a record**. `g1b_tasl.run_node_job` catches only OSError, ValueError, KeyError and SubprocessError; a TypeError or AttributeError escapes with no record and no sums. `job_dir.mkdir` (line 470) raises FileExistsError as a traceback; the test even expects that. Catch `Exception` as `g4_tasl` does, and turn the existing-directory case into a Stop.
> - **m5 — misleading STOP message** (`g4_tasl.py:163`): "one GPU for noise floor and labels" is false for mlab_cifar10, mlgym_cifar10 and Breakout, whose noise floors are measured on TASL-7. Say "one GPU model". The disclosure in draft §3 is fine.
> - **m6 — the "slowest" basis needs its qualifier**. The docstring and plan say "slowest executed census record". Breakout's slowest executed record is smoke s003 at 62.848 s; the spec has 61.781 (B2), which is right under the H200 plan's definition "baseline or declared edit". Add that qualifier.
> - **m7 — R1-T1-TASL-ENV has no text**. Draft line 40 calls it "drafted", but no draft of the row exists in this unit. Either draft it or say "to be drafted". The 460-run and timeout-basis deviations are clearly flagged.
> - **m8 — the wrapper is weakly guarded and weakly tested**. The wrapper flattens every failure to exit 1. It checks that the log doesn't exist, then writes it with `>` (should use noclobber). Its test only greps the script text. Add a test that runs it with a stub `systemd-run`.
> - **m9 — the harness accepts a CPU chunk for any node**. `device: cpu` is not checked against the node; the paper side enforces CPU-only nodes. This does not weaken isolation (no GPU at all). `--gpu-uuid` is resolved correctly (full UUID listed exactly once, no scheduler variables, `CUDA_VISIBLE_DEVICES` empty), and the HTCondor path is unchanged.
> - **m10 — leftover slot-hours in the dates output**: `g4_tasl dates` still prints `requested_slot_hours` per node and per K, which contradicts its own note that direct host runs request no slot-hours.
>
> ## What is right
>
> - G.1b uses both hosts' GPUs, split by node, ≈14 h each.
> - One RTX 4090 model, checked by full UUID; the GPU lease; foreign-process checks before and after each part; the delegated scope matches the census `invocation_inner.sh`.
> - Sealing with receipts, the GPU-h projection and cap, and the CPU node reported in core-hours.
> - G.4 records the server URL, build, settings and per-call latency, enforces `cache_prompt: false`, runs 3 nodes, and recomputes the dates with one slot.
> - G.5 rev 6 is consistent, keeps H200 only as context, poses the two new decisions with options and a recommendation, and has `approved: false`.

## Round 2 (`9c3a5eb5 + harness c025f89a`)

> Verdict: ACCEPTED (round 2). No Blocking or Major findings remain; four minor ones are left.
>
> Scope: paper eae2db87..9c3a5eb5 and harness af480809..c025f89a, reviewed read-only. Scratch is in /tmp/rev_t1tasl/_to_delete/ and both worktrees are clean.
>
> **Tests**
> - Paper: 625 passed, 1 skipped.
> - Harness: the noise_floor / gpu_identity / pilot subset passed (80 passed). The full `tests/trackg/` suite did not finish in 9 minutes on this machine, so I have no result for the rest of the harness suite. Running the whole suite on a host would close that.
> - Both specs validate; both pin c025f89a.
>
> ## Round-1 findings, verified
>
> **B1 (build check): fixed.**
> - `props_build` turns `0.7.0-dev (build 1, commit 620d222)` into `b1-620d222`. That is the form llama.cpp writes to `/props` (`common/build-info.cpp.in`: `"b" + build number + "-" + commit`).
> - The older `N (commit)` form, and a trailing space, are refused when the spec is validated.
> - The fake server now returns the real form.
> - The exam values in the spec match `r1/scripts/configs/exam_portal.json`: binary sha b70f4882…, the build line, GPU-ab72fb4a…, and the same `~/r1_locks/gpu0.lock` lease.
>
> **M1 (late timing STOP): fixed.**
> - The harness flag `stop_on_timeout` is a checked bool, defaults to false, and leaves the HTCondor path unchanged. It writes the timeout row, sets `stop_kind: "timeout"`, and stops the chunk at once.
> - `g1b_tasl` sets the flag and maps `stop_kind` to TimingStop before it looks at the exit code. If the engine crashes after the timeout row, `timing_check` on the rows still catches it.
> - The tests show 2 rows written in the harness test and 4 in the paper test.
>
> **M2 (one failure re-runs the whole table): fixed.**
> - The lease and every preflight check run before anything is written for the node. Refusals go to `_refusals/` (opened with `"x"`, never overwritten), including crashes inside a check.
> - Each run is `<node>/attempt-N`. Only an attempt that ended in an infrastructure STOP can be followed by another.
> - Two CPU-node jobs started at once fail closed: the second sees an attempt with no record and is refused.
> - Seal and assemble work per attempt. Assemble refuses a sealed sibling attempt that is complete, an author STOP, or has no record, and lists the unused infrastructure attempts.
> - I ran the wrapper twice with a stub `systemd-run`: two fresh logs under `_logs/`, exit 4 each time, and the node was not used up. An unknown flag gives exit 2.
>
> **M3 (host-check records): fixed.**
> - `check_host_record` reads the record from `origin/main`, checks its sha256, refuses placeholders and paths outside `docs/r1/reports/`, and requires the four `host_check_*` lines to name this host and the pin.
> - G.1b launch checks both hosts and P2/P3 must cite the record paths. G.4 launch checks TASL-2 and P1 must cite its record.
>
> **m1–m10: all addressed.** I re-ran the numbers:
> - TASL-2 is 14.1 h.
> - G5-TASL-GPUH B: 167+39 ≈ 206 GPU-h at share 0.6, 206+43 ≈ 249 at 0.8; whole span ×2 ≈ 334 and 412. All match `recompute_dates`.
> - No slot-hours keys remain in the dates output.
> - The houseprice cpuset is checked for overlap, and affinity is checked in both jobs.
> - The harness refuses `device: cpu` for any node outside `CPU_ONLY_NODES`.
>
> ## Minor
>
> **m1 — `bin_manifest` and `ldd` don't prove which shared libraries are loaded** (`g4_tasl.py`, `serve`). The manifest covers only the binary's own directory. `ldd` is checked only for "not found". `serve` passes its environment on to `llama-server`, and `LD_LIBRARY_PATH` takes priority over RUNPATH. So a stray `LD_LIBRARY_PATH` on TASL-7 could load a `libggml*`/`libllama*`/`libmtmd*` from outside the manifested directory, and both checks would still pass. Fix: either require every `ldd`-resolved `libllama*`, `libggml*` and `libmtmd*` to resolve inside `bin_dir`, or start the server with `LD_LIBRARY_PATH` unset. Record the environment in `server_record.json`.
>
> **m2 — an attempt with no record blocks the node permanently** (`g1b_tasl.next_attempt`). If a run is killed mid-way (host reboot, scope killed) during a ~14 h node, the attempt has no `job_record.json`. Every later launch is refused with "inspect it". Deleting is off-limits, so the only way out is a new `run_id`, which means a new spec, a new note and all seven nodes again (round-1 M2 again, for crashes). Fix: add a `close-attempt <attempt> --reason` command that writes a record with `stop_class: infrastructure` and the reason, after checking that nothing is running (lease free, no process in the scope).
>
> **m3 — the foreign-process check has a gap at the start** (g1b and g4 `run_node_job`). The check runs during preflight, then `uv pip freeze`, the setup command (data preparation can take minutes) and the default part (G.1b) or pilot (G.4) all run before the next check. The before-check of the first part was removed. A process that appears in that window is caught only after the default part or pilot, which costs a retry. Fix: re-run `check_no_foreign` just before the first engine call.
>
> **m4 — a few paths still crash without a refusal record.** `lease_cm.__enter__()` turns only a Stop into a refusal. An OSError while making `~/r1_locks` or opening the lease file gives a traceback with no record. If `write_refusal` itself fails, it hides the original STOP. Fix: catch Exception around entering the lease the same way as preflight does, and wrap `write_refusal` so the original message still reaches stderr.
>
> ## What's right
>
> - Preflight runs under the lease, and nothing is written for the node until it passes.
> - The retry rule is mechanical, and unused attempts are listed in the assembly.
> - Logs are per call and bound by the seal.
> - G.4 seals `server_record.json` in `SHA256SUMS`, and the dates command refuses two attempts for the same node.
> - The plan, the template and G.5 draft rev 6 agree with the code; the draft is still `approved: false`.
> - There are no unisolated, shared-card or wrong-host paths.

## Round 3 (`2f7c9ccc`)

> Verdict: ACCEPTED (confirmation round, paper 2f7c9ccc, harness unchanged at c025f89a). All four round-2 minors are fixed. Two small new gaps came up, both optional.
>
> **Checks**
> - Paper tests: 628 passed, 1 skipped.
> - Both specs validate.
> - I fed sample `ldd` output to `ldd_outside`: it flags a `libggml-cuda.so` resolved to `/usr/lib` and ignores `libcudart`. That is right.
> - Review was read-only; scratch is in /tmp/rev_t1tasl/_to_delete/ and the worktree is clean.
>
> **The four fixes**
> - **m1 (libraries outside the build directory):** fixed. `serve` drops `LD_LIBRARY_PATH` and `LD_PRELOAD` from the environment it hands to `ldd` and `llama-server` (`env=server_env`). Every `libllama*`, `libggml*` and `libmtmd*` must resolve into the binary's own directory, else STOP. The environment is recorded in `server_record.json`.
> - **m2 (crashed attempt blocks the node):** fixed. `next_attempt` writes `attempt.json`. `close_attempt` requires all of:
>   - no job record yet, a reason of at least 10 characters, and the same host;
>   - the owning process gone;
>   - the GPU lease free.
>
>   It then writes a record with `stop_class: infrastructure`, opened with `"x"`, and the next attempt may start. The CLI checks that the attempt directory belongs to this run and node. The test covers each refusal and the follow-on attempt-2.
> - **m3 (foreign-process gap):** fixed. G.1b now checks before every part including the first (9 checks per node); G.4 checks before the pilot.
> - **m4 (crashes without a record):** fixed. An exception while taking the lease becomes a refusal with a record in both jobs. If the refusal record itself cannot be written, the original STOP still goes to stderr and the STOP stands.
>
> **Optional minors (not blocking)**
> - **n1 — G.4 has no `close-attempt` command.** G.4 attempts also use `next_attempt`, so a crashed G.4 attempt is blocked the same way. But `g1b_tasl.py close-attempt` only accepts paths under the G.1b spec's run, and `g4_tasl.py` has no such command. Fix: add the same subcommand to `g4_tasl.py`, with the worker lease, or let `g1b_tasl.py close-attempt` take a G.4 spec.
> - **n2 — `close_attempt` only checks the orchestrator process.** Children that survive it (an engine left running in the scope) are not checked. For a GPU node the next attempt's foreign-process check catches them, but only while they are on the card. For the CPU node nothing catches them. A smaller, unlikely gap: a crash between `mkdir` and writing `attempt.json` leaves an attempt that `close_attempt` meets with a FileNotFoundError traceback. Fix:
>   - refuse to close while any process's command line contains the attempt path (the engine's argv has `--chunk <attempt>/out/…`);
>   - turn a missing `attempt.json` into a Stop that allows a close, or write `attempt.json` atomically together with the directory.
>
>   One more nit: the `--version` call in `serve` still runs with the inherited environment rather than `server_env`.

## Round 4 (`77fa8634`)

> Verdict: ACCEPTED (second confirmation round, paper 77fa8634, harness unchanged at c025f89a). n1 and n2 are both fixed. One very small nit remains, optional.
>
> **Checks**
> - Paper tests: 629 passed, 1 skipped.
> - `processes_mentioning` run against the real `/proc` on this machine found the live processes whose command line named the path, so the scan works outside the fake `/proc` used in the test.
> - Review was read-only; scratch is in /tmp/rev_t1tasl/_to_delete/ and the worktree is clean.
>
> **n1 (no `close-attempt` for G.4):** fixed. `g4_tasl.py close-attempt` takes the attempt only if its parent is the G.4 worker's `<runs_root>/<run_id>/<node>`. It uses the worker's lease and calls the same `G.close_attempt`.
>
> **n2 (`close_attempt` gaps):** fixed.
> - Before anything else, `close_attempt` scans `/proc/*/cmdline` and refuses while any process names the attempt path. The scan can be replaced in tests.
> - A missing `attempt.json` is now allowed: the owner pid is recorded as None, so the pid check is skipped. The process scan and, for GPU nodes, the lease still apply.
> - `serve` builds `server_env` right after taking the lease, so `--version`, `ldd` and `llama-server` all run without `LD_LIBRARY_PATH`/`LD_PRELOAD`. The test stub asserts this.
>
> **Optional nit:** `processes_mentioning` searches only for the resolved attempt path. The engine's command line uses the unresolved `<runs_root>/…` path. If `runs_root` ever sits under a symlink, a still-running engine would not match the search and the close would go ahead. For a GPU node the lease still guards this; for the CPU node nothing would. Fix: search for both the raw path and the resolved path. (A path like `attempt-1` also matches `attempt-10`, but that only causes a refusal, so it is harmless.)

## Round 5 (`021dbc26`)

> Verdict: ACCEPTED (paper 021dbc26, harness unchanged at c025f89a). This closes the T1 TASL unit.
>
> - **Fix confirmed:** `processes_mentioning` now looks for the attempt path in three forms: as given, absolute, and with symlinks resolved. A still-running engine is found whichever form its command line uses. The new test covers an unresolved path under a symlink.
> - **Tests:** 629 passed, 1 skipped.
> - **Possible follow-up, not needed for acceptance:** if the operator spells the attempt path differently from the spec (for example a relative path typed from another directory), none of the three forms may match the engine's command line, so a still-running engine could be missed. The CLI could add the path built from the spec, `<runs_root>/<run_id>/<node>/attempt-N`, as one more form to look for. On a GPU node the free-lease check still guards against this.
> - **Review hygiene:** I worked read-only. Scratch is under /tmp/rev_t1tasl/_to_delete/ and the worktree is clean.

---

Code-Commit: 021dbc260d87c900e6afe18a8a712e72c04693d1
Verdict: ACCEPTED

Accepted commit: `021dbc260d87c900e6afe18a8a712e72c04693d1` (paper, round 5) with harness `c025f89aeafc2199bf3487b4bcaa16678273c702`.
