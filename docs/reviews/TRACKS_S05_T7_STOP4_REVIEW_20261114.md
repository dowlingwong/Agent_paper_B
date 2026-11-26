# Independent STOP-4 review — Track S `digits_mlp` S0.5 + S0.5b on TASL-7 (14 November 2026)

**Reviewer.** A fresh independent reviewer. I did not write the run, the copy-back, the report, the STATUS entry or
the prior resume-unit reviews, and I took no phase's conclusions as evidence. I verified from the runbook rev 3.3
(commit `13badb0`), the reviewed/accepted resume unit rev 5 and its R2 review, the commits, the accepted copy-back,
and TASL-7 **read-only** (`ssh`, `cat`/`stat`/`sha256sum`, `tmux ls`, `pgrep`, `nvidia-smi`, `flock -n`,
`trks-status`, `git`). I wrote only this file and temporary files/directories under `/tmp`; no host writes, no runs, no TASL-2 writes.
Independence caveat: TASL-2 is down, so its Track S scene could not be re-censused (see §6).

**Unit.** Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch **`trackS-ops-20261030`**, operator worktree
`.claude-worktrees/trackS-ops-20261030` at tip **`a504a604`** (chain `92680170 → e008abfb → b846251e → a0a4c7cb →
a504a604`; worktree clean, 41 tracked files under the result tree). *State note:* while this review ran, `origin`
(GitHub) advanced from `a504a604` to **`ba64517b`** ("Record the Track S S0.5 result reviews (R2 accepted)",
`2026-11-14T14:19:38+01:00` = 13:19:38Z). `ba64517b` adds **only** the two prior-loop review files
(`TRACKS_S05_RESULT_REVIEW_20261114.md`, `_R2_`), is a child of `a504a604`, and changes no payload; the unit reviewed
here is the `a504a604` tree. The operator must fast-forward onto `ba64517b` before committing this review file (normal
push only). `e7417c5e` is preserved on the local backup branch `backup-trackS-ops-e7417c5e-20261114` and is **not** on
origin; no force-push occurred (origin history is linear).

**Scope.** The `digits_mlp` half of Phase 4 only: the resumed/completed S0.5 pilot, the S0.5b truncation sweep, the
merged result record and the STATUS entry. **Not** the `tabular_mlp` half, **not** the S0.5 summary, **not** a
calibration-gate pass, and **not** a Phase-4/S3 authorization.

## 1. Provenance

| commit | time (UTC) | content |
|---|---|---|
| `92680170` | 10:44:25 | record the launcher-fix reviews (R2 accepted) + the resumed run |
| `e008abfb` | 13:02:09 | S0.5 resume/copy-back; L1 pause (13 payload files + SHA256SUMS, 23 entries) |
| `b846251e` | 13:11:31 | merged result record; force-add the 10 ignored files; `logs/`→`host_logs/` |
| `a0a4c7cb` | 13:11:48 | SHA256SUMS covers all 40 payload files (adds nested `operator_capture/SHA256SUMS`) |
| `a504a604` | 13:13:28 | docs-only fix (stale "37/39 files" refs, TASL-2 host-down gap) |
| `ba64517b` | 13:19:38 | **origin tip**; docs/review-record only (see state note) |
| `e7417c5e` | 13:05:55 | operator's superseded line (parent `92680170`); local backup branch only |

- Chain is linear and a fast-forward over `92680170`; `a504a604` is an ancestor of `ba64517b`; worktree clean.
- Authority hashes reproduce: runbook `13badb0` = `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`;
  resume unit rev 5 = `f9373cb532afe17d76683ea4e80f1296d60e5136b1287f14ba310a4bbd5a7431` (81 lines, at `9b217c53`);
  R2 review = `561c546ae934420eb866f19f0a0adeebb7762da39cfe86dd89a515802683d2a4` ("~10:40Z", VERDICT accepted,
  reviewed tip `9b217c53`); round-1 review = `0f5cccc0a90ae9d6a051a5e8d3790d5678fc152ade091e6f3823c41fffa39388`
  (changes required).
- Launchers `f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3` (S0.5) and
  `3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a` (S0.5b): repo == host == copy, `bash -n` OK.
  The pre-fix launcher is `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151` (`e253a423^`).
- TASL-7 bare repo `trackS-ops-20261030` = `d8ac944c` (13 Nov 12:26Z; an ancestor, 15 commits behind) — see MINOR-5.
  TASL-2 bare tracking ref unchanged at `78a1b65e` (12 Nov); TASL-2 unreachable (see §6).

