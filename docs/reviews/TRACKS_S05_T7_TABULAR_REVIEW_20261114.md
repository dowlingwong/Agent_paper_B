# Independent STOP-4 review — Track S `tabular_mlp` S0.5 + S0.5b on TASL-7 (14–15 November 2026)

**Reviewer.** A fresh independent reviewer. I did not write the run, the copy-back, the report, the STATUS
entry or the launchers, and I took no operator/phase conclusion as evidence. I verified from the Track S
operator runbook rev 3.3 (`13badb0`), the accepted STOP-3 and S0.1 records, the commits, the committed and
host bytes, the copied results, and TASL-7 itself. TASL-7 was used **read-only only** (`ssh`, `ls`, `stat`,
`sha256sum`, `wc`, `head`/`tail`, `grep`, `tmux ls`, `pgrep`, `ps`, `nvidia-smi`, `ss`, `flock -n`,
`git rev-parse`/`status`/`ls-remote`). I wrote only this file. I started/stopped/signalled nothing on
TASL-7, attempted nothing on TASL-2, and made no git write operation in the operator worktree.

**Unit.** Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch **`trackS-ops-20261030`**,
operator worktree `.claude-worktrees/trackS-ops-20261030` at tip
**`110b01a81c27665bdb149d345d9854d1f9acd539`**; worktree clean, no untracked files before this review.
The main worktree and other worktrees were not touched.

**Scope.** The `tabular_mlp` half of Phase 4 only: S0.5 at k=2, S0.5b, the report/STATUS record and the
copy-back. **Not** the Mac-side S0.5 summary, **not** a calibration-gate pass, **not** STOP-4 completion,
**not** a Phase-4/S3 authorization.

## Authority read

