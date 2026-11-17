# Track G G.0 U0 on Ada — independent review, round 3 (fix verification, 17 Nov 2026)

Reviewer: fresh independent agent (round 3; did not write the unit, config, wrapper, capture, an Ada file, or
reviews R1/R2). Review period 2026-11-17 00:40–00:47Z (Mac clock). Read first: round-1 review
`reviews/TRACKG_U0_DEPLOY_REVIEW_20261117.md` (292 lines, 24,682 B, sha256 `3fb81927…`, **not accepted**:
BLOCKING-1 gate blind to a new waiting Paper A campaign; MAJOR-1 wrapper failed open; MINORs) and round-2 review
`reviews/TRACKG_U0_DEPLOY_REVIEW_R2_20261117.md` (328 lines, 28,970 B, sha256 `a898aa93…`, **not accepted**:
BLOCKING-1 fixed, MAJOR-1 fixed, **MAJOR-2 open** — canonical rev-2 config/wrapper uncommitted, Ada deployed
config still the old `20ea5687…`, capture produced with the old config; fix = commit rev-2 bytes, install step,
deploy config/wrapper, re-run gate, record new capture/sha).

Access was read-only: `ssh experiment_zhixu` (user `dowling`, uid 1030, host `ucrtasl`) running only
`date`, `hostname`, `id`, `git rev-parse/symbolic-ref/status/log/show/cat-file`, `sha256sum`, `stat`, `ls`,
`find`, `wc`, `df`, `head/tail/sed/grep/cat`, `tmux ls`, `pgrep`, `ps`, `nvidia-smi --query-*`, plus read-only
re-runs of `r1/scripts/paper_a_status.py` with the deployed config and with throw-away configs piped through
`--config /dev/stdin` (no host file created). Two short-lived `/tmp` scratch files used only to count the raw
vs filtered compute-app lists were removed before the end of the review (verified absent); no other Ada file was
created or changed — after the runs the Ada paper worktree still showed only the pre-existing
` M r1/scripts/configs/paper_a_status_ada.json`, the harness was clean, no `__pycache__` appeared under
`r1/scripts/`, and `find … -newermt "00:41:32" -type f` under the deployment root returned nothing. **No GPU
job, no lease, no persistent host write (only the two self-created `/tmp` counters above, removed), no
commit/push, no deletion, no other user's files or processes touched.**

Concurrency note (read-only): when this review began the Mac worktree HEAD was `610fea63`; during the review
another agent committed TASL-2 work on the same branch (HEAD now `507b5279`, 2026-11-17T01:41:43+01:00) and
created an untracked `docs/r1/reports/trackg_g0_20261117/TRACKG_CENSUS_20261117.md`. `git log 610fea63..HEAD --
<U0 paths>` is empty and `git diff 610fea63 -- <U0 paths>` is empty, and `610fea63` is an ancestor of HEAD, so
the canonical bytes below are read from the immutable acceptance commit and are unchanged in the working tree.

## 0. Subject bytes, authority, method

| subject | canonical bytes (brief) | observed at this review |
|---|---|---|
| unit `docs/r1/proposals/TRACKG_U0_DEPLOY_20261117.md` | `957dee34…` / 95 lines | matches: 7,275 B / 95 lines / `957dee34ecff8394950f81b09c71cb336cce589ac803b1770efecb7e410c57ec`, worktree clean vs `610fea63` |
| config `r1/scripts/configs/paper_a_status_ada.json` | `c75bf9c3…` | matches: 2,636 B / 33 lines / `c75bf9c35624b4474bd2260bd3e14621f25ce29c7f09bb237f6b49218e566856`; **Ada deployed copy equals it** (§2) |
| wrapper `docs/r1/reports/trackg_g0_20261117/nvidia-smi-live` | `7e0ec81a…` / 491 B | matches: 491 B / 7 lines / `7e0ec81af481b914aeed5cbb0c10040f19cd9a3b624630adfa5d69eabbb6aaf0`, mode `100755`; **Ada installed copy equals it** (§2) |
| capture `docs/r1/reports/trackg_g0_20261117/u0_status_20261117.json` | `6b62dd2a…` | matches: 829 B / 1 line / `6b62dd2aa5bfc2fa99fd10eb7cb0c6e17ecb88b68ba0ddf31e6cd11e22edc79a`; = Ada `u0_verify/status_final.json` |
| R1 review | `3fb81927…` / 292 lines | matches: 24,682 B / 292 lines; present in the acceptance commit |
| R2 review | `a898aa93…` / 328 lines | matches: 28,970 B / 328 lines; present in the acceptance commit |

