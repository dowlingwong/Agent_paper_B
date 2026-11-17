# Track G G.0 U0 on Ada — independent review, round 2 (fix verification, 17 Nov 2026)

Reviewer: fresh independent agent (did not write the unit, config, wrapper or capture; did not write round 1).
Date 2026-11-17, 00:30–00:39Z. Read first: round-1 review
`reviews/TRACKG_U0_DEPLOY_REVIEW_20261117.md` (292 lines, sha256 `3fb81927…`, **not accepted**:
BLOCKING-1 gate blind to a new waiting Paper A campaign; MAJOR-1 wrapper failed open; MINORs).

Access was read-only: `ssh experiment_zhixu` (user `dowling`, uid 1030, host `ucrtasl`) running only
`date`, `hostname`, `id`, `git rev-parse/status/log/show/cat-file/ls-files`, `sha256sum`, `stat`, `ls`, `find`,
`wc`, `df`, `head/tail/sed/grep/cat`, `tmux ls`, `pgrep`, `ps`, `nvidia-smi --query-*`, and read-only re-runs of
`r1/scripts/paper_a_status.py` (docs: read files / `git symbolic-ref` / `tmux has-session` / `nvidia-smi` query /
`ps -o args=`; it signals and starts nothing). Two config-behaviour tests were done by piping JSON to
`python3 r1/scripts/paper_a_status.py --config /dev/stdin` (no host file created); one local shell-only
`pipefail` demo was run on this Mac (no files). **No GPU job, no lease, no host write, no commit/push, no
deletion, no other user's files or processes touched.** After the runs the Ada paper worktree still showed only
the pre-existing ` M r1/scripts/configs/paper_a_status_ada.json` and no new `__pycache__` (checked).

## 0. Subject bytes, authority, method

| subject | canonical bytes (brief) | observed at review |
|---|---|---|
| `docs/r1/proposals/TRACKG_U0_DEPLOY_20261117.md` | `89c2eec9…` / 88 lines | matches: 6,494 B / 88 lines / `89c2eec99d6aca73a52d0f9d9678a1b3eac8b9f91e75c24670b6cdc405247034` |
| `r1/scripts/configs/paper_a_status_ada.json` | `c75bf9c3…` | matches in the **Mac worktree** (2,636 B / 33 lines); **not** the file deployed on Ada (§4) |
| `docs/r1/reports/trackg_g0_20261117/nvidia-smi-live` | `7e0ec81a…` | matches: 491 B / 7 lines / mode 100755; installed Ada copy hashes `7e0ec81a…`, mode 755 |
| `docs/r1/reports/trackg_g0_20261117/u0_status_20261117.json` | `0044cecd…` | matches: 829 B / 1 line; byte-identical to Ada `u0_verify/status_r2.json` |
| round-1 review | `3fb81927…` | matches: 24,682 B / 292 lines |

Authority re-checked: `R1-TRACKG-G0-GO` and `R1-TRACKG-PORT-OWNER` are in
`origin/author-d8-confirm-20261117` @ `26177d82` (2026-11-17T01:05:30+01:00, +8 lines in `docs/r1/PLAN.md`).
The G0 row authorises exactly U0 (deploy `r1-local-trackg-v2-20261114` @ `717ad835`, configure and verify
`paper_a_status_ada.json`, STOP if not `clear_*`), then U1 → **U2 “每次重查空卡、共享与 Paper A 门”** (re-check
free card, sharing and the Paper A gate every time) → U4, ENGINEERING_ONLY, independent review per unit.
G.0 makes no noise floor / D21 conclusion. The unit's citations and G.0-only restriction are correct.

## 1. Round-1 findings — status

