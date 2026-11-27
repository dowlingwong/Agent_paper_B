# Tier-E review — Ada P.4 synthetic-label probe (`compute/20261127-19`)

**Reviewed:** `origin/compute-p4-ada-probe-20261127` @ `616c09b251c03ac3e6aa78c6c8b2eb97d5cd7956`
**Base:** `origin/main` @ `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505`
**Task card:** `tasks/compute/20261127-19-ada-probe-run.md` on `origin/coord/coordinator` @ `324f6ad4`
**Review branch:** `compute-p4-ada-probe-review-20261127` (this file only)
**Mode:** read-only. No job was launched, stopped or retried. Host checks were `ssh deepthought` / `ssh ada_server` with `ls`, `cat`, `ps`, `nvidia-smi`, `sha256sum` and `git status` only. The sealed attempts under `/ceph` and the launcher logs under `/data1` were read, never written.

## Verdict

**ACCEPTED WITH MINOR FINDINGS.** The probe measurements, seals, charge arithmetic and the 4B-OOM-as-arm-STOP conclusion verify. The two 0.8B PASS records are complete (50/50 steps through `probe`, `stop: null`, the claimed peaks and timings), the two 4B records are the claimed CUDA OOMs on empty cards, and the total charge is 2.1603 GPU-h. Four minor findings follow: one operational cleanup (two engineering guard loops are still running), one P4-T1CHARGE-A record-completeness gap in `probe_charges.json`, one imprecise sentence about which STOP the kept refusal came from, and one false "copied verbatim … with `p4_run.log`" claim. None changes a measured value or the STOP. No re-review is needed if the fixes are applied; the guard loops must be stopped on the host by the operator.

## Confirmed

### 1. Probe spec validates at probe strength; fills are the pinned values

```
$ sha256sum docs/r1/reports/trackp_p4_probe_ada_20261127/p4_probe_spec_ada.json
540bd9798017260ca391612351706189712221c269482a7d47385695160a50a2  .../p4_probe_spec_ada.json

$ python3 r1/scripts/htcondor/trackp_p4/p4_lib.py validate --probe \
    docs/r1/reports/trackp_p4_probe_ada_20261127/p4_probe_spec_ada.json
{"ok": true, "strength": "probe", "run_id": "trackp-p4-probe-20261125-a", "probe": {...}}
# rc 0
```

`p4_lib.check_probe_template(spec, p4_probe_spec.json)` passes. The only differences from the committed template are the four allowed fills:

| Field | Value |
|---|---|
| `paper.commit` | `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505` |
| `image.versions_sha256` | `aaa1a304c2230466f603e63c96d7259d631f0668fa2d8b6486772fef22f0117a` |
| `host_class` | `ada_rtx6000` |
| `hosts.ada_rtx6000.host_config.sha256` | `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908` |

The H200 host-config sha stays a placeholder, as probe strength permits. The filled Ada host-config sha is exactly `sha256(trackp_ada_v1.json @ 91cfd48a)`:

```
$ git show 91cfd48a:r1/scripts/configs/trackp_ada_v1.json | sha256sum
bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908  -
```

The spec's `paper.commit` is the merge commit carrying the Ada host-config fill and the reviewed venv launcher; the Ada config at that commit has `sft.micro_batch: 8`, `gpu.name: NVIDIA RTX 6000 Ada Generation`, `gpu.compute_capability: 8.9`, `gradient_checkpointing: true` (the SFT path itself does not call `enable_gradient_checkpointing`; see §6).

The image VERSIONS claim also verifies independently from the registry. The pinned digest `sha256:49dd9900…5949` has final layer `sha256:593e83870d003c3d5dea4f68297b98b9310ab389c4630abeb94c93a72fd7ad82`; that layer contains `opt/r1/VERSIONS.txt` with sha256 `aaa1a304…`, byte-identical to the committed `T1_VERSIONS.txt`. This is a stronger check than the report's "read from the final OCI layer" statement; the VERSIONS pin is correct.

### 2. All eight committed sealed attempts verify; the copy is byte-identical for the files present

```
$ for d in */*/; do (cd "$d" && sha256sum -c SHA256SUMS); done
out.tar: OK
job_record.json: OK        # x8, all OK
```

For every attempt, `SEAL_RECEIPT.json` agrees with `job_record.json` and `direct_launch.json` on: `job_record_sha256`, `direct_launch_sha256`, arm/attempt, `run_id`, `host_class`, `gpu_uuid`, `other_processes_start/end`, host-config sha, stage-manifest sha, launcher wall clock and exit code, and the STOP string. The receipt's `charged_gpu_hours` is `max(launcher_wall_clock_s/3600, job_record.gpu_hours)` to 4 dp in every case.