Authority re-checked (Mac, `git show origin/author-d8-confirm-20261117:docs/r1/PLAN.md`): `R1-TRACKG-G0-GO`
line 1258 authorises exactly U0 (deploy `r1-local-trackg-v2-20261114` @ `717ad835`, configure and verify
`paper_a_status_ada.json`, STOP if it cannot be judged `clear_*`) → U1 → U2 (“每次重查空卡、共享与 Paper A 门”)
→ U4, ENGINEERING_ONLY, per-unit independent review, resumable units only, Paper A first, no disturbance of
other users; `R1-TRACKG-PORT-OWNER` line 1259. G.0 makes no noise-floor/D21 conclusion. The unit's citations
and G.0-only restriction are correct.

## 1. Acceptance commit — contents (task item 1)

`610fea6380607679a2d20d911c30d7c60deeca50`, parent `44b52368`, author/committer date
2026-11-17T01:40:23+01:00 (= 00:40:23Z, Mac clock), subject
`docs(r1): Track G U0 revision 3 — Paper A liveness gate, fail-closed wrapper, deployed config pin`.
Six paths, all required bytes present:

| path at `610fea63` | status | blob sha256 | size / lines |
|---|---|---|---|
| `docs/r1/proposals/TRACKG_U0_DEPLOY_20261117.md` | M (rev 3) | `957dee34…` | 7,275 B / 95 |
| `r1/scripts/configs/paper_a_status_ada.json` | M (rev 2) | `c75bf9c3…` | 2,636 B / 33 |
| `docs/r1/reports/trackg_g0_20261117/nvidia-smi-live` | M | `7e0ec81a…` | 491 B / 7, mode 100755 |
| `docs/r1/reports/trackg_g0_20261117/u0_status_20261117.json` | M (new capture) | `6b62dd2a…` | 829 B / 1 |
| `docs/r1/reviews/TRACKG_U0_DEPLOY_REVIEW_20261117.md` | A (R1) | `3fb81927…` | 24,682 B / 292 |
| `docs/r1/reviews/TRACKG_U0_DEPLOY_REVIEW_R2_20261117.md` | A (R2) | `a898aa93…` | 28,970 B / 328 |

`git cat-file -e 610fea63:r1/scripts/configs/paper_a_status_ada.json` succeeds, i.e. `c75bf9c3…` now exists as a
git object (the exact defect R2 raised). The committed wrapper is the fixed, fail-closed wrapper
`7e0ec81a…`, not the old fail-open `3be54e99…` (383 B) that was still the `HEAD` blob at round 2.

## 2. MAJOR-2 — CLOSED: committed, installed, re-captured, and pinned

### 2.1 Ada deployment equals the acceptance-commit blobs

| item | observed on Ada (read-only, 00:41–00:46Z) |
|---|---|
| deployed config `…/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json` | sha256 **`c75bf9c3…`**, 2,636 B, mtime 2026-11-17 **00:40:16Z** (Ada clock) = `610fea63:` blob |
| installed wrapper `…/bin/nvidia-smi-live` | sha256 **`7e0ec81a…`**, 491 B, mode `755`, mtime 2026-11-17 **00:40:22Z** = `610fea63:` blob; normal query rc 0, 26 lines |
| `find /home/dowling/r1_trackg_20261117 -name paper_a_status_ada.json` | only the deployed `c75bf9c3…` (2,636 B, paper worktree) and the old draft `c8921734…` (2,169 B, `u0_verify/`, not used) |
| `find … -name nvidia-smi-live` | only the canonical `7e0ec81a…`; the old 383 B fail-open copy was **moved aside, not deleted**, as `u0_verify/nvidia-smi-live.stale.20261117T004027Z` (sha256 `3be54e99…`) |

