# TASL-2 AR-pin host-check STOP review — §3.3 Python `3.12.16` vs the required `3.12.15` (22 November 2026)

**Reviewer.** Fresh independent reviewer (`ar-pin-stop-reviewer`), delegated by the lead; no involvement in writing
the procedure, the run scripts or the STOP report. Read-only: the only file written is this review. No run,
code/record edit, commit/push/delete, HTCondor action and no GPU workload. TASL-2 was inspected with read-only
`ssh -o BatchMode=yes portal_zhixu` commands (`git rev-parse/status/merge-base/reflog/show-ref/worktree list`,
`sha256sum`, `stat`, `readlink`, file reads, `find`, `nvidia-smi` queries, `ps`, and a `flock -n` lease test on the
existing lock file). The submitted checks were **not** re-run and no Python was executed on TASL-2: the
interpreter is established statically from the symlink chain plus the submitted captures. (One transient `/tmp`
checksum log for `sha256sum -c` was created and removed in the same command; nothing under the run root, the T1
trees, the two checkouts, the venv or any repository was written.)

**Object under review.**

- STOP report `docs/r1/reports/g1b_ar_20261122/TASL2_ISOLATION_HOST_CHECK_AR_PIN_20261122_STOP.md` — 112 lines,
  10 175 bytes, sha256 `57e1c7b9c145b88bac22c4f0af745715002dd091107eaa57eb5f005c4b929033`; untracked (`??`) in
  `ops-tasl-20261116`.
- Its sibling captures `TASL2_ISOLATION_HOST_CHECK_AR_PIN_20261122_STOP_captures/` — 45 files (44 listed +
  `SHA256SUMS`), 228 KiB, `SHA256SUMS` sha256
  `00f2a9cbab135438ef97a7982714aa9a34dcd0084cf02b613dd7be589b33688e`; the host digest file
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/SHA256SUMS.sha256` (sha256 `86dd15e4…`) records
  that value.
- Procedure `docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md` — 194 lines,
  12 686 bytes, sha256 `9c32bca35be057b27b752aeeeb7f39c3154c3875bd66f08efdb31a049c30d881`.
- Host evidence root `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/` (live).
- Authority as the report states: R1-G1B-NOTE2-DECISIONS (NOTE2-AR A: the third note is signed only once "a TASL-2
  host check at that pin passes"), i.e. the AR-ENV / NOTE2-AR A host gate. The procedure is not a launch
  authorization.

**Verdict: ACCEPTED — the STOP is correctly fired and its evidence is accurate. 0 BLOCKING, 0 MAJOR, 6 MINOR
(conditions C1–C6; report/procedure text and capture provenance only — no evidence re-run is needed for this STOP,
but the host check itself must be re-run after the AR-ENV decision, as the report says).**

The run stopped exactly where the procedure says it must: §3.3 requires `3.12.15`, the spec interpreter now resolves
to `3.12.16`, and §7 ("The freeze or Python of `ar-cond7a` differs from §3") is a report-and-wait STOP. Sections 4–5
(data staging, C1–C7, the supplementary pytest, the AST CUDA-IPC scan) were not started, no `host_check_*` record
line was written, no binding record was placed, and the spec's `hosts.TASL-2.isolation_host_check.sha256` is still
`TODO`. Every capture is byte-verified locally and on TASL-2, and every load-bearing number in the report
reproduces or is cross-checked independently. The Python change is **host drift after the census, not a test error**
(§3 below). The
remaining decision is the author's AR-ENV choice; the report correctly lists the options instead of taking one.

## 1. Checkout (§1) — verified

- `harness_ar`: `git rev-parse HEAD` = `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`; detached (`symbolic-ref` rc 1);
  `git status --porcelain --untracked-files=all` **empty**; `merge-base --is-ancestor c025f89a… HEAD` rc **0**;
  `git worktree list` has one entry; `origin_branch` = the pin; the reflog is exactly `clone` (`3c80b53`, `main`)
  → `checkout` to `2d09f9a`, i.e. no local commit and no push; GitHub `ls-remote
  https://github.com/dowlingwong/autoresearch_harness.git mac-trackg-t1-ar-20261121` still returns `2d09f9a…`
  (so the branch HEAD is unchanged — no push of a new commit); the worktree's `.git/index` mtime is
  `2026-11-22 02:42:04` and was unchanged by my read-only `status`.
