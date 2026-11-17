# Track G G.0 U0 on Ada — independent review (deploy harness + verify Paper A status, 17 Nov 2026)

Reviewer: fresh independent agent (did not write the unit, the config, the wrapper or the capture).
Date 2026-11-17, 00:15–00:30Z. The only live access was read-only `ssh experiment_zhixu` (user `dowling`):
`git rev-parse/status/show/log`, `sha256sum`, `stat`, `ls`, `df`, `tail/head`, `tmux ls`, `pgrep`, `ps`,
`nvidia-smi --query-compute-apps` and one read-only re-run of `paper_a_status.py` (its documented behaviour is
read files / `git symbolic-ref` / `tmux has-session` / `nvidia-smi` query / `ps -o args=`; it never signals or
starts anything). No host write, no GPU job or lease, no commit/push, no deletion, no other user's process
touched. A local shell-only test of `bash` pipeline status was run on this Mac (no files).

## 0. Subject bytes, authority, method

| subject | bytes / sha256 | review-time state |
|---|---|---|
| `docs/r1/proposals/TRACKG_U0_DEPLOY_20261117.md` | 4,382 B / 62 lines / `c5d343633b4946fba189b04e06b24900dc65a33e42c00d1c0c0dc9db55f52805` | matches the brief; tracked at `45fcf0fa` (it was untracked when this review began) |
| `r1/scripts/configs/paper_a_status_ada.json` | 2,621 B / 34 lines / `20ea56877b019165b498f81956067a44027776682efe845addcb3e752f9ac887` | matches the brief and the committed blob (`git show 45fcf0fa:r1/scripts/configs/paper_a_status_ada.json` = `20ea5687…`); it was an uncommitted ` M` during the live checks (timeline note below) |
| `docs/r1/reports/trackg_g0_20261117/u0_status_20261117.json` | 829 B / 1 line / `db9618a54fd640e023b55df2856eb5d2b33be122405ff5c61633619a1aa00554` | byte-identical to Ada `…/u0_verify/status.json` |
| `docs/r1/reports/trackg_g0_20261117/nvidia-smi-live` | 383 B / 6 lines / `3be54e990bc8741dc69b805e6fd3a7f75143797966bccb7d28510f0f084f6a7e` | equal to the installed Ada copy (below); mode 755; tracked at `45fcf0fa` |

