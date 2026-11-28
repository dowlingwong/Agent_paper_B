# G.5 P11 complete matrix — independent engineering review R2, 28 November 2026

- Date: 2026-11-28 (Europe/Berlin). Independent reviewer, read-only. This is a review of the committed
  record only: no host was touched, no job, signal, edit or delete was made, and no host workload was run.
  The only write is this file, on the review branch.
- Deliverable: `origin/compute-g5-p11-matrix-complete-20261128`, round 1 at
  `b31b42feee724b682e11254bb0a95369d1c84e2d`, round 2 at
  `0ce1e664b9ef836f83c7f147bd24334184d896c5` (parent `b31b42fe`; base of the capture set `f963b1bb`;
  base code `f7dc4945`, harness `cbf7a003`). Record
  `docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md`, captures in
  `tasl2/` and `tasl7/`, `SHA256SUMS` at the record root.
- Scope: the four scenarios this unit adds on the free TASL-7 card — `-determinism`, `-restart`, `-tar`,
  `-closeserver` — and the coverage rows they move. The primary `-lease` matrix, `-infra`, `-closed` and
  the C11/TASL-7 chunk were accepted on the earlier record and were not re-opened; the only primary text
  changes are the result paragraph, the Files paragraph and the coverage/hash rows.
- Review branch: `compute-g5-p11-matrix-complete-20261128-review`, created from `b31b42fe`; the round-2
  commit updates this file only. The deliverable branch is untouched.

## Round 2 — re-check at `0ce1e664` (28 November 2026)

The fix commit is one commit after the reviewed tip. `git diff --name-status b31b42fe 0ce1e664` touches
exactly 20 paths: the record (`M`, +19/−6 lines), `SHA256SUMS` (`M`, one line — the record's own hash) and
the 18 force-added logs (`A`). No other content changed; no test, spec, seal or number was altered.

### Capture integrity — resolved

- In a fresh worktree checked out at `0ce1e664`, `git status --porcelain` is empty and
  `shasum -a 256 -c SHA256SUMS` returns **420/420 OK, exit 0**. The set is exactly closed: 420 payload
  files, 420 entries, **no unsummed file, no missing entry, no duplicate path**. The only sums line that
  changed is `./G5_P11_ENGINEERING_RERUN_20261128.md` (`37cc4014…`), which matches the edited record.
- The 18 added files are exactly the 18 round-1 misses: the 12 scenario node logs (538–742 bytes) and the
  6 `llama-server.log` files, and each hash equals the entry that was already in the round-1 sums.
- I re-extracted the six server logs from the captured `server-N.server.tar` files: the committed
  `*.llama-server.log` files are byte-identical to the tar members (determinism `c21576c6…`,
  restart-1 `cac45ec8…`, restart-2 `747c8b92…`, tar `730ccd24…`, closeserver-1 `fb6b7f08…`,
  closeserver-2 `ac77fdcb…`). No divergent copy was introduced.
- The newly committed node logs also corroborate the scenario timeline rather than merely hashing:
  the ten determinism campaign/chunk logs all end `NODE_EXIT=0` at the times the repeat records carry
  (09:10:52, 09:23:07, 09:34:02, 09:34:36, 09:12:06, 09:45:42, 09:56:42, 09:57:16); the restart log has
  `STOP 12 … Connection refused`, `NODE_EXIT=2`, end 10:02:40Z; the tar log has
  `STOP: out.tar could not be written; out/ kept for the seal`, `NODE_EXIT=2`, end 10:06:05Z.

### M1 — resolved, with the evidence now present

The two 08:37 logs read, in both nodes:

```
STOP: foreign compute processes on the leased GPU before the job:
      [{'pid': 1302930, 'used_memory': '21640 MiB'}] (no shared card)
NODE_EXIT=2
# end=2026-11-28T08:37:25Z
```

That is exactly the "refused before a job record" state the record now describes: no attempt directory,
no job record, no campaign rows; the sealed determinism campaigns start later with `NODE_EXIT=0` at
09:09:37/09:10:52. The record's new paragraph is accurate as to the refusal and the "no campaign from them
entered the run" claim. One small residual: the record attributes the holder to "the P7 server", while the
captured log names only PID 1302930 and 21,640 MiB. The attribution is consistent with the record's own
note that a P7 server ran on TASL-2, but it is not itself evidenced in this record; a one-line citation to
the P7 server record would close it. That is a note, not a blocker.

### Minors from round 1

- **m1 (server-1 wording) — fixed.** The record now says server-1 "was ended by the first kill attempt and
  its wrapper wrote an end record with `server_rc: -9`" and that it is the ordinary seal path, with the
  `close-server` receipt only on server-2. That matches `closeserver.server-1.server_end.json`.
- **m2 (C5 determinism deadline) — fixed.** The clause is gone; C5 now reads `PASS (primary)`, which is
  what the ten captured primary chunk `deadline_epoch` rows support.
- **m3 (probe/server-span stdout) — disclosed.** The Files paragraph now states that the `p11-probe` and
  `server-span` outputs were printed to the console and not saved, and points to the server records, seal
  receipts and the 0-open meter. The limitation is accepted and no longer an implied capture. Residual:
  the `-closeserver` lease/process checks ("lease free before, `gpu0.lock` free after") are still stated
  without a committed check file.
- **m4 (repeat-record `label: EVIDENCE`) — explained.** The record now says these are the synthetic
  engine's internal wire value and that the record and every seal are ENGINEERING_ONLY. This matches the
  code: `g5_p11_engine.py` re-labels only the primary `chunk_record.json`, not the replay record.
- **m5 (C15 REL-T1-G1B) — partly fixed.** The C15 row now names "the reviewed REL-T1-G1B copy in the
  primary record". The copy does exist on `main` (`docs/r1/reports/g5_rel_t1_g1b_20261126/seven/`, with
  `COPY_RECORD.json` hashes), but the row binds no digest and "in the primary record" is imprecise — the
  copy is in its own record, not in either P11 engineering record. Naming it is enough for the scope
  disclaimer; binding `COPY_RECORD.json`'s sha256 would finish the runbook instruction.