| round-1 item | state at round 2 |
|---|---|
| BLOCKING-1 (gate cannot see a new waiting campaign) | **FIXED** — see §2; fix is sound and verified live; residuals must be recorded (MINOR-14) |
| MAJOR-1 (wrapper fails open) | **FIXED** — see §3; `set -uo pipefail`, installed sha matches, failure now non-zero → `unknown` |
| MINOR-1 (record inaccuracies: 10-17, manifest) | **PARTIAL** — unit §3 now says 10-21 and cites `panel/manifest.json`; the canonical **config prose still says 2026-10-17 and “no per-run phase JSON”** (MINOR-9) |
| MINOR-2 (Ada worktree detached + one ` M`) | fixed: unit §3 states it; verified true |
| MINOR-3 (STOP list) | **PARTIAL** — “newer `live_*` / any pgrep match” is now a STOP; still no explicit “deployed config ≠ acceptance-commit blob” (MINOR-12) |
| MINOR-4 (script pin) | fixed: unit §3 pins `paper_a_status.py` `6a36d24f…`; record requires it |
| MINOR-5 (duplicate draft config) | **PARTIAL** — draft `c8921734…` is noted; the stale **383 B fail-open wrapper** and old capture in `u0_verify/` are not (MINOR-13) |
| MINOR-6 (no-GPU evidence in record) | fixed: §4.3 requires an explicit no-GPU confirmation |
| MINOR-7 (wrapper blanket 0-MiB drop) | unchanged/optional (premise reasonable; see §3.3) |
| — | **NEW MAJOR-2** (provenance/deployment; §4) and MINOR-8…18 (§7) |

## 2. BLOCKING-1 — fixed. The three-check pre-launch gate does close the stale-run-dir/waiting-campaign false-clear

The unit now mandates (§2), before **every** Paper B GPU unit on Ada (including each U2 unit), all three:
(a) newest `results/paper_a/replay_panel_v4/live_*` == configured `run_dir`; (b) `pgrep -u $(id -u) -af
'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'` empty after excluding the check's
own command line; (c) `paper_a_status.py` `clear_running`/`clear_finished` + `paper_a_live_waiting_for_card`
present and false + `unidentified_apps: 0`. A STOP there is a unit STOP, not the night.

Why this closes round-1 BLOCKING-1:

- **New campaign with a new run dir:** verified the v4 launcher `/home/dowling/agent-checkpoint-intervention/
  experiments/paper_a/ada/panel_v4_live.sh` (lines 17–21) does `RUN="$NS/live_$(stamp)"; … mkdir -p "$RUN"`;
  then `setsid nohup "$PYTHON" -m experiments.paper_a.panel_v4 supervise --phase live --run "$RUN" …`.
  **The run dir is created before any card is selected or any GPU work starts**, so check (a) catches a new
  campaign even if it is still waiting and even if its process has already exited.
- **Waiting / idle campaign has no GPU process but does have a supervisor process:** verified
  `experiments/paper_a/ada/common.sh` sets `PYTHON="${PYTHON:-$REPO/.venv/bin/python3}"` with
  `REPO=/home/dowling/agent-checkpoint-intervention`, so the supervisor argv is
  `/home/dowling/agent-checkpoint-intervention/.venv/bin/python3 -m experiments.paper_a.panel_v4 supervise …`
  — it contains **both** `agent-checkpoint-intervention` and `experiments.paper_a.panel_v4`, so check (b)
  catches the wait-for-card state that the old tmux/GPU-process signals missed.
- **pgrep self-exclusion is workable, but must be operationalised (MINOR-11).** Verified on Ada at 00:31Z:
  - naive form `ssh experiment_zhixu "pgrep -u 1030 -af '<pattern>'"` returns exactly **one** self line:
    `1363975 bash -c pgrep -u 1030 -af 'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'; echo rc=$?` (rc 0);
  - heredoc form `ssh experiment_zhixu bash -s <<'EOF' … pgrep … EOF` returns **empty, rc 1**
    (the remote command line is only `bash -s`, so nothing self-matches).
  Both are safe: a spurious self-match makes the gate STOP (fail-safe), not clear. The record should show the
  exact command used and the one excluded line.
