# Track G G.0 U2 `mlgym_houseprice` — accepted MINOR record corrections (20 November 2026)

**Status: record corrections APPLIED (no smoke/U2 re-run, no unit/code edit, no deletion, no commit/push).**
Correction window: **2026-11-20T22:25–22:32Z** (result and notes stamped `2026-11-20T22:30Z`). This note is the
change record for
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_20261120T215244Z/`; the result itself carries a
Correction note with the same date/UTC.

**Authority.** Accepted result review
`docs/r1/reviews/TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` sha256
**`b2c463a7941891b115ca2b89037e1f2fef0c760582b65dd709add54641202134`** (ACCEPTED — 0 BLOCKING, 0 MAJOR, 10
result-specific + 5 shared-standard MINOR, conditions H1–H10/S1–S5). Underlying: accepted R2 unit review sha
`81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51` (R2-reviewed unit bytes
`397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551`), round-1 review sha
`36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025` (NOT ACCEPTED), executed unit sha
`0f13d2dc5d59bc487658018764d9517148540bc9cfe4b5313ba75435d77f94fe`; accepted kit update
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026` and its review
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`; worktree `ops-tasl-20261116` HEAD
`6bbf4b3e`, `origin/main` `df58bcd5`. Only files inside the result directory (plus this campaign note) were
written; no commit/push; no Ada write (read-only SSH).

## 1. New shas (old → new)

| object | old sha256 | new sha256 |
|---|---|---|
| result md `U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md` | `c043f0dd3bdf3337df6ca25b7cab075dbd92b4c59b6fec3e0d8f5d390369e178` | **`0b1212e3de41888ae77efa3bfbf3676fe7949e479737b561623d65503a171cf6`** |
| `SHA256SUMS` | `80a835243830471f3df406478455652cf286c93e991daed5b7b765b826cae84c` (445 entries) | **`7607fc5c8520bb558e54cb313f2e68b7a93760e4e316f8a676ef63b780af8066`** (447 entries) |
| `scripts/README.txt` (new, H8) | — | **`5d2db988fafa28eee94b409d7ededd0145167816a51656176bb63165ddc9dfd4`** |
| `prep/static_command_note.txt` (new, H5) | — | **`f778c2310599cb82bd345e2c2abcbd255c89520a83afe625f92854568978de4f`** |

**Changed files:** `U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md`, `SHA256SUMS`, and the two new record files
above. **No existing capture was modified** (all existing captures are byte-identical to live Ada — §4 — so none
needed refreshing). No file deleted; the executed unit and both unit reviews in `references/` remain
byte-identical to the repo files.

## 2. Conditions applied

- **H1 — attempt-2 timing corrected.** `21:52:44Z` is the runner/evidence-dir start (`logs/run_node.log:1`);
  gate JSON `utc 21:52:50Z`; gate check and scope/probe/prechecks `21:52:52Z`; the smoke starts after them; the
  gate precedes the launch (launcher runs the gate before `systemd-run`).
- **H2 — disk-after from the capture.** Now **`70,795,374,592 B`** (and before `70,644,187,136 B`) from
  `disk_before.txt`/`disk_after.txt`; the runner's `RESULT_STATUS` `disk_avail_after_bytes` (`70,795,313,152 B`)
  is named as a different `df` sample and not the source.
- **H3 — truncated per-CPU census + v1 parser artifact.** The co-tenancy claim was narrowed to the
  load/mpstat/users/nproc evidence; the per-CPU list is `ps -eLo … | head -40` (exactly 40 root-kernel-thread
  rows in the "foreign processes on the selected cpus" section, the node's own process cut), so "no other user's
  process was observed" is **not established** by it; the preserved
  `cpu/cpu_summary.v1_parse_artifact.txt` (sha `077de1c1…`, `foreign_users_on_selected_cpus=['root','the']`) is
  disclosed as a parse artifact; corrected capture is `cpu/cpu_summary.txt`.
- **H4 — prepared-data copy / `AR_DATA` wording.** Corrected: the author's `train.csv` is the verified
  `--from-file` source; **`prepare_data.py` writes the prepared `<out>/houseprice.csv` as a byte copy** of it
  (`prepare_data.py:69`; same sha256/md5, different inode — live read-only: author inode `66606474`, prepared
  inode `78787219`). No separate staging copy and no MLGym copy; the `AR_DATA` line records
  sha256/md5/`same_as_mlgym_copy`, not the `--from-file` path, which is recorded by `prep/setup.log` and the
  manifest's `provided_by`/`from_file_name`.
- **H5 — static-test command/mask reconciled.** New `prep/static_command_note.txt` cites the accepted kit-update
  helper `run_static_tests.sh` (live sha `7a9d57fa…`, whose header/footer format and scope line match the
  capture) and its exact command/mask (`systemd-run --user --scope -p Delegate=yes`, `taskset -c 0-15`,
  `CUDA_VISIBLE_DEVICES=`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, `envs/torch312/bin/python -m pytest
  tests/trackg -q -p no:cacheprovider -k "not smoke"`), and explains that `static_launcher.log` is empty because
  the helper redirects output to the static log. The static test was not re-run.
- **H6 — executed-unit R2 residues vs the C1–C4 claim.** Header corrected: the amendment applied the one
  mandatory pre-execution defect (one-physical-line launch command) and removed the truncated pin literal; the
  C1–C4 **substance** is implemented in the launch/result records, while the executed unit text still carries
  R2 MINOR residues (m2/m6/m7/m8/m9/m13/m14/m15/m16). A dedicated section records the unit-vs-launch/result
  split and states the launch/result records are the operative form; the executed unit bytes were **not
  amended** in this record-only pass.
- **H7 — cpuset-selection window and mid-sample wording.** Corrected to the captured samples: harness before
  snapshot selected-set mean idle **80.0 %** (`cpu_before.txt`/`cpu_summary`) + runner's separate one-sample
  check **97.4 %**, i.e. two 1-s samples both ≥ 80 % — **not** a captured 3-sample minimum; the mid snapshot is
  early in the 43.97 s smoke right after the smoke process exec'd, not during the fit.
- **H8 — v1 verifier source/patch residual recorded.** New `scripts/README.txt` records the one-line change from
  the v1 equality check (`node_spec_sha256 expected`, 8/8 issues, comparing against the spec **file** sha
  `1b95447d…`) to the fixed full-64-hex **canonical** check (`spec.raw_sha256 = 2f150cde…`, verified live); the
  v1 source/patch itself was not preserved (only the fixed script + v1 outputs). No reconstruction was guessed.
- **H9 — `s002` bare `NaN` labelled.** The divergent run's `sealed.test_rmse` is the bare literal `NaN`
  (non-strict JSON, non-finite) in `runs/runs_smoke/s002/run_record.json:264`; labelled non-finite/not-used; no
  measurement impact. The run record itself was not edited (it is a preserved run capture).
- **H10 — corrected status authoritative.** The result restates that the historical first `STOP` block in
  `RESULT_STATUS.txt`/`DONE` is the verifier false-negative history and that the appended corrected `PASS` block
  (fixed verifier rc 0 + kit helper `issues: []` + `gate_ok: true`) is authoritative for the census/commit.
- **S1 — record identity added.** New section gives the result path and its post-correction sha (via the
  `SHA256SUMS` entry and this note), the `SHA256SUMS` sha, the canonical `node_spec_sha256` loader formula and
  value (`2f150cde…`), E1–E4 diff shas (`3ee108ef…`, `7e4a71a0…`, `81eaa685…`, `e9a1e8e9…`), the executed
  unit/review shas, and the one-JSON-line-per-run statement (`verify_full.json` `json_run_lines: 9`).
- **S2 — no-resume + filesystem.** Added "no resume (an interrupted unit re-runs wholly from a new
  `<runs-root>`; none occurred)" and named the filesystem `/dev/md0p3` on `/`.
- **S3 — full authority shas.** Kit update `fe232e2bbf23…`, kit review `d8c68f9f04…`, R2-reviewed unit
  `397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551`, round-1 review
  `36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`, result review `b2c463a794…` now cited
  full 64-hex.
- **S4 — "preserved unaltered" + live/Mac split.** Reworded; the live dir holds the **417 raw capture files
  only** and the live attempt-1 dir **22 files** (both byte-identical to the local copies); the **30 local-only
  entries** (31 files incl. `SHA256SUMS`) are the Mac-authored records (result md, `SHA256SUMS`, 22 attempt-1
  copies, 3 `references/`, 2 `scripts/` sources, + the 2 correction-pass files).
- **S5 — "verifier records both" corrected; 2.9 G sourced.** The fixed verifier's rows record only the canonical
  `node_spec_sha256`; the spec file sha `1b95447d…` is cited from `kit.txt:11`. The whole-data-root **2.9 G** is
  now cited to a live read-only `du -sh /home/dowling/r1_trackg_20261117/data` = 2.9 G (this correction pass), as
  it is not in the run's disk captures.

## 3. Verification

- `SHA256SUMS` regenerated over every file in the result directory except itself and verified with
  `shasum -a 256 -c SHA256SUMS`: **rc 0, 447/447 entries OK** (448 files including `SHA256SUMS`); the two new
  files are listed; the result md's new sha is the `./U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md` entry.
- **Live-Ada cross-check (read-only, no write):** every one of the **417** live evidence files is byte-identical
  to the corrected local capture (0 mismatches, 0 live-only); every one of the **22** live attempt-1 files is
  byte-identical to the local `attempt1_prelaunch_cpu_idle_stop/` copies; local-only = 30 entries (Mac-authored
  records + the 2 new files), as expected. Live read-only re-checks: canonical `node_spec_sha256` `2f150cde…`
  (kit loader), data root `du -sh` 2.9 G, author/prepared CSV sha256 `1e18addf…` both, inodes `66606474` vs
  `78787219`, live `run_node_houseprice.sh` `360b2053…` and `verify_u2_records_cpu.py` `63a4bdf1…`
  (byte-identical to the copies), static helper `run_static_tests.sh` `7a9d57fa…`, evidence dir/file modes
  `drwxrwxr-x`/`-rw-rw-r--`.
- No measured number changed. No unit/code, pin, manifest, run record, CPU/disk/gate capture, verifier output or
  existing capture was modified; **no smoke/U2 work, no re-run, no deletion, no commit/push, no
  HTCondor/deepthought action.**

## 4. Residuals (recorded, not guessed)

1. **H8:** the v1 verifier source and fix patch were never preserved (live script edited in place); only the v1
   outputs and the one-line rule description in `scripts/README.txt` exist. A byte-exact v1 source cannot be
   reconstructed without guessing.
2. **H5:** the exact static-test command line is not echoed in the static-test capture; it is reconciled from the
   accepted kit-update helper (`run_static_tests.sh` sha `7a9d57fa…`) whose log format matches the capture. The
   static test was not re-run.
3. **H6:** the executed unit text still carries the R2 MINOR residues (m2/m6/m7/m8/m9/m13/m14/m15/m16); this
   pass was record-only (no unit edit) and the launch/result records are stated as the operative form.
4. **H3:** the per-CPU process list remains capped at 40 rows, so the absence of foreign processes on the
   selected cpuset is not established by the capture; the load/mpstat/users/nproc evidence supports the
   co-tenancy PASS and the limitation is disclosed. The v1 parser artifact remains preserved/disclosed.
5. **H7:** the claimed 3-sample stable-idle selection window was never captured; the record now cites the two
   captured 1-s samples (80.0 % and 97.4 %) instead.
6. **H9/H10:** the bare `NaN` literal in `s002`'s run record and the first `STOP` block in
   `RESULT_STATUS.txt`/`DONE` remain in the byte-faithful captures by design; both are labelled/reconciled in the
   result (no capture edit, no Ada write).
7. **S5:** the 2.9 G whole-data-root figure comes from a post-run live `du -sh` (this pass), not from a run-time
   capture; it is correct but not a run-time capture.

## 5. Attestation

Written locally in `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116` plus
read-only SSH to Ada (`ssh -o BatchMode=yes experiment_zhixu`, no writes, no smoke/GPU work). Commands: reads of
the review/result/captures/unit/reviews; `shasum -a 256`/`shasum -a 256 -c`; Python reads of the run records and
verifier JSON; `cp`/`write` of the two new record files; regeneration of `SHA256SUMS`; live `sha256sum`, `stat`,
`du`, `find`, `grep`, `cat`, read-only kit-loader canonical-spec recomputation. No smoke, no retry, no unit/code
edit, no deletion, no commit/push, no TASL/HTCondor/deepthought action.