- Seven-node checkout `/home/dowling/r1_tracks/t1_tasl/harness`: HEAD `c025f89aeafc2199bf3487b4bcaa16678273c702`,
  detached, `stash list` empty, tracked tree clean; the four pre-existing untracked `data` symlinks are present
  with mtimes `2026-11-21 02:32:55`, `14:42:49`, `14:52:56`, `19:25:23` and targets under
  `/home/dowling/r1_tracks/t1_tasl/data/…` — same before/after and now (the captured before/after status lists
  match). Its `.git/index` mtime is `2026-11-21 01:54:31` (no write since the 21 Nov work).
- Pre-state: `harness_ar` was **absent** before the run (`pre_existing_state.txt`; `host_facts.json`
  `repos.harness_ar.exists=false`), so the script's move-aside branch could not and did not fire;
  `/home/dowling/r1_tracks/t1_tasl/_to_delete` does not exist; `r1_locks/_to_delete` holds only the old retired
  lock (Oct 25 / Nov 16). No collision, no deletion.

## 2. Node pins (§2) — verified independently

All four pinned values match the procedure and the AR spec. Three were recomputed from host bytes; the fourth
(`spec.raw_sha256`) is a canonical hash of the parsed YAML, so it was cross-checked against the manifest's and the
AR spec's declared `node_spec_sha256` rather than recomputed here (no PyYAML on the review host). They are content
hashes, so the `3.12.16` interpreter used to compute them does not invalidate them.

- Spec file `configs/trackg/nodes/autoresearch_fixedtokens.yaml` sha256 = `5bdce00a…` (recomputed directly on
  TASL-2).
- `representative_edits/manifest.json` sha256 = `55f2666a…`; its `node_spec_sha256` is `5c1bdf3d…`, the same value
  the run reports as the spec's canonical `raw_sha256` and the AR spec declares as `node_spec_sha256`.
- All **20** pinned files match the captured `pin_entries` (I re-hashed every one on TASL-2); `frozen_entries=20`.
- The committed pin `147f0d35…` reproduces exactly: `sha256(json.dumps(pin_entries, sort_keys=True))` with the
  harness's own canonical form (no `data` link entry) gives `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`.
- `nodes/autoresearch_fixedtokens/data` is absent (`data_link_present=false`), as §4 was not started.

## 3. Environment (§3) and the drift — the STOP is correct and is host drift, not test error

- `uv` = `uv 0.13.6 (x86_64-unknown-linux-gnu)` — PASS.
- Freeze: 122 lines, sha256 `11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`; the fetched
  `env_freeze_uv.txt` is **byte-identical** (`cmp`) to committed `sweep2/g1b/env/ar-cond7a.freeze.txt` (same sha),
  so the venv's package set is untouched — only its base interpreter moved.
- torch `2.6.0+cu124`, CUDA `12.4`, `cuda_available=True` — PASS.
- Python: `…/venvs/ar-cond7a/bin/python` is a `2026-10-25` symlink to uv's **unversioned** `3.12` alias
  (`…/cpython-3.12-linux-x86_64-gnu/bin/python3.12`); `pyvenv.cfg` `home` is the same unversioned alias; the alias
  itself is a symlink with mtime `2026-11-21 01:53:39.822 -0800` (**09:53:39.8Z**) to
  `cpython-3.12.16-linux-x86_64-gnu`; `readlink -f` gives `…/cpython-3.12.16…/bin/python3.12`, whose binary
  carries the `3.12.16` string. The `cpython-3.12.15-linux-x86_64-gnu` install directory is still present
  (`2026-10-25`) but unreachable through the venv chain. No file under `ar-cond7a` was modified after the run
  (no install, no bytecode).
- Drift chronology: the U2 census capture `TASL2_AR_COND7A_RESULT_20261121_captures/env.txt` says
  `python=Python 3.12.15` at `2026-11-21T02:30:30Z` (smoke `01:58:19Z–02:28:10Z`); the T1 precheck capture
  `TASL2_T1_PRECHECK_20261121_captures/env_uv.txt` says `utc=2026-11-21T09:53:36Z`, `uv python install 3.12.16`,
  "Installed … in 3.04s" → the alias retarget at **09:53:39.8Z** is exactly that install completing; the 3.11 and
  3.13 unversioned aliases share the same retarget second (one `uv` alias update). So the census venv was
  untouched, and the shared alias was moved by the precheck's `uv python install` (7.4 h after the census), which
  silently changed what the "unchanged" venv resolves to. This is host drift, **not** a check bug: the requirement
  and the observed interpreter are both correctly read, and the STOP follows.