### Correction to round 1, and one residual

Round 1 said the missing `-restart` node log was "the only source of the `09:59:11Z` / `10:01:29Z` marker
times". That was an expectation, not a check: the now-committed restart node log carries only the job
start (09:59:07Z), the STOP 12 line and the end (10:02:40Z). The two marker times still appear nowhere in
the committed set — the marker files themselves are in the sealed `out.tar`, and `restart_markers.txt`
records only the names. The ordering and the STOP time are verified; the two marker timestamps remain
uncited prose. This is a residual minor, not a blocker; a `stat` capture of the two marker files or a
drop of the exact times would close it.

**Verdict: ACCEPTED**

The blocker and the major are closed on the files: the capture set is complete and hash-clean from a fresh
checkout (420/420), the 18 files are the right ones, and the 08:37 refusal is now both explained and
captured. No scenario number, PASS/PARTIAL status or seal changes. The residual items are documentation
precision only — the restart marker timestamps, the REL copy digest, the closeserver lease check files and
the P7 PID attribution — and none of them affects a reviewed claim.

## Round 1 (record at `b31b42fe`) — findings as raised

**Round-1 verdict: CHANGES REQUIRED**

The four new scenarios are real and, apart from the items below, their numbers reproduce exactly. The
blocker was capture integrity: `shasum -a 256 -c SHA256SUMS` failed on 18 listed paths, including every
node log of the four new scenarios and (as it turned out in round 2) not the marker times themselves.

## Round-1 verified items

All checks below were made in the committed record set at `b31b42fe`.

### `-determinism` — evidence holds

- Spec `1cc9f4d4e91fec02d7ef1ad257ee20065180babeb491217201e55c016cc865dc` is byte-identical in the
  `tasl2/` and `tasl7/` copies and equals `spec_sha256` in the server record and in both campaign job
  records.
- Server: PID 2748828, started `08:35:26Z`, stopped `09:57:20Z`, `span_seconds 4914.0` — 4,914 s
  (81 m 54 s) to the second. `server_end.json` carries `server_rc 0`, `stop_signal 15`, and the seal
  receipt binds record `cd71834e…`, end `16f51e8d…`, span 4,914 s.
- Campaigns: both nodes wave 1, `proposals 80 / ran 40 / kept 40`, `invalid`, `infrastructure_final`,
  `refused`, `timed_out` all 0, `ledger_stops.baseline_failed 0`, `stop: null` (both
  `campaign.job_record.json` and `campaign.diagnostics.json`).