The eight committed `direct_launch.json`, `job_record.json`, `out.tar`, `SEAL_RECEIPT.json` and `SHA256SUMS` files are byte-identical to the `/ceph` originals (all five hashes match per attempt). The ledger `_submissions.jsonl` on `/ceph` has exactly eight entries, each mapping 1:1 to a sealed attempt by `stage_manifest_sha256`; no attempt is missing and no stage was launched twice.

### 3. The two PASS records are complete

| Arm | Attempt | `steps` | `stop` | `stopped_at` / `total_steps` | Peak | s/step | rc | Wall |
|---|---|---|---|---|---|---|---|---|
| `kev-0.8b` | 4 | `identity, clone, env3_freeze, configs, staging, table, data, probe` | `null` | 50 / 50 | 25,939 MiB | 3.7188 | 0 | 443.139 s (0.1231 h) |
| `qwen3.5-0.8b-base` | 2 | same | `null` | 50 / 50 | 27,271 MiB | 3.7055 | 0 | 1,624.069 s (0.4511 h) |

The `stage_s/sft_report.json` in each `out.tar` shows `completed: true`, `early_stopped: false`, `stopped_at: 50`, `micro_batch: 8`, `effective_batch: 16`, `lr: 1e-5`, `seed: 0`, `protocol_deviation: {"max_steps": 50}`, and a `data_sha256` equal to the job record's `sft_data_sha256`. The `p4_run.log` JSON tail reports the same peak and s/step. The report's "50 steps, peak 25,939 MiB, 3.7188" and "50 steps, peak 27,271 MiB, 3.7055" are exact.

### 4. The two 4B records are the claimed OOMs on empty cards

| Arm | `steps` | `stop` / `stop_class` | `oom` | Peak | Headroom | Card start/end | rc |
|---|---|---|---|---|---|---|---|
| `kev-4b` | `…, data` | `STOP: CUDA OOM in sft-dev at micro-batch 8 (P4-MB; the author decides); …` / `arm` | `true` | 48,385 MiB | 0.0154 | count 0 / 0 | 2 |
| `qwen3.5-4b-base` | `…, data` | same / `arm` | `true` | 48,399 MiB | 0.0151 | count 0 / 0 | 2 |

The tails of `out/logs/001_sft-dev.log` are `torch.OutOfMemoryError: CUDA out of memory` with 47.30 GiB total and 47.44 MiB / 33.50 MiB free; the `direct_launch.json` for both records shows `other_processes_start/end = {count: 0}` and 48,427 MiB free at lease time. The report's "full-card peaks with card_processes_start/end count 0" is correct.

### 5. Charge arithmetic and completeness

The eight receipt charges sum to

```
0.0092 + 0.0688 + 0.0596 + 0.1231 + 0.6320 + 0.1588 + 0.4511 + 0.6577 = 2.1603
```

and `probe_charges.json` reports `total: 2.1603`, `pending: []`, `unrecorded: []`, all eight attempts, one run. T1's committed history is `760065 0 3 0.0`; `p4_lib.t1_record()` returns that one job with `remote_wallclock_s: 0.0`, and `p4_lib.probe_charges(<dir>, t1_wallclock="condor_history")` returns `total: 2.1603`, `t1_gpu_hours: 0.0`. So the claimed total is right and T1's zero does not change it. See L1 for the one gap in the committed JSON.

### 6. P4-MB A makes the 4B OOM an arm STOP; no workaround was applied — and none was required

Governing text (PLAN `R1-TRACKP-P4-DECISIONS`, P4-MB A; decisions row 5): micro-batch 8, effective batch 16; "An OOM is a STOP either way", the author decides. The Ada host config sets `sft.micro_batch: 8`. `R1-CARD-SHARE (3)` makes an OOM **infrastructure** only when it is lost "beside another process"; here every 4B attempt had `card_processes_start/end.count = 0` and `card_shared = false`, so it is the arm's measured fit failure, not infrastructure.