R2's two concrete defects are therefore gone: the Ada config is the canonical `c75bf9c3…` (previously
`20ea5687…`), and the installed wrapper is the committed `7e0ec81a…` (previously uncommitted).

### 2.2 The unit now contains the install step and the deployed-config-vs-commit STOP

- §4 step 3 (lines 74–78): “**Install step (MAJOR-2 fix):** deploy the exact committed
  `paper_a_status_ada.json` to `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/
  paper_a_status_ada.json`, verify its sha256 equals the acceptance-commit blob, set the frozen wrapper
  `7e0ec81a…` at `/home/dowling/r1_trackg_20261117/bin/nvidia-smi-live`, move any stale `u0_verify/` wrapper
  aside (never delete), and record the deployed config/wrapper sha256 and the gate-run timestamps in the
  capture.”
- §3 lines 56–57: “The deployed Ada copy must equal this commit blob; **a mismatch is a STOP before the gate
  run**.” §5 STOP list includes “paper worktree/config/script/wrapper sha mismatch”.
- §3 lines 53–54 states the config sha as “pinned by the commit that carries this unit”, and §4 step 4 requires
  the acceptance record to carry the deployed-config sha and the acceptance commit. A detached clean-tree check
  is not used as the equality test (the deployed file is the expected working-tree ` M` overlay).

### 2.3 The capture was produced after the deployment, with the deployed config

| event | timestamp | evidence |
|---|---|---|
| config installed | 00:40:16Z (Ada clock) | `stat` mtime; sha `c75bf9c3…` = acceptance blob |
| wrapper installed | 00:40:22Z | `stat` mtime; sha `7e0ec81a…` = acceptance blob |
| gate run (capture) | **00:40:27Z** | capture `utc`; capture `config` = the deployed path |
| capture written | 00:40:30Z | `u0_verify/status_final.json` mtime; sha `6b62dd2a…` = committed capture |

So the committed capture `6b62dd2a…` is a post-deployment run against the canonical config — the R2 objection
(capture produced with the old `20ea5687…`) no longer applies. The capture JSON records the deployed config
**path** and the gate **UTC**, but not the config/wrapper sha256; the sha pin lives in unit §3/§4 and in the
commit blob, and the mtime ordering above closes the chain. Procedure wording (“record … in the capture”) is a
MINOR-20 record detail, not a provenance break.

Clock note (for future readers): Ada's clock ran ~13–20 s ahead of the Mac during the review (measured
Ada 00:45:20Z vs Mac 00:45:00Z), so the capture's `utc` (Ada) and the commit's date (Mac) are not directly
comparable; the 4 s apparent ordering (capture `00:40:27` vs commit `00:40:23`) is clock skew, not a
commit-before-capture anomaly. The internal Ada ordering above is consistent.

## 3. BLOCKING-1 and MAJOR-1 still hold (task item 3)

### 3.1 BLOCKING-1 — the three-check pre-launch gate is present and correctly worded

Unit §2 lines 19–37 mandates, before **every** Paper B GPU unit on Ada (including each U2 unit), all three:
(a) newest `results/paper_a/replay_panel_v4/live_*` (under the Paper A checkout) first entry == configured
`run_dir`, a newer `live_*` → STOP; (b) `pgrep -u $(id -u) -af
'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'` must be empty after excluding the
check's own command line and the SSH shell, any match → STOP; (c) `paper_a_status.py --config
r1/scripts/configs/paper_a_status_ada.json` → verdict in {`clear_running`,`clear_finished`},
`paper_a_live_waiting_for_card` present and false, `unidentified_apps: 0`. All three must pass; “the same three
checks are copied into every later Ada GPU unit (U2) as a pre-launch gate; a STOP there is a unit STOP, not the
night.” Correct.

The fix remains grounded in the actual v4 launch mode, re-verified read-only on Ada this round:

- `experiments/paper_a/ada/panel_v4_live.sh` (lines 9–25): `NS="$REPO/results/paper_a/replay_panel_v4"`;
  `RUN="$NS/live_$(stamp)"`; `mkdir -p "$RUN"`; then
  `setsid nohup "$PYTHON" -m experiments.paper_a.panel_v4 supervise --phase live --run "$RUN" …`. The run dir
  is created before the supervisor starts and before any card is selected, so check (a) catches a new
  waiting campaign (and a campaign whose process already exited).
- `experiments/paper_a/ada/common.sh` lines 4–6: `REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"`,
  `PYTHON="${PYTHON:-$REPO/.venv/bin/python3}"`, so the supervisor argv contains both
  `/home/dowling/agent-checkpoint-intervention/` (the venv path) and `-m experiments.paper_a.panel_v4` — check
  (b) sees a waiting supervisor even though a waiting campaign has no GPU process.