- **The gate was re-run read-only and matches the capture** (§6): newest `live_*` = the configured
  `live_20261018T234416Z`; pgrep empty; status JSON `clear_finished`, key false, `unidentified_apps: 0`,
  `compute_apps: 26`.

Remaining false-clear paths (must be recorded as residual; they do not re-open BLOCKING-1 as written):

1. **Different launcher/checkout: a campaign that (i) is launched from a checkout path that does not contain
   `agent-checkpoint-intervention`, (ii) uses a module name that does not contain `experiments.paper_a.panel_v4`
   or `panel_v4_live`, and (iii) writes outside `results/paper_a/replay_panel_v4/live_*`** would miss all three
   existing patterns while waiting. The current v4 launch mode is covered; a future v5 must update the gate.
   (A different module name from *this* checkout is still caught through the venv path in argv.)
2. **TOCTOU:** the gate is a snapshot taken before launch; a Paper A campaign launched between the gate and the
   GPU start is not detected. Mitigation: run checks (a)+(b) immediately before the launch command in the same
   session, record UTC, and re-run if the gap is more than a few minutes.
3. **Mid-run launch:** a Paper A campaign launched *after* a long U2 run has started is not monitored. The
   authority handles this through resumable units (“只跑可断点续跑的单元”); each U2 unit should record that its
   runs are resumable and check the gate again before the next launch/resume (MINOR-14).
4. Operator mis-exclusion in (b) could in principle hide a real match, but the real supervisor line is visibly
   different from the `bash -c pgrep …` self line; a naive regex exclusion (`grep -v pgrep`) cannot hide it.

**U2 duplication:** no U2 unit/proposal exists yet (`docs/r1/proposals/` has only this U0 and the TASL-2 unit),
so “the same three checks are copied into every later Ada GPU unit (U2)” is currently only a prose obligation;
it matches the authority row, but it is unenforced until U2's own proposal and review (MINOR-17: have U2 quote
§2 verbatim, or install a versioned gate script with a pinned sha).

## 3. MAJOR-1 — fixed; verified fail-closed on Ada

3.1 **Bytes.** The canonical wrapper is 7 lines, 491 B, mode 100755:
`set -uo pipefail` followed by `nvidia-smi "$@" | awk -F', ' 'NF < 3 { print; next } ($3 + 0) > 0 { print }'`
(preceded by the explanatory comment, including “pipefail: if nvidia-smi itself fails, this helper must fail
too”). `bash -n` passes. The installed Ada copy `/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live` is
byte-identical: sha256 `7e0ec81af481b914aeed5cbb0c10040f19cd9a3b624630adfa5d69eabbb6aaf0`, 491 B, mode `-rwxr-xr-x`,
installed 2026-11-16 16:28:47 -0800 = 2026-11-17T00:28:47Z.

3.2 **Behaviour on failure is non-zero (fail-closed).** On Ada (read-only):
- normal query: 26 lines, rc 0;
- failing invocation `nvidia-smi-live --version`: **wrapper rc 255**, identical to raw
  `nvidia-smi --version` rc 255;
- the **old 383 B copy** still sitting in `u0_verify/nvidia-smi-live` (sha256 `3be54e99…`, i.e. the committed
  `HEAD:` wrapper) returns **rc 0** on the same invocation — this reproduces exactly the round-1 fail-open
  defect and shows the reinstall fixed it. (This also means the **committed** wrapper is still the fail-open
  one; see MAJOR-2.)
- local shell-only demo with the wrapper's exact awk program: `set -uo pipefail; false | awk …` → rc 1;
  without `pipefail` → rc 0; with two normal lines → rc 0.