## 2. Copy-back completeness and integrity

- **41 tracked files = 40 payload + the top-level `SHA256SUMS`.** `shasum -a 256 -c SHA256SUMS` = **40/40 OK**;
  the nested `operator_capture/SHA256SUMS` verifies **5/5**; all 40 payload paths are covered by `SHA256SUMS` and no
  entry is untracked.
- **The 10 previously-missing files are committed byte-identically.** At `e008abfb` the `SHA256SUMS` (23 entries)
  pinned 10 files that were not in the tree (6 top-level `.jsonl`, `_to_delete/STOP.retired.20261114T103527Z`, and the
  3 `.log` files). They are now force-added (tracked despite `.gitignore` `*.jsonl`, `*.log`, `_to_delete/`) and each
  matches the hash `e008abfb`'s own `SHA256SUMS` recorded for it (10/10 MATCH).
- **Host == copy 25/25.** On TASL-7, the 8 run-tree files (roots/forks/leaves/audit_runs/manifest/calibration/
  truncated/retired STOP) and the 17 `host_logs/` files are byte-identical to the copy (sha256 compare, 0 mismatches):
  roots `039b6955…`, forks `bf638fa6…`, leaves `427faff6…`, audit_runs `93939187…`, manifest `68a0d6e0…`,
  calibration `2e4c9a8c…`, truncated `cd296fd8…`, STOP `e3b0c442…`, `.cmd` `fe9fae36…`.
- **Retired STOP:** `$RUN/STOP` absent; exactly one `_to_delete/STOP.retired.20261114T103527Z`, **0 B, inode
  57048847, sha `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`**, no deletion.
- **The parallel record's result bytes were not altered.** `git diff e008abfb..a504a604 -- manifest.json scripts/` is
  **empty**; every pre-existing payload hash is unchanged (0 changed entries); the 10 added files match the pinned
  hashes. The only changed index is `SHA256SUMS`, necessarily extended 23 → 40 entries (30 added lines = 17
  `host_logs/` paths + 13 `operator_capture/` paths; 13 removed lines = the `logs/`→`host_logs/` path rename). The
  literal `git diff e008abfb..a504a604 -- …/SHA256SUMS` is therefore **not** empty; that extension *is* the fix, not a
  modification of results.

## 3. S0.5 provenance and result

- **Resume:** launch `10:43:33Z` with the fixed launcher `f823b86a…` (host mtime 10:43:28Z, host sha verified), k=2
  servers **pids 666767/666768**, endpoints ready `10:43:35Z`, collector `trks_s05_t7` **pid 666901** (launch log and
  the operator capture at 10:44:13Z agree).
- **Failed first attempt:** `10:35:27Z`, pre-fix launcher `3e957464…`; `s05_t7_resume_launch.rc = rc=1`, stdout 0 B,
  no launch-log line, collector untouched since 13 Nov — it started **nothing**. The pause STOP was renamed **once**
  (no-op rule honoured on the successful resume); **no second/duplicate start**: one `trks_llm`, one collector, one
  resume launch line.
- **Command identity:** `trks_s05_t7.cmd` sha `fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b`
  (786 B), byte-identical to the pause-era capture. It carries the prior + sha, `--obs-inflation 1.0`, `--W 40
  --instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5 --aa-fraction 0.1`, the
  ENGINEERING_ONLY label, the 8 h deadline and the same `--out`/`--work`.
- **Exit:** `trks_s05_t7.exit` `2026-11-14T12:34:03Z rc=0`. **Manifest:** 2 sessions — #0
  `20261113T122552Z–20261113T130300Z` `paused` done `22/6/0/0/0`; #1 `20261114T104335Z–20261114T123402Z`
  **`complete`** done **`28/18/71/0/0`**, `deadline_hit=false`. Provenance (both sessions): paper `8237fd02`,
  harness `a3fedbb`, GGUF `509287f7`, llama.cpp `620d2225`, host TASL-7, gpu `GPU-ab72fb4a-…`,
  `paper_dirty=false`, `harness_dirty=false`, `obs_inflation=1.0`, `g=0.00066`, phase `S0.5`, label
  `ENGINEERING_ONLY`, prior sha `5c849d15…`.