Live state passes all three checks (§6). Residual false-clear paths, which the unit does **not** currently
record (MINOR-14, open) and which must appear in the acceptance record / U2 proposal, are:

1. **Different run-dir pattern / different namespace:** a future launcher writing `results/paper_a/<new_ns>/run_*`
   instead of `replay_panel_v4/live_*` evades check (a) while waiting.
2. **Renamed module / different checkout:** a campaign launched from a checkout path that does not contain
   `agent-checkpoint-intervention`, with a module name that does not contain `experiments.paper_a.panel_v4` or
   `panel_v4_live`, evades check (b) (it would have to also write outside `live_*` to evade all three).
3. **Mid-run start:** a Paper A campaign launched *after* a U2 GPU run has started is not monitored during the
   run; mitigation is the authority's resumable-unit rule plus re-running §2 before the next launch/resume.
4. **TOCTOU:** the gate is a snapshot taken before launch; a campaign launched between the gate and the GPU
   start is not detected. Mitigation: run checks (a)+(b) immediately before the launch command in the same
   session, record UTC, and re-run if more than a few minutes elapse. §5 does not make a stale-gate a STOP.
5. **Operator mis-exclusion in (b):** dropping a real match as if it were the self line would fail open; the
   heredoc `ssh host bash -s` form self-matches nothing (verified) and avoids the judgement entirely.
6. **Wrapper blanket 0-MiB drop** (old MINOR-18/optional): a hypothetical real Paper A GPU process reporting
   0 MiB would be filtered out; the stated premise (a real process always holds memory > 0) is reasonable and
   was accepted in R1/R2.

None of these re-opens BLOCKING-1 as written for the current v4 launcher; they are residual risks that must be
stated, not silently accepted.

### 3.2 MAJOR-1 — the wrapper fails closed, verified live

- Canonical installed wrapper = `7e0ec81a…`, 491 B, mode 755, `set -uo pipefail` followed by
  `nvidia-smi "$@" | awk -F', ' 'NF < 3 { print; next } ($3 + 0) > 0 { print }'`.
- Normal query rc **0**, 26 lines (raw `nvidia-smi`: 30 apps, 4 zero-memory rows; filtered 26 / 0
  unidentifiable).
- Failing invocation `nvidia-smi-live --version` → wrapper rc **255**, identical to raw `nvidia-smi --version`
  rc 255.
- The old 383 B fail-open copy, now `u0_verify/nvidia-smi-live.stale.20261117T004027Z`, returns rc **0** on the
  same invocation — it reproduces exactly the old MAJOR-1 defect, confirming the move-aside matters and the
  installed copy is the fixed one.
- End-to-end: with the deployed config’s `nvidia_smi_binary` overridden (config piped via `/dev/stdin`, no host
  file), `nvidia_smi_binary=/bin/false` → `verdict: unknown`, reason `nvidia-smi failed (rc=1)`;
  `/nonexistent/nvidia-smi` → `verdict: unknown`, reason
  `nvidia-smi could not run: FileNotFoundError(2, 'No such file or directory')`. A wrapper failure therefore
  reaches `unknown`, never a clearance. (`paper_a_status.py` prints the verdict and exits 0 by design; callers
  refuse on `true` and on a missing/`unknown` key.)

## 4. Three-check gate read-only re-run vs the committed capture (task item 2)

