# Track S — S0.4 rerun at the A2-U pin on TASL-2 (`digits_mlp`), 11–12 November 2026 — **STOP 3 rerun**

**Written 12 Nov 2026 by the Track S operator agent (DSH experiment-agent session, Lead: experiment agent);
AI-assisted. ENGINEERING_ONLY.** Not a result. This closes the S0.4 STOP of 9 Nov under the author's STOP-3
option (a): the rerun is complete (10/10 roots, 0 failed), `liveness` passes and the A2-U prior is recorded;
**the phase is submitted for an independent review and Phase 4 is not started.**

**Authority.** Operator runbook O3; Track S operator runbook rev 3.3 (`13badb0`, sha256 `a93fb84b…`) Phase 3;
the author's STOP-3 ruling **option (a)**, verbatim: "Track S STOP 3：选 (a)。等 Mac agent 的 A2-U 修复审查通过、
新 pin 和 PLAN 行提交后，在新目录跑 S0.4，10 个 instance 全部重跑，然后接 liveness 和 fit_prior。旧的 s04
STOP 现场不动。" (recorded in `docs/r1/reports/TRACKS_PHASE3_20261109.md` §11); PLAN §10 row
**R1-TRACKS-A2U-STALE** (11 Nov), which moves the Track S paper pin and defines the precondition below.

**Pins.** paper **`8237fd02b09ef2d28016a1c9f6acac3c35bb768b`** (new; was `d10b05b7`), harness
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (unchanged), llama.cpp
`620d2225cc436ab0b001e3200e590e3b286ef9ab` (unchanged, `v0.7.0-dev` build 11669), GGUF sha256
`509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` (unchanged), server flags per rev 3.3
§0.2 (unchanged), **k = 1** (port 18101). The run manifest records `paper_commit = 8237fd02…`,
`harness_commit = a3fedbb…`, GGUF/build, `host=TASL-2`, `gpu=GPU-4d623e76-…`, `paper_dirty=false`,
`harness_dirty=false`.

## 1. Fix delivery verified (before use)

- Branch `origin/mac-tracks-a2u-stale-20261111` tip **`c8b13b5d63d3d30f5afa642928f1458e863e8935`**; accepted
  fix commit **`fe651e589c2d6bafafc3a27e8eb7d8599845a7df`**; independent review
  `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md` — reviewed over three rounds: **round 1 changes
  requested; accepted at round 2 (`8237fd02`) and round 3 (`fe651e58`)**; tip `c8b13b5d` is docs-only.
- **PLAN §10 row `R1-TRACKS-A2U-STALE` (11 Nov)** names the new pin `8237fd02…`; the pin is an **ancestor** of
  the branch tip; the fix diff from `d10b05b7` is **only** `r1/tracks/a2u.py` (**+37/−8**, i.e. 45 changed lines) and the new
  `r1/tests/test_tracks_a2u_stale.py` (+302). Harness pin `a3fedbb`, GGUF, llama build and flags are unchanged
  by the row.
- The branch was pushed to the **TASL-2 bare repo** (`$R/remotes/Agent_paper_B.git`), which now has
  `mac-tracks-a2u-stale-20261111 = c8b13b5d` and the pin object `8237fd02` (verified on the host). The push
  reported "Everything up-to-date": the branch had already been delivered to the bare repo by the preceding
  phase — no change was needed.
- **Observable chain for the S0.4 rerun.** The launch script was committed at `2026-11-11T23:12:54Z` (commit
  `3899b8ac`, `tasl2_s04r2_20261111.sh`, blob `9ac5d584…`); the host launch log starts the fresh server and
  collector at `23:14:11Z`; the collector ends `23:58:32Z`; this completion phase's dry run / `liveness` /
  `fit_prior` are at `00:04:49Z`–`00:04:59Z`; the manifest has exactly one session and there is no duplicate run.
  So the rerun was launched by a **prior operator phase of the same branch/worktree** — an attribution the
  artifacts support by ordering only (the launcher's agent-session id is not recorded in any committed
  artifact). This phase independently re-verified the precondition and the pin checkout, then ran the dry run,
  `liveness`, `fit_prior`, stopped the server, and copied back. No second S0.4 run was started.