## 4. Sections 4–5 not started; non-actions — verified

- No step-4/5 logs; `scripts/run_checks.sh` is phase-A only and the STOP exited before §§4–5; no C1–C7 capture, no
  pytest log, no AST CUDA-IPC scan.
- Data: `/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens` **absent** (`AR_DATA_ABSENT`); the four
  existing data dirs and `t1_tasl/hf` keep `2026-11-21` mtimes (no Hugging Face download); no
  `nodes/autoresearch_fixedtokens/data` link in `harness_ar`.
- Binding/host-check lines: `grep -rn '^host_check_'` in the whole host run root returns nothing (rc 1); the target
  AR-pin binding file does not exist; the Mac worktree's only `^host_check_` lines are the legacy 21 Nov TASL-2 and
  TASL-7 records; `hosts.TASL-2.isolation_host_check.sha256` is still `TODO`. The host run root's `records/` holds
  only a copy of the STOP report (sha `57e1c7b9…`, byte-identical to the reviewed file), not a binding record.
- GPU/lease: lease free before and after, no compute apps, `GPU-4d623e76-…`, 353 MiB / 0 % — same before/after and
  now; the Track P attempt-1 archive and its lease log keep `2026-11-17 15:42:26.390… / 4096` and
  `15:42:35.402… / 55726` (`stat` unchanged); no T1 job in `ps`; T1 `runs/` and `sealed_g1b/` keep `2026-11-21`
  mtimes; nothing committed (reflog) and the GitHub branch head is unchanged (no push).

## 5. STOP logic and the decision that remains

The report's STOP/FAIL is the correct §7 outcome and it does not overstate: it says "no binding record was written;
this file is evidence, not a launch record and not an authorization", it does not retry, and it refuses to treat
the `3.12.16` as a host-check detail. The decision it leaves open is the author's AR-ENV call, and the report lists
the right four options (accept `3.12.16`; restore the census `3.12.15`; AR-ENV option B copy pinned to `3.12.15`;
AR-ENV option C uv rebuild at `3.12.15`, not recommended). Nothing in the STOP record takes that decision.

## Findings (all MINOR — text, citation or provenance; none changes the STOP or the evidence)

**m1 — §5 "The only host changes are the new run root and the second checkout" is not exact.** The two lease tests
open `~/r1_locks/gpu0.lock` with `exec 9>…`, so its mtime moved from `02:37` (preflight) to
`2026-11-22 02:42:04.636` (end state) — size/content remain 0, the lease *log* is untouched, and no lease was
taken. In addition, the post-STOP drift-evidence step refreshed uv's interpreter cache
(`~/.cache/uv/interpreter-v4/…/ee3634e3c19caf04.msgpack`, mtime `02:42:05`). Fix: say "no substantive host change;
the flock tests touched the 0-byte lock file's mtime and a uv cache entry; the lease log was not written", or open
the lock with `exec 9<…`. (Location: STOP.md §5, line 68.)

**m2 — §5 "seven-node checkout's `runs/` and `sealed_g1b/` trees" is mislocated and misdated.** Those trees are
under the T1 base (`/home/dowling/r1_tracks/t1_tasl/{runs,sealed_g1b}`), not under the checkout
(`…/t1_tasl/harness/` has neither); their mtimes are `2026-11-21 13:45/14:41`, and the capture set contains no
before/after `stat` of them. The "`stat` only; mtimes unchanged 2026-11-17" clause is true only of the Track P
attempt-1 archive and its lease log. Fix: reword, and add the two `stat`s to the rerun's preflight/end-state (they
are in fact untouched — live read confirms `2026-11-21`). (Location: §5, lines 70–71.)