- **Totals:** roots **50** (50 `ok`), forks **24** (5 A/A), leaves **71** (71 `ok`), audit_runs **1780**; all JSONL
  lines parse and every last line is complete; **no `failed_units.jsonl`**, **no STOP**, `exhausted=0`. Observation:
  the manifest session audit counts sum to 1,770; the extra 10 `audit_runs.jsonl` lines are consistent with S0.5b
  appending audits after session #1 closed, but the record does not say so (non-blocking).
- **Calibration:** `s05_calibration.jsonl` **298 rows**, level 0.8 all, k=5 all, sha
  `2e4c9a8c40ef5fb9a740ad5b4ad12e2d7026c42fdc19b4467ddeefbaacc50a2b`. Coverage **231/298 = 0.7752**; the record's
  fine-grained strata reproduce exactly (`HIDDEN_UNITS + 0` 0/20, `BATCH_SIZE + 1-2` 20/40, `HIDDEN_UNITS + 1-2`
  31/40, `HIDDEN_UNITS + >=3` 75/75, `LEARNING_RATE_INIT - 0` 5/11); `delta_audit` mean −0.007418 (min −0.412256, max
  0.192200). The record correctly labels these **descriptive only** and does not claim the gate passes.
- **Gate note (open for STOP 4):** the code's per-node gate (`r1/tracks/analyze.py::calibration_gate`, grouping by
  `stratum`) returns **`fail`** on these rows: stratum 0 = 35/65 = **0.5385**, stratum 1-2 = 60/89 = **0.6742**,
  stratum >=3 = 136/144 = **0.9444**, all outside [0.70, 0.90]. Per Phase 4 a failing stratum 0, or over-coverage, is
  a **STOP for the author**. This does not make the numbers wrong and it is explicit that the gate is deferred, but
  the record's phrase "the aggregate gate is a Phase-4 decision with `tabular_mlp`" is imprecise (the gate is
  per-node) — MINOR-3 — and the deferred S0.5 summary must report the per-node status, not treat it as passed.

## 4. S0.5b

- `tasl7_digits_s05b_20261113.sh` ran `13:00:39Z→13:00:54Z` (CPU, after S0.5 `complete` and with no servers): exit
  `2026-11-14T13:00:53Z rc=0`, `s05b_t7_launch.rc = rc=0`, "S0.5b DONE" 13:00:54Z, log
  `{"out": "$RUN", "truncated_audits": 200}`; **no refusal or error line**; 200 rows, sha
  `cd296fd8f2029266015d536f0f561521e13da36f83d7f00c84a9439d4c1ce135`, 50 rows per W over {8,10,12,20}, policies
  `a2u`/`static:0.00198,0`, reps 0/1, 5 audit seeds each, all lines valid.
- **Cap binding:** binding rows **50/50 (W8), 50/50 (W10), 47/50 (W12), 2/50 (W20)**, i.e. the cap binds at **low** W;
  `y_terminal` means 0.963097 / 0.968334 / 0.970830 / 0.972802 reproduce. The "cap binding is visible at the higher W"
  sentence in the **parallel-phase** record `e008abfb` §3 (line 30 there) is **not** supported by the data. The merged
  record (`b846251e`/`a504a604`) corrects it to "the cap binds at the **low** W values", which the data support —
  MINOR-2 below only concerns the illustrative `8/8, 10/12, 12/22, 16/40` cells and the "16/40 is the … count" wording.

## 5. Governance disclosure

Report §7 and the STATUS entry state the four required facts, and they check out:
**parallel-phase execution** (resume `10:43:33Z`; §1.7 + S0.5b `13:00:38–54Z`) and the operator role (verify/bookkeeping
only; no duplicate run); **record-vs-launch ordering** (R2 ~10:40Z accepted vs. record commit `92680170` at
**10:44:25Z**; launch 10:43:33Z — "record-vs-launch nuance, not an ungated start"); the **failed first attempt**
(rc=1, started nothing, STOP retired once, no deletion); the **deferred `trks-status` fix and its later application**
(host: old `PAPER_SHA=d10b05b7…`/sha `5bd570ff…` at 13:01:25Z → new `8237fd02`/`70fbe8bd…` at 13:02:31Z). The
record is correctly ENGINEERING_ONLY/descriptive/not self-accepted and does not claim Phase-4 completion or S3
authorization. Two dated errors: see MINOR-1.

## 6. Host end state, scope, TASL-2