3.3 **End-to-end `paper_a_status.py` → `unknown`, never a clearance.** Read-only, canonical config piped to
`--config /dev/stdin` on Ada:
- `nvidia_smi_binary=/bin/false` → `verdict: unknown`, reason `nvidia-smi failed (rc=1)`;
- `nvidia_smi_binary=/nonexistent/nvidia-smi` → `verdict: unknown`, reason
  `nvidia-smi could not run: FileNotFoundError(2, 'No such file or directory')`.
The script's `gpu_processes()` raises `Unknown` on `done.returncode != 0` and on `OSError/timeout`; a silent
non-zero/absent `nvidia-smi` now reaches that branch. Residual (old MINOR-7, unchanged and optional): the filter
drops **all** 0-MiB entries, not only ps-unreadable ones; the stated premise “a real Paper A process always
holds memory > 0” is reasonable (the v4 waiting state has no GPU context at all) and was already accepted in
round 1.

## 4. NEW MAJOR-2 — the canonical revision-2 bytes are not committed and the Ada deployment still carries the previous config; U0 as written cannot pass

This is the one remaining blocker. It is a **provenance/deployment pin**, not a gate-design defect: the only
functional change in the config is a comment line, and I verified the canonical config and the deployed config
produce identical verdicts on Ada. But as written, U0 §4 step 1 (“config … sha256s match the values in §3/commit”)
would **STOP** on the current host.

Evidence (all read-only, 00:30–00:39Z):

