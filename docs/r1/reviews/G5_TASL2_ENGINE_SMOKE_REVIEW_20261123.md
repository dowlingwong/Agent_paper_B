# TASL-2 G.5 engine ENGINEERING smoke — independent review (23 November 2026)

**Reviewer.** Fresh independent reviewer (`g5-smoke-reviewer`), delegated by the lead; no involvement in the smoke,
its spec builder, driver, fake engine, captures or report. Read-only: the only file written by this review is this
review. No edit/commit/push/delete of any repository or host artefact; no run of the smoke, the driver, the fake
engine, the paper/harness code, the smoke's `run_all.sh`, or any GPU workload; no HTCondor/deepthought; TASL-7 was not
contacted. TASL-2 was read with `ssh -o BatchMode=yes portal_zhixu` using read-only commands only (`ls`, `cat`,
`find`, `stat`, `du`, `sha256sum`, `sha256sum -c`, `tar -xOf`, `nvidia-smi --query-*`, `oomctl`, `systemctl --user
show|list-units`, and `git --no-optional-locks -C <repo> rev-parse|status`); nothing under the smoke root, any
checkout, `runs`, `sealed_*`, `~/r1_locks` or `~/r1_trackp` was written, and no lock was taken. Local checks used
`git show 76a3c71f:<path>` on already-present objects and `git bundle list-heads` on the delivered harness bundles
(each read-only).

**Object under review.**

- Report `docs/r1/reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123.md` — **20,945 B, 163 lines, sha256
  `469cdac87aa9506f142a961051170b74d63df1e4c3d5716664108adab772997f`**; untracked (`??`) in the
  `ops-tasl-20261116` worktree (HEAD `9253192f`), not on published `main`.
- Capture bundle `docs/r1/reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123_captures/` — **57 files = 56
  hashed + `SHA256SUMS`**; `SHA256SUMS` **5,534 B, sha256
  `a13b7fdb48954c9728a3ba9595ab0be0952efce4d4c90f6e4a8996e92d201ffc`**; `sha256sum -c` verifies all 56.
- Host smoke root `/home/dowling/r1_engineering/tasl2_g5_smoke_20261123/` (TASL-2, uid 1008) — inspected
  read-only. Its host-side capture assembly `_bundle/` is **byte-identical** to the Mac capture bundle
  (`SHA256SUMS` same sha, `diff` of every listed path empty); the final runs tree has 21 attempts and its
  `runs_job_artifacts.sha256` (63 entries) verifies on the host.
- Paper checkout `/home/dowling/r1_tracks/t1_tasl/paper_g5smoke` detached at `76a3c71f…`, clean; harness
  `harness_g5_7` at `52e3c0b0…`, `harness_g5_ar` at `00829da1…`, both clean, `audit_g5.py` sha256
  `1089dbac962d8dace9a7fd124309ee9354bef6e44fbdb5ec1b7a9dc6d3d3d2d4` at both; shared `harness_g5` clean at
  `52e3c0b0…`. `g5_job.py` at `76a3c71f` is byte-identical (`1a8179d7…`) to the accepted G.5 follow-ups tip
  `15877e877`.
- Authority: harness report `G5_ENGINES_20261123` §6 items 1–15 (harness unit accepted at `94a41a7f`/`0aa27e31`,
  confirmed at `40396dc6`/`134b0399`) and paper follow-up `G5_FOLLOWUPS_20261123` §3 / its review (READY 96,
  accepted at `54bafc4a`, confirmed at `15877e87`).

**Verdict: ACCEPTED** for the ENGINEERING_ONLY smoke record, with the corrections in m1–m8 below. No
**BLOCKING/MAJOR** finding was found: every exercised item and every READY-96 addition is supported by evidence that
I re-verified against the host, and the two NOT-EXERCISED items (4 and 13) and the literal-`g5` limitation (item 15)
are disclosed rather than overclaimed. The report is **not** a G.5 authorization: items 4, 13, the real C3/C5 census
timing, the real per-wave disk sizes, the real CPU-only node, the engines' own attribution logic and the literal
`t1_tasl_node.sh g5`/note/launch-switch path remain for the EVIDENCE path (§5 below).