The two 4B arms were attempted exactly once each (`_submissions.jsonl` has one stage per arm; no second stage or attempt). No micro-batch, checkpointing, seed or assertion was changed (the branch is docs-only; the job's `p4_lib_sha256` is the base `f011a65f…`). The SFT path (`sft-dev` → `_stage_s` → `SFT.run_stage_s`) never calls `enable_gradient_checkpointing`, so the record's `"off (SFT path)"` and the report's "with checkpointing off" are accurate even though the host config's `gpu.gradient_checkpointing` is true for other commands.

**My view: no retry or workaround was required.** Re-running micro-batch 8 on an empty 48 GB card cannot change the fit; lowering the micro-batch or enabling checkpointing is a P4-MB author decision that the unit did not have, and doing it silently would have invalidated the "no workaround" claim. The report's STOP + author-decision route is the correct disposition under the rows.

### 7. Harness and stale-main disclosures are accurate; no label read

Both PASS `manifest.json` files record:

```
git.harness = {commit: 897d83c8efa364ec2fdd37288241cc42e01d7274, branch: "HEAD", dirty: false}
git.paper   = {commit: 91cfd48a67f8d62d4e20826976cbdbdbcfcaf505, branch: "HEAD", dirty: false}
environment = {torch: "2.6.0+cu124", transformers: "5.19.0", peft: "0.21.2"}
```

On `ada_server`, `/data1/zli538/paperb_p4_20261127/harness` is at `897d83c8…` with a clean `git status`, and each job directory has `autoresearch_harness -> /data1/zli538/paperb_p4_20261127/harness`. `p4_direct.py`'s native branch sets `environ = {"PATH": ..., VENV_LEASE_FD_ENV: ...}` for the venv job (`execute`, `native = runtime == "venv"`), so `AR_HARNESS_ROOT` indeed cannot reach the job; the symlink is the disclosed workaround. The `qwen3.5-0.8b-base` attempt-1 is sealed `stop_class: protocol` with `origin/main is stale or missing`; the later records' `clone.origin_main` is `7f6f8023…` or `c4250f7e…`, both published `main` ancestors (I checked `7f6f8023` is an ancestor of `origin/main` `c4250f7e`). The sealed tree and the committed copies are unaffected; `paper.commit` stays `91cfd48a`.

Completed records have `data.labels: synthetic`; the `sft-data` command uses `--labels synthetic` and no label-block path appears in the logs. The table (`sweep1_v3` features/configs), split file and classification are read, which the probe spec allows. I found no sealed/test label read.

### 8. The branch is docs/record-only

```
$ git diff --name-only 91cfd48a67f8d62d4e20826976cbdbdbcfcaf505 616c09b2 | grep -v '^docs/'
# (empty)
$ git diff --diff-filter=M --name-only 91cfd48a 616c09b2
# (empty; 50 files, all A, all under docs/)
```

The two commits are `e066dc6d` (spec, T1 VERSIONS, host-config fill record) and `616c09b2` (probe record, sealed attempts, STOP report). No code, assertion, label or existing document was modified.

### 9. Host, card and process facts

`ucrtasl`, uid 1008 / `zli538`, 8 × RTX 6000 Ada Generation, 49,140 MiB each, driver 545.23.08; the pinned 121-line freeze `50238e5a…` with sorted sha `e607c1d8…`; venv Python 3.12.10. The probe used card **0** (`kev-0.8b`, then `qwen3.5-4b-base`), card **2** (`kev-4b`) and card **6** (`qwen3.5-0.8b-base`). At review time `nvidia-smi` showed another user's PID 2754549 on cards 1/3/4/5 and cards 0/2/6 free (5 MiB), consistent with the report's "other users' four cards 1/3/4/5 were not touched". No trackp GPU job was running.

## Findings

### M1 — MEDIUM (operational and report accuracy): two probe guard loops are still running

The report's closing line says "All host processes of this probe are finished; no GPU job is left running." The GPU part is true; the first clause is false. At `2026-11-27 07:48:45 UTC`:

```
$ ps -u zli538 -o pid,ppid,etime,cmd | grep -E 'harness_(watch|fetch)2'
1741570       1       53:02 /bin/bash /data1/zli538/paperb_p4_20261127/harness_watch2.sh
1916154       1       24:23 /bin/bash /data1/zli538/paperb_p4_20261127/harness_fetch2.sh
2109863 1916154       00:00 git -C .../kev-0.8b/20261127T062705Z-1559797-3db5b1//paper fetch -q origin +refs/heads/main:refs/remotes/origin/main
```

`harness_watch2.sh` is a bounded 14,400-iteration loop; `harness_fetch2.sh` is an **unbounded** `while true` that fetches `origin/main` every 10 s into each job's `paper` clone. They do not touch `/ceph/srv/dwong/paperb/trackp_p4/trackp-p4-probe-20261125-a/` (the sealed hashes above are stable), but the statement in the report is wrong and an infinite loop is left on a shared host. **Action:** the operator should stop PIDs 1741570 and 1916154 (and any child fetch) and correct the last line of the report; no branch or spec change is needed.

### L1 — LOW (P4-T1CHARGE A record completeness): `probe_charges.json` has `t1: null`

```
$ python3 -c 'import json;d=json.load(open(".../probe_charges.json"));print(d["t1"],d["t1_gpu_hours"],d["total"])'
None None 2.1603
```

`p4_lib.probe_charges` documents that `t1` is `None` when neither a T1 input nor a charge file holds it, and `probe_records` / `check_probe_ledger` STOP with "no probe charge file holds T1's charge" / "T1's RemoteWallClockTime is required". The report's "(T1 zero)" is substantiated by `condor_history.txt` and by `probe_charges(..., t1_wallclock="condor_history")` (total 2.1603, `t1_gpu_hours: 0.0`), but the committed audit file itself was generated without T1, so it is not by itself a P4-T1CHARGE-A-complete charge record. Because the probe record was refused for the 4B arms anyway, no result is affected; if this JSON is the charge evidence for the note, regenerate it with T1's entry so `t1` is not null.

### L2 — LOW (refusal attribution): the kept refusal names the uv attempt, not the 4B OOM

`probe_record_refusal.txt` says:

```
STOP: /ceph/.../kev-0.8b/attempt-1 is not a sealed, verified, STOP-free probe attempt of this probe spec (on ada_rtx6000)
```

Reproducing `p4_lib.probe_records` against the committed attempts (read-only, no charge files written):

| Input to `probe_records` | STOP |
|---|---|
| all 8 attempts | `kev-0.8b/attempt-1 is not a sealed, verified, STOP-free …` (this is the committed text) |
| only the two STOP-free attempts (`kev-0.8b/attempt-4`, `qwen3.5-0.8b-base/attempt-2`) | `the probe record needs every arm ['kev-0.8b', 'kev-4b', 'qwen3.5-0.8b-base', 'qwen3.5-4b-base']; got ['kev-0.8b', 'qwen3.5-0.8b-base']` |
| the two STOP-free + the two 4B attempts | `kev-4b/attempt-1 is not a sealed, verified, STOP-free …` |
| the two STOP-free + `qwen3.5-4b-base/attempt-1` | `qwen3.5-4b-base/attempt-1 is not a sealed, verified, STOP-free …` |

So the **substantive** reason no Ada record exists is the two 4B OOMs (there is no STOP-free attempt for those arms); it is not a record defect. But the **quoted** refusal is a usage artifact from passing the non-STOP-free `kev-0.8b/attempt-1` (which is also `identity_verified: false`), not the message the 4B OOM produces. The report's sentence "… refuses with [attempt-1] because … the 4B OOM leaves no Ada record for those arms" should distinguish the two, e.g. "the kept run passed all eight attempts and stopped at attempt-1; with only STOP-free attempts the builder stops because the 4B arms have none."

### L3 — LOW (copy claim): `p4_run.log` is not in the committed attempts

The report says the attempts were "copied verbatim … with their `SEAL_RECEIPT.json`, `job_record.json`, `SHA256SUMS`, `out.tar`, `p4_run.log` and `direct_launch.json`." Each source directory on `/ceph` does contain `p4_run.log` (229–382 bytes), and the receipt's `run_log_sha256` matches it, but the committed attempt directories contain only the other five files; `find` and `tar -tf out.tar` show no `p4_run.log`. `SHA256SUMS` covers only `out.tar` and `job_record.json`, so the run log is not sealed either way. The STOP text is in `job_record.stop`, so the record is still readable; either add `p4_run.log` to the copy or drop it from the "copied verbatim" list.

### N1 — NIT (wording): `output_use` says H200 on an Ada record

Every Ada `job_record.json` has `output_use: "ENGINEERING_ONLY H200 SFT fit and timing probe …"` while `host_class: ada_rtx6000`. This is a hardcoded string in the probe summary, not a data error; "H200" should be dropped or made host-class-neutral.

## What I could not verify

- **NEMO2's "no H200 slot" claim.** I have no NEMO2 scheduler access. The committed `versions.dry` (`JobStatus=1`, `RemoteWallClockTime=0.0`), `versions.submit` (`760065`) and `condor_history.txt` (`760065 0 3 0.0`) are consistent with the idle/removal story; the VERSIONS substitution itself is independently verified from the OCI layer.
- **The exact order** "T1 job removed only after the image VERSIONS file had been read." The artifacts show both facts but not their timestamps relative to each other.
- **The exact command that produced `probe_charges.json`.** No CLI subcommand writes that file alone; the data is correct and the `t1: null` gap is visible, but the generating invocation is not recorded.
- **The full test suite** was not rerun (docs/record-only branch; no code changes). The report cites the accepted venv unit's prior run; I did not repeat it.
- **`p4_run.log` text** was read from `/ceph` and its hash matches the receipt, but the text is not in the branch (see L3).

## Reviewer statement

I did not modify the task branch, did not push `main` or `compute-p4-ada-probe-20261127`, and did not launch, stop or retry any job. The only change on `compute-p4-ada-probe-review-20261127` is this review file. The two guard loops in M1 are still running; stopping them is a host action for the operator, not something this read-only review did.