All commands read-only; no lease, no GPU job, no host write.

**(a) Newest `live_*` (from the Paper A checkout):**

```
$ ls -dt /home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_*
/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z
```

Only one `live_*` exists; it equals the configured `run_dir` (`results/paper_a/replay_panel_v4/live_20261018T234416Z`,
resolved against the checkout). PASS.

**(b) Paper A process scan, self-excluded (exact output):**

```
$ ssh experiment_zhixu bash -s <<'EOF'
pgrep -u 1030 -af 'experiments.paper_a.panel_v4|panel_v4_live|agent-checkpoint-intervention'
echo "pgrep_rc=$?"
EOF
pgrep_rc=1                      # empty → PASS
```

The naive form `ssh experiment_zhixu "pgrep -u 1030 -af '<pattern>'"` returns exactly one line — the check's
own `bash -c pgrep …` command line (PID 1471993, rc 0) — which is the expected self-match; excluding it gives
empty. The heredoc form avoids the self-match entirely. PASS. A broader scan for `trackg|paper_a|trackp|
panel_v4|nvidia-smi-live` under uid 1030 was also empty (rc 1). No tmux server: `tmux ls` →
`no server running on /tmp/tmux-1030/default` (rc 1).

**(c) Full gate re-run against the deployed config, `2026-11-17T00:43:10Z` (Ada clock), rc 0:**

```json
{"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)", "utc": "2026-11-17T00:43:10Z",
 "host": "ucrtasl",
 "config": "/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json",
 "verdict": "clear_finished",
 "reasons": ["finished/stopped evidence; no session and no Paper A GPU process"],
 "evidence": {"branch": "paper-a-v4-ada",
              "run_dir": "/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z",
              "finished_markers_present": ["panel/finalize.json"],
              "tmux": {"session": "paper_a_live", "returncode": 1,
                       "stderr": "no server running on /tmp/tmux-1030/default"},
              "gpu": {"patterns": ["agent-checkpoint-intervention"], "compute_apps": 26,
                      "unidentified_apps": 0, "paper_a_processes": []}},
 "paper_a_live_waiting_for_card": false}
```

Config sha used = `c75bf9c3…` (verified immediately before the run); no `__pycache__` was created. Comparison with
the committed capture `6b62dd2a…` (utc `2026-11-17T00:40:27Z`): **identical in every field** — verdict,
reasons, evidence (branch, run_dir, finalize marker, tmux rc 1/no server, patterns, compute_apps 26,
unidentified_apps 0, paper_a_processes []), and key false — except `utc` and the identical config path. PASS.
The unit §3 line 63–65 description of the final run matches the capture and this re-run.

## 5. Host facts vs unit §3 (task item 5)