- **PLAN row location.** `R1-TRACKS-A2U-STALE` is commit `f82ff376` on the fix branch
  `mac-tracks-a2u-stale-20261111` (also present at the branch tip `c8b13b5d` and in `origin` / the TASL-2 bare
  repo); it is **not** in the operator branch's `docs/r1/PLAN.md`. The canonical PLAN was not edited here.

## 2. Precondition test (c) on TASL-2 — **PASS (5 passed, 0 skipped)**

Run at the pinned checkout `$R/work/Agent_paper_B` (HEAD `8237fd02…`, `git status --porcelain` empty),
`AR_HARNESS_ROOT=$R/work/autoresearch_harness` (harness `a3fedbb`), pytest from the scratch target
`/tmp/trks_pytest_20261111.FI7Fdoi8` (the frozen venv was not modified), read-only on the old run tree:

```
TRACKS_S04_ROOTS=$R/scratch/digits_mlp/s04/roots PYTHONDONTWRITEBYTECODE=1 \
  AR_HARNESS_ROOT=$R/work/autoresearch_harness PYTHONPATH=/tmp/trks_pytest_20261111.FI7Fdoi8 \
  $R/venv/bin/python -m pytest -rs -s -p no:cacheprovider \
  r1/tests/test_tracks_a2u_stale.py -k s04_committed_roots
```

Verbatim result (captured in `host_logs/trks_a2u_precondition_operator_20261112.log`, sha256
`49fefcd3ef10de9564f70cc9b98f9dac93733178a695a2c16ee075b8d9545d27`; exit 0; checkout clean before/after):

```
============================= test session starts ==============================
platform linux -- Python 3.11.17, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/dowling/r1_tracks/work/Agent_paper_B
configfile: pyproject.toml
plugins: anyio-4.15.1, langsmith-0.14.16
collected 17 items / 12 deselected / 5 selected

r1/tests/test_tracks_a2u_stale.py tracks_S04_digits_mlp__s30001: 40 trials identical; ledger sha256 14d586ee58f6613c173c2fbe46a09337e13fcacb5ce1c9bd7bfe469dc88e41
.tracks_S04_digits_mlp__s30004: 40 trials identical; ledger sha256 a8dbbd980d3eff068a799758bf678d570749e2799c30c305fa11a38a2c9ee4d7
.tracks_S04_digits_mlp__s30006: 40 trials identical; ledger sha256 cf3843528141fd6a3080ff1f9cb97c700b223329cfe5970b49550105dc3508b1
.tracks_S04_digits_mlp__s30007: 40 trials identical; ledger sha256 8ea9e20b34a6f1c1855a744e4f626dc0a575ad5002336d3a959d47389d013896
.tracks_S04_digits_mlp__s30009: 40 trials identical; ledger sha256 71c358c63165aeea4a8795f314a97cd42137e9cc4409d786acd8cda2fe11907c
.

======================= 5 passed, 12 deselected in 1.92s =======================
```

**Environment, exactly (reviewer MINOR 3).** The invocation above is exact: `PYTHON=/home/dowling/r1_tracks/venv/bin/python`
(Python 3.11.17), `PYTHONPATH=/tmp/trks_pytest_20261111.FI7Fdoi8`,
`AR_HARNESS_ROOT=/home/dowling/r1_tracks/work/autoresearch_harness`,
`TRACKS_S04_ROOTS=/home/dowling/r1_tracks/scratch/digits_mlp/s04/roots`, `PYTHONDONTWRITEBYTECODE=1`,
`-p no:cacheprovider`. With that `PYTHONPATH` the frozen interpreter imports **pytest 9.2.0 from
`/tmp/trks_pytest_20261111.FI7Fdoi8/pytest/__init__.py`** (and pluggy 1.7.0 from `/tmp/…/pluggy/__init__.py`), i.e.
the **scratch `--target` environment**, not the frozen venv. A re-capture with the environment printed is in
`host_logs/trks_a2u_precondition_header_20261112.log` (sha256
`3322b55f706ae4a5b1e257676e37881c08ac6946b54d1141fe948bbb24c99438`): it shows
`pytest_under_env=9.2.0 /tmp/trks_pytest_20261111.FI7Fdoi8/pytest/__init__.py`, `checkout_before=[]`,
`PRECOND_EXIT=0`, `checkout_after=[]`. The earlier phase's header line printed the frozen-venv pytest path
because that header's `python -c` was evaluated **without** `PYTHONPATH`; it is not the environment of the test
invocation. The frozen venv is provably unmodified (`site-packages/pytest/__init__.py` mtime 2026-10-29; no
install was run into it).

