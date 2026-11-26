# Independent review — R1-TRACKP-I2-DISK `request_disk` change (23 November 2026)

Reviewer: `reviewer-i2-disk`, independent and read-only. Scope: the single on-deepthought edit of the I2 probe
submit file `/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/i2/probe.jdl`
(`request_disk` 30,000,000 → 2,000,000 kB), the author row that authorizes it, and the measured-need basis.
Method: read-only `ssh` commands only (`sha256sum`, `diff`, `cmp`, `wc`, `cat -A`, `stat`, `condor_q`,
`condor_history`, `condor_status`, `du`); records on `origin/main` read through `git show`/`git grep`/`git cat-file`.
No job was submitted, edited, held or removed; nothing was written on deepthought; the only write is this review.
The publishing main is `origin/main = 3522e59b` (the local `main` ref is stale at `bc31e15e` from 27 October;
every "main" citation below is at `3522e59b`). No credential/secret file was read. Review time 2026-11-23
≈10:29 CET (09:29Z).

## Bottom line

**ACCEPTED.** The current deepthought `probe.jdl` differs from its pre-change backup `probe.jdl.before_disk_change`
by exactly one line — `request_disk = 30000000` → `request_disk = 2000000` (kB) — and by nothing else, byte for
byte. The author row R1-TRACKP-I2-DISK on main `3522e59b` authorizes exactly this edit (and the subsequent
`condor_rm`/resubmit of 759919). The measured I2 footprint is ≲63 MB, so 2 GB (1.91 GiB) is a conservative request.
This review unblocks `condor_rm 759919` and resubmission from the reviewed JDL; the resubmission itself still
needs the post-submit check recorded under Residuals 5.

## Artifact and hashes

Directory `/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/i2/` on `deepthought.etp.kit.edu` (user `dwong`).

| File | sha256 | Size | Lines | mtime (CET) |
|---|---|---|---|---|
| `probe.jdl` (**after**, current) | `89fdc6afdf38cc9960161f01874ff34f155bf27aad2f640d50ddab415cf6be2c` | 485 B | 16 | 2026-11-23 10:23:22.900 |
| `probe.jdl.before_disk_change` (**before**) | `afa811bc15eddba885858724dad26b7baf4250fcb1af1c029535214d1a22a93a` | 486 B | 16 | 2026-11-23 10:23:22.896 |
| `probe.jdl.orig` (21 Nov original, context only) | — | 486 B | 16 | 2026-11-21 23:28:16.233 |

Both compared files are mode `644`, owner `dwong:cms`, and have identical line structure under `cat -A` (no CR, no
trailing-whitespace or newline change). The 1-byte size decrease is exactly the removed digit in the value.

## Diff (before → after)

```diff
--- probe.jdl.before_disk_change
+++ probe.jdl
@@ -11,6 +11,6 @@
 +RequestWalltime = 3600
 RequestCPUs = 2
 RequestMemory = 8000
-request_disk = 30000000
+request_disk = 2000000
 requirements = TARGET.ProvidesETPResources
 queue 1
```

`diff` returns a single hunk with a single `-`/`+` pair; no other line differs.

## Deterministic proof that nothing else changed

```text
sha256( sed 's/^request_disk = 30000000$/request_disk = 2000000/' probe.jdl.before_disk_change )
  = 89fdc6afdf38cc9960161f01874ff34f155bf27aad2f640d50ddab415cf6be2c
sha256( probe.jdl )
  = 89fdc6afdf38cc9960161f01874ff34f155bf27aad2f640d50ddab415cf6be2c   (identical)
```

The current file is byte-for-byte the backup with only that substitution, so every unchanged field is confirmed
by construction, not just by visual diff:

| Field (JDL line) | Before | After | Verdict |
|---|---|---|---|
| `universe` | `container` | `container` | unchanged |
| `container_image` (CPU digest) | `…r1-htc-cpu@sha256:c152c32980ccd708a9b5fda0a1da49b963064ebcbc608849406adf0c95bdf148` | same | unchanged |
| `executable` | `s4_run.sh` | `s4_run.sh` | unchanged |
| `arguments` | `"$(ClusterId).$(ProcId)"` | same | unchanged |
| `should_transfer_files` / `when_to_transfer_output` | `YES` / `ON_EXIT` | same | unchanged |
| `transfer_input_files` | `s4_run.sh` | same | unchanged |
| `output` / `error` / `log` | `s4.out` / `s4.err` / `s4.log` | same | unchanged |
| `+RequestWalltime` | `3600` | `3600` | unchanged |
| `RequestCPUs` | `2` | `2` | unchanged |
| `RequestMemory` | `8000` | `8000` | unchanged |
| **`request_disk`** | **`30000000`** | **`2000000`** | **the authorized change** |
| `requirements` | `TARGET.ProvidesETPResources` | same | unchanged |
| `queue` | `1` | `1` | unchanged |

`c152c329…` is the v2.1 CPU image digest of `R1-TRACKP-IMAGE-V21`
(`docs/r1/reports/trackp_h200_20261118/V21_IMAGE_006FC315.md`, `cpu` row); the author row explicitly requires the
image digest to be unchanged by this edit, and it is.

## Author row (main `3522e59b`)

From `docs/r1/PLAN.md:1430` (blob `d28a7250…`, sha256 `2331de67…`), under
"### 22 November 2026 (h) — sweep-1 release compatibility replay; I2 disk request (author)":