| check | observed (17 Nov 2026, 00:41–00:46Z) | vs unit §3 |
|---|---|---|
| harness | `/home/dowling/r1_trackg_20261117/autoresearch_harness` HEAD `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `r1-local-trackg-v2-20261114`, `git status --porcelain` empty | PASS, matches |
| paper worktree | `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b`, detached (`git symbolic-ref -q HEAD` rc 1), HEAD `16185b0b4035a58814bce360780182f0e3c34442`; status exactly ` M r1/scripts/configs/paper_a_status_ada.json`; the worktree’s own HEAD blob is the original template `30f5896…`, while the deployed overlay `c75bf9c3…` = the **committed ops-branch** config at `610fea63` (so §3 line 47’s “identical to the committed ops-branch config” is accurate; it is not the paper worktree HEAD blob, which is the intended overlay) | PASS, matches |
| script | `r1/scripts/paper_a_status.py` sha256 `6a36d24f16724e8a381a31f20d4a00a6c59827a36b375aa1e4efb26278478085`, unmodified | PASS, matches |
| disk | `/dev/md0p3` total 1,876,215,308,288 B, **162,443,051,008 B free** (~151.3 GiB, 91 % used) | PASS (≥50 GB; unit §3’s “162.5 G” is a negligible rounding drift) |
| no our GPU job | raw `nvidia-smi` 30 compute apps: 26 readable owners (`asif` 10, `zihaozhao` 16) and 4 zero-memory PIDs (`4052744`, `4063917`, `4020925`, `4094068`) whose `ps -o user=` is empty; wrapper query 26 apps / 0 unidentifiable; **no `dowling` GPU compute PID** (explicit per-PID owner scan); no Track G process (`pgrep -u 1030` for `trackg|paper_a|trackp|panel_v4` empty, rc 1); `tmux ls` no server | PASS, matches |
| GPUs | 8× NVIDIA RTX 6000 Ada Generation | PASS |
| Paper A checkout | branch `paper-a-v4-ada`, HEAD `6b0ac021753eeb46c652db2b889c03451f217183` (2026-10-21T06:43:37 −07:00, “Record completed panel v4 live run and strict receiving outputs”) | PASS, matches §3 (and corrects the config prose, MINOR-9) |
| Paper A run evidence | only `live_*` is `…/live_20261018T234416Z`; `panel/finalize.json` 1,314 B; `panel/manifest.json` 1,318,832 B with `phase: main`, `status: COMPLETED`, 764 events; `console.log` last line `=== 2026-10-21T13:11:35+00:00 supervisor (live): segment 30 ended (exit 0): not resuming: the run completed` | PASS, matches |
| unit/config/wrapper/capture sha | `957dee34…` / `c75bf9c3…` / `7e0ec81a…` / `6b62dd2a…` = brief and commit | PASS |

## 6. Remaining MINORs from R2 — status

| R2 item | status this round |
|---|---|
| **MINOR-8** `--check-config` false claim | **FIXED** — §3 lines 54–56 now say `paper_a_status.py` has no `--check-config` path and the `64073cea…` TASL-2 Unit B digest does not apply here |
| **MINOR-9** repo-log date / manifest | **STILL OPEN (config bytes)** — unit §3 now correctly says 2026-10-21 and cites `panel/manifest.json` (`phase: main`, `status: COMPLETED`, verified), but the committed config `verify_before_first_use[0]` still says **“repo log ends 2026-10-17”** and `[1]` still says **“no per-run phase JSON was found in the run dir”** (the run dir has `panel/manifest.json` with `phase: main`); the unit even notes “the repo at Ada HEAD shows the 2026-10-21 commit (not 10-17)”, so the config prose contradicts both the unit and the host |
| **MINOR-10** tmux placeholder | **PARTIAL** — unit §2 lines 21–23 now correctly call `paper_a_live` “a placeholder, not a v4 signal”; the config `tmux_session` note (line 8) still says “if Paper A is later launched in a different session/socket, set it here before relying on a clear_finished verdict”, which still implies tmux coverage; reword to “tmux is not a v4 signal; defensive placeholder only; detection rests on the §2 gate” |
| **MINOR-11** pgrep operationalisation | **PARTIAL** — §2 line 30–31 now says “excluding the check’s own command line (and the SSH shell)”; no exact command is given. Verified: the heredoc `ssh host bash -s` form is empty rc 1, the naive `ssh host "…"` form returns exactly one self line. Fail-safe, so MINOR only |
| **MINOR-12** STOP deployed config ≠ commit blob | **FIXED** — §3 line 56 (“a mismatch is a STOP before the gate run”) + §5 “config … sha mismatch” |
| **MINOR-13** stale `u0_verify/` artifacts | **PARTIAL** — the old 383 B fail-open wrapper was **moved aside, not deleted**, to `nvidia-smi-live.stale.20261117T004027Z` (sha `3be54e99…`; verified rc 0 on a failing invocation), which is the substantive fix; the draft config `c8921734…` (2,169 B) and old captures `status.json` (`db9618a5…`) / `status_r2.json` (`0044cecd…`) remain unlabelled and there is no `u0_verify/README`; unit §3 notes only the draft config. Labelling is still open (new MINOR-21) |
| **MINOR-14** residual false-clear paths recorded | **OPEN** — unit contains no residual-risk paragraph (grep for `residual|TOCTOU|mid-run|v5` is empty). The residuals are listed in §3.1 above and must go into the acceptance record / U2 proposal |
| **MINOR-15** gate-1 clarity | **PARTIAL** — §2 says “(under the Paper A checkout)”; it does not state that the comparison is on the resolved absolute paths (the config `run_dir` is relative to the checkout) or that an empty `ls`/error is a STOP |
| **MINOR-16** record details | **PARTIAL** — §4 step 2 (“capture each output with SHA256SUMS”) and §4 step 4 (config/script/wrapper/capture shas, deployed-config sha, gate timestamps, full JSON, newest-run-dir + pgrep results, no-GPU confirmation) are present, but the actual capture is only the 829 B status JSON; there is no SHA256SUMS file and no saved output for checks (a)/(b) on Ada or in the repo; the capture does not embed the config/wrapper sha (new MINOR-20) |
| **MINOR-17** U2 enforcement | **OPEN** — still no U2 proposal (`docs/r1/proposals/` has no U2; only `TRACKG_U0_DEPLOY_20261117.md` for Track G), so “copied into every later Ada GPU unit” remains prose only; have U2 quote §2 verbatim (plus the residuals) and have its review check it, or install a versioned gate script with a pinned sha |
| **MINOR-18** optional wrapper hardening | unchanged and still optional: the wrapper drops **every** 0-MiB entry, not only ps-unreadable ones; premise acceptable for Paper A |

New MINORs this round (none blocking):

- **MINOR-19 (revision label / changelog — new):** the unit’s first line still reads `# Unit (revision 2)` and
  the status paragraph says “Revision 2 answers the round-1 review”; the acceptance commit is titled “revision
  3” and this revision also folds in the R2 MAJOR-2 fix (install step). Update the header/changelog to revision 3
  and reference the round-2 review; a future reader must be able to tell which review a revision answers.