## Findings

**No BLOCKING, no MAJOR.** The eight points below are report-accuracy/housekeeping corrections; none changes a
measured result or an item status, and none is evidence of tampering with real data.

**m1 — The "No deletion" sentence is not accurate for the smoke's own earlier trial.** §4 says "trial/superseded
trees were moved aside to `_moved_aside/` on TASL-2". On the host, `_moved_aside/runs-20261124T053206Z/…` contains
only the 05:31:16Z orphan trial (`smoke_orphan/campaigns-wave1/attempt-1` + its `_refusals` record), while
`_moved_aside/captures-jobs-20261124T053206Z/` holds 23 captures and `logs/job-job-20261124T0521…–T052631Z` holds
the raw logs of a **complete earlier trial (05:21:56Z–05:26:31Z)**. That earlier trial's `runs/` tree is nowhere on
the host: no `job_record.json`/`attempt.json`/`out.tar` from 05:22–05:27 exists under `/home/dowling` (or `/tmp`),
and the earlier captures' `attempt_dir` points at `…/runs/g5smoke-engineering-20261123/smoke_ok/…/attempt-1`, a path
that now holds the final run's attempt (`started_utc 05:32:08Z`, different record/out-tar shas). So at least one
superseded trial tree was removed rather than moved aside. **Impact: none on the delivered evidence** — the final
run's 21 attempts and the 63-entry artefact manifest are intact and verify — but the sentence must be corrected (or
the removed tree restored) before the report is cited as the housekeeping record. This does not touch real T1 data,
sealed trees or Track P (verified separately in §3).

