# Independent review — R1-TRACKP-I2-MEM `request_memory` change (23 November 2026)

Reviewer: `reviewer-i2-mem`, independent and read-only. Scope: the single on-deepthought edit of the I2 probe
submit file `/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/i2/probe.jdl`
(`RequestMemory` 8,000 MB → 2,000 MB), the author row that authorizes it, the measured-need basis, and the job
state the change was meant to act on.
Method: read-only `ssh` commands only (`sha256sum`, `diff`, `cmp`, `cat -A`, `stat`, `wc`, `sed`, `ls`, `ps`,
`condor_q`, `condor_history`, `du`); repo records through `git show`/`git grep`/`git rev-parse` at commit
`9e207d3f` and at the current `origin/main`. No job was submitted, edited, held or removed; nothing was written on
deepthought; no credential/secret file was read. The only write is this review. Review time 2026-11-23
≈17:02–17:06 CET (16:02–16:06Z); deepthought's filesystem and condor logs are on CET (its `date` at review time:
`Mon Nov 23 17:03:58 CET 2026` / `16:03:58Z`).

The publishing main is `9e207d3f` as named by the task (2026-11-23 16:42:04 +0100, `docs(r1): R1-TRACKP-I2-MEM`);
`origin/main` has since advanced to `14f19a09` (16:55:30 +0100), a merge that keeps `9e207d3f` as a parent. The
author row text is identical at both (PLAN.md line 1451). Every "main" citation below is at `9e207d3f` unless
stated.

## Bottom line

**NOT ACCEPTED as a gate for `condor_rm`/resubmit.** The JDL diff itself is exactly the authorized change and is
byte-for-byte correct (one value, one line, nothing else touched; see the deterministic proof below). The problem
is not the edit — it is the operation this review was asked to gate: **job 759982 is not present and idle. It
completed successfully at 2026-11-23 16:20:05 CET (15:20:05Z), ExitCode 0, with `I2_PASS`** on the reviewed CPU
image digest. `condor_q 759982` matches 0 jobs. `condor_rm 759982` would be a no-op, and a resubmission would be a
redundant re-run of a check that has already passed. The JDL change needs no correction and may stand for a future
I2 run; no job action is warranted, and the gated `condor_rm`/resubmit must not be executed.

## Artifact and hashes

Directory `/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/i2/` on `deepthought.etp.kit.edu` (user
`dwong`).

