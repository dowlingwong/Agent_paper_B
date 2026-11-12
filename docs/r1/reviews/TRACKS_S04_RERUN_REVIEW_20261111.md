# Track S — independent review of the S0.4 rerun at the A2-U pin (STOP 3, option (a)), 11–12 November 2026

**Reviewer.** Fresh independent reviewer (DSH teammate `track-s-reviewer-s04r2`). I did not see the
operator's work in progress and I did not take its report, STATUS entry or commit messages as evidence.
I re-read the authority documents, re-derived the numbers from the copied-back JSONL/JSON, and re-verified
the pins, commits, launch script, logs and host state directly on TASL-2 (`ssh portal_zhixu`, read-only).
I started/stopped nothing, wrote nothing on either host, ran no Track S phase, touched no TASL-7, and made
no code/pin change. Times UTC unless stated; the host's local clock is PST (UTC−8) and its log timestamps
were converted.

**Artifacts under review.**
- Operator worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackS-ops-20261030`,
  branch `trackS-ops-20261030`, tip **`cac8427089ce475d10bbee709ca4891e649eedef`** (clean at review start;
  `cac84270` = `3899b8ac` pin/launch-script commit → report/STATUS/evidence commit, authored
  `2026-11-12T01:06:51+01:00` = `00:06:51Z`).
- Report `docs/r1/reports/TRACKS_S04_RERUN_20261111.md` (200 lines), STATUS entry of 12 Nov, copy-back
  `results/r1/tracks/digits_mlp/s04_rerun20261111/` (22 files: 21 hashed files + `SHA256SUMS`, including
  `liveness/` and `host_logs/`), `r1/tracks/ops/trks-status` (one line changed).
- Fix branch `origin/mac-tracks-a2u-stale-20261111` tip **`c8b13b5d63d3d30f5afa642928f1458e863e8935`**
  (also the TASL-2 bare-repo ref), accepted commit **`fe651e589c2d6bafafc3a27e8eb7d8599845a7df`**, review
  record `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md` (sha256
  **`95f66b1a1fab341f9e6a19a0167279f85797937a6f2d0be373617dd7b6f67a4e`**), PLAN row `f82ff376`.
- STOP-3 ruling commit **`8ae46a48`**; Phase 3 report `docs/r1/reports/TRACKS_PHASE3_20261109.md`.

**Authority documents read by me, not relayed.**
- Track S operator runbook **rev 3.3** at docs commit **`13badb0`**, sha256
  `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` (verified against
  `git show 13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`), §0.1, §0.4–§0.8, Phase 3
  (S0.4, 3.0 pause drill, liveness, fit_prior, "Done when", STOP 3, 2 % rule).
- Author STOP-3 ruling verbatim (recorded in `8ae46a48`): "…选 (a)。等 Mac agent 的 A2-U 修复审查通过、新 pin
  和 PLAN 行提交后，在新目录跑 S0.4，10 个 instance 全部重跑，然后接 liveness 和 fit_prior。旧的 s04 STOP
  现场不动。" — option (a): new `--out`/`--work`, all ten instances from the start, old scene untouched,
  Phase 4 not authorised.
- PLAN §10 row **R1-TRACKS-A2U-STALE** (11 Nov) at `f82ff376` on the fix branch (also at `c8b13b5d`,
  `origin/mac-tracks-a2u-stale-20261111` and the TASL-2 bare repo): new Track S paper pin **`8237fd02`**;
  harness `a3fedbb`, GGUF, llama build and flags unchanged; read-only TASL-2 precondition with 5 passed /
  0 skipped and any failure/skip/collection error a STOP; rerun in new dirs, old scene untouched, Phase 4
  not authorised. PLAN row **R1-TRACKS-S01-RERUN** (k = 1 by clause (b)) also read.
- Fix review record (rounds 1–3) and check report `docs/r1/reports/TRACKS_A2U_STALE_S04_CHECK_20261111.md`
  (at `fe651e58`).

## 1. Scope

In scope: the delivery and acceptance of the A2-U fix as the new paper pin; the TASL-2 precondition test
(c); the pin move; the S0.4 rerun itself (provenance, session, counts, dry-run completion, 2 % rule);
`liveness` and `fit_prior`; preservation of the old `s04` scene; host end state; copy-back and hashes;
commits/pushes; the provenance/transparency note (run launched by the preceding operator phase); the
3.0 pause-drill non-repetition decision; and scope containment (no Phase 4, TASL-7, Track P, B1).
Out of scope: interpreting the S0.4 outcome, any later phase, and the TASL-7 half of Phase 3.

## 2. Evidence checked

### 2.1 Fix delivery and the acceptance claim (re-derived from the branch)

| Check | Result |
|---|---|
| `origin/mac-tracks-a2u-stale-20261111` (`git ls-remote origin` and the TASL-2 bare repo) | **`c8b13b5d63d3d30f5afa642928f1458e863e8935`** |
| Review record at the tip | sha256 **`95f66b1a…`**; three rounds, "VERDICT: accepted" (round 2) and "Verdict: accepted" (round 3, "Accepted commit: `fe651e58…`"). **Round 1 was "VERDICT: changes requested"** and its five findings (one BLOCKING, four SHOULD-FIX) were answered in rounds 2–3. |
| Pin **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** | named in the PLAN row; **ancestor** of the tip (`git merge-base --is-ancestor` true) |
| `git diff d10b05b7 8237fd02` | only `r1/tracks/a2u.py` **+37/−8** (numstat 37 8; 45 lines changed) and new `r1/tests/test_tracks_a2u_stale.py` **+302/−0**; totals 339 insertions, 8 deletions. (The report writes "+45/−8" for `a2u.py`; see MINOR 1.) |
| `8237fd02..c8b13b5d -- r1/` | **empty** (code/test identical at the pin and the tip); the three later commits are docs only, four files (`PLAN.md` +6, plan-row copy +9, check report +43, review +425) |
| Harness / GGUF / llama / flags in the row | not changed by the fix: the row says so; the run manifest records `harness_commit a3fedbb…`, `manager_gguf_sha256 509287f7…`, `llama_build 620d2225…`; the 9 Nov `s04` manifest recorded the same harness/GGUF/llama with only `paper_commit d10b05b7` different |
| Fix diff content | `StaleProposalError` only wraps the view's own proposal in `replay`; `forecast` turns it into `None` + `forecast_reason`; `_e2_detail` returns "not eligible" when `delta_hat is None` **before** any forecast. Consistent with the review record. |

**Acceptance claim re-derived:** the review record accepts the code at `8237fd02` (round 2) and the
docs-only `fe651e58` (round 3); the tip is docs-only on top. The report's "review accepted" is therefore
correct in substance; its "rounds 1–3 accepted" wording is imprecise (MINOR 1).

### 2.2 Precondition test (c) on TASL-2 — **PASS (5 passed, 0 skipped)**

The old S0.4 run work roots are read-only on the host: `$R/scratch/digits_mlp/s04/roots/` is the run
tree's work dir. I re-hashed the five committed-root ledgers directly on the host and compared them with
the precondition captures, the check report table and the PLAN row:

| root | host `root_trials.jsonl` sha256 | mtime |
|---|---|---|
| `tracks_S04_digits_mlp__s30001` | `14d586ee58f6613c173c2fbe46a09337e13fcacb5ce1c9bd7bfe469dc88e41` | 2026-11-08 |
| `tracks_S04_digits_mlp__s30004` | `a8dbbd980d3eff068a799758bf678d570749e2799c30c305fa11a38a2c9ee4d7` | 2026-11-08 |
| `tracks_S04_digits_mlp__s30006` | `cf3843528141fd6a3080ff1f9cb97c700b223329cfe5970b49550105dc3508b1` | 2026-11-08 |
| `tracks_S04_digits_mlp__s30007` | `8ea9e20b34a6f1c1855a744e4f626dc0a575ad5002336d3a959d47389d013896` | 2026-11-08 |
| `tracks_S04_digits_mlp__s30009` | `71c358c63165aeea4a8795f314a97cd42137e9cc4409d786acd8cda2fe11907c` | 2026-11-08 |

- **Both captures are on the host and match the copies.** `/tmp/trks_a2u_precondition_20261111.log`
  (sha256 `22775d9bcc99425989e2011b07a18bfdf9ee8e5373f50822fc49f92c80ec9276`, mtime **22:25Z**, before the
  23:14:11Z launch) and `/tmp/trks_a2u_precondition_operator_20261112.log` (sha256
  `49fefcd3ef10de9564f70cc9b98f9dac93733178a695a2c16ee075b8d9545d27`, mtime **00:04Z**, the completion
  phase's re-run) both print `collected 17 / 12 deselected / 5 selected`, the five `40 trials identical`
  lines with the hashes above, and `5 passed, 12 deselected` with **no SKIPPED line**.
- The test file's `_s04_ledgers()` fails (collection error) when `TRACKS_S04_ROOTS` is set and a ledger is
  missing, so the `skipif` cannot turn a wrong path into a "pass" (verified in `8237fd02`'s test file).
- **Environment.** The capture records `rootdir: /home/dowling/r1_tracks/work/Agent_paper_B` (the pinned
  checkout, `HEAD 8237fd02` in the earlier capture's header), and the earlier capture records
  `SCRATCH=/tmp/trks_pytest_20261111.FI7Fdoi8`, `PRECOND_EXIT=0`, `checkout status after: []`. The scratch
  `--target` dir exists (`pytest 9.2.0`, `pluggy 1.7.0`) and resolves pytest there when put on
  `PYTHONPATH`; the frozen venv was **not modified** (`site-packages/`, `pytest/__init__.py` mtime
  2026-10-29). **Caveat:** the earlier capture's header line prints
  `pytest from scratch: 9.2.0 /home/dowling/r1_tracks/venv/lib/python3.11/site-packages/pytest/__init__.py`
  (the frozen-venv path), and the completion-phase capture has no environment header at all; the "pytest
  from a separate scratch target" claim is therefore not fully evidenced by the captures (MINOR 3).
- **Old scene read-only:** no file under `$R/out/digits_mlp/s04/` or `$R/scratch/digits_mlp/s04/` is newer
  than 2026-11-09 00:00; the five ledgers keep their 2026-11-08 mtimes and hashes; nothing was deleted.

### 2.3 Pin move and the run's provenance

- `$R/work/Agent_paper_B`: HEAD **`8237fd02…`**, detached, `git status --porcelain` **empty** (only
  gitignored `r1/tracks/__pycache__/a2u.cpython-311.pyc`, written by the run at 23:14:13Z).
- `$R/work/autoresearch_harness`: HEAD **`a3fedbb…`**, clean. `$R/opt/llama.cpp`: HEAD **`620d2225…`**,
  clean. GGUF sha256 **`509287f7…`**. `llama-server --version`: `0.7.0-dev (build 11669, commit 620d2225c)`.
- `bin/trks-status` (host sha256 **`70fbe8bd312fd7aad3a9020b80dcf9284453a8319dbb2cb523e9f6c06f16cc5f`**, equal
  to the committed `r1/tracks/ops/trks-status` at the tip) has `PAPER_SHA=8237fd02…` and prints
  `OK paper 8237fd02…`, `OK harness a3fedbb…`, `OK llama.cpp 620d2225…`, GGUF `OK`.
- `bin/trks-run` `b53bc811…`, `bin/trks-servers` `124316b5…`, `bin/trks-watch` `cf68843e…` equal the
  committed `r1/tracks/ops/*`; `bin/trks` equals the committed file modulo the two fill-ins
  (`HOST_LABEL=TASL-2`, `GPU_ID=GPU-4d623e76-7587-ee15-a633-46f60d220d94`;
  `9fcd227c…` + fill-ins = host `dca17a7d…`). The server flags in `trks-servers`
  (`-ngl 999 -c 8192 --parallel 1 --verbose --alias r1-manager --host 127.0.0.1 --port 1810<i>`) are the
  rev-3.3 §0.2 flags, unchanged since 31 Oct.
- New run manifest (`manifest.json`, sha256 `24c4d70f…`): `sessions[0].provenance` = `paper_commit
  8237fd02…`, `harness_commit a3fedbb…`, `manager_gguf_sha256 509287f7…`, `llama_build 620d2225…`,
  `host TASL-2`, `gpu GPU-4d623e76-…`, `harness_dirty false`, `paper_dirty false`; `server_url
  http://127.0.0.1:18101/v1`. Old → new paper pin: **`d10b05b7` → `8237fd02`**; no other pin changed.

### 2.4 The rerun (new directories, all ten instances)

- New dirs only: `$R/out/digits_mlp/s04_r2_20261111/` (8 files: manifest, roots, s04_rows, audit_runs,
  liveness/{4}) and `$R/scratch/digits_mlp/s04_r2_20261111/` (roots/, audit_tmp/, root_meta/). No
  `failed_units.jsonl`, no `failures/`, no STOP.
- Launch: committed script `r1/tracks/ops/launch/tasl2_s04r2_20261111.sh` in **`3899b8ac`**
  (committed `2026-11-12T00:12:54+01:00` = **23:12:54Z**); host copy
  `$R/launch/tasl2_s04r2_20261111.sh` sha256 **`9ac5d584d35eed402bba2e39c913ff62d594bb2cf5b78cdf4731d80768cf8b60`**
  = the committed blob, mtime 23:12Z. Launch log `$R/logs/s04_r2_20261111_launch.log` (sha256
  `22451b2e…`): start **23:14:11Z**, fresh k = 1 server in `trks_llm`, pid **3284858**, `/v1/models` ready
  **23:14:13Z**, lease **HELD**, collector started **23:14:13Z**.
- Session `trks_s04r2`: `.exit` `23:58:32Z rc=0` (26 bytes, sha256 `772ab3bb…`); `.log` sha256
  `a1683d0a…`, final line the done block; `.cmd` sha256 `dfc0513c…` (the exact rev-3.3 Phase 3 command:
  `--phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY --deadline 28800 --stop-file
  …/s04_r2_20261111/STOP --out …/s04_r2_20261111 --work …/s04_r2_20261111`). Duration 44 m 19 s.
- Manifest `done` = `{roots: 10, forks: 0, leaves: 0, failed: 0, exhausted: 0, deadline_hit: false,
  status: "complete"}`; `audit_runs: 925` (the file has 925 lines, seeds 100000…100184). `roots.jsonl`
  10 lines, all `status: ok`, root ids `…s30000`…`…s30009`, **no duplicate `root_id`**; each
  `root_trials.jsonl` has 40 trials (10 × 40 = 400). `s04_rows.jsonl` **165 rows**, 165 unique
  `(instance, budget_index)` pairs (budget_index 2–40), one kind (`local`), k = 5 seeds per row.
- **Dry run** (new session `trks_s04r2_dry`, `00:04:49Z rc=0`): output
  `{"roots_todo": 0, "forks_known": 0, "leaves_todo": 0, "exhausted": 0}` for the new work dir → phase
  finished. **2 % rule:** `0 / (10 + 0 + 0) = 0.0 % ≤ 2 %` (old STOP scene was 3/8 = 37.5 %).
  See MINOR 4 for a second, unrecorded dry run at `00:15:51Z` on the host.

### 2.5 `liveness` and `fit_prior`

- **Recomputed liveness from the host ledgers** with the pinned `r1.liveness.check.evaluate_ledger_paths`
  (read-only, `PYTHONDONTWRITEBYTECODE=1`): `n_trials 400`, evaluated 200, novel 175,
  equals_incumbent 25, seen_before 25, `active_novelty_fraction 0.875` (≥ 0.5), `invalid_rate 0.0625`
  (25/400, < 0.3), `keep_after_trial_1 75` (≥ 1), inactive-key rejections 0, `pass: true`. Identical to
  the committed `liveness/digits_mlp.json` (sha256 `4e42fb6f…`) and the capture
  `/tmp/s04r2_liveness_20261112.log` (sha256 `aa9114b9…`); `{"liveness": {"digits_mlp": "PASS"}}`.
- **Prior** `$R/out/digits_mlp/a2u_prior_r2_20261111.json` sha256 **`5c849d15…`** = the committed copy.
  `schema tracks_a2u_prior/v2`, `sigma_node 0.0066`, `meta.obs_inflation 1.0`, local
  `mu0 = -0.0011366264955253653`, `tau0 = 0.00099`, `sigma_cmp = 0.018622507203902326`,
  `tau_w = 0.04928522081289578`; stats `rows 165`, `instances 10`, `mean_se2 5.727122162581814e-05`,
  `mu_a2`/`mu0`, `tau_a2 0.01897268940471418`; `meta.sources.s04_rows_sha256 =
  d0f7dae7…` = the run's `s04_rows.jsonl` (sha256 `d0f7dae7d5b892e01e41423d21e6b6e2be6e7fa77cc0a2dc4774c561daa1015f`).
  I recomputed the prior from the run's `s04_rows.jsonl` with the pinned `r1.tracks.a2u.fit_prior`
  (k_label 5, within_key estimated, sigma 0.0066): **identical values and stats**.
- Fit_prior capture `/tmp/s04r2_fitprior_20261112.log` sha256 `017ac677…` = the committed copy; the
  command line in the report (`--sigma-node 0.0066 --obs-inflation 1.0 --prior
  $OUT/a2u_prior_r2_20261111.json`) resolves to the host path above with `OUT=$R/out/digits_mlp`
  (runbook §0.1).

### 2.6 Old `s04` STOP scene preserved

| old host file (`$R/out/digits_mlp/s04/`) | sha256 | mtime |
|---|---|---|
| `manifest.json` | `13d6afb99f99b2b44ce09edbf46e14cdbf23534830688503f8650d59fd24456f` | 2026-11-08 |
| `roots.jsonl` | `22c5c936ffa996ee37c5cb3f6d66a87bbe33f2d2f626b758ed03e77e9b5e3874` | 2026-11-08 |
| `s04_rows.jsonl` | `2341f3a08bd540bd2e52c577b824409a30c45701d61e09dd18d532301a56853f` | 2026-11-08 |
| `failed_units.jsonl` | `f7072d02af5168860ee25e200d1f4376a8346b1b7259bed1e8afe5045a227469` | 2026-11-08 |
| `audit_runs.jsonl` | `d9a4a409bcbc7e116ba6578557ea77926414fc6a8b0b5291baa4d9d89a657352` | 2026-11-08 |

`failures/` still has its 13 files. Under `$R/scratch/digits_mlp/s04/` the 10 root dirs and
`root_meta/`/`audit_tmp/` are present, nothing is newer than 2026-11-09 00:00, and the five committed
ledgers keep their 2026-11-08 mtimes. The Mac copy `results/r1/tracks/digits_mlp/s04/` is byte-identical
to the host (same five hashes; `SHA256SUMS` verifies), has not been touched since `ced1e209` and keeps its
9 Nov mtimes. Nothing was deleted.

### 2.7 Host end state (read-only, 00:16Z)

`tmux ls`: only **`trks_watch`** (created 8 Nov). Lease: `flock -n ~/r1_locks/gpu0.lock true` **succeeds**
(free); only `gpu0.lock` in `~/r1_locks`, no `*.active` and no `$R/trks_drill.active`. No GPU compute app;
no listener on 18101/18102; no `llama-server` process (the only `pgrep` hit was the SSH command string
itself). **0** STOP files under `$R/out`; `watch.log` sha256 `2e74bc69…`, 6 lines (unchanged); disk
**187 G free, 90 % used**. Paper checkout `8237fd02` clean, harness `a3fedbb`; `trks-status` all OK.

### 2.8 Delivery and pushes

- `origin/trackS-ops-20261030` and the TASL-2 bare repo ref both = **`cac84270…`** (local tip = origin
  remote-tracking = `git ls-remote origin`); fix branch = **`c8b13b5d…`** on `origin`, in the TASL-2 bare
  repo, and in `tasl2` remote-tracking; the pin object `8237fd02` is present in the bare repo.
- Commit `cac84270` touches exactly the report (200 lines), the STATUS entry (11 lines),
  `r1/tracks/ops/trks-status` (PAPER_SHA line), and the copy-back (22 files: 21 hashed + `SHA256SUMS`);
  one deletion is the old
  PAPER_SHA line. Working tree clean at review start. Pushes are consistent with normal fast-forwards
  (linear history; no evidence of a rewrite); I cannot prove retroactively that force was never used.
- `SHA256SUMS` verifies **21/21** on the Mac. Host-vs-copy: **19/21** match; the two exceptions are
  `host_logs/trks_s04r2_dry.exit` and `host_logs/trks_s04r2_dry.log` (MINOR 4).

### 2.9 Provenance / transparency

- The launch log puts the start at **23:14:11Z**; `3899b8ac` (the pin + launch-script commit) is
  **23:12:54Z** and the **parent** of `cac84270`; the host script's mtime (23:12Z) and sha256 match the
  committed blob. The run ended **23:58:32Z**; the completion phase's captures are
  **00:04:24Z** (precondition re-run), **00:04:49Z** (dry run), **00:04:59Z** (liveness / fit_prior), and
  its commit is **00:06:51Z**. `manifest.sessions` has exactly **one** session, and there is one launch
  log, one collector log and one set of run dirs: **no duplicate run**.
- The attribution "launched by the immediately preceding operator phase of this same task" is consistent
  with the ordering and with the commit split (the report is written, and the dry run/liveness/fit_prior
  are run, after the run completed), but no artifact carries an agent-session id that ties the launch to
  a distinct operator phase. This is a documentation/attribution point, not a defect in the run (MINOR 5).

### 2.10 3.0 pause drill and scope containment

- **Drill not repeated — acceptable.** Runbook §3.0 says "Exercise it **once per host**"; the drill passed
  on TASL-2 on 9 Nov with the record accepted at STOP 3 (the STOP-3 review's §2.4 and its checklist).
  The pause path is in `trks-watch` (`cf68843e…`, unchanged since 31 Oct), `trks-servers` (`124316b5…`,
  unchanged since 31 Oct) and `trks-run` (`b53bc811…`); the collector detection is
  `pgrep -f 'python -m r1\.tracks\.collect .*--stop-file'` (name-independent), and the fix diff touches
  only `r1/tracks/a2u.py` + a test. Re-exercising it now would also **write** a STOP file into
  `$R/out/digits_mlp/s04/` (the watcher touches a STOP in every dir under `$R/out` with a `manifest.json`;
  the three are `s04`, `s04_r2_20261111`, `smoke`), i.e. it would touch the preserved old scene. The
  report's rationale is right but states "the Lead's instruction" as its authority; the runbook basis
  (once per host + unchanged watcher/server) should be cited (MINOR 5).
- **Scope:** no Phase 4 (`out/digits_mlp` has no `s05*`; the commit has no S0.5 file), no Track P marker
  or work, no B1 change, and no TASL-7 contact in the artifacts (I did not contact TASL-7). The author's
  STOP-3 option (a) and the PLAN row's "Phase 4 is not authorised" are respected.

## 3. Findings

No **BLOCKING** and no **MAJOR** finding. Five **MINOR** items, all documentation/evidence hygiene; none
affects the run, the counts, the 2 % result, liveness, the prior or the old scene. The operator should
answer/fix them in the follow-up commit (or state that a follow-up commit is not needed, with reasons).

### MINOR 1 — Fix-delivery wording: the diff arithmetic and the review-round summary are imprecise.

**Location.** Report §1 and the STATUS entry: "diff … only `r1/tracks/a2u.py` (+45/−8) and the new
test file (+302)"; "review … rounds 1–3 accepted".
**What I verified.** `git diff --numstat d10b05b7 8237fd02` is **`37 8` for `a2u.py`** (45 = lines
changed = 37 additions + 8 deletions) and **`302 0`** for the test. The review record's round 1 is
"VERDICT: changes requested"; rounds 2 and 3 are "VERDICT: accepted"/"Verdict: accepted", and the
"Accepted commit: `fe651e58…`" line is round 3's.
**Required fix/answer.** Write **+37/−8** (or "45 changed lines") and say "reviewed over three rounds;
accepted at round 2 (`8237fd02`) and round 3 (`fe651e58`), tip `c8b13b5d` docs-only".

### MINOR 2 — The report's old-scene wording contradicts the precondition read.

**Location.** Report §4: "The old `$OUT/digits_mlp/s04` and `$WORK/digits_mlp/s04` were neither read nor
written (§7)"; STATUS (11 Nov) "the old `s04` STOP scene is not read or written".
**What I verified.** The rerun collector used only the new dirs (true), **but the precondition test (c)
deliberately reads the old `$R/scratch/digits_mlp/s04/roots`** (§2 of the report and the host captures),
read-only. Saying "neither read nor written" is false for the work tree and contradicts §2.
**Required fix/answer.** Say: "the rerun collector read/wrote only the new dirs; the precondition test
read the old `$WORK/s04/roots` read-only (hashes and 2026-11-08 mtimes unchanged; nothing written or
deleted)."

### MINOR 3 — The capture does not evidence the "pytest from the scratch --target dir" detail.

**Location.** Report §2 (and STATUS): "pytest from the scratch target `/tmp/trks_pytest_20261111.FI7Fdoi8`
(the frozen venv was not modified)"; the captures are
`host_logs/trks_a2u_precondition_20261111.log` (`22775d9b…`) and
`host_logs/trks_a2u_precondition_operator_20261112.log` (`49fefcd3…`).
**What I verified.** The scratch `--target` dir exists and holds pytest 9.2.0/pluggy 1.7.0; with
`PYTHONPATH=/tmp/trks_pytest_20261111.FI7Fdoi8` the frozen interpreter imports pytest from `/tmp`
(without it, from the frozen venv). The frozen venv is **provably unmodified** (site-packages and
`pytest/__init__.py` mtime 2026-10-29). But the earlier capture's header prints
`pytest from scratch: 9.2.0 /home/dowling/r1_tracks/venv/lib/python3.11/site-packages/pytest/__init__.py`,
i.e. the frozen-venv pytest path, and the completion-phase capture has no environment header
(SCRATCH/PWD/HEAD/PYTHONPATH/exit/checkout). The result itself is unaffected (same pytest 9.2.0, same
tests, venv untouched).
**Required answer.** Give the exact invocation/environment used (with
`PYTHONPATH=/tmp/trks_pytest_20261111.FI7Fdoi8` if that is what it was) and explain the venv path in the
earlier header, or re-capture with the environment printed. If the frozen venv's own pytest was used,
say so: the venv already had pytest 9.2.0 installed on 2026-10-29, so "nothing was installed into the
frozen venv" still holds, but "from a separate scratch target" would then have to be corrected in the
report/STATUS.

### MINOR 4 — The copy-back is one dry run behind the host: 2 of 21 files no longer match.

**Location.** `results/r1/tracks/digits_mlp/s04_rerun20261111/host_logs/trks_s04r2_dry.exit` and
`trks_s04r2_dry.log`, report §9 "host and Mac identical", STATUS "host==copy hashes".
**What I found.** The committed copy is the `00:04:49Z` dry run (`dry.exit` 26 bytes, sha256
`28c4a358…`; `dry.log` 1223 bytes, sha256 `5daef59c…`; `dry.cmd` `2893d4bd…`, unchanged). Since the
copy-back, a **second dry run at `2026-11-12T00:15:51Z`** appended to the host files:
`/home/dowling/r1_tracks/logs/trks_s04r2_dry.exit` is now **52 bytes** with two lines
(`…00:04:49Z rc=0`, `…00:15:51Z rc=0`, sha256 `aa3b55ab…`), and `trks_s04r2_dry.log` is **2446 bytes**
with two identical JSON lines (sha256 `4fc0d6b5…`). So 19/21 copy-back hashes match the host; the two
dry-run logs differ, and the second run is not mentioned in the report.
**Effect.** None on the result: the second run's output is byte-identical to the first
(`roots_todo 0 / forks_known 0 / leaves_todo 0 / exhausted 0`, rc = 0), so the completion check stands.
But the committed evidence and the "host==copy" statement are stale, and the second run's origin is not
recorded.
**Required fix/answer.** Either copy back the current `trks_s04r2_dry.*` files and refresh `SHA256SUMS`
(and note the second run in the report), or state explicitly that the committed copy is the
`00:04:49Z` run and that a later re-run (record what/who; e.g. a verification by the Lead) produced the
host's second line. Until then the report/STATUS should not claim all 21 host==copy hashes.

### MINOR 5 — Provenance/attribution wording and the authority quoted for the drill.

**Location.** Report §1/§4 ("launched by the immediately preceding operator phase of this same task"),
§8 ("as authorised by the Lead's instruction"), and the PLAN row location.
**What I verified.** Everything observable is consistent: the launch log says 23:14:11Z; `3899b8ac` is
23:12:54Z and is the parent of the report commit; the host launch script matches the committed blob; the
run ended 23:58:32Z; the completion phase's dry run/liveness/fit_prior are at 00:04:49–00:04:59Z; the
manifest has one session and there is no duplicate run. But no artifact carries the agent-session id of
the launcher, so "immediately preceding operator phase" is an attribution the artifacts support only by
ordering. Likewise, the drill non-repetition rests on runbook §3.0 ("once per host") and the unchanged
watcher/server path; "the Lead's instruction" is not in a committed artifact. The PLAN row
R1-TRACKS-A2U-STALE is on the fix branch (and origin/tasl2) but **not** in the operator branch's
`docs/r1/PLAN.md`.
**Required answer.** State the observable chain (times/commits/sha) and, if available, the session
record, rather than the phase attribution alone; cite runbook §3.0 (+ the unchanged `trks-watch` /
`trks-servers` / `trks-run` shas and the 9 Nov pass) as the basis for not repeating the drill, with the
Lead's instruction as a relayed corroboration; say where the PLAN row lives (fix branch `f82ff376`,
also at the tip/remotes), or update the canonical PLAN in a follow-up docs commit.

## 4. Acceptance checklist

| Requirement (runbook §0.5–§0.8, Phase 3; STOP-3 option (a); PLAN row) | Status | Evidence |
|---|---|---|
| Fix branch tip `c8b13b5d` on origin + TASL-2 bare; review record accepted (rounds 2–3; final `fe651e58`); pin `8237fd02` named in the PLAN row and an ancestor of the tip; fix diff only `a2u.py` + new test; harness/GGUF/llama/flags unchanged | **PASS** | §2.1, §2.3 |
| Precondition (c): pinned checkout, harness `a3fedbb`, 5 passed / 0 skipped, five SHA-256 match the report/PLAN; old work roots read-only (hashes/mtimes unchanged) | **PASS** (MINOR 3 on the scratch-pytest capture) | §2.2 |
| Pin move `d10b05b7 → 8237fd02`; detached clean; `trks-status` PAPER_SHA host + repo; manifest provenance new pin, clean | **PASS** | §2.3 |
| Rerun in new dirs; launch script committed before use; k = 1 fresh server pid 3284858 + readiness; session `trks_s04r2` 23:14:13Z→23:58:32Z rc=0 complete; roots 10, failed 0, exhausted 0; 925 audits; 165 `s04_rows`, no duplicate root/`(instance,budget_index)`; dry run 0/0/0; 2 % = 0.0 % | **PASS** (MINOR 4 on the stale dry-run copy) | §2.4 |
| liveness PASS with the stated numbers; fit_prior sha256 and parameters; `s04_rows_sha256` matches | **PASS** | §2.5 |
| Old `s04` scene untouched (host + Mac mtimes/sha; no deletion; nothing under old `$WORK/s04` modified) | **PASS** | §2.6 |
| Host end state clean (only `trks_watch`, lease free, no compute/listener/llama-server, no markers/STOP, disk) | **PASS** | §2.7 |
| Delivery: tip `cac84270` in origin + TASL-2 bare; worktree clean; report + STATUS + copy-back; `SHA256SUMS` verifies 21/21 locally; host==copy | **PASS on 19/21**, MINOR 4 on the two dry-run logs | §2.8 |
| Provenance chain complete and correctly attributed; no duplicate run | **PASS in substance**, MINOR 5 on the attribution wording | §2.9 |
| 3.0 pause drill non-repetition acceptable | **PASS** (runbook "once per host"; unchanged watcher/server; 9 Nov pass) | §2.10 |
| No Phase 4; no TASL-7 contact; no Track P; no B1 | **PASS** | §2.10 |

## 5. Verdict

The A2-U fix is delivered and accepted as pin `8237fd02` (code identical at the tip; review accepted at
rounds 2–3; the PLAN row binds it; harness/GGUF/llama/flags unchanged), the TASL-2 precondition test (c)
ran read-only against the old work roots with **5 passed, 0 skipped** and the five ledger SHA-256 values
matching the report/PLAN, the pin moved `d10b05b7 → 8237fd02` in the manifest and `trks-status`, and the
rerun completed in the new directories with **10/10 roots, 0 failed, 0 exhausted, 925 audit runs,
165 `s04_rows` (no duplicates), dry run 0/0/0 and 2 % = 0.0 %**. `liveness` **PASS** reproduces exactly
from the run ledgers (400 trials; novelty 0.875; invalid 0.0625; keep-after-1 75), the prior
`a2u_prior_r2_20261111.json` (sha256 `5c849d15…`) reproduces from the run's `s04_rows` and its
`s04_rows_sha256` matches, the old `s04` scene is preserved with unchanged hashes/mtimes and no deletion,
the host is left clean, the commits are pushed to both remotes with the worktree clean, and the scope
stays inside STOP 3 option (a): no Phase 4, no TASL-7, no Track P, no B1. The 3.0 drill need not be
re-exercised for this rerun. The five MINOR items are documentary/evidence hygiene (diff arithmetic and
round wording; "read nor written"; the scratch-pytest capture; the two dry-run files that a post-commit
re-run made stale; provenance/drill authority wording) and do not affect any count, hash, result or the
acceptance basis; the operator should answer/fix them in the follow-up commit.

MINOR items to answer: 5.

Verdict: accepted