**m2 — The capture set was completed by hand after `run_all.sh` stopped, and `run_all.sh` was edited after the run.**
`logs/status.txt` ends at `2026-11-24T05:33:27Z FINAL hygiene`; it contains no `ANALYZE`/`DONE` line, and
`analyze.log` has no `analyze_rc=` line. Yet `analyze.log`/`smoke_summary.json` are from 05:33:52Z,
`repo_and_hygiene_checks.txt` from 05:35:27Z, `runs_job_artifacts.sha256`/`smoke_code.sha256` from 05:35:36Z, and
`_bundle/SHA256SUMS` from 05:35:43Z. The delivered `bin/run_all.sh` mtime is 05:33:42Z — **after** the run ended.
`logs/final_hygiene.txt` (05:33:52Z) contains `== lease flock test ==`, `== gpu ==` and `== user timer/procs ==`
sections that the delivered `bin/run_all.sh` (sha256 `3a5f7b27…`) does not produce, and host `captures/SHA256SUMS`
(run_all.sh's step-6 output) does not exist. So §7's "One smoke run (the full driver …)" does not describe how the
delivered capture set was produced, and the delivered `run_all.sh` is not provably the script that ran. **Impact:
none on the measured results** (the summary was generated from the final runs tree, and every final artefact
verifies against the manifest), but §6/§7 must disclose the manual completion/assembly and the post-run script edit,
and the `_bundle/` directory (the actual source of the Mac capture set, including the `code/`, `logs/` and `spec/`
copies and the `SHA256SUMS`) is not named in §6. If the record is to be archived as reproducible, re-run the full
driver once cleanly.

**m3 — The specific `oomctl` sub-claim in item 10/§2(c) is true on the host but not in the captured evidence.**
§2(c) says "`oomctl` monitors `user@1006/1008.service`, not the scope". I read `oomctl` on TASL-2 now: it does list
`/user.slice/user-1006.slice/user@1006.service` and `/user.slice/user-1008.slice/user@1008.service` under "Memory
Pressure Monitored CGroups", so the sentence is correct. But `probe_scope.json`'s `oomd_lines` only contains lines
matching the scope unit / "Monitored CGroups" / "Default Memory" because `driver.cgroup_scan` filters `oomctl`
output that way; the two `Path:` lines are dropped, and in the capture the lists read as empty. The required check
("systemd-oomd does not act on the scope", `oomd_monitors_scope=false`) **is** evidenced; the 1006/1008 specifics are
not. Fix: capture the raw `oomctl` output, or drop the specifics from the report.

**m4 — "byte-equivalent scope launcher" (§5 residual 2) overstates the equivalence.** The scope-creation argv is
identical to `t1_tasl_node.sh`'s g5 kind (`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G
-p MemorySwapMax=0 --`), but the in-scope launcher is `bin/inner.sh`, a functional replica of the wrapper's
`bash -c '…' t1_tasl "$HERE/$SCRIPT" …`, not byte-identical to it. Say "identical scope argv with a replica
in-scope launcher" (the report's "engineering-equivalent" is otherwise correct).

**m5 — Item 15 wording: the refusing `g5_tasl.py` call is pre-scope, not "in-scope".** §1 item 15 says "its first
in-scope `g5_tasl.py` call refuses … (`…`, wrapper rc 2, no scope started)". In `t1_tasl_node.sh` the first call is
`g5_tasl.py cpus` **before** `systemd-run`; the log confirms no scope was started. Remove "in-scope" (the substance —
fail-closed refusal, rc 2, no scope — is verified).

**m6 — "the operator then killed both pids" (§2(d)/§3) is scripted, not a human operator.** `bin/driver.py`
`cmd_orphan` performs the clear (SIGKILL of the sibling scope's pids, then terminate the sibling scope) as a
simulation of the operator rule. The refusal/clear/rerun results are real and pass; the report should say the driver
simulated the operator rule, not that "the operator" did it.

**m7 — Two PASS headlines are mechanism-only and should be marked PARTIAL/NOT-EXERCISED for the item as written.**
Item 9 is "Timing against the census (C3, C5)" but only synthetic values (99 s vs 5 s; 10 s vs 65 s) were used, and
item 14 is "the size of `out/` per campaign wave against free disk" but only the 51,200 B synthetic tar and 374.6 GB
free space were measured. Both cells disclose this ("synthetic basis", "mechanism; real sizes not exercised"), so
nothing is hidden; a stricter label (`PARTIAL` / `NOT-EXERCISED` for the specified measurement) would be cleaner.
Similarly §1 item 5 says "the real `smoke_ok` audit chunk" — the chunk is synthetic (the check `g5_seal.reduce_rows`
is real); and item 12's `smoke_cpu` is a synthetic `device: cpu` node, not the real CPU-only `mlgym_houseprice` (the
job's CPU branch keys on `node["device"]`, so the code path is the same, and the synthetic-node substitution is
disclosed globally in the Method paragraph, but not in the item).

**m8 — Evidence bookkeeping (host-only evidence, check labels, one disclosure).**
- The raw wrapper/scope logs and the cited `logs/job-kill-…log` (`logs/job-kill-job-20261124T053325Z-510763.log`,
  `deliberate_engine_kill pid=510923`, `kill_signal_ok=1`) are **host-only**; the 56-file bundle's `logs/` holds only
  the thin `run_all` logs. The same is true of the campaign-ledger members inside `out.tar` (item 8; I verified the
  `not_run_duplicate` line on the host has top-level `"code_state_sha256": "S1"`). Either cite host paths explicitly
  or add the files to the bundle.
- `repo_and_hygiene_checks.txt`'s "trackp lease/logs untouched check" lists `~/r1_locks`, not Track P
  (`/home/dowling/r1_trackp`), and its sealed-trees list omits the existing `sealed_dryrun_20261121`. I verified
  independently that no file under `~/r1_trackp`, `runs/`, `sealed_*` or `~/r1_locks` changed after the smoke start,
  so the §4 claim holds; the evidence file should be corrected.
- §5 does not disclose that the job-deadline scenario reaches `TimeoutExpired` by `bin/driver.py` setting
  `g5_job.STARTUP_RESERVE_S = 60` (a test hook); the `TimeoutExpired`/`cgroup.kill`/STOP 9 path itself is real.
- §4's "No commits/pushes" is evidenced only by a clean detached-HEAD status line; no remote check was made. No push
  was run by any captured command (clone/status/checkout only), so the risk is low, but the sentence is not
  independently verified.

## 1. Harness report §6 items 1–15 — item-by-item verification

Status is the report's; "Review" is what I could re-verify. Evidence locations are the report's and the host's.

| # | Report status | Review | Verification |
|---|---|---|---|
| 1 | PASS (job-side) | PASS | `smoke_ok` campaign tar 13 members / audit tar 6 members; binary members `out/campaign/instance_*/runs/s001/work/model.pt` (4) and `out/audit/runs/weights.npy` (1); job ok. |
| 2 | PASS (job-side; engine simulated) | PASS | Fake engine `ALLOC_GIB = 9` in `ar_oomworker`/`ar_oomparent` under the real scope; scope `memory.events` `oom`/`oom_kill` 0→1→2; rows `divergent` with `nonzero_exit` (worker_rc −9) and `oom_kill_memory_limit` (parent_rc −9); engine rc 0, job ok, wrapper rc 0; `memory_events_cgroup` = the scope. |
| 3 | PASS (job-side; engine simulated) | PASS | Worker raise rc 1 and `ctypes.string_at(0)` rc −11; both rows `divergent`/`nonzero_exit`; job ok; no infrastructure failure. |
| 4 | NOT-EXERCISED | NOT-EXERCISED (justified) | Needs the reviewed engine's re-materialised normalised `code_state_sha256` on a real campaign; the fake writes synthetic hashes, `chunk_record.units_rematerialised = 6` is written but `g5_job` does not read it, and the assembly-side reader for the field was not run. Correctly deferred. |
| 5 | PASS | PASS | Real `g5_seal.reduce_rows(spec, rows, chunk, "traindev")` on the synthetic `smoke_ok` audit chunk: `read_rows` 60, `traindev_rows` 30, `evaluation_rows_dropped` 30, `ok=true`. |
| 6 | PASS (job-side) | PASS | `g5_job.read_rows` ran on the 60 `smoke_ok` rows (job ok); the fake engine writes the exact `ISOLATED` block (`effective true`, `waivers {}`, `exceptions []`, `log_intact true`, no parent fields, no `gate_refusal`); negative control `smoke_gate` gives exactly `STOP 2: audit run ('B', 7001) is not effectively isolated (stop_unisolated)`, class `node`. The engine's own `noise_floor.check_effective` gate was not run (disclosed). |
| 7 | PASS | PASS | One synthetic final `infrastructure_failure` row → exactly `STOP 7: final infrastructure failures in the audit chunk after the engine's reruns (a new attempt after diagnosis)`, class `infrastructure`; rows `[infrastructure_failure, ok]`. |
| 8 | PASS (record-shaped) | PASS (record-shaped) | Host `out/campaign/instance_1_history/campaign_ledger.jsonl` `step 20 decision not_run_duplicate` carries top-level `"code_state_sha256": "S1"`; `diagnostics.counts.duplicate = 4`; the assembly-side reader was not run (disclosed). |
| 9 | PASS (synthetic basis) | mechanism PASS; real census NOT-EXERCISED | Slow-run campaign gives the timing STOP (class `timing`), and normal runs give `run_median_over_basis: 0`; basis 5 s / 65 s are synthetic — real C3/C5 values were not used (m7). |
| 10 | PASS | PASS | Host `systemd 249 (249.11-0ubuntu3.23)`; scope `memory.oom.group = "0"`, `memory.max = 8589934592`, `memory.swap.max = "0"`, no `OOMPolicy`; `oomd_monitors_scope = false`; `ManagedOOMMemoryPressure=auto` on `user@1008.service`; the OOM was a kernel memcg OOM (`memory.events` rose), not a userspace kill. The 1006/1008 specifics are host-true but uncited (m3). |
| 11 | PASS | PASS | Job `TimeoutExpired`: `run_cgroups_kill.left = []`, `run_cgroups [ar_deadline_…]`, STOP 9 node; deliberate `kill -9`: engine rc −9, `left: []`, infrastructure STOP for missing rows; no populated `ar_*` after either (empty dirs removed and recorded in `cleaned_empty_ar_dirs`); `probe_scope.kill_probe.kill_write_ok = true`. |
| 12 | PASS | PASS (synthetic CPU node) | `smoke_cpu`: campaign + audit ok; engine argv has no `--gpu-uuid`; `CUDA_VISIBLE_DEVICES=""`; `record.gpu = {"device":"cpu"}`. Not the real `mlgym_houseprice` (m7). |
| 13 | NOT-EXERCISED | NOT-EXERCISED (justified) | No llama-server was started and TASL-7 was not contacted (fake proposer `get`); `TruncationInvalidManager` is only a contract string in the records. Correctly deferred. |
| 14 | PASS (mechanism) | mechanism PASS; real sizes NOT-EXERCISED | Attempt holds only `SHA256SUMS, attempt.json, diagnostics.json, job_record.json, out.tar`; synthetic campaign `out.tar` 51,200 B; free disk 374,598,488,064 B (~349 GiB); real per-wave sizes were not measured (m7). |
| 15 | PASS (engineering-equivalent; literal `g5` NOT-EXERCISED) | PASS as engineering-equivalent; literal NOT-EXERCISED | 23 real `g5_job.run_job` calls (21 main wrapper scopes: 20 attempts + 1 start refusal; plus 2 orphan-scenario calls: 1 start refusal + 1 attempt); every one of the 21 job records has `cgroup.cgroup_parent` matching `user@1008.service/app.slice/run-r[0-9a-f]{32}.scope`; `affinity` 16–31. Literal wrapper: pre-scope `g5_tasl.py cpus` refuses the ENGINEERING_ONLY spec (`STOP: spec must be g5_tasl_labels/v1, label EVIDENCE`), wrapper rc 2, no scope, `literal_g5_wrapper.log`. |

## 2. READY 96 additions (`G5_FOLLOWUPS_20261123` §3 / follow-ups review open items)

| Addition | Review | Evidence |
|---|---|---|
| (a) real scope path contains `user@<uid>.service` | PASS | All 21 job records' `cgroup.cgroup_parent` = `…/user-1008.slice/user@1008.service/app.slice/run-r<hex>.scope`; `probe_scope.user_manager_component_present = true`. |
| (b) sibling `app.slice` scopes readable | PASS | `probe_scope.siblings` reads 5 units' `cgroup.events`/`cgroup.procs` (`readable: true`), incl. `smoke-sibling-probe-507774.scope`; the orphan test read a populated `ar_*` in a default-named sibling `run-r7e628b…scope`; the start-of-job scan refused. |
| (c) `memory.oom.group = 0`, systemd-oomd leaves the scope alone | PASS | `probe_scope` and `smoke_oom` `cgroup_after`: `memory.oom.group "0"`, `oomd_monitors_scope false`, `ManagedOOMMemoryPressure=auto` on `user@1008.service`; host `oomctl` lists `user@1006/1008.service` and not the scope (see m3 for the capture gap). |
| (d) no `ar_*` processes after deadline STOP / deliberate kill; clean after an orphan before the next job | PASS | Deadline and kill: `run_cgroups_kill.left == []`, no populated `ar_*` after, empty dirs removed and recorded. Orphan: populated `ar_*` → start refusal naming `run-r7e628b…scope`: "`STOP: ar_* run cgroups of this or an earlier job's scope hold processes: 1 populated ar_* run cgroup(s) in unit(s) run-r7e628b…scope; operator rule: inspect user@<uid>.service/app.slice/*/ar_* …`"; both pids killed (`cleanup.killed [511990, 511991]`), `ar_left []`, `scope_gone true`, rerun ok (`run_cgroups_kill.left []`). |
| Refusal names an old scope in `run-r…`/`run-u…` form | PASS | Refusal text names `run-r7e628b3ff3c244908a06aa7bb9c51b49.scope`; no `ar_*`/seed names. |
| `check_engines` passes on both families (four needles); `truncation_invalid_in` recorded | PASS | Host `harness_g5_7@52e3c0b0`/`harness_g5_ar@00829da1` clean, `audit_g5.py` sha256 `1089dbac…`; `real_engines.*.check_engines` returns the full contract (marker, both schemas, class needle); every job record has `engine.truncation_invalid_in = autoresearch.trackg.audit_g5.TruncationInvalidManager`. |
| Gate refusal → STOP 2, node class, through the job | PASS | `STOP 2: audit run ('B', 7001) is not effectively isolated (stop_unisolated)`, `stop_class node`. |
| Engine's own deadline STOP through the job, both engines | PASS | Campaign and audit `stop_kind=deadline` → `STOP 9 … (stop_kind deadline; its text is sealed in out.tar)`, class `node`; the next job on `smoke_stopdl` is refused (`STOP: smoke_stopdl has a STOP on record …`); the secret marker never reaches a clear file (`secret_in_clear_files=false`, `engine_log_has_secret=true`). |
| Exit-time check on a clean exit: `out/run_cgroups_kill.json` with `left: []` | PASS | All 21 completed attempts contain `out/run_cgroups_kill.json` with `left: []` (incl. rc 0); attempt entries are exactly the five expected files. |

## 3. Setup and housekeeping — verified

- **Paper**: host `paper_g5smoke` HEAD `76a3c71fe94082e0c1274a1200c7e103a06b90bf`, `git status --porcelain` empty;
  `g5_job.py` `1a8179d7…` (= accepted follow-ups tip `15877e877`), `g5_tasl.py` `a4e873de…`, `t1_tasl_node.sh`
  `8c39844e…`, `g5_tasl_spec.json` `b25fd7f1…` — all match the report/captures.
- **Harness**: `harness_g5_7@52e3c0b0…`, `harness_g5_ar@00829da1…`, shared `harness_g5@52e3c0b0…`, all clean;
  `audit_g5.py` `1089dbac…` at each; delivered harness bundles' heads (`git bundle list-heads`) are exactly
  `52e3c0b0…` and `00829da1…`.
- **Real data untouched**: `r1_tracks/t1_tasl/runs` still holds the five real runs only; `sealed_g1b` (mtime
  20:56 Nov 23 local), `sealed_g4` (Nov 22), `sealed_dryrun_20261121` (Nov 21) and `~/r1_locks` have no files newer
  than the smoke start (Nov 23 21:20 local = Nov 24 05:20Z); no file under `/home/dowling/r1_trackp` is newer than
  the smoke start (Track P untouched — the report's evidence file mislabels this check, m8).
- **No G5 label/evidence row/seal**: the synthetic spec is `g5_tasl_labels/v1` with `label: ENGINEERING_ONLY`;
  the literal wrapper refuses it; the job diagnostics carry the code constant `label: EVIDENCE`, disclosed in §4,
  and the synthetic attempt records are under the engineering root, unsealed and outside `…/runs`/`sealed_*`.
- **No GPU model work**: the fake engine loads no model; the 9 GiB OOM child is CPU (`numpy`) in the scope's memcg;
  GPU nodes only receive `--gpu-uuid` (ignored by the fake), `CUDA_VISIBLE_DEVICES=""`; host GPU at the end:
  353 MiB / 0 % and no compute apps.
- **No HTCondor**; **TASL-7 not contacted** by design (the proposer is `fake_get`; the server record is synthetic) —
  "TASL-7 untouched" cannot be observed from TASL-2 beyond this no-contact design.
- **Clean end state (host, now)**: no `run-*.scope`, no `ar_*` under `app.slice`, only the four system units, no
  smoke processes, GPU 353 MiB / 0 %, `~/r1_locks/gpu0.lock` present (the captured `final_hygiene.txt` records
  `lease_free`).
- **No deletion of real data**: confirmed (see m1 for the one smoke-owned superseded `runs/` tree that is missing).

## 4. Captures, hashes, safety

- Report sha256 `469cdac8…` (20,945 B, 163 lines) and captures `SHA256SUMS` sha256 `a13b7fdb…` (56 files) match the
  task; `sha256sum -c` passes on every file; host `_bundle` is identical to the Mac bundle; the host final-run
  artifact manifest (63 entries = 21 attempts × `job_record.json`/`diagnostics.json`/`out.tar`) verifies with
  `sha256sum -c`.
- The 21 final-run attempts all have `affinity 16-31`, identical attempt entries (`SHA256SUMS`, `attempt.json`,
  `diagnostics.json`, `job_record.json`, `out.tar`), `run_cgroups_kill.left == []`, and `secret_in_clear_files
  == false`; the two deadline/kill attempts are the only ones whose `engine.log` lacks the secret marker (the engine
  was killed before it printed — expected).
- The report's §6 hash table matches the delivered bytes (`smoke_summary` `96f6c2ea…`, `probe_scope` `2a7edd5a…`,
  spec `6bd1fc97…`, server record `6db701da…`, `driver.py` `c34a779a…`, wrapper `4ee5f1d5…`, fake engine
  `ae527620…`, real `audit_g5.py` `1089dbac…`).
- Incidents: every non-ok job is an intended STOP/refusal with the expected class (STOP 2 node `smoke_gate`,
  STOP 7 infrastructure `smoke_infra`, timing `smoke_timing`, STOP 9 node `smoke_deadline`/`smoke_stopdl`/
  `smoke_stopdl_a`, deliberate-kill infrastructure STOP for missing rows, `stopdl` next-job refusal, orphan start
  refusal). No unexpected incident; nothing left behind.

## 5. Conditions before a G5 authorization / EVIDENCE run

1. Fix m1–m8 in the report (in particular correct or restore the "No deletion" claim, disclose the manual
   capture-set assembly and the post-run `run_all.sh` edit, and name `_bundle/`); ideally re-run the full driver
   cleanly once so §7's command reproduces the delivered set.
2. The EVIDENCE path must exercise, and capture, what this smoke necessarily deferred: item 4 (real campaign
   re-materialised normalised `code_state_sha256` and `units_rematerialised`), item 13 (truncation on the real
   TASL-7 llama-server: `usage.completion_tokens == 4096` on `finish_reason: length`), the engines' own attribution
   logic (items 2/3 outcomes), item 9 against the real C3/C5 census basis, item 14 with real per-wave `out/` sizes,
   and item 12 on the real CPU-only `mlgym_houseprice` node.
3. Exercise the literal `t1_tasl_node.sh g5` path (signed note + launch-valid spec + `g5_tasl.py` launch switch) at
   authorization. The smoke only proves the fail-closed refusal; the note/launch-switch checks are not exercised.
4. No EVIDENCE label/row/seal before the signed note; keep the engineering synthetic records (which carry the fixed
   `label: EVIDENCE` in diagnostics) out of `/home/dowling/r1_tracks/t1_tasl/runs` and `sealed_*` (verified they are
   outside now).
5. Reconcile the engine-commit citation for the authorization: the smoke used `harness_g5_7@52e3c0b0` /
   `harness_g5_ar@00829da1` (delivered bundle heads; `audit_g5.py` `1089dbac…` = the accepted file hash) while the
   harness review record names the confirmed commits `40396dc6`/`134b0399`. State which commit the G5 authorization
   binds; the engine bytes are the accepted ones (not blocking).
6. If the capture bundle is to be cited as the smoke's evidence, add the raw `oomctl`, the raw wrapper logs (or at
   least the cited `job-kill-…` log) and the campaign-ledger members, or keep their host paths explicit.

## 6. What I checked (summary)

Local: report/captures hashes and `sha256sum -c`; report/§1–§7 text; harness report §6/§7/§8/§9;
follow-up §3 and its review; paper `76a3c71f` file hashes vs `git show`; `g5_job`/`g5_seal`/`g5_tasl` readers;
harness bundle `list-heads`; fake engine and driver source; all 22 captured job JSONs and the summary; the
host-vs-Mac capture diff. Host (read-only): smoke root, `_bundle`, `_moved_aside`, `runs` (21 attempts), logs
(status, raw wrapper logs, `job-kill` line, `final_hygiene`), paper/harness checkouts and status, real runs/sealed/
Track P mtimes, current scopes/ar_*/GPU/`oomctl`, `sha256sum -c` of the final artefact manifest, and the earlier
trial reconstruction. Not checked: TASL-7 state or network, any remote ref of the repositories, or any content of
the sealed/real T1 runs.

*AI-assisted (Claude). ENGINEERING_ONLY: this review is not evidence, not a label run and not an authorization.*