| File | sha256 | Bytes | Lines | Mode/owner | mtime (CET) |
|---|---|---|---|---|---|
| `probe.jdl` (**after**, current) | `d79d8ef8105b9ae57b7377193434566ac9c09a9fbb19ef16c10236955a07d082` | 485 | 16 | `644 dwong:cms` | 2026-11-23 17:02:22.672 |
| `probe.jdl.before_memory_change` (**before**) | `89fdc6afdf38cc9960161f01874ff34f155bf27aad2f640d50ddab415cf6be2c` | 485 | 16 | `644 dwong:cms` | 2026-11-23 17:02:22.668 |
| `probe.jdl.before_disk_change` (previous step's before, context) | `afa811bc15eddba885858724dad26b7baf4250fcb1af1c029535214d1a22a93a` | 486 | 16 | `644 dwong:cms` | 2026-11-23 10:23:22.896 |
| `probe.jdl.orig` (21 Nov original, context) | `fde29f60a3d3540fe8bfbe3ed16d9562cc6bbdca426eb7327cc4ed2eacbe9de0` | 486 | 16 | `644 dwong:cms` | 2026-11-21 23:28:16.233 |

The **before** hash `89fdc6af…` is exactly the **after** hash recorded for the earlier, separately reviewed
`request_disk` edit (`docs/r1/reviews/I2_DISK_CHANGE_REVIEW_20261123.md`), whose before-file was `afa811bc…`; the
10:23:22.896/.900 mtime pair matches. So the chain of custody is clean: `fde29f60` (original) → v2.1 CPU image pin
→ `afa811bc` → (disk edit) → `89fdc6af` → (this edit) → `d79d8ef8`. This review's object is the last step.

Both compared files are mode `644`, owner `dwong:cms`, and have identical 16-line structure under `cat -A` (no CR,
no trailing whitespace, no newline change). Sizes are equal (485 B) because `8000` and `2000` have the same length.

## Diff (before → after)

```diff
--- probe.jdl.before_memory_change
+++ probe.jdl
@@ -10,7 +10,7 @@
 log = s4.log
 +RequestWalltime = 3600
 RequestCPUs = 2
-RequestMemory = 8000
+RequestMemory = 2000
 request_disk = 2000000
 requirements = TARGET.ProvidesETPResources
 queue 1
```

`diff -u` returns a single hunk with a single `-`/`+` pair. `cmp -l` reports exactly one differing byte:
byte 407 (decimal), old `070` octal (`8`) → new `062` octal (`2`); the exit status is 1 (files differ) for that
byte only. The change is `RequestMemory = 8000` → `RequestMemory = 2000`, in MB.

## Deterministic proof that nothing else changed

```text
sha256( sed 's/^RequestMemory = 8000$/RequestMemory = 2000/' probe.jdl.before_memory_change )
  = d79d8ef8105b9ae57b7377193434566ac9c09a9fbb19ef16c10236955a07d082
sha256( probe.jdl )
  = d79d8ef8105b9ae57b7377193434566ac9c09a9fbb19ef16c10236955a07d082   (identical)
```

The current file is byte-for-byte the backup with only that one substitution, so every unchanged field is
confirmed by construction, not merely by visual diff:

| Field (JDL line) | Before | After | Verdict |
|---|---|---|---|
| `universe` | `container` | `container` | unchanged |
| `container_image` (CPU digest) | `docker://ghcr.io/dowlingwong/r1-htc-cpu@sha256:c152c32980ccd708a9b5fda0a1da49b963064ebcbc608849406adf0c95bdf148` | same | unchanged |
| `executable` | `s4_run.sh` | `s4_run.sh` | unchanged |
| `arguments` | `"$(ClusterId).$(ProcId)"` | same | unchanged |
| `should_transfer_files` / `when_to_transfer_output` | `YES` / `ON_EXIT` | same | unchanged |
| `transfer_input_files` | `s4_run.sh` | same | unchanged |
| `output` / `error` / `log` | `s4.out` / `s4.err` / `s4.log` | same | unchanged |
| `+RequestWalltime` | `3600` | `3600` | unchanged |
| `RequestCPUs` | `2` | `2` | unchanged |
| **`RequestMemory`** | **`8000`** | **`2000`** | **the authorized change** |
| `request_disk` | `2000000` | `2000000` | unchanged |
| `requirements` | `TARGET.ProvidesETPResources` | same | unchanged |
| `queue` | `1` | `1` | unchanged |

`c152c329…` is the v2.1 CPU image digest of `R1-TRACKP-IMAGE-V21` (as required by the author row and already
recorded unchanged in the disk review); this edit leaves it untouched. The JDL `requirements` line is the same
`TARGET.ProvidesETPResources`; HTCondor adds the container/`Arch`/`Disk`/`Memory`/`Cpus`/file-transfer clauses
internally (visible in `dryrun.txt`), and the edit changes none of them.

## Author row (main `9e207d3f`)

`docs/r1/PLAN.md:1451` (blob `527f22be…`, file sha256 `d4eaa207…`), under
"### 23 November 2026 (c) — I2 memory request (author)":

> **R1-TRACKP-I2-MEM** — Image v2.1 check I2 (R1-TRACKP-IMAGE-V21): `request_memory` goes from 8,000 MB to
> 2,000 MB (`reports/release_20261122/I2_MEMORY_DIAGNOSIS_20261123.md`: measured MemoryUsage 48 MB and RSS 73 MB
> on 759693; 0 unclaimed matching slots at 8 GB). Only `request_memory` changes, with a short independent review
> of the JDL diff; 759982 is removed and the job resubmitted. Checks, image digest, pool and `request_disk`
> (2,000,000 kB, R1-TRACKP-I2-DISK) are unchanged. Disclosed in the image report.

Commit `9e207d3f94b7d240740f4378d19dba4ebbb0b026` (2026-11-23 16:42:04 +0100, parent `31e442e8`, the then-main
tip) records the author's chat signature at 16:40 CET ("签 I2-MEM + 推 + 推 main"), committed on their behalf. The
row authorizes exactly the observed value pair and "only `request_memory` changes" — both hold. It also commits to
"759982 is removed and the job resubmitted"; that clause is not fulfilled (see next section). The row is live on
current `origin/main` `14f19a09` at the same line 1451 (blob `ff0bd980…`; text identical), so the authorization
is current, not stale.

## Measured basis (report, independently re-checked)

Report `docs/r1/reports/release_20261122/I2_MEMORY_DIAGNOSIS_20261123.md` at `9e207d3f` (blob `101e171b…`, sha256
`b7ab06a4…`, 69 lines; the PLAN row's relative `reports/…` path resolves under `docs/r1/`). Verified contents:

| Evidence | Value | My read-only check |
|---|---|---|
| Prior I2 v2 job 759693 | `MemoryUsage=48` MB, `ResidentSetSize=75,000` kB (≈73 MB), `ImageSize=50` MB, `DiskUsage=30` kB, wall 243 s | `condor_history 759693 -af …` returned exactly `48 75000 50 30 243.0` — matches |
| Eligible ETP container set | 241 slots (ETP+container+arch/OS+file-transfer+CPUs≥2+Disk≥2 GB) | report's sample; not re-derived (cluster-state dependent) |
| Slots at `request_memory` ≥8,000 MB | 222, **0 unclaimed** | report's sample; statement is accurate for its sample |
| Slots at ≥2,000 MB | 239, **2 unclaimed** (≥1,000 MB: 4) | report's sample |
| Recommendation | 2,000 MB ≈27× the measured RSS (75,000 kB); only `request_memory` | arithmetic checks out |

The report's "0 unclaimed at 8 GB" is a time-local snapshot, not a permanent condition: I2's own 8 GB job did
match and run at 16:19 CET (next section), and the report itself notes capacity appears/disappears between
negotiation cycles. This is a caveat on the urgency argument, not an error in the report; the eligibility
argument (2 GB ≥ 8 GB eligibility) is still true in every sample.

## Job 759982 — the gated premise is false

At review time the old 8,000 MB I2 job is **gone from the queue and completed**. Evidence:

| Property | Value | Source |
|---|---|---|
| `condor_q 759982` | 0 jobs matched (no i2 cluster queued; queue holds only 759624/759625 P6/P7 idle and a friemer GPU job) | `condor_q` |
| `JobStatus` | **4 (Completed)** | `condor_history 759982` |
| `QDate` | `1795426206` = 2026-11-23 **10:30:06 CET** | `condor_history`; `s4.log` submit event 10:30:06 |
| Started executing | 2026-11-23 **16:19:07 CET**, slot `slot1_7@ms03.etp.kit.edu` | `s4.log` event 001 |
| `CompletionDate` | `1795447205` = 2026-11-23 **16:20:05 CET** | `condor_history`; `s4.log` event 005 |
| `ExitCode` | **0** (normal termination, return value 0) | `condor_history`; `s4.log` |
| `RequestMemory` / `RequestDisk` / `RequestCpus` | **8000** / 2000000 / 2 (the old, pre-edit request) | `condor_history` |
| `ContainerImage` | `docker://ghcr.io/dowlingwong/r1-htc-cpu@sha256:c152c329…` | `condor_history` |
| `MemoryUsage` / `ResidentSetSize` / `DiskUsage` | **123 MB** / **150,000 kB** (≈146 MB) / 30 kB | `condor_history`; `s4.log` event 006 |
| `RemoteWallClockTime` | 58 s | `condor_history`; `s4.log` `TimeSlotBusy=58` |
| `Cmd` | `…/i2/s4_run.sh` | `condor_history` |
| Output tree | `/work/dwong/paperb/work/s4_759982.0_20261123T151938Z` (13 MB) | `ls`, `du` |
| Result | **`I2_PASS`** — 4 seeds all `val_score=0.922225`, `train_loss=0.314016`; `pytest_rc=0` twice | `i2_compare.txt`, `i2_summary.txt`, `s4.out` |

The JDL edit at 17:02:22 CET therefore postdates the job's successful completion by about 42 minutes; the edit
was applied on the stale "still idle" state from the ~14:40Z diagnosis. The watcher had in fact already consumed
the result: `watcher.log` at `2026-11-23T15:20:17Z` reads "I2 and I3 PASS … SUBMIT_SMOKE" and submitted smoke
cluster 759983 (GPU digest `31478d99…`), which completed with `ExitCode=1` at 15:29:49Z (`STOP_SMOKE_759983
fail[4 1 551.0]`). The smoke failure is a separate, downstream matter outside this review's scope; it only
confirms that I2 itself was already accepted as PASS by the pipeline.

## Consequence for the gated action

- **Do not `condor_rm 759982`** — there is no matching job; the command would be a no-op.
- **Do not resubmit I2** — the check has already passed under the reviewed v2.1 CPU digest, and a resubmission
  would be a redundant run with a new cluster id, not a fix for anything.
- The JDL change needs **no correction**: it is exactly the authorized edit and is safe on the measured evidence
  (759693: 48 MB/73 MB; 759982, the run that actually exercised v2.1: 123 MB/≈146 MB; 2,000 MB is ≥13.7× the
  largest observed RSS). It may stand for a future I2 run. The before file `89fdc6af…` remains the exact 8 GB
  JDL under which 759982 ran.

## Residuals (non-blocking)

1. **Records are stale and need an author-side correction.** `R1-TRACKP-I2-MEM` (PLAN.md:1451) and
   `I2_MEMORY_DIAGNOSIS_20261123.md` / `I2_DISK_RESUBMISSION_20261123.md` still describe 759982 as idle/queued and
   the row commits to removing/resubmitting it. The actual outcome is: 759982 completed **I2_PASS** at 16:20:05
   CET. The row should record that outcome; the JDL memory edit is then a future-run preparation (or can be
   reverted), not an action tied to 759982.
2. **The cited measured basis is superseded by a tighter one.** The row cites 759693's 48 MB/73 MB; the v2.1 run
   759982 measured 123 MB/150,000 kB (≈146 MB). 2,000 MB is still comfortably safe (≈13.7×), but future-run
   documentation should cite the v2.1 number.
3. **JDL-vs-run mismatch.** The current `probe.jdl` (2 GB) is no longer the file that produced the passing run;
   `probe.jdl.before_memory_change` (`89fdc6af…`) is. Keeping the 2 GB JDL for future runs or restoring the 8 GB
   file are both defensible; this review modifies neither.
4. **Backup creation is corroborated, not independently timestamped.** `probe.jdl.before_memory_change` has the
   edit's own mtime (17:02:22.668 vs .672), so it was written immediately before the edit. Its 8 GB content is
   nevertheless independently confirmed by 759982's job ad (`RequestMemory=8000`) and by `dryrun.txt`
   (`RequestMemory=8000`, `RequestDisk=30000000`, `c152c329…`), both of which predate the edit.
5. **"0 unclaimed at 8 GB" was time-local** (the 8 GB job matched and ran later); noted above, not a defect of the
   diff or of the value chosen.

Nothing in the residuals changes the JDL-diff assessment: the change is the authorized, minimal, measured-safe
edit. The verdict applies solely to executing `condor_rm`/resubmit (or re-running I2) on the false "759982 still
present" premise.

VERDICT: NOT ACCEPTED