**Timeline note.** The live Ada checks and the file hashes above were taken at 2026-11-17 00:17:45–00:27:13Z,
when the unit and captures were untracked and the config was an uncommitted ` M` in both the review worktree
and the Ada paper worktree (the committed `HEAD:` blob then was still the 27-line template `30f5896…`: the
delivery brief's "committed config" was not yet true). While this review was being written, commit `45fcf0fa`
("overnight units — … Track G U0 deploy/Paper A config, captures", branch `ops-tasl-20261116`, tip now
`44b52368`) added the unit, config, wrapper and capture to git; at the tip the committed config blob is
`20ea5687…`. All four subject files were re-hashed at the tip and are byte-identical to the reviewed bytes
(unit `c5d3436…`, config `20ea5687…`, wrapper `3be54e99…`, capture `db9618a5…`), and the Ada deployment was
unchanged at 00:27:13Z. So the unit §3.1 "sha256 equals the committed one" is now satisfiable; the result
record must still pin `45fcf0fa` (or the acceptance commit) and compare the Ada file content to the committed
blob, not require the detached worktree itself to be clean.

Authority: `R1-TRACKG-G0-GO` and `R1-TRACKG-PORT-OWNER` exist at `author-d8-confirm-20261117` @
`26177d82` (remote ref `remotes/origin/author-d8-confirm-20261117`; commit adds 8 lines to `docs/r1/PLAN.md`).
`26177d82`'s G0 row authorises exactly U0's scope: deploy `r1-local-trackg-v2-20261114` @ `717ad835`, configure
and verify `paper_a_status_ada.json`, STOP if it cannot be made `clear_*`, U1/U2/U4 follow, ENGINEERING_ONLY,
independent review per unit, Paper A first, no disturbance; "G.0 不出任何噪声底或 D21 结论" and noise floor /
D21 / D28 are G.1b on L40S (`R1-TRACKG-G1B-HOST`, PLAN.md:1209; `R1-ADA-CENSUS`, PLAN.md:773). The unit's
authority citations and its G.0-only restriction are correct.

## 1. Scope — PASS

- U0 as written is a no-GPU prep unit (deploy + configure/verify the Paper A gate). It starts no GPU job or
  lease, measures nothing, and touches no other user's files or processes; its own writes are the deployment
  under our home (`/home/dowling/r1_trackg_20261117/{autoresearch_harness,Agent_paper_B_main_16185b0b,bin,u0_verify}`,
  verified). It is correctly a prerequisite for later Ada units, and §4 correctly makes a failure an item STOP
  ("not the night") with dependents skipped.
- The status check necessarily reads other users' GPU/process *metadata* with `nvidia-smi`/`ps` (read-only); that
  is inherent to the check and is not "touching" their processes. Accept.

## 2. Ada facts — all factual claims pass; deployed config equals the committed blob

Read-only checks at 2026-11-17 00:17:45Z–00:25:00Z (host `ucrtasl`):

| # | check | observed | result |
|---|---|---|---|
| 1 | harness HEAD / branch / clean | `717ad835df32bbe1047d032fb5bb8dde5384a258`; `r1-local-trackg-v2-20261114`; `git status --porcelain` empty | PASS |
| 2 | paper worktree | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b`, HEAD `16185b0b4035a58814bce360780182f0e3c34442`, detached (`HEAD`); status = ` M r1/scripts/configs/paper_a_status_ada.json` only | PASS (but see MINOR-2: it is not clean, and the unit does not say so) |
| 3 | config on Ada | file sha256 `20ea5687…` = reviewed bytes = committed blob in `45fcf0fa`; the Ada paper worktree shows ` M` because the config is a working-tree overlay on the detached `16185b0b` checkout | PASS (content equals the committed blob; record the commit, MINOR-2) |
| 4 | wrapper installed | `/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live`, `-rwxr-xr-x`, 383 B, sha256 `3be54e99…` = recorded sha | PASS |
| 5 | disk | `/dev/md0p3` 1,876,215,308,288 B, 1,618,337,181,696 B used, **162,496,090,112 B free (152 GiB, 91 %)** | PASS (≥50 GB) |
| 6 | no GPU job started | no `dowling` GPU compute PID (apps belong to `asif` 10, `zihaozhao` 16, 4 namespace-unreadable); no tmux server; no `paper_a`/`panel_v4`/`trackg` process of `dowling` except the reviewer's ssh | PASS |
| 7 | Paper A checkout | branch `paper-a-v4-ada`, HEAD `6b0ac021753eeb46c652db2b889c03451f217183` (2026-10-21 06:43:37 -0700, "Record completed panel v4 live run and strict receiving outputs") | PASS |
| 8 | status script deployed | `r1/scripts/paper_a_status.py` sha256 `6a36d24f16724e8a381a31f20d4a00a6c59827a36b375aa1e4efb26278478085` = `HEAD:` blob; supports the `nvidia_smi_binary` key | PASS (pin it: MINOR-4) |

## 3. Paper A evidence — the current verdict is correct and reproducible

- Checkout is on `paper-a-v4-ada` (symbolic branch, not detached — the script's branch check passes).
- Run dir exists: `/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z`.
- `panel/finalize.json` present (1,314 B, mtime 2026-10-21 06:11:34 -0700); `console.log` mtime 06:11:35 -0700 and
  its last line is `=== 2026-10-21T13:11:35+00:00 supervisor (live): segment 30 ended (exit 0): not resuming: the run completed`
  (the "COMPLETED" event is the preceding line; exactly one match for the completion line).
- No live Paper A tmux (no tmux server on `/tmp/tmux-1030/default`), no Paper A process, no Paper A GPU process.
- Read-only re-run, `cd …/Agent_paper_B_main_16185b0b && python3 r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`
  at 2026-11-17T00:20:24Z:

```json
{"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)", "utc": "2026-11-17T00:20:24Z", "host": "ucrtasl", "config": "/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json", "verdict": "clear_finished", "reasons": ["finished/stopped evidence; no session and no Paper A GPU process"], "evidence": {"branch": "paper-a-v4-ada", "run_dir": "/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z", "finished_markers_present": ["panel/finalize.json"], "tmux": {"session": "paper_a_live", "returncode": 1, "stderr": "no server running on /tmp/tmux-1030/default"}, "gpu": {"patterns": ["agent-checkpoint-intervention"], "compute_apps": 26, "unidentified_apps": 0, "paper_a_processes": []}}, "paper_a_live_waiting_for_card": false}
```

This is the capture field-for-field (only `utc` differs: capture `00:15:23Z`); verdict `clear_finished`,
`paper_a_live_waiting_for_card` present and `false`, `unidentified_apps: 0`. **The capture is reproducible and
the current state is genuinely clear_finished.** However, *why* it is clear (and whether the same config would
catch a new waiting campaign) is the problem in §4.5 / BLOCKING-1.

## 4. The `nvidia-smi` wrapper

### 4.1 The stated rationale is true (verified)

- Raw `nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader,nounits`: **30 lines, 4 with
  `used_memory == 0`** (`4052744`, `4063917`, `4020925`, `4094068`).
- Those 4 PIDs are invisible to `ps` (`ps -o pid=,user=,args= -p <pid>` returns rc 1 and no line) — dead/namespace-
  hidden contexts, as the unit says.
- The wrapper's filtered query returns **26** lines; with `process_patterns` as configured the check reports
  `compute_apps: 26, unidentified_apps: 0`. Without the wrapper, `unidentified_apps` would be 4 and the script
  raises `Unknown("a GPU compute process could not be identified (could be Paper A)")`, i.e. `unknown`, not
  `clear_*`. So the wrapper does what §2 says it does, and its JSON evidence is accurate.
- It is minimal (6 lines) and is documented in three places (wrapper comment, config `verify_before_first_use`,
  unit §2). The "a real Paper A process always holds memory > 0" premise is reasonable for a GPU training/SFT
  campaign; the wrapper only drops zero-memory lines, not real processes.

### 4.2 MAJOR-1 — the wrapper fails **open** on `nvidia-smi` failure (new defect, not in the unit)

`nvidia-smi-live` ends `set -u; nvidia-smi "$@" | awk …` — no `pipefail`, so the wrapper's exit status is
`awk`'s (0), not `nvidia-smi`'s. `paper_a_status.py` (`_run` at line 93-94, call at 140-145) raises Unknown only
when the wrapper returns non-zero or cannot run; with rc 0 and empty stdout it proceeds with `compute_apps: 0`,
and in the `finished` branch a stale finalize marker then yields **`clear_finished` instead of `unknown`**. That
inverts the design rule ("any failure → unknown; never a clearance") in the one place the wrapper was added.

Demonstrated on Ada itself (read-only):

```
$ nvidia-smi --version ; echo rc=$?        # a failing nvidia-smi (nonzero)
... rc=255
$ bash -c 'nvidia-smi --version 2>/dev/null | awk -F", " "NF < 3 { print; next } ($3 + 0) > 0 { print }"; echo rc=$?'
... rc=0                                   # wrapper pipeline status = awk status
$ bash -c 'set -o pipefail; ... same ...; echo rc=$?'
... rc=255                                 # pipefail restores the failure
```

Trigger classes: `nvidia-smi` missing from `PATH` (bash writes "command not found" to stderr, stdout empty,
awk exits 0); a silent non-zero (killed, driver reset, some `TimeoutExpired`-free failure that produces no
stdout). Note that most *noisy* failures print a line with no `", "` and the script then raises
`unparseable nvidia-smi line` (fail-safe) — but the silent class is exactly the one that matters, because the
stale `panel/finalize.json` is always present.

**Fix (one line + sha update):** add `set -o pipefail` (keep `set -u`) to the wrapper, reinstall it, update the
pinned sha256 in unit §2 and in the config comment, and re-run the check. (Optional hardening: drop only entries
that are both 0 MiB **and** `ps`-unreadable, which is the stated rationale; a blanket 0-MiB drop can in principle
hide a legitimate zero-memory context, though that is implausible for a Paper A PyTorch process. See MINOR-7.)

### 4.3 BLOCKING-1 — the config does not detect a new **waiting** Paper A campaign (stale marker false-clear)

The unit asks whether "the finished marker would be stale after a new campaign starts — does the config/tmux/
process design catch a new Paper A launch?". **No, it does not, for Paper A v4's actual launch mechanism.**

What the config's two live signals can catch:
- `tmux_session: "paper_a_live"`: if a live tmux session with exactly that name exists, the script returns
  `waiting` (alive, no Paper A GPU process) → `paper_a_live_waiting_for_card: true` → caught.
- `process_patterns: ["agent-checkpoint-intervention"]`: only applied to **GPU compute PIDs** (`gpu_processes()`,
  lines 135-168). A campaign that is on a GPU is caught (finished + process → `unknown`; or no finished evidence
  + process → `unknown`).

What it cannot catch:
- **Paper A v4 does not use tmux.** The v4 launcher `experiments/paper_a/ada/panel_v4_live.sh` starts the run with
  `setsid nohup "$PYTHON" -m experiments.paper_a.panel_v4 supervise --phase live --run "$RUN" … &` (verified on
  Ada). The v4 runbook (`protocols/paper_a/ADA_RUNBOOK_V4_20261015.md`, "Live" step, line 198) and the v4 live
  agent prompt (`docs/paper_split/v8_20261017/V4_EXPERIMENT_AGENT_PROMPT_LIVE.md:57`) contain no tmux
  instruction at all; the only tmux session names anywhere in the Paper A records are the v3 runbook's
  `v3live`/`v3pilot`. Nothing in the vendored Paper B records, tests or runbooks corroborates a session named
  `paper_a_live`; the string occurs only as this unit/config/capture's value and inside the JSON *key*
  `paper_a_live_waiting_for_card`. **The `paper_a_live` session name is unsupported hand-authored input, not an
  observed Paper A convention**, and the config's own note only covers "if Paper A is later launched in a
  different session/socket" — not "Paper A v4 is never in a tmux session".
- **A waiting campaign has no GPU process.** The v4 supervisor waits for a card inside its own process
  (`no eligible card` / `no free card (exit 75); attempt N of 7`, with the supervisor retrying); the completed
  run's own `console.log` starts with ~20 min of exactly this state (2026-10-18T23:44Z–2026-10-19T00:04Z). So
  during the window the gate exists to protect, both live signals are blind.
- **The configured run dir is fixed and a new campaign writes a new one.** `panel_v4_live.sh` computes
  `RUN="$NS/live_$(stamp)"`; the config pins the 2026-10-18 run. A new campaign's `panel/finalize.json` does not
  exist yet, but the **old** run's `panel/finalize.json` is still there, so the `finished` branch
  (`markers` non-empty, `state is None`, `alive == False`, `procs == []`, `unidentified_apps == 0`) returns
  `clear_finished`.

False-clear chain, exactly reachable: new Paper A v4 campaign launched (new `live_<stamp>` dir) → waiting for a
free card → no tmux session (v4 setsid, no `paper_a_live`) → no GPU compute process → run the configured check →
`clear_finished` / `paper_a_live_waiting_for_card: false` → a Paper B GPU unit on Ada is allowed while Paper A
waits for a card, which is precisely what `R1-ADA-CENSUS` forbids. This is not a theoretical corner: it is the
documented v4 launch mode of the very run the config describes.

**Minimum fix (document/procedure, cheap, within U0):** add to §3 and §4 (and require in every later Ada GPU
unit's pre-launch gate) two independent Paper A liveness checks that do not depend on tmux or a GPU process:

1. `ls -dt /home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_* | head -1` must be
   the configured run dir (a new launch mkdir's its run dir before any GPU work); otherwise STOP / update the
   config.
2. `pgrep -u dowling -af 'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'` must show no
   Paper A supervisor/driver (the v4 supervisor's argv contains the checkout path via `$REPO/.venv/bin/python3`);
   otherwise STOP.

Also strike or ground the `paper_a_live` claim: either record how the next campaign will be launched (and set
`tmux_session` to that real name), or state explicitly that tmux is not a v4 signal and that detection rests on
the two checks above. Optionally extend `paper_a_status.py` (separate reviewed change) with an all-process
pattern scan and/or a "newest run dir" check so the runner-level gate is self-contained, rather than relying on
an operator procedure.

Residual risk if only fixes BLOCKING-1/MAJOR-1 are applied: a future Paper A campaign that is launched by some
new mechanism (different checkout, different run-script, no new `live_*` dir, no matching process name) could
still be missed; that residual is acceptable only if each later GPU unit records the manual Paper A check and the
config is updated when Paper A's launch mode changes. I do **not** accept the residual as written because the
config's own text implies tmux/process coverage that v4 does not provide.

## 5. STOPs / must-not completeness

Present and correct: harness HEAD/branch/dirty; paper worktree/config sha mismatch; wrapper missing/sha mismatch;
Paper A status not `clear_*`; disk <50 GB; touching another user's files/processes or sudo; GPU job/lease in U0;
noise-floor/D21/D28/T1/TASL-7/TASL-2; deletion; push to main/exam-x; no model downloads. G.0-only matches the
authority rows.

Missing (all MINOR unless folded into BLOCKING-1/MAJOR-1):

- **MINOR-3 (STOP list):** no STOP for "a newer Paper A `live_*` run dir exists / a Paper A supervisor process is
  alive / a new campaign was launched" (BLOCKING-1's checks should appear as STOPs). No STOP for "the deployed
  config differs from the acceptance commit's blob" (the content now matches `45fcf0fa`, but the record must say
  so). No explicit
  "`unidentified_apps` must be 0 and the JSON must name the deployed config path" (the script enforces the first;
  state it). No requirement that the status check is re-run before **every** later Ada GPU unit, not only once
  in U0.
- **MINOR-1 (record inaccuracies):** the config's `verify_before_first_use` says the Paper A "repo log ends
  2026-10-17 'Record completed panel v4 live run…'"; the actual HEAD commit `6b0ac021` is dated **2026-10-21
  06:43:37 -0700**. It also says "no per-run phase JSON was found in the run dir"; in fact
  `panel/manifest.json` (1,318,832 B) exists with `phase: main`, `status: COMPLETED` and 764 events (finalize is
  consistent: 06:11:34 -0700). The marker is valid finished evidence, but the recon statement is wrong and the
  manifest could have been used as an explicit state-file/state_key.
- **MINOR-2 (worktree state):** the Ada paper worktree is detached at `16185b0b` **with one working-tree
  modification** (the config, content = committed blob `20ea5687…`). The unit should say so; otherwise the STOP
  "paper worktree/config sha mismatch"
  is ambiguous, and a naive clean-tree check would STOP the valid deployment. (The config must be a working-tree
  overlay: committing it in that checkout would move HEAD off `16185b0b`, so the comparison must be
  file-content-vs-committed-blob, not conftree-clean.)
- **MINOR-4 (script pin):** the procedure does not pin the `paper_a_status.py` sha256 (`6a36d24f…`). The
  `nvidia_smi_binary` config key only exists in that version; an older script would raise unknown-config-key →
  `unknown`. Pin it in §3 and the record.
- **MINOR-5 (duplicate draft on Ada):** `/home/dowling/r1_trackg_20261117/u0_verify/` holds a **different** draft
  config (`c8921734…`, its own `nvidia_smi_binary` pointing at `u0_verify/nvidia-smi-live`) plus an identical
  copy of the capture. The deployed/canonical config is the paper-worktree file (`20ea5687…`) and the wrapper in
  `bin/`; the draft should be labelled (not deleted — deletion is must-not) so the provenance record cannot pick
  the wrong one.
- **MINOR-6 (no-GPU evidence in the record):** the unit's step 3 asks to "record U0 deployed / Paper A status
  verified and the exact hashes/sha256s", but not the no-GPU confirmation. The record should include an
  `nvidia-smi --query-compute-apps` listing showing no `dowling` app, `tmux ls`, and the fact that only the
  read-only status check ran.
- **MINOR-7 (wrapper filter):** see §4.2; if the wrapper is touched for `pipefail`, also consider dropping only
  0-MiB entries whose PID `ps` cannot read.

## 6. May the unit be executed/accepted as written?

The procedure is executable today and the current evidence is correct: all §2/§3 host facts, the capture and the
re-run match, the wrapper rationale is verified, and U0 starts no GPU job. The result record U0 must contain:

- the unit sha256 `c5d3436…` (62 lines) and the reviewed config sha256 `20ea5687…` (34 lines);
- **an acceptance commit** that actually contains the config (and wrapper/capture/unit/review) — now `45fcf0fa` —
  its commit hash, and `git show 45fcf0fa:r1/scripts/configs/paper_a_status_ada.json | sha256sum` = `20ea5687…`;
  the Ada file content sha256 must equal that blob (it does: `20ea5687…`). If the deployed config is changed after
  acceptance, the new sha must be committed and the record updated; a detached clean-tree check must not be used
  as the equality test (MINOR-2);
- harness HEAD `717ad835…`, branch `r1-local-trackg-v2-20261114`, `git status --porcelain` empty;
- paper worktree HEAD `16185b0b…` (detached) and the one expected ` M` config;
- installed wrapper path, mode 755, sha256 `3be54e99…` (or the fixed wrapper's new sha);
- `paper_a_status.py` sha256 `6a36d24f…`;
- Paper A checkout branch `paper-a-v4-ada`, HEAD `6b0ac021…`, run dir, `panel/finalize.json` present, the
  console completion line `2026-10-21T13:11:35Z "not resuming: the run completed"`;
- disk free ≥50 GB (152 GiB at review);
- the full verdict JSON (verdict `clear_finished` or `clear_running`, `paper_a_live_waiting_for_card` present and
  false, `unidentified_apps: 0`, deployed config path) and its sha256;
- the mandatory Paper A liveness checks from BLOCKING-1 (newest `live_*` dir, no live v4 supervisor) and the
  statement of the residual risk they cover;
- the no-GPU confirmation (MINOR-6).

### Verdict detail

- **BLOCKING-1** — the Paper A gate is not grounded in Paper A v4's actual launch mode: `tmux_session:
  "paper_a_live"` is unsupported (v4 uses `setsid nohup`, no tmux), a waiting campaign has no GPU process, and
  the configured finished marker is from the old run dir; a new waiting v4 campaign therefore yields a false
  `clear_finished`. Fix by adding the newest-`live_*`-dir and no-v4-supervisor checks to the unit/STOPs and to
  every later GPU unit's pre-launch gate (and/or extend `paper_a_status.py`), and strike/ground the `paper_a_live`
  claim. Re-review.
- **MAJOR-1** — `nvidia-smi-live` lacks `pipefail` and fails **open** on a silent `nvidia-smi` failure/missing
  binary (`clear_finished` instead of `unknown`). Fix `set -uo pipefail`, reinstall, update the pinned sha, re-run.
- **Resolved during this review (was MAJOR-2)** — when the live checks were taken, the config (the
  safety-critical bytes) was uncommitted in both the review worktree and the Ada paper worktree, and the unit's
  "sha256 equals the committed one" was false at review time (committed blob was the template `30f5896…`).
  Commit `45fcf0fa`, made by another agent while this review was being written, added the exact reviewed bytes:
  `git show 45fcf0fa:r1/scripts/configs/paper_a_status_ada.json` = `20ea5687…`, unit = `c5d3436…`, wrapper =
  `3be54e99…`, capture = `db9618a5…`; the deployed Ada file content equals the committed blob. No fix required
  beyond pinning `45fcf0fa` in the result record and keeping the commit/content equality check. This resolution
  is a provenance fact, not an acceptance of BLOCKING-1/MAJOR-1.
- **MINOR-1…7** — as §5.

`Verdict: not accepted.` The unit is close and the reconnaissance is sound, but as written it would certify a
Paper-A gate that can fail exactly in the waiting-for-a-card case the authority row exists to protect, and its
wrapper can turn a `nvidia-smi` failure into a clearance. Fix BLOCKING-1 and MAJOR-1 (plus the MINORs
that are cheap), commit the revised bytes, then re-submit the exact revised bytes (unit + config + wrapper +
capture) for a fresh review.

---

Reviewer artifact; uncommitted at the time of writing. This review did not modify the unit, the config, the
wrapper, the capture, or any Ada file, and did not start a GPU job. The worktree gained commits `45fcf0fa`
(which tracked the reviewed U0 bytes) and `44b52368` (U1) from other agents during the review; the four U0
subject bytes were re-hashed after those commits and are identical to the reviewed bytes. Canonical unit bytes
reviewed: `c5d343633b4946fba189b04e06b24900dc65a33e42c00d1c0c0dc9db55f52805` (62 lines). Review file sha256 and
line count are reported with the delivery of this review.