| item | observed |
|---|---|
| Mac review worktree HEAD | `44b52368` (2026-11-17T01:25:44+01:00), branch `ops-tasl-20261116`; the four revision-2 subject files are working-tree ` M` (untracked review files aside) |
| committed blobs at `HEAD` | unit `c5d3436…` (rev-1, 62 lines), config `20ea5687…`, wrapper `3be54e99…` (383 B, fail-open), capture `db9618a5…` |
| canonical rev-2 config commit | **none**: `git log --all` on the path shows exactly two commits, and their config content sha256s are `30f5896…` (`79e88d3a`, the original template) and `20ea5687…` (`45fcf0fa`); neither is `c75bf9c3…`, so no commit carries the revision-2 config (the only copy is the uncommitted Mac working-tree file) |
| Ada deployed config | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json` = sha256 **`20ea5687…`** (rev-1, 2,621 B), mtime 2026-11-16 16:15:19 -0800 = **00:15:19Z** — unchanged since the round-1 reconnaissance |
| canonical config on Ada | `find /home/dowling/r1_trackg_20261117 -name paper_a_status_ada.json -exec sha256sum` finds only `c8921734…` (the `u0_verify` draft) and `20ea5687…` (the paper worktree) — **no file with `c75bf9c3…`** |
| capture provenance | capture `0044cecd…` was generated 2026-11-17T00:28:52Z (Ada `u0_verify/status_r2.json`, mtime 00:28:58Z); the config at the capture's recorded path was still `20ea5687…` (the `u0_verify` draft `c8921734…` is not used); the JSON records the config **path** only, so the byte family is invisible in the file |
| wrapper | installed Ada copy is the fixed `7e0ec81a…`, but the committed wrapper blob is the fail-open `3be54e99…`; installing from a fresh/HEAD checkout would regress MAJOR-1 |

Consequences:

- Unit §3 line 54 (“config file sha256 `c75bf9c3…` (pinned by the commit that carries this unit)”) is
  forward-looking: no such commit exists. §3 line 47 (“the only dirty path is the intentionally deployed
  config … identical to the committed ops-branch config”) is true **only for the previous revision**
  (`20ea5687` = current `HEAD` blob); it will be false once the acceptance commit carries `c75bf9c3` while the
  Ada file is still `20ea5687`.
- The pinned capture `0044cecd…` is a capture produced with config `20ea5687…`, not with the canonical
  `c75bf9c3…` (the canonical file was created in the Mac worktree around the same time but never deployed).
- Functional impact: **none**. `git diff HEAD -- r1/scripts/configs/paper_a_status_ada.json` shows the only
  rev-1→rev-2 change is the `nvidia_smi_binary` comment line; re-running the gate on Ada with the canonical
  config piped in (`--config /dev/stdin`) gives the identical JSON/evidence as the deployed-config run and the
  capture (all fields equal except `utc` and the `config` path — checked programmatically). So the gate's
  behaviour is verified for both byte versions; the defect is only the pin/deployment.

**Exact fix (mechanical, within U0; ~1 minute):**

1. Commit the canonical rev-2 bytes as the **acceptance commit**, after folding in the MINOR-8…12 prose/STOP fixes, so
   `git show <commit>:<path> | sha256sum` = unit `89c2eec9…`, config `c75bf9c3…`, wrapper `7e0ec81a…`,
   capture `0044cecd…` (or the new values if the capture is regenerated), and confirm `c75bf9c3…` now exists
   as a git object. The committed wrapper must be `7e0ec81a…`, not the old `3be54e99…`.
2. Add an explicit deployment step to §4 (step 0 or 1a): install the acceptance-commit config blob into the Ada
   paper worktree (`…/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`, the one
   intentional ` M`) and the wrapper into `…/bin/nvidia-smi-live`; then hash-pin both. Say explicitly that the
   currently deployed config is the prior `20ea5687…` revision and must be refreshed.
3. Re-run the three-check gate **after** deployment, record the **new** capture and its sha256, and state the
   config sha actually used. If the team wants to keep `0044cecd…` as the recorded capture, the record must say
   it was produced with config `20ea5687…` and that the canonical `c75bf9c3…` differs only in the comment line.
4. The acceptance record must pin the acceptance commit and the deployed config sha = committed blob; a detached
   clean-tree check must not be used as the equality test (the config is a working-tree overlay).

After this fix a short R3 only needs to re-hash the exact committed bytes and re-read the new Ada capture; no
design re-review is needed.

## 5. Facts/hashes re-verified (17 Nov 2026, 00:30–00:39Z, host `ucrtasl`)

| # | check | observed | result |
|---|---|---|---|
| 1 | harness HEAD / branch / clean | `717ad835df32bbe1047d032fb5bb8dde5384a258`; `r1-local-trackg-v2-20261114`; `git status --porcelain` empty | PASS |
| 2 | paper worktree | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b`, HEAD `16185b0b4035a58814bce360780182f0e3c34442`, detached; status = ` M r1/scripts/configs/paper_a_status_ada.json` only | PASS (expected overlay; but content is `20ea5687…`, MAJOR-2) |
| 3 | config on Ada vs committed blob | Ada `20ea5687…` = `HEAD:` blob `20ea5687…`; canonical rev-2 `c75bf9c3…` is committed nowhere and deployed nowhere | **FAIL for canonical bytes** (MAJOR-2) |
| 4 | wrapper installed | `…/bin/nvidia-smi-live`, `-rwxr-xr-x`, 491 B, sha256 `7e0ec81a…` = canonical | PASS (mtime 00:28:47Z) |
| 5 | `paper_a_status.py` | sha256 `6a36d24f16724e8a381a31f20d4a00a6c59827a36b375aa1e4efb26278478085` = `HEAD:` blob | PASS |
| 6 | disk | `/dev/md0p3` total 1,876,215,308,288 B, **162,465,005,568 B free (~151.3 GiB, 91 % used)** | PASS (≥50 GB) |
| 7 | no GPU job by us | no `dowling` GPU compute PID: raw 30 apps, readable owners `asif` 10 + `zihaozhao` 16, and 4 zero-memory PIDs (`4052744`, `4063917`, `4020925`, `4094068`) whose `ps -o user=,args=` is empty; no tmux server; `pgrep -u 1030` for `trackg|paper_a|trackp|panel_v4` empty; only our read-only SSH ran | PASS |
| 8 | GPUs | 8× NVIDIA RTX 6000 Ada Generation | PASS |
| 9 | Paper A checkout | branch `paper-a-v4-ada`, HEAD `6b0ac021753eeb46c652db2b889c03451f217183` (2026-10-21T06:43:37-07:00 “Record completed panel v4 live run and strict receiving outputs”) | PASS (unit/config prose still says 10-17, MINOR-9) |
| 10 | Paper A run evidence | only `live_*` dir is `…/replay_panel_v4/live_20261018T234416Z` (= configured); `panel/finalize.json` 1,314 B; `panel/manifest.json` 1,318,832 B with `phase: main`, `status: COMPLETED`, 764 events; `console.log` last line `=== 2026-10-21T13:11:35+00:00 supervisor (live): segment 30 ended (exit 0): not resuming: the run completed` | PASS |
| 11 | unit / wrapper / capture sha | `89c2eec9…` / `7e0ec81a…` / `0044cecd…` = brief | PASS |
| 12 | round-1 review sha | `3fb81927…` (292 lines) | PASS |