All five SHA-256 values **match exactly** the list in the PLAN row / the preceding phase's record
(`14d586ee…`, `a8dbbd98…`, `cf384352…`, `8ea9e20b…`, `71c358c6…`). The preceding phase's own run
(`host_logs/trks_a2u_precondition_20261111.log`, sha256 `22775d9b…`, run at 22:25Z before the rerun) shows
the same 5 values, so the gate was satisfied **before** the rerun, and re-verified in this phase. No failure,
skip, collection error or hash difference; the old scene was read-only throughout.

## 3. Pin checkout and local pin strings

- `$R/work/Agent_paper_B` was already at **`8237fd02…` detached** with `git status --porcelain` empty when
  this phase began (verified by `git rev-parse HEAD` and `git status`); the harness checkout stayed
  `a3fedbb` clean, llama.cpp `620d2225` clean, GGUF sha256 the pin.
- `bin/trks-status` **PAPER_SHA** was updated from `d10b05b7…` to **`8237fd02…`** (host + committed
  `r1/tracks/ops/trks-status`); `trks-status` now prints `OK paper 8237fd02…`, `OK harness a3fedbb…`,
  `OK llama.cpp 620d2225…`, GGUF OK. No harness/GGUF/flag change. Old → new paper pin: **`d10b05b7` →
  `8237fd02`** (authority: PLAN row `R1-TRACKS-A2U-STALE`).

## 4. S0.4 rerun (new directories, all ten instances from the start)

- New output/work directories: `$OUT/digits_mlp/s04_r2_20261111`, `$WORK/digits_mlp/s04_r2_20261111`. The
  **rerun collector** read/wrote only the new dirs; the **precondition test (c) deliberately read the old
  `$WORK/digits_mlp/s04/roots` read-only** (hashes and 2026-11-08 mtimes unchanged; nothing written or
  deleted), and the old `$OUT/digits_mlp/s04` was not touched (§7).
- Committed launch script `r1/tracks/ops/launch/tasl2_s04r2_20261111.sh` (`3899b8ac`; new session
  `trks_s04r2`, new STOP/log names, resume-only guard), run as
  `ssh portal_zhixu bash $R/launch/tasl2_s04r2_20261111.sh`. Fresh `k = 1` server in `tmux trks_llm` (pid
  **3284858**, port 18101), bounded `/v1/models` readiness at **`23:14:13Z`** (2 s), lease **HELD**.
- Command (exact rev-3.3 Phase 3 S0.4 command, `--instances 10`):

```
trks-run trks_s04r2 18101 collect --phase S0.4 --node digits_mlp --instances 10 --label ENGINEERING_ONLY \
  --deadline 28800 --stop-file $OUT/digits_mlp/s04_r2_20261111/STOP \
  --out $OUT/digits_mlp/s04_r2_20261111 --work $WORK/digits_mlp/s04_r2_20261111
```

- Session: `trks_s04r2`, `2026-11-11T23:14:13Z` → `2026-11-11T23:58:32Z` (44 m 19 s), exit
  `rc=0`; final done block `{roots: 10, forks: 0, leaves: 0, failed: 0, exhausted: 0, deadline_hit: false,
  status: "complete"}`; 925 audit runs.