**m3 — §7's "as the 21 Nov binding's method did" is wrong and must be corrected before the rerun.** The 21 Nov
binding recorded `git status --porcelain` **empty** before and after; it did not admit untracked artifacts.
Reading "clean at `c025f89a`" as tracked-clean/HEAD-unchanged is a *change* of method, not the 21 Nov method. Keep
the recommendation (define tracked-clean, or explicitly allow the four pre-existing `data` symlinks), but delete
the parenthetical and amend procedure §1.2 ("clean") accordingly; otherwise the rerun will hit an undefined
"clean". (Location: §7, lines 107–110.)

**m4 — "GPU never used" and "every Python step" need precision.** §3.3 executes
`torch.cuda.is_available()`, a CUDA driver availability query; it allocates nothing and holds no lease (the memory,
compute-app and lease evidence is consistent), but the sentence "The GPU was never used" should read "no GPU
compute and no lease; only the reported availability query". Likewise the two `-VV` prints at the top of
`run_checks.sh` are Python invocations not under `taskset` (every logged step is). Fix: wrap them, or narrow the
claim; also state that the git/stat/`nvidia-smi`/`flock` inspection commands were run without `taskset` (no T1 job
was running — preflight `running_jobs` empty), so the procedure's "every non-GPU step" wording is not silently
read as fully met. (Location: §5, lines 71–73.)

**m5 — the end-state and root-cause capture commands are not preserved.** `post_state.txt`,
`gpu_state_after_phaseA.txt`, `gpu_compute_apps_after_all_phaseA.txt`, `lease_status_post.txt`,
`attempt1_stat_after.txt` and `python_drift_evidence.txt` (all mtime `10:42:04Z`) were produced by commands that
are not in `captures/scripts/` (7 files, all phase A) or `captures/logs/`; the final `SHA256SUMS` was likewise
regenerated at `10:42:04.645Z` after them. Only the outputs are in the set. Fix: for the rerun, keep the
end-state/root-cause command (script or exact ssh line) in the capture set and disclose the run-root `records/`
STOP-report copy in §6. The outputs themselves are corroborated live, so nothing here is in doubt.

**m6 — the decision list is right but incomplete.** Add the variant "repoint the shared unversioned `3.12` alias
back to `3.12.15`", which restores the census venv *without editing it* (but is host-global and must be protected
against future `uv python install` alias moves, e.g. a pinned/versioned venv); and, if the author accepts
`3.12.16`, state that the census *timing* basis (`slowest_census_seconds` 255.916 s / timeout 767.748 s) was
measured under `3.12.15` and that the note/provenance text must say the launch interpreter differs from the census
interpreter (freeze and torch are unchanged, so the environment is otherwise the same). This is a condition on the
spec/note/procedure text, not on the STOP record.

## Conditions

- **C1 (m1):** correct §5 "only host changes" (lock mtime, uv cache) or say "no substantive change"; record the
  lease log as unwritten and the lock as 0 bytes.
- **C2 (m2):** reword the `runs/`/`sealed_g1b/` sentence (T1 base, `2026-11-21`), and `stat` those trees
  before/after in the rerun.
- **C3 (m3):** delete the "as the 21 Nov binding's method did" claim; define seven-node "clean" in the procedure
  and handle the four pre-existing `data` symlinks explicitly (allow them, or remove/relocate them) before the
  rerun.
- **C4 (m4):** narrow the GPU/taskset claims or make the exempt commands explicit.
- **C5 (m5):** preserve the end-state/root-cause command in the capture set and name the `records/` copy.
- **C6 (m6):** record the AR-ENV decision (accept `3.12.16` / restore `3.12.15` / B pinned / C) and align
  `envs.ar-cond7a.python`, the third note's env line, P7 and its Python STOP, procedure §3.3, and the spec-support
  environment row; add the alias-repoint variant and, for "accept", the census-timing/provenance caveat. No
  host-check rerun before C6; the rerun restarts at §1 and re-checks the pins and the freeze in the final
  environment.

## What this review does not establish

It does not decide the AR-ENV interpreter, it is not a binding record or launch authorization, and it does not
re-run the C1–C7 host conditions (they were never started). The STOP report is untracked; committing it is the
lead's action. The Python `3.12.16` was established statically (symlink chain, `pyvenv.cfg`, binary string) plus the
submitted execution capture, not by executing the interpreter on TASL-2.

**AI-assisted: DeepSeek Harness agent `ar-pin-stop-reviewer`, 22 Nov 2026. ENGINEERING_ONLY; uncommitted; the
reviewed STOP is accepted as evidence, not as a launch record.**
