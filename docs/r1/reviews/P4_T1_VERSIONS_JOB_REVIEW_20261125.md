# Independent pre-submit review — P.4 T1 `VERSIONS.txt` job, 25 November 2026

**Verdict: ACCEPTED for submission.** No blocking finding. The review gates the submission of T1 only; it is
read-only on the staged files (no job submitted, no file changed on deepthought). T2+ and any P.4 training are
outside this unit.

**Unit.** The read-only NEMO2 H200 HTCondor job of T1 in the accepted P.4 cluster test plan
`docs/r1/reports/trackp_p4_runner_20261122/P4_CLUSTER_TEST_PLAN_20261124.md` (plan accepted at `924205cc4`, file
sha256 `240ffd3b3a549d526f658fac245ea05234735f14970c1e0a06667a0ab4b32443`, byte-identical to this checkout's copy).
It reads `/opt/r1/VERSIONS.txt` in the digest-pinned image v2.2 GPU container on NEMO2 and runs the job's two
unscoped `nvidia-smi` queries (F3), so that `image.versions_sha256` can be filled from exact bytes. Staged on
deepthought in `/work/dwong/paperb/work/trackp-p4-cluster-20261125/T1_versions/` (plan `$D/T1_versions`, route A,
plan lines 234–238, 240–298).

**Reviewed bytes** (sha256 on deepthought; the local copies used for the checks are byte-identical):

```text
125342d1cfed4fd435d68bbc0c5e7655845318d7522c7c9bd64536e1b3432025  versions.sh   561 B  -rwxr-xr-x (0755)
fa7ec821ca1fd597184691117f0f846df139c0a40df32db4afb2553d2d33c97d  versions.jdl  644 B  -rw-r--r--
9d2f1087838e077dc7e036bbda93b72e1dae1b2499837f8f9a0adf1174c0633f  versions.dry 2089 B  -rw-r--r--
```

The directory holds exactly these three files (no submit log, no extra input). I did not submit, hold, release or
modify anything.

## What I checked

1. **Script is the plan's script.** A byte diff against the accepted plan's T1 snippet (lines 241–253) leaves only
   the plan's two explanatory comments absent (n1); every command is identical:
   - `set -uo pipefail` — no `-e`, so a failing `nvidia-smi` is recorded, not fatal;
   - `sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt || exit 2` — versions.out line 1 is the
     `<64 hex>  /opt/r1/VERSIONS.txt` line, the rest is the file text, so the plan's `sha256sum T1_VERSIONS.txt`
     equality check can be made;
   - the F3 block `{ … } > gpu_visibility.txt 2>&1` writes `CUDA_VISIBLE_DEVICES` / `NVIDIA_VISIBLE_DEVICES`, then
     the two queries, **each with `echo "rc=$?"`**, then `exit 0` — exactly as the plan writes them.
   - Both queries are the job's own, verbatim and unscoped (no `--id`): `p4_lib.gpu_identity`
     (`p4_lib.py:343–344`) runs `--query-gpu=name,uuid,driver_version,memory.total,compute_cap --format=csv,noheader`,
     and `run.foreign_compute_processes` (`r1/c3/train/run.py:151`) runs
     `--query-compute-apps=pid,process_name,used_memory --format=csv,noheader` (`4315ab295`). The script matches both
     strings character for character.
   - `bash -n` rc 0; ASCII, LF only, no trailing whitespace; mode 0755.
2. **JDL is the plan's JDL and keeps the accepted smoke header.** Diff against plan lines 257–275 is empty. Against
   the committed smoke `stages/smoke_h200/probe.jdl` the only differences are the digest (v2 → v2.2), the
   executable name, the dropped `arguments` (this job has none) and this job's own output names; every resource and
   selector line is byte-identical: `requirements` NEMO2 + `NVIDIA H200`, `+RemoteJob = True`, `request_GPUs = 1`,
   `request_cpus = 4`, `request_memory = 16000`, `request_disk = 35000000`, `+RequestWalltime = 3600`,
   `periodic_hold = (NumJobStarts > 1)`, `job_machine_attrs = CloudSite`, `should_transfer_files = YES`,
   `when_to_transfer_output = ON_EXIT`, `queue 1`.
3. **Image digest.** `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949`
   is the image v2.2 GPU digest: it equals `V22_BUILD_20261124.md` line 13, the plan (lines 86, 258), host config
   `trackp_htcondor_v2.json` `image.gpu` at `4315ab295`, and the runner report's `p4_spec.json` `image.digest`. It is
   neither the refused v2.1 digest `31478d99…` nor the CPU digest `a3b3a074…`.
4. **Dry run is a parsed job ad from these bytes.** `versions.dry` is a `condor_submit -dry-run` ad (Condor
   25.0.12): `JobUniverse=5`, `WantContainer=true`, `ContainerImage` exactly the v2.2 digest,
   `ContainerImageSource="docker"`, `RemoteJob=true`, `RequestGPUs=1`, `RequestCpus=4`, `RequestMemory=16000`,
   `RequestDisk=35000000`, `RequestWalltime=3600`, `PeriodicHold=(NumJobStarts > 1)`, `JobMachineAttrs="CloudSite"`,
   `ShouldTransferFiles="YES"`, `WhenToTransferOutput="ON_EXIT"`, `TransferOutput="gpu_visibility.txt"`,
   `Out="versions.out"`, `Err="versions.err"`, `JobSubmitFile="versions.jdl"`, one proc (`ProcId=0`, `JobStatus=1`),
   and a `Requirements` string carrying the NEMO2 and H200 terms plus `TARGET.GPUs >= RequestGPUs`. `QDate`/
   `EnteredCurrentStatus = 1795607132` = 2026-11-25 12:45:32 CET equals the mtimes of `versions.jdl` (12:45:32.00)
   and `versions.dry` (12:45:32.03), so the ad comes from the staged JDL. No secret, token or credential string in
   any of the three files; nothing beyond the public image URL, paths and `nvidia-smi` output is written.
5. **`versions.out` will come back although `transfer_output_files` lists only `gpu_visibility.txt`.** HTCondor
   transfers the declared `output`/`error` files as part of the output sandbox in addition to the listed files.
   Pool precedent: `docs/r1/reports/trackp_h200_20261118/i3_h200_20261121/` commits the non-empty `i3.out`
   (sha256 `10855c46…`, 2,534 B) although that job's `transfer_output_files` lists only
   `i3_identity.txt,i3_download.txt,…` and `output = i3.out`. So no JDL change is needed for line 1 of
   `versions.out`; the plan's `head -1` / `tail -n +2` procedure remains valid.
6. **Read-only metadata job, the only GPU job allowed now.** The script reads one file, runs two `nvidia-smi`
   queries and writes `gpu_visibility.txt` in the job sandbox; it reads no data, label, receipt, freeze or test
   path, trains nothing and cannot touch shared state. The plan (lines 132–133) allows the read-only T1 job to run
   before signature; a one-GPU request is the point (same slot kind as the P.4 jobs). At review time no T1 job had
   been submitted (no `versions.out/.err/.log` in the directory; `condor_q` shows no such job), so this review is
   the pre-submit check the plan requires (line 237–238).

## Non-blocking notes

- **n1.** The plan snippet's two comments (`# no -e: …`, `# F3: …`) are not carried into `versions.sh`; cosmetic
  only, no behaviour change.
- **n2.** The plan's F3 pass clause compares the GPU uuid with `CUDA_VISIBLE_DEVICES`, but the I3 record it cites
  lists the uuid in `NVIDIA_VISIBLE_DEVICES` (`i3_identity.txt` line 55). The script records both, so evaluate the
  "uuid equals the assigned device" clause against whichever variable HTCondor sets; do not STOP merely because
  `CUDA_VISIBLE_DEVICES` prints `unset`.
- **n3.** `exit 0` after the F3 block means the job exit code does not by itself gate F3 (by design). The operator
  must judge F3 from `gpu_visibility.txt` per plan T1: exactly one `NVIDIA H200` line whose uuid matches the assigned
  device, an empty compute-apps query, both `rc=0`; a second GPU or any listed compute process is STOP S6 (await a
  reviewed scoping change).
- **n4.** At the review sample the pool advertised 0 NEMO2 H200 slots, so a submitted job may sit idle until
  capacity returns; submission is still allowed by the plan, and no GPU cost accrues while idle.

**After the run** the operator should commit `versions.jdl`, `versions.sh`, `T1_versions_sha256.txt`,
`T1_VERSIONS.txt`, `gpu_visibility.txt`, the job id and the `condor_history` exit record, and check the plan T1 pass
criteria (exit 0, the two sha256 values equal, the expected VERSIONS fields; F3 as above). That outcome is not part
of this pre-submit acceptance.

VERDICT: ACCEPTED