- **MINOR-20 (capture/record pin detail — new):** unit §4 step 3 says “record the deployed config/wrapper
  sha256 and the gate-run timestamps in the capture”, but the committed 829 B capture contains only the config
  *path* and one `utc`; the sha pin lives in unit §3/§4 and in the commit. The acceptance record must therefore
  carry explicitly: deployed-config sha `c75bf9c3…` (= acceptance blob), wrapper sha `7e0ec81a…`, the three gate
  UTC stamps (or the single gate-run UTC + the exact commands), and a SHA256SUMS bundle of the three gate
  outputs. Provenance itself is closed by the deploy/capture mtime ordering (§2.3).
- **MINOR-21 (`u0_verify` labelling — new):** stale wrapper is correctly moved aside; still label/README the
  draft config and the two old captures (no deletion) so a future operator cannot install/quote the old
  fail-open bytes or the old-status capture by mistake.

## 7. Scope / STOP / must-not — PASS

No GPU job/lease in U0, no measurement, no noise-floor/D21/D28, no T1 sweep, no TASL-7/TASL-2 action, no other
user’s files/processes, no deletion, no push to main/exam-x, no model downloads, no change to Paper A’s files —
all present in §1/§5/§6. The authority’s G.0-only scope matches. “A STOP is an item STOP, not the night” is
present (§2 line 37, §5 title); dependents skipped. The STOP list (§5) covers harness HEAD/branch/dirty; paper
worktree/config/script/wrapper sha mismatch; any of the three gate checks failing; a newer `live_*` or any pgrep
match; `paper_a_status.py` failing including a wrapper failure (must fail closed); disk <50 GB; any need to touch
another user’s files/processes, sudo or a GPU job in U0. Missing: empty-`ls`/wrong-cwd gate-1 STOP (MINOR-15),
a stale-gate/TOCTOU window if that mitigation is adopted (MINOR-14/15). The committed config sha and the
deployed-config STOP are present.

## 8. Verdict

- **BLOCKING-1 — FIXED, still holds.** Three-check pre-launch gate present and correctly worded; grounded in
  the verified v4 `setsid nohup` launcher (run dir created before the supervisor/card) and the venv/module argv;
  live state passes (a)/(b)/(c). Residuals must be recorded (MINOR-14).