- **TASL-7 (13:16–13:22Z):** only `trks_watch`; lease **FREE** (`gpu0.lock` free); GPU idle `0 %`/236 MiB; no
  `llama-server`, no collector, no 18101/18102 listener; no `trackx`/`trackp`/drill markers. No S0.5 `STOP`; one
  retired STOP. The only recent writes under `$R` are the approved `bin/trks-status` (mtime
  13:02:31Z) and the run's launch scripts (deployed for the run at 10:43:28Z/13:00:35Z); the 13:00:42/13:01:01/13:01:25 captures still show the old
  `trks-status`, so the fix was applied *after* the run and the verification, at the safe point.
- **`trks-status`:** `PAPER_SHA=8237fd02b09ef2d28016a1c9f6acac3c35bb768b`; script sha
  `70fbe8bd312fd7aad3a9020b80dcf9284453a8319dbb2cb523e9f6c06f16cc5f` (= committed repo file; the previous version at
  `2906b676` is `5bd570ff12b461e1d8cb67f348c6c56569a48cf4c57dbe15f6a5b23420c30869`); it prints `OK paper 8237fd02`,
  `OK harness a3fedbb`, `OK llama.cpp 620d2225`, GGUF OK. The pinned-HEAD section has no `STOP:` line; the manifests
  section prints `STOP-file present` for the legacy Oct-30 `smoke` manifest (not the S0.5 run) — MINOR-4.
- **TASL-2 host-down deferral.** TASL-2 (`portal_zhixu`/100.120.160.70) does not answer `ssh` (TCP timeout at
  13:16Z); I made no write attempt. The merged report's provenance paragraph and the STATUS line
  13 record the deferral as a **host-down gap** and say TASL-2 was not touched; the local TASL-2 tracking ref is still
  `78a1b65e` (12 Nov), so no record push landed. **The deferral is properly disclosed and not silently skipped.** I
  could not re-census the TASL-2 Track S scene itself (host down); the "untouched/resumed" claim is consistent with
  all available evidence (no TASL-2 commits/logs in the unit; the launcher never contacts TASL-2) but is not
  independently re-censused here.
- **Scope:** no B2/X.7/sweep 2 artifacts; the S0.5 summary and STOP 4 explicitly wait for `tabular_mlp`; the
  submission is not self-accepted.

## 7. Findings

**BLOCKING: none. MAJOR: none.** Six MINOR documentary/provenance items:

**MINOR-1 — two times are CET written as UTC.** Locations: report lines 131–132 ("unreachable … at `14:10Z`") and
STATUS line 10 ("re-verified … at `14:12Z`") and line 13 (`14:10Z`). At the review the Mac was 14:19 CET = 13:19Z,
and `a504a604` is 13:13:28Z, so 14:10Z/14:12Z are impossible as UTC; they are 13:10Z/13:12Z (or 14:10/14:12 CET).
Fix: correct the two times (keep one convention; the rest of the record uses `…Z`).

**MINOR-2 — the truncation `runs_used/trials` examples are one campaign's cells, not per-W aggregates.** Locations:
report lines 143–145; STATUS line 12. `8/8, 10/12, 12/22, 16/40` are the `a2u` rep-0 root `tracks_S05_digits_mlp__s30500`
(and its fork) at W8/10/12/20; the binding row counts are 50/50, 50/50, 47/50, 2/50. `16/40` is not "the non-binding
count"; the non-binding row count at W20 is 48/50. The corrected direction ("binds at low W") is right. Fix: label the
four ratios as an illustrative campaign (or report the per-W range), and distinguish the binding **row counts** from
the run/trial pairs.

**MINOR-3 — calibration-gate wording.** Location: report line 141; STATUS line 12 ("the aggregate gate is Phase-4
with `tabular_mlp`"). The numbers are correctly descriptive-only and no pass is claimed, but the gate is **per node**,
not "aggregate", and on these rows it computes `fail` (0.5385/0.6742/0.9444). Fix (or answer): state that the per-node
gate is part of the deferred S0.5 summary and that the digits rows currently fail it (failing stratum 0 / over-coverage
⇒ STOP for the author per Phase 4); keep it descriptive and not accepted.

**MINOR-4 — `trks-status` prints a legacy STOP line.** Location: report line 104 ("no STOP line"). The pinned-HEAD
section has no `STOP:` line, but the manifests section prints `STOP-file present` for the old Oct-30 `smoke` manifest.
Fix: say "no STOP in the pinned-HEAD checks; the legacy `smoke` manifest still reports `STOP-file present` (pre-existing,
not this run)".