## 6. Three-check gate read-only re-run vs capture

**(a) newest `live_*`:** `ls -dt …/replay_panel_v4/live_* | head -1` →
`/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z` — equals the
configured `run_dir`. PASS.

**(b) pgrep:** naive SSH form returns exactly the check's own `bash -c` line (`bash -c pgrep -u 1030 -af
'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'; echo rc=$?`, rc 0); heredoc
`ssh experiment_zhixu bash -s` form returns empty, rc 1. After excluding the check line: **empty**. PASS.

**(c) `paper_a_status.py` re-runs:**

- deployed config (`20ea5687…`), 2026-11-17T00:32:46Z:
  `{"verdict": "clear_finished", "reasons": ["finished/stopped evidence; no session and no Paper A GPU process"],
  "evidence": {"branch": "paper-a-v4-ada", "run_dir": "…/live_20261018T234416Z",
  "finished_markers_present": ["panel/finalize.json"], "tmux": {"session": "paper_a_live", "returncode": 1,
  "stderr": "no server running on /tmp/tmux-1030/default"}, "gpu": {"patterns":
  ["agent-checkpoint-intervention"], "compute_apps": 26, "unidentified_apps": 0, "paper_a_processes": []}},
  "paper_a_live_waiting_for_card": false}`
- canonical config (`c75bf9c3…`) piped via `/dev/stdin` at 00:33:28Z; deployed config re-run again at 00:34:30Z: identical JSON/evidence in every run.
- capture `0044cecd…` (00:28:52Z): equal to both re-runs in every field except `utc` and `config`
  (programmatic comparison: `True`/`True`). So the capture is reproducible and the current state is genuinely
  `clear_finished`; the only provenance caveat is that the capture was produced with config `20ea5687…`
  (MAJOR-2), which is behaviourally identical to canonical.

## 7. MINORs — remaining and new

- **MINOR-8 (false verification claim — new):** unit §3 line 55 says “`--check-config` placeholders `[]`, config
  digest `64073cea…`”. `paper_a_status.py` has **no** `--check-config`: on Ada
  `python3 r1/scripts/paper_a_status.py --check-config` exits rc 2, “unrecognized arguments: --check-config”.
  The sentence is copied from the TASL-2 Unit B record (`trackp.py --check-config` on `trackp_portal.json`;
  digest `64073cea…` appears as `config_sha256` in the Track P P.3a manifests). Delete it, or replace it with a
  real check (e.g. `python3 -c 'import json,sys; json.load(open(sys.argv[1]))' <config>`).
- **MINOR-9 (round-1 MINOR-1 not fully fixed):** the canonical config still says the Paper A “repo log ends
  2026-10-17” (actual HEAD `6b0ac021` is 2026-10-21; unit §3 line 65 now correctly says 10-21 — internal
  contradiction) and “no per-run phase JSON was found in the run dir” (false: `panel/manifest.json`,
  `phase: main`, `status: COMPLETED`, 764 events). Fix both lines in the config when it is committed.
- **MINOR-10 (round-1 BLOCKING-1 “ground the tmux claim”, config half):** the config note still reads
  “if Paper A is later launched in a different session/socket, set it here before relying on a clear_finished
  verdict”, implying tmux coverage; unit §2 correctly calls `paper_a_live` a placeholder and v4 `setsid`-based.
  Reword the config to “tmux is not a v4 signal; defensive placeholder only; detection rests on the §2 gate”.
- **MINOR-11 (pgrep operationalisation):** put the exact safe command in §2/§4 (recommended:
  `ssh experiment_zhixu bash -s <<'EOF' … pgrep -u 1030 -af '<pattern>' … EOF`, which self-matches nothing), or
  state exactly which self line to drop in the `ssh host "…"` form (verified: only the remote `bash -c` line),
  and record it. This is fail-safe, so it is a MINOR, not a blocker.
- **MINOR-12 (STOP list / record):** add an explicit STOP “the deployed config does not equal the acceptance
  commit's blob” (round-1 MINOR-3 partially addressed) and, if the TOCTOU mitigation is adopted, “gate not run
  within N minutes of the launch”.
- **MINOR-13 (stale artifacts on Ada, round-1 MINOR-5 extension):** `…/u0_verify/` still holds the old **383 B
  fail-open wrapper** `3be54e99…` (rc 0 on failure — the exact MAJOR-1 defect), the draft config
  `c8921734…`, and the old capture `status.json` `db9618a5…`. The unit notes only the draft config. Label all
  (no deletion — deletion is must-not), e.g. a README in `u0_verify/` pointing at the canonical `bin/` wrapper
  and the new capture, so a future operator cannot install the fail-open copy.
- **MINOR-14 (residual false-clear paths not stated):** record the §2 residuals (TOCTOU; future
  different-checkout/renamed-module/different-namespace launcher; Paper A launched mid-U2-run → keep runs
  resumable and re-check before the next launch/resume).
- **MINOR-15 (gate-1 clarity):** state that the comparison is on absolute paths (config `run_dir` is relative to
  the Paper A checkout), that the command must be run from the checkout, and that an empty `ls` result is a STOP.
- **MINOR-16 (record details):** the record should include the config sha actually used for the recorded
  capture, the three gate outputs with sha256s, the gate UTC times, and optionally `nvidia-smi --version`/driver
  and the 8-card model line (the GPU model helps interpret the 26-app count).
- **MINOR-17 (U2 enforcement):** no U2 proposal exists yet, so the “copied into every later Ada GPU unit”
  obligation is prose only; have the U2 proposal quote §2 verbatim and have its review check it, or install a
  versioned gate script with a pinned sha so later units cannot drift.
- **MINOR-18 (optional, round-1 MINOR-7):** the wrapper still drops every 0-MiB app, not only ps-unreadable
  ones. Acceptable premise for Paper A; optionally harden to drop only 0-MiB entries whose PID `ps` cannot read.

## 8. Scope / STOP / must-not — PASS

No GPU job/lease in U0, no measurement, no noise-floor/D21/D28, no T1 sweep, no TASL-7/TASL-2 action, no other
user's files/processes, no deletion, no push to main/exam-x, no model downloads, no change to Paper A's files —
all present in §1/§5/§6. `R1-TRACKG-G0-GO` G.0-only scope matches. “A failure is an item STOP, not the night” is
present (§2 line 37, §5 title), dependents skipped. The STOP list covers harness HEAD/branch/dirty, paper
worktree/config/script/wrapper sha mismatch, any of the three gate checks failing, a newer `live_*` or any
pgrep match, `paper_a_status.py`/wrapper failure (must fail closed), disk <50 GB, and any need to touch another
user's files/processes, sudo or a GPU job in U0. Missing STOPs are MINOR-12.

## 9. Verdict

- **BLOCKING-1 — FIXED.** The three-check gate is the right fix, it is grounded in the verified v4 launch mode
  (`setsid nohup`, run dir created before any card is used, supervisor argv contains the checkout path and the
  module name), the pgrep self-exclusion is workable (verified), and the current live state passes all three
  checks. Residuals (TOCTOU, future launcher/checkout, mid-run) are acceptable **if recorded**.
- **MAJOR-1 — FIXED.** `set -uo pipefail`; installed sha/mode match; failure is now non-zero (255 = raw
  `nvidia-smi` rc, old copy rc 0), and the script returns `unknown` on a failing or missing `nvidia-smi`
  (verified end-to-end on Ada).
- **MAJOR-2 — OPEN.** The canonical rev-2 config `c75bf9c3…` is committed nowhere and deployed nowhere; Ada
  still has `20ea5687…`; the pinned capture `0044cecd…` was generated with `20ea5687…`; and the committed
  wrapper is the fail-open `3be54e99…`. As written, U0 §4 step 1 would STOP on the config sha, so the unit cannot be
  executed to a PASS until the canonical bytes are committed, the config/wrapper are (re)installed on Ada, and
  the gate is re-run with the new capture recorded. No safety impact: the two config revisions are
  behaviourally identical (comment-only diff; canonical config verified live via `/dev/stdin`).
- **MINOR-8…18** as §7.

`Verdict: not accepted` — one MAJOR (MAJOR-2, a commit/deploy/re-capture pin) plus MINORs; BLOCKING-1 and
MAJOR-1 are accepted as fixed. After the four mechanical fixes in §4 (commit the canonical bytes with the
MINOR-8…12 prose/STOP corrections, state the config is currently the prior revision and add the install step,
install on Ada, re-run and record the new capture), U0 may be executed as written and the result record must
contain:

- the unit sha256 `89c2eec9…` (88 lines), config `c75bf9c3…`, wrapper `7e0ec81a…` (491 B, mode 755) and
  `paper_a_status.py` `6a36d24f…`;
- the **acceptance commit** hash and `git show <commit>:<path> | sha256sum` equality for unit/config/wrapper/
  capture, with the deployed Ada config sha = that committed blob (not a clean-tree check);
- harness `717ad835…`, branch `r1-local-trackg-v2-20261114`, clean; paper worktree `16185b0b…` detached with the
  one expected ` M` config;
- Paper A branch `paper-a-v4-ada`, HEAD `6b0ac021…`, run dir, `panel/finalize.json`, `panel/manifest.json`
  `phase: main` / `status: COMPLETED`, and the console completion line `2026-10-21T13:11:35Z`;
- disk free ≥50 GB;
- the full status JSON (`clear_finished` or `clear_running`, `paper_a_live_waiting_for_card` present and false,
  `unidentified_apps: 0`, deployed config path) and the sha256 of the **new** capture, plus the three gate
  outputs (newest `live_*` == configured; pgrep empty with the exact excluded self line) and their sha256s;
- an explicit no-GPU confirmation (compute-apps listing, `tmux ls`, only the read-only status check run);
- the §2 residual-risk statement and the statement that every later U2 launch re-runs §2 (and U2 quotes it).

---

Reviewer artifact; uncommitted at the time of writing, at
`docs/r1/reviews/TRACKG_U0_DEPLOY_REVIEW_R2_20261117.md`. This review did not modify the unit, config, wrapper,
capture, or any Ada file; it started no GPU job and made no host write (the Ada paper worktree still shows only
the pre-existing ` M` config and no new `__pycache__`; the `/dev/stdin` config tests created no host files). The
Mac worktree gained no commits during the review (HEAD still `44b52368`, branch `ops-tasl-20261116`); the four
revision-2 subject bytes were already present as working-tree modifications when the review began and were
unchanged at its end (unit `89c2eec9…`, config `c75bf9c3…`, wrapper `7e0ec81a…`, capture `0044cecd…`).
The review file's own sha256 and line count are reported with its delivery.