- Audit chunks: six `determinism.json` members are `200/200/10` `same_fixed_seed_outcomes`; the six
  `repeat_chunk_record.json` members all have `expected_runs 200/200/10`, `diffs_recounted 0`,
  `infrastructure_reruns 2`, `stop: null`, `written_rows == expected_runs`, and the noise-floor gate
  `effective:true`. The six agrees with the record's "six repeat records agree".
- Chunk `diagnostics.json`: label-seed blocks 100/100/5 ok, 0 divergent, 0 infrastructure, `stop: null`,
  K = 10; the plan hash is the same for all three chunks of a node.
- `wave-checks` for both nodes: `stops: []`, `warnings: []`.
- Eight attempt seal receipts (two campaigns, six chunks), all with `stop: null`; the server seal is
  `cd71834e…`/`16f51e8d…`/`c21576c6…`, all three matching the files.
- Meter: proposer 4,914 s, 1 registered, 0 open, `gaps: []`; worker 0.791 GPU-h, which is the sum of the
  eight `gpu_seconds` values (2,846.1 s = 0.791 h).
- The record does **not** claim node/run seals for this scenario and explains why (wave 1 only, no node
  STOP). No overclaim there.

### `-restart` — evidence holds, one timing citation is not in the capture

- Spec `71571e37…` matches in all copies and in both server records and the job record.
- Server-1: PID 2758307, `09:58:06Z`–`09:58:39Z`, 33 s, record `8b768b1d…`, rc 0/signal 15.
- Server-2: PID 2759079, `10:02:19Z`–`10:02:46Z`, 27 s, record `e8ed4127…`, rc 0/signal 15. Meter
  proposer 60 s = 33 + 27, 2 registered, 0 open, no gaps. Worker 0.059 GPU-h = 213.1 s.
- Campaign: started `09:59:07Z`, finished `10:02:40Z`, `STOP 12: after the wave: <urlopen error [Errno
  111] Connection refused> (re-run as a new attempt)`, `stop_class: infrastructure`; identical text in the
  diagnostics. Attempt sealed (job record `d38acd55…`, diagnostics `49321120…`, `out.tar` `d694b9d5…`,
  all three matching the receipt).
- `restart_markers.txt` contains the two marker names. The claimed times `09:59:11Z` and `10:01:29Z`
  appear nowhere in the committed set; they are only in the node log, which is missing (see B1).

### `-tar` — evidence holds

- Spec `fed68f4c…` matches; server record `a94246b6…`, `10:03:49Z`–`10:05:35Z`, span 106 s; meter
  proposer 106 s, 1 registered, 0 open; worker 0.021 GPU-h = 74.0 s.
- Job and diagnostics carry `STOP: out.tar could not be written; out/ kept for the seal`,
  `stop_class: infrastructure`; `out_tar_sha256` is null.
- Seal receipt: `out_clear_files: 1130`, `out_clear.tar` `07c6a35dffae71c5c27780c36115b6e4ae43affb17289e59531fca002ce187d9`,
  plus the job-record hash `8347652f…` and the node-log hash `7fc87cff…`. The sidecar
  `….out_clear.tar.sha256` repeats the archive hash.
- I recounted the listing independently: 1,920 entries = 790 directories + **1,130 files**, matching
  `out_clear_files` and the archive hash receipt. The archive itself is correctly absent; the listing and
  the receipt bind it.

### `-closeserver` — evidence holds

- Spec `324db598…` matches in both server records.
- Server-1: `10:05:59Z`–`10:06:20Z`, 21 s, record `4154b044…`, seal `closed: false`.
- Server-2: `10:06:47Z`–`10:07:07Z`, 20 s, record `967801cc…`; `server_end.json` has `closed: true`,
  `end_basis: "closed_at"`, `reason: "P11 engineering server interruption"`, `stopped_utc 10:07:07Z`,
  `closed_by: g5_seal`, rc/signal null, `latest_log_mtime_utc 10:06:50Z`; the seal receipt repeats
  `closed: true`, end hash `bed5f477…`, span 20 s.
- Meter: worker 0.0, proposer 41 s = 21 + 20, 2 registered, 0 open, no gaps.
- All six scenario server records (determinism, restart 1–2, tar, closeserver 1–2) have
  `foreign_before.foreign: []` and the declared argv `-c 32768 -np 1 -ngl 999`, q8_0 K/V, one slot.