**MINOR-5 — TASL-7 bare repo is behind and only TASL-2's deferral is disclosed.** TASL-7 is up, but its
`trackS-ops-20261030` is `d8ac944c` (13 Nov 12:26Z; 15 commits behind `a504a604`), and the record mentions only the
TASL-2 bare-push deferral (runbook §0.8 asks for both hosts' bare repos). Fix: push `a504a604`/`ba64517b` to the TASL-7
bare repo, or state that the host bare-repo push is deferred to loop close. (No effect on the record's correctness.)

**MINOR-6 — session #1 pause cause wording.** Location: report line 30 ("`status=paused` on a Track X priority
marker"). `watch.log` records the only 13 Nov marker event at **13:47:35Z** (the STOP mtime), 44 min **after** the
collector's 13:03:00Z exit; the evidence fixes the STOP/inode/sha and the "no scene change" disposition, but not a
marker-triggered 13:03:00Z pause. Fix: record the actual 13:03 trigger from evidence (the STOP creation at ~13:00:52Z
is not attributed in the committed capture), or say "paused; the STOP was later re-touched by the watcher at
13:47:35Z". This is a session-#1 documentary issue; it does not affect session #2 or the result.

**Observation (not a finding).** The local worktree is one commit behind origin (`ba64517b`, docs-only); fast-forward
before committing this file. `e7417c5e` is a superseded alternative line (parent `92680170`) preserved only on the local
backup branch; it is not part of the unit. A transient 0-byte `~/r1_locks/trks.lease` was visible at 13:17Z and gone at
13:22Z; it is not the GPU lease (`gpu0.lock` was free throughout) and is not part of the run.

## 8. Explicit answers to the two questions

**Copy-back defect fix — was it fixed without altering the parallel record?** **Yes.** The defect was real: `e008abfb`
committed only 13 of the 23 `SHA256SUMS` entries; `.gitignore` (`*.jsonl`, `*.log`, `_to_delete/`) silently dropped the
6 top-level ledgers, the retired STOP and the 3 collector/launch `.log`s. `b846251e` force-added exactly those 10 files
(and renamed `logs/`→`host_logs/`), `a0a4c7cb` added the nested `operator_capture/SHA256SUMS` to make the index 40
entries, and `a504a604` fixed the stale "37/39 files" text and added the TASL-2 gap. The parallel record's **result
bytes** were not altered: `manifest.json` and `scripts/` are byte-identical, every pre-existing payload hash survives,
and each of the 10 added files matches the hash `e008abfb` itself pinned. Only the `SHA256SUMS` index was extended
(necessarily, that is the fix). The copy-back now verifies 40/40, host==copy 25/25, and the retired STOP is 0 B,
inode 57048847, sha `e3b0c442…`, not deleted.

**TASL-2 host-down deferral — properly disclosed, not silently skipped?** **Yes**, with the caveat in §6: the merged
report's provenance paragraph and the STATUS line 13 state that the TASL-2 bare push is deferred because TASL-2
(`portal_zhixu`, 100.120.160.70) is unreachable by TCP timeout, that it will be retried when TASL-2 returns, and that
TASL-2 was not touched. I reproduced the TCP timeout and confirmed the local TASL-2 ref is unchanged (`78a1b65e`,
12 Nov). The only defect is the mislabelled "14:10Z" (MINOR-1); the deferral itself is disclosed, not skipped. The
TASL-2 scene itself could not be re-censused while the host is down.

## 9. What remains open for STOP 4 (digits-half acceptance is *not* STOP-4 completion)

- **`tabular_mlp` half** — not run; STOP 4 waits for it.
- **Mac-side S0.5 summary** (`python -m r1.tracks.analyze s05-summary --node digits_mlp=… --node tabular_mlp=…`):
  must produce W, σ_cmp,vary, σ_D UCL, between-repetition UCL, `between_policy_sd_at_cap`, the near band b, the
  calibration status and λ. On the present digits rows the per-node gate is **`fail`** (strata 0/1-2/>=3 =
  0.5385/0.6742/0.9444); per Phase 4 that is a **STOP for the author** (failing stratum 0 / over-coverage), and the
  summary must report it. This review's acceptance of the digits half is **not** a calibration-gate pass, **not**
  Phase-4 completion, and **not** an S3 authorization.
- The six MINOR items above (documentary/timestamp/wording, plus the TASL-7 bare-repo push) should be answered or
  fixed before the STOP-4 summary; none changes the run, the numbers or the copy-back.

Verdict: accepted