- **MAJOR-1 — FIXED, still holds.** `set -uo pipefail`; installed sha/mode match the acceptance commit;
  `--version` rc 255 = raw `nvidia-smi` rc, old moved-aside copy rc 0, and end-to-end failure → `unknown`.
- **MAJOR-2 — CLOSED.** The acceptance commit `610fea63` carries the rev-2 config `c75bf9c3…`, the fail-closed
  wrapper `7e0ec81a…`, the new capture `6b62dd2a…`, the rev-3 unit `957dee34…` and both reviews; the Ada
  deployed config and installed wrapper hash-equal the commit blobs; the old fail-open wrapper was moved aside
  (not deleted); the capture post-dates the deploy and reproduces on re-run; the install step and the
  deployed-config-vs-commit STOP are in the unit.
- **MINORs:** 8 and 12 fixed; 9, 10, 11, 13, 15 and 16 partial; 14 and 17 open; 18 optional; new 19–21. None
  of these affects the deployed bytes or the verified gate — they are documentation/prose, residual-risk
  recording and record-completeness items.

**Verdict: `accepted`.** There is no BLOCKING and no MAJOR; U0 may be recorded as **deployed / Paper A gate
verified**. The acceptance result record must contain:

- unit `957dee34…` (95 lines), config `c75bf9c3…` (2,636 B), script `6a36d24f…`, wrapper `7e0ec81a…` (491 B,
  mode 755), capture `6b62dd2a…` (829 B);
- the **acceptance commit** `610fea63` and `git show 610fea63:<path> | sha256sum` equality for
  unit/config/wrapper/capture, with the deployed Ada config sha = that committed blob (not a clean-tree check),
  plus the installed wrapper sha and the deploy timestamps 00:40:16Z / 00:40:22Z (Ada clock);
- harness `717ad835…`, branch `r1-local-trackg-v2-20261114`, clean; paper worktree `16185b0b…` detached with the
  one expected ` M` config; disk ≥50 GB (observed 162,443,051,008 B free); no `dowling` GPU compute PID; no tmux
  server;
- Paper A branch `paper-a-v4-ada`, HEAD `6b0ac021…` (2026-10-21), run dir, `panel/finalize.json` (1,314 B),
  `panel/manifest.json` (`phase: main`, `status: COMPLETED`, 764 events), console completion line
  `2026-10-21T13:11:35Z`;
- the full verdict JSON (`clear_finished`, `paper_a_live_waiting_for_card: false`, `unidentified_apps: 0`,
  `compute_apps: 26`) and the **three gate outputs with their SHA256SUMS** and UTC stamps (newest `live_*`
  absolute path == configured run dir; pgrep empty with the exact command/self line; gate re-run at
  00:43:10Z reproduced the capture except `utc`); note the ~13–20 s Ada/Mac clock skew for timestamps;
- an explicit no-GPU confirmation (compute-apps listing/all owners, `tmux ls`, only read-only checks run);
- the **residual-risk statement** of §3.1 (future launcher/run-dir pattern, renamed module/different checkout,
  mid-run start, TOCTOU, operator mis-exclusion, blanket 0-MiB drop) and the statement that every later U2
  launch re-runs §2 and quotes it; the remaining MINOR prose fixes (9, 10, 11, 13, 15, 16, 17, 19–21) may land
  in a follow-up docs commit and do not block recording U0 as deployed.

---

Reviewer artifact; uncommitted at the time of writing, at
`docs/r1/reviews/TRACKG_U0_DEPLOY_REVIEW_R3_20261117.md`. This review did not modify the unit, config, wrapper,
capture, or any Ada file; it started no GPU job and made no persistent host write (the Ada paper worktree still shows only
the pre-existing ` M` config, the harness is clean, no new `__pycache__` under `r1/scripts/`, and no file under
the deployment root was modified after 00:41:32Z; the `/dev/stdin` config tests created no host files; the two
`/tmp` scratch counters were removed). The Mac worktree HEAD moved from `610fea63` to `507b5279` (another agent’s
TASL-2 commit) during the review, but no U0 path changed after `610fea63` and the canonical bytes above are read
from that immutable commit. The review file’s own sha256 and line count are reported with its delivery.