### Coverage, integrity, overclaim

- C2 PASS: supported (campaigns, six chunks, K = 10, re-materialisation/isolation receipts, six repeat
  records).
- C7 PASS: supported (primary stop/restart plus this scenario's stop-before-start and the server-2 probe).
- C10 stays PARTIAL: correct — the multi-day part remains STOP 12; the record says so.
- C15: the `-tar` failure, `out_clear.tar` and `-closeserver` closed_at path are supported; the row's
  `PASS (assembly/release not yet)` does disclaim the two gated parts (see m5 for the rel-copy).
- The record is ENGINEERING_ONLY throughout, asks for one fresh review, and makes no G.5 note, label,
  test-read or release claim. The release negative control is still a refusal before evidence.
- Pins are consistent: every new job record has `engineering_paper_commit f7dc4945…`,
  `harness commit cbf7a003…`, `label ENGINEERING_ONLY`.

## Round-1 findings

### B1 (blocking) — `SHA256SUMS` fails: 18 listed captures are absent

`shasum -a 256 -c SHA256SUMS` at the record root returns **402 OK / 18 failed, exit 1**. Every file that
is present is correctly summed (no unlisted files, no duplicate paths), so the sums were regenerated
correctly over a staging tree that was not fully committed:

| Missing group | Count | Consequence |
|---|---:|---|
| `./tasl2/<node>-<stamp>.node.log` for the four new scenarios | 12 | The node logs of every new campaign/chunk job are absent. Four attempt seal receipts bind their hashes (`2c2d07c6…` restart, `7fc87cff…` tar, and the ten determinism chunk/campaign logs). The `-restart` marker times have no other source. |
| `./tasl7/<run>.server-N.llama-server.log` | 6 | Absent at the listed path. All six are present and hash-correct **inside** the captured `server-N.server.tar` (e.g. determinism `c21576c6…`, restart-1 `cac45ec8…`, closeserver-2 `ac77fdcb…`), so the evidence exists, but the sums path does not. |

Two of the missing node logs, `mlab_imdb-20261128T083724Z-1308394` and
`mlgym_breakout_minatar-20261128T083725Z-1308708`, are **not attributed by any captured job record or
seal receipt**; they precede the sealed determinism campaign attempts by about 32 minutes. Either they
belong to this record set — in which case the record is silent about whatever ran at 08:37 — or they do
not, in which case they should not be in the sums.

This is a regression against the parent record, whose sums were 289/289 OK at `f963b1bb`. The cause is
`.gitignore:3 (*.log)`: the new commit did not force-add the logs. The earlier capture commit
(`f963b1bb`) explicitly force-added its ignored logs; this one did not.

**Fix:** force-add the 12 node logs (which makes the receipt-bound hashes checkable; the round-2 re-check
shows they do not carry the marker times), either force-add the six `llama-server.log` files or drop their
lines from the sums, account
for or exclude the two 08:37 logs, then regenerate `SHA256SUMS` and re-run `shasum -c` to exit 0.

### M1 (major) — the determinism campaign has an unexplained 32-minute gap before the sealed attempt

The determinism server runs from `08:35:26Z`, but the sealed `mlab_imdb`/`mlgym_breakout_minatar` wave-1
campaign records start at `09:09:37Z`/`09:10:52Z`. The only traces of activity in between are the two
unattributed node logs above, with PIDs 1308394/1308708 (the sealed campaigns use PIDs 1356359/1357965).
The record describes the campaigns as clean (`stop: null`) and mentions no earlier run, while its only
disclosed failure in this period is the kept 04:38 server refusal. If an earlier attempt was started and
abandoned, the record should say so; if not, the two logs should be accounted for. The absent node logs are
exactly the files that would settle it, so this cannot be closed from the current set.

### m1 (minor) — `-closeserver` server-1 is not a "normal end"

The record says server-1 "had a normal end (21 s span) … the ordinary path". Its captured
`server_end.json` reads `server_rc: -9`, `stop_signal: null` — i.e. the child was killed, not stopped with
signal 15. Every other server end in the record (primary 1–2, infra, determinism, restart 1–2, tar) is
`rc 0 / signal 15`. The C15 contrast still holds (server-1 has a wrapper-written end record and
`closed: false`; server-2 has `closed_at`), but "normal end" should read "wrapper-written end record",
with the SIGKILL stated.

### m2 (minor) — the C5 sentence about `-determinism` is not in the capture

The C5 row says "the `-determinism` chunks 0–2 also record the formula". The captured determinism audit
artifacts are `chunk{0,1,2}.diagnostics.json` and `repeat_chunk_record.json`; neither has a
`deadline_epoch` (or any deadline field), only `timeout_factor 3.0` and `measured_run_seconds`. The primary
chunk `job_record.json`s do carry `deadline_epoch`; the determinism chunk job records were not captured.
Either capture them or drop the clause; the primary ten-row C5 table is unaffected.

### m3 (minor) — `server-span`, probe and lease results for the new scenarios are claimed but not captured

- The four new runs have no `server_span_*.json` or `_server_spans/` registration, yet the record claims
  `server-span` rc 0 (`-determinism`) and "accepted both server receipts" (`-restart`). The meter's
  `registered` counts (1/2/1/2) are consistent with the registrations, but the artefacts are missing.
  This is the same class as the earlier accepted review's MINOR-2 for the primary.
- `tasl2/g5-p11-…-determinism.probe1.json` is 0 bytes, and there is no probe capture for
  `-restart`, `-tar` or `-closeserver`. The campaign `server_props_before` fields do confirm the identity
  for determinism/restart/tar; `-closeserver` has no job record, so its "probed" claim has no artefact.
- The runbook asks for the process and lease checks to be preserved for `close-server`; the record states
  the lease was free before and `gpu0.lock` free after, but no check file is committed.

### m4 (minor) — the six repeat records carry `label: EVIDENCE`

Every other artefact in the set is `ENGINEERING_ONLY` (specs, job records, diagnostics, receipts), but the
six `out/audit-repeat/chunk_record.json` members say `"label": "EVIDENCE"`. This is the engine's default
record: `g5_p11_engine.py` re-labels only the primary `chunk_record.json` (`rec["label"] =
"ENGINEERING_ONLY"`), not the replay's. The replay is synthetic and the record does not claim an evidence
run, but the captured metadata contradicts the headline and should be disclosed (or the replay record
re-labelled before sealing).

### m5 (minor) — the C15 `PASS` scope does not mention the REL-T1-G1B copy

R1-G5-P11's pre-run C15 set includes "the REL-T1-G1B copy", and the smoke runbook tells the record to
"retain the earlier reviewed real REL-T1-G1B copy and bind its digest in the coverage record". The C15 row
and the Files section mention neither the copy nor a digest, so `PASS` is broader than what this record
cites. Assembly and release are correctly disclaimed; the rel-copy is simply unaddressed. The same table
still has no rows for C1/C3/C8/C13; those are covered, if at all, by earlier records the record does not
cite. I did not treat the inherited rows as blocking, but the "complete item table" wording should point
to the earlier records it relies on.

## Notes (not findings)

- `tasl2/incoming/g5-p11-…-determinism/server-1.json` is 0 bytes and hashes as the empty file; it is a
  failed copy, not the server record. The real record is in `tasl7/` and is correct.
- The record's "eight attempt receipts … all rc 0" has no `rc` field in any receipt; the `stop: null`
  fields and the successful seals support the claim, but it is inference rather than a captured exit code.
- The `-restart` campaign saw the server already down (server-1 ended `09:58:39Z`, campaign started
  `09:59:07Z`), so it demonstrates a controlled stop-before-start → STOP 12, not a restart mid-wave. The
  record's ordering is accurate; only the label "restart" could mislead a casual reader. The primary
  record's restart around the C11 chunk remains the mid-run evidence.
- `-tar` diagnostics show `inert: 40` with `kept: 40`; the record makes no count claim for that scenario,
  so this is only a fixture observation.

## Round-1 closing ask (met in `0ce1e664`)

Force-add the 12 scenario node logs (and the six server logs, or drop their sums lines), regenerate
`SHA256SUMS` so `shasum -a 256 -c` exits 0, and answer the 08:37 gap. The m1/m2 wording fixes and the
m3–m5 capture/citation gaps can be handled in the same pass; none of them changes a scenario's PASS/PARTIAL
status or any number already in the record. All of this was done in the round-2 commit; only the residual
notes above remain.