> **R1-TRACKP-I2-DISK** — Image v2.1 check I2 (R1-TRACKP-IMAGE-V21): `request_disk` goes from 30,000,000 kB to
> 2,000,000 kB (`reports/release_20261122/I2_WAIT_20261122.md`: measured need about a 30 kB sandbox, a 50 MB image
> and 13 MB of output; 37 slots match at 30 GB, 192 at 2 GB). Only `request_disk` changes, with a short independent
> review of the JDL diff; job 759919 is removed and the job resubmitted. I2's checks, the image digest and the pool
> are unchanged. Disclosed in the image report.

Commit `3522e59bf52e738c92981a1ffde67527059f071b` (merge, 2026-11-23 10:08:44 +0100) is `origin/main`. The row
authorizes exactly the observed edit (value pair, "only `request_disk` changes", a short independent JDL-diff
review, and 759919 removed + resubmitted), and does not authorize any change to the image digest, probe checks or
pool — none of which this edit touches.

## Measured need (supports 2 GB)

Report: `docs/r1/reports/release_20261122/I2_WAIT_20261122.md` (blob `7424fc55…`, sha256 `9a68e3a5…`), read at
`3522e59b`; quantities independently re-measured read-only at review time:

| Evidence | Value | Source |
|---|---|---|
| Prior I2 v2 job 759693 sandbox | `DiskUsage=30` (kB units), `ImageSize=50` MB, `RemoteWallClockTime=243` s | `condor_history 759693 -af …` |
| Prior I2 v2 output trees under `/work` | `s4_5045197.0_20261118T002411Z` = **13 MB**; `s4_759693.0_20261115T002553Z` = 58 kB | `du -sh` |
| Current I2 probe dir | 56 kB (scripts/logs only) | `du -sh` |
| Requested value | 2,000,000 kB = 1,953 MiB ≈ **1.91 GiB** | HTCondor kB = 1024 B |

The combined observed footprint (30 kB scratch + 50 MB image + 13 MB output ≈ 63 MB) is ~31× below the requested
1.91 GiB (and ~150× below it if only the sandbox/output is counted), so 2 GB is conservative; there is no evidence
in the I2 design or its measured runs that anything near 30 GB is needed. The report's ">50×" is a loose rounding
(when the 50 MB image is counted the ratio is ~31×) but the conclusion is unaffected. Corroboration of the
eligibility effect: the report's sample had 37 slots at Disk≥30 GB vs 192 at ≥2 GB (CPUs≥2, Memory≥8000); my
re-sample during review gave 434 ETP slots, 53 at ≥30 GB vs 97 at ≥2 GB — absolute counts move with cluster
state, but 2 GB strictly expands eligibility in every sample.

## Job 759919 status

Read-only `condor_q`/`condor_history`/`s4.log` at review time: cluster **759919.0 is Idle**, `RequestDisk=30000000`,
`RequestCpus=2`, `RequestMemory=8000`, `RequestWalltime=4000` with `RequestWalltime_RAW=3600` (the 3600 is the JDL
value; the 4000 is a site-side adjustment, not a JDL change), `ContainerImage=…@sha256:c152c329…`,
`QDate=1795309830` (2026-11-22 02:10:30Z). `s4.log` shows the 02:10:30 submit event and no run/termination/removal
events. The job is therefore still the old 30 GB request; it must be `condor_rm`'d and resubmitted from the current
`probe.jdl`. The old state is independently corroborated by `dryrun.txt` (generated from `probe.jdl` before the
edit; `JobSubmitFile="probe.jdl"`, `RequestDisk=30000000`, `ContainerImage=…c152c329…`), which also authenticates
the backup's content.

## Residuals (non-blocking)

1. **Post-resubmit verification is still owed.** After `condor_rm 759919` and resubmission, the new cluster ad should
   be checked to carry `RequestDisk=2000000`, `RequestCpus=2`, `RequestMemory=8000`,
   `ContainerImage=…@sha256:c152c329…`, and `Requirements` containing `TARGET.ProvidesETPResources`, and 759919 must
   be gone from `condor_q`. That is a lead/operator step after this review, not part of it.
2. **The JDL is an ops artifact outside the repo.** There is no tracked copy at the new value; this review's
   before/after sha256 pair is the provenance record. Any future re-instantiation of the I2 JDL must use
   2,000,000 kB (the PLAN row alone encodes the value).
3. **`probe.jdl.orig` vs the before file differs only by the image digest** (`08a36eff…` → `c152c329…`). That digest
   update is the separately authorized v2.1 CPU image pin (see V21 report/reviews) and predates this edit; this
   review's "digest unchanged" statement is relative to the before file, which is the correct baseline for the
   disk change.
4. **Report wording on output size.** The I2 report attributes the 13 MB `/work` tree to 759693, while 759693's own
   tree is 58 kB (the 13 MB tree belongs to the separate `s4_5045197…` run the report also lists). Documentation
   precision only; the largest measured output is 13 MB either way, so the 2 GB conclusion is unaffected.
5. **Backup creation is only corroborated, not timestamped independently.** `probe.jdl.before_disk_change` has the
   same mtime as the edit (10:23:22.896 vs .900), i.e. it was made immediately before the edit rather than earlier;
   its pre-change content is nevertheless independently confirmed by the 759919 job ad and `dryrun.txt` (both
   predate the edit and show 30,000,000 + `c152c329…`).
6. **4,000 s vs 3,600 s.** Not a change: `RequestWalltime` in the job ad is 4,000 with `RequestWalltime_RAW=3600`,
   a site-side adjustment of the unchanged JDL `+RequestWalltime = 3600`.

Nothing in the residuals changes the assessment; the edit is the authorized, minimal, measured-safe change.

VERDICT: ACCEPTED