- Track S operator runbook rev 3.3, blob at
  `13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, sha256
  **`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`** (641 lines; the worktree does not
  carry the docs-branch file, so it was read from the commit object). Phase 4, §0.5, §0.6, §0.7, §0.8, §10,
  §11.6.
- Accepted STOP-3 review at `db5f187b`: `docs/r1/reviews/TRACKS_S04_T7_TABULAR_REVIEW_20261114.md`, sha256
  **`fbf0a874aad6d526f1fa9c8f79ff4faf4bcfadb36ab4cdc45dbaf1a34949908b`**, final line `Verdict: accepted`.
- Accepted S0.1 review at `964e6633`: `docs/r1/reviews/TRACKS_S01_T7_TABULAR_REVIEW_20261114.md`, sha256
  **`d01fc7244aec6f13d66bc116a7696e43f63e6d5ad7a82d6b1271f781f8fc4cf8`**, final line
  `Verdict: accepted`; the file is byte-unchanged from `964e6633` to the tip.
- Digits STOP-4 pattern: `docs/r1/reports/TRACKS_S05_T7_RESULT_20261114.md` (sha256
  `8a0c3f9e5bede0cfbefa096c6058f65b75abd7aa9c5c1743dc74326ce2c3fab4`) and its accepted review
  `docs/r1/reviews/TRACKS_S05_T7_STOP4_REVIEW_20261114.md` (sha256
  `4c97854a197537cc703715282c47ffdd0ddf8ea7296d5ed9500a78a8584f101b`).

## 1. Provenance and commits — PASS

- Tip **`110b01a8`**; parent **`e33e1f6b`**. `git merge-base --is-ancestor e33e1f6b 110b01a8` is true and
  `git rev-list --count e33e1f6b..110b01a8` = **1** (fast-forward; no force). `git rev-list --parents` is
  linear, and the origin remote-tracking reflog shows only `update by push` entries (`e33e1f6b` → `110b01a8`
  at 2026-11-15T04:13:07+01:00); no forced update. (A separate local `reset` to `origin` on 14 Nov 14:12
  affects an earlier commit, not this tip, and did not move pushed history.)
- `origin/trackS-ops-20261030` = **`110b01a8`** (`git ls-remote origin`); TASL-7 bare
  `/home/dowling/r1_tracks/remotes/Agent_paper_B.git` `refs/heads/trackS-ops-20261030` = **`110b01a8`**
  (`git ls-remote tasl7`; `git --git-dir … rev-parse`), with `e33e1f6b` an ancestor (fast-forward). TASL-2's
  remote-tracking ref remains `78a1b65e` (12 Nov); no TASL-2 push was attempted (host down).
- Worktree clean (`git status --porcelain` empty, including untracked); `110b01a8` changes exactly
  `M docs/r1/STATUS.md`, `A docs/r1/reports/TRACKS_S05_T7_TABULAR_20261114.md`, and the 18 files under
  `results/r1/tracks/tabular_mlp/s05_t7_20261114/` (17 payload + `SHA256SUMS`).
- Report sha256 **`54839b84739a25d159944d17faebad6a56c5cf33de07faa967be5cbf34bc696d`** (104 lines); STATUS
  sha256 **`02f5bdf84e11ecd0aca901a56d24ea7ef3aeb2c94b04cac533ece3500d3c2c3a`**.
- The accepted S0.1 review and STOP-3 review are committed unchanged at the tip (sha256 values above).

## 2. Launchers and exact command — PASS

- S0.5 launcher `r1/tracks/ops/launch/tasl7_tabular_s05_20261114.sh`, repo sha256
  **`61a3dd5fbb9381032c8d33c164ea0d07ffaa709be71a354853c05aa46203c7ea`**; host
  `/home/dowling/r1_tracks/launch/tasl7_tabular_s05_20261114.sh` sha256 identical (byte-identical);
  `bash -n` OK; committed at `e33e1f6b` and unchanged at the tip.
- S0.5b launcher `r1/tracks/ops/launch/tasl7_tabular_s05b_20261114.sh`, repo sha256
  **`a9cf785c27bd6a4bf1e43d75aee9e9a890684b8312e1878de2245ab43d9a4b4a`**; host sha256 identical; `bash -n` OK.
- S0.5 guards read: priority markers (`trackx_evidence.active`, `trackp_evidence.active`,
  `$R/trks_drill.active`); session `trks_s05t_t7` must not exist; `$RUN` existing without
  `manifest.json` refuses (resume-vs-fresh); paper HEAD must equal `8237fd02…` and the worktree clean;
  prior file and `--prior-sha256 ba8f7783…` must match; if `trks_llm` exists, exactly `K=2` live
  `llama-server … --port 1810[12]` processes, otherwise no GPU compute process and `gpu0.lock` free;
  then starts/uses `trks-servers 2` and waits for both `18101`/`18102`.
- S0.5b guards read: refuses priority markers, an existing `trks_s05bt_t7` session, a running `trks_llm`,
  any `llama-server … --port 1810[12]`, a missing/empty `manifest.json`, and any `done.status != "complete"`.
- `.cmd` sha256 **`3cd5c643c273564dca0547c064127c1946ab26d72e9ad86a9d234f3f67d762b5`** (host identical),
  session `trks_s05t_t7`. The command is exactly the runbook Phase 4 command (paths abbreviated):
  `--phase S0.5 --node tabular_mlp --prior …/s04_t7_20261114/a2u_prior.json --prior-sha256
  ba8f7783d8a57e8650c6f5d6c8db38192e19cf1aeedd43c052687e16ba15732f --obs-inflation 1.0 --W 40
  --instances 20 --policy static:0.00057,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1
  --label ENGINEERING_ONLY --deadline 28800 --stop-file …/STOP --out …/s05_t7_20261114 --work
  …/s05_t7_20261114`. `printf %q` writes `static:0.00057\,0` and `8\,10\,12\,20`; bash resolves these to
  the same argv.
- S0.5b `.cmd` sha256 **`bdff166d84cabb24224158ab0d9331b7efbb1fb807ca3da074ca9f6dd482b103`** (host
  identical), session `trks_s05bt_t7`, `--phase S0.5b --node tabular_mlp --truncate-W 8,10,12,20`.

## 3. S0.5 result and data integrity — PASS

- Launcher start **2026-11-15T00:08:49Z**; `starting fresh servers k=2`; pids **832486/832487**; both
  endpoints **18101/18102 ready 00:08:51Z**; lease HELD; prior sha `ba8f7783…` verified by the launcher;
  collector start 00:08:52Z. Exit **2026-11-15T02:38:52Z rc=0**; manifest session
  `20261115T000852Z–20261115T023851Z`, `done = {roots 50, forks 31, leaves 99, failed 0, exhausted 0,
  deadline_hit false, status "complete"}`.
- Counts and hashes (copy and host byte-identical): `roots.jsonl` 50, sha256
  **`5e082a5825fed7cacbf934c8926ef99445287f872ea961220f0c8608d445345e`**; `forks.jsonl` 31, sha256
  **`b2c4ad5f08874b84f2c5a1e40007cc63fd9915cc647c6a8cf1626ff2192cdfed`**; `leaves.jsonl` 99, sha256
  **`ebae0c9995865a531987109817c6e7ae982fe7022316c202c34692b9934a852b`**; `audit_runs.jsonl` 1930,
  sha256 **`6f17837cdc2f9d411fa43bdd8ed84e2349b498c5b2e26153f88ceb026d7ac21b`**; `s05_calibration.jsonl`
  330, sha256 **`e05cd54a672a62a2f9454dd572d1ce17b61dbd5ab1b87a90d8559b86805a6af3`**;
  `manifest.json`, sha256 **`28e008f66120958e9b78665ef0f3c39ce76655c5947b451ce54237d1ed18a89a`**.
- No `failed_units.jsonl`, no `$RUN/STOP`; `exhausted = 0`; `deadline_hit = false`. The ≤2 % rule is
  **0 / (50 + 99 + 0) = 0.0 %**.
- Ledger integrity: 50 unique `root_id`s, all `status=ok`, rep 0 = 40 / rep 1 = 10; 31 unique `fork_id`s;
  99 unique `(fork_id, arm, rep)` leaves, all `status=ok`, no errors on roots/leaves; 7 A/A leaves all
  `aa_reproduced=True`. Calibration/truncated root ids are a subset of the 50 committed roots; all audit
  seeds lie in the S0.5 block `200000–299999`.
- Provenance in the manifest matches the report: paper `8237fd02…`, harness `a3fedbb…`, GGUF `509287f7…`,
  llama `620d2225…`, host `TASL-7`, gpu `GPU-ab72fb4a-…`, `paper_dirty=false`, `harness_dirty=false`,
  label `ENGINEERING_ONLY`, `obs_inflation=1.0`, `g_declared=g0=0.00019`, `prior_sha256=ba8f7783…`,
  phase `S0.5`. The prior's `meta.obs_inflation` is `1.0` (λ manual check **passes**); the manifest records
  the same value.
- `s05_calibration.jsonl` last line is valid; all 330 rows have level 0.8, `sd > 0`, non-null
  `delta_audit`, boolean `covered`. **Data-derived coverage** (not the Mac summary): overall
  **231/330 = 0.700**; by stratum **0: 21/57 = 0.3684**, **1-2: 62/95 = 0.6526**, **>=3: 148/178 = 0.8315**.
  The pinned code's `calibration_gate` (band [0.70, 0.90], `stratum_min = 20`, `min_n = 100`) returns
  **`status: "fail"`** on these rows. The gate is per node; see MAJOR-1.
- `s05b_truncated.jsonl`: 200 rows, exactly 50 per W over {8,10,12,20}, last line valid; `binding` counts
  **50/50 (W8), 50/50 (W10), 50/50 (W12), 8/50 (W20)**. Rows are linked to the same 50 S0.5 roots and
  S0.5 audit seeds. This is descriptive data only; the S0.5b numbers are not a gate.

## 4. S0.5b truncation sweep — PASS

- Launcher sha `a9cf785c…` (above); ran **2026-11-15T03:10:52Z → 03:11:07Z**, CPU only. The launcher
  refused-nothing (no REFUSE in `s05b_t7_tabular_20261114_launch.log`); `trks_s05bt_t7.exit`
  **`2026-11-15T03:10:53Z rc=0`**; collector log `{"out": "…/s05_t7_20261114", "truncated_audits": 200}`;
  launcher says `S0.5b collector rc=0` and `S0.5b DONE` at 03:11:07Z; no nonzero/refusal/STOP.
- `s05b_truncated.jsonl` 200 rows, sha256
  **`615aa3909eaaece41c82d026d2e876847ae01b1bd765ca9cc16671943e34c3bb`**, last line valid;
  `s05_calibration.jsonl` still 330 rows. `truncated_audits = 200` matches the row count.
- The launcher's `done.status=complete` precondition was satisfied by the S0.5 manifest; the servers were
  stopped before S0.5b (the launcher would have refused a live `trks_llm`/`llama-server`).

## 5. k = 2 provenance — PASS

- The accepted S0.1 review (`d01fc724…`, final line `Verdict: accepted`) independently recomputed
  within-server identity **200/200 on 18101 (serial), 200/200 on 18101 and 200/200 on 18102
  (concurrent)**, and **`cross_server_identity` 200/200 = 1.0000**, with discriminating negative controls.
  The author's rule is recorded: **any identity < 100 % in any required cell is a STOP for the author; no
  k=1 fallback/bypass**. The review's gate sentence authorises S0.5/S0.5b only after acceptance, at k=2.
- S0.5 actually ran with **two resident servers**: the launcher log records `k=2`, pids 832486/832487, both
  endpoints ready, and the GPU compute-apps line lists both server pids; the append-only
  `llama_18101.log`/`llama_18102.log` both show a fresh `model loaded` at the start of the run. The
  collector itself is a single process on 18101, which is exactly the runbook §0.5 exception for S0.5
  (S0.4, S0.5 and the exact placebo are not k-process phases); the launcher refuses a `trks_llm` whose live
  count is not 2. The `.cmd` records `TRKS_PORT=18101`.

## 6. Host end state and TASL-2 — PASS

Verified on TASL-7 at **2026-11-15T03:16Z** (read-only):

- `tmux ls` = only **`trks_watch`**; `pgrep -x llama-server` = none; `ps -eo comm` count of `llama-server`
  = 0; `nvidia-smi --query-compute-apps` empty; `ss -ltnp` has **0** listeners on 1810x; lease
  **FREE** (`flock -n ~/r1_locks/gpu0.lock true`); GPU **0 %, 243 MiB / 24 564 MiB**; disk **525 G free**;
  markers directory has only `bin/`, `gpu0.lock`, `_to_delete` (no `trackx_evidence.active`,
  `trackp_evidence.active` or `trks_drill.active`); `find $R/out -name STOP` = **none**.
- No extra host writes: the only files under `/home/dowling/r1_tracks` newer than the 03:12Z run end are
  the **expected TASL-7 bare-repo push** objects/ref at 03:13Z (33 files; ref = `110b01a8`;
  `e33e1f6b` is an ancestor). No run/data/log files outside the run were written after 03:12Z.
- TASL-2 (`portal_zhixu`, 100.120.160.70) is **unreachable**: `ssh` to port 22 returns
  `Operation timed out` (rc=255). No TASL-2 operation was attempted; its remote-tracking ref is unchanged
  at `78a1b65e`. No B2/X.7/sweep-2: no `trackx_evidence.active`, no extra session/process, no GPU compute.
- The report's §4 end-state check is operator-recorded at 03:10:44Z with no saved capture; the durable
  current state independently confirms the same end state. This is a residual limitation, not a finding.

## 7. Copy-back and preservation — PASS

- `results/r1/tracks/tabular_mlp/s05_t7_20261114/`: **`SHA256SUMS` verifies 17/17** (`shasum -a 256 -c`
  all OK). **Host == copy 16/16** (7 run-tree files + 9 `host_logs/` files; the 17th payload,
  `operator_capture/s05_waiter.log`, is Mac-side only). Run tree: roots/forks/leaves/audit_runs/
  manifest/calibration/truncated; `host_logs/`: both launcher logs, both `.cmd`s, both `.exit`s, both
  collector `.log`s, `watch.log`; `operator_capture/`: `s05_waiter.log`.
- Old scenes preserved: no file under `results/r1/tracks` (outside `s05_t7_20261114`) is newer than
  2026-11-15 01:00 CET; old tabular Oct-30 scenes still carry Oct-30 mtimes (host and Mac), the digits
  S0.5/S0.5b evidence still carries 14 Nov mtimes (host logs 05:00 local = 13:00Z), and the
  `s01_t7_20261114` and `s04_t7_20261114` copy-backs verify their own `SHA256SUMS` and are git-clean.
- The worktree is git-clean apart from this review file; no payload was modified or deleted.

## 8. Report/STATUS accuracy — one material omission

Accurate and re-derived: pins/clean, k=2 basis and the author's no-fallback rule, S0.5 counts/hashes and
the 0.0 % rule, S0.5b `truncated_audits=200` and 200 rows, host end state, copy-back 17/17 and host==copy
16/16, the Lead-relayed author-amendment disclosure (no separate author artifact/PLAN §10 row), §3.0b
**OPEN** (gates Phase 6 / 0.3(c)), B2 not armed, TASL-2 down/deferred, not self-accepted, and the explicit
statement that **STOP 4 remains open for the Mac-side S0.5 summary** and that the digits-half acceptance
was not a calibration-gate pass. Nothing in the record contradicts the Mac-side summary; the summary's
inputs are present and hashed.

The material omission is the **tabular per-node calibration gate**: see MAJOR-1. The report's §6 sentence
("… must report the **digits** per-node calibration `fail` … as well as the tabular rows") names the digits
failure but is silent on the tabular failure, and the STATUS entry (line 11) is likewise silent. A reader
of the STOP-4 record would not learn that the tabular node also fails the Phase-4 gate (and that a failing
stratum 0 is a STOP for the author).

## 9. Findings

**BLOCKING: none.** The run, its provenance, the host end state and the copy-back all re-derive correctly.

**MAJOR-1 — the tabular per-node calibration-gate result is missing from the STOP-4 record.**
Locations: `docs/r1/reports/TRACKS_S05_T7_TABULAR_20261114.md` §6 (lines 85–90) and
`docs/r1/STATUS.md` line 11. The pinned code `calibration_gate` on the 330 committed rows returns
`status: "fail"` (n=330, overall 231/330 = 0.700; stratum 0 21/57 = 0.3684, stratum 1-2 62/95 = 0.6526,
stratum >=3 148/178 = 0.8315; band [0.70, 0.90], `stratum_min=20`). Per runbook Phase 4, a **failing
stratum 0** is a **STOP for the author**; λ₂ cannot fix stratum-0 intervals (they come from the prior
alone), so this is not a λ₂ re-run case. (The code's returned generic `rule` string,
"fail -> revise the inflation factor once and re-check; a second fail is a STOP", is not the runbook's
rule for a failing stratum 0; the runbook's STOP-for-author reading governs, per §0.6's instruction not to
adopt another reading of a STOP rule.) The digits half recorded its analogous fail; the tabular half does
not. **Required fix:** add a descriptive calibration paragraph to the report (and the STATUS entry) giving
the n, overall and per-stratum coverage, the code's gate status `fail`, and the Phase-4 STOP-for-author
consequence; state that the deferred Mac-side S0.5 summary must report **both** nodes' per-node status
(digits `fail` and tabular `fail`), not treat either as passed. No data re-run is required for this
finding. The record is incomplete until this is added.

**MINOR-1 — the TASL-7 bare-repo fast-forward is not recorded.** Locations: report §5 (lines 69–76) and
STATUS lines 9–10 mention only the TASL-2 deferral. The TASL-7 bare repo is at **`110b01a8`**
(`git ls-remote tasl7`; bare `rev-parse`), with `e33e1f6b` an ancestor (fast-forward, no force).
**Required fix:** add one sentence to §5/STATUS recording the TASL-7 bare-repo fast-forward to the
submission tip, as the digits record did.

**MINOR-2 — the operator capture is partial and noisy.** `results/r1/tracks/tabular_mlp/s05_t7_20261114/
operator_capture/s05_waiter.log` stops at **2026-11-15T01:29:12Z** (`roots=46 forks=30 leaves=0`) and
contains harmless `…/leaves.jsonl: No such file or directory` lines from reading the file before it
existed; it does not evidence completion. It is not used as evidence (the manifest/collector log are), so
there is no data impact. **Required fix:** label it as a partial monitor capture (not evidence), or add a
completion capture; do not cite it as proof of the run's end state.

**Residual limitation (not a finding).** The report's 03:10:44Z host end-state check is operator-recorded
with no saved capture; I independently verified the durable end state at 03:16Z. The TASL-2 "untouched"
claim cannot be proven while the host is down; no TASL-2 operation appears in the record and the
remote-tracking ref is unchanged.

## 10. Explicit statements

- **Data integrity: PASS.** All ledgers/manifest/calibration/truncation files are internally consistent,
  linked to the 50 committed roots and the S0.5 audit block, and byte-identical to the host; no
  `failed_units`, no `STOP`, `exhausted=0`, `deadline_hit=false`; the 0.0 % failed-unit rate re-derives.
- **k=2 provenance: PASS.** The accepted S0.1 review (`d01fc724…`) measured 100 % within-server identity
  on both URLs and `cross_server_identity` 200/200 = 1.0000, with the author's "any identity < 100 % =
  STOP, no k=1" rule recorded; S0.5 ran with two resident servers (pids, both endpoints, both server logs,
  GPU compute list) and a single 18101 collector per the runbook's S0.5 exception.
- **Host end state: PASS.** Only `trks_watch`; lease FREE; 0 `llama-server`/compute/listener; no
  markers/STOP; TASL-2 unreachable and untouched; no B2/X.7/sweep 2; the only post-run host write is the
  expected TASL-7 bare-repo push to `110b01a8`.
- **Open Mac-side summary: OPEN, and the tabular record is the input.** STOP 4 remains open for the
  Mac-side S0.5 summary (W, σ_cmp,vary, σ_D UCL, between-rep UCL, `between_policy_sd_at_cap`, b,
  calibration status, λ). That summary must report **digits `fail` (already named) and tabular `fail`**
  (missing from this record). The tabular half is not STOP-4 completion, not a calibration-gate pass and
  not a Phase-4/S3 authorization; the data needed for the summary is present and hashed.
- **Nothing in this record pre-empts or contradicts the Mac-side summary**; the only defect is the omitted
  tabular calibration disclosure (MAJOR-1) plus two documentary MINORs, which do not affect the measured
  data or the k=2 decision.

## 11. What remains open

- MAJOR-1 and MINOR-1/MINOR-2 must be answered/committed; then the operator may resubmit for acceptance.
- The Mac-side S0.5 summary (both nodes' per-node calibration status, W, σ values, b, λ) remains open.
- §3.0b remains OPEN and gates Phase 6 / 0.3(c) on TASL-7. The Lead-relayed 14 Nov author amendment still
  has no separate author artifact/PLAN §10 row (disclosed, not manufactured).
- No B2/X.7/sweep 2; TASL-2 bare-repo push remains deferred.

Verdict: not accepted

## 12. Round-2 re-check — fix commit `9b2fba9a`

**Scope.** Re-check of the three round-1 findings only, plus confirmation that nothing else in the record moved. The
round-1 verdict line above stands as the round-1 verdict; this section supersedes it. No host write, no run, no TASL-2
contact in this round.

**Fix commit.** `9b2fba9a9c23aa135ca14197830702273d60ec39`, parent **`110b01a8`**, one commit
(`git rev-list --count 110b01a8..9b2fba9a` = 1; `git merge-base --is-ancestor 110b01a8 9b2fba9a` true), so both ref moves
are fast-forwards: `git ls-remote origin` and `git ls-remote tasl7` both return **`9b2fba9a`**. `git diff --name-status
110b01a8..9b2fba9a` is exactly `M docs/r1/STATUS.md` + `M docs/r1/reports/TRACKS_S05_T7_TABULAR_20261114.md`; the diff
under `results/` and `r1/` is empty. Report now **`fc8f66a9a505adbea0bae6c44e0e0b5c3b4f3ff4aecff873b0acd634963406cc`**
(was `54839b84…`), STATUS **`b05e613b87e77679afeb845f9b92ffbc28175d3c39fdd4965c54f7b60cfc5122`** (was `02f5bdf8…`).
`git status --porcelain` shows only this review file untracked.

**MAJOR-1 — resolved.** The record now carries the **tabular per-node** gate where round 1 found only the digits one:
report §6 (lines 86–91) gives the pinned call (`r1/tracks/analyze.py`; band [0.70, 0.90], `min_n` 100, `stratum_min` 20),
n = 330, overall 231/330 = 0.700, strata 0 21/57 = 0.3684 / 1-2 62/95 = 0.6526 / >=3 148/178 = 0.8315,
`status: "fail"`, the Phase-4 **STOP-for-author** consequence for a failing stratum 0 (λ₂ cannot fix stratum-0 intervals;
the code's generic "revise once" string is not the runbook rule) and "no data re-run"; report §6 (lines 95–100),
checklist item 6 (lines 113–116) and STATUS lines 11–12 require the deferred Mac-side summary to report **both** nodes'
status (digits `fail` and tabular `fail`) and state that neither half's acceptance is a calibration-gate pass.
**Independent recomputation** on the 330 committed rows (`s05_calibration.jsonl`, sha256 `e05cd54a…`, identical to round 1
and to `SHA256SUMS`), with the exact `calibration_gate` source extracted from `r1/tracks/analyze.py` at `9b2fba9a` (lines
2045–2064; the module itself is not importable in the local Pythons — no numpy/scipy — but the function body has no
numeric-library dependency, so its source was executed verbatim), returns `n=330`, `coverage=0.7`, `status="fail"`, and
`by_stratum` 0: n=57, 21 covered, 0.368421…, gated, `in_band=false`; 1-2: n=95, 62, 0.652631…, gated, `in_band=false`;
>=3: n=178, 148, 0.831460…, gated, `in_band=true` (strata sum 330). A separate from-scratch count with no code imported
gives the same 231/330, 21/57, 62/95, 148/178 — the record's numbers match exactly. **Runbook check:** rev-3.3 blob at
`13badb0:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` (sha256 `a93fb84b…`, 641 lines), Phase 4 lines 291–296:
"**Coverage too high, or a failing stratum `0`:** **STOP** for the author. λ ≥ 1 only widens intervals, and it does not
change stratum-0 intervals … so the λ₂ revision cannot fix these." The record's reading is the runbook's; the code's
returned generic rule string is correctly not adopted.

**MINOR-1 — resolved.** Report §5 (lines 75–76) and STATUS line 10 now record the **TASL-7 bare-repo fast-forward
`e33e1f6b → 110b01a8`** (verified `git ls-remote tasl7`), alongside the still-deferred TASL-2 push. At the round-2 check
both `origin` and `tasl7` are `9b2fba9a`, and `110b01a8` is a one-commit ancestor of it (identical commit hash ⇒ identical
ancestry), so the bare carries the recorded fast-forward history; the recorded value is the tip **as of the submission**
and is superseded only by the pushed fix commit, itself a fast-forward.

**MINOR-2 — resolved.** `operator_capture/s05_waiter.log` (37 lines) runs `WAITER START 2026-11-15T00:09:11Z` to a last
`PROGRESS 2026-11-15T01:29:12Z roots=46 forks=30 leaves=0 lease=HELD markers=none` and contains 19
`No such file or directory` lines for the not-yet-created `roots/forks/leaves` ledgers. It is now labelled a **partial
monitor capture, not completion evidence**, in report §5 (lines 77–80) and STATUS line 10 (stops 01:29:12Z,
roots=46/forks=30), which matches the file. Completion remains evidenced by `host_logs/trks_s05t_t7.exit` =
`2026-11-15T02:38:52Z rc=0` and the manifest session `20261115T000852Z–20261115T023851Z` with `done.status = "complete"`
(roots 50, forks 31, leaves 99, failed 0, exhausted 0, `deadline_hit` false); no `failed_units.jsonl`, no `STOP`.

**Nothing else moved.** The fix commit changes no payload/`SHA256SUMS`/launcher/code; `git status` is clean apart from this
review file; `SHA256SUMS` verifies **17/17** on disk (`shasum -a 256 -c`, all OK, rc=0) with `s05_calibration.jsonl` still
`e05cd54a…`; the review file itself was byte-unchanged before this append (sha256 `9ab84530…`, 256 lines).

**Caveats still present.** STOP 4 remains **open** for the Mac-side S0.5 summary, which must report both nodes' status;
§3.0b is **OPEN**; B2 is **not armed** (no `trackx_evidence.active`); TASL-2 is **down/deferred**; the submission is **not
self-accepted** and is **not** an S0.5-close, STOP-4-completion, Phase-4 or S3 authorization. Text re-read in report §6 and
STATUS lines 10–12; unchanged.

**Residual limitation.** No host was contacted this round except the read-only `git ls-remote` ref query, so "host == copy
16/16" is not re-derived here. It stands on the round-1 host check plus the fact that every tracked payload byte is
unchanged since `110b01a8` (clean tree; `SHA256SUMS` 17/17).

**Editorial (not a finding).** STATUS line 12 now carries an odd number (9) of `**` markers (the pre-fix line had 8), so one
renders literally as `**` after "tabular `fail`". The substance and the both-nodes requirement still read correctly; no
change is needed for acceptance, and fixing it would change the recorded STATUS sha — leave it for the next STATUS
touch-up.

**Findings remaining: none.**

Verdict: accepted