- Committed roots (all ten, no duplicates; no `failed_units.jsonl` was created):
  `s30000, s30001, s30002, s30003, s30004, s30005, s30006, s30007, s30008, s30009`;
  `roots.jsonl` 10 lines, `s04_rows.jsonl` **165 rows**, **0** duplicate `(instance, budget_index)`.
- **Completion check (dry run, new session `trks_s04r2_dry`, `00:04:49Z` rc=0):**
  `{"roots_todo": 0, "forks_known": 0, "leaves_todo": 0, "exhausted": 0}` — phase finished true. A **second dry
  run at `00:15:51Z`** (after this phase's copy-back; its origin process is not recorded in the artifacts)
  appended an identical second line to `$R/logs/trks_s04r2_dry.exit` (now `aa3b55ab…`: `…00:04:49Z rc=0` +
  `…00:15:51Z rc=0`) and a byte-identical second JSON line to `trks_s04r2_dry.log` (`4fc0d6b5…`), so the
  completion check stands; the copy-back and `SHA256SUMS` were refreshed to the host's two-line files.
- **2 % rule:** `exhausted / (committed roots + leaves + exhausted) = 0 / (10 + 0 + 0) = 0.0 % ≤ 2 %` — passes
  (contrast with the 9 Nov STOP scene: 3/8 = 37.5 %).

## 5. `liveness` and `fit_prior`

- **`liveness`** (`trks collect --phase liveness --node digits_mlp --out $OUT/s04_r2_20261111`, `00:04:59Z`):
  rc=0, `{"liveness": {"digits_mlp": "PASS"}}`, manager `langgraph`, memory `append_only_summary`. Node
  `digits_mlp` `pass=true`, `n_trials=400`: active-novelty fraction **0.875** (≥ 0.5), invalid rate **0.0625**
  (< 0.3), keep-after-trial-1 **75** (≥ 1); no failed criteria. Written to `liveness/` in the run tree.
- **`fit_prior`** (`trks collect --phase fit_prior --node digits_mlp --out $OUT/s04_r2_20261111
  --sigma-node 0.0066 --obs-inflation 1.0 --prior $OUT/a2u_prior_r2_20261111.json`, `00:04:59Z`): rc=0;
  prior **`a2u_prior_r2_20261111.json`**, **sha256 `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`**.
  `tracks_a2u_prior/v2`, `sigma_node=0.0066`, `obs_inflation=1.0`; local `mu0=-0.0011366265`,
  `tau0=0.00099`, `sigma_cmp=0.0186225072`, `tau_w=0.0492852208`; sources
  `s04_rows_sha256=d0f7dae7d5b892e01e41423d21e6b6e2be6e7fa77cc0a2dc4774c561daa1015f` (matches the run's
  `s04_rows.jsonl`).

## 6. Host end state (TASL-2, verified `2026-11-12T00:05:19Z`)

`trks_llm` stopped — the server (pid 3284858, started at `23:14:11Z` by the preceding phase of this rerun) was
stopped in this completion phase after the run; only `trks_watch` remains; lease **LOCK-FREE**; **no** GPU
compute app; **no** 18101/18102 listener; **no** llama-server; only `gpu0.lock` in `~/r1_locks` (no
priority/drill marker); **0** STOP files under `$R/out`; disk 187 G free, 90 % used; `watch.log` 6 lines
(unchanged). TASL-7 untouched; no Track P; no B1.

## 7. Old `s04` STOP scene preserved (untouched)

Host `$R/out/digits_mlp/s04/` and `$R/scratch/digits_mlp/s04/` have **unchanged mtimes (2026-11-08)** and
**unchanged sha256** (`manifest.json` `13d6afb9…`, `roots.jsonl` `22c5c936…`, `s04_rows.jsonl` `2341f3a0…`,
`failed_units.jsonl` `f7072d02…`, `audit_runs.jsonl` `d9a4a409…`). The rerun used only the new
`s04_r2_20261111` directories. The Mac copy-back of the STOP scene
(`results/r1/tracks/digits_mlp/s04/`) is also unchanged.

## 8. 3.0 pause drill — **not repeated** (decision recorded; flag for the reviewer)

The A2-U fix changes **only `r1/tracks/a2u.py`** (and adds a test); it does not touch the server, the watcher,
the launch scripts' server block, or the pause path. Basis: runbook **§3.0** says to exercise the pause drill **once per host** ("before any multi-day phase"); it
passed on TASL-2 on 9 Nov (`docs/r1/reports/TRACKS_PHASE3_20261109.md` §3); the watcher/server path is
byte-unchanged — `bin/trks-watch` `cf68843e…`, `bin/trks-servers` `124316b5…`, `bin/trks-run` `b53bc811…`
(identical in the repo and on the host), and `bin/trks-status` differs only in its `PAPER_SHA` string; the
A2-U fix changes only `r1/tracks/a2u.py`. Re-exercising the drill now would also touch a `STOP` into the
preserved old `$R/out/digits_mlp/s04` scene. The Lead's instruction not to repeat it is **relayed
corroboration**, not the primary basis. **Flagged for the reviewer:** if a re-exercise against the `trks_s04r2`
naming is wanted, it can be scheduled.

## 9. Evidence and hashes

Copied back: host `$OUT/digits_mlp/s04_r2_20261111/` → **`results/r1/tracks/digits_mlp/s04_rerun20261111/`**
(the Mac directory name follows the Lead's instruction; the host tree keeps the committed script's name
`s04_r2_20261111`), including `liveness/`, plus `a2u_prior_r2_20261111.json` and `host_logs/` (launch log,
`trks_s04r2.*`, `trks_s04r2_dry.*`, `watch.log`, both precondition logs, `liveness`/`fit_prior` capture logs).
`SHA256SUMS` verifies (**22 files**, refreshed after the second dry run; the two dry-run logs now match the
host's two-line files, `trks_s04r2_dry.exit` `aa3b55ab…` / `trks_s04r2_dry.log` `4fc0d6b5…`, and the
environment-header precondition capture `trks_a2u_precondition_header_20261112.log` `3322b55f…` was added). Key
hashes (host and Mac identical):

| file | sha256 |
|---|---|
| `roots.jsonl` | `5a7c6719cbc61de03dacc0e639db4319ec41194e8857020683f4ef6ac8fb5fa9` |
| `s04_rows.jsonl` | `d0f7dae7d5b892e01e41423d21e6b6e2be6e7fa77cc0a2dc4774c561daa1015f` |
| `audit_runs.jsonl` | `ff23b55e148b161baa047198f3f9634f19c8f5643a2d3584ba2f625e5adaf13a` |
| `manifest.json` | `24c4d70f2b31f8ee3b78cbc39dfe9b3b1167216925f4540cc2ef7d7aae767b01` |
| `liveness/digits_mlp.json` | `4e42fb6f80d993a8161143f5d827a8051fb1f675eaacc83ce1244959da7458bf` |
| `a2u_prior_r2_20261111.json` | `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607` |
| precondition capture | `49fefcd3ef10de9564f70cc9b98f9dac93733178a695a2c16ee075b8d9545d27` |

## 10. Reviewer checklist (STOP 3 rerun)

1. Fix delivery: branch tip `c8b13b5d`, fix `fe651e58`, review accepted (rounds 1–3), PLAN row
   `R1-TRACKS-A2U-STALE` names pin `8237fd02` (ancestor of tip); fix diff vs `d10b05b7` only
   `a2u.py` + the new test; harness/GGUF/flags unchanged; branch in the TASL-2 bare repo.
2. Precondition (c): 5 passed, 0 skipped; the five SHA-256 values match the PLAN row exactly; read-only on the
   old tree; the run checkout clean before/after.
3. Rerun: run checkout at `8237fd02`; manifest provenance = new pin/harness/GGUF/build, dirty=false; new
   out/work dirs only; all 10 instances from the start; session `23:14:13Z`–`23:58:32Z` rc=0 `complete`
   (roots 10, failed 0, exhausted 0); dry run 0/0/0; 2 % = 0 %; 165 `s04_rows`, 925 audit runs, no duplicate
   root or `(instance, budget_index)`.
4. `liveness` PASS (criteria in §5); `fit_prior` prior sha256 and contents (§5); the prior's `s04_rows_sha256`
   matches the run's `s04_rows.jsonl`.
5. Old `s04` STOP scene untouched (host and Mac); host end state clean; copy-back `SHA256SUMS` and
   host==copy hashes; pushes fast-forward only.
6. The 3.0 drill non-repetition rationale (§8) — accept or request a re-run of the drill.
   **Phase 4 has not started.**

## 11. Status

- **STOP 3 rerun complete; not self-accepted.** Submitted for a fresh independent review.
- S0.4 at the A2-U pin: 10/10 roots, 0 failed, 0 exhausted, `complete`; liveness PASS; prior recorded.
- The 9 Nov `s04` STOP scene is preserved untouched; the 9 Nov STOP-3 report remains the STOP record, and this
  report is the rerun record.
- **Phase 4 (and anything later) is not authorised** by this report or by the STOP-3 ruling.

## 12. Review record (STOP 3 rerun, accepted) and MINOR answers

- **Reviewer:** fresh independent reviewer (`track-s-reviewer-s04r2`), file
  `docs/r1/reviews/TRACKS_S04_RERUN_REVIEW_20261111.md` (359 lines). **Verdict: accepted** — 0 BLOCKING,
  0 MAJOR, 5 MINOR (documentation/evidence hygiene). The file as committed has sha256
  **`5f0cda1cc9afb6cee50b9c1bb999d582744ee53f1d036790670ccdfc30d43565`** (29,665 bytes, ends
  "Verdict: accepted"). **Flag:** the reviewer's and Lead's messages state `e62aee2a…`; that value does not
  match the file present in the worktree at commit time. The file was committed as-is; the reviewer should
  confirm the hash (it may be a pre-final-save value).
- **MINOR 1 (diff arithmetic / round wording) — fixed in §1.** `a2u.py` is **+37/−8 = 45 changed lines**
  (`git diff --numstat d10b05b7 8237fd02` → `37 8`), test +302; the review is described as "round 1 changes
  requested; accepted at round 2 (`8237fd02`) and round 3 (`fe651e58`)", tip docs-only.
- **MINOR 2 (old-scene "neither read nor written") — fixed in §4.** The rerun collector used only the new
  dirs; the **precondition deliberately read the old `$WORK/s04/roots` read-only** (hashes/mtimes unchanged;
  nothing written or deleted); the old `$OUT/s04` was not touched.
- **MINOR 3 (scratch-pytest capture) — answered in §2.** Exact invocation/environment given; with
  `PYTHONPATH=/tmp/trks_pytest_20261111.FI7Fdoi8` the frozen interpreter imports pytest 9.2.0 from the
  **scratch target** (evidence: `host_logs/trks_a2u_precondition_header_20261112.log`, sha256 `3322b55f…`).
  The earlier header's venv path came from a `python -c` run **without** `PYTHONPATH`; the frozen venv is
  unmodified.
- **MINOR 4 (copy-back one dry run behind) — fixed.** A second dry run at `00:15:51Z` (origin process not
  recorded) appended an identical line; the copy-back and `SHA256SUMS` were refreshed to the host's current
  two-line `trks_s04r2_dry.exit` (`aa3b55ab…`) / `trks_s04r2_dry.log` (`4fc0d6b5…`), now 22 files, and the
  second run is recorded in §4/§9. The completion check is unchanged.
- **MINOR 5 (provenance/drill wording) — fixed in §1/§8.** The launcher attribution is stated as the
  **observable chain** (times/commits/blob; the session id is not in any artifact); the drill non-repetition
  now rests on **runbook §3.0 ("once per host")**, the unchanged `trks-watch`/`trks-servers`/`trks-run` shas
  and the 9 Nov pass, with the Lead's instruction as relayed corroboration; the PLAN row location
  (`f82ff376` on the fix branch / remotes, not in the operator branch's `docs/r1/PLAN.md`) is recorded.
